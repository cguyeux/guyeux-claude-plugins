# Patrons TikZ — cinq figures compilées et inspectées

Les cinq fichiers de `assets/patrons/` sont des figures **standalone complètes**, compilées
en `-halt-on-error` et relues visuellement. Ils ne sont pas des extraits de documentation :
chacun a été corrigé après sa première lecture visuelle, et les corrections sont commentées
dans le code.

Usage : copier le patron dans `article/figures/`, remplacer le contenu, puis boucler avec

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/fig-ideation/scripts/tikz_build.py article/figures/fig1.tex --dpi 220 --crops
```

et **relire chaque PNG produit** avant de conclure.

| Fichier | Archétype | Ce qu'il faut remplacer |
|---|---|---|
| `frise_double_registre.tex` | T1 | les deux séries d'événements, les HPD, l'échelle `\txdeep` / `\txrecent` |
| `flux_donnees.tex` | P1 | les effectifs de chaque étape et les boîtes d'exclusion |
| `mecanisme_is_deletion.tex` | M1 | les trois états et l'encart de ce que la donnée ne tranche pas |
| `avant_apres_topologie.tex` | C1 | les deux topologies et l'encart « ce qui tranche » |
| `tanglegram.tex` | D3 | les deux arbres, les appariements, le test dans l'encart |

## Ce que ces patrons imposent, et pourquoi

**Un préambule minimal et explicite.** `standalone` avec `border=4pt`, `fontenc T1`,
`lmodern`, et la liste des `\usetikzlibrary` en clair. Un patron dont on doit deviner les
bibliothèques n'est pas réutilisable.

**Des styles nommés, pas des attributs répétés.** Toutes les options apparentées sont
déclarées en tête de `tikzpicture` (`evt/.style`, `flow/.style`, `hpd/.style`). Changer
l'épaisseur de toutes les flèches doit demander une seule édition.

**Un positionnement relatif dès qu'il y a plus de quatre nœuds.** `right=1.5cm of x`,
`below=1.15cm of y`, `$(a)!0.5!(b)$` pour un milieu. Les coordonnées absolues sont tolérées
pour les ancres initiales d'un schéma simple et pour les axes calculés, jamais pour exprimer
« à droite de » ou « en dessous de ».

**Des nœuds qui portent leur propre forme.** `\node[draw, rounded corners, fill=..., inner
sep=6pt, text width=4.6cm, align=center]` et jamais un `\draw ... rectangle` suivi d'un
`\node` de texte séparé : le texte déborderait à la première modification.

**Des pointes de flèche qui s'arrêtent avant leur cible.** `-{Latex[length=5pt]}` avec
`shorten >=2pt, shorten <=2pt`. Une pointe `stealth` sans `shorten` pénètre visiblement dans
la boîte cible dès 200 dpi.

**Une palette Okabe-Ito réduite**, identique dans les cinq patrons : `#0072B2` bleu,
`#D55E00` orange, `#009E73` vert, `#CC79A7` rose, `#4D4D4D` gris neutre. Compatible
deutéranopie et protanopie, et distinguable en niveaux de gris. Pour un article dont les
figures de données utilisent déjà `MTBC_PALETTE_CB` de `geo-map`, aligner sur celle-là.

## Pièges de compilation vécus

### `step`, et toute clé pgf déjà prise
`step/.style={...}` fait échouer la compilation avec `The key '/tikz/step' requires a value`.
`step` est réservé (pas de `grid`). Vérifier avant de nommer un style : `step`, `grid`,
`scale`, `shift`, `text`, `draw`, `fill`, `color`, `above`, `below`, `left`, `right`,
`anchor`, `rotate`, `opacity` sont pris. Préfixer en cas de doute (`stepflow`, `myfill`).

### Un nom de macro TeX ne peut pas contenir de chiffre
`\def\xL69{6.8}` ne définit pas `\xL69` : il définit `\xL` avec un texte de paramètre
délimiteur `69`. Un `\def\xL8{...}` plus loin redéfinit `\xL`, la dernière définition gagne,
et la coordonnée devient un garbage silencieux. Une branche d'arbre s'est retrouvée tracée
au mauvais endroit sans aucune erreur visible. **Noms purement alphabétiques** :
`\xLsixnine`, jamais `\xL69`. Détection : `grep -nE '\\def\\[a-zA-Z]*[0-9]' fig.tex`.

C'est pour cela que `frise_double_registre.tex` code son échelle en `\newcommand` prenant
un argument (`\txdeep{-8500}`) plutôt qu'en `\def` de coordonnées nommées.

### `-interaction=nonstopmode` seul avale les erreurs
pdflatex signale l'erreur, continue, produit un PDF défectueux, et rend 0. `-halt-on-error`
est obligatoire, et c'est ce que fait `tikz_build.py`. Corollaire : relire le log même quand
un PDF sort, en cherchant `doesn't match`, `Undefined control sequence`, `Overfull`.

### `\\` à l'intérieur d'un groupe de changement de fonte casse le parseur de chemin
`{\textit{ligne1\\ligne2}}` dans un nœud produit une erreur fatale `\tikzscope@linewidth`
et aucun PDF, sur pgf 3.1.11a. Un groupe de fonte par ligne, le `\\` reste dehors :
`{\textit{ligne1}\\\textit{ligne2}}`.

### `\begin{center}` interfère avec `calc`
Autour d'un TikZ qui utilise `$(a)!0.5!(b)$`, il peut produire des caractères parasites.
Préférer `\centering`.

### Une figure trop large pour la colonne
`\resizebox{\textwidth}{!}{...}` plutôt que rogner les espacements à la main. Mais vérifier
ensuite la taille de police **effective** : une chaîne horizontale réduite à 70 % rend un
`\tiny` illisible.

## Défauts constatés à la relecture visuelle des patrons eux-mêmes

Ils sont conservés ici parce qu'ils sont représentatifs, et parce qu'ils illustrent que la
boucle d'inspection n'est pas une formalité.

- **Frise, premier tour** : les étiquettes de registre pivotées à 90 degrés chevauchaient la
  première boîte d'événement, et les barres de HPD flottaient sans lien visible avec le nœud
  qu'elles qualifiaient. Corrigé par une marge gauche réservée et par un marqueur d'estimation
  ponctuelle relié au nœud par une tige.
- **Mécanisme, premier tour** : l'encart « ce que la donnée seule ne tranche pas » recouvrait
  la boîte des 4,3 kb perdus. Invisible dans le code, évident sur le PNG.
- **Tanglegram, premier tour** : aucun appariement ne se croisait, ce qui vidait l'archétype
  de son sens. Un tanglegram dont toutes les lignes sont parallèles n'a rien à démontrer.
- **Avant/après, résiduel** : la flèche de repositionnement traverse la bordure du panneau B.
  Acceptable, mais à surveiller si les panneaux sont rapprochés.

## Esquisse jetable avant le livrable

Pour arbitrer entre deux structures avant d'écrire du TikZ.

**Mermaid** rend bien les flux et les décisions. Sans `mmdc` installé, deux voies : publier
une page Artifact, qui rend Mermaid nativement dans une balise ```mermaid ou un
`<pre class="mermaid">` ; ou `npx -y @mermaid-js/mermaid-cli -i x.mmd -o x.png` si le réseau
est disponible. Le skill hors dépôt `~/.claude/skills/design-doc-mermaid/` porte les scripts.

**Graphviz** est installé localement et ne demande aucun réseau :
`dot -Tpng sketch.dot -o sketch.png`. C'est le repli par défaut.

Dans les deux cas, l'esquisse **ne se livre pas**. Elle sert à trancher, puis on écrit le
TikZ. Le dépôt compte deux fichiers `.mmd` dont les PDF existent sans que leur régénération
soit scriptée nulle part : c'est exactement ce qu'il faut éviter.
