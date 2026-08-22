---
name: notes-et-citations
description: >-
  Met un écrit juridique aux conventions de la doctrine française AVANT sa
  production : références détaillées en notes de bas de page (jamais en appel
  abrégé dans le corps), première citation complète puis rappels abrégés,
  vérification de chaque décision de justice et de chaque texte normatif à la
  source officielle. Norme de référence : la thèse de Camille Aynès, référente
  du domaine. À exécuter AVANT toute production de livrable dans un projet de
  droit (article, communication, chapitre, note, rapport, mémoire), et non
  après : les conventions se posent en entrant dans la rédaction, se corriger
  ensuite coûte une relecture intégrale. Déclencher aussi quand l'utilisateur
  demande de citer correctement, de mettre les références en notes, de vérifier
  une citation de jurisprudence, de contrôler un appareil de notes, ou avant
  d'envoyer un texte juridique à un tiers.
argument-hint: "[chemin du livrable ou du projet]"
---

# /notes-et-citations : l'appareil de notes d'un écrit juridique

Ce skill fait deux choses que l'on confond souvent : il pose les **conventions**
de citation d'un écrit juridique, et il **vérifie** que ce qui est cité existe et
dit ce qu'on lui fait dire. La première sans la seconde produit un appareil de
notes impeccable et faux.

Il s'exécute **avant** la rédaction du livrable. C'est le point qui le distingue
d'un correcteur de style : une convention de citation adoptée en cours de route
oblige à reprendre tout ce qui précède, et une référence vérifiée après coup l'est
rarement.

## Préalable, dans l'ordre

1. Lire la mémoire du projet : `cahier_de_labo.md`, `etat_des_decouvertes.md`,
   `CLAUDE.md` local. Un projet de droit a souvent déjà des conventions écrites,
   et les siennes l'emportent sur celles de ce skill.
2. Charger la norme détaillée : `references/norme-aynes.md`. Elle est établie par
   relevé sur la thèse de Camille Aynès et sur ses articles récents, chaque règle
   étant accompagnée de deux exemples réels. **Ne pas reconstruire ces règles de
   mémoire** : c'est exactement ainsi qu'on fabrique une norme plausible et fausse.
3. Établir avec l'auteur trois choses, et les écrire en tête du livrable :
   le **type d'écrit** (article, communication orale, chapitre, note), la **cible**
   (revue, éditeur, colloque) et sa **feuille de style** si elle en impose une.
   Une revue qui impose ses conventions prime sur la norme d'usage.

## Les cinq règles qui structurent tout

Le détail, les variantes et les exemples sont dans `references/norme-aynes.md`.
Ce qui suit est ce qui ne se négocie pas.

1. **La référence vit dans la note, pas dans le corps.** Le corps porte
   l'argument et, au plus, le nom de l'auteur ou de la décision quand la phrase
   en a besoin pour se lire. Tout le reste (titre, éditeur, année, page, numéro
   de décision, recueil) descend en note. On n'écrit pas un appel de type
   auteur-date entre parenthèses : ce n'est pas la convention de la discipline.
2. **La première citation est complète, les suivantes sont abrégées.** La forme
   abrégée doit rester résoluble : un `op. cit.` orphelin, séparé de sa première
   occurrence par cent pages, est une référence perdue. En cas de doute, répéter
   un titre court plutôt que d'abréger.
3. **La note peut discuter.** Chez Aynès, la note n'est pas qu'un renvoi : elle
   porte des contre-points, des nuances, de la doctrine adverse. C'est un usage à
   conserver, et c'est ce qui distingue un appareil juridique d'une bibliographie.
   Ce qui affaiblirait l'argument principal sans le contredire va en note ; ce qui
   le contredit reste dans le corps.
4. **Aucune décision ni aucun texte normatif n'est cité sans vérification à la
   source.** Utiliser le skill `legifrance` (Légifrance et Conseil constitutionnel).
   Recopier depuis la sortie de l'outil, jamais depuis la mémoire ni depuis une
   note de lecture.
5. **Citer une source, c'est l'avoir ouverte.** Une référence reprise d'une autre
   référence se signale comme telle (`cité par`), elle ne se maquille pas en
   lecture directe.

## Les quatre façons dont un appareil de notes devient faux

Elles sont observées, pas imaginées, et aucune ne se voit à la relecture.

- **L'identifiant juste portant une citation fausse.** Le pire cas : le numéro de
  décision existe, il se résout, et le passage qu'on lui attribue n'est pas le sien.
  La note est vérifiable en apparence, donc personne ne la revérifie. Parade :
  faire rendre à l'outil le **texte** du considérant cité, pas seulement confirmer
  que la décision existe.
- **La liste d'auteurs.** C'est le champ le moins contrôlé d'une référence : titre,
  revue et année exacts, et des coauteurs inventés au milieu. Au-delà de trois
  auteurs, recopier la liste depuis la source, jamais depuis la génération.
- **Le texte renuméroté.** Un article de code déplacé, une loi refondue, une
  décision republiée : la référence ancienne reste vraie pour l'état ancien du
  droit et fausse pour l'état courant. Toute citation de texte normatif porte la
  **version** à laquelle elle renvoie quand l'article a bougé.
- **L'absence datée.** « Aucune jurisprudence sur ce point » est une affirmation
  forte déguisée en prudence, et elle périme vite. La dater, et dire où l'on a
  cherché.

## Procédure

1. **Inventorier** les énoncés du livrable qui appellent une référence :
   affirmation de droit positif, citation textuelle, attribution d'une thèse à un
   auteur, chiffre, mention d'une décision.
2. **Classer** chaque référence par type (ouvrage, article, contribution dans un
   collectif, décision, texte normatif, travaux parlementaires, archive) : la
   forme de la note dépend du type, et `references/norme-aynes.md` donne la forme
   exacte de chacun.
3. **Vérifier** décisions et textes normatifs à la source ; pour la doctrine,
   vérifier au moins auteur, titre, année et pagination.
4. **Rédiger** les notes, première occurrence complète, suivantes abrégées.
5. **Tenir un registre** dans le projet (`notes_check.md`) : une ligne par
   référence, avec son statut (vérifiée à la source, vérifiée partiellement, non
   vérifiée) et la date. Sans registre, la vérification n'est pas rejouable et il
   faudra tout refaire à la révision suivante.
6. **Signaler** à l'auteur ce qui n'a pas pu être vérifié, plutôt que de le laisser
   passer en silence. Une référence non vérifiée et dite telle est un problème
   ouvert ; non dite, c'est une erreur en attente.

## Ce que la norme ne couvre pas encore

Le relevé est établi sur les notes de bas de page de la thèse et de deux articles
récents. Il déclare lui-même ses trous, et il faut les traiter comme tels plutôt
que d'improviser une règle qui aurait l'air juste.

- **La citation d'ARCHIVES n'est pas établie.** Aucune cote, aucun dossier
  nominatif, aucune pièce manuscrite dans le corpus observé. C'est précisément ce
  dont un travail sur des archives a besoin : la règle est donc à demander à
  Camille Aynès, et non à déduire. En attendant, citer une pièce d'archive avec
  son fonds, sa cote, sa date, sa nature et sa page ou son image, et le dire.
- **Les sigles de revues** sont employés sans table développable (`RD publ.`,
  `RFDC`, `LPA`, `Gaz. Pal.`, `RSC`, `AJ pénal`, `Dr. adm.`, `RPC`). Le projet
  doit tenir la sienne.
- **Neuf points varient** chez elle (séparateur entre deux auteurs, place du lieu
  d'édition, forme de la coupe, `préc.` contre `cit.`, ordre date/numéro au
  Conseil constitutionnel…). Sur ces points, **ne rien imposer** : suivre l'usage
  déjà en place dans le document, et rester cohérent à l'intérieur d'un même écrit.
- **Attention à la contrainte éditoriale.** Son article de 2025 compose les noms en
  petites capitales et écrit `n°` avec le symbole degré : c'est la revue qui
  l'impose, pas elle. Ne pas reprendre ces traits comme norme par défaut.

## Ce que ce skill ne fait pas

Il ne juge pas le fond du raisonnement juridique, il ne choisit pas la revue, et
il ne réécrit pas l'argumentation. Pour la critique de fond d'un manuscrit, voir
`manuscript-review` ; pour le style et l'économie du texte, `deai-latex` ; pour la
vérification des affirmations elles-mêmes, `claim-check`.

## Référente du domaine

Les conventions retenues sont celles de **Camille Aynès** (maîtresse de
conférences en droit public, Université Paris Nanterre), établies par relevé sur
sa thèse (*La privation des droits civiques et politiques. L'apport du droit pénal
à une théorie de la citoyenneté*, Dalloz, 2022) et sur ses publications récentes.
Toute évolution de la norme se décide avec elle, et se répercute dans
`references/norme-aynes.md`, jamais dans ce fichier.
