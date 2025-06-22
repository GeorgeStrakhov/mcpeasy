"""
Tool registry for dynamic tool discovery and management
"""

import logging
import importlib
import os
from typing import Dict, List, Optional, Type, Any
from pathlib import Path

from .base import BaseTool, ToolSchema, ToolResult
from .execution_queue import SimpleToolQueue

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing and discovering MCP tools"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
        # Add simple queue
        self._queue = SimpleToolQueue(
            max_workers=int(os.getenv("TOOL_MAX_WORKERS", "20")),
            queue_size=int(os.getenv("TOOL_QUEUE_SIZE", "200"))
        )
        self._queue_started = False
    
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
                # For namespaced tools, use the full name
                if "/" in tool_name:
                    schema.name = tool_name
                schemas.append(schema)
            else:
                logger.warning(f"Enabled tool '{tool_name}' not found in registry")
        
        return schemas
    
    def _get_enabled_tools(self) -> List[str]:
        """Get list of enabled tools from TOOLS environment variable"""
        tools_env = os.getenv("TOOLS", "")
        if not tools_env:
            logger.warning("No TOOLS environment variable set, no tools will be enabled")
            return []
        
        # Check for special __all__ value to enable all discovered tools
        if tools_env.strip() == "__all__":
            logger.info("TOOLS=__all__ detected, discovering all available tools")
            return self._discover_all_available_tools()
        
        # Split by comma and strip whitespace
        tools = [t.strip() for t in tools_env.split(",") if t.strip()]
        logger.info(f"Enabled tools from environment: {tools}")
        return tools

    def _discover_all_available_tools(self, tools_package: str = "src.tools") -> List[str]:
        """Discover all available tools by scanning the filesystem"""
        available_tools = []
        
        # Get the tools directory path
        tools_path = Path(tools_package.replace(".", "/"))
        if not tools_path.exists():
            logger.warning(f"Tools directory {tools_path} does not exist")
            return []
        
        # Scan for namespace directories (core, m38, etc.)
        for namespace_dir in tools_path.iterdir():
            if not namespace_dir.is_dir() or namespace_dir.name.startswith("_"):
                continue
                
            namespace = namespace_dir.name
            
            # Scan for tool directories within namespace
            for tool_dir in namespace_dir.iterdir():
                if not tool_dir.is_dir() or tool_dir.name.startswith("_"):
                    continue
                    
                tool_name = tool_dir.name
                
                # Check if tool.py exists
                tool_file = tool_dir / "tool.py"
                if tool_file.exists():
                    full_tool_name = f"{namespace}/{tool_name}"
                    available_tools.append(full_tool_name)
                    logger.debug(f"Found available tool: {full_tool_name}")
        
        logger.info(f"Discovered {len(available_tools)} available tools: {available_tools}")
        return available_tools

    def discover_tools(self, tools_package: str = "src.tools") -> None:
        """Discover and register tools based on TOOLS environment variable"""
        try:
            # Get enabled tools from environment
            enabled_tools = self._get_enabled_tools()
            if not enabled_tools:
                logger.warning("No tools enabled in TOOLS environment variable")
                return
            
            # Discover and register each enabled tool
            registered_count = 0
            for tool_name in enabled_tools:
                if "/" in tool_name:
                    # Namespaced tool (e.g., "core/echo" or "acme/invoice")
                    namespace, tool = tool_name.split("/", 1)
                    tool_class = self._discover_tool_in_namespace(tools_package, namespace, tool)
                    if tool_class:
                        self.register_tool(tool_class, custom_name=tool_name)
                        registered_count += 1
                        logger.debug(f"Registered tool: {tool_name}")
                    else:
                        logger.warning(f"Tool '{tool_name}' not found")
                else:
                    logger.warning(f"Tool '{tool_name}' must have namespace (e.g., 'core/echo')")
            
            logger.info(f"Registered {registered_count} tools from {len(enabled_tools)} requested")
                    
        except Exception as e:
            logger.error(f"Error discovering tools: {e}")

    def _discover_tool_in_namespace(self, base_package: str, namespace: str, tool_name: str) -> Optional[Type[BaseTool]]:
        """Discover a tool in a specific namespace/tool directory"""
        try:
            # Construct module path
            # e.g., src.tools.core.echo.tool or src.tools.acme.invoice.tool
            tool_module_name = f"{base_package}.{namespace}.{tool_name}.tool"
            tool_module = importlib.import_module(tool_module_name)
            
            # Look for classes that inherit from BaseTool
            for attr_name in dir(tool_module):
                attr = getattr(tool_module, attr_name)
                if (isinstance(attr, type) and 
                    hasattr(attr, '__mro__') and
                    any(base.__name__ == 'BaseTool' for base in attr.__mro__) and
                    attr.__name__ != 'BaseTool'):
                    return attr
            
            logger.warning(f"No BaseTool subclass found in {tool_module_name}")
            return None
                    
        except ImportError as e:
            logger.debug(f"Could not import tool {namespace}/{tool_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error discovering tool {namespace}/{tool_name}: {e}")
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
            start_time = time.time()
            
            # Submit to queue instead of direct execution
            result = await self._queue.submit(tool, arguments, config)
            
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
    
    async def ensure_queue_started(self):
        """Ensure queue is started (called once during app startup)"""
        if not self._queue_started:
            await self._queue.start()
            self._queue_started = True
            logger.info("Tool execution queue started")
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get current queue statistics"""
        return self._queue.get_stats()


# Global registry instance
tool_registry = ToolRegistry()