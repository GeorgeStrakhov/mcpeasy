"""
Send Email tool implementation using Postmark - requires per-client configuration
"""

import os
from typing import Any, Dict, Optional
from pathlib import Path
import aiohttp
from postmarker.core import PostmarkClient
from ..base import BaseTool, ToolResult


class SendEmailTool(BaseTool):
    """Email sending tool with per-client configuration"""
    
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
                    "oneOf": [
                        {
                            "type": "string",
                            "description": "Single recipient email address",
                            "format": "email"
                        },
                        {
                            "type": "array",
                            "description": "Multiple recipient email addresses",
                            "items": {
                                "type": "string",
                                "format": "email"
                            }
                        }
                    ],
                    "description": "Recipient email address(es) - can be a single string or array of strings"
                },
                "cc": {
                    "oneOf": [
                        {
                            "type": "string",
                            "description": "Single CC email address",
                            "format": "email"
                        },
                        {
                            "type": "array",
                            "description": "Multiple CC email addresses",
                            "items": {
                                "type": "string",
                                "format": "email"
                            }
                        }
                    ],
                    "description": "CC (carbon copy) email address(es) - can be a single string or array of strings"
                },
                "bcc": {
                    "oneOf": [
                        {
                            "type": "string",
                            "description": "Single BCC email address",
                            "format": "email"
                        },
                        {
                            "type": "array",
                            "description": "Multiple BCC email addresses",
                            "items": {
                                "type": "string",
                                "format": "email"
                            }
                        }
                    ],
                    "description": "BCC (blind carbon copy) email address(es) - can be a single string or array of strings"
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
    
    async def _download_attachment(self, url: str) -> Optional[Dict[str, Any]]:
        """Download attachment from URL and return attachment data"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    
                    # Check content length (25MB limit)
                    content_length = response.headers.get("Content-Length")
                    if content_length and int(content_length) > 25 * 1024 * 1024:
                        return None
                    
                    content = await response.read()
                    
                    # Double check size after download
                    if len(content) > 25 * 1024 * 1024:
                        return None
                    
                    # Get filename from URL or content-disposition
                    filename = None
                    if "Content-Disposition" in response.headers:
                        cd = response.headers["Content-Disposition"]
                        if "filename=" in cd:
                            filename = cd.split("filename=")[1].strip('"')
                    
                    if not filename:
                        filename = Path(url).name or "attachment"
                    
                    return {
                        "Name": filename,
                        "Content": content,
                        "ContentType": response.headers.get("Content-Type", "application/octet-stream")
                    }
        except Exception:
            return None
    
    async def execute(self, arguments: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> ToolResult:
        """Execute the send email tool using Postmark"""
        if not config or not config.get("from_email"):
            return ToolResult.error("Email tool requires configuration with 'from_email' address")
        
        # Extract arguments
        to_email = arguments.get("to")
        cc_email = arguments.get("cc")
        bcc_email = arguments.get("bcc")
        subject = arguments.get("subject")
        body = arguments.get("body")
        attachment_urls = arguments.get("attachments", [])
        
        # For display purposes, convert lists to comma-separated strings
        def format_for_display(emails):
            if isinstance(emails, list):
                return ", ".join(emails)
            return emails
        
        to_display = format_for_display(to_email)
        cc_display = format_for_display(cc_email) if cc_email else None
        bcc_display = format_for_display(bcc_email) if bcc_email else None
        
        # Extract configuration
        from_email = config.get("from_email")
        from_name = config.get("from_name")
        
        # Check if we're in development mode
        is_development = os.getenv("DEVELOPMENT", "false").lower() == "true"
        
        if is_development:
            # Development mode: log email instead of sending
            print("\n" + "="*60)
            print("📧 EMAIL LOGGED (Development Mode)")
            print("="*60)
            print(f"From: {f'{from_name} <{from_email}>' if from_name else from_email}")
            print(f"To: {to_display}")
            if cc_display:
                print(f"CC: {cc_display}")
            if bcc_display:
                print(f"BCC: {bcc_display}")
            print(f"Subject: {subject}")
            print(f"Body: {body}")
            
            if attachment_urls:
                print(f"Attachments ({len(attachment_urls)}):")
                for i, url in enumerate(attachment_urls, 1):
                    print(f"  {i}. {url}")
            
            print("="*60)
            
            result_text = f"""Email logged to console (Development Mode)
From: {f'{from_name} <{from_email}>' if from_name else from_email}
To: {to_display}"""
            if cc_display:
                result_text += f"\nCC: {cc_display}"
            if bcc_display:
                result_text += f"\nBCC: {bcc_display}"
            result_text += f"\nSubject: {subject}\nAttachments: {len(attachment_urls)} URL(s)"
            return ToolResult.text(result_text)
        
        # Production mode: send actual email
        postmark_token = os.getenv("POSTMARK_API_TOKEN")
        if not postmark_token:
            return ToolResult.error("POSTMARK_API_TOKEN environment variable is required")
        
        try:
            # Initialize Postmark client
            postmark = PostmarkClient(server_token=postmark_token)
            
            # Prepare email data - Postmarker accepts both lists and comma-separated strings
            email_data = {
                "From": f"{from_name} <{from_email}>" if from_name else from_email,
                "To": to_email,  # Can be string or list
                "Subject": subject,
                "HtmlBody": body
            }
            
            # Add CC and BCC if provided
            if cc_email:
                email_data["Cc"] = cc_email  # Can be string or list
            if bcc_email:
                email_data["Bcc"] = bcc_email  # Can be string or list
            
            # Download and attach files if provided
            attachments = []
            if attachment_urls:
                for url in attachment_urls:
                    attachment = await self._download_attachment(url)
                    if attachment:
                        attachments.append(attachment)
                    else:
                        return ToolResult.error(f"Failed to download attachment from {url} (check URL and size < 25MB)")
                
                if attachments:
                    email_data["Attachments"] = attachments
            
            # Send email
            response = postmark.emails.send(**email_data)
            
            # Format success message
            result_message = f"""Email sent successfully via Postmark!
From: {email_data['From']}
To: {to_display}"""
            if cc_display:
                result_message += f"\nCC: {cc_display}"
            if bcc_display:
                result_message += f"\nBCC: {bcc_display}"
            result_message += f"\nSubject: {subject}\nMessage ID: {response.get('MessageID', 'N/A')}"
            
            if attachments:
                result_message += f"\nAttachments: {len(attachments)} file(s)"
            
            return ToolResult.text(result_message)
            
        except Exception as e:
            return ToolResult.error(f"Failed to send email: {str(e)}")