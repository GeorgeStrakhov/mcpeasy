"""
Database models for TOOL_NAME custom tool

This file defines database models that your custom tool needs.
When this file exists, Alembic will automatically discover it and include
the models in migration generation.

Replace TOOL_NAME with your actual tool name throughout this file.
"""

from datetime import datetime
from typing import Dict, Any, Optional
import uuid
from sqlalchemy import DateTime, Integer, String, func, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Import the base class from mcpeasy core
from src.models.base import Base

# Import for type hints (optional)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.client import Client


class TOOLNAMEData(Base):
    """
    Example model for storing TOOL_NAME specific data
    
    This demonstrates how to create custom models that:
    - Follow mcpeasy naming conventions
    - Link to core models (like Client)
    - Store tool-specific data
    - Support JSONB for flexible data storage
    """
    
    __tablename__ = "toolname_data"  # Replace with your tool name
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Link to mcpeasy core client model
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("clients.id"), 
        nullable=False
    )
    
    # Tool-specific fields
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    
    # Relationship to core client model
    client: Mapped["Client"] = relationship("Client")
    
    def __repr__(self) -> str:
        return f"<TOOLNAMEData(id={self.id}, client_id={self.client_id}, status='{self.status}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "client_id": str(self.client_id),
            "external_id": self.external_id,
            "status": self.status,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class TOOLNAMELog(Base):
    """
    Example model for logging TOOL_NAME operations
    
    This demonstrates how to create audit/logging tables for your custom tool.
    """
    
    __tablename__ = "toolname_logs"  # Replace with your tool name
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Link to mcpeasy core client model
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("clients.id"), 
        nullable=False
    )
    
    # Link to the main data record (optional)
    toolname_data_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("toolname_data.id"),
        nullable=True
    )
    
    # Log fields
    operation: Mapped[str] = mapped_column(String(100), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    request_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    response_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    # Timing
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    client: Mapped["Client"] = relationship("Client")
    toolname_data: Mapped[Optional["TOOLNAMEData"]] = relationship("TOOLNAMEData")
    
    def __repr__(self) -> str:
        return f"<TOOLNAMELog(id={self.id}, operation='{self.operation}', success={self.success})>"


# Additional example models for different use cases

class TOOLNAMEConfig(Base):
    """
    Example model for storing per-client tool configuration
    
    This can be used as an alternative or supplement to the JSONB configuration
    in the core tool_configurations table.
    """
    
    __tablename__ = "toolname_config"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("clients.id"), 
        nullable=False,
        unique=True  # One config per client
    )
    
    # Specific configuration fields for your tool
    api_endpoint: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Store encrypted
    rate_limit: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Advanced settings as JSONB
    advanced_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    
    # Relationship
    client: Mapped["Client"] = relationship("Client")


# TODO: Add your own custom models here
# 
# Example patterns:
# 
# 1. Data storage models (like TOOLNAMEData above)
# 2. Audit/logging models (like TOOLNAMELog above) 
# 3. Configuration models (like TOOLNAMEConfig above)
# 4. Relationship models (many-to-many tables)
# 5. Cache/temporary data models
#
# Best practices:
# - Always link to core models via ForeignKey when relevant
# - Use JSONB for flexible/evolving data structures
# - Include created_at/updated_at timestamps
# - Add meaningful indexes for query performance
# - Follow naming convention: toolname_tablename
# - Include __repr__ and to_dict methods for debugging