from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ConfigUpdateRequest(BaseModel):
    provider: str = Field(..., description="'local' or 'ollama'")
    selected_embed_model: str
    selected_llm_model: str
    chunk_size: Optional[int] = 300
    chunk_overlap: Optional[int] = 40

class IngestRequest(BaseModel):
    docs_dir: Optional[str] = "./docs"

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User question or prompt")

class HealthResponse(BaseModel):
    status: str
    provider: str
    database: str