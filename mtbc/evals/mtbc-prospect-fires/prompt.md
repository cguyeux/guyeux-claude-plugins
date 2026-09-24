---
name: mtbc-prospect-fires
description: Smoke-test P5.6 — le skill mtbc-prospect du plugin mtbc se déclenche encore sur sa phrase de déclenchement canonique après la restructuration du marketplace en 17 plugins.
tags: [smoke, p5.6, non-regression]
runs: 1
model: sonnet
timeout_seconds: 60
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---

Le projet MTBC en cours a besoin de nouvelles pistes de recherche à
explorer : fais un brainstorming d'angles originaux.
