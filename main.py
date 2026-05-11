"""抽芽 — 轻量化记事日程桌面工具"""

import sys
import traceback
import platform

from config import ensure_app_dirs
from app.root import App


def _init_dpi():
    """声明 DPI 感知，防止 Windows 对窗口做位图缩放导致文字模糊。"""
    if platform.system() != "Windows":
        return
    try:
        import ctypes
        # 优先使用 Windows 10 1703+ 的 PerMonitorV2 模式（最佳清晰度）
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def main():
    ensure_app_dirs()
    _init_dpi()

    try:
        app = App()
        app.run()
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
