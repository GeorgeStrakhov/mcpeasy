# Website Screenshot Tool

A specialized tool for taking high-quality screenshots of websites using the Firecrawl service.

## Features

- **High-quality screenshots**: Capture full websites as PNG images
- **Browser actions**: Interact with pages before taking screenshots
- **Smart automation**: Click buttons, fill forms, scroll, and wait for content
- **Base64 output**: Returns screenshot as file reference for easy handling

## Configuration

Per-client configuration:

```json
{
  "api_key": "your-firecrawl-api-key"
}
```

## Usage Examples

### Basic Screenshot

```json
{
  "url": "https://example.com"
}
```

### Screenshot with Interactions

```json
{
  "url": "https://example.com/app",
  "actions": [
    {
      "type": "wait",
      "milliseconds": 3000
    },
    {
      "type": "click",
      "selector": "#menu-button"
    },
    {
      "type": "wait", 
      "milliseconds": 1000
    }
  ]
}
```

### Screenshot After Form Interaction

```json
{
  "url": "https://search.example.com",
  "actions": [
    {
      "type": "click",
      "selector": "#search-input"
    },
    {
      "type": "write",
      "selector": "#search-input",
      "text": "firecrawl screenshot"
    },
    {
      "type": "press",
      "key": "Enter"
    },
    {
      "type": "wait",
      "milliseconds": 3000
    }
  ]
}
```

### Screenshot with Scroll

```json
{
  "url": "https://longpage.example.com",
  "actions": [
    {
      "type": "scroll"
    },
    {
      "type": "wait",
      "milliseconds": 2000
    }
  ]
}
```

## Available Actions

- **wait**: Pause for specified milliseconds
- **click**: Click on an element (requires selector)
- **write**: Type text into an element (requires selector and text)
- **press**: Press a keyboard key (Enter, Space, etc.)
- **scroll**: Scroll the page

## Response Format

The tool returns a file reference:

```json
{
  "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "mime_type": "image/png", 
  "description": "Screenshot of https://example.com"
}
```

## Use Cases

1. **Visual testing**: Capture page states for comparison
2. **Documentation**: Generate visual documentation of web interfaces
3. **Monitoring**: Take periodic screenshots to monitor changes
4. **Bug reporting**: Capture visual evidence of issues
5. **Content creation**: Generate images for presentations or reports
6. **Responsive design**: Capture how pages look at different stages

## Best Practices

1. **Use wait actions** for dynamic content that loads after page load
2. **Test action sequences** with simple interactions first
3. **Keep action chains short** to avoid timeouts
4. **Use specific selectors** for reliable element targeting
5. **Add reasonable delays** between actions for stability

## Error Handling

The tool handles common issues:
- Invalid URLs or network errors
- Missing or invalid API keys
- Failed browser actions
- Screenshot generation failures
- Service timeouts

## Environment Variables

The tool can use the `FIRECRAWL_API_KEY` environment variable as a fallback if no API key is configured for the client.