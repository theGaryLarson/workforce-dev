# Data Classification

All datasets and artifacts must declare a classification:

- **Public**: safe to share externally.
- **Internal**: non-public but not sensitive.
- **Confidential**: partner data; limited distribution.
- **Restricted**: contains PII/PHI or regulated data; requires explicit egress approval.

When in doubt, treat data as **Restricted** and document handling in run manifests.
