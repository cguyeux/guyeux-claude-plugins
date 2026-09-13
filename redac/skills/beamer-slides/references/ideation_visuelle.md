# L'idéation visuelle

## La règle par défaut, inversée

Dans un deck ordinaire, la liste à puces est le défaut et la figure l'exception.
Ici c'est l'inverse : **l'objet visuel est le défaut, la liste doit se
justifier**. La justification s'écrit dans la fiche de la slide, et le contrôle
la relit.

La raison est mesurée : sur neuf decks du parc, aucun graphique de données, et
pourtant tous les arguments étaient quantitatifs. Le réflexe de la puce est si
fort qu'il survit à des messages qui appellent explicitement une courbe.

## Ne pas dessiner la première forme qui vient

Pour chaque slide non élémentaire, poser **deux ou trois formes candidates**,
puis choisir en disant pourquoi. La première forme qui vient est presque toujours
« des boîtes et des flèches », et c'est ainsi qu'on obtient trois rectangles
arrondis contenant des phrases, c'est-à-dire une liste à puces qui coûte la
place d'une figure.

Trois questions départagent :

1. **Qu'est-ce que la forme fait voir qu'une phrase ne dirait pas ?** Si la
   réponse est « rien », la forme est décorative.
2. **L'auditoire peut-il la lire en dix secondes ?** Au-delà, il lit au lieu
   d'écouter.
3. **Que se passe-t-il si le message est faux ?** Une bonne forme rend le
   contre-message visiblement absurde. Une forme qui reste jolie quel que soit le
   résultat n'argumente pas.

## L'arbre de décision

| Ce que le message fait | Forme |
|---|---|
| Compare des quantités | barres appariées, points alignés (`sci-figure`) |
| Montre une distribution | histogramme, densité, essaim de points |
| Situe dans l'espace | carte (`geo-map`, obligatoire) |
| Situe dans le temps | frise, à double registre si deux échelles de temps coexistent |
| Montre une relation | nuage de points avec la droite et son intervalle |
| Montre une hiérarchie ou une descendance | arbre annoté, élagué aux clades qui portent le message |
| Montre un enchaînement d'étapes | pipeline, labels courts, six étapes au plus |
| Montre un mécanisme | schéma, avec les objets réels et non des boîtes abstraites |
| Oppose deux états | comparaison appariée, même grille des deux côtés |
| Montre une correspondance entre deux ensembles | tanglegram, liens directs |
| Porte sur un seul nombre | grand chiffre |
| Montre une structure interne | anatomie de locus, bande annotée |
| Montre un tri, une sélection, une exclusion | diagramme de flux, effectifs à chaque étape |
| Énumère des éléments sans relation entre eux | liste à puces, et seulement là |

La dernière ligne est la seule qui autorise une liste. Quatre tests statistiques
hétérogènes sans ordre ni composition : liste légitime. Quatre étapes qui
s'enchaînent : pipeline. Quatre régions : carte. Quatre mesures : graphique.

## Le bestiaire

**Frise à double registre.** Deux bandes de temps superposées, l'une pour
l'histoire humaine, l'autre pour l'événement biologique. Fait voir une
coïncidence temporelle sans avoir à l'affirmer.

**Carte à camemberts.** Proportion de deux lignées par site. Le regard fait la
partition tout seul. Toujours par `geo-map`, avec échelle et nord.

**Arbre élagué et annoté.** Un arbre de 2000 feuilles ne dit rien. Élaguer aux
clades qui portent le message, colorer un seul caractère, annoter les deux ou
trois nœuds cités. Un arbre de slide n'est pas un arbre d'article.

**Avant et après de topologie.** Deux petits arbres côte à côte, ce qui a bougé
mis en couleur. Fait voir un reclassement mieux qu'un tableau.

**Flux de sélection.** Effectifs à chaque étape, ce qui sort et pourquoi. Rend
l'échantillon défendable sans le raconter.

**Schéma de mécanisme.** Les objets réels dessinés, pas des rectangles nommés.
La différence entre un schéma et un organigramme est là.

**Barres appariées.** Deux séries, même axe. La forme qui manquait à tous les
decks du parc.

**Grand chiffre.** Un nombre, une phrase. Le type le plus rentable rapporté à
son coût de fabrication.

**Anatomie de locus.** Une bande horizontale, les régions annotées, la position
du variant marquée. Remplace un paragraphe de coordonnées.

**Tanglegram.** Deux arbres face à face, feuilles reliées. La forme naturelle
d'une co-divergence hôte et pathogène.

**Matrice élaguée.** Une heatmap n'est lisible que réduite à ce qui porte le
message : quelques lignes, quelques colonnes, un ordre choisi.

**Comparaison appariée.** Deux colonnes, même grille. Ni plus ni moins.

## Patrons TikZ

Labels courts, jamais des phrases : un nœud de plus de six mots déclenche le
contrôle `V1`.

### Pipeline

```latex
\begin{tikzpicture}[
  node distance=6mm and 9mm,
  etape/.style={draw=gxprofond, thick, rounded corners=2pt, fill=gxsable!30,
                inner sep=5pt, minimum height=9mm, align=center, font=\small},
  fl/.style={-{Stealth[length=2.5mm]}, gxardoise, thick}]
  \node[etape] (a) {Lectures\\SRA};
  \node[etape, right=of a] (b) {Alignement\\BWA};
  \node[etape, right=of b] (c) {Variants\\SPDI};
  \node[etape, right=of c] (d) {Arbre\\RAxML-NG};
  \draw[fl] (a)--(b); \draw[fl] (b)--(c); \draw[fl] (c)--(d);
  \node[below=2mm of b, font=\scriptsize, gxardoise] {1\,995 souches};
\end{tikzpicture}
```

### Frise à double registre

```latex
\begin{tikzpicture}[x=1.28cm, y=1cm]
  \draw[gxardoise, thick, -{Stealth[length=2.5mm]}] (0,0) -- (8.4,0);
  \foreach \x/\l in {0/-4000, 2/-2000, 4/0, 6/1000, 8/2000}
    \draw[gxardoise] (\x,-1.2mm) -- (\x,1.2mm) node[below=2mm, font=\scriptsize] {\l};
  % registre du haut : histoire humaine
  \node[gxprofond, font=\small\bfseries, above=6mm] at (2,0) {expansion bantoue};
  \draw[gxprofond, very thick] (1.4,4mm) -- (3.2,4mm);
  % registre du bas : evenement biologique
  \node[gxaccent, font=\small\bfseries, below=9mm] at (5,0) {divergence L5 / L6};
  \draw[gxaccent, very thick] (4.4,-6mm) -- (5.6,-6mm);
\end{tikzpicture}
```

### Anatomie de locus

```latex
\begin{tikzpicture}[x=1cm]
  \fill[gxsable] (0,0) rectangle (10,0.55);
  \fill[gxsauge!60] (2.2,0) rectangle (4.6,0.55);
  \node[font=\scriptsize] at (3.4,0.28) {domaine catalytique};
  \draw[gxaccent, very thick] (5.9,-0.18) -- (5.9,0.73);
  \node[gxaccent, font=\scriptsize\bfseries, above] at (5.9,0.73) {S315T};
  \draw[gxardoise] (0,-0.16) -- (10,-0.16);
  \foreach \x/\l in {0/1, 5/2250, 10/4500}
    \node[font=\scriptsize, gxardoise, below] at (\x,-0.18) {\l};
\end{tikzpicture}
```

### Flux de sélection

```latex
\begin{tikzpicture}[node distance=5mm,
  b/.style={draw=gxprofond, rounded corners=2pt, inner sep=5pt, align=center,
            font=\small, minimum width=42mm},
  s/.style={draw=gxardoise, dashed, rounded corners=2pt, inner sep=4pt,
            align=left, font=\scriptsize, text=gxardoise}]
  \node[b] (a) {12\,480 souches candidates};
  \node[b, below=14mm of a] (c) {1\,995 retenues};
  \draw[-{Stealth[length=2.5mm]}, gxardoise, thick] (a)--(c);
  % Le point milieu se NOMME. Sous babel FRANCAIS, « ! » est un caractere actif
  % (espace fine avant la ponctuation double), ce qui casse la syntaxe calc
  % $(a)!0.5!(c)$ quand elle est ecrite DANS une option positioning :
  % « Package tikz Error: + or - expected ». Le meme code passe en babel anglais.
  % Nommer la coordonnee contourne le probleme et se lit mieux.
  \coordinate (m) at ($(a)!0.5!(c)$);
  \node[s, right=10mm of m] (x)
    {couverture $<$ 20$\times$ : 6\,412\\espèce non MTBC : 3\,201\\métadonnées absentes : 872};
  \draw[gxardoise, dashed] (m) -- (x);
\end{tikzpicture}
```

Charger `\usetikzlibrary{calc}`. Et ne pas écrire la syntaxe de point milieu
directement dans une option `positioning` (`right=8mm of $(a)!0.5!(c)$`) : sous
`babel` français, `!` est actif et la clé échoue sur « + or - expected », alors
que le même code compile en `babel` anglais. Nommer la coordonnée d'abord.

## Les délégations

- **`geo-map`** dès qu'il y a du géographique. Une carte schématique TikZ ne
  remplace pas une carte pour discuter distribution, foyer ancestral ou flux.
- **`sci-figure`** pour tout graphique de données, **en demandant des tailles de
  projection** : ses presets par défaut sont calibrés pour les revues, donc trop
  fins pour une salle.
- **`slide-design`** pour une slide isolée particulièrement difficile : il
  propose des options structurelles avec leurs références éditoriales.
- **`fig-ideation`** quand c'est le projet entier qui manque d'une figure, pas
  seulement la slide.
- **`slide-polish`** pour reprendre une slide déjà écrite qui ne va pas.

## Ce qui n'est pas un objet visuel

Un rectangle arrondi contenant une phrase. Une accolade décorative. Un jeu
d'icônes qui répète le texte. Un dégradé. Une ombre portée. Un logo répété sur
chaque slide. Une photographie d'illustration sans rapport avec la démonstration.

Le test est toujours le même : **qu'est-ce que cela fait voir qu'une phrase ne
dirait pas ?**
