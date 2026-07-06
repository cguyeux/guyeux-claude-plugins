# Audit de santé des skills claude_plugins

Scan mécanique sur **157 skills** (hors bdd-bridge, beast2-dating, molecular-clock déjà traités cette session).

## Résultat global
- **143 skills propres** — frontmatter valide, scripts compilent, références cohérentes
- **1 vrai bug mécanique** (corrigé) : `overleaf-bridge` n'avait pas de frontmatter YAML → invisible au catalogue. Ajouté (`name`/`description`/`invocation`).
- **2 « faux skills »** : `mes_skills/itol` et `mes_skills/rasigade` sont des dossiers de matériaux bruts (PDF, .pptx, palette iTOL), pas des skills — pas de SKILL.md attendu.
- **1 dépendance morte réelle** : `latex-posters` imposait `generate_schematic.py` / skill `scientific-schematics`, tous deux inexistants — corrigé (redirigé vers TikZ/matplotlib/graphviz).
- **10 faux positifs** du détecteur de références manquantes, tous qualifiés :
  - cross-références vers d'AUTRES skills (délégation voulue) : `bib-check`→latex-paper-en, `latex-document`→generate-image, `latex-formatting`→citation-management, `strain-qc`→mtbc-lineages, `slide-design`/`mtbc-bilan`→geo-map, `senior-data-scientist` (exemples ML génériques), `deploy-predictops` (fichier rapatrié par scp)
  - lignes de tableau d'exemple prises pour des chemins : `fig-check`, `supp-check`

## Vérifications effectuées par skill
1. Frontmatter YAML présent (`---` + `description:`)
2. Compilation de tous les scripts Python (`py_compile`)
3. Cohérence SKILL.md ↔ scripts référencés
4. Comptage lignes/scripts

## Verdict
La santé mécanique du dépôt est **excellente** : sur 157 skills, un seul défaut réel, désormais corrigé. Aucun script ne casse à la compilation.
