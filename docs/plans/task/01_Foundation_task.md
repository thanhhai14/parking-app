# Task list for Phase 1: Foundation

## 1. Infrastructure Setup
- [x] Create project structure
- [x] Configure `.env.example` and `.env`
- [x] Configure `docker-compose.yml` for database (Postgres), cache/message broker (Redis), and object storage (MinIO)
- [x] Create quick startup script or Makefile

## 2. Initialize `parking-api` service
- [x] Create `apps/parking-api/requirements.txt`
- [x] Create `apps/parking-api/Dockerfile`
- [x] Setup `apps/parking-api/core/config.py` (Pydantic settings)
- [x] Setup `apps/parking-api/core/database.py` (SQLAlchemy async engine & session)
- [x] Setup `apps/parking-api/core/logger.py` (JSON logging)
- [x] Setup `apps/parking-api/main.py` (FastAPI app, health endpoint, CORS, exception handlers)

## 3. Database Migration & Models Setup
- [x] Setup `apps/parking-api/models/user.py` (SQLAlchemy models for `users` and `roles`)
- [x] Initialize Alembic in `apps/parking-api/`
- [x] Configure `alembic.ini` and `alembic/env.py` to support Asyncpg and load models
- [x] Generate initial migration script (`001_create_user_table.py`)
- [x] Apply migration to PostgreSQL database

## 4. Auth & Security Implementation
- [x] Setup `apps/parking-api/core/security.py` (Password hashing via passlib/bcrypt, JWT generation via pyjwt)
- [x] Setup `apps/parking-api/api/deps.py` (DB Session dependency, `get_current_user` JWT dependency)
- [x] Setup `apps/parking-api/api/v1/auth.py` (Login API endpoint `/api/v1/auth/login` returning access token)
- [x] Integrate Auth router to `apps/parking-api/main.py`

## 5. Verification & Testing
- [x] Build and start `postgres`, `redis`, `minio` containers
- [x] Run alembic migrations against Postgres container
- [x] Start FastAPI server locally or inside docker
- [x] Verify `/health` and `/docs` endpoints
- [x] Test `/api/v1/auth/login` endpoint
