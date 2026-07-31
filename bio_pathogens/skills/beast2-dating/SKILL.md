---
name: beast2-dating
description: >-
  Academic research toolkit for Bayesian molecular dating of Mycobacterium tuberculosis
  complex (MTBC) phylogenies with BEAST2, for peer-reviewed phylogenomic research. Generates
  correct BEAST2 XML for BINARY SNP alignments (presence/absence 0/1), the format produced
  by the Guyeux group (FEMTO-ST) TB pipeline, and runs BEAST2 headless. Fixes the two
  failures that make BEAST2 runs on MTBC binary data silently fail to converge. Use when
  dating a node or a lineage with BEAST2, writing or debugging a BEAST2 XML, choosing a
  clock or tree prior for MTBC, or diagnosing an ESS that will not rise.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# beast2-dating : BEAST2 sur alignements SNP binaires MTBC

## Pourquoi ce skill existe

Les runs BEAST2 sur données MTBC de notre pipeline échouent presque toujours,
pour **deux raisons distinctes**, identifiées et corrigées ici :

1. **Modèle de substitution incorrect.** Nos alignements sont *binaires*
   (présence/absence de SNP, encodés `A/T` ou `0/1`). Appliquer un modèle
   nucléotidique **HKY** dessus est faux : HKY attend 4 bases, sur un alphabet
   à 2 états `kappa` s'effondre vers 0 et l'horloge devient **non
   identifiable** → `clockRate` ne converge jamais (ESS ≈ 6 même à 5 M
   d'itérations). Il faut un **GeneralSubstitutionModel 2-états** avec
   `dataType="binary"`.

2. **Namespace XML incomplet.** BEAST 2.7 résout les `spec="..."` courts via un
   `namespace='...'` déclaré en tête de fichier. S'il manque un package
   (`beast.base.inference.distribution`, `...substitutionmodel`, ...), le
   chargement échoue avec un message **trompeur** :
   `Could not find class beast.base.core.BEASTInterface as service ...`.
   Ce message fait croire à une installation cassée alors que le XML est en
   cause. Le patron ci-dessous embarque le namespace **complet et validé**.

> Diagnostic établi en comparant à un exemple **livré** avec BEAST
> (`examples/testTipDates.xml`) : celui-ci tourne, le nôtre échouait, donc ni
> le sandbox ni le paquet conda n'étaient en cause, uniquement le XML.

## Générer le XML

```bash
# à partir d'un XML BEAST2 existant (récupère séquences + dates)
python scripts/beast2_binary.py --in ancien_run.xml --out run.xml \
    --chain 20000000 --logevery 5000

# ou à partir d'un PHYLIP binaire + TSV de dates (taxon<TAB>année)
python scripts/beast2_binary.py --phylip aln.phy --dates dates.tsv --out run.xml \
    --chain 20000000
```

Le générateur : `dataType="binary"`, `GeneralSubstitutionModel` 2-états,
`StrictClockModel` estimé, coalescent `ConstantPopulation`, dates de
prélèvement (`date-forward`, aDNA comprises) préservées, arbre initial UPGMA.

## Correction d'ascertainment : INDISPENSABLE pour dater

Un alignement SNP-only ne contient **que des sites variables**. Sans correction,
BEAST considère que tout le génome varie aussi vite → les longueurs de branches
et donc le **taux d'horloge sont gonflés** (facteur ~300 mesuré sur MTBC), et le
TMRCA devient absurdement ancien.

```bash
python scripts/beast2_binary.py --in ancien_run.xml --out run.xml \
    --chain 20000000 --ascertainment --genome-len 4411532
```

`--genome-len` = taille du génome **appelable** (4 411 532 pb = H37Rv
NC_000962.3 ; réduire si des régions sont masquées). Le générateur ajoute un
`FilteredAlignment` avec `constantSiteWeights='n0 0'` où `n0 = genome_len − nSNP`
= nombre de sites constants à l'état de référence, réintégrés dans la
vraisemblance de Felsenstein.

**Effet vérifié** (jeu 36 taxa / 4303 SNP) :

| | sans correction | avec `--ascertainment` |
|---|---|---|
| clockRate (subst/site/an) | ~4.9×10⁻⁵ | **~1.5×10⁻⁷** |
| tree.height (ans) | ~30 000 | **~2 500** |

Le taux corrigé ~1.5×10⁻⁷ retombe dans la fourchette publiée pour MTBC (~1×10⁻⁷).
**Toujours utiliser `--ascertainment` pour une interprétation quantitative.**

## Prior d'horloge : le levier de convergence

Sur les SNP MTBC, `clockRate` et `tree.height` sont **faiblement identifiables
ensemble** (taux bas × arbre haut = même nombre de mutations). Résultat : même
après ascertainment + masquage, l'ESS reste ~5 et le taux dérive jusqu'à 1e-9.
**Ni le nettoyage des données ni les chaînes longues ne suffisent**, il faut
**ancrer** clockRate par un prior informatif.

Le générateur pose un prior LogNormal sur clockRate, paramétrable :

```bash
python scripts/beast2_binary.py --phylip aln.phy --dates dates.tsv --out run.xml \
    --ascertainment --genome-len 3683905 \
    --clock-prior 1e-7 --clock-prior-sd 1.25
```

- `--clock-prior` : **médiane** = M dans l'espace log (défaut `1e-7`, valeur
  génomique publiée pour MTBC). ⚠ sur alignement SNP-only *avec ascertainment*,
  le taux estimé est ~génomique ; sans ascertainment il serait par-site-variable
  (≫ 1e-7), caler le prior en cohérence avec `--ascertainment`.
- `--clock-prior-sd` : **largeur** en log (défaut `1.25` ; IC95% ≈ [9e-9, 1.2e-6]).
  L'historique `2.0` couvre ~3 ordres de grandeur = trop large, laisse la chaîne
  errer. Resserrer si le taux dérive.

Prouvé par comparaison brut/propre/prior (36 taxa, 5 M) : le masquage seul ne
bouge pas l'ESS (4.7→5.6) ; c'est le prior resserré qui contraint le taux à
l'échelle littérature et fait remonter l'ESS. Toujours vérifier `loganalyser`
après coup.

## Lancer BEAST2 (headless, sans GPU)

BEAST2 s'installe par conda (`conda install -c bioconda beast2`). Deux
contraintes en environnement headless / sans GPU :

- **`-java`** : force le calcul en Java pur, sans BEAGLE. Indispensable sans
  GPU (sinon `OpenCL error ... GPUInterfaceOpenCL`).
- **`HOME` inscriptible** : BEAST écrit `beauti.properties` sous `$HOME`. Si le
  HOME par défaut est en lecture seule, pointer `HOME` vers un dossier
  inscriptible.

```bash
export HOME="$PWD/beasthome"; mkdir -p "$HOME"
beast -java -overwrite -seed 42 run.xml
```

Sortie attendue (l'échantillonnage démarre) :

```
        Sample      posterior      clockRate    tree.height
          2000    -31324.1104 1.285989286E-5     34955.1060
          4000    -30927.0494 1.258553878E-5     34954.4646
   ...
Writing file run.log
Writing file run.trees
```

## Post-traitement

```bash
loganalyser run.log            # ESS par paramètre (viser ESS > 200)
treeannotator -burnin 10 run.trees mcc.tree   # arbre consensus MCC
```

TMRCA (année) ≈ date_la_plus_récente − `tree.height` moyen (après burn-in).

## Codage des données : pièges EN AMONT (plus critiques que le XML)

Un run BEAST2 qui *tourne* n'est pas un run *juste*. Les erreurs suivantes sont
dans la **génération de l'alignement**, pas dans le XML, et sont la cause la
plus fréquente d'une horloge non convergente (clockRate qui dérive, ESS ~5).
Diagnostic rapide : un alignement MTBC binaire réaliste **doit** contenir des
cellules manquantes (`?`/`-`). S'il en a **zéro**, c'est un signal d'alarme (voir
RD ci-dessous).

### 1. RD (Regions of Difference) → SNP couverts marqués absents (LE piège n°1)

Une RD est une **délétion**. Chez une souche qui la porte, la région n'existe
pas : les SNP qu'elle couvre sont **non-appelables = `?`**, jamais `0`. Les coder
`0` (état de référence) :
- **double-compte** un événement unique (la colonne booléenne RD *plus* tous les
  SNP couverts basculés à 0) → N+1 changements corrélés pour 1 seul événement ;
- **viole l'indépendance des sites** (hypothèse CTMC) et **gonfle la branche** du
  clade porteur ;
- **distord le taux d'horloge et le TMRCA** → cause directe de non-convergence.

**Correction** : par souche, mettre à `?` les positions SNP tombant dans ses
délétions RD. `dataType="binary"` gère nativement `?`/`-` comme données
manquantes, il suffit de ne pas fournir de faux-0 en amont. Correction dans
`bdd_query.py` / `get_phylo.py`, PAS dans le XML.

### 2. Masquer PE/PPE + répétitions + éléments mobiles

Les PE/PPE (~10 % du génome, GC-riches, répétés) produisent des SNP
homoplasiques par erreurs de mapping (standard MTBC depuis Comas et al.).
Exclure PE/PPE + `repeat_region` + `mobile_element`. Un jeu SNP *synonymes*
(`_syn`) réduit la sélection mais **n'est pas** un masque PE/PPE (les deux filtres
sont complémentaires). **Cohérence ascertainment** : si l'on masque, réduire
`--genome-len` d'autant (génome *appelable* = 4 411 532 − bases masquées),
sinon le poids des sites constants est faux.

### 3. Référence de mapping (H37Rv) vs état ancestral (canettii / MTBC0)

Le modèle binaire est **réversible** : relabeliser 0↔1 ne change ni la
vraisemblance ni les longueurs de branches → le choix de polarité ne biaise
**pas** le taux en soi. MAIS un SNP = « position où une souche diffère de
H37Rv » ⇒ **H37Rv est 0 partout** = taxon tout-à-zéro ⇒ il s'attache
artificiellement près de la racine (faux « ancestral »). Garder H37Rv comme
**référence de mapping** (commode, sans biais sur le taux) mais **enraciner /
polariser sur un vrai extérieur** : *M. canettii* (outgroup MTBC) ou l'ancêtre
reconstruit **MTBC0**.

### 4. Fréquences d'équilibre

Elles sont estimées sur les données : tant que les faux-0 de (1) y sont, π₀ est
surestimé. Poser masque (2) et données manquantes (1) **avant** l'estimation des
fréquences.

> **Ordre de rentabilité** : (1) RD→`?` ≫ (2) masque PE/PPE > (3) enracinement
> externe. Les trois sont en amont ; le XML binaire + ascertainment de ce skill
> ne corrige que la moitié modèle du problème.

## Validé sur

Jeu réel du pipeline : **36 taxa, 4303 SNP binaires**, dates 1154–2020
(8 échantillons aDNA). Trois enseignements successifs :

1. **Le XML tourne** (binaire + namespace complet + `-java`), `clockRate`
   **bouge**, contrairement au HKY cassé où il restait figé (ESS~6 même à 5 M).
2. **L'ascertainment est indispensable** : sans lui clockRate ~4.9e-5 /
   TMRCA absurde ; avec (`--genome-len 4411532`) le taux retombe à l'échelle
   MTBC (~1.5e-7 en run court). Facteur ~300.
3. **La convergence reste le vrai obstacle** : à 5 M, taux et hauteur d'arbre
   dérivent encore (ESS~5), signal temporel faible : MAIS ce jeu contient
   **0 cellule manquante**, symptôme du piège RD→0 (section « Codage des
   données » §1). Corriger le codage EN AMONT avant d'accuser le modèle.

## Fidélité vs pipeline de publication

Ce skill vise un run BEAST2 **qui aboutit** pour l'exploration et le débogage.
Pour un arbre daté de publication, se caler sur la config BEAST2 canonique du
groupe (priors, modèle démographique, longueur de chaîne), ce générateur
utilise un coalescent à taille constante et une horloge stricte par défaut ;
adapter `--chain` (≥ 20 M pour l'ESS) et, si besoin, éditer le modèle
démographique / d'horloge dans le XML produit.

## Notes

- `--ascertainment --genome-len N` : correction du biais SNP (voir section
  dédiée ci-dessus), réintègre les sites constants via `FilteredAlignment`.
- Sites conservés : le générateur garde tous les sites fournis. Filtrer en
  amont si l'on veut restreindre aux positions informatives.
- Complément : le skill `molecular-clock` porte la connaissance épistémique
  (régimes de TMRCA MTBC, TDRP, calibration) qui aide à juger si le
  `clockRate`/TMRCA obtenu est plausible.
