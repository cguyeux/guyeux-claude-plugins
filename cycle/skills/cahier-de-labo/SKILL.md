---
name: cahier-de-labo
description: Read or append timestamped entries to a research project's lab notebook (`cahier_de_labo.md`). Use on `/cahier-de-labo`, `/cahier-de-labo update`, `/cahier-de-labo read`, or "ajouter une entrée au cahier", "mettre à jour le cahier de labo", "consulter le cahier", "what's in the lab notebook". Found by walking up from the current directory.
---

# cahier-de-labo — Lab notebook for a research project

The lab notebook is the **append-only memory** of a research project. Every
session that produces knowledge — a script written, an analysis run, a figure
generated, a result interpreted, a hypothesis formulated, a literature note
taken — gets a timestamped entry. The notebook is the source of truth that
lets a future Claude (or human) pick up the project from cold.

## Locating the cahier

Walk up from the current working directory. The first directory that contains
a file named `cahier_de_labo.md` (or, for older projects, `JOURNAL.md`) is
the **project root**. Use that file. If none is found within five levels up,
report : "Aucun cahier_de_labo.md trouvé en remontant depuis CWD. Initialise
le projet avec `/init-project <nom>`."

## Le cahier du projet CONCERNÉ, pas celui d'où l'on travaille

La règle de localisation ci-dessus dit où se trouve le cahier du répertoire courant.
Elle ne dit pas de quel projet relève la connaissance qu'on vient de produire, et
c'est une autre question.

**Une séance qui produit de la connaissance sur un AUTRE projet écrit dans le cahier
de CE projet**, même si l'on travaille depuis ailleurs. Le cahier courant ne garde
alors qu'un renvoi d'une ou deux lignes, ou rien du tout si la séance ne le concerne
pas.

Cas vécu, 2026-08-25 : une journée de soumissions menée depuis `mtbc/Rv1025` a
journalisé chez lui le choix de revue de `bpal_resistance_emergence`, la coupe de son
manuscrit à 3 498 mots et la soumission de `Rv0810c` chez Proteins. Les cahiers de ces
deux projets s'arrêtaient à 09:49 ce jour-là. Rouverts plus tard, ils ne diraient pas
ce qui leur est arrivé, alors que ce sont eux qu'on relit avant de reprendre un
manuscrit. La commodité d'écrire là où l'on est coûte la mémoire de deux projets.

En pratique, avant d'écrire une entrée, se demander de quel projet parle ce qui vient
d'être appris. Si la réponse n'est pas le projet courant, remonter au cahier du bon
projet (y compris s'il est archivé dans `clos_soumis/` : un projet archivé se relit et sa
soumission continue de vivre), et y écrire l'entrée avec la mention de la session
d'origine. Une séance qui touche trois projets écrit trois entrées, pas une.

## Modes

The user may call this skill in three ways :
- `/cahier-de-labo` (no arg) — show a 1-screen summary of the cahier (read mode).
- `/cahier-de-labo read` — same as above.
- `/cahier-de-labo update` — append a new entry for the current session.

Default to `update` when the user clearly produced knowledge in the session.
Default to `read` at the start of a session ("rappelle-moi où on en est").

Natural-language triggers: « ajouter une entrée au cahier » and « mettre à jour
le cahier de labo » map to `update` ; « consulter le cahier » and "what's in the
lab notebook" map to `read`. Works on any academic research project that has a
`cahier_de_labo.md` at its root.

## Read mode

Print to the conversation :
1. The project name and one-line context (from the file's header).
2. The 3 most recent entries verbatim, headed by their date.
3. A short status synthesis : what's done, what's open, what was the last
   question raised (inferred from the entries).

Do **not** modify the file in read mode. Never open `cahier_de_labo_archive.md`
for a routine read — its whole purpose is to stay out of the default reading
path (see "Archivage automatique" below). Only consult it for a targeted
history question (see "Recherche dans l'historique").

## Archivage automatique (`cahier_de_labo_archive.md`) — économie de tokens

`cahier_de_labo.md` ne garde en clair que les ~4 dernières entrées : le mode
`read` n'en exploite jamais davantage. Le reste vit, verbatim et jamais réécrit,
dans `cahier_de_labo_archive.md` (même dossier).

**Déclenchement obligatoire, sur TOUT projet utilisant ce skill** : après tout
`/cahier-de-labo update` (ajout d'une nouvelle entrée), si `cahier_de_labo.md`
compte alors plus de 5 entrées, archiver les plus anciennes jusqu'à n'en garder
que 4 en clair :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/cahier-de-labo/archive_old_entries.py <chemin>/cahier_de_labo.md --keep 4 --apply --date-tag AAAAMMJJ
```

Le script fait sa propre sauvegarde `<fichier>.bak_<date>` et revérifie que
chaque entrée déplacée est byte-identique dans l'archive avant de conclure
(échoue bruyamment sinon). Idempotent : rien à archiver si le fichier compte
déjà ≤ `--keep` entrées. Dry-run sans `--apply` pour prévisualiser. Si
`cahier_de_labo_archive.md` n'existe pas encore, le script le crée au premier
archivage.

## Recherche dans l'historique

L'usage d'origine du cahier, pendant la rédaction, est de retrouver *sur quel
dataset / avec quel script* un résultat donné a été obtenu. C'est pour ça que
chaque entrée porte désormais un champ `piste:` obligatoire (voir gabarit
ci-dessous) : il relie l'entrée à son identifiant dans `pistes.md` /
`pistes_archive.md`. Pour retrouver l'historique d'une piste, ne jamais lire
`cahier_de_labo_archive.md` en entier — chercher ciblé :

```bash
rg "piste ?: .*P16\b" cahier_de_labo_archive.md      # toutes les entrées liées à P16
rg -i "<mot-clé>" cahier_de_labo_archive.md           # recherche libre
rg "^## 2026-07" cahier_de_labo_archive.md            # plage de dates
```

## Update mode

The lab notebook is **append-only**. Never edit past entries. To add an
entry, append at the end of the file with this structure. The `piste:` line
is **mandatory** — write `piste: -` explicitly if truly nothing applies
(rare : purely administrative session), never omit the field silently, since
that is what makes `rg` lookups against the archive reliable :

The `données :` line, right under `piste :`, is **mandatory** on the same
terms as soon as the session read from a versioned store declared in
`bdd/registre.json` (skill `bdd`) : one citation `<store>@<version>` per
store actually read, semicolon-separated (`données : mtbc-actuelle@r15 ;
mtbc-barcoding@r3`), or `données : -` when nothing versioned was read.
Obtain the citation with `bdd stamp <store>` (or `paths.stamp()` /
`bdd_journal.stamp()` from a script already invoking the store) rather than
guessing a revision — a stale or invented citation is worse than none,
because a reader trusts it without checking.

```markdown
## YYYY-MM-DD HH:MM — <short title>

piste : Pxx[, Pyy]
données : <store>@<version>[ ; <store>@<version>]

### Contexte
<one or two paragraphs describing what triggered this session : a
question, a previous result, a meeting, a request from a co-author.>

### Travaux réalisés
- <action 1, with concrete artefacts : path/to/script.py, figure name,
  N_strains processed, etc.>
- <action 2>

### Résultats / observations
- <bullet of the concrete output, with numbers and units when available>
- <pattern noticed, anomaly spotted, expectation confirmed or denied>

### Interprétation
<one or two paragraphs : what does this mean biologically / scientifically /
operationally? Why is it interesting? Connect to existing literature or
previous entries when relevant.>

### Points ouverts
- <next question to answer>
- <known limitation>

### Suite suggérée
<one paragraph : what would be the next concrete step?>

---
```

### Étape 4 — bilan narratif à l'écran (obligatoire)

Après avoir écrit l'entrée dans le fichier, **toujours** produire un bilan
narratif détaillé dans la conversation, destiné à l'utilisateur. L'utilisateur
ne doit jamais avoir besoin d'aller lire le cahier pour savoir ce qui vient
de se passer. Le bilan doit :
- raconter ce qui a été fait dans la session, dans l'ordre,
- expliciter les découvertes avec leurs chiffres et leur signification
  (biologique, mathématique, opérationnelle selon le domaine),
- mentionner les interprétations, les hypothèses formulées, les patterns vus,
- identifier les points ouverts, les limites des données ou de la méthode,
- suggérer une prochaine étape concrète,
- se terminer par la ligne de consommation de la séance, produite par
  `python3 ${CLAUDE_PLUGIN_ROOT}/skills/routage/scripts/routage.py tache done --piste Px --qualite …`
  (prévu contre observé, verdict de qualité) quand une piste a été ouverte par
  `/pistes start` ; sinon, par la configuration recommandée pour la suite
  (`Lancement : /clear · modèle · effort`).

**Bilan et entrée du cahier ne se recopient pas.** Le bilan à l'écran raconte et
interprète pour l'utilisateur ; l'entrée du cahier consigne les faits, les
chiffres et les chemins pour plus tard. Les chiffres apparaissent dans les deux
(ils sont le fond commun), mais ni le raisonnement ni la méthode ne se
réécrivent deux fois : le bilan renvoie à l'entrée par sa date, l'entrée renvoie
aux fichiers par leur chemin. De même, l'entrée du cahier ne réécrit pas ce que
`etat_des_decouvertes.md` porte déjà : elle dit ce qui a changé et renvoie au §.
Cette économie n'est pas cosmétique — chaque redite est payée à l'écriture puis
à chaque lecture ultérieure du fichier, dans toutes les sessions qui l'ouvrent.

Cette règle s'applique :
- quand `/cahier-de-labo update` est explicitement invoqué,
- quand le hook Stop déclenche la mise à jour automatique en fin de session,
- même si aucun fichier n'a été modifié sur disque mais qu'une connaissance
  a été produite par la discussion (interprétation, hypothèse, réponse
  scientifique).

## Quand l'entrée est-elle nécessaire ?

Toute production de connaissance déclenche l'entrée :
- code écrit ou modifié, scripts lancés, données transformées,
- mais aussi : interprétation de résultats, explication d'un mécanisme,
  formulation d'hypothèses, observation d'un pattern, réponse à une question
  scientifique mobilisant des connaissances du domaine, revue de littérature.

Une session triviale (uniquement de la lecture, ou une question administrative)
ne nécessite pas d'entrée. Si en doute, ajouter une entrée courte plutôt que
rien.

## Format compatible avec les anciens projets

Les projets antérieurs au skill peuvent utiliser `JOURNAL.md` au lieu de
`cahier_de_labo.md`. Si seul `JOURNAL.md` existe, l'utiliser comme cible
(même logique append-only, format markdown libre avec horodatage).

## Erreurs à éviter

- Ne jamais réécrire ou condenser les entrées passées. Si une entrée passée
  contient une erreur factuelle, ajouter une nouvelle entrée qui corrige
  explicitement (« 2026-04-12 — correction de l'entrée du 2026-04-08 :
  ... »).
- Ne pas dupliquer dans la mémoire (`~/.claude/projects/.../memory/`) ce qui
  est déjà dans le cahier — la mémoire vise les patterns inter-projets, le
  cahier vise l'historique de **ce** projet.
- Ne pas créer un nouveau cahier dans le CWD si un cahier existe plus haut
  dans l'arborescence (cela créerait deux cahiers concurrents).
- Ne jamais omettre le champ `piste:` d'une nouvelle entrée (mettre `piste: -`
  si vraiment rien ne s'applique) : un champ manquant casse la recherche `rg`
  a posteriori sur l'archive.
- Ne jamais lire `cahier_de_labo_archive.md` en entier « pour être sûr » :
  c'est exactement le coût que l'archivage automatique est censé éviter.

## Note sur l'écosystème

- Le hook Stop (`~/.claude/settings.json`) vérifie en fin de session que
  le cahier a bien été mis à jour si une production de connaissance a eu
  lieu. Il bloque le Stop sinon.
- Le skill `/init-project` crée `cahier_de_labo.md` à la racine de tout
  nouveau projet.
- Une vue d'ensemble inter-projets (idées, patterns, leçons) reste dans
  `~/.claude/knowledge/` et n'est pas dupliquée ici.
