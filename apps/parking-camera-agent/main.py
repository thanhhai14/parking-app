import asyncio
import io
import json
import logging
import os
import random
import uuid
from datetime import datetime, timezone
import yaml
import websockets
import httpx
from PIL import Image, ImageDraw

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s:%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("parking-camera-agent")

def load_config():
    config_path = "/app/config/camera-agent.yaml"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to read config file: {e}")
            
    # Fallback to environment variables
    return {
        "agent": {
            "id": os.getenv("AGENT_ID", "camera-agent-gate-01"),
            "token": os.getenv("AGENT_TOKEN", "CHANGE_ME_CAMERA_AGENT_TOKEN"),
            "type": "camera"
        },
        "gateway": {
            "url": os.getenv("GATEWAY_WS_URL", "ws://parking-gateway:8300/ws/camera-agent"),
            "heartbeat_interval": 30,
            "reconnect_interval": 5
        },
        "api": {
            "upload_url": os.getenv("API_UPLOAD_URL", "http://parking-api:8000/api/v1/media/upload")
        }
    }

config = load_config()
AGENT_ID = config["agent"]["id"]
TOKEN = config["agent"]["token"]
GATEWAY_URL = config["gateway"]["url"]
HEARTBEAT_INTERVAL = config["gateway"].get("heartbeat_interval", 30)
RECONNECT_INTERVAL = config["gateway"].get("reconnect_interval", 5)
API_UPLOAD_URL = config["api"]["upload_url"]

# Calculate base API url from upload url (to login)
# e.g., "http://parking-api:8000/api/v1/media/upload" -> "http://parking-api:8000/api/v1/auth/login"
API_BASE_URL = API_UPLOAD_URL.split("/api/v1/")[0]
LOGIN_URL = f"{API_BASE_URL}/api/v1/auth/login"

class CameraAgent:
    def __init__(self):
        self.ws = None
        self.is_connected = False
        self.send_loop_task = None
        self.jwt_token = None

    async def get_jwt_token(self) -> str:
        """
        Log in as admin to retrieve JWT token for media uploads
        """
        if self.jwt_token:
            return self.jwt_token
            
        logger.info(f"Authenticating with API at {LOGIN_URL}...")
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    LOGIN_URL,
                    data={"username": "admin", "password": "admin123"},
                    timeout=10.0
                )
                if resp.status_code == 200:
                    self.jwt_token = resp.json()["access_token"]
                    logger.info("Authentication successful. JWT retrieved.")
                    return self.jwt_token
                else:
                    logger.error(f"Authentication failed: {resp.status_code} - {resp.text}")
            except Exception as e:
                logger.error(f"Failed to authenticate with API: {e}")
        return ""

    def generate_mock_image(self, plate_number: str) -> bytes:
        """
        Paint a mock gray image with a white license plate frame and text plate number.
        """
        img = Image.new("RGB", (800, 600), color=(128, 128, 128))
        draw = ImageDraw.Draw(img)
        
        # Draw license plate box
        draw.rectangle([250, 220, 550, 320], fill=(255, 255, 255), outline=(0, 0, 0), width=5)
        
        # Draw license plate text
        draw.text((320, 260), plate_number, fill=(0, 0, 0))
        
        # Save to JPEG buffer
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()

    async def upload_mock_snapshot(self, plate_number: str) -> str:
        """
        Generates mock image and uploads it to the parking-api upload endpoint.
        Returns the uploaded media UUID.
        """
        token = await self.get_jwt_token()
        if not token:
            logger.error("Skipping upload: No valid JWT token.")
            return ""
            
        image_bytes = self.generate_mock_image(plate_number)
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        # Prepare multipart files
        files = {
            "file": ("snapshot.jpg", image_bytes, "image/jpeg")
        }
        
        data = {
            "media_type": "snapshot",
            "source_type": "camera"
        }
        
        logger.info(f"Uploading mock snapshot for plate '{plate_number}' to {API_UPLOAD_URL}...")
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    API_UPLOAD_URL,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=15.0
                )
                if resp.status_code == 201:
                    media_id = resp.json()["id"]
                    logger.info(f"Snapshot uploaded successfully. Media ID: {media_id}")
                    return media_id
                elif resp.status_code == 401:
                    logger.warning("JWT expired. Clearing token and retrying login...")
                    self.jwt_token = None
                    return await self.upload_mock_snapshot(plate_number)
                else:
                    logger.error(f"Failed to upload snapshot: {resp.status_code} - {resp.text}")
            except Exception as e:
                logger.error(f"Error calling upload API: {e}")
        return ""

    async def connect_and_run(self):
        ws_url = f"{GATEWAY_URL}?agent_id={AGENT_ID}&token={TOKEN}"
        logger.info(f"Connecting to Gateway at {GATEWAY_URL}...")
        
        while True:
            try:
                async with websockets.connect(ws_url) as ws:
                    self.ws = ws
                    self.is_connected = True
                    logger.info("Connected to Gateway successfully.")
                    
                    # Start heartbeat loop
                    self.send_loop_task = asyncio.create_task(self.heartbeat_loop())
                    
                    # Listen for incoming snapshot commands
                    await self.listen_commands()
            except (websockets.exceptions.ConnectionClosed, OSError) as e:
                logger.warning(f"Connection lost or failed to connect: {e}. Retrying in {RECONNECT_INTERVAL} seconds...")
            except Exception as e:
                logger.error(f"Unexpected error: {e}. Retrying in {RECONNECT_INTERVAL} seconds...", exc_info=True)
                
            self.is_connected = False
            self.ws = None
            if self.send_loop_task:
                self.send_loop_task.cancel()
                self.send_loop_task = None
                
            await asyncio.sleep(RECONNECT_INTERVAL)

    async def heartbeat_loop(self):
        try:
            while self.is_connected and self.ws:
                heartbeat = {
                    "event_type": "camera.heartbeat",
                    "source": "camera-agent",
                    "source_id": AGENT_ID,
                    "payload": {
                        "status": "online",
                        "uptime": int(asyncio.get_event_loop().time())
                    }
                }
                await self.ws.send(json.dumps(heartbeat))
                logger.info("Heartbeat sent.")
                await asyncio.sleep(HEARTBEAT_INTERVAL)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in heartbeat loop: {e}")

    async def listen_commands(self):
        try:
            while self.is_connected and self.ws:
                message = await self.ws.recv()
                data = json.loads(message)
                logger.info(f"Received command/message from gateway: {data}")
                
                cmd_type = data.get("command_type", "")
                if cmd_type == "camera.snapshot.request" or data.get("command") == "camera.snapshot":
                    correlation_id = data.get("correlation_id", str(uuid.uuid4()))
                    
                    # Get plate number from correlation payload or random simulation
                    # Since it is a mock flow, we can use a default or dynamic plate
                    cmd_payload = data.get("payload", {})
                    plate_number = cmd_payload.get("plate_number", "30-F1 88888")
                    
                    # Trigger mock snapshot and upload
                    media_id = await self.upload_mock_snapshot(plate_number)
                    
                    if media_id:
                        # Respond with camera.snapshot.completed event
                        completed_event = {
                            "event_type": "camera.snapshot.completed",
                            "source": "camera-agent",
                            "source_id": AGENT_ID,
                            "correlation_id": correlation_id,
                            "site_id": data.get("site_id"),
                            "gate_id": data.get("gate_id"),
                            "camera_id": data.get("target_camera_id"),
                            "payload": {
                                "media_id": media_id,
                                "plate_number": plate_number
                            },
                            "created_at": datetime.now(timezone.utc).isoformat()
                        }
                        await self.ws.send(json.dumps(completed_event))
                        logger.info("Snapshot completed event sent to gateway.")
                    else:
                        logger.error("Failed to upload snapshot. Completion event not sent.")
                        
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Gateway connection closed during commands listening.")
        except Exception as e:
            logger.error(f"Error in commands listener: {e}")

if __name__ == "__main__":
    agent = CameraAgent()
    try:
        asyncio.run(agent.connect_and_run())
    except KeyboardInterrupt:
        logger.info("Agent shutting down.")
