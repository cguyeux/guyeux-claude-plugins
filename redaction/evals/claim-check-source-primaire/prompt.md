---
name: claim-check-source-primaire
description: >-
  Regression comportementale (piste Y1, environnement, 2026-09-22) sur la regle de la
  source primaire de claim-check -- porte 3bis de lineage_subdivision_methods
  (2026-09-18/19) : un manuscrit citant un compte desynchronise de son fichier de
  resultats (5 temoins declares, 9 reels dans witnesses.tsv) doit etre signale
  a_corriger, jamais confirme sur la seule lecture de la prose.
tags: [behavior, p:Y1, claim-check, source-primaire]
runs: 1
model: sonnet
timeout_seconds: 300
max_turns: 30
allowed_tools: [Read, Write, Edit, Bash, Grep, Glob, Skill]
---

Verifie les affirmations chiffrees de fixtures/main.tex avant soumission. Le fichier de
resultats associe est fixtures/witnesses.tsv.
