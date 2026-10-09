"""
FastAPI entry point for UrbanPulse AI — municipal complaint anomaly detection and early warning.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, ensure_schema
from backend.app.api.routes import router
from backend.app.fixtures.seed_data import seed_database

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_schema()
    db = SessionLocal()
    try:
        seed_database(db, force_reset=False, include_demo=settings.SEED_DEMO_DATA)
    except Exception:
        # A seeding problem must not take the whole platform down in front of a
        # demo; the API can still serve whatever is already persisted.
        db.rollback()
        logger.exception("Reference/demo seeding failed; continuing on existing data.")
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Detects statistically unusual changes in municipal complaint data across time, "
        "geography and category, and turns them into explainable early-warning alerts for investigation."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "subtitle": settings.APP_SUBTITLE,
        "version": settings.APP_VERSION,
        "documentation": "/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
