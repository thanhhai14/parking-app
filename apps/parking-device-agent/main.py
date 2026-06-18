import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
import yaml
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s:%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("parking-device-agent")

def load_config():
    config_path = "/app/config/device-agent.yaml"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to read config file: {e}")
            
    # Fallback to environment variables
    return {
        "agent": {
            "id": os.getenv("AGENT_ID", "device-agent-gate-01"),
            "token": os.getenv("AGENT_TOKEN", "CHANGE_ME_DEVICE_AGENT_TOKEN"),
            "type": "device"
        },
        "gateway": {
            "url": os.getenv("GATEWAY_WS_URL", "ws://parking-gateway:8300/ws/device-agent"),
            "heartbeat_interval": 30,
            "reconnect_interval": 5
        },
        "storage": {
            "offline_queue_file": "/app/data/offline_events.json"
        }
    }

config = load_config()
AGENT_ID = config["agent"]["id"]
TOKEN = config["agent"]["token"]
GATEWAY_URL = config["gateway"]["url"]
HEARTBEAT_INTERVAL = config["gateway"].get("heartbeat_interval", 30)
RECONNECT_INTERVAL = config["gateway"].get("reconnect_interval", 5)
OFFLINE_FILE = config["storage"]["offline_queue_file"]

# Ensure directories exist
os.makedirs(os.path.dirname(OFFLINE_FILE), exist_ok=True)

class DeviceAgent:
    def __init__(self):
        self.ws = None
        self.is_connected = False
        self.send_loop_task = None
        self.scan_simulator_task = None
        self.scan_state = 0  # 0 for Entry, 1 for Exit (alternating)

    def load_offline_events(self) -> list:
        if os.path.exists(OFFLINE_FILE):
            try:
                with open(OFFLINE_FILE, "r") as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
            except Exception as e:
                logger.error(f"Error reading offline events: {e}")
        return []

    def save_offline_events(self, events: list):
        try:
            with open(OFFLINE_FILE, "w") as f:
                f.write(json.dumps(events))
            logger.info(f"Saved {len(events)} offline events to local file.")
        except Exception as e:
            logger.error(f"Error saving offline events: {e}")

    def append_offline_event(self, event: dict):
        events = self.load_offline_events()
        events.append(event)
        self.save_offline_events(events)

    async def flush_offline_events(self):
        events = self.load_offline_events()
        if not events:
            return
            
        logger.info(f"Flushing {len(events)} offline events to gateway...")
        remaining_events = []
        
        for event in events:
            if not self.is_connected or not self.ws:
                remaining_events.append(event)
                continue
            try:
                # Update timestamp to denote actual sending time/offline delay
                event["sent_offline_retry"] = True
                await self.ws.send(json.dumps(event))
                logger.info(f"Offline event flushed successfully: {event.get('event_type')}")
                await asyncio.sleep(0.2)
            except Exception as e:
                logger.error(f"Failed to send offline event: {e}")
                remaining_events.append(event)
                
        if remaining_events:
            self.save_offline_events(remaining_events)
        else:
            # Delete file if all sent successfully
            try:
                if os.path.exists(OFFLINE_FILE):
                    os.remove(OFFLINE_FILE)
                logger.info("All offline events flushed. Local cache cleared.")
            except Exception as e:
                logger.error(f"Error deleting offline file: {e}")

    async def connect_and_run(self):
        # Build WebSocket connection URL with credentials
        ws_url = f"{GATEWAY_URL}?agent_id={AGENT_ID}&token={TOKEN}"
        logger.info(f"Connecting to Gateway at {GATEWAY_URL}...")
        
        while True:
            try:
                async with websockets.connect(ws_url) as ws:
                    self.ws = ws
                    self.is_connected = True
                    logger.info("Connected to Gateway successfully.")
                    
                    # Flush any offline events queued
                    await self.flush_offline_events()
                    
                    # Start heartbeat and simulated scans
                    self.send_loop_task = asyncio.create_task(self.heartbeat_loop())
                    if not self.scan_simulator_task:
                        self.scan_simulator_task = asyncio.create_task(self.scan_simulator_loop())
                        
                    # Listen for incoming commands
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
                    "event_type": "device.heartbeat",
                    "source": "device-agent",
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

    async def scan_simulator_loop(self):
        """
        Simulate a vehicle card quẹt thẻ every 20 seconds.
        Alternates between Check-In (GATE-IN-EDGE-01) and Check-Out (GATE-OUT-EDGE-01).
        """
        await asyncio.sleep(5)  # Wait for initial connections
        while True:
            try:
                # Alternate scan destination gates
                gate_code = "GATE-IN-EDGE-01" if self.scan_state == 0 else "GATE-OUT-EDGE-01"
                action_name = "CHECK-IN" if self.scan_state == 0 else "CHECK-OUT"
                
                # Mock scanning data
                scan_event = {
                    "event_id": str(uuid.uuid4()),
                    "event_type": "card.scanned",
                    "source": "device-agent",
                    "source_id": AGENT_ID,
                    "correlation_id": str(uuid.uuid4()),
                    "payload": {
                        "card_uid": "04A12345",  # Seedeed in DB migration
                        "gate_code": gate_code,
                        "plate_number": "30-F1 88888"
                    },
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                logger.info(f"Simulating card scan for {action_name} at gate {gate_code}...")
                
                if self.is_connected and self.ws:
                    await self.ws.send(json.dumps(scan_event))
                    logger.info("Simulated scan event sent directly to gateway.")
                else:
                    logger.warning("Agent disconnected. Queueing event locally.")
                    self.append_offline_event(scan_event)
                    
                # Alternate state
                self.scan_state = 1 - self.scan_state
                
            except Exception as e:
                logger.error(f"Error in scan simulator: {e}")
                
            # Wait 20 seconds before next scan
            await asyncio.sleep(20)

    async def listen_commands(self):
        try:
            while self.is_connected and self.ws:
                message = await self.ws.recv()
                data = json.loads(message)
                logger.info(f"Received command/message from gateway: {data}")
                
                # Verify if it's a barrier opening command
                cmd_type = data.get("command_type", "")
                if cmd_type == "barrier.open.request" or data.get("command") == "barrier.open":
                    correlation_id = data.get("correlation_id", str(uuid.uuid4()))
                    
                    logger.info("====================================")
                    logger.info("!!! [BARRIER OPENED] !!!")
                    logger.info("====================================")
                    
                    # Respond with barrier.opened confirmation event
                    opened_event = {
                        "event_type": "barrier.opened",
                        "source": "device-agent",
                        "source_id": AGENT_ID,
                        "correlation_id": correlation_id,
                        "payload": {
                            "status": "open",
                            "gate_id": data.get("gate_id"),
                            "device_id": data.get("target_device_id")
                        }
                    }
                    await self.ws.send(json.dumps(opened_event))
                    logger.info("Barrier confirmation event sent to gateway.")
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Gateway connection closed during commands listening.")
        except Exception as e:
            logger.error(f"Error in commands listener: {e}")

if __name__ == "__main__":
    agent = DeviceAgent()
    try:
        asyncio.run(agent.connect_and_run())
    except KeyboardInterrupt:
        logger.info("Agent shutting down.")
