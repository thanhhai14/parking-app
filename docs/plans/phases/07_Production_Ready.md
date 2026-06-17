# Phase 7: Production Ready (Tối ưu & Đóng gói triển khai)

Giai đoạn cuối cùng trước khi bàn giao hệ thống cho khách hàng sử dụng thực tế. 

## 1. Mục tiêu (Goals)
* Hệ thống hoạt động trơn tru 24/7 không rò rỉ bộ nhớ (memory leak).
* Chống chịu được lỗi mất kết nối mạng.
* Đạt điểm 100% về độ bao phủ Test cho các chức năng liên quan đến Tiền bạc (Billing).

## 2. Checklist Công việc

### 2.1. Kiểm thử Toàn diện (Testing & QA)
- [ ] Viết Automation E2E Test bằng Script Python hoặc Cypress/Playwright cho toàn bộ luồng Web.
- [ ] Kiểm tra Stress Test cho `parking-gateway` (Giả lập 10,000 agents kết nối cùng lúc).
- [ ] Giả lập tình huống sập Database hoặc đứt cáp mạng: Chắc chắn Offline Queue của Device Agent giữ lại thông tin và đẩy bù lên Cloud khi có mạng.

### 2.2. Giám sát & Logs (Observability)
- [ ] Cấu hình Prometheus cào (scrape) `/metrics` từ API và Gateway.
- [ ] Cấu hình Grafana Dashboard hiển thị: Số lượng xe ra vào, Lượng RAM/CPU tiêu thụ, Lượng thẻ rác chưa thanh toán.
- [ ] Gắn cơ chế Alerting: Báo qua Telegram cho Admin nếu Camera Agent nào đó ngắt kết nối quá 5 phút.

### 2.3. Triển khai Môi trường thật (Deployment)
- [ ] Chỉnh sửa `docker-compose.prod.yml` để sử dụng `.env.production`.
- [ ] Triển khai Nginx làm Reverse Proxy.
- [ ] Cài đặt chứng chỉ SSL/TLS bằng Certbot (Let's Encrypt) để bảo mật WebSocket (`wss://`) và HTTPS.
- [ ] Phân quyền lại thư mục chạy trên Linux Server (không chạy bằng user `root`).

### 2.4. Bàn giao
- [ ] Gửi hệ thống tài liệu `docs/` cho đội vận hành.
- [ ] Chạy Backup Database thử và phục hồi.

## 3. Điều kiện Hoàn thành (Definition of Done - DoD)
* Hệ thống live thành công qua tên miền.
* Bảng điều khiển Grafana có màu xanh.
* Không có Bug Critical nào xuất hiện trong 3 ngày Dry-run (Chạy thử nghiệm).

---
**🎉 CHÚC MỪNG: DỰ ÁN SMART PARKING ĐÃ HOÀN THÀNH 🎉**
