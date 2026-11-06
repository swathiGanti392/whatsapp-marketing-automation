# Pilot lead and site-visit analytics

The Bot Lab has a **Leads & visits** view. It reports explicit website test
submissions saved in DynamoDB in Sydney. Property browsing and merely opening
the visit form do not count as leads. Tracking begins with this deployment;
historical messages are not imported or inferred as contacts.

## Submit and inspect

1. Open a property card in the conversation playground.
2. Choose **Interested? Request contact** to submit contact interest, or
   **Plan a site visit** to submit a preferred date with contact details.
3. Supply a name, valid email/phone, and consent to storage.
4. Open **Leads & visits** and choose 7 or 30 days, then Refresh.
5. Export the aggregate JSON summary when needed.

The browser generates a unique submission ID. A retry with the same ID and
matching request data returns the existing outcome instead of counting a second
submission. Two deliberately separate submissions count separately, even if the
contact is the same. Unique contacts are counted using a normalized contact
hash, so a person using different email/phone identities can count separately.

## Definitions

| Metric | Meaning |
| --- | --- |
| Contact interests | Successfully saved contact-interest forms |
| Visit requests | Successfully saved visit-preference forms |
| Unique contacts | Distinct normalized contact identifiers across both types |
| Visits pending | Visit requests awaiting confirmation |
| Requests by day | Contact interests plus visit requests by UTC calendar date |
| Property interest | Saved submissions grouped by property ID |

Windows are 7 or 30 UTC calendar days, including today. The date index is
eventually consistent; new saves may take a few seconds to appear. These counts
are not conversion rates, completed sales, confirmed appointments, or WhatsApp
delivery statistics. No agent is notified by submitting a test form.

## API and storage

- `POST /test/leads`: validates and saves a test lead or visit request.
- `GET /test/analytics?days=7` (or `30`): returns aggregate test counts only.
- The API forces `source=web_test`; clients cannot label submissions as production.
- Contact details are stored in the private DynamoDB table, not returned by the
  analytics API or written to application logs.
- The date index projects only fields needed for aggregation, excluding names
  and raw contact details.
- IAM permits the function to put/get table records and query the specific
  date index; no table-wide administrative access is added.
- Records receive a 90-day TTL. Actual TTL deletion is asynchronous. Backups can
  retain records longer; review data-retention requirements before collecting
  real customer information.
- Point-in-time recovery is enabled. The table is retained if the stack is
  deleted or the resource is replaced.
- Frontend hosting remains private. The demo API permits public submissions and
  aggregate reads with existing API throttling; CORS is not authentication.
  Keep this test-only. Authenticate/isolate the API before production analytics
  or exposing sensitive customer operations.

## AWS monitoring

CloudWatch dashboard **property-whatsapp-bot-leads** shows saved lead/visit events,
Lambda errors/throttles, and API 5xx failures. Metric filters count new
`lead_saved` log events; they do not backfill history and are operational event
counts. DynamoDB aggregation is the source for the website's saved-submission
counts. No contact details become metric dimensions or dashboard labels.

No email/SMS/Slack alert destination is configured by this change. Choose an
approved notification destination before expecting proactive alerts.

## Validation

Tests cover contact/consent/date validation, separate lead and visit counts,
unique-contact counts, exclusion of personal fields from summaries, duplicate
submissions, invalid date windows, and storage failures that must not report
success. Live verification uses clearly fictitious automation contact details;
those sample records are included as test activity.

The existing WhatsApp workflow remains capture-only. Automatic WhatsApp lead
qualification, agent follow-up, booking confirmation, production delivery
analytics, and status-editing workflows are future extensions.
