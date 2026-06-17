# Phase 4: Edge Agents (Tích hợp Thiết bị Biên)

Trong Phase này, chúng ta sẽ code các dịch vụ (Agents) chạy trên máy tính bảo vệ (Edge PC) tại bãi xe. Các Agent này chịu trách nhiệm nối với phần cứng thật và duy trì đường dây tới Gateway.

## 1. Mục tiêu (Goals)
* Chạy thành công Device Agent giả lập (Mocking) và gửi tín hiệu quẹt thẻ đều đặn.
* Chạy thành công Camera Agent, lấy hình ảnh giả lập (hoặc RTSP thật nếu có) và đẩy lên Gateway.
* Xây dựng khả năng vượt tường lửa (NAT Traversal) thông qua WebSocket.

## 2. Checklist Công việc

### 2.1. Phát triển `device-agent`
- [ ] Tạo project Python chạy ở chế độ Terminal/Daemon.
- [ ] Tích hợp thư viện `websockets` (Async).
- [ ] Cấu hình cơ chế tự động kết nối lại (Auto-reconnect) khi rớt mạng.
- [ ] Viết Mock Plugin: Mô phỏng hành động quẹt thẻ mỗi 10 giây hoặc khi gọi lệnh qua terminal.
- [ ] Viết Logic Offline Queue: Nếu mất mạng, lưu sự kiện quẹt thẻ vào mảng/file tạm, có mạng đẩy lên hàng loạt.

### 2.2. Phát triển `camera-agent`
- [ ] Tạo project Python Terminal.
- [ ] Tích hợp thư viện `OpenCV` để đọc frame từ RTSP (hoặc video mp4 giả lập).
- [ ] Kết nối WebSocket lên Gateway.
- [ ] Khi nhận được lệnh `snapshot.request` từ Gateway, chụp frame gần nhất, upload thẳng lên MinIO thông qua Presigned URL (do Gateway cấp) hoặc qua API upload của Phase 2.

### 2.3. Tích hợp Backend & Edge
- [ ] Bổ sung luồng API (Consumer): Sau khi xe vào -> API bắn command `barrier.open` vào Pub/Sub.
- [ ] Gateway nhận lệnh -> Tìm đúng WebSocket connection của Barrier đó -> Bắn qua WS.
- [ ] `device-agent` nhận lệnh mở Barrier và in ra log `[BARRIER OPENED]`.

## 3. Điều kiện Hoàn thành (Definition of Done - DoD)
* Bật 2 màn hình Terminal chạy Agent.
* Không dùng tay gọi HTTP Postman nữa. Chỉ thao tác trên terminal Agent: Bấm phím để "Scan thẻ".
* Tự động thấy luồng hoàn chỉnh: Thẻ -> Gateway -> Redis -> API (Lưu DB) -> Xin lệnh chụp ảnh -> Camera Agent chụp & up ảnh -> API mở Barrier -> Device Agent nhận lệnh mở. Mọi thứ trong dưới 500ms.

> [!NEXT]
> Phần lõi hệ thống đã hoạt động tự động hoàn toàn. Chuyển sang **Phase 5: Giao diện Quản trị Web (Frontend)** để hiển thị trực quan cho người dùng.
