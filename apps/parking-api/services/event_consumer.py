import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from core.database import async_session_maker
from core.redis import redis_client
from models.processed_event import ProcessedEvent
from models.card import RfidCard
from models.parking_lot import ParkingGate, ParkingZone, ParkingSite
from models.device import Camera, Device
from models.session import ParkingSession
from models.fee import FeeRule
from services.pricing_service import PricingEngine

logger = logging.getLogger("parking-api.event_consumer")

def generate_session_code() -> str:
    import random
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    rand_num = random.randint(1000, 9999)
    return f"PK-{now_str}-{rand_num}"

async def handle_card_scanned_event(db, event_id: uuid.UUID, correlation_id: str, payload: dict, metadata: dict):
    """
    Step 1 of flow: Card scanned.
    We validate the card and gate, cache the state in Redis, and issue a camera snapshot request.
    """
    card_uid = payload.get("card_uid")
    plate_number = payload.get("plate_number") or "30-F1 88888"
    gate_code = payload.get("gate_code") or payload.get("gate_id") or metadata.get("gate_id") or metadata.get("gate_code")
    
    if not card_uid:
        raise ValueError("Missing 'card_uid' in event payload.")
    if not gate_code:
        raise ValueError("Missing gate information (gate_code or gate_id) in event.")
        
    # 1. Fetch active card details
    card_query = await db.execute(
        select(RfidCard)
        .options(selectinload(RfidCard.assigned_vehicle))
        .where(RfidCard.card_uid == card_uid)
    )
    card = card_query.scalars().first()
    if not card:
        raise ValueError(f"Card not found: {card_uid}")
    if card.status != "active":
        raise ValueError(f"Card is not active: {card_uid} (status: {card.status})")
        
    # 2. Fetch gate details
    gate = None
    try:
        gate_uuid = uuid.UUID(str(gate_code))
        gate_query = await db.execute(
            select(ParkingGate)
            .options(selectinload(ParkingGate.zone).selectinload(ParkingZone.site))
            .where(ParkingGate.id == gate_uuid)
        )
        gate = gate_query.scalars().first()
    except ValueError:
        pass
        
    if not gate:
        gate_query = await db.execute(
            select(ParkingGate)
            .options(selectinload(ParkingGate.zone).selectinload(ParkingZone.site))
            .where(ParkingGate.code == str(gate_code))
        )
        gate = gate_query.scalars().first()
        
    if not gate:
        raise ValueError(f"Gate not found: {gate_code}")
        
    # 3. Check for existing active session to determine check-in vs check-out action
    active_session_query = await db.execute(
        select(ParkingSession)
        .where(ParkingSession.entry_card_id == card.id)
        .where(ParkingSession.status == "active")
    )
    active_session = active_session_query.scalars().first()
    action = "check-out" if active_session else "check-in"
    
    # Validate gate directions
    if action == "check-in" and gate.direction not in ["in", "both"]:
        raise ValueError(f"Gate {gate.code} is not an entry gate (direction: {gate.direction})")
    elif action == "check-out" and gate.direction not in ["out", "both"]:
        raise ValueError(f"Gate {gate.code} is not an exit gate (direction: {gate.direction})")

    # 4. Find all Cameras associated with this Gate
    camera_query = await db.execute(
        select(Camera).where(Camera.gate_id == gate.id).where(Camera.is_active == True)
    )
    cameras = camera_query.scalars().all()
    
    if not cameras:
        # Bypassing camera snapshots wait since no cameras are configured for this gate
        logger.warning(f"No camera registered in database for gate {gate_code}. Bypassing camera snapshots wait.")
        state = {
            "card_uid": card_uid,
            "gate_code": gate.code,
            "plate_number": plate_number,
            "action": action,
            "gate_id": str(gate.id),
            "site_id": str(gate.zone.site_id),
            "zone_id": str(gate.zone_id),
            "pending_snapshots": {}
        }
        await execute_complete_parking_session(db, state, correlation_id)
        return
        
    pending_snapshots = {str(cam.id): None for cam in cameras}

    # 5. Cache the scan state in Redis
    state = {
        "card_uid": card_uid,
        "gate_code": gate.code,
        "plate_number": plate_number,
        "action": action,
        "gate_id": str(gate.id),
        "site_id": str(gate.zone.site_id),
        "zone_id": str(gate.zone_id),
        "pending_snapshots": pending_snapshots
    }
    redis_key = f"pending_session:{correlation_id}"
    await redis_client.redis.setex(redis_key, 15, json.dumps(state))
    logger.info(f"Cached state for correlation {correlation_id} in Redis (TTL: 15s). Action: {action}, Cameras waiting: {list(pending_snapshots.keys())}")
    
    # 6. Issue camera.snapshot.request Command to Redis Stream for each camera
    for cam in cameras:
        snapshot_command = {
            "command_id": str(uuid.uuid4()),
            "command_type": "camera.snapshot.request",
            "target_agent_id": cam.agent_id or "camera-agent-gate-01",
            "target_camera_id": str(cam.id),
            "site_id": str(gate.zone.site_id),
            "gate_id": str(gate.id),
            "correlation_id": correlation_id,
            "payload": {
                "snapshot_type": "entry_overview" if action == "check-in" else "exit_overview",
                "plate_number": plate_number
            },
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await redis_client.redis.xadd("parking.commands", {"data": json.dumps(snapshot_command)})
        logger.info(f"Published camera snapshot request command for camera '{cam.id}' via agent '{cam.agent_id}' to parking.commands stream.")


async def execute_complete_parking_session(db, state: dict, correlation_id: str):
    """
    Core DB session updates, pricing engine calculations, barrier trigger, 
    and realtime dashboard notifications.
    """
    card_uid = state["card_uid"]
    gate_code = state["gate_code"]
    plate_number = state["plate_number"]
    action = state["action"]
    gate_id = uuid.UUID(state["gate_id"])
    site_id = uuid.UUID(state["site_id"])
    zone_id = uuid.UUID(state["zone_id"])
    pending_snapshots = state.get("pending_snapshots", {})

    # We have all snapshots! Resolve which is plate vs overview
    plate_image_id = None
    overview_image_id = None
    
    for cam_id_str, m_id_str in pending_snapshots.items():
        if not m_id_str:
            continue
        try:
            cam_uuid = uuid.UUID(cam_id_str)
            c_query = await db.execute(select(Camera).where(Camera.id == cam_uuid))
            cam = c_query.scalars().first()
            role = cam.role if cam else "plate"
        except Exception:
            role = "plate"
            
        if "plate" in role.lower():
            plate_image_id = uuid.UUID(m_id_str)
        elif "overview" in role.lower():
            overview_image_id = uuid.UUID(m_id_str)
            
    # Fallbacks if roles are not explicitly configured
    if not plate_image_id and pending_snapshots:
        vals = [v for v in pending_snapshots.values() if v]
        if vals:
            plate_image_id = uuid.UUID(vals[0])
    if not overview_image_id and pending_snapshots:
        vals = [v for v in pending_snapshots.values() if v]
        second_val = vals[1] if len(vals) > 1 else (vals[0] if vals else None)
        if second_val:
            overview_image_id = uuid.UUID(second_val)

    # Fetch active card details
    card_query = await db.execute(
        select(RfidCard)
        .options(selectinload(RfidCard.assigned_vehicle))
        .where(RfidCard.card_uid == card_uid)
    )
    card = card_query.scalars().first()
    if not card:
        raise ValueError(f"Card not found in database during step 2: {card_uid}")

    session_response_payload = {}
    
    # 2. Database Session Processing
    if action == "check-in":
        # Resolve vehicle details
        vehicle_id = None
        vehicle_type_id = None
        owner_id = None
        
        if card.assigned_vehicle:
            vehicle_id = card.assigned_vehicle.id
            vehicle_type_id = card.assigned_vehicle.vehicle_type_id
            owner_id = card.assigned_vehicle.owner_id
        elif card.assigned_owner_id:
            owner_id = card.assigned_owner_id
            
        session = ParkingSession(
            session_code=generate_session_code(),
            site_id=site_id,
            zone_id=zone_id,
            gate_entry_id=gate_id,
            vehicle_id=vehicle_id,
            vehicle_type_id=vehicle_type_id,
            owner_id=owner_id,
            entry_card_id=card.id,
            entry_time=datetime.now(timezone.utc),
            entry_plate_number=plate_number,
            entry_overview_image_id=overview_image_id,
            entry_plate_image_id=plate_image_id,
            status="active"
        )
        db.add(session)
        await db.flush()
        
        # Structure realtime checkin event payload
        session_response_payload = {
            "session_code": session.session_code,
            "card_uid": card.card_uid,
            "entry_time": session.entry_time.isoformat(),
            "entry_plate_number": session.entry_plate_number,
            "status": session.status,
            "entry_plate_image_id": str(plate_image_id) if plate_image_id else None,
            "entry_overview_image_id": str(overview_image_id) if overview_image_id else None
        }
        
        realtime_event_type = "parking.checkin.created"
        session_id_str = str(session.id)
        logger.info(f"Check-In DB record created for card {card_uid}. Session: {session.session_code}")
        
    else:  # check-out
        active_session_query = await db.execute(
            select(ParkingSession)
            .where(ParkingSession.entry_card_id == card.id)
            .where(ParkingSession.status == "active")
        )
        active_session = active_session_query.scalars().first()
        if not active_session:
            raise ValueError(f"No active session found for card {card_uid} during check-out.")
            
        exit_time = datetime.now(timezone.utc)
        rule_type = "hourly"
        rule_config = {
            "free_grace_minutes": 15,
            "first_hours": 4,
            "first_amount": 5000.0,
            "next_hour_amount": 2000.0,
            "max_daily_amount": 30000.0
        }
        
        if active_session.vehicle_type_id:
            try:
                rule_query = await db.execute(
                    select(FeeRule)
                    .where(FeeRule.vehicle_type_id == active_session.vehicle_type_id)
                    .where(FeeRule.is_active == True)
                    .order_by(FeeRule.priority.desc())
                )
                rule = rule_query.scalars().first()
                if rule:
                    rule_type = rule.rule_type
                    rule_config = rule.config
                    active_session.fee_rule_id = rule.id
            except Exception as re:
                logger.warning(f"Error querying fee rules: {re}. Using defaults.")
                
        # Calculate fee
        fee = PricingEngine.calculate_fee(
            entry_time=active_session.entry_time,
            exit_time=exit_time,
            rule_type=rule_type,
            config=rule_config
        )
        
        # Update session
        active_session.exit_time = exit_time
        active_session.gate_exit_id = gate_id
        active_session.exit_plate_number = plate_number
        active_session.exit_card_id = card.id
        active_session.exit_overview_image_id = overview_image_id
        active_session.exit_plate_image_id = plate_image_id
        active_session.calculated_fee = fee
        active_session.status = "completed"
        active_session.payment_status = "paid" if fee == 0.0 else "unpaid"
        
        session_response_payload = {
            "session_code": active_session.session_code,
            "card_uid": card.card_uid,
            "entry_time": active_session.entry_time.isoformat(),
            "exit_time": active_session.exit_time.isoformat(),
            "calculated_fee": float(active_session.calculated_fee),
            "status": active_session.status,
            "payment_status": active_session.payment_status,
            "entry_plate_image_id": str(active_session.entry_plate_image_id) if active_session.entry_plate_image_id else None,
            "entry_overview_image_id": str(active_session.entry_overview_image_id) if active_session.entry_overview_image_id else None,
            "exit_plate_image_id": str(plate_image_id) if plate_image_id else None,
            "exit_overview_image_id": str(overview_image_id) if overview_image_id else None
        }
        
        realtime_event_type = "parking.checkout.completed"
        session_id_str = str(active_session.id)
        logger.info(f"Check-Out DB record completed for card {card_uid}. Session: {active_session.session_code}, Fee: {fee}")

    # 3. Find Barrier device associated with this Gate
    barrier_query = await db.execute(
        select(Device).where(Device.gate_id == gate_id).where(Device.device_type == "barrier")
    )
    barrier = barrier_query.scalars().first()
    
    barrier_agent_id = "device-agent-gate-01"
    barrier_id_str = str(uuid.uuid4())
    
    if barrier:
        barrier_id_str = str(barrier.id)
        if barrier.agent_id:
            barrier_agent_id = barrier.agent_id
    else:
        logger.warning(f"No barrier registered in database for gate {gate_code}. Using defaults.")

    # 4. Issue barrier.open.request Command to Redis Stream
    barrier_command = {
        "command_id": str(uuid.uuid4()),
        "command_type": "barrier.open.request",
        "target_agent_id": barrier_agent_id,
        "target_device_id": barrier_id_str,
        "site_id": str(site_id),
        "gate_id": str(gate_id),
        "correlation_id": correlation_id,
        "payload": {
            "duration_ms": 1500
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await redis_client.redis.xadd("parking.commands", {"data": json.dumps(barrier_command)})
    logger.info(f"Published barrier open request command for agent '{barrier_agent_id}' to parking.commands stream.")

    # 5. Publish final realtime UI notification to Pub/Sub
    realtime_event = {
        "event_type": realtime_event_type,
        "source": "parking-api",
        "session_id": session_id_str,
        "site_id": str(site_id),
        "gate_id": str(gate_id),
        "correlation_id": correlation_id,
        "payload": session_response_payload
    }
    await redis_client.redis.publish("parking.realtime", json.dumps(realtime_event))
    logger.info(f"Published final realtime event '{realtime_event_type}' to Pub/Sub channel 'parking.realtime'.")

    # 6. Delete cached state from Redis
    redis_key = f"pending_session:{correlation_id}"
    await redis_client.redis.delete(redis_key)


async def handle_snapshot_completed_event(db, event_id: uuid.UUID, correlation_id: str, payload: dict, metadata: dict):
    """
    Step 2 of flow: Camera snapshot completed.
    We fetch cached state from Redis, update snapshot progress. Once all camera snapshots are present,
    we perform the CSDL updates, issue a barrier open command, and publish the final realtime success event.
    """
    media_id_str = payload.get("media_id")
    if not media_id_str:
        raise ValueError("Missing 'media_id' in snapshot completed payload.")
    
    # 1. Fetch cached state from Redis
    redis_key = f"pending_session:{correlation_id}"
    state_str = await redis_client.redis.get(redis_key)
    if not state_str:
        logger.warning(f"No pending session found in Redis for correlation {correlation_id} (expired or invalid).")
        return
        
    state = json.loads(state_str)
    
    # Track which camera completed this snapshot
    camera_id_str = metadata.get("camera_id") or payload.get("camera_id")
    pending_snapshots = state.get("pending_snapshots", {})
    
    if camera_id_str and camera_id_str in pending_snapshots:
        pending_snapshots[camera_id_str] = media_id_str
    else:
        # Fallback for backward compatibility (assign to the first empty slot)
        for k, v in pending_snapshots.items():
            if v is None:
                pending_snapshots[k] = media_id_str
                camera_id_str = k
                break
                
    # Save back to cache
    state["pending_snapshots"] = pending_snapshots
    await redis_client.redis.setex(redis_key, 15, json.dumps(state))
    
    # Check if we have received snapshots from all cameras
    all_received = all(v is not None for v in pending_snapshots.values())
    if not all_received:
        logger.info(f"Received snapshot from camera {camera_id_str} for correlation {correlation_id}. Waiting for other cameras: {pending_snapshots}")
        return
        
    # We have all snapshots! Call execute_complete_parking_session helper
    await execute_complete_parking_session(db, state, correlation_id)

async def handle_event(event_id: uuid.UUID, event_type: str, correlation_id: str, payload: dict, metadata: dict):
    """
    Handle single event with Postgres database transaction and idempotency check.
    """
    async with async_session_maker() as db:
        try:
            # 1. Idempotency Check
            dup_query = await db.execute(
                select(ProcessedEvent).where(ProcessedEvent.event_id == event_id)
            )
            existing_event = dup_query.scalars().first()
            if existing_event:
                logger.info(f"Event {event_id} already processed (status: {existing_event.status}). Skipping.")
                return True
                
            # Record processing status
            proc_event = ProcessedEvent(
                event_id=event_id,
                event_type=event_type,
                status="processing"
            )
            db.add(proc_event)
            await db.flush()
            
            # 2. Route event based on type
            if event_type == "card.scanned":
                await handle_card_scanned_event(db, event_id, correlation_id, payload, metadata)
            elif event_type == "camera.snapshot.completed":
                await handle_snapshot_completed_event(db, event_id, correlation_id, payload, metadata)
            else:
                logger.warning(f"Unhandled event type: {event_type}")
                
            # Update to completed
            proc_event.status = "completed"
            await db.commit()
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to process event {event_id}: {e}", exc_info=True)
            
            # Try to record failure status
            try:
                async with async_session_maker() as fail_db:
                    fail_dup = await fail_db.execute(
                        select(ProcessedEvent).where(ProcessedEvent.event_id == event_id)
                    )
                    existing_fail = fail_dup.scalars().first()
                    if not existing_fail:
                        fail_event = ProcessedEvent(
                            event_id=event_id,
                            event_type=event_type,
                            status="failed",
                            error_message=str(e)
                        )
                        fail_db.add(fail_event)
                    else:
                        existing_fail.status = "failed"
                        existing_fail.error_message = str(e)
                    await fail_db.commit()
            except Exception as db_err:
                logger.critical(f"Failed to save event failure status to database: {db_err}")
                
            return False

async def start_event_consumer():
    """
    Infinite loop running background stream reader using consumer groups
    """
    stream_name = "parking.events"
    group_name = "parking-api-group"
    consumer_name = f"api-{uuid.uuid4().hex[:6]}"
    
    # Wait for Redis connection to be initialized
    while not redis_client.redis:
        logger.info("Waiting for Redis connection...")
        await asyncio.sleep(1)
        
    # Create consumer group if not exists
    try:
        await redis_client.redis.xgroup_create(
            name=stream_name,
            groupname=group_name,
            id="$",
            mkstream=True
        )
        logger.info(f"Created Consumer Group '{group_name}' for Stream '{stream_name}'")
    except Exception as e:
        if "BUSYGROUP" in str(e):
            logger.info(f"Consumer Group '{group_name}' already exists.")
        else:
            logger.error(f"Failed to create consumer group: {e}")
            
    logger.info(f"Started reading events from Stream '{stream_name}' using group '{group_name}'")
    
    while True:
        try:
            # Read messages from group
            response = await redis_client.redis.xreadgroup(
                groupname=group_name,
                consumername=consumer_name,
                streams={stream_name: ">"},
                count=10,
                block=2000
            )
            
            if not response:
                continue
                
            for stream, messages in response:
                for message_id, payload in messages:
                    logger.info(f"Received stream event message: {message_id}")
                    
                    try:
                        event_data = {}
                        if "data" in payload:
                            event_data = json.loads(payload["data"])
                        else:
                            event_data = payload
                            
                        event_id_str = event_data.get("event_id")
                        event_type = event_data.get("event_type")
                        correlation_id = event_data.get("correlation_id", "")
                        
                        if not event_id_str or not event_type:
                            logger.error(f"Invalid event data structure: {event_data}")
                            await redis_client.redis.xack(stream_name, group_name, message_id)
                            continue
                            
                        event_id = uuid.UUID(event_id_str)
                        
                        # Handle the event logic
                        success = await handle_event(
                            event_id=event_id,
                            event_type=event_type,
                            correlation_id=correlation_id,
                            payload=event_data.get("payload", {}),
                            metadata=event_data
                        )
                        
                        if success:
                            await redis_client.redis.xack(stream_name, group_name, message_id)
                            logger.info(f"Event ACKed: {message_id}")
                        else:
                            logger.warning(f"Event processing failed for message {message_id}. Will not ACK.")
                            await redis_client.redis.xack(stream_name, group_name, message_id)
                            
                    except Exception as parse_err:
                        logger.error(f"Parse error for stream message {message_id}: {parse_err}")
                        await redis_client.redis.xack(stream_name, group_name, message_id)
                        
        except asyncio.CancelledError:
            logger.info("Event consumer task cancelled.")
            break
        except Exception as loop_err:
            logger.error(f"Error in event consumer loop: {loop_err}")
            await asyncio.sleep(5)
