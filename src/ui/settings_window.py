from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSlider, QLabel, QStackedWidget, QToolButton, QFrame
)
from PyQt5.QtCore import Qt

try:
    from src.ui.icons import get_svg_icon, make_icon_button
except ImportError:
    from src_minimal.ui.icons import get_svg_icon, make_icon_button


class SettingsWindow:
    """Cửa sổ cài đặt giao diện hiện đại 2 cột theo thiết kế mẫu."""

    def __init__(self, config, app_ref):
        self.config = config
        self.app_ref = app_ref
        self.window = QMainWindow()
        self.window.setWindowTitle("Settings")
        self.window.setFixedSize(540, 420)
        self.window.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.window.setAttribute(Qt.WA_TranslucentBackground)

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("settingsContainer")
        self.window.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(14, 12, 14, 14)
        root_layout.setSpacing(10)

        # 1. Header: Icon + Title + Close Button
        header = QHBoxLayout()
        header.setSpacing(8)

        settings_icon = QLabel()
        settings_icon.setPixmap(get_svg_icon("settings", color="#38bdf8", size=18).pixmap(18, 18))
        header.addWidget(settings_icon)

        title = QLabel("Settings")
        title.setObjectName("settingsTitle")
        header.addWidget(title)

        header.addStretch(1)

        close_btn = make_icon_button(
            "close",
            "Đóng cửa sổ cài đặt",
            self.window.close,
            color="#cbd5e1",
            btn_size=28,
            icon_size=14,
            object_name="closeButton",
            parent=central
        )
        header.addWidget(close_btn)
        root_layout.addLayout(header)

        # 2. Main 2-Column Body: Sidebar + Content
        body = QHBoxLayout()
        body.setSpacing(14)

        # Left Sidebar Navigation
        sidebar = QVBoxLayout()
        sidebar.setSpacing(4)
        sidebar.setContentsMargins(0, 0, 0, 0)

        self.tab_buttons = []
        tab_defs = [
            ("Aa Caption", "subtitles"),
            ("Audio", "mic"),
            ("Shortcuts", "keyboard"),
            ("General", "settings"),
        ]

        for idx, (label_text, icon_name) in enumerate(tab_defs):
            btn = QToolButton()
            btn.setObjectName("sidebarTabButton")
            btn.setText(f"  {label_text}")
            btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            btn.setIcon(get_svg_icon(icon_name, color="#cbd5e1", size=15))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(36)
            btn.setMinimumWidth(130)
            btn.clicked.connect(lambda checked=False, i=idx: self._switch_tab(i))
            sidebar.addWidget(btn)
            self.tab_buttons.append(btn)

        sidebar.addStretch(1)
        body.addLayout(sidebar)

        # Right Content Area (QStackedWidget)
        self.stack = QStackedWidget()
        self.stack.setObjectName("settingsStack")

        # Page 0: Caption Settings
        self.stack.addWidget(self._create_caption_page())
        # Page 1: Audio Settings
        self.stack.addWidget(self._create_audio_page())
        # Page 2: Shortcuts Page
        self.stack.addWidget(self._create_shortcuts_page())
        # Page 3: General Page
        self.stack.addWidget(self._create_general_page())

        body.addWidget(self.stack, 1)
        root_layout.addLayout(body, 1)

        self._apply_style()
        self._switch_tab(0)

    def _create_caption_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 0, 8, 8)
        layout.setSpacing(14)

        sec_title = QLabel("Caption Display")
        sec_title.setObjectName("sectionTitle")
        layout.addWidget(sec_title)

        # Font size row
        fs_header = QHBoxLayout()
        fs_label = QLabel("Font size")
        fs_label.setObjectName("paramLabel")
        current_fs = self.config.get("caption_font_size", 14) if self.config else 14
        self.font_size_val = QLabel(f"{current_fs}pt")
        self.font_size_val.setObjectName("paramValue")
        fs_header.addWidget(fs_label)
        fs_header.addStretch(1)
        fs_header.addWidget(self.font_size_val)
        layout.addLayout(fs_header)

        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setRange(8, 36)
        self.font_size_slider.setValue(current_fs)
        self.font_size_slider.valueChanged.connect(self._on_font_size_changed)
        layout.addWidget(self.font_size_slider)

        fs_marks = QHBoxLayout()
        lbl_min = QLabel("8pt")
        lbl_min.setObjectName("scaleMark")
        lbl_max = QLabel("36pt")
        lbl_max.setObjectName("scaleMark")
        fs_marks.addWidget(lbl_min)
        fs_marks.addStretch(1)
        fs_marks.addWidget(lbl_max)
        layout.addLayout(fs_marks)

        # Transparency row
        op_header = QHBoxLayout()
        op_label = QLabel("Overlay transparency")
        op_label.setObjectName("paramLabel")
        current_op = int((self.config.get("caption_opacity", 0.85) if self.config else 0.85) * 100)
        self.opacity_val = QLabel(f"{current_op}%")
        self.opacity_val.setObjectName("paramValue")
        op_header.addWidget(op_label)
        op_header.addStretch(1)
        op_header.addWidget(self.opacity_val)
        layout.addLayout(op_header)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(current_op)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        layout.addWidget(self.opacity_slider)

        op_marks = QHBoxLayout()
        lbl_op_min = QLabel("10%")
        lbl_op_min.setObjectName("scaleMark")
        lbl_op_max = QLabel("100%")
        lbl_op_max.setObjectName("scaleMark")
        op_marks.addWidget(lbl_op_min)
        op_marks.addStretch(1)
        op_marks.addWidget(lbl_op_max)
        layout.addLayout(op_marks)

        layout.addStretch(1)
        return page

    def _create_audio_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 0, 8, 8)
        layout.setSpacing(14)

        sec_title = QLabel("Audio")
        sec_title.setObjectName("sectionTitle")
        layout.addWidget(sec_title)

        # Microphone sensitivity
        sens_header = QHBoxLayout()
        sens_label = QLabel("Microphone sensitivity")
        sens_label.setObjectName("paramLabel")
        thresh = self.config.get("stt_energy_threshold", 300) if self.config else 300
        pct = max(10, min(100, int((thresh / 1000) * 100)))
        self.sens_val = QLabel(f"{pct}%")
        self.sens_val.setObjectName("paramValue")
        sens_header.addWidget(sens_label)
        sens_header.addStretch(1)
        sens_header.addWidget(self.sens_val)
        layout.addLayout(sens_header)

        self.sens_slider = QSlider(Qt.Horizontal)
        self.sens_slider.setRange(10, 100)
        self.sens_slider.setValue(pct)
        self.sens_slider.valueChanged.connect(self._on_sens_changed)
        layout.addWidget(self.sens_slider)

        sens_marks = QHBoxLayout()
        lbl_low = QLabel("Low")
        lbl_low.setObjectName("scaleMark")
        lbl_high = QLabel("High")
        lbl_high.setObjectName("scaleMark")
        sens_marks.addWidget(lbl_low)
        sens_marks.addStretch(1)
        sens_marks.addWidget(lbl_high)
        layout.addLayout(sens_marks)

        layout.addSpacing(10)

        # Test Audio Devices Button
        btn_detect = QToolButton()
        btn_detect.setObjectName("testAudioButton")
        btn_detect.setText("  Test / Select Audio Devices")
        btn_detect.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        btn_detect.setIcon(get_svg_icon("headphones", color="#38bdf8", size=18))
        btn_detect.setCursor(Qt.PointingHandCursor)
        btn_detect.setFixedHeight(40)
        btn_detect.clicked.connect(lambda: self.app_ref._show_audio_devices() if hasattr(self.app_ref, "_show_audio_devices") else None)
        layout.addWidget(btn_detect)

        layout.addStretch(1)
        return page

    def _create_shortcuts_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 0, 8, 8)
        layout.setSpacing(12)

        sec_title = QLabel("Keyboard Shortcuts")
        sec_title.setObjectName("sectionTitle")
        layout.addWidget(sec_title)

        shortcuts = [
            ("Ctrl + Shift + T", "Tạm dừng / Tiếp tục thu âm (Pause / Resume)"),
            ("Ctrl + Shift + C", "Bật / Tắt cửa sổ Caption overlay"),
            ("Ctrl + Shift + V", "Chọn ô nhập mục tiêu (Teams / Browser)"),
            ("Enter", "Dịch sang tiếng Anh & Gõ tự động vào Teams"),
        ]

        for key, desc in shortcuts:
            row = QHBoxLayout()
            key_badge = QLabel(key)
            key_badge.setObjectName("shortcutBadge")
            desc_lbl = QLabel(desc)
            desc_lbl.setObjectName("paramLabel")
            row.addWidget(key_badge)
            row.addWidget(desc_lbl, 1)
            layout.addLayout(row)

        layout.addStretch(1)
        return page

    def _create_general_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 0, 8, 8)
        layout.setSpacing(12)

        sec_title = QLabel("General Settings")
        sec_title.setObjectName("sectionTitle")
        layout.addWidget(sec_title)

        info = QLabel(
            "Live Translator AI v2.6\n"
            "Chạy ngầm trên khay hệ thống Windows.\n"
            "Tối ưu hoá cho Microsoft Teams và cuộc họp trực tuyến."
        )
        info.setObjectName("paramLabel")
        info.setWordWrap(True)
        layout.addWidget(info)

        layout.addStretch(1)
        return page

    def _switch_tab(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.tab_buttons):
            if i == index:
                btn.setStyleSheet(
                    "background: #2563eb; color: #ffffff; border: 1px solid #3b82f6; border-radius: 8px; font: 600 12px 'Segoe UI'; text-align: left; padding-left: 10px;"
                )
            else:
                btn.setStyleSheet(
                    "background: transparent; color: #94a3b8; border: 1px solid transparent; border-radius: 8px; font: 500 12px 'Segoe UI'; text-align: left; padding-left: 10px;"
                )

    def _on_font_size_changed(self, val: int):
        self.font_size_val.setText(f"{val}pt")
        if self.config:
            self.config.set("caption_font_size", val)
        if hasattr(self.app_ref, "caption_window") and self.app_ref.caption_window:
            self.app_ref.caption_window._apply_style()

    def _on_opacity_changed(self, val: int):
        self.opacity_val.setText(f"{val}%")
        if self.config:
            self.config.set("caption_opacity", val / 100.0)

    def _on_sens_changed(self, val: int):
        self.sens_val.setText(f"{val}%")
        if self.config:
            self.config.set("stt_energy_threshold", int(val * 10))

    def _apply_style(self):
        self.window.setStyleSheet(
            """
            #settingsContainer {
                background: rgba(10, 16, 30, 250);
                border: 1px solid rgba(56, 189, 248, 0.25);
                border-radius: 14px;
            }
            #settingsTitle {
                color: #f8fafc;
                font: 700 14px "Segoe UI";
            }
            #sectionTitle {
                color: #f8fafc;
                font: 700 13px "Segoe UI";
                margin-bottom: 2px;
            }
            #paramLabel {
                color: #cbd5e1;
                font: 500 12px "Segoe UI";
            }
            #paramValue {
                color: #38bdf8;
                font: 700 12px "Segoe UI";
            }
            #scaleMark {
                color: #64748b;
                font: 500 10px "Segoe UI";
            }
            #shortcutBadge {
                background: rgba(56, 189, 248, 0.12);
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 6px;
                color: #38bdf8;
                font: 600 11px "Segoe UI";
                padding: 4px 8px;
                min-width: 90px;
            }
            #sidebarTabButton:hover {
                background: rgba(255, 255, 255, 0.08);
                color: #f8fafc;
            }
            #testAudioButton {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                color: #f8fafc;
                font: 600 12px "Segoe UI";
                padding: 0 12px;
            }
            #testAudioButton:hover {
                background: rgba(56, 189, 248, 0.15);
                border-color: rgba(56, 189, 248, 0.4);
            }
            #closeButton {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }
            #closeButton:hover {
                background: rgba(239, 68, 68, 0.85);
                border-color: #ef4444;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: rgba(255, 255, 255, 0.15);
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #3b82f6;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                width: 14px;
                height: 14px;
                margin: -5px 0;
                background: #38bdf8;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #60a5fa;
            }
            """
        )

