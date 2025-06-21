"""
Knowledge Base models
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class KnowledgeBase(Base):
    """Model for knowledge base articles and resources"""
    
    __tablename__ = "knowledge_base"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        return f"<KnowledgeBase(id={self.id}, title='{self.title}', category='{self.category}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "tags": self.tags or [],
            "created_at": self.created_at.isoformat(),
        }