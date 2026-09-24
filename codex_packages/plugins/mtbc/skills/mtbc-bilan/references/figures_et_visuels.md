# Cartes, schemas et figures du bilan -- version integrale

Reference de `mtbc-bilan` : texte integral de la section 9.1ter. Reutilisation
des figures de l'article, appel canonique a `geo-map`, patterns TikZ (carte de
fallback, schema de mecanisme, chronologie, arbre simplifie), grille de choix
reutilisation / generation, regles de qualite.

### 9.1ter Cartes, schemas et figures

Un bilan n'est pas un texte plat. Les visuels (cartes, schemas
mecanistiques, chronologies, arbres simplifies, diagrammes conceptuels)
ameliorent significativement la comprehension d'un lecteur de formation
math/info, qui ne dispose pas des images mentales que le specialiste
forme spontanement.

**Principe** : ne pas hesiter a piocher dans le materiel de l'article ET
a generer des visuels de novo specifiquement pour le bilan. Les figures
de l'article sont concues pour un public expert ; le bilan a besoin en
plus de figures pedagogiques (cartes situant la lignee, schemas du
mecanisme biologique invoque, chronologies replacant l'etude dans
l'histoire de la litterature...).

**Cible quantitative** : 4 a 10 visuels par bilan, dont au minimum
**2 generes specifiquement** pour le bilan (au-dela de la simple
reutilisation de l'article). Si le projet a une dimension geographique
(distribution mondiale, regionale, ou GPS), **au moins une carte
produite via `geo-map`** est obligatoire -- une carte schematique TikZ
ne remplace pas une vraie carte cartographique pour discuter
distribution de lignee, foyer ancestral, ou flux phylogeographiques.

#### A. Reutilisation des figures de l'article

Les templates definissent un `\graphicspath` qui inclut
`../article/figures/`, `../resultats/`, et `./figures/` (relatif au
fichier `.md` du bilan). On peut donc inclure directement par le nom de
fichier (sans le chemin) :

````markdown
```{=latex}
\begin{figure}[H]
  \centering
  \includegraphics[width=0.85\textwidth]{phylogeo_L4_2.pdf}
  \caption{Distribution geographique de proto-L4.2 (412 souches,
    23 pays). Les couleurs codent les sous-clades identifies par
    \textit{lineage-subdivision}. Reproduit de l'article (figure 2).}
  \label{fig:bilan-phylogeo}
\end{figure}
```
````

Selectionner pour le bilan :
- 1-2 figures cles de l'article qui resument visuellement les
  decouvertes principales
- Les figures qui appellent une explication pedagogique (souvent celles
  qu'un reviewer demanderait de simplifier)

Ne pas reproduire mecaniquement TOUTES les figures de l'article -- le
bilan est une selection commentee, pas un duplicata.

#### B. Generation de novo : carte de situation

Quand le projet implique une dimension geographique (lignees regionales,
ecotypes, distribution de souches), une carte aide enormement. **Le
mode par defaut est l'appel au skill `geo-map`** : il produit des
cartes Natural Earth en projection cartographique correcte (Robinson,
Albers, Lambert selon la region), avec ocean, lacs, frontieres, barre
d'echelle, et palette MTBC standardisee. La carte schematique TikZ ne
sert qu'en cas de fallback (pas de donnees geocodees disponibles, ou
besoin tres simplifie).

**Appel canonique a `geo-map` depuis le bilan** :

1. Extraire les donnees du cahier ou des BDD en CSV minimal :
   `country,n` ou `country,lineage,n` ou `lat,lon,lineage`.
2. Lancer `geo-map` en mode approprie, sortie en PDF vectoriel place
   dans `<projet>/bilans/figures/` (creer le dossier si absent) :

   ```bash
   # Cas typique : distribution mondiale d'une lignee
   python3 /home/christophe/docs/environnement/plugins/science-commun/skills/geo-map/scripts/geo_map.py \
     bilans/data/proto-L4.2-countries.csv \
     -t choropleth -v n --log-scale \
     --region world --preset generic \
     --insets auto --smart-labels fast \
     --title "Distribution mondiale de proto-L4.2 (412 souches, 23 pays)" \
     -o bilans/figures/fig-distrib-mondiale.pdf

   # Cas regional avec relief : L5 en Afrique
   python3 /home/christophe/docs/environnement/plugins/science-commun/skills/geo-map/scripts/geo_map.py \
     bilans/data/L5-africa.csv -t choropleth -v n \
     --region africa --hillshade --show-tropics \
     --title "L5 en Afrique sub-saharienne" \
     -o bilans/figures/fig-L5-afrique.pdf

   # Sites d'echantillonnage GPS par sous-lignee
   python3 /home/christophe/docs/environnement/plugins/science-commun/skills/geo-map/scripts/geo_map.py \
     bilans/data/samples-gps.csv -t points \
     --lat-col lat --lon-col lon -g sublineage \
     --region southeast_asia --show-cities --min-pop 2000000 \
     --title "Sites d'echantillonnage L1 -- Asie du Sud-Est" \
     -o bilans/figures/fig-samples-l1.pdf
   ```

3. Inclure le PDF generemnt dans le bilan via `\includegraphics`,
   avec une caption argumentee (3-5 lignes) qui explique ce que le
   lecteur doit y voir et pourquoi.

**Cas ou `geo-map` est l'appel correct** :

- Distribution d'une lignee par pays (choropleth).
- Composition en sous-lignees par pays (pie chart map).
- Sites d'echantillonnage GPS individuels (points).
- Flux phylogeographiques entre regions (arcs, ex : reconstruction
  BEAST 2 discrete trait).
- Comparaison entre lignees / periodes (multi-panel facet).
- Composition complexe (choropleth + points + arcs en `layered`).

**Fallback TikZ schematique** : reserve aux cas ou aucune donnee
geocodee n'existe (ex : carte purement illustrative d'un texte ancien)
ou ou un effet stylistique simplifie est volontairement recherche.
Quand on l'utilise, le mentionner explicitement dans la caption
("Carte schematique, non a l'echelle.").

**Exemple TikZ de fallback** (Afrique avec bulles) :

````markdown
```{=latex}
\begin{figure}[H]
\centering
\begin{tikzpicture}[scale=0.9]
  % Contour simplifie de l'Afrique (polygone schematique)
  \draw[fill=lightgray!40, draw=darkgray, thick]
    (0,0) -- (2,0.3) -- (3.5,0) -- (4,1.5) -- (4.5,3) --
    (4,4.5) -- (3,5.5) -- (1.5,5.8) -- (0,5) --
    (-0.5,3.5) -- (-0.5,1.5) -- cycle;
  % Repere lat/lon approximatif
  \node[font=\tiny, midgray] at (3.5,4.8) {N};
  \node[font=\tiny, midgray] at (-0.3,0.3) {S};
  % Pays cles (positions schematiques)
  \node[font=\scriptsize, darkgray] at (1.0,4.5) {Senegal};
  \node[font=\scriptsize, darkgray] at (1.7,3.8) {Mali};
  \node[font=\scriptsize, darkgray] at (2.4,3.5) {Burkina};
  \node[font=\scriptsize, darkgray] at (3.0,3.2) {Nigeria};
  \node[font=\scriptsize, darkgray] at (3.5,2.0) {RDC};
  \node[font=\scriptsize, darkgray] at (3.0,0.5) {Afrique du Sud};
  % Bulles : taille proportionnelle au nombre de souches
  \fill[notioncolor, opacity=0.55] (1.2,4.4) circle (8pt);
  \fill[notioncolor, opacity=0.55] (1.8,3.7) circle (12pt);
  \fill[notioncolor, opacity=0.55] (2.5,3.5) circle (6pt);
  \fill[notioncolor, opacity=0.55] (3.1,3.1) circle (15pt);
  % Legende
  \node[font=\footnotesize, anchor=north west]
    at (5.5,5) {\textbf{N souches L5}};
  \fill[notioncolor, opacity=0.55] (5.7,4.2) circle (4pt);
  \node[font=\scriptsize, anchor=west] at (6,4.2) {< 10};
  \fill[notioncolor, opacity=0.55] (5.7,3.6) circle (8pt);
  \node[font=\scriptsize, anchor=west] at (6,3.6) {10--50};
  \fill[notioncolor, opacity=0.55] (5.7,3.0) circle (12pt);
  \node[font=\scriptsize, anchor=west] at (6,3.0) {50--150};
\end{tikzpicture}
\caption{Distribution schematique des souches L5 dans le corpus.
  Les bulles sont proportionnelles au nombre de souches par pays.
  Carte simplifiee, non a l'echelle.}
\label{fig:bilan-carte-l5}
\end{figure}
```
````

**Carte plus precise** : si le projet a un fichier shapefile ou des
coordonnees lat/lon, prefer un `pgfplots` avec `axis equal` et un
nuage de points sur fond uni, ou inclure directement une figure
generee par python (`cartopy`, `geopandas`) si elle est dans
`resultats/` ou `article/figures/`.

**Quand generer une carte de novo** : a chaque fois que la dimension
geographique est evoquee dans le bilan ET qu'aucune carte similaire
n'existe deja dans `article/figures/`. Une simple carte avec 5-10
labels de pays et des bulles aide enormement le lecteur a se reperer.

#### C. Generation de novo : schema de mecanisme biologique

Quand un mecanisme est invoque (selection convergente, retro-mutation,
goulot demographique, transmission inter-hote), un schema TikZ
synthetique vaut mieux qu'un long paragraphe.

````markdown
```{=latex}
\begin{figure}[H]
\centering
\begin{tikzpicture}[
  node distance=1.2cm,
  state/.style={circle, draw=darkgray, fill=lightgray!40,
                minimum size=8mm, font=\small},
  arr/.style={-{Stealth[length=4pt]}, thick}
]
  \node[state] (anc) {A};
  \node[state, right=of anc, fill=notioncolor!20] (mut) {C};
  \node[state, right=of mut, fill=remarquablecolor!30] (rev) {A};
  \draw[arr] (anc) -- node[above, font=\scriptsize]{mutation} (mut);
  \draw[arr, dashed, remarquablecolor] (mut) -- node[above, font=\scriptsize]
    {\textbf{retro-mutation}} (rev);
  \node[font=\scriptsize, midgray, below=4mm of anc]
    {ancetre commun};
  \node[font=\scriptsize, midgray, below=4mm of mut]
    {fixation chez L4.9};
  \node[font=\scriptsize, midgray, below=4mm of rev]
    {retour a l'etat ancestral};
\end{tikzpicture}
\caption{Schema d'une retro-mutation : un SNP fixe (A$\to$C) revient a
  l'etat ancestral (C$\to$A) dans un sous-clade ulterieur. Ce phenomene
  est suppose extremement rare en MTBC du fait de la clonalite et du
  faible taux de mutation.}
\label{fig:bilan-retromutation}
\end{figure}
```
````

#### D. Generation de novo : chronologie / timeline

Pour replacer l'etude dans son contexte historique (decouvertes
successives sur la lignee, evenements demographiques, jalons
methodologiques) :

````markdown
```{=latex}
\begin{figure}[H]
\centering
\begin{tikzpicture}[
  evt/.style={font=\scriptsize, anchor=south, align=center},
  ref/.style={font=\tiny, anchor=north, midgray}
]
  % Axe temps
  \draw[->, thick, accent] (0,0) -- (12,0)
    node[right, font=\small] {temps};
  % Graduations
  \foreach \x/\y in {1/2014, 3/2017, 5/2020, 7/2022, 9/2024, 11/2026} {
    \draw (\x,0.1) -- (\x,-0.1) node[ref]{\y};
  }
  % Evenements (au-dessus)
  \node[evt] at (1,0.2) {Coll \textit{et al.}\\barcode L4};
  \node[evt] at (3,0.2) {Stucki\\dual epidemic};
  \node[evt] at (5,0.2) {Napier\\refinement};
  \node[evt] at (7,0.2) {Freschi\\global tree};
  \node[evt, accent] at (9.5,0.2) {\textbf{Ce projet}\\proto-L4.2 mondiale};
  % Repere visuel sur le projet courant
  \fill[accent] (9.5,0) circle (3pt);
\end{tikzpicture}
\caption{Chronologie des travaux majeurs sur la lignee L4 et
  positionnement de ce projet dans la litterature.}
\label{fig:bilan-chronologie}
\end{figure}
```
````

#### E. Generation de novo : arbre simplifie

Pour illustrer la position d'une lignee dans l'arbre MTBC, ou la
structure interne d'un sous-clade, un arbre TikZ simplifie est plus
lisible qu'un arbre Newick brut.

Utiliser le style `child` natif de TikZ ou la bibliotheque `forest`
si elle est chargee.

````markdown
```{=latex}
\begin{figure}[H]
\centering
\begin{tikzpicture}[
  level distance=12mm,
  level 1/.style={sibling distance=22mm},
  level 2/.style={sibling distance=10mm},
  every node/.style={font=\scriptsize, draw=darkgray,
                     rounded corners=2pt, inner sep=2pt}
]
\node {MTBC}
  child {node {L1-L4 (modern)}
    child {node[fill=accent!15]{\textbf{L4}}}
    child {node {L2}}
    child {node {L1}}
  }
  child {node[fill=notioncolor!15]{\textbf{L5-L6} (West-African)}}
  child {node {L7-L10}}
  child {node {animal-adapted\\(\textit{M. bovis}, \textit{M. caprae}...)}};
\end{tikzpicture}
\caption{Position de la lignee etudiee dans l'arbre MTBC simplifie.
  Adapte de Brites \& Gagneux (2017).}
\label{fig:bilan-arbre-mtbc}
\end{figure}
```
````

#### F. Choix entre reutilisation et generation

| Cas | Action |
|-----|--------|
| L'article a deja une figure qui couvre le point | **Reutiliser** via `\includegraphics` |
| L'article a une figure complexe que le lecteur math/info pourrait mal interpreter | Reutiliser **+ ajouter un schema simplifie** generemnt de novo a cote |
| Le point est purement pedagogique (mecanisme, contexte historique, position dans l'arbre MTBC) | **Generer de novo** en TikZ |
| Carte de situation geographique (pays / regions / GPS / flux) | **Appeler `geo-map`** (skill, sortie PDF vectoriel) -- voir B |
| Visualisation chiffree generique (scatter, histo, barplot) | **Appeler `sci-figure`** (skill, sortie PDF vectoriel) si pas dans `resultats/`, sinon reutiliser |
| Visualisation composite ou non standard (heatmap multi-panel, violin par lignee, courbe ROC...) | **Appeler `sci-figure`** (skill, `panel_grid` multi-panneaux, sortie PDF vectoriel) |
| Arbre phylogenetique simplifie illustratif | TikZ natif (voir E) ou skill `iqtree-lsd2`/`itol` si donnees disponibles |
| Pipeline du projet | Section dediee Phase 9 (deja prevue : TikZ generemnt) |

**Regle generale** : ne jamais reinventer en TikZ schematique ce qu'un
skill d'illustration produit en qualite publication. Les skills
disponibles (canoniques sous ~/docs/environnement/plugins/<plugin>/skills/, resolution exacte dans canon_skills.json) :

| Skill | Usage typique dans un bilan |
|-------|----------------------------|
| `geo-map` | Toutes les cartes (choropleth, points GPS, arcs, layered, multi-panel) |
| `sci-figure` | Distributions, scatter, barplot, boxplot, heatmaps, multi-panneaux ; partage les presets de revue de `geo-map` |
| `itol` | Arbres phylogenetiques annotes |
| `iqtree-lsd2` | Arbres dates (chronogrammes) |

Le bilan **enchaine prose + figures** : a chaque fois qu'un paragraphe
mentionne une donnee qui se visualise mieux qu'elle ne se decrit
(distribution geographique, structure d'arbre, gradient temporel,
distribution numerique), inserer la figure correspondante juste apres
le paragraphe, avec une caption argumentee.

#### G. Regles de qualite

1. **Toute figure a une caption explicative**, pas juste un titre. La
   caption explique ce que le lecteur doit voir et pourquoi c'est
   pertinent (3-5 lignes, pas une simple etiquette).
2. **Toute figure est referencee dans le texte** (`Cf.~\cref{fig:...}`),
   sinon elle ne sert a rien et peut etre supprimee.
3. **Couleurs coherentes** : reutiliser les couleurs definies dans le
   template (`accent`, `notioncolor`, `methodecolor`, `originalitecolor`,
   `remarquablecolor`, `verdictgreen`, `verdictorange`). Ne pas
   introduire de nouvelles couleurs.
4. **Cartes de novo** : preciser explicitement dans la caption que la
   carte est schematique (non a l'echelle), pour eviter toute
   surinterpretation.
5. **Eviter les fichiers raster** sauf si vraiment necessaire (PNG/JPG
   uniquement pour des cartes ou des figures de l'article qui n'existent
   qu'en raster). Privilegier PDF, SVG, et generation TikZ native.
6. **Pas de figures decoratives** : si une figure ne porte pas
   d'information specifique, la supprimer. Le bilan est dense, pas
   illustre.
