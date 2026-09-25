"""Модульные тесты ядра бизнес-логики: скидки и расчет сырья (Задание 2, 05.10.2026)."""

import os
import sys
import unittest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from business_logic import calculate_material_consumption, calculate_partner_discount


class TestBusinessLogic(unittest.TestCase):
    """Тестирование обеих функций бизнес-логики бэкенда."""

    # -------------------------------------------------------------
    # 1. Тестирование алгоритма скидок
    # -------------------------------------------------------------
    def test_discount_tiers_boundaries(self) -> None:
        """Проверка всех диапазонов накопительных скидок по ТЗ."""
        # < 10 000 шт. -> 0%
        self.assertEqual(calculate_partner_discount(0), 0)
        self.assertEqual(calculate_partner_discount(5000), 0)
        self.assertEqual(calculate_partner_discount(9999), 0)

        # 10 000 - 49 999 шт. -> 5%
        self.assertEqual(calculate_partner_discount(10000), 5)
        self.assertEqual(calculate_partner_discount(25000), 5)
        self.assertEqual(calculate_partner_discount(49999), 5)

        # 50 000 - 299 999 шт. -> 10%
        self.assertEqual(calculate_partner_discount(50000), 10)
        self.assertEqual(calculate_partner_discount(150000), 10)
        self.assertEqual(calculate_partner_discount(299999), 10)

        # >= 300 000 шт. -> 15%
        self.assertEqual(calculate_partner_discount(300000), 15)
        self.assertEqual(calculate_partner_discount(1000000), 15)

    def test_discount_invalid_inputs(self) -> None:
        """Проверка обработки некорректных типов и отрицательных объемов."""
        with self.assertRaises(ValueError):
            calculate_partner_discount(-1)

        with self.assertRaises(TypeError):
            calculate_partner_discount("10000")  # type: ignore

        with self.assertRaises(TypeError):
            calculate_partner_discount(True)  # type: ignore

    # -------------------------------------------------------------
    # 2. Тестирование алгоритма расчета материалов
    # -------------------------------------------------------------
    def test_material_standard_calculation(self) -> None:
        """Проверка базового расчета: тип 1 (k=1.10), мат 1 (0.10%), 100 шт, 1.5 x 2.0 -> 331."""
        res = calculate_material_consumption(1, 1, 100, 1.5, 2.0)
        self.assertEqual(res, 331)

    def test_material_rounding_strictly_up(self) -> None:
        """Проверка округления строго вверх (ceil)."""
        res = calculate_material_consumption(2, 2, 7, 1.1, 1.1)
        self.assertEqual(res, 22)

    def test_material_invalid_ids_return_minus_one(self) -> None:
        """Проверка возврата -1 при несуществующих ID."""
        self.assertEqual(calculate_material_consumption(999, 1, 10, 1.0, 1.0), -1)
        self.assertEqual(calculate_material_consumption(1, 888, 10, 1.0, 1.0), -1)

    def test_material_negative_params_return_minus_one(self) -> None:
        """Проверка возврата -1 при отрицательных или нулевых габаритах."""
        self.assertEqual(calculate_material_consumption(1, 1, 10, -1.0, 2.0), -1)
        self.assertEqual(calculate_material_consumption(1, 1, 10, 1.0, -2.0), -1)
        self.assertEqual(calculate_material_consumption(1, 1, 10, 0.0, 2.0), -1)

    def test_material_zero_or_negative_quantity_return_minus_one(self) -> None:
        """Проверка возврата -1 при объеме <= 0."""
        self.assertEqual(calculate_material_consumption(1, 1, 0, 1.0, 1.0), -1)
        self.assertEqual(calculate_material_consumption(1, 1, -5, 1.0, 1.0), -1)


if __name__ == "__main__":
    unittest.main()
