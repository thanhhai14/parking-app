# Phase 3: Gateway & EventBus (Xương sống Realtime)

Bước vào giai đoạn kiến trúc nâng cao. Ở đây chúng ta sẽ tháo rời giao tiếp trực tiếp khỏi API, thay vào đó điều hướng qua `parking-gateway` và Redis (Event-Driven).

## 1. Mục tiêu (Goals)
* Xây dựng thành công service `parking-gateway` chuyên xử lý hàng ngàn kết nối WebSocket.
* Tích hợp Redis Streams để lưu sự kiện nghiệp vụ và Redis Pub/Sub để phát sự kiện màn hình.
* Hoàn thiện CQRS Pattern: Mọi hành động từ thiết bị đều là Event (từ Gateway vào Redis), `parking-api` trở thành Consumer xử lý ngầm.

## 2. Checklist Công việc

### 2.1. Khởi tạo `parking-gateway`
- [ ] Khởi tạo project FastAPI mới trên thư mục `gateway/`.
- [ ] Thiết lập WebSocket Router. Viết code quản lý danh sách connection (Web, Device, Camera).
- [ ] Viết luồng Ping/Pong Heartbeat để xóa các kết nối bị rớt mạng.

### 2.2. Xây dựng Event Bus (Redis)
- [ ] Viết module `redis_client.py` trong Gateway và API.
- [ ] Định nghĩa các Event Format (JSON Schema chuẩn) dựa theo `EVENTS_AND_FLOWS.md`.

### 2.3. Cầu nối (Routing Logic)
Tại `parking-gateway`:
- [ ] Viết logic: Nhận WebSocket JSON -> Nếu là `card.scanned` -> Đẩy vào **Redis Stream** (`parking.events`).

Tại `parking-api`:
- [ ] Viết Background Task / Consumer dùng thư viện `aioredis` (hoặc `FastStream`) để đọc liên tục từ `parking.events`.
- [ ] Consumer nhận event `card.scanned` -> Gọi logic check-in (từ Phase 2) để lưu vào DB.
- [ ] Sau khi lưu DB xong -> API đẩy sự kiện `checkin.created` vào **Redis Pub/Sub** (`parking.realtime`).

Tại `parking-gateway` (lượt về):
- [ ] Gateway subscribe `parking.realtime`.
- [ ] Khi nhận được `checkin.created` từ Pub/Sub -> Đẩy sự kiện này qua WebSocket xuống các Web Clients đang mở.

## 3. Điều kiện Hoàn thành (Definition of Done - DoD)
* Dùng công cụ test WebSocket (như Postman WS) đóng giả Agent, gửi `card.scanned` tới Gateway.
* Thấy data chui vào Redis Stream, API tự động bắt được và lưu vào DB Postgres mà không cần gọi HTTP.
* Gateway tự động phản hồi lại qua WebSocket sự kiện báo thành công.

> [!NEXT]
> Khung xương Event Bus đã hoàn thiện. Giờ là lúc gắn "tay chân" vào thông qua **Phase 4: Tích hợp Thiết bị Biên (Edge Agents)**.
