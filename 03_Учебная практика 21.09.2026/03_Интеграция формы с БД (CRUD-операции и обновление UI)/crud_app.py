"""Интеграция формы с БД: CRUD-операции и реактивное обновление интерфейса."""

import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TASK_02_DIR = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "02_Разработка формы добавления_редактирования партнера")
)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
if TASK_02_DIR not in sys.path:
    sys.path.insert(0, TASK_02_DIR)

from database_crud import DatabaseManager
from edit_window import PartnerEditWindow

FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Helvetica"
BG_MAIN = "#F1F5F9"
BG_CARD = "#FFFFFF"
BORDER_COLOR = "#CBD5E1"
ACCENT_BLUE = "#0284C7"
TEXT_PRIMARY = "#0F172A"
TEXT_SECONDARY = "#475569"


class PartnerCardWidget(tk.Frame):
    """Интерактивная карточка партнера с поддержкой двойного клика."""

    def __init__(
        self,
        parent: tk.Widget,
        data: Dict[str, Any],
        on_edit_click: Any,
    ) -> None:
        super().__init__(
            parent,
            bg=BG_CARD,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            padx=14,
            pady=10,
            cursor="hand2",
        )
        self.data = data
        self.on_edit_click = on_edit_click
        self._build_ui()

        # Привязка двойного клика к открытию редактирования (ТЗ пункт 2)
        self.bind("<Double-Button-1>", lambda e: self.on_edit_click(self.data["partner_id"]))
        for child in self.winfo_children():
            child.bind("<Double-Button-1>", lambda e: self.on_edit_click(self.data["partner_id"]))

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        left_box = tk.Frame(self, bg=BG_CARD)
        left_box.grid(row=0, column=0, sticky="w")

        p_type = self.data.get("partner_type", "ООО")
        c_name = self.data.get("company_name", "")
        title_text = f"{p_type} | {c_name}"

        tk.Label(
            left_box,
            text=title_text,
            font=(FONT_FAMILY, 11, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_CARD,
        ).pack(anchor="w")

        dir_text = f"Директор: {self.data.get('director', 'Не указан')}"
        tk.Label(left_box, text=dir_text, font=(FONT_FAMILY, 9), fg=TEXT_SECONDARY, bg=BG_CARD).pack(anchor="w")

        phone_text = f"Тел: {self.data.get('phone', 'Не указан')}  |  Email: {self.data.get('contact_email', '')}"
        tk.Label(left_box, text=phone_text, font=(FONT_FAMILY, 9), fg=TEXT_SECONDARY, bg=BG_CARD).pack(anchor="w")

        rate_text = f"Рейтинг: {self.data.get('rating', 0)}  |  Объем: {self.data.get('total_quantity', 0):,} шт."
        tk.Label(left_box, text=rate_text, font=(FONT_FAMILY, 9), fg=TEXT_SECONDARY, bg=BG_CARD).pack(anchor="w")

        right_box = tk.Frame(self, bg=BG_CARD)
        right_box.grid(row=0, column=1, sticky="e", padx=(10, 0))

        discount_val = self.data.get("discount_percent", 0)
        tk.Label(
            right_box,
            text=f"{discount_val}%",
            font=(FONT_FAMILY, 16, "bold"),
            fg=ACCENT_BLUE,
            bg=BG_CARD,
        ).pack(side="top", anchor="e")

        btn_edit = tk.Button(
            right_box,
            text="Изменить",
            font=(FONT_FAMILY, 9),
            bg="#E2E8F0",
            fg=TEXT_PRIMARY,
            padx=10,
            pady=3,
            relief="flat",
            cursor="hand2",
            command=lambda: self.on_edit_click(self.data["partner_id"]),
        )
        btn_edit.pack(side="bottom", pady=(6, 0))


class CrudAppWindow(tk.Tk):
    """Главное окно приложения с реактивной синхронизацией данных с БД."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        super().__init__()
        self.db = db_manager or DatabaseManager()
        self.title("CRM: Реестр партнеров (CRUD + Live Sync)")
        self.geometry("820x640")
        self.minsize(700, 500)
        self.configure(bg=BG_MAIN)

        self.edit_window: Optional[PartnerEditWindow] = None
        self._build_main_ui()
        self.refresh_list()

    def _build_main_ui(self) -> None:
        # Верхняя панель управления
        top_bar = tk.Frame(self, bg=BG_CARD, padx=20, pady=14, highlightbackground=BORDER_COLOR, highlightthickness=1)
        top_bar.pack(fill="x", side="top")

        tk.Label(
            top_bar,
            text="База данных партнеров компании",
            font=(FONT_FAMILY, 15, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_CARD,
        ).pack(side="left")

        # Кнопка добавления новой записи (ТЗ пункт 1)
        btn_add = tk.Button(
            top_bar,
            text="+ Добавить партнера",
            font=(FONT_FAMILY, 10, "bold"),
            bg=ACCENT_BLUE,
            fg="#FFFFFF",
            padx=16,
            pady=7,
            relief="flat",
            cursor="hand2",
            command=self.open_add_dialog,
        )
        btn_add.pack(side="right")

        # Прокручиваемый контейнер списка карточек
        container = tk.Frame(self, bg=BG_MAIN)
        container.pack(fill="both", expand=True, padx=20, pady=16)

        self.canvas = tk.Canvas(container, bg=BG_MAIN, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.cards_frame = tk.Frame(self.canvas, bg=BG_MAIN)

        self.cards_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

    def refresh_list(self) -> None:
        """Реактивно перезагружает данные из БД и перерисовывает интерфейс (ТЗ пункт 1, 2)."""
        for child in self.cards_frame.winfo_children():
            child.destroy()

        partners = self.db.get_all_partners_with_discounts()
        for p in partners:
            card = PartnerCardWidget(
                self.cards_frame,
                data=p,
                on_edit_click=self.open_edit_dialog,
            )
            card.pack(fill="x", pady=5)

    def open_add_dialog(self) -> None:
        """Открытие пустой формы создания записи."""
        if self.edit_window and self.edit_window.winfo_exists():
            self.edit_window.lift()
            return

        self.edit_window = PartnerEditWindow(
            parent=self,
            partner_id=None,
            partner_data=None,
            on_save=self._handle_save_partner,
        )

    def open_edit_dialog(self, partner_id: int) -> None:
        """Открытие формы с автоматической подгрузкой данных из БД по ID (ТЗ пункт 2)."""
        if self.edit_window and self.edit_window.winfo_exists():
            self.edit_window.lift()
            return

        # Извлекаем свежие данные непосредственно из БД
        data = self.db.get_partner_by_id(partner_id)
        if not data:
            messagebox.showerror("Ошибка", f"Партнер с ID {partner_id} не найден в базе данных.")
            return

        self.edit_window = PartnerEditWindow(
            parent=self,
            partner_id=partner_id,
            partner_data=data,
            on_save=self._handle_save_partner,
        )

    def _handle_save_partner(self, form_data: Dict[str, Any]) -> None:
        """Обработка сохранения: выполнение INSERT или UPDATE с обновлением UI."""
        partner_id = form_data.get("partner_id")
        try:
            if partner_id is None:
                # Режим добавления (ТЗ пункт 1)
                new_id = self.db.add_partner(form_data)
                print(f"[CRUD] Успешно добавлен новый партнер с ID={new_id}")
            else:
                # Режим редактирования (ТЗ пункт 2)
                self.db.update_partner(int(partner_id), form_data)
                print(f"[CRUD] Успешно обновлены данные партнера с ID={partner_id}")

            # Автоматическое перерисовывание таблицы на главной форме
            self.refresh_list()
        except Exception as exc:
            messagebox.showerror(
                "Ошибка базы данных",
                f"Не удалось сохранить данные партнера:\n{exc}\n\nПроверьте уникальность email и корректность полей.",
            )


if __name__ == "__main__":
    app = CrudAppWindow()
    app.mainloop()
