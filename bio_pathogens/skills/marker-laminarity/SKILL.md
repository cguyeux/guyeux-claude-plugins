---
name: marker-laminarity
description: >-
  Teste si un jeu de marqueurs binaires (SPDI, RD, IS, spacers) est compatible
  avec un ARBRE, et si non, dit QUI casse QUOI. Borne combinatoire gratuite,
  matrice de relations a 5 codes, laminarisation gloutonne, arbre + Newick, et
  diagnostic de chaque croisement par fragilite avec les souches temoins.
  Codage 3-etats ON / OFF / UNKNOWN a partir de la couverture reelle des
  report.json, qui distingue enfin ABSENT de NON COUVERT.

  Utiliser quand : valider une charpente reconstruite (M. bovis, L6, L3),
  verifier que des marqueurs core-exclusifs extraits sont mutuellement
  compatibles, decider si un clade tient ou repose sur de l'homoplasie,
  diagnostiquer un arbre instable, ou avant de publier une taxonomie.

argument-hint: "--pool bdd/actuelle/L6 [--markers barcode_complete.tsv --prefix L6] [--gff3 ...]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# marker-laminarity : ce jeu de marqueurs tient-il dans un arbre ?

## La question

Un marqueur binaire coupe les souches en deux : celles qui le portent (le
*present-set*) et les autres. Un jeu de marqueurs admet une phylogenie parfaite
si et seulement si les present-sets forment une **famille laminaire** : deux
present-sets sont emboites ou disjoints, jamais croises. Un croisement est le
conflit des **quatre gametes**, et il signifie qu'au moins un des deux marqueurs
est homoplasique, mal appele, ou que le clade qu'il est cense definir n'existe
pas.

Aucun de nos outils ne posait cette question. `pectinated-subclade-mining`
extrait des marqueurs core-exclusifs mais ne verifie **jamais** qu'ils sont
mutuellement compatibles ; `lineage-subdivision` et `tsne-hdbscan` rendent des
clusters de souches sans leurs marqueurs ; `raxml` infere un arbre mais ne dit
pas quel marqueur le contredit.

## Le piege a connaitre avant tout : absent n'est pas non couvert

Nos `spdi.txt` ne listent que des **presences**. Un SPDI absent du fichier d'une
souche est soit vraiment absent, soit dans un trou de couverture. Ecraser les
deux en "absent" **fabrique des croisements** : il suffit qu'un marqueur de
lignee porte par 606 profils sur 618 manque chez une douzaine de souches mal
couvertes pour qu'il croise *tous* les marqueurs de sous-clade.

Mesure sur L6 (1 387 souches, 4 864 marqueurs de charpente du barcode) :

| lecture | croisements | dont fragiles (<= 2 souches) |
|---|---|---|
| binaire (absent = non liste) | 15 157 | 11 820 (78 %) |
| 3-etats (couverture reelle) | voir `--gff3` | |

L'information manquante est **deja sur disque** : chaque `report.json` porte
`genes[]` avec `percent_missing` et `mean_coverage` pour les 3 978 genes de
H37Rv. Passer `--gff3` active le mode 3-etats : un SPDI dans un gene non couvert
chez cette souche devient **UNKNOWN**, et un desaccord n'est compte que s'il est
**franc des deux cotes**.

Deux limites a enoncer plutot qu'a cacher : la resolution est le **gene**, pas la
base (un gene couvert avec un trou pile sur le SPDI reste lu comme franchement
absent) ; et un SPDI intergenique n'a pas de gene a interroger, il reste absent.

## Convention de coordonnees (verifiee, pas supposee)

Les positions SPDI sont **0-based**, le GFF3 est **1-based inclusif** : la
conversion ajoute 1. Verifie sur H37Rv plutot qu'admis : sur 200 SPDI tires au
hasard d'un `spdi.txt` reel, l'allele de reference correspond a la sequence
NC_000962.3 **200/200 en 0-based** et 44/200 en 1-based (ces 44 sont des
homopolymeres, ou le decalage est invisible). Se tromper ici decale chaque
marqueur d'une base et reassigne silencieusement ceux qui tombent sur une
frontiere de gene.

## Le diagnostic gratuit, avant tout calcul

Un arbre a `n` feuilles admet au plus `n - 1` clades non triviaux. Si les
marqueurs realisent plus de present-sets distincts que cela, l'exces est
**mathematiquement** force d'etre incompatible, quelle que soit la biologie.
Le script l'affiche en premier ; sur L6 : 651 present-sets pour au plus 617
clades, donc au moins 34 incompatibilites certaines avant d'avoir compare
la moindre paire.

## Usage

Charpente d'une lignee, contre le barcode de reference (mode binaire) :

    python3 scripts/check_laminarity.py --pool bdd/actuelle/L6 --pool bdd/actuelle/L6.1 --markers global_supplementary/barcoding_v2/barcode_complete.tsv --prefix L6 --out résultats/L6_laminarity

Une lignee vit dans des repertoires FRERES (`L6`, `L6.1`, `L6.2`...), pas
imbriques sous un seul : `--pool` est repetable, et le shell fait le reste
(`for d in bdd/actuelle/L6*; do printf -- "--pool %s " $d; done`).

Mode 3-etats, avec cache de couverture (les `report.json` font ~2 Mo piece, le
cache evite de les relire) :

    python3 scripts/check_laminarity.py --pool bdd/actuelle/L6 --markers ... --prefix L6 --gff3 investigate_phylo/resources/NC_000962.3.gff3 --coverage-cache data/L6_cov.npz --out résultats/L6_lam3

Tous les SPDI d'un pool, sans referentiel de marqueurs :

    python3 scripts/check_laminarity.py --pool bdd/actuelle/L3 --min-carriers 3 --out résultats/L3_laminarity

Depuis une matrice deja construite (`matrix.npz` + `strains.txt` + `markers.txt`) :

    python3 scripts/check_laminarity.py --matrix data/L3_mc3 --out résultats/L3_laminarity

**Depuis un fit de `binary-coclustering`, et c'est l'usage recommande apres un
co-clustering** :

    python3 scripts/check_laminarity.py --fit résultats/L6_g40_m80 --out résultats/L6_blocks_laminarity

Les taxons sont alors les BLOCS-SOUCHES et les colonnes les BLOCS-MARQUEURS, avec
les trois etats lus directement sur `alpha` (ON > `--on-thr`, defaut 0,9 ; OFF <
1 − seuil ; la bande entre les deux est UNKNOWN). C'est la bonne lecture d'un
co-clustering : **l'unite taxonomique est le present-set d'un bloc-marqueur sur les
blocs-souches, jamais un bloc-souche pris seul** (sur L6, 3 blocs sur 38 seulement
portent une synapomorphie exclusive, alors que les present-sets, eux, sont
laminaires). La sortie affiche la part d'UNKNOWN en premier, precisement pour qu'on
ne prenne pas une laminarite achetee par ignorance pour une preuve.

Resultat de bout en bout sur L6 (fit g=40) : 38 blocs-souches et 75 bloc-marqueurs
→ 24 profils distincts, 21 present-sets → **0 croisement, 0 marqueur retire,
19 clades**, UNKNOWN a 12,4 % seulement.

## Laminarisation a resolution SOUCHE (`--strain-level`)

La laminarisation par defaut (`laminar()`) resout un croisement en sacrifiant le
marqueur ENTIER le plus croisant. C'est mecaniquement conservateur quand la
fragilite est une poignee de taxons face a des present-sets de plusieurs dizaines
ou centaines : `--strain-level` resout d'abord les croisements de fragilite <=
`--strain-tolerance` en retirant CES taxons-la du present-set le plus petit des
deux (une exception par cellule, trace dans `strain_exceptions.tsv`), et ne laisse
la laminarisation classique traiter que ce qui reste.

    python3 scripts/check_laminarity.py --fit résultats/L2.2.1_g370_m480 --strain-level --strain-tolerance 2 --out résultats/L2.2.1_blocks_laminarity

`--strain-tolerance` : >= 1 est un compte absolu de taxons ; < 1 (defaut 0,05) est
une fraction de la taille du plus petit marqueur du croisement. **Avec `--fit`, les
taxons sont des BLOCS-SOUCHES, pas des souches reelles** : une exception y retire un
bloc entier, pas la poignee de souches reelles qui le composent ; pour un nettoyage a
la resolution de la souche reelle, construire une matrice souche-reelle x
marqueur-agrege (presence = porte au moins un SPDI brut membre du marqueur) et la
passer via `--matrix`.

Valide sur `coclustering_lineages` (P12.6.1.2, cahier 2026-08-12) contre les 3
croisements deja arbitres a la main par arbre ML independant (P12.6.1) : reconstruits
a resolution souche reelle, les 3 sont deja parfaitement emboites (0 croisement a
quatre gametes), confirmant independamment que le croisement de P12.3 etait un pur
artefact du decoupage en blocs. A resolution bloc (le grain de `--fit`), sur le
meme fit L2.2.1 (93 present-sets, 53 croisements), `--strain-tolerance 2` (le seuil
« fragilite <= 2 = accident » deja etabli par ce skill) recupere 7 marqueurs
supplementaires (11 -> 4 retires, 88,2 % -> 95,7 % de present-sets conserves).

## Lire la sortie

- **`combinatorial`** : le verdict gratuit ci-dessus. `PROVABLY INCOMPATIBLE`
  veut dire qu'aucun arbre ne peut porter ce jeu, point.
- **`relations`** : comptes par code (emboite / disjoint / egal / **croisement**).
- **`markers`** : chaque marqueur classe en `laminaire` (emboitements seuls, il
  structure l'arbre), `co-support` (meme present-set qu'un autre, redondant),
  `incoherent` (au moins un croisement, c'est lui que la laminarisation retire),
  `isole` (present-set prive).
- **`fragility`** : par croisement, `min(depassement)` = le nombre de souches
  dont le retrait tuerait le conflit. **C'est la lecture la plus utile.** Une
  fragilite de 1 ou 2 est un accident de sequencage ou une souche contaminee,
  pas un signal phylogenetique ; une fragilite a trois chiffres est un vrai
  desaccord topologique. Les **temoins** sont nommes, donc verifiables a la main.
- **`laminarisation`** : combien de marqueurs il a fallu sacrifier pour atteindre
  zero croisement. C'est la mesure d'incompatibilite du jeu.

Fichiers ecrits : `report.json`, `crossings.tsv` (tous les croisements tries par
fragilite, avec temoins), `laminar_tree.nwk` (arbre non enracine, longueurs de
branche = nombre de souches du profil), `removed_markers.txt`, et `browser.html`
(ci-dessous).

## Le navigateur local : un instrument de travail, pas une figure

`browser.html` s'ouvre en `file://`, donnees embarquees, aucune dependance et aucun
framework. Il lie **trois vues** :

1. l'arbre laminaire (clades indentes par profondeur, avec leur poids en souches et
   leur nombre de marqueurs support) ;
2. la heatmap profils x marqueurs en **3 etats** (ON / OFF / UNKNOWN) ;
3. la matrice de relations marqueur x marqueur (5 codes).

Cliquer un clade surligne SES marqueurs dans les deux matrices et liste les SPDI sur
lesquels il repose ; cliquer une colonne de la heatmap dit quel clade ce marqueur
definit, et selectionne ce clade. C'est le geste quotidien du travail taxonomique
manuel, « ce clade tient sur quoi ? ce marqueur definit quoi ? », que `itol` et
`sci-figure` ne permettent pas (figures statiques et unidirectionnelles).

**Contrainte d'echelle, a ne pas decouvrir trop tard.** La grille est peinte une fois
en `ImageData` a 1 px par cellule puis mise a l'echelle par le canvas, ce qui reste
fluide a plusieurs centaines de milliers de cellules. Sur L6 : 618 profils x 651
marqueurs = 402 k cellules, fichier de 1,2 Mo. Sur des souches **brutes** (35 401
lignes pour L2.2.1) l'image serait hors de portee. **On ne navigue jamais la matrice
brute, on navigue la matrice reduite** : la deduplication par profil est
exactement cette reduction.

## Tests

`python3 scripts/test_laminarity.py` : huit cas dont la reponse se derive a la main
(jeu laminaire qui doit rendre `((a,b),(c,d));`, conflit des 4 gametes, depassement
sur UNKNOWN, borne combinatoire, deduplication des deux axes, fragilite et temoins,
`--strain-level` qui repare sous le seuil de tolerance et qui s'abstient au-dessus).
A relancer apres toute modification du coeur.

## Ce que le skill ne fait pas

Il ne dit pas **quel** des deux marqueurs a tort : la laminarisation gloutonne
retire le plus croisant (ou le moins prioritaire si on passe `priority=`), ce qui
est un choix operationnel, pas une preuve. L'arbitre reste l'arbre ML
(`raxml`, `iqtree-lsd2`). Il ne remplace pas non plus une inference : il **teste**
un jeu de marqueurs, il n'en deduit pas une topologie fiable a lui seul.

Un bloc de co-clustering n'est pas davantage un clade : si l'entree vient de
`binary-coclustering`, la laminarite est le controle obligatoire, pas une
confirmation.

## Credit

L'algebre des relations (cinq codes, depassement franc en 3-etats, laminarisation
par couvre-sommet glouton, condensation des composantes fortement connexes en
arbre) est de **Clement Lecarpentier**, `github.com/cdarthos/bi-clustering`
(`phylo/relations.py`, `phylo/why.py`), volet code de sa these. Le present skill
en est une re-expression figee et autonome, pour des matrices souche x marqueur
brutes plutot que des blocs de LBM : pas de dependance a ce depot, pas d'`alpha`,
pas de coude. **Toute valorisation publiee de cette methode se regle avec lui
avant, pas apres.**

Voir aussi : `binary-coclustering` (structure de population par LBM, dont ce
skill est le controle aval), `pectinated-subclade-mining`, `lineage-subdivision`,
`strain-qc`.
