from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSlider, QSpinBox, QPushButton, QTabWidget, QFormLayout
)
from PyQt5.QtCore import Qt


class SettingsWindow:
    """Cửa sổ cài đặt."""

    def __init__(self, config, app_ref):
        self.config = config
        self.app_ref = app_ref
        self.window = QMainWindow()
        self.window.setWindowTitle("Teams Translator - Cài đặt")
        self.window.setFixedSize(500, 500)
        self.window.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.WindowCloseButtonHint
        )

        central = QWidget()
        self.window.setCentralWidget(central)
        tabs = QTabWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(tabs)

        gen_tab = QWidget()
        gen_layout = QFormLayout(gen_tab)
        tabs.addTab(gen_tab, "Chung")
        _ = gen_layout

        cap_tab = QWidget()
        cap_layout = QFormLayout(cap_tab)

        self.font_size = QSpinBox()
        self.font_size.setRange(8, 36)
        self.font_size.setValue(config.get("caption_font_size", 14))
        self.font_size.valueChanged.connect(lambda v: config.set("caption_font_size", v))
        cap_layout.addRow("Cỡ chữ:", self.font_size)

        self.opacity = QSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(20, 100)
        self.opacity.setValue(int(config.get("caption_opacity", 0.85) * 100))
        self.opacity.valueChanged.connect(lambda v: config.set("caption_opacity", v / 100))
        cap_layout.addRow("Độ trong suốt:", self.opacity)

        tabs.addTab(cap_tab, "Caption")

        audio_tab = QWidget()
        audio_layout = QFormLayout(audio_tab)

        self.energy = QSlider(Qt.Orientation.Horizontal)
        self.energy.setRange(100, 1000)
        self.energy.setValue(config.get("stt_energy_threshold", 300))
        self.energy.valueChanged.connect(lambda v: config.set("stt_energy_threshold", v))
        audio_layout.addRow("Độ nhạy microphone:", self.energy)

        tabs.addTab(audio_tab, "Âm thanh")

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_detect = QPushButton("🔊 Kiểm tra thiết bị audio")
        btn_detect.clicked.connect(lambda: self.app_ref._show_audio_devices())
        btn_layout.addWidget(btn_detect)
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.window.close)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
