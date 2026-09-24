---

name: sra-geolocate
description: >-
  Consolidation de l'origine geographique et de la date de collecte d'une souche
  SRA, ou construction d'un dataset de SRA par zone : pays, ville, region,
  zone supranationale (Sahel, Maghreb, Corne de l'Afrique), coordonnees.
  Cascade BioSample / BioProject / PubMed / supplementary materials, avec score
  de confiance et source tracee ; distingue collecte et sequencage.
  Use when: geo_loc_name ou collection_date vague ou vide, cohorte TB par
  region, verification d'origine avant inclusion, incoherences entre sources.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebFetch, WebSearch
---

> [!WARNING]
> **[2026-09-08] TABLES ABSENTES du serveur tblearn.** Ce skill interroge 1 objet(s) qui
> n'existent plus depuis le remplacement du MCP TBannotator. Contrairement au filtre `system_name`,
> ces requêtes ne rendent pas un ensemble vide : elles **lèvent une erreur** `relation does not exist`.
>
> | table citée ici | remplacer par | fondement |
> |---|---|---|
> | `mv_spdi_mutations` | **tb_report_spdi ⋈ tb_report_spdi_annotations sur spdi_id** | le variant dans la première, l'annotation (`locus_tag`, `hgvs_p`, `impact`) dans la seconde |
>
> Correspondances établies en comparant les colonnes, pas devinées. Détail et schéma complet :
> `~/.agents/knowledge/tblearn-migration.md`.


> [!WARNING]
> **[2026-09-08] Les requêtes de ce skill qui filtrent sur un système de lignée MAISON ne rendent
> plus rien.** Le MCP TBannotator est arrêté ; le serveur `tblearn` qui le remplace ne porte que
> huit systèmes **externes** (Coll, Coscolla, Freschi, Lipworth, Napier, Palittapongarnpim,
> Shitikov, Stucki). `system_name = 'guyeux'` et `system_name = 'tblearn'` y rendent **zéro ligne
> sans lever d'erreur**, ce qu'un script lira comme « aucune souche ne satisfait le critère ».
>
> **Substitution, décidée le 2026-09-08 :** les lignées maison se lisent désormais dans la base
> LOCALE `bdd/actuelle/`, qui fait déjà autorité selon
> `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`, via le skill `bdd-bridge` :
>
> ```bash
> B=~/docs/environnement/plugins/mtbc/skills/bdd-bridge/scripts
> export TBANNOTATOR_BDD=~/docs/codes/mtbc/bdd
> python3 $B/bdd_query.py clades                # tous les clades et leurs effectifs
> python3 $B/bdd_query.py denominator <clade>   # effectif réellement exploitable
> python3 $B/bdd_query.py strains <clade>       # souches d'un clade
> ```
>
> `tblearn` reste utilisable pour tout le reste (SPDI, QC, métadonnées, RD, IS, CRISPR) et pour
> **comparer** à une taxonomie externe, mais ce n'est plus la source des lignées maison. Toute
> requête qui filtre sur `system_name` doit d'abord vérifier que le filtre a matché :
> `SELECT system_name, count(*) FROM mv_strain_lineage WHERE system_name = '<x>' GROUP BY 1;`
> — zéro ligne signifie « ce système n'existe pas ici », jamais « aucune souche ».
>
> Détail complet : `~/.agents/knowledge/tblearn-migration.md`.


# /sra-geolocate -- Origine geographique des SRA

Deux modes d'emploi complementaires :

1. **Check** -- verifier ou enrichir l'origine geographique d'un SRA donne
   (ou d'une liste). Chaque entree est resolue via une cascade de sources,
   avec score de confiance et source tracee.
2. **Dataset** -- construire une liste de SRAs appartenant a une zone
   geographique donnee (ex : "Franche-Comte", "Sahel", "Maroc", "Bolivie")
   en cherchant via BioProject, PubMed, Europe PMC, et en validant chaque
   candidat via le cascade du mode check.
3. **Bulk** -- consolider geo+date d'une **lignee MTBC entiere** (10k-80k
   souches) en une requete via son marqueur SPDI racine, hors cascade
   per-SRA. Voir la section **« Mode BULK »** dediee plus bas.

Les modes partagent le meme moteur d'extraction et le meme cache.

---

## Prealable -- Consultation memoire projet

1. Verifier la presence d'un `CLAUDE.md` local → conventions projet.
2. **Cache BioProject central MTBC** (à consulter EN PREMIER pour les souches MTBC) :
   `mtbc/global_supplementary/bioproject_geo/bioproject_metadata.tsv` mappe chaque
   BioProject (**1366+ connus** au 2026-05-31, tout le MTBC) vers `country, date_min,
   date_max, confidence, institution, title, submission_year`. Beaucoup de souches à
   `geo_loc_name` vide sont géolocalisables instantanément via le pays de leur
   BioProject (confidence>=3, mono-pays). Règle de consolidation : géo per-strain
   BioSample prioritaire, sinon pays BioProject. Étendre via `sweep_bioprojects.py
   <liste>` (cf. README du dossier). Raccourci O(BioProjects), pas O(souches).
   **Tables per-strain DÉJÀ consolidées** (à réutiliser avant tout recalcul) :
   `consolidated_geo_<clade>.tsv` pour L1, L2, L3, L4, L5, L6, L7-L10, Bovis,
   animals_other, Canettii, schéma `strain, lineage, country, country_source,
   date_min, date_max, date_source, flag, bioproject`. Pour (re)consolider une lignée
   ENTIÈRE à l'échelle 10k-80k souches, voir la section **« Mode BULK »** plus bas
   (récupération par marqueur de lignée, pas cascade per-SRA).
3. Verifier si un cache partage `sra_geo_cache.csv` existe dans
   `~/.cache/codex/sra-geolocate/` ou dans le repertoire courant → le
   charger. Le cache evite de re-interroger NCBI pour une meme SRA.
3. Verifier la BDD TBannotator locale si disponible
   (`~/docs/codes/mtbc/bdd/actuelle/`) : chaque SRA traite y a
   potentiellement un `report.json` avec des metadonnees deja extraites
   localement → lire en priorite avant toute requete distante.
4. Si `rangement.pkl` est accessible via `tb-cli`, noter les lignages
   connus des SRAs a traiter (utile pour cross-check geographique :
   Bovis en France, L4.9 en Corne de l'Afrique...).

---

## Declenchement

```
# Mode CHECK : un SRA
/sra-geolocate SRR12345678
/sra-geolocate SRR12345678 --deep

# Mode CHECK : liste de SRAs
/sra-geolocate strains.csv
/sra-geolocate strains.csv --output enriched.csv --deep

# Mode DATASET : construire une cohorte par zone
/sra-geolocate --zone "Franche-Comte"
/sra-geolocate --zone "Sahel" --deep
/sra-geolocate --zone "Morocco" --output morocco_cohort.csv

# Mode HYBRID : filtrer une liste par zone
/sra-geolocate strains.csv --zone "France"
```

**Options** :
- `--deep` : pousser jusqu'a l'inspection du texte integral des articles
  PubMed/PMC lies (PDF via Unpaywall, XML via Europe PMC). Sans cette
  option, le skill s'arrete aux abstracts au niveau 4. Les
  supplementary materials (niveau 4b) sont actifs par defaut, hors
  `--deep`.
- `--no-supp` : desactiver le niveau 4b (supplementary materials).
  Utile pour les batchs massifs ou la bande passante est limitee.
- `--cache <path>` : chemin du cache persistant. Defaut :
  `~/.cache/codex/sra-geolocate/sra_geo_cache.csv`.
- `--output <file>` : CSV de sortie. Defaut : `sra_geolocate_YYYY-MM-DD.csv`.
- `--min-confidence N` : ne retenir que les resultats avec confiance
  geographique >= N (la confiance date est independante).
- `--date-only` : ne consolider que la date, ignorer la cascade location.
- `--location-only` : ne consolider que la location (comportement
  historique du skill avant ajout de la cascade date).
- `--force` : ignorer le cache, re-interroger les sources.

---

## Phase 0 -- Chargement du cache et normalisation de l'entree

1. Charger le cache s'il existe. Schema :

   ```
   sra,location_text,country,region,city,lat,lon,confidence,source,queried_at,notes
   SRR12345,"Paris, France",France,Île-de-France,Paris,48.85,2.35,5,biosample,2026-04-09,
   ERR9876,"Alsace (Project title)",France,Grand Est,,,,3,bioproject,2026-04-09,
   ...
   ```

2. Determiner le mode d'invocation :
   - Argument = accession SRA (regex `^[DES]RR\d+$`) → mode CHECK simple.
   - Argument = fichier (`.csv`, `.tsv`, `.txt`) → mode CHECK batch,
     lire la liste (chercher une colonne `sra`, `accession`, ou la
     premiere colonne).
   - `--zone` sans argument positionnel → mode DATASET pur.
   - `--zone` avec fichier → mode HYBRID (filtrer la liste par zone).

3. Si `--zone` est fournie : passer en Phase 1 (resolution de zone)
   avant de traiter les SRAs.

---

## Phase 1 -- Resolution de la zone cible (si applicable)

La zone est un texte libre. Il faut la canoniser pour pouvoir decider si
une location donnee la matche.

1. **Classification** de la zone :
   - Pays (ISO 3166) : "France", "Morocco", "Bolivia" → utiliser
     `pycountry` ou la liste ISO.
   - Region administrative sous-nationale : "Franche-Comte", "Alsace",
     "Bavaria", "Rif" → identifier le pays parent et la hierarchie
     admin via Nominatim (OpenStreetMap) ou Geonames.
   - Ville : "Besancon", "Casablanca" → resoudre en pays + region.
   - Supranational : "Sahel", "Maghreb", "Corne de l'Afrique",
     "Caucase", "Amerique Latine", "Afrique de l'Ouest" → lister les
     pays membres via connaissance geographique (pas besoin d'API,
     mais tracer explicitement les pays inclus dans le cache).
   - Coordonnees : "48.8N 2.3E" ou "48.85,2.35" → definir un rayon
     par defaut (100 km, modifiable via `--radius`).

2. **Expansion** de la zone : pour chaque zone, construire une liste
   de **termes de recherche** :

   ```
   Zone : "Franche-Comte"
     Pays parent : France
     Regions       : Franche-Comte, Bourgogne-Franche-Comte, Grand Est (partiel)
     Villes cles   : Besancon, Belfort, Montbeliard, Dole, Vesoul, Lons-le-Saunier
     Departements  : Doubs, Jura, Haute-Saone, Territoire de Belfort
     Codes postaux : 25xxx, 39xxx, 70xxx, 90xxx
     Termes EN     : Eastern France, Jura region
     Termes FR     : Franche-Comte, Besancon, Doubs, Jura
   ```

   Cette expansion sert double usage :
   - Requetes de recherche NCBI/PubMed (mode DATASET)
   - Matching fuzzy des locations extraites (mode CHECK + `--zone`)

3. **Afficher** la zone resolue a l'utilisateur avant de proceder :

   ```
   Zone cible : "Franche-Comte"
     Pays parent : France (FR)
     Type        : Region administrative
     Termes de recherche : 14 (villes, departements, variants)
     Rayon de match : N/A (zone nommee)
   Proceder ? [Phase 2]
   ```

---

## Phase 2 -- Collecte des SRAs candidats

**Parallelisation** : en mode DATASET, les strategies 1-4 ci-dessous sont
independantes. Lancer les curl/WebFetch des differentes strategies en
parallele (meme message) plutot qu'en cascade. Seule la deduplication
finale est sequentielle. En mode CHECK sur une liste de SRA, les
`efetch` individuels partent aussi en parallele.

### Mode CHECK (SRA ou liste donnes)

Rien a collecter : la liste est l'entree. Passer a la Phase 3.

### Mode DATASET (zone seule)

Chercher des candidats a partir de la zone. Strategies a cascader :

0. **Recherche BioSample directe** (a essayer en premier pour les zones
   nommees -- pays, regions administratives, villes -- ou la zone matche
   directement le champ `geo_loc_name` indexe par NCBI) :

   ```bash
   curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=biosample&term=%22Mycobacterium+tuberculosis%22%5BOrganism%5D+AND+Lebanon%5BAll+Fields%5D&retmax=1000"
   ```

   Cette recherche est tres efficace pour les pays / zones nommees
   stables : elle interroge directement les BioSamples indexes par
   leur `geo_loc_name`, sans passer par BioProject ou PubMed. Pour
   « Lebanon » : 88 hits immediatement, sans cascade. Pour des zones
   ambigues (« Sahel », « Levant », « Maghreb »), revenir aux strategies
   1-4 ci-dessous car ces termes ne matcheront pas un champ
   `geo_loc_name` standard.

   Apres esearch BioSample, pour chaque BioSample ID :
   - `efetch` le XML pour extraire `geo_loc_name`, `collection_date`,
     `lat_lon`, `host`, `isolation_source`, `strain`, `genotype`.
   - `elink` BioSample -> SRA puis `esummary` pour resoudre le
     **Run accession** (SRR/ERR/DRR) -- **et non** le Sample accession
     (SRS/ERS) qui apparait dans `<Id db="SRA">`. Les indexes locaux
     type `rangement.pkl` indexent les Runs, pas les Samples.

   ```bash
   # BioSample ID -> Run accession (peut renvoyer plusieurs Runs)
   ssh_uids=$(curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=biosample&db=sra&id=$BSID" \
              | grep -oP '(?<=<Link><Id>)\d+(?=</Id></Link>)')
   for uid in $ssh_uids; do
       curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=sra&id=$uid" \
           | grep -oE 'Run acc="[A-Z]+[0-9]+"'
   done
   ```

1. **Recherche BioProject via NCBI Entrez** :

   ```bash
   # Pour chaque terme de recherche de la zone :
   curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=bioproject&term=Mycobacterium+tuberculosis+AND+(Franche-Comte+OR+Besancon+OR+Doubs)&retmax=200"
   ```

   Pour chaque BioProject trouve, recuperer les SRA enfants :

   ```bash
   curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=bioproject&db=sra&id=PRJNA12345"
   ```

2. **Recherche PubMed** :

   ```bash
   curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=tuberculosis+AND+(Franche-Comte+OR+Besancon)&retmax=100"
   ```

   Pour chaque PMID, ELink vers SRA :

   ```bash
   curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&db=sra&id=12345678"
   ```

3. **Recherche Europe PMC** (full-text search, utile pour trouver les
   SRAs mentionnes explicitement dans un article) :

   ```bash
   curl -s "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=tuberculosis+AND+Franche-Comte&format=json&resultType=lite&pageSize=100"
   ```

   Pour les articles pertinents, recuperer le texte integral via
   `fullTextXML` et grepper `[DES]RR\d+` pour trouver les accessions
   citees.

4. **TBannotator local** (si disponible) : filtrer la BDD locale par
   lignee/pays si la zone est un pays et le champ geo du `report.json`
   est renseigne. Ce n'est pas un remplacement d'une vraie recherche
   NCBI, juste un raccourci pour les cas simples.

5. **Deduplication** : fusionner les SRAs trouvees par plusieurs
   strategies. Noter pour chaque SRA la source qui l'a produite
   (BioProject / PubMed / Europe PMC / local).

6. **Afficher** le compte intermediaire :

   ```
   Candidats SRA collectes pour "Franche-Comte" :
     via BioProject search : 47
     via PubMed ELink     : 12 (dont 8 nouveaux)
     via Europe PMC       : 23 (dont 15 nouveaux, 8 chevauchent)
     via TBannotator local: 6 (dont 3 nouveaux)
   Total unique : 73

   Proceder a la validation individuelle ? [Phase 3]
   ```

### Mode HYBRID (liste + zone)

Les candidats sont la liste fournie. La Phase 3 produit la location
de chaque SRA ; la Phase 4 applique le filtre zone.

---

## Phase 3 -- Cascade d'extraction de la location

**Pour chaque SRA a traiter**, descendre la cascade suivante et
s'arreter au premier niveau qui produit une location exploitable.
Noter TOUJOURS le niveau atteint (= source) et la confiance.

### Niveau 0 -- Cache

Si le SRA est dans le cache et pas en mode `--force` : retourner
directement l'entree du cache.

### Niveau 1 -- TBannotator (metadata via PostgreSQL `mv_strain_metadata`)

**Important** : le fichier `<bdd>/actuelle/*/<SRA>/NC_000962.3/report.json`
ne contient **PAS** les metadonnees geographiques. Il ne contient que
les annotations bioinformatiques de TBannotator (genes, SNP/SPDI,
qualite de mapping, regions de difference, insertion sequences, etc.).
Ne pas y chercher `geo_loc_name` ni `collection_date` -- ces champs n'y
sont pas.

Les metadonnees NCBI (geo, date, host) sont materialisees dans la vue
PostgreSQL `mv_strain_metadata` cote serveur TBannotator. Y acceder via
le skill `tbannotator-mcp` :

```sql
SELECT sra_id, country, region, city, lat, lon, collection_date, host
FROM mv_strain_metadata
WHERE sra_id = '<SRA>';
```

Scoring (selon contenu de la vue) :
- Pays + ville/region explicite : confiance **5**.
- Pays seul : confiance **4**.
- Coordonnees seules (geocoder inverse via Nominatim) : confiance **4**.
- Tous vides : passer au niveau suivant.

Cette voie est seulement un **cache rapide** des metadonnees BioSample
deja ingerees par le pipeline mp. Pour les SRA recemment deposes (non
encore ingeres -- ex. BioProjects 2024+), le niveau 1 echouera et il
faudra passer directement au niveau 2 (BioSample XML).

> **Source de vérité taxonomique (cf. `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`)** : dans TBannotator, `system_name='guyeux' (ex-'Senelle')` EST le système maison (= moi/Guyeux), mais c'est un **snapshot** susceptible d'être en retard sur la taxonomie vivante. Pour tout clade récent du cycle multi-signal (L1.\*, Bovis1.\*, BCG.\*, L6 profond), recouper le label avec `bdd/actuelle/` + `barcoding_v2/barcode_complete.tsv`. Ne jamais lire `snp_barcoding.csv` (v1 obsolète) ni `strain_lineages.csv` (périmé) comme référence taxonomique.

### Niveau 2 -- BioSample XML via NCBI Entrez

```bash
# SRA → BioSample via ELink
BIOSAMPLE=$(curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=sra&db=biosample&id=SRR12345" | grep -oP '(?<=<Id>)\d+(?=</Id>)' | tail -1)

# BioSample XML
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=biosample&id=$BIOSAMPLE&rettype=xml"
```

Dans le XML, chercher :
- `<Attribute attribute_name="geo_loc_name">...</Attribute>`
- `<Attribute attribute_name="lat_lon">...</Attribute>`
- `<Attribute attribute_name="isolation_source">...</Attribute>`
- `<Attribute attribute_name="host">...</Attribute>` (peut donner un
  indice "human from Besancon")
- `<Attribute attribute_name="collection_date">`

Scoring :
- `geo_loc_name` formatte "Country: Region, City" (standard INSDC) :
  confiance **5**.
- `geo_loc_name` = pays seul : confiance **4**.
- `geo_loc_name` vide mais `lat_lon` present : geocoder inverse via
  Nominatim, confiance **4**.
- `geo_loc_name` texte libre non standard ("Besancon hospital") :
  parser heuristique, confiance **3**.
- Tous absents : passer au niveau suivant.

### Niveau 3 -- BioProject metadata

```bash
# SRA → BioProject via ELink
BIOPROJECT=$(curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=sra&db=bioproject&id=SRR12345" | grep -oP '(?<=<Id>)\d+(?=</Id>)' | tail -1)

# BioProject XML
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=bioproject&id=$BIOPROJECT&rettype=xml"
```

Extraire :
- `<Title>`
- `<Description>` (souvent l'abstract)
- `<Name>`
- Institution soumettant le projet (`<Organization>`, `<Address>`)

Chercher dans ces champs des mentions geographiques. Heuristique :
- Une mention explicite dans le titre ("Tuberculosis in Eastern
  France") : confiance **3**.
- Une mention dans la description/abstract : confiance **3**.
- Rien d'exploitable : passer au niveau suivant.

> [!WARNING]
> **ISOLEMENT vs SÉQUENÇAGE, règle d'or.** Le pays doit etre infere du CONTENU de
> l'etude (titre/abstract = origine des echantillons), JAMAIS de l'INSTITUTION
> soumettrice (`<Organization>` = lieu de SEQUENCAGE). Un centre comme le Wellcome
> Sanger Institute, le Broad, l'Institut Pasteur sequence des souches du monde
> entier : son pays n'est PAS l'origine. Ne jamais deduire la location d'une adresse
> d'institution (sauf en tout dernier recours, confiance **1** explicitement flaggee
> "sequencing_site_guess"). Piege concret : le motif `uk` matche le `.uk` de
> `sanger.ac.uk` dans les URL -> faux "UK" massif. Restreindre les codes pays courts
> hors contexte URL/email. (Cache central MTBC `bioproject_geo/` : `country` y est
> deja basee sur le seul contenu, `org` exclu.)

> [!WARNING]
> **ISOLEMENT vs DÉCLARATION, deuxieme piege, distinct du precedent.** Pour les
> pathogenes "voyageurs", au premier rang *M. canettii*, mais aussi tout cas
> importe, le `geo_loc_name` BioSample (donc confiance 4-5) donne le pays de
> **diagnostic/declaration/residence**, PAS le lieu d'**acquisition**. Cas type :
> les souches de *M. canettii* declarees France (40), Italie (8), UK (5) sont des
> patients/militaires diagnostiques au retour de la **Corne de l'Afrique** (Djibouti),
> ou la bacterie est reellement endemique. Le pays BioSample est ici techniquement
> correct (lieu de prelevement) mais trompeur sur l'origine. NE PAS reecrire
> arbitrairement (non sourcable par souche) : conserver le pays tel quel avec
> `country_source=biosample`, et ajouter une colonne/note `origin_note` portant la
> reserve (ex. `Horn_of_Africa_origin` vs `Djibouti_acquisition`). Reflexe : pour
> toute espece a foyer endemique etroit, comparer la distribution des pays BioSample
> au foyer connu, un exces de pays riches du Nord signale ce biais de declaration.

**Important** : noter la phrase exacte qui a servi a deduire la
location dans le champ `notes` du cache. Si `geo_country` est vide mais
`geo_loc_name` est renseigne (frequent : NCBI remplit souvent l'un sans
l'autre), parser le pays depuis `geo_loc_name` (format INSDC "Country:
region, city" → prendre la partie avant `:`). Filtrer les valeurs
sentinelles `Not available` / `not collected` / `missing` / `uncalculated`
(= vide, pas un pays).

### Niveau 4 -- Publications PubMed liees

```bash
# SRA → PubMed via ELink
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=sra&db=pubmed&id=SRR12345"
```

Pour chaque PMID lie, recuperer l'abstract :

```bash
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=$PMID&rettype=abstract&retmode=text"
```

Chercher dans abstract + title :
- Mention geographique contextuelle a la souche specifique (rare).
- Mention geographique globale de l'etude (frequent) : utiliser comme
  default si rien de mieux.

Scoring :
- Article dedie a une region precise, SRA cite explicitement dans
  l'abstract : confiance **2**.
- Article dedie a une region, SRA inclus dans l'etude sans mention
  specifique : confiance **2**.
- Article multi-pays sans localisation desambiguee : noter "ambigu",
  confiance **1**.

### Niveau 4b -- Supplementary materials (active des que possible)

Les supplementary materials des articles sont souvent la source la
**plus riche** : on y trouve regulierement un tableau (S1, S2...) avec
une ligne par souche, listant l'accession SRA, le pays/region/ville
d'origine, l'annee de collection, le pattern de resistance, etc.
Quand un article lie un SRA, ouvrir son supplementary est presque
toujours payant.

**Quand activer ce niveau** : des qu'au moins un PMID a ete trouve
au niveau 4. Pas besoin de `--deep` pour ce niveau (le `--deep`
sert au texte integral PDF, plus couteux). Activer par defaut, sauf
`--no-supp` pour le desactiver.

**Procedure** :

1. **Identifier les supplementary files** via Europe PMC :

   ```bash
   # Liste des fichiers supplementaires pour un PMCID
   curl -s "https://www.ebi.ac.uk/europepmc/webservices/rest/$PMCID/supplementaryFiles" \
     | jq -r '.supplementaryFiles[]?.url'
   ```

   Sinon, scrapper la page de l'article (section "Supplementary
   information" / "Supporting information") via WebFetch sur l'URL
   PMC (`https://www.ncbi.nlm.nih.gov/pmc/articles/$PMCID/`).

2. **Telecharger** chaque supp file (xlsx, csv, docx, pdf) :

   ```bash
   curl -s -L "$SUPP_URL" -o supp_$PMCID_$N.$EXT
   ```

3. **Parser** selon le type :
   - `.xlsx` / `.xls` : `python -c "import pandas; print(pandas.read_excel(...).to_csv())"` ou via le skill `xlsx`
   - `.csv` / `.tsv` : `Read` direct
   - `.docx` : conversion via `markitdown fichier.docx > fichier.md` (ou pandoc) puis Grep
   - `.pdf` : conversion via le skill `read-scientific-pdf` (OCR Mistral si le PDF est scanne) puis Grep

4. **Chercher** l'accession SRA dans toutes les feuilles/tables :

   ```bash
   grep -E "(SRR|ERR|DRR)\d+" extracted_supp.csv
   ```

   Pour chaque hit, extraire la **ligne entiere** et tenter de
   reconnaitre les colonnes :
   - Toute colonne dont l'en-tete contient `country`, `region`,
     `province`, `city`, `location`, `origin`, `geographic` → location.
   - Toute colonne dont l'en-tete contient `year`, `date`,
     `collection`, `isolation` → date.
   - Toute colonne dont l'en-tete contient `host`, `patient`,
     `subject` → host info (peut renforcer le scoring si elle precise
     "patient from X").

5. **Scoring** :
   - SRA dans un tableau supp avec colonne `country`/`year` claires :
     confiance **4** (souche-specifique, niveau quasi BioSample).
   - SRA dans un tableau supp avec colonne ambigue ("origin" sans
     plus, "isolate name" qui contient une ville en encode) :
     confiance **3**.
   - SRA cite dans le texte d'un supplementary (Methods.docx) sans
     tableau structure : confiance **2**.

6. **Comparaison automatique** avec les niveaux precedents :
   - Supp dit "Mali, 2010" mais BioSample disait "Senegal" : flag
     **conflit critique**. Privilegier la source la plus
     souche-specifique (supp > BioProject).
   - Supp dit "Mali, 2010" et BioSample disait "Mali" sans annee :
     **enrichissement** confirme. Mettre a jour `collection_date`
     avec confiance 4.

7. **Cache** : conserver les supp telecharges dans
   `~/.cache/codex/sra-geolocate/supp/$PMCID/` pour eviter les
   re-telechargements. Conserver l'URL d'origine dans le fichier
   `provenance.json` du dossier.

### Niveau 5 -- Texte integral PDF (--deep uniquement)

Sans `--deep`, s'arreter au niveau 4.

Avec `--deep` :

1. **Europe PMC full-text XML** (open access) :

   ```bash
   # Recuperer le PMCID d'abord
   curl -s "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:$PMID+AND+SRC:MED&format=json" | jq -r '.resultList.result[0].pmcid'
   # Puis le full text XML
   curl -s "https://www.ebi.ac.uk/europepmc/webservices/rest/$PMCID/fullTextXML"
   ```

2. **Unpaywall** (pour les PDFs open access non-PMC) :

   ```bash
   curl -s "https://api.unpaywall.org/v2/$DOI?email=christophe.guyeux@univ-fcomte.fr" | jq -r '.best_oa_location.url_for_pdf'
   ```

3. **Lecture du PDF** : telecharger, convertir via le skill `read-scientific-pdf`
   skill (uvx markitdown) ou `pdftotext`, puis `Grep` l'accession SRA
   dans le texte. Extraire le contexte (+/- 500 chars autour de la
   mention).

4. **Inference contextuelle** : dans ces 1000 chars, chercher :
   - Noms de villes, regions, pays proches de l'accession
   - Tables de metadonnees (souvent un tableau par souche avec pays
     et annee)
   - Supplementary data mentionnees → si possible suivre le lien

Scoring :
- SRA cite explicitement dans un tableau de metadonnees avec
  location : confiance **3** (surpasse le niveau 4, car specifique a
  la souche).
- SRA cite dans une phrase avec une location proche : confiance **2**.
- SRA cite sans contexte clair : confiance **1**.

### Niveau 6 -- Rien trouve

Aucune source n'a produit de location exploitable. Confiance **0**.
`location_text` = "unknown". Noter dans `notes` les sources
consultees.

---

## Phase 3bis -- Cascade de la date de collection

La date de collection (`collection_date`) merite la **meme rigueur** que
la location. Une date NCBI peut etre la date de submission, la date de
sequencage, ou la date reelle de collection -- trois choses
differentes. La cascade ci-dessous est paralllele a la cascade location
et utilise les memes sources, mais avec son propre scoring.

**Principe** : on cherche en priorite la **date d'isolation**
(prelevement du patient/echantillon), pas la date de submission NCBI ni
la date de publication de l'article. Quand seule la date de
publication est disponible, on l'utilise comme borne superieure avec
confiance reduite.

### Niveau D1 -- Cache

Si `date_text` est dans le cache et pas en mode `--force` : retourner
l'entree.

### Niveau D2 -- BioSample (`collection_date`)

Champ `<Attribute attribute_name="collection_date">` du XML BioSample.
Scoring :

- Date ISO 8601 complete (`2014-03-15`) : confiance **5**.
- Annee + mois (`2014-03`) : confiance **5**.
- Annee seule (`2014`) : confiance **4**.
- Plage d'annees (`2010/2014`) : confiance **3**, retenir la mediane,
  noter la plage dans `notes`.
- `not collected` / `missing` / vide : passer au niveau suivant.
- Date manifestement aberrante (avant 1950, apres l'annee courante) :
  flag anomalie, confiance **1**, passer au niveau suivant pour
  cross-check.

**Important** : si la date BioSample est tres proche de la date de
submission NCBI (`ncbi_release_date`), c'est suspect (la valeur a
peut-etre ete inferee par defaut). Verifier si la cascade
plus profonde donne une date plus ancienne et plus credible.

### Niveau D3 -- BioProject

- `<SubmissionDate>` du BioProject : c'est une **borne superieure**,
  pas la date de collection. Utiliser comme fallback avec confiance
  **2** uniquement si tout le reste echoue.
- Mention explicite d'une periode dans le titre/abstract ("samples
  collected between 2008 and 2012") : confiance **3**, retenir la
  mediane de la plage.

### Niveau D4 -- Publications PubMed liees

Dans les abstracts + Methods (via Europe PMC full-text si disponible)
chercher :

- Phrases du type "between 2010 and 2014", "during 2015", "from
  January to December 2018" → extraire la plage, retenir la mediane,
  confiance **3**.
- Date de **publication** de l'article : borne superieure
  (`PubDate`). Confiance **1**, juste pour avoir un majorant si rien
  de mieux.

### Niveau D4b -- Supplementary materials

Souvent une colonne "Year" ou "Collection date" dans le tableau S1
par souche. Si le SRA y figure : extraire la date, confiance **4**
(souche-specifique, fiable). Pour les details, voir le niveau 4b
location (la procedure est identique, seule l'en-tete de colonne
recherchee change).

### Niveau D5 -- Texte integral PDF (--deep)

Comme pour la location, parser le PDF et chercher des dates pres de
la mention du SRA. Confiance **2** au maximum (mention dans le texte,
pas dans un tableau structure).

### Niveau D6 -- Rien

Confiance **0**. `date_text` = "unknown".

### Detection d'anomalies temporelles

Comme pour la location, signaler les contradictions :

- BioSample dit "1995" mais BioProject submission_date est "2010" et
  l'article est de 2012 : possible si la souche a ete deposee plus
  tard, **mais** verifier que ce n'est pas une erreur de saisie
  (frequent : "2015" entre comme "1995").
- BioSample dit "2014-01-01" exactement : valeur defaut typique
  d'un import en masse, flagger.
- Date d'isolation posterieure a la date de publication : impossible,
  flag erreur critique.
- Date d'isolation avant 1950 : extremement rare (sauf souches
  historiques explicitement datees), flag.

### Champs ajoutes au cache et au CSV de sortie

```
date_text       : "2014-03-15" (chaine brute conservee)
date_year       : 2014 (annee canonique pour les analyses)
date_range_min  : 2014 (si plage : borne basse)
date_range_max  : 2014 (si plage : borne haute)
date_confidence : 5
date_source     : biosample
date_evidence   : "BioSample collection_date attribute: 2014-03-15"
date_anomalies  : "" (ou texte decrivant le conflit detecte)
```

---

## Phase 4 -- Matching zone (si `--zone` specifiee)

Pour chaque SRA avec une location extraite, decider si elle matche
la zone cible.

### Algorithme

1. **Normaliser** la location extraite : extraire pays, region, ville
   si possible via un parser INSDC ou Nominatim.
2. **Comparer** aux termes de recherche de la zone (Phase 1) :
   - Match exact sur pays si zone est un pays.
   - Match sur region admin si zone est une region.
   - Match sur ville si zone est une ville.
   - Pour une zone supranationale : verifier si le pays est dans la
     liste des membres.
   - Pour une zone coordonnees : calculer la distance haversine, match
     si < rayon.
3. **Attribuer** un statut :
   - `MATCH` : la location est clairement dans la zone.
   - `PARTIAL` : la location est dans le pays parent mais la region
     exacte n'est pas connue ou est differente.
   - `NO_MATCH` : la location est ailleurs.
   - `UNKNOWN` : pas assez d'information pour decider.
4. **Ajuster la confiance** : si le match repose sur une inference
   indirecte (niveau 3-4), baisser d'un cran.

### Exemple

```
SRA       : SRR12345678
Location  : "France: Besancon, Doubs"
Source    : biosample (niveau 2)
Confiance : 5
Zone      : "Franche-Comte"
Match     : MATCH (Besancon ∈ Doubs ∈ Franche-Comte)
```

---

## Phase 5 -- Sortie et cache

### 5a. Mise a jour du cache

Pour chaque SRA traite (meme ceux avec confiance 0), ecrire/mettre a
jour l'entree dans `sra_geo_cache.csv`. Inclure `queried_at` pour
faciliter les re-verifications futures. Ne jamais supprimer une
entree existante -- au plus la mettre a jour.

### 5b. CSV de sortie principal

Ecrire dans `--output` (defaut `sra_geolocate_YYYY-MM-DD.csv`).
**Schema etendu** (avec les colonnes date ajoutees) :

```csv
sra,location_text,country,region,city,lat,lon,loc_confidence,loc_source,loc_evidence,date_text,date_year,date_range_min,date_range_max,date_confidence,date_source,date_evidence,zone_match,anomalies
SRR12345678,"France: Besancon",France,Franche-Comte,Besancon,47.24,6.02,5,biosample,"BioSample geo_loc_name: France: Besancon","2014-03-15",2014,2014,2014,5,biosample,"BioSample collection_date: 2014-03-15",MATCH,""
SRR998723,"Mali: Point G Hospital",Mali,Bamako,Point G Hospital,12.65,-8.00,5,biosample,"BioSample geo_loc_name: Mali: Point G Hospital","2008/2012",2010,2008,2012,3,publication,"PubMed abstract: 'collected between 2008 and 2012'",MATCH,""
ERR9876543,"Alsace (BioProject abstract)",France,Grand Est,,,,3,bioproject,"BioProject PRJEB12345 title: 'Tuberculosis in Alsace'","2019",2019,2019,2019,1,bioproject_submission,"BioProject SubmissionDate (upper bound)",NO_MATCH,"date_inferred_from_submission"
```

Si mode CHECK sans `--zone`, omettre la colonne `zone_match`. Pour
retrocompatibilite, l'ancien nom `confidence` reste accepte en lecture
de cache et mappe vers `loc_confidence` ; `source` mappe vers
`loc_source`. Les nouvelles colonnes date sont vides si le SRA n'a
ete traite que par `--location-only`.

### 5c. Rapport console

```
━━━━ Rapport sra-geolocate ━━━━

Mode      : [check | dataset | hybrid]
Zone      : [texte] (si applicable)
SRAs traitees : N (cache hits : X, requetes : Y)

== LOCATION ==
Distribution par confiance
  5 (explicite)      : A
  4 (metadonnees)    : B
  3 (bioproject/supp): C
  2 (publication)    : D
  1 (deduction pdf)  : E
  0 (inconnue)       : F

Distribution par source
  biosample     : A1
  bioproject    : A2
  pubmed        : A3
  supp_material : A4 (nouveau)
  europepmc_ft  : A5
  tbannotator   : A6
  unknown       : A7

== DATE ==
Distribution par confiance
  5 (ISO complete)    : DA
  4 (annee BioSample) : DB
  3 (plage article)   : DC
  2 (deduction pdf)   : DD
  1 (submission/pub)  : DE
  0 (inconnue)        : DF

Si mode zone :
  MATCH         : M (score moyen : X.X)
  PARTIAL       : P
  NO_MATCH      : N
  UNKNOWN       : U

Fichier de sortie : <path>
Cache mis a jour  : <path>
Anomalies detectees : K total
  - Geographiques : Kg (BioSample vs BioProject contradictoires...)
  - Temporelles   : Kt (date avant 1950, date > date publication...)
  - Enrichissements: Ke (supp materials complete une metadata vide)
```

### 5d. Detection d'anomalies

Signaler tout SRA pour lequel plusieurs sources se contredisent :

- BioSample dit "France" mais BioProject parle d'Inde → anomalie, noter
  dans le rapport.
- TBannotator report.json dit X mais BioSample dit Y → noter, preferer
  la source la plus recente / fiable.
- Coordonnees lat_lon ne correspondent pas a geo_loc_name : flag.

Ces anomalies sont utiles pour le skill `/supp-check` et pour detecter
des erreurs de soumission dans NCBI.

---

## Mode BULK -- consolider une LIGNÉE ENTIÈRE (10k-80k souches)

La cascade per-SRA (Phases 3/3bis) ne passe pas a l'echelle d'une lignee
MTBC complete : L2 (Beijing) ≈ 78 000 souches, L1 ≈ 26 000, Bovis ≈ 15 000.
Impossible de faire une requete `IN (...)` de 38 000 accessions ni 38 000
`efetch`. La methode validee (sessions 2026-05-30/31, projet
`MTBC-constrained-node-dating`) recupere la metadonnee de TOUTE la lignee en
**une requete**, via son marqueur SPDI racine. Coût O(1 requete) par lignee.
C'est ce qui a produit les `consolidated_geo_<clade>.tsv` du cache central.

### Étape 1 : spdi_id du marqueur racine de la lignee

Le marqueur racine est dans le barcode (`global_supplementary/barcoding_v2/barcode_complete.tsv`,
colonne `spdi`/`role` ; `bdd/actuelle` pour la liste ; NE PAS lire `snp_barcoding.csv`
= v1 obsolète). Resoudre son `spdi_id` numerique
et verifier que son `strain_count` ≈ la taille attendue de la lignee :

```sql
SELECT spdi_id, spdi_variant_name, strain_count
FROM mv_spdi_mutations WHERE spdi_variant_position = <pos>
ORDER BY strain_count DESC;
```

Marqueurs de reference : L1 `1754298:A:C` (spdi_id 105696, 26 295), L2
`63145:G:T` (118, 78 405), L3 `207078:G:C` (1338787, 21 953), L5 `1799920:C:A`
(227484, 794), L6 `982362:G:T` (84980, 1726), Bovis `6405:C:T` BoLaCa (154690,
14 939), L7 `1010995:C:T`, L8 `1596:C:T`, L9 `1116599:C:G`, L10 `1065847:A:G`.
Si plusieurs SNP partagent la position, prendre le `strain_count` le plus proche
de la taille de lignee (les homoplasies ont un compte minuscule).

### Étape 2 : metadonnee de toute la lignee en une requete

```sql
SELECT m.strain_name, m.geo_country, m.collection_date_parsed, m.ncbi_bioproject
FROM mv_strain_metadata m
JOIN tb_report_strain_spdi j ON m.strain_id = j.strain_id
WHERE j.spdi_id = <spdi_id>;
```

Lancer via `tbannotator-mcp` avec `compress=true` et un `max_rows` superieur a
la taille de lignee. Au-dela de ~25k lignes le retour **depasse la limite de
tokens et est automatiquement sauve en fichier** `tool-results/...txt`, ce
n'est PAS une erreur, c'est le comportement attendu. Le fichier contient le
`csv_gzip_base64`.

### Étape 3 : decoder le gzip+base64 en Python (local, sans limite de tokens)

```python
import re, base64, gzip
raw = open("tool-results/mcp-...txt").read()
m = re.search(r"csv_gzip_base64'?:\s*'([A-Za-z0-9+/=]+)'", raw)
csv = gzip.decompress(base64.b64decode(m.group(1))).decode()
# parser : strain_name, geo_country, collection_date_parsed, ncbi_bioproject
```

> [!WARNING]
> Ne PAS coller un gzip+base64 long via Write puis le redecoder : le copier-coller
> l'altere (erreur `BadGzipFile: CRC check failed`, vecu en session). Toujours lire
> le `tool-results` directement, ou combiner plusieurs petites lignees en UNE requete
> (`WHERE j.spdi_id IN (...)`) pour forcer la sauvegarde fichier et eviter le b64 inline.

### Étape 4 : filtrer au placement bdd (verite de classification)

La requete par marqueur ramene TOUTES les souches online portant le SNP
(souvent 2x ce que contient le bdd local). Garder **uniquement les souches
reellement classees** dans `bdd/actuelle/<clade>*` (le placement valide par
l'utilisateur fait foi). Le `lineage` fin (sous-lignee) vient du dossier bdd,
la geo/date de la metadonnee. Cas du prefixe Bovis : sous-lignees nommees
`Bovis1*`/`Bovis2*` (glob `Bovis*`, pas `Bovis.*`).

### Étape 5 : sweep des BioProjects nouveaux puis consolidation

```bash
# BioProjects de la lignee absents du master → sweep
python3 sweep_bioprojects.py <nouveaux_bioprojects.txt>   # met a jour bioproject_metadata.tsv
# consolidation per-strain (regles propres, gere le prefixe Bovis)
python3 build_clades.py <clade...>                        # -> consolidated_geo_<clade>.tsv
```

Persister le snapshot metadonnee dans `inputs/<clade>_meta.csv` pour
reproductibilite. `build_clades.py` applique : country = biosample >
bioproject_content(conf>=3, mono) > none ; date = biosample > bioproject_window
> submission_upper > none ; flag `geo_conflict` si biosample ≠ bioproject.

### Garde-fous BULK (non negociables)

- **Verification anti-regression souche par souche.** Avant d'ecraser un
  `consolidated_geo_<clade>.tsv` existant, sauvegarder l'ancien et verifier
  qu'AUCUNE souche localisee dans l'ancien ne devient `none` dans le nouveau
  (`join` sur les deux). En session, 9 Bovis avaient ainsi disparu.
- **Souches du bdd absentes de la requete par marqueur.** Certaines souches
  classees dans le bdd ne portent pas le marqueur racine (placement par
  d'autres SNP, ou homoplasie). Les recuperer par une requete `IN (...)` ciblee
  sur ces seuls accessions (petit nombre) avec `geo_loc_name` en fallback.
- **Identifiants `CUS*` = uploads custom**, absents de `mv_strain_metadata`
  online : aucune metadonnee recuperable par requete, les laisser `none`.
- **Souches recentes** (BioProjects 2024+) parfois pas encore dans la MV : idem.
- **Distinguer localisation et datation dans les taux annonces.** Ne pas
  confondre « X % localise » et « Y % date », bug de README corrige en session
  (un « 83 % localise » etait en fait le taux de datation). La datation est
  souvent bien plus haute que la localisation grace a `submission_upper`.

---

## Consignes generales

### Ce que le skill DOIT faire

- Descendre la cascade dans l'ordre et s'arreter au premier niveau
  productif -- pas de double travail inutile.
- Noter pour chaque resultat la source exacte et un extrait de la
  preuve (champ `evidence`).
- Cacher **toutes** les requetes distantes pour eviter de re-frapper
  NCBI sans necessite.
- Respecter les limites de l'API NCBI (3 req/s sans cle API, 10 req/s
  avec). Batcher les requetes, espacer si volume eleve.
- Gerer les zones non-pays avec autant de soin que les pays (villes,
  regions, supranational, coordonnees).
- Distinguer clairement **confiance** (qualite de la source) et
  **match** (adequation a la zone).

### Ce que le skill NE DOIT PAS faire

- Inventer une location : si rien n'est trouve, confiance 0.
- Promouvoir une deduction indirecte au rang de certitude
  (confiance ≤ 3 pour toute deduction hors BioSample).
- Ecraser une entree de cache sans tracer la modification
  (`queried_at` doit refleter la derniere interrogation).
- Ignorer les anomalies detectees : elles sont le signal fort du skill.
- Hammer l'API NCBI : respecter les rate limits, utiliser le cache.

### Integration avec l'ecosysteme

- **Cache BioProject central** (`mtbc/global_supplementary/bioproject_geo/`) :
  `bioproject_metadata.tsv` (master 1366+), `sweep_bioprojects.py` (fetch+parse
  Entrez, gazetteer pays, `org` exclu), `build_clades.py` (consolidation
  generique per-strain, gere Bovis), `consolidated_geo_<clade>.tsv` (sorties),
  `inputs/<clade>_meta.csv` (snapshots), `README.md` + `DERIVED_MARKERS.md`.
  À consulter/reutiliser AVANT toute geoloc per-SRA de souches MTBC.
- **`tbannotator-mcp`** : requetes PostgreSQL `mv_strain_metadata`,
  `mv_spdi_mutations`, `tb_report_strain_spdi` (jointure marqueur→souches du
  mode BULK).
- **`/tb-cli`** : wrapper existant pour NCBI et PubMed, peut etre
  reutilise a la place de `curl` brut pour les requetes Entrez.
- **`/pubmed-database`** et **`/europe-pmc`** : fournissent les details
  d'API PubMed/PMC.
- **`/read-scientific-pdf`** : conversion PDF vers texte pour le niveau 5 (OCR inclus).
- **`/geo-map`** : peut consommer la sortie pour visualiser la
  distribution geographique de la cohorte.
- **`/phylogeography`** : complement naturel pour analyser la structure
  spatiale d'une cohorte construite ainsi.
- **`/supp-check`** : les anomalies detectees (BioSample vs BioProject
  contradictoires) sont des entrees utiles pour l'alignement des
  supplementary materials.
- **`/cahier-de-labo`** : loguer une entree apres chaque construction
  de dataset significative (nouvelle cohorte, nouvelle zone).

---

## Epilogue -- Resume et suggestion de suite

### Resume de session

Afficher en 5-8 lignes :
- Mode utilise (check / dataset / hybrid)
- Nombre de SRAs traitees / matches trouvees
- Distribution succincte par confiance
- Cache : hit rate, nouvelles entrees
- Anomalies detectees (top 3 si pertinent)
- Fichiers produits

### Suggestion de prochaine etape

**Scenario dataset (cohorte construite)** :

```
━━━━ Prochaine etape suggeree ━━━━

Cohorte "Franche-Comte" construite : N SRAs (M haute confiance, K
moyenne). Je recommande :

  1. Verifier manuellement les K entrees a confiance moyenne
     (fichier : <path>, filtrer confidence <= 3)
  2. /fetch-tbannotator <cohorte.csv>   ← recuperer les reports
     pour les SRAs non encore presentes dans la BDD locale
  3. /geo-map <cohorte.csv>             ← visualiser la distribution
  4. /phylogeography <cohorte.csv>      ← analyser la structure
     spatiale
  5. /cahier-de-labo update             ← journaliser la construction
     de cette cohorte
```

**Scenario check (verification d'une SRA)** :

```
━━━━ Origine de SRR12345678 ━━━━

  Location  : France: Besancon (Franche-Comte, Doubs)
  Coordonn. : 47.24, 6.02
  Source    : biosample (niveau 2)
  Confiance : 5/5 (explicite)
  Evidence  : BioSample attribute "geo_loc_name" = "France: Besancon"
  Cross-check : BioProject PRJEB99999 titre "TB surveillance in
    Eastern France" confirme la zone.
  Anomalies : aucune

Rien de plus a chercher.
```

**Scenario anomalies detectees** :

```
━━━━ Anomalies a arbitrer ━━━━

N SRAs presentent des sources contradictoires :

  1. SRR12345 : BioSample "India" vs BioProject abstract "Mali" vs
     PubMed article "West Africa". Resolution suggeree : lire le
     supplementary de l'article [PMC12345] ou contacter les auteurs.
     Action : /sra-geolocate SRR12345 --deep puis verification
     manuelle.

  2. ERR67890 : lat_lon = 48.8, 2.3 (Paris) vs geo_loc_name
     "Casablanca". L'un des deux est errone. Action : lire le
     BioProject en entier pour comprendre.
```

## Codex packaging note

This packaged copy targets Codex. MCP tool names in `allowed-tools` are prerequisites: verify them with `codex mcp list` in the active profile before relying on live queries.

## Codex cache note

This packaged copy uses `~/.cache/codex/sra-geolocate/` for reusable cache files instead of Claude-specific cache paths.
