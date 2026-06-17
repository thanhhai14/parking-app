import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

import jwt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.logger import setup_logging
from websocket.connection_manager import manager
from redis_gateway.redis_client import redis_client

setup_logging()
logger = logging.getLogger("parking-gateway")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up parking-gateway service...")
    await redis_client.connect()
    yield
    logger.info("Shutting down parking-gateway service...")
    await redis_client.disconnect()

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "connections": {
            "web_clients": len(manager.web_clients),
            "device_agents": len(manager.device_agents),
            "camera_agents": len(manager.camera_agents)
        }
    }

@app.get("/internal/connections")
async def get_connections():
    return {
        "web_clients": len(manager.web_clients),
        "device_agents": list(manager.device_agents.keys()),
        "camera_agents": list(manager.camera_agents.keys())
    }

def verify_web_token(token: str) -> bool:
    try:
        jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return True
    except jwt.PyJWTError as e:
        logger.warning(f"JWT Verification failed: {e}")
        return False

@app.websocket("/ws/web")
async def ws_web(websocket: WebSocket, token: Optional[str] = Query(None)):
    if not token or not verify_web_token(token):
        logger.warning("Rejected Web client connection due to invalid token.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    await manager.connect_web(websocket)
    try:
        # Web clients usually only receive data, but we listen to keep connection alive
        # and handle potential client-side closure or commands.
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received raw data from web client: {data}")
    except WebSocketDisconnect:
        manager.disconnect_web(websocket)
    except Exception as e:
        logger.error(f"Error in Web Client WebSocket loop: {e}")
        manager.disconnect_web(websocket)

async def handle_agent_connection(
    websocket: WebSocket,
    agent_id: str,
    agent_type: str,
    expected_token: str,
    token: Optional[str]
):
    """
    Common handler for hardware agents (device and camera)
    """
    if token != expected_token:
        logger.warning(f"Rejected {agent_type} agent '{agent_id}' connection: Invalid token.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    await manager.connect_agent(agent_id, agent_type, websocket)
    
    # Acknowledge connection
    await websocket.send_json({
        "event_type": "connection.established",
        "agent_id": agent_id,
        "agent_type": agent_type
    })
    
    try:
        while True:
            # Enforce heartbeat interval using asyncio.wait_for
            # If the client doesn't send any message within timeout window, disconnect it.
            data = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=settings.GATEWAY_HEARTBEAT_TIMEOUT
            )
            
            logger.info(f"Received event from {agent_type} agent '{agent_id}': {data.get('event_type')}")
            
            # Decorate the event with standard fields if missing
            import uuid
            from datetime import datetime, timezone
            
            if not isinstance(data, dict):
                continue
                
            event_type = data.get("event_type")
            if not event_type:
                logger.warning("Received event with missing 'event_type'")
                continue
                
            # Populate metadata
            data.setdefault("event_id", str(uuid.uuid4()))
            data.setdefault("source", f"{agent_type}-agent")
            data.setdefault("source_id", agent_id)
            data.setdefault("correlation_id", str(uuid.uuid4()))
            data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
            
            # Publish to Redis Stream
            await redis_client.publish_event(data)
            
            # If it's a heartbeat, reply with pong to acknowledge
            if event_type.endswith(".heartbeat"):
                await websocket.send_json({
                    "event_type": f"{agent_type}.heartbeat.acknowledged",
                    "correlation_id": data.get("correlation_id")
                })
                
    except asyncio.TimeoutError:
        logger.warning(f"Connection timed out for {agent_type} agent '{agent_id}' (no heartbeat).")
        manager.disconnect_agent(agent_id, agent_type)
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception:
            pass
    except WebSocketDisconnect:
        manager.disconnect_agent(agent_id, agent_type)
    except Exception as e:
        logger.error(f"Error in {agent_type} agent '{agent_id}' WebSocket loop: {e}")
        manager.disconnect_agent(agent_id, agent_type)

@app.websocket("/ws/device-agent")
async def ws_device_agent(
    websocket: WebSocket,
    agent_id: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
    x_agent_id: Optional[str] = Header(None),
    x_agent_token: Optional[str] = Header(None)
):
    # Resolve agent_id and token from query params or headers
    resolved_id = x_agent_id or agent_id or "default-device-agent"
    resolved_token = x_agent_token or token
    
    await handle_agent_connection(
        websocket=websocket,
        agent_id=resolved_id,
        agent_type="device",
        expected_token=settings.DEVICE_AGENT_TOKEN,
        token=resolved_token
    )

@app.websocket("/ws/camera-agent")
async def ws_camera_agent(
    websocket: WebSocket,
    agent_id: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
    x_agent_id: Optional[str] = Header(None),
    x_agent_token: Optional[str] = Header(None)
):
    # Resolve agent_id and token from query params or headers
    resolved_id = x_agent_id or agent_id or "default-camera-agent"
    resolved_token = x_agent_token or token
    
    await handle_agent_connection(
        websocket=websocket,
        agent_id=resolved_id,
        agent_type="camera",
        expected_token=settings.CAMERA_AGENT_TOKEN,
        token=resolved_token
    )
