---
name: etat
description: Read or rewrite a project's consolidated state of knowledge (`etat_des_decouvertes.md`) — proven, refuted, uncertain, position vs literature. Use on `/etat`, `/etat read`, `/etat update`, or "faire le point", "où on en est", "réécrire l'état des découvertes", "consolider ce qu'on sait", "state of knowledge". Project root = first parent with `cahier_de_labo.md`.
argument-hint: "[read | update]"
---

# etat — État des découvertes consolidé d'un projet

`etat_des_decouvertes.md` est la **photographie courante du savoir du projet** :
ce qui est tenu pour prouvé, ce qui est réfuté, ce qui reste incertain, où l'on
se situe par rapport à la littérature, et les grandes directions en cours. C'est
une **vue dérivée régénérable depuis le cahier de labo** (qui, lui, est la vérité
append-only). Si l'état est périmé, on le reconstruit depuis le cahier : il ne
concurrence jamais le cahier, il le résume.

Distinction avec les autres artefacts (à ne pas confondre) :
- `cahier_de_labo.md` = historique append-only, séance par séance (la vérité).
- `CLAUDE.md` §état courant = consignes opérationnelles + pointeur vers ce fichier.
- `pistes.md` = l'arbre des directions futures (géré par `/pistes`).
- `etat_des_decouvertes.md` = le bilan transversal prouvé/infirmé/ouvert (ce skill).

**Savoir ≠ manuscrit.** Ce fichier inventorie ce qui est SU, pas ce qui sera
ÉCRIT. Les deux divergent avec le temps, et un acquis qui sort du périmètre de
l'article se perd si rien ne le trace. D'où le champ `destination:` sur chaque
acquis de §2 et la §9 « Hors périmètre » : c'est le skill `/recadrage` qui les
renseigne et qui essaime vers le registre parent. Ce skill-ci les préserve et
signale ceux qui manquent — il ne tranche pas les destinations lui-même.

## Localiser le projet

Remonter depuis le répertoire courant, 5 niveaux maximum ; le premier répertoire
contenant `cahier_de_labo.md` est la racine. Si rien n'est trouvé : afficher
« Aucun projet structuré trouvé (pas de cahier_de_labo.md). » et s'arrêter.

## Modes

- `/etat` ou `/etat read` → **lecture** : afficher le contenu de
  `etat_des_decouvertes.md`. S'il n'existe pas, le signaler et proposer
  `/etat update` pour le créer depuis le cahier.
- `/etat update` → **réécriture intégrale** (voir ci-dessous). Défaut quand
  l'utilisateur veut « faire le point » en fin d'itération.

Déclencheurs en langue naturelle : « faire le point », « où on en est »,
« réécrire l'état des découvertes », « consolider ce qu'on sait », "state of
knowledge".

## Mode update — réécriture intégrale

Ce fichier est **réécrit en entier** à chaque itération (jamais édité par
fragments). Procédure :

1. Lire `etat_des_decouvertes.md` s'il existe (version N-1) pour récupérer le
   numéro d'itération et la classification précédente.
2. Lire le **delta du cahier** : toutes les entrées de `cahier_de_labo.md`
   postérieures à la dernière réécriture (repérables par leur date). C'est la
   matière première de la mise à jour.
3. Reclasser chaque énoncé du projet dans les 9 sections : ce qui était
   « incertain » et a été tranché passe en « prouvé » ou « réfuté » ; un nouvel
   acquis entre en §2 ; une hypothèse tombée entre en §3 avec le contrôle/null
   qui l'a tuée.
3bis. **Préserver les destinations existantes** de §2 et le contenu de §9 : la
   réécriture intégrale ne doit jamais les effacer (ce serait perdre le tri fait
   par `/recadrage`). Un acquis NOUVEAU entre sans destination ; le signaler à
   l'étape 7 et proposer `/recadrage triage` — ne pas trancher la destination
   soi-même, c'est un jugement de périmètre, pas de preuve.
4. Vérifier la **§5 (position vs littérature)** : consulter
   `litterature_review/index.md` et les fiches du dossier `litterature_review/`.
   Pour chaque énoncé « prouvé », trancher honnêtement : est-ce **nouveau** ou
   **déjà publié** (re-démontré) ? C'est le garde-fou anti-redécouverte.
5. **Réécrire le fichier en entier** avec le squelette ci-dessous, en
   **incrémentant le numéro d'itération** et en redatant. Aucune date interne
   dans le corps (l'historique est dans le cahier).
6. Mettre à jour le pointeur du `CLAUDE.md` s'il manque (« État : voir
   `etat_des_decouvertes.md` »). **Si `CLAUDE.md` est ABSENT DE LA RACINE (pas
   seulement dépourvu du pointeur)** : ne pas le créer unilatéralement — c'est
   un gap de scaffolding du projet (convention `/init-project`/`--migrate`),
   hors périmètre de ce skill. Signaler le fait à l'utilisateur dans le bilan
   de l'étape 7 et proposer `/init-project --migrate`, sans agir seul.
7. **Bilan narratif à l'écran** (obligatoire, comme pour le cahier) : raconter
   ce qui a changé depuis l'itération N-1 (nouvel acquis, hypothèse tombée,
   objectif révisé, direction abandonnée), pour que l'utilisateur n'ait pas à
   ouvrir le fichier.

**Le champ `Phase` se REPORTE, il ne s'invente pas.** C'est l'emplacement canonique de
la phase du cycle-projet, celui que lisent `/cycle-projet`, `INDEX.md` et le hook de
démarrage de session. Puisque ce fichier est réécrit EN ENTIER à chaque itération, un
squelette qui ne le mentionne pas le fait disparaître : mesuré le 2026-09-08 sur le
dépôt `mtbc`, **17 états réécrits depuis août avaient perdu le champ**, dont des projets
en finalisation (`Rv2516c`, `L5L6-codivergence`, `NTM_unidentified`,
`rehumanisation_L6L9L10`), et seulement la moitié des réécritures le conservaient. Règle
opératoire : recopier la valeur existante telle quelle ; si le fichier n'en portait pas,
écrire `**Phase :** non déclarée` plutôt que d'estimer — une phase fausse est pire qu'une
phase absente, puisqu'elle cesse d'être estimée et devient crue. Seul `/cycle-projet`,
qui mesure la phase observée depuis les artefacts, est habilité à la faire avancer.
C'est le même garde-fou que celui tiré de l'incident de l'atlas (piste `P45` de `mtbc`) :
une passe qui ne connaît pas une donnée ne doit pas pouvoir la supprimer.

## Squelette normalisé (8 sections fixes, titres invariants)

```markdown
# État des découvertes — <projet>

**Itération :** N    **Phase :** P/5 — <libellé>    **Réécrit le :** YYYY-MM-DD
**Dernier recadrage :** YYYY-MM-DD (POURSUIVRE|RECADRER|SCINDER)
**MIU projet :** M<0-3> I<0-3> U<0-3>   <!-- maturité / importance / urgence, cf. skill recadrage -->
**Environnement :** vX.Y.Z (rattaché le YYYY-MM-DD)   <!-- version d'environnement, cf. outils/env_version.py -->
**Données :** <store>@<version>[ ; <store>@<version>] ou `-` si aucun store versionné (skill `bdd`) n'a été lu
Règle : fichier RÉÉCRIT en entier à chaque fin d'itération, régénérable depuis
`cahier_de_labo.md`. Pas d'historique ici (il est dans le cahier).

La ligne `**Données :**` est réécrite à chaque `/etat update` à partir des citations
`piste:`/`données:` réellement portées par les entrées du cahier consolidées dans cette
itération (jamais recopiée de l'itération N-1 sans vérifier qu'elle est toujours
d'actualité) : elle dit sur quelle(s) révision(s) de base(s) reposent les acquis §2
au moment de cette réécriture, condition de leur reproductibilité.


## 1. Question de recherche et objectifs (évolutifs)
- Objectif principal : …
- Sous-objectifs : …
- [Si un objectif a changé depuis N-1 : « OBJECTIF RÉVISÉ : … (raison) ».]

## 2. Acquis — ce qui est démontré
- <énoncé falsifiable> — preuve : <script/figure/chiffre> — solidité : forte/moyenne
  — déjà publié ? non / oui (réf) / partiellement (réf) — destination : A|B|C|D
  [après un reboot : « prouvé le YYYY-MM-DD, env vX, <store>@<version> (A<k>) »]

## 3. Réfuté / écarté
- <hypothèse infirmée> — pourquoi : <contrôle ou modèle nul qui l'a tuée>

## 4. Incertain / en cours d'arbitrage
- <énoncé> — ce qui trancherait : <expérience/contrôle décisif>

## 5. Position vs littérature
- Nouveau par rapport à l'état de l'art : …
- Re-démontré (déjà publié) : <réf>

## 6. Grandes directions en cours
- <axe structurant actuel et pourquoi>

## 7. Angles morts / contre-arguments non levés
- <le contre-argument le plus fort qu'on n'a pas encore réfuté>

## 8. Verdict en une phrase
<où en est le projet, lisible par un tiers froid>

## 9. Hors périmètre — essaimé / classé
- <acquis destination C> — essaimé vers `<registre parent>` P<n> le YYYY-MM-DD
- <acquis destination D> — classé sans suite — raison : <pourquoi il n'ira nulle part>
```

Les sections 1 à 8 sont **invariantes**. La §9 est renseignée par `/recadrage` ;
si aucun acquis n'est sorti du périmètre, la laisser avec la mention « néant à ce
jour » plutôt que de la supprimer (son absence se lit comme un oubli, pas comme
un vide).

## Après un reboot : le §2 ne reçoit que du re-prouvé

Si `affirmations.md` existe à la racine, le projet sort d'un `/reboot hard` et
son acquis est en transit : **rien n'entre en §2 qui n'y soit `[prouvée]`**. Un
énoncé hérité qui figurait au §2 de l'état legacy n'est pas un acquis, c'est une
affirmation à retester ; le recopier au motif qu'il était déjà écrit quelque part
annule tout le bénéfice du reboot, qui existe précisément parce qu'une
affirmation vraie sous l'environnement et les données d'il y a huit mois peut
être fausse aujourd'hui sans que rien ne le signale.

Concrètement, à chaque `/etat update` sur un projet en rétablissement : lire le
frontmatter de `affirmations.md`, ne verser au §2 que les lignes `[prouvée]` (au
§3 les `[réfutée]`), en gardant dans l'énoncé la trace de sa preuve — date,
version d'environnement, révision de base, identifiant `A<k>`. Les lignes encore
`[non testée]` ou `[en test]` restent où elles sont ; le §4 peut les mentionner
comme incertaines, jamais le §2. Le fichier se vide ainsi de lui-même, et
`/reboot clore` le gèle dans l'archive quand il ne reste plus rien à trancher.

## Erreurs à éviter

- Ne pas y recopier l'historique séance par séance (c'est le rôle du cahier).
- Ne pas inventer un « prouvé » sans preuve traçable (script, figure, chiffre).
- Ne pas omettre la §5 : un acquis re-démontré DOIT être signalé comme tel.
- Ne pas effacer les `destination:` ni la §9 lors de la réécriture, et ne pas les
  attribuer soi-même (c'est `/recadrage`).
- Ne pas laisser tomber un acquis parce qu'il ne sert plus l'article : il change
  de destination (B, C ou D), il ne disparaît jamais de l'inventaire.
- Ne pas créer un `etat_des_decouvertes.md` dans un sous-répertoire si un cahier
  existe plus haut (un seul état par projet, à la racine).
