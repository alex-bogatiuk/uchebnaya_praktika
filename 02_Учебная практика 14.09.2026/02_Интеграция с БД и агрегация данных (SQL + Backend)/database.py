"""Модуль интеграции с базой данных и агрегации истории продаж партнеров.

Выполняет:
1. Подключение к реляционной базе данных (SQLite / PostgreSQL).
2. SQL-запросы с группировкой SUM(quantity) и LEFT JOIN к истории отгрузок.
3. Обогащение данных партнера индивидуальным процентом скидки
   (на базе функции calculate_partner_discount из Модуля 01).
4. Корректную обработку ситуаций с отсутствием продаж (SUM(quantity) IS NULL -> 0).
"""

import os
import re
import sqlite3
import sys
from typing import Any, Dict, List, Optional, Tuple

# Подключаем модуль расчета скидки из соседней папки Модуля 01
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_01_DIR = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "01_Разработка ядра бизнес-логики (Расчет скидки)")
)
if MODULE_01_DIR not in sys.path:
    sys.path.insert(0, MODULE_01_DIR)

from discount import calculate_partner_discount  # noqa: E402

DEFAULT_DB_PATH = os.path.join(CURRENT_DIR, "partners.db")


def split_company_type_and_name(full_name: str) -> Tuple[str, str]:
    """Разделяет организационно-правовую форму (тип) и название компании.

    Примеры:
        'ООО "Логистик-Экспресс"' -> ('ООО', 'Логистик-Экспресс')
        'ИП Петров А.В.'          -> ('ИП', 'Петров А.В.')
        'ТК "Быстрый Путь"'       -> ('ТК', 'Быстрый Путь')
        'ЗАО База Строитель'      -> ('ЗАО', 'База Строитель')

    Возвращает:
        Tuple[str, str]: (тип_партнера, чистое_наименование)
    """
    cleaned = full_name.strip()
    match = re.match(r"^([A-Za-zА-Яа-яЁё]+)\s*[\"«]?(.*?)[\"»]?$", cleaned)
    if match:
        partner_type = match.group(1).strip()
        name = match.group(2).strip()
        if not name:
            name = partner_type
        return partner_type, name
    return "Партнер", cleaned


class DatabaseManager:
    """Менеджер работы с базой данных партнеров и отгрузок."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        """Инициализация подключения к БД.

        Параметры:
            db_path (str): Путь к файлу базы данных SQLite или ':memory:'.
        """
        self.db_path = db_path
        self._mem_conn: Optional[sqlite3.Connection] = None
        if self.db_path == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:")
            self._mem_conn.row_factory = sqlite3.Row
            self._mem_conn.execute("PRAGMA foreign_keys = ON;")
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Возвращает соединение с базой данных с поддержкой доступа по именам колонок."""
        if self.db_path == ":memory:" and self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def close_connection(self, conn: sqlite3.Connection) -> None:
        """Закрывает соединение, если это не разделяемая in-memory база."""
        if self.db_path != ":memory:":
            conn.close()

    def init_database(self) -> None:
        """Создает структуру таблиц и загружает начальные данные, если БД пуста."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS partners (
                partner_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name  TEXT NOT NULL,
                inn           TEXT NOT NULL UNIQUE,
                contact_email TEXT NOT NULL UNIQUE,
                phone         TEXT,
                director      TEXT,
                rating        REAL,
                created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS products (
                product_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS deliveries (
                delivery_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id    INTEGER NOT NULL,
                product_id    INTEGER NOT NULL,
                delivery_date TEXT NOT NULL,
                quantity      INTEGER NOT NULL CHECK (quantity > 0),
                unit_price    REAL NOT NULL CHECK (unit_price >= 0),
                FOREIGN KEY (partner_id) REFERENCES partners (partner_id),
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            );

            CREATE VIEW IF NOT EXISTS sales_history AS
            SELECT
                delivery_id  AS sale_id,
                partner_id,
                product_id,
                delivery_date AS sale_date,
                quantity,
                unit_price
            FROM deliveries;
            """
        )
        conn.commit()

        # Проверяем, есть ли уже записи в таблице partners
        cursor.execute("SELECT COUNT(*) FROM partners;")
        count = cursor.fetchone()[0]
        if count == 0:
            self._seed_initial_data(conn)

        self.close_connection(conn)

    def _seed_initial_data(self, conn: sqlite3.Connection) -> None:
        """Заполняет базу начальными данными из 1-й практики или типовыми данными."""
        cursor = conn.cursor()

        # Начальные партнеры (включая партнера без продаж для проверки краевого случая)
        partners_data = [
            (
                1,
                'ООО "Логистик-Экспресс"',
                "7701234567",
                "info@logex.ru",
                "+7 (999) 111-22-33",
                "Смирнов Алексей Викторович",
                4.8,
            ),
            (
                2,
                "ИП Петров А.В.",
                "5001098765",
                "petrov_delivery@mail.ru",
                "+7 (916) 223-32-22",
                "Петров Андрей Васильевич",
                4.2,
            ),
            (
                3,
                'ТК "Быстрый Путь"',
                "7812345678",
                "speedway@yandex.ru",
                "+7 (812) 555-44-33",
                "Ковалев Сергей Михайлович",
                4.9,
            ),
            (
                4,
                'ЗАО "База Строитель"',
                "7709876543",
                "stroitel@base.ru",
                "+7 (223) 322-22-32",
                "Воронов Дмитрий Павлович",
                5.0,
            ),
            (
                5,
                'ПАО "Металл-Снаб"',
                "7715678901",
                "metal@snab.ru",
                "+7 (495) 777-88-99",
                "Семенов Игорь Николаевич",
                3.8,
            ),
        ]

        cursor.executemany(
            """
            INSERT INTO partners (partner_id, company_name, inn, contact_email, phone, director, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            partners_data,
        )

        # Начальные товары
        products_data = [
            (1, 'Стиральный порошок "Альфа"'),
            (2, 'Мыло жидкое "Стандарт"'),
            (3, "Кондиционер для белья"),
        ]
        cursor.executemany(
            """
            INSERT INTO products (product_id, product_name)
            VALUES (?, ?);
            """,
            products_data,
        )

        # Начальные отгрузки с разными объемами:
        # Партнер 1: 50 + 30 + 12000 = 12080 ед. -> 5% скидки
        # Партнер 2: 200 + 55000 = 55200 ед. -> 10% скидки
        # Партнер 3: 150 + 310000 = 310150 ед. -> 15% скидки
        # Партнер 4: 8500 ед. -> 0% скидки (< 10000)
        # Партнер 5: 0 поставок (нет записей в deliveries) -> 0% скидки (тест NULL)
        deliveries_data = [
            (101, 1, 1, "2026-03-01", 50, 500.0),
            (102, 2, 2, "2026-03-15", 200, 90.0),
            (103, 1, 3, "2026-03-20", 30, 350.0),
            (104, 3, 2, "2026-03-25", 150, 90.0),
            (105, 1, 2, "2026-04-10", 12000, 85.0),
            (106, 2, 1, "2026-04-15", 55000, 480.0),
            (107, 3, 3, "2026-05-02", 310000, 320.0),
            (108, 4, 1, "2026-05-18", 8500, 490.0),
        ]
        cursor.executemany(
            """
            INSERT INTO deliveries (delivery_id, partner_id, product_id, delivery_date, quantity, unit_price)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            deliveries_data,
        )

        conn.commit()

    def get_partner_total_quantity(self, partner_id: int) -> int:
        """Выполняет SQL-запрос с SUM(quantity) и LEFT JOIN для конкретного партнера.

        Если у партнера нет истории продаж, возвращает 0.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT COALESCE(SUM(d.quantity), 0) AS total_quantity
            FROM partners AS p
            LEFT JOIN deliveries AS d ON p.partner_id = d.partner_id
            WHERE p.partner_id = ?
            GROUP BY p.partner_id;
        """
        cursor.execute(query, (partner_id,))
        row = cursor.fetchone()
        self.close_connection(conn)

        if row is None:
            return 0
        return int(row["total_quantity"])

    def get_partner_with_discount(self, partner_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает словарь с полными данными партнера и рассчитанной скидкой.

        Возвращает None, если партнер с указанным partner_id не найден.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                p.partner_id,
                p.company_name,
                p.inn,
                p.contact_email,
                p.phone,
                p.director,
                p.rating,
                COALESCE(SUM(d.quantity), 0) AS total_quantity
            FROM partners AS p
            LEFT JOIN deliveries AS d ON p.partner_id = d.partner_id
            WHERE p.partner_id = ?
            GROUP BY
                p.partner_id,
                p.company_name,
                p.inn,
                p.contact_email,
                p.phone,
                p.director,
                p.rating;
        """
        cursor.execute(query, (partner_id,))
        row = cursor.fetchone()
        self.close_connection(conn)

        if row is None:
            return None

        total_quantity = int(row["total_quantity"])
        discount_percent = calculate_partner_discount(total_quantity)
        partner_type, clean_name = split_company_type_and_name(row["company_name"])

        return {
            "partner_id": row["partner_id"],
            "company_name": row["company_name"],
            "partner_type": partner_type,
            "clean_name": clean_name,
            "inn": row["inn"],
            "contact_email": row["contact_email"],
            "phone": row["phone"] or "Не указан",
            "director": row["director"] or "Руководитель не указан",
            "rating": float(row["rating"]) if row["rating"] is not None else 0.0,
            "total_quantity": total_quantity,
            "discount_percent": discount_percent,
        }

    def get_all_partners_with_discounts(self) -> List[Dict[str, Any]]:
        """Возвращает список всех партнеров с агрегированными продажами и скидками."""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                p.partner_id,
                p.company_name,
                p.inn,
                p.contact_email,
                p.phone,
                p.director,
                p.rating,
                COALESCE(SUM(d.quantity), 0) AS total_quantity
            FROM partners AS p
            LEFT JOIN deliveries AS d ON p.partner_id = d.partner_id
            GROUP BY
                p.partner_id,
                p.company_name,
                p.inn,
                p.contact_email,
                p.phone,
                p.director,
                p.rating
            ORDER BY
                p.partner_id ASC;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        self.close_connection(conn)

        results = []
        for row in rows:
            total_quantity = int(row["total_quantity"])
            discount_percent = calculate_partner_discount(total_quantity)
            partner_type, clean_name = split_company_type_and_name(row["company_name"])

            results.append(
                {
                    "partner_id": row["partner_id"],
                    "company_name": row["company_name"],
                    "partner_type": partner_type,
                    "clean_name": clean_name,
                    "inn": row["inn"],
                    "contact_email": row["contact_email"],
                    "phone": row["phone"] or "Не указан",
                    "director": row["director"] or "Руководитель не указан",
                    "rating": float(row["rating"]) if row["rating"] is not None else 0.0,
                    "total_quantity": total_quantity,
                    "discount_percent": discount_percent,
                }
            )

        return results
