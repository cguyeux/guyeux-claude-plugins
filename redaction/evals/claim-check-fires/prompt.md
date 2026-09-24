---
name: claim-check-fires
description: Smoke-test P5.6 — le skill claim-check du plugin redaction se déclenche encore sur sa phrase de déclenchement canonique après la restructuration du marketplace en 17 plugins.
tags: [smoke, p5.6, non-regression]
runs: 1
model: haiku
timeout_seconds: 60
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---

Vérifie les affirmations chiffrées de l'article LaTeX de ce projet avant
soumission, et recroise les résultats avec la littérature.
