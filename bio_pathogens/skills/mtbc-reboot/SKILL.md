---
name: mtbc-reboot
description: >-
  Reboot complet d'un projet MTBC. Archive toute la connaissance
  accumulee (decouvertes, claims, scripts, donnees) dans
  archives/YYYY-MM-DD_reboot/ avec tags de confiance
  (VERIFIE/A VERIFIER/INCERTAIN/REFUTE). Reinitialise le projet
  en structure propre. Scanne les projets voisins pour convergences.
  Reanalyse claim par claim avec revue critique du code source ; pour
  les claims qui necessitent un appui litterature, interroge tbmonitor
  (corpus PubMed TB pre-indexe ~190k papiers) avant WebSearch.
  Bloque la redaction tant que la reanalyse n'est pas complete.

  Use when: a project has accumulated too much drift, stale results,
  or unverified claims to continue incrementally; when restarting a
  study after a long pause with uncertain legacy; when claim-check
  reveals too many unverified claims to patch individually; when pivoting a
  project's direction while preserving prior knowledge.
argument-hint: "<sous-commande> [archive | survey | plan | claim N | status | article]"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, mcp__tbannotator__tool_query_postgres, mcp__tbannotator__tool_get_schema, mcp__tbmonitor__execute_sql, mcp__tbmonitor__show_schema
user-invocable: true
---

# /mtbc-reboot -- Reboot critique d'un projet MTBC

Archive la connaissance accumulee d'un projet MTBC avec des tags de confiance,
reinitialise le projet en structure propre, puis re-verifie chaque claim en
portant un regard critique sur le code ET les resultats. L'article est bloque
tant que la reanalyse n'est pas terminee.

**Principe cardinal** : ne rien prendre pour argent comptant. Chaque
decouverte, chaque script, chaque chiffre est traite comme "a credit" jusqu'a
re-verification independante avec les donnees et outils actuels.


> [!NOTE]
> **Frontiere bilan / deepen / reboot (3 skills voisins, ne pas confondre).**
> `mtbc-bilan` PHOTOGRAPHIE l'etat su (lecture seule) ; `mtbc-deepen` EXPLORE de
> nouvelles pistes quand un projet stagne ; `mtbc-reboot` (ce skill) REPART a zero
> proprement quand la derive est trop forte -- archive taggee VERIFIE / A VERIFIER /
> REFUTE + re-analyse claim par claim, **operation destructrice** qui bloque la redaction
> tant qu'elle n'est pas finie. Regle : photographier -> explorer -> repartir. Ne pas
> rebooter ce qu'un simple bilan ou un deepen suffirait a traiter.

## Prealable -- Consultation memoire projet

**Avant toute action** :

1. Lire `CLAUDE.md` du projet (si present).
2. Lire `cahier_de_labo.md` ou `JOURNAL.md` (si present).
3. Lire `~/.claude/knowledge/tuberculosis.md` pour le contexte transversal MTBC.
4. Si `reboot_state.md` existe : lire l'etat courant du reboot en cours.

Afficher un bref resume avant de commencer :

```
Etat projet : [titre]
  Cahier       : [N entrees ou "absent"]
  Claim-check  : [N claims, M infirmes ou "jamais execute"]
  Reboot       : [phase courante ou "jamais execute"]
  Derniere activite : [date]
```


## Declenchement

```
/mtbc-reboot archive    # Phase 1 : archivage + reset
/mtbc-reboot survey     # Phase 2 : scan inter-projets
/mtbc-reboot plan       # Phase 3 : generation du registre de reanalyse
/mtbc-reboot claim N    # Phase 3 : reanalyse du claim #N
/mtbc-reboot status     # Consultation : etat d'avancement (sans gate)
/mtbc-reboot article    # Phase 4 : deblocage article (gated)
```

**Ordre impose** : `archive` → `survey` → `plan` → `claim N` (iteratif) →
`article`. Les gates sont verifiees via `reboot_state.md`. Le sous-commande
`status` est accessible a tout moment.

Sans argument : equivalent a `status` si un reboot est en cours, sinon
afficher l'aide.

---

## Machine a etats : reboot_state.md

Fichier cree a la racine du projet par la sous-commande `archive`.
Tracker YAML frontmatter + prose minimale.

```yaml
---
reboot_date: YYYY-MM-DD
archive_path: archives/YYYY-MM-DD_reboot/
phase: ARCHIVE_COMPLETE
claims_total: 0
claims_reverified: 0
article_blocked: true
---

Reboot initie le YYYY-MM-DD.
Utiliser /mtbc-reboot status pour voir l'avancement.
```

Valeurs de `phase` :
- `ARCHIVE_COMPLETE` → autorise `survey`
- `SURVEY_COMPLETE` → autorise `plan`
- `REANALYSIS_IN_PROGRESS` → autorise `claim N`
- `REANALYSIS_COMPLETE` → autorise `article`
- `ARTICLE_UNBLOCKED` → reboot termine

---

## Phase 1 -- ARCHIVE (`/mtbc-reboot archive`)

L'objectif est de capturer TOUT ce que le projet a produit et decouvert,
puis de reinitialiser la couche de connaissance (CLAUDE.md, cahier, article)
tout en preservant les artefacts reutilisables (data, scripts, resultats).

### Etape 1 : Scan exhaustif du projet

1. **Lire CLAUDE.md integralement** :
   - Titre du projet, lignee, question scientifique.
   - Conventions locales, statut declare.

2. **Lire le cahier integralement** (cahier_de_labo.md ou JOURNAL.md) :
   - Si > 5000 lignes : lire par chunks de 2000, **jamais tronquer**.
   - Extraire :
     - Toutes les decouvertes (sections "Resultats", "Connaissances acquises")
     - Toutes les pistes futures mentionnees, avec leur statut ulterieur
       (close, abandonnee, open)
     - Les echecs instructifs (sections "Negatifs")
     - Les mecanismes biologiques invoques

3. **Lire article/main.tex** (si present) :
   - Resoudre les `\input{}` et `\include{}`.
   - Extraire la structure des sections redigees.
   - Identifier les claims factuels (meme logique que `/claim-check` Phase 1).

4. **Lire article/claim_check.md** (si present) :
   - Importer les statuts existants de chaque claim.

5. **Inventaire des scripts** :
   - `Glob analyses/phase*_*.py` et `Glob analyses/*.py`
   - Pour chaque script : lire la premiere docstring (ou les 10 premieres
     lignes), noter l'objectif, les inputs, les outputs.
   - Detecter les gaps de phases (phase1 + phase3 sans phase2).

6. **Inventaire des donnees** :
   - `Glob data/*` — lister avec tailles.
   - Identifier la lignee BDD : `ls bdd/actuelle/<lignee>/` si accessible.
   - Compter les souches actuellement dans la BDD.

7. **Inventaire des resultats** :
   - `Glob resultats/**/*.{pdf,png,svg,csv,tsv,nwk,tree}`
   - Lister les fichiers cles.

8. **Litterature** :
   - Lire `litterature_review/index.md` si present.
   - Compter les references dans `litterature_review/references.bib`
     et `article/references.bib`.
   - Lister les fiches thematiques.

9. **Bilans** :
   - `Glob bilans/*.md` — lire les verdicts et pistes.

10. **Reviews** :
    - Lire `article/review/INDEX.md` si present.

11. **Knowledge et memoires externes au projet** :
    - Lire `~/.claude/knowledge/tuberculosis.md` et identifier les entrees
      liees a ce projet. Criteres d'identification :
      - Mention explicite du nom de lignee du projet (ex: "L4.9", "La4")
      - Mention du nom de repertoire du projet
      - Decouverte qui correspond a une entree du cahier de ce projet
      - Entree datee au meme moment qu'une session de travail sur ce projet
      **Attention** : ne PAS inclure les entrees generiques MTBC qui ne sont
      pas specifiques a ce projet (ex: architecture TBannotator, seuils SNP
      epidemiologiques, distribution geographique des lignees). Seules les
      entrees qui portent sur des **resultats ou decouvertes** de ce projet
      specifique sont concernees.
    - Lire `~/.claude/projects/.../memory/MEMORY.md` et identifier les
      fichiers `project_*.md` lies a ce projet (par nom de lignee ou titre).


### Etape 2 : Production de knowledge_legacy.md

Creer `archives/YYYY-MM-DD_reboot/` (mkdir -p).

Ecrire `archives/YYYY-MM-DD_reboot/knowledge_legacy.md` :

```markdown
# Knowledge Legacy -- [Projet] -- YYYY-MM-DD

**Genere par** : /mtbc-reboot archive
**Date** : YYYY-MM-DD HH:MM
**Projet source** : [chemin absolu]

---

## Decouvertes

Toutes les decouvertes extraites du cahier, de l'article, et des bilans.

| # | Date | Enonce | Confiance | Source | Script | Data | Notes |
|---|------|--------|-----------|--------|--------|------|-------|
| 1 | 2026-03-15 | "La lignee X est soeur de Y" | VERIFIE | cahier, RAxML bs=95 | phase3_tree.py | data/alignment.fasta | — |
| 2 | 2026-03-20 | "tMRCA = 350 CE" | INCERTAIN | cahier, IC [-6000;-1000] | phase5_clock.py | data/dates.csv | Signal faible |
| ... | ... | ... | ... | ... | ... | ... | ... |

## Claims du manuscrit

[Si article/claim_check.md existait, importer chaque claim avec mapping :
 confirme → VERIFIE, a_corriger → REFUTE,
 partiellement_confirme → A VERIFIER,
 non_verifiable → INCERTAIN,
 jamais verifie → A VERIFIER]

[Si claim_check.md n'existait pas mais que main.tex contient des claims :
 extraire les claims via la logique de /claim-check Phase 1, tous tagges
 A VERIFIER]

| # | P | Section | Enonce | Legacy | Confiance | Source | Notes |
|---|---|---------|--------|--------|-----------|--------|-------|

## Scripts et analyses

| Phase | Script | Description | Etat | Qualite estimee | Output |
|-------|--------|-------------|------|-----------------|--------|
| 1 | phase1_metadata.py | Extraction ENA | Fonctionnel | A auditer | data/strains.csv |

**Qualite estimee** = premiere impression visuelle du scan, PAS un audit.
Valeurs : "A auditer" (defaut), "Semble solide", "Suspect" (si red flags).
L'audit detaille se fera en Phase 3 (sous-commande `claim`).

## Donnees

| Fichier | Type | Taille | Provenance | Description |
|---------|------|--------|------------|-------------|

## Souches BDD

- **Lignee** : [nom]
- **Repertoire** : [bdd/actuelle/<lignee>/]
- **Nombre de souches actuel** : [N]
- **Note** : [si different du N mentionne dans l'article/cahier, le signaler]

## Litterature

- **Fiches thematiques** : [N fiches dans litterature_review/]
- **References totales** : [N dans references.bib]
- **Sujets couverts** : [liste]
- **Lacunes identifiees** : [depuis index.md]

## Pistes non explorees

[Collectees depuis bilans/ et cahier "Pistes futures"]

| # | Piste | Statut | Source | Date |
|---|-------|--------|--------|------|
| 1 | "Tester les marqueurs sur un outgroup" | open | cahier 2026-03-20 | 2026-03-20 |
| 2 | "Analyser la resistance INH" | close | cahier 2026-04-01 (traite) | 2026-03-25 |
```

### Tags de confiance

| Tag | Signification | Mapping depuis claim_check |
|-----|---------------|----------------------------|
| `VERIFIE` | Reproduit avec preuve tangible | confirme |
| `A VERIFIER` | Plausible mais non confirme independamment | partiellement_confirme, ou jamais verifie |
| `INCERTAIN` | Preuve faible (petit n, IC large, source unique) | non_verifiable |
| `REFUTE` | Explicitement montre faux | a_corriger |

### Etape 3 : Copies de sauvegarde

Copier dans `archives/YYYY-MM-DD_reboot/` :

- `cp cahier_de_labo.md archives/.../cahier_de_labo_legacy.md`
- `cp CLAUDE.md archives/.../CLAUDE_legacy.md`
- `cp article/claim_check.md archives/.../claim_check_legacy.md` (si existe)
- `cp article/main.tex archives/.../main_tex_legacy.tex` (si existe)

### Etape 4 : Nettoyage du knowledge et des memoires

Les connaissances issues du projet doivent etre retirees des bases
partagees pour eviter qu'elles n'influencent d'autres travaux tant
qu'elles n'ont pas ete re-verifiees. Elles sont archivees et seront
reinserees au fur et a mesure de la reanalyse.

#### 4.1 Knowledge base (tuberculosis.md)

1. Lire `~/.claude/knowledge/tuberculosis.md`.
2. Identifier les entrees specifiques au projet (via l'inventaire de
   l'etape 1.11). **Ne PAS retirer** les entrees generiques MTBC
   (architecture, conventions, pieges communs).
3. Ecrire `archives/YYYY-MM-DD_reboot/knowledge_entries_removed.md` :

   ```markdown
   # Entrees knowledge retirees -- [Projet] -- YYYY-MM-DD

   Les entrees suivantes ont ete retirees de tuberculosis.md
   car elles proviennent du projet reboote. Elles seront reinserees
   si confirmees par la reanalyse (/mtbc-reboot claim N).

   ---

   ### [date] Titre de l'entree 1
   [contenu integral copie depuis tuberculosis.md]

   ### [date] Titre de l'entree 2
   [contenu integral]

   ---
   ```

4. Retirer ces entrees de `~/.claude/knowledge/tuberculosis.md` via Edit.
   Si une section entiere (## titre) se retrouve vide apres le retrait,
   retirer aussi le titre de section.

#### 4.2 Memoires projet

1. Identifier les fichiers `project_*.md` lies a ce projet dans
   `~/.claude/projects/.../memory/` (via l'inventaire de l'etape 1.11).
2. Pour chaque fichier identifie :
   - Copier dans `archives/YYYY-MM-DD_reboot/memory_<nom>.md`.
   - Supprimer le fichier original (`gio trash`).
   - Retirer la ligne correspondante de `MEMORY.md`.
3. **Ne PAS toucher** aux memoires de type `feedback`, `user`, ou
   `reference`, ni aux memoires d'autres projets.

**Precaution** : cette etape est irreversible au niveau de la base de
connaissances. C'est pourquoi l'etape 3 a deja archive les contenus.
En cas de doute sur l'attribution d'une entree, **la garder** plutot
que la retirer — faux negatif preferable a faux positif.

### Etape 5 : Reset du projet (copie selective)

**Conserve en place** (artefacts reutilisables) :
- `data/` — donnees intactes
- `analyses/` — scripts reutilisables (seront audites en Phase 3)
- `resultats/` — outputs conserves pour comparaison avant/apres
- `experiments/` — experiences passees
- `litterature_review/` — capital de connaissance reutilisable
- `bilans/` — historique
- `archives/` — l'archive qu'on vient de creer

**Reinitialise** :

1. **CLAUDE.md** — reecrire avec :
   - Mention du reboot et lien vers `archives/YYYY-MM-DD_reboot/`
   - Titre et lignee du projet (conserves depuis l'ancien CLAUDE.md)
   - Structure de repertoire standard
   - Note : "Projet en cours de reanalyse. Consulter knowledge_legacy.md
     pour l'historique des decouvertes anterieures."

2. **cahier_de_labo.md** — reinitialiser avec en-tete standard
   (format `/cahier-de-labo init`) et entree de migration :

   ```markdown
   ## YYYY-MM-DD HH:MM [reboot -- migration]

   ### Note de migration
   Ce cahier remplace le precedent suite a un reboot du projet.
   L'historique complet est archive dans :
   - `archives/YYYY-MM-DD_reboot/cahier_de_labo_legacy.md`
   - `archives/YYYY-MM-DD_reboot/knowledge_legacy.md`

   ### Etat a la migration
   - Decouvertes archivees : N (VERIFIE: X, A VERIFIER: Y, INCERTAIN: Z, REFUTE: W)
   - Scripts conserves : M (dans analyses/)
   - Article : reinitialise (ancien dans archives/)
   - Reanalyse : a planifier (/mtbc-reboot plan)

   ---
   ```

3. **article/claim_check.md** — vider le contenu (sera reconstruit par
   la reanalyse). Ecrire un placeholder :

   ```markdown
   # Registre de verification des claims

   **Article :** [titre]
   **Note :** Ce registre sera reconstruit par /mtbc-reboot article
   apres la completion de la reanalyse.

   Voir archives/YYYY-MM-DD_reboot/claim_check_legacy.md pour l'ancien registre.
   ```

4. **article/main.tex** — remplacer par le template vierge standard
   (meme template que `init_project.py`). Conserver le titre et le nom
   de lignee du projet dans le \title{} et les \lignee{}.

**Cree** :
- `reboot_state.md` (voir section Machine a etats ci-dessus)

### Sortie

```
=== Reboot : archive complete ===

Projet [nom] archive dans archives/YYYY-MM-DD_reboot/
  knowledge_legacy.md          : N decouvertes, M claims manuscrit
  knowledge_entries_removed.md : K entrees retirees de tuberculosis.md
  memory_*.md                  : J memoires projet archivees
  Scripts conserves            : S (dans analyses/)
  Donnees conservees           : data/, resultats/
  Litterature                  : conservee (litterature_review/)

Knowledge nettoye :
  tuberculosis.md   : K entrees retirees (archivees, reinserees si confirmees)
  MEMORY.md         : J memoires projet retirees

Projet reinitialise :
  CLAUDE.md          : mis a jour (mention reboot)
  cahier_de_labo.md  : reinitialise avec entree de migration
  article/main.tex   : template vierge (ancien dans archives/)
  claim_check.md     : placeholder (sera reconstruit)

Prochaine etape : /mtbc-reboot survey
```

---

## Phase 2 -- SURVEY (`/mtbc-reboot survey`)

**Gate** : `phase: ARCHIVE_COMPLETE` dans reboot_state.md.

L'objectif est de collecter les connaissances pertinentes des projets
MTBC voisins pour enrichir la reanalyse du projet courant.

### Etape 1 : Identification des projets voisins

1. `ls /home/christophe/docs/codes/mtbc/` — lister les repertoires.
2. Exclure : le projet courant, `bdd/`, `global_supplementary/`,
   `investigate_phylo/`, `init_project.py`, `__pycache__/`.
3. Pour chaque repertoire restant :
   - `Read CLAUDE.md` limit 50 → titre, lignee, statut.
   - Classifier la relation avec le projet courant :
     - **Meme clade** : meme lignee principale (L4.* vs L4.*)
     - **Soeur** : lignee soeur dans la phylogenie (L4 vs L3, Bovis vs Caprae)
     - **Outgroup** : lignee utilisee comme outgroup (Canettii, H37Rv)
     - **Methodologique** : partage de methode, pas de lignee (methodology, data-quality)
     - **Non pertinent** : pas de lien evident

### Etape 2 : Lecture approfondie des voisins pertinents

Pour chaque projet classe "meme clade", "soeur", ou "methodologique" :

1. Lire `cahier_de_labo.md` (limit 200 lignes) pour les decouvertes recentes.
2. Si `article/claim_check.md` existe : scanner les claims confirme pertinents.
3. Si `litterature_review/` existe : scanner les sujets couverts.
4. Si `bilans/` existe : lire le bilan le plus recent.

Pour les outgroups : noter leur existence et leur taille (nb souches) sans
lecture approfondie.

### Etape 3 : Knowledge base transversale

Lire `~/.claude/knowledge/tuberculosis.md` et extraire les sections
pertinentes pour le projet courant (lignee, methodes, pieges connus).

### Etape 4 : Production de cross_project_knowledge.md

Ecrire `archives/YYYY-MM-DD_reboot/cross_project_knowledge.md` :

```markdown
# Cross-Project Knowledge -- [Projet] -- YYYY-MM-DD

**Genere par** : /mtbc-reboot survey
**Projets scannes** : N (pertinents : M)

## Projets voisins pertinents

### [Projet X] -- [Titre]
- **Lignee** : [...]
- **Relation** : [meme clade / soeur / outgroup / methodologique]
- **Decouvertes transferables** :
  - [decouverte qui s'applique au projet courant]
- **Donnees partageables** :
  - [donnees qui pourraient etre reutilisees]
- **Methodes reutilisables** :
  - [scripts ou approches a reprendre]
- **Contradictions potentielles** :
  - [si une decouverte du voisin contredit le legacy du projet courant]

[repeter pour chaque voisin pertinent]

## Convergences identifiees

[Themes transversaux, mutations partagees, patterns methodologiques
 qui emergent de la lecture croisee des projets]

## Connaissances de la base tuberculosis.md

[Extraits cibles de la knowledge base pertinents pour ce projet :
 pieges connus, biais documentes, conventions de lignees]
```

### Sortie et update

Update reboot_state.md : `phase: SURVEY_COMPLETE`.
Entree cahier_de_labo.md documentant le survey.

```
=== Reboot : survey complete ===

Projets scannes : N (pertinents : M)
  [liste des voisins pertinents avec relation]

Convergences identifiees : K
Contradictions potentielles : J

cross_project_knowledge.md ecrit dans archives/

Prochaine etape : /mtbc-reboot plan
```

---

## Phase 3 -- REANALYSE

### Setup (`/mtbc-reboot plan`)

**Gate** : `phase: SURVEY_COMPLETE` dans reboot_state.md.

1. Lire `archives/.../knowledge_legacy.md` et `cross_project_knowledge.md`.
2. Fusionner toutes les sources de claims :
   - Decouvertes du cahier (table "Decouvertes")
   - Claims du manuscrit (table "Claims du manuscrit")
   - Convergences inter-projets qui meritent verification
3. Pour chaque claim :
   - Assigner une **priorite P1-P4** (taxonomie de `/claim-check`,
     voir `bio/skills/claim-check/references/CLAIM_TAXONOMY.md`).
   - Assigner une **strategie de verification** (table de `/claim-check`
     Phase 3 : bioinfo→TBannotator, epidemio→WHO, gene→NCBI, etc.).
   - **Identifier le script source** : quel script dans analyses/ a produit
     ce resultat ? Si aucun : noter "pas de script".
   - **Evaluer la disponibilite de nouvelles donnees** : le nombre de souches
     dans bdd/actuelle/ a-t-il augmente depuis la derniere analyse ?
     TBannotator v3.6 offre-t-il des donnees supplementaires ?
4. Ordonner : P1 d'abord, P4 en dernier. Au sein d'un meme niveau, les
   claims REFUTE ou INCERTAIN du legacy passent avant les VERIFIE (ils
   sont plus susceptibles de changer de statut).

5. Ecrire `reanalysis_registry.md` a la racine du projet :

```markdown
# Registre de reanalyse -- [Projet] -- YYYY-MM-DD

**Genere par** : /mtbc-reboot plan
**Legacy** : archives/YYYY-MM-DD_reboot/knowledge_legacy.md
**Claims totaux** : N
**Reverifies** : 0/N
**Article** : BLOQUE

## Claims

| # | Legacy | P | Enonce | Script | Strategie | Statut | Verifie le | Revue code | Preuve | Notes |
|---|--------|---|--------|--------|-----------|--------|------------|------------|--------|-------|
| 1 | VERIFIE | P1 | "La lignee X est soeur de Y" | phase3_tree.py | RAxML + TBannotator | EN ATTENTE | -- | EN ATTENTE | -- | -- |
| 2 | INCERTAIN | P1 | "tMRCA = 350 CE" | phase5_clock.py | root-to-tip, IC | EN ATTENTE | -- | EN ATTENTE | -- | -- |
| 3 | REFUTE | P2 | "marqueur Z est exclusif" | phase2_markers.py | TBannotator query | EN ATTENTE | -- | EN ATTENTE | -- | Legacy REFUTE, a re-verifier |
```

**Colonnes** :
- **Legacy** : tag de confiance dans knowledge_legacy.md
- **P** : priorite P1-P4
- **Script** : script source dans analyses/ (ou "aucun")
- **Strategie** : methode de re-verification
- **Statut** : EN ATTENTE → confirme / a_corriger / partiellement_confirme / non_verifiable
- **Revue code** : N/A / EN ATTENTE / SOLIDE / FRAGILE / REECRIT
- **Preuve** : resume de la preuve obtenue

6. Afficher le plan :

```
Plan de reanalyse : N claims

#1 [P1] [VERIFIE] "La lignee X est soeur de Y"
   → Script : phase3_tree.py
   → Strategie : relire arbre RAxML, re-verifier support bootstrap
   → Nouvelles donnees : +12 souches depuis derniere analyse

#2 [P1] [INCERTAIN] "tMRCA = 350 CE"
   → Script : phase5_clock.py
   → Strategie : recalcul root-to-tip, intervalle confiance
   → Nouvelles donnees : meme dataset

...

Total : N claims (P1: X, P2: Y, P3: Z, P4: W)
Scripts a auditer : M
```

7. Update reboot_state.md : `phase: REANALYSIS_IN_PROGRESS`, `claims_total: N`.

---

### Execution par claim (`/mtbc-reboot claim N`)

**Gate** : `phase: REANALYSIS_IN_PROGRESS` dans reboot_state.md.

Pour le claim #N :

#### 1. Revue du script source (si applicable)

Si un script est associe au claim :

1. `Read` le script integralement.
2. **Evaluer la solidite** :
   - **Statistique** : les tests sont-ils appropries ? Taille d'effet ?
     Intervalles de confiance ? Corrections pour tests multiples ?
   - **Edge cases** : gestion des souches manquantes, donnees partielles,
     valeurs nulles ? Que se passe-t-il si une souche n'a pas de SPDI ?
   - **Biais de reference H37Rv** : le script traite-t-il H37Rv comme une
     souche "normale" ? (piege recurrent documente dans knowledge base —
     H37Rv est L4.9, utiliser comme reference cree un biais pour L4.9)
   - **Reproductibilite** : chemins en dur ? Dependances non-standard ?
     Seeds aleatoires fixees ?
   - **Qualite du code** : lisibilite, documentation, noms de variables.
3. **Verdict Revue code** :
   - `SOLIDE` — code revu, methodologie correcte, pas de red flag.
   - `FRAGILE` — problemes identifies. Detailler dans Notes :
     - Quel probleme ?
     - Quel impact sur le resultat ?
     - Correction suggeree ?
   - `REECRIT` — si l'utilisateur a accepte la reecriture et qu'elle a ete
     faite. **Le skill NE reecrit PAS automatiquement** : il signale et
     suggere, l'utilisateur decide.

#### 2. Re-verification du claim

1. **Executer la strategie** definie dans le plan de reanalyse :
   - Meme logique que `/claim-check` Phase 4 (requetes TBannotator,
     WebSearch, recalcul, consultation sources primaires).
   - **Si nouvelles donnees disponibles** : re-executer avec le dataset
     actuel. Comparer l'ancien resultat vs le nouveau.
   - **Si le script est FRAGILE** : re-executer apres correction, ou
     utiliser une methode alternative pour verification croisee.

2. **Memoriser les references** :
   - Toute source utilisee pour la verification est ajoutee dans
     `litterature_review/references.bib` avec `keywords = {reboot}`.
   - Meme convention que `/claim-check` : entree BibTeX complete avec
     `annote = {Utilise pour reanalyse claim #N: "enonce"}`.

#### 3. Verdict

1. **Statut reanalyse** : confirme / a_corriger / partiellement_confirme /
   non_verifiable.

2. **Detection de changement** :
   - Si le statut reanalyse differe du tag legacy → flag "decouverte de
     reboot" et ecrire une entree cahier detaillee.
   - Exemples : VERIFIE → a_corriger (resultat ne tient plus avec nouvelles
     donnees), INCERTAIN → confirme (preuve renforcee), REFUTE → confirme
     (la refutation etait erronee).

3. **Priorite P1 non confirme** :
   - Si un claim P1 est a_corriger : notifier l'utilisateur immediatement.
   - Ne pas poursuivre les claims suivants avant que l'utilisateur
     ait pris connaissance de la notification.

4. **Mise a jour du registre** :
   - Mettre a jour la ligne du claim dans `reanalysis_registry.md`.
   - Mettre a jour les compteurs en en-tete (Reverifies : X/N).
   - Mettre a jour `reboot_state.md` : `claims_reverified: X`.

5. **Reinsertion knowledge** (si claim confirme) :
   - Verifier dans `archives/.../knowledge_entries_removed.md` si une
     entree knowledge correspondait a ce claim.
   - Si oui : reinseree dans `~/.claude/knowledge/tuberculosis.md` avec
     la date originale conservee et une note `[re-verifie YYYY-MM-DD]`.
   - Si le resultat a change (ex: chiffre mis a jour) : reinseree avec
     le contenu corrige, pas l'ancien.
   - Si le claim est a_corriger : l'entree knowledge n'est PAS reinseree.
     Ajouter a la place une note dans tuberculosis.md sous la section
     concernee : `**[YYYY-MM-DD] Corrige** : [description de la correction]`.

6. **Entree cahier** :
   - Pour chaque verification non triviale, ecrire une entree dans
     `cahier_de_labo.md` documentant :
     - Le claim re-examine
     - La methode de verification
     - Le resultat et la comparaison avec le legacy
     - Le verdict de la revue de code (si applicable)
     - La reinsertion knowledge (si applicable)

#### 4. Progression

```
Reanalyse : 7/28 claims
  P1 : 3/4 (2 confirmes, 1 infirme!)
  P2 : 4/8 (3 confirmes, 1 partiellement confirme)
  P3 : 0/12
  P4 : 0/4
  Revue code : 5 SOLIDE, 2 FRAGILE, 0 REECRIT
  Article : BLOQUE (21 claims restants)

Prochaine action suggeree : /mtbc-reboot claim 8
```

Si TOUS les claims sont re-verifies : update `phase: REANALYSIS_COMPLETE`.

---

## Phase 4 -- ARTICLE (`/mtbc-reboot article`)

**Gate** : TOUS les claims dans `reanalysis_registry.md` ont un statut
different de `EN ATTENTE`. Si la gate echoue :

```
Article BLOQUE : X claims en attente de reanalyse.
Utiliser /mtbc-reboot claim N pour les claims restants :
  #8  [P2] "..."
  #12 [P3] "..."
  ...
```

Si la gate passe :

### Etape 1 : Synthese de reanalyse

Ecrire `reanalysis_synthesis.md` a la racine du projet :

```markdown
# Synthese de reanalyse -- [Projet] -- YYYY-MM-DD

**Claims totaux** : N
**Confirmes** : X | **Infirmes** : Y | **Partiels** : Z | **Non verifiables** : W

## Changements de statut

| # | Enonce | Legacy | Reanalyse | Impact | Action |
|---|--------|--------|-----------|--------|--------|
| 5 | "Marqueur Z exclusif" | A VERIFIER | a_corriger | P2 | Retirer du manuscrit |
| 8 | "N = 25 souches" | A VERIFIER | confirme (N=26) | P3 | Corriger le chiffre |

## Claims supprimes
[Claims du legacy qui ne tiennent plus et ne doivent pas apparaitre
 dans le nouveau manuscrit, avec la raison de leur suppression]

## Claims consolides
[Claims qui sont maintenant plus fortement soutenus qu'avant le reboot]

## Nouveaux claims
[Claims decouverts pendant la reanalyse qui n'etaient pas dans le legacy]

## Bilan revue de code
- **Scripts SOLIDE** : [liste]
- **Scripts FRAGILE** : [liste avec problemes identifies]
- **Scripts REECRIT** : [liste avec ameliorations apportees]
```

### Etape 2 : Reconstruction du claim_check.md

Reconstruire `article/claim_check.md` a partir du registre de reanalyse
(meme format que celui maintenu par `/claim-check`, colonnes P/Section/
Claim/Statut/Date/Source/Ref/Notes).

### Etape 3 : Deblocage

Update reboot_state.md : `phase: ARTICLE_UNBLOCKED`, `article_blocked: false`.

### Sortie

```
=== Reboot : article debloque ===

Reanalyse terminee : N claims
  confirme : X | a_corriger : Y | partiellement_confirme : Z | non_verifiable : W
  Changements de statut : K

Fichiers produits :
  reanalysis_synthesis.md — synthese complete
  article/claim_check.md — reconstruit depuis la reanalyse

L'article peut maintenant etre redige en s'appuyant sur :
  1. reanalysis_synthesis.md (quoi ecrire et quoi ne pas ecrire)
  2. archives/.../knowledge_legacy.md (historique)
  3. archives/.../cross_project_knowledge.md (contexte inter-projets)

Prochaines etapes suggerees :
  1. Rediger article/main.tex
  2. /claim-check article/main.tex (verifier le nouveau manuscrit)
  3. /manuscript-review (revue structuree)
```

---

## Sous-commande STATUS (`/mtbc-reboot status`)

**Pas de gate** — accessible a tout moment.

Lire `reboot_state.md` et `reanalysis_registry.md` (si existe).
Afficher :

```
=== Reboot status : [Projet] ===
Phase          : [ARCHIVE_COMPLETE / SURVEY_COMPLETE / REANALYSIS_IN_PROGRESS / ...]
Archive        : archives/YYYY-MM-DD_reboot/ (knowledge_legacy.md: N claims)
Survey         : [COMPLETE (M projets scannes) / A FAIRE]
Reanalyse      : X/N claims (P1: a/b, P2: c/d, P3: e/f, P4: g/h)
  confirme     : X
  a_corriger   : Y
  PARTIEL      : Z
  NON VERIF.   : W
  EN ATTENTE   : V
  Revue code   : A SOLIDE, B FRAGILE, C REECRIT, D EN ATTENTE
Article        : [BLOQUE (V claims restants) / DEBLOQUE]

Prochaine action : /mtbc-reboot [sous-commande suggeree]
```

---

## Consignes generales

### Ce que le skill DOIT faire
- Lire TOUT avant d'archiver — ne rien laisser de cote
- Etre exhaustif dans l'extraction des claims et decouvertes
- Porter un regard critique severe sur le code source des scripts
- Utiliser les outils reels pour chaque re-verification (TBannotator,
  WebSearch, recalcul — jamais se fier a la memoire)
- Documenter chaque verification dans le cahier
- Notifier en priorite les claims P1 non confirmes
- Preserver les artefacts (data, scripts, resultats) pour reutilisation
- Maintenir les registres a jour et coherents
- **Nettoyer le knowledge** : retirer de tuberculosis.md les entrees
  specifiques au projet reboote (archivees dans knowledge_entries_removed.md)
- **Reinseree les connaissances confirmees** : quand un claim est confirme,
  reinseree l'entree knowledge correspondante (si elle avait ete retiree)
- **Nettoyer les memoires projet** : archiver et retirer les fichiers
  project_*.md lies au projet dans la memoire Claude

### Ce que le skill NE DOIT PAS faire
- Modifier ou supprimer les fichiers dans archives/ (read-only)
- Reecrire des scripts sans accord explicite de l'utilisateur
- Debloquer l'article si des claims sont encore EN ATTENTE
- Se fier a un ancien resultat sans le re-verifier
- Prendre un claim VERIFIE du legacy comme definitivement vrai
  (meme les VERIFIE sont re-analyses)
- Utiliser `rm` pour quoi que ce soit (toujours `gio trash` ou copie)
- Modifier les entrees passees du cahier
- **Retirer des entrees knowledge generiques** : les entrees sur
  l'architecture TBannotator, les conventions de lignees, les pieges
  communs, les seuils epidemiologiques etc. ne sont PAS specifiques a
  un projet et doivent rester intactes
- **Retirer des memoires d'autres projets** : seules les memoires
  project_*.md du projet reboote sont concernees (pas feedback, user,
  reference, ni les project_*.md d'autres lignees)

### Integration avec l'ecosysteme

- **`/claim-check`** : le registre de reanalyse est compatible avec
  le format claim_check.md. Apres le reboot, `/claim-check` peut prendre
  le relais pour le suivi courant du manuscrit.
- **`/cahier-de-labo`** : le cahier est reinitialise par le reboot et
  enrichi a chaque sous-commande. Le hook Stop continue de fonctionner.
- **`/mtbc-bilan`** : apres un reboot, un bilan peut etre fait sur le
  projet reinitialise pour evaluer l'avancement de la reanalyse.
- **`/lit-review`** : la litterature_review/ est conservee et peut etre
  approfondie pendant la reanalyse.
- **`/mtbc-deepen`** : une fois le reboot termine, mtbc-deepen peut
  proposer de nouvelles pistes sur les bases solides du reboot.

---

## Epilogue

A la fin de chaque sous-commande, produire systematiquement :

1. **Resume de ce qui a ete fait** (3-5 lignes).
2. **Etat mis a jour** des fichiers produits/modifies.
3. **Prochaine etape suggeree** avec la sous-commande exacte a lancer.

Si tous les claims sont re-verifies et l'article debloque, le dire :

```
=== Reboot termine ===

Le projet [nom] a ete reboote avec succes.
  N claims re-verifies : X confirmes, Y infirmes, Z partiels
  K scripts audites : A solides, B fragiles, C reecrits
  Article debloque : pret pour redaction

Le fichier reboot_state.md peut etre archive (gio trash) une fois
le nouveau manuscrit en cours.
```
