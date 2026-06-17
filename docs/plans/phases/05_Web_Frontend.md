# Phase 5: Web Frontend (Giao diện Quản trị)

Phase xây dựng mặt tiền của hệ thống cho các Bác bảo vệ, Quản lý bãi xe thao tác hằng ngày. 

## 1. Mục tiêu (Goals)
* Hoàn thiện bộ giao diện bằng Vue 3 + TailwindCSS.
* Bảng điều khiển (Dashboard) cập nhật số liệu theo thời gian thực không cần tải lại trang.
* Màn hình Check-in / Check-out trực quan cho bảo vệ đối chiếu hình ảnh.

## 2. Checklist Công việc

### 2.1. Thiết lập Project
- [ ] Khởi tạo `npm create vite@latest web -- --template vue-ts`.
- [ ] Cài đặt TailwindCSS, Vue Router, Pinia (State Management).
- [ ] Thiết lập Axios để gọi HTTP REST tới `parking-api`.
- [ ] Xây dựng màn hình Login và lưu JWT vào LocalStorage.

### 2.2. Kết nối Thời gian thực
- [ ] Cài đặt thư viện WebSocket/Socket.io client.
- [ ] Khởi tạo file `websocket.ts` (như trong thiết kế `services/web.md`) để duy trì kết nối với `parking-gateway:8300`.
- [ ] Lưu các Event (`checkin.created`, `checkout.completed`) vào Pinia Store.

### 2.3. Xây dựng Màn hình
- [ ] **Màn hình Danh mục**: Quản lý thẻ, Quản lý Xe vé tháng, Quản lý thông tin thiết bị (CRUD qua API Phase 2).
- [ ] **Màn hình Làn Xe (Lane Monitor)**: Chia đôi màn hình (Làn vào / Làn ra).
  - Khi xe quẹt thẻ ở cổng, Gateway bắn event -> Web tự động hiển thị popup thông tin biển số và hình ảnh xe.
  - Có nút "Mở thủ công" để quản lý gọi API kích hoạt barrier.
- [ ] **Màn hình Báo cáo**: Hiển thị bảng dữ liệu lịch sử xe ra vào.

## 3. Điều kiện Hoàn thành (Definition of Done - DoD)
* Login thành công vào Dashboard.
* Khi chạy song song `device-agent` để quẹt thẻ, giao diện Web sẽ "nháy" sáng và tự động đẩy thông tin một dòng xe cộ lên màn hình mà không cần ấn F5.
* Giao diện Responsive hoạt động tốt trên màn hình máy tính bảng của bảo vệ.

> [!NEXT]
> Hệ thống về cơ bản đã hoàn chỉnh và sử dụng được cho bãi xe thông thường. Tiếp theo sẽ gắn "não bộ" nhận diện tự động trong **Phase 6: AI Workers**.
