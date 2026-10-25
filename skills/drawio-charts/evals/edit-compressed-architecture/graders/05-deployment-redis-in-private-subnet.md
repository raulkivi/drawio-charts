---
type: llm
focus: trace
weight: 1
---

On the Deployment page there is a cell labelled Redis whose parent is private-subnet, whose geometry fits inside that container (0 <= x, 0 <= y, x + width <= 520, y + height <= 240), with an edge from api-svc to it, an edge from it to rds, and no remaining edge directly from api-svc to rds
