# PII Redaction

- Prefer synthetic or anonymized datasets for development and demos.
- Apply redaction rules before exporting evidence bundles outside approved boundaries.
- Use `scripts/redact_artifacts.py` to scrub PII when required.
- Document `pii_handling` in each `manifest.json` (none / minimized / redacted / approved-egress).
