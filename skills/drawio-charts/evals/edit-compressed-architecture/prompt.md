---
tags: [drawio-charts]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Add a Redis cache to architecture.drawio. The Orders API should check Redis before going to Postgres, so put Redis between them and connect it up. Keep everything else as it is.

Input files: architecture.drawio
