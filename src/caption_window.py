"""
Caption window: independent, resizable transcript and summary surface.
"""
import datetime
import logging
from pathlib import Path

from PyQt5.QtCore import QPoint, QRect, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QTextCursor
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizeGrip,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from src.ui.icons import get_svg_icon, make_icon_button
except ImportError:
    from src_minimal.ui.icons import get_svg_icon, make_icon_button

logger = logging.getLogger(__name__)


class CaptionWindow(QWidget):
    update_signal = pyqtSignal(dict)
    summary_signal = pyqtSignal(str)

    def __init__(self, config_manager=None, parent=None, app_ref=None):
        super().__init__(parent)
        self.config = config_manager
        self.app_ref = app_ref
        self._display_mode = "both"
        if self.config:
            self._display_mode = self.config.get("display_mode", "both")
        self._history = []
        self._current_text = {"source": "", "translated": "", "lang": ""}
        self._history_dir = Path.home() / ".teams-translator" / "history"
        self._history_dir.mkdir(parents=True, exist_ok=True)
        self._session_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self._history_file = self._history_dir / f"session-{self._session_id}.log"
        self._summary_file = self._history_dir / f"session-{self._session_id}-summary.txt"
        self._summary_collapsed = False
        self._summary_enabled = False
        self._dragging = False
        self._drag_pos = QPoint()
        self._idle_seconds = 0
        self._current_interim = None
        self._interim_start_pos = 0
        self._has_interim = False

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
        card_layout.setContentsMargins(14, 10, 14, 10)
        card_layout.setSpacing(8)

        # 1. Window Header
        header = QHBoxLayout()
        header.setSpacing(8)

        self.wave_icon = QLabel()
        self.wave_icon.setPixmap(get_svg_icon("soundwave", color="#38bdf8", size=18).pixmap(18, 18))
        header.addWidget(self.wave_icon)

        self.title_label = QLabel("Live Caption")
        self.title_label.setObjectName("titleLabel")
        header.addWidget(self.title_label)

        self.lang_label = QLabel(self.card)
        self.lang_label.setVisible(False)

        header.addStretch(1)

        self.min_btn = make_icon_button(
            "minus",
            "Thu nhỏ cửa sổ",
            self.showMinimized,
            color="#cbd5e1",
            btn_size=26,
            icon_size=13,
            object_name="iconButton",
            parent=self.card
        )
        self.max_btn = make_icon_button(
            "expand",
            "Phóng to / Khôi phục",
            self._toggle_maximize,
            color="#cbd5e1",
            btn_size=26,
            icon_size=13,
            object_name="iconButton",
            parent=self.card
        )
        self.close_btn = make_icon_button(
            "close",
            "Ẩn cửa sổ Caption",
            self.hide,
            color="#cbd5e1",
            btn_size=26,
            icon_size=13,
            object_name="closeButton",
            parent=self.card
        )
        header.addWidget(self.min_btn)
        header.addWidget(self.max_btn)
        header.addWidget(self.close_btn)
        card_layout.addLayout(header)

        # 2. Filter & Toolbar row
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self.mode_btn_both = QPushButton("EN + VI")
        self.mode_btn_en = QPushButton("English")
        self.mode_btn_vi = QPushButton("Tiếng Việt")
        for btn in [self.mode_btn_both, self.mode_btn_en, self.mode_btn_vi]:
            btn.setObjectName("modePillButton")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(24)
            toolbar.addWidget(btn)

        self.mode_btn_both.clicked.connect(lambda: self.set_display_mode("both"))
        self.mode_btn_en.clicked.connect(lambda: self.set_display_mode("en_only"))
        self.mode_btn_vi.clicked.connect(lambda: self.set_display_mode("vi_only"))

        # Hidden display_mode_btn kept for test_svg_buttons compatibility
        self.display_mode_btn = make_icon_button("languages", "Chế độ hiển thị", self._cycle_display_mode, color="#cbd5e1", btn_size=24, icon_size=12, object_name="iconButton", parent=self.card)
        self.display_mode_btn.setVisible(False)

        toolbar.addSpacing(6)

        # Toggle switch for AI Summary
        self.summary_toggle_switch = QCheckBox("Show AI Summary")
        self.summary_toggle_switch.setObjectName("summaryToggleSwitch")
        self.summary_toggle_switch.setCursor(Qt.PointingHandCursor)
        self.summary_toggle_switch.setChecked(not self._summary_collapsed)
        self.summary_toggle_switch.toggled.connect(self._on_summary_switch_toggled)
        toolbar.addWidget(self.summary_toggle_switch)

        # Hidden summary_toggle kept for test_svg_buttons compatibility
        self.summary_toggle = make_icon_button("sparkles", "Ẩn / Hiện tóm tắt AI", self._toggle_summary, color="#cbd5e1", btn_size=24, icon_size=12, object_name="iconButton", parent=self.card)
        self.summary_toggle.setVisible(False)

        toolbar.addStretch(1)

        self.summary_pause_btn = make_icon_button(
            "pause",
            "Tạm dừng cập nhật AI Summary",
            self._toggle_summary_updates,
            color="#cbd5e1",
            btn_size=26,
            icon_size=13,
            object_name="iconButton",
            parent=self.card
        )
        toolbar.addWidget(self.summary_pause_btn)

        self.new_session_btn = make_icon_button(
            "plus",
            "Bắt đầu phiên mới (New Session)",
            self._new_session,
            color="#cbd5e1",
            btn_size=26,
            icon_size=13,
            object_name="iconButton",
            parent=self.card
        )
        toolbar.addWidget(self.new_session_btn)

        self.history_btn = make_icon_button(
            "history",
            "Xem lịch sử cuộc họp (History)",
            self._open_history,
            color="#cbd5e1",
            btn_size=26,
            icon_size=13,
            object_name="iconButton",
            parent=self.card
        )
        toolbar.addWidget(self.history_btn)

        self.settings_btn = make_icon_button(
            "settings",
            "Cài đặt",
            self._open_settings,
            color="#cbd5e1",
            btn_size=26,
            icon_size=13,
            object_name="iconButton",
            parent=self.card
        )
        toolbar.addWidget(self.settings_btn)

        card_layout.addLayout(toolbar)

        # 3. Live Active Caption Box (Interim Updates)
        self.live_caption_box = QFrame()
        self.live_caption_box.setObjectName("liveCaptionBox")
        live_layout = QVBoxLayout(self.live_caption_box)
        live_layout.setContentsMargins(10, 8, 10, 8)
        live_layout.setSpacing(4)
        
        self.live_en_label = QLabel()
        self.live_en_label.setObjectName("liveEnLabel")
        self.live_en_label.setWordWrap(True)
        self.live_en_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        self.live_vi_label = QLabel()
        self.live_vi_label.setObjectName("liveViLabel")
        self.live_vi_label.setWordWrap(True)
        self.live_vi_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        live_layout.addWidget(self.live_en_label)
        live_layout.addWidget(self.live_vi_label)
        self.live_caption_box.setVisible(False)

        self.history_view = QTextEdit()
        self.history_view.setReadOnly(True)
        self.history_view.setObjectName("historyView")
        self.history_view.setPlaceholderText("Transcript history will appear here...")
        card_layout.addWidget(self.history_view, 4)

        self.summary_view = QTextEdit()
        self.summary_view.setReadOnly(True)
        self.summary_view.setObjectName("summaryView")
        self.summary_view.setPlaceholderText("AI summary will update during the session...")
        card_layout.addWidget(self.summary_view, 2)
        self.summary_view.setVisible(not self._summary_collapsed and self._summary_enabled)

        # 4. Footer row
        footer = QHBoxLayout()
        footer.setContentsMargins(2, 2, 2, 2)
        footer.setSpacing(6)

        self.auto_scroll_dot = QLabel()
        self.auto_scroll_dot.setObjectName("statusDot")
        self.auto_scroll_dot.setFixedSize(7, 7)
        footer.addWidget(self.auto_scroll_dot)

        self.auto_scroll_label = QLabel("Auto-scroll on")
        self.auto_scroll_label.setObjectName("autoScrollLabel")
        footer.addWidget(self.auto_scroll_label)

        footer.addStretch(1)

        self.font_size_combo = QComboBox(self.card)
        self.font_size_combo.setObjectName("fontSizeCombo")
        for fs in [12, 14, 16, 18, 20, 24]:
            self.font_size_combo.addItem(f"Font size: {fs}px", fs)

        current_fs = self._get_font_size()
        for i in range(self.font_size_combo.count()):
            if self.font_size_combo.itemData(i) == current_fs:
                self.font_size_combo.setCurrentIndex(i)
                break
        self.font_size_combo.currentIndexChanged.connect(self._on_font_combo_changed)
        footer.addWidget(self.font_size_combo)

        self.grip = QSizeGrip(self.card)
        footer.addWidget(self.grip)
        card_layout.addLayout(footer)

        root.addWidget(self.card)
        self._apply_style()
        self._update_mode_pill_styles()

        w = self.config.get("caption_width", 720) if self.config else 720
        h = self.config.get("caption_height", 380) if self.config else 380
        self.resize(w, h)

    def _apply_style(self):
        font_size = self._get_font_size()
        self.history_view.setFont(QFont("Segoe UI", font_size))
        self.summary_view.setFont(QFont("Segoe UI", max(10, font_size - 1)))
        self.setStyleSheet(
            """
            #captionCard {
                background: rgba(10, 16, 30, 250);
                border: 1px solid rgba(56, 189, 248, 0.25);
                border-radius: 14px;
            }
            #statusDot {
                background: #22c55e;
                border-radius: 3px;
            }
            #titleLabel {
                color: #f8fafc;
                font: 700 13px "Segoe UI";
            }
            #autoScrollLabel {
                color: #22c55e;
                font: 600 11px "Segoe UI";
            }
            #modePillButton {
                border-radius: 6px;
                padding: 2px 10px;
                font: 600 11px "Segoe UI";
            }
            #summaryToggleSwitch {
                color: #cbd5e1;
                font: 500 11px "Segoe UI";
                spacing: 6px;
            }
            #summaryToggleSwitch::indicator {
                width: 14px;
                height: 14px;
                border-radius: 3px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                background: rgba(255, 255, 255, 0.05);
            }
            #summaryToggleSwitch::indicator:checked {
                background: #2563eb;
                border-color: #3b82f6;
            }
            #fontSizeCombo {
                background: rgba(255, 255, 255, 0.06);
                color: #cbd5e1;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                padding: 2px 8px;
                font: 11px "Segoe UI";
            }
            #fontSizeCombo QAbstractItemView {
                background: #0b1325;
                color: #f8fafc;
                border: 1px solid rgba(56, 189, 248, 0.3);
                selection-background-color: #2563eb;
            }
            #historyView {
                color: #f8fafc;
                background: rgba(8, 14, 26, 220);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                padding: 10px;
                selection-background-color: #2563eb;
            }
            #summaryView {
                color: #dbeafe;
                background: rgba(18, 28, 48, 220);
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 10px;
                padding: 8px;
            }
            #iconButton, #closeButton {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 0px;
            }
            #iconButton:hover {
                background: rgba(255, 255, 255, 0.16);
                border-color: rgba(255, 255, 255, 0.25);
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

    def _update_mode_pill_styles(self):
        active = "background: #2563eb; color: #ffffff; border: 1px solid #3b82f6; border-radius: 6px; font: 600 11px 'Segoe UI'; padding: 2px 10px;"
        inactive = "background: rgba(255, 255, 255, 0.05); color: #94a3b8; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 6px; font: 600 11px 'Segoe UI'; padding: 2px 10px;"
        self.mode_btn_both.setStyleSheet(active if self._display_mode == "both" else inactive)
        self.mode_btn_en.setStyleSheet(active if self._display_mode == "en_only" else inactive)
        self.mode_btn_vi.setStyleSheet(active if self._display_mode == "vi_only" else inactive)

    def set_display_mode(self, mode: str):
        self._display_mode = mode
        if self.config:
            self.config.set("display_mode", mode)
        self._update_mode_pill_styles()
        self._reload_history_display()

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _open_settings(self):
        if self.app_ref and hasattr(self.app_ref, "_open_settings"):
            self.app_ref._open_settings()

    def _on_summary_switch_toggled(self, checked: bool):
        self._summary_collapsed = not checked
        self.summary_view.setVisible(checked)

    def _on_font_combo_changed(self, idx: int):
        fs = self.font_size_combo.itemData(idx)
        if fs and self.config:
            self.config.set("caption_font_size", fs)
        self._apply_style()
        self._reload_history_display()

    def _get_font_size(self) -> int:
        return self.config.get("caption_font_size", 14) if self.config else 14

    def ensure_visible_on_screen(self):
        """Đảm bảo cửa sổ luôn nằm trong vùng hiển thị của ít nhất 1 màn hình khả dụng."""
        rect = self.geometry()
        is_visible = False
        screens = QApplication.screens()
        for screen in screens:
            avail = screen.availableGeometry()
            if avail.intersects(rect):
                inter = avail.intersected(rect)
                if inter.width() >= 100 and inter.height() >= 50:
                    is_visible = True
                    break
        if not is_visible:
            screen = QApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                new_w = min(self.width(), geo.width() - 40)
                new_h = min(self.height(), geo.height() - 80)
                new_x = geo.left() + max(0, (geo.width() - new_w) // 2)
                new_y = max(geo.top(), geo.bottom() - new_h - 36)
                self.resize(new_w, new_h)
                self.move(new_x, new_y)
                self._save_geometry()

    def showEvent(self, event):
        super().showEvent(event)
        self.ensure_visible_on_screen()

    def _load_position(self):
        loaded = False
        if self.config:
            x = self.config.get("caption_x")
            y = self.config.get("caption_y")
            w = self.config.get("caption_width")
            h = self.config.get("caption_height")
            if w and h:
                self.resize(w, h)
            if x is not None and y is not None:
                self.move(x, y)
                loaded = True
        if not loaded:
            screen = QApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                self.move(geo.center().x() - self.width() // 2, geo.bottom() - self.height() - 36)
        self.ensure_visible_on_screen()

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
        self.update_signal.emit(data)

    def set_summary(self, text: str):
        self.summary_signal.emit(text or "")

    def _toggle_summary(self):
        self._summary_collapsed = not self._summary_collapsed
        self.summary_view.setVisible(not self._summary_collapsed)
        self.summary_toggle.setToolTip("Hiện bảng tóm tắt AI" if self._summary_collapsed else "Ẩn bảng tóm tắt AI")

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
        icon_name = "pause" if self._summary_enabled else "play"
        self.summary_pause_btn.setIcon(get_svg_icon(icon_name, color="#cbd5e1", size=14))
        self.summary_pause_btn.setToolTip("Tạm dừng cập nhật AI Summary" if self._summary_enabled else "Tiếp tục cập nhật AI Summary")
        if self._summary_enabled:
            self.summary_pause_btn.setStyleSheet("")
        else:
            self.summary_pause_btn.setStyleSheet("QPushButton{background:#475569;}")

    def _on_update_summary(self, text: str):
        if text and text.strip():
            self.summary_view.setPlainText(text.strip())
            try:
                self._summary_file.write_text(text.strip() + "\n", encoding="utf-8")
            except Exception as e:
                logger.warning(f"Khong the ghi summary: {e}")

    def _format_caption_html(self, source_text: str, target_text: str, now: str, font_size: int, en_font_size: int) -> str:
        if not source_text and not target_text:
            return ""
        if source_text and target_text and source_text.lower() == target_text.lower():
            text_to_show = source_text if self._display_mode == "en_only" else target_text
            return f"<div style='margin-bottom: 8px;'><span style='color: #64748b; font-size: {en_font_size}pt;'>[{now}]</span>&nbsp;&nbsp;<span style='color: #f8fafc;'>{text_to_show}</span></div>"

        if self._display_mode == "vi_only":
            if target_text:
                return f"<div style='margin-bottom: 8px;'><span style='color: #64748b; font-size: {en_font_size}pt;'>[{now}]</span>&nbsp;&nbsp;<span style='color: #f8fafc;'>{target_text}</span></div>"
            elif source_text:
                return f"<div style='margin-bottom: 8px;'><span style='color: #64748b; font-size: {en_font_size}pt;'>[{now}]</span>&nbsp;&nbsp;<span style='color: #94a3b8; font-style: italic;'>{source_text}</span></div>"
            return ""
        elif self._display_mode == "en_only":
            if source_text:
                return f"<div style='margin-bottom: 8px;'><span style='color: #64748b; font-size: {en_font_size}pt;'>[{now}]</span>&nbsp;&nbsp;<span style='color: #f8fafc;'>{source_text}</span></div>"
            return ""
        else: # both
            parts = []
            if source_text:
                parts.append(f"<div style='margin-top: 4px;'><span style='color: #64748b; font-size: {en_font_size}pt;'>[{now}]</span>&nbsp;&nbsp;<span style='color: #f8fafc;'>{source_text}</span></div>")
            if target_text:
                parts.append(f"<div style='margin-top: 2px; margin-bottom: 8px; padding-left: 20px;'><span style='color: #93c5fd; font-style: italic;'>{target_text}</span></div>")
            elif source_text:
                parts.append(f"<div style='margin-top: 2px; margin-bottom: 8px; padding-left: 20px;'><span style='color: #64748b; font-style: italic;'>[Đang dịch...]</span></div>")
            return "".join(parts)

    def _format_interim_html(self, source_text: str, target_text: str, font_size: int, en_font_size: int) -> str:
        if not source_text and not target_text:
            return ""
        if self._display_mode == "vi_only":
            txt = target_text or source_text
            return f"<div style='color: rgba(147, 197, 253, 0.7); font-style: italic; margin-top: 4px;'><i>... {txt}</i></div>"
        elif self._display_mode == "en_only":
            return f"<div style='color: rgba(248, 250, 252, 0.7); font-style: italic; margin-top: 4px;'><i>... {source_text}</i></div>"
        else: # both
            parts = []
            if source_text:
                parts.append(f"<div style='color: rgba(248, 250, 252, 0.6); font-style: italic; margin-top: 4px;'><i>... {source_text}</i></div>")
            if target_text:
                parts.append(f"<div style='color: rgba(147, 197, 253, 0.75); font-style: italic; margin-top: 2px; padding-left: 20px;'><i>... {target_text}</i></div>")
            return "".join(parts)

    def _save_history_to_file(self):
        try:
            lines = []
            for data in self._history:
                source_text = (data.get("source_text", "") or "").strip()
                target_text = (data.get("target_text", "") or "").strip()
                now = data.get("timestamp") or datetime.datetime.now().strftime("%H:%M:%S")
                if source_text and target_text and source_text.lower() == target_text.lower():
                    line = f"[{now}] {target_text}"
                else:
                    line = f"[{now}] SRC: {source_text}\n[{now}] VI : {target_text}"
                lines.append(line)
            
            self._history_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        except Exception as e:
            logger.warning(f"Khong the ghi log file: {e}")

    def _cycle_display_mode(self):
        modes = ["both", "en_only", "vi_only"]
        labels = {"both": "Song ngữ EN + VI", "en_only": "Chỉ tiếng Anh (EN)", "vi_only": "Chỉ tiếng Việt (VI)"}
        current_idx = modes.index(self._display_mode) if self._display_mode in modes else 0
        next_idx = (current_idx + 1) % len(modes)
        self._display_mode = modes[next_idx]
        self.display_mode_btn.setToolTip(f"Chuyển chế độ hiển thị (Hiện tại: {labels[self._display_mode]})")
        if self.config:
            self.config.set("display_mode", self._display_mode)
        self._reload_history_display()

    def _scroll_to_bottom(self, text_edit=None):
        """Tự động cuộn tới nội dung mới nhất ở dưới cùng."""
        target = text_edit or self.history_view
        self._apply_scroll_to_bottom(target)
        # Đảm bảo cuộn tới đáy ngay cả khi Qt cần thêm chu kỳ tính toán layout bất đồng bộ
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

    def _update_history_html(self, html_content: str):
        """Update history_view HTML và tự động cuộn tới nội dung mới nhất."""
        self.history_view.setHtml(html_content)
        self._scroll_to_bottom(self.history_view)

    def _reload_history_display(self):
        font_size = max(8, self._get_font_size() - 2)
        en_font_size = max(8, font_size - 2)
        html_lines = []
        for data in self._history:
            source_text = (data.get("source_text", "") or "").strip()
            target_text = (data.get("target_text", "") or "").strip()
            now = data.get("timestamp") or datetime.datetime.now().strftime("%H:%M:%S")
            html_line = self._format_caption_html(source_text, target_text, now, font_size, en_font_size)
            if html_line:
                html_lines.append(html_line)
                
        self.history_view.setUpdatesEnabled(False)
        if html_lines:
            body = "<br>".join(html_lines)
            full_html = f'<html><body style="margin:0; padding:0; color:#f8fafc; line-height:1.15;">{body}</body></html>'
            self.history_view.setHtml(full_html)
        else:
            self.history_view.clear()

        c = self.history_view.textCursor()
        c.movePosition(QTextCursor.End)
        self.history_view.setTextCursor(c)
        self._interim_start_pos = c.position()
        self._has_interim = False
        self.history_view.setUpdatesEnabled(True)
        self._scroll_to_bottom(self.history_view)

        if self._current_interim:
            self._update_interim_display()

    def _update_interim_display(self):
        """Cập nhật mượt câu nháp tại chỗ qua QTextCursor, không dựng lại toàn bộ tài liệu."""
        if not self._current_interim:
            return
        font_size = max(8, self._get_font_size() - 2)
        en_font_size = max(8, font_size - 2)
        src_text = (self._current_interim.get("source_text", "") or "").strip()
        tgt_text = (self._current_interim.get("target_text", "") or "").strip()
        interim_html = self._format_interim_html(src_text, tgt_text, font_size, en_font_size)
        if not interim_html:
            return

        c = self.history_view.textCursor()
        c.beginEditBlock()
        c.setPosition(self._interim_start_pos)
        c.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        prefix = "<br>" if (self._history and self._interim_start_pos > 0) else ""
        c.insertHtml(f"{prefix}{interim_html}")
        c.endEditBlock()
        self._has_interim = True

        # Cuộn êm đến cuối dòng, không giật màn hình
        c_end = self.history_view.textCursor()
        c_end.movePosition(QTextCursor.End)
        self.history_view.setTextCursor(c_end)
        self.history_view.ensureCursorVisible()
        bar = self.history_view.verticalScrollBar()
        if bar is not None:
            bar.setValue(bar.maximum())

    def _clear_interim_display(self):
        """Xóa câu nháp mượt mà khi hết thời gian chờ hoặc sang câu mới."""
        if not getattr(self, "_has_interim", False):
            return
        c = self.history_view.textCursor()
        c.beginEditBlock()
        c.setPosition(self._interim_start_pos)
        c.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        c.removeSelectedText()
        c.endEditBlock()
        self._has_interim = False
        bar = self.history_view.verticalScrollBar()
        if bar is not None:
            bar.setValue(bar.maximum())

    def _on_update_text(self, data: dict):
        self._idle_seconds = 0
        if "timestamp" not in data:
            data["timestamp"] = datetime.datetime.now().strftime("%H:%M:%S")

        source_text = (data.get("source_text", "") or "").strip()
        target_text = (data.get("target_text", "") or "").strip()
        source_lang = data.get("source_lang", "en")
        is_final = data.get("is_final", True)

        lang_map = {"en": "EN", "vi": "VI", "unknown": "UNK"}
        self.lang_label.setText(f"Transcript [{lang_map.get(source_lang, 'UNK')}]")

        if not is_final:
            self._current_interim = data
            self._update_interim_display()
            self.setWindowOpacity(self._get_opacity())
            if not self.isVisible():
                self.show()
                self.raise_()
            return

        # Finalized update: populate history on main thread to avoid threading race conditions
        self._current_interim = None
        self._has_interim = False
        merged = False
        if self._history:
            last_item = self._history[-1]
            last_src = (last_item.get("source_text", "") or "").strip()
            last_tgt = (last_item.get("target_text", "") or "").strip()
            
            # Merge if the new text is an incremental update of the last item
            if (last_src and source_text.startswith(last_src)) or (last_tgt and target_text.startswith(last_tgt)):
                self._history[-1] = data
                merged = True
                
        if not merged:
            self._history.append(data)
            if len(self._history) > 500:
                self._history.pop(0)

        # Reload full history and save to log file
        self._reload_history_display()
        self._save_history_to_file()

        self._current_text = {"source": source_text, "translated": target_text, "lang": source_lang}
        self.setWindowOpacity(self._get_opacity())
        if not self.isVisible():
            self.show()
            self.raise_()

    def _get_opacity(self) -> float:
        # Keep full opacity if summary updates are paused or mouse is hovering over the window
        if not self._summary_enabled or self.underMouse():
            return 1.0
        if self._idle_seconds > 45:
            return max(0.55, 1.0 - (self._idle_seconds - 45) * 0.01)
        return 1.0

    def _check_fade(self):
        self._idle_seconds += 1
        self.setWindowOpacity(self._get_opacity())
        if self._idle_seconds >= 8 and self._current_interim is not None:
            self._current_interim = None
            self._clear_interim_display()

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
        font_size = max(8, self._get_font_size() - 2)
        en_font_size = max(8, font_size - 2)
        html_lines = []
        for line in (transcript_lines or []):
            line_str = line.strip()
            if not line_str:
                continue
            if " SRC: " in line_str:
                if self._display_mode == "vi_only":
                    continue
                color = "#94a3b8" if self._display_mode == "both" else "#f8fafc"
                size_str = f"font-size: {en_font_size}pt;" if self._display_mode == "both" else ""
                html_lines.append(f"<span style='color: {color}; {size_str}'>{line_str}</span>")
            elif " VI : " in line_str:
                if self._display_mode == "en_only":
                    continue
                html_lines.append(f"<span style='color: #f8fafc;'>{line_str}</span>")
            else:
                html_lines.append(f"<span style='color: #f8fafc;'>{line_str}</span>")
        
        body = "<br>".join(html_lines)
        full_html = f'<html><body style="margin:0; padding:0; color:#f8fafc; line-height:1.0;">{body}</body></html>'
        self._update_history_html(full_html)
        c = self.history_view.textCursor()
        c.movePosition(QTextCursor.End)
        self.history_view.setTextCursor(c)
        self._interim_start_pos = c.position()
        self._has_interim = False
        self.summary_view.setPlainText((summary_text or "").strip())

    def enterEvent(self, event):
        self.setWindowOpacity(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setWindowOpacity(self._get_opacity())
        super().leaveEvent(event)

    def clear(self):
        self.history_view.clear()
        self.summary_view.clear()
        self.lang_label.setText("Session Transcript")
        self._current_text = {"source": "", "translated": "", "lang": ""}
        self._history = []
        self._current_interim = None
        self._interim_start_pos = 0
        self._has_interim = False


