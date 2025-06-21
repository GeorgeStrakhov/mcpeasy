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
- **Deployment filtering**: YAML-based tool/resource whitelisting for environment-specific deployments
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

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Run development server**:
   ```bash
   python dev.py
   ```

4. **Access admin interface**:
   ```
   http://localhost:3000 (on prod this will be just https://yourdomain.com/admin)
   # Login with your SUPERADMIN_PASSWORD
   ```

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

1. Visit `/admin` and login with superadmin password
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

**Core Tools:**
- `echo` - Simple echo tool for testing (no configuration needed)
- `get_weather` - Weather information (no configuration needed)  
- `send_email` - Send emails (requires: from_email, optional: smtp_server)
- `youtube_lookup` - YouTube video information lookup (no configuration needed)

**Custom Tools:**
- Custom tools can be added via git submodules in organization-specific repositories
- Each deployment can whitelist different custom tools via YAML configuration
- Custom tools show with purple "CUSTOM" badges in admin UI vs blue "CORE" badges
- (Tool ecosystem grows with auto-discovery and organization contributions)

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

- `knowledge` - Knowledge base articles and categories (configurable: allowed_categories, max_articles, allow_search, excluded_tags)
- (Resource ecosystem grows with auto-discovery)

## Configuration

### Environment Variables

```bash
DATABASE_URL=postgresql://user:pass@host:port/db
PORT=8000
SESSION_SECRET=your_secure_session_key_here
SUPERADMIN_PASSWORD=your_secure_password
```

see .env.example for more

### Multi-Tenant Architecture

The system uses three main entities:
- **Clients**: Organizations or users (e.g., "ACME Corp") with UUID identifiers
- **API Keys**: Multiple rotatable keys per client
- **Tool Configurations**: Per-client tool settings stored as JSON with strict access control
- **Resource Configurations**: Per-client resource settings stored as JSON with strict access control

## Custom Tools Development

MCPeasy supports adding organization-specific tools while maintaining clean separation from core functionality:

### Quick Custom Tool Setup

1. **Fork mcpeasy repository**
2. **Create custom tool repository** with your organization's tools
3. **Add as git submodule**: `git submodule add https://github.com/yourorg/mcp-tools.git src/custom_tools/yourorg`
4. **Configure deployment**: Add tools to `config/deployment.yaml`
5. **Enable for clients**: Use admin UI to configure tools per client

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

### Templates and Documentation

- **Templates**: Complete tool/resource templates in `templates/` directory
- **Best practices**: Examples show proper dependency management and configuration
- **Git submodule workflow**: Clean separation between core and custom code
- **YAML deployment filtering**: Environment-specific tool availability

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

- **Background processing**: Tool call logging moved to background tasks for faster response times
- **Request timeouts**: 30-second timeouts prevent runaway tool executions
- **Configuration caching**: 5-minute TTL cache reduces database queries for configuration lookups
- **Connection pooling**: Optimized PostgreSQL connection management with pre-ping validation
- **Multi-worker setup**: 2 workers optimized for Fly.io deployment with automatic recycling

## Deployment

- **Platform**: Recommended deployment with Fly.io. NB! In some situations (e.g. if your MCP client connected to this runs inside cloudflare workers - you should set `force_https = false` in your fly.toml, because otherwise you may get endless redirect issues on the MCP client side)
- **Database**: Any postgres will do, tested on Neon PostgreSQL with automatic migrations
- **Environment**: Production-ready with proper error handling and migration safety
- **Workers**: 2 Uvicorn workers with 1000 request recycling for optimal memory management