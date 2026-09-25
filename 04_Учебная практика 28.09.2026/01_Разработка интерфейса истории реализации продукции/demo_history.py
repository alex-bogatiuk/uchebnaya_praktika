"""Демонстрационный запуск интерфейса истории реализации продукции."""

import os
import sys
import tkinter as tk
from tkinter import ttk

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from history_window import PartnerHistoryWindow, DEFAULT_DB_PATH

FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Helvetica"


def main() -> None:
    root = tk.Tk()
    root.title("CRM: Реестр партнеров (Демонстрация истории)")
    root.geometry("640x380")
    root.configure(bg="#F1F5F9")

    tk.Label(
        root,
        text="Выберите партнера и нажмите кнопку для просмотра истории продаж:",
        font=(FONT_FAMILY, 11, "bold"),
        bg="#F1F5F9",
    ).pack(pady=(20, 10))

    partners = [
        (1, "ООО 'Логистик-Экспресс'"),
        (2, "ИП Петров А.В."),
        (3, "ТК 'Быстрый Путь'"),
        (4, "ЗАО 'База Строитель'"),
        (5, "ПАО 'Металл-Снаб' (без продаж)"),
    ]

    selected_var = tk.IntVar(value=1)

    frame = tk.Frame(root, bg="#FFFFFF", padx=16, pady=12, highlightbackground="#CBD5E1", highlightthickness=1)
    frame.pack(fill="x", padx=30, pady=10)

    for pid, pname in partners:
        rb = tk.Radiobutton(
            frame,
            text=f"ID {pid}: {pname}",
            variable=selected_var,
            value=pid,
            bg="#FFFFFF",
            font=(FONT_FAMILY, 10),
            anchor="w",
        )
        rb.pack(fill="x", pady=2)

    def open_history() -> None:
        pid = selected_var.get()
        pname = next(name for i, name in partners if i == pid)
        PartnerHistoryWindow(root, partner_id=pid, partner_name=pname, db_path=DEFAULT_DB_PATH)

    btn = tk.Button(
        root,
        text="История продаж →",
        font=(FONT_FAMILY, 11, "bold"),
        bg="#0284C7",
        fg="#FFFFFF",
        padx=18,
        pady=8,
        relief="flat",
        cursor="hand2",
        command=open_history,
    )
    btn.pack(pady=15)

    root.mainloop()


if __name__ == "__main__":
    main()
