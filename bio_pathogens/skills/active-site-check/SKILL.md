---
name: active-site-check
description: >
  Academic research toolkit (Guyeux group, FEMTO-ST) : valide une requalification
  d'enzyme « same fold → enzyme active » en vérifiant que les RÉSIDUS CATALYTIQUES
  de l'enzyme M-CSA appariée par Foldseek sont conservés dans la protéine requête.
  Utiliser quand : gène « hypothetical »/dark du MTBC avec hit Foldseek vers une
  enzyme, annotation d'un protéome par structure, preuve de site actif demandée
  par un reviewer.
---

# active-site-check : validation du site catalytique via M-CSA

## Quand l'utiliser

- Un gène « hypothetical » / dark du MTBC a un hit Foldseek vers une enzyme connue et il faut
  trancher « enzyme active vs simple homologie de repli » avant d'écrire une fonction dans une
  fiche (projets `annotation_mtbc`, `TA_repertoire`, `dark_enzymes`).
- On annote un protéome bactérien par structure et il faut **graduer la confiance** des
  requalifications enzymatiques.
- Un reviewer demande des **preuves de site actif** à l'appui d'une annotation fonctionnelle.

Formulations qui doivent déclencher ce skill : « est-ce une enzyme active ou juste le même
repli », « résidus catalytiques », « site actif conservé », « M-CSA », « valider un hit
Foldseek enzyme ».

## Pourquoi ce skill

Le pipeline d'annotation structure-guidée (ESMFold + Foldseek + Pfam + eggNOG/UniProt, cf.
`annotation_mtbc/`) répond à « quel repli ? » et transfère des GO/EC par similarité. Mais **un hit
Foldseek significatif signifie « même repli », pas « enzyme active »** : beaucoup de protéines
adoptent un repli enzymatique sans en avoir le site actif (résidus catalytiques mutés/absents,
pseudo-enzymes, domaines détournés). Ce skill ajoute la couche manquante : confronter le hit aux
**résidus catalytiques curés de M-CSA** et vérifier leur présence/conservation dans la requête.

C'est l'apport additif par rapport :
- au pipeline atlas actuel (Foldseek seul → repli) ;
- au papier *Functional (re)annotation of Mycobacteroides abscessus proteome* (Gnanasekar et al.,
  Curr Res Struct Biol 2025, `10.1016/j.crstbi.2025.100172`), qui fait du transfert de GO par
  Foldseek sur modèles AlphaFold mais **ne valide pas les sites actifs**. Ce skill est précisément
  le cran de rigueur en plus, réutilisable sur tout protéome.

## Données : M-CSA

Mechanism and Catalytic Site Atlas (Thornton group, EBI). ~1003 entrées / 895 EC, résidus
catalytiques curés à la main, mappés sur PDB **et** UniProt, avec leurs rôles mécanistiques.
API REST (utilisée par le script, cache disque sous `$MCSA_CACHE` ou `~/.cache/mcsa/`) :
- `…/api/entries/<id>/?format=json`, entrée détaillée (résidus embarqués).
- `…/api/entries/?format=json`, liste paginée (indexée localement par EC/UniProt/PDB).
Champs clés : `reaction.ec`, `reference_uniprot_id`, `residues[i].residue_sequences[0].resid`
(numérotation UniProt), `residues[i].residue_chains[0].{pdb_id,chain_name,auth_resid,code}`,
`residues[i].roles_summary`. Citation : Ribeiro et al., NAR 2018 (M-CSA), CC-BY 4.0.

## Usage

```bash
PY=~/.claude/skills/active-site-check/active_site_check.py   # (symlink) ou chemin canonical

# 1) Lister les résidus catalytiques d'une enzyme M-CSA (par EC, UniProt, PDB ou M-CSA id)
python3 $PY residues --mcsa 2
python3 $PY residues --ec 3.5.2.6
python3 $PY residues --pdb 1btl        # (charge la liste complète au 1er appel, puis cache)

# 2) Vérifier la conservation du site actif dans la requête
#    qaln/taln = chaînes alignées requête/cible (avec '-'), en coordonnées de SÉQUENCE de la cible ;
#    tstart = numéro de résidu UniProt du premier résidu cible aligné ;
#    qstart = numéro de résidu (séquence requête) du premier résidu requête aligné (def. 1 --
#             ne le laisser à 1 que si qaln couvre la requête depuis son tout premier résidu ;
#             pour un alignement LOCAL, style Foldseek, passer son propre `qstart`).
python3 $PY check --uniprot P62593 --tstart 68 --qaln "S-ALK..." --taln "SXALK..."
```

Verdict : sur N résidus catalytiques, k présents (non-gap) et m identiques.
`m/N ≥ 0.8` → **site actif conservé → enzyme probablement active** ; `k/N < 0.5` → **fold-only**
(même repli, site actif non retenu) ; entre les deux → partiel/ambigu à inspecter.

**Sortie `check` (2026-08-01) : chaque résidu porte désormais `query_resid`**, le numéro du
résidu REQUÊTE (pas seulement sa lettre) sur lequel le résidu catalytique cible s'est aligné —
`None` s'il tombe dans un gap de la requête. C'est le seul chiffre qui permette de confronter le
résultat à une autre méthode (superposition structurale, autre outil) : sans lui, chaque appelant
devait ré-parcourir `qaln`/`taln` à la main pour le retrouver (dette constatée et corrigée,
`dark_enzymes` P10.3, cf. `smoke_test.py`).

## Branchement sur le pipeline atlas (Foldseek)

L'alignement requête↔cible vient directement de Foldseek (phase2c) lancé avec
`--format-output query,target,...,qaln,taln,qstart,tstart,...`. Pour chaque hit dont la cible est
une enzyme cataloguée M-CSA (résoudre l'EC/UniProt de la cible PDB), passer `qaln/taln/tstart` à
`check`. Pour une intégration proteome-wide, en faire une phase `phase2i_mcsa.py` qui itère sur les
hits Foldseek significatifs et écrit une colonne `mcsa` sur la fiche (résidus catalytiques attendus,
présents, identiques, verdict).

## Limites / garde-fous (à respecter, cf. conventions MTBC)

- **Réconciliation de numérotation** (le point délicat). M-CSA donne le résidu en numérotation
  UniProt ET PDB (`auth_resid`), souvent décalées (ex. entrée 2 : SER68 UniProt = PDB A:70). Le
  script mappe en coordonnées de **séquence cible** (UniProt) : il faut donc que `taln/tstart`
  soient dans la même numérotation que les `uniprot_resid` de M-CSA. Si l'alignement Foldseek est en
  coordonnées de structure PDB, convertir via le mapping SEQRES↔auth_resid de la cible avant `check`.
  En cas de doute, lister d'abord les résidus (`residues`) et vérifier l'ancrage sur 1-2 positions.
- **Conservation ≠ activité prouvée.** Un site actif conservé est une forte présomption, pas une
  preuve d'activité ; rester au niveau « probablement active », corroborer (littérature, contexte
  opéron/voie, expression) avant d'écrire un fait. Cohérent avec le garde-fou ESM/structure de
  `annotation_mtbc/CLAUDE.md`.
- **Couverture M-CSA limitée** (~895 EC) : beaucoup d'enzymes n'y sont pas ; absence d'entrée ≠
  absence de fonction. Le skill ne s'applique qu'aux hits dont la cible est cataloguée M-CSA.
- **Pseudo-enzymes** : un verdict fold-only peut révéler une pseudo-enzyme régulatrice
  (intéressant en soi), pas forcément une erreur d'annotation.

## Quand M-CSA ne couvre pas la cible : la ROUTE DE SUBSTITUTION (à appliquer par défaut)

**C'est le cas le plus fréquent, pas l'exception.** Portée mesurée deux fois : 1 gène sur 3906 dans
l'atlas MTBC ; 0 des 8 cibles AFDB de Rv3909 (2026-08-10). Face à un
`No M-CSA entry matched the selector`, ne pas s'arrêter là et surtout ne pas conclure : basculer sur
la procédure ci-dessous, qui rend un verdict PLUS solide que la route M-CSA nominale.

1. **Changer de template pour un membre de la même famille cristallisé AVEC son ligand**
   (substrat, analogue, inhibiteur). Chercher via la littérature de la famille, pas via le hit
   Foldseek d'origine. Vérifier d'abord que le template EST publié :
   `data.rcsb.org/rest/v1/core/entry/<ID>` → si `citation[].title` vaut « To be published », il n'a
   AUCUN résidu catalytique publié et ne peut pas servir de référence (cas 7E1Y).
2. **Définir le site géométriquement** : tous les résidus de la chaîne à < 4 Å d'un hétéro-atome non
   solvant (filtrer HOH/GOL/EDO/SO4/PO4/PEG/MPD/ACT/DMS et ions). Rend typiquement 15-25 positions
   au lieu des 2-3 de la dyade, donc de la puissance — et capture la machinerie de liaison
   (tryptophanes de stacking d'une CAZyme, etc.), dont l'absence est aussi parlante.
3. **Aligner la requête sur CE template** (Foldseek `easy-search`, en demandant
   `qcov,tcov,alntmscore,qtmscore,ttmscore,lddt,qaln,taln,qstart,tstart`).
4. **Trancher contre le NUL, jamais dans l'absolu** : comparer l'identité sur les résidus du site à
   l'identité de FOND du même alignement, par queue binomiale. Un site actif réel est nettement plus
   conservé que le fond. Exemple de verdict fold-only net : site 1/14 = 7,1 % contre fond
   41/346 = 11,8 %, p = 0,83. Sans ce nul, « la dyade n'est pas conservée » a très peu de puissance :
   à ~10 % d'identité l'absence est l'attendu, et une présence fortuite n'est pas rare non plus
   (E+D ≈ 12 % des résidus).

**Implémentation de référence, réutilisable en changeant template et dyade** :
`mtbc/Rv3909/analyses/phase2_active_site_aaapu.py` (parse mmCIF par nom de colonne, contacts
ligand, mapping d'alignement, nul binomial, sortie JSON).

**Contrôle de numérotation à mettre DANS LE CODE, pas dans la tête.** Avant tout mapping, vérifier
que la structure porte bien l'acide aminé attendu à `auth_seq_id = n`, et faire échouer bruyamment
sinon. Coût : 3 lignes ; bénéfice mesuré : a intercepté une dyade attribuée à la mauvaise protéine
(deux amylopullulanases GH57 homonymes, SmApu vs AaApu, conflatées par une recherche web). Sans ce
contrôle, le rapport aurait été faux et parfaitement présentable.

**Argument négatif gratuit à joindre au verdict** : `interpro/api/entry/pfam/<PF>` → si
`metadata.sets` est `null`, la famille n'appartient à aucun clan Pfam, donc aucune parenté de profil
avec la superfamille enzymatique envisagée.

## Statut

v1 (2026-06-09) : récupération M-CSA + mapping/conservation au niveau séquence, testée (entrée 2,
β-lactamase). v1.1 (2026-08-01, `dark_enzymes` P10.3) : `map_active_site`/`check` retournent la
position REQUÊTE de chaque résidu catalytique (`query_resid`) et acceptent un `qstart` non-1 pour
les alignements locaux (Foldseek) ; smoke test offline ajouté (`smoke_test.py`, sans réseau).
v1.2 (2026-08-10, `Rv3909` P2.1) : ajout de la section « route de substitution », qui couvre le cas
MAJORITAIRE où M-CSA ne connaît pas la cible — template porteur de ligand, site défini
géométriquement, verdict rendu contre un nul d'identité de fond, contrôle de numérotation
obligatoire dans le code. Le script Python reste inchangé (route M-CSA) ; la route de substitution
s'appuie sur l'implémentation de référence citée ci-dessus, à intégrer ici en v2 si elle resert.
Validé en conditions réelles : appliqué à Rv2492 contre M-CSA 31 (ThyA), a retrouvé exactement les
positions Cys151/Arg175/Asp178 déjà établies par superposition structurale indépendante, à partir
d'un simple alignement de séquence à 26 % d'identité. Reste à industrialiser : la réconciliation de
numérotation structure↔séquence pour un branchement proteome-wide automatique (phase2i), et
l'option d'un test SPATIAL (superposition 3D plutôt qu'alignement de séquence) pour les cas de
faible identité de séquence mais repli conservé.

v2 (2026-08-11, `annotation_mtbc` P16.2a-sexies-bis.6) : la route de substitution a resservi une
troisième fois (Rv3031, `annotation_mtbc/analyses/phase_deepdive10_active_site_rv3031.py`), toujours
selon le même patron ad hoc — d'où sa factorisation en module réutilisable, `substitution_route.py`,
à côté de `active_site_check.py` (route M-CSA, inchangée). Expose : `check_template_published`
(rejet RCSB « to be published »), `fetch_cif`, `define_site` (site géométrique par ancrage sur le
site publié — la règle qui évite le piège du glycérol de 3n98, cf. « limites » ci-dessus),
`run_foldseek`, `analyse_pair` + `analyse_site` (score de conservation contre le nul d'identité de
fond, positions du site exclues), `spatial_probe` (sonde par superposition pour les positions
gapées), `verdict` (seuils en paramètres, pas en constantes cachées). Les deux contrôles de
numérotation restent dans le code, pas dans la tête : `define_site` vérifie la structure contre la
publication, `analyse_pair` vérifie l'alignement Foldseek contre la séquence résolue de la
structure. **Non-régression validée** : rejoué sur Rv3031 vs template 3n98, `substitution_route.py`
reproduit EXACTEMENT le résultat publié de `phase_deepdive10_active_site_rv3031.py` (site
ligand-défini 16/18 p=3.01e-07, site publié 7/7 p=2.73e-04, dyade 2/2, même verdict). Ce que
`substitution_route.py` NE fournit PAS, par construction : les templates, le site publié, les
témoins positif/négatif/contexte et les seuils de verdict restent à la charge du script appelant —
ce sont des choix scientifiques citables, pas des valeurs par défaut de bibliothèque. Reste ouvert :
le test SPATIAL (superposition) est factorisé (`spatial_probe`) mais toujours pas branché en routine
proteome-wide (phase2i) faute de déclencheur systématique (quand une position du site publié tombe
en gap).
