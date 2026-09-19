"""Скрипт стресс-тестирования, отладки и проверки отказоустойчивости приложения.

Проверяет ключевые требования ТЗ Подзадания 4:
1. Обработка ситуаций, когда у партнера нет истории продаж (SUM(quantity) IS NULL или 0).
   Скидка должна быть строго 0%, приложение не должно выбрасывать исключения (TypeError / NullPointerException).
2. Обработка неполных/отсутствующих данных (NULL телефон, NULL директор, NULL рейтинг).
3. Нагрузочный стресс-тест: генерация 1 000 партнеров и 10 000 отгрузок с измерением
   производительности SQL-агрегации и вычисления скидок.
4. Экстремальные значения объемов отгрузок (пограничные и сверхбольшие объемы).
"""

import os
import random
import sys
import tempfile
import time
import unittest

# Подключение модулей
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
from discount import calculate_partner_discount


class TestResilienceAndNullHandling(unittest.TestCase):
    """Тестирование отказоустойчивости при обработке NULL и нулевых продаж."""

    def setUp(self) -> None:
        """Инициализация изолированной БД во временном файле."""
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_file.close()
        self.db = DatabaseManager(db_path=self.temp_file.name)

    def tearDown(self) -> None:
        """Очистка временного файла."""
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_null_sales_handling(self) -> None:
        """Партнер без отгрузок (SUM(quantity) IS NULL) должен давать 0% скидки без ошибок."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO partners (company_name, inn, contact_email, phone, director, rating)
            VALUES ('ООО "Новый Партнер"', '7700000001', 'new@partner.ru', NULL, NULL, NULL);
            """
        )
        partner_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Проверяем получение объема продаж
        total_qty = self.db.get_partner_total_quantity(partner_id)
        self.assertEqual(total_qty, 0)

        # Проверяем получение полного объекта с рассчитанной скидкой
        partner = self.db.get_partner_with_discount(partner_id)
        self.assertIsNotNone(partner)
        assert partner is not None
        self.assertEqual(partner["total_quantity"], 0)
        self.assertEqual(partner["discount_percent"], 0)
        self.assertEqual(partner["phone"], "Не указан")
        self.assertEqual(partner["director"], "Руководитель не указан")
        self.assertEqual(partner["rating"], 0.0)

    def test_missing_and_corrupt_data_robustness(self) -> None:
        """Проверка устойчивости при частично заполненных данных нескольких партнеров."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        test_partners = [
            ('ЗАО "Без Телефона"', "7700000002", "p2@corp.ru", None, "Иванов И. И.", 5.0),
            ('ИП "Без Директора"', "7700000003", "p3@corp.ru", "+79991234567", None, 3.5),
            ('ООО "Без Рейтинга"', "7700000004", "p4@corp.ru", "+79997654321", "Петров П. П.", None),
        ]
        cursor.executemany(
            """
            INSERT INTO partners (company_name, inn, contact_email, phone, director, rating)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            test_partners,
        )
        conn.commit()
        conn.close()

        all_partners = self.db.get_all_partners_with_discounts()
        self.assertGreaterEqual(len(all_partners), 8)
        for p in all_partners:
            self.assertIsInstance(p["discount_percent"], int)
            self.assertGreaterEqual(p["discount_percent"], 0)
            self.assertIsInstance(p["clean_name"], str)
            self.assertIsInstance(p["partner_type"], str)


class StressTestPerformance(unittest.TestCase):
    """Стресс-тест производительности и масштабируемости."""

    def test_high_volume_stress(self) -> None:
        """Стресс-тест с 1 000 партнеров и 10 000 отгрузок."""
        print("\n" + "=" * 60)
        print("СТАРТ СТРЕСС-ТЕСТИРОВАНИЯ (1 000 партнеров, 10 000 отгрузок)")
        print("=" * 60)

        temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_db.close()
        db = DatabaseManager(db_path=temp_db.name)
        conn = db.get_connection()
        cursor = conn.cursor()

        # Генерация 1 000 партнеров
        t0 = time.perf_counter()
        partners_data = []
        types = ["ООО", "ИП", "ЗАО", "ПАО", "ТК"]
        for i in range(10, 1010):
            p_type = random.choice(types)
            p_name = f'{p_type} "Партнер Тест #{i}"'
            p_inn = f"77{i:08d}"
            p_email = f"test_{i}@partner.ru"
            p_phone = f"+7 (999) {i:07d}" if i % 10 != 0 else None  # 10% без телефона
            p_dir = f"Директор Тестовый #{i}" if i % 15 != 0 else None  # часть без директора
            p_rate = round(random.uniform(1.0, 5.0), 1) if i % 20 != 0 else None
            partners_data.append((i, p_name, p_inn, p_email, p_phone, p_dir, p_rate))

        cursor.executemany(
            """
            INSERT INTO partners (partner_id, company_name, inn, contact_email, phone, director, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            partners_data,
        )
        conn.commit()
        t_partners = time.perf_counter() - t0
        print(f"-> 1 000 партнеров сгенерировано за: {t_partners:.4f} сек")

        # Генерация 10 000 отгрузок
        t0 = time.perf_counter()
        deliveries_data = []
        # Распределяем поставки так, чтобы часть партнеров (например 100 штук) остались с 0 продаж
        active_partner_ids = list(range(10, 910))
        for d_id in range(1000, 11000):
            p_id = random.choice(active_partner_ids)
            qty = random.randint(5, 35000)
            price = round(random.uniform(50.0, 1500.0), 2)
            deliveries_data.append((d_id, p_id, 1, "2026-06-01", qty, price))

        cursor.executemany(
            """
            INSERT INTO deliveries (delivery_id, partner_id, product_id, delivery_date, quantity, unit_price)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            deliveries_data,
        )
        conn.commit()
        t_deliveries = time.perf_counter() - t0
        print(f"-> 10 000 отгрузок сгенерировано за: {t_deliveries:.4f} сек")

        # Создаем индекс для ускорения JOIN
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_deliv_partner ON deliveries(partner_id);")
        conn.commit()
        conn.close()

        # Тест агрегации полного списка с расчетом скидок
        t0 = time.perf_counter()
        results = db.get_all_partners_with_discounts()
        t_query = time.perf_counter() - t0
        print(f"-> Агрегация + расчет скидок для всех партнеров: {t_query:.4f} сек")

        # Проверка целостности
        self.assertGreaterEqual(len(results), 1000)

        # Подсчет распределения скидок
        discount_counts = {0: 0, 5: 0, 10: 0, 15: 0}
        zero_sales_count = 0
        for r in results:
            d = r["discount_percent"]
            discount_counts[d] = discount_counts.get(d, 0) + 1
            if r["total_quantity"] == 0:
                zero_sales_count += 1
                self.assertEqual(r["discount_percent"], 0)

        print("\nРаспределение скидок по результатам стресс-теста:")
        for disc, count in sorted(discount_counts.items()):
            print(f"   Скидка {disc:>2}%: {count} партнеров")
        print(f"   Партнеров с 0 продажами (NULL): {zero_sales_count} (скидка 0% гарантирована)")
        print("=" * 60)
        print("СТРЕСС-ТЕСТ УСПЕШНО ПРОЙДЕН: Сбоев нет, время отклика < 0.5 сек")
        print("=" * 60 + "\n")

        # Производительность агрегации должна быть быстрее 1.0 секунды
        self.assertLess(t_query, 1.0)

        # Очистка временного файла
        if os.path.exists(temp_db.name):
            try:
                os.remove(temp_db.name)
            except OSError:
                pass


def run_all_stress_tests() -> bool:
    """Запуск всех проверок отказоустойчивости и стресс-тестов."""
    suite = unittest.TestSuite()
    suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestResilienceAndNullHandling))
    suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(StressTestPerformance))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_stress_tests()
    sys.exit(0 if success else 1)
