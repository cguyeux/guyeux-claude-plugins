---

name: lineage-subdivision
description: >-
  Subdiviser une lignée MTBC (bactérie clonale) en sous-lignées : mode explore =
  structure de population (SPDI + IS6110 + RD, t-SNE, HDBSCAN, dendrogramme, PNG
  et HTML interactif) ; mode optimize = optimisation MDL sous contraintes
  synapomorphiques, balayage lambda, Pareto, matérialisation réversible.
  Use when: chercher des clusters, décider s'il faut scinder une lignée, produire
  une taxonomie reproductible sur un clade dense ou sur-séquencé.
  Portée : développé sur le MTBC, applicable à toute bactérie clonale (Yersinia,
  Leptospira...) — structure de population et optimisation MDL sont génériques. Hors MTBC :
  fournir le chemin de la base de souches et les marqueurs du genre (IS6110 et RD sont des
  canaux d'entrée propres au MTBC, les SPDI sont le canal générique).
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# /lineage-subdivision : découper une lignée en sous-lignées

Deux modes pour un seul geste, dans cet ordre :

| Mode | Question | Sortie | Statut de la sortie |
|------|----------|--------|---------------------|
| `explore` | Y a-t-il de la structure dans cette lignée ? | t-SNE, HDBSCAN, dendrogramme UPGMA, PNG, HTML interactif | **Hypothèse**, jamais une taxonomie |
| `optimize` | Où placer les bornes, et combien de sous-lignées nommer ? | partition MDL, marqueurs, `materialize` dans `bdd/actuelle/` | Taxonomie candidate, à valider par l'utilisateur |

La formulation ne suppose rien de propre au MTBC : elle vaut pour toute **bactérie
clonale** (faible recombinaison, synapomorphies stables). Seuls les miners de marqueurs
sont genre-spécifiques (cf. `mine_bovis_markers.py`, à adapter pour un autre genre).

## Cadrage : un cluster n'est pas un clade (à lire AVANT d'agir)

C'est la règle qui gouverne les deux modes, et la raison pour laquelle ils vivent dans
le même skill. Le mode `explore` produit des **clusters phénétiques** ; une sous-lignée
est un **clade synapomorphique**. Les deux objets ne coïncident pas, et confondre le
premier pour le second est l'erreur classique de la subdivision.

1. **Arbre ≠ clusters.** Le t-SNE, HDBSCAN et le dendrogramme average-linkage sont des
   proxys de **distance globale**. Ils servent à voir l'emboîtement, à dédupliquer, à
   échafauder. Ils ne posent **JAMAIS** les bornes d'une sous-lignée. Les bornes = une
   synapomorphie propre + la monophylie, rien d'autre. Un cluster t-SNE bien séparé peut
   n'être qu'un artefact d'échantillonnage (un BioProject sur-représenté, une
   couverture inégale, un paquet de transmission) ; à l'inverse deux vraies sous-lignées
   sœurs peuvent se superposer dans l'embedding.
2. **La longueur de branche n'est PAS le critère.** Chez un clonal, une COURTE branche
   (même 1 SNP) peut définir une vraie lignée. Ce qui définit un clade est la
   **synapomorphie propre** (état dérivé partagé, fixé, exclusif, hors homoplasie), pas
   la magnitude. C'est une contrainte de faisabilité (C1), pas un objectif à maximiser.
3. **Ne pas forcer des bifurcations.** Il y a de vraies POLYTOMIES (radiations clonales).
   Elles émergent en n'autorisant des coupes qu'aux nœuds synapo-soutenus, pas en
   coupant un dendrogramme à une hauteur donnée.

Corollaire pratique : ne jamais passer directement d'un cluster HDBSCAN à un répertoire
de `bdd/actuelle/`. Le chemin légitime est `explore` (il y a de la structure) puis
`optimize` (voici où sont les bornes, et elles sont synapo-soutenues). Un cluster non
confirmé par `optimize` reste une observation, pas une lignée.

Et le BRUIT se traite EN AMONT, sinon on optimise sur du bruit (séquençage vers faux SNP
vers fausses synapomorphies ; chimères ; mauvaise couverture ; paquets de transmission à
2-3 SNP qui sur-pondèrent les zones denses). Le contrôle de GC par MAD sur le lot
(cf. `strain-qc`, critère 2) fait partie de cet amont : une souche contaminée forme un
bloc d'artefact qui croise tout le monde et déguise un problème de qualité en problème
de topologie.

### Face au co-clustering : règle d'emploi mesurée (L6, 2026-08-10)

Le recouvrement avec `binary-coclustering` est réel et a été tranché par la mesure sur le
même pool (L6, 1 364 souches), pas par argument :

| | densité (SVD-150 + HDBSCAN) | co-clustering (g=40) |
|---|---|---|
| clusters rendus | 13 | 38 |
| souches non classées | **398 (29,2 %)** | 0 |
| marqueurs exclusifs à un seul cluster (médiane) | 135 | 0 |
| temps | 55 s | 149 s |
| ARI entre les deux partitions | 0,097 | |

Lecture : les deux ne mesurent pas la même chose. La densité est deux fois plus rapide et
rend des groupes gros et nettement séparés, chacun avec ses marqueurs exclusifs, mais elle
**renvoie 29 % des souches au bruit**, ce qui est exactement le régime redouté sur un clade
sur-échantillonné. Le co-clustering ne jette personne et descend plus fin, mais ses blocs
**ne sont pas des candidats clades** (3 sur 38 seulement portent une synapomorphie
exclusive) : ils ne se lisent qu'à travers les present-sets de leurs blocs-marqueurs, qui
eux sont laminaires (0 croisement sur ce fit).

**Règle : densité pour EXPLORER (y a-t-il de la structure ?), co-clustering pour DÉFINIR
(sur quels marqueurs ?), `marker-laminarity` pour trancher dans les deux cas.** L'ARI de
0,097 entre les deux partitions n'est pas un désaccord à arbitrer, c'est la conséquence de
granularités et de régimes différents.

### Confirmé ET nuancé sur L3 (8 744 souches, 2026-08-11, projet `coclustering_lineages`, P12.2)

Même protocole rejoué sur un pool 6× plus gros, cette fois contre une vraie vérité terrain
(taxonomie d'avant l'aplatissement, 81 sous-lignées, 7 254 souches), pas seulement les deux
partitions l'une contre l'autre :

| | co-clustering (g=120, m=200) | densité (SVD-200 + HDBSCAN-10) |
|---|---|---|
| clusters proposés | 120 | 79 |
| souches non classées | 0 | 2 933 (33,5 %) |
| sans marqueur exclusif à 1 cluster | 41/120 | 6/79 |
| marqueurs médians / cluster | 15 | 72 |
| temps de calcul | 5 791 s (96 min) | 259 s (4,3 min) |
| ARI vs vérité terrain (81 sous-lignées) | 0,252 | 0,682 (hors bruit) |

La lecture naïve attendue était « la densité échoue sur les pools géants, le co-clustering
réussit » : ce n'est PAS ce que montrent les chiffres. Sur les 66,5 % de souches qu'elle ose
classer, la densité est nettement PLUS fidèle à la vérité terrain (0,682) que le
co-clustering sur l'intégralité du pool (0,252), et 22× plus rapide. Le co-clustering ne
l'emporte pas par précision ponctuelle ; il l'emporte parce qu'il ne jette personne (0
souche non classée contre 33,5 % de bruit) et parce que ses fusions, quand il y en a, sont
individuellement défendables (97,22 % de part défendable mesurée sur ce même pool). La
colonne « sans marqueur exclusif » ne se lit pas comme un échec du co-clustering : c'est
l'effet d'exclusivité déjà caractérisé sur L6 (une structure emboîtée pénalise
mécaniquement la partition la plus fine sur ce critère), à lire via `marker-laminarity` sur
les present-sets, pas via ce compte.

**RÈGLE D'EMPLOI CONSOLIDÉE (L6 + L3), complémentarité et non substitution : la densité pour
un premier passage rapide et des appels haute confiance, quand jeter un tiers du pool est
acceptable ; le co-clustering pour une classification exhaustive avec marqueurs définissants
et zéro souche perdue, au prix d'environ 22× le temps de calcul.** Le co-clustering est plus
COMPLET, pas plus PRÉCIS ; ne jamais présenter l'un comme remplaçant l'autre dans un
manuscrit ou un choix de pipeline.

### Contrôle de sortie : la subdivision proposée tient-elle dans un arbre ?

Une fois `optimize` passé, la partition retenue s'accompagne de ses marqueurs
définissants. Chacun a été validé contre son pool, aucun ne l'a été **contre les
autres**. Le test qui manque est celui de la compatibilité mutuelle : les
present-sets des marqueurs définissants forment-ils une famille laminaire (emboîtés
ou disjoints), ou se croisent-ils ?

    python3 <skills>/marker-laminarity/scripts/check_laminarity.py --pool bdd/actuelle/<L> --markers <registre de marqueurs> --gff3 investigate_phylo/resources/NC_000962.3.gff3 --out résultats/<L>_laminarity

Un croisement de forte fragilité (des dizaines ou des centaines de souches de part et
d'autre) dit qu'au moins une des deux bornes proposées n'existe pas comme clade. C'est
exactement le contrôle que « un cluster n'est pas un clade » appelle, mais rendu
mesurable : au lieu de rappeler la règle, on la teste.

À l'inverse, la fragilité 1-2 domine dès qu'on lit nos `spdi.txt` en binaire (78 % des
croisements sur L6) : passer `--gff3` pour le mode 3-états, sinon le contrôle rend un
verdict d'incompatibilité qui ne mesure que des trous de couverture.

## Skills liés

- `pectinated-subclade-mining` : **complémentaire**, extraction manuelle d'UN sous-clade
  (filtre PER-POOL strict de synapomorphismes SPDI) après inspection visuelle d'un arbre.
  Ici on OPTIMISE au contraire la partition entière d'une lignée.
- `mtbc-lineages` : registre canonique des lignées et barcodes, une fois la subdivision
  matérialisée. Il **prime** sur ce skill pour les définitions déjà publiées.
- `tbmonitor-papers` : à interroger AVANT de proposer une nouvelle sous-lignée
  (réplication n'est pas découverte, cf. la fin du mode `explore`).

---

# Mode `explore` : structure de population

```
/lineage-subdivision explore /path/to/bdd/actuelle/L4.9/
/lineage-subdivision explore /path/to/bdd/actuelle/L4.9/ --min-cluster-size 10
/lineage-subdivision explore /path/to/bdd/actuelle/L4.9/ --no-is --no-rd
```

```bash
S=scripts/clade_finder.py
python3 "$S" /path/to/bdd/actuelle/L4.9/ [options]
# ou, depuis un plugin : "scripts/clade_finder.py"
```

Dépendances : `numpy`, `scipy`, `scikit-learn`, `hdbscan`, `matplotlib`.

## Phase 0 : scan du répertoire

1. Lister les sous-répertoires SRA du répertoire de lignée.
2. Pour chaque SRA, lire `SRA/<REF>/report.json` (source préférée) ou, à défaut,
   `SRA/<REF>/spdi.txt` (fallback ; `--ref`, défaut `NC_000962.3`).
3. Un SRA sans aucun SPDI lisible est **ignoré silencieusement** (y compris s'il a un
   `report.json` illisible ou vide). Le script **s'arrête** en dessous de 5 SRAs
   exploitables.
4. Afficher :

```
Clade-finder : L4.9
SRAs trouvés   : 820
  avec report.json : 780
  avec spdi.txt seul : 35
  sans données (ignorés) : 5
```

## Phase 1 : extraction des features

Trois sous-vecteurs binaires, concaténés en une matrice `n_SRA × (n_spdi + n_is + n_rd)`.

**Pan-SPDI (présence/absence)** : source `report.json → d['snp'][i]['spdi']`, ou fallback
`spdi.txt`. Union de tous les SPDIs = pan-SPDI. Filtrage par fréquence : un SPDI est
retenu si son effectif est compris entre `max(2, n × min_freq)` et `n × max_freq`
(défauts 2 % et 98 %), ce qui écarte les singletons et les quasi-fixés non informatifs.

**Positions IS (présence/absence)** : source `report.json → d['insertion_sequences']`.
Chaque IS devient un identifiant `nom_position` (ex. `IS6110_701383`), pan-IS = union de
ces paires. `--no-is` retire cette source.

**RD (présence/absence)** : source `report.json → d['large_rd'] + d['missing_rd']`. Un RD
de `large_rd` est présent si son `percent_missing < 50 %` ; un RD listé dans `missing_rd`
est absent. Les RD dynamiques `CUS_GS_*` sont **exclus** (spécifiques à chaque souche,
ils ne détectent que des délétions individuelles). Un RD non renseigné pour une souche
est compté présent. `--no-rd` retire cette source.

## Phase 2 : t-SNE puis HDBSCAN

Attention à la métrique, elle change entre les deux étapes :

- **t-SNE** : matrice de distances **Jaccard** précalculée (adaptée au binaire),
  `n_components=2`, `init="random"`, 1000 itérations, `random_state=42`
  (reproductible). Perplexité auto = `min(50, max(5, (n-1)/3))`, ou `--perplexity`.
- **HDBSCAN** : tourne sur l'**embedding 2D**, donc en métrique **euclidienne**, pas
  Jaccard. `min_cluster_size` auto = `max(3, n//15)`, borné ensuite dans `[2, n//3]`, ou
  `--min-cluster-size`. Les points non assignés portent le label `-1` (bruit).
- **Silhouette** : calculée sur l'embedding, bruit exclu, seulement s'il y a au moins
  2 clusters (sinon `-1.0`).

Conséquence à garder en tête pour l'interprétation : la silhouette qualifie la séparation
**dans le plan t-SNE**, pas dans l'espace des caractères. Elle mesure la netteté d'une
projection, pas le support d'un clade.

## Phase 3 : dendrogramme UPGMA

En plus du t-SNE, un **dendrogramme UPGMA (average linkage) sur les distances Jaccard**
de la même matrice binaire :

- un dendrogramme **par SRA** (toutes les souches en feuilles), branches et étiquettes
  colorées par le cluster HDBSCAN d'appartenance ;
- quand il y a **≥ 2 clusters**, un second dendrogramme **par cluster**, calculé sur les
  **centroïdes** Jaccard : il résume les relations entre clusters.

Ce dendrogramme est phénétique. Voir le cadrage : il ne pose pas de bornes.

## Phase 4 : PNG

Un PNG (défaut 300 DPI, `--dpi` ; largeur 24 pouces à 3 panneaux, 20 à 2 ; hauteur
adaptative `max(10, n_SRA × 0.12)`), enregistré dans `<lineage_dir>/clade_finder.png`
ou `--output` :

- **panneau gauche** : t-SNE coloré par cluster HDBSCAN, bruit en gris, légende donnant
  la taille de chaque cluster ;
- **panneau central** : dendrogramme UPGMA par SRA, orientation droite, branches et
  labels colorés par cluster, taille de police adaptée à l'effectif ;
- **panneau droit** (seulement si ≥ 2 clusters) : « Relations entre clusters », le
  dendrogramme des centroïdes ;
- titre : nom de la lignée, n SRAs, n clusters, silhouette, et composition des features.

## Phase 5 : page HTML interactive

Le script écrit AUSSI une page HTML autonome à côté du PNG (même chemin, extension
`.html` ; ex. `<lineage_dir>/clade_finder.html`). C'est la sortie la plus utile pour
juger un cluster, et la plus facile à oublier. Elle contient un **dendrogramme D3.js
interactif lié à un scatter t-SNE** :

- clic sur un nœud pour déplier ou replier ; boutons `+ Tout`, `- Tout`, `+ 1 niv`,
  `- 1 niv`, et `Undo` / `Redo` / `Reset` ; l'arbre s'ouvre à la profondeur 2 ;
- chaque nœud affiche `n SRAs | core: X | excl: Y`, où **core** = nombre de SPDIs
  présents chez TOUS les descendants du nœud, et **excl** = nombre de SPDIs core ABSENTS
  de tous les non-descendants. `excl` est donc un compte de **synapomorphies candidates**
  (SPDI seulement, les colonnes IS et RD n'entrent pas dans ce calcul) : c'est la lecture
  utile pour juger si un cluster mérite le statut de sous-lignée ;
- exclusion d'un SRA à la volée (le `x` rouge sur une feuille, étiquette barrée) : les
  compteurs core/excl sont **recalculés en direct**, ce qui permet de tester si une
  souche aberrante ou mal séquencée porte à elle seule la structure observée ; le
  compteur `actifs/total` du titre suit ;
- survol et clic croisés avec le panneau t-SNE (mise en évidence de la souche),
  info-bulle par point.

**La page charge D3 v7 depuis `https://d3js.org` : elle a besoin d'un accès réseau à
l'ouverture.** Sans réseau, la page s'affiche vide et seul le PNG reste lisible.

Le compte `excl` de cette page est le pont vers le mode `optimize` : c'est une
synapomorphie *candidate*, mesurée dans le seul contexte de la lignée chargée et sur un
regroupement phénétique. `optimize` la re-teste per-pool, avec seuils et masques.

## Phase 6 : rapport JSON sur stdout

```json
{
  "lineage": "L4.9",
  "n_samples": 815,
  "features": {"spdi": 4521, "is": 87, "rd": 42, "total": 4650},
  "tsne": {"perplexity": 30.0},
  "hdbscan": {
    "min_cluster_size": 54,
    "n_clusters": 5,
    "noise_count": 23,
    "noise_ratio": 0.028,
    "silhouette_score": 0.67,
    "cluster_sizes": {"0": 312, "1": 198, "2": 145, "3": 98, "4": 39}
  },
  "output_png": "/path/to/L4.9/clade_finder.png",
  "output_html": "/path/to/L4.9/clade_finder.html"
}
```

Grille d'interprétation :

- **silhouette > 0.5** et clusters bien séparés : sous-lignées probables, passer à
  `optimize` ;
- **silhouette 0.25 à 0.5** : structure faible, à confirmer ; lire les compteurs `excl`
  de la page HTML avant toute conclusion ;
- **silhouette < 0.25**, ou un seul cluster : lignée homogène, pas de découpe.

Dans tous les cas la silhouette **autorise** ou **décourage** un passage à `optimize` :
elle ne valide aucune borne.

## Options du script `clade_finder.py`

| Option | Défaut | Description |
|--------|--------|-------------|
| `--min-cluster-size N` | auto | Taille minimale d'un cluster HDBSCAN |
| `--perplexity N` | auto | Perplexité t-SNE |
| `--dpi N` | 300 | Résolution du PNG |
| `--no-spdi` | off | Exclure les SPDIs des features |
| `--no-is` | off | Exclure les IS des features |
| `--no-rd` | off | Exclure les RD des features |
| `--output PATH` | `<dir>/clade_finder.png` | Chemin du PNG (le HTML prend la même racine) |
| `--ref REF` | `NC_000962.3` | ID de la référence génome |
| `--min-freq F` | 0.02 | Fréquence min d'un SPDI pour être retenu |
| `--max-freq F` | 0.98 | Fréquence max d'un SPDI pour être retenu |

## Après la découverte d'un cluster

1. **Vérifier la littérature AVANT de proposer une nouvelle sous-lignée.** Interroger
   `tbmonitor-papers` (~190 000 papiers PubMed TB pré-indexés, SQL sub-seconde) pour
   savoir si le cluster a déjà été décrit. Réplication n'est pas découverte.
2. **Un seul sous-clade à extraire, arbre déjà construit** : passer à
   `pectinated-subclade-mining` (filtre PER-POOL strict de synapomorphismes SPDI).
3. **La partition entière d'une lignée** : mode `optimize` ci-dessous.

---

# Mode `optimize` : définition par optimisation MDL sous contraintes

Définit les sous-lignées d'une lignée `ROOT` (un répertoire de `bdd/actuelle/`, ex.
`Bovis.2.2.2.2.2.1`, `L4.11`, `Orygis_La3`) comme la solution d'un problème
d'optimisation, pas d'un seuil. Le script unique `scripts/lineage_mdl.py` enchaîne les
étapes ; chaque étape écrit dans `<projet>/résultats/lineage_mdl/<ROOT>/`.

Cas d'usage visé : obtenir une taxonomie de sous-lignées **reproductible et défendable**
pour des études évolutives (**phylogéographie**, **datation**), en particulier sur un
clade **dense, clonal et sur-séquencé** où un seuil constant sur-résout les zones
sur-échantillonnées et sous-résout les autres.

La granularité est ainsi **pilotée par la biologie** plutôt que par un seuil, sous
garantie de support synapomorphique (contrainte C1). Précision d'implémentation :
l'objectif MDL porte sur la cohérence **géographique** (`H(pays|lignée)`) ; l'**hôte** est
affiché en annotation (colonne `pays / hôte` des sorties `deepen`) mais n'entre PAS dans
l'objectif optimisé.

## Architecture (et les deux seuls boutons)

```
(A) DEBRUITER  : masque homoplasie+resistance (traces_mask) ; QC compte SPDI (med±5MAD)
                 + RD4 (bovis_rd4_qc) ; chimeres (>=2 synapo exclusives de 2 macro-branches) ;
                 DEReplication a RAYON ~2 SNP (PAS exact : un paquet de transmission >=5 a
                 2 SNP deviendrait une fausse lignee).
(B) CONTRAINTES (faisabilite d'un clade) : C1 DEFINISSABILITE = >=MINSYN marqueurs MULTI-SIGNAL
                 (SNP union RD union IS6110) qui SEPARENT le noeud DANS SON CONTEXTE (per-pool :
                 in>=t_in~0.9 dans le noeud, complement<=t_out~0.02 dans le reste de la lignee ;
                 positions masquees). PAS d'exclusivite globale all-MTBC requise (on definit dans
                 le contexte de la lignee : intersection/union de SNP, SNP du pere + le sien,
                 conjonction avec un IS...). L'exclusivite globale (clade_spdi_count/rd_cc/is_cc
                 <=KGLOB) est un garde-fou OPTIONNEL (KGLOB=0 = off par defaut). C2 >=5 souches ;
                 C3 monophylie. -> espace reduit, polytomies natives.
(C) OBJECTIF MDL : LL = sum_pays k*log(k/n) = -n*H(pays|lignee) (<=0, 0=pur), -lambda/lignee
                 (single-BioProject *1.5). DP bottom-up best(v)=max(terminal, subdiviser
                 avec REPLI GLOUTON des enfants geo-redondants dans le grade). Balayer
                 lambda -> Pareto resolution<->parcimonie -> COUDE.
```

Boutons : **MINSYN** (combien de marqueurs per-pool suffisent à DÉFINIR ; 1 = définissable
par un seul marqueur per-pool-exclusif de type SNP/RD/IS, le père donnant le contexte ;
2-3 = plus robuste) et **lambda** (parcimonie). Tout le reste est fixe ou principiel.

**Interpréter lambda.** lambda = le PRIX, en nats d'information géographique, que doit
payer chaque lignée nommée : le DP ne nomme une coupe que si elle réduit l'incertitude
`H(pays|lignée)` de PLUS de lambda nats (environ lambda/0.69 bits). Petit lambda (2 à 8)
donne beaucoup de lignées fines ; grand lambda (45 à 90) donne peu de lignées larges. Le
bon point est le COUDE de la courbe lambda vers #lignées vers cohérence (au-delà, la
cohérence ne baisse presque plus mais le #lignées s'effondre). NE PAS choisir lambda dans
l'abstrait : lancer `optimize` avec un balayage fin et RÉGULIER (ex. 2,4,6,8,10,14,18,24,
32,45,65,90), lire la table, et choisir par le NOMBRE de lignées et la cohérence voulus.
La granularité est continue (objectif MDL + repli glouton) ; tout entier intermédiaire de
lambda donne un résultat sensible.

## Flux de travail

```bash
P=~/docs/codes/mtbc/<projet>            # ex. Bovis_full ; sorties dans $P/résultats/lineage_mdl/<ROOT>/
PY=/home/christophe/venvs/ars311/bin/python
S=scripts/lineage_mdl.py

$PY $S denoise   <ROOT>                 # chiffre le bruit (masque/QC/derep/chimeres) ; rien d'autre requis
$PY $S rdis      <ROOT>                 # per-souche RD/IS depuis report.json (hors CUS_GS) -> rdis.pkl
$PY $S tree      <ROOT> [radius=2]      # dendrogramme DEBRUITE (masque + derep) -> dendro.pkl
# optimize : ORDRE = <ROOT> <lambdas,csv> <MINSYN> <T_IN> <T_OUT> <KGLOB> (lambdas AVANT les params !)
$PY $S optimize  <ROOT> 2,4,6,8,10,14,18,24,32,45,65,90 2 0.9 0.02 0   # Pareto lambda -> choisir le coude
# inspect/materialize : ORDRE = <ROOT> <LAM> <MINSYN> <T_IN> <T_OUT> <KGLOB> (LAM en premier)
$PY $S inspect   <ROOT> 8 2 0.9 0.02 0                   # partition + flagging -> inspect_lam8.tsv
# (sur go utilisateur seulement, modifie bdd/) :
$PY $S materialize <ROOT> 8 2 0.9 0.02 0 apply           # cree dirs + markers, log reversible
```

`RDIS=0` en variable d'environnement désactive le multi-signal (comparer SNP seul). Le
multi-signal ne CHANGE la partition que sur les lignées CLONALES pauvres en SNP
(BCG-like) ; sur une lignée SNP-saturée il corrobore sans rien sauver (vérifié sur A/Eu1).

## Lecture du résultat et ré-investigation relâchée

`inspect` annote chaque lignée : n, synapo, #BioProject, **#pays, étendue temporelle
(span), divergence IS interne**, pays dominant, fenêtre. Il **FLAGue** (colonne flag ou
symbole) les terminaux à `n_pays>=4` OU `span>=30 ans` OU `IS_div>=3` : ce sont des
sous-lignées à forte étendue spatio-temporelle ou divergence IS, donc **sous-résolues**,
candidates à une **ré-investigation sous contraintes RELÂCHÉES** via le mode `deepen` :

```bash
$PY $S deepen <ROOT> 24            # cible le PLUS GROS terminal flagge a lambda=24
DEEPEN_IDX=1 $PY $S deepen <ROOT> 24   # cible le 2e plus gros flagge
# tuning : DEEPEN_MINSYN=1 DEEPEN_TIN=0.85 (defauts)
```

`deepen` re-partitionne à `lambda`, prend le terminal ou grade flaggé ciblé, RECONSTRUIT
un arbre sur ce sous-ensemble avec **SNP + IS6110 + RD dans la distance** (pour que les
clades IS-définis émergent), et nomme les sous-clades faisables sous **contraintes
relâchées** (MINSYN=1, t_in=0.85). Comme la géographie y est homogène (ex. cœur UK
tout-UK), l'objectif géo ne s'applique pas : la résolution vient de la SYNAPO, de l'IS et
du temporel. C'est le 2e étage du système TWO-TIER : géo-MDL pour le squelette (lignées
géo-distinctes) plus `deepen` pour les cœurs clonaux géo-homogènes mais IS-divergents
(ex. cœur UK d'Eu1 : grade d'environ 5000 souches, IS_div 18, clades régionaux APHA
résolus par IS).

## Cycle complet, registres et primitives

(consolidé depuis `lineage-cycle` et `lineage-traces`, archivés le 2026-06-24)

Ce skill est le MOTEUR de SUBDIVISION (définition des sous-lignées). Le reste du cycle
taxonomique (outliers, mal-rangées, régénération des registres, multi-signal, traces
rares) vit dans des scripts de `global_supplementary/` ; les deux anciens skills sont
archivés, leur contenu opérant est ici. Les scripts eux-mêmes PERSISTENT (rien supprimé).

1. **Régénérer les registres après `materialize`** (obligatoire pour rendre la taxonomie
   utilisable par les autres outils ; les dirs bdd seuls ne suffisent pas). Depuis
   `global_supplementary/barcoding_v2/`, après un snapshot
   `cp -p barcode_complete.tsv barcode_complete.tsv.cyclesnap_<clade>_<date>` :
   `python3 build_inventory.py` (entités depuis bdd/actuelle) puis
   `python3 mine_bovis_markers.py` (markers per-pool, Bovis ; pour d'autres genres
   adapter le miner) puis `python3 build_barcodes.py` (écrit `barcode_complete.tsv`).
   Puis les caches : `traces_mask/build_clade_unions.py` (et `build_rdis_index.py` pour
   RD/IS). NOTE : `mine_bovis_markers` exige l'exclusivité vs TOUT le genre
   (IN>=0.9/OUT<=0.02), donc une sous-lignée définie SEULEMENT per-pool-dans-sa-lignée
   (ex. D.Espagne) ressort à 0 marker dans le barcode ; c'est normal (le barcode est
   SPDI-globalement-exclusif), ses markers per-pool propres restent dans les sorties de
   ce skill. `data/markers_v2/*.txt` d'un projet (noms underscore) n'est PAS lu par
   `build_barcodes`.

2. **Cycle orchestrateur (ce que ce skill ne fait PAS)** : `traces_mask/lineage_cycle.py
   --prefix <P> [--apply]` = détection OUTLIERS (QC couverture < frac*médiane et
   isolement NN > Q3+k*IQR) plus MAL-RANGÉES (vs `barcode_complete.tsv`) plus triage
   chimères, vers `bdd/ignore/`, plus régénération des registres. DRY-RUN par défaut ;
   backup DIR (`tar` dans `traces_mask/_backups/`) avant tout `--apply`. C'est
   l'AUTORITÉ D'ÉCRITURE de la taxonomie maison (cf.
   `barcoding_v2/SOURCES_OF_TRUTH.md`). Après un `materialize`, un `lineage_cycle`
   dry-run détecte les outliers et mal-rangées résiduels que la subdivision ne traite pas.

3. **Multi-signal RD/IS** : après `build_rdis_index.py`, `traces_mask/multi_subdiv.py
   --prefix <P> --apply` enrichit `_marker_overrides.json` (SPDI) plus `rd_markers.json`
   plus `is_markers.json` plus blacklist SPDI-marker-less. Réparation :
   `fix_lineage_markers.py --prefix <P> --tol 1` re-dérive les markers exclusifs et
   blackliste les clades clonaux SANS synapo SPDI propre (BCG), ce qui évite la cascade
   de fausses chimères et mal-rangées (BCG : 67 fausses chimères avant fix). `--tol 1`
   (tolère 1 homoplasie) sinon un clade à 68 markers quasi-exclusifs est vidé à tort.
   Exclusivité RD/IS = GLOBALE (rd_cc/is_cc), JAMAIS within-leaf (RD/IS homoplastiques,
   donc sous-lignées fantômes).

4. **Traces rares 1-2 SNP (sensibilité aux radiations rapides)** :
   `traces_mask/traces_detect.py --prefix <P>` (read-only) détecte les sous-lignées à 1-2
   SNP exclusif que le régime MINSYN>=2 manque (tige courte = radiation rapide = la trace
   historique recherchée). Garde-fous orthogonaux à RÉUTILISER quand on descend à
   MINSYN=1 : **C3 profondeur** (min_dH>=3, median_dH>=10, sites ségrégants s>=8, ce qui
   écarte les bursts de transmission et les clones) et **C5 monophylie par
   PURETÉ-DE-VOISINAGE** (>=0.80 des porteuses ont pour plus proche voisin une autre
   porteuse ; robuste au missing-data, supérieur au test 4-gamètes que `spdi.txt` fausse).
   `max-ingroup-frac` 0.50 : une vraie sous-lignée rare est minoritaire dans son ingroup.

5. **Principes de design salvagés** (à intégrer dans les choix MINSYN/lambda) :
   (a) validité OU-jamais-ET, garder un clade s'il est PEUPLÉ (>=minn, même à 1 SPDI
   exclusif) OU rare-mais-riche (>=sig_rich SPDI propres, dès 2 souches : ex. L8/L10) ;
   plancher n>=2 pour rare-riche, sinon >=5. (b) Seuil rare-riche ADAPTATIF, jamais fixe :
   `max(gap, null-permutation)` par pool (le missing-data clonal fabrique environ 15 faux
   SPDI « exclusifs » entre 2 souches ; sur le tronc Bovis le seuil dérivé était 62 contre
   15 fixe). (c) PAS de gate bootstrap en clonal (un clade à 38 synapo peut avoir un
   support 0.5 ; la preuve est un SNP exclusif co-ségrégant plus >=5 porteuses plus la
   monophylie). (d) Membership = PORTEURS du SNP signature, pas la bipartition brute de
   l'arbre (qui aspire des non-porteurs par la topologie).

## Limites connues du mode `optimize`

- L'arbre est SNP-only (RD/IS augmentent le support des nœuds existants) ; un clade défini
  UNIQUEMENT par IS sans cluster SNP serait manqué. Pour ces cas, inclure RD/IS dans la
  distance avant linkage (extension future ; c'est ce que fait déjà `deepen` sur son
  sous-ensemble).
- Le repli glouton est une heuristique de sélection de sous-ensemble (pas l'optimum exact
  du subset) ; suffisant en pratique, le Pareto est lisse.

### Faut-il passer à une vraie optimisation multi-objectif (NSGA-II) ? Non, instruction du 2026-08-10

La question était ouverte (piste P9.3) : un balayage de `lambda` sur une scalarisation
n'est pas une optimisation multi-objectif, et un vrai front rendrait le choix explicite.
Verdict après examen : **ne pas réécrire le solveur**, pour deux raisons dont la seconde
est scientifique et non budgétaire.

**1. Sur les deux objectifs actuels, le balayage ne rate rien.** Une scalarisation
pondérée n'atteint que les points du front situés sur son enveloppe convexe. Mesuré sur
un front concave de référence : le balayage de 5 000 valeurs de `lambda` ne rend que
**2 solutions sur 41**, les deux extrêmes, et 95 % du front est hors de portée quelle que
soit la pondération. Sur un front convexe, en revanche, il rend **41 sur 41**. Le critère
de décision est donc la géométrie du front réel, et le skill la documente déjà : « le
Pareto est lisse ». Un Pareto lisse et régulier en `lambda` est la signature d'un front
convexe. Dans ce régime, NSGA-II retrouverait exactement ce que le balayage trouve déjà,
pour un coût de réécriture élevé.

**2. Le troisième objectif ne doit PAS en être un.** L'apport théorique de NSGA-III serait
de traiter la pureté synapomorphique comme un objectif à maximiser plutôt que comme la
contrainte `MINSYN`, un balayage 1D de `lambda` étant alors structurellement incapable de
couvrir un front à deux dimensions. Mais `MINSYN >= 2` est un critère **principiel**, pas
un compromis négociable : une sous-lignée sans synapomorphie propre n'est pas un clade,
elle est un cluster. En faire un objectif reviendrait à accepter des lignées sans
synapomorphie en échange d'un meilleur MDL, exactement ce que le cadrage « un cluster
n'est pas un clade » interdit. Le front gagné serait un front de solutions
taxonomiquement irrecevables.

À rouvrir seulement si un balayage réel montre des sauts de `#lignées` que `lambda` ne
peut pas franchir (symptôme de non-convexité), ou si un objectif légitimement négociable
s'ajoute. Note de coût, accessoire : le skill `pymoo` est installé mais **la bibliothèque
ne l'est pas** dans le Python système.
- La cohérence géo dépend de la couverture de géolocalisation (terminaux peu géolocalisés
  donnent un pays dominant bruité ; MINSYN et #BioProject filtrent).

---

# Garde-fous (impératifs, valables pour les DEUX modes)

- **JAMAIS `rm`** : `gio trash`. Aucune sortie de ce skill (PNG, HTML, TSV, pickle,
  répertoire de `bdd/`) ne se supprime définitivement. `materialize` logue tout et reste
  réversible.
- **Ne lancer `materialize ... apply` qu'après validation explicite de l'utilisateur** de
  la granularité (le coude du Pareto plus l'inspection). La taxonomie MTBC est pilotée par
  CG. Un cluster `explore` ne constitue jamais cette validation.
- **Taille minimale d'une sous-lignée = 5 souches** (en deçà, c'est de la microvariation
  clonale). Vaut aussi pour la lecture d'`explore` : un cluster HDBSCAN de 3 ou 4 souches
  ne se propose pas comme sous-lignée, quelle que soit sa silhouette.
- **Assignation des souches = CHARACTER-BASED (markers), PAS le dendrogramme** (corrigé
  2026-06-24 ; le dendrogramme average-linkage misplaçait les souches de GRADE, d'où des
  grades polyphylétiques, vécu A.2 17 souches plus D 15 souches). `materialize` RÉASSIGNE
  chaque souche au nœud nommé le plus profond dont elle PORTE la signature
  synapomorphique : descente top-down où, à chaque niveau, NODE (branche interne) =
  dominance RELATIVE (>=2 markers-signature, et 2x le 2e enfant) ; CLADE (crown terminal)
  = appartenance ABSOLUE (>=CLADE_FRAC~0.4 de la signature crown, sinon la souche reste au
  grade du nœud parent). Résultat : crowns monophylétiques, grades sur la BONNE branche,
  souches vraiment basales au grade racine. VÉRIFIER après `materialize` qu'aucun label de
  grade n'apparaît des 2 côtés d'un arbre ML (test anti-polyphylie).
- Le cœur (DP, synapo, MDL) reste **déterministe-séquentiel**, jamais un fan-out d'agents
  (reproductibilité, et un fan-out de prompts pathogène/souches a été policy-bloqué).
- **LIMITE RÉSIDUELLE (P7.8, 2026-06-25) : la SUBDIVISION (quels nœuds nommer) reste
  pilotée par le DENDROGRAMME average-linkage, qui ne voit que les CROWNS et RATE les
  clades LARGES ou NICHÉS** (les basaux partageant une synapomorphie PROFONDE sont
  éparpillés par l'average-linkage). C'est la même limite phénétique que celle du cadrage,
  ici du côté `optimize`. Symptôme (vécu D.1/D.2) : un clade large réel (Maroc-large 13 =
  crown 6 plus 7 basaux à 18 synapo ; France-large = crown 153 plus sœur 11) n'est pas
  nommé, ses basaux finissent au grade. PIÈGE ASSOCIÉ : `polytomy_check` sur les CROWNS
  donne une FAUSSE polytomie quand le nœud a un grade portant les synapo profondes (elles
  sont dans le « reste », donc tuent l'exclusivité ; cas D.1 : crowns UK/Esp/Maroc à 0
  synapo entre paires, lu « polytomie », alors qu'il y a une vraie bifurcation
  {UK+Maroc | Espagne}).
  CORRECTIF (outil) : `scripts/remat_from_tree.py <clade> <arbre_ML.nwk> <max_depth>
  [minsz] [minsyn] [apply]` (re)matérialise un clade depuis un ARBRE ML ou parcimonie
  (sous-clades = nœuds ML maximaux disjoints >=minsz et >=minsyn synapo per-pool ; grade =
  reste). PAS de collapse des nœuds-épine, donc traiter UN clade à la fois, pas un
  sous-arbre profond d'un coup. La PROFONDEUR `max_depth` dépend de la FORME du clade :
  COMB pectiné (lignées qui décrochent une à une, ex. D.2 France) demande une profondeur
  FAIBLE (1-2) et de nommer les divergentes À PLAT (sinon sur-nichage en cascade binaire) ;
  arbre BALANCÉ (bifurcations emboîtées, ex. Bovis.2.3) demande une profondeur PLUS
  GRANDE (4+) pour capturer les sœurs (une profondeur 3 les FUSIONNE).
  RÈGLE : re-matérialiser via `remat_from_tree` si une subdivision dendrogramme (i) rate
  un clade large ou niché, (ii) a un grade polyphylétique, OU (iii) a un GRADE qui cache
  une vraie sœur (souches directes d'un nœud formant un clade synapo-soutenu,
  MRCA-exact-sister du clade nommé). NE PAS conclure « clade sain, laisser » sur la seule
  monophylie des CLADES TERMINAUX : vérifier que les GRADES ne cachent pas de sœurs (test :
  synapo communes >=2 plus MRCA(grade ∪ sœur-candidate) = exactement leurs tips).
- Sources de vérité : `traces_mask/` (masques, clade_spdi_count, rd_cc/is_cc,
  bovis_rd4_qc), `bioproject_geo/consolidated_geo_<lignée>.tsv` (pays, dates, bioproject).
  RD/IS curées via `read_report` (missing_rd HORS CUS_GS ; IS6110), JAMAIS `report.json`
  brut. Le mode `explore` lit lui `report.json` directement, sans masque : ses features
  ne sont donc pas débruitées, ce qui est une raison de plus de ne pas en tirer de bornes.

## Codex script path note

Bundled script paths in this packaged copy are relative to the directory containing this `SKILL.md`. For sibling packaged skills, resolve the sibling directory in the same plugin cache before running scripts.
