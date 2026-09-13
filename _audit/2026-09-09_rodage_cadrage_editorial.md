# Rodage à blanc du skill `cadrage-editorial` — 2026-09-09

Première exécution réelle de la passe, sur le manuscrit `mtbc/variant_nucs` (porte 3bis
franchie le 2026-09-07, verdict SOUMETTRE, niveau AVANCÉE). Objet du rodage : éprouver la
mécanique avant que son point de contrôle bloquant n'intervienne sur une vraie soumission.

Cible de rodage : `microbial-genomics`. Choisie comme hypothèse de travail, pas comme cible
retenue : le choix de revue appartient à l'auteur, et cette revue est de fait écartée pour lui
par un APC gold de 2 203 GBP sans dispense applicable (fiche vérifiée le 2026-08-25). Les
mesures restent valides comme test du dispositif.

Aucune écriture dans `mtbc/variant_nucs` : pas de `cadrage_editorial.md` créé, aucune retouche
appliquée au manuscrit. Un verdict de cadrage écrit pour une revue que l'auteur n'a pas arrêtée
aurait pollué le registre du projet et faussé le pré-vol.

## Ce que le temps 1 a mesuré

Corpus Europe PMC de Microbial Genomics sur douze mois : 300 références récoltées, 283
exploitables après filtrage des éditoriaux et errata.

| Mesure | Revue | Manuscrit |
|---|---|---|
| Longueur de titre | 15 mots médians, p10-p90 10-20 | 12 mots |
| Titres interrogatifs | 0 % (1 titre sur 283) | oui |
| Nom d'espèce en tête | 63 % | non |
| Méthode affichée dans le titre | 11 % | non |
| Longueur de résumé | 236 mots médians, p10-p90 163-305 | 524 mots, percentile 100 |
| Résumés structurés | 12 % | non |

Cinq écarts francs remontés, dont trois lexicaux. Les deux qui portent : un résumé au
percentile 100 de la distribution (limite de résumé de la revue non vérifiable, page
d'instructions en 403, donc risque non quantifiable mais réel au collage dans le portail), et
un titre interrogatif dans une revue qui n'en publie pas.

## Deux défauts de mesure trouvés et corrigés

Le rodage a produit son bénéfice principal sous forme de bugs, tous deux dans
`scripts/corpus_fit.py` et corrigés avec leur commentaire d'origine.

**Titre interrogatif à question interne non détecté.** L'heuristique testait
`title.endswith("?")` ; le titre candidat est « Homoplasy or artefact? Re-examining... », dont
le point d'interrogation est au milieu. L'écart le plus visible du dossier passait donc
inaperçu. Corrigé en testant la présence du caractère n'importe où dans le titre.

**Balisage HTML échappé dans les données Europe PMC.** 207 des 300 titres et 248 des 300
résumés portent des balises d'italique échappées (`&lt;i&gt;`). Conséquence : un nom d'espèce en
italique en tête de titre échappait à la détection de binôme, et surtout toute recherche
lexicale d'une expression à cheval sur une balise rendait zéro par artefact. Mesuré :
« Mycobacterium tuberculosis complex » comptait zéro occurrence dans un corpus qui en porte, la
balise fermante tombant entre le deuxième et le troisième mot. Corrigé par une fonction
`unmarkup` appliquée à la récolte et, rétroactivement, à la lecture du cache, pour que les
caches déjà écrits ne restent pas faux.

Après correction, la part de noms d'espèce en tête passe de 61 à 63 % et celle des résumés
structurés de 11 à 12 %.

## Un enseignement de fond, versé au SKILL.md

Un zéro lexical brut n'est pas un signal exploitable tant que ses variantes n'ont pas été
instruites. Mesuré sur ce corpus : `homoplasy` zéro occurrence mais `recurrent` cinq et
`convergent` deux ; `reference strain` zéro mais `reference genome` vingt-huit. Un zéro brut
aurait conclu à la mauvaise cible, alors que la revue avait publié dans l'année deux articles
directement voisins du sujet, « Hybrid sequencing reveals incompleteness of the H37Rv reference
genome... » et « Reference-free clustering as an epidemiological tool for Mycobacterium
tuberculosis lineage typing ». La conclusion juste est un vocabulaire à aligner, retouche
légitime et bornée, non un changement de cible.

Corollaire ajouté au skill : les articles les plus proches trouvés dans le corpus servent deux
fois, comme exemples pour la simulation et comme vérification du critère 2 du choix de revue
par une autre voie que la requête par méthode.

## Constat de cadrage relevé au passage

`article/main.tex` de `variant_nucs` ne porte aucun mot-clé et aucune lettre d'accompagnement.
Les deux font partie du matériel que l'éditeur lit, et leur absence est un point de cadrage à
traiter avant dépôt, non un oubli de forme.

Signalé aussi, hors périmètre de cette passe : la fiche de `microbial-genomics` cite
`10.1099/mgen.0.001690` (biais de référence et de lignée), voisin immédiat de la thèse du
manuscrit. À vérifier comme citation attendue par un relecteur, ce qui relève de `/bib-check`.

## Temps 2, simulation de rejet éditorial

Déléguée à une session Claude indépendante de cette machine (`bovis-full-2b`), avec pour seul
matériel le titre, le résumé, le scope, la limite de résumé déclarée non vérifiée, et les trois
articles les plus proches du corpus. Le protocole complet est dans
`skills/cadrage-editorial/references/simulation-desk-reject.md`.

À noter pour l'usage courant : le skill prévoit une délégation par sous-agent, qui reste la voie
normale. Le passage par une session voisine a été employé ici parce que cette session-ci n'avait
pas d'autorisation de sous-agents, et il a l'avantage d'une indépendance réelle plutôt que
simulée.

## État du dispositif après rodage

La chaîne mesure, simulation, retouche, verdict tient ; les deux corrections portaient sur les
mesures, pas sur la structure de la passe. Le point de contrôle de `preflight.py` a été validé
séparément sur ses cinq branches (registre absent, revue différente, `RETOUCHER`, `ALIGNE` avec
empreinte inchangée, vitrine modifiée après cadrage).

Ce qui reste non éprouvé : le temps 3 en conditions réelles, c'est-à-dire des retouches
effectivement appliquées à un manuscrit puis revérifiées jusqu'au point fixe, ce qui demande une
cible arrêtée par l'auteur.

## Résultat du temps 2, reçu de `bovis-full-2b`

Verdict rendu : RELECTURE, pas desk-reject, au motif que le sujet est au coeur du scope et
recoupe un article publié par la revue dans l'année sur l'incomplétude de H37Rv. Réserve posée
d'emblée : restructuration du résumé et passage sous la limite avant envoi aux relecteurs.

La reformulation « ce que je crois que ce papier fait » est fidèle au manuscrit, ce qui est le
signal le plus utile du protocole : le résumé transmet correctement sa thèse. Les quatre
incompréhensions relevées portent toutes sur des informations que le manuscrit contient, donc sur
la vitrine et non sur le fond : jeu de données de remplacement jamais dimensionné alors que
l'argument repose sur sa supériorité, nombre de génomes du clade non donné, article source non
nommé, et apport positif non énoncé au-delà de la correction. Ces quatre points sont exactement le
matériau de retouche que le temps 3 doit traiter, et aucun n'exige de toucher aux Résultats.

Sur la forme, la simulation retrouve sans les mesures ce que le temps 1 avait mesuré : résumé trop
long, non structuré là où l'article voisin l'est, titre interrogatif quand les publiés sont
déclaratifs. Convergence de deux instruments indépendants sur le même diagnostic.

## Limite structurelle du temps 2, relevée par la session sollicitée

Remarque qu'elle formule elle-même comme un résultat sur le skill : une simulation qui ne voit que
la vitrine ne peut pas distinguer un manuscrit mince d'un manuscrit dense mal résumé, et son
incompréhension principale portait ici sur une information que le manuscrit contient certainement.

C'est juste, et ce n'est pas un défaut à corriger : c'est la propriété qui fait la valeur du test,
puisque l'éditeur réel est dans la même position. La conséquence pratique est une règle de lecture,
versée dans `references/simulation-desk-reject.md` : une incompréhension portant sur une
information présente dans le manuscrit est un défaut de vitrine et vaut retouche due ; seule une
incompréhension portant sur une information réellement absente du manuscrit interroge le fond.

Second point relevé : la limite de résumé étant déclarée non vérifiée (page en 403), le constat de
forme ne repose que sur les trois articles du corpus, ce qui est plus faible qu'une règle de la
revue mais reste utilisable. La déclaration explicite du non-vérifié a donc fonctionné comme prévu,
sans conduire l'instance à inventer une limite.

## Illustration canonique de ce que la passe est censée produire

Le second échange avec la session sollicitée a livré le cas d'école que le SKILL.md décrivait en
abstrait. Sur le manque le plus sérieux (aucun apport positif énoncé au-delà de la correction
d'un article), elle a relevé que le recodage à trois états présent, absent, non couvert, appuyé
sur une profondeur de séquençage par gène, est un apport méthodologique transposable bien au-delà
du codon étudié, et que le résumé ne le présente que comme un moyen au service de la réfutation.

Le remonter au rang de contribution ne demande ni analyse nouvelle, ni chiffre nouveau, ni
retouche des Résultats : le fait est déjà dans le manuscrit, seule sa mise en avant change. C'est
la définition exacte du périmètre de la passe, et la preuve que « changer ce qui est mis en avant »
peut se faire sans rien promettre de plus que ce que la preuve soutient.
