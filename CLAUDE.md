# Multi-MCP Server Implementation Notes

## Architecture Decision: Multi-Tenant API Key Routing

**Key insight**: Multi-tenant design where clients can have multiple rotatable API keys with per-tool and per-resource configurations. API keys are embedded in URL path (`/mcp/{api_key}`) for simple MCP client integration.

### Benefits:
- **Multi-tenancy**: Clear client separation with multiple API keys per client
- **Configuration isolation**: Each client can configure tools and resources differently
- **Key rotation**: Generate new keys without losing tool/resource configurations
- **Per-tool config**: Same tool behaves differently for different clients
- **Per-resource config**: Same resource provides different data access per client
- **Scalable**: No custom auth headers needed, each key gets automatic routing
- **Compatible**: Works with any MCP client expecting HTTP URL

## Core Components

### 1. Main FastAPI App (`main.py`)
- **Lifespan management**: Database and MCP factory initialization
- **API key routing**: Single endpoint `/mcp/{api_key}` handles all MCP requests
- **Streaming support**: All responses use StreamingResponse for performance

### 2. MCP Server Factory (`server/factory.py`)
- **Instance caching**: Reuses MCP server instances based on client configuration
- **Tool registration**: Dynamic tool setup with per-client configurations
- **Resource registration**: Dynamic resource setup with per-client configurations via registry
- **Configuration injection**: Passes client-specific tool and resource configs
- **Streaming protocol**: Custom streaming response handling for MCP

### 3. Database Service (`database.py`)
- **Multi-tenant storage**: Clients, API keys, tool configurations, and resource configurations
- **SQLAlchemy async**: Modern async database layer with proper typing and asyncpg driver
- **Connection pooling**: PostgreSQL with optimized pool settings
- **Migration system**: Alembic-based migrations with automatic execution on startup
- **Soft deletes**: Keys marked inactive instead of hard delete

### 4. Admin Interface (`admin/routes.py`)
- **Client management**: Create, edit, and manage client organizations
- **API key management**: Generate, rotate, and expire keys per client
- **Tool configuration**: Dynamic forms based on tool schemas
- **Resource configuration**: Dynamic forms based on resource schemas
- **Session auth**: Secure session-based authentication

## Implementation Patterns

### Streamable HTTP Transport
Every subserver provides streaming via:
```python
async def generate_response():
    yield f"data: {json.dumps(response)}\n\n"

return StreamingResponse(generate_response(), media_type="text/plain")
```

### Multi-Tenant Tool Configuration
Tools are configured per client with optional tool-specific settings:
```python
# Get client by API key
client = await db.get_client_by_api_key(api_key)

# Get tool configurations for this client
tool_configs = await db.get_tool_configurations(client.id)

# Execute tool with client-specific config
config = tool_configs.get(tool_name, {})
result = await tool.execute(arguments, config)
```

### Multi-Tenant Resource Configuration
Resources are configured per client with optional resource-specific settings:
```python
# Get client by API key
client = await db.get_client_by_api_key(api_key)

# Get resource configurations for this client
resource_configs = await db.get_resource_configurations(client.id)

# List/read resources with client-specific config
enabled_resources = list(resource_configs.keys())
resources = await resource_registry.list_resources(enabled_resources, resource_configs)
```

### Database Schema
```sql
-- Clients (organizations/users)
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- API Keys (many per client, rotatable)
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    client_id UUID REFERENCES clients(id),
    key_value VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Tool Configurations (per client per tool)
CREATE TABLE tool_configurations (
    id SERIAL PRIMARY KEY,
    client_id UUID REFERENCES clients(id),
    tool_name VARCHAR(255) NOT NULL,
    configuration JSONB, -- NULL allowed for tools that don't need config
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(client_id, tool_name)
);

-- Resource Configurations (per client per resource)
CREATE TABLE resource_configurations (
    id SERIAL PRIMARY KEY,
    client_id UUID REFERENCES clients(id),
    resource_name VARCHAR(255) NOT NULL,
    configuration JSONB, -- NULL allowed for resources that don't need config
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(client_id, resource_name)
);

-- Tool Call Tracking (audit log for all tool executions)
CREATE TABLE tool_calls (
    id SERIAL PRIMARY KEY,
    client_id UUID REFERENCES clients(id),
    api_key_id INTEGER REFERENCES api_keys(id),
    tool_name VARCHAR(255) NOT NULL,
    input_data JSONB NOT NULL,        -- Tool arguments
    output_data JSONB,                -- Tool response (NULL for errors)
    error_message TEXT,               -- Error details (NULL for success)
    execution_time_ms INTEGER,        -- Duration in milliseconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Testing Approach

1. **Health check**: `GET /health`
2. **Admin access**: `GET /admin` → login → manage clients
3. **Client setup**: Create client → generate API key → configure tools and resources
4. **MCP endpoint**: `GET /mcp/{api_key}` for capability discovery  
5. **Tool calls**: `POST /mcp/{api_key}` with MCP request body
6. **Resource access**: `POST /mcp/{api_key}` with resources/list and resources/read
7. **Configuration testing**: Same tool/resource, different behavior per client

## Production Considerations

- **Database**: Use connection pooling for PostgreSQL
- **Logging**: Structured logging for debugging
- **Security**: Environment-based secrets management
- **Monitoring**: Health endpoints and metrics
- **Scaling**: Factory pattern allows efficient resource sharing

## Database Architecture

### Model Organization

Models are organized into separate files by domain for better maintainability:

```
src/models/
├── __init__.py          # Central model imports
├── base.py              # SQLAlchemy Base class
├── client.py            # Client and APIKey models  
├── configuration.py     # ToolConfiguration and ResourceConfiguration
├── knowledge.py         # KnowledgeBase model
└── tool_call.py         # ToolCall tracking model
```

### Tool and Resource Architecture

**Consistent Registry Pattern**: Both tools and resources use the same architecture for better maintainability:

```
src/tools/
├── __init__.py          # Tool exports
├── base.py              # BaseTool abstract class
├── types.py             # ToolSchema and ToolResult types
├── registry.py          # ToolRegistry for discovery and execution
└── {tool_name}/         # Individual tool implementations
    ├── __init__.py
    ├── tool.py
    └── README.md        # Tool-specific documentation

src/resources/
├── __init__.py          # Resource exports
├── base.py              # BaseResource abstract class  
├── types.py             # MCPResource and ResourceContent types
├── registry.py          # ResourceRegistry for discovery and access
└── {resource_name}/     # Individual resource implementations
    ├── __init__.py
    └── resource.py
```

**Key Architecture Features**:
- **Registry-only pattern**: Single registry class handles discovery, registration, and execution
- **Type separation**: Types defined in dedicated `types.py` files
- **Database injection**: Registry provides `set_database()` and `initialize()` methods
- **Auto-discovery**: Both registries scan their packages for implementations
- **Per-client configuration**: Registries filter based on client's enabled items

### Migration System - Simplified & Automated

**Alembic Integration**: Production-ready database migrations with zero-friction developer experience
- **Auto-generation**: Detects model changes and creates migration files
- **Startup execution**: Migrations run automatically when Docker containers start
- **Version tracking**: Database tracks current migration state
- **Safe deployments**: Failed migrations prevent app startup
- **Developer-friendly**: Single script handles all migration operations

**Simplified Migration Workflow**:
```bash
# The only command you need for development:
./migrate.sh create "add user preferences"

# Migrations apply automatically on:
docker-compose up          # First startup
docker-compose restart app # After creating migrations

# Optional manual commands:
./migrate.sh upgrade       # Apply migrations manually
./migrate.sh status        # Check status
./migrate.sh history       # View history
```

**Key Improvements Made**:
- ✅ **Removed migration manager complexity**: No more custom Python migration wrapper classes
- ✅ **Docker-native approach**: `alembic upgrade head` runs directly in Dockerfile CMD
- ✅ **Smart database handling**: `./migrate.sh` auto-starts database when needed for migration creation
- ✅ **Volume-mounted migrations**: New migration files immediately available in containers
- ✅ **Health check integration**: App waits for database to be ready via `depends_on: condition: service_healthy`

**Database Service**: Modern async database layer with asyncpg
```python
async with db.get_session() as session:
    # Proper session management with rollback
```

## Session-Based Authentication

**Session Management**: Proper FastAPI session middleware
- Secure session cookies with configurable secret
- Login/logout flow with redirects
- Protection against unauthorized access

**Admin Interface**: Production-ready HTML interface
- Responsive dashboard with token listing
- Copy MCP URLs to clipboard
- Delete tokens with confirmation
- Real-time token management

## Development Commands

### Local Development (without Docker)
```bash
# Install dependencies
uv sync

# Run development server (with auto-reload)
python dev.py

# Test health endpoint
curl http://localhost:8000/health

# Access admin (now with proper auth)
open http://localhost:8000/admin
```

### Docker Development (recommended)
```bash
# Development with live reload (default docker-compose.yml)
docker-compose up

# Or run in background
docker-compose up -d

# View logs with live updates
docker-compose logs -f app

# Stop services
docker-compose down

# Rebuild after dependency changes
docker-compose up --build

# Test health endpoint
curl http://localhost:8000/health

# Access admin interface
open http://localhost:8000/admin
```

### Docker Production
```bash
# Production build (uses docker-compose.prod.yml)
docker-compose -f docker-compose.prod.yml up

```

### Database Management
```bash
# Connect to local PostgreSQL (when running with docker-compose)
docker-compose exec db psql -U postgres -d mcp

# View database logs
docker-compose logs db

# Reset database (removes all data) 
docker-compose down -v
docker-compose up

# Access Adminer database inspector (development only)
open http://localhost:8080
# Login: Server=db, Username=postgres, Password=postgres, Database=mcp
```

### Migration Management - Zero-Friction Development

```bash
# Modern simplified approach:
./migrate.sh create "add user preferences table"    # Create migration
docker-compose restart app                          # Apply automatically

# Advanced commands (rarely needed):
./migrate.sh status                                 # Check status
./migrate.sh upgrade                                # Manual apply
./migrate.sh history                                # View history

# View migration files
ls src/migrations/versions/
```

**Migration Architecture Benefits**:
- **No Docker exec needed**: `./migrate.sh` handles database dependency automatically
- **Instant feedback**: Migration files immediately available via volume mounts
- **Production-safe**: Same automatic migration system in production
- **Zero configuration**: Works out of the box with docker-compose health checks

## Testing the Admin Interface

1. **Login**: Visit `/admin` and enter superadmin password
2. **Create tokens**: Use the dashboard form (no more password repetition!)
3. **View tokens**: Table shows all active tokens with tools
4. **Copy URLs**: Click "Copy URL" to get MCP endpoint
5. **Delete tokens**: Soft delete with confirmation

## Testing MCP Protocol

### MCP Inspector Setup
```bash
# Install MCP Inspector
npx @modelcontextprotocol/inspector

# Opens at http://localhost:5173
# Add your server URL: http://localhost:8000/mcp/{token}
```

### What to Test
1. **Connection**: Server should connect and show capabilities ✅
2. **Tool Discovery**: Should list only explicitly configured tools ✅
3. **Resource Discovery**: Should list only explicitly configured resources ✅
4. **Tool Execution**: Test each tool with different parameters ✅
5. **Resource Access**: Test resource reading with different URIs ✅
6. **Error Handling**: Try invalid tool/resource names or parameters ✅
7. **Access Control**: Verify unconfigured tools/resources are not accessible ✅

### Critical MCP Protocol Implementation Details

**Key Debugging Lessons Learned**:

1. **Field Naming**: MCP protocol uses camelCase for response fields:
   - `protocolVersion` (not `protocol_version`)
   - `serverInfo` (not `server_info`)

2. **Required Capabilities**: Must include all capability sections:
   ```python
   "capabilities": {
       "tools": {"listChanged": True},
       "resources": {"listChanged": True}, 
       "prompts": {"listChanged": True},
       "logging": {},
       "experimental": {"streaming": True}
   }
   ```

3. **Notification Handling**: Must handle `notifications/initialized` with empty response

4. **Protocol Version**: Must match client version exactly (`2025-03-26`)

5. **FastMCP ASGI Issues**: Direct JSON-RPC implementation works better than FastMCP's ASGI wrapper due to lifespan complexity

### Working Implementation Pattern
```python
# This approach bypasses FastMCP ASGI lifespan issues
if method == "initialize":
    response = {
        "jsonrpc": "2.0", 
        "id": request_data.get("id"),
        "result": {
            "protocolVersion": "2025-03-26",
            "capabilities": {...},
            "serverInfo": {...}
        }
    }
```

## Environment Setup

Add to your `.env`:
```bash
SESSION_SECRET=your_secure_session_key_here
SUPERADMIN_PASSWORD=your_admin_password
DATABASE_URL=postgresql://user:pass@host/db
```

## Production Deployment Ready

### What's Working
- ✅ Token-based URL routing (`/mcp/{token}`)
- ✅ SQLAlchemy async database with Neon PostgreSQL
- ✅ Session-based admin authentication
- ✅ MCP protocol fully compliant (2025-03-26)
- ✅ MCP Inspector integration verified
- ✅ Dynamic tool configuration per token
- ✅ Dynamic resource configuration per token
- ✅ Proper error handling and CORS
- ✅ Database health monitoring

### Multi-Tenant Architecture Implementation

**Phase 1: Core Infrastructure** ✅
- ✅ Multi-tenant database schema (clients, api_keys, tool_configurations, resource_configurations)
- ✅ UUID-based client IDs for better scalability and security
- ✅ Enhanced tool interface with configuration schemas
- ✅ Enhanced resource interface with configuration schemas
- ✅ Client and API key management in admin interface
- ✅ Per-client tool configuration system with strict access control
- ✅ Per-client resource configuration system with strict access control
- ✅ Intuitive admin UX: "Add" for simple tools/resources, "Configure" for complex ones
- ✅ Modular resource system with auto-discovery (knowledge base resource implemented)

### Example Resource Configuration (Knowledge Base)
```json
{
  "allowed_categories": ["documentation", "api"],
  "max_articles": 50,
  "allow_search": true,
  "excluded_tags": ["internal", "draft"]
}
```
This configuration allows a client to:
- Access only "documentation" and "api" categories
- See maximum 50 articles in listings
- Use search functionality
- Exclude articles tagged with "internal" or "draft"

**Phase 2: Enhanced Tooling & Resources**
1. **Tool ecosystem**: File operations, web search, database queries
2. **Resource ecosystem**: File system access, database tables, external APIs
3. **Configuration validation**: JSON schema validation for tool/resource configs
4. **Tool/Resource marketplace**: Easy discovery and configuration of available tools and resources

**Phase 2 Complete: Database & Migration System** ✅
- ✅ **Model organization**: Separated into domain-specific files
- ✅ **Alembic integration**: Auto-generation and startup execution  
- ✅ **Migration CLI**: Development commands for database management
- ✅ **Production safety**: Failed migrations prevent deployment
- ✅ **AsyncPG driver**: Full async/await database operations

**Phase 3: Production Features**
4. **Enhanced auth**: Role-based access, client user management
5. **Monitoring**: Per-client metrics, usage tracking, rate limiting
6. **Caching**: Redis for tool configurations and client data
7. **Testing**: Unit and integration tests for multi-tenant scenarios

**Phase 3: Tool Call Tracking & Monitoring** ✅
- ✅ **Automatic tool call logging**: Every tool execution tracked with timing
- ✅ **Complete audit trail**: Input arguments, output data, and error messages
- ✅ **Performance monitoring**: Execution time tracking in milliseconds
- ✅ **Per-client analytics**: Usage patterns and tool preferences by client
- ✅ **Error tracking**: Failed tool calls with detailed error information
- ✅ **Database integration**: Seamless logging without affecting tool performance

**Phase 4: Enterprise Features**
9. **Usage analytics dashboard**: Visual tool usage reports and metrics
10. **Billing integration**: Usage-based billing per client with detailed breakdowns
11. **High availability**: Multi-region deployment
12. **Advanced security**: Client isolation, data encryption

### Tool Call Tracking Implementation

**Architecture**: Transparent logging at the tool registry level

```python
# Automatic tracking in tool registry
async def execute_tool(name: str, arguments: dict, config: dict = None, context: dict = None):
    start_time = time.time()
    result = await tool.execute(arguments, config)
    execution_time_ms = int((time.time() - start_time) * 1000)
    
    # Log to database
    await db.create_tool_call(
        client_id=context['client'].id,
        api_key_id=context['api_key_record'].id,
        tool_name=name,
        input_data=arguments,
        output_data=result.content if not result.is_error else None,
        error_message=result.content[0]["text"] if result.is_error else None,
        execution_time_ms=execution_time_ms
    )
```

**Key Benefits**:
- **Transparent**: No changes needed to individual tools
- **Complete**: Captures all tool executions automatically
- **Performance**: Logging doesn't block tool execution
- **Resilient**: Failed logging doesn't break tool calls
- **Detailed**: Full context including client, API key, timing, and I/O data

**Use Cases**:
- **Monitoring**: Track which tools are used most frequently
- **Performance**: Identify slow tools and optimize them
- **Billing**: Usage-based pricing per client and tool
- **Debugging**: Full audit trail for troubleshooting issues
- **Analytics**: Understanding client behavior and tool preferences

## Performance & Scalability Optimizations

**Phase 4: Production Performance** ✅

### Background Task Processing
- ✅ **Async tool call logging**: Tool call auditing moved to FastAPI BackgroundTasks
- ✅ **Non-blocking responses**: Tool execution responses sent immediately while logging happens in background
- ✅ **Error resilience**: Failed background logging doesn't affect tool execution success
- ✅ **Automatic fallback**: Graceful degradation to synchronous logging if background tasks unavailable

```python
# Background logging implementation
async def execute_tool(name: str, arguments: dict, config: dict = None, 
                      context: dict = None, background_tasks: BackgroundTasks = None):
    result = await tool.execute(arguments, config)
    
    # Log in background after response is sent
    if background_tasks:
        background_tasks.add_task(log_tool_call_background, context, name, result)
    
    return result  # Response sent immediately
```

### Request Timeout Protection
- ✅ **30-second timeouts**: All tool executions wrapped with `asyncio.wait_for()`
- ✅ **Graceful timeout handling**: Proper error responses for timed-out tools
- ✅ **Worker protection**: Prevents runaway tools from blocking workers

```python
# Timeout implementation
try:
    result = await asyncio.wait_for(tool.execute(arguments, config), timeout=30.0)
except asyncio.TimeoutError:
    return ToolResult.error(f"Tool '{name}' execution timed out")
```

### Configuration Caching
- ✅ **5-minute TTL cache**: In-memory cache for tool/resource configurations
- ✅ **Per-client caching**: Reduces database queries for repeated configuration lookups
- ✅ **Cache invalidation**: Time-based expiry with manual refresh capability

```python
# Caching implementation
def _get_cached_config(client_id: str, config_type: str):
    cache_key = f"{client_id}:{config_type}"
    if cache_key in _config_cache:
        cached_data, cache_time = _config_cache[cache_key]
        if time.time() - cache_time < 300:  # 5 minutes
            return cached_data
    return None
```

### Database Connection Optimization
- ✅ **Connection pooling**: 10 base connections + 20 overflow per worker
- ✅ **Connection recycling**: 1-hour connection lifecycle to prevent stale connections
- ✅ **Pre-ping validation**: Automatic connection health checks
- ✅ **Timeout management**: 30-second pool timeout for connection acquisition

```python
# Database pool configuration
engine_kwargs = {
    "pool_size": 10,           # Base connections per worker
    "max_overflow": 20,        # Additional connections allowed
    "pool_timeout": 30,        # Max wait time for connection
    "pool_recycle": 3600,      # Recycle after 1 hour
    "pool_pre_ping": True,     # Validate connections
}
```

### Multi-Worker Production Setup
- ✅ **2-worker configuration**: Optimized for Fly.io 1GB instance
- ✅ **Worker recycling**: Automatic restart every 1000 requests
- ✅ **UvicornWorker class**: Better async performance and memory management
- ✅ **Graceful shutdown**: Proper cleanup on worker restart

```dockerfile
# Production Dockerfile optimization
CMD ["uvicorn", "src.main:app", 
     "--workers", "2",
     "--worker-class", "uvicorn.workers.UvicornWorker",
     "--max-requests", "1000",
     "--max-requests-jitter", "100"]
```

### Performance Impact
**Expected improvements from optimizations**:
- **Response latency**: 30-50% reduction in tool call response times
- **Throughput**: 2x increase with multi-worker setup
- **Database efficiency**: 80% reduction in configuration lookup latency
- **Reliability**: Better handling of concurrent requests and timeouts
- **Resource utilization**: Optimized connection pooling and worker management

### Monitoring & Metrics
**Key performance indicators to track**:
- Tool execution response times (P50, P95, P99)
- Background task completion rates
- Database connection pool utilization
- Worker memory usage and restart frequency
- Tool timeout occurrences

## Custom Tools Architecture - Production Ready

### Git Submodule Strategy

**Problem Solved**: Organizations can now add custom tools without forking the entire mcpeasy codebase or dealing with merge conflicts when pulling upstream changes.

**Architecture Benefits**:
- **Clean Separation**: Core tools in main repo, custom tools in organization-specific git repos
- **No Merge Conflicts**: Custom directories are gitignored, avoiding upstream conflicts
- **Two-Level Filtering**: Deployment YAML whitelist → Per-client database configuration
- **Version Control**: Each organization controls their custom tool versions independently
- **Easy Updates**: Pull upstream mcpeasy changes without affecting custom code

### Directory Structure

```
mcpeasy/
├── src/
│   ├── tools/                    # Core tools (committed to main repo)
│   ├── custom_tools/             # Custom tools root (gitignored contents)
│   │   ├── .gitkeep             # Keeps directory structure
│   │   ├── README.md            # Instructions for adding custom tools
│   │   └── {org-name}/          # Git submodule per organization
│   │       ├── tools/           # Organization's custom tools
│   │       └── requirements.txt # Additional dependencies (optional)
│   ├── resources/               # Core resources
│   ├── custom_resources/        # Custom resources (same pattern)
│   └── migrations/versions/     # All migrations (core + custom)
├── config/
│   ├── deployment.yaml          # Production tool whitelist
│   ├── deployment.dev.yaml      # Development tool whitelist
│   └── deployment.staging.yaml  # Staging tool whitelist
└── templates/                   # Templates for custom development
    ├── custom_tool/
    └── custom_resource/
```

### Deployment Configuration (YAML)

**Environment-specific tool filtering**:

```yaml
# config/deployment.yaml
deployment:
  name: "production"
  description: "Production deployment configuration"
  
  # Core tools to include
  core_tools:
    - echo
    - weather
    - email
    - youtube_lookup
  
  # Custom tool packages to include (from submodules)
  custom_tools:
    - acme/invoice_generator      # From custom_tools/acme/tools/invoice_generator
    - acme/crm_integration
    - widgets-inc/reporting
  
  # Core resources to include  
  core_resources:
    - knowledge
  
  # Custom resource packages to include
  custom_resources:
    - acme/product_catalog
    - widgets-inc/customer_data
```

### Enhanced Tool Response System

**Multiple Content Types for LLM Optimization**:

```python
# Enhanced ToolResult API for custom tools
class ToolResult:
    @classmethod
    def json(cls, data: Union[Dict, List]) -> "ToolResult":
        """Structured data for LLM processing (uses MCP structuredContent)"""
        return cls(content=[], structured_content=data)
    
    @classmethod 
    def text(cls, text: str) -> "ToolResult":
        """Human-readable text responses"""
        return cls(content=[{"type": "text", "text": text}])
        
    @classmethod
    def markdown(cls, markdown: str) -> "ToolResult":
        """Markdown-formatted responses"""
        return cls(content=[{"type": "text", "text": markdown}])
        
    @classmethod
    def file(cls, uri: str, mime_type: str = None) -> "ToolResult":
        """File references (S3, URLs, etc.)"""
        file_data = {"url": uri}
        if mime_type:
            file_data["mime_type"] = mime_type
        return cls(content=[], structured_content=file_data)
        
    @classmethod
    def error(cls, message: str) -> "ToolResult":
        """Error responses with user-friendly messages"""
        return cls(content=[{"type": "text", "text": message}], is_error=True)
```

### Registry Discovery Enhancement

**Multi-Directory Tool Discovery**:

```python
class ToolRegistry:
    def discover_tools(self):
        # 1. Load deployment configuration from YAML
        config = self._load_deployment_config()
        
        # 2. Discover from core directory  
        core_tools = self._discover_in_package("src.tools")
        
        # 3. Discover from custom directories
        custom_tools = self._discover_custom_tools("src/custom_tools")
        
        # 4. Filter by deployment whitelist
        allowed_tools = config.get('core_tools', []) + config.get('custom_tools', [])
        filtered_tools = [t for t in (core_tools + custom_tools) if t.name in allowed_tools]
        
        # 5. Register filtered tools with proper namespacing
        for tool in filtered_tools:
            # Custom tools get org/tool_name format
            if "/" in tool.name:  # Custom tool
                tool.schema.name = tool.name  # Override for MCP protocol
            self.register_tool(tool)
```

### Admin UI Enhancements

**Visual Tool Source Identification**:

- **CORE tools**: Blue badges for tools from main mcpeasy repository
- **CUSTOM tools**: Purple badges for organization-specific tools (detected by "/" in tool name)
- **Response type tracking**: Separate JSON vs TEXT analytics with badges
- **Tool configuration**: Same interface works for both core and custom tools

### Database Schema Updates

**Enhanced Tool Call Tracking**:

```sql
-- Updated tool_calls table with separate output columns
CREATE TABLE tool_calls (
    id SERIAL PRIMARY KEY,
    client_id UUID REFERENCES clients(id),
    api_key_id INTEGER REFERENCES api_keys(id),
    tool_name VARCHAR(255) NOT NULL,           -- Can be "core_tool" or "org/custom_tool"
    input_data JSONB NOT NULL,
    output_text JSONB,                         -- Text/markdown content arrays
    output_json JSONB,                         -- Structured data responses
    error_message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Migration Strategy

**Automatic Custom Migration Discovery**:

- **Timestamp-based naming**: `YYYYMMDD_HHMMSS_core_description.py` vs `YYYYMMDD_HHMMSS_custom_org_description.py`
- **Auto-discovery**: Enhanced `src/migrations/env.py` finds custom models in submodules
- **Ordering guarantee**: Core migrations always run before custom migrations
- **Custom migration flag**: `./migrate.sh create --custom "message"` for organization-specific migrations

### User Workflow

**Complete Custom Tool Development Cycle**:

1. **Fork mcpeasy** → Clone organization's fork
2. **Create custom tool repo** → Separate git repository for organization's tools  
3. **Add as submodule** → `git submodule add https://github.com/org/tools.git src/custom_tools/org`
4. **Configure deployment** → Add tool names to `config/deployment.yaml`
5. **Deploy application** → Custom tools automatically discovered and registered
6. **Configure per client** → Use admin UI to enable/configure tools per client
7. **Update independently** → Pull upstream mcpeasy changes without conflicts

### Production Features

**Enterprise-Ready Custom Tools**:

- ✅ **MCP Protocol Compliance**: Full compatibility with Model Context Protocol 2025-03-26
- ✅ **Multi-tenant Security**: Per-client tool configuration with deployment filtering  
- ✅ **Performance Optimizations**: Background logging, timeouts, caching for custom tools
- ✅ **Comprehensive Analytics**: Usage tracking with execution times for all tool types
- ✅ **Source Identification**: Clear visual distinction between CORE and CUSTOM tools
- ✅ **Response Type Analytics**: Separate tracking for JSON vs TEXT responses
- ✅ **Template System**: Complete templates for rapid custom tool development
- ✅ **Dependency Management**: Automatic installation of custom tool dependencies
- ✅ **End-to-End Testing**: Verified working with MCP Inspector and real custom tools