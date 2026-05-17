# Hướng dẫn tránh mojibake (UTF-8)

## Nguyên nhân gốc
Mojibake xảy ra khi file được lưu bằng một encoding nhưng lại được đọc bằng encoding khác (thường gặp trên Windows khi editor/terminal dùng code page mặc định).

## Quy tắc bắt buộc trong dự án
- Tất cả file code/tài liệu phải lưu bằng `UTF-8`.
- Không lưu file bằng ANSI/Windows-1252/Windows-1258.
- Giữ `LF` để tránh nhiễu khi chạy script đa môi trường.

## Thiết lập khuyến nghị
- Repo đã có `.editorconfig` để ép `charset = utf-8`.
- Với VS Code: đặt `"files.encoding": "utf8"` và bật `"files.autoGuessEncoding": false`.
- Khi chạy Python trên Windows, ưu tiên terminal UTF-8:
  - PowerShell: `chcp 65001`
  - Biến môi trường: `PYTHONUTF8=1`

## Checklist trước khi commit
- Quét nhanh ký tự lỗi phổ biến:
  - `rg -n "Lá»|Ã|Â|â€" src test*.py README.md`
- Nếu phát hiện chuỗi lỗi, sửa ở **file gốc** (không chỉ sửa hiển thị terminal).
- Mở lại file sau khi lưu để xác nhận tiếng Việt có dấu hiển thị đúng.
