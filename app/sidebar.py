"""侧边栏导航"""

import tkinter as tk
from tkinter import ttk
from config import FONT_SANS, FONT_CAPTION, FONT_TITLE, PAD_X, PAD_Y, GAP


class Sidebar(ttk.Frame):
    NAV_ITEMS = [
        ("schedule", "📅 自律日程"),
        ("todo", "📋 待办记事"),
        ("workbench", "🪴 工作台"),
        ("settings", "⚙ 设置"),
    ]

    def __init__(self, parent, theme: dict, on_nav=None):
        super().__init__(parent, style="Sidebar.TFrame")
        self.theme = theme
        self._on_nav = on_nav
        self._active_idx = 0
        self._buttons: list[tk.Frame] = []

        self._build_ui()

    def _build_ui(self):
        # Logo / 标题
        header = ttk.Frame(self, style="Sidebar.TFrame")
        header.pack(fill=tk.X, padx=PAD_X, pady=(PAD_Y + 4, PAD_Y))

        self._logo_label = ttk.Label(
            header, text="🌱 抽芽", font=FONT_TITLE,
            foreground=self.theme["primary"], background=self.theme["sidebar_bg"],
        )
        self._logo_label.pack(anchor=tk.W)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X)

        # 导航按钮
        nav_frame = ttk.Frame(self, style="Sidebar.TFrame")
        nav_frame.pack(fill=tk.X, padx=0, pady=(GAP, 0))

        for idx, (key, label) in enumerate(self.NAV_ITEMS):
            btn = self._make_nav_button(nav_frame, key, label, idx)
            btn.pack(fill=tk.X, padx=6, pady=1)
            self._buttons.append(btn)

        self._highlight_active()

        # 底部用户信息占位
        bottom = ttk.Frame(self, style="Sidebar.TFrame")
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=PAD_X, pady=PAD_Y)
        ttk.Label(
            bottom, text="v1.0", style="Muted.TLabel",
            font=FONT_CAPTION, background=self.theme["sidebar_bg"],
        ).pack(side=tk.LEFT)

    def _make_nav_button(self, parent, key: str, label: str, idx: int) -> tk.Frame:
        frame = tk.Frame(parent, bg=self.theme["sidebar_bg"], cursor="hand2")

        # 左侧高亮指示条
        indicator = tk.Frame(frame, width=4, bg=self.theme["sidebar_bg"])
        indicator.place(x=0, y=2, relheight=0.85)
        frame.indicator = indicator

        text = tk.Label(
            frame, text=label, font=FONT_SANS,
            bg=self.theme["sidebar_bg"], fg=self.theme["text"],
            anchor=tk.W, padx=12, pady=10,
        )
        text.pack(fill=tk.X)

        # 绑定事件
        for w in (frame, text):
            w.bind("<Button-1>", lambda e, k=key, i=idx: self._on_click(k, i))
            w.bind("<Enter>", lambda e, f=frame, t=text: self._on_hover(f, t, True))
            w.bind("<Leave>", lambda e, f=frame, t=text: self._on_hover(f, t, False))

        frame.text = text
        frame.key = key
        frame.idx = idx
        return frame

    def _on_hover(self, frame: tk.Frame, text: tk.Label, entering: bool):
        if frame.idx == self._active_idx:
            return
        if entering:
            frame.configure(bg=self.theme["sidebar_active"])
            text.configure(bg=self.theme["sidebar_active"])
        else:
            frame.configure(bg=self.theme["sidebar_bg"])
            text.configure(bg=self.theme["sidebar_bg"])

    def _on_click(self, key: str, idx: int):
        self._active_idx = idx
        self._highlight_active()
        if self._on_nav:
            self._on_nav(key)

    def _highlight_active(self):
        for i, btn in enumerate(self._buttons):
            is_active = (i == self._active_idx)
            btn.configure(bg=self.theme["sidebar_active"] if is_active else self.theme["sidebar_bg"])
            btn.text.configure(
                bg=self.theme["sidebar_active"] if is_active else self.theme["sidebar_bg"],
                fg=self.theme["primary"] if is_active else self.theme["text"],
            )
            btn.indicator.configure(
                bg=self.theme["sidebar_indicator"] if is_active else self.theme["sidebar_bg"],
            )

    def set_active_by_key(self, key: str):
        """程序化切换激活项"""
        for i, item in enumerate(self.NAV_ITEMS):
            if item[0] == key:
                self._active_idx = i
                self._highlight_active()
                return

    def apply_theme(self, theme: dict):
        self.theme = theme
        self.configure(style="Sidebar.TFrame")
        # Logo
        self._logo_label.configure(
            foreground=theme["primary"], background=theme["sidebar_bg"])
        for child in self.winfo_children():
            if isinstance(child, ttk.Frame):
                child.configure(style="Sidebar.TFrame")
        # 重建 custom widgets
        for btn in self._buttons:
            btn.configure(bg=self.theme["sidebar_bg"])
            btn.indicator.configure(bg=self.theme["sidebar_bg"])
            btn.text.configure(bg=self.theme["sidebar_bg"], fg=self.theme["text"])
        self._highlight_active()
