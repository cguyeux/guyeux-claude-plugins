---

name: species-id
description: >-
  Academic research toolkit for peer-reviewed pathogen-genomics research (Guyeux group,
  FEMTO-ST). Bacterial species and genus identification to detect published research
  isolates mislabelled as M. tuberculosis, by two methods: the NCBI BLAST API and Mash
  screen against a RefSeq sketch. Quality-control step before adding a genome to the group's
  research database. Use when a research isolate labelled M. tuberculosis looks suspicious
  (aberrant SNP count, too few or too many SPDI, odd phylogenetic placement), when importing
  genomes from SRA or ENA, or when TBannotator reports a mixed or misassigned sample.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebFetch
---

# /species-id -- Identification d'espece bacterienne

Identifie l'espece ou le genre d'une souche bacterienne pour detecter
les etiquetages errones (ex: "M. tuberculosis" qui est en realite un
*E. coli*, un *M. abscessus*, ou une autre mycobacterie non-MTBC).

**Cas d'usage typique** : une souche recuperee du SRA est etiquetee
"Mycobacterium tuberculosis" mais presente un nombre de SPDI aberrant
(trop peu, trop eleve, ou un profil atypique dans TBannotator). Avant
de l'integrer dans la BDD ou de l'inclure dans un arbre phylogenetique,
on verifie qu'elle est bien ce qu'elle pretend etre.

---

> [!CAUTION]
> **Garde-fou anti-faux-positif (échec Mycobacterium_sp_novel, clos 2026-05-29).**
> Mesurer l'ANI TOUJOURS via **skani** (ou fastANI), ou à défaut sur contigs filtrés
> ≥ 10 kb, JAMAIS par un BLAST length-weighted sur un assemblage SPAdes complet : les
> petits contigs (rRNA, protéines ribosomales, housekeeping ultra-conservés) matchent
> toute mycobactérie à ~99 % et fabriquent un faux signal de proximité (faux 92 % vs MTBC
> au lieu du vrai ~82 %). Inclure le **panel NTM** dans la comparaison, en particulier
> ***M. kansasii*** et le complexe MKC, qui miment cliniquement la TB et sont
> régulièrement misclassifiés *M. tuberculosis* (≥ 25 cas dans TBannotator). Pour tout
> profil aberrant (compte SPDI anormal, couverture H37Rv partielle, placement instable),
> un `skani` contre `bdd/hors_mtbc/M_kansasii/` (11 type strains) au démarrage détecte
> l'erreur en quelques secondes.

## Methodes disponibles

| Methode | Stockage local | Vitesse | Precision | Quand l'utiliser |
|---------|---------------|---------|-----------|------------------|
| **BLAST API** | 0 | ~1-2 min/souche | Tres haute | Par defaut, quelques souches suspectes |
| **Mash screen** | ~1 Go (sketch) | ~5 sec/souche | Haute | Screening systematique de lots |

Par defaut : `--method blast`. Utiliser `--method mash` pour le
screening en lot, `--method both` pour la double confirmation.

---

## Declenchement

```
/species-id SRR12345678                    # BLAST API sur un accession SRA
/species-id assembly.fasta                 # BLAST API sur un FASTA local
/species-id *.fasta --method mash          # Mash screen sur un lot
/species-id SRR12345678 --method both      # Double verification
/species-id SRR12345678 --gene rpoB        # Forcer le gene marqueur
```

---

## Raccourci *Mycobacterium* : référentiel local (préférer au BLAST nt en ligne)

Si la souche est (ou pourrait être) un *Mycobacterium*, un référentiel de
reconnaissance LOCAL existe et est plus rapide/contrôlé que le BLAST nt en ligne.
Point d'entrée : **`~/docs/codes/mtbc/global_supplementary/RECOGNITION_STRATEGY.md`**
(arbre de décision à 3 niveaux). En pratique :

```bash
# 1) extraire le rpoB de la souche (mapping/assembly), puis :
blastn -query rpoB_inconnu.fa -db ~/docs/codes/mtbc/global_supplementary/conserved_gene_markers/rpoB \
       -outfmt "6 sseqid pident length" -max_target_seqs 5
# -> meilleure espèce (44 réfs ; robuste, y compris espèces divergentes leprae/gordonae/xenopi)
```

- Espèce proche de H37Rv : confirmer/affiner via les panels SPDI
  `global_supplementary/species_markers/<sp>_markers.txt` (≥50 % portés ⇒ espèce).
- Complexe (MAC/MKC) : sous-typer via `global_supplementary/species_markers/subtypes/`.
- rpoB ambigu (complexes *ulcerans*, *intracellulare*/*paraintracellulare*…) : best-ref
  mapping (`a_ranger_phylo/analyses/phase53b_identify_best_ref.py`).
- Distinguer MTBC / *M. canettii* / NTM : voir le skill `mtbc-lineages` (non-MTBC screen).

Le BLAST nt en ligne ci-dessous reste le recours pour les genres NON couverts par ce
référentiel (contamination non-mycobactérienne, organisme hors panel).

## Phase 0 -- Resolution de l'entree

### Cas 1 : Accession SRA/ENA (SRR*, ERR*, DRR*)

1. Telecharger l'assembly ou les reads via :
   ```bash
   # Verifier si un assembly existe dans la BDD locale
   ls ~/docs/codes/mtbc/bdd/actuelle/*/<SRA>/assembly.fasta 2>/dev/null

   # Sinon, tenter de recuperer depuis NCBI
   # Option A : assembly pre-calcule via datasets
   datasets download genome accession <SRA> --filename /tmp/species_id_<SRA>.zip

   # Option B : si pas d'assembly, recuperer le FASTA du contig/scaffold
   # via le report.json de TBannotator (champ "assembly_accession")
   ```

2. Si aucune sequence n'est recuperable : signaler a l'utilisateur et
   proposer de telecharger les reads FASTQ (plus lourd).

### Cas 2 : Fichier FASTA local

Utiliser directement le fichier fourni.

### Cas 3 : Plusieurs fichiers (lot)

Traiter sequentiellement, produire un tableau recapitulatif.

---

## Phase 1 -- Extraction du gene marqueur

Le gene marqueur est la sequence qu'on va soumettre a BLAST pour
identifier l'espece. Utiliser un gene conserve et discriminant.

### Selection du gene (`--gene` ou `auto`)

| Gene | Pouvoir discriminant | Taille | Quand l'utiliser |
|------|---------------------|--------|------------------|
| **rpoB** | Tres haut (espece) | ~3500 bp | Defaut pour mycobacteries |
| **16S rRNA** | Haut (genre/espece) | ~1500 bp | Quand rpoB absent |
| **hsp65** | Haut (mycobacteries) | ~440 bp | Confirmation mycobacterienne |

En mode `auto` (defaut) :
1. Chercher rpoB dans l'assembly (BLAST local si blastn disponible,
   sinon recherche par coordonnees H37Rv : 759807-763325)
2. Si rpoB non trouve : chercher 16S rRNA (coordonnees H37Rv :
   1471846-1473382)
3. Si rien trouve : utiliser les premiers 10 000 bp de l'assembly
   (moins precis mais fonctionnel)

### Extraction

```python
from Bio import SeqIO

# Charger l'assembly
records = list(SeqIO.parse("assembly.fasta", "fasta"))

# Chercher rpoB par BLAST local contre la reference H37Rv
# ou par coordonnees si le genome est proche de H37Rv
```

**Si l'assembly est multi-contig** : chercher le gene sur le plus grand
contig d'abord.

**Si l'assembly est absent et qu'on n'a que des reads** : utiliser les
reads directement (soumettre les 10 000 premieres bases du plus long
read, ou un sous-echantillon).

---

## Phase 2a -- Methode BLAST API

Soumettre le gene marqueur a NCBI BLAST via l'API Biopython.

### Execution

```python
from Bio.Blast import NCBIWWW, NCBIXML

# Soumettre a BLAST
result_handle = NCBIWWW.qblast(
    program="blastn",
    database="nt",           # ou "ref_genomic" pour plus de vitesse
    sequence=marker_sequence,
    megablast=True,
    hitlist_size=10,
    entrez_query="Bacteria[ORGN]"
)

# Parser les resultats
blast_records = NCBIXML.parse(result_handle)
blast_record = next(blast_records)
```

### Interpretation des resultats

Pour chaque hit dans les 10 meilleurs :

1. **Extraire** : organisme, score, e-value, % identite, % couverture
2. **Classer** par % identite × % couverture (score composite)

### Criteres de decision

| % identite | Interpretation |
|------------|---------------|
| >= 99% | Meme espece (probable) |
| 97-99% | Meme genre, espece proche |
| 95-97% | Meme genre, espece differente |
| 90-95% | Meme famille probable |
| < 90% | Genre different |

**Pour les mycobacteries specifiquement** (rpoB) :
- >= 97% : meme espece
- 94-97% : meme genre, espece differente
- Les especes du MTBC (M. tuberculosis, M. bovis, M. africanum,
  M. caprae, M. microti, M. pinnipedii, M. canettii...) ont >99.5%
  d'identite entre elles sur rpoB, la discrimination intra-MTBC
  se fait par SNP, pas par marqueur.

### Format de sortie BLAST

```
=== Species ID : <nom/accession> ===
Methode   : BLAST API (blastn vs nt)
Gene      : rpoB (3519 bp)
Soumis le : YYYY-MM-DD HH:MM

Top 5 hits :
  1. Mycobacterium tuberculosis H37Rv  99.97%  (e=0.0, cov=100%)
  2. Mycobacterium bovis AF2122/97     99.94%  (e=0.0, cov=100%)
  3. Mycobacterium africanum           99.89%  (e=0.0, cov=100%)
  4. Mycobacterium canettii            99.72%  (e=0.0, cov=100%)
  5. Mycobacterium abscessus           92.14%  (e=0.0, cov=98%)

Verdict : ✓ MTBC confirme (M. tuberculosis complex)
  Confiance : haute (identite >= 99.5% sur rpoB)
```

Ou en cas de mauvais etiquetage :

```
Verdict : ✗ PAS MTBC — Escherichia coli detecte
  Hit #1 : Escherichia coli str. K-12  99.8% identite
  Etiquetage SRA : "Mycobacterium tuberculosis"
  Confiance : tres haute
  Action recommandee : exclure de la BDD MTBC
```

---

## Phase 2b -- Methode Mash screen

### Prerequis (a installer une seule fois)

```bash
# Installer Mash
conda install -c bioconda mash   # ou apt install mash

# Telecharger le sketch RefSeq (~1 Go)
wget https://gembox.cbcb.umd.edu/mash/refseq.genomes.k21s1000.msh \
  -O ~/databases/refseq.genomes.k21s1000.msh
```

Si Mash n'est pas installe ou si le sketch n'est pas present :
signaler a l'utilisateur et proposer les commandes d'installation.
Ne PAS bloquer, basculer sur la methode BLAST API.

### Execution

```bash
# Screen d'un assembly contre RefSeq
mash screen -w -p 4 \
  ~/databases/refseq.genomes.k21s1000.msh \
  assembly.fasta \
  | sort -gr \
  | head -10
```

### Interpretation

Les colonnes de sortie de `mash screen` :
- **identity** : estimation de l'identite ANI
- **shared-hashes** : nombre de k-mers partages
- **median-multiplicity** : profondeur (utile pour reads)
- **p-value** : significativite
- **query-ID** : accession RefSeq du hit

### Criteres de decision (Mash)

| Identite Mash | Interpretation |
|---------------|---------------|
| >= 0.99 | Meme espece |
| 0.95-0.99 | Meme genre |
| 0.90-0.95 | Genre proche |
| < 0.90 | Organisme different |

### Format de sortie Mash

```
=== Species ID : <nom/accession> ===
Methode   : Mash screen (RefSeq k21s1000)
Input     : assembly.fasta (4.4 Mb, 1 contig)
Temps     : 3.2 sec

Top 5 hits :
  1. GCF_000195955.2  M. tuberculosis H37Rv     0.9998  (987/1000)
  2. GCF_000427155.1  M. bovis AF2122/97        0.9995  (984/1000)
  3. GCF_000253375.1  M. africanum GM041182     0.9991  (979/1000)
  4. GCF_000789395.1  M. canettii CIPT 140010059  0.9974  (961/1000)
  5. GCF_000069185.1  M. marinum M              0.9214  (412/1000)

Verdict : ✓ MTBC confirme
```

---

## Phase 3 -- Synthese et rapport

### Mode souche unique

Afficher le verdict directement dans la console (voir formats ci-dessus).

### Mode lot (plusieurs souches)

Produire un tableau recapitulatif :

```
=== Species ID — Screening lot (N souches) ===
Methode : <blast|mash|both>
Date    : YYYY-MM-DD

| Souche | Etiquetage SRA | Espece identifiee | Identite | Verdict |
|--------|---------------|-------------------|----------|---------|
| SRR001 | M. tuberculosis | M. tuberculosis  | 99.97% | ✓ OK |
| SRR002 | M. tuberculosis | E. coli          | 99.81% | ✗ MAL ETIQUETEE |
| SRR003 | M. tuberculosis | M. abscessus     | 99.45% | ✗ MAL ETIQUETEE |
| SRR004 | M. tuberculosis | M. bovis         | 99.94% | ⚠ MTBC (pas M.tb) |
| SRR005 | M. tuberculosis | M. tuberculosis  | 99.98% | ✓ OK |

Resume :
  Total : 5 souches
  ✓ MTBC confirme (M. tuberculosis) : 2
  ⚠ MTBC mais autre espece (M. bovis) : 1
  ✗ Mal etiquetees : 2
    - SRR002 : E. coli (contaminant probable)
    - SRR003 : M. abscessus (NTM, pas MTBC)

Action recommandee :
  - Exclure SRR002 et SRR003 de la BDD MTBC
  - SRR004 : verifier si le projet attend M. tuberculosis stricto sensu
    ou tout le complexe MTBC
```

### Mode `--method both`

Lancer les deux methodes et comparer :

```
=== Double verification : <souche> ===

| Methode | Espece #1 | Identite | Espece #2 | Identite |
|---------|-----------|----------|-----------|----------|
| BLAST   | M. tuberculosis | 99.97% | M. bovis | 99.94% |
| Mash    | M. tuberculosis | 0.9998 | M. bovis | 0.9995 |

Concordance : ✓ Les deux methodes convergent vers M. tuberculosis
```

Si discordance : signaler et recommander une investigation manuelle.

---

## Cas particuliers

### Distinction intra-MTBC

rpoB et 16S ne distinguent PAS les especes du MTBC entre elles
(>99.5% d'identite). Pour ca, utiliser les outils MTBC existants :
- `/tb-cli` ou `/tbannotator-mcp` pour le typage par SNP
- Les regions de deletion (RD) : RD1, RD4, RD9, RD12, etc.

Le skill `/species-id` repond a la question "est-ce du MTBC ?" pas
"quelle espece du MTBC ?".

### Contamination mixte

Si les deux premiers hits ont des genres differents avec des scores
proches, suspecter une contamination mixte :

```
⚠ CONTAMINATION MIXTE SUSPECTEE
  Hit #1 : M. tuberculosis  99.3%
  Hit #2 : E. coli          98.7%
  → L'echantillon contient probablement deux organismes
  → Recommandation : verifier les reads, chercher des adaptateurs,
    re-assembler avec filtrage de contamination
```

### Mycobacteries non-tuberculeuses (NTM)

Si le hit #1 est une mycobacterie hors MTBC (M. avium, M. abscessus,
M. kansasii, M. marinum, etc.) : le signaler explicitement comme NTM
et recommander l'exclusion de la BDD MTBC.

---

## Integration avec l'ecosysteme

- **/tbannotator-mcp** : si TBannotator rapporte un nombre de SPDI
  anormal pour une souche, lancer `/species-id` pour verifier
- **/fetch-tbannotator** : recuperer l'assembly depuis le report.json
- **/ncbi-pathogen-detection** : verifier si la souche est dans la base
  NCBI Pathogen Detection et avec quel organisme
- **/phylo-history** : une souche qui se place systematiquement en
  long branch dans tous les arbres pourrait etre mal etiquetee
- **`tbmonitor-papers`** : une fois une espece non-TB identifiee,
  confirmer si le BioProject / la SRA sous-jacente a **deja ete
  rapportee comme mal classee dans la litterature publiee**,
  rechercher l'identifiant SRA / BioProject dans le titre ou
  l'abstract du corpus PubMed TB pre-indexe

---

## Points de vigilance

1. **BLAST API est lent** : ~1-2 min par souche. Pour plus de 10
   souches, privilegier Mash.
2. **Rate limiting NCBI** : ne pas soumettre plus de 3 requetes par
   seconde. Ajouter un delai de 3s entre les soumissions en lot.
3. **Mash non installe** : basculer sur BLAST API sans bloquer.
4. **Sketch RefSeq absent** : proposer le telechargement, ne pas
   bloquer.
5. **Assemblies de mauvaise qualite** : si l'assembly est tres
   fragmente (>100 contigs), les resultats sont moins fiables.
   Mentionner la qualite de l'assembly dans le rapport.
6. **Cache** : ne pas re-BLASTer une souche deja verifiee. Stocker
   les resultats dans un fichier `species_id_results.tsv` dans le
   repertoire du projet pour eviter les requetes redondantes.
7. **Espace disque** : le sketch RefSeq fait ~1 Go. Verifier l'espace
   disponible avant de proposer le telechargement.
8. **Pas de distinction intra-MTBC** : ce skill repond "est-ce du
   MTBC ?" pas "M. tuberculosis ou M. bovis ?". Pour ca, utiliser
   les outils de typage SNP.

## Codex packaging note

This packaged copy targets Codex. MCP tool names in `allowed-tools` are prerequisites: verify them with `codex mcp list` in the active profile before relying on live queries.
