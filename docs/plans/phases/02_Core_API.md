# Phase 2: Core API (Nghiệp vụ Cốt lõi)

Giai đoạn này tập trung vào việc định nghĩa và xây dựng các bảng dữ liệu (Database Schema) liên quan đến nghiệp vụ bãi đỗ xe và các RESTful API phục vụ thao tác CRUD. Trong Phase này, **tất cả API chỉ gọi bằng HTTP thông thường**, chưa tích hợp Realtime/EventBus.

## 1. Mục tiêu (Goals)
* Hoàn thành thiết kế toàn bộ cấu trúc CSDL cho bãi xe.
* Các API REST cơ bản hoạt động ổn định (Tạo xe, Tạo vé, Phân quyền thiết bị).
* Xây dựng xong logic tính toán tiền gửi xe (Pricing Engine).

## 2. Checklist Công việc

### 2.1. Cấu trúc CSDL (Database Schema)
Tạo Alembic Migration và SQLAlchemy Models cho các bảng sau:
- [ ] Bảng `vehicles`: Lưu thông tin xe (biển số, màu sắc, loại xe).
- [ ] Bảng `cards`: Thẻ RFID (Mã UID, trạng thái kích hoạt, loại vé ngày/tháng).
- [ ] Bảng `devices`: Đầu đọc thẻ, Barrier (ID tĩnh để cấp Agent Token sau này).
- [ ] Bảng `cameras`: Camera LPR/Snapshot (IP, thông số cấu hình RTSP).
- [ ] Bảng `parking_sessions`: Bảng **cốt lõi** lưu lượt xe ra/vào (check-in time, check-out time, fee, status).

### 2.2. CRUD APIs
Viết các endpoint quản lý danh mục (dành cho Admin/Web):
- [ ] `GET/POST /api/v1/vehicles`
- [ ] `GET/POST /api/v1/cards`
- [ ] `GET/POST /api/v1/devices`
- [ ] `GET/POST /api/v1/cameras`

### 2.3. Logic Nghiệp vụ (Check-in / Check-out Mock API)
Viết các endpoint giả lập việc check-in, check-out qua HTTP (chưa dùng Event Bus):
- [ ] `POST /api/v1/parking/checkin`: Tạo session mới khi quẹt thẻ.
- [ ] `POST /api/v1/parking/checkout`: Cập nhật session khi xe ra.
- [ ] Viết Service tính giá tiền (`pricing_service.py`): Tính phí dựa trên giờ vào/ra, miễn phí dưới 15 phút, chặn vé tháng hết hạn.

### 2.4. File Upload (Media)
- [ ] Viết API `POST /api/v1/media/upload`: Nhận file ảnh từ client, lưu lên MinIO.
- [ ] Trả về presigned-url hoặc public link của ảnh.

## 3. Điều kiện Hoàn thành (Definition of Done - DoD)
* Dùng Postman có thể tạo luồng tạo thẻ -> gọi API checkin -> trả về thành công -> gọi API checkout -> trả về số tiền đúng.
* Đã có Unit Test bao phủ 100% hàm `pricing_service.py`.

> [!NEXT]
> Sau khi Core API đã định hình cấu trúc dữ liệu chuẩn, chúng ta sẽ chuyển sang **Phase 3: Xây dựng Xương sống Thời gian thực (Gateway & EventBus)**.
