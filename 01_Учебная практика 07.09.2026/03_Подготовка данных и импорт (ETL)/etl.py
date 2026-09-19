from __future__ import annotations

import csv
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = BASE_DIR / "source"
CLEANED_DIR = BASE_DIR / "cleaned"

PARTNERS_SOURCE = SOURCE_DIR / "import_partners.csv"
SALES_SOURCE = SOURCE_DIR / "import_sales.txt"

CLEANED_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(value: str | None) -> str | None:
    """Удаляет пробелы по краям и превращает пустую строку в None."""
    if value is None:
        return None
    value = value.strip()
    return value or None


def normalize_phone(value: str | None) -> str | None:
    """Приводит российские номера к виду +7XXXXXXXXXX, если это возможно."""
    value = clean_text(value)
    if value is None:
        return None

    digits = re.sub(r"\D", "", value)

    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]

    if len(digits) == 11 and digits.startswith("7"):
        return "+" + digits

    # Для учебного ETL оставляем международный номер в очищенном виде.
    return "+" + digits if digits else None


def normalize_date(value: str) -> str:
    """Поддерживает ISO и формат DD.MM.YYYY, возвращает YYYY-MM-DD."""
    value = value.strip()
    for date_format in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, date_format).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"некорректный формат даты: {value}")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def extract_and_clean_partners() -> tuple[list[dict], list[dict]]:
    cleaned: list[dict] = []
    rejected: list[dict] = []

    seen_ids: set[int] = set()
    seen_inn: set[str] = set()
    seen_emails: set[str] = set()

    with PARTNERS_SOURCE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for source_row in reader:
            try:
                partner_id = int(source_row["partner_id"])
                company_name = clean_text(source_row.get("company_name"))
                inn = clean_text(source_row.get("inn"))
                contact_email = clean_text(source_row.get("contact_email"))
                phone = normalize_phone(source_row.get("phone"))
                rating_raw = clean_text(source_row.get("rating"))

                if not company_name:
                    raise ValueError("company_name пуст")
                if not inn:
                    raise ValueError("inn пуст")
                if not contact_email:
                    raise ValueError("contact_email пуст")
                if "@" not in contact_email:
                    raise ValueError("некорректный email")

                contact_email = contact_email.lower()

                if partner_id in seen_ids:
                    raise ValueError("дубликат partner_id")
                if inn in seen_inn:
                    raise ValueError("дубликат inn")
                if contact_email in seen_emails:
                    raise ValueError("дубликат contact_email")

                rating = None
                if rating_raw is not None:
                    try:
                        rating = Decimal(rating_raw).quantize(Decimal("0.1"))
                    except InvalidOperation as exc:
                        raise ValueError("некорректный rating") from exc
                    if not Decimal("0") <= rating <= Decimal("5"):
                        raise ValueError("rating должен быть от 0 до 5")

                cleaned.append(
                    {
                        "partner_id": partner_id,
                        "company_name": company_name,
                        "inn": inn,
                        "contact_email": contact_email,
                        "phone": phone,
                        "rating": "" if rating is None else str(rating),
                    }
                )

                seen_ids.add(partner_id)
                seen_inn.add(inn)
                seen_emails.add(contact_email)

            except Exception as exc:
                rejected.append(
                    {
                        **source_row,
                        "reject_reason": str(exc),
                    }
                )

    return cleaned, rejected


def extract_and_clean_sales(
    valid_partner_ids: set[int],
) -> tuple[list[dict], list[dict], list[dict]]:
    """Возвращает products, deliveries и отклоненные продажи."""
    raw_valid_sales: list[dict] = []
    rejected_sales: list[dict] = []
    seen_sale_ids: set[int] = set()

    with SALES_SOURCE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter="\t")

        for source_row in reader:
            try:
                sale_id = int(source_row["sale_id"])
                partner_id = int(source_row["partner_id"])
                product_name = clean_text(source_row.get("product_name"))
                delivery_date = normalize_date(source_row["sale_date"])
                quantity = int(source_row["quantity"])
                total_amount = Decimal(source_row["total_amount"])

                if sale_id in seen_sale_ids:
                    raise ValueError("дубликат sale_id")
                if partner_id not in valid_partner_ids:
                    raise ValueError(
                        f"partner_id={partner_id} отсутствует в очищенном справочнике partners"
                    )
                if not product_name:
                    raise ValueError("product_name пуст")
                if quantity <= 0:
                    raise ValueError("quantity должен быть > 0")
                if total_amount < 0:
                    raise ValueError("total_amount не может быть отрицательным")

                unit_price = (total_amount / Decimal(quantity)).quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_UP
                )

                raw_valid_sales.append(
                    {
                        "sale_id": sale_id,
                        "partner_id": partner_id,
                        "product_name": product_name,
                        "delivery_date": delivery_date,
                        "quantity": quantity,
                        "unit_price": unit_price,
                    }
                )
                seen_sale_ids.add(sale_id)

            except Exception as exc:
                rejected_sales.append(
                    {
                        **source_row,
                        "reject_reason": str(exc),
                    }
                )

    # Формируем отдельный справочник products.
    product_id_by_name: dict[str, int] = {}
    products: list[dict] = []

    for sale in raw_valid_sales:
        product_name = sale["product_name"]
        if product_name not in product_id_by_name:
            product_id = len(product_id_by_name) + 1
            product_id_by_name[product_name] = product_id
            products.append(
                {
                    "product_id": product_id,
                    "product_name": product_name,
                }
            )

    deliveries: list[dict] = []
    for sale in raw_valid_sales:
        deliveries.append(
            {
                "delivery_id": sale["sale_id"],
                "partner_id": sale["partner_id"],
                "product_id": product_id_by_name[sale["product_name"]],
                "delivery_date": sale["delivery_date"],
                "quantity": sale["quantity"],
                "unit_price": str(sale["unit_price"]),
            }
        )

    return products, deliveries, rejected_sales


def main() -> None:
    partners, rejected_partners = extract_and_clean_partners()
    valid_partner_ids = {row["partner_id"] for row in partners}

    products, deliveries, rejected_sales = extract_and_clean_sales(valid_partner_ids)

    write_csv(
        CLEANED_DIR / "partners.csv",
        ["partner_id", "company_name", "inn", "contact_email", "phone", "rating"],
        partners,
    )

    write_csv(
        CLEANED_DIR / "products.csv",
        ["product_id", "product_name"],
        products,
    )

    write_csv(
        CLEANED_DIR / "deliveries.csv",
        [
            "delivery_id",
            "partner_id",
            "product_id",
            "delivery_date",
            "quantity",
            "unit_price",
        ],
        deliveries,
    )

    write_csv(
        CLEANED_DIR / "rejected_partners.csv",
        [
            "partner_id",
            "company_name",
            "inn",
            "contact_email",
            "phone",
            "rating",
            "reject_reason",
        ],
        rejected_partners,
    )

    write_csv(
        CLEANED_DIR / "rejected_sales.csv",
        [
            "sale_id",
            "partner_id",
            "product_name",
            "sale_date",
            "quantity",
            "total_amount",
            "reject_reason",
        ],
        rejected_sales,
    )

    report_lines = [
        "ETL REPORT",
        "==========",
        f"Partners loaded: {len(partners)}",
        f"Partners rejected: {len(rejected_partners)}",
        f"Products created: {len(products)}",
        f"Deliveries loaded: {len(deliveries)}",
        f"Sales rejected: {len(rejected_sales)}",
        "",
        "Transformations:",
        "- leading/trailing spaces removed",
        "- empty strings converted to NULL/empty CSV fields",
        "- emails normalized to lowercase",
        "- phones normalized",
        "- dates normalized to YYYY-MM-DD",
        "- duplicate partner_id/inn/email checks performed",
        "- duplicate sale_id checks performed",
        "- product dictionary extracted from sales",
        "- unit_price calculated as total_amount / quantity",
        "- rows with invalid foreign keys rejected",
        "",
        "Rejected sales:",
    ]

    if rejected_sales:
        for row in rejected_sales:
            report_lines.append(
                f"- sale_id={row.get('sale_id', '')}: {row.get('reject_reason', '')}"
            )
    else:
        report_lines.append("- none")

    (CLEANED_DIR / "etl_report.txt").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )

    print("\n".join(report_lines))


if __name__ == "__main__":
    main()
