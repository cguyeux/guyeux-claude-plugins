# Audit CCX-14 des surfaces auxiliaires

Ce fichier est généré par `_audit/tools/audit_auxiliary_surfaces.py`.
Aucune valeur secrète MCP n'est sérialisée.

- Statut : OK
- Codex : `codex-cli 0.154.0`
- Pyright : `pyright 1.1.410`
- Graphify : `0.9.50`
- MCP Codex : context7, superhuman, tbannotator, tbmonitor
- Agents Claude classés : 4
- Commandes Claude à importer : 0

| surface | décision | raison |
|---|---|---|
| graphify | import-adapte | capacité absente, source amont épinglée |
| pyright-lsp | remplace-runtime-local | plugin Claude sans payload serveur |
| agents-bio-redac | abandonne-redondant | prompts Claude obsolètes, pipelines Codex déjà présents |
| commandes-Claude | aucun-import | aucune commande Markdown détectée |
| MCP | conserve | les quatre noms observés sont déjà configurés dans Codex |
| statusline | remplace-TUI-native | configuration Codex persistante |
| caches-marketplace | aucun-import | caches non canoniques |
| frontend-design | aucun-import | plugin Claude désactivé et capacité Codex déjà disponible |

## Réserves

- Les quatre noms MCP sont présents dans Codex. La divergence d'URL de `tbannotator` a été conservée pour ne pas écraser silencieusement une configuration Codex opérationnelle.
- Un en-tête MCP statique porteur d'un secret existe encore. Sa valeur n'est jamais copiée dans cet audit. Le passage à une variable d'environnement relève du durcissement ultérieur.
- Les modifications TUI et Graphify ne deviennent visibles dans la découverte d'une session déjà ouverte qu'après une nouvelle session.
