# CFA Applied Agentic AI — Production Repository

## Platform-Agnostic, Governance-First, Evaluation-Ready, Security & Privacy-Aware

This repository is the **single authoritative production system of record** for all work produced in the Applied Agentic AI program.

Sandbox experimentation, vendor consoles, and external tooling may be used during development, but **all work must be promoted into this repository**—with full evidence—to be considered complete.

---

## Setup

### Prerequisites

- **Python 3.10+** (3.11 or 3.12 recommended)
- **uv** - Fast Python package installer and resolver ([installation instructions](https://github.com/astral-sh/uv#installation))

### Installation

1. **Install uv** (if not already installed):

   *Windows (PowerShell):*
   ```powershell
   # Using PowerShell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   *Linux/macOS (Bash):*
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the repository**:

   ```bash
   git clone https://github.com/theGaryLarson/workforce-dev.git
   cd cfa-applied-agentic-ai
   ```

3. **Install dependencies**:

   ```bash
   uv pip install -r requirements.lock
   ```

   Or sync the environment:

   ```bash
   uv pip sync requirements.lock
   ```

4. **Environment setup** (optional):

   Create a `.env` file in the repository root for local configuration:

   ```bash
   # .env
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4o-mini
   ```

   Copy from `.env.example` for a template:

   ```bash
   cp .env.example .env
   # Then edit .env with your actual API keys
   ```

5. **Verify installation**:

   Run tests to verify the setup:

   ```bash
   uv run pytest agentic_systems/tests/ -v
   ```

### Running the CLI

The CLI can be run using `uv`:

```bash
uv run python -m agentic_systems.cli.main <command>
```

---

## Architecture

### Core Design Principles

1. **Platform-Agnostic Core**: Deterministic business logic lives exclusively in `core/` with no vendor platform dependencies
2. **Agents Orchestrate, Tools Execute**: Agents coordinate workflows; tools perform all data transformations
3. **Stable Contracts**: All agents conform to the `BaseAgent` contract for side-by-side platform evaluation
4. **Auditability**: Every run produces inspectable evidence bundles with complete decision trails
5. **Repository as System of Record**: Vendor UIs assist but never replace repository artifacts
6. **Security & PII Controls**: Mandatory data classification, PII handling, and sanitization

### Agents

#### OrchestratorAgent

Coordinates the intake workflow, detects partner file uploads from partner-specific subfolders, manages HITL pauses, and resumes processing when corrected files are uploaded.

- **Purpose**: Orchestrates the complete intake workflow with file detection and HITL integration
- **Tools Used**: 
  - Uses `SimpleIntakeAgent` internally for data processing
  - Special orchestration tools: `inspect_run_status`, `wait_for_partner_correction`, `wait_for_initial_upload`
- **Key Features**:
  - File system monitoring (watchdog) for partner uploads in partner-specific subfolders
  - Partner detection from file path (extracts partner name from `sharepoint_simulation/uploads/{partner_name}/` structure)
  - Content signature matching for file detection
  - Resume state management for HITL workflows
  - SharePoint simulation at repo root (`agentic_systems/sharepoint_simulation/`) with simplified structure
  - Watches `sharepoint_simulation/uploads/` recursively for both initial files and corrected files

#### SimpleIntakeAgent

Processes partner data through the complete intake pipeline: ingestion → validation → canonicalization.

- **Purpose**: Core intake agent that processes partner files end-to-end
- **Tools Used**:
  - `IngestPartnerFileTool` - Loads and parses partner files (CSV/Excel) using partner-specific parsing configurations
  - `ValidateStagedDataTool` - Validates data against shared business rules (client-level validation rules)
  - `CanonicalizeStagedDataTool` - Transforms validated data to canonical format using shared canonical mappings
- **Partner Communication Tools** (HITL workflow):
  - `CollectWSACAggregatesTool` - Collects WSAC aggregate data for comparison
  - `GeneratePartnerErrorReportTool` - Generates Excel error reports with comments
  - `GeneratePartnerEmailTool` - Generates partner notification emails
  - `CreateSecureLinkTool` - Creates secure access links for error reports
  - `RequestStaffApprovalTool` - Requests staff approval for validation exceptions
  - `UploadSharePointTool` - Uploads files to SharePoint simulation folders (partner-based organization)
- **Partner-Specific Configuration**:
  - Each partner has a parsing configuration at `clients/cfa/partners/{partner_name}/parsing_config.yaml`
  - Parsing configs map partner-specific file formats (column names, date formats, file structure) to canonical schema
  - Validation rules and canonical mappings remain shared at client level (`clients/cfa/rules.py` and `clients/cfa/client_spec.yaml`)

#### ReconciliationAgent

Reconciles canonical data with WSAC prior-quarter authoritative records to identify discrepancies.

- **Purpose**: Reconciles canonical participant data with WSAC records
- **Tools Used**:
  - `LoadWSACDataTool` - Loads WSAC prior-quarter data
  - `ReconcileParticipantsTool` - Matches and reconciles participants
- **Status**: Implementation pending

#### ExportAgent

Generates validated export files for WSAC bulk upload and Dynamics import.

- **Purpose**: Creates export files in WSAC and Dynamics formats
- **Tools Used**:
  - `GenerateWSACExportTool` - Generates WSAC bulk upload CSV (camelCase, ISO dates)
  - `GenerateDynamicsExportTool` - Generates Dynamics import CSV (special field names, MM/DD/YYYY dates)
  - `ValidateWSACExportTool` - Validates WSAC export format
- **Status**: Implementation pending

### Repository Structure

```
agentic_systems/
├── partner_uploads/            # Partner file uploads
│   ├── test-partner-1/         # Partner 1 uploads
│   └── test-partner-2/         # Partner 2 uploads
│
├── sharepoint_simulation/       # SharePoint simulation (repo root)
│   ├── uploads/                # Partner uploads for corrected files
│   │   ├── test-partner-1/     # Partner 1 corrected files
│   │   └── test-partner-2/     # Partner 2 corrected files
│   ├── partner_accessible/      # Partner-accessible reports
│   │   ├── test-partner-1/     # Partner 1 reports
│   │   └── test-partner-2/     # Partner 2 reports
│   └── internal/               # Internal staff review (run-based)
│
├── core/                       # Deterministic, platform-agnostic logic
│   ├── canonical/              # CDM + canonicalization logic
│   ├── ingestion/              # Partner file ingestion
│   ├── validation/             # Business rule enforcement
│   ├── reconciliation/         # WSAC reconciliation logic
│   ├── exports/                # WSAC & Dynamics exports
│   ├── partner_communication/  # HITL partner communication tools
│   └── audit/                  # System-of-record evidence
│       ├── runs/               # One directory per agent run
│       └── evidence.py        # Evidence validation helpers
│
├── agents/                     # Orchestration layer
│   ├── base_agent.py          # Shared agent contract
│   ├── orchestrator_agent.py  # Orchestrates intake workflow
│   ├── simple_intake_agent.py # Core intake agent
│   ├── reconciliation_agent.py # Reconciliation agent
│   ├── export_agent.py        # Export agent
│   └── platforms/              # Vendor agent platform adapters
│       ├── minimal/
│       ├── langchain/
│       ├── openai/
│       └── anthropic/
│
├── security/                   # Security, privacy, and compliance utilities
│   ├── data-classification.md # Definitions: public/internal/confidential/restricted
│   ├── pii-redaction.md        # Redaction rules and examples
│   ├── threat-model.md        # Lightweight threat model + mitigations
│   └── allowlist.md            # Approved tools, vendors, and data egress rules
│
├── clients/
│   └── cfa/
│       ├── partners/           # Partner-specific configurations
│       │   ├── test-partner-1/
│       │   │   └── parsing_config.yaml  # Partner 1 parsing config
│       │   └── test-partner-2/
│       │       └── parsing_config.yaml  # Partner 2 parsing config
│       ├── client_spec.yaml   # Shared canonical mappings
│       └── rules.py           # Shared validation rules
│
├── cli/
│   └── main.py                 # CLI entrypoint & run coordinator
│
├── tests/                      # Unit + integration tests
│
└── docs/
    ├── prd-trd.md             # Product/Technical Requirements Document
    └── brd.md                  # Business Requirements Document
```

---

## Workflow and CLI Commands

### Orchestrator Command

The orchestrator watches for partner file uploads and manages the complete intake workflow, including HITL pauses and resume processing.

*Windows (PowerShell):*
```powershell
uv run python -m agentic_systems.cli.main orchestrate intake `
  --partner <partner> `
  --quarter <quarter> `
  --platform <platform> `
  [--sharepoint-sim-root <path>] `
  [--poll-interval <seconds>]
```

*Linux/macOS (Bash):*
```bash
uv run python -m agentic_systems.cli.main orchestrate intake \
  --partner <partner> \
  --quarter <quarter> \
  --platform <platform> \
  [--sharepoint-sim-root <path>] \
  [--poll-interval <seconds>]
```

**Arguments:**
- `--partner` (required): Partner identifier (e.g., "test-partner-1", "test-partner-2"). Used for partner detection and to determine which parsing configuration to load.
- `--quarter` (required): Reporting quarter (e.g., "Q1", "Q2")
- `--platform` (optional, default: "minimal"): Agent platform to use
- `--sharepoint-sim-root` (optional): Root directory for SharePoint simulation folders (default: `agentic_systems/sharepoint_simulation/`). The orchestrator watches `sharepoint_simulation/uploads/` recursively for partner-specific uploads.
- `--poll-interval` (optional): Polling interval in seconds if watchdog unavailable (default: 5)

**Example:**
```bash
uv run python -m agentic_systems.cli.main orchestrate intake --partner test-partner-1 --quarter Q1 --platform minimal
```

**Expected Output:**
- Evidence bundle created at `agentic_systems/core/audit/runs/<partner>-<quarter>-<platform>/`
- Orchestrator watches for files and processes them automatically
- Terminal output shows file detection, validation status, and workflow state

### Orchestrator prompts & partner file flow

The orchestrator prints an execution banner, the BRD references it is demonstrating, the partner/quarter/platform trio, and the directory it is watching (`sharepoint_simulation/uploads/` at repo root, watched recursively for partner subfolders). If `watchdog` is installed you also see `Using file system events (watchdog) for file detection`; otherwise you see a warning plus `Polling interval: <seconds>` before it begins watching manually. While waiting for uploads you will see `Waiting for initial upload or corrected files... (Ctrl+C to cancel)` and, when a file is spotted, `[Orchestrator] Detected file: <filename>` followed by `[Orchestrator] Detected partner: <partner_name>` and the generated summary. If the orchestrator pauses for a corrected upload, the console prints the associated wait summary (e.g., `[Orchestrator] Waiting for partner correction...`) so you know when to drop the corrected CSV.

The orchestrator watches `sharepoint_simulation/uploads/` which contains partner-specific subfolders (e.g., `sharepoint_simulation/uploads/test-partner-1/`, `sharepoint_simulation/uploads/test-partner-2/`). **Both initial files and corrected files** should be placed in the appropriate partner subfolder. The orchestrator detects the partner name from the file path and loads the corresponding parsing configuration. When placing files:
- **Initial files**: Place in `agentic_systems/sharepoint_simulation/uploads/{partner_name}/` (e.g., `sharepoint_simulation/uploads/test-partner-1/Example Quarterly Data Report.mock.csv`)
- **Corrected files**: Place in the same location `agentic_systems/sharepoint_simulation/uploads/{partner_name}/` (e.g., `sharepoint_simulation/uploads/test-partner-1/partner_error_report_corrected.csv`)

The CLI monitors this folder recursively for new files, so a drop or save there triggers the detection flow and lets the run process or resume automatically.

### Understanding a run's artifacts

Every run stores all evidence under `agentic_systems/core/audit/runs/<run-id>/` where `<run-id>` follows the pattern `<partner>-<quarter>-<platform>` (e.g., `test-partner-1-Q1-minimal`). The most important artifacts are:

- `manifest.json`: Run metadata, classification, and status flags (partner, quarter, platform, PII handling, whether a resume is available, etc.).
- `plan.md`: The orchestrator plan that was executed (or paused and resumed).
- `summary.md`: A human-readable summary showing what file was processed, validation counts, and canonicalization results.
- `tool_calls.jsonl`: An ordered, sanitized log of each tool invocation for auditing and troubleshooting.
- `resume_state.json`: When the orchestrator pauses for a partner correction, this file captures the state needed to resume execution once the corrected file arrives.
- `secure_link_code.txt`: The shareable code tied to the simulated SharePoint secure link.

**SharePoint Simulation Structure** (at repo root `agentic_systems/sharepoint_simulation/`):
- `sharepoint_simulation/uploads/{partner_name}/`: Single source of truth for all file operations:
  - **Initial files**: Partner data files uploaded for processing (e.g., `Example Quarterly Data Report.mock.csv`)
  - **Corrected files**: Partner corrected files after validation errors (e.g., `partner_error_report_corrected.csv`)
  - **Error report publishing**: Contains `link.json` metadata pointing to the canonical `outputs/partner_error_report.xlsx` file in the evidence bundle (created after staff approval)

Within the `outputs/` subfolder:

- `canonical.csv`: The canonicalized dataset produced by ingestion/validation.
- `validation_report.csv`: Row-level validation findings (empty if there are no errors or warnings).
- `partner_error_report.xlsx`: Excel error report shared with the partner via the simulated SharePoint link.
- `partner_email.html` & `partner_email.txt`: The generated partner notification email in HTML and plain-text formats.
- `partner_email_approved.txt`: The version of the partner email after any staff approval (if no approvals were required, it mirrors the final email).
- `staff_approval_record.json`: Audit trail of any staff approvals, overrides, or exception requests.
- Additional helper artifacts (other email drafts, link metadata, etc.) that the workflow emits also live here for reviewers or automated tests.

### Individual Agent Commands

#### Intake Agent

Processes a partner file through ingestion, validation, and canonicalization.

*Windows (PowerShell):*
```powershell
uv run python -m agentic_systems.cli.main run intake `
  --file <file_path> `
  --partner <partner> `
  --quarter <quarter> `
  [--platform <platform>] `
  [--resume <run_id>] `
  [--watch <run_id>]
```

*Linux/macOS (Bash):*
```bash
uv run python -m agentic_systems.cli.main run intake \
  --file <file_path> \
  --partner <partner> \
  --quarter <quarter> \
  [--platform <platform>] \
  [--resume <run_id>] \
  [--watch <run_id>]
```

**Arguments:**
- `--file` (required): Path to partner file (CSV or Excel)
- `--partner` (required): Partner identifier
- `--quarter` (required): Reporting quarter
- `--platform` (optional, default: "minimal"): Agent platform to use
- `--resume` (optional): Resume processing with corrected file (provide run_id)
- `--watch` (optional): Watch for corrected files and auto-resume (provide run_id)

**Example:**
```bash
uv run python -m agentic_systems.cli.main run intake \
  --file "sharepoint_simulation/uploads/test-partner-1/Example Quarterly Data Report.mock.csv" \
  --partner test-partner-1 \
  --quarter Q1 \
  --platform minimal
```

**Expected Output:**
- Evidence bundle at `agentic_systems/core/audit/runs/<partner>-<quarter>-<platform>/`
- `outputs/canonical.csv` - Canonicalized data (if validation passes)
- `outputs/validation_report.csv` - Validation violations (if any)
- `summary.md` - Human-readable execution summary

#### Reconciliation Agent

Reconciles canonical data with WSAC prior-quarter records.

*Windows (PowerShell):*
```powershell
uv run python -m agentic_systems.cli.main run reconciliation `
  --partner <partner> `
  --quarter <quarter> `
  [--platform <platform>]
```

*Linux/macOS (Bash):*
```bash
uv run python -m agentic_systems.cli.main run reconciliation \
  --partner <partner> \
  --quarter <quarter> \
  [--platform <platform>]
```

**Arguments:**
- `--partner` (required): Partner identifier
- `--quarter` (required): Reporting quarter
- `--platform` (optional, default: "minimal"): Agent platform to use

**Status**: Implementation pending

#### Export Agent

Generates WSAC and Dynamics export files from canonicalized data.

*Windows (PowerShell):*
```powershell
uv run python -m agentic_systems.cli.main run export `
  --run-id <run_id> `
  --partner <partner> `
  --quarter <quarter> `
  [--platform <platform>]
```

*Linux/macOS (Bash):*
```bash
uv run python -m agentic_systems.cli.main run export \
  --run-id <run_id> \
  --partner <partner> \
  --quarter <quarter> \
  [--platform <platform>]
```

**Arguments:**
- `--run-id` (required): Run identifier to load canonical data from evidence bundle
- `--partner` (required): Partner identifier
- `--quarter` (required): Reporting quarter
- `--platform` (optional, default: "minimal"): Agent platform to use

**Status**: Implementation pending

**Note**: Line continuation differences:
- **PowerShell**: Use backtick (`` ` ``) for line continuation
- **Bash**: Use backslash (`\`) for line continuation

---

## Evidence Bundle

Every agent run produces an **Evidence Bundle** stored under:

```
agentic_systems/core/audit/runs/<run-id>/
```

Each Evidence Bundle includes:

- **`manifest.json`** - Run metadata, platform, data classification, PII handling, timestamps
- **`plan.md`** - Explicit agent execution plan
- **`tool_calls.jsonl`** - Ordered record of tool invocations (sanitized, no PII)
- **`outputs/`** - Generated files (canonical.csv, validation_report.csv, etc.)
- **`summary.md`** - Staff-facing explanation of decisions and outcomes
- **`resume_state.json`** - State for HITL resume workflows (if applicable)

Runs missing required evidence are **invalid**.

---

## Data Classification & PII Handling

All datasets and run artifacts must be labeled as one of:

- **Public**: Safe to share externally
- **Internal**: Non-public but not sensitive
- **Confidential**: Partner data; limited distribution
- **Restricted**: Contains PII/PHI or regulated data

**Rules:**
- **Restricted data must never be sent to third-party LLMs/tools** unless explicitly approved and documented
- Prefer **synthetic or anonymized datasets** for development
- When in doubt, treat data as **Restricted**

---

## Security & Secrets

- Do not commit secrets (`.env`, keys, tokens, connection strings)
- Store secrets in approved systems (e.g., Azure Key Vault, CI secret manager)
- Use least privilege credentials with short-lived access
- Rotate credentials immediately if leakage is suspected

**Security Preflight** (recommended before runs with Confidential/Restricted data):
- Verify no secrets in working tree
- Ensure platform/tool is listed in `security/allowlist.md`
- Ensure run manifest includes `data_classification` and `pii_handling`
- Redact artifacts when required using `scripts/redact_artifacts.py`

---

## TODO

Future enhancement tasks:

1. **Write dynamic imports file** - Implement Dynamics export functionality (`GenerateDynamicsExportTool`) with corrected field mappings
2. **Write WSAC upload file** - Implement WSAC export functionality (`GenerateWSACExportTool`) with camelCase format and ISO date transformations
3. **Update excel_utils.py** - Enhance `agentic_systems/core/partner_communication/excel_utils.py` to:
   - Accept Excel files with two sheets
   - Implement partner-specific subfunctions for reading data (each partner follows slightly different Excel worksheet formats)

---

## Documentation References

### Product/Technical Requirements Document (PRD-TRD)

**File**: [`agentic_systems/docs/prd-trd.md`](agentic_systems/docs/prd-trd.md)

The PRD-TRD defines:
- System architecture and technical specifications
- Agent contracts and tool protocols
- Data models and API specifications
- Integration requirements (SharePoint, Dataverse, WSAC, Dynamics)
- Evidence bundle format and auditability requirements
- Platform evaluation criteria

**Key Sections:**
- Section 5: Agent Specifications (BaseAgent contract, tool protocol)
- Section 11: CLI and Orchestration
- Section 3: Evidence Bundle Format

### Business Requirements Document (BRD)

**File**: [`agentic_systems/docs/brd.md`](agentic_systems/docs/brd.md)

The BRD defines:
- Business problem and objectives
- Functional requirements (FR-001 through FR-013)
- Validation rules and error handling
- Partner communication workflows
- Success metrics and acceptance criteria
- Data classification and PII handling requirements

**Key Sections:**
- Section 2: Business Context (data classification, PII handling)
- Section 3: Functional Requirements (validation, HITL, partner communication)
- Section 8: Data Models and Mappings

---

## Completion Rule (Hard Gate)

Work is **not complete** unless it:

- Produces a valid Evidence Bundle in `agentic_systems/core/audit/runs/`
- Declares `data_classification` and `pii_handling` in the run manifest
- Uses deterministic tools in `core/`
- Conforms to the BaseAgent contract
- Runs or validates end-to-end via the CLI
- Passes required tests
- Passes required security checks (no secrets committed; artifacts sanitized when required)
- Lives entirely in this repository

Vendor consoles may assist execution,  
but **this repository is the final authority**.
