---
name: manuscript-review
description: >-
  Peer review of a scientific manuscript as for a high-impact journal. Reads the full paper
  (LaTeX or text), evaluates structure, methodology, statistics, terminology, figures and
  references, and produces a structured review in French with severity-ranked
  recommendations. For TB / MTBC manuscripts, validates the state of the art and citation
  completeness against tbmonitor-papers (~190k PubMed TB abstracts). Use when the user asks
  for a critical read of a manuscript, wants to know what a reviewer would object to, asks
  to review a paper before submission, or wants a second opinion on a draft.
argument-hint: "<path to main.tex or manuscript file>"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, mcp__tbmonitor__execute_sql, mcp__tbmonitor__show_schema
---

# /manuscript-review : Review de manuscrit scientifique

Produit une review structuree, serieuse et complete d'un article scientifique,
comme le ferait un reviewer exigeant pour un journal a haut facteur d'impact.



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
/manuscript-review path/to/main.tex
```

Si aucun argument, chercher un fichier `main.tex` dans le repertoire courant.

## Processus

### Phase 1 : Lecture integrale du manuscrit

Lire le manuscrit **en entier**, section par section. Ne pas commencer la review
avant d'avoir lu la derniere ligne (bibliographie incluse).

Pour un fichier LaTeX :
1. Identifier la structure : `\section`, `\subsection`, `\begin{table}`, `\begin{figure}`
2. Lire par blocs de 300 lignes max (limite du Read tool)
3. Prendre des notes mentales sur chaque section au fur et a mesure
4. Lire aussi les fichiers inclus (`\input{}`, `\include{}`)
5. Identifier les figures referencees et verifier qu'elles existent

### Phase 1bis : RECROISEMENT MECANIQUE des chiffres avec les donnees sources (OBLIGATOIRE)

**Ne jamais se fier a la relecture pour verifier un chiffre.** La relecture ne rattrape
PAS une valeur attribuee au mauvais modele/echantillon/condition : elle lit une phrase
plausible et passe. Seul le recroisement mecanique l'attrape. Cette phase est donc
obligatoire des que le manuscrit rapporte des nombres issus de calculs.

1. **Localiser les donnees sources** : fichiers de resultats (`.json`, `.csv`, logs de
   run, tableaux) produits par les scripts d'analyse. Les demander a l'utilisateur si
   leur emplacement n'est pas evident.
2. **Extraire tous les nombres du manuscrit** (abstract, texte, legendes, tables) avec
   leur contexte : a quelle condition, quel modele, quel echantillon chacun est attribue.
3. **Verifier chaque nombre contre la source**, et surtout **verifier l'ATTRIBUTION** :
   le chiffre existe-t-il bien dans les donnees, et provient-il bien de la condition
   annoncee dans la phrase ? Signaler en priorite les valeurs qui **existent dans les
   donnees mais sous une autre condition** (c'est le mode d'erreur le plus dangereux :
   le chiffre est « vrai », mais il ne dit pas ce que la phrase lui fait dire).
4. **Verifier l'HOMOGENEITE des bras de comparaison** : quand plusieurs valeurs sont
   comparees (dans une phrase, une figure, un tableau), proviennent-elles de conditions
   qui ne different QUE par le facteur dont on tire la conclusion ? Tout facteur
   supplementaire qui varie en meme temps est un facteur de confusion → BLOQUANT.
5. **Verifier la coherence interne** : abstract vs resultats vs discussion vs legendes
   vs tables. Un meme resultat doit porter le meme chiffre partout.
6. **RECALCULER les nombres DERIVES, ne pas se contenter de les retrouver.** Un nombre
   du manuscrit qui n'existe PAS tel quel dans les donnees (une difference, une somme,
   un pourcentage, un « ajoute N elements », un « sur N cas ») est **derive** : il ne
   peut pas etre valide par simple recherche dans les sources. Il doit etre **recalcule
   depuis les donnees brutes**. Les points 1-5 sont aveugles a cette classe d'erreur,
   parce que le nombre n'a aucune source a laquelle le confronter.
   **PIEGE CANONIQUE : une difference de CARDINAUX n'est pas un nombre d'ELEMENTS
   NOUVEAUX.** $|A| - |B| \neq |A \setminus B|$ des que la correspondance entre $A$ et
   $B$ n'est pas injective. Vecu (mabossDemo) : un modele etendu passait de 25 a 49
   etats stables, et le manuscrit en concluait « adds 24 states ». Le calcul de la
   difference ENSEMBLISTE reelle donnait **12** nouveaux etats seulement, les 12 autres
   etant des **dedoublements** d'etats existants (meme configuration, deux variantes
   d'une boucle bistable). Le decompte etait faux, et sa correction (49 = 25 + 12 + 12)
   s'est revelee bien plus informative que l'affirmation initiale.
   **REFLEXE : pour tout « ajoute / gagne / perd N elements », exiger le calcul de la
   difference ensembliste (ou de l'appariement explicite), jamais la soustraction des
   totaux.** Verifier de meme les pourcentages (recalculer numerateur et denominateur)
   et les « N sur M » (verifier M).

**Risque specifique aux etudes multi-variantes / multi-modeles / multi-jeux de donnees**
(frameworks de variantes, ablations, grilles d'hyperparametres, cohortes multiples) :
le recit veut une serie homogene, les donnees viennent de variantes heterogenes, et la
substitution d'un chiffre par celui d'une variante voisine est **invisible a la
relecture**. C'est le premier endroit ou chercher.

Consigner les ecarts trouves : ils alimentent les preoccupations MAJEURES de la review.

### Phase 2 : Grille d'evaluation (11 dimensions)

Evaluer le manuscrit sur chaque dimension. Pour chaque probleme identifie,
attribuer un niveau de severite :

| Niveau | Signification |
|--------|---------------|
| **BLOQUANT** | Empeche la publication en l'etat |
| **MAJEUR** | Affaiblit significativement la credibilite |
| **MODERE** | Amelioration necessaire mais non bloquante |
| **MINEUR** | Polish, coherence, presentation |

#### D1. Titre et Abstract
- Le titre reflète-t-il fidelement le contenu ?
- L'abstract est-il autonome (comprehensible sans lire l'article) ?
- Les claims de l'abstract sont-elles toutes soutenues dans le texte ?
- Les chiffres cles sont-ils qualifies (biais, limites) ?
- Longueur appropriee pour le journal cible ?

#### D2. Introduction
- Contexte suffisant pour un lecteur du domaine large ?
- Etat de l'art complet et equilibre ?
- Gap clairement identifie ?
- Objectifs explicites, numerotes si multiples ?
- Progression logique : contexte → gap → objectifs ?

#### D3. Methodes : Reproductibilite
- Un chercheur independant pourrait-il reproduire l'analyse ?
- Versions logicielles et parametres documentes ?
- Criteres d'inclusion/exclusion formalises et objectifs ?
- Pipeline dependant d'un outil unique non valide ? → RED FLAG
- Donnees d'entree accessibles ?

#### D4. Methodes : Rigueur statistique
- Tests statistiques adaptes aux types de donnees ?
- Correction pour tests multiples decrite et appliquee ?
- Tailles d'echantillon suffisantes ?
- Biais d'echantillonnage identifies et traites ?
- Intervalles de confiance rapportes ?
- Distinction correlation/causalite respectee ?

#### D5. Resultats : Coherence et completude
- Tous les objectifs annonces sont-ils traites ?
- Les resultats soutiennent-ils les claims ?
- Statistiques de genetique des populations presentes si pertinentes ?
  (pi, FST, Tajima's D, Ne, structure AMOVA...)
- Chiffres coherents entre abstract, resultats, discussion, tables ?
- Resultats negatifs rapportes honnetement ?

#### D6. Discussion : Interpretation
- Les interpretations depassent-elles les donnees ?
- Les limites sont-elles discutees honnetement et completement ?
- Comparaison adequate avec la litterature existante ?
- Distinction entre convergence vraie et contraintes universelles ?
- Hypotheses clairement etiquetees comme telles ?
- Les resultats refutes sont-ils traites avec la meme rigueur que les confirmes ?

#### D7. Terminologie et nomenclature
- Terminologie conforme aux standards du domaine ?
- Definitions fournies pour termes non standard ?
- Coherence interne (meme terme = meme concept tout au long) ?
- Noms de genes en italique, proteines en romain ?
- Unites SI, abbreviations definies a la premiere occurrence ?

#### D8. Figures et tables
- Figures referencees dans le texte ?
- Legendes autonomes (comprehensibles sans lire le texte) ?
- Qualite suffisante (resolution, lisibilite) ?
- Tables non redondantes avec le texte ?
- Coherence des chiffres entre texte et tables ?

#### D9. Bibliographie
- References appropriees et a jour ?
- Format homogene ?
- Auto-citations dans les normes (<15% sauf justification) ?
- References manquantes pour les claims fortes ?
- Preprints ou « in preparation » pour des outils critiques ? → FLAG

> **Manuscrits TB / MTBC, validation de l'etat de l'art.** Valider la
> completude de l'etat de l'art et des citations contre `tbmonitor-papers`
> (~190k abstracts PubMed TB pre-indexes, acces SQL sub-seconde via
> `mcp__tbmonitor__execute_sql`). Objectif : faire remonter **toute
> publication recente majeure oubliee par les auteurs** sur le sujet du
> manuscrit, et la signaler explicitement dans la review.

#### D10. Structure et equilibre
- Proportions section par section equilibrees ?
- Discussion structuree en sous-sections thematiques ?
- Materiaux supplementaires listes et decrits ?
- Longueur globale appropriee pour le journal cible ?
- Redondances entre sections ?

#### D11. Impact et originalite
- Quelle est la contribution principale ?
- Le manuscrit change-t-il la pratique ou la comprehension ?
- Les donnees/methodes sont-elles reutilisables par d'autres ?
- Le manuscrit repond-il a un besoin reel du domaine ?

### Phase 3 : Redaction de la review

Produire la review en **francais**, en suivant strictement ce format :

```markdown
# REVIEW DE MANUSCRIT

**Titre :** [titre complet du manuscrit]
**Reviewer :** Expertise en [domaines pertinents]

---

## EVALUATION GENERALE

[Paragraphe de synthese : forces, faiblesses, positionnement.
 Doit etre lisible independamment du reste.]

**Recommandation :** [Accepte / Revisions mineures / Revisions majeures / Rejet]

---

## I. PREOCCUPATIONS MAJEURES

### 1. [Titre du point]
[Description du probleme, impact, et recommandation concrete]
**Recommandation :** [action specifique]

[Repeter pour chaque point BLOQUANT ou MAJEUR]

---

## II. PREOCCUPATIONS MODEREES

### N. [Titre]
[Plus court, mais toujours avec recommandation]

---

## III. PREOCCUPATIONS MINEURES

### N. [Titre]
[Concis, format liste acceptable]

---

## IV. POINTS DE FORCE

[5-8 points positifs specifiques et argumentes.
 NE PAS OUBLIER cette section — une review equilibree est plus credible.]

---

## V. RECOMMANDATIONS FINALES

### Obligatoires (bloquantes)
1. [...]

### Fortement souhaitables
N. [...]

### Souhaitables
N. [...]

---

**DECISION :** [Revisions majeures / mineures / etc.]
**Score :** [X/10] (potentiel Y/10 apres revisions)
```

## Consignes

### Ce que la review DOIT faire
- Lire TOUT le manuscrit avant de commencer a rediger
- Etre **specifique** : citer les numeros de ligne, les phrases problematiques
- Proposer des **solutions concretes**, pas juste signaler des problemes
- Evaluer la **coherence interne** (abstract vs resultats vs discussion vs tables)
- Verifier les **chiffres** : totaux, pourcentages, effectifs coherents ?
- Identifier les **claims non soutenues** par les donnees presentees
- Distinguer ce qui est **demontré** vs **suggere** vs **speculé**

### Ce que la review NE DOIT PAS faire
- Survoler des sections, chaque paragraphe compte
- Etre complaisante : une review molle n'aide personne
- Etre destructrice : critiquer sans proposer
- Ignorer les points positifs : l'equilibre renforce la credibilite
- Proposer des analyses irréalisables (ex. : wet lab quand l'equipe est bioinformatique)
- Repeter les memes points sous des formulations differentes

### Calibration du score
| Score | Signification |
|-------|---------------|
| 9-10  | Publiable en l'etat dans Nature/Science (exceptionnel) |
| 8-8.5 | Revisions mineures, journal top-10 du domaine |
| 7-7.5 | Revisions majeures, bon potentiel apres corrections |
| 6-6.5 | Revisions majeures substantielles, potentiel incertain |
| 5-5.5 | Faiblesses structurelles, resoumission necessaire |
| <5    | Rejet recommande, problemes fondamentaux |

### Adaptation au domaine
- **Genomique/bioinformatique** : verifier reproductibilite pipeline, validation independante, standards FAIR
- **Epidemiologie** : verifier biais d'echantillonnage, correction, generalisation
- **Phylogenetique** : verifier modeles d'evolution, support branches, sensibilite parametres
- **Resistance medicamenteuse** : verifier genotypique vs phenotypique, catalogues de reference
- **NLP / evaluation de LLM / ML** : verifier variance run-a-run et significativite (sorties LLM stochastiques → un run unique ne suffit pas), IC de Wilson/bootstrap sur petits jeux de test, macro-F1 vs accuracy sur classes desequilibrees (le « best model » se renverse selon la metrique), reproductibilite du prompt (texte integral, temperature, version/date d'API, exclusion des sorties invalides), asymetrie par classe masquee par la macro-moyenne, comparaison equitable supervise fine-tune vs LLM zero/few-shot (dispositif souvent apples-to-oranges), recall=1.0 exact = comportement degenere. **Grille detaillee : `~/.claude/knowledge/manuscript-review-llm-eval.md` (a lire avant de reviewer un papier qui mesure/compare un systeme LLM).**
- **Statistique** : verifier assumptions, puissance, corrections multiples

> Note : la dimension **D5** liste des statistiques de genetique des populations (pi, FST, Tajima's D, AMOVA...), pertinentes UNIQUEMENT pour les papiers de genomique evolutive. Pour un papier hors de ce domaine (NLP, ML, ingenierie logicielle...), ignorer ces items et appliquer les criteres du domaine ci-dessus a la place.

### Sauvegarde automatique de la review

A la fin de la Phase 3, **sauvegarder systematiquement** la review dans un fichier
Markdown horodate :

1. Creer le repertoire `review/` a cote du fichier `.tex` s'il n'existe pas
2. Nommer le fichier avec la date et l'heure : `review/YYYY-MM-DD_HHhMM.md`
   (ex. `review/2026-04-05_14h32.md`)
3. Y ecrire la review complete telle qu'affichee a l'utilisateur
4. Confirmer le chemin du fichier sauvegarde dans la sortie

Cela permet de conserver un historique des reviews successives et de comparer
l'evolution du manuscrit entre deux passages.

### Si argument fourni
L'argument `$ARGUMENTS` est le chemin vers le manuscrit. Commencer la lecture immediatement.
Si pas d'argument, chercher `main.tex` dans le repertoire courant, sinon demander.


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
