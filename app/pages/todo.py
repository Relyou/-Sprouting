"""待办记事页面"""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk, messagebox
from datetime import datetime, date

from config import (
    FONT_TITLE, FONT_SANS, FONT_SANS_BOLD, FONT_CAPTION, FONT_MONO,
    PAD_X, PAD_Y, GAP,
)

# ── 重要/紧急标签映射 ──
IMP_LABELS = {1: "很低", 2: "较低", 3: "一般", 4: "重要", 5: "非常重要"}
URG_LABELS = {1: "不急", 2: "较缓", 3: "一般", 4: "紧急", 5: "非常紧急"}

# ── 坐标轴颜色映射 ──
X_AXIS_COLORS = ["#10B981", "#34D399", "#FBBF24", "#F87171", "#EF4444"]   # 紧急: 绿→红
Y_AXIS_COLORS = ["#FCD34D", "#FDE68A", "#C4B5FD", "#A78BFA", "#8B5CF6"]   # 重要: 黄→紫


# ═══════════════════════════════════════════
# 待办事项对话框
# ═══════════════════════════════════════════

class TodoDialog(tk.Toplevel):
    """新建或编辑待办事项"""

    def __init__(self, parent, theme: dict, edit_data: dict | None = None):
        super().__init__(parent)
        self.theme = theme
        self.result: dict | None = None
        self._edit_data = edit_data

        self.title("编辑待办" if edit_data else "新建待办")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=theme["card_bg"])

        self._build_form()
        self._center_on_parent(parent)
        self.wait_window()

    def _build_form(self):
        pad = {"padx": 16, "pady": (8, 2)}
        bg = self.theme["card_bg"]
        fg = self.theme["text"]
        ed = self._edit_data or {}

        # ── 标题 ──
        ttk.Label(self, text="标题", background=bg).pack(anchor=tk.W, **pad)
        self._title_var = tk.StringVar(value=ed.get("title", ""))
        ttk.Entry(self, textvariable=self._title_var, width=44).pack(
            fill=tk.X, padx=16, pady=(0, 8))

        # ── 描述 ──
        ttk.Label(self, text="描述（可选）", background=bg).pack(anchor=tk.W, **pad)
        self._desc_text = tk.Text(self, height=3, width=44, font=FONT_SANS,
                                  bg=self.theme["input_bg"], fg=self.theme["text"],
                                  relief="solid", borderwidth=1,
                                  wrap=tk.WORD)
        self._desc_text.pack(fill=tk.X, padx=16, pady=(0, 8))
        if ed.get("description"):
            self._desc_text.insert("1.0", ed["description"])

        # ── 截止日期 + 提醒时间 ──
        row1 = tk.Frame(self, bg=bg)
        row1.pack(fill=tk.X, padx=16, pady=(0, 8))

        ttk.Label(row1, text="截止日期", background=bg).pack(side=tk.LEFT)
        self._due_var = tk.StringVar(
            value=ed.get("due_date") or date.today().strftime("%Y-%m-%d"))
        due_entry = ttk.Entry(row1, textvariable=self._due_var, width=14,
                              font=FONT_MONO)
        due_entry.pack(side=tk.LEFT, padx=GAP)
        ttk.Label(row1, text="YYYY-MM-DD", foreground=self.theme["text_secondary"],
                  background=bg, font=FONT_CAPTION).pack(side=tk.LEFT)
        ttk.Label(row1, text="  提醒", background=bg).pack(side=tk.LEFT, padx=(16, 0))
        self._remind_var = tk.StringVar(value=ed.get("remind_time", ""))
        ttk.Entry(row1, textvariable=self._remind_var, width=10, font=FONT_MONO).pack(
            side=tk.LEFT, padx=GAP)
        ttk.Label(row1, text="HH:MM", foreground=self.theme["text_secondary"],
                  background=bg, font=FONT_CAPTION).pack(side=tk.LEFT)

        # ── 重要程度 ──
        ttk.Label(self, text="重要程度", background=bg).pack(anchor=tk.W, **pad)
        self._imp_var = tk.IntVar(value=ed.get("importance", 3))
        self._imp_label = ttk.Label(self, text=IMP_LABELS[self._imp_var.get()],
                                    background=bg, foreground=self.theme["primary"],
                                    font=FONT_SANS_BOLD, width=8)
        imp_row = tk.Frame(self, bg=bg)
        imp_row.pack(fill=tk.X, padx=16, pady=(0, 8))
        imp_scale = ttk.Scale(imp_row, from_=1, to=5, variable=self._imp_var,
                              orient=tk.HORIZONTAL, length=300,
                              command=lambda v: self._on_scale_change("imp"))
        imp_scale.pack(side=tk.LEFT)
        self._imp_label.pack(side=tk.LEFT, padx=(12, 0))

        # ── 紧急程度 ──
        ttk.Label(self, text="紧急程度", background=bg).pack(anchor=tk.W, **pad)
        self._urg_var = tk.IntVar(value=ed.get("urgency", 3))
        self._urg_label = ttk.Label(self, text=URG_LABELS[self._urg_var.get()],
                                    background=bg, foreground=self.theme["danger"],
                                    font=FONT_SANS_BOLD, width=8)
        urg_row = tk.Frame(self, bg=bg)
        urg_row.pack(fill=tk.X, padx=16, pady=(0, 12))
        urg_scale = ttk.Scale(urg_row, from_=1, to=5, variable=self._urg_var,
                              orient=tk.HORIZONTAL, length=300,
                              command=lambda v: self._on_scale_change("urg"))
        urg_scale.pack(side=tk.LEFT)
        self._urg_label.pack(side=tk.LEFT, padx=(12, 0))

        # ── 按钮 ──
        btn_row = tk.Frame(self, bg=bg)
        btn_row.pack(fill=tk.X, padx=16, pady=(0, 16))
        ttk.Button(btn_row, text="取消", command=self.destroy).pack(side=tk.RIGHT, padx=(GAP, 0))
        ttk.Button(btn_row, text="确定", command=self._on_confirm).pack(side=tk.RIGHT)

    def _on_scale_change(self, which: str):
        if which == "imp":
            self._imp_label.configure(text=IMP_LABELS[self._imp_var.get()])
        else:
            self._urg_label.configure(text=URG_LABELS[self._urg_var.get()])

    def _on_confirm(self):
        title = self._title_var.get().strip()
        if not title:
            messagebox.showwarning("提示", "请输入待办标题", parent=self)
            return
        due = self._due_var.get().strip()
        remind = self._remind_var.get().strip()

        # 基本日期格式校验
        if due:
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("提示", "日期格式应为 YYYY-MM-DD", parent=self)
                return
        if remind:
            try:
                datetime.strptime(remind, "%H:%M")
            except ValueError:
                messagebox.showwarning("提示", "时间格式应为 HH:MM", parent=self)
                return

        self.result = {
            "title": title,
            "description": self._desc_text.get("1.0", tk.END).strip(),
            "due_date": due or None,
            "remind_time": remind or None,
            "importance": self._imp_var.get(),
            "urgency": self._urg_var.get(),
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
# 查看全部对话框
# ═══════════════════════════════════════════

class TodoListDialog(tk.Toplevel):
    """查看所有待办事件的完整信息"""

    def __init__(self, parent, theme: dict, items: list[dict],
                 on_edit=None, on_complete=None, on_delete=None):
        super().__init__(parent)
        self.theme = theme
        self._on_edit = on_edit
        self._on_complete = on_complete
        self._on_delete = on_delete

        self.title("所有待办事项")
        self.transient(parent)
        self.configure(bg=theme["bg"])
        self.geometry("640x480")

        self._build_ui(items)
        self._center_on_parent(parent)

    def _build_ui(self, items: list[dict]):
        bg = self.theme["bg"]

        # 头
        header = tk.Frame(self, bg=bg)
        header.pack(fill=tk.X, padx=12, pady=(10, 4))
        ttk.Label(header, text=f"共 {len(items)} 项待办",
                  font=FONT_TITLE).pack(side=tk.LEFT)

        # 滚动列表
        canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0), pady=(0, 12))

        inner = ttk.Frame(canvas, style="TFrame")
        canvas.create_window((0, 0), window=inner, anchor=tk.NW, tags="inner")

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(
            canvas.find_withtag("inner")[0], width=e.width) if canvas.find_withtag("inner") else None)
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        for item in items:
            self._add_item_card(inner, item)

        if not items:
            ttk.Label(inner, text="暂无待办事项",
                      style="Muted.TLabel", font=FONT_CAPTION).pack(pady=40)

    def _add_item_card(self, parent, item: dict):
        card = tk.Frame(parent, bg=self.theme["card_bg"],
                        highlightbackground=self.theme["border"],
                        highlightthickness=1)
        card.pack(fill=tk.X, padx=0, pady=4)

        # 第一行：标题 + 状态
        row1 = tk.Frame(card, bg=self.theme["card_bg"])
        row1.pack(fill=tk.X, padx=10, pady=(8, 2))
        is_done = item.get("is_completed", 0)
        title_font = FONT_SANS_BOLD + ("overstrike",) if is_done else FONT_SANS_BOLD
        title_fg = self.theme["text_secondary"] if is_done else self.theme["text"]
        tk.Label(row1, text=item["title"], font=title_font, fg=title_fg,
                 bg=self.theme["card_bg"], anchor=tk.W).pack(side=tk.LEFT)

        status_text = "✓ 已完成" if is_done else "进行中"
        status_fg = self.theme["success"] if is_done else self.theme["primary"]
        tk.Label(row1, text=status_text, font=FONT_CAPTION, fg=status_fg,
                 bg=self.theme["card_bg"]).pack(side=tk.RIGHT)

        # 第二行：描述
        desc = item.get("description", "")
        if desc:
            tk.Label(card, text=desc, font=FONT_CAPTION,
                     fg=self.theme["text_secondary"], bg=self.theme["card_bg"],
                     anchor=tk.W, wraplength=500, justify=tk.LEFT,
                     ).pack(fill=tk.X, padx=10, pady=(0, 2))

        # 第三行：截止 / 提醒 / 重要 / 紧急
        row3 = tk.Frame(card, bg=self.theme["card_bg"])
        row3.pack(fill=tk.X, padx=10, pady=(2, 8))

        meta_parts = []
        if item.get("due_date"):
            meta_parts.append(f"📅 {item['due_date']}")
        if item.get("remind_time"):
            meta_parts.append(f"⏰ {item['remind_time']}")
        meta_parts.append(f"⭐ {'★' * item['importance']}{'☆' * (5 - item['importance'])}")
        meta_parts.append(f"🔥 {'●' * item['urgency']}{'○' * (5 - item['urgency'])}")

        tk.Label(row3, text="  |  ".join(meta_parts),
                 font=FONT_CAPTION, fg=self.theme["text_muted"],
                 bg=self.theme["card_bg"]).pack(side=tk.LEFT)

        # 操作按钮
        btn_frame = tk.Frame(card, bg=self.theme["card_bg"])
        btn_frame.pack(side=tk.RIGHT, padx=(0, 10))

        if not is_done:
            done_btn = tk.Label(btn_frame, text="完成", font=FONT_CAPTION,
                                fg=self.theme["success"], bg=self.theme["card_bg"],
                                cursor="hand2")
            done_btn.pack(side=tk.RIGHT, padx=(8, 0))
            done_btn.bind("<Button-1>", lambda e, iid=item["id"],
                          c=card: self._mark_done(iid, c))

        edit_btn = tk.Label(btn_frame, text="编辑", font=FONT_CAPTION,
                            fg=self.theme["primary"], bg=self.theme["card_bg"],
                            cursor="hand2")
        edit_btn.pack(side=tk.RIGHT, padx=(8, 0))
        edit_btn.bind("<Button-1>", lambda e, iid=item["id"]: self._trigger_edit(iid))

        del_btn = tk.Label(btn_frame, text="删除", font=FONT_CAPTION,
                           fg=self.theme["danger"], bg=self.theme["card_bg"],
                           cursor="hand2")
        del_btn.pack(side=tk.RIGHT, padx=(8, 0))
        del_btn.bind("<Button-1>", lambda e, iid=item["id"]: self._trigger_delete(iid))

    def _mark_done(self, item_id: int, card: tk.Frame):
        if self._on_complete:
            self._on_complete(item_id)
        self.destroy()

    def _trigger_edit(self, item_id: int):
        if self._on_edit:
            self._on_edit(item_id)
        self.destroy()

    def _trigger_delete(self, item_id: int):
        if self._on_delete:
            self._on_delete(item_id)
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
# 四象限散点图
# ═══════════════════════════════════════════

class QuadrantChart(tk.Canvas):
    """重要-紧急四象限散点图"""

    MARGIN_LEFT = 52
    MARGIN_RIGHT = 24
    MARGIN_TOP = 20
    MARGIN_BOTTOM = 34

    def __init__(self, parent, theme: dict):
        super().__init__(parent, bg=theme["card_bg"], highlightthickness=0)
        self.theme = theme
        self._items: list[dict] = []
        self._point_rects: list[tuple] = []  # (x1, y1, x2, y2, item_id, title, due_date)
        self._tooltip_id = None
        self._tip_font = tkfont.Font(family=FONT_CAPTION[0], size=FONT_CAPTION[1])

        self.bind("<Configure>", self._on_resize)
        self.bind("<Motion>", self._on_motion)

    def set_items(self, items: list[dict]):
        self._items = items
        self._draw()

    def _plot_area(self):
        w = self.winfo_width()
        h = self.winfo_height()
        return (
            self.MARGIN_LEFT,
            self.MARGIN_TOP,
            w - self.MARGIN_RIGHT,
            h - self.MARGIN_BOTTOM,
        )

    def _data_to_xy(self, urgency: float, importance: float):
        """将数据坐标 (1~5, 1~5) 映射到画布坐标"""
        x1, y1, x2, y2 = self._plot_area()
        x = x1 + (urgency - 1) / 4 * (x2 - x1)
        y = y2 - (importance - 1) / 4 * (y2 - y1)
        return x, y

    def _xy_to_data(self, cx: float, cy: float):
        """画布坐标 → 数据坐标（仅用于 tooltip 匹配）"""
        x1, y1, x2, y2 = self._plot_area()
        urgency = (cx - x1) / (x2 - x1) * 4 + 1
        importance = (y2 - cy) / (y2 - y1) * 4 + 1
        return urgency, importance

    def _on_resize(self, event=None):
        self._draw()

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10:
            return

        x1, y1, x2, y2 = self._plot_area()

        # ── 四象限渐变背景 ──
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2

        # 每个象限用 6×6 网格模拟渐变
        GRID = 6
        quads = [
            # (qx1, qy1, qx2, qy2, color_origin, color_dir_x, color_dir_y)
            # color_dir 是渐变目标方向（远离原点 = 更饱和）
            (x1, y1, mid_x, mid_y, "#F7FEF7", "#E8F5E9", "#E8F5E9"),       # 左下
            (mid_x, y1, x2, mid_y, "#FFFBF5", "#FFF3E0", "#FFF3E0"),       # 右下
            (x1, mid_y, mid_x, y2, "#F8F6FF", "#EDE7F6", "#EDE7F6"),       # 左上
            (mid_x, mid_y, x2, y2, "#FFF5F5", "#FFEBEE", "#FFEBEE"),       # 右上
        ]
        for qx1, qy1, qx2, qy2, c_origin, c_dx, c_dy in quads:
            step_w = (qx2 - qx1) / GRID
            step_h = (qy2 - qy1) / GRID
            for gi in range(GRID):
                for gj in range(GRID):
                    rx = qx1 + gi * step_w
                    ry = qy1 + gj * step_h
                    # 越靠近原点（(1,1) 数据坐标 = 左下角）越浅
                    # 用 gi+gj 作为距离原点的近似
                    t = (gi + gj) / (GRID * 2 - 2)  # 0 (近原点) → 1 (远原点)
                    c = _lerp_hex(c_origin, c_dx, t)
                    self.create_rectangle(
                        rx, ry, rx + step_w + 1, ry + step_h + 1,
                        fill=c, outline="", tags="quad",
                    )

        # ── 象限分割线 ──
        self.create_line(mid_x, y1, mid_x, y2, fill=self.theme["border"], width=1, dash=(3, 3))
        self.create_line(x1, mid_y, x2, mid_y, fill=self.theme["border"], width=1, dash=(3, 3))

        # ── 坐标轴 ──
        self.create_line(x1, y2, x2, y2, fill=self.theme["border"], width=1)
        self.create_line(x1, y1, x1, y2, fill=self.theme["border"], width=1)

        # ── 轴刻度和标签 ──
        for i in range(1, 6):
            # x 轴
            tx, _ = self._data_to_xy(i, 1)
            self.create_line(tx, y2, tx, y2 + 5, fill=self.theme["text_secondary"], width=1)
            xc = X_AXIS_COLORS[i - 1]
            self.create_text(tx, y2 + 16, text=str(i), font=FONT_CAPTION, fill=xc, anchor=tk.N)

            # y 轴
            _, ty = self._data_to_xy(1, i)
            self.create_line(x1 - 5, ty, x1, ty, fill=self.theme["text_secondary"], width=1)
            yc = Y_AXIS_COLORS[i - 1]
            self.create_text(x1 - 8, ty, text=str(i), font=FONT_CAPTION, fill=yc, anchor=tk.E)

        # ── 轴标签 ──
        self.create_text((x1 + x2) / 2, h - 4, text="紧急程度 →",
                          font=FONT_CAPTION, fill=self.theme["text_muted"], anchor=tk.S)
        self.create_text(6, (y1 + y2) / 2, text="重\n要\n程\n度\n→",
                          font=FONT_CAPTION, fill=self.theme["text_muted"], anchor=tk.CENTER)

        # ── 绘制事件点 ──
        self._point_rects.clear()
        for item in self._items:
            eff_urg = _effective_urgency(item)
            imp = item["importance"]
            px, py = self._data_to_xy(eff_urg, imp)

            # 点大小基于综合重要度
            weight = eff_urg * imp
            radius = max(4, min(int(weight * 1.6), 12))

            fill_color = _blend_point_color(eff_urg, imp)
            border_color = self._darken(fill_color, 0.3)

            # 已完成事项用灰色
            if item.get("is_completed"):
                fill_color = self.theme["text_secondary"]
                border_color = self.theme["text_muted"]

            self.create_oval(px - radius, py - radius, px + radius, py + radius,
                             fill=fill_color, outline=border_color, width=1,
                             tags=f"point_{item['id']}")

            # 记录点击区域（含截止日期用于 tooltip）
            r = radius + 2  # 扩大点击热区
            self._point_rects.append((
                px - r, py - r, px + r, py + r,
                item["id"], item["title"], item.get("due_date") or "",
            ))

    def _on_motion(self, event):
        """鼠标悬停检测 + tooltip"""
        cx, cy = event.x, event.y

        # 清除旧 tooltip（用 * 解包，确保逐个删除）
        if self._tooltip_id:
            self.delete(*self._tooltip_id)
            self._tooltip_id = None

        for (rx1, ry1, rx2, ry2, item_id, title, due_date) in self._point_rects:
            if rx1 <= cx <= rx2 and ry1 <= cy <= ry2:
                # 显示 tooltip：第一行事件名，第二行截止日期
                tip_x = cx + 14
                tip_y = cy - 40
                due_str = due_date or "无截止"
                text = f"{title}\n📅 {due_str}"
                line1, line2 = text.split("\n")
                # 用字体测量实际像素宽度
                tw = max(self._tip_font.measure(line1),
                         self._tip_font.measure(line2), 80)
                th = 44  # 两行高度

                # tooltip 背景
                bg_id = self.create_rectangle(
                    tip_x - 4, tip_y - 2, tip_x + tw, tip_y + th,
                    fill="#1E293B", outline="", tags="tooltip",
                )
                text_id = self.create_text(
                    tip_x - 4 + tw / 2, tip_y - 2 + th / 2,
                    text=text,
                    font=FONT_CAPTION, fill="#F1F5F9", anchor=tk.CENTER,
                    tags="tooltip",
                )
                self._tooltip_id = (bg_id, text_id)
                return

    @staticmethod
    def _darken(hex_color: str, factor: float) -> str:
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = int(r * (1 - factor))
        g = int(g * (1 - factor))
        b = int(b * (1 - factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    def fade_dot(self, item_id: int, t: float):
        """淡化指定事项的圆点（t: 0→1，越大越淡）"""
        tag = f"point_{item_id}"
        items = self.find_withtag(tag)
        if not items:
            return
        orig_color = self.itemcget(items[0], "fill")
        if not orig_color:
            return
        bg = self.theme["card_bg"]
        fade_color = _lerp_hex(orig_color, bg, t)
        orig_outline = self.itemcget(items[0], "outline") or orig_color
        self.itemconfig(items[0], fill=fade_color, outline=_lerp_hex(orig_outline, bg, t))

    def apply_theme(self, theme: dict):
        self.theme = theme
        self.configure(bg=theme["card_bg"])
        self._draw()


# ═══════════════════════════════════════════
# 紧急事项时间线图
# ═══════════════════════════════════════════

class TimelineChart(tk.Canvas):
    """水平时间线：最紧急 6 事项的卡片排列"""

    def __init__(self, parent, theme: dict):
        super().__init__(parent, bg=theme["card_bg"], highlightthickness=0)
        self.theme = theme
        self._items: list[dict] = []
        self.bind("<Configure>", self._on_resize)

    def set_items(self, items: list[dict]):
        self._items = items[:6]
        self._draw()

    def _on_resize(self, event=None):
        self._draw()

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 20 or h < 20:
            return

        items = self._items
        if not items:
            self.create_text(w / 2, h / 2, text="暂无亟待解决的事项",
                             font=FONT_CAPTION, fill=self.theme["text_secondary"],
                             anchor=tk.CENTER)
            return

        n = len(items)
        card_margin = 8
        total_margin = card_margin * (n + 1)
        card_w = (w - total_margin) / n
        card_h = h - 16

        for i, item in enumerate(items):
            x1 = card_margin + i * (card_w + card_margin)
            y1 = 8
            x2 = x1 + card_w
            y2 = y1 + card_h

            is_done = item.get("is_completed", 0)

            # 卡片背景
            bg_color = self.theme["card_bg"] if not is_done else self.theme["bg"]
            self.create_rectangle(x1, y1, x2, y2,
                                  fill=bg_color,
                                  outline=self.theme["border"],
                                  width=1, tags=f"card_{i}")

            # 顶部颜色条（反映紧急度）
            urg_color = X_AXIS_COLORS[min(item["urgency"] - 1, 4)]
            bar_h = 3
            self.create_rectangle(x1 + 1, y1 + 1, x2 - 1, y1 + 1 + bar_h,
                                  fill=urg_color, outline="", tags=f"bar_{i}")

            # 重要度星级
            stars = "★" * item["importance"] + "☆" * (5 - item["importance"])
            self.create_text(x1 + card_w / 2, y1 + 16, text=stars,
                             font=("Segoe UI", 8), fill=Y_AXIS_COLORS[min(item["importance"] - 1, 4)],
                             anchor=tk.CENTER, tags=f"stars_{i}")

            # 标题（截断）
            title = item["title"]
            max_chars = max(int(card_w / 10), 3)
            display_title = title[:max_chars] + "…" if len(title) > max_chars else title
            title_font = FONT_CAPTION + ("overstrike",) if is_done else FONT_CAPTION + ("bold",)
            self.create_text(x1 + card_w / 2, y1 + card_h / 2 - 4,
                             text=display_title,
                             font=title_font,
                             fill=self.theme["text_secondary"] if is_done else self.theme["text"],
                             anchor=tk.CENTER, tags=f"title_{i}")

            # 截止日期
            due_str = item.get("due_date", "") or "无截止"
            if due_str and len(due_str) > 10:
                due_str = due_str[5:]  # 只显示 MM-DD
            due_color = self._due_color(item.get("due_date"))
            self.create_text(x1 + card_w / 2, y1 + card_h / 2 + 16,
                             text=f"📅 {due_str}",
                             font=FONT_CAPTION,
                             fill=due_color,
                             anchor=tk.CENTER, tags=f"due_{i}")

            # 紧急描述
            urg_text = f"紧急 {item['urgency']}/5"
            self.create_text(x1 + card_w / 2, y1 + card_h - 14,
                             text=urg_text,
                             font=FONT_CAPTION,
                             fill=self.theme["text_muted"],
                             anchor=tk.CENTER, tags=f"urg_{i}")

            # 完成标记
            if is_done:
                self.create_text(x1 + card_w - 14, y1 + 14,
                                 text="✓", font=("Segoe UI", 12, "bold"),
                                 fill=self.theme["success"], anchor=tk.CENTER)

    def _due_color(self, due_str: str | None) -> str:
        if not due_str:
            return self.theme["text_muted"]
        try:
            due = datetime.strptime(due_str, "%Y-%m-%d").date()
            today = date.today()
            days_left = (due - today).days
            if days_left < 0:
                return self.theme["danger"]
            elif days_left <= 3:
                return "#F97316"  # orange urgent
            elif days_left <= 7:
                return self.theme["warning"]
            else:
                return self.theme["success"]
        except ValueError:
            return self.theme["text_muted"]

    def apply_theme(self, theme: dict):
        self.theme = theme
        self.configure(bg=theme["card_bg"])
        self._draw()


# ═══════════════════════════════════════════
# 待办记事主页面
# ═══════════════════════════════════════════

class TodoPage(ttk.Frame):
    def __init__(self, parent, theme: dict, db, thread_pool):
        super().__init__(parent, style="TFrame")
        self.theme = theme
        self.db = db
        self.thread_pool = thread_pool
        self._sort_mode = "urgency"  # urgency | importance | created

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # ── 工具栏 ──
        toolbar = ttk.Frame(self, style="TFrame")
        toolbar.pack(fill=tk.X, padx=PAD_X, pady=(PAD_Y, 0))

        ttk.Label(toolbar, text="待办记事", font=FONT_TITLE).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="+ 新建事项", command=self.on_new).pack(side=tk.RIGHT)

        # ── 主内容：PanedWindow ──
        content = tk.PanedWindow(self, orient=tk.HORIZONTAL,
                                 bg=self.theme["border"], sashwidth=1)
        content.pack(fill=tk.BOTH, expand=True, padx=PAD_X, pady=(PAD_Y, 0))

        # ── 左侧：事件列表 ──
        list_frame = ttk.Frame(content, style="TFrame")
        content.add(list_frame, width=420, minsize=300)

        list_header = ttk.Frame(list_frame, style="TFrame")
        list_header.pack(fill=tk.X, pady=(0, GAP))

        ttk.Label(list_header, text="所有事件", font=FONT_TITLE).pack(side=tk.LEFT)
        ttk.Button(list_header, text="查看全部", command=self._on_view_all).pack(side=tk.RIGHT)

        # 排序按钮
        sort_bar = ttk.Frame(list_frame, style="TFrame")
        sort_bar.pack(fill=tk.X, pady=(0, GAP))
        self._sort_var = tk.StringVar(value="urgency")
        self._sort_label = ttk.Label(sort_bar, text="排序:", font=FONT_CAPTION,
                                     foreground=self.theme["text_secondary"],
                                     background=self.theme["bg"])
        self._sort_label.pack(side=tk.LEFT, padx=(0, 4))
        for key, text in [("urgency", "紧急"), ("importance", "重要"), ("created", "创建")]:
            btn = ttk.Label(sort_bar, text=text, font=FONT_CAPTION,
                           foreground=self.theme["primary"],
                           background=self.theme["bg"],
                           cursor="hand2")
            btn.pack(side=tk.LEFT, padx=2)
            btn.bind("<Button-1>", lambda e, k=key: self._on_sort(k))
            setattr(self, f"_sort_btn_{key}", btn)

        columns = ("title", "importance", "urgency", "due_date", "status")
        self._tree = ttk.Treeview(list_frame, columns=columns,
                                   show="headings", selectmode="browse")
        self._tree.heading("title", text="标题")
        self._tree.heading("importance", text="重要")
        self._tree.heading("urgency", text="紧急")
        self._tree.heading("due_date", text="截止")
        self._tree.heading("status", text="状态")
        self._tree.column("title", width=160, minwidth=80)
        self._tree.column("importance", width=50, anchor=tk.CENTER)
        self._tree.column("urgency", width=50, anchor=tk.CENTER)
        self._tree.column("due_date", width=110, anchor=tk.CENTER)
        self._tree.column("status", width=50, anchor=tk.CENTER)

        tree_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                        command=self._tree.yview)
        self._tree.configure(yscrollcommand=tree_scrollbar.set)

        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 操作按钮栏
        action_bar = ttk.Frame(list_frame, style="TFrame")
        action_bar.pack(fill=tk.X, pady=(GAP, 0))
        self._action_edit_btn = ttk.Button(action_bar, text="编辑",
                                           command=self._on_edit)
        self._action_edit_btn.pack(side=tk.LEFT, padx=(0, GAP))
        self._action_done_btn = ttk.Button(action_bar, text="完成",
                                           command=self._on_action_complete)
        self._action_done_btn.pack(side=tk.LEFT, padx=(0, GAP))
        self._action_del_btn = ttk.Button(action_bar, text="删除",
                                          command=self._on_delete)
        self._action_del_btn.pack(side=tk.LEFT)

        # 为紧急度和重要度配置行颜色（匹配右侧图表轴色）
        for i, c in enumerate(X_AXIS_COLORS):
            self._tree.tag_configure(f"urg_{i + 1}", foreground=c)
        for i, c in enumerate(Y_AXIS_COLORS):
            self._tree.tag_configure(f"imp_{i + 1}", foreground=c)

        self._tree.bind("<Double-1>", lambda e: self._on_edit())
        self._tree.bind("<Delete>", lambda e: self._on_delete())
        self._tree.bind("<Button-3>", self._on_tree_right_click)

        # ── 右侧：图表区 ──
        chart_frame = ttk.Frame(content, style="TFrame")
        content.add(chart_frame)

        # 图表 1：四象限
        chart1_frame = ttk.LabelFrame(chart_frame, text="重要-紧急四象限", padding=4)
        chart1_frame.pack(fill=tk.BOTH, expand=True, pady=(0, GAP))

        self._chart1 = QuadrantChart(chart1_frame, self.theme)
        self._chart1.pack(fill=tk.BOTH, expand=True)

        # 图表 2：时间线
        chart2_frame = ttk.LabelFrame(chart_frame, text="亟待解决", padding=4)
        chart2_frame.pack(fill=tk.BOTH, expand=True, pady=(0, PAD_Y))

        self._chart2 = TimelineChart(chart2_frame, self.theme)
        self._chart2.pack(fill=tk.BOTH, expand=True)

    # ── 数据加载 ──
    def _load_data(self):
        order_map = {
            "urgency": "urgency DESC, importance DESC",
            "importance": "importance DESC, urgency DESC",
            "created": "created_at ASC",
        }
        order = order_map.get(self._sort_mode, "urgency DESC, importance DESC")
        items = self.db.fetch_all(
            f"SELECT * FROM todo_items WHERE is_completed = 0 ORDER BY {order}"
        )
        # 同时加载已完成项（用于图表显示）
        all_items = self.db.fetch_all(
            f"SELECT * FROM todo_items ORDER BY {order}"
        )

        # 更新 Treeview
        for row in self._tree.get_children():
            self._tree.delete(row)
        for item in items:
            status = "⏳" if not item.get("is_completed") else "✓"
            imp = item["importance"]
            urg = item["urgency"]
            self._tree.insert("", tk.END, iid=str(item["id"]),
                              values=(item["title"], imp, urg,
                                      item.get("due_date", "") or "",
                                      status),
                              tags=(f"urg_{urg}",))

        # 更新图表（四象限只显示未完成项）
        self._chart1.set_items([i for i in all_items if not i.get("is_completed")])
        self._chart2.set_items(items)

    # ── 回调 ──
    def on_new(self):
        dlg = TodoDialog(self.winfo_toplevel(), self.theme)
        if dlg.result:
            data = dlg.result
            self.db.insert(
                """INSERT INTO todo_items (title, description, due_date, remind_time,
                   importance, urgency) VALUES (?, ?, ?, ?, ?, ?)""",
                (data["title"], data["description"], data["due_date"],
                 data["remind_time"], data["importance"], data["urgency"]),
            )
            self._load_data()

    def _on_edit(self):
        selection = self._tree.selection()
        if not selection:
            return
        item_id = int(selection[0])
        item = self.db.fetch_one("SELECT * FROM todo_items WHERE id = ?", (item_id,))
        if not item:
            return

        dlg = TodoDialog(self.winfo_toplevel(), self.theme, edit_data=item)
        if dlg.result:
            data = dlg.result
            self.db.update(
                """UPDATE todo_items SET title=?, description=?, due_date=?, remind_time=?,
                   importance=?, urgency=?, updated_at=datetime('now','localtime')
                   WHERE id=?""",
                (data["title"], data["description"], data["due_date"],
                 data["remind_time"], data["importance"], data["urgency"], item_id),
            )
            self._load_data()

    def _on_delete(self):
        selection = self._tree.selection()
        if not selection:
            return
        item_id = int(selection[0])
        if not messagebox.askyesno("确认删除", "确定要删除这个待办事项吗？"):
            return
        self.db.delete("DELETE FROM todo_items WHERE id = ?", (item_id,))
        self._load_data()

    def _on_action_complete(self):
        selection = self._tree.selection()
        if selection:
            self._mark_done(int(selection[0]))

    def _on_tree_right_click(self, event):
        item_iid = self._tree.identify_row(event.y)
        if item_iid:
            self._tree.selection_set(item_iid)
            item = self.db.fetch_one("SELECT * FROM todo_items WHERE id = ?", (int(item_iid),))
            is_done = item.get("is_completed") if item else False
            menu = tk.Menu(self, tearoff=0,
                           bg=self.theme["card_bg"], fg=self.theme["text"],
                           activebackground=self.theme["primary"],
                           activeforeground="#FFFFFF")
            menu.add_command(label="编辑", command=self._on_edit)
            if is_done:
                menu.add_command(label="撤销完成", command=lambda: self._undo_done(int(item_iid)))
            else:
                menu.add_command(label="标记完成", command=lambda: self._mark_done(int(item_iid)))
            menu.add_separator()
            menu.add_command(label="删除", command=self._on_delete)
            menu.post(event.x_root, event.y_root)

    def _undo_done(self, item_id: int):
        """撤销待办完成"""
        self.db.update(
            "UPDATE todo_items SET is_completed=0, updated_at=datetime('now','localtime') WHERE id=?",
            (item_id,),
        )
        self._load_data()

    def _on_sort(self, mode: str):
        self._sort_mode = mode
        # 更新排序按钮样式
        for key in ("urgency", "importance", "created"):
            btn = getattr(self, f"_sort_btn_{key}", None)
            if btn:
                btn.configure(
                    foreground=self.theme["primary"] if key == mode else self.theme["text_secondary"],
                    font=FONT_CAPTION + ("bold",) if key == mode else FONT_CAPTION,
                )
        self._load_data()

    def _on_view_all(self):
        order_map = {
            "urgency": "urgency DESC, importance DESC",
            "importance": "importance DESC, urgency DESC",
            "created": "created_at ASC",
        }
        order = order_map.get(self._sort_mode, "urgency DESC, importance DESC")
        all_items = self.db.fetch_all(f"SELECT * FROM todo_items ORDER BY {order}")
        TodoListDialog(self.winfo_toplevel(), self.theme, all_items,
                       on_edit=lambda iid: self._edit_by_id(iid),
                       on_complete=lambda iid: self._mark_done(iid),
                       on_delete=lambda iid: self._delete_by_id(iid))

    def _edit_by_id(self, item_id: int):
        item = self.db.fetch_one("SELECT * FROM todo_items WHERE id = ?", (item_id,))
        if not item:
            return
        dlg = TodoDialog(self.winfo_toplevel(), self.theme, edit_data=item)
        if dlg.result:
            data = dlg.result
            self.db.update(
                """UPDATE todo_items SET title=?, description=?, due_date=?, remind_time=?,
                   importance=?, urgency=?, updated_at=datetime('now','localtime')
                   WHERE id=?""",
                (data["title"], data["description"], data["due_date"],
                 data["remind_time"], data["importance"], data["urgency"], item_id),
            )
            self._load_data()

    def _delete_by_id(self, item_id: int):
        if messagebox.askyesno("确认删除", "确定要删除这个待办事项吗？"):
            self.db.delete("DELETE FROM todo_items WHERE id = ?", (item_id,))
            self._load_data()

    def _mark_done(self, item_id: int):
        """渐隐动画后标记完成"""
        self._animate_fade(item_id, step=0)

    def _animate_fade(self, item_id: int, step: int):
        """逐帧渐隐：树行和图表圆点同步淡化"""
        STEPS = 6
        if step >= STEPS:
            # 动画结束，真正写入数据库
            self.db.update(
                "UPDATE todo_items SET is_completed = 1, updated_at = datetime('now','localtime') WHERE id = ?",
                (item_id,),
            )
            self._load_data()
            return

        t = (step + 1) / STEPS  # 0.17 → 1.0
        bg = self.theme["bg"]

        # 淡化树行
        try:
            orig_color = X_AXIS_COLORS[
                min(self.db.fetch_one(
                    "SELECT urgency FROM todo_items WHERE id = ?", (item_id,)
                ).get("urgency", 3) - 1, 4)
            ]
        except Exception:
            orig_color = "#64748B"
        fade_color = _lerp_hex(orig_color, bg, t)
        tag_name = f"fade_{item_id}"
        self._tree.tag_configure(tag_name, foreground=fade_color)
        if self._tree.exists(str(item_id)):
            self._tree.item(str(item_id), tags=(tag_name,))

        # 淡化图表圆点
        self._chart1.fade_dot(item_id, t)

        self.after(80, lambda: self._animate_fade(item_id, step + 1))

    # ── 外部接口 ──
    def on_save(self):
        pass

    def apply_theme(self, theme: dict):
        self.theme = theme
        self.configure(style="TFrame")
        self._chart1.apply_theme(theme)
        self._chart2.apply_theme(theme)
        # 刷新排序按钮配色
        self._sort_label.configure(background=theme["bg"])
        for key in ("urgency", "importance", "created"):
            btn = getattr(self, f"_sort_btn_{key}", None)
            if btn:
                btn.configure(background=theme["bg"])


# ═══════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════

def _effective_urgency(item: dict) -> float:
    """计算紧急度漂移：离截止日期越近，x 坐标越大"""
    base = float(item.get("urgency", 3))
    due = item.get("due_date")
    created = item.get("created_at")
    if not due or not created:
        return base
    try:
        created_dt = datetime.fromisoformat(created)
        due_dt = datetime.strptime(due, "%Y-%m-%d") if len(due) <= 10 else datetime.fromisoformat(due)
        total = (due_dt - created_dt).total_seconds()
        elapsed = (datetime.now() - created_dt).total_seconds()
        if total <= 0:
            return base
        drift = min(elapsed / total * 2.0, 5.0 - base)
        return round(base + drift, 1)
    except (ValueError, TypeError):
        return base


def _blend_point_color(urgency: float, importance: float) -> str:
    """x 轴颜色（紧急）+ y 轴颜色（重要）各 50% RGB 混合"""
    # 插值索引
    x_idx = max(0, min(4, int(urgency - 1)))
    x_frac = urgency - 1 - x_idx
    if x_idx >= 4:
        xc = X_AXIS_COLORS[4]
    else:
        xc = _lerp_hex(X_AXIS_COLORS[x_idx], X_AXIS_COLORS[x_idx + 1], x_frac)

    y_idx = max(0, min(4, int(importance - 1)))
    y_frac = importance - 1 - y_idx
    if y_idx >= 4:
        yc = Y_AXIS_COLORS[4]
    else:
        yc = _lerp_hex(Y_AXIS_COLORS[y_idx], Y_AXIS_COLORS[y_idx + 1], y_frac)

    # 混合
    xc = xc.lstrip("#")
    yc = yc.lstrip("#")
    r = (int(xc[0:2], 16) + int(yc[0:2], 16)) // 2
    g = (int(xc[2:4], 16) + int(yc[2:4], 16)) // 2
    b = (int(xc[4:6], 16) + int(yc[4:6], 16)) // 2
    return f"#{r:02x}{g:02x}{b:02x}"


def _lerp_hex(c1: str, c2: str, t: float) -> str:
    c1 = c1.lstrip("#")
    c2 = c2.lstrip("#")
    r = int(int(c1[0:2], 16) + (int(c2[0:2], 16) - int(c1[0:2], 16)) * t)
    g = int(int(c1[2:4], 16) + (int(c2[2:4], 16) - int(c1[2:4], 16)) * t)
    b = int(int(c1[4:6], 16) + (int(c2[4:6], 16) - int(c1[4:6], 16)) * t)
    return f"#{r:02x}{g:02x}{b:02x}"
