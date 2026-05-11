"""底部状态栏"""

from tkinter import ttk
from config import FONT_CAPTION


class StatusBar(ttk.Frame):
    def __init__(self, parent, theme: dict):
        super().__init__(parent, style="Statusbar.TFrame", height=28)
        self.theme = theme
        self.pack(side="bottom", fill="x")

        self._label = ttk.Label(
            self,
            text="就绪",
            style="Muted.TLabel",
            font=FONT_CAPTION,
            background=theme["statusbar_bg"],
        )
        self._label.pack(side="left", padx=12)

    def set_text(self, text: str):
        self._label.configure(text=text)

    def apply_theme(self, theme: dict):
        self.theme = theme
        self.configure(style="Statusbar.TFrame")
        self._label.configure(background=theme["statusbar_bg"])
