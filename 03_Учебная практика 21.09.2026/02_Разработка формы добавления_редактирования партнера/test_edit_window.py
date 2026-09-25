"""Модульные тесты формы PartnerEditWindow (Задание 2)."""

import os
import sys
import unittest
import tkinter as tk

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from edit_window import PartnerEditWindow, PARTNER_TYPES


class TestPartnerEditWindow(unittest.TestCase):
    """Тестирование инициализации формы, полей ввода и автозаполнения."""

    def setUp(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self) -> None:
        self.root.destroy()

    def test_combobox_values(self) -> None:
        """Проверка списка допустимых типов партнеров в выпадающем списке."""
        self.assertIn("ООО", PARTNER_TYPES)
        self.assertIn("ЗАО", PARTNER_TYPES)
        self.assertIn("ИП", PARTNER_TYPES)
        self.assertIn("ПАО", PARTNER_TYPES)
        self.assertIn("ОАО", PARTNER_TYPES)

    def test_empty_form_creation(self) -> None:
        """Проверка пустой формы в режиме добавления."""
        form = PartnerEditWindow(self.root, partner_id=None)
        self.assertEqual(form.title(), "CRM: Карточка партнера [Добавление]")
        self.assertEqual(form.entry_name.get(), "")
        self.assertEqual(form.combo_type.get(), "ООО")
        self.assertFalse(form.has_unsaved_changes())
        form.destroy()

    def test_populate_fields_in_edit_mode(self) -> None:
        """Проверка корректной подгрузки данных партнера в поля."""
        partner_data = {
            "partner_id": 10,
            "company_name": "ООО Ромашка",
            "partner_type": "ЗАО",
            "rating": 7,
            "address": "г. Москва, ул. Ленина, 1",
            "director": "Иванов И.И.",
            "phone": "+7 (999) 000-11-22",
            "contact_email": "ivanov@romashka.ru",
        }
        form = PartnerEditWindow(self.root, partner_id=10, partner_data=partner_data)
        self.assertEqual(form.title(), "CRM: Карточка партнера [Редактирование]")
        self.assertEqual(form.entry_name.get(), "ООО Ромашка")
        self.assertEqual(form.combo_type.get(), "ЗАО")
        self.assertEqual(form.entry_rating.get(), "7")
        self.assertEqual(form.entry_address.get(), "г. Москва, ул. Ленина, 1")
        self.assertEqual(form.entry_director.get(), "Иванов И.И.")
        self.assertEqual(form.entry_phone.get(), "+7 (999) 000-11-22")
        self.assertEqual(form.entry_email.get(), "ivanov@romashka.ru")
        self.assertFalse(form.has_unsaved_changes())

        # Изменяем имя
        form.entry_name.delete(0, tk.END)
        form.entry_name.insert(0, "ООО Василек")
        self.assertTrue(form.has_unsaved_changes())
        form.destroy()


if __name__ == "__main__":
    unittest.main()
