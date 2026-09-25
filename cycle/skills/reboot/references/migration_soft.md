# Mode `soft` — migration d'environnement sans archivage

## Pourquoi ce mode existe

`hard` jette l'acquis d'un projet dans une archive datée et refonde les cinq
artefacts à neuf : c'est le geste juste pour un projet dont l'écart avec
l'environnement courant est devenu si large, ou dont la dernière trace est si
ancienne, que relire l'existant coûterait plus cher que le reconstruire. Mais
la majorité des reprises ne sont pas dans ce cas. Un projet dont la dernière
entrée de cahier date de six semaines, ou dont le seul tort est de citer une
version d'environnement mineure dépassée, a un état des découvertes exact, des
pistes cohérentes, un manuscrit qui avance : rien de tout cela n'a besoin
d'être archivé. Ce qui a bougé, ce n'est pas ce que le projet sait, c'est
l'environnement qui l'entoure — un script déplacé, une convention de nommage
changée, un registre de bases mis à jour. Le travail qui reste à faire est de
re-citer ce qui dépend de l'environnement et de relire le manuscrit contre les
règles nouvelles, pas de tout reprendre à zéro.

`soft` est donc le mode qui **pose une piste de travail** plutôt que d'agir à
la place de l'utilisateur : il ne déplace aucun fichier, ne crée aucune
archive, ne réécrit aucun registre applicatif. Son seul effet est d'ouvrir,
dans les artefacts vivants du projet, la trace explicite qu'une migration est
due et de lister ce qu'elle doit couvrir.

## Quand `soft` s'applique plutôt que `hard` (règles 4 et 5 du diagnostic)

`reboot.py` évalue les règles du diagnostic dans l'ordre et retient la
première qui s'applique (`evaluer_regles`, `reboot.py:380-426`). Après la
règle 1 (projet en répertoire de clôture → `AUCUN`, ramener en `en_cours/`
avant tout reboot), la règle 2 (projet actif et récent, sans dérive majeure →
`AUCUN`) et la règle 3 (`HARD`), viennent :

- **Règle 4 — `SOFT`** : au moins l'une de ces conditions,
  - `delta == "soft"`, c'est-à-dire un delta d'environnement **mineur** entre
    la version citée par le projet (`env_projet`) et la version courante
    (`env_courant`), tel que rendu par `env_version.py` ;
  - le projet n'a jamais été rattaché à une version (`rattache` faux) et l'âge
    de la dernière entrée de cahier est compris entre 30 et 90 jours (en
    deçà de 30 jours, la règle 2 aurait déjà rendu `AUCUN` ; au-delà de 90
    jours sans estampille, la règle 3 rend `HARD`) ;
  - une dérive des données citées est détectée alors que la phase du projet
    est déjà avancée (`phase >= 4`) — un projet dont l'essentiel de l'analyse
    est fait n'a pas besoin d'être refondu pour re-citer une base.
- **Règle 5 — `AUCUN`** : par défaut, si aucune des règles 1 à 4 ne se
  déclenche.

Le distinguo avec `HARD` (règle 3) tient donc à l'**ampleur du delta**
(mineur contre majeur, au sens `env_version.py` : `MINEUR → soft`,
`MAJEUR → hard`, `CORRECTIF → aucune`, cf. `outils/env_version.py:41`) et à la
**fraîcheur du projet** (30-90 jours pour `soft`, ≥ 90 jours ou delta majeur
pour `hard`). Un projet très ancien mais dont le delta se trouve n'être que
mineur reste basculé en `HARD` par la règle 3 dès que son absence d'estampille
et son âge ≥ 90 jours la déclenchent en premier — les règles ne se cumulent
pas, la première qui matche l'emporte.

## Ce que `soft --apply` écrit exactement

`cmd_soft` (`reboot.py:1365`) refuse d'agir si `pistes.md` n'existe pas dans
le projet (repli : projet hors format `init-project`, `soft` n'a pas de prise
sur lui) et se contente, sinon, de trois écritures ciblées.

### La piste majeure et ses cinq sous-pistes

Un bloc est ajouté en fin de `pistes.md` (`_bloc_piste_soft`,
`reboot.py:1319`) :

```
## Pn. Migration d'environnement vA→vB (reboot soft <date>) [en cours]
  origine : reboot soft <date>    maj : <date>
  - Pn.1  Impact sur l'article : relire `main.tex` (et `main_fr.tex`) contre les règles nouvelles de l'environnement [à faire] [Opus:high]
  - Pn.2  Données à re-citer : `bdd check` puis `bdd stamp`, recomptes [à faire] [Sonnet:high]
  - Pn.3  Scripts à re-valider : réexécution témoin de chaque script cité dans l'état [à faire] [Sonnet:xhigh]
  - Pn.4  Registres à estampiller : renvoi de péremption en tête de `claim_check.md`, `fig_check.md`, `verdict_diffusion.md`, `plan_narratif.md` [à faire] [Sonnet:high]
  - Pn.5  En-tête de l'état (`**Environnement :**`), `/etat update`, clôture de la piste [à faire] [Sonnet:high]
```

Le libellé et l'étiquette de routage de chaque sous-piste sont fixés par la
constante `SOUS_PISTES_SOFT` (`reboot.py:1252`) — ils ne se paramètrent pas.
Point à ne pas mal lire : **`soft` pose ces cinq sous-pistes à l'état
`[à faire]`, il ne les exécute pas**. Relire le manuscrit, re-citer les
données, réexécuter les scripts et poser les renvois de péremption dans les
registres restent un travail que l'agent ou l'utilisateur mène ensuite, piste
par piste, exactement comme n'importe quelle autre entrée de `pistes.md`.
`soft` ne fait que rendre ce travail visible et daté.

L'identifiant de piste `Pn` est calculé par `_prochain_id_piste`
(`reboot.py:1276`) sur la convention majoritaire des projets scaffoldés par
`init-project` (`P<entier>`, incrémenté sur la lettre dominante) ; pour un
projet qui numérote ses pistes majeures par lettres pures — cas du projet
`environnement` lui-même — le repli est l'incrément façon colonnes de
tableur (`Z → AA`).

### La ligne `**Environnement :**` de l'état, réécrite en place

`_ligne_environnement_soft` (`reboot.py:1340`) réécrit la ligne existante si
elle est trouvée (`RE_ENV_PROJET`), ou l'insère juste après la ligne
`**Réécrit le :**` si celle-ci existe, ou juste après le titre `# ...` sinon.
Le reste de `etat_des_decouvertes.md` n'est **pas touché** : à la différence de
`hard`, qui remplace l'état entier par un squelette neuf, `soft` préserve
intégralement l'acquis §1 à §9 — c'est exactement le point : rien n'est perdu
puisque rien n'est faux, seule l'estampille change. La nouvelle ligne prend la
forme :

```
**Environnement :** vB (migration soft depuis vA, <date>, piste Pn)
```

ou, en repli (voir plus bas), le texte explicite d'un delta non calculable.

### Le bloc ajouté au `CLAUDE.md` du projet

Si `CLAUDE.md` existe, `_bloc_claude_soft` (`reboot.py:1330`) lui ajoute en
fin de fichier :

```
## Migration d'environnement (soft, <date>)

- **Delta :** vA → vB
- **Piste :** Pn — voir `pistes.md`
- **Statut :** en cours ; cinq sous-pistes (article, données, scripts, registres, état).
```

Si `CLAUDE.md` n'existe pas, le bloc n'est pas écrit et `soft` le signale sur
la sortie standard sans échouer.

### Les renvois de péremption posés en tête des registres

Contrairement à ce que le libellé de la sous-piste Pn.4 pourrait laisser
penser, `soft` ne pose lui-même **aucun** renvoi de péremption dans
`claim_check.md`, `fig_check.md`, `verdict_diffusion.md` ou
`plan_narratif.md` : il se contente d'ouvrir la sous-piste qui demande de le
faire. C'est la même logique que pour Pn.1 à Pn.3 : `soft` déclare le travail,
il ne l'exécute pas. Poser le renvoi lui-même reste un geste manuel de
l'agent qui traite Pn.4, à la manière de ce que `hard --kb-renvoi` fait pour
les entrées de KB partagée — jamais un retrait, toujours un renvoi qui dit
« ce qui suit était vrai sous l'environnement vA, à revérifier sous vB ».

## Garde-fous réellement codés

- **Refus du doublon pour un même couple de versions.** `_piste_migration_existe`
  (`reboot.py:1314`) cherche dans `pistes.md` une piste « Migration
  d'environnement » déjà associée au couple `vA_fmt → vB_fmt` calculé pour
  l'appel courant ; si elle existe, `cmd_soft` refuse et n'écrit rien. Sans ce
  garde-fou, relancer `/reboot soft` plusieurs fois sur le même projet avant
  d'avoir traité la migration précédente empilerait des pistes redondantes.
- **Refus quand `vA == vB` (« déjà à jour »).** Bug réel trouvé en test
  (`pistes/AB.md`, sous-piste AB4) : un premier `soft --apply` réécrit la
  ligne `**Environnement :**` de l'état avec `vB`. Un second appel, lancé par
  mégarde ou par un agent qui ne relit pas l'état avant d'invoquer `soft`,
  recalculait alors `vA_fmt == vB_fmt == vB` et créait une piste de migration
  **vide de sens** (« migration de vB vers vB ») au lieu de reconnaître que le
  projet était déjà à jour. Le correctif ajoute la vérification explicite en
  tête de `cmd_soft` (`reboot.py:1374`) et distingue ce cas du doublon
  ci-dessus par un message dédié : « projet déjà à jour, rien à migrer ».
- **Repli quand le versionnage d'environnement n'est pas déployé.**
  `_delta_soft` (`reboot.py:1296`) gère deux causes de repli distinctes : soit
  `env_version.py` est indisponible (`env_disponible` faux), soit le projet
  n'a jamais été rattaché à une version (`env_courant` absent). Dans les deux
  cas, `vB_fmt` devient le littéral `v?` et le champ `texte` explique la cause
  et renvoie au cahier de `environnement` autour de la date de la dernière
  entrée du projet, pour que l'agent qui traite Pn.1 sache où chercher ce qui
  a changé. Bug réel corrigé en cours de test (AB4) : ce repli produisait un
  doublon de préfixe (« vnon estampillé » au lieu de « non estampillé »)
  quand le projet n'avait jamais été rattaché — `vA_fmt` vaut alors déjà le
  texte complet « non estampillé », sans le `v` que l'affichage rajoutait par
  ailleurs.

## Limites assumées

`soft` ne pose **pas** de `MANIFEST.json`. C'est une différence délibérée
avec `hard`, qui journalise chaque opération (`create`, `move`,
`kb_renvoi`, …) dans l'archive précisément pour permettre à `annuler`
(`reboot.py:1174`) de rejouer les opérations à l'envers. `soft` n'archive
rien et ne déplace aucun fichier : ses trois écritures (piste, ligne
`**Environnement :**`, bloc `CLAUDE.md`) sont des mutations en place,
directement dans les artefacts vivants du projet, exactement comme n'importe
quelle autre mutation de `pistes.md` ou `etat_des_decouvertes.md` faite à la
main. La sous-commande `annuler` cherche un `archives/<date>_reboot[-suffixe]/
MANIFEST.json` : pour un reboot `soft`, ce fichier n'existe jamais, et
`annuler` refusera systématiquement avec « rien à annuler ». Revenir en
arrière après un `soft --apply` se fait donc comme on annule n'importe quelle
mutation de piste : `git checkout` sur les trois fichiers touchés si le
projet est versionné, ou retouche manuelle sinon. Ce n'est pas un oubli mais
une conséquence directe de l'absence d'archive — le plan (§AB.4, §AB.6) ne
prévoit d'ailleurs `MANIFEST.json` que pour `hard`.
