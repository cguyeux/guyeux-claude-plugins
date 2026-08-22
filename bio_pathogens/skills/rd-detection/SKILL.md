---
name: rd-detection
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST) for regions of difference
  (RD) in MTBC genomes of published research isolates: reading the RD calls the
  TBannotator pipeline already produces, and cross-checking them with an
  independent published implementation (RDscan, Bespiatykh et al., mSphere 2021).
  Use when: an RD-based argument enters a manuscript, a clade is defined by a
  deletion, a new candidate deletion (CUS) needs confirming, or an RD call
  contradicts the literature and one needs to know which side is wrong.
argument-hint: "<souche|clade> [--crosscheck] [--rd RD9|RD105|...]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# Régions de différence : lire les appels existants, et les recouper

## Pourquoi ce skill existe

Les RD portent des arguments phylogénétiques lourds (une délétion partagée définit un clade, et
c'est un caractère quasi irréversible, donc précieux). Or nos appels de RD viennent d'**une seule
implémentation, la nôtre**, dont les seuils ont été fixés en interne. Une méthode maison non recoupée
qui décide d'un clade dans un manuscrit est un point faible en évaluation par les pairs.

## Ce que la chaîne produit déjà, et où

Par souche, dans `mp:/data/current/run/results/<SRA>/` (VPN requis, voir `remote-compute`) :

| fichier | contenu |
|---|---|
| `coverage_report_rd.bed.tsv` | RD **connues** de la littérature, avec couverture, médiane, ratio, score de qualité |
| `coverage_report_dynamic_rd.bed.tsv` | RD **candidates détectées de novo**, nommées `CUS_GS_<start>_<end>` |
| `clipping_info.tsv` | le signal brut de clipping, dont dérivent les deux précédents |
| `report.json` (champ `large_rd`/`missing_rd`) | même donnée, plus l'appel binaire déjà calculé |

**Méthode maison, lue au code source (pas au résumé) le 2026-08-17** sur `mp:/data/current/run/`
(pipeline Snakemake de gsenelle, `rules/clipping.smk` + `rules/coverage.smk` +
`scripts/{clipping_info,dynamic_rd,regions_coverage}.py` + `scripts/json_report.py`) :

1. **Clipping brut** (`clipping_info.py`) : pour chaque read mappé sur `mapped.cram`, on retient les
   séquences soft-clippées d'au moins **10 pb** de chaque côté (`minClipping = 10`).
2. **Signal groupé** (`rules/clipping.smk`) : les positions de clipping sont groupées et comptées ;
   seules celles portées par **> 10 reads** (`minCount`) passent en signal.
3. **Flancs** : les régions candidates sont bordées d'une marge de **20 pb** (`flankSize`), et le
   croisement flanc↔signal exige un recouvrement `bedtools intersect -F 0.5` (**≥ 50 %**).
4. **Score de qualité** (`regions_coverage.py`, fonction `analysis()`) : les séquences clippées de
   chaque flanc (fenêtre **200 pb**, `pair_side_size`) sont réalignées (Biopython `pairwise2.align.localms`,
   scores +1/-1/-1/-0.5) contre la séquence de référence du côté opposé sur un chevauchement de **40 pb**
   (`sequence_overlap_length`) ; une séquence compte comme "haute qualité" si `score/longueur > 0.8`
   (`min_quality_score`). Le score final = moyenne des deux flancs (0-1), plafonné à 1.
5. **Couverture** : `mean_ratio` = profondeur moyenne de la région / profondeur moyenne du génome ;
   `low_coverage` = fraction de bases sous une profondeur minimale de **5×** (`minDepth`).
6. **`other`** (`other_mutation_signal`) : signal de clipping supplémentaire près des bornes qui ne
   fait PAS partie de la paire retenue — un signe de mutation complexe, pas d'une délétion nette.

**L'appel binaire présent/absent n'est PAS une colonne du TSV** : `coverage_report_rd.bed.tsv` et
`coverage_report_dynamic_rd.bed.tsv` ne portent que les mesures brutes (`quality`, `low_coverage`,
`mean_ratio`, `other`…). Le seuillage qui produit `missing_rd` dans `report.json` (`json_report.py`,
lu en source) est un **OU de trois conditions**, PAS un ET, et diffère entre RD connues et candidates :

| jeu | condition de « RD absente / délétée » (`report.json.missing_rd`) |
|---|---|
| RD connues (`large_rd`) | `quality > 0.8` **OU** `low_coverage > 0.95` **OU** `mean_ratio < 0.1` |
| RD candidates (`dynamic_rd`/CUS) | `quality > 0.8` **uniquement** (plus exigeant : pas de repli couverture) |
| gènes (`missing_genes`, pour référence) | `low_coverage > 0.8` **OU** `mean_ratio < 0.1` (seuil de couverture différent, 0.8 pas 0.95) |

> [!IMPORTANT]
> **Un appel de RD n'est pas une absence de couverture, et le seuil OU n'est pas un ET.** Une
> couverture faible peut venir d'un biais GC, d'un sous-échantillonnage, ou d'une région répétée où
> les lectures ne mappent pas de façon unique — c'est pour ça que `quality` (le signal de clipping)
> suffit SEUL à déclarer une RD connue absente, indépendamment de la couverture. Un texte antérieur de
> ce skill (et de `~/.claude/knowledge/tuberculosis.md`) disait « profondeur >90 % ET ratio <10 % ET
> score ≥80 % » : c'est faux sur les trois points (seuil couverture réel 95 % pas 90 %, c'est un OU pas
> un ET, et `quality` seul suffit). `scripts/crosscheck_rdscan.py known` calcule l'appel avec la
> formule vérifiée ci-dessus par défaut (`--rd-type known|dynamic`), pas une colonne devinée.

## Recoupement indépendant : RDscan

`RDscan` (Bespiatykh et al., *mSphere* 2021, `10.1128/mSphere.00535-21`, MIT,
`github.com/dbespiatykh/RDscan`) est un pipeline Snakemake qui cherche délétions et RD putatives dans
des génomes MTBC, et sait aussi travailler sur des assemblages. C'est une implémentation
**indépendante** du même calcul : le contrôle le moins cher qui existe sur nos appels.

Protocole de recoupement, en trois temps :

1. **Choisir un jeu témoin où la réponse est connue** : quelques souches dont l'appartenance de lignée
   est certaine et dont les RD diagnostiques sont publiées (RD9 pour la séparation *tuberculosis* /
   animale, RD105 pour L2, RD750 pour L3...). Un recoupement sans témoin positif ne mesure rien.
2. **Comparer l'appel, et les bornes quand elles existent** : pour les RD connues, RDscan rend un
   appel présent/absent par échantillon sur des bornes fixes (celles de `resources/RD.bed`) — seul
   l'appel se compare. Pour les RD candidates, RDscan rend une coordonnée par détection : un désaccord
   de **bornes** de quelques dizaines de paires de bases n'est alors pas un désaccord d'appel, c'est
   une différence de définition du flanc.
3. **Documenter les désaccords dans le cahier de labo**, en distinguant les trois cas : la chaîne
   appelle et RDscan non, l'inverse, ou les deux appellent avec des bornes divergentes. Seul le
   deuxième cas suggère un défaut de sensibilité chez nous.

`scripts/crosscheck_rdscan.py` outille les trois temps, souche par souche (`--sample`), pas en batch
sur toute la cohorte. **Format RDscan vérifié sur le source du dépôt** (commit `f7e2d91`, 2026-08-17 :
`workflow/scripts/makeTables.R`, `proportions.py`, `concatenate_bed.py`, `resources/RD.bed`) : ce
n'est pas une table longue par RD, mais deux matrices larges cohort-wide, d'où deux sous-commandes.

```bash
# RD connues (RD9, RD105, RD750...) : notre table vs RD_known.bin.tsv (ligne = echantillon, colonne = RD)
python3 scripts/crosscheck_rdscan.py known coverage_report_rd.bed.tsv RD_known.bin.tsv \
    --sample SRR12345678 --witness RD9,RD105,RD750 -o crosscheck_known.tsv

# RD candidates (CUS) : notre table vs RD_putative.tsv (ligne = deletion candidate, colonne = echantillon)
python3 scripts/crosscheck_rdscan.py putative coverage_report_dynamic_rd.bed.tsv RD_putative.tsv \
    --sample SRR12345678 --margin 100 -o crosscheck_putative.tsv
```

> [!IMPORTANT]
> `RD_known.bin.tsv` ne porte **aucune coordonnée** : les bornes des RD connues sont fixes, définies
> une fois pour toutes dans `resources/RD.bed` de RDscan, donc le mode `known` compare uniquement des
> appels (présent/absent), jamais des bornes. La comparaison de bornes n'a de sens que pour les RD
> candidates (`putative`), où RDscan rend une coordonnée par détection.

> [!CAUTION]
> **Ne pas remplacer nos appels par ceux de RDscan sans mesure.** L'outil est publié, ce qui ne le rend
> pas plus juste : il a ses propres seuils. L'objectif est un **accord chiffré** (« N RD concordantes
> sur M, désaccords sur telles bornes »), pas un changement de source de vérité. Un accord élevé rend
> l'argument RD du manuscrit défendable ; un désaccord localisé est en soi un résultat.

## Nouvelles RD candidates (CUS)

`scripts/dynamic_rd.py` (lu en source) : un CUS est une paire signal-droit → signal-gauche, tous deux
à > 10 reads, dont l'écart au génome de référence est **< 30 pb** (constante codée en dur, pas un
paramètre de config malgré ce qu'un résumé antérieur laissait entendre) ; nommage
`CUS_GS_<startInclus0based>_<endExclus0based>`. Un candidat, pas une RD établie. Avant d'en faire un
caractère de clade : recouper avec RDscan, vérifier qu'aucune étude ne l'a déjà nommée (`lit-review`,
et `tbmonitor-papers` pour la littérature TB), et contrôler qu'elle ne tombe pas dans une région
PE/PPE ou riche en IS, où les artefacts abondent (`isfinder-offline`, et `mtbc-lineages` pour ce que
la chaîne appelle réellement IS6110 — voir ci-dessous).

**Piège de sens** : une IS présente chez H37Rv et absente de la souche produit un signal de
délétion ; c'est bien une RD, mais son mécanisme est la perte d'un élément mobile, pas une délétion
chromosomique classique. Le distinguer change l'interprétation évolutive.

**Le même moteur sert à appeler IS6110** (`scripts/insertion_sequence.py`, `is_report.json`), avec un
piège d'interprétation propre, différent de celui des RD : la liste `insertion_sequences` de
`report.json` **ne contient que des appels positifs** (IS confirmée présente en référence OU nouvelle
insertion confirmée) — il n'existe **aucune entrée pour une IS confirmée absente**. Une position IS
absente de cette liste peut donc vouloir dire trois choses indiscernables sans relire les fichiers de
couverture bruts : (1) délétion nette confirmée (`quality ≥ 0.8`), (2) signal ambigu et donc écarté
(`other > 0`, mutation complexe aux abords), ou (3) position simplement non testée. Ceci explique la
zone « 1-2 copies = borderline » de `mtbc-lineages` (`is-mtbc`) : un compte bas peut être un vrai
signal évolutif ou un artefact de filtrage silencieux. Ne jamais lire un compte IS6110 bas comme une
« absence confirmée » sans recouper `coverage_report_is.bed.tsv` (mêmes colonnes que les RD :
`quality`, `low_coverage`, `mean_ratio`, `other`).

## Composition

`fetch-tbannotator` (rapatrier les rapports) → **`rd-detection`** (lire et recouper) →
`mtbc-lineages` / `lineage-comparison` (que dit la nomenclature ?) → `panisa` (est-ce un élément
mobile ?) → `claim-check` (le chiffre du manuscrit correspond-il aux données ?).
