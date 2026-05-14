import logging
import re
import time

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout

import pyautogui

logger = logging.getLogger(__name__)


class LiveInputWindow(QWidget):
    """
    Composer trung gian:
    - User go tieng Viet trong o nay
    - App dich sang tieng Anh
    - Bam vao input muc tieu da capture va paste tieng Anh
    """

    def __init__(self, app_ref):
        super().__init__(None)
        self.app_ref = app_ref
        self.target_pos = None
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle("VN -> EN Composer")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.resize(460, 230)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.status_label = QLabel("Chua chon input dich. Dua chuot vao input app va bam Ctrl+Shift+V")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #dbeafe;")
        layout.addWidget(self.status_label)

        self.vn_input = QTextEdit()
        self.vn_input.setPlaceholderText("Go tieng Viet o day...")
        self.vn_input.setFont(QFont("Segoe UI", 11))
        layout.addWidget(self.vn_input, 1)

        btn_row = QHBoxLayout()
        self.translate_btn = QPushButton("Dich va go vao app")
        self.translate_btn.clicked.connect(self.translate_and_inject)
        btn_row.addWidget(self.translate_btn)

        self.clear_btn = QPushButton("Xoa")
        self.clear_btn.clicked.connect(self.vn_input.clear)
        btn_row.addWidget(self.clear_btn)
        layout.addLayout(btn_row)

    def update_target_position(self, x: int, y: int):
        self.target_pos = (x, y)
        self.status_label.setText(f"Da chon input dich tai ({x}, {y}). Bam 'Dich va chen vao app'.")

    def translate_and_inject(self):
        source_text = self.vn_input.toPlainText().strip()
        if not source_text:
            self.status_label.setText("Chua co noi dung tieng Viet de dich.")
            return
        if not self.target_pos:
            self.status_label.setText("Chua co input dich. Dua chuot vao input app va bam Ctrl+Shift+V.")
            return

        result = self.app_ref.translator.translate_bidirectional(source_text, direction="vi2en")
        target_text = (result.get("target_text") or "").strip()
        target_text = self._sanitize_for_target_input(target_text)
        if not target_text:
            self.status_label.setText("Khong dich duoc. Thu lai.")
            return

        try:
            # Tra focus ve input dich theo vi tri user da danh dau
            pyautogui.click(self.target_pos[0], self.target_pos[1])
            time.sleep(0.12)
            pyautogui.typewrite(target_text, interval=0.004)
            self.status_label.setText("Da go tieng Anh vao input dich. Ban tu bam Enter de gui.")
        except Exception as e:
            logger.exception("Inject text failed")
            self.status_label.setText(f"Loi chen text: {e}")

    def _sanitize_for_target_input(self, text: str) -> str:
        """
        Loai bo icon/moji khong mong muon (loa, mic...) de app dich chi nhan text thuong.
        """
        cleaned = (text or "").strip()
        if not cleaned:
            return ""
        # Bo cac ky tu icon thuong gap o dau cau
        cleaned = re.sub(r"^[\s\u200b\u200c\u200d\ufeff]*(🔊|🔈|🔉|📢|📣|🎤|🎙️|🎙|🗣️|🗣)+\s*", "", cleaned)
        return cleaned.strip()
