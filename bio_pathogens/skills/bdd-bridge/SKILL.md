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
argument-hint: "clades | strain <clade> <SRA> | synapo <clade> | phylo run <clade>"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# bdd-bridge : pont read-only sur `bdd/actuelle/` + inférence phylo

Deux CLI **stdlib pure** (zéro dépendance), appelables à l'identique depuis
Claude Code (shell-out) et depuis un agent de calcul. Le but : que la lecture de
la base locale de souches et l'inférence phylo se fassent **de la même façon**
dans les deux environnements, sans serveur à maintenir.

## Localisation de la BDD

Par priorité : `--bdd <chemin>` → `$TBANNOTATOR_BDD` → `../bdd` remonté depuis le
script. Depuis un sous-projet, la BDD est en `../../bdd`. Toutes les opérations
sont **strictement en lecture**, aucun script n'écrit dans `bdd/`.

## `bdd_query.py` : lecture de la base

```bash
S=bio_pathogens/skills/bdd-bridge/scripts     # ou le canonical réel
python3 $S/bdd_query.py clades                 # tous les clades + effectif
python3 $S/bdd_query.py strains L4.15          # souches d'un clade
python3 $S/bdd_query.py --json strain L4.15 ERR1023322   # QC + nb SNP d'une souche
python3 $S/bdd_query.py matrix L4.15 --min-frac 0.1       # matrice SNP binaire -> TSV
python3 $S/bdd_query.py synapo L4.15                      # synapomorphies (frac >= 0.95)
python3 $S/bdd_query.py synapo L5.2.1 --recursive --min-frac 0.90  # agrège L5.2.1 + tout son sous-arbre L5.2.1.*
python3 $S/bdd_query.py align L4.15 --mask MASK.txt --rd-table RD.csv --out aln.phy  # alignement propre pour datation
```

- `clades` : `<clade>\t<n_souches>` (ignore les `_flatten_*_undo_log.tsv`).
- `strain` : lit `report.json` (couverture, profondeur, MAPQ, GC) + compte les SPDI.
- `matrix` : lignes = souches, colonnes = positions SPDI présentes chez ≥ `min_frac`
  des souches ; `--json` renvoie aussi le vecteur 0/1 par souche.
- `synapo` : positions partagées par ≥ seuil (défaut 0.95), candidates marqueurs de clade.
- `--recursive` (sur `strains`/`matrix`/`synapo`) : agrège le conteneur `clade` avec TOUT son
  sous-arbre `clade.*`. Indispensable dès qu'une lignée a été matérialisée en plusieurs
  sous-conteneurs (géographiques, phylogénétiques...) : sans ce flag, `synapo L5.2.1` ne voit que
  les souches du dossier racine `L5.2.1/` et ignore ses 7 sous-conteneurs `L5.2.1.*`, ce qui fausse
  toute comparaison à un marqueur ou barcode publié portant sur le clade entier.
- `align` : alignement binaire PHYLIP multi-clades **propre pour l'horloge moléculaire**
  (voir section dédiée ci-dessous).

Toute commande accepte `--json` (sortie structurée) et `--bdd`.

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
