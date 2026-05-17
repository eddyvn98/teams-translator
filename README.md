# Teams Translator - Dịch Anh-Việt realtime cho Microsoft Teams

Ứng dụng desktop Windows hỗ trợ:
- Nghe loopback/micro
- Chuyển giọng nói thành văn bản
- Dịch Anh-Việt theo ngữ cảnh
- Hiển thị caption và hỗ trợ nhập phản hồi

## Cấu trúc chính
- `main.py`: entry point, khởi động app
- `src/translator.py`: dịch Anh ↔ Việt
- `src/speech_to_text.py`: nhận dạng giọng nói
- `src/text_to_speech.py`: phát âm phản hồi
- `src/teams_agent.py`: tích hợp luồng làm việc với Teams
- `src/caption_window.py`: cửa sổ caption nổi
- `src/config_manager.py`: quản lý cấu hình
- `src/ui/`: các thành phần giao diện
- `resources/icon.png`: biểu tượng ứng dụng

## Quy ước encoding
Tất cả file mã nguồn và tài liệu trong repo phải dùng UTF-8. Xem thêm hướng dẫn tại `docs/ENCODING.md`.
