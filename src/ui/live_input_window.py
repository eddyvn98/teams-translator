import logging
import re
import time

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizeGrip,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import pyautogui

logger = logging.getLogger(__name__)


class LiveInputWindow(QWidget):
    """
    Independent VN -> EN composer.
    """

    def __init__(self, app_ref):
        super().__init__(None)
        self.app_ref = app_ref
        self.target_pos = None
        self._dragging = False
        self._drag_pos = QPoint()
        self._last_reply_payload = {}
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle("VN -> EN Composer")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(520, 360)
        self.resize(640, 520)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame(self)
        self.card.setObjectName("composerCard")
        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        self.title_label = QLabel("VN -> EN Composer")
        self.title_label.setObjectName("titleLabel")
        self.status_label = QLabel("Move mouse to target input and press Ctrl+Shift+V")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.status_label)
        header.addLayout(title_box, 1)

        self.min_btn = QPushButton("_")
        self.min_btn.setObjectName("iconButton")
        self.min_btn.clicked.connect(self.showMinimized)
        header.addWidget(self.min_btn)

        self.close_btn = QPushButton("x")
        self.close_btn.setObjectName("closeButton")
        self.close_btn.clicked.connect(self.hide)
        header.addWidget(self.close_btn)
        layout.addLayout(header)

        self.vn_input = QTextEdit()
        self.vn_input.setObjectName("mainInput")
        self.vn_input.setPlaceholderText("Type Vietnamese here...")
        self.vn_input.setFont(QFont("Segoe UI", 11))
        layout.addWidget(self.vn_input, 3)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.translate_btn = self._make_button("Translate + type", self.translate_and_inject, "primaryButton")
        self.reply_btn = self._make_button("Context reply", self.generate_reply_from_vn)
        self.auto_reply_btn = self._make_button("Auto reply", self.generate_auto_reply)
        self.speak_btn = self._make_button("Speak EN", self.speak_reply)
        self.clear_btn = self._make_button("Clear", self.vn_input.clear)
        for button in [self.translate_btn, self.reply_btn, self.auto_reply_btn, self.speak_btn, self.clear_btn]:
            btn_row.addWidget(button)
        layout.addLayout(btn_row)

        reply_row = QHBoxLayout()
        reply_row.setSpacing(10)
        en_col = QVBoxLayout()
        vi_col = QVBoxLayout()
        en_label = QLabel("English reply")
        vi_label = QLabel("Vietnamese reference")
        en_label.setObjectName("sectionLabel")
        vi_label.setObjectName("sectionLabel")
        self.reply_en = QTextEdit()
        self.reply_en.setReadOnly(True)
        self.reply_en.setObjectName("replyBox")
        self.reply_en.setPlaceholderText("English reply will appear here...")
        self.reply_vi = QTextEdit()
        self.reply_vi.setReadOnly(True)
        self.reply_vi.setObjectName("replyBox")
        self.reply_vi.setPlaceholderText("Vietnamese reference will appear here...")
        en_col.addWidget(en_label)
        en_col.addWidget(self.reply_en, 1)
        vi_col.addWidget(vi_label)
        vi_col.addWidget(self.reply_vi, 1)
        reply_row.addLayout(en_col, 1)
        reply_row.addLayout(vi_col, 1)
        layout.addLayout(reply_row, 3)

        footer = QHBoxLayout()
        footer.addStretch(1)
        self.resize_hint = QLabel("drag corner to resize")
        self.resize_hint.setObjectName("resizeHint")
        footer.addWidget(self.resize_hint)
        footer.addWidget(QSizeGrip(self.card))
        layout.addLayout(footer)

        root.addWidget(self.card)
        self._apply_style()

    def _make_button(self, text: str, callback, object_name: str = "toolbarButton") -> QPushButton:
        button = QPushButton(text)
        button.setObjectName(object_name)
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(callback)
        return button

    def _apply_style(self):
        self.setStyleSheet(
            """
            #composerCard {
                background: rgba(248, 250, 252, 242);
                border: 1px solid rgba(148, 163, 184, 160);
                border-radius: 14px;
            }
            #titleLabel {
                color: #0f172a;
                font: 700 14px "Segoe UI";
            }
            #statusLabel, #resizeHint {
                color: #64748b;
                font: 10px "Segoe UI";
            }
            #sectionLabel {
                color: #334155;
                font: 700 11px "Segoe UI";
            }
            QTextEdit {
                color: #0f172a;
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                padding: 8px;
                selection-background-color: #bfdbfe;
            }
            #mainInput {
                font: 11pt "Segoe UI";
            }
            #replyBox {
                background: #f8fafc;
            }
            #toolbarButton, #primaryButton, #iconButton, #closeButton {
                color: #0f172a;
                background: #e2e8f0;
                border: 1px solid #cbd5e1;
                border-radius: 9px;
                padding: 7px 10px;
                font: 600 11px "Segoe UI";
            }
            #primaryButton {
                color: white;
                background: #2563eb;
                border-color: #1d4ed8;
            }
            #toolbarButton:hover, #iconButton:hover {
                background: #cbd5e1;
            }
            #primaryButton:hover {
                background: #1d4ed8;
            }
            #closeButton:hover {
                color: white;
                background: #dc2626;
                border-color: #ef4444;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: rgba(100, 116, 139, 120);
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            """
        )

    def update_target_position(self, x: int, y: int):
        self.target_pos = (x, y)
        self.status_label.setText(f"Target input selected at ({x}, {y}).")

    def translate_and_inject(self):
        source_text = self.vn_input.toPlainText().strip()
        if not source_text:
            self.status_label.setText("No Vietnamese text to translate.")
            return
        if not self.target_pos:
            self.status_label.setText("Select target input first with Ctrl+Shift+V.")
            return

        result = self.app_ref.translator.translate_bidirectional(source_text, direction="vi2en")
        target_text = (result.get("target_text") or "").strip()
        target_text = self._sanitize_for_target_input(target_text)
        if not target_text:
            self.status_label.setText("Translation failed. Try again.")
            return

        try:
            pyautogui.click(self.target_pos[0], self.target_pos[1])
            time.sleep(0.12)
            pyautogui.typewrite(target_text, interval=0.004)
            self.status_label.setText("Typed English into target input.")
        except Exception as e:
            logger.exception("Inject text failed")
            self.status_label.setText(f"Text injection failed: {e}")

    def generate_reply_from_vn(self):
        source_text = self.vn_input.toPlainText().strip()
        if not source_text:
            self.status_label.setText("No text to generate a reply from.")
            return
        payload = self.app_ref.generate_reply_from_vietnamese(source_text)
        self._render_reply(payload, source="manual")

    def generate_auto_reply(self):
        payload = self.app_ref.generate_auto_reply()
        self._render_reply(payload, source="auto")

    def speak_reply(self):
        if not self._last_reply_payload:
            self.status_label.setText("No reply to speak.")
            return
        self.app_ref.speak_english_reply(self._last_reply_payload)
        self.status_label.setText("Speaking English reply...")

    def _render_reply(self, payload: dict, source: str):
        english = (payload.get("english_reply") or "").strip()
        vietnamese = (payload.get("vietnamese_translation") or "").strip()
        if not english:
            self.status_label.setText("Could not generate reply. Check API/model.")
            return
        self._last_reply_payload = payload
        self.reply_en.setPlainText(english)
        self.reply_vi.setPlainText(vietnamese)
        self.status_label.setText(f"Generated {source} reply.")

    def _sanitize_for_target_input(self, text: str) -> str:
        cleaned = (text or "").strip()
        if not cleaned:
            return ""
        cleaned = re.sub(
            r"^[\s\u200b\u200c\u200d\ufeff]*(🔊|🔈|🔉|📢|📣|🎤|🎙️|🎙|🗣️|🗣)+\s*",
            "",
            cleaned,
        )
        return cleaned.strip()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.y() <= 56:
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
        if event.button() == Qt.LeftButton:
            self._dragging = False
            event.accept()
            return
        super().mouseReleaseEvent(event)
