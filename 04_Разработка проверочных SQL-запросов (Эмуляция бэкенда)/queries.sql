-- queries.sql
-- Три проверочных сценария, эмулирующих работу будущего backend-приложения.

-- =====================================================================
-- 1. Список партнеров, отсортированный по названию,
--    с общим количеством сделанных доставок.
--    Требование: LEFT JOIN + COUNT.
-- =====================================================================
SELECT
    p.partner_id,
    p.company_name,
    p.inn,
    p.contact_email,
    p.phone,
    p.rating,
    COUNT(d.delivery_id) AS deliveries_count
FROM partners AS p
LEFT JOIN deliveries AS d
    ON d.partner_id = p.partner_id
GROUP BY
    p.partner_id,
    p.company_name,
    p.inn,
    p.contact_email,
    p.phone,
    p.rating
ORDER BY
    p.company_name;


-- =====================================================================
-- 2. Добавление данных в одной транзакции:
--    создание нового партнера и его первой тестовой доставки.
--
--    Используется product_id = 1, который присутствует в тестовом наборе
--    после выполнения ETL. Если добавление доставки завершится ошибкой,
--    вся транзакция будет отменена PostgreSQL.
-- =====================================================================
BEGIN;

WITH new_partner AS (
    INSERT INTO partners (
        company_name,
        inn,
        contact_email,
        phone,
        rating
    )
    VALUES (
        'ООО "Тестовый партнер"',
        '7709999999',
        'test_partner@example.com',
        '+79990000000',
        5.0
    )
    RETURNING partner_id
)
INSERT INTO deliveries (
    partner_id,
    product_id,
    delivery_date,
    quantity,
    unit_price
)
SELECT
    new_partner.partner_id,
    1,
    CURRENT_DATE,
    10,
    500.0000
FROM new_partner;

COMMIT;


-- =====================================================================
-- 3. Детальная история отгрузок конкретного партнера за период.
--
--    В будущем приложении значения partner_id, date_from и date_to
--    должны передаваться параметрами. Для проверочного запуска здесь
--    используются partner_id = 1 и период 2026-03-01..2026-03-31.
-- =====================================================================
SELECT
    d.delivery_id,
    p.product_name,
    d.delivery_date,
    d.quantity,
    d.unit_price,
    ROUND(d.quantity * d.unit_price, 2) AS total_amount
FROM deliveries AS d
JOIN products AS p
    ON p.product_id = d.product_id
WHERE
    d.partner_id = 1
    AND d.delivery_date BETWEEN DATE '2026-03-01' AND DATE '2026-03-31'
ORDER BY
    d.delivery_date DESC,
    d.delivery_id DESC;
