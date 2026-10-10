from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class SystemConfig(SQLModel, table=True):
    """
    Stores persistent application configurations and user model choices.
    """
    id: Optional[int] = Field(default=1, primary_key=True)
    provider: str = Field(default="ollama", description="Active execution provider: 'local' or 'ollama'")
    selected_embed_model: str = Field(default="nomic-embed-text:latest", description="Active embedding model name or path")
    selected_llm_model: str = Field(default="qwen2.5:7b", description="Active generator LLM model name or path")
    chunk_size: int = Field(default=300, description="Recursive chunking character size limit")
    chunk_overlap: int = Field(default=40, description="Recursive chunking character overlap")
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class DocumentIngestionLog(SQLModel, table=True):
    """
    Tracks files and chunks indexed into ChromaDB.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(index=True)
    filepath: str
    file_size_bytes: int
    total_chunks: int
    provider_used: str
    embedding_model_used: str
    ingested_at: datetime = Field(default_factory=datetime.utcnow)