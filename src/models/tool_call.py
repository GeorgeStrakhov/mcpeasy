"""
Tool call tracking model for auditing and monitoring
"""
from datetime import datetime
from typing import Dict, Any, Optional
import uuid
from sqlalchemy import DateTime, Integer, String, Text, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

# Import for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .client import Client, APIKey


class ToolCall(Base):
    """Model for tracking tool call executions"""
    
    __tablename__ = "tool_calls"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    api_key_id: Mapped[int] = mapped_column(Integer, ForeignKey("api_keys.id"), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False)
    input_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)  # Tool arguments
    output_text: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)  # Text/content array responses
    output_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)  # Structured JSON responses
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # If tool failed
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Duration in milliseconds
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    client: Mapped["Client"] = relationship("Client")
    api_key: Mapped["APIKey"] = relationship("APIKey")
    
    def __repr__(self) -> str:
        return f"<ToolCall(id={self.id}, tool='{self.tool_name}', client_id={self.client_id}, created_at={self.created_at})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "client_id": str(self.client_id),
            "api_key_id": self.api_key_id,
            "tool_name": self.tool_name,
            "input_data": self.input_data,
            "output_text": self.output_text,
            "output_json": self.output_json,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at.isoformat()
        }