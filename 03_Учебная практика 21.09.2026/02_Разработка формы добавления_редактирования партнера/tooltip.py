"""Модуль вспомогательных всплывающих подсказок (ToolTips) для Tkinter."""

import tkinter as tk
from typing import Optional


class ToolTip:
    """Всплывающая контекстная подсказка при наведении курсора мыши на виджет."""

    def __init__(self, widget: tk.Widget, text: str, delay_ms: int = 400) -> None:
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self.tip_window: Optional[tk.Toplevel] = None
        self.scheduled_id: Optional[str] = None

        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)
        self.widget.bind("<ButtonPress>", self._on_leave)

    def _on_enter(self, event: Optional[tk.Event] = None) -> None:
        self._schedule()

    def _on_leave(self, event: Optional[tk.Event] = None) -> None:
        self._cancel()
        self._hide()

    def _schedule(self) -> None:
        self._cancel()
        self.scheduled_id = self.widget.after(self.delay_ms, self._show)

    def _cancel(self) -> None:
        if self.scheduled_id:
            self.widget.after_cancel(self.scheduled_id)
            self.scheduled_id = None

    def _show(self) -> None:
        if self.tip_window or not self.text:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tip_window,
            text=self.text,
            justify="left",
            background="#0F172A",
            foreground="#FFFFFF",
            font=("Segoe UI", 9),
            padx=8,
            pady=4,
            relief="flat",
        )
        label.pack()

    def _hide(self) -> None:
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
