# docs/services/camera-agent.md

# Parking Camera Agent

## 1. Giới thiệu

`parking-camera-agent` là service chịu trách nhiệm quản lý camera và xử lý luồng hình ảnh.

Service này hoạt động độc lập với:

* parking-api
* parking-web
* parking-worker

Nó có thể chạy:

* Trên máy chủ trung tâm
* Trên máy bảo vệ
* Trên Mini PC
* Trên Jetson Nano
* Trên Raspberry Pi

---

# 2. Nhiệm vụ

Camera Agent chịu trách nhiệm:

### Quản lý camera

* RTSP Camera
* ONVIF Camera
* USB Webcam
* HTTP Snapshot Camera

---

### Xử lý hình ảnh

* Snapshot
* Crop ảnh
* Resize
* Rotate
* Encode JPEG
* Watermark

---

### Stream

* Live Stream
* MJPEG
* WebRTC
* HLS

---

### Ghi hình

* Record video
* Record theo sự kiện
* Record liên tục

---

### AI

* Motion Detection
* OCR biển số
* Face Detection
* Vehicle Detection

---

# 3. Công nghệ

| Thành phần | Công nghệ  |
| ---------- | ---------- |
| Language   | Python     |
| Async      | asyncio    |
| Video      | OpenCV     |
| Stream     | FFmpeg     |
| ONVIF      | onvif-zeep |
| AI         | OpenCV DNN |
| Upload     | MinIO      |
| API        | FastAPI    |
| Realtime   | WebSocket  |

---

# 4. Kiến trúc

```mermaid
graph TD

A[Camera Manager]

--> B[RTSP Plugin]

--> C[USB Plugin]

--> D[ONVIF Plugin]

--> E[HTTP Snapshot Plugin]

B --> F[Frame Buffer]

C --> F

D --> F

E --> F

F --> G[Snapshot Service]

F --> H[Record Service]

F --> I[AI Pipeline]

F --> J[Stream Service]

G --> K[MinIO]

H --> K

I --> L[Parking Worker]

J --> M[Parking Web]

N[Parking API]

--> G

N --> H

N --> J
```

---

# 5. Cấu trúc thư mục

```text
parking-camera-agent/

├── app/

│

├── main.py

│

├── config/

│ └── settings.py

│

├── core/

│ ├── camera_manager.py

│ ├── stream_manager.py

│ ├── frame_buffer.py

│ └── event_bus.py

│

├── api/

│ ├── health.py

│ ├── snapshot.py

│ ├── stream.py

│ └── cameras.py

│

├── websocket/

│ └── client.py

│

├── services/

│ ├── snapshot_service.py

│ ├── record_service.py

│ ├── upload_service.py

│ └── ai_service.py

│

├── plugins/

│

│ ├── rtsp/

│

│ ├── usb/

│

│ ├── onvif/

│

│ ├── snapshot/

│

│ └── mock/

│

├── cache/

├── data/

├── tests/

│

├── Dockerfile

└── requirements.txt
```

---

# 6. Camera Plugin

Tất cả camera đều implement interface chung.

```python
class CameraPlugin:

    async def connect():

        pass

    async def disconnect():

        pass

    async def get_frame():

        pass

    async def snapshot():

        pass

    async def health():

        pass
```

---

# 7. RTSP Camera Plugin

Hỗ trợ:

```text
Hikvision

Dahua

KBVision

Uniview

Ezviz

TP-Link VIGI

Generic RTSP
```

---

Ví dụ URL:

```text
rtsp://admin:123456@192.168.1.100:554/Streaming/Channels/101
```

---

Config:

```yaml
id: cam-entry-01

plugin: rtsp

url: rtsp://admin:123456@192.168.1.100:554/Streaming/Channels/101

reconnect_interval: 5

fps: 10

resolution:

  width: 1920

  height: 1080
```

---

# 8. USB Camera Plugin

Ví dụ:

```text
/dev/video0

/dev/video1
```

Config:

```yaml
id: webcam-entry

plugin: usb

device: /dev/video0

width: 1280

height: 720

fps: 30
```

---

# 9. ONVIF Plugin

Tự động:

* Tìm camera
* Lấy RTSP URL
* Snapshot URL
* PTZ

---

Config:

```yaml
host: 192.168.1.100

username: admin

password: 123456
```

---

# 10. Frame Buffer

Mỗi camera có bộ nhớ đệm.

Ví dụ:

```text
Camera

↓

Frame Buffer

↓

100 frame gần nhất

↓

Snapshot

Record

AI
```

---

Mục đích:

* Snapshot không phải chờ camera
* AI đọc frame nhanh
* Record không giật

---

## Buffer

```yaml
buffer:

  max_frames: 100

  fps: 10
```

---

# 11. Snapshot Service

API:

```http
POST /snapshot
```

Request:

```json
{
  "camera_id":"cam-01"
}
```

---

Response:

```json
{
  "media_id":"xxx",

  "bucket":"parking-media",

  "object_key":"..."
}
```

---

Luồng:

```mermaid
sequenceDiagram

participant API

participant Camera

participant Buffer

participant MinIO

API->>Camera: Snapshot

Camera->>Buffer: Get latest frame

Buffer->>Camera: Frame

Camera->>MinIO: Upload image

MinIO->>API: media_id
```

---

# 12. Record Service

Có 3 chế độ.

---

## Record liên tục

```text
24/7
```

---

## Record theo lịch

Ví dụ:

```text
06:00 → 18:00
```

---

## Record theo sự kiện

Ví dụ:

```text
RFID quẹt

↓

Record 5 giây trước

+

10 giây sau
```

---

Sơ đồ:

```mermaid
graph TD

RFID Event

↓

Frame Buffer

↓

Extract Video Clip

↓

FFmpeg

↓

MinIO
```

---

# 13. Stream Service

Hỗ trợ:

```text
MJPEG

HLS

WebRTC
```

---

## MJPEG

```text
http://camera-agent:8200/stream/mjpeg/cam-01
```

---

## HLS

```text
http://camera-agent:8200/stream/hls/cam-01/index.m3u8
```

---

## WebRTC

Dùng cho:

* Độ trễ thấp
* Xem realtime

---

# 14. Đồng bộ với Parking Session

Luồng:

```mermaid
sequenceDiagram

participant Reader

participant API

participant Camera

participant MinIO

participant DB

Reader->>API: Quẹt thẻ

API->>Camera: Snapshot

Camera->>MinIO: Upload

Camera->>API: media_id

API->>DB: Update parking_session
```

---

Kết quả:

```text
parking_session

├── entry_overview_image

├── entry_plate_image

├── exit_overview_image

└── exit_plate_image
```

---

# 15. AI Pipeline

Camera Agent không chạy AI nặng.

Nó chỉ:

* Cắt frame
* Resize
* Gửi Worker

---

Luồng:

```mermaid
graph TD

Camera

↓

Frame Buffer

↓

Crop

↓

Resize

↓

Worker OCR

↓

Worker ALPR

↓

Worker Face Detection

↓

Parking API
```

---

# 16. Motion Detection

Dùng OpenCV.

Khi phát hiện:

```text
Motion

↓

Event

↓

Snapshot

↓

Record

↓

Upload
```

---

Event:

```json
{
  "event":"motion.detected",

  "camera_id":"cam-01"
}
```

---

# 17. Watermark

Khi snapshot.

Ví dụ:

```text
2026-06-17 09:30:00

Gate: Cổng số 1

Camera: Entry Camera

Plate: 51A12345
```

---

# 18. Health Check

```http
GET /health
```

---

Response:

```json
{
    "status":"ok"
}
```

---

Chi tiết:

```http
GET /health/full
```

Response:

```json
{
  "status":"ok",

  "cameras":{

      "cam-entry":"online",

      "cam-exit":"online"

  },

  "fps":{

      "cam-entry":10,

      "cam-exit":10

  }
}
```

---

# 19. WebSocket

Agent kết nối:

```text
ws://parking-gateway:8300/ws/camera-agent
```

---

Heartbeat:

```json
{
  "event":"heartbeat",

  "payload":{

      "camera_count":4,

      "cpu":30,

      "memory":42

  }
}
```

---

# 20. File cấu hình

```yaml
agent:

  id: camera-agent-01

server:

  api_url: http://parking-api:8000

  websocket_url: ws://parking-gateway:8300/ws/camera-agent

minio:

  endpoint: minio:9000

  access_key: minioadmin

  secret_key: minioadmin

  bucket: parking-media

storage:

  snapshot_retention_days: 180

  video_retention_days: 30
```

---

# 21. Dockerfile

```dockerfile
FROM python:3.13-slim

RUN apt update && apt install -y \

    ffmpeg \

    libgl1 \

    libglib2.0-0

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD [

"python",

"-m",

"app.main"

]
```

---

# 22. Docker Compose

```yaml
camera-agent:

  build:

    context: ./apps/parking-camera-agent

  restart: unless-stopped

  devices:

    - /dev/video0

  volumes:

    - ./config:/app/config

    - ./cache:/app/cache

    - ./data:/app/data

  environment:

    TZ: Asia/Ho_Chi_Minh
```

---

# 23. Chế độ Mock

Plugin:

```text
mock
```

Tự sinh:

* Frame ngẫu nhiên
* Ảnh biển số mẫu
* RTSP giả lập
* Motion Detection giả lập

---

# 24. Roadmap

## MVP

* RTSP
* USB Camera
* Snapshot
* Record
* Frame Buffer
* Upload MinIO

---

## Version 1

* ONVIF
* HLS
* Motion Detection
* WebRTC

---

## Version 2

* PTZ
* AI Edge
* GPU Decode
* Multi-stream
* Camera Auto Discovery

---

# 25. Tổng kết

`parking-camera-agent` là service chịu trách nhiệm:

* Kết nối camera
* Chụp ảnh
* Ghi hình
* Stream realtime
* Đồng bộ với Parking API
* Chuẩn bị dữ liệu cho AI

Nó được thiết kế như một **Video Gateway**, để sau này có thể mở rộng:

* OCR biển số
* Nhận diện khuôn mặt
* Phân tích hành vi
* AI Edge Computing
* Hệ thống giám sát an ninh
