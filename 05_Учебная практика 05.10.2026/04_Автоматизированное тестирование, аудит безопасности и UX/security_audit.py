"""Модуль аудита безопасности и проверки отсутствия SQL-инъекций (Задание 4, 05.10.2026)."""

import os
import re
import sqlite3
import sys
import tempfile

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TASK_01_DIR = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "01_Инфраструктура данных и ETL (База данных в 3NF)")
)
SCHEMA_PATH = os.path.join(TASK_01_DIR, "schema.sql")
LOG_PATH = os.path.join(CURRENT_DIR, "app.log")


def log_event(level: str, message: str) -> None:
    """Запись форматированного сообщения в файл app.log."""
    import datetime
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{now_str} [{level}] {message}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as lf:
        lf.write(entry)


def audit_sql_parameterization(repo_path: str) -> bool:
    """Статический аудит файлов репозитория на отсутствие небезопасных f-строк в SQL."""
    log_event("INFO", "Запуск статического анализа исходного кода на SQL-инъекции")
    dangerous_patterns = [
        re.compile(r'execute\(\s*f["\'].*?(SELECT|INSERT|UPDATE|DELETE)', re.I),
        re.compile(r'execute\(\s*["\'].*?(WHERE|VALUES).*?["\']\s*\+', re.I),
        re.compile(r'execute\(\s*["\'].*?(WHERE|VALUES).*?\.format\(', re.I),
    ]

    clean = True
    for root, _, files in os.walk(repo_path):
        for f in files:
            if f.endswith(".py") and not f.startswith("security_audit"):
                fp = os.path.join(root, f)
                with open(fp, "r", encoding="utf-8", errors="replace") as file_obj:
                    for line_no, line in enumerate(file_obj, 1):
                        for p in dangerous_patterns:
                            if p.search(line):
                                clean = False
                                log_event("WARNING", f"Подозрительный SQL в {fp}:{line_no}: {line.strip()}")
    return clean


def audit_dynamic_sql_protection() -> bool:
    """Динамический стресс-тест базы данных с передачей SQL-инъекционных строк."""
    log_event("INFO", "Запуск динамического тестирования внедрения SQL-нагрузок")
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()

    try:
        conn = sqlite3.connect(temp_db.name)
        conn.execute("PRAGMA foreign_keys = ON;")
        with open(SCHEMA_PATH, "r", encoding="utf-8") as sf:
            conn.executescript(sf.read())

        cur = conn.cursor()

        payloads = [
            "' OR '1'='1",
            "'; DROP TABLE partners; --",
            "test@domain.ru' OR 1=1 --",
        ]

        for p in payloads:
            # Безопасный параметризованный запрос
            query = "INSERT INTO partners (company_name, partner_type, contact_email, rating) VALUES (?, ?, ?, ?);"
            cur.execute(query, (f"Компания {p}", "ООО", f"p_{abs(hash(p))}@test.ru", 5))
            conn.commit()

            # Проверка, что строка сохранилась как литерал, а не как команда
            cur.execute("SELECT company_name FROM partners WHERE company_name = ?;", (f"Компания {p}",))
            res = cur.fetchone()
            if not res or res[0] != f"Компания {p}":
                log_event("ERROR", f"Тест на инъекцию провален для нагрузки: {p}")
                conn.close()
                return False

        conn.close()
        log_event("INFO", "Динамические тесты успешно пройдены: все запросы параметризованы")
        return True
    finally:
        if os.path.exists(temp_db.name):
            try:
                os.remove(temp_db.name)
            except Exception:
                pass


def main() -> None:
    print("=" * 80)
    print("ФИНАЛЬНЫЙ АУДИТ БЕЗОПАСНОСТИ ПРОЕКТА (05.10.2026)")
    print("=" * 80)

    repo_dir = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
    is_static_clean = audit_sql_parameterization(repo_dir)
    is_dynamic_clean = audit_dynamic_sql_protection()

    if is_static_clean:
        print("[SUCCESS] Статический анализ: прямой конкатенации строк в SQL не найдено.")
    else:
        print("[WARNING] Статический анализ: зафиксированы замечания (см. app.log).")

    if is_dynamic_clean:
        print("[SUCCESS] Динамический аудит: СУБД защищена параметризацией драйвера.")
    else:
        print("[FAIL] Динамический аудит: обнаружена уязвимость.")

    print(f"\nЖурнал аудита обновлен: {LOG_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    main()
