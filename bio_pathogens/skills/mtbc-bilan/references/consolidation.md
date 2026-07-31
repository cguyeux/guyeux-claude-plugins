# Consolidation des connaissances et niveaux de consolidation -- version integrale

Reference de `mtbc-bilan` : texte integral des Phases 1 et 1bis. Le SKILL.md
en garde la procedure resumee. A lire pendant la lecture du cahier de labo,
notamment pour les regles d'attribution des sept niveaux et les heuristiques
de detection des faits volatils / fragiles.

## Phase 1 -- Lecture du cahier et consolidation des connaissances

L'objectif de cette phase n'est pas de reconstituer l'histoire iterative
du projet, mais de **consolider l'etat actuel des connaissances**. La
lecture se fait **en partant des entrees les plus recentes** et en
remontant le temps, en accumulant les faits etablis et en gardant la
derniere version consolidee en cas de conflit.

**Sources autorisees pour cette phase** :

- `<projet>/CLAUDE.md` (lecture integrale).
- `<projet>/cahier_de_labo.md` (ou `JOURNAL.md`) lu **en entier**,
  dans l'ordre inverse.
- `<projet>/article/` : manuscrit en cours, `claim_check.md`,
  `review/INDEX.md`, `litterature_review/`.
- `<projet>/analyses/`, `<projet>/resultats/`, `<projet>/data/` :
  inspection legere pour l'inventaire (Phase 2).
- `~/.claude/knowledge/tuberculosis.md`, skills `mtbc-lineages`,
  `mtbc-bilan --deepen`.

**Source explicitement INTERDITE** : tout fichier dans
`<projet>/bilans/` (qu'il s'agisse de `.md`, `.pdf`, ou `.tex`).
Les bilans precedents ne sont **ni lus, ni resumes, ni cites**. La
seule operation autorisee sur ce repertoire est `ls` pour detecter
une collision de nom de fichier le jour meme (afin d'appliquer le
suffixe `_v2`, `_v3`...). Cette interdiction garantit que chaque
nouveau bilan est un **document standalone**, ecrit a partir du
cahier de labo et de la litterature, sans reprendre ni amender un
texte anterieur.

**Pourquoi cette regle** : un bilan qui s'appuie sur le precedent
derive vers un mode "delta" ("rien de neuf cote phylogeographie",
"voir v2 pour la datation"), qui suppose la lecture de l'archive
anterieure et perd progressivement son autonomie. L'utilisateur, qui
ouvre le bilan le plus recent pour avoir l'etat du projet, doit y
trouver l'**etat consolide complet**, pas un changelog. La memoire
factuelle reside dans le cahier de labo ; le bilan en est une
relecture argumentee a date.

1. `Read <projet>/CLAUDE.md` (integralement) :
   - Extraire le titre du projet, la lignee, les conventions locales.
   - Comprendre la question scientifique fondatrice du projet.

2. Localiser le journal :
   - Prioritairement `cahier_de_labo.md`.
   - Fallback `JOURNAL.md` (anciens projets comme `methodology/`).
   - Si les deux existent : lire les deux et signaler l'incoherence.

3. **Lire le cahier INTEGRALEMENT, mais dans l'ordre inverse** -- c'est
   la phase la plus importante. Commencer par la derniere entree, puis
   remonter entree par entree jusqu'a la premiere. Si > 5000 lignes, lire
   par chunks de 2000 en partant de la fin, **jamais tronquer
   silencieusement**. Ne pas se contenter de grep les headers.

   **Pourquoi a rebours** : ce qui est ecrit le plus recemment reflete
   l'etat actuel du savoir et des outils du projet. En remontant, on
   ajoute des elements anterieurs uniquement quand ils n'ont pas ete
   recouverts ou contredits par une entree posterieure.

4. **Consolidation au fil de la lecture** : maintenir mentalement (ou
   dans un brouillon) deux structures :

   **A. Carte des connaissances actuelles** -- thematique (lignee/clade,
   marqueurs, datation, phylogeographie, resistance, methodologie...). Pour
   chaque fait consolide, noter :
   - **Le fait** lui-meme (formulation actuelle, post-consolidation)
   - **Comment il a ete etabli** (script `phase4_xxx.py`, methode
     RAxML-NG GTR+G, base de donnees de N souches, reference Coll 2014...)
   - **Le niveau de consolidation** (voir taxonomie Phase 1bis) :
     `etabli`, `convergent`, `unique`, `volatile`, `fragile`,
     `hypothetique`, `speculatif`.
   - **Pour les faits non `etabli`** : amplitude de variation observee
     ou source de fragilite (en chiffres ou en mots si pas chiffrable),
     et une **piste de consolidation** quand elle existe (ou explicitement
     "pas de voie de consolidation evidente avec les donnees actuelles").
   - **Eventuellement** : la mention "version revisee, anterieurement
     [ancien chiffre/affirmation]" si l'evolution est instructive
     (changement de methode, donnee corrigee, biais decouvert).

   **B. Liste des intentions non honorees** -- toute mention dans le
   cahier d'une chose a faire, a verifier, a explorer, qui n'apparait
   ulterieurement nulle part dans une entree plus recente comme realisee.
   Sources typiques :
   - `### Pistes futures` (sections explicites)
   - "il faudrait", "a verifier", "TODO", "on devrait", "prochaine etape"
   - Hypothese formulee mais non testee dans les entrees ulterieures
   - Donnee mentionnee mais non integree (souche, BDD, fichier externe)
   - Reference suggeree comme a lire mais non incorporee a la
     litterature_review

   **Regle de consolidation en cas de conflit** : si l'entree du
   2026-04-15 dit "57 SNP retro-mutes detectes" et celle du 2026-04-22
   dit "apres correction d'alignement, 38 SNP retro-mutes confirmes",
   on garde **38**, eventuellement avec une note pedagogique sur la
   correction. Ne JAMAIS garder les deux chiffres comme si c'etait deux
   resultats independants.

5. Pendant la consolidation, aussi noter :

   a. **Les mecanismes biologiques actuellement invoques** : quels
      genes, quels pathways, quelles hypotheses evolutives sont
      mentionnes dans les entrees recentes ? Alimentera la mise en
      perspective avec la litterature.

   b. **Les echecs instructifs** confirmes (pas remplaces par un succes
      ulterieur) : `Grep ^#### Negatifs` mais aussi lire les sections
      ou quelque chose n'a pas marche. Si une entree ulterieure decrit
      la solution, l'echec est devenu un pas-de-cote dans le narratif
      court ; sinon, il reste comme une limite ou une piste.

   c. **Les indices de statut** :
      `Grep -i "submitted\|accepted\|published\|en preparation\|bouclee"`
      (recents en priorite).

   d. **Le squelette du narratif chronologique court** : 4-8 jalons
      dates qui ressortent en remontant le cahier. Ne PAS reconstruire
      tous les pas du projet ; ne retenir que les tournants reels
      (premier resultat marquant, reorientation, decouverte majeure,
      soumission...).

**Important : separation stricte bookkeeping vs redaction.** La
structure "fait + methode + niveau de consolidation + amplitude /
fragilite + piste" est un format de **bookkeeping interne** utilise
pendant la lecture du cahier en Phase 1. Elle **ne doit jamais
apparaitre telle quelle** dans le bilan final (sous forme de blocs
quote "**Fait :** ... **Methode :** ..." ou de fiches structurees).
Au moment de la redaction (Phase 9.1), chaque element bookkeepe est
**re-rendu en prose** dans des paragraphes argumentes, ou ces memes
informations (chiffres, methode, niveau de consolidation, amplitude)
s'integrent naturellement dans les phrases. Voir les exemples
narratifs de la section "Etat actuel des connaissances acquises" et
"Decouvertes majeures et leur signification" pour le rendu attendu.

---

## Phase 1bis -- Taxonomie du niveau de consolidation

Chaque fait consolide en Phase 1 recoit l'un des **sept niveaux**
suivants. Le choix du niveau est explicite, jamais sous-entendu, et
apparait textuellement dans le bilan (section "Etat actuel des
connaissances" et section "Decouvertes majeures").

### Les sept niveaux

| Niveau | Definition | Indication typique |
|--------|------------|---------------------|
| `etabli` | Reproduit par >=2 methodes ou >=2 executions independantes ; claim-check OK ; robuste aux variations raisonnables de parametres | Vert |
| `convergent` | Plusieurs methodes/analyses concordent, mais non encore formellement reproduit (meme jeu de donnees, methodes proches) | Vert clair |
| `unique` | Une seule analyse/methode ; valeur precise mais sensibilite non testee | Jaune |
| `volatile` | La valeur exacte change significativement avec la methode, le parametre, ou la sous-selection de donnees ; le pattern qualitatif peut rester | Orange |
| `fragile` | Depend d'une hypothese forte (horloge moleculaire stricte, biais H37Rv, modele d'evolution) qui pourrait etre violee | Orange |
| `hypothetique` | Hypothese de travail formulee a partir des resultats du projet, pas encore testee | Rouge clair |
| `speculatif` | Suggere par la litterature, par analogie, ou par intuition ; aucun test sur les donnees du projet | Rouge |

**Regles d'attribution** :

1. Un fait n'est `etabli` que si on peut citer **deux** sources de
   validation (par exemple : RAxML-NG + IQ-TREE concordent, OU resultat
   reproduit a un mois d'intervalle apres ajout de souches, OU verifie
   par claim-check).
2. Un fait est `volatile` des qu'une variation de methode (BEAST vs
   LSD2, modele GTR vs GTR+G+I, sous-echantillonnage) change le
   resultat de plus de 15-20 % en relatif, ou de plus que l'IC95
   nominal.
3. Un fait est `fragile` s'il repose sur une hypothese identifiable et
   testable mais non testee : ex. "MRCA = 1240 CE en supposant horloge
   stricte" -> fragile si la relaxation de l'horloge n'a pas ete
   essayee.
4. La distinction `volatile` / `fragile` :
   - **volatile** = "le chiffre bouge quand on change la methode"
     (instabilite empirique observee)
   - **fragile** = "le chiffre repose sur une hypothese non verifiee
     qui, si fausse, le casserait" (instabilite logique potentielle)
   Un meme fait peut etre les deux ; dans ce cas, prendre le niveau le
   plus pessimiste (`fragile`).
5. `hypothetique` vs `speculatif` :
   - **hypothetique** = formule a partir des donnees du projet,
     testable a l'avenir (ex. "la retro-mutation pourrait s'expliquer
     par selection convergente sur katG").
   - **speculatif** = vient de l'exterieur, pas de donnee projet pour
     le supporter ou le refuter directement (ex. "l'apparition de
     proto-L4.2 pourrait coincider avec les famines du XIVe siecle").

### Marquage explicite des faits volatils / fragiles

Tout fait `volatile` ou `fragile` doit imperativement preciser :

1. **L'amplitude de variation observee** (volatile) ou **l'hypothese
   qui pourrait casser** (fragile). En chiffres si possible :
   - "MRCA = 1240 CE [LSD2 sur arbre RAxML] ; 1080-1410 CE selon la
     methode (BEAST tip-dating : 1110 CE ; BEAST node-dating : 1340 CE ;
     LSD2 : 1240 CE)."
   - "Estimation fragile : suppose une horloge moleculaire stricte
     ; la relaxation par BEAST n'a pas ete testee, elle pourrait
     elargir l'IC de ~200 ans."
2. **Une piste de consolidation** quand elle existe :
   - "Pour consolider : lancer BEAST avec horloge relaxee et
     calibration par dates de prelevement (`/molecular-clock`)."
   - "Pour consolider : repliquer avec sous-echantillonnage 80%
     (jackknife) pour estimer la stabilite empirique."
   - Si aucune piste evidente : "Pas de voie de consolidation
     immediate avec les donnees actuelles ; la stabilite ne pourra
     etre evaluee qu'avec un corpus elargi."
3. La piste de consolidation est **automatiquement ajoutee** soit a
   "A faire maintenant" (si elle a deja ete evoquee dans le cahier),
   soit a "Pistes d'approfondissement" (si c'est une piste deduite).
   Le lien est explicite : "Cf. section 'A faire maintenant', item
   `<titre>`."

### Encadre `fragilite` (nouveau type)

Pour les faits centraux du projet qui sont `volatile` ou `fragile`,
inserer un encadre dedie dans le bilan PDF, sur le modele de
`notion`/`methode`/`originalite`/`remarquable`. Ce nouvel encadre,
**`fragilite`**, attire l'attention sur :

- Pourquoi le resultat est instable / fragile
- L'amplitude exacte de la variation
- Les hypotheses sous-jacentes
- Les voies de consolidation

Voir section 9.1bis pour la syntaxe LaTeX exacte (a ajouter au template
`bilan.latex` lors de la prochaine evolution du template ; en attendant,
utiliser un environnement `tcolorbox` rouge/orange ad hoc, ou recycler
`remarquable` avec un titre commencant par "Fragilite :").

### Heuristiques de detection automatique

Pendant la lecture du cahier (Phase 1), reperer les signaux suivants
qui orientent vers `volatile`/`fragile`/`hypothetique` :

- Mots-cles : "depend de", "selon la methode", "varie entre", "sous
  hypothese de", "il faudrait verifier", "preliminaire", "indicatif",
  "ordre de grandeur", "robuste a confirmer", "a tester", "non encore
  reproduit".
- Plusieurs valeurs differentes pour le meme fait au fil des entrees
  (ex. dates de MRCA qui evoluent) -> `volatile` par defaut, meme si
  la derniere valeur est rapportee comme "consolidee".
- Resultat issu d'un seul script sans re-execution -> jamais `etabli`,
  au mieux `unique`.
- Hypothese biologique mentionnee dans la section "Hypotheses" ou
  "Interpretation" mais sans test associe -> `hypothetique`.
