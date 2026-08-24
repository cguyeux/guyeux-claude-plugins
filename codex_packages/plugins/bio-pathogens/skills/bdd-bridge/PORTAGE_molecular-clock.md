# Note de portage — `molecular-clock` vers Claude Science

Exemple concret de portage d'un skill riche. **Correction de classification** :
`molecular-clock` n'est **pas** tier E — son frontmatter porte
`mcp__tbannotator__tool_query_postgres` et ses scripts lisent `bdd/`, donc il est
**tier A + C mélangés**. Ce qui suit décompose ce qui migre comment.

## Décomposition par couche

| Couche | Contenu | Portabilité Science | Preuve |
|--------|---------|---------------------|--------|
| **Connaissance** | 889 lignes markdown : TDRP, trois régimes TMRCA, quatre mécanismes, règle d'or calibration, Bison antiquus, scope/limites | **Copier tel quel** — pur markdown, zéro dépendance | lisible directement |
| **Calcul portable** | `molecular_clock.py` : `root-to-tip`, régression, bootstrap CI, `nexus-to-newick` | **Tourne tel quel** dans Science (numpy/pandas/scipy/biopython présents) | smoke test offline OK ✓ |
| **Extraction dates** | requêtes MCP `tbannotator__tool_query_postgres` pour les dates de collecte | **Nécessite le serveur MCP TBannotator attaché** à la session Science | dépend du connecteur |
| **Collecte locale** | `molecular_clock_pipeline.py` : lit `bdd/ancien/` + `bdd/actuelle/`, résout `iqtree2` dans `investigate_phylo/` | **Nécessite les données locales** (ou le pont `bdd-bridge`) | tier C |

## Vérifié dans Claude Science (env mtb)

```
$ PYTHONPATH=. python3 smoke_test.py
n=5 rate=1.00e-03 R2=1.0000 boot95=[1.00e-03,1.00e-03] quality=strong  → OK

$ python3 molecular_clock.py root-to-tip t.nwk d.csv --summary
root_date_estimate: 2000.0   signal_quality: "strong (unusual for MTBC)"
```

Dépendances présentes : numpy 2.5.0, pandas 3.0.3, scipy, biopython 1.87.

## Verdict de portage

- **La connaissance et le root-to-tip migrent sans rien toucher** — c'est ~90 %
  de la valeur intellectuelle du skill.
- **L'extraction de dates** se règle en attachant le connecteur TBannotator à la
  session Science (le MÊME serveur MCP que Claude Code utilise — point de
  convergence, pas de réécriture).
- **La collecte `bdd/ancien`+`bdd/actuelle`** est exactement ce que le pont
  `bdd-bridge` adresse : `molecular_clock_pipeline.py` pourrait à terme appeler
  `bdd_query.py` au lieu de ses propres fonctions `collect_*`.

## Recommandation (respecte votre convention anti-doublon)

**Ne pas dupliquer** le skill. Le SKILL.md actuel fonctionne déjà en Science pour
sa partie connaissance + calcul ; il suffit d'y ajouter une ligne « en Claude
Science, attacher le connecteur TBannotator ; pour la collecte locale, utiliser
`bdd-bridge` ». La note ci-dessus sert de référence pour cette migration.
