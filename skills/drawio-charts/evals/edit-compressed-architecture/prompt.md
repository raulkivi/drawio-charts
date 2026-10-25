---
tags: [drawio-charts]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Add a Redis cache to architecture.drawio, on both pages. The Orders API should only talk to Redis now, and Redis reads through to Postgres on a cache miss, so put Redis between them. On the Deployment page it runs in the private subnet with the other services. Don't change anything else.

Input files: architecture.drawio
