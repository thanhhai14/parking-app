from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

import asyncio
from core.config import settings
from core.logger import setup_logging
from core.database import get_db_session
from core.redis import redis_client
from services.event_consumer import start_event_consumer
from api.v1.auth import router as auth_router
from api.v1.media import router as media_router
from api.v1.vehicles import router as vehicles_router
from api.v1.cards import router as cards_router
from api.v1.devices import router as devices_router
from api.v1.parking import router as parking_router


# Initialize logging configuration
setup_logging()
logger = logging.getLogger("parking-api")

event_consumer_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global event_consumer_task
    logger.info("Starting up parking-api service...")
    redis_client.connect()
    event_consumer_task = asyncio.create_task(start_event_consumer())
    yield
    logger.info("Shutting down parking-api service...")
    if event_consumer_task:
        event_consumer_task.cancel()
        try:
            await event_consumer_task
        except asyncio.CancelledError:
            pass
    await redis_client.disconnect()

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
app.include_router(media_router, prefix="/api/v1/media", tags=["media"])
app.include_router(vehicles_router, prefix="/api/v1/vehicles", tags=["vehicles"])
app.include_router(cards_router, prefix="/api/v1/cards", tags=["cards"])
app.include_router(devices_router, prefix="/api/v1/devices", tags=["devices"])
app.include_router(parking_router, prefix="/api/v1/parking", tags=["parking"])


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
