---

name: gwas-clonal-lineage
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST) for testing whether a
  variant, gene or locus is genuinely associated with a clinical trait (drug
  resistance, tissue tropism, disease form) in a bacterial GWAS on a CLONAL
  population such as the MTBC — where lineage is the dominant confounder and a
  naive association almost always recovers lineage instead of phenotype.
  Packages a pipeline reforged independently 4 times in this repo into one
  module: lineage-stratified Cochran-Mantel-Haenszel (CMH) at cohort level (is
  lineage itself associated?) and locus level (does the variant stay
  associated once lineage is controlled?), a Breslow-Day heterogeneity test
  flagging a pooled odds ratio hiding opposite effects between strata, a
  paucibacillarity/dropout filter, a mappability/paralogy BLAST check, and a
  tree-free homoplasy probe. Use whenever a GWAS hit or a top-N genes table
  needs checking before a manuscript — never trust a GWAS hit on a clonal
  pathogen without the lineage-stratified locus-level CMH first.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# GWAS sur bactérie clonale — pipeline stratifié par lignée

Une bactérie clonale comme *M. tuberculosis* ne recombine (quasiment) pas : toute association
naïve entre un variant et un phénotype (résistance, forme clinique, tropisme) risque de
capturer la **structure de lignée** plutôt que la biologie du variant, parce qu'un variant
ancien porté par toute une lignée cosegrège avec n'importe quel trait sur-représenté dans
cette même lignée. C'est le piège documenté et reretrouvé indépendamment sur au moins quatre
projets de ce dépôt (résistance CRyPTIC, tropisme méningé Cambau/Bridier-Nahmias, cohorte
OUCRU Vietnam TBM) : **contrôler la lignée n'est pas optionnel, c'est la première chose à
faire**, pas une vérification a posteriori.

## Les six étapes canoniques

Chaque étape répond à une question DIFFÉRENTE des autres — ne jamais sauter une étape en
pensant qu'une étape voisine l'a déjà couverte.

### 1. CMH stratifié par lignée — à DEUX niveaux, jamais confondus

Deux questions distinctes, à ne jamais confondre (piège vécu, cf. `references/methodology.md`
§1) :

- **Niveau COHORTE** : la lignée elle-même est-elle associée au phénotype dans cette
  cohorte ? (répond à « y a-t-il un confondant de structure de population en général »,
  sans référence à un locus précis)
- **Niveau LOCUS** : le portage de CE variant précis reste-t-il associé au phénotype une
  fois la lignée retirée du signal ? (le vrai test GWAS pour un candidat)

Un CMH cohorte-niveau non significatif **ne prouve rien** sur un locus précis — le test
locus-niveau peut très bien rester significatif (observé sur Rv1125 : cohorte-niveau
p=0,05-0,36, mais 2/3 SNP restent p<1e-7 au niveau locus). Toujours refaire le test au
niveau dont la question a besoin.

Utiliser `scripts/stratified_cmh.py` : `cmh(tables)` prend une liste de tables 2×2 (une par
strate de lignée) et rend un `CMHResult` (statistique CMH, p-value, OR poolé Mantel-Haenszel,
IC95%, test de Breslow-Day). `build_strata_tables()` construit ces tables depuis des comptages
`{lignée: (a, b, c, d)}` et **exclut automatiquement** toute strate à marge nulle (la variance
de Mantel-Haenszel diverge sinon) — toujours reporter les strates exclues dans le résultat
final, un reviewer demandera pourquoi.

Deux implémentations, même interface : `cmh_statsmodels()` (par défaut, exacte, déjà
validée croisée sur 3 projets) et `cmh_pure_python()` (repli sans dépendance, formule
Mantel-Haenszel avec correction de continuité + `math.erfc` pour le chi² exact — pas de
Breslow-Day ni d'IC, à n'utiliser que si `statsmodels` est réellement indisponible, par
exemple un paquet SLURM portable). L'entrée `cmh()` bascule automatiquement entre les deux.

**Le test de Breslow-Day n'est pas optionnel non plus** : un OR poolé significatif peut
masquer des effets de sens OPPOSÉ selon la strate (observé sur `SNP_1248382` de Rv1125 :
sens opposé en lineage1 et lineage2, Breslow-Day p=0,0025) — dans ce cas l'OR poolé n'est
pas une lecture sûre du signal, quelle que soit sa significativité globale.

### 2. Filtre direction / paucibacillarité

Sur des cohortes de charge bacillaire différentielle (ex. méningé = paucibacillaire vs
pulmonaire), un site à faible couverture perd des appels SNP (« absence = non-appelé »,
pas « absence = référence »). Cela ne fabrique QUE de fausses PERTES (variant absent dans
le bras à faible biomasse), jamais de faux GAINS. Règle : **ne garder que les variants
enrichis (OR>1) dans le bras d'intérêt**, jeter systématiquement la direction perte tant
que l'origine du dropout n'est pas positivement écartée. Détail et chiffres réels (5-9 %
de SNP en moins en méningé, concentré sur les PE_PGRS GC-riches) : `references/
methodology.md` §2.

### 3. Confirmation phylo-aware (homoplasie) — sans reconstruire d'arbre

Un variant apparu UNE fois dans un sous-clade qui a ensuite proliféré et se trouve
sur-représenté dans le phénotype d'intérêt produit exactement le même signal CMH qu'un
variant réellement causal apparu indépendamment plusieurs fois (convergence). Le test
tree-free : re-calculer le MÊME CMH stratifié à profondeur de préfixe CROISSANTE
(`L4` → `L4.3` → `L4.3.4` → `L4.3.4.2`, cf. convention dir-mixte de la BDD). Un variant
synapomorphique d'un sous-clade devient monomorphe (donc non-informatif) dans sa strate
dès que la profondeur dépasse le nœud où il est apparu — son signal s'annule. Un variant
convergent reste polymorphe et son signal survit.

`scripts/homoplasy_scan.py` : `homoplasy_report(strains, carrier_ids)` rend le résultat CMH
à chaque profondeur testée, plus deux indices descriptifs parmi les porteurs
phénotype-positifs (nombre de sous-lignées distinctes, indice de clonalité = fraction dans
le plus gros sous-clade). Un vrai arbre déjà disponible pour le projet ? Préférer les skills
`convergent-evolution` ou `pastml`, qui testent l'homoplasie directement dessus — ce module
est le repli quand seuls les codes de clade textuels sont disponibles, pas un substitut.

### 4. Réplication inter-cohorte

Un signal qui réplique dans une seconde cohorte indépendante (pays, BioProject différents)
est plus solide qu'un signal isolé — MAIS voir l'avertissement critique de l'étape 5 avant
de le lire comme une confirmation : la réplication ne disculpe PAS un artefact de mappabilité
qui reproduit systématiquement, précisément parce qu'il est systématique.

### 5. Mappabilité / paralogie — le filtre qui a tout tué une fois

**Ne jamais sauter cette étape**, même — surtout — sur un signal répliqué. Cas vécu et
chiffré : 10/10 candidats GAIN répliqués sur deux cohortes indépendantes (Vietnam +
Thaïlande) se sont révélés être en région paralogue (famille esx, opéron pps, duplication
tandem lpp) — la réplication répliquait l'artefact de cross-mapping du génome de référence,
pas la biologie. Les familles qui reviennent systématiquement dans les GWAS MTBC short-read
(PE/PPE, esx, pks/pps, lpp, éléments IS, **répétitifs REP et bordures de prophage**) sont le
~10 % du génome non uniquement mappable à la longueur de lecture Illumina — tout signal qui s'y concentre est le suspect n°1, pas un
signal renforcé par sa récurrence.

`scripts/mappability_filter.py` : `check_mappability(genome_fasta, candidates)` extrait une
fenêtre de lecture (défaut 101 pb) centrée sur chaque position candidate, BLAST contre le
génome de référence, et classe `PARALOG-RISK` tout site avec un hit secondaire à identité
≥80 % sur ≥50 pb ailleurs dans le génome (seuils ajustables). Nécessite `blastn` et
`makeblastdb` (NCBI BLAST+) sur le PATH.

**Piège de référentiel de coordonnées avant tout BLAST/overlap.** Cas vécu (`mtbc/Rv1125`,
P1.3.j, 2026-09-01) : la coordonnée locus recopiée depuis une fiche `annotation_mtbc`
(champ `start_mtbc0`/`end_mtbc0`) est le référentiel pangénomique MTBC0 (Harrison et al.
2024), pas une coordonnée H37Rv/NC_000962.3 — les deux ne coïncident PAS systématiquement
gène par gène (coïncidence vérifiée pour un gène voisin, divergence de plusieurs kb pour un
autre). Une coordonnée MTBC0 utilisée par erreur comme coordonnée H37Rv peut déplacer le
site candidat hors de sa vraie fenêtre et fausser silencieusement le test de chevauchement
avec le masque de non-mappabilité ou la fenêtre BLAST. Avant tout appel à
`check_mappability` ou à un masque de non-mappabilité, vérifier la coordonnée candidate
contre le GFF3 RefSeq H37Rv local (ou les locus voisins attendus dans `genomic_context`),
jamais contre le seul champ de la fiche atlas.

### 6. Polarité — l'allèle « variant » est-il l'état DÉRIVÉ, ou l'état ancestral du complexe ?

Ajoutée le 2026-09-10, sur mesure. Toute la chaîne SPDI est mappée sur H37Rv, qui est une
souche **L4.9**. Partout où H37Rv porte l'état dérivé vis-à-vis de l'ancêtre du complexe,
c'est la quasi-totalité du MTBC qui apparaît « mutée », et le contraste entre deux groupes
ne mesure alors que leur composition en lignées. Cas vécu : le rang 3 d'un GWAS TBM était un
variant synonyme porté par 98,20 % de 142 675 souches et par 147/149 *M. canettii*, l'état
dérivé privé étant celui de H37Rv (`mtbc/Rv2566` P2.12).

**L'asset** : `mtbc/mixed_infections_multimarker/résultats/pilote_cram/l4path_pos.tsv`, les
1 311 positions de la branche L4 de Malaga et al. 2024 (*Microb Genom*, PMID 38175684),
c'est-à-dire les positions où H37Rv diffère de l'ancêtre MTBC0. Densité de fond 0,297/kb,
une position toutes les 3 365 pb.

**Deux usages, à ne pas confondre.** Par CANDIDAT : la position est-elle dans la liste ? Si
oui, le « variant » est l'allèle ancestral et le signal est du biais de référence, point.
Par JEU de candidats : le classement entier est-il enrichi en positions L4-path ? Un
enrichissement dit que le classement est structuré par la composition en lignées des bras,
même quand aucun hit pris isolément n'est dans la liste. Mesuré à 5,13 fois sur un top-28
réel (p_perm 3,5e-4), et l'effet survivait au retrait des PE/PPE (3,73) et des pps/pks (4,54).

**Le nul, et c'est là que ça se joue** : ne PAS tirer des fenêtres génomiques aléatoires. Les
gènes ne sont pas des fenêtres, et les gènes LONGS de MTBC sont les PE_PGRS et les pks,
eux-mêmes riches en positions L4-path. Tirer des **gènes réels appariés en longueur** depuis le
GFF3 (`mtbc/investigate_phylo/resources/NC_000962.3.gff3`, 3 978 gènes). Passer d'un nul à
l'autre a déplacé une p-value de 4e-4 à 0,041 sur un sous-ensemble.

**Limite à énoncer telle quelle** : le test par jeu mesure la présence de positions L4-path
DANS le gène, pas que le SNP porteur du signal EST une position L4-path. Propriété du jeu,
pas cause de chaque hit ; trancher exige les positions exactes des variants.

Implémentation de référence, à recopier plutôt qu'à réécrire :
`mtbc/anrs_camille_allam/analyses/l4path_test.py` (test + Poisson + permutation par fenêtres),
`l4path_ctrl.py` (sous-ensembles PE/PPE, pps/pks), `l4path_genenull.py` (nul par gènes réels),
`fetch_genes.py` (coordonnées via l'API REST TB-annotator).

**Réserve de complétude** : ces 1 311 positions couvrent la branche L4 seulement. Un biais de
référence existe aussi pour les branches plus profondes ; l'asset le lève partiellement, jamais
totalement.

## Pipeline recommandé, dans l'ordre

```
1. lignée × phénotype (cohorte)  -->  confondant de structure en général ?
2. portage-du-variant × phénotype, stratifié lignée (locus)  -->  le vrai test GWAS
3. filtre direction (garder OR>1 dans le bras d'intérêt seulement)
4. homoplasie (profondeur croissante)  -->  convergent ou marqueur de sous-clade ?
5. réplication inter-cohorte, SI disponible
6. mappabilité/paralogie  -->  jamais sauté, même sur un signal répliqué
7. polarité vs l'ancêtre du complexe  -->  le « variant » est-il l'allèle ancestral ?
```

Le pas 7 se fait aussi en AMONT, sur le jeu entier : un classement enrichi en positions
L4-path est structuré par la composition en lignées des bras avant même qu'on regarde un
candidat, et cela se mesure en quelques secondes. Le faire tôt évite d'instruire un à un des
hits qu'une seule mesure globale disqualifie.

Un résultat n'est publiable comme déterminant robuste que s'il survit aux SEPT contrôles. Un
résultat qui meurt à l'étape 1 ou 2 (structure de lignée explique tout) est déjà informatif
en négatif — ne pas continuer les étapes suivantes dessus, l'écrire tel quel.

## Garde-fous supplémentaires et cas vécus

`references/methodology.md` détaille, avec chiffres et sources : le piège cohorte-vs-locus
(§1), la mécanique du dropout paucibacillaire (§2), le résultat mappabilité qui a renversé
la lecture d'un « beau signal convergent » (§3), et les seuils/paramètres par défaut utilisés
dans chaque script avec leur justification. Le lire avant d'adapter un seuil.

## Validation

`scripts/smoke_test.py` reproduit EXACTEMENT (chi², p-value, OR poolé, Breslow-Day) les
résultats déjà publiés dans `mtbc/Rv1125/résultats/phase1_p1_3_i_cmh_snp_lignee/rapport.md`
(cahier 2026-08-30) à partir du module consolidé, plus un test synthétique du filtre de
mappabilité. Le lancer après toute modification de `stratified_cmh.py` ou
`mappability_filter.py` : `python scripts/smoke_test.py`.

## Ce que ce skill NE fait PAS

- Ne remplace pas une vraie GWAS pangénomique (pyseer, treeWAS, DBGWAS) — c'est l'outil pour
  auditer/confirmer un candidat déjà identifié, cohorte-restreint ou gène-par-gène, pas pour
  scanner un génome entier depuis zéro.
- Ne construit pas d'arbre phylogénétique ; l'étape homoplasie est un repli tree-free, pas un
  substitut à `convergent-evolution`/`pastml` quand un arbre existe déjà.
- Ne teste pas l'ascertainment bias du filtre d'exclusivité de marqueurs de lignée (variants
  core-exclusifs) — c'est le rôle du skill `mk-ascertainment`, orthogonal à celui-ci.
