"""seed_devices_for_testing

Revision ID: eed5ee63ff9c
Revises: 374047e3e6ad
Create Date: 2026-06-18 08:38:53.151535

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


import uuid
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision: str = 'eed5ee63ff9c'
down_revision: Union[str, None] = '374047e3e6ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fixed UUIDs for referential integrity
SITE_ID = 'a832c324-df38-4221-8f55-1f92c1032df3'
ZONE_ID = 'b421a8d9-299f-4310-9b6b-8012b186b51e'
GATE_IN_ID = 'c1b18129-87a3-48ff-98eb-3298a098c11e'
GATE_OUT_ID = 'd908c12e-128a-49bf-811c-291bfae8b11c'
CAMERA_IN_ID = 'e819b18d-f32a-4312-98ab-30129f123de3'
CAMERA_OUT_ID = 'f829c381-12a3-4bcf-a8e1-f921bc19e34c'
BARRIER_IN_ID = 'a1b2c3d4-e5f6-7a8b-9c0d-e1f2a3b4c5d6'
BARRIER_OUT_ID = 'b2c3d4e5-f6a7-8b9c-0d1e-f2a3b4c5d6e7'
CARD_ID = 'cf89b1c9-12a8-48bc-b3a1-098ea1203e4c'

def upgrade() -> None:
    # 1. Seed Site
    op.execute(
        f"INSERT INTO parking_sites (id, code, name, is_active, created_at, updated_at) "
        f"VALUES ('{SITE_ID}', 'SITE-EDGE-01', 'Main Edge Parking Site', true, now(), now()) "
        f"ON CONFLICT (code) DO NOTHING"
    )
    
    # 2. Seed Zone
    op.execute(
        f"INSERT INTO parking_zones (id, site_id, code, name, capacity, current_count, is_active, created_at, updated_at) "
        f"VALUES ('{ZONE_ID}', '{SITE_ID}', 'ZONE-EDGE-01', 'Zone EDGE A', 100, 0, true, now(), now()) "
        f"ON CONFLICT (site_id, code) DO NOTHING"
    )
    
    # 3. Seed Gates
    op.execute(
        f"INSERT INTO parking_gates (id, zone_id, code, name, gate_type, direction, is_active, created_at, updated_at) "
        f"VALUES ('{GATE_IN_ID}', '{ZONE_ID}', 'GATE-IN-EDGE-01', 'Edge Entry Gate', 'entry', 'in', true, now(), now()) "
        f"ON CONFLICT (zone_id, code) DO NOTHING"
    )
    op.execute(
        f"INSERT INTO parking_gates (id, zone_id, code, name, gate_type, direction, is_active, created_at, updated_at) "
        f"VALUES ('{GATE_OUT_ID}', '{ZONE_ID}', 'GATE-OUT-EDGE-01', 'Edge Exit Gate', 'exit', 'out', true, now(), now()) "
        f"ON CONFLICT (zone_id, code) DO NOTHING"
    )
    
    # 4. Seed Cameras
    op.execute(
        f"INSERT INTO cameras (id, gate_id, code, name, camera_type, role, status, agent_id, is_active, created_at, updated_at) "
        f"VALUES ('{CAMERA_IN_ID}', '{GATE_IN_ID}', 'CAM-IN-EDGE-01', 'Entry Camera', 'mock', 'overview', 'offline', 'camera-agent-gate-01', true, now(), now()) "
        f"ON CONFLICT (code) DO NOTHING"
    )
    op.execute(
        f"INSERT INTO cameras (id, gate_id, code, name, camera_type, role, status, agent_id, is_active, created_at, updated_at) "
        f"VALUES ('{CAMERA_OUT_ID}', '{GATE_OUT_ID}', 'CAM-OUT-EDGE-01', 'Exit Camera', 'mock', 'overview', 'offline', 'camera-agent-gate-01', true, now(), now()) "
        f"ON CONFLICT (code) DO NOTHING"
    )
    
    # 5. Seed Barriers (Devices)
    op.execute(
        f"INSERT INTO devices (id, gate_id, code, name, device_type, connection_type, status, agent_id, is_active, created_at, updated_at) "
        f"VALUES ('{BARRIER_IN_ID}', '{GATE_IN_ID}', 'BARRIER-IN-EDGE-01', 'Entry Barrier', 'barrier', 'mock', 'offline', 'device-agent-gate-01', true, now(), now()) "
        f"ON CONFLICT (code) DO NOTHING"
    )
    op.execute(
        f"INSERT INTO devices (id, gate_id, code, name, device_type, connection_type, status, agent_id, is_active, created_at, updated_at) "
        f"VALUES ('{BARRIER_OUT_ID}', '{GATE_OUT_ID}', 'BARRIER-OUT-EDGE-01', 'Exit Barrier', 'barrier', 'mock', 'offline', 'device-agent-gate-01', true, now(), now()) "
        f"ON CONFLICT (code) DO NOTHING"
    )
    
    # 6. Seed active RFID Card for quick manual testing
    op.execute(
        f"INSERT INTO rfid_cards (id, card_uid, card_number, card_type, status, created_at, updated_at) "
        f"VALUES ('{CARD_ID}', '04A12345', '1001', 'rfid', 'active', now(), now()) "
        f"ON CONFLICT (card_uid) DO NOTHING"
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM rfid_cards WHERE id = '{CARD_ID}'")
    op.execute(f"DELETE FROM devices WHERE id IN ('{BARRIER_IN_ID}', '{BARRIER_OUT_ID}')")
    op.execute(f"DELETE FROM cameras WHERE id IN ('{CAMERA_IN_ID}', '{CAMERA_OUT_ID}')")
    op.execute(f"DELETE FROM parking_gates WHERE id IN ('{GATE_IN_ID}', '{GATE_OUT_ID}')")
    op.execute(f"DELETE FROM parking_zones WHERE id = '{ZONE_ID}'")
    op.execute(f"DELETE FROM parking_sites WHERE id = '{SITE_ID}'")
