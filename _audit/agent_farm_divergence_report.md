# Rapport CCX-06 des divergences Claude/Agents

Ce fichier est genere par `_audit/tools/report_agent_skill_divergences.py`.
Il compare les skills communs declares divergents dans `_audit/agent_farm_expected_delta.json`.

- Total : 23
- instruction-review-required : 21
- payload-review-required : 2

| skill | classification | decision | fichiers Claude-only | fichiers Agents-only | fichiers modifies | delta lignes |
|---|---|---|---:|---:|---:|---|
| agent-development | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+10/-10 |
| cahier-de-labo | payload-review-required | codex-adapted-divergence-justified | 1 | 0 | 1 | SKILL.md:+26/-56 |
| claude-api | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+50/-50 |
| command-development | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+19/-19 |
| design-doc-mermaid | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+2/-2 |
| docx | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+10/-10 |
| find-skills | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+1/-1 |
| hook-development | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+22/-22 |
| init-project | payload-review-required | codex-adapted-divergence-justified | 0 | 0 | 2 | SKILL.md:+20/-41, init_project.py:+394/-778 |
| mcp-integration | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+13/-13 |
| memory-management | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+34/-33 |
| plugin-settings | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+30/-30 |
| plugin-structure | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+25/-25 |
| recall | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+9/-4 |
| reflect | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+8/-3 |
| researcher | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+21/-31 |
| skill-creator | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+21/-21 |
| skill-development | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+25/-25 |
| update | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+1/-1 |
| using-git-worktrees | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+9/-9 |
| web-artifacts-builder | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+3/-3 |
| write-query | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+1/-1 |
| writing-hookify-rules | instruction-review-required | codex-adapted-divergence-justified | 0 | 0 | 1 | SKILL.md:+7/-7 |
