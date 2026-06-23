import os
import math
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QPixmap, QFont, QFontMetrics
from PySide6.QtWidgets import QWidget


class REFIndPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme = None
        self.selected_index = 0
        self.bg_color = QColor(30, 30, 30)
        self.setMinimumSize(400, 300)

    def set_theme(self, theme):
        self.theme = theme
        self.selected_index = 0
        self.update()

    def reload(self):
        if self.theme:
            self.theme.load()
        self.update()

    def paintEvent(self, event):
        if not self.theme:
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor(40, 40, 40))
            painter.setPen(QColor(180, 180, 180))
            painter.drawText(self.rect(), Qt.AlignCenter, "Select a theme to preview")
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w = self.width()
        h = self.height()

        bg_img = self._load_image(self.theme.get_background_path())

        if bg_img and not bg_img.isNull():
            pix = bg_img.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = (pix.width() - w) // 2
            y = (pix.height() - h) // 2
            painter.drawPixmap(0, 0, w, h, pix, x, y, w, h)
        else:
            painter.fillRect(self.rect(), self.bg_color)

        big_size = int(self.theme.settings.get("big_icon_size", "128"))
        small_size = int(self.theme.settings.get("small_icon_size", "48"))

        big_size = min(big_size, max(32, w // 4 - 20))
        small_size = min(small_size, max(24, big_size // 2))

        os_icons = self._get_preview_icons()
        sel_big = self._load_image(self.theme.get_selection_big_path())

        if os_icons and self.selected_index < len(os_icons):
            self._draw_selection(painter, os_icons, self.selected_index, big_size, w, h, sel_big)

        if os_icons:
            self._draw_icon_row(painter, os_icons, big_size, w, h)

        tool_icons = self._get_tool_preview_icons()
        if tool_icons:
            self._draw_tool_row(painter, tool_icons, small_size, w, h)

    def _get_entry_icons(self):
        icons = []
        for entry in self.theme.menu_entries:
            if not entry.get("enabled", True):
                continue
            icon_path = entry["settings"].get("icon", "")
            if not icon_path:
                continue
            resolved = self.theme._resolve_path(icon_path)
            if resolved and os.path.exists(resolved):
                icons.append({"path": resolved, "name": entry["name"], "filename": os.path.basename(resolved)})
        return icons

    def _get_preview_icons(self):
        return self.theme.get_os_icons() + self._get_entry_icons()

    def _get_tool_preview_icons(self):
        os_icons = self.theme.get_os_icons()
        tool_icons = [ic for ic in os_icons if ic["name"].startswith("tool_") or ic["name"].startswith("func_")]
        if not tool_icons:
            tool_icons = [ic for ic in self.theme.get_icons() if ic["name"].startswith("tool_") or ic["name"].startswith("func_")]
        return tool_icons

    def _load_image(self, path):
        if path and os.path.exists(path):
            return QPixmap(path)
        return QPixmap()

    def _draw_icon_row(self, painter, icons, icon_size, w, h):
        n = min(len(icons), 8)
        if n == 0:
            return
        spacing = icon_size // 5 + 10
        total_w = n * (icon_size + spacing) - spacing
        start_x = (w - total_w) // 2
        y = h // 3

        for i, ic in enumerate(icons[:n]):
            pix = QPixmap(ic["path"])
            if pix.isNull():
                pix = self._default_icon(icon_size)
            else:
                pix = pix.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = start_x + i * (icon_size + spacing)
            px = x + (icon_size - pix.width()) // 2
            py = y + (icon_size - pix.height()) // 2
            painter.drawPixmap(px, py, pix)

            label = ic["name"].replace("os_", "").replace("func_", "").replace("tool_", "").replace("_", " ").title()
            painter.setPen(QColor(220, 220, 220))
            f = QFont("sans-serif", max(8, icon_size // 16))
            painter.setFont(f)
            fm = QFontMetrics(f)
            tw = fm.horizontalAdvance(label)
            lx = x + (icon_size - tw) // 2
            painter.drawText(lx, y + icon_size + 14, label)

    def _draw_selection(self, painter, icons, idx, icon_size, w, h, sel_img):
        n = min(len(icons), 8)
        spacing = icon_size // 5 + 10
        total_w = n * (icon_size + spacing) - spacing
        start_x = (w - total_w) // 2
        y = h // 3
        x = start_x + idx * (icon_size + spacing)

        if sel_img and not sel_img.isNull():
            pad = icon_size // 8
            s = sel_img.scaled(icon_size + pad * 2, icon_size + pad * 2, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            sx = x + (icon_size + pad * 2 - s.width()) // 2
            sy = y + (icon_size + pad * 2 - s.height()) // 2
            painter.drawPixmap(sx - pad, sy - pad, s)
        else:
            painter.setPen(QColor(0, 120, 215, 200))
            painter.setBrush(QColor(0, 120, 215, 50))
            painter.drawRoundedRect(x - 6, y - 6, icon_size + 12, icon_size + 12, 8, 8)

    def _draw_tool_row(self, painter, icons, icon_size, w, h):
        n = min(len(icons), 8)
        if n == 0:
            return
        spacing = icon_size // 5 + 8
        total_w = n * (icon_size + spacing) - spacing
        start_x = (w - total_w) // 2
        y = h - icon_size - 30

        for i, ic in enumerate(icons[:n]):
            pix = QPixmap(ic["path"])
            if pix.isNull():
                continue
            pix = pix.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = start_x + i * (icon_size + spacing)
            px = x + (icon_size - pix.width()) // 2
            py = y + (icon_size - pix.height()) // 2
            painter.drawPixmap(px, py, pix)

    def _default_icon(self, size):
        pix = QPixmap(size, size)
        pix.fill(QColor(80, 80, 80, 200))
        return pix

    def mousePressEvent(self, event):
        if not self.theme:
            return
        os_icons = self._get_preview_icons()
        if not os_icons:
            return
        n = min(len(os_icons), 8)
        if n == 0:
            return
        icon_size = int(self.theme.settings.get("big_icon_size", "128"))
        spacing = icon_size // 5 + 10
        w = self.width()
        total_w = n * (icon_size + spacing) - spacing
        start_x = (w - total_w) // 2
        y = self.height() // 3
        x = event.position().x()
        y_click = event.position().y()
        if y - 10 <= y_click <= y + icon_size + 30:
            idx = int((x - start_x) // (icon_size + spacing))
            if 0 <= idx < n:
                self.selected_index = idx
                self.update()
