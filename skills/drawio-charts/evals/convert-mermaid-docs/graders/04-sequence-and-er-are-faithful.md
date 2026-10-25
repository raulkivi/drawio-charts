---
type: llm
focus: trace
weight: 1
---

The sequence diagram's draw.io diagram has lifelines for Customer (an actor), Order API and Payment provider, the messages Place order, Charge, OK, Order confirmed, Declined and Payment failed in that order, and an alt frame with approved and declined sections; the ER diagram has tables CUSTOMER, ORDER and ORDER_LINE with their attributes, and relationships CUSTOMER-ORDER (one to zero-or-many, label places) and ORDER-ORDER_LINE (one to one-or-many, label contains)
