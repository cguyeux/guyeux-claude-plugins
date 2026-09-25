---
name: reboot
description: Reprise d'un projet de recherche interrompu, quand l'environnement (cycle, cinq artefacts, skills, hooks, données) a changé depuis la dernière séance et qu'on ne sait plus ce qui, dans l'acquis du projet, tient encore. Rend un verdict mesuré HARD / SOFT / AUCUN, puis conduit soit une simple migration d'environnement, soit une refondation complète où tout l'acquis legacy transite par `affirmations.md` et n'est réinscrit à l'état qu'une fois re-prouvé. Déclencheurs — « je reprends ce projet », « ça date de plusieurs mois », « où en étais-je », « est-ce que ces chiffres tiennent encore », « le projet est périmé », « il faut repartir de zéro », « l'environnement a changé depuis », « diagnostic de reprise », un bandeau SQUELETTE NON RENSEIGNÉ, un état dont les données citées ont dérivé, `/reboot`.
argument-hint: "[diagnostic | soft | hard | status | affirmations | affirmation <id> | recycler <chemin> | lire-archive [fichier] | clore | annuler <date>]"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# reboot — Reprendre un projet que le temps a décalé

Un projet de recherche ne périme pas parce qu'il est faux. Il périme parce que
**le monde autour de lui a bougé** : la taxonomie a été repensée, la base de
souches a été re-rangée, les conventions d'écriture ont changé, le cycle est
passé de trois artefacts à cinq, des skills ont disparu et d'autres sont
apparus. Six mois plus tard, le `CLAUDE.md` du projet décrit une structure qui
n'existe plus, l'état des découvertes affirme des chiffres calculés sur une
version de la base que personne ne sait plus nommer, et le manuscrit cite des
clades qui ont changé de nom. Rien n'est signalé : tout a l'air normal.

C'est le mode d'échec que ce skill existe pour empêcher — **reprendre un
travail périmé en croyant reprendre un travail acquis**. Sa règle centrale est
une seule phrase : *aucune affirmation héritée n'est un acquis tant qu'elle
n'a pas été re-prouvée dans l'environnement courant, avec les données
courantes.*

Le skill est **générique** et sans biologie : il vaut pour un projet de
phylogénomique comme pour un projet de droit, d'IA ou de pompiers. Il remplace,
dans l'environnement d'origine, un skill antérieur spécifique à un seul domaine,
non scripté et bâti sur un modèle à trois artefacts plus pauvre.

## Le script fait les mesures, l'assistant fait les jugements

Tout ce qui est mesurable est mesuré par `reboot.py` (stdlib, aucun réseau,
aucun MCP) :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/reboot/reboot.py <sous-commande> [<projet>] [options]
```

Sans argument de projet, la racine est localisée en remontant depuis le
répertoire courant (5 niveaux au plus) jusqu'au premier répertoire portant
`cahier_de_labo.md`, exactement comme le skill `pistes`.

**Toutes les sous-commandes qui écrivent sont en dry-run par défaut** et ne
touchent rien tant que `--apply` n'est pas passé. Un dry-run répété laisse
l'empreinte du répertoire strictement identique : c'est vérifié par
`tests/test_reboot.py` dans le projet `environnement`.

| sous-commande | écrit | rôle |
|---|---|---|
| `diagnostic [--json]` | non | mesures et verdict `HARD` / `SOFT` / `AUCUN`, motifs, réserves |
| `status [--legacy] [--json]` | non | état dérivé du reboot en cours ; `--legacy` lit les vestiges de `mtbc-reboot` |
| `signals [--quiet]` | non | bloc `[REBOOT]` / `[AFFIRMATIONS]` pour `session_context.sh` |
| `affirmations [--ecrire F] [--pistes-ecrire F] [--json]` | sur option | dérive `affirmations.md` et le `pistes.md` de reboot ; prévisualise sans les options |
| `affirmation <id> --statut … --preuve … [--apply]` | oui | tranche une affirmation, recompte, ferme sa sous-piste `P1.k` |
| `hard [--apply] [--garder-article] [--commit-article] [--kb-renvoi] [--suffixe S]` | oui | archive complète et refondation |
| `soft [--apply]` | oui | piste de migration d'environnement, sans aucune archive |
| `recycler <chemin> [--vers D] [--verdict …] [--lien] [--apply]` | oui | instruit puis statue sur un artefact legacy |
| `lire-archive [fichier] [--grep MOTIF] [--json]` | non | lecture à la demande de l'archive |
| `clore [--apply]` | oui | gèle `affirmations.md`, allège le bloc Reboot du `CLAUDE.md` |
| `annuler <date> [--suffixe S] [--apply]` | oui | rejoue le `MANIFEST.json` d'un `hard` à l'envers |

Ce que le script ne fera **jamais**, et qui reste le travail de l'assistant :
lire un artefact legacy en entier, juger qu'un énoncé est prouvé, trancher un
doublon douteux, décider d'un recadrage, écrire l'entrée de cahier de la
séance. Le script mesure, propose et exécute ; il ne conclut pas.

## Étape 1 — toujours `diagnostic`, jamais le verdict au flair

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/reboot/reboot.py diagnostic
```

Mesures relevées : version d'environnement du projet (ligne
`**Environnement :**` de l'état ; absente signifie « antérieur au
versionnage »), version courante et delta de conséquence, âge du cahier
(dernière entrée `## AAAA-MM-JJ`), âge de l'état (`**Réécrit le :**`), dérive
des données (`bdd check` sur chaque citation `<store>@<version>` trouvée dans
l'état et les tables de vérification), phase déclarée et observée
(`cycle_status.py`), statut de répertoire, bandeau « SQUELETTE NON RENSEIGNÉ »,
recouvrement avec les projets voisins (`carrefour.py overlap`). Lorsque le
versionnage d'environnement ou de bases n'est pas déployé, le repli est annoncé
dans la sortie plutôt que silencieux.

Les règles s'appliquent dans l'ordre, la première qui mord l'emporte :

| n° | condition | verdict |
|---|---|---|
| 1 | projet sous `clos_*/` | `AUCUN` — le ramener en `en_cours/` par `deplacer_projet.py` avant tout reboot |
| 2 | cahier < 30 j **et** état < 30 j **et** delta au plus `soft` | `AUCUN` (conseil : poser `**Environnement :**` s'il manque) |
| 3 | delta MAJEUR, **ou** estampille absente avec cahier ≥ 90 j, **ou** squelette non renseigné sur un cahier ≥ 5 entrées, **ou** dérive de données en phase ≤ 3 | `HARD` |
| 4 | delta MINEUR, **ou** estampille absente avec cahier entre 30 et 90 j, **ou** dérive de données en phase ≥ 4 | `SOFT` |
| 5 | sinon | `AUCUN` |

Les réserves sont affichées à part du verdict, parce qu'elles n'en changent
pas la nature mais la conduite : manuscrit mûr (`main_fr.tex`, répertoire de
soumission) qui appelle `hard --garder-article` ; `article/` porteur de
modifications non committées ; projet hors format `init-project`.

Un verdict est une mesure, pas un ordre. Si le diagnostic dit `HARD` et que
vous jugez le contraire, le désaccord se tranche avec CG et se consigne — les
seuils (30 j, 90 j, 5 entrées) sont posés à dire d'expert et attendent d'être
recalibrés sur l'inventaire réel des projets.

## Étape 2a — `soft`, quand seul l'environnement a bougé

Le projet est vivant, son acquis tient, mais il a été fait sous des règles plus
anciennes. Rien n'est archivé : `soft --apply` ouvre une piste majeure
« Migration d'environnement vA→vB » avec ses cinq sous-pistes (article,
données à re-citer, scripts à re-valider, registres à estampiller, en-tête de
l'état), réécrit la ligne `**Environnement :**`, ajoute trois lignes au
`CLAUDE.md` et pose des renvois de péremption en tête des registres. Détail,
garde-fous et limites : `references/migration_soft.md`.

## Étape 2b — `hard`, dans cet ordre et pas un autre

`hard` est la seule opération lourde du skill. **L'ordre est imposé**, et il
l'est pour une raison mesurable : un recadrage a besoin de l'état riche et de
l'index `carrefour` encore en place, donc il se fait **avant** l'archivage, pas
après.

1. `diagnostic` — obtenir et lire le verdict.
2. `/recadrage` complet sur les artefacts legacy, **avant** d'archiver quoi que
   ce soit. Sa sortie est déposée dans `archives/<date>_reboot/RECADRAGE.md`.
   Les verdicts qui engagent deux projets (transférer, fusionner, redécouper)
   deviennent des sous-pistes `P2.k [DÉCISION CG]` et ne sont **jamais**
   exécutés d'office. Ce recadrage juge l'acquis legacy **avant** qu'il soit
   re-prouvé : il ne remplace pas celui qui suit la clôture (étape 4).
3. Si vous travaillez avec plusieurs sessions en parallèle sur cette machine et
   disposez d'un outil de coordination (ex. `agentctl status`), vérifier
   qu'aucune autre session n'a pour répertoire courant un dossier sur le point
   d'être renommé.
4. `hard` en dry-run, lecture intégrale du plan d'action proposé.
5. `hard --apply`, puis `carrefour.py reindex`.
6. Entrée de cahier de la séance, écrite par l'assistant dans le **nouveau**
   cahier (le stub posé par le script ne compte pas pour le hook `Stop`).

Ce que `hard` déplace, et ce qu'il laisse en place :

| artefact | sort en `hard` |
|---|---|
| les cinq artefacts, `.claude/`, `litterature_review/`, `archives/`, `.gitignore`, `README.md` | liste blanche : conservés ou recréés |
| cahier, état, pistes (et `pistes/`, archives, `.bak_*`) | déplacés verbatim dans l'archive, artefacts neufs posés depuis les gabarits d'`init-project` |
| `analyses/`, `résultats/`, `experiments/`, `data/`, `bilans/`, vrac de racine | déplacés (le vrac sous `racine_legacy/`), répertoires neufs recréés |
| `claim_check.md`, `fig_check.md`, `plan_narratif.md`, `verdict_diffusion.md`, `DERNIERE_SESSION.md`… | déplacés après extraction vers `affirmations.md` |
| `article/` | `git status --porcelain` puis tag `avant-reboot-<date>`, dépôt entier déplacé, nouveau dépôt neuf ; `--garder-article` le gèle sur place avec un bandeau au lieu de le remplacer |
| mémoire native du projet | copiée sous l'archive, originaux à la corbeille, lignes d'index retirées ; les mémoires `feedback_*`, `user_*`, `reference_*` ne sont jamais touchées |
| entrées de KB citant le projet | **jamais retirées** — inventaire seul, et renvoi de péremption sur `--kb-renvoi` |

Le second `--apply` du même jour est refusé sans `--suffixe`, chaque archive
porte un `MANIFEST.json`, et `annuler <date> --apply` restaure l'arborescence.
Deux effets annexes ne sont pas repris par `annuler`, volontairement :
`.claude/settings.json` (recalculé par `profil_plugins.py`) et `.carrefour/`.

## Étape 3 — rétablir l'acquis, une affirmation à la fois

L'archive est **en lecture seule** : rien ne s'y exécute, rien ne s'y importe.
Tout ce qui doit revivre passe par deux artefacts transitoires, et par eux
seuls : `affirmations.md` pour le savoir, `RECYCLAGE.md` pour les outils et les
figures.

`affirmations` dérive une ligne par énoncé hérité (état §2/§3/§4, tables de
vérification, registre d'ancien reboot), dédoublonne, et engendre le nouveau
`pistes.md` de reboot (P1 rétablissement, P2 recadrage, P3 recyclage, P4 pistes
legacy, P5 manuscrit). Chaque énoncé prouvé remonte ensuite à l'état par
`/etat update`, chaque énoncé réfuté au §3. Tant qu'une affirmation P1 n'est
pas tranchée, la rédaction est bloquée : c'est une condition **nécessaire** de
la porte 1, jamais sa levée (voir étape 4). Détail complet :
`references/affirmations.md`. Recyclage d'un script, d'une figure ou d'un jeu
de résultats legacy : `references/recyclage.md`.

Quand plus aucune affirmation n'est en attente, `clore --apply` gèle
`affirmations.md` dans l'archive et réduit le bloc `## Reboot` du `CLAUDE.md` à
la ligne de clôture plus la trace de la porte 1 rouverte. Le projet a fini de
renaître ; il redevient un projet ordinaire **en phase 1, porte 1 ouverte**,
quelle qu'ait été sa phase avant le reboot.

## Étape 4 — après `clore` : la porte 1 est rouverte, jamais franchie

**Règle (décision CG, 2026-09-25, cas La4) : la clôture d'un reboot HARD ne
vaut ni franchissement de la porte 1 ni décision de porte 1bis ou 3bis, même
si la porte 1 avait été franchie avant le reboot.** Elle la rouvre. Ni P1 soldé,
ni P3/P4 soldés, ni `clore --apply` n'autorisent à dégeler le manuscrit (P5).

Pourquoi : un reboot hard peut infirmer ce qui est déjà écrit et faire émerger
de l'inédit. Or le seul recadrage que prévoit l'étape 2b porte sur les
artefacts **legacy**, avant l'archivage, donc avant qu'aucune affirmation soit
tranchée ; la revue de littérature du projet, elle, date d'avant les acquis
nouveaux. Traiter la clôture comme un point fixe, c'est rédiger ou soumettre
sur un cadrage jamais réinterrogé et une littérature jamais recroisée avec ce
que le reboot a changé.

Ce qui suit `clore`, dans cet ordre :

1. **`/recadrage` sur l'état post-reboot** : les affirmations réfutées (ce que
   le manuscrit legacy affirmait à tort), les acquis nouveaux apparus pendant le
   reboot (P4 notamment), et les prouvées dont le poids a changé. La question
   posée est celle du message : tient-il encore, a-t-il changé, le projet
   déborde-t-il ? Verdicts qui engagent deux projets : `[DÉCISION CG]`, comme en
   2b.
2. **`/lit-review` ciblée**, toujours, même si le recadrage ne change pas le
   message : les mots-clés viennent du cadrage issu de 1 et des acquis nouveaux,
   et chaque résultat que le futur manuscrit revendiquerait est recroisé avec ce
   qui a paru depuis la revue legacy (antériorité, contradiction, données
   nouvelles). La conditionner à un recadrage qui « élargit » est l'erreur à
   éviter : une revue faite avant le reboot est périmée par construction.
3. **Porte 1 ordinaire**, selon `cycle-projet` : les pistes que 1 et 2 ouvrent
   se traitent en phase 1, et la porte se re-prouve sur ses trois conditions et
   ses deux tours à vide. Le recadrage et la revue post-clôture en sont le
   premier tour, pas le dernier.
4. **Porte 1bis re-rendue** (`/verdict-diffusion amont`) avant tout dégel du
   manuscrit. Tout verdict 1bis ou 3bis antérieur à la clôture est périmé ; un
   manuscrit conservé par `--garder-article` reste gelé jusque-là, et repasse
   ensuite la phase 3 puis la 3bis avant toute soumission.

**Trace.** `clore --apply` écrit dans le bloc `## Reboot` du `CLAUDE.md` deux
lignes « à faire », une pour le recadrage post-clôture et une pour la revue
ciblée. L'assistant remplace chaque « à faire » par « fait le AAAA-MM-JJ » suivi
du titre de l'entrée de cahier qui le porte, et par rien d'autre. Ces lignes
sont lues à chaque session (le `CLAUDE.md` est chargé) et servent de preuve à
`/cycle-projet gate`. Un projet clos avant cette règle n'a pas ces lignes :
les ajouter à la main, datées des passes réellement faites.

> **Cas La4 (2026-09-24/25).** Reboot `2026-09-22_reboot` clos le 2026-09-24,
> P3 et P4.3 soldés le même jour ; le bilan de séance recommande alors de
> dégeler P5. Or P4.3 venait de renverser les trois piliers du volet ESX-2 du
> manuscrit legacy et de produire neuf acquis nouveaux (A82-A90), **après** le
> seul recadrage post-reboot (P2, 2026-09-23). Le recadrage post-clôture (P7.1)
> a rendu RECADRER : le message central de l'article a changé, donc son titre,
> son résumé et l'ordre de sa démonstration. La revue ciblée (P7.2) a trouvé
> deux publications 2025-2026 appuyant le nouveau message et deux souches
> candidates jamais testées, ouvertes en P8. Dégeler au 2026-09-24, c'était
> réécrire l'ancien article sur un cadrage déjà faux.

## Garde-fous, tous nés d'un incident

- **Jamais `rm`.** Le skill procède par renommages, et met à la corbeille par
  `gio trash` quand il doit retirer quelque chose. C'est la règle absolue de
  cet environnement, pas une précaution locale.
- **`résultats/` porte un accent.** La lecture tolère `resultats/`, l'écriture
  ne crée jamais la forme sans accent : un ancien skill globbait la mauvaise
  et passait à côté de tout le répertoire.
- **Aucune piste n'est supprimée.** Le registre legacy entier part à l'archive
  et les pistes restées ouvertes réapparaissent sous `P4` avec leur
  identifiant d'origine.
- **La KB partagée n'est jamais amputée.** `mtbc-reboot` en retirait des
  entrées ; le nouveau skill les inventorie et, sur demande explicite, les
  estampille d'un renvoi de péremption. Une entrée de KB vaut pour d'autres
  projets que celui qu'on reboote.
- **Rien ne s'exécute depuis une archive.** Un script legacy tourne encore très
  bien et rend un résultat d'apparence fraîche calculé sur des chemins, des
  données et des conventions périmés. Un rappel de hook se déclenche sur
  l'exécution d'un fichier d'archive.
- **Vérifier les sessions concurrentes avant `--apply`, si vous en avez.** Si
  plusieurs sessions travaillent en parallèle sur cette machine, renommer le
  répertoire courant de l'une d'elles la casse silencieusement.

## Vestiges des anciens reboots

Six projets portent déjà un `archives/<date>_reboot/` et un
`reanalysis_registry.md` produits par `mtbc-reboot`, et certains un
`reboot_state.md`. `status --legacy` les lit sans rien y écrire. Ne pas les
convertir : ils sont datés, ils valent comme trace historique, et le nouveau
cycle repart d'un diagnostic neuf.

## Consignation

Une séance de reboot se clôt comme toute séance productive : entrée datée dans
le cahier du projet (écrite par l'assistant, pas par le script), pistes mises à
jour, et — si le reboot a révélé un enseignement transférable — `/reflect` vers
la base de connaissances. La fiche de doctrine de ce dispositif est
`~/.agents/knowledge/reboot.md`.

## Erreurs à éviter

- Lancer `hard --apply` sans avoir lu le dry-run en entier.
- Archiver avant d'avoir recadré : le recadrage a besoin de l'état riche.
- Lire `clore` (ou P1 soldé) comme la levée de la porte 1, et proposer de
  dégeler le manuscrit dans la foulée. La clôture rouvre la porte 1 : recadrage
  post-clôture, revue ciblée, porte 1 re-prouvée, puis 1bis (étape 4).
- Recopier un énoncé legacy dans l'état sans l'avoir prouvé, au motif qu'il
  était déjà écrit quelque part. C'est exactement ce que le skill empêche.
- Exécuter ou importer un script depuis l'archive.
- Traiter `affirmations.md` comme un sixième artefact permanent : il est
  transitoire, il naît de l'archive et se vide dans l'état.
- Rebooter un projet sous `clos_*/` : le ramener d'abord en `en_cours/`.
- Fermer une affirmation « prouvée » sans citer la preuve (chemin d'expérience
  rejouée, ou transfert depuis un projet voisin qui l'a établie).
