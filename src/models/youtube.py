"""
YouTube chunk model for vector similarity search
"""

from sqlalchemy import Column, Integer, String, Text, REAL
from pgvector.sqlalchemy import Vector
from .base import Base


class YouTubeChunk(Base):
    """YouTube video chunk with embeddings for similarity search"""
    
    __tablename__ = "youtube_chunks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_slug = Column(String(255), nullable=False, index=True)
    video_id = Column(String(255), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    title = Column(Text, nullable=False)
    start_timestamp = Column(REAL, nullable=False)
    end_timestamp = Column(REAL, nullable=False)
    text = Column(Text, nullable=False)
    word_count = Column(Integer, nullable=False)
    sentence_count = Column(Integer, nullable=False)
    embedding = Column(Vector(1024), nullable=True)
    
    def __repr__(self):
        return f"<YouTubeChunk(project_slug='{self.project_slug}', video_id='{self.video_id}', chunk_index={self.chunk_index})>"
    
    def get_youtube_url(self) -> str:
        """Get YouTube URL with timestamp"""
        timestamp_seconds = int(self.start_timestamp)
        return f"https://www.youtube.com/watch?v={self.video_id}&t={timestamp_seconds}s"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "project_slug": self.project_slug,
            "video_id": self.video_id,
            "chunk_index": self.chunk_index,
            "title": self.title,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "text": self.text,
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
            "youtube_url": self.get_youtube_url()
        }