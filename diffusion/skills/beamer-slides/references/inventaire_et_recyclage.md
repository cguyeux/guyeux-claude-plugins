# L'inventaire de la matière, et le recyclage des figures

## Les cinq rangs

Transposition à l'oral du geste 6 de `narratif`. Chaque item de l'acquis reçoit
un rang, et le rang décide de son sort.

| Rang | Définition | Coût en slides |
|---|---|---|
| NOYAU | Sans lui la démonstration tombe. C'est un maillon de la chaîne. | une slide, parfois deux |
| APPUI | Soutient un maillon sans le porter. | partage une slide, ou une ligne de lecture |
| MENTION | Une phrase qui garde le chiffre, sans slide propre. | zéro |
| ANNEXE | Sera demandé en questions, mais n'entre pas dans l'arc. | une slide après `\appendix`, gratuite |
| ÉCARTÉ | N'entre pas, avec son motif écrit. | zéro |

Écrire le motif d'un ÉCARTÉ n'est pas une formalité : c'est ce qui empêche de
réinstruire le même arbitrage au prochain exposé, et ce qui permet de le rouvrir
si le public change.

## La taxe de coût irrécupérable

Trois semaines de calcul ne gagnent pas une slide. Un résultat coûteux mais qui
ne sert aucun maillon est ÉCARTÉ ou ANNEXE, jamais NOYAU. C'est la règle la plus
difficile à tenir et celle qui rend le plus : la moitié des slides en trop d'un
deck de recherche sont là parce qu'elles ont coûté cher.

Symptôme à surveiller : une slide dont le message se formule « nous avons aussi
fait X ». Ce n'est pas un message, c'est une justification de temps passé.

## Quand le NOYAU dépasse le budget

Ce n'est pas le budget qui cède. Deux issues seulement :

1. Le message est trop large : retourner au geste 2 et le resserrer. C'est
   presque toujours la bonne réponse.
2. La durée est mal estimée : vérifier auprès de l'organisateur avant de
   sacrifier la démonstration.

Rétrécir la police, empiler deux idées par slide ou parler plus vite ne sont pas
des issues, ce sont les trois façons de rater l'exposé.

## L'audit des figures existantes

Une figure d'article est calibrée pour un lecteur à trente centimètres qui peut
s'y arrêter. L'auditoire est à huit mètres et dispose de quatre-vingt-dix
secondes. Les critères ne sont donc pas les mêmes, et une figure publiée n'est
presque jamais réutilisable telle quelle.

Où chercher : `article/figures/`, `résultats/`, `figures/`, et les
`presentations/` antérieures du projet. Le registre `fig_check.md` de l'article,
s'il existe, dit déjà lesquelles sont saines.

### Les quatre verdicts

**Réutilisable telle quelle.** Rare. La figure porte un seul message, ses textes
restent lisibles une fois réduits à la largeur d'une slide, elle n'a pas de
panneau hors sujet, et sa palette tient à la projection.

**À reforger.** Le cas général. Les gestes qui reviennent : agrandir les polices
d'axes et de légende, passer au ratio 16:9, supprimer les panneaux qui ne
servent pas le message de CETTE slide, remplacer la légende par une annotation
directe sur la figure, alléger la grille, réduire le nombre de couleurs. Une
figure à six panneaux devient trois slides ou un seul panneau.

**À refaire.** La figure répond à une autre question que celle de la slide. La
reforger reviendrait à la refaire : autant partir du message.

**Inutilisable ici.** Trop dense par nature (une heatmap de 400 lignes, un arbre
à 2000 feuilles). Elle peut aller en annexe, où l'on prend le temps de la lire
si la question vient.

### Le test de lisibilité

Le seul qui compte, et il est mécanique : rendre la slide en PNG, puis regarder.
Un texte d'axe doit rester lisible sur un rendu à 110 dpi réduit de moitié. Si
l'on doit zoomer pour le lire à l'écran, la salle ne le lira pas.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/beamer-slides/scripts/deck_render.py deck.tex -p 7 --crops
```

Les recadrages `gauche` et `droite` à 300 dpi servent exactement à cela.

### Les ordres de grandeur

Pour une slide 16:9 de 160 mm de large, projetée dans une salle de taille
ordinaire :

| Élément | Taille minimale à la projection |
|---|---|
| Texte d'axe, légende de figure | équivalent 14 pt sur la slide |
| Étiquette de série, annotation | équivalent 16 pt |
| Chiffre que la salle doit lire | équivalent 20 pt |
| Trait de courbe | 1,5 pt, jamais 0,5 |

`sci-figure` produit par défaut aux normes des revues, qui sont plus fines.
Demander explicitement des tailles de projection, sinon la figure sortira
calibrée pour du papier.

### Ce qu'on gagne à consigner

Écrire le verdict par figure dans `plan_presentation.md`, avec la date. Au
prochain exposé du même projet, l'audit ne recommence pas : il ne porte que sur
les figures nouvelles ou modifiées depuis.
