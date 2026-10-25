---
tags: [drawio-charts]
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Our docs use Mermaid but we're moving to draw.io. Convert the Mermaid diagrams in docs/ to draw.io and replace them in the markdown so they still show up on GitHub. Keep the original Mermaid around somewhere in case we need to roll back.

Input files: docs/architecture.md
