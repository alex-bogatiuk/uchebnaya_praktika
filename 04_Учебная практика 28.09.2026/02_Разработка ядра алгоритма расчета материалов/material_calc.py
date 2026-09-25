"""Ядро бизнес-логики: алгоритм расчета количества необходимых материалов.

Формула расчета:
    Базовый расход на 1 ед. = param_1 * param_2 * Коэффициент типа продукции
    Общий чистый расход = Базовый расход на 1 ед. * quantity
    Итоговый расход с учетом брака = Общий чистый расход * (1 + Процент брака материала / 100)
    Результат = ceil(Итоговый расход с учетом брака)

Правила оформления по ТЗ:
- Строго одна команда на строку;
- snake_case для всех функций и переменных;
- Краткие комментарии только в неочевидных местах алгоритма;
- Возврат -1 при некорректных ID, отрицательных параметрах или количестве <= 0.
"""

import math
import sqlite3
from typing import Any, Dict, Optional, Tuple

# Справочники по умолчанию (для автономной работы и тестирования без БД)
DEFAULT_PRODUCT_TYPES: Dict[int, float] = {
    1: 1.10,
    2: 2.50,
    3: 8.43,
    4: 1.50,
}

DEFAULT_MATERIAL_TYPES: Dict[int, float] = {
    1: 0.10,
    2: 0.95,
    3: 0.28,
    4: 0.55,
    5: 0.34,
}


def get_product_coefficient(product_type_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[float]:
    """Извлекает коэффициент типа продукции из БД или справочника."""
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT coefficient FROM product_types WHERE type_id = ?;", (product_type_id,))
            row = cursor.fetchone()
            if row is not None:
                return float(row[0])
        except Exception:
            pass
    return DEFAULT_PRODUCT_TYPES.get(product_type_id)


def get_material_defect_percent(material_type_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[float]:
    """Извлекает процент брака материала из БД или справочника."""
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT defect_percent FROM material_types WHERE type_id = ?;", (material_type_id,))
            row = cursor.fetchone()
            if row is not None:
                return float(row[0])
        except Exception:
            pass
    return DEFAULT_MATERIAL_TYPES.get(material_type_id)


def calculate_material_consumption(
    product_type_id: int,
    material_type_id: int,
    quantity: int,
    param_1: float,
    param_2: float,
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """Вычисляет необходимое количество сырья для производства продукции.

    Параметры:
        product_type_id (int): Идентификатор типа продукции.
        material_type_id (int): Идентификатор типа материала.
        quantity (int): Объем выпускаемой продукции (> 0).
        param_1 (float): Первый вещественный габаритный параметр продукции (> 0).
        param_2 (float): Второй вещественный габаритный параметр продукции (> 0).
        conn (Optional[sqlite3.Connection]): Активное соединение с БД.

    Возвращает:
        int: Округленное вверх целое число единиц материала либо -1 при ошибке.
    """
    # Защита от передачи булевых типов (в Python bool является подклассом int)
    if isinstance(quantity, bool) or isinstance(product_type_id, bool) or isinstance(material_type_id, bool):
        return -1

    if not isinstance(quantity, int) or not isinstance(product_type_id, int) or not isinstance(material_type_id, int):
        return -1

    if not isinstance(param_1, (int, float)) or not isinstance(param_2, (int, float)):
        return -1

    if isinstance(param_1, bool) or isinstance(param_2, bool):
        return -1

    # Проверка положительности количества и параметров изделия
    if quantity <= 0:
        return -1

    if param_1 <= 0.0 or param_2 <= 0.0:
        return -1

    # Получение коэффициентов из справочников или таблиц БД
    coefficient = get_product_coefficient(product_type_id, conn)
    if coefficient is None or coefficient <= 0:
        return -1

    defect_percent = get_material_defect_percent(material_type_id, conn)
    if defect_percent is None or defect_percent < 0:
        return -1

    # Расчет чистого расхода без брака
    unit_base = float(param_1) * float(param_2) * float(coefficient)
    total_net = unit_base * float(quantity)

    # Учет технологических потерь (процента брака)
    defect_factor = 1.0 + (float(defect_percent) / 100.0)
    gross_consumption = total_net * defect_factor

    # Математическое округление строго в большую сторону (по ТЗ ceil)
    result = math.ceil(gross_consumption)
    return int(result)
