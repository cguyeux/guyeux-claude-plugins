---
name: lit-review
description: >-
  Revue de litterature systematique et incrementale : synthetise dans
  litterature_review/, maintient un BibTeX cumulatif. Sources :
  tbmonitor-papers (prioritaire pour TB / MTBC), pubmed-database, WebSearch.
  Mode --wide : backward chaining, recherche pre-nomenclature.

  Use when: construire ou approfondir une revue, preparer un etat de l'art,
  identifier les lacunes, trouver les travaux precurseurs anterieurs a la
  nomenclature courante.
argument-hint: "[sujet] [--deep] [--wide] [--direction 'nouvelle direction']"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebSearch, WebFetch
---

# /lit-review -- Revue de litterature systematique et incrementale

Construit progressivement une revue de litterature sur un sujet donne.
A chaque invocation, approfondit la recherche dans de nouvelles directions
ou enrichit ce qui est deja connu. Toutes les sources sont memorisees en
BibTeX. Les resultats sont stockes dans `litterature_review/`.



## Prealable -- Consultation memoire projet

**Avant toute action**, verifier si le projet possede :
1. Un `JOURNAL.md` dans le repertoire du projet → le lire pour connaitre l'historique
2. Un `CLAUDE.md` local → le lire pour les instructions specifiques
3. Un `claim_check.md`, `review/INDEX.md`, ou `response.md` → connaitre l'etat courant

Afficher un bref resume de l'etat connu du projet avant de commencer :

```
Etat projet : [titre article]
  Journal     : [derniere entree ou "absent"]
  Claim-check : [N claims, M infirmes ou "jamais execute"]
  Reviews     : [N reviews, M en cours ou "aucune"]
  Derniere action : [date et description]
```

## Declenchement

```
/lit-review katG mutations and INH resistance
/lit-review katG mutations and INH resistance --direction "diagnostics"
/lit-review katG mutations and INH resistance --deep
/lit-review La4 lineage --wide
/lit-review La4 lineage --wide --deep
/lit-review                                        # affiche l'index existant
```

- **Premier argument** : le sujet de la revue (texte libre)
- `--deep` : exploration approfondie (plus de requetes, citation chaining
  a 3 niveaux au lieu de 2, articles related via co-citation, et
  traitement des articles faible-pertinence pour le chaining)
- `--wide` : recherche elargie (voir section dediee ci-dessous). Active
  trois mecanismes complementaires aux requetes par mots-cles :
  (1) backward chaining systematique sur TOUS les articles de haute
  pertinence, (2) recherche pre-nomenclature pour trouver les travaux
  precurseurs avant qu'un concept ait ete nomme, (3) expansion des
  termes historiques et synonymes
- `--direction "X"` : forcer l'exploration d'une direction specifique
- **Sans argument** : afficher l'index des sujets existants et proposer
  des approfondissements
- `--wide` et `--deep` sont combinables : `--wide` elargit le spectre,
  `--deep` approfondit chaque direction

---

## Repertoire persistant `litterature_review/`

Le skill cree et maintient ce repertoire dans le repertoire de travail courant :

```
litterature_review/
├── index.md              # Index global : sujets explores, stats
├── references.bib        # BibTeX cumulatif de toutes les sources
├── katg_inh_resistance.md    # Synthese structuree du sujet
├── l4_phylogeography.md      # Autre sujet
└── ...
```

Le nom de fichier de chaque sujet est derive du titre (lowercase, underscores,
sans caracteres speciaux, max 50 caracteres).

---

## Phase 0 -- Chargement de l'etat existant

1. Chercher `litterature_review/` dans le repertoire courant
2. **Si existant** :
   - Lire `index.md` : sujets couverts, stats
   - Lire `references.bib` : compter les entrees, lister les cles existantes
   - Si le sujet demande correspond a un sujet existant (correspondance semantique,
     pas necessairement mot a mot) : charger sa fiche, lister les directions
     deja couvertes et les suggestions non encore explorees
3. **Si inexistant** : noter qu'il sera cree en Phase 4
4. **Si aucun sujet fourni** : afficher l'index et les suggestions d'approfondissement,
   puis s'arreter (ne pas lancer de recherche)
5. Afficher :

```
Lit-review : [sujet]
Repertoire : litterature_review/
Etat       : [nouveau sujet / approfondissement]
Articles existants dans references.bib : N
  dont sur ce sujet : M
Directions deja couvertes : [liste ou "aucune"]
Directions suggerees non explorees : [liste ou "aucune"]
```

---

## Phase 1 -- Strategie de recherche

Consulter [references/SEARCH_STRATEGY.md](references/SEARCH_STRATEGY.md) pour
les principes de construction de requetes.

### Nouveau sujet

1. Decomposer le sujet en **3-5 directions** de recherche complementaires
   (voir la methode PICO ou la decomposition par facettes dans SEARCH_STRATEGY.md)
2. Pour chaque direction, construire **1-2 requetes PubMed** :
   - Une requete MeSH precise (haute precision)
   - Une requete texte libre plus large (haute sensibilite)
3. Ordonner les directions par pertinence (la plus centrale d'abord)

**Exemple** pour le sujet "katG mutations and INH resistance" :
```
Direction 1 : Mecanismes moleculaires (katG structure, catalase-peroxidase, INH-NAD)
  → katG[ti] AND isoniazid[mh] AND (mechanism* OR structural OR catalase-peroxidase)[tiab]
  → "katG S315T"[tiab] AND resistance[tiab]

Direction 2 : Epidemiologie de la resistance
  → katG[ti] AND isoniazid resistance[mh] AND (prevalence OR epidemiol*)[tiab]

Direction 3 : Diagnostic moleculaire
  → katG[ti] AND (diagnosis OR detection OR genotyp*)[tiab] AND isoniazid[mh]

Direction 4 : Fitness cost et compensation
  → katG[ti] AND (fitness OR compensat* OR reversion)[tiab]

Direction 5 : Nouvelles mutations (hors S315T)
  → katG[ti] AND mutation*[tiab] AND isoniazid[mh] NOT S315T[tiab]
```

### Sujet existant (approfondissement)

1. Lire les directions deja couvertes dans le fichier sujet_X.md
2. Lire les suggestions de directions futures
3. **Si `--direction` fourni** : explorer cette direction specifique
4. **Sinon**, par ordre de priorite :
   a. Explorer les directions suggerees non encore couvertes
   b. Rechercher les articles recents (depuis la derniere exploration) sur
      les directions deja couvertes (mise a jour temporelle)
   c. **Citation chaining** sur les articles fondateurs existants
      (voir Phase 2, section 2.1b, systematique, pas reserve a `--deep`)
   d. **Si `--wide`** : ajouter automatiquement une direction "Travaux
      precurseurs" qui applique la recherche pre-nomenclature et le
      backward ref scan systematique (voir section 2.1c). Cette direction
      est ajoutee meme si elle n'est pas dans les suggestions existantes.
5. Construire les requetes pour les nouvelles directions
6. **Si `--wide`** : apres les requetes standard, construire les requetes
   pre-nomenclature et planifier le backward ref scan (voir 2.1c)

**Afficher le plan de recherche** avant de l'executer :

```
Plan de recherche :

Sujet : katG mutations and INH resistance
Mode  : approfondissement

Directions a explorer cette session :
  1. [NOUVELLE] Fitness cost et compensation
     → Requete : katG[ti] AND (fitness OR compensat*)[tiab]
  2. [MISE A JOUR] Mecanismes moleculaires (derniere exploration : 2026-03-15)
     → Requete : katG[ti] AND isoniazid[mh] AND mechanism*[tiab] AND 2026/03/15:3000[dp]
  3. [DEEP] Citations forward des 3 articles cles
     → Via ELink related articles

Proceder ?
```

---

## Phase 2 -- Recherche et collecte

**Parallelisation** : lancer les requetes de TOUTES les directions en
parallele (plusieurs tool calls dans un meme message). Ne pas boucler
sequentiellement. Les ESearch, WebSearch, et EFetch des differentes
directions sont independants et doivent partir simultanement. Le tri
par ordre de plan se fait a la consolidation des resultats, pas a
l'execution.

### 2.1 Execution de la recherche

#### Priorite des sources (regle operationnelle)

**Pour tout sujet TB / MTBC, interroger le skill `tbmonitor-papers` AVANT
l'API PubMed live.** Le corpus `tbmonitor` est un index pre-construit
d'environ **190 000 papiers PubMed TB**, avec les termes MeSH, les auteurs
et les keywords stockes en JSON et requetables en **SQL sub-seconde**
(`mcp__tbmonitor__show_schema` puis `mcp__tbmonitor__execute_sql`). Une
requete y coute une fraction du temps et du quota d'un aller-retour
E-utilities, et permet des filtres (MeSH x annee x auteur) impossibles a
formuler en une seule requete ESearch.

Ordre a respecter :

1. `tbmonitor-papers` (sujets TB / MTBC uniquement) ;
2. **API PubMed live** (E-utilities) pour ce que `tbmonitor` ne couvre pas :
   sujets hors TB, articles trop recents pour l'index, ou champs absents ;
3. `WebSearch` / `WebFetch` pour les sources hors PubMed (preprints,
   rapports institutionnels, theses).

Ne pas tomber directement sur l'API live ou sur `WebSearch` pour un sujet
TB : c'est le mode d'echec le plus courant (lent, quota, et couverture
inferieure a celle de l'index).

1. **PubMed** via E-utilities (lancees en parallele pour toutes directions) :
   - `ESearch` : obtenir les PMIDs correspondant a la requete
   - `ESummary` : obtenir titre, auteurs, journal, annee, DOI pour chaque resultat
   - `EFetch` (format abstract) : obtenir l'abstract complet
   - Limiter a **50 resultats par requete** (les plus recents d'abord),
     sauf en mode `--deep` (100)
2. **WebSearch** pour les sources hors PubMed si pertinent (en parallele
   avec PubMed) :
   - Preprints (bioRxiv, medRxiv)
   - Rapports institutionnels (WHO, ECDC)
   - Theses
3. En mode `--deep` : **ELink** pour les articles related des articles cles

### 2.1b Citation chaining (systematique, pas uniquement --deep)

Le citation chaining n'est **pas** reserve au mode `--deep`. Il doit
etre declenche des qu'un article est identifie comme **fondateur** ou
**cle** pour le sujet. Cela arrive :
- lors de la premiere exploration d'un nouveau sujet (Phase 1) ;
- lors de l'approfondissement d'un sujet existant (Phase 1b) ;
- a chaque fois qu'un article de pertinence **haute** est retenu
  (section 2.2 ci-dessous).

#### Quand un article est considere comme fondateur

Un article est fondateur s'il remplit au moins une de ces conditions :
- C'est la **premiere description** d'une lignee, d'un gene, d'un
  mecanisme, d'un outil (ex : la decouverte de La4, le premier
  barcode de Coll 2014, la description de TBannotator).
- C'est le **papier le plus cite** de sa direction (cite par >=10
  articles dans la revue courante ou visible dans les references de
  la majorite des articles retenus).
- L'utilisateur l'a explicitement designe comme fondateur (dans le
  cahier de labo, la litterature_review, ou dans sa requete).
- L'article **definit une methodologie** qui est ensuite reutilisee
  par d'autres papiers du meme domaine.

#### Comment faire le citation chaining

Pour chaque article fondateur identifie :

1. **Forward citations** (articles qui CITENT ce papier fondateur) :
   - Europe PMC : `https://www.ebi.ac.uk/europepmc/webservices/rest/MED/$PMID/citations?format=json&page=1&pageSize=100`
   - Ou via PubMed ELink : `elink.fcgi?dbfrom=pubmed&db=pubmed&id=$PMID&linkname=pubmed_pubmed_citedin`
   - Trier les citants par pertinence au sujet (lire les titres et
     abstracts), retenir ceux de pertinence haute/moyenne.
   - Cela permet de trouver les **travaux qui ont construit** sur
     l'article fondateur : replications, extensions, contradictions.

2. **Backward citations** (articles que ce papier fondateur CITE) :
   - Lire la section references de l'article fondateur si le texte
     integral est accessible (Europe PMC full text, ou PDF via
     Unpaywall).
   - Ou via PubMed ELink : `elink.fcgi?dbfrom=pubmed&db=pubmed&id=$PMID&linkname=pubmed_pubmed_refs`
   - Retenir les references elles-memes de pertinence haute qui
     n'etaient pas encore dans `references.bib`.

3. **Tracer l'origine** : dans le champ `annote` BibTeX de chaque
   article trouve par citation chaining, noter :
   `Found via forward citation of @fondateur_cle` ou
   `Found via backward citation of @fondateur_cle`.
   Cela permet de reconstruire la chaine et d'identifier les clusters
   de connaissances.

4. **Iterativite** : si un article trouve par citation chaining est
   lui-meme fondateur (premiere description d'un aspect connexe,
   ou tres cite), appliquer recursivement le chaining. Limiter la
   profondeur a **2 niveaux** (fondateur → citant → citant du citant)
   pour eviter l'explosion combinatoire. En mode `--deep`, autoriser
   3 niveaux.

5. **Affichage** : signaler a l'utilisateur chaque chaine parcourue :

   ```
   Citation chaining sur @coll2014barcode (fondateur) :
     Forward citations : 847 total, 23 pertinents retenus
     Backward citations : 31 refs, 5 nouvelles retenues
     Chain level 2 : 3 articles fondateurs secondaires identifies
       → @napier2020robust (89 forward cit., 7 retenus)
       → @freschi2021population (142 forward cit., 12 retenus)
   ```

#### Ce que le mode `--deep` ajoute en plus

En mode `--deep`, le citation chaining est **plus agressif** :
- 3 niveaux au lieu de 2.
- Les articles de pertinence **faible** sont aussi traites pour le
  chaining (ils peuvent citer des articles pertinents).
- ELink related articles (articles connexes par co-citation, sans
  lien de citation directe) est active en plus du forward/backward.

### 2.1c Mode `--wide` -- Recherche elargie

Le mode `--wide` resout un probleme fondamental des revues de litterature
par mots-cles : **un concept peut exister dans la litterature bien avant
d'avoir ete nomme**. Exemple : la lignee La4 de M. bovis a ete
formellement definie en ~2023, mais Loiseau et al. 2019 avaient deja
identifie des clades enigmatiques dans le complexe bovis/caprae qui
correspondent a ce qui sera plus tard appele La4. Une recherche "La4" ne
retrouve pas cet article, car le terme n'existait pas. Pourtant, l'article
definissant La4 le cite dans sa bibliographie.

Le mode `--wide` active trois mecanismes complementaires :

#### Mecanisme 1 : Backward chaining systematique elargi

**Difference avec le chaining standard** : en mode normal, seuls les
articles *fondateurs* declenchent le backward chaining. En mode `--wide`,
**tout article de pertinence haute** declenche un scan de ses references.

Pour chaque article de haute pertinence retenu (pas seulement les
fondateurs) :

1. Recuperer la liste de ses references via :
   - PubMed ELink : `elink.fcgi?dbfrom=pubmed&db=pubmed&id=$PMID&linkname=pubmed_pubmed_refs`
   - Europe PMC references : `https://www.ebi.ac.uk/europepmc/webservices/rest/MED/$PMID/references?format=json&page=1&pageSize=500`
   - Si le texte integral est accessible (Europe PMC OA, Unpaywall) :
     parser la section References/Bibliography pour recuperer les refs
     qui n'ont pas de PMID (rapports, theses, communications).
2. Pour chaque reference trouvee :
   - Verifier si elle est deja dans `references.bib` → si oui, passer
   - Recuperer titre + abstract via ESummary/EFetch
   - Evaluer la pertinence par rapport au sujet
   - **Attention particuliere** aux articles dont le titre ne contient
     pas les termes du sujet mais dont l'abstract revele une pertinence
     (c'est exactement le cas des travaux pre-nomenclature)
3. Tracer dans le champ `annote` BibTeX :
   `Found via backward ref scan of @article_cle (wide mode)`

**Budget** : max 500 references totales scannees par session `--wide`
(seuil pour eviter l'explosion). Si atteint, prioriser les references
des articles les plus recents et les plus cites.

#### Mecanisme 2 : Recherche pre-nomenclature

Avant de lancer les requetes PubMed standard, le skill doit identifier
si le sujet fait reference a un concept **recemment nomme** et construire
des requetes alternatives qui capturent les travaux precurseurs.

**Etapes** :

1. **Detection** : le sujet fait-il reference a une entite nommee
   recemment ?
   - Lignees MTBC nommees apres 2015 (ex : La4, L4.11, sous-lignees
     Guyeux, sous-lignees Zwyer)
   - Genes/variants recemment decouverts ou renommes
   - Concepts methodologiques recents (ex: "genomic surveillance" avant
     que le terme soit consacre)
   - En cas de doute, consulter le skill `mtbc-lineages` pour connaitre
     la date de premiere definition d'une lignee.

2. **Reconstruction des termes precurseurs** : pour chaque concept
   recemment nomme, identifier comment il etait decrit AVANT d'etre
   nomme :
   - Lire l'article fondateur (celui qui a defini le concept) et
     extraire les termes descriptifs qu'il utilise pour le concept dans
     son introduction ("novel clade", "unnamed cluster", "atypical
     strains", "divergent M. bovis", etc.)
   - Lire les references de l'article fondateur qui mentionnent le
     phenomene precurseur
   - Construire une liste de **termes precurseurs** :
     ```
     Concept actuel : La4 (lignee animale MTBC, definie ~2023)
     Termes precurseurs :
       - "novel M. bovis clade" / "unknown M. bovis lineage"
       - "atypical M. caprae" / "divergent M. caprae"
       - "M. bovis cluster" + pays concernes (France, Espagne)
       - "unclassified MTBC animal lineage"
       - Noms de clades provisoires utilises dans les arbres
         (ex : "clade A", "cluster 3" dans certains papiers)
       - Spoligotypes associes (si connus)
     ```

3. **Requetes alternatives** : construire des requetes PubMed utilisant
   les termes precurseurs au lieu (ou en complement) de la nomenclature
   actuelle :
   ```
   Requete standard : "La4"[tiab] AND tuberculosis[mh]
   Requetes pre-nomenclature :
     → ("novel clade" OR "unknown lineage" OR "unclassified")[tiab]
       AND ("M. bovis" OR "M. caprae")[tiab] AND tuberculosis[mh]
     → ("atypical" OR "divergent")[tiab] AND "Mycobacterium bovis"[mh]
       AND phylogen*[tiab]
     → (Loiseau[au] OR Duarte[au] OR auteurs-cles[au]) AND bovis[tiab]
       AND (clade OR lineage OR cluster)[tiab]
   ```

4. **Affichage** : montrer explicitement les requetes pre-nomenclature
   dans le plan de recherche :
   ```
   Plan de recherche (mode wide) :

   Sujet : La4 lineage in MTBC animal complex
   Nomenclature recente detectee : "La4" (definie ~2023)

   Requetes standard :
     1. "La4"[tiab] AND tuberculosis → N resultats attendus
     2. ...

   Requetes pre-nomenclature (mode wide) :
     3. [PRE-NOM] "novel clade" AND "M. bovis" AND phylogen* → ?
     4. [PRE-NOM] "atypical" AND "Mycobacterium bovis" AND cluster → ?
     5. [PRE-NOM] Loiseau[au] AND bovis AND clade → ?

   Backward ref scan :
     6. [BACK-SCAN] Refs de l'article fondateur La4 (N refs a scanner)
   ```

#### Mecanisme 3 : Expansion des termes historiques et synonymes

En complement de la pre-nomenclature, `--wide` active une expansion
systematique des termes de recherche :

1. **Synonymes taxonomiques** : variations d'especes/sous-especes
   (ex : "M. bovis" = "Mycobacterium bovis" = "M. tuberculosis var.
   bovis" dans d'anciens articles)
2. **Acronymes et noms longs** : (ex : MTBC = "M. tuberculosis
   complex" = "Mycobacterium tuberculosis complex")
3. **Termes geographiques** : si le sujet a une composante
   geographique, inclure les noms historiques de regions/pays
4. **Noms de methodes anterieures** : si le concept a ete identifie
   par une methode aujourd'hui obsolete (ex : spoligotypage,
   MIRU-VNTR), chercher aussi avec ces termes
5. **Auteurs-cles** : identifier les 3-5 auteurs les plus publiant
   sur le sujet et faire des requetes par auteur croisees avec des
   termes generiques du domaine

Les requetes elargies sont **marquees** dans le fichier de synthese
pour distinguer les trouvailles par recherche standard vs wide :

```markdown
## Directions explorees

### 3. Travaux precurseurs (mode wide, YYYY-MM-DD)

- **Requetes pre-nomenclature** : [liste]
- **Backward ref scan** : articles fondateurs scannes [liste]
- **Resultats** : N articles trouves, M retenus
- **Decouverte notable** : Loiseau et al. 2019 avait identifie
  un clade enigmatique correspondant a La4 avant sa denomination
  formelle. Trouve via backward ref scan de @article_la4_2023.
```

#### Interaction `--wide` + `--deep`

Les deux flags sont combinables et complementaires :
- `--wide` seul : elargit le spectre (pre-nomenclature, backward scan
  systematique, synonymes) mais reste a 2 niveaux de profondeur
- `--deep` seul : approfondit le chaining (3 niveaux, articles faibles,
  ELink related) mais ne fait pas de pre-nomenclature
- `--wide --deep` : les deux. Le backward scan systematique du `--wide`
  alimente le chaining profond du `--deep`. Budget elargi a 800
  references scannees.

### 2.2 Evaluation et filtrage

Pour chaque article retourne :

1. **Deduplication** : verifier si le DOI, PMID, ou titre existe deja dans
   `references.bib`. Si oui → passer (compter comme "deja connu")
2. **Lecture de l'abstract** : lire et evaluer la pertinence par rapport au sujet
3. **Classification de pertinence** :
   - **Haute** : directement sur le sujet, apporte une contribution claire
   - **Moyenne** : lie au sujet, utile pour le contexte ou une facette secondaire
   - **Faible** : tangentiel, a ne retenir que si rien de mieux n'est disponible
4. **Retenir** : articles de pertinence haute et moyenne. Ignorer les faibles
   sauf en mode `--deep`

### 2.3 Extraction BibTeX

Pour chaque article retenu :

1. Construire l'entree BibTeX a partir des metadonnees PubMed/ESummary :
   - Type : `@article` (par defaut), `@inproceedings`, `@phdthesis`, `@misc` selon le cas
   - Cle : `premierauteur_annee_motcle` (ex: `smith2024katg`)
   - Champs obligatoires : `author`, `title`, `journal`, `year`
   - Champs recommandes : `volume`, `pages`, `doi`, `pmid`
   - **Champ `keywords`** : nom normalise du sujet (le meme pour tout le sujet,
     correspond au nom de fichier du sujet, ex: `katg_inh_resistance`)
   - **Champ `annote`** : resume en 1-2 phrases de la contribution principale
     de l'article au sujet
2. Verifier que la cle BibTeX est unique dans references.bib
   (si collision, ajouter une lettre : `smith2024katga`)

### 2.4 Progression

Afficher tous les 10 articles traites :

```
Direction "Mecanismes moleculaires" : 30/47 articles evalues
  Retenus : 12 (haute : 5, moyenne : 7)
  Deja connus : 8
  Ignores (faible pertinence) : 10
```

---

## Phase 3 -- Synthese et redaction

### Nouveau sujet

Rediger le fichier `sujet_X.md` avec cette structure :

```markdown
# [Titre du sujet]

**Cree le :** YYYY-MM-DD
**Derniere exploration :** YYYY-MM-DD
**Requetes PubMed utilisees :** (liste cumulative)

## Synthese

[Texte de synthese structure en paragraphes. Organise par themes ou par
chronologie selon ce qui est le plus naturel. Chaque affirmation importante
est accompagnee de sa reference BibTeX : \cite{cle} ou [@cle].
Le texte doit etre redigeable, pas une simple liste d'articles.
Viser 1-2 pages par direction exploree.]

## Articles cles

| # | Ref BibTeX | Titre | Annee | Pertinence | Contribution principale |
|---|------------|-------|-------|------------|------------------------|
| 1 | @smith2024katg | "Structural basis..." | 2024 | Haute | Mecanisme structural de katG S315T |
| 2 | @jones2023inh | "Global survey..." | 2023 | Haute | Epidemiologie mondiale resistance INH |
| ... | ... | ... | ... | ... | ... |

## Directions explorees

### 1. [Nom de la direction] (YYYY-MM-DD)

- **Requete** : `requete PubMed utilisee`
- **Resultats** : N articles trouves, M retenus
- **Resume** : [2-3 phrases resumant les trouvailles de cette direction]

### 2. [Autre direction] (YYYY-MM-DD)
...

## Directions a explorer (suggestions)

- [Direction identifiee pendant la lecture mais pas encore couverte]
- [Question ouverte soulevee par la litterature]
- [Facette du sujet non encore abordee]

## Lacunes identifiees

- [Ce qui manque dans la litterature sur ce sujet]
- [Questions sans reponse claire dans les articles trouves]
- [Contradictions entre articles]
```

### Approfondissement d'un sujet existant

1. **Ne pas reecrire la synthese existante** : la completer, l'enrichir
2. Ajouter les nouvelles trouvailles dans la section "Synthese" avec un
   marqueur de date si le changement est substantiel
3. Ajouter les nouveaux articles dans le tableau "Articles cles"
4. Ajouter la/les nouvelle(s) direction(s) dans "Directions explorees"
5. Mettre a jour "Directions a explorer" : retirer celles qui viennent
   d'etre couvertes, ajouter les nouvelles suggestions
6. Mettre a jour "Lacunes identifiees"
7. Mettre a jour la date "Derniere exploration"

---

## Phase 4 -- Persistance et rapport

### 4.1 Mise a jour de references.bib

**`litterature_review/references.bib` est le depot BibTeX partage du projet.**
Il est alimente par `/lit-review`, `/claim-check`, et tout skill qui rencontre
une reference. La memorisation des references est systematique : aucun article
lu, consulte ou utilise comme source ne doit rester sans entree BibTeX.

**Regles** :
- **Append** les nouvelles entrees BibTeX a la fin du fichier
- Ne jamais supprimer ou modifier les entrees existantes
- **Deduplication avant ajout** : verifier par DOI, PMID, ou titre que l'entree
  n'existe pas deja (un autre skill peut l'avoir ajoutee avant)
- Le champ `keywords` trace l'origine : `lit_review` pour ce skill,
  `claim_check` pour /claim-check. Si un article est trouve par les deux,
  ajouter les deux keywords a l'entree existante
- Le champ `annote` resume la contribution de l'article
- Si le fichier n'existe pas, le creer avec un commentaire d'en-tete :
  ```bibtex
  % Depot BibTeX partage du projet
  % Alimente par /lit-review, /claim-check, et tout skill utilisant des references
  % Le champ 'keywords' trace quel skill a ajoute l'entree
  % Le champ 'annote' resume la contribution de l'article
  % Derniere mise a jour : YYYY-MM-DD
  ```

### 4.2 Mise a jour de index.md

```markdown
# Revue de litterature

**Projet :** [nom du repertoire parent]
**Cree le :** YYYY-MM-DD
**Derniere mise a jour :** YYYY-MM-DD

## Sujets explores

| Sujet | Fichier | Articles | Derniere exploration | Directions couvertes |
|-------|---------|----------|----------------------|----------------------|
| katG mutations and INH resistance | katg_inh_resistance.md | 23 | 2026-04-05 | mechanisms, epidemiology, diagnostics |
| L4 lineage phylogeography | l4_phylogeography.md | 15 | 2026-04-02 | Europe, migration, molecular clock |

## Statistiques

- Articles totaux dans references.bib : N
- Sujets explores : M
- Derniere exploration : YYYY-MM-DD
```

### 4.3 Rapport de session

Afficher a l'utilisateur :

```
=== Lit-review terminee ===

Sujet      : katG mutations and INH resistance
Mode       : approfondissement
Fichier    : litterature_review/katg_inh_resistance.md

Directions explorees cette session : 2
  - Fitness cost et compensation (nouvelle)
  - Mecanismes moleculaires (mise a jour)

Articles evalues   : 47
  Nouveaux retenus : 14
  Deja connus      : 8
  Ignores          : 25

Entrees BibTeX ajoutees : 14
Total articles sur ce sujet : 37
Total references.bib : 52

Suggestions pour prochaine relance :
  - "Resistance INH hors katG (inhA, ndh, nat)"
  - "Modeles animaux et etudes in vivo"
  - "katG mutations dans les mycobacteries non-tuberculeuses"
```

En mode `--wide`, le rapport inclut en plus :

```
=== Recherche elargie (wide) ===

Pre-nomenclature :
  Termes precurseurs identifies : 5
  Requetes pre-nomenclature executees : 3
  Articles trouves hors recherche standard : 7
    dont pertinence haute : 3

Backward ref scan :
  Articles scannes (refs) : 4
  References totales parcourues : 187
  Nouvelles decouvertes : 9
    dont pertinence haute : 4

Decouverte notable :
  Loiseau et al. 2019 — identifie un clade enigmatique dans M. bovis/caprae
  correspondant a La4 avant sa denomination formelle.
  Trouve via : backward ref scan de @smith2023la4
```

---

## Consignes generales

### Ce que le skill DOIT faire

- **Construire incrementalement** : chaque relance enrichit, ne repart jamais de zero
- **Memoriser CHAQUE source en BibTeX** : aucun article lu, consulte, ou meme
  parcouru sans entree dans references.bib. C'est la regle la plus importante.
  Un article retenu = une entree BibTeX. Un article ecarte mais lu = une entree
  BibTeX quand meme (avec `annote = {Ecarte: raison}`)
- **Rediger une vraie synthese** : pas une liste d'articles mais un texte structure
  qui raconte une histoire scientifique avec des references
- **Identifier les lacunes** : la valeur ajoutee est aussi de voir ce qui manque
- **Deduplication rigoureuse** : ne pas ajouter deux fois le meme article
- **Lire les abstracts** : ne pas se fier aux seuls titres pour evaluer la pertinence
- **Afficher le plan de recherche** avant de l'executer

### Ce que le skill NE DOIT PAS faire

- Se fier a sa memoire pour les faits scientifiques : toujours rechercher
- Reecrire la synthese existante lors d'un approfondissement (enrichir seulement)
- Supprimer des entrees BibTeX existantes
- Retenir un article sans avoir lu son abstract
- Produire des entrees BibTeX avec des metadonnees inventees
- Ignorer les articles hors PubMed quand le sujet le justifie (preprints, rapports)
- **Lire ou utiliser un article sans l'ajouter dans references.bib**

### Integration avec l'ecosysteme

- **`litterature_review/references.bib`** : depot BibTeX partage. Alimente aussi
  par `/claim-check` et tout skill qui rencontre des references. Le champ
  `keywords` trace l'origine de chaque entree
- **`tbmonitor-papers`** : source **prioritaire** pour tout sujet TB / MTBC
  (~190 000 papiers PubMed TB pre-indexes, MeSH/auteurs/keywords en JSON,
  SQL sub-seconde). A interroger avant l'API PubMed live (voir Phase 2, 2.1)
- **`pubmed-database`** : utiliser sa syntaxe de requetes PubMed documentee
  dans ses references/ (search_syntax.md, common_queries.md, api_reference.md).
  Employe pour les recherches PubMed live, en complement de `tbmonitor-papers`
- **`bib-check`** : le references.bib produit peut etre verifie par bib-check
- **`claim-check`** : les claims des articles trouves peuvent alimenter claim-check,
  et claim-check alimente references.bib avec ses propres sources
- **`grant-proposal`** : la synthese peut alimenter la section "etat de l'art"


---

## Epilogue -- Resume et suggestion de suite

A la **fin de chaque invocation** (apres le rapport, le registre, ou la derniere
action du skill), ajouter systematiquement un bloc de cloture pour l'humain.

### Resume de session

Rappeler en 3-5 lignes :
- Ce qui vient d'etre fait dans cette invocation
- L'etat actuel du manuscrit (claims verifies, review en cours, references OK...)
- Les fichiers produits ou modifies

### Suggestion de prochaine etape

Evaluer l'etat global du manuscrit et proposer **la ou les commandes prioritaires**
parmi le pipeline de qualite :

| Commande | Quand la suggerer |
|----------|-------------------|
| `/claim-check` | Claims non verifies, article modifie depuis dernier run, ou jamais execute |
| `/bib-check` | References non verifiees, nouvelles refs ajoutees, ou jamais execute |
| `/deai-latex` | Article jamais nettoye IA, ou modifie substantiellement depuis |
| `/manuscript-review` | Article pret pour une evaluation globale, ou modifications majeures appliquees |
| `/lit-review [sujet]` | Un sujet necessite un approfondissement bibliographique |
| `/reviewer-response` | Une review existe non encore traitee, ou traitement en cours |
| `/reviewer-response next` | Remarques en attente dans la review active |

**Format de la suggestion** :

```
━━━━ Prochaine etape suggeree ━━━━

Le manuscrit a ete modifie par cette session. Je recommande :

  1. /claim-check --force    ← re-verifier les claims apres les modifications
  2. /bib-check              ← verifier les nouvelles references ajoutees

(ou /reviewer-response next s'il reste des remarques en attente)
```

Si a ton sens le travail est **termine** (toutes les reviews traitees, claims
verifies, bib OK, texte nettoye), le dire clairement :

```
━━━━ Etat du manuscrit ━━━━

Le manuscrit semble pret pour soumission/resoumission :
  ✅ Claims verifies (claim_check.md : 0 infirme)
  ✅ References verifiees (34/34, 0 suspecte)
  ✅ Review traitee (14/14 remarques resolues)
  ✅ Texte nettoye (deai-latex applique)

Aucune action supplementaire identifiee.
```
