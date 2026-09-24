---

name: sci-table
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST), redaction d'articles evalues par les
  pairs : conception et mise en forme des TABLEAUX d'un manuscrit. Traite d'abord le FOND
  (ce tableau doit-il exister, ou est-ce une phrase, une figure, un supplementaire ; quelles
  lignes, quelles colonnes, quel ordre, quelle precision), puis la FORME (booktabs, alignement
  decimal siunitx, notes threeparttable, legende autonome, largeur reelle et ancrage colonne /
  pleine page / rotation / longtable). Audite mecaniquement les tableaux d'un .tex (20 regles :
  colonne constante, precision heterogene, largeur debordante, police reduite en rustine,
  tableau non cite, tableau relu dans le texte), construit un tableau depuis un CSV en
  explicitant ses decisions, et tient le registre
  tab_check.md. A utiliser quand on ecrit ou retravaille un tableau d'article, quand un tableau
  deborde de la marge, quand on hesite entre un tableau et une figure, ou avant une soumission.
  Pour la seule syntaxe de tabularray, voir latex-tables.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# sci-table — le fond du tableau, puis sa forme

> **Règle d'or.** Un tableau existe quand le lecteur a besoin de la **valeur exacte** et
> qu'il doit la **comparer** à d'autres. Tout le reste est une phrase, une figure, ou un
> fichier supplémentaire. La mise en forme ne sauve pas un tableau qui n'aurait pas dû
> exister ; elle achève un tableau dont le contenu a été décidé.

Ce skill est aux tableaux ce que `fig-ideation` et `fig-check` sont aux figures. Il couvre
les trois gestes que rien d'autre ne porte : **décider** ce que le tableau contient,
**produire** un tableau aux normes, **auditer** ceux d'un manuscrit déjà écrit.

## Le trou que ce skill remplit

`latex-tables` documente la syntaxe du paquet `tabularray` et recommande `hlines, vlines` :
c'est un tutoriel de paquet, indifférent au fond, et son exemple d'ouverture produit une
grille que la typographie scientifique proscrit. `deai-latex` ne voit du tableau que sa
marge, et sa règle R18 propose `\small` comme remède, c'est-à-dire la rustine mesurée
ci-dessous. `manuscript-review` pose deux questions sur les tables dans sa dimension D8.
`supp-check` vérifie l'alignement corps/supplémentaire une fois les tableaux écrits.
**Personne ne dit « cette colonne ne discrimine rien », « cette précision est inventée »,
« ce tableau est une phrase ».**

### Le diagnostic qui justifie ce skill

Mesuré le 2026-09-09 sur `mtbc/`, 121 manuscrits, **120 tableaux** analysés hors slides
(`table_lint.py --corpus ~/docs/codes/mtbc`) :

| Constat | Chiffre |
|---|---|
| Manuscrits portant au moins un tableau | **35 sur 121** (médiane 2 tableaux, maximum 15) |
| Tableaux en `booktabs` | 111 sur 115 : **la mécanique de base est acquise** |
| Tableaux dont la légende ne suffit pas à les lire seuls | **63 (52 %)** |
| Tableaux à police réduite (`\small` … `\tiny`) ou mis à l'échelle | **29 (24 %)** |
| Tableaux dépassant la largeur utile de la colonne de texte | **28 (23 %)** |
| Colonnes à décimales sans alignement décimal (`siunitx` absent de 111 tableaux sur 115) | **28 (23 %)** |
| En-têtes groupés par `\multicolumn` sans `\cmidrule` | **19 (16 %)** |
| Tableaux non cités dans le corps, ou sans `\label` | **14 (12 %)** |
| Tableaux dont plus de 70 % des valeurs sont réécrites dans le texte | **12 (10 %)** |
| Colonnes mélangeant plusieurs précisions décimales | **11 (9 %)** |
| Colonnes constantes, qui ne discriminent rien | **8 (7 %)** |
| Tableaux sans aucun signalement de fond ni de forme | **26 sur 120** |

Le défaut dominant n'est donc pas l'ignorance de `booktabs`, largement acquis, mais
l'**absence de décision sur le contenu** : on verse dans le tableau ce que le calcul a
produit, puis on rétrécit la police quand ça déborde.

## Ce que ce skill ne fait pas

| Besoin | Délégation |
|---|---|
| Syntaxe détaillée de `tabularray` / `tblr` | `latex-tables` |
| Graphique de données aux normes d'une revue | `sci-figure` |
| Figure qui manque au manuscrit | `fig-ideation` |
| Relecture visuelle des figures | `fig-check` |
| Alignement corps ↔ supplémentaire | `supp-check` |
| Longueur du manuscrit, style, économie du texte | `deai-latex` |
| Cohérence des chiffres avec les données | `claim-check` |
| Place de chaque fait dans la démonstration | `narratif` |

Il ne recalcule aucune donnée : il met en forme ce qu'on lui donne et signale ce qui, dans la
forme, trahit un problème de fond.

---

## Mode `review` — auditer les tableaux d'un manuscrit

Le mode par défaut quand on passe un `.tex`.

```bash
python3 scripts/table_lint.py main.tex
python3 scripts/table_lint.py main.tex supplementary.tex --width 48
python3 scripts/table_lint.py --corpus ~/docs/codes/mtbc --json
```

`--width` donne la largeur utile en caractères : **90** pour un article une colonne, **48**
pour une classe deux colonnes (IEEE, Elsevier). Les fichiers Beamer sont reconnus et leurs
tabulars échappent aux règles de flottant.

Trois sévérités : **FOND** (le tableau ne devrait pas être ce qu'il est), **FORME** (bon
objet, mauvaise mise en forme), **INFO** (à vérifier à l'œil).

Procédure :

1. Lancer le linter sur le manuscrit et sur ses supplémentaires.
2. **Traiter les FOND en premier, et un par un** : chacun demande un arbitrage, pas une
   correction automatique. Une colonne constante se retire, mais ce qu'elle disait doit
   passer dans la légende ; un tableau non cité se cite ou se supprime, et le choix est
   scientifique.
3. Traiter les FORME, qui se corrigent mécaniquement (`fond.md` §4, `forme.md` §1 à §5).
4. **Compiler et relire le PDF**, tableau par tableau, à taille réelle. Le source ne montre
   ni un débordement, ni un flottant parti trois pages plus loin.
5. Écrire le verdict dans `tab_check.md` (voir plus bas).

Les vingt règles sont listées en fin de fiche.

---

## Mode `design` — concevoir un tableau avant de l'écrire

À faire avant de produire quoi que ce soit, et systématiquement pour un tableau nouveau.
Charger `references/fond.md` et dérouler :

1. **Écrire la question** à laquelle le tableau répond, en une phrase. Si elle ne s'écrit
   pas, s'arrêter : il n'y a pas encore de tableau.
2. **Choisir le véhicule** (`fond.md` §1). Le lecteur a-t-il besoin de la valeur exacte ?
   Doit-il percevoir une forme plutôt qu'une valeur ? Le résultat tient-il en une phrase ?
   Ce test élimine plus de tableaux qu'il n'en valide, et c'est son intérêt.
3. **Identifier l'archétype** dans le bestiaire (`fond.md` §5, douze types) et vérifier que
   le tableau porte bien ce que son type doit porter.
4. **Fixer lignes, colonnes et ordre** : lignes = unités comparées, colonnes = attributs, ce
   qu'on veut voir comparé dans une même colonne, ordre des lignes dicté par l'argument.
   Transposer si les attributs sont plus nombreux que les unités.
5. **Justifier chaque colonne** : discrimine-t-elle ? son unité est-elle en en-tête ? sa
   précision est-elle celle de la mesure ? l'incertitude accompagne-t-elle l'estimation ?
6. **Écrire la légende avant le tableau** : ce qui est compté, sur quel effectif, dans quelle
   unité, par quel test, dans quel ordre. Si elle ne s'écrit pas, le tableau n'est pas conçu.
7. **Décider corps ou supplémentaire** (`fond.md` §6).

Rendre une **spécification** de quelques lignes avant de coder, et la faire valider quand le
tableau est structurant.

---

## Mode `build` — produire le tableau

```bash
python3 scripts/table_build.py data.csv \
    --caption "Profondeur de séquençage par sous-lignée." --label tab:depth \
    --note "MDR, multirésistant." --journal onecol --preview . --out table_depth.tex
```

Le script fait les gestes qu'on oublie et **dit ce qu'il a fait**, sur la sortie d'erreur :
colonne constante retirée, unité remontée dans l'en-tête, précision homogénéisée (avec un
avertissement quand le fichier mélange des précisions très différentes : le compromis est un
choix, pas une mesure), p-values bornées, `table-format` calculé, filets `booktabs`, légende
au-dessus, notes en `threeparttable`, préambule requis, et un **verdict d'ancrage** fondé sur
la largeur mesurée : colonne de texte, pleine largeur, rotation, ou tableau à repenser.

Options : `--transpose`, `--sig N` (chiffres significatifs), `--keep-constant`, `--group N`
(`\addlinespace` toutes les N lignes), `--journal onecol|twocol|nature|plos|elsevier`,
`--tabularray`, `--env`, `--preview DIR`.

`--preview` compile un PDF autonome, le rogne aux marges et en tire un PNG : **le relire
visuellement fait partie de la production**, comme `fig-check` le fait pour les figures. Y
vérifier l'alignement décimal, la lisibilité des en-têtes, la place des notes, et l'absence
de débordement.

Quand les données ne viennent pas d'un CSV, écrire le tableau à la main en suivant
`forme.md`, puis passer `table_lint.py` dessus : le linter est aussi un contrôle de sortie.

---

## Le registre `tab_check.md`

À la racine du projet, à côté de `claim_check.md` et `fig_check.md`. Une section datée par
passe, jamais réécrite : ce qui a été corrigé, ce qui a été délibérément laissé, et pourquoi.
Un tableau laissé en l'état avec un motif écrit n'est pas un défaut ; c'est un arbitrage, et
la passe suivante n'y revient pas.

```markdown
## 2026-09-09 — passe avant soumission (main.tex, 6 tableaux)

- **T3 (colonne constante)** — Tableau 4, colonne « Relation » constante à ⊂ : retirée,
  énoncée dans la légende.
- **T5 (précision)** — Tableau 2, GC en 1 à 3 décimales : homogénéisé à 2, précision réelle
  de l'estimation par reads.
- **LAISSÉ** — Tableau 6 en `\small` : 9 colonnes toutes nécessaires à la comparaison
  demandée par le relecteur 2 ; pleine largeur impossible en classe une colonne.
```

---

## Les vingt règles du linter

| Règle | Ce qu'elle mesure | Sévérité |
|---|---|---|
| T0 | Tabular hors flottant : ni légende, ni label, ni numérotation | INFO |
| T1 | Véhicule : moins de 3 lignes (une phrase), plus de 25 lignes dans le corps (supplémentaire) | FOND |
| T2 | Largeur estimée supérieure à la largeur utile | FORME |
| T3 | Police réduite ou mise à l'échelle (`resizebox`, `scalebox`, `adjustbox`) | FORME/FOND |
| T4 | Filets verticaux, `\hline` répétés, double filet | FORME |
| T5 | Précisions décimales mélangées dans une colonne | FORME |
| T6 | Colonne à décimales sans colonne `S` de siunitx | FORME |
| T7 | Unité répétée dans les cellules au lieu de l'en-tête | FORME |
| T8 | Colonne constante | FOND |
| T9 | p-value affichée à zéro | FORME |
| T10 | Légende absente, sous le tableau, trop courte, ou sans effectif ni unité ni test | FORME |
| T11 | Tableau sans `\label`, ou jamais cité dans le corps | FOND |
| T12 | Nombres ≥ 10 000 sans séparateur de milliers | FORME |
| T13 | Note de tableau bricolée en `\multicolumn` au lieu de `threeparttable` | FORME |
| T14 | En-tête groupé par `\multicolumn` sans `\cmidrule` | FORME |
| T15 | Colonnes `n` et `%` côte à côte (redondantes si le dénominateur est constant) | INFO |
| T16 | Deux colonnes dont la seconde est du texte long : liste déguisée en tableau | FOND |
| T17 | `longtable` pour un tableau qui tient sur une page | FORME |
| T18 | Plus de 70 % des valeurs du tableau réécrites dans le texte | FOND |
| T19 | Précision affichée supérieure à la précision plausible de la mesure | FORME |
| T20 | Marqueurs de donnée absente mélangés (`---`, `NA`, vide) | FORME |

Le linter mesure, il ne tranche pas : une règle déclenchée est un candidat à inspecter. Deux
d'entre elles ont des faux positifs connus, documentés dans `references/pieges.md`.

---

## Pièges vérifiés

- **Une cellule non numérique dans une colonne `S` casse la compilation** sur un message qui
  ne nomme pas le coupable (`Invalid number`) : accolades obligatoires, en-tête compris.
- **`table-format` trop court fait déborder la colonne en silence** : TeX émet un
  `Overfull \hbox … detected at line`, forme que le filtrage habituel du log manque.
- **`longtable` échoue en classe deux colonnes** (`longtable not in 1-column mode`) :
  `supertabular`, ou basculer au supplémentaire.
- **`\resizebox` change la taille de police d'un facteur arbitraire** : incohérent d'un
  tableau à l'autre, et refusé ou recomposé par les éditeurs.

Détail et vérifications dans `references/forme.md` et `references/pieges.md`.

---

## Place dans le cycle

En **phase 2**, après `narratif` : le plan dit quels faits sont dus, `sci-table` décide
lesquels prennent la forme d'un tableau. En **phase 3**, à chaque itération de rédaction. En
**phase 4**, avant soumission, en même temps que `fig-check` : `claim-check` vérifie que les
chiffres sont justes, `sci-table` que le tableau les rend lisibles.

Terminer toute passe par une entrée au cahier de labo si elle a produit un arbitrage, et par
la mise à jour de `tab_check.md`.

## Codex script path note

Bundled script paths in this packaged copy are relative to the directory containing this `SKILL.md`. For sibling packaged skills, resolve the sibling directory in the same plugin cache before running scripts.
