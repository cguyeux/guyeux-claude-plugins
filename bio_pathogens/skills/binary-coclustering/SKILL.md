---
name: binary-coclustering
description: >-
  Co-clustering binaire (Latent Block Model de Bernoulli) d'une matrice souche x
  marqueur : rend SIMULTANEMENT les blocs de souches et les blocs de marqueurs qui
  les definissent, la ou lineage-subdivision et tsne-hdbscan ne rendent que les
  premiers. Compresse par PROFIL au lieu de sous-echantillonner, donc tient sur les
  pools geants (L2.2.1, L3, L4.1). Placement de souches NOUVELLES a modele fige,
  avec mesure de confiance et detection du « ne rentre nulle part ».

  Utiliser quand : subdiviser une lignee trop grosse pour un arbre focalise,
  obtenir des synapomorphies candidates avec les clusters, classer des souches de
  a_ranger avec une probabilite a posteriori, ou detecter une sous-lignee non
  encore decrite.

argument-hint: "<pool bdd/actuelle> [-g blocs-souches] [-m blocs-marqueurs]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# binary-coclustering : les clusters ET les marqueurs qui les definissent

## Ce que ca apporte, et a quoi ca ne se substitue pas

Un LBM de Bernoulli ajuste `alpha[i, j]` = probabilite qu'un marqueur du bloc `j`
soit present chez une souche du bloc `i`. Les deux axes sont partitionnes en meme
temps, donc **chaque bloc de souches arrive avec les blocs de marqueurs qui le
caracterisent** : les synapomorphies candidates tombent avec les clusters, sans
passe de scoring separee.

C'est la difference de nature avec nos outils existants :

| | clusters de souches | marqueurs definissants | regime |
|---|---|---|---|
| `tsne-hdbscan` | oui | non | **densite** : noie un clade sur-echantillonne |
| `lineage-subdivision --explore` | oui | non | densite |
| `lineage-subdivision --optimize` | oui | contrainte imposee APRES coup | MDL |
| `pectinated-subclade-mining` | non (on les donne) | oui, un clade a la fois | per-pool |
| **`binary-coclustering`** | **oui** | **oui, conjointement** | **profil** |

Sur un pool geant, la difference n'est pas cosmetique. HDBSCAN est pilote par la
densite, donc par la MASSE : 35 401 Beijing modernes quasi identiques forment un
continuum sans frontieres et les petits groupes partent au bruit. Le co-clustering
ne jette personne, il **compresse par profil** : les memes 35 401 souches tombent
dans quelques centaines de blocs de profil distinct.

**Un bloc de souches n'est PAS un clade.** Le LBM est un melange sans contrainte de
monophylie : deux groupes non apparentes au profil voisin peuvent fusionner. Le
controle obligatoire est `marker-laminarity` sur les marqueurs definissants, et
l'arbitre final reste l'arbre ML.

## REGLE D'EMPLOI, mesuree sur L6 le 2026-08-10 (a lire avant d'interpreter un fit)

**Un bloc-souche n'est pas un clade, et ce n'est meme pas un candidat clade.** Mesure
sur L6 (1 364 souches, g=40) : seuls **3 blocs sur 38** portent au moins un SPDI
synapomorphique exclusif en lecture native du LBM (`alpha > 0,9` ici, `< 0,1` dans
tous les autres blocs) ; 35 n'en ont aucun. Ce n'est pas un defaut de la methode,
c'est que **l'exclusivite a UN bloc est le mauvais critere sur une structure
emboitee** : un marqueur qui definit L6.1 est present dans tous les blocs de L6.1,
donc exclusif a aucun.

**L'unite taxonomique est le PRESENT-SET d'un bloc-marqueur sur les blocs-souches**,
pas le bloc-souche. Lus ainsi, les 21 bloc-marqueurs informatifs du meme fit sont
**parfaitement laminaires : 0 croisement, 0 retire, 19 clades** et un Newick complet.
Et ce n'est pas obtenu par ignorance (le controle qu'impose la KB) : la bande UNKNOWN
ne couvre que **12,4 %** des cellules `alpha`, et meme en lecture binaire stricte
(seuil 0,5, zero UNKNOWN) il ne reste que **30 croisements et 4 retraits sur 35**.

A comparer aux **15 157 croisements et 34,7 % de marqueurs retires** sur les SPDI
BRUTS des memes souches : le co-clustering agit donc comme un **debruiteur**, en
absorbant dans les blocs le bruit d'appel qui fabriquait les faux croisements.

**Enchainement correct** : `binary-coclustering` (fit) puis `marker-laminarity` sur
les present-sets des bloc-marqueurs, et c'est CE resultat qui propose des clades.
Jamais « un bloc = une sous-lignee ».

### Face a `lineage-subdivision --explore` (densite), sur le meme pool L6

| | co-clustering (g=40) | densite (SVD-150 + HDBSCAN) |
|---|---|---|
| clusters rendus | 38 | 13 |
| souches non classees | 0 | **398 (29,2 %)** |
| marqueurs exclusifs a un seul cluster (mediane) | 0 | 135 |
| temps | 149 s | 55 s |
| ARI entre les deux partitions | 0,097 | |

Les deux ne mesurent pas la meme chose et **se completent** : la densite est deux
fois plus rapide et rend des groupes gros et bien separes, mais elle **jette 29 % des
souches au bruit** ; le co-clustering ne jette personne et descend plus fin, mais ses
blocs ne se lisent qu'a travers leurs present-sets. Regle : **densite pour explorer
(y a-t-il de la structure ?), co-clustering pour definir (sur quels marqueurs ?)**,
et `marker-laminarity` pour trancher dans les deux cas.

### Confirme ET NUANCE sur L3 (8 744 souches, 2026-08-11, projet coclustering_lineages, P12.2)

Meme protocole rejoue sur un pool 6x plus gros, cette fois contre une vraie verite
terrain (taxonomie d'avant l'aplatissement, 81 sous-lignees, 7 254 souches), pas
seulement les deux partitions l'une contre l'autre :

| | co-clustering (g=120, m=200) | densite (SVD-200 + HDBSCAN-10) |
|---|---|---|
| clusters proposes | 120 | 79 |
| souches non classees | 0 | 2 933 (33,5 %) |
| sans marqueur exclusif a 1 cluster | 41/120 | 6/79 |
| marqueurs medians / cluster | 15 | 72 |
| temps de calcul | 5 791 s (96 min) | 259 s (4,3 min) |
| ARI vs verite terrain (81 sous-lignees) | 0,252 | 0,682 (hors bruit) |

La lecture naive attendue etait « la densite echoue sur les pools geants, le
co-clustering reussit » : ce n'est PAS ce que montrent les chiffres. Sur les 66,5 % de
souches qu'elle ose classer, la densite est nettement PLUS fidele a la verite terrain
(0,682) que le co-clustering sur l'integralite du pool (0,252), et 22x plus rapide. Le
co-clustering ne l'emporte pas par precision ponctuelle ; il l'emporte parce qu'il ne
jette personne (0 souche non classee contre 33,5 % de bruit) et parce que ses fusions,
quand il y en a, sont individuellement defendables (97,22 % de part defendable mesuree
sur ce meme pool, cf. validation retrospective). La colonne « sans marqueur exclusif »
ne se lit pas comme un echec : c'est l'effet d'exclusivite deja caracterise sur L6
(une structure emboitee penalise mecaniquement la partition la plus fine sur ce
critere), a lire via `marker-laminarity` sur les present-sets, pas via ce compte.

**REGLE D'EMPLOI CONSOLIDEE (L6 + L3), complementarite et non substitution : la
densite pour un premier passage rapide et des appels haute confiance, quand jeter un
tiers du pool est acceptable ; le co-clustering pour une classification exhaustive
avec marqueurs definissants et zero souche perdue, au prix d'environ 22x le temps de
calcul.** Le co-clustering est plus COMPLET, pas plus PRECIS ; ne jamais presenter l'un
comme remplaçant l'autre dans un manuscrit ou un choix de pipeline.

## Les trois reserves, a porter dans tout usage

**(a) Le plancher de porteurs est le plafond de finesse, et il y en a DEUX.** Le
premier est explicite (le filtre a la construction de la matrice). Le second est
cache dans `StaircaseLBM.fit`, qui re-filtre les colonnes a une MAF dans
[0,02 ; 0,98] : sur 8 744 souches cela ecarte silencieusement tout marqueur porte
par moins de 175 d'entre elles, et un seuil plus bas en aval n'y change alors
**rien**. Un sous-clade de 30 souches est structurellement invisible a un tel run.
`fit_coclustering.py` contourne l'escalier et appelle le moteur directement, pour
que le seul plancher soit celui qu'on a choisi (defaut : 3 porteurs).

**(b) Un fit non converge fabrique de fausses sous-lignees.** Sur `chain10k` en
amont, clusters 767 -> 1 243 et incoherences 529 -> 1 956 **encore en hausse** a
l'iteration 119. Le nombre d'incoherences (via `marker-laminarity`) est le moniteur
a surveiller avant toute lecture, pas la log-vraisemblance seule.

**(c) Initialisation supervisee : legitime chez nous, mais elle coute la
validation.** Clement Lecarpentier s'interdit toute init supervisee parce que sa
these DEMONTRE qu'une structure non supervisee retrouve Napier. Nous ne demontrons
pas, nous raffinons : amorcer le fit par la subdivision existante est defendable.
Mais alors la concordance avec notre taxonomie **cesse d'etre une validation**.
Choisir, et le dire dans le manuscrit.

## Usage

Construire la matrice depuis un pool, puis ajuster :

    python3 scripts/build_matrix.py bdd/actuelle/L3 --out data/L3_mc3 --min-carriers 3
    python3 scripts/fit_coclustering.py data/L3_mc3 --out résultats/L3_fit -g 120 -m 200 --n-init 3

Ordre de grandeur mesure (L3, 8 744 souches x 72 100 marqueurs, nnz 12,3 M, CPU) :
le cout croit avec `(g + m)`, comptez ~2 min a `g=20, m=40` et de l'ordre de
l'heure a `g=120, m=200` avec 3 redemarrages. Lancer en tache de fond.

Placer des souches nouvelles sur un modele deja ajuste (P11.5) :

    python3 scripts/build_matrix.py bdd/actuelle/a_ranger --vocabulary data/L3_mc3/markers.txt --out data/a_ranger_L3
    python3 scripts/place_strains.py résultats/L3_fit data/a_ranger_L3 --reference data/L3_mc3 --out résultats/L3_placement

La matrice des nouvelles souches doit utiliser **le meme vocabulaire de marqueurs**
que celle du fit : d'ou `--vocabulary`, qui reprend le `markers.txt` verbatim (le
script de placement refuse sinon).

## Lire un placement, et pourquoi la confiance vaut plus que l'argmax

`barcoding_v2` applique une regle deterministe : elle repond toujours, et sans
mesure. Le placement a modele fige rend une **probabilite a posteriori**, donc
(a) un classement gradue et (b) surtout la detection du « ne rentre nulle part »
(responsabilite diffuse), qui est le signal d'une sous-lignee non decrite **ou**
d'un probleme de QC (melange, contamination, couverture partielle). Les souches
signalees `diffuse` sont a passer a `strain-qc` avant d'etre lues comme une
decouverte.

**Le posterior seul ne detecte PAS le « n'appartient a rien », et c'est structurel :
une responsabilite est RELATIVE, elle ne fait que classer les blocs entre eux.** Une
souche d'une autre lignee est donc quand meme affectee quelque part, souvent avec
assurance. Mesure sur L6 (modele) contre 26 souches L5 (qui n'ont leur place nulle
part dedans) : le seuil d'entropie a 0,3 n'en signale que **5 sur 26**, et 21 sont
placees avec confiance.

Ce qui marche est la **vraisemblance ABSOLUE** du meilleur bloc, calibree sur les
souches d'entrainement (`--reference`, seuil au 1er centile) : **26/26 souches L5
detectees pour 1,0 % de faux positifs**. Toujours passer `--reference` ; sans lui, la
colonne `belongs_nowhere` reste vide et il ne reste que l'entropie, insuffisante.

Deux pieges rendent le chiffre de confiance faux si on ne les traite pas, et le
script les traite par defaut :

- **Pseudo-replication clonale.** Chez une clonale, les marqueurs d'un meme bloc
  sont le MEME evenement evolutif compte `m_j` fois. La vraisemblance devient
  massivement sur-confiante et toutes les probabilites saturent a 0 ou 1.
  L'argmax survit, la confiance non. Defaut `--weight block` : un bloc-marqueur
  compte pour **une** observation (la fraction de presence porte l'information).
  `--weight marker` reproduit la formule naive, gardee pour comparaison — si les
  posterieurs saturent avec elle et pas avec `block`, c'est la demonstration du
  piege sur vos donnees.
- **Absence contre non-couverture.** Un marqueur non appele n'est pas une absence.
  Ne sommer que sur les marqueurs reellement interrogeables (meme probleme
  3-etats que `marker-laminarity`, qui sait construire ce masque depuis les
  `report.json`).

## Tests

`python3 scripts/test_place_strains.py` — quatre cas sur donnees synthetiques
generees DEPUIS un `alpha` connu, donc a reponse verifiable. Ils exhibent les deux
pieges au lieu de les affirmer : sous `--weight marker` les trois posterieurs
saturent a **1,000**, sous `--weight block` ils valent 0,990 a 0,993 ; et l'argmax
est identique dans les deux cas, ce qui montre que **seule la confiance est
fausse**, pas l'affectation. Une souche au profil aleatoire ressort a une entropie
normalisee de **0,98** (« ne rentre nulle part »), contre ~0 pour les souches bien
placees : c'est le signal recherche.

## Moteur : pilote, pas reimplemente

Le moteur EM est celui de C. Lecarpentier (`tblearn_biclustering.core`), utilise
tel quel : `_fit_lbm` pour les redemarrages aleatoires, `_em_cpu` pour l'EM
variationnel chunke. Nous n'entretenons pas un second moteur. Seule la plomberie
de donnees est a nous, parce que le chargeur amont passe par leur MCP TBLearn
alors que nos matrices viennent de `bdd/actuelle`.

Verifie : le paquet s'importe et tourne avec le Python systeme (numpy 2.5,
scipy 1.18, Python 3.14), et `StaircaseLBM.fit` accepte une matrice creuse locale
sans aucune dependance a leur serveur. Renseigner le chemin du depot en tete de
`fit_coclustering.py`.

## Credit

Methode et implementation : **Clement Lecarpentier**,
`github.com/cdarthos/bi-clustering`, volet code de sa these (TB-Annotator,
Paris-Saclay). La paternite du LBM binaire applique au MTBC lui revient, et toute
valorisation publiee se regle **avec lui avant, pas apres**.

Voir aussi : `marker-laminarity` (controle obligatoire en aval),
`lineage-subdivision`, `tsne-hdbscan`, `pectinated-subclade-mining`, `strain-qc`.
