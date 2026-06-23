import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QScrollArea, QFrame, QLineEdit,
    QCheckBox, QComboBox, QSpinBox, QListWidget, QAbstractItemView,
    QMessageBox, QInputDialog, QFileDialog, QStackedWidget, QGroupBox,
    QFormLayout, QSplitter, QSizePolicy, QTextEdit, QListWidgetItem
)
from PySide6.QtCore import Qt, QSize, Signal, QPoint
from PySide6.QtGui import QPixmap, QFont, QPalette, QColor, QIcon

from app.theme_manager import (
    ALL_OPTIONS, get_sections, scan_themes, create_theme,
    get_themes_dir, Theme
)
from app.preview_renderer import REFIndPreview


class ThemeCard(QFrame):
    clicked = Signal(str)

    def __init__(self, theme_name, bg_path=None):
        super().__init__()
        self.theme_name = theme_name
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            ThemeCard {
                background: #2a2a2a;
                border: 2px solid #3a3a3a;
                border-radius: 8px;
            }
            ThemeCard:hover {
                border: 2px solid #0078d7;
                background: #333;
            }
        """)
        self.setMinimumSize(200, 180)
        self.setMaximumSize(260, 220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(200, 140)
        self.preview.setStyleSheet("background: #1a1a1a; border-radius: 8px 8px 0 0;")

        self._card_pixmap = QPixmap()
        loaded = False
        if bg_path and os.path.exists(bg_path):
            self._card_pixmap = QPixmap(bg_path)
            if not self._card_pixmap.isNull():
                self._card_pixmap = self._card_pixmap.scaled(200, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview.setPixmap(self._card_pixmap)
                loaded = True
        if not loaded:
            self.preview.setText("No Preview")
            self.preview.setStyleSheet("color: #888; background: #1a1a1a; border-radius: 8px 8px 0 0; font-size: 13px;")

        layout.addWidget(self.preview)

        name_label = QLabel(theme_name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("color: #ddd; font-size: 14px; font-weight: bold; padding: 8px;")
        layout.addWidget(name_label)

    def mousePressEvent(self, event):
        self.clicked.emit(self.theme_name)


class ThemeListPage(QWidget):
    def __init__(self, on_theme_selected, on_create_theme):
        super().__init__()
        self.on_theme_selected = on_theme_selected
        self.on_create_theme = on_create_theme
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QHBoxLayout()
        title = QLabel("rEFInd Theme Editor")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #eee;")
        header.addWidget(title)

        header.addStretch()

        create_btn = QPushButton("+ Create Theme")
        create_btn.setStyleSheet("""
            QPushButton {
                background: #0078d7;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover { background: #0086f0; }
            QPushButton:pressed { background: #006abc; }
        """)
        create_btn.clicked.connect(self.on_create_theme)
        header.addWidget(create_btn)

        layout.addLayout(header)

        sub = QLabel("Select a theme to edit and preview")
        sub.setStyleSheet("color: #999; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(sub)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(15)
        scroll.setWidget(self.grid_widget)

        layout.addWidget(scroll)

    def refresh(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        themes_dir = get_themes_dir()
        themes = scan_themes(themes_dir)

        if not themes:
            placeholder = QLabel("No themes found. Click '+ Create Theme' to get started!")
            placeholder.setStyleSheet("color: #888; font-size: 16px; padding: 60px;")
            placeholder.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(placeholder, 0, 0, 1, 4)
            return

        cols = max(1, self.width() // 240)
        for i, theme in enumerate(themes):
            bg_path = theme.get_background_path()
            card = ThemeCard(theme.name, bg_path)
            card.clicked.connect(self.on_theme_selected)
            self.grid_layout.addWidget(card, i // cols, i % cols)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refresh()


class SpinBox(QSpinBox):
    def wheelEvent(self, event):
        event.ignore()


class ComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()


class MultiChoiceWidget(QFrame):
    changed = Signal()

    def __init__(self, choices, current, parent=None):
        super().__init__(parent)
        self.choices = choices
        self.setStyleSheet("""
            MultiChoiceWidget {
                background: #222;
                border: 1px solid #444;
                border-radius: 4px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 3, 6, 3)
        layout.setSpacing(4)

        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setStyleSheet("background: transparent; color: #ccc; border: none;")
        layout.addWidget(self.display)

        self.arrow_btn = QPushButton("▼")
        self.arrow_btn.setFixedSize(20, 20)
        self.arrow_btn.setStyleSheet("""
            QPushButton {
                background: #3a3a3a; color: #aaa; border: none;
                border-radius: 3px; font-size: 10px;
            }
            QPushButton:hover { background: #4a4a4a; }
        """)
        self.arrow_btn.clicked.connect(self._toggle_popup)
        layout.addWidget(self.arrow_btn)

        self.popup = QFrame()
        self.popup.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.popup.setStyleSheet("""
            QFrame {
                background: #2a2a2a;
                border: 1px solid #555;
                border-radius: 6px;
            }
            QCheckBox {
                color: #ccc; font-size: 12px; padding: 3px 6px;
            }
            QCheckBox::indicator {
                width: 14px; height: 14px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #666; background: #222; border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #0078d7; background: #0078d7; border-radius: 3px;
            }
        """)
        popup_layout = QVBoxLayout(self.popup)
        popup_layout.setContentsMargins(6, 4, 6, 4)
        popup_layout.setSpacing(1)

        self._checkboxes = []
        current_set = set(v.strip() for v in current.split(",") if v.strip())
        for choice in choices:
            cb = QCheckBox(choice)
            cb.setChecked(choice in current_set)
            cb.toggled.connect(self._on_toggle)
            popup_layout.addWidget(cb)
            self._checkboxes.append(cb)

        self._update_display()

    def _toggle_popup(self):
        pos = self.mapToGlobal(QPoint(0, self.height()))
        self.popup.setFixedWidth(self.width())
        self.popup.move(pos)
        self.popup.show()

    def _on_toggle(self):
        self._update_display()
        self.changed.emit()

    def _update_display(self):
        selected = [cb.text() for cb in self._checkboxes if cb.isChecked()]
        self.display.setText(", ".join(selected) if selected else "None selected")
        if selected:
            self.display.setStyleSheet("background: transparent; color: #ccc; border: none;")
        else:
            self.display.setStyleSheet("background: transparent; color: #777; border: none;")

    def get_value(self):
        return ",".join(cb.text() for cb in self._checkboxes if cb.isChecked())

    def set_value(self, text):
        values = set(v.strip() for v in text.split(",") if v.strip())
        for cb in self._checkboxes:
            cb.blockSignals(True)
            cb.setChecked(cb.text() in values)
            cb.blockSignals(False)
        self._update_display()

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        self.display.setStyleSheet(
            f"background: transparent; color: {'#ccc' if enabled else '#555'}; border: none;"
        )
        self.arrow_btn.setEnabled(enabled)


class SettingWidget(QFrame):
    changed = Signal()

    def __init__(self, opt, theme, parent=None):
        super().__init__(parent)
        self.opt = opt
        self.theme = theme
        self.key = opt["key"]
        self.enabled = True
        self.value_widget = None
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            SettingWidget {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)

        header = QHBoxLayout()
        self.checkbox = QCheckBox()
        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(self.key in self.theme.settings)
        self.checkbox.blockSignals(False)
        self.checkbox.toggled.connect(self._on_toggle)

        label = QLabel(self.opt["label"])
        label.setStyleSheet("color: #ddd; font-size: 13px; font-weight: bold;")
        header.addWidget(self.checkbox)
        header.addWidget(label)
        header.addStretch()

        desc = QLabel(self.opt["desc"])
        desc.setStyleSheet("color: #777; font-size: 11px;")
        desc.setWordWrap(True)

        layout.addLayout(header)
        layout.addWidget(desc)

        val_layout = QHBoxLayout()
        self._create_value_widget(val_layout)
        layout.addLayout(val_layout)

        self._update_enabled()

    def _on_value_change(self):
        if self.checkbox.isChecked():
            self.theme.settings[self.key] = self._get_value()
        self.changed.emit()

    def _create_value_widget(self, layout):
        opt = self.opt
        t = opt["type"]
        current = self.theme.settings.get(self.key, "")
        self.browse_btn = None

        if t == "bool":
            self.value_widget = ComboBox()
            self.value_widget.addItems(["false", "true"])
            self.value_widget.setCurrentText(current if current in ("true", "false") else "false")
            self.value_widget.currentTextChanged.connect(self._on_value_change)
            layout.addWidget(self.value_widget)
        elif t == "int":
            self.value_widget = SpinBox()
            self.value_widget.setRange(-1, 999999)
            try:
                self.value_widget.setValue(int(current) if current else 0)
            except ValueError:
                self.value_widget.setValue(0)
            self.value_widget.valueChanged.connect(self._on_value_change)
            layout.addWidget(self.value_widget)
        elif t == "choice":
            self.value_widget = ComboBox()
            self.value_widget.addItems(opt.get("choices", []))
            if current in opt.get("choices", []):
                self.value_widget.setCurrentText(current)
            self.value_widget.currentTextChanged.connect(self._on_value_change)
            layout.addWidget(self.value_widget)
        elif t == "multichoice":
            self.value_widget = MultiChoiceWidget(opt.get("choices", []), current)
            self.value_widget.changed.connect(self._on_value_change)
            layout.addWidget(self.value_widget)
        elif t == "file":
            self.value_widget = QLineEdit(current)
            self.value_widget.setStyleSheet("background: #222; color: #ccc; border: 1px solid #444; border-radius: 4px; padding: 4px;")
            self.value_widget.textChanged.connect(self._on_value_change)
            layout.addWidget(self.value_widget)
            self.browse_btn = QPushButton("Browse")
            self.browse_btn.setStyleSheet("background: #444; color: #ccc; border: none; border-radius: 4px; padding: 4px 8px;")
            self.browse_btn.clicked.connect(self._browse_file)
            layout.addWidget(self.browse_btn)
        else:
            self.value_widget = QLineEdit(current)
            self.value_widget.setStyleSheet("background: #222; color: #ccc; border: 1px solid #444; border-radius: 4px; padding: 4px;")
            self.value_widget.textChanged.connect(self._on_value_change)
            layout.addWidget(self.value_widget)

    def _browse_file(self):
        subdir = self.opt.get("subdir", "")
        start_dir = self.theme.path
        if subdir:
            start_dir = os.path.join(start_dir, subdir)
        file_type = self.opt.get("file_type", "")
        if file_type == "image":
            path, _ = QFileDialog.getOpenFileName(self, "Select Image", start_dir, "Images (*.png *.bmp *.jpg *.jpeg *.icns)")
        elif file_type == "dir":
            path = QFileDialog.getExistingDirectory(self, "Select Directory", start_dir)
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select File", start_dir)
        if path:
            app_root = os.path.dirname(os.path.dirname(self.theme.path))
            rel = os.path.relpath(path, app_root)
            self.value_widget.setText(rel)
            self.changed.emit()

    def _on_toggle(self, checked):
        self._update_enabled()
        if checked:
            self.theme.settings[self.key] = self._get_value()
        elif self.key in self.theme.settings:
            del self.theme.settings[self.key]
        self.changed.emit()

    def _update_enabled(self):
        enabled = self.checkbox.isChecked()
        if self.value_widget is None:
            return
        self.value_widget.setEnabled(enabled)
        if self.browse_btn:
            self.browse_btn.setEnabled(enabled)
        if isinstance(self.value_widget, QLineEdit):
            self.value_widget.setStyleSheet(
                f"background: {'#333' if enabled else '#222'}; color: {'#ccc' if enabled else '#555'}; border: 1px solid {'#444' if enabled else '#333'}; border-radius: 4px; padding: 4px;"
            )

    def _get_value(self):
        if self.value_widget is None:
            return ""
        if isinstance(self.value_widget, QSpinBox):
            return str(self.value_widget.value())
        elif isinstance(self.value_widget, QComboBox):
            return self.value_widget.currentText()
        elif isinstance(self.value_widget, QLineEdit):
            return self.value_widget.text()
        elif isinstance(self.value_widget, MultiChoiceWidget):
            return self.value_widget.get_value()
        return ""

    def apply(self):
        if self.checkbox.isChecked():
            self.theme.settings[self.key] = self._get_value()
            self.changed.emit()
        elif self.key in self.theme.settings:
            del self.theme.settings[self.key]
            self.changed.emit()


class MenuEntryEditor(QFrame):
    changed = Signal()

    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        self.setStyleSheet("background: #222; border: 1px solid #444; border-radius: 6px;")
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        title = QLabel("Custom OS Entries (menuentry)")
        title.setStyleSheet("color: #ddd; font-size: 14px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("+ Add Entry")
        add_btn.setStyleSheet("background: #0078d7; color: white; border: none; border-radius: 4px; padding: 6px 14px;")
        add_btn.clicked.connect(self._add_entry)
        header.addWidget(add_btn)
        layout.addLayout(header)

        self.entries_widget = QVBoxLayout()
        layout.addLayout(self.entries_widget)

    def refresh(self):
        while self.entries_widget.count():
            item = self.entries_widget.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for entry in self.theme.menu_entries:
            ew = _EntryWidget(entry, self.theme)
            ew.changed.connect(self.changed.emit)
            ew.remove_requested.connect(self._remove_entry)
            self.entries_widget.addWidget(ew)

    def _add_entry(self):
        name, ok = QInputDialog.getText(self, "New OS Entry", "Entry name (e.g. 'My Linux'):")
        if ok and name.strip():
            loader_name = name.strip().lower().replace(" ", "")
            entry = {
                "name": name.strip(),
                "enabled": True,
                "settings": {
                    "icon": f"themes/{self.theme.name}/icons/os_{loader_name}.png",
                    "loader": f"/EFI/{loader_name}/grubx64.efi",
                },
                "disabled": False,
            }
            self.theme.menu_entries.append(entry)
            self.refresh()
            self.changed.emit()

    def _remove_entry(self, entry):
        if entry in self.theme.menu_entries:
            self.theme.menu_entries.remove(entry)
            self.refresh()
            self.changed.emit()


class _EntryWidget(QFrame):
    changed = Signal()
    remove_requested = Signal(object)

    def __init__(self, entry, theme, parent=None):
        super().__init__(parent)
        self.entry = entry
        self.theme = theme
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("_EntryWidget { background: #2a2a2a; border: 1px solid #3a3a3a; border-radius: 4px; margin: 2px; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)

        header = QHBoxLayout()
        name_label = QLabel(self.entry["name"])
        name_label.setStyleSheet("color: #ddd; font-size: 13px; font-weight: bold;")
        header.addWidget(name_label)
        header.addStretch()

        disabled_cb = QCheckBox("Disabled")
        disabled_cb.setChecked(self.entry.get("disabled", False))
        disabled_cb.setStyleSheet("color: #999;")
        disabled_cb.toggled.connect(self._toggle_disabled)
        header.addWidget(disabled_cb)

        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(24, 24)
        remove_btn.setStyleSheet("background: #c44; color: white; border: none; border-radius: 12px; font-size: 12px;")
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.entry))
        header.addWidget(remove_btn)

        layout.addLayout(header)

        form = QFormLayout()
        form.setContentsMargins(0, 4, 0, 0)
        for k, v in list(self.entry["settings"].items()):
            if k == "disabled":
                continue
            if k == "icon":
                self.icon_combo = QComboBox()
                self.icon_combo.setStyleSheet("""
                    QComboBox { background: #222; color: #ccc; border: 1px solid #444; border-radius: 4px; padding: 2px; }
                    QComboBox::drop-down { border: none; }
                    QComboBox QAbstractItemView { background: #2a2a2a; color: #ccc; selection-background-color: #0078d7; border: 1px solid #555; outline: none; }
                """)
                self._populate_icon_combo(self.icon_combo, v)
                self.icon_combo.currentIndexChanged.connect(self._on_icon_idx_changed)
                form.addRow("icon:", self.icon_combo)
            else:
                le = QLineEdit(v)
                le.setStyleSheet("background: #222; color: #ccc; border: 1px solid #444; border-radius: 4px; padding: 3px;")
                le.textChanged.connect(lambda text, key=k: self._update_setting(key, text))
                form.addRow(k + ":", le)
        layout.addLayout(form)

    def _populate_icon_combo(self, combo, current_value):
        combo.clear()
        icon_dir = self.theme.icons_path
        matched_idx = -1
        if os.path.isdir(icon_dir):
            for f in sorted(os.listdir(icon_dir)):
                if f.lower().endswith((".png", ".bmp", ".jpg", ".jpeg", ".icns")):
                    app_root = os.path.dirname(os.path.dirname(self.theme.path))
                    rel = os.path.relpath(os.path.join(icon_dir, f), app_root)
                    combo.addItem(f, rel)
                    if current_value and (rel == current_value or f == os.path.basename(current_value)):
                        matched_idx = combo.count() - 1
        if matched_idx >= 0:
            combo.setCurrentIndex(matched_idx)
        elif current_value:
            combo.addItem(os.path.basename(current_value), current_value)
            combo.setCurrentIndex(combo.count() - 1)

    def _on_icon_idx_changed(self, idx):
        val = self.icon_combo.itemData(idx)
        if val:
            self._update_setting("icon", val)

    def _toggle_disabled(self, v):
        self.entry["disabled"] = v
        self.changed.emit()

    def _update_setting(self, key, value):
        self.entry["settings"][key] = value
        self.changed.emit()


class ImageResourceCard(QFrame):
    changed = Signal()

    def __init__(self, label, setting_key, theme, file_type="image", parent=None):
        super().__init__(parent)
        self.label = label
        self.setting_key = setting_key
        self.theme = theme
        self.file_type = file_type
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            ImageResourceCard {
                background: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)

        header = QHBoxLayout()
        lbl = QLabel(self.label)
        lbl.setStyleSheet("color: #ccc; font-size: 12px; font-weight: bold;")
        header.addWidget(lbl)
        header.addStretch()

        self.enable_cb = QCheckBox("Enable")
        self.enable_cb.setStyleSheet("color: #999; font-size: 11px;")
        enabled = self.theme is not None and self.setting_key in self.theme.settings
        self.enable_cb.setChecked(enabled)
        self.enable_cb.toggled.connect(self._on_toggle)
        header.addWidget(self.enable_cb)
        layout.addLayout(header)

        preview_row = QHBoxLayout()

        self.preview_lbl = QLabel()
        self.preview_lbl.setFixedSize(64, 64)
        self.preview_lbl.setAlignment(Qt.AlignCenter)
        self.preview_lbl.setStyleSheet("background: #1a1a1a; border: 1px solid #444; border-radius: 4px; color: #666; font-size: 10px;")
        preview_row.addWidget(self.preview_lbl)

        info_layout = QVBoxLayout()
        self.path_edit = QLineEdit()
        current = self.theme.settings.get(self.setting_key, "") if self.theme else ""
        self.path_edit.setText(current)
        self.path_edit.setPlaceholderText("Path relative to app root")
        self.path_edit.setStyleSheet("background: #222; color: #ccc; border: 1px solid #444; border-radius: 4px; padding: 3px; font-size: 11px;")
        self.path_edit.textChanged.connect(self._on_path_change)
        info_layout.addWidget(self.path_edit)

        btn_row = QHBoxLayout()
        browse_btn = QPushButton("Browse...")
        browse_btn.setStyleSheet("background: #3a3a3a; color: #ccc; border: none; border-radius: 3px; padding: 4px 10px; font-size: 11px;")
        browse_btn.clicked.connect(self._browse)
        btn_row.addWidget(browse_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.setStyleSheet("background: #5a2a2a; color: #d88; border: none; border-radius: 3px; padding: 4px 10px; font-size: 11px;")
        remove_btn.clicked.connect(self._remove)
        btn_row.addWidget(remove_btn)

        btn_row.addStretch()
        info_layout.addLayout(btn_row)
        preview_row.addLayout(info_layout)

        layout.addLayout(preview_row)

    def _update_preview(self):
        if self.theme is None:
            self.preview_lbl.setText("No\nImage")
            self.preview_lbl.setPixmap(QPixmap())
            return
        path = self.theme.get_resolved_path(self.setting_key)
        if not path or not os.path.exists(path):
            path = self.path_edit.text()
            if path:
                path = self.theme._resolve_path(path)
        if path and os.path.exists(path):
            self._thumb_pixmap = QPixmap(path)
            if not self._thumb_pixmap.isNull():
                self._thumb_pixmap = self._thumb_pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_lbl.setPixmap(self._thumb_pixmap)
                return
        self.preview_lbl.setText("No\nImage")
        self.preview_lbl.setPixmap(QPixmap())

    def _on_path_change(self, text):
        if self.theme is None:
            return
        if self.enable_cb.isChecked() and text:
            self.theme.settings[self.setting_key] = text
            self._update_preview()
            self.changed.emit()
        elif self.setting_key in self.theme.settings:
            if not text or not self.enable_cb.isChecked():
                del self.theme.settings[self.setting_key]
            self.changed.emit()

    def _on_toggle(self, checked):
        if self.theme is None:
            return
        if checked:
            val = self.path_edit.text()
            self.theme.settings[self.setting_key] = val
            self._update_preview()
        elif self.setting_key in self.theme.settings:
            del self.theme.settings[self.setting_key]
        self.path_edit.setEnabled(checked)
        self.changed.emit()

    def _browse(self):
        if self.theme is None:
            return
        start = self.theme.path
        if self.file_type == "dir":
            path = QFileDialog.getExistingDirectory(self, "Select Directory", start)
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, f"Select {self.label}", start,
                "Images (*.png *.bmp *.jpg *.jpeg *.icns);;All Files (*)"
            )
        if path:
            app_root = os.path.dirname(os.path.dirname(self.theme.path))
            rel = os.path.relpath(path, app_root)
            self.path_edit.setText(rel)
            self.enable_cb.setChecked(True)

    def _remove(self):
        if self.theme is None:
            return
        self.path_edit.clear()
        self.enable_cb.setChecked(False)
        if self.setting_key in self.theme.settings:
            del self.theme.settings[self.setting_key]
        self._update_preview()
        self.changed.emit()

    def refresh(self):
        if self.theme is None:
            return
        current = self.theme.settings.get(self.setting_key, "")
        self.path_edit.blockSignals(True)
        self.path_edit.setText(current)
        self.path_edit.blockSignals(False)
        enabled = self.setting_key in self.theme.settings
        self.enable_cb.blockSignals(True)
        self.enable_cb.setChecked(enabled)
        self.enable_cb.blockSignals(False)
        self.path_edit.setEnabled(enabled)
        self._update_preview()


class IconManagerPanel(QFrame):
    changed = Signal()

    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            IconManagerPanel {
                background: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)

        header = QHBoxLayout()
        lbl = QLabel("Icons")
        lbl.setStyleSheet("color: #ccc; font-size: 12px; font-weight: bold;")
        header.addWidget(lbl)
        header.addStretch()

        import_btn = QPushButton("Import Icon...")
        import_btn.setStyleSheet("background: #3a3a3a; color: #ccc; border: none; border-radius: 3px; padding: 4px 10px; font-size: 11px;")
        import_btn.clicked.connect(self._import_icon)
        header.addWidget(import_btn)

        layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setMinimumHeight(100)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.icon_grid = QWidget()
        self.icon_grid.setStyleSheet("background: transparent;")
        self.grid_layout = QHBoxLayout(self.icon_grid)
        self.grid_layout.setSpacing(6)
        self.grid_layout.setContentsMargins(2, 2, 2, 2)
        self.grid_layout.addStretch()
        scroll.setWidget(self.icon_grid)
        layout.addWidget(scroll)

    def refresh(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._icon_pixmaps = []
        icons = self.theme.get_icons()
        if not icons:
            placeholder = QLabel("No icons yet. Click 'Import Icon...' to add one.")
            placeholder.setStyleSheet("color: #666; font-size: 11px; padding: 10px;")
            placeholder.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(placeholder)
            self.grid_layout.addStretch()
            return

        for ic in icons:
            frame = QFrame()
            frame.setFixedSize(72, 90)
            frame.setStyleSheet("QFrame { background: #1e1e1e; border: 1px solid #3a3a3a; border-radius: 4px; }")
            vl = QVBoxLayout(frame)
            vl.setContentsMargins(4, 4, 4, 2)
            vl.setSpacing(2)

            icon_lab = QLabel()
            icon_lab.setFixedSize(64, 56)
            icon_lab.setAlignment(Qt.AlignCenter)
            icon_lab.setStyleSheet("background: transparent; border: none;")
            ipix = QPixmap(ic["path"])
            if not ipix.isNull():
                iscaled = ipix.scaled(60, 52, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_lab.setPixmap(iscaled)
                self._icon_pixmaps.append(iscaled)
            else:
                icon_lab.setText("?")
                icon_lab.setStyleSheet("color: #666; font-size: 18px;")
            vl.addWidget(icon_lab, alignment=Qt.AlignCenter)

            name_lab = QLabel(ic["name"][:14])
            name_lab.setAlignment(Qt.AlignCenter)
            name_lab.setStyleSheet("color: #999; font-size: 9px; background: transparent; border: none;")
            name_lab.setToolTip(ic["name"])
            vl.addWidget(name_lab)

            self.grid_layout.addWidget(frame)

        self.grid_layout.addStretch()

    def _import_icon(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Icon", "",
            "Images (*.png *.bmp *.jpg *.jpeg *.icns);;All Files (*)"
        )
        if path:
            app_root = os.path.dirname(os.path.dirname(self.theme.path))
            raw = self.theme.icons_dir
            if raw.startswith("themes/"):
                dest_dir = os.path.join(app_root, raw)
            else:
                dest_dir = os.path.join(app_root, "themes", self.theme.name, raw)
            os.makedirs(dest_dir, exist_ok=True)
            fname = os.path.basename(path)
            dest = os.path.join(dest_dir, fname)
            shutil.copy2(path, dest)
            self.theme.load()
            self.refresh()
            self.changed.emit()


class EditorPage(QWidget):
    def __init__(self, on_back):
        super().__init__()
        self.on_back = on_back
        self.current_theme = None
        self.setting_widgets = []
        self.resource_cards = []
        self._section_boxes = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(10, 8, 10, 8)

        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet("""
            QPushButton {
                background: #3a3a3a;
                color: #ddd;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover { background: #4a4a4a; }
        """)
        back_btn.clicked.connect(self.on_back)
        toolbar.addWidget(back_btn)

        self.title_label = QLabel("Theme Editor")
        self.title_label.setStyleSheet("color: #eee; font-size: 18px; font-weight: bold;")
        toolbar.addWidget(self.title_label)

        toolbar.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #0078d7;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background: #0086f0; }
        """)
        save_btn.clicked.connect(self._save)
        toolbar.addWidget(save_btn)

        layout.addLayout(toolbar)

        hsplitter = QSplitter(Qt.Horizontal)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #1a1a1a; } QScrollBar:vertical { width: 8px; } QScrollBar::handle:vertical { background: #555; border-radius: 4px; }")

        self.form_widget = QWidget()
        self.form_widget.setStyleSheet("background: #1a1a1a;")
        self.form_layout = QVBoxLayout(self.form_widget)
        self.form_layout.setContentsMargins(15, 10, 15, 10)
        self.form_layout.setSpacing(4)
        self.form_layout.addStretch()
        scroll.setWidget(self.form_widget)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search options...")
        self._search_edit.setStyleSheet("background: #222; color: #ccc; border: 1px solid #444; border-radius: 4px; padding: 6px; font-size: 12px; margin-bottom: 4px;")
        self._search_edit.textChanged.connect(self._filter_options)
        self.form_layout.addWidget(self._search_edit)

        hsplitter.addWidget(scroll)

        right_panel = QWidget()
        right_panel.setStyleSheet("background: #1a1a1a;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(6)

        resources_group = QGroupBox("Theme Resources")
        resources_group.setStyleSheet("""
            QGroupBox {
                color: #aaa;
                font-size: 13px;
                font-weight: bold;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        resources_layout = QVBoxLayout(resources_group)
        resources_layout.setContentsMargins(6, 4, 6, 4)
        resources_layout.setSpacing(4)

        self.res_cards = {}
        for key in ["banner"]:
            card = ImageResourceCard("Background", key, None, "image")
            card.changed.connect(lambda: self._on_resource_change())
            card.enable_cb.toggled.connect(lambda checked, k=key: self._sync_setting_widget(k))
            card.path_edit.textChanged.connect(lambda text, k=key: self._sync_setting_widget(k))
            self.res_cards[key] = card
            resources_layout.addWidget(card)

        for key in ["selection_big"]:
            card = ImageResourceCard("Selection Big", key, None, "image")
            card.changed.connect(lambda: self._on_resource_change())
            card.enable_cb.toggled.connect(lambda checked, k=key: self._sync_setting_widget(k))
            card.path_edit.textChanged.connect(lambda text, k=key: self._sync_setting_widget(k))
            self.res_cards[key] = card
            resources_layout.addWidget(card)

        for key in ["selection_small"]:
            card = ImageResourceCard("Selection Small", key, None, "image")
            card.changed.connect(lambda: self._on_resource_change())
            card.enable_cb.toggled.connect(lambda checked, k=key: self._sync_setting_widget(k))
            card.path_edit.textChanged.connect(lambda text, k=key: self._sync_setting_widget(k))
            self.res_cards[key] = card
            resources_layout.addWidget(card)

        self.icon_manager = IconManagerPanel(None)
        self.icon_manager.changed.connect(lambda: self._on_resource_change())
        resources_layout.addWidget(self.icon_manager)

        right_layout.addWidget(resources_group)

        preview_group = QGroupBox("Preview")
        preview_group.setStyleSheet("""
            QGroupBox {
                color: #aaa;
                font-size: 13px;
                font-weight: bold;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(4, 4, 4, 4)

        self.preview = REFIndPreview()
        self.preview.setStyleSheet("background: #111; border-radius: 4px;")
        preview_layout.addWidget(self.preview)
        right_layout.addWidget(preview_group)

        hsplitter.addWidget(right_panel)
        hsplitter.setSizes([400, 600])

        layout.addWidget(hsplitter)

    def _on_resource_change(self):
        for key in self.res_cards:
            self._sync_setting_widget(key)
        if self.preview:
            self.preview.update()

    def _sync_setting_widget(self, key):
        for sw in self.setting_widgets:
            if sw.key == key:
                enabled = key in self.current_theme.settings
                sw.checkbox.blockSignals(True)
                sw.checkbox.setChecked(enabled)
                sw.checkbox.blockSignals(False)
                val = self.current_theme.settings.get(key, "")
                if isinstance(sw.value_widget, QLineEdit):
                    sw.value_widget.blockSignals(True)
                    sw.value_widget.setText(val)
                    sw.value_widget.blockSignals(False)
                elif isinstance(sw.value_widget, MultiChoiceWidget):
                    sw.value_widget.set_value(val)
                sw._update_enabled()
                break

    def _sync_resource_card(self, key):
        card = self.res_cards.get(key)
        if card and card.theme:
            card.refresh()

    def load_theme(self, theme):
        self.current_theme = theme
        self.title_label.setText(f"Editing: {theme.name}")
        self._build_form()
        for card in self.res_cards.values():
            card.theme = theme
            card.refresh()
        self.icon_manager.theme = theme
        self.icon_manager.refresh()
        self.preview.set_theme(theme)

    def _build_form(self):
        # Remove search edit from layout without deleting it
        search_item = None
        for i in range(self.form_layout.count()):
            item = self.form_layout.itemAt(i)
            if item and item.widget() is self._search_edit:
                search_item = self.form_layout.takeAt(i)
                break

        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.setting_widgets = []
        self._section_boxes = []

        if not self.current_theme:
            if search_item:
                self.form_layout.addWidget(self._search_edit)
            return

        if search_item:
            self.form_layout.addWidget(self._search_edit)

        self._search_edit.clear()
        self._search_edit.show()

        for section_name, options in get_sections():
            gb = QGroupBox(section_name)
            gb.setStyleSheet("""
                QGroupBox {
                    color: #aaa;
                    font-size: 14px;
                    font-weight: bold;
                    border: 1px solid #3a3a3a;
                    border-radius: 6px;
                    margin-top: 12px;
                    padding-top: 16px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 6px;
                }
            """)
            section_layout = QVBoxLayout(gb)
            section_layout.setSpacing(6)

            section_widgets = []
            for opt in options:
                sw = SettingWidget(opt, self.current_theme)
                sw.changed.connect(lambda: self.preview.update())
                if opt["type"] == "file":
                    sw.changed.connect(lambda k=opt["key"]: self._sync_resource_card(k))
                self.setting_widgets.append(sw)
                section_layout.addWidget(sw)
                section_widgets.append(sw)

            section_layout.addStretch()
            self.form_layout.addWidget(gb)
            self._section_boxes.append((gb, section_widgets))

        # Menu entries editor
        me = MenuEntryEditor(self.current_theme)
        me.changed.connect(lambda: self.preview.update())
        self.form_layout.addWidget(me)

        self.form_layout.addStretch()

    def _filter_options(self, text):
        text = text.lower()
        for gb, widgets in self._section_boxes:
            any_visible = False
            for sw in widgets:
                match = (
                    not text
                    or text in sw.key.lower()
                    or text in sw.opt["label"].lower()
                    or text in sw.opt.get("desc", "").lower()
                )
                sw.setVisible(match)
                if match:
                    any_visible = True
            gb.setVisible(any_visible)

    def _save(self):
        if not self.current_theme:
            return
        for key in self.res_cards:
            self._sync_setting_widget(key)
        for sw in self.setting_widgets:
            sw.apply()
        self.current_theme.save()
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(f"Theme '{self.current_theme.name}' saved successfully!")
        msg.setStyleSheet("color: #ddd; background: #2a2a2a;")
        msg.exec()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("rEFInd Theme Editor")
        self.setMinimumSize(1024, 700)
        self.setStyleSheet("""
            QMainWindow { background: #1a1a1a; }
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: #252525;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QInputDialog {
                background: #2a2a2a;
                color: #ddd;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)

        self.stack = QStackedWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

        self.theme_list = ThemeListPage(
            on_theme_selected=self._open_theme,
            on_create_theme=self._create_theme
        )
        self.editor = EditorPage(on_back=self._go_back)

        self.stack.addWidget(self.theme_list)
        self.stack.addWidget(self.editor)
        self.stack.setCurrentWidget(self.theme_list)

    def showEvent(self, event):
        super().showEvent(event)
        self.theme_list.refresh()

    def _open_theme(self, theme_name):
        themes_dir = get_themes_dir()
        theme_path = os.path.join(themes_dir, theme_name)
        if os.path.isdir(theme_path):
            theme = Theme(theme_path)
            self.editor.load_theme(theme)
            self.stack.setCurrentWidget(self.editor)

    def _create_theme(self):
        name, ok = QInputDialog.getText(self, "Create Theme", "Theme name:")
        if ok and name.strip():
            themes_dir = get_themes_dir()
            theme = create_theme(themes_dir, name.strip())
            if theme:
                self._open_theme(theme.name)
            else:
                QMessageBox.warning(self, "Error", f"Theme '{name}' already exists!")

    def _go_back(self):
        self.stack.setCurrentWidget(self.theme_list)
        self.theme_list.refresh()
