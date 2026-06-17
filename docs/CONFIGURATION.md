# docs/CONFIGURATION.md

# Cấu hình hệ thống Parking System

## 1. Mục tiêu

Tài liệu này mô tả toàn bộ cấu hình cần thiết để chạy hệ thống Parking System.

Hệ thống gồm các service chính:

```text
parking-web
parking-api
parking-gateway
parking-device-agent
parking-camera-agent
parking-worker
postgres
redis
minio
nginx
```

---

# 2. Nguyên tắc cấu hình

## 2.1. Cấu hình chung dùng `.env`

Các cấu hình chung như database, Redis, MinIO, JWT nên đặt trong:

```text
.env
```

## 2.2. Cấu hình thiết bị dùng YAML

Các cấu hình thiết bị như RFID, camera, barrier nên đặt trong:

```text
config/device-agent.yaml
config/camera-agent.yaml
```

Lý do:

* Dễ đọc
* Dễ sửa
* Dễ version control
* Phù hợp nhiều thiết bị

---

# 3. Redis: Streams và Pub/Sub

Hệ thống dùng cả Redis Streams và Redis Pub/Sub.

## 3.1. Redis Streams

Dùng cho event quan trọng, không được mất dữ liệu.

```text
parking.events
parking.commands
parking.tasks
parking.dead_letters
```

Dùng cho:

```text
card.scanned
camera.snapshot.completed
ocr.detect_plate.completed
barrier.opened
barrier.closed
```

## 3.2. Redis Pub/Sub

Dùng cho realtime event nhẹ, có thể bỏ qua nếu client mất kết nối.

```text
parking.realtime
parking.notifications
```

Dùng cho:

```text
parking.checkin.created
parking.checkout.completed
device.online
device.offline
camera.online
camera.offline
```

---

# 4. File .env.example

```env
# App
APP_ENV=development
APP_DEBUG=true
TZ=Asia/Ho_Chi_Minh

# Public URLs
WEB_PUBLIC_URL=http://localhost:3000
API_PUBLIC_URL=http://localhost:8000
GATEWAY_PUBLIC_URL=ws://localhost:8300

# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=parking
POSTGRES_USER=parking
POSTGRES_PASSWORD=parking

DATABASE_URL=postgresql+psycopg://parking:parking@postgres:5432/parking

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

REDIS_URL=redis://redis:6379/0

# Redis Streams
REDIS_STREAM_EVENTS=parking.events
REDIS_STREAM_COMMANDS=parking.commands
REDIS_STREAM_TASKS=parking.tasks
REDIS_STREAM_DEAD_LETTERS=parking.dead_letters

# Redis Pub/Sub
REDIS_CHANNEL_REALTIME=parking.realtime
REDIS_CHANNEL_NOTIFICATIONS=parking.notifications

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_PUBLIC_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=parking-media
MINIO_SECURE=false

# Auth
JWT_SECRET=CHANGE_ME
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_SECONDS=3600
JWT_REFRESH_TOKEN_EXPIRE_SECONDS=604800

# Agent Auth
AGENT_TOKEN_SECRET=CHANGE_ME
AGENT_TOKEN_EXPIRE_DAYS=365

# Gateway
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8300
GATEWAY_HEARTBEAT_INTERVAL=30
GATEWAY_HEARTBEAT_TIMEOUT=90

# API
API_HOST=0.0.0.0
API_PORT=8000

# Web
VITE_API_URL=http://localhost:8000
VITE_GATEWAY_WS_URL=ws://localhost:8300/ws/web

# Worker
WORKER_CONCURRENCY=2
MOCK_OCR=true
MOCK_ALPR=true
MOCK_FACE=true

# Camera
CAMERA_SNAPSHOT_QUALITY=90
CAMERA_RECONNECT_INTERVAL=5
CAMERA_DEFAULT_FPS=10

# Media retention
IMAGE_RETENTION_DAYS=180
VIDEO_RETENTION_DAYS=30
AUDIT_LOG_RETENTION_DAYS=365
DEVICE_EVENT_RETENTION_DAYS=90

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

# 5. parking-api cấu hình

## 5.1. Biến môi trường

`parking-api` dùng:

```text
DATABASE_URL
REDIS_URL
MINIO_ENDPOINT
MINIO_ACCESS_KEY
MINIO_SECRET_KEY
JWT_SECRET
```

## 5.2. Nhiệm vụ với Redis

API consume:

```text
parking.events
```

API publish:

```text
parking.commands
parking.tasks
parking.realtime
```

## 5.3. Ví dụ config

```env
APP_NAME=parking-api
APP_PORT=8000

DATABASE_URL=postgresql+psycopg://parking:parking@postgres:5432/parking
REDIS_URL=redis://redis:6379/0

MINIO_ENDPOINT=minio:9000
MINIO_BUCKET=parking-media

JWT_SECRET=CHANGE_ME
```

---

# 6. parking-gateway cấu hình

## 6.1. Biến môi trường

```env
APP_NAME=parking-gateway
APP_PORT=8300

REDIS_URL=redis://redis:6379/0

AGENT_TOKEN_SECRET=CHANGE_ME
JWT_SECRET=CHANGE_ME

HEARTBEAT_INTERVAL=30
HEARTBEAT_TIMEOUT=90
```

## 6.2. WebSocket endpoints

```text
/ws/web
/ws/device-agent
/ws/camera-agent
```

## 6.3. Nhiệm vụ với Redis

Gateway ghi vào Streams:

```text
parking.events
```

Gateway đọc từ Streams:

```text
parking.commands
```

Gateway subscribe Pub/Sub:

```text
parking.realtime
parking.notifications
```

---

# 7. parking-device-agent cấu hình

File:

```text
config/device-agent.yaml
```

Ví dụ:

```yaml
agent:
  id: device-agent-gate-01
  name: Device Agent Cổng 01
  type: device

server:
  gateway_url: ws://parking-gateway:8300/ws/device-agent
  agent_token: CHANGE_ME

queue:
  enabled: true
  type: sqlite
  path: /app/data/device-agent-queue.db

heartbeat:
  interval: 30

devices:
  - id: rfid-entry-01
    name: RFID Cổng Vào
    type: rfid_reader
    plugin: serial
    enabled: true
    config:
      port: /dev/ttyUSB0
      baudrate: 9600
      timeout: 1

  - id: barrier-entry-01
    name: Barrier Cổng Vào
    type: barrier
    plugin: tcp
    enabled: true
    config:
      host: 192.168.10.50
      port: 6000
      open_command: "OPEN"
      close_command: "CLOSE"
```

---

# 8. parking-camera-agent cấu hình

File:

```text
config/camera-agent.yaml
```

Ví dụ:

```yaml
agent:
  id: camera-agent-gate-01
  name: Camera Agent Cổng 01
  type: camera

server:
  gateway_url: ws://parking-gateway:8300/ws/camera-agent
  agent_token: CHANGE_ME

minio:
  endpoint: minio:9000
  access_key: minioadmin
  secret_key: minioadmin
  bucket: parking-media
  secure: false

heartbeat:
  interval: 30

cameras:
  - id: cam-entry-overview
    name: Camera Toàn Cảnh Cổng Vào
    type: rtsp
    role: entry_overview
    enabled: true
    config:
      url: rtsp://admin:password@192.168.10.101:554/Streaming/Channels/101
      reconnect_interval: 5
      fps: 10
      width: 1920
      height: 1080

  - id: cam-entry-plate
    name: Camera Biển Số Cổng Vào
    type: rtsp
    role: entry_plate
    enabled: true
    config:
      url: rtsp://admin:password@192.168.10.102:554/Streaming/Channels/101
      reconnect_interval: 5
      fps: 10
      width: 1920
      height: 1080
```

---

# 9. parking-worker cấu hình

## 9.1. Worker OCR

```env
WORKER_NAME=worker-ocr
WORKER_QUEUE=ocr
REDIS_URL=redis://redis:6379/0
MINIO_ENDPOINT=minio:9000
MOCK_OCR=true
```

## 9.2. Worker ALPR

```env
WORKER_NAME=worker-alpr
WORKER_QUEUE=alpr
REDIS_URL=redis://redis:6379/0
MINIO_ENDPOINT=minio:9000
MOCK_ALPR=true
ALPR_DEVICE=cpu
```

Nếu dùng GPU:

```env
ALPR_DEVICE=cuda
CUDA_VISIBLE_DEVICES=0
```

---

# 10. parking-web cấu hình

File:

```text
apps/parking-web/.env
```

```env
VITE_APP_NAME=Parking System
VITE_API_URL=http://localhost:8000
VITE_GATEWAY_WS_URL=ws://localhost:8300/ws/web
```

Production:

```env
VITE_API_URL=https://parking.example.com/api
VITE_GATEWAY_WS_URL=wss://parking.example.com/ws/web
```

---

# 11. Nginx cấu hình

```nginx
server {
    listen 80;
    server_name parking.example.com;

    location / {
        proxy_pass http://parking-web:3000;
    }

    location /api/ {
        proxy_pass http://parking-api:8000/;
    }

    location /ws/ {
        proxy_pass http://parking-gateway:8300/ws/;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /minio/ {
        proxy_pass http://minio:9000/;
    }
}
```

---

# 12. Mock mode

Dùng khi phát triển chưa có thiết bị thật.

```env
MOCK_RFID=true
MOCK_CAMERA=true
MOCK_OCR=true
MOCK_ALPR=true
MOCK_BARRIER=true
```

Mock mode có thể tự sinh:

```text
UID thẻ
Ảnh xe vào
Ảnh xe ra
Biển số
Sự kiện camera
Sự kiện barrier
```

---

# 13. Logging

Khuyến nghị dùng JSON log.

```env
LOG_LEVEL=INFO
LOG_FORMAT=json
```

Ví dụ:

```json
{
  "timestamp": "2026-06-17T09:30:00+07:00",
  "service": "parking-api",
  "level": "INFO",
  "message": "parking.checkin.created",
  "correlation_id": "uuid",
  "session_id": "uuid"
}
```

---

# 14. Cấu hình production cần đổi

Không dùng giá trị mặc định:

```text
POSTGRES_PASSWORD=parking
MINIO_ROOT_PASSWORD=minioadmin
JWT_SECRET=CHANGE_ME
AGENT_TOKEN_SECRET=CHANGE_ME
```

Cần đổi thành secret mạnh.

Ví dụ tạo secret:

```bash
openssl rand -hex 32
```

---

# 15. Tổng kết

Cấu hình hệ thống chia thành 3 nhóm:

```text
.env
```

Dùng cho cấu hình chung.

```text
config/device-agent.yaml
config/camera-agent.yaml
```

Dùng cho thiết bị vật lý.

```text
apps/parking-web/.env
```

Dùng cho frontend build-time config.

Redis được chia rõ:

```text
Redis Streams:
- parking.events
- parking.commands
- parking.tasks
- parking.dead_letters

Redis Pub/Sub:
- parking.realtime
- parking.notifications
```

Thiết kế này giúp hệ thống vừa an toàn dữ liệu nghiệp vụ, vừa nhẹ cho realtime UI.
