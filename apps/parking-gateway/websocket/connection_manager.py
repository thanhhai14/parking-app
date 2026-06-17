import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger("parking-gateway.connection_manager")

class ConnectionManager:
    def __init__(self):
        # Web clients receive real-time updates
        self.web_clients: Set[WebSocket] = set()
        
        # Hardware agents receive commands and send telemetry
        self.device_agents: Dict[str, WebSocket] = {}
        self.camera_agents: Dict[str, WebSocket] = {}
        
    async def connect_web(self, websocket: WebSocket):
        await websocket.accept()
        self.web_clients.add(websocket)
        logger.info(f"Web client connected. Total web clients: {len(self.web_clients)}")
        
    def disconnect_web(self, websocket: WebSocket):
        if websocket in self.web_clients:
            self.web_clients.remove(websocket)
            logger.info(f"Web client disconnected. Total web clients: {len(self.web_clients)}")
            
    async def connect_agent(self, agent_id: str, agent_type: str, websocket: WebSocket):
        await websocket.accept()
        if agent_type == "device":
            self.device_agents[agent_id] = websocket
            logger.info(f"Device agent '{agent_id}' connected. Total device agents: {len(self.device_agents)}")
        elif agent_type == "camera":
            self.camera_agents[agent_id] = websocket
            logger.info(f"Camera agent '{agent_id}' connected. Total camera agents: {len(self.camera_agents)}")
            
    def disconnect_agent(self, agent_id: str, agent_type: str):
        if agent_type == "device":
            if agent_id in self.device_agents:
                del self.device_agents[agent_id]
                logger.info(f"Device agent '{agent_id}' disconnected. Total device agents: {len(self.device_agents)}")
        elif agent_type == "camera":
            if agent_id in self.camera_agents:
                del self.camera_agents[agent_id]
                logger.info(f"Camera agent '{agent_id}' disconnected. Total camera agents: {len(self.camera_agents)}")
                
    async def broadcast_to_web(self, message: dict):
        if not self.web_clients:
            return
        logger.debug(f"Broadcasting to {len(self.web_clients)} web clients: {message}")
        disconnected = set()
        for websocket in self.web_clients:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Error sending message to web client: {e}")
                disconnected.add(websocket)
                
        for websocket in disconnected:
            self.disconnect_web(websocket)
            
    async def send_command_to_agent(self, agent_id: str, agent_type: str, command: dict) -> bool:
        websocket = None
        if agent_type == "device":
            websocket = self.device_agents.get(agent_id)
        elif agent_type == "camera":
            websocket = self.camera_agents.get(agent_id)
            
        if not websocket:
            logger.warning(f"Agent '{agent_id}' ({agent_type}) is not connected.")
            return False
            
        try:
            await websocket.send_json(command)
            logger.info(f"Command sent to agent '{agent_id}' ({agent_type}): {command}")
            return True
        except Exception as e:
            logger.error(f"Failed to send command to agent '{agent_id}': {e}")
            self.disconnect_agent(agent_id, agent_type)
            return False

manager = ConnectionManager()
