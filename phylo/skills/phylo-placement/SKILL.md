---
name: phylo-placement
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST): decides which
  phylogenetic PLACEMENT tool fits a given need, for any clonal bacterial
  pathogen (MTBC, Yersinia, Leptospira...) — UShER (parsimony placement on a
  mutation-annotated tree, fast, incremental), EPA-ng (maximum-likelihood
  placement with uncertainty), Nextclade (community-facing placement on a
  frozen nomenclature), or none of them when a full re-inference is still the
  right call. Also documents the bridge between this group's internal binary
  SPDI presence/absence format and the VCF / FASTA-alignment inputs these
  tools actually expect.

  Use when: placing new or residual strains (`a_ranger`, `bin_*`, freshly
  fetched SRA/ENA runs) onto an existing reference tree without re-running a
  multi-hour RAxML-NG inference; maintaining a classification as a database
  keeps growing; asking "which tool for phylogenetic placement", "comment
  classer ces souches sans refaire l'arbre", "UShER ou EPA-ng", "diffuser un
  dataset Nextclade"; or before installing any of usher/matUtils/epa-ng/nextclade,
  to confirm the choice is the right one for the data at hand.
argument-hint: "<clade ou lignée de référence> [--need incremental|ml-uncertainty|community-dataset]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# phylo-placement : quel outil pour placer une souche sur un arbre existant

> Portée : développé sur le MTBC (projet `Bovis_full`, piste P10), applicable à toute bactérie
> clonale — la distinction PLACEMENT vs DÉCOUVERTE et le pont de format sont génériques. Hors
> MTBC : le format d'entrée natif change (SPDI H37Rv-relatif ici), pas le raisonnement.

## Le clivage qui structure tout ce skill

Deux familles d'outils répondent à deux questions différentes, et les confondre est la source
d'erreur la plus probable.

- **DÉCOUVERTE** : définir les lignées elles-mêmes — synapomorphies, remat, arbre ML complet
  (RAxML-NG, cf. skill `raxml`), MDL (`mtbc:lineage-subdivision`). Question : *quelles sont les
  bonnes coupures dans cette population ?*
- **PLACEMENT** : étant donné une taxonomie déjà établie et un arbre de référence, décider où
  tombe UNE souche nouvelle ou résiduelle. Question : *où va cette souche dans ce qui existe déjà ?*

Ce skill ne couvre QUE le second cas. Le point de douleur récurrent qu'il adresse : classer des
résidus (`a_ranger`, `bin_*`, nouvelles accessions SRA) exige aujourd'hui de refaire un arbre ML
complet (RAxML-NG, plusieurs heures) à chaque fois que la base grandit — c'est l'angle mort de
l'« arbre représentatif » nommé dans `pistes/P10.md`. Les outils de placement classent en
secondes à minutes sans ré-inférer l'arbre entier.

## Arbre de décision

```
Besoin de PLACER des souches sur un arbre déjà construit et validé
│
├─ Le référentiel doit rester exploitable en interne, mis à jour en continu,
│  et l'échelle est celle d'une base qui grandit (dizaines à dizaines de
│  milliers de souches) ?
│  → UShER (+ matUtils). Priorité HAUTE (P10.2). Parcimonie, secondes, tient
│    un mutation-annotated tree qu'on peut ré-augmenter à chaque nouvel apport.
│
├─ Le référentiel est un arbre ML publié/figé, et la décision de placement a
│  besoin d'une MESURE D'INCERTITUDE (likelihood weight ratio) plutôt que
│  d'un placement binaire tranché ?
│  → EPA-ng. **ÉCARTÉ (P10.3, tranché 2026-09-20, CAVEAT DUR CONFIRMÉ, ne pas
│    réinvestiguer sans raison neuve)** : EPA-ng ne supporte PAS les profils
│    binaires présence/absence façon SNP-matrix BIN+G. Preuve code, pas
│    seulement doc : `src/core/pll/epa_pll_util.cpp::get_model()` (dépôt
│    github.com/pierrebarbera/epa-ng) énumère explicitement `states==4`→DNA et
│    `states==20`→protein puis lève `runtime_error("Couldn't determine
│    sequence type from partition")` pour tout le reste — le type `binary`
│    existe dans l'énum `DataType` héritée du code RAxML-NG vendored
│    (`src/core/raxml/types.hpp`), mais aucun chemin d'exécution du binaire ne
│    l'atteint. Le README confirme côté doc : « handle DNA and Amino Acid
│    data » seulement, aucune mention de morphologique/binaire. Encoder le 0/1
│    en pseudo-nucléotides (A/T) contournerait le crash mais fausserait le
│    modèle de substitution (GTR/JC n'a pas de sens sur un caractère binaire),
│    ce qui aurait invalidé la mesure d'incertitude (LWR) qui est la seule
│    raison de préférer EPA-ng à UShER. UShER (P10.2, déjà validé de bout en
│    bout sur ce dépôt) couvre le besoin de placement ; la mesure d'incertitude
│    ML reste un manque assumé, pas un problème résolu.
│
├─ Le but est la DIFFUSION communautaire sur une nomenclature déjà stabilisée
│  (vitrine open-science, outil que d'autres labos utilisent sans notre BDD) ?
│  → Nextclade. Priorité BASSE, différée (P10.4) : n'a de sens qu'une fois la
│    taxonomie cible figée (ex. Bovis une fois P6/P7 clos). Binaire statique,
│    installation la plus simple des trois.
│
└─ Le besoin porte sur la classification ELLE-MÊME (nouvelles coupures, pas
   placement dans des coupures existantes) → ce n'est pas ce skill, voir
   `raxml`, `mtbc:lineage-subdivision`, `mtbc:pectinated-subclade-mining`.

Écartés (P10.5, dominés à notre échelle, ne pas réinvestiguer sans raison neuve) :
pplacer (dominé par EPA-ng, plus lent, même famille de limites nucléotidiques),
APPLES-2 (repli par distances, moins précis qu'UShER quand un MAT existe déjà),
SCAMPP/BSCAMPP (pensé pour >50k tips, sur-dimensionné à notre échelle actuelle).
```

## État d'installation

Vérifié 2026-09-19, machine locale : `usher`, `matUtils`, `epa-ng`, `nextclade` absents du `PATH`,
ni `conda` ni `mamba` non plus (donc pas de voie bioconda immédiate en local). Avant de le faire en
local, appliquer la doctrine du dépôt : le portable sert à écrire/décider, pas à calculer
(`~/docs/codes/CLAUDE.md` § Calcul distant) ; regarder `mp` en priorité pour l'installation ET
l'exécution si l'échelle dépasse quelques centaines de souches.

**`mp` a en réalité déjà conda** (correction 2026-09-20, P10.2) : `/data/cguyeux/miniconda3`
(conda 26.7.0 + mamba), posé par un projet antérieur, hors PATH par défaut mais pleinement
fonctionnel via `source /data/cguyeux/miniconda3/etc/profile.d/conda.sh`. Pas de bootstrap
micromamba nécessaire contrairement à ce que redoutait la note « coût install » de la piste P10.2 —
un simple `mamba create -n usher -c bioconda -c conda-forge usher` suffit, paquet précompilé (pas
de compilation source). Ne PAS présumer l'inverse sur la seule foi de `remote-compute.md`
(« pas de conda… dans le PATH » n'y décrit que le PATH système par défaut, pas `/data`).

## Pont de format : SPDI présence/absence → ce que ces outils attendent

Le format natif du groupe est **une liste SPDI par souche** (`bdd/actuelle/<clade>/<souche>/spdi.txt`,
convention `NC_000962.3:position:ref:alt` ou l'équivalent du génome de référence du genre), converti
en **matrice binaire présence/absence** (0/1) pour RAxML-NG (modèle BIN+G). Aucun de ces trois outils
de placement ne consomme ce format directement.

| Outil | Format attendu | Ce qu'il faut construire depuis le SPDI |
|---|---|---|
| UShER / matUtils | VCF (souches à placer) + arbre de référence en **mutation-annotated tree** (`.pb`), lui-même dérivé d'un VCF global + Newick | Un VCF par souche (ou multi-échantillons) où chaque position SPDI variante devient une ligne VCF standard (CHROM=accession de référence, POS, REF, ALT) ; le MAT de référence se construit une fois avec `usher --vcf <global.vcf> --tree <ref.nwk>` puis s'augmente de façon incrémentale (`usher -i tree.pb -v new.vcf -o tree_updated.pb`) |
| EPA-ng | Alignement de référence (FASTA, souches connues) + alignement des « query » (souches à placer), même longueur de séquence, format Phylip/FASTA nucléotidique ou protéique | **ÉCARTÉ (P10.3)** : pas de pont à construire, l'outil rejette au runtime toute partition qui n'est pas ADN (4 états) ou protéines (20 états) — cf. verdict ci-dessus |
| Nextclade | FASTA de séquences + dataset (arbre de référence + annotations + primers/QC) au format Nextclade dataset (`tree.json`, `genome_annotation.gff3`, `reference.fasta`, `pathogen.json`) | Construction d'un dataset dédié depuis la taxonomie figée, pas une simple conversion — voir la doc Nextclade dataset creation le moment venu (P10.4, différé) |

**Script écrit (P10.2, 2026-09-20)** : `scripts/spdi_to_vcf.py` du skill `mtbc:bdd-bridge`
(canonical `~/docs/environnement/plugins/mtbc/skills/bdd-bridge/scripts/spdi_to_vcf.py`), symétrique
de `bdd_query.py` — au lieu d'empiler les SPDI en colonnes 0/1, émet une ligne VCF par position
variante avec les souches en colonnes génotype (sous-commande `vcf`), plus une sous-commande
`self-test` qui fabrique un VCF jouet à 3 souches synthétiques (SNP simple, site multi-allélique,
1 indel) pour valider `usher --vcf` avant tout usage réel — vérification avant calcul, cf.
`~/docs/codes/mtbc/CLAUDE.md`. Testé localement sur `Bovis.1.1` (1 souche exploitable, 2495 SPDI,
226 indels) : sortie VCF valide.

**Encodage GT VALIDÉ empiriquement le 2026-09-20** : `--gt-style haploid` (défaut du script, valeur
unique "1"/"0"/".") est le bon choix — confirmé DEUX FOIS indépendamment sur `mp` une fois
`usher`/`matUtils`/`faToVcf` installés (mêmes binaires que ceux embarqués dans le paquet bioconda
`usher`) : (1) `faToVcf` sur un FASTA jouet écrit lui-même des génotypes à valeur unique
("GT\t1\t0\t1", jamais "1/1") ; (2) le VCF produit par `spdi_to_vcf.py self-test` (3 souches, SNP
simple + site multi-allélique + 1 indel) a été chargé sans erreur par
`usher --vcf toy.vcf --tree toy.nwk --save-mutation-annotated-tree toy.pb`, MAT produit (score de
parcimonie 3), `matUtils summary` cohérent. **L'indel (site 200000, souche toy_s3) a bien été
ignoré par UShER** — branche `toy_s3:0` dans l'arbre final malgré le variant présent dans le
VCF — confirmant empiriquement le caveat documenté plus haut, pas seulement lu dans la doc.
`--gt-style diploid` reste dans le script au cas où un autre outil de la même famille l'exigerait,
mais n'est plus la voie par défaut à tester en premier.

## Protocole production d'un MAT de placement (mesuré sur le cœur UK, 1 763 souches, P10.6)

Un MAT brut (toutes positions du VCF, backbone quelconque) est dominé par du bruit non
arborescent : sur le cœur UK `Bovis.2.2.1.2.2.2.1.1.1.1.2.9`, 11,6 changements Fitch par site
variable, dont indels + masque canonique + sites instables font plus des trois quarts. Quatre
étapes, dans cet ordre, avant de faire confiance au placement :

1. **SNP ponctuels seulement.** UShER ignore les indels de toute façon, mais l'alignement
   `phylo_job.py align` et tout score Fitch les comptent (873 sites à 27 changements/site ici) ;
   les retirer du VCF pour que le MAT et sa validation regardent la même matrice.
2. **Masque canonique** `global_supplementary/traces_mask/{traces_mask_positions,resistance_positions}.txt`
   (appliqué par défaut par `lineage_navigator`, PAS par `phylo_job.py` ni `spdi_to_vcf.py`) :
   retire 24 % des sites informatifs mais 57 % des événements.
3. **Masque data-driven** : sites à ≥ 10 changements Fitch sur le backbone
   (`scripts/binary_fitch.py --per-site`), l'équivalent des « problematic sites » du pipeline
   UShER SARS-CoV-2. Ici 460 sites SNP hors masque portaient 57 % des événements restants ; ils
   sont à fréquence intermédiaire et mixtes à l'intérieur de chaque BioProject (appel instable
   position-spécifique, pas effet de lot), majoritairement PE/PPE, `espE`, homopolymères.
4. **Souches sous-appelées signalées, pas placées en silence** : à ≥ 200 SNP de tout voisin avec
   moins de SNP que le pool et profondeur < 20× (garde-fou « absence d'appel ≠ allèle de
   référence », `mtbc/CLAUDE.md`), elles font des branches longues par réversion apparente.

**Ce que le leave-30-out a ensuite montré (2026-09-21), et qui borne les étapes 2-3.** Sur le
VCF brut, 13/30 souches retirées reviennent exactement à leur position ML (20/30 placements
uniques) ; sur le VCF propre (étapes 1-3), **4/30** seulement, 236 souches condensées en génomes
identiques, déplacement médian 391 SNP. Cause mesurée sur les 565 mutations des 30 branches
terminales : 67 % dans le masque canonique, 16 % aux sites instables, **17 % propres, soit ≈ 3
par souche, et 11 souches sur 30 n'en ont aucune**. Dans un clade terminal clonal, les branches
terminales sont du bruit ; le brut « réussit » parce qu'il reproduit ce bruit, le propre « échoue »
parce qu'il n'y a rien à placer plus finement qu'à la polytomie. Conséquences :
(a) **valider un MAT au niveau des nœuds NOMMÉS du registre** (`matUtils annotate` sur le MAT,
puis « clade assigné identique » pour chaque souche retirée), pas au niveau de la feuille sœur,
qui ne signifie rien dans une expansion clonale ; (b) **compter ce que le masque laisse aux
pointes** (mutations terminales par catégorie sur un échantillon) avant de conclure ; (c)
**backbone ML et VCF de placement sur la même matrice** : un arbre inféré sur le brut a sa
structure fine façonnée par les sites retirés ensuite, et le leave-k-out contre lui est circulaire
en défaveur du propre. Le rôle des étapes 1-3 n'est donc pas d'améliorer le retour à la feuille
sœur, c'est de rendre honnête le niveau auquel le placement est déterminé. Détail :
`~/.agents/knowledge/bioinformatics.md` [2026-09-21].

**Backbone : ML plutôt que parcimonie séquentielle.** `usher --tree seed.nwk` (graine à 3 souches)
sur 1 760 souches coûte 176 min (le coût croît avec la taille de l'arbre ; la promesse
« parcimonie en secondes » ne vaut que pour le placement sur un arbre existant) puis
`matOptimize` 13 s. Mesure du 2026-09-20 (3 arbres ML RAxML-NG BIN+G partiels, matrice propre =
étapes 1+2 et sans les sous-appelées) : les arbres ML sont 4 à 5 % **plus parcimonieux** que
l'arbre usher+matOptimize (21 621-21 876 contre 22 854), et le classement lnL / Fitch coïncide.
La construction parcimonie n'atteint donc pas l'optimum de son propre critère, pour un gain de
temps de 3 h contre ~9 h (10 départs RAxML), pas des minutes contre des heures. Non testé :
`matOptimize` à rayon/tours plus grands, `usher-sampled`, TNT.

Pièges mesurés : (a) `matOptimize` bioconda plante à `MPI_Init` (PMIX OUT-OF-RESOURCE) sur `mp`,
contournement `PMIX_MCA_gds=hash OMPI_MCA_btl=self,vader` ; (b) le « Total Tree Parsimony » de
`matUtils summary` n'est PAS un score Fitch sur la matrice (2 787 vs 758 sur 15 souches, 50 676 vs
65 490 sur 1 763), mode de comptage non élucidé — ne comparer entre eux que des scores Fitch ;
(c) RAxML-NG sur 1 763 taxa × 5 718 sites : 4 h 30 par recherche sous charge 100/64, et deux départs
aléatoires ont battu le départ parcimonie de 1 900 à 3 000 unités de lnL — ne pas se contenter
d'un seul arbre de départ.

Scripts du skill : `scripts/binary_fitch.py` (Fitch numpy d'un arbre sur une matrice binaire,
décomposition par masque et par tips, validé contre un Sankoff indépendant) ;
`scripts/mat_leave_k_out.py` (prepare/evaluate : retrait de k tips, élagage ete3, découpe du VCF,
puis frère identique / plus proches voisins identiques / **déplacement en SNP et « même
polytomie »** (`--sites <longueur alignement> --eps 0.5`) / ambiguïté depuis le log usher).
Pièges usher : `final-tree.nh` porte des feuilles `node_N_condensed_K_leaves` dès que des
génomes sont identiques → `matUtils extract -i placed.pb -t out.nh` avant `evaluate` ;
`mutation-paths.txt` sépare les nœuds par des espaces avec un espace final (`split()`).

## Suite

1. **P10.2 (UShER) — RÉALISÉ, toolchain validée de bout en bout (2026-09-20).**
   `spdi_to_vcf.py` écrit et testé sur `Bovis.1.1` réel puis sur le clade `Bovis.2.2.1.2.2.2.1.1.1.2.1.1.2`
   (15 souches, verdict `OK` au registre autoritaire). MAT construit (`usher --vcf ... --tree ...`,
   parcimonie 2787, 28 nœuds/15 échantillons). **Validation par retrait-réinsertion (leave-2-out)** :
   deux souches retirées, MAT reconstruit à 13, replacées par `usher --load-mutation-annotated-tree`
   en placement incrémental — reviennent exactement à leur position ML d'origine, sans ambiguïté.
   Détail : `résultats/p10_usher_placement_validation/NOTES.md` (projet `Bovis_full`).
2. **P10.3 (EPA-ng) — ABANDONNÉ (2026-09-20), voir le verdict dans l'arbre de décision ci-dessus.**
   Ne pas réinvestiguer sans fait nouveau (ex. un fork EPA-ng qui répare `get_model()` pour le
   binaire, ou un besoin qui justifierait ce travail d'ingénierie disproportionné pour un pipeline
   de recherche interne).
3. **P10.4 (Nextclade)** : différé jusqu'à taxonomie Bovis stabilisée (post P6/P7).
4. **P10.6 — TRANCHÉ par les registres (2026-09-20), en exécution.** L'alternative « attendre P4 vs
   construire » reposait sur une prémisse fausse (un MAT est topologie + mutations, la taxonomie
   n'en est qu'une annotation `matUtils annotate` régénérable). MAT du cœur UK en cours : RAxML-NG
   10 départs sur `mp`, puis MAT propre selon le protocole ci-dessus et leave-30-out
   (`résultats/p10_6_mat_coeur_uk/pipeline_propre.sh`, projet `Bovis_full`). **Leave-30-out
   fait (2026-09-21)** : brut 13/30, propre 4/30, lecture dans la section Protocole ci-dessus.
   Portée production (MAT de tout *M. bovis*, 13 189 souches) : à déclencher à la prochaine
   arrivée de souches non classées, backbone ML sur matrice propre, validation au niveau des
   nœuds du registre (`matUtils annotate`).
