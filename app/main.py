from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings
from app.models.database import Base, engine


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Cria as tabelas do banco de dados na inicialização
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title="Advisor Code Analyzer",
        version="1.0.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(router, prefix="/api/v1")

    @application.get("/")
    async def root() -> dict[str, str]:
        return {
            "status": "ok",
            "message": "Advisor Code Analyzer",
            "provider": settings.model_provider,
        }

    return application


app = create_app()
