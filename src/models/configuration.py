"""
Tool and Resource configuration models
"""
from datetime import datetime
from typing import Dict, Any, Optional
import uuid
from sqlalchemy import DateTime, Integer, String, func, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

# Import for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .client import Client


class ToolConfiguration(Base):
    """Model for per-client tool configurations"""
    
    __tablename__ = "tool_configurations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False)
    configuration: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)  # NULL allowed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="tool_configurations")
    
    # Unique constraint - one configuration per client per tool
    __table_args__ = (
        UniqueConstraint('client_id', 'tool_name', name='uq_client_tool'),
    )
    
    def __repr__(self) -> str:
        return f"<ToolConfiguration(id={self.id}, client_id={self.client_id}, tool='{self.tool_name}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "client_id": str(self.client_id),
            "tool_name": self.tool_name,
            "configuration": self.configuration,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class ResourceConfiguration(Base):
    """Model for per-client resource configurations"""
    
    __tablename__ = "resource_configurations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    resource_name: Mapped[str] = mapped_column(String(255), nullable=False)
    configuration: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)  # NULL allowed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="resource_configurations")
    
    # Unique constraint - one configuration per client per resource
    __table_args__ = (
        UniqueConstraint('client_id', 'resource_name', name='uq_client_resource'),
    )
    
    def __repr__(self) -> str:
        return f"<ResourceConfiguration(id={self.id}, client_id={self.client_id}, resource='{self.resource_name}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "client_id": str(self.client_id),
            "resource_name": self.resource_name,
            "configuration": self.configuration,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }