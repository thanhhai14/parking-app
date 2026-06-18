# Task list for Phase 4: Edge Agents

## 1. Create Agent Configurations & Seed Database
- [x] Create `config/device-agent.yaml`
- [x] Create `config/camera-agent.yaml`
- [x] Write seed migration script to register camera and barrier devices in Postgres DB for gates

## 2. Develop Device Agent (`parking-device-agent`)
- [x] Create `apps/parking-device-agent/requirements.txt`
- [x] Create `apps/parking-device-agent/Dockerfile`
- [x] Create `apps/parking-device-agent/main.py` (WebSocket client, heartbeat sender, command receiver, offline JSON queue)

## 3. Develop Camera Agent (`parking-camera-agent`)
- [x] Create `apps/parking-camera-agent/requirements.txt`
- [x] Create `apps/parking-camera-agent/Dockerfile`
- [x] Create `apps/parking-camera-agent/main.py` (WebSocket client, heartbeat sender, mock image painter, HTTP upload, snapshot event publisher)

## 4. Upgrade API Event Consumer (State Machine & Redis Cache)
- [x] Modify `apps/parking-api/services/event_consumer.py`:
  - Handle `card.scanned` -> store state in Redis -> publish `camera.snapshot.request` command
  - Handle `camera.snapshot.completed` -> load state from Redis -> run checkin/checkout logic -> publish `barrier.open.request` command -> delete state from Redis -> publish `parking.checkin.created`/`checkout.completed` to Pub/Sub

## 5. Verification & Testing
- [x] Create `test/04_edge_agents_integration_test.py`
- [x] Run test suite: `docker compose exec -T -e PYTHONPATH=. parking-api pytest test/04_edge_agents_integration_test.py`
- [x] Rebuild entire docker stack with agents and verify manual execution flow via logs
