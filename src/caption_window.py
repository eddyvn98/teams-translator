"""
Caption Window - hien thi lich su caption theo phien va khung AI tom tat.
"""
import logging
import datetime
from pathlib import Path
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication, QTextEdit
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QBrush

logger = logging.getLogger(__name__)


class CaptionWindow(QWidget):
    update_signal = pyqtSignal(dict)
    summary_signal = pyqtSignal(str)

    def __init__(self, config_manager=None, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self._history = []
        self._current_text = {"source": "", "translated": "", "lang": ""}
        self._history_dir = Path.home() / ".teams-translator" / "history"
        self._history_dir.mkdir(parents=True, exist_ok=True)
        self._session_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self._history_file = self._history_dir / f"session-{self._session_id}.log"
        self._summary_file = self._history_dir / f"session-{self._session_id}-summary.txt"

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self._setup_ui()
        self._load_position()

        self.update_signal.connect(self._on_update_text)
        self.summary_signal.connect(self._on_update_summary)

        self._fade_timer = QTimer()
        self._fade_timer.timeout.connect(self._check_fade)
        self._fade_timer.start(1000)
        self._idle_seconds = 0

        self._dragging = False
        self._drag_pos = QPoint()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        self.lang_label = QLabel("Live Transcript")
        self.lang_label.setFont(QFont("Segoe UI", 9))
        self.lang_label.setStyleSheet("color: rgba(255,255,255,180); background: transparent;")
        layout.addWidget(self.lang_label)

        self.history_view = QTextEdit()
        self.history_view.setReadOnly(True)
        self.history_view.setFont(QFont("Segoe UI", self._get_font_size()))
        self.history_view.setStyleSheet(
            "QTextEdit { color: rgba(240,240,240,255); background: rgba(0,0,0,40); border: 1px solid rgba(80,120,200,80); border-radius: 8px; }"
        )
        self.history_view.setPlaceholderText("Transcript se hien thi tai day...")
        layout.addWidget(self.history_view, 5)

        self.summary_title = QLabel("AI Tom Tat")
        self.summary_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.summary_title.setStyleSheet("color: rgba(180,220,255,220); background: transparent;")
        layout.addWidget(self.summary_title)

        self.summary_view = QTextEdit()
        self.summary_view.setReadOnly(True)
        self.summary_view.setFont(QFont("Segoe UI", max(10, self._get_font_size() - 1)))
        self.summary_view.setStyleSheet(
            "QTextEdit { color: rgba(255,255,255,235); background: rgba(10,25,45,120); border: 1px solid rgba(100,170,255,120); border-radius: 8px; }"
        )
        self.summary_view.setPlaceholderText("AI tom tat se cap nhat theo phien...")
        layout.addWidget(self.summary_view, 3)

        self.setLayout(layout)

        w = self.config.get("caption_width", 700) if self.config else 700
        h = self.config.get("caption_height", 420) if self.config else 420
        self.resize(w, h)

    def _get_font_size(self) -> int:
        return self.config.get("caption_font_size", 14) if self.config else 14

    def _load_position(self):
        if self.config:
            x = self.config.get("caption_x")
            y = self.config.get("caption_y")
            if x is not None and y is not None:
                self.move(x, y)
                return
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.center().x() - self.width() // 2, geo.center().y() - self.height() // 2)

    def _save_position(self):
        if self.config:
            self.config.set("caption_x", self.x())
            self.config.set("caption_y", self.y())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        opacity = self.config.get("caption_opacity", 0.9) if self.config else 0.9
        color = QColor(0, 0, 0, int(255 * opacity))
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(60, 120, 240, 100), 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)
        super().paintEvent(event)

    def show_caption(self, data: dict):
        self._idle_seconds = 0
        self.update_signal.emit(data)
        self._history.append(data)
        if len(self._history) > 500:
            self._history.pop(0)

    def set_summary(self, text: str):
        self.summary_signal.emit(text or "")

    def _on_update_summary(self, text: str):
        if text and text.strip():
            self.summary_view.setPlainText(text.strip())
            try:
                self._summary_file.write_text(text.strip() + "\n", encoding="utf-8")
            except Exception as e:
                logger.warning(f"Khong the ghi summary: {e}")

    def _on_update_text(self, data: dict):
        source_text = (data.get("source_text", "") or "").strip()
        target_text = (data.get("target_text", "") or "").strip()
        source_lang = data.get("source_lang", "en")

        lang_map = {"en": "EN", "vi": "VI", "unknown": "UNK"}
        self.lang_label.setText(f"Session Transcript [{lang_map.get(source_lang, 'UNK')}]")

        now = datetime.datetime.now().strftime("%H:%M:%S")
        if source_text and target_text and source_text.lower() == target_text.lower():
            line = f"[{now}] {target_text}"
        else:
            line = f"[{now}] SRC: {source_text}\n[{now}] VI : {target_text}"

        if line.strip():
            self.history_view.append(line)
            bar = self.history_view.verticalScrollBar()
            bar.setValue(bar.maximum())
            try:
                with self._history_file.open("a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except Exception as e:
                logger.warning(f"Khong the ghi history: {e}")

        self._current_text = {"source": source_text, "translated": target_text, "lang": source_lang}
        self.setWindowOpacity(self._get_opacity())
        self.show()
        self.raise_()

    def _get_opacity(self) -> float:
        if self._idle_seconds > 30:
            return max(0.3, 1.0 - (self._idle_seconds - 30) * 0.01)
        return 1.0

    def _check_fade(self):
        self._idle_seconds += 1
        self.setWindowOpacity(self._get_opacity())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            self._save_position()
            event.accept()

    def mouseDoubleClickEvent(self, event):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.center().x() - self.width() // 2, geo.center().y() - self.height() // 2)
            self._save_position()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()

    def closeEvent(self, event):
        self._save_position()
        super().closeEvent(event)

    @property
    def current_text(self) -> dict:
        return dict(self._current_text)

    @property
    def history(self) -> list:
        return list(self._history)

    def clear(self):
        self.history_view.clear()
        self.summary_view.clear()
        self.lang_label.setText("")
        self._current_text = {"source": "", "translated": "", "lang": ""}
