---
name: crisprcasdb
description: >-
  Academic research database client (Guyeux group, FEMTO-ST, peer-reviewed
  comparative genomics) for the LOCAL copy of CRISPRCasdb, the PostgreSQL
  database behind CRISPR-Cas++ (I2BC, Universite Paris-Saclay): 36 605 complete
  prokaryote genomes, 143 878 CRISPR arrays, 608 232 spacers, 17 369 cas gene
  clusters, all produced by CRISPRCasFinder. Use when: extracting the spacers or
  direct repeats of a published genome, asking which organisms carry a given
  spacer, comparing CRISPR-Cas system types across taxa, retrieving the DR
  consensus of a lineage, cross-checking an in-silico spoligotype against an
  independent source, or querying CRISPR content for a scientific manuscript.
argument-hint: "<organism, accession, spacer sequence, or SQL question>"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# CRISPRCasdb en local (CRISPR-Cas++, I2BC)

## Ce que c'est

Copie locale et interrogeable de la base PostgreSQL qui alimente le site
[CRISPR-Cas++](https://crisprcas.i2bc.paris-saclay.fr/) (equipe de Christine Pourcel,
I2BC, Universite Paris-Saclay). Contenu produit par **CRISPRCasFinder** sur les genomes
procaryotes complets de GenBank, arrete au **6 avril 2022** (le site lui-meme n'a pas ete
recharge depuis : sa version 2.0.1 de mars 2026 concerne le logiciel, pas les donnees).

Reference a citer : Pourcel C. et al., *CRISPRCasdb a successor of CRISPRdb containing
CRISPR arrays and cas genes from complete genome sequences, and tools to download and query
lists of repeats and spacers*, Nucleic Acids Research 2020, 48(D1):D535-D544.

| | |
|---|---|
| Serveur | conteneur Docker `crisprcasdb`, PostgreSQL 16, `127.0.0.1:5433` |
| Base / utilisateur / mot de passe | `crisprcasdb` / `postgres` / `crispr` |
| Infrastructure et rechargement | `~/docs/codes/mtbc/crisprcasdb_local/` |
| Taille | 635 Mo |
| Souches | 36 605 (36 052 bacteries, 553 archees) |
| Loci CRISPR | 143 878 dont **32 624 en evidence level 4** |
| Spacers / DR distincts | 608 232 / 212 267 |
| Clusters cas | 17 369 |

## Interroger

Le script `scripts/ccdb.py` n'a **aucune dependance Python** (il pilote `psql`) et demarre
le conteneur tout seul s'il est arrete.

```bash
CCDB=~/docs/codes/claude_plugins/bio_pathogens/skills/crisprcasdb/scripts/ccdb.py
$CCDB stats
$CCDB strain H37Rv                                  # nom, GCA/GCF ou accession de replicon
$CCDB arrays GCA_000195955.2                        # loci CRISPR (evidence 4 par defaut)
$CCDB spacers AL123456.3 --format fasta              # spacers dans l'ordre genomique
$CCDB spacers AL123456.3 --with-dr                   # avec les DR intercales
$CCDB whohas --exact TCGGGCACGGCCGAAACACC...         # qui porte ce spacer ?
$CCDB cas GCA_000195955.2                            # systemes cas et genes
$CCDB taxon 77643                                    # tout un clade NCBI (recursif)
$CCDB sql "SELECT ..."                               # SQL libre
```

Options globales : `--format table|tsv|json|fasta`, `--limit N` (100 par defaut),
`--all-levels` (pour `arrays` et `spacers`, leve le filtre evidence 4).

En SQL direct : `PGPASSWORD=crispr psql -h 127.0.0.1 -p 5433 -U postgres -d crisprcasdb`.

## Modele de donnees

Le schema est en heritage : la table `entity` porte l'identite (uuid, `class`, `name`) et
les tables specialisees **partagent le meme uuid**. Le nom lisible d'une souche ou d'un
replicon se lit donc dans `entity`, jamais dans `strain` ni `sequence`.

```
entity (id, class, name)            class = Strain | Sequence | LocusCRISPR | ClusterCAS | Job
  |-- strain (id, genbank, refseq, taxon, assembly_status)   name = organisme
  |     `-- sequence (id, strain, category, length, description)  name = accession (AL123456.3)
  |           |-- crisprlocus (id, sequence, start, length, orientation,
  |           |                evidencelevel, drconsensus -> region, drconservation)
  |           |     `-- crisprlocus_region (crisprlocus, region, start, length)
  |           |           `-- region (id, sequence, category)      les sequences ADN
  |           `-- clustercas (id, sequence, start, length, class)
  |                 `-- clustercas_gene (clustercas, gene, start, orientation)
  `-- taxon (id, parent, scientificname, rank)                arbre NCBI, recursif
```

`crisprcasdb` est une table **denormalisee, une ligne par souche** (`id` = celui de la
souche), avec `name`, `cas_type`, `cas_gene`, `crispr_all_sum`, `crispr4_all_sum`,
`superkingdom` et `lineage_taxon`. C'est le point d'entree le plus rapide pour un comptage
ou un filtre par clade, sans jointure.

### Vocabulaires controles (verifies sur la base, 2026-08-03)

| Champ | Valeurs |
|---|---|
| `region.category` | **1 = DR** (30 nt en moyenne), **3 = spacer** (35 nt), **5 = leader** (flanc gauche, 100 nt), **6 = trailer** (flanc droit) |
| `crisprlocus.evidencelevel` | 1 (106 716 loci), 2 (3 786), 3 (752), **4 (32 624)**. La colonne `trusted` est `false` partout : elle n'est pas exploitable. |
| `crisprlocus.orientation` | 1 = brin +, 2 = brin -, **3 = indeterminee (107 166 loci, soit 74 %)** |
| `sequence.category` | 1 = chromosome, 2 = plasmide ou replicon secondaire |
| `clustercas.class` | `CAS-TypeI-E` (5 981), `CAS-TypeII-C`, `CAS-TypeI-C`, `CAS-TypeIII-A` (1 124)... |
| `crisprlocus.evidencelevelreeval` | vide (137 932), `perfect_match` (4 031), `blast_score_sup_threshold` (1 915) |

## Garde-fous

**1. Filtrer sur `evidencelevel = 4`, toujours.** Les niveaux 1 a 3 sont majoritairement des
faux positifs, en particulier chez les genomes riches en GC. H37Rv illustre le probleme :
CRISPRCasFinder y annonce 9 loci, dont **7 sont du bruit** et 2 seulement sont le vrai
locus DR. Le script filtre par defaut ; `--all-levels` leve le filtre quand on veut voir
le bruit.

**Le bruit prend DEUX formes distinctes, et la seconde trompe** (verifie 2026-08-03) :

| forme | niveau | n spacers | `drconservation` | exemple H37Rv |
|---|---|---|---|---|
| locus trop court | 1 | **1** | 67-100 % (trivial : 2 DR identiques) | 692025, 1191316, 2168814, 4110678 |
| **repetitions mal conservees** | 2 | **10 a 16** | **18-29 %** | 366463 (PPE5), 1211950 (PE-PGRS21), 1572185 (PE-PGRS25) |
| vrai locus DR | 4 | 17 et 23 | **90-97 %** | 3119185, 3121862 |

La seconde forme est piegeuse : avec 10 a 16 spacers annonces, elle **ressemble a un vrai
array** et a deja ete prise pour des « archeo-CRISPR » ancestraux dans un projet du groupe.
Le discriminant n'est pas le nombre de spacers mais **`drconservation`** : un CRISPR est par
definition fait de repetitions, donc des DR a 18-28 % d'identite ne sont pas des DR. Ces
faux positifs tombent sur les familles **PE-PGRS** (repetitions en tandem Gly-Ala) et **PPE**.

**Calibration a connaitre** : `drconservation` moyenne par niveau sur toute la base : ev1
93,3 % (biaisee, loci a 1 spacer), ev2 **41,6 %** (mediane 43,1, max 70), ev3 85,2 %,
ev4 93,1 % (mediane 95,5). Le niveau 2 EST la classe des repetitions mal conservees. Et
chez les *Mycobacterium*, les loci du type « ev<=2, >=8 spacers, conservation <35 % » sont
**1 243, contre 1 091 vrais loci ev4** : ce bruit est plus frequent que le signal, il n'a
donc rien de remarquable sur un genome donne.

**Regle** : avant de faire d'un locus non-ev4 un objet d'etude, lire `drconservation`. En
dessous de ~70 %, ce ne sont pas des repetitions.

**2. Les sequences sont stockees sur le brin + du genome, pas dans le sens de la
nomenclature publiee.** Verifie sur H37Rv contre les 43 spacers historiques du spoligotypage
(Kamerbeek) : **35 des 36 spacers retrouves ne matchent qu'en complement inverse**, un seul
en sens direct. Toute comparaison avec un catalogue externe doit tester les deux sens.
Ne pas se fier a `orientation` pour trancher : elle vaut 3 (indeterminee) dans 74 % des cas,
et pour le locus DR de H37Rv elle vaut 2 alors que le DR consensus stocke est deja dans la
forme publiee.

**3. Filtrer un clade par taxid, jamais par nom.** `WHERE name ~* 'bovis|microti'` ramene
936 souches, dont **175 hors MTBC** (*Streptococcus bovis* et consorts). Le compte correct
du MTBC est **587 souches**, obtenu soit par `lineage_taxon LIKE '%#77643#%'`, soit par la
descente recursive de `taxon` (sous-commande `taxon 77643`). `lineage_taxon` est une chaine
de taxids encadres de `#`, du plus specifique a la racine.

**4. 6 689 noms d'organismes contiennent des retours a la ligne** herites de GenBank
(`Mycobacterium tuberculosis (high GC Gram+)\n 060827`). En sortie TSV, ils coupent
silencieusement un enregistrement en deux. `ccdb.py` transporte tout en JSON pour cette
raison ; en SQL direct, penser a `regexp_replace(name, '\s+', ' ', 'g')`.

**5. `strain.genbank` est une accession d'assemblage** (`GCA_000195955.2`), pas une accession
de sequence. L'accession du replicon (`AL123456.3`, `CP063804.1`) est dans
`entity.name` de la ligne `sequence` correspondante.

**6. Le total affiche par le site (72 104 bacteries) contredit sa propre ventilation**
(20 950 + 1 812 + 944 + 12 346 = 36 052, exactement notre base). C'est un artefact
d'affichage du site, pas un dump incomplet : la ventilation de `crisprcas_stats` correspond
chiffre pour chiffre a la page publique.

## Recettes

Spacers d'un genome, dans l'ordre, avec leur rang :

```sql
SELECT row_number() OVER (PARTITION BY cl.id ORDER BY lr.start) AS rang,
       lr.start, r.category, r.sequence
FROM crisprlocus cl
JOIN crisprlocus_region lr ON lr.crisprlocus = cl.id
JOIN region r ON r.id = lr.region
JOIN sequence sq ON sq.id = cl.sequence
JOIN entity es ON es.id = sq.id
WHERE es.name = 'AL123456.3' AND cl.evidencelevel = 4 AND r.category = 3
ORDER BY cl.start, lr.start;
```

Spacers partages entre deux genomes (mesure de proximite CRISPR) :

```sql
WITH a AS (SELECT DISTINCT r.sequence FROM ... WHERE es.name = 'AL123456.3' ...),
     b AS (SELECT DISTINCT r.sequence FROM ... WHERE es.name = 'CP063804.1' ...)
SELECT (SELECT count(*) FROM a) AS n_a, (SELECT count(*) FROM b) AS n_b,
       (SELECT count(*) FROM a JOIN b USING (sequence)) AS partages;
```

Spacers les plus repandus (candidats a une origine mobile largement diffusee) :

```sql
SELECT r.sequence, count(DISTINCT sq.strain) AS n_souches
FROM region r JOIN crisprlocus_region lr ON lr.region = r.id
JOIN crisprlocus cl ON cl.id = lr.crisprlocus AND cl.evidencelevel = 4
JOIN sequence sq ON sq.id = cl.sequence
WHERE r.category = 3
GROUP BY 1 ORDER BY 2 DESC LIMIT 20;
```

Repartition des types de systemes cas dans un clade :

```sql
SELECT d.cas_type, count(*) FROM crisprcasdb d
WHERE d.lineage_taxon LIKE '%#77643#%' GROUP BY 1 ORDER BY 2 DESC;
```

## Ce que la base dit du MTBC

Faits verifies sur la copie locale, utiles comme point de depart et comme controle
independant du pipeline maison :

- **587 souches MTBC** (taxid 77643), dont 576 en `TypeIII-A`. Le systeme III-A est donc
  quasi invariant dans le complexe.
- **H37Rv (GCA_000195955.2, AL123456.3)** : locus DR coupe en **deux blocs**, 3 119 185 a
  3 120 468 (17 spacers) et 3 121 862 a 3 123 576 (23 spacers). L'intervalle vide de
  ~1 394 pb entre les deux correspond a la taille d'IS6110 : c'est l'insertion bien connue
  qui scinde le locus DR, et elle explique que CRISPRCasFinder rende deux loci et non un.
  DR consensus : `GTTTCCGTCCCCTCTCGGGGTTTTGGGTCTGACGAC` (36 pb, forme publiee).
- Les 40 spacers ainsi extraits reproduisent **exactement le spoligotype connu de H37Rv** :
  absents = spacers **20, 21, 25, 33, 34, 35, 36**, ce dernier bloc 33-36 etant la signature
  Euro-American. C'est une validation croisee de la base et une source independante de
  spoligotype in silico pour les genomes complets.
- Le cluster cas de H37Rv (3 123 625, 8 933 pb) contient **Cas1, Cas2, Csm6, Csm5, Csm4,
  Csm3, Csm2, Cas10, Cas6**. Confirmation independante que Cas1 et Cas2 sont bien presents
  chez H37Rv, contrairement a l'affirmation repandue de leur absence.
- ***M. canettii* est heterogene** : sur 27 souches, 17 en `TypeIII-A` mais **10 portent des
  systemes de type I** (`TypeI-G`, `TypeI-E`, `TypeI-C`) **sans aucun III-A**. A confronter a
  Singh 2021 (mSystems), qui place l'acquisition du III-A chez l'ancetre commun du MTBC et
  de *M. canettii*.

## Entretien

```bash
~/docs/codes/mtbc/crisprcasdb_local/bin/ccdb_service.sh {start|stop|status|psql|backup}
```

Le dump amont ne livre que les cles primaires : les index de jointure et les index trigramme
ont ete ajoutes en local (`crisprcasdb_local/sql/indexes.sql`). Apres tout rechargement
depuis un dump neuf, relancer `ccdb_service.sh reindex`, sinon chaque jointure part en
parcours sequentiel sur les 1,9 million de lignes de `crisprlocus_region`.

Le dump public reste telechargeable a
`https://crisprcas.i2bc.paris-saclay.fr/Home/DownloadFile?filename=ccpp_db.zip` (103 Mo,
372 Mo decompresses). Les listes brutes de spacers et de DR au format FASTA sont proposees
separement (`spacer_34.zip`, `dr_34.zip`) : plus pratiques pour un BLAST massif, mais sans
le rattachement aux souches ni aux loci, que seule la base fournit.

## Voisinage

`spdi-annotation` et `tbannotator-mcp` pour les variants et les souches MTBC ;
`sitvitweb` et `mbovis` pour les spoligotypes de reference (SIT, SB) ;
`spoligo_clock` (projet) pour l'usage du spoligotype comme horloge moleculaire.
La base repond a une question qu'aucun de ces outils ne couvre : le contenu CRISPR
**hors MTBC**, sur 7 549 especes bacteriennes et 274 especes d'archees (comptees sur les
taxids de rang `species` effectivement rattaches a une souche).
