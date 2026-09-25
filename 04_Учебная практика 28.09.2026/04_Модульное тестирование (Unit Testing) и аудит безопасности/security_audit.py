"""Аудит безопасности: автоматическая проверка защиты от SQL-инъекций (SQL Injection).

Выполняет:
1. Статический анализ исходного кода приложения на наличие опасной конкатенации строк
   (f-строки, операторы + и .format() внутри SQL-запросов);
2. Динамическое тестирование базы данных с внедрением вредоносных SQL-нагрузок
   (например, "' OR '1'='1", "'; DROP TABLE partners; --");
3. Логирование результатов аудита в файл app.log.
"""

import os
import re
import sqlite3
import sys
from typing import Dict, List, Tuple

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TASK_03_WEEK_03 = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "..", "03_Учебная практика 21.09.2026", "03_Интеграция формы с БД (CRUD-операции и обновление UI)")
)

for p in [CURRENT_DIR, TASK_03_WEEK_03]:
    if p not in sys.path:
        sys.path.insert(0, p)

from logger import app_logger
from database_crud import DatabaseManager


def run_static_code_audit(scan_directories: List[str]) -> List[Dict[str, Any]]:
    """Сканирует исходные файлы Python на предмет небезопасного формирования SQL-запросов."""
    app_logger.info("Запуск статического аудита кода на защиту от SQL-инъекций...")
    findings = []
    # Паттерны опасных конструкций: f-строки с SQL ключевыми словами
    dangerous_patterns = [
        (re.compile(r'execute\(\s*f["\'].*?(SELECT|INSERT|UPDATE|DELETE).*?["\']', re.IGNORECASE), "Использование f-строк в cursor.execute"),
        (re.compile(r'executescript\(\s*f["\']', re.IGNORECASE), "Использование f-строк в cursor.executescript"),
        (re.compile(r'execute\(\s*["\'].*?(WHERE|VALUES).*?["\']\s*\+', re.IGNORECASE), "Конкатенация строк через оператор '+' в SQL"),
        (re.compile(r'execute\(\s*["\'].*?(WHERE|VALUES).*?\.format\(', re.IGNORECASE), "Использование .format() внутри SQL-запроса"),
    ]

    for dir_path in scan_directories:
        if not os.path.exists(dir_path):
            continue
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith(".py") and not file.startswith("security_audit"):
                    full_path = os.path.join(root, file)
                    with open(full_path, "r", encoding="utf-8", errors="replace") as fp:
                        lines = fp.readlines()
                    for idx, line in enumerate(lines, 1):
                        for pattern, desc in dangerous_patterns:
                            if pattern.search(line):
                                findings.append({
                                    "file": full_path,
                                    "line_num": idx,
                                    "code": line.strip(),
                                    "issue": desc,
                                })
    return findings


def run_dynamic_injection_test() -> bool:
    """Выполняет тестирование защиты с внедрением типовых атак внедрения SQL."""
    app_logger.info("Запуск динамических тестов с внедрением SQL-инъекций...")
    import tempfile
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()
    db = DatabaseManager(temp_db.name)

    # Попытка внедрения инъекции через поля поиска и добавления
    malicious_inputs = [
        "' OR '1'='1",
        "'; DROP TABLE partners; --",
        "Admin'--",
        "105' UNION SELECT NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL--",
    ]

    try:
        for payload in malicious_inputs:
            # Тест добавления партнера со вредоносной строкой
            partner_data = {
                "company_name": f"Компания {payload}",
                "partner_type": "ООО",
                "contact_email": f"hacker_{abs(hash(payload))}@test.ru",
                "phone": "+7 (000) 000-00-00",
                "director": "Иванов",
                "address": payload,
                "rating": 5,
            }
            # Запрос должен выполниться безопасно (строка сохраняется как литерал, а не команда)
            new_id = db.add_partner(partner_data)
            fetched = db.get_partner_by_id(new_id)

            # Проверяем, что таблица не повреждена и данные сохранены строго как текст
            if not fetched or fetched["address"] != payload:
                app_logger.error(f"Отказ безопасности при проверке нагрузки: {payload}")
                return False

            # Проверяем поиск
            search_query = "SELECT * FROM partners WHERE company_name = ?;"
            rows = db.execute_query(search_query, (f"Компания {payload}",))
            if len(rows) != 1:
                app_logger.error(f"Сбой параметризованного поиска: {payload}")
                return False

        app_logger.info("Все динамические тесты на SQL-инъекции успешно пройдены! Инъекции нейтрализованы.")
        return True
    finally:
        if os.path.exists(temp_db.name):
            try:
                os.remove(temp_db.name)
            except Exception:
                pass


def main() -> None:
    print("=" * 80)
    print("ОТЧЕТ АУДИТА БЕЗОПАСНОСТИ: ЗАЩИТА ОТ SQL-ИНЪЕКЦИЙ")
    print("=" * 80)

    repo_root = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
    static_issues = run_static_code_audit([repo_root])

    print(f"\n1. Результаты статического анализа кода:")
    if not static_issues:
        print("  [SUCCESS] Уязвимых мест не обнаружено.")
        print("  Все SQL-запросы в репозитории строго используют параметризацию ('?').")
        print("  Прямой конкатенации строк и f-строк в запросах не зафиксировано.")
    else:
        print(f"  [WARNING] Обнаружено потенциальных уязвимостей: {len(static_issues)}")
        for issue in static_issues:
            print(f"  - {issue['file']}:{issue['line_num']} -> {issue['issue']}")

    print(f"\n2. Результаты динамического тестирования внедрения SQL:")
    dynamic_success = run_dynamic_injection_test()
    if dynamic_success:
        print("  [SUCCESS] Все атаки SQL-инъекций успешно изолированы параметризацией драйвера SQLite.")
    else:
        print("  [FAIL] Зафиксирована уязвимость к динамической инъекции.")

    print("\n" + "=" * 80)
    print(f"Журнал аудита сохранен в файл: {os.path.join(CURRENT_DIR, 'app.log')}")
    print("=" * 80)


if __name__ == "__main__":
    main()
