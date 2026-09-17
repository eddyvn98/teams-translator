from PyQt5.QtCore import QPoint, QSize, Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

try:
    from src.ui.icons import get_svg_icon, make_icon_button
except ImportError:
    from src_minimal.ui.icons import get_svg_icon, make_icon_button


class FloatingControlWidget(QWidget):
    def __init__(self, app_ref):
        super().__init__(None)
        self.app_ref = app_ref
        self._drag_offset = QPoint()
        self._dragging = False
        self._capturing = False
        self.setWindowTitle("Teams Translator Controls")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._build_ui()
        self.adjustSize()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame(self)
        self.card.setObjectName("controlPill")
        layout = QHBoxLayout(self.card)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        # Drag grip dots
        self.grip_icon = QLabel()
        self.grip_icon.setObjectName("gripIcon")
        self.grip_icon.setPixmap(get_svg_icon("dots_grip", color="#64748b", size=15).pixmap(15, 15))
        self.grip_icon.setCursor(Qt.SizeAllCursor)
        layout.addWidget(self.grip_icon)

        # Blue soundwave logo
        self.wave_icon = QLabel()
        self.wave_icon.setObjectName("waveIcon")
        self.wave_icon.setPixmap(get_svg_icon("soundwave", color="#38bdf8", size=18).pixmap(18, 18))
        layout.addWidget(self.wave_icon)

        # Status indicator: dot + text
        self.status_dot = QLabel()
        self.status_dot.setObjectName("statusDot")
        self.status_dot.setFixedSize(7, 7)
        layout.addWidget(self.status_dot)

        self.status_text = QLabel("Listening")
        self.status_text.setObjectName("statusText")
        layout.addWidget(self.status_text)

        # Control buttons
        self.pause_btn = make_icon_button(
            "pause",
            "Tạm dừng thu âm / dịch (Pause)",
            self._on_pause_resume_clicked,
            color="#ffffff",
            btn_size=32,
            icon_size=15,
            object_name="pausePillButton",
            parent=self.card
        )

        self.caption_btn = make_icon_button(
            "cc",
            "Bật / Tắt cửa sổ Caption (Ctrl+Shift+C)",
            self.app_ref._toggle_caption,
            color="#cbd5e1",
            btn_size=32,
            icon_size=16,
            object_name="pillButton",
            parent=self.card
        )

        self.input_btn = make_icon_button(
            "expand",
            "Mở bảng điều khiển dịch đầy đủ",
            self.app_ref._restore_main_panel,
            color="#cbd5e1",
            btn_size=32,
            icon_size=15,
            object_name="pillButton",
            parent=self.card
        )

        self.exit_btn = make_icon_button(
            "close",
            "Thoát ứng dụng",
            self.app_ref._quit,
            color="#cbd5e1",
            btn_size=32,
            icon_size=14,
            object_name="pillCloseButton",
            parent=self.card
        )

        for button in [self.pause_btn, self.caption_btn, self.input_btn, self.exit_btn]:
            layout.addWidget(button)

        root.addWidget(self.card)
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(
            """
            #controlPill {
                background: rgba(10, 16, 30, 245);
                border: 1px solid rgba(56, 189, 248, 0.25);
                border-radius: 22px;
            }
            #statusDot {
                background: #22c55e;
                border-radius: 3px;
            }
            #statusText {
                color: #e2e8f0;
                font: 600 12px "Segoe UI";
                margin-right: 4px;
            }
            #pausePillButton {
                background: rgba(220, 38, 38, 0.28);
                border: 1px solid rgba(239, 68, 68, 0.55);
                border-radius: 10px;
                padding: 0px;
            }
            #pausePillButton:hover {
                background: rgba(239, 68, 68, 0.6);
                border-color: #ef4444;
            }
            #pillButton, #pillCloseButton {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 0px;
            }
            #pillButton:hover {
                background: rgba(255, 255, 255, 0.16);
                border-color: rgba(255, 255, 255, 0.25);
            }
            #pillCloseButton:hover {
                background: rgba(239, 68, 68, 0.85);
                border-color: #ef4444;
            }
            QToolTip {
                background: #0b1325;
                color: #f8fafc;
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 6px;
                padding: 4px 8px;
                font: 600 11px "Segoe UI";
            }
            """
        )

    def sync_state(self, capturing: bool):
        self._capturing = capturing
        if capturing:
            self.pause_btn.setIcon(get_svg_icon("pause", color="#ffffff", size=15))
            self.pause_btn.setToolTip("Tạm dừng thu âm / dịch (Pause)")
            self.status_dot.setStyleSheet("background: #22c55e; border-radius: 3px;")
            self.status_text.setText("Listening")
            self.pause_btn.setStyleSheet(
                "QPushButton { background: rgba(220, 38, 38, 0.35); border: 1px solid rgba(239, 68, 68, 0.6); border-radius: 10px; }"
                "QPushButton:hover { background: rgba(239, 68, 68, 0.65); }"
            )
        else:
            self.pause_btn.setIcon(get_svg_icon("play", color="#ffffff", size=15))
            self.pause_btn.setToolTip("Tiếp tục thu âm / dịch (Resume)")
            self.status_dot.setStyleSheet("background: #64748b; border-radius: 3px;")
            self.status_text.setText("Paused")
            self.pause_btn.setStyleSheet(
                "QPushButton { background: rgba(37, 99, 235, 0.35); border: 1px solid rgba(59, 130, 246, 0.6); border-radius: 10px; }"
                "QPushButton:hover { background: rgba(37, 99, 235, 0.65); }"
            )

    def _on_pause_resume_clicked(self):
        self.app_ref._toggle_capture()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_offset = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and (event.buttons() & Qt.LeftButton):
            self.move(event.globalPos() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            event.accept()
            return
        super().mouseReleaseEvent(event)
