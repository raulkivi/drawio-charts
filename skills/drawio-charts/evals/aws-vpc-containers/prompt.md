---
tags: [drawio-charts]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Draw our AWS setup as a draw.io diagram (aws-architecture.drawio): users hit an Application Load Balancer in a public subnet, which forwards to two ECS services (orders-service and payments-service) in a private subnet. Both services talk to an RDS Postgres instance, also in the private subnet. Everything is inside one VPC.
