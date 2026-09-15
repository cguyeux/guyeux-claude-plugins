# La forme d'un tableau : typographie scientifique et LaTeX

Référence chargée à la demande par `sci-table`. Le fond est dans `fond.md`. Tout ce qui suit
a été compilé et vérifié (TeX Live 2025, `pdflatex`, 2026-09-09) ; les échecs constatés sont
signalés comme tels.

---

## 1. Les trois règles qui font la différence à l'œil

**Aucun filet vertical.** Les colonnes se séparent par le blanc. Un trait vertical est une
convention de tableur, pas de typographie scientifique : il fragmente la page et empêche
l'œil de descendre une colonne. Aucune revue à comité ne l'exige, plusieurs l'interdisent.

**Trois filets horizontaux, pas plus** : un au-dessus de l'en-tête, un sous l'en-tête, un
sous le corps. `booktabs` les donne d'épaisseurs différentes, et c'est cette différence qui
fait lire la hiérarchie. `\hline` répété ligne à ligne produit une grille où plus rien ne
ressort. Pour un sous-groupe, `\addlinespace` (un blanc) ou `\cmidrule(lr){2-3}` (un filet
partiel), jamais un filet pleine largeur.

**Les nombres s'alignent sur la virgule décimale.** C'est ce qui permet de comparer des
ordres de grandeur d'un coup d'œil. Une colonne `c` de nombres est illisible dès que les
valeurs n'ont pas la même longueur.

```latex
\usepackage{booktabs,siunitx}
\sisetup{detect-all, group-digits=integer, group-minimum-digits=5}

\begin{tabular}{l S[table-format=5.0] S[table-format=2.2]}
  \toprule
  Lignée & {Souches} & {GC (\%)} \\   % en-tête d'une colonne S : ENTRE ACCOLADES
  \midrule
  L4.1 & 1284  & 65.61 \\
  L4.2 & 12043 & 65.61 \\             % rendu : 12 043, groupé automatiquement
  \bottomrule
\end{tabular}
```

---

## 2. siunitx : deux pièges qui coûtent une compilation ou une marge

**Piège 1, vérifié le 2026-09-09 — toute cellule non numérique d'une colonne `S` doit être
entre accolades**, en-tête compris. Sans elles, la compilation s'arrête sur
`! Package siunitx Error: Invalid number 'e'.` suivi d'une cascade de
`Forbidden control sequence` qui ne dit rien du vrai coupable. `{n.d.}`, `{---}`, `{Total}`
et `{GC (\%)}` sont corrects ; `n.d.` ne l'est pas.

**Piège 2, silencieux — `table-format` doit couvrir la plus grande valeur de la colonne.**
Avec `S[table-format=2.1]`, une valeur `105.2` déborde : TeX émet un
`Overfull \hbox (5.0pt too wide) detected at line ...` (le mot *detected*, pas *in paragraph
at lines*), qu'une relecture du log filtrant `Overfull` dans les paragraphes laisse passer.
Compter les chiffres avant de fixer le format ; `table_build.py` le calcule.

Formats utiles :

| Besoin | Spécification |
|---|---|
| Entiers jusqu'à 5 chiffres | `S[table-format=5.0]` |
| Deux décimales | `S[table-format=2.2]` |
| Valeurs négatives | `S[table-format=-2.2]` |
| Estimation ± incertitude | `S[table-format=2.1(2)]` avec `\sisetup{separate-uncertainty}`, cellule `12.3(4)` → 12,3 ± 0,4 |
| Exposant | `S[table-format=1.2e2]`, cellule `1.23e-4` |
| Intervalle de confiance | colonne `c` ordinaire, cellule `1.10--1.83` (un intervalle n'est pas un nombre) |

---

## 3. Les notes de tableau

Une note de tableau n'est pas une note de bas de page : `\footnote` dans un flottant se perd
ou casse. `threeparttable` aligne les notes sur la largeur du tableau et gère les appels.

```latex
\begin{table}[htbp]
  \centering
  \begin{threeparttable}
  \caption{...}\label{tab:x}
  \begin{tabular}{l S[table-format=4.0]}
    \toprule
    Lignée & {n} \\
    \midrule
    L5\tnote{a} & 97 \\
    \bottomrule
  \end{tabular}
  \begin{tablenotes}[flushleft]\footnotesize
    \item[a] Effectif faible, intervalle non calculé.
    \item Abréviations : MDR, multirésistant ; IC, intervalle de confiance.
  \end{tablenotes}
  \end{threeparttable}
\end{table}
```

Les notes portent, dans cet ordre : les abréviations des en-têtes, la définition du marqueur
de donnée manquante, le test statistique et sa correction, la source des données.

---

## 4. La légende

**Au-dessus du tableau**, à l'inverse d'une figure : le lecteur a besoin de la clé avant les
chiffres. En LaTeX, `\caption` avant `\begin{tabular}` suffit à l'obtenir.

Elle doit rendre le tableau **autonome** : ce qui est compté, sur quel effectif, dans quelle
unité, par quel test, dans quel ordre sont les lignes. Une légende de sept mots oblige à
retourner au corps, ce qu'un relecteur pressé ne fera pas.

Une légende longue accepte un titre court pour la liste des tableaux :
`\caption[Titre court]{Légende complète...}`.

---

## 5. Quand le tableau est trop large : les remèdes, dans l'ordre

L'ordre compte. Les trois premiers portent sur le fond et améliorent le tableau ; les
derniers sont des expédients qui dégradent la page.

1. **Retirer des colonnes.** Colonne constante, colonne dérivable d'une autre, `%` quand le
   dénominateur est constant, colonne que le texte commente déjà.
2. **Transposer.** Beaucoup d'attributs et peu d'unités : `--transpose` de `table_build.py`.
3. **Abréger les en-têtes** et développer les abréviations en note ; en-tête sur deux lignes
   avec `\thead{Lignée\\(ancienne)}` (`makecell`).
4. **Scinder en deux tableaux** qui répondent à deux questions distinctes.
5. **Pleine largeur** : `table*` en classe deux colonnes (le flottant remonte en haut d'une
   page, comportement normal).
6. **Rotation** : `\usepackage{rotating}` puis `sidewaystable`. Acceptable pour un tableau
   large et important, à éviter au-delà d'un par article.
7. **Verser au supplémentaire** et ne garder dans le corps qu'une synthèse.
8. **En dernier recours, `\small`.** Jamais en dessous de `\footnotesize`, et jamais sans
   avoir essayé les sept remèdes précédents. Mesuré sur le corpus `mtbc/` : **24 % des
   tableaux réduisent la police**, presque toujours à la place d'une réflexion sur le contenu.

**Ce qu'il ne faut pas faire : `\resizebox`, `\scalebox`, `adjustbox`.** Ils changent la
taille de la police du tableau par un facteur arbitraire, différent d'un tableau à l'autre :
le résultat est incohérent avec le texte et avec les autres tableaux, et un éditeur le
refuse ou le recompose.

---

## 6. Tableaux longs

`longtable` casse le tableau sur plusieurs pages avec répétition de l'en-tête :

```latex
\begin{longtable}{l S[table-format=3.0] l}
  \caption{...}\label{tab:long}\\
  \toprule Accession & {n} & Pays \\ \midrule
  \endfirsthead
  \toprule Accession & {n} & Pays \\ \midrule
  \endhead
  \midrule \multicolumn{3}{r}{\footnotesize suite page suivante}\\
  \endfoot
  \bottomrule
  \endlastfoot
  SRR100 & 12 & France \\
\end{longtable}
```

**Piège vérifié le 2026-09-09 : `longtable` échoue en classe deux colonnes**, sur
`! Package longtable Error: longtable not in 1-column mode.` C'est le cas de la plupart des
gabarits de revues (IEEE, Elsevier deux colonnes, certaines classes ACM). Trois issues :
`supertabular` (vérifié fonctionnel en deux colonnes le même jour), basculer la table en
supplémentaire (préférable neuf fois sur dix), ou l'isoler dans un `\onecolumn`.

---

## 7. tabularray, et quand s'en passer

`tabularray` (`tblr`) est le paquet moderne : cellules fusionnées sans acrobaties, styles par
ligne et par colonne, largeurs fixes propres, couleurs. Il est légitime pour un tableau à
structure complexe, et le skill `latex-tables` en porte la syntaxe détaillée.

```latex
\begin{tblr}{colspec={l Q[c,2cm] r}, row{1}={font=\bfseries}, hline{1,2,Z}={0.8pt}}
  Marqueur & Position & Freq \\
  katG & 2155168 & 0.42 \\
\end{tblr}
```

Deux réserves, à peser plutôt qu'à appliquer aveuglément. D'abord, `tabularray` est un paquet
LaTeX3 récent : une chaîne de production éditoriale figée sur une distribution ancienne peut
ne pas le compiler, alors que `booktabs` est présent partout depuis vingt ans. Ensuite, ses
options par défaut invitent aux filets partout (`hlines`, `vlines`), qui sont précisément ce
que la typographie scientifique proscrit. **Pour un manuscrit soumis, `booktabs` + `tabular`
+ `siunitx` reste le défaut sûr** ; `tblr` se justifie par un besoin de structure que
`tabular` ne couvre pas.

---

## 8. Contraintes des revues

Elles changent, et un skill n'est pas une source : **vérifier le guide de la revue visée à la
date de soumission** (le skill `soumission` tient la base `~/.agents/knowledge/journals/`).
Ce qui est stable et vaut comme défaut :

- pas de filets verticaux, pas de fond de couleur, pas d'information portée par la seule
  couleur (l'impression en niveaux de gris et le daltonisme) ;
- chaque tableau cité dans le texte, dans l'ordre de numérotation ;
- unités et abréviations définies dans la légende ou les notes du tableau lui-même ;
- pas d'image de tableau : un tableau se soumet en texte, jamais en PNG ;
- certaines revues (famille *Nature*) demandent les tableaux **en fin de manuscrit**, un par
  page, hors du flux du texte ; d'autres (PLOS) les veulent juste après le paragraphe qui les
  cite. Les deux se satisfont avec le même code, seul le placement change.

---

## 9. Le contrôle final, sur le PDF

Le source ne dit pas tout. Après compilation :

- lire le tableau **dans le PDF rendu**, à taille réelle, et non dans le `.tex` ;
- vérifier qu'aucune cellule ne déborde de la marge (le log ne suffit pas : voir le piège 2
  de siunitx et la fiche `latex-unbreakable-token-margin-overflow.md`) ;
- vérifier que le flottant n'a pas dérivé trois pages après le paragraphe qui le cite ;
- vérifier que la colonne de nombres est alignée sur la décimale, à l'œil, sur le rendu.

`table_build.py --preview` compile un aperçu autonome, rogné aux marges, et signale les
débordements détectés par TeX.
