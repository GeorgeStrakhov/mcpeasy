"""
Base classes for modular MCP tools using Pydantic
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .types import ToolSchema, ToolResult


class BaseTool(ABC):
    """Abstract base class for all MCP tools"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name - must be unique"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for MCP clients"""
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """JSON schema for tool input parameters"""
        pass
    
    @classmethod
    def get_config_schema(cls) -> Optional[Dict[str, Any]]:
        """Return JSON schema for tool configuration, or None if no config needed"""
        return None
    
    @classmethod
    def requires_config(cls) -> bool:
        """Check if tool requires configuration"""
        return cls.get_config_schema() is not None
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> ToolResult:
        """Execute the tool with given arguments and optional configuration"""
        pass
    
    def get_schema(self) -> ToolSchema:
        """Get the MCP tool schema"""
        return ToolSchema(
            name=self.name,
            description=self.description,
            inputSchema=self.input_schema
        )
    
    def validate_arguments(self, arguments: Dict[str, Any]) -> bool:
        """Validate arguments against the input schema (basic validation)"""
        # This could be enhanced with jsonschema validation
        required_fields = self.input_schema.get("required", [])
        properties = self.input_schema.get("properties", {})
        
        # Check required fields
        for field in required_fields:
            if field not in arguments:
                return False
        
        # Check field types (basic)
        for field, value in arguments.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if expected_type == "string" and not isinstance(value, str):
                    return False
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    return False
                elif expected_type == "boolean" and not isinstance(value, bool):
                    return False
                elif expected_type == "array" and not isinstance(value, list):
                    return False
                elif expected_type == "object" and not isinstance(value, dict):
                    return False
        
        return True