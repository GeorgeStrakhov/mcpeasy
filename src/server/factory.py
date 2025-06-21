"""
MCP Server Factory - Creates and manages MCP server instances
"""
from typing import Dict, Any, Optional
from fastapi import Request, Response, BackgroundTasks
from fastmcp import FastMCP
import json
import logging
import time
from functools import lru_cache

from ..database import DatabaseService
from ..resources.registry import resource_registry
from ..tools.registry import tool_registry

logger = logging.getLogger(__name__)

# Simple in-memory cache with TTL
_config_cache = {}
_cache_ttl = 300  # 5 minutes


def _get_cached_config(client_id: str, config_type: str, db: DatabaseService):
    """Get cached configuration with TTL"""
    cache_key = f"{client_id}:{config_type}"
    current_time = time.time()
    
    # Check if we have valid cached data
    if cache_key in _config_cache:
        cached_data, cache_time = _config_cache[cache_key]
        if current_time - cache_time < _cache_ttl:
            logger.debug(f"Cache hit for {cache_key}")
            return cached_data
    
    # Cache miss or expired, will be filled by caller
    logger.debug(f"Cache miss for {cache_key}")
    return None

def _set_cached_config(client_id: str, config_type: str, data: Any):
    """Set cached configuration with current timestamp"""
    cache_key = f"{client_id}:{config_type}"
    _config_cache[cache_key] = (data, time.time())
    logger.debug(f"Cached {config_type} config for client {client_id}")

def clear_config_cache(client_id: str = None, config_type: str = None):
    """Clear configuration cache for a specific client/config type or all"""
    global _config_cache
    
    if client_id and config_type:
        # Clear specific cache entry
        cache_key = f"{client_id}:{config_type}"
        if cache_key in _config_cache:
            del _config_cache[cache_key]
            logger.debug(f"Cleared cache for {cache_key}")
    elif client_id:
        # Clear all cache entries for a client
        keys_to_delete = [k for k in _config_cache.keys() if k.startswith(f"{client_id}:")]
        for key in keys_to_delete:
            del _config_cache[key]
        logger.debug(f"Cleared all cache entries for client {client_id}")
    else:
        # Clear entire cache
        _config_cache.clear()
        logger.debug("Cleared entire configuration cache")

class MCPServerInstance:
    """Wrapper for individual MCP server instances with direct FastMCP handling"""
    
    def __init__(self, config: Dict[str, Any], db: DatabaseService):
        self.config = config
        self.db = db
        logger.info(f"Creating MCP server instance: {config.get('name', 'default')}")
        logger.debug(f"Server config: {config}")
        self.mcp = FastMCP(config.get("name", "default"))
        
        # Initialize resource registry with database
        resource_registry.initialize(db)
        
        # Discover and initialize tools
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup tools based on configuration using the new modular system"""
        # Discover all available tools (this loads them into the registry)
        tool_registry.discover_tools()
        logger.debug(f"Tools discovered in registry: {list(tool_registry._tools.keys())}")
        
        # Tools will be filtered by enabled_tools when listing/calling them
        enabled_tools = self.config.get("enabled_tools", [])
        logger.info(f"Enabled tools for this server: {enabled_tools}")
    
    
    async def handle_request(self, request: Request, background_tasks: BackgroundTasks = None) -> Response:
        """
        Handle MCP request by directly using FastMCP's server capabilities
        without the ASGI wrapper (which requires lifespan management)
        """
        logger.debug(f"Handling {request.method} request to MCP server")
        logger.debug(f"Request headers: {dict(request.headers)}")
        
        # Get request body
        body = await request.body()
        logger.debug(f"Request body length: {len(body)}")
        
        if request.method == "GET":
            # Handle capability discovery
            capabilities = {
                "protocolVersion": "2025-03-26",
                "capabilities": {
                    "tools": {
                        "listChanged": True
                    },
                    "resources": {
                        "listChanged": True
                    },
                    "prompts": {
                        "listChanged": True
                    },
                    "logging": {},
                    "experimental": {
                        "streaming": True
                    }
                },
                "serverInfo": {
                    "name": self.config.get("name", "mcp-server"),
                    "version": "1.0.0"
                }
            }
            
            return Response(
                content=json.dumps(capabilities),
                status_code=200,
                media_type="application/json",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                    "Cache-Control": "no-cache",
                }
            )
            
        elif request.method == "POST":
            # Handle JSON-RPC requests
            try:
                if body:
                    request_data = json.loads(body.decode())
                    method = request_data.get("method")
                    logger.info(f"Processing MCP method: {method}")
                    logger.debug(f"Request data: {request_data}")
                    
                    if method == "initialize":
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_data.get("id"),
                            "result": {
                                "protocolVersion": "2025-03-26",
                                "capabilities": {
                                    "tools": {
                                        "listChanged": True
                                    },
                                    "resources": {
                                        "listChanged": True
                                    },
                                    "prompts": {
                                        "listChanged": True
                                    },
                                    "logging": {},
                                    "experimental": {
                                        "streaming": True
                                    }
                                },
                                "serverInfo": {
                                    "name": self.config.get("name", "mcp-server"),
                                    "version": "1.0.0"
                                }
                            }
                        }
                    elif method == "notifications/initialized":
                        # Handle initialized notification
                        logger.debug("Received initialized notification")
                        response = None  # No response needed for notifications
                    elif method == "ping":
                        # Handle ping requests
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_data.get("id"),
                            "result": {}
                        }
                    elif method == "resources/list":
                        # List available resources for this client
                        client = await self._get_client_from_request(request)
                        if not client:
                            response = {
                                "jsonrpc": "2.0",
                                "id": request_data.get("id"),
                                "error": {
                                    "code": -32603,
                                    "message": "Invalid API key"
                                }
                            }
                        else:
                            # Get configured resources for this client (with caching)
                            resource_configs = _get_cached_config(str(client.id), "resources", self.db)
                            if resource_configs is None:
                                resource_configs = await self.db.get_resource_configurations(client.id)
                                _set_cached_config(str(client.id), "resources", resource_configs)
                            enabled_resources = list(resource_configs.keys())
                            
                            logger.debug(f"Listing resources for client {client.name}, enabled: {enabled_resources}")
                            
                            resources = await resource_registry.list_resources(enabled_resources, resource_configs)
                            
                            response = {
                                "jsonrpc": "2.0",
                                "id": request_data.get("id"),
                                "result": {
                                    "resources": [resource.to_dict() for resource in resources]
                                }
                            }
                    elif method == "resources/read":
                        # Read resource content
                        params = request_data.get("params", {})
                        uri = params.get("uri")
                        
                        if not uri:
                            response = {
                                "jsonrpc": "2.0",
                                "id": request_data.get("id"),
                                "error": {
                                    "code": -32602,
                                    "message": "Missing required parameter: uri"
                                }
                            }
                        else:
                            # Get client and their resource configurations
                            client = await self._get_client_from_request(request)
                            if not client:
                                response = {
                                    "jsonrpc": "2.0",
                                    "id": request_data.get("id"),
                                    "error": {
                                        "code": -32603,
                                        "message": "Invalid API key"
                                    }
                                }
                            else:
                                # Get resource configurations for this client (with caching)
                                resource_configs = _get_cached_config(str(client.id), "resources", self.db)
                                if resource_configs is None:
                                    resource_configs = await self.db.get_resource_configurations(client.id)
                                    _set_cached_config(str(client.id), "resources", resource_configs)
                                enabled_resources = list(resource_configs.keys())
                                
                                resource_content = await resource_registry.read_resource(uri, enabled_resources, resource_configs)
                                
                                if resource_content:
                                    response = {
                                        "jsonrpc": "2.0",
                                        "id": request_data.get("id"),
                                        "result": {
                                            "contents": [resource_content.to_dict()]
                                        }
                                    }
                                else:
                                    response = {
                                        "jsonrpc": "2.0",
                                        "id": request_data.get("id"),
                                        "error": {
                                            "code": -32603,
                                            "message": f"Resource not found or not accessible: {uri}"
                                        }
                                    }
                    elif method == "prompts/list":
                        # List available prompts (empty for now)
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_data.get("id"),
                            "result": {
                                "prompts": []
                            }
                        }
                    elif method == "tools/list":
                        # List available tools for this client
                        # Get client and their tool configurations
                        client = await self._get_client_from_request(request)
                        if not client:
                            response = {
                                "jsonrpc": "2.0",
                                "id": request_data.get("id"),
                                "error": {
                                    "code": -32603,
                                    "message": "Invalid API key"
                                }
                            }
                        else:
                            # Get configured tools for this client (with caching)
                            tool_configs = _get_cached_config(str(client.id), "tools", self.db)
                            if tool_configs is None:
                                tool_configs = await self.db.get_tool_configurations(client.id)
                                _set_cached_config(str(client.id), "tools", tool_configs)
                            enabled_tools = list(tool_configs.keys())
                            
                            logger.debug(f"Listing tools for client {client.name}, enabled: {enabled_tools}")
                            
                            # Only show tools that are explicitly configured for this client
                            tool_schemas = tool_registry.list_tools(enabled_tools)
                            tools = [schema.dict(by_alias=True) for schema in tool_schemas]
                            
                            response = {
                                "jsonrpc": "2.0",
                                "id": request_data.get("id"),
                                "result": {
                                    "tools": tools
                                }
                            }
                    elif method == "tools/call":
                        # Handle tool calls using the new modular system
                        params = request_data.get("params", {})
                        tool_name = params.get("name")
                        tool_args = params.get("arguments", {})
                        
                        # Get client and their tool configurations
                        client = await self._get_client_from_request(request)
                        if not client:
                            response = {
                                "jsonrpc": "2.0",
                                "id": request_data.get("id"),
                                "error": {
                                    "code": -32603,
                                    "message": "Invalid API key"
                                }
                            }
                        else:
                            # Get tool configurations for this client (with caching)
                            tool_configs = _get_cached_config(str(client.id), "tools", self.db)
                            if tool_configs is None:
                                tool_configs = await self.db.get_tool_configurations(client.id)
                                _set_cached_config(str(client.id), "tools", tool_configs)
                            
                            # Check if tool is explicitly configured for this client
                            if tool_name not in tool_configs:
                                response = {
                                    "jsonrpc": "2.0",
                                    "id": request_data.get("id"),
                                    "error": {
                                        "code": -32602,
                                        "message": f"Tool '{tool_name}' is not configured for this client"
                                    }
                                }
                            else:
                                # Get tool-specific configuration for this client
                                tool_config = tool_configs.get(tool_name, {})
                                
                                # Get API key for context
                                api_key = request.path_params.get("token")
                                
                                # Create context for tool call tracking
                                context = {
                                    'db': self.db,
                                    'client': client,
                                    'api_key': api_key
                                }
                                
                                # Execute tool using registry with client configuration and tracking context
                                tool_result = await tool_registry.execute_tool(tool_name, tool_args, tool_config, context, background_tasks)
                                
                                if tool_result.is_error:
                                    response = {
                                        "jsonrpc": "2.0",
                                        "id": request_data.get("id"),
                                        "error": {
                                            "code": -32603,
                                            "message": tool_result.content[0]["text"] if tool_result.content else "Tool execution failed"
                                        }
                                    }
                                else:
                                    result_data = {"content": tool_result.content}
                                    
                                    # Include structuredContent if present
                                    if hasattr(tool_result, 'structured_content') and tool_result.structured_content is not None:
                                        result_data["structuredContent"] = tool_result.structured_content
                                    
                                    response = {
                                        "jsonrpc": "2.0",
                                        "id": request_data.get("id"),
                                        "result": result_data
                                    }
                    elif method == "logging/setLevel":
                        # Handle logging level changes
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_data.get("id"),
                            "result": {}
                        }
                    elif method == "completion/complete":
                        # Handle completion requests (optional)
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_data.get("id"),
                            "result": {
                                "completion": {
                                    "values": [],
                                    "total": 0,
                                    "hasMore": False
                                }
                            }
                        }
                    else:
                        # Unknown method
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_data.get("id"),
                            "error": {
                                "code": -32601,
                                "message": f"Method not found: {method}"
                            }
                        }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32600,
                            "message": "Invalid request"
                        }
                    }
                
                logger.debug(f"MCP response: {response}")
                
                # Handle notifications (no response needed)
                if response is None:
                    return Response(
                        content="",
                        status_code=200,
                        media_type="application/json",
                        headers={
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                            "Access-Control-Allow-Headers": "Content-Type, Authorization",
                            "Cache-Control": "no-cache",
                        }
                    )
                
                return Response(
                    content=json.dumps(response),
                    status_code=200,
                    media_type="application/json",
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization",
                        "Cache-Control": "no-cache",
                    }
                )
                
            except Exception as e:
                logger.error(f"Error in MCP tool handling: {e}", exc_info=True)
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                
                return Response(
                    content=json.dumps(error_response),
                    status_code=500,
                    media_type="application/json",
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization",
                    }
                )
    
    async def _get_client_from_request(self, request: Request):
        """Extract API key from URL and lookup client"""
        # Extract API key from URL path
        api_key = request.path_params.get("token")  # Using 'token' path param for backward compatibility
        if not api_key:
            return None
        
        # Lookup client by API key
        client = await self.db.get_client_by_api_key(api_key)
        return client


class MCPServerFactory:
    """Factory for creating and caching MCP server instances"""
    
    def __init__(self, db: DatabaseService):
        self.db = db
        self._servers: Dict[str, MCPServerInstance] = {}
    
    async def get_server(self, api_key: str) -> Optional[MCPServerInstance]:
        """Get or create MCP server instance based on API key"""
        # Get client by API key
        client = await self.db.get_client_by_api_key(api_key)
        if not client:
            return None
        
        # Use client ID as cache key
        cache_key = f"client_{client.id}"
        
        if cache_key not in self._servers:
            # Create legacy config format for backward compatibility
            config = {
                "name": client.name,
                "client_id": client.id,
                "version": "2.0"
            }
            self._servers[cache_key] = MCPServerInstance(config, self.db)
        
        return self._servers[cache_key]
    
    async def get_server_legacy(self, config: Dict[str, Any]) -> MCPServerInstance:
        """Legacy method for backward compatibility"""
        config_key = self._get_config_key(config)
        
        if config_key not in self._servers:
            self._servers[config_key] = MCPServerInstance(config, self.db)
        
        return self._servers[config_key]
    
    def _get_config_key(self, config: Dict[str, Any]) -> str:
        """Generate a unique key for the configuration"""
        # Create a stable key based on configuration
        key_parts = [
            config.get("name", "default"),
            "-".join(sorted(config.get("enabled_tools", []))),
            str(config.get("version", "1.0"))
        ]
        return ":".join(key_parts)