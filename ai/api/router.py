from fastapi import APIRouter
from ai.api.routes import config, ingest, query

api_router = APIRouter()

api_router.include_router(config.router)
api_router.include_router(ingest.router)
api_router.include_router(query.router)