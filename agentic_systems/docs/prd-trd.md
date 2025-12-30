# Product/Technical Requirements Document (PRD/TRD)
## CFA Applied Agentic AI — Quarterly Workforce Reporting System

**Version:** 1.0  
**Date:** 2025  
**Status:** Draft  
**Owner:** Development Team

---

## 1. System Overview

### 1.1 Purpose
This document defines the technical and product requirements for the CFA Applied Agentic AI system, including architecture, APIs, data models, integrations, and implementation specifications.

### 1.2 System Architecture

**High-Level Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Coordinator                          │
│              (agentic_systems/cli/main.py)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐    ┌────▼────┐   ┌────▼────┐
   │ Intake  │    │Reconcile│   │ Export  │
   │ Agent   │    │ Agent   │   │ Agent   │
   └────┬────┘    └────┬────┘   └────┬────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐    ┌────▼────┐   ┌────▼────┐
   │Ingestion│    │Canonical│   │Validation│
   │  Tools  │    │  Tools  │   │  Tools   │
   └────┬────┘    └─────────┘   └────┬─────┘
        │                             │
        │                             │
   ┌────▼────────────────────────────▼─────┐
   │   SharePoint/Dataverse Integration    │
   │   - Partner file storage               │
   │   - Validation report sharing          │
   │   - Secure link generation            │
   └─────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│         Data Analysis Platform (Week 10+)                  │
│  ┌──────────────┐              ┌──────────────┐            │
│  │ Copilot      │              │ Browser App  │            │
│  │ (Teams/etc)  │              │  (Web UI)    │            │
│  └──────┬───────┘              └──────┬───────┘            │
└─────────┼──────────────────────────────┼────────────────────┘
          │                              │
          └──────────────┬───────────────┘
                         │
          ┌──────────────▼───────────────┐
          │   Unified API Layer         │
          │   (FastAPI REST API)        │
          │   - /api/analyze            │
          │   - /api/datasets           │
          └──────────────┬───────────────┘
                         │
          ┌──────────────▼───────────────┐
          │   Data Analysis Agent       │
          │   (BaseAgent)               │
          └──────────────┬───────────────┘
                         │
          ┌──────────────▼───────────────┐
          │   Query Engine              │
          │   - NL → SQL conversion     │
          │   - Query validation        │
          └──────────────┬───────────────┘
                         │
          ┌──────────────▼───────────────┐
          │   Canonical Data Model      │
          │   (CDM Database)            │
          └─────────────────────────────┘
```

### 1.3 Technology Stack

**Backend:**
- Python 3.10+
- FastAPI (API server)
- SQLAlchemy (database ORM)
- Pandas (data processing)
- LangChain (optional - implementation detail)

**Database:**
- PostgreSQL (development and production)
- CDM schema with participants, enrollments, employment_records, etc.

**Frontend:**
- Browser App: React/Vue or vanilla JavaScript
- Chart.js/D3.js (visualizations)

**Integrations:**
- Microsoft Copilot Studio (plugin)
- Microsoft Teams Bot Framework (optional)
- Azure Bot Service
- Azure AD (authentication)
- SharePoint Online (partner file storage, validation report sharing)
- Dataverse (alternative storage for validation reports)
- External Wage API (prevailing wage validation)

**Infrastructure:**
- Azure App Service or similar (API hosting)
- Azure Key Vault (secrets management)

---

## 2. Technical Architecture

### 2.1 Core Principles

1. **Platform-Agnostic Core**: All deterministic business logic in `core/`
2. **Agent Orchestration**: Agents plan, coordinate, explain; tools execute
3. **Evidence Bundles**: Every run produces complete audit trail
4. **Data Classification**: All runs declare Public/Internal/Confidential/Restricted
5. **Contract-First**: All agents implement BaseAgent contract
6. **Framework as Implementation Detail**: LangChain used inside agents, not replacing contract

### 2.2 Component Architecture

**Core Layer** (`agentic_systems/core/`):
- `canonical/` - CDM schema and canonicalization logic
- `ingestion/` - Partner file ingestion (local and SharePoint)
- `validation/` - Business rule enforcement (enhanced rules: active past graduation, name misspellings, prevailing wage)
- `reconciliation/` - WSAC reconciliation logic
- `exports/` - WSAC & Dynamics export generation
- `analysis/` - Query engine and NL→SQL conversion
- `audit/` - Evidence bundle generation and validation
- `integrations/sharepoint/` - SharePoint client and secure link generation

**Agent Layer** (`agentic_systems/agents/`):
- `base_agent.py` - BaseAgent contract implementation
- `intake_agent.py` - Intake orchestration
- `reconciliation_agent.py` - Reconciliation orchestration
- `export_agent.py` - Export orchestration
- `data_analysis_agent.py` - Data analysis orchestration
- `platforms/` - Vendor platform adapters (Microsoft, OpenAI, Anthropic, LangChain, Minimal)

**API Layer** (`agentic_systems/api/`):
- `server.py` - FastAPI server
- `analysis_api.py` - Data analysis endpoints
- `copilot_plugin.py` - Copilot Studio configuration
- `auth.py` - Authentication middleware

**Web Layer** (`agentic_systems/web/`):
- `index.html` - Browser app
- `app.js` - Frontend logic
- `styles.css` - Styling

**CLI Layer** (`agentic_systems/cli/`):
- `main.py` - CLI entrypoint
- `orchestrator.py` - Full quarter orchestration

---

## 3. Data Models

### 3.1 Canonical Data Model (CDM)

**participants**
- `participant_id` (PK)
- `first_name`, `last_name`, `middle_name`
- `date_of_birth`
- `wsac_id` (nullable)
- `race`, `gender`, `ethnicity`
- `address_line1`, `address_line2`, `city`, `state`, `zip`
- `email`, `phone`
- `highest_education`
- `priority_populations`
- `disability`, `disability_type`
- `veteran_status`
- `created_at`, `updated_at`

**program_enrollments**
- `enrollment_id` (PK)
- `participant_id` (FK)
- `pathway` (e.g., "Data Analytics", "IT Support")
- `program_name`
- `start_date`, `end_date`, `expected_end_date`
- `status` (e.g., "Currently active", "Graduated/completed", "Withdrawn/terminated")
- `completion_type` (nullable)
- `noncompletion_reason` (nullable)
- `quarter`, `year`
- `created_at`, `updated_at`

**employment_records**
- `employment_id` (PK)
- `participant_id` (FK)
- `job_start_date`
- `job_occupation` (NAICS code)
- `employer`
- `employment_type` (e.g., "Full-time", "Part-time", "Earn and Learn")
- `earn_and_learn_type` (nullable)
- `employment_status` (e.g., "Employed In-field", "Still seeking")
- `hourly_wage`
- `created_at`, `updated_at`

**validation_results**
- `validation_id` (PK)
- `run_id`
- `row_identifier`
- `field_name`
- `rule_violated`
- `severity` (Error/Warning/Info)
- `current_value`
- `expected_value`
- `created_at`

**reconciliation_matches**
- `match_id` (PK)
- `run_id`
- `participant_id` (FK)
- `wsac_participant_id`
- `classification` (NEW/EXISTING/CHANGED/MISSING/UNMATCHED)
- `match_confidence`
- `differences` (JSON)
- `created_at`

**status_transitions**
- `transition_id` (PK)
- `participant_id` (FK)
- `old_status`
- `new_status`
- `source` (e.g., "WSAC", "Canonicalization")
- `transition_date`
- `run_id`

**change_log**
- `change_id` (PK)
- `run_id`
- `entity_type` (participant/enrollment/employment)
- `entity_id`
- `field_name`
- `old_value`
- `new_value`
- `change_type` (created/updated)
- `created_at`

**secure_links**
- `link_id` (PK)
- `access_code` (unique, indexed)
- `file_url` (SharePoint file URL)
- `partner_email`
- `expires_at`
- `access_count` (default: 0)
- `created_at`
- `last_accessed_at` (nullable)

**approval_requests**
- `approval_id` (PK)
- `run_id` (FK, indexed)
- `request_id` (unique, Teams message ID)
- `status` (pending/approved/rejected)
- `requested_at`
- `responded_at` (nullable)
- `approver_email` (nullable)
- `rejection_reason` (nullable)
- `validation_summary` (JSON)
- `report_url` (internal SharePoint URL)

### 3.2 Evidence Bundle Structure

**Directory:** `core/audit/runs/<run-id>/`

**Required Files:**
- `manifest.json` - Run metadata, data classification, PII handling
- `plan.md` - Human-readable execution plan
- `tool_calls.jsonl` - Ordered tool call log (JSONL format)
- `summary.json` - Structured summary
- `audit_record.json` - Compliance record
- `evidence_bundle.json` - Bundle manifest
- `outputs/` - Generated artifacts (CSVs, worksheets)

**Manifest Schema:**
```json
{
  "run_id": "cfa-q4-2025-minimal",
  "agent": "IntakeAgent",
  "client_id": "CFA",
  "goal": "Process Partner X for Q4 2025",
  "timestamp_utc": "2025-01-15T10:30:00Z",
  "platform": "minimal",
  "execution_mode": "CLI",
  "data_classification": "CONFIDENTIAL",
  "pii_handling": "minimized",
  "egress_approval_ref": null,
  "artifacts": {
    "trace_path": "trace.jsonl",
    "artifact_keys": ["summary.json", "audit_record.json"]
  }
}
```

---

## 4. API Specifications

### 4.1 Analysis API Endpoints

**Base URL:** `https://api.cfa.example.com`

#### POST /api/analyze
**Purpose:** Execute natural language data analysis query

**Request:**
```json
{
  "query": "Show me participants enrolled in Data Analytics pathway in Q4 2025",
  "filters": {
    "quarter": "Q4",
    "year": 2025
  },
  "format": "table"
}
```

**Response:**
```json
{
  "results": {
    "data": [
      {"participant_id": "123", "name": "John Doe", "status": "Active", ...}
    ],
    "row_count": 45
  },
  "summary": "Found 45 participants enrolled in Data Analytics pathway in Q4 2025",
  "visualization": null
}
```

**Error Response:**
```json
{
  "error": "Invalid query",
  "message": "Table 'invalid_table' does not exist",
  "suggestions": ["Did you mean 'program_enrollments'?"]
}
```

#### GET /api/datasets
**Purpose:** List available datasets

**Response:**
```json
{
  "datasets": [
    {
      "name": "participants",
      "description": "Participant records",
      "row_count": 1250
    },
    {
      "name": "enrollments",
      "description": "Program enrollments",
      "row_count": 3420
    }
  ]
}
```

#### GET /api/schema
**Purpose:** Get CDM schema information

**Response:**
```json
{
  "tables": {
    "participants": {
      "columns": ["participant_id", "first_name", "last_name", ...],
      "primary_key": "participant_id"
    },
    "program_enrollments": {
      "columns": ["enrollment_id", "participant_id", "pathway", ...],
      "foreign_keys": {"participant_id": "participants"}
    }
  }
}
```

#### POST /api/messages (Week 2 MVP)
**Purpose:** Simple message endpoint for Copilot MVP

**Request:**
```json
{
  "text": "Hello"
}
```

**Response:**
```json
{
  "text": "Echo: Hello. Data analysis capabilities coming in Week 10!"
}
```

#### POST /api/webhooks/sharepoint-file-updated
**Purpose:** Receive SharePoint webhook notifications when partner files are updated

**Request:**
```json
{
  "resource": "file_url",
  "changeType": "updated",
  "clientState": "run_id"
}
```

**Response:**
```json
{
  "status": "accepted",
  "run_id": "cfa-q4-2025-minimal",
  "action": "validation_retry_triggered"
}
```

**Behavior:**
- Validates webhook signature/authentication
- Triggers validation retry for affected run
- Loads checkpoint and re-runs validation
- If validation passes: Automatically resumes from canonicalization step
- If validation fails: Generates new report and requests approval again

#### POST /api/webhooks/teams-approval
**Purpose:** Receive Teams Adaptive Card action responses for approval requests

**Request:**
```json
{
  "type": "message",
  "action": {
    "type": "Action.Submit",
    "id": "approve",
    "data": {
      "approval_request_id": "req_123",
      "action": "approve"
    }
  }
}
```

**Response:**
```json
{
  "status": "approved",
  "approval_request_id": "req_123",
  "secure_link_generated": true
}
```

**Behavior:**
- Validates Teams webhook signature
- Updates approval status in PostgreSQL `approval_requests` table
- If approved: Triggers secure link generation and partner notification
- If rejected: Halts workflow and logs rejection reason

### 4.2 Authentication

**Week 2 MVP:** No authentication (development only)

**Week 11 Enhancement:**
- Azure AD authentication for `/api/analyze` endpoints
- Bearer token in Authorization header
- Role-based access control (if needed)

---

## 5. Agent Specifications

### 5.1 BaseAgent Contract

**Required Methods:**
- `run(goal: str, client_id: str, params: Dict[str, Any], output_dir: Optional[str]) -> AgentState`
- `plan(state: AgentState) -> List[Dict[str, Any]]` (must override)
- `summarize(state: AgentState) -> Dict[str, Any]`
- `audit_record(state: AgentState) -> Dict[str, Any]`
- `evidence_bundle(state: AgentState) -> Dict[str, Any]`

**State Management:**
- `AgentState` dataclass with: goal, params, run_id, plan, step_results, artifacts, severity_counts
- State is externalized and serializable

**Tool Protocol:**
- Tools implement: `name: str` and `__call__(**kwargs) -> ToolResult`
- `ToolResult` contains: ok, summary, data, warnings, blockers

### 5.2 Intake Agent

**Tools:**
- `IngestPartnerFileTool`
- `ValidateStagedDataTool`
- `CanonicalizeStagedDataTool`

**Plan Format:**
```python
[
  {"step": "ingest", "tool": "IngestPartnerFileTool", "args": {"file_path": "..."}},
  {"step": "validate", "tool": "ValidateStagedDataTool", "args": {"run_id": "..."}},
  {"step": "canonicalize", "tool": "CanonicalizeStagedDataTool", "args": {"run_id": "..."}}
]
```

### 5.3 Data Analysis Agent

**Tools:**
- `QueryCanonicalDataTool`
- `AnalyzeTrendsTool`
- `ComparePeriodsTool`
- `GenerateSummaryTool`

**Query Processing:**
1. Receive natural language query
2. Convert to SQL using LLM with CDM schema context
3. Validate SQL (no DROP/DELETE, valid tables/columns)
4. Execute query against CDM
5. Format results for frontend
6. Generate human-readable summary

### 5.4 Tool Specifications

**Tool Protocol:**
All tools must implement the `Tool` protocol:
```python
from typing import Protocol
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class ToolResult:
    ok: bool
    summary: str
    data: Dict[str, Any]
    warnings: List[str]
    blockers: List[str]

class Tool(Protocol):
    name: str
    
    def __call__(self, **kwargs) -> ToolResult:
        ...
```

**Ingestion Tools:**

**IngestPartnerFileTool**
- **Purpose**: Load and parse partner data files from local filesystem or SharePoint
- **Parameters**:
  - `file_path: str` - Path to CSV/Excel file (local or SharePoint relative path)
  - `file_format: str` - Format type ("quarterly_report", "dynamics_import", "wsac_bulk_upload")
  - `source: str` - Source type ("local" or "sharepoint", default: "local")
  - `run_id: str` - Run identifier for tracking
- **Returns**: `ToolResult` with:
  - `ok: bool` - Success/failure
  - `summary: str` - "Ingested X rows from file Y (SharePoint)" or "Ingested X rows from file Y"
  - `data: Dict` - `{"rows_ingested": int, "staging_table": str, "file_hash": str, "source": str}`
  - `warnings: List[str]` - Encoding issues, missing columns
  - `blockers: List[str]` - File not found, invalid format, SharePoint access denied
- **Behavior**:
  - **Local files**: Reads from local filesystem
  - **SharePoint files**: Uses `SharePointClient` to read from SharePoint (requires Azure AD authentication)
  - Detects file encoding (UTF-8, Windows-1252, etc.)
  - Parses format-specific structure
  - Normalizes column names
  - Writes to PostgreSQL staging tables with run metadata
  - Records file hash for idempotency

**ValidateStagedDataTool**
- **Purpose**: Execute business rules against staged data with enhanced validation rules, including HITL approval workflow
- **Parameters**:
  - `run_id: str` - Run identifier
  - `partner_name: str` - Partner name for report generation
  - `quarter: str` - Quarter identifier
  - `validation_rules: List[str]` - Rule names to execute (optional, defaults to all provided rules)
  - `wsac_data: List[Dict]` - WSAC prior-quarter data for name comparison (optional)
  - `approval_recipients: List[str]` - Teams channel/user group for approval requests
- **Returns**: `ToolResult` with:
  - `ok: bool` - True if no blocking errors and approval granted
  - `summary: str` - "X errors, Y warnings, Z info messages. Report approved and shared via secure link." or "Report rejected by staff."
  - `data: Dict` - `{"validation_results": List[Dict], "report_url": str, "severity_counts": Dict, "blocks_wsac_entry": bool, "approval_request_id": str, "approval_status": str}`
  - `warnings: List[str]` - Warning-level violations
  - `blockers: List[str]` - Error-level violations or rejection reason
- **Behavior**:
  - Executes validation rules from CFA-provided `clients/cfa/rules.py` (rules integrated into validation engine framework) including:
    - **Active past graduation**: Checks if participant marked as "Currently active" but `end_date` has passed (Error)
    - **Name misspelling detection**: Compares canonical participant names with WSAC data using fuzzy matching (Warning, <85% similarity threshold)
    - **Prevailing wage validation**: Validates job placements meet prevailing wage requirements via external API (Error, `blocks_wsac_entry=True`)
  - Queries PostgreSQL staging tables
  - Generates enhanced review worksheet (Excel with color-coding, action required column)
  - **Two-stage upload process:**
    1. Uploads validation report to SharePoint/Dataverse (internal location for staff review)
    2. After approval, uploads to partner-accessible location
  - **HITL Approval Workflow:**
    - Sends Teams Adaptive Card approval request to specified recipients
    - Includes validation summary (error/warning counts, severity breakdown)
    - Includes link to view full report (internal SharePoint link)
    - Waits for approval response via Teams webhook
    - If approved: Generates secure link (code-based or Azure AD auth) and uploads report to partner location
    - If rejected: Halts workflow and returns rejection reason
  - Counts violations by severity
  - Applies stop conditions (halts if errors present)
  - Returns secure link URL for partner notification (only if approved)
  - **Checkpoint Management**: Saves checkpoint after validation for resume capability

**CanonicalizeStagedDataTool**
- **Purpose**: Transform validated staging data to canonical records
- **Parameters**:
  - `run_id: str` - Run identifier
  - `participant_matching_strategy: str` - Matching strategy (default: "name_dob_wsac")
- **Returns**: `ToolResult` with:
  - `ok: bool` - Success/failure
  - `summary: str` - "Created X participants, updated Y, processed Z enrollments"
  - `data: Dict` - `{"participants_created": int, "participants_updated": int, "enrollments_processed": int, "changes_logged": int}`
  - `warnings: List[str]` - Ambiguous matches, data conflicts
  - `blockers: List[str]` - Database errors, constraint violations
- **Behavior**:
  - Resolves participant identity (deduplication) via PostgreSQL queries
  - Maps staging fields to CDM schema
  - Performs idempotent upserts to PostgreSQL CDM tables
  - Records all changes in PostgreSQL change_log table

**Reconciliation Tools:**

**LoadWSACDataTool**
- **Purpose**: Load WSAC prior-quarter export
- **Parameters**:
  - `wsac_file_path: str` - Path to WSAC CSV export
  - `quarter: str` - Quarter identifier (e.g., "Q3")
  - `year: int` - Year
- **Returns**: `ToolResult` with WSAC participant data loaded into PostgreSQL staging tables

**ReconcileParticipantsTool**
- **Purpose**: Match and classify participants against WSAC data
- **Parameters**:
  - `canonical_participants: List[Dict]` - Canonical participant records (from PostgreSQL CDM)
  - `wsac_participants: List[Dict]` - WSAC participant records (from PostgreSQL staging)
  - `matching_strategy: str` - Matching algorithm (default: "wsac_id_primary")
- **Returns**: `ToolResult` with reconciliation matches and classifications stored in PostgreSQL reconciliation_matches table

**Export Tools:**

**GenerateWSACExportTool**
- **Purpose**: Generate WSAC bulk upload CSV
- **Parameters**:
  - `quarter: str` - Quarter identifier
  - `year: int` - Year
  - `output_path: str` - Output file path
- **Returns**: `ToolResult` with export file path and validation results
- **Behavior**:
  - Queries PostgreSQL CDM for participant/enrollment data
  - Maps to WSAC format per `clients/cfa/mappings.py`
  - Generates CSV file
  - Validates against WSAC schema
  - **Blocks export if `blocks_wsac_entry=True` from Week 2 validation** (prevailing wage violations)

**GenerateDynamicsExportTool**
- **Purpose**: Generate Dynamics import CSV
- **Parameters**:
  - `output_path: str` - Output file path
  - `include_relationships: bool` - Include related records
- **Returns**: `ToolResult` with export file path and integrity validation
- **Behavior**:
  - Queries PostgreSQL CDM for participant/enrollment/employment data
  - Maps to Dynamics format per `clients/cfa/mappings.py`
  - Validates referential integrity
  - Generates CSV/Excel file

**SharePoint Integration Tools:**

**SharePointClient**
- **Purpose**: Read partner files from SharePoint and upload validation reports
- **Methods**:
  - `read_file(file_path: str) -> bytes` - Read partner file from SharePoint
  - `upload_file(file_content: bytes, folder_path: str, filename: str) -> str` - Upload validation report to SharePoint
  - `create_secure_link(file_url: str, expiration_days: int) -> SecureLink` - Create authenticated sharing link
- **Authentication**: Azure AD app registration (client ID/secret)
- **Library**: `office365-rest-python-client`

**SecureLinkGenerator**
- **Purpose**: Generate secure links for partner access to validation reports
- **Methods**:
  - `generate_code_link(file_url: str, partner_email: str) -> SecureLink` - Generate code-based access link
  - `generate_auth_link(file_url: str) -> SecureLink` - Generate Azure AD authenticated link
- **Behavior**:
  - Generates cryptographically secure access codes (`secrets.token_urlsafe(16)`)
  - Stores codes in PostgreSQL `secure_links` table with expiration (7 days default)
  - Sends access code to partner email via secure email service
  - Returns secure link URL for partner notification
  - Tracks access counts and last accessed timestamp

**Validation Rule Tools:**

**ValidateActivePastGraduation**
- **Purpose**: Check if participant marked as active past graduation date
- **Parameters**:
  - `enrollment: Dict` - Enrollment record with status and end_date
- **Returns**: `ValidationResult` with Error severity if violation found
- **Behavior**: Compares enrollment status ("Currently active") with end_date, flags if end_date < today()

**ValidateNameSpelling**
- **Purpose**: Detect name misspellings by comparing canonical and WSAC participant names
- **Parameters**:
  - `canonical_participant: Dict` - Canonical participant record
  - `wsac_participant: Dict` - WSAC participant record
- **Returns**: `ValidationResult` with Warning severity if similarity < 85%
- **Behavior**: Uses fuzzy matching (Levenshtein distance) to compare full names, threshold: 85% similarity

**ValidatePrevailingWage**
- **Purpose**: Validate job placements meet prevailing wage requirements
- **Parameters**:
  - `employment_record: Dict` - Employment record with job_occupation, region, hourly_wage
  - `wage_api_client: WageAPIClient` - External wage API client
- **Returns**: `ValidationResult` with Error severity and `blocks_wsac_entry=True` if wage below prevailing wage
- **Behavior**: 
  - Fetches prevailing wage from external API (occupation code + region)
  - Compares hourly_wage with prevailing_wage
  - Flags error if hourly_wage < prevailing_wage
  - Sets `blocks_wsac_entry=True` to prevent WSAC export

**SharePoint Integration Tools:**

**SharePointClient**
- **Purpose**: Read partner files from SharePoint and upload validation reports
- **Methods**:
  - `read_file(file_path: str) -> bytes` - Read partner file from SharePoint
  - `upload_file(file_content: bytes, folder_path: str, filename: str) -> str` - Upload validation report to SharePoint
  - `create_secure_link(file_url: str, expiration_days: int) -> SecureLink` - Create authenticated sharing link
- **Authentication**: Azure AD app registration (client ID/secret)
- **Library**: `office365-rest-python-client`

**SecureLinkGenerator**
- **Purpose**: Generate secure links for partner access to validation reports
- **Methods**:
  - `generate_code_link(file_url: str, partner_email: str) -> SecureLink` - Generate code-based access link
  - `generate_auth_link(file_url: str) -> SecureLink` - Generate Azure AD authenticated link
- **Behavior**:
  - Generates cryptographically secure access codes (`secrets.token_urlsafe(16)`)
  - Stores codes in PostgreSQL `secure_links` table with expiration (7 days default)
  - Sends access code to partner email via secure email service
  - Returns secure link URL for partner notification
  - Tracks access counts and last accessed timestamp

**Validation Rule Tools:**

**ValidateActivePastGraduation**
- **Purpose**: Check if participant marked as active past graduation date
- **Parameters**:
  - `enrollment: Dict` - Enrollment record with status and end_date
- **Returns**: `ValidationResult` with Error severity if violation found
- **Behavior**: Compares enrollment status ("Currently active") with end_date, flags if end_date < today()

**ValidateNameSpelling**
- **Purpose**: Detect name misspellings by comparing canonical and WSAC participant names
- **Parameters**:
  - `canonical_participant: Dict` - Canonical participant record
  - `wsac_participant: Dict` - WSAC participant record
- **Returns**: `ValidationResult` with Warning severity if similarity < 85%
- **Behavior**: Uses fuzzy matching (Levenshtein distance) to compare full names, threshold: 85% similarity

**ValidatePrevailingWage**
- **Purpose**: Validate job placements meet prevailing wage requirements
- **Parameters**:
  - `employment_record: Dict` - Employment record with job_occupation, region, hourly_wage
  - `wage_api_client: WageAPIClient` - External wage API client
- **Returns**: `ValidationResult` with Error severity and `blocks_wsac_entry=True` if wage below prevailing wage
- **Behavior**: 
  - Fetches prevailing wage from external API (occupation code + region)
  - Compares hourly_wage with prevailing_wage
  - Flags error if hourly_wage < prevailing_wage
  - Sets `blocks_wsac_entry=True` to prevent WSAC export

**Analysis Tools:**

**QueryCanonicalDataTool**
- **Purpose**: Execute SQL query against PostgreSQL CDM
- **Parameters**:
  - `sql_query: str` - Validated SQL query
  - `query_type: str` - Query type ("select", "aggregate", "trend")
- **Returns**: `ToolResult` with query results and metadata
- **Behavior**:
  - Executes parameterized query against PostgreSQL CDM
  - Returns results as DataFrame
  - Includes row count and execution metadata

**AnalyzeTrendsTool**
- **Purpose**: Analyze trends across time periods
- **Parameters**:
  - `metric: str` - Metric to analyze (e.g., "enrollments", "employment_rate")
  - `time_period: str` - Time period ("quarter", "year")
  - `start_date: str` - Start date (ISO format)
  - `end_date: str` - End date (ISO format)
- **Returns**: `ToolResult` with trend data and visualization data
- **Behavior**:
  - Generates SQL query for trend analysis
  - Executes against PostgreSQL CDM
  - Calculates period-over-period changes
  - Formats for chart visualization

**ComparePeriodsTool**
- **Purpose**: Compare data across quarters/periods
- **Parameters**:
  - `metric: str` - Metric to compare
  - `period1: Dict` - First period (quarter, year)
  - `period2: Dict` - Second period (quarter, year)
- **Returns**: `ToolResult` with comparison results and delta calculations
- **Behavior**:
  - Queries PostgreSQL CDM for both periods
  - Calculates deltas and percentages
  - Formats comparison results

### 5.5 Component Interaction Protocols

**Agent → Tool Invocation:**

Agents invoke tools through the BaseAgent `_execute_step()` method:

```python
def _execute_step(self, state: AgentState, step_name: str, tool_name: str, tool_args: Dict) -> StepResult:
    # 1. Lookup tool from registry
    tool = self.tools.get(tool_name)
    if not tool:
        return StepResult(ok=False, summary=f"Tool {tool_name} not found", ...)
    
    # 2. Emit trace event (STEP_START)
    self._emit(state, "STEP_START", f"Executing {step_name}", {"tool": tool_name, "args": tool_args})
    
    # 3. Invoke tool
    try:
        result = tool(**tool_args)
    except Exception as e:
        # 4. Handle errors
        self._emit(state, "STEP_ERROR", str(e), {"tool": tool_name})
        return StepResult(ok=False, summary=str(e), ...)
    
    # 5. Record result in state
    state.step_results.append({
        "step": step_name,
        "tool": tool_name,
        "result": result
    })
    
    # 6. Emit trace event (STEP_END)
    self._emit(state, "STEP_END", f"Completed {step_name}", {"tool": tool_name, "ok": result.ok})
    
    # 7. Check stop conditions
    if not result.ok or result.blockers:
        self._apply_stop_conditions(state)
    
    return StepResult(ok=result.ok, summary=result.summary, ...)
```

**API → Agent Invocation:**

The API layer invokes agents through the BaseAgent `run()` method:

```python
# In analysis_api.py
async def analyze_query(query: str, filters: Dict) -> Dict:
    # 1. Initialize agent
    agent = DataAnalysisAgent(...)
    
    # 2. Create agent state
    state = AgentState(
        goal=f"Analyze data: {query}",
        params={"query": query, "filters": filters},
        run_id=generate_run_id(),
        ...
    )
    
    # 3. Run agent
    final_state = agent.run(
        goal=state.goal,
        client_id="CFA",
        params=state.params,
        output_dir=f"core/audit/runs/{state.run_id}"
    )
    
    # 4. Extract results
    return {
        "results": final_state.step_results[-1].data,
        "summary": agent.summarize(final_state)["summary"]
    }
```

**Tool → Database Interaction:**

Tools interact with PostgreSQL via SQLAlchemy ORM:

```python
# In canonicalization tool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))  # PostgreSQL connection string
Session = sessionmaker(bind=engine)

def upsert_participant(participant_data: Dict) -> Tuple[bool, bool]:
    session = Session()
    try:
        # Query existing participant from PostgreSQL
        participant = session.query(Participant).filter_by(...).first()
        
        if participant:
            # Update existing
            for key, value in participant_data.items():
                setattr(participant, key, value)
            session.commit()
            return (False, True)  # (created, updated)
        else:
            # Create new
            participant = Participant(**participant_data)
            session.add(participant)
            session.commit()
            return (True, False)  # (created, updated)
    finally:
        session.close()
```

**Error Propagation:**

Errors propagate through the system as follows:

1. **Tool Level**: Tool catches exceptions, returns `ToolResult(ok=False, blockers=[error_message])`
2. **Agent Level**: Agent checks `result.ok`, emits `STEP_ERROR` event, applies stop conditions
3. **API Level**: API catches agent exceptions, returns error response with status code
4. **Frontend**: Frontend displays error message from API response

**State Management:**

- **AgentState**: Externalized dataclass, serialized to JSON after each step
- **Checkpoints**: State saved to `core/audit/runs/<run-id>/checkpoints/<step-name>.json`
- **Resume**: Load checkpoint, restore AgentState, continue from failed step
- **Database State**: PostgreSQL transactions ensure atomicity; rollback on errors

---

## 6. Integration Specifications

### 6.1 Microsoft Copilot Studio Integration

**Plugin Type:** Conversational Plugin (REST API)

**Configuration:**
- Plugin name: "CFA Data Analyzer"
- Endpoint: `https://api.cfa.example.com/api/analyze`
- Authentication: Azure AD (Week 11)
- Response format: Text (Week 10), Adaptive Cards (Week 12)

**Week 2 MVP:**
- Endpoint: `/api/messages`
- Simple echo response
- No authentication

**Week 10 Enhancement:**
- Endpoint: `/api/analyze`
- Connect to Data Analysis Agent
- Return formatted analysis results

### 6.2 Teams Bot Integration (Optional)

**Framework:** Microsoft Bot Framework SDK (Python)

**Configuration:**
- Azure Bot Service registration
- Webhook endpoint: `/api/teams/messages`
- Bot manifest for Teams

**Week 2 MVP:**
- Simple echo handler
- Basic message parsing

**Week 10 Enhancement:**
- Connect to Data Analysis Agent
- Format results as Teams cards

### 6.3 Browser Application

**Technology:** React/Vue or vanilla JavaScript

**Week 10 MVP:**
- Query input field
- Results table display
- Basic error handling
- ~100-200 lines of code

**Week 11 Enhancement:**
- Chart visualization
- Filter UI
- Export functionality
- Query history

**Week 12 Enhancement:**
- Dashboard views
- Saved queries
- Scheduled reports

### 6.4 Platform Adapter Specifications

**BaseAgent Contract Compliance:**

All platform adapters must:
1. Extend `BaseAgent` class
2. Implement required methods (`plan()`, `summarize()`, `audit_record()`, `evidence_bundle()`)
3. Use BaseAgent `Tool` protocol (not platform-specific tools)
4. Generate evidence bundles via BaseAgent methods
5. Emit trace events via BaseAgent `_emit()` method

**Minimal Platform Adapter** (`platforms/minimal/`):

**Implementation:**
- Pure Python implementation, no frameworks
- Direct tool invocation: `tool(**args)`
- Planning via simple step list generation
- State management via BaseAgent `AgentState`

**Example:**
```python
class MinimalIntakeAgent(BaseAgent):
    def plan(self, state: AgentState) -> List[Dict]:
        # Simple deterministic planning
        return [
            {"step": "ingest", "tool": "IngestPartnerFileTool", "args": {...}},
            {"step": "validate", "tool": "ValidateStagedDataTool", "args": {...}},
            {"step": "canonicalize", "tool": "CanonicalizeStagedDataTool", "args": {...}}
        ]
    
    def _execute_step(self, state, step_name, tool_name, tool_args):
        # Use BaseAgent default execution
        return super()._execute_step(state, step_name, tool_name, tool_args)
```

**LangChain Platform Adapter** (`platforms/langchain/`):

**Implementation:**
- Uses LangChain `create_agent()` internally
- Converts BaseAgent tools to LangChain `@tool` format via adapter
- Uses `AgentMiddleware` to intercept tool calls for evidence generation
- Converts LangChain results back to BaseAgent formats

**Tool Conversion:**
```python
def _baseagent_tool_to_langchain(self, name: str, tool_impl: Tool):
    @tool(name=name, description=f"Tool: {name}")
    def langchain_wrapper(**kwargs) -> str:
        result = tool_impl(**kwargs)
        if result.ok:
            return result.summary
        else:
            return f"Error: {result.summary}. Blockers: {result.blockers}"
    return langchain_wrapper
```

**Note on Production Usage**: The LangChain platform adapter is provided for framework comparison and demonstration purposes. For production deterministic ETL workflows (Intake, Reconciliation, Export agents), the minimal platform is the recommended choice. LLM/LangChain is used in production for the Data Analysis Agent (Week 10+) where it adds value through NL→SQL conversion per [BRD FR-008](../../brd.md#39-natural-language-data-analysis-fr-008).

**State Conversion:**
```python
def _convert_to_langchain_state(self, state: AgentState) -> Dict:
    return {
        "messages": [{"role": "user", "content": state.goal}],
        "run_id": state.run_id,
        "params": state.params
    }

def _parse_langchain_plan(self, langchain_result: Dict) -> List[Dict]:
    # Extract plan from LangChain agent output
    # Convert to BaseAgent plan format
    return [...]
```

**Microsoft Platform Adapter** (`platforms/microsoft/`):

**Implementation:**
- Uses Azure AI Studio / Semantic Kernel
- Maps BaseAgent tools to Semantic Kernel functions
- Uses Semantic Kernel planner for plan generation
- Converts Semantic Kernel results to BaseAgent formats
- Maintains BaseAgent contract compliance

**OpenAI Platform Adapter** (`platforms/openai/`):

**Implementation:**
- Uses OpenAI Assistants API
- Maps BaseAgent tools to OpenAI function calling format
- Uses Assistant API for planning
- Converts Assistant API results to BaseAgent formats
- Maintains BaseAgent contract compliance

**Anthropic Platform Adapter** (`platforms/anthropic/`):

**Implementation:**
- Uses Claude API with tool use
- Maps BaseAgent tools to Claude tool format
- Uses Claude for planning via tool use
- Converts Claude responses to BaseAgent formats
- Maintains BaseAgent contract compliance

**Adapter Comparison:**

| Feature | Minimal | LangChain | Microsoft | OpenAI | Anthropic |
|---------|---------|-----------|------------|--------|-----------|
| Planning | Deterministic | LLM-based | Semantic Kernel | Assistants API | Claude tool use |
| Tool Format | BaseAgent | Converted | Converted | Converted | Converted |
| Evidence | BaseAgent | BaseAgent | BaseAgent | BaseAgent | BaseAgent |
| State | AgentState | Converted | Converted | Converted | Converted |
| Vendor Lock-in | None | Low (OSS) | Medium | Medium | Medium |

---

## 7. Data Flow Specifications

### 7.1 Quarterly Processing Flow

```
1. Partner Files (CSV/Excel)
   ↓
2. Ingestion Tool (parse, normalize, stage)
   ↓
3. Validation Tool (execute rules, generate worksheet)
   ↓ [HITL if errors]
4. Canonicalization Tool (identity resolution, upsert)
   ↓
5. Reconciliation Tool (match with WSAC, classify)
   ↓
6. WSAC Export Tool (generate upload CSV, validate)
   ↓ [HITL if not ready]
7. [Manual WSAC Upload]
   ↓
8. WSAC Truth Sync Tool (load response, update CDM)
   ↓
9. Dynamics Export Tool (generate import CSV, validate)
   ↓
10. Evidence Bundle (complete audit trail)
```

### 7.2 Data Analysis Flow

```
1. User Query (Natural Language)
   ↓
2. Data Analysis Agent (plan query execution)
   ↓
3. Query Engine (NL → SQL conversion)
   ↓
4. Query Validator (safety checks)
   ↓
5. PostgreSQL CDM Database (execute SQL)
   ↓
6. Result Formatter (format for frontend)
   ↓
7. Response (table/chart/summary)
```

### 7.3 Query Engine Implementation Details

**NL → SQL Conversion Algorithm:**

1. **Schema Context Loading:**
   - Load CDM schema from PostgreSQL information_schema
   - Extract table names, column names, data types, foreign keys
   - Format as context prompt for LLM

2. **LLM Query Generation:**
   - Prompt: "Given this schema: {cdm_schema}, convert this query to SQL: {natural_language_query}"
   - Use LLM (OpenAI GPT-4, Claude, or Azure OpenAI) to generate SQL
   - Request parameterized query format (use placeholders for values)

3. **SQL Validation:**
   - Parse SQL using SQLAlchemy or sqlparse
   - Check for forbidden operations: DROP, DELETE, TRUNCATE, ALTER, CREATE
   - Validate table names against CDM schema
   - Validate column names against table schemas
   - Check for SQL injection patterns

4. **Query Execution:**
   - Use parameterized queries (prevent injection)
   - Execute against PostgreSQL CDM via SQLAlchemy
   - Set query timeout (prevent resource exhaustion)
   - Limit result set size (prevent memory issues)

5. **Result Formatting:**
   - Convert PostgreSQL results to DataFrame
   - Format based on query type:
     - **Table**: Return as-is
     - **Chart**: Aggregate and format for visualization
     - **Summary**: Generate natural language summary

**Query Validation Rules:**

```python
FORBIDDEN_KEYWORDS = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE"]

def validate_query(sql: str, cdm_schema: CDMSchema) -> ValidationResult:
    # 1. Check for forbidden keywords
    sql_upper = sql.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in sql_upper:
            return ValidationResult(valid=False, error=f"Forbidden operation: {keyword}")
    
    # 2. Parse SQL
    parsed = parse_sql(sql)
    
    # 3. Validate table names
    for table in parsed.tables:
        if table not in cdm_schema.tables:
            return ValidationResult(valid=False, error=f"Unknown table: {table}")
    
    # 4. Validate column names
    for table, columns in parsed.columns.items():
        if table not in cdm_schema.tables:
            continue
        schema_columns = cdm_schema.tables[table].columns
        for col in columns:
            if col not in schema_columns:
                return ValidationResult(valid=False, error=f"Unknown column: {table}.{col}")
    
    return ValidationResult(valid=True)
```

**CDM Schema Context Format:**

```python
def get_cdm_schema_context() -> str:
    """Generate schema context for LLM prompt."""
    schema = load_cdm_schema()  # From PostgreSQL
    context = "Canonical Data Model Schema:\n\n"
    
    for table_name, table_info in schema.tables.items():
        context += f"Table: {table_name}\n"
        context += f"  Primary Key: {table_info.primary_key}\n"
        context += f"  Columns:\n"
        for col_name, col_type in table_info.columns.items():
            context += f"    - {col_name} ({col_type})\n"
        if table_info.foreign_keys:
            context += f"  Foreign Keys:\n"
            for fk in table_info.foreign_keys:
                context += f"    - {fk.column} -> {fk.references_table}.{fk.references_column}\n"
        context += "\n"
    
    return context
```

### 7.4 Evidence Bundle Generation Flow

**Generation Process:**

1. **Run Initialization:**
   - Create evidence bundle directory: `core/audit/runs/<run-id>/`
   - Generate `manifest.json` with run metadata
   - Initialize `trace.jsonl` file

2. **During Execution:**
   - **Plan Phase**: Write plan to `plan.md` via `_write_plan()`
   - **Tool Calls**: Append to `tool_calls.jsonl` via `_emit()` with STEP_START/STEP_END events
   - **Artifacts**: Write to `outputs/` directory via `_write_json_artifact()`
   - **State Checkpoints**: Save to `checkpoints/<step-name>.json` after each step

3. **After Execution:**
   - **Summary**: Generate `summary.json` via `summarize()` method
   - **Audit Record**: Generate `audit_record.json` via `audit_record()` method
   - **Evidence Bundle Manifest**: Generate `evidence_bundle.json` via `evidence_bundle()` method

**Trace Event Emission:**

```python
def _emit(self, state: AgentState, event_type: str, message: str, data: Dict = None):
    """Emit trace event to JSONL file."""
    event = TraceEvent(
        timestamp=datetime.utcnow().isoformat(),
        event_type=event_type,
        run_id=state.run_id,
        message=message,
        data=data or {}
    )
    
    trace_path = f"{self.output_dir}/trace.jsonl"
    with open(trace_path, "a") as f:
        f.write(json.dumps(event.__dict__) + "\n")
```

**Artifact Collection:**

- **Validation Worksheets**: Written by `ValidateStagedDataTool` to `outputs/validation_worksheet.csv`
- **Reconciliation Worksheets**: Written by `ReconcileParticipantsTool` to `outputs/reconciliation_worksheet.csv`
- **Export Files**: Written by export tools to `outputs/wsac_export.csv` or `outputs/dynamics_export.csv`
- **Query Results**: Written by analysis tools to `outputs/query_results.json`

**Evidence Bundle Validation:**

```python
def validate_evidence_bundle(run_id: str) -> ValidationResult:
    """Validate evidence bundle completeness."""
    bundle_dir = f"core/audit/runs/{run_id}"
    required_files = [
        "manifest.json",
        "plan.md",
        "trace.jsonl",
        "summary.json",
        "audit_record.json",
        "evidence_bundle.json"
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(f"{bundle_dir}/{file}"):
            missing.append(file)
    
    if missing:
        return ValidationResult(valid=False, errors=[f"Missing files: {missing}"])
    
    return ValidationResult(valid=True)
```

---

## 8. Security Requirements

### 8.1 Authentication & Authorization

**Week 2 MVP:**
- No authentication (development only)

**Week 3:**
- Azure AD app registration for SharePoint access
- SharePoint client authentication via client ID/secret
- Secure link access (code-based or Azure AD auth)

**Week 11:**
- Azure AD authentication for API endpoints
- Bearer token validation
- Role-based access control (if needed)

### 8.2 Data Classification

**Requirements:**
- All runs must declare data classification (Public/Internal/Confidential/Restricted)
- Restricted data must not be sent to third-party LLMs without approval
- PII must be minimized in evidence bundles
- Redaction tools available for PII removal

### 8.3 Secret Management

**Requirements:**
- No hardcoded credentials
- Use Azure Key Vault or environment variables
- Rotate credentials regularly
- Least privilege access

**SharePoint Integration:**
- Azure AD app registration with least privilege permissions
- Client ID and secret stored in Azure Key Vault
- SharePoint site URL and folder paths in configuration

**Secure Link Security:**
- Access codes generated using `secrets.token_urlsafe(16)` (cryptographically secure)
- Codes stored in PostgreSQL `secure_links` table (not in-memory)
- Link expiration: 7 days (configurable)
- Access logging for audit trail
- Email delivery via secure email service (no PII in email body)

### 8.4 Query Safety

**Requirements:**
- Prevent DROP, DELETE, TRUNCATE operations
- Validate table/column names against CDM schema
- Limit query complexity (prevent resource exhaustion)
- Rate limiting on API endpoints

---

## 9. Performance Requirements

### 9.1 Response Times

- **Data Analysis Queries**: <5 seconds for queries against <10K records
- **Ingestion**: 1000+ rows per minute
- **Validation**: <30 seconds for 1000 rows
- **Canonicalization**: <60 seconds for 1000 rows

### 9.2 Scalability

- **Concurrent Users**: Support 10+ concurrent Copilot/browser users
- **Database**: Support 100K+ participant records
- **Evidence Bundles**: Efficient storage and retrieval

### 9.3 Resource Usage

- **Memory**: <2GB for typical quarter processing
- **CPU**: Efficient batch processing
- **Storage**: Evidence bundles <100MB per run

---

## 10. Testing Requirements

### 10.1 Unit Tests

- All deterministic logic in `core/` must have unit tests
- Test coverage: 80%+ for core modules
- Tests must not call external services

### 10.2 Integration Tests

- End-to-end quarter workflow test
- Error recovery test
- Evidence bundle completeness test
- Data analysis query test

### 10.3 Test Data

- Use masked/mock data for testing
- Synthetic data generators available
- Test fixtures for all data formats

---

## 11. Deployment Requirements

### 11.1 Environment Setup

**Development:**
- Local Python environment
- PostgreSQL database (local instance or Azure Database for PostgreSQL)
- Local API server

**Production:**
- Azure App Service or similar
- PostgreSQL database (Azure Database for PostgreSQL)
- Azure Key Vault for secrets
- Azure Bot Service for Teams bot

### 11.2 Configuration Management

- Environment variables for configuration
- `.env.example` with placeholders (no secrets)
- Configuration files in `clients/cfa/`

**Required Environment Variables:**

**Database:**
```bash
DATABASE_URL=postgresql://user:password@host:port/database
```

**SharePoint Integration (Week 2+):**
```bash
SHAREPOINT_SITE_URL=https://yourorg.sharepoint.com/sites/CFA
SHAREPOINT_CLIENT_ID=<Azure AD App ID>
SHAREPOINT_CLIENT_SECRET=<Azure AD App Secret>
SHAREPOINT_WEBHOOK_SECRET=<Webhook secret for file change notifications>
```

**Teams Integration (Week 2+):**
```bash
TEAMS_WEBHOOK_URL=<Teams webhook URL for Adaptive Card actions>
TEAMS_WEBHOOK_SECRET=<Webhook secret for Teams>
TEAMS_APP_ID=<Teams app ID>
TEAMS_APP_SECRET=<Teams app secret>
```

**Prevailing Wage API (Week 2+):**
```bash
WAGE_API_URL=<External prevailing wage API URL>
WAGE_API_KEY=<API key>
```

**CDM Schema (Week 1):**
```bash
CDM_SCHEMA_PATH=<Path to CFA-provided PostgreSQL schema file>
# Or use direct database connection if schema already applied
```

### 11.3 Monitoring & Logging

- Structured logging (JSON format)
- Request/response logging for API
- Error tracking and alerting
- Performance metrics

---

## 12. Documentation Requirements

### 12.1 Technical Documentation

- Architecture documentation
- API reference
- Tool API documentation
- Evidence bundle format specification
- Database schema documentation

### 12.2 User Documentation

- Runbook for operations
- Data analysis user guide
- Copilot integration guide
- Browser app user guide
- SharePoint integration guide (Azure AD setup, folder structure, secure link generation, webhook configuration)
- Enhanced validation rules documentation (active past graduation, name misspellings, prevailing wage)
- Partner communication workflow (secure link access, code verification)
- HITL approval workflow guide (Teams Adaptive Cards, approval process, rejection handling)
- Validation retry and resume workflow guide (SharePoint webhooks, automatic retry, checkpoint management)

### 12.3 Code Documentation

- Module-level docstrings for all Python files
- Function docstrings with type hints
- Inline comments for complex logic

---

## 13. Implementation Phases

### Phase A: Foundations (Weeks 1-3) - CONDENSED
- **Week 1**: BaseAgent contract, CDM schema import (CFA-provided), evidence bundles, platform adapters (minimal required; LangChain optional for comparison)
- **Week 2**: Ingestion, validation engine framework, integrate CFA-provided validation rules, SharePoint integration, HITL approval workflow (Teams Adaptive Cards), validation retry/resume logic, Teams/Copilot MVP
- **Week 3**: Canonicalization with identity resolution and change tracking
- **Note**: Timeline condensed assuming CFA provides CDM schema, business rules, and validation logic

### Phase B: Reconciliation & Exports (Weeks 4-7)
- **Week 4**: WSAC reconciliation (moved from Week 5 due to condensed Phase A)
- **Week 5**: WSAC export generation
- **Week 6**: WSAC post-upload truth sync
- **Week 7**: Dynamics export preparation

### Phase C: Analysis & Capstone (Weeks 8-12)
- **Week 8**: Multi-step orchestration coordinator (moved from Week 9)
- **Week 9**: Data Analysis Agent foundation
- **Week 10**: Data Analysis Agent + Copilot enhancement + Browser App MVP
- **Week 11**: End-to-end quarter close-out
- **Week 12**: Capstone demo & framework comparison

---

## 14. Acceptance Criteria

### 14.1 Functional Acceptance

- ✅ Complete quarter workflow runs end-to-end from CLI
- ✅ All platforms produce valid, comparable evidence bundles
- ✅ Natural language queries return accurate results
- ✅ Copilot integration works in Teams/Outlook/Word
- ✅ Browser app displays query results correctly
- ✅ Enhanced validation rules detect active past graduation errors
- ✅ Name misspelling detection flags potential errors before WSAC upload
- ✅ Prevailing wage validation blocks WSAC export when requirements not met
- ✅ Validation reports uploaded to SharePoint/Dataverse successfully (two-stage: internal first, partner-accessible after approval)
- ✅ HITL approval workflow functional via Teams Adaptive Cards
- ✅ Secure links generated and accessible by partners (only after staff approval)
- ✅ Partner files read from SharePoint during ingestion
- ✅ Validation retry and resume workflow functional (SharePoint webhook triggers re-validation)
- ✅ Automatic resume from canonicalization when validation passes on retry

### 14.2 Technical Acceptance

- ✅ All agents conform to BaseAgent contract
- ✅ All deterministic logic has unit tests
- ✅ Evidence bundles validated and complete
- ✅ No secrets committed to repository
- ✅ API endpoints documented and tested

### 14.3 Quality Acceptance

- ✅ Code follows Python type hints and docstring conventions
- ✅ Architecture documentation complete
- ✅ Runbook available for operations
- ✅ Security controls implemented

---

## 15. Dependencies & Constraints

### 15.1 External Dependencies

- Microsoft Copilot Studio availability
- Azure Bot Service availability
- WSAC export/import format stability
- Dynamics import format stability
- SharePoint webhook notifications available for file change events
- Teams webhook infrastructure available for Adaptive Card actions
- Azure AD app registration configured for SharePoint and Teams access
- **CFA provides PostgreSQL CDM schema** (ready to import, not designed from scratch)
- **CFA provides business rules and validation logic** (ready to integrate into validation engine framework)

### 15.2 Technical Constraints

- Python 3.10+ required
- Database: PostgreSQL (required for all environments)
- API: FastAPI framework
- Frontend: Modern browser support (Chrome, Edge, Firefox)

### 15.3 Business Constraints

- Must maintain auditability (evidence bundles)
- Must support human-in-the-loop (HITL)
- Must declare data classification
- Must handle PII appropriately

---

## 16. Risk Mitigation

### Technical Risks

**Risk:** Query injection attacks  
**Mitigation:** Query validation, parameterized queries, schema validation

**Risk:** Vendor lock-in  
**Mitigation:** Platform-agnostic core, BaseAgent contract, framework evaluation

**Risk:** Performance issues  
**Mitigation:** Query optimization, indexing, caching, rate limiting

**Risk:** Data loss  
**Mitigation:** Idempotent operations, checkpoints, evidence bundles, backups

---

## 17. Success Metrics

### Technical Metrics

- **Test Coverage**: 80%+ for core modules
- **API Response Time**: <5 seconds for analysis queries
- **Uptime**: 99% availability
- **Error Rate**: <1% of runs fail

### Business Metrics

- **Processing Time**: 60%+ reduction in quarterly processing time
- **Data Quality**: 99%+ validation accuracy
- **User Adoption**: 80%+ of staff use data analysis features
- **Audit Readiness**: 100% of runs have complete evidence bundles

---

## 18. Approval

**Technical Lead:** [TBD]  
**Architecture Review:** [TBD]  
**Security Review:** [TBD]  
**Date:** [TBD]

