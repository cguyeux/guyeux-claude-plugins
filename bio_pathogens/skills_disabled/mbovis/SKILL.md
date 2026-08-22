---
name: mbovis
description: >-
  Academic research database client (Guyeux group, FEMTO-ST, peer-reviewed
  research) for mbovis.org, the Spoligo Bovis (SB) reference database for animal
  MTBC spoligotypes: SB assignment (M. bovis, M. caprae, M. pinnipedii,
  M. orygis, M. microti), BIN/OCT/HEX conversion, clonal complexes
  Eu1/Eu2/Af1/Af2, cross-reference with SITVIT2 ([[sitvitweb]]).

  Use when: pattern to SB number, SB0001..SB2902+ lookup, full DB download,
  profiles by country.
argument-hint: "<SB number, BIN/OCT/HEX spoligotype, ou pays>"
user-invocable: true
---

# mbovis.org : Spoligo Bovis (SB) Database Guide

> [!TIP]
> **SITVITBovis, la déclinaison *M. bovis* de SITVIT.** `pasteur-guadeloupe.fr:8081/SITVIT_Bovis`
> (`10.1093/database/baab081`) est une base publique **et un outil de cartographie** des cas animaux
> **et humains** attribués à *M. bovis*, donc la ressource adaptée quand la question porte sur
> l'interface hôte animal / hôte humain. Complète `sitvitweb` (spoligotypes MTBC en général) et se
> croise avec `bovine-genomics` pour le versant hôte.


## Vue d'ensemble

mbovis.org est la base de données internationale de référence pour la nomination
des profils de spoligotype issus de souches du complexe MTBC d'origine animale.
Elle attribue des **numéros SB** (Spoligo Bovis), identifiants uniques pour
chaque profil de 43 espaceurs distinct.

| Métrique | Valeur (mai 2026) |
|---|---|
| Profils enregistrés | 2 325 |
| Numéro SB maximum | SB2902 |
| URL principale | https://www.mbovis.org/database.php |
| Téléchargement complet | https://www.mbovis.org/overview-excel.php |
| Maintenu par | Unité Mycobactéries, **VISAVET Health Surveillance Centre**, Universidad Complutense de Madrid |
| Historique | 2003-2015 : Noel Smith & Rainer Hilscher (Univ. Sussex) avec soutien DEFRA/VLA (maintenant APHA) |

> [!IMPORTANT]
> mbovis.org n'a **pas d'API REST**. Les requêtes individuelles nécessitent
> une interaction via formulaires POST (voir paramètres exacts ci-dessous).
> Le téléchargement complet (`overview-excel.php`) est accessible par simple GET.

---

## Espèces couvertes

La base couvre toutes les espèces animales du complexe MTBC :

| Espèce | Hôtes principaux |
|---|---|
| *M. bovis* | bovins, cervidés, sangliers, blaireaux, chèvres |
| *M. caprae* | chèvres, moutons, bovins (principalement péninsule ibérique, Alpes) |
| *M. pinnipedii* | phoques, otaries (Australie, Amérique du Sud) |
| *M. orygis* | antilopes, cervidés (Asie, Afrique) |
| *M. microti* | rongeurs (campagnols) |

---

## Formats de spoligotype

Tous les formulaires acceptent trois encodages interchangeables des 43 espaceurs :

| Format | Description | Exemple (SB0001) |
|---|---|---|
| **BIN** | Chaîne de 43 bits (1=présent, 0=absent) | `1001111111111111111111111111000010110001111` |
| **OCT** | 15 chiffres octaux (groupes de 3 bits ; 43e bit seul) | `477777777413071` |
| **HEX** | 6 blocs hex séparés par des tirets (7+7+7+7+8+7 bits) | `4F-7F-7F-7F-0B-0F` |

### Conversion BIN → OCT
Grouper les 42 premiers bits par 3 (→ 14 chiffres octaux), puis lire le
43e bit seul (→ 1 chiffre octal : 0 ou 4) :
```
BIN: 111 111 111 111 111 111 111 111 111 111 111 111 111 111 0
OCT:  7   7   7   7   7   7   7   7   7   7   7   7   7   7  0
→ "777777777777770"
```

### Conversion BIN → HEX
Découper en 6 blocs (7+7+7+7+8+7 bits), convertir chaque bloc en 2 chiffres hex :
```
Spacers  1- 7  : 7 bits → 2 hex digits
Spacers  8-14  : 7 bits → 2 hex digits
Spacers 15-21  : 7 bits → 2 hex digits
Spacers 22-28  : 7 bits → 2 hex digits
Spacers 29-36  : 8 bits → 2 hex digits
Spacers 37-43  : 7 bits → 2 hex digits
Format final : XX-XX-XX-XX-XX-XX
```

---

## Clonal complexes de *M. bovis*

Quatre clonal complexes majeurs sont définis par des délétions chromosomiques
spécifiques visibles dans le spoligotype (Smith et al. 2011, Berg et al. 2011) :

| Complex | Marqueur génomique | Signature spoligotype | Distribution géographique |
|---|---|---|---|
| **European 1 (Eu1)** | Délétion RDEu1 (806 bp) | Spacer 11 **absent** | Mondial (Îles Britanniques, ex-colonies, Amériques, Kazakhstan, Corée) |
| **European 2 (Eu2)** | SNP gène *guaA* | Pas de signature spoligo unique | Péninsule ibérique, Brésil |
| **African 1 (Af1)** | Délétion RDAf1 (5 322 bp) | Spacer 30 **absent** | Afrique centrale et occidentale |
| **African 2 (Af2)** | Délétion RDAf2 (14 094 bp) | Spacers 3-7 **tous absents** | Afrique de l'Est |

**Représentation dans mbovis.org (mai 2026, sur 2 326 profils)** :
- Eu1 (spacer 11 absent) : ~1 114 profils (~48%)
- Af1-like (spacer 30 absent, spacer 11 présent) : ~299 profils
- Af2-like (spacers 3-7 tous absents) : ~298 profils

**SB de référence fréquemment cités** :
- Eu1 : SB0140 (OCT : `664073777777600`)
- Eu1 : SB0120 (OCT : `676773777777600`)

> [!NOTE]
> Un 5e complex (European 3) est parfois décrit dans la littérature récente.
> Eu2 n'a pas de signature spoligotype unique, son identification requiert
> le génotypage du gène *guaA* ou le WGS.

---

## Paramètres POST exacts des formulaires

**URL** : `POST https://www.mbovis.org/database.php`

### Formulaire 1 : Spoligotype simple → SB number

```python
import urllib.request, urllib.parse

data = urllib.parse.urlencode({
    'qsb': 'qsb',
    'code': 'codeOCT',        # ou 'codeBIN' ou 'codeHEX'
    'codeOCT_input': '477777777413071',  # le pattern
    # alternatives : 'codeBIN_input': '...', 'codeHEX_input': '...'
    'submit': 'SEARCH',
    'accion': 'getSBfromPattern'
}).encode()
req = urllib.request.Request('https://www.mbovis.org/database.php', data=data,
    headers={'User-Agent': 'Mozilla/5.0',
             'Content-Type': 'application/x-www-form-urlencoded'})
with urllib.request.urlopen(req) as r:
    html = r.read().decode('utf-8', errors='replace')
# Parser la réponse HTML pour extraire le SB number retourné
```

| Paramètre | Valeurs possibles | Description |
|---|---|---|
| `qsb` | `qsb` | Marqueur fixe du formulaire 1 |
| `code` | `codeBIN`, `codeHEX`, `codeOCT`, `codePAT` | Format du pattern saisi |
| `codeBIN_input` | chaîne 43 bits | Pattern binaire |
| `codeHEX_input` | format XX-XX-XX-XX-XX-XX | Pattern hexadécimal |
| `codeOCT_input` | 15 chiffres | Pattern octal |
| `ss1`..`ss43` | `1` | Spacers individuels (mode visuel `codePAT`) |
| `accion` | `getSBfromPattern` | Action fixe |

### Formulaire 2 : Spoligotypes multiples → SB numbers

| Paramètre | Valeurs | Description |
|---|---|---|
| `qsbm` | `qsbm` | Marqueur fixe |
| `codeM` | `codeMBIN`, `codeMHEX`, `codeMOCT` | Format des patterns |
| `codeMultiple_input` | texte multiligne | Un pattern par ligne |
| `accion` | `getSBfromPatternM` | Action fixe |

### Formulaire 3 : SB number → spoligotype

| Paramètre | Valeurs | Description |
|---|---|---|
| `qsp` | `qsp` | Marqueur fixe |
| `sbnumber` | `SB0001` | Numéro SB à rechercher |
| `accion` | `getPatternFromSB` | Action fixe |

### Formulaire 4 : SB numbers multiples → spoligotypes

| Paramètre | Valeurs | Description |
|---|---|---|
| `qsp` | `qsp` | Marqueur fixe |
| `sbnumberM` | texte multiligne | Un SB par ligne |
| `accion` | `getPatternFromSBM` | Action fixe |

### Formulaire 5 : Pays → profils

| Paramètre | Valeurs | Description |
|---|---|---|
| `qsbm` | `qsbm` | Marqueur fixe |
| `country_input` | nom du pays (en anglais) | Ex : `France`, `Spain` |
| `accion` | `getByCountry` | Action fixe |

Pays disponibles (90+) : Algeria, Argentina, Australia, Austria, Belgium,
Botswana, Brazil, Burkina Faso, Burundi, Cameroon, Canada, Chad, Chile, China,
Czech Republic, Ethiopia, France, Germany, Ghana, Hungary, India, Indonesia,
Iran, Ireland, Italy, Madagascar, Malawi, Mali, Mexico, Morocco, Mozambique,
New Zealand, Niger, Nigeria, Poland, Portugal, Saudi Arabia, Somalia,
South Africa, South Korea, Spain, Switzerland, Tanzania, Tunisia, Turkey,
Uganda, United Kingdom, United States, Venezuela, Zambia, et d'autres.

---

## Téléchargement de la base complète

La méthode la plus efficace pour les analyses sur plus de 10 souches :

```python
import urllib.request, subprocess

# 1. Télécharger
urllib.request.urlretrieve(
    'https://www.mbovis.org/overview-excel.php',
    'mbovis_database.xls'
)

# 2. Convertir en CSV via libreoffice (le fichier .xls peut être corrompu pour xlrd)
subprocess.run(
    ['libreoffice', '--headless', '--convert-to', 'csv', 'mbovis_database.xls'],
    check=True
)

# 3. Lire le CSV résultant
import csv
db = {}
with open('mbovis_database.csv') as f:
    reader = csv.reader(f)
    next(reader)  # ligne date
    next(reader)  # headers
    for row in reader:
        if row and row[0].startswith('SB'):
            db[row[0]] = {'bin': row[1].strip(), 'oct': row[2].strip(), 'hex': row[3].strip()}
# → db = {'SB0001': {'bin': '100111...', 'oct': '477...', 'hex': '4F-...'}, ...}
```

> [!WARNING]
> Le fichier `.xls` retourné par `overview-excel.php` est corrompu pour `xlrd`
> (`CompDocError`). Passer systématiquement par `libreoffice --headless --convert-to csv`.

---

## Pipeline WGS → SB

Pour assigner un SB number à partir d'une séquence brute :

```
1. Extraction du spoligotype depuis les reads FASTQ/BAM
   → SpolPred2 (Iqbal et al. 2012, Bioinformatics)
   → Spotyping (Xia et al. 2016, Genome Med)
   → TB-Profiler (Phelan et al. 2019) — retourne le spoligotype octal

2. Conversion en SB number
   → Requête POST mbovis.org (Formulaire 1, codeOCT)
   OU
   → Recherche locale dans la base téléchargée (plus rapide, hors-ligne)

3. Identification du clonal complex
   → Vérifier présence/absence des spacers diagnostiques (tableau ci-dessus)
   → Ou WGS : détecter RDEu1, RDAf1, RDAf2 par alignement
```

---

## Stratégie pour les profils orphelins

Si un pattern ne matche aucun SB existant (réponse "No match found") :

1. Vérifier l'encodage (BIN/OCT/HEX correctement formé, 43 spacers)
2. Chercher le profil le plus proche dans la base locale (distance de Hamming sur BIN)
3. Signaler un nouveau profil aux curators : formulaire de contact sur https://www.mbovis.org/contact.php
4. En attendant l'attribution d'un SB, décrire le profil par son OCT ou BIN dans les publications

---

## Limitations du spoligotypage

- **Résolution faible** : convergence évolutive fréquente (même profil SB par pertes indépendantes de spacers dans des lignées différentes). Compléter avec MIRU-VNTR 24-loci ou WGS pour la discrimination fine.
- **Eu2 invisible** : son marqueur (SNP *guaA*) n'est pas détectable par spoligotypage. L'assignation au complex Eu2 nécessite un génotypage ciblé ou le WGS.
- **Absence ≠ délétion** : la PCR peut rater un spacer (faux négatif) si la qualité du DNA est mauvaise ou si la souche est en mélange.
- **À ne pas confondre avec SITVIT2** : les SIT numbers (SITVIT2, [[sitvitweb]]) sont distincts des SB numbers. Un même profil peut avoir un SIT et un SB, les deux bases utilisent des nomenclatures indépendantes.

---

## Relation avec SITVIT2 ([[sitvitweb]])

| Critère | mbovis.org (SB) | SITVIT2 (SIT) |
|---|---|---|
| Organisme cible | MTBC animal (*M. bovis*, *M. caprae*, etc.) | MTBC humain (*M. tuberculosis*, *M. africanum*, *M. bovis* zoonotique) |
| Identifiant | SB number (SB0001…) | SIT number (1…) |
| Spacers | 43 (identiques) | 43 (identiques) |
| Maintenu par | VISAVET, Complutense Madrid | Institut Pasteur de Guadeloupe |
| Résultat | SB number + BIN/OCT/HEX | SIT + clade + MIRU + géographie |

Un même spoligotype peut avoir un SB chez mbovis.org ET un SIT chez SITVIT2.
Les deux nomenclatures sont indépendantes et complémentaires.

---

## Cross-références avec d'autres skills

- [[sitvitweb]] : Spoligotypes MTBC humain (SITVIT2, SIT numbers, clades Beijing/LAM/T)
- [[tbannotator-mcp]] : Vue `mv_strain_metadata` contient les champs `spol43` et `spol98`
- [[mtbc-lineages]] : Lignages SNP-based (L1-L9) complémentaires du spoligotypage
- [[phylogeography]] : Analyse phylogéographique combinant spoligotypes et SNPs
- [[ncbi-pathogen-detection]] : Isolats MTBC déposés avec métadonnées de spoligotypage

---

## Références

- Smith NH, Upton P. (2012) *Naming spoligotype patterns for the RD9-deleted lineage of the Mycobacterium tuberculosis complex.* mbovis.org
- Smith NH et al. (2011) *European 1: a globally important clonal complex of M. bovis.* Infect Genet Evol.
- Berg S et al. (2011) *African 1, an epidemiologically important clonal complex of M. bovis dominant in sub-Saharan Africa.* PNAS.
- Base de données : https://www.mbovis.org (VISAVET Health Surveillance Centre, Universidad Complutense de Madrid)
