# Le cadrage : quatre paramètres, et ce que chacun commande

Un exposé sans cadrage explicite hérite par défaut du cadrage de l'article, qui
n'en est jamais un : l'article s'adresse à un relecteur spécialiste, sans limite
de temps, dans une seule langue. Les quatre paramètres ci-dessous ne sont pas
des préliminaires administratifs, ils décident du contenu.

## 1. L'occasion

| Occasion | Intensité | Durée usuelle | Ce qu'elle change |
|---|---|---|---|
| Séminaire d'équipe | académique | 30 à 60 min | On peut entrer dans la méthode, l'auditoire reviendra la semaine suivante. Annexes peu utiles. |
| Conférence | académique | 12 à 20 min | Une seule thèse, une seule preuve par maillon. Le public décide en trois minutes s'il écoute. |
| Audition, recrutement | affirmée | 15 à 25 min + questions | Le jury évalue une trajectoire, pas un résultat. Prévoir un tiers d'annexes, elles seront demandées. |
| Soutenance | affirmée | 40 à 50 min | La démonstration doit être complète et traçable. Les annexes sont un second deck. |
| Cours | académique | 1 à 2 h | Le rythme se relâche, les notions s'expliquent sur la slide et pas seulement en annexe. |
| Grand public | affirmée | 20 à 45 min | Aucune notation, aucun acronyme. Une image par idée. Le chiffre remplace le tableau. |
| Réunion de projet | académique | 10 à 20 min | On montre l'état et la décision demandée, pas la démonstration. |

L'occasion fixe l'option du thème, `academique` ou `affirmee`, et rien d'autre
ne la fixe : ne pas la déduire de l'humeur.

## 2. Le public réel

La question n'est pas « qui est invité » mais « qui va effectivement écouter, et
que sait cette personne ». Un séminaire annoncé comme pluridisciplinaire réunit
souvent trois spécialistes et douze curieux : c'est pour les douze qu'on écrit
l'introduction, et pour les trois qu'on prépare les annexes.

| Public | Suppose connu | À expliquer systématiquement |
|---|---|---|
| Spécialistes du domaine | lignées, marqueurs, outils, nomenclature | seulement ce qui est neuf ou contesté |
| Biologistes non informaticiens | biologie, évolution, échantillonnage | ce que fait l'algorithme, ce que mesure la statistique, ce qu'un arbre garantit et ce qu'il ne garantit pas |
| Informaticiens non biologistes | statistiques, arbres, complexité | l'objet biologique, pourquoi la question se pose, ce qu'est un isolat |
| Jury pluridisciplinaire | rien de commun | chaque notion à sa première apparition, en une phrase, sans jamais s'excuser |
| Étudiants | le programme de leur année | la totalité du vocabulaire, et le pourquoi avant le comment |

Le public commande directement `notes_techniques.md` : les notions à y détailler
sont celles que ce public précis n'a pas.

## 3. La durée

Demander deux choses, pas une : la durée totale, et si les questions sont
comprises dedans ou s'ajoutent. Un créneau de 20 minutes questions comprises
laisse 14 à 15 minutes de parole, pas 20. L'erreur coûte trois slides.

Demander aussi, quand l'occasion s'y prête, s'il existe une contrainte de fin
dure : un orateur suivant, un train, une fin de session. Si oui, prévoir un
point de sortie anticipé, c'est-à-dire une slide après laquelle l'exposé reste
complet même si les suivantes sautent, et le noter dans `notes_orateur.md`.

## 4. Les deux langues

Les demander séparément, toujours. Les combinaisons réelles :

| Slides | Oral | Livrables |
|---|---|---|
| français | français | notes orateur en français |
| anglais | anglais | notes orateur en anglais, plus une version française si l'orateur prépare en français |
| anglais | français | slides en anglais, notes orateur en français. Cas fréquent en France. |
| français | anglais | rare, mais légitime devant un public francophone avec un intervenant étranger |

Le piège : écrire les notes dans la langue des slides par automatisme. Les notes
servent à l'orateur, elles suivent la langue de l'oral, et la version dans
l'autre langue s'ajoute si elle sert à préparer.

Quand les slides sont en anglais et l'oral en français, ne pas traduire les
titres dans les notes : l'orateur doit voir à l'écran ce que voit la salle.

## Ce qu'il faut faire de ces réponses

Les écrire en tête de `plan_presentation.md`, dans le bloc machine-lisible du
gabarit. Tout le reste du skill les relit : le budget de temps vient de la
durée, la sélection des notions vient du public, l'intensité du thème vient de
l'occasion, et les livrables viennent des langues.
