# Echo Tool

A simple testing tool that echoes back any message provided to it.

## Purpose
This tool is primarily used for testing and debugging MCP integrations. It provides a reliable way to verify that the tool execution pipeline is working correctly.

## Parameters

| Parameter | Type   | Required | Description           |
|-----------|--------|----------|-----------------------|
| message   | string | Yes      | The message to echo back |

## Configuration
No configuration required.

## Example Usage

**Input:**
```json
{
  "message": "Hello, World!"
}
```

**Output:**
```
Echo: Hello, World!
```

## Implementation Details
- Simple synchronous execution
- No external dependencies
- Always returns successfully unless message parameter is missing