"""自律日程页面"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
import calendar

from config import FONT_TITLE, FONT_SANS, FONT_SANS_BOLD, FONT_CAPTION, FONT_MONO
from config import PAD_X, PAD_Y, GAP

# ── 标记图标选项 ──
MARK_ICONS = ["★", "✿", "♥", "◆", "●", "✓", "☀", "♫", "✈", "☁"]

# ── 标记颜色预设 ──
MARK_COLORS = [
    "#3B82F6",  # 蓝
    "#EF4444",  # 红
    "#F59E0B",  # 琥珀
    "#10B981",  # 绿
    "#8B5CF6",  # 紫
    "#EC4899",  # 粉
    "#06B6D4",  # 青
    "#F97316",  # 橙
]

# ── 标签颜色预设 ──
LABEL_COLORS = [
    "#6366F1",  # 靛蓝
    "#EC4899",  # 粉
    "#F59E0B",  # 琥珀
    "#10B981",  # 绿
    "#EF4444",  # 红
    "#8B5CF6",  # 紫
    "#06B6D4",  # 青
    "#F97316",  # 橙
    "#3B82F6",  # 蓝
    "#14B8A6",  # 茶绿
]

# ── 日历绿色深度 ──
GREEN_SCALE = [
    None,           # 0 完成
    "#ECFDF5",      # 1
    "#D1FAE5",      # 2
    "#A7F3D0",      # 3
    "#6EE7B7",      # 4+
]


# ═══════════════════════════════════════════
# 新建 / 编辑事项对话框
# ═══════════════════════════════════════════

class ScheduleDialog(tk.Toplevel):
    """新建或编辑自律事项"""

    def __init__(self, parent, theme: dict, edit_data: dict | None = None,
                 labels: list[dict] | None = None, parent_id: int | None = None,
                 is_subtask: bool = False, is_composite: bool = False):
        super().__init__(parent)
        self.theme = theme
        self.result: dict | None = None
        self._edit_data = edit_data
        self._labels = labels or []
        self._parent_id = parent_id
        self._is_subtask = is_subtask
        self._is_composite = is_composite

        if edit_data:
            self.title("编辑事项")
        elif is_subtask:
            self.title("新建子事项")
        else:
            self.title("新建事项")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.configure(bg=theme["card_bg"])
        self._build_form()
        self._center_on_parent(parent)

        self.wait_window()

    def _build_form(self):
        pad = {"padx": 16, "pady": 6}
        bg = self.theme["card_bg"]
        fg = self.theme["text"]

        # ── 名称 ──
        ttk.Label(self, text="事项名称", background=bg).pack(anchor=tk.W, **pad)
        self._name_var = tk.StringVar(value=self._edit_data.get("name", "") if self._edit_data else "")
        name_entry = ttk.Entry(self, textvariable=self._name_var, width=36)
        name_entry.pack(fill=tk.X, padx=16, pady=(0, 6))
        name_entry.focus_set()

        # ── 复合事项（仅新建顶层事项时显示） ──
        show_composite_cb = (not self._edit_data and not self._is_subtask and not self._is_composite)
        self._composite_var = tk.BooleanVar(value=self._is_composite)
        self._detail_frame = None  # 存放刷新/目标/计时/最大完成次数的容器

        if show_composite_cb:
            comp_row = tk.Frame(self, bg=bg)
            comp_row.pack(fill=tk.X, padx=16, pady=(0, 6))
            ttk.Checkbutton(comp_row, text="复合事项（包含子事项）",
                           variable=self._composite_var,
                           command=self._on_composite_toggle).pack(side=tk.LEFT)

        # ── 描述 ──
        ttk.Label(self, text="描述（可选）", background=bg).pack(anchor=tk.W, **pad)
        self._desc_text = tk.Text(self, height=2, width=36, font=FONT_SANS,
                                  bg=self.theme["input_bg"], fg=self.theme["text"],
                                  relief="solid", borderwidth=1, wrap=tk.WORD)
        self._desc_text.pack(fill=tk.X, padx=16, pady=(0, 6))
        if self._edit_data and self._edit_data.get("description"):
            self._desc_text.insert("1.0", self._edit_data["description"])

        # ── 详细设置容器（刷新/目标/计时/最大完成次数，复合事项时隐藏） ──
        self._detail_frame = tk.Frame(self, bg=bg)
        self._detail_frame.pack(fill=tk.X, padx=0, pady=(0, 0))

        df = self._detail_frame  # 简写

        # ── 刷新类型 + 间隔 ──
        row1 = tk.Frame(df, bg=bg)
        row1.pack(fill=tk.X, padx=16, pady=(0, 6))

        ttk.Label(row1, text="刷新", background=bg).pack(side=tk.LEFT)
        self._type_var = tk.StringVar(value="daily")
        if self._edit_data:
            self._type_var.set(self._edit_data.get("refresh_type", "daily"))
        type_cb = ttk.Combobox(row1, textvariable=self._type_var,
                               values=["daily", "weekly", "monthly"],
                               state="readonly", width=10)
        type_cb.pack(side=tk.LEFT, padx=GAP)

        ttk.Label(row1, text="间隔", background=bg).pack(side=tk.LEFT, padx=(12, 0))
        self._interval_var = tk.IntVar(value=1)
        if self._edit_data:
            self._interval_var.set(self._edit_data.get("refresh_interval", 1))
        self._interval_spin = ttk.Spinbox(row1, from_=1, to=30, textvariable=self._interval_var,
                                          width=5, state="readonly")
        self._interval_spin.pack(side=tk.LEFT, padx=4)
        self._unit_label = ttk.Label(row1, text="天", background=bg)
        self._unit_label.pack(side=tk.LEFT)

        type_cb.bind("<<ComboboxSelected>>", self._on_type_changed)

        # ── 目标计数 ──
        row2 = tk.Frame(df, bg=bg)
        row2.pack(fill=tk.X, padx=16, pady=(0, 6))

        ttk.Label(row2, text="目标次数", background=bg).pack(side=tk.LEFT)
        self._target_var = tk.IntVar(value=1)
        if self._edit_data:
            self._target_var.set(self._edit_data.get("target_count", 1))
        ttk.Spinbox(row2, from_=1, to=127, textvariable=self._target_var,
                    width=6, state="readonly").pack(side=tk.LEFT, padx=GAP)
        ttk.Label(row2, text="（1 ~ 127）", foreground=self.theme["text_secondary"],
                  background=bg, font=FONT_CAPTION).pack(side=tk.LEFT)

        # ── 计时 ──
        row_timer = tk.Frame(df, bg=bg)
        row_timer.pack(fill=tk.X, padx=16, pady=(0, 6))

        self._timer_var = tk.BooleanVar(value=False)
        if self._edit_data:
            self._timer_var.set(bool(self._edit_data.get("timer_minutes")))
        timer_cb = ttk.Checkbutton(row_timer, text="是否计时", variable=self._timer_var,
                                   command=self._on_timer_toggle)
        timer_cb.pack(side=tk.LEFT)

        ttk.Label(row_timer, text="时间（分钟）", background=bg).pack(side=tk.LEFT, padx=(12, 0))
        self._timer_minutes_var = tk.IntVar(value=25)
        if self._edit_data and self._edit_data.get("timer_minutes"):
            self._timer_minutes_var.set(self._edit_data["timer_minutes"])
        self._timer_spin = ttk.Spinbox(row_timer, from_=1, to=180,
                                       textvariable=self._timer_minutes_var,
                                       width=5, state="readonly")
        self._timer_spin.pack(side=tk.LEFT, padx=4)
        self._on_timer_toggle()  # 初始化状态

        # ── 最大完成次数 ──
        row_max = tk.Frame(df, bg=bg)
        row_max.pack(fill=tk.X, padx=16, pady=(0, 6))

        self._max_comp_var = tk.BooleanVar(value=False)
        if self._edit_data:
            self._max_comp_var.set(bool(self._edit_data.get("max_completions")))
        max_cb = ttk.Checkbutton(row_max, text="最大完成次数", variable=self._max_comp_var,
                                 command=self._on_max_comp_toggle)
        max_cb.pack(side=tk.LEFT)

        self._max_comp_spin_var = tk.IntVar(value=7)
        if self._edit_data and self._edit_data.get("max_completions"):
            self._max_comp_spin_var.set(self._edit_data["max_completions"])
        self._max_comp_spin = ttk.Spinbox(row_max, from_=1, to=365,
                                          textvariable=self._max_comp_spin_var,
                                          width=5, state="readonly")
        self._max_comp_spin.pack(side=tk.LEFT, padx=4)
        ttk.Label(row_max, text="次后永久完成", background=bg,
                  foreground=self.theme["text_secondary"],
                  font=FONT_CAPTION).pack(side=tk.LEFT)
        self._on_max_comp_toggle()

        # ── 标记图标（子事项不需要） ──
        if not self._is_subtask:
            ttk.Label(self, text="标记图标", background=bg).pack(anchor=tk.W, **pad)
            row3 = tk.Frame(self, bg=bg)
            row3.pack(fill=tk.X, padx=16, pady=(0, 6))

            default_icon = self._edit_data.get("mark_icon", "★") if self._edit_data else "★"
            self._icon_var = tk.StringVar(value=default_icon)
            self._icon_btns = []
            for icon in MARK_ICONS:
                is_selected = (icon == self._icon_var.get())
                btn = tk.Label(row3, text=icon, font=("Segoe UI", 14),
                               bg=self.theme["primary"] if is_selected else self.theme["card_bg"],
                               fg="#FFFFFF" if is_selected else self.theme["text"],
                               padx=4, pady=1, cursor="hand2",
                               relief="solid" if is_selected else "flat",
                               borderwidth=1)
                btn.pack(side=tk.LEFT, padx=1)
                btn.bind("<Button-1>", lambda e, i=icon: self._select_icon(i))
                self._icon_btns.append((btn, icon))

            # ── 标记颜色 ──
            ttk.Label(self, text="标记颜色", background=bg).pack(anchor=tk.W, **pad)
            row4 = tk.Frame(self, bg=bg)
            row4.pack(fill=tk.X, padx=16, pady=(0, 12))

            default_color = self._edit_data.get("mark_color", "#3B82F6") if self._edit_data else "#3B82F6"
            self._color_var = tk.StringVar(value=default_color)
            self._color_btns = []
            for color in MARK_COLORS:
                is_selected = (color == self._color_var.get())
                size = 26 if is_selected else 22
                btn = tk.Label(row4, text="", bg=color, width=3, height=1,
                               relief="solid" if is_selected else "flat",
                               borderwidth=2, cursor="hand2",
                               highlightbackground=color,
                               highlightthickness=2 if is_selected else 0)
                btn.pack(side=tk.LEFT, padx=3)
                btn.bind("<Button-1>", lambda e, c=color: self._select_color(c))
                # 保持 label 尺寸稳定
                btn.place_configure
                self._color_btns.append((btn, color))
        else:
            self._icon_var = tk.StringVar(value="★")
            self._color_var = tk.StringVar(value="#3B82F6")
            self._icon_btns = []
            self._color_btns = []

        # ── 标签分类 ──
        ttk.Label(self, text="标签分类", background=bg).pack(anchor=tk.W, **pad)
        row5 = tk.Frame(self, bg=bg)
        row5.pack(fill=tk.X, padx=16, pady=(0, 6))

        label_names = ["（无）"] + [l["name"] for l in self._labels]
        self._label_var = tk.StringVar(value="（无）")
        self._label_id_var = tk.IntVar(value=0)  # 0 = 无标签
        if self._edit_data:
            edit_label_id = self._edit_data.get("label_id") or 0
            self._label_id_var.set(edit_label_id)
            if edit_label_id:
                for lb in self._labels:
                    if lb["id"] == edit_label_id:
                        self._label_var.set(lb["name"])
                        break

        label_cb = ttk.Combobox(row5, textvariable=self._label_var,
                                values=label_names, state="readonly", width=28)
        label_cb.pack(side=tk.LEFT)
        label_cb.bind("<<ComboboxSelected>>", self._on_label_selected)

        # 初始状态：编辑复合事项时隐藏详细设置
        if self._is_composite:
            self._detail_frame.pack_forget()

        # ── 按钮 ──
        btn_row = tk.Frame(self, bg=bg)
        btn_row.pack(fill=tk.X, padx=16, pady=(0, 16))

        ttk.Button(btn_row, text="取消", command=self.destroy).pack(side=tk.RIGHT, padx=(GAP, 0))
        ttk.Button(btn_row, text="确定", command=self._on_confirm).pack(side=tk.RIGHT)

    def _on_composite_toggle(self):
        if self._composite_var.get():
            self._detail_frame.pack_forget()
        else:
            self._detail_frame.pack(fill=tk.X, padx=0, pady=(0, 0),
                                    after=self._desc_text)

    def _on_type_changed(self, event=None):
        t = self._type_var.get()
        limits = {"daily": (1, 30), "weekly": (1, 4), "monthly": (1, 12)}
        lo, hi = limits.get(t, (1, 30))
        self._interval_spin.configure(from_=lo, to=hi)
        if self._interval_var.get() > hi:
            self._interval_var.set(hi)
        unit = {"daily": "天", "weekly": "周", "monthly": "月"}[t]
        self._unit_label.configure(text=unit)

    def _select_icon(self, icon: str):
        self._icon_var.set(icon)
        for btn, ic in self._icon_btns:
            is_sel = (ic == icon)
            btn.configure(
                bg=self.theme["primary"] if is_sel else self.theme["card_bg"],
                fg="#FFFFFF" if is_sel else self.theme["text"],
                relief="solid" if is_sel else "flat",
            )

    def _select_color(self, color: str):
        self._color_var.set(color)
        for btn, cl in self._color_btns:
            is_sel = (cl == color)
            btn.configure(
                width=4 if is_sel else 3,
                height=2 if is_sel else 1,
                relief="solid" if is_sel else "flat",
                highlightthickness=2 if is_sel else 0,
            )

    def _on_timer_toggle(self):
        if self._timer_var.get():
            self._timer_spin.configure(state="readonly")
        else:
            self._timer_spin.configure(state="disabled")

    def _on_max_comp_toggle(self):
        if self._max_comp_var.get():
            self._max_comp_spin.configure(state="readonly")
        else:
            self._max_comp_spin.configure(state="disabled")

    def _on_label_selected(self, event=None):
        name = self._label_var.get()
        if name == "（无）":
            self._label_id_var.set(0)
        else:
            for lb in self._labels:
                if lb["name"] == name:
                    self._label_id_var.set(lb["id"])
                    break

    def _on_confirm(self):
        name = self._name_var.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入事项名称", parent=self)
            return

        label_id = self._label_id_var.get()
        is_composite = self._composite_var.get() if hasattr(self, '_composite_var') else False

        if is_composite:
            # 复合事项：只保存描述/图标/颜色/标签
            timer_minutes = None
            max_completions = None
            refresh_type = "daily"
            refresh_interval = 1
            target_count = 1
        else:
            timer_minutes = self._timer_minutes_var.get() if self._timer_var.get() else None
            max_completions = self._max_comp_spin_var.get() if self._max_comp_var.get() else None
            refresh_type = self._type_var.get()
            refresh_interval = self._interval_var.get()
            target_count = self._target_var.get()

        self.result = {
            "name": name,
            "description": self._desc_text.get("1.0", tk.END).strip(),
            "refresh_type": refresh_type,
            "refresh_interval": refresh_interval,
            "target_count": target_count,
            "mark_icon": self._icon_var.get(),
            "mark_color": self._color_var.get(),
            "label_id": label_id if label_id else None,
            "timer_minutes": timer_minutes,
            "max_completions": max_completions,
            "parent_id": self._parent_id,
            "is_composite": 1 if is_composite else 0,
        }
        self.destroy()

    def _center_on_parent(self, parent):
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        w, h = self.winfo_width(), self.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"+{x}+{y}")


# ═══════════════════════════════════════════
# 标签管理对话框
# ═══════════════════════════════════════════

class LabelManagerDialog(tk.Toplevel):
    """管理标签分类：新建、编辑、删除"""

    def __init__(self, parent, theme: dict, db):
        super().__init__(parent)
        self.theme = theme
        self.db = db

        self.title("标签分类管理")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=theme["card_bg"])

        self._build_ui()
        self._center_on_parent(parent)
        self.wait_window()

    def _build_ui(self):
        bg = self.theme["card_bg"]
        fg = self.theme["text"]

        # 标题行
        header = tk.Frame(self, bg=bg)
        header.pack(fill=tk.X, padx=16, pady=(12, 8))
        tk.Label(header, text="管理标签分类", font=FONT_SANS_BOLD,
                 bg=bg, fg=fg).pack(side=tk.LEFT)

        # 分隔线
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=16)

        # 标签列表区
        self._list_frame = tk.Frame(self, bg=bg)
        self._list_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(8, 4))

        self._label_rows: dict[int, dict] = {}  # label_id -> widget refs
        self._refresh_label_list()

        # 新建标签区
        add_frame = tk.Frame(self, bg=bg)
        add_frame.pack(fill=tk.X, padx=16, pady=(8, 12))

        ttk.Label(add_frame, text="名称", background=bg).pack(side=tk.LEFT)
        self._new_name_var = tk.StringVar()
        name_entry = ttk.Entry(add_frame, textvariable=self._new_name_var, width=14)
        name_entry.pack(side=tk.LEFT, padx=(4, 8))

        ttk.Label(add_frame, text="颜色", background=bg).pack(side=tk.LEFT)
        self._new_color_var = tk.StringVar(value=LABEL_COLORS[0])
        color_cb = ttk.Combobox(add_frame, textvariable=self._new_color_var,
                                values=LABEL_COLORS, state="readonly", width=10)
        color_cb.pack(side=tk.LEFT, padx=(4, 8))
        # 颜色预览块
        self._color_preview = tk.Label(add_frame, text="  ", bg=LABEL_COLORS[0],
                                       relief="solid", borderwidth=1, width=3)
        self._color_preview.pack(side=tk.LEFT, padx=(0, 8))
        self._new_color_var.trace_add("write", lambda *_: self._color_preview.configure(
            bg=self._new_color_var.get()))

        ttk.Button(add_frame, text="添加标签", command=self._add_label).pack(side=tk.LEFT)

        # 关闭按钮
        ttk.Button(self, text="关闭", command=self.destroy).pack(pady=(0, 12))

    def _refresh_label_list(self):
        """重新加载标签列表"""
        parent = self._list_frame
        for child in parent.winfo_children():
            child.destroy()
        self._label_rows.clear()

        labels = self.db.fetch_all(
            "SELECT * FROM schedule_labels ORDER BY created_at ASC"
        )

        if not labels:
            tk.Label(parent, text="暂无标签，请在下方创建",
                     font=FONT_CAPTION, bg=self.theme["card_bg"],
                     fg=self.theme["text_secondary"]).pack(pady=8)
            return

        for lb in labels:
            row = tk.Frame(parent, bg=self.theme["card_bg"])
            row.pack(fill=tk.X, pady=2)

            # 颜色块
            color_block = tk.Label(row, text="  ", bg=lb["color"],
                                   relief="solid", borderwidth=1, width=2)
            color_block.pack(side=tk.LEFT, padx=(0, 8))

            # 名称
            name_label = tk.Label(row, text=lb["name"], font=FONT_SANS,
                                  bg=self.theme["card_bg"], fg=self.theme["text"])
            name_label.pack(side=tk.LEFT)

            # 编辑按钮
            edit_btn = tk.Label(row, text="✎", font=("Segoe UI", 12),
                                bg=self.theme["card_bg"],
                                fg=self.theme["text_secondary"],
                                cursor="hand2")
            edit_btn.pack(side=tk.RIGHT, padx=(4, 0))
            edit_btn.bind("<Button-1>", lambda e, lid=lb["id"], nm=lb["name"],
                           cl=lb["color"]: self._edit_label(lid, nm, cl))

            # 删除按钮
            del_btn = tk.Label(row, text="✕", font=("Segoe UI", 10),
                               bg=self.theme["card_bg"],
                               fg=self.theme["text_secondary"],
                               cursor="hand2")
            del_btn.pack(side=tk.RIGHT, padx=(2, 0))
            del_btn.bind("<Button-1>", lambda e, lid=lb["id"]: self._delete_label(lid))
            del_btn.bind("<Enter>", lambda e, b=del_btn: b.configure(fg=self.theme["danger"]))
            del_btn.bind("<Leave>", lambda e, b=del_btn: b.configure(fg=self.theme["text_secondary"]))

            self._label_rows[lb["id"]] = {
                "frame": row, "name": name_label, "color": color_block
            }

    def _add_label(self):
        name = self._new_name_var.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入标签名称", parent=self)
            return

        color = self._new_color_var.get()
        try:
            self.db.insert(
                "INSERT INTO schedule_labels (name, color) VALUES (?, ?)",
                (name, color),
            )
            self._new_name_var.set("")
            self._refresh_label_list()
        except Exception as e:
            if "UNIQUE" in str(e):
                messagebox.showwarning("提示", f"标签「{name}」已存在", parent=self)
            else:
                messagebox.showerror("错误", str(e), parent=self)

    def _edit_label(self, label_id: int, old_name: str, old_color: str):
        """弹出小窗编辑标签"""
        dlg = tk.Toplevel(self)
        dlg.title("编辑标签")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()
        dlg.configure(bg=self.theme["card_bg"])

        bg = self.theme["card_bg"]

        ttk.Label(dlg, text="名称", background=bg).pack(anchor=tk.W, padx=16, pady=(12, 0))
        name_var = tk.StringVar(value=old_name)
        ttk.Entry(dlg, textvariable=name_var, width=24).pack(fill=tk.X, padx=16, pady=(2, 8))

        ttk.Label(dlg, text="颜色", background=bg).pack(anchor=tk.W, padx=16)
        color_var = tk.StringVar(value=old_color)
        color_cb = ttk.Combobox(dlg, textvariable=color_var,
                                values=LABEL_COLORS, state="readonly", width=20)
        color_cb.pack(fill=tk.X, padx=16, pady=(2, 8))

        btn_row = tk.Frame(dlg, bg=bg)
        btn_row.pack(fill=tk.X, padx=16, pady=(0, 12))
        ttk.Button(btn_row, text="取消", command=dlg.destroy).pack(side=tk.RIGHT, padx=(4, 0))
        ttk.Button(btn_row, text="确定", command=lambda: self._save_edit_label(
            dlg, label_id, name_var.get().strip(), color_var.get())).pack(side=tk.RIGHT)

        dlg.update_idletasks()
        self.update_idletasks()
        sx, sy = self.winfo_rootx(), self.winfo_rooty()
        sw, sh = self.winfo_width(), self.winfo_height()
        dw, dh = dlg.winfo_width(), dlg.winfo_height()
        dlg.geometry(f"+{sx + (sw - dw) // 2}+{sy + (sh - dh) // 2}")
        dlg.wait_window()

    def _save_edit_label(self, dlg: tk.Toplevel, label_id: int,
                         name: str, color: str):
        if not name:
            messagebox.showwarning("提示", "标签名称不能为空", parent=dlg)
            return
        try:
            self.db.update(
                "UPDATE schedule_labels SET name=?, color=? WHERE id=?",
                (name, color, label_id),
            )
            dlg.destroy()
            self._refresh_label_list()
        except Exception as e:
            if "UNIQUE" in str(e):
                messagebox.showwarning("提示", f"标签「{name}」已存在", parent=dlg)
            else:
                messagebox.showerror("错误", str(e), parent=dlg)

    def _delete_label(self, label_id: int):
        if not messagebox.askyesno("确认删除", "删除标签后，其下事项将变为未分类。\n确定删除？"):
            return
        self.db.update(
            "UPDATE schedule_items SET label_id = NULL WHERE label_id = ?",
            (label_id,),
        )
        self.db.delete("DELETE FROM schedule_labels WHERE id = ?", (label_id,))
        self._refresh_label_list()

    def _center_on_parent(self, parent):
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        w, h = self.winfo_width(), self.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"+{x}+{y}")


# ═══════════════════════════════════════════
# 事项横条组件
# ═══════════════════════════════════════════

class ScheduleItemBar(tk.Frame):
    """单条自律事项横条（普通 / 复合父事项 / 子事项）"""

    def __init__(self, parent, item: dict, theme: dict,
                 on_increment=None, on_edit=None, on_delete=None, on_reset=None,
                 on_start_timer=None, on_undo=None, on_archive=None,
                 on_add_subtask=None, is_child: bool = False,
                 children_count: int = 0, children_done: int = 0):
        indent = 20 if is_child else 8
        super().__init__(parent, bg=theme["card_bg"], cursor="hand2",
                         highlightthickness=0)
        self.theme = theme
        self.item = item
        self._on_increment = on_increment
        self._on_edit = on_edit
        self._on_delete = on_delete
        self._on_reset = on_reset
        self._on_start_timer = on_start_timer
        self._on_undo = on_undo
        self._on_archive = on_archive
        self._on_add_subtask = on_add_subtask
        self._is_child = is_child
        self._children_count = children_count
        self._children_done = children_done

        # 缩进
        self._indent = tk.Frame(self, bg=theme["card_bg"], width=indent)
        self._indent.pack(side=tk.LEFT, fill=tk.Y)
        self._indent.pack_propagate(False)
        self._indent.configure(height=28)

        self._build()
        self._bind_events()

    def _build(self):
        item = self.item
        is_done = item.get("is_completed", 0)
        mark_icon = item.get("mark_icon", "★")
        mark_color = item.get("mark_color", "#3B82F6")
        label_color = item.get("label_color", "")
        strip_color = label_color if label_color else self.theme["text_secondary"]
        is_composite = self._children_count > 0 or item.get("is_composite")

        # 左侧标签色条
        strip = tk.Frame(self, bg=strip_color, width=4)
        strip.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
        strip.pack_propagate(False)
        strip.configure(height=28)
        self._label_strip = strip

        # 左侧图标
        icon_label = tk.Label(self, text=mark_icon, font=("Segoe UI", 16),
                              bg=self.theme["card_bg"], fg=mark_color)
        icon_label.pack(side=tk.LEFT, padx=(0, 8))
        self.icon_label = icon_label

        # 事项名称
        name_font = FONT_SANS_BOLD if not is_done else FONT_SANS + ("overstrike",)
        name_fg = self.theme["text_secondary"] if is_done else self.theme["text"]
        name_label = tk.Label(self, text=item["name"], font=name_font,
                              bg=self.theme["card_bg"], fg=name_fg, anchor=tk.W, width=12)
        name_label.pack(side=tk.LEFT, padx=(0, 8))
        self.name_label = name_label

        # 进度条 / 计数
        progress_w = 140
        progress_h = 12
        progress_canvas = tk.Canvas(self, width=progress_w, height=progress_h,
                                    bg=self.theme["card_bg"],
                                    highlightthickness=0)
        progress_canvas.pack(side=tk.LEFT, padx=(0, 8))
        self.progress_canvas = progress_canvas
        self._progress_w = progress_w
        self._progress_h = progress_h

        if is_composite:
            self._draw_progress(self._children_done, self._children_count)
            count_text = f"{self._children_done}/{self._children_count}"
        else:
            target = item["target_count"]
            current = item["current_count"]
            self._draw_progress(current, target)
            count_text = f"{current}/{target}"

        count_label = tk.Label(self, text=count_text, font=FONT_MONO,
                               bg=self.theme["card_bg"], fg=self.theme["text"], width=6)
        count_label.pack(side=tk.LEFT, padx=(0, 8))
        self.count_label = count_label

        # 完成勾 / + 按钮 / ▶ 计时按钮 / 子事项按钮
        self._btn_frame = tk.Frame(self, bg=self.theme["card_bg"])
        self._btn_frame.pack(side=tk.RIGHT)

        self._timer_btn = None
        self._subtask_btn = None

        if is_composite:
            # 复合父事项：始终显示子事项添加按钮
            self.check_label = None
            self.plus_btn = None
            if is_done:
                check = tk.Label(self._btn_frame, text="✓", font=("Segoe UI", 14, "bold"),
                                 bg=self.theme["card_bg"], fg=self.theme["success"])
                check.pack(side=tk.RIGHT, padx=(2, 6))
                self.check_label = check
            subtask_btn = tk.Label(self._btn_frame, text="＋子事项", font=("Segoe UI", 11, "bold"),
                                   bg=self.theme["card_bg"], fg=self.theme["primary"],
                                   cursor="hand2", padx=4)
            subtask_btn.pack(side=tk.RIGHT)
            subtask_btn.bind("<Button-1>", lambda e: self._on_add_subtask_click())
            self._subtask_btn = subtask_btn
        elif is_done:
            check = tk.Label(self._btn_frame, text="✓", font=("Segoe UI", 14, "bold"),
                             bg=self.theme["card_bg"], fg=self.theme["success"])
            check.pack(side=tk.RIGHT, padx=(2, 6))
            self.check_label = check
            self.plus_btn = None
        elif item.get("timer_minutes"):
            # 计时事项不显示加号，只显示计时按钮
            self.check_label = None
            self.plus_btn = None
            timer_btn = tk.Label(self._btn_frame, text="▶", font=("Segoe UI", 12, "bold"),
                                 bg=self.theme["card_bg"], fg=self.theme["success"],
                                 cursor="hand2", padx=3)
            timer_btn.pack(side=tk.RIGHT, padx=(0, 4))
            timer_btn.bind("<Button-1>", lambda e: self._on_start_timer_click())
            self._timer_btn = timer_btn
        else:
            self.check_label = None
            plus_btn = tk.Label(self._btn_frame, text="＋", font=("Segoe UI", 14, "bold"),
                                bg=self.theme["card_bg"], fg=self.theme["primary"],
                                cursor="hand2", padx=4)
            plus_btn.pack(side=tk.RIGHT)
            plus_btn.bind("<Button-1>", lambda e: self._on_plus())
            self.plus_btn = plus_btn

    def _draw_progress(self, current: int, target: int):
        c = self.progress_canvas
        c.delete("all")
        w = self._progress_w
        h = self._progress_h
        r = 4  # 圆角半径

        # 底色轨道
        c.create_rectangle(0, 0, w, h, fill=self.theme["border"],
                           outline="", tags="track")

        # 填充
        if target > 0 and current > 0:
            ratio = min(current / target, 1.0)
            fill_w = int(w * ratio)
            fill_color = self.theme["success"] if current >= target else self.theme["primary"]
            c.create_rectangle(0, 0, fill_w, h, fill=fill_color,
                               outline="", tags="fill")

    def _on_start_timer_click(self):
        if self._on_start_timer:
            self._on_start_timer(self.item["id"], self.item.get("timer_minutes", 25))

    def _on_plus(self):
        if self._on_increment:
            self._on_increment(self.item["id"])

    def _on_add_subtask_click(self):
        if self._on_add_subtask:
            self._on_add_subtask(self.item["id"])

    def _bind_events(self):
        if self.plus_btn:
            self.plus_btn.bind("<Enter>",
                               lambda e: self.plus_btn.configure(fg=self.theme["primary_hover"]))
            self.plus_btn.bind("<Leave>",
                               lambda e: self.plus_btn.configure(fg=self.theme["primary"]))

        for w in (self, self.name_label, self.icon_label, self.count_label, self.progress_canvas):
            w.bind("<Button-3>", self._on_right_click)

    def _on_right_click(self, event):
        menu = tk.Menu(self, tearoff=0, bg=self.theme["card_bg"],
                       fg=self.theme["text"],
                       activebackground=self.theme["primary"],
                       activeforeground="#FFFFFF")
        menu.add_command(label="编辑", command=lambda: self._on_edit and self._on_edit(self.item["id"]))
        menu.add_command(label="重置计数", command=lambda: self._on_reset and self._on_reset(self.item["id"]))
        if self.item.get("is_composite") and not self.item.get("is_completed"):
            menu.add_command(label="添加子事项", command=lambda: self._on_add_subtask and self._on_add_subtask(self.item["id"]))
        if self.item.get("is_completed") and self._children_count == 0:
            menu.add_command(label="撤销完成", command=lambda: self._on_undo and self._on_undo(self.item["id"]))
            menu.add_command(label="永久完成", command=lambda: self._on_archive and self._on_archive(self.item["id"]))
        elif self.item.get("is_completed") and (self._children_count > 0 or self.item.get("is_composite")):
            menu.add_command(label="永久完成", command=lambda: self._on_archive and self._on_archive(self.item["id"]))
        menu.add_separator()
        menu.add_command(label="删除", command=lambda: self._on_delete and self._on_delete(self.item["id"]))
        menu.post(event.x_root, event.y_root)

    def _rebuild_action_button(self, is_done: bool):
        """根据完成状态重建右侧的 + 按钮或 ✓ 标记"""
        if self.plus_btn:
            self.plus_btn.destroy()
            self.plus_btn = None
        if hasattr(self, 'check_label') and self.check_label:
            self.check_label.destroy()
            self.check_label = None
        if self._timer_btn:
            self._timer_btn.destroy()
            self._timer_btn = None
        if self._subtask_btn:
            self._subtask_btn.destroy()
            self._subtask_btn = None

        frame = self._btn_frame
        for w in frame.winfo_children():
            w.destroy()

        is_composite = self._children_count > 0 or self.item.get("is_composite")

        if is_composite:
            if is_done:
                self.check_label = tk.Label(
                    frame, text="✓", font=("Segoe UI", 14, "bold"),
                    bg=self.theme["card_bg"], fg=self.theme["success"],
                )
                self.check_label.pack(side=tk.RIGHT, padx=(2, 6))
            self._subtask_btn = tk.Label(
                frame, text="＋子事项", font=("Segoe UI", 11, "bold"),
                bg=self.theme["card_bg"], fg=self.theme["primary"],
                cursor="hand2", padx=4,
            )
            self._subtask_btn.pack(side=tk.RIGHT)
            self._subtask_btn.bind("<Button-1>", lambda e: self._on_add_subtask_click())
        elif not is_done and self.item.get("timer_minutes"):
            self._timer_btn = tk.Label(
                frame, text="▶", font=("Segoe UI", 12, "bold"),
                bg=self.theme["card_bg"], fg=self.theme["success"],
                cursor="hand2", padx=3,
            )
            self._timer_btn.pack(side=tk.RIGHT, padx=(0, 4))
            self._timer_btn.bind("<Button-1>",
                                 lambda e: self._on_start_timer_click())
        elif is_done:
            self.check_label = tk.Label(
                frame, text="✓", font=("Segoe UI", 14, "bold"),
                bg=self.theme["card_bg"], fg=self.theme["success"],
            )
            self.check_label.pack(side=tk.RIGHT, padx=(2, 6))
        elif not self.item.get("timer_minutes") or self._is_child:
            self.plus_btn = tk.Label(
                frame, text="＋", font=("Segoe UI", 14, "bold"),
                bg=self.theme["card_bg"], fg=self.theme["primary"],
                cursor="hand2", padx=4,
            )
            self.plus_btn.pack(side=tk.RIGHT)
            self.plus_btn.bind("<Button-1>", lambda e: self._on_plus())
            self.plus_btn.bind("<Enter>",
                               lambda e: self.plus_btn.configure(fg=self.theme["primary_hover"]))
            self.plus_btn.bind("<Leave>",
                               lambda e: self.plus_btn.configure(fg=self.theme["primary"]))

    def update_item(self, item: dict, children_count: int = 0, children_done: int = 0):
        """从外部更新 item 数据并刷新显示（不重建 widget）"""
        self.item = item
        self._children_count = children_count
        self._children_done = children_done
        is_done = item.get("is_completed", 0)

        # 更新标签色条
        if hasattr(self, '_label_strip'):
            label_color = item.get("label_color", "")
            strip_color = label_color if label_color else self.theme["text_secondary"]
            self._label_strip.configure(bg=strip_color)

        self.name_label.configure(
            text=item["name"],
            font=FONT_SANS + ("overstrike",) if is_done else FONT_SANS_BOLD,
            fg=self.theme["text_secondary"] if is_done else self.theme["text"],
        )
        self.icon_label.configure(text=item.get("mark_icon", "★"),
                                  fg=item.get("mark_color", "#3B82F6"))

        if children_count > 0 or item.get("is_composite"):
            self.count_label.configure(text=f"{children_done}/{children_count}")
            self._draw_progress(children_done, children_count)
        else:
            self.count_label.configure(
                text=f"{item['current_count']}/{item['target_count']}")
            self._draw_progress(item["current_count"], item["target_count"])

        # 处理 + 按钮和 ✓ 的切换（重建右侧按钮区）
        self._rebuild_action_button(is_done)

    def apply_theme(self, theme: dict):
        self.theme = theme
        self.configure(bg=theme["card_bg"])
        self._indent.configure(bg=theme["card_bg"])
        item = self.item
        # 更新标签色条（无标签时用灰色跟随主题）
        if hasattr(self, '_label_strip'):
            label_color = item.get("label_color", "")
            self._label_strip.configure(
                bg=label_color if label_color else theme["text_secondary"]
            )
        self.icon_label.configure(bg=theme["card_bg"])
        is_done = item.get("is_completed", 0)
        self.name_label.configure(bg=theme["card_bg"],
                                  fg=theme["text_secondary"] if is_done else theme["text"])
        self.count_label.configure(bg=theme["card_bg"], fg=theme["text"])
        self.progress_canvas.configure(bg=theme["card_bg"])
        if self._children_count > 0 or self.item.get("is_composite"):
            self._draw_progress(self._children_done, self._children_count)
        else:
            self._draw_progress(item["current_count"], item["target_count"])
        if self.plus_btn:
            self.plus_btn.configure(bg=theme["card_bg"], fg=theme["primary"])
        if self.check_label:
            self.check_label.configure(bg=theme["card_bg"], fg=theme["success"])
        if self._timer_btn:
            self._timer_btn.configure(bg=theme["card_bg"], fg=theme["success"])
        if hasattr(self, '_subtask_btn') and self._subtask_btn:
            self._subtask_btn.configure(bg=theme["card_bg"], fg=theme["primary"])


# ═══════════════════════════════════════════
# 标签分组标题栏
# ═══════════════════════════════════════════

class LabelHeaderBar(tk.Frame):
    """标签分组标题栏，左侧色条 + 标签名称"""

    def __init__(self, parent, label: dict, theme: dict):
        super().__init__(parent, bg=theme["card_bg"], cursor="hand2",
                         highlightthickness=0)
        self.theme = theme
        self.label = label

        # 左侧彩色指示条
        strip = tk.Frame(self, bg=label["color"], width=4)
        strip.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        # 防止被 pack 压缩
        strip.pack_propagate(False)
        strip.configure(height=22)

        # 标签名称
        name_lbl = tk.Label(self, text=label["name"], font=FONT_SANS_BOLD,
                            bg=theme["card_bg"], fg=label["color"])
        name_lbl.pack(side=tk.LEFT)

    def apply_theme(self, theme: dict):
        self.theme = theme
        self.configure(bg=theme["card_bg"])
        for child in self.winfo_children():
            if isinstance(child, tk.Label):
                child.configure(bg=theme["card_bg"])


# ═══════════════════════════════════════════
# Canvas 月历组件
# ═══════════════════════════════════════════

class MonthCalendar(tk.Canvas):
    """可交互的月历：导航、标记图标、绿色深度"""

    # 布局常量（比例）
    HEADER_H = 32
    DAYNAME_H = 22

    DAY_NAMES = ["一", "二", "三", "四", "五", "六", "日"]

    def __init__(self, parent, theme: dict, db, on_day_click=None):
        super().__init__(parent, bg=theme["card_bg"], highlightthickness=0)
        self.theme = theme
        self.db = db
        self._on_day_click = on_day_click

        self._year = date.today().year
        self._month = date.today().month
        self._today = date.today()

        # 缓存日志数据
        self._log_cache: dict[str, list[dict]] = {}
        self._todo_due_cache: dict[str, int] = {}  # date_str → count

        self.bind("<Configure>", self._on_resize)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Motion>", self._on_motion)

        self._hovered_day: tuple[int, int] | None = None  # (row, col)
        self._resize_after_id = None  # 防抖 ID

    def set_month(self, year: int, month: int):
        self._year = year
        self._month = month
        self._load_logs()
        self._draw()

    def refresh(self):
        self._load_logs()
        self._draw()

    def _load_logs(self):
        """加载当前月份所有 schedule_logs"""
        self._log_cache.clear()
        year, month = self._year, self._month

        # 确定查询范围（包含上月/下月填充日）
        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(year, month + 1, 1) - timedelta(days=1)

        # 扩展范围到完整周
        start_weekday = start.weekday()  # 0=Mon
        start_date = start - timedelta(days=start_weekday)
        end_weekday = end.weekday()
        end_date = end + timedelta(days=6 - end_weekday)

        logs = self.db.fetch_all(
            """SELECT sl.done_date, sl.item_id, si.mark_icon, si.mark_color, si.name
               FROM schedule_logs sl
               JOIN schedule_items si ON sl.item_id = si.id
               WHERE sl.done_date BETWEEN ? AND ?
               ORDER BY sl.done_date, sl.created_at""",
            (start_date.isoformat(), end_date.isoformat()),
        )

        for log in logs:
            d = log["done_date"]
            if d not in self._log_cache:
                self._log_cache[d] = []
            self._log_cache[d].append(log)

        # 同时加载待办截止日期
        self._todo_due_cache.clear()
        todos = self.db.fetch_all(
            """SELECT due_date, COUNT(*) as cnt
               FROM todo_items
               WHERE is_completed = 0
                 AND due_date BETWEEN ? AND ?
               GROUP BY due_date""",
            (start_date.isoformat(), end_date.isoformat()),
        )
        for t in todos:
            self._todo_due_cache[t["due_date"]] = t["cnt"]

    def _on_resize(self, event=None):
        """防抖重绘：窗口缩放停止 50ms 后才真正重绘"""
        if self._resize_after_id:
            self.after_cancel(self._resize_after_id)
        self._resize_after_id = self.after(50, self._do_resize_draw)

    def _do_resize_draw(self):
        self._resize_after_id = None
        self._draw()

    def _cell_rect(self, row: int, col: int):
        """返回格子 (x1, y1, x2, y2)"""
        w = self.winfo_width()
        h = self.winfo_height()

        cell_w = (w - 2) / 7
        header_total = self.HEADER_H + self.DAYNAME_H
        cell_h = max((h - header_total - 2) / 6, 20)

        x1 = 1 + col * cell_w
        y1 = header_total + 1 + row * cell_h
        x2 = x1 + cell_w - 1
        y2 = y1 + cell_h - 1
        return x1, y1, x2, y2

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        if w < 10:
            return

        h = self.winfo_height()
        cell_w = (w - 2) / 7
        header_total = self.HEADER_H + self.DAYNAME_H
        cell_h = max((h - header_total - 2) / 6, 20)

        # ── 标题行 ──
        title_text = f"{self._year}年 {self._month}月"
        cx = w / 2
        cy = self.HEADER_H / 2

        # 左箭头
        self._draw_arrow(cx - 70, cy, -1)
        # 右箭头
        self._draw_arrow(cx + 70, cy, 1)

        self.create_text(cx, cy, text=title_text,
                         font=FONT_SANS_BOLD, fill=self.theme["text"],
                         anchor=tk.CENTER, tags="title")

        # ── 分隔线 ──
        self.create_line(1, self.HEADER_H, w - 1, self.HEADER_H,
                         fill=self.theme["border"], tags="line")

        # ── 星期头 ──
        for i, dname in enumerate(self.DAY_NAMES):
            dx = 1 + i * cell_w + cell_w / 2
            dy = self.HEADER_H + self.DAYNAME_H / 2
            is_weekend = (i >= 5)
            fg = self.theme["text_secondary"] if is_weekend else self.theme["text"]
            self.create_text(dx, dy, text=dname,
                             font=FONT_CAPTION, fill=fg,
                             anchor=tk.CENTER, tags="dayname")

        self.create_line(1, self.HEADER_H + self.DAYNAME_H, w - 1,
                         self.HEADER_H + self.DAYNAME_H,
                         fill=self.theme["border"], tags="line")

        # ── 日期格子 ──
        cal = calendar.monthcalendar(self._year, self._month)

        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                x1, y1, x2, y2 = self._cell_rect(row_idx, col_idx)
                cx_cell = (x1 + x2) / 2
                cy_cell = (y1 + y2) / 2

                if day == 0:
                    continue

                is_current_month = self._is_current_month(row_idx, col_idx, cal)
                is_today = (self._year == self._today.year and
                            self._month == self._today.month and
                            day == self._today.day)

                date_str = date(self._year, self._month, day).isoformat()
                logs = self._log_cache.get(date_str, [])
                count = len(logs)

                # 背景色（绿色深度）
                bg_color = self._cell_bg(count)

                # 绘制格子背景
                if bg_color or is_today:
                    self.create_rectangle(x1 + 1, y1 + 1, x2 - 1, y2 - 1,
                                          fill=bg_color or "",
                                          outline="",
                                          tags=f"cell_{row_idx}_{col_idx}")

                # 今日高亮边框
                if is_today:
                    self.create_rectangle(x1 + 1, y1 + 1, x2 - 1, y2 - 1,
                                          fill="",
                                          outline=self.theme["primary"],
                                          width=2,
                                          tags=f"today_{row_idx}_{col_idx}")

                # 日期数字
                num_fg = self.theme["text_secondary"] if not is_current_month else (
                    self.theme["text"] if not is_today else self.theme["primary"]
                )
                num_font = FONT_SANS_BOLD if is_today else FONT_SANS
                self.create_text(cx_cell + cell_w * 0.32, cy_cell - cell_h * 0.28,
                                 text=str(day),
                                 font=num_font, fill=num_fg,
                                 anchor=tk.CENTER,
                                 tags=f"num_{row_idx}_{col_idx}")

                # 标记图标
                icon_size = max(min(int(cell_h * 0.38), 14), 9)
                icon_font = ("Segoe UI", icon_size)
                max_icons = min(count, 3)
                start_x = x1 + cell_w * 0.12
                icon_y = cy_cell + cell_h * 0.22

                for i in range(max_icons):
                    log = logs[i]
                    icon_color = log.get("mark_color", "#3B82F6")
                    ix = start_x + i * (icon_size + 2)
                    self.create_text(ix, icon_y,
                                     text=log["mark_icon"],
                                     font=icon_font, fill=icon_color,
                                     anchor=tk.W,
                                     tags=f"icon_{row_idx}_{col_idx}_{i}")

                if count > 3:
                    plus_x = start_x + 3 * (icon_size + 2)
                    self.create_text(plus_x, icon_y,
                                     text=f"+{count - 3}",
                                     font=FONT_CAPTION,
                                     fill=self.theme["text_secondary"],
                                     anchor=tk.W,
                                     tags=f"more_{row_idx}_{col_idx}")

                # 待办截止标记（右下角）
                todo_count = self._todo_due_cache.get(date_str, 0)
                if todo_count > 0:
                    todo_x = x2 - cell_w * 0.08
                    todo_y = y2 - cell_h * 0.12
                    self.create_text(todo_x, todo_y,
                                     text=f"📋{todo_count}",
                                     font=("Segoe UI", max(min(int(cell_h * 0.28), 10), 7)),
                                     fill="#F97316",
                                     anchor=tk.SE,
                                     tags=f"todo_{row_idx}_{col_idx}")

                # 悬停格子背景（hover 态另画）
                # 保存 cell 区域到 tag 以便点击检测

    def _draw_arrow(self, cx: float, cy: float, direction: int):
        """绘制 ◀ / ▶ 导航箭头"""
        arrow = "◀" if direction < 0 else "▶"
        tag = "prev_btn" if direction < 0 else "next_btn"
        self.create_text(cx, cy, text=arrow,
                         font=("Segoe UI", 14), fill=self.theme["text_secondary"],
                         anchor=tk.CENTER, tags=tag)

    @staticmethod
    def _cell_bg(count: int) -> str | None:
        if count <= 0:
            return None
        if count >= len(GREEN_SCALE):
            return GREEN_SCALE[-1]
        return GREEN_SCALE[count]

    def _is_current_month(self, row: int, col: int, cal: list[list[int]]) -> bool:
        day = cal[row][col]
        if day <= 0:
            return False
        # 第一周且日期 > 20 → 上月
        if row == 0 and day > 20:
            return False
        # 最后一周且日期 < 10 → 下月
        if row >= len(cal) - 1 and day < 10:
            return False
        return True

    def _on_click(self, event):
        x, y = event.x, event.y

        # 标题栏箭头点击
        if y < self.HEADER_H:
            w = self.winfo_width()
            cx = w / 2
            if x < cx - 40:
                self._navigate(-1)
                return
            elif x > cx + 40:
                self._navigate(1)
                return

        # 日期格子点击
        cell_w = (self.winfo_width() - 2) / 7
        header_total = self.HEADER_H + self.DAYNAME_H
        cell_h = max((self.winfo_height() - header_total - 2) / 6, 20)

        col = int((x - 1) // cell_w)
        row = int((y - header_total - 1) // cell_h)

        if col < 0 or col > 6 or row < 0 or row > 5:
            return

        cal = calendar.monthcalendar(self._year, self._month)
        if row >= len(cal):
            return

        day = cal[row][col]
        if day <= 0:
            # 点击了填充日（上月/下月），切换到对应月份
            if row == 0 and day > 20:
                self._navigate(-1)
            elif row >= len(cal) - 1 and day < 10:
                self._navigate(1)
            return

        if self._on_day_click:
            clicked_date = date(self._year, self._month, day)
            self._on_day_click(clicked_date)

    def _on_motion(self, event):
        """鼠标悬停高亮"""
        x, y = event.x, event.y
        cell_w = (self.winfo_width() - 2) / 7
        header_total = self.HEADER_H + self.DAYNAME_H
        cell_h = max((self.winfo_height() - header_total - 2) / 6, 20)

        col = int((x - 1) // cell_w)
        row = int((y - header_total - 1) // cell_h)

        new_hover = (row, col) if (0 <= col <= 6 and 0 <= row <= 5) else None

        if new_hover != self._hovered_day:
            # 移除旧高亮
            if self._hovered_day:
                self._remove_hover_highlight(*self._hovered_day)
            # 添加新高亮
            self._hovered_day = new_hover
            if self._hovered_day:
                self._add_hover_highlight(*self._hovered_day)

    def _add_hover_highlight(self, row: int, col: int):
        cal = calendar.monthcalendar(self._year, self._month)
        if row >= len(cal) or col >= 7:
            return
        day = cal[row][col]
        if day <= 0:
            return
        x1, y1, x2, y2 = self._cell_rect(row, col)
        self.create_rectangle(x1 + 1, y1 + 1, x2 - 1, y2 - 1,
                              fill="", outline=self.theme["primary"],
                              width=1, dash=(2, 2),
                              tags="hover_highlight")

    def _remove_hover_highlight(self, row: int, col: int):
        self.delete("hover_highlight")

    def _navigate(self, delta: int):
        new_month = self._month + delta
        new_year = self._year
        if new_month < 1:
            new_month = 12
            new_year -= 1
        elif new_month > 12:
            new_month = 1
            new_year += 1
        self.set_month(new_year, new_month)

    def apply_theme(self, theme: dict):
        self.theme = theme
        self.configure(bg=theme["card_bg"])
        self._draw()


# ═══════════════════════════════════════════
# 自律日程主页面
# ═══════════════════════════════════════════

class SchedulePage(ttk.Frame):
    def __init__(self, parent, theme: dict, db, thread_pool):
        super().__init__(parent, style="TFrame")
        self.theme = theme
        self.db = db
        self.thread_pool = thread_pool

        self._item_bars: dict[int, ScheduleItemBar] = {}
        self._label_headers: list[LabelHeaderBar] = []
        self._sections: dict[str, ttk.LabelFrame] = {}
        self._empty_labels: dict[str, ttk.Label] = {}

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # ── 顶部工具栏 ──
        toolbar = ttk.Frame(self, style="TFrame")
        toolbar.pack(fill=tk.X, padx=PAD_X, pady=(PAD_Y, 0))

        ttk.Label(toolbar, text="自律日程", font=FONT_TITLE).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="+ 新建事项", command=self.on_new).pack(side=tk.RIGHT)
        ttk.Button(toolbar, text="标签分类", command=self.on_manage_labels).pack(side=tk.RIGHT, padx=(0, GAP))
        ttk.Button(toolbar, text="查看全部", command=self._on_view_all).pack(side=tk.RIGHT, padx=(0, GAP))

        # ── 三个板块容器（Canvas + Scrollbar 实现滚动） ──
        scroll_wrapper = ttk.Frame(self, style="TFrame")
        scroll_wrapper.pack(fill=tk.BOTH, expand=True, padx=PAD_X, pady=(PAD_Y, 0))

        self._sections_canvas = tk.Canvas(scroll_wrapper, bg=self.theme["bg"],
                                          highlightthickness=0)
        self._sections_scrollbar = ttk.Scrollbar(scroll_wrapper, orient=tk.VERTICAL,
                                                 command=self._sections_canvas.yview)
        self._sections_canvas.configure(yscrollcommand=self._sections_scrollbar.set)

        self._sections_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._sections_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Canvas 内部的 Frame，真正容纳三个板块
        self._panes_inner = ttk.Frame(self._sections_canvas, style="TFrame")
        self._canvas_window_id = self._sections_canvas.create_window(
            (0, 0), window=self._panes_inner, anchor=tk.NW, tags="inner")

        # 绑定滚动和尺寸事件
        self._panes_inner.bind("<Configure>", self._on_inner_configure)
        self._sections_canvas.bind("<Configure>", self._on_canvas_configure)
        # 滚轮：绑定到 Canvas 并在 Enter 时捕获焦点
        self._sections_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._sections_canvas.bind("<Enter>",
                                   lambda e: self._sections_canvas.focus_set())

        section_names = [
            ("daily", "记日", "按天刷新"),
            ("weekly", "记周", "按周刷新"),
            ("monthly", "记月", "按月刷新"),
        ]

        for key, title, _desc in section_names:
            section = ttk.LabelFrame(self._panes_inner, text=title, padding=8)
            section.pack(fill=tk.X, pady=(0, GAP))

            inner = ttk.Frame(section, style="TFrame")
            inner.pack(fill=tk.X)

            empty_label = ttk.Label(
                inner, text=f"暂无{title}事项，点击上方按钮创建",
                style="Muted.TLabel", font=FONT_CAPTION,
                background=self.theme["bg"],
            )
            empty_label.pack(pady=8)

            self._sections[key] = section
            self._empty_labels[key] = empty_label

        # ── 月历 ──
        self._calendar = MonthCalendar(
            self, self.theme, self.db,
            on_day_click=self._on_day_click,
        )
        self._calendar.pack(fill=tk.X, expand=False, padx=PAD_X, pady=(GAP, PAD_Y))
        self.bind("<Configure>", self._on_page_configure, add="+")

    def _on_inner_configure(self, event=None):
        """内部 Frame 尺寸变化时更新 Canvas 滚动区域"""
        self._sections_canvas.configure(scrollregion=self._sections_canvas.bbox("all"))

    def _on_canvas_configure(self, event=None):
        """Canvas 宽度变化时同步内部 Frame 的宽度"""
        canvas_w = event.width if event else self._sections_canvas.winfo_width()
        if canvas_w > 0:
            self._sections_canvas.itemconfig(self._canvas_window_id, width=canvas_w)

    def _bind_scroll_recursive(self, widget):
        """递归绑定鼠标滚轮到所有子控件"""
        widget.bind("<MouseWheel>", self._on_mousewheel)
        for child in widget.winfo_children():
            self._bind_scroll_recursive(child)

    def _on_mousewheel(self, event):
        """鼠标滚轮事件 → 滚动 Canvas"""
        bbox = self._sections_canvas.bbox("all")
        if not bbox or bbox[3] <= self._sections_canvas.winfo_height():
            return  # 内容不足，无需滚动
        self._sections_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_page_configure(self, event=None):
        """页面大小变化时调整日历高度"""
        if event and event.widget != self:
            return
        w = self.winfo_width()
        if w < 10:
            return
        cal_w = w - PAD_X * 2
        cal_h = min(int(cal_w * 3 / 7), 380)
        self._calendar.configure(height=cal_h)

    # ── 数据加载 ──
    def _load_data(self):
        """从数据库加载所有事项，处理刷新逻辑，渲染 UI"""
        items = self.db.fetch_all(
            "SELECT * FROM schedule_items ORDER BY refresh_type, created_at ASC"
        )

        # 构建父子关系映射
        children_map: dict[int, list[dict]] = {}
        for item in items:
            pid = item.get("parent_id")
            if pid:
                children_map.setdefault(pid, []).append(item)

        # 处理刷新逻辑（跳过复合父事项，其状态由子事项衍生）
        today = date.today()
        for item in items:
            if item.get("parent_id"):
                # 子事项：正常刷新
                if self._needs_reset(item, today):
                    self._reset_item(item["id"], today)
            elif item["id"] not in children_map:
                # 普通事项：正常刷新
                if self._needs_reset(item, today):
                    self._reset_item(item["id"], today)
            # 复合父事项：不独立刷新，但子事项刷新后需要重新检查完成状态

        # 子事项刷新后，重新计算所有复合父事项的完成状态
        for item in items:
            if item.get("parent_id") is None and item["id"] in children_map:
                self._sync_parent_completion(item["id"])

        # 重新查询以获得更新后的数据（排除已归档）
        items = self.db.fetch_all(
            """SELECT * FROM schedule_items
               WHERE is_archived = 0
               ORDER BY refresh_type, created_at ASC"""
        )

        # 重建 children_map（刷新后数据可能变化）
        children_map.clear()
        for item in items:
            pid = item.get("parent_id")
            if pid:
                children_map.setdefault(pid, []).append(item)

        # 清除旧 UI
        self._clear_sections()
        self._item_bars.clear()

        # 分组渲染（只渲染顶层事项，子事项跟随父事项）
        grouped = {"daily": [], "weekly": [], "monthly": []}
        for item in items:
            if item.get("parent_id") is None:
                tp = item.get("refresh_type", "daily")
                if tp in grouped:
                    grouped[tp].append(item)

        for key in ("daily", "weekly", "monthly"):
            self._populate_section(key, grouped[key], children_map)

        # 递归绑定滚轮到所有板块控件
        self._bind_scroll_recursive(self._panes_inner)

        # 刷新日历
        self._calendar.refresh()

    def _needs_reset(self, item: dict, today: date) -> bool:
        refresh_type = item.get("refresh_type", "daily")
        interval = item.get("refresh_interval", 1)

        try:
            reset_date = datetime.fromisoformat(item.get("reset_date", "")).date()
        except (ValueError, TypeError):
            return True  # 无 reset_date，需要初始化

        if refresh_type == "daily":
            return today > reset_date + timedelta(days=interval)
        elif refresh_type == "weekly":
            # ISO 周比较
            reset_week = reset_date.isocalendar()[0:2]  # (year, week)
            today_week = today.isocalendar()[0:2]
            week_diff = (today_week[0] - reset_week[0]) * 52 + (today_week[1] - reset_week[1])
            return week_diff >= interval
        elif refresh_type == "monthly":
            month_diff = (today.year - reset_date.year) * 12 + (today.month - reset_date.month)
            return month_diff >= interval
        return False

    def _reset_item(self, item_id: int, today: date):
        self.db.update(
            """UPDATE schedule_items
               SET current_count = 0, is_completed = 0, reset_date = ?
               WHERE id = ?""",
            (today.isoformat(), item_id),
        )

    def _sync_parent_completion(self, parent_id: int):
        """同步复合父事项的完成状态（由子事项衍生）"""
        children = self.db.fetch_all(
            "SELECT * FROM schedule_items WHERE parent_id = ?", (parent_id,))
        if not children:
            self.db.update(
                "UPDATE schedule_items SET is_completed = 0 WHERE id = ?",
                (parent_id,))
            return

        all_done = all(c["is_completed"] for c in children)
        today_str = date.today().isoformat()

        if all_done:
            parent = self.db.fetch_one(
                "SELECT is_completed FROM schedule_items WHERE id = ?", (parent_id,))
            if parent and not parent["is_completed"]:
                self.db.update(
                    "UPDATE schedule_items SET is_completed = 1, updated_at = datetime('now','localtime') WHERE id = ?",
                    (parent_id,))
                self.db.insert(
                    "INSERT INTO schedule_logs (item_id, done_date) VALUES (?, ?)",
                    (parent_id, today_str))
        else:
            self.db.update(
                "UPDATE schedule_items SET is_completed = 0 WHERE id = ?",
                (parent_id,))

    def _clear_sections(self):
        for key, section in self._sections.items():
            # 删除内部的所有 item bar 和 label header（保留 empty label）
            for child in section.winfo_children():
                if isinstance(child, ttk.Frame):
                    for widget in child.winfo_children():
                        if isinstance(widget, (ScheduleItemBar, LabelHeaderBar)):
                            widget.destroy()
            self._empty_labels[key].pack_forget()
        self._label_headers.clear()

    def _populate_section(self, key: str, items: list[dict],
                          children_map: dict[int, list[dict]] | None = None):
        section = self._sections[key]
        inner = section.winfo_children()[0]  # 第一个 child 是 inner Frame

        if not items:
            self._empty_labels[key].pack(pady=8)
            return

        self._empty_labels[key].pack_forget()

        if children_map is None:
            children_map = {}

        # 加载所有标签
        all_labels = self.db.fetch_all("SELECT * FROM schedule_labels ORDER BY created_at ASC")
        label_map = {lb["id"]: lb for lb in all_labels}

        # 按标签分组（只对顶层事项分组）
        grouped: dict[int | None, list[dict]] = {}  # label_id -> items
        unlabeled: list[dict] = []
        for item in items:
            lid = item.get("label_id")
            if lid and lid in label_map:
                grouped.setdefault(lid, []).append(item)
            else:
                unlabeled.append(item)

        # 渲染单个事项（包括其子事项）
        def render_item(parent_item: dict, parent_inner, is_child: bool = False):
            item_id = parent_item["id"]
            kids = children_map.get(item_id, [])
            is_composite = len(kids) > 0 or parent_item.get("is_composite")
            kids_done = sum(1 for k in kids if k.get("is_completed"))

            bar = ScheduleItemBar(
                parent_inner, parent_item, self.theme,
                on_increment=self._on_increment,
                on_edit=self._on_edit_item,
                on_delete=self._on_delete_item,
                on_reset=self._on_reset_item,
                on_start_timer=self._on_start_timer,
                on_undo=self._on_undo_item,
                on_archive=self._on_archive_item,
                on_add_subtask=self._on_add_subtask,
                is_child=is_child,
                children_count=len(kids),
                children_done=kids_done,
            )
            bar.pack(fill=tk.X, pady=2)
            self._item_bars[item_id] = bar

            # 渲染子事项（缩进已在 ScheduleItemBar 内部处理）
            for kid in kids:
                kid["label_color"] = parent_item.get("label_color", "")
                render_item(kid, parent_inner, is_child=True)

        # 先渲染有标签的分组
        for lid, group_items in grouped.items():
            lb = label_map[lid]
            header = LabelHeaderBar(inner, lb, self.theme)
            header.pack(fill=tk.X, pady=(6, 1))
            self._label_headers.append(header)

            for item in group_items:
                item["label_color"] = lb["color"]
                render_item(item, inner)

        # 再渲染无标签的事项
        if unlabeled:
            if grouped:
                unlabeled_lb = {"name": "未分类", "color": self.theme["text_secondary"]}
                header = LabelHeaderBar(inner, unlabeled_lb, self.theme)
                header.pack(fill=tk.X, pady=(6, 1))
                self._label_headers.append(header)
            for item in unlabeled:
                item["label_color"] = ""
                render_item(item, inner)

    # ── 交互回调 ──
    def _on_increment(self, item_id: int):
        item = self.db.fetch_one("SELECT * FROM schedule_items WHERE id = ?", (item_id,))
        if not item:
            return

        parent_id = item.get("parent_id")
        is_child = parent_id is not None

        # 检查是否为复合父事项（不能直接递增）
        if item.get("is_composite"):
            return  # 复合父事项不能直接递增
        children = self.db.fetch_all(
            "SELECT COUNT(*) as cnt FROM schedule_items WHERE parent_id = ?", (item_id,))
        if children and children[0]["cnt"] > 0:
            return  # 有子事项的父事项也不能直接递增

        current = item["current_count"] + 1
        target = item["target_count"]
        is_done = 1 if current >= target else 0
        today_str = date.today().isoformat()

        self.db.update(
            "UPDATE schedule_items SET current_count = ?, is_completed = ?, updated_at = datetime('now','localtime') WHERE id = ?",
            (current, is_done, item_id),
        )

        if is_done:
            if is_child:
                # 子事项完成不记入日历，检查父事项
                self._sync_parent_completion(parent_id)
            else:
                # 普通事项完成记入日历
                self.db.insert(
                    "INSERT INTO schedule_logs (item_id, done_date) VALUES (?, ?)",
                    (item_id, today_str),
                )

        # 刷新 item bar 数据
        self._refresh_item_bar(item_id)
        if is_child:
            self._refresh_item_bar(parent_id)

        if not is_child:
            self._check_auto_archive(item_id)
        self._calendar.refresh()

    def _refresh_item_bar(self, item_id: int):
        """刷新单个 item bar 的显示"""
        if item_id not in self._item_bars:
            return
        updated_item = self.db.fetch_one("SELECT * FROM schedule_items WHERE id = ?", (item_id,))
        if not updated_item:
            return
        lid = updated_item.get("label_id")
        if lid:
            lb = self.db.fetch_one("SELECT color FROM schedule_labels WHERE id = ?", (lid,))
            updated_item["label_color"] = lb["color"] if lb else ""
        else:
            updated_item["label_color"] = ""

        # 获取子事项信息
        children = self.db.fetch_all(
            "SELECT * FROM schedule_items WHERE parent_id = ?", (item_id,))
        kids_done = sum(1 for k in children if k.get("is_completed"))
        self._item_bars[item_id].update_item(
            updated_item,
            children_count=len(children),
            children_done=kids_done,
        )

    def _on_edit_item(self, item_id: int):
        item = self.db.fetch_one("SELECT * FROM schedule_items WHERE id = ?", (item_id,))
        if not item:
            return

        # 判断是否为复合父事项
        children = self.db.fetch_all(
            "SELECT COUNT(*) as cnt FROM schedule_items WHERE parent_id = ?", (item_id,))
        is_composite = (children and children[0]["cnt"] > 0) or item.get("is_composite")
        is_child = item.get("parent_id") is not None

        labels = self.db.fetch_all("SELECT * FROM schedule_labels ORDER BY name ASC")
        dlg = ScheduleDialog(self.winfo_toplevel(), self.theme, edit_data=item,
                             labels=labels, is_subtask=is_child,
                             is_composite=is_composite)
        if dlg.result:
            data = dlg.result
            if is_composite:
                # 编辑复合父事项：仅更新名称/描述/图标/颜色/标签
                self.db.update(
                    """UPDATE schedule_items
                       SET name=?, description=?, mark_icon=?, mark_color=?,
                           label_id=?, updated_at=datetime('now','localtime')
                       WHERE id=?""",
                    (data["name"], data["description"],
                     data["mark_icon"], data["mark_color"],
                     data["label_id"], item_id),
                )
            else:
                self.db.update(
                    """UPDATE schedule_items
                       SET name=?, description=?, refresh_type=?, refresh_interval=?,
                           target_count=?, mark_icon=?, mark_color=?, label_id=?,
                           timer_minutes=?, max_completions=?,
                           updated_at=datetime('now','localtime')
                       WHERE id=?""",
                    (data["name"], data["description"], data["refresh_type"],
                     data["refresh_interval"], data["target_count"],
                     data["mark_icon"], data["mark_color"],
                     data["label_id"], data["timer_minutes"],
                     data["max_completions"], item_id),
                )
            self._load_data()

    def _on_delete_item(self, item_id: int):
        # 检查是否为复合父事项
        children = self.db.fetch_all(
            "SELECT id FROM schedule_items WHERE parent_id = ?", (item_id,))
        if children:
            msg = f"确定要删除这个复合事项及其 {len(children)} 个子事项吗？\n相关的完成记录也会被删除。"
        else:
            msg = "确定要删除这个事项吗？\n相关的完成记录也会被删除。"

        if not messagebox.askyesno("确认删除", msg):
            return

        if children:
            # 先删除子事项的 logs 和子事项本身
            for child in children:
                cid = child["id"]
                self.db.delete("DELETE FROM schedule_logs WHERE item_id = ?", (cid,))
                self.db.delete("DELETE FROM schedule_items WHERE id = ?", (cid,))
        self.db.delete("DELETE FROM schedule_logs WHERE item_id = ?", (item_id,))
        self.db.delete("DELETE FROM schedule_items WHERE id = ?", (item_id,))
        self._load_data()

    def _on_reset_item(self, item_id: int):
        today = date.today()
        item = self.db.fetch_one("SELECT * FROM schedule_items WHERE id = ?", (item_id,))
        if not item:
            return

        # 检查是否为复合父事项
        children = self.db.fetch_all(
            "SELECT id FROM schedule_items WHERE parent_id = ?", (item_id,))
        if children:
            # 重置所有子事项
            for child in children:
                self.db.update(
                    """UPDATE schedule_items
                       SET current_count = 0, is_completed = 0, reset_date = ?,
                           updated_at = datetime('now','localtime')
                       WHERE id = ?""",
                    (today.isoformat(), child["id"]),
                )
            # 父事项也重置完成状态
            self.db.update(
                """UPDATE schedule_items
                   SET is_completed = 0, updated_at = datetime('now','localtime')
                   WHERE id = ?""",
                (item_id,),
            )
        else:
            self.db.update(
                """UPDATE schedule_items
                   SET current_count = 0, is_completed = 0, reset_date = ?,
                       updated_at = datetime('now','localtime')
                   WHERE id = ?""",
                (today.isoformat(), item_id),
            )
            # 如果重置的是子事项，同步父事项状态
            parent_id = item.get("parent_id")
            if parent_id:
                self._sync_parent_completion(parent_id)

        self._load_data()

    def _on_undo_item(self, item_id: int):
        """撤销完成：回到未完成状态，移除今天的完成日志"""
        today_str = date.today().isoformat()
        item = self.db.fetch_one("SELECT * FROM schedule_items WHERE id = ?", (item_id,))

        self.db.update(
            """UPDATE schedule_items
               SET is_completed = 0, current_count = MAX(0, target_count - 1),
                   updated_at = datetime('now','localtime')
               WHERE id = ?""",
            (item_id,),
        )
        self.db.delete(
            "DELETE FROM schedule_logs WHERE item_id = ? AND done_date = ?",
            (item_id, today_str),
        )

        # 如果是子事项，同步父事项状态
        if item and item.get("parent_id"):
            self._sync_parent_completion(item["parent_id"])

        self._load_data()

    def _on_archive_item(self, item_id: int):
        """永久完成：归档事项"""
        children = self.db.fetch_all(
            "SELECT COUNT(*) as cnt FROM schedule_items WHERE parent_id = ?", (item_id,))
        has_children = children and children[0]["cnt"] > 0
        msg = "确定将该事项标记为永久完成？\n归档后可在「查看全部」中找到。"
        if has_children:
            msg = "确定将该复合事项及其所有子事项标记为永久完成？\n归档后可在「查看全部」中找到。"

        if not messagebox.askyesno("永久完成", msg, parent=self):
            return

        if has_children:
            self.db.update(
                "UPDATE schedule_items SET is_archived = 1, updated_at = datetime('now','localtime') WHERE parent_id = ?",
                (item_id,),
            )
        self.db.update(
            "UPDATE schedule_items SET is_archived = 1, updated_at = datetime('now','localtime') WHERE id = ?",
            (item_id,),
        )
        self._load_data()

    def _check_auto_archive(self, item_id: int):
        """检查是否达到最大完成次数，自动归档"""
        item = self.db.fetch_one(
            "SELECT max_completions, is_archived FROM schedule_items WHERE id = ?", (item_id,))
        if not item or item["is_archived"]:
            return
        max_c = item.get("max_completions")
        if not max_c:
            return
        count = self.db.fetch_one(
            "SELECT COUNT(*) as cnt FROM schedule_logs WHERE item_id = ?", (item_id,))
        if count and count["cnt"] >= max_c:
            self.db.update(
                "UPDATE schedule_items SET is_archived = 1 WHERE id = ?", (item_id,))

    def _on_day_click(self, clicked_date: date):
        """点击日历格子：弹出当日完成详情和待办"""
        date_str = clicked_date.isoformat()
        logs = self.db.fetch_all(
            """SELECT sl.id, sl.done_date, si.name, si.mark_icon, si.mark_color
               FROM schedule_logs sl
               JOIN schedule_items si ON sl.item_id = si.id
               WHERE sl.done_date = ?
               ORDER BY sl.created_at DESC""",
            (date_str,),
        )
        todos = self.db.fetch_all(
            """SELECT id, title, description, importance, urgency, is_completed
               FROM todo_items
               WHERE due_date = ?
               ORDER BY urgency DESC, importance DESC""",
            (date_str,),
        )

        DayDetailPopover(self.winfo_toplevel(), clicked_date, logs, todos,
                         self.theme, on_delete_log=self._on_delete_log)

    def _on_delete_log(self, log_id: int):
        """从日历详情中删除一条完成记录"""
        self.db.delete("DELETE FROM schedule_logs WHERE id = ?", (log_id,))
        self._calendar.refresh()
        self._load_data()

    # ── 外部接口 ──
    def on_save(self):
        pass

    def _on_add_subtask(self, parent_id: int):
        """为复合父事项添加子事项"""
        parent = self.db.fetch_one("SELECT * FROM schedule_items WHERE id = ?", (parent_id,))
        if not parent:
            return

        labels = self.db.fetch_all("SELECT * FROM schedule_labels ORDER BY name ASC")
        # 子事项默认继承父事项的标签和颜色
        default_data = {
            "label_id": parent.get("label_id"),
            "mark_color": parent.get("mark_color", "#3B82F6"),
        }
        dlg = ScheduleDialog(self.winfo_toplevel(), self.theme,
                             labels=labels, parent_id=parent_id,
                             is_subtask=True)
        if dlg.result:
            data = dlg.result
            self.db.insert(
                """INSERT INTO schedule_items
                   (name, description, refresh_type, refresh_interval, target_count,
                    mark_icon, mark_color, label_id, timer_minutes, max_completions,
                    parent_id, is_composite)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (data["name"], data["description"], data["refresh_type"],
                 data["refresh_interval"], data["target_count"],
                 data["mark_icon"], data["mark_color"],
                 data["label_id"], data["timer_minutes"],
                 data["max_completions"], parent_id,
                 data["is_composite"]),
            )
            # 确保父事项不处于完成状态
            self._sync_parent_completion(parent_id)
            self._load_data()

    def on_new(self):
        labels = self.db.fetch_all("SELECT * FROM schedule_labels ORDER BY name ASC")
        dlg = ScheduleDialog(self.winfo_toplevel(), self.theme, labels=labels)
        if dlg.result:
            data = dlg.result
            self.db.insert(
                """INSERT INTO schedule_items
                   (name, description, refresh_type, refresh_interval, target_count,
                    mark_icon, mark_color, label_id, timer_minutes, max_completions,
                    parent_id, is_composite)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (data["name"], data["description"], data["refresh_type"],
                 data["refresh_interval"], data["target_count"],
                 data["mark_icon"], data["mark_color"],
                 data["label_id"], data["timer_minutes"],
                 data["max_completions"], data["parent_id"],
                 data["is_composite"]),
            )
            self._load_data()

    def on_manage_labels(self):
        """打开标签管理对话框"""
        LabelManagerDialog(self.winfo_toplevel(), self.theme, self.db)
        self._load_data()

    def _on_view_all(self):
        """查看已归档（永久完成）的事项"""
        items = self.db.fetch_all(
            """SELECT si.*, sl.name as label_name, sl.color as label_color
               FROM schedule_items si
               LEFT JOIN schedule_labels sl ON si.label_id = sl.id
               WHERE si.is_archived = 1
               ORDER BY sl.name IS NULL, sl.name ASC, si.name ASC"""
        )

        dlg = tk.Toplevel(self.winfo_toplevel())
        dlg.title("已归档事项")
        dlg.transient(self.winfo_toplevel())
        dlg.configure(bg=self.theme["bg"])
        dlg.geometry("520x420")

        header = tk.Frame(dlg, bg=self.theme["bg"])
        header.pack(fill=tk.X, padx=12, pady=(10, 4))
        tk.Label(header, text=f"已归档事项（{len(items)}）", font=FONT_TITLE,
                 bg=self.theme["bg"], fg=self.theme["text"],
                 ).pack(side=tk.LEFT)

        canvas = tk.Canvas(dlg, bg=self.theme["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(dlg, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0), pady=(0, 12))

        inner = ttk.Frame(canvas, style="TFrame")
        canvas.create_window((0, 0), window=inner, anchor=tk.NW, tags="inner")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(
            canvas.find_withtag("inner")[0], width=e.width) if canvas.find_withtag("inner") else None)
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        if not items:
            ttk.Label(inner, text="暂无已归档事项", style="Muted.TLabel",
                      font=FONT_CAPTION).pack(pady=32)
        else:
            # 按标签分组
            last_label_id = None
            for item in items:
                lid = item.get("label_id")
                if lid != last_label_id:
                    last_label_id = lid
                    lb_name = item.get("label_name") or "未分类"
                    lb_color = item.get("label_color") or self.theme["text_secondary"]
                    header = LabelHeaderBar(inner, {"name": lb_name, "color": lb_color}, self.theme)
                    header.pack(fill=tk.X, pady=(8, 1))

                card = tk.Frame(inner, bg=self.theme["card_bg"],
                                highlightbackground=self.theme["border"],
                                highlightthickness=1)
                card.pack(fill=tk.X, padx=2, pady=3)

                # 标签色条
                lc = item.get("label_color", self.theme["text_secondary"])
                strip = tk.Frame(card, bg=lc, width=4)
                strip.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
                strip.pack_propagate(False)
                strip.configure(height=32)

                info = tk.Frame(card, bg=self.theme["card_bg"])
                info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8), pady=6)

                tk.Label(info, text=item["name"], font=FONT_SANS_BOLD,
                         bg=self.theme["card_bg"], fg=self.theme["text_secondary"],
                         anchor=tk.W).pack(anchor=tk.W)

                meta = f"{item.get('refresh_type', '')} · 目标 {item['target_count']}次"
                tk.Label(info, text=meta, font=FONT_CAPTION,
                         bg=self.theme["card_bg"], fg=self.theme["text_muted"],
                         anchor=tk.W).pack(anchor=tk.W)

                # 恢复按钮
                restore_btn = tk.Label(card, text="恢复", font=FONT_CAPTION,
                                       bg=self.theme["primary"], fg="#FFFFFF",
                                       padx=8, pady=2, cursor="hand2")
                restore_btn.pack(side=tk.RIGHT, padx=(0, 8), pady=6)
                restore_btn.bind("<Button-1>",
                                 lambda e, iid=item["id"], d=dlg: self._restore_item(iid, d))

        dlg.wait_window()

    def _restore_item(self, item_id: int, dialog: tk.Toplevel):
        """从归档恢复事项"""
        self.db.update(
            """UPDATE schedule_items
               SET is_archived = 0, current_count = 0, is_completed = 0,
                   reset_date = ?, updated_at = datetime('now','localtime')
               WHERE id = ?""",
            (date.today().isoformat(), item_id),
        )
        dialog.destroy()
        self._load_data()

    def _on_start_timer(self, item_id: int, target_minutes: int):
        """从自律日程页面启动计时"""
        app = self.master._app if hasattr(self.master, '_app') else None
        if not app:
            return
        item = self.db.fetch_one("SELECT * FROM schedule_items WHERE id = ?", (item_id,))
        if not item:
            return
        app.timer_active = True
        app.timer_item_id = item_id
        app.timer_item_name = item["name"]
        app.timer_target_minutes = target_minutes
        app.timer_start_time = datetime.now()
        app.timer_notified = False
        # 导航到工作台
        app.sidebar.set_active_by_key("workbench")
        app.content.show_page("workbench")

    def apply_theme(self, theme: dict):
        self.theme = theme
        self.configure(style="TFrame")
        self._sections_canvas.configure(bg=theme["bg"])
        self._calendar.apply_theme(theme)
        for bar in self._item_bars.values():
            bar.apply_theme(theme)
        for header in self._label_headers:
            header.apply_theme(theme)
        for key in self._empty_labels:
            self._empty_labels[key].configure(background=theme["bg"])
        # 主题切换后重算日历高度
        self._on_page_configure()


# ═══════════════════════════════════════════
# 日期详情浮窗
# ═══════════════════════════════════════════

class DayDetailPopover(tk.Toplevel):
    """点击日历格子弹出的当日完成详情和待办"""

    def __init__(self, parent, clicked_date: date,
                 logs: list[dict], todos: list[dict],
                 theme: dict, on_delete_log=None):
        super().__init__(parent)
        self.theme = theme
        self._on_delete_log = on_delete_log

        self.title(f"{clicked_date.isoformat()} 详情")
        self.resizable(False, False)
        self.transient(parent)
        self.configure(bg=theme["card_bg"])

        # 标题
        header = tk.Frame(self, bg=theme["card_bg"])
        header.pack(fill=tk.X, padx=12, pady=(10, 4))

        weekday_names = ["一", "二", "三", "四", "五", "六", "日"]
        wd = weekday_names[clicked_date.weekday()]
        tk.Label(header, text=f"{clicked_date.isoformat()} 星期{wd}",
                 font=FONT_SANS_BOLD, bg=theme["card_bg"], fg=theme["text"],
                 ).pack(side=tk.LEFT)

        # ── 自律完成记录 ──
        if logs:
            ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=12)
            tk.Label(self, text=f"✅ 完成记录（{len(logs)}）", font=FONT_CAPTION,
                     bg=theme["card_bg"], fg=self.theme["text_secondary"],
                     ).pack(anchor=tk.W, padx=12, pady=(6, 2))
            for log in logs:
                row = tk.Frame(self, bg=theme["card_bg"])
                row.pack(fill=tk.X, padx=12, pady=3)

                icon = log.get("mark_icon", "★")
                color = log.get("mark_color", "#3B82F6")
                tk.Label(row, text=icon, font=("Segoe UI", 14),
                         bg=theme["card_bg"], fg=color).pack(side=tk.LEFT, padx=(0, 8))
                tk.Label(row, text=log["name"], font=FONT_SANS,
                         bg=theme["card_bg"], fg=theme["text"],
                         ).pack(side=tk.LEFT)

                del_btn = tk.Label(row, text="✕", font=("Segoe UI", 10),
                                   bg=theme["card_bg"], fg=theme["text_secondary"],
                                   cursor="hand2")
                del_btn.pack(side=tk.RIGHT)
                del_btn.bind("<Button-1>", lambda e, lid=log["id"]: self._delete(lid))
                del_btn.bind("<Enter>",
                             lambda e, b=del_btn: b.configure(fg=theme["danger"]))
                del_btn.bind("<Leave>",
                             lambda e, b=del_btn: b.configure(fg=theme["text_secondary"]))

        # ── 待办截止 ──
        if todos:
            ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=12, pady=(4, 0))
            tk.Label(self, text=f"📋 截止待办（{len(todos)}）", font=FONT_CAPTION,
                     bg=theme["card_bg"], fg=self.theme["text_secondary"],
                     ).pack(anchor=tk.W, padx=12, pady=(6, 2))
            for todo in todos:
                row = tk.Frame(self, bg=theme["card_bg"])
                row.pack(fill=tk.X, padx=12, pady=3)
                status = "✓" if todo.get("is_completed") else "○"
                tk.Label(row, text=status, font=("Segoe UI", 10),
                         bg=theme["card_bg"],
                         fg=self.theme["success"] if todo.get("is_completed") else self.theme["text_muted"],
                         ).pack(side=tk.LEFT, padx=(0, 8))
                tk.Label(row, text=todo["title"], font=FONT_SANS,
                         bg=theme["card_bg"], fg=self.theme["text"],
                         ).pack(side=tk.LEFT)

        # 空状态
        if not logs and not todos:
            ttk.Label(self, text="当天没有记录或待办",
                      style="Muted.TLabel", font=FONT_CAPTION,
                      background=theme["card_bg"],
                      ).pack(padx=16, pady=20)

        ttk.Button(self, text="关闭", command=self.destroy).pack(pady=(8, 12))

        self._center_near_parent(parent)
        self.wait_window()

    def _delete(self, log_id: int):
        if self._on_delete_log:
            self._on_delete_log(log_id)
        # 从浮窗移除该行
        for child in self.winfo_children():
            if isinstance(child, tk.Frame):
                for widget in child.winfo_children():
                    widget.destroy()
        self.destroy()

    def _center_near_parent(self, parent):
        self.update_idletasks()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        w, h = self.winfo_width(), self.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"+{x}+{y}")
