# Property listing bot

The existing Flask bot now answers listing questions from `data/listings.json`.
The included five properties are fictional; replies carry a DEMO DATA warning.
No model calls or inferred property facts are used. Include an ID in each
question; conversation context and advanced search filters are not implemented.

Examples:

- `What is the price of DEMO-001?`
- `Does DEMO-005 allow pets?`
- `Show details for DEMO-003`
- `Can I visit DEMO-004?` (returns instructions, does not book a viewing)

## Spreadsheet updates

Edit the supplied workbook's Listings sheet, keeping column names unchanged.
Export that sheet alone as UTF-8 CSV. Numbers must be plain numeric values,
`transaction` must be `rent` or `sale`, `updated_on` must be YYYY-MM-DD.
Leave unknown facts blank. IDs must be unique, using letters, digits or hyphens.

```bash
python3 import_listings.py data/sample-property-listings.csv
python3 -m unittest test_property_bot -v
```

For real data, replace ALL demo rows, then import with `--real-data`. That flag
removes the demo warning. Imports validate before replacing the previous catalog.
The Lambda catalog is a packaged snapshot: rebuild and deploy after each import.
The bot does not directly read Excel or a live Google Sheet.

## Local Twilio setup

Install dependencies using your usual virtual environment. Set these environment
variables in your shell/process manager:

- `TWILIO_AUTH_TOKEN`: Twilio account auth token, never commit it.
- `TWILIO_WEBHOOK_URL`: exact HTTPS URL configured in Twilio, including any query.

`.env` is not automatically loaded by this application. Use your existing secure
environment loader; do not print tokens into logs. Start with `python3 bot.py`
(port 5001), expose HTTPS using your preferred tunnel, and configure the Twilio
WhatsApp sandbox/sender's incoming-message webhook to POST to
`https://YOUR-HOST/webhook/whatsapp`. Update TWILIO_WEBHOOK_URL whenever the tunnel
URL changes. Unsigned requests return 403; missing security settings return 503.

Inbound replies use TwiML, so account SID and WhatsApp sender number are only
needed if you use the separate outbound helper. The local `/config/replies`
endpoint is disabled unless ADMIN_API_TOKEN is set and a matching Bearer token
is provided. It manages legacy canned replies, not the property catalog.
It is not exposed by the AWS API.

The old `test_bot.py` uses Meta's direct webhook format and the old
`test_twilio_bot.py` does not sign requests. Neither is a valid security test for
this bot. Use `test_property_bot.py`; it tests Flask and Lambda without sending
messages or accessing AWS.

## AWS deployment (not yet deployed)

Use Lambda on-demand Event Functions because API Gateway invokes this Python
handler per webhook. A persistent HTTP server is unnecessary. The HTTP API keeps
the front door simple; REST API is the upgrade path if WAF integration or usage
plans are required. The public Twilio route uses signature authentication in
the application, rather than a Cognito login that Twilio cannot supply.

Prerequisites: AWS CLI credentials, SAM CLI, Python 3.12 and make. Select your
AWS profile and region explicitly. In AWS Secrets Manager, create a secret named
`property-bot/twilio` containing JSON with the key `auth_token` and your Twilio
auth token. Enter it through your normal secret-management process; never put
it in source code, CLI parameters, or this document.

The CloudFormation deployment identity needs permission to resolve that secret.
SAM creates a Lambda execution role with basic logging access; no database,
model, or secret-fetch permission is needed by the running function. The token
is resolved into the Lambda environment at deployment. After rotation, increment
ConfigurationRevision and redeploy to force a configuration update.

```bash
sam build --template-file template.yaml
sam deploy --guided --template-file .aws-sam/build/template.yaml
```

Choose a stack name and AWS region in guided deployment, acknowledge generated
IAM resources, and supply the secret NAME rather than the token. Only deploy
after reviewing the change set and costs for your account. Configure the output
WebhookUrl as the exact POST webhook in Twilio. Send an actual WhatsApp message
from a sandbox-joined phone to verify the complete integration.

Makefile uses an allowlist for the Lambda artifact. Only bot.py, listings.py,
lambda_handler.py, dependencies and data/listings.json are copied. It excludes
.env, git history and unrelated project files. Do not replace it with a recursive
copy of the repository. SAM itself may stage the source folder locally while
building; protect the working folder and do not share intermediate build caches.

CloudWatch retains access/function logs for 14 days. Access logs exclude bodies
and sender numbers. A Lambda error alarm is included; attach notification actions
before relying on alerts. Handled HTTP 5xx failures need API monitoring too.
Conversation logging remains optional legacy code and is disabled in this stack;
enable it only with an existing compatible table, scoped IAM and a retention plan.

No AWS resources or Twilio settings were changed during local implementation.
Account-specific permissions, regional deployment and live WhatsApp delivery
must be verified during deployment. The bot has no durable message deduplication;
Twilio retries may repeat a TwiML answer. It does not initiate marketing messages.

## Local validation results

14 unit/integration tests passed, covering signed and tampered webhooks,
missing security configuration, ambiguous property selection, unknown facts,
CSV imports and the API Gateway v2 adapter. The spreadsheet was rendered and
visually reviewed. cfn-lint 1.60.0 reported no errors or warnings.

Three AWS Guard registry rules were evaluated against the authored template:
log retention passed; two rule families reported three resource findings:

- `CLOUDWATCH_ALARM_ACTION_CHECK`: ErrorAlarm has no notification action. Set
  `AlarmActions` to an existing, approved notification topic ARN before relying
  on notifications. No recipient was invented during development.
- `CLOUDWATCH_LOG_GROUP_ENCRYPTED`: ApiLogs and FunctionLogs have no customer
  managed `KmsKeyId`. Default CloudWatch encryption remains in effect. If your
  policy requires customer managed keys, supply the key ARN and a suitable key
  policy for CloudWatch Logs before deployment.

This was a scoped Guard check, not a full compliance audit of SAM-generated
resources. No account-aware CloudFormation validation, SAM build, AWS deployment
or live Twilio delivery test ran: AWS CLI/SAM are unavailable in this environment.
