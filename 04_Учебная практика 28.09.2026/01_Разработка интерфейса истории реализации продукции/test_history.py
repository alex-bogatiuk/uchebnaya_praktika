"""Модульные тесты интерфейса истории реализации продукции (Задание 1, 28.09.2026)."""

import os
import sqlite3
import sys
import unittest
import tkinter as tk

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from history_window import PartnerHistoryWindow, format_human_date, DEFAULT_DB_PATH


class TestPartnerHistory(unittest.TestCase):
    """Тестирование окна истории отгрузок и форматирования дат."""

    def setUp(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self) -> None:
        self.root.destroy()

    def test_date_formatting_human_readable(self) -> None:
        """Проверка конвертации YYYY-MM-DD в ДД.ММ.ГГГГ."""
        self.assertEqual(format_human_date("2026-03-01"), "01.03.2026")
        self.assertEqual(format_human_date("2026-12-31"), "31.12.2026")
        self.assertEqual(format_human_date("15.03.2026"), "15.03.2026")
        self.assertEqual(format_human_date(""), "-")

    def test_window_title_format(self) -> None:
        """Проверка заголовка окна истории по ТЗ."""
        win = PartnerHistoryWindow(
            self.root,
            partner_id=1,
            partner_name="ООО Логистик",
            db_path=DEFAULT_DB_PATH,
        )
        expected_title = "CRM: История реализации продукции — ООО Логистик"
        self.assertEqual(win.title(), expected_title)
        win.destroy()

    def test_sql_join_query_results(self) -> None:
        """Проверка выполнения SQL-запроса с JOIN к таблицам deliveries и products."""
        if not os.path.exists(DEFAULT_DB_PATH):
            self.skipTest("База данных не найдена")

        conn = sqlite3.connect(DEFAULT_DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        query = """
            SELECT
                pr.product_name,
                d.quantity,
                d.delivery_date
            FROM deliveries AS d
            INNER JOIN products AS pr ON d.product_id = pr.product_id
            WHERE d.partner_id = ?;
        """
        cur.execute(query, (1,))
        rows = cur.fetchall()
        conn.close()

        self.assertGreater(len(rows), 0)
        first_row = dict(rows[0])
        self.assertIn("product_name", first_row)
        self.assertIn("quantity", first_row)
        self.assertIn("delivery_date", first_row)
        self.assertIsInstance(first_row["quantity"], int)


if __name__ == "__main__":
    unittest.main()
