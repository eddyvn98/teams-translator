from PyQt5.QtCore import QPoint, QSize, Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

try:
    from src_minimal.ui.icons import get_svg_icon, make_icon_button
except ImportError:
    from src.ui.icons import get_svg_icon, make_icon_button


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
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(6)

        self.status_dot = QLabel()
        self.status_dot.setObjectName("statusDot")
        self.status_dot.setFixedSize(8, 8)
        layout.addWidget(self.status_dot)

        # 2026 Minimalist icon buttons (No text)
        self.pause_btn = make_icon_button(
            "play",
            "Tiếp tục thu âm / dịch (Resume)",
            self._on_pause_resume_clicked,
            color="#ffffff",
            btn_size=32,
            icon_size=15,
            object_name="primaryButton",
            parent=self.card
        )

        self.caption_btn = make_icon_button(
            "subtitles",
            "Bật / Tắt cửa sổ Caption (Ctrl+Shift+C)",
            self.app_ref._toggle_caption,
            color="#cbd5e1",
            btn_size=32,
            icon_size=16,
            object_name="toolButton",
            parent=self.card
        )

        self.input_btn = make_icon_button(
            "panel",
            "Mở bảng điều khiển dịch đầy đủ",
            self.app_ref._restore_main_panel,
            color="#cbd5e1",
            btn_size=32,
            icon_size=16,
            object_name="toolButton",
            parent=self.card
        )

        self.exit_btn = make_icon_button(
            "close",
            "Thoát ứng dụng",
            self.app_ref._quit,
            color="#cbd5e1",
            btn_size=32,
            icon_size=15,
            object_name="closeButton",
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
                background: rgba(15, 23, 42, 230);
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 20px;
            }
            #statusDot {
                background: #64748b;
                border-radius: 4px;
            }
            #primaryButton, #toolButton, #closeButton {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                padding: 0px;
            }
            #primaryButton:hover, #toolButton:hover {
                background: rgba(255, 255, 255, 0.16);
                border-color: rgba(255, 255, 255, 0.22);
            }
            #closeButton:hover {
                background: rgba(239, 68, 68, 0.85);
                border-color: #ef4444;
            }
            QToolTip {
                background: #0f172a;
                color: #f8fafc;
                border: 1px solid rgba(148, 163, 184, 0.3);
                border-radius: 6px;
                padding: 4px 8px;
                font: 600 11px "Segoe UI";
            }
            """
        )

    def sync_state(self, capturing: bool):
        self._capturing = capturing
        if capturing:
            self.pause_btn.setIcon(get_svg_icon("pause", color="#111827", size=15))
            self.pause_btn.setToolTip("Tạm dừng thu âm / dịch (Pause)")
            self.status_dot.setStyleSheet("background: #22c55e; border-radius: 4px;")
            self.pause_btn.setStyleSheet(
                "QPushButton { background: #f59e0b; border: 1px solid #fbbf24; border-radius: 10px; }"
                "QPushButton:hover { background: #fbbf24; }"
            )
        else:
            self.pause_btn.setIcon(get_svg_icon("play", color="#ffffff", size=15))
            self.pause_btn.setToolTip("Tiếp tục thu âm / dịch (Resume)")
            self.status_dot.setStyleSheet("background: #64748b; border-radius: 4px;")
            self.pause_btn.setStyleSheet(
                "QPushButton { background: #2563eb; border: 1px solid #3b82f6; border-radius: 10px; }"
                "QPushButton:hover { background: #1d4ed8; }"
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
