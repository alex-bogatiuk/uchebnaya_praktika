"""Модуль работы с базой данных SQLite с поддержкой CRUD-операций и ссылочной целостности."""

import os
import sqlite3
import sys
from typing import Any, Dict, List, Optional, Tuple

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(CURRENT_DIR, "partners.db")


class DatabaseManager:
    """Менеджер базы данных с гарантией ссылочной целостности и CRUD-методами."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Возвращает соединение с включенным контролем внешних ключей."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Обязательное включение ссылочной целостности в SQLite (ТЗ пункт 3)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_database(self) -> None:
        """Инициализация схемы БД и начального наполнения."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.executescript(
                """
                CREATE TABLE IF NOT EXISTS partners (
                    partner_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name  TEXT NOT NULL,
                    partner_type  TEXT NOT NULL DEFAULT 'ООО',
                    inn           TEXT UNIQUE,
                    contact_email TEXT NOT NULL UNIQUE,
                    phone         TEXT,
                    director      TEXT,
                    address       TEXT,
                    rating        INTEGER NOT NULL DEFAULT 0 CHECK (rating >= 0),
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
                    FOREIGN KEY (partner_id) REFERENCES partners (partner_id) ON DELETE RESTRICT,
                    FOREIGN KEY (product_id) REFERENCES products (product_id) ON DELETE RESTRICT
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

            # Если партнеров еще нет, заполняем начальными эталонными данными
            cursor.execute("SELECT COUNT(*) FROM partners;")
            if cursor.fetchone()[0] == 0:
                self._seed_data(cursor)
            conn.commit()
        finally:
            conn.close()

    def _seed_data(self, cursor: sqlite3.Cursor) -> None:
        """Заполнение начальными данными."""
        sample_partners = [
            (1, "Логистик-Экспресс", "ООО", "7701234567", "info@logex.ru", "+7 (999) 111-22-33", "Смирнов Алексей Викторович", "г. Москва, ул. Ленина, 10", 5),
            (2, "Петров А.В.", "ИП", "5001098765", "petrov_delivery@mail.ru", "+7 (916) 223-32-22", "Петров Андрей Васильевич", "г. Подольск, ул. Мира, 4", 4),
            (3, "Быстрый Путь", "ТК", "7812345678", "speedway@yandex.ru", "+7 (812) 555-44-33", "Ковалев Сергей Михайлович", "г. Санкт-Петербург, пр. Невский, 15", 5),
            (4, "База Строитель", "ЗАО", "7709876543", "stroitel@base.ru", "+7 (223) 322-22-32", "Воронов Дмитрий Павлович", "г. Москва, ш. Варшавское, 50", 5),
            (5, "Металл-Снаб", "ПАО", "7715678901", "metal@snab.ru", "+7 (495) 777-88-99", "Семенов Игорь Николаевич", "г. Екатеринбург, ул. Заводская, 2", 3),
        ]
        cursor.executemany(
            """
            INSERT INTO partners (partner_id, company_name, partner_type, inn, contact_email, phone, director, address, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            sample_partners,
        )

        sample_products = [
            (1, 'Стиральный порошок "Альфа"'),
            (2, 'Мыло жидкое "Стандарт"'),
            (3, 'Кондиционер для белья'),
        ]
        cursor.executemany(
            "INSERT INTO products (product_id, product_name) VALUES (?, ?);",
            sample_products,
        )

        sample_deliveries = [
            (101, 1, 1, "2026-03-01", 12080, 500.0),
            (102, 2, 2, "2026-03-15", 55200, 90.0),
            (103, 3, 3, "2026-03-20", 310150, 350.0),
            (104, 4, 1, "2026-03-25", 8500, 490.0),
        ]
        cursor.executemany(
            """
            INSERT INTO deliveries (delivery_id, partner_id, product_id, delivery_date, quantity, unit_price)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            sample_deliveries,
        )

    def execute_query(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """Выполняет запрос на чтение с гарантированным закрытием соединения."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def execute_non_query(self, query: str, params: Tuple = ()) -> Tuple[int, int]:
        """Выполняет запрос на модификацию (INSERT/UPDATE/DELETE) и возвращает (lastrowid, rowcount)."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid, cursor.rowcount
        finally:
            conn.close()

    def get_all_partners_with_discounts(self) -> List[Dict[str, Any]]:
        """Возвращает список всех партнеров с агрегированным объемом продаж и скидкой."""
        query = """
            SELECT
                p.partner_id,
                p.company_name,
                p.partner_type,
                p.inn,
                p.contact_email,
                p.phone,
                p.director,
                p.address,
                p.rating,
                COALESCE(SUM(d.quantity), 0) AS total_quantity
            FROM partners AS p
            LEFT JOIN deliveries AS d ON p.partner_id = d.partner_id
            GROUP BY p.partner_id
            ORDER BY p.partner_id ASC;
        """
        rows = self.execute_query(query)
        result = []
        for r in rows:
            qty = int(r["total_quantity"])
            if qty < 10000:
                discount = 0
            elif qty < 50000:
                discount = 5
            elif qty < 300000:
                discount = 10
            else:
                discount = 15

            item = dict(r)
            item["discount_percent"] = discount
            result.append(item)
        return result

    def get_partner_by_id(self, partner_id: int) -> Optional[Dict[str, Any]]:
        """Получает полные актуальные данные партнера по ID."""
        rows = self.execute_query("SELECT * FROM partners WHERE partner_id = ?;", (partner_id,))
        return dict(rows[0]) if rows else None

    def add_partner(self, data: Dict[str, Any]) -> int:
        """Создает новую запись партнера (INSERT) и возвращает присвоенный ID."""
        query = """
            INSERT INTO partners (company_name, partner_type, contact_email, phone, director, address, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        params = (
            data["company_name"].strip(),
            data.get("partner_type", "ООО").strip(),
            data["contact_email"].strip(),
            data.get("phone", "").strip(),
            data.get("director", "").strip(),
            data.get("address", "").strip(),
            int(data.get("rating", 0)),
        )
        lastrowid, _ = self.execute_non_query(query, params)
        return lastrowid

    def update_partner(self, partner_id: int, data: Dict[str, Any]) -> bool:
        """Обновляет существующую запись партнера (UPDATE)."""
        query = """
            UPDATE partners
            SET
                company_name = ?,
                partner_type = ?,
                contact_email = ?,
                phone = ?,
                director = ?,
                address = ?,
                rating = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE partner_id = ?;
        """
        params = (
            data["company_name"].strip(),
            data.get("partner_type", "ООО").strip(),
            data["contact_email"].strip(),
            data.get("phone", "").strip(),
            data.get("director", "").strip(),
            data.get("address", "").strip(),
            int(data.get("rating", 0)),
            partner_id,
        )
        _, rowcount = self.execute_non_query(query, params)
        return rowcount > 0

    def delete_partner(self, partner_id: int) -> bool:
        """Удаляет партнера с проверкой ссылочной целостности."""
        query = "DELETE FROM partners WHERE partner_id = ?;"
        _, rowcount = self.execute_non_query(query, (partner_id,))
        return rowcount > 0
