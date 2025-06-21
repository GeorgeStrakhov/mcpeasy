# Custom Tool Template

This template provides a starting point for creating custom MCP tools.

## Quick Start

1. **Copy this template** to your custom tools repository:
   ```bash
   cp -r templates/custom_tool/ your-org-tools/tools/your_tool_name/
   ```

2. **Replace placeholders** in `tool.py`:
   - `TOOL_NAME` → your actual tool name (lowercase, no spaces)
   - `TOOL_NAMETool` → your tool class name (PascalCase)
   - Update `description` with what your tool does

3. **Implement the `execute` method** with your tool logic

4. **Update configuration schema** if your tool needs configuration

5. **Test your tool** before committing

## Tool Structure

```
your_tool_name/
├── __init__.py          # Package initialization
├── tool.py              # Main tool implementation
└── README.md            # This documentation
```

## Configuration

If your tool needs configuration (API keys, URLs, etc.), implement `get_config_schema()`:

```python
@classmethod
def get_config_schema(cls) -> Optional[Dict[str, Any]]:
    return {
        "type": "object",
        "properties": {
            "api_key": {"type": "string", "description": "Your API key"}
        },
        "required": ["api_key"]
    }
```

## Available Dependencies

These dependencies are already available in mcpeasy:
- `requests` - HTTP client
- `sqlalchemy` - Database ORM
- `pydantic` - Data validation
- `fastapi` - Web framework
- `asyncio` - Async programming
- `logging` - Logging utilities

## Adding New Dependencies

If you need additional dependencies:

1. **Add to this directory's `requirements.txt`**:
   ```
   stripe==5.4.0
   pandas>=1.5.0,<2.0.0
   ```

2. **Import with graceful fallback**:
   ```python
   try:
       import stripe
   except ImportError:
       stripe = None  # Handle missing dependency
   ```

3. **Use specific versions** to avoid conflicts

4. **Keep dependencies minimal** - prefer existing mcpeasy dependencies when possible

5. **Test the Docker build** to ensure dependencies install correctly

## Example Implementation

```python
async def execute(self, arguments: Dict[str, Any], config: Dict[str, Any] = None) -> ToolResult:
    try:
        # Extract arguments
        text = arguments.get("text", "")
        
        # Use configuration
        api_key = config.get("api_key") if config else None
        
        # Process with existing dependency
        import requests
        response = requests.post(
            "https://api.example.com/process",
            json={"text": text},
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        # Return structured JSON data (recommended)
        return ToolResult.json(response.json())
        
        # Or return plain text:
        # return ToolResult.text(f"Processed: {response.text}")
        
    except Exception as e:
        return ToolResult.error(f"Processing failed: {str(e)}")
```

## Testing

Test your tool locally before deployment:

```python
# In your development environment
from your_org.tools.your_tool.tool import YourToolTool

tool = YourToolTool()
result = await tool.execute({"text": "test"}, {"api_key": "test_key"})
print(result)
```

## Next Steps

1. Implement your tool logic
2. Add it to your deployment configuration
3. Test in development environment
4. Deploy and enable for specific clients via admin UI