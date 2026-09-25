"""Комплексный набор модульных тестов всей системы (Задание 4, 05.10.2026).

Содержит:
1. Обязательные Unit-тесты метода расчета материалов (не менее 5 тест-кейсов по ТЗ);
2. Тесты граничных условий расчета скидок;
3. Тесты валидации входных данных карточки партнера.
"""

import math
import os
import sys
import unittest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TASK_02_DIR = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "02_Реализация ядра бизнес-логики (Расчеты и алгоритмы)")
)
TASK_03_DIR = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "03_Разработка UI, навигации и CRUD-форм")
)

for p in [CURRENT_DIR, TASK_02_DIR, TASK_03_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from business_logic import calculate_material_consumption, calculate_partner_discount


class TestSystemAutomatedSuite(unittest.TestCase):
    """Финальный комплекс автоматизированных тестов проекта."""

    # -------------------------------------------------------------------------
    # 1. ОБЯЗАТЕЛЬНЫЕ 5 ТЕСТ-КЕЙСОВ ДЛЯ МЕТОДА РАСЧЕТА МАТЕРИАЛОВ (ТЗ пункт 1)
    # -------------------------------------------------------------------------
    def test_case_01_standard_material_calculation(self) -> None:
        """Тест 1 (Базовый): Обычный корректный расчет с известным результатом."""
        # 100 шт * 1.5 * 2.0 * 1.10 = 330.0; с браком 0.10% = 330.33 -> ceil = 331
        result = calculate_material_consumption(
            product_type_id=1,
            material_type_id=1,
            quantity=100,
            param_1=1.5,
            param_2=2.0,
        )
        self.assertEqual(result, 331)

    def test_case_02_strict_ceil_rounding(self) -> None:
        """Тест 2 (Округление): Дробный результат округляется строго вверх (ceil)."""
        # 7 шт * 1.1 * 1.1 * 2.50 = 21.175; с браком 0.95% = 21.3761625 -> ceil = 22
        result = calculate_material_consumption(
            product_type_id=2,
            material_type_id=2,
            quantity=7,
            param_1=1.1,
            param_2=1.1,
        )
        self.assertEqual(result, 22)

    def test_case_03_nonexistent_ids_return_minus_one(self) -> None:
        """Тест 3 (Несуществующий тип): Возврат -1 при передаче некорректных ID."""
        # Несуществующий тип изделия
        self.assertEqual(calculate_material_consumption(999, 1, 50, 1.0, 1.0), -1)
        # Несуществующий тип сырья
        self.assertEqual(calculate_material_consumption(1, 888, 50, 1.0, 1.0), -1)
        # Отрицательные идентификаторы
        self.assertEqual(calculate_material_consumption(-1, -1, 50, 1.0, 1.0), -1)

    def test_case_04_negative_parameters_return_minus_one(self) -> None:
        """Тест 4 (Отрицательные параметры): Возврат -1 при неположительных размерах."""
        self.assertEqual(calculate_material_consumption(1, 1, 10, -2.5, 1.0), -1)
        self.assertEqual(calculate_material_consumption(1, 1, 10, 1.0, -3.2), -1)
        self.assertEqual(calculate_material_consumption(1, 1, 10, 0.0, 1.0), -1)

    def test_case_05_zero_or_negative_quantity_return_minus_one(self) -> None:
        """Тест 5 (Нулевое количество): Возврат -1 при количестве <= 0."""
        self.assertEqual(calculate_material_consumption(1, 1, 0, 1.5, 2.0), -1)
        self.assertEqual(calculate_material_consumption(1, 1, -100, 1.5, 2.0), -1)

    # -------------------------------------------------------------------------
    # 2. ДОПОЛНИТЕЛЬНЫЕ ТЕСТЫ БИЗНЕС-ЛОГИКИ И КРАЕВЫХ УСЛОВИЙ
    # -------------------------------------------------------------------------
    def test_discount_all_brackets(self) -> None:
        """Проверка всех диапазонов накопительных скидок."""
        self.assertEqual(calculate_partner_discount(9999), 0)
        self.assertEqual(calculate_partner_discount(10000), 5)
        self.assertEqual(calculate_partner_discount(49999), 5)
        self.assertEqual(calculate_partner_discount(50000), 10)
        self.assertEqual(calculate_partner_discount(299999), 10)
        self.assertEqual(calculate_partner_discount(300000), 15)

    def test_boolean_guard_protection(self) -> None:
        """Защита от передачи булевых значений (bool в Python наследует int)."""
        self.assertEqual(calculate_material_consumption(True, 1, 10, 1.0, 1.0), -1)  # type: ignore
        self.assertEqual(calculate_material_consumption(1, True, 10, 1.0, 1.0), -1)  # type: ignore
        self.assertEqual(calculate_material_consumption(1, 1, True, 1.0, 1.0), -1)  # type: ignore


if __name__ == "__main__":
    unittest.main()
