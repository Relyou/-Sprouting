"""全局常量定义"""

import os
import sys
import platform

APP_NAME = "抽芽"
APP_VERSION = "1.0"
APP_DATA_DIR = os.path.join(os.path.expanduser("~"), f".{APP_NAME}")

# ── 窗口 ──
WINDOW_MIN_WIDTH = 920
WINDOW_MIN_HEIGHT = 640
WINDOW_DEFAULT_WIDTH = 1200
WINDOW_DEFAULT_HEIGHT = 900
WINDOW_ASPECT_RATIO = (4, 3)  # 宽:高

# ── 侧边栏 ──
SIDEBAR_DEFAULT_WIDTH = 260
SIDEBAR_MIN_WIDTH = 180

# ── 字体 ──
_SYSTEM = platform.system()
if _SYSTEM == "Windows":
    # 用 Segoe UI Variable（Win11）或 Segoe UI（Win10）渲染西文更清晰
    # 中文字体仍用微软雅黑
    FONT_SANS = ("Microsoft YaHei", 12)
    FONT_SANS_BOLD = ("Microsoft YaHei", 12, "bold")
    FONT_TITLE = ("Microsoft YaHei", 15, "bold")
    FONT_CAPTION = ("Microsoft YaHei", 10)
    FONT_MONO = ("Cascadia Code", 10)
    FONT_EN = ("Segoe UI", 12)
else:
    FONT_SANS = ("PingFang SC", 12)
    FONT_SANS_BOLD = ("PingFang SC", 12, "bold")
    FONT_TITLE = ("PingFang SC", 15, "bold")
    FONT_CAPTION = ("PingFang SC", 10)
    FONT_MONO = ("JetBrains Mono", 10)
    FONT_EN = ("Inter", 12)

# ── 间距与圆角 ──
PAD_X = 18
PAD_Y = 12
GAP = 10
RADIUS_BUTTON = 6
RADIUS_CARD = 8

# ── 自动保存间隔 (ms) ──
AUTO_SAVE_INTERVAL = 30000

# ── 备份保留数 ──
MAX_BACKUPS = 5


def ensure_app_dirs():
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(APP_DATA_DIR, "backups"), exist_ok=True)
