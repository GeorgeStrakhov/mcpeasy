# Send Email Tool

Sends emails using Postmark API with support for HTML content and file attachments.

## Purpose
Enable email sending capabilities with professional features including HTML formatting and attachment support.

## Parameters

| Parameter    | Type                        | Required | Description                                      |
|--------------|-----------------------------|-----------|-------------------------------------------------|
| to           | string or array of strings  | Yes      | Recipient email address(es)                      |
| cc           | string or array of strings  | No       | CC (carbon copy) recipient email address(es)     |
| bcc          | string or array of strings  | No       | BCC (blind carbon copy) recipient email address(es) |
| subject      | string                      | Yes      | Email subject line                               |
| body         | string                      | Yes      | Email body content (supports HTML)               |
| attachments  | array of strings            | No       | List of URLs to download and attach (max 25MB each) |

## Configuration

**Required configuration:**
```json
{
  "from_email": "sender@example.com",  // Required: Must be verified in Postmark
  "from_name": "Sender Name"           // Optional: Display name for sender
}
```

## Environment Variables

| Variable           | Required | Description                               |
|-------------------|----------|-------------------------------------------|
| POSTMARK_API_TOKEN| Yes*     | Postmark API token for sending emails     |
| DEVELOPMENT       | No       | Set to "true" to enable development mode  |

*Not required in development mode

## Features

- **HTML Support**: Send rich HTML emails
- **Multiple Recipients**: Support for multiple To, CC, and BCC recipients
- **Attachments**: Download and attach files from URLs (up to 25MB each)
- **Development Mode**: Log emails to console instead of sending
- **Content Type Detection**: Automatic MIME type detection for attachments
- **Error Handling**: Comprehensive error messages for debugging

## Example Usage

**Basic Email:**
```json
{
  "to": "recipient@example.com",
  "subject": "Hello from MCP",
  "body": "This is a test email"
}
```

**Email with Multiple Recipients:**
```json
{
  "to": ["recipient1@example.com", "recipient2@example.com"],
  "cc": "manager@example.com",
  "subject": "Team Update",
  "body": "<h1>Weekly Update</h1><p>Here's our progress this week.</p>"
}
```

**HTML Email with Attachment and BCC:**
```json
{
  "to": "recipient@example.com",
  "bcc": ["archive@example.com", "backup@example.com"],
  "subject": "Report Ready",
  "body": "<h1>Your Report</h1><p>Please find the report attached.</p>",
  "attachments": ["https://example.com/report.pdf"]
}
```

## Development Mode

When `DEVELOPMENT=true` is set, emails are logged to console instead of being sent:

```
============================================================
📧 EMAIL LOGGED (Development Mode)
============================================================
From: Test Sender <test@example.com>
To: recipient@example.com
CC: manager@example.com
BCC: archive@example.com
Subject: Test Email
Body: This is a test
Attachments (0):
============================================================
```

## Error Cases

- Missing Postmark API token (production mode)
- Invalid recipient email format
- Attachment download failures
- Attachment size exceeds 25MB limit
- Postmark API errors

## Security Notes

- Verify sender email addresses in Postmark before use
- Be cautious with attachment URLs from untrusted sources
- HTML content is not sanitized - ensure content is safe