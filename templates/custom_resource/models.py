"""
Database models for RESOURCE_NAME custom resource

This file defines database models that your custom resource needs.
When this file exists, Alembic will automatically discover it and include
the models in migration generation.

Replace RESOURCE_NAME with your actual resource name throughout this file.
"""

from datetime import datetime
from typing import Dict, Any, Optional
import uuid
from sqlalchemy import DateTime, Integer, String, func, ForeignKey, Text, Boolean, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Import the base class from mcpeasy core
from src.models.base import Base

# Import for type hints (optional)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.client import Client


class RESOURCENAMEItem(Base):
    """
    Example model for storing RESOURCE_NAME items
    
    This demonstrates how to create custom models for resources that:
    - Store resource data in the database
    - Support client-specific filtering
    - Cache external API data
    - Enable fast searching and filtering
    """
    
    __tablename__ = "resourcename_items"  # Replace with your resource name
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # External identifier (from source system)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Resource content
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    # Resource metadata
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)  # Array of strings
    mime_type: Mapped[str] = mapped_column(String(100), default="text/plain", nullable=False)
    
    # Access control and filtering
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allowed_clients: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)  # Array of client IDs
    
    # Cache management
    source_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    last_synced: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sync_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # For detecting changes
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    
    # Add indexes for common queries
    __table_args__ = (
        Index('ix_resourcename_external_id', 'external_id'),
        Index('ix_resourcename_category', 'category'),
        Index('ix_resourcename_public', 'is_public'),
        Index('ix_resourcename_last_synced', 'last_synced'),
    )
    
    def __repr__(self) -> str:
        return f"<RESOURCENAMEItem(id={self.id}, external_id='{self.external_id}', name='{self.name}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "external_id": self.external_id,
            "name": self.name,
            "description": self.description,
            "content": self.content,
            "category": self.category,
            "tags": self.tags,
            "mime_type": self.mime_type,
            "is_public": self.is_public,
            "source_url": self.source_url,
            "last_synced": self.last_synced.isoformat() if self.last_synced else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def to_mcp_resource(self) -> Dict[str, Any]:
        """Convert to MCP Resource format"""
        return {
            "uri": f"resourcename://{self.external_id}",  # Replace with your URI scheme
            "name": self.name,
            "description": self.description or "",
            "mimeType": self.mime_type
        }


class RESOURCENAMEAccess(Base):
    """
    Example model for tracking resource access per client
    
    This demonstrates how to:
    - Log resource usage for analytics
    - Track client-specific access patterns
    - Support billing/usage reporting
    """
    
    __tablename__ = "resourcename_access"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Link to mcpeasy core client model
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("clients.id"), 
        nullable=False
    )
    
    # Link to resource item
    resource_item_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("resourcename_items.id"),
        nullable=False
    )
    
    # Access details
    operation: Mapped[str] = mapped_column(String(50), nullable=False)  # 'list', 'read'
    uri_requested: Mapped[str] = mapped_column(String(1000), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Performance tracking
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bytes_returned: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    client: Mapped["Client"] = relationship("Client")
    resource_item: Mapped["RESOURCENAMEItem"] = relationship("RESOURCENAMEItem")
    
    # Indexes for analytics queries
    __table_args__ = (
        Index('ix_resourcename_access_client', 'client_id'),
        Index('ix_resourcename_access_created', 'created_at'),
        Index('ix_resourcename_access_operation', 'operation'),
    )
    
    def __repr__(self) -> str:
        return f"<RESOURCENAMEAccess(id={self.id}, client_id={self.client_id}, operation='{self.operation}')>"


class RESOURCENAMESync(Base):
    """
    Example model for tracking synchronization with external systems
    
    This demonstrates how to:
    - Track sync operations with external APIs
    - Store sync metadata and status
    - Enable sync scheduling and monitoring
    """
    
    __tablename__ = "resourcename_sync"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Sync details
    sync_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'full', 'incremental'
    source_system: Mapped[str] = mapped_column(String(100), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # Sync status
    status: Mapped[str] = mapped_column(String(50), default="running", nullable=False)  # 'running', 'completed', 'failed'
    started_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Sync results
    items_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_deleted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    # Sync metadata
    sync_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    last_cursor: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # For incremental sync
    
    def __repr__(self) -> str:
        return f"<RESOURCENAMESync(id={self.id}, status='{self.status}', items_processed={self.items_processed})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "sync_type": self.sync_type,
            "source_system": self.source_system,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "items_processed": self.items_processed,
            "items_created": self.items_created,
            "items_updated": self.items_updated,
            "items_deleted": self.items_deleted,
            "error_message": self.error_message
        }


# TODO: Add your own custom models here
# 
# Example patterns for resources:
# 
# 1. Item storage models (like RESOURCENAMEItem above)
# 2. Access tracking models (like RESOURCENAMEAccess above) 
# 3. Sync/cache models (like RESOURCENAMESync above)
# 4. Category/taxonomy models for organizing resources
# 5. Permission/ACL models for fine-grained access control
# 6. Metadata/annotation models for enriching resources
#
# Best practices:
# - Always consider client-specific access patterns
# - Add indexes for common query patterns
# - Use JSONB for flexible metadata storage
# - Include sync/cache management if using external data
# - Track usage for analytics and billing
# - Follow naming convention: resourcename_tablename