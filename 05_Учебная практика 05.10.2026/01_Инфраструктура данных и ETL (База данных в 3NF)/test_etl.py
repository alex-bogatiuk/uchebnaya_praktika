"""Модульные тесты ETL-конвейера и схемы базы данных 3NF (Задание 1, 05.10.2026)."""

import os
import sqlite3
import sys
import unittest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from etl import DB_PATH, parse_date_to_iso, run_etl, split_type_and_name


class TestDataInfrastructureAndETL(unittest.TestCase):
    """Тестирование нормализации 3NF, очистки данных и ссылочной целостности."""

    def test_date_normalization(self) -> None:
        """Проверка приведения дат к стандарту ГГГГ-ММ-ДД."""
        self.assertEqual(parse_date_to_iso("15.03.2026"), "2026-03-15")
        self.assertEqual(parse_date_to_iso("2026-04-01"), "2026-04-01")
        self.assertEqual(parse_date_to_iso("01.12.2025"), "2025-12-01")
        self.assertIsNone(parse_date_to_iso("invalid-date"))

    def test_trim_and_type_splitting(self) -> None:
        """Проверка удаления пробелов и отделения ОПФ."""
        p_type, name = split_type_and_name('  ООО "Логистик-Экспресс"  ')
        self.assertEqual(p_type, "ООО")
        self.assertEqual(name, "Логистик-Экспресс")

    def test_etl_execution_and_foreign_keys(self) -> None:
        """Проверка запуска ETL и отсутствия битых внешних ключей."""
        stats = run_etl()
        self.assertEqual(stats["rejected_count"], 1)  # Запись 104 отфильтрована
        self.assertGreater(stats["sales_count"], 0)

        # Проверяем базу данных
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Проверяем, что в sales_history нет записей с partner_id=4
        cur.execute("SELECT COUNT(*) FROM sales_history WHERE partner_id = 4;")
        self.assertEqual(cur.fetchone()[0], 0)

        # Проверяем все даты в sales_history (должны быть в формате YYYY-MM-DD)
        cur.execute("SELECT sale_date FROM sales_history;")
        dates = [row[0] for row in cur.fetchall()]
        for d in dates:
            self.assertRegex(d, r"^\d{4}-\d{2}-\d{2}$")

        conn.close()


if __name__ == "__main__":
    unittest.main()
