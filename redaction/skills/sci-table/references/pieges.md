# Pièges, limites du linter, et faux positifs assumés

Référence chargée à la demande par `sci-table`. Elle dit où l'outil se trompe, pour qu'un
signalement ne soit jamais pris pour un verdict.

---

## 1. Ce que `table_lint.py` mesure mal, par construction

**La largeur (T2) est une estimation en caractères, pas une mesure en points.** Elle compte
le plus long contenu de chaque colonne, plus deux caractères de gouttière. Une police
proportionnelle rend les chiffres plus étroits que les lettres, et `\thead` sur deux lignes
change tout. L'erreur constatée est de l'ordre de ±15 % : **la règle T2 sert à trier, le PDF
compilé tranche.** Un tableau signalé à 95 caractères pour une cible de 90 passe souvent ; un
tableau à 170 ne passe jamais.

**La détection du séparateur de milliers est ambiguë.** `12,345` vaut 12 345 en anglais et
12,345 en français. Le linter suppose qu'un dernier groupe de trois chiffres est un
séparateur, ce qui est faux pour `0,123`. Conséquence : quelques faux positifs et faux
négatifs sur T5 et T12 dans les fichiers `main_fr.tex`.

**Les cellules en mode mathématique sont réduites à un caractère.** `$\subset$` devient `*`
dans le rapport : le contenu réel se lit dans le source, le linter ne sert qu'à pointer la
colonne.

**Les tabulars imbriqués ne sont pas gérés.** Un `tabular` dans une cellule d'un autre
tabular est du bricolage de mise en page qu'il vaut mieux défaire, mais le linter l'analysera
de travers sans le dire.

---

## 2. Les six faux positifs légitimes

Une règle déclenchée n'est pas une faute. Ces six cas sont normaux, et la bonne réponse est
de les inscrire comme **LAISSÉ** dans `tab_check.md` avec leur motif.

| Règle | Cas où le signalement est faux |
|---|---|
| **T1** (plus de 25 lignes) | Une synthèse de littérature (archétype T-d) a le droit d'être longue : c'est son objet. |
| **T8** (colonne constante) | Quand la constance **est** le résultat : « tous les isolats de ce clade portent l'allèle », la colonne est l'argument. Le dire dans la légende reste préférable. |
| **T10** (légende sans effectif) | L'effectif figure déjà en colonne `n`. |
| **T15** (`n` et `%`) | Le dénominateur varie d'une ligne à l'autre : les deux colonnes sont nécessaires. |
| **T18** (valeurs réécrites) | Un tableau de composition de l'échantillon dont le texte reprend les deux ou trois chiffres structurants. Le seuil de 70 % vise le cas où le texte **relit le tableau**, pas celui où il en cite les points saillants. |
| **T6** (pas de colonne `S`) | Une colonne de valeurs toutes de même longueur (des pourcentages à une décimale entre 10 et 99) s'aligne visuellement en `c`. Le gain de `S` est alors nul. |

À l'inverse, **T11 (tableau non cité) et T3 (mise à l'échelle) n'ont pas de faux positif
connu** : les traiter systématiquement.

---

## 3. Pièges LaTeX vérifiés

Vérifications faites le 2026-09-09, TeX Live 2025, `pdflatex`.

**Colonne `S` et cellule non numérique.** `\begin{tabular}{l S[table-format=2.1]}` avec
l'en-tête `Age` non protégé s'arrête sur `! Package siunitx Error: Invalid number 'e'.`, suivi
de `Forbidden control sequence found while scanning use of \__siunitx_table_print_format_auxi:w`
et de `Missing \endgroup inserted`. Le message ne nomme jamais la cellule fautive : chercher
toute cellule non numérique de la colonne, en-tête compris, et l'entourer d'accolades.

**`table-format` trop court.** `S[table-format=2.1]` avec une valeur `105.2` produit
`Overfull \hbox (5.0pt too wide) detected at line 18` — noter la forme *detected at line*, et
non *in paragraph at lines*, que la plupart des scripts de vérification de log ne cherchent
pas. Aucun message de siunitx.

**`longtable` en deux colonnes.** `! Package longtable Error: longtable not in 1-column
mode.` — l'erreur est franche, mais elle survient tard, en pleine soumission. `supertabular`
compile correctement dans le même document (vérifié) ; il n'a pas la syntaxe `\endhead` de
longtable mais `\tablefirsthead`, `\tablehead`, `\tabletail`, `\tablelasttail` et
`\topcaption`.

**Identifiants insécables dans une cellule.** Un `\texttt{}` à underscores échappés (une
accession, un chemin, un nom de checkpoint) n'offre aucun point de césure et déborde sans
que le log le signale toujours. Utiliser `\path{...}` ou `\seqsplit`. Fiche complète :
`~/.agents/knowledge/latex-unbreakable-token-margin-overflow.md`.

**Le `&` et le `%` dans un contenu.** Un nom de pays ou de gène contenant `&`, ou une valeur
suivie de `%`, doivent être échappés (`\&`, `\%`). `table_build.py` le fait, sauf sur les
cellules qui contiennent déjà du LaTeX, qu'il laisse intactes : vérifier ces cellules-là.

**Deux compilations.** Un tableau avec `\label` cité par `\cref` demande deux passes ; un
`longtable` en demande parfois trois pour stabiliser ses largeurs de colonnes.

---

## 4. Pièges de fond, plus coûteux que les précédents

**La précision inventée.** Homogénéiser une colonne vers le maximum de décimales observé
fabrique des chiffres : `65,6` devenu `65,600` promet une exactitude que la mesure n'a pas.
`table_build.py` prend la médiane et **avertit** quand l'écart est d'au moins deux décimales,
mais c'est un compromis mécanique : la bonne valeur est celle de la précision réelle de la
mesure, que seul l'auteur connaît.

**Le zéro qui n'en est pas un.** `0` affiché pour une p-value, une fréquence non observée et
une donnée non mesurée sont trois choses différentes. Une p-value nulle n'existe pas : elle
s'écrit `< 10^{-3}`, ou à la borne réellement atteignable compte tenu du nombre de
permutations. Une case vide et un `0` se distinguent par un marqueur explicite en note.

**Le total qui ne tombe pas juste.** Les arrondis par ligne ne somment pas au total arrondi.
Un relecteur le voit immédiatement. Soit on donne le total exact et on note l'écart
d'arrondi, soit on ajuste, jamais en silence.

**Les colonnes non comparables présentées comme comparables.** Deux colonnes côte à côte
suggèrent une comparaison ; si elles proviennent de jeux de données, d'unités ou de seuils
différents, la mise en page fabrique un argument faux. Séparer par un `\addlinespace`, ou
faire deux tableaux.
