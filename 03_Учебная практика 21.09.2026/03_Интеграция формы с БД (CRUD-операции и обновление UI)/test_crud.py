"""Модульные тесты CRUD-операций и ссылочной целостности базы данных (Задание 3)."""

import os
import sqlite3
import sys
import tempfile
import unittest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from database_crud import DatabaseManager


class TestDatabaseCRUD(unittest.TestCase):
    """Тестирование CRUD-операций и ссылочной целостности."""

    def setUp(self) -> None:
        """Создание изолированной временной базы данных для тестов."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db = DatabaseManager(db_path=self.temp_db.name)

    def tearDown(self) -> None:
        """Удаление временной базы данных."""
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_add_partner_insert(self) -> None:
        """Проверка добавления нового партнера (INSERT)."""
        new_partner = {
            "company_name": "ООО Новатор",
            "partner_type": "ООО",
            "contact_email": "novator@test.ru",
            "phone": "+7 (900) 123-45-67",
            "director": "Кузнецов К.К.",
            "address": "г. Казань, ул. Баумана, 5",
            "rating": 8,
        }
        new_id = self.db.add_partner(new_partner)
        self.assertIsInstance(new_id, int)
        self.assertGreater(new_id, 0)

        # Проверяем, что запись действительно появилась в БД
        fetched = self.db.get_partner_by_id(new_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["company_name"], "ООО Новатор")
        self.assertEqual(fetched["partner_type"], "ООО")
        self.assertEqual(fetched["contact_email"], "novator@test.ru")
        self.assertEqual(fetched["rating"], 8)

    def test_update_partner_query(self) -> None:
        """Проверка обновления существующего партнера (UPDATE)."""
        original = self.db.get_partner_by_id(1)
        self.assertIsNotNone(original)

        updated_data = {
            "company_name": "ООО Логистик-Групп",
            "partner_type": "ПАО",
            "contact_email": "updated_info@logex.ru",
            "phone": "+7 (999) 777-77-77",
            "director": "Смирнов Алексей Викторович (Обновлен)",
            "address": "г. Москва, ул. Ленина, д. 99",
            "rating": 10,
        }
        success = self.db.update_partner(1, updated_data)
        self.assertTrue(success)

        # Проверяем обновленные данные
        refreshed = self.db.get_partner_by_id(1)
        self.assertEqual(refreshed["company_name"], "ООО Логистик-Групп")
        self.assertEqual(refreshed["partner_type"], "ПАО")
        self.assertEqual(refreshed["rating"], 10)
        self.assertEqual(refreshed["contact_email"], "updated_info@logex.ru")

    def test_referential_integrity_foreign_key_protection(self) -> None:
        """Проверка ссылочной целостности: запрет удаления партнера с активными поставками."""
        # Партнер с ID=1 имеет поставку delivery_id=101
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.delete_partner(1)

    def test_get_all_partners_aggregates_sales(self) -> None:
        """Проверка выгрузки полного каталога с расчетом скидок."""
        partners = self.db.get_all_partners_with_discounts()
        self.assertGreaterEqual(len(partners), 5)
        # Проверяем партнера 1 (объем 12080 ед. -> 5% скидки)
        p1 = next(p for p in partners if p["partner_id"] == 1)
        self.assertEqual(p1["total_quantity"], 12080)
        self.assertEqual(p1["discount_percent"], 5)


if __name__ == "__main__":
    unittest.main()
