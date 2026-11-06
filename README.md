# Shraddha Properties WhatsApp Bot

A Python POC for property discovery, rich conversation previews, and test lead
and site-visit analytics. The AWS deployment runs in Sydney (`ap-southeast-2`).
The [private Bot Lab](https://shraddha-bot-lab.swathiganti392.chatgpt.site) exercises
the same conversation engine through a dedicated test API.

## Implemented

- Signed Twilio incoming-message validation and capture-only processing.
- Villas, Apartments, and Office Space menus with six fictional sample listings.
- Structured property cards and brochure, price, location, and visit follow-ups.
- Consent-based website test lead and visit-request storage in DynamoDB.
- Aggregate 7/30-day analytics and a CloudWatch monitoring dashboard.
- AWS SAM infrastructure and automated local/live workflow verification.

The current POC does not send WhatsApp responses, confirm visits, notify agents,
or persist conversation sessions. Production queues, delivery tracking, durable
message deduplication, and operational hardening are planned in the roadmap.

## Local setup

Use Python 3.12 to match AWS Lambda:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Use `.env.example` as a configuration reference. The application does not load
`.env` automatically: export settings through your shell or process manager.
Never commit credentials. Use AWS profiles/roles rather than putting access keys
in example files. Keep `REPLY_TRANSPORT=capture` for safe POC testing.

```bash
make test
python bot.py
```

The local Flask server uses port 5001. `POST /test/workflow` can be exercised
without Twilio sending credentials:

```bash
curl http://127.0.0.1:5001/test/workflow \
  -H 'Content-Type: application/json' \
  -d '{"message":"Hi"}'
```

Incoming Twilio webhooks require `TWILIO_AUTH_TOKEN` and the exact public
`TWILIO_WEBHOOK_URL`. Local lead APIs also require `LEADS_TABLE` and appropriate
AWS permissions. Unit tests mock storage; they do not send messages or need live
AWS access.

## Listing updates

Edit the current CSV, preserving its headers and `property_type` column:

```bash
python import_listings.py data/sample-property-listings.csv
make test
```

Imports validate before replacing `data/listings.json`. Replace every fictional
row before importing with `--real-data`. Rebuild/redeploy to refresh the Lambda
catalog; it does not directly read a live spreadsheet.

## Endpoints

| Route | Purpose |
| --- | --- |
| `GET /health` | Basic health response |
| `POST /webhook/whatsapp` | Signed Twilio incoming messages |
| `POST /test/workflow` | Demo workflow simulation; never sends messages |
| `POST /test/leads` | Save a consented test contact-interest or visit request |
| `GET /test/analytics?days=7` | Aggregate test submissions; supports 7 or 30 days |

The private website and its AWS test API have separate access boundaries. The
POC API permits public test submissions and aggregate reads with throttling.
CORS is not authentication. Protect/isolate these routes before production use.

## Repository layout

| File | Responsibility |
| --- | --- |
| `bot.py` | Flask routes, webhook validation, capture/send adapters |
| `conversation.py` | Menu and rich response generation |
| `listings.py` | Catalog validation and factual listing answers |
| `lead_analytics.py` | Submission validation, idempotent saves, aggregate queries |
| `lambda_handler.py` | API Gateway v2 to Flask adapter |
| `import_listings.py` | CSV catalog importer |
| `automate_workflow.py` | Opt-in live capture-mode verification |
| `test_*.py` | Local unit/integration tests |
| `template.yaml`, `Makefile` | SAM infrastructure and allowlisted packaging |
| `data/` | Fictional demo catalog and CSV |

The website source is maintained in a separate Sites repository. Its project and
checkout details are recorded in the session handoff; no Node application or
package manifest is needed in this Python backend repository.

## Documentation

- [Product Roadmap](PRODUCT-ROADMAP.md): weekly timelines, progress bars, and go-live checks.
- [Deployment Guide](PROPERTY-BOT.md): local configuration, AWS build/deployment, and verification.
- [Conversation Workflow](WORKFLOW.md): implemented menu and capture-mode behavior.
- [Pilot Architecture](docs/PILOT-ARCHITECTURE.md): proposed reliability pipeline and detailed actions.
- [Pilot Costs](docs/PILOT-COSTS.md): pay-per-use assumptions, estimates, and exclusions.
- [Lead Analytics](docs/LEAD-ANALYTICS.md): submission definitions, privacy, retention, and monitoring.
- [Session Handoff](docs/RESUME.md): deployment identifiers and resumption context.
- [Original Platform Concept](ARCHITECTURE.md): broader future marketing-platform design, not deployed functionality.
