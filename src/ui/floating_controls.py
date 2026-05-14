from PyQt5.QtWidgets import QWidget, QPushButton
from PyQt5.QtCore import Qt, QPoint


class DragButton(QPushButton):
    def __init__(self, text: str, owner_widget: "FloatingControlWidget"):
        super().__init__(text, owner_widget)
        self.owner_widget = owner_widget
        self._press_pos = QPoint()
        self._drag_started = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_pos = event.globalPos()
            self._drag_started = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            delta = event.globalPos() - self._press_pos
            if delta.manhattanLength() >= 6:
                self._drag_started = True
                self.owner_widget._dragging = True
                self.owner_widget._drag_offset = event.globalPos() - self.owner_widget.frameGeometry().topLeft()
                self.owner_widget.move(event.globalPos() - self.owner_widget._drag_offset)
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drag_started:
            event.accept()
            return
        super().mouseReleaseEvent(event)


class FloatingControlWidget(QWidget):
    def __init__(self, app_ref):
        super().__init__(None)
        self.app_ref = app_ref
        self._drag_offset = QPoint()
        self._dragging = False
        self.setWindowTitle("Teams Translator Controls")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._build_ui()
        self.resize(48, 48)

    def _build_ui(self):
        self.pause_btn = DragButton(">", self)
        self.pause_btn.setGeometry(0, 0, 44, 44)
        self.pause_btn.setCursor(Qt.PointingHandCursor)
        self.pause_btn.clicked.connect(self._on_pause_resume_clicked)
        self.pause_btn.setStyleSheet(
            "QPushButton { background: #1f6feb; color: white; border: 0; border-radius: 22px; font-size: 16px; font-weight: 700; }"
            "QPushButton:hover { background: #2f81f7; }"
        )

        self.exit_btn = QPushButton("x", self)
        self.exit_btn.setGeometry(30, -2, 18, 18)
        self.exit_btn.setCursor(Qt.PointingHandCursor)
        self.exit_btn.clicked.connect(self.app_ref._quit)
        self.exit_btn.setStyleSheet(
            "QPushButton { background: #da3633; color: white; border: 1px solid rgba(255,255,255,160); border-radius: 9px; font-size: 11px; font-weight: 700; padding: 0; }"
            "QPushButton:hover { background: #f85149; }"
        )

        self.setStyleSheet("background: transparent;")

    def sync_state(self, capturing: bool):
        if capturing:
            self.pause_btn.setText("||")
            self.pause_btn.setStyleSheet(
                "QPushButton { background: #f59e0b; color: #111; border: 0; border-radius: 22px; font-size: 14px; font-weight: 800; }"
                "QPushButton:hover { background: #fbbf24; }"
            )
        else:
            self.pause_btn.setText(">")
            self.pause_btn.setStyleSheet(
                "QPushButton { background: #1f6feb; color: white; border: 0; border-radius: 22px; font-size: 16px; font-weight: 700; }"
                "QPushButton:hover { background: #2f81f7; }"
            )

    def _on_pause_resume_clicked(self):
        self.app_ref._toggle_capture()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_offset = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and (event.buttons() & Qt.LeftButton):
            self.move(event.globalPos() - self._drag_offset)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)
