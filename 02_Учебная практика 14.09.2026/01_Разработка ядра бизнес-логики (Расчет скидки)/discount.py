"""Модуль расчета индивидуального процента скидки партнера.

Реализует изолированную функцию calculate_partner_discount в соответствии
с требованиями технического задания (ТЗ):
- Объем < 10 000 ед.           -> 0%
- Объем от 10 000 до 49 999 ед. -> 5%
- Объем от 50 000 до 299 999 ед. -> 10%
- Объем от 300 000 ед. и более -> 15%

Код оформлен строго по стандарту PEP 8:
- именование в стиле snake_case;
- строгая типизация (type hinting);
- ровно одна команда на строку.
"""


def calculate_partner_discount(total_quantity: int) -> int:
    """Рассчитывает процент скидки партнера на основе суммарного объема продаж.

    Параметры:
        total_quantity (int): Суммарный объем купленной партнером продукции.
                              Должен быть неотрицательным целым числом.

    Возвращает:
        int: Процент скидки (0, 5, 10 или 15).

    Исключения:
        TypeError: Если total_quantity не является целым числом (int).
        ValueError: Если total_quantity меньше нуля.
    """
    if not isinstance(total_quantity, int) or isinstance(total_quantity, bool):
        raise TypeError("Суммарный объем продукции должен быть целым числом (int)")

    if total_quantity < 0:
        raise ValueError("Суммарный объем продукции не может быть отрицательным")

    if total_quantity < 10000:
        return 0

    if total_quantity < 50000:
        return 5

    if total_quantity < 300000:
        return 10

    return 15
