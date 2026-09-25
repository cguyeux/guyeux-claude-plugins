---
name: pistes
description: Research-leads tree (`pistes.md`) of a project — directions and sub-leads with states à faire / en cours / réalisé / abandonné. Use on `/pistes`, `/pistes add "…"`, `/pistes start P1.2`, `/pistes done P1.2`, `/pistes drop P3 "raison"`, or "ajouter une piste", "quelles pistes restent", "cocher cette piste", "abandonner cette piste". Project root = first parent with `cahier_de_labo.md`.
argument-hint: "[read | add \"…\" | start Px | done Px | drop Px \"raison\" | match \"<découverte>\" | locks | hollow]"
---

# pistes — Arbre des pistes de recherche d'un projet

`pistes.md` est l'**arbre persistant des directions** d'un projet : pistes,
sous-pistes, sous-sous-pistes, chacune avec un état. Il existe pour répondre à
une dérive précise : quand on se lance sur une piste, on oublie les autres,
pourtant prometteuses. L'arbre garde la trace de tout ce qui a été envisagé, de
ce qui est en cours, de ce qui est clos et pourquoi.

C'est un **arbre muté localement**, jamais réécrit en bloc (à la différence de
`etat_des_decouvertes.md` qui, lui, est réécrit intégralement). Une piste
`[réalisé]` ou `[abandonné]` n'est **jamais supprimée** : sa présence est la
mémoire des chemins déjà parcourus.

## Localiser le projet

Remonter depuis le répertoire courant, 5 niveaux max ; premier répertoire avec
`cahier_de_labo.md` = racine. Si rien : « Aucun projet structuré trouvé. » et
s'arrêter. Si `pistes.md` n'existe pas : proposer de le créer (en amorçant
depuis les sections « Points ouverts » / « Suite suggérée » du cahier).

## États (imposés)

`[à faire]` · `[en cours]` · `[réalisé]` · `[abandonné]`

## L'intitulé nomme l'OBJET, jamais l'action du jour où la piste s'ouvre

Un titre de piste est relu cent fois pour un contenu lu une fois : c'est lui qui part
dans les récapitulatifs de fin de réponse, dans les points d'étape et dans la mémoire
de qui n'ouvrira pas le détail. Il doit donc porter la QUESTION ou l'OBJET durable, pas
le geste technique du moment, sous peine d'égarer durablement son propre auteur.

Cas mesuré (GIS IA-SUR, 2026-09-11). Une sous-piste intitulée « repointage de
`gis-iasur.duckdns.org` » décrivait en réalité le sort d'une adresse HISTORIQUE, le
site officiel étant `gis-iasur.gclab.fr` depuis des semaines, ce que son contenu disait
correctement. L'intitulé a suffi à faire restituer trois fois de suite, dans une même
conversation, une liste de pistes où le GIS semblait héberger son site chez DuckDNS,
jusqu'à ce que l'utilisateur corrige. Le contenu était juste, le titre mentait.

Règle pratique : au moment d'écrire ou de renommer un en-tête, se demander ce que
comprendra quelqu'un qui ne lira QUE cette ligne dans six mois. Préférer « sort de
l'ancienne adresse X » à « repointage de X », « statut du certificat HTTPS » à
« relance du certificat ». Et quand la mutation d'une piste révèle que son titre ne
correspond plus à son objet, **renommer l'en-tête est une mutation locale légitime**,
à dater et à motiver en une phrase, au même titre qu'un changement d'état.

## Architecture index + détail (`pistes/Px.md`) — économie de tokens

Analogue au fonctionnement d'un skill Claude Code : une description toujours
chargée (le frontmatter), un corps lu seulement quand ce skill précis est
invoqué, des références bundlées lues plus rarement encore. Appliqué ici :

- **`pistes.md`** ne contient qu'un **index** : pour CHAQUE piste majeure,
  l'en-tête `## Px. <titre> [état]`, sa ligne `origine : ... maj : ... MIU :
  ...` (ou la ligne de contexte qui en tient lieu) si elle existe, et un
  pointeur `-> détail : pistes/Px.md`. Rien d'autre — aucune sous-piste, aucune
  prose, aucun historique. Coût de lecture de l'index : quelques lignes par
  piste majeure, quel que soit le volume réel de son contenu.
- **`pistes/Px.md`** (un fichier par piste MAJEURE, dossier `pistes/` à la
  racine du projet, à côté de `pistes.md`) contient le corps COMPLET et
  verbatim de cette piste : toutes ses sous-pistes, sous-sous-pistes,
  historique, addenda. C'est la mémoire de recherche réelle — jamais
  supprimée, jamais réécrite en bloc, seulement mutée localement, exactement
  comme `pistes.md` l'était avant ce découpage.

Ce mécanisme **remplace** l'ancien archivage (`archive_closed_pistes.py` /
`pistes_archive.md`) : puisque TOUTE piste, ouverte ou close, a désormais son
fichier de détail, il n'y a plus de geste séparé à faire à la clôture. Un
projet migré avant ce changement peut avoir un `pistes_archive.md` : le script
de restructuration le lit comme une source de corps supplémentaire (pour les
pistes déjà archivées à l'ancienne), copie leur contenu vers `pistes/Px.md`,
puis **fige** `pistes_archive.md` (note ajoutée en tête, contenu jamais
modifié ni supprimé ensuite — traçabilité historique).

**Déclenchement obligatoire, sur TOUT projet** (pas seulement celui où ce
mécanisme a été introduit), à chaque `/pistes read`, AVANT l'audit de
cohérence — idempotent, no-op si déjà restructuré :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pistes/split_pistes_files.py <chemin>/pistes.md --apply --date-tag AAAAMMJJ
```

Dry-run sans `--apply` pour prévisualiser. Le script fait sa propre sauvegarde
`<pistes.md>.bak_split_<date>` et vérifie l'intégrité (chaque `pistes/Px.md`
byte-identique à son corps d'origine, union des IDs inchangée) avant de
conclure ; échoue bruyamment plutôt que de risquer une perte.

**`/pistes done Px` sur une piste majeure** n'a donc plus besoin d'un
archivage séparé : mettre à jour l'état dans l'index (`pistes.md`) ET dans
`pistes/Px.md` (même tag, même règle de cohérence qu'avant), c'est tout.

## Passage obligé avant toute mutation

**Ne jamais lire l'arbre entier.** Lire `pistes.md` (l'index, cheap) pour
situer l'action dans la hiérarchie des pistes MAJEURES (éviter de dupliquer ou
de contredire une piste déjà présente), puis n'ouvrir QUE le(s)
`pistes/Px.md` réellement concerné(s) par la mutation — jamais les autres.
C'est ce passage, désormais à deux niveaux (index puis détail ciblé), qui
empêche l'oubli et la duplication des sous-pistes tout en gardant le coût
proportionnel à ce qu'on travaille, pas à la taille totale du projet.

## Lire une piste précise (découverte à la demande)

Quand une session travaille ou discute une piste `Px` identifiée dans
l'index : ouvrir directement `pistes/Px.md` (Read, ou `rg` ciblé si seul un
passage précis est utile — ex. `rg -A5 "P16\.2a-sexies-bis\.4" pistes/P16.md`).
Ne jamais charger les autres fichiers `pistes/*.md` sans raison : chacun est
indépendant, et le coût d'une session qui ne touche que `P16` doit rester
celui de `P16.md` seul, pas celui de l'arbre entier.

## Modes

- `/pistes` ou `/pistes read` → **avant** d'afficher, faire l'audit de cohérence
  décrit dans « Audit de cohérence à chaque `/pistes read` » ci-dessous, puis
  afficher l'arbre selon le format décrit dans « Rendu de `/pistes read` » :
  en surlignant les `[en cours]` et les `[à faire]` prioritaires ; résumer en
  une phrase « prochaine piste naturelle ».
- `/pistes add "<libellé>" [sous Px]` → **nouvelle piste MAJEURE** : ajouter sa
  ligne d'index dans `pistes.md` (état `[à faire]`, `origine:`, `maj:` du jour,
  pointeur `-> détail : pistes/Py.md`) ET créer `pistes/Py.md` avec le même
  en-tête. **Sous-piste sous `Px` existante** : n'ouvrir QUE `pistes/Px.md`,
  y ajouter la sous-piste (`origine:`/`maj:` comme avant) ; ne toucher à
  l'index que si l'état de `Px` lui-même doit changer (ex. `[à faire]` →
  `[en cours]`, cf. corollaire 2bis plus bas). Toute piste FEUILLE (sans
  sous-piste) reçoit en plus son **étiquette `[Modèle:effort]`** et son **`amorce :`**,
  voir « Étiquette de routage et amorce » ci-dessous ; l'étiquette se choisit avec
  `python3 ${CLAUDE_PLUGIN_ROOT}/skills/routage/scripts/routage.py estimer "<libellé>"`, jamais au flair.
- `/pistes start Px` → passer `Px` à `[en cours]` dans l'index ET dans
  `pistes/Px.md` (même tag sur les deux), mettre à jour `maj:` sur les deux. Puis
  **afficher l'`amorce :` de la piste** (elle porte le contexte nécessaire pour travailler
  sans re-explorer le projet) et lancer
  `routage.py tache start --piste Px --projet <racine> --etiquette "<tag>" --cout-prevu <bande>`,
  qui enregistre la prévision et signale un décalage entre l'étiquette et le modèle courant.
  Si le décalage est signalé et que le contexte est encore court, proposer `/clear` puis la
  bascule ; s'il est déjà lourd, rester sur place et le dire — une bascule à chaud relit tout
  le contexte sans cache.
- `/pistes done Px` → passer `Px` à `[réalisé]` dans l'index ET dans
  `pistes/Px.md`, mettre à jour `maj:` sur les deux, **et proposer de migrer
  l'acquis** vers `etat_des_decouvertes.md §2` (via `/etat update`). Ne pas
  supprimer la ligne. Lancer aussi
  `routage.py tache done --piste Px --qualite OK|reprise|echec` : il mesure la consommation
  réelle de la piste depuis les transcripts, la compare à la prévision, et rend une ligne à
  reporter telle quelle dans le bilan de séance. `reprise` = il a fallu relancer ou corriger
  substantiellement ; `echec` = la configuration n'a pas suffi. Ces trois verdicts sont ce qui
  fait progresser la grille : les donner honnêtement. Lancer enfin
  `python3 ${CLAUDE_PLUGIN_ROOT}/skills/pistes/impact_done.py Px` (miroir de `/pistes match`, mais à
  l'intérieur du seul projet courant) : il retrouve, parmi les pistes encore `[à faire]`/`[en
  cours]` du même `pistes.md`, celles que la clôture de `Px` recoupe fortement — candidates à
  vérifier pour une réponse, une fermeture ou une caducité, jamais une clôture automatique.
  Afficher les candidats à l'utilisateur, ne rien fermer soi-même sans relire chacun.
- `/pistes drop Px "<raison>"` → passer `Px` à `[abandonné]` dans l'index ET
  dans `pistes/Px.md`, en consignant la raison (modèle nul falsifié,
  hors-sujet, coût trop élevé…). Ne pas supprimer.
- `/pistes match "<découverte>"` → chercher un DESTINATAIRE à un fait, dans
  tout le dépôt, avant de l'écrire où que ce soit. Cf. section dédiée
  ci-dessous.
- `/pistes locks` → les obstacles qui bloquent PLUSIEURS projets à la fois,
  sans qu'on ait à savoir lesquels chercher. Compléteur de file, jamais
  détecteur autonome : cf. la section dédiée et son modèle nul.
- `/pistes hollow` → les projets que l'appariement ne voit pas, et pourquoi.

Dans tous les cas où `Px` est une SOUS-piste (`Px.y`), seul `pistes/Px.md`
est ouvert et muté — l'index ne référence que les pistes majeures, il n'a
donc rien à mettre à jour sauf si l'état de la piste majeure parente change
en conséquence.

Après toute mutation : afficher à l'écran l'état mis à jour de la branche touchée.

## Déclencheurs en langue naturelle

Les formulations libres se rabattent sur les modes ci-dessus : « ajouter une
piste » → `add` ; « quelles pistes restent » (ou « où en sont les pistes ») →
`read` ; « cocher cette piste » → `done` ; « abandonner cette piste » → `drop`.

**Message d'ouverture de session réduit à un seul identifiant de piste** (ex. `P3`,
`AC1`, avec ou sans autre texte) : CG l'emploie pour dire « Fais la piste `<id>` »,
c'est-à-dire commencer directement le TRAVAIL de cette piste, pas seulement la
marquer `[en cours]`. Lire d'abord son détail (`pistes/Px.md` ou la section
correspondante de l'index) comme le préconise « Passage obligé avant toute
mutation » ci-dessous, puis exécuter ce que la piste décrit ; passer par
`/pistes start` fait partie de ce démarrage, elle n'en tient pas lieu.

## Format de l'arbre

`pistes.md` (l'INDEX — jamais de sous-piste ici) :

```markdown
# Pistes — <projet>

Règle : édité par mutation locale (jamais réécrit en bloc), uniquement via
`/pistes`. Une piste [réalisé]/[abandonné] n'est jamais supprimée (traçabilité).
États : [à faire] [en cours] [réalisé] [abandonné].

## P1. <piste majeure> [en cours]
  origine : cahier 2026-06-20    maj : 2026-06-24    MIU : M2 I3 U1
  -> détail : pistes/P1.md

## P2. <piste majeure> [à faire]
  origine : /challenge    maj : 2026-06-24
  -> détail : pistes/P2.md
```

`pistes/P1.md` (le DÉTAIL de cette seule piste — sous-pistes, historique, tout) :

```markdown
## P1. <piste majeure> [en cours]
  origine : cahier 2026-06-20    maj : 2026-06-24    MIU : M2 I3 U1
  I: <ce que ça change — obligatoire dès I≥2> ; U: <dépendance ou date — date obligatoire si U=3>
  - P1.1 <sous-piste> [réalisé] → cf. ÉTAT §2    maj : 2026-06-22
  - P1.2 <sous-piste, a des enfants : pas d'étiquette> [à faire]
    - P1.2.a <sous-sous-piste, FEUILLE> [Sonnet:xhigh] [à faire]    gain attendu : … / coût : …
      amorce : entrée <chemins> ; outil <skill ou script> ; sortie <fichier attendu> ;
        vérif : <test local qui prouve le résultat> ; piège : <ce qui a déjà fait perdre du temps>.
  - P1.3 <sous-piste> [abandonné] — raison : modèle nul falsifié    maj : 2026-06-23
```

## Étiquette de routage et amorce (convention du 2026-09-13)

Toute piste **feuille** (aucune sous-piste sous elle) porte, **avant** son crochet d'état,
une étiquette `[Modèle:effort]` disant sur quelle configuration Claude elle doit être lancée :
`[Haiku]` (pas d'effort sur Haiku), `[Sonnet:low|medium|high|xhigh|max]`, `[Opus:…]`,
`[Fable:…]`, avec un suffixe facultatif `[Sonnet:xhigh +Opus]` pour un advisor. Une piste
majeure qui a des sous-pistes n'en porte pas : c'est le travail atomique qu'on route.

Elle sert à deux choses. D'abord ne pas dépenser un modèle de frontière sur un travail qu'un
modèle plus économe fait aussi bien, ce qui allonge d'autant la semaine de travail avant
blocage du forfait. Ensuite ne pas lancer sur un modèle trop faible un travail dont l'échec
ne se verrait pas : la règle est **la moindre configuration à qualité strictement égale, et
dans le doute la plus forte**. La grille (sept archétypes), les chiffres et les règles de
repli vivent dans `~/.agents/knowledge/model-routing.md` ; le choix se calcule avec
`python3 ${CLAUDE_PLUGIN_ROOT}/skills/routage/scripts/routage.py estimer "<libellé>"`.

L'`amorce :` est le mini-contexte qui permet de lancer la piste **à froid**, après un
`/clear`, sans redécouvrir le projet. Une à quatre lignes indentées sous la piste :
entrées (chemins réels), outil ou skill à utiliser, sortie attendue, critère de vérification
locale, piège connu. Ce n'est pas un résumé de la piste : c'est ce qu'il faudrait sinon
retrouver en dix appels d'outil, c'est-à-dire précisément ce qui coûte cher.

`status.py` retire l'étiquette du libellé, l'expose en dernière colonne du TSV et en champ
`etiquette` du JSON, et son audit compte les feuilles ouvertes qui n'en ont pas. Ce compteur
est **tolérant** : on étiquette à la réouverture d'un projet, jamais en masse.
`routage.py etiqueter <projet>` propose les étiquettes manquantes dans
`<projet>/pistes_etiquettes_proposees.md`, à relire avant `--apply`.

## Édition hors mode (résultat ajouté en cours de session)

En pratique, une piste ne se clôt pas toujours par un `/pistes done` explicite :
souvent, un résultat (« RÉALISÉ », « FAIT », « ✅ », « déployé et vérifié »…) est
ajouté au corps d'une piste au fil d'une session de travail normale, par une
édition directe de `pistes.md`. C'est légitime, mais **le tag d'état entre
crochets en tête de cette même piste/sous-piste doit être corrigé dans la MÊME
édition** — jamais laissé pour plus tard. Un tag qui dit `[à faire]` ou
`[en cours]` alors que le texte juste en dessous dit « FAIT » est la
désynchronisation la plus fréquente de ce fichier ; elle passe inaperçue
précisément parce qu'elle n'a jamais lieu via `/pistes done`, donc jamais sous
l'œil du passage de relecture ci-dessus.

Corollaire : quand une sous-piste passe à `[réalisé]` ou `[abandonné]` et que
c'est désormais le cas de **toutes** ses sœurs sous la même piste parente,
recalculer et corriger l'état de la piste parente (`## Px. ... [état]`)
**immédiatement**, dans la même passe — ne pas attendre une relecture
ultérieure. C'est la deuxième désynchronisation la plus fréquente : l'en-tête
`## Px` fige l'état constaté à sa création et n'est plus jamais revisité une
fois que le travail se poursuit sous-piste par sous-piste.

Un hook `Stop` (`~/.claude/settings.json`) rattrape les deux cas ci-dessus s'ils
sont oubliés en fin de session, mais seulement pour les lignes touchées PENDANT
la session courante — il ne fait pas d'audit rétroactif du fichier entier. Ne
pas compter dessus pour éviter la vigilance ci-dessus : il bloque après coup,
corriger tout de suite coûte moins cher.

## Audit de cohérence à chaque `/pistes read`

Le hook `Stop` et la vigilance d'édition (section précédente) ne rattrapent que
les lignes touchées PENDANT une session. Ils laissent donc passer un cas
fréquent : une piste `[en cours]` dont TOUTES les sous-pistes ont fini par
passer `[réalisé]`/`[abandonné]` au fil de plusieurs sessions, sans qu'aucune
passe de relecture ne recalcule son en-tête. Une piste ne doit jamais rester
`[en cours]` sans qu'au moins une sous-piste directe soit encore `[à faire]`
ou `[en cours]` — ni, à l'inverse, sans sous-piste du tout (une piste sans
enfant qui n'est ni `[à faire]` ni close est une piste dont personne n'a
tranché l'état).

**Sous l'architecture index + détail, cet audit se fait piste OUVERTE par
piste ouverte, jamais sur tout l'arbre d'un coup** : depuis l'index
`pistes.md`, repérer les pistes majeures `[en cours]` ; pour CHACUNE, `rg
"^\s*(-\s+P\d+\.|##)"` (ou équivalent) sur son seul `pistes/Px.md` pour
extraire juste les en-têtes et états des sous-pistes — pas besoin de charger
la prose complète pour ce contrôle, l'état des sous-pistes suffit. N'ouvrir
le fichier en lecture complète (Read) que pour une piste où une incohérence
est confirmée et doit être corrigée en connaissance de son contexte réel.
Les pistes CLOSES (`[réalisé]`/`[abandonné]`) n'ont, par construction, plus
rien à auditer ici : ne pas ouvrir leur `pistes/Px.md` pour ce passage.

Donc, pour chaque piste majeure `[en cours]` de l'index : vérifier qu'elle a
au moins une sous-piste directe encore ouverte dans son fichier de détail.
Pour chaque piste en défaut, trancher — ne jamais la laisser telle quelle :

- **Si le corps ne documente plus aucun objectif restant** (toutes les
  sous-pistes closes, rien dans le texte n'indique une suite) → la repasser
  `[réalisé]` (ou `[abandonné]` si pertinent), dater `maj:` du jour, et
  proposer la migration de l'acquis vers `etat_des_decouvertes.md §2` comme
  le ferait un `/pistes done` explicite.
- **Si un objectif reste identifiable mais non formalisé** (un sous-objectif
  continu comme une veille, une suite mentionnée dans le corps mais jamais
  numérotée, une décision en attente) → ajouter une nouvelle sous-piste
  `[à faire]` qui l'explicite (avec `origine:` = « audit /pistes read » et
  `maj:` du jour), plutôt que de laisser la piste parente `[en cours]` sans
  rien dessous qui le justifie.

Cette mutation suit les mêmes règles que toute édition hors mode : jamais de
suppression, jamais de réécriture en bloc, seulement les lignes concernées
dans `pistes/Px.md` — et si l'état de la piste MAJEURE change en conséquence,
répercuter le même tag sur sa ligne d'index dans `pistes.md`. Elle doit être
reflétée dans l'affichage qui suit, pas faite après coup.

## Établir l'état courant : `status.py`, jamais un `grep` (obligatoire)

**Avant tout affichage, tout audit et toute réponse mentionnant les pistes ouvertes,
exécuter `python3 <skill>/status.py <projet> --open` et partir de sa sortie.** Ne
jamais construire la liste des pistes ouvertes par un `grep "[à faire]"` ou
`grep "[en cours]"` sur `pistes.md` / `pistes/Px.md`.

La raison est mécanique et a produit trois listes fausses d'affilée le 2026-09-05 sur
`nucs_deletion_mutators` : ces fichiers sont **append-only et narratifs**. Le corps
d'une piste raconte l'histoire d'autres pistes, et une phrase comme « nouvelle
sous-piste ouverte : **P2.15.2.1** [à faire] », écrite dans le récit d'un tour de
`/mtbc-prospect`, reste dans le fichier pour toujours — même une fois P2.15.2.1
réalisée, cinq jours plus tard, par une note ajoutée plus bas. Un `grep` remonte ces
traces historiques exactement comme un état courant et rend des pistes closes pour
ouvertes. Deux pièges de forme s'y ajoutent, tous deux présents dans ce dépôt : un
marqueur d'état peut être **coupé par un retour à la ligne** (`[réalisé, 2026-09-02 —
verdict\n NUANCÉ...]`) et peut porter du **gras ou une casse haute**
(`[**RÉALISÉ, ...**]`).

`status.py` applique la seule règle qui sépare définition et prose : une piste n'est
définie que par un titre de section `## Px.` ou par un item de liste dont le PREMIER
token est son identifiant, et son état est le premier marqueur rencontré à partir de
là ; tout marqueur ultérieur est de la prose.

- `status.py <projet>` — TSV `id / état / fichier:ligne / libellé`, arbre complet.
- `status.py <projet> --open` — seulement `[à faire]`, `[en cours]` et les pistes
  dont l'état n'est pas déclaré (défaut de registre à combler).
- `status.py <projet> --json` — même chose, exploitable par un autre outil.
- `status.py <projet> --audit` — sur stderr, les défauts de registre :
  les mentions en prose qui **contredisent** l'état courant (à ignorer à la lecture,
  jamais à corriger : ce sont des faits datés) ; les pistes dont la **clôture n'a
  jamais été répercutée sur la ligne de définition** (heuristique, à vérifier à la
  main puis à corriger par `done`, le corps d'une piste « porte » narrant
  légitimement l'état d'autres pistes) ; les pistes **ABSENTES du registre pour
  cause de forme non conforme** ; et les **états hors nomenclature**.
- `status.py <projet> --audit-json` — les mêmes contrôles en JSON sur stdout
  (compteurs destinés à un hook ; `--audit` n'en est qu'un affichage).
- `audit_signals.py <projet> --quiet` — silencieux si le registre est sain, sinon une
  ligne par contrôle non nul. `--diff FIC` ne signale que les hausses depuis un
  instantané, `--pistes-ouvertes` rend le bloc de démarrage. Cf. « Le passage de
  l'audit est MÉCANIQUE » plus bas.

Les deux derniers contrôles ont été ajoutés le 2026-09-06, après un audit où ils ont
trouvé chacun un cas réel, et ils traitent un mode d'échec plus grave que les deux
premiers : là où une prose périmée fait seulement paraître une piste close plus
longtemps qu'elle ne l'est, ceux-ci font disparaître une piste **entièrement**, sans
produire aucune ligne dans aucune liste.

- **Forme non conforme.** Une définition écrite `  **P5.1** [réalisé] — ...`, en gras
  hors item de liste, n'est pas reconnue. Sur `nucs_deletion_mutators`, les cinq
  sous-pistes de `P5` l'étaient toutes : `P5` apparaissait donc comme une piste
  majeure `[en cours]` **sans aucune sous-piste**, l'audit de cohérence ne pouvait
  pas conclure, et `recadrage_signals.py` la classait en tête du classement ACTION
  avec la seule note `U2` du projet — alors qu'elle était close depuis la veille. Un
  défaut de FORME se déguise en défaut de PRIORITÉ. Corriger la forme de la ligne,
  jamais l'état qu'elle porte.
- **État hors nomenclature.** `[partiellement réalisé]` est honnête pour un lecteur
  humain mais n'appartient pas aux quatre états imposés : le filtre `--open` le rejette
  sans que la piste entre pour autant dans les closes. Elle n'est dans AUCUNE des deux
  listes. Trancher vers un des quatre états, en décrivant la nuance dans le corps.
- **Piste majeure sans aucun état déclaré** (contrôle ajouté le 2026-09-08). Une
  étiquette entièrement libre — `[CLOSE POSITIVEMENT 2026-08-22]`, `[DÉPLOYÉ, RECETTE
  EN ATTENTE]`, `[CAUSE ÉTABLIE, CORRECTIF PRÊT, NON DÉPLOYÉ]` — ne contient aucun des
  quatre mots, donc `--open` la rend TOUTES par prudence et le contrôle « hors
  nomenclature » ne la voit pas (il exclut explicitement l'état non déclaré). Sur
  `predictops`, 24 pistes majeures sur 69 étaient dans ce cas et `--open` en annonçait
  32 ouvertes au lieu de 11 : une liste fausse par excès, exactement ce que ce script
  existe pour empêcher. Le contrôle distingue celles dont l'étiquette **annonce une
  clôture en toutes lettres** (donc closes mais comptées ouvertes) de celles qui sont
  seulement indécidables. Cas fondateur : `P67`, dont l'en-tête annonçait « CORRECTIF
  PRÊT, NON DÉPLOYÉ » **des deux côtés** alors que son corps consignait le déploiement
  de la veille — le désaccord index/détail ne le voyait donc pas non plus, et un faux
  feu vert de déploiement a été demandé à l'utilisateur sur cette base. Corriger en
  posant l'état EN TÊTE de l'étiquette, le qualificatif restant juste après :
  `[réalisé, CLOSE POSITIVEMENT 2026-08-22]`.

### Déclarer une clôture ASSUMÉE : la note `**Assumé**` (2026-09-09)

Une piste majeure peut légitimement rester close en portant une sous-piste ouverte, quand
celle-ci est une **option coûteuse et conditionnelle délibérément non lancée**, et non un
oubli. Le contrôle « majeure close portant une sous-piste ouverte » le reconnaît désormais,
à deux conditions cumulatives :

1. l'en-tête de la piste majeure, dans son `pistes/Px.md`, porte une note en **gras**
   commençant par `**Assumé**` ;
2. cette note **nomme** la ou les sous-pistes concernées.

```markdown
## P21. <titre> [réalisé, 2026-09-08 — TRANCHÉ : négatif, aucun aDNA Bovis n'existe]
  maj : 2026-09-08
  **Assumé** : la piste MAJEURE est close (question aDNA tranchée) ; P21.1 reste
  `[à faire]` en dessous DÉLIBÉRÉMENT, comme option coûteuse et conditionnelle non
  lancée, pas comme un oubli — cf. sa propre note de coût.
```

Le cas est alors rendu en **CONTEXTE**, jamais compté comme défaut. Une note vague qui ne
nomme aucune sous-piste ne vaut pas déclaration : sans cette exigence, une note générale
absoudrait d'un coup toutes les sous-pistes ouvertes de la racine, y compris celles
apparues des mois plus tard.

**Pourquoi ce correctif existe.** Le hook `Stop` demande de « consigner pourquoi c'est
assumé », mais consigner ne décrémentait aucun compteur : la sonde ne savait pas lire la
justification, et l'alerte était **ineffaçable**. Mesuré sur `mtbc/Rv2566` le 2026-09-09,
trois occurrences de la même fausse alerte en une journée, sur les deux mêmes pistes, deux
séances distinctes ayant chacune dû l'instruire de zéro. Un contrôle qui reproche
indéfiniment un cas justifié cesse d'être lu, ce que l'en-tête du hook identifie lui-même
comme son principal mode d'échec.

**Ce qui n'a PAS changé** : une majeure close dont la sous-piste ouverte n'est pas déclarée
reste un défaut, et c'est toujours le sens d'erreur le plus coûteux. La note ne dispense pas
de trancher, elle déclare qu'on a tranché.

- **Sous-piste VIVANTE enterrée sous une piste majeure close** (contrôle ajouté le
  2026-09-08). Le contrôle précédent ne regarde que les majeures, et c'est délibéré : sur
  `predictops`, 0 majeure sans état mais 112 **sous**-pistes, dont 83 sous une majeure déjà
  close. Leur réclamer un état à toutes ferait du bruit sans fin. Leur faire HÉRITER de l'état
  du parent a été testé sur un échantillon stratifié puis **réfuté** : `P19.2` porte
  « [ÉCHEC, CORRECTIF À REPRENDRE] » sous un `P19` réalisé, `P34.1bis` attend une coordination
  externe, et `P12.4` (« Leçon méthodo générale ») n'est ni ouverte ni close mais **n'est pas
  une direction de travail** — troisième catégorie que les quatre états ne couvrent pas.
  Hériter aurait marqué closes des pistes dont le libellé dit l'inverse : une liste fausse par
  DÉFAUT, la pire des deux. Le contrôle ne compte donc que le cas actionnable, la sous-piste
  muette dont l'étiquette annonce une réserve ouverte (`MOTS_RESERVE`). Rendement mesuré :
  4 sur 83. Les autres sont rendues en contexte, comptées et non listées.

Corollaire de lecture, qui vaut au-delà de ces deux contrôles : **lire aussi la sortie
complète de `status.py`, pas seulement `--open`**. Un décompte par état
(`status.py <projet> | awk -F'\t' '{print $2}' | sort | uniq -c`) tient en une ligne et
rend visible tout état aberrant noyé dans une centaine de pistes closes ; c'est lui qui
a révélé le cas `[partiellement réalisé]`.

Faire tourner `--audit` à chaque `read` et traiter ce qu'il remonte : c'est le seul
garde-fou contre un registre qui dérive silencieusement, et il a immédiatement trouvé
deux clôtures jamais répercutées sur ce projet (`P1.4`, porte 1 franchie le
2026-08-31 mais encore `[à faire]` ; `P2.2b`, close le 2026-08-27 mais encore
`[en cours]`).

### Le passage de l'audit est MÉCANIQUE, plus seulement prescrit (2026-09-08)

La consigne ci-dessus a existé seule pendant deux jours, et pendant ces deux jours
personne ne l'a appliquée : l'en-tête de `P67` a continué d'annoncer « CORRECTIF PRÊT,
NON DÉPLOYÉ » alors que son corps consignait le déploiement de la veille, et un faux
feu vert de mise en **production** a été demandé à l'utilisateur sur cette base. Le
défaut n'était pas l'absence d'outil — `--audit` portait déjà le contrôle — mais
l'absence de **déclenchement**. Une consigne dans un SKILL.md n'est pas un mécanisme.

Deux hooks lancent désormais l'audit sans que personne ait à y penser, via
`audit_signals.py` (même répertoire), qui appelle `status.py` et n'en réimplémente
aucun contrôle :

- **`SessionStart`** (`hooks/session_context.sh`) — `--quiet` : une ligne par contrôle
  non nul, **rien du tout** si les huit contrôles à zéro attendu sont à zéro. Il dit
  le défaut AVANT qu'on s'appuie sur un état périmé, ce qui est exactement le moment
  où `P67` aurait dû être rattrapé. Il dépose au passage l'instantané des compteurs.
- **`Stop`** (`hooks/pistes_audit_stop.sh`) — `--diff` contre cet instantané : bloque
  la fin de session **uniquement** si un compteur a MONTÉ pendant la séance. Le stock
  ancien ne déclenche jamais rien.

La distinction stock / dégradation porte tout le dispositif. Un contrôle qui reproche
à chaque fin de session un défaut ancien et connu cesse d'être lu en deux jours — c'est
le mode d'échec le plus probable de ce garde-fou, avant le faux négatif (mesuré sur
`completude_cahier`, 60 % de bruit avant son crible). D'où aussi le champ
`zero_attendu` de `SECTIONS_AUDIT` : deux contrôles portent un bruit structurel déjà
instruit (le cahier append-only nomme des identifiants qui n'ont jamais été des pistes)
et sont rendus comme contexte, jamais comme anomalie.

Corollaire pour qui modifie ces contrôles : `status.py --audit-json` rend les mêmes
compteurs en JSON, et `collecte_audit()` est la seule source. **Ne jamais
réimplémenter un contrôle côté hook** : il divergerait du texte au premier ajout.

Même leçon appliquée au hook lui-même. La liste de pistes ouvertes qu'il injecte au
démarrage venait d'un `grep -E '\[(en cours|à faire)\]'` sur `pistes.md`, et elle
rendait **3 pistes là où `predictops` en portait 12** : l'expression exigeait le
crochet fermant juste après l'état (donc `[en cours, backend livré]` lui échappait) et
était sensible à la casse (donc `[EN COURS]` aussi). Poser l'état en tête de
l'étiquette, ce qui est le correctif recommandé ci-dessus, a mécaniquement aggravé ce
trou. Une piste ouverte absente du contexte de démarrage est une piste oubliée : le
hook passe maintenant par `audit_signals.py --pistes-ouvertes`.

### Contrôle bidirectionnel cahier ↔ détail ↔ index (ajouté le 2026-09-07)

Les quatre contrôles précédents ne regardent que la cohérence **interne** du
registre : ils comparent les pistes entre elles, à l'intérieur des mêmes
fichiers. Ils sont donc aveugles aux deux dérèglements qui, en une semaine, ont
fait perdre de la mémoire de recherche sur `annotation_mtbc` — et aucun des deux
ne lève d'erreur, parce que chacun laisse un registre parfaitement cohérent avec
lui-même.

- **Sens 1, le détail perd son contenu** pendant que l'index continue de résumer
  un travail réellement fait. `pistes/P42.md` réduit à un stub de 4 lignes ;
  `pistes/P40.md` écrasé par une version ANTÉRIEURE de lui-même (P40.1 encore
  `[à faire]` alors que le cahier atteste P40.2 à P40.7). Le critère employé
  alors — « contenu utile byte-identique au bloc d'index » — n'a vu ni l'un ni
  l'autre : le premier avait été examiné puis classé faux positif, le second
  n'était pas un stub. Le seul test qui tranche est la confrontation au
  **cahier append-only**, qui est la seule source capable de dire quelles
  sous-pistes ont existé : toute sous-piste `Px.y` nommée par une entrée de
  cahier doit se retrouver dans `pistes/Px.md`.
- **Sens 2, l'index ment** sur un fichier qu'on a précisément évité d'ouvrir.
  Une session met `pistes/P37.md` à jour sans toucher la ligne d'index, qui
  reste sur l'état de la veille. C'est le défaut que l'architecture index +
  détail rend le plus coûteux, puisque son intérêt même est de dispenser de lire
  le détail.

`status.py --audit` porte donc deux contrôles supplémentaires, tous deux
signalants et jamais correctifs :

- **complétude « cahier → détail »** : les sous-pistes nommées dans
  `cahier_de_labo*.md` et introuvables là où elles devraient être. Trois
  gravités, séparées à l'affichage parce que les mélanger rend le contrôle
  illisible : **introuvable dans tout le registre** (le vrai signal — soit une
  perte, soit une sous-piste numérotée dans le récit du cahier et jamais portée
  à l'arbre ; l'outil ne tranche pas entre les deux) ; **définie ailleurs**
  (rangée sous une autre piste majeure par un redécoupage `/recadrage` qui ne
  renumérote pas — rien à faire, et c'est le gros du volume, donc agrégé par
  destination) ; **restée dans l'archive figée ou l'index** (migration
  index+détail inachevée : rapatrier le corps). Un identifiant dont même la
  piste majeure est étrangère au registre est listé à part, en une ligne : c'est
  un renvoi à un autre projet ou une collision avec la numérotation du dépôt
  parent, donc informationnel.

  Deux règles de fabrication, apprises en mesurant les faux positifs du premier
  jet (60 signalements sur `annotation_mtbc`, dont ~90 % de bruit). D'abord,
  **cribler ce qui ressemble à un identifiant sans en être un** : un chemin de
  fichier (`pistes/P8.md`, `P2.md.bak`), une plage (`P1-P18`, `P16.17-24`), un
  gabarit (`…-bis.x`), un mot collé (`P2.14.1-style`), un zéro non significatif
  (`P2.09`). Ensuite, **chercher la DÉFINITION, jamais la mention** : une piste
  citée en passant dans la prose d'un autre fichier n'y a pas son corps, et s'y
  fier fait annoncer le mauvais fichier de destination.
- **désaccord index ↔ détail** : pour chaque piste majeure, l'état des deux
  faces (comparé sur le mot d'état, un qualificatif n'étant pas un désaccord) et
  la date `maj :` la plus récente de chacune. La sortie dit **laquelle est en
  retard**, elle ne tranche pas : le détail fait foi sur le contenu, l'index sur
  la vue d'ensemble, et seul l'auteur sait lequel des deux a raison dans un cas
  donné.

Traiter un signalement de complétude ne se fait **pas** en recopiant l'index
dans le détail : le corps se reconstitue depuis les entrées de cahier qui
nomment la sous-piste, comme cela a été fait pour P40 et P42 le 2026-09-05.

**Et il commence toujours par instruire, jamais par conclure à la perte.**
Sur `predictops` le 2026-09-08, les 13 signalements ont donné zéro perte. Cinq
étaient un défaut de FORME — écrites `- P35.4. Titre`, point séparateur compris,
elles étaient invisibles à `RE_ITEM` alors qu'elles figuraient au complet dans
leur fichier ; corrigé depuis dans le parseur, mais le réflexe reste de vérifier
d'abord si l'identifiant est présent dans son fichier sous une autre forme. Les
huit autres étaient des faux positifs d'une famille que le criblage ne peut pas
attraper : le nom d'un SCRIPT (`P1.16`, la déduplication ATMO), des pistes
d'AUTRES projets citées en renvoi (`P5.8.a` d'OptimOps), une divergence de
notation entre cahier et registre (`P11.4a` contre `P11.4(a)`), un suffixe de
version d'artefact (`P59.4bis-v1`, seul cas désormais filtré). Annoncer « de la
mémoire de recherche possiblement perdue » sur la foi du compteur, avant d'avoir
ouvert les fichiers, fait paniquer pour rien et coûte la confiance dans l'audit :
le message dit « deux lectures, à trancher à la main », et c'est à prendre au
mot.

## Rendu de `/pistes read`

Avec un arbre qui grossit (plusieurs dizaines de pistes sur un projet mûr),
un dépliage intégral est illisible. L'affichage doit lire comme un petit
document soigné, pas comme un dump du fichier brut : un titre en tête
(`## Pistes actives — <projet>`), un bloc visuellement distinct pour les
pistes closes et un pour les pistes ouvertes (séparateur `---` ou sous-titre
entre les deux), les identifiants de piste mis en évidence (`**P3**`) plutôt
que noyés dans la phrase, et un alignement constant à l'intérieur de chaque
liste (numéro → libellé court → ce qui bloque). Structurer précisément
ainsi :

1. **Une ligne de comptage** en tête : nombre de pistes majeures par état
   (ex. « 22 pistes majeures : 15 closes, 6 en cours, 1 à faire »).
2. **Les pistes closes** (`[réalisé]`/`[abandonné]` sans aucune sous-piste
   encore ouverte) : une seule ligne chacune, juste le numéro, le titre et
   l'état — jamais le détail des sous-pistes déjà closes. Les grouper dans
   un seul bloc compact, clairement séparé des pistes ouvertes.
3. **Les pistes ouvertes** (`[en cours]` ou `[à faire]`) : une section par
   piste, avec son état en tête, puis SEULEMENT ses sous-pistes encore
   ouvertes, chacune réduite à une ligne (numéro, libellé court, ce qui
   bloque ou la prochaine action concrète) — pas l'historique ni les
   sous-pistes déjà closes en dessous. Le détail complet reste dans
   `pistes/Px.md` ; l'affichage pointe, il ne recopie pas.
4. **Une phrase de clôture** : la « prochaine piste naturelle », qui doit se
   déduire de ce qui vient d'être listé (pas une piste absente de l'affichage).
5. **Clôture obligatoire — prochaines pistes à investiguer.** Toujours
   présente, immédiatement après le point 4, sur sa propre ligne :

   `Prochaines pistes à investiguer : P10.3, P11-a-ii, P12.7.1, ...`

   - 5 à 10 identifiants de pistes ou sous-pistes `[à faire]` ou
     `[en cours]`, séparés par des virgules, dans le format de leur propre
     numérotation (`P10.3`, `P11-a-ii`, `P12.7.1`…).
   - Exclure toute piste dont la prochaine action concrète relève de la
     **paillasse** (manipulation physique : PCR, extraction, séquençage,
     culture…) ou d'un **envoi de mail** (solliciter un collaborateur, un
     coauteur, une base externe par contact humain) : ce sont des pistes qui
     ne peuvent pas être lancées séance tenante, à la différence des autres.
   - Mélanger délibérément des pistes à fort impact (haut du classement
     PROMESSE ou ACTION issu de la notation MIU, cf. section suivante) et des
     pistes rapides à faire (coût faible, gain immédiat même si M ou I bas)
     — jamais l'un sans l'autre.
   - Si moins de 5 pistes satisfont ces critères, lister ce qu'il y a et le
     signaler explicitement plutôt que de compléter avec des pistes de
     paillasse ou d'envoi de mail déguisées.
6. **Avis sur la relance d'un moteur de découverte.** Une à deux phrases,
   juste après la liste précédente : le classement MIU et l'audit de
   cohérence donnent-ils à penser qu'il faut relancer `/mtbc-prospect`
   (réserve de pistes divergentes épuisée, plusieurs pistes closes sans
   piste neuve pour les remplacer) ou un `/lit-review <sujet>` ciblé (un
   sous-champ mentionné dans le corps d'une piste mais jamais couvert par une
   revue) ? Nommer le sujet précis si un `/lit-review` est recommandé. Écrire
   explicitement « rien à signaler de ce côté » si ni l'un ni l'autre n'est
   indiqué, plutôt que de forcer une recommandation à chaque passage.

But : que l'utilisateur voie en quelques secondes ce qui est réellement actif,
sans avoir à traverser l'historique de ce qui est déjà fait — et reparte avec
une liste concrète de ce qu'il peut lancer tout de suite.

## Notation MIU et classement (à chaque `/pistes read`)

Une piste majeure porte, sur sa ligne `origine:`/`maj:`, une note
`MIU : M<0-3> I<0-3> U<0-3>` — **m**aturité (idée nue → prêt à rédiger),
**i**mportance (anecdotique → publiable en soi), **u**rgence (aucune → échéance
ferme datée). Barème complet, garde-fous anti-inflation (une I≥2 exige une clause
`I:` qui dit ce que ça change ; une U=3 exige une date) et procédure : skill
`recadrage`, Phase 3quater.

Après l'audit de cohérence et avant l'affichage, exécuter :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/recadrage/recadrage_signals.py --priorites
```

et intégrer sa sortie à l'affichage : le classement **ACTION** (urgent d'abord,
puis important ET mûr) remplace avantageusement l'énumération à plat des pistes
ouvertes, et le classement **PROMESSE** (importance élevée, maturité faible) doit
être affiché **séparément** — un pari n'a jamais l'air prioritaire face à un
chantier ouvert, donc le fondre dans un classement unique revient à garantir
qu'aucun ne sera lancé.

Les pistes ouvertes non notées sont comptées par le script. En noter deux ou
trois à chaque passage suffit ; ne jamais noter rétroactivement les pistes
closes, c'est du travail sans lecteur. Sur `/pistes add`, proposer un MIU dès la
création — c'est le moment où l'on sait le mieux ce que vaut l'idée.

## Restructuration : fusionner ou redécouper (à surveiller à chaque `read`)

L'arbre se dégrade toujours des deux mêmes façons, et l'audit de cohérence des
tags ne les voit pas :

- **Deux pistes qui posent la même question** (même lignée, même gène, même
  locus ; ou l'une est un test de l'autre) doivent être **fusionnées**, l'une
  devenant sous-piste de l'autre. Séparées, elles produisent deux écrits qui se
  citent mal, ou un écrit qui oublie la moitié de son propre argument. Attention :
  partager une *méthode* n'est pas poser la même question.
- **Une piste dont le titre a besoin d'un « et » pour être vrai** en pose deux :
  la **redécouper**. Autres signaux : ≥ 8 sous-pistes directes, ou deux groupes
  de sous-pistes sans dépendance mutuelle.

Les deux gestes sont non destructifs (rattachement noté, sous-pistes recopiées
avec leur `origine:` d'origine, rien de supprimé). Sous l'architecture index +
détail : une FUSION déplace du contenu entre deux `pistes/Px.md` (et retire la
ligne d'index de la piste absorbée, jamais son fichier) ; un REDÉCOUPAGE crée
un nouveau `pistes/Py.md` et sa ligne d'index. Procédure détaillée : skill
`recadrage`, Phase 3ter. Signaler la restructuration souhaitable dans le
commentaire de sortie plutôt que de l'exécuter d'office : elle change la lecture
de l'arbre, et c'est une décision.

## Chercher un destinataire : `/pistes match` (carrefour inter-projets)

Un arbre de pistes répond à « que reste-t-il à faire dans CE projet ». Il ne
sait pas dire si un fait qu'on vient d'établir répond à la question ouverte
d'un projet VOISIN. C'est le trou que ce mode comble : avant d'écrire une
découverte quelque part, chercher qui la cherchait déjà.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pistes/carrefour.py match "<le fait, en une phrase>"
```

Le script indexe, sur tout le dépôt, ce que chaque projet CHERCHE (pistes
ouvertes, « incertain », « angles morts »), ce qu'il SAIT (acquis), ce qu'il a
déjà ÉCARTÉ (réfuté) et — pour les projets archivés — la cause qui l'a clos. Il
apparie un texte libre par BM25 avec un bonus sur les identifiants du domaine
(L4.15, Rv0007, IS6110, RD303). Une requête coûte quelques dixièmes de seconde
et une vingtaine de lignes, là où lire les registres du dépôt coûterait des
dizaines de milliers de tokens. L'index vit dans `.carrefour/` à la racine du
dépôt : dérivé, régénérable, **jamais lu par un agent**, hors suivi de version,
et régénéré tout seul dès qu'une source a bougé (contrôle par mtime, aucune
lecture de fichier).

Colonnes de sortie : score relatif au meilleur candidat, marque de statut
(` ` vivant, `C` clos, `A` abandonné), projet, type d'item, référence de la
piste ou de la section, début du texte, puis les trois tokens qui ont décidé
du rapprochement — cette dernière colonne est là pour juger le match, pas pour
le décorer. Sous-commandes : `reindex` (forcé), `stats` (volumétrie et dette
de causes de clôture), `overlap` (paires de projets dont l'objet se recouvre,
matière du verdict FUSIONNER), `locks` et `hollow` (ci-dessous).

**Repli sur le cahier, pour les projets qu'aucun registre ne fait parler.**
Un projet sans `pistes.md` ni `etat_des_decouvertes.md`, ou dont le registre
n'est que du gabarit `/init-project` jamais rempli, est invisible à
l'appariement — et son silence se lit à tort comme « ce projet ne cherche
rien ». Mesuré sur `mtbc/` le 2026-08-26 : **74 projets sur 127**, dont les plus
productifs du dépôt. Pour ceux-là, et pour eux seuls, l'index se rabat sur
l'intitulé du projet et les questions ouvertes des 4 dernières entrées de leur
cahier. Le cahier reste une source de **second rang** : il est append-only, donc
un point ouvert y vieillit sans que rien ne l'invalide. D'où le type distinct
(`question-cahier`, `objectif-cahier`) et la date portée en référence : ils
disent au lecteur que la fraîcheur n'est pas garantie et qu'il doit revérifier
avant d'agir. Un registre tenu n'est jamais supplanté par le cahier.

`hollow` liste les projets muets et distingue leur cause — `gabarit-seul`
(scaffoldé, jamais renseigné) ou `sans-registre` (antérieur à la convention des
cinq artefacts) — et marque `⚠ MUET` ceux dont même le cahier ne donne rien. La
dette est ainsi nommée plutôt que masquée par le repli qui la compense.

**Verrous partagés : `locks`.** Un obstacle qui bloque plusieurs projets à la
fois vaut d'être vu, parce qu'un investissement méthodologique s'y amortit
autant de fois qu'il y a de projets bloqués. Ce qui sépare un verrou d'un thème
n'est pas le sujet mais la TOURNURE : sur `mtbc/`, 35 projets *parlent* de
datation, 9 en sont *bloqués*. Le tri se fait donc sur un lexique d'empêchement
(« insuffisant », « ne permet pas », « faute de », « aucune datation encore
produite »), évalué à l'indexation sur le texte complet de l'item — le titre
d'une piste dit rarement ce qui la bloque, c'est son corps qui l'avoue.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pistes/carrefour.py locks --null 200
```

**À présenter pour ce qu'il est, pas plus.** Le modèle nul (`--null`, tirages de
même effectif dans les questions ouvertes) donne p ≈ 0,32 sur `mtbc/` : le
NOMBRE de verrous détectés n'excède pas le hasard. `locks` n'est donc pas un
détecteur de verrous inconnus, c'est un **compléteur de file pour un verrou déjà
nommé** : lancé sur `mtbc/`, il a ajouté 4 projets qu'une passe manuelle
attentive avait manqués, tout en en ratant 4 qu'elle avait vus. La mesure ne
remplace pas la lecture, elle trouve ce que la lecture rate — et réciproquement.
Deux faux positifs à connaître : la négation d'un empêchement (« n'empêche pas
le tip-dating »), désormais filtrée, et l'homonymie de vocabulaire (une « fuite
temporelle » de benchmark d'apprentissage n'est pas un défaut d'horloge), que
seul un lecteur peut écarter.

**Trois garde-fous, à appliquer sans exception.** Le risque de cet outil n'est
pas de manquer un rapprochement, c'est d'en fabriquer trop : 70 registres
transformés en boîtes de réception.

1. **Un match n'est pas une décision.** Le script rend des candidats classés,
   jamais un verdict. Lire le `pistes/Px.md` du candidat avant d'écrire chez
   lui : le score dit que deux textes partagent du vocabulaire, pas qu'ils
   posent la même question.
2. **Écrire chez un voisin lui coûte du travail.** N'y écrire que si le fait
   est ACTIONNABLE pour lui — il change ce qu'il ferait ensuite. Jamais « pour
   information ». Et ne jamais fermer soi-même la piste d'autrui : on lui
   apporte une réponse, on ne décide pas à sa place qu'elle suffit.
3. **Un recouvrement élevé ne prouve rien.** Le doublon le mieux classé du
   dépôt (`La4` ~ `La4-phylogenie`, 0,43) est parfaitement sain et assumé, sa
   division du travail est écrite ; et les scores qui le DÉPASSENT sont des
   projets `Rv####` distincts qui partagent seulement le texte de cadrage de
   la passe de seed qui les a créés. La mesure capte la proximité de
   vocabulaire, jamais la pathologie du doublon. Un profil maigre est en outre
   dégénéré : deux projets réduits au même « Pointeur croisé : … » ont sorti
   0,78 avant que les items de repli n'entrent dans le profil.

**Projets archivés.** Ils restent appariables par ce qu'ils savent et par ce
qui les a clos, jamais par ce qu'ils cherchaient (`--include-closed` pour
lever cette restriction). Chaque projet de `clos_soumis/` ou `clos_abandonne/`
porte un `ARCHIVE_NOTE.md` dont l'en-tête normalisé est machine-lisible :

```markdown
    clôture : AAAA-MM-JJ
    cause : soumis | données-absentes | artefact-technique | hypothèse-infirmée |
            complété | scindé | non-projet
    réouverture : <la condition falsifiable qui lèverait cette cause>
```

Le seul critère de réouverture défendable est « le fait nouveau lève la cause
qui a clos le projet », d'où l'exigence que la cause soit écrite pour être
appariable. `carrefour.py stats` liste en fin de sortie les projets archivés
qui n'ont pas encore cette en-tête.

## Invitation au recadrage (à chaque `/pistes read`)

Cet arbre répond à « que reste-t-il à faire **dans le cadre actuel** ». Il ne
sait pas dire si le cadre lui-même tient encore. Après l'affichage, exécuter :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/recadrage/recadrage_signals.py --quiet
```

Silencieux tant que rien n'est dû (30 jours, 15 entrées de cahier, ou un acquis
sans destination). S'il parle, **relayer sa sortie et proposer `/recadrage`** —
proposer seulement : ne jamais enchaîner sur un recadrage complet sans accord,
c'est une passe lourde qui peut déplacer des acquis hors de l'article.

Deux réflexes qui vont avec, quand une direction nouvelle apparaît pendant la
lecture de l'arbre :

- **Une direction qui ne concerne plus l'objet de ce projet ne va pas ici** —
  mais pas non plus mécaniquement au registre parent. Chercher d'abord un
  destinataire (`/pistes match`, ci-dessus) : si un projet VIVANT pose déjà la
  question, la direction s'écrit chez lui en sous-piste (destination **C1**) ;
  faute de destinataire seulement, elle va au `pistes.md` du répertoire
  **parent** (registre de sérendipité, destination **C2**), au format
  `[SÉRENDIPITÉ ← <projet>]` avec ses sous-pistes d'amorçage ET la ligne
  `destinataire cherché :` qui garde la trace du match. Cf. `/recadrage`,
  Phase 3bis. L'inscrire dans le projet la condamne à disparaître avec lui ;
  l'inscrire au registre sans avoir cherché la condamne à attendre que quelqu'un
  la relise par hasard.
- **Un fait établi ici qui répond à la question ouverte d'un AUTRE projet**
  (destination **E**) s'écrit chez lui, en sous-piste
  `[RÉPONSE EXTERNE ← <projet> <date>]`, `[à faire]`, seulement s'il lui est
  actionnable, et sans jamais fermer sa piste à sa place.
- **Une direction qui concerne bien le projet mais pas l'article en cours**
  (second papier, supplementary) reste ici, sous une piste de valorisation, avec
  la mention explicite « hors article courant » — sans quoi elle sera lue comme
  du retard sur le manuscrit.

## Erreurs à éviter

- Ne jamais supprimer une piste (même abandonnée) : la traçabilité est le but.
- Ne jamais réécrire l'arbre en bloc : muter ligne par ligne.
- Ne pas dupliquer une piste déjà présente : d'où le passage obligé de relecture.
- Sur `done`, ne pas oublier de proposer la migration de l'acquis vers l'ÉTAT.
- Après avoir ajouté un résultat qui clôt une piste/sous-piste (même hors mode
  `/pistes`), corriger son tag d'état dans la même édition, et vérifier si la
  piste parente doit être recalculée en conséquence (cf. section ci-dessus).
- Ne jamais afficher un `/pistes read` sans avoir fait l'audit de cohérence
  au préalable : une piste `[en cours]` sans sous-piste ouverte doit être
  tranchée (close ou complétée d'une nouvelle sous-piste) avant, pas notée
  comme curiosité dans le commentaire de sortie.
- Ne pas enterrer dans l'arbre d'un projet une piste qui n'est plus de son
  ressort : elle appartient au registre parent (cf. « Invitation au recadrage »).
- Ne jamais lire `pistes_archive.md` en entier « pour être sûr » (fichier figé,
  hérité des projets migrés avant l'architecture index + détail) : une
  recherche `rg` ciblée suffit toujours, et de toute façon son contenu vit
  aussi désormais dans `pistes/Px.md`.
- Ne jamais ouvrir tous les `pistes/*.md` d'un projet en une passe « pour être
  complet » : c'est exactement le coût que le découpage index + détail est
  censé éviter. N'ouvrir que les fichiers réellement concernés par la tâche
  (la piste travaillée, ou — pour l'audit de cohérence — les pistes `[en
  cours]` de l'index, une par une).
- Après toute mutation de `pistes/Px.md` qui change l'état de la piste
  MAJEURE elle-même, répercuter le même tag sur la ligne d'index
  correspondante dans `pistes.md` dans la MÊME passe — l'index qui ment sur
  l'état réel d'un fichier de détail est la désynchronisation la plus
  coûteuse possible sous cette architecture (elle trompe justement le
  mécanisme censé éviter d'ouvrir le fichier).
