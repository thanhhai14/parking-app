# Phase 6: AI Workers (Xử lý nền)

Giai đoạn tự động hóa bãi xe. Thay vì bảo vệ phải nhìn bằng mắt thường và bấm biển số bằng tay, hệ thống sẽ tự động đọc biển số xe thông qua các Worker chạy ngầm.

## 1. Mục tiêu (Goals)
* Tách biệt logic tốn CPU (Machine Learning / Computer Vision) ra khỏi `parking-api`.
* Có khả năng scale nhiều server Worker chạy độc lập để xử lý hàng ngàn ảnh cùng lúc nếu hệ thống lớn.
* Tích hợp thành công luồng sự kiện: Có ảnh -> Nhận diện -> Lưu DB.

## 2. Checklist Công việc

### 2.1. Cấu hình Hạ tầng Worker
- [ ] Khởi tạo dự án Python trong thư mục `worker/`.
- [ ] Tích hợp Celery hoặc thư viện xử lý Stream bất đồng bộ (như `FastStream`).
- [ ] Cho Worker lắng nghe Redis Stream `parking.events` (lọc lấy event `snapshot.completed`).

### 2.2. Nhận diện Biển số (ALPR Plugin)
- [ ] Cài đặt các thư viện AI mã nguồn mở (ví dụ: OpenALPR, PaddleOCR hoặc YOLOv8).
- [ ] Viết hàm `recognize_license_plate(image_path) -> string`.
- [ ] **Luồng chạy:**
  1. Worker nhận thông báo có xe vừa chụp ảnh xong.
  2. Worker gọi API lấy ảnh từ MinIO xuống.
  3. Đưa ảnh qua hàm nhận diện.
  4. Lấy được Text biển số (VD: `51G-12345`).
  5. Bắn event `alpr.completed` vào Redis.

### 2.3. Hậu xử lý tại Core API
- [ ] `parking-api` nghe thấy `alpr.completed`.
- [ ] Tìm Session đỗ xe tương ứng và cập nhật biển số xe vào Database.
- [ ] Bắn event báo màn hình Web tự động hiển thị biển số xe lên cho bảo vệ xác nhận.

## 3. Điều kiện Hoàn thành (Definition of Done - DoD)
* Xe quẹt thẻ -> Máy ảnh chụp -> Nhận diện xong -> Giao diện web báo số vé và Biển số xe khớp nhau dưới 2 giây.

> [!NEXT]
> Tất cả các thành phần chức năng đã xong. Tiến hành đóng gói và bảo mật ở **Phase 7: Production Ready**.
