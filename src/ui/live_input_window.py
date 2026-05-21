import logging
import re
import time

from PyQt5.QtCore import QPoint, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QTextBlockFormat, QTextCursor
from PyQt5.QtWidgets import (
    QGridLayout,
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
    caption_signal = pyqtSignal(dict)
    summary_signal = pyqtSignal(str)
    capture_state_signal = pyqtSignal(bool)
    caption_enabled_signal = pyqtSignal(bool)
    summary_enabled_signal = pyqtSignal(bool)

    def __init__(self, app_ref):
        super().__init__(None)
        self.app_ref = app_ref
        self.target_pos = None
        self._dragging = False
        self._drag_pos = QPoint()
        self._last_reply_payload = {}
        self._caption_lines = []
        self._caption_visible = True
        self._summary_enabled = True
        self._build_ui()
        self.caption_signal.connect(self._on_caption_update)
        self.summary_signal.connect(self._on_summary_update)
        self.capture_state_signal.connect(self._on_capture_state_update)
        self.caption_enabled_signal.connect(self._on_caption_enabled_update)
        self.summary_enabled_signal.connect(self._on_summary_enabled_update)

    def _build_ui(self):
        self.setWindowTitle("Live Translator AI")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(460, 660)
        self.resize(520, 900)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame(self)
        self.card.setObjectName("composerCard")
        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(16, 14, 16, 12)
        layout.setSpacing(9)

        header = QHBoxLayout()
        header.setSpacing(10)
        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        self.title_label = QLabel("Live Translator AI")
        self.title_label.setObjectName("titleLabel")
        self.status_label = QLabel("Listening")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.status_label)
        header.addLayout(title_box, 1)

        self.pause_btn = self._make_button("Pause", self.app_ref._toggle_capture, "bottomButton")
        self.mark_btn = self._make_button("Mark target", self.app_ref._mark_target_input, "bottomButton")
        self.caption_btn = self._make_button("Caption", self.app_ref._toggle_caption, "bottomButton")
        self.hide_btn = self._make_button("Thu nhỏ", self.app_ref._minimize_to_floating, "bottomButton")
        self.hide_btn.setText("Thu nhỏ")

        self.min_btn = QPushButton("_")
        self.min_btn.setObjectName("iconButton")
        self.min_btn.clicked.connect(self.showMinimized)
        header.addWidget(self.min_btn)

        self.close_btn = QPushButton("x")
        self.close_btn.setObjectName("closeButton")
        self.close_btn.clicked.connect(self.hide)
        header.addWidget(self.close_btn)
        layout.addLayout(header)

        action_row = QGridLayout()
        action_row.setHorizontalSpacing(8)
        action_row.setVerticalSpacing(8)
        action_row.addWidget(self.pause_btn, 0, 0)
        action_row.addWidget(self.mark_btn, 0, 1)
        action_row.addWidget(self.caption_btn, 0, 2)
        action_row.addWidget(self.hide_btn, 0, 3)
        layout.addLayout(action_row)

        caption_header = QHBoxLayout()
        caption_header.setSpacing(8)
        self.caption_title = QLabel("LIVE CAPTION")
        self.caption_title.setObjectName("sectionHeader")
        caption_header.addWidget(self.caption_title)
        caption_header.addStretch(1)
        self.detach_btn = QPushButton("Tách cửa sổ")
        self.detach_btn.setText("Tách cửa sổ")
        self.detach_btn.setObjectName("miniButton")
        self.detach_btn.clicked.connect(self.app_ref._toggle_detached_caption_panel)
        caption_header.addWidget(self.detach_btn)
        self.caption_section_toggle = QPushButton("Ẩn")
        self.caption_section_toggle.setText("Ẩn")
        self.caption_section_toggle.setObjectName("miniButton")
        self.caption_section_toggle.clicked.connect(self.toggle_caption_section)
        caption_header.addWidget(self.caption_section_toggle)
        layout.addLayout(caption_header)

        self.caption_view = QTextEdit()
        self.caption_view.setReadOnly(True)
        self.caption_view.setObjectName("captionBox")
        self.caption_view.setPlaceholderText("Live caption will appear here...")
        self.caption_view.setFont(QFont("Segoe UI", 16))
        layout.addWidget(self.caption_view, 5)

        summary_header = QHBoxLayout()
        self.summary_title = QLabel("AI SUMMARY")
        self.summary_title.setObjectName("sectionHeader")
        summary_header.addWidget(self.summary_title)
        summary_header.addStretch(1)
        self.summary_toggle_btn = QPushButton("Pause")
        self.summary_toggle_btn.setObjectName("miniButton")
        self.summary_toggle_btn.clicked.connect(self.app_ref._toggle_summary_updates)
        summary_header.addWidget(self.summary_toggle_btn)
        self.new_session_btn = QPushButton("New")
        self.new_session_btn.setObjectName("miniButton")
        self.new_session_btn.clicked.connect(self.app_ref.start_new_session)
        summary_header.addWidget(self.new_session_btn)
        self.history_btn = QPushButton("History")
        self.history_btn.setObjectName("miniButton")
        self.history_btn.clicked.connect(self.app_ref.open_session_history)
        summary_header.addWidget(self.history_btn)
        layout.addLayout(summary_header)

        self.summary_view = QTextEdit()
        self.summary_view.setReadOnly(True)
        self.summary_view.setObjectName("summaryBox")
        self.summary_view.setPlaceholderText("AI summary will update during the meeting...")
        self.summary_view.setFont(QFont("Segoe UI", 14))
        layout.addWidget(self.summary_view, 3)

        ask_title = QLabel("ASK AI")
        ask_title.setObjectName("sectionHeader")
        layout.addWidget(ask_title)

        self.vn_input = QTextEdit()
        self.vn_input.setObjectName("mainInput")
        self.vn_input.setPlaceholderText("Hỏi AI về nội dung cuộc họp...")
        self.vn_input.setFont(QFont("Segoe UI", 11))
        layout.addWidget(self.vn_input, 2)

        btn_row = QGridLayout()
        btn_row.setHorizontalSpacing(8)
        btn_row.setVerticalSpacing(8)
        self.translate_btn = self._make_button("Translate + type", self.translate_and_inject, "primaryButton")
        self.reply_btn = self._make_button("Reply từ VN", self.generate_reply_from_vn)
        self.auto_reply_btn = self._make_button("Auto reply", self.generate_auto_reply)
        self.speak_btn = self._make_button("Speak EN", self.speak_reply)
        self.clear_btn = self._make_button("Clear", self.vn_input.clear, "toolbarButton")
        btn_row.addWidget(self.reply_btn, 0, 0)
        btn_row.addWidget(self.auto_reply_btn, 0, 1)
        btn_row.addWidget(self.speak_btn, 0, 2)
        btn_row.addWidget(self.translate_btn, 1, 0, 1, 2)
        btn_row.addWidget(self.clear_btn, 1, 2)
        layout.addLayout(btn_row)

        en_label = QLabel("AI gợi ý trả lời (English)")
        vi_label = QLabel("Input Translator")
        en_label.setObjectName("sectionHeader")
        vi_label.setObjectName("sectionHeader")
        layout.addWidget(en_label)
        self.reply_en = QTextEdit()
        self.reply_en.setReadOnly(True)
        self.reply_en.setObjectName("replyBox")
        self.reply_en.setPlaceholderText("English reply will appear here...")
        layout.addWidget(self.reply_en, 2)

        layout.addWidget(vi_label)
        self.reply_vi = QTextEdit()
        self.reply_vi.setReadOnly(True)
        self.reply_vi.setObjectName("replyBox")
        self.reply_vi.setPlaceholderText("Kết quả dịch và bản nháp sẽ hiện tại đây...")
        layout.addWidget(self.reply_vi, 2)

        footer = QHBoxLayout()
        footer.addStretch(1)
        footer.addWidget(QSizeGrip(self.card))
        layout.addLayout(footer)

        root.addWidget(self.card)
        self._apply_style()

    def _make_button(self, text: str, callback, object_name: str = "toolbarButton") -> QPushButton:
        button = QPushButton(text)
        button.setObjectName(object_name)
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(34)
        button.clicked.connect(callback)
        return button

    def _apply_style(self):
        self.setStyleSheet(
            """
            #composerCard {
                background: rgba(10, 16, 28, 246);
                border: 1px solid rgba(124, 139, 164, 150);
                border-radius: 14px;
            }
            #titleLabel {
                color: #f8fafc;
                font: 800 15px "Segoe UI";
            }
            #statusLabel {
                color: #86efac;
                font: 700 11px "Segoe UI";
            }
            #sectionHeader {
                color: #cbd5e1;
                font: 800 11px "Segoe UI";
                letter-spacing: 0px;
            }
            QTextEdit {
                color: #f8fafc;
                background: rgba(16, 24, 39, 225);
                border: 1px solid rgba(100, 116, 139, 140);
                border-radius: 8px;
                padding: 10px;
                selection-background-color: #1d4ed8;
            }
            QTextEdit:focus {
                border: 1px solid rgba(96, 165, 250, 210);
                background: rgba(15, 23, 42, 245);
            }
            #mainInput {
                font: 11pt "Segoe UI";
            }
            #replyBox {
                color: #dbeafe;
                background: rgba(5, 10, 22, 225);
            }
            #captionBox {
                background: rgba(3, 8, 18, 235);
                border-color: rgba(148, 163, 184, 150);
                font: 700 16px "Segoe UI";
                line-height: 1.5;
            }
            #summaryBox {
                color: #e5eefc;
                background: rgba(18, 28, 45, 235);
                font: 500 14px "Segoe UI";
                line-height: 1.45;
            }
            #toolbarButton, #primaryButton, #iconButton, #closeButton, #miniButton, #bottomButton {
                color: #e2e8f0;
                background: rgba(31, 42, 58, 235);
                border: 1px solid rgba(124, 139, 164, 145);
                border-radius: 8px;
                padding: 7px 11px;
                font: 700 11px "Segoe UI";
            }
            #primaryButton {
                color: white;
                background: #1f6feb;
                border-color: #3b82f6;
                font: 800 11px "Segoe UI";
            }
            #miniButton {
                min-height: 26px;
                padding: 4px 10px;
                font: 700 10px "Segoe UI";
            }
            #bottomButton {
                min-height: 34px;
                font: 700 10px "Segoe UI";
            }
            #iconButton, #closeButton {
                min-width: 30px;
                max-width: 30px;
                min-height: 30px;
                padding: 0px;
                border-radius: 8px;
            }
            #toolbarButton:hover, #iconButton:hover, #miniButton:hover, #bottomButton:hover {
                background: rgba(51, 65, 85, 245);
                border-color: rgba(148, 163, 184, 190);
            }
            #primaryButton:hover {
                background: #1d4ed8;
            }
            #closeButton:hover {
                background: #dc2626;
                border-color: #ef4444;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 9px;
            }
            QScrollBar::handle:vertical {
                background: rgba(148, 163, 184, 125);
                border-radius: 4px;
                min-height: 34px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            """
        )

    def _button_state_style(self, background: str, color: str, border: str, min_height: int = 34) -> str:
        return (
            f"background:{background};"
            f"color:{color};"
            f"border:1px solid {border};"
            "border-radius:8px;"
            "padding:7px 11px;"
            "font:700 11px 'Segoe UI';"
            f"min-height:{min_height}px;"
        )

    def update_target_position(self, x: int, y: int):
        self.target_pos = (x, y)
        self.status_label.setText(f"Target input selected at ({x}, {y}).")

    def update_live_caption(self, payload: dict):
        self.caption_signal.emit(payload or {})

    def update_ai_summary(self, summary: str):
        self.summary_signal.emit(summary or "")

    def set_capture_state(self, capturing: bool):
        self.capture_state_signal.emit(bool(capturing))

    def set_caption_enabled(self, enabled: bool):
        self.caption_enabled_signal.emit(bool(enabled))

    def set_summary_enabled(self, enabled: bool):
        self.summary_enabled_signal.emit(bool(enabled))

    def set_detached_mode(self, detached: bool):
        self.detach_btn.setText("Gắn vào panel" if detached else "Tách cửa sổ")
        self.caption_title.setVisible(not detached and self._caption_visible)
        self.caption_section_toggle.setVisible(not detached)
        self.caption_view.setVisible(not detached and self._caption_visible)
        self.summary_title.setVisible(not detached and self._caption_visible)
        self.summary_toggle_btn.setVisible(not detached and self._caption_visible)
        self.summary_view.setVisible(not detached and self._caption_visible)

    def toggle_caption_section(self):
        self.set_caption_enabled(not self._caption_visible)

    def _on_caption_update(self, payload: dict):
        source = (payload.get("source_text") or "").strip()
        translated = (payload.get("target_text") or payload.get("display_text") or "").strip()
        if not source and not translated:
            return
        line = translated if translated else source
        if not line:
            return
        self._caption_lines.append(line)
        if len(self._caption_lines) > 120:
            self._caption_lines = self._caption_lines[-120:]
        self.caption_view.setPlainText("\n".join(self._caption_lines))
        cursor = self.caption_view.textCursor()
        cursor.select(QTextCursor.Document)
        block_format = QTextBlockFormat()
        block_format.setLineHeight(155, QTextBlockFormat.ProportionalHeight)
        cursor.mergeBlockFormat(block_format)
        cursor.clearSelection()
        self.caption_view.setTextCursor(cursor)
        self.caption_view.verticalScrollBar().setValue(self.caption_view.verticalScrollBar().maximum())

    def _on_summary_update(self, summary: str):
        text = (summary or "").strip()
        if text:
            self.summary_view.setPlainText(text)
            cursor = self.summary_view.textCursor()
            cursor.select(QTextCursor.Document)
            block_format = QTextBlockFormat()
            block_format.setLineHeight(145, QTextBlockFormat.ProportionalHeight)
            cursor.mergeBlockFormat(block_format)
            cursor.clearSelection()
            self.summary_view.setTextCursor(cursor)

    def _on_capture_state_update(self, capturing: bool):
        self.pause_btn.setText("Pause" if capturing else "Resume")
        self.status_label.setText("Listening" if capturing else "Paused")
        if capturing:
            self.pause_btn.setStyleSheet(self._button_state_style("#f59e0b", "#111827", "#fbbf24"))
        else:
            self.pause_btn.setStyleSheet(self._button_state_style("#1f6feb", "#ffffff", "#3b82f6"))

    def _on_caption_enabled_update(self, enabled: bool):
        self._caption_visible = enabled
        detached = self.detach_btn.text().strip().lower().startswith("gắn")
        self.caption_title.setVisible(enabled and not detached)
        self.caption_view.setVisible(enabled and not detached)
        self.summary_title.setVisible(enabled and not detached)
        self.summary_toggle_btn.setVisible(enabled and not detached)
        self.summary_view.setVisible(enabled and not detached)
        self.caption_section_toggle.setText("Ẩn" if enabled else "Hiện")
        if enabled:
            self.caption_btn.setStyleSheet(self._button_state_style("#22c55e", "#052e16", "#4ade80"))
        else:
            self.caption_btn.setStyleSheet(self._button_state_style("#475569", "#e2e8f0", "#64748b"))

    def _on_summary_enabled_update(self, enabled: bool):
        self._summary_enabled = enabled
        self.summary_toggle_btn.setText("Pause" if enabled else "Resume")
        if enabled:
            self.summary_toggle_btn.setStyleSheet(self._button_state_style("#22c55e", "#052e16", "#4ade80", 26))
            self.summary_view.setPlaceholderText("AI summary will update during the meeting...")
        else:
            self.summary_toggle_btn.setStyleSheet(self._button_state_style("#475569", "#e2e8f0", "#64748b", 26))
            self.summary_view.setPlaceholderText("AI summary is paused.")

    def load_session_view(self, transcript_lines: list[str], summary_text: str):
        self._caption_lines = list(transcript_lines or [])
        self.caption_view.setPlainText("\n".join(self._caption_lines))
        self.summary_view.setPlainText((summary_text or "").strip())
        self.caption_view.verticalScrollBar().setValue(self.caption_view.verticalScrollBar().maximum())

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

        self._last_reply_payload = {
            "english_reply": target_text,
            "vietnamese_translation": source_text,
            "speaking_script": target_text,
        }
        self.reply_en.setPlainText(target_text)
        self.reply_vi.setPlainText(source_text)

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
        source_text = self.vn_input.toPlainText().strip()
        if source_text:
            result = self.app_ref.translator.translate_bidirectional(source_text, direction="vi2en")
            english_text = self._sanitize_for_target_input((result.get("target_text") or "").strip())
            if not english_text:
                self.status_label.setText("Translation failed. Try again.")
                return
            self._last_reply_payload = {
                "english_reply": english_text,
                "vietnamese_translation": source_text,
                "speaking_script": english_text,
            }
            self.reply_en.setPlainText(english_text)
            self.reply_vi.setPlainText(source_text)
        elif not self._last_reply_payload:
            english_text = self.reply_en.toPlainText().strip()
            if english_text:
                self._last_reply_payload = {
                    "english_reply": english_text,
                    "vietnamese_translation": self.reply_vi.toPlainText().strip(),
                    "speaking_script": english_text,
                }
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
