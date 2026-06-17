# Cẩm nang Hướng dẫn Trợ lý AI (AI Development Guide)

Tài liệu này được thiết kế làm **Ngữ cảnh hệ thống (System Context)** để cung cấp cho các công cụ AI CLI (như Codex CLI, GitHub Copilot CLI) hoặc các AI Agent khác trước khi chúng thực thi tác vụ trên dự án Smart Parking.

> **Dành cho Developer:** Khi bạn muốn giao việc cho Codex CLI, hãy gõ lệnh:
> `codex "Đọc docs/AI_GUIDE.md và docs/EVENTS_AND_FLOWS.md. Sau đó viết cho tôi luồng Check-in mới..."`

---

## 1. Mục tiêu của Dự án
Smart Parking là hệ thống phần mềm quản lý bãi xe vi mô, phân tán. Hệ thống tách biệt hoàn toàn thiết bị ở biên (Edge - bãi xe) và máy chủ trung tâm (Cloud/Core API) thông qua API Gateway và Event-Driven Architecture.

## 2. Các quy tắc "Sống còn" AI phải tuân thủ

Để giữ kiến trúc không bị vỡ nát do AI tự sinh code tùy tiện, AI phải áp dụng các bộ lọc sau:

### 2.1. Quy tắc kết nối WebSocket
Mọi luồng dữ liệu thời gian thực (Camera gửi ảnh realtime, Đầu đọc thẻ báo quẹt thẻ, Web theo dõi dashboard) **không bao giờ được phép** kết nối trực tiếp đến `parking-api`.
- Điểm đầu mối (Endpoint) duy nhất cho WebSocket là: `parking-gateway` (Port 8300).
- `parking-gateway` nhận WebSocket, sau đó đóng gói lại thành Event và đẩy vào **Redis Streams** hoặc **Redis Pub/Sub**.

### 2.2. Quy tắc chia nhỏ Event (CQRS pattern)
- **Stateful Events (Dữ liệu quan trọng, cần lưu, có thể retry):** Bắt buộc phải dùng `Redis Streams`. Ví dụ: Xe quẹt thẻ (`card.scanned`), Camera đã chụp xong ảnh (`snapshot.completed`).
- **Stateless Events (Dữ liệu tức thời, rớt mạng bỏ qua):** Bắt buộc dùng `Redis Pub/Sub`. Ví dụ: Bảng LED hiển thị số lượng chỗ trống, Web thông báo Notification chớp nhoáng.

### 2.3. Quy tắc Cập nhật Đồng bộ (Documentation First)
AI không chỉ là thợ code, AI là kỹ sư phần mềm.
Khi AI được yêu cầu: "Hãy viết code API mới để xử lý vé tháng", AI BẮT BUỘC phải làm 2 việc:
1. Viết code cho tính năng đó.
2. Chủ động sửa file `docs/API_REFERENCE.md` để thêm Document cho API vừa tạo mà không cần đợi con người nhắc nhở.

## 3. Kiến trúc Microservices Cốt lõi
AI cần ghi nhớ cấu trúc thư mục và dịch vụ sau để tìm đúng chỗ khi cần sửa code:
- `api/`: Thư mục chứa `parking-api` (HTTP REST).
- `gateway/`: Thư mục chứa `parking-gateway` (WebSocket Router).
- `worker/`: Thư mục chứa các tác vụ background nặng (OCR biển số xe).
- `device-agent/` & `camera-agent/`: Thư mục chứa code chạy trên máy tính cục bộ tại bãi xe, giao tiếp với phần cứng.
- `web/`: Thư mục Frontend (Vue 3).

## 4. Giao tiếp khi có sự cố
Nếu AI phát hiện một yêu cầu của lập trình viên đi ngược lại với kiến trúc trong tài liệu `ARCHITECTURE.md` (Ví dụ: Lập trình viên bắt AI mở port WebSocket thẳng vào `parking-api`), AI có trách nhiệm **cảnh báo và giải thích** lý do tại sao điều đó sai quy tắc, và đề xuất cách làm đúng (đẩy qua Gateway).
