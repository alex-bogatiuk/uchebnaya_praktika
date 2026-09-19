# 02. Интеграция с БД и агрегация данных (SQL + Backend)

## Описание модуля

Данный модуль связывает реляционную базу данных и ядро бизнес-логики (расчет скидки):
1. Выполняет SQL-запрос с группировкой `SUM(quantity)` и `LEFT JOIN` к таблице истории отгрузок / продаж (`deliveries` / `sales_history`).
2. Корректно обрабатывает случай, когда у партнера нет истории отгрузок (`SUM(quantity) IS NULL` преобразуется в `0` через `COALESCE`).
3. Объединяет извлеченные данные партнера и результат функции `calculate_partner_discount` в единый объект / словарь.

---

## Архитектура и стек

- **СУБД**: SQLite (встроенная, нулевая зависимость для автономной работы) и совместимость со схемой PostgreSQL из практики 07.09.2026.
- **Драйвер**: нативный `sqlite3` с `row_factory = sqlite3.Row` для именованного доступа к полям.
- **Представление (View)**: создано представление `sales_history` поверх `deliveries` для полного соответствия формулировке ТЗ.

---

## SQL-запросы агрегации

### 1. Агрегация по конкретному партнеру
```sql
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
LEFT JOIN deliveries AS d
    ON p.partner_id = d.partner_id
WHERE p.partner_id = :partner_id
GROUP BY
    p.partner_id,
    p.company_name,
    p.inn,
    p.contact_email,
    p.phone,
    p.director,
    p.rating;
```

### 2. Агрегация по всем партнерам
```sql
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
LEFT JOIN deliveries AS d
    ON p.partner_id = d.partner_id
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
```

---

## Формат выходного словаря (объекта)

Метод `get_partner_with_discount(partner_id)` возвращает:

```json
{
  "partner_id": 1,
  "company_name": "ООО \"Логистик-Экспресс\"",
  "partner_type": "ООО",
  "clean_name": "Логистик-Экспресс",
  "inn": "7701234567",
  "contact_email": "info@logex.ru",
  "phone": "+7 (999) 111-22-33",
  "director": "Смирнов Алексей Викторович",
  "rating": 4.8,
  "total_quantity": 12080,
  "discount_percent": 5
}
```

---

## Запуск и проверка

Запуск тестов агрегации и работы с БД:
```bash
python test_database.py
```

Файл SQL-запросов: [`queries.sql`]  
Модуль интеграции: [`database.py`]
