---
name: bdd
description: Versionnage et journalisation de bases de donnees internes declarees dans un registre `bdd/registre.json` (par exemple un corpus principal, un corpus de barcodes, un atlas de genes/lignees, un second genre ou domaine suivi separement...). Sous-commandes `init/stamp/check/bump/log/diff/miroir/abonnes` via `bdd.py` ; bibliotheque d'ecriture `bdd_journal.py` pour les scripts qui modifient un store ; registre d'abonnes pour verifier a la demande que les projets consommateurs d'un store n'ont pas derive. Declencheurs — "quelle version de la base actuelle", "cite la source de ces donnees", "cette base a-t-elle derive", "journalise ce script d'ecriture", "qui consomme cette base, a-t-il derive", "bdd init/stamp/check/bump/abonnes", `/bdd`.
argument-hint: "init|stamp|check|bump|log|diff|miroir|abonnes <store> [options]"
---

# bdd — versionnage des bases internes

`bdd/registre.json` declare les stores (racine par defaut `~/docs/environnement/`,
surchargeable par la variable d'environnement `BDD_REGISTRE`). Ce skill (`bdd.py`,
`bdd_journal.py`, stdlib uniquement) leur donne une version citable, un journal
append-only des ecritures, et un `check` qui detecte la derive silencieuse.

## Quatre types de store

| type | unite versionnee | condensat |
|---|---|---|
| `arbre_souches` | arbre `<clade>/<SRA>/<ref>/{spdi.txt,report.json,...}` (ou plat, `plate: true`) | 6 hex **placement** (clade+SRA) + 6 hex **contenu** (SRA+tailles+mtimes, sans le clade — un `mv` ne doit changer QUE le placement) |
| `jeu_fichiers` | liste `fichiers` explicite du registre (pas un scan de repertoire) | sha256 des couples (chemin, sha256 contenu) |
| `fichier` | un seul fichier | sha256 du contenu |
| `git` | delegue a git : HEAD court + `## vNNN` du `changelog` declare, `+dirty` si `git status --porcelain` non vide sur le `sous_arbre` | pas de condensat propre, pas de `.bdd/`, pas de journal — `git log`/`git commit` font foi |

Format de version (sauf `git`) : `AAAA-MM-JJ-<Nc->-<Ms->-<12hex>` (arbre_souches),
`AAAA-MM-JJ-<Nf>-<12hex>` (jeu_fichiers), `AAAA-MM-JJ-<12hex>` (fichier). `git` :
`vNNN-gHEAD[+dirty]`. La revision ordinale `r<N>` (version.json, journal, manifestes)
est un compteur separe, jamais citee seule.

## `.bdd/<store_id>/` : jamais a l'interieur de la racine d'un `arbre_souches`

Un `.bdd/` sous la racine d'un store `arbre_souches` (ex. `bdd/mon-corpus/`)
deviendrait une entree fantome pour tout script qui enumere ce repertoire. Le
registre declare donc un `meta` explicite, hors de la racine, pour chaque store
`arbre_souches` reel (`bdd/.bdd/mon-corpus`, sibling de `bdd/mon-corpus`). A defaut
de `meta` dans le registre, `bdd.py` calcule un repli sur le
PARENT de la racine (jamais a l'interieur) pour `arbre_souches` et `fichier` ; pour
`jeu_fichiers`, le repli est a l'interieur de la racine (les fichiers suivis sont une
liste explicite, pas un scan — pas de risque de clade fantome). Contenu de `.bdd/` :
`version.json`, `journal.jsonl` (append-only), `manifests/r<N>.tsv.gz` (tous conserves),
`cache/sentinelle.json`.

## Commandes

```
bdd init <store> [--write] [--sans-coord]
bdd stamp <store> [--json] [--verifier]
bdd check <store> [--json] [--regulariser --motif M [--outil O] [--undo-log F] --write]
bdd bump <store> --outil O --motif M [--piste P] [--undo-log F | --sans-undo] [--sauvegarde S] --write
bdd log <store> [--json] [-n N]
bdd diff <store> r<A> [r<B>|actuel]
bdd miroir <store> [--commit]
bdd abonnes <store> [--json]
```

- **`init`** pose la revision `r0` (« etat constate le <date>, aucun historique
  revendique »). Dry-run par defaut (affiche ce qui serait ecrit) ; `--write` pour
  ecrire reellement. Indexe au passage les sauvegardes suffixees anterieures au skill
  (`.bak*`, `_*_undo_log.tsv`, `*.avant_*`...) dans l'entree journal `anterieures`, sans
  y toucher. Refuse si le store est deja initialise (utiliser `bump`).
- **`stamp`** ne scanne jamais (lit `version.json` + une sentinelle ~2 ms : mtime
  racine, nombre d'entrees de premier niveau, sha de leurs (nom, mtime)) : citation en
  moins de 100 ms. `+dirty` si la sentinelle a bouge depuis le dernier `bump`/`init`/
  `check`. `--verifier` force un `check` complet avant de repondre.
- **`check`** rescanne et compare au manifeste de la derniere revision : À JOUR, ou
  DÉRIVÉ avec le detail (ajouts, suppressions, deplacements groupes `clade -> clade
  (n)`, modifies, doublons, clades crees/supprimes, variation des vides), et
  `journalise ?` (une entree de journal posterieure a la derniere ecriture explique-t-
  elle la derive, meme un `ecriture_interrompue`, ou est-elle totalement silencieuse ?).
  `--regulariser --write` cree une revision `regularisation` (`attribution.presumee:
  true`) sans pretendre reconstituer un historique qui n'existe pas.
- **`bump`** refuse un delta vide (code **3**, idempotent : rejouer un bump sans
  changement ne fait rien). Sur `arbre_souches`, exige `--undo-log <fichier>` (sauf
  `--sans-undo` explicite) : un bump sans trace de defaisabilite sur un arbre de
  plusieurs dizaines de milliers d'entrees serait une regression, pas une amelioration.
- **`log`/`diff`** lisent journal et manifestes ; `diff <store> r5 actuel` rescanne pour
  comparer a l'etat live (pas sous coordination — reserver aux petits stores ou le
  combiner a `check`, qui l'est).
- **`miroir`** recopie `version.json`+`journal.jsonl` (jamais les manifestes, trop
  volumineux) vers `~/docs/environnement/bdd/journaux/<store>/`, appele automatiquement
  par `init`/`bump`/`check --regulariser`. `--commit` en plus un `git commit` explicite
  dans le depot `environnement` — jamais automatique sans ce flag.
- **`abonnes`** audite a la demande les projets consommateurs declares dans le champ
  `abonnes` d'un store du registre (`{"projet", "racine", ...}`) : pour chacun, lit sa
  derniere citation `**Donnees :**`/`donnees :` (etat des decouvertes ou cahier de labo,
  meme logique que le hook `session_donnees.py`) et la compare a la version reference du
  store. Trois verdicts par abonne — A JOUR, DERIVE (avec le nombre d'ecritures
  journalisees depuis), ou AUCUNE CITATION (le projet ne cite jamais ce store : le garde-
  fou passif du hook SessionStart lui est structurellement aveugle). Code de sortie non
  nul si au moins un abonne est en anomalie. `bump` rappelle automatiquement, apres un
  bump reussi, le nombre d'abonnes declares pour le store bumpe et la commande a lancer.

## Registre d'abonnes : pourquoi

Le hook SessionStart (§ Integration lecture ci-dessous) n'alerte sur une derive que si le
PROJET CONSOMMATEUR cite lui-meme le store dans son etat ou son cahier — mecanisme TIRE,
passif. Un projet qui fige une copie d'un store (ex. un export `.tsv` gele a une date)
sans jamais ecrire cette citation reste invisible : c'est ce type de situation, vecu au
moins une fois avec un desalignement de plusieurs centaines d'entrees passe inapercu
plusieurs semaines cote d'un projet consommateur, qui motive ce registre. Le registre
`abonnes` et la commande `bdd abonnes` renversent la charge : la SOURCE (le store) connait
ses consommateurs declares et peut etre interrogee a tout moment pour savoir qui a derive,
sans dependre de la discipline de citation du consommateur. Declarer un abonnement :
ajouter `{"projet": ..., "racine": ..., "artefact": ..., "declare": "AAAA-MM-JJ
(motif)"}` a la liste `abonnes` du store concerne dans le registre, puis cabler le script
qui fige la copie pour qu'il imprime `bdd_journal.stamp(<store>)` a chaque regeneration et
rappeler a l'operateur de reporter cette ligne dans le cahier du projet consommateur.

Types de store : `git` repond seulement a `stamp` (les autres verbes rendent un message
de delegation, code 0, rien a faire cote skill). Un store `arbre_souches` declare mais pas
encore peuple (`"etat": "à créer"` dans le registre) repond `@non-versionnee` a `stamp`,
rien d'autre.

## Coordination ressources partagees (`agentctl`/`runsafe`)

Un scan estime a 50 000 entrees ou plus (heuristique : compte de la derniere version
connue, ou echantillonnage d'un clade au tout premier `init`) passe automatiquement
sous `runsafe --cpu 4 --ram-gb 2` (re-execution du CLI dans un cgroup, garde interne
`--interne-runsafe` contre la recursion) et sous `agentctl task start/done`. Le garde-
fou de charge partagee peut refuser (machine chargee) : relancer plus tard, ou
`--sans-coord` en connaissance de cause (obligatoire dans les tests — fixtures toujours
petites, et on ne veut pas qu'un test invoque des binaires systeme). Absence
d'`agentctl`/`runsafe` sur la machine (ex. `mp`) : dégrade proprement, avertissement sur
stderr, scan lance quand meme.

## Bibliotheque d'ecriture : `bdd_journal.py`

Import par chemin fixe au sein du plugin (`${CLAUDE_PLUGIN_ROOT}/skills/bdd/bdd_journal.py`
depuis un script d'un autre skill du meme plugin ; chemin relatif au propre repertoire du
skill depuis un script sous `bdd/`), avec degradation silencieuse si le module est
introuvable — `stamp()` rend alors `store@non-versionnee`, `ecriture()` devient un context
manager transparent (aucun journal, aucun refus de derive) :

```python
import importlib.util, os, sys
from pathlib import Path
_racine = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", Path(__file__).resolve().parents[2]))
_chemin = _racine / "skills" / "bdd" / "bdd_journal.py"
if _chemin.is_file():
    _spec = importlib.util.spec_from_file_location("bdd_journal", _chemin)
    bdd_journal = importlib.util.module_from_spec(_spec)
    sys.modules["bdd_journal"] = bdd_journal
    _spec.loader.exec_module(bdd_journal)
else:
    bdd_journal = None

with bdd_journal.ecriture("mon-corpus-principal", outil=__file__,
                            motif="flatten sous-groupe A -> A.3",
                            piste="P42.3", undo_log=str(chemin_undo_log)) if bdd_journal else nullcontext():
    deplacer_les_fichiers()
```

A l'entree : sentinelle + refus (`ErreurDerive`) si le store est `+dirty` depuis le
dernier `bump` (sauf `malgre_derive=True`, explicite). A la sortie normale : rescan,
delta, bump si non vide, entree de journal, miroir. Sur exception : entree
`ecriture_interrompue`, jamais de bump — le store reste `+dirty`, honnetement.
`bdd_journal.stamp(store_id)` / `stamp_json(store_id)` pour une citation a coller dans
un en-tete de sortie (`# donnees : mon-corpus-principal@... ; mon-corpus-barcodes@...`).

## Integration lecture

Points d'integration lecture, a cabler sur ce modele (import differe, degradation
silencieuse a `<store>@non-versionnee`) :
- un script d'exploration de vos donnees : `stamp()` / `stamp_json()`.
- un pont de requetage vers une base externe : ligne `# donnees : ...` en sortie texte,
  cle `donnees` en sortie JSON (toutes sous-commandes).
- un outil de synthese qui agrege plusieurs stores (ex. corpus principal + corpus de
  barcodes) : cite `<store-1>@...` et `<store-2>@...` dans son en-tete de sortie.
- un outil qui interroge une API distante : cite le store local qui fait autorite derriere
  cette API, que l'API elle-meme ne dit pas (`<store>@v...-g...`).
- un fichier de conventions de type `SOURCES_OF_TRUTH.md` : une section « comment citer ».
- skill `cahier-de-labo` (ligne `donnees :` obligatoire sous `piste :`), skill `etat`
  et gabarit `init_project.py` (ligne `**Donnees :**` de l'en-tete).
- hook `SessionStart` (`session_context.sh`) : bloc `[DONNÉES — ...]` via
  `session_donnees.py <racine_projet>`, silencieux sauf derive detectee entre la
  derniere citation du projet (etat ou cahier) et l'etat courant du store.

## Wrappers d'ecriture

Illustration vecue (nombre et scripts exacts propres a l'instance d'origine, pas repris
ici) : une poignee de scripts d'un meme ecosysteme enveloppes par `bdd_journal.ecriture()`
(transparent en dry-run et si le module est absent) — des scripts de deplacement/fusion de
donnees, des scripts d'import depuis une source externe (store resolu a l'execution via
`store_for_path()` quand la destination est un parametre libre), des scripts de synthese
qui CITENT un store en LECTURE sans le faire entrer dans la cle de comparaison de
`--check` (a documenter explicitement en commentaire pour eviter qu'un futur changement de
`--check` ne casse silencieusement cette lecture).

Deux fonctions ajoutees a `bdd_journal.py` pour ces wrappers : `meta_dir(store_id)` (chemin
`.bdd/<store>` resolu, pour deposer une sauvegarde AVANT overwrite plutot qu'a cote du fichier
suivi) et `store_for_path(chemin)` (quel store contient un chemin donne, ou `None`).

## Ce que ce skill NE fait PAS

Un store declare peut tres bien n'avoir encore ni wrapper d'ecriture ni premier `init` :
c'est un etat transitoire normal, pas une erreur du skill. Un script d'import qui ecrit sur
une machine distante par SSH reste volontairement hors journal : le scan de `check` reste
LOCAL uniquement. Un script qui n'a
pas encore son wrapper reste invisible au journal — c'est attendu, pas un bug de ce skill.
