from fastapi import Depends, HTTPException
from sqlmodel import Session, select

from infrastructure.db.session import get_session
from infrastructure.db.models import SystemConfig
from ai.config import Config, ExecutionProvider
from ai.rag.chroma_client import ChromaVectorStore
from ai.rag.pipeline import RAGPipelineFactory, RAGPipeline

def get_active_pipeline(session: Session = Depends(get_session)) -> RAGPipeline:
    """
    Dynamically constructs a RAGPipeline instance using active SQLite settings.
    """
    db_config = session.exec(select(SystemConfig).where(SystemConfig.id == 1)).first()
    if not db_config:
        raise HTTPException(status_code=500, detail="System configuration not initialized in database.")

    # Sync runtime Config with SQLite store
    if db_config.provider.lower() == "local":
        Config.PROVIDER = ExecutionProvider.LOCAL
    else:
        Config.PROVIDER = ExecutionProvider.OLLAMA

    Config.OLLAMA_EMBED_MODEL = db_config.selected_embed_model
    Config.OLLAMA_LLM_MODEL = db_config.selected_llm_model

    embedder = RAGPipelineFactory.create_embedder()
    generator = RAGPipelineFactory.create_generator()
    vector_store = ChromaVectorStore(
        persist_dir=Config.CHROMA_PERSIST_DIR,
        collection_name=Config.COLLECTION_NAME
    )

    return RAGPipeline(
        embedder=embedder,
        generator=generator,
        vector_store=vector_store
    )