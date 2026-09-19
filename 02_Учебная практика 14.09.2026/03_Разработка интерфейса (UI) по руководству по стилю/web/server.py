"""Локальный HTTP/API сервер для асинхронного взаимодействия с веб-интерфейсом.

Предоставляет:
- Раздачу статических файлов веб-интерфейса (HTML, CSS, JS, картинки);
- REST API эндпоинт GET /api/partners для получения списка партнеров с рассчитанной скидкой.
"""

import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_02_DIR = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "..", "02_Интеграция с БД и агрегация данных (SQL + Backend)")
)
if MODULE_02_DIR not in sys.path:
    sys.path.insert(0, MODULE_02_DIR)

from database import DatabaseManager  # noqa: E402


class CRMRequestHandler(SimpleHTTPRequestHandler):
    """Кастомный HTTP-обработчик с поддержкой JSON API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(CURRENT_DIR), **kwargs)

    def do_GET(self) -> None:
        """Обработка GET запросов."""
        if self.path == "/api/partners":
            db = DatabaseManager()
            partners = db.get_all_partners_with_discounts()

            response_bytes = json.dumps(partners, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(response_bytes)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(response_bytes)
            return

        if self.path in ("/", "/index.html"):
            self.path = "/web/index.html"

        return super().do_GET()


def run_server(port: int = 8000) -> None:
    """Запуск локального сервера."""
    server_address = ("", port)
    httpd = HTTPServer(server_address, CRMRequestHandler)
    print(f"Сервер CRM запущен: http://localhost:{port}/web/index.html")
    print(f"API эндпоинт: http://localhost:{port}/api/partners")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
