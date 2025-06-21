"""
Base classes for modular MCP resources using Pydantic
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field

from .types import MCPResource, ResourceContent


class ResourceSchema(BaseModel):
    """Pydantic model for MCP resource schema definition"""
    uri: str
    name: str
    description: str
    mime_type: Optional[str] = Field(None, alias="mimeType")
    
    class Config:
        validate_by_name = True


class BaseResource(ABC):
    """Abstract base class for all MCP resources"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Resource name - must be unique"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Resource description for MCP clients"""
        pass
    
    @property
    @abstractmethod
    def uri_scheme(self) -> str:
        """URI scheme for this resource type (e.g., 'knowledge', 'files')"""
        pass
    
    @classmethod
    def get_config_schema(cls) -> Optional[Dict[str, Any]]:
        """Return JSON schema for resource configuration, or None if no config needed"""
        return None
    
    @classmethod
    def requires_config(cls) -> bool:
        """Check if resource requires configuration"""
        return cls.get_config_schema() is not None
    
    @abstractmethod
    async def list_resources(self, config: Optional[Dict[str, Any]] = None) -> List[MCPResource]:
        """List all available resources with optional client-specific configuration"""
        pass
    
    @abstractmethod
    async def read_resource(self, uri: str, config: Optional[Dict[str, Any]] = None) -> Optional[ResourceContent]:
        """Read resource content with optional client-specific configuration"""
        pass
    
    def validate_uri(self, uri: str) -> bool:
        """Validate if this resource can handle the given URI"""
        return uri.startswith(f"{self.uri_scheme}://")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration against the config schema (basic validation)"""
        schema = self.get_config_schema()
        if not schema:
            return True  # No config needed
        
        # Basic validation - could be enhanced with jsonschema
        required_fields = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # Check required fields
        for field in required_fields:
            if field not in config:
                return False
        
        # Check field types (basic)
        for field, value in config.items():
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