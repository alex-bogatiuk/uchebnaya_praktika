"""Модульные тесты многооконной архитектуры и навигации (Задание 1)."""

import os
import sys
import unittest

# Добавление текущей папки в sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from navigation_app import MainWindow, PartnerEditWindow


class TestNavigationArchitecture(unittest.TestCase):
    """Проверка переходов между окнами и корректности заголовков."""

    def setUp(self) -> None:
        """Создание экземпляра MainWindow в скрытом режиме."""
        self.app = MainWindow()
        self.app.withdraw()

    def tearDown(self) -> None:
        """Корректное уничтожение окон."""
        if self.app.edit_window_instance and self.app.edit_window_instance.winfo_exists():
            self.app.edit_window_instance.destroy()
        self.app.destroy()

    def test_main_window_title(self) -> None:
        """Проверка заголовка главного окна по ТЗ."""
        self.assertEqual(self.app.title(), "CRM: Реестр партнеров")

    def test_open_add_window_title_and_mode(self) -> None:
        """Проверка заголовка окна в режиме добавления."""
        self.app.open_add_window()
        self.assertIsNotNone(self.app.edit_window_instance)
        self.assertEqual(
            self.app.edit_window_instance.title(),
            "CRM: Карточка партнера [Добавление]",
        )
        self.assertIsNone(self.app.edit_window_instance.partner_id)

    def test_open_edit_window_title_and_mode(self) -> None:
        """Проверка заголовка окна в режиме редактирования."""
        sample_partner = {"partner_id": 42, "company_name": "ООО Тест", "type": "ООО"}
        self.app.open_edit_window(sample_partner)
        self.assertIsNotNone(self.app.edit_window_instance)
        self.assertEqual(
            self.app.edit_window_instance.title(),
            "CRM: Карточка партнера [Редактирование]",
        )
        self.assertEqual(self.app.edit_window_instance.partner_id, 42)

    def test_back_button_closes_edit_window_safely(self) -> None:
        """Проверка закрытия карточки по кнопке Назад без повреждения главного окна."""
        self.app.open_add_window()
        subwindow = self.app.edit_window_instance
        self.assertTrue(subwindow.winfo_exists())

        # Симуляция нажатия кнопки Назад
        subwindow.on_back_pressed()
        self.assertFalse(subwindow.winfo_exists())
        self.assertIsNone(self.app.edit_window_instance)
        self.assertTrue(self.app.winfo_exists())


if __name__ == "__main__":
    unittest.main()
