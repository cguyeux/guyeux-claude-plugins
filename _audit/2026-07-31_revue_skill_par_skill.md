# Revue skill par skill, 2026-07-31 (Opus 5)

Passe complète sur les 165 SKILL.md canoniques (152 collection MTBC + 12 maboss +
`phylo-history` version narration). Méthode : audit mécanique scripté, puis
correction manuelle de chaque signalement, puis vérification.

Les deux outils écrits pour cette passe sont conservés dans `_audit/tools/` plutôt
que jetés avec la session, pour que la suivante ne les réécrive pas et surtout ne
redécouvre pas leurs pièges :

- **`_audit/tools/audit_skills.py`** : audit mécanique (frontmatter, longueur de
  description, déclencheur, cadrage AUP, références de fichiers, cadratins en
  prose, doublons de nom entre plugins). Son en-tête documente les trois
  heuristiques qui ont produit du bruit à la première passe. Un décompte de sortie
  est une liste de candidats à inspecter, pas un verdict.
- **`_audit/tools/dedash.py`** : nettoyage des tirets cadratin de la prose, avec
  `--dry-run`. Son en-tête explique pourquoi le demi-cadratin ne doit jamais être
  touché, exemples de corruption à l'appui.

Les deux couvrent le même périmètre (neuf plugins, maboss compris) : deux outils
qui divergent sur leur périmètre produisent des bilans contradictoires.

## Ce qui a été corrigé

### Cassures réelles (le skill échouait à l'exécution)

| Skill | Défaut | Correction |
|---|---|---|
| `pectinated-subclade-mining` | chemin `bio/skills/...` périmé depuis la scission du plugin | `${CLAUDE_PLUGIN_ROOT}` |
| `mtbc-reboot` | référence à `bio/skills/claim-check/references/CLAIM_TAXONOMY.md` | `${CLAUDE_PLUGIN_ROOT}` |
| `slide-design` | 2 références à `bio/skills/geo-map/scripts/geo_map.py` | `${CLAUDE_PLUGIN_ROOT}` |
| `slide-polish` | chemin codé en dur vers `bio_redac/` alors que le skill vit dans `redac/` | `${CLAUDE_PLUGIN_ROOT}` |
| `cv` | racine du CV annoncée à `~/Documents/docs/cv/`, qui n'existe pas | `~/docs/cv/`, plus un contrôle d'existence avant lecture |
| `grant-proposal` | même préfixe fantôme `~/Documents/docs/projects/` | `~/docs/projects/` |
| `deploy-predictops` | répertoire de travail annoncé à `~/Documents/docs/codes/predictops` | `~/docs/codes/predictops` |
| `latex-formatting` | dépendait de `citation-management`, skill inexistant ; chemins `~/.claude/skills/` codés en dur | scripts réels de `latex-paper-en`, chemins `${CLAUDE_PLUGIN_ROOT}` |
| `latex-document` | appelait `generate-image`, skill inexistant | `sci-figure` / `geo-map` / `graphviz_to_pdf.sh` |
| `latex-posters` | renvoyait à `scientific-schematics` et `figure-style`, inexistants | outils réels et `sci-figure` |
| `latex-paper-en` | renvoyait à `paper-audit`, inexistant | `manuscript-review` puis les quatre skills de contrôle |
| `sra-geolocate` | 4 références à `markdown-converter`, inexistant | `read-scientific-pdf` et `markitdown` |
| `pdf-to-latex`, `slide-design` | idem | `read-scientific-pdf`, `pdftoppm` |
| `clinical-trial-protocol-skill` | l'arborescence annonçait `05-generate-document.md`, le fichier réel est `05-concatenate-protocol.md` | nom corrigé |
| 9 skills MTBC | chemins absolus `~/docs/codes/claude_plugins/<plugin>/skills/...` vers d'autres skills, non portables après clonage | `${CLAUDE_PLUGIN_ROOT}` |

### Doublons structurels

`ia/` portait des **copies réelles** de `scikit-learn`, `statsmodels` et
`scientific-problem-selection`, identiques à celles de `bio_population_genetics/`.
Remplacées par des symlinks relatifs : deux copies identiques divergent
silencieusement à la première modification.

### Descriptions de frontmatter

La description pilote le déclenchement du skill par le harness : c'est le levier
le plus rentable du dépôt.

- 16 descriptions sans aucun déclencheur explicite se sont vu ajouter une clause
  « Use when ... » : `pysam`, `scanpy`, `scikit-learn`, `ml-model-explainer`,
  `numpy-low-level`, `pandas-performance`, `sklearn-advanced`,
  `sklearn-explainability`, `deploy-predictops`, `beamer-slides`,
  `latex-posters`, `overleaf-bridge`, `theme-factory`, `webapp-testing`,
  `beast2-dating`, plus `mtbc-gene` et `resistance-catalogue`.
- 5 skills du pipeline rédaction (`bib-check`, `claim-check`, `deai-latex`,
  `manuscript-review`, `reviewer-response`) ont reçu un déclencheur volontairement
  étroit : ce sont des skills lourds, il ne faut pas qu'une mention incidente les
  déclenche.
- 14 descriptions dépassaient 1024 caractères et risquaient la troncature.
  `latex-document` culminait à 3665 caractères avec une énumération de 51 items ;
  ramenée à 1023. Aussi `slide-polish` (2261), `text-to-speech` (1645), les trois
  maboss, et sept autres.
- Cadrage AUP académique explicite ajouté là où le vocabulaire l'exigeait
  (`lineage-comparison`, `molecular-clock`, `species-id`, `thd`, `geo-map`,
  `bayesian-skyline`, `nextstrain`, `pastml`, `strain-qc`).

### Fond

| Skill | Apport |
|---|---|
| `senior-data-scientist` | Réécrit intégralement. C'était du remplissage (« world-class », SLO de latence, Kubernetes, scripts stubs, références de 80 lignes génériques) dont la description large captait l'auto-sélection au détriment des skills spécifiques. Devenu une porte de conception d'analyse : routage vers le bon skill, et les quatre modes d'échec du domaine (non-indépendance phylogénétique, tests multiples, biais de constatation, fuite par apparentement). Stubs et références envoyés à la corbeille. |
| `statsmodels` | Ajout de `MixedLM`, de GEE pour les réponses binaires, des erreurs standard robustes par grappe, de la correction BH, et de deux exemples du domaine (association d'allèle de résistance, comptage de SNP en Poisson avec test de surdispersion). Exemple OLS de base retiré du jeu de données `tips`. |
| `statistical-analysis` | Table de correspondance entre les exemples génériques et les quantités du domaine ; section multiple-testing refondue (BH contre Bonferroni selon le régime, q-values, mise en garde sur la non-indépendance en amont). |
| `pysam` | Table exacte des conventions de coordonnées (la source d'erreur numéro un), détection du nom de contig, génotypage manuel par pileup avec les paramètres qui comptent (`truncate`, `max_depth`, `ignore_overlaps`), couverture et largeur, comptage par gène corrigé (l'exemple précédent était quadratique et bugué), écriture de VCF filtré. |
| `biopython` | Table de traduction `pairwise2` vers `PairwiseAligner`, signalement du retrait de `Bio.Application` en 1.85 et de la dépréciation de `NCBIXML`, modernisation des imports standards et du pattern d'alignement de base. |
| `scanpy` | Le pattern de base ne pouvait pas s'exécuter : `sc.pp.neighbors` manquait avant `umap` et `leiden`. Ajout du QC mitochondrial, de `adata.raw`, du choix de `n_pcs`, du `flavor="igraph"` requis depuis 1.10, et d'une section sur l'usage d'AnnData hors cellule unique (matrice isolats × variants) avec les trois ajustements obligatoires. |
| `sklearn-explainability` | `shap.Explainer(model.predict, ...)` forçait le chemin agnostique lent : corrigé, avec la table des explicateurs choisis par famille de modèle. Le stub vide `explain_prediction` remplacé par une décomposition exacte pour modèle linéaire. |
| `ml-model-explainer` | Le Quick Start ne correspondait pas à la signature réelle (`plot_waterfall(instance_index, output)`, `explain` attend un DataFrame). Corrigé, et le script dispatchait tous les ensembles vers `KernelExplainer` parce qu'il ne testait que `tree_` : `_is_tree_model` ajouté. |
| `numpy-low-level` | `sliding_window_view` promu comme voie normale ; `as_strided` rétrogradé en repli avancé avec ses deux garde-fous manquants (contiguïté forcée, `writeable=False`). |
| `fig-check` | Phase 2bis : conversion SVG/EPS vers PNG avant de classer une figure `UNREVIEWABLE`. C'était le format d'export d'iTOL et de ggtree, donc les figures principales échappaient à l'inspection. |
| `deploy-predictops` | Étape 7 de rollback complète (relevé du SHA avant push, checkout, restart, vérification, retour sur `main`, consignation), absente alors que ces serveurs alimentent des services de secours. |
| `bayesian-skyline` | Recette sans interface graphique : blocs XML pour BSP, Skygrid et BDSKY, opérateurs que BSP exige, extraction de la trajectoire depuis le `.log` sans Tracer. Le skill était entièrement dépendant de BEAUti, donc inexécutable par un agent. |
| `triangulate-route` | SQL vérifié en direct contre le schéma TBannotator : `geo_country` (normalisé) au lieu de `geo_loc_name ILIKE`, avec la contrepartie chiffrée (174 k lignes renseignées sur 255 k) ; CTE inutile supprimée ; piège `NOT IN` avec NULL explicité. |
| `pangenome-enrichment` | Origine de `gene_presence.csv` documentée (Panaroo/PPanGGOLiN contre dérivation TBannotator) et distinction entre présence du gène et intégrité du cadre de lecture, que le skill confondait. |
| `nextflow-development` | Plancher Java relevé (11 n'est plus tenable avec `self-update`), diagnostic de `UnsupportedClassVersionError`, versions de pipelines présentées comme un instantané avec la commande pour vérifier. |
| `tooluniverse-sequence-retrieval` | L'objet `tu` n'était jamais construit : installation et `load_tools()` ajoutés, plus un repli E-utilities en `curl` et une section de récupération microbienne/MTBC (les défauts MANE sont humano-centrés). |
| `synthesize-research` | Deux registres explicites, scientifique et produit, qui partagent les méthodes mais pas les livrables. Le skill était purement UX et ne se serait jamais déclenché pour le travail du groupe. |
| `slide-polish` | Numérotation homogénéisée : le résumé annonçait 10 défauts, §7.5.2.b en énumère 22. |
| `ops/documentation` | Section sur la documentation de code de recherche (invocation enregistrée, épinglage de ce qui varie, exclusions justifiées). |

### Typographie

1637 lignes de prose nettoyées de leurs tirets cadratin dans 115 fichiers. Le
demi-cadratin est **volontairement préservé** : dans ce corpus il sert de
séparateur d'intervalle numérique (« 40 000–70 000 BP », « C29–C32 ») et de trait
d'union de composé (« host–pathogen »). Un premier script qui le convertissait
aussi a produit « 40 000, 70 000 BP », c'est-à-dire une corruption factuelle. Les
124 cadratins restants sont tous à l'intérieur de blocs de code (arbres ASCII,
sorties d'exemple) et doivent y rester.

Ce qui ressemblait à un problème d'emojis (50 skills signalés) n'en était pas un :
la détection attrapait les caractères de dessin de boîte (`─│├└`), les flèches et
les symboles mathématiques. Les seuls marqueurs réels sont les `✅` / `❌` des
sections DO/DON'T, qui sont fonctionnels.

## Invariants à re-tester après toute modification

```bash
cd /home/christophe/docs/codes/claude_plugins

# 0. audit mécanique complet (code retour 1 s'il reste un signalement)
python3 _audit/tools/audit_skills.py --detail
python3 _audit/tools/dedash.py --dry-run   # doit annoncer 0 ligne

# 1. aucun symlink cassé, aucun symlink absolu
find . -xtype l -not -path "./.git/*"
find */skills -maxdepth 1 -type l -lname '/*'

# 2. aucun chemin absolu vers un autre skill (doit être ${CLAUDE_PLUGIN_ROOT})
grep -rn "docs/codes/claude_plugins/[a-z_]*/skills/" --include=SKILL.md .

# 3. aucun chemin vers l'ex-plugin bio/
grep -rn "\bbio/skills/" --include=SKILL.md .

# 4. tous les scripts Python parsent
find */skills -name "*.py" -not -path "*__pycache__*" -not -path "*venv*" \
  -exec python3 -c "import ast,sys;[ast.parse(open(f).read(),f) for f in sys.argv[1:]]" {} +

# 5. frontmatter présent, name == nom du dossier, description < 1024 caractères
# 6. docs/ régénérable et sans anglais résiduel
python3 docs/build_docs.py
```

## Ce qui reste ouvert

- `clinical-trial-protocol-skill` dépend d'un MCP « clinical trials » installé par
  `.mcpb` dans Claude Desktop, mécanisme hors environnement du groupe, alors que
  ClinicalTrials.gov est interrogeable directement. Le skill reste hors mission ;
  décision à prendre (réécrire l'accès aux données, ou retirer).
- `mes_skills/` à la racine du dépôt contient des matériaux bruts (un PDF, des
  .pptx) et non des skills. À déplacer ou à documenter.
- `bio_redac/skills/phylo-history` et `bio_pathogens/skills/phylo-history` restent
  les deux seules versions à maintenir en parallèle, par choix.
