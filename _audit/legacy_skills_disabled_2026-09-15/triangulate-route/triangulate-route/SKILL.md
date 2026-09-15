---
name: triangulate-route
description: >-
  Academic phylogeography research toolkit (Guyeux group, FEMTO-ST).
  Triangulates the published genomic signature of an MTBC research lineage
  against historical human-migration corpora to produce peer-review-ready
  dispersal scenarios. Takes a lineage and a target country as input,
  returns: (a) global published neighbours by sub-lineage (Shitikov23)
  via TBannotator research database, (b) candidate historical dispersal
  routes sourced from SlaveVoyages, OWTRAD, and the specialized
  scholarly literature, (c) a triangulation table formatted for
  scientific publication. Implements the methodology described in
  peer-reviewed case studies (e.g. Madagascar MTBC phylogeography).

  Utiliser quand : ecrire une section phylogeographique d'un article
  scientifique sur un pays/region (Bresil, Antilles, Cap Vert, Maurice,
  Comores, Inde, etc.), valider une signature genomique publiee avec
  corpus historiques d'archives, preparer une diapositive de seminaire
  academique, ou rediger un *case study* dans un manuscrit scientifique.
---

# triangulate-route -- Triangulation MTBC × corpus historiques

## Overview

Skill agentique qui industrialise la triangulation à 3 niveaux validée sur le cas
Madagascar (cahier_de_labo entrées 59-62 du projet musee_de_lhomme) :

1. **Voisinages mondiaux** par sous-lignée TBannotator (Shitikov23, 46 sous-lignées,
   le plus fin disponible)
2. **Routes historiques candidates** via pointeurs vers les skills `slavevoyages`
   (36 000 voyages 1514-1866) et `owtrad` (routes pré-modernes 10 000 BCE-1820 CE)
3. **Validation peer-reviewed** via recherche bibliographique ciblée (skill
   `lit-review` ou WebSearch ciblé)

Si les 3 niveaux convergent → la signature génomique est scientifiquement
défendable face à un reviewer rigoureux.

## Quand l'invoquer

- L'utilisateur veut analyser un nouveau pays/region MTBC sur le modèle Madagascar
- Préparer une slide bonus pour audition/séminaire avec triangulation génomique × historique
- Écrire une section *case study* dans un papier méthodologique
- Valider une signature génomique inattendue avec corpus historiques d'archives

## Quand ne PAS l'invoquer

- L'utilisateur veut juste compter des souches par pays → utiliser TBannotator MCP directement
- L'utilisateur travaille sur les hôtes humains (AADR) sans pathogène → utiliser `aadr`
- Le pays cible n'a pas assez de souches dans TBannotator (< 50) → triangulation peu informative

## Usage typique

```bash
# Etape 1 : interroger TBannotator pour les voisins mondiaux d'un pays cible
python triangulate.py --country "Cabo Verde" --output cv_triangulation.tsv

# Etape 2 : si signature riche, faire la triangulation historique
# (consulter skills slavevoyages + owtrad pour le pays cible)

# Etape 3 : générer la figure/table de triangulation
python plot_triangulation.py cv_triangulation.tsv --output cv_triangulation.png
```

## Workflow détaillé (4 étapes)

### Étape 1 : Inventaire MTBC du pays cible

Requête TBannotator (vérifiée contre le schéma courant, 2026-07-31) :

```sql
SELECT sc.lineage_level_1, sc.lineage_code, COUNT(DISTINCT sc.strain_id) AS n
FROM mv_strain_classification sc
JOIN mv_strain_metadata sm ON sc.strain_id = sm.strain_id
WHERE sm.geo_country = '<PAYS>'
  AND sm.species_group = 'M. tuberculosis'
  AND sc.system_name = 'Coll'
GROUP BY sc.lineage_level_1, sc.lineage_code
ORDER BY n DESC;
```

**Géographie : deux colonnes, deux usages.** `mv_strain_metadata` porte
`geo_loc_name` (chaîne NCBI brute, par exemple `Mexico: Jalisco`), `geo_country`
(pays normalisé) et `geo_region` (subdivision). Filtrer sur `geo_country = '<PAYS>'`
plutôt que sur `geo_loc_name ILIKE '<PAYS>%'` : la normalisation gère les libellés
non préfixés par le pays et les variantes orthographiques, que le `ILIKE` rate
silencieusement.

Contrepartie à connaître : `geo_country` n'est renseigné que pour environ 174 000
souches sur 255 000 (168 pays distincts). Un filtre sur `geo_country` écarte donc
en silence un tiers de la base. Pour un inventaire exhaustif, récupérer aussi ce
qui reste :

```sql
-- ce que le filtre normalise a laissé de côté
SELECT geo_loc_name, COUNT(*) FROM mv_strain_metadata
WHERE geo_country IS NULL AND geo_loc_name ILIKE '%<PAYS>%'
GROUP BY geo_loc_name ORDER BY 2 DESC;
```

Filtrer les sous-lignées avec n ≥ 5 pour analyse robuste. Avant toute lecture
historique, rapporter n au total séquencé du pays : un pays à 40 génomes déposés
ne porte aucune signature exploitable, et l'absence d'une sous-lignée y est une
absence d'échantillonnage.

### Étape 2 : Voisinages mondiaux par sous-lignée (Shitikov23)

Pour chaque sous-lignée présente avec n ≥ 5 dans le pays cible :

```sql
SELECT sm.geo_country, COUNT(DISTINCT sc.strain_id) AS n
FROM mv_strain_classification sc
JOIN mv_strain_metadata sm ON sc.strain_id = sm.strain_id
WHERE sc.system_name = 'Shitikov23'
  AND sc.lineage_code = '<SOUS-LIGNEE>'
  AND sm.species_group = 'M. tuberculosis'
  AND sm.geo_country IS DISTINCT FROM '<PAYS>'
  AND sm.geo_country NOT IN ('USA', 'United Kingdom', 'Australia', 'Canada',
                             'Sweden', 'Germany', 'Netherlands', 'France',
                             'Norway', 'Denmark', 'Switzerland', 'Belgium')
GROUP BY sm.geo_country
ORDER BY n DESC
LIMIT 15;
```

La sous-lignée cible est déjà connue de l'étape 1, donc la CTE `target_strains`
de la version précédente était un aller-retour inutile : elle ne servait qu'à
retrouver un `lineage_code` déjà fixé par le paramètre. La requête directe
ci-dessus renvoie le même résultat en un seul balayage.

Attention à `NOT IN` avec des NULL : `geo_country NOT IN (...)` est faux dès que
`geo_country` est NULL, donc les souches sans pays normalisé sont exclues, ce qui
est le comportement voulu ici. En revanche `geo_country != '<PAYS>'` aurait le
même effet par accident ; d'où le `IS DISTINCT FROM`, qui exprime l'intention
explicitement.

**Filtre crucial** : exclure les pays de l'immigration moderne (USA, UK, AU, CA, etc.)
pour réduire le biais d'échantillonnage diaspora. Ces pays accumulent les souches de
tous les pays sources, donc apparaîtraient toujours en tête.

### Étape 3 : Mapping voisinages → bassins historiques

Construire un tableau de catégorisation par patterns :

| Pattern de voisinage | Bassin historique candidat |
|---|---|
| Inde + Thaïlande + Vietnam + Indonésie | Asie du Sud-Est / routes commerciales asiatiques |
| Tanzanie + Malawi + Kenya + Mozambique | Route arabo-swahili Afrique de l'Est |
| Pérou + Brésil + Argentine + Gambie | Traite atlantique (sens Afrique → Amériques ou réciproque) |
| Nigeria + Ghana + RDC + Rwanda + Cameroun | Bantou ouest-africain (L4.6.2, L5, L6) |
| Italie + Espagne + Portugal + France + Roumanie | Colonial européen post-1500 (LAM/Haarlem) |
| Géorgie + Chine + Russie + Asie Centrale | Beijing globalisé post-1900 |
| Iran + Pakistan + Inde + Asie Centrale | Routes silk road (L3 CAS, L2 Beijing) |

### Étape 4 : Validation historique via skills

Pour chaque bassin candidat identifié :

| Bassin | Skill à consulter | Type de requête |
|---|---|---|
| Traite atlantique | `bio_redac:slavevoyages` | Voyages port embarquement → port débarquement |
| Routes commerciales pré-modernes | `bio_redac:owtrad` | Routes maritimes/terrestres par période |
| Colonisation européenne | recherche bibliographique | Histoire coloniale du pays |
| Bantou / Africain | `lit-review` + Sahal 2023 PLOS NTD | Lignées Cameroun-Nigeria-Ghana |
| Austronésien | `lit-review` + Crowther 2016 PNAS | Migration Bornéo + route côtière |
| Silk Road | `bio_redac:owtrad` Silk Road dataset | Routes Asie Centrale |

### Étape 5 : Produire table + figure de triangulation

Suivre le format Madagascar Z30 :

| Route MTBC | n_target | Voisins TBannotator | Source historique | Validation |
|---|---|---|---|---|
| ... | ... | Top 3 pays | Référence | Pourquoi cohérent |

## Exemple : usage sur le Brésil (cas L1 traite atlantique enrichi)

```bash
# 1. Inventaire L1 Brésil
python triangulate.py --country Brazil --filter "lineage_code LIKE '1%'" --output brazil_l1.tsv

# 2. Sous-lignée L1.1.2 voisins (devrait montrer Mozambique 47, Tanzanie...)
# Confirmation du papier Guyeux 2026 sur la traite atlantique

# 3. Comparer avec sous-lignée L4 Brésil pour voir si pattern différent
python triangulate.py --country Brazil --filter "lineage_code LIKE '4%'" --output brazil_l4.tsv
```

## Cas tests pré-validés

| Pays | Routes attendues | Validation Madagascar entrée 62 |
|---|---|---|
| **Madagascar** | Austronésien + arabo-swahili + traite atlantique + bantou + colonial | ✓ entrées 59-62 |
| **Brésil** | Traite atlantique + colonial européen | À tester (enrichit Guyeux 2026) |
| **Cap Vert** | Traite atlantique + colonial portugais | À tester |
| **Antilles** | Traite atlantique + colonial européen | À tester |
| **Comores** | Arabo-swahili + austronésien | À tester |
| **Maurice/Réunion** | Indien + colonial français + bantou | À tester |

## Limites

- Biais d'échantillonnage TBannotator : sur-représentation Inde, Tanzanie, Vietnam.
  Filtre des pays diaspora moderne (USA, UK, AU, CA) recommandé.
- Sous-lignées Shitikov23 plus fines que Coll (46 vs 28) mais pas exhaustives.
  Pour analyse plus fine, calcul distance SNP réel via SPDI (post-recrutement).
- Pas de datation : la triangulation identifie les routes plausibles mais ne date pas
  les introductions. Pour datation : `bio_redac:beast2-phylogeography` ou
  `bio_redac:iqtree-lsd2`.

## Citation

```bibtex
@misc{guyeux2026triangulateroute,
  title = {triangulate-route: Automated triangulation of MTBC genomic signatures with historical archive corpora},
  author = {Guyeux, Christophe},
  year = {2026},
  note = {Skill agentique, écosystème bio_redac. Méthodologie démontrée sur Madagascar (cahier_de_labo musee_de_lhomme entrées 59-62).}
}
```

## Intégration avec autres skills

| Skill | Rôle |
|---|---|
| `bio_redac:tbannotator-mcp` | Source des voisins par sous-lignée |
| `bio_redac:slavevoyages` | Validation routes traite atlantique post-1514 |
| `bio_redac:owtrad` | Validation routes pré-modernes 10 000 BCE-1820 CE |
| `host-pathogen-pair` | Pairing avec humains anciens AADR |
| `bio_redac:lit-review` | Validation peer-reviewed des routes candidates |
| `bio_redac:claim-check` | Vérification des chiffres historiques |
