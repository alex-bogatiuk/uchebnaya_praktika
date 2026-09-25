"""Модуль централизованного логирования системных событий и ошибок в файл app.log."""

import logging
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(CURRENT_DIR, "app.log")


def setup_logger(name: str = "CRM_App") -> logging.Logger:
    """Настраивает и возвращает регистратор событий с записью в app.log."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Формат: Дата, время, уровень, модуль, текст сообщения (ТЗ пункт 3)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Файловый обработчик
        file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Консольный обработчик
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


# Экземпляр логгера по умолчанию
app_logger = setup_logger()
