# Threat Model

This scaffold assumes sensitive partner data:

- **Risks**: data leakage to third-party LLMs, improper access controls, untracked egress.
- **Mitigations**:
  - Enforce least-privilege credentials and avoid committing secrets.
  - Require data classification and PII handling in run manifests.
  - Capture full evidence bundles to support audits and reruns.
  - Keep deterministic business logic in `core/` to enable reproducibility.
