# Axes lateraux -- banques de questions generatrices et exemples travailles

A lire **au moment d'attaquer la Phase 2** (divergence). Pour chaque axe :
la logique, une banque de questions a se poser sur les donnees et la lignee du
projet, les skills/donnees qui l'alimentent, et un ou deux exemples travailles
pour calibrer la qualite attendue. Ne pas repondre a toutes les questions :
s'en servir comme amorces jusqu'a ce que des idees neuves emergent.

Regle transversale : chaque idee generee ici est **brute**. Elle passera le
modele nul et le challenge en Phase 6. Ici on ne censure pas.

---

## A. `hote` -- Coevolution avec l'hote humain

**Logique.** Le MTBC est un pathogene obligatoire, sans reservoir environnemental
pour les lignees humaines : son histoire est indissociable de celle de ses hotes.
Le modele sympatrique (Gagneux) propose que chaque lignee est adaptee a une
population humaine et y reussit mieux -- une hypothese testable des qu'on croise
lignee du pathogene et ascendance de l'hote.

**Banque de questions.**
- La distribution des lignees/sous-lignees du projet epouse-t-elle une structure
  de population humaine connue (ascendance, groupe ethno-linguistique) ?
- Peut-on tester un appariement sympatrique : les isolats d'une lignee viennent-ils
  preferentiellement d'hotes d'une ascendance donnee, au-dela de la simple
  cooccurrence geographique ?
- Des variants de l'immunite innee/adaptative de l'hote (HLA classe I/II,
  `SLC11A1`/NRAMP1, TLR2/8, LTA4H, cytokines) sont-ils associes a la lignee dans
  la region du projet (litterature) ?
- Existe-t-il des **paires hote-pathogene anciennes** (aDNA humain + aDNA MTBC)
  dans la region/periode, permettant de dater la coevolution ?
- Y a-t-il un signal de co-divergence formel (topologie pathogene vs topologie
  hote) testable par un test de congruence ?

**Skills / donnees.** `host-pathogen-pair` (AADR x SPAAM), `coevolution` (Mantel,
PACo, congruence), `modern-human-reference-panels` (1kGP/SGDP/HGDP),
`migration-data`, `ancestral-reconstruction`.

**Exemple travaille.** Projet a forte composante migratoire (main-d'oeuvre
sud-asiatique) : plutot que "L1 vient d'Asie du Sud" (trivial), tester si la
sous-structure L1 des isolats suit l'ascendance fine des hotes (Tamoul vs
Bengali vs Sindhi), ce qui distinguerait un flux unique d'un brassage de sources
-- et croiser avec HGDP/1kGP pour l'ascendance de reference. Piste neuve car elle
descend au niveau sous-lignee x ascendance, pas pays x lignee.

---

## B. `histoire` -- Histoire genetique et evolutive humaine

**Logique.** Une date d'introduction ou un TMRCA n'a de sens qu'en regard de la
frise des mouvements humains. La meme date "1200 CE" est banale ou remarquable
selon qu'elle tombe sur une expansion commerciale documentee ou dans un vide
historique.

**Banque de questions.**
- Les TMRCA / dates d'introduction estimees coincident-ils avec un evenement
  demographique humain date (Neolithique, age du Bronze, expansions
  commerciales, conquetes, traites, colonisation, migrations de travail
  contemporaines) ?
- Une expansion Ne(t) de la lignee s'aligne-t-elle sur une transition
  demographique humaine (urbanisation, revolution industrielle locale, boom
  petrolier et immigration) ?
- La profondeur de diversite d'une lignee dans la region trahit-elle un ancrage
  ancien (siecles) vs une importation recente (decennies) -- et l'histoire
  connue de la region soutient-elle l'un ou l'autre ?
- Un evenement historique brutal (famine, guerre, deplacement force) a-t-il pu
  laisser un goulot d'etranglement visible dans la phylogenie ?

**Skills / donnees.** `molecular-clock`, `iqtree-lsd2` (tip-dating LSD2),
`bayesian-skyline` (Ne(t)), `migration-data` (frise historique curatee),
`beast2-phylogeography`.

**Exemple travaille.** Distinguer "endemique ancien" d'"importe recent" ne se
tranche pas par l'appartenance a une sous-lignee (une sous-lignee peut etre a la
fois ancienne dans la region ET reintroduite). Le trancher par la **structure
temporelle interne** : une lignee endemique ancienne montre une diversite intra-
regionale profonde et un skyline plat ancien ; une importee recente montre un
skyline en cliquet recent cale sur la periode de migration documentee. Piste :
comparer skyline par lignee vs frise migratoire de la region.

---

## C. `geo` -- Histoire, geographie, routes

**Logique.** Les corridors genomiques ne tombent pas du ciel : ils suivent des
routes physiques (maritimes, caravanieres), des reseaux d'empire, des flux de
pelerinage, des regimes climatiques (mousson). La geographie et l'histoire
fournissent des **priors** forts pour interpreter -- ou predire -- un
enrichissement de corridor.

**Banque de questions.**
- Quelles routes historiques relient la region du projet aux pays enrichis dans
  les corridors observes (commerce, esclavage, pelerinage, empire) ?
- Un corridor "surprenant" statistiquement s'explique-t-il par une route
  historique oubliee (et donc n'est pas un artefact) ?
- Le climat (mousson, saisons de navigation) structure-t-il la direction et la
  saisonnalite des flux ?
- Le pelerinage (Hajj, autres) constitue-t-il un brasseur periodique de lignees a
  l'echelle continentale, testable via la sur-representation de certaines
  origines ?
- La geographie interne (desert, montagne, littoral vs interieur) cree-t-elle une
  structuration infra-nationale (ex. un gouvernorat cotier plus connecte a
  l'ocean Indien qu'a l'interieur) ?

**Skills / donnees.** `phylogeography`, `geo-map`, `sra-geolocate`,
`ancestral-reconstruction` (fleches de migration), `migration-data`,
`itol` (arbre annote geo).

**Exemple travaille (Oman).** L'enrichissement du corridor **Tanzanie** (mesure a
8x l'attendu) n'est pas un hasard statistique : le sultanat d'Oman a gouverne
Zanzibar et la cote swahili, et le commerce de la mousson de l'ocean Indien a lie
Mascate/Sohar a l'Afrique de l'Est pendant des siecles. Piste : tester si les
isolats du corridor tanzanien portent une signature L3/L1 est-africaine coherente
avec ce commerce, et si le signal est plus fort dans les gouvernorats cotiers.
Deuxieme prior : le **Hajj** comme brasseur -- sur-representation attendue
d'origines de tout le monde musulman, a distinguer du flux de main-d'oeuvre
sud-asiatique unidirectionnel.

---

## D. `reseaux` -- Reseaux de genes, epistasie, evolution compensatoire

**Logique.** Les mutations n'evoluent pas independamment : elles interagissent
(epistasie), se compensent (cout de fitness rachete par une seconde mutation), et
s'organisent en operons et regulons. Une lignee peut se distinguer moins par une
mutation isolee que par un **recablage** de reseau.

**Banque de questions.**
- Les mutations definissant la lignee co-occurrent-elles plus qu'attendu (paires
  en desequilibre, sur un meme operon/regulon) ?
- Y a-t-il une signature d'**evolution compensatoire** : mutation couteuse
  (ex. rpoB de resistance, katG) suivie d'une compensatrice (rpoC/rpoA, ahpC) ?
- Le reseau d'interaction (STRING) d'un gene mute est-il enrichi en autres genes
  mutes dans cette lignee (module fonctionnel sous selection) ?
- Un regulon (DosR, PhoPR, WhiB) porte-t-il une accumulation de variants
  lignee-specifiques suggerant une adaptation de tout un programme
  transcriptionnel ?
- Les pertes de genes (RD, missing_genes) dessinent-elles une reduction de reseau
  coherente (adaptation a un mode de vie/hote) ?

**Skills / donnees.** `mtbc-gene-network`, `string-db`, `convergent-evolution`,
`spdi-annotation`, `pangenome-enrichment`.

**Exemple travaille.** Au lieu de compter les mutations de resistance une a une,
cartographier leur **ordre et leur compensation** : dans les isolats MDR de la
lignee, rpoB-S450L precede-t-il systematiquement une mutation rpoC compensatrice ?
La presence/absence de la compensatrice predit-elle le succes epidemique (croiser
avec THD) ? Piste reliant reseaux (D) et phylodynamique (G).

---

## E. `3d` -- Evolution de la conformation 3D des proteines

**Logique.** Deux mutations synonymes en apparence peuvent avoir des consequences
structurales opposees (l'une neutre, l'autre destabilisant un site actif ou une
interface). La structure 3D est une couche d'interpretation que le comptage de
SNP ignore.

**Banque de questions.**
- Les mutations lignee-specifiques touchent-elles des positions structuralement
  critiques (site actif, interface, coeur hydrophobe) plutot que la surface ?
- Y a-t-il **convergence structurale** : des mutations differentes, dans des
  lignees differentes, produisant le meme effet 3D (meme poche deformee) ?
- Un gene annote "hypothetique"/"dark" de la lignee a-t-il un repliement (Foldseek/
  ESM) trahissant une fonction enzymatique, avec site catalytique conserve ?
- Les mutations de resistance de perte-de-fonction (pncA, ethA, katG) correspondent-
  elles a des lesions structuralement destructrices coherentes avec le phenotype ?
- L'impact 3D predit (ESM-1v, score de destabilisation) hierarchise-t-il les
  variants au statut OMS "incertain" mieux que le seul comptage ?

**Skills / donnees.** `esm-atlas-cli` (ESM Atlas), `active-site-check` (residus
catalytiques M-CSA), `mtbc-gene` (impact fonctionnel d'une mutation), `spdi-annotation`.

**Exemple travaille.** Pour la prediction de resistance (WP PZA/BPaLM d'un projet
resistance) : classer les variants pncA "incertains" du catalogue par **score de
destabilisation structurale** ESM, et tester si le seuil structural separe mieux
R/S que l'appartenance au catalogue exact. Piste reliant 3D (E) et resistance ;
apport concret a l'amelioration du catalogue OMS.

---

## F. `mycobacteries` -- Place dans les mycobacteries, polarisation par Canettii et animales

**Logique.** Un caractere n'est "derive" ou "specifique" que par rapport a un etat
ancestral. L'outgroup (*M. canettii*, ecotypes animaux, NTM proches) est le seul
moyen de **polariser** : sans lui, on prend un ancestral conserve pour une
nouveaute, ou l'inverse. C'est aussi le garde-fou anti-misclassification
(cf. l'echec `Mycobacterium_sp_novel`).

**Banque de questions.**
- Un trait presente comme "specifique a la lignee" l'est-il encore une fois
  compare a canettii / bovis / caprae / orygis / microti (polarisation) ?
- Quel etat d'un caractere (presence de gene, RD, allele) est ancestral vs derive,
  vu depuis canettii ?
- Le contenu genomique "absent de H37Rv" d'une lignee est-il ancestral (present
  chez canettii, perdu dans le tronc MTBC) ou accessoire/contaminant ?
- Un transfert horizontal visible chez *M. canettii* (genome mosaique) a-t-il un
  echo -- ou une absence signifiante -- dans la lignee ?
- La lignee montre-t-elle une reduction de genome (pseudogenisation, pertes de RD)
  sur la trajectoire generale du MTBC, ou une exception ?
- Toute souche au profil aberrant du projet a-t-elle ete criblee contre les NTM
  (`bdd/hors_mtbc/`) pour ecarter une misclassification (M. kansasii mime la TB) ?

**Skills / donnees.** `denovo-content-qc` (ancestral vs accessoire vs contaminant),
`species-id` (skani/Mash), `pangenome-enrichment`, `convergent-evolution`,
`strain-qc` ; projet voisin `Canettii/`, `bdd/hors_mtbc/`.

**Exemple travaille.** Avant d'annoncer qu'un ilot genomique est "signature de la
lignee", le polariser : BLAST/skani contre canettii + M. bovis. S'il est present
chez canettii, c'est un **caractere ancestral conserve**, pas une nouveaute -- une
piste qui inverse l'interpretation. Garde-fou obligatoire pour toute revendication
de nouveaute (cf. CLAUDE.md, echec Mycobacterium_sp_novel).

---

## G. `phylodyn` -- Phylodynamique et ecologie evolutive

**Logique.** Au-dela de "qui est apparente a qui", la phylodynamique lit dans la
forme de l'arbre l'histoire des populations : croissance, declin, succes
epidemique, structure de transmission. Le binaire cluster/singleton est pauvre en
regard.

**Banque de questions.**
- La trajectoire Ne(t) (skyline) d'une lignee raconte-t-elle une expansion ou un
  declin cale sur un evenement identifiable ?
- Le succes epidemique gradue (THD, densite haplotypique) distingue-t-il mieux les
  lignees qui se propagent de celles qui stagnent que le seuil de cluster ?
- La topologie du reseau de transmission (chaines longues vs etoiles) trahit-elle
  un mode de propagation (super-propagation vs transmission diffuse) ?
- Y a-t-il des infections mixtes / de l'evolution intra-hote detectables (heterozygotie
  de SNP) qui brouillent les distances de transmission ?
- Le seuil de distance de transmission (12 SNP) est-il valide pour le type
  d'alignement utilise (genome entier vs core-genome), ou faut-il le recalibrer ?

**Skills / donnees.** `bayesian-skyline`, `thd`, `snp-distance`, `tsne-hdbscan`,
`iqtree-lsd2`.

**Exemple travaille.** Remplacer le comptage de clusters <12 SNP par une mesure
**continue** de succes (THD parametree par une echelle de temps) : elle gradue le
succes sans imposer un seuil binaire, separe endemique de long terme et
importe-recent-qui-se-propage, et se correle a des covariables (nationalite, annee).
Piste directement pertinente pour un projet de dynamique de transmission.

---

## H. `selection` -- Selection moleculaire et immuno-evasion

**Logique.** La signature de la selection (positive, purifiante, balancee) revele
ce qui est adaptatif. Le MTBC a une particularite frappante : ses epitopes de
lymphocytes T sont **hyperconserves** (Comas 2010), ce qui suggere que le
pathogene "veut" etre reconnu -- un paradoxe fertile.

**Banque de questions.**
- Quels genes de la lignee portent une signature de selection positive (dN/dS,
  test MK) une fois corrige le biais d'ascertainment propre aux SNP MTBC ?
- Le paradoxe des epitopes T hyperconserves tient-il dans cette lignee, ou
  observe-t-on une variation d'epitope signalant une echappee immunitaire locale ?
- Y a-t-il **convergence adaptative** inter-lignees (memes genes mutes
  independamment dans plusieurs lignees) signalant une pression selective partagee
  (hote, antibiotique, environnement) ?
- Les familles PE/PPE, les systemes ESX, les PKS/PDIM (paroi, virulence)
  montrent-ils une evolution acceleree specifique a la lignee ?
- Une mutation de resistance porte-t-elle un cout de fitness detectable (branche
  plus courte, sous-representation) rachete ou non par compensation (lien vers D) ?

**Skills / donnees.** `mk-ascertainment` (MK corrige), `convergent-evolution`,
`lineage-comparison` (tests stat), `spdi-annotation`, `pangenome-enrichment`.

**Exemple travaille.** Scanner les genes mutes independamment dans >= 2 lignees
majeures du projet (convergence) et tester l'enrichissement en PE/PPE/ESX vs le
reste du genome : une convergence enrichie en genes d'interface avec l'hote
signale une pression selective liee a l'hote, pas au hasard. Attention au modele
nul : la convergence peut aussi etre de l'homoplasie par hypermutabilite locale --
a distinguer.

---

## Meta-axe `--wild` -- analogies transverses

**Logique.** Les percees viennent souvent d'un concept importe d'un champ
etranger. En mode `--wild`, prendre deliberement une idee hors phylogenomique et
la projeter sur le projet. Assumer le haut risque ; le challenge fera le tri.

**Amorces (a instancier sur le projet).**
- **Ecologie des metapopulations** : traiter les gouvernorats/pays comme des
  patchs source-puits ; une lignee est-elle une metapopulation avec source
  identifiable et puits satellites ?
- **Reseaux sociaux / epidemiologie de reseau** : la structure de transmission
  suit-elle une topologie scale-free (super-propagateurs) plutot qu'aleatoire ?
- **Linguistique historique** : l'arbre des lignees et l'arbre des langues de la
  region partagent-ils une topologie (co-dispersion langue-pathogene avec les
  populations) ?
- **Theorie des jeux evolutionnaires** : resistance vs sensibilite comme
  strategies a frequence-dependance ; un equilibre est-il attendu ?
- **Physique des transitions de phase / percolation** : le passage endemique ->
  epidemique se lit-il comme un seuil de percolation dans le reseau de contacts ?
- **Theorie de l'information / compression** : la complexite d'un alignement de
  lignee (entropie par site) discrimine-t-elle diversite profonde vs expansion
  clonale mieux qu'une distance moyenne ?

Chaque analogie ne vaut que si elle produit une **prediction testable** sur les
donnees du projet ; sinon, la tuer en Phase 6 comme jolie mais sterile.
