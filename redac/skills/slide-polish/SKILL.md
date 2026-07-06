---
name: slide-polish
description: Amélioration ciblée d'une slide Beamer existante, sur le fond et sur la forme, **avec étape obligatoire de brassage large pour reconstruire la thèse pleine du projet et éviter la moyennisation par polissage** (un défaut classique : prendre une slide moyenne et la rendre *plus belle moyenne*, en sacrifiant spécificité, nuance et voix). Reçoit en argument le titre (ou l'identifiant, ou le numéro) d'une slide dans un fichier .tex. Localise la slide et son voisinage, compile et lit visuellement les PNG par capacité multimodale, prend de la hauteur sur le fond, **reconstruit la thèse pleine en lisant largement la matière du projet (cahier de labo, manuscrit, JOURNAL, notes, claim-check), détecte les axes de perte par rapport à la thèse pleine (spécificité, contre-intuitivité, nuance) et oriente vers enrichir vers la singularité plutôt qu'alléger vers la généralité**, décide d'une modalité (TikZ, Mermaid, frise, nuage de mots-clés, filigrane, big number, carte via geo-map), cherche au besoin des informations complémentaires, applique `deai-latex` étendu (trois familles : tirets cadratin/demi-cadratin/double, rhétorique pseudo-éloquente type "pas X, j'apporte Y", cohérence manuscrit), **score chaque version sur 16 points avec veto anti-moyennisation (tout gain typographique au prix d'une perte de spécificité, chiffre, nuance ou voix est annulé)**, itère tant que le score progresse, enchaîne une boucle propreté visuelle (10 défauts physiques inspectés sur PNG haute résolution : débordements, collisions, veuves, footer poussé), **puis un test final bloquant de voix scientifique qui valide chaque phrase par la question "l'auteur l'écrirait-il en mail à un collègue ?" et bannit antithèses pompeuses, slogans creux, métaphores filées fades, et tous tirets cadratin résiduels**. Le cycle n'est pas terminé tant que la slide n'est pas propre, spécifique, et écrite en voix d'auteur. Trigger when the user types `/slide-polish`, asks to "améliore la slide X", "polish la slide qui parle de Y", "retravaille la slide n°12", "rends meilleure cette slide", "regarde la slide sur Z et propose une version améliorée", "rework slide titled '...'", or any request to upgrade a specific existing slide rather than build a new one or generate a whole deck.
user_invocable: true
invocation: /slide-polish
argument-hint: "<titre ou numéro de la slide> [chemin/vers/main.tex]"
---

# Slide Polish — Améliorer une slide Beamer existante

Ce skill agit sur **une slide déjà écrite**. Il ne crée pas (c'est `slide-design`), il ne génère pas un deck entier (c'est `beamer-slides`). Il prend une frame existante, la regarde à l'œil et à la tête, décide quoi en faire, et la livre remaniée.

L'amélioration porte **autant sur le fond que sur la forme**. Une slide visuellement propre mais qui ne pose pas d'argument reste à retravailler. Une slide à l'argument net mais visuellement encombrée reste à retravailler.

## Quand l'invoquer

- L'utilisateur tape `/slide-polish "Titre de la slide"` ou `/slide-polish 12`.
- L'utilisateur dit « cette slide est moyenne, regarde si tu peux la rendre mieux ».
- L'utilisateur vient de relire son deck et identifie 1 à 3 slides à reprendre.
- L'utilisateur prépare un oral et veut élever quelques slides clés sans toucher au reste du deck.

**Ne pas invoquer si** :
- La slide n'existe pas encore (utiliser `slide-design`).
- Le deck entier est à reprendre (utiliser `beamer-slides` ou enchaîner plusieurs appels à `slide-polish`).
- Il s'agit d'un PowerPoint/Keynote (déléguer au skill `pptx`, qui a ses propres outils).

## Philosophie

1. **Une slide ne se juge pas seule** : sa qualité dépend de son voisinage. Lue après quoi ? avant quoi ? Si l'idée a déjà été énoncée à la slide n-1, le polish consiste à l'alléger ou à la faire pivoter. Si l'idée surprend à la slide n+1, il faut l'introduire mieux ici.
2. **L'œil avant le code** : on regarde le PNG compilé avant de toucher le `.tex`. Ce qui paraît correct dans le code peut paraître chargé à l'écran, et vice-versa.
3. **Modalité avant texte** : avant d'éditer les mots, se demander si la slide ne devrait pas être un schéma, une frise, une carte, un big number. Changer de modalité fait souvent plus de bien que polir une liste de puces.
4. **Pas de fioriture vide** : ajouter une illustration de fond ne se justifie que si elle *ancre* le propos. Un watermark décoratif sans rapport dégrade la slide.
5. **Le ton scientifique se gagne** : il s'obtient par sobriété typographique, prudence des affirmations, absence d'emphase ornementale. Le passage `/deai-latex` n'est pas un luxe, c'est la dernière étape obligatoire.
6. **Préserver le style hôte** : la slide remaniée doit s'insérer sans rupture dans le deck. Mêmes macros, mêmes couleurs, mêmes proportions.

## Processus

Sept phases avec une étape d'élargissement obligatoire après le diagnostic : **Localiser → Inspecter → Diagnostiquer → *Brasser large (Phase 3bis)* → Décider → Enrichir → Réécrire → Vérifier (trois boucles : qualité éditoriale, propreté visuelle, voix scientifique)**. Aucune phase ne doit être sautée, même si l'utilisateur a demandé à ne pas être interrompu : ce sont des étapes de production, pas des questions.

La **Phase 3bis** est la garantie anti-moyennisation : avant toute décision de modalité, reconstruire la *thèse pleine* du projet sur ce point et vérifier que la slide actuelle ne l'a pas rabotée. Cette étape est *fondamentale*, elle commande tout ce qui suit. Sans elle, le polish risque de polir un fond appauvri en *plus belle moyenne*.

La Phase 7 enchaîne **trois boucles distinctes et toutes bloquantes** :

- **§7.4 — Boucle qualité** : score sur 16, itère tant que ça monte (plafond 16/16, convergence < 2 pts, régression bloquée, limite dure 5 itérations). **Veto anti-moyennisation** : tout gain typographique obtenu au prix d'une perte de spécificité, de chiffre précis, de nuance ou de voix est annulé d'office.
- **§7.5 — Boucle propreté** : score binaire pass/fail sur 10 défauts physiques (texte qui sort de la slide, texte qui dépasse d'un node TikZ, collisions, image qui déborde, hors-champ, veuves, footer poussé, filigrane qui mord, crédit écrasé, saut de titre malheureux). Itère **jusqu'à zéro défaut**. Limite dure 5 itérations, signalement explicite si défauts résiduels.
- **§7.5bis — Test de voix scientifique** : pour chaque phrase de la slide, vérifier qu'elle pourrait être écrite par l'auteur dans un mail à un collègue. Bloque toute antithèse pompeuse type *« je n'apporte pas X, j'apporte Y »*, tout slogan creux, tout tiret cadratin / demi-cadratin / double tiret encore présent. **Aucune slide ne sort sans validation §7.5bis.**

**Le cycle n'est pas terminé tant que la slide n'est pas propre *et* écrite en voix scientifique.** Une slide à 16/16 en qualité, 10 NON en propreté, mais 1 antithèse pompeuse à §7.5bis, n'est pas livrable.

### Phase 1 — Localiser la slide et son voisinage

1. **Identifier le fichier** :
   - Si un chemin est passé en argument, l'utiliser.
   - Sinon, chercher `main.tex` puis `presentation.tex` puis `*.tex` dans le répertoire courant. Si plusieurs candidats : demander.
2. **Identifier la frame cible** par ordre de priorité :
   - Match exact sur le titre passé en argument (`\begin{frame}{<titre>}`).
   - Match insensible à la casse et aux accents.
   - Match partiel (sous-chaîne).
   - Numéro de slide (compter les `\begin{frame}` en partant du début, en tenant compte des `\section` et `\subsection` qui peuvent insérer des frames).
   - Si plusieurs matches : lister à l'utilisateur, demander.
3. **Capturer le voisinage** :
   - Frame n-1 : la `\begin{frame}` immédiatement précédente (qu'elle soit dans la même section ou non). S'il n'y en a pas (première frame), le noter.
   - Frame n+1 : idem, suivante.
   - **Section et sous-section courantes** : remonter jusqu'au dernier `\section{...}` / `\subsection{...}`.
   - **Plan global** : extraire la table des sections du deck pour situer la slide dans le récit.
4. **Lire le préambule** :
   - Thème Beamer, palette (`\definecolor`), polices (`fontspec`), `\graphicspath`, macros maison (`\kb`, `\alert`, etc.), `aspectratio`.
   - Bibliothèques TikZ déjà chargées.
   - Pour ne **rien réinventer** : si une macro maison existe pour les keybox, l'utiliser.

### Phase 2 — Inspecter visuellement (multimodal)

1. **Compiler le deck complet** une première fois (sans modification) dans un dossier temporaire :

```bash
cp -r <projet>/. /tmp/slide-polish-<id>/
cd /tmp/slide-polish-<id>
latexmk -xelatex -interaction=nonstopmode <main>.tex >/dev/null 2>&1 \
  || latexmk -pdflatex -interaction=nonstopmode <main>.tex >/dev/null 2>&1
```

Si la compilation échoue, **ne pas poursuivre** : signaler à l'utilisateur l'erreur exacte, proposer de la corriger d'abord. Une slide à polir doit pouvoir être lue à l'écran.

2. **Extraire les trois pages en PNG haute résolution** :

```bash
pdftoppm -r 180 -f $((N-1)) -l $((N+1)) <main>.pdf trio -png
# produit trio-1.png (n-1), trio-2.png (n), trio-3.png (n+1)
```

3. **Lire les trois PNG** avec l'outil `Read` (capacité multimodale) et **décrire ce que l'œil voit** pour chacune des trois slides, en distinguant :
   - **Densité** : surcharge / juste / vide.
   - **Point focal** : présent et clair / dilué / absent.
   - **Hiérarchie typographique** : trois niveaux discernables / écrasée / inversée.
   - **Palette** : respectée / cassée / inexistante.
   - **Illustration** : présente et signifiante / présente et décorative / absente alors qu'elle aurait pu aider.
   - **Sensation générale** : éditoriale / fonctionnelle / amateur.

Restituer cette lecture en prose courte à l'utilisateur. C'est le diagnostic visuel partagé.

### Phase 3 — Diagnostiquer le fond

Quatre questions de hauteur :

1. **Le titre porte-t-il l'argument ?** Un titre comme « Résultats » ou « Discussion » est un drapeau rouge. Le titre doit énoncer ce que la slide démontre. Si le titre est seulement catégoriel, c'est la première chose à reprendre.
2. **Quel est le rôle narratif de cette slide dans le voisinage ?**
   - *Préparer* la suivante (poser une question, planter le décor) ?
   - *Démontrer* (porter une donnée, un résultat) ?
   - *Récapituler* (synthèse à mi-parcours) ?
   - *Transitionner* (charnière entre deux idées) ?
   - *Lever une objection* anticipée ?
   - Si la slide ne sait pas quel rôle elle joue, c'est qu'elle est inutile ou mal placée — en parler à l'utilisateur.
3. **Redondance ou orphelinat ?**
   - Y a-t-il chevauchement substantiel avec n-1 ou n+1 (idée déjà dite, donnée déjà montrée) ? Alléger ou fusionner.
   - À l'inverse, la slide est-elle un saut narratif (n-1 parle d'autre chose, n+1 aussi) ? Soit la déplacer, soit la rattacher (transition explicite, ou enrichissement).
4. **L'information est-elle sourcée ?**
   - Chiffres, dates, citations : si la slide les affirme sans qu'on puisse les retrouver dans le projet, déclencher `claim-check`.
   - Si un chiffre semble incertain : déclencher `WebSearch` ou `lit-review` ciblé.

### Phase 3bis — Brasser large sur le fond (anti-moyennisation)

**Phase fondamentale, jamais sautée.** Avant de décider d'une modalité (Phase 4), poser la question qui décide de toute la suite : *la slide actuelle dit-elle le maximum de ce qu'elle pourrait dire, ou est-elle un sous-produit moyennisé d'une thèse plus riche ?*

L'erreur la plus dangereuse d'un polish est de prendre une slide moyenne et de la rendre *plus belle moyenne*. Le résultat lit bien, est typographiquement propre, le score §7.4 grimpe, mais la slide a perdu en singularité. C'est le contraire du but : le polish doit servir l'argument, pas le lisser.

#### 3bis.1 — Reconstruire la thèse pleine

Sortir de la slide. Lire **largement** la matière du projet pour reconstruire ce que l'auteur pourrait dire de plus pointu sur ce point :

- `cahier_de_labo.md` — entrées datées récentes liées au sujet de la slide. C'est là que la pensée encore vive est consignée, pas dans le manuscrit final.
- Section du manuscrit `.tex` correspondante — souvent plus riche en nuances que ce que la slide retient.
- Notes / drafts dans le projet (`notes/`, `drafts/`, `brouillons/`, fichiers `.md` éparpillés).
- `JOURNAL.md` si présent — décisions techniques argumentées récemment.
- `reviewer-response/` et `claim-check.md` — formulations déjà arbitrées avec des relecteurs ou avec soi-même.
- Commentaires Git récents sur les figures de la slide.

Synthétiser en **5 à 10 phrases la thèse pleine** : ce que l'auteur sait et pense vraiment de ce point précis, au-delà de ce que la slide retient.

#### 3bis.2 — Comparer slide actuelle vs thèse pleine

Trois axes de perte à inspecter :

1. **Spécificité perdue** : la slide utilise-t-elle des termes plus généraux que la thèse pleine ? « diversité » au lieu de « divergence intra-lignée à 0,8 %/site/Ma », « stratégie » au lieu de « tip-dating BEAST avec horloge log-normale », « beaucoup de cas » au lieu de « 4 200 isolats sur 18 régions sanitaires »). Si oui : *appauvrissement à corriger*.
2. **Contre-intuitivité perdue** : la thèse pleine contient-elle une affirmation qui *surprend*, contredit une vue reçue, identifie une exception ? La slide en a-t-elle hérité, ou est-elle revenue à un constat banal ?
3. **Nuance perdue** : la thèse pleine prend-elle des précautions, signale-t-elle une limite, une zone d'incertitude ? La slide les évoque-t-elle, ou affirme-t-elle sans condition ?

Si **au moins une** est perdue, le polish doit *enrichir vers la singularité*, pas *alléger vers la généralité*.

#### 3bis.3 — Inverser le réflexe d'allègement

Conséquence souvent négligée : la décision Phase 4 peut être **« enrichir »** alors que la slide paraît déjà chargée. Une slide qui a 5 puces banales n'est pas trop pleine, elle est mal remplie. La remplacer par une seule phrase contre-intuitive précise est un enrichissement *du fond*, pas un allègement.

Inversement, une slide minimaliste à 20 mots peut être un appauvrissement déguisé en élégance, si elle a sacrifié la spécificité au compte de mots. **Le minimalisme typographique ne rachète pas un fond pauvre.**

#### 3bis.4 — Test de moyennisation

Avant de passer à la Phase 4, lire la slide actuelle et appliquer trois questions :

- *Cette phrase pourrait-elle être dite par n'importe qui travaillant dans le même champ ?* — si oui, signe de moyennisation.
- *Y a-t-il un seul mot, un seul chiffre, qui ne pourrait pas figurer dans un slide générique sur le même thème ?* — si non, signe de moyennisation.
- *L'auteur, en privé avec un collègue, dirait-il cela ainsi, ou dirait-il quelque chose de plus pointu, de plus risqué, de plus personnel ?* — si plus pointu en privé, signe de moyennisation.

Si moyennisation détectée, **la première mission du polish est de remonter le niveau de spécificité**, pas de ranger les puces.

#### 3bis.5 — Restitution à l'utilisateur

Avant la décision Phase 4, exposer en quelques lignes :

- La thèse pleine reconstituée (5 à 10 phrases).
- Les axes de perte constatés (spécificité, contre-intuitivité, nuance).
- L'orientation suggérée : *enrichir vers la singularité* ou *poursuivre vers l'élégance* (rare).

L'utilisateur peut alors rediriger si la thèse pleine reconstruite est inexacte ou si la perte constatée est en fait volontaire (auditoire grand public, ancrage différent du manuscrit, etc.).

### Phase 4 — Décider de la modalité

C'est le cœur du skill. **Toujours envisager quatre directions** avant de choisir, et expliciter le choix.

#### 4.1 — Alléger

Indicateurs : densité « surcharge » au diagnostic visuel, plus de 60 mots visibles hors titre, deux idées dans une slide, trois colonnes de puces.

Geste : **retirer** au moins 30 % du texte ; convertir les puces en une seule phrase clé + une visualisation ; remplacer 5 puces par 1 keybox.

#### 4.2 — Enrichir

Indicateurs : densité « vide », slide à 12 mots, titre qui annonce mais corps qui ne montre rien, slide qui s'arrête juste avant le moment intéressant.

Geste : ajouter une donnée (figure, chiffre), une citation, un schéma. Si la matière manque : Phase 5 (recherche complémentaire).

#### 4.3 — Changer de modalité

C'est souvent l'amélioration la plus forte. Six modalités à considérer :

| Modalité | Quand l'utiliser | Outil |
|----------|-----------------|-------|
| **Schéma TikZ** | Workflow, mécanisme, architecture, structure spatiale | Patrons de `slide-design §5.2` |
| **Diagramme Mermaid** | Séquence, flowchart, dépendances logiques | `\usepackage{mermaid}` ou export PNG préalable |
| **Frise chronologique** | Histoire, évolution, succession datée | Patron timeline de `slide-design §5.2` |
| **Nuage de mots-clés** | Champ lexical, diversité d'un concept, profusion | TikZ `tikzpeople`/`wordcloud2` (générer PNG, inclure) |
| **Carte** | Toute géographie réelle | **Toujours `geo-map`**, jamais à la main |
| **Big number / pull quote** | Un chiffre, une citation, un effet rhétorique | Patrons big number et pull quote de `slide-design §5.2` |
| **Image plein fond en filigrane** | Slide narrative / transition / question rhétorique | Voir Phase 6 |

**Règle** : changer de modalité doit *renforcer* l'argument, pas l'orner. Si le passage de « 5 puces » à « schéma de flux » ne change ni la mémorisation ni la clarté, ne pas changer.

#### 4.4 — Statu quo + polissage cosmétique

Possible si la slide est déjà bonne : seulement alignement, espacement, ajustement de palette, recadrage du titre. Annoncer honnêtement à l'utilisateur que la slide est déjà solide.

#### 4.5 — Document la décision

Avant de réécrire, énoncer en deux phrases :
- Quelle modalité a été retenue, et pourquoi (en référence au diagnostic).
- Quelle modalité a été écartée, et pourquoi.

L'utilisateur peut alors arbitrer avant qu'on parte.

### Phase 5 — Enrichir si besoin (recherche complémentaire)

Si le diagnostic révèle un manque de matière (Phase 4.2 / Phase 4.3) :

1. **Information locale d'abord** :
   - Lire le `cahier_de_labo.md`, le `JOURNAL.md`, l'article LaTeX en cours, les CSV de résultats. La matière est souvent déjà dans le projet, juste pas portée à la slide.
2. **Recherche externe** *seulement si* la matière n'existe pas localement :
   - `WebSearch` pour un chiffre récent (épidémiologie OMS, statistique INSEE, etc.).
   - `WebFetch` pour récupérer une page identifiée.
   - Skill `lit-review` pour un point de littérature ciblé (1 à 3 références).
   - Skill `claim-check` si un chiffre déjà affiché doit être vérifié.
3. **Toujours sourcer** : tout chiffre nouveau apporté à la slide doit avoir une source affichée en pied (police 8-9 pt). « OMS Global TB Report 2024 », « INSEE 2023 », « Smith et al., Nature 2022 ».
4. **Refuser le chiffre non sourçable** : si la recherche ne trouve pas de source fiable, ne pas afficher le chiffre.

### Phase 6 — Réécrire la slide

#### 6.1 — Préserver le contexte technique

- Conserver les macros maison (`\kb`, `\alert`, etc.) déjà utilisées dans le deck.
- Conserver la palette (`\definecolor` du préambule). Ne pas redéfinir.
- Conserver l'`aspectratio` du deck.
- Si une bibliothèque TikZ supplémentaire est nécessaire, **signaler à l'utilisateur** le `\usetikzlibrary{...}` à ajouter au préambule.

#### 6.2 — Illustration de fond en filigrane (si pertinent)

Pattern Beamer pour fond watermark, utilisable seulement quand :
- Le slide est une transition / question rhétorique / point « contexte ».
- L'image **ancre sémantiquement** le propos (carte du pays dont on parle, silhouette de bactérie, micrographie de poumon pour un slide TB, etc.).
- L'image est **libre de droit** (Wikimedia Commons, domaine public, CC-BY avec attribution).

Code :

```latex
\begin{frame}{Titre informatif}
\begin{tikzpicture}[remember picture,overlay]
  \node[opacity=0.12,anchor=center] at (current page.center)
    {\includegraphics[width=\paperwidth,height=\paperheight,
                       keepaspectratio]{figures/silhouette_continent.pdf}};
\end{tikzpicture}
% contenu normal de la slide ici, lisible par-dessus le filigrane
\textbf{Idée clé.} Texte de premier plan, contraste suffisant.
\par\medskip
\kb{Phrase clé.}
\par\vfill
{\tiny Fond : Wikimedia Commons, domaine public.}
\end{frame}
```

Niveau d'opacité : 0.10 à 0.18 sur fond clair, 0.20 à 0.30 sur fond foncé. **Tester l'opacité après compilation** : si le texte de premier plan devient illisible, baisser l'opacité.

Ne **jamais** mettre un fond watermark sur une slide qui contient une figure scientifique (deux niveaux de lecture concurrents → confusion).

#### 6.3 — Schémas par délégation

- **Mermaid** : produire le code Mermaid, le rendre en PNG (via `mmdc` si disponible, ou demander à l'utilisateur), puis inclure le PNG dans la frame. Ne pas tenter de rendre du Mermaid natif dans Beamer.
- **TikZ** : écrire directement dans la frame, en suivant les patrons §6.3bis ci-dessous. **Ne pas réinventer**, surtout pas avec coordonnées absolues à la main.
- **Carte** : appel à `geo-map` en sous-agent. Produire un PDF, l'inclure.
- **Nouvelle figure de données** : appel à `create-viz` / `seaborn` / `matplotlib-pro`. Produire un PDF, l'inclure.

#### 6.3bis — Patrons TikZ canoniques pour schémas conceptuels Beamer

C'est ici que la slide passe d'« amateur » à « chercheur habile ». **Anti-pattern récurrent à éliminer impérativement** :

```latex
% ANTIPATTERN — NE JAMAIS FAIRE
\begin{tikzpicture}[x=1cm, y=0.7cm]
  \draw[fill=cream, draw=terracotta, rounded corners] (-5.5, 1.5) rectangle (-1.7, 2.5);
  \node[font=\scriptsize] at (-3.6, 2.0) {Génome humain\\ diploïde, recombinaison, lent};
  \draw[fill=...] (0.6, 0.7) rectangle (4.6, 1.7);
  \node[...] at (2.6, 1.2) {Génome pathogène...};
  ...
  \draw[->] (-3.6, 1.5) -- (-1.2, 0.7);
\end{tikzpicture}
```

Pourquoi c'est un antipattern :
- Coordonnées **absolues**, fragiles à la moindre modification de texte
- Texte placé **manuellement** au centre estimé du rectangle → débordements quand le texte s'allonge
- Pas de `text width` → pas de wrap, le texte sort sans avertissement
- Maintenance impossible : ajouter un mot recasse le layout
- Trahit immédiatement l'amateur Beamer

**Patron canonique à utiliser à la place** :

```latex
\usetikzlibrary{positioning, arrows.meta, shapes.geometric}
% À ajouter dans le préambule si absent. Vérifier avant.

\begin{tikzpicture}[
    every node/.style={font=\scriptsize, align=center},
    concept/.style={
      draw,                       % cadre dessiné
      rounded corners=3pt,
      thick,                      % épaisseur lisible (équiv. ~0.6-0.8pt)
      inner sep=8pt,              % padding interne — protège du débordement
      text width=3.8cm,           % LARGEUR FIXÉE → wrap automatique
      align=center,
      minimum height=1.0cm,
      font=\scriptsize
    },
    arrow/.style={
      -Latex,                     % pointe propre
      thick,
      shorten >=2pt,              % la pointe s'arrête 2pt avant la cible (évite la pénétration stealth)
      shorten <=2pt
    }
]
  \node[concept, fill=cream, draw=terracotta] (host)
    {\textbf{Génome humain}\\[2pt] {\tiny diploïde · recombinaison · neutre · lent}};
  \node[concept, fill=cream, draw=darkforest, right=2.5cm of host] (path)
    {\textbf{Génome pathogène}\\[2pt] {\tiny haploïde clonal · sélection · rapide}};
  \node[concept, fill=sage!25, draw=sage!60!darkforest,
        below=1.3cm of $(host)!0.5!(path)$, text width=4.5cm] (event)
    {\textbf{Même événement humain}\\[2pt] {\tiny\itshape admixture · crise · migration}};

  \draw[arrow, color=terracotta!85] (host.south) -- (event.north west);
  \draw[arrow, color=darkforest!85] (path.south) -- (event.north east);
\end{tikzpicture}
```

Pourquoi ça marche :
- `text width=3.8cm` : le texte se *wrappe* automatiquement, pas de débordement
- `inner sep=8pt` : padding qui sépare le texte du cadre, lisibilité garantie
- `right=2.5cm of host` : positionnement *relatif* — modifier un node ne casse rien
- `(host.south) -- (event.north west)` : les flèches partent du **bord exact** du node, pas d'une coordonnée numérique estimée
- `shorten >=2pt` : la pointe `-Latex` s'arrête proprement, jamais de pénétration
- `below=1.3cm of $(host)!0.5!(path)$` : positionnement à mi-chemin entre les deux nodes du haut (nécessite la library `calc`, à ajouter si absente)

**Bibliothèques TikZ à charger systématiquement pour des schémas conceptuels Beamer** :

```latex
\usetikzlibrary{positioning}        % above of, below of, right of, etc.
\usetikzlibrary{arrows.meta}        % pointes Latex, Stealth, Triangle
\usetikzlibrary{shapes.geometric}   % ellipse, diamond, trapezium
\usetikzlibrary{calc}               % $(a)!0.5!(b)$ pour milieu
\usetikzlibrary{fit}                % englober plusieurs nodes
\usetikzlibrary{backgrounds}        % couches d'arrière-plan
```

Si l'une manque dans le préambule, **signaler à l'utilisateur** la `\usetikzlibrary{...}` à ajouter (ne pas l'insérer sans confirmation, le préambule appartient à l'utilisateur).

**Diagnostic du débordement texte / node TikZ** :

Avant compilation, vérifier dans le code :
- [ ] Chaque `\node[...]` qui contient du texte sur plusieurs lignes a `text width=...` défini
- [ ] `inner sep` est défini (typiquement 5-10pt), sinon le texte touche le cadre
- [ ] `align=center` (ou `left`, `right`) explicite pour multi-lignes
- [ ] **Pas de `\draw rectangle` suivi d'un `\node` séparé** : antipattern, fusionner en un seul `\node[draw]{texte}`

Si on hérite d'un schéma avec coordonnées absolues, la réécriture en patron canonique est **systématique**, pas optionnelle. C'est ce que fait un chercheur habile en Beamer.

**Patrons spécialisés selon le type de schéma** :

| Type de schéma | Library | Squelette |
|----------------|---------|-----------|
| Workflow horizontal | `positioning, arrows.meta` | nodes `right=of` chaînés |
| Triangle / V inversé | `positioning, calc` | 2 nodes en haut + 1 en bas via `$(a)!0.5!(b)$` |
| Concept map | `positioning, arrows.meta, fit` | nodes + flèches étiquetées + `fit` pour regrouper |
| Timeline | `positioning, arrows.meta, decorations.markings` | ligne base + nodes datés |
| Venn 2 cercles | `shapes.geometric` | 2 `ellipse, opacity=0.4` superposées |
| Pipeline | `positioning, arrows.meta` | nodes `chain=going right` |
| Hiérarchie / arbre | `trees` | `child` declarations |

Pour chacun, utiliser des `style` réutilisables (`concept`, `arrow`, etc.) déclarés dans `[every node/.style={...}]` du `\begin{tikzpicture}` ou dans le préambule via `\tikzset{...}`.

#### 6.4 — Réécriture du texte

- Titre informatif (énonce l'argument).
- Corps : moins de 40 mots visibles hors titre dans 90 % des cas.
- Trois grandeurs typographiques maximum.
- Hiérarchie : un point focal unique.
- Sources en pied si données externes.

### Phase 7 — Vérifier (deai, compilation, critique visuelle)

#### 7.1 — Passage `deai-latex` étendu (trois familles de défauts)

**Étape obligatoire.** Une fois la frame réécrite, appliquer le skill `deai-latex` *ciblé sur le fragment*, **complété par les vérifications ci-dessous** qui dépassent le périmètre du skill externe. Le passage automatique seul ne suffit pas : il rate la rhétorique pseudo-éloquente, qui est le marqueur IA le plus dégradant pour la qualité ressentie.

##### Famille 1 — Marqueurs typographiques

Bannir **tous les types de tirets non-trait-d'union** :
- `—` (tiret cadratin, em-dash, U+2014).
- `–` (tiret demi-cadratin, en-dash, U+2013).
- `--` (double tiret bas, qui se transforme en en-dash à la compilation).
- `---` (triple tiret, qui se transforme en em-dash).

Remplacement systématique : virgule, parenthèses, deux-points, ou reformulation. **Recherche obligatoire dans le code source par `grep -E '—|–|---?'`** sur le fragment final. Si une seule occurrence persiste, la slide n'est pas livrable.

Autres marqueurs typographiques :
- Pas de gras décoratif (`\textbf{...}` uniquement pour : nom propre première occurrence, terme défini, valeur clé numérique).
- Italique seulement pour les noms d'espèce (`\emph{Mycobacterium tuberculosis}`) et les emphases nécessaires.
- Pas de listes à puces systématique : si la prose porte le propos, prose.
- Acronymes définis à la première occurrence dans le deck (chercher en amont).

##### Famille 2 — Rhétorique pseudo-éloquente (le marqueur IA le plus dégradant)

C'est ici que le polish bascule en *plaquette commerciale*. Bannir absolument les patterns suivants, qui sont la signature la plus reconnaissable d'un texte produit par IA :

| Pattern | Exemple à rejeter | Pourquoi |
|---------|-------------------|----------|
| **Antithèse binaire pompeuse** | « Je n'apporte pas une transposition d'outils, j'apporte une seconde fenêtre observationnelle. » | Aucun scientifique n'écrit cela. C'est une construction publicitaire « pas X, mais Y » qui suggère une distinction creuse |
| **Slogan creux** | « Une nouvelle fenêtre observationnelle », « Une approche unique », « Une révolution silencieuse » | Métaphore filée sans contenu vérifiable |
| **Chiasme vide** | « Comprendre pour transformer, transformer pour comprendre » | Le retournement masque l'absence d'argument |
| **Parallélisme triadique mécanique** | « Précision, rigueur, ouverture » | Trois mots de longueur équivalente, sans nécessité |
| **Anaphore publicitaire** | Trois phrases consécutives commençant par le même mot | Marqueur de rhétorique scolaire |
| **Métaphore filée fade** | « Explorer le paysage », « franchir un cap », « ouvrir une voie », « repousser les frontières » | Verbes-images interchangeables sur tout sujet |
| **Hyperbole creuse** | « Révolutionnaire », « inédit », « sans précédent », « unique au monde » | Dévaluation du fond |
| **Verbes passe-partout** | « Met en lumière », « interroge », « explore », « questionne », « éclaire » | Quand le verbe précis serait « démontre », « réfute », « mesure », « identifie », « infère » |
| **Connecteurs IA** | « Par ailleurs », « En outre », « Il convient de noter », « Il est intéressant de souligner », « Comme nous l'avons vu » | Marqueurs de transition mécanique |
| **Conclusion-bilan IA** | « En définitive », « Au final », « Ainsi donc » suivis d'une généralité | Verrou rhétorique creux |

**Test pratique, à appliquer à chaque phrase de la slide finale** :

> *L'auteur, dans un mail informel à un collègue, écrirait-il cette phrase ?*

Si la réponse est **non**, réécrire dans la voix de l'auteur (ce que dirait le `cahier_de_labo.md` ou le manuscrit, pas ce qu'écrirait une plaquette) **ou supprimer**.

**Exemple de réécriture** :

| Avant (rhétorique IA) | Après (voix scientifique) |
|----------------------|---------------------------|
| « Je n'apporte pas une transposition d'outils, j'apporte une seconde fenêtre observationnelle. » | « En croisant la généalogie SNP et la datation BEAST, j'obtiens des âges de divergence absolus, là où la phylogénie seule ne donne que des âges relatifs. » |
| « Cette étude met en lumière la complexité du phénomène. » | « Sur 412 isolats, 73 % portent rpoB-S450L ; le reste se répartit entre rpoB-D435V et trois mutations rares. » |
| « Une approche unique pour comprendre la résistance. » | « Tip-dating BEAST avec horloge log-normale, n=412, 18 régions sanitaires. » |

##### Famille 3 — Cohérence avec le manuscrit et le projet

- Pas de néologisme inventé pour la slide : cohérence terminologique avec l'article principal.
- Pas de chiffres approximatifs si le manuscrit a le chiffre précis.
- Pas de tournure plus emphatique sur la slide que dans le manuscrit (la slide accompagne, elle ne survend pas).
- Si le `cahier_de_labo.md` consigne une nuance ou une précaution sur ce point, elle doit apparaître ou être respectée.

Si `deai-latex` n'est pas exécutable sur un fragment, appliquer manuellement les trois familles ci-dessus. C'est plus long mais c'est ce qui distingue une slide *qui pourrait passer pour humaine* d'une slide *qui sonne IA dès la première lecture*.

#### 7.2 — Recompilation et capture

Recompiler le deck modifié et extraire la nouvelle slide en PNG :

```bash
latexmk -xelatex -interaction=nonstopmode <main>.tex >/dev/null
pdftoppm -r 180 -f $N -l $N <main>.pdf nouvelle -png
```

#### 7.3 — Critique visuelle scorée (grille sur 16 points)

Lire les deux PNG (avant : `trio-2.png`, après : `nouvelle-1.png`) et **scorer** chaque version. C'est le score qui pilote la boucle d'amélioration (§7.4), donc il doit être fait honnêtement, pas pour valider une version qu'on aurait envie de garder.

**Points binaires (10 × 1 pt = 10 pts)** : 1 si validé, 0 sinon.

1. Point focal unique, atteint en moins d'une seconde.
2. Titre informatif (énonce l'argument, pas une catégorie).
3. Hiérarchie typographique : trois grandeurs discernables, contraste net.
4. Densité raisonnable (< 3 zones d'information par cm²).
5. Alignement sur la grille 12 colonnes.
6. Palette respectée, ratio chromatique 60/30/10 tenu.
7. Contraste de lecture WCAG AA (notamment si filigrane).
8. Crédit visible pour toute image / source externe.
9. Pas de marqueur IA (gras gratuit, em-dash, listes mécaniques, clichés).
10. Cohérence avec n-1 et n+1 vérifiée : pas de redondance, pas de saut narratif.

**Points qualitatifs (2 × 3 pts = 6 pts)** : note de 0 à 3.

11. **Impression éditoriale** — *0 amateur, 1 fonctionnel, 2 soigné, 3 éditorial publiable.*
12. **Force argumentative** — *0 ne pose pas d'argument, 1 annonce, 2 démontre, 3 démontre et ancre dans le voisinage narratif.*

**Total sur 16.** Une slide à 16/16 est considérée comme publiable et clôt la boucle.

Sauvegarder le score dans `iterations/v<k>.score` au format :

```
v1 — 11/16
  1. Focal     [OK]
  2. Titre     [OK]
  3. Hiérarchie [--]   <- point le plus faible
  ...
  11. Édito    [2/3]
  12. Argument [3/3]
```

#### 7.4 — Boucle d'amélioration itérative (tant que ça monte)

C'est l'étape qui transforme un polish en un vrai travail d'édition. **Itérer tant que le score progresse strictement.** Le critère d'arrêt est mécanique, pas subjectif.

**Mécanique** :

1. **v0 = original**. Scorer (`iterations/v0.score`). Sauvegarder `v0.tex`, `v0.png`.
2. **v1 = première révision** issue de la Phase 6 + §7.1-7.3. Si `score(v1) ≤ score(v0)` : **restaurer v0**, signaler honnêtement à l'utilisateur que la première révision n'a pas amélioré la slide, et s'arrêter là. (Cela peut arriver : la slide d'origine était déjà bonne.)
3. **Tant que** toutes les conditions ci-dessous sont vraies, **itérer** :
   - `score(vk) < 16`, ET
   - nombre d'itérations cumulées `< 5` (limite dure), ET
   - dernière itération a apporté `≥ 2 points` (sinon convergence atteinte).
4. **À chaque nouvelle itération `vk → vk+1`** :
   - Identifier le **point le plus faible** de `vk` dans le score (le premier des 12 items à valeur la plus basse).
   - Proposer une modification **ciblée sur ce seul point**, sans toucher au reste. Exemple : si l'impression éditoriale est à 1/3 alors que tout le reste est à 1, retravailler typographie, espacement, palette — pas le titre, pas l'argument.
   - Compiler, extraire PNG, scorer `vk+1`.
   - **Si `score(vk+1) > score(vk)`** : garder, sauvegarder `vk+1.tex`, `vk+1.png`, `vk+1.score`, continuer.
   - **Si `score(vk+1) ≤ score(vk)`** : restaurer `vk`, *changer de cible* (point faible suivant dans le classement) et retenter. Après **3 tentatives consécutives ratées**, considérer que `vk` est le plateau atteint, arrêter.

5. **Quatre conditions d'arrêt** :
   - **Plafond** : `score(vk) = 16/16` → livrer `vk`.
   - **Convergence** : dernière progression `< 2 points` → livrer `vk`.
   - **Régression bloquée** : 3 tentatives consécutives ratées → livrer `vk`.
   - **Limite dure** : `k = 5` itérations cumulées → livrer `vk`. Au-delà, l'*over-polishing* prend le pas sur l'amélioration réelle.

6. **Historisation** : pour chaque version retenue, dans `/tmp/slide-polish-<id>/iterations/` :

```
iterations/
├── v0.tex   v0.png   v0.score
├── v1.tex   v1.png   v1.score
├── v2.tex   v2.png   v2.score
├── ...
└── scores.md     # tableau consolidé des scores et deltas
```

Format de `scores.md` :

```
| Version | Score | Δ    | Cible de l'itération        | Décision     |
|---------|-------|------|------------------------------|--------------|
| v0      | 8/16  | —    | (état initial)               | baseline     |
| v1      | 11/16 | +3   | refonte modalité (big number)| retenu       |
| v2      | 13/16 | +2   | hiérarchie typographique     | retenu       |
| v3      | 13/16 | 0    | filigrane carte              | écarté       |
| v3'     | 14/16 | +1   | impression éditoriale (typo) | retenu, conv |
```

**Garde-fous opérationnels** :

- **Veto anti-moyennisation (priorité absolue)** : avant de valider que `score(vk+1) > score(vk)`, vérifier que vk+1 **n'a pas perdu en spécificité sémantique** par rapport à vk. Quatre régressions de fond annulent automatiquement le gain typographique :
  1. Termes techniques précis substitués par des termes plus généraux (« divergence intra-lignée » → « diversité »).
  2. Chiffres précis remplacés par des approximations (« 412 isolats » → « plusieurs centaines »).
  3. Nuance d'incertitude effacée au profit d'une affirmation lisse (« autour de 6 000 ans, IC95 : 4 200-8 300 » → « plusieurs millénaires »).
  4. Voix singulière de l'auteur (telle qu'attestée par le manuscrit ou le `cahier_de_labo.md`) remplacée par une tournure neutre IA.
  
  Si **une seule** régression est constatée, **`score(vk+1)` est invalidé même si la grille typographique monte**. Restaurer vk, changer de cible vers un autre item. Cette règle prime sur toutes les autres : *la forme ne rachète jamais une perte de fond*.

- **Pas de cosmétique sans gain** : si une modification n'augmente strictement aucun item de la grille, elle est rejetée d'office. La beauté seule ne suffit pas — elle doit faire bouger le score (par exemple via item 11 « impression éditoriale »).
- **Régression sur un autre item** : si une modification fait passer un item à 1 mais en casse un autre à 0, le score net peut être nul ou négatif. Restaurer.
- **Honnêteté du scoring** : à chaque itération, scorer comme si la version vk était nouvelle. Ne pas valider à 1 un item douteux pour rester sous le seuil de convergence.
- **Pas de boucle sur le voisinage** : item 10 (cohérence n-1/n+1) ne peut être l'objet d'une itération — il n'y a qu'une seule façon de le valider et elle se fait en Phase 3. Si l'item 10 est à 0, c'est qu'il faut **déplacer ou supprimer la slide**, pas la repolir.

**Communication à l'utilisateur** : à chaque itération, **une ligne** :

```
v3 [14/16] (+1 vs v2) — cible : impression éditoriale → typographie/espacement
```

À la fin, **livrer un récapitulatif** de la trajectoire (le tableau `scores.md`) en plus de la version retenue.

**Cas spécial — l'utilisateur veut une seule passe** : si la demande contient « une seule passe », « pas de boucle », « directement », « rapide », appliquer Phase 6 + §7.1-7.3 puis livrer v1 sans entrer dans la boucle §7.4. L'annoncer en une ligne : « Mode passe unique — livraison de v1 sans itération. »

#### 7.4bis — Audit du code source LaTeX (bloquant, distinct de l'audit visuel)

**Pourquoi cette phase existe.** Plusieurs épisodes documentés ont montré qu'un score 16/16 (qualité éditoriale) + 10/10 NON (propreté visuelle) peut coexister avec un code source **structurellement amateur** que n'importe quel chercheur habile en LaTeX/Beamer détecterait immédiatement à la lecture du `.tex`. Le rendu PDF peut « presque » marcher, mais le code trahit l'absence d'expertise et devient ingérable en maintenance. Cette phase audite le *code*, pas le *rendu*.

**Principe** : grille pass/fail sur 8 antipatterns LaTeX/Beamer/TikZ. Tout OUI bloque la livraison.

**Lecture du fragment final** : extraire le code de la frame finale (du `\begin{frame}` au `\end{frame}` correspondant) et passer chaque item :

##### Antipatterns TikZ structurels

1. **`\draw rectangle` + `\node` texte séparé** (au lieu de `\node[draw,...]{texte}`)
   - Signal : présence de `\draw[...] (x,y) rectangle (x',y');` suivie d'un `\node[...] at (x'',y'') {...};` qui contient le texte de cette boîte.
   - Pourquoi c'est mauvais : le texte ne s'auto-dimensionne pas, donc tout changement du contenu peut faire déborder le cadre. Corrigeable seulement à coordonnées manuelles.
   - Remplacement : `\node[draw, rounded corners, fill, text width=Xcm, align=center, inner sep=Ypt] (id) at (x,y) {texte};` — un seul élément, auto-dimensionné.

2. **Coordonnées absolues numériques pour le positionnement relatif** (au lieu de `right=Xcm of A`, `below=Ycm of B`)
   - Signal : plusieurs `\node[...] at (x1,y1)` puis `\node[...] at (x2,y2)` avec relations spatiales évidentes (« à droite de », « en dessous de »).
   - Pourquoi c'est mauvais : ajouter ou réordonner un node oblige à recalculer tout. Fragile.
   - Remplacement : positionnement relatif `right=2cm of host`, `below=1cm of $(a)!0.5!(b)$` (libs `positioning, calc`).
   - Exception tolérée : 1 ou 2 nodes d'ancrage initiaux peuvent être en coordonnées absolues si le schéma est simple (≤ 4 nodes).

3. **Pas de `text width` sur nodes multi-lignes**
   - Signal : un `\node[...]{Texte avec \\ saut de ligne}` sans `text width=Xcm` dans les options.
   - Pourquoi c'est mauvais : le saut de ligne forcé est laid et fragile. Le wrap automatique est plus propre.
   - Remplacement : ajouter `text width=Xcm, align=center` dans le style ou les options.

4. **Flèches `>=stealth` sans `shorten >=Xpt`**
   - Signal : `\draw[->, >=stealth] (a) -- (b)` où `b` est un node ou rectangle (pas une coordonnée libre).
   - Pourquoi c'est mauvais : la pointe `stealth` déborde sur la cible (pénétration). Le rendu peut sembler propre à basse résolution mais montre des collisions à 220 dpi.
   - Remplacement : `\draw[-Latex, shorten >=3pt]` (lib `arrows.meta`) ou `\draw[->, >=stealth, shorten >=2pt]`.

5. **Pas de `\usetikzlibrary` chargé pour des fonctionnalités utilisées**
   - Signal : code TikZ avec `right=of`, `Latex`, `$(a)!0.5!(b)$`, `fit`, etc., sans les libs correspondantes (`positioning`, `arrows.meta`, `calc`, `fit`) dans le préambule.
   - Pourquoi c'est mauvais : compilation peut marcher par accident sur une installation TeX généreuse mais casse ailleurs.
   - Remplacement : signaler explicitement les `\usetikzlibrary{...}` manquantes à l'utilisateur (ne pas modifier le préambule sans confirmation).

##### Antipatterns LaTeX/Beamer généraux

6. **`\\` orphelin dans une `frame` (hors environnement adapté)**
   - Signal : `\\` au niveau racine de la frame, hors `tabular`, `align`, `cases`, `aligned`.
   - Pourquoi c'est mauvais : produit un saut de paragraphe Beamer souvent imprévisible.
   - Remplacement : `\par`, `\medskip`, `\bigskip`, ou structurer en `\begin{itemize}`/`\begin{block}`.

7. **`\vspace{Xpt}` ou `\vspace{-Xem}` répétés pour faire tenir**
   - Signal : ≥ 3 `\vspace` (positifs ou négatifs) dans la même frame pour rééquilibrer.
   - Pourquoi c'est mauvais : symptôme d'un design qui ne tient pas. Chaque vspace masque un problème, jamais le résout.
   - Remplacement : revoir la modalité (alléger contenu, restructurer en colonnes, splitter la frame).

8. **`\scriptsize` ou `\tiny` global sur la frame** (au lieu d'une hiérarchie typo)
   - Signal : `\scriptsize` immédiatement après `\begin{frame}{titre}`.
   - Pourquoi c'est mauvais : tout est petit, pas de hiérarchie. Plus c'est généralisé, moins c'est éditorial.
   - Remplacement : taille par défaut au niveau frame, `\scriptsize` ou `\tiny` ciblé sur des blocs spécifiques (notes de bas, légendes, refs).

##### Procédure d'audit

```
v_final — audit code source

1. \draw rectangle + node séparé   [OUI / NON]
2. Coords absolues pos. relatif    [OUI / NON]
3. Pas de text width sur multi-l   [OUI / NON]
4. Pointe stealth sans shorten     [OUI / NON]
5. Libs TikZ manquantes            [OUI / NON]
6. \\ orphelin hors env.           [OUI / NON]
7. \vspace répétés                 [OUI / NON]
8. Taille globale au lieu de hier. [OUI / NON]

Statut : NON propre — corriger items X, Y.
```

**Critère bloquant** : tout item à OUI doit être corrigé avant livraison. La règle est binaire : « le code que je livre, un Beamer-iste habile l'aurait-il écrit ainsi ? ». Si non, refactoriser.

**Limite dure** : 3 itérations max d'audit code. Au-delà, signaler honnêtement les antipatterns résiduels à l'utilisateur plutôt que d'itérer en silence.

**Cette phase doit être exécutée AVANT §7.5** : un code propre produit le plus souvent un rendu propre. L'audit visuel §7.5 devient alors une confirmation, pas un détecteur.

#### 7.5 — Vérification de propreté visuelle (bloquante, boucle dédiée)

**Le cycle de polish n'est pas terminé tant que la slide n'est pas propre.** La grille de score §7.3 mesure la *qualité éditoriale* (argument, hiérarchie, palette). Elle ne détecte pas les *débordements physiques*. Une slide à 16/16 peut avoir du texte qui sort, un node TikZ trop étroit, un filigrane qui mord sur un mot. Cette §7.5 comble ce manque par une seconde boucle, distincte et bloquante.

**Principe** : score binaire pass/fail sur 10 items concrets ; on ne livre pas tant qu'un seul item est à OUI (défaut présent).

##### 7.5.1 — Parse des warnings de compilation

```bash
xelatex -interaction=nonstopmode <main>.tex 2>&1 | tee compile.log
grep -nE "Overfull |Underfull |LaTeX Warning|Missing character|Float" compile.log | head -40
```

Cibler en priorité :
- `Overfull \hbox` → boîte horizontale qui déborde, presque toujours visible à l'écran.
- `Overfull \vbox` → frame trop chargée verticalement, contenu écrasé ou rejeté hors page.
- `Missing character` → caractère manquant dans la police (souvent diacritique ou symbole exotique).

Pour chaque warning, **vérifier le numéro de ligne** : s'il pointe dans la frame cible, traiter immédiatement, ne pas continuer.

##### 7.5.2 — Inspection visuelle ciblée (capacité multimodale)

Convertir la slide finale en PNG haute résolution :

```bash
pdftoppm -r 220 -f $N -l $N <main>.pdf clean -png
```

###### 7.5.2.a — Procédure d'inspection par crops obligatoires (anti-mensonge)

**Pourquoi cette procédure existe.** Plusieurs épisodes documentés ont montré qu'une déclaration « 22/22 NON » sur la base d'une vue d'ensemble PNG peut être *factuellement fausse* : des débordements aux bords (texte sortant de la slide en bas, node sortant à droite) sont systématiquement ratés à la résolution PNG d'ensemble. La vue d'ensemble écrase les détails de bord. **L'audit honnête exige des crops dédiés à chaque bord.**

**Procédure obligatoire avant toute déclaration de score §7.5** — utiliser le script fourni dans le skill :

```bash
python3 ~/docs/codes/claude_plugins/bio_redac/skills/slide-polish/slide_crops.py main.pdf --page <N>
# ou directement sur un PNG :
python3 ~/docs/codes/claude_plugins/bio_redac/skills/slide-polish/slide_crops.py clean-1.png
```

Le script génère 5 fichiers `<base>_{top,bottom,left,right,center}.png` à côté de l'input.

Pour générer manuellement (si le script n'est pas disponible) :

```bash
python3 -c "
from PIL import Image
im = Image.open('clean-1.png')
w, h = im.size
im.crop((0, 0, w, h // 8)).save('crop_top.png')
im.crop((0, h * 7 // 8, w, h)).save('crop_bottom.png')
im.crop((0, 0, w // 8, h)).save('crop_left.png')
im.crop((w * 7 // 8, 0, w, h)).save('crop_right.png')
im.crop((w // 4, h // 4, w * 3 // 4, h * 3 // 4)).save('crop_center.png')
"
```

Lire les 5 crops avec l'outil `Read` (capacité multimodale) et répondre **explicitement** :

| Crop | Question | Verdict attendu si propre |
|---|---|---|
| `crop_top.png` | Le titre tient-il ? Pas de mot coupé ? Pas d'élément touchant le bord haut ? | NON débordement |
| `crop_bottom.png` | Le footer X/N est-il visible avec ≥ 1 ligne de blanc avant ? Aucun mot ni accolade ne touche le bord bas ? | NON débordement |
| `crop_left.png` | Aucun node, image, ou texte ne touche le bord gauche ? Marge respectée ? | NON débordement |
| `crop_right.png` | Aucun node TikZ, étiquette, ou bloc ne touche ou dépasse le bord droit ? | NON débordement |
| `crop_center.png` | Les éléments centraux (schéma, blocs) sont-ils intègres ? Aucun chevauchement node sur node ? | NON collision |

**Règle bloquante** : tant que ces 5 crops n'ont pas été *visuellement lus*, item A1 (Texte hors slide) et item C10 (Collision) ne peuvent pas être déclarés à NON. La déclaration « 22/22 NON sans crops » est interdite.

**Pattern à reconnaître dans les crops** :
- *Crop bas* : présence de toute lettre touchant le bord inférieur ou interrompue par lui = texte coupé. Footer X/N doit être à au moins 5 % de hauteur de slide au-dessus du bord = espace réservé Beamer.
- *Crop droit/gauche* : présence de tout cadre TikZ (`\node[draw,...]`) dont la bordure droite/gauche touche ou sort du bord = node hors slide.
- *Crop centre* : présence de 2 cadres TikZ dont les bordures se chevauchent visiblement = collision nodes.

###### 7.5.2.b — Inspection systématique des 22 items

Lire `clean-1.png` avec l'outil `Read` (en complément des 5 crops) et **chercher explicitement** chacun des vingt-deux défauts ci-dessous, organisés en cinq familles (A débordements, B espaces, C collisions, C-bis labels et logique des flèches, D typographie). Chaque item se répond OUI (défaut présent) / NON (slide propre sur ce point). Une slide *propre* a **les 22 items à NON**.

**Items A1, A5, C10 ne peuvent jamais être déclarés NON sans crops 7.5.2.a effectués au préalable.**

##### Famille A — Débordements physiques

1. **Texte qui sort de la slide** : un mot, une ligne, un objet touche ou dépasse un bord (gauche, droit, bas, haut). Inspecter les quatre marges séparément, à la pixel près sur le PNG haute résolution.
2. **Texte qui dépasse d'un node TikZ** : un mot ou une ligne sort du cadre d'un `node` (rectangle, circle, ellipse, shape custom). Vérifier chaque cellule de chaque schéma : le texte est-il intégralement dans le cadre, ou un mot final ou une virgule sortent-ils ?
3. **Image qui dépasse** : `\includegraphics` débordant de la zone disponible (image plus grande que le canvas, ou ratio mal négocié).
4. **Élément hors-champ** : objet TikZ positionné en `(x,y)` au-delà de la zone visible (typique sur frames à overlay).
5. **Pied de page / footer poussé** : numéro de slide, footer, *frame title* débordant ou tronqué.

##### Famille B — Espaces et équilibres

6. **Grande zone de blanc inutile** : zone vide d'au moins 1/6 de la surface de la slide qui ne sert ni à respirer un point focal ni à séparer deux blocs distincts. Inspecter spécifiquement : entre titre et premier bloc, entre deux colonnes, entre dernière ligne de contenu et footer.
7. **Espace injustifié entre éléments** : `\vspace{}` excessif (positif ou négatif), `\medskip` répété, ligne vide LaTeX qui produit un blanc visible non motivé. Si la respiration n'a pas de fonction (séparer un keypoint, isoler un crédit), elle est de trop.
8. **Saut de ligne pour un seul mot orphelin** : une ligne contient un mot seul ou deux mots courts parce que le précédent a wrappé juste avant. Au lieu d'accepter ce wrap, **reformuler la phrase** pour qu'elle tienne. Le wrap technique n'est pas un substitut à l'écriture ; un mot orphelin signale presque toujours une formulation trop longue d'un cran.
9. **Densité hétérogène entre colonnes** : 3 colonnes dont une est saturée de texte et les deux autres semi-vides. Soit rééquilibrer le contenu, soit changer de layout.

##### Famille C — Collisions et hiérarchies

10. **Collision entre éléments** : deux objets se chevauchent (texte sur figure, label sur axe, légende sur courbe, flèche sur node, accolade sur texte).
11. **Flèche qui mord un texte ou une cellule** : une flèche TikZ part *au-dessus* du texte d'un node (au lieu de partir du bord bas), ou sa pointe pénètre dans un autre node, ou son trait traverse une légende. Inspecter chaque flèche : son origine est-elle sur le bord propre d'un node ? Sa pointe s'arrête-t-elle visiblement *avant* la cible ?
12. **Texte de cellule TikZ trop petit** : font excessivement petite (`\tiny` ou inférieur visible) laissant ≥ 30 % de la cellule vide. La cellule est sur-dimensionnée par rapport au texte. Réduire la taille du node ou augmenter la font.
13. **Texte de cellule TikZ trop gros** : font qui sature la cellule (texte qui touche les bords, ou pas de marge interne visible). Symptôme : `inner sep` trop petit ou pas de `text width`. Augmenter le padding ou réduire la font.
14. **Couleur ou trait incohérents entre nodes apparentés** : trois nodes du même type avec trois épaisseurs de trait différentes, ou deux flèches « même rôle » avec deux couleurs aléatoires.

##### Famille C-bis — Labels et logique des flèches dans les schémas TikZ

Cette sous-famille est dédiée aux **erreurs sémantiques et de positionnement des labels** dans les schémas conceptuels. Elle est souvent ratée par les audits classiques parce qu'elle exige de comprendre l'argument narratif du schéma, pas seulement le rendu visuel.

15a. **Label de flèche/arc mal centré sous son ancre visuelle**
   - Signal : un label « bouclé sur shap » alors que l'arc va de `dowhy` à `sim` ; donc le label devrait être centré sous le **milieu de l'arc** (entre `sim` et `dowhy`), pas sous `shap` qui est au milieu du pipeline mais pas du milieu de l'arc.
   - Pour chaque flèche/arc, vérifier : *quel est son milieu visuel ?* Et *où est positionné son label ?* Si les deux ne coïncident pas, déplacer le label avec `at ($(source)!0.5!(cible) + (0,-Xcm)$)` ou similaire.

15b. **Label posé sur ou trop près de la flèche/arc**
   - Signal : le texte du label chevauche le trait de la flèche, ou s'en approche à moins de 0.2 cm.
   - Geste : décaler le label perpendiculairement à la flèche ; pour un arc descendant, descendre le label de `0.3` à `1cm` selon l'amplitude de l'arc.

15c. **Erreur de logique dans le sens de la flèche**
   - Signal : la flèche va de A vers B, mais le narratif demande que B influe sur A (cas du feedback, du contrôle, de la cause).
   - Vérifier pour chaque flèche : *la pointe va-t-elle vers le node qui reçoit/subit ?* Pour un feedback type « DoWhy déclenche une révision des simulations », la flèche doit avoir sa pointe sur `sim`, pas sur `dowhy`.

15d. **Erreur de logique dans la source/cible de la flèche**
   - Signal : la boucle est censée représenter « si DoWhy détecte un confounder non identifiable, on retourne aux simulations » mais elle part de `Décision` au lieu de `DoWhy`.
   - Vérifier pour chaque flèche : *quels sont le node source et le node cible attendus par le narratif ?* Les ancres TikZ doivent correspondre.

15e. **Incohérence visuelle entre le type de flèche et son rôle narratif**
   - Si une flèche est de pilotage (LLM → stages), elle doit être visuellement distincte (pointillé, couleur secondaire) des flèches de flux (sim → xgb → ...).
   - Si une flèche est de feedback (DoWhy → sim), elle doit être visuellement distincte également (arc inférieur, autre couleur).
   - Vérifier pour chaque type de flèche : *son style est-il cohérent dans tout le schéma ?* Et *son style est-il distinct des autres types ?*

##### Famille D — Typographie et effets

15. **Trop de gras** : `\textbf{...}` sur plus de ~15 % du texte visible, ou plusieurs mots gras dans une même phrase. Le gras est un signal — il perd son sens si appliqué partout. Le retenir pour : noms propres première occurrence, valeurs clés numériques, terme défini.
16. **Trop d'effets typographiques mixés** : italique + gras + couleur + emphase sur le même mot ; ou plus de 3 grandeurs typographiques dans une même slide. Symptôme du « tout important = rien important ».
17. **Saut de ligne du titre malheureux** : titre cassé à un endroit qui sépare un nom propre, un terme composé, un sigle de son développement. **Et plus largement** : titre sur 2 lignes alors qu'une reformulation l'aurait fait tenir.

Sortie attendue (à journaliser dans `iterations/clean.score`) :

```
v_final — propreté

1. Texte hors slide          [NON]
2. Texte hors node TikZ      [OUI] <- node "Méthodes" trop étroit (x=2,y=1.4)
3. Collision                 [NON]
4. Image dépasse             [NON]
5. Hors-champ                [NON]
6. Coupure / veuve           [NON]
A. Débordements physiques
 1. Texte hors slide            [NON]
 2. Texte hors node TikZ        [NON]
 3. Image dépasse               [NON]
 4. Hors-champ                  [NON]
 5. Footer / titre poussé       [NON]

B. Espaces et équilibres
 6. Grande zone de blanc        [NON]
 7. Espace injustifié           [NON]
 8. Mot orphelin / wrap inutile [NON]
 9. Densité hétérogène cols     [NON]

C. Collisions et hiérarchies
10. Collision éléments          [NON]
11. Flèche mord texte/cellule   [NON]
12. Texte cellule trop petit    [NON]
13. Texte cellule trop gros     [NON]
14. Couleurs incohérentes       [NON]

C-bis. Labels et logique des flèches
15a. Label mal centré sous arc  [NON]
15b. Label trop près de l'arc   [NON]
15c. Sens de flèche incorrect   [NON]
15d. Source/cible incorrecte    [NON]
15e. Style flèche incohérent    [NON]

D. Typographie et effets
16. Trop de gras                [NON]
17. Trop d'effets mixés         [NON]
18. Saut titre malheureux       [NON]

Statut : NON propre — corriger items X, Y, Z.
```

##### 7.5.3 — Boucle de propreté (jusqu'à zéro défaut)

Si un ou plusieurs items sont à OUI, **corriger ciblé** et recompiler. Recettes typiques :

| Défaut | Geste de correction |
|--------|---------------------|
| 1. Texte hors slide | Réduire police, élargir la zone (`\hsize`), retravailler le wrap, raccourcir le titre |
| 2. Texte hors node TikZ | Ajouter `text width=<W>cm`, augmenter `inner sep=<n>pt`, ou agrandir `minimum width` |
| 3. Image dépasse | `width=0.95\paperwidth,height=0.85\paperheight,keepaspectratio` |
| 4. Hors-champ | Vérifier les coordonnées TikZ ; recadrer dans `(-7,-4) -- (7,4)` pour 16:9 |
| 5. Footer / titre poussé | Réduire le contenu, raccourcir le titre, ou splitter en deux frames |
| 6. Grande zone de blanc | Remplir intentionnellement (filigrane, big number, citation) ou redistribuer les blocs |
| 7. Espace injustifié | Supprimer le `\vspace` ou `\medskip` ; si nécessaire à la mise en page, c'est qu'il manque un contenu |
| 8. Mot orphelin | **Reformuler la phrase**, pas forcer le wrap. Le mot orphelin signale presque toujours une formulation à raccourcir |
| 9. Densité hétérogène | Rééquilibrer le contenu, ou changer de layout (passer de 3 cols à 2+1) |
| 10. Collision éléments | `node distance` plus grand, `to[bend left=20]`, changer ancrage (`.north east`) |
| 11. Flèche mord | Flèche doit partir d'un bord propre (`.south`, pas du centre) ; ajouter `shorten >=3pt` ; vérifier que la cible n'est pas masquée |
| 12. Texte cellule trop petit | Réduire la taille du node ou augmenter la font ; ratio texte/cellule visé ≥ 60 % |
| 13. Texte cellule trop gros | Augmenter `inner sep` ou réduire la font ; laisser ≥ 4pt de marge interne visible |
| 14. Couleurs incohérentes | Définir des styles nommés réutilisables dans `\tikzset{...}` |
| 15a. Label arc mal centré | Repositionner avec `at ($(source)!0.5!(cible) + (0,-Xcm)$)` au milieu géométrique de l'arc |
| 15b. Label trop près de l'arc | Augmenter le décalage perpendiculaire, typiquement `+(0,-0.8cm)` à `+(0,-1cm)` pour un arc inférieur |
| 15c. Sens flèche incorrect | Inverser source et cible, ou utiliser `<-` ou `<->` ; vérifier le narratif (qui influe sur qui ?) |
| 15d. Source/cible incorrecte | Identifier les nodes attendus par le narratif et corriger les ancres TikZ (`A.south` → `B.south`) |
| 15e. Style flèche incohérent | Créer des styles nommés (`flow`, `pilot`, `loop`) pour distinguer flux / pilotage / feedback |
| 16. Trop de gras | Retirer 2/3 des `\textbf{...}` ; ne garder que les valeurs clés et les noms propres première occurrence |
| 17. Trop d'effets | Une emphase par mot maximum (gras OU italique OU couleur, pas deux ensemble) ; max 3 grandeurs typo |
| 18. Saut titre malheureux | Insérer `\\` explicite à un endroit propre, raccourcir le titre, ou `\linebreak[3]` |

Recompiler, re-extraire le PNG, re-lire, re-scorer.

**Limite dure** : 5 itérations de propreté max. Si après 5 cycles certains items restent à OUI, **stopper et signaler honnêtement à l'utilisateur** quels défauts subsistent, leur localisation et leur cause probable. Ne **jamais** livrer une slide non propre en silence.

**Le cycle de polish n'est pas terminé** tant que les 22 items de §7.5.2 ne sont pas tous à NON, ou que la limite dure est atteinte avec signalement explicite. Il est tout à fait possible — et même fréquent — que la boucle qualité §7.4 finisse, donne une version éditorialement bonne, et qu'il faille deux à trois cycles supplémentaires de §7.5 pour rendre la slide *physiquement* propre. C'est attendu, c'est normal, ce n'est pas une régression.

#### 7.5bis — Test de voix scientifique (bloquant, dernière étape avant livraison)

Une slide peut avoir un score qualité 16/16 (§7.4), être physiquement propre 10 NON (§7.5), et néanmoins **sonner faux à l'oreille de l'auteur**. C'est précisément ce qui s'est produit dans les cas où le polish a inséré des phrases comme *« Je n'apporte pas une transposition d'outils, j'apporge une seconde fenêtre observationnelle »* — phrase au score impeccable, au tiret cadratin caché, et que **l'auteur n'écrirait jamais**.

Ce test final, multimodal cette fois **sur le texte** (pas sur le PNG), vérifie que la voix est celle d'un scientifique, pas celle d'une plaquette ni d'une IA cultivée.

##### Procédure

1. **Extraire** tout le texte visible de la slide finale : titre, sous-titre, corps, légendes, *keybox*, crédit.
2. **Pour chaque phrase**, appliquer les trois questions de la grille de voix :
   - L'auteur, dans un mail à un collègue, écrirait-il cette phrase ?
   - Cette formulation se trouve-t-elle dans le manuscrit ou le `cahier_de_labo.md`, ou a-t-elle été produite ex nihilo pour la slide ?
   - Y a-t-il un mot ou une tournure qu'aucun scientifique du domaine n'emploierait dans un papier ?
3. **Si une seule phrase échoue**, réécrire dans la voix de l'auteur (ce que dit le manuscrit, pas ce qu'écrirait une plaquette) ou supprimer. Référence des patterns rouges : tableau Famille 2 de §7.1.
4. **Re-vérifier les tirets** par `grep -E '—|–|---?'` après réécriture. Une réécriture peut réintroduire un tiret cadratin si on remplace par une virgule augmentée d'un tiret.

##### Critère bloquant

- Zéro tiret cadratin / demi-cadratin / double tiret dans le code source du fragment.
- Zéro antithèse binaire pompeuse, zéro slogan creux, zéro chiasme vide, zéro métaphore filée fade.
- Au moins un terme technique précis par phrase non-titre (chiffre, méthode nommée, taxon, gène, mutation, paramètre).
- Aucune phrase qui aurait pu être générée pour n'importe quel sujet voisin (test de transférabilité : si la phrase reste plausible en remplaçant le sujet par autre chose, elle est trop générique).

##### Journalisation

Dans `iterations/voice.score` :

```
v_final — voix scientifique

Phrase 1 (titre) : [OK]
Phrase 2 (corps) : [OK]
Phrase 3 (corps) : [FAIL — antithèse pompeuse « pas X, j'apporte Y »]
Phrase 4 (keybox): [OK]
Phrase 5 (crédit): [OK]

grep tirets   : [OK] (aucune occurrence)
Statut global : NON valide — réécrire phrase 3.
```

##### Boucle

Si une phrase échoue, **réécrire et reboucler §7.5bis** (zéro tiret, zéro pattern rhétorique). Limite dure 3 itérations de voix : au-delà, signaler à l'utilisateur qu'une phrase résiste à la réécriture et lui proposer une formulation alternative à valider à la main. **Ne jamais livrer une slide non validée §7.5bis**.

#### 7.6 — Livraison

- Présenter le PNG **avant** (v0) et le PNG **après** (version retenue à l'issue de §7.4, puis nettoyée par §7.5, puis validée §7.5bis) dans la réponse.
- Inclure le **tableau des scores qualité** (`scores.md`) pour expliciter la trajectoire d'amélioration et la raison d'arrêt (plafond / convergence / régression bloquée / limite dure).
- Inclure le **score de propreté final** (`clean.score`) — confirmer 10/10 NON, ou lister honnêtement les défauts résiduels si limite dure §7.5 atteinte.
- Inclure le **score de voix** (`voice.score`) — confirmer 100 % des phrases validées, ou lister les formulations laissées à l'arbitrage manuel.
- Inclure la **synthèse Phase 3bis** : la thèse pleine reconstituée, les axes de spécificité préservés, ce que la slide finale dit en plus / mieux que la version initiale.
- Donner le **diff** des lignes modifiées dans le `.tex` (lecture rapide).
- Sauvegarder l'original sous `<main>.tex.bak.<timestamp>` avant d'écraser.
- Justifier en 3 lignes maximum les choix retenus (modalité, illustration, allègements, gains d'itération).
- Suggérer une suite : autre slide à polir, ou validation globale par `beamer-slides` ou `manuscript-review`.

## Sous-agents et délégation

| Besoin | Skill délégué |
|--------|---------------|
| Carte géographique | `geo-map` (toujours, jamais à la main) |
| Figure de données depuis CSV | `create-viz`, puis `seaborn` / `matplotlib-pro` / `plotly` |
| Arbre phylogénétique réel | `iqtree-lsd2`, `itol` |
| Vérification d'un chiffre / d'une date | `claim-check` |
| Recherche de littérature ciblée (1 à 3 réfs) | `lit-review` |
| Passage de style scientifique | `deai-latex` (**obligatoire** en Phase 7.1) |
| Patrons TikZ avancés | `slide-design §5.2` (lecture pour modèles) |
| Slide PowerPoint au lieu de Beamer | `pptx` |
| Refonte du thème complet du deck | `theme-factory` |

Règle : un seul niveau de délégation par défaut.

## Anti-patrons à éviter

0bis. **Mensonge structurel d'audit § 7.5 sans crops** (l'antipattern le plus grave, à éliminer en priorité absolue). Déclarer « 22/22 NON » sur la propreté visuelle d'une slide en lisant seulement le PNG d'ensemble, sans générer ni lire les 5 crops obligatoires (top, bottom, left, right, center). La vue d'ensemble écrase systématiquement les détails de bord — un débordement de texte par le bas, un node TikZ qui sort à droite, une collision entre 2 cadres centraux sont **invisibles à la résolution d'ensemble**. Conséquence : on livre une slide bancale avec une déclaration de score qui prétend qu'elle est propre. C'est un *mensonge structurel* car le pipeline a un score de validation, mais ce score peut être fabriqué sans audit réel. Antidote : procédure §7.5.2.a obligatoire — générer les 5 crops via `slide_crops.py` (fourni dans le skill), les lire **chacun** avec `Read`, répondre explicitement avant toute déclaration d'items A1/A5/C10. Sans les crops, on ne déclare *jamais* « propre ».

0. **Moyennisation par polissage** (le pire après le mensonge structurel). Prendre une slide moyenne et la rendre *plus belle moyenne* : score §7.4 qui grimpe, hiérarchie typographique propre, palette respectée — mais perte de spécificité, perte de nuance, perte de voix. Le polish a servi la forme contre le fond. Antidote : Phase 3bis (reconstruire la thèse pleine), veto anti-moyennisation §7.4, test de voix §7.5bis.
00. **Rhétorique IA insérée comme amélioration**. Patterns à reconnaître au premier regard : « pas X, j'apporte Y », « une seconde fenêtre sur Z », « explorer le paysage de », « une approche unique pour », « met en lumière », « interroge la complexité de ». Aucun chercheur n'écrit cela en mail à un collègue. Antidote : §7.1 Famille 2 et §7.5bis.
1. **Refondre une slide déjà bonne** par envie de toucher. Si la grille de critique passe à 10/10, livrer telle quelle avec un mot de validation.
2. **Changer de modalité sans gain narratif** : remplacer une liste correcte par un TikZ joli mais creux est une régression.
3. **Watermark décoratif sans rapport** : photo de microscope sur slide d'épidémiologie statistique → confusion sémantique.
4. **Watermark trop opaque** : si le texte devient pénible à lire, l'ensemble échoue.
5. **Ignorer le voisinage** : améliorer la slide en isolation et casser la cohérence du deck (redondance avec n-1, saut narratif vers n+1).
6. **Couper du contenu essentiel** au nom de l'allègement : « moins de mots » n'est pas « moins de sens ».
7. **Sourcer par WebSearch sans vérifier la source** : un chiffre Wikipedia non corroboré reste un chiffre fragile.
8. **Sauter `deai-latex`** : sans cette étape, la slide garde la signature stylistique d'un texte produit par IA (gras réflexes, em-dashes, listes mécaniques, clichés).
9. **Ne pas recompiler avant livraison** : un fragment qui « semble correct » dans le code peut casser la compilation ou paraître écrasé à l'écran.
10. **Oublier de sauvegarder l'original** : toujours produire `<main>.tex.bak.<timestamp>` avant d'écraser.

## Exemples d'invocation typiques

**Cas 1 — Slide trop chargée**
> « /slide-polish "Caractéristiques épidémiologiques du Burundi" »

Phase 2 : diagnostic visuel — densité saturée, 6 puces, deux idées concurrentes. Phase 3 : titre catégoriel, l'argument se cache au milieu des puces. Phase 4 : décision *alléger + changer de modalité* (big number + sparkline pour le chiffre marquant, le reste passe en commentaire oral). Phase 6 : nouvelle slide « 73 % des isolats portent rpoB-S450L au Burundi » + sparkline 2008-2024. Phase 7 : `deai-latex`, recompilation, critique.

**Cas 2 — Slide trop vide**
> « polish-moi la slide qui s'appelle "Méthodologie" »

Phase 2 : slide à 9 mots, point focal absent. Phase 3 : titre catégoriel, voisinage n+1 parle directement de résultats sans avoir posé l'approche. Phase 4 : décision *enrichir + changer de modalité* (workflow TikZ 4 boîtes : Échantillonnage → Séquençage → Phylogénie → Datation). Phase 5 : matière déjà dans le `cahier_de_labo.md`, pas de recherche externe. Phase 6 : schéma TikZ. Phase 7 : `deai-latex`, vérification.

**Cas 3 — Slide d'introduction sans illustration**
> « /slide-polish 3 » (la slide 3 introduit la tuberculose globale)

Phase 2 : densité moyenne, palette correcte, pas d'illustration. Phase 3 : voisinage n-1 = titre, n+1 = chiffres précis ; la slide 3 doit poser l'enjeu global. Phase 4 : décision *enrichir avec un filigrane* (carte du monde stylisée en opacity 0.12, incidence TB en arrière-plan). Délégation `geo-map`. Phase 6 : intégration en Phase 6.2. Phase 7 : recompilation, vérification que le texte reste lisible par-dessus, `deai-latex`.

## Format des sorties à copier-coller

Si l'utilisateur demande la version révisée pour la coller dans Overleaf, fournir le fragment LaTeX bien indenté, prêt à `\input{}` ou à coller en remplacement du bloc `\begin{frame}...\end{frame}` original. Pas de doubles sauts de ligne parasites, pas d'indentation avant les balises.

## Résumé du skill

Une slide remaniée est une slide qui *raisonne* mieux *sur du fond préservé voire enrichi*, qui *lit* mieux, *se situe* mieux, ne déborde pas physiquement, et **parle dans la voix de l'auteur, pas dans celle d'une IA cultivée**. `slide-polish` impose, dans l'ordre :

1. **Brasser large sur le fond** (Phase 3bis) : reconstruire la thèse pleine du projet sur ce point, détecter si la slide actuelle est un sous-produit moyennisé d'une pensée plus pointue, orienter vers *enrichir vers la singularité* plutôt que *alléger vers la généralité*. Cette étape est fondamentale, elle commande tout.
2. **Réécrire** dans la modalité retenue, en respectant le système de design et le voisinage narratif.
3. **Itérer** sur la qualité éditoriale (§7.4) avec veto anti-moyennisation : tout gain typographique obtenu au prix d'une perte de fond est annulé.
4. **Nettoyer** physiquement (§7.5) : zéro débordement, zéro collision, zéro veuve.
5. **Valider la voix scientifique** (§7.5bis) : zéro antithèse pompeuse, zéro slogan creux, zéro tiret cadratin / demi-cadratin / double tiret, chaque phrase passe le test « l'auteur l'écrirait-il en mail à un collègue ? ».

Le cycle n'est pas terminé tant que la slide n'est pas *propre*, *spécifique*, et *écrite en voix d'auteur*. Le résultat livré inclut le PNG avant/après, la thèse pleine reconstruite, les tableaux de scores qualité/propreté/voix, et la raison d'arrêt explicite — pour que l'utilisateur sache ce qui a été préservé, ce qui a été gagné, et qu'aucune phrase de plaquette ne s'est glissée dans le rendu final.
