---
name: miru-vntr
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST), peer-reviewed MTBC
  phylogenomics: use MIRU-VNTR loci as a bridge to legacy literature and
  databases, never as a replacement for WGS/SNP lineage inference. Provides
  lookup, interpretation limits, and safe handling of MIRU-profiler/TBannotator
  outputs. Use when: mapping published MIRU-VNTR profiles to MTBC context,
  comparing pre-WGS studies, or checking whether a VNTR signal is only
  historical or epidemiological support.
argument-hint: "<souche|SIT|octal|profil MIRU> [--call <assembly.fasta>] [--check-feasibility <accession SRA>]"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebFetch
user-invocable: true
---

# miru-vntr — génotypage MIRU-VNTR du MTBC : lookup avant calcul

> [!TIP]
> **Lectures longues : MIRUReader.** Ce skill suppose des lectures courtes. Pour du Nanopore ou du
> PacBio, **MIRUReader** (Chan et al., *Bioinformatics* 2019, `10.1093/bioinformatics/btz771`, MIT,
> `github.com/phglab/MIRUReader`) type les 24 loci MIRU-VNTR directement depuis les lectures longues
> non corrigées, sans assemblage. Utile quand le nombre de répétitions est justement ce que les lectures
> courtes rendent mal. Voir aussi **MAC-INMV-SSR** pour le complexe *M. avium* (skill `ntm-resources`)
> et **MSDB** pour les bases MLVA multi-espèces.


## Pourquoi ce skill, et ce qu'il n'est PAS

- **Pas un remplaçant du typage WGS/SNP** (`mtbc-lineages`, `barcoding_v2`). Le MIRU-VNTR
  est un pont vers la littérature et les bases pré-WGS, jamais une preuve phylogénétique
  autonome dans ce groupe — doctrine déjà actée dans `~/.claude/knowledge/tuberculosis.md`
  (« WGS = gold standard actuel, remplace MIRU-VNTR »).
- **Pas un calculateur MIRU-VNTR réinventé.** Le mode LOOKUP réutilise `SIT.xls`, déjà
  mirroré et lu par `sitvitweb`. Le mode CALL réutilise un outil publié (MIRU-profiler)
  plutôt que raccoder un pipeline maison de comptage de répétitions. **Vérifié en source le
  2026-08-17** : le pipeline TBannotator (`mp:/data/current/run/`) contient bien une tentative
  interne (`rules/vntr_report.smk` + `mp:/data/current/run/scripts/vntr_report.py`, primer-pairs des 24 loci MIRU-VNTR
  standard → extraction d'amplicon → TRF pour compter les répétitions), mais elle est **désactivée**
  (cible commentée dans `Snakefile`, `# expand(...vntr_report.json...)`) et le script lui-même est
  **incomplet** : il ne contient aucun `json.dump` vers sa sortie déclarée (seulement des `print()`
  capturés dans un log), et porte trois TODO non résolus par l'auteur (arrondi du nombre de copies,
  cas sans répétition détectée, contigs tronqués). **Confirmé sur disque** : `vntr_report.json`
  n'existe pour AUCUNE souche testée (0/3, y compris des souches assemblées qui ont un
  `crispr_report.json`). Ne jamais chercher ce fichier dans `report.json`/`results/<SRA>/` — il n'a
  jamais été produit en production, raison de plus de passer par MIRU-profiler (mode CALL).
- **Complémentaire à `thd`**, qui consomme un profil MIRU-VNTR déjà constitué (colonnes
  `MIRU02, MIRU04, ...` d'un CSV) mais n'en fournit aucun — c'est le trou que ce skill comble.

## Doctrine de fond (à ne jamais perdre de vue)

- **Homoplasie extensive.** Outhred et al. 2020 (Front Public Health, PMID 32974265) : le
  nombre de répétitions aux loci MIRU dérive de façon récurrente et convergente dans les
  lignées modernes du MTBC, **sans** signal adaptatif. Un profil MIRU partagé n'est pas une
  synapomorphie par défaut ; le prouver exige une reconstruction ancestrale (cf. entrée
  correspondante de `tuberculosis.md`, section génotypage).
- **Discordance MIRU-VNTR vs WGS documentée et dépendante de la lignée.** Lipworth et al.
  2018 (UKHSA, PMC6116353, cohorte prospective) : seulement **18,6 %** des paires de souches
  « identiques » en MIRU-VNTR sont à ≤5 SNV en WGS, avec un contraste marqué entre lignées
  (**8 %** pour L1, **31 %** pour L4). Un profil MIRU-VNTR identique ne dit donc quasiment
  rien de la parenté réelle, et encore moins pour les lignées à faible taux de mutation.
- **Conséquence pratique.** Un profil MIRU-VNTR (looké ou calculé par ce skill) sert de
  **clé de pont** vers une cohorte, un cluster ou une nomenclature publiés avant l'ère WGS —
  jamais d'argument de clustering de transmission ou de définition de clade dans un
  manuscrit de ce groupe.

## Mode LOOKUP (par défaut, gratuit, à toujours essayer en premier)

Source : copie locale SITVIT2 `~/Documents/codes/MTBC/TB-tools/data/SIT.xls` (62 996
isolats), déjà utilisée par le skill `sitvitweb`. Colonnes utiles : `12/15/24-loci MIRU`
(taille du panel utilisé), `VNTR` (profil, chaîne de répétitions par locus), `12/15/24-MIT`
et `VIT` (numérotation internationale MIRU/VNTR, pendant du `SIT` pour le spoligotype),
`SIT`, `Clade`. Mêmes pièges de lecture que `sitvitweb` : format OLE (`xlrd` requis dans un
venv, PEP 668), forcer `dtype=str` partout, `zfill` sur les codes à zéros de tête.

1. **Souche/SRA → profil MIRU historique** : jointure par SIT, nom d'isolat ou métadonnée
   BioSample si l'isolat provient d'une étude pré-WGS. Pour du WGS pur récent, cette colonne
   est le plus souvent vide — basculer en Mode CALL seulement si le besoin scientifique le
   justifie (voir doctrine ci-dessus).
2. **Profil MIRU (12/15/24 loci) → MIT/VIT/SIT candidats → lignée SNP**, via le pont déjà
   construit `SITVIT23882_PHELAN_SNPBASEDLIN_SORTED.xlsx` (30 646 génomes WGS portant SIT +
   `SNP-based lineage`), même logique que le crosswalk spoligotype de `sitvitweb`.
3. **Toujours rapporter la pureté** du SIT/MIT concerné (répartition réelle des lignées SNP
   pour ce type) avant de l'utiliser comme raccourci de lignée — méthode déjà validée dans
   `tuberculosis.md` (jeter les SIT/MIT à pureté < 0,90, calcul
   `groupby('MIT')['lineage'].value_counts().max()/n`).
4. **Base externe MIRU-VNTRplus** (`miru-vntrplus.org`) : à essayer seulement en repli,
   jamais en premier. État vérifié 2026-08-12 : réponse HTTP 403 au fetch direct, et un
   résultat de recherche pointant vers un service de *domain drop-catching* pour ce nom de
   domaine — signal de fragilité comparable à SITVIT2 (souvent injoignable, cf. `sitvitweb`).
   Ne pas y perdre de temps avant d'avoir épuisé `SIT.xls`.

## Mode CALL (in-silico depuis un assemblage, gardé par un test de faisabilité)

### Étape 0 — gate de faisabilité, OBLIGATOIRE avant tout calcul

**Ne jamais lancer un appel MIRU-VNTR sur un assemblage sans avoir d'abord vérifié la
plateforme et la longueur de read du run source.** Fondement publié : MIRU-profiler
(Rajwani, Shehzad & Siu 2018, *PeerJ* 6:e5090 = PMC6045920) précise noir sur blanc que
« *the MIRU-VNTR loci are not accurately assembled in genome assemblies with very short
reads (for example 150 bp)* », et fixe son seuil d'entrée validé à **reads ≥ 250 bp**.
Cohérent avec les tailles d'amplicon publiées par Supply et al. 2006 : **136 à 1374 pb**
selon le locus et l'allèle — bien au-delà d'un read Illumina 2×150 bp, et parfois au-delà
même d'un 2×250/300 bp pour les allèles à haut nombre de copies.

Récupérer plateforme + longueur moyenne de read en réutilisant le motif déjà en place dans
`sra-geolocate`/`bioproject-scout` (`esearch`/`esummary db=sra`, champ `ExpXml`), ou l'API
ENA `filereport` (`fields=instrument_platform,instrument_model,base_count,read_count`, la
longueur moyenne se dérive de `base_count/read_count`). Appliquer ensuite :

| Plateforme / longueur | Verdict | Remarque |
|---|---|---|
| PacBio (HiFi ou CLR), Oxford Nanopore | **GO** | Un seul read couvre déjà le plus grand amplicon connu (1374 pb) |
| Illumina ≥ 250 pb (MiSeq 2×250/2×300) | **GO, prudence** | Seuil validé par MIRU-profiler ; vérifier a posteriori tout allèle extrême (locus 4052/QUB-4156 en particulier) contre la plage publiée avant de le citer |
| Illumina 2×150 pb (HiSeq/NovaSeq — la majorité du dépôt SRA MTBC) | **NO-GO par défaut** | Assemblage non fiable pour ces loci d'après les auteurs de l'outil ; basculer en Mode LOOKUP ou déclarer « non évaluable depuis ce WGS » plutôt que forcer un chiffre |
| Assemblage déjà présent dans `bdd/` mais construit à partir de reads courts | **NO-GO rétroactif** | L'existence du FASTA ne rend pas le calcul plus fiable ; la restriction porte sur la longueur de read source, pas sur la disponibilité d'un assemblage |

### Étape 1 — appel, seulement après un GO

Réutiliser **MIRU-profiler** (`github.com/rahimrajwani/MIRU-profiler`) sur le FASTA
assemblé plutôt que réimplémenter un scanner de répétitions. Entrée : assemblage (SPAdes ou
équivalent) construit à partir de reads qualifiés à l'Étape 0. Sortie : nombre de
répétitions par locus (24), format tabulaire, directement réutilisable comme entrée du
skill `thd`.

### Étape 2 — interprétation

- **Ne jamais publier un profil MIRU-VNTR calculé sans mentionner explicitement** la
  plateforme et la longueur de read source, et le verdict de faisabilité de l'Étape 0. Un
  chiffre silencieux laisse croire à une fiabilité de niveau PCR alors qu'il vient d'un WGS
  court sur la limite.
- Reporter le résultat dans le même esprit qu'un couple SIT/MIT du Mode LOOKUP : comme clé
  de pont vers la littérature ou une base historique, jamais comme preuve autonome de
  cluster de transmission ou de clade (cf. doctrine de fond).

## Intégration avec l'écosystème

- **En amont de `thd`**, qui consomme un profil MIRU-VNTR déjà constitué mais n'en
  construit aucun.
- **Complémentaire à `sitvitweb`** (même fichier source `SIT.xls`, colonnes spoligotype vs
  MIRU/VNTR/MIT/VIT) — ne pas dupliquer la logique de lecture OLE/`xlrd`, la référencer.
- **Complémentaire à `sra-geolocate`/`bioproject-scout`** pour la récupération de
  métadonnées de plateforme/longueur de read (réutiliser leur motif `esearch`/`esummary`
  plutôt qu'un nouveau client NCBI).
- Pour resituer un cluster MIRU-VNTR publié sur l'arbre SNP du groupe : coupler avec
  `mtbc-lineages` / `phylo-history`.

## Ce que le skill NE DOIT PAS faire

- Lancer un calcul in-silico sans avoir d'abord tracé la plateforme/longueur de read du run
  source (Étape 0 du Mode CALL).
- Présenter un profil MIRU-VNTR (calculé ou looké) comme preuve de lignée ou de
  transmission sans le crosswalk de pureté SIT/MIT vs lignée SNP.
- Retenter l'API MIRU-VNTRplus en boucle si elle échoue une première fois — `SIT.xls` local
  suffit dans l'immense majorité des cas d'usage de ce groupe.
- Halluciner un nombre de répétitions par similarité avec un locus voisin quand
  l'assemblage ne couvre pas franchement le locus : un résultat `NA`/non évaluable est plus
  utile qu'un chiffre inventé.

## Sources

- Supply P et al. 2006, *J Clin Microbiol* — standardisation des 24 loci MIRU-VNTR, unités
  de répétition 50-100 pb, amplicons 136-1374 pb selon locus/allèle.
- Rajwani R, Shehzad S, Siu GKH 2018, *PeerJ* 6:e5090 (PMC6045920) — MIRU-profiler,
  seuil de reads ≥250 pb validé pour un appel fiable depuis un assemblage.
- Outhred AC et al. 2020, *Front Public Health* (PMID 32974265) — homoplasie extensive du
  nombre de répétitions MIRU dans les lignées modernes du MTBC.
- Lipworth S et al. 2018 (UKHSA/Oxford, PMC6116353) — évaluation quantitative MIRU-VNTR vs
  WGS pour l'identification de transmission, discordance dépendante de la lignée.
