---
name: strain-qc
description: >-
  Controle qualite d'une souche MTBC avant integration dans la BDD ou
  un arbre phylogenetique. Verifie 7 criteres : (1) chimere intra-MTBC
  par classification multi-systeme, (2) taux GC, (3) couverture du
  genome, (4) profondeur de sequencage, (5) nombre de SPDI vs
  distribution de la lignee, (6) contamination inter-especes par
  signature des genes housekeeping, (7) qualite de mapping (genes
  manquants vs depth). Produit un verdict PASS/WARN/FAIL avec
  justification. Fonctionne en mode souche unique ou lot.

  Use when: importing new strains from SRA/ENA, filtering strains
  before phylogenetic reconstruction, investigating a strain with
  aberrant placement or long branch in a tree, screening a BDD for
  problematic entries, or when get_phylo.py reports exclusions and
  you want to understand why. When a WARN/FAIL verdict is produced on
  a strain, check `tbmonitor-papers` for any published study mentioning
  the same SRA / BioProject (could be a known problematic dataset
  reported elsewhere, or conversely a strain validated in a previous
  study despite borderline metrics).
argument-hint: "<SRA|dir|spdi.txt> [--batch <list.txt>] [--strict]"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
user-invocable: true
---

# /strain-qc -- Controle qualite des souches MTBC

Evalue la qualite d'une souche MTBC en appliquant 7 criteres
diagnostiques. Chaque critere produit un verdict independant (PASS,
WARN, FAIL), et le verdict global est le pire des 7.

**Principe** : mieux vaut exclure une souche douteuse que contaminer
un arbre phylogenetique. Un FAIL sur un seul critere suffit a
recommander l'exclusion.

---

## Declenchement

```
/strain-qc SRR12345678                    # QC d'une souche (cherche dans la BDD)
/strain-qc ~/path/to/strain/dir           # QC depuis un repertoire souche
/strain-qc spdi.txt                       # QC minimal (SPDI seul, pas de stats)
/strain-qc --batch strains.txt            # QC en lot (un SRA par ligne)
/strain-qc SRR12345678 --strict           # Seuils plus exigeants
```

---

## Phase 0 -- Resolution de l'entree

### Souche unique

1. Si l'argument est un accession SRA (SRR/ERR/DRR) :
   - Chercher dans la BDD locale :
     ```bash
     find ~/docs/codes/mtbc/bdd/actuelle/ \
       -maxdepth 2 -name "<SRA>" -type d
     ```
   - Si trouve : utiliser ce repertoire comme source.
   - Si absent : chercher dans `bdd/ignorees/` (souche deja exclue).
   - Si nulle part : signaler et proposer `/fetch-tbannotator`.

2. Si l'argument est un repertoire : l'utiliser directement.

3. Si l'argument est un fichier `spdi.txt` ou `snps.vcf` : mode
   degrade (seuls les criteres 1 et 5 sont evaluables).

### Mode lot

Lire le fichier `--batch` (un SRA par ligne, lignes vides et `#`
ignorees). Traiter chaque souche sequentiellement.

---

## Les 7 criteres de qualite

**Vue d'ensemble des criteres et de ce qu'ils detectent** :

| Critere | Detecte | Mecanisme |
|---------|---------|-----------|
| 1. Chimere intra-MTBC | Co-infection ou melange de 2 souches MTBC | Marqueurs de 2 lignees de base |
| 2. Taux GC | Contamination massive par un organisme a GC different | GC global hors 61-69% |
| 3. Couverture | Sequencage incomplet | % bases H37Rv couvertes |
| 4. Profondeur | Sequencage superficiel | Depth moyen |
| 5. Nombre de SPDI | Deficit (filtrage) ou exces (contamination) | vs distribution de la lignee |
| 6. **Contamination inter-especes** | Reads d'une NTM/bacterie environnementale | **SNPs dans rpoB/rpoC/housekeeping + MNP + depth bimodal** |
| 7. **Qualite de mapping** | Problemes d'assemblage ou biais de reference | **Genes manquants eleves malgre bonne depth** |

Les criteres 6 et 7 ont ete ajoutes apres l'identification de cas
reels dans la BDD (cf. section "Cas de reference" a la fin).

### Critere 1 : Detection de chimere intra-MTBC

**Important.** Une chimere est un echantillon contenant l'ADN de deux
souches MTBC differentes. Le signal : la souche porte les marqueurs
definissant de deux lignees de base MTBC incompatibles.

**Note** : ce critere ne detecte PAS une contamination par un
organisme non-MTBC (NTM, bacterie environnementale) — pour cela,
voir le Critere 6.

#### Methode

1. Lancer la classification multi-systeme via le script existant :
   ```bash
   python3 ~/docs/codes/claude_plugins/bio_pathogens/skills/mtbc-lineages/scripts/lineages.py \
     classify <spdi.txt|snps.vcf|dir> --min-pct 50
   ```

2. Pour chaque systeme de taxonomie, extraire les lignees de base
   (sans point dans le code : `1`, `2`, `3`, `4`, `5`, `6`, `7`,
   `8`, `9`, `10`, ou les lignees animales `La1`-`La4`,
   `BOV`, `BOV_AFRI`, etc.).

3. **Test de chimere** : si une souche matche >=2 lignees de base
   dans un meme systeme avec un score >=50%, c'est un signal fort
   de chimere.

4. **Verification multi-systeme** : le signal est confirme si la
   chimere est detectee dans au moins 2 systemes parmi :
   Coll, Freschi, Napier, Shitikov23, moi.

#### Seuils

| Condition | Verdict |
|-----------|---------|
| 0-1 lignee de base dans tous les systemes | PASS |
| 2+ lignees de base dans 1 seul systeme | WARN — chimere possible |
| 2+ lignees de base dans 2+ systemes | FAIL — chimere probable |

#### Sortie

```
Critere 1 : Chimere/Pollution
  Verdict : FAIL
  Detail  : marqueurs de L2 ET L4 detectes
    - Coll: L2 (100%), L4 (100%)
    - Freschi: 2 (100%), 4 (100%)
    - Napier: 2 (15/17 = 88.2%), 4 (12/14 = 85.7%)
    - moi: 2, 4
  Interpretation : cette souche contient probablement un melange
    d'ADN de L2 et L4. Cela peut resulter d'une co-infection, d'une
    contamination en laboratoire, ou d'une erreur d'assemblage.
  Action : exclure de la BDD et de tout arbre phylogenetique.
```

### Critere 2 : Taux GC

Le genome de M. tuberculosis a un taux GC de ~65.6%. Un ecart
significatif indique une contamination par un autre organisme.

#### Methode

Lire le `report.json` de TBannotator :
```python
gc = report['quality']['after_filtering']['gc_content']
```

Si `report.json` absent : tenter de recuperer le taux GC depuis les
metadonnees SRA via l'API NCBI (Entrez).

#### Seuils

| Taux GC | Verdict |
|---------|---------|
| 61% - 69% | PASS |
| 59% - 61% ou 69% - 71% | WARN — GC marginal |
| < 59% ou > 71% | FAIL — GC incompatible avec MTBC |

En mode `--strict` : PASS = 63% - 68%.

#### Sortie

```
Critere 2 : Taux GC
  Verdict : PASS
  GC      : 65.4%
  Attendu : 61% - 69% (MTBC normal : ~65.6%)
```

### Critere 3 : Couverture du genome

Le pourcentage de bases du genome de reference (H37Rv) couvertes par
au moins 1 read.

#### Methode

Lire le `report.json` de TBannotator :
```python
coverage = report['mapping_stats']['covered_bases_percent']
```

#### Seuils

| Couverture | Verdict |
|------------|---------|
| >= 95% | PASS |
| 90% - 95% | WARN — couverture faible |
| < 90% | FAIL — couverture insuffisante |

En mode `--strict` : PASS = >= 98%.

#### Sortie

```
Critere 3 : Couverture du genome
  Verdict : PASS
  Couverture : 99.2% des bases de H37Rv couvertes
```

### Critere 4 : Profondeur de sequencage

La profondeur moyenne de lecture sur le genome.

#### Methode

Lire le `report.json` de TBannotator :
```python
depth = report['mapping_stats']['mean_depth']
```

#### Seuils

| Profondeur | Verdict |
|------------|---------|
| >= 30x | PASS |
| 15x - 30x | WARN — profondeur moderee |
| < 15x | FAIL — profondeur insuffisante |

En mode `--strict` : PASS = >= 50x.

Note : une profondeur de 15-30x est suffisante pour le SNP calling
mais rend difficile la detection de variants heterogenes (mixed
infections faible ratio).

#### Sortie

```
Critere 4 : Profondeur de sequencage
  Verdict : WARN
  Profondeur : 22.4x (moyenne)
  Note : suffisant pour SNP calling, mais detection de mixed
    infections limitee en dessous de 30x.
```

### Critere 5 : Nombre de SPDI vs distribution de la lignee

Le nombre total de variants (SPDI) est un indicateur de qualite. Un
deficit signale generalement un probleme de profondeur ou de
mapping ; un exces signale une contamination.

#### Methode

Compter les lignes du fichier `spdi.txt` :
```bash
wc -l <dir>/NC_000962.3/spdi.txt
```

Comparer avec la distribution de reference de la lignee identifiee
au Critere 1.

#### Distributions de reference par lignee (mesurees sur bdd/actuelle)

Valeurs calculees le 2026-04-12 sur l'ensemble de la BDD :

| Lignee | n | Min | Q25 | Mediane | Max |
|--------|---|-----|-----|---------|-----|
| L1.2.1 | 154 | 1671 | 2007 | 2064 | 2233 |
| L1.2.2 | 156 | 1766 | 2029 | 2069 | 2389 |
| L2.2.2 | 2110 | 1311 | — | ~1400 | 1510 |
| L4.1 | 11389 | 464 | 966 | 994 | 1119 |
| L4.1.1 | 1006 | 681 | 966 | 1001 | 1111 |
| L4.1.2 | 2011 | 591 | 966 | 994 | 1077 |
| L4.8 | 4446 | 251 | — | 582 | 717 |
| L4.9 | 815 | 181 | — | 347 | 509 |
| L5.2 | 172 | 2001 | — | 2221 | 2354 |
| L6 (all) | 1645 | 1397 | 2280 | 2324 | 2475 |
| L7 | 80 | 1945 | — | 2155 | 2352 |
| Bovis | 159 | 2261 | 2430 | 2453 | 2549 |
| Microti | ~50 | 2159 | — | — | 2214 |
| Caprae | ~30 | 2467 | — | — | 2617 |
| Orygis | ~20 | 2670 | — | — | 2740 |

Pour les lignees absentes de cette table, calculer la distribution
en direct :
```bash
for s in ~/docs/codes/mtbc/bdd/actuelle/<LINEAGE>/*/NC_000962.3/spdi.txt; do
  wc -l < "$s"
done | sort -n
```

#### Seuils

Soient `min_l`, `max_l` les bornes observees pour la lignee.

| Condition | Verdict |
|-----------|---------|
| min_l <= SPDI <= max_l | PASS |
| 0.9·min_l <= SPDI < min_l ou max_l < SPDI <= 1.1·max_l | WARN |
| SPDI < 0.9·min_l ou SPDI > 1.1·max_l | FAIL |

**Exces important** (SPDI > 1.3·max_l) : forte suspicion de
contamination inter-especes — declencher le Critere 6.

Si la lignee est inconnue : appliquer les seuils generiques
(800-3000 PASS, <500 ou >4000 FAIL).

#### Sortie

```
Critere 5 : Nombre de SPDI vs lignee
  Verdict : PASS
  SPDI    : 2188
  Lignee  : L1.2.2 (mesure 1766-2389, n=156, mediane 2069)
```

### Critere 6 : Contamination inter-especes

**Detecte une contamination par un organisme non-MTBC** (mycobacterie
non-tuberculeuse, bacterie environnementale) dont les reads mappent
sur les regions conservees du genome H37Rv. Ce type de contamination
**n'est PAS detecte** par le Critere 1 (chimere) car le contaminant
n'a pas les marqueurs MTBC.

**Mecanisme** : les genes les plus conserves entre especes bacteriennes
(rpoB, rpoC, groEL, dnaK, tuf, ftsZ, proteines ribosomales) ont des
homologues chez toutes les bacteries. Les reads d'un contaminant
trouvent ces homologues dans H37Rv et y mappent avec suffisamment
d'identite pour passer les filtres de qualite, mais suffisamment de
divergence pour produire des centaines de faux SNPs — souvent sous
forme de MNP (multi-nucleotide polymorphisms).

#### Methode

Parser le `report.json` pour calculer 4 indicateurs :

1. **SNPs rpoB** : nombre de SPDI dans la fenetre `759807-763325`
2. **SNPs rpoC** : nombre de SPDI dans la fenetre `763370-767320`
3. **Ratio MNP** : fraction de SPDI ou `len(ref) > 1` ou `len(alt) > 1`
4. **Ratio depth HK/autre** : depth median dans les genes housekeeping
   divise par depth median dans les autres genes

Genes housekeeping a surveiller :
```python
HOUSEKEEPING = {'rpoB', 'rpoC', 'groEL2', 'dnaK', 'tuf', 'fusA1',
                'ftsZ', 'ftsH', 'infB', 'secA1', 'clpX', 'clpC1',
                'clpP2', 'rpsA', 'rpsB', 'rpsC', 'rpsE', 'rpsL',
                'recA', 'gyrA', 'gyrB'}
```

**ATTENTION Rv0215c** : dans les report.json de TBannotator v1, un
bug d'annotation snpEff etiquette faussement `gene_name='gene-Rv0215c'`
a des SNPs repartis sur tout le genome (positions 258k a 4074k) avec
`feature_type='gene_variant'` et `gene_locus_tag=null`. Le vrai gene
Rv0215c ne fait que ~5 kb (253455-258660). Toujours filtrer ces
annotations parasites :
```python
for ann in snp['annotations']:
    if ann.get('gene_name') == 'gene-Rv0215c' and \
       ann.get('feature_type') == 'gene_variant' and \
       ann.get('gene_locus_tag') is None:
        continue  # bug d'annotation v1, ignorer
    # ... utiliser cette annotation
```

#### Seuils

Pour une souche MTBC saine, chaque housekeeping porte typiquement
0-3 SNPs, les MNP sont <10%, et le depth est uniforme.

| Indicateur | PASS | WARN | FAIL |
|------------|------|------|------|
| rpoB + rpoC (SNPs) | <=5 | 6-10 | >10 |
| Ratio MNP | <10% | 10-15% | >15% |
| Ratio depth HK/autre | <1.5 | 1.5-3 | >3 |

**Verdict combine** : FAIL si au moins 2 indicateurs sur 3 sont FAIL,
ou si rpoB+rpoC >15 (seuil absolu).

#### Sortie

```
Critere 6 : Contamination inter-especes
  Verdict : FAIL
  rpoB + rpoC SNPs : 88 (attendu <=5)
  Ratio MNP        : 24.7% (attendu <10%)
  Depth HK/autre   : 7.6x (attendu ~1.0)
  Top housekeeping : rpoC (47), rpoB (41), groEL2 (38), dnaK (36)
  Interpretation : signature classique de contamination par une
    bacterie non-MTBC. Les reads du contaminant mappent sur les
    genes conserves de H37Rv et produisent des centaines de faux
    SNPs, concentres dans les housekeeping et sous forme de MNP.
  Action : exclure de la BDD et lancer /species-id pour identifier
    le contaminant.
```

### Critere 7 : Qualite de mapping (genes manquants)

**Detecte les problemes d'assemblage ou de mapping** distincts de la
profondeur de sequencage. Une souche avec une excellente depth mais
beaucoup de genes manquants signale un probleme au niveau du
pipeline de variant calling, pas du sequencage.

#### Methode

Lire le `report.json` :
```python
n_missing = len(report.get('missing_genes', []))
depth = report['mapping_stats']['mean_depth']
```

Le nombre total de genes dans H37Rv est ~3978, donc 1% ≈ 40 genes.

#### Seuils

| Condition | Verdict |
|-----------|---------|
| n_missing <= 50 | PASS |
| 50 < n_missing <= 100 | WARN |
| n_missing > 100 | FAIL |

**Paradoxe depth/mapping** : si depth >= 50x ET n_missing > 50,
signaler explicitement que le probleme n'est pas le sequencage mais
le mapping. Causes possibles :
- Grandes deletions ou rearrangements par rapport a H37Rv
- Reads chimeriques mal filtres
- Contamination eucaryote qui absorbe les reads au mapping
- Biais de reference H37Rv pour les lignees phylogenetiquement
  distantes (L1, L5, lignees animales)

#### Sortie

```
Critere 7 : Qualite de mapping
  Verdict : FAIL
  Genes manquants : 163 / 3978 (4.1%)
  Depth           : 185x (excellent)
  Paradoxe detecte : depth eleve mais mapping incomplet
  Interpretation : le probleme n'est pas le sequencage mais le
    mapping. Possibles causes : grandes deletions vs H37Rv,
    reads chimeriques, biais de reference.
  Action recommandee : re-annoter avec TBannotator v3 ou verifier
    si la lignee est distante de L4 (biais de reference).
```

### Critere 8 : Identification taxonomique (MTBC / Canettii / NTM / candidat nouveau)

**Ajoute apres la campagne d'audit a_ranger (2026-05).** Les criteres 1-7
detectent les problemes de qualite et de contamination, mais ne tranchent
PAS l'identite taxonomique d'une souche divergente : est-ce du MTBC a
ranger en lignee, du *M. canettii* (MTBC sensu lato legitime), un NTM
misclassifie, ou une vraie nouveaute ? Ce critere le decide, en s'appuyant
sur les references de `global_supplementary/`.

**A declencher** quand nSPDI eleve (> ~2700) ou %MNP > 18% (souche divergente).

#### References (toutes dans `~/docs/codes/mtbc/global_supplementary/`)

- `M_kansasii_robust_markers_201_*.txt` : 201 marqueurs SPDI **specifiques**
  M. kansasii. **Le discriminant kansasii** : >=50/201 => M. kansasii.
- `M_kansasii_spdi_markers_3789_*.txt` : 3789 marqueurs (core MKC) ; donne
  un signal de **fond du complexe** (8-20% chez un NTM du clade), PAS
  kansasii-specifique.
- `Canettii_ancestral_markers_3679_*.txt` : marqueurs ancestraux Canettii.
  **PIEGE** : biaises vers une sous-lignee de reference ; *M. canettii* est
  polyphyletique (STB-A a STB-L), donc une vraie Canettii d'une branche
  divergente (ex STB-K) donne **canettii_pct = 0** malgre une couverture
  excellente. **Ne JAMAIS conclure "pas Canettii" sur ce seul critere.**
- 11 type strains hors-MTBC dans `bdd/hors_mtbc/` (genomes), clades MTBAP
  (decipiens/lacus/riyadhense/shinjukuense) et MKC (kansasii/persicum/
  pseudokansasii/innocens/attenuatum/ostraviense). Le panel NE CONTIENT
  PAS Canettii.
- Classifieur cle-en-main : `a_ranger_phylo/analyses/taxo_classify.py`
  (`Classifier().classify(snv, cov_pct, mnp_pct, nspdi, ...)`).

#### Reperes diagnostiques (calibres campagne a_ranger 2026-05)

| Profil | Verdict taxonomique |
|--------|---------------------|
| %MNP ~10-12% + nSPDI <2700 + barcode hit | MTBC normal -> ranger en lignee |
| %MNP <18% + nSPDI >= 8000 + best_NTM<40% + kan_full<5% | **M. canettii** (MTBC s.l.), meme si canettii_pct=0 |
| %MNP >30% + kansasii robuste >=50/201 | **M. kansasii** |
| %MNP >25% + match plat type strains MKC/MTBAP (30-50%, pas de pic) | **NTM** du super-clade MKC/MTBAP, espece indeterminee |
| %MNP >25% + cov H37Rv <5% | NTM cross-mapping epars (basse couverture) |
| %MNP >25% + cov >50% + ne matche AUCUNE espece (best<40%, kan_full<10%, can<10%) + multi-BioProject independants | **CANDIDAT NOUVEAU** -> investiguer (ne pas trancher) |

**Garde-fou anti-fausse-espece (imperatif, cf. CLAUDE.md global)** :
le %MNP eleve + nSPDI eleve seuls NE suffisent PAS a revendiquer une
nouveaute. Deux fausses "especes nouvelles" ont ete evitees en 2026-05
(projet sp_novel = M. kansasii ; cluster3 = NTM MKC) precisement parce
que la couverture et les marqueurs robustes ont ete verifies. Toujours :
(1) tester les 201 marqueurs robustes kansasii, (2) verifier la couverture
H37Rv (un "candidat" a cov <10% est un artefact de cross-mapping), (3)
inclure M. kansasii et tout le panel hors_mtbc avant toute revendication.

#### Sortie

```
Critere 8 : Identification taxonomique
  Verdict : NTM (complexe M. kansasii)
  Detail  : %MNP 37%, kansasii robuste 0/201, match plat lacus/ostraviense 43%,
            canettii 0% (non informatif), cov 52%
  Interpretation : NTM du super-clade MKC/MTBAP misclassifie 'M. tuberculosis'.
  Routage : bdd/hors_mtbc/Mycobacterium_MKC_sp/
```

---

## Phase 2 -- Verdict global, decision de routage et rapport

### Verdict global (qualite)

| Pire critere | Verdict global |
|-------------|----------------|
| Tous PASS | PASS — souche de bonne qualite |
| Au moins un WARN | WARN — souche acceptable avec reserve |
| Au moins un FAIL | FAIL — souche a exclure |

### Decision de routage (croise qualite + identite taxonomique)

Le verdict qualite (criteres 1-7) et l'identite (critere 8) se combinent en
une **decision de rangement** dans la BDD :

| Situation | Decision |
|-----------|----------|
| Qualite FAIL avere (chimere, contamination, GC aberrant, cov<30%, mapping defaillant) | -> `bdd/ignore/<sous-rep justifie>` (creer un sous-repertoire nommant la cause + README) |
| Qualite OK + identite MTBC | -> `bdd/actuelle/<lignee>` (lignee par le barcoder v2 sur `barcoding_v2/barcode_complete.tsv` + placement `bdd/actuelle/` ; voir `SOURCES_OF_TRUTH.md`. NE PAS lire `snp_barcoding.csv` = v1 obsolete) |
| Identite NTM (kansasii/MKC/MTBAP) | -> `bdd/hors_mtbc/Mycobacterium_<espece-ou-MKC_sp>/` (+ meta.json) |
| Identite M. canettii | -> `bdd/actuelle/Canettii/` |
| Identite lignee animale (bovis/orygis/africanum...) | -> `bdd/actuelle/<lignee animale>` |
| CANDIDAT NOUVEAU (divergent, bien couvert, ne matche rien) | -> **NE PAS ranger** ; flag pour investigation dediee (spin-off projet) |
| Quasi-vide (nSPDI <200) ou cov <30% | -> `bdd/ignore/low_quality_empty` |

**Regle de prudence** : ne jamais ranger une souche comme "nouvelle espece"
automatiquement. Un candidat survit seulement apres verification adversariale
(couverture, marqueurs robustes, panel complet hors_mtbc). En cas de doute,
laisser en place et signaler.

### Rapport souche unique

```
=== Strain QC : <SRA> ===
Lignee detectee : <lignee Guyeux> (systeme "moi")
Source : <chemin BDD>

Critere 1 : Chimere intra-MTBC ........... PASS
Critere 2 : Taux GC (65.4%) ............. PASS
Critere 3 : Couverture (99.2%) .......... PASS
Critere 4 : Profondeur (42.1x) .......... PASS
Critere 5 : SPDI (2188 vs L1.2.2) ....... PASS
Critere 6 : Contamination inter-especes . PASS
Critere 7 : Qualite de mapping (12 mg) .. PASS

Verdict global : PASS ✓

[Si FAIL ou WARN, detail du/des critere(s) concerne(s)]
```

### Rapport lot

```
=== Strain QC — Lot (N souches) ===
Mode : standard | strict
Date : YYYY-MM-DD

| SRA | Lignee | GC | Couv. | Prof. | SPDI | Chim. | ISx | Map | Verdict |
|-----|--------|-----|-------|-------|------|-------|-----|-----|---------|
| SRR001 | L1.2.2 | 65.4% | 99.2% | 42x | 2188 | - | - | - | PASS |
| SRR002 | L4/L2? | 64.1% | 97.8% | 31x | 1847 | L2+L4 | - | - | FAIL |
| SRR003 | L4.1 | 55.2% | 88.1% | 12x | 643 | - | - | - | FAIL |
| SRR004 | L2 | 65.5% | 99.8% | 84x | 2035 | - | !!! | - | FAIL |
| SRR005 | L1.2.1 | 65.3% | 98.5% | 185x | 1917 | - | - | 163 | FAIL |

Resume :
  PASS : 1
  WARN : 0
  FAIL : 4
    - SRR002 : chimere L2+L4 (critere 1)
    - SRR003 : GC 55.2% + couverture 88.1% + profondeur 12x (criteres 2,3,4)
    - SRR004 : contamination inter-especes rpoB=41 MNP=24.7% (critere 6)
    - SRR005 : mapping defaillant 163 genes manquants a 185x (critere 7)

Souches a exclure :
  SRR002, SRR003, SRR004, SRR005
```

### Persistance

Si execute dans un projet MTBC (`codes/mtbc/<projet>/`) :
- Ecrire le rapport dans `<projet>/resultats/qc_YYYY-MM-DD.md`
- En mode lot, ecrire aussi un TSV machine-readable :
  `<projet>/resultats/qc_YYYY-MM-DD.tsv`

---

## Integration avec l'ecosysteme

- **`/mtbc-lineages classify`** : utilise en interne pour le critere 1
  (chimere). La commande classify du skill mtbc-lineages fait le gros
  du travail.
- **`/species-id`** : si le taux GC est aberrant (FAIL critere 2),
  suggerer `/species-id` pour verifier que c'est bien du MTBC.
- **`/fetch-tbannotator`** : pour recuperer le report.json si absent.
- **`get_phylo.py`** : le skill reproduit et enrichit la logique de
  filtrage de `investigate_phylo/get_phylo.py` (fonctions
  `est_pollution()` et `get_stats()`). Les seuils sont identiques
  (GC 61-69%, couverture 95%, profondeur 15x).
- **`/phylo-history`** : une souche qui echoue au QC devrait etre
  verifiee dans son historique phylogenetique (placement instable
  = signal complementaire).

---

## Points de vigilance

1. **Les criteres 1 et 6 sont les plus importants** : un GC normal et
   une bonne couverture n'excluent ni une chimere intra-MTBC ni une
   contamination inter-especes. Toujours tester les deux.
2. **Critere 1 ne detecte pas la contamination inter-especes** : si
   un contaminant non-MTBC est present, il n'aura pas les marqueurs
   MTBC et le critere 1 passera en PASS. C'est le critere 6 qui le
   detectera via la signature des housekeeping.
3. **Mode degrade** : si seul le `spdi.txt` est disponible (pas de
   report.json), seuls les criteres 1 et 5 sont evaluables. Les
   criteres 2, 3, 4, 6, 7 necessitent le report.json. Le signaler
   clairement dans le rapport.
4. **Bug Rv0215c TBannotator v1** : dans les rapports v1, des SNPs
   genome-wide sont faussement etiquetes `gene-Rv0215c` avec
   `feature_type='gene_variant'` et `locus_tag=null`. Toujours les
   filtrer pour le critere 6, sinon faux FAIL.
5. **Lignees animales** : les seuils de SPDI sont differents pour les
   lignees animales (bovis, caprae, microti, orygis, chimpanze,
   dassie...). Utiliser les distributions mesurees du critere 5.
6. **Mixed infection vs chimere** : une mixed infection (deux souches
   MTBC dans le meme patient) peut ressembler a une chimere. Le QC
   ne distingue pas les deux — il signale le probleme, l'interpretation
   est humaine.
7. **Seuils** : les seuils par defaut correspondent a ceux de
   `get_phylo.py`. Le mode `--strict` durcit les seuils pour les
   etudes ou la qualite est critique (datation moleculaire, etc.).
8. **Cache report.json** : le report.json peut etre absent si la
   souche n'a pas encore ete annotee par TBannotator. Ne pas bloquer
   — evaluer ce qui est possible et signaler les criteres manquants.
9. **Ne pas supprimer** : le skill signale les souches problematiques
   mais ne les deplace pas. C'est `get_phylo.py` ou l'utilisateur
   qui decide de l'exclusion.
10. **Biais de reference H37Rv** : les lignees phylogenetiquement
    distantes de L4 (L1, L5, animales) peuvent avoir des SPDI
    deficitaires meme avec un bon sequencage, a cause du mapping
    sur H37Rv. Le critere 7 aide a distinguer "mauvaise qualite" vs
    "biais de reference".

---

## Cas de reference

Exemples reels d'investigations passees qui ont calibre les seuils
des criteres 5, 6 et 7. Ces cas sont documentes en detail dans
`investigate_phylo/cahier_de_labo.md` et `data-quality/cahier_de_labo.md`.

### Cas 1 — SRR28351342 (contamination inter-especes) — 2026-04-11

- **Contexte** : souche etiquetee L2.2.1, 2035 SPDI dans `bdd/a_ranger/`
- **Classifications** : Thawornwattana/Napier L2.2.1 (concordant), RD105
  absent (= L2 confirme), kit d'extraction Molzym Ultra-Deep Microbiome
  Prep (metagenomique)
- **Signature de contamination** :
  - rpoB : 41 SNPs (vs 2 typique L2)
  - rpoC : 47 SNPs
  - Top housekeeping : groEL2 38, dnaK 36, clpX 39, secA1 36
  - Ratio MNP : 24.7% (503/2035)
  - Depth HK/autre : 7.6x (352x dans HK vs 46x ailleurs)
- **Diagnostic** : MTBC L2 authentique contaminee par une bacterie
  environnementale (NTM probable). Les reads du contaminant mappent
  sur les genes conserves de H37Rv.
- **Action** : deplacee vers `bdd/ignore/`
- **Calibre** : seuils du critere 6 (rpoB+rpoC >10, MNP >15%, ratio >3)

### Cas 2 — ERR2513290 (paradoxe depth/mapping) — 2026-04-12

- **Contexte** : souche L1.2.1, 1917 SPDI, dans `bdd/ignore/`
- **Paradoxe** : depth excellent 185x MAIS 163 genes manquants
- **rpoB/rpoC** : 1 et 2 (normal, pas de contamination)
- **Ratio MNP** : 10.1% (normal)
- **Diagnostic** : probleme de mapping/assemblage, pas de sequencage.
  Possibles : grandes deletions, reads chimeriques, biais de reference
  H37Rv pour L1 (phylogenetiquement distante de L4).
- **Calibre** : seuil du critere 7 (>100 genes manquants = FAIL) et
  le "paradoxe depth/mapping" signale explicitement

### Cas 3 — ERR9786341 (faux positif par distance phylogenetique) — 2026-04-12

- **Contexte** : souche L4.9, 341 SPDI, exclue car longue branche
- **Analyse** : L4.9 a une distribution SPDI de 181-509 (mediane 347)
- **Diagnostic** : 341 est EXACTEMENT la mediane L4.9 — exclusion
  injustifiee. La longue branche est structurelle : L4.9 est
  phylogenetiquement distante de L4 sensu stricto.
- **Calibre** : critere 5 doit utiliser les distributions par lignee,
  pas un seuil generique

### Cas 4 — 25 souches « longues branches » — 2026-04-12

Investigation en lot de 25 souches exclues pour long branch :
- **0 contamination inter-especes** (Critere 6)
- **8 LOW_DEPTH** (Critere 4 FAIL)
- **7 MARGINAL** (Critere 5 WARN)
- **2 paradoxes depth/mapping** (Critere 7 FAIL avec depth OK)
- **1 VERY_LOW** (probable NTM, Critere 5 FAIL)
- **1 NORMAL** faux positif (ERR9786341)

**Lecon** : la majorite des longues branches ne sont pas des
contaminations mais des problemes de profondeur ou de mapping.
Le critere 6 ne doit etre invoque qu'en cas de signal specifique
(rpoB/rpoC eleves).

### Cas 5 — Campagne d'audit a_ranger (~1100 souches divergentes) — 2026-05-28/30

Tri systematique des souches divergentes (a_ranger + ignore + TBannotator
>=2700 SPDI). Resultat : **0 nouvelle espece** sur ~1100 souches. Tout s'est
resolu en : MTBC (range en lignees), *M. canettii* (109 promues), NTM
complexe kansasii/MTBAP (~90 -> hors_mtbc), lignees animales, constructions
de labo (Canettii STB-K = PRJNA662472), ou artefacts basse couverture.

**Pieges qui ont calibre le Critere 8** :
1. **Marqueur canettii_pct biaise** : 109 vraies Canettii (cov 96-98%) avaient
   canettii_pct=0 a cause de la polyphylie STB. Ne jamais s'y fier seul.
2. **Seuil nSPDI pour Canettii** : sans condition nSPDI>=8000, 203 MTBC
   normaux (nSPDI <2400) ont ete classes "canettii" a tort.
3. **2 fausses especes nouvelles evitees** : sp_novel (= M. kansasii, ANI
   99.8% vs ATCC 12478) et cluster3 (NTM MKC). Le garde-fou (marqueurs
   robustes + couverture + panel complet) a tranche.
4. **6 faux "candidats nouveaux"** demasques par la couverture (3.5-7.6% =
   NTM cross-mapping epars, pas une nouveaute).
5. **Format coverage_stats.tsv** (samtools) : couverture en colonne 5
   (`coverage`), profondeur en colonne 6 (`meandepth`).
6. **mp / TBannotator** : le pipeline ne produit PAS de `report.json` ; le
   livrable mappe est `snps.vcf` (+ `coverage_stats.tsv`).

**Lecon transverse** : pour une souche divergente, le triage fiable croise
%MNP + nSPDI + couverture + marqueurs robustes (kansasii 201) + match panel
hors_mtbc + SNP-barcoding. Aucun critere isole ne suffit.
