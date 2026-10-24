import logging
import re
import time

from PyQt5.QtCore import QPoint, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QTextBlockFormat, QTextCursor
from PyQt5.QtWidgets import (
    QApplication,
    QGridLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QSizeGrip,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import pyautogui

try:
    from src.ui.icons import get_svg_icon, make_icon_button, make_action_card_button, make_labeled_button
except ImportError:
    from src_minimal.ui.icons import get_svg_icon, make_icon_button, make_action_card_button, make_labeled_button

logger = logging.getLogger(__name__)


class LiveInputWindow(QWidget):
    """
    Independent VN -> EN composer and Meeting Assistant.
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
        self._caption_en_lines = []
        self._caption_vi_lines = []
        self._live_en_partial = ""
        self._live_vi_partial = ""
        self._caption_history_items = []
        self._caption_visible = True
        self._summary_enabled = True
        self._detached_mode = False
        self._interim_start_pos = 0
        self._en_interim_start_pos = 0
        self._vi_interim_start_pos = 0
        self._has_interim = False
        cfg = getattr(self.app_ref, "config", None)
        self._input_section_visible = bool(cfg.get("input_section_visible", True)) if cfg else True
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
        self.setMinimumSize(460, 520)
        self.resize(520, 720)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame(self)
        self.card.setObjectName("composerCard")
        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # 1. Header: Wave logo + Titles + Status dot/label + Window controls
        header = QHBoxLayout()
        header.setSpacing(10)

        self.logo_icon = QLabel()
        self.logo_icon.setObjectName("logoIcon")
        self.logo_icon.setPixmap(get_svg_icon("soundwave", color="#38bdf8", size=24).pixmap(24, 24))
        header.addWidget(self.logo_icon)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        self.title_label = QLabel("Live Translator AI")
        self.title_label.setObjectName("titleLabel")
        self.sub_title_label = QLabel("Your AI meeting companion")
        self.sub_title_label.setObjectName("subTitleLabel")

        status_row = QHBoxLayout()
        status_row.setSpacing(5)
        self.status_dot = QLabel()
        self.status_dot.setObjectName("statusDot")
        self.status_dot.setFixedSize(7, 7)
        self.status_label = QLabel("Listening")
        self.status_label.setObjectName("statusLabel")
        status_row.addWidget(self.status_dot)
        status_row.addWidget(self.status_label)
        status_row.addStretch(1)

        title_box.addWidget(self.title_label)
        title_box.addWidget(self.sub_title_label)
        title_box.addLayout(status_row)
        header.addLayout(title_box, 1)

        self.min_btn = make_icon_button(
            "minus",
            "Thu nhỏ cửa sổ xuống Taskbar",
            self.showMinimized,
            color="#cbd5e1",
            btn_size=28,
            icon_size=14,
            object_name="iconButton",
            parent=self.card,
        )
        self.hide_btn = make_icon_button(
            "menu",
            "Thu nhỏ về thanh điều khiển nổi (Pill)",
            self.app_ref._minimize_to_floating,
            color="#cbd5e1",
            btn_size=28,
            icon_size=14,
            object_name="iconButton",
            parent=self.card,
        )
        self.close_btn = make_icon_button(
            "close",
            "Ẩn cửa sổ",
            self.hide,
            color="#cbd5e1",
            btn_size=28,
            icon_size=14,
            object_name="closeButton",
            parent=self.card,
        )
        header.addWidget(self.min_btn)
        header.addWidget(self.hide_btn)
        header.addWidget(self.close_btn)
        layout.addLayout(header)

        # 2. Quick Action Bar: 6 Card Buttons with icon above and text below
        action_toolbar = QHBoxLayout()
        action_toolbar.setSpacing(6)

        self.pause_btn = make_action_card_button(
            "pause",
            "Pause",
            "Tạm dừng thu âm / dịch (Ctrl+Shift+T)",
            self.app_ref._toggle_capture,
            color="#ef4444",
            btn_width=68,
            btn_height=56,
            icon_size=18,
            object_name="pauseCardButton",
            parent=self.card,
        )
        self.detach_btn = make_action_card_button(
            "detach",
            "Detach",
            "Tách bảng dịch thành cửa sổ riêng",
            self.app_ref._toggle_detached_caption_panel,
            color="#cbd5e1",
            btn_width=68,
            btn_height=56,
            icon_size=18,
            object_name="actionCardButton",
            parent=self.card,
        )
        self.caption_btn = make_action_card_button(
            "cc",
            "Captions",
            "Bật / Tắt dịch phụ đề (Ctrl+Shift+C)",
            self.app_ref._toggle_caption,
            color="#cbd5e1",
            btn_width=68,
            btn_height=56,
            icon_size=18,
            object_name="actionCardButton",
            parent=self.card,
        )
        self.mark_btn = make_action_card_button(
            "pin",
            "Pin to Teams",
            "Chọn ô nhập Teams / App mục tiêu (Ctrl+Shift+V)",
            self.app_ref._mark_target_input,
            color="#cbd5e1",
            btn_width=72,
            btn_height=56,
            icon_size=18,
            object_name="actionCardButton",
            parent=self.card,
        )
        self.setup_audio_btn = make_action_card_button(
            "headphones",
            "Speaker",
            "Nghe loa & Dịch (Cable Output)",
            self.app_ref.manual_setup_audio,
            color="#cbd5e1",
            btn_width=68,
            btn_height=56,
            icon_size=18,
            object_name="actionCardButton",
            parent=self.card,
        )
        self.restore_audio_btn = make_action_card_button(
            "refresh",
            "Reset Audio",
            "Khôi phục loa mặc định",
            self.app_ref.manual_restore_audio,
            color="#cbd5e1",
            btn_width=72,
            btn_height=56,
            icon_size=18,
            object_name="actionCardButton",
            parent=self.card,
        )

        for btn in [self.pause_btn, self.detach_btn, self.caption_btn, self.mark_btn, self.setup_audio_btn, self.restore_audio_btn]:
            action_toolbar.addWidget(btn)

        layout.addLayout(action_toolbar)

        # 3. LIVE CAPTION Section (Dual Columns) — wrapped in section widget for proper collapse
        self.caption_section_widget = QWidget(self.card)
        self.caption_section_widget.setObjectName("captionSection")
        caption_section_layout = QVBoxLayout(self.caption_section_widget)
        caption_section_layout.setContentsMargins(0, 0, 0, 0)
        caption_section_layout.setSpacing(6)

        caption_header = QHBoxLayout()
        caption_header.setSpacing(6)

        caption_icon = QLabel()
        caption_icon.setPixmap(get_svg_icon("soundwave", color="#38bdf8", size=14).pixmap(14, 14))
        caption_header.addWidget(caption_icon)

        self.caption_title = QLabel("LIVE CAPTION")
        self.caption_title.setObjectName("sectionHeader")
        caption_header.addWidget(self.caption_title)
        caption_header.addStretch(1)

        self.caption_section_toggle = make_icon_button(
            "chevron_up",
            "Thu gọn phần Live Caption",
            self.toggle_caption_section,
            color="#cbd5e1",
            btn_size=26,
            icon_size=13,
            object_name="miniButton",
            parent=self.card,
        )
        caption_header.addWidget(self.caption_section_toggle)
        caption_section_layout.addLayout(caption_header)

        # Dual Column View Container
        self.caption_container = QWidget(self.caption_section_widget)
        self.caption_container.setObjectName("captionContainer")
        col_layout = QHBoxLayout(self.caption_container)
        col_layout.setContentsMargins(0, 0, 0, 0)
        col_layout.setSpacing(8)

        # Left Column: English (Recognition)
        left_col = QVBoxLayout()
        left_col.setSpacing(4)
        left_head = QHBoxLayout()
        left_lbl = QLabel("English (Recognition)")
        left_lbl.setObjectName("columnTitle")
        left_head.addWidget(left_lbl)
        left_head.addStretch(1)
        self.badge_en = QLabel("● Live")
        self.badge_en.setObjectName("liveBadgeEn")
        left_head.addWidget(self.badge_en)
        left_col.addLayout(left_head)

        self.caption_en_view = QTextEdit(self.caption_container)
        self.caption_en_view.setReadOnly(True)
        self.caption_en_view.setObjectName("captionBox")
        self.caption_en_view.setPlaceholderText("Speech transcript will appear here...")
        self.caption_en_view.setFont(QFont("Segoe UI", 12))
        left_col.addWidget(self.caption_en_view, 1)
        col_layout.addLayout(left_col, 1)

        # Right Column: Tiếng Việt (Bản dịch)
        right_col = QVBoxLayout()
        right_col.setSpacing(4)
        right_head = QHBoxLayout()
        right_lbl = QLabel("Tiếng Việt (Bản dịch)")
        right_lbl.setObjectName("columnTitle")
        right_head.addWidget(right_lbl)
        right_head.addStretch(1)
        self.badge_vi = QLabel("● Trực tiếp")
        self.badge_vi.setObjectName("liveBadgeVi")
        right_head.addWidget(self.badge_vi)
        right_col.addLayout(right_head)

        self.caption_vi_view = QTextEdit(self.caption_container)
        self.caption_vi_view.setReadOnly(True)
        self.caption_vi_view.setObjectName("captionBox")
        self.caption_vi_view.setPlaceholderText("Bản dịch tiếng Việt sẽ hiển thị ở đây...")
        self.caption_vi_view.setFont(QFont("Segoe UI", 12))
        right_col.addWidget(self.caption_vi_view, 1)
        col_layout.addLayout(right_col, 1)

        caption_section_layout.addWidget(self.caption_container)
        layout.addWidget(self.caption_section_widget, 4)

        # Compatibility alias
        self.caption_view = self.caption_en_view

        # Hidden stubs kept for backend/signal compatibility
        self.summary_title = QLabel()
        self.summary_title.setVisible(False)
        self.summary_toggle_btn = make_icon_button(
            "pause", "", self.app_ref._toggle_summary_updates,
            color="#cbd5e1", btn_size=26, icon_size=13,
            object_name="miniButton", parent=self.card,
        )
        self.summary_toggle_btn.setVisible(False)
        self.new_session_btn = make_labeled_button(
            "plus", "+ New", "Bắt đầu phiên mới (New Session)",
            self.app_ref.start_new_session,
            color="#cbd5e1", btn_height=26, icon_size=11,
            object_name="miniLabeledButton", parent=self.card,
        )
        self.new_session_btn.setVisible(False)
        self.history_btn = make_labeled_button(
            "history", "History", "Xem lịch sử cuộc họp (History)",
            self.app_ref.open_session_history,
            color="#cbd5e1", btn_height=26, icon_size=11,
            object_name="miniLabeledButton", parent=self.card,
        )
        self.history_btn.setVisible(False)
        self.summary_view = QTextEdit()
        self.summary_view.setVisible(False)
        self.reply_en = QTextEdit()
        self.reply_en.setVisible(False)
        self.reply_vi = QTextEdit()
        self.reply_vi.setVisible(False)
        self.copy_en_btn = make_icon_button("copy", "", self.copy_en_text, color="#94a3b8", btn_size=22, icon_size=12, object_name="copyMiniButton", parent=self.card)
        self.copy_en_btn.setVisible(False)
        self.copy_vi_btn = make_icon_button("copy", "", self.copy_vi_text, color="#94a3b8", btn_size=22, icon_size=12, object_name="copyMiniButton", parent=self.card)
        self.copy_vi_btn.setVisible(False)

        # 4. NHẬP TIẾNG VIỆT Section
        input_header = QHBoxLayout()
        input_header.setSpacing(6)

        ask_icon = QLabel()
        ask_icon.setPixmap(get_svg_icon("sparkles", color="#38bdf8", size=14).pixmap(14, 14))
        input_header.addWidget(ask_icon)

        self.input_title = QLabel("NHẬP TIẾNG VIỆT")
        self.input_title.setObjectName("sectionHeader")
        input_header.addWidget(self.input_title)
        input_header.addStretch(1)

        self.input_section_toggle = make_icon_button(
            "chevron_up",
            "Thu gọn phần nhập tiếng Việt",
            self.toggle_input_section,
            color="#cbd5e1",
            btn_size=26,
            icon_size=13,
            object_name="miniButton",
            parent=self.card,
        )
        input_header.addWidget(self.input_section_toggle)
        layout.addLayout(input_header)

        self.input_container = QWidget(self.card)
        input_layout = QVBoxLayout(self.input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)

        # Text input with character counter inside frame
        input_frame = QFrame(self.input_container)
        input_frame.setObjectName("inputFrame")
        input_frame_layout = QVBoxLayout(input_frame)
        input_frame_layout.setContentsMargins(8, 6, 8, 6)
        input_frame_layout.setSpacing(2)

        self.vn_input = QTextEdit(input_frame)
        self.vn_input.setObjectName("mainInput")
        self.vn_input.setPlaceholderText("Nhập nội dung cần dịch / phản hồi...")
        self.vn_input.setFont(QFont("Segoe UI", 11))
        self.vn_input.textChanged.connect(self._adjust_vn_input_height)
        input_frame_layout.addWidget(self.vn_input)

        counter_row = QHBoxLayout()
        counter_row.addStretch(1)
        self.char_count_label = QLabel("0/2000")
        self.char_count_label.setObjectName("charCounter")
        counter_row.addWidget(self.char_count_label)
        input_frame_layout.addLayout(counter_row)

        input_layout.addWidget(input_frame)

        # Action buttons row: Clear, Send (removed Rewrite / Smart Reply / Play per user request)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.clear_btn = make_labeled_button("trash", "Clear", "Xóa nội dung nhập", self.vn_input.clear, color="#cbd5e1", btn_height=32, icon_size=13, parent=self.card)
        self.reply_btn = make_labeled_button("pencil", "Rewrite to English", "Gợi ý câu trả lời tiếng Anh", self.generate_reply_from_vn, color="#cbd5e1", btn_height=32, icon_size=13, parent=self.card)
        self.auto_reply_btn = make_labeled_button("sparkles", "Smart Reply", "Tự động tạo câu trả lời thông minh", self.generate_auto_reply, color="#cbd5e1", btn_height=32, icon_size=13, parent=self.card)
        self.speak_btn = make_labeled_button("volume_1", "Play (TTS)", "Phát âm câu trả lời tiếng Anh", self.speak_reply, color="#cbd5e1", btn_height=32, icon_size=13, parent=self.card)
        self.translate_btn = make_labeled_button("send", "Send", "Dịch sang tiếng Anh & Gõ tự động vào Teams (Enter)", self.translate_and_inject, color="#ffffff", btn_height=32, icon_size=13, object_name="sendButton", parent=self.card)

        self.reply_btn.setVisible(False)
        self.auto_reply_btn.setVisible(False)
        self.speak_btn.setVisible(False)

        btn_row.addWidget(self.clear_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(self.translate_btn)
        input_layout.addLayout(btn_row)

        layout.addWidget(self.input_container)

        # Footer resize grip
        footer = QHBoxLayout()
        footer.addStretch(1)
        footer.addWidget(QSizeGrip(self.card))
        layout.addLayout(footer)

        root.addWidget(self.card)
        self._apply_style()
        self._update_input_section_ui(skip_resize=True)
        self._adjust_vn_input_height()

    def copy_en_text(self):
        txt = self.reply_en.toPlainText().strip()
        if txt:
            QApplication.clipboard().setText(txt)
            self.status_label.setText("Copied English reply!")

    def copy_vi_text(self):
        txt = self.reply_vi.toPlainText().strip()
        if txt:
            QApplication.clipboard().setText(txt)
            self.status_label.setText("Copied Vietnamese meaning!")

    def _apply_style(self):
        self.setStyleSheet(
            """
            #composerCard {
                background: rgba(10, 16, 30, 250);
                border: 1px solid rgba(56, 189, 248, 0.25);
                border-radius: 16px;
            }
            #titleLabel {
                color: #f8fafc;
                font: 800 15px "Segoe UI";
            }
            #subTitleLabel {
                color: #94a3b8;
                font: 500 11px "Segoe UI";
            }
            #statusLabel {
                color: #4ade80;
                font: 600 11px "Segoe UI";
            }
            #statusDot {
                background: #22c55e;
                border-radius: 3px;
            }
            #sectionHeader {
                color: #94a3b8;
                font: 800 11px "Segoe UI";
                letter-spacing: 0.5px;
            }
            #columnTitle {
                color: #cbd5e1;
                font: 700 11px "Segoe UI";
            }
            #liveBadgeEn {
                background: rgba(168, 85, 247, 0.2);
                border: 1px solid rgba(168, 85, 247, 0.4);
                border-radius: 4px;
                color: #c084fc;
                font: 700 9px "Segoe UI";
                padding: 1px 6px;
            }
            #liveBadgeVi {
                background: rgba(34, 197, 94, 0.2);
                border: 1px solid rgba(34, 197, 94, 0.4);
                border-radius: 4px;
                color: #4ade80;
                font: 700 9px "Segoe UI";
                padding: 1px 6px;
            }
            #actionCardButton {
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                color: #cbd5e1;
                font: 600 10px "Segoe UI";
                padding: 4px 2px;
            }
            #actionCardButton:hover {
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(56, 189, 248, 0.3);
                color: #f8fafc;
            }
            #pauseCardButton {
                background: rgba(239, 68, 68, 0.16);
                border: 1px solid rgba(239, 68, 68, 0.4);
                border-radius: 10px;
                color: #fca5a5;
                font: 600 10px "Segoe UI";
                padding: 4px 2px;
            }
            #pauseCardButton:hover {
                background: rgba(239, 68, 68, 0.3);
            }
            #captionBox {
                background: rgba(8, 14, 26, 220);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 10px;
                padding: 8px;
                color: #f8fafc;
                font: 12px "Segoe UI";
            }
            #summaryBox {
                background: rgba(10, 16, 30, 220);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 10px;
                padding: 8px;
                color: #cbd5e1;
                font: 11px "Segoe UI";
            }
            #inputFrame {
                background: rgba(8, 14, 26, 220);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
            }
            #mainInput {
                background: transparent;
                border: none;
                color: #f8fafc;
                padding: 4px;
            }
            #charCounter {
                color: #64748b;
                font: 10px "Segoe UI";
                padding-right: 4px;
                padding-bottom: 2px;
            }
            #labeledButton {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 7px;
                color: #cbd5e1;
                font: 600 11px "Segoe UI";
                padding: 0 10px;
            }
            #labeledButton:hover {
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(56, 189, 248, 0.25);
                color: #f8fafc;
            }
            #sendButton {
                background: #2563eb;
                border: 1px solid #3b82f6;
                border-radius: 7px;
                color: #ffffff;
                font: 700 11px "Segoe UI";
                padding: 0 14px;
            }
            #sendButton:hover {
                background: #1d4ed8;
            }
            #responseCard {
                background: rgba(8, 14, 26, 220);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 10px;
            }
            #cardHeaderLabel {
                color: #94a3b8;
                font: 600 11px "Segoe UI";
            }
            #replyBox {
                background: transparent;
                border: none;
                color: #e2e8f0;
                padding: 2px;
            }
            #copyMiniButton {
                background: transparent;
                border: none;
                border-radius: 4px;
            }
            #copyMiniButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            #miniButton, #miniLabeledButton {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                color: #cbd5e1;
                font: 600 10px "Segoe UI";
                padding: 0 6px;
            }
            #miniButton:hover, #miniLabeledButton:hover {
                background: rgba(255, 255, 255, 0.12);
            }
            #iconButton, #closeButton {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 0px;
            }
            #iconButton:hover {
                background: rgba(255, 255, 255, 0.16);
            }
            #closeButton:hover {
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
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: rgba(148, 163, 184, 120);
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            """
        )

    def _button_state_style(self, background: str, color: str, border: str, min_height: int = 34) -> str:
        return (
            f"background:{background};"
            f"border:1px solid {border};"
            "border-radius:8px;"
            "padding:0px;"
            f"min-height:{min_height}px;"
            f"max-height:{min_height}px;"
            f"min-width:{min_height}px;"
            f"max-width:{min_height}px;"
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
        was_detached = getattr(self, "_detached_mode", False)
        self._detached_mode = bool(detached)
        if detached:
            self.detach_btn.setIcon(get_svg_icon("attach", color="#38bdf8", size=18))
            self.detach_btn.setText("Attach")
            self.detach_btn.setToolTip("Gắn lại bảng dịch vào panel chính")
            self.detach_btn.setStyleSheet("""
                QToolButton {
                    background: rgba(56, 189, 248, 0.16);
                    border: 1px solid rgba(56, 189, 248, 0.4);
                    border-radius: 10px;
                    color: #7dd3fc;
                    font: 600 10px "Segoe UI";
                    padding: 4px 2px;
                }
            """)
        else:
            self.detach_btn.setIcon(get_svg_icon("detach", color="#cbd5e1", size=18))
            self.detach_btn.setText("Detach")
            self.detach_btn.setToolTip("Tách bảng dịch thành cửa sổ riêng")
            self.detach_btn.setStyleSheet("")

        if detached:
            if not was_detached and self.height() > 400:
                self._attached_size = self.size()
            self.caption_title.setText("LIVE CAPTION (ĐÃ TÁCH)")
            # Hide entire caption section when detached
            if hasattr(self, "caption_section_widget"):
                self.caption_section_widget.setVisible(False)
            self.caption_title.setVisible(False)
            self.caption_section_toggle.setVisible(False)

            min_h = 200 if not getattr(self, "_input_section_visible", True) else 300
            self.setMinimumSize(420, min_h)
            self.setMaximumHeight(360 if getattr(self, "_input_section_visible", True) else 220)

            self.card.layout().activate()
            self.layout().activate()
            self.updateGeometry()

            compact_h = 200 if not getattr(self, "_input_section_visible", True) else getattr(self, "_detached_height", 300)
            self.resize(self.width(), compact_h)
        else:
            self.setMaximumHeight(16777215)
            if was_detached and self.height() <= 400:
                self._detached_height = self.height()
            self.caption_title.setText("LIVE CAPTION")
            self.caption_title.setVisible(self._caption_visible)
            self.caption_section_toggle.setVisible(True)
            if hasattr(self, "caption_section_widget"):
                self.caption_section_widget.setVisible(self._caption_visible)
            self.setMinimumSize(460, 520)

            self.card.layout().activate()
            self.layout().activate()
            self.updateGeometry()

            restored_h = getattr(self, "_attached_size", None) and self._attached_size.height() or 720
            if restored_h < 520:
                restored_h = 720
            self.resize(self.width(), restored_h)


    def toggle_caption_section(self):
        self.set_caption_enabled(not self._caption_visible)

    def toggle_input_section(self):
        self.set_input_section_visible(not getattr(self, "_input_section_visible", True))

    def set_input_section_visible(self, visible: bool):
        self._input_section_visible = bool(visible)
        cfg = getattr(self.app_ref, "config", None)
        if cfg:
            try:
                cfg.set("input_section_visible", self._input_section_visible)
            except Exception:
                pass
        self._update_input_section_ui()

    def _update_input_section_ui(self, skip_resize: bool = False):
        visible = getattr(self, "_input_section_visible", True)
        if hasattr(self, "input_container"):
            self.input_container.setVisible(visible)
        if hasattr(self, "input_section_toggle"):
            self.input_section_toggle.setIcon(
                get_svg_icon("chevron_up" if visible else "chevron_down", color="#cbd5e1", size=13)
            )
            self.input_section_toggle.setToolTip(
                "Thu gọn phần nhập tiếng Việt" if visible else "Mở rộng phần nhập tiếng Việt"
            )
        if hasattr(self, "card") and self.card.layout():
            self.card.layout().activate()
        if self.layout():
            self.layout().activate()
        self.updateGeometry()

        if getattr(self, "_detached_mode", False):
            min_h = 240 if not visible else 360
            self.setMinimumSize(420, min_h)
            if not skip_resize:
                compact_h = 240 if not visible else getattr(self, "_detached_height", 460)
                self.resize(self.width(), compact_h)

    def _adjust_vn_input_height(self):
        if not hasattr(self, "vn_input") or not self.vn_input:
            return
        doc = self.vn_input.document()
        vp_width = self.vn_input.viewport().width()
        if vp_width > 0:
            doc.setTextWidth(vp_width)
        doc_height = doc.size().height()
        target_h = max(56, min(int(doc_height + 22), 160))

        if hasattr(self, "char_count_label"):
            count = len(self.vn_input.toPlainText())
            self.char_count_label.setText(f"{count}/2000")
            if count > 2000:
                self.char_count_label.setStyleSheet("color: #ef4444; font: 10px 'Segoe UI';")
            else:
                self.char_count_label.setStyleSheet("color: #64748b; font: 10px 'Segoe UI';")

        old_h = self.vn_input.height()
        if old_h != target_h:
            self.vn_input.setFixedHeight(target_h)
            self.vn_input.updateGeometry()
            if hasattr(self, "input_container"):
                self.input_container.updateGeometry()
            if hasattr(self, "card") and self.card.layout():
                self.card.layout().activate()
            if self.layout():
                self.layout().activate()
            self.updateGeometry()
            if getattr(self, "_detached_mode", False):
                compact_h = max(self.minimumHeight(), self.card.layout().sizeHint().height())
                self.resize(self.width(), compact_h)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._adjust_vn_input_height()

    def _scroll_to_bottom(self, text_edit=None):
        """Tự động cuộn tới nội dung mới nhất ở dưới cùng."""
        targets = [text_edit] if text_edit else [self.caption_en_view, self.caption_vi_view]
        for t in targets:
            if t is not None:
                self._apply_scroll_to_bottom(t)
                QTimer.singleShot(0, lambda target=t: self._apply_scroll_to_bottom(target))
                QTimer.singleShot(50, lambda target=t: self._apply_scroll_to_bottom(target))

    def _apply_scroll_to_bottom(self, target):
        try:
            if target is None:
                return
            target.moveCursor(QTextCursor.End)
            target.ensureCursorVisible()
            bar = target.verticalScrollBar()
            if bar is not None:
                bar.setValue(bar.maximum())
        except Exception:
            pass

    def _smart_scroll(self, text_edit, threshold: int = 60):
        """Tự động cuộn tới nội dung mới nhất."""
        self._scroll_to_bottom(text_edit)

    @staticmethod
    def _is_vietnamese(text: str) -> bool:
        return bool(re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', (text or "").lower()))

    def _render_final_caption_lines(self):
        """Render lại toàn bộ danh sách câu đã chốt cho cả 2 cột EN và VI."""
        for view, lines, attr in [
            (self.caption_en_view, self._caption_en_lines, "_en_interim_start_pos"),
            (self.caption_vi_view, self._caption_vi_lines, "_vi_interim_start_pos"),
        ]:
            view.setUpdatesEnabled(False)
            view.setPlainText("\n".join(lines))
            cursor = QTextCursor(view.document())
            cursor.select(QTextCursor.Document)
            block_format = QTextBlockFormat()
            block_format.setLineHeight(155, QTextBlockFormat.ProportionalHeight)
            cursor.mergeBlockFormat(block_format)

            c = view.textCursor()
            c.movePosition(QTextCursor.End)
            view.setTextCursor(c)
            setattr(self, attr, c.position())
            view.setUpdatesEnabled(True)
            self._scroll_to_bottom(view)
        self._has_interim = False

    def _update_interim_lines(self):
        """Cập nhật mượt mà câu nháp trong cả 2 cột EN và VI tại chỗ mà không dựng lại toàn bộ tài liệu."""
        for view, text, attr, lines in [
            (self.caption_en_view, getattr(self, "_live_en_partial", ""), "_en_interim_start_pos", self._caption_en_lines),
            (self.caption_vi_view, getattr(self, "_live_vi_partial", ""), "_vi_interim_start_pos", self._caption_vi_lines),
        ]:
            start_pos = getattr(self, attr, 0)
            c = view.textCursor()
            c.beginEditBlock()
            c.setPosition(start_pos)
            c.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
            prefix = "\n" if (lines and start_pos > 0) else ""
            c.insertText(f"{prefix}{text}")
            c.endEditBlock()

            c_end = view.textCursor()
            c_end.movePosition(QTextCursor.End)
            view.setTextCursor(c_end)
            view.ensureCursorVisible()
            bar = view.verticalScrollBar()
            if bar is not None:
                bar.setValue(bar.maximum())
        self._has_interim = True

    def _on_caption_update(self, payload: dict):
        source = (payload.get("source_text") or "").strip()
        target = (payload.get("target_text") or payload.get("display_text") or "").strip()
        source_lang = (payload.get("source_lang") or "en").strip()
        is_final = payload.get("is_final", True)
        if not source and not target:
            return

        # Content guard: đảm bảo tiếng Việt vào cột VI, tiếng Anh vào cột EN
        if self._is_vietnamese(source) and not self._is_vietnamese(target):
            source, target = target, source
            source_lang = "en"

        timestamp = time.strftime("[%H:%M:%S] ")

        if is_final:
            self._has_interim = False
            prev_en = getattr(self, "_live_en_partial", "")
            self._live_en_partial = ""
            self._live_vi_partial = ""

            en_raw = source if source_lang == "en" else target
            vi_raw = target if source_lang == "en" else source

            if not en_raw and prev_en and not self._is_vietnamese(prev_en):
                en_raw = prev_en

            if self._is_vietnamese(en_raw):
                if not vi_raw or vi_raw == "...":
                    vi_raw = en_raw
                en_raw = prev_en if (prev_en and not self._is_vietnamese(prev_en)) else ""

            # Check if this is an update of the last finalized line
            updated = False
            for idx in range(len(self._caption_en_lines) - 1, max(-1, len(self._caption_en_lines) - 4), -1):
                existing_en = self._caption_en_lines[idx]
                clean_en = re.sub(r"^\[\d{2}:\d{2}:\d{2}\]\s*", "", existing_en)
                if en_raw and clean_en == en_raw:
                    if vi_raw:
                        prefix_match = re.match(r"^(\[\d{2}:\d{2}:\d{2}\]\s*)", existing_en)
                        pfx = prefix_match.group(1) if prefix_match else timestamp
                        self._caption_vi_lines[idx] = f"{pfx}{vi_raw}"
                        updated = True
                    break

            if not updated:
                en_line = f"{timestamp}{en_raw}" if en_raw else ""
                vi_line = f"{timestamp}{vi_raw}" if vi_raw else f"{timestamp}..."
                self._caption_en_lines.append(en_line)
                self._caption_vi_lines.append(vi_line)
                self._caption_lines.append(en_line or vi_line)

            if len(self._caption_en_lines) > 120:
                self._caption_en_lines = self._caption_en_lines[-120:]
                self._caption_vi_lines = self._caption_vi_lines[-120:]
                self._caption_lines = self._caption_lines[-120:]

            self._render_final_caption_lines()
        else:
            if self._is_vietnamese(source):
                self._live_vi_partial = f"{timestamp}{source}"
                self._live_en_partial = f"{timestamp}{target}" if target else ""
            elif source_lang == "en":
                self._live_en_partial = f"{timestamp}{source}"
                self._live_vi_partial = f"{timestamp}{target}" if target else f"{timestamp}..."
            else:
                self._live_en_partial = f"{timestamp}{target}" if target else f"{timestamp}..."
                self._live_vi_partial = f"{timestamp}{source}"

            self._update_interim_lines()

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
        if capturing:
            self.status_dot.setStyleSheet("background: #22c55e; border-radius: 3px;")
            self.status_label.setText("Listening")
            self.status_label.setStyleSheet("color: #4ade80; font: 600 11px 'Segoe UI';")
            self.pause_btn.setIcon(get_svg_icon("pause", color="#ef4444", size=18))
            self.pause_btn.setText("Pause")
            self.pause_btn.setToolTip("Tạm dừng thu âm / dịch (Ctrl+Shift+T)")
            self.pause_btn.setStyleSheet("""
                QToolButton {
                    background: rgba(239, 68, 68, 0.16);
                    border: 1px solid rgba(239, 68, 68, 0.4);
                    border-radius: 10px;
                    color: #fca5a5;
                    font: 600 10px "Segoe UI";
                    padding: 4px 2px;
                }
                QToolButton:hover {
                    background: rgba(239, 68, 68, 0.3);
                }
            """)
        else:
            self.status_dot.setStyleSheet("background: #f59e0b; border-radius: 3px;")
            self.status_label.setText("Paused")
            self.status_label.setStyleSheet("color: #f59e0b; font: 600 11px 'Segoe UI';")
            self.pause_btn.setIcon(get_svg_icon("play", color="#38bdf8", size=18))
            self.pause_btn.setText("Resume")
            self.pause_btn.setToolTip("Tiếp tục thu âm / dịch (Ctrl+Shift+T)")
            self.pause_btn.setStyleSheet("""
                QToolButton {
                    background: rgba(56, 189, 248, 0.16);
                    border: 1px solid rgba(56, 189, 248, 0.4);
                    border-radius: 10px;
                    color: #7dd3fc;
                    font: 600 10px "Segoe UI";
                    padding: 4px 2px;
                }
                QToolButton:hover {
                    background: rgba(56, 189, 248, 0.3);
                }
            """)

    def _on_caption_enabled_update(self, enabled: bool):
        self._caption_visible = enabled
        detached = getattr(self, "_detached_mode", False)
        if detached:
            self.caption_title.setText("LIVE CAPTION (ĐÃ TÁCH)")
            self.caption_title.setVisible(False)
            self.caption_section_toggle.setVisible(False)
            if hasattr(self, "caption_section_widget"):
                self.caption_section_widget.setVisible(False)
        else:
            self.caption_title.setText("LIVE CAPTION")
            self.caption_section_toggle.setVisible(True)
            if hasattr(self, "caption_section_widget"):
                self.caption_section_widget.setVisible(enabled)
            self.caption_section_toggle.setIcon(get_svg_icon("chevron_up" if enabled else "chevron_down", color="#cbd5e1", size=13))
            self.caption_section_toggle.setToolTip("Thu gọn bảng Live Caption" if enabled else "Mở rộng bảng Live Caption")

            if not enabled:
                min_h = 200 if not getattr(self, "_input_section_visible", True) else 300
                self.setMinimumSize(420, min_h)
                self.setMaximumHeight(360 if getattr(self, "_input_section_visible", True) else 220)
                compact_h = 200 if not getattr(self, "_input_section_visible", True) else getattr(self, "_detached_height", 300)
                self.resize(self.width(), compact_h)
            else:
                self.setMaximumHeight(16777215)
                self.setMinimumSize(460, 520)
                restored_h = getattr(self, "_attached_size", None) and self._attached_size.height() or 720
                if restored_h < 520:
                    restored_h = 720
                self.resize(self.width(), restored_h)


        if enabled:
            self.caption_btn.setStyleSheet("""
                QToolButton {
                    background: rgba(34, 197, 94, 0.16);
                    border: 1px solid rgba(34, 197, 94, 0.4);
                    border-radius: 10px;
                    color: #86efac;
                    font: 600 10px "Segoe UI";
                    padding: 4px 2px;
                }
                QToolButton:hover {
                    background: rgba(34, 197, 94, 0.25);
                }
            """)
        else:
            self.caption_btn.setStyleSheet("""
                QToolButton {
                    background: rgba(255, 255, 255, 0.04);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 10px;
                    color: #64748b;
                    font: 600 10px "Segoe UI";
                    padding: 4px 2px;
                }
            """)

    def _on_summary_enabled_update(self, enabled: bool):
        self._summary_enabled = enabled
        self.summary_toggle_btn.setIcon(get_svg_icon("pause" if enabled else "play", color="#cbd5e1", size=13))
        self.summary_toggle_btn.setToolTip("Tạm dừng AI Summary" if enabled else "Tiếp tục AI Summary")
        if enabled:
            self.summary_toggle_btn.setStyleSheet(self._button_state_style("#22c55e", "#052e16", "#4ade80", 26))
            self.summary_view.setPlaceholderText("AI summary will update during the meeting...")
        else:
            self.summary_toggle_btn.setStyleSheet(self._button_state_style("#475569", "#e2e8f0", "#64748b", 26))
            self.summary_view.setPlaceholderText("AI summary is paused.")

    def load_session_view(self, transcript_lines: list[str], summary_text: str):
        self._caption_lines = list(transcript_lines or [])
        self._caption_en_lines = list(transcript_lines or [])
        self._caption_vi_lines = [""] * len(self._caption_en_lines)
        self._render_final_caption_lines()
        self.summary_view.setPlainText((summary_text or "").strip())

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
            r"^[\s\u200b\u200c\u200d\ufeff]*(ðŸ”Š|ðŸ”ˆ|ðŸ”‰|ðŸ“¢|ðŸ“£|ðŸŽ¤|ðŸŽ™ï¸|ðŸŽ™|ðŸ—£ï¸|ðŸ—£)+\s*",
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

