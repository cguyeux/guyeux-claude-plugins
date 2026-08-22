---
name: molecular-clock
description: >-
  Academic research toolkit for peer-reviewed MTBC evolutionary genomics (Guyeux group,
  FEMTO-ST). Molecular dating of Mycobacterium tuberculosis complex phylogenies under weak
  temporal signal: root-to-tip regression, TempEst analysis, BEAST XML generation, multi-
  constraint calibration for the MTBC-specific clock challenges, and date-randomisation
  controls. Use when estimating divergence times for MTBC lineages in a research study,
  evaluating temporal signal in a published phylogeny, preparing BEAST or BEAST2 analyses,
  or dating the emergence of a sub-lineage or of an antimicrobial-resistance allele for a
  scientific publication.
argument-hint: "<tree.nwk> <dates.csv> [--method root-to-tip|beast] [--rate 0.5]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, mcp__tbannotator__tool_query_postgres
---

# Molecular Clock : Datation moléculaire MTBC

> [!TIP]
> **Ce qui déborde ici, c'est la mémoire, pas le temps.** Une matrice de distances ou un alignement
> de plusieurs milliers de souches passe mal en local : `mp` offre 125 Go immédiatement disponibles,
> `mh` partition `bigmem` va jusqu'à 1 To. À noter, `treetime` est **déjà installé aux deux
> endroits** : `/usr/bin/treetime` sur `mp` (route la moins coûteuse pour une datation rapide) et
> version 0.12.1 dans `/Work/Users/cguyeux/envs/phylo/bin` sur `mh`.
> Voir le skill `remote-compute` (sonde d'état, modèles `sbatch`, pièges). Prérequis : VPN monté (`sudo vpn up`).


Estimation des temps de divergence pour les phylogénies MTBC. Gère spécifiquement le problème du signal temporel faible (R² < 0.01) inhérent à MTBC, avec des stratégies de calibration multi-contraintes.

## Phase 0 : Cadre épistémique : les TMRCA dépendent de la fenêtre de calibration

**Avant tout calcul**, comprendre que le taux de substitution MTBC n'est pas une constante universelle mais une quantité qui varie avec l'échelle temporelle de mesure. Menardo et al. 2019 (*PLoS Pathog*) documentent une plage de $10^{-8}$ à $5 \times 10^{-7}$ subs/site/an selon le clade et la fenêtre de sampling. Cette variance est **structurelle**, pas statistique : elle reflète le *time-dependent rate phenomenon* (TDRP), une loi empirique négative entre taux inféré et timescale de mesure documentée massivement chez les virus (Ho 2011/2015, Duchêne 2014, Aiewsakun 2015, Membrebe 2019) et émergente chez les bactéries clonales (Rieux & Balloux 2016, Rasmussen 2015 *Yersinia*).

### Les trois régimes de mesure MTBC

| Régime | Timescale | Taux observé | TMRCA associé |
|--------|-----------|--------------|---------------|
| Modern tip-dating seul | ~50 ans | $\sim 10^{-7}$ | 40 000–70 000 BP (Wirth 2008, Comas 2013) |
| aDNA-calibré court-moyen | 100–2 200 ans | $2$–$3 \times 10^{-8}$ | 2 190–6 000 BP (Bos 2014, Sabin 2020) |
| TDRP-corrigé (envelope) | Coalescence MTBC | $\sim 7$–$9 \times 10^{-9}$ | **8 500–21 000 BP** |

Les trois estimations sont mutuellement incompatibles si lues comme des mesures d'une même quantité ; elles deviennent cohérentes si lues comme des **segments distincts d'une courbe de décroissance de taux** (loi de puissance $r(t) = r_0 (t/t_0)^\alpha$, $\alpha \approx -0.44$). Voir `complex_datation/article/main.tex` Appendix A et C pour le fit empirique.

### Quatre mécanismes candidats du TDRP

1. **Sélection purifiante**, dominant chez MTBC. Les substitutions délétères sont éliminées avec le temps ; l'échantillonnage moderne voit du polymorphisme transitoire que la trace fossile a déjà filtré. Soubrier et al. 2012 démontrent que l'hétérogénéité de taux parmi sites amplifie la dépendance temporelle.
2. **Saturation de séquence**, négligeable chez MTBC sur 10⁴ ans (génome 4.4 Mb, ~0.4 SNP/an → double hit rare).
3. **Erreurs de calibration**, biais asymétriques des dates ¹⁴C et BioSample.
4. **Mauvaise spécification du modèle**, horloge stricte là où elle ne s'applique pas, priors démographiques incorrects.

**Conséquence opérationnelle** : le filtrage synonymes-only que ce skill applique par défaut n'est pas une astuce pragmatique. C'est une **correction mécanistique** du facteur dominant du TDRP mycobactérien : on retire les sites soumis à la sélection purifiante différentielle, qui est précisément ce que Soubrier 2012 identifie comme amplificateur du phénomène.

### Règle d'or : redondance à timescale plutôt qu'à timescales variés

Intuition empirique contre-intuitive vérifiée par bootstrap 1000 sur le fit TDRP joint MTBC+leprae (cf. `complex_datation/` 2026-04-19) : **deux anchors indépendants à même timescale valent plus que deux anchors à timescales différents** pour contraindre l'envelope TMRCA. L'ajout d'un unique anchor indépendant à $t = 2\,000$ ans a contracté le bootstrap upper tail de $\sim\!65\,000$ BP à $\sim\!29\,600$ BP, exclusion formelle du long-clock Comas 2013 qui n'était pas possible avec trois anchors à trois époques distinctes (50 y, 1 000 y, 2 000 y).

**Mécanisme** : deux valeurs indépendantes à même timescale se contraignent mutuellement et suppriment les réalisations bootstrap à exposants $\alpha$ extrêmes. Un troisième anchor à une époque déjà couverte élimine plus d'incertitude que son troisième collègue à une nouvelle époque.

**Conséquence pratique** : avant de chercher à étendre la fenêtre temporelle couverte (nouveau anchor Antiquité, nouveau anchor Mésolithique), chercher d'abord à **doubler un anchor existant** par une méthode indépendante (publication différente, pipeline différent, lignée différente du même clade). C'est plus rentable en termes de contraction de l'incertitude.

### Upper bound qualitatif : Bison antiquus (17 870 BP)

Rothschild et al. 2001 (*Clin Infect Dis*) ont extrait du DNA MTBC d'un métacarpe de *Bison antiquus* du Natural Trap Cave (Wyoming), radiocarbone-daté à **17 870 ± 230 ans BP**. Deux laboratoires indépendants ont confirmé par PCR et spoligotypage avec précautions anti-contamination strictes ; le spoligotype est plus proche de *M. africanum* (82.3) que de *M. bovis* (72.7). Lee et al. 2012 ont indépendamment confirmé par GC-MS des biomarqueurs lipidiques spécifiques du MTBC (mycocerosates C29–C32, mycolipenates C27) sur le même spécimen. L'authentification pré-date les standards MapDamage/PMDtools, donc le statut reste ouvert jusqu'à un re-séquençage shotgun 2025.

**Si authentifié, ce spécimen impose TMRCA MTBC > 17 870 BP**, ce qui invalide mécaniquement toute estimation aDNA-calibrée en dessous de ce seuil, y compris la nôtre à 3932 BP (facteur 4.5). Utiliser comme **sanity-check qualitatif** : un TMRCA MTBC global calculé < 18 000 BP doit être reporté avec une clause TDRP explicite (cf. section "Scope" ci-dessous).

### Scope et limites explicites du skill

| Cas d'usage | Adapté ? |
|-------------|----------|
| Émergence d'une sous-lignée (L4.6.2, L2.2.1 Beijing, L4.15), fenêtre 100–2 000 ans | **Oui, directement** |
| TMRCA d'une lignée entière (L4, L2), fenêtre 1 000–5 000 ans | Oui, **avec warning TDRP explicite** |
| TMRCA MTBC global, divergence animales paraphylétiques, fenêtre > 10 000 ans | **Non**, sortir vers Membrebe 2019 / BEAST2 TDRP-aware / fit loi de puissance Aiewsakun 2015 |
| Datation événement historique intra-lignée (résistance, expansion coloniale) | **Oui** |
| Host–pathogen co-dating (TYK2, HLA) | Pas couvert, voir Kerner 2021, Romeyer d'Herbey 2026 |

**Règle de sécurité** : le pipeline v5 calibre un taux sur la fenêtre 100–2 200 BP. Les TMRCA extrapolés à partir de ce taux sont des **TMRCA calibrés aDNA**, systématiquement plus récents que le vrai TMRCA sous TDRP. Toujours reporter les résultats avec cette qualification.

### Références externes inter-projet

- `complex_datation/article/main.tex`, perspective piece TDRP-centrée (16 pages, 40 citations, 3 figures, 3 appendix empiriques).
- `complex_datation/litterature_review/time_dependent_rate_phenomenon.md`, revue TDRP (9 articles clés, cadre théorique complet).
- `complex_datation/litterature_review/mycobacterium_leprae_ancient_dating.md`, corpus aDNA *M. leprae* (>50 génomes, 4 continents, benchmark méthodologique).
- `complex_datation/litterature_review/ancient_dna_mtbc_dating.md`, revue aDNA MTBC exhaustive.
- `complex_datation/data/adna_mtbc_corpus.csv`, corpus consolidé 23 aDNA MTBC + 1 Bison.

## Le problème MTBC

MTBC a un taux de mutation très faible (~0.3-0.5 SNP/génome/an) et des temps de génération longs. Conséquences :

| Problème | Impact | Solution |
|----------|--------|----------|
| R² très faible (<0.01) | Root-to-tip regression non significative | Analyses bayésiennes avec priors informatifs |
| Variation du taux entre lignées | Horloge stricte inappropriée | Horloge relaxée (UCLD) |
| Dates de collection imprécises | Bruit dans la calibration | Tip-dating avec incertitude |
| Homoplasie | Sature le signal | Filtrer sites hypervariables, utiliser BIN+G |
| Recombinaison | Fausse topologie | MTBC essentiellement clonal → risque faible |

## Phase 1 : Découverte (OBLIGATOIRE)

1. **Quel arbre ?** (Newick, sortie RAxML-NG)
2. **Dates de collection ?** (CSV : strain_id, date, format YYYY ou YYYY-MM-DD)
3. **Objectif ?**
   - Dater l'émergence d'une lignée/sous-lignée
   - Estimer le taux de mutation
   - Dater l'acquisition de résistance
   - Calibrer un arbre pour une figure d'article
4. **Calibrations disponibles ?**
   - Dates de collection des souches (tip-dating)
   - Fossiles/événements historiques (node calibration)
   - Taux de mutation publié (prior)

## Phase 2 : Root-to-tip regression (exploratoire)

> **Diagnostic d'entrée** : `python3 scripts/molecular_clock.py root-to-tip tree.nwk
> dates.csv -o rtt.csv -p rtt.png`. Distances racine-feuille VRAIES (Bio.Phylo, pas un
> proxy de longueur de branche terminale) ; rapporte R², le taux et un **IC 95 %
> bootstrap** (`rate_boot_ci95_lo/hi`, resampling des souches) en plus de l'IC
> analytique, avec une évaluation honnête du signal (faible/typique MTBC → BEAST
> recommandé). Self-check : `python3 scripts/smoke_test.py`. **Choisir l'outil** : ce
> diagnostic D'ABORD (y a-t-il du signal temporel ?), puis `iqtree-lsd2` pour dater
> vite en ML à grande échelle, ou `beast2-phylogeography` pour des postérieurs bayésiens
> complets (la génération du XML BEAST relève de `beast2-phylogeography`, pas d'ici).

### Extraire les dates depuis TBannotator

```sql
SELECT m.strain_id, m.collection_date
FROM mv_strain_metadata m
JOIN mv_strain_classification c ON m.strain_id = c.strain_id
WHERE c.system_name = 'guyeux' AND c.lineage_code LIKE '4.15%'
  AND m.collection_date IS NOT NULL;
```

### Script root-to-tip

```bash
python3 scripts/molecular_clock.py root-to-tip tree.nwk dates.csv \
  -o rtt_results.csv -p rtt_plot.png
```

**Sortie** :
- Plot root-to-tip distance vs date de collection
- Régression linéaire : pente = taux de substitution estimé
- R², p-value, IC95 du taux
- Résidus pour identifier les outliers temporels

### Interprétation du R²

| R² | Interprétation MTBC | Action |
|----|---------------------|--------|
| > 0.3 | Signal temporel fort (rare pour MTBC) | Root-to-tip suffisant, BEAST confirmera |
| 0.1-0.3 | Signal modéré | BEAST recommandé avec horloge relaxée |
| 0.01-0.1 | Signal faible (typique MTBC) | BEAST obligatoire, priors informatifs |
| < 0.01 | Pas de signal détectable | **Tip-dating MORT** → passer à la Phase 2c (ancres internes + datation bracketée). Ne PAS lancer BEAST. |

### Test de randomisation des dates (DRT) : garde-fou AVANT BEAST

Le R² seul ne dit pas si un signal faible est **réel** ou fortuit. Le DRT
permute les dates entre souches et recompte la pente : s'il y a un vrai signal,
la pente observée sort du nuage des pentes permutées. **À faire avant de lancer
une chaîne BEAST de 30-50 M**, évite de dater dans le vide.

```bash
python3 scripts/molecular_clock.py date-randomization tree.nwk dates.csv \
  --midpoint -p drt.png       # --midpoint : enracine au midpoint si pas d'outgroup
```

Sortie JSON : `observed_slope`, `observed_r_squared`, `drt_p_value` (unilatéral,
obs > permutées), `temporal_signal` (bool), et le nuage permuté (médiane, IC95).
Verdict `temporal_signal=true` ssi `drt_p_value < 0.05` **et** pente > 0.

**Lecture** : un `drt_p_value` proche de 0.05 = signal marginal, souvent porté par
les seuls points aDNA, dater reste hasardeux. Validé sur un jeu Pinnipedii+L4
(36 taxa) : R²=0.078, DRT p=0.038 → signal *présent mais fragile*, cohérent avec
une lignée de niche récente et peu diverse. Sur une grande lignée diverse
(Bovis, L2…) on attend R² et marge DRT nettement plus francs.

## Phase 2c : Que faire quand le DRT dit NON : la taxonomie des ANCRES CALENDAIRES INTERNES

C'est le cas le plus **fréquent** sur MTBC (fenêtre de sampling ~25 ans, taux ~0,3 SNP/an) et le skill ne doit pas
s'arrêter là. Quand `temporal_signal=false`, il reste deux voies, et **une seule loi** pour choisir entre elles.

### La datation bracketée (méthode par défaut, importée du projet L1)

`âge = profondeur SNP masquée / taux`, calculée sur un **ÉVENTAIL de taux externes** (0,10 / 0,26 / 0,40 / 0,50 /
1,10 SNP/génome/an). On rapporte un **INTERVALLE, jamais un point**. Trois règles :
- **LE TAUX DOMINE** : l'intervalle est plus sensible au taux choisi qu'à la profondeur mesurée. Les taux calibrés
  sur clades profonds **surestiment** l'âge des nœuds récents (TDRP, cf. Phase 0) ; un taux natif de lignée
  (rapide) pousse les dates vers le moderne. Toujours donner les deux bouts.
- **CROWN ≠ INTRODUCTION** : le crown date la diversification LOCALE. Une introduction ancienne persistant en une
  seule lignée donne un crown récent. Ne jamais lire un crown comme une date d'arrivée.
- **Masquer avant de compter** : homoplasie / résistance / répétitions (`traces_mask`) sinon la profondeur est
  gonflée d'un facteur 1,3-2.

### ★ THÉORÈME D'ASYMÉTRIE DES ANCRES : à appliquer AVANT de chercher une ancre

> Un événement qui **OUVRE** un corridor (migration, colonisation, mise en contact) borne l'âge d'un foyer de
> destination **PAR LE HAUT** (on ne transmet pas avant d'être arrivé) → **borne INFÉRIEURE sur le taux** → borne
> SUPÉRIEURE sur l'âge de tous les nœuds.
>
> Seuls un événement qui **FERME** (barrière/isolement durable) ou une **OBSERVATION DATÉE** (spécimen ancien
> authentifié) bornent l'âge **PAR LE BAS** → **borne SUPÉRIEURE sur le taux**.

**Conséquence pratique** : dans le monde moderne, les corridors ne se referment jamais (traite → colonisation →
aviation). Les ancres « ouverture » sont donc **abondantes**, les ancres « fermeture » **quasi inexistantes**. On
sait presque toujours dire « ce clade n'est pas PLUS VIEUX que X », presque jamais « il n'est pas PLUS JEUNE que X ».

**Réflexe** : avant d'investir dans une ancre, demander **ouvre-t-elle ou ferme-t-elle ?** Si elle ouvre, elle ne
tranchera jamais un « ancien vs récent » par le côté récent. Une question du type « médiéval ou colonial ? » peut
être **structurellement indécidable**, ce n'est alors pas un défaut d'effort mais un **défaut de données**, et
cela se rapporte comme tel, assorti d'un appel à données (aDNA de la région ; ou séquençage des **collections
historiques de culture**, qui étendent la fenêtre d'échantillonnage de ~25 à ~60 ans, c'est exactement ce dont le
signal temporel a besoin).

### Ancre « OUVERTURE » qui MARCHE : le foyer de corridor migratoire

Un corridor migratoire moderne daté (ex. Afrique de l'Ouest → Italie, 1980-1990) borne un **foyer de transmission
qui s'est diversifié À DESTINATION** : `MRCA ≥ date d'ouverture` → `profondeur ≤ taux × durée` → **taux ≥ profondeur
/ durée**. Validé sur L6 (foyer italien, 7 souches, prof. 6,3 SNP → **taux ≥ 0,17-0,24**).

**DEUX CONTRÔLES OBLIGATOIRES**, sans lesquels l'ancre est fausse :
1. **Aucune souche du pays SOURCE dans le rayon SNP du cluster**, sinon le « foyer » n'est qu'un clone déjà
   diversifié en Afrique, importé plusieurs fois, et son MRCA est **pré-migration** (a tué l'ancre Allemagne :
   souche africaine à **0 SNP**).
2. **Multi-BioProject**, un cluster mono-BioProject est indistinguable d'un artefact de batch (a tué l'ancre
   Royaume-Uni : 17 souches, un seul PRJEB).

### ⛔ Ancres qui NE MARCHENT PAS (testées et fermées : ne pas les re-tenter)

| Ancre | Pourquoi elle échoue |
|-------|----------------------|
| **Mutation de résistance fixée dans un clade** | `tMRCA ≥ date d'introduction du médicament`, mais falsifiée par le test « diversité vs date du médicament » : le clade est bien plus divers que ne l'autorise la date. Attention aussi aux faux positifs : **gyrA 7584 (S95T) est un marqueur PHYLOGÉNÉTIQUE**, pas une résistance aux fluoroquinolones (codons 90/94). |
| **Traite atlantique / diaspora ancienne** | Le signal de diaspora observé est de la **migration MODERNE**, pas de la traite (aucune préservation type Gullah, absence des groupes attendus). |
| **Régression sur PAIRES SÉRIELLES (close-pairs)** | ⚠ **LE PIÈGE LE PLUS SÉDUISANT.** Théorie correcte (`E[d] = taux × (Δt + 2·t_coal)` → en restreignant aux paires proches, la pente de d sur Δt estime le taux ; test LOCAL, donc censé survivre à la mort du root-to-tip). **MAIS `d` et `Δt` sont corrélés par la STRUCTURE D'ÉCHANTILLONNAGE** (les prélèvements anciens viennent d'études/pays/sous-clades différents des récents) → la pente mesure le confond. **DIAGNOSTIC OBLIGATOIRE : lancer AUSSI la régression NON restreinte.** Si la pente y devient biologiquement absurde (mesuré : **3,69 SNP/génome/an**, p=1e-43, contre 0,1-0,5 attendu), le confond est prouvé et les seuils intermédiaires « significatifs » sont des artefacts. Une pente qui **dérive avec le seuil de proximité** est le signe du confond ; seul le régime le plus serré (d≤20, t_coal≈0) est interprétable, et s'il n'y a pas de signal là (mesuré : p=0,19), il n'y en a nulle part. |
| **Spoligotype ancien (Dollo)** | Deux blocages : (a) un spoligotype aDNA dégradé **mime toujours** *africanum*/*bovis* (cf. l'encadré CAUTION plus bas) ; (b) TBannotator ne donne **PAS** de spoligotype, `report.json` expose `known_coverage/DR0..DR48` mais le locus DR est à profondeur médiane **~2x** quand le génome est à 100-190x (le mapping jette les reads du DR, répétitif → filtre mapq). Vérifiable en 30 s : deux Beijing (spoligotype quasi invariant) y donnent des motifs **opposés**. Il faudrait SpoTyping/SpolPred sur les **FASTQ bruts**. |

### Borne triviale, à mentionner pour mémoire

`crown(clade) ≥ (aujourd'hui − date du plus vieux tip du clade)`, sans aucun taux. Sur des corpus MTBC modernes,
cela plafonne à 20-60 ans : **sans effet** pour trancher une question historique. Le vérifier quand même coûte une
ligne de code et évite de croire qu'on a une borne.

## Phase 2b : IQ-TREE/LSD2 (tip-dating rapide : RECOMMANDÉ en premier)

Avant BEAST, tester systématiquement IQ-TREE/LSD2 qui est 10-100× plus rapide et donne
des résultats comparables pour les analyses mono-lignée. IQ-TREE 2.3.6+ intègre LSD2.

```bash
iqtree2 -s alignment.phy -m GTR2+G \
  --date dates.tsv \
  --date-ci 100 \
  --date-options "-v 1 -r a" \
  -o outgroup1,outgroup2 \
  -T 4
```

**Format dates.tsv** : une ligne par taxon daté, format `taxon\tdate_decimal` (PAS d'en-tête numérique).

**Pour données binaires (SPDI 0/1)** : utiliser `-m GTR2+G` (modèle binaire 2 états).

**Options LSD2 clés** :
- `-v 1` : variance des branches basée sur la longueur (important pour données hétérogènes)
- `-r a` : recherche automatique de la racine sur toutes les branches
- `-u 0` : branches de longueur minimale 0 dans l'arbre temporel

### Résultat de référence : Pinnipedii (validé 2026-04-11)

| Paramètre | Valeur | IC 95% |
|-----------|--------|--------|
| Taux | 1.62 × 10⁻⁴ subst/site/an (sur 3421 sites informatifs) | [8.9 × 10⁻⁵ ; 2.6 × 10⁻⁴] |
| En SNP/génome/an | **0.55** | [0.30 ; 0.90] |
| tMRCA pinnipedii+Bovis | 153 CE | [-622 ; 672] |
| R² root-to-tip | 0.80 |, |
| Échantillon | 6 anciens (~1154-1545 CE) + 16 modernes + 3 outgroup Bovis |, |

Ce résultat sert de **référence interne** pour valider les futures datations.

## Corpus aDNA MTBC 2026 (23 génomes + 1 specimen qualitatif)

### Génomes complets intégrés dans notre pipeline v5 (9)

| Échantillon | Publication | Date | Espèce | Couverture | Emplacement | 
|-------------|------------|------|--------|------------|-------------|
| Bos 2014 ×3 | Nature 514:494 | ~1154 CE (¹⁴C) | *M. pinnipedii* | 25–44x | bdd/ancien/Pinipedii/ |
| Vågene 2022 ×3 | Nat Commun 13:1195 | 1322–1545 CE (¹⁴C) | *M. pinnipedii* | 11–15x | bdd/ancien/Pinipedii/ (BAM GitHub) |
| Kay 2015 body_68 (clean) | Nat Commun 6:6717 | ~1797 CE | *M. tuberculosis* L4 | 17.9x (déconvolué inter-L4) | bdd/ancien/M_tuberculosis_L4/ |
| Kay 2015 body_92 | Nat Commun 6:6717 | ~1797 CE | *M. tuberculosis* L4 | 240x | bdd/ancien/M_tuberculosis_L4/ |
| Sabin 2020 Winstrup | Genome Biol 21:201 | 1679 CE | *M. tuberculosis* L4 | 672x | bdd/ancien/M_tuberculosis_L4/ |

### Génomes complets publiés non intégrés (14 supplémentaires)

| Cohorte | Publication | Date | Espèce | Statut intégration |
|---------|------------|------|--------|---------------------|
| Kay 2015 ×12 autres Vác genotypes | Nat Commun 6:6717 | ~1797 CE | *M. tuberculosis* L4 | Exclus (mixed infection ou basse couverture : body 23, 25, 28, 78, 80, 121) |
| Jäger 2022 ×2 | *Tuberculosis* 135 | 18ᵉ-19ᵉ CE | *M. tuberculosis* L4 | À intégrer (midwife hongroise, mixed infection documentée) |
| Kharlamova 2023 ×~3 | [ref TBD] | 18ᵉ-19ᵉ CE | *M. tuberculosis* L4 | À intégrer (Irkutsk, Sibérie orientale) |

### Contraintes topologiques sans génome assemblé

| Source | Date | Contrainte | Usage |
|--------|------|------------|-------|
| Taylor 2007 Aymyrlyg | Âge du Fer | PCR *M. bovis* authentifié, 4 individus | Node calibration bovis |
| Müller 2014 | Médiéval UK/Europe | Spoligotypage, pas de génome | Placement topologique |
| Hershkovitz 2015 Atlit-Yam | 9 250–8 160 BP | PCR 5 loci MTBC humain + bovin, biomarqueurs mycoliques | **Node calibration clé : émergence zoonotique néolithique** |
| Molnár 2015 | 8ᵉ CE Hungary | Spoligotypage | Placement |
| Losch 2015 Guadeloupe | 18ᵉ-19ᵉ CE | Spoligotypage esclaves africains | Placement |
| Nelson 2020 | Pre-contact Andes | Spoligotypage | Placement |
| ~~Zink 2003 / Gad 2021 momies égyptiennes~~ | ~~Antiquité~~ | ~~Spoligotypage~~ | ⛔ **NE PAS UTILISER**, artefact, voir l'encadré ci-dessous |

> [!CAUTION]
> **Un spoligotype ancien DÉGRADÉ mime TOUJOURS une lignée à délétions (*africanum* / *bovis*). Ne jamais
> utiliser un spoligotype aDNA comme contrainte de calibration sans vérifier le protocole d'hybridation.**
>
> Mécanisme (établi 2026-07-11, projet `L5L6-codivergence_ethnies_ouest_afrique`, piste P3.5f) : sur ADN
> dégradé/faible copie, l'hybridation des spacers **échoue** et produit des **absences FAUSSES**. Or les motifs
> *M. africanum* et *M. bovis* **se DÉFINISSENT par des absences de spacers**. Un artefact qui fabrique des
> absences dérive donc **mécaniquement** tout motif ancien vers une signature *africanum*/*bovis*-like.
>
> Cas d'école : **Zink et al. 2003** (*J Clin Microbiol* 41:359-67) annonce une « *M. africanum*-type specific
> spoligotyping signature » dans des momies de Thèbes-Ouest du Moyen Empire (2050-1650 av. J.-C.) et en tire que
> *M. tuberculosis* dériverait d'un précurseur proche de *M. africanum*. **Réfuté par van Soolingen lui-même**
> (l'inventeur du spoligotypage) : Parwati, van Crevel, van Soolingen & van der Zanden, *J Clin Microbiol*
> 2003;41(11):5350-1, « Application of spoligotyping to noncultured *M. tuberculosis* bacteria requires an
> optimized approach » : Zink a appliqué le protocole **non optimisé** de Kamerbeek, d'où « **no hybridization
> with spacers 2, 14, and 39** ». Le protocole optimisé (van der Zanden 2002 : MgCl₂ 3,0 mM au lieu de 0,7 mM,
> Tris-HCl 15 mM au lieu de 5 mM, 20-50 pmol d'amorce) restaure le motif complet.
>
> **Conséquence : il n'existe AUCUN spécimen ancien authentifié de *M. africanum*.** La « lacune africaine » du
> corpus aDNA MTBC (23 génomes, 100 % Europe + Amérique du Sud) est **entière**, les momies égyptiennes ne la
> comblent pas. Toute lignée africaine (L5, L6, L7-L10) est donc **non calibrable en interne par aDNA** en l'état.

### Specimen qualitatif : Bison antiquus (upper bound MTBC > 17 870 BP)

| Source | Date | Preuve | Implication |
|--------|------|--------|-------------|
| Rothschild 2001 + Lee 2012 | **17 870 ± 230 BP** | PCR MTBC 2 labs indép. + lipidomique GC-MS (mycocerosates C29-C32, mycolipenates C27) | Si authentifié par re-séquençage 2025, **impose TMRCA MTBC > 18 kBP** |

Authentification pré-MapDamage → statut ouvert. Priorité R3(g) du roadmap `complex_datation/`. Notre pipeline v5 donne TMRCA 3932 BP ; si Bison authentifié, ce chiffre doit être lu comme **anchor calibré aDNA** et non comme TMRCA vrai (cf. Phase 0).

### Corpus comparateur *M. leprae* (benchmark méthodologique)

| Métrique | MTBC | *M. leprae* |
|----------|------|-------------|
| Génomes aDNA publiés 2026 | 23 | >50 |
| Continents couverts | 2 (Europe, Amérique du Sud) | 4 (Europe, Afrique N, Amériques, Pacifique) |
| Spécimen le plus ancien | ~1 000 BP (Bos 2014) | **2 200 BP** (Neukamm 2020 Ptolémaïque) |
| Hôte animal ancien séquencé | 0 | 1 (Urban 2024 écureuil médiéval) |
| Pre-Columbian humain lineage | 0 | 1 (Lopopolo 2025 *M. lepromatosis*) |
| Taux publié | $10^{-8}$ à $5 \times 10^{-7}$ | $6 \times 10^{-9}$ à $2 \times 10^{-8}$ (branche-dépendant) |
| Seuil critique de diversité | **Non franchi** (23 génomes) | Franchi en 2018–2021 |

**Leçon pour le MTBC** : notre corpus est sous-seuil critique. Schuenemann 2018 a montré que 10 génomes supplémentaires suffisent à révéler 4 branches coexistantes dans un cimetière médiéval unique ; Pfrengle 2021 en doublant le corpus a exposé une diversité ibérique insoupçonnée. Le MTBC à 23 génomes attend le même saut qualitatif.

### Trois transferts méthodologiques *M. leprae* → MTBC

1. **Corpus inflation** (Schuenemann 2018, Pfrengle 2021) : ajouter 20–30 génomes MTBC change qualitativement l'inférence.
2. **Animal hosts séquençables** (Urban 2024, 2.2× coverage sur écureuil médiéval) : restes archéologiques bovins/caprins/pinnipèdes sont des cibles tractables.
3. **Pre-Columbian screening humain** (Lopopolo 2025 sur 389 spécimens) : MTBC humain-adapté pré-1492 aux Amériques reste non testé.

**Attention aDNA** : les anciens traités par TBannotator sur des runs individuels à basse couverture (<10x) produisent des SPDI artefactuels (0.4% d'overlap avec la référence). Toujours utiliser les BAM **fusionnés** par les auteurs originaux (GitHub, supplementary data) avec un variant calling adapté (bcftools, QUAL≥30, DP≥3).

### Contraintes temporelles dérivées de phylogénies récentes (TMRCA-as-prior)

Lorsqu'une analyse antérieure a fourni une estimation TMRCA sur un sous-clade donné, cette borne peut être réutilisée comme **prior souple** (BEAST2 `MRCAPrior`) ou **soft constraint** (LSD2 `-g`) pour des analyses ultérieures qui contiennent ce même sous-clade dans la phylogénie. Pratique pour : (a) accélérer la convergence MCMC en pinning un nœud bien contraint, (b) propager les calibrations établies à travers les sous-projets.

| Sous-clade | TMRCA estimé | Méthode | Source | Statut | Usage recommandé |
|---|---|---|---|---|---|
| **L4.6.2.2 Madagascar (6 souches)** | **1750-1900** (CI large) | Monophylie + Hamming pairwise SPDI bruts + taux Menardo 0.5 SNP/an | Guyeux 2026-05-16 (`musee_de_lhomme/experiments/2026-05-16_l462_madagascar_dating/`) | **Préliminaire** (RAxML+BIN+G, R² treetime 0.01-0.03, non filtré IS/PE/PPE) | Prior log-normal centré 1850 sigma 75 ans pour BEAST2 MRCAPrior sur clade Mad ; soft constraint LSD2 `-g constraints.txt` avec ligne `node Madagascar 1750 1900` |
| L4.11 (Bangladesh MDR + Pérou) | ~1965 (95% CI 1560-1996) | TempEst R²=0.008 (signal faible) | projet `methodology/`, claim_check #23 (2026-04-05) | Validé pour Discussion uniquement | Borne molle (CI très large) ; ne pas utiliser comme contrainte forte |

**À enrichir au fil des projets.** Quand un projet publie ou consolide une estimation TMRCA, l'ajouter au tableau avec : source, méthode, statut (préliminaire / validé / publié), et le format de contrainte recommandé pour BEAST2/LSD2.

**Format BEAST2** (MRCAPrior dans le XML) :
```xml
<distribution id="L462MadCladePrior" spec="beast.math.distributions.MRCAPrior"
              tree="@Tree" monophyletic="true">
  <taxonset id="L462Mad">
    <taxon idref="ERR9030369"/>
    <taxon idref="ERR9030445"/>
    <taxon idref="ERR9030448"/>
    <taxon idref="ERR9030396"/>
    <taxon idref="ERR9030536"/>
    <taxon idref="ERR9030291"/>
  </taxonset>
  <Normal mean="1850.0" sigma="75.0" offset="0"/>
</distribution>
```

**Format LSD2** (fichier `constraints.txt` passé à `--date-tip 0 -g constraints.txt`) :
```
L462Mad_node ERR9030369 ERR9030445 ERR9030448 ERR9030396 ERR9030536 ERR9030291 b(1750,1900)
```

**Caveat à toujours signaler** : les TMRCA préliminaires sur SPDI brutes sont gonflés d'un facteur 1.3-2 par les régions IS/PE/PPE. Le TMRCA réel après filtrage est typiquement plus tardif (vers la borne haute). Quand on utilise une de ces contraintes, ne pas oublier de la marquer "preliminary, awaiting BEAST2 propre confirmation" dans le manuscrit final.

## Pièges découverts (sessions 2026-04-11/12)

| Piège | Symptôme | Solution |
|-------|----------|----------|
| **TBannotator sur ADN ancien** | 0.4% d'overlap SPDI entre runs séparés et référence | Utiliser les BAM fusionnés des auteurs, pas TBannotator |
| **Dates BioSample H37Rv** | Variance intra-année >> inter-année (2-50 SNP en 2021) | Inutilisable sans historique de passage documenté |
| **Souches "1905" colombiennes** | 800-870 SNP au lieu de <100 | Isolats cliniques L4.9 mislabelés, pas des stocks Koch |
| **Strict clock inter-espèces** | LSD2 + BEAST2 échouent (taux borne inf, tree height bloqué) | Relaxed clock OU filtrer substitutions synonymes |
| **dataType="binary" BEAST2 v2.7** | ClassNotFoundException | Convertir 0→A, 1→T + JukesCantor (équivalent) |
| **Fusion de runs avec mixed infection** | Couverture ×30 → tMRCA décalé de +2000 ans | Utiliser 1 run (génotype dominant) ou déconvoluer séparément. Vérifier la publication pour mixed infection documentée (Kay 2015 Vác body 68, body 80). |
| **Process substitution zcat en background** | BWA produit BAM vide sans erreur | Aligner les runs séparément et `samtools merge` |
| **Concaténation FASTQ pour merge** | Double l'espace disque (OOM) | Aligner séparément puis merger BAMs |
| **`gio trash` vs vraie suppression** | Espace disque ne se libère pas | `gio trash --empty` nécessaire |
| **Délétion (RD) codée `0`/REF au lieu de `?`** | Branches des clades délétés gonflées, nœuds profonds rajeunis, CI dégradés | Coder `?` per-souche aux RD fixées du clade (voir sous-section ci-dessous) |

### Préparation de l'alignement : délétions (RD) en données MANQUANTES, pas en état ancestral

**Le piège.** Une région délétée (RD) chez une souche n'a pas de séquence à comparer : c'est une donnée **MANQUANTE** (`?`/`N`), PAS l'état de référence. Dans une **matrice binaire présence/absence de SPDI** (`"1" if spdi∈profil else "0"`), une souche ayant délété une zone ne porte aucun SPDI de la zone → elle est codée **`0` = état ancestral** alors qu'elle devrait être `?`. Quand un clade a acquis un variant (1) et qu'une fille délète la région → **fausse réversion 1→0** → branche terminale gonflée (en BIN, chaque délétion couvrant un site informatif = un faux changement d'état). Effet : clades délétés → taux apparent local surestimé → nœuds **rajeunis** + CI dégradés. Quantifié sur *M. bovis* : **~10 % des sites variables** de l'alignement de datation tombent dans une vraie RD de délétion ; le masque `traces_mask` n'en couvre que ~30 %.

**Pourquoi c'est CRITIQUE à l'échelle MTBC.** H37Rv = L4 → toute lignée éloignée (animales, L5/L6, L2-Beijing avec RD105/RD207, L1 avec RD239) porte ses RD propres → le biais frappe **toutes les branches inter-lignées profondes** (celles du débat 70 vs 6 kya), couplé au biais de référence (les lignées loin de H37Rv ont plus de positions « absentes »).

**Remède (par rigueur croissante).**
1. *Rigoureux (recommandé)* : coder `?` **per-souche** aux positions des RD **fixées** du clade de la souche. RAxML BIN ignore les `?`. Source = `global_supplementary/traces_mask/clade_rd.pkl` (curé : clade→RD), **JAMAIS** `report.json missing_rd` (97 % d'artefacts `CUS_GS` + 30 % de faux négatifs per-souche).
2. *Simple* : masquer globalement les positions des vraies RD de délétion (perte ~10 % des sites).

**Caveat `rd.bed` hétérogène** : il mélange vraies délétions de clade et grandes régions de **contexte** (`DS6` = 1543306-1998604 = **455 kb**, 10 % du génome, PAS une délétion) → filtrer les vraies délétions (≤50 kb) avant tout masquage, sinon on jette des milliers de SNP légitimes.

**Ne pas mélanger les horloges** : la délétion est **un événement Dollo** (≠ N substitutions) → horloge séparée du SNP, jamais comptée comme N réversions. Outil de quantification : `Bovis_emergence/analyses/check_rd_mask_overlap.py` (recouvrement RD ∩ masque ∩ alignement).

## Phase 3 : Préparation BEAST

### Fichier de dates

```csv
strain_id,date
ERR551415,2015.5
SRR33638270,2018.0
DRR261083,2012.75
```

Format décimal : 2015.5 = juillet 2015. Pour dates exactes : année + (mois-1)/12 + (jour-1)/365.

### Paramètres BEAST recommandés pour MTBC

| Paramètre | Valeur recommandée | Justification |
|-----------|-------------------|---------------|
| Modèle de substitution | GTR+G (ou HKY+G pour rapidité) | Standard MTBC |
| Horloge | **UCLD** (uncorrelated lognormal) | Variation de taux entre branches |
| Prior sur le taux | LogNormal(mean=5e-8, stdev=1.0) | ~0.5 SNP/site/an pour MTBC |
| Tree prior | **Coalescent Skyline** | Capture la dynamique démographique |
| Chaîne MCMC | 100M-500M selon n | Vérifier ESS > 200 |
| Échantillonnage | every 10000 | Mémoire raisonnable |
| Burn-in | 10-20% | Vérifier convergence dans Tracer |

### Prior sur le taux de mutation MTBC

Taux publiés (SNP/site/an) :

| Étude | Lignée | Taux | IC95 |
|-------|--------|------|------|
| Ford et al. 2011 | L4 | 4.6e-8 | 3.3-6.0e-8 |
| Menardo et al. 2019 | MTBC global | 3.0-5.0e-8 |, |
| Bos et al. 2014 | Ancien MTBC | ~2.0e-8 |, |
| Comas et al. 2013 | MTBC global | 4.3e-8 | 2.9-5.7e-8 |

**Conversion** : 1 SNP/génome/an ≈ 2.3e-7 SNP/site/an (génome MTBC ~4.4 Mb).

> ⚠️ **Alignement SNP-only → correction d'ascertainment OBLIGATOIRE dans BEAST.** Si on donne à BEAST un
> alignement de sites variables seulement (cas le plus fréquent en MTBC), il surestime le taux par site et
> **compresse les dates vers le présent** (vu : MRCA *M. bovis* tiré de ~835 BCE à ~1390 CE). La bonne
> correction n'est PAS le conditionnement de Felsenstein (fragile, plante le likelihood threadé) mais l'input
> **`siteWeights`** d'`Alignment` : préfixer 4 colonnes constantes A,C,G,T pondérées par le vrai nombre de sites
> invariants de chaque base (SNP à poids 1) → BEAST modélise le génome complet, taux et dates corrects. Impose
> `TreeLikelihood` simple (pas `ThreadedTreeLikelihood`). Recette headless complète + gotchas (Java 23, `setsid`,
> ne pas juger en burn-in) dans le skill **`beast2-phylogeography`** ; implémentation testée dans
> `mtbc/Bovis_emergence/analyses/build_beast_*.py`.

### Script de génération BEAST XML

```bash
python3 scripts/molecular_clock.py beast-xml tree.nwk dates.csv \
  --clock ucld --tree-prior skyline \
  --rate-prior "lognormal(5e-8,1.0)" \
  --chain-length 100000000 \
  -o analysis.xml
```

## Phase 3b : Approche synonymes-only (RECOMMANDÉ pour inter-lignées)

La sélection purifiante crée une hétérotachie apparente entre lignées MTBC (taux
non-synonymes varie selon la pression de sélection, hôte, taille de population).
Les substitutions synonymes, neutres par définition, évoluent de manière plus
homogène → le strict clock converge sur inter-lignées.

### Procédure

1. **Annoter les SPDI** : pour chaque souche avec `report.json` TBannotator, extraire
   les SPDI annotés `synonymous_variant`. Pour les souches sans report.json (bcftools),
   annoter manuellement avec le GenBank H37Rv (NC_000962.3.gb) :

```python
from Bio import SeqIO
from Bio.Seq import Seq

record = SeqIO.read("NC_000962.3.gb", "genbank")
ref_seq = str(record.seq)
cds = [(int(f.location.start), int(f.location.end), f.location.strand) 
       for f in record.features if f.type == "CDS"]

def is_synonymous(pos_0, ref_a, alt_a):
    for start, end, strand in cds:
        if start <= pos_0 < end:
            if strand == 1:
                cp = (pos_0 - start) % 3
                cs = pos_0 - cp
                codon_ref = ref_seq[cs:cs+3]
                codon_alt = list(codon_ref); codon_alt[cp] = alt_a
            else:
                cp = (end - 1 - pos_0) % 3
                ce = pos_0 + cp + 1
                cs2 = ce - 3
                codon_ref = str(Seq(ref_seq[cs2:ce]).reverse_complement())
                fc = list(ref_seq[cs2:ce]); fc[pos_0-cs2] = alt_a
                codon_alt = list(str(Seq(''.join(fc)).reverse_complement()))
            return str(Seq(codon_ref).translate()) == str(Seq(''.join(codon_alt)).translate())
    return False
```

2. **Construire la matrice binaire synonymes** : seuls les sites `synonymous_variant`.
   Attendu : ~29% des SPDI sont synonymes.

3. **IQ-TREE/LSD2** comme en Phase 2b, sur les sites synonymes uniquement.

## Script pipeline v5 réexploitable

Un script Python encapsule tout le workflow v5 :

```bash
# Mode single-seed (reproductible, mais dépendant de l'échantillonnage aléatoire)
python3 scripts/molecular_clock_pipeline.py \
  --output résultats/my_analysis \
  --seed 2026

# Mode multi-seed RECOMMANDÉ — lance N runs, conserve le meilleur selon objective function
python3 scripts/molecular_clock_pipeline.py \
  --output résultats/my_run \
  --multi-seed 10

# Options complètes
python3 scripts/molecular_clock_pipeline.py \
  --output résultats/my_run \
  --bdd /path/to/bdd \
  --lineages L4.1,L4.3.3,L4.8,L4.2.1,L4.7.1,L4.7.2 \
  --n-per-lineage 5 \
  --n-h37rv 50 \
  --n-outgroup 3 \
  --outgroup-lineage Bovis \
  --multi-seed 10 \
  --iqtree /path/to/iqtree2 \
  --threads 4
```

**Résolution automatique du binaire iqtree2** : si `--iqtree` n'est pas fourni, le script cherche dans l'ordre (1) `<script>/../../investigate_phylo/iqtree2` (contexte projet MTBC), (2) `~/docs/codes/mtbc/investigate_phylo/iqtree2`, (3) `iqtree2` ou `iqtree` dans `$PATH`.

**Défauts mis à jour (2026-05-31)** : `--lineages L4.1,L4.3.3,L4.8,L4.2.1,L4.7.1,L4.7.2` (L4.7 a été divisée en L4.7.1 et L4.7.2 dans `bdd/actuelle/`), `--outgroup-lineage Bovis` (racine *M. bovis* réelle, ~1417 souches ; les anciens noms `Bovis_La1`/`Bovis2_La1` n'existent plus dans `bdd/actuelle/`, toujours vérifier le nom de dossier contre `bdd/actuelle/`, cf. `SOURCES_OF_TRUTH.md`).

**Taille minimale recommandée** : `--n-per-lineage 5 --n-h37rv 50`. Sur un échantillon plus réduit (ex. 3 par lignée, 20 H37Rv), les tMRCA sortent souvent hors plage plausible (>8000 BP) à cause d'un sampling insuffisant, CV inter-seed peut dépasser 40%.

**Phases du pipeline** :
1. Collect 9 anciens pré-curés depuis `bdd/ancien/`
2. Sample moderns + H37Rv stocks (<100 SNP) depuis `bdd/actuelle/`
3. Extract synonymes via TBannotator report.json ou spdi_syn.txt
4. Build binary PHYLIP + LSD2 dates avec `b(min,max)` + MRCA H37Rv
5. Run IQ-TREE/LSD2 tip-dating (single ou multi-seed)
6. Parse résultats → JSON résumé (multi-seed : sélection automatique du meilleur)

**Sortie** :
- Single-seed : `{prefix}.{phy,simple.dates,lsd2.dates,mrca,treefile,timetree.lsd,summary.json}`
- Multi-seed : idem pour chaque run (`{prefix}.seed_<N>.*`) + `{prefix}.multi_seed_summary.json` avec tous les runs et le meilleur sélectionné.

### Critère de sélection multi-seed : objective function

LSD2 rapporte dans `.timetree.lsd` une **objective function** qui mesure le fit du dating (résidus au modèle strict clock). **Règle impérative** : rapporter le run de **plus faible objective function**, pas la moyenne. La moyenne est tirée par les mauvais fits et biaise vers des tMRCA plus anciens.

**Variance inter-seed réelle** : CV ≈ 36% sur le taux (test 10-seeds, 2026-04-12). Cette variance provient du sampling aléatoire des modernes L4 : la structure phylogénétique du sous-échantillon influence le clock. Un mode multi-seed avec N ≥ 10 est **obligatoire** pour un résultat publiable.

**Corrélation observée** : meilleur fit (obj bas) → tMRCA plus récent → meilleure cohérence avec la littérature publiée.

### Résultat de référence v5 multi-seed (validé 2026-04-12)

Meilleur run sur 10 seeds aléatoires (seed retenu : 927067) :

| Paramètre | Valeur | IC 95% |
|-----------|--------|--------|
| Taux synonyme | 7.40 × 10⁻⁵ subst/site/an (1654 sites) | [5.01 × 10⁻⁵ ; 9.16 × 10⁻⁵] |
| **Taux génome complet** | **2.82 × 10⁻⁸ subst/site/an** |, |
| **tMRCA (Pinni+L4)** | **3932 BP** | [3115 ; 6024 BP] |
| Objective function | **0.508** (meilleur fit de toutes les versions) |, |
| Échantillon | 102 souches (9 anciens + 50 H37Rv + 25 L4 mod. + 16 Pinni mod. + 3 Bovis OG) |, |

**Historique des versions de référence** (cohérentes entre elles) :
- v5 manuel (dataset figé, 2026-04-12) : 2.61 × 10⁻⁸, 4219 BP, obj=0.512
- v5 multi-seed pipeline (2026-04-12) : **2.82 × 10⁻⁸, 3932 BP, obj=0.508** ⭐

**Robustesse leave-one-out v5** : CV taux = 13.6%, dépendance max à un seul ancien = +21.7% (Bos58). **Aucun calibrateur ne domine**, c'est le signe d'un dataset vraiment robuste, contrairement à v2 où Winstrup dominait (+71%).

**Vs littérature** :
- Bos 2014 : ~2.0 × 10⁻⁸ → notre 2.61 × 10⁻⁸ (+30%)
- Sabin 2020 : 2190-4501 BP → **overlap direct** avec notre IC [3265;6354] BP
- Menardo 2019 : ~3000 BP → **dans notre IC**
- Comas 2013 : ~70 000 BP → toujours exclu

**Évolution historique** :
- v1 (72 taxa, 8 anciens, 20 H37Rv) : 2.68 × 10⁻⁸, 4011 BP
- v2 (102 taxa, 8 anciens, 50 H37Rv) : 2.36 × 10⁻⁸, 4475 BP
- v3 (+ Body 92) : 2.11 × 10⁻⁸, 5146 BP
- v4 (Body 68 raw, CHIMÉRIQUE) : 1.42 × 10⁻⁸, 7907 BP ⚠ contamination mixed infection
- **v5 (Body 68 CLEAN, L4-validé)** : **2.61 × 10⁻⁸, 4219 BP** ⭐

**Filtrage Body 68 mixed infection** (clé de v5) :
Kay 2015 a documenté que body 68 contient 2 génotypes (B68-1 L4.1.2.1 à 332x + B68-2 L4.7 à 253x). Fusionner les 3 runs donne un profil SPDI chimérique. Solution : filtrer les SNP de body 68 par **cohérence inter-L4**, ne garder que ceux partagés avec Winstrup ou Body 92 (qui sont L4 propres). Approche alternative à la déconvolution par allele frequency de Kay 2015 quand le BAM n'est pas disponible.

Compatible avec Sabin 2020, Bos 2014, Menardo 2019. Exclut Comas 2013 (70 000 BP).

### Calibrations disponibles

| Source | Type | Date | Usage |
|--------|------|------|-------|
| Bos 2014 (3 pinnipedii) | Tip date ¹⁴C | `b(1028,1280)` | Ancrage profond pinnipedii |
| Vågene 2022 (3 pinnipedii) | Tip date ¹⁴C | `b(1250,1470)` etc. | Étage intermédiaire |
| Winstrup (Sabin 2020) | Tip date historique | `1679` | Ancrage L4 |
| Body 68 (Kay 2015) | Tip date historique | `b(1731,1838)` | Second ancrage L4 |
| **H37Rv stocks** | **Contrainte nodale** | **MRCA = `b(1900,1910)`** | Ancrage L4.9 (1905) |
| **MRCA(BCG vaccinal)** | **Contrainte nodale** | **`b(1908,1921)`** | Ancrage Bovis1.2.1 (Pasteur strain divulguée 1921 ; passages CG dès 1908) |
| **MRCA(proto-BCG ∪ BCG)** | **Contrainte nodale** | **`b(1880,1908)`** | Souche-source Nocard 1902 isolée de mammite tuberculeuse à Garches ; le MRCA avec la pop sauvage parente est borné supérieurement à 1908 (début Calmette-Guérin), inférieurement par l'estimation antérieure raisonnable |
| **BCG sub-souches** | **Tip dates historiques** | dates individuelles | Russia 1924, Tokyo 1924, Sweden 1926, Moreau 1925, Phipps 1928, Birkhaug 1929, Danish 1931, Frappier 1937, Connaught 1948, Glaxo 1954 (Behr&Small 1999, Brosch 2007) |
| Modernes datés | Tip date BioSample | variable | Ancrage récent |

### Ancres de résistance : borne supérieure datée, multipliable par lignée

**Principe.** Une mutation de résistance **fixée** dans un clade monophylétique implique `tMRCA(clade défini par R) ≥ date d'introduction clinique de l'antibiotique` → **BORNE SUPÉRIEURE sur l'âge du nœud** (le clade « n'est pas plus vieux que » le médicament), posée sur le MRCA de la nouveauté (pas sur la divergence avec la sœur sensible, qui est antérieure). Levier décisif : **chaque lignée humaine a ses propres clones MDR/XDR récents** → ancres récentes INDÉPENDANTES par lignée, qui contraignent le taux RÉCENT lignée par lignée (le haut de la courbe TDRP) ; combinées aux ancres aDNA profondes, elles tiennent les deux bouts → lèvent l'identifiabilité taux↔temps.

| Antibiotique | Intro. clinique TB | Gène(s), mutation causale | Borne |
|---|---|---|---|
| streptomycine | 1944 | rpsL, rrs, gid | tMRCA ≥ 1944 |
| isoniazide | 1952 | katG (S315T), fabG1/inhA | ≥ 1952 |
| éthambutol | 1961 | embB (M306) | ≥ 1961 |
| **rifampicine** | **1968** | **rpoB (RRDR)** | **≥ 1968, l'ancre reine (MDR)** |
| fluoroquinolones | ~1985 | gyrA (A90V, D94G), gyrB | ≥ 1985 (pré-XDR/XDR) |
| bédaquiline | 2012 | Rv0678, atpE, pepQ | ≥ 2012 (calibre le taux moderne) |

**Garde-fous obligatoires.** (1) **Monophylie vérifiée par ACR/PastML** : les loci de résistance sont les plus homoplastiques du génome (katG S315T, rpoB S450L = des centaines d'origines indépendantes) → sans origine unique dans le sous-arbre, PAS d'ancre. (2) Borne **molle** (standing variation possible). (3) Mutation **causale** seule (pas compensatoire rpoC/rpoA ni co-résistance MDR co-transmise). (4) **Masquer** ces positions du calcul de longueur de branche (homoplasie) même quand on les utilise comme ancre topologique.

**PIÈGE résistance intrinsèque (*M. bovis*).** La résistance au pyrazinamide de *M. bovis* (`pncA` H57D, marqueur d'espèce) est **ANCESTRALE**, la traiter comme ancre daterait le MRCA bovis à ≥1952 (absurde). Plus largement, les ancres de résistance marchent **mal** pour *M. bovis* (réservoir abattu, non traité → peu de résistance acquise) ; bovis est ancré par l'HÔTE (BCG, spillovers, criollo). **Les deux familles d'ancres se relaient selon le clade** : résistance ↔ lignées humaines traitées, événements-hôte ↔ bovis/animal.

Catalogue : `MTBC-constrained-node-dating/data/antibiotic_introduction_anchors.tsv` (18 antibiotiques). Skill `resistance-profiler` pour annoter les profils de résistance des souches avant l'ACR.

### Note : BCG comme ancrage historique unique en MTBC

Le complexe BCG constitue un **système modèle exceptionnel** pour la calibration phylogénétique MTBC parce que :

1. **Le MRCA est daté avec quasi-certitude historique** (1908-1921) : les sous-souches mondiales sont toutes issues d'une lignée propagée par Calmette-Guérin à l'Institut Pasteur de Lille à partir de 1908, et distribuée internationalement à partir de 1921 (Pasteur strain). Pas d'analyse phylogénétique nécessaire pour ce nœud, c'est de l'histoire des sciences documentée.
2. **Chaque sous-souche vaccinale a une date d'isolement publiée** (cf. table ci-dessus), donc tip dates fiables.
3. **Une population sauvage parente est disponible** à la base du clade `Bovis1.2.1.BCG` (souches françaises Bos taurus 1999-2009, RD1 intact, basales aux sous-souches vaccinales RD1-délétées ; l'ancien nom de dossier `Bovis1.2.1.proto-BCG` a été fusionné dans `Bovis1.2.1.BCG`), qui donne le deuxième nœud calibré.
4. **Sur l'arbre Bovis1, ces deux nœuds sont *enchâssés***, ce qui contraint très fortement le taux de substitution local et permet une **validation en aveugle de l'horloge moléculaire** : si l'algorithme retrouve 1921 ± qq années pour le MRCA des sous-souches BCG en utilisant uniquement les tips datés du reste de l'arbre, c'est une démonstration spectaculaire de la précision de la méthode.

Format LSD2/TreeTime pour ces contraintes :

```text
# mrca_constraints.txt (LSD2 via -g)
mrca(BCG_Pasteur_CUS...,BCG_Russia_CUS...,BCG_Tokyo_CUS...,...) b(1908,1921)
mrca(BCG_*,SRR7851309,SRR7851316,SRR7851346,SRR7851359) b(1880,1908)
```

```python
# TreeTime via --clade-dates clades.tsv :
# node_name<TAB>date_or_range
BCG_vaccinal_MRCA	1921
proto_BCG_BCG_MRCA	1908
```

### Commande complète (pipeline validé)

```bash
# 1. IQ-TREE sur l'alignement synonymes
iqtree2 -s alignment_syn.phy -m GTR2+G \
  --date dates_midpoints.tsv \
  --date-ci 100 \
  --date-options "-v 1 -r a -d dates_with_uncertainty.tsv -g mrca_constraints.txt" \
  -o outgroup1,outgroup2 \
  -T 4

# Format dates_with_uncertainty.tsv (pour LSD2 via -d) :
#   72              ← nombre de taxons datés
#   SRR1238557  b(1028,1280)
#   Winstrup    1679
#   ERR551134   2018

# Format mrca_constraints.txt (pour LSD2 via -g) :
#   mrca(H37Rv_SRA1,H37Rv_SRA2,...) b(1900,1910)
```

### Topologie MTBC de référence (indispensable pour choisir les calibrateurs)

```
M. canettii (outgroup)
├── Clade humain strict
│   ├── L1, L7
│   └── L2, L3, L4
└── Grand clade
    ├── L5  ← basale du grand clade
    └── [écotypes animaux paraphylétiques + lignées secondairement humaines]
            ├── L6, L9, L10  (secondairement humains, imbriqués)
            └── Bovis, Caprae, Microti, Pinnipedii, Mungi, Surricatae,
                Chimpanzee, Orygis, Dassie bacillus  (paraphylétiques)
```

**Conséquence directe** : les calibrateurs pinnipedii anciens (Bos 2014, Vågene 2022)
calibrent des nœuds *dans* le grand clade. Ils sont donc :
- **Très utiles** pour dater L5, L6, L9, L10 (même grand clade, distance phylogénétique courte)
- **Peu utiles** pour dater L4, L1, L2, L3 (clade humain strict séparé, calibration traverserait la
  divergence profonde entre les deux grands clades, propageant une incertitude massive)

### Principe : un calibrateur contraint un taux, pas un nœud cible

Erreur fréquente : penser qu'un calibrateur doit être *sur la branche* qu'on veut dater. Faux.
En tip-dating, un ancien daté contraint le **taux de substitution** dans son contexte
phylogénétique. Sous horloge stricte, ce taux s'applique à toutes les branches du clade.
Sous horloge relaxée, il informe la distribution de taux à laquelle les branches sœurs sont
soumises. **Il est donc presque toujours préférable d'inclure les anciens disponibles dans
le clade cible plutôt que de retomber sur un prior MTBC global**, qui mélange clade humain
strict et grand clade, deux dynamiques évolutives distinctes.

### Stratégie de calibration par lignée

| Lignée | Grand clade ? | Calibrateurs recommandés | Stratégie |
|--------|:---:|--------------------------|-----------|
| **Toute lignée L4 (L4.1 → L4.10, y compris sous-lignées comme L4.6.2)** | Non | **Winstrup 1679 + body_68 ~1797 + H37Rv MRCA 1905** | Tip-dating L4 + node H37Rv. Les anciens n'ont **pas besoin d'être sur la branche cible** : ils calibrent le taux L4, qui s'applique à toute sous-lignée L4 sous horloge relaxée. Inclure quelques L4 représentatifs pour ancrer la position des anciens dans l'arbre. |
| L5 | Oui (basal) | Pinnipedii anciens (Bos 2014 ×3, Vågene 2022 ×3) + bovis/caprae contexte | Tip-dating dans grand clade |
| L6 | Oui (imbriquée) | Pinnipedii anciens, calibration quasi-directe si L6 sœur d'un clade proche | Tip-dating dans grand clade |
| L9, L10 | Oui (imbriquées) | Pinnipedii anciens + bovis/caprae contexte | Tip-dating dans grand clade |
| L1, L2, L3, L7 | Non | Aucun ancien disponible dans le clade humain strict | Prior Menardo OU node calibration historique (ex. expansion L2 Beijing ~200-400 ans) |
| **Fallback ultime (toutes lignées)** |, | Prior Menardo seul + outgroup biologique | Uniquement si l'inclusion des anciens du clade est impossible (échantillon trop restreint, contrainte computationnelle, topologie incompatible). À documenter explicitement comme limitation. |

**Caveat pour L5/L6/L9/L10** : les écotypes animaux ont potentiellement des taux de substitution
différents des lignées humaines (dynamique de transmission, hôte, pression sélective). Utiliser
une horloge relaxée (LSD2 multi-rate ou BEAST2 UCLD) et valider par leave-one-out en vérifiant
que les branches animales ne sont pas aberrantes.

**Cas L4.6.2, version actuelle vs version améliorée recommandée (2026-04-13)** :

| Setup | Composition | Calibration | Résultat |
|-------|-------------|-------------|----------|
| Actuel (sous-optimal) | 498 L4.6 + 13 L4.6.1 outgroup | Prior Menardo seul | Split L4.6 = 560 CE [381;671], MRCA L4.6.2 = 723 CE [608;798], UFBoot 100/100 |
| **Recommandé** | 498 L4.6 + 13 L4.6.1 outgroup + Winstrup + body_68 + quelques L4 représentatifs (L4.1, L4.7) | **Tip-dating sur Winstrup 1679 + body_68 ~1797** + H37Rv node si applicable | Attendu : intervalles plus resserrés, calibration sur des dates XVIIᵉ-XVIIIᵉ historiquement validées plutôt que sur un prior global |

La branche L4.6 elle-même ne porte pas d'ancien, mais le taux L4 estimé depuis Winstrup + body_68
s'applique à L4.6 sous horloge relaxée. C'est nettement plus défendable que le fallback prior
seul, qui devrait être réservé aux cas où l'inclusion des L4 anciens est impossible.

### Limitation fondamentale (révisée)

Couverture des calibrateurs disponibles, par grand clade :

- **Clade humain strict (L1, L2, L3, L4, L7)** : calibrateurs uniquement pour L4 (Winstrup 1679,
  body_68 ~1797, H37Rv MRCA 1900-1910). Le taux estimé depuis ces L4 anciens s'applique à
  toute sous-lignée L4 sous horloge relaxée, y compris L4.6, L4.11, L4.15, etc., moyennant
  l'ajout de quelques L4 représentatifs pour ancrer leur position dans l'arbre. Pour L1, L2, L3,
  L7 : aucun ancien disponible, fallback prior Menardo ou node calibration historique.
- **Grand clade (L5, L6, L9, L10 + écotypes animaux + pinnipedii)** : 6 pinnipedii anciens
  (Bos 2014 ×3, Vågene 2022 ×3, ~1154-1545 CE). Le taux estimé s'applique à toute lignée du
  grand clade sous horloge relaxée, sous réserve de valider que les branches animales ne sont
  pas aberrantes (leave-one-out).

**Règle pratique** : avant de basculer sur un prior externe, toujours vérifier si la lignée
cible appartient à un clade qui contient des anciens utilisables. Le prior seul est un
fallback, pas un défaut.

Ajouter des lignées sans calibration dans un arbre dégrade le résultat (taux borne inf.).

## Phase 4 : Calibrations alternatives

### Node calibration (événements historiques)

| Événement | Date estimée | Usage |
|-----------|-------------|-------|
| Divergence humains/animaux | ~6000-70000 ans | Racine MTBC |
| Expansion L4 (colonisation européenne) | ~500-1000 ans | Nœud L4 |
| Émergence Beijing (L2.2.1) | ~200-400 ans | Nœud L2.2.1 |
| Expansion M. bovis (domestication) | ~10000 ans | Nœud clade animal |

### Multi-contrainte

Combiner tip-dating + node calibration pour surmonter le signal faible :

```xml
<!-- Tip dates -->
<taxa id="date_ERR551415"><date value="2015.5" direction="forwards" units="years"/></taxa>

<!-- Node calibration: MRCA of all L4 -->
<tmrcaStatistic id="tmrca_L4">
  <mrca><taxa idref="L4_taxa"/></mrca>
</tmrcaStatistic>
<uniformPrior lower="500" upper="2000" />
```

## Phase 4b : Validation leave-one-out (RECOMMANDÉ)

Avant de publier un taux ou un tMRCA, toujours vérifier la robustesse :

```bash
python3 analyses/phase3_leave_one_out.py
```

Le script retire chaque ancien un par un, relance IQ-TREE/LSD2, et produit un tableau comparatif.

### Critères de robustesse

| Critère | Seuil | Interprétation |
|---------|-------|----------------|
| Δ taux par ancien | < 15% | ✓ Robuste, signal distribué |
| Δ taux par ancien | 15-50% | ⚠ Ancien influent, documenter |
| Δ taux par ancien | > 50% | ✗ Fragile, calibration insuffisante sur cette branche |
| Toutes les analyses convergent | taux > 1e-9 | ✓ Le modèle tient sans chaque ancien |

### Résultat de référence v5 (2026-04-12, dataset final)

Leave-one-out sur les 9 anciens de v5 :

| Calibrateur retiré | Δ taux | Δ tMRCA |
|--------------------|--------|---------|
| SRR1238557 (Bos) | −8.5% | −460 ans |
| SRR1238558 (Bos) | +21.7% | +667 ans |
| SRR1238559 (Bos) | −3.7% | −388 ans |
| Vagene2022_S82 | −5.2% | −170 ans |
| Vagene2022_S281 | +10.6% | +385 ans |
| Vagene2022_S386 | +2.4% | +113 ans |
| Winstrup_LUND1 | +5.3% | +252 ans |
| Body68_Kay2015_clean | −24.1% | −1212 ans |
| Body92_Kay2015 | +15.7% | +531 ans |

- **CV taux inter-LOO** : 13.6%
- **Δ taux max** : +21.7% (Bos58), bien sous le seuil critique 50%.
- **Distribution uniforme** : aucun calibrateur ne domine (contrairement à v2 où Winstrup dominait à +71%).
- **Conclusion** : dataset **robuste**, publiable.

**Historique de stabilité** :

| Version | CV taux | Max Δ taux | Statut |
|---------|---------|-----------|--------|
| v2 | 24.6% | +71.8% (Winstrup) | Fragile sur L4 |
| v3 | 17.2% | +51.1% (Body92) | Dépendant Body92 |
| v4 | 36.3% | +112% (Body92) | Instable (Body68 chimérique) |
| **v5** | **13.6%** | **+21.7% (Bos58)** | **Référence finale** |

## Phase 4c : Validation TDRP formelle par bootstrap (RECOMMANDÉ pour TMRCA > 5 000 BP)

Après le tip-dating LSD2, si le TMRCA rapporté excède 5 000 BP **ou** si l'on veut formellement exclure une hypothèse long-clock concurrente (Comas 2013, Wirth 2008), le tip-dating seul ne suffit pas : il faut projeter son taux calibré aDNA dans un fit TDRP joint MTBC+leprae bootstrap pour borner l'envelope.

### Procédure

1. **Récupérer le taux génome calibré** de son analyse LSD2 (ex. $2.82 \times 10^{-8}$ pour v5).
2. **Injecter comme anchor dans le fit joint** : modifier `MTBC_ANCHORS` dans `complex_datation/analyses/phase3_tdrp_joint_fit.py` en ajoutant une ligne `(timescale_years, rate, "Your study", "yourstudy202X")`.
3. **Relancer** : `python3 phase3_tdrp_joint_fit.py`. Sortie : `article/figures/tdrp_joint_fit_results.txt` + figure régénérée.
4. **Lire les trois critères-clés** :

| Sortie | Seuil | Interprétation |
|--------|-------|----------------|
| $\|\alpha_{\text{your}} - \alpha_{\text{leprae}}\|$ | < 0.2 | Shared-TDRP mycobactérien validé ; votre résultat s'inscrit dans l'envelope cohérent |
| 95% bootstrap upper tail $t^\ast$ | < 30 000 BP | Long-clock Comas 2013 formellement exclu au sketch |
| 95% bootstrap upper tail $t^\ast$ | > 50 000 BP | Manque un anchor redondant ; voir Règle d'or Phase 0 |

### Exemple validé (2026-04-19, molecular_clock v5)

Avec 4 anchors MTBC (Menardo 50y, Bos 1000y, Sabin 2000y, v5 2000y) + 3 anchors leprae :
- $\alpha_{\text{shared}} = -0.366$ [95% CI : -0.552 ; -0.303]
- $t^\ast$ point estimate : 7 334 – 14 577 BP
- **95% bootstrap upper at high-d : 29 614 BP → long-clock exclu**
- $|\alpha_{\text{MTBC}} - \alpha_{\text{leprae}}| = 0.054$ → shared-TDRP validé

### Pièges

- **Ne pas double-compter** : si votre anchor réutilise les mêmes aDNA tips qu'un anchor existant (ex. Sabin 2020), l'ajout est statistiquement redondant. Seules les pipelines ou les données réellement indépendantes contractent l'envelope.
- **Ne pas extrapoler au-delà du regime TDRP** : le fit reste une loi de puissance ajustée sur 50–2 200 ans ; l'extrapolation vers 10⁵ BP fait partie de la logique du TDRP mais reste sensible à la forme fonctionnelle (loi de puissance vs exponentielle vs multiphasique). La sensibilité fonctionnelle est traitée dans `complex_datation/main.tex` Appendix B.
- **Reporter les deux chiffres** : le tip-dating LSD2 (valeur courte-échelle) et l'envelope TDRP bootstrap (valeur corrigée). Le premier est un anchor, le second est une estimation probabiliste du vrai TMRCA.

### Script réutilisable

- `complex_datation/analyses/phase3_tdrp_joint_fit.py`, fit loi de puissance joint MTBC+leprae, bootstrap 1000, extrapolation TMRCA, figure 600 DPI. Script auto-contenu (dépendances : numpy, scipy, matplotlib).

## Phase 5 : Post-analyse

### Vérification dans Tracer

- **ESS > 200** pour tous les paramètres (sinon : allonger la chaîne)
- **Convergence** : traces stationnaires après burn-in
- **Prior vs Posterior** : le posterior doit différer du prior (données informatives)

### Extraction des résultats

```bash
# MCC tree (Maximum Clade Credibility)
treeannotator -burnin 10 -heights median trees.trees mcc_tree.nex

# Convertir en Newick pour iTOL
python3 scripts/molecular_clock.py nexus-to-newick mcc_tree.nex -o dated_tree.nwk
```

### Résumé pour l'article

```json
{
  "root_age": {"median": 5200, "95%HPD": [3100, 8400]},
  "substitution_rate": {"median": 4.2e-8, "95%HPD": [2.8e-8, 5.9e-8]},
  "clock_model": "UCLD",
  "tree_prior": "Coalescent Skyline",
  "ESS_min": 245,
  "n_tips": 523,
  "chain_length": 200000000,
  "burnin_pct": 10
}
```

## Pièges courants MTBC

| Piège | Symptôme | Solution |
|-------|----------|----------|
| Horloge stricte sur MTBC | Taux irréaliste, mauvais fit | Toujours UCLD |
| Pas assez de chaîne | ESS < 100 | 200-500M iterations |
| Dates manquantes traitées comme 0 | Taux explosé | Exclure les souches sans date |
| Sites hypervariables | Saturation, taux surestimé | Exclure PE/PPE, sites récurrents |
| Homoplasie dans L2/Beijing | Signal trompeur | Vérifier consistency index |

## Limites du pipeline actuel

Le pipeline `molecular_clock_pipeline.py` encapsule v5 et donne des résultats publiables, mais il a plusieurs limites assumées :

- **Mesure à l'échelle aDNA-calibrée (fenêtre 100–2 200 BP uniquement)**. Le taux produit et le tMRCA qui en découle sont un point de la courbe TDRP, pas une estimation non-biaisée du vrai TMRCA. Cf. Phase 0 : pour des TMRCA > 5 000 BP, appliquer une correction TDRP explicite (Aiewsakun 2015, Membrebe 2019) ou sortir vers `complex_datation/` Appendix A/C.
- **Horloge stricte uniquement** (LSD2 avec `-r a`). Pas de relaxed clock dans ce mode rapide. Pour une horloge relaxée UCLD, basculer sur BEAST2 (phase 3 manuelle).
- **Variance inter-seed ~36%** sur le taux, due au sampling aléatoire des modernes L4. Le mode `--multi-seed` avec N ≥ 10 est **obligatoire** pour un résultat publiable (sinon on rapporte un artefact de sampling).
- **Pas de génération BEAST2 XML automatisée** : la phase 3 BEAST reste à écrire à la main (voir exemples Phase 3 ci-dessus).
- **Convention de répertoires spécifique** : le pipeline requiert `bdd/ancien/` (anciens pré-curés par lignée) et `bdd/actuelle/` (format TBannotator `<SRA>/NC_000962.3/{spdi.txt,report.json}`). Pour une autre arborescence, adapter les fonctions `collect_*` du script.
- **Objective function LSD2 ≠ log-likelihood** : ce n'est pas une probabilité bayésienne, juste un résidu au modèle strict clock. Elle sert à comparer des runs comparables, pas à faire un model selection formel.
- **H37Rv MRCA fixée à `b(1900,1910)`** : c'est une contrainte nodale essentielle pour la convergence. Si on traite une lignée sans stocks H37Rv, adapter (`write_mrca_constraint`) ou accepter une moins bonne convergence.
- **Upper bound Bison antiquus non intégré automatiquement** : le pipeline ne teste pas si le tMRCA produit viole la contrainte 17 870 BP du spécimen Rothschild 2001 / Lee 2012. Vérifier manuellement pour les analyses MTBC global ; un TODO futur serait un `--check-bison-bound` qui émet un warning.

## Intégration

| Skill | Usage |
|-------|-------|
| `raxml` | Arbre ML en input pour root-to-tip ou starting tree BEAST |
| `itol` | Visualiser l'arbre daté avec branches proportionnelles au temps |
| `tbannotator-mcp` | Dates de collection des souches |
| `resistance-profiler` | Dater l'acquisition de résistance sur l'arbre |
| `spaam-ancient-metagenome-dir` | Catalogue aDNA MTBC + *M. leprae* |
| `beast2-phylogeography` | BEAST2 + MASCOT/BASTA/DTA pour TDRP-aware tip-dating |
| `bayesian-skyline` | Reconstruction démographique Ne(t)/Re(t) |

## Références bibliographiques

### Cadre TDRP (lire avant toute datation MTBC profonde)

- **Ho SYW & Larson G. 2006**, *Trends Genet* 22:79, introduction du concept "time-dependent rates".
- **Ho SYW et al. 2011**, *Mol Ecol* 20:3087, revue fondatrice : taux courts excèdent taux longs d'un ordre de grandeur ou plus.
- **Ho SYW et al. 2015**, *Proc Natl Acad Sci* 112:3100, mise à jour, mécanismes, réponse aux critiques.
- **Duchêne S et al. 2014**, *Proc Biol Sci* 281:20140732, démonstration TDRP massif chez virus.
- **Aiewsakun P & Katzourakis A. 2015**, *BMC Evol Biol* 15:119, formalisation loi de puissance vs exponentielle, rejet empirique de l'exponentielle chez foamy viruses.
- **Membrebe JV et al. 2019**, *Mol Biol Evol* 36:1793, cadre bayésien formel pour histoires évolutives sous TDRP ; à utiliser pour les TMRCA MTBC profonds.
- **Soubrier J et al. 2012**, *Mol Biol Evol* 29:3345, rôle de l'hétérogénéité de taux entre sites, amplification TDRP par sélection purifiante.
- **Duchêne S et al. 2020**, *Virus Evol* 6:veaa061, guide pratique tip-dating/damage-patterns sur aDNA.
- **Rieux A & Balloux F. 2016**, *Mol Ecol* 25:1911, tip-calibration : critère "timespan doit couvrir fraction du temps de coalescence".

### Taux MTBC et aDNA

- **Menardo F et al. 2019**, *PLoS Pathog* 15:e1008067, plage $10^{-8}$–$5 \times 10^{-7}$ sur 6 285 souches, horloge relâchée requise. Point d'entrée obligatoire.
- **Bos KI et al. 2014**, *Nature* 514:494, premier aDNA MTBC, TMRCA < 6 000 BP, *M. pinnipedii* pré-Columbien.
- **Sabin S et al. 2020**, *Genome Biol* 21:201 : Winstrup 1679, TMRCA 2 190–4 501 BP, anchor clé.
- **Kay GL et al. 2015**, *Nat Commun* 6:6717. 14 génomes Vác 18ᵉ CE, documentation mixed infections.
- **Vågene AJ et al. 2022**, *Nat Commun* 13:1195, étend pinnipedii américain.
- **Rothschild BM et al. 2001**, *Clin Infect Dis* 33:305 + **Lee OYC et al. 2012**, *PLoS ONE* 7:e41923, *Bison antiquus* 17 870 BP (upper bound).
- **Hershkovitz I et al. 2015**, *Tuberculosis* 95:S122 : Atlit-Yam PPNC 9 250–8 160 BP, humain + bovin.
- **Comas I et al. 2013**, *Nat Genet* 45:1176 : TMRCA 70 000 BP, modern-only (long-clock).
- **Wirth T et al. 2008**, *PLoS Pathog* 4:e1000160 : TMRCA 40 000 BP via tandem repeats.
- **O'Neill MB et al. 2019**, *Mol Biol Evol* 36:1751, tip-dating 552 génomes + anciens.

### *M. leprae* comme benchmark méthodologique

- **Schuenemann VJ et al. 2018**, *Nat Commun* 9:3163. 4 branches médiévales coexistantes, seuil critique franchi.
- **Pfrengle S et al. 2021**, *BMC Biol* 19:220, doublement du corpus, diversité ibérique.
- **Neukamm J et al. 2020**, *BMC Biol* 18:108. 2 200 BP Ptolémaïque, plus ancien mycobactérien aDNA authentifié.
- **Urban C et al. 2024**, *Curr Biol* 34:2221, écureuil médiéval séquencé, feasibility animal host.
- **Lopopolo M et al. 2025**, *Science*, *M. lepromatosis* pré-européen aux Amériques.

### Host–pathogen co-dating

- **Kerner G et al. 2021**, *Am J Hum Genet* 108:517 : TYK2 P1104A sélection négative depuis ~2 000 BP.
- **Romeyer d'Herbey F et al. 2026** : HLA leprosy-driven selection médiévale.

### Références internes projet

- `complex_datation/article/main.tex`, perspective piece TDRP MTBC (v1.0, 28 pages, 41 refs, 3 figures, 3 appendix empiriques, §2.3 calibration short-timescale).
- `complex_datation/data/adna_mtbc_corpus.csv`, corpus consolidé source.
- `complex_datation/analyses/phase3_tdrp_joint_fit.py`, fit loi de puissance joint MTBC+leprae, bootstrap 1000, critère de rejet long-clock. Utilisé par Phase 4c.
- `complex_datation/litterature_review/time_dependent_rate_phenomenon.md`, revue TDRP exhaustive (9 articles-clés).
- `molecular_clock/analyses/molecular_clock_pipeline.py`, pipeline v5 multi-seed, produit l'anchor courte-échelle à injecter dans Phase 4c.

## Dépendances

```bash
pip install pandas numpy scipy matplotlib biopython
# BEAST2 doit être installé séparément : https://www.beast2.org/
```
