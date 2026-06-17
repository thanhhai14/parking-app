# Task list for Phase 2: Core API

## 1. Database Schema & SQLAlchemy Models
- [x] Create `apps/parking-api/models/parking_lot.py` (Site, Zone, Gate models)
- [x] Create `apps/parking-api/models/vehicle.py` (VehicleType, VehicleOwner, Vehicle models)
- [x] Create `apps/parking-api/models/card.py` (RfidCard model)
- [x] Create `apps/parking-api/models/device.py` (Device, Camera models)
- [x] Create `apps/parking-api/models/media.py` (MediaFile model)
- [x] Create `apps/parking-api/models/fee.py` (FeeRule model)
- [x] Create `apps/parking-api/models/session.py` (ParkingSession, Payment models)
- [x] Generate Alembic migration script (`002_core_schema.py`)
- [x] Apply migration to PostgreSQL database

## 2. MinIO Client Integration & Upload API
- [x] Create `apps/parking-api/core/s3.py` (MinIO/S3 connection and upload client)
- [x] Create `apps/parking-api/api/v1/media.py` (`POST /api/v1/media/upload` endpoint)
- [x] Integrate media router into `main.py`

## 3. CRUD REST APIs
- [x] Create `apps/parking-api/api/v1/vehicles.py` (CRUD for vehicles, vehicle types, vehicle owners)
- [x] Create `apps/parking-api/api/v1/cards.py` (CRUD for RFID cards)
- [x] Create `apps/parking-api/api/v1/devices.py` (CRUD for devices, cameras)
- [x] Integrate routers into `main.py`

## 4. Pricing Engine Implementation
- [x] Create `apps/parking-api/services/pricing_service.py` (Extensible pricing strategy engine)
- [x] Create unit tests in `apps/parking-api/tests/test_pricing.py` to verify all pricing scenarios

## 5. Check-in & Check-out REST APIs
- [x] Create `apps/parking-api/api/v1/parking.py` (`/parking/check-in` & `/parking/check-out` endpoints)
- [x] Integrate parking router into `main.py`

## 6. Verification & E2E Testing
- [x] Run Alembic migrations
- [x] Run unit tests for pricing service
- [x] Execute manual E2E check-in/check-out tests via curl and verify database results
