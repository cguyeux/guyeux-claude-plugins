# Strategies de recherche pour la revue de litterature

Guide pour construire des strategies de recherche efficaces et systematiques.

## Decomposition d'un sujet en facettes

Un sujet de recherche se decompose en **facettes** independantes qui,
combinees, delimitent precisement le champ de la revue.

### Methode PICO (pour les sujets cliniques/epidemio)

| Facette | Description | Exemple |
|---------|-------------|---------|
| **P**opulation | Qui ? Quelles souches ? Quel contexte ? | M. tuberculosis, lineage L4 |
| **I**ntervention | Quel traitement, methode, gene ? | katG mutations, WGS-based typing |
| **C**omparaison | Par rapport a quoi ? | phenotypic DST, other lineages |
| **O**utcome | Quel resultat mesure ? | INH resistance, transmission rate |

### Methode par facettes (pour les sujets fondamentaux)

1. **Objet central** : le gene, la molecule, l'organisme, la methode
2. **Processus/mecanisme** : ce qui se passe (resistance, transmission, evolution)
3. **Contexte** : geographique, temporel, methodologique
4. **Angle specifique** : ce qui distingue cette revue des revues existantes

### Exemple : "katG mutations and INH resistance"

```
Facette 1 (objet)     : katG gene, catalase-peroxidase
Facette 2 (processus) : isoniazid resistance, drug resistance
Facette 3 (contexte)  : M. tuberculosis, MTBC
Facette 4 (angles)    : molecular mechanism, epidemiology, diagnostics,
                        fitness cost, non-S315T mutations
```

Chaque **combinaison de facettes** = une direction de recherche.

---

## Construction de requetes PubMed

### Principes

1. **Deux requetes par direction** :
   - Requete **precise** (MeSH + champs specifiques) : haute precision, peu de bruit
   - Requete **large** (texte libre, wildcards) : haute sensibilite, attrape les
     articles non encore indexes en MeSH

2. **Combiner les facettes avec AND** :
   ```
   (facette_1 terms) AND (facette_2 terms) AND (facette_3 terms)
   ```

3. **Au sein d'une facette, utiliser OR** pour les synonymes :
   ```
   (katG OR "catalase-peroxidase" OR "KatG protein")
   ```

4. **Utiliser les MeSH quand ils existent** :
   - `isoniazid[mh]` inclut automatiquement les termes plus specifiques
   - `drug resistance, bacterial[mh]` capture toutes les formes de resistance

5. **Restreindre par champ quand pertinent** :
   - `[ti]` (titre) pour les articles tres cibles
   - `[tiab]` (titre + abstract) pour un bon compromis
   - `[tw]` (texte complet indexe) pour la sensibilite maximale

### Modeles de requetes par type de sujet

#### Gene/mutation et phenotype
```
(GENE[ti] OR "protein name"[tiab]) AND PHENOTYPE[mh] AND ORGANISM[mh]
```
Exemple :
```
(katG[ti] OR "catalase-peroxidase"[tiab]) AND isoniazid[mh] AND "mycobacterium tuberculosis"[mh]
```

#### Epidemiologie d'un trait
```
TRAIT[mh] AND (prevalence OR incidence OR epidemiol*)[tiab] AND CONTEXTE[mh]
```
Exemple :
```
"isoniazid resistance"[tiab] AND (prevalence OR epidemiol*)[tiab] AND tuberculosis[mh]
```

#### Methode/outil
```
METHOD[ti] AND (DOMAINE OR APPLICATION)[tiab]
```
Exemple :
```
"whole genome sequencing"[ti] AND ("drug resistance" OR "resistance prediction")[tiab] AND tuberculosis[mh]
```

#### Phylogenie/evolution
```
ORGANISME[mh] AND (phylogen* OR evolution* OR "molecular clock" OR lineage*)[tiab]
```
Exemple :
```
"mycobacterium tuberculosis"[mh] AND (phylogeograph* OR "lineage L4" OR "lineage 4")[tiab]
```

#### Comparaison de methodes
```
(METHOD_A[tiab] AND METHOD_B[tiab]) AND (compar* OR performance OR accuracy)[tiab] AND DOMAINE[mh]
```

---

## Strategies d'approfondissement

Quand un sujet a deja ete explore, utiliser ces strategies pour aller
plus loin sans refaire le meme travail.

### 1. Mise a jour temporelle

Relancer les memes requetes avec une restriction de date :
```
requete_existante AND YYYY/MM/DD:3000[dp]
```
(ou YYYY/MM/DD est la date de la derniere exploration)

**Quand** : a chaque relance, systematiquement pour toutes les directions
deja couvertes.

### 2. Citation chaining (forward)

Pour chaque article cle (pertinence haute), trouver les articles
qui le citent :
- Via PubMed ELink (`dbfrom=pubmed&cmd=neighbor`)
- Via Google Scholar "Cited by"
- Via Semantic Scholar API

**Quand** : en mode `--deep`, ou quand un article cle est tres recent
et n'avait pas encore de citations lors de la derniere exploration.

### 3. Citation chaining (backward)

Lire les references d'un article cle pour trouver des sources fondamentales
qu'on aurait manquees.

**Quand** : quand un article de review recent est trouve — ses references
sont une mine d'or.

### 4. Articles related (PubMed)

Utiliser ELink `related` pour trouver des articles similaires a un
article cle. PubMed utilise un algorithme de similarite base sur
MeSH, titre, et abstract.

**Quand** : quand les requetes par mots-cles ne suffisent pas
a couvrir un angle specifique.

### 5. Exploration par auteur

Identifier les auteurs les plus productifs sur le sujet et explorer
leurs autres publications :
```
"Nom Prenom"[au] AND SUJET_GENERAL[tiab]
```

**Quand** : quand 2-3 auteurs reviennent systematiquement et sont
clairement des experts du sujet.

### 6. Elargissement par synonymes

Ajouter des termes que les premieres requetes n'avaient pas captures :
- Noms alternatifs (gene aliases, noms de proteines)
- Variantes orthographiques
- Termes plus generaux ou plus specifiques

**Quand** : quand une direction semble pauvre en resultats malgre
l'existence connue d'une litterature.

---

## Criteres d'inclusion/exclusion par defaut

### Inclusion

- Articles de recherche originale (research articles)
- Reviews et systematic reviews (signaler comme telles)
- Lettres et brief communications si contenu substantiel
- Preprints sur bioRxiv/medRxiv si pas encore publies
- Rapports institutionnels (WHO, ECDC) si directement pertinents

### Exclusion

- Articles dans une langue non maitrisee (sauf si abstract anglais disponible)
- Articles retractes (verifier via Retraction Watch si doute)
- Commentaires, editoriaux, errata (sauf si corrigent un article cle)
- Doublons (meme etude publiee comme preprint puis article — garder l'article)

### Pertinence

| Niveau | Critere | Action |
|--------|---------|--------|
| **Haute** | Directement sur le sujet, apporte des donnees ou une analyse originale | Retenir, inclure dans les articles cles |
| **Moyenne** | Lie au sujet, utile pour le contexte ou une facette secondaire | Retenir, inclure dans la synthese |
| **Faible** | Tangentiel, ne traite du sujet que marginalement | Ignorer (sauf mode `--deep`) |

---

## Exemples concrets domaine TB/bioinfo

### Sujet : "Resistance aux fluoroquinolones dans MTBC"

**Directions :**
1. Mecanismes moleculaires (gyrA, gyrB)
   ```
   (gyrA[ti] OR gyrB[ti]) AND fluoroquinolone*[tiab] AND tuberculosis[mh]
   ```
2. Epidemiologie de la resistance FQ
   ```
   fluoroquinolone resistance[tiab] AND tuberculosis[mh] AND (prevalence OR epidemiol*)[tiab]
   ```
3. Detection moleculaire (GenoType MTBDRsl, WGS)
   ```
   fluoroquinolone*[tiab] AND tuberculosis[mh] AND (detection OR genotyp* OR "whole genome")[tiab]
   ```
4. Impact sur le traitement XDR/pre-XDR
   ```
   (XDR OR pre-XDR OR "extensively drug-resistant")[tiab] AND fluoroquinolone*[tiab] AND tuberculosis[mh]
   ```

### Sujet : "Phylogeographie de la lignee L4"

**Directions :**
1. Distribution globale de L4 et sous-lignees
   ```
   ("lineage 4" OR "Euro-American" OR "L4")[tiab] AND tuberculosis[mh] AND (phylogeograph* OR distribut*)[tiab]
   ```
2. Histoire evolutive et horloge moleculaire
   ```
   ("lineage 4" OR L4)[tiab] AND tuberculosis[mh] AND ("molecular clock" OR "evolutionary history" OR "time-scaled")[tiab]
   ```
3. Transmission et dynamique epidemique
   ```
   ("lineage 4" OR L4)[tiab] AND tuberculosis[mh] AND (transmission OR cluster* OR outbreak*)[tiab]
   ```
4. Virulence et fitness comparees entre sous-lignees
   ```
   ("lineage 4" OR L4)[tiab] AND tuberculosis[mh] AND (virulence OR fitness OR "growth rate")[tiab]
   ```

### Sujet : "Machine learning pour la prediction de resistance"

**Directions :**
1. Modeles de prediction de resistance par WGS
   ```
   ("machine learning" OR "deep learning" OR "random forest")[tiab] AND "drug resistance"[tiab] AND tuberculosis[mh]
   ```
2. Features genomiques (SNPs, indels, genes)
   ```
   ("resistance prediction" OR "resistance classification")[tiab] AND (genomic OR "whole genome" OR SNP)[tiab] AND tuberculosis[mh]
   ```
3. Benchmarks et comparaison avec methodes phenotypiques
   ```
   ("resistance prediction")[tiab] AND (benchmark* OR accuracy OR sensitivity OR "AUC")[tiab] AND tuberculosis[mh]
   ```
4. Outils disponibles (Mykrobe, TBProfiler, GenTB)
   ```
   (Mykrobe OR TBProfiler OR "TB-Profiler" OR GenTB OR ResFinder)[ti] AND tuberculosis[mh]
   ```
