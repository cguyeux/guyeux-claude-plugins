# Rapport CCX-06 des divergences Claude/Agents

Ce fichier est genere par `_audit/tools/report_agent_skill_divergences.py`.
Il compare les skills communs declares divergents dans `_audit/agent_farm_expected_delta.json`.

- Total : 30
- instruction-review-required : 25
- payload-review-required : 5

| skill | classification | decision | fichiers Claude-only | fichiers Agents-only | fichiers modifies | delta lignes |
|---|---|---|---:|---:|---:|---|
| agent-development | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+10/-10 |
| cahier-de-labo | payload-review-required | codex-adapted-divergence-justified | 6 | 0 | 1 | SKILL.md:+27/-96 |
| challenge | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+17/-113 |
| claude-api | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+50/-50 |
| command-development | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+19/-19 |
| cycle-projet | payload-review-required | codex-adapted-divergence-justified | 0 | 0 | 4 | SKILL.md:+47/-399, cycle_status.py:+12/-263, references/plugins.md:+43/-62, references/soumission.md:+13/-108 |
| design-doc-mermaid | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+2/-2 |
| docx | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+10/-10 |
| etat | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+4/-19 |
| find-skills | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+1/-1 |
| hook-development | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+22/-22 |
| init-project | payload-review-required | codex-adapted-divergence-justified | 0 | 0 | 2 | SKILL.md:+26/-79, init_project.py:+515/-1208 |
| mcp-integration | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+13/-13 |
| memory-management | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+34/-33 |
| pistes | payload-review-required | codex-adapted-divergence-justified | 7 | 0 | 4 | SKILL.md:+21/-472, audit_signals.py:+1/-1, split_pistes_files.py:+9/-62, status.py:+2/-2 |
| plugin-settings | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+30/-30 |
| plugin-structure | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+25/-25 |
| qcm-generator | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+1/-1 |
| recadrage | payload-review-required | codex-adapted-divergence-justified | 0 | 0 | 2 | SKILL.md:+35/-261, recadrage_signals.py:+5/-28 |
| recall | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+9/-4 |
| reflect | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+8/-3 |
| researcher | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+21/-31 |
| screenshot | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+3/-3 |
| skill-creator | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+21/-21 |
| skill-development | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+25/-25 |
| update | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+1/-1 |
| using-git-worktrees | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+9/-9 |
| web-artifacts-builder | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+3/-3 |
| write-query | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+1/-1 |
| writing-hookify-rules | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+7/-7 |
