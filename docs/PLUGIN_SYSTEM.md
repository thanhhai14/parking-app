# docs/PLUGIN_SYSTEM.md

# Plugin System

## 1. Giới thiệu

`Plugin System` là cơ chế mở rộng của Parking System.

Mục tiêu là cho phép hệ thống hỗ trợ nhiều loại thiết bị, camera, barrier, OCR, ALPR mà không cần sửa mã nguồn lõi.

Các thành phần nên hỗ trợ plugin:

```text
parking-device-agent
parking-camera-agent
parking-worker
```

---

# 2. Vì sao cần Plugin System?

Trong hệ thống giữ xe thực tế, phần cứng rất đa dạng:

* Đầu đọc RFID USB
* Đầu đọc RFID Serial
* Đầu đọc thẻ TCP/IP
* Barcode scanner
* QR scanner
* Bộ điều khiển Wiegand
* Barrier TCP/IP
* Barrier RS485
* Relay USB
* Camera RTSP
* Camera ONVIF
* Camera HTTP Snapshot
* Webcam USB
* OCR local
* OCR cloud
* ALPR bằng YOLO
* ALPR bằng OpenALPR

Nếu viết cứng vào core, sau này mỗi lần thêm thiết bị mới sẽ phải sửa source chính.

Thiết kế đúng hơn:

```text
Core Service
    ↓
Plugin Interface
    ↓
Plugin cụ thể
```

---

# 3. Kiến trúc tổng quan

```mermaid
graph TD
    Core[Core Service]

    Core --> PluginManager[Plugin Manager]

    PluginManager --> DevicePlugin[Device Plugin]
    PluginManager --> CameraPlugin[Camera Plugin]
    PluginManager --> BarrierPlugin[Barrier Plugin]
    PluginManager --> OCRPlugin[OCR Plugin]
    PluginManager --> ALPRPlugin[ALPR Plugin]

    DevicePlugin --> RFIDSerial[RFID Serial]
    DevicePlugin --> RFIDTCP[RFID TCP]
    DevicePlugin --> RFIDKeyboard[RFID Keyboard]

    CameraPlugin --> RTSP[RTSP Camera]
    CameraPlugin --> ONVIF[ONVIF Camera]
    CameraPlugin --> USB[USB Camera]

    BarrierPlugin --> BarrierTCP[Barrier TCP]
    BarrierPlugin --> RelayUSB[Relay USB]

    OCRPlugin --> PaddleOCR[PaddleOCR]
    ALPRPlugin --> YOLO[YOLO ALPR]
```

---

# 4. Nguyên tắc thiết kế plugin

## 4.1. Core không phụ thuộc vào thiết bị cụ thể

Core chỉ biết interface.

Ví dụ:

```python
await plugin.connect()
await plugin.health()
await plugin.read()
```

Core không cần biết plugin đó đang đọc:

```text
/dev/ttyUSB0
192.168.10.50:6000
USB HID
MQTT topic
```

---

## 4.2. Plugin phải khai báo metadata

Mỗi plugin cần có metadata:

```json
{
  "name": "rfid-serial",
  "version": "1.0.0",
  "type": "device",
  "description": "Đọc RFID qua cổng Serial",
  "author": "Parking System",
  "supported_platforms": ["linux", "windows"],
  "capabilities": ["read_card", "health_check"]
}
```

---

## 4.3. Plugin config bằng YAML

Ví dụ:

```yaml
devices:
  - id: rfid-entry-01
    name: RFID Cổng Vào
    type: rfid_reader
    plugin: rfid_serial
    enabled: true
    config:
      port: /dev/ttyUSB0
      baudrate: 9600
      timeout: 1
```

---

## 4.4. Plugin không được gọi trực tiếp database

Plugin không được kết nối trực tiếp:

```text
PostgreSQL
MinIO
parking-api database
```

Plugin chỉ được:

* Đọc thiết bị
* Gửi event về core
* Nhận command từ core
* Trả kết quả cho core

---

# 5. Phân loại plugin

## 5.1. Device Plugin

Dùng trong:

```text
parking-device-agent
```

Hỗ trợ:

```text
rfid_reader
barcode_reader
qr_reader
barrier
relay
controller
loop_detector
display_board
```

---

## 5.2. Camera Plugin

Dùng trong:

```text
parking-camera-agent
```

Hỗ trợ:

```text
rtsp
onvif
usb
http_snapshot
mock
```

---

## 5.3. Worker Plugin

Dùng trong:

```text
parking-worker
```

Hỗ trợ:

```text
ocr
alpr
face_recognition
vehicle_detection
media_processing
```

---

# 6. Cấu trúc thư mục plugin

Đề xuất:

```text
plugins/

├── device/

│   ├── rfid_serial/

│   ├── rfid_tcp/

│   ├── rfid_keyboard/

│   ├── barcode_keyboard/

│   ├── barrier_tcp/

│   ├── relay_usb/

│   └── mock_device/

│

├── camera/

│   ├── rtsp_camera/

│   ├── onvif_camera/

│   ├── usb_camera/

│   ├── http_snapshot_camera/

│   └── mock_camera/

│

├── worker/

│   ├── paddle_ocr/

│   ├── yolo_alpr/

│   ├── openalpr/

│   ├── insightface/

│   └── mock_ai/

│

└── README.md
```

---

# 7. Plugin metadata

Mỗi plugin nên có file:

```text
plugin.yaml
```

Ví dụ:

```yaml
name: rfid_serial
display_name: RFID Serial Reader
version: 1.0.0
type: device
category: rfid_reader
description: Đọc thẻ RFID qua Serial/COM port
author: Parking System
license: MIT

supported_platforms:
  - linux
  - windows

capabilities:
  - connect
  - disconnect
  - read_card
  - health_check

config_schema:
  port:
    type: string
    required: true
    example: /dev/ttyUSB0

  baudrate:
    type: integer
    required: true
    default: 9600

  timeout:
    type: number
    required: false
    default: 1
```

---

# 8. Device Plugin Interface

## 8.1. Interface chuẩn

```python
from abc import ABC, abstractmethod
from typing import Any, Dict

class DevicePlugin(ABC):
    plugin_name: str
    plugin_type: str

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def health(self) -> Dict[str, Any]:
        pass

    async def read(self) -> Dict[str, Any] | None:
        return None

    async def write(self, command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
```

---

## 8.2. RFID Plugin Interface

RFID plugin cần trả về event dạng:

```json
{
  "event_type": "card.scanned",
  "payload": {
    "card_uid": "04A12345",
    "raw": "04A12345"
  }
}
```

---

## 8.3. Barrier Plugin Interface

Barrier plugin cần hỗ trợ command:

```text
open
close
stop
status
```

Ví dụ response:

```json
{
  "success": true,
  "command": "open",
  "device_id": "barrier-entry-01",
  "payload": {
    "duration_ms": 1500
  }
}
```

---

# 9. Ví dụ RFID Serial Plugin

```python
import serial
from typing import Any, Dict

class RFIDSerialPlugin:
    plugin_name = "rfid_serial"
    plugin_type = "rfid_reader"

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.serial_client = None

    async def connect(self) -> None:
        self.serial_client = serial.Serial(
            port=self.config["port"],
            baudrate=self.config.get("baudrate", 9600),
            timeout=self.config.get("timeout", 1),
        )

    async def disconnect(self) -> None:
        if self.serial_client:
            self.serial_client.close()

    async def health(self) -> Dict[str, Any]:
        return {
            "status": "online" if self.serial_client and self.serial_client.is_open else "offline"
        }

    async def read(self) -> Dict[str, Any] | None:
        if not self.serial_client:
            return None

        raw_data = self.serial_client.readline().decode("utf-8").strip()

        if not raw_data:
            return None

        return {
            "event_type": "card.scanned",
            "payload": {
                "card_uid": raw_data,
                "raw": raw_data
            }
        }
```

---

# 10. Ví dụ RFID TCP Plugin

```python
import asyncio
from typing import Any, Dict

class RFIDTCPPlugin:
    plugin_name = "rfid_tcp"
    plugin_type = "rfid_reader"

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.reader = None
        self.writer = None

    async def connect(self) -> None:
        self.reader, self.writer = await asyncio.open_connection(
            self.config["host"],
            self.config["port"]
        )

    async def disconnect(self) -> None:
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

    async def health(self) -> Dict[str, Any]:
        return {
            "status": "online" if self.writer else "offline"
        }

    async def read(self) -> Dict[str, Any] | None:
        if not self.reader:
            return None

        data = await self.reader.readline()
        card_uid = data.decode("utf-8").strip()

        if not card_uid:
            return None

        return {
            "event_type": "card.scanned",
            "payload": {
                "card_uid": card_uid,
                "raw": card_uid
            }
        }
```

---

# 11. Ví dụ Barrier TCP Plugin

```python
import asyncio
from typing import Any, Dict

class BarrierTCPPlugin:
    plugin_name = "barrier_tcp"
    plugin_type = "barrier"

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.reader = None
        self.writer = None

    async def connect(self) -> None:
        self.reader, self.writer = await asyncio.open_connection(
            self.config["host"],
            self.config["port"]
        )

    async def disconnect(self) -> None:
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

    async def health(self) -> Dict[str, Any]:
        return {
            "status": "online" if self.writer else "offline"
        }

    async def write(self, command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if command == "open":
            raw_command = self.config.get("open_command", "OPEN")
        elif command == "close":
            raw_command = self.config.get("close_command", "CLOSE")
        else:
            raise ValueError(f"Unsupported command: {command}")

        self.writer.write(raw_command.encode("utf-8"))
        await self.writer.drain()

        return {
            "success": true,
            "command": command
        }
```

---

# 12. Camera Plugin Interface

## 12.1. Interface chuẩn

```python
from abc import ABC, abstractmethod
from typing import Any, Dict

class CameraPlugin(ABC):
    plugin_name: str
    plugin_type: str

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def health(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_frame(self) -> Any:
        pass

    @abstractmethod
    async def snapshot(self) -> Dict[str, Any]:
        pass
```

---

# 13. Ví dụ RTSP Camera Plugin

```python
import cv2
from typing import Any, Dict

class RTSPCameraPlugin:
    plugin_name = "rtsp_camera"
    plugin_type = "camera"

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.capture = None

    async def connect(self) -> None:
        self.capture = cv2.VideoCapture(self.config["url"])

    async def disconnect(self) -> None:
        if self.capture:
            self.capture.release()

    async def health(self) -> Dict[str, Any]:
        return {
            "status": "online" if self.capture and self.capture.isOpened() else "offline"
        }

    async def get_frame(self):
        if not self.capture:
            return None

        success, frame = self.capture.read()

        if not success:
            return None

        return frame

    async def snapshot(self) -> Dict[str, Any]:
        frame = await self.get_frame()

        if frame is None:
            return {
                "success": False,
                "error": "NO_FRAME"
            }

        return {
            "success": True,
            "frame": frame
        }
```

---

# 14. Worker Plugin Interface

## 14.1. OCR Plugin

```python
from abc import ABC, abstractmethod
from typing import Any, Dict

class OCRPlugin(ABC):
    plugin_name: str

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def load_model(self) -> None:
        pass

    @abstractmethod
    async def recognize(self, image_path: str) -> Dict[str, Any]:
        pass
```

Response chuẩn:

```json
{
  "success": true,
  "text": "51A12345",
  "confidence": 0.97
}
```

---

## 14.2. ALPR Plugin

```python
from abc import ABC, abstractmethod
from typing import Any, Dict

class ALPRPlugin(ABC):
    plugin_name: str

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def load_model(self) -> None:
        pass

    @abstractmethod
    async def detect_plate(self, image_path: str) -> Dict[str, Any]:
        pass
```

Response chuẩn:

```json
{
  "success": true,
  "plate": "51A12345",
  "confidence": 0.96,
  "bbox": [100, 120, 300, 180]
}
```

---

# 15. Plugin Manager

`Plugin Manager` có nhiệm vụ:

* Load plugin
* Validate config
* Khởi tạo plugin instance
* Theo dõi trạng thái plugin
* Reload plugin khi config thay đổi
* Ghi log lỗi plugin

---

## 15.1. Luồng load plugin

```mermaid
sequenceDiagram
    participant Service as Core Service
    participant Manager as Plugin Manager
    participant FS as Plugin Folder
    participant Plugin as Plugin

    Service->>Manager: load_plugins()
    Manager->>FS: scan plugins/
    FS->>Manager: plugin.yaml
    Manager->>Manager: validate metadata
    Manager->>Plugin: import module
    Manager->>Plugin: create instance
    Plugin->>Manager: ready
    Manager->>Service: plugin registered
```

---

## 15.2. Ví dụ Plugin Manager

```python
import importlib
from pathlib import Path

class PluginManager:
    def __init__(self, plugin_dir: str):
        self.plugin_dir = Path(plugin_dir)
        self.plugins = {}

    def load_plugin(self, plugin_name: str, config: dict):
        module_path = f"plugins.{plugin_name}.plugin"
        module = importlib.import_module(module_path)

        plugin_class = getattr(module, "Plugin")
        plugin_instance = plugin_class(config)

        self.plugins[plugin_name] = plugin_instance

        return plugin_instance

    def get_plugin(self, plugin_name: str):
        return self.plugins.get(plugin_name)
```

---

# 16. Cấu hình device-agent với plugin

```yaml
agent:
  id: device-agent-gate-01
  name: Device Agent Cổng 01

server:
  gateway_url: ws://parking-gateway:8300/ws/device-agent
  agent_token: CHANGE_ME

devices:
  - id: rfid-entry-01
    name: RFID Cổng Vào
    type: rfid_reader
    plugin: rfid_serial
    enabled: true
    config:
      port: /dev/ttyUSB0
      baudrate: 9600
      timeout: 1

  - id: barrier-entry-01
    name: Barrier Cổng Vào
    type: barrier
    plugin: barrier_tcp
    enabled: true
    config:
      host: 192.168.10.50
      port: 6000
      open_command: OPEN
      close_command: CLOSE
```

---

# 17. Cấu hình camera-agent với plugin

```yaml
agent:
  id: camera-agent-gate-01
  name: Camera Agent Cổng 01

server:
  gateway_url: ws://parking-gateway:8300/ws/camera-agent
  agent_token: CHANGE_ME

cameras:
  - id: cam-entry-overview
    name: Camera Toàn Cảnh Cổng Vào
    type: rtsp
    plugin: rtsp_camera
    role: entry_overview
    enabled: true
    config:
      url: rtsp://admin:password@192.168.10.101:554/Streaming/Channels/101
      fps: 10
      width: 1920
      height: 1080

  - id: cam-entry-plate
    name: Camera Biển Số Cổng Vào
    type: rtsp
    plugin: rtsp_camera
    role: entry_plate
    enabled: true
    config:
      url: rtsp://admin:password@192.168.10.102:554/Streaming/Channels/101
      fps: 10
      width: 1920
      height: 1080
```

---

# 18. Cấu hình worker với plugin

```yaml
worker:
  name: worker-alpr
  queue: alpr

plugins:
  alpr:
    plugin: yolo_alpr
    enabled: true
    config:
      model_path: /app/models/yolo/plate-detector.pt
      device: cpu
      confidence_threshold: 0.6

  ocr:
    plugin: paddle_ocr
    enabled: true
    config:
      lang: en
      use_angle_cls: true
      device: cpu
```

---

# 19. Mock Plugin

Mọi nhóm plugin nên có mock plugin.

## 19.1. Mock RFID

```json
{
  "event_type": "card.scanned",
  "payload": {
    "card_uid": "MOCK-000001"
  }
}
```

## 19.2. Mock Camera

Trả ảnh mẫu từ thư mục:

```text
samples/images/
```

## 19.3. Mock Barrier

Luôn trả:

```json
{
  "success": true,
  "command": "open"
}
```

## 19.4. Mock OCR

```json
{
  "success": true,
  "text": "51A12345",
  "confidence": 0.99
}
```

---

# 20. Error handling

Plugin lỗi không được làm crash toàn bộ service.

Nguyên tắc:

* Catch exception trong plugin
* Ghi log
* Đánh dấu plugin offline
* Gửi event lỗi về Gateway
* Tự reconnect nếu có thể

Ví dụ event lỗi:

```json
{
  "event_type": "device.error",
  "source": "device-agent",
  "source_id": "device-agent-gate-01",
  "device_id": "rfid-entry-01",
  "payload": {
    "plugin": "rfid_serial",
    "error_code": "SERIAL_PORT_NOT_FOUND",
    "message": "Không tìm thấy /dev/ttyUSB0"
  }
}
```

---

# 21. Plugin lifecycle

Một plugin có vòng đời:

```mermaid
stateDiagram-v2
    [*] --> Loaded
    Loaded --> Configured
    Configured --> Connected
    Connected --> Running
    Running --> Error
    Error --> Reconnecting
    Reconnecting --> Connected
    Running --> Stopped
    Stopped --> [*]
```

---

# 22. Hot reload plugin

MVP chưa cần hot reload.

Production có thể hỗ trợ:

```text
Sửa file config
    ↓
Agent phát hiện thay đổi
    ↓
Disconnect plugin cũ
    ↓
Load config mới
    ↓
Connect lại plugin
```

Lưu ý:

* Không hot reload khi đang xử lý command quan trọng.
* Nên ghi audit log nếu config thay đổi từ UI.
* Nên validate config trước khi reload.

---

# 23. Security cho plugin

## 23.1. Không chạy plugin không rõ nguồn

Plugin có thể truy cập thiết bị, file, network.

Vì vậy:

* Chỉ load plugin trong thư mục được cấu hình
* Không auto tải plugin từ Internet
* Không cho plugin tự sửa `.env`
* Không cho plugin truy cập trực tiếp database
* Không cho plugin đọc secret không liên quan

---

## 23.2. Plugin permission

Có thể thiết kế permission cho plugin:

```yaml
permissions:
  network: true
  serial: true
  usb: true
  filesystem: false
  database: false
```

---

# 24. Quy ước đặt tên plugin

Dùng snake_case.

Ví dụ đúng:

```text
rfid_serial
rfid_tcp
rfid_keyboard
barrier_tcp
relay_usb
rtsp_camera
onvif_camera
paddle_ocr
yolo_alpr
```

Không nên:

```text
RFIDSerial
rfid-serial
serialReaderPlugin
```

---

# 25. Versioning

Plugin dùng SemVer:

```text
MAJOR.MINOR.PATCH
```

Ví dụ:

```text
1.0.0
1.1.0
2.0.0
```

Quy ước:

* Tăng `PATCH` khi sửa lỗi nhỏ.
* Tăng `MINOR` khi thêm tính năng không phá vỡ tương thích.
* Tăng `MAJOR` khi thay đổi interface.

---

# 26. Testing plugin

Mỗi plugin cần có test.

Ví dụ:

```text
tests/plugins/device/test_rfid_serial.py
tests/plugins/camera/test_rtsp_camera.py
tests/plugins/worker/test_paddle_ocr.py
```

Test nên kiểm tra:

* Load plugin
* Validate config
* Connect
* Health
* Read/write
* Error handling
* Mock mode

---

# 27. Checklist khi thêm plugin mới

```text
[ ] Tạo thư mục plugin
[ ] Tạo plugin.yaml
[ ] Implement interface
[ ] Thêm config_schema
[ ] Thêm test
[ ] Thêm tài liệu hướng dẫn
[ ] Thêm ví dụ config
[ ] Kiểm tra mock mode
[ ] Kiểm tra error handling
[ ] Kiểm tra log
```

---

# 28. Plugin marketplace trong tương lai

Sau này có thể phát triển:

```text
Plugin Registry
Plugin Marketplace
Plugin Installer
Plugin Version Manager
```

Ví dụ:

```bash
parking plugin install rfid_zkteco
parking plugin update rfid_zkteco
parking plugin list
```

MVP chưa cần tính năng này.

---

# 29. Roadmap

## MVP

Hỗ trợ plugin:

```text
rfid_keyboard
rfid_serial
rfid_tcp
barrier_tcp
rtsp_camera
usb_camera
mock_device
mock_camera
mock_ocr
```

---

## Version 1

Thêm:

```text
onvif_camera
http_snapshot_camera
relay_usb
mqtt_device
paddle_ocr
yolo_alpr
```

---

## Version 2

Thêm:

```text
zkteco_reader
acr122u_reader
wiegand_controller
hikvision_sdk
dahua_sdk
insightface
cloud_ocr
plugin_marketplace
```

---

# 30. Tổng kết

Plugin System giúp Parking System trở thành nền tảng mở.

Nguyên tắc chính:

* Core không phụ thuộc thiết bị cụ thể.
* Mỗi thiết bị là một plugin.
* Mỗi AI engine là một plugin.
* Plugin không truy cập trực tiếp database.
* Plugin giao tiếp với core qua interface chuẩn.
* Plugin lỗi không được làm crash service.
* Mọi plugin cần metadata, config schema và test.

Thiết kế này giúp hệ thống dễ mở rộng từ MVP đến production nhiều bãi xe, nhiều loại thiết bị và nhiều mô hình AI khác nhau.
