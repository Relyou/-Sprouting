"""工作台页面 — 左侧自律事项 + 右侧亟待解决待办，支持专注计时"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date

from config import (
    FONT_TITLE, FONT_SANS, FONT_SANS_BOLD, FONT_CAPTION, FONT_MONO,
    PAD_X, PAD_Y, GAP,
)


class WorkbenchPage(ttk.Frame):
    def __init__(self, parent, theme: dict, db, thread_pool, app):
        super().__init__(parent, style="TFrame")
        self.theme = theme
        self.db = db
        self.thread_pool = thread_pool
        self.app = app

        self._schedule_bars: list[tk.Frame] = []
        self._todo_bars: list[tk.Frame] = []

        # 专注模式控件
        self._focus_frame: tk.Frame | None = None
        self._countdown_label: tk.Label | None = None
        self._timer_after_id = None

        self._build_ui()

    def _build_ui(self):
        # ── 正常模式容器 ──
        self._normal_frame = ttk.Frame(self, style="TFrame")

        # 工具栏
        toolbar = ttk.Frame(self._normal_frame, style="TFrame")
        toolbar.pack(fill=tk.X, padx=PAD_X, pady=(PAD_Y, 0))
        ttk.Label(toolbar, text="工作台", font=FONT_TITLE).pack(side=tk.LEFT)

        # 左右分栏
        content = tk.PanedWindow(self._normal_frame, orient=tk.HORIZONTAL,
                                 bg=self.theme["border"], sashwidth=1)
        content.pack(fill=tk.BOTH, expand=True, padx=PAD_X, pady=(PAD_Y, PAD_Y))

        # ── 左侧：自律事项 ──
        left_frame = ttk.Frame(content, style="TFrame")
        content.add(left_frame, width=500, minsize=320)

        left_header = ttk.Frame(left_frame, style="TFrame")
        left_header.pack(fill=tk.X, pady=(0, GAP))
        ttk.Label(left_header, text="自律事项", font=FONT_SANS_BOLD).pack(side=tk.LEFT)

        self._left_canvas = tk.Canvas(left_frame, bg=self.theme["bg"],
                                      highlightthickness=0)
        left_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL,
                                    command=self._left_canvas.yview)
        self._left_canvas.configure(yscrollcommand=left_scroll.set)
        left_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._left_inner = ttk.Frame(self._left_canvas, style="TFrame")
        self._left_canvas.create_window((0, 0), window=self._left_inner,
                                        anchor=tk.NW, tags="inner")
        self._left_inner.bind("<Configure>",
                              lambda e: self._left_canvas.configure(
                                  scrollregion=self._left_canvas.bbox("all")))
        self._left_canvas.bind("<Configure>", self._on_left_canvas_config)
        self._left_canvas.bind("<MouseWheel>", self._on_left_mousewheel)
        self._left_inner.bind("<MouseWheel>", self._on_left_mousewheel)

        # ── 右侧：亟待解决待办 ──
        right_frame = ttk.Frame(content, style="TFrame")
        content.add(right_frame)

        right_header = ttk.Frame(right_frame, style="TFrame")
        right_header.pack(fill=tk.X, pady=(0, GAP))
        ttk.Label(right_header, text="亟待解决", font=FONT_SANS_BOLD).pack(side=tk.LEFT)

        self._right_canvas = tk.Canvas(right_frame, bg=self.theme["bg"],
                                       highlightthickness=0)
        right_scroll = ttk.Scrollbar(right_frame, orient=tk.VERTICAL,
                                     command=self._right_canvas.yview)
        self._right_canvas.configure(yscrollcommand=right_scroll.set)
        right_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._right_inner = ttk.Frame(self._right_canvas, style="TFrame")
        self._right_canvas.create_window((0, 0), window=self._right_inner,
                                         anchor=tk.NW, tags="inner")
        self._right_inner.bind("<Configure>",
                               lambda e: self._right_canvas.configure(
                                   scrollregion=self._right_canvas.bbox("all")))
        self._right_canvas.bind("<Configure>", self._on_right_canvas_config)
        self._right_canvas.bind("<MouseWheel>", self._on_right_mousewheel)
        self._right_inner.bind("<MouseWheel>", self._on_right_mousewheel)

        self._normal_frame.pack(fill=tk.BOTH, expand=True)

    def _on_left_canvas_config(self, event):
        w = event.width
        if w > 0:
            self._left_canvas.itemconfig(
                self._left_canvas.find_withtag("inner")[0], width=w)

    def _on_right_canvas_config(self, event):
        w = event.width
        if w > 0:
            self._right_canvas.itemconfig(
                self._right_canvas.find_withtag("inner")[0], width=w)

    def _on_left_mousewheel(self, event):
        if self._left_canvas.bbox("all") and \
           self._left_canvas.bbox("all")[3] > self._left_canvas.winfo_height():
            self._left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_right_mousewheel(self, event):
        if self._right_canvas.bbox("all") and \
           self._right_canvas.bbox("all")[3] > self._right_canvas.winfo_height():
            self._right_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    @staticmethod
    def _bind_scroll_recursive(widget, callback):
        widget.bind("<MouseWheel>", callback)
        for child in widget.winfo_children():
            WorkbenchPage._bind_scroll_recursive(child, callback)

    # ── 数据加载 ──
    def refresh(self):
        """刷新两侧数据（从外部调用）"""
        self._load_schedule()
        self._load_todos()
        # 检查是否有活跃计时器
        if self.app.timer_active:
            self._show_focus_mode()

    def _load_schedule(self):
        for w in self._left_inner.winfo_children():
            w.destroy()
        self._schedule_bars.clear()

        items = self.db.fetch_all(
            """SELECT * FROM schedule_items
               WHERE is_archived = 0
               ORDER BY is_completed ASC, created_at ASC"""
        )
        # 加载标签颜色
        labels = self.db.fetch_all("SELECT * FROM schedule_labels")
        label_map = {lb["id"]: lb for lb in labels}

        if not items:
            tk.Label(self._left_inner, text="暂无自律事项",
                     font=FONT_CAPTION, fg=self.theme["text_secondary"],
                     bg=self.theme["bg"]).pack(pady=20)
            return

        for item in items:
            self._add_schedule_bar(item, label_map)

        self._bind_scroll_recursive(self._left_inner, self._on_left_mousewheel)

    def _add_schedule_bar(self, item: dict, label_map: dict):
        bg = self.theme["card_bg"]
        bar = tk.Frame(self._left_inner, bg=bg,
                       highlightbackground=self.theme["border"],
                       highlightthickness=1)
        bar.pack(fill=tk.X, padx=2, pady=3)

        # 标签色条
        lid = item.get("label_id")
        label_color = label_map[lid]["color"] if lid and lid in label_map else self.theme["text_secondary"]
        strip = tk.Frame(bar, bg=label_color, width=4)
        strip.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        strip.pack_propagate(False)
        strip.configure(height=40)

        # 中间信息区
        info = tk.Frame(bar, bg=bg)
        info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=6)

        is_done = item.get("is_completed", 0)
        name_font = FONT_SANS_BOLD
        name_fg = self.theme["text"]
        if is_done:
            name_font = FONT_SANS_BOLD
            name_fg = self.theme["text_secondary"]

        name_label = tk.Label(info, text=item["name"], font=name_font,
                              bg=bg, fg=name_fg, anchor=tk.W)
        name_label.pack(anchor=tk.W)

        # 右侧区域（先创建，描述折叠按钮可能需要引用它）
        right_area = tk.Frame(bar, bg=bg)
        right_area.pack(side=tk.RIGHT, padx=(8, 8), pady=6)

        desc = item.get("description", "")
        if desc:
            desc_row = tk.Frame(info, bg=bg)
            desc_row.pack(anchor=tk.W, pady=(2, 0), fill=tk.X)

            # 折叠三角（描述左上角，位置固定不变）
            toggle_btn = tk.Label(desc_row, text="▶", font=("Segoe UI", 10),
                                 bg=bg, fg=self.theme["text_secondary"],
                                 cursor="hand2", padx=0, pady=0)
            toggle_btn.pack(side=tk.LEFT, anchor=tk.NW)

            short_desc = self._shorten_desc(desc)
            desc_label = tk.Label(desc_row, text=short_desc, font=FONT_CAPTION,
                                 bg=bg, fg=self.theme["text_secondary"],
                                 anchor=tk.W, wraplength=300,
                                 justify=tk.LEFT)
            desc_label.pack(side=tk.LEFT, anchor=tk.NW, fill=tk.X, expand=True)
            desc_label._full_text = desc
            desc_label._collapsed = True

            toggle_btn.bind("<Button-1>",
                           lambda e, dl=desc_label, tb=toggle_btn: self._toggle_desc(dl, tb))

        # 进度
        current = item["current_count"]
        target = item["target_count"]
        tk.Label(right_area, text=f"{current}/{target}", font=FONT_MONO,
                 bg=bg, fg=self.theme["text"]).pack(side=tk.LEFT, padx=(0, 8))

        # 计时按钮
        timer_minutes = item.get("timer_minutes")
        if timer_minutes:
            start_btn = tk.Label(right_area, text="▶ 开始", font=FONT_CAPTION,
                                 bg=self.theme["primary"], fg="#FFFFFF",
                                 padx=12, pady=3, cursor="hand2")
            start_btn.pack(side=tk.LEFT, padx=(0, 8))
            start_btn.bind("<Button-1>",
                           lambda e, iid=item["id"], tm=timer_minutes:
                           self._start_timer(iid, tm))

        # + 按钮 / ✓ 标记
        if is_done:
            tk.Label(right_area, text="✓", font=("Segoe UI", 14, "bold"),
                     bg=bg, fg=self.theme["success"]).pack(side=tk.LEFT)
        else:
            plus_btn = tk.Label(right_area, text="＋", font=("Segoe UI", 14, "bold"),
                                bg=bg, fg=self.theme["primary"],
                                cursor="hand2", padx=4)
            plus_btn.pack(side=tk.LEFT)
            plus_btn.bind("<Button-1>", lambda e, iid=item["id"]: self._inc_schedule(iid))

        self._schedule_bars.append(bar)

    def _inc_schedule(self, item_id: int):
        """工作台中递增自律事项计数"""
        from datetime import date as dt_date
        item = self.db.fetch_one("SELECT * FROM schedule_items WHERE id = ?", (item_id,))
        if not item:
            return

        current = item["current_count"] + 1
        target = item["target_count"]
        is_done = 1 if current >= target else 0
        today_str = dt_date.today().isoformat()

        self.db.update(
            """UPDATE schedule_items
               SET current_count=?, is_completed=?,
                   updated_at=datetime('now','localtime')
               WHERE id=?""",
            (current, is_done, item_id),
        )
        if is_done:
            self.db.insert(
                "INSERT INTO schedule_logs (item_id, done_date) VALUES (?, ?)",
                (item_id, today_str),
            )
        self.refresh()

    def _load_todos(self):
        for w in self._right_inner.winfo_children():
            w.destroy()
        self._todo_bars.clear()

        items = self.db.fetch_all(
            """SELECT * FROM todo_items
               WHERE is_completed = 0
               ORDER BY urgency DESC, importance DESC
               LIMIT 20"""
        )

        if not items:
            tk.Label(self._right_inner, text="暂无亟待解决的事项",
                     font=FONT_CAPTION, fg=self.theme["text_secondary"],
                     bg=self.theme["bg"]).pack(pady=20)
            return

        for item in items:
            self._add_todo_bar(item)

        self._bind_scroll_recursive(self._right_inner, self._on_right_mousewheel)

    def _add_todo_bar(self, item: dict):
        bg = self.theme["card_bg"]
        bar = tk.Frame(self._right_inner, bg=bg,
                       highlightbackground=self.theme["border"],
                       highlightthickness=1)
        bar.pack(fill=tk.X, padx=2, pady=3)

        # 紧急度色条
        from app.pages.todo import X_AXIS_COLORS
        urg_color = X_AXIS_COLORS[min(item["urgency"] - 1, 4)]
        strip = tk.Frame(bar, bg=urg_color, width=4)
        strip.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        strip.pack_propagate(False)
        strip.configure(height=40)

        info = tk.Frame(bar, bg=bg)
        info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=6)

        tk.Label(info, text=item["title"], font=FONT_SANS_BOLD,
                 bg=bg, fg=self.theme["text"], anchor=tk.W).pack(anchor=tk.W)

        desc = item.get("description", "")
        if desc:
            tk.Label(info, text=desc, font=FONT_CAPTION,
                     bg=bg, fg=self.theme["text_secondary"],
                     anchor=tk.W, wraplength=280,
                     ).pack(anchor=tk.W, pady=(2, 0))

        # 右侧元信息
        right_area = tk.Frame(bar, bg=bg)
        right_area.pack(side=tk.RIGHT, padx=(8, 8), pady=6)

        due = item.get("due_date", "")
        if due:
            tk.Label(right_area, text=f"📅 {due}", font=FONT_CAPTION,
                     bg=bg, fg=self.theme["text_muted"]).pack(side=tk.LEFT, padx=(0, 8))

        stars = "★" * item["importance"] + "☆" * (5 - item["importance"])
        tk.Label(right_area, text=stars,
                 font=("Segoe UI", 8), bg=bg,
                 fg="#F59E0B").pack(side=tk.LEFT, padx=(0, 8))

        dots = "●" * item["urgency"] + "○" * (5 - item["urgency"])
        tk.Label(right_area, text=dots,
                 font=("Segoe UI", 8), bg=bg,
                 fg=urg_color).pack(side=tk.LEFT, padx=(0, 8))

        # 完成按钮
        done_btn = tk.Label(right_area, text="完成", font=FONT_CAPTION,
                            bg=self.theme["success"], fg="#FFFFFF",
                            padx=8, pady=2, cursor="hand2")
        done_btn.pack(side=tk.LEFT)
        done_btn.bind("<Button-1>", lambda e, iid=item["id"]: self._mark_todo_done(iid))

        self._todo_bars.append(bar)

    def _mark_todo_done(self, item_id: int):
        """标记待办完成（需二次确认）"""
        if not messagebox.askyesno("确认完成", "确定要将该待办事项标记为完成吗？", parent=self):
            return
        self.db.update(
            "UPDATE todo_items SET is_completed=1, updated_at=datetime('now','localtime') WHERE id=?",
            (item_id,),
        )
        self.refresh()

    # ── 计时器 ──
    def _start_timer(self, item_id: int, target_minutes: int):
        """开始专注计时"""
        item = self.db.fetch_one(
            "SELECT * FROM schedule_items WHERE id = ?", (item_id,))
        if not item:
            return

        self.app.timer_active = True
        self.app.timer_item_id = item_id
        self.app.timer_target_minutes = target_minutes
        self.app.timer_start_time = datetime.now()
        self.app.timer_notified = False
        self.app.timer_item_name = item["name"]
        self.app.timer_target_minutes = target_minutes

        # 导航到工作台
        self.app.sidebar.set_active_by_key("workbench")
        self.app.content.show_page("workbench")
        self._show_focus_mode()

    def _show_focus_mode(self):
        """切换到专注计时视图"""
        if self._focus_frame:
            self._focus_frame.destroy()

        self._normal_frame.pack_forget()

        bg = self.theme["bg"]
        self._focus_frame = tk.Frame(self, bg=bg)
        self._focus_frame.pack(fill=tk.BOTH, expand=True)

        # 中央内容
        center = tk.Frame(self._focus_frame, bg=bg)
        center.place(relx=0.5, rely=0.4, anchor=tk.CENTER)

        # 盆栽图标
        tk.Label(center, text="🪴", font=("Segoe UI Emoji", 72),
                 bg=bg).pack()

        # "努力生长中"
        tk.Label(center, text="努力生长中", font=FONT_TITLE,
                 bg=bg, fg=self.theme["text"]).pack(pady=(12, 0))

        # 事项名称
        tk.Label(center, text=self.app.timer_item_name or "",
                 font=FONT_CAPTION, bg=bg,
                 fg=self.theme["text_secondary"]).pack(pady=(4, 16))

        # 倒计时
        self._countdown_label = tk.Label(center, text="", font=("Cascadia Code", 28, "bold"),
                                         bg=bg, fg=self.theme["primary"])
        self._countdown_label.pack(pady=(0, 24))

        # 退出按钮
        exit_btn = tk.Label(center, text="退出计时", font=FONT_SANS,
                            bg=self.theme["danger"], fg="#FFFFFF",
                            padx=24, pady=8, cursor="hand2")
        exit_btn.pack()
        exit_btn.bind("<Button-1>", lambda e: self._exit_timer())

        self._update_countdown()

    def _update_countdown(self):
        """每秒更新倒计时"""
        if not self.app.timer_active or not self._countdown_label:
            return

        elapsed = (datetime.now() - self.app.timer_start_time).total_seconds()
        target_seconds = self.app.timer_target_minutes * 60
        remaining = max(0, target_seconds - int(elapsed))

        # 超过目标后显示正计时
        if elapsed >= target_seconds:
            over = int(elapsed - target_seconds)
            m, s = divmod(over, 60)
            self._countdown_label.configure(
                text=f"+{m:02d}:{s:02d}",
                fg=self.theme["success"],
            )
            if not self.app.timer_notified:
                self.app.timer_notified = True
                self._show_time_up_notification()
        else:
            m, s = divmod(remaining, 60)
            self._countdown_label.configure(text=f"{m:02d}:{s:02d}")

        self._timer_after_id = self.after(1000, self._update_countdown)

    def _show_time_up_notification(self):
        """计时到时的提醒弹窗"""
        self.after(100, lambda: messagebox.showinfo(
            "计时完成",
            f"「{self.app.timer_item_name}」的计时时间已到！\n你可以继续专注，或点击退出按钮结束。",
            parent=self,
        ))

    def _exit_timer(self):
        """退出计时"""
        elapsed = (datetime.now() - self.app.timer_start_time).total_seconds()
        target_seconds = self.app.timer_target_minutes * 60
        time_sufficient = elapsed >= target_seconds

        if time_sufficient:
            msg = "硕果累累，是否退出？"
        else:
            msg = "小草要枯萎了，你真的要退出吗？"

        if not messagebox.askyesno("退出计时", msg, parent=self):
            return

        if time_sufficient:
            self._complete_timed_item()
        self._stop_timer()

    def _complete_timed_item(self):
        """计时达标后自动标记事项完成"""
        item_id = self.app.timer_item_id
        if not item_id:
            return
        item = self.db.fetch_one("SELECT * FROM schedule_items WHERE id = ?", (item_id,))
        if not item or item.get("is_completed"):
            return
        from datetime import date as dt_date
        target = item["target_count"]
        self.db.update(
            """UPDATE schedule_items
               SET current_count=?, is_completed=1,
                   updated_at=datetime('now','localtime')
               WHERE id=?""",
            (target, item_id),
        )
        self.db.insert(
            "INSERT INTO schedule_logs (item_id, done_date) VALUES (?, ?)",
            (item_id, dt_date.today().isoformat()),
        )

    def _stop_timer(self):
        """停止计时器"""
        self.app.timer_active = False
        self.app.timer_item_id = None
        self.app.timer_start_time = None
        self.app.timer_notified = False

        if self._timer_after_id:
            self.after_cancel(self._timer_after_id)
            self._timer_after_id = None

        if self._focus_frame:
            self._focus_frame.destroy()
            self._focus_frame = None
        self._countdown_label = None

        self._normal_frame.pack(fill=tk.BOTH, expand=True)
        self.refresh()

    # ── 外部接口 ──
    def on_save(self):
        pass

    def on_new(self):
        pass

    @staticmethod
    def _shorten_desc(text: str, max_chars: int = 60) -> str:
        """截断描述文本到约两行"""
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."

    def _toggle_desc(self, desc_label: tk.Label, toggle_btn: tk.Label):
        """切换描述文本的折叠/展开"""
        if desc_label._collapsed:
            desc_label.configure(text=desc_label._full_text)
            toggle_btn.configure(text="▼")
            desc_label._collapsed = False
        else:
            short = self._shorten_desc(desc_label._full_text)
            desc_label.configure(text=short)
            toggle_btn.configure(text="▶")
            desc_label._collapsed = True

    def apply_theme(self, theme: dict):
        self.theme = theme
        self.configure(style="TFrame")
        if self._left_canvas.winfo_exists():
            self._left_canvas.configure(bg=theme["bg"])
        if self._right_canvas.winfo_exists():
            self._right_canvas.configure(bg=theme["bg"])
        if self._focus_frame and self._focus_frame.winfo_exists():
            self._focus_frame.configure(bg=theme["bg"])
