"""
API endpoints for admin interface
"""
import secrets
import json
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel

from src.database import DatabaseService
from src.tools.registry import tool_registry
from src.resources.registry import resource_registry
from src.server.factory import clear_config_cache
from src.utils.prompt_generator import generate_system_prompt
from src.admin.auth import require_admin_auth, authenticate_admin, verify_admin_session, logout_admin, get_current_admin_username


# Request/Response models
class LoginRequest(BaseModel):
    username: str
    password: str

class CreateClientRequest(BaseModel):
    name: str
    description: Optional[str] = None

class CreateApiKeyRequest(BaseModel):
    name: str
    expires_days: Optional[int] = None

class AuthResponse(BaseModel):
    authenticated: bool
    message: Optional[str] = None

class ClientSummary(BaseModel):
    id: str
    name: str
    description: Optional[str]
    api_key_count: int
    tool_count: int
    created_at: datetime
    is_active: bool

class DashboardResponse(BaseModel):
    clients: List[ClientSummary]
    total_api_keys: int
    total_tools: int  # Total configured tools across all clients
    available_tools: int  # Total available tools in the system

class ApiKeySummary(BaseModel):
    id: int
    key_value: str
    name: str
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool

class ToolInfo(BaseModel):
    name: str
    description: Optional[str]
    requires_config: bool
    config_schema: Optional[Dict[str, Any]]
    is_configured: bool
    configuration: Optional[Dict[str, Any]]

class ResourceInfo(BaseModel):
    name: str
    requires_config: bool
    config_schema: Optional[Dict[str, Any]]
    is_configured: bool
    configuration: Optional[Dict[str, Any]]

class ClientDetailResponse(BaseModel):
    client: ClientSummary
    api_keys: List[ApiKeySummary]
    tools: List[ToolInfo]
    resources: List[ResourceInfo]

class SystemPromptSummary(BaseModel):
    id: int
    version: int
    user_requirements: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class GeneratePromptRequest(BaseModel):
    user_requirements: str
    is_revision: bool = False
    parent_version_id: Optional[int] = None

class SavePromptRequest(BaseModel):
    prompt_text: str
    user_requirements: str
    generation_context: Dict[str, Any]
    parent_version_id: Optional[int] = None

class SystemPromptResponse(BaseModel):
    id: int
    client_id: str
    prompt_text: str
    version: int
    user_requirements: str
    generation_context: Dict[str, Any]
    is_active: bool
    parent_version_id: Optional[int]
    created_at: datetime
    updated_at: datetime


router = APIRouter()


# Authentication API Routes

@router.post("/auth/login", response_model=AuthResponse)
async def api_login(request: Request, login_data: LoginRequest):
    """API endpoint for admin login"""
    db: DatabaseService = request.app.state.db
    
    if await authenticate_admin(request, login_data.username, login_data.password, db):
        return AuthResponse(authenticated=True, message="Login successful")
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")


@router.post("/auth/logout", response_model=AuthResponse)
async def api_logout(request: Request):
    """API endpoint for admin logout"""
    logout_admin(request)
    return AuthResponse(authenticated=False, message="Logout successful")


@router.get("/auth/status", response_model=AuthResponse)
async def api_auth_status(request: Request):
    """Check current authentication status"""
    authenticated = verify_admin_session(request)
    return AuthResponse(authenticated=authenticated)


# Dashboard API Routes

@router.get("/dashboard", response_model=DashboardResponse)
async def api_dashboard(request: Request, _: None = Depends(require_admin_auth)):
    """Get dashboard data with client summary"""
    db: DatabaseService = request.app.state.db
    clients = await db.list_clients()
    
    # Discover tools to get accurate count (only if not already registered)
    if not tool_registry._tools:
        tool_registry.discover_tools()
    available_tools_count = len(tool_registry._tools)
    
    # Enhance client data with counts
    enhanced_clients = []
    total_api_keys = 0
    total_tools = 0
    
    for client in clients:
        api_keys = await db.list_api_keys_for_client(client.id)
        tool_configs = await db.list_tool_configurations_for_client(client.id)
        
        active_keys = len([key for key in api_keys if key.is_active])
        total_api_keys += active_keys
        total_tools += len(tool_configs)
        
        enhanced_clients.append(ClientSummary(
            id=str(client.id),
            name=client.name,
            description=client.description,
            api_key_count=active_keys,
            tool_count=len(tool_configs),
            created_at=client.created_at,
            is_active=client.is_active
        ))
    
    return DashboardResponse(
        clients=enhanced_clients,
        total_api_keys=total_api_keys,
        total_tools=total_tools,
        available_tools=available_tools_count
    )


@router.get("/clients/{client_id}", response_model=ClientDetailResponse)
async def api_client_detail(request: Request, client_id: str, _: None = Depends(require_admin_auth)):
    """Get detailed client information with API keys, tools, and resources"""
    db: DatabaseService = request.app.state.db
    
    # Get client
    client = await db.get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get API keys
    api_keys = await db.list_api_keys_for_client(client_id)
    api_key_summaries = [
        ApiKeySummary(
            id=key.id,
            key_value=key.key_value,
            name=key.name,
            created_at=key.created_at,
            expires_at=key.expires_at,
            is_active=key.is_active
        )
        for key in api_keys
    ]
    
    # Get tool configurations
    tool_configs = await db.list_tool_configurations_for_client(client_id)
    configured_tools = {config.tool_name: config for config in tool_configs}
    
    # Get all available tools and their config schemas (only discover if not already registered)
    if not tool_registry._tools:
        tool_registry.discover_tools()
    available_tools = tool_registry._tools.keys()
    tool_schemas = tool_registry.get_tool_config_schemas()
    
    # Build tool data
    tools = []
    for tool_name in available_tools:
        config = configured_tools.get(tool_name)
        schema = tool_schemas.get(tool_name)
        
        # Get tool description from the tool instance
        tool_description = None
        tool_instance = tool_registry._tools.get(tool_name)
        if tool_instance:
            tool_description = tool_instance.description
        
        tools.append(ToolInfo(
            name=tool_name,
            description=tool_description,
            requires_config=schema is not None,
            config_schema=schema,
            is_configured=config is not None,
            configuration=config.configuration if config else None
        ))
    
    # Get resource configurations
    resource_configs = await db.list_resource_configurations_for_client(client_id)
    configured_resources = {config.resource_name: config for config in resource_configs}
    
    # Get all available resources and their config schemas (only discover if not already registered)
    if not resource_registry._resources:
        resource_registry.discover_resources()
    available_resources = resource_registry._resources.keys()
    resource_schemas = resource_registry.get_resource_config_schemas()
    
    # Build resource data
    resources = []
    for resource_name in available_resources:
        config = configured_resources.get(resource_name)
        schema = resource_schemas.get(resource_name)
        
        resources.append(ResourceInfo(
            name=resource_name,
            requires_config=schema is not None,
            config_schema=schema,
            is_configured=config is not None,
            configuration=config.configuration if config else None
        ))
    
    # Build client summary
    client_summary = ClientSummary(
        id=str(client.id),
        name=client.name,
        description=client.description,
        api_key_count=len([key for key in api_keys if key.is_active]),
        tool_count=len(tool_configs),
        created_at=client.created_at,
        is_active=client.is_active
    )
    
    return ClientDetailResponse(
        client=client_summary,
        api_keys=api_key_summaries,
        tools=tools,
        resources=resources
    )


@router.post("/clients", response_model=ClientSummary)
async def api_create_client(
    request: Request,
    client_data: CreateClientRequest,
    _: None = Depends(require_admin_auth)
):
    """Create a new client"""
    db: DatabaseService = request.app.state.db
    client = await db.create_client(client_data.name, client_data.description)
    
    if not client:
        raise HTTPException(status_code=500, detail="Failed to create client")
    
    return ClientSummary(
        id=str(client.id),
        name=client.name,
        description=client.description,
        api_key_count=0,  # New client has no API keys yet
        tool_count=0,     # New client has no tools configured yet
        created_at=client.created_at,
        is_active=client.is_active
    )


@router.put("/clients/{client_id}", response_model=ClientSummary)
async def api_update_client(
    request: Request,
    client_id: str,
    client_data: CreateClientRequest,
    _: None = Depends(require_admin_auth)
):
    """Update an existing client"""
    db: DatabaseService = request.app.state.db
    
    # Update client
    success = await db.update_client(client_id, client_data.name, client_data.description)
    if not success:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get updated client
    client = await db.get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get current counts
    api_keys = await db.list_api_keys_for_client(client_id)
    tool_configs = await db.list_tool_configurations_for_client(client_id)
    
    return ClientSummary(
        id=str(client.id),
        name=client.name,
        description=client.description,
        api_key_count=len([key for key in api_keys if key.is_active]),
        tool_count=len(tool_configs),
        created_at=client.created_at,
        is_active=client.is_active
    )


# API Key Management Routes

@router.post("/clients/{client_id}/keys", response_model=ApiKeySummary)
async def create_api_key(
    request: Request,
    client_id: str,
    key_data: CreateApiKeyRequest,
    _: None = Depends(require_admin_auth)
):
    """Generate a new API key for a client"""
    db: DatabaseService = request.app.state.db
    
    # Generate secure API key
    api_key = secrets.token_urlsafe(32)
    
    # Calculate expiry date if provided
    expires_at = None
    if key_data.expires_days:
        expires_at = datetime.now() + timedelta(days=key_data.expires_days)
    
    # Create API key
    key = await db.create_api_key(client_id, api_key, key_data.name, expires_at)
    if not key:
        raise HTTPException(status_code=500, detail="Failed to create API key")
    
    return ApiKeySummary(
        id=key.id,
        key_value=key.key_value,
        name=key.name,
        created_at=key.created_at,
        expires_at=key.expires_at,
        is_active=key.is_active
    )


@router.delete("/keys/{api_key}")
async def delete_api_key(request: Request, api_key: str, _: None = Depends(require_admin_auth)):
    """Delete an API key"""
    db: DatabaseService = request.app.state.db
    success = await db.delete_api_key(api_key)
    
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {"success": True, "message": "API key deleted"}


# Tool Configuration Routes

@router.post("/clients/{client_id}/tools/{tool_name:path}")
async def configure_tool(
    request: Request,
    client_id: str,
    tool_name: str,
    _: None = Depends(require_admin_auth)
):
    """Configure a tool for a client"""
    db: DatabaseService = request.app.state.db
    
    # Get request body
    body = await request.body()
    try:
        data = json.loads(body)
        configuration = data.get("configuration")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Set tool configuration
    success = await db.set_tool_configuration(client_id, tool_name, configuration)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to configure tool")
    
    # Clear cache for this client's tools
    clear_config_cache(client_id, "tools")
    
    return {"success": True, "message": f"Tool {tool_name} configured"}


@router.delete("/clients/{client_id}/tools/{tool_name:path}")
async def delete_tool_configuration(
    request: Request,
    client_id: str,
    tool_name: str,
    _: None = Depends(require_admin_auth)
):
    """Remove tool configuration for a client"""
    db: DatabaseService = request.app.state.db
    success = await db.delete_tool_configuration(client_id, tool_name)
    
    if not success:
        raise HTTPException(status_code=404, detail="Tool configuration not found")
    
    # Clear cache for this client's tools
    clear_config_cache(client_id, "tools")
    
    return {"success": True, "message": f"Tool {tool_name} configuration removed"}


@router.get("/clients")
async def list_clients(request: Request, _: None = Depends(require_admin_auth)):
    """List all active clients (API endpoint)"""
    db: DatabaseService = request.app.state.db
    clients = await db.list_clients()
    return [client.to_dict() for client in clients]


@router.delete("/clients/{client_id}")
async def delete_client(request: Request, client_id: str, _: None = Depends(require_admin_auth)):
    """Delete a client"""
    db: DatabaseService = request.app.state.db
    success = await db.delete_client(client_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return {"success": True, "message": f"Client {client_id} deleted"}


# Resource Configuration Routes

@router.post("/clients/{client_id}/resources/{resource_name:path}")
async def configure_resource(
    request: Request,
    client_id: str,
    resource_name: str,
    _: None = Depends(require_admin_auth)
):
    """Configure a resource for a client"""
    db: DatabaseService = request.app.state.db
    
    # Get request body
    body = await request.body()
    try:
        data = json.loads(body)
        configuration = data.get("configuration")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Set resource configuration
    success = await db.set_resource_configuration(client_id, resource_name, configuration)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to configure resource")
    
    # Clear cache for this client's resources
    clear_config_cache(client_id, "resources")
    
    return {"success": True, "message": f"Resource {resource_name} configured"}


@router.delete("/clients/{client_id}/resources/{resource_name:path}")
async def delete_resource_configuration(
    request: Request,
    client_id: str,
    resource_name: str,
    _: None = Depends(require_admin_auth)
):
    """Remove resource configuration for a client"""
    db: DatabaseService = request.app.state.db
    success = await db.delete_resource_configuration(client_id, resource_name)
    
    if not success:
        raise HTTPException(status_code=404, detail="Resource configuration not found")
    
    # Clear cache for this client's resources
    clear_config_cache(client_id, "resources")
    
    return {"success": True, "message": f"Resource {resource_name} configuration removed"}


# Tool Call Analytics Routes

class ToolCallSummary(BaseModel):
    """Tool call summary response model"""
    id: int
    client_id: str
    tool_name: str
    input_data: Any  # Can be dict or list or other types
    output_text: Optional[Any]  # Text/content array responses
    output_json: Optional[Any]  # Structured JSON responses
    error_message: Optional[str]
    execution_time_ms: Optional[int]
    created_at: datetime
    

class ToolCallListResponse(BaseModel):
    """Tool call list response with pagination"""
    tool_calls: List[ToolCallSummary]
    total_count: int
    limit: int
    offset: int
    

class ToolCallStatsResponse(BaseModel):
    """Tool call statistics response"""
    total_calls: int
    successful_calls: int
    failed_calls: int
    success_rate: float
    avg_execution_time_ms: Optional[float]
    top_tools: List[Dict[str, Any]]
    period_days: int


@router.get("/tool-calls", response_model=ToolCallListResponse)
async def list_tool_calls(
    request: Request,
    client_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    order_by: str = "created_at",
    order_dir: str = "desc",
    _: None = Depends(require_admin_auth)
):
    """List tool calls with pagination and filtering"""
    db: DatabaseService = request.app.state.db
    
    # Validate limit and offset
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be non-negative")
    
    # Validate order parameters
    valid_order_by = ["created_at", "tool_name", "execution_time_ms"]
    if order_by not in valid_order_by:
        raise HTTPException(status_code=400, detail=f"order_by must be one of {valid_order_by}")
    
    if order_dir not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="order_dir must be 'asc' or 'desc'")
    
    # Get tool calls
    tool_calls, total_count = await db.list_tool_calls(
        client_id=client_id,
        tool_name=tool_name,
        search=search,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_dir=order_dir
    )
    
    # Convert to response format
    tool_call_summaries = [
        ToolCallSummary(
            id=call.id,
            client_id=str(call.client_id),
            tool_name=call.tool_name,
            input_data=call.input_data,
            output_text=call.output_text,
            output_json=call.output_json,
            error_message=call.error_message,
            execution_time_ms=call.execution_time_ms,
            created_at=call.created_at
        )
        for call in tool_calls
    ]
    
    return ToolCallListResponse(
        tool_calls=tool_call_summaries,
        total_count=total_count,
        limit=limit,
        offset=offset
    )


@router.get("/tool-calls/stats", response_model=ToolCallStatsResponse)
async def get_tool_call_stats(
    request: Request,
    client_id: Optional[str] = None,
    days: int = 30,
    _: None = Depends(require_admin_auth)
):
    """Get tool call statistics"""
    db: DatabaseService = request.app.state.db
    
    # Validate days parameter
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
    
    # Get statistics
    stats = await db.get_tool_call_stats(client_id=client_id, days=days)
    
    return ToolCallStatsResponse(**stats)


@router.get("/clients/{client_id}/tool-calls", response_model=ToolCallListResponse)
async def list_client_tool_calls(
    request: Request,
    client_id: str,
    tool_name: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    order_by: str = "created_at",
    order_dir: str = "desc",
    _: None = Depends(require_admin_auth)
):
    """List tool calls for a specific client"""
    # This is a convenience endpoint that calls list_tool_calls with client_id
    return await list_tool_calls(
        request=request,
        client_id=client_id,
        tool_name=tool_name,
        search=search,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_dir=order_dir,
        _=_
    )


@router.get("/clients/{client_id}/tool-calls/stats", response_model=ToolCallStatsResponse)
async def get_client_tool_call_stats(
    request: Request,
    client_id: str,
    days: int = 30,
    _: None = Depends(require_admin_auth)
):
    """Get tool call statistics for a specific client"""
    # This is a convenience endpoint that calls get_tool_call_stats with client_id
    return await get_tool_call_stats(
        request=request,
        client_id=client_id,
        days=days,
        _=_
    )


# System Monitoring Routes

class QueueMetricsResponse(BaseModel):
    """Queue metrics response model"""
    queue_depth: int
    max_workers: int
    max_queue_size: int
    workers_started: int
    is_started: bool
    utilization_percent: float
    active_workers: int
    total_tasks_processed: int
    peak_queue_depth: int
    peak_active_workers: int
    
class SystemHealthResponse(BaseModel):
    """System health response model"""
    database_status: str
    queue_metrics: QueueMetricsResponse
    timestamp: datetime


@router.get("/metrics/queue", response_model=QueueMetricsResponse)
async def get_queue_metrics(request: Request, _: None = Depends(require_admin_auth)):
    """Get current queue statistics"""
    from src.tools.registry import tool_registry
    
    stats = tool_registry.get_queue_stats()
    
    # Calculate utilization percentage
    utilization_percent = 0.0
    if stats["max_queue_size"] > 0:
        utilization_percent = (stats["queue_depth"] / stats["max_queue_size"]) * 100
    
    return QueueMetricsResponse(
        queue_depth=stats["queue_depth"],
        max_workers=stats["max_workers"], 
        max_queue_size=stats["max_queue_size"],
        workers_started=stats["workers_started"],
        is_started=stats["is_started"],
        utilization_percent=round(utilization_percent, 1),
        active_workers=stats["active_workers"],
        total_tasks_processed=stats["total_tasks_processed"],
        peak_queue_depth=stats["peak_queue_depth"],
        peak_active_workers=stats["peak_active_workers"]
    )


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(request: Request, _: None = Depends(require_admin_auth)):
    """Get overall system health status"""
    db: DatabaseService = request.app.state.db
    
    # Check database health
    db_healthy = await db.health_check()
    db_status = "connected" if db_healthy else "disconnected"
    
    # Get queue metrics
    queue_metrics = await get_queue_metrics(request, _)
    
    return SystemHealthResponse(
        database_status=db_status,
        queue_metrics=queue_metrics,
        timestamp=datetime.now()
    )


# Admin Management Routes

class AdminSummary(BaseModel):
    """Admin summary response model"""
    id: int
    username: str
    email: str
    created_at: datetime
    created_by_username: Optional[str]
    is_superadmin: bool

class CreateAdminRequest(BaseModel):
    """Request model for creating new admin"""
    username: str
    email: str
    password: str

class ChangePasswordRequest(BaseModel):
    """Request model for changing admin password"""
    new_password: str

class AdminListResponse(BaseModel):
    """Admin list response model"""
    admins: List[AdminSummary]
    current_admin: str


@router.get("/admins", response_model=AdminListResponse)
async def list_admins(request: Request, _: None = Depends(require_admin_auth)):
    """List all admins"""
    db: DatabaseService = request.app.state.db
    admins = await db.list_admins()
    current_username = get_current_admin_username(request)
    
    # Build admin summaries with created_by info
    admin_summaries = []
    for admin in admins:
        created_by_username = None
        if admin.created_by_id:
            # Get creator info
            for creator in admins:
                if creator.id == admin.created_by_id:
                    created_by_username = creator.username
                    break
        
        admin_summaries.append(AdminSummary(
            id=admin.id,
            username=admin.username,
            email=admin.email,
            created_at=admin.created_at,
            created_by_username=created_by_username,
            is_superadmin=(admin.username == "superadmin")
        ))
    
    return AdminListResponse(
        admins=admin_summaries,
        current_admin=current_username
    )


@router.post("/admins")
async def create_admin(request: Request, admin_data: CreateAdminRequest, _: None = Depends(require_admin_auth)):
    """Create a new admin user"""
    db: DatabaseService = request.app.state.db
    
    # Get current admin ID from session
    current_admin_id = request.session.get("admin_id")
    if not current_admin_id:
        raise HTTPException(status_code=500, detail="Session error: admin ID not found")
    
    # Check if username already exists
    existing = await db.get_admin_by_username(admin_data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create admin
    admin = await db.create_admin(
        username=admin_data.username,
        email=admin_data.email,
        password=admin_data.password,
        created_by_id=current_admin_id
    )
    
    if not admin:
        raise HTTPException(status_code=500, detail="Failed to create admin")
    
    return {"success": True, "message": f"Admin '{admin_data.username}' created successfully"}


@router.delete("/admins/{username}")
async def delete_admin(request: Request, username: str, _: None = Depends(require_admin_auth)):
    """Delete an admin user (except superadmin)"""
    db: DatabaseService = request.app.state.db
    
    if username == "superadmin":
        raise HTTPException(status_code=400, detail="Cannot delete superadmin")
    
    current_username = get_current_admin_username(request)
    if username == current_username:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    success = await db.delete_admin(username)
    if not success:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    return {"success": True, "message": f"Admin '{username}' deleted successfully"}


@router.post("/admins/{username}/change-password")
async def change_admin_password(
    request: Request, 
    username: str, 
    password_data: ChangePasswordRequest, 
    _: None = Depends(require_admin_auth)
):
    """Change password for an admin (admins can only change their own password)"""
    db: DatabaseService = request.app.state.db
    
    current_username = get_current_admin_username(request)
    if username != current_username:
        raise HTTPException(status_code=403, detail="You can only change your own password")
    
    success = await db.change_admin_password(username, password_data.new_password)
    if not success:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    return {"success": True, "message": "Password changed successfully"}


# System Prompt API Routes

@router.get("/clients/{client_id}/prompts", response_model=List[SystemPromptSummary])
async def get_client_prompts(client_id: str, request: Request, admin: str = Depends(require_admin_auth)):
    """Get all system prompts for a client"""
    db: DatabaseService = request.app.state.db
    
    try:
        # Validate UUID format
        try:
            uuid.UUID(client_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid client ID format: {client_id}")
            
        prompts = await db.list_system_prompts(client_id)
        return [
            SystemPromptSummary(
                id=prompt.id,
                version=prompt.version,
                user_requirements=prompt.user_requirements,
                is_active=prompt.is_active,
                created_at=prompt.created_at,
                updated_at=prompt.updated_at
            )
            for prompt in prompts
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clients/{client_id}/prompts/generate")
async def generate_system_prompt_endpoint(
    client_id: str, 
    request: Request, 
    generate_request: GeneratePromptRequest,
    admin: str = Depends(require_admin_auth)
):
    """Generate a new system prompt using LLM"""
    db: DatabaseService = request.app.state.db
    
    try:
        # Validate UUID format
        try:
            uuid.UUID(client_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid client ID format: {client_id}")
        # Get client and their configurations
        client = await db.get_client(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get tool configurations for this client
        tool_configs = await db.get_tool_configurations(client.id)
        enabled_tools = list(tool_configs.keys())
        
        # Get resource configurations for this client
        resource_configs = await db.get_resource_configurations(client.id)
        enabled_resources = list(resource_configs.keys())
        
        # Get previous prompt if this is a revision
        previous_prompt = None
        if generate_request.is_revision and generate_request.parent_version_id:
            parent_prompt = await db.get_system_prompt(generate_request.parent_version_id)
            if parent_prompt:
                previous_prompt = parent_prompt.prompt_text
        
        # Generate the prompt using utility function
        generated_prompt = await generate_system_prompt(
            tool_registry=tool_registry,
            resource_registry=resource_registry,
            enabled_tools=enabled_tools,
            enabled_resources=enabled_resources,
            user_requirements=generate_request.user_requirements,
            is_revision=generate_request.is_revision,
            previous_prompt=previous_prompt
        )
        
        return {"prompt_text": generated_prompt}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clients/{client_id}/prompts", response_model=SystemPromptResponse)
async def save_system_prompt(
    client_id: str,
    request: Request,
    save_request: SavePromptRequest,
    admin: str = Depends(require_admin_auth)
):
    """Save a system prompt"""
    db: DatabaseService = request.app.state.db
    
    try:
        # Validate UUID format
        try:
            uuid.UUID(client_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid client ID format: {client_id}")
        prompt = await db.create_system_prompt(
            client_id=client_id,
            prompt_text=save_request.prompt_text,
            user_requirements=save_request.user_requirements,
            generation_context=save_request.generation_context,
            parent_version_id=save_request.parent_version_id
        )
        
        return SystemPromptResponse(
            id=prompt.id,
            client_id=str(prompt.client_id),
            prompt_text=prompt.prompt_text,
            version=prompt.version,
            user_requirements=prompt.user_requirements,
            generation_context=prompt.generation_context,
            is_active=prompt.is_active,
            parent_version_id=prompt.parent_version_id,
            created_at=prompt.created_at,
            updated_at=prompt.updated_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts/{prompt_id}", response_model=SystemPromptResponse)
async def get_system_prompt(prompt_id: int, request: Request, admin: str = Depends(require_admin_auth)):
    """Get a specific system prompt by ID"""
    db: DatabaseService = request.app.state.db
    
    try:
        prompt = await db.get_system_prompt(prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="System prompt not found")
            
        return SystemPromptResponse(
            id=prompt.id,
            client_id=str(prompt.client_id),
            prompt_text=prompt.prompt_text,
            version=prompt.version,
            user_requirements=prompt.user_requirements,
            generation_context=prompt.generation_context,
            is_active=prompt.is_active,
            parent_version_id=prompt.parent_version_id,
            created_at=prompt.created_at,
            updated_at=prompt.updated_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/clients/{client_id}/prompts/active/{prompt_id}")
async def set_active_system_prompt(
    client_id: str,
    prompt_id: int,
    request: Request,
    admin: str = Depends(require_admin_auth)
):
    """Set a system prompt as active"""
    db: DatabaseService = request.app.state.db
    
    try:
        # Validate UUID format
        try:
            uuid.UUID(client_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid client ID format: {client_id}")
        success = await db.set_active_system_prompt(client_id, prompt_id)
        if not success:
            raise HTTPException(status_code=404, detail="System prompt not found or doesn't belong to client")
            
        return {"success": True, "message": "System prompt activated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))