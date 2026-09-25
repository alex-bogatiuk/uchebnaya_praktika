"""Интерактивная консольная демонстрация методов бизнес-логики."""

from business_logic import calculate_material_consumption, calculate_partner_discount


def main() -> None:
    print("=" * 80)
    print("БЭКЕНД-МОДУЛЬ БИЗНЕС-ЛОГИКИ: РАСЧЕТ СКИДОК И СЫРЬЯ")
    print("=" * 80)

    print("\n1. Проверка алгоритма накопительных скидок партнеров:")
    test_volumes = [0, 8500, 10000, 25000, 50000, 120000, 300000, 550000]
    for vol in test_volumes:
        disc = calculate_partner_discount(vol)
        print(f"  Объем продаж: {vol:>7,} шт. -> Индивидуальная скидка: {disc:>2}%".replace(",", " "))

    print("\n2. Проверка алгоритма расчета сырья (материалов):")
    calc_samples = [
        ("Ламинат (тип 1, мат 1, 100 шт, 1.5 x 2.0)", 1, 1, 100, 1.5, 2.0),
        ("Паркет (тип 2, мат 2, 7 шт, 1.1 x 1.1, ceil)", 2, 2, 7, 1.1, 1.1),
        ("Несуществующий тип продукции (тип 999)", 999, 1, 10, 1.0, 1.0),
        ("Отрицательный параметр размера (-1.5)", 1, 1, 10, -1.5, 2.0),
        ("Нулевой объем продукции (0 шт)", 1, 1, 0, 1.0, 1.0),
    ]
    for desc, pt, mt, qty, p1, p2 in calc_samples:
        ans = calculate_material_consumption(pt, mt, qty, p1, p2)
        res_str = f"{ans} ед." if ans != -1 else "-1 (Некорректные параметры)"
        print(f"  {desc} -> {res_str}")

    print("=" * 80)


if __name__ == "__main__":
    main()
