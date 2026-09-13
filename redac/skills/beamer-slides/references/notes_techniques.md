# `notes_techniques.md` : le soutien pédagogique et technique

## À quoi il sert

À tenir debout quand une question sort du script. Il porte ce que l'orateur doit
**comprendre** pour défendre ses slides, alors que `notes_orateur.md` porte ce
qu'il doit **dire**.

C'est aussi le fichier qui décharge les slides : une notion expliquée ici n'a
pas à encombrer l'écran. La règle du thème est explicite, un encadré `\notion`
sur une slide fait trois à cinq lignes, le détail vit ici.

## Ce qu'il doit couvrir, slide par slide

**Chaque métrique affichée** : sa définition en une phrase, ce qu'elle vaut
quand tout va bien et quand tout va mal, et surtout **pourquoi celle-là plutôt
qu'une autre**. Le « pourquoi ce choix » est la question de jury la plus
fréquente et la moins préparée.

**Chaque test statistique** : ce qu'il teste exactement, son hypothèse nulle,
ce que la valeur de p dit et ce qu'elle ne dit pas, la correction pour tests
multiples si elle s'applique, et la taille d'effet, qui est ce qu'on aurait dû
regarder d'abord.

**Chaque outil nommé** : ce qu'il fait, sur quelles données, ses hypothèses, ses
modes d'échec connus. « RAxML-NG » sur une slide appelle trois lignes ici.

**Chaque chiffre affiché** : sa valeur exacte, sa source, sa date. C'est le
matériau du contrôle de traçabilité.

**Les réserves** : ce que le résultat ne montre pas, les biais d'échantillonnage,
ce qui reste à consolider. Les dire soi-même vaut mieux que se les faire dire.

**Les questions probables et leurs réponses**, avec le renvoi à la slide
d'annexe.

## Le catalogue de notions

Le catalogue de `mtbc-bilan` sert de liste de départ, classé par domaine. Il vit
dans le plugin `bio_pathogens`, sous
`skills/mtbc-bilan/references/notions_pedagogiques.md`, donc il n'est lisible
que si ce plugin est actif dans la session. S'il ne l'est pas, ne pas bloquer :
construire la liste depuis le public déclaré, et le signaler.

Il couvre l'anthropologie et l'ethnolinguistique, la biologie et la génétique des
populations, la phylogénétique et l'évolution moléculaire, les statistiques
inférentielles, les outils et formats du domaine, et les concepts MTBC.

**Le tri se fait par le public déclaré au geste 1**, pas par exhaustivité. Devant
des microbiologistes, expliquer le F_ST et l'inférence bayésienne, pas la
tuberculose. Devant des informaticiens, l'inverse. Un fichier qui explique tout
n'aide personne.

## Le format

````markdown
# Notes techniques — Le pathogène comme archive sociale

Public : microbiologiste MTBC. Ce qui est supposé connu : lignées MTBC, spoligotypage,
RD, notions d'épidémiologie. Ce qui est expliqué ici : génétique des populations,
statistiques, phylogénétique quantitative.

---

## Slide 8 — Les peuples ouest-africains sont génétiquement quasi identiques

### La métrique : F_ST
Part de la diversité génétique totale attribuable à la différenciation **entre**
groupes plutôt qu'à la variation **à l'intérieur** des groupes. Varie de 0
(groupes indistinguables) à 1 (groupes sans allèle commun).

**Pourquoi F_ST et pas une distance génétique.** Une distance dit à quel point
deux groupes diffèrent ; F_ST rapporte cette différence à la variation interne,
donc il répond directement à « la frontière entre ces groupes est-elle
étanche ? ». C'est la question posée ici.

**Ordres de grandeur.** Entre populations humaines continentales, 0,10 à 0,15.
Entre populations européennes, 0,005 à 0,01. Nos valeurs, 0,005 à 0,006, sont
dans le second régime : à l'échelle ouest-africaine, la frontière génétique
n'existe pratiquement pas.

### Le chiffre affiché
0,005 à 0,006, estimateur de Weir et Cockerham, sur les quatre familles
linguistiques. Source : `etat_des_decouvertes.md` du 2026-07-06, section 5.

### La réserve
Estimé sur des panels publics dont l'échantillonnage par ethnie est inégal.
L'ordre de grandeur est robuste, le classement fin entre ethnies ne l'est pas.

### Question probable
> « Un F_ST de 0,005, ce n'est pas simplement un manque de puissance ? »

Non : le même jeu de marqueurs rend 0,06 sur le chromosome Y dans les mêmes
groupes. Ce n'est donc pas la puissance qui manque, c'est la structure qui est
absente sur l'autosomal. Voir annexe A3.
````

## La règle qui commande le reste

**Aucune affirmation ici ne doit être plus assurée que dans
`etat_des_decouvertes.md`.** C'est le fichier que l'orateur relira sous pression
et dont il tirera ses réponses ; y glisser une certitude que le projet n'a pas
est le moyen le plus direct de se faire prendre en défaut en séance.
