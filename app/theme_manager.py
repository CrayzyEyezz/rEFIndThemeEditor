import os
import re
import shutil

THEMES_DIR_NAME = "themes"

ALL_OPTIONS = [
    {"key": "timeout", "type": "int", "section": "General", "label": "Timeout (seconds)", "desc": "Timeout in seconds for the main menu screen. 0 = no timeout, -1 = immediate boot."},
    {"key": "default_selection", "type": "string", "section": "General", "label": "Default Selection", "desc": "Tag name or disk label to boot by default."},
    {"key": "log_level", "type": "int", "section": "General", "label": "Log Level", "desc": "Logging level (0-4). 0 = no logging."},
    {"key": "screensaver", "type": "int", "section": "General", "label": "Screensaver (seconds)", "desc": "Screen blanks after this many seconds. -1 = start blanked. 0 = disabled."},
    {"key": "shutdown_after_timeout", "type": "bool", "section": "General", "label": "Shutdown After Timeout", "desc": "Shut down instead of booting default after timeout."},
    {"key": "use_nvram", "type": "bool", "section": "General", "label": "Use NVRAM", "desc": "Store variables in NVRAM (true) or in files on disk (false)."},

    {"key": "banner", "type": "file", "section": "Visual", "label": "Banner Image", "desc": "Background/banner image (PNG, BMP, or JPEG).", "file_type": "image", "subdir": "assets"},
    {"key": "banner_scale", "type": "choice", "section": "Visual", "label": "Banner Scale", "choices": ["noscale", "fillscreen"], "desc": "How to scale the banner image."},
    {"key": "icons_dir", "type": "file", "section": "Visual", "label": "Icons Directory", "desc": "Subdirectory for icons (relative to theme root).", "file_type": "dir"},
    {"key": "small_icon_size", "type": "int", "section": "Visual", "label": "Small Icon Size", "desc": "Size of small icons (for tools and second-row OS icons)."},
    {"key": "big_icon_size", "type": "int", "section": "Visual", "label": "Big Icon Size", "desc": "Size of large/boot option icons."},
    {"key": "selection_big", "type": "file", "section": "Visual", "label": "Selection Big Image", "desc": "Background for selected big icon.", "file_type": "image", "subdir": "assets"},
    {"key": "selection_small", "type": "file", "section": "Visual", "label": "Selection Small Image", "desc": "Background for selected small icon.", "file_type": "image", "subdir": "assets"},
    {"key": "font", "type": "file", "section": "Visual", "label": "Font", "desc": "Custom font image file.", "file_type": "image", "subdir": "assets"},
    {"key": "textonly", "type": "bool", "section": "Visual", "label": "Text Only Mode", "desc": "Disable graphics and show only text menu."},
    {"key": "textmode", "type": "choice", "section": "Visual", "label": "Text Mode", "choices": ["0", "1", "2", "3", "1024"], "desc": "Text mode video mode. 0=80x25, 1=80x50, 2-3=system-specific, 1024=no change."},
    {"key": "hideui", "type": "multichoice", "section": "Visual", "label": "Hide UI Elements", "choices": ["banner", "label", "singleuser", "safemode", "hwtest", "arrows", "hints", "editor", "badges", "all"], "desc": "UI elements to hide."},
    {"key": "showtools", "type": "multichoice", "section": "Visual", "label": "Show Tools", "choices": ["shell", "memtest", "gdisk", "gptsync", "install", "bootorder", "apple_recovery", "csr_rotate", "windows_recovery", "mok_tool", "fwupdate", "netboot", "about", "hidden_tags", "exit", "shutdown", "reboot", "firmware"], "desc": "Tool entries to show on the tools row."},
    {"key": "mouse_size", "type": "int", "section": "Visual", "label": "Mouse Pointer Size", "desc": "Size of the mouse pointer in pixels."},

    {"key": "resolution", "type": "string", "section": "Display", "label": "Resolution", "desc": "Display resolution (e.g. '1024 768', '1440 900', 'max', '3')."},
    {"key": "enable_mouse", "type": "bool", "section": "Input", "label": "Enable Mouse", "desc": "Enable mouse support."},
    {"key": "enable_touch", "type": "bool", "section": "Input", "label": "Enable Touch", "desc": "Enable touchscreen support."},
    {"key": "mouse_speed", "type": "int", "section": "Input", "label": "Mouse Speed", "desc": "Mouse pointer speed multiplier."},

    {"key": "scanfor", "type": "multichoice", "section": "Scanning", "label": "Scan For", "choices": ["internal", "external", "optical", "netboot", "hdbios", "biosexternal", "cd", "manual", "firmware"], "desc": "Types of devices to scan for boot loaders."},
    {"key": "also_scan_dirs", "type": "string", "section": "Scanning", "label": "Also Scan Directories", "desc": "Additional directories to scan for boot loaders."},
    {"key": "dont_scan_volumes", "type": "string", "section": "Scanning", "label": "Don't Scan Volumes", "desc": "Volumes to skip when scanning."},
    {"key": "dont_scan_dirs", "type": "string", "section": "Scanning", "label": "Don't Scan Directories", "desc": "Directories to skip when scanning."},
    {"key": "dont_scan_files", "type": "string", "section": "Scanning", "label": "Don't Scan Files", "desc": "Files to skip when scanning."},
    {"key": "dont_scan_firmware", "type": "string", "section": "Scanning", "label": "Don't Scan Firmware", "desc": "Firmware types to skip."},
    {"key": "scan_delay", "type": "int", "section": "Scanning", "label": "Scan Delay", "desc": "Delay in seconds before scanning disks."},
    {"key": "scan_all_linux_kernels", "type": "bool", "section": "Scanning", "label": "Scan All Linux Kernels", "desc": "Scan for all Linux kernels instead of just the most recent."},
    {"key": "fold_linux_kernels", "type": "bool", "section": "Scanning", "label": "Fold Linux Kernels", "desc": "Group Linux kernel entries into submenus."},
    {"key": "support_gzipped_loaders", "type": "bool", "section": "Scanning", "label": "Support Gzipped Loaders", "desc": "Scan for and boot gzipped EFI executables."},
    {"key": "linux_prefixes", "type": "string", "section": "Scanning", "label": "Linux Kernel Prefixes", "desc": "Kernel filename prefixes to recognize."},
    {"key": "extra_kernel_version_strings", "type": "string", "section": "Scanning", "label": "Extra Kernel Version Strings", "desc": "Additional strings in kernel filenames to treat as version info."},
    {"key": "also_scan_tool_dirs", "type": "string", "section": "Scanning", "label": "Also Scan Tool Dirs", "desc": "Additional directories with EFI tools."},
    {"key": "dont_scan_tools", "type": "string", "section": "Scanning", "label": "Don't Scan Tools", "desc": "EFI tools to skip."},
    {"key": "windows_recovery_files", "type": "string", "section": "Scanning", "label": "Windows Recovery Files", "desc": "Windows recovery tool locations."},
    {"key": "scan_driver_dirs", "type": "string", "section": "Scanning", "label": "Scan Driver Directories", "desc": "Directories with EFI drivers."},
    {"key": "uefi_deep_legacy_scan", "type": "bool", "section": "Scanning", "label": "UEFI Deep Legacy Scan", "desc": "Perform deep scan for legacy boot loaders."},
    {"key": "use_graphics_for", "type": "multichoice", "section": "Scanning", "label": "Use Graphics For", "choices": ["osx", "linux", "elilo", "grub", "windows"], "desc": "OS types to use graphics mode for instead of text."},

    {"key": "follow_symlinks", "type": "bool", "section": "Advanced", "label": "Follow Symlinks", "desc": "Follow symbolic links when scanning."},
    {"key": "write_systemd_vars", "type": "bool", "section": "Advanced", "label": "Write systemd Variables", "desc": "Tell systemd where the ESP is mounted."},
    {"key": "max_tags", "type": "int", "section": "Advanced", "label": "Max Tags", "desc": "Maximum number of hidden tags to remember. 0 = unlimited."},
    {"key": "enable_and_lock_vmx", "type": "bool", "section": "Advanced", "label": "Enable & Lock VMX", "desc": "Enable and lock Intel VMX (for Hyper-V compatibility)."},
    {"key": "spoof_osx_version", "type": "string", "section": "Advanced", "label": "Spoof OS X Version", "desc": "Fake the macOS version reported to the bootloader."},
    {"key": "csr_values", "type": "string", "section": "Advanced", "label": "CSR Values", "desc": "System Integrity Protection (SIP) configuration values."},
    {"key": "include", "type": "string", "section": "Advanced", "label": "Include", "desc": "Include another configuration file."},
]

SECTION_ORDER = ["General", "Visual", "Display", "Input", "Scanning", "Advanced"]


def get_sections():
    sections = {}
    for opt in ALL_OPTIONS:
        s = opt["section"]
        if s not in sections:
            sections[s] = []
        sections[s].append(opt)
    result = []
    for s in SECTION_ORDER:
        if s in sections:
            result.append((s, sections[s]))
    return result


class Theme:
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.settings = {}
        self.menu_entries = []
        self.load()

    @property
    def icons_dir(self):
        return self.settings.get("icons_dir", "icons")

    @property
    def icons_path(self):
        val = self.icons_dir
        if not val:
            val = "icons"
        app_root = os.path.dirname(os.path.dirname(self.path))
        candidates = [
            os.path.join(app_root, val),
            os.path.join(self.path, val),
        ]
        if os.path.isabs(val):
            candidates.insert(0, val)
        for p in candidates:
            if os.path.isdir(p) and any(
                f.lower().endswith((".png", ".bmp", ".jpg", ".jpeg", ".icns"))
                for f in os.listdir(p)
            ):
                return p
        return candidates[0]

    @property
    def assets_path(self):
        return os.path.join(self.path, "assets")

    def load(self):
        conf_path = os.path.join(self.path, "refind.conf")
        self.settings = {}
        self.menu_entries = []
        if os.path.exists(conf_path):
            self._parse_config(conf_path)

    def _parse_config(self, filepath):
        with open(filepath, "r") as f:
            text = f.read()

        lines = text.split("\n")
        i = 0
        while i < len(lines):
            raw = lines[i]
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                i += 1
                continue

            if stripped.startswith("menuentry"):
                name = ""
                m = re.match(r'menuentry\s+"([^"]*)"\s*{', stripped)
                if m:
                    name = m.group(1)
                entry = {"name": name, "enabled": True, "settings": {}, "disabled": False}
                i += 1
                while i < len(lines):
                    inner = lines[i].strip()
                    if inner == "}":
                        break
                    if inner and not inner.startswith("#"):
                        if inner == "disabled":
                            entry["disabled"] = True
                        else:
                            parts = inner.split(None, 1)
                            key = parts[0]
                            val = parts[1].strip() if len(parts) > 1 else ""
                            entry["settings"][key] = val
                    i += 1
                self.menu_entries.append(entry)
            else:
                parts = stripped.split(None, 1)
                key = parts[0]
                val = parts[1].strip() if len(parts) > 1 else ""
                self.settings[key] = val
            i += 1

    def save(self):
        lines = ["# rEFInd Theme Configuration", f"# Generated by rEFInd Theme Editor", "#"]
        prefix = f"themes/{self.name}/"
        esp_prefix = f"/EFI/refind/themes/{self.name}/"
        file_keys = {opt["key"] for opt in ALL_OPTIONS if opt["type"] == "file"}

        def to_app_root(val):
            if val and not val.startswith("/") and not val.startswith("themes/"):
                return prefix + val
            return val

        def to_esp_root(val):
            if val:
                if val.startswith(esp_prefix):
                    return val
                if val.startswith(prefix):
                    return val.replace(prefix, esp_prefix, 1)
                if not val.startswith("/"):
                    return esp_prefix + val
            return val

        for section_name, options in get_sections():
            lines.append("")
            lines.append(f"# {section_name}")
            for opt in options:
                key = opt["key"]
                if key in self.settings:
                    val = self.settings[key]
                    if key in file_keys:
                        val = to_app_root(val)
                    lines.append(f"{key} {val}")
                else:
                    lines.append(f"#{key} {opt.get('default', '')}")
        lines.append("")
        lines.append("# Custom OS Entries")
        for entry in self.menu_entries:
            if entry["enabled"]:
                name = entry["name"]
                lines.append(f"")
                lines.append(f'menuentry "{name}" {{')
                for ek, ev in entry["settings"].items():
                    if ek == "icon":
                        ev = to_esp_root(ev)
                    lines.append(f"    {ek} {ev}")
                if entry["disabled"]:
                    lines.append(f"    disabled")
                lines.append("}")
        with open(os.path.join(self.path, "refind.conf"), "w") as f:
            f.write("\n".join(lines) + "\n")

    def get_resolved_path(self, setting_key, default=None):
        val = self.settings.get(setting_key)
        if not val:
            return default
        return self._resolve_path(val)

    def _resolve_path(self, val):
        if not val:
            return None
        app_root = os.path.dirname(os.path.dirname(self.path))
        if os.path.isabs(val):
            if val.startswith("/EFI/refind/"):
                local = os.path.join(app_root, val[len("/EFI/refind/"):])
                if os.path.exists(local):
                    return local
            return val
        p = os.path.join(app_root, val)
        if os.path.exists(p):
            return p
        p = os.path.join(self.path, val)
        if os.path.exists(p):
            return p
        return os.path.join(app_root, val)

    def get_background_path(self):
        return self.get_resolved_path("banner")

    def get_selection_big_path(self):
        return self.get_resolved_path("selection_big")

    def get_selection_small_path(self):
        return self.get_resolved_path("selection_small")

    def get_icons(self):
        icons = []
        ipath = self.icons_path
        if os.path.isdir(ipath):
            for f in sorted(os.listdir(ipath)):
                if f.lower().endswith((".png", ".bmp", ".jpg", ".jpeg", ".icns")):
                    full = os.path.join(ipath, f)
                    name = os.path.splitext(f)[0]
                    icons.append({"path": full, "name": name, "filename": f})
        return icons

    def get_os_icons(self):
        """Get only OS-type icons (os_ prefix)"""
        return [ic for ic in self.get_icons() if ic["name"].startswith("os_")]

    def get_tool_icons(self):
        """Get only tool/function icons"""
        return [ic for ic in self.get_icons() if not ic["name"].startswith("os_")]


def scan_themes(themes_dir):
    themes = []
    if not os.path.isdir(themes_dir):
        return themes
    for entry in sorted(os.listdir(themes_dir)):
        entry_path = os.path.join(themes_dir, entry)
        if os.path.isdir(entry_path) and not entry.startswith("."):
            themes.append(Theme(entry_path))
    return themes


def create_theme(themes_dir, name):
    theme_path = os.path.join(themes_dir, name)
    if os.path.exists(theme_path):
        return None
    os.makedirs(os.path.join(theme_path, "icons"))
    os.makedirs(os.path.join(theme_path, "assets"))
    conf = Theme(theme_path)
    conf.save()
    return conf


def get_themes_dir():
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(script_dir, THEMES_DIR_NAME)
