# Báo cáo Kết quả Phase 4: Edge Agents (Tích hợp Thiết bị Biên)

Báo cáo này tóm tắt kết quả triển khai Phase 4, hoàn thành phát triển hai Edge Agents độc lập (`parking-device-agent` và `parking-camera-agent`), gieo dữ liệu thiết bị biên kết hợp với Cổng và nâng cấp `parking-api` event consumer thành State Machine bất đồng bộ xử lý luồng nghiệp vụ đầy đủ.

## 1. Các thành phần đã triển khai

### A. Tệp cấu hình YAML & Database Seeding
- Tạo tệp [config/device-agent.yaml](file:///home/thanhhai14/Data/Code/parking-app/config/device-agent.yaml) và [config/camera-agent.yaml](file:///home/thanhhai14/Data/Code/parking-app/config/camera-agent.yaml) để định nghĩa URL gateway, agent ID, token xác thực, heartbeat interval, và tệp queue offline.
- Tạo và thực thi thành công Alembic migration `eed5ee63ff9c_seed_devices_for_testing.py` gieo dữ liệu CSDL Postgres bao gồm:
  - 1 Site: `SITE-EDGE-01`
  - 1 Zone: `ZONE-EDGE-01`
  - 2 Gates: Cổng vào `GATE-IN-EDGE-01`, Cổng ra `GATE-OUT-EDGE-01`
  - 2 Cameras: `CAM-IN-EDGE-01`, `CAM-OUT-EDGE-01` (liên kết với agent `camera-agent-gate-01`)
  - 2 Devices (Barriers): `BARRIER-IN-EDGE-01`, `BARRIER-OUT-EDGE-01` (liên kết với agent `device-agent-gate-01`)
  - 1 Active RFID Card: `04A12345`

### B. Device Agent (`parking-device-agent`)
- Tạo dự án Python daemon độc lập chạy trong docker.
- Hỗ trợ auto-reconnect tự động kết nối lại WebSocket gateway sau mỗi 5 giây nếu mất mạng.
- Định kỳ gửi heartbeat `device.heartbeat` mỗi 30 giây.
- Lắng nghe command từ Gateway: Nhận lệnh `barrier.open.request` -> In ra log màn hình `[BARRIER OPENED]` -> Gửi lại event xác nhận `barrier.opened`.
- **Offline Queue (JSON file)**: Khi bị ngắt kết nối gateway, mọi event quẹt thẻ phát sinh sẽ tự động được ghi nhận vào file cục bộ `/app/data/offline_events.json`. Khi kết nối lại thành công, tự động đọc, gửi bù toàn bộ và xóa file đệm.
- Mô phỏng chạy ngầm: Tự động giả lập quẹt thẻ `04A12345` xen kẽ giữa cổng vào (check-in) và cổng ra (check-out) mỗi 20 giây để hệ thống tự vận hành.

### C. Camera Agent (`parking-camera-agent`)
- Tạo dự án Python daemon độc lập kết nối WebSocket gateway và gửi heartbeat.
- Lắng nghe command `camera.snapshot.request` gửi từ API qua Gateway:
  - Tự động login vào REST API của `parking-api` bằng tài khoản admin để lấy JWT token.
  - Sử dụng thư viện `Pillow` (PIL) để vẽ một ảnh bảng biển số mock có chứa biển số xe ngẫu nhiên hoặc biển số từ yêu cầu (ví dụ `30-F1 88888`).
  - Thực hiện HTTP POST tải file ảnh lên `/api/v1/media/upload` kèm header `Authorization: Bearer <JWT>`.
  - Nhận về `media_id` từ API và gửi lại sự kiện `camera.snapshot.completed` chứa `media_id` lên Gateway.

### D. Nâng cấp API Event Consumer thành State Machine
- Nâng cấp [apps/parking-api/services/event_consumer.py](file:///home/thanhhai14/Data/Code/parking-app/apps/parking-api/services/event_consumer.py) để triển khai luồng Check-In/Check-Out 2 bước bất đồng bộ chuẩn:
  1. **Bước 1 (card.scanned)**: Xác thực thẻ và cổng. Lưu trạng thái tạm (gồm card_uid, gate_code, plate_number, action checkin/checkout) vào **Redis Cache** với key `pending_session:{correlation_id}` (TTL 300s). Sau đó gửi command chụp ảnh `camera.snapshot.request` vào stream `parking.commands`.
  2. **Bước 2 (camera.snapshot.completed)**: Lấy trạng thái tạm từ Redis Cache theo `correlation_id`. Tiến hành nghiệp vụ check-in (tạo session mới) hoặc check-out (tính tiền, hoàn thành session) trong Postgres DB và gán ảnh xe `media_id`. Tiếp tục gửi command mở barrier `barrier.open.request` vào stream `parking.commands`. Xóa key Redis tạm và bắn realtime event lên kênh Pub/Sub `parking.realtime`.
- Đảm bảo idempotency chống xử lý trùng lặp qua bảng CSDL `processed_events`.

---

## 2. Kết quả Kiểm thử (Verification & Testing)

### A. Kịch bản test tự động
Chúng tôi đã viết tệp test tích hợp tại [test/04_edge_agents_integration_test.py](file:///home/thanhhai14/Data/Code/parking-app/test/04_edge_agents_integration_test.py) để giả lập toàn bộ môi trường chạy thật mà không dùng PIL (tránh dependencies trong API test runner, chỉ gửi dummy bytes làm ảnh):
1. Đăng nhập hệ thống, tạo một thẻ RFID động độc nhất cho test để tránh xung đột với simulator chạy ngầm.
2. Mở song song 3 WebSocket connections (Dashboard, Device Agent, Camera Agent).
3. Gửi sự kiện quẹt thẻ check-in -> Đợi Camera Agent nhận command `camera.snapshot.request` -> Camera Agent mock upload ảnh và trả về `camera.snapshot.completed` -> Đợi Device Agent nhận command `barrier.open.request` và gửi xác nhận -> Đợi Web Dashboard nhận sự kiện `parking.checkin.created`.
4. Làm tương tự cho check-out ở cổng ra -> Verify Web Dashboard nhận sự kiện `parking.checkout.completed` có status `completed` và calculated_fee = 0.0 VND.

### B. Kết quả thực thi test
Đã thực thi toàn bộ test suite (gồm cả test của Phase 2, 3 và 4) bên trong container:
```bash
docker compose exec -T -e PYTHONPATH=. parking-api pytest test/
```

Kết quả:
```text
============================= test session starts ==============================
platform linux -- Python 3.10.20, pytest-9.1.0, pluggy-1.6.0
rootdir: /app
plugins: anyio-4.14.0
collected 6 items

test/02_core_api_e2e_test.py .                                           [ 16%]
test/02_core_api_pricing_test.py ...                                     [ 66%]
test/03_gateway_eventbus_integration_test.py .                           [ 83%]
test/04_edge_agents_integration_test.py .                                [100%]
============================== 6 passed in 1.07s ===============================
```

Tất cả 6 bài test đều vượt qua thành công tốt đẹp, xác nhận sự chính xác và hiệu năng cao của cơ chế xử lý bất đồng bộ!
