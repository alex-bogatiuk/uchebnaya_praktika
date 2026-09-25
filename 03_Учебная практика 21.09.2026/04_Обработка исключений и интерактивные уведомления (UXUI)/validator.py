"""Модуль валидации пользовательского ввода и обработки исключений (UX/UI)."""

import re
from typing import Any, Dict


class ValidationError(Exception):
    """Исключение, возникающее при нарушении правил валидации полей формы."""

    def __init__(self, message: str, remediation_steps: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.remediation_steps = remediation_steps

    def get_full_message(self) -> str:
        """Возвращает форматированный текст ошибки с инструкцией по исправлению."""
        if self.remediation_steps:
            return f"{self.message}\n\nПорядок действий:\n{self.remediation_steps}"
        return self.message


def validate_partner_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Проверяет корректность введенных данных партнера перед отправкой в БД.

    Правила:
    1. Наименование компании обязательно для заполнения.
    2. Email обязателен и должен соответствовать валидному формату адреса.
    3. Рейтинг должен быть строго целым неотрицательным числом (>= 0).

    Возвращает:
        Dict[str, Any]: Очищенные нормализованные данные.

    Исключения:
        ValidationError: При выявлении некорректного значения.
    """
    company_name = str(data.get("company_name", "")).strip()
    if not company_name:
        raise ValidationError(
            "Поле 'Наименование компании' не может быть пустым.",
            "1. Введите официальное или коммерческое наименование организации.\n"
            "2. Повторите попытку сохранения.",
        )

    contact_email = str(data.get("contact_email", "")).strip()
    if not contact_email:
        raise ValidationError(
            "Поле 'Электронная почта (Email)' обязательно для заполнения.",
            "1. Укажите действующий адрес корпоративной или личной почты.\n"
            "2. Адрес должен содержать символ '@' и доменную зону (например: info@domain.ru).",
        )

    # Проверка формата Email по регулярному выражению
    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not re.match(email_pattern, contact_email):
        raise ValidationError(
            f"Введен некорректный адрес электронной почты: '{contact_email}'.",
            "1. Убедитесь в отсутствии пробелов и спецсимволов.\n"
            "2. Проверьте правильность написания доменного имени (например: partner@mail.ru).",
        )

    raw_rating = data.get("rating", "")
    try:
        # Проверяем, является ли значение целым числом
        if isinstance(raw_rating, str):
            clean_rating_str = raw_rating.strip()
            if not clean_rating_str:
                rating = 0
            else:
                # Если строка содержит точку или запятую, это вещественное число, что недопустимо по ТЗ
                if "." in clean_rating_str or "," in clean_rating_str:
                    raise ValueError("Дробное число")
                rating = int(clean_rating_str)
        elif isinstance(raw_rating, (int, float)):
            if isinstance(raw_rating, float) and not raw_rating.is_integer():
                raise ValueError("Дробное число")
            rating = int(raw_rating)
        else:
            raise ValueError("Неизвестный тип данных")

        if rating < 0:
            raise ValueError("Отрицательное число")
    except (ValueError, TypeError):
        raise ValidationError(
            "Рейтинг должен быть целым неотрицательным числом от 0 и выше.",
            "1. Удалите знаки препинания, точки, запятые и пробелы.\n"
            "2. Введите только целые цифры (например: 0, 5, 10, 42).\n"
            "3. Повторите попытку сохранения.",
        )

    cleaned_payload = dict(data)
    cleaned_payload["company_name"] = company_name
    cleaned_payload["contact_email"] = contact_email
    cleaned_payload["rating"] = rating
    cleaned_payload["partner_type"] = str(data.get("partner_type", "ООО")).strip()
    cleaned_payload["phone"] = str(data.get("phone", "")).strip()
    cleaned_payload["director"] = str(data.get("director", "")).strip()
    cleaned_payload["address"] = str(data.get("address", "")).strip()

    return cleaned_payload
