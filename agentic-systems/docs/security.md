# Security and Evidence Handling

- Do not commit secrets; use approved secret storage.
- Declare `data_classification` and `pii_handling` in run manifests.
- Redact artifacts when required and store sanitized evidence in `core/audit/runs/`.
