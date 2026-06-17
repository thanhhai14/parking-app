import pytest
import httpx
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000"

def test_checkin_checkout_flow():
    with httpx.Client(base_url=BASE_URL) as client:
        # 1. Login
        resp = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # 2. Create site
        site_code = f"SITE-TEST-{datetime.now(timezone.utc).timestamp()}"
        resp = client.post("/api/v1/devices/sites", headers=headers, json={
            "code": site_code,
            "name": "E2E Test Site"
        })
        assert resp.status_code == 201
        site_id = resp.json()["id"]
        
        # 3. Create zone
        zone_code = f"ZONE-TEST-{datetime.now(timezone.utc).timestamp()}"
        resp = client.post("/api/v1/devices/zones", headers=headers, json={
            "site_id": site_id,
            "code": zone_code,
            "name": "E2E Test Zone"
        })
        assert resp.status_code == 201
        zone_id = resp.json()["id"]
        
        # 4. Create entry gate
        gate_in_code = f"GATE-IN-{datetime.now(timezone.utc).timestamp()}"
        resp = client.post("/api/v1/devices/gates", headers=headers, json={
            "zone_id": zone_id,
            "code": gate_in_code,
            "name": "E2E Entry Gate",
            "gate_type": "entry",
            "direction": "in"
        })
        assert resp.status_code == 201
        
        # 5. Create exit gate
        gate_out_code = f"GATE-OUT-{datetime.now(timezone.utc).timestamp()}"
        resp = client.post("/api/v1/devices/gates", headers=headers, json={
            "zone_id": zone_id,
            "code": gate_out_code,
            "name": "E2E Exit Gate",
            "gate_type": "exit",
            "direction": "out"
        })
        assert resp.status_code == 201
        
        # 6. Create card
        card_uid = f"CARD-{datetime.now(timezone.utc).timestamp()}"
        resp = client.post("/api/v1/cards/", headers=headers, json={
            "card_uid": card_uid,
            "card_number": "9999",
            "card_type": "rfid",
            "status": "active"
        })
        assert resp.status_code == 201
        
        # 7. Check-in
        resp = client.post("/api/v1/parking/check-in", json={
            "card_uid": card_uid,
            "plate_number": "29-A1 99999",
            "gate_code": gate_in_code
        })
        assert resp.status_code == 201
        session = resp.json()
        assert session["status"] == "active"
        
        # 8. Check-out
        resp = client.post("/api/v1/parking/check-out", json={
            "card_uid": card_uid,
            "plate_number": "29-A1 99999",
            "gate_code": gate_out_code
        })
        assert resp.status_code == 200
        checkout_session = resp.json()
        assert checkout_session["status"] == "completed"
        assert checkout_session["calculated_fee"] == 0.0
