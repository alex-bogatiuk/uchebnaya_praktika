# ER-диаграмма

```mermaid
erDiagram
    PARTNERS ||--o{ DELIVERIES : receives
    PRODUCTS ||--o{ DELIVERIES : contains

    PARTNERS {
        int partner_id PK
        varchar company_name
        varchar inn UK
        varchar contact_email UK
        varchar phone
        decimal rating
        timestamp created_at
        timestamp updated_at
    }

    PRODUCTS {
        int product_id PK
        varchar product_name UK
    }

    DELIVERIES {
        int delivery_id PK
        int partner_id FK
        int product_id FK
        date delivery_date
        int quantity
        decimal unit_price
    }
```
