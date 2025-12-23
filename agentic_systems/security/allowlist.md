# Allowlist Guidance

List approved tools, vendors, and data egress channels here. Any platform not listed
requires explicit approval before processing Confidential or Restricted data.

- Example entries: Azure Key Vault, GitHub Actions secrets, approved storage buckets.

## LLM Platform Integration (Part 2 POC)

- **OpenAI API** - Approved for POC with Internal data classification only. Requires `egress_approval_ref` in manifest for Restricted data.
- **Anthropic API** - Approved for POC with Internal data classification only. Requires `egress_approval_ref` in manifest for Restricted data.

**Note**: LLM platforms receive metadata only (file names, sizes, column names, error counts, types) - no raw participant data, no PII, no field values per BRD Section 2.3. This ensures "redacted" PII handling.
