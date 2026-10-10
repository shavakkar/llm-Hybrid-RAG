from fastapi import APIRouter, Depends
from ai.api.schemas import QueryRequest
from ai.api.dependencies import get_active_pipeline
from ai.rag.pipeline import RAGPipeline

router = APIRouter(tags=["RAG Search & Generation"])

@router.post("/query")
def process_query(
    payload: QueryRequest,
    pipeline: RAGPipeline = Depends(get_active_pipeline)
):
    response = pipeline.query(user_query=payload.query)
    return response