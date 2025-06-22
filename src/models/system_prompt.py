from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Integer, String, Text, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base

# Import for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .client import Client



class SystemPrompt(Base):
    __tablename__ = "system_prompts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    user_requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generation_context: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    parent_version_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("system_prompts.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="system_prompts")
    parent_version: Mapped[Optional["SystemPrompt"]] = relationship("SystemPrompt", remote_side=[id], backref="revisions")
    
    def __repr__(self) -> str:
        return f"<SystemPrompt(id={self.id}, client_id={self.client_id}, version={self.version}, is_active={self.is_active})>"