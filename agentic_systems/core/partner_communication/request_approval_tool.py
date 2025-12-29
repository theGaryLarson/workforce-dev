"""RequestStaffApprovalTool per BRD FR-012.

Interactive CLI prompt for staff review and approval of partner emails.
Contains explicit production comments marking where Teams Adaptive Card integration would occur.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..tools import ToolResult


class RequestStaffApprovalTool:
    """Requests CFA staff approval before sending email to partner per BRD FR-012.
    
    For POC: Interactive CLI prompt asking staff to review and approve.
    Displays email preview and error summary.
    Waits for staff input (approve/reject).
    
    Production comments mark where Teams Adaptive Card integration would occur per BRD FR-012.
    """
    
    name = "RequestStaffApprovalTool"
    
    def __call__(
        self,
        email_content: str,
        error_report_path: Path,
        internal_report_url: Optional[str],
        error_summary: Dict[str, Any],
        partner_name: str,
        quarter: str,
        year: Optional[str] = None,
        aggregates: Optional[Dict[str, Any]] = None,
        demo_mode: bool = True,
        approval_recipients: Optional[List[str]] = None,
    ) -> ToolResult:
        """Request staff approval for sending email to partner.
        
        Args:
            email_content: Generated email content (text version)
            error_report_path: Path to error report CSV
            internal_report_url: URL to internal SharePoint/Dataverse review worksheet
                                 (simulated or real, used for Teams Adaptive Card link)
            error_summary: Summary of error counts by type
            partner_name: Partner identifier
            quarter: Quarter identifier
            demo_mode: When True, use interactive CLI prompt. When False, this tool
                       is expected to be triggered via Teams Adaptive Card workflow.
            approval_recipients: Optional list of recipients/user groups for Teams
                                 Adaptive Card in production.
        
        Returns:
            ToolResult with approval_status, staff_comments, and approval_timestamp in data
        """
        # PRODUCTION: If demo_mode is False, this tool is expected to be wired into
        # a Teams Adaptive Card workflow via webhooks (see PRD-TRD Section 4.3 and
        # BRD FR-012). In that mode, the approval decision would arrive asynchronously
        # and this method would likely not be called directly from the CLI.
        #
        # For the POC, we keep the interactive CLI behavior to simulate the HITL step.
        if not demo_mode:
            # Placeholder behavior: fall back to CLI prompt until Teams integration
            # is implemented. Inline comment explicitly marks where production code
            # should go.
            print("\n[WARNING] RequestStaffApprovalTool called with demo_mode=False,")
            print("but Teams Adaptive Card integration is not yet implemented.")

        # Display approval request to console (demo simulation of Teams card)
        print("\n" + "=" * 80)
        print("=== STAFF APPROVAL REQUIRED ===")
        print("=" * 80)
        print(f"\nPartner: {partner_name}")
        print(f"Quarter: {quarter}")
        print(f"\nError Report (local path): {error_report_path}")
        if internal_report_url:
            # Show simulated/real SharePoint URL so staff can open the internal worksheet
            print(f"Internal review worksheet URL (SharePoint / simulated): {internal_report_url}")
        
        # Display error summary
        print("\nError Summary:")
        if 'required_field' in error_summary:
            print(f"  - Required Field Errors: {error_summary.get('required_field', 0)}")
        if 'active_past_graduation' in error_summary:
            print(f"  - Active Past Graduation Errors: {error_summary.get('active_past_graduation', 0)}")
        if 'zip_code_format' in error_summary:
            print(f"  - Zip Code Format Errors: {error_summary.get('zip_code_format', 0)}")
        if 'date_validation' in error_summary:
            print(f"  - Date Validation Errors: {error_summary.get('date_validation', 0)}")
        if 'address_validation' in error_summary:
            print(f"  - Address Validation Errors: {error_summary.get('address_validation', 0)}")
        if 'status_validation' in error_summary:
            print(f"  - Program Status Errors: {error_summary.get('status_validation', 0)}")
        if 'employment_validation' in error_summary:
            print(f"  - Employment Information Errors: {error_summary.get('employment_validation', 0)}")
        if 'other' in error_summary:
            print(f"  - Other Errors: {error_summary.get('other', 0)}")
        
        total_errors = error_summary.get('total_errors', 0)
        total_warnings = error_summary.get('total_warnings', 0)
        print(f"\n  Total Errors: {total_errors}")
        print(f"  Total Warnings: {total_warnings}")
        
        # Display WSAC Aggregates Summary if available per BRD FR-004
        if aggregates:
            print("\n" + "-" * 80)
            print("WSAC Aggregates Summary:")
            print("-" * 80)
            print(f"  Total Participants: {aggregates.get('total_participants', 0)}")
            print(f"  Total Enrollments: {aggregates.get('total_enrollments', 0)}")
            print(f"  Total Employment Placements: {aggregates.get('total_employment_placements', 0)}")
            
            status_breakdown = aggregates.get('status_breakdown', {})
            if status_breakdown:
                print(f"\n  Status Breakdown:")
                print(f"    Active: {status_breakdown.get('active', 0)}")
                print(f"    Graduated: {status_breakdown.get('graduated', 0)}")
                print(f"    Withdrawn: {status_breakdown.get('withdrawn', 0)}")
            
            wraparound = aggregates.get('wraparound_services', {})
            usage_counts = wraparound.get('usage_counts', {})
            if usage_counts and any(usage_counts.values()):
                print(f"\n  Wraparound Services Usage:")
                from ...clients.cfa.rules import WRAPAROUND_SERVICE_NAMES
                for service_type, count in usage_counts.items():
                    if count > 0:
                        service_name = WRAPAROUND_SERVICE_NAMES.get(service_type, service_type.replace('_', ' ').title())
                        print(f"    {service_name}: {count} participants")
            
            print("-" * 80)
        
        # Display email preview
        print("\n" + "-" * 80)
        print("Email Preview:")
        print("-" * 80)
        # Show first 20 lines of email for preview
        email_preview_lines = email_content.split('\n')[:20]
        for line in email_preview_lines:
            print(line)
        if len(email_content.split('\n')) > 20:
            print("... (email continues)")
        print("-" * 80)
        
        # PRODUCTION: Send Teams Adaptive Card approval request here instead of CLI:
        # - Card includes validation summary and internal_report_url link
        # - Approve/Reject buttons send action to /api/webhooks/teams-approval
        # - Approval decision stored in PostgreSQL approval_requests table
        # - This method would then read from that table or be bypassed entirely
        #
        # For POC, we simulate the HITL decision via interactive CLI prompt.
        print("\n" + "=" * 80)
        while True:
            response = input("Approve sending this email to partner? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                approval_status = 'approved'
                staff_comments = input("Enter any comments (optional, press Enter to skip): ").strip()
                break
            elif response in ['n', 'no']:
                approval_status = 'rejected'
                staff_comments = input("Enter rejection reason (required): ").strip()
                if not staff_comments:
                    print("Rejection reason is required. Please provide a reason.")
                    continue
                break
            else:
                print("Please enter 'y' for yes or 'n' for no.")
        
        approval_timestamp = datetime.now().isoformat()
        
        print(f"\nApproval Status: {approval_status.upper()}")
        if staff_comments:
            print(f"Staff Comments: {staff_comments}")
        print("=" * 80 + "\n")
        
        return ToolResult(
            ok=(approval_status == 'approved'),
            summary=f"Staff approval: {approval_status}",
            data={
                "approval_status": approval_status,
                "staff_comments": staff_comments if staff_comments else None,
                "approval_timestamp": approval_timestamp
            },
            warnings=[],
            blockers=[] if approval_status == 'approved' else [f"Email sending rejected by staff: {staff_comments}"]
        )

