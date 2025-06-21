"""
MCP Resource type definitions using Pydantic
"""
from typing import Dict, Any, Optional
import base64
from pydantic import BaseModel, Field


class MCPResource(BaseModel):
    """Represents an MCP resource"""
    uri: str
    name: str
    description: str
    mime_type: Optional[str] = Field(None, alias="mimeType")
    
    class Config:
        validate_by_name = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MCP protocol format"""
        return self.dict(by_alias=True, exclude_none=True)


class ResourceContent(BaseModel):
    """Represents resource content for MCP responses"""
    uri: str
    mime_type: str = Field(alias="mimeType")
    text: Optional[str] = None
    blob: Optional[bytes] = None
    
    class Config:
        validate_by_name = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MCP protocol format"""
        result = {
            "uri": self.uri,
            "mimeType": self.mime_type
        }
        if self.text is not None:
            result["text"] = self.text
        if self.blob is not None:
            # Base64 encode blob
            result["blob"] = base64.b64encode(self.blob).decode('utf-8')
        return result