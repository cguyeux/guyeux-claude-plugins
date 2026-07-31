# Catalogue des notions a expliciter pedagogiquement -- version integrale

Reference de `mtbc-bilan` : texte integral de la Phase 4.6. Passer en revue les
six categories A-F et retenir les concepts effectivement presents dans le projet.

### 4.6 Identification des notions a expliciter pedagogiquement

Le bilan est destine en premier lieu a **Christophe Guyeux**, dont la
formation est mathematiques pures + informatique de base. Tout ce qui
releve de la biologie evolutive, de la genetique des populations, de
l'ethno-linguistique, de l'epidemiologie des maladies infectieuses, ou
des statistiques inferentielles avancees est **a priori opaque** pour ce
profil et doit etre explicite.

**Principe directeur** : mieux vaut un encadre superflu qu'une notion
laissee dans l'ombre. Avoir la main lourde sur les explications --
l'objectif est qu'a la lecture du bilan, le specialiste de math
pures puisse expliquer a un collegue ce que sont les Bantu, ce qu'est
un test de Mantel partiel, et pourquoi c'est utilise ici.

**Avant de commencer la redaction (Phase 9)**, dresser une liste des
notions presentes dans le projet qui meritent un encadre pedagogique.
Categories typiques a passer en revue :

#### A. Anthropologie, ethno-linguistique, geographie historique
Concepts a expliciter quand ils apparaissent dans le projet (frequents
sur les lignees L5, L6, L9, L10 et tout projet a dimension
phylogeographique africaine, asiatique ou amerindienne) :
- Familles linguistiques (Bantu, Kwa, Niger-Congo, Afro-asiatiques,
  Nilo-sahariennes, Khoisan, Austronesien, Sino-tibetain...)
- Migrations historiques (expansion bantoue, peuplement du Sahel,
  routes de la soie, traites negrieres et leurs consequences
  demographiques)
- Groupes ethniques cles cites dans l'article (Yoruba, Akan, Mossi,
  Zoulou, Massai, Hutu/Tutsi, Pygmees, San, Ewondo...)
- Ecotypes et co-evolution hote-pathogene (notion d'animal-adapted
  vs human-adapted MTBC, ecotypes M. bovis / M. caprae / M. mungi /
  M. orygis...)
- Geographie sanitaire et historique coloniale (anciennes colonies,
  decoupages administratifs hérites qui structurent encore les bases
  de donnees)

Pour chacun de ces concepts presents dans le projet, expliquer dans un
encadre **Notion** :
1. De quoi il s'agit (en 2-4 phrases)
2. Pourquoi c'est pertinent pour le projet (genetique des populations
   humaines coevoluant avec MTBC, pression demographique, brassage)
3. Quels groupes/regions sont concernes
4. Une reference de vulgarisation ou un article de reference si
   disponible

#### B. Biologie et genetique des populations
Concepts qui semblent triviaux a un biologiste mais ne le sont pas
pour un mathematicien :
- Goulot d'etranglement, effet fondateur, derive genetique
- Isolat, deme, structure de population (Fst, Wright)
- Coalescent, ancestral state reconstruction
- Selection (positive, purifiante, balancee, frequence-dependante)
- Equilibre de Hardy-Weinberg, deviation et ses causes
- Recombinaison vs mutation, mutation rate, taux de substitution
- Marqueurs neutres vs sous selection
- Linkage disequilibrium, hitchhiking
- Notion d'haplotype, haplogroupe
- Notions d'epidemiologie : R0, transmission cluster, source case,
  super-spreader, latence, reactivation
- Specificites MTBC : clonalite (pas de recombinaison horizontale
  significative), absence de plasmide majeur, lent taux de mutation

#### C. Phylogenetique et evolution moleculaire
Methodes phylogenetiques avancees a expliciter :
- Maximum de vraisemblance (ML) vs maximum de parcimonie vs
  inference bayesienne
- Modeles de substitution (JC69, HKY, GTR, GTR+G+I, partitionnement)
- Bootstrap et support : que mesure-t-il vraiment ?
- Datation moleculaire : horloge stricte vs relachee, calibration
  par fossiles ou par dates de prelevement (tip-dating)
- Notion d'outgroup et de polarisation
- Ancestral state reconstruction (parsimony, ML, stochastic mapping)
- Coalescent et skyline plots (BEAST, LSD2)
- Tree skewness, balance index, branche longue
- Notions de monophylie, paraphylie, polyphylie
- Specificites SNP-based phylogeny chez MTBC (faible diversite,
  ascertainment bias, biais de reference H37Rv)

#### D. Statistiques inferentielles utilisees en biologie
A expliciter systematiquement -- ces tests ne font partie d'aucun
cursus standard de math pures ou d'informatique :
- Test de Mantel (simple), test de Mantel partiel : qu'est-ce que
  ca compare, quelle est la statistique, pourquoi des permutations,
  quand est-ce justifie ?
- Tests non-parametriques (Wilcoxon, Mann-Whitney, Kruskal-Wallis) :
  quand les preferer aux tests parametriques
- Correction multiple (Bonferroni, FDR de Benjamini-Hochberg) :
  pourquoi corriger, qu'est-ce que controle chaque methode
- Tests d'enrichissement (hypergeometrique, GO enrichment, gene
  set enrichment analysis)
- Tests de neutralite (Tajima's D, Fu-Li, McDonald-Kreitman, dN/dS)
- ABC (Approximate Bayesian Computation), MCMC dans le contexte
  phylogenetique
- Bootstrap parametrique vs non-parametrique
- p-values, intervalles de confiance, taille d'effet : la difference
- Tests de robustesse, analyses de sensibilite

#### E. Outils et formats specifiques au domaine
Les acronymes et formats qui sont du folklore pour un bioinformaticien
mais opaques sinon :
- VCF, BAM, FASTA, FASTQ, GFF3, GenBank
- SPDI, HGVS pour la nomenclature des variants
- Spoligotyping, MIRU-VNTR, RFLP
- WGS, WES, ddRADseq, amplicon sequencing
- BWA, GATK, samtools, bcftools, snippy, BLAST
- RAxML, IQ-TREE, BEAST, MrBayes, PhyML
- Outils MTBC-specifiques (TBProfiler, MTBseq, Mykrobe, TBannotator)

#### F. Concepts MTBC et tuberculose
Memes les chercheurs MTBC repertorient ces notions, donc a fortiori
un mathematicien :
- Definition des lignees (L1-L10) et leur biogeographie
- Animal-adapted vs human-adapted ecotypes
- Notion de "modern" vs "ancient" lineages (L2/L4 vs L5/L6/L7)
- Pathogenie : granulome, latence, reactivation, miliaire
- Resistance : MDR, XDR, pre-XDR, definition OMS, mecanismes
  (katG, rpoB, embB, gyrA, pncA)
- Outils diagnostiques : GeneXpert, LJ, MGIT, BACTEC
- Notion de "transmission cluster" en epidemiologie moleculaire

**Rendu** : pour chaque concept retenu, prevoir un encadre dans la
section appropriee du bilan (typiquement la premiere occurrence dans
"Etat des connaissances avant ce projet", "Etat actuel des
connaissances acquises", ou "Decouvertes majeures").
La syntaxe d'insertion est detaillee en Phase 9.

**Cible quantitative** : un bilan typique contient **10 a 25 encadres
pedagogiques** repartis sur l'ensemble du document, dont typiquement :
- 5 a 12 encadres `notion` (concepts de domaine)
- 3 a 6 encadres `methode` (techniques non triviales)
- 1 a 5 encadres `originalite` (un par decouverte majeure)
- 3 a 6 encadres `remarquable` (resultats frappants en soi)
- 1 a 5 encadres `fragilite` (un par fait central marque `volatile`
  ou `fragile` en Phase 1bis ; **obligatoire** pour les datations,
  estimations de taille de population, et tout chiffre dont la valeur
  exacte depend de la methode)

Un bilan court avec 2-3 encadres seulement signifie generalement que la
phase 4.6 a ete bacleee. Un bilan avec > 35 encadres peut au contraire
devenir lourd a lire et signifie qu'il faudrait fusionner certains
concepts ou eliminer les encadres `remarquable` qui ne sont pas
genuinement saisissants.
