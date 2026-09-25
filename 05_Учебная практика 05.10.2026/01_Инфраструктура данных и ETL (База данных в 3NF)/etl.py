"""ETL-конвейер: очистка сырых данных, нормализация и загрузка в базу данных 3NF.

Выполняет:
1. Удаление лишних пробелов (TRIM) во всех строковых полях;
2. Нормализацию дат к стандарту СУБД (ГГГГ-ММ-ДД);
3. Проверку ссылочной целостности и фильтрацию строк с несуществующим ID партнера (в rejected_sales.csv);
4. Наполнение базы данных partners.db согласно schema.sql;
5. Формирование аналитического отчета etl_report.txt.
"""

import csv
import datetime
import os
import re
import sqlite3
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(CURRENT_DIR, "source")
CLEANED_DIR = os.path.join(CURRENT_DIR, "cleaned")
DB_PATH = os.path.join(CURRENT_DIR, "partners.db")
SCHEMA_PATH = os.path.join(CURRENT_DIR, "schema.sql")


def parse_date_to_iso(raw_date: str) -> Optional[str]:
    """Нормализует дату из форматов ДД.ММ.ГГГГ или ГГГГ-ММ-ДД к формату СУБД YYYY-MM-DD."""
    cleaned = raw_date.strip()
    if not cleaned:
        return None

    # Попытка парсинга ГГГГ-ММ-ДД
    if re.match(r"^\d{4}-\d{2}-\d{2}$", cleaned):
        try:
            dt = datetime.datetime.strptime(cleaned, "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return None

    # Попытка парсинга ДД.ММ.ГГГГ
    if re.match(r"^\d{2}\.\d{2}\.\d{4}$", cleaned):
        try:
            dt = datetime.datetime.strptime(cleaned, "%d.%m.%Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return None

    return None


def split_type_and_name(raw_name: str) -> Tuple[str, str]:
    """Извлекает организационно-правовую форму (ООО, ИП, ТК) и чистое наименование."""
    cleaned = raw_name.strip()
    match = re.match(r"^([A-Za-zА-Яа-яЁё]+)\s*[\"«]?(.*?)[\"»]?$", cleaned)
    if match:
        p_type = match.group(1).strip()
        c_name = match.group(2).strip()
        if not c_name:
            c_name = p_type
            p_type = "ООО"
        return p_type, c_name
    return "ООО", cleaned


def run_etl() -> Dict[str, Any]:
    """Основной метод запуска ETL-процесса."""
    os.makedirs(CLEANED_DIR, exist_ok=True)

    partners_file = os.path.join(SOURCE_DIR, "import_partners.csv")
    sales_file = os.path.join(SOURCE_DIR, "import_sales.txt")

    if not os.path.exists(partners_file) or not os.path.exists(sales_file):
        raise FileNotFoundError("Исходные файлы ETL не найдены в каталоге source/")

    cleaned_partners: List[Dict[str, Any]] = []
    valid_partner_ids: Set[int] = set()

    # 1. Чтение и очистка import_partners.csv
    with open(partners_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            p_id = int(row["partner_id"].strip())
            raw_name = row["company_name"].strip()
            p_type, c_name = split_type_and_name(raw_name)
            inn = row["inn"].strip()
            email = row["contact_email"].strip()
            phone = row["phone"].strip() if row.get("phone") else ""
            raw_rating = row.get("rating", "").strip()

            try:
                # Нормализация рейтинга к неотрицательному целому числу
                rating = int(float(raw_rating)) if raw_rating else 0
                if rating < 0:
                    rating = 0
            except ValueError:
                rating = 0

            cleaned_partners.append({
                "partner_id": p_id,
                "company_name": c_name,
                "partner_type": p_type,
                "inn": inn,
                "contact_email": email,
                "phone": phone,
                "director": "Руководитель организации",
                "address": "Юридический адрес компании",
                "rating": rating,
            })
            valid_partner_ids.add(p_id)

    # 2. Чтение, очистка и фильтрация истории продаж из import_sales.txt
    cleaned_sales: List[Dict[str, Any]] = []
    rejected_sales: List[Dict[str, Any]] = []
    products_map: Dict[str, int] = {}
    product_counter = 1

    with open(sales_file, "r", encoding="utf-8") as f:
        # Файл разделен табуляциями или запятыми
        lines = [line.strip() for line in f if line.strip()]
        header = lines[0].split("\t") if "\t" in lines[0] else lines[0].split(",")
        header = [h.strip() for h in header]

        for line in lines[1:]:
            parts = line.split("\t") if "\t" in line else line.split(",")
            parts = [p.strip() for p in parts]
            if len(parts) < len(header):
                continue

            row_dict = dict(zip(header, parts))
            sale_id = int(row_dict["sale_id"])
            partner_id = int(row_dict["partner_id"])
            product_name = row_dict["product_name"]
            raw_date = row_dict["sale_date"]
            qty = int(row_dict["quantity"])
            total_amount = float(row_dict["total_amount"])
            unit_price = round(total_amount / qty, 2) if qty > 0 else 0.0

            # Проверка ссылочной целостности: существует ли partner_id в partners? (ТЗ пункт 3)
            if partner_id not in valid_partner_ids:
                row_dict["rejection_reason"] = f"Несуществующий partner_id={partner_id}"
                rejected_sales.append(row_dict)
                continue

            # Нормализация даты к формату YYYY-MM-DD (ТЗ пункт 3)
            norm_date = parse_date_to_iso(raw_date)
            if not norm_date:
                row_dict["rejection_reason"] = f"Неверный формат даты: {raw_date}"
                rejected_sales.append(row_dict)
                continue

            # Регистрация продукта в 3NF-справочнике
            if product_name not in products_map:
                products_map[product_name] = product_counter
                product_counter += 1

            product_id = products_map[product_name]

            cleaned_sales.append({
                "sale_id": sale_id,
                "partner_id": partner_id,
                "product_id": product_id,
                "product_name": product_name,
                "sale_date": norm_date,
                "quantity": qty,
                "unit_price": unit_price,
            })

    # 3. Сохранение чистых CSV в папку cleaned/
    # partners.csv
    partners_csv_path = os.path.join(CLEANED_DIR, "partners.csv")
    with open(partners_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["partner_id", "company_name", "partner_type", "inn", "contact_email", "phone", "director", "address", "rating"])
        writer.writeheader()
        writer.writerows(cleaned_partners)

    # products.csv
    products_csv_path = os.path.join(CLEANED_DIR, "products.csv")
    with open(products_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["product_id", "product_name"])
        for pname, pid in products_map.items():
            writer.writerow([pid, pname])

    # sales_history.csv
    sales_csv_path = os.path.join(CLEANED_DIR, "sales_history.csv")
    with open(sales_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["sale_id", "partner_id", "product_id", "sale_date", "quantity", "unit_price"])
        writer.writeheader()
        for s in cleaned_sales:
            writer.writerow({
                "sale_id": s["sale_id"],
                "partner_id": s["partner_id"],
                "product_id": s["product_id"],
                "sale_date": s["sale_date"],
                "quantity": s["quantity"],
                "unit_price": s["unit_price"],
            })

    # rejected_sales.csv
    rejected_csv_path = os.path.join(CLEANED_DIR, "rejected_sales.csv")
    if rejected_sales:
        with open(rejected_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rejected_sales[0].keys()))
            writer.writeheader()
            writer.writerows(rejected_sales)

    # 4. Загрузка в SQLite базу данных
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as sf:
        conn.executescript(sf.read())

    cursor = conn.cursor()
    # Справочники типов для калькулятора материалов
    cursor.executemany(
        "INSERT OR IGNORE INTO product_types (type_id, type_name, coefficient) VALUES (?, ?, ?);",
        [
            (1, "Ламинат", 1.10),
            (2, "Паркетная доска", 2.50),
            (3, "Массивная доска", 8.43),
            (4, "Пробковое покрытие", 1.50),
        ],
    )
    cursor.executemany(
        "INSERT OR IGNORE INTO material_types (type_id, type_name, defect_percent) VALUES (?, ?, ?);",
        [
            (1, "Тип материала 1", 0.10),
            (2, "Тип материала 2", 0.95),
            (3, "Тип материала 3", 0.28),
            (4, "Тип материала 4", 0.55),
            (5, "Тип материала 5", 0.34),
        ],
    )

    # Очистка и вставка нормализованных данных
    cursor.execute("DELETE FROM sales_history;")
    cursor.execute("DELETE FROM products;")
    cursor.execute("DELETE FROM partners;")

    cursor.executemany(
        """
        INSERT INTO partners (partner_id, company_name, partner_type, inn, contact_email, phone, director, address, rating)
        VALUES (:partner_id, :company_name, :partner_type, :inn, :contact_email, :phone, :director, :address, :rating);
        """,
        cleaned_partners,
    )

    cursor.executemany(
        "INSERT INTO products (product_id, product_name) VALUES (?, ?);",
        [(pid, pname) for pname, pid in products_map.items()],
    )

    cursor.executemany(
        """
        INSERT INTO sales_history (sale_id, partner_id, product_id, sale_date, quantity, unit_price)
        VALUES (:sale_id, :partner_id, :product_id, :sale_date, :quantity, :unit_price);
        """,
        cleaned_sales,
    )
    conn.commit()
    conn.close()

    # 5. Формирование текстового отчета etl_report.txt
    report_path = os.path.join(CLEANED_DIR, "etl_report.txt")
    report_content = (
        "=======================================================\n"
        "ОТЧЕТ О ВЫПОЛНЕНИИ ETL-КОНВЕЙЕРА (ОЧИСТКА И ИМПОРТ 3NF)\n"
        "=======================================================\n"
        f"Дата и время обработки: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Импортировано партнеров: {len(cleaned_partners)}\n"
        f"Импортировано товаров в номенклатуру: {len(products_map)}\n"
        f"Успешно загружено продаж: {len(cleaned_sales)}\n"
        f"Отклонено некорректных записей: {len(rejected_sales)}\n"
        "-------------------------------------------------------\n"
        "Детали отклоненных записей:\n"
    )
    for rej in rejected_sales:
        report_content += f"  - ID продажи {rej.get('sale_id')}: {rej.get('rejection_reason')}\n"
    report_content += "=======================================================\n"

    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write(report_content)

    return {
        "partners_count": len(cleaned_partners),
        "products_count": len(products_map),
        "sales_count": len(cleaned_sales),
        "rejected_count": len(rejected_sales),
    }


if __name__ == "__main__":
    stats = run_etl()
    print("ETL процесс успешно завершен:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
