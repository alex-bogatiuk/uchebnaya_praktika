"""Модуль unit-тестирования расчета скидки партнера.

Проверяет 100% логических ветвей и граничные условия из ТЗ:
- 0, 9999 (0%)
- 10000, 49999 (5%)
- 50000, 299999 (10%)
- 300000, 1000000 (15%)
- Отрицательные значения и некорректные типы данных.
"""

import unittest
from discount import calculate_partner_discount


class TestCalculatePartnerDiscount(unittest.TestCase):
    """Набор тестов для функции calculate_partner_discount."""

    def test_zero_sales(self) -> None:
        """Проверка при нулевом объеме продаж (0 ед.)."""
        self.assertEqual(calculate_partner_discount(0), 0)

    def test_boundary_below_10000(self) -> None:
        """Пограничное значение 9 999 ед. должно давать 0% скидки."""
        self.assertEqual(calculate_partner_discount(9999), 0)

    def test_boundary_exact_10000(self) -> None:
        """Пограничное значение 10 000 ед. должно давать 5% скидки."""
        self.assertEqual(calculate_partner_discount(10000), 5)

    def test_within_tier_5_percent(self) -> None:
        """Промежуточное значение диапазона 10 000 - 49 999 ед. (25 000 ед.)."""
        self.assertEqual(calculate_partner_discount(25000), 5)

    def test_boundary_exact_49999(self) -> None:
        """Пограничное значение 49 999 ед. должно давать 5% скидки."""
        self.assertEqual(calculate_partner_discount(49999), 5)

    def test_boundary_exact_50000(self) -> None:
        """Пограничное значение 50 000 ед. должно давать 10% скидки."""
        self.assertEqual(calculate_partner_discount(50000), 10)

    def test_within_tier_10_percent(self) -> None:
        """Промежуточное значение диапазона 50 000 - 299 999 ед. (150 000 ед.)."""
        self.assertEqual(calculate_partner_discount(150000), 10)

    def test_boundary_exact_299999(self) -> None:
        """Пограничное значение 299 999 ед. должно давать 10% скидки."""
        self.assertEqual(calculate_partner_discount(299999), 10)

    def test_boundary_exact_300000(self) -> None:
        """Пограничное значение 300 000 ед. должно давать 15% скидки."""
        self.assertEqual(calculate_partner_discount(300000), 15)

    def test_large_volume_above_300000(self) -> None:
        """Значение свыше 300 000 ед. (1 000 000 ед.) должно давать 15% скидки."""
        self.assertEqual(calculate_partner_discount(1000000), 15)

    def test_negative_quantity_raises_value_error(self) -> None:
        """Отрицательное количество должно вызывать исключение ValueError."""
        with self.assertRaises(ValueError):
            calculate_partner_discount(-1)

        with self.assertRaises(ValueError):
            calculate_partner_discount(-10000)

    def test_invalid_types_raise_type_error(self) -> None:
        """Некорректные типы (float, str, None, bool) должны вызывать TypeError."""
        with self.assertRaises(TypeError):
            calculate_partner_discount("10000")  # type: ignore

        with self.assertRaises(TypeError):
            calculate_partner_discount(10000.5)  # type: ignore

        with self.assertRaises(TypeError):
            calculate_partner_discount(None)  # type: ignore

        with self.assertRaises(TypeError):
            calculate_partner_discount(True)  # type: ignore


if __name__ == "__main__":
    unittest.main(verbosity=2)
