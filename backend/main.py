from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.agents import router as agents_router
from app.api.v1.credentials import router as credentials_router
from app.api.v1.builds import router as builds_router
from app.api.v1.models import router as models_router
from app.api.v1.chat import router as chat_router
from app.database.session import create_tables
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    create_tables()
    app = FastAPI(
        title="Agethrix API",
        description="Agethrix — From Intent to Intelligence.",
        version="0.1.0",
    )
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(credentials_router)
    app.include_router(agents_router)
    app.include_router(builds_router)
    app.include_router(models_router)
    app.include_router(chat_router)
    app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    return app


app = create_app()
