-- checks.sql
-- Проверка количества импортированных строк.

SELECT COUNT(*) AS partners_count
FROM partners;
-- Ожидается: 3

SELECT COUNT(*) AS products_count
FROM products;
-- Ожидается: 3

SELECT COUNT(*) AS deliveries_count
FROM deliveries;
-- Ожидается: 4
