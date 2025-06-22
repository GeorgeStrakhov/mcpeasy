"""
Client model for multi-tenant system
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid
from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

# Import for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .api_key import APIKey
    from .configuration import ToolConfiguration, ResourceConfiguration
    from .system_prompt import SystemPrompt


class Client(Base):
    """Model for client organizations/users"""
    
    __tablename__ = "clients"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    api_keys: Mapped[List["APIKey"]] = relationship("APIKey", back_populates="client")
    tool_configurations: Mapped[List["ToolConfiguration"]] = relationship("ToolConfiguration", back_populates="client")
    resource_configurations: Mapped[List["ResourceConfiguration"]] = relationship("ResourceConfiguration", back_populates="client")
    system_prompts: Mapped[List["SystemPrompt"]] = relationship("SystemPrompt", back_populates="client")
    
    def __repr__(self) -> str:
        return f"<Client(id={self.id}, name='{self.name}', active={self.is_active})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active
        }