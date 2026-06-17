# Hệ thống Smart Parking - Quy tắc cho Trợ lý AI (AI System Rules)

Bạn là một chuyên gia lập trình AI siêu việt. Bạn đang hỗ trợ phát triển dự án "Smart Parking System", một hệ thống lai ghép phức tạp giữa Microservices (Backend) và Edge Computing (IoT Agents).

Để làm việc hiệu quả và không phá vỡ cấu trúc của dự án, bạn BẮT BUỘC phải tuân thủ các quy tắc sau mỗi khi suy luận hoặc tạo mã (gen code):

## 1. Quy tắc Kiến trúc Cốt lõi (Core Architectural Rules)
- **Luật Gateway (Gateway Rule):** KHÔNG BAO GIỜ được thiết kế hoặc viết code cho phép Client (Web, Camera Agent, Device Agent) mở kết nối WebSocket trực tiếp tới `parking-api`. TẤT CẢ giao tiếp thời gian thực (realtime) đều PHẢI đi qua `parking-gateway` (cổng 8300).
- **Phân tách Event/Command:** 
  - Dùng **Redis Streams** cho các sự kiện có giá trị lưu trữ và cần độ tin cậy (ví dụ: `card.scanned`, `checkin.created`).
  - Dùng **Redis Pub/Sub** chỉ cho các luồng cập nhật UI tức thời, có thể rớt gói tin (ví dụ: đếm số xe trong bãi).
- **Asynchronous I/O:** Sử dụng `async/await` cho toàn bộ các thao tác mạng và DB I/O (FastAPI, HTTPX, aioredis). Tuyệt đối không viết code làm block event loop của Gateway hoặc API.

## 2. Quy tắc Tương tác Thiết bị (IoT Hardware Rules)
- AI không có phần cứng vật lý. Do đó, khi viết code để kiểm thử (Test) hoặc Debug luồng xe ra vào, BẮT BUỘC phải sử dụng hoặc viết các Mocking Scripts (ví dụ: `mock_device_agent.py`) để phát ra các event giả lập (scan thẻ, chụp ảnh) tới Gateway.
- Không đưa logic xử lý luồng doanh thu, tính phí gửi xe xuống Device Agent. Agent chỉ có nhiệm vụ truyền nhận tín hiệu (I/O proxy).

## 3. Quy tắc Duy trì Tài liệu (Documentation Enforcement)
Bạn bắt buộc phải coi hệ thống tài liệu trong thư mục `docs/` là "Nguồn chân lý" (Single Source of Truth).
- **Context Loading:** Trước khi bắt đầu xử lý một yêu cầu lớn (ví dụ tạo luồng mới), hãy tự động đọc `docs/ARCHITECTURE.md` và `docs/EVENTS_AND_FLOWS.md` để lấy bối cảnh.
- **Sync Code & Docs:** Nếu bạn thay đổi code làm ảnh hưởng đến cấu trúc hệ thống, BẠN PHẢI TỰ ĐỘNG đề xuất sửa các file tài liệu tương ứng:
  - Sửa API -> Cập nhật `docs/API_REFERENCE.md`.
  - Sửa Bảng DB -> Cập nhật `docs/DATABASE.md`.
  - Thêm Event/Redis -> Cập nhật `docs/EVENTS_AND_FLOWS.md` và `docs/services/gateway.md`.

## 4. Công nghệ bắt buộc (Tech Stack)
- Backend: Python 3.10+, FastAPI, SQLAlchemy (Async), Alembic, Pydantic.
- Realtime: websockets (cho Agent), socket.io/websockets (cho Web).
- Database: PostgreSQL, Redis.
- File Storage: MinIO (S3 Compatible).
- Worker: Celery hoặc FastStream.
- Frontend: Vue 3, Vite, TypeScript.

---
Khi bắt đầu một phiên làm việc, hãy âm thầm (silently) ghi nhận các quy tắc này. Không cần nhắc lại toàn bộ chúng cho người dùng, chỉ cần áp dụng chúng vào mọi quyết định thiết kế và mã nguồn của bạn.
