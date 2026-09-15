---
name: atlantic-voyages
description: >-
  Aggregate and format historical Atlantic maritime voyage data for comparison with M.
  tuberculosis L5/L6 (M. africanum) and L4 sub-lineage phylogeography. Wraps six open-data
  sources: SlaveVoyages Trans-Atlantic (Eltis et al., Emory/Rice, 36 000 voyages,
  1514-1866), AfricanOrigins (~92 000 named individuals with inferred ethnolinguistic
  origin), Liberated Africans Database (~250 000 individuals, 1808-1862), the Slavery,
  Abolition and Social Justice portal, Intra-American Voyages (~11 000 voyages, 1626-1860)
  and Voyages to Liberty. Use when comparing L5/L6 dispersal to documented Atlantic routes,
  building origin-destination matrices for Mantel tests against MTBC pairwise distances,
  overlaying TMRCA estimates on voyage chronologies, or relating diaspora L5/L6 strains to
  probable West African source regions.
argument-hint: "<command: slavevoyages|african-origins|liberated|intra-american|returnees|routes|timeline|fetch> [options]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebFetch
---

# Atlantic Voyages : Données maritimes historiques pour études MTBC L5/L6/L4

Skill complémentaire à `indian-ocean-voyages` (océan Indien pour L1) et à
`slavevoyages` (interface unique avec slavevoyages.org). Ici on cible
spécifiquement la **traite atlantique** et les **routes maritimes du monde
atlantique** (1450-1870, plus reverse migrations 1808-1870 et diaspora
moderne) pour l'étude phylogéographique des lignées **L5, L6
(M. africanum)** et certaines sous-lignées **L4** de *M. tuberculosis*,
sur le modèle de l'approche L1 / Indian Ocean (Morel-Journel, Guyeux,
Sola 2026, *Tuberculosis* 157:102734) et L4 / European migration
(Brynildsrud et al. 2018).

## Contexte d'utilisation

Les datasets MTBC contemporains contiennent typiquement quelques centaines
de souches L5/L6 hors d'Afrique de l'Ouest (USA ~180, Europe ~230 dans le
projet L5L6-codivergence au 2026-05-10). La question phylogéographique
est de savoir si ces souches sont :

1. Des **descendants directs de la traite atlantique** (transplantation
   ancienne 1500-1860, accumulation SPDI conséquente)
2. Des **immigrants modernes** ouest-africains (1960-2025, faible
   accumulation SPDI vs founder africain)
3. Un mélange des deux

Ce skill fournit les routes maritimes documentées et les données
de volumes (Africains déportés par embarcation × destination ×
période) pour confronter à l'arbre phylogénétique observé.

## Phase 1 : Découverte (OBLIGATOIRE)

### 1. Quelle source ?

| Source | Contenu | Période | Granularité | Usage L5/L6 |
|--------|---------|---------|-------------|-------------|
| **SlaveVoyages Trans-Atlantic** | 36 000 voyages, 12.5 M enslaved persons | 1514-1866 | O-D, dates, volumes, nationalité armateur, capitaine | Routes Senegambie/Côte d'Or/Bénin/Biafra/Angola → Bahia/Rio/Caraïbes/USA Sud |
| **AfricanOrigins** | 91 491 individus nommés avec origine inférée | 1808-1862 | Nom, ethnie, port d'embarquement, voyage | Test ethnolinguistique source africaine → diaspora |
| **Liberated Africans** | ~250 000 affranchis 1808-1862 (Atlantique + Indian Ocean) | 1808-1862 | Affranchissement (port, date, navire de prise, devenir) | Routes inverses : Sierra Leone, Libéria, Bahia returnees, Cuba emancipados |
| **Intra-American Voyages** | ~11 000 voyages inter-Caraïbes et coastwise | 1626-1860 | O-D, volumes | Re-dispersion intra-Caraïbes/Brésil interne après débarquement initial |
| **Voyages to Liberty** | Returnees Sierra Leone (Krio), Liberia (Americo-Liberian), Bahia (Aguda) post-1808 | 1808-1900 | Origin → return | Routes inverses Amériques → Afrique de l'Ouest |
| **Slavery, Abolition...** | Logs, lettres, contrats (Adam Matthew Digital) | 1500-1900 | Documents primaires | Validation qualitative des routes |

### 2. Quelle période ?

- **Pré-européenne** (avant 1450) : routes terrestres trans-sahariennes,
  cabotage afro-africain, **non couvertes par les bases atlantiques**,
  voir `seshat` pour États précoloniaux + `migration-data` pour
  contexte général
- **Portugaise précoce** (1450-1640) : SlaveVoyages très partiel,
  reconstitution via archives portugaises (Biblioteca Nacional de
  Portugal, Arquivo Histórico Ultramarino)
- **Néerlandaise + anglaise + française** (1640-1800) : SlaveVoyages
  complet, pic 1700-1800
- **Pic anglais + interdiction graduelle** (1800-1850) : SlaveVoyages
  + Liberated Africans (post-1808)
- **Cuba/Brésil tardif** (1820-1870) : SlaveVoyages tardif + AfricanOrigins
- **Reverse migration** (1808-1900) : Voyages to Liberty
- **Diaspora moderne** (1960-2025) : non couverte par ces bases, voir
  recensements modernes (US Census, UK ONS, INSEE France) et études
  d'émigration ouest-africaine

### 3. Quel format de sortie ?

- **CSV origine-destination** pour Mantel tests vs distances MTBC
- **Timeline** pour overlay sur arbres datés
- **Matrices volumes** par décennie/région
- **Routes géocodées** pour cartes phylogéographiques

## Phase 2 : Routes principales de la traite atlantique

### Routes par grande région d'embarquement

| Région embarquement | Période pic | Volumes | Ports principaux | Sub-lignées L5/L6 attendues |
|---|---|---|---|---|
| **Senegambia + Sierra Leone** | 1650-1830 | ~750 000 | Gorée, James Fort, Bance Island | L6.1.1 Mande, L6.1.2.1.2 Mel_Atlantic, **L5.1** Mossi_Gurma |
| **Windward Coast** (Liberia/Côte d'Ivoire) | 1700-1830 | ~310 000 | Cap des Palmes, Grand Bassam | L5.2.2.1 Tano, mixed Kwa |
| **Gold Coast** (Ghana) | 1650-1800 | ~1 300 000 | Elmina, Cape Coast, Anomabu | **L5.2.2.1.1.2.1.1.1 Akan strict** (P2 phase 27), L5.2.2.x Tano |
| **Bight of Benin** | 1670-1810 | ~2 000 000 | Ouidah, Lagos, Allada | **L5.2.1.1.1 Gbe** (Bénin/Togo, Dahomey), L5.2.x Yoruba |
| **Bight of Biafra** | 1730-1840 | ~1 600 000 | Bonny, Calabar, Cameroon | L5.2.x Igbo (Yoruba-Igbo Volta-Niger), L5.2.2.x |
| **West-Central Africa** | 1500-1860 | ~5 700 000 | Luanda, Benguela, Cabinda | **L5.2.1.1.2 Bantu_Central** (record P2 z=+25.6), L5.2.2.1.1.2.1.2 Gabon |
| **Southeast Africa** | 1780-1860 | ~520 000 | Mozambique Island, Quelimane, Kilwa | L1 (couvert par `indian-ocean-voyages`), pas L5/L6 |

### Routes par destination

| Destination | Volumes | Période | Région source dominante | Sub-lignée L5/L6 attendue |
|---|---|---|---|---|
| **Brésil (Bahia)** | ~1 700 000 | 1550-1860 | Bight of Benin + WCA | L5.2.1.1.1 Gbe + L5.2.1.1.2 Bantu_Central |
| **Brésil (Rio/Sudeste)** | ~2 100 000 | 1550-1860 | WCA dominant | **L5.2.1.1.2 Bantu_Central** (record) |
| **Brésil (Nord, Pará)** | ~400 000 | 1700-1860 | WCA + Bight of Benin | L5.2.x diversité |
| **Caraïbes britanniques** (Jamaïque) | ~1 200 000 | 1650-1830 | Gold Coast + Bight of Benin | L5.2.2.1.1.2.1.x Akan + L5.2.1.1.1 Gbe |
| **Caraïbes françaises** (Saint-Domingue) | ~860 000 | 1670-1791 | Bight of Benin + WCA + Senegambia | Diversité large L5+L6 |
| **Caraïbes hispaniques** (Cuba) | ~780 000 | 1790-1870 | WCA + Bight of Biafra (tardif) | L5.2.1.1.2 + L5.2.x Igbo |
| **USA Sud** (Caroline, Géorgie, Virginie) | ~390 000 | 1700-1808 | Senegambia + Sierra Leone + Bight of Biafra | L6.1.1 Mande + L6.1.2.1.2 Mel_Atlantic + L5.2.x Igbo |
| **Suriname** (néerlandais) | ~325 000 | 1670-1815 | Gold Coast + WCA | L5.2.2.1.1.2.1.x Akan + L5.2.1.1.2 |
| **Guyane française** | ~70 000 | 1700-1820 | WCA + Bight of Benin | L5.2.1.1.2 + L5.2.1.1.1 |

### Pic chronologique

Le **pic de la traite atlantique** est XVIIIe siècle (env. 1700-1810, ~6.5 M
déportés). Les sous-clades fondés à cette époque devraient avoir accumulé
~150-200 SPDIs au taux 0.40 SNP/an (acquis projet L1) entre 1750 et 2025
(soit ~275 ans).

À comparer aux signatures observées :
- L5.2.2.1.1.2.1.1.1 (Akan-strict) : 8 SPDIs cohésifs propres → **émergence
  récente** (300-800 ans BP, compatible Empire Ashanti)
- L5.2.2.1.1.2.1.2 (Gabon) : 76 SPDIs propres → émergence **ancienne**
  (2 000-5 000 ans BP, pré-bantou ou proto-bantou)

→ Le pic de la traite ne correspondrait pas à des fondateurs cohésifs
modernes mais à des **importations multiples polyphylétiques** dans la
diaspora (cohérent avec phase 27 du projet L5L6-codivergence).

## Phase 3 : Commandes disponibles

### `atlantic-voyages slavevoyages [--region REGION] [--year-min YEAR] [--year-max YEAR] [--destination DEST]`

Télécharge ou interroge le subset Trans-Atlantic de SlaveVoyages.

```bash
# Routes Sénégambie → USA Sud entre 1700-1808
atlantic-voyages slavevoyages --region "Senegambia" --destination "Carolinas" --year-min 1700 --year-max 1808

# Routes Gold Coast → Caraïbes britanniques
atlantic-voyages slavevoyages --region "Gold Coast" --destination "Jamaica"

# Volumes total par décennie
atlantic-voyages slavevoyages --aggregate decade
```

### `atlantic-voyages african-origins [--ethnicity ETHNIC] [--year-min YEAR]`

Interroge AfricanOrigins pour les 92 000 individus nommés avec origine.

```bash
# Origines des affranchis Aku/Yoruba post-1830
atlantic-voyages african-origins --ethnicity "Yoruba" --year-min 1830

# Distribution ethnique des affranchis libérés à Sierra Leone
atlantic-voyages african-origins --port "Sierra Leone"
```

### `atlantic-voyages liberated [--year YEAR] [--port PORT]`

Liberated Africans Database (250 000 individus affranchis 1808-1862).

```bash
# Affranchis débarqués à Cuba dans les années 1830
atlantic-voyages liberated --port "Cuba" --year 1830
```

### `atlantic-voyages intra-american`

Voyages inter-Caraïbes et coastwise (11 000 voyages 1626-1860). Pour
re-dispersion intra-régionale après débarquement initial.

### `atlantic-voyages returnees`

Routes inverses Amériques → Afrique de l'Ouest (Krio, Americo-Liberians,
Aguda) post-1808.

### `atlantic-voyages routes --source REGION --dest REGION [--format od|matrix|timeline]`

Construit une matrice O-D pour Mantel tests ou couplage MTBC.

```bash
# Matrice complète O-D pour test Mantel L5/L6
atlantic-voyages routes --source "Gold Coast,Bight of Benin,WCA,Senegambia" \
                       --dest "Bahia,Rio,Jamaica,Saint-Domingue,Cuba,Carolinas" \
                       --format matrix
```

### `atlantic-voyages timeline --lineage L5L6 [--region REGION]`

Construit la timeline chronologique pour overlay sur arbres datés MTBC.

```bash
# Timeline des départs Bight of Benin 1670-1810 pour overlay L5.2.1.1.1 Gbe
atlantic-voyages timeline --region "Bight of Benin" --year-min 1670 --year-max 1810
```

### `atlantic-voyages fetch <dataset-name>`

Télécharge un dataset complet en CSV pour usage local.

```bash
atlantic-voyages fetch trans-atlantic  # CSV principal
atlantic-voyages fetch african-origins
atlantic-voyages fetch intra-american
atlantic-voyages fetch liberated
```

## Phase 4 : URLs et accès aux sources

### SlaveVoyages.org

- **Principal** : `https://www.slavevoyages.org/`
- **Voyages Trans-Atlantic** : `https://www.slavevoyages.org/voyage/database`
- **Carte interactive (Timelapse)** : `https://www.slavevoyages.org/voyage/maps`
- **Downloads** : `https://www.slavevoyages.org/voyage/database#downloads`
- **Intra-American** : `https://www.slavevoyages.org/american/database`
- **Enslaved People (named)** : `https://www.slavevoyages.org/past/database`

NB : L'API REST `api.slavevoyages.org` requiert authentification. Utiliser
les downloads CSV publics ou WebFetch sur la base interactive.

### African Origins

- **Principal** : `https://www.african-origins.org/`
- **Database** : `https://www.african-origins.org/african-data/`
- **Download** : `https://www.african-origins.org/african-data/?download=true`

### Liberated Africans Database

- **Principal** : `https://liberatedafricans.org/`
- **Search** : `https://liberatedafricans.org/search/`

### Slavery, Abolition and Social Justice (Adam Matthew)

- Accès institutionnel uniquement (universités abonnées)
- `https://www.amdigital.co.uk/primary-sources/slavery-abolition-and-social-justice`

### Voyages to Liberty (returnees)

- Documenté dans la littérature secondaire (Lovejoy, Schwartz)
- Pas de base de données unique, agrégation via SlaveVoyages + littérature

## Phase 5 : Couplage avec MTBC L5/L6

### Workflow standard

1. **Inventaire diaspora L5/L6** : pour chaque souche hors Afrique
   ouest-africaine (USA, Europe, Brésil, etc.), récupérer pays et
   sous-lignée fine via `bdd/actuelle/` (vérité de référence).

2. **Inférence source africaine** : pour chaque souche, identifier la
   sous-lignée africaine source via similarité SPDI (cf. méthode
   SPDI-cohésif P2 phases 26-27). Exemples attendus :
   - L5.2.2.1.1.2.1.1.1 → Akan Ghana (Gold Coast)
   - L5.2.1.1.1 → Gbe Bénin/Togo (Bight of Benin)
   - L5.2.1.1.2 → Bantu_Central Kongo/Angola (WCA)
   - L6.1.1 → Mande Sénégambie

3. **Couplage SlaveVoyages** : pour chaque source africaine, récupérer
   les volumes documentés de déportation vers la destination observée
   du strain diaspora.

4. **Test de cohérence** : la fréquence diaspora observée par sous-clade
   est-elle corrélée aux volumes historiques de la traite ?

5. **Discrimination moderne vs historique** : pour chaque strain diaspora,
   comparer `collection_date` (récent = immigrant moderne) et accumulation
   SPDIs depuis founder africain (élevée = descendant traite) au taux
   0.40 SNP/an validé projet L1.

### Cas pilotes pour validation méthodologique

**L5.2.2.1.1.2.1.1.1 (Akan strict)** :
- En Afrique : 46 souches Ghana strict (Empire Ashanti, 300-800 BP)
- Diaspora attendue : Caraïbes britanniques (Jamaïque), USA Sud, Suriname
- À vérifier : présence dans les 179 USA L5/L6 (10 souches portent ce
  code dans bdd/actuelle/ projet L5L6-codivergence)

**L5.2.1.1.2 (Bantu_Central Kongo)** :
- En Afrique : 41 souches Bantu_Central RDC (record P2 z=+25.6)
- Diaspora attendue : Brésil Sudeste, Cuba tardif, Caraïbes françaises
- À vérifier : présence dans les 11 souches USA + 9 Europe
  L5.2.1.1.2 (P5 phase 28)

**L6.1.1 (Mande Sénégambie)** :
- En Afrique : 667 souches saturated Mande
- Diaspora attendue : USA Sud (Caroline Sea Islands Gullah/Geechee)
- À vérifier : sous-clades L6.1.1.x parmi les ~30 souches USA Mande

## Phase 6 : Liens avec projets MTBC en cours

- **Projet L1-Brazil_Mozambique-triangular_slave_trade** : modèle
  méthodologique publié (Morel-Journel, Guyeux, Sola 2026,
  *Tuberculosis* 157:102734). Horloge 0.40 SNP/an validée.
- **Projet L5L6-codivergence_ethnies_ouest_afrique** : sources
  africaines identifiées P2 phases 26-27 (SPDI-cohésif). 4 sub-clades
  cohésifs avec marqueurs définis.
- **Projet animal_vs_human** : co-évolution multi-pathogène (P3).

Ce skill **complète indian-ocean-voyages** : ensemble ils couvrent les
**routes maritimes triangulaires** de l'esclavage (Indian Ocean pour L1,
Atlantique pour L5/L6/L4) et permettent la **vue d'ensemble MTBC ×
traite mondiale**.

## Phase 7 : Limites et caveats

- **Africains illégalement déportés post-1808** : sous-comptés dans
  SlaveVoyages (clandestin)
- **Volumes intra-africains** : routes terrestres trans-sahariennes,
  cabotage afro-africain pré-européen mal documentés
- **Granularité ethnique** : les origines sont inférées par port
  d'embarquement et non par ethnie réelle des captifs (qui pouvaient
  venir de très loin à l'intérieur du continent)
- **Mortalité différentielle** : ~15-20% Middle Passage. Les souches
  TB qui ont survécu peuvent être un sous-échantillon biaisé
- **Sous-séquençage Caraïbes/Suriname/Guyane** : zones les plus
  densément peuplées par descendants directs d'esclaves restent
  largement non-séquencées (cf. phase 28 P5 du projet
  L5L6-codivergence : 0 souche publique pour Cuba, Jamaïque, Haïti,
  Trinidad, Suriname, Guyane française)

## Phase 8 : Référence et lien

- Eltis, D. (2007). *The Voyage of the Slave Ship: Studies of the
  Atlantic Slave Trade*. Cambridge UP.
- Lovejoy, P. (2000). *Transformations in Slavery*. Cambridge UP.
- Morel-Journel, T., Guyeux, C., Sola, C. (2026). *Migrations and
  Tuberculosis: comparative study of Mycobacterium tuberculosis
  genomic population structure in Brazil and Mozambique...*
  *Tuberculosis* 157:102734.
- Brynildsrud, O. B. et al. (2018). Global expansion of Mycobacterium
  tuberculosis lineage 4 shaped by colonial migration and local
  adaptation. *Sci Adv* 4(10):eaat5869.
- Rabahi, M. F. et al. (2020). First report of Mycobacterium africanum
  in Brazil. *PMID: 32920193*. Cluster with Gambian strains.
