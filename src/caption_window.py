"""
Caption window: independent, resizable transcript and summary surface.
"""
import datetime
import logging
from pathlib import Path

from PyQt5.QtCore import QPoint, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizeGrip,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class CaptionWindow(QWidget):
    update_signal = pyqtSignal(dict)
    summary_signal = pyqtSignal(str)

    def __init__(self, config_manager=None, parent=None, app_ref=None):
        super().__init__(parent)
        self.config = config_manager
        self.app_ref = app_ref
        self._history = []
        self._current_text = {"source": "", "translated": "", "lang": ""}
        self._history_dir = Path.home() / ".teams-translator" / "history"
        self._history_dir.mkdir(parents=True, exist_ok=True)
        self._session_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self._history_file = self._history_dir / f"session-{self._session_id}.log"
        self._summary_file = self._history_dir / f"session-{self._session_id}-summary.txt"
        self._summary_collapsed = False
        self._summary_enabled = True
        self._dragging = False
        self._drag_pos = QPoint()
        self._idle_seconds = 0

        self.setWindowTitle("Teams Translator - Caption")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setMinimumSize(420, 240)

        self._setup_ui()
        self._load_position()

        self.update_signal.connect(self._on_update_text)
        self.summary_signal.connect(self._on_update_summary)

        self._fade_timer = QTimer()
        self._fade_timer.timeout.connect(self._check_fade)
        self._fade_timer.start(1000)

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame(self)
        self.card.setObjectName("captionCard")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(9, 9)
        self.status_dot.setObjectName("statusDot")
        header.addWidget(self.status_dot)

        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        self.title_label = QLabel("Live Caption")
        self.title_label.setObjectName("titleLabel")
        self.lang_label = QLabel("Session Transcript")
        self.lang_label.setObjectName("metaLabel")
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.lang_label)
        header.addLayout(title_box, 1)

        self.mode_label = QLabel("LISTENING")
        self.mode_label.setObjectName("modePill")
        header.addWidget(self.mode_label)

        self.summary_toggle = QPushButton("Summary")
        self.summary_toggle.setObjectName("smallButton")
        self.summary_toggle.clicked.connect(self._toggle_summary)
        header.addWidget(self.summary_toggle)
        self.summary_pause_btn = QPushButton("Pause")
        self.summary_pause_btn.setObjectName("smallButton")
        self.summary_pause_btn.clicked.connect(self._toggle_summary_updates)
        header.addWidget(self.summary_pause_btn)
        self.new_session_btn = QPushButton("New")
        self.new_session_btn.setObjectName("smallButton")
        self.new_session_btn.clicked.connect(self._new_session)
        header.addWidget(self.new_session_btn)
        self.history_btn = QPushButton("History")
        self.history_btn.setObjectName("smallButton")
        self.history_btn.clicked.connect(self._open_history)
        header.addWidget(self.history_btn)

        self.min_btn = QPushButton("_")
        self.min_btn.setObjectName("iconButton")
        self.min_btn.clicked.connect(self.showMinimized)
        header.addWidget(self.min_btn)

        self.close_btn = QPushButton("x")
        self.close_btn.setObjectName("closeButton")
        self.close_btn.clicked.connect(self.hide)
        header.addWidget(self.close_btn)
        card_layout.addLayout(header)

        self.history_view = QTextEdit()
        self.history_view.setReadOnly(True)
        self.history_view.setObjectName("historyView")
        self.history_view.setPlaceholderText("Transcript will appear here...")
        card_layout.addWidget(self.history_view, 5)

        self.summary_view = QTextEdit()
        self.summary_view.setReadOnly(True)
        self.summary_view.setObjectName("summaryView")
        self.summary_view.setPlaceholderText("AI summary will update during the session...")
        card_layout.addWidget(self.summary_view, 2)

        footer = QHBoxLayout()
        footer.addStretch(1)
        self.resize_hint = QLabel("drag corner to resize")
        self.resize_hint.setObjectName("resizeHint")
        footer.addWidget(self.resize_hint)
        self.grip = QSizeGrip(self.card)
        footer.addWidget(self.grip)
        card_layout.addLayout(footer)

        root.addWidget(self.card)
        self._apply_style()

        w = self.config.get("caption_width", 720) if self.config else 720
        h = self.config.get("caption_height", 360) if self.config else 360
        self.resize(w, h)

    def _apply_style(self):
        font_size = self._get_font_size()
        self.history_view.setFont(QFont("Segoe UI", font_size))
        self.summary_view.setFont(QFont("Segoe UI", max(10, font_size - 1)))
        self.setStyleSheet(
            """
            #captionCard {
                background: rgba(14, 18, 27, 232);
                border: 1px solid rgba(123, 164, 255, 120);
                border-radius: 14px;
            }
            #statusDot {
                background: #22c55e;
                border-radius: 4px;
            }
            #titleLabel {
                color: #f8fafc;
                font: 700 13px "Segoe UI";
            }
            #metaLabel, #resizeHint {
                color: rgba(203, 213, 225, 170);
                font: 10px "Segoe UI";
            }
            #modePill {
                color: #bbf7d0;
                background: rgba(34, 197, 94, 35);
                border: 1px solid rgba(34, 197, 94, 95);
                border-radius: 8px;
                padding: 4px 8px;
                font: 700 10px "Segoe UI";
            }
            #historyView, #summaryView {
                color: #f8fafc;
                background: rgba(15, 23, 42, 170);
                border: 1px solid rgba(148, 163, 184, 75);
                border-radius: 10px;
                padding: 8px;
                selection-background-color: #2563eb;
            }
            #summaryView {
                color: #dbeafe;
                background: rgba(30, 41, 59, 185);
            }
            #smallButton, #iconButton, #closeButton {
                color: #e2e8f0;
                background: rgba(51, 65, 85, 180);
                border: 1px solid rgba(148, 163, 184, 90);
                border-radius: 8px;
                padding: 5px 9px;
                font: 600 11px "Segoe UI";
            }
            #smallButton:hover, #iconButton:hover {
                background: rgba(71, 85, 105, 220);
            }
            #closeButton:hover {
                background: #dc2626;
                border-color: #ef4444;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: rgba(148, 163, 184, 120);
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            """
        )

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
            self.move(geo.center().x() - self.width() // 2, geo.bottom() - self.height() - 36)

    def _save_geometry(self):
        if self.config:
            self.config.set("caption_x", self.x())
            self.config.set("caption_y", self.y())
            self.config.set("caption_width", self.width())
            self.config.set("caption_height", self.height())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(255, 255, 255, 20), 1))
        painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 16, 16)
        super().paintEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.width() < 560:
            self.history_view.setFont(QFont("Segoe UI", max(11, self._get_font_size() - 2)))
        else:
            self.history_view.setFont(QFont("Segoe UI", self._get_font_size()))
        self._save_geometry()

    def show_caption(self, data: dict):
        self._idle_seconds = 0
        self.update_signal.emit(data)
        self._history.append(data)
        if len(self._history) > 500:
            self._history.pop(0)

    def set_summary(self, text: str):
        self.summary_signal.emit(text or "")

    def _toggle_summary(self):
        self._summary_collapsed = not self._summary_collapsed
        self.summary_view.setVisible(not self._summary_collapsed)
        self.summary_toggle.setText("Show summary" if self._summary_collapsed else "Summary")

    def _toggle_summary_updates(self):
        if self.app_ref:
            self.app_ref._toggle_summary_updates()

    def _new_session(self):
        if self.app_ref:
            self.app_ref.start_new_session()

    def _open_history(self):
        if self.app_ref:
            self.app_ref.open_session_history()

    def set_summary_enabled(self, enabled: bool):
        self._summary_enabled = bool(enabled)
        self.summary_pause_btn.setText("Pause" if self._summary_enabled else "Resume")
        if self._summary_enabled:
            self.summary_pause_btn.setStyleSheet("")
        else:
            self.summary_pause_btn.setStyleSheet("QPushButton{background:#475569;color:#e2e8f0;}")

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
        self.lang_label.setText(f"Transcript [{lang_map.get(source_lang, 'UNK')}]")

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
        if self._idle_seconds > 45:
            return max(0.55, 1.0 - (self._idle_seconds - 45) * 0.01)
        return 1.0

    def _check_fade(self):
        self._idle_seconds += 1
        self.setWindowOpacity(self._get_opacity())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.y() <= 48:
            self._dragging = True
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            self._save_geometry()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.resize(min(900, geo.width() - 80), 360)
            self.move(geo.center().x() - self.width() // 2, geo.bottom() - self.height() - 36)
            self._save_geometry()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()

    def closeEvent(self, event):
        self._save_geometry()
        super().closeEvent(event)

    @property
    def current_text(self) -> dict:
        return dict(self._current_text)

    @property
    def history(self) -> list:
        return list(self._history)

    def start_new_session(self, session_id: str):
        sid = (session_id or "").strip() or datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self._session_id = sid
        self._history_file = self._history_dir / f"session-{sid}.log"
        self._summary_file = self._history_dir / f"session-{sid}-summary.txt"
        self.clear()

    def load_session_view(self, transcript_lines: list[str], summary_text: str):
        self.history_view.setPlainText("\n".join(transcript_lines or []))
        self.summary_view.setPlainText((summary_text or "").strip())
        bar = self.history_view.verticalScrollBar()
        bar.setValue(bar.maximum())

    def clear(self):
        self.history_view.clear()
        self.summary_view.clear()
        self.lang_label.setText("Session Transcript")
        self._current_text = {"source": "", "translated": "", "lang": ""}
        self._history = []
