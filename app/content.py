"""内容区域 — 页面容器"""

import tkinter as tk
from tkinter import ttk
from app.pages.schedule import SchedulePage
from app.pages.todo import TodoPage
from app.pages.workbench import WorkbenchPage
from app.pages.settings import SettingsPage


class ContentArea(ttk.Frame):
    def __init__(self, parent, theme: dict, db, thread_pool):
        super().__init__(parent, style="TFrame")
        self.theme = theme
        self.db = db
        self.thread_pool = thread_pool
        self._app = None  # 由 App 设置

        # 页面注册
        self._pages: dict[str, ttk.Frame] = {}
        self._current_page: str | None = None

        self._build_pages()

    def set_app(self, app):
        self._app = app
        # 重建 workbench 页面（需要 app 引用）
        if "workbench" in self._pages:
            self._pages["workbench"].destroy()
        self._pages["workbench"] = WorkbenchPage(
            self, self.theme, self.db, self.thread_pool, app)

    def _build_pages(self):
        self._pages["schedule"] = SchedulePage(self, self.theme, self.db, self.thread_pool)
        self._pages["todo"] = TodoPage(self, self.theme, self.db, self.thread_pool)
        self._pages["settings"] = SettingsPage(self, self.theme)
        self._pages["settings"]._on_export = self._on_export_data
        self._pages["settings"]._on_import = self._on_import_data
        self._pages["settings"]._on_clear_data = self._on_clear_data
        self._pages["settings"]._on_theme_changed = self._on_theme_change
        # workbench 在 set_app 中创建（需要 app 引用）

        # 默认显示日程页
        self.show_page("schedule")

    def show_page(self, name: str):
        page = self._pages.get(name)
        if page is None:
            return

        # 如果已在目标页且非计时状态，直接返回
        if name == self._current_page and not (self._app and self._app.timer_active):
            return

        if self._current_page and self._current_page != name:
            self._pages[self._current_page].pack_forget()

        if name != self._current_page:
            page.pack(fill=tk.BOTH, expand=True)
        self._current_page = name

        # 切换页面时自动刷新数据
        if name == "workbench" and hasattr(page, "refresh"):
            page.refresh()
        elif hasattr(page, "_load_data"):
            page._load_data()

    def save_current_page(self):
        page = self._pages.get(self._current_page)
        if page and hasattr(page, "on_save"):
            page.on_save()

    def new_item(self):
        page = self._pages.get(self._current_page)
        if page and hasattr(page, "on_new"):
            page.on_new()

    def _on_export_data(self):
        if self._app:
            self._app._export_data()

    def _on_import_data(self):
        if self._app:
            self._app._import_data()

    def _on_clear_data(self):
        if self._app:
            self._app._clear_all_data()

    def _on_theme_change(self, theme_name: str):
        if not self._app:
            return
        from theme import LIGHT_THEME
        if theme_name == "system":
            theme_name = "light"
        is_light = self._app._current_theme == LIGHT_THEME
        if (theme_name == "light" and not is_light) or (theme_name == "dark" and is_light):
            self._app.toggle_theme()

    def apply_theme(self, theme: dict):
        self.theme = theme
        self.configure(style="TFrame")
        for page in self._pages.values():
            if hasattr(page, "apply_theme"):
                page.apply_theme(theme)
