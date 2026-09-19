/**
 * app.js - Клиентская логика веб-интерфейса CRM
 * Обеспечивает динамический рендеринг карточек партнеров и расчет скидок.
 */

// Резервные тестовые данные из БД на случай открытия файла index.html напрямую в браузере (file://)
const FALLBACK_PARTNERS = [
    {
        partner_id: 1,
        partner_type: "ООО",
        clean_name: "Логистик-Экспресс",
        company_name: 'ООО "Логистик-Экспресс"',
        director: "Смирнов Алексей Викторович",
        phone: "+7 (999) 111-22-33",
        rating: 4.8,
        total_quantity: 12080,
        discount_percent: 5
    },
    {
        partner_id: 2,
        partner_type: "ИП",
        clean_name: "Петров А.В.",
        company_name: "ИП Петров А.В.",
        director: "Петров Андрей Васильевич",
        phone: "+7 (916) 223-32-22",
        rating: 4.2,
        total_quantity: 55200,
        discount_percent: 10
    },
    {
        partner_id: 3,
        partner_type: "ТК",
        clean_name: "Быстрый Путь",
        company_name: 'ТК "Быстрый Путь"',
        director: "Ковалев Сергей Михайлович",
        phone: "+7 (812) 555-44-33",
        rating: 4.9,
        total_quantity: 310150,
        discount_percent: 15
    },
    {
        partner_id: 4,
        partner_type: "ЗАО",
        clean_name: "База Строитель",
        company_name: 'ЗАО "База Строитель"',
        director: "Воронов Дмитрий Павлович",
        phone: "+7 (223) 322-22-32",
        rating: 5.0,
        total_quantity: 8500,
        discount_percent: 0
    },
    {
        partner_id: 5,
        partner_type: "ПАО",
        clean_name: "Металл-Снаб",
        company_name: 'ПАО "Металл-Снаб"',
        director: "Семенов Игорь Николаевич",
        phone: "+7 (495) 777-88-99",
        rating: 3.8,
        total_quantity: 0,
        discount_percent: 0
    }
];

let allPartners = [];

// Расчет скидки в соответствии с ТЗ (для автономного клиентского расчета)
function calculateClientDiscount(totalQuantity) {
    const qty = Number(totalQuantity) || 0;
    if (qty < 10000) return 0;
    if (qty < 50000) return 5;
    if (qty < 300000) return 10;
    return 15;
}

// Загрузка данных: сначала пробуем получить по API, при ошибке используем локальные данные
async function loadPartnersData() {
    const counterEl = document.getElementById("partnersCounter");
    counterEl.textContent = "Обновление...";

    try {
        const response = await fetch("/api/partners");
        if (response.ok) {
            allPartners = await response.json();
        } else {
            allPartners = FALLBACK_PARTNERS;
        }
    } catch (e) {
        // Если API сервер не запущен, используем данные из базы
        allPartners = FALLBACK_PARTNERS;
    }

    renderPartners(allPartners);
}

// Рендеринг карточек партнеров строго по макету Screenshot_2.png
function renderPartners(partners) {
    const listContainer = document.getElementById("partnersList");
    const counterEl = document.getElementById("partnersCounter");

    listContainer.innerHTML = "";
    counterEl.textContent = `Всего партнеров: ${partners.length}`;

    if (partners.length === 0) {
        listContainer.innerHTML = `
            <div class="empty-state">
                По вашему запросу партнеры не найдены.
            </div>
        `;
        return;
    }

    partners.forEach(partner => {
        const card = document.createElement("article");
        card.className = "partner-card";

        const partnerType = partner.partner_type || "ООО";
        const cleanName = partner.clean_name || partner.company_name;
        const director = partner.director || "Директор не указан";
        const directorFormatted = director.toLowerCase().startsWith("директор") ? director : `Директор: ${director}`;
        const phone = partner.phone || "Телефон не указан";
        const rating = partner.rating !== undefined && partner.rating !== null ? partner.rating : "—";
        const discount = partner.discount_percent !== undefined ? partner.discount_percent : calculateClientDiscount(partner.total_quantity);

        card.innerHTML = `
            <div class="card-left">
                <div class="partner-title">${escapeHtml(partnerType)} | ${escapeHtml(cleanName)}</div>
                <div class="partner-director">${escapeHtml(directorFormatted)}</div>
                <div class="partner-phone">${escapeHtml(phone)}</div>
                <div class="partner-rating">Рейтинг: ${escapeHtml(String(rating))}</div>
            </div>
            <div class="card-right">
                <div class="partner-discount">${discount}%</div>
            </div>
        `;

        card.addEventListener("click", () => {
            console.log("Выбран партнер:", partner);
        });

        listContainer.appendChild(card);
    });
}

// Фильтрация партнеров в реальном времени
function setupSearchFilter() {
    const searchInput = document.getElementById("searchInput");
    searchInput.addEventListener("input", (e) => {
        const query = e.target.value.toLowerCase().trim();
        if (!query) {
            renderPartners(allPartners);
            return;
        }

        const filtered = allPartners.filter(p => {
            const name = (p.company_name || "").toLowerCase();
            const cleanName = (p.clean_name || "").toLowerCase();
            const inn = (p.inn || "").toLowerCase();
            const director = (p.director || "").toLowerCase();
            return name.includes(query) || cleanName.includes(query) || inn.includes(query) || director.includes(query);
        });

        renderPartners(filtered);
    });
}

// Вспомогательная функция санитизации строк
function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// Инициализация при загрузке DOM
document.addEventListener("DOMContentLoaded", () => {
    setupSearchFilter();
    loadPartnersData();

    document.getElementById("refreshBtn").addEventListener("click", () => {
        loadPartnersData();
    });
});
