# Le fond d'un tableau : quoi y mettre, et d'abord s'il doit exister

Référence chargée à la demande par le skill `sci-table`. Elle porte la partie qui ne
s'automatise pas : décider **ce que** le tableau contient. La mise en forme est dans
`forme.md`, les pièges outillés dans `pieges.md`.

---

## 1. Le choix du véhicule, avant toute chose

Une même donnée peut prendre quatre formes, et une seule est la bonne. Le critère n'est
pas la quantité de chiffres, c'est **ce que le lecteur doit faire avec eux**.

| Ce que le lecteur doit faire | Véhicule | Signe qu'on s'est trompé |
|---|---|---|
| Retenir **un** chiffre qui porte l'argument | une phrase | un flottant de deux lignes |
| **Lire une valeur précise** et la citer ailleurs | tableau | on a fait un graphique dont on lit mal les valeurs |
| Percevoir une **forme** : tendance, écart, ordre, recouvrement | figure | on a fait un tableau que le lecteur doit mentalement tracer |
| **Retrouver plus tard**, vérifier, réanalyser | supplémentaire (CSV, pas un tableau LaTeX) | un tableau de 60 lignes dans le corps |

Trois questions tranchent presque tous les cas :

1. **Le lecteur a-t-il besoin de la valeur exacte ?** Si oui, tableau : une figure oblige à
   estimer à l'œil, et un relecteur qui veut recalculer un rapport ne peut pas.
2. **La comparaison est-elle sur plus de deux dimensions ?** Un tableau se lit en colonnes ;
   au-delà de trois ou quatre attributs par unité comparée, il devient une grille qu'on ne
   parcourt plus. Une figure, ou deux tableaux.
3. **Le nombre de lignes dépasse-t-il la vingtaine ?** Alors le lecteur ne compare plus, il
   consulte : le tableau appartient au supplémentaire, et le corps ne garde que la
   statistique qui porte l'argument.

**Le cas le plus fréquent, et le plus coûteux : le tableau qui aurait dû être une phrase.**
Trois lignes et deux colonnes ne justifient jamais un flottant. Elles justifient une phrase
qui donne les trois valeurs et l'écart, ce que le lecteur lit sans quitter le fil.

**Le cas symétrique, et personne ne le signale :** la figure qui aurait dû être un tableau.
Un histogramme à quatre barres, un camembert à trois parts, un nuage de six points : le
lecteur y perd la valeur exacte sans rien gagner en forme. Mesuré sur le corpus `mtbc/`
(août 2026, `fig-ideation`), **50,4 % des figures sont un graphique statistique tiré d'un
tableau** : une part non négligeable rendrait mieux service en tableau.

---

## 2. La question à laquelle le tableau répond

Un tableau qui a du fond répond à **une** question, formulable en une phrase, et sa
structure est dictée par elle.

> « Les sous-lignées diffèrent-elles par leur profondeur de séquençage ? »
> → lignes : les sous-lignées ; colonnes : n, profondeur, dispersion ; ordre : par
> profondeur décroissante, pas alphabétique.

Si la question ne s'écrit pas, le tableau est un déversoir : il porte ce que le calcul a
produit plutôt que ce que la démonstration exige. C'est exactement le défaut que
`plan_narratif.md` (skill `narratif`) cherche à prévenir en amont : chaque fait reçoit un
lieu, et « tableau » est un lieu comme un autre, à mériter.

**Test de la légende.** Écrire la légende AVANT le tableau. Si elle ne peut pas dire ce qui
est compté, sur quel effectif, dans quelle unité et par quel test, le tableau n'est pas
encore conçu.

---

## 3. La grammaire : lignes, colonnes, ordre

**Les lignes sont les unités comparées, les colonnes leurs attributs.** L'inverse se lit
mal : l'œil descend une colonne bien plus facilement qu'il ne parcourt une ligne. D'où la
règle opérationnelle : **ce qu'on veut voir comparé doit être dans une même colonne**, et
les colonnes à comparer entre elles doivent être adjacentes.

Conséquence pratique, souvent décisive : quand il y a beaucoup d'attributs et peu d'unités,
**transposer**. Trois souches et douze métriques donnent un tableau illisible de 13 colonnes,
et un tableau confortable de 12 lignes.

**L'ordre des lignes est un argument.** L'ordre alphabétique n'informe de rien ; l'ordre par
la valeur qui porte la démonstration montre le résultat avant même qu'on le lise. Exceptions
légitimes : un ordre chronologique, un ordre phylogénétique, un ordre imposé par une
nomenclature. Dans tous les cas, l'ordre choisi se dit dans la légende.

**L'ordre des colonnes va de l'identifiant au dérivé** : ce qui nomme la ligne, puis
l'effectif, puis les mesures brutes, puis les grandeurs calculées, puis le test. Le lecteur
suit la même progression que le calcul.

**Les groupes se marquent par un `\addlinespace` ou un `\cmidrule`, jamais par un filet
plein.** Un blanc suffit à dire « ici commence autre chose ».

---

## 4. Ce que chaque colonne doit mériter

- **Discriminer.** Une colonne dont toutes les valeurs sont identiques n'informe pas : elle
  s'énonce une fois dans la légende. (Règle T8 du linter, déclenchée sur 7 % des tableaux du
  corpus.)
- **Porter son unité dans l'en-tête**, entre parenthèses, jamais répétée dans les cellules :
  la colonne ne contient alors que des nombres, donc comparables d'un coup d'œil.
- **Afficher la précision de la mesure, pas celle du calcul.** `65,614 %` sur un contenu en
  GC estimé à partir de reads promet une exactitude qui n'existe pas. Trois chiffres
  significatifs est la convention par défaut ; ce qui compte est que la précision soit la
  même dans toute la colonne, et justifiable.
- **Donner l'incertitude avec l'estimation.** Une moyenne sans dispersion, un odds ratio sans
  intervalle, une fréquence sans dénominateur : le chiffre seul n'est pas vérifiable.
- **Distinguer zéro, absent et non mesuré.** Un seul marqueur pour la donnée manquante dans
  tout le tableau, expliqué en note. `0` et `---` ne veulent pas dire la même chose, et cette
  confusion a déjà changé une conclusion.
- **Ne pas mettre côte à côte `n` et `%` quand le dénominateur est constant** : il se donne
  une fois dans la légende. Quand il varie d'une ligne à l'autre, les deux sont nécessaires.

---

## 5. Bestiaire des tableaux scientifiques

Douze archétypes couvrent l'essentiel des tableaux d'un article de biologie computationnelle.
Chacun a une structure canonique et une erreur typique. S'en servir comme d'une liste de
contrôle : « de quel type est ce tableau ? porte-t-il bien ce que ce type doit porter ? »

| # | Archétype | Structure canonique | Erreur typique | Lieu |
|---|---|---|---|---|
| **T-a** | Composition de l'échantillon | une ligne par strate, colonnes n et part, ligne de total | totaux qui ne somment pas ; strates non exhaustives | corps |
| **T-b** | Comparaison de groupes | lignes = variables, colonnes = groupes, puis effet et test | donner p sans taille d'effet ni n par groupe | corps |
| **T-c** | Table de contingence | catégories × catégories, marges | omettre les marges, donc empêcher tout recalcul | corps |
| **T-d** | Synthèse de littérature | une ligne par étude : source, n, méthode, résultat, limite | colonne « résultat » en prose de trois lignes | corps (le seul type qui a droit d'être long) |
| **T-e** | Catalogue de marqueurs | position, réf/alt, gène, effet, fréquence | mettre 300 lignes dans le corps au lieu du supplémentaire | corps (les définitoires) + supp (l'exhaustif) |
| **T-f** | Performances de méthodes | lignes = méthodes, colonnes = métriques, meilleur en gras | comparer sur des jeux différents sans le dire | corps |
| **T-g** | Paramètres d'un modèle | paramètre, prior, estimation, IC, diagnostic (ESS) | omettre les diagnostics de convergence | corps ou supp |
| **T-h** | Ablation / sensibilité | une ligne par variante, colonne « effet sur le résultat » | ne montrer que les variantes favorables | corps |
| **T-i** | Correspondance de nomenclatures | notre nom ↔ système A ↔ système B, avec la relation | laisser une colonne « relation » constante | corps |
| **T-j** | Provenance des données | accession, source, pays, date, QC | donner les accessions sans le statut QC | supp (résumé en corps) |
| **T-k** | Décompte séquentiel (CONSORT génomique) | une ligne par filtre : entrées, exclus, motif, restants | ne pas faire boucler les comptes | corps ou figure de flux |
| **T-l** | Bilan de vérification | affirmation, preuve, statut | tenir ce registre dans l'article plutôt que dans `claim_check.md` | nulle part : registre de projet |

Un tableau qui ne rentre dans aucun de ces types n'est pas nécessairement fautif, mais il
mérite qu'on se demande à voix haute quelle question il traite.

---

## 6. Corps ou supplémentaire

Le corps porte **ce qui sert la démonstration** ; le supplémentaire porte **ce qui permet de
la vérifier**. La bascule n'est pas une punition pour tableau trop long, c'est une division
du travail.

Vont au supplémentaire, systématiquement : les listes d'accessions, les catalogues exhaustifs
de variants, les tableaux par souche, les résultats de toutes les configurations testées.
Sous forme de **CSV ou XLSX**, pas de tableau LaTeX de 80 lignes : le lecteur qui veut ces
données veut les charger, pas les lire. Le corps garde alors une ligne de synthèse et un
renvoi explicite.

Restent au corps, même longs : le tableau de composition de l'échantillon, la synthèse de
littérature qui situe le travail, et le tableau que la discussion commente ligne à ligne.

Le skill `supp-check` vérifie ensuite l'alignement entre les deux, et `deai-latex` mesure la
longueur globale contre la limite de la revue.

---

## 7. Ce qui ne va jamais dans un tableau

- **Une méthode.** Une séquence d'étapes est de la prose ou une figure de flux, pas une
  grille à deux colonnes.
- **Des définitions.** Terme et définition font un environnement `description`, ou une liste
  d'abréviations en note.
- **Ce que le texte dit déjà.** Le texte doit dire ce que le tableau *montre*, pas le relire.
  Quand plus des deux tiers des valeurs du tableau sont aussi écrites dans le corps (règle
  T18), l'un des deux est de trop, et c'est presque toujours le texte.
- **Un raisonnement.** Une colonne « interprétation » est une discussion déguisée : elle
  appartient au corps, où elle peut être argumentée.
