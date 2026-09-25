"""Многооконная архитектура и навигация для CRM-системы партнеров.

Реализует:
1. Главную форму со списком партнеров (MainWindow) с заголовком "CRM: Реестр партнеров".
2. Дочернее окно добавления/редактирования (PartnerEditWindow) с заголовками:
   - "CRM: Карточка партнера [Добавление]"
   - "CRM: Карточка партнера [Редактирование]"
3. Механизм последовательного перехода между окнами:
   - Кнопка "Добавить партнера" на главной форме открывает модальное окно PartnerEditWindow.
   - Кнопка "Назад" / "Отмена" закрывает окно карточки и возвращает пользователя к реестру.
4. Сохранение контекста и состояния окон без аварийных завершений.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional

# Определение шрифта для операционной системы
FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Helvetica"
BG_MAIN = "#F1F5F9"
BG_CARD = "#FFFFFF"
BORDER_COLOR = "#94A3B8"
ACCENT_BLUE = "#0284C7"
TEXT_PRIMARY = "#0F172A"
TEXT_SECONDARY = "#475569"


class PartnerEditWindow(tk.Toplevel):
    """Окно добавления / редактирования партнера.

    Открывается поверх главного окна в модальном режиме или с возвратом на главную форму.
    """

    def __init__(
        self,
        parent: tk.Tk,
        partner_id: Optional[int] = None,
        partner_data: Optional[Dict[str, Any]] = None,
        on_save_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_close_callback: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent)
        self.parent = parent
        self.partner_id = partner_id
        self.partner_data = partner_data or {}
        self.on_save_callback = on_save_callback
        self.on_close_callback = on_close_callback

        # Настройка уникального заголовка окна в зависимости от режима (ТЗ пункт 3)
        if self.partner_id is None:
            self.title("CRM: Карточка партнера [Добавление]")
        else:
            self.title("CRM: Карточка партнера [Редактирование]")

        self.geometry("540x480")
        self.minsize(480, 420)
        self.configure(bg=BG_MAIN)

        # Модальное поведение: блокировка фокуса родительского окна
        self.transient(parent)
        self.grab_set()

        self._init_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_back_pressed)

    def _init_ui(self) -> None:
        """Построение базового каркаса окна и элементов навигации."""
        container = tk.Frame(self, bg=BG_MAIN, padx=20, pady=20)
        container.pack(fill="both", expand=True)

        # Заголовочная плашка
        header_text = (
            "Создание нового партнера"
            if self.partner_id is None
            else f"Редактирование партнера (ID: {self.partner_id})"
        )
        header_lbl = tk.Label(
            container,
            text=header_text,
            font=(FONT_FAMILY, 14, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_MAIN,
        )
        header_lbl.pack(anchor="w", pady=(0, 16))

        # Демонстрационная информационная карточка
        info_frame = tk.Frame(container, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, padx=16, pady=16)
        info_frame.pack(fill="both", expand=True)

        mode_desc = (
            "Режим: Добавление новой карточки в реестр.\n"
            "После заполнения полей нажмите 'Сохранить' или вернитесь назад."
            if self.partner_id is None
            else f"Режим: Редактирование существующей записи.\n"
            f"Текущий партнер: {self.partner_data.get('company_name', 'Загрузка...')}"
        )
        tk.Label(
            info_frame,
            text=mode_desc,
            font=(FONT_FAMILY, 10),
            fg=TEXT_SECONDARY,
            bg=BG_CARD,
            justify="left",
        ).pack(anchor="w")

        # Панель навигационных кнопок в нижней части окна (ТЗ пункт 2)
        btn_frame = tk.Frame(container, bg=BG_MAIN, pady=14)
        btn_frame.pack(fill="x", side="bottom")

        # Кнопка 'Назад' (или 'Отмена') возвращает пользователя на главную форму
        self.btn_back = tk.Button(
            btn_frame,
            text="← Назад",
            font=(FONT_FAMILY, 10),
            bg="#E2E8F0",
            fg=TEXT_PRIMARY,
            padx=14,
            pady=6,
            relief="flat",
            cursor="hand2",
            command=self.on_back_pressed,
        )
        self.btn_back.pack(side="left")

        # Кнопка имитации сохранения
        self.btn_save = tk.Button(
            btn_frame,
            text="Сохранить",
            font=(FONT_FAMILY, 10, "bold"),
            bg=ACCENT_BLUE,
            fg="#FFFFFF",
            padx=16,
            pady=6,
            relief="flat",
            cursor="hand2",
            command=self.on_save_pressed,
        )
        self.btn_save.pack(side="right")

    def on_back_pressed(self) -> None:
        """Возврат на главную форму с корректным освобождением фокуса."""
        if self.on_close_callback:
            self.on_close_callback()
        self.grab_release()
        self.destroy()

    def on_save_pressed(self) -> None:
        """Обработка сохранения и закрытие окна."""
        if self.on_save_callback:
            self.on_save_callback(self.partner_data)
        self.grab_release()
        self.destroy()


class MainWindow(tk.Tk):
    """Главная форма системы со списком партнеров (ТЗ пункт 1)."""

    def __init__(self, demo_partners: Optional[List[Dict[str, Any]]] = None) -> None:
        super().__init__()
        # Заголовок строго отражает реестр (ТЗ пункт 3)
        self.title("CRM: Реестр партнеров")
        self.geometry("700x520")
        self.minsize(580, 420)
        self.configure(bg=BG_MAIN)

        self.partners = demo_partners or [
            {"partner_id": 1, "company_name": 'ООО "Логистик-Экспресс"', "type": "ООО", "rating": 5},
            {"partner_id": 2, "company_name": 'ИП Петров А.В.', "type": "ИП", "rating": 4},
            {"partner_id": 3, "company_name": 'ТК "Быстрый Путь"', "type": "ТК", "rating": 5},
        ]

        self.edit_window_instance: Optional[PartnerEditWindow] = None
        self._init_ui()

    def _init_ui(self) -> None:
        """Построение интерфейса главной формы."""
        top_bar = tk.Frame(self, bg=BG_CARD, padx=20, pady=14, highlightbackground=BORDER_COLOR, highlightthickness=1)
        top_bar.pack(fill="x", side="top")

        title_lbl = tk.Label(
            top_bar,
            text="Реестр партнеров компании",
            font=(FONT_FAMILY, 15, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_CARD,
        )
        title_lbl.pack(side="left")

        # Кнопка 'Добавить партнера' (ТЗ пункт 2)
        self.btn_add = tk.Button(
            top_bar,
            text="+ Добавить партнера",
            font=(FONT_FAMILY, 10, "bold"),
            bg=ACCENT_BLUE,
            fg="#FFFFFF",
            padx=14,
            pady=6,
            relief="flat",
            cursor="hand2",
            command=self.open_add_window,
        )
        self.btn_add.pack(side="right")

        # Основной контейнер со списком
        self.content_frame = tk.Frame(self, bg=BG_MAIN, padx=20, pady=16)
        self.content_frame.pack(fill="both", expand=True)

        self.render_list()

    def render_list(self) -> None:
        """Отрисовывает элементы реестра партнеров с кнопками редактирования."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        for item in self.partners:
            card = tk.Frame(
                self.content_frame,
                bg=BG_CARD,
                highlightbackground=BORDER_COLOR,
                highlightthickness=1,
                padx=12,
                pady=10,
            )
            card.pack(fill="x", pady=4)

            info_text = f"{item.get('type', 'ООО')} | {item.get('company_name')} (Рейтинг: {item.get('rating', 0)})"
            tk.Label(
                card,
                text=info_text,
                font=(FONT_FAMILY, 11, "bold"),
                fg=TEXT_PRIMARY,
                bg=BG_CARD,
            ).pack(side="left")

            # Кнопка перехода к редактированию конкретного партнера
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
                command=lambda p=item: self.open_edit_window(p),
            )
            btn_edit.pack(side="right")

    def open_add_window(self) -> None:
        """Открытие окна в режиме добавления партнера."""
        if self.edit_window_instance is not None and self.edit_window_instance.winfo_exists():
            self.edit_window_instance.lift()
            return

        self.edit_window_instance = PartnerEditWindow(
            parent=self,
            partner_id=None,
            partner_data=None,
            on_save_callback=self._on_partner_added,
            on_close_callback=self._on_subwindow_closed,
        )

    def open_edit_window(self, partner: Dict[str, Any]) -> None:
        """Открытие окна в режиме редактирования выбранного партнера."""
        if self.edit_window_instance is not None and self.edit_window_instance.winfo_exists():
            self.edit_window_instance.lift()
            return

        self.edit_window_instance = PartnerEditWindow(
            parent=self,
            partner_id=partner.get("partner_id"),
            partner_data=partner,
            on_save_callback=self._on_partner_edited,
            on_close_callback=self._on_subwindow_closed,
        )

    def _on_partner_added(self, data: Dict[str, Any]) -> None:
        """Коллбэк при добавлении партнера."""
        new_id = len(self.partners) + 1
        new_entry = {
            "partner_id": new_id,
            "company_name": f"Новый партнер #{new_id}",
            "type": "ООО",
            "rating": 5,
        }
        self.partners.append(new_entry)
        self.render_list()

    def _on_partner_edited(self, data: Dict[str, Any]) -> None:
        """Коллбэк при редактировании существующего партнера."""
        self.render_list()

    def _on_subwindow_closed(self) -> None:
        """Коллбэк возврата на главную форму."""
        self.edit_window_instance = None


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
