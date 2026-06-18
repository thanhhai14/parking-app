import asyncio
import json
import os
import uuid
import pytest
import httpx
import websockets

from core.database import async_session_maker
from models.user import User, Role
from core.security import get_password_hash
from models.parking_lot import ParkingGate
from models.device import Camera

BASE_URL = "http://localhost:8000"
GATEWAY_WS_URL = "ws://parking-gateway:8300"
BARRIER_IN_ID = "a1b2c3d4-e5f6-7a8b-9c0d-e1f2a3b4c5d6"

def test_web_frontend_enhancements_integration():
    asyncio.run(run_integration_test())

def uuid_generator():
    return str(uuid.uuid4())

async def seed_guard_user():
    async with async_session_maker() as db:
        from sqlalchemy.future import select
        res = await db.execute(select(User).where(User.username == "guard_test"))
        guard_user = res.scalars().first()
        if not guard_user:
            role_res = await db.execute(select(Role).where(Role.code == "guard"))
            guard_role = role_res.scalars().first()
            assert guard_role is not None
            
            pwd_hash = get_password_hash("guard123")
            new_guard = User(
                username="guard_test",
                password_hash=pwd_hash,
                full_name="Guard Test User",
                role_id=guard_role.id,
                is_active=True
            )
            db.add(new_guard)
            await db.commit()

async def setup_test_cameras():
    from sqlalchemy.future import select
    async with async_session_maker() as db:
        gate_res = await db.execute(select(ParkingGate).where(ParkingGate.code == "GATE-IN-EDGE-01"))
        gate = gate_res.scalars().first()
        assert gate is not None
        
        # Clean up old cameras associated with this gate
        old_cams_res = await db.execute(select(Camera).where(Camera.gate_id == gate.id))
        old_cams = old_cams_res.scalars().all()
        for cam in old_cams:
            await db.delete(cam)
        await db.commit()
        
        # Create 2 new active test cameras
        cam_plate_id = uuid.uuid4()
        cam_overview_id = uuid.uuid4()
        
        cam_plate = Camera(
            id=cam_plate_id,
            gate_id=gate.id,
            code="CAM-TEST-PLATE",
            name="Camera Bien So Test",
            camera_type="ip",
            role="plate",
            agent_id="camera-agent-gate-01",
            status="online",
            is_active=True
        )
        cam_overview = Camera(
            id=cam_overview_id,
            gate_id=gate.id,
            code="CAM-TEST-OVERVIEW",
            name="Camera Toan Canh Test",
            camera_type="ip",
            role="overview",
            agent_id="camera-agent-gate-01",
            status="online",
            is_active=True
        )
        db.add(cam_plate)
        db.add(cam_overview)
        await db.commit()
        return gate.id, cam_plate_id, cam_overview_id

async def run_integration_test():
    gate_in_code = "GATE-IN-EDGE-01"
    plate_number = "30-F1 99999"
    
    # 0. Seed guard user and test cameras
    await seed_guard_user()
    gate_id, cam_plate_id, cam_overview_id = await setup_test_cameras()
    
    # 1. Login via REST API to obtain Web JWT Tokens (Admin & Guard)
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        admin_login_resp = await client.post("/api/v1/auth/login", data={
            "username": "admin",
            "password": "admin123"
        })
        assert admin_login_resp.status_code == 200
        admin_token = admin_login_resp.json()["access_token"]
        admin_headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        
        guard_login_resp = await client.post("/api/v1/auth/login", data={
            "username": "guard_test",
            "password": "guard123"
        })
        assert guard_login_resp.status_code == 200
        guard_token = guard_login_resp.json()["access_token"]
        guard_headers = {
            "Authorization": f"Bearer {guard_token}",
            "Content-Type": "application/json"
        }
        
        # 2. Check administrative protection (RBAC) on backend API
        # Guard should get 403 Forbidden on list cameras
        guard_cams_resp = await client.get("/api/v1/devices/cameras", headers=guard_headers)
        assert guard_cams_resp.status_code == 403
        
        # Admin should get 200 OK on list cameras
        admin_cams_resp = await client.get("/api/v1/devices/cameras", headers=admin_headers)
        assert admin_cams_resp.status_code == 200
        
        # Generate unique card for check-in
        card_uid = f"CARD-WEB-{uuid_generator()[:8]}"
        card_resp = await client.post("/api/v1/cards/", headers=admin_headers, json={
            "card_uid": card_uid,
            "card_number": "8888",
            "card_type": "rfid",
            "status": "active"
        })
        assert card_resp.status_code == 201
        card_id = card_resp.json()["id"]

    # Connect WebSocket clients
    web_ws_url = f"{GATEWAY_WS_URL}/ws/web?token={admin_token}"
    device_token = os.environ.get("DEVICE_AGENT_TOKEN", "CHANGE_ME_DEVICE_AGENT_TOKEN")
    device_ws_url = f"{GATEWAY_WS_URL}/ws/device-agent?agent_id=device-agent-gate-01&token={device_token}"
    camera_token = os.environ.get("CAMERA_AGENT_TOKEN", "CHANGE_ME_CAMERA_AGENT_TOKEN")
    camera_ws_url = f"{GATEWAY_WS_URL}/ws/camera-agent?agent_id=camera-agent-gate-01&token={camera_token}"

    # 3. Connect Web and Agent websockets
    async with websockets.connect(web_ws_url) as web_ws, \
               websockets.connect(device_ws_url) as device_ws, \
               websockets.connect(camera_ws_url) as camera_ws:
               
        # Accept established agent handshake
        dev_conn = json.loads(await device_ws.recv())
        assert dev_conn["event_type"] == "connection.established"
        
        cam_conn = json.loads(await camera_ws.recv())
        assert cam_conn["event_type"] == "connection.established"

        # ========================================================
        # --- TEST REAL-TIME CHECKIN WITH 2 CAMERAS FLOW ---
        # ========================================================
        
        # Simulate Card Scanned from Device Agent
        correlation_id = uuid_generator()
        scan_event = {
            "event_id": uuid_generator(),
            "event_type": "card.scanned",
            "correlation_id": correlation_id,
            "payload": {
                "card_uid": card_uid,
                "gate_code": gate_in_code,
                "plate_number": plate_number
            }
        }
        await device_ws.send(json.dumps(scan_event))
        
        # Camera agent must receive 2 commands (one for each active camera)
        cmds = []
        for _ in range(2):
            cmd_msg = await asyncio.wait_for(camera_ws.recv(), timeout=5.0)
            cmd = json.loads(cmd_msg)
            assert cmd["command_type"] == "camera.snapshot.request"
            assert cmd["correlation_id"] == correlation_id
            cmds.append(cmd)
            
        target_camera_ids = [cmd["target_camera_id"] for cmd in cmds]
        assert str(cam_plate_id) in target_camera_ids
        assert str(cam_overview_id) in target_camera_ids

        # Simulating camera agent uploading snapshots
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            upload_resp1 = await client.post(
                "/api/v1/media/upload",
                headers={"Authorization": f"Bearer {admin_token}"},
                files={"file": ("snapshot_plate.jpg", b"mock_plate_bytes_data", "image/jpeg")},
                data={"media_type": "snapshot", "source_type": "camera"}
            )
            assert upload_resp1.status_code == 201
            media_id1 = upload_resp1.json()["id"]

            upload_resp2 = await client.post(
                "/api/v1/media/upload",
                headers={"Authorization": f"Bearer {admin_token}"},
                files={"file": ("snapshot_overview.jpg", b"mock_overview_bytes_data", "image/jpeg")},
                data={"media_type": "snapshot", "source_type": "camera"}
            )
            assert upload_resp2.status_code == 201
            media_id2 = upload_resp2.json()["id"]

        # Send completed event for the first camera
        cmd_plate = next(c for c in cmds if c["target_camera_id"] == str(cam_plate_id))
        cmd_overview = next(c for c in cmds if c["target_camera_id"] == str(cam_overview_id))

        completed_event_1 = {
            "event_id": uuid_generator(),
            "event_type": "camera.snapshot.completed",
            "correlation_id": correlation_id,
            "site_id": cmd_plate.get("site_id"),
            "gate_id": cmd_plate.get("gate_id"),
            "camera_id": cmd_plate.get("target_camera_id"),
            "payload": {
                "media_id": media_id1,
                "plate_number": plate_number
            }
        }
        await camera_ws.send(json.dumps(completed_event_1))

        # Confirm barrier is NOT opened yet (device_ws receives nothing) and web_ws receives nothing
        try:
            msg = await asyncio.wait_for(device_ws.recv(), timeout=1.5)
            payload = json.loads(msg)
            if payload.get("command_type") == "barrier.open.request":
                pytest.fail("Barrier opened prematurely before all snapshots were completed!")
        except asyncio.TimeoutError:
            pass # Correct behavior

        try:
            msg = await asyncio.wait_for(web_ws.recv(), timeout=1.5)
            payload = json.loads(msg)
            if payload.get("event_type") == "parking.checkin.created":
                pytest.fail("Checkin session created prematurely before all snapshots were completed!")
        except asyncio.TimeoutError:
            pass # Correct behavior

        # Send completed event for the second camera
        completed_event_2 = {
            "event_id": uuid_generator(),
            "event_type": "camera.snapshot.completed",
            "correlation_id": correlation_id,
            "site_id": cmd_overview.get("site_id"),
            "gate_id": cmd_overview.get("gate_id"),
            "camera_id": cmd_overview.get("target_camera_id"),
            "payload": {
                "media_id": media_id2,
                "plate_number": plate_number
            }
        }
        await camera_ws.send(json.dumps(completed_event_2))

        # Confirm Device Agent now receives barrier open request
        dev_msg = await asyncio.wait_for(device_ws.recv(), timeout=5.0)
        barrier_cmd = json.loads(dev_msg)
        assert barrier_cmd["command_type"] == "barrier.open.request"
        assert barrier_cmd["correlation_id"] == correlation_id

        # Confirm Web Dashboard client receives real-time checkin event
        web_msg = await asyncio.wait_for(web_ws.recv(), timeout=5.0)
        checkin_realtime = json.loads(web_msg)
        assert checkin_realtime["event_type"] == "parking.checkin.created"
        assert checkin_realtime["payload"]["card_uid"] == card_uid
        assert checkin_realtime["payload"]["entry_plate_number"] == plate_number
        assert checkin_realtime["payload"]["entry_plate_image_id"] == str(media_id1)
        assert checkin_realtime["payload"]["entry_overview_image_id"] == str(media_id2)

        # ========================================================
        # --- TEST CRUD API UPDATES & DELETES ---
        # ========================================================
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            # 1. Card Update
            put_card_resp = await client.put(f"/api/v1/cards/{card_id}", headers=admin_headers, json={
                "card_uid": card_uid,
                "card_number": "8889",
                "card_type": "rfid",
                "status": "blocked",
                "note": "Blocked test"
            })
            assert put_card_resp.status_code == 200
            assert put_card_resp.json()["status"] == "blocked"
            assert put_card_resp.json()["card_number"] == "8889"

            # Card Delete
            del_card_resp = await client.delete(f"/api/v1/cards/{card_id}", headers=admin_headers)
            assert del_card_resp.status_code == 204

            # 2. Vehicle CRUD
            # Fetch vehicle types
            vtype_resp = await client.get("/api/v1/vehicles/types", headers=admin_headers)
            assert vtype_resp.status_code == 200
            vtype_id = vtype_resp.json()[0]["id"]

            # Create Vehicle
            v_create_resp = await client.post("/api/v1/vehicles/", headers=admin_headers, json={
                "vehicle_type_id": vtype_id,
                "plate_number": "29-A1 99999",
                "brand": "Toyota",
                "model": "Camry",
                "color": "black",
                "description": "Test vehicle"
            })
            assert v_create_resp.status_code == 201
            vehicle_id = v_create_resp.json()["id"]

            # Update Vehicle
            v_update_resp = await client.put(f"/api/v1/vehicles/{vehicle_id}", headers=admin_headers, json={
                "vehicle_type_id": vtype_id,
                "plate_number": "29-A1 88888",
                "brand": "Toyota",
                "model": "Camry",
                "color": "white",
                "description": "Updated test vehicle"
            })
            assert v_update_resp.status_code == 200
            assert v_update_resp.json()["plate_number"] == "29-A1 88888"
            assert v_update_resp.json()["color"] == "white"

            # Delete Vehicle
            v_delete_resp = await client.delete(f"/api/v1/vehicles/{vehicle_id}", headers=admin_headers)
            assert v_delete_resp.status_code == 204

            # 3. Camera CRUD updates & deletes
            # Update Camera
            cam_update_resp = await client.put(f"/api/v1/devices/cameras/{cam_plate_id}", headers=admin_headers, json={
                "gate_id": str(gate_id),
                "code": "CAM-TEST-PLATE-UPDATED",
                "name": "Camera Bien So Test Updated",
                "camera_type": "ip",
                "role": "plate_front",
                "stream_url": "rtsp://test/updated",
                "agent_id": "camera-agent-gate-01"
            })
            assert cam_update_resp.status_code == 200
            assert cam_update_resp.json()["code"] == "CAM-TEST-PLATE-UPDATED"
            assert cam_update_resp.json()["role"] == "plate_front"

            # Delete Cameras
            cam_del_resp1 = await client.delete(f"/api/v1/devices/cameras/{cam_plate_id}", headers=admin_headers)
            assert cam_del_resp1.status_code == 204
            
            cam_del_resp2 = await client.delete(f"/api/v1/devices/cameras/{cam_overview_id}", headers=admin_headers)
            assert cam_del_resp2.status_code == 204

        # Restore original seeded camera for GATE-IN-EDGE-01 for other tests compatibility
        async with async_session_maker() as db:
            original_cam = Camera(
                id=uuid.UUID("e819b18d-f32a-4312-98ab-30129f123de3"),
                gate_id=uuid.UUID("c1b18129-87a3-48ff-98eb-3298a098c11e"),
                code="CAM-IN-EDGE-01",
                name="Entry Camera",
                camera_type="mock",
                role="overview",
                status="offline",
                agent_id="camera-agent-gate-01",
                is_active=True
            )
            db.add(original_cam)
            await db.commit()

        print("Integration integration test for Phase 5.1 passed successfully!")
