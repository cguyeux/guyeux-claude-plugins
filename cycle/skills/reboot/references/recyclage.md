# Recyclage contrôlé des artefacts legacy

## Pourquoi une archive de reboot est en lecture seule

`hard --apply` déplace tout ce qui n'est pas retenu dans la liste blanche
(cahier, état, pistes, `article/`, `analyses/`, `résultats/`, `experiments/`,
`data/`, `bilans/`, le vrac de racine) vers `archives/<date>_reboot/`. Ce
déplacement n'est pas un simple rangement : c'est une mise sous scellés
délibérée. La doctrine, répétée dans le bloc `## Reboot` du `CLAUDE.md`
réécrit, dans le rappel `precompute_reminder.sh` et dans le `SKILL.md`, tient
en une phrase : rien ne s'exécute et rien ne s'importe depuis une archive de
reboot.

La raison n'est pas administrative. Un script legacy qui tourne encore
produit un résultat d'apparence fraîche — une figure qui s'ouvre, un tableau
qui se remplit, un modèle qui s'entraîne sans erreur — à partir de chemins,
de données et de conventions qui ont pu diverger de tout ce qui existe
aujourd'hui : un store de données qui a été réorganisé depuis, un corpus dont
les fichiers ont changé de schéma, une fonction utilitaire dont la signature
ou la sémantique a évolué. Rien dans
l'exécution elle-même ne signale cette dérive — le script ne plante pas, il
répond, avec des nombres qui n'ont plus le même sens que ceux qu'il
produisait au moment où le projet a été mis en pause. C'est précisément ce
mode d'échec — un résultat qui a toutes les apparences de la fraîcheur mais
qui repose sur un substrat périmé — que le dispositif de recyclage existe
pour empêcher, en forçant un chemin de sortie explicite (contrôle, lecture,
réexécution témoin **hors** archive) avant qu'un script ou un jeu de données
legacy ne redevienne actif.

C'est aussi pour cela que `hard` ne supprime jamais rien : l'archive
conserve l'intégralité du projet interrompu, disponible en lecture
(`lire-archive`) à tout moment, mais chaque remise en circulation passe par
une porte unique, `recycler`, qui trace ce qui a été vérifié et ce qui ne
l'a pas été.

## `RECYCLAGE.md`

Un fichier par archive, à `archives/<date>_reboot/RECYCLAGE.md`, créé au
premier appel de `recycler` sur cette archive (pas par `hard` lui-même — une
archive fraîchement créée n'a pas encore de `RECYCLAGE.md` tant qu'aucun
recyclage n'a été demandé). Table à onze colonnes :

| colonne | ce qu'elle porte |
|---|---|
| `chemin legacy` | chemin relatif du fichier dans l'archive, calculé depuis la racine de l'archive elle-même (pas depuis le projet) |
| `type` | déduit de l'extension : `répertoire`, `script` (`.py .r .sh .pl`), `doc` (`.md .tex .txt .rst`), `données` (`.csv .tsv .json .xlsx .parquet .tab`), `figure` (`.png .pdf .svg .jpg .jpeg`), `autre` sinon |
| `demandé le` | date du premier appel de `recycler` sur ce chemin ; conservée telle quelle aux appels suivants |
| `lecture intégrale (déclarée)` | voir plus bas — **ne prouve pas** qu'une lecture a eu lieu ; le nom de colonne le dit désormais lui-même (correctif AB8c, 2026-09-22 — l'ancien nom « lecture intégrale » laissait croire à une vérification) |
| `bugs KB` | liste des `mcp__…` cités dans le fichier |
| `chemins en dur` | chemins absolus détectés (voir contrôles mécaniques) |
| `données citées vs courantes` | **toujours** `non vérifié automatiquement` — aucune fonction ne calcule cette colonne, quel que soit l'état d'avancement du recyclage (voir plus bas) |
| `réexécution témoin (déclarée)` | même mécanique que « lecture intégrale (déclarée) » — un texte d'apparence de statut, pas une preuve |
| `verdict` | `recyclé`, `réécrit` ou `rejeté`, ou `—` tant qu'aucun `--verdict` n'a été passé |
| `destination` | le `--vers` fourni, ou `—` |
| `affirmation` | identifiant `A<k>` à relier à `affirmations.md` — **jamais rempli automatiquement**, colonne à servir à la main s'il y a un rapprochement à tracer |

Une ligne par chemin recyclé, identifiée par le chemin relatif : un second
appel `recycler` sur le même chemin **met à jour** la ligne existante plutôt
que d'en créer une seconde (recherche par égalité exacte de `chemin
legacy`), en conservant la date de première demande.

**Piège de dialecte, déjà rencontré et corrigé (AB4).** Le format d'écriture
et le format de lecture de cette table ont un temps divergé : l'écriture
produisait un en-tête sans barre verticale de tête tandis que la lecture
(`_lire_table_recyclage`) attendait deux lignes déjà pipées avant les
données, ce qui aurait décalé la première ligne réelle hors de la table dès
le deuxième appel. Le code actuel est cohérent (l'en-tête et la ligne de
séparation sont toutes deux préfixées `|`, et la lecture saute exactement
ces deux lignes), mais c'est le genre de rupture silencieuse — pas
d'erreur, juste une ligne de données interprétée comme une ligne d'en-tête
ou l'inverse — qui justifie de relire `RECYCLAGE.md` après chaque appel
plutôt que de faire confiance à l'idempotence du format sans vérification.

## Ce que `recycler <chemin>` contrôle mécaniquement

Liste exacte, lue dans `_controles_mecaniques` :

- **chemins absolus suspects** : toute occurrence commençant par `/home/`,
  `/Users/`, `/mnt/`, `/data/`, `/tmp/` ou `/srv/`, hors lignes shebang
  (`#!/usr/bin/env python3` n'est jamais compté). Le motif capture tout ce
  qui suit jusqu'au premier espace ou séparateur de ponctuation — il détecte
  un chemin en dur, pas une variable qui le contiendrait dynamiquement.
- **motifs mécaniques** : présence littérale, comme sous-chaîne, des signatures
  déclarées par le projet via `CYCLE_MOTIFS_MECANIQUES` (liste vide par
  défaut : ce contrôle est spécifique aux conventions de nommage de vos
  propres stores de données, à déclarer projet par projet, jamais imposées
  par le skill).
- **outils MCP cités** : tout token `mcp__…` trouvé dans le fichier, à
  vérifier vivant (un outil MCP legacy peut avoir disparu ou changé de nom
  depuis).
- **date d'en-tête vs date de l'archive** : si les 40 premières lignes du
  fichier contiennent une date ISO et que l'archive porte elle-même une date
  dans son nom (`<date>_reboot`), un écart entre les deux est signalé — sans
  jugement sur ce que cet écart signifie, seulement son existence.
- **script producteur de figure** : détection de `savefig(`, `ggsave(` ou
  `plt.show(` dans le texte, pour repérer les scripts qui régénèrent une
  image plutôt que ceux qui analysent seulement.

Ces contrôles ne portent que sur des fichiers, jamais sur des répertoires
(`_controles_mecaniques` rend un résultat vide pour tout chemin qui est un
répertoire) — recycler un répertoire entier ne déclenche aucun de ces
contrôles, seulement la mécanique de ligne et de copie.

**Ce que la commande laisse entièrement au jugement humain**, malgré des
libellés de colonne qui pourraient laisser croire à une vérification
automatique — et corrigés en ce sens le 2026-09-22 (AB8c : le suffixe
« (déclarée) » porte désormais cet avertissement dans le nom de colonne
lui-même, pas seulement dans cette référence) :

- **« lecture intégrale (déclarée) »** et **« réexécution témoin (déclarée) »**
  ne portent jamais autre chose que deux valeurs possibles, dérivées de la
  seule présence ou absence de `--verdict` dans l'appel : `déclarée (verdict
  posé)` si un verdict a été fourni, `non déclarée` sinon. Le script ne lit
  jamais le fichier pour juger de son contenu, et ne réexécute jamais rien
  lui-même : ces deux colonnes sont un **rappel de discipline**, pas un
  compte-rendu de travail réellement effectué. Poser `--verdict` sans avoir
  réellement lu le fichier ni réexécuté quoi que ce soit produit exactement la
  même ligne que si ces deux étapes avaient eu lieu — la colonne fait
  confiance à qui l'invoque, elle ne la vérifie pas.
- **« données citées vs courantes »** est, sans aucune exception dans le
  code actuel, la chaîne fixe `non vérifié automatiquement`. Aucune fonction
  de `reboot.py` ne compare les stores cités par un script legacy à l'état
  courant de `bdd/registre.json` au moment du recyclage — c'est une
  différence explicite avec `affirmations.md`, dont le frontmatter porte
  bien `donnees_legacy`/`donnees_courantes` calculés par `citations_stores`
  et `bdd check`. Sur `recycler`, ce rapprochement reste un jugement humain
  entier : relire le script, identifier les stores qu'il cite, lancer `bdd
  stamp <store>` ou `bdd check <store>` à la main, et ne considérer la
  colonne comme informative que si on l'a soi-même remplie en substance
  ailleurs (note, ou colonne `notes` d'`affirmations.md` si un rapprochement
  a eu lieu).
- **la lecture intégrale elle-même**, la réexécution witness dans
  `experiments/<date>_recyclage_<nom>/`, et le choix du verdict (« recyclé »,
  « réécrit » ou « rejeté ») sont un travail d'assistant : lire le fichier en
  entier (pas seulement les 40 premières lignes que scrutent les contrôles
  mécaniques), comprendre ce qu'il fait, le rejouer dans un répertoire
  d'expérience isolé avec les données courantes, comparer le résultat à ce
  que le legacy prétendait produire, puis seulement alors choisir un
  verdict et lancer `recycler … --verdict … --apply`.

## Les trois verdicts et ce que `--vers`, `--lien`, `--apply` font exactement

- **`recyclé`** : le fichier est jugé directement réutilisable sans
  modification. Exige `--vers DEST`.
- **`réécrit`** : le fichier a été (ou sera) repris avant réutilisation —
  chemins en dur corrigés, appel de store mis à jour, etc. Exige lui aussi
  `--vers DEST`. Rien dans `recycler` ne fait la réécriture elle-même : la
  commande enregistre seulement le verdict et copie ce qui se trouve
  aujourd'hui dans l'archive vers `DEST` — si la réécriture doit encore être
  faite, c'est à l'assistant de la faire dans le fichier copié, après coup,
  pas dans l'archive.
- **`rejeté`** : le fichier reste dans l'archive, jamais recyclé. `--vers`
  n'est pas exigé pour ce verdict (la vérification `verdict in ("recyclé",
  "réécrit") and not vers` ne s'applique pas à `rejeté`).

`--vers CHEMIN` : destination de la copie, relative à la racine du projet
si non absolue. **L'archive n'est jamais modifiée par cette copie** — le
fichier ou répertoire source reste en place sous `archives/…`, intact ;
`recycler` ne fait qu'ajouter une copie ailleurs. C'est délibéré : l'archive
reste la trace complète et non altérée du projet interrompu, y compris
après recyclage de certains de ses fichiers.

`--lien` : force un lien symbolique vers le fichier de l'archive plutôt
qu'une copie physique. Sans cette option, un lien symbolique est tout de
même posé automatiquement dès que le fichier source dépasse 100 Mo (calcul
sur `chemin.stat().st_size`, uniquement pour les fichiers — un répertoire
recyclé sans `--lien` explicite est toujours copié intégralement quelle que
soit sa taille, `shutil.copytree`). Si la destination existe déjà au moment
de poser un lien, elle est mise à la corbeille (`gio trash`, jamais
supprimée directement) avant la création du lien.

`--apply` : sans cette option, `recycler` est un dry-run complet — il
affiche les contrôles mécaniques, la ligne qui serait écrite dans
`RECYCLAGE.md` et l'action de copie ou de lien qui serait faite, mais
n'écrit ni le fichier ni la copie. C'est le mode à utiliser pour une
première passe de contrôle mécanique avant de s'engager sur la lecture
intégrale et la réexécution témoin.

Refus systématiques, avant tout autre traitement : chemin introuvable ;
chemin qui n'est sous aucune `archives/<date>_reboot/` du projet courant
(`_archive_reboot_de` vérifie l'appartenance à la bonne archive du bon
projet — un chemin qui serait, par accident de structure de répertoires,
un sous-chemin de l'archive d'un *autre* projet n'est plus accepté depuis la
correction faite en test AB4) ; verdict hors nomenclature ; `--vers` manquant
avec un verdict qui l'exige.

## Le garde-fou de hook

`precompute_reminder.sh`, déclenché en `PreToolUse` sur les outils `Write`
et `Bash`, porte un second rappel non bloquant spécifique au recyclage
(le premier rappel, sur `Write` sous `analyses/`/`experiments/`, est sans
rapport avec le reboot). Sur `Bash`, une expression régulière cherche dans
la commande un interpréteur (`python3?`, `Rscript`, `bash`, `sh`, ou `./`)
suivi d'un chemin de la forme `archives/<AAAA>-<MM>-<JJ>_reboot[-suffixe]/
….{py,R,r,sh}` :

```
\b(python3?|Rscript|bash|sh|\./)\S*[[:space:]]+\S*archives/[0-9]{4}-[0-9]{2}-[0-9]{2}_reboot[^/[:space:]]*/\S+\.(py|R|r|sh)\b
```

Si la commande matche, le hook injecte (silencieusement, dans le contexte du
modèle — jamais affiché au terminal, confirmé auprès de `claude-code-guide`
avant l'ajout) le rappel :

> Ce script vit dans une archive de reboot (`archives/<date>_reboot/`) :
> lecture seule par doctrine, rien ne s'y exécute ni ne s'y importe
> directement. Passer par `/reboot recycler <chemin>` (contrôles
> mécaniques, puis copie hors archive avant réexécution).

Le hook est délibérément étroit : il ne se déclenche que sur une commande
qui ressemble à une exécution directe d'un script d'archive (interpréteur
suivi du chemin), pas sur une simple lecture (`cat`, `less`, `head` d'un
fichier d'archive restent silencieux), et pas sur toute autre commande
Bash. C'est un rappel, pas un blocage : rien n'empêche techniquement
d'exécuter le script malgré l'avertissement, la discipline reste portée par
qui lit le rappel. Il ne couvre pas non plus un `import` fait depuis un
interpréteur Python déjà lancé (`python3 -c "import sys;
sys.path.insert(0, 'archives/...'); import module"`) ni une commande passée
par un chemin relatif construit dynamiquement — le motif est mécanique, pas
une analyse de flot d'exécution.
