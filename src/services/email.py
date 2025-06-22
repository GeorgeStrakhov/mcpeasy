"""
Email service with Postmark integration - reusable across the application
"""

import os
from typing import Any, Dict, Optional, List, Union
from pathlib import Path
import aiohttp
from postmarker.core import PostmarkClient


class EmailService:
    """Email service with Postmark integration"""
    
    def __init__(self):
        self.postmark_token = os.getenv("POSTMARK_API_TOKEN")
        self.is_development = os.getenv("DEVELOPMENT", "false").lower() == "true"
    
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
    
    def _format_email_list(self, emails: Union[str, List[str]]) -> str:
        """Format email list for display"""
        if isinstance(emails, list):
            return ", ".join(emails)
        return emails
    
    def _log_development_email(self, email_data: Dict[str, Any], attachment_urls: List[str] = None) -> str:
        """Log email to console in development mode"""
        print("\n" + "="*60)
        print("📧 EMAIL LOGGED (Development Mode)")
        print("="*60)
        print(f"From: {email_data.get('From')}")
        print(f"To: {self._format_email_list(email_data.get('To'))}")
        
        if email_data.get('Cc'):
            print(f"CC: {self._format_email_list(email_data.get('Cc'))}")
        if email_data.get('Bcc'):
            print(f"BCC: {self._format_email_list(email_data.get('Bcc'))}")
        
        print(f"Subject: {email_data.get('Subject')}")
        print(f"Body: {email_data.get('HtmlBody', email_data.get('TextBody', ''))}")
        
        if attachment_urls:
            print(f"Attachments ({len(attachment_urls)}):")
            for i, url in enumerate(attachment_urls, 1):
                print(f"  {i}. {url}")
        
        print("="*60)
        
        # Return formatted result
        result_text = f"""Email logged to console (Development Mode)
From: {email_data.get('From')}
To: {self._format_email_list(email_data.get('To'))}"""
        
        if email_data.get('Cc'):
            result_text += f"\nCC: {self._format_email_list(email_data.get('Cc'))}"
        if email_data.get('Bcc'):
            result_text += f"\nBCC: {self._format_email_list(email_data.get('Bcc'))}"
        
        result_text += f"\nSubject: {email_data.get('Subject')}"
        if attachment_urls:
            result_text += f"\nAttachments: {len(attachment_urls)} URL(s)"
        
        return result_text
    
    async def send_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: str,
        from_email: str,
        from_name: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        attachment_urls: Optional[List[str]] = None,
        is_html: bool = True
    ) -> Dict[str, Any]:
        """
        Send an email via Postmark
        
        Args:
            to: Recipient email(s)
            subject: Email subject
            body: Email body content
            from_email: Sender email address
            from_name: Sender display name (optional)
            cc: CC email(s) (optional)
            bcc: BCC email(s) (optional)
            attachment_urls: List of URLs to download and attach (optional)
            is_html: Whether body contains HTML (default: True)
        
        Returns:
            Dict with success status and message/error details
        """
        
        # Prepare email data
        email_data = {
            "From": f"{from_name} <{from_email}>" if from_name else from_email,
            "To": to,
            "Subject": subject,
        }
        
        # Set body type
        if is_html:
            email_data["HtmlBody"] = body
        else:
            email_data["TextBody"] = body
        
        # Add optional recipients
        if cc:
            email_data["Cc"] = cc
        if bcc:
            email_data["Bcc"] = bcc
        
        # Handle development mode
        if self.is_development:
            log_message = self._log_development_email(email_data, attachment_urls or [])
            return {
                "success": True,
                "message": log_message,
                "message_id": "dev-mode-no-id"
            }
        
        # Production mode: validate token
        if not self.postmark_token:
            return {
                "success": False,
                "error": "POSTMARK_API_TOKEN environment variable is required"
            }
        
        try:
            # Initialize Postmark client
            postmark = PostmarkClient(server_token=self.postmark_token)
            
            # Download and attach files if provided
            attachments = []
            if attachment_urls:
                for url in attachment_urls:
                    attachment = await self._download_attachment(url)
                    if attachment:
                        attachments.append(attachment)
                    else:
                        return {
                            "success": False,
                            "error": f"Failed to download attachment from {url} (check URL and size < 25MB)"
                        }
                
                if attachments:
                    email_data["Attachments"] = attachments
            
            # Send email
            response = postmark.emails.send(**email_data)
            
            # Format success message
            result_message = f"""Email sent successfully via Postmark!
From: {email_data['From']}
To: {self._format_email_list(to)}"""
            
            if cc:
                result_message += f"\nCC: {self._format_email_list(cc)}"
            if bcc:
                result_message += f"\nBCC: {self._format_email_list(bcc)}"
            
            result_message += f"\nSubject: {subject}\nMessage ID: {response.get('MessageID', 'N/A')}"
            
            if attachments:
                result_message += f"\nAttachments: {len(attachments)} file(s)"
            
            return {
                "success": True,
                "message": result_message,
                "message_id": response.get('MessageID'),
                "response": response
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to send email: {str(e)}"
            }