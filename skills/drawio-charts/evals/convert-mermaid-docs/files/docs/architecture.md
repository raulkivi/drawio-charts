# Order service architecture

The order service accepts orders from the web shop, charges the customer and
hands paid orders to the warehouse.

## Request flow

```mermaid
flowchart TD
  client([Web shop]) --> api[Order API]
  api --> valid{Valid order?}
  valid -->|no| reject[Return 400]
  valid -->|yes| pay[Charge card]
  subgraph async [Async processing]
    queue[(Order queue)] --> worker[Fulfilment worker]
  end
  pay --> queue
  worker --> wms[Warehouse system]
```

## Checkout

```mermaid
sequenceDiagram
  actor C as Customer
  participant API as Order API
  participant PSP as Payment provider
  C->>+API: Place order
  API->>+PSP: Charge
  alt approved
    PSP-->>API: OK
    API-->>C: Order confirmed
  else declined
    PSP-->>-API: Declined
    API-->>-C: Payment failed
  end
```

## Data model

```mermaid
erDiagram
  CUSTOMER ||--o{ ORDER : places
  ORDER ||--|{ ORDER_LINE : contains
  CUSTOMER {
    int id PK
    string email
  }
  ORDER {
    int id PK
    int customer_id FK
    string status
  }
  ORDER_LINE {
    int order_id FK
    string sku
    int qty
  }
```

## Roadmap

```mermaid
gantt
  title Order service roadmap
  section Q1
  Async fulfilment :a1, 2026-01-05, 30d
```
