# Проект БД партнёров и истории отгрузок

Учебный проект по проектированию и реализации базы данных PostgreSQL для работы с партнёрами компании и историей их отгрузок.

## Бизнес-требования

Система должна обеспечивать:

1. просмотр партнёров;
2. редактирование данных партнёров;
3. просмотр истории отгрузок;
4. хранение состава отгрузок и стоимости товаров на момент отгрузки.

## Структура репозитория

```text
partner-db-practice/
├── 01_database_design/
│   └── README.md
├── 02_ddl/
│   ├── README.md
│   └── schema.sql
├── 03_etl/
│   ├── README.md
│   ├── etl.py
│   ├── load_data.sql
│   ├── source/
│   │   ├── import_partners.csv
│   │   └── import_sales.txt
│   └── output/
│       ├── partner_types.csv
│       ├── partners_clean.csv
│       ├── products_clean.csv
│       ├── shipment_statuses.csv
│       ├── shipments_clean.csv
│       ├── shipment_items_clean.csv
│       ├── rejected_sales.csv
│       └── etl_report.txt
└── 04_backend_queries/
    ├── README.md
    └── queries.sql
```

## Технологии

- PostgreSQL
- SQL
- Python 3
- CSV / TSV
- Mermaid для ER-диаграммы

Для ETL используются только модули стандартной библиотеки Python, поэтому установка дополнительных пакетов не требуется.

## Быстрый запуск

### 1. Создать структуру БД

```bash
psql -d your_database -f 02_ddl/schema.sql
```

### 2. Подготовить данные

Из каталога `03_etl`:

```bash
python etl.py
```

### 3. Загрузить данные

Из каталога `03_etl`:

```bash
psql -d your_database -f load_data.sql
```

### 4. Выполнить проверочные запросы

Файл:

```text
04_backend_queries/queries.sql
```

Запросы содержат параметры `$1`, `$2` и т. д., поскольку имитируют вызовы будущего backend-приложения.

## Результат

Проект последовательно демонстрирует полный цикл работы с реляционной БД: проектирование в 3NF → DDL → ETL → SQL-запросы приложения.
