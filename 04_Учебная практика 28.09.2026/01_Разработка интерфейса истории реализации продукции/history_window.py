"""Окно истории реализации продукции партнера (PartnerHistoryWindow).

Соответствует требованиям ТЗ:
1. Заголовок: "CRM: История реализации продукции — [Название партнера]";
2. Соответствие руководству по стилю (цвета, шрифты, корпоративный логотип и иконка);
3. Таблица со следующими обязательными полями:
   - Наименование продукции
   - Количество (шт.)
   - Дата продажи (в понятном для человека формате ДД.ММ.ГГГГ);
4. Навигация: возможность возврата на главную форму без потери контекста.
"""

import datetime
import os
import sqlite3
import sys
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional

FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Helvetica"
BG_MAIN = "#F1F5F9"
BG_HEADER = "#FFFFFF"
BG_CARD = "#FFFFFF"
BORDER_COLOR = "#CBD5E1"
ACCENT_BLUE = "#0284C7"
TEXT_PRIMARY = "#0F172A"
TEXT_SECONDARY = "#475569"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Поиск файла БД в структуре проекта
DB_CANDIDATES = [
    os.path.join(CURRENT_DIR, "..", "..", "03_Учебная практика 21.09.2026", "03_Интеграция формы с БД (CRUD-операции и обновление UI)", "partners.db"),
    os.path.join(CURRENT_DIR, "..", "..", "02_Учебная практика 14.09.2026", "02_Интеграция с БД и агрегация данных (SQL + Backend)", "partners.db"),
    os.path.join(CURRENT_DIR, "partners.db"),
]
DEFAULT_DB_PATH = next((p for p in DB_CANDIDATES if os.path.exists(p)), DB_CANDIDATES[0])
RESOURCES_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "resources"))


def format_human_date(raw_date: str) -> str:
    """Преобразует дату из формата YYYY-MM-DD в понятный человеку формат ДД.ММ.ГГГГ."""
    if not raw_date:
        return "-"
    cleaned = raw_date.strip()
    try:
        if "-" in cleaned:
            dt = datetime.datetime.strptime(cleaned, "%Y-%m-%d")
            return dt.strftime("%d.%m.%Y")
        elif "." in cleaned:
            parts = cleaned.split(".")
            if len(parts) == 3 and len(parts[2]) == 4:
                return cleaned
    except Exception:
        pass
    return cleaned


class PartnerHistoryWindow(tk.Toplevel):
    """Окно просмотра истории реализации продукции выбранного партнера."""

    def __init__(
        self,
        parent: tk.Tk,
        partner_id: int,
        partner_name: str,
        db_path: str = DEFAULT_DB_PATH,
        on_close: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent)
        self.parent = parent
        self.partner_id = partner_id
        self.partner_name = partner_name.strip()
        self.db_path = db_path
        self.on_close = on_close

        # Строгий контекстный заголовок окна по ТЗ (пункт 2)
        self.title(f"CRM: История реализации продукции — {self.partner_name}")
        self.geometry("780x560")
        self.minsize(650, 450)
        self.configure(bg=BG_MAIN)

        self._apply_icons()
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._load_history_data()
        self.protocol("WM_DELETE_WINDOW", self.on_back_clicked)

    def _apply_icons(self) -> None:
        """Установка иконки приложения."""
        ico_path = os.path.join(RESOURCES_DIR, "icon.ico")
        png_path = os.path.join(RESOURCES_DIR, "icon.png")
        if os.path.exists(ico_path) and sys.platform == "win32":
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass
        elif os.path.exists(png_path):
            try:
                img = tk.PhotoImage(file=png_path)
                self.iconphoto(True, img)
            except Exception:
                pass

    def _build_ui(self) -> None:
        """Построение интерфейса окна истории."""
        # Верхняя плашка с логотипом и названием партнера
        header_frame = tk.Frame(self, bg=BG_HEADER, padx=20, pady=14, highlightbackground=BORDER_COLOR, highlightthickness=1)
        header_frame.pack(fill="x", side="top")

        # Загрузка логотипа, если доступен
        logo_path = os.path.join(RESOURCES_DIR, "logo.png")
        self.logo_img = None
        if os.path.exists(logo_path):
            try:
                self.logo_img = tk.PhotoImage(file=logo_path)
                logo_lbl = tk.Label(header_frame, image=self.logo_img, bg=BG_HEADER)
                logo_lbl.pack(side="left", padx=(0, 14))
            except Exception:
                pass

        title_box = tk.Frame(header_frame, bg=BG_HEADER)
        title_box.pack(side="left", fill="y")

        tk.Label(
            title_box,
            text="История реализации продукции",
            font=(FONT_FAMILY, 14, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_HEADER,
        ).pack(anchor="w")

        self.subtitle_lbl = tk.Label(
            title_box,
            text=f"Партнер: {self.partner_name} (ID: {self.partner_id})",
            font=(FONT_FAMILY, 10),
            fg=TEXT_SECONDARY,
            bg=BG_HEADER,
        )
        self.subtitle_lbl.pack(anchor="w")

        # Карточка итоговой статистики
        stats_frame = tk.Frame(header_frame, bg=BG_HEADER)
        stats_frame.pack(side="right")

        self.lbl_total_quantity = tk.Label(
            stats_frame,
            text="Всего отгружено: ... шт.",
            font=(FONT_FAMILY, 10, "bold"),
            fg=ACCENT_BLUE,
            bg=BG_HEADER,
        )
        self.lbl_total_quantity.pack(anchor="e")

        # Основной контейнер с таблицей
        body = tk.Frame(self, bg=BG_MAIN, padx=20, pady=16)
        body.pack(fill="both", expand=True)

        # Стилизация таблицы ttk.Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "History.Treeview",
            font=(FONT_FAMILY, 10),
            rowheight=28,
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
        )
        style.configure(
            "History.Treeview.Heading",
            font=(FONT_FAMILY, 10, "bold"),
            background="#E2E8F0",
            foreground=TEXT_PRIMARY,
        )
        style.map("History.Treeview", background=[("selected", "#E0F2FE")])

        cols = ("product_name", "quantity", "delivery_date", "unit_price", "total_sum")
        self.tree = ttk.Treeview(
            body,
            columns=cols,
            show="headings",
            style="History.Treeview",
            selectmode="browse",
        )

        # Обязательные поля по ТЗ (пункт 4)
        self.tree.heading("product_name", text="Наименование продукции", anchor="w")
        self.tree.heading("quantity", text="Количество (шт.)", anchor="e")
        self.tree.heading("delivery_date", text="Дата продажи", anchor="center")
        self.tree.heading("unit_price", text="Цена за ед. (руб.)", anchor="e")
        self.tree.heading("total_sum", text="Сумма (руб.)", anchor="e")

        self.tree.column("product_name", width=260, anchor="w")
        self.tree.column("quantity", width=120, anchor="e")
        self.tree.column("delivery_date", width=120, anchor="center")
        self.tree.column("unit_price", width=110, anchor="e")
        self.tree.column("total_sum", width=120, anchor="e")

        scroll_y = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        # Нижняя панель с кнопкой Назад
        footer = tk.Frame(self, bg=BG_MAIN, padx=20, pady=12)
        footer.pack(fill="x", side="bottom")

        btn_back = tk.Button(
            footer,
            text="← Назад",
            font=(FONT_FAMILY, 10),
            bg="#E2E8F0",
            fg=TEXT_PRIMARY,
            padx=18,
            pady=7,
            relief="flat",
            cursor="hand2",
            command=self.on_back_clicked,
        )
        btn_back.pack(side="left")

    def _load_history_data(self) -> None:
        """Выполняет SQL-запрос с JOIN и заполняет таблицу (ТЗ пункт 4)."""
        if not os.path.exists(self.db_path):
            self.lbl_total_quantity.config(text="Файл БД не найден")
            return

        query = """
            SELECT
                pr.product_name,
                d.quantity,
                d.delivery_date,
                d.unit_price,
                (d.quantity * d.unit_price) AS total_sum
            FROM deliveries AS d
            INNER JOIN products AS pr
                ON d.product_id = pr.product_id
            WHERE
                d.partner_id = ?
            ORDER BY
                d.delivery_date DESC;
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, (self.partner_id,))
            rows = cursor.fetchall()

            total_qty = 0
            total_money = 0.0

            for r in rows:
                qty = int(r["quantity"])
                total_qty += qty
                price = float(r["unit_price"])
                total_row_sum = float(r["total_sum"])
                total_money += total_row_sum

                # Человекочитаемая дата ДД.ММ.ГГГГ
                date_str = format_human_date(str(r["delivery_date"]))

                self.tree.insert(
                    "",
                    "end",
                    values=(
                        r["product_name"],
                        f"{qty:,} шт.".replace(",", " "),
                        date_str,
                        f"{price:,.2f}".replace(",", " "),
                        f"{total_row_sum:,.2f}".replace(",", " "),
                    ),
                )

            conn.close()

            if rows:
                self.lbl_total_quantity.config(
                    text=f"Всего отгружено: {total_qty:,} шт. | Сумма: {total_money:,.2f} ₽".replace(",", " ")
                )
            else:
                self.lbl_total_quantity.config(text="История отгрузок пуста (0 шт.)")
                self.tree.insert("", "end", values=("— Нет записей об отгрузках —", "0", "-", "-", "-"))
        except Exception as exc:
            self.lbl_total_quantity.config(text=f"Ошибка загрузки данных: {exc}")

    def on_back_clicked(self) -> None:
        """Возврат на главную форму."""
        if self.on_close:
            self.on_close()
        self.grab_release()
        self.destroy()
