# Business Requirements Document (BRD)
## CFA Applied Agentic AI — Quarterly Workforce Reporting System

**Version:** 1.1  
**Date:** 11-16-2025 
**Status:** Draft  
**Owner:** Computing For All (CFA)

---

## 1. Executive Summary

### 1.1 Purpose
This document defines the business requirements for the CFA Applied Agentic AI system, a quarterly workforce-reporting platform that automates data processing, validation, reconciliation, and reporting while maintaining full auditability and governance controls. The system includes enhanced validation rules to catch common manual errors and secure SharePoint/Dataverse integration for partner communication.

### 1.2 Business Problem
CFA currently processes quarterly workforce data through manual, error-prone workflows:
- Partner data arrives in multiple formats
- Manual validation and reconciliation is time-consuming and error-prone
- Common errors include: participants marked as active past graduation date, name misspellings not caught until HITL, job placements not meeting prevailing wage requirements
- Manual partner communication requires email attachments, violating data sharing policies
- Lack of audit trail makes compliance reviews difficult
- Staff cannot easily query and analyze canonicalized data
- No natural language interface for data exploration

### 1.3 Business Objectives
1. **Automate Quarterly Reporting Workflow**: Reduce manual effort in processing partner data
2. **Ensure Data Quality**: Automated validation with enhanced rules for common errors and human-in-the-loop safeguards
3. **Secure Partner Communication**: Share validation reports via secure links (no email attachments) to comply with data sharing policies
4. **Maintain Auditability**: Complete evidence trail for every data processing run
5. **Enable Data Analysis**: Natural language queries against canonicalized data
6. **Support Multiple Access Methods**: Teams (via Copilot plugin or Teams Bot) and browser interfaces
7. **Enable Platform Comparison**: Evaluate vendor agent platforms for production use

### 1.4 Success Metrics
- **Efficiency**: Reduce quarterly processing time by 60%+
- **Accuracy**: Zero data loss, 99%+ validation accuracy
- **Error Detection**: 95%+ of manual errors caught automatically (active past graduation, name misspellings, prevailing wage)
- **Partner Communication**: 100% of validation reports shared via secure links (no email attachments)
- **Auditability**: 100% of runs produce complete evidence bundles
- **Usability**: Staff can query data using natural language (no SQL knowledge required)
- **Compliance**: All runs declare data classification and PII handling
- **WSAC Export Blocking**: 100% of prevailing wage violations prevent WSAC export

---

## 2. Business Context

### 2.1 Stakeholders

**Primary Users:**
- **CFA Staff**: Process quarterly reports, validate data, generate exports, communicate with partners
- **Data Analysts**: Query and analyze canonicalized data
- **Compliance Officers**: Review evidence bundles and audit trails

**Secondary Stakeholders:**
- **CFA Leadership**: Receive production recommendations and framework comparisons
- **External Partners**: Provide data in various formats, receive validation reports via secure links
- **WSAC**: Receive bulk uploads and provide authoritative data

### 2.2 Business Process Overview

**Current State:**
1. Partner submits data files (various formats)
2. Manual data entry/validation
3. Manual error detection (active past graduation, name misspellings, prevailing wage)
4. Manual partner communication via email and scheduled meetings
5. Manual reconciliation with WSAC prior-quarter data
6. Manual export generation for WSAC and Dynamics
7. Manual tracking of changes and status updates

**Future State:**
1. Partner submits data files to SharePoint → Automated ingestion from SharePoint
2. Automated validation with enhanced rules (active past graduation, name misspellings, prevailing wage)
3. Automated validation report generation and upload to SharePoint/Dataverse
4. Automated secure link generation for partner access (no email attachments)
5. Automated canonicalization with identity resolution
6. Automated reconciliation with WSAC (provides data for name comparison)
7. Automated export generation with pre-submission validation (blocks if prevailing wage violations)
8. Automated truth sync from WSAC post-upload
9. Natural language data analysis via Copilot/browser

### 2.3 Business Rules

**Data Classification:**
- Partner data is **Confidential** by default
- Data containing PII is **Restricted**
- All runs must declare data classification in evidence bundles
- Restricted data must not be sent to third-party LLMs without approval

**Validation Rules:**
- Required fields must be present (Error severity)
- Date ranges must be valid (Error/Warning)
- Employment status must be consistent (Warning)
- Program status transitions must be valid (Error)
- **Active status past graduation date** (Error severity)
  - Participants marked as "Currently active" but `end_date` has passed must be flagged
  - Blocks processing until status corrected
- **Name misspelling detection** (Warning severity)
  - Compare canonical participant names with WSAC prior-quarter data
  - Use fuzzy matching (Levenshtein distance) with 85% similarity threshold
  - Flags potential misspellings before WSAC upload
- **Prevailing wage validation** (Error severity, blocks WSAC entry)
  - Job placements must meet prevailing wage requirements
  - Fetches prevailing wage from external API (occupation code + region)
  - Blocks WSAC export if wage below prevailing wage
  - Special flag: `blocks_wsac_entry=True`
- Any Error = automatic halt for human review
- N+ Warnings = halt threshold (configurable)

**Partner Communication Rules:**
- Validation reports must be shared via secure links (no email attachments)
- Secure links require authentication (code-based or Azure AD)
- Links expire after 7 days (configurable)
- Access codes sent to partner's registered email
- All link accesses logged for audit

**Reconciliation Rules:**
- WSAC is the authoritative source of truth
- Prior-quarter WSAC data must be reconciled before new quarter upload
- WSAC data used for name misspelling detection during validation
- WSAC-assigned IDs must be synced back to canonical data
- Status transitions must be tracked and validated

**Export Rules:**
- WSAC exports must pass pre-submission validation
- WSAC exports blocked if `blocks_wsac_entry=True` (prevailing wage violations)
- Dynamics exports must maintain referential integrity
- All exports must be validated before delivery

---

## 3. Functional Requirements

### 3.1 Data Ingestion (FR-001)

**Requirement:** System must ingest partner data from multiple formats and sources

**Business Need:** Partners submit data in different formats, stored in SharePoint

**Acceptance Criteria:**
- Support CSV and Excel formats
- Handle encoding variations (UTF-8, Windows-1252, etc.)
- Parse Quarterly Report format
- Parse Dynamics Import format
- Parse WSAC Bulk Upload format
- **Read partner files from SharePoint** (Week 2+)
- Support local file reading (for development/testing)
- Record file hash and metadata for audit
- Generate ingestion summary with row counts and parse errors

**Priority:** Must Have (P0)

---

### 3.2 Data Validation (FR-002)

**Requirement:** System must validate ingested data against CFA business rules, including enhanced rules for common manual errors

**Business Need:** Ensure data quality before canonicalization, catch errors that are currently missed until HITL

**Acceptance Criteria:**
- Execute validation rules with severity levels (Error/Warning/Info)
- **Enhanced validation rules (provided by CFA and integrated into validation engine):**
  - Active status past graduation date (Error)
  - Name misspelling detection via WSAC comparison (Warning)
  - Prevailing wage validation (Error, blocks WSAC entry)
- Generate enhanced review worksheet with:
  - Color-coding by severity
  - Action Required column with specific guidance
  - Notes column for additional context
- **Two-stage report upload:**
  - First: Upload validation report to SharePoint/Dataverse (internal location for staff review)
  - Second: After staff approval, upload to partner-accessible location
- **HITL Approval Workflow:**
  - Send Teams Adaptive Card approval request to CFA staff/user group
  - Include validation summary (error/warning counts, severity breakdown)
  - Include link to view full report (internal SharePoint link)
  - Wait for staff approval before proceeding
- Generate secure link for partner access (code-based or Azure AD auth) **only after staff approval**
- Halt processing on Error-level violations
- Halt processing on configurable Warning threshold
- **Validation Retry & Resume:**
  - SharePoint webhook triggers re-validation when partner uploads fixed file
  - If validation passes: Automatically resume from canonicalization step
  - If validation fails: Generate new report and request approval again
- Generate validation summary for staff review
- Link validation results to evidence bundle
- **Return secure link URL** for partner notification (after approval)

**Priority:** Must Have (P0)

---

### 3.3 Secure Partner Sharing (FR-013)

**Requirement:** System must share validation reports with partners via secure links (no email attachments)

**Business Need:** Comply with data sharing policies that prohibit email attachments

**Acceptance Criteria:**
- Upload validation reports to SharePoint/Dataverse (two-stage: internal first, partner-accessible after approval)
- **Generate secure access links only after staff approval via Teams Adaptive Card**
- Generate secure access links (code-based or Azure AD authenticated)
- Access codes cryptographically secure (`secrets.token_urlsafe(16)`)
- Store access codes in PostgreSQL `secure_links` table (not in-memory)
- Send access codes to partner's registered email via secure email service
- Links expire after 7 days (configurable)
- Track access counts and last accessed timestamp
- Log all link accesses for audit
- Provide secure link verification API endpoint
- Support code entry frontend for partner access
- **SharePoint webhook integration** for automatic validation retry when partner fixes data

**Priority:** Must Have (P0)

---

### 3.4 Canonicalization (FR-003)

**Requirement:** System must transform validated data into canonical data model

**Business Need:** Single source of truth for participant, enrollment, and employment data

**Acceptance Criteria:**
- Resolve participant identity (deduplication)
- Create/update canonical records idempotently
- Track all changes with before/after values
- Generate change log for audit
- Support multiple enrollments per participant
- Support multiple employment records per participant

**Priority:** Must Have (P0)

---

### 3.5 WSAC Reconciliation (FR-004)

**Requirement:** System must reconcile canonical data with WSAC prior-quarter data

**Business Need:** Ensure consistency with WSAC authoritative records, provide data for name misspelling detection

**Acceptance Criteria:**
- Load WSAC prior-quarter export
- Match participants (WSAC ID, name+DOB+ZIP)
- Classify participants (New/Existing/Changed/Missing/Unmatched)
- Generate color-coded reconciliation worksheet
- Explain classification decisions
- Generate reconciliation summary
- **Provide WSAC data to Week 3 validation** for name comparison

**Priority:** Must Have (P0)

---

### 3.6 WSAC Export Generation (FR-005)

**Requirement:** System must generate WSAC bulk upload CSV

**Business Need:** Submit quarterly data to WSAC

**Acceptance Criteria:**
- Map canonical data to WSAC format
- Transform fields per WSAC specifications
- Validate export against WSAC schema
- Assess readiness (READY/NOT_READY/REQUIRES_REVIEW)
- **Check for `blocks_wsac_entry=True` flag** from Week 3 validation
- **Block export if prevailing wage violations exist**
- Generate pre-submission validation report
- Block submission if NOT_READY

**Priority:** Must Have (P0)

---

### 3.7 WSAC Truth Sync (FR-006)

**Requirement:** System must sync WSAC post-upload outcomes back to canonical data

**Business Need:** WSAC is authoritative source; must reflect WSAC-assigned IDs and statuses

**Acceptance Criteria:**
- Load WSAC post-upload response
- Update canonical records with WSAC-assigned IDs
- Update participant statuses based on WSAC acceptance/rejection
- Track status transitions
- Generate delta report showing changes
- Handle WSAC errors (rejected records)

**Priority:** Must Have (P0)

---

### 3.8 Dynamics Export Generation (FR-007)

**Requirement:** System must generate Dynamics import files

**Business Need:** Import data into internal Dynamics system

**Acceptance Criteria:**
- Map canonical data to Dynamics format
- Validate referential integrity
- Ensure all required relationships present
- Generate import checklist
- Validate lookup values
- Generate integrity validation report

**Priority:** Must Have (P0)

---

### 3.9 Natural Language Data Analysis (FR-008)

**Requirement:** Staff must be able to query canonicalized data using natural language

**Business Need:** Enable data exploration without SQL knowledge

**Acceptance Criteria:**
- Accept natural language queries (e.g., "Show Q4 enrollments")
- Convert to SQL queries against CDM
- Execute queries safely (no DROP/DELETE)
- Return results in table, chart, or summary format
- Support trend analysis queries
- Support comparison queries (quarter-over-quarter)
- Generate human-readable summaries

**Priority:** Must Have (P0)

---

### 3.10 Microsoft Teams Integration (FR-009)

**Requirement:** Staff must access data analysis via Microsoft Teams

**Business Need:** Access data analysis within existing Microsoft 365 workflow

**Acceptance Criteria:**
- **Option 1 - Copilot Studio Plugin:**
  - Copilot plugin available in Teams, Outlook, Word
  - Natural language queries work in Copilot
  - Responses formatted appropriately for Copilot
- **Option 2 - Teams Bot (Optional):**
  - Teams Bot available in Teams via Microsoft Bot Framework SDK
  - Natural language queries work via bot interface
  - Responses formatted as Teams cards
- Authentication via Azure AD
- Available Week 2 (MVP), enhanced Week 10 (full analysis)

**Priority:** Must Have (P0)

---

### 3.11 Browser Application (FR-010)

**Requirement:** Staff must access data analysis via web browser

**Business Need:** Alternative access method for data analysis

**Acceptance Criteria:**
- Web-based interface for natural language queries
- Display results in table format (MVP)
- Display results in charts (Week 11)
- Export results to CSV/PDF
- Query history (Week 12)
- Dashboard views (Week 12)

**Priority:** Must Have (P0)

---

### 3.12 Evidence Bundle Generation (FR-011)

**Requirement:** Every agent run must produce complete evidence bundle

**Business Need:** Auditability and compliance

**Acceptance Criteria:**
- Evidence bundle includes: manifest.json, plan.md, tool_calls.jsonl, outputs/, summary.md
- Manifest declares data classification and PII handling
- Trace file records all tool calls in order
- Summary explains what happened and why
- Evidence bundle validated before run completion
- Runs without evidence bundles are invalid

**Priority:** Must Have (P0)

---

### 3.13 Human-in-the-Loop Safeguards (FR-012)

**Requirement:** System must halt for human review when validation thresholds are exceeded, with staff approval required before sharing validation reports with partners

**Business Need:** Prevent automated processing of invalid data and ensure staff oversight of partner communications

**Acceptance Criteria:**
- Halt on any Error-level validation violation
- Halt on configurable Warning threshold
- Generate review worksheet for human review
- **Upload review worksheet to SharePoint/Dataverse (internal location)**
- **Send Teams Adaptive Card approval request to CFA staff/user group** with validation summary and link to view report
- **Wait for staff approval before generating secure link for partner access**
- If approved: Generate secure link and send to partner
- If rejected: Halt workflow and log rejection reason
- **Support validation retry and resume**: When partner fixes data and uploads new file, SharePoint webhook triggers re-validation
- **Automatic resume**: If validation passes on retry, automatically resume from canonicalization step
- **Conditional retry**: If validation still fails on retry, generate new report and request approval again
- Record HITL decisions and approval status in evidence bundle

**Priority:** Must Have (P0)

---

## 4. Non-Functional Requirements

### 4.1 Performance (NFR-001)

- **Query Response Time**: Data analysis queries must return results within 5 seconds for queries against <10K records
- **Ingestion Throughput**: Process 1000+ rows per minute
- **Concurrent Users**: Support 10+ concurrent Copilot/browser users
- **SharePoint API**: Handle SharePoint file operations efficiently (retry logic, error handling)

### 4.2 Reliability (NFR-002)

- **Uptime**: 99% availability during business hours
- **Error Recovery**: System must support resumption from checkpoints
- **Idempotency**: Same input must produce same output (deterministic)
- **SharePoint Resilience**: Fallback to local storage if SharePoint unavailable

### 4.3 Security (NFR-003)

- **Authentication**: Azure AD authentication for Copilot/browser access
- **SharePoint Authentication**: Azure AD app registration with least privilege permissions
- **Secure Links**: Cryptographically secure access codes, expiration enforcement, access logging
- **Data Classification**: All runs must declare data classification
- **PII Handling**: Restricted data must not be sent to third-party services without approval
- **Secret Management**: No hardcoded credentials; use Azure Key Vault or similar
- **Audit Trail**: Complete audit trail for all data access and secure link usage

### 4.4 Usability (NFR-004)

- **Natural Language**: Staff can query data without SQL knowledge
- **Error Messages**: Clear, actionable error messages
- **Partner Access**: Simple code entry interface for secure link access
- **Documentation**: Complete user guides and runbooks
- **Training**: Minimal training required (intuitive interface)

### 4.5 Compliance (NFR-005)

- **Evidence Bundles**: Complete evidence bundles for all runs
- **Data Classification**: All data properly classified
- **PII Redaction**: PII redaction tools available when needed
- **Audit Readiness**: System must support after-the-fact audit reviews
- **Data Sharing Policy**: No email attachments; all sharing via secure links

---

## 5. Business Value

### 5.1 Efficiency Gains
- **Time Savings**: Reduce quarterly processing from days to hours
- **Error Reduction**: Automated validation catches errors early, including common manual errors
- **Consistency**: Standardized processing across all partners
- **Partner Communication**: Automated secure link generation eliminates manual email coordination

### 5.2 Quality Improvements
- **Data Accuracy**: Automated validation ensures data quality, catches active past graduation, name misspellings, prevailing wage violations
- **Error Prevention**: Enhanced validation rules prevent WSAC export errors before submission
- **Audit Trail**: Complete evidence bundles support compliance
- **Traceability**: Every decision is traceable and explainable

### 5.3 Capability Enhancements
- **Data Analysis**: Natural language queries enable self-service analytics
- **Accessibility**: Multiple access methods (Copilot, browser) increase adoption
- **Governance**: Built-in governance controls ensure safe automation
- **Partner Engagement**: Secure link sharing improves partner communication workflow

### 5.4 Risk Mitigation
- **Compliance**: Complete audit trails support regulatory compliance
- **Data Security**: Data classification and PII handling controls, secure link sharing
- **Human Oversight**: HITL safeguards prevent automated errors
- **Policy Compliance**: Secure link sharing eliminates email attachment policy violations

---

## 6. User Stories

### US-001: As a CFA staff member, I want to ingest partner data files from SharePoint so that I can process quarterly reports automatically
**Acceptance:** System reads CSV/Excel files from SharePoint, parses multiple formats, generates ingestion summary

### US-002: As a CFA staff member, I want validation errors highlighted so that I can fix data issues before processing
**Acceptance:** Review worksheet shows errors with severity levels, system halts on blocking errors

### US-003: As a CFA staff member, I want the system to detect participants marked as active past graduation so that I don't have to catch this error manually
**Acceptance:** System flags participants with "Currently active" status but past end_date, Error severity

### US-004: As a CFA staff member, I want the system to detect name misspellings by comparing with WSAC data so that errors are caught before WSAC upload
**Acceptance:** System compares canonical names with WSAC data using fuzzy matching, flags <85% similarity as Warning

### US-005: As a CFA staff member, I want the system to validate prevailing wage requirements so that WSAC export errors are prevented
**Acceptance:** System checks job placements against prevailing wage API, blocks WSAC export if wage below requirement

### US-006: As a CFA staff member, I want to share validation reports with partners via secure links so that I comply with data sharing policies
**Acceptance:** Validation reports uploaded to SharePoint, secure link generated, partner receives code via email, accesses report via secure link

### US-007: As a CFA data analyst, I want to query data using natural language so that I don't need to know SQL
**Acceptance:** Can ask "Show Q4 enrollments" and get results in table/chart format

### US-008: As a CFA staff member, I want to access data analysis from Teams so that I can query data without leaving my workflow
**Acceptance:** 
- Option 1: Copilot plugin available in Teams (via Copilot Studio conversational plugin), responds to natural language queries
- Option 2: Teams Bot available in Teams (via Microsoft Bot Framework SDK), responds to natural language queries
- Both options provide access to data analysis within Teams workflow

### US-009: As a compliance officer, I want to review evidence bundles so that I can verify data processing decisions
**Acceptance:** Evidence bundles include manifest, plan, tool calls, outputs, and summary

### US-010: As a CFA staff member, I want the system to halt for review when data quality issues are detected so that errors don't propagate
**Acceptance:** System stops on validation errors, generates review worksheet, uploads to SharePoint (internal), sends Teams approval request, waits for staff approval, then generates secure link for partner if approved

### US-012: As a CFA staff member, I want to approve validation reports before they are shared with partners so that I can review errors and ensure appropriate communication
**Acceptance:** Receive Teams Adaptive Card with validation summary and link to view report, approve or reject with one click, system only generates secure link after approval

### US-013: As a CFA staff member, I want the system to automatically retry validation when partners fix data so that I don't have to manually trigger re-validation
**Acceptance:** When partner uploads fixed file to SharePoint, webhook triggers automatic re-validation; if validation passes, workflow automatically resumes from canonicalization step

### US-011: As a partner, I want to access validation reports via secure link so that I can review and fix data errors
**Acceptance:** Receive access code via email, enter code on secure link page, access validation report from SharePoint

---

## 7. Out of Scope

- **Real-time Data Processing**: System processes quarterly batches, not real-time streams
- **Partner Portal**: Partners submit files via existing channels (SharePoint), not through this system
- **WSAC/Dynamics Integration**: System generates exports; manual upload to external systems
- **Historical Data Migration**: Focus on new quarterly processing (not historical data migration)
- **Multi-Client Support**: Initial focus on CFA; extensible to other clients later
- **Direct Email Integration**: Partners receive access codes via secure email service, not direct system email

---

## 8. Dependencies

### 8.1 External Dependencies
- **WSAC**: Provides prior-quarter exports and accepts bulk uploads
- **Microsoft Dynamics**: Receives import files
- **Microsoft Copilot**: Platform for Copilot Studio plugin
- **Microsoft Teams Bot Framework**: Platform for Teams Bot integration (optional)
- **Azure Services**: Azure Bot Service, Azure AD for authentication
- **SharePoint Online**: Partner file storage, validation report sharing
- **Dataverse**: Alternative storage for validation reports (optional)
- **External Wage API**: Provides prevailing wage data for validation

### 8.2 Internal Dependencies
- **Partner Data**: Partners must provide data in supported formats, stored in SharePoint
- **Business Rules**: CFA business rules and validation logic must be provided (ready to integrate into validation engine framework)
- **CDM Schema**: Canonical data model (PostgreSQL schema) must be provided by CFA (ready to import)
- **Partner Email Addresses**: Partner registered email addresses for secure link code delivery
- **SharePoint Webhooks**: SharePoint webhook notifications configured for file change events
- **Teams Webhook Infrastructure**: Teams webhook infrastructure configured for Adaptive Card action responses

---

## 9. Assumptions

1. Partners will continue to provide data in current formats, stored in SharePoint
2. WSAC export/import formats remain stable
3. Microsoft Copilot remains available and supports plugin integration
4. Staff have access to Microsoft 365 (Teams, Outlook, Word)
5. Data classification policies are defined and stable
6. SharePoint Online is available and accessible for partner file storage
7. External Wage API is available and provides accurate prevailing wage data
8. Partners have registered email addresses for secure link code delivery
9. Secure email service is available for sending access codes
10. **CFA provides PostgreSQL CDM schema** (ready to import, not designed from scratch)
11. **CFA provides business rules and validation logic** (ready to integrate into validation engine framework)
12. **SharePoint webhook notifications** are available for file change events
13. **Teams webhook infrastructure** is available for Adaptive Card action responses
14. **Azure AD app registration** is configured for SharePoint and Teams access

---

## 10. Risks and Mitigations

### Risk 1: Data Quality Issues
**Mitigation:** Automated validation with enhanced rules (active past graduation, name misspellings, prevailing wage), HITL safeguards, review worksheets

### Risk 2: WSAC Format Changes
**Mitigation:** Versioned mappings, validation against WSAC schema

### Risk 3: Vendor Lock-in
**Mitigation:** Platform-agnostic core, BaseAgent contract, framework evaluation

### Risk 4: PII Exposure
**Mitigation:** Data classification controls, PII redaction tools, approval workflows

### Risk 5: System Complexity
**Mitigation:** Iterative development, comprehensive documentation, runbooks

### Risk 6: SharePoint API Failures
**Mitigation:** Retry logic, fallback to local storage, error handling, access logging

### Risk 7: Secure Link Compromise
**Mitigation:** Cryptographically secure code generation, expiration enforcement, access logging, rate limiting on verification endpoint

### Risk 8: Prevailing Wage API Unavailability
**Mitigation:** Async API calls, timeout handling, fallback to manual validation, cached wage data

### Risk 9: Name Misspelling False Positives
**Mitigation:** Configurable similarity threshold (default 85%), manual review flag, confidence scoring

### Risk 10: Partner Access Issues
**Mitigation:** Clear instructions for secure link access, support for code resend, alternative Azure AD authentication option

---

## 11. Approval

**Business Owner:** Ritu Bahl  
**Technical Owner:** Gary Larson
**Date:** 12/17/2025

