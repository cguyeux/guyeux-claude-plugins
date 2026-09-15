---
name: supp-check
description: >-
  Verification d'alignement entre un manuscrit principal et ses supplementary
  materials. Pour chaque table/figure/fichier : reconstruit sa genese via le
  cahier_de_labo.md, detecte les divergences avec le main.tex. Le cahier fait
  autorite : si un supplementary est obsolete, propose de le retravailler, de
  reecrire le main, ou d'arbitrer par une experience. Use when: soumission,
  resoumission, ou apres modification de la BDD ou des scripts.
argument-hint: "<main.tex> [--force] [--stale-days 90] [--fix]"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# /supp-check -- Alignement main.tex x supplementary materials

Le supplementary material est souvent l'enfant pauvre : on le genere
une fois, puis on raffine les analyses du main.tex sans revenir dessus.
Consequence : souche ecartee dans le main mais toujours dans Table S1,
nouveau BioProject ajoute apres le gel du supp, bug corrige qui change
les SPDI dans le main mais pas dans Table S3, nouvelle version
TBannotator qui reclasse des souches... Ce skill detecte et resout
ces desalignements.

**Principe cardinal** : **les dernieres entrees du cahier de labo font
autorite**. Le main et le supplementary sont des projections figees a
des instants passes ; le cahier capture la verite en mouvement. Quand
une divergence existe entre main, supp et cahier, c'est le cahier le
plus recent qui tranche.

---

## Quand lancer ce skill

- Preparation d'une **soumission** ou d'une **resoumission**.
- Apres toute **modification de la BDD** ou des **scripts d'analyse**.
- Apres **correction d'un bug influencant les chiffres**.
- Apres **mise a jour d'une methode ou d'un outil** (nouvelle version
  TBannotator, nouveau modele phylogenetique...).
- **Avant envoi de revisions a un reviewer.**

---

## Prealable -- Consultation memoire projet

**Avant toute action** :

1. Lire `CLAUDE.md` local (conventions, format du supplementary).
2. Lire `cahier_de_labo.md` **integralement** (ou `JOURNAL.md` en
   fallback). Ce skill depend fondamentalement du cahier -- refuser
   de s'executer si aucun n'existe, en proposant `/cahier-de-labo init`.
3. Charger `supp_check.md` existant dans le repertoire de l'article
   s'il est present (registre persistant).
4. Charger `claim_check.md` et `fig_check.md` s'ils existent : leurs
   constats peuvent recouper ceux de ce skill (ex : un claim P1 infirme
   sur une souche est probablement lie a un desalignement de Table S1).

Afficher un etat initial :

```
Etat projet : [titre article]
Cahier      : [N entrees, derniere YYYY-MM-DD]
Supp registre : [M items, K divergents ou "jamais execute"]
Derniere verification : [date ou "jamais"]
```

---

## Declenchement

```
/supp-check path/to/main.tex
/supp-check path/to/main.tex --force
/supp-check path/to/main.tex --stale-days 180
/supp-check path/to/main.tex --fix
```

- Sans argument : chercher `main.tex` dans le repertoire courant
- `--force` : re-verifier tous les supplementary, meme ceux valides
  recemment
- `--stale-days N` (defaut 90) : re-verifier ceux valides il y a plus
  de N jours
- `--fix` : appliquer automatiquement les corrections deterministes
  quand un script source regenerable est detecte. Sans cette option,
  le skill se contente de proposer les corrections.

---

## Phase 0 -- Chargement du registre

1. Localiser le `.tex` principal.
2. Resoudre les `\input{}` et `\include{}`.
3. Chercher `supp_check.md` dans le meme repertoire que le `.tex`.
4. Si present : parser le tableau (un item par ligne : identifiant,
   fichier, fingerprint, statut, date).
5. Chercher `claim_check.md` et `fig_check.md` pour correlation.

---

## Phase 1 -- Inventaire des supplementary materials

Les supplementary prennent plusieurs formes. Tout identifier.

### 1a. Supp declares dans le main.tex

- `Grep -n '\\label{tab:S[0-9]\|\\label{fig:S[0-9]\|Table S[0-9]\|Figure S[0-9]\|Supplementary Table\|Supplementary Figure\|Supplementary File\|Supplementary Data' main.tex`
- Collecter : identifiant (S1, S2...), caption associee dans le main,
  section qui le reference.
- Un supplementary peut etre mentionne sans avoir son propre `\label`
  (ex : "see Table S3"). Grep toutes les occurrences `S\d+` dans le
  texte pour trouver les references orphelines.

### 1b. Supp presents sur le disque

- `ls article/supplementary/`, `article/supplementary_materials/`,
  `article/supp/`, `article/sm/` -- essayer les conventions courantes.
- `Glob article/**/*.{csv,tsv,xlsx,xls,pdf,md,tex,fasta,nwk,txt,json}`
  filtre par repertoire supplementary.
- Identifier tout fichier dont le nom contient `supp`, `S1`, `S2`,
  `SI_`, `Table_S`, `Figure_S`, `File_S`, `Data_S`.

### 1c. Supp embarques dans le main

- `Grep '\\begin{table\|\\begin{figure}' main.tex` : certaines tables
  supplementary sont en fait dans le main (environnement `table*` avec
  caption "Supplementary Table").
- Noter leur emplacement et leur contenu.

### 1d. Reconciliation

- Croiser les trois listes : chaque supp declare dans main.tex doit
  avoir un fichier correspondant sur disque, et inversement.
- **Orphelins fichiers** : fichier supp present sur disque mais non
  reference dans le main → potentiellement obsolete ou oublie.
- **Orphelins references** : supp mentionne dans le main mais fichier
  absent → bloquant.
- **Doublons** : plusieurs fichiers nommes differemment mais destines
  au meme item (ex : `Table_S2_STRING_enrichment.csv` et
  `supplementary_table_S2.csv`) → signaler lequel est canonique.

---

## Phase 2 -- Comprehension de chaque supplementary

Pour chaque supplementary identifie, **comprendre son role**. Ne pas
juste mesurer sa taille : comprendre **ce qu'il represente
scientifiquement**.

### 2a. Lecture du contenu

- **CSV/TSV** : `Read` pour obtenir les headers et les premieres lignes
  (limit ~50 suffit pour le header + echantillon). `wc -l` pour le
  nombre total de lignes. Si besoin de l'integralite, lire par chunks.
- **XLSX** : si disponible, utiliser le skill `xlsx` pour extraire les
  feuilles, headers, row counts. Sinon, demander a l'utilisateur de
  convertir en CSV.
- **PDF** (figure supp ou document) : `Read` (support multimodal). Pour
  un document multi-pages, lire les premieres pages pour l'en-tete.
- **MD / TXT** : `Read` integralement.
- **FASTA / NWK** : compter sequences / feuilles via `Grep -c`.
- **JSON** : lire la structure, extraire les cles principales.

### 2b. Lecture de la caption associee

- Dans le main.tex, extraire la phrase complete de caption
  (`\caption{...}` ou sentence that references "Supplementary Table
  S1:").
- Cette caption est la **promesse contractuelle** du supplementary :
  elle decrit ce que le fichier est cense contenir.

### 2c. Extraction des metriques-cles

Pour chaque supp, extraire un **fingerprint structurel** qui servira
a detecter les desalignements :

| Type de supp | Metriques a extraire |
|--------------|----------------------|
| Table metadonnees souches | nombre de lignes (souches), liste des IDs SRA/ERR/SRR, pays distincts, BioProjects distincts, dates |
| Table variants/SPDI | nombre de lignes (variants), nombre de souches colonnes, gene names distincts |
| Table resistance | nombre de souches, nombre de drogues, prevalence globale |
| Table phylogenie | nombre de clades, nombre de branches, modele, bootstrap moyen |
| Table enrichissement | outil utilise (STRING, GO, KEGG), seuil p-value, categories retenues |
| Figure supp | meme criteres que `/fig-check` (caption, lisibilite) + fingerprint visuel |
| Fichier d'alignement (fasta/txt) | nombre de sequences, longueur, reference |
| Arbre (nwk) | nombre de feuilles, presence d'un outgroup, format de support |
| File S (script/README) | version, dependances citees |

Le fingerprint sert de **signature** pour cette session de verification.

### 2d. Comparaison caption x contenu

Premier check **sans meme regarder le cahier** : la caption correspond-
elle au contenu reel du fichier ?
- Caption dit "68 strains", fichier a 67 lignes → divergence directe.
- Caption dit "19 countries", fichier a 17 pays distincts → divergence.
- Caption dit "columns: ID, Lineage, Country, Year", fichier a des
  colonnes supplementaires ou manquantes → divergence.

Une divergence caption/contenu est une issue **immediate** a
enregistrer, independamment du cahier.

---

## Phase 3 -- Reconstitution de la genese via le cahier

**Pour chaque supplementary**, fouiller le `cahier_de_labo.md` et
reconstruire sa trajectoire.

### 3a. Entree de creation

`Grep` dans le cahier :
- Nom exact du fichier (`Table_S1_strain_metadata.csv`)
- Nom de base sans extension
- Label LaTeX (`tab:S1`, `fig:S2`)
- Mot-cle generique associe (STRING, enrichment, metadata, alignment)

Identifier l'entree datee ou le supp a ete cree pour la premiere fois.
Extraire de cette entree :
- Le **script** qui l'a produit (section "Scripts et outils")
- Les **donnees d'entree** (section "Donnees" : nb souches, BDD, fichiers)
- Les **parametres** (seuils, filtres, version d'outil)
- Le **resultat** attendu

Cet instantane est **l'etat initial** du supp : ce qu'il representait
au moment de sa creation.

### 3b. Entrees ulterieures affectant le supp

C'est la partie **critique**. Trouver **tout** ce qui s'est passe
dans le cahier APRES la creation du supp et qui aurait du le
retoucher :

| Type d'evenement a detecter | Comment le detecter dans le cahier |
|-----------------------------|-------------------------------------|
| **Souche(s) ecartee(s)** | `Grep -i "exclus\|ecart\|retire\|remove\|outlier\|qualite\|quality\|exclus\|bdd\|ignore"` + contexte |
| **Souche(s) ajoutee(s)** | `Grep -i "ajout\|added\|nouvelle souche\|fetch\|recuperat\|missing strain"` |
| **BioProject ajoute** | `Grep -i "bioproject\|PRJ[NE][AB]"` |
| **Bug corrige influencant SPDI/annotations** | `Grep -i "bug\|correction\|corrige\|fix\|mauvais\|erreur"` |
| **Nouvelle version d'outil** | `Grep -i "tbannotator v\|raxml\|snpeff\|version\|upgrade\|mise a jour"` |
| **Changement de reference genomique** | `Grep -i "NC_000962\|reference\|H37Rv"` |
| **Nouveau filtre ou seuil** | `Grep -i "seuil\|filtre\|threshold\|cutoff\|p-value\|bootstrap"` |
| **Reclassement de lignee** | `Grep -i "reclass\|rename\|lineage\|sous-lignee\|malplace"` |
| **Nouvelle analyse dominante** | chaque `^### Objectif` post-creation dont la sortie recoupe le domaine du supp |

Pour chaque evenement detecte :
- Date de l'entree
- Nature du changement
- Impact estime sur le supp : **affecte directement** (chiffres a
  changer), **affecte indirectement** (methode citee obsolete),
  **orthogonal** (sans rapport).

### 3c. Etat de verite le plus recent

Determiner **l'etat actuel** du domaine couvert par le supp :
- Nombre de souches actuel dans `../../bdd/actuelle/<lignee>/` si
  applicable.
- Derniere valeur citee dans le cahier (ex : "L4.9 passe de 819 a 824
  souches" → verite actuelle = 824).
- Dernier script qui a touche au domaine.
- Derniere decision methodologique (ex : "critere L4.9 : <=10 des 57
  marqueurs inverses").

C'est cet etat qui est la **reference** pour l'alignement.

---

## Phase 4 -- Detection des divergences

Pour chaque supplementary, comparer trois sources :

1. **Le supp lui-meme** (contenu reel du fichier)
2. **Le main.tex** (ce qu'il affirme a propos du supp et des chiffres
   lies)
3. **Le cahier** (etat de verite le plus recent)

### Matrice de comparaison

| Cas | supp | main | cahier | Interpretation |
|-----|------|------|--------|----------------|
| A | agree | agree | agree | OK |
| B | agree | agree | diverge | main **et** supp obsoletes, cahier dit la verite → regenerer les deux |
| C | agree | diverge |, | main incoherent avec son propre supp : lequel est la verite ? consulter cahier |
| D | diverge | agree | agree | le supp est obsolete, main deja mis a jour → regenerer le supp |
| E | diverge | diverge | agree | main mis a jour, supp pas a jour → regenerer le supp |
| F |, |, | silence | le cahier n'a rien sur le sujet → ne pas trancher, demander decision manuelle ou experimentation |
| G | diverge-caption |, |, | le fichier supp ne correspond pas a sa propre caption → divergence interne, corriger l'un ou l'autre |

### Chiffres a verifier systematiquement

Extraire du main.tex **toutes** les mentions chiffrees du domaine de
chaque supp, et les comparer au contenu du fichier :

- "`68 genomes`", "`67 after exclusion`", "`19 countries`",
  "`34 BioProjects`" → comparer a Table S1.
- "`501 SPDI markers`", "`39 core-exclusive variants`", "`33 NS / 0 S`"
  → comparer a Table S3.
- "`8 internal clades (A-H)`", "`TMRCA ~1718 CE`" → comparer au supp
  phylogenetique et a la caption de la figure d'arbre.
- "`p = 0.006`", "`p < 0.001`" → verifier que le supp d'enrichissement
  affiche la meme statistique.

**Methode** : `Grep -n -E '[0-9]+[.,]?[0-9]*' main.tex` sur les sections
Results/Methods/Discussion, filtrer les chiffres suspects (nombres
"ronds" style 68, 501, 19, 34), et pour chacun chercher l'entree du
cahier ou la ligne du supp qui devrait porter la meme valeur.

### Severite des divergences

| Severite | Definition |
|----------|------------|
| `OK` | Toutes les metriques s'alignent |
| `MINOR` | Divergence decorative (ordre de colonnes, casse, formatage) |
| `MAJOR` | Divergence de contenu : chiffres differents, IDs differents, categories differentes |
| `CRITICAL` | Divergence qui invalide une conclusion du main (ex : souche ecartee encore presente dans Table S1 et citee dans la discussion) |
| `BLOCKING` | Fichier manquant, caption contredite par contenu, identifiant inexistant |
| `AMBIGUOUS` | Divergence detectee mais le cahier ne permet pas de trancher la verite → requiert decision humaine ou experimentation |

---

## Phase 5 -- Arbitrage et actions proposees

Pour chaque divergence, proposer une action. Quatre familles :

### 5a. Retravail du supplementary

Si le cahier indique clairement que le main est a jour et le supp
obsolete :
- Identifier le script source qui genere ce supp (via Phase 2 et 3a).
- Proposer sa relance avec la BDD/donnees actuelles.
- En mode `--fix` et si le script est deterministe : le relancer via
  `Bash`, verifier la sortie, remplacer le fichier supp. **Jamais
  toucher aux fichiers `.tex` du main** en mode `--fix`.

### 5b. Reecriture du main

Si le cahier et le supp s'accordent mais le main affirme autre chose :
- Identifier les phrases exactes du main a corriger (section, ligne,
  texte actuel, texte propose).
- **Ne pas appliquer automatiquement** meme en mode `--fix` : une
  correction de manuscrit doit passer par l'utilisateur (ou par
  `/manuscript-review`). Juste proposer precisement la modification.

### 5c. Experimentation d'arbitrage

Si main, supp et cahier sont en desaccord **sans que le cahier tranche**,
ou si la source de verite est impossible a determiner sur pieces :
- Proposer une experience concrete (une requete a relancer, un script
  a executer, une validation croisee) dont le resultat trancherait.
- Suggerer explicitement une commande : `/snp-distance`,
  `/lineage-comparison`, une requete TBannotator MCP, un recomptage
  via script dedie.
- Noter qu'apres l'experience, ce skill doit etre relance.

### 5d. Remise en question globale

Si les divergences sont **massives** (>30% des supp en CRITICAL, ou
plusieurs souches du main.tex manquent dans toutes les tables, ou un
changement methodologique majeur dans le cahier n'a touche ni main ni
supp) :
- Lever une **alerte globale** en tete du rapport.
- Proposer de suspendre toute soumission et de refaire le pipeline
  complet.
- Ne pas tenter de corrections ponctuelles dans ce cas -- signaler
  qu'un retraitement en profondeur est necessaire.

---

## Phase 6 -- Rapport et mise a jour du registre

### 6a. Ecrire `supp_check.md`

```markdown
# Registre de verification des supplementary materials

**Article :** [titre extrait du \title{}]
**Derniere verification :** YYYY-MM-DD
**Supplementary totaux :** N (tables : X, figures : Y, files : Z)

## Etat global
- Alignement : [bon / partiel / compromis]
- Divergences critiques : K
- Divergences majeures : M
- Items a regenerer : R
- Experiences d'arbitrage requises : E
- Alerte globale : [oui (details) / non]

## Items

| # | Label | Fichier | Fingerprint | Statut | Verifie le | Divergence principale | Action | Script source |
|---|-------|---------|-------------|--------|------------|-----------------------|--------|---------------|
| 1 | tab:S1 | supplementary/Table_S1_strain_metadata.csv | 68 lignes, 19 pays, 34 BioProjects | CRITICAL | 2026-04-09 | Main cite 67 strains apres exclusion, Table S1 en contient 68 (ERR1465988 non retiree) | Retrait de la ligne ERR1465988, regeneration via analyses/phase2_metadata.py | analyses/phase2_metadata.py |
| 2 | tab:S2 | supplementary/Table_S2_STRING_enrichment.csv | 12 categories | MAJOR | 2026-04-09 | p-values differentes du main (main : 0.006, supp : 0.012, cahier : 0.006 avec nouveau seuil) | Regenerer depuis STRING avec seuil actuel | résultats/scripts/string_enrichment.py |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |

## Alerte globale
[Vide ou detail si une remise en question du tout est proposee]

## Details par item

### Item 1 — tab:S1 (CRITICAL)

**Genese (cahier)** :
- 2026-03-12 : cree par `analyses/phase2_metadata.py` depuis la BDD
  locale (68 souches). Input : `../../bdd/actuelle/L4.15/`.

**Evolution depuis la genese** :
- 2026-03-18 : "ERR1465988 identifiee comme outlier (distance SPDI
  anormale), exclue de l'analyse. Main.tex mis a jour pour indiquer
  '67 genomes after exclusion'."
- 2026-03-25 : "ajout de 3 nouveaux BioProjects (PRJEB12345,
  PRJNA67890, PRJDB1111). Total 34 BioProjects, 19 pays."

**Etat de verite (cahier le plus recent)** :
- 67 souches actives (68 initiales moins ERR1465988)
- 19 pays, 34 BioProjects
- Derniere modification pertinente : 2026-03-25

**Contenu actuel du fichier** :
- 68 lignes (incluant ERR1465988)
- 19 pays, 34 BioProjects

**Main.tex** :
- "We analyzed 67 genomes (68 minus one outlier, ERR1465988) from 19
  countries and 34 BioProjects."

**Divergence** : supp vs (cahier + main). Main et cahier accordent ;
Table S1 est obsolete.

**Action proposee** :
- Relancer `analyses/phase2_metadata.py` pour regenerer le fichier
  avec l'exclusion d'ERR1465988.
- **Ou** en mode `--fix` : lancer automatiquement le script et
  verifier que la nouvelle sortie contient 67 lignes.
- Recompiler le PDF article apres correction.

---
```

### 6b. Afficher le rapport resume a l'ecran

```
━━━━ Rapport supp-check ━━━━

Article : [titre]
Date    : YYYY-MM-DD
Mode    : [normal / force / stale-days=N / fix]

Supplementary inventoriees : N (tables X, figures Y, files Z)
Alerte globale : [oui/non]

Statut
  OK        : A
  MINOR     : B
  MAJOR     : C
  CRITICAL  : D  ⚠
  BLOCKING  : E  ⛔
  AMBIGUOUS : F  ❓

Divergences les plus urgentes
  1. Table S1 (CRITICAL) — ERR1465988 toujours presente, doit etre retiree
  2. Table S3 (CRITICAL) — 500 markers vs 501 dans main (regeneration requise)
  3. Figure S2 (MAJOR) — arbre sans mise a jour des 5 souches L4.9.1 ajoutees

Actions d'arbitrage requises (cahier silencieux)
  • Table S4 : p-value de STRING mais pas de decision sur le seuil dans le
    cahier → decision humaine necessaire

Actions proposees en mode --fix (si applique)
  • Relancer analyses/phase2_metadata.py
  • Relancer résultats/scripts/string_enrichment.py
```

---

## Phase 7 -- Corrections (suggestion ou application)

### Sans `--fix`

- Pour chaque divergence, donner un plan d'action precis : quel
  script relancer avec quels arguments, quelle ligne du main a
  retoucher, quelle experience lancer.
- **Ne modifier aucun fichier.**

### Avec `--fix`

Regles strictes :

1. **Ne jamais modifier `main.tex`** meme en `--fix`. Les corrections
   textuelles du manuscrit restent sous controle humain.
2. **Ne jamais ecraser un fichier supplementary sans backup** : avant
   regeneration, copier l'ancien en `<nom>.pre_fix_YYYY-MM-DD.<ext>`.
3. Regenerer uniquement les supp pour lesquels :
   - un script source a ete identifie avec certitude (Phase 2/3a),
   - ce script est deterministe (lecture de donnees + sortie fichier,
     pas d'input utilisateur),
   - la divergence est classee MAJOR ou CRITICAL (pas MINOR, pas
     AMBIGUOUS, pas BLOCKING).
4. Apres regeneration, re-executer les Phases 2 et 4 sur ce supp pour
   verifier que la divergence est resolue. Si elle persiste : laisser
   en MAJOR/CRITICAL et signaler que la regeneration n'a pas suffi
   (script obsolete, input manquant, bug de genese).
5. Pour toute divergence classee AMBIGUOUS, BLOCKING, ou issue de la
   Phase 5d (remise en question globale) : **ne rien toucher**.
6. Apres toute serie de regenerations, signaler qu'un
   `make -C article/` est necessaire pour regenerer le PDF final,
   suivi d'un `/claim-check --force` et d'un `/fig-check --force`
   pour la boucle de qualite complete.

---

## Consignes generales

### Ce que le skill DOIT faire

- Traiter TOUS les supplementary, y compris ceux oublies par le main
- Lire CHAQUE fichier supplementary reellement (pas juste `ls`)
- Parcourir INTEGRALEMENT le cahier pour chaque item
- Traiter les dernieres entrees du cahier comme verite de reference
- Extraire les chiffres du main.tex et les comparer aux fichiers supp
- Distinguer les divergences tranchables des divergences ambigues
- Proposer pour chaque divergence une action concrete et testable
- Detecter les doublons (deux fichiers pour le meme Table S2)
- Detecter les orphelins (fichier sans ref dans main, ou ref sans
  fichier)
- En mode `--fix`, limiter strictement l'action aux scripts sources
  et laisser le main intact

### Ce que le skill NE DOIT PAS faire

- Se fier a un fichier README ou a un CLAUDE.md comme verite si le
  cahier dit autre chose de plus recent
- Trancher une divergence ambigue en inventant une valeur
- Modifier le main.tex en `--fix`
- Ecraser un supplementary sans backup
- Ignorer les supp supplementaires ou les File S (README,
  alignements, scripts)
- Proposer une correction pour un supp BLOCKING sans avoir compris
  la cause
- Passer une divergence sous silence parce qu'elle semble mineure :
  meme un MINOR merite d'etre trace dans le registre

### Integration avec l'ecosysteme

- **Complementaire a `/claim-check`** : les claims textuels et les supp
  sont deux facettes de la meme verite. Un claim P1 infirme est
  souvent correle a un supp CRITICAL.
- **Complementaire a `/fig-check`** : les figures supplementary sont
  dans les deux scopes ; `/supp-check` gere leur alignement avec les
  tables et le cahier, `/fig-check` leur qualite visuelle.
- **Declenche `/claim-check --force` et `/fig-check --force`** apres
  toute correction en mode `--fix`, pour boucler la verification.
- **Depend de `/cahier-de-labo`** : sans cahier a jour, ce skill
  perd sa source de verite. Refuser de s'executer ou degrader
  gracieusement.

---

## Epilogue -- Resume et suggestion de suite

### Resume de session

Afficher en 5-8 lignes :
- Nombre de supplementary inventories
- Statut global : aligne / partiel / compromis
- Top 3 divergences par severite
- Actions appliquees en mode `--fix` (scripts relances, fichiers
  regeneres, backups crees)
- Fichiers produits : `supp_check.md`, eventuelles regenerations

### Suggestion de prochaine etape

Scenario "alignement OK" :

```
━━━━ Etat du supplementary ━━━━

Tous les supplementary materials sont alignes avec le main et le
cahier (N items, 0 divergence critique) :
  ✅ Inventaire complet (pas d'orphelin, pas de doublon)
  ✅ Captions coherentes avec les fichiers
  ✅ Chiffres alignes entre main, supp et cahier
  ✅ Pas d'evenement cahier non reporte

Aucune action requise sur les supplementary.
```

Scenario "divergences detectees" :

```
━━━━ Prochaine etape suggeree ━━━━

N divergences detectees (K critiques). Je recommande :

  1. /supp-check --fix           ← appliquer les regenerations
     deterministes (scripts sources identifies : X)
  2. Corrections manuelles du main.tex pour les items suivants :
     • ligne 142 de main.tex : "68 genomes" → "67 genomes"
     • ligne 267 : "500 markers" → "501 markers"
  3. make -C article/            ← recompiler le PDF
  4. /claim-check --force        ← re-verifier les claims
     textuels apres correction
  5. /fig-check --force          ← re-verifier les figures

(Si l'item X reste en AMBIGUOUS, lancer d'abord l'experience
d'arbitrage : [commande suggeree])
```

Scenario "alerte globale" :

```
━━━━ ⚠ Alerte globale ━━━━

Les divergences detectees suggerent que l'article et les
supplementary sont substantiellement desynchronises de la verite
actuelle du cahier. Avant toute soumission :

  1. Relire attentivement les N dernieres entrees du cahier
  2. Decider si l'article reflete encore les analyses actuelles
  3. Envisager une refonte de la section Results et des tables
     supplementary concernees
  4. Eventuellement, relancer le pipeline complet et comparer

Ne pas appliquer `--fix` tant que cette decision n'est pas prise.
```
