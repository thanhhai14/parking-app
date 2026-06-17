# Báo cáo Kết quả Phase 3: Gateway & EventBus (Xương sống Realtime)

Báo cáo này tóm tắt kết quả triển khai Phase 3, xây dựng cơ sở hạ tầng giao tiếp realtime dựa trên sự kiện (Event-Driven Architecture) bằng cách kết hợp FastAPI WebSockets, Redis Streams và Redis Pub/Sub.

## 1. Các thành phần đã triển khai

### A. Docker Compose & Cấu hình môi trường
- Đã cấu hình hot-reload cho service `parking-gateway` bằng cách mount volume `./apps/parking-gateway:/app` và `./test:/app/test` vào trong container, đồng thời chạy server uvicorn bằng cờ `--reload`.
- Bổ sung thư viện `redis>=5.0.0` vào `apps/parking-api/requirements.txt` để hỗ trợ kết nối async Redis.

### B. Idempotency Model & Migrations (API)
- **Model mới**: Tạo model `ProcessedEvent` tại `apps/parking-api/models/processed_event.py` để lưu giữ thông tin định danh của các sự kiện đã xử lý, đảm bảo chống trùng lặp dữ liệu (Idempotency).
- **Migration**: Đã tạo và áp dụng thành công script Alembic migration `374047e3e6ad_create_processed_events.py` để đồng bộ CSDL PostgreSQL.

### C. API Event Consumer (FastAPI Background Task)
- Xây dựng background worker tại `apps/parking-api/services/event_consumer.py` chạy bất đồng bộ cùng FastAPI lifespan:
  - Tự động đăng ký Consumer Group `parking-api-group` trên Redis Stream `parking.events`.
  - Liên tục consume các sự kiện `card.scanned` từ stream.
  - Phân tích và quyết định Check-In hoặc Check-Out dựa trên trạng thái của thẻ RFID (sử dụng logic nghiệp vụ và Pricing Engine thừa kế từ Phase 2).
  - Cập nhật CSDL và ghi nhận trạng thái vào bảng `processed_events`.
  - Publish realtime event (`parking.checkin.created`, `parking.checkout.completed`) lên kênh Pub/Sub `parking.realtime`.
  - Xác nhận xử lý sự kiện qua `XACK`.

### D. Service Parking Gateway
- Tạo mới service độc lập tại `apps/parking-gateway` sử dụng Python 3.10-slim.
- Thiết lập `main.py` khai báo các WebSocket router:
  - `/ws/web`: Xác thực JWT token của người dùng trước khi chấp nhận kết nối.
  - `/ws/device-agent`: Xác thực Agent token tĩnh của thiết bị. Nhận event `card.scanned` từ Agent, chuẩn hóa thành định dạng chuẩn JSON và đẩy vào Redis Stream `parking.events` qua `XADD`.
  - `/ws/camera-agent`: Xác thực Agent token của camera, nhận dữ liệu ảnh/event đẩy vào Stream.
- Tránh bóng mờ import (Module Shadowing) bằng cách đặt tên thư mục Redis cục bộ là `redis_gateway`.
- Khởi chạy background tasks trong Gateway:
  - Subscriber kênh Pub/Sub `parking.realtime` để chuyển tiếp (broadcast) mọi sự kiện tạo lượt gửi/hoàn thành lượt gửi xe tới Web client.
  - Reader stream `parking.commands` để điều phối lệnh từ API tới các Agent qua WebSocket.
  - Cơ chế heartbeat dọn dẹp các connection chết qua `asyncio.wait_for` trên WebSocket.

---

## 2. Kết quả Kiểm thử (Verification & Testing)

### A. Kịch bản test tự động
Chúng tôi đã viết file test tích hợp tại [test/03_gateway_eventbus_integration_test.py](file:///home/thanhhai14/Data/Code/parking-app/test/03_gateway_eventbus_integration_test.py):
1. Khởi tạo dữ liệu giả lập (Site, Zone, Cổng vào, Cổng ra, Thẻ RFID kích hoạt) qua HTTP client.
2. Thiết lập song song 2 kết nối WebSocket độc lập tới Gateway đóng vai:
   - Một Web Dashboard (xác thực bằng JWT token).
   - Một Device Agent (xác thực bằng Agent token).
3. Mô phỏng Device Agent gửi event quẹt thẻ `card.scanned` cho Check-In.
4. Kiểm tra sự kiện được truyền tải qua Redis Stream tới API, cập nhật DB và phát lại lên Pub/Sub để Web Dashboard nhận được đúng gói tin `parking.checkin.created` có trạng thái `active`.
5. Tiếp tục gửi quẹt thẻ ở cổng ra, kiểm tra Web Dashboard nhận được `parking.checkout.completed` có trạng thái `completed` và mức phí đã tính là `0.0`.

### B. Kết quả thực thi test
Đã thực thi toàn bộ test suite (gồm cả test của Phase 2 và Phase 3) bên trong container:
```bash
docker compose exec -T -e PYTHONPATH=. parking-api pytest test/
```

Kết quả:
```text
============================= test session starts ==============================
platform linux -- Python 3.10.20, pytest-9.1.0, pluggy-1.6.0
rootdir: /app
plugins: anyio-4.14.0
collected 5 items

test/02_core_api_e2e_test.py .                                           [ 20%]
test/02_core_api_pricing_test.py ...                                     [ 80%]
test/03_gateway_eventbus_integration_test.py .                           [100%]
============================== 5 passed in 0.54s ===============================
```

Tất cả 5 bài test đều vượt qua thành công, chứng tỏ luồng xử lý realtime hoạt động ổn định và có hiệu năng cao.
