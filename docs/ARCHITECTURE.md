# docs/ARCHITECTURE.md

# System Architecture

Parking System is designed using Microservices Architecture.

Each service has a single responsibility and can be deployed independently.

---

## Services

### parking-web

Responsibilities:

* User Interface
* Dashboard
* Check-in screen
* Check-out screen
* Camera preview
* Device monitoring

Technology:

* Vue3
* Vite
* Pinia
* TailwindCSS

---

### parking-api

Responsibilities:

* Business logic
* Authentication
* Vehicle management
* Card management
* Check-in
* Check-out
* Fee calculation

Technology:

* FastAPI
* SQLAlchemy
* Alembic

---

### parking-gateway

Responsibilities:

* Quản lý kết nối WebSocket từ Client và Agents
* Định tuyến event từ thiết bị vào Redis Streams
* Broadcast realtime event từ Redis Streams về Web
* Quản lý trạng thái online/offline của agent (Heartbeat)

Technology:

* Python
* FastAPI (WebSocket)
* Redis Streams
* Pydantic

---

### parking-device-agent

Responsibilities:

* RFID Reader
* Barcode Reader
* Barrier Control
* Serial Device
* TCP Device

Runs on:

* Windows
* Linux

Communication:

* REST API
* WebSocket
* MQTT

---

### parking-camera-agent

Responsibilities:

* RTSP Stream
* USB Camera
* Snapshot
* Video Recording
* Camera Health Check

Libraries:

* OpenCV
* FFmpeg

---

### parking-worker

Responsibilities:

* OCR
* ALPR
* Image Processing
* AI Tasks

Libraries:

* PaddleOCR
* OpenALPR
* YOLO
* Celery

---

## Communication

```text
Web / Device Agent / Camera Agent
        ↓
Parking Gateway
        ↓
Redis Streams
        ↓
Parking API / Workers
```

---

## Storage

### PostgreSQL

Store:

* Vehicles
* Cards
* Users
* Checkin records
* Checkout records
* Logs

### MinIO

Store:

* Vehicle images
* Entry images
* Exit images
* Camera snapshots
* Videos

### Redis

Store:

* Queue
* Realtime events
* Session cache

---

## Deployment

Recommended:

```text
1 Server

Docker Compose

parking-web

parking-gateway

parking-api

postgres

redis

minio

worker
```

Remote:

```text
Guard PC

device-agent

camera-agent
```

Communication:

```text
WebSocket (đi qua parking-gateway)

REST API (đến parking-api)

MQTT
```
