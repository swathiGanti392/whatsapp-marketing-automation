# Production pilot: pay-per-use cost estimate

Estimate prepared on 6 November 2026 for Shraddha Properties, using up to
100 conversations per day and a single-region AWS deployment in Sydney
(`ap-southeast-2`). These are planning estimates, not a provider quote or an
analysis of actual account charges. The proposed reliability components in the
[pilot architecture plan](PILOT-ARCHITECTURE.md) are not all deployed yet.

## Monthly estimate

Assumptions:

- 100 conversations per day over a 30-day month: 3,000 conversations.
- One exchange means one customer message plus one bot response.
- Every inbound and outbound WhatsApp message counts separately.
- Twilio's published Pay-as-you-go platform fee is USD 0.005 per inbound or
  outbound WhatsApp message, as checked on the estimate date.
- Meta fees, number charges, taxes, implementation work, and website/domain
  costs are excluded from the base totals below.
- AWS infrastructure receives a USD 5–20/month planning allowance, described
  below. No free-tier eligibility or promotional credits are assumed.

| Conversation length | Total messages per conversation | Messages per month | Twilio platform fee | AWS allowance | Base monthly estimate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Short: 2 exchanges | 4 | 12,000 | USD 60 | USD 5–20 | **USD 65–80** |
| Typical: 4 exchanges | 8 | 24,000 | USD 120 | USD 5–20 | **USD 125–140** |
| Longer: 6 exchanges | 12 | 36,000 | USD 180 | USD 5–20 | **USD 185–200** |

These are base estimates, not all-inclusive totals. For a typical pilot, budget
USD 125–140/month **plus Meta fees, applicable number charges, and taxes**.

## Calculation

```text
Monthly conversations = conversations/day × days/month
Monthly messages      = monthly conversations × exchanges/conversation × 2
Twilio platform fee   = monthly messages × USD 0.005
Base monthly estimate = Twilio platform fee + AWS allowance
```

Example: 100 × 30 × 4 × 2 = 24,000 messages; 24,000 × USD 0.005 = USD 120
in Twilio platform fees. Adding the AWS allowance gives USD 125–140 before the
additional charges listed below.

Sending an image, brochure, or follow-up as a separate message increases the
message count. Count actual outbound message objects rather than assuming that
every user input always generates exactly one response. Retries, failures,
provider-specific processing fees, and additional testing can also affect the
bill; verify applicable terms before launch.

## Twilio and Meta

Use Twilio's standard Pay-as-you-go option for the pilot; an enterprise contract
is not assumed in this estimate. Paid WhatsApp testing also requires completing
the supported sender setup. Do not assume the current trial number will become
the permanent business sender.

Meta charges are passed through separately and depend on message category,
destination country, and the current rate card. Do not assume that operating
within the 24-hour customer-service window eliminates every Meta charge.
Recalculate against the actual recipient countries and planned message types
before approving a final budget. No specific Meta amount has been included here.

An eligible existing number may be registered, or a Twilio number may be
purchased subject to sender requirements. Include rental where applicable.

## AWS infrastructure allowance

USD 5–20/month is a planning allowance, **not an itemized Sydney-region pricing
calculation**. It assumes low pilot traffic, small records, modest log retention
and media downloads, and the following single-region components:

| Component | Usage covered by the allowance |
| --- | --- |
| API Gateway | Inbound webhooks, delivery callbacks, and limited test traffic |
| Lambda | Ingress validation, conversation processing, and callback handling |
| SQS | Queue processing and a failed-message queue |
| Conversation-state database | Small session, deduplication, and delivery records |
| Secrets Manager | Bot credentials and low request volume |
| CloudWatch | Modest logs, metrics, alarms, and notifications |
| Object storage | Small catalog/media footprint and modest brochure downloads |

Free allowances and credits may reduce charges, but should not be required for
the business budget to work. Re-estimate if adding substantial media traffic,
frequent synthetic tests, extensive logs, advanced monitoring, additional
environments, network appliances/NAT, or multi-region infrastructure.

The POC is not guaranteed to be free: AWS resources can incur charges even while
Twilio remains on a free trial or outbound WhatsApp delivery is disabled.

## Additional and excluded costs

| Item | Budget treatment |
| --- | --- |
| Meta messaging fees | Additional; verify category and destination-specific rates |
| Business phone number | Additional rental if applicable to the selected number |
| Taxes and currency conversion | Additional according to billing location and payment method |
| Production implementation | One-time engineering effort; not an operating-usage charge |
| Website hosting and domain | Separate from this backend estimate; review existing tester hosting terms separately |
| Paid support plans | Not included |
| AI model usage | None in the current rules-based bot; estimate separately if an LLM is added |

The production implementation effort includes durable queuing, state and
deduplication, delivery callbacks, WhatsApp media/buttons, access controls,
staging, monitoring, and safe rollout/rollback. This document does not price that
engineering work.

## Pilot cost controls and validation

1. Set separate AWS and Twilio spending notifications before enabling sends.
   Alerts notify; do not assume they impose a hard spending cap.
2. Keep automated website tests in capture-only mode.
3. Measure actual inbound/outbound message counts and conversation length during
   the first pilot week, then project a monthly total.
4. Separate Meta fees, Twilio platform fees, number rental, and AWS costs when
   reviewing the bill.
5. Review logging volume and retention, media download volume, and retries.
6. Recalculate using current provider rates and actual usage before expanding.

## Sources and refresh

- [Twilio WhatsApp pricing](https://www.twilio.com/en-us/whatsapp/pricing)
- [Twilio WhatsApp sender registration](https://www.twilio.com/docs/whatsapp/self-sign-up)
- [Twilio trial restrictions](https://www.twilio.com/docs/usage/trials/try-out-whatsapp)
- [AWS Pricing Calculator](https://calculator.aws/)
- [AWS Lambda pricing](https://aws.amazon.com/lambda/pricing/)
- [Amazon API Gateway pricing](https://aws.amazon.com/api-gateway/pricing/)
- [Amazon SQS pricing](https://aws.amazon.com/sqs/pricing/)
- [AWS Secrets Manager pricing](https://aws.amazon.com/secrets-manager/pricing/)
- [Amazon CloudWatch pricing](https://aws.amazon.com/cloudwatch/pricing/)

Refresh this estimate whenever message rates, destination mix, conversation
length, architecture, or provider pricing changes. Update the estimate date and
retain explicit assumptions rather than presenting the range as a fixed fee.
