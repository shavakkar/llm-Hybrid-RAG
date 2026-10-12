from typing import Optional
from fastapi import Depends, HTTPException
from sqlmodel import Session, select

from infrastructure.db.session import get_session
from infrastructure.db.models import SystemConfig
from ai.config import Config, ExecutionProvider
from ai.rag.chroma_client import ChromaVectorStore
from ai.rag.pipeline import RAGPipelineFactory, RAGPipeline

# Global cached pipeline singleton & state tracker
_cached_pipeline: Optional[RAGPipeline] = None
_cached_config_state: Optional[dict] = None


def get_active_pipeline(session: Session = Depends(get_session)) -> RAGPipeline:
    """
    Returns a cached RAGPipeline instance. 
    Only reloads models from disk if the provider or model choice changed in SQLite.
    """
    global _cached_pipeline, _cached_config_state

    db_config = session.exec(select(SystemConfig).where(SystemConfig.id == 1)).first()
    if not db_config:
        raise HTTPException(status_code=500, detail="System configuration not initialized.")

    # Track current active setup state
    current_state = {
        "provider": db_config.provider.lower(),
        "embed_model": db_config.selected_embed_model,
        "llm_model": db_config.selected_llm_model
    }

    # If pipeline is already loaded AND configuration hasn't changed, reuse it instantly!
    if _cached_pipeline is not None and _cached_config_state == current_state:
        return _cached_pipeline

    print(f"[Pipeline Cache] Config changed or initial load. Loading models into memory...")

    # Update runtime config
    if db_config.provider.lower() == "local":
        Config.PROVIDER = ExecutionProvider.LOCAL
    else:
        Config.PROVIDER = ExecutionProvider.OLLAMA

    Config.OLLAMA_EMBED_MODEL = db_config.selected_embed_model
    Config.OLLAMA_LLM_MODEL = db_config.selected_llm_model

    # Construct pipeline once
    embedder = RAGPipelineFactory.create_embedder()
    generator = RAGPipelineFactory.create_generator()
    vector_store = ChromaVectorStore(
        persist_dir=Config.CHROMA_PERSIST_DIR,
        collection_name=Config.COLLECTION_NAME
    )

    # Store in global cache
    _cached_pipeline = RAGPipeline(
        embedder=embedder,
        generator=generator,
        vector_store=vector_store
    )
    _cached_config_state = current_state

    return _cached_pipeline