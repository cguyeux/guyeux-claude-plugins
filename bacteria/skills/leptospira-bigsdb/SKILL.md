---
name: leptospira-bigsdb
description: >-
  Academic research database client (Guyeux group, FEMTO-ST). Queries BIGSdb Pasteur
  (Institut Pasteur, Unité Biologie des Spirochètes) for published-research Leptospira
  genomes and curated provenance metadata only. REST bridge to the pubmlst_leptospira_isolates
  and pubmlst_leptospira_seqdef databases (cgMLST scheme, 529 loci): filter isolates by clade,
  species, serogroup, serovar, host, country or sample type, export a faithful metadata table
  with an explicit completeness report, and download assembled genomes (FASTA) for a filtered
  batch.

  Use when: preparing a Leptospira genomics collaboration with Institut Pasteur, testing a
  reservoir-serovar or host-association hypothesis, building a training set to predict
  serogroup/serovar from genome sequence, or needing curated epidemiological provenance
  (host, country, clade, sample type) that plain NCBI assemblies do not carry.
---

# BIGSdb Pasteur — pont de lecture pour *Leptospira*

## Contexte

`https://bigsdb.pasteur.fr/leptospira/` (interface web) et `https://bigsdb.pasteur.fr/api`
(REST) hébergent deux bases pour le genre *Leptospira*, maintenues par l'unité Biologie des
Spirochètes de l'Institut Pasteur (Mathieu Picardeau) :

- `pubmlst_leptospira_isolates` — 1558 isolats, dont **1557 portent un génome assemblé**
  téléchargeable en FASTA, avec 38 champs de métadonnées de provenance curées.
- `pubmlst_leptospira_seqdef` — définitions d'allèles et de schémas (dont le cgMLST à 529
  loci) consommées par `pubmlst_leptospira_isolates` pour le typage.

Origine de ce skill : mail d'Alexandre Giraud-Gatineau (Institut Pasteur) du 2026-09-18. Le
volet scientifique (cadrage des questions, antériorités) vit dans
`~/.agents/knowledge/leptospira.md`, qui porte aussi le détail des mesures ci-dessous — ne pas
le dupliquer ici.

**Ce que BIGSdb apporte par rapport à NCBI** : NCBI porte davantage d'assemblages du genre
(2528 au 2026-09-22 contre 1558/1557 ici) — l'argument de volume ne joue pas en faveur de
BIGSdb. Ce qui en fait la valeur est la **métadonnée curée** : `clade`, `serogroup`, `serovar`,
`host`, `sample_type`, `country`, que NCBI ne porte pas de façon homogène.

## Accès

- **Lecture libre, sans compte**, mais **plafonnée aux dépôts soumis au plus tard le
  2024-12-31** — un avertissement de la base le dit explicitement à chaque requête (relayé sur
  stderr par le script, jamais tu). Un compte Pasteur (demandable à Alex) lève la barrière ;
  la volumétrie au-delà n'a pas pu être mesurée sans compte.
- Interface web (`bigsdb.pasteur.fr/leptospira/`) : SPA React — conditions d'utilisation et
  exigence de citation **non lisibles par `curl`**. Demander aux curateurs (via Alex) avant
  tout usage destiné à publication.

## Le pont : `scripts/bigsdb_leptospira.py`

```bash
python3 scripts/bigsdb_leptospira.py stats
python3 scripts/bigsdb_leptospira.py fields
python3 scripts/bigsdb_leptospira.py breakdown clade serogroup serovar host sample_type country
python3 scripts/bigsdb_leptospira.py search --filter clade=P2 --filter host=human --out p2_human.tsv
python3 scripts/bigsdb_leptospira.py genomes --filter clade=S2 --out-dir genomes_s2/
python3 scripts/bigsdb_leptospira.py isolate 2
```

Aucune dépendance hors `requests` (déjà présent dans l'environnement de recherche). Pas
d'authentification implémentée : le pont reste dans le plafond public 2024-12-31 ; brancher un
jeton de compte Pasteur serait une extension distincte, à faire seulement si le plafond devient
réellement bloquant pour une question posée.

### `stats` — volumétrie et répartition par clade
Premier réflexe pour vérifier que le pont fonctionne : nombre d'isolats, de génomes assemblés,
répartition par clade (P1/P2/S1/S2/Unknown).

### `fields` — champs de provenance disponibles
Liste les ~38 champs (nom, type, obligatoire, valeurs autorisées) **lue en direct depuis
l'API**, jamais codée en dur : la base évolue (nouveaux dépôts, nouveaux champs).

### `breakdown <champ...>` — répartition ET complétude réelle
Sans argument, parcourt tous les champs (~38 requêtes, quelques secondes). Calcule, par champ,
la fraction de valeurs **informatives** : `Unknown`, `unknown`, `Not examined`, `not examined`
et graphies voisines (`Unknow` observé sur `sample_type`) sont exclues, en plus des champs
absents de l'enregistrement (non simplement vides). Un comptage naïf des valeurs non vides
gonfle la complétude — mesuré à l'écriture de ce skill : `serogroup` 58,7 % informatif
(914/1558), `serovar` seulement 34,5 % (538/1558), `host` 91,0 % mais dont ~40 % de la partie
informative sont des humains, `sample_type` 69,6 %. Ces quatre chiffres sont reproduits par
`breakdown` à l'exécution (vérifié le 2026-09-22) — s'ils dérivent, la base a changé, pas le
script.

### `search --filter champ=valeur [--filter ...]` — table de métadonnées
Filtres combinés en ET logique, **égalité stricte insensible à la casse** (pas de recherche par
sous-chaîne : `country=Fran` ne retrouve pas `France`). Exporte les valeurs **brutes** de tous
les champs de provenance (fidélité : pas de normalisation qui masquerait une graphie
inattendue). Un filtre sur un nom de champ inexistant lève immédiatement, avec la liste des
noms valides ; un filtre légitimement vide (valeur hors des `allowed_values`) rend un tableau à
zéro ligne mais l'annonce sur stderr — jamais silencieux.

### `genomes --filter champ=valeur --out-dir <dir>` — téléchargement du lot
Télécharge le FASTA assemblé de chaque isolat du lot filtré (`.../contigs_fasta`), écrit un
`manifest.tsv` (id, nom d'isolat, clade, espèce, nombre de contigs et longueur totale déclarés
par la base, chemin local). **Garde-fous** : `--filter` est obligatoire, sauf `--all-isolates`
explicite (le lot non filtré pèse plusieurs Gio) ; `--limit` plafonne à 50 par défaut
(`--limit 0` pour lever le plafond) ; un lot filtré sans aucun génome associé lève une erreur
plutôt que d'écrire un répertoire vide silencieux. Vérifié le 2026-09-22 sur `clade=S2` (9
isolats, 9 génomes téléchargés, nombre de contigs de chaque FASTA reconcilié avec celui déclaré
par la base — 0 écart).

### `isolate <id>` — enregistrement JSON brut
Utile pour inspecter un cas particulier (schémas, publications liées, historique) sans passer
par `search`.

## Pièges mesurés (2026-09-22, en direct sur l'API)

1. **`GET /db/{base}/isolates?<champ>=<valeur>` ignore silencieusement un paramètre de filtre
   inconnu et renvoie toute la base** (1558 isolats) sans erreur ni avertissement — vérifié
   avec `?clade=P2`. Le seul endpoint de filtrage réel est `POST /isolates/search` avec un
   corps JSON `{"field.<nom>": "<valeur>"}`. `search`/`genomes` de ce skill n'utilisent que ce
   second endpoint ; ne jamais réintroduire un filtre en paramètres de `GET /isolates`.
2. **Plafond 2024-12-31 sans authentification** (cf. Accès) — relayé sur stderr à chaque
   commande.
3. **Graphies multiples pour « non renseigné » sur le MÊME champ** (`Unknown`/`unknown`/
   `Not examined`/`not examined`/`Unknow`), et **casse variable des valeurs réelles**
   (`human` vs `Human`, 579 contre 2 occurrences sur `host`). Ne jamais calculer une
   complétude par un simple `!= ""` ; utiliser `breakdown`.
4. **Correspondance stricte, pas de sous-chaîne**, mais **insensible à la casse** côté serveur :
   vérifié avec `country=algeria` (18 résultats, identique à `Algeria`) contre `country=Fran`
   (0 résultat, alors que `France` porte 141 isolats).

## Workflows

### A. Cadrer une collaboration : vue d'ensemble avant tout engagement
```bash
python3 scripts/bigsdb_leptospira.py stats
python3 scripts/bigsdb_leptospira.py breakdown serogroup serovar host sample_type country
```
Donne en une minute la taille réelle de tout sous-ensemble envisagé, avant de promettre un
effectif à un collaborateur.

### B. Jeu d'entraînement sérogroupe/sérovar ↔ génotype
Les isolats avec sérogroupe **et** génome forment un jeu d'entraînement direct pour un
prédicteur génomique de sérogroupe (piste `mtbc/pistes.md` P78.4.b côté volet scientifique) :
```bash
python3 scripts/bigsdb_leptospira.py search --filter serogroup=Icterohaemorrhagiae --out train_icter.tsv
python3 scripts/bigsdb_leptospira.py genomes --filter serogroup=Icterohaemorrhagiae --limit 0 --out-dir genomes_icter/
```
Répéter par sérogroupe cible, ou croiser avec `host`/`country` pour une question
réservoir-sérovar.

### C. Comparaison à un jeu NCBI
`genomes` produit un FASTA par isolat, directement typable par `bacteria:pymlst` (moteur de
typage local, cgMLST/MLST) ou classable par `bacteria:ani-panel-classify` (placement
générique par ANI) pour situer un lot BIGSdb face à des assemblages NCBI non curés.

## Caveats

- **Pas de recherche par sous-chaîne** côté serveur : construire les valeurs de filtre à partir
  de `fields`/`breakdown` (valeurs exactes observées), pas d'un nom approximatif.
- **cgMLST ≠ SNP tree** (comme pour EnteroBase) : les schémas de `pubmlst_leptospira_seqdef`
  comptent des différences alléliques, pas des mutations ; pour un placement phylogénétique
  fin, assembler puis passer par les skills MTBC génériques (arbre SNP), pas le cgMLST seul.
- **Rate limits & fair use** : serveur académique partagé (Institut Pasteur) ; `--sleep 0.2`
  par défaut entre requêtes séquentielles, ne pas paralléliser agressivement.
- **Citation/ToU non vérifiées par ce skill** (piège 2 ci-dessus) : demander confirmation aux
  curateurs avant tout usage publiant.

## Intégration avec d'autres skills

| Skill | Rôle |
|---|---|
| `bacteria:pymlst` | Typage local (MLST/cgMLST) des génomes téléchargés ici |
| `bacteria:ani-panel-classify` | Placement générique par ANI, y compris hors *Leptospira* |
| `bacteria:enterobase` | Pont de la même famille (base externe cgMLST + métadonnées) pour les genres entériques ; gabarit dont ce skill est dérivé |
| `mtbc:pangenome-enrichment`, `mtbc:mk-ascertainment` | Analyses de contenu génique/sélection par clade, génériques, applicables à un lot de génomes *Leptospira* annotés |

## Citation

```bibtex
@article{jolley2018bigsdb,
  title   = {Open-access bacterial population genomics: BIGSdb software, the PubMLST.org
             website and their applications},
  author  = {Jolley, Keith A. and Bray, James E. and Maiden, Martin C. J.},
  journal = {Wellcome Open Research},
  volume  = {3},
  pages   = {124},
  year    = {2018},
  doi     = {10.12688/wellcomeopenres.14826.1}
}
```
