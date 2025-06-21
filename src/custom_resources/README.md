# Custom Resources Directory

This directory contains git submodules for custom MCP resources developed by organizations.

## Structure

Each organization should add their custom resources as a git submodule:

```
src/custom_resources/
├── .gitkeep
├── README.md (this file)
└── {org-name}/          # Git submodule per organization
    ├── resources/
    │   ├── resource_name_1/
    │   │   ├── __init__.py
    │   │   └── resource.py  # Implements BaseResource
    │   └── resource_name_2/
    │       ├── __init__.py
    │       └── resource.py
    ├── requirements.txt     # Additional dependencies (optional)
    └── README.md
```

## Adding Custom Resources

1. **Create your custom resources repository** in your organization's GitHub/GitLab
2. **Add as submodule to this directory**:
   ```bash
   git submodule add https://github.com/your-org/mcp-resources.git src/custom_resources/your-org
   ```
3. **Configure deployment** in `config/deployment.yaml` to include your resources
4. **Enable for clients** using the admin interface

## Development Guidelines

- **Use existing dependencies**: Prefer dependencies already available in mcpeasy core
- **Follow naming convention**: Resource names should be `{org}/{resource_name}` format
- **Implement BaseResource**: All resources must inherit from `src.resources.base.BaseResource`
- **Add configuration schema**: If your resource needs configuration, implement `get_config_schema()`
- **Include documentation**: Add README.md for each resource explaining its purpose and usage

## Available Dependencies

These dependencies are already available in mcpeasy core:
- `requests` - HTTP client
- `sqlalchemy` - Database ORM
- `pydantic` - Data validation
- `fastapi` - Web framework
- `asyncio` - Async programming
- `logging` - Logging utilities
- Core mcpeasy modules: `src.database`, `src.resources.base`, etc.

## Example Resource Implementation

```python
# your-org/resources/example_resource/resource.py
from typing import Dict, Any, Optional, List
from src.resources.base import BaseResource
from src.resources.types import MCPResource, ResourceContent

class ExampleResource(BaseResource):
    name = "example_resource"
    description = "An example custom resource"
    
    @classmethod
    def get_config_schema(cls) -> Optional[Dict[str, Any]]:
        return {
            "type": "object",
            "properties": {
                "data_source": {"type": "string", "description": "Data source URL"}
            },
            "required": ["data_source"]
        }
    
    def validate_uri(self, uri: str) -> bool:
        return uri.startswith("example://")
    
    async def list_resources(self, config: Dict[str, Any] = None) -> List[MCPResource]:
        # Return list of available resources
        return [
            MCPResource(
                uri="example://item1",
                name="Example Item 1",
                description="An example resource item",
                mimeType="text/plain"
            )
        ]
    
    async def read_resource(self, uri: str, config: Dict[str, Any] = None) -> ResourceContent:
        # Return resource content
        return ResourceContent(
            uri=uri,
            mimeType="text/plain",
            text="Example resource content"
        )
```

For more details, see the main [CUSTOMTOOLS_README.md](../../CUSTOMTOOLS_README.md) file.