# Teams Translator - Real-time dịch Anh-Việt cho Microsoft Teams
# Ứng dụng Windows desktop

# Cấu trúc:
# main.py               - Entry point, system tray icon
# src/
#   translator.py        - Dịch Anh ↔ Việt (Google Translate)
#   speech_to_text.py    - Nhận dạng giọng nói (microphone)
#   text_to_speech.py    - Đọc to (loa)
#   teams_agent.py       - Teams integration (overlay, auto-type)
#   caption_window.py    - Cửa sổ caption nổi
#   config_manager.py    - Quản lý cấu hình
#   main_window.py       - Cửa sổ chính Settings
# resources/
#   icon.png             - Icon ứng dụng
