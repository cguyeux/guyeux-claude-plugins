---
name: mixed-infection
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST) for detecting mixed
  infections and within-host heterogeneity in published MTBC research isolates,
  with QuantTB (Anglin/Abeel lab, BMC Genomics 2020) for identifying and
  quantifying co-infecting strains, and binoSNP (Research Center Borstel,
  Scientific Reports 2020) for low-frequency antimicrobial-resistance alleles
  under a binomial model. Use when: a strain shows an impossible marker
  combination or an inflated variant count, a resistance allele appears at
  intermediate frequency, a candidate new sublineage must be ruled out as an
  artefact of co-infection, or within-host diversity is the object itself.
argument-hint: "<souche|liste> [--quantify] [--resistance]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# Infections mixtes et hétérogénéité intra-hôte

## Pourquoi cela compte au-delà de la clinique

Une infection mixte n'est pas seulement un fait épidémiologique : c'est un **générateur de faux
résultats phylogénomiques**. Deux souches dans un même échantillon produisent, après appel de
variants majoritaire, un profil chimérique qui porte des marqueurs de deux lignées à la fois. Les
conséquences sont exactement celles que nos travaux de subdivision cherchent à éviter :

- une combinaison de marqueurs **impossible** au regard de la nomenclature, lue à tort comme une
  lignée nouvelle ;
- un **compte de variants anormalement élevé** (les positions hétérozygotes s'ajoutent) ;
- des marqueurs « exclusifs » d'un clade candidat qui ne sont que le second génotype présent ;
- une résistance apparemment discordante entre génotype et phénotype, parce que l'allèle résistant
  n'est porté que par une fraction de la population.

> [!IMPORTANT]
> **Avant d'annoncer un clade nouveau à faible effectif, écarter l'infection mixte.** C'est un modèle
> nul alternatif au même titre que l'homoplasie ou l'erreur de placement, et il est testable. La
> discipline du dépôt sur les marqueurs (voir `taxonomy-node-validation` dans la base de
> connaissances) mesure la fuite et le portage, mais un profil chimérique peut passer ces filtres.

## Deux outils, deux questions

| outil | question | référence |
|---|---|---|
| **QuantTB** | combien de souches dans cet échantillon, et dans quelles proportions ? | Abeel lab, *BMC Genomics* 2020, `10.1186/s12864-020-6486-3`, GPL-3.0, `github.com/AbeelLab/quanttb` |
| **binoSNP** | cet allèle de résistance existe-t-il à basse fréquence ? | Research Center Borstel (`ngs-fzb`), *Sci Rep* 2020, `10.1038/s41598-020-64708-8`, GPL-3.0, workflow R |

QuantTB travaille sur des SNP et compare l'échantillon à une base de génotypes de référence : il
identifie **et** quantifie. binoSNP teste chaque position candidate sous un **modèle binomial**, ce qui
lui permet d'appeler un allèle minoritaire là où un appel majoritaire le rejette.

Note de provenance utile : binoSNP vient de **Borstel**, avec qui le groupe a déjà un dossier
(`~/docs/codes/mtbc/Borstel/`). L'outil et l'interlocuteur vont ensemble.

## QuantTB — installation validée sur `mp`, et incompatibilité bloquante avec nos VCF

> [!WARNING]
> **QuantTB, tel quel, ne fonctionne PAS sur les VCF produits par le pipeline TBannotator/freebayes
> du groupe (`annotated.vcf`).** Ce n'est pas une question d'installation : son parseur
> (`quanttb/scripts/classify.py`) suppose un format **Pilon**, où le 6e champ `;`-séparé de `INFO`
> est `BC=<A>,<C>,<G>,<T>` (comptage de lectures par nucléotide, cœur de son calcul
> d'hétérogénéité). Notre `INFO` (`AB;AO;DP;QA;QR;RO;TYPE;ANN...`) place à cette position
> `RO=<entier unique>`, que le code interprète à tort comme un vecteur `BC` à un seul élément ;
> `sum(BC)` tombe alors à 0 pour toute position homozygote de référence, et la quasi-totalité des
> variants du fichier est classée « qualité insuffisante ». Résultat observé : une table de sortie
> **entièrement vide** (pas un score bas — rien à comparer), sans message d'erreur explicite.
> Constaté le 2026-08-29 sur `SRR25515049` (projet `nucs_deletion_mutators`), 1461 variants, 0
> retenu. **Ne pas retenter sans corriger ce point** (traduire `AO`/`RO`/`REF`/`ALT` en un faux
> vecteur `BC` est possible mécaniquement mais dégrade la mesure — les deux bases non observées y
> sont mises à 0, rendant invisible par construction une 3e base minoritaire réelle, ce qui va à
> l'encontre même de l'usage prévu par ce skill). **Pour un VCF issu de ce pipeline, préférer la
> voie CRAM** : `mixed_infections_multimarker/analyses/` (`phase0_signal_inventory.py`,
> `phase1_prevalence_screen.py` et suivants) implémente `het_frac` + re-pileup CRAM ciblé
> (`bcftools mpileup -a AD,DP`), déjà validé à 136 824 souches, qui travaille directement sur
> `mapped.cram` sans dépendre du format `INFO` d'un VCF externe — insensible à cette
> incompatibilité. Réserver QuantTB à un VCF réellement issu de Pilon, ou à la voie FASTQ (`-f`,
> nécessite `samtools`+`bwa` dans le `PATH`), qui contourne l'incompatibilité en produisant
> elle-même un VCF Pilon et n'exige aucun VPN — voir la section « Voie FASTQ » ci-dessous.

**Installation validée sur `mp`** (aucun `sudo` requis, testée 2026-08-29) : QuantTB est écrit en
Python 2.x, désormais obsolète, et son dépôt amont (`github.com/AbeelLab/quanttb`) contient
plusieurs bugs qui empêchent toute exécution telle quelle.

```
mkdir -p ~/tools && cd ~/tools && git clone --depth 1 https://github.com/AbeelLab/quanttb.git
virtualenv -p python2 ~/tools/quanttb_venv
source ~/tools/quanttb_venv/bin/activate
pip install --upgrade 'pip<21' setuptools wheel
pip install numpy==1.14.5 scipy==1.1.0   # subprocess32 échoue à compiler (Python.h absent, pas de python2.7-dev sans sudo)
printf 'from subprocess import *\n' > ~/tools/quanttb_venv/lib/python2.7/site-packages/subprocess32.py  # shim : l'API utilisée (subprocess32.call) est un sous-ensemble de subprocess standard
cd ~/tools/quanttb && pip install --no-deps -e .
```

Quatre corrections locales sont ensuite nécessaires (bugs du dépôt amont, jamais remontés en
issue/PR à ce jour — à faire si l'outil doit resservir souvent) :

1. `quanttb/scripts/quanttb.py:35` — `os.mkdirs(qtobj.temp)` n'existe pas en Python (`os` n'a que
   `os.makedirs`) → remplacer par `os.makedirs(qtobj.temp)`.
2. `quanttb/scripts/quanttb.py:1` — `errno` est utilisé (`e.errno == errno.EEXIST`) sans jamais
   être importé → ajouter `import errno` en tête de fichier.
3. `quanttb/scripts/quanttb.py:39-40` — le bloc `try/except OSError as e: if ...: pass` est suivi
   d'un `else: raise` **au même niveau d'indentation que `except`**, formant un `try/except/else`
   où le `else` s'exécute (et lève une exception invalide, `TypeError`) précisément quand le
   `try` a RÉUSSI. Réindenter `else: raise` de 4 espaces pour le rattacher au `if` interne (il
   doit se déclencher seulement quand l'erreur n'est PAS un simple « dossier déjà existant »).
4. `quanttb/scripts/classify.py:127` — `int(base[5])` (colonne QUAL du VCF) échoue sur un `QUAL`
   flottant (`7831.78`, format GATK/freebayes) → remplacer par `int(float(base[5]))`.

Après ces quatre correctifs, l'outil s'exécute et reproduit exactement la table attendue par le
README amont sur ses données d'exemple (`exdata/sample1snps.vcf`) — l'installation elle-même est
donc validée ; c'est uniquement la compatibilité avec NOS VCF qui reste bloquante (voir
avertissement ci-dessus).

## Voie FASTQ (`quant -f`) : installation LOCALE sans VPN, et format de sortie

> [!IMPORTANT]
> **Le verrou « il faut le VPN » est souvent un verrou sur le CHEMIN HABITUEL, pas sur la
> question.** QuantTB par la voie VCF exige nos `annotated.vcf` de `mp` (VPN), et se heurte de
> toute façon à l'incompatibilité de format ci-dessus. La voie FASTQ n'a besoin ni de l'un ni de
> l'autre : les lectures brutes sont **publiques sur l'ENA** (`ftp.sra.ebi.ac.uk`, en HTTPS,
> ~2,5 Mo/s mesuré), et c'est le pipeline interne de QuantTB (`bwa` puis Pilon) qui produit le
> VCF au format Pilon qu'attend son propre parseur. Le contournement de l'incompatibilité est
> donc gratuit. Vérifié le 2026-09-06 (projet `variant_nucs`, P8.8).

**Installation locale (poste de travail, sans `sudo`, Python 2 obsolète), variante de la recette
`mp` ci-dessus** : `get-pip` pour 2.7 en `--user`, `numpy==1.14.5` et `scipy==1.1.0` en roues
`cp27`, et `subprocess32==3.5.4` **réellement compilé** (le shim de la recette `mp` reste le repli
quand `Python.h` manque). Les quatre correctifs amont restent nécessaires à l'identique.

**Coût réel, à budgéter avant de lancer** : `bwa` traite une souche en ~100 s, mais **Pilon est le
facteur limitant**, plusieurs dizaines de minutes par souche même à faible profondeur. Compter en
heures pour une vingtaine de souches, trois jobs en parallèle. Prévoir aussi le disque : ~500 Mo à
1 Go de FASTQ par souche, plus un BAM de ~150 Mo. Le `temp/` est purgé automatiquement par
`rmtree` en fin de souche (sauf `--keepin`), mais les FASTQ, eux, restent.

**Un répertoire de sortie par souche, et un verrou.** QuantTB écrit son `temp/` À CÔTÉ du chemin
passé à `-o` : deux jobs parallèles partageant le même répertoire se détruisent mutuellement.
Un `mkdir` atomique (`mkdir "$d/.lock" || exit 0`) protège en plus contre le cas réel où un job
lancé à la main est relancé par-dessus par un pilote qui itère sur toute la liste.

> [!WARNING]
> **Format de sortie : CSV séparé par des VIRGULES, pas TSV**, avec un **espace de tête** sur
> chaque nom de colonne (`quanttb/scripts/quanttb.py` l.291-293 : `header = "sample, refname,
> totscore, relabundance, depth\n"`, puis `",".join(...)`). Une ligne par souche de référence
> détectée : `n == 1` = souche unique, `n > 1` = mélange, `relabundance` pour les proportions.
> Lu en TSV, le fichier rend une colonne unique, chaque conversion en flottant échoue et un
> parseur qui avale l'erreur (`except ValueError: continue`) rend **zéro ligne** — ce qui se lit
> « aucune co-infection », c'est-à-dire exactement l'hypothèse nulle qu'on cherchait à confirmer.
> Mode d'échec silencieux et indiscernable du résultat attendu. **Tester le parseur sur deux
> fichiers fabriqués à la main (un mélange, un échantillon pur) AVANT de lancer le calcul.**
> Noter aussi que le fichier est ouvert en `"ab"` : relancer sur le même `-o` empile les
> résultats, d'où l'utilité d'un garde « déjà fait ».

> [!CAUTION]
> **`-o` n'est PAS le nom du fichier de sortie : QuantTB lui accole `qtb.txt`.**
> `quanttb.py` l.29 : `out = outdir + "/" + prefix + 'qtb.txt'`, où le préfixe est le chemin
> passé à `-o`. Un `-o .../results.txt` produit donc **`.../results.txtqtb.txt`**. Conséquence
> vécue (2026-09-06) : le garde « déjà fait » du script de lancement, l'agrégateur de résultats
> et la veille d'avancement cherchaient tous les trois `results.txt` et voyaient « aucun
> résultat » alors que la première souche avait terminé avec succès. C'est la **troisième**
> façon, après le séparateur CSV et le mode append, dont cet outil rend un faux « rien trouvé »
> sans rien signaler. Chercher la sortie par motif (`ls "$d"/*qtb.txt`, `glob("*qtb.txt")`),
> jamais par le nom qu'on croit avoir choisi.

> [!CAUTION]
> **QuantTB SUR-APPELLE des infections mixtes, et le mécanisme n'est pas connu.** Mesuré le
> 2026-09-07 sur 21 souches MTBC monoclonales par ailleurs (projet `variant_nucs`, P8.8) :
> **16 sur 21 reçoivent un appel de seconde souche** à 12-50 % d'abondance, qu'aucune mesure
> indépendante ne corrobore. Deux contrôles à exiger avant de croire un appel de mélange, et
> ils doivent concorder. (1) EXTERNE : l'impureté génome-entier (fraction de lectures de
> référence aux sites variants) doit être du même ordre que la fraction minoritaire annoncée ;
> observé ici 0,09-1,3 % contre 12-50 % annoncés, soit des facteurs 10 à 500. (2) INTERNE, sans
> calibration : la somme des `depth` attribués aux composantes ne peut pas dépasser ce qu'une
> souche seule explique, des populations qui se PARTAGENT les lectures ne totalisant pas plus de
> 100 % de la profondeur. Calibrer ce second contrôle sur les souches que l'outil lui-même
> appelle monoclonales (critère indépendant du ratio, donc non circulaire) : ici 0,57-0,84 pour
> les monoclonales contre 0,91-1,69 pour les appels de mélange, **séparation complète**.
>
> **MÉCANISME ÉTABLI (2026-09-07) : le critère d'arrêt des itérations est un seuil ABSOLU.**
> `classify.py` l.379/469/488 : `while ... and maxvalue > maxthresh ...`, avec `maxthresh` = 0,15,
> relevé à 0,20 quand la couverture moyenne dépasse 25x. L'outil ne demande jamais si la
> composante suivante est bonne *par rapport* à la première, ni si elle explique une part
> importante du résidu : il la compare à un plancher fixe. Or sur un jeu MTBC ordinaire, la
> MEILLEURE référence n'obtient qu'un `totscore` de 0,39 à 0,50 — l'échelle entière des scores
> est du même ordre que le plancher. Mesuré sur les 21 souches : composantes de rang 1 à 0,482 de
> médiane, composantes supplémentaires à 0,282, et **aucune composante appelée sous 0,20**, les
> minima frôlant le seuil (0,201 et 0,209) — la distribution est coupée net par le plancher.
> L'outil distingue donc bien une bonne composante d'une mauvaise (0,482 contre 0,282), mais ne
> s'en sert pas pour s'arrêter : un critère RELATIF au score de la première aurait coupé là où le
> plancher laisse passer. **Conséquence pratique : sur tout jeu dont les scores d'ajustement sont
> de l'ordre du seuil, QuantTB ajoutera des composantes tant que le budget d'itérations le permet
> (`iterationmax`, 8 par défaut), et le nombre de souches qu'il annonce ne mesure alors plus la
> co-infection.**
>
> Deux explications ont été testées et RÉFUTÉES avant celle-ci, à ne pas resservir : l'ambiguïté
> entre références voisines (les références co-appelées sont à 962 SNP de médiane contre 1160
> pour des paires au hasard, z = -1,49) et la mauvaise représentation de la souche par la base
> (totscore de la meilleure identique chez monoclonales et sur-appelées, U = 40, p = 1,00,
> rho = 0,011). Scripts : `variant_nucs/analyses/phase59_*`, `phase60_*`, `phase61_*`.

**Puissance de détection, à porter dans le tableau de sortie.** Un verdict « souche unique » n'est
informatif que si la profondeur rendait la minoritaire comptable : ~20 lectures attendues pour une
sous-population à 5 % demandent une profondeur totale d'environ 100x. En dessous, l'absence de
mélange est une absence de puissance, à déclarer comme telle dans une colonne dédiée plutôt que
laissée à l'interprétation du lecteur.

## Ce que nos données permettent, et ce qu'elles ne permettent pas

> [!WARNING]
> **Le `bdd/` local ne conserve pas le signal sous-clonal.** `spdi.txt` et le `report.json` portent des
> appels majoritaires. Pour toute question d'hétérogénéité intra-hôte, il faut remonter aux données
> qui gardent les comptes d'allèles : `annotated.vcf` et `mapped.cram` sur `mp`
> (`/data/current/run/results/<SRA>/`), où les champs de profondeur par allèle existent. Voir
> `fetch-tbannotator` et `remote-compute` (VPN requis).
>
> **Et le seuil d'appel de la chaîne masque le phénomène par construction** : les critères sont
> profondeur ≥ 10, qualité d'erreur < 5 %, et **≥ 90 % des lectures soutenant la mutation**. Un allèle
> présent chez 30 % de la population est donc invisible dans nos sorties standard, non parce qu'il
> n'existe pas, mais parce qu'il a été filtré. C'est la raison même d'utiliser ces deux outils.

## Garde-fous d'interprétation

**Une fraction n'est pas une preuve de co-infection.** Un allèle à fréquence intermédiaire peut venir
d'une contamination croisée en laboratoire, d'un mapping ambigu dans une région répétée (PE/PPE, IS),
ou d'une duplication. Vérifier la position contre les régions masquées avant de conclure, et exiger
plusieurs positions cohérentes plutôt qu'une seule.

**La profondeur commande, ici encore.** Détecter une sous-population à 5 % demande une profondeur qui
la rende comptable : sur nos souches MTBC (36× à 538×, mesuré) c'est jouable, sur une cohorte à 5× non.
Trier sur `meandepth` de `coverage_stats.tsv` avant de lancer.

**Distinguer les trois explications d'un phénotype discordant** : allèle minoritaire réel, mutation
hors du catalogue interrogé (`resistance-catalogue`), ou résistance non génétique. Les trois demandent
des vérifications différentes, et seule la première relève de ce skill.

## Composition

`fetch-tbannotator` (obtenir VCF et CRAM) → **`mixed-infection`** (l'échantillon est-il pur ?) →
`strain-qc` (la souche est-elle exploitable ?) → `mtbc-lineages` / `pectinated-subclade-mining` (le
clade candidat survit-il à l'écartement de l'infection mixte ?) → `resistance-profiler` pour le volet
allèles de résistance.
