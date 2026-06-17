# Lộ trình Phát triển Hệ thống (Development Phases)

Khu vực này lưu trữ các tài liệu chia nhỏ vòng đời phát triển của dự án Smart Parking.
Team phát triển cần đánh dấu Checklist trong các file này để theo dõi tiến độ.

## Các Giai đoạn (Phases)

| Giai đoạn | Tên Giai Đoạn | Mô tả | Trạng thái |
|---|---|---|---|
| Phase 1 | [Foundation](./phases/01_Foundation.md) | Xây dựng Base project, Database, Docker, Auth | Chưa bắt đầu |
| Phase 2 | [Core API](./phases/02_Core_API.md) | Xây dựng CRUD, Logic giá tiền, cấu trúc DB đỗ xe | Chưa bắt đầu |
| Phase 3 | [Gateway & EventBus](./phases/03_Gateway_EventBus.md) | Dựng WebSocket, Redis Streams cho CQRS Pattern | Chưa bắt đầu |
| Phase 4 | [Edge Agents](./phases/04_Edge_Agents.md) | Tích hợp code chạy ở máy tính bảo vệ, Camera, Hardware | Chưa bắt đầu |
| Phase 5 | [Web Frontend](./phases/05_Web_Frontend.md) | Giao diện cho Admin và Bảo vệ, Realtime dashboard | Chưa bắt đầu |
| Phase 6 | [AI Workers](./phases/06_AI_Workers.md) | Worker nền tự động đọc biển số xe ALPR/OCR | Chưa bắt đầu |
| Phase 7 | [Production Ready](./phases/07_Production_Ready.md) | Giám sát, HTTPS, Test tự động, Đóng gói bàn giao | Chưa bắt đầu |

> [!TIP]
> Hãy đi từ **Phase 1 đến Phase 7** theo đúng thứ tự để không bị kẹt ở khâu thiết kế dữ liệu. Mỗi khi team bắt đầu code, hãy vào đây check lại các hạng mục công việc.
