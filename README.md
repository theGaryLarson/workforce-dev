# CFA Applied Agentic AI — Production Repository Scaffold (v2.1)
## Platform-Agnostic, Governance-First, Evaluation-Ready, Security & Privacy-Aware

This repository is the **single authoritative production system of record** for all work produced in the Applied Agentic AI program.

Sandbox experimentation, vendor consoles, and external tooling may be used during development, but **all work must be promoted into this repository**—with full evidence—to be considered complete.

---

## Core Design Principles

### 1. Platform-Agnostic Core
- Deterministic business logic lives exclusively in `core/`
- No agent framework or vendor platform code is allowed in `core/`
- The core must remain portable, testable, and rerunnable without AI services

### 2. Agents Orchestrate, Tools Execute
- Agents are responsible for:
  - Planning
  - Tool invocation
  - State tracking
  - Human-readable explanation
- Tools perform **all data transformations and side effects**
- Agents may not silently modify data

### 3. Stable Contracts Enable Comparison
- All agents must conform to a shared **BaseAgent contract**
- Vendor agent platforms are adapted to this contract
- This enables side-by-side evaluation of **agent platforms**, not demos

### 4. Auditability Is Non-Negotiable
- Every run produces inspectable artifacts
- All decisions must be explainable after the fact
- Reruns must be safe, bounded, and comparable

### 5. The Repository Is the System of Record
- Vendor UIs and consoles may assist execution
- They may **not** be the source of truth
- The repository must contain everything required to understand, evaluate, and justify a run

### 6. Security & PII Controls Are Mandatory
- Treat partner and learner data as **sensitive by default**
- Never paste sensitive data into third-party tools or LLM prompts unless explicitly approved and documented
- Secrets are never committed; use approved secret storage (e.g., Azure Key Vault / GitHub Actions secrets)
- Evidence artifacts must be **sanitized** when required (redaction, hashing, minimization)
- Enforce least privilege for credentials and service principals
- All runs must declare their data classification and sanitization status

---

## Repository Structure

```
agentic_systems/
├── core/                       # Deterministic, platform-agnostic logic
│   ├── canonical/              # CDM + canonicalization logic
│   ├── ingestion/              # Partner file ingestion
│   ├── validation/             # Business rule enforcement
│   ├── reconciliation/         # WSAC reconciliation logic
│   ├── exports/                # WSAC & Dynamics exports
│   └── audit/                  # System-of-record evidence
│       ├── runs/               # One directory per agent run
│       └── evidence.py         # Evidence validation helpers
│
├── agents/                     # Orchestration layer
│   ├── base_agent.py           # Shared agent contract
│   ├── intake_agent.py         # Platform-agnostic wrapper
│   ├── reconciliation_agent.py
│   ├── export_agent.py
│   └── platforms/              # Vendor agent platform adapters
│       ├── microsoft/
│       │   └── intake_impl.py
│       ├── openai/
│       │   └── intake_impl.py
│       ├── anthropic/
│       │   └── intake_impl.py
│       └── minimal/
│           └── intake_impl.py
│
├── security/                   # Security, privacy, and compliance utilities
│   ├── data-classification.md  # Definitions: public/internal/confidential/restricted
│   ├── pii-redaction.md        # Redaction rules and examples
│   ├── threat-model.md         # Lightweight threat model + mitigations
│   └── allowlist.md            # Approved tools, vendors, and data egress rules
│
├── scripts/
│   ├── redact_artifacts.py     # Scrub PII from evidence bundles (when required)
│   └── verify_no_secrets.py    # Local preflight checks (optional)
│
├── clients/
│   └── cfa/
│       ├── client_spec.yaml    # CFA-specific configuration
│       ├── rules.py            # Reporting rules
│       └── mappings.py         # External system mappings
│
├── cli/
│   └── main.py                 # CLI entrypoint & run coordinator
│
├── tests/                      # Unit + integration tests
│
├── docs/
│   ├── architecture.md
│   ├── trace-format.md
│   ├── runbook.md
│   ├── platform-comparison.md
│   ├── evaluation-rubric.md
│   └── security.md             # How to handle secrets, PII, and evidence
│
└── README.md
```

---

## Data Classification & PII Handling (Program Standard)

All datasets and run artifacts must be labeled as one of:

- **Public**: safe to share externally
- **Internal**: non-public but not sensitive
- **Confidential**: partner data; limited distribution
- **Restricted**: contains PII/PHI or regulated data

Rules:
- **Restricted data must never be sent to third-party LLMs/tools** unless explicitly approved and documented in the run manifest.
- Prefer **synthetic or anonymized datasets** for development and demonstration.
- When in doubt, treat data as **Restricted**.

---

## Secrets & Credentials

- Do not commit secrets (`.env`, keys, tokens, connection strings).
- Store secrets in approved systems (e.g., Azure Key Vault, CI secret manager).
- Provide `.env.example` with placeholders only.
- Use least privilege credentials with short-lived access where possible.
- Rotate credentials immediately if leakage is suspected.

---

## Evidence Bundle (Required for Every Run)

Every agent run—whether executed locally, via SDK, or in a vendor console—must produce an **Evidence Bundle** stored under:

```
core/audit/runs/<run-id>/
```

Each Evidence Bundle must include:

- `manifest.json`
  - platform name and version
  - execution mode (CLI / SDK / console)
  - **data_classification** (Public / Internal / Confidential / Restricted)
  - **pii_handling** (none / minimized / redacted / approved-egress)
  - inputs, configuration references, timestamps
  - **egress_approval_ref** (required if any Restricted data leaves approved boundaries)
- `plan.md`
  - the explicit agent plan shown before execution
- `tool_calls.jsonl`
  - ordered record of tool invocations, inputs, outputs, and status
  - PII must be minimized; if present, the bundle must be marked accordingly
- `outputs/`
  - generated CSVs, worksheets, and export packages
- `summary.md`
  - staff-facing explanation of what happened and why
  - include references to validation, exceptions, and approvals (if applicable)
- `vendor_export/` (optional)
  - raw exports from vendor consoles, if available

Runs missing required evidence are **invalid**.

---

## Platform Selection via CLI

The CLI coordinates execution and validation of agent runs.

```bash
agent run intake --platform microsoft --partner X --quarter Q2
```

Depending on the platform:
- The CLI may execute agents directly
- Or prepare inputs and validate exported evidence from a vendor console

In all cases, the CLI validates that a complete Evidence Bundle exists before marking a run successful.

---

## Security Preflight (Recommended)

Before any run that touches Confidential or Restricted data:

- Verify no secrets are present in the working tree
- Ensure the platform/tool is listed in `security/allowlist.md`
- Ensure the run manifest includes `data_classification` and `pii_handling`
- Redact artifacts when required using `scripts/redact_artifacts.py`

---

## Evaluation Readiness

This scaffold enables end-of-program evaluation by enforcing:

- Identical inputs across platforms (or equivalently anonymized inputs)
- Stable agent contracts
- Comparable Evidence Bundles
- Clear separation between orchestration and execution

**Vendor agent platforms are evaluated on:**
- Contract compliance
- Auditability and trace completeness
- Determinism and rerun safety
- Debuggability and cognitive load
- Governance and lock-in risk
- Long-term operational fit for CFA

---

## Completion Rule (Hard Gate)

Work is **not complete** unless it:

- Produces a valid Evidence Bundle in `core/audit/`
- Declares `data_classification` and `pii_handling` in the run manifest
- Uses deterministic tools in `core/`
- Conforms to the BaseAgent contract
- Runs or validates end-to-end via the CLI
- Passes required tests
- Passes required security checks (no secrets committed; artifacts sanitized when required)
- Lives entirely in this repository

Vendor consoles may assist execution,  
but **this repository is the final authority**.
