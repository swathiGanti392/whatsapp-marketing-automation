# Resume here: Shraddha Properties WhatsApp bot

Last updated: 6 November 2026 (Asia/Kolkata).

This is a handoff summary of the work and decisions in the Codex conversation.
It is not a verbatim transcript. Read current files and deployed settings before
making changes; this document records the state at the end of the session.

## User objective and decisions

- Build a Twilio WhatsApp property bot for Shraddha Properties.
- Start with a POC; planned production pilot is up to 100 conversations/day.
- Deploy AWS resources in **Sydney (`ap-southeast-2`)**, not Mumbai.
- Stay on the Twilio free trial for now. Do not initiate a paid upgrade.
- Test generated responses through a website and signed automation because the
  current Twilio trial restricts custom WhatsApp responses.
- Use rich, infographic-style conversations: welcome, property choices, property
  cards, prices, brochure overview, location/amenities, and visit preferences.
- Prioritize **leads and site-visit analytics**. User explicitly approved a small
  DynamoDB on-demand table in Sydney for test submissions.

## Locations

- Application repository:
  `/Users/kameswraiganti/workspace/whatsapp-marketing-automation`
- Codex working directory:
  `/Users/kameswraiganti/Documents/Codex/2026-11-06/use-aws-to-help-build-my`
- Website checkout, relative to that working directory:
  `work/shraddha-bot-lab`
- User-facing copies/reports: `outputs/` under that working directory.

## Deployed services

| Item | Value |
| --- | --- |
| AWS account | `014512980980` |
| Region | `ap-southeast-2` |
| CloudFormation stack | `property-whatsapp-bot` |
| API base | `https://xm62t0ivx8.execute-api.ap-southeast-2.amazonaws.com` |
| WhatsApp webhook | `POST /webhook/whatsapp` |
| Website conversation test | `POST /test/workflow` |
| Lead/visit submission | `POST /test/leads` |
| Aggregate analytics | `GET /test/analytics?days=7` or `30` |
| Health | `GET /health` |
| Bot Lab | `https://shraddha-bot-lab.swathiganti392.chatgpt.site` |
| Sites project ID | `appgprj_6aedc43985b08191bc9354223e62b3b4` |
| Latest published website source commit | `b2687a951f251f2ab9e29f24aa12f5be7444ba82` |
| Function log group | `/aws/lambda/property-whatsapp-bot-PropertyBot-us7mfKOt1IYp` |
| API access log group | `property-whatsapp-bot-ApiLogs-HDRWV4DMNsuC` |
| CloudWatch dashboard | `property-whatsapp-bot-leads` |

The website is owner-private through Sites. Its manifest is
`work/shraddha-bot-lab/.openai/hosting.json`. Preserve its project ID and audience;
update this Site rather than creating a new one.

The Twilio trial sender shown by the current console is `+1 737 250 8034`, with
join text `join twilio-trial`. The user joined it and its custom inbound webhook
was saved successfully. Verify the current console before reusing trial details.
Do not assume the older shared Sandbox number in local configuration is current.

## Current application behavior

- Incoming Twilio requests require a valid SDK-verified signature.
- Production Lambda is deliberately in **`REPLY_TRANSPORT=capture`** mode.
- Incoming messages generate a response and a `workflow_response` log, then
  return HTTP 204. No WhatsApp send is attempted in this mode.
- Website tests call the same conversation engine and receive structured cards
  and response text. The test route never sends WhatsApp messages.
- `Hi`/`MENU` offers Villas, Apartments, and Office Space. Text or numeric choices
  select a category; explicit commands such as `price DEMO-004`,
  `brochure DEMO-004`, `location DEMO-004`, and `visit DEMO-004` drive follow-ups.
- Six catalog records remain fictional demo properties. Do not reuse project
  claims in the user's style-reference screenshots as verified listing facts.
- Architecture images are labelled concept illustrations, not real photos.
- Brochure downloads are generated text overviews, not original PDF brochures.
- Conversation stage is **not persistently remembered**. Step 5 of the proposed
  architecture processes transitions; Step 6 would persist conversation state.
  The current DynamoDB table stores submissions, not conversation sessions.

## Leads and visits

- Property cards include a contact-interest form and a visit-request form.
- Names, email/phone, and consent are required; visit requests also require a
  valid preferred date.
- Submissions are stored in a DynamoDB on-demand table created by the stack as
  logical resource `LeadsTable`. Discover its physical name from CloudFormation.
- Conditional writes prevent a retry of the same submission ID from being
  counted again. A deliberately new submission counts separately.
- Records are marked `source=web_test`. Lead status is `new`; visit status is
  `pending_confirmation`. No notifications or bookings are triggered.
- The aggregate dashboard shows contact interests, visit requests, unique contact
  identifiers, pending visits, daily totals, and requests by property.
- Windows are 7/30 UTC calendar days including today. The date index is eventually
  consistent. There is no historical backfill of previous conversations.
- Names and raw contact details are excluded from analytics API responses and
  application logs. Aggregates remain test-only; do not treat them as sales.
- Records receive a 90-day TTL; deletion is asynchronous and backups may retain
  data longer. Point-in-time recovery is enabled. Stack deletion/replacement
  retains the table.
- Synthetic verification left one test contact-interest submission and two test
  visit requests using fictitious automation details. User activity may add more.
- Metric filters and CloudWatch dashboard track saved events plus function/API
  failures. No proactive notification destination is configured.

## Source map

| File | Responsibility |
| --- | --- |
| `bot.py` | Flask routes, signature validation, capture/send modes, submission APIs |
| `conversation.py` | Menu, property selection, rich cards and follow-up commands |
| `listings.py` | Catalog validation and factual listing answers |
| `lead_analytics.py` | Submission validation, idempotent saves, aggregate queries |
| `lambda_handler.py` | API Gateway v2 adapter; trusted external URL from request context |
| `import_listings.py` | CSV-to-JSON catalog import |
| `data/listings.json` | Current six-record demo catalog |
| `data/sample-property-listings.csv` | Current category-aware demo CSV |
| `template.yaml` | SAM infrastructure, scoped table/index permissions, monitoring |
| `Makefile` | Allowlisted Lambda packaging with Linux Python 3.12 dependencies |
| `automate_workflow.py` | Signed live webhook test plus CloudWatch response verification |
| `test_property_bot.py` | Webhook, listing, import, and Lambda tests |
| `test_conversation.py` | Menu, cards, follow-ups, capture and website test API tests |
| `test_lead_analytics.py` | Validation, privacy, aggregate and duplicate handling tests |

Website `dist/` contains `index.html`, `style.css`, `app.js`, `analytics.js`, and
three SVG architecture illustrations. Preserve the existing Sites source workflow.

## Verification at handoff

- **32 backend tests passed.**
- SAM build and template lint passed; AWS stack deployment completed.
- Live signed webhook capture and website menu/category/follow-up calls passed.
- Three browser conversation scenarios passed using a local preview proxy to
  the actual AWS test endpoint.
- Live lead/visit creation, duplicate suppression, aggregate counts, personal-data
  exclusion, and browser CORS checks passed.
- Browser form submission saved a synthetic visit request and displayed its
  pending-confirmation acknowledgement. Analytics rendering was visually checked.
- Private production-site browser automation was gated by sign-in; the user
  independently confirmed the website worked. Sites publication succeeded.

Run local tests from the application repository:

```bash
python3 -m unittest test_property_bot test_conversation test_lead_analytics -v
```

The system Python used during the session is 3.9; the deployed runtime is 3.12.
Temporary tool environments use bundled Python 3.12. Recheck dependencies and
Python paths rather than assuming all environments are interchangeable.

## Credentials and tools: do not print secrets

- Real `.env` in the application repository contains configuration/credentials.
  Do not print, copy into documentation, commit, or package it.
- AWS Secrets Manager secret name: `property-bot/twilio`, with `auth_token` and
  `account_sid` fields. Never fetch secret values into chat/tool output.
- CloudFormation resolves secret references into the Lambda environment.
- Default CLI credentials worked as IAM user `nova-reel-user`. User attached
  `AdministratorAccess`; verified API access succeeded. Do not change permissions
  without authorization. A scoped deployment role is a production action item.
- The attempted `property-bot` browser-login profile was not established or
  needed after default-user access was fixed. Verify identity before deployment.
- Temporary deployment tools are relative to the Codex working directory:
  `work/deploy-tools/bin/sam` and
  `work/awscli-unpacked/aws-cli.pkg/Payload/aws-cli/aws`.
- SAM source staging/build directories: `work/deployment-source`,
  `work/sam-build`, `work/sam-cache`; generated SAM local config:
  `work/sam-config` via `__SAM_CLI_APP_DIR`.
- Stage only allowlisted files; never recursively package the original repo's
  `.env` or Git history. Refresh staging/build files after source changes.
- Sites Git credentials are short-lived. Obtain a fresh credential for the
  existing project, keep it in tool memory, and send it to the source helper via
  hidden stdin. Never persist it in a file or echo it.
- Local preview servers started by the agent were stopped at handoff.

## Twilio blocker and production work remaining

The current trial rejected direct TwiML with `12300` and custom outbound message
bodies with `21654: ContentSid Required`. Switching XML content types did not
solve the trial limitation. Do not retry that as a proposed fix. Paid operation
requires sender setup and supported WhatsApp rendering, then explicit activation
of sending. Capture mode must remain safe for website automation.

The target architecture is documented, **not implemented in full**:

1. Twilio customer messages.
2. API Gateway.
3. Signature-validating ingress that durably accepts events.
4. SQS FIFO queue.
5. Conversation worker.
6. Persistent conversation/message state and deduplication.
7. Twilio send adapter.
8. Delivery-status callback processing.
9. Failed-message queue and controlled replay.
10. Monitoring, notification destinations, staging, aliases and rollback.

Do not describe the new lead table as fulfilling conversation state, queuing, or
outbound-delivery deduplication. Customer-message recovery, delivery callbacks,
staging, canary releases, and production API authentication remain work items.
The private tester's AWS APIs currently allow public test submissions and
aggregate reads with throttling; CORS is not authentication. Isolate/authenticate
them before production use. Visit request status editing and agent notification
are also not implemented.

## Documentation and cost decisions

- [Pilot architecture and detailed actions](PILOT-ARCHITECTURE.md)
- [Pay-per-use cost estimate](PILOT-COSTS.md)
- [Lead and visit analytics](LEAD-ANALYTICS.md)
- [Implemented conversation workflow](../WORKFLOW.md)
- [Deployment guide](../PROPERTY-BOT.md) — consolidated during repository cleanup.

The earlier planning estimate for 100 conversations/day, 30 days/month:
Twilio platform fees USD 60/120/180 at 2/4/6 exchanges per conversation, plus an
AWS allowance of USD 5–20/month. Meta fees, phone rental, taxes, website/domain,
and production implementation are additional. Not an actual bill or quote;
refresh provider pricing and include the latest monitoring/storage configuration
before committing to a budget. No paid Twilio upgrade was performed.

## Repository status and next-session starting point

Application changes include pre-existing and new uncommitted work. The user
subsequently requested a roadmap documentation push, then repository cleanup
and a commit of the application code. Verify Git history and remote state for
the outcome; a local code commit does not imply a GitHub push. Sites publication separately committed/pushed its
website source through the Sites helper; that is not a commit to the application
repository.

The [product roadmap](../PRODUCT-ROADMAP.md) proposes a 9 November 2026 kickoff
and a six-week plan through 18 December. Dates are assumptions, not an agreed
start or delivery commitment. Production exit checks currently begin at 0%.

For the next session:

1. Read this note, `git status`, current source, and the tracked Sites manifest.
2. Confirm AWS identity, region and deployed state without exposing secrets.
3. Ask which next feature the user wants, or follow their explicit next request.
4. Keep the POC capture-only unless sending/paid setup is explicitly authorized.

## Repository cleanup follow-up

The later cleanup removed the obsolete Meta/unsigned manual test scripts,
placeholder Node manifest, duplicate BOT-README, canned-reply editor, and unused
conversation logger. README and PROPERTY-BOT are the current entry points.
Configuration examples contain placeholders only. See Git history for the code
commit; no AWS or Sites deployment is implied by cleanup.
