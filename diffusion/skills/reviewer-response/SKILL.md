---
name: reviewer-response
description: >-
  Systematic point-by-point response to a manuscript review. Parses reviewer comments into
  individual tasks, critically evaluates each (agree or disagree), plans and executes
  analyses (bioinfo, literature, statistics) in experiments/, improves the manuscript, and
  produces a timestamped rebuttal letter in review/. Use when the user has received referee
  reports and wants to answer them, asks to handle a revision, or mentions a rebuttal or
  response letter. Invoke with review/file.md to start, next to advance, status for
  progress, R05 to jump to a specific remark.
argument-hint: "<review_file.md | next | status | R01..R99>"
---

# /reviewer-response -- Reponse systematique aux reviewers

Orchestre une reponse point par point a une review de manuscrit scientifique.
Chaque remarque du reviewer est traitee comme une tache independante :
evaluation critique, plan d'experience, analyses, amelioration de l'article,
redaction de la reponse.



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

## Modes d'invocation

```
/reviewer-response                               # Reprendre la derniere review non terminee
/reviewer-response review/2026-04-05_17h00.md    # Initialiser une nouvelle review
/reviewer-response next                          # Traiter la prochaine remarque
/reviewer-response status                        # Afficher la progression (toutes reviews)
/reviewer-response R05                           # Traiter la remarque #5 de la review active
/reviewer-response finalize                      # Generer la lettre de rebuttal
```

**Comportement par defaut (sans argument)** : trouver la derniere review non
integralement traitee et lancer `next` dessus. C'est le mode le plus courant :
l'utilisateur tape `/reviewer-response` et le skill reprend la ou il en etait.

---

## Arborescence et historisation

Chaque review recoit son propre repertoire de traitement a cote du fichier
source. Un index central `review/INDEX.md` permet de savoir ou en est
chaque review d'un coup d'oeil.

```
article/
├── main.tex
├── review/
│   ├── INDEX.md                             # Index central de toutes les reviews
│   │
│   ├── 2026-04-05_17h00.md                  # Review #1 (fichier source, read-only)
│   ├── 2026-04-05_17h00/                    # Repertoire de traitement de la review #1
│   │   ├── response.md                      # Registre persistant (remarques + reponses)
│   │   ├── rebuttal.md                      # Lettre de rebuttal (genere par finalize)
│   │   └── experiments/                     # Experiences liees a cette review
│   │       ├── R01_zenodo_deposit/
│   │       │   ├── PLAN.md
│   │       │   ├── scripts/
│   │       │   ├── results/
│   │       │   └── SUMMARY.md
│   │       └── R03_bingG_multilignee/
│   │           └── ...
│   │
│   ├── 2026-05-12_09h15.md                  # Review #2 (round 2, apres revision)
│   └── 2026-05-12_09h15/                    # Traitement de la review #2
│       ├── response.md
│       └── experiments/
```

### INDEX.md -- Index central

Ce fichier est cree automatiquement et mis a jour a chaque action du skill.
Il donne une vue d'ensemble de toutes les reviews traitees pour cet article.

```markdown
# Index des reviews

**Manuscrit :** article/main.tex
**Derniere mise a jour :** YYYY-MM-DD HH:MM

| # | Date | Fichier source | Remarques | Resolues | Statut |
|---|------|----------------|-----------|----------|--------|
| 1 | 2026-04-05 | 2026-04-05_17h00.md | 14 | 14/14 | COMPLETE |
| 2 | 2026-05-12 | 2026-05-12_09h15.md | 8 | 3/8 | EN COURS ← active |
```

**Statuts possibles** :
- `EN COURS` : review en cours de traitement (au plus une a la fois marquee `← active`)
- `COMPLETE` : toutes les remarques resolues, rebuttal genere
- `ABANDONNEE` : review annulee (ex. nouvelle version de review recue)

---

## Phase 0 -- Initialisation et resolution de la review active

### 0.1 Localiser le manuscrit

Chercher `main.tex` dans le repertoire courant ou remonter d'un niveau.

### 0.2 Charger l'index

Lire `review/INDEX.md` s'il existe. Identifier :
- La review **active** (derniere avec statut `EN COURS`)
- Le nombre total de reviews, leur etat

### 0.3 Determiner la review cible

| Argument | Comportement |
|----------|-------------|
| *(aucun)* | Reprendre la review active (derniere `EN COURS`). S'il n'y en a pas, chercher le plus recent fichier `review/*.md` non encore parse et lancer Phase 1 |
| Chemin `.md` | Initialiser le traitement de cette review (Phase 1). Si deja parsee, reprendre son registre |
| `next` | Idem que sans argument : reprendre la review active et traiter la prochaine remarque |
| `status` | Afficher l'index complet + le detail de la review active |
| `R{nn}` | Traiter la remarque #{nn} de la review active |
| `finalize` | Generer le rebuttal de la review active |

### 0.4 Charger le registre de la review cible

Lire `review/{date}/response.md` pour la review cible. Compter les remarques
par statut (RESOLU, EN COURS, EN ATTENTE).

### 0.5 Afficher l'etat

```
━━━━ Reviewer-response ━━━━
Manuscrit     : article/main.tex
Review active : review/2026-04-05_17h00.md (#1)
Registre      : review/2026-04-05_17h00/response.md
Progression   : 3/14 resolues | Prochaine : R04 [MAJEUR]

Historique :
  #1  2026-04-05  14 remarques  3/14  EN COURS ← active
```

### 0.6 Router

Selon l'argument, enchainer sur Phase 1, Phase 2, ou Phase 3.

---

## Phase 1 -- Parsing et triage de la review

### 1.1 Extraction des remarques

Lire la review en entier. Extraire chaque point numerote dans les sections
structurees :
- `## I. PREOCCUPATIONS MAJEURES` → severite MAJEUR
- `## II. PREOCCUPATIONS MODEREES` → severite MODERE
- `## III. PREOCCUPATIONS MINEURES` → severite MINEUR
- Tout point dans `## V. RECOMMANDATIONS FINALES` → mapper sur la severite
  correspondante (Obligatoires = MAJEUR, Fortement souhaitables = MODERE,
  Souhaitables = MINEUR)

Si la review n'utilise pas ce format exact, s'adapter : chercher les titres
numerotes (### 1., ### 2., etc.) et inferer la severite du contexte.

### 1.2 Structuration

Pour chaque remarque extraire :

| Champ | Description |
|-------|-------------|
| **ID** | `R01`, `R02`... dans l'ordre de la review (MAJEUR d'abord) |
| **Severite** | MAJEUR / MODERE / MINEUR |
| **Enonce** | Texte complet du reviewer (verbatim) |
| **Resume** | Une phrase de synthese (~15 mots) |
| **Lignes** | Numeros de ligne dans le .tex si mentionnes |
| **Type** | `analyse` / `redaction` / `donnees` / `structure` (estimation initiale) |

### 1.3 Creation du repertoire de traitement et du registre

1. Creer `review/{basename_sans_ext}/` (ex. `review/2026-04-05_17h00/`)
2. Creer `review/{basename}/experiments/`
3. Ecrire le registre `review/{basename}/response.md` :

```markdown
# Registre de reponse au reviewer

**Review source :** [chemin relatif du fichier .md source]
**Manuscrit :** [chemin main.tex]
**Review #** : {numero sequentiel}
**Date debut :** YYYY-MM-DD
**Derniere mise a jour :** YYYY-MM-DD

## Progression

| Resolues | En cours | En attente | Total |
|----------|----------|------------|-------|
| 0        | 0        | N          | N     |

## Remarques

| ID  | Severite | Type     | Resume                        | Verdict | Statut     | Repertoire |
|-----|----------|----------|-------------------------------|---------|------------|------------|
| R01 | MAJEUR   | donnees  | Infrastructure non perenne    | —       | EN ATTENTE | —          |
| R02 | MAJEUR   | redaction| Subjectivite Phase I          | —       | EN ATTENTE | —          |
| ... | ...      | ...      | ...                           | ...     | ...        | ...        |

## Reponses detaillees

<!-- Rempli au fur et a mesure du traitement de chaque remarque -->
```

### 1.4 Mise a jour de l'index central

Mettre a jour (ou creer) `review/INDEX.md` :
- Ajouter une ligne pour cette review avec statut `EN COURS ← active`
- Si une autre review etait marquee `← active`, retirer le marqueur
- Incrementer le numero sequentiel

### 1.5 Affichage et confirmation

Afficher le tableau complet a l'utilisateur avec un resume :

```
Parsing termine : N remarques extraites
  MAJEUR  : X
  MODERE  : Y
  MINEUR  : Z

Repertoire de traitement : review/2026-04-05_17h00/
Index mis a jour         : review/INDEX.md

Premiere remarque a traiter : R01 — [resume]
Lancer /reviewer-response ou /reviewer-response next pour commencer.
```

---

## Phase 2 -- Traitement d'une remarque

Declenchee par `next` (prochaine non resolue) ou `R{nn}` (specifique).

### Etape 2.1 -- Evaluation critique

**Lire la remarque** (enonce complet) **et le passage concerne** de l'article.

Poser les 3 questions fondamentales :

| Question | Si OUI | Si NON |
|----------|--------|--------|
| Le reviewer a-t-il **factuellement raison** ? | Correction necessaire | Argumenter / defendre |
| La demande est-elle **realisable** dans le cadre de cet article ? | Planifier l'execution | Expliquer les contraintes |
| La correction **ameliorerait-elle** reellement l'article ? | Prioriser | Renforcer pour prevenir la meme remarque |

**Attribuer un verdict** :

| Verdict | Signification | Action |
|---------|---------------|--------|
| `ACCEPTE` | Le reviewer a raison, on corrige/complete | Plan d'experience → analyses → modification article |
| `PARTIELLEMENT ACCEPTE` | Raison sur le fond, solution differente | Proposer une alternative, analyser, modifier |
| `REFUTE` | Le reviewer a tort ou la demande est hors propos | Renforcer l'article pour prevenir, rediger reponse diplomatique |
| `HORS PERIMETRE` | Demande irrealisable (wet lab, refonte totale, autre etude) | Reponse polie expliquant pourquoi, eventuellement ajouter en Perspectives |

**IMPERATIF : Afficher le verdict avec sa justification a l'utilisateur
et attendre sa validation avant de poursuivre.** L'utilisateur peut ajuster
le verdict ou donner des instructions supplementaires.

Format d'affichage :

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
R01 [MAJEUR] — Infrastructure non perenne
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reviewer :
> TBannotator v2 est heberge sur un serveur personnel (freeboxos.fr).
> L'article reconnait ce probleme mais la reproductibilite est compromise.
> Recommandation : deposer un jeu minimal sur Zenodo.

Passage concerne (L.674) :
> The pipeline's infrastructure dependency warrants consideration...

Verdict : ACCEPTE
Justification : Le reviewer a raison — la dependance a un serveur personnel
est un point faible reel pour la reproductibilite. Le depot Zenodo est
faisable et ameliore significativement l'article.

Type d'action : donnees (depot externe)

Confirmer ce verdict ? [Entrer pour continuer, ou donner des instructions]
```

### Etape 2.2 -- Plan d'experience

Si le verdict necessite des analyses ou des actions non triviales :

1. Creer le repertoire `review/{review_dir}/experiments/R{ID}_{nom_court}/`
2. Ecrire `review/{review_dir}/experiments/R{ID}_{nom_court}/PLAN.md` :

```markdown
# Plan d'experience — R{ID} : {titre}

**Remarque :** {enonce resume}
**Verdict :** {verdict}
**Date :** YYYY-MM-DD

## Objectif
{Ce qu'on cherche a demontrer ou produire}

## Donnees necessaires
- {Source 1} : {description, comment l'obtenir}
- {Source 2} : ...

## Methode
1. {Etape 1}
2. {Etape 2}
3. ...

## Critere de succes
{Comment savoir que l'analyse est concluante}

## Scripts a produire
- `scripts/{nom}.py` : {description}
- ...

## Resultats attendus
- `results/{fichier}` : {description}
```

3. **Afficher le plan a l'utilisateur et attendre validation.**

Si le verdict est `REFUTE` ou `HORS PERIMETRE`, le plan est redige directement
(pas d'experience, juste la strategie de reponse et l'eventuel renforcement
du texte).

### Etape 2.3 -- Execution des analyses

Executer le plan valide :

1. Ecrire les scripts dans `review/{review_dir}/experiments/R{ID}/scripts/`
2. Lancer les analyses :
   - **Bioinfo** : TBannotator MCP, Python (pandas, scipy, matplotlib, ete3...)
   - **Litterature** : WebSearch + WebFetch pour les abstracts. **Regle de
     priorite** : quand un reviewer reclame des citations supplementaires sur
     un sujet TB / MTBC, passer d'abord par le skill `tbmonitor-papers`
     (~190 000 papiers PubMed TB, acces SQL sub-seconde avec MeSH / auteurs /
     mots-cles en JSON) AVANT de retomber sur `lit-review` ou WebSearch.
   - **Statistiques** : scripts Python avec tests adaptes
   - **Donnees** : telechargements, requetes BDD, compilations
3. Sauvegarder tous les resultats dans `review/{review_dir}/experiments/R{ID}/results/`
4. **Afficher la progression a chaque etape importante** :

```
R01 — Execution du plan d'experience
  [1/3] Preparation du depot Zenodo... OK
  [2/3] Generation du manifest CSV... OK
  [3/3] Verification des fichiers... OK
```

5. Si les resultats ne sont pas concluants ou revelent un probleme inattendu :
   - **Signaler immediatement** a l'utilisateur
   - Proposer des analyses complementaires
   - Iterer (retour a 2.3) si necessaire

### Etape 2.4 -- Regard critique sur les resultats

Avant d'integrer quoi que ce soit dans l'article, evaluer :

1. Les resultats soutiennent-ils la correction envisagee ?
2. Y a-t-il des resultats inattendus qui changent l'interpretation ?
3. Les resultats sont-ils suffisamment robustes pour etre publies ?
4. Faut-il des analyses de sensibilite supplementaires ?

Si des analyses supplementaires sont necessaires → retour a 2.3.

Ecrire `review/{review_dir}/experiments/R{ID}/SUMMARY.md` :

```markdown
# Synthese — R{ID} : {titre}

## Resultats cles
- {Resultat 1}
- {Resultat 2}

## Interpretation
{Ce que les resultats signifient pour l'article}

## Modifications a apporter
- Section {X}, L.{YYY} : {description du changement}
- Nouvelle figure/table : {description}
- Materiel supplementaire : {description}

## Texte propose
{Paragraphe(s) pret(s) a inserer, en anglais scientifique}
```

### Etape 2.5 -- Modification de l'article

1. **Afficher le plan de modification** :

```
Modifications planifiees pour R01 :
  1. Section "Data Availability" (L.697) : ajouter DOI Zenodo
  2. Section 3.1 (L.674) : modifier la phrase sur l'infrastructure
  3. Nouveau : Supplementary Table S7 (manifest du depot)

Appliquer ces modifications ?
```

2. Appliquer les editions sur `main.tex` (et fichiers inclus si necessaire)
3. Verifier la compilation LaTeX (`pdflatex`)
4. Si erreur de compilation : corriger et recompiler

### Etape 2.6 -- Redaction de la reponse

Ajouter la reponse dans la section `## Reponses detaillees` du registre :

```markdown
### R{ID} — {titre}

**Reviewer :**
> {citation exacte de la remarque}

**Verdict :** {ACCEPTE / PARTIELLEMENT ACCEPTE / REFUTE / HORS PERIMETRE}

**Reponse au reviewer :**
{Texte en anglais, formel, respectueux. Commence par "We thank the reviewer..."
ou "We appreciate this comment..." selon le verdict.
Si ACCEPTE : decrire ce qui a ete fait.
Si REFUTE : expliquer pourquoi avec des arguments scientifiques,
mentionner les renforcements apportes.}

**Modifications apportees :**
- L.{XXX} : {description}
- Nouvelle figure/table : {description}
- Experiences : `experiments/R{ID}_{nom}/`

**Statut : RESOLU**
```

### Etape 2.7 -- Mise a jour et progression

1. Mettre a jour le tableau du registre (verdict, statut → RESOLU, repertoire)
2. Mettre a jour les compteurs de progression
3. Mettre a jour la date de derniere modification
4. **Afficher la progression** :

```
━━━━ Progression ━━━━
R01 [MAJEUR]  Infrastructure Zenodo       RESOLU ✅
R02 [MAJEUR]  Subjectivite Phase I        EN ATTENTE
R03 [MAJEUR]  Validation BIN+G multi      EN ATTENTE
...
Resolues : 1/14 | Prochaine : R02

Lancer /reviewer-response pour continuer.
```

### Routage automatique quand toutes les remarques sont resolues

Quand `next` est invoque (explicitement ou par defaut) et qu'il **ne reste
aucune remarque EN ATTENTE** :

- **Si le rebuttal n'a pas encore ete genere** → enchainer automatiquement
  sur **Phase 3** (finalize). Afficher :

```
Toutes les remarques sont resolues (N/N).
Generation automatique de la lettre de rebuttal...
```

- **Si le rebuttal a deja ete genere** (statut `COMPLETE` dans INDEX.md) →
  enchainer sur **Phase 4** (bilan de cloture). Afficher :

```
Cette review a ete integralement traitee.
Generation du bilan de cloture...
```

L'utilisateur n'a jamais besoin de taper `finalize` manuellement,
le workflow `next` → `next` → ... → finalize → bilan se deroule naturellement.

---

## Phase 3 -- Generation de la lettre de rebuttal

Declenchee automatiquement quand le dernier `next` constate que toutes les
remarques sont resolues, ou manuellement par `/reviewer-response finalize`.

1. Compiler toutes les reponses detaillees du registre de la review active
2. Generer `review/{review_dir}/rebuttal.md` au format journal standard :
3. Mettre a jour `review/INDEX.md` : statut → `COMPLETE`

```markdown
# Response to Reviewer Comments

**Manuscript:** {titre}
**Authors:** {auteurs}
**Date:** YYYY-MM-DD

Dear Editor,

We thank the reviewer for their thorough and constructive evaluation of our
manuscript. We have carefully addressed each comment as detailed below.
All changes in the revised manuscript are highlighted in [blue/track changes].

---

## Response to Reviewer 1

### Major Concerns

**Comment 1:** {citation}

**Response:** {reponse}

**Changes:** {liste des modifications avec numeros de ligne}

---

[Repeter pour chaque remarque]

---

## Summary of Changes

| Section | Change | Motivation |
|---------|--------|-----------|
| ... | ... | ... |

## New Supplementary Materials

- Table S{X}: ...
- Figure S{Y}: ...
```

4. Afficher un resume final :

```
Lettre de rebuttal generee : review/{review_dir}/rebuttal.md
Index mis a jour            : review/INDEX.md (statut → COMPLETE)

Resume :
  Remarques MAJEUR  : X/X resolues
  Remarques MODERE  : Y/Y resolues
  Remarques MINEUR  : Z/Z resolues
  Experiences       : N repertoires dans experiments/
  Modifications     : M edits dans main.tex
```

---

## Phase 4 -- Bilan de cloture

Declenchee automatiquement quand `next` est invoque sur une review deja
`COMPLETE` (rebuttal genere). C'est le dernier acte du cycle de review :
un bilan detaille pour l'humain.

### 4.1 Lecture de l'etat avant/apres

1. Lire le **registre** `review/{review_dir}/response.md` en entier
2. Lire le **manuscrit actuel** `main.tex`
3. Lire la **review source** pour rappeler les preoccupations initiales
4. Si un `claim_check.md` existe, le lire aussi pour l'etat des claims
5. Lister tous les `experiments/R*/SUMMARY.md` pour les resultats produits

### 4.2 Redaction du bilan

Generer `review/{review_dir}/bilan.md` avec la structure suivante :

```markdown
# Bilan de cloture — Review #{n}

**Manuscrit :** {titre}
**Review source :** {chemin}
**Date debut traitement :** YYYY-MM-DD
**Date cloture :** YYYY-MM-DD

---

## 1. Resume executif

{Paragraphe de synthese : combien de remarques, combien acceptees/refutees,
quelles analyses majeures realisees, quel impact global sur l'article.}

## 2. Inventaire des actions realisees

| ID  | Remarque (resume)       | Verdict              | Action realisee                          |
|-----|------------------------|----------------------|------------------------------------------|
| R01 | Infrastructure Zenodo  | ACCEPTE              | Depot Zenodo, DOI ajoute dans le texte   |
| R02 | Subjectivite Phase I   | PARTIELLEMENT ACCEPTE| Discussion renforcee + captures iTOL     |
| R03 | Validation BIN+G       | ACCEPTE              | Nouvelle analyse multi-lignee (Fig. S8)  |
| ... | ...                    | ...                  | ...                                      |

## 3. Analyses et experiences produites

{Pour chaque repertoire experiments/R*/ :}

### R01 — {titre}
- **Repertoire :** `review/{dir}/experiments/R01_{nom}/`
- **Scripts :** {liste}
- **Resultats cles :** {resume en 2-3 phrases}
- **Impact sur l'article :** {sections modifiees, figures ajoutees}

### R03 — {titre}
- ...

## 4. Etat du manuscrit : avant vs apres cette review

### Avant la review
- Score estime : {score de la review}
- Points faibles identifies : {liste des preoccupations majeures}
- Donnees manquantes : {ce qui n'etait pas fourni}

### Apres le traitement
- Modifications textuelles : {N edits dans M sections}
- Nouvelles figures/tables : {liste}
- Nouveau materiel supplementaire : {liste}
- Donnees deposees : {DOI, liens}
- Points faibles restants : {le cas echeant, sinon "aucun identifie"}

### Delta
{Paragraphe narratif : ce qui a concretement change dans l'article,
en quoi il est plus solide maintenant.}

## 5. Etat des connaissances sur le sujet de l'article

{Section la plus importante du bilan. Synthetiser ce que l'on sait
MAINTENANT sur le sujet, en integrant les resultats des analyses
menees pendant la review.}

### Ce qui est nouveau par rapport a la litterature
{Contributions originales de l'article, consolidees par cette review.
Ce que personne d'autre n'a publie.}

### Ce qui est acquis et consolide
{Resultats confirmes, valides empiriquement pendant cette etape
de review. Par exemple : la validation BIN+G multi-lignee,
les marqueurs de nouvelles lignees, etc.}

### Ce qui a ete corrige par cette etape de review
{Erreurs factuelles corrigees, claims renforces, analyses ajoutees
en reponse au reviewer. Ce que l'article disait avant qui etait
inexact ou insuffisant.}

### Questions ouvertes
{Ce que l'article ne resout pas encore, les limitations reconnues,
les pistes pour de futurs travaux.}

## 6. Recommandation de prochaine etape

{Conseiller l'humain : resoumission immediate ? Attendre un preprint
compagnon ? Analyses supplementaires a prevoir ?}

## 7. Enseignements transferables

{Pour chaque remarque ACCEPTE, PARTIELLEMENT ACCEPTE ou REFUTE du registre : releve-t-elle
un fait de DOMAINE qui depasse ce manuscrit (methode, biais, resultat de litterature), ou
un defaut REUTILISABLE d'un skill/outil canonique (claim-check, bib-check, ce skill
lui-meme) plutot qu'une simple erreur locale au manuscrit ? Lister, pour chaque
enseignement retenu : la remarque source, le fichier KB ou l'outil concerne, et l'action
faite ou reportee.}

| ID  | Enseignement                              | Destination                | Action                    |
|-----|--------------------------------------------|-----------------------------|---------------------------|
| R03 | {resume du fait transferable}               | `~/.agents/knowledge/X.md`  | verse le {date}           |
| R07 | {defaut d'outil revele}                     | skill `Y`                   | corrige le {date}         |
| ... | ...                                          | ...                          | reporte, piste `Pz` ouverte |

{Si aucun enseignement transferable n'a ete identifie, l'ecrire explicitement et dire
pourquoi (remarques toutes locales au manuscrit) — ne jamais laisser cette section vide
sans un mot : le silence sur cette question est precisement ce qu'elle corrige.}
```

### 4.2bis Enseignements transferables (avant l'affichage)

Avant d'afficher le bilan, relire le registre `response.md` en entier et vérifier, pour
CHAQUE remarque ACCEPTE, PARTIELLEMENT ACCEPTE ou REFUTE (jamais HORS PERIMETRE, qui ne
dit rien du manuscrit) :

1. **Fait de domaine transferable ?** Le point souleve par le reviewer, ou l'analyse menee
   pour y repondre, etablit-il quelque chose qui depasse CE manuscrit — un biais methodo,
   un resultat de litterature, une regle de robustesse — et qui merite d'etre versé dans la
   base de connaissances transversale du domaine (`~/.agents/knowledge/<domaine>.md`, ex.
   `tuberculosis.md` pour un projet MTBC) ?
2. **Defaut d'outil reutilisable ?** La remarque a-t-elle revele qu'un skill/outil canonique
   (`claim-check`, `bib-check`, `manuscript-review`, ce skill lui-meme) ratait un cas, ou
   qu'un contournement manuel a ete necessaire pendant le traitement de cette remarque ?

Si l'une des deux reponses est OUI : **agir tout de suite**, pas seulement le signaler —
editer le fichier KB concerne, ou le skill/outil defaillant. Si l'action est trop lourde
pour cette session (necessite une recherche, une decision de l'utilisateur, un chantier
separe), ouvrir une piste explicite dans le `pistes.md` du projet qui trace le report et sa
raison, plutot que de laisser l'enseignement se perdre dans le bilan une fois cloture.
Renseigner le tableau du §7 en consequence.

Ce pas ne re-ouvre AUCUNE remarque deja tranchee : c'est une relecture a posteriori du
registre, jamais une nouvelle iteration de traitement.

### 4.3 Affichage du bilan a l'utilisateur

Afficher le bilan en entier a l'utilisateur (c'est le moment de faire
le point, pas de faire court). Puis conclure :

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Review #{n} integralement traitee ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fichiers produits :
  Registre   : review/{dir}/response.md
  Rebuttal   : review/{dir}/rebuttal.md
  Bilan      : review/{dir}/bilan.md
  Experiences: review/{dir}/experiments/ (N repertoires)

Index : review/INDEX.md (review #{n} → COMPLETE)

Aucune remarque en attente. Manuscrit pret pour resoumission.
```

### 4.4 Mise a jour finale de l'index

Verifier que `review/INDEX.md` est bien a jour avec le statut `COMPLETE`
et la date de cloture.

---

## Consignes generales

### Ce que le skill DOIT faire

- Traiter **une seule remarque a la fois**, chaque remarque est une tache
  complete et independante (sauf si l'utilisateur demande un batch)
- **Afficher le verdict** et attendre confirmation avant toute action
- **Afficher le plan d'experience** et attendre confirmation avant de lancer
- **Afficher le plan de modification** et attendre confirmation avant d'editer
- **Tenir l'humain informe** a chaque transition d'etape : un message clair
  indiquant ce qui vient d'etre fait et ce qui va suivre
- Creer des repertoires d'experience **propres et documentes** (PLAN.md, SUMMARY.md)
- **Compiler le LaTeX** apres chaque modification de l'article
- Maintenir le **registre a jour en temps reel** (jamais de desynchronisation)
- Etre **diplomatique mais ferme** dans les reponses : ne pas s'ecraser devant
  le reviewer, mais ne pas etre arrogant non plus
- Pour les verdicts REFUTE : toujours **renforcer l'article** (ajouter une phrase,
  une reference, une nuance) meme si le reviewer a tort, cela previent qu'un
  prochain reviewer souleve la meme question

### Ce que le skill NE DOIT PAS faire

- Traiter toutes les remarques d'un coup sans validation humaine
- Modifier l'article sans avoir presente les resultats d'analyse
- Accepter aveuglementement toutes les demandes du reviewer
- Refuser aveuglement toutes les demandes du reviewer
- Lancer des analyses sans plan valide par l'utilisateur
- Ignorer des resultats inattendus ou derangeants
- Produire des reponses serviles ("We fully agree with the reviewer's excellent
  suggestion"), etre professionnel, pas obsequieux
- Oublier de mettre a jour le registre apres chaque action
- Laisser l'utilisateur dans le flou sur l'etat d'avancement

### Ton des reponses au reviewer

| Verdict | Ton |
|---------|-----|
| ACCEPTE | "We thank the reviewer for this pertinent observation. We have now..." |
| PARTIELLEMENT ACCEPTE | "We appreciate this suggestion. While [nuance], we have addressed the underlying concern by..." |
| REFUTE | "We respectfully disagree with this assessment. [Argument factuel]. To clarify this point, we have strengthened the manuscript by..." |
| HORS PERIMETRE | "We acknowledge this interesting direction. However, [raison]. We have added this as a perspective for future work (Section X)." |

### Si argument fourni

L'argument `$ARGUMENTS` determine le mode :
- Chemin vers un `.md` → Phase 0 + Phase 1 (parsing de cette review)
- `next` → Phase 0 + Phase 2 (prochaine remarque de la review active)
- `status` → Phase 0 (affichage index + detail review active)
- `R{nn}` (ex. `R05`) → Phase 0 + Phase 2 sur cette remarque
- `finalize` → Phase 0 + Phase 3 (rebuttal de la review active)

**Si pas d'argument** (mode par defaut, le plus courant) :
1. Charger `review/INDEX.md`
2. Trouver la derniere review avec statut `EN COURS`
3. Si trouvee : lancer Phase 2 (`next`) sur cette review
4. Si aucune review en cours : chercher le plus recent fichier
   `review/*.md` (hors `INDEX.md` et sous-repertoires) non encore parse,
   et lancer Phase 1
5. Si tout est `COMPLETE` : afficher l'index et indiquer que toutes
   les reviews sont traitees


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
