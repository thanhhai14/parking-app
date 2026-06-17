from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from core.config import settings
from core.logger import setup_logging
from core.database import get_db_session
from api.v1.auth import router as auth_router

# Initialize logging configuration
setup_logging()
logger = logging.getLogger("parking-api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up parking-api service...")
    yield
    logger.info("Shutting down parking-api service...")

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.APP_DEBUG,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production based on requirements
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])

@app.get("/health", tags=["health"])
async def health_check(db: AsyncSession = Depends(get_db_session)):
    try:
        # Perform a quick database ping
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "app": settings.APP_NAME
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "detail": str(e)
        }
