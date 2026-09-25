"""Главная точка входа информационной системы CRM (Финал практики 05.10.2026).

Связывает воедино все модули практики:
1. Инфраструктуру данных 3NF (schema.sql, etl.py);
2. Ядро бизнес-логики (скидки и расчет расхода сырья);
3. Графический интерфейс, многооконную навигацию и синхронизацию с СУБД;
4. Автоматизированное тестирование, аудит безопасности и обработку исключений.

Режимы запуска:
    python main.py          - Запуск графического интерфейса (GUI)
    python main.py --cli    - Консольный просмотр реестра партнеров
    python main.py --calc   - Быстрый запуск калькулятора материалов
    python main.py --test   - Запуск модульного тестирования
    python main.py --audit  - Запуск аудита безопасности на SQL-инъекции
"""

import argparse
import os
import sqlite3
import sys
import unittest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TASK_01_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "01_Инфраструктура данных и ETL (База данных в 3NF)"))
TASK_02_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "02_Реализация ядра бизнес-логики (Расчеты и алгоритмы)"))
TASK_03_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "03_Разработка UI, навигации и CRUD-форм"))

for p in [CURRENT_DIR, TASK_01_DIR, TASK_02_DIR, TASK_03_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app_ui import DB_PATH, MainWindow
from business_logic import calculate_material_consumption, calculate_partner_discount
from security_audit import audit_dynamic_sql_protection, audit_sql_parameterization, log_event


def run_cli_view() -> None:
    """Вывод актуального реестра партнеров со скидками в терминал."""
    if not os.path.exists(DB_PATH):
        print(f"Ошибка: база данных не найдена по пути {DB_PATH}. Сначала выполните etl.py")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    query = """
        SELECT
            p.partner_id,
            p.company_name,
            p.partner_type,
            p.director,
            p.phone,
            p.contact_email,
            p.rating,
            COALESCE(SUM(s.quantity), 0) AS total_quantity
        FROM partners AS p
        LEFT JOIN sales_history AS s ON p.partner_id = s.partner_id
        GROUP BY p.partner_id
        ORDER BY p.partner_id ASC;
    """
    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    print("\n" + "=" * 95)
    print("CRM: РЕЕСТР ПАРТНЕРОВ, КОНТАКТОВ И НАКОПИТЕЛЬНЫХ СКИДОК")
    print("=" * 95)
    print(f"{'ID':<4} | {'ОПФ | Наименование':<30} | {'Директор':<24} | {'Телефон':<18} | {'Объем':<8} | {'Скидка'}")
    print("-" * 95)

    for r in rows:
        title = f"{r['partner_type']} {r['company_name']}"
        director = (r['director'] or '-')[:23]
        qty = int(r["total_quantity"])
        discount = calculate_partner_discount(qty)
        phone = r['phone'] or '-'
        print(f"{r['partner_id']:<4} | {title:<30} | {director:<24} | {phone:<18} | {qty:<8} | {discount:>4}%")

    print("=" * 95)
    print(f"Всего партнеров в базе данных: {len(rows)}\n")


def run_tests() -> None:
    """Запуск комплекса модульных тестов."""
    import test_suite
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_suite)
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)


def run_audit() -> None:
    """Запуск аудита безопасности."""
    from security_audit import main as audit_main
    audit_main()


def run_calc() -> None:
    """Запуск независимого калькулятора материалов."""
    WEEK_04_CALC_DIR = os.path.abspath(
        os.path.join(CURRENT_DIR, "..", "..", "04_Учебная практика 28.09.2026", "03_Интеграция метода расчета и комплексное тестирование")
    )
    if WEEK_04_CALC_DIR not in sys.path:
        sys.path.insert(0, WEEK_04_CALC_DIR)
    from calculator_window import MaterialCalculatorWindow
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    calc = MaterialCalculatorWindow(root)
    calc.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(description="CRM: Главная точка входа (Практика 05.10.2026)")
    parser.add_argument("--cli", action="store_true", help="Консольный вывод списка партнеров")
    parser.add_argument("--calc", action="store_true", help="Запустить калькулятор расхода сырья")
    parser.add_argument("--test", action="store_true", help="Запустить автоматизированные Unit-тесты")
    parser.add_argument("--audit", action="store_true", help="Запустить аудит безопасности кода")

    args = parser.parse_args()

    if args.cli:
        run_cli_view()
    elif args.calc:
        run_calc()
    elif args.test:
        run_tests()
    elif args.audit:
        run_audit()
    else:
        # Запуск нативного десктопного интерфейса
        log_event("INFO", "Запуск главного графического интерфейса приложения")
        app = MainWindow(db_path=DB_PATH)
        app.mainloop()


if __name__ == "__main__":
    main()
