# Web Scraping Tool

A powerful web scraping tool powered by the Firecrawl service, designed for extracting clean, structured data from web pages.

## Features

- **Multiple Output Formats**: Get data as markdown, HTML, raw HTML, links, screenshots, or structured JSON
- **Smart Content Extraction**: Focus on main content, exclude navigation and footers
- **Advanced Filtering**: Include or exclude specific HTML tags, classes, and IDs
- **JavaScript Support**: Wait for dynamic content to load before scraping
- **Browser Actions**: Perform clicks, scrolls, and form submissions before scraping
- **Structured Data Extraction**: Use AI to extract specific data using schemas and prompts
- **PDF Support**: Parse PDFs as markdown or get base64-encoded content
- **Domain Control**: Configure allowed/blocked domains per client

## Configuration

Per-client configuration options:

```json
{
  "api_key": "your-firecrawl-api-key",
  "allowed_domains": ["example.com", "docs.example.com"],
  "blocked_domains": ["private.example.com"],
  "max_timeout": 30000
}
```

## Usage Examples

### Basic Page Scraping

```json
{
  "url": "https://example.com/article"
}
```

### Multiple Formats

```json
{
  "url": "https://example.com",
  "formats": ["markdown", "links", "screenshot"],
  "only_main_content": true
}
```

### Advanced Content Filtering

```json
{
  "url": "https://news.example.com/article",
  "include_tags": ["article", ".content", "#main-story"],
  "exclude_tags": ["nav", ".sidebar", ".comments"],
  "wait_for": 2000
}
```

### Browser Actions

```json
{
  "url": "https://example.com/search",
  "actions": [
    {
      "type": "click",
      "selector": "#search-button"
    },
    {
      "type": "wait",
      "milliseconds": 2000
    },
    {
      "type": "write",
      "selector": "#search-input",
      "text": "firecrawl"
    },
    {
      "type": "press",
      "key": "Enter"
    }
  ]
}
```

### Structured Data Extraction

```json
{
  "url": "https://store.example.com/product/123",
  "extraction": {
    "schema": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "price": {"type": "number"},
        "description": {"type": "string"},
        "features": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    },
    "prompt": "Extract product information from this page"
  }
}
```

### Custom Headers and PDF Handling

```json
{
  "url": "https://api.example.com/docs.pdf",
  "headers": {
    "User-Agent": "MyBot/1.0",
    "Authorization": "Bearer token123"
  },
  "parse_pdf": true,
  "timeout": 45000
}
```

## Available Formats

- **markdown**: Clean markdown content (default)
- **html**: Cleaned HTML content  
- **rawHtml**: Original HTML without processing
- **links**: All links found on the page
- **screenshot**: Base64-encoded screenshot
- **json**: Structured data (when using extraction)

## Browser Actions

Supported action types:
- **wait**: Wait for specified milliseconds
- **screenshot**: Take a screenshot
- **click**: Click on an element (requires selector)
- **write**: Type text into an element (requires selector and text)
- **press**: Press a keyboard key
- **scroll**: Scroll the page

## Response Format

```json
{
  "success": true,
  "url": "https://example.com/article",
  "markdown": "# Article Title\n\nContent...",
  "metadata": {
    "title": "Article Title",
    "description": "Article description",
    "language": "en"
  },
  "links": ["https://example.com/related"],
  "screenshot": "base64-encoded-image",
  "extract": {
    "name": "Product Name",
    "price": 29.99
  }
}
```

## Error Handling

The tool handles various error cases:
- Invalid or missing API key
- Domain restrictions (allowed/blocked lists)
- Timeout limits exceeded
- Network errors or invalid URLs
- Malformed action sequences
- Invalid extraction schemas

## Best Practices

1. **Use `only_main_content: true`** for cleaner results
2. **Set appropriate timeouts** for slow-loading pages
3. **Filter content** using include/exclude tags for better results
4. **Test extraction schemas** with simple examples first
5. **Configure domain restrictions** for security
6. **Use actions sparingly** - they increase processing time
7. **Check format compatibility** - not all formats work together

## Environment Variables

As a fallback, the tool can use the `FIRECRAWL_API_KEY` environment variable if no API key is configured for the client.