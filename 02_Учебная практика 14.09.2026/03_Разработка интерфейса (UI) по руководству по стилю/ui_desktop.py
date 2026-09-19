"""Пользовательский графический интерфейс (Desktop UI) на базе Tkinter.

Разработан в строгом соответствии с макетом Screenshot_2.png и ТЗ:
- Заголовок окна: "CRM: Список партнеров и скидок";
- Иконка приложения в углу окна (resources/icon.png / icon.ico);
- Шапка с логотипом компании (resources/logo.png);
- Прокручиваемый список карточек партнеров:
    * Тип | Наименование партнера (жирный шрифт)
    * Директор: ФИО руководителя
    * Номер телефона
    * Рейтинг: X
    * Справа: процент скидки (например, 10%)
- Цветовая гамма: чистый светлый фон карточек, контрастные границы,
  современная типографика Segoe UI / Arial.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional

# Подключение модулей бэкенда и бизнес-логики
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_02_DIR = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "02_Интеграция с БД и агрегация данных (SQL + Backend)")
)
if MODULE_02_DIR not in sys.path:
    sys.path.insert(0, MODULE_02_DIR)

try:
    from database import DatabaseManager
except ImportError:
    DatabaseManager = None  # type: ignore


# Константы стилизации в соответствии с Screenshot_2
FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Helvetica"
BG_MAIN = "#F1F5F9"
BG_HEADER = "#FFFFFF"
BG_CARD = "#FFFFFF"
BG_CARD_HOVER = "#F8FAFC"
BORDER_COLOR = "#94A3B8"
TEXT_PRIMARY = "#0F172A"
TEXT_SECONDARY = "#475569"
TEXT_MUTED = "#64748B"
ACCENT_DISCOUNT = "#0F172A"


class PartnerCard(tk.Frame):
    """Визуальная карточка одного партнера по макету Screenshot_2.png."""

    def __init__(
        self,
        parent: tk.Widget,
        partner_data: Dict[str, Any],
        on_click: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        super().__init__(
            parent,
            bg=BG_CARD,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            padx=16,
            pady=12,
            cursor="hand2",
        )
        self.partner_data = partner_data
        self.on_click = on_click
        self._build_card()

    def _build_card(self) -> None:
        """Построение элементов внутри карточки."""
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        # Левая колонка: 4 строки информации
        left_frame = tk.Frame(self, bg=BG_CARD)
        left_frame.grid(row=0, column=0, sticky="w")

        # 1 строка: "Тип | Наименование партнера"
        partner_type = self.partner_data.get("partner_type", "ООО")
        clean_name = self.partner_data.get("clean_name") or self.partner_data.get("company_name", "")
        title_text = f"{partner_type} | {clean_name}"

        title_lbl = tk.Label(
            left_frame,
            text=title_text,
            font=(FONT_FAMILY, 12, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_CARD,
            anchor="w",
        )
        title_lbl.pack(fill="x", anchor="w", pady=(0, 2))

        # 2 строка: "Директор"
        director_name = self.partner_data.get("director") or "Директор: не указан"
        director_text = director_name if director_name.lower().startswith("директор") else f"Директор: {director_name}"
        director_lbl = tk.Label(
            left_frame,
            text=director_text,
            font=(FONT_FAMILY, 10),
            fg=TEXT_SECONDARY,
            bg=BG_CARD,
            anchor="w",
        )
        director_lbl.pack(fill="x", anchor="w", pady=(0, 2))

        # 3 строка: Номер телефона
        phone = self.partner_data.get("phone") or "Телефон не указан"
        phone_lbl = tk.Label(
            left_frame,
            text=phone,
            font=(FONT_FAMILY, 10),
            fg=TEXT_SECONDARY,
            bg=BG_CARD,
            anchor="w",
        )
        phone_lbl.pack(fill="x", anchor="w", pady=(0, 2))

        # 4 строка: "Рейтинг: 10"
        rating_val = self.partner_data.get("rating", 0)
        rating_text = f"Рейтинг: {int(rating_val) if float(rating_val).is_integer() else rating_val}"
        rating_lbl = tk.Label(
            left_frame,
            text=rating_text,
            font=(FONT_FAMILY, 10),
            fg=TEXT_MUTED,
            bg=BG_CARD,
            anchor="w",
        )
        rating_lbl.pack(fill="x", anchor="w")

        # Правая колонка: Процент скидки
        discount_val = self.partner_data.get("discount_percent", 0)
        discount_lbl = tk.Label(
            self,
            text=f"{discount_val}%",
            font=(FONT_FAMILY, 18, "bold"),
            fg=ACCENT_DISCOUNT,
            bg=BG_CARD,
            anchor="e",
        )
        discount_lbl.grid(row=0, column=1, sticky="e", padx=(20, 0))

        # Привязка событий наведения (hover)
        widgets = [self, left_frame, title_lbl, director_lbl, phone_lbl, rating_lbl, discount_lbl]
        for w in widgets:
            w.bind("<Enter>", lambda e: self._set_bg(BG_CARD_HOVER, widgets))
            w.bind("<Leave>", lambda e: self._set_bg(BG_CARD, widgets))
            if self.on_click:
                w.bind("<Button-1>", lambda e: self.on_click(self.partner_data))

    def _set_bg(self, color: str, widgets: List[tk.Widget]) -> None:
        for w in widgets:
            try:
                w.config(bg=color)
            except tk.TclError:
                pass


class PartnersWindow(tk.Tk):
    """Главное окно приложения 'CRM: Список партнеров и скидок'."""

    def __init__(self, db_manager: Optional[Any] = None) -> None:
        super().__init__()
        self.title("CRM: Список партнеров и скидок")
        self.geometry("780x640")
        self.minsize(600, 480)
        self.configure(bg=BG_MAIN)

        self.db_manager = db_manager or (DatabaseManager() if DatabaseManager else None)

        self._setup_icons()
        self._build_header()
        self._build_card_list_container()
        self._load_and_render_partners()

    def _setup_icons(self) -> None:
        """Установка иконки приложения в заголовке окна."""
        res_dir = os.path.join(CURRENT_DIR, "resources")
        icon_png_path = os.path.join(res_dir, "icon.png")
        icon_ico_path = os.path.join(res_dir, "icon.ico")

        if os.path.exists(icon_png_path):
            try:
                self.icon_photo = tk.PhotoImage(file=icon_png_path)
                self.iconphoto(True, self.icon_photo)
            except Exception as e:
                print(f"Не удалось загрузить icon.png: {e}")

        if sys.platform == "win32" and os.path.exists(icon_ico_path):
            try:
                self.iconbitmap(icon_ico_path)
            except Exception as e:
                print(f"Не удалось установить icon.ico: {e}")

    def _build_header(self) -> None:
        """Построение верхней шапки с логотипом компании и заголовком."""
        header_frame = tk.Frame(
            self,
            bg=BG_HEADER,
            highlightbackground="#E2E8F0",
            highlightthickness=1,
            padx=20,
            pady=12,
        )
        header_frame.pack(fill="x", side="top")

        # Логотип компании
        res_dir = os.path.join(CURRENT_DIR, "resources")
        logo_path = os.path.join(res_dir, "logo.png")
        if os.path.exists(logo_path):
            try:
                self.logo_img = tk.PhotoImage(file=logo_path)
                logo_lbl = tk.Label(header_frame, image=self.logo_img, bg=BG_HEADER)
                logo_lbl.pack(side="left", padx=(0, 14))
            except Exception as e:
                print(f"Не удалось загрузить logo.png: {e}")

        # Текстовый заголовок шапки
        text_frame = tk.Frame(header_frame, bg=BG_HEADER)
        text_frame.pack(side="left", fill="y")

        app_title = tk.Label(
            text_frame,
            text="CRM: Список партнеров и скидок",
            font=(FONT_FAMILY, 15, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_HEADER,
        )
        app_title.pack(anchor="w")

        subtitle = tk.Label(
            text_frame,
            text="Компания «Мастер Пол» • Расчет накопительных скидок по ТЗ",
            font=(FONT_FAMILY, 9),
            fg=TEXT_MUTED,
            bg=BG_HEADER,
        )
        subtitle.pack(anchor="w", pady=(2, 0))

        # Правая часть шапки: кнопка обновления и счетчик
        right_frame = tk.Frame(header_frame, bg=BG_HEADER)
        right_frame.pack(side="right")

        self.stats_lbl = tk.Label(
            right_frame,
            text="Партнеров: 0",
            font=(FONT_FAMILY, 10, "bold"),
            fg=TEXT_SECONDARY,
            bg=BG_HEADER,
        )
        self.stats_lbl.pack(anchor="e", pady=(0, 4))

        refresh_btn = tk.Button(
            right_frame,
            text="⟳ Обновить данные",
            font=(FONT_FAMILY, 9),
            bg="#F8FAFC",
            fg=TEXT_PRIMARY,
            activebackground="#E2E8F0",
            relief="groove",
            cursor="hand2",
            padx=10,
            pady=3,
            command=self._load_and_render_partners,
        )
        refresh_btn.pack(anchor="e")

    def _build_card_list_container(self) -> None:
        """Создает прокручиваемую область (Canvas + Scrollbar) для карточек."""
        container = tk.Frame(self, bg=BG_MAIN)
        container.pack(fill="both", expand=True, padx=20, pady=16)

        self.canvas = tk.Canvas(
            container,
            bg=BG_MAIN,
            highlightthickness=0,
        )
        self.scrollbar = ttk.Scrollbar(
            container,
            orient="vertical",
            command=self.canvas.yview,
        )
        self.scrollable_frame = tk.Frame(self.canvas, bg=BG_MAIN)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw",
        )

        # Растягиваем карточки по ширине окна при изменении размера
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width),
        )

        # Прокрутка колесиком мыши
        self.canvas.bind_all(
            "<MouseWheel>",
            lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def _load_and_render_partners(self) -> None:
        """Загрузка партнеров из БД и отрисовка карточек."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not self.db_manager:
            err_lbl = tk.Label(
                self.scrollable_frame,
                text="Ошибка подключения к базе данных",
                fg="red",
                bg=BG_MAIN,
                font=(FONT_FAMILY, 12),
            )
            err_lbl.pack(pady=40)
            return

        partners = self.db_manager.get_all_partners_with_discounts()
        self.stats_lbl.config(text=f"Партнеров: {len(partners)}")

        if not partners:
            empty_lbl = tk.Label(
                self.scrollable_frame,
                text="Список партнеров пуст",
                fg=TEXT_MUTED,
                bg=BG_MAIN,
                font=(FONT_FAMILY, 12),
            )
            empty_lbl.pack(pady=40)
            return

        for partner in partners:
            card = PartnerCard(
                self.scrollable_frame,
                partner,
                on_click=self._on_partner_click,
            )
            card.pack(fill="x", expand=True, pady=6)

    def _on_partner_click(self, partner: Dict[str, Any]) -> None:
        """Обработка клика по карточке партнера."""
        print(
            f"Выбран партнер: {partner.get('company_name')} (Скидка: {partner.get('discount_percent')}%)"
        )


def launch_ui() -> None:
    """Точка входа для отдельного запуска UI."""
    app = PartnersWindow()
    app.mainloop()


if __name__ == "__main__":
    launch_ui()
