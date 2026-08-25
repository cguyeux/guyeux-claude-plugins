# Audit CCX-12 des permissions Claude et Codex

Date UTC : `2026-08-25T16:02:58.383940+00:00`

## Inventaire

- Claude : 97 autorisations, dont 89 Bash, 7 destructives et 74 exactes ou historiques.
- Codex historique : 447 règles, décisions {'allow': 447}.
- Codex canonique : 15 règles, décisions {'allow': 1, 'forbidden': 4, 'prompt': 10}.
- Politique active canonique : True (`/home/christophe/.codex/rules/default.rules`).
- Réduction : 432 règles retirées de la politique active.

## Signaux de dérive historiques

- `broad-prefix` : 9
- `exact-or-long` : 354
- `legacy-knowledge-path` : 89
- `other` : 78
- `remote` : 19
- `shell-wrapper` : 177
- `temporary-path` : 143

## Usage observé sur 7 jours

3213 appels shell ont été lus dans 51 fichiers de session. Seuls les noms d'exécutables sont conservés.

| Exécutable | Occurrences |
|---|---:|
| `python3` | 562 |
| `git` | 558 |
| `sed` | 550 |
| `rg` | 288 |
| `npx` | 244 |
| `find` | 209 |
| `curl` | 163 |
| `codex` | 81 |
| `gio` | 68 |
| `ls` | 57 |
| `test` | 54 |
| `tail` | 52 |
| `jq` | 48 |
| `mkdir` | 46 |
| `yt-dlp` | 45 |
| `docker` | 33 |
| `scw` | 33 |
| `mv` | 32 |
| `nl` | 30 |
| `sha256sum` | 27 |
| `env` | 24 |
| `claude` | 24 |
| `cp` | 24 |
| `python` | 24 |
| `mktemp` | 22 |
| `wc` | 17 |
| `grep` | 17 |
| `date` | 16 |
| `pytest` | 16 |
| `diff` | 16 |

## Politique retenue

- `allow` : 1
- `forbidden` : 4
- `prompt` : 10

Les commandes ordinaires restent confinées au sandbox. Les règles explicites servent seulement aux sorties du sandbox : suppression permanente interdite, mutations distantes ou système soumises à approbation, et `gio trash` autorisé comme retrait récupérable.

Les autorisations Claude exactes ne sont pas recopiées. Les commandes sûres n'ont pas besoin d'une permission globale lorsqu'elles restent dans le workspace; les commandes externes ou destructrices doivent conserver une décision contextuelle.

## Validation

Statut structurel : OK.
