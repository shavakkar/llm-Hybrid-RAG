import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from infrastructure.db.session import init_db, get_session
from infrastructure.db.models import SystemConfig, DocumentIngestionLog
from ai.config import Config, ExecutionProvider, get_categorized_ollama_models
from ai.ingestion.loader import LocalFileLoader
from ai.ingestion.chunker import RecursiveCharacterChunker
from ai.rag.chroma_client import ChromaVectorStore
from ai.rag.pipeline import RAGPipelineFactory, RAGPipeline


# -------------------------------------------------------------------
# Pydantic Request / Response Models
# -------------------------------------------------------------------

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


# -------------------------------------------------------------------
# Application Lifecycle & FastAPI Setup
# -------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes SQLite database on startup."""
    print("[FastAPI] Starting application server...")
    init_db()
    yield
    print("[FastAPI] Shutting down application server...")


app = FastAPI(
    title="Enterprise RAG Engine API",
    version="1.0.0",
    description="Modular Python REST API connecting local/Ollama RAG pipelines to Next.js",
    lifespan=lifespan
)

# Enable CORS for Next.js frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# Helper: Instantiate RAG Pipeline from SQLite Config
# -------------------------------------------------------------------

def get_active_pipeline(session: Session = Depends(get_session)) -> RAGPipeline:
    """
    Dynamically constructs a RAGPipeline instance based on current SQLite settings.
    """
    db_config = session.exec(select(SystemConfig).where(SystemConfig.id == 1)).first()
    if not db_config:
        raise HTTPException(status_code=500, detail="System configuration not initialized.")

    # Override runtime Config object from SQLite settings
    if db_config.provider.lower() == "local":
        Config.PROVIDER = ExecutionProvider.LOCAL
    else:
        Config.PROVIDER = ExecutionProvider.OLLAMA

    Config.OLLAMA_EMBED_MODEL = db_config.selected_embed_model
    Config.OLLAMA_LLM_MODEL = db_config.selected_llm_model

    # Construct dynamically via Factory
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


# -------------------------------------------------------------------
# REST API Endpoints
# -------------------------------------------------------------------

@app.get("/api/health")
def health_check(session: Session = Depends(get_session)):
    """Backend status and database check."""
    config = session.exec(select(SystemConfig).where(SystemConfig.id == 1)).first()
    return {
        "status": "online",
        "provider": config.provider if config else "unknown",
        "database": "connected"
    }


@app.get("/api/models")
def list_available_models():
    """
    Discovers installed models from local directory paths and local Ollama instance.
    """
    ollama_models = get_categorized_ollama_models(Config.OLLAMA_BASE_URL)
    
    local_embeds = [Config.LOCAL_EMBED_PATH] if os.path.exists(Config.LOCAL_EMBED_PATH) else []
    local_llms = [Config.LOCAL_LLM_PATH] if os.path.exists(Config.LOCAL_LLM_PATH) else []

    return {
        "ollama": ollama_models,
        "local": {
            "embedders": local_embeds,
            "generators": local_llms
        }
    }


@app.get("/api/config")
def get_current_config(session: Session = Depends(get_session)):
    """Retrieves current application settings from SQLite."""
    config = session.exec(select(SystemConfig).where(SystemConfig.id == 1)).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found.")
    return config


@app.put("/api/config")
def update_config(payload: ConfigUpdateRequest, session: Session = Depends(get_session)):
    """Updates active provider and model preferences in SQLite."""
    config = session.exec(select(SystemConfig).where(SystemConfig.id == 1)).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found.")

    config.provider = payload.provider.lower()
    config.selected_embed_model = payload.selected_embed_model
    config.selected_llm_model = payload.selected_llm_model
    if payload.chunk_size:
        config.chunk_size = payload.chunk_size
    if payload.chunk_overlap:
        config.chunk_overlap = payload.chunk_overlap

    session.add(config)
    session.commit()
    session.refresh(config)
    return {"message": "Configuration updated successfully", "config": config}


@app.post("/api/ingest")
def ingest_documents(payload: IngestRequest, session: Session = Depends(get_session)):
    """
    Loads files from disk, recursively chunks text, generates embeddings,
    saves vectors to ChromaDB, and records an audit log entry in SQLite.
    """
    config = session.exec(select(SystemConfig).where(SystemConfig.id == 1)).first()
    
    # 1. Load raw files
    loader = LocalFileLoader(docs_dir=payload.docs_dir)
    raw_docs = loader.load_documents()

    if not raw_docs:
        return {"message": "No valid documents found in specified directory.", "chunks_ingested": 0}

    # 2. Chunk recursively
    chunker = RecursiveCharacterChunker(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap
    )
    chunked_docs = chunker.chunk_documents(raw_docs)

    # 3. Instantiate pipeline & persist to ChromaDB
    pipeline = get_active_pipeline(session)
    pipeline.ingest_documents(chunked_docs)

    # 4. Log ingestion in SQLite
    for raw_doc in raw_docs:
        filepath = raw_doc["metadata"].get("path", payload.docs_dir)
        filename = raw_doc["metadata"].get("source", "unknown")
        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0

        log_entry = DocumentIngestionLog(
            filename=filename,
            filepath=filepath,
            file_size_bytes=file_size,
            total_chunks=len(chunked_docs),
            provider_used=config.provider,
            embedding_model_used=config.selected_embed_model
        )
        session.add(log_entry)

    session.commit()

    return {
        "message": "Ingestion completed successfully",
        "documents_loaded": len(raw_docs),
        "chunks_ingested": len(chunked_docs)
    }


@app.post("/api/query")
def process_query(payload: QueryRequest, session: Session = Depends(get_session)):
    """
    Executes context retrieval and LLM answer generation for user query.
    """
    pipeline = get_active_pipeline(session)
    response = pipeline.query(user_query=payload.query)
    return response


# -------------------------------------------------------------------
# Application Entrypoint for Development
# -------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ai.main:app", host="0.0.0.0", port=8000, reload=True)