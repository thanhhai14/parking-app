# Hướng dẫn Môi trường Phát triển (Local Development)

Tài liệu này giúp lập trình viên mới gia nhập dự án có thể cấu hình và chạy hệ thống Smart Parking trên máy cá nhân một cách nhanh chóng nhất.

## 1. Yêu cầu Hệ thống (Prerequisites)

Máy tính của bạn cần cài đặt sẵn:
1. **Docker & Docker Compose**: Để chạy Postgres, Redis và các container.
2. **Python 3.10+**: Để phát triển API, Gateway, Worker và Agents.
3. **Node.js 18+ & npm**: Để phát triển Web Frontend (nếu có làm fullstack).
4. **Git**: Tải code từ repository.

## 2. Các Bước Cài đặt Nhanh (Quick Start)

### Bước 1: Clone dự án và chuẩn bị biến môi trường
Mở Terminal và chạy:
```bash
git clone <repository_url> parking-app
cd parking-app

# Copy file cấu hình mẫu thành cấu hình thật
cp .env.example .env
```
*(Nếu cần, hãy mở file `.env` để sửa đổi mật khẩu DB hoặc cổng mặc định).*

### Bước 2: Khởi chạy Hạ tầng (Database & Redis)
Bạn không cần (và không nên) cài đặt trực tiếp Postgres hay Redis lên máy mình. Dùng Docker Compose:
```bash
# Khởi chạy Postgres và Redis ở chế độ nền
docker-compose -f docker-compose.dev.yml up -d postgres redis

# Kiểm tra xem chúng đã chạy chưa
docker-compose ps
```

### Bước 3: Cài đặt thư viện Python
Nên sử dụng môi trường ảo (Virtual Environment):
```bash
python -m venv venv
source venv/bin/activate  # Trên Windows dùng: venv\Scripts\activate

# Cài đặt toàn bộ requirements cho hệ thống backend
pip install -r requirements.txt
```

### Bước 4: Chạy Migration (Khởi tạo DB)
```bash
# Giả sử dự án dùng Alembic
alembic upgrade head
```

## 3. Khởi chạy các Service để Code

Tùy vào bạn đang code phần nào, hãy mở các terminal khác nhau.

**Chạy API (HTTP REST):**
```bash
uvicorn api.main:app --reload --port 8000
```
API sẽ có mặt tại `http://localhost:8000`. Tài liệu Swagger tại `http://localhost:8000/docs`.

**Chạy Gateway (WebSocket):**
```bash
uvicorn gateway.main:app --reload --port 8300
```

## 4. Giả lập Thiết bị (Mocking Edge Agents)

Để test luồng realtime mà không có Camera thật hay Đầu đọc thẻ thật cắm vào máy, bạn khởi chạy Script giả lập (Mock Agents):

```bash
# Terminal 1: Chạy Device Agent giả lập
python scripts/mock_device_agent.py --gateway-url ws://localhost:8300

# Terminal 2: Phát sinh một sự kiện quẹt thẻ vào Agent
curl -X POST http://localhost:9001/trigger/scan_card -d '{"card_id": "123"}'
```

## 5. Xử lý Lỗi thường gặp (Troubleshooting)

1. **Lỗi `Address already in use` trên cổng 5432 hoặc 6379**
   * *Nguyên nhân*: Máy bạn đã cài Postgres/Redis trực tiếp từ trước.
   * *Khắc phục*: Tắt service cũ đi (`sudo systemctl stop postgresql`) hoặc vào file `.env` đổi `DB_PORT=5433` và sửa cổng map trong `docker-compose`.

2. **Lỗi `Connection refused` khi chạy API**
   * *Nguyên nhân*: API không tìm thấy Redis/Postgres.
   * *Khắc phục*: Đảm bảo bạn đã chạy Bước 2 (`docker-compose up -d`) và biến môi trường `DATABASE_URL`, `REDIS_URL` trỏ vào `localhost` thay vì tên container.

> [!TIP]
> Sử dụng phần mềm **DBeaver** hoặc **pgAdmin** để kết nối vào `localhost:5432` xem dữ liệu thực tế đang thay đổi như thế nào trong lúc code.
