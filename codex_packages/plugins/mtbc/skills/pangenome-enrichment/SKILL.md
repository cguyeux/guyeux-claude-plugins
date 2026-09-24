---

name: pangenome-enrichment
description: >-
  Pangenome analysis and functional enrichment by MTBC lineage.
  Core/soft-core/shell/cloud gene classification, KEGG pathway enrichment,
  lineage-specific gene content analysis.

  Use when: comparing gene content between lineages, identifying lineage-specific
  genes, performing KEGG enrichment on differential genes, analyzing pangenome
  structure for an article.

  Scope: developed on the MTBC, applies to any clonal bacterial pathogen
  (Yersinia, Leptospira...) — core/shell/cloud classification and KEGG enrichment
  are genus-agnostic, and matter MORE outside the MTBC (plasmids, larger
  accessory genome). Outside the MTBC: supply the gene presence/absence matrix
  (Roary, Panaroo) and the genus KEGG organism code.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres
---

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


# Pangenome Enrichment : Analyse du pangénome MTBC

Classification des gènes en core/soft-core/shell/cloud par lignée MTBC, enrichissement fonctionnel KEGG, et comparaison du contenu génique entre lignées.

## Concepts

### Classification des gènes

| Catégorie | Définition | Seuil | Interprétation MTBC |
|-----------|-----------|-------|---------------------|
| **Core** | Présent dans ≥99% des souches | ≥0.99 | Gènes essentiels, conservés |
| **Soft-core** | Présent dans 95-99% | 0.95-0.99 | Quasi-universels, quelques pertes |
| **Shell** | Présent dans 15-95% | 0.15-0.95 | Variables, souvent lignée-spécifiques |
| **Cloud** | Présent dans <15% | <0.15 | Rares, souvent acquis ou artefacts |

### MTBC vs autres bactéries

Le MTBC a un pangénome très fermé (peu de transfert horizontal). Les variations de contenu génique sont principalement dues à :
- **Régions de délétion (RD)** : grandes délétions lignée-spécifiques
- **Frameshifts** : pseudogénisation par mutations décalantes
- **PE/PPE** : famille très variable en nombre de copies et intégrité

## Phase 1 : Découverte (OBLIGATOIRE)

1. **Quelles lignées comparer ?**
   - Humaines vs animales
   - Sous-lignées d'une lignée majeure (ex. L4.15 vs L4.14)
   - Toutes les lignées majeures (vue d'ensemble)

2. **Source des données ?**
   - Matrice de gènes (CSV : strain_id × gene → 0/1)
   - Données SPDI depuis TBannotator (frameshifts, stop gains)
   - Régions de délétion (RD) depuis la littérature

3. **Type d'enrichissement ?**
   - **KEGG pathways** : voies métaboliques sur/sous-représentées
   - **Gene families** : PE/PPE, ESX, mce, lipid metabolism
   - **COG categories** : catégories fonctionnelles
   - Combinaison

## Phase 2 : Extraction des données

> **Source de vérité (cf. `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`)** : dans TBannotator, `system_name='guyeux'` EST le système maison (= moi/Guyeux), mais c'est un **snapshot** susceptible d'être en retard sur la taxonomie vivante. Pour tout clade récent du cycle multi-signal (L1.\*, Bovis1.\*, BCG.\*, L6 profond), recouper le label avec `bdd/actuelle/` + `barcoding_v2/barcode_complete.tsv`. Ne jamais lire `snp_barcoding.csv` (v1 obsolète) ni `strain_lineages.csv` (périmé) comme référence taxonomique.

### Gènes altérés (frameshifts/stops) par lignée depuis TBannotator

> ⚠ **`mv_protein_position_mutations` n'est PAS peuplée** côté serveur (vérifié 2026-07-31) et elle est
> agrégée (pas de `strain_id`). Route valide : `tb_report_spdi_annotations` → `tb_report_spdi` →
> `tb_report_strain_spdi`. Colonnes réelles : `locus_tag` (Rv####), `annotation_type`
> (`frameshift_variant`, `stop_gained`, `missense_variant`…), `impact` (LOW/MODERATE/HIGH), `hgvs_p`.
> **Alternative bien plus rapide pour la perte de gène** : `tb_report_strain_missing_gene`
> (souche × gène absent, 17,4M lignes, indexée), c'est la vraie table de délétion.

```sql
-- Gènes disruptés (frameshift/stop) par lignée
-- Coût élevé : restreindre par lignée ou par liste de locus_tag.
SELECT a.locus_tag, a.annotation_type, c.lineage_code,
       COUNT(DISTINCT ss.strain_id) AS n_strains
FROM tb_report_spdi_annotations a
JOIN tb_report_spdi s           ON s.spdi_variant_name = a.spdi_variant_name
JOIN tb_report_strain_spdi ss   ON ss.spdi_id = s.spdi_id
JOIN mv_strain_classification c ON c.strain_id = ss.strain_id
WHERE c.system_name = 'guyeux'
  AND c.lineage_code LIKE '4.15%'                       -- filtrer !
  AND a.annotation_type IN ('frameshift_variant', 'stop_gained')
GROUP BY a.locus_tag, a.annotation_type, c.lineage_code
HAVING COUNT(DISTINCT ss.strain_id) >= 10
ORDER BY n_strains DESC;
```

### Gènes absents (délétion) par lignée : route rapide

```sql
-- Proportion de souches d'une lignée où le gène est ABSENT (délétion réelle, pas disruption ponctuelle)
SELECT g.locus_tag,
       c.lineage_code,
       COUNT(DISTINCT mg.strain_id) AS n_missing,
       ROUND(100.0 * COUNT(DISTINCT mg.strain_id) /
         NULLIF((SELECT COUNT(DISTINCT strain_id) FROM mv_strain_classification
                 WHERE system_name = 'guyeux' AND lineage_code = c.lineage_code), 0), 2) AS pct
FROM tb_report_strain_missing_gene mg
JOIN tb_report_gene g           ON g.gene_id = mg.gene_id
JOIN mv_strain_classification c ON c.strain_id = mg.strain_id
WHERE c.system_name = 'guyeux' AND c.lineage_code LIKE '4.15%'
GROUP BY g.locus_tag, c.lineage_code
ORDER BY n_missing DESC
LIMIT 50;
```

### Diversité fonctionnelle par gène

> ⚠ **`mv_protein_effect_diversity` n'est PAS peuplée** côté serveur (vérifié 2026-07-31) : la requête
> échoue (`has not been populated`). Si l'équipe TBannotator la rafraîchit, ses colonnes réelles sont
> `locus_tag`, `annotation_type`, `mutation_count`, `total_strains`, `shannon_diversity`,
> `simpson_diversity` (**pas** `gene`, ni `n_variants`, ni `n_strains`). En attendant, calculer la
> diversité soi-même depuis les tables.

```sql
-- Diversité des mutations par gène, calculée depuis les tables (route qui fonctionne)
-- Coût élevé : restreindre la liste de locus_tag.
SELECT a.locus_tag,
       COUNT(DISTINCT a.hgvs_p)        AS n_distinct_mutations,
       COUNT(DISTINCT ss.strain_id)    AS n_strains
FROM tb_report_spdi_annotations a
JOIN tb_report_spdi s         ON s.spdi_variant_name = a.spdi_variant_name
JOIN tb_report_strain_spdi ss ON ss.spdi_id = s.spdi_id
WHERE a.locus_tag IN ('Rv1908c', 'Rv0667')
  AND a.annotation_type = 'missense_variant'
GROUP BY a.locus_tag
ORDER BY n_distinct_mutations DESC;
```

## Phase 3 : Classification pangenome

### D'où vient `gene_presence.csv` (entrée obligatoire)

Le script attend une matrice **souche × gène** à valeurs 0/1, une ligne par
souche, plus une colonne de groupe (`lineage`). Ce fichier n'existe pas dans la
base : il faut le construire, et de quelle façon on le construit change le
résultat. Deux routes, qui ne mesurent pas la même chose.

**Route A : pangénome calculé depuis les annotations (la vraie route).**
Annoter les génomes avec Prokka ou Bakta, puis grouper les gènes en familles
orthologues :

```bash
# Panaroo, plus strict sur les erreurs d'annotation, recommandé pour MTBC
panaroo -i annotations/*.gff -o panaroo_out --clean-mode strict -t 8
# -> panaroo_out/gene_presence_absence.Rtab : matrice gène × souche, 0/1

# Alternative : PPanGGOLiN, plus rapide sur des milliers de génomes,
# et qui produit directement sa propre partition persistent/shell/cloud
ppanggolin workflow --anno annotations.list -o ppanggolin_out
```

La matrice de Panaroo est **transposée** par rapport à ce qu'attend le script
(gènes en lignes) et n'a pas de colonne de lignée :

```python
import pandas as pd

rtab = pd.read_csv("panaroo_out/gene_presence_absence.Rtab", sep="\t", index_col=0)
mat = rtab.T                                   # souches en lignes
mat.index.name = "strain_id"
lineages = pd.read_csv("lineages.tsv", sep="\t", index_col="strain_id")["lineage"]
mat.insert(0, "lineage", lineages.reindex(mat.index))
mat.dropna(subset=["lineage"]).to_csv("gene_presence.csv")
```

Note sur PPanGGOLiN : sa partition `persistent / shell / cloud` est estimée par
un modèle statistique, pas par les seuils de fréquence de ce skill. Ne pas
mélanger les deux nomenclatures dans un même tableau.

**Route B : présence fonctionnelle dérivée de TBannotator (le raccourci).**
Partir de H37Rv et marquer 0 les gènes pseudogénisés (frameshift, stop gagné) ou
supprimés par une RD connue, via les requêtes de la Phase 2.

**Ces deux routes ne mesurent pas la même chose, et les confondre casse
l'interprétation.** La route A mesure la **présence du gène** dans l'assemblage.
La route B mesure l'**intégrité du cadre de lecture** d'un gène qui, physiquement,
est toujours là. Un gène pseudogénisé dans toute une lignée est absent au sens B
et présent au sens A. Concrètement :

- Si le fichier vient de la route B, ne pas l'appeler un pangénome : c'est une
  matrice de pseudogénisation. Les catégories restent utilisables, mais la
  lecture correcte est « gène fonctionnel dans x % des souches », pas « gène
  présent ».
- Le MTBC ayant un pangénome quasi fermé (transfert horizontal négligeable), la
  route A produit un core énorme et un cloud presque vide : le signal biologique
  intéressant est concentré dans les RD et les familles PE/PPE. C'est justement
  là que la route A est la moins fiable, les PE/PPE étant riches en répétitions
  et donc mal assemblés depuis des lectures courtes.
- Un « gène absent » qui n'apparaît que sur les assemblages à faible couverture
  est un artefact d'assemblage. Contrôler la corrélation entre le nombre de gènes
  absents par souche et sa profondeur de couverture avant toute conclusion : une
  corrélation nette invalide l'analyse, et `strain-qc` sert à filtrer en amont.
- Ne jamais mélanger dans une même matrice des génomes assemblés de novo et des
  génomes mappés sur H37Rv.

### Script

```bash
python3 scripts/pangenome_enrichment.py gene_presence.csv \
  --group-column lineage --thresholds 0.99,0.95,0.15 \
  -o pangenome_classification.csv --summary
```

### Algorithme

Pour chaque gène et chaque groupe :
1. Calculer la fréquence (proportion de souches ayant le gène fonctionnel)
2. Classifier selon les seuils : core ≥ 99%, soft-core 95-99%, shell 15-95%, cloud < 15%
3. Identifier les gènes **différentiellement présents** entre groupes (Fisher exact)

## Phase 4 : Enrichissement KEGG

### API KEGG

```
GET https://rest.kegg.jp/link/pathway/mtu:{gene_name}
GET https://rest.kegg.jp/get/pathway:mtu00010
```

**Important** : respecter le rate limiting (0.5s entre requêtes). Utiliser un cache local.

### Test d'enrichissement

Pour chaque pathway KEGG :

| | Dans le set différentiel | Hors du set |
|---|---|---|
| Dans le pathway | a | b |
| Hors du pathway | c | d |

Test de Fisher exact. Correction FDR Benjamini-Hochberg sur l'ensemble des pathways testés.

### Pathways MTBC d'intérêt

| Pathway | ID KEGG | Pertinence MTBC |
|---------|---------|-----------------|
| Fatty acid metabolism | mtu00071 | Lipides de paroi, virulence |
| Biosynthesis of PDIM/PGL |, | Virulence, spécifique mycobactéries |
| Two-component systems | mtu02020 | Régulation adaptation environnement |
| ABC transporters | mtu02010 | Import/export, résistance |
| Beta-oxidation | mtu00071 | Source de carbone in vivo |
| Amino acid metabolism | mtu00250-00350 | Auxotrophies lignée-spécifiques |

## Phase 5 : Sortie

### CSV de classification

```csv
gene,overall_category,freq_L4.15,cat_L4.15,freq_L4.14,cat_L4.14,freq_M.bovis,cat_M.bovis,differential,p_value,p_adjusted
Rv0001,core,1.0,core,1.0,core,1.0,core,no,,
PE35,shell,0.85,shell,0.92,shell,0.45,shell,yes,0.001,0.01
pncA,soft-core,0.98,soft-core,0.97,soft-core,0.12,cloud,yes,<0.001,<0.001
```

### Résumé JSON

```json
{
  "n_genes": 4000,
  "pangenome_by_group": {
    "L4.15": {"core": 3650, "soft_core": 120, "shell": 180, "cloud": 50},
    "M.bovis": {"core": 3580, "soft_core": 100, "shell": 220, "cloud": 100}
  },
  "n_differential": 85,
  "kegg_enrichment": {
    "mtu00071": {"name": "Fatty acid degradation", "p_adjusted": 0.003, "genes": 8},
    "mtu02020": {"name": "Two-component system", "p_adjusted": 0.01, "genes": 5}
  }
}
```

### Figure : heatmap du pangénome

Matrice gènes différentiels (lignes) × lignées (colonnes), colorée par fréquence (0-1). Annoté par :
- Catégorie fonctionnelle (COG) en marge gauche
- Pathway KEGG enrichi en marge droite
- Dendrogramme de clustering sur les lignes

## Régions de délétion (RD) connues

| RD | Lignées | Gènes affectés | Impact |
|----|---------|-----------------|--------|
| RD1 | M. bovis BCG | esxA, esxB | Perte de virulence (BCG) |
| RD4 | M. bovis | Rv1508-1514 | Marqueur M. bovis |
| RD7 | L5, L6 | Rv1572-1587 | Marqueur M. africanum |
| RD9 | L5, L6, animales | Rv2073-2083 | Marqueur grand clade |
| RD10 | M. bovis, M. caprae | Rv3478-3487 | Spécifique animal clade 1 |
| RD12 | M. canettii absent |, | Marqueur MTBC vs canettii |
| TbD1 | L2, L3, L4 | mmpS6, mmpL6 | "Modern" lineages |

## Intégration

| Skill | Usage |
|-------|-------|
| `tbannotator-mcp` | Source des mutations, classifications |
| `convergent-evolution` | Identifier la convergence dans les gènes du pangénome |
| `lineage-comparison` | Tests statistiques pour les gènes différentiels |
| `sci-figure` | Heatmaps et figures personnalisées |

## Dépendances

```bash
pip install pandas numpy scipy matplotlib seaborn requests
```

**KEGG API** : pas d'installation, REST pur. Respecter rate limiting 0.5s.

## Codex packaging note

This packaged copy targets Codex. MCP tool names in `allowed-tools` are prerequisites: verify them with `codex mcp list` in the active profile before relying on live queries.
