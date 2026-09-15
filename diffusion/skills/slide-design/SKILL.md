---
name: slide-design
description: >-
  Transform a short description of what you want to say into one to a few editorial-grade
  slides. Enforces a design system (palette, typography, grid), reasons about the narrative,
  proposes several structural options with explicit editorial references (NYT Graphics,
  Bloomberg, Pudding, Tufte, Nature Methods), requires at least one option with a strong
  visual signature, prefers schemas, timelines and diagrams over plain text, reuses figures
  found in the project, delegates maps to geo-map and charts to sci-figure, matches the host
  deck's style, and systematically compiles a preview and critiques the PNG before delivery.
  Use when the user types /slide-design, asks for one or two slides on an idea, says "I need
  a slide that says..." or "fais-moi 2 slides sur Y", or otherwise needs a verbal idea
  turned into polished slide material rather than a whole presentation.
user_invocable: true
invocation: /slide-design
---

# Slide Design : Concevoir 1 à quelques slides à partir d'une description

Ce skill ne remplace pas `beamer-slides` (qui génère une présentation entière depuis un article). Il intervient sur l'autre besoin : **partir d'une idée verbale et concevoir 1 à quelques slides** vraiment travaillés, où chaque choix de mise en forme est justifié.

L'objectif est de produire des supports **visuels, clairs, agréables, utiles**, pas du texte mis en colonnes. Tout slide qui peut être un schéma, une frise, un diagramme ou une illustration doit l'être.

## Quand l'invoquer

- L'utilisateur tape `/slide-design`.
- L'utilisateur demande explicitement 1 à 5 slides sur un point précis (« fais-moi une slide qui montre... », « j'ai besoin de deux slides pour expliquer... »).
- L'utilisateur a déjà une présentation et veut **insérer** un petit bloc (« il me manque une slide entre la X et la Y sur Z »).
- L'utilisateur expose oralement une idée et demande comment la mettre en forme visuellement.

**Ne pas invoquer** si le besoin est une présentation complète (15+ slides depuis un article) : utiliser `beamer-slides`. Si le doute persiste, demander.

## Philosophie

1. **Le slide est un support, pas le discours.** Le texte sur la slide n'est pas ce qui sera dit ; c'est ce qui aide à le retenir. Donc : moins de mots, plus d'objets visuels.
2. **Une slide = une idée.** Si l'idée se subdivise, c'est deux slides.
3. **Une image bien choisie économise un paragraphe.** Schéma, frise, diagramme, photo, icône, métaphore visuelle : toujours envisager avant de saisir une puce de texte.
4. **Proposer avant de produire.** Le skill propose plusieurs options (2 à 3 angles narratifs) en prose courte, l'utilisateur choisit, puis seulement on génère le LaTeX/Beamer (ou PowerPoint si demandé).
5. **Cohérence avec l'existant.** Si la slide s'insère dans un deck, on respecte la palette, les polices, l'aspect ratio, les macros locales.

## Système de design : la grammaire visuelle avant le contenu

Un slide visuellement réussi ne sort pas d'un patron générique : il sort d'un **système cohérent** fixé avant la production. Trois choix à arrêter explicitement à chaque appel.

### 1. Palette (3 à 5 couleurs maximum)

Cinq palettes professionnelles prêtes à l'emploi (HEX, testées en projection et impression) :

| Nom | Usage typique | Primaire | Secondaire | Accent | Fond clair | Texte foncé |
|-----|---------------|----------|------------|--------|------------|-------------|
| Editorial | jury HDR, conférence sérieuse | `#1F3A5F` | `#7B9EB6` | `#C73E1D` | `#F2EFE9` | `#1B1B1B` |
| Lab | lab meeting, présentation interne | `#2A6F97` | `#61A0AF` | `#F4A261` | `#F7F4EE` | `#2D2D2D` |
| Heritage | histoire des sciences, vulgarisation | `#7E4E3B` | `#C4A484` | `#6B8E5A` | `#EFE6D6` | `#2A211B` |
| Vivid | pitch, slide à fort impact | `#0F4C81` | `#F5B82E` | `#E63946` | `#FAFAFA` | `#0A0A0A` |
| MTBC | toute slide sur la tuberculose | `#264653` | `#2A9D8F` | `#E76F51` | `#F4F1DE` | `#1F1B16` |

Pour les lignées MTBC, **ne jamais redéfinir les couleurs** : importer la palette canonique de `${CLAUDE_PLUGIN_ROOT}/skills/geo-map/scripts/geo_map.py` (constantes `MTBC_PALETTE` et `MTBC_PALETTE_CB`). Cohérence transversale avec les cartes et figures du projet.

**Règle de hiérarchie chromatique** : 60 % surface neutre / 30 % primaire ou secondaire / 10 % accent. Toute palette qui sort de ce ratio fatigue l'œil.

Si la slide accompagne un manuscrit ou un deck existant, **toujours préférer la palette du contexte** (extraite par `pptx`/`theme-factory` ou lue dans le préambule Beamer). Les palettes ci-dessus servent pour les slides nues.

### 2. Typographie (un couple, pas plus)

| Couple | Titre | Corps | Bien pour |
|--------|-------|-------|-----------|
| Editorial moderne | Inter Tight Bold | Source Serif Pro | Sciences humaines, vulgarisation |
| Scientifique propre | IBM Plex Sans Bold | IBM Plex Serif | Lab meeting, comité |
| Magazine | Playfair Display | Lato | Communication, grand public |
| Technique | JetBrains Mono Bold | Inter | Slides "punch", pitch tech |
| Sobre par défaut | Fira Sans SemiBold | Fira Sans | Toute slide neutre |

Polices à charger via `fontspec` avec `xelatex` ou `lualatex`. Si le deck hôte est compilé en `pdflatex` et impose Computer Modern, **ne pas chercher à forcer la police** : travailler les graisses (`\bfseries`), les capitales, l'espacement. Une slide est rarement décevante à cause de Computer Modern ; elle l'est à cause d'une hiérarchie absente.

### 3. Hiérarchie typographique et espacement

Trois grandeurs de texte maximum :
- **Titre** : 28-32 pt, gras, court, *informatif* (pas « Résultats » mais « La lignée 4.6.1.2 est dix fois plus fréquente au Burundi qu'au Bénin »).
- **Corps** : 14-18 pt, régulier.
- **Légende / crédit** : 9-11 pt.

Espacement à base de **4 pt** (8, 12, 16, 24, 32, 48). Aucune valeur arbitraire. Marge intérieure 4 % de la largeur. Grille implicite 12 colonnes, gouttière 12 pt.

**Test de justification** : si je ne peux pas justifier en une phrase pourquoi un élément est à *cet* endroit, à *cette* taille, dans *cette* couleur, alors le slide n'est pas conçu, il est jeté ensemble. Reprendre.

### 4. Bibliothèques TikZ à charger systématiquement

```latex
\usetikzlibrary{
  arrows.meta, positioning, fit, backgrounds,
  shadows.blur, fadings, decorations.pathreplacing,
  decorations.markings, calc, shapes.geometric,
  patterns.meta, intersections
}
```

Sans ces extensions, la qualité graphique reste celle d'un schéma de 2005. **Ne jamais s'en passer.**

## Processus

Le skill suit 5 phases : **Cadrer → Inventorier → Proposer → Choisir → Produire**. Ne sauter aucune phase.

### Phase 1 : Cadrer le besoin

Avant toute production, clarifier (et si l'utilisateur a demandé de ne pas s'interrompre, faire les choix raisonnables en les annonçant) :

1. **Le message exact** : reformuler en une phrase ce que l'audience doit retenir après avoir vu ces slides. Si plusieurs messages, c'est plusieurs slides.
2. **Le nombre de slides cible** : si pas précisé, proposer (généralement 1 à 3).
3. **Le public** : pairs spécialistes, comité mixte, grand public, étudiants, financeurs, jury ? Le registre change tout.
4. **Le contexte d'insertion** :
   - Slide isolée (export PNG/PDF) ?
   - À insérer dans un Beamer existant ? Demander le chemin du `.tex` parent.
   - Dans un PowerPoint/Keynote existant ? Demander un export ou une capture d'une slide voisine pour calquer le style.
5. **La langue** : par défaut, celle de l'utilisateur (français). Termes techniques restent dans leur langue d'origine.
6. **Le degré de formalité** : conférence sérieuse, lab meeting, vulgarisation, pitch ?

### Phase 2 : Inventorier les matériaux disponibles

Avant d'inventer, **chercher ce qui existe déjà**. C'est cette phase qui distingue un slide générique d'un slide réellement ancré dans le travail.

#### 2.1 : Si le slide concerne des résultats d'un projet local

Identifier le projet (le répertoire courant si l'utilisateur travaille dedans, sinon demander). Puis explorer :

```bash
# Figures déjà produites pour l'article ou d'autres présentations
find <project> -type d \( -name figures -o -name figs -o -name results -o -name "résultats" \) 2>/dev/null
find <project> -type f \( -name "*.png" -o -name "*.pdf" -o -name "*.svg" -o -name "*.jpg" \) 2>/dev/null | head -50

# Données tabulaires réexploitables
find <project> -type f \( -name "*.csv" -o -name "*.tsv" -o -name "*.parquet" \) 2>/dev/null | head -20
```

Pour chaque figure trouvée, juger :
- Est-elle **lisible telle quelle** projetée à 5 mètres ? (police > 14pt équivalent, légende lisible)
- Faut-il la **simplifier** (retirer panels secondaires, agrandir légende) ?
- Faut-il en **produire une nouvelle** à partir des données brutes ? Si oui, déléguer à `sci-figure` (preset `slide`) via le mécanisme sous-agent (voir §Sous-agents).

#### 2.2 : Si le slide est conceptuel (schéma, frise, méthode, contexte)

Pas de figure existante par défaut. Évaluer :
- Un **schéma TikZ** est-il pertinent ? (pour un workflow, une architecture, un mécanisme)
- Une **frise chronologique** ? (pour une histoire, une revue, une évolution)
- Un **diagramme de Venn / matrice 2×2 / quadrant** ? (pour une comparaison, une typologie)
- Une **icône + texte minimal** ? (pour une métaphore, un slogan)
- Une **image illustrative** depuis le web ? Voir §2.3.

#### 2.3 : Recherche web : quand et comment

Une image web n'a sa place que si :
- Elle est **immédiatement compréhensible** (photo d'objet, carte, portrait historique, organisme).
- Elle a une **licence claire** (Wikimedia Commons, Unsplash, Pexels, domaines publics, ou figures sous licence CC-BY avec attribution).
- Elle **ajoute** quelque chose qu'un schéma ne donnerait pas (la chose réelle plutôt que sa représentation).

Procédure si pertinent :
1. Lancer une recherche via `WebSearch` ou `WebFetch` sur les dépôts d'images libres (Wikimedia Commons en priorité).
2. Toujours **lister à l'utilisateur** les options trouvées avec leur source + licence avant insertion.
3. Ne jamais télécharger une image sans confirmer la licence. En cas de doute, proposer un schéma TikZ à la place.

**Ne pas chercher d'image web** pour des résultats scientifiques propres au projet, c'est à `sci-figure` / aux figures locales de couvrir ce besoin.

#### 2.4 : Inventaire iconographique et symbolique

Au-delà des figures, repérer systématiquement les ressources visuelles légères qui transforment un slide en objet éditorial :

- **Icônes vectorielles** : `\usepackage{fontawesome5}` (icônes génériques), `\usepackage{academicons}` (logos académiques : ORCID, arXiv, ResearchGate), `\usepackage{tikzsymbols}` (symboles sciences vivantes). Préférer toujours une icône vectorielle à un PNG.
- **Pictogrammes ISO** : `\usepackage{tikzpeople}` pour silhouettes humaines (déplacements, contacts, isolement). Domaine public, licence permissive.
- **Sparklines** : courbes condensées (10 à 20 points) inclusibles inline. Construire avec `\pgfplotsset{compat=1.18}` + axe minimaliste, ou via `\tikz\draw plot coordinates {...};` pour micro-tendances.
- **Symboles MTBC** : importer la palette canonique de `${CLAUDE_PLUGIN_ROOT}/skills/geo-map/scripts/geo_map.py`. Pour un bacille stylisé, capsule TikZ allongée (`shape=ellipse`, ratio 3:1, contour fin, motif strié léger).
- **Numerus / chiffres-clés** : `fontspec` + chiffres tabular / lining (`Numbers=Lining,Tabular`) pour les grands chiffres alignés sur une grille.

Critère : **si l'élément peut être ajouté en moins de 10 lignes TikZ et fait gagner en lisibilité, l'ajouter**. Sinon non.

#### 2.5 : Style du deck hôte

Si l'utilisateur insère dans un deck existant :
- **Beamer** : lire le préambule du `.tex` parent. Repérer le thème, les couleurs définies (`\definecolor`), les commandes maison (`\kb`, `\alert`, etc.), `aspectratio`, la `\graphicspath`. Réutiliser strictement.
- **PowerPoint/Keynote** : demander un export PDF du deck ou une capture d'une slide voisine. Lire les polices, palettes, marges, position du titre. Si le skill `pptx` est disponible et que le deck est un `.pptx`, le déléguer en sous-agent pour extraire le master et les layouts.
- **Aucun deck existant** : utiliser le thème Metropolis par défaut (cohérent avec `beamer-slides`) mais le mentionner.

### Phase 3 : Proposer (toujours 2 à 3 options narratives)

C'est l'apport principal du skill. **Ne pas se contenter d'une seule structure.** Toujours présenter à l'utilisateur 2 à 3 options bien distinctes, en prose courte (pas encore de LaTeX), chacune décrivant :

- **Angle narratif** (la promesse de la slide en une phrase).
- **Forme visuelle dominante** (schéma TikZ / frise / figure existante simplifiée / image web / diagramme custom / split figure+keymessage).
- **Disposition** (1 colonne, 2 colonnes 50/50 ou 60/40, plein-cadre, titre+image+caption).
- **Texte qui restera** (les seuls mots que l'audience lira).
- **Effort de production** (faible : assemblage / moyen : nouvelle figure simple / élevé : schéma TikZ complexe ou nouvelle analyse).

Exemple de présentation des options (à adapter, c'est un gabarit interne) :

```
Option A — Frise chronologique (1 slide)
  Forme : timeline TikZ horizontale, 5 jalons, icônes par jalon.
  Texte : titre + 5 dates + 1 mot-clé par date.
  Idéal pour : montrer l'évolution d'un concept ou d'une lignée.
  Effort : moyen (TikZ à écrire mais squelette standard).

Option B — Split figure + 3 take-aways (1 slide)
  Forme : colonne gauche figure existante simplifiée
          (figures/ml_tree_lineage4.pdf), colonne droite 3 puces courtes + keybox.
  Texte : titre spécifique + 3×8 mots + 1 phrase clé.
  Idéal pour : ancrer une interprétation sur une donnée.
  Effort : faible (figure existe).

Option C — 2 slides : "le problème" puis "ce qu'on a trouvé"
  Slide 1 : illustration plein cadre (carte du Burundi, libre Wikimedia)
            + une phrase de question.
  Slide 2 : votre figure de résultat + une phrase de réponse.
  Idéal pour : effet rhétorique question/réponse.
  Effort : faible.
```

**Contrainte obligatoire** : parmi les 2 à 3 options proposées, **au moins une** doit reposer sur une *signature visuelle forte* (schéma TikZ original, big number éditorial, image plein cadre avec overlay, frise stylisée, métaphore graphique, isotype data viz). Ne jamais ne proposer que des variantes « titre + colonnes de texte » : c'est ce qui rend un deck oubliable.

**Référence éditoriale explicite** : citer pour chaque option une *inspiration* visuelle, sans copier. Cela aide l'utilisateur à se projeter avant production :

- *NYT Graphics*, typographie éditoriale, hiérarchie forte, palette restreinte.
- *Pudding (pudding.cool)*, narration visuelle, sparklines, micro-cartes.
- *Bloomberg Graphics*, densité maîtrisée, slope charts, small multiples.
- *Nature Methods / Communications*, sobriété scientifique, micro-légendes.
- *Information is Beautiful*, métaphores graphiques fortes pour publics mixtes.
- *IPCC AR6 figures*, communication de données complexes au grand public.
- *Edward Tufte*, sparklines, small multiples, ratio données/encre maximal.
- *FT Visual Journalism*, annotations dans la figure, pas en légende externe.

Format des options (gabarit interne, à adapter) :

```
Option A — Frise chronologique (1 slide)
  Forme : timeline TikZ horizontale, 5 jalons, icônes par jalon.
  Texte : titre informatif + 5 dates + 1 mot-clé par date.
  Inspiration : Pudding / FT Visual Journalism (annotations inline).
  Idéal pour : montrer l'évolution d'un concept ou d'une lignée.
  Effort : moyen (TikZ à écrire mais squelette standard).

Option B — Big number + sparkline (1 slide, signature visuelle forte)
  Forme : « 73 % » plein cadre, sparkline 2008-2024 en dessous, keybox.
  Texte : titre + 1 chiffre + 1 phrase de contexte + n=412.
  Inspiration : Bloomberg, NYT Graphics.
  Idéal pour : un résultat marquant à imprimer dans l'esprit.
  Effort : faible.

Option C — Split figure + 3 take-aways
  Forme : colonne gauche figure existante simplifiée
          (figures/ml_tree_lineage4.pdf), colonne droite 3 puces
          + keybox interprétative.
  Texte : titre spécifique + 3×8 mots + 1 phrase clé.
  Inspiration : Nature Methods.
  Idéal pour : ancrer une interprétation sur une donnée.
  Effort : faible (figure existe).
```

Conclure par une **recommandation explicite** (« je suggère B, car... ») et inviter à choisir, mélanger, ou rediriger.

Si l'utilisateur a explicitement demandé à ne pas être interrompu, choisir l'option recommandée et l'annoncer en une phrase avant de produire.

### Phase 4 : Choix et arbitrages

Une fois l'option retenue, verrouiller les paramètres :
- **Figure définitive** : chemin local exact, ou plan de production (« je vais lancer `sci-figure` sur `data/lineage_counts.csv` pour produire un barplot horizontal »).
- **Image web définitive** : URL + licence + attribution à mettre en pied de slide.
- **Palette** : 3 à 5 couleurs maximum, cohérentes avec le deck hôte.
- **Aspect ratio** : 16:9 par défaut, 4:3 si le deck l'impose.

### Phase 5 : Produire

#### 5.1 : Format de sortie

Par défaut : **Beamer/LaTeX** (un fragment `.tex` que l'utilisateur peut `\input{}` ou copier-coller). Demander si l'utilisateur préfère :
- Un fichier `.tex` autonome compilable (pour test en isolation),
- Un fragment à insérer (par défaut),
- Un `.pptx` (déléguer alors au skill `pptx`),
- Une exportation PDF/PNG d'une slide unique (compiler puis convertir).

#### 5.2 : Patrons techniques utilisables

S'inspirer des patrons déjà documentés dans le skill `beamer-slides` (colonnes, `keybox`, titre informatif, etc.). Ajouter ici les patrons spécifiques à ce skill :

**Frise chronologique TikZ minimaliste** :

```latex
\begin{frame}{Titre informatif et spécifique}
\centering
\begin{tikzpicture}[x=2.4cm,y=1cm,
  every node/.style={font=\footnotesize}]
  \draw[-{Latex[length=3mm]},line width=1pt]
    (0,0) -- (5.4,0);
  \foreach \x/\year/\label in {
      0/1882/{Découverte},
      1/1944/{Streptomycine},
      2/1993/{Urgence OMS},
      3/2006/{XDR-TB},
      4/2024/{Bedaquiline+}} {
    \filldraw (\x,0) circle (2pt);
    \node[above=4pt] at (\x,0) {\textbf{\year}};
    \node[below=8pt,align=center,text width=2.2cm] at (\x,0) {\label};
  }
\end{tikzpicture}
\vspace{6pt}
\kb{La résistance suit la pression antibiotique.}
\end{frame}
```

**Quadrant / matrice 2×2 TikZ** :

```latex
\begin{frame}{Deux axes, quatre profils}
\centering
\begin{tikzpicture}[font=\small]
  \draw[->] (-3.4,0) -- (3.4,0) node[right]{Axe X};
  \draw[->] (0,-2.2) -- (0,2.6) node[above]{Axe Y};
  \node at ( 1.7, 1.3) {\textbf{Profil A}};
  \node at (-1.7, 1.3) {\textbf{Profil B}};
  \node at (-1.7,-1.3) {\textbf{Profil C}};
  \node at ( 1.7,-1.3) {\textbf{Profil D}};
\end{tikzpicture}
\end{frame}
```

**Schéma de workflow (boîtes + flèches)** :

```latex
\begin{frame}{Pipeline d'analyse}
\centering
\begin{tikzpicture}[
  node distance=1.1cm and 1.2cm,
  box/.style={draw,rounded corners=2pt,minimum width=2.4cm,
              minimum height=0.9cm,align=center,font=\footnotesize},
  arr/.style={-{Latex[length=2.5mm]},line width=0.7pt}]
  \node[box] (d) {Données\\brutes};
  \node[box,right=of d] (p) {Pré-traitement};
  \node[box,right=of p] (a) {Analyse};
  \node[box,right=of a] (r) {Résultats};
  \draw[arr] (d) -- (p);
  \draw[arr] (p) -- (a);
  \draw[arr] (a) -- (r);
\end{tikzpicture}
\end{frame}
```

**Image plein cadre + une phrase** (pour rhétorique) :

```latex
{
\setbeamercolor{background canvas}{bg=black}
\setbeamercolor{normal text}{fg=white}
\begin{frame}[plain]
\centering
\includegraphics[width=\paperwidth,height=\paperheight,
  keepaspectratio]{figures/image_pleine.jpg}
\vfill
{\Large\bfseries Une question. Une seule.}
\vfill
{\tiny Crédit : Wikimedia Commons, CC-BY-SA 4.0}
\end{frame}
}
```

**Slide « big number »** (pour un résultat marquant) :

```latex
\begin{frame}[standout]
\centering
{\fontsize{60pt}{72pt}\selectfont\bfseries 73\,\%}\\[8pt]
{\Large des isolats portent la même mutation}\\[14pt]
{\footnotesize n=412, lignée 4, période 2008--2024}
\end{frame}
```

**Big number + sparkline** (signature éditoriale forte) :

```latex
\begin{frame}{Une mutation devient dominante}
\centering
\begin{tikzpicture}
  \node[anchor=south,font=\fontsize{72pt}{82pt}\bfseries] (n) at (0,0) {73\,\%};
  \node[anchor=north,font=\large] at (n.south) {des isolats portent rpoB-S450L};
  % sparkline
  \begin{scope}[yshift=-2.6cm,xshift=-3cm]
    \draw[gray!40,line width=0.4pt] (0,0) -- (6,0);
    \draw[Maroon,line width=1.2pt] plot[smooth] coordinates
      {(0,0.1) (0.6,0.15) (1.2,0.25) (1.8,0.4) (2.4,0.55)
       (3.0,0.65) (3.6,0.85) (4.2,1.1) (4.8,1.3) (5.4,1.55) (6,1.7)};
    \node[font=\footnotesize,anchor=north] at (0,0) {2008};
    \node[font=\footnotesize,anchor=north] at (6,0) {2024};
  \end{scope}
\end{tikzpicture}\\[4pt]
{\footnotesize n=412 isolats, lignée 4 / Burundi 2008--2024}
\end{frame}
```

**Iceberg métaphore** (visible / invisible) :

```latex
\begin{frame}{La part déclarée n'est qu'un dixième}
\centering
\begin{tikzpicture}[scale=1.1]
  % ligne d'eau
  \draw[blue!15,line width=14pt] (-5,0) -- (5,0);
  % partie émergée
  \fill[white,draw=gray!40,line width=0.6pt]
    (-1.2,0) -- (-0.6,1.6) -- (0.4,1.9) -- (1.0,1.2) -- (1.4,0) -- cycle;
  \node[font=\small,align=center] at (0.0,1.0) {Cas\\déclarés};
  % partie immergée
  \fill[blue!15,draw=blue!30,line width=0.4pt]
    (-1.8,0) -- (-2.8,-1.0) -- (-2.3,-2.4) -- (-0.6,-3.2)
    -- (1.4,-3.4) -- (2.6,-2.6) -- (3.2,-1.4) -- (2.0,0) -- cycle;
  \node[font=\small,align=center,white] at (0.2,-1.9) {Cas non détectés\\ ($\sim$3 millions/an)};
\end{tikzpicture}\\[6pt]
{\footnotesize OMS Global TB Report 2023.}
\end{frame}
```

**Concept map en étoile** (concept central, 5 rayons) :

```latex
\begin{frame}{Cinq forces façonnent la diversité MTBC}
\centering
\begin{tikzpicture}[
  node distance=2.2cm,
  central/.style={circle,fill=Maroon!85,text=white,minimum size=2cm,
                  font=\small\bfseries,align=center},
  branche/.style={rectangle,rounded corners=2pt,fill=gray!10,
                  draw=gray!40,minimum width=2.4cm,font=\footnotesize,
                  align=center,inner sep=4pt}]
  \node[central] (c) {Diversité\\MTBC};
  \foreach \angle/\nom in {90/Migrations,162/Co-évolution,234/Antibiotiques,306/Démographie,18/Climat} {
    \node[branche] (\nom) at (\angle:3.4) {\nom};
    \draw[gray!50,line width=0.5pt] (c) -- (\nom);
  }
\end{tikzpicture}
\end{frame}
```

**Comparaison side-by-side avec règle typographique** :

```latex
\begin{frame}{Avant et après le passage de Koch}
\begin{columns}[T,onlytextwidth]
\begin{column}{0.46\textwidth}
  \textcolor{gray!70}{\footnotesize\textsc{Avant 1882}}\\[2pt]
  \textbf{Phtisie} : maladie héréditaire,\\ familles « scrofuleuses »,
  cause humorale.\\[6pt]
  \emph{Pas de germe identifié.}
\end{column}
\begin{column}{0.04\textwidth}\centering
  \tikz\draw[gray!40,line width=0.6pt] (0,0) -- (0,-3);
\end{column}
\begin{column}{0.46\textwidth}
  \textcolor{Maroon!80}{\footnotesize\textsc{Après 1882}}\\[2pt]
  \textbf{Tuberculose} : maladie infectieuse,
  agent \emph{Mycobacterium tuberculosis}, transmission aérienne.\\[6pt]
  \emph{La phtisiologie devient bactériologie.}
\end{column}
\end{columns}
\end{frame}
```

**Section divider plein cadre** (rupture narrative) :

```latex
{
\setbeamercolor{background canvas}{bg=NavyBlue!90!black}
\setbeamercolor{normal text}{fg=white}
\begin{frame}[plain]
\vfill
\centering
{\fontsize{10pt}{12pt}\selectfont\textcolor{white!60!NavyBlue}{\textsc{Partie\,III}}}\\[14pt]
{\fontsize{34pt}{40pt}\selectfont\bfseries Phylogéographie\\ d'une expansion}\\[18pt]
{\fontsize{14pt}{18pt}\selectfont\itshape Reconstruire l'itinéraire d'une lignée}
\vfill
\end{frame}
}
```

**Pull quote éditorial** (citation à fort impact) :

```latex
\begin{frame}{}
\vfill
\centering
\begin{tikzpicture}
  \node[font=\fontsize{180pt}{200pt}\selectfont,
        text=Maroon!20,anchor=north west] (q) at (-5,1.8) {\guillemotleft};
  \node[text width=8cm,align=center,
        font=\Large\itshape] at (0,0)
        {Une mutation peut faire la fortune\\ d'une bactérie autant
         qu'une catastrophe\\ écologique fait la fortune d'un mammifère.};
  \node[font=\footnotesize\scshape] at (0,-2.5) {Stephen J. Gould, 1989};
\end{tikzpicture}
\vfill
\end{frame}
```

**Bacille MTBC stylisé** (icône thématique réutilisable) :

```latex
\begin{frame}{Mycobacterium tuberculosis}
\centering
\begin{tikzpicture}[scale=1.3]
  % capsule
  \shade[top color=Maroon!55,bottom color=Maroon!90,
         draw=Maroon!90,line width=0.5pt]
    (-2,0) arc[start angle=90,end angle=270,x radius=0.5,y radius=0.5]
    -- (2,-0.5) arc[start angle=270,end angle=90,x radius=0.5,y radius=0.5]
    -- cycle;
  % stries (paroi acido-alcoolo-résistante)
  \foreach \x in {-1.6,-1.2,...,1.6} {
    \draw[white!60!Maroon,line width=0.3pt] (\x,-0.45) -- (\x,0.45);
  }
\end{tikzpicture}\\[12pt]
{\small Bacille acido-alcoolo-résistant, 2--4 µm, croissance lente
($\tau \approx$ 18 h)}
\end{frame}
```

**Flux Sankey simplifié** (3 origines → 2 destinations) :

```latex
\begin{frame}{Flux migratoires reconstruits}
\centering
\begin{tikzpicture}[
  x=1.0cm,y=0.5cm,
  src/.style={rectangle,fill=#1,minimum width=1.2cm,minimum height=#2*0.4cm,
              anchor=west},
  dst/.style={rectangle,fill=#1,minimum width=1.2cm,minimum height=#2*0.4cm,
              anchor=east}]
  \node[src={NavyBlue!70}{6}] (s1) at (0,4) {};
  \node[src={NavyBlue!70}{3}] (s2) at (0,1) {};
  \node[src={NavyBlue!70}{2}] (s3) at (0,-1) {};
  \node[dst={Maroon!70}{7}] (d1) at (8,3.5) {};
  \node[dst={Maroon!70}{4}] (d2) at (8,0) {};
  \foreach \s/\d/\op in {s1/d1/.7,s1/d2/.3,s2/d1/.5,s2/d2/.5,s3/d2/.9} {
    \draw[NavyBlue!40,line width=4pt,opacity=\op]
      (\s.east) to[out=0,in=180] (\d.west);
  }
  \node[font=\footnotesize,anchor=east] at (s1.west) {Asie};
  \node[font=\footnotesize,anchor=east] at (s2.west) {Afrique};
  \node[font=\footnotesize,anchor=east] at (s3.west) {Europe};
  \node[font=\footnotesize,anchor=west] at (d1.east) {L4 moderne};
  \node[font=\footnotesize,anchor=west] at (d2.east) {L2 Beijing};
\end{tikzpicture}
\end{frame}
```

**Stat callout en petite multiple** (3 chiffres alignés) :

```latex
\begin{frame}{Trois résultats clés}
\centering
\begin{tikzpicture}[
  card/.style={rectangle,rounded corners=4pt,
               draw=gray!30,line width=0.5pt,
               minimum width=3.5cm,minimum height=3.5cm,
               inner sep=8pt,align=center}]
  \node[card] (a) at (-4.2,0)
    {{\fontsize{32pt}{36pt}\selectfont\bfseries 412}\\[4pt]
     {\footnotesize isolats séquencés}};
  \node[card] (b) at (0,0)
    {{\fontsize{32pt}{36pt}\selectfont\bfseries 14}\\[4pt]
     {\footnotesize sites d'échantillonnage}};
  \node[card] (c) at (4.2,0)
    {{\fontsize{32pt}{36pt}\selectfont\bfseries 6\,200\,a.}\\[4pt]
     {\footnotesize MRCA estimé}};
\end{tikzpicture}
\end{frame}
```

**Arbre phylogénétique stylisé minimal** (silhouette, pas vraies branches) :

```latex
\begin{frame}{Quatre lignées, quatre histoires}
\centering
\begin{tikzpicture}[
  leaf/.style={font=\footnotesize,anchor=west},
  scale=0.9]
  \draw[line width=1pt] (0,0) -- (3,2);
  \draw[line width=1pt] (0,0) -- (3,1);
  \draw[line width=1pt] (0,0) -- (3,-1);
  \draw[line width=1pt] (0,0) -- (3,-2);
  \node[leaf,text=Maroon] at (3,2)   {L1 — Indien océanique};
  \node[leaf,text=NavyBlue] at (3,1)   {L2 — Beijing};
  \node[leaf,text=OliveGreen] at (3,-1) {L4 — euro-américaine};
  \node[leaf,text=Purple] at (3,-2)  {L5/L6 — africaine de l'Ouest};
  \node[font=\footnotesize\itshape,anchor=east] at (0,0) {MRCA $\sim$6\,000 a.};
\end{tikzpicture}
\end{frame}
```

**Carte stylisée + bulles proportionnelles** (déléguer à `geo-map`) :

Ne **jamais** reproduire une carte à la main dans TikZ. Pour toute slide impliquant une géographie réelle, appeler `geo-map` (cf. §Sous-agents) avec `--style bubble` ou `--style choropleth`, exporter en `.pdf`, puis l'inclure :

```latex
\begin{frame}{Concentration des cas dans la corne de l'Afrique}
\centering
\includegraphics[width=0.95\textwidth]{figures/carte_corneAfrique.pdf}\\[4pt]
{\footnotesize Source : production locale `geo-map`, palette MTBC, Robinson.}
\end{frame}
```

#### 5.3 : Vérifications avant livraison

- [ ] Titre **spécifique** (pas « Résultats », pas « Méthodologie »), il dit ce que la slide démontre.
- [ ] Mot-compte raisonnable (< 40 mots visibles hors titre dans 90 % des cas).
- [ ] Si figure : axes lisibles, légende explicite, source / n indiqué.
- [ ] Si image web : licence + crédit visibles en pied de slide.
- [ ] Si insertion dans deck existant : compilation testée avec le préambule réel (au minimum signaler les `\usepackage` requis).
- [ ] Aucun `\input{}` cassé, aucun chemin de figure invalide.
- [ ] Sortie compile : `pdflatex -interaction=nonstopmode` sans erreur (si fichier autonome demandé).

#### 5.4 : Boucle preview + critique visuelle (obligatoire)

C'est l'étape qui distingue un slide *livré* d'un slide *décevant*. **Ne jamais sauter cette boucle**, même quand l'utilisateur a demandé à ne pas être interrompu : ce n'est pas une question, c'est de la production.

1. **Compiler le fragment en standalone** dans un dossier temporaire :

```bash
mkdir -p /tmp/slide-preview && cd /tmp/slide-preview
cat > slide.tex <<'EOF'
\documentclass[aspectratio=169]{beamer}
\usetheme{metropolis}        % ou le theme du deck hôte
\usepackage{fontawesome5}
\usepackage[dvipsnames]{xcolor}
\usetikzlibrary{arrows.meta,positioning,fit,backgrounds,
                shadows.blur,fadings,decorations.pathreplacing,
                decorations.markings,calc,shapes.geometric}
\begin{document}
\input{fragment.tex}
\end{document}
EOF
xelatex -interaction=nonstopmode slide.tex >/dev/null
```

2. **Convertir en PNG haute résolution** :

```bash
pdftoppm -r 200 slide.pdf preview -png
```

3. **Lire le PNG** avec l'outil `Read` (capacité multimodale) et **critiquer visuellement** selon la grille suivante. Chaque point se répond par oui/non :

   - **Point focal unique** : l'œil sait où atterrir en moins d'1 seconde ?
   - **Titre informatif** : le titre énonce l'argument, pas la catégorie ?
   - **Hiérarchie typo** : trois grandeurs maximum, contraste clair ?
   - **Densité** : moins de 3 zones d'information par cm² ?
   - **Alignement** : tous les éléments accrochés à la grille 12 colonnes ?
   - **Palette respectée** : pas plus de 5 couleurs ? Ratio 60/30/10 tenu ?
   - **Contraste de lecture** : texte sur fond passant WCAG AA ?
   - **Crédit visible** : si image web, attribution lisible au pied ?
   - **Pas de gras / italique gratuit** : seulement quand sémantiquement nécessaire ?
   - **Pas de typo défaut Beamer** (sans-serif uniforme grise) : un système typographique a-t-il bien été activé ?

4. **Si un seul point faillit, itérer.** Modifier le fragment, recompiler, re-critiquer. Une à trois itérations sont attendues.

5. **Livraison finale** : ne pointer l'utilisateur vers le `.tex` *que* après cette boucle. Joindre le PNG d'aperçu dans la réponse pour que l'utilisateur puisse juger sans recompiler.

**Cas particulier, figure générée par sous-agent** (`geo-map`, `sci-figure`, etc.) : ouvrir le PDF de la figure pour vérifier *avant* de l'intégrer. Une figure laide dans un slide propre reste un slide laid.

## Sous-agents et délégation

Ce skill **délègue activement** quand un autre skill est mieux placé. Schéma de décision :

| Besoin | Skill à invoquer (via `Skill` ou via `Agent` en sous-agent) |
|--------|-------------------------------------------------------------|
| Produire un graphique scientifique depuis un CSV | `sci-figure` (preset `slide`, ou celui de la revue si la figure ressert dans l'article) |
| Carte géographique (monde, région, pays, distribution spatiale) | **`geo-map` (toujours)**, ne jamais redessiner une carte à la main |
| Arbre phylogénétique réel à afficher | `iqtree-lsd2`, `itol`, puis export PDF inclus |
| Sortie `.pptx` au lieu de Beamer | `pptx` |
| Le deck hôte est un `.pptx` à analyser pour calquer le style | `pptx` (lecture + extraction layouts) |
| Le contenu factuel doit être vérifié (chiffres, dates) | `claim-check` |
| Une revue de littérature courte pour produire une slide « contexte » | `lit-review` |
| Un thème Beamer spécifique demandé | `theme-factory` |
| Une figure existe en LaTeX TikZ et doit être resimplifiée | délégation manuelle, sans skill dédié |
| Conversion d'un PDF de figure en png inclusible | `pdftoppm -png -r 200 fig.pdf fig` (ou `pdftocairo -png -singlefile`) |

Règle : **un seul niveau de délégation** par défaut. Si plusieurs skills sont nécessaires, les enchaîner explicitement et tracer le résultat de chaque sous-agent.

## Exemples d'invocation typiques

**Cas 1 : Slide unique pour réunion d'équipe**
> « Fais-moi une slide qui montre que la lignée 4.6.1.2 est sur-représentée au Burundi par rapport au Bénin. »

Cadrer : 1 slide, pairs spécialistes, FR, inséré dans deck Beamer local.
Inventorier : chercher `figures/lineage_*.pdf` dans le projet courant.
Proposer : (A) barplot horizontal des proportions par pays, (B) carte choroplèthe stylisée, (C) split barplot + keybox interprétative.
Choisir : (selon l'utilisateur).
Produire : fragment `.tex`.

**Cas 2 : Deux slides « contexte » pour vulgarisation**
> « J'introduis la tuberculose à un public non spécialiste, 2 slides. »

Cadrer : 2 slides, grand public, FR, autonome.
Inventorier : aucune figure de projet ; envisager photo d'Hippocrate / Koch / radiographie thoracique depuis Wikimedia.
Proposer : (A) frise historique 1 slide + slide « chiffres-clés » ; (B) image pleine + slogan, puis carte mondiale d'incidence ; (C) métaphore visuelle (iceberg : cas déclarés / non déclarés).
Choisir, produire.

**Cas 3 : Insertion dans deck PowerPoint existant**
> « Voici `presentation_jury.pptx`, j'ai besoin d'insérer une slide entre la 12 et la 13 qui explique le principe du goodness-of-fit RAxML. »

Cadrer : 1 slide, jury HDR, FR, deck `.pptx` existant.
Inventorier : déléguer à `pptx` pour extraire le master/layout/couleurs.
Proposer : (A) schéma TikZ « arbre observé vs arbre attendu sous H0 » + une phrase, (B) split formule + diagramme, (C) icône + 3 puces clés.
Choisir, produire au format `.pptx` via le skill `pptx` pour respecter le master.

## Exemples avant / après

Trois cas représentatifs où une formulation pauvre devient un slide de qualité éditoriale.

**Cas 1 : Titre indistinct → titre argumentatif**

| Avant | Après |
|-------|-------|
| « Résultats » | « rpoB-S450L porte 73 % de la résistance, et sa fréquence double tous les 8 ans » |

Le titre *est* l'argument. Le corps de slide ne fait que l'illustrer.

**Cas 2 : Trois colonnes de puces → big number + sparkline**

| Avant | Après |
|-------|-------|
| 3 colonnes × 5 puces de 12 mots chacune | Big number « 73 % » plein cadre + sparkline 2008-2024 + n=412 |

Le slide perd 150 mots, gagne en mémorisation.

**Cas 3 : Carte « monde + ronds » faite à la main → délégation `geo-map`**

| Avant | Après |
|-------|-------|
| TikZ artisanal, frontières approximatives, ronds non échelle | `geo-map --preset nature_double --style bubble --palette mtbc`, palette canonique, projection Robinson, légende propre |

Un slide qui contient une carte mal dessinée perd toute crédibilité scientifique.

## Anti-patrons à éviter

1. **Le mur de texte caché en « slide propre »** : 5 puces de 15 mots chacune sur deux colonnes, c'est un mur.
2. **Le schéma décoratif** : un TikZ joli mais qui ne porte aucun message. Si on peut le retirer sans rien perdre, on le retire.
3. **L'image générique** : photo de stock « équipe diverse devant un écran » pour illustrer la science. Toujours mieux : rien.
4. **Le surplus de licences** : trois images web différentes sur une même slide. Une suffit.
5. **L'oubli du style hôte** : utiliser Metropolis dans un deck Berkeley fuchsia. Toujours lire le préambule avant.
6. **Le « je propose tout de suite »** : sauter la phase 3 et produire directement une option unique. L'utilisateur perd l'arbitrage.
7. **L'invention de données** : si la slide affiche un chiffre, il doit venir d'une source identifiable (figure locale, CSV, article cité). Sinon, demander.

## Format des sorties à coller

L'utilisateur a parfois besoin de copier-coller le fragment dans Overleaf ou un éditeur. Respecter alors les règles globales :
- Fragment LaTeX bien indenté, pas de lignes trop longues, prêt à `\input{}`.
- Si l'utilisateur demande explicitement un texte à coller dans un formulaire web (résumé de la slide, par exemple), suivre les règles de la section « Format des sorties à copier-coller » de l'instruction globale (une ligne par paragraphe, pas d'indentation).

## Galerie de références visuelles

À consulter mentalement (et à citer en Phase 3 pour fixer un imaginaire commun avec l'utilisateur) :

- **NYT Graphics** (`nytimes.com/spotlight/graphics`), référence absolue en typographie éditoriale et hiérarchie. Voir notamment leurs *small multiples* et leurs *annotated charts*.
- **Pudding** (`pudding.cool`), narration visuelle, sparklines, micro-cartes, scrollytelling. Pour les slides qui doivent *raconter*.
- **Bloomberg Graphics**, densité élevée mais hiérarchie nette. Excellents *slope charts*.
- **FT Visual Journalism**, annotations *dans* la figure plutôt qu'en légende externe. Modèle pour les cartes thématiques.
- **Reuters Graphics**, sobre, fonctionnel, légendes condensées.
- **Information is Beautiful** (David McCandless), métaphores visuelles fortes, public mixte.
- **Nature Methods / Communications**, sobriété scientifique, micro-légendes, ratio donnée/encre élevé.
- **IPCC AR6 figures**, communication de données complexes pour publics non spécialistes.
- **Edward Tufte**, *Beautiful Evidence*, *Visual Display of Quantitative Information*. Sparklines, small multiples.
- **Stefanie Posavec / Giorgia Lupi** (*Dear Data*), pour la métaphore graphique au-delà de l'orthodoxie chart-bar.
- **ColorBrewer** (`colorbrewer2.org`), pour fixer une palette adaptée à un usage cartographique précis.

Ne pas copier : citer l'esprit. La copie d'un style éditorial sans en comprendre la logique produit un pastiche.

## Résumé du skill

Un slide réussi est un objet **visuel pensé** : l'idée, choisie ; la forme, justifiée ; la matière, trouvée (locale, créée, ou empruntée avec attribution) ; le style, cohérent avec son contexte ; le texte, réduit à l'essentiel ; **et chaque sortie est visualisée puis critiquée avant d'être livrée**. Le rôle du skill est de garantir ces six propriétés à chaque appel, en proposant plusieurs chemins avant d'en choisir un et en bouclant sur l'aperçu.
