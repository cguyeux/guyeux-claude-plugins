# Fusion famille MTBC (bio_pathogens) — rapport d'analyse

12 skills analysés, SKILL.md lus intégralement, fichiers annexes et dépendances vérifiés sur disque. Aucun fichier modifié.

## 1. Inventaire

| Skill | Cat. | Rôle réel | Fichiers annexes | Chevauchement |
|---|---|---|---|---|
| mtbc-gene-function | analyse | Gène H37Rv vers annotation curatée (UniProt, EC, Pfam, STRING, conservation), local d'abord | `src/mtbc_gene_function/` (core, local, smoke_test) | Bibliothèque de base : appelée par mutation-impact, pathway-explain, gene-network |
| mtbc-atlas | analyse | Même corpus servi par l'API REST mtbc.gclab.fr, plus stats et recherche globales | `atlas_query.py` (stdlib seule) | Fort avec gene-function : son texte dit que l'API sert « the SAME data » que les fiches locales |
| mtbc-mutation-impact | analyse | Gène plus substitution vers LLR ESM-1v, plus deltas SAE dépréciés | `src/mtbc_mutation_impact/` (llr, spdi), `run_llr.sh` | Dépend de gene-function, câblé en dur dans son PYTHONPATH |
| mtbc-pathway-explain | analyse | Set de gènes ou table de sélection vers narration de pathway | `src/mtbc_pathway_explain/` + `data/pathways.yaml`, `run_pathway.sh` | Dépend de gene-function et de gene-network |
| mtbc-lineages | analyse | Autorité de LECTURE : définitions de lignées, marqueurs, classification, cas spéciaux | `data/` (4 tables), `references/` (5 notes), `scripts/lineages.py`, `tests/` | Faible : arbitre les autres, ne calcule rien |
| lineage-mdl | analyse | Moteur d'ÉCRITURE : définit les sous-lignées par optimisation MDL sous contraintes | `scripts/lineage_mdl.py`, `scripts/remat_from_tree.py` | Même question que clade-finder (où couper) |
| clade-finder | analyse | Exploration phénétique t-SNE plus HDBSCAN, PNG et HTML interactif | `scripts/clade_finder.py` (1215 lignes) | Amont direct de lineage-mdl |
| lineage-comparison | analyse | Tests statistiques de traits entre lignées (Fisher, chi2, Clopper-Pearson, FDR) | `scripts/lineage_comparison.py` (299 lignes) | Aucun dans cette famille |
| atlas-add-lineage | analyse (publication) | Écrit une fiche de lignée dans `atlas_mtbc/content/lineages/` puis l'ingère | aucun | Consomme mtbc-lineages et pathway-explain |
| mtbc-bilan | workflow | Photographie consolidée d'un projet, Markdown plus PDF plus Beamer | `templates/bilan.latex`, `templates/bilan_slides.tex` | Est la phase 1 de deepen |
| mtbc-deepen | workflow | Bilan, puis lit-review élargie, puis inventaire des méthodes non mobilisées, puis verdict | aucun | Contient bilan |
| mtbc-reboot | workflow | Archivage tagué, nettoyage du knowledge, réanalyse claim par claim sous gates | aucun | Aucun |

Hypothèse workflow confirmée par le contenu : mtbc-reboot et mtbc-deepen portent le même encadré, « `mtbc-bilan` PHOTOGRAPHIE l'état su (lecture seule) ; `mtbc-deepen` EXPLORE de nouvelles pistes quand un projet stagne ; `mtbc-reboot` REPART à zéro proprement quand la dérive est trop forte. Règle : photographier, explorer, repartir. » Les trois ne produisent aucun résultat scientifique et ne partagent ni script ni donnée avec les neuf autres. Ils concentrent 101 des 107 invocations de la famille.

Deux corrections aux apparences. `clade-finder` est très sous-documenté : son SKILL.md ne décrit qu'un PNG alors que le script produit aussi un dendrogramme de clusters et une page HTML interactive (`generate_html`, environ 480 lignes). `mtbc-bilan` a une description courte (972 caractères) mais un corps de 127 Ko, soit environ 32 000 tokens chargés à chacune de ses 35 invocations.

## 2. Groupes de fusion

### (a) Fusions évidentes, sans perte

`mtbc-gene-function` + `mtbc-atlas` + `mtbc-mutation-impact` + `mtbc-pathway-explain`.

Ce ne sont pas quatre outils voisins mais une seule constellation Python déjà couplée en dur. Les launchers le prouvent : `run_llr.sh:23` exporte `PYTHONPATH="$BP/mtbc-mutation-impact/src:$BP/mtbc-gene-function/src:$BPG/esm-atlas-cli/src"` et `run_pathway.sh:14` chaîne quatre `src/` dont celui de gene-function. Autrement dit `mtbc-gene-function/src` est déjà une bibliothèque partagée déguisée en skill ; la fusion supprime cette plomberie au lieu de la déplacer. Les quatre répondent à la même question posée à des granularités croissantes : un résidu, un gène, un set de gènes, le protéome entier. `mtbc-atlas` documente lui-même son redoublement, précisant que pour le travail en lot il faut lire les JSON locaux, c'est-à-dire exactement ce que fait gene-function.

Variante prudente : fusionner d'abord gene-function + mtbc-atlas (doublon strict de source de données), absorber mutation-impact et pathway-explain dans un second temps.

### (b) Fusions à compromis

`mtbc-bilan` + `mtbc-deepen`. La phase 1 de deepen dit littéralement « Exécuter l'équivalent de /mtbc-bilan sur le projet » ; deepen n'ajoute que trois phases (lit-review élargie, inventaire des skills non mobilisés, grille de décision). Deepen est un mode de bilan, pas un skill distinct. Compromis : deux skills très utilisés (35 et 26 invocations) et un corps déjà volumineux. Contrepartie favorable : la frontière est aujourd'hui arbitrée par un encadré en prose, exactement le genre de distinction qu'un modèle rate ; un drapeau `--deepen` la rend mécanique.

`clade-finder` + `lineage-mdl`. Même objet (subdiviser une lignée), deux étapes successives, et lineage-mdl renvoie déjà à clade-finder. Compromis conceptuel : lineage-mdl consacre un paragraphe à marteler que « Arbre != clusters », que le dendrogramme est phénétique et ne doit jamais poser les bornes. Mettre l'outil de clustering dans le skill qui met en garde contre son usage abusif est un risque, mais c'est aussi l'occasion de rendre l'avertissement inévitable au lieu de le laisser dans un skill invocable seul. Deux modes explicites, `explore` et `optimize`, avec la mise en garde à la charnière.

### (c) À garder autonomes

- `mtbc-reboot` : opération destructive avec machine à états et gates, 40 invocations, aucun recouvrement. Le fusionner avec bilan mettrait un archivage irréversible derrière un drapeau d'un skill de lecture seule.
- `mtbc-lineages` : couche d'autorité que tous consultent, avec ses propres données de référence (marqueurs inverses L4.9, IS6110, signature ancestrale L8/Canettii, PGG) et ses notes bibliographiques. Déclare explicitement primer sur clade-finder, lineage-comparison, tb-cli et TBannotator. Une couche d'arbitrage ne se fusionne pas avec ses arbitrés.
- `atlas-add-lineage` : canal de publication vers un projet distinct (`atlas_mtbc`, module `ingest/` complet, 5 fiches existantes). Ne partage ni données ni scripts avec mtbc-atlas malgré la parenté des noms.
- `lineage-comparison` : statistiques inférentielles sur des traits, zéro recouvrement. Piège à éviter : `mtbc-lineages` a déjà une sous-commande `compare` qui signifie « réconcilier les taxonomies entre systèmes », pas « comparer statistiquement deux lignées » ; la fusion créerait une collision de sens sur le même verbe.

## 3. Détail des fusions

### Fusion A : `mtbc-gene` (4 vers 1)

Structure du SKILL.md : préambule posant l'objet (un gène H37Rv identifié par nom ou locus tag), puis quatre sections de mode (`function`, `mutation`, `pathway`, `atlas`), chacune avec son invocation et ses sorties. Les mises en garde communes (features SAE exploratoires et non citables, confirmer tout domaine par Pfam `hmmscan --cut_ga`) sont aujourd'hui répétées à l'identique dans trois SKILL.md sur quatre : elles deviennent une section unique, ou mieux un `references/caveats.md` chargé à la demande. Les diagrammes « Workflow alignment », également redondants, fusionnent en un seul.

Scripts préservés à l'identique sous `mtbc-gene/` : `atlas_query.py`, `src/mtbc_gene_function/`, `src/mtbc_mutation_impact/` (avec `llr.py` et `spdi.py`), `src/mtbc_pathway_explain/` (avec `data/pathways.yaml`), `run_llr.sh`, `run_pathway.sh`.

Trois retouches obligatoires, sinon la fusion casse des appels existants :
- les PYTHONPATH des deux launchers se simplifient en un seul `src/` local ;
- deux chemins codés en dur pointent depuis l'extérieur vers l'ancien répertoire : `atlas-add-lineage/SKILL.md:82` et `mk-ascertainment/SKILL.md:107` (`SK=~/docs/codes/claude_plugins/bio_pathogens/skills/mtbc-pathway-explain`) ;
- `mtbc-gene-network/run_network.sh:17` référence `mtbc-gene-function/src`.

Les caches `__pycache__` et `*.egg-info` peuvent partir à la corbeille au passage (`gio trash`), ils pèsent l'essentiel des 400 Ko de ces quatre répertoires.

Description (297 caractères) :

```
H37Rv gene and protein layer: curated function (UniProt, EC, Pfam, STRING, conservation) from a gene name or Rv locus tag; ESM-1v LLR impact of a point mutation; pathway or gene-set narration, including from a selection table; atlas-wide search, stats and evidence layers via the mtbc.gclab.fr API.
```

### Fusion B1 : `mtbc-bilan` (2 vers 1, nom conservé pour l'usage acquis)

Structure : les phases 0 à 9 actuelles de bilan restent le tronc commun ; les phases 2, 3 et 4 de deepen (lit-review élargie, inventaire des méthodes non mobilisées, grille de décision CLORE / APPROFONDIR / PIVOTER) deviennent une section « Mode --deepen » intercalée entre la phase 7 (hiérarchisation) et la phase 8 (verdict), puisqu'elles alimentent exactement ces deux phases. La grille de scoring à cinq dimensions de deepen remplace avantageusement celle à trois dimensions de bilan, ou coexiste selon le mode. Templates préservés tels quels. L'encadré de frontière se réécrit en frontière à deux, bilan contre reboot.

Description (282 caractères) :

```
Bilan consolidé d'un projet MTBC : ce qui est su, comment ça a été établi, ce qui reste à faire (Markdown + PDF + slides). --deepen ajoute lit-review élargie, inventaire des méthodes non mobilisées et verdict CLORE / APPROFONDIR / PIVOTER. --full : comparatif de tous les projets mtbc.
```

### Fusion B2 : `lineage-subdivision` (2 vers 1)

Structure : section de cadrage posant d'emblée la distinction entre clusters phénétiques et clades synapomorphiques (aujourd'hui enterrée dans lineage-mdl), puis un mode `explore` (contenu de clade-finder : features SPDI + IS + RD, t-SNE, HDBSCAN, PNG et HTML interactif, grille d'interprétation par silhouette) et un mode `optimize` (débruitage, contraintes, MDL, balayage lambda, Pareto, `inspect`, `deepen`, `materialize`). Les garde-fous de lineage-mdl (jamais `rm`, validation explicite avant `materialize`, minimum 5 souches, assignation character-based) restent en section terminale et s'appliquent aux deux modes.

Scripts préservés sous `scripts/` : `lineage_mdl.py`, `remat_from_tree.py`, `clade_finder.py`. Aucun chemin externe codé en dur vers ces deux skills : fusion sans effet de bord.

Description (299 caractères) :

```
Subdiviser une lignée MTBC en sous-lignées : exploration de la structure (t-SNE, HDBSCAN, dendrogramme, PNG et HTML interactif), puis définition par optimisation MDL sous contraintes synapomorphiques multi-signal (SNP, RD, IS6110), balayage lambda, Pareto, matérialisation réversible dans bdd/actuelle.
```

## 4. Skills réellement obsolètes

Aucun. Sur les quatre skills à zéro invocation, le contenu contredit l'obsolescence dans les quatre cas :

- `mtbc-atlas` interroge une API vivante qui est l'endpoint de disponibilité des données cité dans un manuscrit (« Data availability: ... REST API at https://mtbc.gclab.fr/api/v1 ») ;
- `atlas-add-lineage` vise un projet actif : `atlas_mtbc` a cahier de labo, état des découvertes, pistes, module `ingest/` complet (10 modules) et 4 fiches de lignées ;
- `clade-finder` livre 1215 lignes dont un export HTML interactif que son propre SKILL.md ne mentionne même pas ;
- `lineage-comparison` livre 299 lignes de statistiques correctes (Clopper-Pearson exact, Fisher, FDR Benjamini-Hochberg).

Aucune référence à un pipeline abandonné : les deux seuls skills cités comme archivés, `lineage-cycle` et `lineage-traces`, sont effectivement absents du disque et leur contenu opérant a bien été consolidé dans `lineage-mdl`, ce qui constitue un précédent de fusion réussie plutôt qu'un vestige.

Obsolescence partielle en revanche, à nettoyer pendant les fusions. Trois skills disqualifient eux-mêmes leur couche ESM Atlas SAE :
- `mtbc-mutation-impact` : compter les features basculées « n'est pas une preuve d'effet de variant et fut un sur-claim documenté (rehumanisation_L6L9L10, 2026-05-30) » ; seul le module `llr` (ESM-1v masked-marginal, Meier 2021) est citable ;
- `mtbc-gene-function` : rapporte la lecture SAE « AAA+ ATPase » de Rv0386 qui était en fait un régulateur HTH LuxR/GerE sans domaine ATPase ;
- `mtbc-pathway-explain` : reprend le même avertissement pour `--esm`.

Par ailleurs `mtbc-lineages` traîne environ 60 lignes d'arbre Bovis `s2.X.Y.Z` explicitement marquées « SUPERSÉDÉE (datée 2026-05-16, pré-refonte) », conservées pour leurs annotations biologiques mais dont les labels sont périmés.

## 5. Gain estimé

Base d'audit : 14 960 caractères de description pour les 12 skills. (Ma mesure normalisée, espaces repliés, donne 13 023 ; l'écart correspond à l'indentation du bloc YAML.)

| Étape | Avant | Après | Gain |
|---|---|---|---|
| Fusion A (4 vers 1) | 5 703 | 300 | 5 403 |
| Fusion B1 (2 vers 1) | 1 849 | 320 | 1 529 |
| Fusion B2 (2 vers 1) | 2 904 | 330 | 2 574 |
| Autonomes inchangés | 4 504 | 4 504 | 0 |
| **Total** | **14 960** | **5 454** | **9 506 (64 %)** |

12 skills deviennent 7. En réécrivant aussi les quatre autonomes au même budget de 300 à 450 caractères (`mtbc-lineages` à 1 611 et `mtbc-reboot` à 1 210 sont très au-dessus du nécessaire pour déclencher correctement), le total tombe vers 2 400 caractères, soit environ **12 560 caractères gagnés (84 %)**.

Deux gains hors listing. Le corps cumulé des quatre skills de la fusion A fait 30,4 Ko avec avertissements et diagrammes répétés trois fois ; la déduplication devrait le ramener vers 20 à 22 Ko. Surtout, `mtbc-bilan` a un corps de 127 Ko chargé 35 fois : si le coût en contexte compte autant que l'éviction du listing, y appliquer la divulgation progressive (catalogues de notions pédagogiques et syntaxe LaTeX des encadrés vers `references/`) rapporte davantage que toutes les fusions de descriptions réunies.

## Avertissements de périmètre

La famille réelle déborde les 12 skills confiés. `mtbc-gene-network` et `string-db` appartiennent à la même constellation Python que la fusion A (`run_network.sh:17` chaîne `mtbc-gene-network/src`, `mtbc-gene-function/src`, `esm-atlas-cli/src`, `string-db/src`) : gene-network devrait probablement entrer dans la fusion A, la portant à 5 vers 1. `pectinated-subclade-mining` est cité par clade-finder et lineage-mdl comme troisième pièce de la chaîne de subdivision. `resistance-profiler`, `phylogeography` et `thd` sont les consommateurs naturels de lineage-comparison. À arbitrer avec l'agent qui traite ces familles avant de figer les périmètres.

Risque de triage indépendant des fusions : `mtbc-atlas` (atlas des gènes, projet `annotation_mtbc`, 3 974 fiches) et `atlas-add-lineage` (atlas des lignées, projet `atlas_mtbc`, 4 fiches) désignent deux atlas différents sous des noms quasi identiques. La fusion A résout la collision par accident ; si elle n'est pas retenue, il faut renommer.

Note de convention : les descriptions proposées ci-dessus sont accentuées correctement, alors que les descriptions actuelles de la famille (mtbc-bilan, mtbc-reboot, mtbc-deepen, lineage-mdl) sont en ASCII non accentué. À trancher pour la cohérence du catalogue.
