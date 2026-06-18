import asyncio
import json
import os
import io
import uuid
import pytest
import httpx
import websockets

BASE_URL = "http://localhost:8000"
GATEWAY_WS_URL = "ws://parking-gateway:8300"

def test_edge_agents_full_flow():
    asyncio.run(run_integration_test())

def generate_mock_image(plate_number: str) -> bytes:
    # Use simple dummy bytes instead of drawing with Pillow to avoid dependency errors
    return b"dummy_jpeg_data_representing_vehicle_image_with_plate_" + plate_number.encode()

async def run_integration_test():
    gate_in_code = "GATE-IN-EDGE-01"
    gate_out_code = "GATE-OUT-EDGE-01"
    plate_number = "30-F1 88888"
    
    # 1. Login and create a unique card for this test to avoid collision with background simulators
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
        assert resp.status_code == 200
        user_token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}
        
        # Generate unique card
        card_uid = f"CARD-WS-{uuid_generator()[:8]}"
        resp = await client.post("/api/v1/cards/", headers=headers, json={
            "card_uid": card_uid,
            "card_number": "7777",
            "card_type": "rfid",
            "status": "active"
        })
        assert resp.status_code == 201
            
    device_token = os.environ.get("DEVICE_AGENT_TOKEN", "CHANGE_ME_DEVICE_AGENT_TOKEN")
    camera_token = os.environ.get("CAMERA_AGENT_TOKEN", "CHANGE_ME_CAMERA_AGENT_TOKEN")
    
    web_ws_url = f"{GATEWAY_WS_URL}/ws/web?token={user_token}"
    device_ws_url = f"{GATEWAY_WS_URL}/ws/device-agent?agent_id=device-agent-gate-01&token={device_token}"
    camera_ws_url = f"{GATEWAY_WS_URL}/ws/camera-agent?agent_id=camera-agent-gate-01&token={camera_token}"
    
    # 2. Establish connections for all components
    async with websockets.connect(web_ws_url) as web_ws, \
               websockets.connect(device_ws_url) as device_ws, \
               websockets.connect(camera_ws_url) as camera_ws:
               
        # Confirm agent connections established
        device_conn = json.loads(await device_ws.recv())
        assert device_conn["event_type"] == "connection.established"
        
        camera_conn = json.loads(await camera_ws.recv())
        assert camera_conn["event_type"] == "connection.established"
        
        # ========================================================
        # --- TEST CHECK-IN (Entry Gate) ---
        # ========================================================
        
        # A. Scanner quẹt thẻ gửi card.scanned
        correlation_id_in = uuid_generator()
        scan_event_in = {
            "event_id": uuid_generator(),
            "event_type": "card.scanned",
            "correlation_id": correlation_id_in,
            "payload": {
                "card_uid": card_uid,
                "gate_code": gate_in_code,
                "plate_number": plate_number
            }
        }
        await device_ws.send(json.dumps(scan_event_in))
        
        # B. Camera Agent PHẢI nhận được camera.snapshot.request
        cmd_msg = await asyncio.wait_for(camera_ws.recv(), timeout=5.0)
        camera_cmd = json.loads(cmd_msg)
        assert camera_cmd["command_type"] == "camera.snapshot.request"
        assert camera_cmd["correlation_id"] == correlation_id_in
        
        # C. Camera Agent mock chụp ảnh và upload lên API
        image_bytes = generate_mock_image(plate_number)
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            upload_resp = await client.post(
                "/api/v1/media/upload",
                headers={"Authorization": f"Bearer {user_token}"},
                files={"file": ("snapshot_in.jpg", image_bytes, "image/jpeg")},
                data={"media_type": "snapshot", "source_type": "camera"}
            )
            assert upload_resp.status_code == 201
            media_id = upload_resp.json()["id"]
            
        # D. Camera Agent gửi lại camera.snapshot.completed
        completed_event_in = {
            "event_id": uuid_generator(),
            "event_type": "camera.snapshot.completed",
            "correlation_id": correlation_id_in,
            "site_id": camera_cmd.get("site_id"),
            "gate_id": camera_cmd.get("gate_id"),
            "camera_id": camera_cmd.get("target_camera_id"),
            "payload": {
                "media_id": media_id,
                "plate_number": plate_number
            }
        }
        await camera_ws.send(json.dumps(completed_event_in))
        
        # E. Device Agent PHẢI nhận được barrier.open.request
        device_msg = await asyncio.wait_for(device_ws.recv(), timeout=5.0)
        barrier_cmd = json.loads(device_msg)
        assert barrier_cmd["command_type"] == "barrier.open.request"
        assert barrier_cmd["correlation_id"] == correlation_id_in
        
        # Send barrier confirmation opened back
        opened_event_in = {
            "event_id": uuid_generator(),
            "event_type": "barrier.opened",
            "correlation_id": correlation_id_in,
            "payload": {"status": "open"}
        }
        await device_ws.send(json.dumps(opened_event_in))
        
        # F. Web Dashboard PHẢI nhận được parking.checkin.created
        web_msg = await asyncio.wait_for(web_ws.recv(), timeout=5.0)
        checkin_realtime = json.loads(web_msg)
        assert checkin_realtime["event_type"] == "parking.checkin.created"
        assert checkin_realtime["payload"]["card_uid"] == card_uid
        assert checkin_realtime["payload"]["status"] == "active"
        
        # ========================================================
        # --- TEST CHECK-OUT (Exit Gate) ---
        # ========================================================
        
        # A. Scanner quẹt thẻ lần 2 gửi card.scanned
        correlation_id_out = uuid_generator()
        scan_event_out = {
            "event_id": uuid_generator(),
            "event_type": "card.scanned",
            "correlation_id": correlation_id_out,
            "payload": {
                "card_uid": card_uid,
                "gate_code": gate_out_code,
                "plate_number": plate_number
            }
        }
        await device_ws.send(json.dumps(scan_event_out))
        
        # B. Camera Agent PHẢI nhận được camera.snapshot.request
        cmd_msg = await asyncio.wait_for(camera_ws.recv(), timeout=5.0)
        camera_cmd = json.loads(cmd_msg)
        assert camera_cmd["command_type"] == "camera.snapshot.request"
        assert camera_cmd["correlation_id"] == correlation_id_out
        
        # C. Camera Agent mock chụp và upload
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            upload_resp = await client.post(
                "/api/v1/media/upload",
                headers={"Authorization": f"Bearer {user_token}"},
                files={"file": ("snapshot_out.jpg", image_bytes, "image/jpeg")},
                data={"media_type": "snapshot", "source_type": "camera"}
            )
            assert upload_resp.status_code == 201
            media_id = upload_resp.json()["id"]
            
        # D. Camera Agent gửi camera.snapshot.completed
        completed_event_out = {
            "event_id": uuid_generator(),
            "event_type": "camera.snapshot.completed",
            "correlation_id": correlation_id_out,
            "site_id": camera_cmd.get("site_id"),
            "gate_id": camera_cmd.get("gate_id"),
            "camera_id": camera_cmd.get("target_camera_id"),
            "payload": {
                "media_id": media_id,
                "plate_number": plate_number
            }
        }
        await camera_ws.send(json.dumps(completed_event_out))
        
        # E. Device Agent PHẢI nhận được barrier.open.request
        device_msg = await asyncio.wait_for(device_ws.recv(), timeout=5.0)
        barrier_cmd = json.loads(device_msg)
        assert barrier_cmd["command_type"] == "barrier.open.request"
        assert barrier_cmd["correlation_id"] == correlation_id_out
        
        # F. Web Dashboard PHẢI nhận được parking.checkout.completed
        web_msg = await asyncio.wait_for(web_ws.recv(), timeout=5.0)
        checkout_realtime = json.loads(web_msg)
        assert checkout_realtime["event_type"] == "parking.checkout.completed"
        assert checkout_realtime["payload"]["card_uid"] == card_uid
        assert checkout_realtime["payload"]["status"] == "completed"

def uuid_generator():
    return str(uuid.uuid4())
