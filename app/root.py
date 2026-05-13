"""主窗口与应用入口"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading

from config import (
    APP_NAME, WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT,
    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, WINDOW_ASPECT_RATIO,
    SIDEBAR_DEFAULT_WIDTH, SIDEBAR_MIN_WIDTH, AUTO_SAVE_INTERVAL,
)
from theme import LIGHT_THEME, DARK_THEME, apply_theme
from data.settings_manager import SettingsManager
from data.database import DatabaseManager
from utils.thread_pool import ThreadPool
from app.sidebar import Sidebar
from app.content import ContentArea
from app.statusbar import StatusBar


class App:
    def __init__(self):
        self.settings = SettingsManager()
        self.db = DatabaseManager()
        self.thread_pool = ThreadPool()

        # 计时器状态
        self.timer_active = False
        self.timer_item_id = None
        self.timer_item_name = ""
        self.timer_target_minutes = 0
        self.timer_start_time = None
        self.timer_notified = False

        # 托盘图标
        self._tray_icon = None
        self._quitting = False

        self.root = tk.Tk()
        self._aspect_after_id = None  # 防抖 ID
        self._in_aspect_enforce = False  # 防止递归
        self._setup_window()
        self._setup_menu()

        # 当前主题
        theme_name = self.settings.get("theme", "light")
        self._current_theme = LIGHT_THEME if theme_name == "light" else DARK_THEME
        self._style = apply_theme(self.root, self._current_theme)

        # 主布局：PanedWindow（侧边栏 | 内容区）
        self.main_pane = tk.PanedWindow(
            self.root,
            orient=tk.HORIZONTAL,
            bg=self._current_theme["border"],
            sashwidth=1,
            sashrelief=tk.FLAT,
        )
        self.main_pane.pack(fill=tk.BOTH, expand=True)

        # 侧边栏
        sidebar_w = self.settings.get("sidebar_width", SIDEBAR_DEFAULT_WIDTH)
        self.sidebar = Sidebar(self.main_pane, self._current_theme, on_nav=self._on_nav)
        self.main_pane.add(self.sidebar, width=sidebar_w, minsize=SIDEBAR_MIN_WIDTH)

        # 内容区
        self.content = ContentArea(self.main_pane, self._current_theme, self.db, self.thread_pool)
        self.content.set_app(self)
        self.main_pane.add(self.content)

        # 状态栏
        self.statusbar = StatusBar(self.root, self._current_theme)

        # 恢复窗口位置/大小
        self._restore_geometry()

        # 绑定事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close_window)
        self.root.bind("<Configure>", lambda e: self._on_configure(), add="+")
        self.main_pane.bind("<ButtonRelease-1>", lambda e: self._on_sash_release(), add="+")

        # 自动保存 & 线程轮询 & 提醒检查 & 午夜刷新
        self.root.after(AUTO_SAVE_INTERVAL, self._auto_save)
        self.root.after(100, self._poll_threads)
        self.root.after(5000, self._check_reminders)
        self._last_refresh_date = None
        self.root.after(30000, self._check_midnight_refresh)

        # 初始化数据库
        self.db.init_db()

    # ── 窗口设置 ──
    def _setup_window(self):
        self.root.title(APP_NAME)
        self.root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.root.geometry(f"{WINDOW_DEFAULT_WIDTH}x{WINDOW_DEFAULT_HEIGHT}")
        self.root.resizable(True, True)

        try:
            self.root.iconbitmap(default="assets/icon.ico")
        except Exception:
            pass

    def _restore_geometry(self):
        w = self.settings.get("window_width")
        h = self.settings.get("window_height")
        x = self.settings.get("window_x")
        y = self.settings.get("window_y")
        if w and h:
            geo = f"{w}x{h}"
            if x is not None and y is not None:
                geo += f"+{x}+{y}"
            self.root.geometry(geo)

    # ── 菜单栏 ──
    def _setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="新建事项", command=lambda: self.content.new_item())
        file_menu.add_separator()
        file_menu.add_command(label="导出数据", command=self._export_data)
        file_menu.add_command(label="导入数据", command=self._import_data)
        file_menu.add_separator()
        file_menu.add_command(label="最小化到托盘", command=self._minimize_to_tray)
        file_menu.add_command(label="退出", command=self._quit_app)
        menubar.add_cascade(label="文件", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="切换主题", command=self.toggle_theme)
        menubar.add_cascade(label="视图", menu=view_menu)

    # ── 导航回调 ──
    def _on_nav(self, page_name: str):
        # 计时期间锁定在工作台
        if self.timer_active and page_name != "workbench":
            return
        self.content.show_page(page_name)
        self.settings.set("last_page", page_name)

    # ── 主题切换 ──
    def toggle_theme(self):
        new_name = "dark" if self._current_theme == LIGHT_THEME else "light"
        self._current_theme = DARK_THEME if new_name == "dark" else LIGHT_THEME
        self._style = apply_theme(self.root, self._current_theme)
        self.sidebar.apply_theme(self._current_theme)
        self.content.apply_theme(self._current_theme)
        self.statusbar.apply_theme(self._current_theme)
        self.main_pane.configure(bg=self._current_theme["border"])
        self.settings.set("theme", new_name)

    def get_current_theme(self) -> dict:
        return self._current_theme

    # ── 自动保存 ──
    def _auto_save(self):
        self.content.save_current_page()
        self.root.after(AUTO_SAVE_INTERVAL, self._auto_save)

    # ── 线程轮询 ──
    def _poll_threads(self):
        self.thread_pool.poll()
        self.root.after(100, self._poll_threads)

    # ── 提醒检查 ──
    def _check_reminders(self):
        """每 30 秒检查一次待办提醒"""
        from datetime import datetime, date
        now = datetime.now()
        today_str = date.today().isoformat()
        current_time_str = now.strftime("%H:%M")

        items = self.db.fetch_all(
            """SELECT * FROM todo_items
               WHERE is_completed = 0
                 AND remind_time IS NOT NULL
                 AND due_date IS NOT NULL"""
        )

        for item in items:
            due = item.get("due_date", "")
            remind = item.get("remind_time", "")
            if not due or not remind:
                continue
            # 提醒时间：截止日期 + 提醒时刻
            try:
                remind_dt = datetime.strptime(f"{due} {remind}", "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            # 到了提醒时间
            if now >= remind_dt:
                self.root.after(0, lambda i=item: self._show_reminder(i))
                # 清除 remind_time 防止重复提醒
                self.db.update(
                    "UPDATE todo_items SET remind_time = NULL WHERE id = ?",
                    (item["id"],),
                )

        self.root.after(30000, self._check_reminders)

    def _check_midnight_refresh(self):
        """每 30 秒检查是否跨天，跨天则刷新所有页面数据"""
        from datetime import date
        today = date.today().isoformat()
        if self._last_refresh_date is None:
            self._last_refresh_date = today
        elif self._last_refresh_date != today:
            self._last_refresh_date = today
            for p in self.content._pages.values():
                if hasattr(p, "_load_data"):
                    p._load_data()
                if hasattr(p, "refresh"):
                    p.refresh()
        self.root.after(30000, self._check_midnight_refresh)

    def _show_reminder(self, item: dict):
        """弹出提醒通知"""
        due = item.get("due_date", "")
        title = item.get("title", "")
        desc = item.get("description", "")
        body = f"「{title}」\n截止日期：{due}"
        if desc:
            body += f"\n\n{desc}"
        messagebox.showinfo("⏰ 待办提醒", body, parent=self.root)

    # ── 数据导入导出 ──
    def _export_data(self):
        """导出所有数据为 JSON 文件"""
        import json
        from datetime import date as dt_date

        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="导出数据",
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json")],
            initialfile=f"抽芽备份_{dt_date.today().isoformat()}.json",
        )
        if not path:
            return

        data = {
            "schedule_labels": self.db.fetch_all("SELECT * FROM schedule_labels"),
            "schedule_items": self.db.fetch_all("SELECT * FROM schedule_items"),
            "schedule_logs": self.db.fetch_all("SELECT * FROM schedule_logs"),
            "todo_items": self.db.fetch_all("SELECT * FROM todo_items"),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("导出成功", f"数据已导出到:\n{path}", parent=self.root)

    def _import_data(self):
        """从 JSON 文件导入数据（合并模式）"""
        import json

        if not messagebox.askyesno(
            "确认导入", "导入将合并到现有数据中，不会覆盖已有记录。\n确定继续？", parent=self.root
        ):
            return

        path = filedialog.askopenfilename(
            parent=self.root,
            title="导入数据",
            filetypes=[("JSON 文件", "*.json")],
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("导入失败", f"无法读取文件:\n{e}", parent=self.root)
            return

        count = 0
        label_id_map = {}   # old_id → new_id
        item_id_map = {}    # old_id → new_id

        # 1) 标签：建 old_id → new_id 映射
        for row in data.get("schedule_labels", []):
            existing = self.db.fetch_one(
                "SELECT id FROM schedule_labels WHERE name=?", (row["name"],))
            if existing:
                label_id_map[row["id"]] = existing["id"]
            else:
                new_id = self.db.insert(
                    "INSERT INTO schedule_labels (name, color) VALUES (?, ?)",
                    (row["name"], row.get("color", "#3B82F6")),
                )
                label_id_map[row["id"]] = new_id
                count += 1

        # 2) 事项：重映射 label_id，建 old_id → new_id 映射
        for row in data.get("schedule_items", []):
            old_lid = row.get("label_id")
            new_lid = label_id_map.get(old_lid) if old_lid else None
            try:
                new_id = self.db.insert(
                    """INSERT INTO schedule_items
                       (name, description, refresh_type, refresh_interval, target_count,
                        current_count, mark_icon, mark_color, label_id, timer_minutes,
                        max_completions, is_archived, is_completed, reset_date)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (row.get("name", ""), row.get("description", ""),
                     row.get("refresh_type", "daily"), row.get("refresh_interval", 1),
                     row.get("target_count", 1), row.get("current_count", 0),
                     row.get("mark_icon", "★"), row.get("mark_color", "#3B82F6"),
                     new_lid, row.get("timer_minutes"),
                     row.get("max_completions"), row.get("is_archived", 0),
                     row.get("is_completed", 0), row.get("reset_date", "")),
                )
                item_id_map[row["id"]] = new_id
                count += 1
            except Exception:
                pass

        # 3) 日志：重映射 item_id
        for row in data.get("schedule_logs", []):
            old_iid = row.get("item_id")
            new_iid = item_id_map.get(old_iid)
            if new_iid:
                try:
                    self.db.insert(
                        "INSERT INTO schedule_logs (item_id, done_date) VALUES (?, ?)",
                        (new_iid, row.get("done_date", "")),
                    )
                except Exception:
                    pass

        # 4) 待办事项
        for row in data.get("todo_items", []):
            try:
                self.db.insert(
                    """INSERT INTO todo_items
                       (title, description, due_date, remind_time, importance, urgency, is_completed)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (row.get("title", ""), row.get("description", ""),
                     row.get("due_date"), row.get("remind_time"),
                     row.get("importance", 3), row.get("urgency", 3),
                     row.get("is_completed", 0)),
                )
                count += 1
            except Exception:
                pass

        messagebox.showinfo("导入完成", f"成功导入 {count} 条记录", parent=self.root)
        # 刷新所有页面
        for p in self.content._pages.values():
            if hasattr(p, "_load_data"):
                p._load_data()
            if hasattr(p, "refresh"):
                p.refresh()

    def _clear_all_data(self):
        """清除所有数据"""
        if not messagebox.askyesno(
            "确认清除", "此操作将删除所有数据（标签、自律事项、完成记录、待办），不可恢复！\n\n确定继续？",
            parent=self.root,
        ):
            return
        if not messagebox.askyesno(
            "再次确认", "数据一旦清除将无法找回。\n建议先导出备份。\n\n确定清除所有数据？",
            parent=self.root,
        ):
            return
        self.db.delete("DELETE FROM schedule_logs")
        self.db.delete("DELETE FROM schedule_items")
        self.db.delete("DELETE FROM schedule_labels")
        self.db.delete("DELETE FROM todo_items")
        messagebox.showinfo("已清除", "所有数据已清除", parent=self.root)
        # 刷新所有页面
        for p in self.content._pages.values():
            if hasattr(p, "_load_data"):
                p._load_data()
            if hasattr(p, "refresh"):
                p.refresh()

    # ── 窗口事件 ──
    def _on_configure(self):
        """窗口大小变化时延迟强制长宽比（防抖 60ms）"""
        if self._in_aspect_enforce:
            return
        if self._aspect_after_id:
            self.root.after_cancel(self._aspect_after_id)
        self._aspect_after_id = self.root.after(60, self._enforce_aspect)

    def _enforce_aspect(self):
        """强制窗口保持 WINDOW_ASPECT_RATIO（高度跟随宽度）"""
        self._aspect_after_id = None
        self._in_aspect_enforce = True
        try:
            w = self.root.winfo_width()
            rw, rh = WINDOW_ASPECT_RATIO
            target_h = int(w * rh / rw)
            current_h = self.root.winfo_height()
            if abs(current_h - target_h) > 4:
                self.root.geometry(f"{w}x{target_h}")
        finally:
            self._in_aspect_enforce = False

    def _on_sash_release(self):
        sash_coord = self.main_pane.sash_coord(0)
        if sash_coord:
            self.settings.set("sidebar_width", sash_coord[0])

    def _on_close_window(self):
        """关闭窗口 → 退出应用"""
        if self._tray_icon:
            self._tray_icon.stop()
            self._tray_icon = None
        self._quit_app()

    def _minimize_to_tray(self):
        """隐藏窗口，显示托盘图标"""
        if self._tray_icon:
            self.root.withdraw()
            return
        self._create_tray_icon()
        self.root.withdraw()

    def _create_tray_icon(self):
        """创建系统托盘图标"""
        import pystray
        from PIL import Image, ImageDraw

        # 生成 64x64 图标（绿色嫩芽）
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([18, 10, 46, 52], fill="#10B981")
        draw.ellipse([4, 28, 38, 54], fill="#10B981")
        draw.rectangle([29, 12, 35, 58], fill="#059669")

        menu = pystray.Menu(
            pystray.MenuItem("显示窗口", self._restore_from_tray, default=True),
            pystray.MenuItem("退出", self._quit_app),
        )
        self._tray_icon = pystray.Icon("chouya", img, "抽芽", menu)

        # 在后台线程运行托盘图标
        threading.Thread(target=self._tray_icon.run, daemon=True).start()

    def _restore_from_tray(self):
        """从托盘恢复窗口"""
        self.root.after(0, self._do_restore)

    def _do_restore(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _quit_app(self):
        """完全退出应用"""
        self._quitting = True
        if self._tray_icon:
            self._tray_icon.stop()
            self._tray_icon = None
        self.root.after(0, self._on_close)

    def _on_close(self):
        self.settings.set("window_width", self.root.winfo_width())
        self.settings.set("window_height", self.root.winfo_height())
        self.settings.set("window_x", self.root.winfo_x())
        self.settings.set("window_y", self.root.winfo_y())

        try:
            self.db.backup()
        except Exception:
            pass
        self.db.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
