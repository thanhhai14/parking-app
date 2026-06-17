# docs/services/api.md

# Parking API Service

## 1. Giới thiệu

`parking-api` là service trung tâm của hệ thống.

Nhiệm vụ:

* Xử lý nghiệp vụ
* Quản lý người dùng
* Quản lý phương tiện
* Quản lý thẻ RFID
* Check-in
* Check-out
* Tính phí
* Quản lý camera
* Quản lý thiết bị
* Cung cấp REST API
* Publish realtime event vào Redis Streams (`parking.realtime`) và consume event từ `parking.events`

---

# 2. Công nghệ

| Thành phần     | Công nghệ    |
| -------------- | ------------ |
| Framework      | FastAPI      |
| ORM            | SQLAlchemy 2 |
| Migration      | Alembic      |
| Validation     | Pydantic     |
| Authentication | JWT          |
| Realtime       | Redis Streams|
| Background Job | Celery       |
| Database       | PostgreSQL   |
| Cache          | Redis        |

---

# 3. Cấu trúc thư mục

```text
parking-api/

├── app/

│   ├── main.py

│   ├── config/

│   │   ├── settings.py

│   │   └── logging.py

│   │

│   ├── api/

│   │   ├── auth.py

│   │   ├── users.py

│   │   ├── vehicles.py

│   │   ├── cards.py

│   │   ├── parking_sessions.py

│   │   ├── devices.py

│   │   ├── cameras.py

│   │   ├── media.py

│   │   ├── payments.py

│   │   └── websocket.py

│   │

│   ├── models/

│   ├── schemas/

│   ├── services/

│   ├── repositories/

│   ├── tasks/

│   ├── websocket/

│   ├── utils/

│   └── dependencies/

│

├── migrations/

├── tests/

├── Dockerfile

├── requirements.txt

└── alembic.ini
```

---

# 4. Kiến trúc nội bộ

```mermaid
graph TD
    A[API Router] --> B[Schema Validation]
    B --> C[Service Layer]
    C --> D[Repository Layer]
    D --> E[(PostgreSQL)]

    C --> F[(Redis)]
    C --> G[MinIO]
    C --> H[Celery]

    RedisStreams[Redis Streams: parking.events] -->|Consume| C
    C -->|Publish| RedisRealtime[Redis Streams: parking.realtime]
```

---

# 5. Nguyên tắc thiết kế

API được chia thành 4 lớp:

## Router

Nhận request.

Ví dụ:

```python
POST /api/v1/vehicles
```

---

## Schema

Validate dữ liệu.

Ví dụ:

```python
VehicleCreate

VehicleUpdate

VehicleResponse
```

---

## Service

Xử lý nghiệp vụ.

Ví dụ:

```python
VehicleService

ParkingSessionService

FeeService

PaymentService
```

---

## Repository

Tương tác database.

Ví dụ:

```python
VehicleRepository

UserRepository

CardRepository
```

---

# 6. Authentication

Sử dụng:

```text
JWT Access Token
+
Refresh Token
```

---

## Đăng nhập

```http
POST /api/v1/auth/login
```

Request:

```json
{
    "username":"admin",
    "password":"123456"
}
```

Response:

```json
{
    "access_token":"xxxxx",

    "refresh_token":"yyyy",

    "expires_in":3600
}
```

---

## Refresh token

```http
POST /api/v1/auth/refresh
```

---

## Logout

```http
POST /api/v1/auth/logout
```

---

# 7. API Người dùng

## Danh sách

```http
GET /api/v1/users
```

---

## Chi tiết

```http
GET /api/v1/users/{id}
```

---

## Tạo

```http
POST /api/v1/users
```

---

## Cập nhật

```http
PUT /api/v1/users/{id}
```

---

## Xóa

```http
DELETE /api/v1/users/{id}
```

---

# 8. API Chủ xe

```http
GET    /api/v1/owners

GET    /api/v1/owners/{id}

POST   /api/v1/owners

PUT    /api/v1/owners/{id}

DELETE /api/v1/owners/{id}
```

---

# 9. API Phương tiện

```http
GET    /api/v1/vehicles

GET    /api/v1/vehicles/{id}

POST   /api/v1/vehicles

PUT    /api/v1/vehicles/{id}

DELETE /api/v1/vehicles/{id}
```

---

## Tìm biển số

```http
GET /api/v1/vehicles/search

?plate=51A12345
```

Response:

```json
{
    "id":"xxx",

    "plate_number":"51A-12345",

    "owner":"Nguyễn Văn A"
}
```

---

# 10. API RFID Card

## Danh sách

```http
GET /api/v1/cards
```

---

## Chi tiết

```http
GET /api/v1/cards/{id}
```

---

## Tạo

```http
POST /api/v1/cards
```

---

## Khóa thẻ

```http
POST /api/v1/cards/{id}/block
```

---

## Mở khóa

```http
POST /api/v1/cards/{id}/unblock
```

---

## Tìm theo UID

```http
GET /api/v1/cards/by-uid/{uid}
```

---

# 11. API Parking Session

Đây là API quan trọng nhất.

---

## Check-in

```http
POST /api/v1/parking-sessions/checkin
```

Request:

```json
{
    "card_uid":"04A3B112",

    "gate_id":"xxx",

    "entry_user_id":"xxx"
}
```

---

### Luồng xử lý

```mermaid
sequenceDiagram
    participant Reader as Đầu đọc RFID
    participant Agent as Device Agent
    participant Gateway as Parking Gateway
    participant Redis as Redis Streams
    participant API as Parking API
    participant Camera as Camera Agent
    participant DB as PostgreSQL
    participant Web as Parking Web

    Reader->>Agent: Quẹt thẻ
    Agent->>Gateway: card.scanned (WebSocket)
    Gateway->>Redis: XADD parking.events
    API->>Redis: XREADGROUP
    API->>Redis: XADD parking.commands (snapshot.request)
    Gateway->>Redis: XREADGROUP
    Gateway->>Camera: snapshot.request (WebSocket)
    Camera->>Gateway: snapshot.completed (Upload MinIO)
    Gateway->>Redis: XADD parking.events (camera.snapshot.completed)
    API->>Redis: XREADGROUP
    API->>DB: Lưu session check-in
    API->>Redis: XADD parking.realtime (parking.checkin.created)
    Gateway->>Redis: Subscribe realtime
    Gateway->>Web: parking.checkin.created (WebSocket)
```

---

Response:

```json
{
    "success":true,

    "session_id":"xxx",

    "plate":"51A12345",

    "entry_time":"2026-06-17T08:30:00Z"
}
```

---

# 12. Check-out

```http
POST /api/v1/parking-sessions/checkout
```

Request:

```json
{
    "card_uid":"04A3B112",

    "gate_id":"xxx",

    "exit_user_id":"xxx"
}
```

---

Luồng:

```mermaid
sequenceDiagram
    participant Reader as Đầu đọc RFID
    participant Agent as Device Agent
    participant Gateway as Parking Gateway
    participant Redis as Redis Streams
    participant API as Parking API
    participant Camera as Camera Agent
    participant Worker as OCR Worker
    participant DB as PostgreSQL
    participant Web as Parking Web

    Reader->>Agent: Quẹt thẻ
    Agent->>Gateway: card.scanned (WebSocket)
    Gateway->>Redis: XADD parking.events
    API->>Redis: XREADGROUP
    API->>DB: Tìm session active
    API->>Redis: XADD parking.commands (snapshot.request)
    Gateway->>Redis: XREADGROUP
    Gateway->>Camera: snapshot.request (WebSocket)
    Camera->>Gateway: snapshot.completed (Upload MinIO)
    Gateway->>Redis: XADD parking.events (camera.snapshot.completed)
    API->>Redis: XREADGROUP
    API->>Redis: XADD parking.tasks (OCR)
    Worker->>Redis: Consume task
    Worker->>Worker: Nhận diện biển số (OCR)
    Worker->>Redis: XADD parking.events (ocr.completed)
    API->>Redis: XREADGROUP
    API->>API: Tính phí gửi xe
    API->>DB: Cập nhật checkout session
    API->>Redis: XADD parking.commands (barrier.open.request)
    Gateway->>Redis: XREADGROUP
    Gateway->>Agent: barrier.open (WebSocket)
    API->>Redis: XADD parking.realtime (parking.checkout.completed)
    Gateway->>Redis: Subscribe realtime
    Gateway->>Web: parking.checkout.completed (WebSocket)
```

---

Response:

```json
{
    "success":true,

    "session_id":"xxx",

    "duration_minutes":180,

    "amount":5000,

    "payment_status":"unpaid"
}
```

---

# 13. API Camera

## Danh sách camera

```http
GET /api/v1/cameras
```

---

## Snapshot

```http
POST /api/v1/cameras/{id}/snapshot
```

Response:

```json
{
    "media_id":"xxx",

    "url":"..."
}
```

---

## Test camera

```http
POST /api/v1/cameras/{id}/test
```

---

## Stream URL

```http
GET /api/v1/cameras/{id}/stream
```

---

# 14. API Device

## Danh sách thiết bị

```http
GET /api/v1/devices
```

---

## Trạng thái

```http
GET /api/v1/devices/{id}/status
```

Response:

```json
{
    "status":"online",

    "last_seen":"...",

    "firmware":"1.0.1"
}
```

---

## Mở barrier

```http
POST /api/v1/devices/{id}/open
```

---

## Đóng barrier

```http
POST /api/v1/devices/{id}/close
```

---

## Restart

```http
POST /api/v1/devices/{id}/restart
```

---

# 15. API Media

## Upload

```http
POST /api/v1/media/upload
```

---

## Lấy Signed URL

```http
GET /api/v1/media/{id}/signed-url
```

Response:

```json
{
    "url":"https://minio....",

    "expired_at":"..."
}
```

---

## Xóa media

```http
DELETE /api/v1/media/{id}
```

---

# 16. API Dashboard

## Tổng quan

```http
GET /api/v1/dashboard/overview
```

Response:

```json
{
    "vehicles_inside":102,

    "today_entry":350,

    "today_exit":248,

    "today_revenue":1250000,

    "available_spaces":58
}
```

---

## Theo giờ

```http
GET /api/v1/dashboard/hourly
```

---

## Theo ngày

```http
GET /api/v1/dashboard/daily
```

---

# 17. Realtime Event Stream (Redis Streams)

`parking-api` không trực tiếp duy trì kết nối WebSocket của khách hàng/thiết bị nữa (vai trò này thuộc về `parking-gateway`).

Thay vào đó, nó ghi nhận các sự kiện nghiệp vụ và đẩy vào Redis Stream `parking.realtime`. `parking-gateway` sẽ subscribe stream này và phát lại (broadcast) cho client.

Các event chính đẩy vào `parking.realtime`:

## 17.1. Xe vào (`parking.checkin.created`)

```json
{
  "event_id": "uuid",
  "event_type": "parking.checkin.created",
  "source": "parking-api",
  "payload": {
    "session_id": "xxx",
    "card_uid": "04A3B112",
    "plate": "51A-12345",
    "entry_time": "2026-06-17T08:30:00Z"
  },
  "created_at": "2026-06-17T08:30:00Z"
}
```

---

## 17.2. Xe ra (`parking.checkout.completed`)

```json
{
  "event_id": "uuid",
  "event_type": "parking.checkout.completed",
  "source": "parking-api",
  "payload": {
    "session_id": "xxx",
    "card_uid": "04A3B112",
    "plate": "51A-12345",
    "duration_minutes": 180,
    "amount": 5000,
    "exit_time": "2026-06-17T11:30:00Z"
  },
  "created_at": "2026-06-17T11:30:00Z"
}
```

---

# 18. Health Check

## Kiểm tra service

```http
GET /health
```

Response:

```json
{
    "status":"ok"
}
```

---

## Kiểm tra dependency

```http
GET /health/full
```

Response:

```json
{
    "api":"ok",

    "postgres":"ok",

    "redis":"ok",

    "minio":"ok"
}
```

---

# 19. Dockerfile

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
```

---

# 20. Biến môi trường

```env
APP_NAME=parking-api

APP_ENV=production

APP_DEBUG=false

DATABASE_URL=postgresql+psycopg://user:pass@postgres:5432/parking

REDIS_URL=redis://redis:6379

MINIO_ENDPOINT=minio:9000

MINIO_ACCESS_KEY=minioadmin

MINIO_SECRET_KEY=minioadmin

MINIO_BUCKET=parking-media

JWT_SECRET=CHANGE_ME

JWT_EXPIRE=3600
```

---

# 21. Swagger

FastAPI tự sinh tài liệu:

```text
http://localhost:8000/docs

http://localhost:8000/redoc
```

---

# 22. Mục tiêu

`parking-api` là service trung tâm.

Tất cả service khác:

* parking-web
* parking-device-agent
* parking-camera-agent
* parking-worker

đều tương tác thông qua API hoặc WebSocket.

Điều này giúp:

* Dễ scale
* Dễ test
* Dễ thay đổi UI
* Dễ viết mobile app
* Dễ viết plugin
* Dễ chuyển sang Kubernetes sau này
