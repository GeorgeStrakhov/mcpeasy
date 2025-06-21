"""
Type definitions for the tools module
"""

from typing import Any, Dict, List, Union, Optional
from pydantic import BaseModel, Field


class ToolSchema(BaseModel):
    """Pydantic model for MCP tool schema definition"""
    name: str
    description: str
    input_schema: Dict[str, Any] = Field(alias="inputSchema")
    
    class Config:
        validate_by_name = True


class ToolResult(BaseModel):
    """
    Pydantic model for MCP tool execution results
    
    Supports multiple content types optimized for different use cases:
    - text(): Plain text results
    - markdown(): Rich formatted text 
    - json(): Structured data (best for LLM processing)
    - file(): File/resource references
    - error(): Error messages
    """
    content: List[Dict[str, Any]]
    is_error: bool = False
    structured_content: Optional[Union[Dict[str, Any], List[Any]]] = Field(None, alias="structuredContent")
    
    class Config:
        populate_by_name = True
    
    @classmethod
    def text(cls, text: str) -> "ToolResult":
        """
        Create a plain text result
        
        Args:
            text: Plain text content
            
        Returns:
            ToolResult with text content
            
        Example:
            return ToolResult.text("Operation completed successfully")
        """
        return cls(content=[{"type": "text", "text": text}])
    
    @classmethod
    def markdown(cls, content: str) -> "ToolResult":
        """
        Create a markdown-formatted result (returns as plain text for MCP compatibility)
        
        Args:
            content: Markdown-formatted text
            
        Returns:
            ToolResult with text content
            
        Example:
            return ToolResult.markdown("# Success\\n\\nOperation **completed**")
        """
        return cls(content=[{"type": "text", "text": content}])
    
    @classmethod
    def json(cls, data: Union[Dict[str, Any], List[Any]]) -> "ToolResult":
        """
        Create a structured JSON result (recommended for LLM processing)
        
        Uses MCP's structuredContent field for proper JSON data handling.
        
        Args:
            data: Dictionary or list to return as structured data
            
        Returns:
            ToolResult with structured JSON content
            
        Example:
            return ToolResult.json({
                "operation": "add",
                "result": 42,
                "operands": [20, 22]
            })
        """
        return cls(content=[], structured_content=data)
    
    @classmethod
    def file(cls, uri: str, mime_type: str = None, description: str = None) -> "ToolResult":
        """
        Create a file/resource reference result (returns as structured JSON for MCP compatibility)
        
        Args:
            uri: URI to the file (e.g., S3 URL, local path, etc.)
            mime_type: MIME type of the file (optional)
            description: Human-readable description (optional)
            
        Returns:
            ToolResult with structured file reference
            
        Example:
            return ToolResult.file(
                "s3://bucket/report.pdf",
                mime_type="application/pdf",
                description="Generated quarterly report"
            )
        """
        file_data = {"url": uri}
        
        if mime_type:
            file_data["mime_type"] = mime_type
            
        if description:
            file_data["description"] = description
            
        return cls(content=[], structured_content=file_data)
    
    @classmethod
    def error(cls, error_message: str) -> "ToolResult":
        """
        Create an error result
        
        Args:
            error_message: Error description
            
        Returns:
            ToolResult with error content
            
        Example:
            return ToolResult.error("Invalid input: value must be positive")
        """
        return cls(
            content=[{"type": "text", "text": f"Error: {error_message}"}],
            is_error=True
        )