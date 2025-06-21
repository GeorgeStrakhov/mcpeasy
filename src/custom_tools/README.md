# Custom Tools Directory

This directory contains git submodules for custom MCP tools developed by organizations.

## Structure

Each organization should add their custom tools as a git submodule:

```
src/custom_tools/
├── .gitkeep
├── README.md (this file)
└── {org-name}/          # Git submodule per organization
    ├── tools/
    │   ├── tool_name_1/
    │   │   ├── __init__.py
    │   │   ├── tool.py      # Implements BaseTool
    │   │   └── README.md
    │   └── tool_name_2/
    │       ├── __init__.py
    │       └── tool.py
    ├── requirements.txt     # Additional dependencies (optional)
    └── README.md
```

## Adding Custom Tools

1. **Create your custom tools repository** in your organization's GitHub/GitLab
2. **Add as submodule to this directory**:
   ```bash
   git submodule add https://github.com/your-org/mcp-tools.git src/custom_tools/your-org
   ```
3. **Configure deployment** in `config/deployment.yaml` to include your tools
4. **Enable for clients** using the admin interface

## Development Guidelines

- **Use existing dependencies**: Prefer dependencies already available in mcpeasy core
- **Follow naming convention**: Tool names should be `{org}/{tool_name}` format
- **Implement BaseTool**: All tools must inherit from `src.tools.base.BaseTool`
- **Add configuration schema**: If your tool needs configuration, implement `get_config_schema()`
- **Include documentation**: Add README.md for each tool explaining its purpose and usage

## Available Dependencies

These dependencies are already available in mcpeasy core:
- `requests` - HTTP client
- `sqlalchemy` - Database ORM  
- `pydantic` - Data validation
- `fastapi` - Web framework
- `asyncio` - Async programming
- `logging` - Logging utilities
- Core mcpeasy modules: `src.database`, `src.tools.base`, etc.

## Example Tool Implementation

```python
# your-org/tools/example_tool/tool.py
from typing import Dict, Any, Optional
from src.tools.base import BaseTool
from src.tools.types import ToolResult
import requests  # Using existing dependency

class ExampleTool(BaseTool):
    name = "example_tool"
    description = "An example custom tool"
    
    @classmethod
    def get_config_schema(cls) -> Optional[Dict[str, Any]]:
        return {
            "type": "object",
            "properties": {
                "api_key": {"type": "string", "description": "API key for service"}
            },
            "required": ["api_key"]
        }
    
    async def execute(self, arguments: Dict[str, Any], config: Dict[str, Any] = None) -> ToolResult:
        # Tool implementation here
        
        # Return different types based on your data:
        
        # For plain text responses:
        # return ToolResult.text("Tool executed successfully")
        
        # For markdown-formatted responses (sent as plain text):
        # return ToolResult.markdown("# Success\n\nTool **executed** successfully")
        
        # For structured data (recommended for LLM processing):
        return ToolResult.json({
            "status": "success",
            "message": "Tool executed successfully",
            "data": {"processed_items": 42}
        })
        
        # For file/resource references (sent as structured JSON):
        # return ToolResult.file("s3://bucket/result.pdf", mime_type="application/pdf")
        
        # For errors:
        # return ToolResult.error("Something went wrong")
```

For more details, see the main [CUSTOMTOOLS_README.md](../../CUSTOMTOOLS_README.md) file.