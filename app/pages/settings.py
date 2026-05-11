"""设置页面"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import FONT_TITLE, FONT_SANS, PAD_X, PAD_Y, GAP


class SettingsPage(ttk.Frame):
    def __init__(self, parent, theme: dict):
        super().__init__(parent, style="TFrame")
        self.theme = theme
        self._on_theme_changed = None
        self._on_export = None
        self._on_import = None
        self._on_clear_data = None

        self._build_ui()

    def _build_ui(self):
        ttk.Label(self, text="设置", font=FONT_TITLE).pack(
            anchor=tk.W, padx=PAD_X, pady=(PAD_Y, PAD_Y))

        # ── 主题设置 ──
        theme_frame = ttk.LabelFrame(self, text="外观", padding=12)
        theme_frame.pack(fill=tk.X, padx=PAD_X, pady=(0, GAP))

        self._theme_var = tk.StringVar(value="light")
        ttk.Radiobutton(theme_frame, text="浅色模式", variable=self._theme_var,
                        value="light", command=self._on_theme_select).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(theme_frame, text="深色模式", variable=self._theme_var,
                        value="dark", command=self._on_theme_select).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(theme_frame, text="跟随系统", variable=self._theme_var,
                        value="system", command=self._on_theme_select).pack(anchor=tk.W, pady=2)

        # ── 数据管理 ──
        data_frame = ttk.LabelFrame(self, text="数据", padding=12)
        data_frame.pack(fill=tk.X, padx=PAD_X, pady=(0, GAP))

        ttk.Button(data_frame, text="导出数据",
                   command=self._trigger_export).pack(anchor=tk.W, pady=2)
        ttk.Button(data_frame, text="导入数据",
                   command=self._trigger_import).pack(anchor=tk.W, pady=2)
        ttk.Button(data_frame, text="清除所有数据",
                   command=self._trigger_clear_data).pack(anchor=tk.W, pady=2)

        # ── 关于 ──
        about_frame = ttk.LabelFrame(self, text="关于", padding=12)
        about_frame.pack(fill=tk.X, padx=PAD_X, pady=(0, GAP))

        ttk.Label(about_frame, text="抽芽 v1.0",
                  font=FONT_SANS).pack(anchor=tk.W)
        ttk.Label(about_frame, text="轻量化记事日程桌面工具",
                  style="Muted.TLabel").pack(anchor=tk.W)

    def _on_theme_select(self):
        theme = self._theme_var.get()
        if self._on_theme_changed:
            self._on_theme_changed(theme)

    def _trigger_export(self):
        if self._on_export:
            self._on_export()

    def _trigger_import(self):
        if self._on_import:
            self._on_import()

    def _trigger_clear_data(self):
        if self._on_clear_data:
            self._on_clear_data()

    def apply_theme(self, theme: dict):
        self.theme = theme
        self.configure(style="TFrame")
