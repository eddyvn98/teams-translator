from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget


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
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        self.status_dot = QLabel()
        self.status_dot.setObjectName("statusDot")
        self.status_dot.setFixedSize(9, 9)
        layout.addWidget(self.status_dot)

        self.pause_btn = self._make_button("Resume", "primaryButton", self._on_pause_resume_clicked)
        self.caption_btn = self._make_button("Caption", "toolButton", self.app_ref._toggle_caption)
        self.input_btn = self._make_button("Mở panel", "toolButton", self.app_ref._restore_main_panel)
        self.input_btn.setText("Mở panel")
        self.exit_btn = self._make_button("x", "closeButton", self.app_ref._quit)

        for button in [self.pause_btn, self.caption_btn, self.input_btn, self.exit_btn]:
            layout.addWidget(button)

        root.addWidget(self.card)
        self._apply_style()

    def _make_button(self, text: str, object_name: str, callback) -> QPushButton:
        button = QPushButton(text, self.card)
        button.setObjectName(object_name)
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(callback)
        return button

    def _apply_style(self):
        self.setStyleSheet(
            """
            #controlPill {
                background: rgba(15, 23, 42, 235);
                border: 1px solid rgba(148, 163, 184, 130);
                border-radius: 18px;
            }
            #statusDot {
                background: #64748b;
                border-radius: 4px;
            }
            #primaryButton, #toolButton, #closeButton {
                color: #e2e8f0;
                background: rgba(51, 65, 85, 190);
                border: 1px solid rgba(148, 163, 184, 80);
                border-radius: 12px;
                padding: 6px 10px;
                font: 700 11px "Segoe UI";
            }
            #primaryButton {
                min-width: 70px;
            }
            #primaryButton:hover, #toolButton:hover {
                background: rgba(71, 85, 105, 230);
            }
            #closeButton {
                min-width: 24px;
                padding-left: 7px;
                padding-right: 7px;
            }
            #closeButton:hover {
                background: #dc2626;
                border-color: #ef4444;
            }
            """
        )

    def sync_state(self, capturing: bool):
        self._capturing = capturing
        if capturing:
            self.pause_btn.setText("Pause")
            self.status_dot.setStyleSheet("background: #22c55e; border-radius: 4px;")
            self.pause_btn.setStyleSheet(
                "QPushButton { color: #111827; background: #f59e0b; border: 1px solid #fbbf24; "
                "border-radius: 12px; padding: 6px 10px; font: 800 11px 'Segoe UI'; min-width: 70px; }"
                "QPushButton:hover { background: #fbbf24; }"
            )
        else:
            self.pause_btn.setText("Resume")
            self.status_dot.setStyleSheet("background: #64748b; border-radius: 4px;")
            self.pause_btn.setStyleSheet(
                "QPushButton { color: white; background: #2563eb; border: 1px solid #3b82f6; "
                "border-radius: 12px; padding: 6px 10px; font: 800 11px 'Segoe UI'; min-width: 70px; }"
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
