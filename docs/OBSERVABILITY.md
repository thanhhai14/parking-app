# Observability & Monitoring

Tài liệu này hướng dẫn cách thiết lập, giám sát và vận hành hệ thống Smart Parking, đảm bảo hệ thống hoạt động ổn định và có thể phát hiện, xử lý lỗi nhanh chóng.

## 1. Tổng quan Kiến trúc Giám sát

Hệ thống sử dụng các công cụ chuẩn ngành cho việc giám sát:
* **Metrics & Monitoring:** Prometheus (thu thập metrics) và Grafana (hiển thị Dashboard).
* **Logging Tập trung:** ELK Stack (Elasticsearch, Logstash, Kibana) hoặc EFK Stack (Fluentd).
* **Distributed Tracing:** Jaeger (theo dõi request xuyên suốt qua Gateway, Redis, API).
* **Alerting:** Alertmanager (gắn với Prometheus) gửi cảnh báo qua Telegram/Slack.

## 2. Metrics & Dashboards

### 2.1. Prometheus
Tất cả các service (API, Gateway) đều phơi bày một endpoint `/metrics` theo định dạng Prometheus.
* **`parking-api`**: Thu thập thông tin về số lượng request HTTP, độ trễ, số lượng event đã xử lý từ Redis Streams.
* **`parking-gateway`**: Thu thập số lượng kết nối WebSocket đang hoạt động, tỷ lệ rớt kết nối, và độ trễ Ping/Pong.

Cấu hình mẫu `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'parking-api'
    static_configs:
      - targets: ['parking-api:8000']
  - job_name: 'parking-gateway'
    static_configs:
      - targets: ['parking-gateway:8300']
```

### 2.2. Grafana Dashboards
Các Dashboard quan trọng cần thiết lập trong Grafana:
1. **System Health**: CPU, RAM của các container.
2. **WebSocket Connections**: Số lượng Device Agent / Camera Agent đang online.
3. **Queue Size**: Độ dài của Redis Streams (nếu hàng đợi tăng liên tục, chứng tỏ Worker/API đang xử lý không kịp).

## 3. Logging Tập trung (Centralized Logging)

Mọi container trong hệ thống đẩy log về một hub trung tâm. Không đọc log trực tiếp bằng `docker logs` trên production.

### 3.1. Định dạng Log
Sử dụng định dạng **JSON** để dễ dàng phân tích và tìm kiếm.
Mỗi dòng log tối thiểu cần có các trường:
```json
{
  "timestamp": "2026-06-17T09:00:00Z",
  "level": "INFO",
  "service": "parking-gateway",
  "request_id": "req-12345",
  "message": "Device Agent kết nối thành công",
  "device_id": "cam-in-01"
}
```

### 3.2. Truy vết Request (Correlation ID)
Để theo dõi vòng đời của một sự kiện (ví dụ: thẻ quét -> camera chụp -> lưu DB -> gửi Web), hệ thống sử dụng `request_id` (hoặc `correlation_id`).
* `parking-gateway` sinh `request_id` ngay khi nhận event từ Device.
* `request_id` được gắn vào Redis Streams.
* `parking-api` lấy event từ Redis, khi ghi log luôn kèm theo `request_id` này.

## 4. Hệ thống Cảnh báo (Alerting)

Thiết lập Alertmanager để chủ động nhận thông báo khi có sự cố, thay vì đợi khách hàng báo cáo.

### 4.1. Các rule cảnh báo mức Độ Critical (Gọi điện/Nhắn tin khẩn)
* **API/Gateway Down**: Nếu Prometheus không thể scrape `/metrics` của API hoặc Gateway trong 1 phút.
* **Redis Disconnected**: Khi API không thể kết nối tới Redis.
* **Database Deadlock/Timeout**: Các query tới PostgreSQL mất hơn 5 giây.

### 4.2. Các rule cảnh báo mức Độ Warning (Thông báo Slack/Telegram)
* **Agent Offline**: Nếu số lượng Device/Camera kết nối qua WebSocket giảm đột ngột (ví dụ < 90% tổng số thiết bị đã đăng ký).
* **Redis Stream Lag**: Hàng đợi chưa xử lý (pending messages) vượt quá 1000.
* **High Memory Usage**: Container sử dụng trên 80% RAM cấp phát.

## 5. Health Checks
Mỗi service tự phơi bày endpoint `/health` để Docker/Kubernetes biết service còn sống hay đã "treo".

* **Đường dẫn**: `GET /health`
* **Response**:
  ```json
  {
    "status": "up",
    "dependencies": {
      "database": "up",
      "redis": "up"
    }
  }
  ```

> [!TIP]
> Luôn cấu hình `healthcheck` trong `docker-compose.yml` dựa vào endpoint này để Docker tự khởi động lại container khi service treo.
