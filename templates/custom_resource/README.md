# Custom Resource Template

This template provides a starting point for creating custom MCP resources.

## Quick Start

1. **Copy this template** to your custom resources repository:
   ```bash
   cp -r templates/custom_resource/ your-org-resources/resources/your_resource_name/
   ```

2. **Replace placeholders** in `resource.py`:
   - `RESOURCE_NAME` → your actual resource name (lowercase, no spaces)
   - `RESOURCE_NAMEResource` → your resource class name (PascalCase)
   - Update `description` with what your resource provides
   - Update URI scheme (e.g., `"company://products/"`)

3. **Implement the required methods**:
   - `validate_uri()` - Check if URI belongs to your resource
   - `list_resources()` - Return available resources
   - `read_resource()` - Return content for specific resource

4. **Update configuration schema** if your resource needs configuration

5. **Test your resource** before committing

## Resource Structure

```
your_resource_name/
├── __init__.py          # Package initialization
├── resource.py          # Main resource implementation
└── README.md            # This documentation
```

## Configuration

If your resource needs configuration (API keys, filters, etc.), implement `get_config_schema()`:

```python
@classmethod
def get_config_schema(cls) -> Optional[Dict[str, Any]]:
    return {
        "type": "object",
        "properties": {
            "api_key": {"type": "string", "description": "Your API key"},
            "allowed_categories": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Categories this client can access"
            }
        },
        "required": ["api_key"]
    }
```

## URI Schemes

Design a clear URI scheme for your resources:

```python
def validate_uri(self, uri: str) -> bool:
    return uri.startswith("company://")

# Examples:
# company://products/123
# company://customers/456
# company://orders/789
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
   pandas>=1.5.0,<2.0.0
   openpyxl>=3.0.0
   ```

2. **Import with graceful fallback**:
   ```python
   try:
       import pandas as pd
   except ImportError:
       pd = None  # Handle missing dependency
   ```

3. **Use specific versions** to avoid conflicts

4. **Keep dependencies minimal** - prefer existing mcpeasy dependencies when possible

5. **Test the Docker build** to ensure dependencies install correctly

## Example Implementation

```python
async def list_resources(self, config: Dict[str, Any] = None) -> List[MCPResource]:
    # Fetch from API
    import requests
    api_key = config.get("api_key") if config else None
    
    response = requests.get(
        "https://api.company.com/products",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    
    resources = []
    for product in response.json():
        resources.append(MCPResource(
            uri=f"company://products/{product['id']}",
            name=product["name"],
            description=product.get("description", ""),
            mimeType="application/json"
        ))
    
    return resources

async def read_resource(self, uri: str, config: Dict[str, Any] = None) -> ResourceContent:
    # Extract ID from URI
    product_id = uri.replace("company://products/", "")
    
    # Fetch product details
    import requests
    api_key = config.get("api_key") if config else None
    
    response = requests.get(
        f"https://api.company.com/products/{product_id}",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    
    return ResourceContent(
        uri=uri,
        mimeType="application/json",
        text=response.text
    )
```

## MIME Types

Support appropriate MIME types for your content:

- `text/plain` - Plain text content
- `application/json` - JSON data
- `text/html` - HTML content
- `image/jpeg`, `image/png` - Images
- `application/pdf` - PDF documents

## Per-Client Filtering

Use configuration to filter resources per client:

```python
async def list_resources(self, config: Dict[str, Any] = None) -> List[MCPResource]:
    all_products = await self._fetch_all_products()
    
    # Filter by allowed categories
    allowed_categories = config.get("allowed_categories", []) if config else []
    if allowed_categories:
        all_products = [
            p for p in all_products 
            if p["category"] in allowed_categories
        ]
    
    return [self._to_mcp_resource(p) for p in all_products]
```

## Testing

Test your resource locally before deployment:

```python
# In your development environment
from your_org.resources.your_resource.resource import YourResourceResource

resource = YourResourceResource()

# Test listing
resources = await resource.list_resources({"api_key": "test_key"})
print(f"Found {len(resources)} resources")

# Test reading
content = await resource.read_resource("company://products/123", {"api_key": "test_key"})
print(content.text)
```

## Next Steps

1. Implement your resource logic
2. Add it to your deployment configuration
3. Test in development environment
4. Deploy and enable for specific clients via admin UI