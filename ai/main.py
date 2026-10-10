from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from infrastructure.db.session import init_db
from ai.api.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[FastAPI] Initializing database and starting server...")
    init_db()
    yield
    print("[FastAPI] Shutting down server...")

app = FastAPI(
    title="Enterprise RAG Engine API",
    version="1.0.0",
    description="SOLID-compliant REST API connecting RAG pipeline to Next.js",
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

# Attach consolidated router
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ai.main:app", host="0.0.0.0", port=8000, reload=True)