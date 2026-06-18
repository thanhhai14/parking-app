import asyncio
import json
import os
import uuid
import pytest
import httpx
import websockets

BASE_URL = "http://localhost:8000"
GATEWAY_WS_URL = "ws://parking-gateway:8300"

# Target Barrier seeded ID from migration script eed5ee63ff9c
BARRIER_IN_ID = "a1b2c3d4-e5f6-7a8b-9c0d-e1f2a3b4c5d6"

def test_web_frontend_integration():
    asyncio.run(run_web_integration_test())

def uuid_generator():
    return str(uuid.uuid4())

async def run_web_integration_test():
    gate_in_code = "GATE-IN-EDGE-01"
    plate_number = "30-F1 99999"
    
    # 1. Login via REST API to obtain Web JWT Token
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        login_resp = await client.post("/api/v1/auth/login", data={
            "username": "admin",
            "password": "admin123"
        })
        assert login_resp.status_code == 200
        web_token = login_resp.json()["access_token"]
        headers = {
            "Authorization": f"Bearer {web_token}",
            "Content-Type": "application/json"
        }
        
        # 2. Check list devices endpoint returns status 200
        devices_resp = await client.get("/api/v1/devices/", headers=headers)
        assert devices_resp.status_code == 200
        devices_list = devices_resp.json()
        assert len(devices_list) > 0
        
        # Check target barrier is present
        barrier_exists = any(d["id"] == BARRIER_IN_ID for d in devices_list)
        assert barrier_exists, f"Seed barrier '{BARRIER_IN_ID}' not found in database."
        
        # Generate unique card for check-in
        card_uid = f"CARD-WEB-{uuid_generator()[:8]}"
        card_resp = await client.post("/api/v1/cards/", headers=headers, json={
            "card_uid": card_uid,
            "card_number": "8888",
            "card_type": "rfid",
            "status": "active"
        })
        assert card_resp.status_code == 201

    # Connect WebSocket clients
    web_ws_url = f"{GATEWAY_WS_URL}/ws/web?token={web_token}"
    device_token = os.environ.get("DEVICE_AGENT_TOKEN", "CHANGE_ME_DEVICE_AGENT_TOKEN")
    device_ws_url = f"{GATEWAY_WS_URL}/ws/device-agent?agent_id=device-agent-gate-01&token={device_token}"
    camera_token = os.environ.get("CAMERA_AGENT_TOKEN", "CHANGE_ME_CAMERA_AGENT_TOKEN")
    camera_ws_url = f"{GATEWAY_WS_URL}/ws/camera-agent?agent_id=camera-agent-gate-01&token={camera_token}"

    # 3. Connect Web and Device agents
    async with websockets.connect(web_ws_url) as web_ws, \
               websockets.connect(device_ws_url) as device_ws, \
               websockets.connect(camera_ws_url) as camera_ws:
               
        # Accept established agent handshake
        dev_conn = json.loads(await device_ws.recv())
        assert dev_conn["event_type"] == "connection.established"
        
        cam_conn = json.loads(await camera_ws.recv())
        assert cam_conn["event_type"] == "connection.established"

        # ========================================================
        # --- TEST REAL-TIME CHECKIN NOTIFICATION ON WEB WS ---
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
        
        # Camera agent receives snapshot request command
        cmd_msg = await asyncio.wait_for(camera_ws.recv(), timeout=5.0)
        camera_cmd = json.loads(cmd_msg)
        assert camera_cmd["command_type"] == "camera.snapshot.request"
        assert camera_cmd["correlation_id"] == correlation_id

        # Simulating camera agent upload snapshot
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            upload_resp = await client.post(
                "/api/v1/media/upload",
                headers={"Authorization": f"Bearer {web_token}"},
                files={"file": ("snapshot_in.jpg", b"mock_plate_bytes_data", "image/jpeg")},
                data={"media_type": "snapshot", "source_type": "camera"}
            )
            assert upload_resp.status_code == 201
            media_id = upload_resp.json()["id"]

        # Camera Agent posts snapshot completed event
        completed_event = {
            "event_id": uuid_generator(),
            "event_type": "camera.snapshot.completed",
            "correlation_id": correlation_id,
            "site_id": camera_cmd.get("site_id"),
            "gate_id": camera_cmd.get("gate_id"),
            "camera_id": camera_cmd.get("target_camera_id"),
            "payload": {
                "media_id": media_id,
                "plate_number": plate_number
            }
        }
        await camera_ws.send(json.dumps(completed_event))

        # Confirm Device Agent receives barrier open request
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

        # ========================================================
        # --- TEST MANUAL BARRIER OPEN FROM WEB CLIENT API ---
        # ========================================================
        
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            # Trigger manual barrier open command via Web API
            control_resp = await client.post(
                f"/api/v1/devices/{BARRIER_IN_ID}/control",
                headers=headers,
                json={"command": "barrier.open"}
            )
            assert control_resp.status_code == 200
            assert control_resp.json()["status"] == "success"
            
        # Device agent should receive a new barrier.open.request command
        dev_msg_manual = await asyncio.wait_for(device_ws.recv(), timeout=5.0)
        barrier_cmd_manual = json.loads(dev_msg_manual)
        assert barrier_cmd_manual["command_type"] == "barrier.open.request"
        assert barrier_cmd_manual["target_device_id"] == BARRIER_IN_ID
        
        print("Integration integration test for Web Frontend passed successfully!")
