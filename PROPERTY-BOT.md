# Property bot deployment guide

For functionality and local setup, use [README](README.md). For the implemented
conversation behavior, use [WORKFLOW](WORKFLOW.md). This guide covers the current
capture-mode backend and its deployment.

## Environment

- Runtime: Python 3.12 on Lambda; local development should use Python 3.12.
- Region: Sydney (`ap-southeast-2`).
- Stack: `property-whatsapp-bot`.
- Catalog: packaged `data/listings.json`; all current records are fictional.
- Mode: `REPLY_TRANSPORT=capture`; no outbound WhatsApp messages are sent.

`.env` is private and is not automatically loaded. Export settings through your
shell/process manager. `.env.example` contains placeholders only.

| Variable | Purpose |
| --- | --- |
| `REPLY_TRANSPORT` | Use `capture` for POC testing; `twiml` and `rest` are opt-in send adapters |
| `TWILIO_AUTH_TOKEN` | Verify incoming Twilio signatures |
| `TWILIO_WEBHOOK_URL` | Exact external URL for local/tunnel signature validation |
| `TWILIO_ACCOUNT_SID` | Needed only for the REST send adapter |
| `TWILIO_WHATSAPP_NUMBER` | REST sender fallback; incoming `To` is preferred |
| `LEADS_TABLE` | DynamoDB test lead/visit storage |
| `TEST_SITE_ORIGIN` | Allowed browser origin for demo APIs |
| `LISTINGS_FILE` | Optional catalog path override |
| `PORT` | Local server port; defaults to 5001 |

In Lambda, the adapter reconstructs the external webhook URL from trusted API
Gateway request context. It does not trust a caller-supplied Host header for the
signature URL. Missing webhook security configuration fails closed.

## AWS prerequisites

Use AWS CLI credentials/profile, SAM CLI, Python 3.12 and make. Verify the
intended AWS account and region before deploying. Use short-lived credentials
where available. The current session's deployment identifiers are in
[the handoff](docs/RESUME.md).

The stack expects Secrets Manager secret `property-bot/twilio` with JSON fields
`auth_token` and `account_sid`. Create/manage it through your approved secret
process. Never put secret values in command arguments, source, logs, or docs.
CloudFormation resolves dynamic references into the Lambda environment. Increment
`ConfigurationRevision` and redeploy after changing the secret to refresh it.

## Build and deploy

```bash
make test
sam build --template-file template.yaml
sam validate --lint --template-file .aws-sam/build/template.yaml --region ap-southeast-2
sam deploy --guided --template-file .aws-sam/build/template.yaml --region ap-southeast-2
```

Review the change set and account costs before deploying. SAM creates the
execution role and scopes lead-table put/get and date-index query access.
The DynamoDB table uses on-demand billing, recovery protection and 90-day record
TTL; it is retained across stack deletion/replacement. CloudWatch retains
application/access logs for 14 days and provides a business dashboard.

The Makefile installs Linux x86_64 Python 3.12 dependencies and copies only the
allowlisted modules and catalog into the Lambda artifact. Do not replace it
with a recursive copy of the repository: `.env`, Git history, test artifacts,
and local environments must remain excluded. Protect local intermediate caches.

## Verify

```bash
make test
```

After deployment, verify health, unsigned webhook rejection, signed capture,
website workflow responses, and lead storage/analytics. `automate_workflow.py`
provides opt-in signed live capture verification; it requires a securely supplied
Twilio token, AWS access, the webhook URL and function log-group name. It refuses
to run unless the deployed function is capture-only.

The current Twilio trial rejects custom response bodies/TwiML. Changing XML
content types does not remove that restriction. Keep capture mode until paid
sender setup and end-to-end WhatsApp rendering/delivery tracking are ready.

## Removed legacy behavior

The unused canned-reply editor and `/config/replies` route were removed. The old
optional conversation logger was also removed; it was not a session store.
`LEADS_TABLE` is the supported persistent store for test submissions only.
The obsolete Meta-format and unsigned manual webhook scripts were replaced by
the signed local test suite and the opt-in live automation runner.

## Limits

The demo APIs remain publicly callable with throttling; CORS is not
server-side authentication. The private tester frontend does not change that.
Do not expose real customer management through them without access controls.

No agent notifications, booking confirmations, durable conversation sessions,
message queues, or outbound delivery callbacks are implemented. See the
[roadmap](PRODUCT-ROADMAP.md) and [architecture plan](docs/PILOT-ARCHITECTURE.md).
