"""
Caption window: independent, resizable transcript surface using aligned side-by-side HTML tables.
"""
import datetime
import logging
from pathlib import Path

from PyQt5.QtCore import QPoint, QRect, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QTextCursor
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

try:
    from src_minimal.ui.icons import get_svg_icon, make_icon_button
except ImportError:
    from src.ui.icons import get_svg_icon, make_icon_button

logger = logging.getLogger(__name__)


class CaptionWindow(QWidget):
    update_signal = pyqtSignal(dict)
    summary_signal = pyqtSignal(str)  # Kept for compatibility but not used for AI summary

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
        self.setMinimumSize(420, 180)

        self._setup_ui()
        self._load_position()

        self.update_signal.connect(self._on_update_text)

        self._fade_timer = QTimer()
        self._fade_timer.timeout.connect(self._check_fade)
        self._fade_timer.start(1000)

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame(self)
        self.card.setObjectName("captionCard")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(6, 6, 6, 6)
        card_layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(6)
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

        self.new_session_btn = make_icon_button(
            "plus",
            "Bắt đầu phiên mới (New Session)",
            self._new_session,
            color="#5D4037",
            btn_size=28,
            icon_size=14,
            object_name="iconButton",
            parent=self.card
        )
        header.addWidget(self.new_session_btn)

        self.history_btn = make_icon_button(
            "history",
            "Xem lịch sử cuộc họp (History)",
            self._open_history,
            color="#5D4037",
            btn_size=28,
            icon_size=14,
            object_name="iconButton",
            parent=self.card
        )
        header.addWidget(self.history_btn)

        self.min_btn = make_icon_button(
            "minus",
            "Thu nhỏ cửa sổ",
            self.showMinimized,
            color="#5D4037",
            btn_size=28,
            icon_size=14,
            object_name="iconButton",
            parent=self.card
        )
        header.addWidget(self.min_btn)

        self.close_btn = make_icon_button(
            "close",
            "Ẩn cửa sổ Caption",
            self.hide,
            color="#5D4037",
            btn_size=28,
            icon_size=14,
            object_name="closeButton",
            parent=self.card
        )
        header.addWidget(self.close_btn)
        card_layout.addLayout(header)

        # Single view for aligned HTML table layout
        self.history_view = QTextEdit()
        self.history_view.setReadOnly(True)
        self.history_view.setObjectName("historyView")
        self.history_view.setPlaceholderText("Transcript will appear here...")
        card_layout.addWidget(self.history_view, 4)

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
        h = self.config.get("caption_height", 280) if self.config else 280
        self.resize(w, h)

    def _apply_style(self):
        font_size = self._get_font_size()
        self.history_view.setFont(QFont("Segoe UI", font_size))
        self.setStyleSheet(
            """
            #captionCard {
                background: #FAF2EB;
                border: 2px solid #E5D8CD;
                border-radius: 14px;
            }
            #statusDot {
                background: #795548;
                border-radius: 4px;
            }
            #titleLabel {
                color: #1C1B1F;
                font: 700 13px "Segoe UI";
            }
            #metaLabel, #resizeHint {
                color: #6B686E;
                font: 10px "Segoe UI";
            }
            #modePill {
                color: #795548;
                background: #F3E3D3;
                border: 1px solid #E5D8CD;
                border-radius: 6px;
                padding: 3px 6px;
                font: 700 9px "Segoe UI";
            }
            #historyView {
                color: #1C1B1F;
                background: #FFFFFF;
                border: 1px solid #E5D8CD;
                border-radius: 10px;
                padding: 6px;
                selection-background-color: #F3E3D3;
                selection-color: #1C1B1F;
            }
            #smallButton {
                color: #1C1B1F;
                background: #F3E3D3;
                border: 1px solid #E5D8CD;
                border-radius: 6px;
                padding: 3px 6px;
                font: 600 10px "Segoe UI";
            }
            #iconButton, #closeButton {
                background: #F3E3D3;
                border: 1px solid #E5D8CD;
                border-radius: 8px;
                padding: 0px;
            }
            #iconButton:hover {
                background: #E5D8CD;
                border-color: #C8B9AD;
            }
            #closeButton:hover {
                background: #E8D5C4;
                border-color: #C8B9AD;
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
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #E5D8CD;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            """
        )

    def _get_font_size(self) -> int:
        # Reduced default font size to 11
        return self.config.get("caption_font_size", 11) if self.config else 11

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
            sz = max(9, self._get_font_size() - 2)
            self.history_view.setFont(QFont("Segoe UI", sz))
        else:
            sz = self._get_font_size()
            self.history_view.setFont(QFont("Segoe UI", sz))
        self._save_geometry()

    def show_caption(self, data: dict):
        self.update_signal.emit(data)

    def set_summary(self, text: str):
        pass  # Removed AI summary display

    def set_summary_enabled(self, enabled: bool):
        pass  # Removed AI summary pause/resume logic

    def _new_session(self):
        if self.app_ref:
            self.app_ref.start_new_session()

    def _open_history(self):
        if self.app_ref:
            self.app_ref.open_session_history()

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

    def _scroll_to_bottom(self, text_edit=None):
        """Tự động cuộn tới nội dung mới nhất ở dưới cùng."""
        target = text_edit or self.history_view
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

    def _update_history_html(self, html_content: str):
        """Update history_view HTML và tự động cuộn tới nội dung mới nhất."""
        self.history_view.setHtml(html_content)
        self._scroll_to_bottom(self.history_view)

    def _reload_history_display(self):
        font_size = max(8, self._get_font_size() - 2)
        time_font_size = max(7, font_size - 2)
        
        html_parts = []
        html_parts.append('<table width="100%" style="table-layout: fixed; border-collapse: collapse; margin: 0; padding: 0;">')
        
        for data in self._history:
            source_text = (data.get("source_text", "") or "").strip()
            target_text = (data.get("target_text", "") or "").strip()
            now = data.get("timestamp") or datetime.datetime.now().strftime("%H:%M:%S")
            
            # Formatted time label (smaller and faded grey)
            time_html = f"<span style='color: #8E8A90; font-size: {time_font_size}pt; font-family: Segoe UI;'>[{now}]</span>"
            
            en_cell = f"{time_html} <span style='font-size: {font_size}pt;'>{source_text}</span>" if source_text else ""
            vi_cell = f"{time_html} <span style='font-size: {font_size}pt;'>{target_text}</span>" if target_text else ""
            
            html_parts.append(
                f"<tr>"
                f"<td style='width: 50%; vertical-align: top; padding-right: 8px; padding-bottom: 2px; color: #1C1B1F; font-family: Segoe UI; line-height: 1.1;'>{en_cell}</td>"
                f"<td style='width: 50%; vertical-align: top; padding-left: 8px; padding-bottom: 2px; border-left: 1px solid #E5D8CD; color: #1C1B1F; font-family: Segoe UI; line-height: 1.1;'>{vi_cell}</td>"
                f"</tr>"
            )
            
        html_parts.append('</table>')
        body = "".join(html_parts)
        full_html = f'<html><body style="margin:0; padding:0; line-height:1.1;">{body}</body></html>'
        
        self.history_view.setUpdatesEnabled(False)
        self.history_view.setHtml(full_html)
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
        """Cập nhật mượt mà câu nháp tại chỗ qua QTextCursor."""
        if not self._current_interim:
            return
        font_size = max(8, self._get_font_size() - 2)
        src_text = (self._current_interim.get("source_text", "") or "").strip()
        tgt_text = (self._current_interim.get("target_text", "") or "").strip()
        en_interim = f"<span style='color: rgba(28, 27, 31, 130); font-style: italic; font-size: {font_size}pt;'>* {src_text}...</span>" if src_text else ""
        vi_interim = f"<span style='color: rgba(28, 27, 31, 130); font-style: italic; font-size: {font_size}pt;'>* {tgt_text}...</span>" if tgt_text else ""
        interim_html = f"<div style='margin-top: 4px; padding: 2px 0;'>{en_interim} &nbsp; {vi_interim}</div>"

        c = self.history_view.textCursor()
        c.beginEditBlock()
        c.setPosition(self._interim_start_pos)
        c.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        c.insertHtml(interim_html)
        c.endEditBlock()
        self._has_interim = True

        c_end = self.history_view.textCursor()
        c_end.movePosition(QTextCursor.End)
        self.history_view.setTextCursor(c_end)
        self.history_view.ensureCursorVisible()
        bar = self.history_view.verticalScrollBar()
        if bar is not None:
            bar.setValue(bar.maximum())

    def _clear_interim_display(self):
        """Xóa câu nháp mượt mà khi kết thúc hoặc idle."""
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

        # Finalized update: populate history
        self._current_interim = None
        self._has_interim = False
        merged = False
        if self._history:
            last_item = self._history[-1]
            last_src = (last_item.get("source_text", "") or "").strip()
            last_tgt = (last_item.get("target_text", "") or "").strip()
            if (last_src and (source_text == last_src or source_text.startswith(last_src))) or (last_tgt and (target_text == last_tgt or target_text.startswith(last_tgt))):
                self._history[-1] = data
                merged = True
                
        if not merged:
            self._history.append(data)
            if len(self._history) > 500:
                self._history.pop(0)

        self._reload_history_display()
        self._save_history_to_file()

        self._current_text = {"source": source_text, "translated": target_text, "lang": source_lang}
        self.setWindowOpacity(self._get_opacity())
        if not self.isVisible():
            self.show()
            self.raise_()

    def _get_opacity(self) -> float:
        if self.underMouse():
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
            self.resize(min(900, geo.width() - 80), 300)
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
        self.clear()

    def load_session_view(self, transcript_lines: list[str], summary_text: str):
        self._history = []
        current_data = {}
        
        for line in (transcript_lines or []):
            line_str = line.strip()
            if not line_str:
                continue
                
            ts = ""
            if line_str.startswith("[") and "]" in line_str:
                idx = line_str.find("]")
                ts = line_str[1:idx]
                content_part = line_str[idx+1:].strip()
            else:
                content_part = line_str
                
            if "SRC: " in content_part:
                text = content_part.replace("SRC: ", "").strip()
                if current_data and (current_data.get("timestamp") != ts or "source_text" in current_data):
                    self._history.append(current_data)
                    current_data = {}
                current_data["timestamp"] = ts
                current_data["source_text"] = text
            elif "VI : " in content_part:
                text = content_part.replace("VI : ", "").strip()
                if current_data and current_data.get("timestamp") == ts:
                    current_data["target_text"] = text
                else:
                    if current_data:
                        self._history.append(current_data)
                    current_data = {"timestamp": ts, "target_text": text}
            else:
                if current_data:
                    self._history.append(current_data)
                current_data = {"timestamp": ts, "source_text": content_part, "target_text": content_part}
                
        if current_data:
            self._history.append(current_data)
            
        self._reload_history_display()

    def enterEvent(self, event):
        self.setWindowOpacity(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setWindowOpacity(self._get_opacity())
        super().leaveEvent(event)

    def clear(self):
        self.history_view.clear()
        self.lang_label.setText("Session Transcript")
        self._current_text = {"source": "", "translated": "", "lang": ""}
        self._history = []
        self._current_interim = None
        self._interim_start_pos = 0
        self._has_interim = False
