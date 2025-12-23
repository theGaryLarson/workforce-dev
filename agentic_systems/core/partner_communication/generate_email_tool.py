"""GeneratePartnerEmailTool per BRD FR-012.

Generates templated email explaining validation errors to partners.
Email contains NO PII - only error metadata per BRD Section 2.3.
Uses LLM to generate concise, professional error summaries.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..tools import ToolResult

# Optional LLM imports for professional summary generation
try:
    from langchain.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class GeneratePartnerEmailTool:
    """Generates templated email explaining validation errors per BRD FR-012.
    
    Takes error report path and violations list, generates email with:
    - LLM-generated concise, professional summary of errors (if LLM available)
    - Per-row error explanations (row number, field, reason)
    - Secure link URL (placeholder until approval)
    - Instructions for accessing corrected file
    
    Security Note: Email template does NOT include PII - only error metadata
    (row numbers, field names, error messages) per BRD Section 2.3.
    """
    
    name = "GeneratePartnerEmailTool"
    
    def __init__(self, llm: Optional[Any] = None):
        """Initialize tool with optional LLM for summary generation.
        
        Args:
            llm: Optional LangChain LLM instance. If None, will attempt to
                 initialize from environment variables (OPENAI_API_KEY or
                 ANTHROPIC_API_KEY). If LLM unavailable, falls back to raw output.
        """
        self.llm = llm
        if self.llm is None and LLM_AVAILABLE:
            self.llm = self._get_llm()
    
    def _get_llm(self) -> Optional[Any]:
        """Get LLM instance from environment variables.
        
        Returns:
            LangChain LLM instance or None if unavailable
        """
        if not LLM_AVAILABLE:
            return None
        
        import os
        
        # Check for OpenAI API key
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            model = os.getenv("OPENAI_MODEL", "gpt-4")
            return ChatOpenAI(model=model, temperature=0)
        
        # Check for Anthropic API key
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
            return ChatAnthropic(model=model, temperature=0)
        
        return None
    
    def _generate_error_summary_with_llm(
        self,
        violations: List[Dict[str, Any]],
        error_counts: Dict[str, int],
        total_errors: int,
        total_warnings: int,
        partner_name: str,
        quarter: str,
        year: str,
    ) -> Optional[str]:
        """Generate concise, professional error summary using LLM.
        
        Args:
            violations: List of violation dicts (not used, kept for API compatibility)
            error_counts: Dictionary of error counts by category
            total_errors: Total number of errors
            total_warnings: Total number of warnings
            partner_name: Partner identifier
            quarter: Quarter identifier
            year: Year
        
        Returns:
            LLM-generated summary string, or None if LLM unavailable or fails
        """
        if not self.llm:
            return None
        
        # Build minimal error summary (text format, similar to terminal output)
        # Only include categories with errors > 0 to minimize tokens
        error_summary_lines = []
        category_labels = {
            'required_field': 'Required Field Errors',
            'active_past_graduation': 'Active Past Graduation Errors',
            'zip_code_format': 'Zip Code Format Errors',
            'date_validation': 'Date Validation Errors',
            'address_validation': 'Address Validation Errors',
            'status_validation': 'Program Status Errors',
            'employment_validation': 'Employment Information Errors',
            'other': 'Other Errors'
        }
        
        for category, count in error_counts.items():
            if count > 0:
                label = category_labels.get(category, category.replace('_', ' ').title())
                error_summary_lines.append(f"- {label}: {count}")
        
        error_summary_text = "\n".join(error_summary_lines) if error_summary_lines else "No errors found"
        
        prompt = f"""You are a professional data quality analyst writing an email to a partner organization.

Context:
- Partner: {partner_name}
- Quarter: {quarter} {year}
- Total validation errors: {total_errors}
- Total warnings: {total_warnings}

Error Summary:
{error_summary_text}

Generate a concise, professional summary paragraph (2-4 sentences) that:
1. Acknowledges the data submission
2. Clearly states the number and types of validation errors found
3. Emphasizes the importance of data quality for accurate reporting
4. Maintains a supportive, collaborative tone

Do NOT include:
- Specific row numbers or PII
- Technical jargon
- Overly detailed error descriptions

Return only the summary paragraph text, no greeting or closing."""

        try:
            messages = [
                SystemMessage(
                    content="You are a professional data quality analyst who writes clear, "
                    "concise, and supportive communication to partner organizations."
                ),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            summary = response.content if hasattr(response, 'content') else str(response)
            return summary.strip()
        except Exception as e:
            # Fall back to raw output if LLM fails
            return None
    
    def __call__(
        self,
        error_report_path: Path,
        violations: List[Dict[str, Any]],
        partner_name: str,
        quarter: str,
        year: str = None,
        secure_link_url: str = None,
        access_code: str = None,
    ) -> ToolResult:
        """Generate templated email explaining validation errors.
        
        Args:
            error_report_path: Path to error report CSV
            violations: List of violations for context
            partner_name: Partner identifier (from CLI --partner)
            quarter: Quarter identifier (e.g., "Q1")
            year: Year (defaults to current year)
            secure_link_url: URL for accessing error report (placeholder until approval)
            access_code: Access code for secure link (if code-based)
        
        Returns:
            ToolResult with email_content and email_html in data
        """
        if year is None:
            year = str(datetime.now().year)
        
        # Count errors by type
        error_counts = {
            'required_field': 0,
            'active_past_graduation': 0,
            'zip_code_format': 0,
            'date_validation': 0,
            'address_validation': 0,
            'status_validation': 0,
            'employment_validation': 0,
            'other': 0
        }
        
        for v in violations:
            message_lower = v.get('message', '').lower()
            if 'required' in message_lower or 'missing' in message_lower:
                error_counts['required_field'] += 1
            elif 'active past graduation' in message_lower or 'graduation' in message_lower:
                error_counts['active_past_graduation'] += 1
            elif 'zip' in message_lower or 'postal' in message_lower:
                error_counts['zip_code_format'] += 1
            elif 'date' in message_lower and ('invalid' in message_lower or 'format' in message_lower or 'earlier' in message_lower):
                error_counts['date_validation'] += 1
            elif 'address' in message_lower:
                error_counts['address_validation'] += 1
            elif 'status' in message_lower or 'program status' in message_lower:
                error_counts['status_validation'] += 1
            elif 'employment' in message_lower:
                error_counts['employment_validation'] += 1
            else:
                error_counts['other'] += 1
        
        total_errors = len([v for v in violations if v.get('severity', 'Error') == 'Error'])
        total_warnings = len([v for v in violations if v.get('severity') == 'Warning'])
        
        # Generate LLM summary (or fall back to raw output)
        llm_summary = self._generate_error_summary_with_llm(
            violations=violations,
            error_counts=error_counts,
            total_errors=total_errors,
            total_warnings=total_warnings,
            partner_name=partner_name,
            quarter=quarter,
            year=year,
        )
        
        # Generate email text
        email_lines = [
            f"Subject: Action Required: Data Validation Errors - {partner_name} {quarter} {year}",
            "",
            f"Dear {partner_name},",
            "",
        ]
        
        # Use LLM summary if available, otherwise use raw error counts
        if llm_summary:
            email_lines.append(llm_summary)
            email_lines.append("")
        else:
            # Fallback to raw output
            email_lines.append(
                f"We have identified {total_errors} validation error(s) and {total_warnings} warning(s) "
                f"in your quarterly data submission for {quarter} {year}."
            )
            email_lines.append("")
            email_lines.append("Error Summary:")
            if error_counts['required_field'] > 0:
                email_lines.append(f"- Required Field Errors: {error_counts['required_field']}")
            if error_counts['active_past_graduation'] > 0:
                email_lines.append(f"- Active Past Graduation Errors: {error_counts['active_past_graduation']}")
            if error_counts['zip_code_format'] > 0:
                email_lines.append(f"- Zip Code Format Errors: {error_counts['zip_code_format']}")
            if error_counts['date_validation'] > 0:
                email_lines.append(f"- Date Validation Errors: {error_counts['date_validation']}")
            if error_counts['address_validation'] > 0:
                email_lines.append(f"- Address Validation Errors: {error_counts['address_validation']}")
            if error_counts['status_validation'] > 0:
                email_lines.append(f"- Program Status Errors: {error_counts['status_validation']}")
            if error_counts['employment_validation'] > 0:
                email_lines.append(f"- Employment Information Errors: {error_counts['employment_validation']}")
            if error_counts['other'] > 0:
                email_lines.append(f"- Other Errors: {error_counts['other']}")
            email_lines.append("")
        
        email_lines.extend([
            "",
            "To review and correct these errors:",
            "1. Access the error report using this secure link:",
        ])
        
        if secure_link_url:
            email_lines.append(f"   {secure_link_url}")
        else:
            email_lines.append("   [Secure link will be provided after staff approval]")
        
        if access_code:
            email_lines.append(f"2. Access code: {access_code}")
        else:
            email_lines.append("2. Access code: [Will be provided after staff approval]")
        
        email_lines.extend([
            "3. Review the error details in the Excel file (errors are highlighted with comments)",
            "4. Correct the data in your source file",
            "5. Upload the corrected file to: [Upload location]",
            "",
            "",
            "If you have any questions, please contact the CFA Data Processing Team.",
            "",
            "Thank you,",
            "CFA Data Processing Team"
        ])
        
        email_text = "\n".join(email_lines)
        
        # Generate HTML version
        email_html = f"""<html>
<body>
<p>Dear {partner_name},</p>
"""
        
        if llm_summary:
            email_html += f"<p>{llm_summary.replace(chr(10), '<br>')}</p>"
        else:
            email_html += f"<p>We have identified {total_errors} validation error(s) and {total_warnings} warning(s) in your quarterly data submission for {quarter} {year}.</p>"
            email_html += "<h3>Error Summary:</h3><ul>"
            if error_counts['required_field'] > 0:
                email_html += f"<li>Required Field Errors: {error_counts['required_field']}</li>"
            if error_counts['active_past_graduation'] > 0:
                email_html += f"<li>Active Past Graduation Errors: {error_counts['active_past_graduation']}</li>"
            if error_counts['zip_code_format'] > 0:
                email_html += f"<li>Zip Code Format Errors: {error_counts['zip_code_format']}</li>"
            if error_counts['date_validation'] > 0:
                email_html += f"<li>Date Validation Errors: {error_counts['date_validation']}</li>"
            if error_counts['address_validation'] > 0:
                email_html += f"<li>Address Validation Errors: {error_counts['address_validation']}</li>"
            if error_counts['status_validation'] > 0:
                email_html += f"<li>Program Status Errors: {error_counts['status_validation']}</li>"
            if error_counts['employment_validation'] > 0:
                email_html += f"<li>Employment Information Errors: {error_counts['employment_validation']}</li>"
            if error_counts['other'] > 0:
                email_html += f"<li>Other Errors: {error_counts['other']}</li>"
            email_html += "</ul>"
        
        email_html += f"""</ul>
<p>To review and correct these errors:</p>
<ol>
"""
        
        if secure_link_url:
            email_html += f"<li>Access the error report using this secure link: <a href=\"{secure_link_url}\">{secure_link_url}</a></li>"
        else:
            email_html += "<li>Access the error report using this secure link: [Secure link will be provided after staff approval]</li>"
        
        if access_code:
            email_html += f"<li>Access code: {access_code}</li>"
        else:
            email_html += "<li>Access code: [Will be provided after staff approval]</li>"
        
        email_html += """<li>Review the error details in the Excel file (errors are highlighted with comments)</li>
<li>Correct the data in your source file</li>
<li>Upload the corrected file to: [Upload location]</li>
</ol>
<p>If you have any questions, please contact the CFA Data Processing Team.</p>
<p>Thank you,<br>CFA Data Processing Team</p>
</body>
</html>"""
        
        return ToolResult(
            ok=True,
            summary=f"Generated email template with {total_errors} errors and {total_warnings} warnings" + 
                   (" (LLM summary)" if llm_summary else " (raw summary)"),
            data={
                "email_content": email_text,
                "email_html": email_html,
                "error_count": total_errors,
                "warning_count": total_warnings,
                "llm_summary_used": llm_summary is not None
            },
            warnings=[],
            blockers=[]
        )

