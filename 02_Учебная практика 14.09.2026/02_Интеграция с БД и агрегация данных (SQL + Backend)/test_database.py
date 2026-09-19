"""Тестирование модуля базы данных и агрегации истории продаж."""

import os
import tempfile
import unittest
from database import DatabaseManager, split_company_type_and_name


class TestDatabaseManager(unittest.TestCase):
    """Набор тестов для DatabaseManager."""

    def setUp(self) -> None:
        """Создание временной тестовой базы данных для изоляции тестов."""
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db_file.close()
        self.db = DatabaseManager(db_path=self.temp_db_file.name)

    def tearDown(self) -> None:
        """Удаление временного файла тестовой БД."""
        if os.path.exists(self.temp_db_file.name):
            os.remove(self.temp_db_file.name)

    def test_split_company_type_and_name(self) -> None:
        """Проверка корректного разделения организационной формы и названия."""
        self.assertEqual(
            split_company_type_and_name('ООО "Логистик-Экспресс"'),
            ("ООО", "Логистик-Экспресс"),
        )
        self.assertEqual(
            split_company_type_and_name("ИП Петров А.В."),
            ("ИП", "Петров А.В."),
        )
        self.assertEqual(
            split_company_type_and_name('ЗАО "База Строитель"'),
            ("ЗАО", "База Строитель"),
        )

    def test_partner_total_quantity_with_deliveries(self) -> None:
        """Партнер 1 имеет сумму поставок: 50 + 30 + 12000 = 12080."""
        qty = self.db.get_partner_total_quantity(1)
        self.assertEqual(qty, 12080)

    def test_partner_without_deliveries_returns_zero(self) -> None:
        """Партнер 5 не имеет поставок: проверка SUM(quantity) IS NULL -> 0."""
        qty = self.db.get_partner_total_quantity(5)
        self.assertEqual(qty, 0)

    def test_partner_with_discount_5_percent(self) -> None:
        """Партнер 1: 12 080 ед. -> 5% скидки."""
        data = self.db.get_partner_with_discount(1)
        self.assertIsNotNone(data)
        assert data is not None
        self.assertEqual(data["total_quantity"], 12080)
        self.assertEqual(data["discount_percent"], 5)
        self.assertEqual(data["partner_type"], "ООО")
        self.assertEqual(data["clean_name"], "Логистик-Экспресс")

    def test_partner_with_discount_10_percent(self) -> None:
        """Партнер 2: 200 + 55000 = 55 200 ед. -> 10% скидки."""
        data = self.db.get_partner_with_discount(2)
        self.assertIsNotNone(data)
        assert data is not None
        self.assertEqual(data["total_quantity"], 55200)
        self.assertEqual(data["discount_percent"], 10)

    def test_partner_with_discount_15_percent(self) -> None:
        """Партнер 3: 150 + 310000 = 310 150 ед. -> 15% скидки."""
        data = self.db.get_partner_with_discount(3)
        self.assertIsNotNone(data)
        assert data is not None
        self.assertEqual(data["total_quantity"], 310150)
        self.assertEqual(data["discount_percent"], 15)

    def test_partner_with_discount_zero_sales(self) -> None:
        """Партнер 5 (нет поставок): total_quantity = 0, discount_percent = 0."""
        data = self.db.get_partner_with_discount(5)
        self.assertIsNotNone(data)
        assert data is not None
        self.assertEqual(data["total_quantity"], 0)
        self.assertEqual(data["discount_percent"], 0)

    def test_non_existent_partner_returns_none(self) -> None:
        """Запрос несуществующего партнера возвращает None без ошибок."""
        data = self.db.get_partner_with_discount(999)
        self.assertIsNone(data)

    def test_get_all_partners_with_discounts(self) -> None:
        """Проверка выгрузки полного списка партнеров."""
        partners = self.db.get_all_partners_with_discounts()
        self.assertEqual(len(partners), 5)
        # Проверяем наличие всех ключевых полей
        for p in partners:
            self.assertIn("partner_id", p)
            self.assertIn("company_name", p)
            self.assertIn("partner_type", p)
            self.assertIn("clean_name", p)
            self.assertIn("director", p)
            self.assertIn("phone", p)
            self.assertIn("rating", p)
            self.assertIn("total_quantity", p)
            self.assertIn("discount_percent", p)


if __name__ == "__main__":
    unittest.main(verbosity=2)
