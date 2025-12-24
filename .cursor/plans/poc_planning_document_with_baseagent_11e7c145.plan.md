---
name: POC Planning Document with BaseAgent
overview: Update the POC planning document to integrate BaseAgent contract demonstration and add comprehensive environment variables/configuration section for both POC (no env vars needed) and full implementation requirements.
todos:
  - id: update-poc-plan
    content: Update .cursor/plans/poc_planning_document_ec7db169.plan.md with BaseAgent integration and environment variables section
    status: pending
  - id: update-simple-agent-spec
    content: Update SimpleIntakeAgent specification to extend BaseAgent with plan(), execute(), summarize() methods
    status: completed
  - id: update-cli-spec
    content: Update CLI specification to demonstrate BaseAgent contract usage (plan → execute → summarize)
    status: completed
  - id: add-env-section
    content: Add comprehensive Environment Variables & Configuration section covering POC (none needed) and full implementation requirements
    status: completed
  - id: create-env-example
    content: Add .env.example template file creation to implementation plan with all documented placeholders
    status: pending
  - id: update-objectives
    content: Update objectives to include BaseAgent contract demonstration
    status: completed
  - id: update-architecture-diagram
    content: Update architecture diagram to show BaseAgent contract methods (plan, execute, summarize)
    status: completed
  - id: update-success-criteria
    content: Add BaseAgent contract demonstration to success criteria
    status: completed
  - id: create_partner_comm_package
    content: Create agentic_systems/core/partner_communication/ package with __init__.py
    status: completed
  - id: implement_error_report_tool
    content: Implement GeneratePartnerErrorReportTool to create CSV with full row data for error rows
    status: pending
    dependencies:
      - create_partner_comm_package
  - id: implement_email_tool
    content: Implement GeneratePartnerEmailTool to create templated email with per-row error explanations
    status: pending
    dependencies:
      - create_partner_comm_package
  - id: implement_secure_link_tool
    content: Implement CreateSecureLinkTool (lightweight demo) with explicit production comments
    status: pending
    dependencies:
      - create_partner_comm_package
  - id: implement_request_approval_tool
    content: Implement RequestStaffApprovalTool with interactive CLI prompt for staff review and approval
    status: pending
    dependencies:
      - create_partner_comm_package
  - id: update_simple_agent_hitl
    content: Update SimpleIntakeAgent.execute() to add HITL workflow (error report → email → staff approval → secure link → send email → halt)
    status: pending
    dependencies:
      - implement_error_report_tool
      - implement_email_tool
      - implement_request_approval_tool
      - implement_secure_link_tool
  - id: update_simple_agent_resume
    content: Add SimpleIntakeAgent.resume() method to handle corrected file re-validation and continuation
    status: pending
    dependencies:
      - update_simple_agent_hitl
  - id: update_langchain_agent_hitl
    content: Update LangChainIntakeAgent.execute() to add same HITL workflow with staff approval
    status: pending
    dependencies:
      - implement_error_report_tool
      - implement_email_tool
      - implement_request_approval_tool
      - implement_secure_link_tool
  - id: update_langchain_agent_resume
    content: Add LangChainIntakeAgent.resume() method (same as SimpleIntakeAgent)
    status: pending
    dependencies:
      - update_langchain_agent_hitl
  - id: update_write_evidence_hitl
    content: Update write_evidence.py to write resume_state.json and serialize partner communication outputs
    status: pending
    dependencies:
      - update_simple_agent_hitl
  - id: update_cli_resume
    content: Add --resume <run-id> and --watch <directory> flags to CLI main.py
    status: pending
    dependencies:
      - update_simple_agent_resume
      - update_langchain_agent_resume
  - id: add_part3_unit_tests
    content: Add unit tests for GeneratePartnerErrorReportTool, GeneratePartnerEmailTool, CreateSecureLinkTool, and RequestStaffApprovalTool
    status: pending
    dependencies:
      - implement_error_report_tool
      - implement_email_tool
      - implement_secure_link_tool
      - implement_request_approval_tool
  - id: manual_verification_part3
    content: "Test end-to-end HITL workflow: validation → error report → email → staff approval → secure link → send email → resume with corrected file. Also test approval rejection flow."
    status: pending
    dependencies:
      - update_cli_resume
      - add_part3_unit_tests
  - id: implement_wsac_aggregates_tool
    content: Implement CollectWSACAggregatesTool to collect aggregates from partner data and compare against WSAC prior-quarter data
    status: pending
    dependencies:
      - create_partner_comm_package
  - id: update_error_report_wsac_comparison
    content: Update GeneratePartnerErrorReportTool to include WSAC aggregates comparison section in partner reports
    status: pending
    dependencies:
      - implement_wsac_aggregates_tool
  - id: update_resume_wsac_recheck
    content: Update resume() method to re-check WSAC aggregates comparison and WSAC upload rules after partner fixes
    status: pending
    dependencies:
      - implement_wsac_aggregates_tool
      - update_simple_agent_resume
  - id: implement_sharepoint_upload_simulation
    content: Implement UploadSharePointTool with three folder types (internal, partner_accessible, upload) for simulated SharePoint workflow
    status: pending
    dependencies:
      - create_partner_comm_package
  - id: implement_cli_watch_polling
    content: Implement CLI --watch mode that polls sharepoint_simulation/uploads/<run-id>/ for corrected files and triggers resume
    status: pending
    dependencies:
      - implement_sharepoint_upload_simulation
      - update_cli_resume
---

# POC Planning Document: Rapid ETL Deployment with BaseAgent

## Overview

This document outlines a rapid proof-of-concept (POC) deployment strategy for the ETL components of the CFA Applied Agentic AI system. The goal is to demonstrate a working ingestion → validation → canonicalization pipeline with BaseAgent contract compliance in minimal time for instructor/mentor demonstration and curriculum development.**Three-Part Demonstration:**

- **Part 1**: Deterministic baseline (no LLM) - shows contract pattern with hardcoded orchestration
- **Part 2**: LLM-based orchestration - shows same contract with AI-powered planning and summarization
- **Part 3**: HITL Partner Communication - demonstrates complete error correction workflow with staff approval, secure link sharing, WSAC aggregates comparison, and SharePoint upload simulation

## Objectives

- Deploy working ETL pipeline (Extract → Transform → Load) in < 30 minutes (Part 1)
- Demonstrate tool-based architecture aligned with BaseAgent contract (see [PRD-TRD Section 5.1](../../agentic_systems/docs/prd-trd.md#51-baseagent-contract))
- Show contract-first agent design pattern (plan → execute → summarize)
- **Part 2**: Demonstrate LLM-based orchestration using same tools (see [PRD-TRD Section 6.4](../../agentic_systems/docs/prd-trd.md#64-platform-adapter-specifications))
- **Part 3**: Demonstrate HITL workflow with partner error reporting, staff approval, WSAC aggregates comparison, resume functionality, and SharePoint upload simulation (per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012), [BRD FR-013](../../agentic_systems/docs/brd.md#33-secure-partner-sharing-fr-013), [BRD FR-004](../../agentic_systems/docs/brd.md#35-wsac-reconciliation-fr-004))
- Generate evidence bundles per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011) and [PRD-TRD Section 3.2](../../agentic_systems/docs/prd-trd.md#32-evidence-bundle-structure)
- Provide testable CLI interface for rapid iteration
- Establish foundation for full implementation

---*[Note: This plan document has been reconstructed. The full detailed content from the original plan is preserved in `.cursor/plans/poc_planning_document_with_baseagent.original.plan.md`. This file contains the todos and key updates including WSAC aggregates comparison and SharePoint upload simulation integration.]***For complete implementation details, refer to:** `.cursor/plans/poc_planning_document_with_baseagent.original.plan.md`**Key additions in this version:**

- WSAC aggregates comparison tool integration (Task 16-18 in todos)
- SharePoint upload simulation with three-folder structure (internal, partner_accessible, upload)
- CLI --watch polling mode for automated resume detection

# POC Planning Document: Rapid ETL Deployment with BaseAgent

## Overview

This document outlines a rapid proof-of-concept (POC) deployment strategy for the ETL components of the CFA Applied Agentic AI system. The goal is to demonstrate a working ingestion → validation → canonicalization pipeline with BaseAgent contract compliance in minimal time for instructor/mentor demonstration and curriculum development.**Three-Part Demonstration:**

- **Part 1**: Deterministic baseline (no LLM) - shows contract pattern with hardcoded orchestration
- **Part 2**: LLM-based orchestration - shows same contract with AI-powered planning and summarization
- **Part 3**: HITL Partner Communication - demonstrates complete error correction workflow with staff approval and secure link sharing

## Objectives

- Deploy working ETL pipeline (Extract → Transform → Load) in < 30 minutes (Part 1)
- Demonstrate tool-based architecture aligned with BaseAgent contract (see [PRD-TRD Section 5.1](../../agentic_systems/docs/prd-trd.md#51-baseagent-contract))
- Show contract-first agent design pattern (plan → execute → summarize)
- **Part 2**: Demonstrate LLM-based orchestration using same tools (see [PRD-TRD Section 6.4](../../agentic_systems/docs/prd-trd.md#64-platform-adapter-specifications))
- **Part 3**: Demonstrate HITL workflow with partner error reporting, staff approval, and resume functionality (per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012) and [BRD FR-013](../../agentic_systems/docs/brd.md#33-secure-partner-sharing-fr-013))
- Generate evidence bundles per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011) and [PRD-TRD Section 3.2](../../agentic_systems/docs/prd-trd.md#32-evidence-bundle-structure)
- Provide testable CLI interface for rapid iteration
- Establish foundation for full implementation

---

# Part 1: Deterministic Baseline (No LLM)

## Architecture

The POC implements a simplified version of the full system:

```javascript
Partner File (CSV/Excel)
    ↓
[SimpleIntakeAgent.plan()] → Generate execution plan
    ↓
[SimpleIntakeAgent.execute()] → Orchestrate tools
    ↓
[IngestPartnerFileTool] → Extract & Parse
    ↓
[ValidateStagedDataTool] → Transform & Validate
    ↓
[CanonicalizeStagedDataTool] → Load & Canonicalize
    ↓
[SimpleIntakeAgent.summarize()] → Generate summary
    ↓
Canonical Data (DataFrame/JSON) + Summary
```



## Implementation Plan

### File Structure

Create the following files:

1. **`agentic_systems/core/tools.py`**

- Tool protocol definition (`Tool` Protocol) per [PRD-TRD Section 5.4](../../agentic_systems/docs/prd-trd.md#54-tool-specifications)
- `ToolResult` dataclass with `ok`, `summary`, `data`, `warnings`, `blockers` per [PRD-TRD Section 5.4](../../agentic_systems/docs/prd-trd.md#54-tool-specifications)

2. **`agentic_systems/core/ingestion/__init__.py`** (empty)
3. **`agentic_systems/core/ingestion/ingest_tool.py`**

- `IngestPartnerFileTool` class implementing `Tool` protocol
- Handles CSV/Excel files with encoding detection
- Returns in-memory DataFrame in `ToolResult.data` for tool chaining (evidence writer serializes to `outputs/` later)

4. **`agentic_systems/core/validation/__init__.py`** (empty)
5. **`agentic_systems/core/validation/validate_tool.py`**

- `ValidateStagedDataTool` class
- Basic validation rules (required fields, active past graduation check)
- Returns validation results with error/warning counts

6. **`agentic_systems/core/canonical/__init__.py`** (empty)
7. **`agentic_systems/core/canonical/canonicalize_tool.py`**

- `CanonicalizeStagedDataTool` class
- Transforms validated data to canonical format
- Simple ID generation for POC (can be replaced with PostgreSQL later)

8. **`agentic_systems/agents/simple_intake_agent.py`**

- `SimpleIntakeAgent` class extending `BaseAgent` contract
- Implements `plan()`, `execute()`, and `summarize()` methods
- `plan()`: Returns structured execution steps (List[Dict]) for ingest → validate → canonicalize sequence
- `execute()`: Orchestrates the three tools in sequence
- `summarize()`: Produces staff-facing summary of outcomes
- Demonstrates contract-first agent design pattern

9. **`agentic_systems/cli/main.py`** (update existing)

- Update existing CLI to accept `--file` argument for `agent run intake` command per [PRD-TRD Section 11.2](../../agentic_systems/docs/prd-trd.md#112-configuration-management)
- Validate file path exists before processing
- Keep run_id pattern `<partner>-<quarter>-<platform>` per [PRD-TRD Section 11.2](../../agentic_systems/docs/prd-trd.md#112-configuration-management)
- **Agent routing (direct instantiation per [PRD-TRD Section 6.4](../../agentic_systems/docs/prd-trd.md#64-platform-adapter-specifications)):**
  ```python
        # CLI directly instantiates platform-specific agents per PRD-TRD Section 6.4
        # No dispatcher needed - CLI routes directly to platform implementations
        if args.platform == "minimal":
            from agentic_systems.agents.simple_intake_agent import SimpleIntakeAgent
            agent = SimpleIntakeAgent()  # Part 1: Deterministic baseline
        elif args.platform == "langchain":
            from agentic_systems.agents.platforms.langchain.intake_impl import LangChainIntakeAgent
            agent = LangChainIntakeAgent()  # Part 2: LLM orchestration
        else:
            raise ValueError(f"Unknown platform: {args.platform}")
        
        # Demonstrate BaseAgent contract per PRD-TRD Section 5.1
        plan = agent.plan({"file_path": args.file, "run_id": run_id})
        print("=== PLAN ===")
        print(plan)  # Per BRD FR-011, plan shown before execution
        
        results = agent.execute({"file_path": args.file, "run_id": run_id})
        
        summary = agent.summarize(results)
        print("\n=== SUMMARY ===")
        print(summary)  # Per BRD FR-011, summary shown after execution
  ```




- Pass file path into agent inputs
- Print plan before execution and summary after execution (demonstrates BaseAgent contract)
- Shows canonical data summary (row count, column names, sample record count - no raw PII data per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules))

10. **`agentic_systems/setup_poc.sh`** (or `setup_poc.bat` for Windows)

                                                                                                                                                                                                                                                                - Creates `__init__.py` files in all package directories:
                                                                                                                                                                                                                                                                - `agentic_systems/__init__.py` (enables `python -m agentic_systems.cli.main` from repo root)
                                                                                                                                                                                                                                                                - `agentic_systems/core/__init__.py`
                                                                                                                                                                                                                                                                - `agentic_systems/core/ingestion/__init__.py`
                                                                                                                                                                                                                                                                - `agentic_systems/core/validation/__init__.py`
                                                                                                                                                                                                                                                                - `agentic_systems/core/canonical/__init__.py`
                                                                                                                                                                                                                                                                - `agentic_systems/agents/__init__.py`
                                                                                                                                                                                                                                                                - `agentic_systems/agents/platforms/__init__.py`
                                                                                                                                                                                                                                                                - `agentic_systems/agents/platforms/langchain/__init__.py` (Part 2)
                                                                                                                                                                                                                                                                - Installs minimal dependencies (pandas, openpyxl)

11. **`agentic_systems/core/audit/write_evidence.py`** (new)

                                                                                                                                                                                                                                                                - Deterministic core tool for evidence bundle generation per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011)
                                                                                                                                                                                                                                                                - Writes required files: `manifest.json`, `plan.md`, `summary.md`, and serializes `outputs/` per [PRD-TRD Section 3.2](../../agentic_systems/docs/prd-trd.md#32-evidence-bundle-structure)
                                                                                                                                                                                                                                                                - **Note**: Does NOT write `tool_calls.jsonl` - that is handled by BaseAgent.execute() which appends JSONL events directly as tools run
                                                                                                                                                                                                                                                                - Sets `data_classification="Internal"` and `pii_handling="redacted"` in `manifest.json` (JSON values only)
                                                                                                                                                                                                                                                                - **Code comment in `write_evidence.py`**: `# Masked mock data is treated as Internal; PII is redacted per BRD Section 2.3`

12. **`.env.example`** (new - at repository root)

                                                                                                                                                                                                                                                                - Template for environment variables per [README Section "Secrets & Credentials"](README.md#secrets--credentials)
                                                                                                                                                                                                                                                                - Documents all configuration options (POC and full implementation)
                                                                                                                                                                                                                                                                - **Placeholders must be clearly fake:** `OPENAI_API_KEY=sk-example-placeholder-do-not-use-real-key` (prevents secret scanner false positives)
                                                                                                                                                                                                                                                                - Location: Repository root (alongside `README.md`), not in `agentic_systems/`

## Key Implementation Details

### BaseAgent Contract Implementation

`SimpleIntakeAgent` extends `BaseAgent` to demonstrate the contract-first pattern per [PRD-TRD Section 5.1](../../agentic_systems/docs/prd-trd.md#51-baseagent-contract):

- **`plan(inputs: Dict[str, Any]) -> List[Dict[str, Any]]`**: 
- Analyzes inputs (file path, run_id)
- Returns structured execution steps: `[{'tool': 'IngestPartnerFileTool', 'args': {...}}, {'tool': 'ValidateStagedDataTool', 'args': {...}}, {'tool': 'CanonicalizeStagedDataTool', 'args': {...}}]`
- Human-readable `plan.md` is generated from structured steps by `write_evidence.py` per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011)
- **`execute(inputs: Dict[str, Any]) -> Dict[str, Any]`**:
- Orchestrates tool calls: `IngestPartnerFileTool` → `ValidateStagedDataTool` → `CanonicalizeStagedDataTool`
- **Wraps each tool call with evidence logging:**
                                                                                                                                                                                                                                                                - Emits `STEP_START` event to `tool_calls.jsonl` before tool invocation (per [PRD-TRD Section 7.4](../../agentic_systems/docs/prd-trd.md#74-evidence-bundle-generation-flow))
                                                                                                                                                                                                                                                                - Invokes tool: `result = tool(**kwargs)`
                                                                                                                                                                                                                                                                - Emits `STEP_END` event to `tool_calls.jsonl` after tool invocation with sanitized metadata (counts, hashes, status only)
- Returns structured results with step outcomes and canonical data (in-memory objects in `data` for tool chaining)
- **`summarize(run_results: Dict[str, Any]) -> str`**:
- Produces staff-facing summary per [PRD-TRD Section 5.1](../../agentic_systems/docs/prd-trd.md#51-baseagent-contract)
- Includes: file processed, validation status, canonical record count, any warnings/blockers
- Summary written to `summary.md` in evidence bundle per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011)

### Tool Protocol

All tools follow the `Tool` protocol per [PRD-TRD Section 5.4](../../agentic_systems/docs/prd-trd.md#54-tool-specifications):

- `name: str` attribute
- `__call__(**kwargs) -> ToolResult` method

### ToolResult Structure

```python
@dataclass
class ToolResult:
    ok: bool                    # Success/failure indicator
    summary: str               # Human-readable summary
    data: Dict[str, Any]        # Structured data - may contain in-memory objects (DataFrames, lists) for tool chaining
    warnings: List[str]         # Non-blocking issues
    blockers: List[str]         # Blocking errors
```

**Data Flow Design (per [PRD-TRD Section 5.4](../../agentic_systems/docs/prd-trd.md#54-tool-specifications)):****Single Clear Rule:**

- `ToolResult.data` can contain in-memory objects (DataFrames, lists of dicts) for tool chaining between steps
- `tool_calls.jsonl` logs sanitized metadata only (counts, hashes, status) - no DataFrames or raw data in evidence logs
- Evidence writer (`write_evidence.py`) serializes in-memory tool results to `outputs/` directory once (after all tools complete)

### IngestPartnerFileTool Features

- Supports CSV and Excel files per [BRD FR-001](../../agentic_systems/docs/brd.md#31-data-ingestion-fr-001)
- Encoding detection (UTF-8, Windows-1252, Latin-1) per [BRD FR-001](../../agentic_systems/docs/brd.md#31-data-ingestion-fr-001) acceptance criteria
- Column name normalization (lowercase, replace spaces) per [BRD FR-001](../../agentic_systems/docs/brd.md#31-data-ingestion-fr-001) acceptance criteria
- File hash calculation for idempotency per [PRD-TRD Section 5.4](../../agentic_systems/docs/prd-trd.md#54-tool-specifications)
- Returns parsed rows + metadata (row count, columns, hash) in `ToolResult.data`
- **Data Flow Design:** DataFrame stored in memory for tool chaining, `ToolResult.data` contains in-memory DataFrame for next tool, but evidence logging uses sanitized metadata only

**Example Implementation:**

```python
# IngestPartnerFileTool per BRD FR-001 and PRD-TRD Section 5.4
class IngestPartnerFileTool:
    def __call__(self, file_path: str) -> ToolResult:
        # Parse file per BRD FR-001 acceptance criteria
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # Compute file hash for idempotency per PRD-TRD Section 5.4
        file_hash = hashlib.sha256(open(file_path, 'rb').read()).hexdigest()
        
        # Return in-memory DataFrame for tool chaining (ToolResult.data holds objects per PRD-TRD Section 5.4)
        # Evidence logging will use sanitized metadata only (counts, hash, status)
        # Evidence writer will serialize DataFrame to outputs/ later (tools return in-memory data only)
        return ToolResult(
            ok=True,
            summary=f"Ingested {len(df)} rows from {file_path}",
            data={"dataframe": df, "row_count": len(df), "columns": list(df.columns), "file_hash": file_hash},  # In-memory objects for chaining
            warnings=[],
            blockers=[]
        )
```



### ValidateStagedDataTool Features

- Required column validation per [BRD FR-002](../../agentic_systems/docs/brd.md#32-data-validation-fr-002)
- Active past graduation check (if status/end_date columns present) - see [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules) validation rules
- Empty field detection
- **Row-level validation reporting (redacted per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules)): **Emit entries as `{row_index, field, severity, message}` - **no raw field values** per [BRD FR-002](../../agentic_systems/docs/brd.md#32-data-validation-fr-002) acceptance criteria
- Example: `{row_index: 5, field: "end_date", severity: "Error", message: "Participant marked active past graduation date"}`
- Excludes raw participant data to maintain "redacted" PII handling
- Returns validation summary counts + row-level list in `ToolResult.data` (in-memory list for tool chaining)
- **Note**: Evidence writer serializes validation results to `outputs/validation_report.csv` once (tools return in-memory data only)

### CanonicalizeStagedDataTool Features

- Map staged fields to canonical fields per [BRD FR-003](../../agentic_systems/docs/brd.md#34-canonicalization-fr-003)
- Generate stable POC IDs (`P000001`, `P000002`, etc.) - simple ID generation for POC (can be replaced with PostgreSQL later)
- Returns canonical rows + counts in `ToolResult.data` (in-memory DataFrame for tool chaining)
- **Note**: Evidence writer serializes canonical data to `outputs/canonical.csv` once (tools return in-memory data only) per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011)

## Environment Variables & Configuration

### POC Requirements: None

**The POC requires NO environment variables or API keys.** It is designed to be completely self-contained:

- All file operations are local (no SharePoint)
- Data processing is in-memory (no PostgreSQL)
- No external API calls (no wage validation API)
- No authentication required

### Full Implementation Requirements

For future full implementation, the following environment variables will be needed. Create `.env.example` template documenting these:

#### Database Configuration

Per [PRD-TRD Section 11.2](../../agentic_systems/docs/prd-trd.md#112-configuration-management):

```bash
# PostgreSQL connection string (required for full implementation)
DATABASE_URL=postgresql://user:password@host:port/database
```



#### SharePoint Integration (Optional - Week 3+)

Per [BRD FR-001](../../agentic_systems/docs/brd.md#31-data-ingestion-fr-001) (partner file reading) and [BRD FR-013](../../agentic_systems/docs/brd.md#33-secure-partner-sharing-fr-013) (validation report sharing):

```bash
# SharePoint site URL
SHAREPOINT_SITE_URL=https://yourorg.sharepoint.com/sites/CFA

# Azure AD App Registration credentials
SHAREPOINT_CLIENT_ID=<Azure AD App ID>
SHAREPOINT_CLIENT_SECRET=<Azure AD App Secret>

# SharePoint folder paths (optional)
SHAREPOINT_PARTNER_FILES_FOLDER=/sites/CFA/Shared Documents/Partner Files
SHAREPOINT_REPORTS_FOLDER=/sites/CFA/Shared Documents/Validation Reports
```



#### External API Integration (Optional - Week 3+)

Per [BRD FR-002](../../agentic_systems/docs/brd.md#32-data-validation-fr-002) (prevailing wage validation):

```bash
# Prevailing wage validation API
WAGE_API_URL=https://api.example.com/wage-validation
WAGE_API_KEY=<API key for wage validation service>
```



#### LLM Platform Integration (Optional - Part 2)

Per [PRD-TRD Section 6.4](../../agentic_systems/docs/prd-trd.md#64-platform-adapter-specifications) (platform adapter specifications):

```bash
# OpenAI (if using OpenAI platform adapter)
OPENAI_API_KEY=<OpenAI API key>

# Anthropic (if using Anthropic platform adapter)
ANTHROPIC_API_KEY=<Anthropic API key>

# Azure OpenAI (if using Microsoft platform adapter)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=<Azure OpenAI API key>
AZURE_OPENAI_DEPLOYMENT_NAME=<deployment name>
```



### Environment Variable Setup Instructions

1. **For POC**: No setup needed - just run the CLI with local files
2. **For Full Implementation**:

- Copy `.env.example` to `.env` (this file is gitignored)
- Fill in actual values for your environment
- Never commit `.env` file (already in `.gitignore`)
- Use Azure Key Vault or CI secret manager for production

3. **Security Best Practices**:

- Store secrets in approved systems (Azure Key Vault, GitHub Secrets)
- Use least privilege credentials
- Rotate credentials immediately if leakage suspected
- Never hardcode secrets in code
- Use `.env.example` as documentation template only

### .env.example Template File

Create `.env.example` at repository root (alongside `README.md`) per [PRD-TRD Section 11.2](../../agentic_systems/docs/prd-trd.md#112-configuration-management) and [README Section "Secrets & Credentials"](README.md#secrets--credentials) with all placeholders:

```bash
# ============================================
# POC Configuration
# ============================================
# POC requires NO environment variables
# All operations are local and in-memory

# ============================================
# Database Configuration (Full Implementation)
# ============================================
# PostgreSQL connection string per PRD-TRD Section 11.2
# Format: postgresql://user:password@host:port/database
DATABASE_URL=postgresql://user:password@localhost:5432/cfa_db

# ============================================
# SharePoint Integration (Optional - Week 3+)
# ============================================
# SharePoint integration per BRD FR-001 and FR-013
SHAREPOINT_SITE_URL=https://yourorg.sharepoint.com/sites/CFA
SHAREPOINT_CLIENT_ID=example-azure-ad-app-id-placeholder
SHAREPOINT_CLIENT_SECRET=example-azure-ad-app-secret-placeholder
SHAREPOINT_PARTNER_FILES_FOLDER=/sites/CFA/Shared Documents/Partner Files
SHAREPOINT_REPORTS_FOLDER=/sites/CFA/Shared Documents/Validation Reports

# ============================================
# External API Integration (Optional - Week 3+)
# ============================================
# Prevailing wage validation API per BRD FR-002
WAGE_API_URL=https://api.example.com/wage-validation
WAGE_API_KEY=example-wage-api-key-placeholder

# ============================================
# LLM Platform Integration (Optional - Part 2)
# ============================================
# OpenAI (for Part 2 LLM orchestration per PRD-TRD Section 6.4)
OPENAI_API_KEY=sk-example-placeholder-do-not-use-real-key

# Anthropic (for Part 2 LLM orchestration per PRD-TRD Section 6.4)
ANTHROPIC_API_KEY=sk-ant-example-placeholder-do-not-use-real-key

# Azure OpenAI (for Part 2 LLM orchestration per PRD-TRD Section 6.4)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=example-placeholder-do-not-use-real-key
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
```

**Note**: Placeholders use clearly fake patterns (`example-placeholder-do-not-use-real-key`) to prevent secret scanner false positives per [README Section "Secrets & Credentials"](README.md#secrets--credentials).

## Evidence Bundle Generation

**Required per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011) and [PRD-TRD Section 3.2](../../agentic_systems/docs/prd-trd.md#32-evidence-bundle-structure):**The POC includes simplified evidence bundle generation to demonstrate the contract. BaseAgent `execute()` method wraps tool calls and emits trace events per [PRD-TRD Section 7.4](../../agentic_systems/docs/prd-trd.md#74-evidence-bundle-generation-flow).**Evidence Generation Flow:**

1. BaseAgent `execute()` wraps each tool call and appends JSONL events directly to `tool_calls.jsonl` as tools run (BaseAgent owns tool_calls.jsonl writing)
2. Tools return in-memory data (DataFrames, lists) in `ToolResult.data` for tool chaining
3. `write_evidence.py` writes `manifest.json`, `plan.md`, `summary.md` from agent state
4. `write_evidence.py` serializes in-memory data to `outputs/` directory once (after all tools complete)

- Serializes validation results to `outputs/validation_report.csv`
- Serializes canonical data to `outputs/canonical.csv`

Create `agentic_systems/core/audit/write_evidence.py` as a deterministic core tool that writes:

- **`manifest.json`**: Run metadata per [PRD-TRD Section 3.2](../../agentic_systems/docs/prd-trd.md#32-evidence-bundle-structure)
- `data_classification="Internal"` and `pii_handling="redacted"` (JSON values only, per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules))
- For Part 2: `"platform": "langchain"`, `"model": "gpt-4"` (or equivalent), `"egress_approval_ref": null` (or approval ID if Restricted data sent)
- **Code comment in `write_evidence.py`**: `# Masked mock data is treated as Internal; PII is redacted per BRD Section 2.3` (comment in code, not JSON)
- **`plan.md`**: Human-readable execution plan generated from structured steps returned by `agent.plan()` per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011)
- **`tool_calls.jsonl`**: Ordered tool call log (JSONL format) per [PRD-TRD Section 7.4](../../agentic_systems/docs/prd-trd.md#74-evidence-bundle-generation-flow)
- Populated by BaseAgent `execute()` method wrapping each tool call
- Each tool call emits `STEP_START` and `STEP_END` events with sanitized metadata only (counts, hashes, status) - no DataFrames or raw data
- **Example trace event:**
    ```python
                                                                                                                        # BaseAgent._emit() writes to tool_calls.jsonl per PRD-TRD Section 7.4
                                                                                                                        event = {
                                                                                                                            "timestamp": "2025-01-15T10:30:00Z",
                                                                                                                            "event_type": "STEP_END",
                                                                                                                            "run_id": run_id,
                                                                                                                            "message": "Completed IngestPartnerFileTool",
                                                                                                                            "data": {
                                                                                                                                "tool": "IngestPartnerFileTool",
                                                                                                                                "ok": True,
                                                                                                                                "row_count": 500,  # Metadata only - no DataFrame
                                                                                                                                "file_hash": "abc123...",  # Hash for idempotency per PRD-TRD Section 5.4
                                                                                                                                "columns": ["first_name", "last_name", ...]  # Column names only - no raw data
                                                                                                                            }
                                                                                                                        }
                                                                                                                        # Append to tool_calls.jsonl per BRD FR-011
    ```




- **`outputs/`**: Generated artifacts per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011):
- `outputs/validation_report.csv` (row-level validation entries: row_index, field, severity, message only - no raw values)
- `outputs/canonical.csv` (canonicalized data)
- **Ownership**: Evidence writer (`write_evidence.py`) serializes in-memory tool results to `outputs/` once (tools return in-memory data only)
- **`summary.md`**: Staff-facing summary from `agent.summarize()` per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011)

Evidence bundle location: `agentic_systems/core/audit/runs/<run-id>/` per [PRD-TRD Section 3.2](../../agentic_systems/docs/prd-trd.md#32-evidence-bundle-structure).**Example Implementation (`write_evidence.py`):**

```python
# Evidence bundle writer per BRD FR-011 and PRD-TRD Section 3.2
def write_manifest(run_id: str, agent_name: str, platform: str) -> None:
    manifest = {
        "run_id": run_id,
        "agent": agent_name,
        "platform": platform,
        # Data classification per BRD Section 2.3 - JSON values only (no comments in JSON)
        "data_classification": "Internal",  # Masked mock data is treated as Internal per BRD Section 2.3
        "pii_handling": "redacted",  # PII is redacted per BRD Section 2.3
        # For Part 2: include platform/model metadata per PRD-TRD Section 3.2
        "model": "gpt-4" if platform == "langchain" else None,
        "egress_approval_ref": None  # No Restricted data sent to LLM per BRD Section 2.3
    }
    # Write manifest.json per PRD-TRD Section 3.2
    with open(f"core/audit/runs/{run_id}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
```



## Testing Strategy

### Unit Tests (Required per [PRD-TRD Section 10.1](../../agentic_systems/docs/prd-trd.md#101-unit-tests))

**Part 1 Tests (Deterministic):**Add unit tests under `agentic_systems/tests/` for deterministic core logic:

- **Header normalization + file hash**: Test `IngestPartnerFileTool` encoding detection and hash calculation
- **Row-level validation detection**: Test `ValidateStagedDataTool` required field checks and active past graduation rule
- **Canonical ID generation**: Test `CanonicalizeStagedDataTool` ID generation logic

Tests must not call external services and should achieve 80%+ coverage for core modules per [PRD-TRD Section 10.1](../../agentic_systems/docs/prd-trd.md#101-unit-tests).**Part 2 Tests (LLM Platform):**

- Unit tests mock LLM responses (no real API calls) per [PRD-TRD Section 10.1](../../agentic_systems/docs/prd-trd.md#101-unit-tests)
- Integration tests marked `@pytest.mark.integration` require API key and are manual-only
- **Manual verification checklist** (recorded, not automated):
- [ ] LLM generates dynamic plan based on file metadata
- [ ] LLM creates contextual summary from validation results
- [ ] Evidence bundle includes platform/model metadata in manifest.json
- [ ] No raw data sent to LLM (verify via manifest.json egress_approval_ref)

### Test Data

Use existing mock data files:

- `agentic_systems/data/masked/Example Quarterly Data Report.mock.csv`
- `agentic_systems/data/masked/dynamics_import.mock.csv`

### Test Commands

**Working Directory:** Repository root (`cfa-applied-agentic-ai/`)**Exact Command:**

```bash
# Part 1: Deterministic baseline
python -m agentic_systems.cli.main run intake --file agentic_systems/data/masked/Example\ Quarterly\ Data\ Report.mock.csv --partner demo --quarter Q1 --platform minimal

# Part 2: LLM-based orchestration (requires API key)
python -m agentic_systems.cli.main run intake --file agentic_systems/data/masked/Example\ Quarterly\ Data\ Report.mock.csv --partner demo --quarter Q1 --platform langchain
```

**Prerequisites:**

- `agentic_systems/__init__.py` must exist (created by setup script)
- Python package structure allows `agentic_systems` import from repo root

### Expected Output

- Plan output (human-readable format generated from structured steps returned by `agent.plan()`) printed before execution
- Step-by-step progress messages
- Summary of each step (ingest, validate, canonicalize)
- Error/warning counts
- Final summary (from `agent.summarize()`) printed after execution
- Evidence bundle created in `core/audit/runs/<run-id>/`
- Summary of canonical data (row count, column names, sample record count - no raw PII data per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules))

### Manual Verification

- Run Part 1: `python -m agentic_systems.cli.main run intake --file agentic_systems/data/masked/Example\ Quarterly\ Data\ Report.mock.csv --partner demo --quarter Q1 --platform minimal`
- Verify evidence bundle contents in `core/audit/runs/<run-id>/`
- Confirm validation report is row-level (`outputs/validation_report.csv`)
- Confirm canonical output exists (`outputs/canonical.csv`)
- Verify `tool_calls.jsonl` contains JSON-serializable metadata only

## Dependencies

Minimal dependencies for POC per [PRD-TRD Section 11.2](../../agentic_systems/docs/prd-trd.md#112-configuration-management):

- `pandas` - Data manipulation
- `openpyxl` - Excel file support
- Standard library `abc` module - For BaseAgent abstract base class

Installation:

```bash
pip install pandas openpyxl
```



## Data Classification

**POC Defaults (per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules)):**

- **Data Classification**: `Internal` (masked mock data is treated as Internal)
- **PII Handling**: `redacted` (PII is redacted in evidence bundles)
- **Rationale**: Mock data files are masked and contain no real PII, so classified as Internal with redacted PII handling

This must be declared in `manifest.json` per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011) acceptance criteria.

## Limitations & Assumptions

**POC Limitations:**

- In-memory DataFrames (no PostgreSQL) - see [PRD-TRD Section 11.2](../../agentic_systems/docs/prd-trd.md#112-configuration-management) for full implementation
- Simple ID generation (no identity resolution) - full implementation per [BRD FR-003](../../agentic_systems/docs/brd.md#34-canonicalization-fr-003)
- Basic validation rules (subset of full rules) - see [BRD FR-002](../../agentic_systems/docs/brd.md#32-data-validation-fr-002) for enhanced rules
- **Simplified evidence bundle generation** - includes required files (manifest.json, plan.md, tool_calls.jsonl, outputs/, summary.md) but not full audit trail features like checkpoints or state management
- No SharePoint integration - see [BRD FR-001](../../agentic_systems/docs/brd.md#31-data-ingestion-fr-001) for SharePoint file reading
- No HITL approval workflow - see [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012) for full HITL implementation
- No external API calls - see [BRD FR-002](../../agentic_systems/docs/brd.md#32-data-validation-fr-002) for prevailing wage API integration

**Assumptions:**

- Files are local (no SharePoint)
- Data fits in memory
- Simple canonical format (can be extended)
- No environment variables or API keys needed

## Next Steps for Full Implementation

1. **PostgreSQL Integration**

- Replace DataFrame storage with PostgreSQL staging tables
- Implement CDM schema (from CFA-provided schema)
- Add database connection management
- Configure `DATABASE_URL` environment variable

2. **Enhanced Validation**

- Integrate CFA-provided validation rules from `clients/cfa/rules.py`
- Add name misspelling detection (fuzzy matching)
- Add prevailing wage validation (external API)
- Configure `WAGE_API_URL` and `WAGE_API_KEY`

3. **Identity Resolution**

- Implement participant matching logic (name + DOB + WSAC ID)
- Handle duplicate detection
- Create vs. update logic

4. **Enhanced BaseAgent Features**

- Add `audit_record()` and `evidence_bundle()` methods (beyond POC's `plan/execute/summarize`) per [PRD-TRD Section 5.1](../../agentic_systems/docs/prd-trd.md#51-baseagent-contract)
- Implement full evidence bundle generation with complete audit trail features (checkpoints, state management) per [PRD-TRD Section 7.4](../../agentic_systems/docs/prd-trd.md#74-evidence-bundle-generation-flow)
- Add state management and externalized state tracking

5. **SharePoint Integration**

- Add `SharePointClient` for file reading
- Implement secure link generation
- Add HITL approval workflow
- Configure SharePoint environment variables

6. **Change Tracking**

- Implement change log recording
- Track before/after values
- Generate diff reports

## Implementation Checklist

### 1) CLI Trigger (file upload = CLI invocation)

- [ ] Update `agentic_systems/cli/main.py` to accept `--file` for `agent run intake` and validate the path
- [ ] Keep run_id pattern `<partner>-<quarter>-<platform>` per [PRD-TRD Section 11.2](../../agentic_systems/docs/prd-trd.md#112-configuration-management) and pass the file path into the agent inputs
- [ ] Print plan before execution and summary after execution

### 2) Tool Protocol + Results Contract

- [ ] Add `agentic_systems/core/tools.py` with `Tool` protocol + `ToolResult` dataclass per [PRD-TRD Section 5.4](../../agentic_systems/docs/prd-trd.md#54-tool-specifications)
- [ ] Design `ToolResult.data` to hold in-memory objects (DataFrames, lists) for tool chaining
- [ ] Ensure `tool_calls.jsonl` logs sanitized metadata only (counts, hashes, status) - no DataFrames or raw data per [PRD-TRD Section 3.2](../../agentic_systems/docs/prd-trd.md#32-evidence-bundle-structure)

### 3) Ingestion Tool (extract/parse)

- [ ] Add `agentic_systems/core/ingestion/ingest_tool.py` per [BRD FR-001](../../agentic_systems/docs/brd.md#31-data-ingestion-fr-001)
- [ ] Parse CSV/Excel, normalize headers, compute file hash
- [ ] Return parsed rows + metadata (row count, columns, hash) in `ToolResult.data`

### 4) Validation Tool (row‑level report)

- [ ] Add `agentic_systems/core/validation/validate_tool.py` per [BRD FR-002](../../agentic_systems/docs/brd.md#32-data-validation-fr-002)
- [ ] Implement required field checks + example business rule(s) (active past graduation) per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules)
- [ ] Emit row‑level report entries: `{row_index, field, severity, message}` - **no raw field values** per [BRD FR-002](../../agentic_systems/docs/brd.md#32-data-validation-fr-002) acceptance criteria and [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules) PII handling
- [ ] Return validation summary counts + row‑level list in `ToolResult.data` (in-memory list for tool chaining)

### 5) Canonicalization Tool (load/canonicalize)

- [ ] Add `agentic_systems/core/canonical/canonicalize_tool.py` per [BRD FR-003](../../agentic_systems/docs/brd.md#34-canonicalization-fr-003)
- [ ] Map staged fields to canonical fields; generate stable POC IDs
- [ ] Return canonical rows + counts in `ToolResult.data`

### 6) Agent Orchestration (BaseAgent contract)

- [ ] Add `agentic_systems/agents/simple_intake_agent.py` per [PRD-TRD Section 5.1](../../agentic_systems/docs/prd-trd.md#51-baseagent-contract)
- [ ] **Remove `agentic_systems/agents/intake_agent.py`** - CLI routes directly to platform implementations, no dispatcher needed. If file exists, delete it to avoid confusion. Existing imports of `intake_agent.py` should be updated to import platform-specific agents directly.
- [ ] `plan()`: return structured steps `List[Dict] `for ingest → validate → canonicalize sequence (human-readable `plan.md` generated from structured steps by `write_evidence.py` per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011))
- [ ] `execute()`: call tools in order, stop on blockers
- **Wrap each tool call with evidence logging** per [PRD-TRD Section 7.4](../../agentic_systems/docs/prd-trd.md#74-evidence-bundle-generation-flow):
    ```python
                                                                                                                        # BaseAgent.execute() wraps tool calls per PRD-TRD Section 7.4
                                                                                                                        def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                                                                                                                            for step in self.plan(inputs):
                                                                                                                                # Emit STEP_START event to tool_calls.jsonl per BRD FR-011
                                                                                                                                self._emit(state, "STEP_START", f"Executing {step['tool']}", 
                                                                                                                                          {"tool": step['tool'], "args": step['args']})
                                                                                                                                
                                                                                                                                # Invoke tool - returns ToolResult with in-memory data for chaining
                                                                                                                                result = self.tools[step['tool']](**step['args'])  # Per PRD-TRD Section 5.4
                                                                                                                                
                                                                                                                                # Emit STEP_END with sanitized metadata only (no DataFrames) per PRD-TRD Section 3.2
                                                                                                                                self._emit(state, "STEP_END", f"Completed {step['tool']}", 
                                                                                                                                          {"tool": step['tool'], "ok": result.ok, 
                                                                                                                                           "summary": result.summary, "row_count": len(result.data.get('dataframe', [])),
                                                                                                                                           "file_hash": result.data.get('file_hash')})  # Metadata only
    ```




                                                                                                                                                                                                                                                                - Emit `STEP_START` event to `tool_calls.jsonl` before tool invocation
                                                                                                                                                                                                                                                                - Invoke tool: `result = tool(**kwargs)` (returns ToolResult with in-memory data for chaining)
                                                                                                                                                                                                                                                                - Emit `STEP_END` event to `tool_calls.jsonl` after tool invocation with sanitized metadata (counts, hashes, status only)
- [ ] `summarize()`: include file, validation counts, canonical row count (summary written to `summary.md` per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011))

### 7) Evidence Bundle Writer (deterministic core tool)

- [ ] Add `agentic_systems/core/audit/write_evidence.py` per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011) and [PRD-TRD Section 3.2](../../agentic_systems/docs/prd-trd.md#32-evidence-bundle-structure)
- [ ] Write `manifest.json`, `plan.md`, `summary.md` from agent state per [PRD-TRD Section 3.2](../../agentic_systems/docs/prd-trd.md#32-evidence-bundle-structure)
- [ ] **Note**: `write_evidence.py` does NOT write `tool_calls.jsonl` - BaseAgent.execute() appends JSONL events directly as tools run
- [ ] **Serialize in-memory tool results to `outputs/` directory** (tools return in-memory data only; evidence writer handles file serialization):
- Serialize validation results to `outputs/validation_report.csv`
- Serialize canonical data to `outputs/canonical.csv`
- [ ] Set `data_classification="Internal"` and `pii_handling="redacted"` in `manifest.json` (JSON values only) per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules)
- [ ] **Code comment in `write_evidence.py`**: `# Masked mock data is treated as Internal; PII is redacted per BRD Section 2.3` (comment in code, not JSON)
- [ ] BaseAgent `execute()` method wraps tool calls and emits trace events to `tool_calls.jsonl` per [PRD-TRD Section 7.4](../../agentic_systems/docs/prd-trd.md#74-evidence-bundle-generation-flow)
- [ ] Ensure `tool_calls.jsonl` logs sanitized metadata only (counts, hashes, status) - no DataFrames or raw data

### 8) Outputs (reports + canonical data)

- [ ] Evidence writer (`write_evidence.py`) serializes in-memory tool results to `outputs/` directory per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011)
- [ ] Serialize validation results to `outputs/validation_report.csv` from validation tool's in-memory results
- [ ] Serialize canonical data to `outputs/canonical.csv` from canonicalization tool's in-memory results
- [ ] **Note**: Tools return in-memory data only; evidence writer handles all file serialization

### 9) Tests (deterministic core)

- [ ] Add unit tests under `agentic_systems/tests/` per [PRD-TRD Section 10.1](../../agentic_systems/docs/prd-trd.md#101-unit-tests) for:
- header normalization + file hash
- row‑level validation detection
- canonical ID generation

### 10) Manual Verification

- [ ] **Working Directory**: Repository root
- [ ] Run Part 1: `python -m agentic_systems.cli.main run intake --file agentic_systems/data/masked/Example\ Quarterly\ Data\ Report.mock.csv --partner demo --quarter Q1 --platform minimal`
- [ ] Verify evidence bundle contents in `agentic_systems/core/audit/runs/<run-id>/`
- [ ] Confirm validation report is row‑level (metadata only: row_index, field, severity, message) and canonical output exists
- [ ] Verify `tool_calls.jsonl` contains sanitized metadata only (no DataFrames)
- [ ] **Part 2 Manual Verification** (requires API key):
- [ ] Run Part 2: `python -m agentic_systems.cli.main run intake --file agentic_systems/data/masked/Example\ Quarterly\ Data\ Report.mock.csv --partner demo --quarter Q1 --platform langchain`
- [ ] Verify LLM-generated plan and summary in evidence bundle
- [ ] Verify `manifest.json` includes platform/model metadata and `egress_approval_ref` per [PRD-TRD Section 3.2](../../agentic_systems/docs/prd-trd.md#32-evidence-bundle-structure)
- [ ] Compare Part 1 vs Part 2 evidence bundles

## Combined Success Criteria

The complete three-part POC is successful when:

### Part 1 Success Criteria

- ✅ Can ingest CSV/Excel files per [BRD FR-001](../../agentic_systems/docs/brd.md#31-data-ingestion-fr-001)
- ✅ Can validate data and report errors/warnings with row-level detail per [BRD FR-002](../../agentic_systems/docs/brd.md#32-data-validation-fr-002)
- ✅ Can canonicalize data to standard format per [BRD FR-003](../../agentic_systems/docs/brd.md#34-canonicalization-fr-003)
- ✅ CLI demonstrates BaseAgent contract (plan → execute → summarize) per [PRD-TRD Section 5.1](../../agentic_systems/docs/prd-trd.md#51-baseagent-contract)
- ✅ Evidence bundle generated with all required files per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011)
- ✅ CLI provides clear feedback on each step
- ✅ Can process at least one mock data file end-to-end
- ✅ Code structure aligns with full system architecture
- ✅ No environment variables required for Part 1 execution
- ✅ Unit tests pass for deterministic core logic per [PRD-TRD Section 10.1](../../agentic_systems/docs/prd-trd.md#101-unit-tests)

### Part 2 Success Criteria

- ✅ LLM generates dynamic plans based on file characteristics
- ✅ LLM orchestrates same tools from Part 1 (no tool changes needed)
- ✅ LLM creates contextual summaries explaining decisions
- ✅ Evidence bundles show LLM-generated plans and summaries
- ✅ BaseAgent contract maintained (same interface as Part 1)
- ✅ Can compare Part 1 vs Part 2 evidence bundles side-by-side
- ✅ Demonstrates platform flexibility per [PRD-TRD Section 6.4](../../agentic_systems/docs/prd-trd.md#64-platform-adapter-specifications)

### Part 3 Success Criteria

- ✅ Validation errors trigger error report generation
- ✅ Error report CSV contains full row data for error rows
- ✅ Email template includes per-row error explanations
- ✅ Staff approval is required before sending email per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012)
- ✅ Staff can review email content and approve/reject
- ✅ Secure link code is generated only after staff approval (demo version)
- ✅ Email is sent (or marked ready) only after staff approval
- ✅ Execution halts when errors are found or approval is rejected
- ✅ Resume functionality works with corrected files
- ✅ File watch detects corrected files (optional)
- ✅ Evidence bundle includes HITL artifacts and approval records
- ✅ Both minimal and langchain platforms support HITL workflow

## Timeline

### Part 1 Timeline

- **Setup**: 5 minutes (run setup script, install dependencies)
- **Implementation**: 20-30 minutes (create files, test)
- **Testing**: 5-10 minutes (run with mock data, verify output)
- **Total**: ~30-45 minutes for Part 1 deployment

### Part 2 Timeline (Additional)

- **Setup**: 5 minutes (install LangChain dependencies, set API key)
- **Implementation**: 30-40 minutes (create adapter, LLM agent, update CLI)
- **Testing**: 10 minutes (run both platforms, compare outputs)
- **Total**: ~45-55 minutes for Part 2 (adds to Part 1)

### Part 3 Timeline (Additional)

- **Setup**: 5 minutes (create new package structure)
- **Implementation**: 60-90 minutes (tools + agent updates + CLI resume)
- **Testing**: 20 minutes (end-to-end HITL workflow)
- **Total**: ~85-115 minutes for Part 3 (adds to Parts 1 and 2)
- **Combined Total**: ~160-215 minutes for complete three-part demonstration

## File Locations

### Part 1 Files

- `agentic_systems/core/tools.py`
- `agentic_systems/core/ingestion/ingest_tool.py`
- `agentic_systems/core/validation/validate_tool.py`
- `agentic_systems/core/canonical/canonicalize_tool.py`
- `agentic_systems/core/audit/write_evidence.py` (new - evidence bundle writer)
- `agentic_systems/agents/simple_intake_agent.py`
- `agentic_systems/agents/intake_agent.py` (delete if exists - CLI routes directly to platform implementations)
- `agentic_systems/cli/main.py` (update existing)
- `agentic_systems/tests/test_ingest_tool.py` (new - unit tests)
- `agentic_systems/tests/test_validate_tool.py` (new - unit tests)
- `agentic_systems/tests/test_canonicalize_tool.py` (new - unit tests)
- `agentic_systems/setup_poc.sh` (or `.bat`)
- `.env.example` (new - at repository root, not in `agentic_systems/`)

### Part 2 Files (Additional)

- `agentic_systems/agents/platforms/langchain/__init__.py` (new)
- `agentic_systems/agents/platforms/langchain/adapter.py` (new - tool conversion layer)
- `agentic_systems/agents/platforms/langchain/intake_impl.py` (new - LLM-based agent)

### Part 3 Files (Additional)

- `agentic_systems/core/partner_communication/__init__.py` (new)
- `agentic_systems/core/partner_communication/collect_wsac_aggregates_tool.py` (new)
- `agentic_systems/core/partner_communication/generate_error_report_tool.py` (new)
- `agentic_systems/core/partner_communication/generate_email_tool.py` (new)
- `agentic_systems/core/partner_communication/secure_link_tool.py` (new)
- `agentic_systems/core/partner_communication/request_approval_tool.py` (new)
- `agentic_systems/core/partner_communication/upload_sharepoint_tool.py` (new or update)
- `agentic_systems/tests/test_generate_error_report_tool.py` (new)
- `agentic_systems/tests/test_generate_email_tool.py` (new)
- `agentic_systems/tests/test_secure_link_tool.py` (new)
- `agentic_systems/tests/test_request_approval_tool.py` (new)
- `agentic_systems/tests/test_upload_sharepoint_tool.py` (new)

## Part 1 Notes for Instructors

- This POC demonstrates the tool-based architecture and BaseAgent contract without full complexity
- Can be used to show interns the pattern before full implementation
- Easy to extend incrementally (add PostgreSQL, then validation rules, then identity resolution)

### Teaching Points

- **Emphasize the contract-first design**: All agents must implement `plan()`, `execute()`, and `summarize()` methods
- **Show agent orchestration**: Demonstrate how agents coordinate tools but don't perform data transformations themselves
- **Separation of concerns**: Tools do the work, agents coordinate and explain
- **Walk through the flow**: Use the CLI output to walk through the plan → execute → summarize lifecycle
- **Scalability demonstration**: Point out that this pattern scales to full implementation with evidence bundles, state management, and audit trails

### For Interns

- **Starting baseline**: This is their foundation - they can extend it incrementally
- **Zero setup friction**: No environment variables required - just clone, install dependencies, and run
- **Clear extension points**: Code structure shows exactly where to add features (PostgreSQL integration, SharePoint, enhanced validation)
- **Contract compliance**: BaseAgent contract ensures consistency across all agent implementations they'll build
- **Learning progression**: Start with this simple POC, then add complexity one layer at a time

---

# Part 2: LLM-Based Orchestration (Agentic AI in Action)

## Part 2 Overview

Part 2 extends Part 1 to demonstrate LLM-based orchestration while maintaining the same BaseAgent contract and using the same deterministic tools. The LLM acts as an intelligent orchestrator that:

- Generates dynamic execution plans based on file characteristics
- Handles errors and adapts plans dynamically
- Creates contextual summaries explaining decisions
- Uses the same tools from Part 1 (no changes to core tools)

This demonstrates how the contract-first design enables platform flexibility per [PRD-TRD Section 6.4](../../agentic_systems/docs/prd-trd.md#64-platform-adapter-specifications).

## Part 2 Architecture

The POC extends Part 1 with LLM orchestration:

```javascript
Partner File (CSV/Excel)
    ↓
[LLMIntakeAgent.plan()] → LLM generates dynamic plan based on file analysis
    ↓
[LLMIntakeAgent.execute()] → LLM orchestrates tools, handles errors adaptively
    ↓
[Same Tools from Part 1]
    ↓
[IngestPartnerFileTool] → Extract & Parse (deterministic)
    ↓
[ValidateStagedDataTool] → Transform & Validate (deterministic)
    ↓
[CanonicalizeStagedDataTool] → Load & Canonicalize (deterministic)
    ↓
[LLMIntakeAgent.summarize()] → LLM generates contextual summary
    ↓
Canonical Data + AI-Generated Summary
```

**Key Difference from Part 1:**

- Part 1: Hardcoded plan, simple string concatenation for summary
- Part 2: LLM generates plan dynamically, creates contextual summaries, handles errors intelligently
- **Same tools, same contract, different orchestration intelligence**

## Part 2 Implementation Plan

### File Structure (Additional Files for Part 2)

13. **`agentic_systems/agents/platforms/langchain/__init__.py`** (empty)
14. **`agentic_systems/agents/platforms/langchain/adapter.py`** (new)

                                                                                                                                                                                                                                                                - Tool conversion layer: BaseAgent `Tool` → LangChain `@tool` format per [PRD-TRD Section 6.4](../../agentic_systems/docs/prd-trd.md#64-platform-adapter-specifications)
                                                                                                                                                                                                                                                                - State conversion: BaseAgent `AgentState` ↔ LangChain state
                                                                                                                                                                                                                                                                - Result conversion: LangChain results → BaseAgent `ToolResult`
                                                                                                                                                                                                                                                                - Wraps Part 1 tools for LLM orchestration

15. **`agentic_systems/agents/platforms/langchain/intake_impl.py`** (new)

                                                                                                                                                                                                                                                                - `LangChainIntakeAgent` class extending `BaseAgent` contract
                                                                                                                                                                                                                                                                - Uses LangChain internally for LLM orchestration per [PRD-TRD Section 6.4](../../agentic_systems/docs/prd-trd.md#64-platform-adapter-specifications)
                                                                                                                                                                                                                                                                - Implements `plan()`, `execute()`, and `summarize()` using LLM
                                                                                                                                                                                                                                                                - Converts BaseAgent tools to LangChain tools via adapter
                                                                                                                                                                                                                                                                - Maintains BaseAgent contract compliance

## Part 2 Key Implementation Details

### LLM-Based Planning

**`plan(inputs: Dict[str, Any]) -> List[Dict[str, Any]]`** (per [PRD-TRD Section 6.4](../../agentic_systems/docs/prd-trd.md#64-platform-adapter-specifications)):

- Uses LLM (OpenAI GPT-4 or Claude) to analyze preflight metadata and inputs
- **Preflight Step**: Before plan(), read file metadata (size, extension, header row) without full ingestion
- **LLM Input Restrictions (per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules)):**
- LLM receives **preflight metadata only**: file name, size, extension, column names from header (no row data)
- Validation error counts and types (not row-level details) - only available during execution, not planning
- Tool execution status summaries - only available during execution, not planning
- **No raw participant data, no PII, no field values** - ensures "redacted" PII handling
- Generates dynamic plan based on file characteristics (format, size, expected structure from preflight)
- Prompt includes tool descriptions and available tools
- Returns structured execution steps: `[{'tool': 'IngestPartnerFileTool', 'args': {...}}, ...]`
- Human-readable `plan.md` is generated from structured steps by `write_evidence.py`
- Example structured steps: `[{'tool': 'IngestPartnerFileTool', 'args': {'file_path': '...'}}, {'tool': 'ValidateStagedDataTool', 'args': {...}}, {'tool': 'CanonicalizeStagedDataTool', 'args': {...}}]`

### LLM-Based Execution

**`execute(inputs: Dict[str, Any]) -> Dict[str, Any]`** (per [PRD-TRD Section 6.4](../../agentic_systems/docs/prd-trd.md#64-platform-adapter-specifications)):

- Uses LangChain `AgentExecutor` to orchestrate tools per [PRD-TRD Section 6.4](../../agentic_systems/docs/prd-trd.md#64-platform-adapter-specifications)
- **LLM Input Restrictions (per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules)):**
- LLM receives tool summaries (metadata) only - no raw data
- Tool execution context includes counts, status, error types - not field values
- LLM selects tools dynamically based on execution context
- Handles errors adaptively: if validation fails, LLM can suggest next steps
- Converts LangChain tool calls to BaseAgent tool invocations
- Records all decisions in evidence bundle per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011)

### LLM-Based Summarization

**`summarize(run_results: Dict[str, Any]) -> str`** (per [PRD-TRD Section 5.1](../../agentic_systems/docs/prd-trd.md#51-baseagent-contract)):

- Uses LLM to generate contextual summary
- **LLM Input Restrictions (per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules)):**
- LLM receives **metadata only**: validation error counts, types, severity breakdowns
- Row-level validation entries (metadata: row_index, field, severity, message - no raw values)
- Tool execution summaries (counts, status)
- **No raw participant data, no PII, no field values** - ensures "redacted" PII handling
- Explains what happened, why decisions were made, and what issues were found
- References specific validation error types and their implications (without exposing raw data)
- Provides actionable next steps if blockers exist
- Example: "Processed 500 rows from quarterly report. Validation found 3 errors (active past graduation) and 12 warnings (missing optional fields). Canonicalized 485 valid records. Errors require partner correction before proceeding..."

### Tool Adapter Pattern

Per [PRD-TRD Section 6.4](../../agentic_systems/docs/prd-trd.md#64-platform-adapter-specifications), tools from Part 1 are wrapped for LangChain:

```python
# In adapter.py - converts BaseAgent tools to LangChain format per PRD-TRD Section 6.4
def _baseagent_tool_to_langchain(self, name: str, tool_impl: Tool):
    @tool(name=name, description=f"Tool: {name}")
    def langchain_wrapper(**kwargs) -> str:
        # Calls Part 1 deterministic tool (same tools, no changes needed)
        # Tool returns ToolResult with in-memory data (DataFrame) for tool chaining
        result = tool_impl(**kwargs)  # Per PRD-TRD Section 5.4 Tool protocol
        
        if result.ok:
            # LLM receives summary only (metadata) - no raw data per BRD Section 2.3
            # This ensures "redacted" PII handling when LLM processes tool results
            return result.summary
        else:
            return f"Error: {result.summary}. Blockers: {result.blockers}"
    return langchain_wrapper
```

**Key Point**: Same deterministic tools from Part 1, just wrapped for LLM orchestration. LLM receives tool summaries (metadata) only, not raw data per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules).

## Part 2 Dependencies

Additional dependencies for Part 2:

- `langchain` - LLM orchestration framework
- `langchain-openai` or `langchain-anthropic` - LLM provider integration
- `openai` or `anthropic` - LLM API clients

Installation:

```bash
pip install langchain langchain-openai openai
# OR
pip install langchain langchain-anthropic anthropic
```



## Part 2 Environment Variables

Part 2 requires LLM API keys (not needed for Part 1):

```bash
# Add to .env for Part 2 (already documented in .env.example)
OPENAI_API_KEY=sk-your-openai-api-key
# OR
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
```

**Note**: Part 1 remains completely self-contained (no API keys needed).

## Part 2 Testing Strategy

### Test Commands

```bash
# Part 1: Deterministic (no LLM)
python -m agentic_systems.cli.main run intake --file agentic_systems/data/masked/Example\ Quarterly\ Data\ Report.mock.csv --partner demo --quarter Q1 --platform minimal

# Part 2: LLM-based orchestration (requires API key)
python -m agentic_systems.cli.main run intake --file agentic_systems/data/masked/Example\ Quarterly\ Data\ Report.mock.csv --partner demo --quarter Q1 --platform langchain
```



### Expected Differences

**Part 1 Output:**

- Hardcoded plan: "1. Ingest partner file, 2. Validate staged data, 3. Canonicalize..."
- Simple summary: "Processed file. Found X errors, Y warnings. Generated Z canonical records."

**Part 2 Output:**

- Dynamic plan: "Analyzing file... Detected CSV with 500 rows. Plan: Ingest with UTF-8 encoding detection, validate required fields (first_name, last_name, DOB) and active past graduation rule, canonicalize with sequential ID generation..."
- Contextual summary: "Successfully processed quarterly report. Validation identified 3 critical errors where participants are marked active past their graduation date - these must be corrected by partner before canonicalization. Generated 485 valid canonical records. Next steps: Partner should review validation report and correct status fields..."

## Part 2 Implementation Checklist

### 1) LangChain Platform Adapter

- [ ] Create `agentic_systems/agents/platforms/langchain/adapter.py` per [PRD-TRD Section 6.4](../../agentic_systems/docs/prd-trd.md#64-platform-adapter-specifications)
- [ ] Implement `_baseagent_tool_to_langchain()` to wrap Part 1 tools
  ```python
                                                            # Tool adapter per PRD-TRD Section 6.4
                                                            def _baseagent_tool_to_langchain(self, name: str, tool_impl: Tool):
                                                                @tool(name=name, description=f"Tool: {name}")
                                                                def langchain_wrapper(**kwargs) -> str:
                                                                    # Calls Part 1 deterministic tool - same tools, no changes needed
                                                                    result = tool_impl(**kwargs)  # Per PRD-TRD Section 5.4 Tool protocol
                                                                    # LLM receives summary only (metadata) - no raw data per BRD Section 2.3
                                                                    return result.summary if result.ok else f"Error: {result.summary}"
                                                                return langchain_wrapper
  ```




- [ ] Implement state conversion methods (BaseAgent ↔ LangChain) per [PRD-TRD Section 6.4](../../agentic_systems/docs/prd-trd.md#64-platform-adapter-specifications)

### 2) LLM-Based Intake Agent

- [ ] Create `agentic_systems/agents/platforms/langchain/intake_impl.py` per [PRD-TRD Section 6.4](../../agentic_systems/docs/prd-trd.md#64-platform-adapter-specifications)
- [ ] Add preflight metadata extraction before LLM plan() (reads file size, extension, header row without full ingestion)
- [ ] Implement `plan()` using LLM with tool descriptions and preflight metadata
- **LLM receives preflight metadata only** (file name, size, extension, column names from header - no row data) per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules)
- Returns structured steps `List[Dict]` (same contract as Part 1)
- No raw data sent to LLM
- [ ] Implement `execute()` using LangChain `AgentExecutor` per [PRD-TRD Section 6.4](../../agentic_systems/docs/prd-trd.md#64-platform-adapter-specifications)
- LLM receives tool summaries (metadata) only - no raw data per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules)
- [ ] Implement `summarize()` using LLM with run results context
- **LLM receives metadata only** (error counts, types, severity breakdowns) per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules)
- Row-level validation entries (metadata: row_index, field, severity, message - no raw values)
- [ ] Ensure BaseAgent contract compliance per [PRD-TRD Section 5.1](../../agentic_systems/docs/prd-trd.md#51-baseagent-contract)
- [ ] Update `manifest.json` to include `"platform": "langchain"`, `"model": "gpt-4"`, `"egress_approval_ref": null` per [PRD-TRD Section 3.2](../../agentic_systems/docs/prd-trd.md#32-evidence-bundle-structure)

### 3) CLI Platform Selection

- [ ] Update `cli/main.py` to support `--platform langchain` option per [PRD-TRD Section 11.2](../../agentic_systems/docs/prd-trd.md#112-configuration-management)
- [ ] **Direct instantiation routing** (per [PRD-TRD Section 6.4](../../agentic_systems/docs/prd-trd.md#64-platform-adapter-specifications)):
  ```python
                                                            # CLI directly instantiates platform-specific agents per PRD-TRD Section 6.4
                                                            # No dispatcher needed - CLI routes directly to platform implementations
                                                            if args.platform == "minimal":
                                                                from agentic_systems.agents.simple_intake_agent import SimpleIntakeAgent
                                                                agent = SimpleIntakeAgent()  # Part 1: Deterministic baseline
                                                            elif args.platform == "langchain":
                                                                from agentic_systems.agents.platforms.langchain.intake_impl import LangChainIntakeAgent
                                                                agent = LangChainIntakeAgent()  # Part 2: LLM orchestration
                                                            else:
                                                                raise ValueError(f"Unknown platform: {args.platform}")
                                                            
                                                            # Demonstrate BaseAgent contract per PRD-TRD Section 5.1
                                                            plan = agent.plan({"file_path": args.file, "run_id": run_id})
                                                            print("=== PLAN ===")
                                                            print(plan)  # Per BRD FR-011, plan shown before execution
                                                            
                                                            results = agent.execute({"file_path": args.file, "run_id": run_id})
                                                            
                                                            summary = agent.summarize(results)
                                                            print("\n=== SUMMARY ===")
                                                            print(summary)  # Per BRD FR-011, summary shown after execution
  ```




- [ ] Route to `LangChainIntakeAgent` when platform is "langchain"
- [ ] Route to `SimpleIntakeAgent` when platform is "minimal" (Part 1)

### 4) Evidence Bundle Comparison

- [ ] Run same file with both platforms
- [ ] Compare evidence bundles: same structure, different plan/summary content
- [ ] Verify both produce valid evidence bundles per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011)
- [ ] Verify Part 2 `manifest.json` includes platform/model metadata and `egress_approval_ref` per [PRD-TRD Section 3.2](../../agentic_systems/docs/prd-trd.md#32-evidence-bundle-structure)

### 5) Security Documentation

- [ ] Update `agentic_systems/security/allowlist.md` with LLM platform entries per [README Section "Security Preflight"](README.md#security-preflight-recommended) and [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules) (data classification and PII handling):
- "OpenAI API / Anthropic API - Approved for POC with Internal data classification only. Requires `egress_approval_ref` in manifest for Restricted data."

## Part 2 Success Criteria

Part 2 is successful when:

- ✅ LLM generates dynamic plans based on file characteristics
- ✅ LLM orchestrates same tools from Part 1 (no tool changes needed)
- ✅ LLM creates contextual summaries explaining decisions
- ✅ Evidence bundles show LLM-generated plans and summaries
- ✅ BaseAgent contract maintained (same interface as Part 1)
- ✅ Can compare Part 1 vs Part 2 evidence bundles side-by-side
- ✅ Demonstrates platform flexibility per [PRD-TRD Section 6.4](../../agentic_systems/docs/prd-trd.md#64-platform-adapter-specifications)

## Part 2 Timeline

- **Setup**: 5 minutes (install LangChain dependencies, set API key)
- **Implementation**: 30-40 minutes (create adapter, LLM agent, update CLI)
- **Testing**: 10 minutes (run both platforms, compare outputs)
- **Total**: ~45-55 minutes for Part 2 (adds to Part 1's 30-45 minutes)

## Part 2 Teaching Points

### For Instructors

- **Contract Consistency**: Show how same BaseAgent contract works with deterministic and LLM orchestration
- **Tool Reusability**: Emphasize that Part 1 tools are reused in Part 2 (no changes needed)
- **Platform Flexibility**: Demonstrate how contract-first design enables platform comparison
- **Evidence Comparison**: Compare Part 1 vs Part 2 evidence bundles to show what changes (plan/summary) and what stays the same (tools, structure)

### For Interns

- **Progressive Complexity**: Start with Part 1 (understand the pattern), then add Part 2 (see AI in action)
- **Same Tools, Different Intelligence**: Tools remain deterministic; only orchestration uses AI
- **Platform Evaluation**: Learn how to evaluate different orchestration approaches while maintaining contract compliance

---

# Part 3: HITL Partner Communication Workflow

## Part 3 Overview

Part 3 extends Parts 1 and 2 to demonstrate a complete HITL workflow where validation errors trigger partner communication. When validation fails, the system:

1. Generates a CSV file containing full row data for all rows with errors (PII included)
2. **Collects aggregates from partner data and compares against WSAC prior-quarter data** (per [BRD FR-004](../../agentic_systems/docs/brd.md#35-wsac-reconciliation-fr-004) and [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules))
3. Creates a templated email explaining errors per row
4. **Includes WSAC aggregates comparison in partner error report** to help partners understand data discrepancies
5. **Requests CFA staff approval before sending email** per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012)
6. After staff approval: Implements lightweight secure link sharing and sends email to partner per [BRD FR-013](../../agentic_systems/docs/brd.md#33-secure-partner-sharing-fr-013)
7. Halts processing and waits for partner corrections per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012)
8. **When partner fixes errors and re-uploads: Re-validates data, re-checks WSAC aggregates comparison, and re-validates WSAC upload rules** (prevailing wage, name misspelling, aggregate discrepancies) per [BRD FR-005](../../agentic_systems/docs/brd.md#36-wsac-export-generation-fr-005) and [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules)
9. Resumes validation and canonicalization when corrections are detected (file watch or CLI resume) per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012)

This demonstrates the complete error correction cycle while maintaining PII security through secure links and ensuring staff oversight of partner communications. The WSAC aggregates comparison helps partners understand data quality issues and ensures compliance with WSAC upload requirements.

## Part 3 Architecture

```mermaid
flowchart TD
    A[IngestPartnerFileTool] --> B[ValidateStagedDataTool]
    B --> C{Errors Found?}
    C -->|No| D[CanonicalizeStagedDataTool]
    C -->|Yes| E[CollectWSACAggregatesTool]
    E --> F[GeneratePartnerErrorReportTool]
    F --> G[GeneratePartnerEmailTool]
    G --> H[RequestStaffApproval]
    H --> I{Staff Approved?}
    I -->|No| J[Halt - Approval Rejected]
    I -->|Yes| K[CreateSecureLinkTool]
    K --> L[SendEmailToPartner]
    L --> M[Halt - Wait for Corrections]
    M --> N{Resume Triggered?}
    N -->|File Watch| O[Detect Corrected File]
    N -->|CLI Resume| P[CLI --resume flag]
    O --> Q[Re-validate Corrected File]
    P --> Q
    Q --> R[Re-check WSAC Aggregates]
    R --> S[Re-check WSAC Upload Rules]
    S --> T{All Checks Pass?}
    T -->|Yes| D
    T -->|No| E
```



## Part 3 Implementation Plan

### File Structure (Additional Files for Part 3)

16. **`agentic_systems/core/partner_communication/__init__.py`** (empty)
17. **`agentic_systems/core/partner_communication/collect_wsac_aggregates_tool.py`** (new)

                                                                                                                                                                                                                                                                - `CollectWSACAggregatesTool` class per [BRD FR-004](../../agentic_systems/docs/brd.md#35-wsac-reconciliation-fr-004) and [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules)
                                                                                                                                                                                                                                                                - Collects aggregates from partner data:
                                                                                                                                                                                                                                                                                                                                                                                                - Total participants
                                                                                                                                                                                                                                                                                                                                                                                                - Total enrollments
                                                                                                                                                                                                                                                                                                                                                                                                - Total employment placements
                                                                                                                                                                                                                                                                                                                                                                                                - Status breakdowns (active, graduated, withdrawn)
                                                                                                                                                                                                                                                                                                                                                                                                - Employment status breakdowns
                                                                                                                                                                                                                                                                - Compares against WSAC prior-quarter data (if available):
                                                                                                                                                                                                                                                                                                                                                                                                - Participant count changes
                                                                                                                                                                                                                                                                                                                                                                                                - Enrollment count changes
                                                                                                                                                                                                                                                                                                                                                                                                - Employment placement changes
                                                                                                                                                                                                                                                                                                                                                                                                - Status transition patterns
                                                                                                                                                                                                                                                                - Flags significant discrepancies (e.g., >10% change in participant count) as warnings
                                                                                                                                                                                                                                                                - Returns aggregates comparison in `ToolResult.data` per [PRD-TRD Section 5.4](../../agentic_systems/docs/prd-trd.md#54-tool-specifications)
                                                                                                                                                                                                                                                                - **Note**: For POC, WSAC prior-quarter data may be mock/placeholder; production will load from PostgreSQL CDM per [BRD FR-004](../../agentic_systems/docs/brd.md#35-wsac-reconciliation-fr-004)

18. **`agentic_systems/core/partner_communication/generate_error_report_tool.py`** (new)

                                                                                                                                                                                                                                                                - `GeneratePartnerErrorReportTool` class per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012)
                                                                                                                                                                                                                                                                - Takes validation violations + staged DataFrame + WSAC aggregates comparison (optional)
                                                                                                                                                                                                                                                                - Filters DataFrame to rows with errors (by row_index)
                                                                                                                                                                                                                                                                - Adds violation details as columns (error_fields, error_messages, severity_summary)
                                                                                                                                                                                                                                                                - **Adds WSAC aggregates comparison section** to error report:
                                                                                                                                                                                                                                                                                                                                                                                                - Partner data aggregates vs. WSAC prior-quarter aggregates
                                                                                                                                                                                                                                                                                                                                                                                                - Discrepancies flagged as warnings
                                                                                                                                                                                                                                                                                                                                                                                                - Explanation of what the comparison means
                                                                                                                                                                                                                                                                - Returns CSV path in ToolResult.data per [PRD-TRD Section 5.4](../../agentic_systems/docs/prd-trd.md#54-tool-specifications)
                                                                                                                                                                                                                                                                - **Note**: Contains full PII - must be shared via secure link only per [BRD FR-013](../../agentic_systems/docs/brd.md#33-secure-partner-sharing-fr-013) and [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules)

19. **`agentic_systems/core/partner_communication/generate_email_tool.py`** (new)

                                                                                                                                                                                                                                                                - `GeneratePartnerEmailTool` class per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012)
                                                                                                                                                                                                                                                                - Takes error report CSV path + violations list
                                                                                                                                                                                                                                                                - Generates templated email with:
                                                                                                                                                                                                                                                                                                                                                                                                - Summary of error counts by type
                                                                                                                                                                                                                                                                                                                                                                                                - Per-row error explanations (row number, field, reason)
                                                                                                                                                                                                                                                                                                                                                                                                - Secure link URL (placeholder for demo) per [BRD FR-013](../../agentic_systems/docs/brd.md#33-secure-partner-sharing-fr-013)
                                                                                                                                                                                                                                                                                                                                                                                                - Instructions for accessing corrected file
                                                                                                                                                                                                                                                                - Returns email content (HTML/text) in ToolResult.data per [PRD-TRD Section 5.4](../../agentic_systems/docs/prd-trd.md#54-tool-specifications)
                                                                                                                                                                                                                                                                - **Note**: Email template does NOT include PII - only error metadata per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules)

20. **`agentic_systems/core/partner_communication/secure_link_tool.py`** (new)

                                                                                                                                                                                                                                                                - `CreateSecureLinkTool` class (lightweight demo version) per [BRD FR-013](../../agentic_systems/docs/brd.md#33-secure-partner-sharing-fr-013)
                                                                                                                                                                                                                                                                - Generates cryptographically secure access code (`secrets.token_urlsafe(16)`) per [BRD FR-013](../../agentic_systems/docs/brd.md#33-secure-partner-sharing-fr-013) acceptance criteria
                                                                                                                                                                                                                                                                - For demo: Writes access code to `evidence_dir/secure_link_code.txt`
                                                                                                                                                                                                                                                                - For demo: Creates local file URL (file:// or http://localhost:8000/secure-link/<code>)
                                                                                                                                                                                                                                                                - **Explicit comments** mark where production would use per [BRD FR-013](../../agentic_systems/docs/brd.md#33-secure-partner-sharing-fr-013):
                                                                                                                                                                                                                                                                                                                                                                                                - PostgreSQL `secure_links` table storage
                                                                                                                                                                                                                                                                                                                                                                                                - SharePoint secure link generation
                                                                                                                                                                                                                                                                                                                                                                                                - Email service integration
                                                                                                                                                                                                                                                                - Returns secure link URL and access code in ToolResult.data per [PRD-TRD Section 5.4](../../agentic_systems/docs/prd-trd.md#54-tool-specifications)

21. **`agentic_systems/core/partner_communication/request_approval_tool.py`** (new)

                                                                                                                                                                                                                                                                - `RequestStaffApprovalTool` class per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012)
                                                                                                                                                                                                                                                                - Takes email content and error report path
                                                                                                                                                                                                                                                                - For POC: Interactive CLI prompt asking staff to review and approve
                                                                                                                                                                                                                                                                - Displays email preview and error summary
                                                                                                                                                                                                                                                                - Waits for staff input (approve/reject) per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012) acceptance criteria
                                                                                                                                                                                                                                                                - Returns approval status and staff comments in ToolResult.data per [PRD-TRD Section 5.4](../../agentic_systems/docs/prd-trd.md#54-tool-specifications)
                                                                                                                                                                                                                                                                - **Production comments** mark where Teams Adaptive Card integration would occur per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012)

### Modified Files for Part 3

21. **`agentic_systems/agents/simple_intake_agent.py`** (update)

                                                                                                                                                                                                                                                                - Add HITL workflow to `execute()` method per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012):
                                                                                                                                                                                                                                                                                                                                                                                                - After validation, check for errors
                                                                                                                                                                                                                                                                                                                                                                                                - If errors found: call error report, email generation, and staff approval tools
                                                                                                                                                                                                                                                                                                                                                                                                - If approved: call secure link tool and send email per [BRD FR-013](../../agentic_systems/docs/brd.md#33-secure-partner-sharing-fr-013)
                                                                                                                                                                                                                                                                                                                                                                                                - If rejected: halt execution with rejection reason per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012)
                                                                                                                                                                                                                                                                                                                                                                                                - Store resume state in evidence bundle (`resume_state.json`)
                                                                                                                                                                                                                                                                - Add `resume()` method per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012):
                                                                                                                                                                                                                                                                                                                                                                                                - Load resume state from evidence bundle
                                                                                                                                                                                                                                                                                                                                                                                                - Re-validate corrected file
                                                                                                                                                                                                                                                                                                                                                                                                - If validation passes: continue to canonicalization
                                                                                                                                                                                                                                                                                                                                                                                                - If validation fails: regenerate error report

22. **`agentic_systems/agents/platforms/langchain/intake_impl.py`** (update)

                                                                                                                                                                                                                                                                - Add same HITL workflow to `execute()` method per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012)
                                                                                                                                                                                                                                                                - LLM can generate contextual email content (using metadata only) per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules)
                                                                                                                                                                                                                                                                - Staff approval step required before sending email (same as SimpleIntakeAgent) per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012)
                                                                                                                                                                                                                                                                - Add `resume()` method (same as SimpleIntakeAgent) per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012)

23. **`agentic_systems/core/audit/write_evidence.py`** (update)

                                                                                                                                                                                                                                                                - Add `write_resume_state()` function per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012):
                                                                                                                                                                                                                                                                                                                                                                                                - Saves run_id, original_file_path, corrected_file_path (when available)
                                                                                                                                                                                                                                                                                                                                                                                                - Saves validation violations for comparison
                                                                                                                                                                                                                                                                                                                                                                                                - Saves secure link code and URL per [BRD FR-013](../../agentic_systems/docs/brd.md#33-secure-partner-sharing-fr-013)
                                                                                                                                                                                                                                                                                                                                                                                                - Saves staff approval record per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012)
                                                                                                                                                                                                                                                                - Update `serialize_outputs()` to include per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011):
                                                                                                                                                                                                                                                                                                                                                                                                - `outputs/partner_error_report.csv` (full row data with errors)
                                                                                                                                                                                                                                                                                                                                                                                                - `outputs/partner_email.txt` (templated email content - before approval)
                                                                                                                                                                                                                                                                                                                                                                                                - `outputs/partner_email_approved.txt` (approved email - after staff approval)
                                                                                                                                                                                                                                                                                                                                                                                                - `outputs/staff_approval_record.json` (approval decision and timestamp)
                                                                                                                                                                                                                                                                                                                                                                                                - `secure_link_code.txt` (access code for demo - only if approved)

24. **`agentic_systems/core/partner_communication/upload_sharepoint_tool.py`** (new or update)

                                                                                                                                                                                                                                                                - `UploadSharePointTool` class per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012) and [BRD FR-013](../../agentic_systems/docs/brd.md#33-secure-partner-sharing-fr-013)
                                                                                                                                                                                                                                                                - Supports three `folder_type` values in demo mode:
                                                                                                                                                                                                                                                                                                                                                                                                - `"internal"` → copies files into `sharepoint_simulation/internal/<run-id>/` for staff review worksheet (FR-012)
                                                                                                                                                                                                                                                                                                                                                                                                - `"partner"` or `"partner_accessible"` → copies files into `sharepoint_simulation/partner_accessible/<run-id>/` for partner-facing error report (FR-013)
                                                                                                                                                                                                                                                                                                                                                                                                - `"upload"` → copies files into `sharepoint_simulation/uploads/<run-id>/` as simulated partner upload/drop-off location for corrected files (BRD FR-012 validation retry & resume)
                                                                                                                                                                                                                                                                - Returns `file://` URL for demo mode
                                                                                                                                                                                                                                                                - **Explicit comments** distinguish demo-only behavior (local filesystem) vs. production SharePoint client expectations
                                                                                                                                                                                                                                                                - Inline comments reference **BRD FR-012/FR-013** and **PRD-TRD SharePoint tools section**
                                                                                                                                                                                                                                                                - Returns file path/URL in ToolResult.data per [PRD-TRD Section 5.4](../../agentic_systems/docs/prd-trd.md#54-tool-specifications)

25. **`agentic_systems/cli/main.py`** (update)

                                                                                                                                                                                                                                                                - Add `--resume <run-id>` argument per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012) and [PRD-TRD Section 11.2](../../agentic_systems/docs/prd-trd.md#112-configuration-management)
                                                                                                                                                                                                                                                                - When resume flag is set:
                                                                                                                                                                                                                                                                                                                                                                                                - Load agent from evidence bundle manifest
                                                                                                                                                                                                                                                                                                                                                                                                - Call `agent.resume()` with corrected file path
                                                                                                                                                                                                                                                                                                                                                                                                - Continue evidence bundle generation per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011)
                                                                                                                                                                                                                                                                - Add `--watch <run-id>` option per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012):
                                                                                                                                                                                                                                                                                                                                                                                                - Resolves `<run-id>` → evidence directory
                                                                                                                                                                                                                                                                                                                                                                                                - Polls `sharepoint_simulation/uploads/<run-id>/` folder at configurable interval (e.g., every 5 seconds)
                                                                                                                                                                                                                                                                                                                                                                                                - Detects new corrected files (any non-empty file created after `resume_state.timestamp` OR filename pattern like `<partner>_<quarter>_corrected.*`)
                                                                                                                                                                                                                                                                                                                                                                                                - When new file detected, invokes same internal path as `--resume` with that file
                                                                                                                                                                                                                                                                                                                                                                                                - **Clearly comment** that in production this would be replaced by SharePoint webhook handler calling the same resume entry point (per PRD-TRD 4.1 and 4.4)
                                                                                                                                                                                                                                                                                                                                                                                                - Ensure polling logic is clearly marked as **demo-only** and does not violate PRD-TRD's production story (webhook-based)

## Part 3 Key Implementation Details

### GeneratePartnerErrorReportTool

**Purpose**: Create CSV with full row data for rows containing validation errors.**Inputs**:

- `staged_dataframe`: Original DataFrame from ingestion
- `violations`: List of violation dicts from ValidateStagedDataTool
- `output_path`: Path where CSV should be written

**Logic**:

1. Extract unique `row_index` values from violations (filter out -1 for file-level errors)
2. Filter DataFrame to rows with errors: `error_rows = staged_dataframe.iloc[error_row_indices]`
3. For each error row, aggregate violations:

                                                                                                                                                                                                - `error_fields`: Comma-separated list of fields with errors
                                                                                                                                                                                                - `error_messages`: Comma-separated list of error messages
                                                                                                                                                                                                - `severity_summary`: Highest severity (Error > Warning > Info)

4. Add aggregated columns to error rows DataFrame
5. Write to CSV (includes all original columns + error metadata)

**Output**: CSV file path in `ToolResult.data['error_report_path']`**Security Note**: This CSV contains full PII - must be shared via secure link only, never via email attachment per [BRD FR-013](../../agentic_systems/docs/brd.md#33-secure-partner-sharing-fr-013) and [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules).

### GeneratePartnerEmailTool

**Purpose**: Generate templated email explaining validation errors.**Inputs**:

- `error_report_path`: Path to error report CSV
- `violations`: List of violations for context
- `partner_name`: Partner identifier (from CLI --partner)
- `secure_link_url`: URL for accessing error report (placeholder until approval)
- `access_code`: Access code for secure link (if code-based)

**Email Template Structure**:

```javascript
Subject: Action Required: Data Validation Errors - [Partner Name] Q[Quarter]

Dear [Partner Name],

We have identified [X] validation errors in your quarterly data submission for [Quarter] [Year].

Error Summary:
- Required Field Errors: [count]
- Active Past Graduation Errors: [count]
- Zip Code Format Errors: [count]
- Other Errors: [count]

To review and correct these errors:
1. Access the error report using this secure link: [secure_link_url]
2. Access code: [access_code] (if code-based)
3. Review the error details for each row
4. Correct the data in your source file
5. Upload the corrected file to: [upload_location]

Per-Row Error Details:
[For each row with errors:]
  Row [row_index]: 
    - [Field Name]: [Error Message]
    - [Field Name]: [Error Message]

[Additional instructions...]

Thank you,
CFA Data Processing Team
```

**Output**: Email content (HTML and plain text) in `ToolResult.data['email_content']` and `ToolResult.data['email_html']`**Security Note**: Email contains NO PII - only error metadata (row numbers, field names, error messages) per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules).

### CreateSecureLinkTool (Lightweight Demo)

**Purpose**: Generate secure access link for error report (demo version) per [BRD FR-013](../../agentic_systems/docs/brd.md#33-secure-partner-sharing-fr-013).**Demo Implementation**:

- Generate access code: `secrets.token_urlsafe(16)`
- Write code to `evidence_dir/secure_link_code.txt`
- Create local file URL: `file:///path/to/evidence_dir/outputs/partner_error_report.csv`
- **OR** create HTTP URL: `http://localhost:8000/secure-link/<access_code>`
- Return URL and code in ToolResult

**Production Comments** (explicit markers for future implementation):

```python
# PRODUCTION: Store access code in PostgreSQL secure_links table
# PRODUCTION: Generate SharePoint secure link with Azure AD authentication
# PRODUCTION: Send access code via secure email service (not in email body)
# PRODUCTION: Implement link expiration (7 days default)
# PRODUCTION: Track access counts and last accessed timestamp
```

**Output**: Secure link URL and access code in `ToolResult.data['secure_link_url']` and `ToolResult.data['access_code']`

### RequestStaffApprovalTool

**Purpose**: Request CFA staff approval before sending email to partner per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012).**Inputs**:

- `email_content`: Generated email content (text and HTML)
- `error_report_path`: Path to error report CSV
- `error_summary`: Summary of error counts by type
- `partner_name`: Partner identifier

**POC Implementation** (Interactive CLI):

1. Display email preview to console
2. Display error summary (counts by type)
3. Prompt staff: "Approve sending this email to partner? (y/n): "
4. If approved: Return approval status and proceed
5. If rejected: Prompt for rejection reason, return rejection status

**Display Format**:

```javascript
=== STAFF APPROVAL REQUIRED ===

Partner: [Partner Name]
Quarter: [Quarter] [Year]

Error Summary:
- Required Field Errors: [count]
- Active Past Graduation Errors: [count]
- Zip Code Format Errors: [count]
- Total Rows with Errors: [count]

Email Preview:
[Email content displayed here]

Approve sending this email to partner? (y/n): 
```

**Production Comments** (explicit markers for future implementation):

```python
# PRODUCTION: Send Teams Adaptive Card approval request
# PRODUCTION: Include validation summary and link to view full report
# PRODUCTION: Wait for approval response via Teams webhook
# PRODUCTION: Record approval decision in PostgreSQL approval_requests table
# PRODUCTION: Support approval/rejection with comments
```

**Output**: Approval status, staff comments (if any), and timestamp in `ToolResult.data['approval_status']`, `ToolResult.data['staff_comments']`, and `ToolResult.data['approval_timestamp']`

### Agent Resume Logic

Per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012) (validation retry and resume):**Resume State Structure** (saved to `evidence_dir/resume_state.json`):

```json
{
  "run_id": "demo-Q1-minimal",
  "original_file_path": "path/to/original/file.csv",
  "validation_violations": [...],
  "secure_link_code": "abc123...",
  "secure_link_url": "file:///path/to/error_report.csv",
  "halted_at": "ValidateStagedDataTool",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Resume Flow**:

1. Load resume state from evidence bundle
2. Accept corrected file path (from CLI `--resume` or file watch)
3. Re-run ingestion on corrected file
4. Re-run validation
5. Compare violations:

                                                                                                                                                                                                - If no errors: Continue to canonicalization
                                                                                                                                                                                                - If errors remain: Regenerate error report and email

6. Update evidence bundle with resume metadata

### File Watch Mechanism (Optional)

Per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012) (validation retry and resume):**Implementation**:

- Poll directory for files matching pattern: `*_corrected.csv` or `*_fixed.csv`
- Compare file hash with original to detect changes per [PRD-TRD Section 5.4](../../agentic_systems/docs/prd-trd.md#54-tool-specifications)
- When corrected file detected:
                                                                                                                                - Extract run_id from filename or directory structure
                                                                                                                                - Call `agent.resume(corrected_file_path)` per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012)
                                                                                                                                - Log resume event to evidence bundle per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011)

**CLI Command**:

```bash
# Watch for corrected files in a directory
python -m agentic_systems.cli.main watch --directory agentic_systems/data/corrected/ --pattern "*_corrected.csv"

# Manual resume with corrected file
python -m agentic_systems.cli.main run intake --resume demo-Q1-minimal --file agentic_systems/data/corrected/Example_Quarterly_Data_Report_corrected.csv
```



## Part 3 Evidence Bundle Updates

Per [BRD FR-011](../../agentic_systems/docs/brd.md#312-evidence-bundle-generation-fr-011) and [PRD-TRD Section 3.2](../../agentic_systems/docs/prd-trd.md#32-evidence-bundle-structure):**New Files in Evidence Bundle**:

- `resume_state.json`: State saved when execution halts
- `outputs/partner_error_report.csv`: Full row data with errors (PII)
- `outputs/partner_email.txt`: Templated email content (before approval)
- `outputs/partner_email_approved.txt`: Approved email content (after staff approval)
- `outputs/partner_email.html`: HTML version of email
- `outputs/staff_approval_record.json`: Staff approval decision, comments, and timestamp
- `secure_link_code.txt`: Access code (for demo, only if approved)

**Updated manifest.json**:

```json
{
  "run_id": "demo-Q1-minimal",
  "agent": "SimpleIntakeAgent",
  "platform": "minimal",
  "data_classification": "Internal",
  "pii_handling": "redacted",
  "model": null,
  "egress_approval_ref": null,
  "hitl_status": "halted",
  "staff_approval_status": "approved",
  "staff_approval_timestamp": "2025-01-15T10:35:00Z",
  "secure_link_code": "abc123...",
  "resume_available": true
}
```



## Part 3 Testing Strategy

### Unit Tests

Per [PRD-TRD Section 10.1](../../agentic_systems/docs/prd-trd.md#101-unit-tests):

- `test_generate_error_report_tool.py`: Test error report CSV generation
- `test_generate_email_tool.py`: Test email template generation
- `test_secure_link_tool.py`: Test access code generation
- `test_request_approval_tool.py`: Test staff approval workflow (mock user input) per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012)

### Integration Tests

- End-to-end HITL workflow: validation → error report → email → staff approval → secure link → send email → resume
- Staff approval rejection: verify workflow halts when approval rejected
- Resume with corrected file: verify re-validation and continuation
- File watch detection: verify corrected file triggers resume

### Manual Verification

1. Run intake with file containing errors
2. Verify error report CSV contains full row data
3. Verify email template includes per-row error details
4. Verify staff approval prompt is displayed
5. Approve email sending
6. Verify secure link code is generated (only after approval)
7. Verify email is sent (or marked as ready to send)
8. Test rejection flow: reject approval and verify workflow halts
9. Correct errors in source file
10. Resume with corrected file
11. Verify validation passes and canonicalization completes

## Part 3 Security Considerations

**PII Handling** (per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules)):

- Error report CSV contains full PII - must be shared via secure link only per [BRD FR-013](../../agentic_systems/docs/brd.md#33-secure-partner-sharing-fr-013)
- Email template contains NO PII - only error metadata per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules)
- Secure link code stored in evidence bundle (demo) - production would use PostgreSQL per [BRD FR-013](../../agentic_systems/docs/brd.md#33-secure-partner-sharing-fr-013)
- Access logging (production) - track who accessed error report per [BRD FR-013](../../agentic_systems/docs/brd.md#33-secure-partner-sharing-fr-013)

**Demo vs Production**:

- Demo uses local file URLs and plain text code storage
- Production comments mark where SharePoint, PostgreSQL, and email service integration would occur
- Secure link expiration and access tracking marked for production implementation

## Part 3 Dependencies

**New Dependencies**:

- `jinja2` (optional): For email template rendering (or use Python string formatting)

**No New External Services**:

- Demo uses local file system for secure links
- Production would require SharePoint, PostgreSQL, email service (marked with comments)

## Part 3 Success Criteria

Part 3 is successful when:

- ✅ Validation errors trigger error report generation
- ✅ Error report CSV contains full row data for error rows
- ✅ Email template includes per-row error explanations
- ✅ Staff approval is required before sending email per [BRD FR-012](../../agentic_systems/docs/brd.md#313-human-in-the-loop-safeguards-fr-012)
- ✅ Staff can review email content and approve/reject
- ✅ Secure link code is generated only after staff approval (demo version)
- ✅ Email is sent (or marked ready) only after staff approval
- ✅ Execution halts when errors are found or approval is rejected
- ✅ Resume functionality works with corrected files
- ✅ File watch detects corrected files (optional)
- ✅ Evidence bundle includes HITL artifacts and approval records
- ✅ Both minimal and langchain platforms support HITL workflow

## Part 3 Timeline

- **Setup**: 5 minutes (create new package structure)
- **Implementation**: 60-90 minutes (tools + agent updates + CLI resume)
- **Testing**: 20 minutes (end-to-end HITL workflow)
- **Total**: ~85-115 minutes for Part 3

## Part 3 Teaching Points

### For Instructors

- **HITL Workflow**: Demonstrate complete error correction cycle with staff oversight
- **Security First**: Show how PII is protected through secure links (no email attachments)
- **Resume Capability**: Demonstrate how the system can pause and resume based on partner corrections
- **Staff Oversight**: Emphasize the importance of staff approval before partner communication

### For Interns

- **Complete Workflow**: See how validation errors trigger a full communication cycle
- **Security Patterns**: Learn secure link generation and PII protection patterns
- **Resume Logic**: Understand how state is preserved and workflows can be resumed
- **Production Readiness**: See explicit comments marking where production integrations would occur

---

## Combined Execution Order

**Recommended flow for complete demonstration:**

1. **Part 1 Implementation** (~30-45 minutes)

- Implement deterministic baseline (SimpleIntakeAgent)
- Test with `--platform minimal`
- Verify evidence bundle generation

2. **Part 2 Implementation** (~45-55 minutes additional)

- Implement LangChain adapter and LLM agent
- Test with `--platform langchain` (requires API key)
- Compare evidence bundles side-by-side

3. **Part 3 Implementation** (~85-115 minutes additional)

- Implement partner communication tools (error report, email, secure link, staff approval)
- Update agents to support HITL workflow and resume functionality
- Test end-to-end error correction cycle
- Test staff approval and rejection flows

**Total Time**: ~160-215 minutes for complete three-part demonstration

## Implementation Clarifications Summary

This plan addresses all critical implementation decisions to ensure executable step-by-step deployment:

### Data Flow Design

- **ToolResult.data**: Can contain in-memory objects (DataFrames, lists) for tool chaining per [PRD-TRD Section 5.4](../../agentic_systems/docs/prd-trd.md#54-tool-specifications)
- **tool_calls.jsonl**: Logs sanitized metadata only (counts, hashes, status) - no DataFrames or raw data per [PRD-TRD Section 3.2](../../agentic_systems/docs/prd-trd.md#32-evidence-bundle-structure)
- **Outputs ownership**: Tools return in-memory data only; evidence writer (`write_evidence.py`) serializes to `outputs/` directory once
- **Separation**: In-memory objects for tool chaining, sanitized metadata for evidence logs, evidence writer handles file serialization

### Evidence Bundle Generation

- **BaseAgent.execute()** wraps tool calls and appends JSONL events directly to `tool_calls.jsonl` as tools run (BaseAgent owns tool_calls.jsonl writing) per [PRD-TRD Section 7.4](../../agentic_systems/docs/prd-trd.md#74-evidence-bundle-generation-flow)
- **write_evidence.py** writes manifest.json, plan.md, summary.md from agent state and serializes outputs/ (does NOT write tool_calls.jsonl)
- **Data classification comment**: Lives in code (`write_evidence.py`), not in JSON manifest per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules)

### CLI Invocation

Per [PRD-TRD Section 11.2](../../agentic_systems/docs/prd-trd.md#112-configuration-management):

- **Working Directory**: Repository root
- **Command**: `python -m agentic_systems.cli.main run intake --file agentic_systems/data/masked/... --partner demo --quarter Q1 --platform minimal`
- **Requires**: `agentic_systems/__init__.py` (created by setup script)

### Agent Routing

- **Direct instantiation**: CLI directly instantiates platform-specific agents (no dispatcher) per [PRD-TRD Section 6.4](../../agentic_systems/docs/prd-trd.md#64-platform-adapter-specifications)
- **`intake_agent.py` decision**: Remove `agentic_systems/agents/intake_agent.py` - it is not needed since CLI routes directly to platform implementations (`SimpleIntakeAgent` or `LangChainIntakeAgent`). If file exists, delete it to avoid confusion. Existing imports of `intake_agent.py` should be updated to import platform-specific agents directly.

### Validation Reporting

- **Row-level entries**: `{row_index, field, severity, message}` only - no raw field values per [BRD Section 2.3](../../agentic_systems/docs/brd.md#23-business-rules) PII handling
- Maintains "redacted" classification