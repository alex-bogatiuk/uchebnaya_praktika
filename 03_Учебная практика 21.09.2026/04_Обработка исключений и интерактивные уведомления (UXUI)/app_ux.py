"""Приложение с интерактивными диалоговыми окнами и обработкой исключений (UX/UI)."""

import os
import sqlite3
import sys
import tkinter as tk
from tkinter import messagebox
from typing import Any, Dict, Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TASK_02_DIR = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "02_Разработка формы добавления_редактирования партнера")
)
TASK_03_DIR = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "03_Интеграция формы с БД (CRUD-операции и обновление UI)")
)

for p in [CURRENT_DIR, TASK_02_DIR, TASK_03_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from database_crud import DatabaseManager
from edit_window import PartnerEditWindow
from validator import ValidationError, validate_partner_payload

FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Helvetica"
BG_MAIN = "#F1F5F9"
BG_CARD = "#FFFFFF"
BORDER_COLOR = "#CBD5E1"
ACCENT_BLUE = "#0284C7"
TEXT_PRIMARY = "#0F172A"


class UXPartnerEditWindow(PartnerEditWindow):
    """Расширенная форма партнера с UX-валидацией и MessageBox трех типов."""

    def on_cancel_clicked(self) -> None:
        """Перехват выхода: если данные изменены, показываем Warning MessageBox (ТЗ пункт 2)."""
        if self.has_unsaved_changes():
            answer = messagebox.askyesno(
                title="Предупреждение: несохраненные данные",
                message=(
                    "В форме обнаружены несохраненные изменения.\n\n"
                    "При возврате назад все внесенные правки будут безвозвратно утеряны.\n"
                    "Вы действительно хотите покинуть форму без сохранения?"
                ),
                icon="warning",
                parent=self,
            )
            if not answer:
                # Пользователь решил остаться и продолжить редактирование
                return

        super().on_cancel_clicked()

    def on_save_clicked(self) -> None:
        """Валидация через try...except и показ Error / Information диалогов."""
        raw_data = self.get_form_data()
        try:
            # Валидация входных данных (ТЗ пункт 1)
            cleaned_data = validate_partner_payload(raw_data)
        except ValidationError as err:
            # Вывод Error MessageBox с пояснением и порядком действий (ТЗ пункт 2)
            messagebox.showerror(
                title="Ошибка валидации данных",
                message=err.get_full_message(),
                icon="error",
                parent=self,
            )
            return

        if self.on_save:
            try:
                self.on_save(cleaned_data)
                # Вывод Information MessageBox при успехе (ТЗ пункт 2)
                mode_action = "обновлены" if self.partner_id else "добавлены в базу"
                messagebox.showinfo(
                    title="Успешное сохранение",
                    message=(
                        f"Данные партнера '{cleaned_data['company_name']}' успешно {mode_action}!\n"
                        "Реестр партнеров автоматически обновлен."
                    ),
                    icon="info",
                    parent=self.parent,
                )
                self.grab_release()
                self.destroy()
            except sqlite3.IntegrityError as db_err:
                messagebox.showerror(
                    title="Ошибка базы данных (Нарушение уникальности)",
                    message=(
                        f"Не удалось сохранить запись из-за конфликта данных:\n{db_err}\n\n"
                        "Порядок действий:\n"
                        "1. Проверьте адрес электронной почты на уникальность (такой email уже может существовать).\n"
                        "2. Измените email и повторите попытку."
                    ),
                    icon="error",
                    parent=self,
                )
            except Exception as unk_err:
                messagebox.showerror(
                    title="Критическая ошибка системы",
                    message=(
                        f"Произошел системный сбой:\n{unk_err}\n\n"
                        "Порядок действий:\n"
                        "1. Проверьте доступность файла базы данных partners.db.\n"
                        "2. Обратитесь к системному администратору."
                    ),
                    icon="error",
                    parent=self,
                )


class UxAppMainWindow(tk.Tk):
    """Главная форма CRM с полной защитой от сбоев и эргономичным UX."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        super().__init__()
        self.db = db_manager or DatabaseManager()
        self.title("CRM: Реестр партнеров [Интерактивная защита UX/UI]")
        self.geometry("820x640")
        self.minsize(700, 500)
        self.configure(bg=BG_MAIN)

        self.edit_window: Optional[UXPartnerEditWindow] = None
        self._build_ui()
        self.refresh_list()

    def _build_ui(self) -> None:
        top_bar = tk.Frame(self, bg=BG_CARD, padx=20, pady=14, highlightbackground=BORDER_COLOR, highlightthickness=1)
        top_bar.pack(fill="x", side="top")

        tk.Label(
            top_bar,
            text="Управление реестром партнеров (UX/UI Validation)",
            font=(FONT_FAMILY, 15, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_CARD,
        ).pack(side="left")

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

        self.container = tk.Frame(self, bg=BG_MAIN, padx=20, pady=16)
        self.container.pack(fill="both", expand=True)

    def refresh_list(self) -> None:
        for w in self.container.winfo_children():
            w.destroy()

        partners = self.db.get_all_partners_with_discounts()
        for p in partners:
            card = tk.Frame(self.container, bg=BG_CARD, padx=14, pady=10, highlightbackground=BORDER_COLOR, highlightthickness=1)
            card.pack(fill="x", pady=4)

            title = f"{p.get('partner_type', 'ООО')} | {p.get('company_name')} (Скидка: {p.get('discount_percent', 0)}%)"
            tk.Label(card, text=title, font=(FONT_FAMILY, 11, "bold"), fg=TEXT_PRIMARY, bg=BG_CARD).pack(side="left")

            btn_edit = tk.Button(
                card,
                text="Редактировать",
                font=(FONT_FAMILY, 9),
                bg="#E2E8F0",
                fg=TEXT_PRIMARY,
                padx=10,
                pady=3,
                relief="flat",
                cursor="hand2",
                command=lambda pid=p["partner_id"]: self.open_edit_dialog(pid),
            )
            btn_edit.pack(side="right")

    def open_add_dialog(self) -> None:
        if self.edit_window and self.edit_window.winfo_exists():
            self.edit_window.lift()
            return

        self.edit_window = UXPartnerEditWindow(
            parent=self,
            partner_id=None,
            partner_data=None,
            on_save=self._on_save_partner,
        )

    def open_edit_dialog(self, partner_id: int) -> None:
        if self.edit_window and self.edit_window.winfo_exists():
            self.edit_window.lift()
            return

        data = self.db.get_partner_by_id(partner_id)
        if not data:
            messagebox.showerror(
                "Ошибка",
                f"Партнер с ID={partner_id} не найден в базе данных.",
                icon="error",
            )
            return

        self.edit_window = UXPartnerEditWindow(
            parent=self,
            partner_id=partner_id,
            partner_data=data,
            on_save=self._on_save_partner,
        )

    def _on_save_partner(self, cleaned_data: Dict[str, Any]) -> None:
        pid = cleaned_data.get("partner_id")
        if pid is None:
            self.db.add_partner(cleaned_data)
        else:
            self.db.update_partner(int(pid), cleaned_data)
        self.refresh_list()


if __name__ == "__main__":
    app = UxAppMainWindow()
    app.mainloop()
