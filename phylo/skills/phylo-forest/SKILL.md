---
name: phylo-forest
description: >-
  Bibliothèque interrogeable des arbres phylogénétiques déjà calculés dans un
  dépôt de recherche : moissonne les Newick existants, en extrait une fiche
  (outil, modèle, alignement, taxons, composition par clade avec son système
  taxonomique), et répond à « ai-je déjà un arbre qui ferait l'affaire ? » AVANT
  de relancer un calcul. Rend aussi des FORÊTS pour les statistiques
  inter-arbres qu'un arbre isolé ne permet pas (fréquence d'un clade à travers
  des reconstructions indépendantes).

  Use when: avant tout RAxML / IQ-TREE / FastTree, pour chercher un arbre
  existant ; après un calcul, pour le verser à la forêt ; pour retrouver l'arbre
  d'une figure ; pour mesurer la stabilité d'un clade entre études.
argument-hint: "[find --clade L4.13 | find --taxa SRR1,SRR2 | show <id> | support --taxa … | cite [todo] | harvest | stats | annotate <id> \"question\"]"
user-invocable: true
allowed-tools: Bash, Read, Glob, Grep
---

# /phylo-forest : la forêt du dépôt, interrogeable

Un dépôt de phylogénomique produit des centaines d'arbres et en exploite chacun
une fois. Ils restent sur le disque, sans fiche, sous des noms comme
`T3.raxml.bestTree`, et le calcul suivant repart de zéro. Ce skill transforme ce
dépôt d'artefacts en **bibliothèque** : on cherche avant de calculer, et ce
qu'on calcule enrichit la bibliothèque.

```bash
F=~/docs/codes/claude_plugins/bio_pathogens/skills/phylo-forest/scripts/forest.py
python3 $F find --clade L4.13 --min 20      # un arbre couvrant ce clade existe-t-il ?
python3 $F find --taxa SRR1234567,ERR765432 # un arbre contenant ces souches ?
python3 $F show 7f3a1c9d2b               # la fiche complète d'un arbre
python3 $F support --taxa @groupe.txt       # ce groupe est-il un clade dans la forêt ?
python3 $F diverge                          # même jeu, topologies différentes ?
python3 $F clades --since 2026-07-06        # la taxonomie tient-elle dans la forêt ?
python3 $F unstable --since 2026-07-06      # quelles souches changent de place ?
python3 $F cite todo                        # quels arbres d'un manuscrit n'ont pas leur question ?
python3 $F harvest                          # récolter (après un nouveau calcul)
```

## Le principe : moissonner, pas enregistrer

Le dépôt disposait déjà d'un archivage sur déclaration explicite
(`investigate_phylo/history/`, alimenté par `get_phylo.py`). Mesuré le
2026-08-27 : **3 arbres archivés, aucun depuis le 15 mai 2026**, pour environ
1 800 fichiers d'arbres réellement produits. Ce n'est pas un défaut de
discipline, c'est un enseignement de conception : **un archivage qui coûte un
geste n'est pas alimenté.** Celui-ci ne coûte rien, il lit ce qui est déjà sur
le disque, et il est régénérable à tout moment.

Conséquence pratique : `harvest` est idempotent et rapide, on le relance sans y
penser. L'index vit dans `.forest/` à la racine du dépôt — dérivé, jamais lu
directement par un agent, hors suivi de version. Seul `notes.json` (les
questions annotées à la main) porte de l'information non régénérable, et le
moissonnage ne l'écrase jamais.

## La fiche d'un arbre, en cinq blocs

Ce qu'un Newick ne dit pas est exactement ce qui décide de sa réutilisabilité :
le modèle, l'alignement, la commande et le nombre de réplicats vivent dans les
fichiers voisins (`.raxml.log`, `.iqtree`, `.bestModel`) que personne ne relit.
Le moissonnage les récolte.

1. **Identité** — `tree_id` (contenu), `topo_sha` (topologie NON ENRACINÉE, donc
   stable si l'arbre est réenraciné sur un autre outgroup), `taxa_sha` (jeu de
   taxons). Trois clés qui répondent à trois questions différentes : le même
   fichier ? le même arbre ? les mêmes souches ?
2. **Provenance** — projet, tous les chemins où ce contenu existe, date, rôle
   (`ML best`, `consensus`, `réplicat bootstrap`, `arbre de départ`).
3. **Méthode** — outil et version, modèle, alignement source, nombre de sites,
   réplicats de bootstrap, graine, commande complète.
4. **Forme** — nombre de feuilles, enraciné ou non, longueurs de branches,
   supports (médiane et échelle 0-1 vs 0-100), longueur totale, hauteur
   racine-feuille, branche médiane, branches nulles, polytomies, nombre de
   splits informatifs.
5. **Contenu biologique** — composition par clade, **avec le système taxonomique
   nommé et daté** (voir ci-dessous), nombre de tips non reconnus, et traduction
   vers les autres nomenclatures.

Le champ `question` (la demande à l'origine du calcul) n'est PAS devinable : il
reste vide jusqu'à ce qu'on l'écrive avec `annotate`. Le moissonnage propose à
sa place un `contexte` tiré du chemin et du README voisin, présenté comme un
indice et jamais comme la question elle-même.

## Toujours nommer la taxonomie

Dire « cet arbre contient 40 souches de L4.13 » n'a pas de sens sans dire selon
quel système : le dépôt en connaît dix-huit (Coll, Napier, Freschi, Shitikov,
Lipworth, Zwyer, Coscolla, Thawornwattana…) et ils ne découpent pas le même
arbre de la même façon. La référence locale est `bdd/actuelle/`, système
**`guyeux/bdd-actuelle`**, et son état est lui-même daté puisqu'il bouge de
semaine en semaine — la fiche porte donc `snapshot: AAAA-MM-JJ`.

`show` traduit chaque clade vers les autres systèmes via
`global_supplementary/barcoding_v2/taxonomy_crossmap.tsv`, en n'affichant que
les correspondances au-dessus de 50 % de Jaccard : en dessous, écrire une
équivalence serait faire dire à la table le contraire de ce qu'elle mesure.

**Le piège de la date.** Un arbre de mai 2026 a été composé avec la taxonomie de
mai 2026. Si un clade a été redécoupé depuis, l'arbre reste juste — les souches
n'ont pas changé — mais l'étiquette de sa composition, elle, est recalculée avec
la taxonomie d'aujourd'hui. C'est voulu (on veut savoir ce que l'arbre contient
maintenant), et c'est aussi la première chose à vérifier avant de réemployer un
arbre ancien pour un argument taxonomique.

## Chercher un arbre

`find` classe les candidats par deux nombres qu'il faut lire ensemble :

- **couv** (couverture) — quelle part de ce qu'on demande est dans l'arbre ;
- **spéc** (spécificité) — quelle part de l'arbre est ce qu'on demande.

Une couverture de 1,00 avec une spécificité de 0,01 signale un arbre global où
les souches voulues sont noyées : utilisable pour situer, pas pour résoudre.
L'inverse signale un arbre focalisé mais incomplet. Aucun des deux n'est
meilleur dans l'absolu, cela dépend de la question — d'où l'affichage des deux
plutôt qu'un score unique qui trancherait à la place du lecteur.

Filtres : `--min-tips`, `--max-tips`, `--tool`, `--project`, `--since`,
`--support` (seulement les arbres à supports), `--rooted`, `--all`
(les arbres intermédiaires — départ, réplicats ML et bootstrap — sont écartés
par défaut : ce ne sont pas des reconstructions indépendantes).

## Statistiques de forêt : `support`

C'est ce qu'une bibliothèque permet et qu'un arbre isolé ne permet pas.
`support --taxa A,B,C,…` mesure la fréquence à laquelle un groupe forme un clade
**à travers toutes les reconstructions du dépôt qui contiennent assez de ses
membres**.

Un bootstrap mesure la robustesse au rééchantillonnage des SITES, dans un arbre,
sous un modèle, sur un jeu de taxons. Cette mesure-ci porte sur la robustesse au
changement d'échantillonnage des TAXONS, de modèle, d'outil et d'analyste. Un
clade qui survit à quarante reconstructions indépendantes est appuyé autrement
qu'un clade à 100 de bootstrap dans l'unique arbre où il ait jamais été testé.

**Deux réserves à porter avec le chiffre, toujours.** Les arbres du dépôt ne
sont pas indépendants : ils partagent des alignements, la référence H37Rv, un
pipeline et ses biais, donc un taux n'est pas une probabilité postérieure. Et un
groupe absent d'un arbre n'y est pas réfuté, il n'y est pas testé — d'où
l'affichage du nombre d'arbres réellement testés à côté du taux.

## Quand le même jeu est reconstruit deux fois : `diverge`

```bash
python3 $F diverge
```

Regroupe les arbres par jeu de taxons strictement identique, ne garde que ceux
qui ont donné plusieurs topologies, et calcule entre elles une distance de
Robinson-Foulds normalisée. Surtout, il **stratifie par cause possible**, sans
quoi on additionne des divergences de natures différentes :

- **optimisation** — même outil, même alignement : l'inférence n'a pas convergé
  au même optimum ;
- **alignements** — même outil, alignements différents : les données d'entrée
  ne sont pas les mêmes ;
- **outils** — l'inférence elle-même diffère.

Mesuré sur `mtbc/` le 2026-08-30 : 228 jeux à topologies multiples, dont **183
de la seule optimisation** (RF médiane 0,052), 5 d'alignements (0,051) et 33
d'outils (0,027). Autrement dit, **relancer le même outil sur le même alignement
produit un arbre plus différent que changer d'outil** — un ordre de grandeur du
bruit de fond contre lequel tout effet méthodologique revendiqué doit être
comparé, et que la littérature du champ ne publie pas.

**Ce que ce mode ne dit pas.** Il ignore POURQUOI deux alignements diffèrent :
deux pipelines de variant calling distincts n'y apparaissent que comme « deux
alignements », ce qui interdit d'en tirer une conclusion sur un pipeline
particulier. Et la stratification n'est pas contrôlée : le rattachement d'un
arbre à son log passe par le préfixe du nom de fichier, et une bonne part des
runs ne déclarent aucune graine. C'est un ordre de grandeur, jamais une mesure
d'expérience — laquelle demanderait N inférences à graines contrôlées sur un
alignement figé.

**Trois pièges déjà payés, que le mode évite désormais.** Un NEXUS BEAST
numérote ses feuilles et donne les noms dans un bloc `Translate` : sans
l'appliquer, deux sous-échantillons de souches entièrement différentes portent
le même jeu de taxons et sont comparés (mesuré à RF 1,000, purement artefactuel).
Un arbre de CONTRAINTE, qui ne porte que quelques splits, donne mécaniquement une
distance maximale contre une reconstruction complète : une résolution minimale
est exigée. Et un même alignement écrit tantôt en absolu tantôt en relatif se
compte comme deux, ce qui déplace des groupes d'une strate à l'autre.

**Une divergence trouvée n'est pas une anomalie.** Vérifié sur le cas le plus
spectaculaire du dépôt — 1 305 souches, six topologies, deux projets apparents :
c'était un diagnostic délibéré de l'effet du masquage des RD, exécuté et conclu
dans le cahier du projet concerné. Lire le cahier avant d'alerter qui que ce soit.

## Mettre la taxonomie à l'épreuve de la forêt : `clades`

```bash
python3 $F clades --since 2026-07-01
python3 $F clades --since 2026-07-01 --scope global          # à périmètre comparable
python3 $F clades --since 2026-07-01 --min-tips 200          # arbres de taille comparable
```

Pour chaque clade de la taxonomie locale, compte dans combien d'arbres son
groupe de souches ressort monophylétique, avec un **modèle nul** intégré :
les mêmes tests sur des groupes aléatoires de mêmes tailles dans les mêmes
arbres. Sans ce nul, un taux de confirmation ne veut rien dire. Mesuré sur
`mtbc/` : **80,3 % pour les clades réels contre 0,00 % au hasard**.

Quatre précautions sont câblées dans le mode, chacune payée par une mesure
fausse avant correction.

**La date d'abord.** Un arbre porte les étiquettes de la taxonomie du jour où
il fut construit ; un clade redéfini depuis y rassemble des souches alors
dispersées, et son « échec » mesure la distance entre la taxonomie
d'aujourd'hui et un arbre d'hier. Le taux monte de 39 % (avril) à 81 % (août)
pour cette seule raison. Toujours passer `--since`, et lire la ventilation par
mois que le mode affiche.

**Les conteneurs nus ensuite.** Sous la convention dir-mixte, les souches
basales ou non classées d'un clade vivent dans son répertoire propre, ses
sous-clades ayant les leurs : le contenu d'un conteneur nu est un GRADE, pas un
clade. Un nœud interne est donc testé avec toute sa descendance. Avant cette
correction, `L4.1` (8 389 souches, 7 sous-clades) ressortait « éclaté », et les
échecs semblaient concentrés sur une lignée qui, correctement testée, n'a aucun
problème.

**La fenêtre temporelle, et c'est le piège le plus coûteux.** `--since` doit être
postérieur à la dernière RESTRUCTURATION du clade testé, jamais une date ronde.
Mesuré : avec un seuil au 1er juillet, toute la charpente L6 ressortait à 0 % de
monophylie sur 11 à 16 arbres — signal massif, parfaitement cohérent avec l'état
déclaré du projet concerné, et entièrement faux : les répertoires `L6.*` dataient
du 3 au 5 juillet, donc la fenêtre incluait des arbres antérieurs à la charpente
testée. Bornée au 6 juillet, L6 disparaît des échecs. Une fenêtre mal choisie
fabrique un résultat crédible et indiscernable d'un vrai sans ce contrôle.

**La descendance se détecte par préfixe, donc un renommage la casse.** Le mode
signale les clades sans descendance déclarée qui dépassent 500 souches : c'est la
signature d'un conteneur nu dont la subdivision porte un autre nom (`L1`, 21 163
souches, subdivisé sous `L_1.*`). Leurs échecs sont attendus, pas informatifs.

**La portée des arbres, et c'est la correction la plus récente (P62).** Un arbre
FOCALISÉ sur un clade ne peut pas mettre ce clade à l'épreuve : toutes ses
feuilles y appartiennent. Agréger son taux de monophylie avec celui d'un arbre
GLOBAL fabrique une progression qui mesure l'essor des arbres focalisés, pas un
gain de qualité taxonomique. Mesuré : la série par mois montait de 14,8 % (2021)
à 91,5 % (août 2026), l'essentiel de l'écart venant des 4 277 arbres focalisés de
`lineage_navigator` sur 7 122. Le mode classe donc chaque arbre par la portée de
ses feuilles (la plus profonde étiquette de clade qui couvre ≥ 95 % d'entre
elles), affiche le recensement des portées, **rend deux séries par mois au lieu
d'une** et ajoute au tableau des échecs deux colonnes `n_glob`/`taux_g`
restreintes aux arbres globaux : un clade dont `n_glob` vaut 0 n'a jamais été
réellement testé. `--scope global` ou `--scope focalise` restreint la mesure à
une seule population. `--min-tips`/`--max-tips` sont désormais appliqués ici
aussi, sans quoi un arbre de 20 feuilles et un arbre de 30 000 se comparaient
alors que leur difficulté n'a rien de commun.

**La circularité enfin, et elle ne se corrige pas.** Les clades sont définis
par des marqueurs qui servent aussi à bâtir les alignements : un taux élevé ne
prouve rien. Deux sorties y échappent et ce sont les seules à lire — les clades
vus dans UN SEUL arbre, jamais mis à l'épreuve, et ceux qui ÉCHOUENT malgré
tout, c'est-à-dire qu'un groupe que tout conspire à confirmer s'éclate quand
même.

## Souches au placement instable : `unstable`

```bash
python3 $F unstable --since 2026-07-06 --min 5
```

Compare, pour chaque souche, le voisinage topologique — les feuilles du plus
petit clade la contenant — entre paires d'arbres. Sortie complète dans
`.forest/unstable.tsv`.

**Le contrôle est ce qui fait la mesure.** Une souche change de voisins soit
parce qu'elle est mal placée, soit simplement parce que ses voisins ne sont pas
dans l'autre arbre. Deux arbres ne sont donc opposés que si les voisins du
premier sont PRÉSENTS dans le second ; sinon le cas est écarté, ni stable ni
instable.

**Comparer les clades, pas les voisins.** Chez un organisme clonal, deux souches
séparées par zéro ou un SNP permutent d'un arbre à l'autre sans que rien ne
bouge : compter ces permutations donnait 17 % de souches « instables » sur
`mtbc/`, chiffre sans valeur. Le mode compare donc le clade majoritaire du
voisinage — il reste 1,5 %.

**Lire d'abord la ligne d'en-tête.** Elle donne le nombre de souches réellement
testables, et c'est souvent le vrai résultat : sur `mtbc/`, 7 204 des 7 208
souches testables sont des Bovis, parce que seule cette lignée a des arbres
récents assez recouvrants. Le silence du mode sur les autres lignées n'est pas
un résultat les concernant.

**Une souche listée est une candidate, jamais un verdict** : le désaccord peut
venir de l'arbre autant que de la souche. La suite est une grille QC
(`/strain-qc`, `/species-id`), pas une reclassification.

## Ce que les manuscrits montrent : `cite`

```bash
python3 $F cite              # toutes les figures d'arbre et leur arbre
python3 $F cite todo         # les arbres cités qui n'ont PAS de question
python3 $F cite unresolved   # les figures d'arbre dont l'arbre reste introuvable
```

Un manuscrit ne cite jamais un `tree_id` : il inclut une figure. Le mode
reconstruit le chaînon manquant — `main.tex` → `\includegraphics` → script qui
a produit la figure → chemin du Newick → fiche de la forêt — et rend les trois
issues qui comptent : l'arbre est retrouvé, l'arbre est **mort** (le script le
nomme, le fichier n'existe plus), ou la figure ne repose sur aucun arbre du
dépôt.

C'est ce mode qui donne un critère d'arrêt à l'annotation : *tout arbre montré
par un manuscrit porte sa question*. `cite todo` liste exactement ce qui reste.

**La légende est le second résolveur, et souvent le seul.** Un script sur trois
ne nomme aucun chemin d'arbre (la figure lit un CSV intermédiaire), mais la
légende, elle, annonce presque toujours son effectif : « 181~taxa »,
« 91-taxon dataset », « 151 representative MTBC genomes ». Ce nombre, cherché
parmi les arbres du même projet, retrouve l'arbre là où le code se tait.

**Quatre pièges, chacun payé par un faux résultat avant correction.**
`f"{p}.treefile"` livre au parseur un fragment d'extension qui ressemble à un
nom de fichier et matche alors *tous* les `.treefile` du dépôt (608 arbres pour
une figure). Un basename générique comme `T3.raxml.bestTree` désigne des
centaines d'arbres : il n'est accepté que si le projet du manuscrit lève
l'ambiguïté, et le projet prime toujours sur le nom seul. Les chemins codés en
dur pointent vers l'arborescence d'avant un déménagement du dépôt, et il faut
retomber sur le basename. Enfin `topology` désigne aussi le repliement d'une
protéine : sans garde-fou, toute figure de structure entre dans le décompte.

**Une figure sans arbre n'est pas une faute.** Beaucoup de cladogrammes de
manuscrit sont dessinés à la main (matplotlib, TikZ) pour illustrer une
topologie consolidée, et c'est légitime. Ce que le mode signale, c'est l'écart
entre ce que la légende annonce et ce que le dépôt contient — à lire, jamais à
conclure seul.

## Protocole (ce qui doit devenir un réflexe)

**Avant** de lancer RAxML / IQ-TREE / FastTree :

```bash
python3 $F find --clade <clade> --min <n>        # ou --taxa
```

Trois issues. Un arbre convient : l'exploiter, et le dire dans le cahier avec
son `tree_id`. Un arbre convient presque : juger si le recalcul se justifie (un
outgroup manquant, oui ; trois souches de plus, rarement). Rien ne convient :
calculer — c'est le cas légitime, et le `find` négatif est lui-même une
information à consigner.

**Après** un nouveau calcul :

```bash
python3 $F harvest
python3 $F annotate <tree_id> "la question à laquelle cet arbre répondait"
```

L'annotation est le seul geste manuel du dispositif, et il est court. C'est
aussi le seul qui porte ce qu'aucune machine ne peut récolter : pourquoi cet
arbre a été construit.

## Rapport aux autres skills

- `phylo-history` répond à « où cette souche a-t-elle été placée, à travers les
  arbres ? ». Il lit `investigate_phylo/history/strain_history.json`, qui ne
  couvre que 3 arbres : sur la forêt moissonnée, la même question se pose avec
  `find --taxa <SRA>` puis `support`, sur deux ordres de grandeur de plus.
- `raxml` et `iqtree-lsd2` CALCULENT un arbre. Ce skill se place avant (faut-il
  calculer ?) et après (verser à la forêt).
- `itol` rend une figure d'un arbre ; `phylo-forest` dit lequel.
- `marker-laminarity` teste la compatibilité de marqueurs avec UN arbre ; la
  forêt lui fournit les arbres témoins.

## Extensions non faites, et pourquoi

La fiche ne porte ni pays ni hôte des souches, alors que ce serait utile pour
retrouver « un arbre avec des souches du Sahel ». Ces métadonnées existent
(TBannotator, `sra-geolocate`) mais leur récolte suppose un accès réseau par
souche, là où tout le reste de l'index se calcule hors ligne en quelques
minutes. Les ajouter ferait dépendre le moissonnage d'un service, ce que
l'expérience du dépôt déconseille. La voie propre est un enrichissement séparé
et optionnel, sur les seuls arbres qu'on interroge — piste ouverte, pas dette.

## Comparer deux arbres : `scripts/compare_trees.py` (ajouté 2026-09-10)

Quand on veut savoir si deux reconstructions du MÊME jeu de taxons diffèrent *pour de vrai* (effet
d'un masque, d'un modèle, d'un outil), la distance de Robinson-Foulds seule induit en erreur : sur
un clade clonal récent la plupart des nœuds sont mal résolus, et un RF de 46 % peut ne recouvrir
aucun désaccord soutenu. Ce script ajoute la seule chose qui tranche, le SUPPORT BOOTSTRAP des
bipartitions en désaccord.

    python3 scripts/compare_trees.py A.raxml.support B.raxml.support \
        --nom-a FULL --nom-b MASKED --seuil 95

Rend : RF brute et normalisée, bipartitions propres à chaque arbre avec la distribution de leurs
supports, évolution du support sur les bipartitions communes, et un verdict qui distingue « des
nœuds sur lesquels on conclurait ont bougé » de « seul du bruit s'est déplacé ». Lire l'ASYMÉTRIE :
un arbre qui gagne des bipartitions à 95 % sans qu'aucune ne disparaisse en face n'a pas « changé »,
il a mieux résolu. Cas d'usage d'origine : `mtbc` P72.4, effet du masque PE/PPE (les deux arbres
partageaient 28 bipartitions à support médian 100 %, et toute l'information était dans les trois
que seul l'arbre masqué résolvait).
