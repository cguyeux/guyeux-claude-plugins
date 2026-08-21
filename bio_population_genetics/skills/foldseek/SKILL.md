---
name: foldseek
description: >
  Academic research toolkit for peer-reviewed structural bioinformatics in the
  Guyeux group (FEMTO-ST). This skill should be used when the user asks to
  search a protein structure with Foldseek, compare AlphaFold or ESMFold models
  against PDB, AlphaFold DB or CATH, investigate a structurally conserved dark
  gene, interpret Foldseek E-values and TM-scores, or cluster predicted protein
  structures without overclaiming molecular function.
---

# foldseek : recherche de repli structural, locale ou web

## Quand l'utiliser, et quand NE PAS

**Utiliser** pour comparer un modèle 3D (AlphaFold, ESMFold) à des bases de structures connues (PDB,
AlphaFold DB, CATH) et détecter une homologie de REPLI invisible en séquence — le point de départ
classique d'un dark gene bien replié mais sans hit Pfam/BLAST exploitable.

**Ne PAS utiliser** pour conclure une fonction à partir d'un seul hit de repli : un même repli peut
servir des fonctions très différentes (ferredoxin-like : liaison ARN, régulation, signalisation…). Un
hit Foldseek nomme une FAMILLE STRUCTURALE candidate, jamais une activité — croiser avec
`active-site-check` (résidus catalytiques M-CSA) avant de requalifier un gène vers une enzyme nommée.

## Pourquoi ce skill existe

Foldseek est utilisé de longue date à travers l'écosystème MTBC (`annotation_mtbc/analyses/phase2c_foldseek_dark.py`,
`phase16_alphafold_foldseek.py`, `phase36_dark_structural_clustering.py`, et divers projets de lignée),
mais sans documentation centralisée : chaque script réinvente ses chemins, ses seuils et son format de
sortie. Ce skill consolide ce qui a été appris en production, y compris deux pièges vécus qui ont coûté
du temps de diagnostic.

## Base locale déjà construite — VÉRIFIER AVANT DE (RE)TÉLÉCHARGER

**Emplacement canonique, partagé par tous les projets MTBC** : `annotation_mtbc/tools/`.

```
annotation_mtbc/tools/
├── foldseek/bin/foldseek       # binaire (statically linked, ~50 Mo compressé)
├── foldseek_db/pdb*            # base PDB complète, ~4,3 Go
└── foldseek_afdb/afdb_sp*      # base AlphaFold DB / Swiss-Prot, ~3,9 Go
```

**Piège vécu (2026-08-01→03, projet Rv2516c) : un check de présence sur un MAUVAIS chemin relatif a
fait croire à une suppression qui n'avait jamais eu lieu.** `ls tools/foldseek/bin/` lancé depuis un
sous-projet (`mtbc/<projet>/`) renvoie « introuvable » puisque `tools/` n'existe QUE sous
`annotation_mtbc/`, jamais sous un sous-projet — ce n'est pas une preuve de suppression, seulement la
preuve qu'on a cherché au mauvais endroit. Cela a fondé à tort tout un récit d'incident (venv disparu,
runner à durcir) dans le cahier de labo d'un projet, jusqu'à ce qu'un test direct révèle le binaire et
les deux bases parfaitement intacts et fonctionnels, avec un binaire vieux de plus d'un an (jamais
retouché). **Toujours vérifier avec le CHEMIN ABSOLU ou relatif à `annotation_mtbc/` explicitement**
avant de conclure à une disparition et de déclencher une réinstallation de plusieurs Go :

```bash
ls -la /chemin/vers/mtbc/annotation_mtbc/tools/foldseek/bin/foldseek   # jamais un chemin relatif ambigu
/chemin/vers/mtbc/annotation_mtbc/tools/foldseek/bin/foldseek version  # test minimal, doit rendre un hash
```

## Installation (si réellement absente — binaire + une base)

```bash
# Binaire (vérifier AVX2 : cat /proc/cpuinfo | grep avx2, sinon build SSE2)
wget https://mmseqs.com/foldseek/foldseek-linux-avx2.tar.gz
tar xvzf foldseek-linux-avx2.tar.gz -C tools/       # -> tools/foldseek/bin/foldseek
# Alternative sans wget : conda install -c conda-forge -c bioconda foldseek

# Base (choisir selon le besoin ; PDB est la plus petite et la plus rapide à interpréter)
tools/foldseek/bin/foldseek databases PDB tools/foldseek_db/pdb tmp/
tools/foldseek/bin/foldseek databases Alphafold/Swiss-Prot tools/foldseek_afdb/afdb_sp tmp/
```

**Coût réel avant de lancer** : `foldseek databases` liste les options avec leur URL, mais PAS leur
taille précompressée — mesurer le `du -sh` d'une base sœur déjà construite (PDB ≈ 4,3 Go, AFDB/Swiss-Prot
≈ 3,9 Go) donne un ordre de grandeur avant de committer plusieurs Go sur un disque déjà chargé. **`df -h`
avant, systématiquement** — même règle que pour Boltz (cf. skill `boltz`), et le même risque : un disque
d'analyse MTBC tourne souvent au-delà de 90 % d'occupation.

## Recherche locale (`easy-search`)

```bash
tools/foldseek/bin/foldseek easy-search modele.pdb tools/foldseek_db/pdb sortie.m8 tmp/ \
    --format-output query,target,evalue,alntmscore,qstart,qend,tstart,tend
```

**Toujours demander `alntmscore`** (TM-score de l'alignement) en plus de `evalue` : Foldseek est un
outil de REPLI, le TM-score est le signal principal, l'E-value un filtre de rappel. Sans lui, il faut
recalculer l'alignement pour obtenir le TM-score, un aller-retour évitable.

**Comparer un DOMAINE, pas la protéine entière, sur toute protéine multidomaine.** Mesuré à répétition
sur le projet Rv2516c : chercher la protéine entière DILUE le signal du domaine informatif — un gain de
plus de 4 500× en E-value a été mesuré en isolant un domaine de 60 aa d'une protéine de 267 aa
(HHpred), et un gain comparable existe pour Foldseek : la protéine entière ne rendait AUCUN hit
Ig-like alors qu'un domaine C-terminal de 90 aa, isolé, en rendait un consensus massif. **Découper le
modèle par domaine (carte de contacts CA, zéro contact inter-segments = frontière) avant de chercher**,
systématiquement sur toute protéine de plus de ~150 aa sans hit net sur la séquence entière.

## Recherche web (`search.foldseek.com`) — quand la base locale ne suffit pas

Utile pour : une base non construite localement (AFDB complet au-delà du sous-ensemble Swiss-Prot,
CATH50, ESMAtlas30), ou l'absence de toute base locale. Gratuit, scriptable, sans compte :

```bash
curl -s https://search.foldseek.com/api/ticket -F q=@modele.pdb -F mode=3diaa \
    -F 'database[]=pdb100' -F 'database[]=afdb-swissprot' -F 'database[]=cath50'
# -> {"id": "...", "status": "..."}  -- poll :
curl -s https://search.foldseek.com/api/ticket/<id>
# une fois COMPLETE :
curl -sL https://search.foldseek.com/api/result/download/<id> -o resultat.tar.gz
```

**PIÈGE VÉCU, à ne jamais refaire : les résultats réels sont dans `alis_<db>.m8`, PAS
`alis_<db>_report.m8`.** Le fichier `_report.m8` est un rapport de TAXONOMIE agrégée (comptage par
espèce), pas la liste des hits structuraux — un parseur naïf qui l'ouvre en pensant lire des hits
produit un classement vide ou incohérent sans message d'erreur. Toujours cibler explicitement
`alis_<nom_de_base_sans_report>.m8`.

## Lecture des résultats : seuils, et ce qu'un hit ne dit PAS

Convention validée en production sur plusieurs dark genes (Rv1025, Rv2516c, Rv3222c…) :

| E-value | Lecture |
|---|---|
| < 1e-3 | significatif |
| ~1e-2 | suggestif, à corroborer par une autre méthode avant de citer |
| > 1 | bruit — même répété sur plusieurs hits de la même famille, un TM-score de 0,6-0,7 sur un petit repli α/β reste ordinaire |

**Un hit non significatif répété n'en devient pas significatif.** Huit hits Foldseek non significatifs
vers la même famille structurale ne remplacent pas un hit significatif ; ils appuient tout au plus un
FAISCEAU d'indices, à écrire comme tel (« convergence de plusieurs axes non significatifs »), jamais
comme une preuve. Toujours donner `significant: E<1e-3` explicitement à côté du TM-score dans tout
dossier ou fiche généré automatiquement — un TM-score cité seul, sans son statut de significativité,
est la source documentée d'un cadrage fondateur faux sur au moins un projet MTBC (dossier `<Rv>_dossier.txt`,
correctif atlas P18.2).

**Même repli ≠ même fonction, et encore moins même partenaire.** Un hit vers une enzyme exige une
vérification `active-site-check` (résidus catalytiques M-CSA conservés) avant toute requalification.
Un hit vers un régulateur transcriptionnel n'implique ni le même opérateur, ni le même partenaire.

## All-vs-all entre dark genes : trouver des familles sans base externe

Quand la recherche contre une base externe (PDB/AFDB) n'a rien donné, un Foldseek du dossier de modèles
CONTRE LUI-MÊME (query = target = même dossier) révèle des familles de repli paralogues propres au
protéome, invisibles en séquence — coût quasi nul si les modèles sont déjà sur disque, aucun
téléchargement :

```bash
foldseek easy-search modeles/ modeles/ aln.m8 tmp/ \
    --format-output query,target,evalue,alntmscore,qstart,qend,tstart,tend
```

Construire un graphe (arête si `query != target`, TM-score ≥ 0,5, E ≤ 0,01) et en extraire les
composantes connexes. Deux usages productifs : (1) un cluster contenant au moins un membre caractérisé
propage sa fonction candidate aux membres dark de la même famille (guilt-by-structure) ; (2) un dark qui
clusterise avec une toxine connue et a une antitoxine adjacente dans le génome est un candidat système
toxine-antitoxine. **Garde-fous obligatoires avant de citer un cluster** : flaguer tout cluster dominé
par des hélices transmembranaires multiples (promiscuité structurale, pas homologie réelle), par une
composition en acides aminés de faible complexité, ou par un pLDDT moyen < 60 (modèle non fiable).

## Voir aussi

- `boltz` — prédiction de complexes (multimères, ions, ligands) ; Foldseek ne prédit pas d'interaction,
  seulement une similarité de repli entre structures déjà modélisées.
- `active-site-check` — valide un hit Foldseek vers une enzyme par conservation des résidus catalytiques.
- `esm-atlas-cli` — structures ESMFold et recherche de similarité par contenu-hash, alternative légère
  quand aucun modèle AlphaFold n'existe encore pour la protéine.
