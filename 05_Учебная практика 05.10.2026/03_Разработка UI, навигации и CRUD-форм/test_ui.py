"""Модульные тесты интерфейса UI, навигации и форм (Задание 3, 05.10.2026)."""

import os
import sys
import unittest
import tkinter as tk

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from app_ui import DB_PATH, MainWindow, PartnerEditWindow, PartnerHistoryWindow


class TestUIAndNavigation(unittest.TestCase):
    """Тестирование главных окон и переходов."""

    def setUp(self) -> None:
        self.root = MainWindow(db_path=DB_PATH)
        self.root.withdraw()

    def tearDown(self) -> None:
        self.root.destroy()

    def test_main_window_title_and_branding(self) -> None:
        """Проверка заголовка и компонентов главной формы."""
        self.assertEqual(self.root.title(), "CRM: Реестр партнеров компании")
        self.assertIsNotNone(self.root.cards_frame)

    def test_open_add_window_title(self) -> None:
        """Проверка открытия окна добавления партнера."""
        edit_win = PartnerEditWindow(self.root, partner_id=None, db_path=DB_PATH)
        self.assertEqual(edit_win.title(), "CRM: Карточка партнера [Добавление]")
        edit_win.destroy()

    def test_open_edit_window_title(self) -> None:
        """Проверка открытия окна редактирования партнера."""
        sample_data = {"partner_id": 1, "company_name": "ООО Тест", "rating": 5}
        edit_win = PartnerEditWindow(self.root, partner_id=1, partner_data=sample_data, db_path=DB_PATH)
        self.assertEqual(edit_win.title(), "CRM: Карточка партнера [Редактирование]")
        edit_win.destroy()

    def test_open_history_window_title(self) -> None:
        """Проверка открытия окна истории отгрузок."""
        hist_win = PartnerHistoryWindow(self.root, partner_id=1, partner_name="ООО Логистик", db_path=DB_PATH)
        self.assertEqual(hist_win.title(), "CRM: История реализации продукции — ООО Логистик")
        hist_win.destroy()


if __name__ == "__main__":
    unittest.main()
