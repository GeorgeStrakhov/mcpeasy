"""
SQLAlchemy models for the multi-tenant MCP server
"""
# Import the base class first
from .base import Base

# Import all models
from .admin import Admin
from .client import Client, APIKey
from .configuration import ToolConfiguration, ResourceConfiguration
from .knowledge import KnowledgeBase
from .tool_call import ToolCall
from .youtube import YouTubeChunk

# Export all models for easy importing
__all__ = [
    "Base",
    "Admin",
    "Client", 
    "APIKey",
    "ToolConfiguration",
    "ResourceConfiguration", 
    "KnowledgeBase",
    "ToolCall",
    "YouTubeChunk"
]