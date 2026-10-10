import os
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from infrastructure.db.session import get_session
from infrastructure.db.models import SystemConfig, DocumentIngestionLog
from ai.api.schemas import IngestRequest
from ai.api.dependencies import get_active_pipeline
from ai.ingestion.loader import LocalFileLoader
from ai.ingestion.chunker import RecursiveCharacterChunker
from ai.rag.pipeline import RAGPipeline

router = APIRouter(tags=["Document Ingestion"])

@router.post("/ingest")
def ingest_documents(
    payload: IngestRequest,
    session: Session = Depends(get_session),
    pipeline: RAGPipeline = Depends(get_active_pipeline)
):
    config = session.exec(select(SystemConfig).where(SystemConfig.id == 1)).first()
    
    loader = LocalFileLoader(docs_dir=payload.docs_dir)
    raw_docs = loader.load_documents()

    if not raw_docs:
        return {"message": "No valid documents found in specified directory.", "chunks_ingested": 0}

    chunker = RecursiveCharacterChunker(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap
    )
    chunked_docs = chunker.chunk_documents(raw_docs)

    pipeline.ingest_documents(chunked_docs)

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