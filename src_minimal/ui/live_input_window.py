import logging
import re
import time

from PyQt5.QtCore import QPoint, Qt, QTimer, pyqtSignal
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

try:
    from src_minimal.ui.icons import get_svg_icon, make_icon_button
except ImportError:
    from src.ui.icons import get_svg_icon, make_icon_button

logger = logging.getLogger(__name__)


class LiveInputWindow(QWidget):
    """
    Independent VN -> EN composer.
    """
    caption_signal = pyqtSignal(dict)
    # summary_signal = pyqtSignal(str)
    capture_state_signal = pyqtSignal(bool)
    caption_enabled_signal = pyqtSignal(bool)
    # summary_enabled_signal = pyqtSignal(bool)

    def __init__(self, app_ref):
        super().__init__(None)
        self.app_ref = app_ref
        self.target_pos = None
        self._dragging = False
        self._drag_pos = QPoint()
        self._last_reply_payload = {}
        self._caption_en_lines = []
        self._caption_vi_lines = []
        self._live_en_partial = ""
        self._live_vi_partial = ""
        self._caption_lines = []  # backward compatibility
        self._caption_visible = True
        self._detached_mode = False
        self._en_interim_start_pos = 0
        self._vi_interim_start_pos = 0
        self._has_interim = False
        cfg = getattr(self.app_ref, "config", None)
        self._input_section_visible = bool(cfg.get("input_section_visible", True)) if cfg else True
        # self._summary_enabled = True
        self._build_ui()
        self.caption_signal.connect(self._on_caption_update)
        # self.summary_signal.connect(self._on_summary_update)
        self.capture_state_signal.connect(self._on_capture_state_update)
        self.caption_enabled_signal.connect(self._on_caption_enabled_update)
        # self.summary_enabled_signal.connect(self._on_summary_enabled_update)

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
        header.setSpacing(8)
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.title_label = QLabel("Live Translator AI")
        self.title_label.setObjectName("titleLabel")
        self.status_label = QLabel("Listening")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.status_label)
        header.addLayout(title_box, 1)

        # Unified window control buttons (28x28)
        self.hide_btn = make_icon_button(
            "shrink",
            "Thu nhỏ về thanh điều khiển nổi (Pill)",
            self.app_ref._minimize_to_floating,
            color="#795548",
            btn_size=28,
            icon_size=14,
            object_name="iconButton",
            parent=self.card,
        )
        self.min_btn = make_icon_button(
            "minus",
            "Thu nhỏ cửa sổ xuống Taskbar",
            self.showMinimized,
            color="#795548",
            btn_size=28,
            icon_size=14,
            object_name="iconButton",
            parent=self.card,
        )
        self.close_btn = make_icon_button(
            "close",
            "Ẩn cửa sổ",
            self.hide,
            color="#795548",
            btn_size=28,
            icon_size=14,
            object_name="closeButton",
            parent=self.card,
        )
        header.addWidget(self.hide_btn)
        header.addWidget(self.min_btn)
        header.addWidget(self.close_btn)
        layout.addLayout(header)

        # 2026 Minimalist Action Toolbar (Icon-only, Grouped)
        action_toolbar = QHBoxLayout()
        action_toolbar.setSpacing(6)

        self.pause_btn = make_icon_button(
            "pause",
            "Tạm dừng thu âm / dịch (Ctrl+Shift+T)",
            self.app_ref._toggle_capture,
            color="#1C1B1F",
            btn_size=34,
            icon_size=16,
            object_name="bottomButton",
            parent=self.card,
        )
        self.detach_btn = make_icon_button(
            "detach",
            "Tách bảng dịch thành cửa sổ riêng",
            self.app_ref._toggle_detached_caption_panel,
            color="#1C1B1F",
            btn_size=34,
            icon_size=16,
            object_name="bottomButton",
            parent=self.card,
        )
        self.caption_btn = make_icon_button(
            "subtitles",
            "Bật / Tắt dịch phụ đề (Ctrl+Shift+C)",
            self.app_ref._toggle_caption,
            color="#1C1B1F",
            btn_size=34,
            icon_size=16,
            object_name="bottomButton",
            parent=self.card,
        )
        self.mark_btn = make_icon_button(
            "target",
            "Chọn ô nhập Teams / App mục tiêu (Ctrl+Shift+V)",
            self.app_ref._mark_target_input,
            color="#1C1B1F",
            btn_size=34,
            icon_size=16,
            object_name="bottomButton",
            parent=self.card,
        )

        for btn in [self.pause_btn, self.detach_btn, self.caption_btn, self.mark_btn]:
            action_toolbar.addWidget(btn)

        # Subtle divider
        toolbar_sep = QFrame(self.card)
        toolbar_sep.setFrameShape(QFrame.VLine)
        toolbar_sep.setFrameShadow(QFrame.Plain)
        toolbar_sep.setStyleSheet("color: #E5D8CD; max-height: 20px; margin: 0 3px;")
        action_toolbar.addWidget(toolbar_sep)

        self.setup_audio_btn = make_icon_button(
            "headphones",
            "Nghe loa & Dịch (Cable Output)",
            self.app_ref.manual_setup_audio,
            color="#1C1B1F",
            btn_size=34,
            icon_size=16,
            object_name="bottomButton",
            parent=self.card,
        )
        self.restore_audio_btn = make_icon_button(
            "speaker",
            "Khôi phục loa mặc định",
            self.app_ref.manual_restore_audio,
            color="#1C1B1F",
            btn_size=34,
            icon_size=16,
            object_name="bottomButton",
            parent=self.card,
        )
        self.receive_tts_btn = make_icon_button(
            "radio",
            "Nhận dịch ASR qua TTS",
            self._toggle_receive_tts,
            color="#1C1B1F",
            btn_size=34,
            icon_size=16,
            object_name="bottomButton",
            parent=self.card,
        )

        for btn in [self.setup_audio_btn, self.restore_audio_btn, self.receive_tts_btn]:
            action_toolbar.addWidget(btn)

        action_toolbar.addStretch(1)
        layout.addLayout(action_toolbar)

        caption_header = QHBoxLayout()
        caption_header.setSpacing(6)
        self.caption_title = QLabel("LIVE TRANSLATION")
        self.caption_title.setObjectName("sectionHeader")
        caption_header.addWidget(self.caption_title)
        caption_header.addStretch(1)
        self.caption_section_toggle = make_icon_button(
            "chevron_up",
            "Thu gọn bảng Live Caption",
            self.toggle_caption_section,
            color="#795548",
            btn_size=26,
            icon_size=13,
            object_name="miniButton",
            parent=self.card,
        )
        caption_header.addWidget(self.caption_section_toggle)
        layout.addLayout(caption_header)

        # Split side-by-side panel for live caption (EN Left, VI Right)
        self.caption_container = QWidget(self.card)
        self.caption_layout = QHBoxLayout(self.caption_container)
        self.caption_layout.setContentsMargins(0, 0, 0, 0)
        self.caption_layout.setSpacing(8)

        self.caption_en_view = QTextEdit(self.caption_container)
        self.caption_en_view.setReadOnly(True)
        self.caption_en_view.setObjectName("captionBox")
        self.caption_en_view.setPlaceholderText("English caption will appear here...")
        self.caption_en_view.setFont(QFont("Segoe UI", 13))

        self.caption_vi_view = QTextEdit(self.caption_container)
        self.caption_vi_view.setReadOnly(True)
        self.caption_vi_view.setObjectName("captionBox")
        self.caption_vi_view.setPlaceholderText("Tiếng Việt dịch ở đây...")
        self.caption_vi_view.setFont(QFont("Segoe UI", 13))

        self.caption_layout.addWidget(self.caption_en_view, 1)
        self.caption_layout.addWidget(self.caption_vi_view, 1)
        layout.addWidget(self.caption_container, 1)

        # Create self.caption_view dummy for compatibility
        self.caption_view = self.caption_en_view

        # Instantiate summary components (Removed AI summary)
        self.summary_title = None
        self.summary_toggle_btn = None
        self.summary_view = None

        # Nhập tiếng việt section
        input_header = QHBoxLayout()
        input_header.setSpacing(6)
        self.input_title = QLabel("NHẬP TIẾNG VIỆT")
        self.input_title.setObjectName("sectionHeader")
        input_header.addWidget(self.input_title)
        input_header.addStretch(1)
        self.input_section_toggle = make_icon_button(
            "chevron_up",
            "Thu gọn phần nhập tiếng Việt",
            self.toggle_input_section,
            color="#795548",
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

        self.vn_input = QTextEdit(self.input_container)
        self.vn_input.setObjectName("mainInput")
        self.vn_input.setPlaceholderText("Nhập nội dung cần dịch / phản hồi...")
        self.vn_input.setFont(QFont("Segoe UI", 11))
        self.vn_input.textChanged.connect(self._adjust_vn_input_height)
        input_layout.addWidget(self.vn_input)

        # Cleaned up button row (2026 Minimalist Icon Buttons)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.clear_btn = make_icon_button("trash", "Xóa nội dung nhập", self.vn_input.clear, color="#795548", btn_size=34, icon_size=16, object_name="toolbarButton", parent=self.card)
        self.speak_btn = make_icon_button("volume_1", "Phát âm câu trả lời tiếng Anh (Speak EN)", self.speak_reply, color="#795548", btn_size=34, icon_size=16, object_name="toolbarButton", parent=self.card)
        self.translate_btn = make_icon_button("send", "Dịch sang tiếng Anh & Gõ tự động vào Teams (Ctrl+Enter)", self.translate_and_inject, color="#ffffff", btn_size=34, icon_size=16, object_name="primaryButton", parent=self.card)

        # Keep references to removed buttons for backend logic compatibility
        self.reply_btn = QPushButton()
        self.auto_reply_btn = QPushButton()

        btn_row.addWidget(self.clear_btn)
        btn_row.addWidget(self.speak_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(self.translate_btn)
        input_layout.addLayout(btn_row)

        layout.addWidget(self.input_container)

        # Instantiate hidden reply boxes for backend compatibility (not added to layout)
        self.reply_en = QTextEdit()
        self.reply_en.setReadOnly(True)
        self.reply_en.setObjectName("replyBox")
        self.reply_vi = QTextEdit()
        self.reply_vi.setReadOnly(True)
        self.reply_vi.setObjectName("replyBox")

        footer = QHBoxLayout()
        footer.addStretch(1)
        footer.addWidget(QSizeGrip(self.card))
        layout.addLayout(footer)

        root.addWidget(self.card)
        self._apply_style()
        self._update_receive_tts_btn(self.app_ref.receive_tts_enabled)
        self._update_input_section_ui(skip_resize=True)
        self._adjust_vn_input_height()

    def _make_button(self, text: str, callback, object_name: str = "toolbarButton") -> QPushButton:
        button = QPushButton(text)
        button.setObjectName(object_name)
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(34)
        button.clicked.connect(callback)
        return button

    def _apply_style(self):
        self.setStyleSheet(
            '''
            #composerCard {
                background: #FAF2EB;
                border: 2px solid #E5D8CD;
                border-radius: 16px;
            }
            #titleLabel {
                color: #1C1B1F;
                font: 800 15px "Segoe UI";
            }
            #statusLabel {
                color: #795548;
                font: 700 11px "Segoe UI";
            }
            #sectionHeader {
                color: #795548;
                font: 800 11px "Segoe UI";
                letter-spacing: 0.5px;
            }
            QTextEdit {
                color: #1C1B1F;
                background: #FFFFFF;
                border: 1px solid #E5D8CD;
                border-radius: 10px;
                padding: 10px;
                selection-background-color: #F3E3D3;
                selection-color: #1C1B1F;
            }
            QTextEdit:focus {
                border: 1.5px solid #795548;
            }
            #mainInput {
                font: 11pt "Segoe UI";
                padding: 8px 12px;
                line-height: 1.4;
            }
            #replyBox {
                color: #1C1B1F;
                background: #FFFFFF;
                border: 1px solid #E5D8CD;
            }
            #captionBox {
                background: #FFFFFF;
                border-color: #E5D8CD;
                font: 700 16px "Segoe UI";
                line-height: 1.5;
            }
            #summaryBox {
                color: #1C1B1F;
                background: #FFFFFF;
                border-color: #E5D8CD;
                font: 500 14px "Segoe UI";
                line-height: 1.45;
            }
            #toolbarButton, #primaryButton, #iconButton, #closeButton, #miniButton, #bottomButton {
                background: #F3E3D3;
                border: 1px solid #E5D8CD;
                border-radius: 8px;
                padding: 0px;
            }
            #primaryButton {
                background: #795548;
                border-color: #795548;
            }
            #miniButton {
                min-width: 26px;
                max-width: 26px;
                min-height: 26px;
                max-height: 26px;
                background: #FFFFFF;
            }
            #bottomButton, #toolbarButton {
                min-width: 34px;
                max-width: 34px;
                min-height: 34px;
                max-height: 34px;
            }
            #iconButton, #closeButton {
                min-width: 28px;
                max-width: 28px;
                min-height: 28px;
                max-height: 28px;
            }
            #toolbarButton:hover, #iconButton:hover, #miniButton:hover, #bottomButton:hover {
                background: #E5D8CD;
                border-color: #C8B9AD;
            }
            #primaryButton:hover {
                background: #5D3E35;
                border-color: #5D3E35;
            }
            #closeButton:hover {
                background: #E8D5C4;
            }
            QToolTip {
                background: #FAF2EB;
                color: #1C1B1F;
                border: 1px solid #E5D8CD;
                border-radius: 6px;
                padding: 4px 8px;
                font: 600 11px "Segoe UI";
            }
            QScrollBar:vertical {
                background: transparent;
                width: 9px;
            }
            QScrollBar::handle:vertical {
                background: #E5D8CD;
                border-radius: 4px;
                min-height: 34px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            '''
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
        pass

    def set_capture_state(self, capturing: bool):
        self.capture_state_signal.emit(bool(capturing))

    def set_caption_enabled(self, enabled: bool):
        self.caption_enabled_signal.emit(bool(enabled))

    def set_summary_enabled(self, enabled: bool):
        pass

    def set_detached_mode(self, detached: bool):
        was_detached = getattr(self, "_detached_mode", False)
        self._detached_mode = bool(detached)
        if detached:
            self.detach_btn.setIcon(get_svg_icon("attach", color="#FFFFFF", size=16))
            self.detach_btn.setToolTip("Gắn lại bảng dịch vào panel chính")
            self.detach_btn.setStyleSheet(self._button_state_style("#795548", "#FFFFFF", "#795548"))
        else:
            self.detach_btn.setIcon(get_svg_icon("detach", color="#1C1B1F", size=16))
            self.detach_btn.setToolTip("Tách bảng dịch thành cửa sổ riêng")
            self.detach_btn.setStyleSheet(self._button_state_style("#F3E3D3", "#1C1B1F", "#E5D8CD"))

        if detached:
            if not was_detached and self.height() > 400:
                self._attached_size = self.size()
            self.caption_title.setText("LIVE TRANSLATION (ĐÃ TÁCH)")
            self.caption_title.setVisible(False)
            self.caption_section_toggle.setVisible(False)
            if hasattr(self, "caption_container"):
                self.caption_container.setVisible(False)
            self.caption_en_view.setVisible(False)
            self.caption_vi_view.setVisible(False)

            min_h = 130 if not getattr(self, "_input_section_visible", True) else 240
            self.setMinimumSize(420, min_h)
            self.setMaximumHeight(380 if getattr(self, "_input_section_visible", True) else 180)

            self.card.layout().activate()
            self.layout().activate()
            self.updateGeometry()

            compact_h = 250 if getattr(self, "_input_section_visible", True) else 140
            self.resize(self.width(), compact_h)
        else:
            self.setMaximumHeight(16777215)
            if was_detached and self.height() <= 450:
                self._detached_height = self.height()
            self.caption_title.setText("LIVE TRANSLATION")
            self.caption_title.setVisible(self._caption_visible)
            self.caption_section_toggle.setVisible(True)
            if hasattr(self, "caption_container"):
                self.caption_container.setVisible(self._caption_visible)
            self.caption_en_view.setVisible(self._caption_visible)
            self.caption_vi_view.setVisible(self._caption_visible)
            self.setMinimumSize(460, 660)

            self.card.layout().activate()
            self.layout().activate()
            self.updateGeometry()

            restored_h = getattr(self, "_attached_size", None) and self._attached_size.height() or 880
            if restored_h < 660:
                restored_h = 880
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
                get_svg_icon("chevron_up" if visible else "chevron_down", color="#795548", size=13)
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
            min_h = 130 if not visible else 200
            self.setMinimumSize(420, min_h)
            if not skip_resize:
                compact_h = max(min_h, self.card.layout().sizeHint().height())
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
        target = text_edit or self.caption_en_view
        self._apply_scroll_to_bottom(target)
        QTimer.singleShot(0, lambda: self._apply_scroll_to_bottom(target))
        QTimer.singleShot(50, lambda: self._apply_scroll_to_bottom(target))

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
        for view, lines, attr in [(self.caption_en_view, self._caption_en_lines, "_en_interim_start_pos"),
                                   (self.caption_vi_view, self._caption_vi_lines, "_vi_interim_start_pos")]:
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
        for view, text, attr, lines in [(self.caption_en_view, getattr(self, "_live_en_partial", ""), "_en_interim_start_pos", self._caption_en_lines),
                                         (self.caption_vi_view, getattr(self, "_live_vi_partial", ""), "_vi_interim_start_pos", self._caption_vi_lines)]:
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
        target = (payload.get("target_text") or "").strip()
        source_lang = (payload.get("source_lang") or "en").strip()
        is_final = payload.get("is_final", True)
        if not source and not target:
            return

        # Content guard: đảm bảo tuyệt đối tiếng Việt vào cột VI, tiếng Anh vào cột EN
        if self._is_vietnamese(source) and not self._is_vietnamese(target):
            source, target = target, source
            source_lang = "en"

        if is_final:
            self._has_interim = False
            prev_en_partial = getattr(self, "_live_en_partial", "")
            self._live_en_partial = ""
            self._live_vi_partial = ""

            en_line = source if source_lang == "en" else target
            vi_line = target if source_lang == "en" else source

            # Nếu en_line rỗng nhưng có prev_en_partial hợp lệ
            if not en_line and prev_en_partial and not self._is_vietnamese(prev_en_partial):
                en_line = prev_en_partial

            # Chắn an toàn: nếu en_line bị nhiễm tiếng Việt, đẩy sang vi_line
            if self._is_vietnamese(en_line):
                if not vi_line or vi_line == "...":
                    vi_line = en_line
                en_line = prev_en_partial if (prev_en_partial and not self._is_vietnamese(prev_en_partial)) else ""

            # Check if this is an update (translation arrival) for a recently finalized line
            updated = False
            for idx in range(len(self._caption_en_lines) - 1, max(-1, len(self._caption_en_lines) - 4), -1):
                if en_line and self._caption_en_lines[idx] == en_line:
                    if vi_line:
                        self._caption_vi_lines[idx] = vi_line
                        updated = True
                    elif not self._caption_vi_lines[idx] or self._caption_vi_lines[idx] == "...":
                        self._caption_vi_lines[idx] = "..."
                        updated = True
                    break

            if not updated:
                self._caption_en_lines.append(en_line)
                self._caption_vi_lines.append(vi_line if vi_line else "...")

            # Keep max 120 lines
            if len(self._caption_en_lines) > 120:
                self._caption_en_lines = self._caption_en_lines[-120:]
                self._caption_vi_lines = self._caption_vi_lines[-120:]

            self._render_final_caption_lines()
        else:
            if self._is_vietnamese(source):
                self._live_vi_partial = source
                self._live_en_partial = target if target else ""
            elif source_lang == "en":
                self._live_en_partial = source
                self._live_vi_partial = target if target else "..."
            else:
                self._live_en_partial = target if target else "..."
                self._live_vi_partial = source

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
        self.status_label.setText("Listening" if capturing else "Paused")
        if capturing:
            self.pause_btn.setIcon(get_svg_icon("pause", color="#FFFFFF", size=16))
            self.pause_btn.setToolTip("Tạm dừng thu âm / dịch (Pause)")
            self.pause_btn.setStyleSheet(self._button_state_style("#D32F2F", "#FFFFFF", "#D32F2F"))
        else:
            self.pause_btn.setIcon(get_svg_icon("play", color="#FFFFFF", size=16))
            self.pause_btn.setToolTip("Tiếp tục thu âm / dịch (Resume)")
            self.pause_btn.setStyleSheet(self._button_state_style("#795548", "#FFFFFF", "#795548"))

    def _on_caption_enabled_update(self, enabled: bool):
        self._caption_visible = enabled
        detached = getattr(self, "_detached_mode", False)
        if detached:
            self.caption_title.setText("LIVE TRANSLATION (ĐÃ TÁCH)")
            self.caption_title.setVisible(False)
            self.caption_section_toggle.setVisible(False)
            if hasattr(self, "caption_container"):
                self.caption_container.setVisible(False)
            self.caption_en_view.setVisible(False)
            self.caption_vi_view.setVisible(False)
        else:
            self.caption_title.setText("LIVE TRANSLATION")
            self.caption_title.setVisible(enabled)
            self.caption_section_toggle.setVisible(True)
            if hasattr(self, "caption_container"):
                self.caption_container.setVisible(enabled)
            self.caption_en_view.setVisible(enabled)
            self.caption_vi_view.setVisible(enabled)
            self.caption_section_toggle.setIcon(get_svg_icon("chevron_up" if enabled else "chevron_down", color="#795548", size=13))
            self.caption_section_toggle.setToolTip("Thu gọn bảng Live Caption" if enabled else "Mở rộng bảng Live Caption")

            if not enabled:
                min_h = 130 if not getattr(self, "_input_section_visible", True) else 240
                self.setMinimumSize(420, min_h)
                self.setMaximumHeight(380 if getattr(self, "_input_section_visible", True) else 180)
                compact_h = 250 if getattr(self, "_input_section_visible", True) else 140
                self.resize(self.width(), compact_h)
            else:
                self.setMaximumHeight(16777215)
                self.setMinimumSize(460, 660)
                restored_h = getattr(self, "_attached_size", None) and self._attached_size.height() or 880
                if restored_h < 660:
                    restored_h = 880
                self.resize(self.width(), restored_h)

        if hasattr(self, "card") and self.card.layout():
            self.card.layout().activate()
        if self.layout():
            self.layout().activate()
        self.updateGeometry()

        if enabled:
            self.caption_btn.setStyleSheet(self._button_state_style("#22c55e", "#052e16", "#4ade80"))
        else:
            self.caption_btn.setStyleSheet(self._button_state_style("#FAF2EB", "#1C1B1F", "#E5D8CD"))

    def _on_summary_enabled_update(self, enabled: bool):
        pass

    def load_session_view(self, transcript_lines: list[str], summary_text: str):
        self._caption_en_lines = []
        self._caption_vi_lines = []
        
        for line in (transcript_lines or []):
            line_str = line.strip()
            if not line_str:
                continue
                
            content_part = line_str
            if line_str.startswith("[") and "]" in line_str:
                idx = line_str.find("]")
                content_part = line_str[idx+1:].strip()
                
            if "SRC: " in content_part:
                text = content_part.replace("SRC: ", "").strip()
                self._caption_en_lines.append(text)
            elif "VI : " in content_part:
                text = content_part.replace("VI : ", "").strip()
                self._caption_vi_lines.append(text)
            elif "EN: " in content_part:
                text = content_part.replace("EN: ", "").strip()
                self._caption_en_lines.append(text)
            elif "VI: " in content_part:
                text = content_part.replace("VI: ", "").strip()
                self._caption_vi_lines.append(text)
            else:
                self._caption_vi_lines.append(line_str)

        self._render_final_caption_lines()

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

    def _toggle_receive_tts(self):
        enabled = not getattr(self.app_ref, "receive_tts_enabled", True)
        self.app_ref.receive_tts_enabled = enabled
        self._update_receive_tts_btn(enabled)

    def _update_receive_tts_btn(self, enabled: bool):
        if enabled:
            self.receive_tts_btn.setIcon(get_svg_icon("radio", color="#FFFFFF", size=16))
            self.receive_tts_btn.setToolTip("Nhận dịch ASR qua TTS: ĐANG BẬT (Bấm để tắt)")
            self.receive_tts_btn.setStyleSheet(self._button_state_style("#795548", "#FFFFFF", "#795548"))
        else:
            self.receive_tts_btn.setIcon(get_svg_icon("volume_x", color="#795548", size=16))
            self.receive_tts_btn.setToolTip("Nhận dịch ASR qua TTS: ĐÃ TẮT (Bấm để bật)")
            self.receive_tts_btn.setStyleSheet(self._button_state_style("#F3E3D3", "#1C1B1F", "#E5D8CD"))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.y() <= 56:
            self._dragging = True
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and bool(event.buttons() & Qt.LeftButton):
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

