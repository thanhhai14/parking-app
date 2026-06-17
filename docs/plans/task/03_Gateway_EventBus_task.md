# Task list for Phase 3: Gateway & EventBus

## 1. Docker Compose & Dependency Configuration
- [x] Add `redis>=5.0.0` to `apps/parking-api/requirements.txt`
- [x] Modify `docker-compose.yml` to mount volumes (`./apps/parking-gateway:/app`, `./test:/app/test`) and enable `--reload` command for `parking-gateway`

## 2. Idempotency Model & Migrations (API)
- [x] Create `apps/parking-api/models/processed_event.py` (`ProcessedEvent` model)
- [x] Import `ProcessedEvent` into `apps/parking-api/alembic/env.py`
- [x] Generate Alembic migration script for `processed_events` table
- [x] Apply migration to PostgreSQL database

## 3. Redis Client & Event Consumer (API)
- [x] Create `apps/parking-api/core/redis.py` (Async Redis client setup)
- [x] Create `apps/parking-api/services/event_consumer.py` (Background event consumer task using consumer group)
- [x] Modify `apps/parking-api/main.py` to start event consumer in FastAPI `lifespan` startup

## 4. Initialize Parking Gateway Service
- [x] Create `apps/parking-gateway/requirements.txt`
- [x] Create `apps/parking-gateway/Dockerfile`
- [x] Create `apps/parking-gateway/core/config.py` (Gateway settings & environment variables)
- [x] Create `apps/parking-gateway/core/logger.py` (Gateway logging setup)
- [x] Create `apps/parking-gateway/websocket/connection_manager.py` (WebSocket client registry)
- [x] Create `apps/parking-gateway/redis_gateway/redis_client.py` (Redis Pub/Sub listener & Streams publisher/commands consumer)
- [x] Create `apps/parking-gateway/main.py` (FastAPI app & WebSockets endpoints with Ping/Pong, health checks)

## 5. Verification & Testing
- [x] Create `test/03_gateway_eventbus_integration_test.py`
- [x] Verify test execution inside docker: `docker compose exec -T -e PYTHONPATH=. parking-api pytest test/03_gateway_eventbus_integration_test.py`
- [x] Verify manual check-in/check-out via mock WebSockets event sending and DB state updates
