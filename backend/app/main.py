from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import Base, engine
from .routers import health, auth, users, files, conversions, stripe_routes

def create_app() -> FastAPI:
    app = FastAPI(title="Bank Statement Converter API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # create tables for MVP (prefer Alembic in production)
    Base.metadata.create_all(bind=engine)

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(files.router)
    app.include_router(conversions.router)
    app.include_router(stripe_routes.router)

    return app

app = create_app()
