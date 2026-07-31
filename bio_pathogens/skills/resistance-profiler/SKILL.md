---
name: resistance-profiler
description: >-
  Academic peer-reviewed MTBC research toolkit (Guyeux group, FEMTO-ST):
  antimicrobial-resistance allele frequencies across Mycobacterium
  tuberculosis complex lineages from the curated TBannotator database, as
  lineage x resistance cross-tabulations and iTOL annotation files.

  Use when: reporting lineage-level AMR allele frequencies in a
  phylogenomics article, supplementary tables or figures, iTOL annotation
  tracks.
argument-hint: "<lineage or strain_sql> [--drugs RIF,INH,EMB,PZA] [--output table.csv]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres
---

# Resistance Profiler : Profil de résistance MTBC

> Cadre : groupe Guyeux, Institut FEMTO-ST (CNRS UMR 6174), Université Marie et Louis
> Pasteur (ex-Université de Franche-Comté), Besançon. Outil de recherche académique,
> destiné à des publications évaluées par les pairs en phylogénomique de la résistance
> aux antimicrobiens. Les synthèses produites suivent le format des tableaux publiés.

Profil automatisé de résistance aux antituberculeux pour une collection de souches MTBC. Produit des tableaux de résistance, des cross-tabulations lignée × résistance, et des fichiers d'annotation iTOL.

## Phase 1 : Découverte (OBLIGATOIRE)

1. **Quelles souches ?** (lignée, pays, SQL, SRA IDs)
2. **Quels antibiotiques ?** (défaut : RIF, INH, EMB, PZA, les 4 first-line)
3. **Quel niveau de détail ?**
   - Phénotypique : antibiogramme BioSample (`antibiogram_inh/rif/pza/emb`), d'où l'on DÉRIVE le type
     de résistance (MDR = INH-R et RIF-R). Il n'y a pas de colonne `dr_type` en v3.6, et seules
     ~23 000 souches sur ~255 000 sont antibiogrammées.
   - Génotypique : mutations individuelles (rpoB S450L, katG S315T, etc.)
   - Les deux (recommandé pour articles)
4. **Sorties souhaitées ?**
   - Tableau résumé (CSV)
   - Cross-tabulation lignée × résistance
   - Dataset iTOL binaire
   - Tableau supplémentaire article (mutations détaillées)

## Phase 2 : Extraction des données

> **Source de vérité (cf. `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`)** : dans TBannotator, `system_name='guyeux'` EST le système maison (= moi/Guyeux), mais c'est un **snapshot** susceptible d'être en retard sur la taxonomie vivante. Ici l'usage (fréquences d'allèles sur des lignées déjà assignées) n'est pas fautif ; c'est seulement une précaution sur la fraîcheur du label. Pour tout clade récent du cycle multi-signal (L1.\*, Bovis1.\*, BCG.\*, L6 profond), recouper le label avec `bdd/actuelle/` + `barcoding_v2/barcode_complete.tsv`. Ne jamais lire `snp_barcoding.csv` (v1 obsolète) ni `strain_lineages.csv` (périmé) comme référence taxonomique.

### Profil phénotypique (antibiogramme BioSample)

> ⚠ **Il n'existe PAS de colonne `dr_type`** dans TBannotator v3.6. Le phénotype disponible est
> l'**antibiogramme par molécule** de `mv_strain_metadata` : `antibiogram_inh`, `antibiogram_rif`,
> `antibiogram_pza`, `antibiogram_emb`, aux valeurs `'INH-S'`/`'INH-R'`, `'RIF-S'`/`'RIF-R'`…
> On dérive donc le type de résistance (MDR = INH-R **et** RIF-R). **Couverture faible** : seules
> ~23 000 souches sur ~255 000 portent un antibiogramme → toujours rapporter le dénominateur réel,
> jamais un pourcentage sur l'effectif total de la lignée.

```sql
-- Distribution des types de résistance pour une lignée (dérivée de l'antibiogramme)
SELECT CASE
         WHEN m.antibiogram_inh = 'INH-R' AND m.antibiogram_rif = 'RIF-R' THEN 'MDR'
         WHEN m.antibiogram_inh = 'INH-R' OR  m.antibiogram_rif = 'RIF-R' THEN 'mono/poly-R'
         ELSE 'susceptible'
       END AS dr_type,
       COUNT(*) AS n,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.strain_id
WHERE c.system_name = 'guyeux' AND c.lineage_code LIKE '4.15%'
  AND (m.antibiogram_inh IS NOT NULL OR m.antibiogram_rif IS NOT NULL)
GROUP BY 1
ORDER BY n DESC;
```

### Cross-tabulation sous-lignée × résistance

```sql
-- Résistance par sous-lignée
SELECT c.lineage_code,
       CASE
         WHEN m.antibiogram_inh = 'INH-R' AND m.antibiogram_rif = 'RIF-R' THEN 'MDR'
         WHEN m.antibiogram_inh = 'INH-R' OR  m.antibiogram_rif = 'RIF-R' THEN 'mono/poly-R'
         ELSE 'susceptible'
       END AS dr_type,
       COUNT(*) AS n
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.strain_id
WHERE c.system_name = 'guyeux' AND c.lineage_code LIKE '4.15%'
  AND (m.antibiogram_inh IS NOT NULL OR m.antibiogram_rif IS NOT NULL)
GROUP BY c.lineage_code, 2
ORDER BY c.lineage_code, 2;
```

### Profil génotypique (mutations de résistance)

> ⚠ **Ne PAS utiliser `mv_protein_position_mutations` / `mv_protein_effect_diversity`** : ces deux vues
> matérialisées existent dans le schéma v3.6 mais **ne sont PAS peuplées** côté serveur (`has not been
> populated`, vérifié 2026-07-31) — et elles sont de toute façon **agrégées** (`strain_count`), donc sans
> `strain_id` : impossible d'y joindre des souches. Passer par les TABLES :
> `tb_report_spdi_annotations` → `tb_report_spdi` → `tb_report_strain_spdi`.
> Les gènes y sont désignés par **locus_tag `Rv####`**, jamais par nom (`rpoB` = `Rv0667`, `katG` = `Rv1908c`,
> `inhA` = `Rv1484`, `embB` = `Rv3795`, `pncA` = `Rv2043c`, `rpsL` = `Rv0682`, `gyrA` = `Rv0006`,
> `gyrB` = `Rv0005`, `ethA` = `Rv3854c`, `tlyA` = `Rv1694`). Champs : `hgvs_p` (p.Ser315Thr),
> `annotation_type` (missense_variant, synonymous_variant…), `impact` (LOW/MODERATE/HIGH).

```sql
-- Fréquence des mutations protéiques d'un gène de résistance (ici katG = Rv1908c)
-- Validé 2026-07-31 : p.Ser315Thr → 64 770 souches ; p.Arg463Leu → 145 516 (polymorphisme de lignée, pas R).
-- Coût : ~40 s (426M lignes dans tb_report_strain_spdi) → TOUJOURS filtrer par locus_tag.
SELECT a.locus_tag, a.hgvs_p, a.annotation_type,
       COUNT(DISTINCT ss.strain_id) AS n_strains
FROM tb_report_spdi_annotations a
JOIN tb_report_spdi s        ON s.spdi_variant_name = a.spdi_variant_name
JOIN tb_report_strain_spdi ss ON ss.spdi_id = s.spdi_id
WHERE a.locus_tag = 'Rv1908c'
  AND a.annotation_type = 'missense_variant'
GROUP BY a.locus_tag, a.hgvs_p, a.annotation_type
ORDER BY n_strains DESC
LIMIT 20;
```

```sql
-- Restreint à une lignée (ajouter la jointure classification ; encore plus coûteux : filtrer fort)
SELECT a.hgvs_p, COUNT(DISTINCT ss.strain_id) AS n_strains
FROM tb_report_spdi_annotations a
JOIN tb_report_spdi s         ON s.spdi_variant_name = a.spdi_variant_name
JOIN tb_report_strain_spdi ss ON ss.spdi_id = s.spdi_id
JOIN mv_strain_classification c ON c.strain_id = ss.strain_id
WHERE a.locus_tag = 'Rv1908c' AND a.annotation_type = 'missense_variant'
  AND c.system_name = 'guyeux' AND c.lineage_code LIKE '4.15%'
GROUP BY a.hgvs_p
ORDER BY n_strains DESC;
```

### Gènes de résistance par antibiotique

| Antibiotique | Gènes principaux | Mutations sentinelles |
|-------------|-------------------|----------------------|
| Rifampicine (RIF) | `rpoB` | S450L (>95% RIF-R) |
| Isoniazide (INH) | `katG`, `inhA` promoteur | S315T (~65% INH-R) |
| Ethambutol (EMB) | `embB` | M306V/I/L |
| Pyrazinamide (PZA) | `pncA` | Très divers (>600 mutations) |
| Streptomycine (SM) | `rpsL`, `rrs` | K43R, K88R |
| Fluoroquinolones (FQ) | `gyrA`, `gyrB` | D94G/N/A/Y |
| Aminoglycosides | `rrs`, `tlyA` | a1401g, c1402t |
| Ethionamide (ETH) | `ethA`, `inhA` | Divers |

## Phase 3 : Génération des sorties

### Tableau résumé CSV

```csv
lineage,total,susceptible,mono_R,poly_R,MDR,pre_XDR,XDR,pct_any_R
4.15,523,412,45,12,38,10,6,21.2
4.15.1,210,180,12,3,10,3,2,14.3
4.15.2,313,232,33,9,28,7,4,25.9
```

### Dataset binaire iTOL

Générer un fichier `02_resistance.txt` au format DATASET_BINARY :

```
DATASET_BINARY
SEPARATOR TAB
DATASET_LABEL	Drug Resistance
COLOR	#ff0000
FIELD_SHAPES	2	2	2	2
FIELD_LABELS	RIF	INH	EMB	PZA
FIELD_COLORS	#ff0000	#ff6600	#0066ff	#009933
LEGEND_TITLE	Drug Resistance
LEGEND_SHAPES	2	2
LEGEND_COLORS	#333333	#cccccc
LEGEND_LABELS	Resistant	Susceptible
DATA
ERR551415	1	1	0	0
SRR33638270	0	0	0	0
```

### Tableau supplémentaire article

Format pour supplément :

```csv
strain_id,lineage,dr_type,rpoB,katG,inhA,embB,pncA,gyrA,rpsL,rrs
ERR551415,4.15.1,MDR,S450L,S315T,,,,,
SRR33638270,4.15.2,susceptible,,,,,,,
```

## Phase 4 : Analyse

### Statistiques calculées par le script

```bash
python3 scripts/resistance_profiler.py strains_metadata.csv \
  -o summary.csv --itol resistance.txt --supplement supplement.csv
```

Le script calcule :
- Prévalence de résistance par sous-lignée avec IC95 (binomial exact)
- Test de Fisher exact pour comparer les taux entre sous-lignées
- Odds ratio (ex. L4.15.2 vs L4.15.1 pour MDR)

### Interprétation

| Indicateur | Seuil | Interprétation |
|-----------|-------|----------------|
| Taux MDR > 5% | Élevé | Lignée à surveiller |
| MDR + FQ-R | pre-XDR | Alerte clinique |
| MDR + FQ-R + injectables-R | XDR | Urgence |
| Taux R significativement différent entre sous-lignées | p < 0.05 (Fisher) | Association lignée-résistance |

## Intégration avec d'autres skills

| Skill | Usage |
|-------|-------|
| `itol` | Ajouter le dataset binaire résistance sur la phylogénie |
| `lineage-comparison` | Tests statistiques avancés (FDR, régression) |
| `phylogeography` | Corrélation résistance × géographie |
| `tbannotator-mcp` | Source des données de résistance |
| `tbmonitor-papers` | Contextualiser les fréquences obtenues dans la littérature publiée (corpus indexé de ~190 k résumés PubMed TB), à lancer en parallèle du profilage |

## Dépendances

```bash
pip install pandas numpy scipy
```
