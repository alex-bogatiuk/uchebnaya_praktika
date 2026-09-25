"""Интерфейс калькулятора расхода материалов (Интеграция метода расчета).

Реализует:
1. Вывод результатов расчета сырья на экран формы;
2. Обработку кода ошибки -1 без аварийных завершений интерфейса;
3. Информативные сообщения об ошибке для пользователя;
4. Строго одна команда на строку и стиль snake_case.
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TASK_02_DIR = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "02_Разработка ядра алгоритма расчета материалов")
)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
if TASK_02_DIR not in sys.path:
    sys.path.insert(0, TASK_02_DIR)

from material_calc import (
    DEFAULT_MATERIAL_TYPES,
    DEFAULT_PRODUCT_TYPES,
    calculate_material_consumption,
)

FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Helvetica"
BG_MAIN = "#F1F5F9"
BG_CARD = "#FFFFFF"
BORDER_COLOR = "#CBD5E1"
ACCENT_BLUE = "#0284C7"
TEXT_PRIMARY = "#0F172A"
TEXT_SECONDARY = "#475569"
ERROR_RED = "#DC2626"
SUCCESS_GREEN = "#16A34A"


class MaterialCalculatorWindow(tk.Toplevel):
    """Окно калькулятора потребности материалов для производственного заказа."""

    def __init__(self, parent: Optional[tk.Tk] = None) -> None:
        super().__init__(parent)
        self.title("CRM: Калькулятор расхода сырья")
        self.geometry("580x640")
        self.minsize(520, 560)
        self.configure(bg=BG_MAIN)

        self._build_ui()

    def _build_ui(self) -> None:
        """Построение формы ввода параметров калькулятора."""
        container = tk.Frame(self, bg=BG_MAIN, padx=24, pady=20)
        container.pack(fill="both", expand=True)

        # Шапка формы
        tk.Label(
            container,
            text="Калькулятор расхода материалов",
            font=(FONT_FAMILY, 15, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_MAIN,
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            container,
            text="Расчет необходимого сырья с учетом типа продукции и процента брака",
            font=(FONT_FAMILY, 10),
            fg=TEXT_SECONDARY,
            bg=BG_MAIN,
        ).pack(anchor="w", pady=(0, 16))

        # Карточка ввода параметров
        card = tk.Frame(container, bg=BG_CARD, padx=20, pady=20, highlightbackground=BORDER_COLOR, highlightthickness=1)
        card.pack(fill="both", expand=True)
        card.columnconfigure(1, weight=1)

        # 1. Тип продукции
        tk.Label(card, text="Тип продукции:", font=(FONT_FAMILY, 10, "bold"), fg=TEXT_PRIMARY, bg=BG_CARD).grid(row=0, column=0, sticky="w", pady=8)
        self.product_type_map = {
            "Тип 1 (Ламинат, k = 1.10)": 1,
            "Тип 2 (Паркетная доска, k = 2.50)": 2,
            "Тип 3 (Массивная доска, k = 8.43)": 3,
            "Тип 4 (Пробковое покрытие, k = 1.50)": 4,
            "Несуществующий тип 99 (Тест ошибки)": 99,
        }
        self.combo_product = ttk.Combobox(card, values=list(self.product_type_map.keys()), state="readonly", font=(FONT_FAMILY, 10))
        self.combo_product.current(0)
        self.combo_product.grid(row=0, column=1, sticky="ew", pady=8, padx=(10, 0))

        # 2. Тип материала
        tk.Label(card, text="Тип материала (сырья):", font=(FONT_FAMILY, 10, "bold"), fg=TEXT_PRIMARY, bg=BG_CARD).grid(row=1, column=0, sticky="w", pady=8)
        self.material_type_map = {
            "Материал 1 (0.10% брака)": 1,
            "Материал 2 (0.95% брака)": 2,
            "Материал 3 (0.28% брака)": 3,
            "Материал 4 (0.55% брака)": 4,
            "Материал 5 (0.34% брака)": 5,
            "Несуществующий материал 88 (Тест ошибки)": 88,
        }
        self.combo_material = ttk.Combobox(card, values=list(self.material_type_map.keys()), state="readonly", font=(FONT_FAMILY, 10))
        self.combo_material.current(0)
        self.combo_material.grid(row=1, column=1, sticky="ew", pady=8, padx=(10, 0))

        # 3. Количество продукции
        tk.Label(card, text="Количество продукции (шт.):", font=(FONT_FAMILY, 10, "bold"), fg=TEXT_PRIMARY, bg=BG_CARD).grid(row=2, column=0, sticky="w", pady=8)
        self.entry_quantity = tk.Entry(card, font=(FONT_FAMILY, 10), relief="flat", highlightbackground=BORDER_COLOR, highlightthickness=1)
        self.entry_quantity.insert(0, "100")
        self.entry_quantity.grid(row=2, column=1, sticky="ew", pady=8, padx=(10, 0))

        # 4. Параметр 1
        tk.Label(card, text="Параметр 1 (длина/ширина):", font=(FONT_FAMILY, 10, "bold"), fg=TEXT_PRIMARY, bg=BG_CARD).grid(row=3, column=0, sticky="w", pady=8)
        self.entry_p1 = tk.Entry(card, font=(FONT_FAMILY, 10), relief="flat", highlightbackground=BORDER_COLOR, highlightthickness=1)
        self.entry_p1.insert(0, "1.5")
        self.entry_p1.grid(row=3, column=1, sticky="ew", pady=8, padx=(10, 0))

        # 5. Параметр 2
        tk.Label(card, text="Параметр 2 (толщина/высота):", font=(FONT_FAMILY, 10, "bold"), fg=TEXT_PRIMARY, bg=BG_CARD).grid(row=4, column=0, sticky="w", pady=8)
        self.entry_p2 = tk.Entry(card, font=(FONT_FAMILY, 10), relief="flat", highlightbackground=BORDER_COLOR, highlightthickness=1)
        self.entry_p2.insert(0, "2.0")
        self.entry_p2.grid(row=4, column=1, sticky="ew", pady=8, padx=(10, 0))

        # Кнопка расчета
        btn_calc = tk.Button(
            card,
            text="Рассчитать потребность сырья",
            font=(FONT_FAMILY, 10, "bold"),
            bg=ACCENT_BLUE,
            fg="#FFFFFF",
            padx=16,
            pady=8,
            relief="flat",
            cursor="hand2",
            command=self.perform_calculation,
        )
        btn_calc.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(16, 8))

        # Блок отображения результата на форме (ТЗ пункт 1)
        self.result_frame = tk.Frame(card, bg="#F8FAFC", padx=16, pady=14, highlightbackground=BORDER_COLOR, highlightthickness=1)
        self.result_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        self.lbl_result_title = tk.Label(
            self.result_frame,
            text="Результат расчета:",
            font=(FONT_FAMILY, 10),
            fg=TEXT_SECONDARY,
            bg="#F8FAFC",
        )
        self.lbl_result_title.pack(anchor="w")

        self.lbl_result_value = tk.Label(
            self.result_frame,
            text="Нажмите кнопку для расчета",
            font=(FONT_FAMILY, 16, "bold"),
            fg=TEXT_PRIMARY,
            bg="#F8FAFC",
        )
        self.lbl_result_value.pack(anchor="w", pady=(4, 0))

    def perform_calculation(self) -> None:
        """Считывание параметров, вызов метода расчета и безопасная обработка -1 (ТЗ пункт 2)."""
        pt_key = self.combo_product.get()
        mt_key = self.combo_material.get()
        product_type_id = self.product_type_map.get(pt_key, -1)
        material_type_id = self.material_type_map.get(mt_key, -1)

        raw_qty = self.entry_quantity.get().strip()
        raw_p1 = self.entry_p1.get().strip()
        raw_p2 = self.entry_p2.get().strip()

        # Безопасное приведение типов
        try:
            quantity = int(raw_qty)
            param_1 = float(raw_p1.replace(",", "."))
            param_2 = float(raw_p2.replace(",", "."))
        except (ValueError, TypeError):
            self._display_error(
                "Ошибка ввода данных",
                "Поля параметров должны содержать положительные числа.\n"
                "Количество продукции должно быть целым числом.\n"
                "Проверьте введенные значения.",
            )
            return

        # Вызов ядра бизнес-логики
        consumption = calculate_material_consumption(
            product_type_id=product_type_id,
            material_type_id=material_type_id,
            quantity=quantity,
            param_1=param_1,
            param_2=param_2,
        )

        # Анализ результата: если возвращено -1, интерфейс не падает (ТЗ пункт 2)
        if consumption == -1:
            self._display_error(
                "Некорректные параметры расчета (Код: -1)",
                "Алгоритм вернул код ошибки -1.\n\n"
                "Возможные причины:\n"
                "1. Передан несуществующий идентификатор типа продукции или материала;\n"
                "2. Указаны неположительные геометрические параметры (param <= 0);\n"
                "3. Указано нулевое или отрицательное количество продукции (quantity <= 0).",
            )
        else:
            self._display_success(consumption)

    def _display_success(self, consumption: int) -> None:
        """Отображение успешного результата на экране формы."""
        self.result_frame.configure(bg="#F0FDF4", highlightbackground=SUCCESS_GREEN)
        self.lbl_result_title.configure(text="Итоговый расход сырья (с учетом брака):", bg="#F0FDF4", fg=SUCCESS_GREEN)
        self.lbl_result_value.configure(
            text=f"{consumption:,} ед. сырья".replace(",", " "),
            fg=SUCCESS_GREEN,
            bg="#F0FDF4",
        )

    def _display_error(self, title: str, message: str) -> None:
        """Отображение состояния ошибки на форме и всплывающего предупреждения."""
        self.result_frame.configure(bg="#FEF2F2", highlightbackground=ERROR_RED)
        self.lbl_result_title.configure(text="Ошибка расчета:", bg="#FEF2F2", fg=ERROR_RED)
        self.lbl_result_value.configure(text="Ошибка: -1 (Неверные данные)", fg=ERROR_RED, bg="#FEF2F2")

        messagebox.showerror(
            title=title,
            message=message,
            icon="error",
            parent=self,
        )


def main() -> None:
    root = tk.Tk()
    root.withdraw()
    app = MaterialCalculatorWindow(root)
    app.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()
