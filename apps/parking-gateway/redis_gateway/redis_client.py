import asyncio
import json
import logging
import uuid
import redis.asyncio as aioredis
from core.config import settings
from websocket.connection_manager import manager

logger = logging.getLogger("parking-gateway.redis")

class RedisGatewayClient:
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.redis = None
        self._pubsub_task = None
        self._commands_task = None
        self.consumer_name = f"gateway-{uuid.uuid4().hex[:6]}"
        self.group_name = "parking-gateway-group"
        self.commands_stream = "parking.commands"
        self.realtime_channel = "parking.realtime"

    async def connect(self):
        self.redis = aioredis.from_url(
            self.redis_url,
            decode_responses=True,
            socket_timeout=None,
            socket_connect_timeout=None
        )
        logger.info("Connected to Redis successfully.")
        
        # Start background listeners
        self._pubsub_task = asyncio.create_task(self.listen_realtime_pubsub())
        self._commands_task = asyncio.create_task(self.listen_commands_stream())

    async def disconnect(self):
        if self._pubsub_task:
            self._pubsub_task.cancel()
        if self._commands_task:
            self._commands_task.cancel()
            
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis.")

    async def listen_realtime_pubsub(self):
        """
        Listen to Redis Pub/Sub channel `parking.realtime` and broadcast events to all web clients.
        """
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self.realtime_channel)
        logger.info(f"Subscribed to Pub/Sub channel '{self.realtime_channel}'")
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        logger.info(f"Received realtime event: {data.get('event_type')}")
                        await manager.broadcast_to_web(data)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to decode Pub/Sub message: {message['data']}")
                    except Exception as e:
                        logger.error(f"Error broadcasting Pub/Sub event: {e}")
        except asyncio.CancelledError:
            logger.info("Pub/Sub listener cancelled.")
        except Exception as e:
            logger.error(f"Redis Pub/Sub connection error: {e}")
            # Wait and retry connection
            await asyncio.sleep(5)
            self._pubsub_task = asyncio.create_task(self.listen_realtime_pubsub())

    async def listen_commands_stream(self):
        """
        Read commands from Redis Stream `parking.commands` using consumer group and route to agents.
        """
        # Create consumer group if not exists
        try:
            await self.redis.xgroup_create(
                name=self.commands_stream,
                groupname=self.group_name,
                id="$",
                mkstream=True
            )
            logger.info(f"Created Consumer Group '{self.group_name}' for Stream '{self.commands_stream}'")
        except Exception as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer Group '{self.group_name}' already exists.")
            else:
                logger.error(f"Failed to create consumer group: {e}")

        logger.info(f"Started reading commands from Stream '{self.commands_stream}' using group '{self.group_name}'")
        
        try:
            while True:
                # Read new messages
                response = await self.redis.xreadgroup(
                    groupname=self.group_name,
                    consumername=self.consumer_name,
                    streams={self.commands_stream: ">"},
                    count=10,
                    block=2000
                )
                
                if not response:
                    continue
                    
                for stream, messages in response:
                    for message_id, payload in messages:
                        try:
                            # Redis streams payload is flat key-value strings. 
                            # If payload was serialized as a nested JSON, parse it.
                            logger.info(f"Received command message: {payload}")
                            
                            cmd_data = {}
                            if "data" in payload:
                                cmd_data = json.loads(payload["data"])
                            else:
                                # Fallback if fields are flat
                                cmd_data = payload
                                if isinstance(cmd_data.get("payload"), str):
                                    cmd_data["payload"] = json.loads(cmd_data["payload"])
                                    
                            agent_id = cmd_data.get("target_agent_id")
                            cmd_type = cmd_data.get("command_type", "")
                            
                            # Determine agent type
                            agent_type = "camera" if cmd_type.startswith("camera.") else "device"
                            
                            if agent_id:
                                success = await manager.send_command_to_agent(
                                    agent_id=agent_id,
                                    agent_type=agent_type,
                                    command=cmd_data
                                )
                                if success:
                                    # Send XACK if routed successfully
                                    await self.redis.xack(self.commands_stream, self.group_name, message_id)
                                    logger.info(f"Command ACKed: {message_id}")
                                else:
                                    logger.warning(f"Could not route command to agent {agent_id}. Will retry later.")
                            else:
                                logger.error("Missing 'target_agent_id' in command payload.")
                                # Ack it anyway to not block the stream
                                await self.redis.xack(self.commands_stream, self.group_name, message_id)
                        except Exception as e:
                            logger.error(f"Error processing command message {message_id}: {e}")
                            # Ack it anyway to avoid poison pills blocking processing
                            await self.redis.xack(self.commands_stream, self.group_name, message_id)
                            
        except asyncio.CancelledError:
            logger.info("Commands stream reader cancelled.")
        except Exception as e:
            logger.error(f"Redis Stream reader connection error: {e}")
            await asyncio.sleep(5)
            self._commands_task = asyncio.create_task(self.listen_commands_stream())

    async def publish_event(self, event_data: dict):
        """
        Publish an event received from WebSockets agent into the `parking.events` Redis Stream.
        """
        if not self.redis:
            raise RuntimeError("Redis is not connected.")
            
        stream_name = "parking.events"
        # Store serialized JSON under the key 'data' to preserve nesting structure
        serialized_data = json.dumps(event_data)
        message_id = await self.redis.xadd(stream_name, {"data": serialized_data})
        logger.info(f"Published event '{event_data.get('event_type')}' to Stream '{stream_name}' with ID: {message_id}")
        return message_id

redis_client = RedisGatewayClient()
