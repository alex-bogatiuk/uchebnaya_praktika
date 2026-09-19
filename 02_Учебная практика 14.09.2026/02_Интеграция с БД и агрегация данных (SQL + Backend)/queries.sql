-- queries.sql
-- Проверочные SQL-запросы для модуля 02: Агрегация данных и расчет скидки.

-- =====================================================================
-- 1. Получение суммарного объема продаж по КОНКРЕТНОМУ партнеру
--    Используется LEFT JOIN и SUM(quantity) с обработкой NULL -> 0.
--    Таблица deliveries алиасится также как sales_history.
-- =====================================================================
SELECT
    p.partner_id,
    p.company_name,
    p.inn,
    p.contact_email,
    p.phone,
    p.rating,
    COALESCE(SUM(d.quantity), 0) AS total_quantity
FROM partners AS p
LEFT JOIN deliveries AS d
    ON p.partner_id = d.partner_id
WHERE
    p.partner_id = :partner_id
GROUP BY
    p.partner_id,
    p.company_name,
    p.inn,
    p.contact_email,
    p.phone,
    p.rating;


-- =====================================================================
-- 2. Получение агрегированных объемов продаж по ВСЕМ партнерам
--    Позволяет бэкенду за один запрос получить данные для всего каталога.
-- =====================================================================
SELECT
    p.partner_id,
    p.company_name,
    p.inn,
    p.contact_email,
    p.phone,
    p.rating,
    COALESCE(SUM(d.quantity), 0) AS total_quantity
FROM partners AS p
LEFT JOIN deliveries AS d
    ON p.partner_id = d.partner_id
GROUP BY
    p.partner_id,
    p.company_name,
    p.inn,
    p.contact_email,
    p.phone,
    p.rating
ORDER BY
    p.partner_id ASC;


-- =====================================================================
-- 3. Создание представления sales_history для полной совместимости с ТЗ
-- =====================================================================
CREATE VIEW IF NOT EXISTS sales_history AS
SELECT
    delivery_id  AS sale_id,
    partner_id,
    product_id,
    delivery_date AS sale_date,
    quantity,
    unit_price
FROM deliveries;


-- =====================================================================
-- 4. Запрос непосредственно из sales_history по конкретному партнеру
-- =====================================================================
SELECT
    p.partner_id,
    p.company_name,
    COALESCE(SUM(s.quantity), 0) AS total_quantity
FROM partners AS p
LEFT JOIN sales_history AS s
    ON p.partner_id = s.partner_id
WHERE
    p.partner_id = :partner_id
GROUP BY
    p.partner_id,
    p.company_name;
