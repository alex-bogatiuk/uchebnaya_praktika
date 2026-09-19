-- load_data.sql
-- PostgreSQL / psql
-- Запускайте из корня репозитория после выполнения 02_ddl/schema.sql и 03_etl/etl.py.

BEGIN;

-- Повторный импорт начинается с чистых таблиц.
TRUNCATE TABLE deliveries, products, partners RESTART IDENTITY CASCADE;

\copy partners (partner_id, company_name, inn, contact_email, phone, rating) FROM '03_etl/cleaned/partners.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

\copy products (product_id, product_name) FROM '03_etl/cleaned/products.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

\copy deliveries (delivery_id, partner_id, product_id, delivery_date, quantity, unit_price) FROM '03_etl/cleaned/deliveries.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

-- После импорта явных ID синхронизируем identity-последовательности,
-- чтобы последующие INSERT без ID не конфликтовали с загруженными строками.
SELECT setval(
    pg_get_serial_sequence('partners', 'partner_id'),
    COALESCE((SELECT MAX(partner_id) FROM partners), 1),
    true
);

SELECT setval(
    pg_get_serial_sequence('products', 'product_id'),
    COALESCE((SELECT MAX(product_id) FROM products), 1),
    true
);

SELECT setval(
    pg_get_serial_sequence('deliveries', 'delivery_id'),
    COALESCE((SELECT MAX(delivery_id) FROM deliveries), 1),
    true
);

COMMIT;
