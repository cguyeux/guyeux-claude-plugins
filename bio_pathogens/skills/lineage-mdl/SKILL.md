---
name: lineage-mdl
description: >-
  Definir les sous-lignees d'une lignee MTBC (ou bacterie clonale) par OPTIMISATION
  MULTICRITERES SOUS CONTRAINTES, le bruit traite en amont. Remplace les seuils
  heuristiques (GAIN constant, longueur de branche) par une formulation principielle :
  (A) DEBRUITAGE (masque homoplasie/resistance, QC compte SPDI + RD4, de003replication
  a rayon SNP, chimeres) ; (B) CONTRAINTES de faisabilite = un clade ssi >=MINSYN
  synapomorphies PROPRES multi-signal (SNP union RD union IS6110, exclusivite per-pool
  + globale) ET >=5 souches ET monophylie (polytomies emergent) ; (C) OBJECTIF de
  selection de modele MDL = maximiser la log-vraisemblance conditionnelle
  -n*H(pays|lignee) moins lambda par lignee (parcimonie ; single-BioProject penalise),
  optimise par un DP bottom-up avec REPLI dans le grade des enfants geo-redondants ;
  balayage de lambda -> front de Pareto -> coude. Flague les terminaux a forte etendue
  spatio-temporelle ou divergence IS comme candidats a re-investigation relachee.

  Utiliser quand : on veut une taxonomie de sous-lignees reproductible et defendable
  pour des etudes evolutives (phylogeographie, datation), pas un decoupage arbitraire ;
  quand un clade est dense/clonal et sur-sequence (un seuil constant sur/sous-resout) ;
  quand on veut que la granularite soit PILOTEE par la biologie (coherence geo/hote)
  sous garantie de support synapomorphique. NE PAS confondre l'ARBRE (synapo+monophylie
  = definit les clades) avec les CLUSTERS de distance (servent a dedupliquer/QC).
  Complementaire de pectinated-subclade-mining (extraction manuelle d'UN sous-clade) :
  ici on OPTIMISE la partition entiere d'une lignee. Voir aussi clade-finder, mtbc-lineages.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
argument-hint: "<ROOT-clade> [mode] (ex: Bovis.2.2.2.2.2.1 optimize)"
user-invocable: true
---

# /lineage-mdl -- Definition de sous-lignees par optimisation MDL sous contraintes

Definit les sous-lignees d'une lignee MTBC `ROOT` (un repertoire de `bdd/actuelle/`,
ex. `Bovis.2.2.2.2.2.1`, `L4.11`, `Orygis_La3`) comme la solution d'un probleme
d'optimisation, pas d'un seuil. Le script unique `scripts/lineage_mdl.py` enchaine les
etapes ; chaque etape ecrit dans `<projet>/résultats/lineage_mdl/<ROOT>/`.

## Pourquoi (le cadrage, a relire avant d'agir)

Decouper une lignee clonale dense est un **probleme d'optimisation multicriteres sous
contraintes en presence de bruit**. Trois erreurs a NE PAS commettre :

1. **La longueur de branche n'est PAS le critere.** Chez un clonal, une COURTE branche
   (meme 1 SNP) peut definir une vraie lignee. Ce qui definit un clade = la
   **synapomorphie propre** (etat derive partage, fixe, exclusif, hors-homoplasie),
   pas la magnitude. -> contrainte C1, pas un objectif.
2. **Ne pas forcer des bifurcations.** Il y a de vraies POLYTOMIES (radiations clonales).
   Elles emergent en n'autorisant des coupes qu'aux noeuds synapo-soutenus.
3. **Arbre != clusters.** Le dendrogramme average-linkage est PHENETIQUE (proxy) : il
   sert a dedupliquer et a echafauder, PAS a poser les bornes. Les bornes = synapo + monophylie.

Et le BRUIT se traite EN AMONT, sinon on optimise sur du bruit (sequencage -> faux SNP
-> fausses synapo ; chimeres ; mauvaise couverture ; paquets de transmission 2-3 SNP qui
sur-poids­ent les zones denses).

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

Boutons : **MINSYN** (combien de marqueurs per-pool suffisent a DEFINIR ; 1 = definissable
par un seul marqueur per-pool-exclusif de type SNP/RD/IS [le pere donne le contexte] ;
2-3 = plus robuste) et **lambda** (parcimonie). Tout le reste est fixe/principie.

**Interpreter lambda.** lambda = le PRIX, en nats d'information geographique, que doit payer
chaque lignee nommee : le DP ne nomme une coupe que si elle reduit l'incertitude
`H(pays|lignee)` de PLUS de lambda nats (~ lambda/0.69 bits). Petit lambda (2-8) -> beaucoup
de lignees fines ; grand lambda (45-90) -> peu de lignees larges. Le bon point = le COUDE de
la courbe lambda->#lignees->coherence (au-dela, la coherence ne baisse presque plus mais le
#lignees s'effondre). NE PAS choisir lambda dans l'abstrait : lancer `optimize` avec un
balayage fin et REGULIER (ex. 2,4,6,8,10,14,18,24,32,45,65,90), lire la table, et choisir par
le NOMBRE de lignees et la coherence voulus. La granularite est continue (objectif MDL + repli
glouton) ; tout entier intermediaire de lambda donne un resultat sensible.

## Flux de travail

```bash
P=~/docs/codes/mtbc/<projet>            # ex. Bovis_full ; sorties dans $P/résultats/lineage_mdl/<ROOT>/
PY=/home/christophe/venvs/ars311/bin/python
S=~/docs/codes/claude_plugins/bio_pathogens/skills/lineage-mdl/scripts/lineage_mdl.py

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

`RDIS=0` en variable d'env desactive le multi-signal (compare SNP-seul). Le multi-signal
ne CHANGE la partition que sur les lignees CLONALES pauvres en SNP (BCG-like) ; sur une
lignee SNP-saturee il corrobore sans rien sauver (verifie sur A/Eu1).

## Lecture du resultat et re-investigation relachee

`inspect` annote chaque lignee : n, synapo, #BioProject, **#pays, etendue temporelle
(span), divergence IS interne**, pays dominant, fenetre. Il **FLAGue** (colonne flag /
symbole) les terminaux a `n_pays>=4` OU `span>=30 ans` OU `IS_div>=3` : ce sont des
sous-lignees a forte etendue spatio-temporelle ou divergence IS, donc **sous-resolues**,
candidates a une **ré-investigation sous contraintes RELACHEES** via le mode `deepen` :

```bash
$PY $S deepen <ROOT> 24            # cible le PLUS GROS terminal flagge a lambda=24
DEEPEN_IDX=1 $PY $S deepen <ROOT> 24   # cible le 2e plus gros flagge
# tuning : DEEPEN_MINSYN=1 DEEPEN_TIN=0.85 (defauts)
```

`deepen` re-partitionne a `lambda`, prend le terminal/grade flagge cible, RECONSTRUIT un arbre
sur ce sous-ensemble avec **SNP + IS6110 + RD dans la distance** (pour que les clades IS-definis
emergent), et nomme les sous-clades faisables sous **contraintes relachees** (MINSYN=1, t_in=0.85).
Comme la geographie y est homogene (ex. coeur UK tout-UK), l'objectif geo ne s'applique pas : la
resolution vient de la SYNAPO + l'IS + le temporel. C'est le 2e etage du systeme TWO-TIER :
geo-MDL pour le squelette (lignees geo-distinctes) + `deepen` pour les coeurs clonaux geo-
homogenes mais IS-divergents (ex. coeur UK d'Eu1 : grade ~5000 souches, IS_div 18 -> clades
regionaux APHA resolus par IS).

## Garde-fous (imperatifs)

- **JAMAIS** `rm` : `gio trash`. `materialize` logue tout (reversible).
- Ne lancer `materialize ... apply` qu'apres **validation explicite** de l'utilisateur de
  la granularite (le coude du Pareto + inspection). La taxonomie MTBC est pilotee par CG.
- Le coeur (DP, synapo, MDL) reste **deterministe-sequentiel**, jamais fan-out d'agents
  (reproductibilite + un fan-out de prompts pathogene/souches a ete policy-bloque).
- Taille minimale d'une sous-lignee = **5 souches** (en deca = microvariation clonale).
- **ASSIGNATION des souches = CHARACTER-BASED (markers), PAS le dendrogramme** (corrige 2026-06-24 ; le
  dendrogramme average-linkage misplacait les souches de GRADE -> grades polyphyletiques, vecu A.2 17 souches
  + D 15 souches). `materialize` REASSIGNE chaque souche au noeud nomme le plus profond dont elle PORTE la
  signature synapomorphique : descente top-down ou, a chaque niveau, NODE (branche interne) = dominance
  RELATIVE (>=2 markers-signature, et 2x le 2e enfant) ; CLADE (crown terminal) = appartenance ABSOLUE
  (>=CLADE_FRAC~0.4 de la signature crown, sinon la souche reste au grade du noeud parent). Resultat : crowns
  monophyletiques + grades sur la BONNE branche + souches vraiment basales au grade racine. VERIFIER apres
  materialize qu'aucun label de grade n'apparait des 2 cotes d'un arbre ML (test anti-polyphylie).
- **LIMITE RESIDUELLE (P7.8, 2026-06-25) : la SUBDIVISION (quels noeuds nommer) reste pilotee par le
  DENDROGRAMME average-linkage, qui ne voit que les CROWNS et RATE les clades LARGES/NICHES** (les basaux
  partageant une synapomorphie PROFONDE sont eparpilles par le average-linkage). Symptome (vecu D.1/D.2) : un
  clade large reel (Maroc-large 13 = crown 6 + 7 basaux a 18 synapo ; France-large = crown 153 + soeur 11)
  n'est pas nomme, ses basaux finissent au grade. PIEGE ASSOCIE : `polytomy_check` sur les CROWNS donne une
  FAUSSE polytomie quand le noeud a un grade portant les synapo profondes (elles sont dans le « reste » -> tuent
  l'exclusivite ; cas D.1 : crowns UK/Esp/Maroc 0 synapo entre paires = « polytomie », MAIS vraie bifurcation
  {UK+Maroc | Espagne}). CORRECTIF (outil) : `scripts/remat_from_tree.py <clade> <arbre_ML.nwk> <max_depth>
  [minsz] [minsyn] [apply]` = (re)materialise un clade depuis un ARBRE ML/parcimonie (sous-clades = noeuds ML
  maximaux disjoints >=minsz & >=minsyn synapo per-pool ; grade = reste). PAS de collapse des noeuds-epine ->
  traiter UN clade a la fois, pas un sous-arbre profond d'un coup. La PROFONDEUR `max_depth` depend de la FORME
  du clade : COMB pectine (lignees qui decrochent 1 a 1, ex. D.2 France) -> depth FAIBLE (1-2) + nommer les
  divergentes A PLAT (sinon sur-niche en cascade binaire) ; arbre BALANCE (bifurcations emboitees, ex.
  Bovis.2.3) -> depth PLUS PROFONDE (4+) pour capturer les soeurs (depth 3 les FUSIONNE). REGLE : re-materialiser
  via remat_from_tree si une subdivision dendrogramme (i) rate un clade large/niche, (ii) a un grade
  polyphyletique, OU (iii) a un GRADE qui cache une vraie soeur (souches directes d'un noeud formant un clade
  synapo-soutenu, MRCA-exact-sister du clade nomme). NE PAS conclure « clade sain, laisser » sur la seule
  monophylie des CLADES TERMINAUX : verifier que les GRADES ne cachent pas de soeurs (test : synapo communes
  >=2 + MRCA(grade ∪ soeur-candidate) = exactement leurs tips).
- Sources de verite : `traces_mask/` (masques, clade_spdi_count, rd_cc/is_cc,
  bovis_rd4_qc), `bioproject_geo/consolidated_geo_<lignee>.tsv` (pays+dates+bioproject).
  RD/IS curees via `read_report` (missing_rd HORS CUS_GS ; IS6110), JAMAIS report.json brut.

## Cycle complet, registres & primitives (consolide depuis lineage-cycle / lineage-traces, archives 2026-06-24)

lineage-mdl est le MOTEUR de SUBDIVISION (definition des sous-lignees). Le reste du cycle taxonomique
(outliers, mal-rangees, regeneration des registres, multi-signal, traces rares) vit dans des scripts de
`global_supplementary/` ; ces deux anciens skills (lineage-cycle, lineage-traces) sont archives, leur contenu
operant est ici. Les scripts eux-memes PERSISTENT (rien supprime).

1. **Regenerer les registres apres `materialize`** (obligatoire pour rendre la taxonomie utilisable par les
   autres outils ; les dirs bdd seuls ne suffisent pas). Depuis `global_supplementary/barcoding_v2/`, apres un
   snapshot `cp -p barcode_complete.tsv barcode_complete.tsv.cyclesnap_<clade>_<date>` :
   `python3 build_inventory.py` (entites depuis bdd/actuelle) -> `python3 mine_bovis_markers.py` (markers
   per-pool, Bovis ; pour d'autres genres adapter le miner) -> `python3 build_barcodes.py` (ecrit
   `barcode_complete.tsv`). Puis les caches : `traces_mask/build_clade_unions.py` (+ `build_rdis_index.py`
   pour RD/IS). NOTE : `mine_bovis_markers` exige l'exclusivite vs TOUT le genre (IN>=0.9/OUT<=0.02) -> une
   sous-lignee definie SEULEMENT per-pool-dans-sa-lignee (ex. D.Espagne) ressort a 0 marker dans le barcode ;
   c'est normal (le barcode est SPDI-globalement-exclusif), ses markers per-pool propres restent dans les
   sorties lineage-mdl. `data/markers_v2/*.txt` d'un projet (noms underscore) n'est PAS lu par build_barcodes.

2. **Cycle orchestrateur (ce que lineage-mdl ne fait PAS)** : `traces_mask/lineage_cycle.py --prefix <P>
   [--apply]` = detection OUTLIERS (QC couverture < frac*mediane + isolement NN > Q3+k*IQR) + MAL-RANGEES (vs
   `barcode_complete.tsv`) + triage chimeres -> `bdd/ignore/` + regeneration registres. DRY-RUN par defaut ;
   backup DIR (`tar` dans `traces_mask/_backups/`) avant tout `--apply`. C'est l'AUTORITE D'ECRITURE de la
   taxonomie maison (cf. `barcoding_v2/SOURCES_OF_TRUTH.md`). Apres lineage-mdl materialize, un lineage_cycle
   dry-run detecte les outliers/mal-rangees residuels que la subdivision ne traite pas.

3. **Multi-signal RD/IS** : apres `build_rdis_index.py`, `traces_mask/multi_subdiv.py --prefix <P> --apply`
   enrichit `_marker_overrides.json` (SPDI) + `rd_markers.json` + `is_markers.json` + blacklist SPDI-marker-less.
   Reparation : `fix_lineage_markers.py --prefix <P> --tol 1` re-derive les markers exclusifs et blackliste les
   clades clonaux SANS synapo SPDI propre (BCG) -> evite la cascade de fausses chimeres/mal-rangees (BCG : 67
   fausses chimeres avant fix). `--tol 1` (tolere 1 homoplasie) sinon un clade a 68 markers quasi-exclusifs est
   vide a tort. Exclusivite RD/IS = GLOBALE (rd_cc/is_cc), JAMAIS within-leaf (RD/IS homoplastiques -> sous-
   lignees fantomes).

4. **Traces rares 1-2 SNP (sensibilite aux radiations rapides)** : `traces_mask/traces_detect.py --prefix <P>`
   (read-only) detecte les sous-lignees a 1-2 SNP exclusif que le regime MINSYN>=2 manque (tige courte =
   radiation rapide = la trace historique recherchee). Garde-fous orthogonaux a REUTILISER quand on descend a
   MINSYN=1 : **C3 profondeur** (min_dH>=3, median_dH>=10, sites segregants s>=8 -> ecarte les bursts de
   transmission/clones) et **C5 monophylie par PURETE-DE-VOISINAGE** (>=0.80 des porteuses ont pour plus proche
   voisin une autre porteuse -- robuste au missing-data, superieur au test 4-gametes que spdi.txt fausse).
   `max-ingroup-frac` 0.50 : une vraie sous-lignee rare est minoritaire dans son ingroup.

5. **Principes de design salvages** (a integrer dans les choix MINSYN/lambda) : (a) validite OU-jamais-ET --
   garder un clade s'il est PEUPLE (>=minn, meme a 1 SPDI exclusif) OU rare-mais-riche (>=sig_rich SPDI
   propres, des 2 souches : ex. L8/L10) ; plancher n>=2 pour rare-riche, sinon >=5. (b) Seuil rare-riche
   ADAPTATIF, jamais fixe : `max(gap, null-permutation)` par pool (le missing-data clonal fabrique ~15 faux
   SPDI "exclusifs" entre 2 souches ; sur le tronc Bovis le seuil derive etait 62 vs 15 fixe). (c) PAS de gate
   bootstrap en clonal (un clade a 38 synapo peut avoir support 0.5 ; la preuve = SNP exclusif co-segregant +
   >=5 porteuses + monophylie). (d) Membership = PORTEURS du SNP signature, pas la bipartition brute de l'arbre
   (qui aspire des non-porteurs par la topologie).

## Limites connues

- L'arbre est SNP-only (RD/IS augmentent le support des noeuds existants) ; un clade
  defini UNIQUEMENT par IS sans cluster SNP serait manque -> pour ces cas, inclure RD/IS
  dans la distance avant linkage (extension future).
- Le repli glouton est une heuristique de selection de sous-ensemble (pas l'optimum
  exact du subset) ; suffisant en pratique, le Pareto est lisse.
- La coherence geo depend de la couverture de geolocalisation (terminaux peu geoloc =
  pays dominant bruite ; MINSYN + #BioProject filtrent).
```
