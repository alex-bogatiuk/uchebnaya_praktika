"""Модульные тесты валидации ввода и обработки исключений UX/UI (Задание 4)."""

import os
import sys
import unittest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from validator import ValidationError, validate_partner_payload


class TestValidationAndExceptions(unittest.TestCase):
    """Тестирование правил валидации и генерации информативных исключений."""

    def test_valid_payload_success(self) -> None:
        """Проверка успешной валидации корректных данных."""
        raw_data = {
            "company_name": "  ООО 'Мастер Снаб'  ",
            "partner_type": "ООО",
            "contact_email": "  snab@master.ru  ",
            "rating": "5",
            "phone": "+7 (999) 000-00-00",
            "director": "Иванов И.И.",
            "address": "г. Москва, ул. Мира, 1",
        }
        cleaned = validate_partner_payload(raw_data)
        self.assertEqual(cleaned["company_name"], "ООО 'Мастер Снаб'")
        self.assertEqual(cleaned["contact_email"], "snab@master.ru")
        self.assertEqual(cleaned["rating"], 5)

    def test_empty_company_name_raises_error(self) -> None:
        """Проверка блокировки пустого наименования компании."""
        payload = {
            "company_name": "   ",
            "contact_email": "test@test.ru",
            "rating": 0,
        }
        with self.assertRaises(ValidationError) as ctx:
            validate_partner_payload(payload)
        self.assertIn("Наименование компании", str(ctx.exception))
        self.assertIn("Порядок действий", ctx.exception.get_full_message())

    def test_invalid_email_formats_raise_error(self) -> None:
        """Проверка блокировки некорректных форматов почты."""
        bad_emails = ["", "   ", "plainaddress", "missing_at.domain.com", "user@nodomain", "user@domain."]
        for email in bad_emails:
            with self.subTest(email=email):
                payload = {
                    "company_name": "ООО Тест",
                    "contact_email": email,
                    "rating": 1,
                }
                with self.assertRaises(ValidationError) as ctx:
                    validate_partner_payload(payload)
                self.assertTrue(
                    "почт" in ctx.exception.get_full_message().lower()
                    or "email" in ctx.exception.get_full_message().lower()
                )

    def test_negative_rating_raises_error(self) -> None:
        """Проверка блокировки отрицательного рейтинга."""
        payload = {
            "company_name": "ООО Тест",
            "contact_email": "test@company.ru",
            "rating": -5,
        }
        with self.assertRaises(ValidationError) as ctx:
            validate_partner_payload(payload)
        self.assertIn("целым неотрицательным числом", ctx.exception.get_full_message())

    def test_float_rating_raises_error(self) -> None:
        """Проверка блокировки дробного рейтинга по ТЗ (строго целое число)."""
        bad_ratings = [4.8, "4.8", "3,5", "4.01"]
        for rate in bad_ratings:
            with self.subTest(rate=rate):
                payload = {
                    "company_name": "ООО Тест",
                    "contact_email": "test@company.ru",
                    "rating": rate,
                }
                with self.assertRaises(ValidationError) as ctx:
                    validate_partner_payload(payload)
                self.assertIn("целым неотрицательным числом", ctx.exception.get_full_message())

    def test_string_non_numeric_rating_raises_error(self) -> None:
        """Проверка блокировки нечисловых символов в рейтинге."""
        payload = {
            "company_name": "ООО Тест",
            "contact_email": "test@company.ru",
            "rating": "пять звезд",
        }
        with self.assertRaises(ValidationError) as ctx:
            validate_partner_payload(payload)
        self.assertIn("целым неотрицательным числом", ctx.exception.get_full_message())


if __name__ == "__main__":
    unittest.main()
