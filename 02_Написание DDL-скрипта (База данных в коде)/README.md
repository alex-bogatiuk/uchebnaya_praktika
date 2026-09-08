# 2. DDL-скрипт

Файл `schema.sql` разворачивает структуру PostgreSQL-базы данных.

Он содержит:

- `DROP TABLE IF EXISTS` в правильном порядке зависимостей;
- `CREATE TABLE` для `partners`, `products`, `deliveries`;
- `PRIMARY KEY`;
- `FOREIGN KEY ... ON DELETE RESTRICT`;
- `NOT NULL`;
- `UNIQUE` для ИНН и email партнера;
- `CHECK` для рейтинга, количества и цены;
- `DATE`, `TIMESTAMP`, `VARCHAR`, `INTEGER`, `DECIMAL`;
- индексы для истории отгрузок.

Запуск из корня репозитория:

```bash
psql -d your_database -f 02_ddl/schema.sql
```
