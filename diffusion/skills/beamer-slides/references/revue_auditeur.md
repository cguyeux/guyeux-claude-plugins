# La revue par auditeur simulé

## Le principe

Un pipeline de contrôle prouve qu'un deck est bien fait. Il ne dit pas s'il sera
bien reçu. La revue comble cet écart en se mettant dans la peau du public
déclaré au geste 1, et en rendant ce que cette personne aurait pensé sans le
dire.

**Déléguer à une instance indépendante de celle qui a rédigé le deck.** L'auteur
d'une slide ne voit pas ce qu'elle ne dit pas : il complète mentalement avec ce
qu'il sait. C'est la même raison qui fait déléguer le contrôle de nouveauté de
la porte 3bis.

Entrées de la revue : le deck rendu en PNG, `notes_orateur.md`,
`notes_techniques.md`, `plan_presentation.md`, et le cadrage.

## Ce que la revue examine

**Le fond.** La thèse est-elle identifiable dès les trois premières minutes ?
Chaque maillon est-il établi avant d'être utilisé ? Les points de bascule
tuent-ils vraiment l'explication concurrente, ou l'écartent-ils par assertion ?
Les réserves sont-elles dites, ou attend-on qu'on les trouve ?

**La forme.** Y a-t-il des slides qu'on ne comprend pas en dix secondes ? Des
slides trop chargées ? Des figures dont on ne sait pas ce qu'il faut regarder ?
Le deck se répète-t-il visuellement ? Les titres sont-ils des assertions ou des
étiquettes ?

**L'équilibre.** Le temps est-il réparti conformément à l'enjeu de chaque partie ?
Le défaut le plus fréquent est l'introduction expédiée : la salle n'a pas eu le
temps de comprendre pourquoi la question se pose, et tout ce qui suit tombe à
plat. Le second est la chute arrivée sans préparation.

**Le texte à dire.** Les notes sont-elles trop détaillées ici et trop maigres
là ? Les transitions existent-elles ? Le texte répète-t-il la slide au lieu de
l'augmenter ? Le budget de temps est-il tenable en le lisant à voix haute ?

## Ce que le public déclaré change

| Public | Ce qu'il pardonne | Ce qu'il ne pardonne pas |
|---|---|---|
| Spécialistes | une introduction rapide | une méthode non justifiée, une réserve tue, une référence manquante |
| Biologistes non informaticiens | une notation approximative | un algorithme présenté comme une boîte noire, une statistique non interprétée |
| Informaticiens non biologistes | un détour biologique | une motivation floue, l'absence de définition du problème |
| Jury pluridisciplinaire | une simplification assumée | un jargon non défini, une absence de fil, une trajectoire illisible |
| Étudiants | la lenteur | un implicite, un saut logique, un vocabulaire non introduit |
| Grand public | tout sauf l'ennui | un acronyme, une équation, une nuance qui noie le message |

Une revue qui rendrait les mêmes remarques quel que soit le public n'a pas fait
son travail.

## Le format de sortie

Structure de `manuscript-review`, adaptée. Fichier `revue_auditeur.md` daté dans
le répertoire de la présentation.

````markdown
# Revue d'auditeur — Le pathogène comme archive sociale
2026-09-15 · dans la peau d'un microbiologiste MTBC, non spécialiste de
génétique des populations · deck de 14 slides pour 18 min

## Impression d'ensemble
Ce que j'ai compris, en une phrase. Ce que j'aurais su redire le lendemain.
Ce sur quoi je serais resté perplexe.

## I. Majeur
### 1. La slide 6 demande d'accepter le F_ST sans l'avoir défini
La slide affirme que 0,005 est faible, mais rien n'a dit ce qu'est un F_ST ni ce
qui serait fort. Un microbiologiste n'a pas cette échelle en tête, donc le
maillon ne passe pas et toute la suite repose dessus.
**Suggestion** : un encadré `\notion` de trois lignes, ou un repère visuel
comparant à des valeurs connues.

## II. Modéré
## III. Mineur
## IV. Points forts
## V. Recommandations
### Bloquantes
### Fortement souhaitables
### Souhaitables
````

## Ce que la revue doit faire, et ne pas faire

Elle **doit** être spécifique : « la slide 6 » et non « certaines slides ». Elle
doit dire ce qui bloque la compréhension, pas ce qui déplaît. Elle doit proposer
une correction praticable dans le temps disponible.

Elle **ne doit pas** réécrire l'exposé, ni proposer un autre message : le message
a été arbitré au geste 2, et le remettre en cause ici est hors de propos sauf s'il
n'est pas démontrable, auquel cas c'est un point majeur et il se dit comme tel.
Elle ne doit pas non plus répéter ce que l'audit mécanique a déjà signalé : les
débordements et les densités sont traités ailleurs, la revue parle de ce qu'aucune
mesure ne voit.

## Après la revue

Traiter les points bloquants, puis relancer l'audit mécanique : une correction de
fond rallonge presque toujours une slide. Les points non traités restent dans le
fichier avec leur motif. Une revue dont toutes les remarques ont disparu sans
trace n'a pas été utilisée, elle a été effacée.
