# MCPeasy

_the easiest way to set-up and self-host your own multi-MCP server with streamable http transport and multi-client and key management_

A production-grade multi-tenant MCP server that provides different tools and configurations to different clients using API key-based routing.

## Architecture

- **FastMCP 2.6**: Core MCP implementation following https://gofastmcp.com/llms-full.txt
- **FastAPI**: Web framework with API key-based URL routing
- **PostgreSQL**: Multi-tenant data storage with SQLAlchemy
- **Streamable HTTP**: All subservers provide streamable transport
- **Multi-tenancy**: Clients can have multiple API keys with tool-specific configurations

## Key Features

- **Multi-tenant design**: Clients manage multiple rotatable API keys
- **Per-tool configuration**: Each client can configure tools differently (e.g., custom email addresses)
- **Dynamic tool sets**: Different clients get different tool combinations
- **Tool auto-discovery**: Modular tool system with automatic registration
- **Custom tools support**: Add organization-specific tools via git submodules with clean upstream separation
- **Per-resource configuration**: Each client can access different resources with custom settings
- **Dynamic resource sets**: Different clients get different resource combinations
- **Resource auto-discovery**: Modular resource system with automatic registration
- **Enhanced tool responses**: Multiple content types (text, JSON, markdown, file) for optimal LLM integration
- **Environment-based discovery**: Simple environment variable configuration for tool/resource enablement
- **Shared infrastructure**: Database, logging, and configuration shared across servers
- **Admin interface**: Web-based client and API key management with CORE/CUSTOM tool source badges
- **Production ready**: Built for Fly deployment with Neon database
- **High performance**: Background task processing, request timeouts, configuration caching, and optimized database connections

## Quick Start

1. **Setup environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your database URL, admin password, and session secret
   ```

2. **Start all services with Docker Compose** (recommended):
   ```bash
   docker-compose up
   ```

3. **Access the services**:
   ```
   http://localhost:8000       # Main API endpoint
   http://localhost:3000       # Admin interface (on prod: https://yourdomain.com/admin). Log in with username 'superadmin', pass: your 'SUPERADMIN_PASSWORD' from .env
   http://localhost:8080       # Database inspector (Adminer)
   ```

That's it! Docker Compose handles all dependencies, database setup, and migrations automatically.

## API Endpoints

- `GET /health` - Health check
- `GET /admin` - Admin login page
- `GET /admin/clients` - Client management dashboard
- `POST /admin/clients` - Create new client
- `GET /admin/clients/{id}/keys` - Manage API keys for client
- `POST /admin/clients/{id}/keys` - Generate new API key
- `GET /admin/clients/{id}/tools` - Configure tools for client
- `GET|POST /mcp/{api_key}` - MCP endpoint (streamable)

## Client & API Key Management

### Creating Clients

1. Visit `/` (in development localhost:3000) and login with superadmin password
2. Create client with name and description
3. Generate API keys for the client
4. Configure tools and resources with their settings per client

### Managing API Keys

- **Multiple keys per client**: Production, staging, development keys
- **Key rotation**: Generate new keys without losing configuration
- **Expiry management**: Set expiration dates for keys
- **Secure deletion**: Deactivate compromised keys immediately

### Tool Configuration

Each client must explicitly configure tools to access them:
- **Simple tools**: `echo`, `get_weather` - click "Add" to enable (no configuration needed)
- **Configurable tools**: `send_email` - click "Configure" to set from address, SMTP settings
- **Per-client settings**: Same tool, different configuration per client
- **Strict access control**: Only configured tools are visible and callable

### Available Tools

**Namespaced Tool System:**
All tools are organized in namespaces for better organization and conflict avoidance:

**Core Tools (namespace: `core/`):**
- `core/echo` - Simple echo tool for testing (no configuration needed)
- `core/weather` - Weather information (no configuration needed)  
- `core/send_email` - Send emails (requires: from_email, optional: smtp_server)
- `core/datetime` - Date and time utilities
- `core/scrape` - Web scraping functionality
- `core/youtube_lookup` - YouTube video information

**Custom Tools (namespace: `{org}/`):**
- `myorg/send_invoice` - Custom tool would live here
- Custom tools can be added in organization-specific namespaces
- Each deployment can control which tools are available via environment configuration
- Custom tools show with purple "CUSTOM" badges in admin UI vs blue "CORE" badges

**Tool Discovery:**
- Use `TOOLS=__all__` to automatically discover and enable all available tools
- Or specify exact tools: `TOOLS='core/echo,core/weather,myorg/send_invoice'`
- Directory structure: `src/tools/{namespace}/{tool_name}/tool.py`

### Tool Call Tracking

All tool executions are automatically tracked in the database for monitoring and auditing:

- **Complete tracking**: Input arguments, output data, execution time, and errors
- **Per-client logging**: Track usage patterns by client and API key
- **Performance monitoring**: Execution time tracking in milliseconds
- **Error logging**: Failed tool calls with detailed error messages
- **Automatic**: No configuration needed - all tool calls are logged transparently

### Resource Configuration

Each client must explicitly configure resources to access them:
- **Simple resources**: `knowledge` - click "Add" to enable with default settings
- **Configurable resources**: `knowledge` - click "Configure" to set category filters, article limits, search permissions
- **Per-client settings**: Same resource, different configuration per client (e.g., different category access)
- **Strict access control**: Only configured resources are visible and accessible

### Available Resources

**Namespaced Resource System:**
Resources follow the same namespacing pattern as tools for better organization:

**Core Resources:**
- `knowledge` - Knowledge base articles and categories (configurable: allowed_categories, max_articles, allow_search, excluded_tags)

**Custom Resources (namespace: `{org}/`):**
- `myorg/knowledge` - Example of a namespaced resource
- Custom resources can be added in organization-specific namespaces
- Each deployment can control which resources are available via environment configuration

**Resource Discovery:**
- Use `RESOURCES=__all__` to automatically discover and enable all available resources
- Or specify exact resources: `RESOURCES='knowledge,myorg/product_catalog'`
- Directory structure: `src/resources/{namespace}/{resource_name}/resource.py` or `src/resources/{resource_name}/resource.py`

### Resource Auto-Seeding

Resources can automatically seed initial data when their table is empty, perfect for:
- **Reference data**: Countries, categories, product catalogs
- **Demo content**: Sample articles, documentation
- **Initial configuration**: Default settings, presets

**How It Works:**
1. Resource checks if its table is empty on first initialization
2. If empty, loads seed data from configured source (CSV/JSON file or URL)
3. Inserts data into database with proper field mapping
4. Only runs once - subsequent startups skip seeding

**Setup Example:**
```python
class ProductCatalogResource(BaseResource):
    name = "myorg/products"
    seed_source = "seeds/initial_products.csv"  # Local file
    # seed_source = "https://cdn.myorg.com/products.csv"  # Or remote URL
    
    async def _get_model_class(self):
        from .models import Product
        return Product
```

**Supported Formats:**
- **CSV**: Column names match model fields, empty strings become NULL
- **JSON**: Array of objects with field names as keys
- **Remote URLs**: Fetch seed data from CDNs or APIs

**Example Seed Files:**
```csv
# seeds/products.csv
id,name,category,price,description
1,Widget A,widgets,29.99,Premium widget
2,Widget B,widgets,39.99,Deluxe widget
```

```json
// seeds/products.json
[
  {"id": 1, "name": "Widget A", "category": "widgets", "price": 29.99},
  {"id": 2, "name": "Widget B", "category": "widgets", "price": 39.99}
]
```

## Configuration

### Environment Variables

```bash
DATABASE_URL=postgresql://user:pass@host:port/db
PORT=8000
SESSION_SECRET=your_secure_session_key_here
SUPERADMIN_PASSWORD=your_secure_password

# Tool and resource discovery
TOOLS=__all__              # Enable all discovered tools, or list specific ones like 'core/echo,m38/calculator'
RESOURCES=__all__          # Enable all discovered resources, or list specific ones like 'knowledge'

# Tool execution queue configuration
TOOL_MAX_WORKERS=20        # Max concurrent tool executions (default: 20)
TOOL_QUEUE_SIZE=200        # Max queued requests (default: 200)
```

see .env.example for more

### Multi-Tenant Architecture

The system uses three main entities:
- **Clients**: Organizations or users (e.g., "ACME Corp") with UUID identifiers
- **API Keys**: Multiple rotatable keys per client
- **Tool Configurations**: Per-client tool settings stored as JSON with strict access control
- **Resource Configurations**: Per-client resource settings stored as JSON with strict access control

## Custom Tools Development

MCPeasy supports adding organization-specific tools using a simplified namespaced directory structure:

### Quick Custom Tool Setup

1. **Create namespace directory**: `mkdir -p src/tools/yourorg`
2. **Add your tool**: Create `src/tools/yourorg/yourtool/tool.py` with your tool implementation
3. **Auto-discovery**: Tool automatically discovered as `yourorg/yourtool`
4. **Configure environment**: 
   - Use `TOOLS=__all__` to enable all tools automatically
   - Or specify: `TOOLS='core/echo,yourorg/yourtool'`
5. **Enable for clients**: Use admin UI to configure tools per client

### Directory Structure

```
src/tools/
├── core/                    # Core mcpeasy tools
│   ├── echo/
│   ├── weather/
│   └── send_email/
├── m38/                     # Example custom namespace
│   └── calculator/
└── yourorg/                 # Your organization's tools
    ├── invoice_generator/
    ├── crm_integration/
    └── custom_reports/
```

### Enhanced Tool Response Types

Custom tools support multiple content types for optimal LLM integration:

```python
# Structured data (recommended for LLM processing)
return ToolResult.json({"result": 42, "status": "success"})

# Human-readable text
return ToolResult.text("Operation completed successfully!")

# Markdown formatting
return ToolResult.markdown("# Success\n\n**Result**: 42")

# File references
return ToolResult.file("s3://bucket/report.pdf", mime_type="application/pdf")

# Error handling
return ToolResult.error("Invalid operation: division by zero")
```

### Running Synchronous Code in Tools

If your custom tool needs to run synchronous (blocking) code, use `asyncio.to_thread()` to avoid blocking the async event loop:

```python
import asyncio
from src.tools.base import BaseTool, ToolResult

class MyCustomTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_custom_tool"
    
    async def execute(self, arguments: dict, config: dict = None) -> ToolResult:
        # For CPU-bound or blocking I/O operations
        result = await asyncio.to_thread(self._blocking_operation, arguments)
        return ToolResult.json(result)
    
    def _blocking_operation(self, arguments: dict):
        # This runs in a thread pool, safe to block
        import time
        time.sleep(5)  # Example: blocking operation
        return {"processed": True, "data": arguments}
```

**Important**: Never use blocking operations directly in the `execute()` method as it will block the entire event loop and affect other tool executions.

## Custom Resources Development

MCPeasy supports adding organization-specific resources with automatic data seeding capabilities:

### Quick Custom Resource Setup

1. **Create namespace directory**: `mkdir -p src/resources/yourorg`
2. **Add your resource**: Create `src/resources/yourorg/yourresource/resource.py` with implementation
3. **Auto-discovery**: Resource automatically discovered as `yourorg/yourresource`
4. **Configure environment**: 
   - Use `RESOURCES=__all__` to enable all resources automatically
   - Or specify: `RESOURCES='knowledge,yourorg/yourresource'`
5. **Optional seeding**: Add `seed_source` and `seeds/` directory for initial data
6. **Enable for clients**: Use admin UI to configure resources per client

### Directory Structure

```
src/resources/
├── knowledge/               # Core resources (simple)
├── myorg/                   # Namespaced resources
│   └── knowledge/
│       ├── resource.py
│       ├── models.py
│       └── seeds/
│           ├── articles.csv
│           └── categories.json
└── yourorg/                 # Your organization's resources
    ├── product_catalog/
    │   ├── resource.py
    │   ├── models.py
    │   └── seeds/
    │       └── products.csv
    └── customer_data/
        ├── resource.py
        └── models.py
```

### Custom Resource with Auto-Seeding

```python
from src.resources.base import BaseResource
from src.resources.types import MCPResource, ResourceContent

class ProductCatalogResource(BaseResource):
    name = "yourorg/products"
    description = "Product catalog with pricing and inventory"
    uri_scheme = "products"
    
    # Optional: Auto-seed when table is empty
    seed_source = "seeds/initial_products.csv"
    
    async def _get_model_class(self):
        from .models import Product
        return Product
    
    async def list_resources(self, config=None):
        # Implementation with client-specific filtering
        pass
    
    async def read_resource(self, uri: str, config=None):
        # Implementation with access control
        pass
```

### Templates and Documentation

- **Templates**: Complete tool/resource templates in `templates/` directory with auto-seeding examples
- **Best practices**: Examples show proper dependency management, configuration, and data seeding
- **Namespace organization**: Clean separation between core and custom tools/resources
- **Environment variable discovery**: Simple TOOLS and RESOURCES configuration
- **Seed data examples**: CSV and JSON seed file templates included

## Development

### Docker Development (Recommended)

```bash
# Start all services with live reload
docker-compose up

# Access services:
# - App: http://localhost:8000
# - Admin: http://localhost:3000
# - Database Inspector: http://localhost:8080
```

Live reload on both frontend and backend

### Database Inspector (Adminer)

When running with Docker Compose, Adminer provides a lightweight web interface to inspect your PostgreSQL database:

- **URL**: `http://localhost:8080`
- **Login credentials**:
  - Server: `db`
  - Username: `postgres` 
  - Password: `postgres`
  - Database: `mcp`

**Features**:
- Browse all tables (clients, api_keys, tool_configurations, resource_configurations, tool_calls)
- View table data and relationships
- Run SQL queries
- Export data
- Monitor database schema changes
- Analyze tool usage patterns and performance metrics

### Local Development

- **Dependencies**: Managed with `uv`
- **Code structure**: Modular design with SQLAlchemy models, session auth, admin UI
- **Database**: PostgreSQL with async SQLAlchemy and Alembic migrations
- **Authentication**: Session-based admin authentication with secure cookies
- **Migrations**: Automatic database migrations with Alembic
- **Testing**: Run development server with auto-reload

## Testing MCP Endpoints

### Using MCP Inspector (Recommended)

1. **Get token URL**: From admin dashboard, copy the MCP URL for your token
2. **Install inspector**: `npx @modelcontextprotocol/inspector`
3. **Open inspector**: Visit http://localhost:6274 in browser (include proxy auth if needed, following instructions at inspector launch)
4. **Add server**: Enter your MCP URL: `http://localhost:8000/mcp/{token}`
5. **Configure tools and resources**: In admin interface, add/configure tools and resources for your client
6. **Test functionality**: Click on configured tools and resources to test them (unconfigured items won't appear)

**✅ Verified Working**: The MCP Inspector successfully connects and displays only configured tools and resources!

### Manual Testing

```bash
# Test capability discovery
curl http://localhost:8000/mcp/{your_api_key}

# Test echo tool (no configuration needed)
curl -X POST http://localhost:8000/mcp/{your_api_key} \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "echo",
      "arguments": {"message": "Hello MCP!"}
    }
  }'

# Test send_email tool (uses client-specific configuration)
curl -X POST http://localhost:8000/mcp/{your_api_key} \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "send_email",
      "arguments": {
        "to": "user@example.com",
        "subject": "Test",
        "body": "This uses my configured from address!"
      }
    }
  }'

# Test knowledge resource (uses client-specific configuration)
curl -X POST http://localhost:8000/mcp/{your_api_key} \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "resources/read",
    "params": {
      "uri": "knowledge://search?q=api"
    }
  }'
```

## Database Migrations

The system uses Alembic for database migrations with **automatic execution on Docker startup** for the best developer experience.

### Migration Workflow (Simplified)

```bash
# 1. Create a new migration after making model changes
./migrate.sh create "add user preferences table"

# 2. Restart the app (migrations apply automatically)
docker-compose restart app

# That's it! No manual migration commands needed.
```

### Available Migration Commands

The `./migrate.sh` script provides all migration functionality:

```bash
# Create new migration (auto-starts database if needed)
./migrate.sh create "migration message"

# Apply pending migrations manually (optional)
./migrate.sh upgrade

# Check current migration status
./migrate.sh status

# View migration history
./migrate.sh history
```

### How It Works

1. **Development**: Use `./migrate.sh create "message"` to generate migration files
2. **Automatic Application**: Migrations run automatically when Docker containers start
3. **No Manual Steps**: The Docker containers handle `alembic upgrade head` on startup
4. **Database Dependency**: Docker waits for database health check before running migrations
5. **Volume Mounting**: Migration files are immediately available in containers via volume mounts

### Model Organization

Models are organized in separate files by domain:

- `src/models/base.py` - SQLAlchemy Base class
- `src/models/client.py` - Client and APIKey models
- `src/models/configuration.py` - Tool and Resource configurations
- `src/models/knowledge.py` - Knowledge base models
- `src/models/tool_call.py` - Tool call tracking and auditing

### Migration Workflow

1. **Make model changes** in the appropriate model files
2. **Generate migration**: The system auto-detects changes and creates migration files
3. **Review migration**: Check the generated SQL in `src/migrations/versions/`
4. **Deploy**: Migrations run automatically on startup in production

### Production Migration Behavior

- ✅ **Automatic execution**: Migrations run on app startup
- ✅ **Safe rollouts**: Failed migrations prevent app startup
- ✅ **Version tracking**: Database tracks current migration state
- ✅ **Idempotent**: Safe to run multiple times

## Performance & Scalability

The system is optimized for production workloads with several performance enhancements:

- **Queue-based execution**: Bounded concurrency with configurable worker pools prevents server overload
- **Fair scheduling**: FIFO queue ensures all clients get served during traffic bursts
- **Background processing**: Tool call logging moved to background tasks for faster response times
- **Extended timeouts**: 3-minute timeouts support long-running tools (configurable)
- **Configuration caching**: 5-minute TTL cache reduces database queries for configuration lookups
- **Connection pooling**: Optimized PostgreSQL connection management with pre-ping validation
- **Multi-worker setup**: 2 workers optimized for Fly.io deployment with automatic recycling
- **Queue monitoring**: Real-time queue metrics available at `/metrics/queue` endpoint

### Queue Configuration

Control tool execution concurrency and queue behavior:

```bash
# Environment variables for .env
TOOL_MAX_WORKERS=20    # Concurrent tool executions (default: 20)
TOOL_QUEUE_SIZE=200    # Maximum queued requests (default: 200)

# Recommended settings by server size:
# Small servers: TOOL_MAX_WORKERS=5, TOOL_QUEUE_SIZE=50
# Production: TOOL_MAX_WORKERS=50, TOOL_QUEUE_SIZE=500
```

### Queue Monitoring

```bash
# Check queue health and capacity
curl http://localhost:8000/metrics/queue

# Response includes:
{
  "queue_depth": 3,          # Current requests waiting
  "max_workers": 20,         # Maximum concurrent executions  
  "max_queue_size": 200,     # Maximum queue capacity
  "workers_started": 20,     # Number of active workers
  "is_started": true         # Queue system status
}
```

## Deployment

- **Platform**: Recommended deployment with Fly.io. NB! In some situations (e.g. if your MCP client connected to this runs inside cloudflare workers - you should set `force_https = false` in your fly.toml, because otherwise you may get endless redirect issues on the MCP client side)
- **Database**: Any postgres will do, tested on Neon PostgreSQL with automatic migrations
- **Environment**: Production-ready with proper error handling and migration safety
- **Workers**: 2 Uvicorn workers with 1000 request recycling for optimal memory management