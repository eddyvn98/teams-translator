"""
SVG Icon Library & Utilities for Teams Translator (2026 Minimalist Aesthetic).
Generates high-DPI QIcon instances from crisp vector SVG paths.
"""

from PyQt5.QtCore import QByteArray, QSize, Qt
from PyQt5.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QPushButton

# Standard Lucide-style SVG paths (viewBox: 0 0 24 24, stroke-width: 2, linecap: round, linejoin: round)
SVG_PATHS = {
    "play": '<polygon points="6 4 20 12 6 20 6 4" fill="currentColor" stroke="currentColor"/>',
    "pause": '<rect x="6" y="4" width="4" height="16" rx="1" fill="currentColor" stroke="none"/><rect x="14" y="4" width="4" height="16" rx="1" fill="currentColor" stroke="none"/>',
    "subtitles": (
        '<rect x="3" y="5" width="18" height="14" rx="3"/>'
        '<path d="M7 15h4M15 15h2M7 11h2M13 11h4"/>'
    ),
    "panel": (
        '<rect width="18" height="18" x="3" y="3" rx="3"/>'
        '<path d="M9 3v18"/>'
        '<path d="m14 9 3 3-3 3"/>'
    ),
    "close": '<path d="M18 6 6 18M6 6l12 12"/>',
    "minus": '<path d="M5 12h14"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "history": (
        '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>'
        '<path d="M3 3v5h5"/>'
        '<path d="M12 7v5l4 2"/>'
    ),
    "rotate_ccw": (
        '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>'
        '<path d="M3 3v5h5"/>'
    ),
    "languages": (
        '<circle cx="12" cy="12" r="10"/>'
        '<path d="M12 2a14.5 14.5 0 0 0 0 20M12 2a14.5 14.5 0 0 1 0 20M2 12h20"/>'
    ),
    "sparkles": (
        '<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z"/>'
    ),
    "target": (
        '<circle cx="12" cy="12" r="10"/>'
        '<line x1="22" y1="12" x2="18" y2="12"/>'
        '<line x1="6" y1="12" x2="2" y2="12"/>'
        '<line x1="12" y1="6" x2="12" y2="2"/>'
        '<line x1="12" y1="22" x2="12" y2="18"/>'
    ),
    "shrink": (
        '<polyline points="4 14 10 14 10 20"/>'
        '<polyline points="20 10 14 10 14 4"/>'
        '<line x1="14" y1="10" x2="21" y2="3"/>'
        '<line x1="3" y1="21" x2="10" y2="14"/>'
    ),
    "headphones": (
        '<path d="M3 18v-6a9 9 0 0 1 18 0v6"/>'
        '<path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/>'
    ),
    "speaker": (
        '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>'
        '<path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>'
        '<path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>'
    ),
    "volume_1": (
        '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>'
        '<path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>'
    ),
    "volume_x": (
        '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>'
        '<line x1="22" y1="9" x2="16" y2="15"/>'
        '<line x1="16" y1="9" x2="22" y2="15"/>'
    ),
    "send": (
        '<line x1="22" y1="2" x2="11" y2="13"/>'
        '<polygon points="22 2 15 22 11 13 2 9 22 2" fill="currentColor"/>'
    ),
    "trash": (
        '<path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>'
    ),
    "detach": (
        '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
        '<polyline points="15 3 21 3 21 9"/>'
        '<line x1="10" y1="14" x2="21" y2="3"/>'
    ),
    "attach": (
        '<rect width="18" height="18" x="3" y="3" rx="2"/>'
        '<path d="M15 3v18"/>'
        '<path d="m10 9-3 3 3 3"/>'
    ),
    "chevron_up": '<path d="m18 15-6-6-6 6"/>',
    "chevron_down": '<path d="m6 9 6 6 6-6"/>',
    "eye": (
        '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>'
        '<circle cx="12" cy="12" r="3"/>'
    ),
    "eye_off": (
        '<path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/>'
        '<path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/>'
        '<path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/>'
        '<line x1="2" y1="2" x2="22" y2="22"/>'
    ),
    "radio": (
        '<path d="M4.9 19.1C1 15.2 1 8.8 4.9 4.9M7.8 16.2c-2.3-2.3-2.3-6.1 0-8.5"/>'
        '<circle cx="12" cy="12" r="2" fill="currentColor"/>'
        '<path d="M16.2 7.8c2.3 2.3 2.3 6.1 0 8.5M19.1 4.9C23 8.8 23 15.2 19.1 19.1"/>'
    ),
    "activity": (
        '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>'
    ),
    "check": '<polyline points="20 6 9 17 4 12"/>',
    "bot": (
        '<rect width="18" height="14" x="3" y="7" rx="3"/>'
        '<path d="M12 7V3M8 3h8"/>'
        '<circle cx="9" cy="13" r="1.5" fill="currentColor"/>'
        '<circle cx="15" cy="13" r="1.5" fill="currentColor"/>'
    ),
    "soundwave": (
        '<line x1="4" y1="10" x2="4" y2="14"/>'
        '<line x1="8" y1="5" x2="8" y2="19"/>'
        '<line x1="12" y1="2" x2="12" y2="22"/>'
        '<line x1="16" y1="6" x2="16" y2="18"/>'
        '<line x1="20" y1="10" x2="20" y2="14"/>'
    ),
    "pin": (
        '<line x1="12" y1="17" x2="12" y2="22"/>'
        '<path d="M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.89A2 2 0 0 1 15 10.77V5h1a1 1 0 0 0 0-2H8a1 1 0 0 0 0 2h1v5.77a2 2 0 0 1-1.11 1.79l-1.78.89A2 2 0 0 0 5 15.24Z"/>'
    ),
    "copy": (
        '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/>'
        '<path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>'
    ),
    "settings": (
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>'
    ),
    "menu": (
        '<line x1="4" y1="6" x2="20" y2="6"/>'
        '<line x1="4" y1="12" x2="20" y2="12"/>'
        '<line x1="4" y1="18" x2="20" y2="18"/>'
    ),
    "dots_grip": (
        '<circle cx="8" cy="6" r="1.5" fill="currentColor"/>'
        '<circle cx="8" cy="12" r="1.5" fill="currentColor"/>'
        '<circle cx="8" cy="18" r="1.5" fill="currentColor"/>'
        '<circle cx="14" cy="6" r="1.5" fill="currentColor"/>'
        '<circle cx="14" cy="12" r="1.5" fill="currentColor"/>'
        '<circle cx="14" cy="18" r="1.5" fill="currentColor"/>'
    ),
    "cc": (
        '<rect x="2" y="4" width="20" height="16" rx="3"/>'
        '<path d="M10 9a3 3 0 0 0-3 3v0a3 3 0 0 0 3 3"/>'
        '<path d="M17 9a3 3 0 0 0-3 3v0a3 3 0 0 0 3 3"/>'
    ),
    "expand": (
        '<polyline points="15 3 21 3 21 9"/>'
        '<polyline points="9 21 3 21 3 15"/>'
        '<line x1="21" y1="3" x2="14" y2="10"/>'
        '<line x1="3" y1="21" x2="10" y2="14"/>'
    ),
    "mic": (
        '<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>'
        '<path d="M19 10v2a7 7 0 0 1-14 0v-2"/>'
        '<line x1="12" y1="19" x2="12" y2="22"/>'
    ),
    "keyboard": (
        '<rect width="20" height="14" x="2" y="5" rx="2"/>'
        '<line x1="6" y1="9" x2="6.01" y2="9"/>'
        '<line x1="10" y1="9" x2="10.01" y2="9"/>'
        '<line x1="14" y1="9" x2="14.01" y2="9"/>'
        '<line x1="18" y1="9" x2="18.01" y2="9"/>'
        '<line x1="6" y1="13" x2="6.01" y2="13"/>'
        '<line x1="18" y1="13" x2="18.01" y2="13"/>'
        '<line x1="10" y1="13" x2="14" y2="13"/>'
    ),
    "refresh": (
        '<path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>'
        '<path d="M3 3v5h5"/>'
        '<path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>'
        '<path d="M16 21h5v-5"/>'
    ),
    "power": (
        '<path d="M18.36 6.64a9 9 0 1 1-12.73 0"/>'
        '<line x1="12" y1="2" x2="12" y2="12"/>'
    ),
    "pencil": (
        '<path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>'
    ),
}

_ICON_CACHE = {}


def build_svg_xml(path_content: str, stroke_color: str = "#e2e8f0", fill_color: str = "none") -> str:
    """Wrap path content into a full SVG markup with 24x24 viewBox."""
    processed_paths = path_content.replace("currentColor", stroke_color)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        f'fill="{fill_color}" stroke="{stroke_color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round">'
        f"{processed_paths}"
        f"</svg>"
    )


def get_svg_icon(name: str, color: str = "#e2e8f0", size: int = 24) -> QIcon:
    """
    Renders SVG vector icon cleanly to high-DPI QIcon using QSvgRenderer.
    Cached for peak UI performance.
    """
    cache_key = (name, color, size)
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    path_data = SVG_PATHS.get(name)
    if not path_data:
        return QIcon()

    xml = build_svg_xml(path_data, stroke_color=color)
    byte_arr = QByteArray(xml.encode("utf-8"))
    renderer = QSvgRenderer(byte_arr)

    # Scale 2x for retina / high-DPI crystal clear display
    render_size = size * 2
    pixmap = QPixmap(render_size, render_size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    renderer.render(painter)
    painter.end()

    icon = QIcon(pixmap)
    _ICON_CACHE[cache_key] = icon
    return icon


from PyQt5.QtWidgets import QPushButton, QToolButton


def make_icon_button(
    icon_name: str,
    tooltip: str,
    callback=None,
    color: str = "#e2e8f0",
    btn_size: int = 34,
    icon_size: int = 18,
    object_name: str = "iconButton",
    parent=None
) -> QPushButton:
    """
    Factory creating a minimalist, textless icon button ready for 2026 UI standards.
    """
    btn = QPushButton(parent) if parent else QPushButton()
    btn.setObjectName(object_name)
    btn.setText("")  # Never display text
    btn.setToolTip(tooltip)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedSize(btn_size, btn_size)
    btn.setIconSize(QSize(icon_size, icon_size))
    btn.setIcon(get_svg_icon(icon_name, color=color, size=icon_size))

    if callback:
        btn.clicked.connect(callback)

    return btn


def make_action_card_button(
    icon_name: str,
    label: str,
    tooltip: str,
    callback=None,
    color: str = "#e2e8f0",
    btn_width: int = 68,
    btn_height: int = 56,
    icon_size: int = 18,
    object_name: str = "actionCardButton",
    parent=None
) -> QToolButton:
    """
    Creates a rounded card action button with icon on top and text label below.
    """
    btn = QToolButton(parent) if parent else QToolButton()
    btn.setObjectName(object_name)
    btn.setText(label)
    btn.setToolTip(tooltip)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
    btn.setFixedSize(btn_width, btn_height)
    btn.setIconSize(QSize(icon_size, icon_size))
    btn.setIcon(get_svg_icon(icon_name, color=color, size=icon_size))

    if callback:
        btn.clicked.connect(callback)

    return btn


def make_labeled_button(
    icon_name: str,
    label: str,
    tooltip: str,
    callback=None,
    color: str = "#e2e8f0",
    btn_height: int = 32,
    icon_size: int = 14,
    object_name: str = "labeledButton",
    parent=None
) -> QPushButton:
    """
    Creates a horizontal button with icon + text label side by side.
    """
    btn = QPushButton(parent) if parent else QPushButton()
    btn.setObjectName(object_name)
    btn.setText(label)
    btn.setToolTip(tooltip)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(btn_height)
    if icon_name:
        btn.setIconSize(QSize(icon_size, icon_size))
        btn.setIcon(get_svg_icon(icon_name, color=color, size=icon_size))

    if callback:
        btn.clicked.connect(callback)

    return btn

