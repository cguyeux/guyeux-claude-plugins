# Les contrôles

## Le principe

Le script mesure, il ne tranche pas. Un FAIL est un fait établi mécaniquement,
pas un verdict esthétique : c'est à la lecture d'en décider la suite. Mais un
FAIL non traité doit être justifié dans le registre, pas ignoré.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/beamer-slides/scripts/slide_audit.py deck.tex --duree 20 --pixels
python3 ${CLAUDE_PLUGIN_ROOT}/skills/beamer-slides/scripts/slide_audit.py --pourquoi
```

`--pourquoi` affiche l'origine mesurée de chaque seuil. Les changer demande une
mesure, pas une intuition.

## Les codes

| Code | Niveau | Ce qu'il mesure |
|---|---|---|
| `C1` | FAIL | erreurs de compilation |
| `C2` | FAIL | `Overfull \vbox` : du contenu déborde sous le cadre, rattaché à sa slide |
| `C3` | WARN | `Overfull \hbox` : du texte sort de la marge droite, typiquement un identifiant insécable |
| `T1` | FAIL | un bloc de texte du source est absent du PDF rendu |
| `D1` | FAIL | réduction de police dans le corps d'une frame |
| `D2` | WARN / FAIL | densité, au-delà de 40 puis 60 mots portés |
| `D3` | WARN | take-away de plus de 25 mots |
| `V1` | FAIL | TikZ décoratif : des nœuds portant des phrases, sans axe ni donnée |
| `V2` | FAIL | plus de 30 % des slides de corps sans objet visuel |
| `M1` | WARN | plus de 60 % des slides de même signature structurelle |
| `M2` | WARN | plus de trois slides consécutives du même type |
| `R1` | WARN / FAIL | rythme : nombre de slides contre la durée déclarée |
| `P1` | WARN | encre anormale dans la bande basse, par rapport à la médiane du deck |

Les slides de titre, de section, de rupture et d'annexe sont typées et **exclues
des ratios du corps** : une page de titre n'a pas à porter un objet visuel.

## Les deux contrôles de débordement, et pourquoi il en faut deux

`C2` lit le log de compilation. Il est exact mais il ne dit rien du contenu.

`T1` compare le texte du source au texte réellement rendu, extrait par
`pdftotext`. Il attrape ce que le log ne signale pas : un bloc absorbé sans
avertissement, un `\only` mal fermé, une colonne qui déborde.

Les deux sont nécessaires. Sur L5L6, la légende de la slide 5 chevauche le pied
de page : `C2` la voit, `T1` non, parce que le texte **est** dans le PDF, il est
simplement au mauvais endroit. Inversement, sur l'audition PR, quatorze blocs
sont absents du rendu sans que le log ne le dise partout.

**Ne jamais se fier au contrôle visuel seul** : du contenu passé sous le bord
ressemble, à l'œil, à une slide simplement courte. C'est précisément pourquoi ce
défaut survit à des relectures répétées.

## Les faux positifs déjà payés

Chacun a coûté une mesure. Les corrections sont dans `normalize()` et ne doivent
pas être défaites.

**Les accents LaTeX.** `\'e`, `` \`a ``, `\^i`, `\c{c}` sont des commandes d'un
caractère **non alphabétique** : la regex générale ne les voit pas, et il reste
`'e` côté source contre `é` côté PDF. Toute phrase accentuée remonte alors comme
tronquée. Corrigé en effaçant la commande d'accent et en comparant sans
diacritiques des deux côtés.

**Les dimensions.** `\vspace{6pt}` laisse `6pt` au milieu de la phrase quand la
regex mange la commande mais garde l'argument. Corrigé en effaçant les commandes
de mise en page **avec** leur argument, `\begin` et `\end` compris.

**Les colonnes.** `pdftotext -layout` entrelace les colonnes d'une slide à trois
colonnes : neuf fausses troncatures sur une seule slide de l'audition PR. Corrigé
en lisant aussi en mode `-raw`, qui suit l'ordre du flux, et en acceptant une
sonde trouvée dans l'un ou l'autre.

**La césure.** `babel` coupe les mots en fin de ligne, ce qui casse une sonde
contiguë. Corrigé par une seconde chance sur une forme compactée, sans espaces
ni ponctuation.

Effet mesuré de ces quatre corrections sur l'audition PR : 120 signalements de
troncature ramenés à 14, sans perdre un seul défaut réel.

## Les deux contrôles que le script ne peut pas faire

**fig-check par slide.** Pour chaque slide portant une figure, rendre et
regarder : lisibilité à la projection, taille des textes d'axe, chevauchements,
correspondance entre ce que la figure montre et ce que le titre affirme. La
grille de `fig-check` s'applique, avec des seuils de taille plus durs.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/beamer-slides/scripts/deck_render.py deck.tex -p 5 --crops
```

**claim-check des slides.** Chaque chiffre et chaque affirmation affichés doivent
être traçables à `claim_check.md`, `etat_des_decouvertes.md` ou un résultat sur
disque. Une slide affirme en six mots ce qu'un article nuance en trois phrases,
et personne ne la relit. Trois défauts à chercher en particulier : le chiffre
arrondi qui a dérivé depuis le manuscrit ; l'affirmation dont la nuance a sauté
au passage à l'oral ; le résultat encore marqué incertain dans l'état et devenu
affirmatif sur la slide.

## Le registre

`slide_check.md` dans le répertoire de la présentation, au format de
`fig_check.md` : en-tête daté, un tableau par slide avec son statut, puis le
détail des issues. Incrémental, on ne re-vérifie que ce qui a bougé depuis la
dernière passe.

````markdown
# Registre de vérification des slides

Deck : `deck.tex` · dernière passe : 2026-09-15 · 14 slides de corps

| Slide | Statut | Codes | Note |
|---|---|---|---|
| 3 | OK | | |
| 5 | FAIL | C2, D1 | légende sous le cadre, corps réduit à `\footnotesize` |
| 7 | WARN | D2 | 46 mots, acceptable car la slide est lue lentement |

## Détail

### Slide 5 — Ce n'est pas la géographie (FAIL)
`C2` Overfull de 10,7 pt ligne 129. La clé de lecture passe sous le cadre et
chevauche le pied de page. Corrigé le 2026-09-15 en passant à `\slidefigure`,
dont la hauteur d'image est calculée.
````

## Quand un FAIL est légitime

Rarement, mais cela existe. Une slide d'annexe dense pour une question technique
peut dépasser le seuil de densité : c'est un choix, il s'écrit dans le registre
avec son motif. Ce qui n'est pas acceptable, c'est le FAIL silencieux.
