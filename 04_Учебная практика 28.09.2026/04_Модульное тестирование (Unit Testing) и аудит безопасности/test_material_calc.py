"""Модульное тестирование алгоритма расчета материалов (Unit Testing по ТЗ).

Реализует обязательные тест-кейсы:
- Тест 1 (Стандартный): Проверка обычного корректного расчета с известным результатом;
- Тест 2 (Округление): Проверка, что дробный результат округляется строго в большую сторону (ceil);
- Тест 3 (Несуществующий тип): Возврат -1 при некорректных ID типов продукции/материала;
- Тест 4 (Отрицательные параметры): Возврат -1 при отрицательных размерах изделий;
- Тест 5 (Нулевое количество): Возврат -1 при объеме продукции <= 0.
"""

import os
import sys
import unittest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TASK_02_DIR = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "02_Разработка ядра алгоритма расчета материалов")
)

for p in [CURRENT_DIR, TASK_02_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from logger import app_logger
from material_calc import calculate_material_consumption


class TestMaterialCalculationUnits(unittest.TestCase):
    """Набор модульных тестов алгоритма расчета материалов (ТЗ пункт 1)."""

    def test_01_standard_calculation(self) -> None:
        """Тест 1 (Стандартный): Корректный расчет с известным эталонным значением.

        Вход:
            product_type_id = 1 (коэффициент 1.10)
            material_type_id = 1 (процент брака 0.10%)
            quantity = 100 шт.
            param_1 = 1.5
            param_2 = 2.0

        Расчет:
            базовый_расход_на_ед = 1.5 * 2.0 * 1.10 = 3.3
            общий_чистый = 3.3 * 100 = 330.0
            с_браком = 330.0 * (1 + 0.10 / 100) = 330.0 * 1.0010 = 330.33
            округление_ceil = 331
        """
        app_logger.info("Запуск Теста 1: Стандартный расчет")
        result = calculate_material_consumption(
            product_type_id=1,
            material_type_id=1,
            quantity=100,
            param_1=1.5,
            param_2=2.0,
        )
        self.assertEqual(result, 331)

    def test_02_rounding_strictly_up(self) -> None:
        """Тест 2 (Округление): Дробный результат округляется строго вверх (ceil).

        Вход:
            product_type_id = 2 (коэффициент 2.50)
            material_type_id = 2 (процент брака 0.95%)
            quantity = 7 шт.
            param_1 = 1.1
            param_2 = 1.1

        Расчет:
            базовый = 1.1 * 1.1 * 2.50 = 3.025
            общий_чистый = 3.025 * 7 = 21.175
            с_браком = 21.175 * 1.0095 = 21.3761625
            ceil(21.3761625) = 22 (при стандартном round было бы 21)
        """
        app_logger.info("Запуск Теста 2: Проверка округления strictly ceil")
        result = calculate_material_consumption(
            product_type_id=2,
            material_type_id=2,
            quantity=7,
            param_1=1.1,
            param_2=1.1,
        )
        self.assertEqual(result, 22)

    def test_03_nonexistent_types_return_minus_one(self) -> None:
        """Тест 3 (Несуществующий тип): Возврат -1 при некорректных ID справочников.

        Проверяются:
        - Несуществующий тип продукции (ID = 999);
        - Несуществующий тип материала (ID = 888);
        - Отрицательные ID типов (-1).
        """
        app_logger.info("Запуск Теста 3: Проверка несуществующих типов продукции и материала")
        # Несуществующий тип продукции
        res_bad_product = calculate_material_consumption(
            product_type_id=999,
            material_type_id=1,
            quantity=50,
            param_1=1.0,
            param_2=1.0,
        )
        self.assertEqual(res_bad_product, -1)

        # Несуществующий тип материала
        res_bad_material = calculate_material_consumption(
            product_type_id=1,
            material_type_id=888,
            quantity=50,
            param_1=1.0,
            param_2=1.0,
        )
        self.assertEqual(res_bad_material, -1)

        # Отрицательные ID
        res_neg_id = calculate_material_consumption(
            product_type_id=-1,
            material_type_id=-2,
            quantity=10,
            param_1=1.0,
            param_2=1.0,
        )
        self.assertEqual(res_neg_id, -1)

    def test_04_negative_parameters_return_minus_one(self) -> None:
        """Тест 4 (Отрицательные параметры): Возврат -1 при неположительных размерах.

        Проверяются:
        - param_1 < 0;
        - param_2 < 0;
        - param_1 == 0;
        - param_2 == 0.
        """
        app_logger.info("Запуск Теста 4: Проверка отрицательных и нулевых геометрических параметров")
        # Отрицательный param_1
        self.assertEqual(
            calculate_material_consumption(1, 1, 10, -1.5, 2.0),
            -1,
        )
        # Отрицательный param_2
        self.assertEqual(
            calculate_material_consumption(1, 1, 10, 1.5, -2.0),
            -1,
        )
        # Нулевой param_1
        self.assertEqual(
            calculate_material_consumption(1, 1, 10, 0.0, 2.0),
            -1,
        )
        # Нулевой param_2
        self.assertEqual(
            calculate_material_consumption(1, 1, 10, 1.5, 0.0),
            -1,
        )

    def test_05_zero_or_negative_quantity_return_minus_one(self) -> None:
        """Тест 5 (Нулевое количество): Возврат -1 при объеме выпуска <= 0.

        Проверяются:
        - quantity == 0;
        - quantity < 0.
        """
        app_logger.info("Запуск Теста 5: Проверка нулевого и отрицательного количества продукции")
        # Количество равно нулю
        res_zero = calculate_material_consumption(
            product_type_id=1,
            material_type_id=1,
            quantity=0,
            param_1=1.5,
            param_2=2.0,
        )
        self.assertEqual(res_zero, -1)

        # Отрицательное количество
        res_negative = calculate_material_consumption(
            product_type_id=1,
            material_type_id=1,
            quantity=-25,
            param_1=1.5,
            param_2=2.0,
        )
        self.assertEqual(res_negative, -1)


if __name__ == "__main__":
    unittest.main()
