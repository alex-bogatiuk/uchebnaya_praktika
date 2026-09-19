"""Главный исполняемый файл приложения CRM (Финал сборки практики 14.09.2026).

Связывает воедино:
- Модуль 01: Ядро бизнес-логики расчета скидок (calculate_partner_discount);
- Модуль 02: Реляционную базу данных и агрегацию продаж (DatabaseManager);
- Модуль 03: Графический интерфейс по руководству по стилю (PartnersWindow / Web UI).

Поддерживает режимы запуска:
- Без аргументов: Запуск нативного десктопного GUI окна (Tkinter);
- С флагом --cli: Консольный вывод актуального списка партнеров со скидками;
- С флагом --web: Запуск локального веб-сервера и браузерного интерфейса;
- С флагом --test: Запуск стресс-теста отказоустойчивости и отладки.
"""

import argparse
import os
import sys

# Настройка путей к модулям практики
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_01_DIR = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "01_Разработка ядра бизнес-логики (Расчет скидки)")
)
MODULE_02_DIR = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "02_Интеграция с БД и агрегация данных (SQL + Backend)")
)
MODULE_03_DIR = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "03_Разработка интерфейса (UI) по руководству по стилю")
)

for path in [MODULE_01_DIR, MODULE_02_DIR, MODULE_03_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

from database import DatabaseManager
from ui_desktop import PartnersWindow


def run_cli_view() -> None:
    """Вывод актуального списка партнеров со скидками в терминал."""
    db = DatabaseManager()
    partners = db.get_all_partners_with_discounts()

    print("\n" + "=" * 95)
    print("CRM: СПИСОК ПАРТНЕРОВ, КОНТАКТОВ И НАКОПИТЕЛЬНЫХ СКИДОК")
    print("=" * 95)
    header = f"{'ID':<4} | {'Тип | Наименование':<32} | {'Директор':<26} | {'Телефон':<18} | {'Объем':<8} | {'Скидка':<6}"
    print(header)
    print("-" * 95)

    for p in partners:
        title = f"{p['partner_type']} | {p['clean_name']}"
        director = p['director'].replace("Директор: ", "")[:25]
        row = (
            f"{p['partner_id']:<4} | "
            f"{title:<32} | "
            f"{director:<26} | "
            f"{p['phone']:<18} | "
            f"{p['total_quantity']:<8} | "
            f"{p['discount_percent']:>4}%"
        )
        print(row)

    print("=" * 95)
    print(f"Всего партнеров в базе данных: {len(partners)}")
    print("=" * 95 + "\n")


def run_web_server() -> None:
    """Запуск веб-версии приложения."""
    web_dir = os.path.join(MODULE_03_DIR, "web")
    sys.path.insert(0, web_dir)
    from server import run_server
    run_server()


def run_gui() -> None:
    """Запуск десктопного интерфейса."""
    db = DatabaseManager()
    app = PartnersWindow(db_manager=db)
    print("Запуск графического интерфейса 'CRM: Список партнеров и скидок'...")
    app.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CRM: Информационная система управления партнерами и скидками"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Запустить вывод списка партнеров в консольном режиме",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Запустить локальный веб-сервер с веб-интерфейсом",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Запустить стресс-тест отказоустойчивости",
    )

    args = parser.parse_args()

    if args.cli:
        run_cli_view()
    elif args.web:
        run_web_server()
    elif args.test:
        from stress_test import run_all_stress_tests
        success = run_all_stress_tests()
        sys.exit(0 if success else 1)
    else:
        run_gui()


if __name__ == "__main__":
    main()
