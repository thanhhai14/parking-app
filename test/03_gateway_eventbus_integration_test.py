import asyncio
import json
import os
import pytest
import httpx
import websockets
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000"
GATEWAY_WS_URL = "ws://parking-gateway:8300"

def test_gateway_eventbus_flow():
    # Run the async integration test inside a standard sync pytest function
    asyncio.run(run_integration_test())

async def run_integration_test():
    # 1. Setup DB data via API using HTTP Client
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # A. Login as admin
        resp = await client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        user_token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}
        
        # B. Create site
        site_code = f"SITE-WS-{datetime.now(timezone.utc).timestamp()}"
        resp = await client.post("/api/v1/devices/sites", headers=headers, json={
            "code": site_code,
            "name": "WS Test Site"
        })
        assert resp.status_code == 201
        site_id = resp.json()["id"]
        
        # C. Create zone
        zone_code = f"ZONE-WS-{datetime.now(timezone.utc).timestamp()}"
        resp = await client.post("/api/v1/devices/zones", headers=headers, json={
            "site_id": site_id,
            "code": zone_code,
            "name": "WS Test Zone"
        })
        assert resp.status_code == 201
        zone_id = resp.json()["id"]
        
        # D. Create entry gate
        gate_in_code = f"GATE-IN-WS-{datetime.now(timezone.utc).timestamp()}"
        resp = await client.post("/api/v1/devices/gates", headers=headers, json={
            "zone_id": zone_id,
            "code": gate_in_code,
            "name": "WS Entry Gate",
            "gate_type": "entry",
            "direction": "in"
        })
        assert resp.status_code == 201
        
        # E. Create exit gate
        gate_out_code = f"GATE-OUT-WS-{datetime.now(timezone.utc).timestamp()}"
        resp = await client.post("/api/v1/devices/gates", headers=headers, json={
            "zone_id": zone_id,
            "code": gate_out_code,
            "name": "WS Exit Gate",
            "gate_type": "exit",
            "direction": "out"
        })
        assert resp.status_code == 201
        
        # F. Create RFID card
        card_uid = f"CARD-WS-{datetime.now(timezone.utc).timestamp()}"
        resp = await client.post("/api/v1/cards/", headers=headers, json={
            "card_uid": card_uid,
            "card_number": "8888",
            "card_type": "rfid",
            "status": "active"
        })
        assert resp.status_code == 201

    # Get device agent token from env
    device_token = os.environ.get("DEVICE_AGENT_TOKEN", "CHANGE_ME_DEVICE_AGENT_TOKEN")
    
    # 2. Establish WebSocket connection for Web Client (listening to Pub/Sub)
    web_ws_url = f"{GATEWAY_WS_URL}/ws/web?token={user_token}"
    device_ws_url = f"{GATEWAY_WS_URL}/ws/device-agent?agent_id=test-device-agent&token={device_token}"
    
    async with websockets.connect(web_ws_url) as web_ws:
        # 3. Establish WebSocket connection for Device Agent
        async with websockets.connect(device_ws_url) as device_ws:
            # Enforce gate connection established confirmation
            conn_est = await device_ws.recv()
            conn_est_data = json.loads(conn_est)
            assert conn_est_data["event_type"] == "connection.established"
            assert conn_est_data["agent_id"] == "test-device-agent"
            
            # 4. Trigger CHECK-IN (Device Agent sends card.scanned event)
            checkin_event = {
                "event_type": "card.scanned",
                "payload": {
                    "card_uid": card_uid,
                    "gate_code": gate_in_code,
                    "plate_number": "30-F1 88888"
                }
            }
            await device_ws.send(json.dumps(checkin_event))
            
            # Read Check-In realtime event broadcasted to Web Client
            # Add timeout to avoid hanging forever if failing
            web_msg = await asyncio.wait_for(web_ws.recv(), timeout=5.0)
            checkin_realtime = json.loads(web_msg)
            
            assert checkin_realtime["event_type"] == "parking.checkin.created"
            assert checkin_realtime["payload"]["card_uid"] == card_uid
            assert checkin_realtime["payload"]["status"] == "active"
            assert checkin_realtime["payload"]["entry_plate_number"] == "30-F1 88888"
            
            # 5. Trigger CHECK-OUT (Device Agent sends card.scanned event again at exit gate)
            checkout_event = {
                "event_type": "card.scanned",
                "payload": {
                    "card_uid": card_uid,
                    "gate_code": gate_out_code,
                    "plate_number": "30-F1 88888"
                }
            }
            await device_ws.send(json.dumps(checkout_event))
            
            # Read Check-Out realtime event broadcasted to Web Client
            web_msg = await asyncio.wait_for(web_ws.recv(), timeout=5.0)
            checkout_realtime = json.loads(web_msg)
            
            assert checkout_realtime["event_type"] == "parking.checkout.completed"
            assert checkout_realtime["payload"]["card_uid"] == card_uid
            assert checkout_realtime["payload"]["status"] == "completed"
            assert checkout_realtime["payload"]["calculated_fee"] == 0.0
