# Validation CCX-14 : surfaces auxiliaires Claude et Codex

Date : 2026-08-26

## Verdict

Les surfaces secondaires ont toutes un verdict explicite et le lot est clos
pour l'import. Graphify est le seul payload nouvellement installé. Pyright,
les quatre MCP et les capacités de plugins scientifiques étaient déjà présents.
Les agents Claude obsolètes, les caches marketplace et le script statusline ne
sont pas recopiés.

## Décisions

| surface | observation | décision |
|---|---|---|
| `graphify` | règle globale présente, skill absent | import adapté depuis `graphifyy==0.9.50`, commit amont épinglé, Apache-2.0 |
| `pyright-lsp` | cache Claude réduit à une notice | remplacé par Pyright local 1.1.410 et `pyright-langserver` |
| quatre agents `bio_redac` | `model: opus`, anciens chemins `~/Documents`, orchestration hors portes projet | abandonnés avec raison, remplacés par agents Codex natifs et skills manuscrit existants |
| commandes personnelles Claude | aucun fichier `commands/*.md` | aucun import |
| MCP | mêmes quatre noms déjà configurés dans Codex | déjà présents, aucune copie de valeur secrète |
| statusline | script Claude dépendant de son protocole | remplacé par `tui.status_line` et `tui.terminal_title` |
| flags Codex retirés | `external_migration` et `terminal_resize_reflow` signalés `removed` | retirés de la configuration après sauvegarde |
| caches marketplace et plugin désactivé | sources non canoniques ou capacité déjà disponible | aucun import |

Les réglages TUI s'appuient sur les clés persistantes décrites dans la
[référence de configuration Codex](https://learn.chatgpt.com/docs/config-file/config-reference)
et les commandes `/statusline` et `/title` décrites dans la
[référence des commandes développeur](https://learn.chatgpt.com/docs/developer-commands?surface=cli).
La conservation des MCP suit le stockage partagé sous `~/.codex/config.toml`
décrit par la [documentation MCP Codex](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).
Les caches Claude ne sont pas transformés en plugins Codex, dont le modèle
d'installation et de découverte est distinct, comme le rappelle la
[documentation des plugins Codex](https://learn.chatgpt.com/docs/plugins).

## Changements persistants

- Sauvegarde de configuration : `~/.agents/migration/backups/ccx14/20260826T061657Z/config.toml`.
- Configuration Codex : statusline et titre natifs ajoutés, deux flags retirés, `memories` conservé.
- Runtime : `graphifyy` mis à niveau de 0.7.5 à 0.9.50.
- Skill canonique : `~/.agents/skills/graphify`, avec `PROVENANCE.md` et adaptations locales.
- Aucun doublon : `~/.codex/skills/graphify` est absent.
- Aucun hook Graphify Git, Codex ou projet n'a été installé.

## Contrôles

```text
codex --strict-config --version
codex-cli 0.149.1

python3 _audit/tools/audit_auxiliary_surfaces.py --check
OK : surfaces auxiliaires auditées

python3 -m unittest _audit.tests.test_auxiliary_surfaces _audit.tests.test_check_all
Ran 4 tests
OK

python3 -m unittest discover -s _audit/tests
Ran 108 tests dans la projection exacte de l'index Git
OK
```

Une session Codex éphémère neuve, en lecture seule, a répondu
`GRAPHIFY_DISCOVERED`. Les hooks `SessionStart` et `Stop` ont également terminé
normalement.

Le harnais global `check_all.py --source git-index` a validé les générateurs de
skills, les matrices Codex, la documentation et l'audit canonique, puis s'est
arrêté sur `_audit/project_instruction_report.{json,md}` devenu obsolète à la
suite de changements de projets externes à CCX-14. Ces rapports n'ont pas été
régénérés ni absorbés dans ce commit. Les 108 tests unitaires passent dans la
projection exacte de l'index ; les deux échecs observés dans le worktree réel
proviennent uniquement du brouillon non indexé `redac/skills/soumission/`.

## Réserves explicites

- Superhuman est configuré mais la sonde de nouvelle session a demandé une
  authentification OAuth. Aucune autorisation externe n'a été déclenchée.
- `tbannotator` porte une URL différente entre les deux configurations. La
  configuration Codex n'a pas été écrasée sans preuve qu'elle est erronée.
- Un en-tête MCP statique porteur d'un secret subsiste dans la configuration
  Codex. Sa valeur n'est présente dans aucun rapport versionné. Sa migration
  vers une variable d'environnement doit attendre une source d'environnement
  réelle et testée.
- Une session déjà ouverte ne redécouvre pas dynamiquement le nouveau skill ni
  tous les réglages TUI. Une nouvelle session est requise.
