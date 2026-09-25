"""Форма добавления и редактирования партнера (PartnerEditWindow).

Обеспечивает ввод разнородных типов данных в строгом соответствии с ТЗ:
- Наименование (текстовое поле);
- Тип партнера (выпадающий список / ComboBox: ЗАО, ООО, ИП, ПАО, ОАО);
- Рейтинг (целое неотрицательное число);
- Юридический адрес (текстовое поле);
- ФИО руководителя (текстовое поле);
- Телефон и Email компании с визуальными подсказками (маски, плейсхолдеры и ToolTips).
"""

import os
import sys
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, Optional

# Импорт всплывающих подсказок из текущего модуля
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from tooltip import ToolTip

FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Helvetica"
BG_MAIN = "#F1F5F9"
BG_CARD = "#FFFFFF"
BORDER_COLOR = "#CBD5E1"
ACCENT_BLUE = "#0284C7"
TEXT_PRIMARY = "#0F172A"
TEXT_MUTED = "#64748B"
PARTNER_TYPES = ["ООО", "ЗАО", "ИП", "ПАО", "ОАО"]


class PartnerEditWindow(tk.Toplevel):
    """Окно создания и редактирования карточки партнера с валидацией полей."""

    def __init__(
        self,
        parent: tk.Tk,
        partner_id: Optional[int] = None,
        partner_data: Optional[Dict[str, Any]] = None,
        on_save: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent)
        self.parent = parent
        self.partner_id = partner_id
        # Копируем словарь исходных данных для отслеживания факта изменений (dirty state)
        self.initial_data = dict(partner_data) if partner_data else {}
        self.on_save = on_save
        self.on_cancel = on_cancel

        # Установка уникального заголовка в зависимости от переданного ID
        mode_str = "Редактирование" if self.partner_id is not None else "Добавление"
        self.title(f"CRM: Карточка партнера [{mode_str}]")

        self.geometry("600x620")
        self.minsize(540, 560)
        self.configure(bg=BG_MAIN)

        self.transient(parent)
        self.grab_set()

        self._build_form()
        self._populate_fields()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel_clicked)

    def _build_form(self) -> None:
        """Построение сетки формы ввода и подписи полей."""
        root_pad = tk.Frame(self, bg=BG_MAIN, padx=24, pady=20)
        root_pad.pack(fill="both", expand=True)

        header_title = (
            f"Редактирование партнера #{self.partner_id}"
            if self.partner_id is not None
            else "Регистрация нового партнера"
        )
        tk.Label(
            root_pad,
            text=header_title,
            font=(FONT_FAMILY, 15, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_MAIN,
        ).pack(anchor="w", pady=(0, 16))

        form_card = tk.Frame(root_pad, bg=BG_CARD, padx=20, pady=20, highlightbackground=BORDER_COLOR, highlightthickness=1)
        form_card.pack(fill="both", expand=True)
        form_card.columnconfigure(1, weight=1)

        fields = [
            ("Наименование компании *:", "entry_name"),
            ("Тип партнера *:", "combo_type"),
            ("Рейтинг (целое неотриц.) *:", "entry_rating"),
            ("Юридический адрес:", "entry_address"),
            ("ФИО руководителя:", "entry_director"),
            ("Контактный телефон:", "entry_phone"),
            ("Электронная почта (Email) *:", "entry_email"),
        ]

        row_idx = 0
        for label_text, attr_name in fields:
            lbl = tk.Label(
                form_card,
                text=label_text,
                font=(FONT_FAMILY, 10, "bold"),
                fg=TEXT_PRIMARY,
                bg=BG_CARD,
                anchor="w",
            )
            lbl.grid(row=row_idx, column=0, sticky="w", pady=7, padx=(0, 12))

            if attr_name == "combo_type":
                # Запрещаем свободный ввод произвольного текста, фиксируя допустимые ОПФ
                combo = ttk.Combobox(
                    form_card,
                    values=PARTNER_TYPES,
                    state="readonly",
                    font=(FONT_FAMILY, 10),
                )
                combo.current(0)
                combo.grid(row=row_idx, column=1, sticky="ew", pady=7)
                setattr(self, attr_name, combo)
            else:
                entry = tk.Entry(
                    form_card,
                    font=(FONT_FAMILY, 10),
                    highlightbackground=BORDER_COLOR,
                    highlightthickness=1,
                    relief="flat",
                    bg="#FFFFFF",
                )
                entry.grid(row=row_idx, column=1, sticky="ew", pady=7)
                setattr(self, attr_name, entry)

            row_idx += 1

        # Навешивание ToolTips и плейсхолдеров на телефон и email
        ToolTip(self.entry_phone, "Ожидаемый формат: +7 (XXX) XXX-XX-XX или +7XXXXXXXXXX")
        ToolTip(self.entry_email, "Пример: partner@company.ru (обязательно содержит '@' и точку)")
        ToolTip(self.entry_rating, "Целое число от 0 и выше (например: 0, 5, 10, 100)")

        # Панель управления действиями (Назад / Сохранить)
        btn_bar = tk.Frame(root_pad, bg=BG_MAIN, pady=16)
        btn_bar.pack(fill="x", side="bottom")

        self.btn_cancel = tk.Button(
            btn_bar,
            text="← Назад",
            font=(FONT_FAMILY, 10),
            bg="#E2E8F0",
            fg=TEXT_PRIMARY,
            padx=16,
            pady=7,
            relief="flat",
            cursor="hand2",
            command=self.on_cancel_clicked,
        )
        self.btn_cancel.pack(side="left")

        self.btn_save = tk.Button(
            btn_bar,
            text="Сохранить изменения" if self.partner_id else "Добавить в реестр",
            font=(FONT_FAMILY, 10, "bold"),
            bg=ACCENT_BLUE,
            fg="#FFFFFF",
            padx=20,
            pady=7,
            relief="flat",
            cursor="hand2",
            command=self.on_save_clicked,
        )
        self.btn_save.pack(side="right")

    def _populate_fields(self) -> None:
        """Заполнение полей формы существующими данными при редактировании."""
        if not self.initial_data:
            return

        company_name = self.initial_data.get("company_name", "")
        self.entry_name.insert(0, company_name)

        partner_type = self.initial_data.get("partner_type", "ООО")
        if partner_type in PARTNER_TYPES:
            self.combo_type.set(partner_type)
        else:
            self.combo_type.set("ООО")

        rating_val = str(self.initial_data.get("rating", 0))
        self.entry_rating.insert(0, rating_val)

        address_val = self.initial_data.get("address", "")
        self.entry_address.insert(0, address_val)

        director_val = self.initial_data.get("director", "")
        self.entry_director.insert(0, director_val)

        phone_val = self.initial_data.get("phone", "")
        self.entry_phone.insert(0, phone_val)

        email_val = self.initial_data.get("contact_email", "")
        self.entry_email.insert(0, email_val)

    def get_form_data(self) -> Dict[str, Any]:
        """Сборка текущих введенных значений полей формы в словарь."""
        return {
            "partner_id": self.partner_id,
            "company_name": self.entry_name.get().strip(),
            "partner_type": self.combo_type.get().strip(),
            "rating": self.entry_rating.get().strip(),
            "address": self.entry_address.get().strip(),
            "director": self.entry_director.get().strip(),
            "phone": self.entry_phone.get().strip(),
            "contact_email": self.entry_email.get().strip(),
        }

    def has_unsaved_changes(self) -> bool:
        """Сравнивает текущие данные формы с начальным состоянием."""
        current = self.get_form_data()
        if not self.initial_data:
            # Для режима добавления проверяем наличие ввода хотя бы в одно поле
            return any(
                bool(current[k])
                for k in ["company_name", "rating", "address", "director", "phone", "contact_email"]
            )
        # Для режима редактирования проверяем несовпадение значений
        for key in ["company_name", "partner_type", "address", "director", "phone", "contact_email"]:
            if str(current.get(key, "")).strip() != str(self.initial_data.get(key, "")).strip():
                return True
        if str(current.get("rating", "")).strip() != str(self.initial_data.get("rating", "")).strip():
            return True
        return False

    def on_cancel_clicked(self) -> None:
        """Закрытие карточки партнера и возврат управления."""
        if self.on_cancel:
            self.on_cancel()
        self.grab_release()
        self.destroy()

    def on_save_clicked(self) -> None:
        """Сбор данных и отправка коллбэка сохранения."""
        data = self.get_form_data()
        if self.on_save:
            self.on_save(data)
        self.grab_release()
        self.destroy()
