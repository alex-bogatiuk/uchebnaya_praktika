"""Ядро бизнес-логики CRM: расчет накопительных скидок и потребности сырья.

Реализует две независимые чистые функции:
1. calculate_partner_discount: расчет индивидуальной скидки партнера;
2. calculate_material_consumption: расчет необходимого объема сырья с учетом брака.

Строго соблюдается правило ТЗ:
- Одна команда на строку;
- snake_case для всех идентификаторов;
- Возврат -1 вместо падения программы при некорректных входных параметрах.
"""

import math
import os
import sqlite3
from typing import Optional, Tuple

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TASK_01_DIR = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "01_Инфраструктура данных и ETL (База данных в 3NF)")
)
DEFAULT_DB_PATH = os.path.join(TASK_01_DIR, "partners.db")

# Автономные справочные коэффициенты
FALLBACK_PRODUCT_COEFFICIENTS = {
    1: 1.10,
    2: 2.50,
    3: 8.43,
    4: 1.50,
}

FALLBACK_MATERIAL_DEFECTS = {
    1: 0.10,
    2: 0.95,
    3: 0.28,
    4: 0.55,
    5: 0.34,
}


def calculate_partner_discount(total_quantity: int) -> int:
    """Вычисляет процент накопительной скидки партнера на основе суммарного объема продаж.

    Правило по ТЗ:
    - < 10 000 шт.        -> 0%
    - 10 000 - 49 999 шт. -> 5%
    - 50 000 - 299 999 шт.-> 10%
    - >= 300 000 шт.      -> 15%

    Параметры:
        total_quantity (int): Суммарный объем реализованной продукции.

    Возвращает:
        int: Процент скидки (0, 5, 10 или 15).
    """
    if isinstance(total_quantity, bool):
        raise TypeError("Суммарный объем не может быть булевым типом")

    if not isinstance(total_quantity, int):
        raise TypeError("Суммарный объем должен быть целым числом")

    if total_quantity < 0:
        raise ValueError("Суммарный объем не может быть отрицательным числом")

    if total_quantity < 10000:
        return 0

    if total_quantity < 50000:
        return 5

    if total_quantity < 300000:
        return 10

    return 15


def get_product_coefficient_from_db(product_type_id: int, db_path: str) -> Optional[float]:
    """Извлекает коэффициент типа продукции из базы данных."""
    if not os.path.exists(db_path):
        return FALLBACK_PRODUCT_COEFFICIENTS.get(product_type_id)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT coefficient FROM product_types WHERE type_id = ?;", (product_type_id,))
        row = cursor.fetchone()
        conn.close()
        if row is not None:
            return float(row[0])
    except Exception:
        pass

    return FALLBACK_PRODUCT_COEFFICIENTS.get(product_type_id)


def get_material_defect_from_db(material_type_id: int, db_path: str) -> Optional[float]:
    """Извлекает процент брака материала из базы данных."""
    if not os.path.exists(db_path):
        return FALLBACK_MATERIAL_DEFECTS.get(material_type_id)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT defect_percent FROM material_types WHERE type_id = ?;", (material_type_id,))
        row = cursor.fetchone()
        conn.close()
        if row is not None:
            return float(row[0])
    except Exception:
        pass

    return FALLBACK_MATERIAL_DEFECTS.get(material_type_id)


def calculate_material_consumption(
    product_type_id: int,
    material_type_id: int,
    quantity: int,
    param_1: float,
    param_2: float,
    db_path: str = DEFAULT_DB_PATH,
) -> int:
    """Вычисляет количество сырья для производства готовой продукции с учетом брака.

    Формула:
        Расход = ceil(Количество * param_1 * param_2 * Коэффициент * (1 + Процент брака / 100))

    Возвращает:
        int: Итоговый расход сырья либо -1 при некорректных входных данных.
    """
    # Защита от передачи булевых типов (в Python bool является подклассом int)
    if isinstance(quantity, bool) or isinstance(product_type_id, bool) or isinstance(material_type_id, bool):
        return -1

    if isinstance(param_1, bool) or isinstance(param_2, bool):
        return -1

    if not isinstance(quantity, int) or not isinstance(product_type_id, int) or not isinstance(material_type_id, int):
        return -1

    if not isinstance(param_1, (int, float)) or not isinstance(param_2, (int, float)):
        return -1

    # Проверка положительности количества и параметров
    if quantity <= 0:
        return -1

    if param_1 <= 0.0 or param_2 <= 0.0:
        return -1

    # Запрос справочников из БД
    coeff = get_product_coefficient_from_db(product_type_id, db_path)
    if coeff is None or coeff <= 0:
        return -1

    defect = get_material_defect_from_db(material_type_id, db_path)
    if defect is None or defect < 0:
        return -1

    # Расчет расхода
    unit_base = float(param_1) * float(param_2) * float(coeff)
    total_net = unit_base * float(quantity)
    total_with_defect = total_net * (1.0 + (float(defect) / 100.0))

    # Округление строго в большую сторону
    result_ceil = math.ceil(total_with_defect)
    return int(result_ceil)
