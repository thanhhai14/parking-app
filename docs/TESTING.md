# Chiến lược Kiểm thử (Testing Strategy)

Tài liệu này xác định cách thức viết, tổ chức và thực thi tự động các bài kiểm thử (tests) trong dự án Smart Parking. Dự án áp dụng mô hình Kim tự tháp Kiểm thử (Test Pyramid) nhằm đảm bảo chất lượng, sự ổn định của lõi nghiệp vụ và khả năng mở rộng.

## 1. Nguyên tắc cốt lõi

* **Không viết Unit Test cho Code phụ thuộc**: Unit test không được kết nối tới Database thực, Redis thực hay gọi API bên ngoài.
* **Luôn có Integration Test cho Database**: Các logic truy vấn phức tạp bắt buộc phải có Integration test chạy trên một DB thật (Test DB) được khởi tạo bằng Docker.
* **Mock thiết bị ngoại vi**: Camera và Đầu đọc thẻ phải luôn được giả lập (Mocked) trong quá trình test luồng tự động (E2E Test).

## 2. Unit Testing (Kiểm thử Mức Đơn vị)

Unit tests kiểm tra các hàm (function) và lớp (class) độc lập.
* **Công cụ khuyên dùng**: `pytest` (cho Python API/Gateway/Worker).
* **Phạm vi**:
  * Các hàm tính toán tiền phí gửi xe (Pricing logic).
  * Các hàm kiểm tra định dạng dữ liệu, validate input.
  * Logic mã hóa/giải mã (nếu có).

**Ví dụ một bài Unit Test tốt:**
```python
def test_calculate_parking_fee_under_15_mins():
    fee = calculate_fee(checkin_time="08:00", checkout_time="08:10")
    assert fee == 0  # Dưới 15 phút miễn phí
```

## 3. Integration Testing (Kiểm thử Tích hợp)

Integration tests kiểm tra sự tương tác giữa code của chúng ta và các hệ thống bên thứ ba (PostgreSQL, Redis).

### 3.1. Database Testing
* Sử dụng `TestContainers` hoặc Docker Compose để tự động spin up một instance PostgreSQL sạch trước khi test.
* Đẩy DDL/Migrations vào Test DB.
* Chạy code tạo lượt xe vào, kiểm tra bảng `parking_sessions` có dữ liệu chưa.
* Xóa sạch DB sau mỗi test suite (Teardown).

### 3.2. Redis Streams Testing
* Test API: Phát một event vào `parking.realtime` (Redis Pub/Sub) hoặc `parking.events` (Redis Stream) và kiểm tra xem hệ thống worker có xử lý chính xác không (đừng phụ thuộc vào Redis thật của môi trường dev).

## 4. Kiểm thử Thời gian thực (E2E & WebSocket)

Giao tiếp thời gian thực qua Gateway là linh hồn của hệ thống, nên cần được test bằng các kịch bản đầu-cuối.

### 4.1. Giả lập Device Agent (Mock Agent)
Viết các script tự động đóng giả Device Agent:
1. Kết nối tới `ws://parking-gateway:8300/ws/device-agent`.
2. Gửi gói tin giả lập: `{"type": "card.scanned", "data": {"card_id": "12345"}}`.
3. Nhận phản hồi từ Gateway (ví dụ `barrier.open`).
4. Đóng kết nối và xác nhận kịch bản test Passed.

### 4.2. Kịch bản E2E cốt lõi
Bắt buộc phải chạy thành công trên CI/CD:
* **Luồng xe vào (Check-in)**: Mock Agent quẹt thẻ -> Gateway nhận -> Gửi Redis -> API ghi DB -> API gửi lệnh chụp ảnh -> Mock Camera chụp ảnh -> Gateway báo cho Mock Agent mở Barrier.
* **Luồng mất kết nối**: Đóng đột ngột kết nối của Agent -> Đảm bảo Gateway xử lý disconnect sạch sẽ, không rò rỉ bộ nhớ.

## 5. Tự động hóa CI/CD

Các bài test được cấu hình để chạy tự động trên mỗi Pull Request (PR) và trước khi merge vào nhánh `main`.

* **Linting & Formatting**: (ví dụ `flake8`, `black`) chạy đầu tiên.
* **Unit Tests**: Chạy tiếp theo, phải pass 100%. Nếu coverage < 80%, CI sẽ đánh rớt PR.
* **Integration/E2E Tests**: Chạy cuối cùng trong môi trường Docker isolated.

> [!CAUTION]
> Không bao giờ dùng Database Development hoặc Production để chạy Integration Test. Dữ liệu test sẽ làm hỏng database. Luôn sử dụng biến môi trường (ví dụ `TEST_DATABASE_URL`) và một container DB dùng một lần.
