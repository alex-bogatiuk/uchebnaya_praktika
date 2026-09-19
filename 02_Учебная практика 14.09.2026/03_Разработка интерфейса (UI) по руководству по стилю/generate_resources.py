"""Генератор корпоративного логотипа и иконки приложения в чистом Python.
Использует только стандартные библиотеки zlib, struct.
"""

import os
import struct
import zlib


def create_png(width: int, height: int, pixels_rgba: bytes) -> bytes:
    """Создает валидный PNG файл из RGBA байтов без сторонних библиотек."""

    def make_chunk(chunk_type: bytes, data: bytes) -> bytes:
        length = struct.pack(">I", len(data))
        chunk = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)
        return length + chunk + crc

    # Заголовок PNG
    header = b"\x89PNG\r\n\x1a\n"

    # IHDR
    ihdr_data = struct.pack(
        ">IIBBBBB",
        width,
        height,
        8,  # bit depth
        6,  # RGBA
        0,  # compression
        0,  # filter
        0,  # interlace
    )
    ihdr_chunk = make_chunk(b"IHDR", ihdr_data)

    # Scanlines с нулевым фильтром (filter byte 0)
    raw_scanlines = bytearray()
    row_stride = width * 4
    for y in range(height):
        raw_scanlines.append(0)  # filter type None
        raw_scanlines.extend(pixels_rgba[y * row_stride : (y + 1) * row_stride])

    compressed_idat = zlib.compress(bytes(raw_scanlines), 9)
    idat_chunk = make_chunk(b"IDAT", compressed_idat)
    iend_chunk = make_chunk(b"IEND", b"")

    return header + ihdr_chunk + idat_chunk + iend_chunk


def generate_logo_rgba(width: int, height: int) -> bytes:
    """Генерирует стильный корпоративный логотип с эмблемой и градиентом."""
    pixels = bytearray(width * height * 4)
    # Корпоративные цвета: глубокий темно-синий/индиго #1E293B и акцентный лазурный #0284C7
    for y in range(height):
        for x in range(width):
            idx = (y * width + x) * 4
            # Фон: прозрачный
            r, g, b, a = 0, 0, 0, 0

            # Рисуем скругленный прямоугольный бэйдж эмблемы
            badge_size = 44
            bx, by = 6, (height - badge_size) // 2
            if bx <= x < bx + badge_size and by <= y < by + badge_size:
                dx = x - (bx + badge_size // 2)
                dy = y - (by + badge_size // 2)
                dist_sq = dx * dx + dy * dy
                if dist_sq < (badge_size // 2) ** 2:
                    # Градиент внутри эмблемы
                    factor = (x + y) / (width + height)
                    r = int(14 + factor * 20)
                    g = int(116 + factor * 40)
                    b = int(144 + factor * 70)
                    a = 255

                    # Буква 'P' или геометрический символ внутри эмблемы
                    # Вертикальная стойка
                    if (
                        bx + 14 <= x <= bx + 19
                        and by + 10 <= y <= by + badge_size - 10
                    ):
                        r, g, b, a = 255, 255, 255, 255
                    # Верхняя петля 'P'
                    elif (
                        bx + 19 < x <= bx + 30
                        and (by + 10 <= y <= by + 14 or by + 22 <= y <= by + 26)
                    ):
                        r, g, b, a = 255, 255, 255, 255
                    elif bx + 27 <= x <= bx + 31 and by + 12 <= y <= by + 24:
                        r, g, b, a = 255, 255, 255, 255

            pixels[idx] = r
            pixels[idx + 1] = g
            pixels[idx + 2] = b
            pixels[idx + 3] = a

    return bytes(pixels)


def generate_icon_rgba(size: int = 32) -> bytes:
    """Генерирует иконку приложения 32x32."""
    pixels = bytearray(size * size * 4)
    radius = size // 2 - 1
    cx, cy = size // 2, size // 2

    for y in range(size):
        for x in range(size):
            idx = (y * size + x) * 4
            dx = x - cx
            dy = y - cy
            dist_sq = dx * dx + dy * dy

            if dist_sq <= radius * radius:
                # Градиентный фон иконки
                r = int(30 + (x / size) * 40)
                g = int(58 + (y / size) * 50)
                b = int(138 + (x / size) * 60)
                a = 255

                # Символ "P" (Partner) в центре
                if cx - 5 <= x <= cx - 2 and cy - 8 <= y <= cy + 8:
                    r, g, b = 255, 255, 255
                elif cx - 2 < x <= cx + 6 and (
                    cy - 8 <= y <= cy - 5 or cy - 1 <= y <= cy + 2
                ):
                    r, g, b = 255, 255, 255
                elif cx + 3 <= x <= cx + 6 and cy - 7 <= y <= cy + 1:
                    r, g, b = 255, 255, 255
            else:
                r, g, b, a = 0, 0, 0, 0

            pixels[idx] = r
            pixels[idx + 1] = g
            pixels[idx + 2] = b
            pixels[idx + 3] = a

    return bytes(pixels)


def create_ico_from_png(png_data: bytes, width: int, height: int) -> bytes:
    """Создает валидный Windows .ico файл из PNG данных."""
    # ICO Header: Reserved (2 bytes = 0), Type (2 bytes = 1 for icon), Count (2 bytes = 1)
    ico_header = struct.pack("<HHH", 0, 1, 1)
    # Directory entry: Width, Height, Colors (0=no palette), Reserved, Planes (1), BPP (32), Size (4 bytes), Offset (4 bytes)
    offset = 6 + 16  # header (6) + 1 entry (16)
    ico_entry = struct.pack(
        "<BBBBHHII",
        width if width < 256 else 0,
        height if height < 256 else 0,
        0,
        0,
        1,
        32,
        len(png_data),
        offset,
    )
    return ico_header + ico_entry + png_data


def main() -> None:
    res_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
    os.makedirs(res_dir, exist_ok=True)

    # Логотип (ширина 56, высота 56)
    logo_rgba = generate_logo_rgba(56, 56)
    logo_png = create_png(56, 56, logo_rgba)
    with open(os.path.join(res_dir, "logo.png"), "wb") as f:
        f.write(logo_png)

    # Иконка (32x32)
    icon_rgba = generate_icon_rgba(32)
    icon_png = create_png(32, 32, icon_rgba)
    with open(os.path.join(res_dir, "icon.png"), "wb") as f:
        f.write(icon_png)

    # Windows ICO
    icon_ico = create_ico_from_png(icon_png, 32, 32)
    with open(os.path.join(res_dir, "icon.ico"), "wb") as f:
        f.write(icon_ico)

    print("Ресурсы успешно сгенерированы в:", res_dir)


if __name__ == "__main__":
    main()
