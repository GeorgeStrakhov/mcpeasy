# Custom Resource Template

This template provides a starting point for creating custom MCP resources.

## Quick Start

1. **Copy this template** to your custom resources src/resources/{yourorg}/your resource

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
├── models.py            # SQLAlchemy models (if database-backed)
├── seeds/               # Optional seed data directory
│   ├── example_data.csv # CSV seed data
│   └── example_data.json # JSON seed data
├── requirements.txt     # Custom dependencies (if any)
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

## Auto-Seeding Data (Optional)

Resources can automatically seed initial data when their table is empty. This is useful for:
- Reference data (countries, categories, etc.)
- Demo/sample data
- Initial configuration

### How to Enable Seeding

1. **Add seed_source to your resource class**:
   ```python
   class YourResource(BaseResource):
       name = "your_resource"
       seed_source = "seeds/initial_data.csv"  # or .json
   ```

2. **Create seed data files**:
   - CSV: Column names should match your model fields
   - JSON: Array of objects with field names as keys
   - Can also use URLs: `seed_source = "https://example.com/data/seed.csv"`

3. **Override _get_model_class() if using database**:
   ```python
   async def _get_model_class(self):
       from .models import YourModel
       return YourModel
   ```

### Seed Data Formats

**CSV Format** (`seeds/data.csv`):
```csv
id,name,category,description,priority
1,Item One,documents,First item description,1
2,Item Two,images,Second item description,2
```

**JSON Format** (`seeds/data.json`):
```json
[
  {
    "id": 1,
    "name": "Item One",
    "category": "documents",
    "description": "First item description",
    "priority": 1
  },
  {
    "id": 2,
    "name": "Item Two",
    "category": "images",
    "description": "Second item description",
    "priority": 2
  }
]
```

### Seeding Behavior

- Only runs when table is completely empty
- Runs automatically on first resource initialization
- No versioning or merging - it's a one-time operation
- Logs success/failure for debugging
- Non-blocking - failures won't prevent resource from working

## Next Steps

1. Implement your resource logic
2. put your resource code into src/resources/{yourorg}/{yourResource}  and don't forget to enable in .env (unless you are using RESOURCES='__all__')
3. Test in development environment
4. Deploy and enable for specific clients via admin UI