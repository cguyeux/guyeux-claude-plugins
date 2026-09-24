# Méthodologie détaillée — GWAS sur bactérie clonale

Chiffres, sources et justification des seuils par défaut des scripts. À lire avant d'ajuster
un paramètre, pas en lecture systématique.

## §1. Cohorte-niveau vs locus-niveau : deux questions, pas une

**Cas source** : `mtbc/Rv1125`, GWAS candidat rang #13/1352 (Cambau/Bridier-Nahmias, tropisme
méningé vs pulmonaire), cahier 2026-08-30.

Un premier test transféré depuis un projet voisin (`mtbc/Rv2566`) — CMH lignée × TBM au
niveau de la COHORTE ENTIÈRE, sur les 3 paires lineage1/2/4 — était non significatif partout
(p=0,05 à 0,36). Lecture erronée possible : « la structure de lignée explique probablement le
hit GWAS de Rv1125 ». Un second test, plus fin — CMH porteur/non-porteur DU SNP LUI-MÊME ×
TBM/PTB, stratifié par lignée (mêmes fichiers sources, même patron de code, seule la variable
comparée change) — a montré que 2 des 3 SNP restent **fortement significatifs et homogènes**
après ce contrôle (p=3,3e-8 et p=1,6e-10, Breslow-Day non significatif).

**Pourquoi les deux tests peuvent diverger** : le premier dit si la lignée EN GÉNÉRAL est
associée au phénotype dans cette cohorte ; le second dit si UN LOCUS PRÉCIS reste associé une
fois la lignée retirée du signal. Le premier n'implique NI ne réfute le second, ni logiquement
ni empiriquement. Un locus peut porter un signal réel même dans une cohorte où la lignée
elle-même n'est pas confondante ; à l'inverse, une cohorte où la lignée EST confondante
n'implique pas que chaque locus individuel en hérite automatiquement (dépend de la
distribution du variant entre lignées).

**Angle mort générique de la méthode, même au niveau locus** : le CMH stratifié par lignée
ne contrôle QUE la variable de stratification choisie. Une sous-structure plus fine
(sous-clade, BioProject/site de recrutement) non présente dans les données de synthèse
reste un confondant possible non exclu — un CMH significatif après stratification par lignée
écarte l'explication « lignée grossière », pas toute explication de structure de population
plus fine. Voir §3 pour le repli tree-free qui adresse spécifiquement ce point via la
profondeur de préfixe de clade.

## §2. Direction et dropout paucibacillaire

**Cas source** : `mtbc/tissue_tropism_mtbc`, cohorte PRJNA1028637 (Vietnam/OUCRU, 830 souches,
méningé vs pulmonaire).

Sur des sites paucibacillaires (charge bacillaire faible, ex. liquide céphalorachidien), le
pipeline d'appel de variants confond structurellement deux états : « absence = référence » et
« absence = NON APPELÉ » (couverture insuffisante pour trancher). Mesuré : 5-9 % de SNP
appelés en moins dans le bras méningé que dans le bras pulmonaire (médianes vérifiées par
lignée), décrochage concentré sur les régions PE_PGRS riches en GC (couverture Illumina
intrinsèquement plus faible sur ces régions, indépendamment du phénotype).

**Conséquence directionnelle** : ce mécanisme ne peut fabriquer que de fausses PERTES —
un variant réellement présent qui n'est pas appelé faute de couverture se lit comme
« absent », jamais l'inverse (un dropout ne peut pas faire APPARAÎTRE un variant absent).
Donc toute direction PERTE (variant appauvri dans le bras à faible biomasse) est
structurellement suspecte de dropout et doit être écartée par défaut, tandis qu'une direction
GAIN (variant enrichi dans le bras à faible biomasse) ne peut PAS s'expliquer par ce mécanisme
— c'est le sous-ensemble à garder pour la suite du pipeline (homoplasie, réplication,
mappabilité).

Sur la cohorte source : 210/254 hits significatifs après CMH étaient en direction PERTE
(écartés comme probable artefact de dropout), 32 hits GAIN hors gènes de résistance/PE-PPE
restaient à instruire par les étapes suivantes — dont la totalité s'est révélée en région
paralogue à l'étape mappabilité (§3).

## §3. Mappabilité/paralogie — le résultat qui a renversé une lecture positive

**Cas source** : `mtbc/tissue_tropism_mtbc`, candidats GAIN répliqués Vietnam + Thaïlande.

Après CMH stratifié (§1), filtre direction (§2) et réplication dans une seconde cohorte
indépendante, un jeu de gènes cohérent biologiquement (ESX-5 : `esxV`/`esxO` ; PDIM-PGL :
`ppsA` ; lipoprotéines : `lppA`/`lppB`) semblait constituer un signal convergent solide —
répliqué dans deux cohortes indépendantes, cohérent fonctionnellement, direction GAIN propre.

Le test de mappabilité (fenêtre de 100 pb centrée sur chaque SNP, BLAST contre H37Rv) a
montré que **10/10 des candidats GAIN répliqués** sont en région paralogue : `esxV` a un
paralogue **100 % identique sur 101 pb** (la famille esx compte ≥5 copies quasi-identiques,
ESX-5 en particulier) ; `ppsA` est dans un opéron tandem à 99 % d'identité ; `lppA`/`lppB`
sont une duplication tandem à 95 % ; les sites intergéniques candidats sont dans des régions
répétées/IS à 100 %.

**Leçon centrale, contre-intuitive** : la réplication inter-cohorte NE DISCULPE PAS un
artefact dont la cause est la paralogie du génome de référence combinée au pipeline de
calling — au contraire, elle réplique PARCE QUE l'artefact est systématique (même génome de
référence, même pipeline, dans les deux cohortes). Les familles de gènes qui reviennent
invariablement dans les GWAS MTBC en lectures courtes (PE/PPE, esx, pks/pps, lpp, éléments
IS) constituent le ~10 % du génome non uniquement mappable à la longueur de lecture Illumina
standard — tout signal qui s'y concentre est le suspect n°1 d'artefact de cross-mapping,
justement PARCE qu'il est récurrent d'une étude à l'autre (trois études indépendantes du
tropisme méningé — thèse La 2023, Faksri 2018, Ruesen 2018 — retombent toutes sur des
PE/PPE/pks, signal probablement partagé pour la même raison structurelle plutôt que par
coïncidence biologique).

**Résultat de fond, honnête et publiable en négatif** : sur la question spécifique du
tropisme méningé bactérien, aucun déterminant nucléotidique robuste ET mappable n'a été
identifié dans les WGS publics une fois les six étapes de ce pipeline appliquées jusqu'au
bout. Un résultat qui meurt à l'étape mappabilité n'est pas un échec de méthode — c'est le
pipeline qui fait son travail.

## §4. Seuils par défaut des scripts et leur justification

- `mappability_filter.py` : fenêtre de lecture 101 pb (`half_window=50`, taille read
  Illumina standard) ; seuil PARALOG-RISK à identité ≥80 % sur ≥50 pb (permet de détecter des
  paralogues divergents, pas seulement des duplications exactes — un seuil plus strict comme
  ≥95 % raterait des familles comme `lppA`/`lppB` à 95 % pile à la limite). Pour caractériser
  la paralogie d'un GÈNE ENTIER plutôt qu'une seule position, élargir la fenêtre à la longueur
  du gène et baisser le seuil de longueur minimale en proportion.
- `stratified_cmh.py` / `build_strata_tables()` : `min_informative=2` strates — en dessous,
  la variance de Mantel-Haenszel n'est pas interprétable de façon fiable (observé sur Rv1125 :
  2/3 lignées informatives suffit, mais publier un CMH à une seule strate reviendrait à publier
  un simple test du chi² sur cette strate en le faisant passer pour un test stratifié).
- `homoplasy_scan.py` : profondeurs testées par défaut `(1, 2, 3, 4)` — calées sur la
  granularité typique des codes de clade `bdd/actuelle` (lignée majeure → sous-lignée →
  sous-clade → très fin). Ajuster selon la profondeur réelle de nommage du projet.
