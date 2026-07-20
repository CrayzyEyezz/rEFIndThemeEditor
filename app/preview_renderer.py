import os
import math
from PySide6.QtCore import Qt, QRect, QRectF, QPointF, QPropertyAnimation, QEasingCurve, QSize, Property, Signal
from PySide6.QtGui import QPainter, QColor, QPixmap, QFont, QFontMetrics, QLinearGradient, QRadialGradient, QBrush, QPen, QPainterPath
from PySide6.QtWidgets import QWidget


class REFIndPreview(QWidget):
    selection_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme = None
        self.hover_index = -1

        self._hover_anim_progress = 0.0
        self._hover_anim = QPropertyAnimation(self, b"hover_anim_progress")
        self._hover_anim.setDuration(150)
        self._hover_anim.setEasingCurve(QEasingCurve.OutCubic)

        self._pulse_progress = 0.0
        self._pulse_anim = QPropertyAnimation(self, b"pulse_progress")
        self._pulse_anim.setDuration(1500)
        self._pulse_anim.setLoopCount(-1)
        self._pulse_anim.setStartValue(0.0)
        self._pulse_anim.setEndValue(1.0)
        self._pulse_anim.setEasingCurve(QEasingCurve.InOutSine)
        self._pulse_anim.start()

        self.setMinimumSize(560, 400)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        self._cached_icons = {}
        self._bg_cache = None
        self._bg_cache_size = QSize(0, 0)
        self._selection_big_cache = None
        self._selection_small_cache = None

        self._bg_color = QColor(18, 18, 22)
        self._icon_label_color = QColor(200, 200, 200)
        self._selection_glow_color = QColor(0, 120, 215, 180)
        self._selection_bg_color = QColor(0, 120, 215, 30)

    def get_hover_anim_progress(self):
        return self._hover_anim_progress

    def set_hover_anim_progress(self, v):
        self._hover_anim_progress = v
        self.update()

    hover_anim_progress = Property(float, get_hover_anim_progress, set_hover_anim_progress)

    def get_pulse_progress(self):
        return self._pulse_progress

    def set_pulse_progress(self, v):
        self._pulse_progress = v
        self.update()

    pulse_progress = Property(float, get_pulse_progress, set_pulse_progress)

    def set_theme(self, theme):
        self.theme = theme
        self.hover_index = -1
        self._clear_caches()
        self.update()

    def reload(self):
        if self.theme:
            self.theme.load()
        self._clear_caches()
        self.update()

    def _clear_caches(self):
        self._cached_icons.clear()
        self._bg_cache = None
        self._bg_cache_size = QSize(0, 0)
        self._selection_big_cache = None
        self._selection_small_cache = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.TextAntialiasing)

        w = self.width()
        h = self.height()

        if not self.theme:
            self._draw_empty_state(painter, w, h)
            return

        self._draw_background(painter, w, h)
        self._draw_os_row(painter, w, h)
        self._draw_tool_row(painter, w, h)

    def _draw_empty_state(self, painter, w, h):
        painter.fillRect(0, 0, w, h, QColor(28, 28, 34))
        painter.setPen(QColor(120, 120, 130))
        font = QFont("Inter", 14, QFont.Medium)
        painter.setFont(font)
        painter.drawText(QRect(0, 0, w, h), Qt.AlignCenter, "Select a theme to preview")

    def _draw_background(self, painter, w, h):
        if self._bg_cache and self._bg_cache_size == self.size():
            painter.drawPixmap(0, 0, self._bg_cache)
            return

        bg_path = self.theme.get_background_path() if self.theme else None
        if bg_path and os.path.exists(bg_path):
            bg_img = QPixmap(bg_path)
            if not bg_img.isNull():
                scaled = bg_img.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                x = (scaled.width() - w) // 2
                y = (scaled.height() - h) // 2
                painter.drawPixmap(0, 0, w, h, scaled, x, y, w, h)

                self._bg_cache = QPixmap(scaled)
                self._bg_cache_size = self.size()
                return

        painter.fillRect(0, 0, w, h, self._bg_color)

        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor(25, 25, 35, 80))
        grad.setColorAt(0.5, QColor(20, 20, 30, 40))
        grad.setColorAt(1, QColor(15, 15, 25, 100))
        painter.fillRect(0, 0, w, h, grad)

    def _draw_os_row(self, painter, w, h):
        icons = self._get_preview_icons()
        if not icons:
            return

        n = min(len(icons), 8)
        if n == 0:
            return

        big_size = int(self.theme.settings.get("big_icon_size", "128"))
        big_size = min(big_size, max(64, w // 6 - 16))

        spacing = max(16, big_size // 5)
        total_w = n * (big_size + spacing) - spacing
        start_x = (w - total_w) // 2
        y = int(h * 0.3)

        sel_big = self._get_selection_big()

        for i, ic in enumerate(icons[:n]):
            x = start_x + i * (big_size + spacing)
            icon_rect = QRectF(x, y, big_size, big_size)

            is_hovered = (i == self.hover_index)

            self._draw_os_icon(painter, ic, icon_rect, big_size, is_hovered, sel_big)

    def _draw_os_icon(self, painter, ic, rect, icon_size, is_hovered, sel_big):
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()

        pix = self._get_cached_icon(ic["path"], icon_size)
        if pix.isNull():
            pix = self._default_icon(icon_size)

        icon_x = x + (w - pix.width()) / 2
        icon_y = y + (h - pix.height()) / 2

        hover_scale = 1.0 + 0.05 * self._hover_anim_progress if is_hovered else 1.0

        if hover_scale != 1.0:
            painter.save()
            painter.translate(icon_x + pix.width() / 2, icon_y + pix.height() / 2)
            painter.scale(hover_scale, hover_scale)
            painter.translate(-pix.width() / 2, -pix.height() / 2)
            painter.drawPixmap(0, 0, pix)
            painter.restore()
        else:
            painter.drawPixmap(icon_x, icon_y, pix)

        if is_hovered:
            if sel_big and not sel_big.isNull():
                pad = int(icon_size * 0.15)
                sel_w = icon_size + pad * 2
                sel_h = icon_size + pad * 2
                scaled_sel = sel_big.scaled(sel_w, sel_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                sel_x = x + (icon_size - scaled_sel.width()) / 2 - pad
                sel_y = y + (icon_size - scaled_sel.height()) / 2 - pad

                painter.save()
                painter.setOpacity(0.6 + 0.2 * self._hover_anim_progress)
                painter.drawPixmap(sel_x, sel_y, scaled_sel)
                painter.restore()
            else:
                glow_alpha = int(100 + 60 * math.sin(self._pulse_progress * math.pi * 2))
                glow_color = QColor(self._selection_glow_color)
                glow_color.setAlpha(glow_alpha)

                path = QPainterPath()
                r = icon_size * 0.55
                path.addRoundedRect(x + w/2 - r, y + h/2 - r, r*2, r*2, 12, 12)

                painter.save()
                pen = QPen(glow_color, 3)
                painter.setPen(pen)
                painter.setBrush(QBrush(QColor(self._selection_bg_color)))
                painter.drawPath(path)
                painter.restore()

        label = ic["name"].replace("os_", "").replace("func_", "").replace("tool_", "").replace("_", " ").title()
        font_size = max(10, min(13, icon_size // 11))
        font = QFont("Inter", font_size, QFont.Medium)
        painter.setFont(font)
        painter.setPen(QColor(220, 220, 220))
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(label)
        lx = x + (icon_size - tw) / 2
        painter.drawText(lx, y + icon_size + 18, label)

    def _draw_tool_row(self, painter, w, h):
        tool_icons = self._get_tool_preview_icons()
        if not tool_icons:
            return

        small_size = int(self.theme.settings.get("small_icon_size", "48"))
        small_size = min(small_size, max(32, int(small_size * 0.8)))

        n = min(len(tool_icons), 12)
        spacing = max(10, small_size // 4)
        total_w = n * (small_size + spacing) - spacing
        start_x = (w - total_w) // 2
        y = h - small_size - 30

        for i, ic in enumerate(tool_icons[:n]):
            x = start_x + i * (small_size + spacing)
            pix = self._get_cached_icon(ic["path"], small_size)
            if pix.isNull():
                continue
            pix = pix.scaled(small_size, small_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            px = x + (small_size - pix.width()) / 2
            py = y + (small_size - pix.height()) / 2
            painter.drawPixmap(px, py, pix)

            # Draw label under tool icon
            label = ic["name"].replace("tool_", "").replace("func_", "").replace("arrow_", "").replace("_", " ").title()
            if label == "Mouse":
                label = "Mouse"
            font_size = max(8, min(10, small_size // 6))
            font = QFont("Inter", font_size, QFont.Medium)
            painter.setFont(font)
            painter.setPen(QColor(180, 180, 180))
            fm = QFontMetrics(font)
            tw = fm.horizontalAdvance(label)
            lx = x + (small_size - tw) / 2
            painter.drawText(lx, y + small_size + 14, label)

    def _get_preview_icons(self):
        return self.theme.get_os_icons() + self._get_entry_icons()

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

    def _get_tool_preview_icons(self):
        """Get all available tool/function icons from the theme's icons folder.
        Includes standard rEFInd tool icons that may be present."""
        if not self.theme:
            return []
        
        all_icons = self.theme.get_icons()
        
        # Standard rEFInd tool/function icon prefixes
        tool_prefixes = (
            "tool_", "func_",
            "arrow_",  # arrow_left, arrow_right
            "mouse",   # mouse pointer
        )
        
        tool_icons = []
        for ic in all_icons:
            name = ic["name"]
            if any(name.startswith(prefix) for prefix in tool_prefixes):
                tool_icons.append(ic)
        
        # Sort by name for consistent ordering
        tool_icons.sort(key=lambda x: x["name"])
        
        # Limit to 12 icons max for the tool row
        return tool_icons[:12]

    def _get_cached_icon(self, path, size):
        key = (path, size)
        if key in self._cached_icons:
            return self._cached_icons[key]
        if path and os.path.exists(path):
            pix = QPixmap(path)
            if not pix.isNull():
                pix = pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self._cached_icons[key] = pix
                return pix
        return QPixmap()

    def _get_selection_big(self):
        if self._selection_big_cache:
            return self._selection_big_cache
        path = self.theme.get_selection_big_path() if self.theme else None
        if path and os.path.exists(path):
            self._selection_big_cache = QPixmap(path)
        return self._selection_big_cache

    def _get_selection_small(self):
        if self._selection_small_cache:
            return self._selection_small_cache
        path = self.theme.get_selection_small_path() if self.theme else None
        if path and os.path.exists(path):
            self._selection_small_cache = QPixmap(path)
        return self._selection_small_cache

    def _default_icon(self, size):
        pix = QPixmap(size, size)
        pix.fill(QColor(80, 80, 80, 200))
        return pix

    def mouseMoveEvent(self, event):
        if not self.theme:
            return
        os_icons = self._get_preview_icons()
        if not os_icons:
            return
        n = min(len(os_icons), 8)
        if n == 0:
            return
        icon_size = int(self.theme.settings.get("big_icon_size", "128"))
        icon_size = min(icon_size, max(64, self.width() // 6 - 16))
        spacing = max(16, icon_size // 5)
        w = self.width()
        total_w = n * (icon_size + spacing) - spacing
        start_x = (w - total_w) // 2
        y = int(self.height() * 0.3)
        x = event.position().x()
        y_click = event.position().y()
        if y - 10 <= y_click <= y + icon_size + 30:
            idx = int((x - start_x) // (icon_size + spacing))
            if 0 <= idx < n:
                if idx != self.hover_index:
                    self.hover_index = idx
                    self._hover_anim.stop()
                    self._hover_anim.setStartValue(self._hover_anim_progress)
                    self._hover_anim.setEndValue(1.0)
                    self._hover_anim.start()
                self.selection_changed.emit(idx)
            else:
                self._reset_hover()
        else:
            self._reset_hover()

    def leaveEvent(self, event):
        self._reset_hover()
        super().leaveEvent(event)

    def _reset_hover(self):
        if self.hover_index != -1:
            self.hover_index = -1
            self._hover_anim.stop()
            self._hover_anim.setStartValue(self._hover_anim_progress)
            self._hover_anim.setEndValue(0.0)
            self._hover_anim.start()

    def keyPressEvent(self, event):
        if not self.theme:
            return
        icons = self._get_preview_icons()
        if not icons:
            return
        n = min(len(icons), 8)
        if event.key() == Qt.Key_Left:
            self.hover_index = (self.hover_index - 1) % n if self.hover_index >= 0 else 0
            self._hover_anim.stop()
            self._hover_anim.setStartValue(self._hover_anim_progress)
            self._hover_anim.setEndValue(1.0)
            self._hover_anim.start()
            self.selection_changed.emit(self.hover_index)
        elif event.key() == Qt.Key_Right:
            self.hover_index = (self.hover_index + 1) % n if self.hover_index >= 0 else 0
            self._hover_anim.stop()
            self._hover_anim.setStartValue(self._hover_anim_progress)
            self._hover_anim.setEndValue(1.0)
            self._hover_anim.start()
            self.selection_changed.emit(self.hover_index)
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.selection_changed.emit(self.hover_index if self.hover_index >= 0 else 0)