---
name: beamer-slides
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST): designs and checks a full
  scientific Beamer talk from existing peer-reviewed research material. Reads
  the project memory and manuscript, settles message, audience, duration and
  the two languages (slides, speaker), turns the time budget into a slide
  budget, ranks what may enter, audits which figures survive projection,
  writes the narrative plan and per-slide spec, then emits the deck plus a
  timed speaker script and a pedagogical support sheet. Ends with mechanical
  checks (overflow, density, decorative TikZ, claim traceability) and a
  simulated-audience review. Also EDITS an existing deck under the constraint
  that any addition pays for itself in the time budget, and DECLINES it into a
  shorter or translated variant sharing one source. Use for a talk, seminar,
  conference or defence deck, speaker notes, a deck check, a short version, a
  fork of a deck, or /slides. For one or two slides use slide-design; for one
  slide, slide-polish; for a poster, latex-posters.
user_invocable: true
invocation: /slides
---

# beamer-slides — concevoir un exposé, puis le contrôler

## Le défaut qu'il corrige, mesuré

Audit de neuf decks du parc, 2026-09-09. Ce ne sont pas des impressions.

| Mesure | Constat |
|---|---|
| Graphiques de données (`pgfplots`, `axis`) | **0** sur huit decks sur neuf. Des arguments quantitatifs, jamais montrés comme données. |
| Réductions de police | 431 pour 75 frames (audition PR), 311 pour 96 (séminaire), 95 pour 22. On rétrécit pour faire tenir au lieu de couper. |
| `Overfull \vbox` | 17, 5 et 3 dans les logs, jamais relus. Sur L5L6, une légende passe sous le cadre et chevauche le pied de page, dans un deck présenté. |
| Volume contre durée | 75 à 96 frames pour 20 minutes. |
| Thèmes | `default`, `Madrid`, metropolis, ou aucun. Pas d'identité. |

Et deux défauts de fond, visibles à l'œil. La **puce déguisée en schéma** :
TikZ ne sert qu'à dessiner des rectangles arrondis contenant des phrases, ce
qui n'apporte rien de plus qu'une liste tout en occupant la moitié de la slide.
Le **mur de puces en colonnes** : trente-cinq items en corps réduit, illisibles
au-delà du troisième rang.

Ce qui, en revanche, va déjà bien : le narratif. `presentation_squelette.md` de
L5L6 porte un fil rouge en une phrase, un arc explicite, un message par section,
un take-home et une note de calibrage. Ne pas le réinventer, s'en inspirer.

## Le principe qui commande tout le reste

**Une slide est un objet à regarder, pas un texte à lire.** L'auditoire ne peut
pas faire les deux à la fois : s'il lit, il n'écoute pas. D'où la règle par
défaut, inversée par rapport à l'usage courant : **l'objet visuel est le défaut,
la liste à puces est l'exception qui doit se justifier** dans la fiche de la
slide. Un titre est une assertion, pas une étiquette : « L5 et L6 épousent la
partition ethnolinguistique », jamais « Résultats ».

Deuxième principe, qui commande le volume : **le budget de temps précède le
choix du contenu.** On convertit d'abord la durée en nombre de slides, puis on
décide ce qui entre. L'ordre inverse produit mécaniquement les 75 frames pour
20 minutes.

## Localiser le contexte

Racine du projet : premier parent contenant `cahier_de_labo.md`. Lire, dans cet
ordre et seulement s'ils existent :

```
CLAUDE.md                    instructions opérationnelles du projet
etat_des_decouvertes.md      la vérité scientifique consolidée, et la phase déclarée
plan_narratif.md             si l'article a déjà été conçu, sa chaîne d'arguments
article/main.tex             le manuscrit, s'il existe
cahier_de_labo.md            les trois dernières entrées seulement
pistes.md                    ce qui est ouvert, pour la slide des perspectives
claim_check.md, fig_check.md ce qui est déjà vérifié, et ce qui ne l'est pas
```

Afficher un résumé de l'état connu avant de travailler. **Si ces fichiers
n'existent pas, le dire** et travailler depuis ce que l'utilisateur fournit :
ne jamais affirmer un état scientifique qu'aucun registre ne porte.

Livrables dans `<projet>/presentations/AAAA-MM-JJ_<slug>/`. Un projet donne
plusieurs exposés au fil du temps, à des publics différents ; un répertoire par
exposé les empêche de s'écraser.

## Les douze gestes

Les gestes 1 à 7 ne produisent **aucun LaTeX**. C'est délibéré : écrire des
slides avant d'avoir décidé quoi montrer est la cause première des decks du parc.

### 1. Le cadrage

Quatre paramètres. Les demander par `AskUserQuestion` s'ils ne sont pas donnés,
en une seule question à choix multiples plutôt qu'en quatre allers-retours.

- **L'occasion** : séminaire d'équipe, conférence, audition, soutenance, cours,
  grand public, réunion de projet. Elle fixe l'intensité du thème et le degré de
  formalisme.
- **Le public réel**, pas le public nominal : spécialistes du domaine,
  biologistes non informaticiens, informaticiens non biologistes, jury
  pluridisciplinaire, étudiants. C'est lui qui décide de ce qu'il faut
  expliquer et de ce qu'on peut supposer connu.
- **La durée**, et si les questions sont dedans ou en plus.
- **Les deux langues, séparément** : celle des slides et celle de l'oral. Elles
  diffèrent souvent (slides en anglais, exposé en français) et commandent des
  livrables différents.

Détail et conséquences de chaque valeur : `references/cadrage.md`.

### 2. Le message et le fil conducteur

Produire **deux à quatre propositions contrastées, jamais une seule**. Une
proposition unique n'est pas un choix, c'est une décision déguisée.

Chaque proposition porte : le message en une phrase, c'est-à-dire ce que
l'auditoire doit pouvoir redire le lendemain ; l'arc en cinq à huit temps ; les
deux ou trois points de bascule ; **ce qu'elle sacrifie** ; et pour quel public
elle marche le mieux. Deux propositions qui ne diffèrent que par l'ordre ne sont
pas contrastées : faire varier la thèse, pas la table des matières.

Soumettre par `AskUserQuestion`, avec **une option explicite « aucune de
celles-ci, voici la mienne »**. Si l'utilisateur dicte son message, reconstruire
l'arc autour sans discuter, puis signaler en une phrase ce que ce message oblige
à laisser dehors.

Comment construire des propositions réellement différentes :
`references/message_et_fil.md`.

### 3. Le budget de temps

Avant tout choix de contenu. Convertir la durée en budget :

| Type de slide | Coût |
|---|---|
| Slide de contenu, registre académique | 60 à 90 s |
| Slide de rupture, grand chiffre | 15 à 30 s |
| Figure à commenter réellement | 90 à 150 s |
| Page de section | 5 à 10 s |

Réserver 10 % pour l'entrée en matière et les aléas. Une slide d'annexe ne coûte
rien : elle ne se montre que si la question vient.

Rendre le budget explicitement : « 20 minutes, questions en plus, donc 18 min de
parole, donc 14 slides de corps dont 4 figures, 2 ruptures, 3 pages de section
et 6 annexes ». **Ce budget contraint le geste 4, jamais l'inverse.**

### 4. L'inventaire de la matière

Lister tout ce qui pourrait entrer, puis donner à chaque item un rang. Repris du
geste 6 de `narratif`, adapté à l'oral :

- **NOYAU** — sans lui la démonstration tombe. Il aura sa slide.
- **APPUI** — soutient un maillon du raisonnement. Il partage une slide.
- **MENTION** — une phrase qui garde le chiffre, sans slide propre.
- **ANNEXE** — une slide après `\appendix`, pour les questions.
- **ÉCARTÉ** — avec son motif, écrit.

La **taxe de coût irrécupérable** s'applique : trois semaines de calcul ne
gagnent pas une slide. Si le total des NOYAU dépasse le budget du geste 3, ce
n'est pas le budget qui cède : c'est le message qui est trop large, et on
retourne au geste 2.

### 5. Le recyclage

Auditer les figures et tableaux déjà produits (`article/figures/`, `résultats/`,
`figures/`, decks antérieurs du projet) selon des critères **de projection**,
plus durs que ceux d'un article. Une figure d'article est conçue pour un lecteur
à trente centimètres ; l'auditoire est à huit mètres.

Quatre verdicts par figure : **réutilisable telle quelle** (rare) ; **à
reforger** (agrandir les polices, changer le ratio pour le 16:9, élaguer les
panneaux hors sujet, annoter directement sur la figure au lieu d'une légende) ;
**à refaire** ; **inutilisable ici**. Consigner le verdict par figure dans le
registre : c'est ce qui évite de réauditer les mêmes figures au prochain exposé.

Grille détaillée et seuils : `references/inventaire_et_recyclage.md`.

### 6. Le narratif fin et le squelette

Fixer la chaîne d'arguments : les maillons que l'auditoire doit accepter l'un
après l'autre pour passer de ce qu'il croyait à ce qu'on veut lui faire admettre.
Repérer les **points de bascule**, ces endroits où une explication concurrente
meurt et où une preuve visuelle est donc due. Décider l'ordre.

Puis **émettre le squelette**, chaque section portant son allocation en
commentaire, comme le fait `narratif` pour un article :

```latex
\section{Le résultat central}
% presentation: maillon M2 | bascule B1 -> slide de preuve | budget 4 min | 4 slides
```

Un plan qui n'émet pas le squelette est décoratif, et sera contredit dès la
première slide.

### 7. La fiche par slide

Pour chaque slide, dans `plan_presentation.md` :

- **Rôle** dans l'arc, en une ligne.
- **Message** en une phrase. C'est lui qui deviendra le **titre** de la slide.
- **Informations** à porter, avec le rang des items consommés.
- **Durée visée**.
- **Modalité pressentie**, et si c'est une liste à puces, **pourquoi aucune
  forme visuelle ne convient**.

Gabarit littéral du registre : `references/gabarit_plan.md`.

### 8. L'idéation visuelle

Pour chaque slide non élémentaire, proposer **deux ou trois formes candidates
avant d'en écrire une**, et motiver le choix. Ne pas dessiner la première forme
qui vient : c'est ainsi qu'on obtient trois rectangles arrondis.

Le bestiaire, l'arbre de décision « quelle forme pour ce message » et les
patrons TikZ prêts à copier sont dans `references/ideation_visuelle.md`.
Délégations :

- **carte** : `geo-map`, obligatoire dès qu'il y a du géographique. Une carte
  schématique en TikZ ne remplace pas une carte pour discuter distribution,
  foyer ancestral ou flux.
- **graphique de données** : `sci-figure`, en demandant explicitement des tailles
  de police de projection, pas les presets de revue.
- **une slide isolée particulièrement difficile** : `slide-design`, qui propose
  des options structurelles avec références éditoriales.
- **une figure qui manque au projet entier** : `fig-ideation`, qui cherche la
  figure absente plutôt que de dessiner celle qu'on demande.

### 9. La production

Écrire le deck avec le thème maison, à l'intensité fixée au geste 1 :

```latex
\documentclass[aspectratio=169,11pt]{beamer}
\usetheme[academique]{guyeux}     % ou [affirmee]
\usepackage[french]{babel}        % ou [english]
\usepackage{graphicx}
\graphicspath{{figures/}{../../article/figures/}{../../résultats/}}
```

Copier `assets/beamerthemeguyeux.sty` dans le répertoire de la présentation :
le répertoire doit être autonome, donc portable vers Overleaf sans rien
installer. Le thème et ses macros sont documentés dans `references/theme.md`,
la grammaire des types de slide dans `references/grammaire_slides.md`.

Compiler, puis **regarder chaque slide rendue** avant de déclarer quoi que ce
soit :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/beamer-slides/scripts/deck_render.py deck.tex
```

### 10. Les deux markdowns

Écrits depuis les fiches du geste 7, pas depuis les slides : des notes dérivées
des slides ne font que les paraphraser.

**`notes_orateur.md`** — par slide : le rôle dans le narratif en une ligne, le
temps à y passer, puis le **texte à dire**, rédigé pour être parlé, et les
phrases de transition, qui sont ce qui manque le plus souvent. En français, et
**aussi en anglais si l'oral est anglais**.

**`notes_techniques.md`** — le soutien pédagogique : définition de chaque
métrique affichée et **pourquoi celle-là plutôt qu'une autre**, ce que fait
chaque outil nommé, quel test statistique et comment lire sa valeur de p, les
chiffres exacts avec leur source, les réserves, et les questions probables avec
leur réponse.

Gabarits : `references/notes_orateur.md` et `references/notes_techniques.md`.

### 11. Les contrôles

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/beamer-slides/scripts/slide_audit.py deck.tex --duree 20 --pixels
python3 ${CLAUDE_PLUGIN_ROOT}/skills/beamer-slides/scripts/slide_audit.py --pourquoi   # d'où viennent les seuils
```

Le script mesure ; il ne tranche pas. Codes : `C2`/`C3` débordement vertical et
horizontal, `T1` texte absent du PDF rendu, `D1` réduction de police, `D2`
densité, `D3` take-away trop long, `V1` TikZ décoratif, `V2` part de slides sans
objet visuel, `M1`/`M2` monotonie, `R1` rythme contre la durée, `S0` aucune frame trouvée alors
que le PDF en compte (fragment non résolu : le rapport ne vaut alors rien),
`S1` `\input` introuvable, `S2` liste des fragments réellement audités.
Le script suit les `\input`, situe chaque défaut dans son fragment
(« corps.tex:37 »), et **chaque variante s'audite avec sa propre durée**.

S'y ajoutent deux contrôles que le script ne peut pas faire :

- **fig-check par slide portant une figure** : lisibilité à la projection,
  taille des textes, correspondance entre la figure et le message annoncé.
- **claim-check des slides** : chaque chiffre et chaque affirmation affichés
  doivent être traçables à `claim_check.md`, `etat_des_decouvertes.md` ou un
  résultat sur disque. **Une slide affirme plus vite qu'un article, et personne
  ne la relit.**

Registre `slide_check.md`, au format de `fig_check.md`, horodaté, incrémental :
on ne re-vérifie que ce qui a bougé. Détail : `references/controles.md`.

### 12. La revue par auditeur simulé

Se mettre dans la peau du public déclaré au geste 1 et rendre une critique
constructive, structurée comme `manuscript-review` : MAJEUR, MODÉRÉ, MINEUR,
POINTS FORTS, RECOMMANDATIONS. Elle porte sur le fond, sur la forme **et sur le
texte à dire**. Déléguer à une instance indépendante de celle qui a rédigé le
deck : l'auteur d'une slide ne voit pas ce qu'elle ne dit pas.

Grille par public et gabarit de sortie : `references/revue_auditeur.md`.
Sortie datée dans `revue_auditeur.md`.

## Modes d'invocation

- **`/slides`** — cycle complet, les douze gestes.
- **`/slides read`** — afficher le plan courant et sa fraîcheur, sans rien modifier.
- **`/slides notes`** — régénérer les deux markdowns depuis les fiches.
- **`/slides check`** — gestes 11 seul, sur un deck existant.
- **`/slides review`** — geste 12 seul.
- **`/slides edit <deck.tex> "<demande>"`** — modification demandée d'un deck
  qu'on tient : ajouter une section, en retirer une, corriger un chiffre. Tout
  ajout **rend la monnaie** du budget, et la demande passe par une fiche de
  slide avant tout LaTeX.
- **`/slides fork <deck.tex> --duree 15`** (ou `--langue en`) — décliner le
  **même** exposé dans un autre format. Vérifier d'abord que le message ne
  change pas : si c'est le cas, ce n'est pas une variante mais un nouvel
  exposé, et il repart du geste 1. La bascule vers des fragments partagés est
  mécanique, donc outillée, et se contrôle comme une refactorisation :

  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/skills/beamer-slides/scripts/deck_fork.py deck.tex --nom court
  ```

  Le script découpe `preambule.tex` et `corps.tex`, écrit les deux maîtres,
  puis **vérifie que le PDF de référence n'a pas changé de longueur**. Reste
  ensuite le vrai travail, qui n'est pas mécanique : rejouer le budget et les
  rangs pour la nouvelle durée.
- **`/slides upgrade <deck.tex>`** — reprise d'un deck existant. Compiler, le
  regarder slide par slide, passer l'audit, **reconstruire le plan que le deck
  porte réellement**, le confronter à celui qu'il devrait porter, et **rendre le
  chantier avant d'agir**. Calque du mode `reprise` de `narratif`. Ne jamais
  réécrire un deck sans avoir montré ce qu'on va changer et pourquoi.

## Éditer et décliner

Un exposé est rarement donné une fois : il se retouche, il se raccourcit, il se
traduit. Trois demandes voisines, un seul tri, qui tient en une question — **le
message du geste 2 change-t-il ?**

- **Non, et le contenu bouge à la marge** : c'est une **édition**. Elle se paie.
  Le skill repose sur l'ordre budget puis contenu ; une demande d'ajout attaque
  cet ordre de face, et c'est ainsi qu'un deck devient trop long, non pas d'un
  coup mais par ajouts dont aucun n'a été compensé. Chiffrer l'ajout, puis
  soumettre trois issues : **compenser** en nommant ce qui sort, **allonger** en
  actant que la durée change, ou **verser en annexe** à coût nul. Et dire **à
  quel maillon** l'ajout se rattache : celui qui ne sert aucun maillon est une
  annexe, pas une section.
- **Non, mais le format change** (durée, langue) : c'est une **variante**. Elle
  ne se fabrique pas en copiant le répertoire, qui divergerait dès la première
  correction de chiffre, ni par `\includeonlyframes`, qui perd les pages de
  section et laisse une numérotation calée sur le deck complet — mesuré. Un
  maître par variante, des fragments partagés, un booléen. Et une version
  courte n'est **pas** la longue tronquée : on rejoue le budget et les rangs,
  et des slides fusionnent.
- **Oui** : ce n'est pas un fork, c'est un **nouvel exposé** qui recycle la
  matière au geste 5. Le déguiser en variante donne deux decks qui divergent en
  prétendant partager une source.

Détail des trois gestes, structure de fichiers, mécanisme mesuré et registre des
variantes : `references/edition_et_variantes.md`.

## Erreurs à éviter

- **Ajouter une slide sans rendre la monnaie du budget.**
- **Fabriquer une version courte en supprimant des slides** au lieu de rejouer
  le budget, les rangs et l'arc.
- **Écrire des slides au geste 2.** Le LaTeX arrive au geste 9, pas avant.
- **Choisir le contenu puis regarder la durée.** C'est l'ordre qui produit les
  decks à 75 frames.
- **Comprimer l'article.** Un exposé n'est pas un manuscrit court : il a un
  public, une durée et une seule thèse.
- **Mettre du texte dans des rectangles et appeler cela un schéma.** Si les
  nœuds portent des phrases et qu'il n'y a ni axe, ni échelle, ni donnée, c'est
  une liste à puces qui coûte la place d'une figure.
- **Réduire la police pour faire tenir.** Le contenu est en trop : c'est lui
  qu'on coupe. `\footnotesize` et ses voisins sont réservés aux sources et aux
  notes.
- **Réutiliser une figure d'article telle quelle.** Elle est calibrée pour la
  lecture à trente centimètres.
- **Répéter le même gabarit.** Titre, filet, contenu, encadré, vingt fois : au
  bout de dix minutes l'œil ne distingue plus rien.
- **Livrer sans avoir regardé les slides rendues.** Un débordement ressemble à
  une slide simplement courte.
- **Déclarer un chiffre qu'aucun registre ne porte.**
- **Écrire les notes depuis les slides.** Elles ne feraient que les paraphraser ;
  elles se dérivent des fiches.

## Frontière avec les skills voisins

`slide-design` conçoit une à quelques slides depuis une idée verbale ;
`beamer-slides` conçoit un exposé entier et le contrôle. `slide-polish` améliore
**une** slide existante, et c'est à lui que le geste 8 délègue une slide
difficile et le mode `upgrade` une slide à reprendre. `latex-posters` fait les
posters. `fig-ideation` cherche la figure qui manque au projet ; `sci-figure` et
`geo-map` produisent graphiques et cartes. `narratif` fait pour un article ce
que les gestes 2, 4, 6 et 7 font pour un exposé : si `plan_narratif.md` existe,
**en partir** au lieu de refaire la chaîne d'arguments. `mtbc-bilan` produit un
point d'étape interne, destiné à l'auteur ; un exposé est destiné à un public,
et sa grammaire de slides est celle d'ici.

## Références

- `references/cadrage.md` — les quatre paramètres et ce que chacun commande.
- `references/message_et_fil.md` — fabriquer des propositions réellement contrastées.
- `references/inventaire_et_recyclage.md` — rangs, et audit des figures pour la projection.
- `references/gabarit_plan.md` — format littéral de `plan_presentation.md`.
- `references/grammaire_slides.md` — les types de slide et leur emploi.
- `references/ideation_visuelle.md` — bestiaire, arbre de décision, patrons TikZ.
- `references/notes_orateur.md` — gabarit du script parlé.
- `references/notes_techniques.md` — gabarit du soutien pédagogique.
- `references/controles.md` — les contrôles, leurs seuils, leurs faux positifs connus.
- `references/revue_auditeur.md` — la revue par public.
- `references/theme.md` — le thème, ses deux intensités, ses macros.
- `references/edition_et_variantes.md` — éditer un deck existant sous contrainte
  de budget, et le décliner en versions courte, longue ou traduite.
