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
2. Add a durable queue with idempotency guarantees behind the local FastAPI adapter.
3. Compare the baseline with a human-reviewed ML/LLM classifier; log disagreement.
4. Add an analytics dashboard: response time, hand-off rate, conversion by segment.
5. Add data retention, access controls, and audit logs before production deployment.

## Privacy and limitations

Emails are personal data: use only with lawful access. JSON exports contain the submitted contact emails, so store and share them securely. Scoring is a configurable business policy, **not evidence of purchase intent or a claim about an individual**. Do not use it to make sensitive eligibility decisions.

## License

MIT. See `LICENSE`.


## Local FastAPI demo

The HTTP adapter reuses the scoring policy; it does not call a model. Python 3.11+:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m uvicorn leadops.api:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs and try `POST /v1/qualify`:

```json
{"leads":[{"name":"Ana","email":"ana@example.com","company":"Example","industry":"SaaS","company_size":50,"job_title":"VP Sales","source":"inbound"}]}
```

Expected: one decision scoring 100, segment HOT, action sales_review. The API
accepts 1–100 records per request, trims strings, rejects extra fields and invalid
sizes, and deduplicates normalized emails within the batch (first record wins).
Invalid batches return 422 atomically. Error responses omit submitted values.
Repeated requests compute the same result; there is no durable queue or CRM write,
so no claim of cross-request exactly-once delivery is made. CSV intake retains its
row-level error behavior; API intake uses all-or-nothing schema validation.

Run `python -m unittest discover -s tests -v` after installing dependencies.
The manual CI workflow is configured for both interfaces on Python 3.11 and 3.13. No network calls are needed
by tests. The uninstalled CLI still uses only Python's standard library.

### Deployment boundary

This is a local portfolio service, not a public production deployment. Bind only
to loopback. Before exposing it, add authentication, TLS, request-byte limits at
the ingress, rate limits, access controls and a data-retention policy. Field and
batch bounds are schema validation, not a transport-level body-size limit.
Responses contain contact data; do not log bodies. There are no sending tools.

### CI cost control

This repository is private. The workflow is manual-only (`workflow_dispatch`)
to avoid consuming paid Actions minutes without budget approval. It is not
automatically triggered by pushes or pull requests. Local checks run the same
commands. Enable automatic PR triggers after confirming free quota or a free runner.
