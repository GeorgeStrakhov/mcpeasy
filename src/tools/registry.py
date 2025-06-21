"""
Tool registry for dynamic tool discovery and management
"""

import logging
import importlib
import pkgutil
import yaml
import os
from typing import Dict, List, Optional, Type, Any
from pathlib import Path

from .base import BaseTool, ToolSchema, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing and discovering MCP tools"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
        self._deployment_config: Optional[Dict[str, Any]] = None
    
    def register_tool(self, tool_class: Type[BaseTool], custom_name: str = None) -> None:
        """Register a tool class with optional custom name for namespacing"""
        tool_instance = tool_class()
        tool_name = custom_name if custom_name else tool_instance.name
        
        if tool_name in self._tools:
            logger.warning(f"Tool '{tool_name}' already registered, overwriting")
        
        self._tools[tool_name] = tool_instance
        self._tool_classes[tool_name] = tool_class
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        return self._tools.get(name)
    
    def list_tools(self, enabled_tools: List[str] = None) -> List[ToolSchema]:
        """List available tools, optionally filtered by enabled_tools"""
        if enabled_tools is None:
            enabled_tools = list(self._tools.keys())
        
        schemas = []
        for tool_name in enabled_tools:
            if tool_name in self._tools:
                tool = self._tools[tool_name]
                schema = tool.get_schema()
                # For custom tools, override the name to include the org prefix
                if "/" in tool_name:  # Custom tool
                    schema.name = tool_name
                schemas.append(schema)
            else:
                logger.warning(f"Enabled tool '{tool_name}' not found in registry")
        
        return schemas
    
    def _load_deployment_config(self) -> Dict[str, Any]:
        """Load deployment configuration from YAML file"""
        if self._deployment_config is not None:
            return self._deployment_config
            
        # Determine config file path based on environment
        env = os.getenv("DEPLOYMENT_ENV", "default")
        config_file = f"config/deployment.{env}.yaml" if env != "default" else "config/deployment.yaml"
        config_path = Path(config_file)
        
        if not config_path.exists():
            logger.warning(f"Deployment config {config_path} not found, using default")
            config_path = Path("config/deployment.yaml")
        
        if not config_path.exists():
            logger.warning("No deployment config found, allowing all tools")
            return {"core_tools": [], "custom_tools": []}
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                self._deployment_config = config.get('deployment', {})
                logger.info(f"Loaded deployment config: {self._deployment_config.get('name', 'unknown')}")
                return self._deployment_config
        except Exception as e:
            logger.error(f"Error loading deployment config: {e}")
            return {"core_tools": [], "custom_tools": []}

    def discover_tools(self, tools_package: str = "src.tools") -> None:
        """Discover and register tools from core and custom directories"""
        try:
            # Load deployment configuration
            config = self._load_deployment_config()
            
            # Discover core tools
            core_tools = self._discover_core_tools(tools_package)
            
            # Discover custom tools
            custom_tools = self._discover_custom_tools("src/custom_tools")
            
            # Filter by deployment configuration
            all_discovered_tools = core_tools + custom_tools
            allowed_core_tools = config.get('core_tools', [])
            allowed_custom_tools = config.get('custom_tools', [])
            
            # Register filtered tools
            registered_count = 0
            for tool_class, tool_name in all_discovered_tools:
                # Check if tool is allowed in deployment
                if (tool_name in allowed_core_tools or 
                    any(tool_name == custom_tool for custom_tool in allowed_custom_tools)):
                    # For custom tools, register with the full org/tool_name
                    if "/" in tool_name:  # Custom tool
                        self.register_tool(tool_class, custom_name=tool_name)
                    else:  # Core tool
                        self.register_tool(tool_class)
                    registered_count += 1
                    logger.debug(f"Registered tool: {tool_name}")
                else:
                    logger.debug(f"Skipped tool not in deployment config: {tool_name}")
            
            logger.info(f"Registered {registered_count} tools from {len(all_discovered_tools)} discovered")
                    
        except Exception as e:
            logger.error(f"Error discovering tools: {e}")

    def _discover_core_tools(self, tools_package: str) -> List[tuple]:
        """Discover tools from the core tools package"""
        discovered_tools = []
        try:
            # Import the tools package
            package = importlib.import_module(tools_package)
            package_path = Path(package.__file__).parent
            
            # Walk through all subdirectories in the tools package
            for subdir in package_path.iterdir():
                if subdir.is_dir() and not subdir.name.startswith("__"):
                    tool_class = self._discover_tool_in_directory(tools_package, subdir.name)
                    if tool_class:
                        discovered_tools.append((tool_class, subdir.name))
            
            logger.debug(f"Discovered {len(discovered_tools)} core tools")
            return discovered_tools
                    
        except Exception as e:
            logger.error(f"Error discovering core tools: {e}")
            return []

    def _discover_custom_tools(self, base_path: str) -> List[tuple]:
        """Discover tools from custom tools directories (submodules)"""
        discovered_tools = []
        
        custom_tools_path = Path(base_path)
        if not custom_tools_path.exists():
            logger.debug("Custom tools directory does not exist")
            return []
        
        try:
            # Scan each organization's submodule
            for org_dir in custom_tools_path.iterdir():
                if org_dir.is_dir() and not org_dir.name.startswith('.') and org_dir.name != "__pycache__":
                    # Look for tools directory within the organization
                    tools_dir = org_dir / "tools"
                    if tools_dir.exists():
                        for tool_dir in tools_dir.iterdir():
                            if tool_dir.is_dir() and not tool_dir.name.startswith('.'):
                                tool_name = f"{org_dir.name}/{tool_dir.name}"
                                tool_class = self._discover_custom_tool_in_directory(base_path, org_dir.name, tool_dir.name)
                                if tool_class:
                                    discovered_tools.append((tool_class, tool_name))
            
            logger.debug(f"Discovered {len(discovered_tools)} custom tools")
            return discovered_tools
            
        except Exception as e:
            logger.error(f"Error discovering custom tools: {e}")
            return []
    
    def _discover_tool_in_directory(self, base_package: str, tool_dir: str) -> Optional[Type[BaseTool]]:
        """Discover a tool in a specific core directory"""
        try:
            # Try to import the tool module
            tool_module_name = f"{base_package}.{tool_dir}.tool"
            tool_module = importlib.import_module(tool_module_name)
            
            # Look for classes that inherit from BaseTool
            for attr_name in dir(tool_module):
                attr = getattr(tool_module, attr_name)
                if (isinstance(attr, type) and 
                    hasattr(attr, '__mro__') and
                    any(base.__name__ == 'BaseTool' for base in attr.__mro__) and
                    attr.__name__ != 'BaseTool'):
                    return attr
            return None
                    
        except ImportError:
            logger.debug(f"Could not import tool from {tool_dir}")
            return None
        except Exception as e:
            logger.error(f"Error discovering tool in {tool_dir}: {e}")
            return None

    def _discover_custom_tool_in_directory(self, base_path: str, org_name: str, tool_name: str) -> Optional[Type[BaseTool]]:
        """Discover a custom tool in a specific organization/tool directory"""
        try:
            # Construct module path for custom tool
            # e.g., src.custom_tools.acme.tools.invoice_generator.tool
            tool_module_name = f"{base_path.replace('/', '.')}.{org_name}.tools.{tool_name}.tool"
            tool_module = importlib.import_module(tool_module_name)
            
            # Look for classes that inherit from BaseTool
            for attr_name in dir(tool_module):
                attr = getattr(tool_module, attr_name)
                if (isinstance(attr, type) and 
                    hasattr(attr, '__mro__') and
                    any(base.__name__ == 'BaseTool' for base in attr.__mro__) and
                    attr.__name__ != 'BaseTool'):
                    return attr
            return None
                    
        except ImportError as e:
            logger.debug(f"Could not import custom tool {org_name}/{tool_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error discovering custom tool {org_name}/{tool_name}: {e}")
            return None
    
    async def execute_tool(self, name: str, arguments: Dict[str, any], config: Dict[str, any] = None, context: Dict[str, any] = None, background_tasks=None) -> ToolResult:
        """Execute a tool by name with given arguments and optional configuration"""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult.error(f"Tool '{name}' not found")
        
        # Validate arguments
        if not tool.validate_arguments(arguments):
            return ToolResult.error(f"Invalid arguments for tool '{name}'")
        
        try:
            # Add tracking context to the tool if it supports it
            if hasattr(tool, 'set_context'):
                tool.set_context(context or {})
            
            import time
            import asyncio
            start_time = time.time()
            
            # Execute tool with timeout
            try:
                result = await asyncio.wait_for(tool.execute(arguments, config), timeout=30.0)
            except asyncio.TimeoutError:
                logger.warning(f"Tool '{name}' execution timed out after 30 seconds")
                return ToolResult.error(f"Tool '{name}' execution timed out")
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Log tool call in background if context and background_tasks are provided
            if context and 'db' in context and 'client' in context and 'api_key' in context and background_tasks:
                background_tasks.add_task(
                    self._log_tool_call_background,
                    context=context,
                    tool_name=name,
                    arguments=arguments,
                    result=result,
                    execution_time_ms=execution_time_ms
                )
            elif context and 'db' in context and 'client' in context and 'api_key' in context:
                # Fallback to synchronous logging if no background_tasks provided
                await self._log_tool_call(
                    context=context,
                    tool_name=name,
                    arguments=arguments,
                    result=result,
                    execution_time_ms=execution_time_ms
                )
            
            return result
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000) if 'start_time' in locals() else 0
            
            # Log failed tool call in background
            if context and 'db' in context and 'client' in context and 'api_key' in context and background_tasks:
                error_result = ToolResult.error(f"Tool execution failed: {str(e)}")
                background_tasks.add_task(
                    self._log_tool_call_background,
                    context=context,
                    tool_name=name,
                    arguments=arguments,
                    result=error_result,
                    execution_time_ms=execution_time_ms
                )
            
            logger.error(f"Error executing tool '{name}': {e}")
            return ToolResult.error(f"Tool execution failed: {str(e)}")
    
    async def _log_tool_call(self, context: Dict[str, any], tool_name: str, arguments: Dict[str, any], result: ToolResult, execution_time_ms: int):
        """Log tool call to database (synchronous version)"""
        try:
            db = context.get('db')
            client = context.get('client')
            api_key = context.get('api_key')
            
            if not all([db, client, api_key]):
                return
                
            # Get API key record
            api_key_record = await db.get_api_key(api_key)
            if not api_key_record:
                return
                
            # Determine output data - store in appropriate column based on type
            output_text = None
            output_json = None
            if not result.is_error:
                if hasattr(result, 'structured_content') and result.structured_content is not None:
                    # For structured JSON responses, store in output_json
                    output_json = result.structured_content
                elif result.content:
                    # For text/content responses, store in output_text
                    output_text = result.content
            
            await db.create_tool_call(
                client_id=client.id,
                api_key_id=api_key_record.id,
                tool_name=tool_name,
                input_data=arguments,
                output_text=output_text,
                output_json=output_json,
                error_message=result.content[0]["text"] if result.is_error and result.content else None,
                execution_time_ms=execution_time_ms
            )
            logger.debug(f"Logged tool call: {tool_name} for client {client.name}")
            
        except Exception as e:
            logger.error(f"Failed to log tool call: {e}")
            # Don't fail the tool call if logging fails
    
    async def _log_tool_call_background(self, context: Dict[str, any], tool_name: str, arguments: Dict[str, any], result: ToolResult, execution_time_ms: int):
        """Log tool call to database (background task version)"""
        try:
            db = context.get('db')
            client = context.get('client')
            api_key = context.get('api_key')
            
            if not all([db, client, api_key]):
                return
                
            # Get API key record
            api_key_record = await db.get_api_key(api_key)
            if not api_key_record:
                return
                
            # Determine output data - store in appropriate column based on type
            output_text = None
            output_json = None
            if not result.is_error:
                if hasattr(result, 'structured_content') and result.structured_content is not None:
                    # For structured JSON responses, store in output_json
                    output_json = result.structured_content
                elif result.content:
                    # For text/content responses, store in output_text
                    output_text = result.content
            
            await db.create_tool_call(
                client_id=client.id,
                api_key_id=api_key_record.id,
                tool_name=tool_name,
                input_data=arguments,
                output_text=output_text,
                output_json=output_json,
                error_message=result.content[0]["text"] if result.is_error and result.content else None,
                execution_time_ms=execution_time_ms
            )
            logger.debug(f"Background logged tool call: {tool_name} for client {client.name}")
            
        except Exception as e:
            logger.error(f"Failed to background log tool call: {e}")
            # Don't fail the background task if logging fails
    
    def get_tool_config_schemas(self) -> Dict[str, Optional[Dict[str, any]]]:
        """Get configuration schemas for all registered tools"""
        schemas = {}
        for tool_name, tool in self._tools.items():
            tool_class = self._tool_classes[tool_name]
            schemas[tool_name] = tool_class.get_config_schema()
        return schemas
    
    def get_tool_config_schema(self, tool_name: str) -> Optional[Dict[str, any]]:
        """Get configuration schema for a specific tool"""
        if tool_name not in self._tool_classes:
            return None
        
        tool_class = self._tool_classes[tool_name]
        return tool_class.get_config_schema()


# Global registry instance
tool_registry = ToolRegistry()