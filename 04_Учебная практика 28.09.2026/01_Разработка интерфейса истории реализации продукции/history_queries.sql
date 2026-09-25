-- history_queries.sql
-- SQL-запросы для модуля отображения истории реализации продукции партнерам

-- 1. Запрос с JOIN для получения полной истории отгрузок конкретного партнера
--    Обязательные поля по ТЗ:
--    - Наименование продукции (pr.product_name)
--    - Количество (шт.) (d.quantity)
--    - Дата продажи (d.delivery_date)
SELECT
    pr.product_name,
    d.quantity,
    d.delivery_date,
    d.unit_price,
    (d.quantity * d.unit_price) AS total_sum
FROM deliveries AS d
INNER JOIN products AS pr
    ON d.product_id = pr.product_id
WHERE
    d.partner_id = :partner_id
ORDER BY
    d.delivery_date DESC;

-- 2. Запрос суммарной статистики партнера для шапки окна истории
SELECT
    p.partner_id,
    p.company_name,
    p.partner_type,
    COALESCE(SUM(d.quantity), 0) AS total_quantity,
    COALESCE(SUM(d.quantity * d.unit_price), 0.0) AS total_revenue
FROM partners AS p
LEFT JOIN deliveries AS d
    ON p.partner_id = d.partner_id
WHERE
    p.partner_id = :partner_id
GROUP BY
    p.partner_id,
    p.company_name,
    p.partner_type;
