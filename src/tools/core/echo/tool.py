"""
Echo tool implementation - returns the input message
"""

from typing import Any, Dict, Optional
from src.tools.base import BaseTool, ToolResult


class EchoTool(BaseTool):
    """Simple echo tool for testing MCP functionality"""
    
    @property
    def name(self) -> str:
        return "echo"
    
    @property
    def description(self) -> str:
        return "Echo back the provided message"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The message to echo back"
                }
            },
            "required": ["message"]
        }
    
    async def execute(self, arguments: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> ToolResult:
        """Execute the echo tool"""
        message = arguments.get("message", "")
        return ToolResult.text(f"Echo: {message}")