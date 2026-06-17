# Khôi phục Thảm họa & Sao lưu (Disaster Recovery & Backup)

Tài liệu này vạch ra các quy trình bảo vệ dữ liệu và các kịch bản phục hồi khi hệ thống gặp sự cố nghiêm trọng (Server vật lý hỏng, Xóa nhầm dữ liệu, Mất kết nối diện rộng).

## 1. Mục tiêu Khôi phục
Hệ thống Smart Parking được thiết kế với mục tiêu:
* **RPO (Recovery Point Objective)**: Tối đa 1 giờ (Chỉ mất dữ liệu nhiều nhất của 1 giờ qua).
* **RTO (Recovery Time Objective)**: Dưới 30 phút để dựng lại toàn bộ cụm Server và khôi phục dịch vụ cơ bản.

## 2. Chiến lược Sao lưu (Backup Strategy)

### 2.1. PostgreSQL (Dữ liệu quan trọng nhất)
Database chứa toàn bộ vé xe, thông tin khách hàng và lịch sử thu tiền.
* **Cronjob pg_dump**: Chạy mỗi giờ một lần (`pg_dump -Fc`), xuất ra một file nén.
* **WAL Archiving (Tùy chọn)**: Nếu RPO cần bằng 0 (không mất giao dịch nào), bật tính năng Ghi nhật ký Giao dịch (Write-Ahead Logging) và đồng bộ liên tục lên S3 Storage.
* **Lưu trữ Off-site**: File sao lưu KHÔNG được để trên cùng một Server. Một worker sẽ tự động đẩy file backup .dump lên AWS S3, Google Cloud Storage, hoặc một Server NAS dự phòng mỗi đêm.

### 2.2. Redis (Dữ liệu hàng đợi & Caching)
Mặc dù Redis chủ yếu dùng làm bộ đệm và Pub/Sub, ta dùng Redis Streams cho Event Bus nên cần đảm bảo không mất event nếu Redis crash.
* **Cấu hình AOF (Append Only File)**: Bật AOF với chế độ `appendfsync everysec` để đảm bảo event được ghi xuống đĩa mỗi giây.
* **RDB Snapshots**: Chụp ảnh nhanh Redis DB mỗi 15 phút một lần để có thể khởi động lại nhanh chóng.

## 3. Quy trình Phục hồi (Restore Procedures)

Trong trường hợp rủi ro xấu nhất (Server vật lý cháy nổ, phải thuê Server mới hoàn toàn):

### Bước 1: Dựng hạ tầng cơ bản (Phút 0 - Phút 10)
1. Provision một VPS/Server mới.
2. Clone repository code: `git clone <repo_url> /app/parking-app`.
3. Cài đặt Docker và Docker Compose.
4. Tải file `.env.production` từ trình quản lý mật khẩu của team (VD: Bitwarden, AWS Secrets Manager) vào Server.

### Bước 2: Khôi phục Database (Phút 10 - Phút 20)
1. Chỉ khởi động database container: `docker-compose up -d postgres`.
2. Tải file backup mới nhất từ S3 về Server: `aws s3 cp s3://parking-backup/db-2026-06-17.dump ./`.
3. Khôi phục dữ liệu:
   ```bash
   docker exec -i parking_postgres pg_restore -U user -d parking_db < db-2026-06-17.dump
   ```

### Bước 3: Chạy lại toàn bộ hệ thống (Phút 20 - Phút 30)
1. Khởi động các container còn lại: `docker-compose up -d`.
2. Hệ thống Redis khởi động và tự tải file AOF từ Volume.
3. Các Device/Camera Agent ở bãi xe tự động kết nối lại vào `parking-gateway`. Hệ thống hoạt động bình thường.

## 4. Xử lý "Split Brain" hoặc mất đồng bộ
Trong tình huống bãi xe mất mạng Internet nhiều ngày, Gateway không nhận được dữ liệu. Khi có mạng lại, Device Agent sẽ dồn toàn bộ ảnh chụp và log cục bộ lên Gateway cùng một lúc (hàng ngàn request).
* **Gateway Rate Limiting**: Gateway phải giới hạn lượng request của mỗi Agent để tránh sập Server.
* **Worker Scaling**: Kubernetes/Docker Compose cần tự động tăng số lượng container của `parking-api` (hoặc `parking-worker`) lên nhiều lần để xử lý hàng đợi Redis nhanh chóng, sau đó hạ xuống.

> [!WARNING]
> Quy trình Phục hồi cần được diễn tập (Dry-run) ít nhất 3 tháng 1 lần trên một Test Server độc lập để đảm bảo các file Backup thực sự hoạt động và file `.env` còn chính xác.
