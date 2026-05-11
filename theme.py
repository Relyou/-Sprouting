"""主题定义与应用"""

import tkinter as tk
from tkinter import ttk

from config import FONT_TITLE, FONT_SANS

# ── 浅色主题 ──
LIGHT_THEME = {
    "bg": "#F8FAFC",
    "card_bg": "#FFFFFF",
    "primary": "#3B82F6",
    "primary_hover": "#2563EB",
    "success": "#10B981",
    "success_hover": "#059669",
    "danger": "#EF4444",
    "warning": "#F59E0B",
    "text": "#1E293B",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",
    "border": "#E2E8F0",
    "sidebar_bg": "#F1F5F9",
    "sidebar_active": "#E0E7FF",
    "sidebar_indicator": "#3B82F6",
    "statusbar_bg": "#F8FAFC",
    "statusbar_text": "#64748B",
    "input_bg": "#FFFFFF",
    "input_focus_border": "#3B82F6",
    "scrollbar_bg": "#E2E8F0",
    "scrollbar_thumb": "#94A3B8",
}

# ── 深色主题 ──
DARK_THEME = {
    "bg": "#0F172A",
    "card_bg": "#1E293B",
    "primary": "#3B82F6",
    "primary_hover": "#60A5FA",
    "success": "#10B981",
    "success_hover": "#34D399",
    "danger": "#EF4444",
    "warning": "#F59E0B",
    "text": "#F1F5F9",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",
    "border": "#334155",
    "sidebar_bg": "#1A2332",
    "sidebar_active": "#1E3A5F",
    "sidebar_indicator": "#3B82F6",
    "statusbar_bg": "#0F172A",
    "statusbar_text": "#94A3B8",
    "input_bg": "#1E293B",
    "input_focus_border": "#60A5FA",
    "scrollbar_bg": "#1E293B",
    "scrollbar_thumb": "#475569",
}


def _configure_ttk_styles(style: ttk.Style, theme: dict) -> None:
    """配置 ttk 全局样式"""
    style.theme_use("clam")

    style.configure(".", background=theme["bg"], foreground=theme["text"])

    style.configure("TFrame", background=theme["bg"])
    style.configure("Card.TFrame", background=theme["card_bg"], relief="solid")

    style.configure("TLabel", background=theme["bg"], foreground=theme["text"])
    style.configure("Card.TLabel", background=theme["card_bg"], foreground=theme["text"])
    style.configure("Secondary.TLabel", foreground=theme["text_secondary"])
    style.configure("Muted.TLabel", foreground=theme["text_muted"])
    style.configure("Title.TLabel", font=FONT_TITLE)

    style.configure("TButton",
                    background=theme["primary"],
                    foreground="#FFFFFF",
                    borderwidth=0,
                    padding=(18, 6),
                    font=FONT_SANS)
    style.map("TButton",
              background=[("active", theme["primary_hover"]),
                          ("disabled", theme["text_secondary"])])

    style.configure("Success.TButton",
                    background=theme["success"],
                    foreground="#FFFFFF")
    style.map("Success.TButton",
              background=[("active", theme["success_hover"])])

    style.configure("Outline.TButton",
                    background=theme["bg"],
                    foreground=theme["primary"],
                    borderwidth=1)
    style.map("Outline.TButton",
              background=[("active", theme["border"])])

    style.configure("TEntry",
                    fieldbackground=theme["input_bg"],
                    foreground=theme["text"],
                    borderwidth=1,
                    padding=6)
    style.configure("TNotebook", background=theme["bg"], borderwidth=0)
    style.configure("TNotebook.Tab",
                    background=theme["bg"],
                    foreground=theme["text"],
                    padding=(18, 8),
                    borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", theme["card_bg"])],
              foreground=[("selected", theme["primary"])])

    style.configure("Treeview",
                    background=theme["card_bg"],
                    foreground=theme["text"],
                    fieldbackground=theme["card_bg"],
                    borderwidth=0,
                    rowheight=36)
    style.map("Treeview",
              background=[("selected", theme["primary"])],
              foreground=[("selected", "#FFFFFF")])

    style.configure("TScrollbar",
                    background=theme["scrollbar_bg"],
                    troughcolor=theme["scrollbar_bg"],
                    arrowcolor=theme["text_secondary"])
    style.map("TScrollbar",
              background=[("active", theme["scrollbar_thumb"])])

    style.configure("TSeparator", background=theme["border"])

    style.configure("Statusbar.TFrame", background=theme["statusbar_bg"])
    style.configure("Sidebar.TFrame", background=theme["sidebar_bg"])


def apply_theme(root: tk.Tk, theme: dict) -> ttk.Style:
    """将主题应用到整个应用，返回配置后的 Style 对象"""
    root.configure(bg=theme["bg"])
    style = ttk.Style(root)
    _configure_ttk_styles(style, theme)

    # 配置 ttk.PanedWindow 的 sash
    style.configure("TPanedwindow", background=theme["border"])

    return style


def get_contrast_hex(hex_color: str) -> str:
    """根据背景色返回合适的文字颜色（黑或白）"""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#1E293B" if luminance > 0.6 else "#FFFFFF"
