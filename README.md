# LeadOps — B2B Lead Qualification Automation

A **local-first, explainable lead intake pipeline** for SDR and RevOps workflows. It validates incoming CSV records, de-duplicates contacts, scores leads against a configurable ideal customer profile, and routes each lead to the next action.

This version is deliberately **deterministic automation, not a machine-learning model**. The scored baseline is useful for comparing against an optional future LLM enrichment step without pretending that rules are AI.

## Quick start (Python 3.10+; no runtime dependencies)

```bash
python -m leadops.cli --input examples/leads.csv --output decisions.json
python -m unittest discover -s tests -v
```

The command writes machine-readable JSON with qualified leads, routing decisions, and invalid-row diagnostics. No leads leave your machine. The example input is synthetic.

## Business use case

A small sales team uploads a CSV from its CRM. Rather than manually checking every lead, LeadOps produces:
- validated, normalized records with duplicate suppression
- a transparent 0–100 ICP score with reasons for each point allocation
- HOT (sales), WARM (nurture), or COLD (research) routing
- row-level errors to repair malformed input rather than silently losing it

**Not included:** scraping, buying leads, email sending, autonomous outreach, external enrichment, or API keys.

## Architecture

`CSV → parsing & validation → duplicate detection → ICP scoring → action routing → JSON report`

`leadops/core.py` contains the business logic; `leadops/cli.py` is the operator interface. The scoring weights are intentionally visible and easy to replace. This is a simple proof-of-value portfolio project, not a predictive conversion model.

## Example

```bash
python -m leadops.cli --input examples/leads.csv
```

## Next iterations

1. Integrate a CRM API with scoped credentials and opt-in data handling.
2. Add FastAPI endpoints and a queue with idempotency guarantees.
3. Compare the baseline with a human-reviewed ML/LLM classifier; log disagreement.
4. Add an analytics dashboard: response time, hand-off rate, conversion by segment.
5. Add data retention, access controls, and audit logs before production deployment.

## Privacy and limitations

Emails are personal data: use only with lawful access. JSON exports contain the submitted contact emails, so store and share them securely. Scoring is a configurable business policy, **not evidence of purchase intent or a claim about an individual**. Do not use it to make sensitive eligibility decisions.

## License

MIT. See `LICENSE`.
