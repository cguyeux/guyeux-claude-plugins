---
name: pocket-detection
description: >
  Academic research toolkit (Guyeux group, FEMTO-ST) : détection de poches de
  liaison sur un modèle structural (P2Rank, fpocket, PocketMiner/AE-PocketMiner),
  installation locale validée (workarounds GCC 14+/16 et GPU→CPU inclus), et
  surtout le garde-fou qui prime sur les trois outils : aucun score de poche ne
  se lit en valeur absolue sans calibration par témoins positif ET négatif
  appariés à la population étudiée (taille, membranaire ou non, prédit ou
  expérimental). Utiliser quand : chercher un site de liaison candidat sur un
  gène dark bien replié, juger la druggabilité d'une cible, ou évaluer si
  l'absence de poche est un résultat négatif informatif ou un angle mort du
  détecteur (protéines courtes, membranaires).
---

# pocket-detection : poches de liaison (P2Rank, fpocket, PocketMiner) et leur calibration

## Quand l'utiliser, et le garde-fou qui prime sur tout le reste

Utiliser pour cribler un gène dark bien replié (structure prédite ou expérimentale) à la
recherche d'un site de liaison candidat, juger sa druggabilité, ou décider si l'absence de
poche détectée est un résultat négatif citable ou un simple angle mort de la méthode.

**Garde-fou central, vérifié empiriquement sur les TROIS outils ci-dessous (2026-08) : un score
de poche brut n'est JAMAIS interprétable sans témoin positif ET négatif appariés à la
population étudiée.** Ce n'est pas une precaution générique, c'est un résultat mesuré à chaque
fois qu'on a cherché à le vérifier :
- **P2Rank** calibré sur enzymes prouvées vs protéines non catalytiques (même pipeline, mêmes
  modèles AlphaFold) : 50,7 % de poche confiante chez les enzymes, 4,5 % chez les dark — MAIS le
  détecteur n'a AUCUN pouvoir sous 200 acides aminés (3,8 % de détection même chez des enzymes
  PROUVÉES de cette taille, contre 60,5 % au-delà). Un contrôle négatif « mauvais modèle » est
  lui-même confondu ici (la qualité du modèle influence directement la détection) — n'utiliser
  QUE des groupes appariés en qualité de modèle, jamais un contrôle par pLDDT seul.
- **fpocket**, testé sur une protéine à 4 hélices transmembranaires : trouve une poche de
  1866 ų (200 sphères alpha, druggability 0,629) qui est presque certainement la gouttière
  lipidique entre hélices prise pour une cavité, pas un site réel. fpocket sous-note aussi
  systématiquement les sites actifs polaires/chargés de métalloenzymes (score entraîné sur des
  poches apolaires « drug-like ») — ne jamais conclure « non-druggable » sur un site métal à
  score bas.
- **PocketMiner / AE-PocketMiner** (réseau GVP-GNN) : score moyen par résidu élevé et PROCHE
  sur une protéine test ET sur un témoin soluble à poche connue (0,61 et 0,53) — pas un
  artefact de la protéine testée, une propriété du score brut de ce modèle, conçu à l'origine
  pour un CLASSEMENT RELATIF intra-protéine (Meller et al. 2023), pas une probabilité calibrée à
  seuiller à 0,5 pour n'importe quelle protéine.

**Question à se poser avant de croire un chiffre, quel que soit l'outil** : « ce score
discrimine-t-il un témoin positif connu d'un témoin négatif connu, dans la MÊME tranche de
taille et le MÊME type structural (soluble/membranaire, prédit/expérimental) que ma cible ? »
Si cette calibration n'a pas été faite, le chiffre n'est pas interprétable — répondre « je ne
sais pas encore » est plus honnête que d'en tirer une conclusion.

## Les trois outils, et quand choisir lequel

- **P2Rank** (Krivák & Hoksza 2018) : le plus rapide, calibré sur les poches
  d'expérimental (PDB) donc optimiste sur un modèle prédit. Nécessite Java 17
  (`JAVA_HOME`), fonctionne tel quel sur toute structure PDB/mmCIF. Bon premier passage.
- **fpocket** (Le Guilloux 2009) : géométrique pur (sphères alpha), donne aussi un score de
  druggabilité et un volume/SASA par poche — utile pour discounter les faux positifs
  membranaires par leur géométrie disproportionnée (volume/SASA/distance centre-de-masse
  anormalement grands).
- **PocketMiner / AE-PocketMiner** (Meller et al. 2023 ; successeur `bowman-lab/ae-pocketminer`,
  ajoute une couche d'attention pour un signal ALLOSTÉRIQUE distinct du score de poche) : seul
  des trois à viser les poches CRYPTIQUES (fermées dans la structure statique), donc
  potentiellement complémentaire de P2Rank/fpocket sur un repli fermé sans cavité apparente.
  Score à lire par RANG intra-protéine, jamais en valeur absolue (cf. garde-fou ci-dessus).

## Installation locale (recettes validées, sans root, CPU uniquement)

> [!TIP]
> Le repli CPU décrit ci-dessous reste la voie normale pour quelques structures. Pour un CRIBLE
> (plusieurs dizaines de protéines, ou AE-PocketMiner sur un protéome), le GPU du mésocentre est
> disponible : partition `gpu` de `mh` (A100 40 Go), avec le module `deep/tensorflow-gpu/2.12.0`
> qui évite de reconstruire un environnement. Ne pas viser `gpu_l40`, qui est une partition privée. Voir le skill
> `remote-compute` (sonde d'état, modèles `sbatch`, plafond d'un GPU par utilisateur). Prérequis :
> VPN monté (`sudo vpn up`).

### P2Rank
Nécessite Java 17 spécifiquement (le défaut système est souvent 8) :
```bash
JAVA_HOME=/usr/lib/jvm/java-17-openjdk <chemin>/prank predict targets.ds -o out -threads 4
```

### fpocket
```bash
scripts/build_fpocket.sh
```
Wrapper de build DURCI (piste Rv1025 P5.3, 2026-08-24) : clone le commit épinglé
(`4bb0d8447f62fee77e2c3c29f54b5fcaf5e2c066`) dans `~/.cache/fpocket_build/` (hors scratchpad,
réutilisé d'un projet à l'autre), détecte la version de GCC et n'applique le contournement
`-Wno-error=...` que si GCC >= 14, vérifie que le binaire produit répond bien comme fpocket
(pas seulement qu'il existe) avant de l'installer dans `~/.local/bin/fpocket`, et est idempotent
(ne reconstruit pas si un binaire fonctionnel est déjà installé ; `--force` pour reconstruire).
**PIÈGE, GCC 14+/16** : `make` seul échoue, `-Wincompatible-pointer-types` &co. sont promus en
ERREURS dures depuis GCC 14 — c'est ce que le script contourne, sans toucher au Makefile. Build
~1-2 min, source mise en cache ~360 Mo, binaire installé quelques Mo.

### PocketMiner / AE-PocketMiner
Le README officiel dit « requires Linux and a GPU » et l'`environment.yml` épingle
`cudatoolkit`/`cudnn`/`tensorflow-gpu` — **c'est l'environnement FOURNI par les auteurs (vitesse
d'entraînement), pas une contrainte de l'inférence.** Le code (`xtal_predict.py`, `models.py`)
n'a aucun appel `tf.device('/GPU:0')` ni opérateur CUDA-only. Contournement, même famille que le
skill `boltz` (PyTorch CPU) mais pour TensorFlow :
```bash
uv python install 3.10
uv venv --python 3.10 ~/venvs/pocketminer
uv pip install --python ~/venvs/pocketminer/bin/python "tensorflow==2.10.0"   # PAS tensorflow-gpu
uv pip install --python ~/venvs/pocketminer/bin/python "numpy==1.26.4"        # voir piège ci-dessous
uv pip install --python ~/venvs/pocketminer/bin/python \
  "pandas==2.2.2" "h5py==3.8.0" "mdtraj==1.10.0" "tqdm==4.64.1" "matplotlib==3.9.2" \
  "biopython==1.84" "scikit-learn==1.5.1" "biotite==1.1.0" "networkx==3.4.2" \
  "tabulate==0.9.0" "msgpack==1.1.0" "pillow==10.4.0" "joblib==1.4.2" "pyyaml==6.0.2" "scipy==1.15.1"

git clone https://github.com/bowman-lab/ae-pocketminer.git
git -C ae-pocketminer checkout 3328ca0376d3e4959545bac35e036435d582ff2e
```
**PIÈGE CRITIQUE (numpy)** : installer `tensorflow==2.10.0` seul tire numpy 2.x par défaut, qui
**casse le wrapper bfloat16 compilé de TF 2.10** (`TypeError: Unable to convert function return
value to a Python type!`). Épingler `numpy==1.26.4` (la version exacte de l'`environment.yml`
d'origine) APRÈS l'install de tensorflow, pas avant (sinon un pip ultérieur le remonte).
Les modèles pré-entraînés (~19 Mo, `aepocketminer`+`pocketminer`) sont DÉJÀ dans le clone Git,
aucun téléchargement séparé (contraste avec Boltz, ~8 Go). Empreinte totale mesurée : fpocket
360 Mo + ae-pocketminer 880 Mo + venv 2,1 Go ≈ **3,3 Go**. Les avertissements
`Could not load dynamic library 'libcudart.so...'` / `Skipping registering GPU devices...` au
runtime sont le comportement ATTENDU (repli CPU), pas une erreur.

**Usage local** (place le PDB dans `inputs/`, édite `nn_path` dans une copie de
`src/example_config.yaml` vers le chemin ABSOLU du clone, `use_attention: True` pour
AE-PocketMiner ou `False` pour PocketMiner pur) :
```bash
python src/xtal_predict.py my_config.yaml
```
Sorties dans `results/<modèle>/` : `<pdb>-preds.npy` (probabilité de poche cryptique par
résidu, 1×N) et, si `use_attention: True`, `<pdb>-attention_weights.npy` (matrice N×N de poids
d'attention résidu-résidu — signal ALLOSTÉRIQUE distinct, cf. `find_key_attention_residues.py`
pour en tirer les résidus de couplage les plus influents sur un site donné).

## Garde-fous d'interprétation supplémentaires

1. **Une poche ne nomme NI ligand NI réaction.** Compatible avec catalyse, stockage, senseur,
   interaction protéine-protéine, ou rôle structural.
2. **Sous ~200 acides aminés, un négatif n'est pas un résultat** (mesuré : 3,8 % de détection
   P2Rank chez des enzymes prouvées de cette taille). Écrire cette limite dans toute fiche
   plutôt que de laisser un blanc ambigu entre « testé, rien trouvé » et « le test n'a aucun
   pouvoir ici ».
3. **Le contrôle « mauvais modèle » (pLDDT bas) est confondu pour la détection de poche**, pas
   pour la conservation de séquence. Utiliser des groupes appariés en QUALITÉ DE MODÈLE
   (tous pLDDT élevé), jamais un contraste cibles-bon-modèle vs contrôle-mauvais-modèle.
4. **fpocket sous-note les sites polaires/métalliques** : ne jamais conclure « non druggable »
   sur ce seul score pour un site suspecté de lier un métal. **Chiffré** (Rv1025, triade
   Cys113/His115/Glu59 conservée) : la poche fpocket qui héberge le site métal a un Druggability
   Score de **0,238**, contre **0,645** pour une autre poche apolaire distincte de la même
   protéine — presque 3x plus bas, alors que le site métal est le site fonctionnel réel (conservé
   à 99-100 %, cf. `Rv1025/analyses/phase5_conservation_site.py`). **Recette pour attribuer
   correctement une poche fpocket à un site fonctionnel candidat** : ne PAS se fier au classement
   par Druggability Score, mesurer la distance minimale entre les sommets de sphères alpha de
   chaque poche (`pocketN_vert.pqr`) et les atomes donneurs candidats (Sγ Cys, Nδ1/Nε2 His,
   Oε1/Oε2 Glu, Oδ1/Oδ2 Asp...) sur le modèle APO — la poche dont les sphères alpha sont les plus
   proches (`<5 Å`) des donneurs conservés est le site fonctionnel, indépendamment de son DS.
   Script de référence, directement réutilisable : `Rv1025/analyses/phase14_druggability.py`
   (parse `<name>_info.txt` + `pocketN_vert.pqr`, calcule `dmin(poche, donneurs)`).
5. **PocketMiner/AE-PocketMiner : lire par rang intra-protéine**, jamais la valeur absolue.
6. **Toujours croiser au moins deux outils avant d'écrire une conclusion forte** ; leurs biais
   respectifs (expérimental-optimiste pour P2Rank, apolaire-biaisé pour fpocket, propension
   relative pour PocketMiner) ne se recouvrent pas.
7. **`find_key_attention_residues.py` : ne JAMAIS rapporter le « top-40 » tel quel, et TOUJOURS
   EXCLURE le premier et le dernier résidu du classement avant toute lecture** (calibré sur un
   panel de 11 protéines, 30-900 aa, 2026-08-04). Le résidu N-terminal est **dominant (rang 1 ou 2,
   ratio au bruit de fond 10x à 423x) dans 8 des 11 protéines testées**, sur toute la plage 30 à
   740 aa — ce n'est pas un artefact occasionnel mais quasi systématique en dessous de ~700 aa
   (donc sur la grande majorité du protéome MTBC). Il ne s'effondre que sur les protéines les plus
   longues du panel (550, 900 aa), et PAS de façon monotone avec la taille (à 700 aa le ratio est
   encore de 423x). Le biais C-terminal est beaucoup plus faible et erratique (0,4x à 3,2x) : ce
   n'est PAS un artefact symétrique, seul le N-terminus est massivement affecté. Recalculer aussi
   la distribution complète des scores restants (hors N/C-terminal) avant de croire un « top-N » :
   sur Rv2620c, le rang 40/41 ne se séparait que de 0,1 % de l'étendue totale — un seul résidu
   dominait réellement au-delà du terminus, les 39 suivants étaient indiscernables du bruit.
   Calibration : `analyses/phase96_p16_3i_terminus_bias_calibration.py` (annotation_mtbc).
8. **Sous ~200 aa, fpocket ET AE-PocketMiner échouent AUSSI à discriminer — le garde-fou #2
   n'est pas propre à P2Rank, c'est un plancher de la CLASSE de méthode.** Calibré sur le même
   panel apparié que #2 (25 enzymes courtes prouvées vs 25 protéines non catalytiques courtes,
   pLDDT_AF≥70) : **fpocket** trouve ≥1 poche sur 25/25 des DEUX groupes (Fisher p=1,0 — la simple
   présence d'une poche ne discrimine RIEN sur ce segment de taille, fpocket étant par construction
   sensible et non spécifique) et son meilleur drug_score ne sépare pas non plus les groupes
   (médianes 0,461 vs 0,429, Mann-Whitney p=0,82) ; **AE-PocketMiner** ne discrimine ni sur le score
   brut maximal (p=0,20) ni sur le contraste intra-protéine (max-médiane)/écart-type recommandé par
   le garde-fou #5 (p=0,55). Les TROIS outils (P2Rank géométrique-ML, fpocket géométrique pur,
   AE-PocketMiner GNN+attention) échouent donc, chacun À SA MANIÈRE (silence quasi total pour
   P2Rank, bruit indiscriminé pour fpocket, absence de séparation pour AE-PocketMiner), sur les
   protéines courtes — signature d'une limite géométrique/physique du problème (une petite surface
   n'a simplement pas la place de former une poche profonde distinguable d'une irrégularité de
   surface), pas d'une faiblesse corrigible d'un algorithme en particulier. **Ne pas déployer l'un
   de ces outils comme « recours » quand un autre échoue sous ce seuil** : les trois partagent le
   même angle mort. Calibration : `analyses/phase99_p16_3h_pocket_calibration_short.py`
   (annotation_mtbc).

## Voir aussi

- `boltz` (même famille de contournement GPU→CPU, pour la prédiction de complexes plutôt que de
  poches) ; `active-site-check` (site catalytique M-CSA, à croiser avec une poche P2Rank/fpocket
  avant d'écrire « enzyme active ») ; `esm-atlas-cli` (structure prédite en amont).
- Exemple travaillé : `annotation_mtbc/analyses/phase72_pocket_af_full.py` (P2Rank calibré),
  `phase72b_pocket_calibration.py` (calibration par groupes appariés), `phase76_rv2620c_boltz.py`
  et `tools/fpocket/`, `tools/ae-pocketminer/` (installations de référence sur cette machine) ;
  `mtbc/Rv1025/analyses/phase14_druggability.py` (attribution poche fpocket ↔ site fonctionnel par
  distance sphères alpha/donneurs, garde-fou #4).
