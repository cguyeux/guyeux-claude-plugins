# Rapport CCX-04 base de connaissances Claude/Codex

Ce fichier est genere par `_audit/tools/sync_knowledge_base.py`.
Il compare les vues `~/.claude/knowledge` et `~/.Codex/knowledge`, puis controle la source neutre `~/.agents/knowledge`.

- Total union : 85
- claude-only : 71
- codex-only : 7
- common-divergent : 7
- Fichiers canoniques : 85
- Manquants du canonique : 0
- Extras dans le canonique : 0

| chemin | statut | lignes Claude | lignes Codex |
|---|---|---:|---:|
| KNOWLEDGE.md | common-divergent | 90 | 12 |
| KNOWLEDGE.md.full-2026-08-05 | claude-only | None |  |
| KNOWLEDGE_DETAIL.md | claude-only | 255 |  |
| agent-background-orchestration.md | claude-only | 293 |  |
| agent-tooling.md | codex-only |  | 251 |
| ars.md | claude-only | 115 |  |
| audition-recrutement-public.md | claude-only | 121 |  |
| bash-patterns.md | claude-only | 924 |  |
| bioinformatics.md | claude-only | 2006 |  |
| brilliant-ideas.md | claude-only | 159 |  |
| cahier-de-labo-archive-header-regex.md | claude-only | 44 |  |
| claude-in-chrome-automation.md | claude-only | 304 |  |
| claude-plugins-aup.md | claude-only | 773 |  |
| claude-workflow-tool.md | claude-only | 58 |  |
| collaborators.md | common-divergent | 1926 | 163 |
| corpus-archives-numerisees.md | claude-only | 982 |  |
| cv-workflow.md | claude-only | 76 |  |
| data-provenance.md | codex-only |  | 331 |
| deployment.md | common-divergent | 1061 | 66 |
| figures-publication-inspection.md | claude-only | 377 |  |
| french-writing-proofreading.md | claude-only | 131 |  |
| frontend-patterns.md | claude-only | 486 |  |
| ghostwriting-adversarial.md | claude-only | 64 |  |
| git-github.md | codex-only |  | 41 |
| hook-prompt-doubt-clause.md | claude-only | 119 |  |
| htr-ecritures-anciennes.md | claude-only | 582 |  |
| iappels.md | claude-only | 335 |  |
| iconographie-et-licences-figures.md | claude-only | 152 |  |
| journals/README.md | claude-only | 51 |  |
| journals/SCHEMA.md | claude-only | 38 |  |
| journals/author_profile.json | claude-only | 66 |  |
| journals/journals.tsv | claude-only | 126 |  |
| journals/parts/ai_securite.tsv | claude-only | 27 |  |
| journals/parts/elsevier.tsv | claude-only | 22 |  |
| journals/parts/gratuit.tsv | claude-only | 36 |  |
| journals/parts/societies.tsv | claude-only | 38 |  |
| journals/parts/springer.tsv | claude-only | 22 |  |
| journals/portal_lessons.md | claude-only | 261 |  |
| journals/portals.tsv | claude-only | 10 |  |
| journals/preprints_et_delais.md | claude-only | 797 |  |
| journals/rejections.md | claude-only | 29 |  |
| journals/submissions.tsv | claude-only | 9 |  |
| latex-babel-french-bibtex-colon.md | claude-only | 38 |  |
| latex-elsevier-elsarticle.md | claude-only | 110 |  |
| legifrance-api.md | claude-only | 185 |  |
| linux-desktop.md | common-divergent | 841 | 7 |
| lit-review-fanout-verification.md | claude-only | 639 |  |
| literature-search.md | codex-only |  | 462 |
| long-transcript-synthesis.md | claude-only | 249 |  |
| maboss.md | claude-only | 646 |  |
| manuscript-review-llm-eval.md | claude-only | 667 |  |
| marker-compatibility-laminarity.md | claude-only | 387 |  |
| micwatch-pipeline.md | claude-only | 395 |  |
| micwatch-pipeline.md.bak_20260821_before_long_stt_incident | claude-only | None |  |
| multiagent-skills-eval.md | claude-only | 164 |  |
| multimedia-tts.md | claude-only | 143 |  |
| office-docx-formulaires.md | claude-only | 120 |  |
| office-xlsx-automation.md | claude-only | 225 |  |
| opencv.md | claude-only | 112 |  |
| optimops.md | claude-only | 953 |  |
| papyrology.md | codex-only |  | 177 |
| pdf-supplementary-tables.md | claude-only | 116 |  |
| population-genetics-inference.md | claude-only | 38 |  |
| predictops.md | common-divergent | 4939 | 5 |
| proposition-ciblee.md | claude-only | 58 |  |
| python-patterns.md | common-divergent | 4266 | 1902 |
| python-patterns.md.bak_20260821_before_micwatch_reflect | codex-only |  | None |
| quodlibet.md | claude-only | 127 |  |
| referee-reports.md | claude-only | 63 |  |
| reference-bias-pipelines.md | claude-only | 234 |  |
| refuter-sa-propre-piste.md | claude-only | 563 |  |
| remote-compute.md | claude-only | 414 |  |
| research-guardrails.md | claude-only | 3988 |  |
| research-interfaces.md | codex-only |  | 993 |
| scientific-journals.md | common-divergent | 571 | 80 |
| scientific-writing-en.md | claude-only | 831 |  |
| server-access.md | claude-only | 152 |  |
| slides-build-system.md | claude-only | 139 |  |
| superhuman-mcp.md | claude-only | 96 |  |
| sympa-mailing-lists.md | claude-only | 202 |  |
| taxonomy-node-validation.md | claude-only | 1173 |  |
| tikz-beamer-patterns.md | claude-only | 368 |  |
| toolkit-transfer-clonal-bacteria.md | claude-only | 69 |  |
| tuberculosis.md | claude-only | 14280 |  |
| verif-stats-sources.md | claude-only | 385 |  |
