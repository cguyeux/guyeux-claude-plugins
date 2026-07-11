---
name: claim-check
description: >-
  Extraction et verification systematique des affirmations scientifiques
  d'un article. Classe les claims par priorite (structurants -> annexes),
  verifie via bioinfo, BDD, ou litterature. Pour la verification
  litterature TB / MTBC : interroger en priorite tbmonitor (corpus
  pre-indexe de ~190 000 papiers PubMed TB, requetable en SQL
  sub-seconde) avant de tomber sur WebSearch / WebFetch. Maintient un
  registre claim_check.md avec dates de verification. Re-verifie
  uniquement les claims non verifies ou anciens.
argument-hint: "<main.tex> [--force] [--stale-days 90]"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, mcp__tbannotator__tool_query_postgres, mcp__tbannotator__tool_get_schema, mcp__tbmonitor__execute_sql, mcp__tbmonitor__show_schema
---

# /claim-check -- Verification systematique des affirmations scientifiques

Extrait toutes les affirmations factuelles verifiables d'un article scientifique,
les classe par importance, et verifie chacune via les outils disponibles
(bioinfo, bases de donnees, litterature). Maintient un registre persistant
`claim_check.md` dans le repertoire du projet. **Toute reference utilisee
pour verifier un claim est systematiquement ajoutee dans
`litterature_review/references.bib`** (cree si inexistant).



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
/claim-check path/to/main.tex
/claim-check path/to/main.tex --force
/claim-check path/to/main.tex --stale-days 180
```

- Sans argument : chercher `main.tex` dans le repertoire courant
- `--force` : re-verifier TOUS les claims, meme ceux deja verifies
- `--stale-days N` (defaut : 90) : re-verifier les claims verifies il y a plus de N jours

---

## Phase 0 -- Lecture et chargement du registre

1. Localiser le `.tex` principal (argument `$ARGUMENTS` ou `main.tex`)
2. Lire le fichier en entier. Resoudre les `\input{}` et `\include{}`
3. Chercher `claim_check.md` dans le meme repertoire que le `.tex`
4. Si le fichier existe :
   - Le lire et parser le tableau de claims
   - Compter : claims totaux, verifies recemment, perimes, jamais verifies
5. Si le fichier n'existe pas :
   - Noter qu'il sera cree en Phase 5
6. Afficher :

```
Claim-check : [titre de l'article]
Registre    : [chemin claim_check.md ou "a creer"]
Claims existants : X (verifies : Y, perimes : Z, jamais verifies : W)
Mode        : [normal / force / stale-days=N]
```

---

## Phase 1 -- Extraction des claims

Parcourir l'article **section par section** et extraire chaque affirmation
factuelle verifiable.

### Ce qui est un claim

- Tout enonce factuel qui pourrait etre vrai ou faux
- Tout chiffre, pourcentage, statistique
- Toute attribution ("X a montre que...", "selon [ref]...")
- Tout resultat presente comme nouveau ("nous avons trouve que...")
- Toute comparaison ("X est superieur a Y")

### Ce qui n'est PAS un claim

- Les definitions standard du domaine ("TB is caused by M. tuberculosis")
- Les descriptions de methode pure ("We used RAxML v8.2")
- Les opinions explicitement signalees comme telles
- Les formulations hypothetiques ("this could suggest...")

### Pour chaque claim extraire

- **Localisation** : section + numero de ligne approximatif
- **Enonce** : la phrase ou partie de phrase contenant le claim
- **Reference(s)** : \cite{} associe(s), s'il y en a
- **Type** : resultat bioinfo, epidemio, gene/mutation, methodologique,
  litterature, chiffre (voir [references/CLAIM_TAXONOMY.md](references/CLAIM_TAXONOMY.md))

### Deduplication avec le registre existant

- Comparer chaque claim extrait avec ceux deja dans `claim_check.md`
- Un claim est considere comme "le meme" si l'enonce est semantiquement equivalent
  (pas besoin d'etre mot a mot identique)
- Si le claim existe deja ET est verifie recemment ET pas en mode `--force` : passer
- Si le claim existe mais est perime (> stale-days) : marquer pour re-verification
- Si le claim est nouveau : l'ajouter

---

## Phase 1bis -- Audit de coherence numerique interne

**Objectif** : detecter les incoherences entre les chiffres repetes a travers
le manuscrit (et entre la version EN et la version FR si elle existe). Cette
phase ne verifie pas la *justesse* d'un chiffre (c'est le role de la Phase 4)
mais sa *coherence interne* : un meme fait quantitatif doit etre rapporte
avec la meme valeur partout, et les decompositions doivent additionner.

Voir [references/NUMBER_CONSISTENCY.md](references/NUMBER_CONSISTENCY.md) pour
le detail des regex, des classes de chiffres et des recettes d'audit.

### 0. Outil : recroisement mecanique tex <-> donnees sources (OBLIGATOIRE si des chiffres viennent de calculs)

```bash
# Mode DECLARATIF (fiable, a privilegier) : on declare quel chiffre vient de quel chemin
python3 ${CLAUDE_PLUGIN_ROOT}/skills/claim-check/scripts/numeric_crosscheck.py \
    main.tex --data results/*.json --assert-file claims_numeric.json
# -> exit 0 si tout concorde, 1 sinon. Le fichier claims_numeric.json est un ARTEFACT
#    du projet : il se rejoue a chaque modification du manuscrit.

# Mode SCAN (aide a la DECOUVERTE, PAS une alerte) : quels chiffres du .tex ne se
# retrouvent pas tels quels dans les donnees ?
python3 .../numeric_crosscheck.py main.tex --data results/*.json --min 0.01
```

**Pourquoi cet outil.** La relecture ne rattrape PAS un chiffre attribue au mauvais modele :
elle lit une phrase plausible et passe. Le mode d'erreur dangereux n'est pas le chiffre
invente (voyant) mais le chiffre VRAI rapporte sous la MAUVAISE condition. Cas fondateur
(mabossDemo, 2026-07-11) : un manuscrit issu d'un framework multi-variantes donnait « 0,20 »
comme valeur de controle ; le 0,20 existait, mais pour une AUTRE variante (le controle valait
0,341). **Deux reviews humaines successives ne l'avaient pas vu.** Seul le recroisement
mecanique l'a trouve.

**Limite du mode SCAN, a connaitre avant de s'y fier.** Il compare des NOMBRES, pas du SENS :
il rapprochera « 0,15 % » (borne d'une regle de trois) de « 0,163 » (une probabilite de
simulation) parce qu'ils sont numeriquement voisins. Ses sorties PROCHE/ABSENT/MULTIPLE sont
des PISTES a inspecter, jamais des verdicts. **Ne pas le traiter comme une alerte** : un test
qui crie a tort est un test qu'on apprend a ignorer, donc pire qu'absent. Le mode qui FAIT FOI
est le mode declaratif, ou c'est l'agent qui porte l'attribution et le script qui la verifie.

### 1. Extraction de tous les nombres

```bash
rg -n -o "[0-9][0-9~,. \\\\]*[0-9]|[0-9]+" main.tex > /tmp/numbers_en.txt
rg -n -o "[0-9][0-9~,. \\\\]*[0-9]|[0-9]+" main_fr.tex > /tmp/numbers_fr.txt
```

Comptes attendus : ~1000-3000 nombres dans un manuscrit Results+Discussion typique.

### 2. Classes de chiffres a surveiller

| Classe | Exemples | Test de coherence |
|--------|----------|-------------------|
| **Tailles d'echantillon** | n=1556 L6, n=21 L9, n=2 L10 | Identiques en abstract, methods, results, discussion, captions, tableaux |
| **Sous-decompositions** | 936 + 232 + 8 + 16 + 364 = 1556 | La somme doit egaler le total |
| **Dates / TMRCA** | 990 BCE crown, 1498 BCE stem, 508 ans gap | Texte == legendes figures == lignes ref. de tables de sensibilite |
| **Ratios** | N:S = 30/12, dN/dS = 0.89, p = 0.71 | La decomposition (3 HIGH + 28 missense...) doit etre coherente avec le ratio |
| **p-values, q-values** | p=0.045, q=0.146 | Identiques abstract et tableaux |
| **Pourcentages** | 11.6% rejet QC, 95% CI | EN (`11.6`) et FR (`11{,}6`) -- separateur conditionne par langue |
| **Conventions de formatage** | `1\,556` vs `1~556` vs `1556` | Une seule convention par document (sauf tableaux compactes) |
| **Comptes par branche** | 23 stem + 71 L6L9 + 117 L6 + 217 L9 + 431 L10 | Chiffres identiques entre Results, Tableau, Figure, Discussion |
| **Sommes implicites** | 50 L6 + 21 L9 + 2 L10 + 10 CladeA + 10 Animal_1 + 5 L5 + 1 H37Rv = 99 | Doit egaler le total annonce |
| **Partitions / funnels** | 311 = 18 widespread + 67 convergent + 87 near-clonal + 139 Dollo | Categories MECE (mutuellement exclusives + exhaustives) ET somme == total ; ne PAS y additionner un flag orthogonal ni un verdict intermediaire |

### 3. Recettes ripgrep typiques

```bash
# Lister toutes les occurrences d'une valeur cle (avec contexte)
for n in "1\\\\,556" "1~556" "1556" "936" "232" "364"; do
  echo "=== $n ===";
  rg -n -F "$n" main.tex | head -3
done

# Detecter conventions de separateurs heterogenes
rg -c "[0-9]~[0-9]" main.tex                    # ~ insecable
rg -c "[0-9]\\\\,[0-9]" main.tex                 # \, thin space
rg -c "\\b[0-9]{4,}\\b" main.tex                 # nombres sans separateur

# Verifier coherence EN vs FR (si les deux existent)
diff <(rg -o "[0-9]+" main.tex | sort -u) \
     <(rg -o "[0-9]+" main_fr.tex | sort -u) | head -20
```

### 4. Detection des divergences

Pour chaque valeur quantitative recurrente :

1. **Localiser toutes ses occurrences** dans le manuscrit
2. **Verifier que la valeur est strictement identique** (chiffres + unite)
3. **Verifier que la convention de formatage est uniforme** (`\,` vs `~` vs `,`)
4. **Si plusieurs versions linguistiques** : verifier que EN et FR portent
   la meme valeur (avec convention propre a la langue : `0.89` EN / `0{,}89` FR
   pour la virgule decimale)

### 5. Verification des sommes attendues

Pour chaque ensemble de sous-totaux :

```python
# Exemple : sommes des sous-lignages L6
assert 936 + 232 + 8 + 16 + 364 == 1556, "Somme L6 incoherente"
# Sommes signature
assert 3 + 28 + 12 + 6 == 49, "Decomposition signature incoherente"
# Sommes tip-dating
assert 50 + 21 + 2 + 10 + 10 + 5 + 1 == 99, "Sommes tip-dating incoherente"
```

### 5bis. Verification des partitions disjointes (MECE) -- le piege du faux funnel

Une somme fausse n'est pas toujours une typo. Quand un ensemble de comptes est
presente comme une **partition** (un entonnoir/funnel qui decompose un tout), la
cause la plus insidieuse est que les categories **se chevauchent**. Une partition
doit etre **MECE** : mutuellement exclusive ET collectivement exhaustive. Deux
pieges recurrents (documentes sur `gene_decay_census`, funnel 311) qui font qu'une
« partition » ne somme pas au total :

1. **Un flag ORTHOGONAL melange a la partition.** Un attribut transversal (ex.
   `mobile_repeat`, marque par nom/Pfam, recoupe plusieurs categories) n'est PAS
   une part du tout : l'additionner double-compte. Le garder hors de la somme
   (« N/total portent le flag »).
2. **Un verdict GROSSIER intermediaire melange a la determination FINALE.** Un
   classement d'etape (verdict heuristique) et la determination finale (test
   strict) se chevauchent : des items du verdict intermediaire sont promus ou
   recales par le test final. Ne jamais sommer les deux.

Regle : **partitionner sur la determination FINALE seulement.** Verifier
explicitement que (a) chaque item tombe dans exactement une categorie, (b) aucune
categorie n'est un flag transversal, (c) la somme egale le total. Si une « somme »
d'article ne tombe pas juste, tester CETTE hypothese (categories non disjointes)
AVANT de conclure a une typo. Detail et exemple : voir
[references/NUMBER_CONSISTENCY.md](references/NUMBER_CONSISTENCY.md) §2.7.

### 6. Generation des claims de type `internal_consistency`

Chaque incoherence detectee est transformee en un claim de type
`internal_consistency` avec priorite **auto-promue a P1** (un manuscrit qui
se contredit est un blocage critique). Format :

```
Claim #N (P1, internal_consistency)
  Enonce : "n=L10 : 3 occurrences avec n=2 (abstract, dataset, tip-dating, fig:strata, table 1)
            mais 1 occurrence avec n=3 (caveat THD, l.410 EN / l.421 FR)"
  Strategie : verifier la valeur reelle (Phase 4) et harmoniser
  Statut suggere : a_corriger
```

### 7. Affichage du resultat de la phase

```
Audit de coherence numerique :
  Nombres extraits      : 1920 EN / 1920 FR
  Valeurs cles testees  : 47
  Incoherences detectees : 4
    - L10 sample size : n=3 vs n=2 (caveat THD)
    - TMRCA crown : 990 BCE (texte) vs 992 BCE (table ref.)
    - Decomposition signature : 3 HIGH (sec 3.2) vs 2 HIGH (sec 3.5)
    - Conventions separateur : 1\,556 (8) vs 1~556 (5) vs 1556 (3)
  Claims internal_consistency generes : 4 (tous P1)
```

Ces claims rejoignent ensuite le flux normal (Phases 2 a 5).

---

## Phase 2 -- Classification par priorite

Classer chaque claim selon la taxonomie P1-P4
(voir [references/CLAIM_TAXONOMY.md](references/CLAIM_TAXONOMY.md) pour le detail) :

| Priorite | Nom | Critere | Impact si faux |
|----------|-----|---------|----------------|
| **P1** | Structurant | Fonde l'argumentation principale | L'article s'effondre |
| **P2** | Support | Renforce l'argument sans le porter seul | L'article est affaibli |
| **P3** | Contexte | Etat de l'art, introduction, discussion | Genant, ne change pas les resultats |
| **P4** | Annexe | Peripherique, illustration, detail mineur | Erreur mineure |

**Ordonner les claims de P1 a P4.** Au sein de chaque niveau, ordonner par
apparition dans l'article (les claims des Results/Discussion avant ceux de l'Intro).

Afficher le tableau des claims classes avant de poursuivre :

```
Claims extraits : X (nouveaux : N, a re-verifier : R, deja OK : S)

P1 (structurants) : N claims
P2 (support)      : N claims
P3 (contexte)     : N claims
P4 (annexe)       : N claims

Total a verifier cette session : M
```

---

## Phase 3 -- Planification de la verification

Pour chaque claim a verifier, determiner la **strategie de verification** :

| Type de claim | Strategie |
|---------------|-----------|
| Resultat bioinfo (SNP, distances, phylogenie, arbres) | Reproduire via TBannotator MCP (`tool_query_postgres`), scripts existants, ou recalcul |
| Donnee epidemiologique (prevalence, incidence, mortalite) | Verifier dans WHO Global TB Report, ECDC, ou litterature recente via WebSearch |
| Affirmation gene/mutation (katG S315T, rpoB S450L...) | Requete TBannotator (`tool_query_postgres`) ou NCBI/UniProt via WebSearch |
| Claim methodologique ("X surpasse Y", "X est le gold standard") | Verifier dans le papier original cite (WebSearch + WebFetch de l'abstract) |
| Claim de litterature ("il a ete montre que...", "selon [ref]...") | WebSearch du papier cite, lire l'abstract, verifier la correspondance |
| Claim attribue a une reference (TOUTE `\citep`/`\citet`) | **Resoudre la CLE vers le VRAI papier** (lire l'entree .bib : titre, revue, annee, DOI/PMID), puis verifier que ce papier soutient bien l'enonce. Voir le garde-fou « cles quasi-dupliquees » ci-dessous |
| Donnee chiffree ("42% des souches...", "n=342") | Requete BDD si les donnees sont accessibles, sinon verification dans la source citee |
| Claim de selection sur un codon (invariance / conservation / dN-dS d'un residu catalytique ou de site actif) | **Re-requeter `mv_spdi_mutations` aux 3 positions du codon ET re-traduire chaque variant** (syn vs NS) avant de faire confiance a un label ; voir le garde-fou ci-dessous |

### Garde-fou -- CLES QUASI-DUPLIQUEES : le claim attribue au MAUVAIS papier

Une `references.bib` construite par FUSION (plusieurs revues, plusieurs agents, plusieurs
sessions) contient presque toujours des **entrees quasi-dupliquees** : le meme papier sous
deux cles, et surtout **deux papiers differents du meme auteur/annee** sous des cles toutes
deux plausibles. Citer « la cle qui a l'air bonne » attribue alors silencieusement un claim
au mauvais papier -- et **rien ne le signale** : bibtex resout la cle, LaTeX compile sans
warning, la relecture lit un nom d'auteur correct.

Vecu (mabossDemo, /claim-check 2026-07-11) : le manuscrit attribuait « le controle
combinatoire de l'EMT a ete etabli par des cribles booleens d'interventions » a
`steinway_2014_hcc` -> qui resout vers Steinway **2014**, *Cancer Research* (« Network
modeling of TGFbeta signaling in hepatocellular carcinoma », PMID 25189528). Le papier qui
etablit reellement ce resultat est Steinway **2015**, *npj Syst Biol Appl* (« **Combinatorial
interventions** inhibit TGFbeta-driven EMT », PMID 28725463). La `.bib` contenait **quatre**
entrees Steinway = 2 papiers, chacun duplique. L'erreur portait sur l'ANTECEDENT PIVOT du
positionnement de l'article, et apparaissait deux fois.

**Procedure (obligatoire des que le manuscrit cite plus d'une dizaine de references) :**

1. **Detecter les entrees a risque** : grouper les entrees de `references.bib` par
   (premier auteur, annee). Tout groupe de taille > 1 est un piege potentiel.
   ```bash
   grep -oE "^@[a-z]+\{[^,]+" references.bib | sed 's/^@[a-z]*{//' | \
     sed -E 's/[_-]?[0-9]{4}.*//' | sort | uniq -d   # familles d'auteurs dupliquees
   ```
2. **Pour chaque cle REELLEMENT citee dans le .tex**, resoudre la cle vers son entree .bib
   et **lire titre + revue + annee + DOI/PMID**. Ne jamais se fier au nom de la cle : une cle
   nommee `steinway_2014_hcc` ne dit rien de fiable sur le contenu.
3. **Confronter le titre du papier a l'ENONCE du claim.** Si l'enonce parle d'interventions
   combinatoires et que le titre parle de modelisation de reseau, c'est une misattribution.
4. **Verifier via PubMed/DOI** (esummary) que le PMID/DOI de l'entree correspond bien au
   papier attendu.
5. Signaler les doublons a `/bib-check` pour dedoublonnage : ils sont la CAUSE RACINE et
   resteront un piege tant qu'ils existent.

### Garde-fou -- LIMITES OPERATIONNELLES de l'outil vs TAILLE des donnees (reproductibilite)

Un numero de version ne suffit pas a rendre une methode reproductible : verifier que l'outil,
dans sa configuration PAR DEFAUT, **accepte les donnees de l'article**. Vecu (mabossDemo) : le
manuscrit annoncait « MaBoSS 2.6.6 », mais le binaire par defaut est limite a **64 noeuds** et
les modeles etendus en comptent 65-66 ; ils tournaient en realite sur `MaBoSS_128n`, choisi
automatiquement par le wrapper. Les resultats etaient valides, mais **un lecteur reproduisant
avec le binaire par defaut aurait echoue sans comprendre pourquoi**. Reflexe : pour tout outil
cite, chercher ses bornes (nombre max d'entites, taille max, precision) et verifier qu'elles
couvrent les donnees ; si un binaire/mode alternatif a ete utilise, le DIRE dans les Methodes.

### Garde-fou -- claims de selection per-codon (re-traduire avant de croire)

Pour tout claim qui affirme l'invariance, la conservation ou un dN/dS d'un
**residu catalytique / de site actif** (typique des articles d'annotation
structure-guidee MTBC), ne JAMAIS recopier les labels syn/NS ni les comptes d'un
dossier d'analyse : les re-deriver depuis la base brute. Piege recurrent
documente (projet `dark_enzymes`, /claim-check 2026-06-06) : sur les genes du
**brin +**, des variants **synonymes de la 3e base (wobble)** avaient ete
comptes comme non-synonymes, des substitutions d'acides amines avaient ete mal
nommees, et un variant du **codon voisin** avait ete attribue au mauvais residu
(« H136P n=17 » etait en fait le synonyme H136H ; « D178E n=87 » appartenait au
codon suivant). Les conclusions de fond tenaient mais les chiffres illustratifs
etaient faux.

Procedure de verification (deterministe) :
1. Calculer le codon de chaque residu sur la reference H37Rv et **verifier qu'il
   traduit bien l'acide amine attendu** (garde-fou de cadre de lecture). Brin + :
   position SPDI 0-based == index Python ; `idx0 = cds_start1 + (res-1)*3 - 1`,
   `codon = genome[idx0:idx0+3]`. Brin - : extraire le codon forward puis
   `revcomp` (cf. entree KB « SPDI brin negatif »).
2. Requeter `mv_spdi_mutations` aux 3 positions, filtrer `mutation_type='SNP'`.
3. Pour chaque variant, reconstruire le codon mute et re-traduire :
   `SYN si translate(new)==translate(ref) sinon NS`. Ne compter comme variant du
   site QUE les positions DANS le codon (un variant a codon±1 = autre residu).
4. Le contraste « site invariant vs voisins variables » doit comparer des **NS
   reels**, pas « tout variant au codon » (un wobble synonyme frequent fausse
   tout).
5. Verifier `mv_lineage_markers` aux positions : 0 marqueur = « aucune lignee
   fixee » solide.

Patron reutilisable : `dark_enzymes/analyses/phase4_selection_recheck.py`.

**Afficher le plan de verification complet** avant de l'executer :

```
Plan de verification :

#1 [P1] "Les souches L4.1 presentent 95% de resistance a l'INH"
   → Strategie : requete TBannotator (resistance x lineage)

#2 [P1] "katG S315T est la mutation la plus frequente"
   → Strategie : requete TBannotator + verification WHO catalogue

#3 [P2] "La distance SNP mediane entre L4.1 et L4.2 est de 847"
   → Strategie : recalcul via TBannotator (snp_distance)

...

Proceder ? (les claims sont traites par ordre P1 → P4)
```

---

## Phase 4 -- Execution des verifications

**Parallelisation** : les verifications de claims independants (ne se
referant pas les uns aux autres) sont lancees en parallele dans un meme
message tool-use. Grouper par priorite : d'abord tous les P1 en
parallele, puis P2, puis P3+P4 ensemble. Les requetes TBannotator,
WebSearch, et WebFetch des differents claims n'ont pas de dependance
mutuelle et gagnent 3-5x en vitesse avec l'execution concurrente.

### Pour chaque claim :

1. **Executer la strategie** definie en Phase 3
2. **Attribuer un statut** :

   | Statut | Signification |
   |--------|---------------|
   | confirme | L'affirmation est verifiee et correcte |
   | a_corriger | L'affirmation est fausse ou significativement inexacte |
   | partiellement_confirme | L'affirmation est globalement correcte mais imprecise ou exageree |
   | non_verifiable | Impossible a verifier avec les outils disponibles |

3. **Documenter la preuve** : quelle source, quelle requete, quel resultat
4. **Capturer la reference en BibTeX** (voir section ci-dessous)
5. **Ajouter des notes** si necessaire (correction suggeree, nuance, etc.)

### Memorisation systematique des references

**Regle absolue** : toute source utilisee pour verifier un claim doit etre
memorisee en BibTeX dans `litterature_review/references.bib`. Cela inclut :

- Les articles cites dans le manuscrit et consultes pour verification
- Les articles trouves via WebSearch qui confirment ou infirment un claim
- Les rapports institutionnels (WHO, ECDC) utilises comme preuve
- Les catalogues de reference (WHO catalogue of mutations, etc.)

**Pour chaque reference ajoutee** :
1. Construire l'entree BibTeX complete (author, title, journal, year, doi, pmid)
2. Ajouter le champ `keywords = {claim_check}` pour tracer l'origine
3. Ajouter le champ `annote = {Utilise pour verifier claim #N: "enonce du claim"}` 
4. Verifier que l'entree n'existe pas deja dans references.bib (par DOI ou PMID)
5. Append a la fin du fichier

**Si `litterature_review/` n'existe pas** : le creer avec un `references.bib`
et un `index.md` minimal. Le skill `/lit-review` pourra ensuite enrichir
ce repertoire.

**Exceptions** (pas de BibTeX a creer) :
- Verification par recalcul direct (requete TBannotator, script) → pas de ref externe
- Verification par coherence interne de l'article → pas de ref externe

**Format BibTeX** :
```bibtex
@article{who2023catalogue,
  author  = {{World Health Organization}},
  title   = {Catalogue of mutations in {Mycobacterium tuberculosis} complex
             and their association with drug resistance},
  year    = {2023},
  doi     = {10.xxxx/xxxxx},
  keywords = {claim_check},
  annote  = {Utilise pour verifier claim #2: "katG S315T est la mutation
             la plus frequente conferant la resistance a l'INH"}
}
```

### Progression

Afficher l'avancement tous les 5 claims :

```
Progression : 10/28 claims verifies
  P1 : 4/4 (3 confirmes, 1 infirme ⚠)
  P2 : 6/8
  P3 : 0/12
  P4 : 0/4
```

### Regles imperatives

- **Priorite absolue si P1 non confirme** : signaler a l'utilisateur des la
  decouverte. Un claim structurant incorrect remet en question l'article
- **Ne pas inventer de preuves** : si la verification est inconcluante, statut = non_verifiable
- **Utiliser les outils reels** : ne pas se fier a sa memoire pour confirmer un chiffre.
  Toujours executer la requete/recherche
- **Garder une trace** de chaque requete executee pour la reproductibilite

---

## Phase 5 -- Rapport et mise a jour du registre

### 1. Ecrire/mettre a jour `claim_check.md`

Format du fichier :

```markdown
# Registre de verification des claims

**Article :** [titre extrait du \title{}]
**Derniere verification :** YYYY-MM-DD

## Claims

| # | Priorite | Section | Claim | Statut | Verifie le | Source/Preuve | Ref BibTeX | Notes |
|---|----------|---------|-------|--------|------------|---------------|------------|-------|
| 1 | P1 | Results | "Les souches L4.1 presentent 95% de resistance a l'INH" | confirme | 2026-04-05 | TBannotator: SELECT ... | — (recalcul) | — |
| 2 | P1 | Discussion | "katG S315T est la mutation la plus frequente" | confirme | 2026-04-05 | WHO catalogue 2023 | @who2023catalogue | — |
| 3 | P2 | Results | "La distance SNP mediane est de 12" | a_corriger | 2026-04-05 | Recalcul = 14 | — (recalcul) | Corriger |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |
```

**Regles d'ecriture :**
- Les claims sont ordonnes par priorite (P1 en haut, P4 en bas)
- Au sein d'un meme niveau, ordre d'apparition dans l'article
- Les claims non_verifiable conservent leur derniere date de tentative
- En mode `--force`, toutes les dates sont mises a jour

### 2. Afficher le rapport resume

```markdown
# Rapport claim-check

**Article :** [titre]
**Date :** YYYY-MM-DD
**Mode :** [normal / force / stale-days=N]

## Resume

| Priorite | Total | Confirme | Infirme | Partiel | Non verifiable |
|----------|-------|----------|---------|---------|----------------|
| P1 | N | N | N | N | N |
| P2 | N | N | N | N | N |
| P3 | N | N | N | N | N |
| P4 | N | N | N | N | N |

## Claims necessitant correction ou verification

### P1 — Claims structurants necessitant correction

- **Claim #3** (Results, L.142) : "La distance SNP mediane est de 12"
  - Statut : a_corriger
  - Preuve : Recalcul via TBannotator donne 14
  - Impact : Ce chiffre est utilise dans la discussion pour argumenter X
  - Action suggeree : Corriger le chiffre et verifier les conclusions qui en decoulent

### Claims P2-P4 a revoir

- **Claim #7** (Intro, L.28) : "TB est responsable de 1.3M deces/an"
  - Statut : partiellement_confirme
  - Preuve : WHO 2024 donne 1.25M (chiffre mis a jour)
  - Action suggeree : Mettre a jour le chiffre

## Claims non verifiables

- **Claim #15** (Methods, L.89) : raison de l'echec de verification
```

---

## Consignes generales

### Ce que le skill DOIT faire
- Lire TOUT le manuscrit avant d'extraire les claims
- Etre exhaustif dans l'extraction (ne pas passer a cote de claims importants)
- **Executer la Phase 1bis (audit de coherence numerique)** sur tout manuscrit
  comportant plus de quelques chiffres : extraire tous les nombres via ripgrep,
  detecter les divergences inter-occurrences, verifier les sommes attendues,
  controler la coherence EN/FR si les deux versions coexistent. Toute
  incoherence devient un claim `internal_consistency` auto-promu P1.
- Prioriser correctement : un claim P1 non confirme necessite une action prioritaire
- Utiliser les outils reels (TBannotator, WebSearch) pour chaque verification
- **Memoriser systematiquement chaque reference** utilisee pour la verification
  dans `litterature_review/references.bib` (creer le repertoire si inexistant)
- Maintenir le registre `claim_check.md` a jour et coherent
- Afficher le plan de verification AVANT de l'executer

### Ce que le skill NE DOIT PAS faire
- Se fier a sa memoire pour confirmer un fait, un chiffre ou une reference
- Verifier un claim deja verifie recemment (sauf `--force`)
- Modifier le contenu de l'article (seulement signaler les problemes)
- Attribuer un statut confirme sans preuve tangible
- Ignorer les claims P4 (ils doivent etre extraits et classes, meme si verifies en dernier)
- **Utiliser une reference pour verifier un claim sans l'ajouter dans references.bib**

### Integration avec l'ecosysteme

- **`litterature_review/references.bib`** : depot BibTeX partage avec `/lit-review`.
  Chaque reference utilisee pour la verification y est ajoutee avec
  `keywords = {claim_check}` pour tracer son origine
- **`/lit-review`** : peut ensuite approfondir les sujets identifies par claim-check
- **`/bib-check`** : peut verifier les references ajoutees par claim-check


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
