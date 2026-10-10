import os
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from infrastructure.db.session import get_session
from infrastructure.db.models import SystemConfig
from ai.api.schemas import ConfigUpdateRequest, HealthResponse
from ai.config import Config, get_categorized_ollama_models

router = APIRouter(tags=["System & Configuration"])

@router.get("/health", response_model=HealthResponse)
def health_check(session: Session = Depends(get_session)):
    config = session.exec(select(SystemConfig).where(SystemConfig.id == 1)).first()
    return {
        "status": "online",
        "provider": config.provider if config else "unknown",
        "database": "connected"
    }

@router.get("/models")
def list_available_models():
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

@router.get("/config")
def get_current_config(session: Session = Depends(get_session)):
    config = session.exec(select(SystemConfig).where(SystemConfig.id == 1)).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found.")
    return config

@router.put("/config")
def update_config(payload: ConfigUpdateRequest, session: Session = Depends(get_session)):
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