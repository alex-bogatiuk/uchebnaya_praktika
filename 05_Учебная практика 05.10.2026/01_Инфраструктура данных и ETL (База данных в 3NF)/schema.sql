-- schema.sql
-- Реляционная схема базы данных в третьей нормальной форме (3NF).
-- Единый стиль именования: snake_case.
-- Поддержка ограничений целостности: NOT NULL, UNIQUE, FOREIGN KEY, CHECK.

PRAGMA foreign_keys = ON;

-- 1. Справочник типов продукции (для калькулятора материалов)
CREATE TABLE IF NOT EXISTS product_types (
    type_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name    TEXT NOT NULL UNIQUE,
    coefficient  REAL NOT NULL CHECK (coefficient > 0)
);

-- 2. Справочник типов сырья / материалов (с процентом брака)
CREATE TABLE IF NOT EXISTS material_types (
    type_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name       TEXT NOT NULL UNIQUE,
    defect_percent  REAL NOT NULL CHECK (defect_percent >= 0)
);

-- 3. Основная таблица информации о партнерах компании (3NF)
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
    updated_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_partners_name_non_empty CHECK (length(trim(company_name)) > 0),
    CONSTRAINT chk_partners_email_format CHECK (contact_email LIKE '%@%.%')
);

-- 4. Справочник товарной номенклатуры (3NF)
CREATE TABLE IF NOT EXISTS products (
    product_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL UNIQUE,

    CONSTRAINT chk_products_name_non_empty CHECK (length(trim(product_name)) > 0)
);

-- 5. История реализации продукции партнерам (sales_history)
CREATE TABLE IF NOT EXISTS sales_history (
    sale_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_id    INTEGER NOT NULL,
    product_id    INTEGER NOT NULL,
    sale_date     TEXT NOT NULL,
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    unit_price    REAL NOT NULL CHECK (unit_price >= 0),

    FOREIGN KEY (partner_id) REFERENCES partners (partner_id) ON DELETE RESTRICT,
    FOREIGN KEY (product_id) REFERENCES products (product_id) ON DELETE RESTRICT
);

-- 6. Представление deliveries для обратной совместимости с модулями 02-04
CREATE VIEW IF NOT EXISTS deliveries AS
SELECT
    sale_id AS delivery_id,
    partner_id,
    product_id,
    sale_date AS delivery_date,
    quantity,
    unit_price
FROM sales_history;

-- Индексы для оптимизации выборок и JOIN-запросов
CREATE INDEX IF NOT EXISTS idx_sales_partner_date
    ON sales_history (partner_id, sale_date DESC);

CREATE INDEX IF NOT EXISTS idx_sales_product
    ON sales_history (product_id);
