---
name: skill-fires
description: Smoke-test P5.6 — le skill cahier-de-labo se déclenche encore sur sa phrase de déclenchement canonique après la restructuration du marketplace en 17 plugins.
tags: [smoke, p5.6, non-regression]
runs: 1
model: haiku
timeout_seconds: 60
max_turns: 5
allowed_tools: [Read, Glob, Grep, Skill]
---

Ajoute une entrée au cahier de labo du projet en cours pour dire que le
harnais de tests P1.5 a été rejoué avec succès.
