# docs/API_REFERENCE.md

# API Reference

## 1. Giới thiệu

Tài liệu này mô tả hệ thống REST API của **Parking System**.

`parking-api` là service xử lý nghiệp vụ chính:

* Đăng nhập
* Quản lý người dùng
* Quản lý chủ xe
* Quản lý phương tiện
* Quản lý thẻ RFID
* Quản lý bãi xe
* Quản lý cổng
* Quản lý thiết bị
* Quản lý camera
* Check-in
* Check-out
* Tính phí
* Thanh toán
* Media
* Báo cáo
* Audit log

Realtime WebSocket không nằm trực tiếp ở `parking-api`, mà được xử lý bởi:

```text
parking-gateway
```

---

# 2. Base URL

## Development

```text
http://localhost:8000/api/v1
```

## Production

```text
https://parking.example.com/api/v1
```

---

# 3. Authentication

API sử dụng JWT.

Client gửi token qua header:

```http
Authorization: Bearer <access_token>
```

---

# 4. Response format chuẩn

## 4.1. Thành công

```json
{
  "success": true,
  "data": {},
  "message": "OK"
}
```

## 4.2. Lỗi

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Dữ liệu không hợp lệ",
    "details": {}
  }
}
```

---

# 5. HTTP status code

| Status | Ý nghĩa              |
| -----: | -------------------- |
|    200 | Thành công           |
|    201 | Tạo mới thành công   |
|    400 | Request không hợp lệ |
|    401 | Chưa đăng nhập       |
|    403 | Không đủ quyền       |
|    404 | Không tìm thấy       |
|    409 | Xung đột dữ liệu     |
|    422 | Validation error     |
|    500 | Lỗi server           |

---

# 6. Pagination

Các API danh sách dùng format:

```http
GET /resources?page=1&page_size=20
```

Response:

```json
{
  "success": true,
  "data": {
    "items": [],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 100,
      "total_pages": 5
    }
  }
}
```

---

# 7. Sort và filter

Ví dụ:

```http
GET /vehicles?search=51A&page=1&page_size=20&sort=-created_at
```

Quy ước:

```text
sort=created_at     tăng dần
sort=-created_at    giảm dần
```

---

# 8. Auth API

## 8.1. Login

```http
POST /auth/login
```

Request:

```json
{
  "username": "admin",
  "password": "admin123"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "access_token": "jwt-access-token",
    "refresh_token": "jwt-refresh-token",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "uuid",
      "username": "admin",
      "full_name": "Administrator",
      "role": "admin"
    }
  }
}
```

---

## 8.2. Refresh token

```http
POST /auth/refresh
```

Request:

```json
{
  "refresh_token": "jwt-refresh-token"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "access_token": "new-access-token",
    "expires_in": 3600
  }
}
```

---

## 8.3. Logout

```http
POST /auth/logout
```

Response:

```json
{
  "success": true,
  "message": "Đăng xuất thành công"
}
```

---

## 8.4. Thông tin người dùng hiện tại

```http
GET /auth/me
```

Response:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "username": "admin",
    "full_name": "Administrator",
    "email": "admin@example.com",
    "role": {
      "code": "admin",
      "name": "Quản trị viên"
    }
  }
}
```

---

# 9. Users API

## 9.1. Danh sách người dùng

```http
GET /users
```

Query:

| Tên       | Kiểu    | Bắt buộc | Mô tả                         |
| --------- | ------- | -------: | ----------------------------- |
| search    | string  |    Không | Tìm theo tên, username, email |
| role      | string  |    Không | Lọc theo role                 |
| is_active | boolean |    Không | Trạng thái                    |
| page      | integer |    Không | Trang                         |
| page_size | integer |    Không | Số dòng/trang                 |

Response:

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "username": "guard01",
        "full_name": "Nguyễn Văn A",
        "email": "guard01@example.com",
        "role": "guard",
        "is_active": true
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 1,
      "total_pages": 1
    }
  }
}
```

---

## 9.2. Tạo người dùng

```http
POST /users
```

Permission:

```text
user.create
```

Request:

```json
{
  "username": "guard01",
  "password": "123456",
  "full_name": "Nguyễn Văn A",
  "email": "guard01@example.com",
  "phone": "0900000000",
  "role_id": "uuid",
  "is_active": true
}
```

Response:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "username": "guard01"
  }
}
```

---

## 9.3. Cập nhật người dùng

```http
PUT /users/{id}
```

Permission:

```text
user.update
```

Request:

```json
{
  "full_name": "Nguyễn Văn A",
  "email": "guard01@example.com",
  "phone": "0900000000",
  "role_id": "uuid",
  "is_active": true
}
```

---

## 9.4. Khóa người dùng

```http
POST /users/{id}/disable
```

Permission:

```text
user.disable
```

---

# 10. Roles API

## 10.1. Danh sách role

```http
GET /roles
```

Response:

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "code": "admin",
      "name": "Quản trị viên",
      "permissions": {
        "*": true
      }
    },
    {
      "id": "uuid",
      "code": "guard",
      "name": "Nhân viên bảo vệ",
      "permissions": {
        "parking.checkin": true,
        "parking.checkout": true
      }
    }
  ]
}
```

---

# 11. Owners API

## 11.1. Danh sách chủ xe

```http
GET /owners
```

Query:

```text
search
owner_type
is_active
page
page_size
```

---

## 11.2. Tạo chủ xe

```http
POST /owners
```

Request:

```json
{
  "owner_code": "EMP001",
  "full_name": "Nguyễn Văn A",
  "owner_type": "employee",
  "phone": "0900000000",
  "email": "a@example.com",
  "identity_number": "012345678901",
  "address": "TP.HCM",
  "note": "Nhân viên công ty"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "owner_code": "EMP001"
  }
}
```

---

## 11.3. Chi tiết chủ xe

```http
GET /owners/{id}
```

Response:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "owner_code": "EMP001",
    "full_name": "Nguyễn Văn A",
    "vehicles": [
      {
        "id": "uuid",
        "plate_number": "51A-12345"
      }
    ],
    "cards": [
      {
        "id": "uuid",
        "card_uid": "04A12345",
        "status": "active"
      }
    ]
  }
}
```

---

# 12. Vehicles API

## 12.1. Danh sách phương tiện

```http
GET /vehicles
```

Query:

| Tên             | Mô tả                    |
| --------------- | ------------------------ |
| search          | Tìm theo biển số, chủ xe |
| plate           | Biển số                  |
| owner_id        | Chủ xe                   |
| vehicle_type_id | Loại xe                  |
| is_active       | Trạng thái               |

---

## 12.2. Tạo phương tiện

```http
POST /vehicles
```

Request:

```json
{
  "owner_id": "uuid",
  "vehicle_type_id": "uuid",
  "plate_number": "51A-12345",
  "brand": "Honda",
  "model": "Vision",
  "color": "Đen",
  "description": "Xe nhân viên"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "plate_number": "51A-12345",
    "normalized_plate_number": "51A12345"
  }
}
```

---

## 12.3. Tìm theo biển số

```http
GET /vehicles/search?plate=51A12345
```

Response:

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "plate_number": "51A-12345",
      "owner": {
        "id": "uuid",
        "full_name": "Nguyễn Văn A"
      },
      "vehicle_type": {
        "code": "motorbike",
        "name": "Xe máy"
      }
    }
  ]
}
```

---

# 13. Vehicle Types API

## 13.1. Danh sách loại xe

```http
GET /vehicle-types
```

Response:

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "code": "motorbike",
      "name": "Xe máy"
    },
    {
      "id": "uuid",
      "code": "car",
      "name": "Ô tô"
    }
  ]
}
```

---

## 13.2. Tạo loại xe

```http
POST /vehicle-types
```

Request:

```json
{
  "code": "electric_bike",
  "name": "Xe đạp điện",
  "description": "Xe đạp điện / xe máy điện",
  "color": "#10B981"
}
```

---

# 14. RFID Cards API

## 14.1. Danh sách thẻ

```http
GET /cards
```

Query:

```text
search
status
card_type
assigned_vehicle_id
assigned_owner_id
page
page_size
```

---

## 14.2. Tạo thẻ

```http
POST /cards
```

Request:

```json
{
  "card_uid": "04A12345",
  "card_number": "CARD0001",
  "card_type": "rfid",
  "assigned_vehicle_id": "uuid",
  "assigned_owner_id": "uuid",
  "expired_at": "2027-01-01T00:00:00+07:00",
  "note": "Thẻ xe nhân viên"
}
```

---

## 14.3. Tìm thẻ theo UID

```http
GET /cards/by-uid/{uid}
```

Response:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "card_uid": "04A12345",
    "status": "active",
    "assigned_vehicle": {
      "id": "uuid",
      "plate_number": "51A-12345"
    },
    "assigned_owner": {
      "id": "uuid",
      "full_name": "Nguyễn Văn A"
    }
  }
}
```

---

## 14.4. Khóa thẻ

```http
POST /cards/{id}/block
```

Permission:

```text
card.block
```

Request:

```json
{
  "reason": "Báo mất thẻ"
}
```

---

## 14.5. Mở khóa thẻ

```http
POST /cards/{id}/unblock
```

Permission:

```text
card.unblock
```

Request:

```json
{
  "reason": "Đã tìm lại thẻ"
}
```

---

# 15. Parking Sites API

## 15.1. Danh sách bãi xe

```http
GET /parking-sites
```

---

## 15.2. Tạo bãi xe

```http
POST /parking-sites
```

Request:

```json
{
  "code": "main-site",
  "name": "Bãi xe chính",
  "address": "TP.HCM",
  "timezone": "Asia/Ho_Chi_Minh"
}
```

---

# 16. Parking Zones API

## 16.1. Danh sách khu vực

```http
GET /parking-zones
```

Query:

```text
site_id
vehicle_type_id
is_active
```

---

## 16.2. Tạo khu vực

```http
POST /parking-zones
```

Request:

```json
{
  "site_id": "uuid",
  "code": "zone-b1",
  "name": "Tầng hầm B1",
  "capacity": 500,
  "vehicle_type_id": "uuid"
}
```

---

# 17. Parking Gates API

## 17.1. Danh sách cổng

```http
GET /parking-gates
```

Query:

```text
site_id
zone_id
direction
is_active
```

---

## 17.2. Tạo cổng

```http
POST /parking-gates
```

Request:

```json
{
  "zone_id": "uuid",
  "code": "gate-entry-01",
  "name": "Cổng vào số 1",
  "gate_type": "entry",
  "direction": "in"
}
```

---

# 18. Devices API

## 18.1. Danh sách thiết bị

```http
GET /devices
```

Query:

```text
gate_id
device_type
status
agent_id
```

---

## 18.2. Tạo thiết bị

```http
POST /devices
```

Request:

```json
{
  "gate_id": "uuid",
  "code": "rfid-entry-01",
  "name": "RFID Cổng Vào",
  "device_type": "rfid_reader",
  "connection_type": "serial",
  "agent_id": "device-agent-gate-01",
  "connection_config": {
    "port": "/dev/ttyUSB0",
    "baudrate": 9600
  }
}
```

---

## 18.3. Mở barrier

```http
POST /devices/{id}/open
```

Permission:

```text
barrier.open
```

Request:

```json
{
  "reason": "Mở thủ công từ màn hình quản lý",
  "duration_ms": 1500
}
```

Response:

```json
{
  "success": true,
  "data": {
    "command_id": "uuid",
    "status": "queued"
  }
}
```

Event sinh ra:

```text
barrier.open.request
```

Stream:

```text
parking.commands
```

---

## 18.4. Đóng barrier

```http
POST /devices/{id}/close
```

Permission:

```text
barrier.close
```

---

## 18.5. Restart thiết bị

```http
POST /devices/{id}/restart
```

Permission:

```text
device.restart
```

---

# 19. Cameras API

## 19.1. Danh sách camera

```http
GET /cameras
```

Query:

```text
gate_id
camera_type
role
status
agent_id
```

---

## 19.2. Tạo camera

```http
POST /cameras
```

Request:

```json
{
  "gate_id": "uuid",
  "code": "cam-entry-overview",
  "name": "Camera Toàn Cảnh Cổng Vào",
  "camera_type": "rtsp",
  "role": "entry_overview",
  "stream_url": "rtsp://admin:password@192.168.10.101:554/Streaming/Channels/101",
  "agent_id": "camera-agent-gate-01",
  "config": {
    "fps": 10,
    "width": 1920,
    "height": 1080
  }
}
```

---

## 19.3. Snapshot

```http
POST /cameras/{id}/snapshot
```

Request:

```json
{
  "snapshot_type": "manual",
  "quality": 90
}
```

Response:

```json
{
  "success": true,
  "data": {
    "command_id": "uuid",
    "status": "queued"
  }
}
```

Command sinh ra:

```text
camera.snapshot.request
```

Stream:

```text
parking.commands
```

---

# 20. Parking Sessions API

Đây là nhóm API quan trọng nhất.

---

## 20.1. Danh sách lượt gửi xe

```http
GET /parking-sessions
```

Query:

| Tên       | Mô tả                        |
| --------- | ---------------------------- |
| status    | active, completed, cancelled |
| plate     | Biển số                      |
| card_uid  | UID thẻ                      |
| from_date | Từ ngày                      |
| to_date   | Đến ngày                     |
| site_id   | Bãi xe                       |
| gate_id   | Cổng                         |
| page      | Trang                        |
| page_size | Số dòng/trang                |

---

## 20.2. Chi tiết lượt gửi xe

```http
GET /parking-sessions/{id}
```

Response:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "session_code": "PK202606170001",
    "status": "active",
    "entry_time": "2026-06-17T08:30:00+07:00",
    "exit_time": null,
    "entry_plate_number": "51A12345",
    "exit_plate_number": null,
    "vehicle": {
      "id": "uuid",
      "plate_number": "51A-12345"
    },
    "card": {
      "id": "uuid",
      "card_uid": "04A12345"
    },
    "entry_images": {
      "overview": "media-id",
      "plate": "media-id"
    },
    "exit_images": null,
    "calculated_fee": 0,
    "payment_status": "unpaid"
  }
}
```

---

## 20.3. Check-in thủ công

API này dùng cho trường hợp nhập tay từ web hoặc fallback khi mất đầu đọc.

```http
POST /parking-sessions/checkin
```

Permission:

```text
parking.checkin
```

Request:

```json
{
  "card_uid": "04A12345",
  "gate_id": "uuid",
  "vehicle_type_id": "uuid",
  "plate_number": "51A12345",
  "note": "Check-in thủ công"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "session_id": "uuid",
    "session_code": "PK202606170001",
    "status": "active",
    "entry_time": "2026-06-17T08:30:00+07:00"
  }
}
```

Realtime event:

```text
parking.checkin.created
```

Pub/Sub channel:

```text
parking.realtime
```

---

## 20.4. Checkout thủ công

```http
POST /parking-sessions/checkout
```

Permission:

```text
parking.checkout
```

Request:

```json
{
  "card_uid": "04A12345",
  "gate_id": "uuid",
  "plate_number": "51A12345",
  "payment_method": "cash",
  "paid_amount": 5000,
  "note": "Checkout thủ công"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "session_id": "uuid",
    "status": "completed",
    "duration_minutes": 510,
    "calculated_fee": 5000,
    "paid_amount": 5000,
    "payment_status": "paid"
  }
}
```

Realtime event:

```text
parking.checkout.completed
```

---

## 20.5. Hủy lượt gửi xe

```http
POST /parking-sessions/{id}/cancel
```

Permission:

```text
parking.session.cancel
```

Request:

```json
{
  "reason": "Tạo nhầm lượt gửi xe"
}
```

---

## 20.6. Đóng lượt gửi xe thủ công

Dùng khi mất thẻ hoặc lỗi thiết bị.

```http
POST /parking-sessions/{id}/manual-close
```

Permission:

```text
parking.session.manual_close
```

Request:

```json
{
  "reason": "Khách mất thẻ",
  "exit_time": "2026-06-17T18:00:00+07:00",
  "paid_amount": 20000,
  "payment_method": "cash"
}
```

---

# 21. Fee Rules API

## 21.1. Danh sách quy tắc tính phí

```http
GET /fee-rules
```

---

## 21.2. Tạo quy tắc tính phí

```http
POST /fee-rules
```

Request tính theo lượt:

```json
{
  "code": "motorbike-flat",
  "name": "Xe máy theo lượt",
  "vehicle_type_id": "uuid",
  "rule_type": "flat",
  "priority": 10,
  "config": {
    "amount": 5000
  }
}
```

Request tính theo giờ:

```json
{
  "code": "car-hourly",
  "name": "Ô tô theo giờ",
  "vehicle_type_id": "uuid",
  "rule_type": "hourly",
  "priority": 10,
  "config": {
    "first_hours": 2,
    "first_amount": 20000,
    "next_hour_amount": 10000,
    "max_daily_amount": 100000
  }
}
```

---

## 21.3. Tính thử phí

```http
POST /fee-rules/calculate
```

Request:

```json
{
  "vehicle_type_id": "uuid",
  "entry_time": "2026-06-17T08:00:00+07:00",
  "exit_time": "2026-06-17T17:00:00+07:00"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "amount": 5000,
    "rule_id": "uuid",
    "rule_name": "Xe máy theo lượt"
  }
}
```

---

# 22. Payments API

## 22.1. Danh sách thanh toán

```http
GET /payments
```

Query:

```text
parking_session_id
payment_method
from_date
to_date
```

---

## 22.2. Tạo thanh toán

```http
POST /payments
```

Request:

```json
{
  "parking_session_id": "uuid",
  "amount": 5000,
  "payment_method": "cash",
  "reference_code": "CASH-001",
  "note": "Thanh toán tiền mặt"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "amount": 5000,
    "payment_status": "paid"
  }
}
```

---

# 23. Media API

## 23.1. Upload media

```http
POST /media/upload
```

Content-Type:

```text
multipart/form-data
```

Fields:

| Tên         | Mô tả                           |
| ----------- | ------------------------------- |
| file        | File ảnh/video                  |
| source_type | parking_session, vehicle, owner |
| source_id   | UUID                            |
| media_type  | image, video, snapshot          |

Response:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "bucket": "parking-media",
    "object_key": "main-site/2026/06/17/file.jpg",
    "mime_type": "image/jpeg",
    "file_size": 204800
  }
}
```

---

## 23.2. Signed URL

```http
GET /media/{id}/signed-url
```

Query:

```text
expires=300
```

Response:

```json
{
  "success": true,
  "data": {
    "url": "http://localhost:9000/parking-media/...",
    "expires_in": 300
  }
}
```

---

## 23.3. Xóa media

```http
DELETE /media/{id}
```

Permission:

```text
media.delete
```

---

# 24. Dashboard API

## 24.1. Tổng quan

```http
GET /dashboard/overview
```

Query:

```text
site_id
date
```

Response:

```json
{
  "success": true,
  "data": {
    "vehicles_inside": 132,
    "today_entry": 850,
    "today_exit": 718,
    "today_revenue": 12500000,
    "available_spaces": 368,
    "device_online": 8,
    "device_offline": 1,
    "camera_online": 6,
    "camera_offline": 0
  }
}
```

---

## 24.2. Lưu lượng theo giờ

```http
GET /dashboard/hourly
```

Query:

```text
site_id
date
```

Response:

```json
{
  "success": true,
  "data": [
    {
      "hour": "08:00",
      "entry": 120,
      "exit": 40
    },
    {
      "hour": "09:00",
      "entry": 150,
      "exit": 60
    }
  ]
}
```

---

## 24.3. Doanh thu theo ngày

```http
GET /dashboard/revenue-daily
```

Query:

```text
site_id
from_date
to_date
```

---

# 25. Reports API

## 25.1. Báo cáo lượt gửi xe

```http
GET /reports/parking-sessions
```

Query:

```text
from_date
to_date
site_id
vehicle_type_id
status
```

---

## 25.2. Báo cáo doanh thu

```http
GET /reports/revenue
```

Query:

```text
from_date
to_date
site_id
group_by=day|month|vehicle_type|gate
```

---

## 25.3. Export Excel

```http
GET /reports/revenue/export.xlsx
```

---

# 26. Audit Logs API

## 26.1. Danh sách audit log

```http
GET /audit-logs
```

Permission:

```text
audit_log.view
```

Query:

```text
user_id
action
resource_type
resource_id
from_date
to_date
```

Response:

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "user": {
          "id": "uuid",
          "full_name": "Nguyễn Văn A"
        },
        "action": "barrier.open_manual",
        "resource_type": "device",
        "resource_id": "uuid",
        "created_at": "2026-06-17T09:30:00+07:00"
      }
    ]
  }
}
```

---

# 27. System Settings API

## 27.1. Danh sách cấu hình

```http
GET /settings
```

Permission:

```text
settings.view
```

---

## 27.2. Cập nhật cấu hình

```http
PUT /settings/{setting_key}
```

Permission:

```text
settings.update
```

Request:

```json
{
  "setting_value": {
    "image_retention_days": 180
  }
}
```

---

# 28. Health API

## 28.1. Health cơ bản

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

---

## 28.2. Health đầy đủ

```http
GET /health/full
```

Response:

```json
{
  "status": "ok",
  "dependencies": {
    "postgres": "ok",
    "redis": "ok",
    "minio": "ok"
  }
}
```

---

# 29. Error codes

| Code                      | Ý nghĩa                         |
| ------------------------- | ------------------------------- |
| AUTH_INVALID_CREDENTIALS  | Sai username hoặc password      |
| AUTH_TOKEN_EXPIRED        | Token hết hạn                   |
| PERMISSION_DENIED         | Không đủ quyền                  |
| VALIDATION_ERROR          | Dữ liệu không hợp lệ            |
| RESOURCE_NOT_FOUND        | Không tìm thấy dữ liệu          |
| CARD_NOT_FOUND            | Không tìm thấy thẻ              |
| CARD_BLOCKED              | Thẻ đã bị khóa                  |
| CARD_EXPIRED              | Thẻ hết hạn                     |
| SESSION_ACTIVE_EXISTS     | Thẻ đang có lượt gửi xe active  |
| SESSION_NOT_FOUND         | Không tìm thấy lượt gửi xe      |
| SESSION_ALREADY_COMPLETED | Lượt gửi xe đã hoàn tất         |
| CAMERA_OFFLINE            | Camera offline                  |
| DEVICE_OFFLINE            | Thiết bị offline                |
| BARRIER_COMMAND_FAILED    | Mở barrier thất bại             |
| PAYMENT_INVALID_AMOUNT    | Số tiền thanh toán không hợp lệ |

---

# 30. Permission chính

```text
user.view
user.create
user.update
user.disable

role.view
role.update

owner.view
owner.create
owner.update
owner.delete

vehicle.view
vehicle.create
vehicle.update
vehicle.delete

card.view
card.create
card.update
card.block
card.unblock

parking.checkin
parking.checkout
parking.session.cancel
parking.session.manual_close

device.view
device.create
device.update
device.restart

barrier.open
barrier.close

camera.view
camera.create
camera.update
camera.snapshot

media.view
media.delete

report.view
report.export

settings.view
settings.update

audit_log.view
```

---

# 31. Event liên quan API

## 31.1. API publish vào Redis Streams

```text
parking.commands
parking.tasks
```

Ví dụ:

```text
camera.snapshot.request
barrier.open.request
ocr.detect_plate.request
alpr.detect_plate.request
```

---

## 31.2. API consume từ Redis Streams

```text
parking.events
```

Ví dụ:

```text
card.scanned
camera.snapshot.completed
barrier.opened
ocr.detect_plate.completed
```

---

## 31.3. API publish vào Redis Pub/Sub

```text
parking.realtime
parking.notifications
```

Ví dụ:

```text
parking.checkin.created
parking.checkout.completed
parking.warning.created
device.online
camera.offline
```

---

# 32. Tổng kết

`parking-api` là service nghiệp vụ chính.

Nguyên tắc:

* REST API dùng cho thao tác quản trị và nghiệp vụ từ Web.
* WebSocket không nằm trực tiếp trong API, mà qua `parking-gateway`.
* Event nghiệp vụ dùng Redis Streams.
* Event realtime dùng Redis Pub/Sub.
* Tất cả thao tác quan trọng phải ghi audit log.
* Các API nhạy cảm phải kiểm tra permission.
