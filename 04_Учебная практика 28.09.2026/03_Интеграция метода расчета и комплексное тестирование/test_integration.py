"""Интеграционные тесты калькулятора расчета материалов (Задание 3, 28.09.2026)."""

import os
import sys
import unittest
import tkinter as tk

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from unittest.mock import patch
from calculator_window import MaterialCalculatorWindow


class TestCalculatorIntegration(unittest.TestCase):
    """Тестирование интеграции алгоритма расчета с графическим интерфейсом."""

    def setUp(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.patcher = patch("tkinter.messagebox.showerror")
        self.mock_error = self.patcher.start()
        self.calc = MaterialCalculatorWindow(self.root)

    def tearDown(self) -> None:
        self.patcher.stop()
        self.calc.destroy()
        self.root.destroy()

    def test_calculator_window_title(self) -> None:
        """Проверка заголовка окна калькулятора."""
        self.assertEqual(self.calc.title(), "CRM: Калькулятор расхода сырья")

    def test_successful_calculation_display(self) -> None:
        """Проверка отображения успешного расчета на экране формы."""
        self.calc.combo_product.set("Тип 1 (Ламинат, k = 1.10)")
        self.calc.combo_material.set("Материал 1 (0.10% брака)")
        self.calc.entry_quantity.delete(0, tk.END)
        self.calc.entry_quantity.insert(0, "100")
        self.calc.entry_p1.delete(0, tk.END)
        self.calc.entry_p1.insert(0, "1.5")
        self.calc.entry_p2.delete(0, tk.END)
        self.calc.entry_p2.insert(0, "2.0")

        self.calc.perform_calculation()
        result_text = self.calc.lbl_result_value.cget("text")
        self.assertIn("331", result_text)
        self.assertIn("ед. сырья", result_text)

    def test_error_handling_negative_param_no_crash(self) -> None:
        """Проверка безопасной обработки возврата -1 без падения формы."""
        self.calc.entry_p1.delete(0, tk.END)
        self.calc.entry_p1.insert(0, "-1.5")  # Отрицательный параметр

        # Вызываем расчет: форма не должна упасть с исключением
        self.calc.perform_calculation()
        result_text = self.calc.lbl_result_value.cget("text")
        self.assertIn("-1", result_text)
        self.assertTrue(self.calc.winfo_exists())

    def test_error_handling_nonexistent_type_no_crash(self) -> None:
        """Проверка выбора несуществующего типа продукции (ID=99)."""
        self.calc.combo_product.set("Несуществующий тип 99 (Тест ошибки)")
        self.calc.perform_calculation()
        result_text = self.calc.lbl_result_value.cget("text")
        self.assertIn("-1", result_text)
        self.assertTrue(self.calc.winfo_exists())


if __name__ == "__main__":
    unittest.main()
