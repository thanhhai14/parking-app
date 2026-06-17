# Phase 1: Foundation (Hạ tầng & Lõi cơ bản)

Đây là giai đoạn đầu tiên của dự án Smart Parking. Mục tiêu là thiết lập xong nền móng cơ sở hạ tầng (Database, Message Broker) và dựng khung sườn cho dịch vụ lõi (`parking-api`).

## 1. Mục tiêu (Goals)
* Các thành viên trong team có thể gõ `docker-compose up -d` và chạy được đầy đủ Postgres, Redis, MinIO trên máy cá nhân.
* Có sẵn bộ khung (Boilerplate) cho REST API bằng FastAPI.
* Có sẵn hệ thống Xác thực (Authentication) cơ bản để các Phase sau có thể dùng bảo mật ngay từ đầu.

## 2. Checklist Công việc

### 2.1. Cấu hình Hạ tầng (Infrastructure)
- [ ] Khởi tạo thư mục dự án theo chuẩn Monorepo hoặc Multi-repo.
- [ ] Tạo file `.env.example` với các thông số cấu hình mặc định.
- [ ] Tạo file `docker-compose.yml` định nghĩa các container:
  - `postgres` (port 5432)
  - `redis` (port 6379)
  - `minio` (port 9000)
- [ ] Viết script hoặc Makefile để khởi tạo nhanh (VD: `make dev`).

### 2.2. Khởi tạo `parking-api`
- [ ] Tạo thư mục `api/` và file `main.py` chạy FastAPI.
- [ ] Thiết lập kết nối Async tới PostgreSQL thông qua `SQLAlchemy` (AsyncEngine).
- [ ] Thiết lập công cụ Migration cơ sở dữ liệu (`Alembic`). Chạy lệnh `alembic init` thành công.
- [ ] Tích hợp Logging cơ bản (JSON format).

### 2.3. Base Auth & Users Domain
- [ ] Tạo model SQLAlchemy: `users` và `roles`.
- [ ] Tạo Alembic migration đầu tiên tạo bảng `users`.
- [ ] Viết API `/auth/login` cấp phát **JWT Token**.
- [ ] Viết Middleware/Dependency trong FastAPI để bảo vệ các endpoint yêu cầu Auth (JWT validation).

## 3. Điều kiện Hoàn thành (Definition of Done - DoD)
* Hệ thống khởi chạy mượt mà trên môi trường Local thông qua Docker.
* Swagger UI hiển thị ở `http://localhost:8000/docs`.
* Gọi API đăng nhập bằng Postman trả về JWT Token hợp lệ.

> [!NEXT]
> Sau khi Phase 1 hoàn thành, hệ thống đã sẵn sàng kết nối CSDL và Auth, chuẩn bị bước sang **Phase 2: Xây dựng Nghiệp vụ Cốt lõi (Core Domain)**.
