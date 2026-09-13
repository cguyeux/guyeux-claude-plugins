---
name: bdd-bridge
description: >-
  Academic research toolkit. Read-only bridge over the local curated MTBC
  research database (bdd/actuelle/, Guyeux group, FEMTO-ST, University of
  Franche-Comte), a snapshot of published-research isolates stored as
  per-strain SPDI variant lists. Exposes two dependency-free CLIs, callable
  identically from Claude Code and from a compute agent, so that lineage
  bookkeeping and phylogenetic inference run the same way in both. `bdd_query.py`
  lists clades, reads per-strain QC, builds binary SNP matrices, and extracts
  clade synapomorphies; `phylo_job.py` builds a binary alignment and runs or
  submits RAxML-NG (BIN+G) locally or as a portable SLURM package.

  Use when: reporting clade-level strain counts or QC for a peer-reviewed
  phylogenomics manuscript, extracting synapomorphies to define a published
  sub-lineage, or building a scientific-publication phylogeny for an MTBC clade
  from the local research database.
argument-hint: "clades | denominator <clade> | strain <clade> <SRA> | synapo <clade> | polarize <SPDI> [--strains liste] | phylo run <clade>"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# bdd-bridge : pont read-only sur `bdd/actuelle/` + inférence phylo

Deux CLI **stdlib pure** (zéro dépendance), appelables à l'identique depuis
Claude Code (shell-out) et depuis un agent de calcul. Le but : que la lecture de
la base locale de souches et l'inférence phylo se fassent **de la même façon**
dans les deux environnements, sans serveur à maintenir.

## Deux pièges de comptage, à connaître avant d'annoncer un effectif

**1. Un répertoire d'accession ne garantit pas une souche exploitable.** Balayage exhaustif du
2026-09-06 (168 155 répertoires) : 86,99 % portent un `report.json`, 12,41 % un `spdi.txt` seul, et
**1 025 ne portent AUCUNE donnée génomique** — dont **943 dans la seule lignée L4.7**, où ils font
**41,4 % des répertoires** (548 entièrement vides créés en un lot le 2026-03-17, 395 ne contenant
qu'un `crispr_reads_report.json`). Compter L4.7 par énumération de répertoires **surestime de
69 %**. D'où la colonne `exploitables` de `clades` et la commande `denominator`.

**2. `bdd/` n'est pas un miroir de TBannotator, c'est le sous-ensemble CURÉ de ce qui a été
ÉTUDIÉ** (politique énoncée par CG le 2026-09-06). 105 929 souches de la base n'ont aucun répertoire
local : elles ne sont pas écartées, elles n'ont pas encore été prises pour objet. Un effectif local
décrit donc **l'échantillon travaillé, jamais la population**. Symétriquement, 18 849 souches
locales sont inconnues de la base, dont 17 846 vivent sur le pipeline `mp` sans y avoir été
ingérées, la base étant **figée à février 2026** le temps de la reprise de TBannotator par
C. Lecarpentier (déploiement IDEEV / Paris-Saclay). Mesures et listes :
`mtbc/résultats/p63_diff_bdd_tbannotator/`, pistes P63 et P64.

Enfin, `denominator` ne prétend pas que les deux nombres mesurent la même chose : le placement local
fait autorité (`bdd/actuelle` est vivante) et peut diverger de la classification de la base. Il les
affiche côte à côte et le dit.

## Localisation de la BDD

Par priorité : `--bdd <chemin>` → `$TBANNOTATOR_BDD` → `../bdd` remonté depuis le
script. Depuis un sous-projet, la BDD est en `../../bdd`. Toutes les opérations
sont **strictement en lecture**, aucun script n'écrit dans `bdd/`.

## `bdd_query.py` : lecture de la base

```bash
S=bio_pathogens/skills/bdd-bridge/scripts     # ou le canonical réel
python3 $S/bdd_query.py clades                 # tous les clades + effectif (repertoires / exploitables)
python3 $S/bdd_query.py denominator L4.7       # garde de denominateur : local exploitable vs TBannotator
python3 $S/bdd_query.py strains L4.15          # souches d'un clade
python3 $S/bdd_query.py --json strain L4.15 ERR1023322   # QC + nb SNP d'une souche
python3 $S/bdd_query.py matrix L4.15 --min-frac 0.1       # matrice SNP binaire -> TSV
python3 $S/bdd_query.py synapo L4.15                      # synapomorphies (frac >= 0.95)
python3 $S/bdd_query.py synapo L5.2.1 --recursive --min-frac 0.90  # agrège L5.2.1 + tout son sous-arbre L5.2.1.*
python3 $S/bdd_query.py align L4.15 --mask MASK.txt --rd-table RD.csv --out aln.phy  # alignement propre pour datation
```

- `clades` : `<clade>\t<repertoires>\t<exploitables>` (ignore les `_flatten_*_undo_log.tsv`). La colonne **exploitables** compte les souches qui portent réellement une donnée génomique (`report.json` ou `spdi.txt`) ; voir l'encadré ci-dessous.
- `denominator <clade>` : **garde de dénominateur**. Met côte à côte l'effectif local EXPLOITABLE et l'effectif que TBannotator classe sous le code correspondant, avec les avertissements qui empêchent de confondre l'échantillon étudié et la population. `--system` (défaut `guyeux`), `--local-only` pour ne pas interroger la base. **À appeler avant d'écrire un effectif dans un manuscrit.**
- `strain` : lit `report.json` (couverture, profondeur, MAPQ, GC) + compte les SPDI.
- `matrix` : lignes = souches, colonnes = positions SPDI présentes chez ≥ `min_frac`
  des souches ; `--json` renvoie aussi le vecteur 0/1 par souche.
- `synapo` : positions partagées par ≥ seuil (défaut 0.95), candidates marqueurs de clade.
- `polarize <SPDI>` : distribution d'**un** site à travers les clades, en **3 états**
  `ON` / `OFF` / `UNKNOWN`, avec polarisation par un groupe externe et, en option, la
  **dose-réponse** couverture × non-portage. Voir la section dédiée ci-dessous.
- `--recursive` (sur `strains`/`matrix`/`synapo`) : agrège le conteneur `clade` avec TOUT son
  sous-arbre `clade.*`. Indispensable dès qu'une lignée a été matérialisée en plusieurs
  sous-conteneurs (géographiques, phylogénétiques...) : sans ce flag, `synapo L5.2.1` ne voit que
  les souches du dossier racine `L5.2.1/` et ignore ses 7 sous-conteneurs `L5.2.1.*`, ce qui fausse
  toute comparaison à un marqueur ou barcode publié portant sur le clade entier.
- `align` : alignement binaire PHYLIP multi-clades **propre pour l'horloge moléculaire**
  (voir section dédiée ci-dessous).

Toute commande accepte `--json` (sortie structurée) et `--bdd`.

## `polarize` : un site, tous les clades, et la distinction ABSENT / NON COUVERT

```bash
python3 $S/bdd_query.py polarize 'NC_000962.3:2887961:GGC:G' --clades Bovis.2 --outgroup Canettii
python3 $S/bdd_query.py polarize 'NC_000962.3:2889632:T:C' --outgroup Canettii --dose-response
python3 $S/bdd_query.py polarize '<SPDI>' --clades L4 L2 --gene Rv2566 --json
python3 $S/bdd_query.py polarize '<SPDI>' --strains clade_souches.tsv --strains-name mon_clade --gene Rv2566 --dose-response
```

**Le problème que cette commande résout.** Compter les porteurs d'un SPDI dans un clade est trivial
(`rg -l` sur les `spdi.txt`). Ce qui ne l'est pas, c'est de distinguer les deux causes possibles
d'une ABSENCE : la souche porte l'allèle de référence (`OFF`), ou la position n'était pas
appelable (`UNKNOWN`). Sans cette distinction, une fréquence de 98,6 % ne se distingue pas d'une
fixation totale entachée de 1,4 % de non-appels, et deux lectures opposées du même chiffre restent
également défendables. `polarize` lit la couverture réelle du gène dans `report.json`
(`median_coverage`, `percent_missing`, et `mean_ratio` = couverture du gène / profondeur du génome)
et rend les trois états, plus la fréquence corrigée `ON/(ON+OFF)`.

Seuils par défaut, calqués sur les critères réels du pipeline : `--min-median-cov 10` (Snippy exige
une profondeur ≥ 10 pour appeler), `--max-pct-missing 0.10`, `--min-mean-ratio 0.10` (seuil
`missing_genes`). Le gène portant le site est déduit de l'annotation du premier porteur ; `--gene`
le force si aucun porteur n'existe dans le périmètre demandé.

### `--dose-response` : le test qui tranche vraiment, et pourquoi le seuil 3 états ne suffit pas

### `--strains` : quand le clade réel n'a PAS de nom dans la taxonomie de répertoires

`--clades` prend des PRÉFIXES de répertoires. Or un clade réel n'a pas toujours de répertoire :
sur `Rv2566` (2026-09-08), le sous-clade L1 portant un frameshift fixé est réparti entre un
conteneur NU `L1` de 21 163 souches, `L_1.A.2` et `L_1.A.2.1`. Aucun préfixe ne le désigne, et
il a fallu écrire un scanner local — exactement le doublon que ce skill existe pour supprimer.

`--strains <fichier>` prend une liste explicite `<clade>/<sra>`, une par ligne, et en fait un
groupe nommé (`--strains-name`, défaut : le nom du fichier). Le lecteur tolère un TSV dont la
première colonne porte le chemin, une ligne d'en-tête, les commentaires `#`, un préfixe `./` et
un suffixe `/NC_000962.3[/spdi.txt]` : les sorties de `rg -l` et les tables d'analyse passent
telles quelles. Le dédoublonnage sur (clade, accession) est fait dans le lecteur, contre les
chemins qui DOUBLENT l'accession.

Se combine avec `--clades` et `--outgroup` : le groupe nommé s'ajoute aux préfixes, et la
dose-réponse reste rendue PAR GROUPE.

**Calibrage mesuré, et il contredit le défaut.** Sur ce cas, le codage 3 états avec le seuil par
défaut (`--min-median-cov 10`) rend 148 ON / 9 OFF / 0 UNKNOWN, donc une fréquence de 94,27 % et
neuf « vrais sauvages ». La dose-réponse dit l'inverse : 26,47 % de non-portage dans la tranche
[10,20) et **0,00 % dans TOUTES les tranches au-dessus de 20x**. Décroissance vers zéro sans
plateau : les neuf sont des non-appels et le site est fixé à 100 %. Pour un indel de 1 pb, le
seuil par défaut de 10x est donc trop bas ; c'est la FORME de la courbe qui tranche, jamais le
compte 3 états.

**À lire avant d'utiliser `polarize` sur un INDEL, un microsatellite ou une région répétée.** Le
codage 3 états repose sur la couverture du GÈNE, qui fait plusieurs kilobases, alors que l'appel se
joue à la POSITION. Pour un SNP dans un gène bien couvert, l'approximation tient. Pour un indel,
elle peut rendre le verdict **inverse** du bon : sur l'indel de 2 pb de `Rv2566` chez *M. bovis*,
le seuil de gène classe 176 des 177 non-porteurs en `OFF`, c'est-à-dire en « vrais sauvages »,
alors que la fixation est en réalité **totale**.

Ce qui tranche est la **forme de la courbe** non-portage × couverture, que `--dose-response` rend :

| Profil observé | Lecture |
|---|---|
| décroissance monotone vers **zéro**, sans plateau | ce sont des **non-appels** ; le site est en réalité fixé |
| **plateau** non nul quand la couverture monte | ce sont de **vrais allèles de référence** |
| **plat à 100 %** à toutes les couvertures | absence **réelle** — profil attendu d'un groupe externe |

Exemple réel (site Bovis, sortie de la commande ci-dessus) : *M. bovis* passe de 57,1 % de
non-portage sous 20× à 0,03 % au-dessus de 80× et **0,00 % au-dessus de 120×** — décroissance vers
zéro, donc fixation totale ; *M. canettii* reste à 100 % à toutes les tranches — absence réelle.
Les deux profils, dans une même sortie, se lisent d'un coup d'œil.

`--dose-response` lit `report.json` pour TOUTES les souches du périmètre et non pour les seuls
non-porteurs : c'est le mode coûteux. La courbe est rendue **par groupe**, jamais agrégée —
mélanger un clade cible et son groupe externe, qui est par construction non porteur, fabrique un
plateau là où il n'y en a pas, donc le verdict inverse du bon.

### Précaution de lecture sur les conteneurs nus

Un « clade » de `bdd/actuelle` peut être un conteneur NON subdivisé de dizaines de milliers de
souches (`L1` en compte 21 163, `L2.2.1` 35 405). Stratifier dessus ne contrôle presque rien de la
sous-structure. Vérifier l'effectif de la strate avant de conclure qu'une fréquence par clade
« contrôle la lignée ».

## `align` : alignement propre pour datation (BEAST2 / RAxML)

Un alignement SNP-only brut a **trois défauts** qui sabotent une horloge
moléculaire (voir aussi le skill `beast2-dating`). `align` les corrige en amont :

```bash
MASK=global_supplementary/traces_mask/traces_mask_positions.txt
RDT=structural_variation_is_rd/data/bespiatykh_canonical_rd.csv
python3 $S/bdd_query.py --bdd ../../bdd align L4.15 \
    --mask $MASK --rd-table $RDT --out aln.phy
# -> aln.phy + aln.positions.txt, et suggère la commande beast2_binary.py
```

1. **`--mask`** : écarte les positions bruitées (PE/PPE, répétitions, éléments
   mobiles, résistance sous sélection). Réutilise le masque consolidé existant
   `traces_mask_positions.txt` (727 627 positions). Sur L4.15, ~23 % des colonnes
   sont écartées.
2. **Délétions RD → `?`** (par défaut ; `--no-rd` pour désactiver). Une RD est une
   délétion : les SNP qu'elle couvre sont **non-appelables** chez la souche
   porteuse, pas `0`. Les coder `0` double-compte l'événement et gonfle la
   branche. Les `CUS_GS_<start>_<stop>` de `missing_rd` portent leurs coordonnées
   dans le nom (auto-suffisants) ; `--rd-table` ajoute les RD nommés résolvables.
3. **`--genome-len` ajusté** : la sortie calcule le génome *appelable* =
   4 411 532 − positions masquées, à passer à `beast2_binary.py --ascertainment`
   pour un poids de sites constants cohérent.

### Génomes anciens (aDNA) : filtrage des transitions

Les aDNA (dossiers `bdd/ancien/`) portent des faux SNP de **désamination**
(C→T, G→A) qui gonflent leur branche terminale et faussent l'horloge (la souche
ancienne paraît plus dérivée que les modernes → pente racine-vs-temps négative,
biologiquement impossible).

```bash
python3 $S/bdd_query.py align L4.8.3 \
    --mask $MASK --rd-table $RDT \
    --adna Body92_Kay2015,Winstrup_LUND1 --adna-transversions --out aln.phy
```

`--adna` liste les souches anciennes (répétable ou liste séparée par virgules) ;
`--adna-transversions` code en `?` leurs SNP de type transition, ne gardant que
les transversions (non affectées par la désamination). Mesuré sur 2 aDNA L4.8 :
l'inflation de branche passe de **12× à 5×** la médiane moderne.

**Limite** : le résiduel (~5×) vient de la **couverture partielle** des aDNA,
un site non couvert est indistinguable d'un site ancestral dans un alignement
binaire SNP-only. Sans fichier de positions appelables (BED de couverture),
il n'est pas corrigeable proprement : coder toutes les absences aDNA en `?`
**surcorrige** (branche → ∞, le taxon perd toute information). Le filtrage des
transitions est le meilleur compromis disponible sur les seuls `spdi.txt`.

La sortie écrit `aln.phy` (PHYLIP relaxé binaire, `?` = manquant), `aln.positions.txt`
(une position génomique par colonne) et imprime la ligne `beast2_binary.py` prête.

**Diagnostic** : un alignement propre **doit** contenir des `?` ; zéro `?` signale
que les délétions RD ont été codées `0` (le piège n°1). Validé bout-à-bout sur
L4.15 : 52 souches, 3864→2966 sites après masque, 248 cellules `?`, BEAST2
accepte l'alignement filtré (`2966 sites + 3680939 constant sites`).

## `phylo_job.py` : alignement + RAxML-NG (BIN+G)

Construit un PHYLIP binaire (0/1 = absence/présence du variant) en ne gardant que
les **colonnes informatives** (ni toutes-0 ni toutes-1 : les positions fixées
n'apportent rien à l'arbre), puis :

```bash
python3 $S/phylo_job.py align  L4.15 --out phylo_out          # écrit .phy + .positions.txt
python3 $S/phylo_job.py run    L4.15 --out phylo_out          # + exécute raxml-ng en local
python3 $S/phylo_job.py run    L4.15 --all --bs 100           # ML + bootstrap
python3 $S/phylo_job.py submit L4.15 --out pkg                # paquet distant (align+submit.sh+params.json)
python3 $S/phylo_job.py --subsample 200 run L2.2.1            # pool géant -> 200 souches (reproductible)
python3 $S/phylo_job.py --bdd ../../bdd detect-raxml          # diagnostic : où est trouvé raxml-ng ?
```

- **Détection du binaire RAxML-NG** (ordre) : `$RAXML` → `investigate_phylo/raxml-ng`
  ancré sur l'outil **ou sur la BDD passée par `--bdd`** → `raxml-ng` dans le PATH.
  `detect-raxml` renvoie `{raxml, found, source}` pour diagnostiquer sans lancer de calcul.
  Depuis le dépôt `mtbc/`, la détection relative suffit ; sinon passer `--bdd` ou `$RAXML`.
- **`--subsample N`** : tire N souches (reproductible par `--seed`) avant l'alignement,
  indispensable pour les pools géants (L2.2.1 ≈ 35 k, L3 ≈ 8,7 k ; cf. `pistes.md` P4.28).
- `submit` produit un dossier autoportant : `rsync` vers le cluster puis `sbatch submit.sh`.
- Modèle `BIN+G` (aligné sur la convention du dépôt pour les alignements SNP 0/1).

## Notes

- Validé sur L4.15 (52 souches) : 3559 sites informatifs, arbre ML en ~55 s (BIN+G,
  logL ≈ −22440). Les pools géants (L2.2.1 ≈ 35 k, L3 ≈ 8,7 k) demandent un
  sous-échantillonnage avant un arbre brut (cf. `pistes.md` P4.28).
- Réutilisable tel quel comme brique derrière un serveur MCP si un jour vous voulez
  l'exposer comme connecteur, même CLI, une enveloppe en plus.

## Fidélité vs `investigate_phylo/get_phylo.py` (à lire avant usage en prod)

Ce pont est une **ré-implémentation légère**, pas un wrapper de `get_phylo.py`.
L'encodage 0/1 (présence/absence d'un SPDI) et le modèle `BIN+G` sont **identiques**
à ceux du pipeline canonique (`get_phylo.py`, `--model BIN+G`, `'1' if s in spdi_set
else '0'`). Différences volontaires, à connaître :

- **Colonnes** : `phylo_job.py` ne garde que les sites **informatifs** (ni tout-0 ni
  tout-1). `get_phylo.py` écrit le **pan-SPDI complet** (union de tous les variants).
  Les deux sont valides pour RAxML-NG, mais les alignements ne sont pas bit-à-bit identiques.
- **Format** : PHYLIP relaxé ici, **FASTA** dans `get_phylo.py`.
- **Outgroup** : `get_phylo.py` ajoute un outgroup (`spdi.txt` d'une souche de référence)
  et exclut le set `Ignore` ; ce pont ne fait ni l'un ni l'autre.

Pour un arbre destiné à publication, utiliser le pipeline canonique `get_phylo.py`.
Ce pont vise l'exploration rapide et l'usage identique Code/Science.
