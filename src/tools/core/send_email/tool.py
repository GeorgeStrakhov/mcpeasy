"""
Send Email tool implementation - requires per-client configuration
"""

from typing import Any, Dict, Optional
from src.tools.base import BaseTool, ToolResult
from src.services.email import EmailService


class SendEmailTool(BaseTool):
    """Email sending tool with per-client configuration"""
    
    def __init__(self):
        super().__init__()
        self.email_service = EmailService()
    
    @property
    def name(self) -> str:
        return "send_email"
    
    @property
    def description(self) -> str:
        return "Send an email with configured sender settings"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email address (single email or comma-separated list: 'user1@example.com,user2@example.com')"
                },
                "cc": {
                    "type": "string",
                    "description": "CC (carbon copy) email address (optional, single email or comma-separated list)"
                },
                "bcc": {
                    "type": "string", 
                    "description": "BCC (blind carbon copy) email address (optional, single email or comma-separated list)"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject"
                },
                "body": {
                    "type": "string",
                    "description": "Email body content (supports HTML)"
                },
                "attachments": {
                    "type": "array",
                    "description": "List of attachment URLs to download and attach (max 25MB each)",
                    "items": {
                        "type": "string",
                        "format": "uri",
                        "description": "URL of file to download and attach"
                    }
                }
            },
            "required": ["to", "subject", "body"]
        }
    
    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Configuration schema for per-client Postmark settings"""
        return {
            "type": "object",
            "properties": {
                "from_email": {
                    "type": "string",
                    "description": "Sender email address (must be verified in Postmark)",
                    "format": "email"
                },
                "from_name": {
                    "type": "string",
                    "description": "Sender display name (optional)"
                }
            },
            "required": ["from_email"]
        }
    
    async def execute(self, arguments: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> ToolResult:
        """Execute the send email tool using the email service"""
        if not config or not config.get("from_email"):
            return ToolResult.error("Email tool requires configuration with 'from_email' address")
        
        # Extract arguments and handle comma-separated emails
        def parse_emails(email_str):
            """Parse comma-separated email string into list"""
            if not email_str:
                return None
            if isinstance(email_str, str) and "," in email_str:
                return [email.strip() for email in email_str.split(",") if email.strip()]
            return email_str
        
        to_email = parse_emails(arguments.get("to"))
        cc_email = parse_emails(arguments.get("cc"))
        bcc_email = parse_emails(arguments.get("bcc"))
        subject = arguments.get("subject")
        body = arguments.get("body")
        attachment_urls = arguments.get("attachments", [])
        
        # Extract configuration
        from_email = config.get("from_email")
        from_name = config.get("from_name")
        
        # Send email using the service
        result = await self.email_service.send_email(
            to=to_email,
            subject=subject,
            body=body,
            from_email=from_email,
            from_name=from_name,
            cc=cc_email,
            bcc=bcc_email,
            attachment_urls=attachment_urls,
            is_html=True
        )
        
        # Return appropriate result
        if result["success"]:
            return ToolResult.text(result["message"])
        else:
            return ToolResult.error(result["error"])