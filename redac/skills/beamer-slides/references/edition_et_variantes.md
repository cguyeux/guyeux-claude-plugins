# Éditer un exposé existant, et le décliner

Un exposé n'est presque jamais donné une fois. On le retouche la veille, on en
tire une version de quinze minutes pour un autre créneau, on traduit les slides
pour une conférence. Ces trois demandes se ressemblent et n'appellent pas du
tout le même geste. Les séparer est le premier travail.

## Le tri, en une question

**Le message du geste 2, en une phrase, change-t-il ?**

| Réponse | Nature | Geste |
|---|---|---|
| Non, et le contenu bouge à la marge | **Édition** | `/slides edit` |
| Non, mais le format change : durée, langue, salle | **Variante** | `/slides fork` |
| Oui | **Nouvel exposé** | `/slides` complet, qui *recycle* (geste 5) |

Le troisième cas est celui qu'on se cache. « La même chose mais pour des
informaticiens » n'est pas une variante : le public commande ce qu'il faut
expliquer, donc l'arc, donc le message. Le traiter en fork produit deux decks
qui divergent immédiatement tout en prétendant partager une source, ce qui est
le pire des deux mondes : on n'entretient plus rien et on croit le contraire.
Dire non au fork ici et repartir du geste 1 en réutilisant les figures est
plus court, pas plus long.

## L'édition, et la monnaie du budget

Le skill entier repose sur un ordre : le budget de temps précède le choix du
contenu. Une demande d'ajout attaque cet ordre de face, et c'est exactement le
chemin qui produit les decks à soixante-quinze frames pour vingt minutes : on
n'y arrive jamais d'un coup, on y arrive par ajouts successifs dont aucun n'a
été payé.

Donc **tout ajout rend la monnaie**. Chiffrer d'abord la demande avec le
barème du geste 3, puis rendre les trois issues et faire trancher :

- **compenser** — ce qui sort, nommément, pour que l'ajout rentre. C'est
  l'issue par défaut, et elle se propose avec ses candidats déjà choisis dans
  les rangs APPUI, jamais en demandant à l'utilisateur de trouver lui-même.
- **allonger** — la durée change. Recevable, mais c'est une décision qui
  engage l'organisateur, pas une conséquence discrète d'une demande de slide.
- **verser en annexe** — après `\appendix`, coût nul, disponible si la
  question vient. Souvent la bonne réponse pour un ajout qui ne sert aucun
  maillon.

Puis **où**, ce qui compte autant que combien. Une section ajoutée à la fin
parce que c'est là qu'il reste de la place casse le fil. Nommer le maillon de
la chaîne d'arguments que l'ajout sert ; s'il n'en sert aucun, c'est une
annexe, et le dire vaut mieux que de l'insérer poliment.

Le reste suit la mécanique ordinaire : une fiche de slide (geste 7) **avant**
tout LaTeX, l'idéation visuelle (geste 8) pour ne pas poser une liste à puces
au milieu d'un deck visuel, l'écriture (geste 9), les notes des deux markdowns
mises à jour pour les slides touchées, et l'audit relancé avec la durée
**effective** après édition.

Enfin, le registre. `plan_presentation.md` reçoit une ligne datée dans une
section « Dérives », sur le modèle de `narratif` : ce qui a été ajouté, ce qui
a été retiré en échange, à la demande de qui, et quel jour. Un deck qui a servi
trois fois sans registre est un deck dont plus personne ne connaît la version
présentée.

## La variante, et ce qui la fabrique vraiment

### Ce qui ne marche pas : `\includeonlyframes`

Mesuré le 2026-09-10 sur le thème maison. Une sélection de trois frames dans un
deck de cinq donne un PDF de trois pages, mais :

- **les pages de section disparaissent**, puisqu'elles sont produites par
  `\AtBeginSection` et ne portent aucun label ;
- **le pied de page reste calé sur le deck complet** : après convergence, les
  trois pages s'affichent « 2/5 » et « 4/5 ». Le public voit une numérotation
  fausse et une barre de progression qui saute.

C'est donc un outil de relecture, commode pour recompiler vite la slide sur
laquelle on travaille, et rien d'autre. Ne jamais projeter le résultat.

### Ce qui marche : un maître par variante, des fragments partagés

Mesuré le même jour : numérotation correcte et propre à chaque variante
(« 2/4 » à « 4/4 » contre « 2/5 » à « 5/5 »), pages de section conservées.

La bascule d'un deck monolithique vers cette structure est mécanique, donc
outillée. `scripts/deck_fork.py deck.tex --nom court` découpe les fragments,
écrit les deux maîtres et **contrôle que le PDF de référence garde exactement
sa longueur** : une refactorisation qui change le rendu a cassé quelque chose,
et le script refuse de laisser passer. Mesuré sur un deck de 34 pages le
2026-09-10 : 34 pages avant, 34 après, et l'audit rend les mêmes cinq FAIL et
onze WARN aux mêmes slides, désormais situés en `corps.tex:20`.

```
2026-09-10_sdis/
  preambule.tex      thème, langue, titre, macros, \tikzset partagés
  corps.tex          le contenu, source unique de tous les chiffres
  deck.tex           \newif\ifgxlong \gxlongtrue  \input{preambule} …
  deck_court.tex     \newif\ifgxlong \gxlongfalse \input{preambule} …
```

```latex
% deck.tex — version de référence, 30 min
\documentclass[aspectratio=169,11pt]{beamer}
\newif\ifgxlong \gxlongtrue
\input{preambule}
\begin{document}
\input{corps}
\end{document}
```

```latex
% corps.tex — trois cas d'usage du booléen
\begin{frame}{Ce que la machine rend}…\end{frame}   % dans toutes les variantes

\ifgxlong
\begin{frame}{Le détail du calcul}…\end{frame}      % longue seulement
\fi

\ifgxlong\else
\begin{frame}{En un mot}…\end{frame}                % courte seulement
\fi
```

Une fois les fragments en place, poser les conditionnels. Mesuré sur ce même
deck réel : la version courte tombe de 34 à 29 pages et sa numérotation de pied
de page suit, « x/15 » là où la référence affiche « x/20 ». C'est exactement ce
que `\includeonlyframes` ne sait pas faire.

Le troisième cas est le plus important, et c'est celui qu'on oublie. **Une
version courte n'est pas la version longue tronquée.** Supprimer une slide sur
deux détruit l'arc et laisse les points de bascule sans preuve. Il faut rejouer
le geste 3 avec la nouvelle durée, puis le geste 4 : des items NOYAU deviennent
APPUI, des APPUI deviennent MENTION, et trois slides développées fusionnent en
une slide de synthèse qui n'existe que dans la courte. C'est du travail de
conception, pas de la coupe.

Règle qui commande le découpage : **un chiffre, une source**. Tout ce qui est
mesuré, daté ou cité vit dans le fragment partagé. Si un nombre apparaît dans
deux fichiers, la prochaine correction n'en touchera qu'un, et la variante non
corrigée sera projetée un jour, devant quelqu'un qui a lu l'autre.

### La traduction

Même mécanisme, mais le partage se déplace : deux corps, `corps_fr.tex` et
`corps_en.tex`, un seul préambule et un seul jeu de figures. Le texte ne se
partage plus, les objets visuels si, ce qui est justement là où est le travail.
`notes_orateur.md` se dédouble par langue de l'oral, jamais par langue des
slides : les deux sont indépendantes (geste 1).

### Le contrôle des variantes

Chaque variante s'audite **séparément, avec sa propre durée** :

```bash
python3 scripts/slide_audit.py deck.tex       --duree 30 --pixels
python3 scripts/slide_audit.py deck_court.tex --duree 15 --pixels
```

Le script suit les `\input` et situe chaque défaut dans son fragment
(« corps.tex:37 »). Trois codes lui sont propres : `S0` aucune frame trouvée
alors que le PDF en compte, ce qui signale un fragment non résolu et invalide
tout le rapport ; `S1` un `\input` introuvable, dont le contenu n'est donc pas
audité ; `S2` la liste des fichiers effectivement lus, à vérifier d'un coup
d'œil.

Ce garde-fou n'est pas décoratif. Avant le 2026-09-10, l'audit d'un deck
fragmenté rendait « 0 FAIL, 0 WARN » sur zéro slide pour un PDF de sept pages :
un feu vert entièrement faux, le pire mode d'échec possible pour un outil de
contrôle.

Le contrôle visuel, lui, se refait **entièrement sur la variante**. Une slide
qui tient dans la longue peut déborder dans la courte : la fusion de trois
slides en une est précisément l'endroit où le contenu déborde du cadre.

## Le registre des variantes

Les variantes d'un même exposé vivent dans **un seul répertoire**, avec leurs
maîtres côte à côte. Le répertoire par exposé sépare des exposés, pas des
formats du même exposé. `plan_presentation.md` porte alors une section :

```markdown
## Variantes

| Maître | Durée | Public | Écart au deck de référence | Présentée le |
|---|---|---|---|---|
| `deck.tex` | 30 min | SDIS partenaire | référence | 2026-09-18 |
| `deck_court.tex` | 15 min | comité de pilotage | sans les huit familles détaillées ; « En un mot » fusionne 6 à 9 | jamais |
```

La colonne « présentée le » est ce qui empêche, deux ans plus tard, de rouvrir
le mauvais fichier la veille d'une réunion.

## Erreurs à éviter

- **Ajouter sans rendre la monnaie.** Les decks du parc n'ont pas été écrits
  trop longs, ils le sont devenus.
- **Insérer là où il reste de la place** plutôt qu'au maillon que l'ajout sert.
- **Appeler variante ce qui est un autre exposé**, parce que le mot fork est
  flatteur et que repartir du geste 1 semble coûteux.
- **Projeter un `\includeonlyframes`.** Numérotation fausse, sections perdues.
- **Fabriquer la courte en supprimant des slides** au lieu de rejouer le budget
  et les rangs.
- **Dupliquer un chiffre entre deux fragments.**
- **Auditer la seule variante de référence.** Chacune se contrôle avec sa durée.
- **Copier un répertoire pour faire une variante.** Deux copies divergent dès la
  première correction, et rien ne le signale.
