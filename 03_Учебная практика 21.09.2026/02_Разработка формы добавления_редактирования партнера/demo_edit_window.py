"""Демонстрационный запуск формы добавления/редактирования партнера."""

import tkinter as tk
from edit_window import PartnerEditWindow


def main() -> None:
    root = tk.Tk()
    root.title("Тестовый хост PartnerEditWindow")
    root.geometry("400x200")
    root.configure(bg="#F1F5F9")

    def show_saved(data: dict) -> None:
        print("Получены сохраненные данные формы:")
        for k, v in data.items():
            print(f"  {k}: {v}")

    def open_add() -> None:
        PartnerEditWindow(root, partner_id=None, on_save=show_saved)

    def open_edit() -> None:
        sample = {
            "partner_id": 1,
            "company_name": "ООО 'Логистик-Экспресс'",
            "partner_type": "ООО",
            "rating": 5,
            "address": "г. Москва, ул. Ленина, д. 10",
            "director": "Смирнов Алексей Викторович",
            "phone": "+7 (999) 111-22-33",
            "contact_email": "info@logex.ru",
        }
        PartnerEditWindow(root, partner_id=1, partner_data=sample, on_save=show_saved)

    tk.Label(root, text="Демонстрация карточки партнера", font=("Segoe UI", 12, "bold"), bg="#F1F5F9").pack(pady=10)
    tk.Button(root, text="Открыть форму [Добавление]", font=("Segoe UI", 10), command=open_add, padx=10, pady=4).pack(pady=5)
    tk.Button(root, text="Открыть форму [Редактирование]", font=("Segoe UI", 10), command=open_edit, padx=10, pady=4).pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    main()
