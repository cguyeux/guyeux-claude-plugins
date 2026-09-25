# `affirmations.md` — l'acquis legacy en transit

## Ce que c'est, et pourquoi ce n'est pas un sixième artefact

`affirmations.md` naît au `hard` : `reboot.py` lit l'état, les `claim_check.md`
et le `reanalysis_registry.md` legacy, en tire une liste plate d'énoncés
candidats et les écrit à la racine du projet, aux côtés du nouvel
`etat_des_decouvertes.md` que le `hard` vient de vider. Il vit ensuite tout le
temps du rétablissement : chaque affirmation qu'on retranche par
`affirmation <id> --statut prouvée` migre vers `etat_des_decouvertes.md` §2 ;
chaque réfutée migre vers §3. Quand il ne reste plus aucune ligne `non
testée` ou `en test`, `clore` gèle le fichier dans l'archive
(`archives/<date>_reboot/affirmations.md`) et il disparaît de la racine.

Ce cycle — naître de l'archive, se vider dans l'état, se geler dans
l'archive — est ce qui distingue `affirmations.md` d'un sixième artefact
permanent. Les cinq artefacts (`cahier_de_labo.md`, `etat_des_decouvertes.md`,
`pistes.md`, `verdict_diffusion.md`, `plan_narratif.md`) existent pour toute
la vie d'un projet ; `affirmations.md` n'existe que le temps d'un
rétablissement, et son absence chez l'immense majorité des projets — ceux qui
n'ont jamais subi de `hard` — n'est jamais un défaut ni un oubli. Le voir
présent est le signal qu'un rétablissement est en cours ; ne pas le confondre
avec un registre à tenir indéfiniment.

## La règle cardinale

Aucune ligne de ce fichier n'est un acquis tant qu'elle n'a pas été
re-prouvée dans l'environnement courant, avec les données courantes. Un
énoncé qui semblait solide dans le projet legacy — un chiffre, une lignée
assignée, une corrélation — a pu être produit avec un `bdd/actuelle` qui a
depuis dérivé, un script de barcoding remplacé, une convention de dossier
changée par une des refontes de l'environnement. `affirmations.md` existe
précisément pour empêcher qu'un tel acquis retraverse silencieusement dans
le nouvel `etat_des_decouvertes.md` sans être repassé au crible : c'est le
mode d'échec qu'un reboot mal fait produit, un manuscrit qui cite des
chiffres qu'on ne sait plus reproduire. La ligne en tête du fichier généré le
rappelle mot pour mot, et `cycle_status.py` en fait une porte (voir plus
bas) plutôt qu'un simple rappel textuel.

## Frontmatter et compteurs

`generer_affirmations_md` (`affirmations.py`) écrit un bloc YAML en tête :

- `reboot` et `date` : la date du jour de génération (les deux champs
  portent la même valeur — il n'y a pas de distinction entre date de reboot
  et date de génération dans le code actuel) ;
- `archive` : **toujours** `non archivé (généré en prévisualisation AB2)`.
  Ni `cmd_affirmations` ni `cmd_hard` ne passent le paramètre `archive` à
  `generer_affirmations_md`, alors que la signature de la fonction
  l'accepte. Autrement dit, même après un `hard --apply` réel qui a créé
  `archives/<date>_reboot/`, le frontmatter du `affirmations.md` de la
  racine ne mentionne jamais le nom de cette archive. C'est une divergence
  entre l'intention (le paramètre existe, il devait manifestement servir) et
  le comportement observé : ne pas se fier à ce champ pour retrouver
  l'archive d'un reboot, chercher plutôt le dernier `archives/*_reboot/` du
  projet (c'est ce que fait `lire-archive`, `recycler` et `clore` en
  interne) ;
- `env_legacy` / `env_courant` : version d'environnement du projet au moment
  du reboot et version courante, telles que rendues par `env_version.py
  verdict --json` (adaptateur avec repli « non déployé »/« non rattaché » si
  le versionnage n'est pas encore posé sur la machine) ;
- `donnees_legacy` / `donnees_courantes` : les stores `bdd/registre.json`
  cités dans l'état ou les `claim_check.md` du projet, sous forme
  `store@version_citée` puis `store=statut` (« à jour », « dérivé », etc.,
  ou « non vérifié » si `bdd check` n'a pas pu répondre) ;
- `compteurs` : les cinq statuts, recomptés par balayage complet du tableau
  à chaque écriture — jamais incrémentés à la volée, donc jamais désynchronisés
  tant que l'écriture passe par `reboot.py` et pas par une édition manuelle
  du tableau sans recomptage.

## Les colonnes du tableau

`| id | P | énoncé | provenance | dépendances | legacy | statut | piste | preuve | notes |`

- **id** : `A1`, `A2`, … attribués dans l'ordre fixe où `assembler_affirmations`
  parcourt les sources : d'abord l'état (§2 puis §3 puis §4, dans cet ordre),
  puis `claim_check.md` de la racine, puis chaque `article*/claim_check.md`
  trouvé (triés par nom), puis `reanalysis_registry.md`. Le numéro ne dit
  rien de l'importance ni de l'ordre de traitement souhaité — seulement
  l'ordre de lecture des fichiers sources.
- **P** : `P1` (structurant), `P2` (chiffré, par défaut), `P3` (détail).
  Hérité de `claim_check`/`reanalysis_registry` quand la source le porte
  (section `### P<n> — …` ou colonne `Priorité`), sinon dérivé de la
  destination recadrage legacy : destination `A` (article en cours) → `P1`,
  toute autre destination ou absence de destination → `P2`. Les lignes
  issues de §3 (réfuté) et §4 (incertain) de l'état sont **toujours** `P3`,
  quelle que soit leur destination legacy — le code ne regarde la
  destination que pour les acquis de §2. C'est la porte de rédaction
  (§ ci-dessous) qui donne son poids réel à `P1` : tant qu'une ligne `P1`
  reste `non testée` ou `en test`, la rédaction est bloquée.
- **énoncé** : le texte de la puce ou de la cellule source, nettoyé
  (`nettoyer_enonce`) — espaces normalisés, mention `destination : X` retirée,
  tronqué à 220 caractères avec une ellipse. Le nettoyage ne reformule
  jamais le sens ; c'est une copie allégée, pas une synthèse.
- **provenance** : `état §2`/`état §3`/`état §4`, `claim_check <dossier>/
  #n` (le `<dossier>` est le nom du dossier qui contient le `claim_check.md`
  — celui du projet lui-même pour le fichier racine, `article`/`article2`/…
  pour les fichiers en sous-dossier), ou `registry #n`.
- **dépendances** : toujours `—` dans le code actuel. La colonne existe dans
  l'en-tête et dans le plan (`env <v> ; <store>@<version>`) mais aucune
  fonction ne la renseigne ligne à ligne ; les dépendances réelles restent à
  lire dans le frontmatter global (`env_legacy`/`donnees_legacy`) ou à
  ajouter à la main lors du tranchage.
- **legacy** : toujours `oui` — toutes les lignes générées par ce script
  viennent du projet legacy, il n'existe pas de génération de lignes non
  legacy dans le code actuel.
- **statut** : voir la section dédiée plus bas.
- **piste** : `P1.k` pour chaque affirmation `non testée`/`en test` (correctif
  AB8b, 2026-09-22), `—` pour les autres. `assigner_pistes` fixe cette valeur
  UNE FOIS, juste après `assembler_affirmations` et avant toute génération —
  `generer_affirmations_md` et `generer_pistes_reboot_md` la LISENT toutes les
  deux, elles ne la recalculent plus chacune de leur côté. Avant ce correctif,
  le rapprochement `Ak` ↔ `P1.k` ne tenait qu'à la position dans la liste en
  mémoire (le k-ième élément de `a_retablir`) et la colonne restait vide dans
  `affirmations.md` : une ligne ajoutée ou retirée entre les deux générations
  décalait silencieusement le lien. `cmd_affirmation` (tranchage, plus bas)
  dépend directement de cette colonne pour proposer `/pistes done P1.k`.
- **preuve** : reprise telle quelle de `claim_check`/`reanalysis_registry`
  quand la source en portait une, sinon vide ; renseignée par `affirmation
  <id> --preuve …` au tranchage.
- **notes** : notes de la source, plus l'horodatage « vérifié le … » si
  `claim_check.md` en portait un, plus les annotations de doublon possible
  (voir dédoublonnage). Colonne cumulative : chaque `affirmation <id>
  --notes …` **remplace** la valeur existante (`cols[9] = notes`), elle ne
  l'ajoute pas à la suite — écraser une note de doublon en tranchant une
  ligne sans reprendre son contenu la fait disparaître du tableau.

## Les cinq statuts et leurs transitions

`non testée` (défaut à la génération pour tout ce qui n'a pas de statut
legacy reconnu), `en test`, `prouvée`, `réfutée`, `abandonnée`. Rien dans le
code n'empêche de passer d'un statut à n'importe quel autre : `affirmation
<id> --statut` accepte toute valeur de la nomenclature sans vérifier l'état
précédent — la machine à états à cinq statuts est une discipline documentée,
pas une contrainte imposée par le script. `--statut prouvée`, `réfutée` ou
`abandonnée` horodate automatiquement la cellule (`prouvée <date>`) ; `en
test` et `non testée` restent sans date.

La normalisation depuis le vocabulaire legacy (`_MAP_STATUT_LEGACY` dans
`affirmations.py`) mérite d'être lue avant de faire confiance à un statut
hérité : `vérifié`/`confirmé`/`part. confirmé` → `prouvée`, mais aussi
`corrigé` → `prouvée` — cas mesuré sur le dialecte La4, où un claim réputé
faux puis corrigé et revérifié est traité comme une preuve courante, pas
comme une réfutation. `partiellement confirmé` → `en test` ; `à vérifier`,
`ambigu` → `en test` ; `en attente` → `non testée` ; `infirmé`, `incorrect`
(et sa variante `incorrect imprécis`) → `réfutée` ; `non vérifiable` →
`non testée`. Tout statut legacy absent de cette table, ou dont le préfixe
normalisé ne matche aucune clé, retombe sur `non testée` — jamais sur
`prouvée` par défaut : le repli est toujours du côté qui redemande une
preuve, jamais du côté qui en dispense.

## D'où viennent les lignes

Trois sources, dans l'ordre où elles sont lues :

1. **`etat_des_decouvertes.md` §2/§3/§4** (repli `_section_repli` si
   `cycle_status.py` n'est pas importable). Les puces de premier niveau
   (`- …`, continuations incluses) sont découpées une à une ; les
   placeholders connus (`[à renseigner]`, `(rien encore)`, `[À
   REGÉNÉRER…`, `néant`) sont filtrés, pas transformés en ligne vide.
2. **`claim_check.md`**, racine et chaque `article*/claim_check.md`. Deux
   dialectes réels coexistent sur le dépôt, mesurés le 2026-09-21, et le
   parseur les distingue par tentative successive plutôt que par
   détection explicite : il cherche d'abord des sections `### P<n> — …`
   (dialecte observé sur `L4.13`), et seulement si aucune section de ce
   type n'est trouvée, il retombe sur une table unique `## Claims` avec une
   colonne `Priorité` (dialecte observé sur `La4`). Un projet qui mélangerait
   un jour les deux formes dans le même fichier ne serait lu que par le
   premier dialecte trouvé — volontairement, pour ne jamais compter deux
   fois la même table.
3. **`reanalysis_registry.md`** (produit par l'ancien `/mtbc-reboot`), sections
   `## Claims P<n>`. Présent sur six projets déjà rebootés par l'ancien
   dispositif ; lu de la même façon qu'un `claim_check.md` mais avec ses
   propres noms de colonnes (`énoncé`/`enonce`, `preuve`, `notes`).

4. **Le cahier legacy, optionnel, `--migrate`** (correctif AB8a, 2026-09-22).
   Le plan d'origine (§ AB.5) prévoyait, pour un état legacy réduit à un
   squelette, que l'assistant dépouille le cahier à la main (`rg` ciblé) pour
   retrouver des affirmations que l'état squelette ne porte plus — une étape
   `[Opus:high]`, donc un jugement, jamais un parseur. `extraire_cahier_migrate`
   ne fait PAS ce jugement : c'est un repérage mécanique, un candidat brut par
   puce de premier niveau sous chaque entrée datée (`## AAAA-MM-JJ`) du cahier
   (et de son archive), destiné à réduire le coût de repérage avant la relecture
   assistée, pas à s'y substituer. `assembler_affirmations(..., migrer=True)`
   les ajoute avec `p = "P2"`, `statut = "non testée"` et une note explicite
   (« candidat brut --migrate »). `cmd_affirmations --migrate` n'active
   effectivement cette source que si `collecter_mesures(root)["squelette"]` est
   vrai (bandeau « SQUELETTE NON RENSEIGNÉ ») ; sinon `--migrate` est ignoré
   avec un message sur stderr, plutôt que de dupliquer ce que §2/§3/§4 portent
   déjà. Limite assumée, comme le reste du module : une entrée de cahier
   rédigée en prose continue sans puce `- ` n'est pas vue.

Un candidat `--migrate` en `non testée` entre automatiquement dans les `P1.k`
générés (`_affirmations_a_retablir` filtre sur le `statut`, pas sur le `p`) —
c'est précisément ce qui permet à `carrefour.py match` par lot (ci-dessous) de
l'annoter comme n'importe quelle autre affirmation à rétablir.

**`carrefour.py match` par lot sur les P1** (correctif AB8a). `cmd_affirmations
--carrefour-match` appelle `annoter_carrefour_voisins`, qui interroge
`carrefour.py match "<énoncé>"` (via `adaptateur_match`, même convention de
parsing texte fixe que `adaptateur_overlap`) pour chaque affirmation
`non testée`/`en test`, et ajoute à sa colonne `notes` le meilleur voisin
**vivant** trouvé (`voisin carrefour : <projet> (<score>) — <extrait>`). Une
annotation, jamais une preuve : elle indique où chercher, pas ce qu'il faut en
conclure — cf. « Ce qui relève du jugement de l'assistant » plus bas. Aucun des
deux flags n'est câblé dans `cmd_hard` : les deux sont des aides à la relecture
qui précèdent `hard --apply`, pas des étapes de l'archivage lui-même.

## Le dédoublonnage Jaccard

`marquer_doublons` compare **toutes les paires** d'affirmations assemblées
(pas seulement au sein d'une même source) sur leurs jeux de tokens : mots en
minuscules d'au moins trois caractères, alphanumériques (accents compris
dans la classe de caractères, mais aucune normalisation d'accent — `étude`
et `etude` sont deux tokens distincts). Au-delà du seuil 0,6 de similarité
de Jaccard (intersection sur union), les deux lignes reçoivent chacune une
note `doublon possible avec A<k> (Jaccard 0.NN)`, ajoutée à la colonne
`notes` existante. **C'est une annotation, jamais une fusion ni une
suppression** : les deux lignes survivent telles quelles dans le tableau,
avec leurs statuts et leurs `P` propres, potentiellement différents (un
doublon peut être `P1` d'un côté — venu de l'état — et `P3` de l'autre —
venu d'un `claim_check` réfuté). Le script ne tranche jamais lequel des deux
est le doublon « de trop » : c'est un jugement humain, fait au moment du
tranchage (`affirmation <id>`), qui décide de traiter les deux comme un
seul fait à prouver une fois ou comme deux nuances distinctes à garder
séparées. Un seuil à 0,6 sur des tokens de surface ne détecte pas deux
formulations sémantiquement identiques mais lexicalement éloignées (« la
lignée L4.6 domine en Afrique de l'Ouest » vs « L4.6 est la lignée majoritaire
ouest-africaine ») : l'absence de note de doublon n'est pas une garantie
d'absence de redite, seulement l'absence de redite détectable par
recouvrement de mots.

## La commande `affirmations`

`reboot.py affirmations [projet] [--ecrire CHEMIN] [--pistes-ecrire CHEMIN]
[--json] [--migrate] [--carrefour-match]`. Sans `--ecrire`, la commande
**n'écrit rien** : elle imprime sur stdout le contenu du `affirmations.md`
qui serait généré (ou son équivalent JSON avec `--json`, qui donne le
tableau des compteurs et la liste complète des dictionnaires d'affirmations,
plus riche que ce que rendent les colonnes du markdown). C'est le mode de
prévisualisation à utiliser pour relire les lignes dérivées avant tout
engagement d'écriture. `--ecrire CHEMIN` écrit effectivement le markdown à
cet endroit (typiquement la racine du projet, mais rien dans le code n'impose
ce chemin — `--ecrire` accepte n'importe quel chemin). `--pistes-ecrire
CHEMIN` écrit séparément le squelette `pistes.md` de reboot ; les deux
options sont indépendantes et peuvent être utilisées seules ou ensemble dans
le même appel. `--migrate` et `--carrefour-match` (AB8a, ci-dessus) sont deux
aides indépendantes l'une de l'autre : la première ajoute des candidats
bruts tirés du cahier (seulement si l'état est un squelette), la seconde
annote les affirmations déjà réunies d'un voisin vivant.

## La commande `affirmation <id>`

`reboot.py affirmation <id> [projet] --statut … --preuve … --notes …
[--apply]`. Refuse si `affirmations.md` n'existe pas à la racine du projet
(message : lancer d'abord `affirmations --ecrire`), si le statut demandé est
hors nomenclature, si l'identifiant n'existe pas dans le tableau, ou si la
ligne trouvée n'a pas exactement dix colonnes (garde-fou contre un tableau
corrompu par une édition manuelle malheureuse). Sans `--apply`, affiche la
ligne avant/après sans rien écrire. Avec `--apply` : réécrit la ligne,
**recompte entièrement** les cinq compteurs du frontmatter par balayage du
tableau (jamais par incrément local — un compteur ne peut donc jamais
diverger du contenu réel du tableau tant que l'écriture passe par cette
commande), puis écrit le fichier.

**Ce que cette commande ne fait jamais**, malgré ce que suggère la lecture
rapide du plan d'origine : elle ne touche pas `pistes.md`. Si le tranchage
porte sur une ligne dont la colonne `piste` indique une sous-piste (`P1.k`)
et que le nouveau statut est `prouvée`, `réfutée` ou `abandonnée`, la
commande imprime seulement un rappel :

> piste associée P1.k : clore manuellement (`/pistes done P1.k` puis
> `impact_done.py P1.k`) — non automatisé par cette sous-commande

`impact_done.py` n'est donc **jamais invoqué automatiquement** par
`affirmation <id>` — contrairement à ce que la formulation du plan (« recompte,
mutation de la sous-piste P1.k, `impact_done.py` ») peut laisser penser à
première lecture. Trancher une affirmation et clore sa sous-piste restent
deux gestes séparés, le second entièrement à la charge de l'assistant.

## Le `pistes.md` de reboot engendré

`generer_pistes_reboot_md` produit un squelette à cinq pistes majeures :

- **P1** — une sous-piste `P1.k` par affirmation `non testée` ou `en test`
  (dans l'ordre du tableau), plus, s'il existe des affirmations `réfutée`,
  une sous-piste finale groupant leur réexamen. Les affirmations `prouvée`
  ou `abandonnée` à la génération n'ont pas de sous-piste : le squelette ne
  porte que ce qui reste à trancher.
- **P2** — recadrage post-reboot, avec une unique sous-piste marquée
  `[DÉCISION CG]` (TRANSFÉRER / FUSIONNER / REDÉCOUPER) : jamais exécutée
  d'office par le script, quel que soit le contenu du projet.
- **P3** — recyclage des artefacts legacy, laissée vide de sous-pistes par
  ce générateur (elles se peuplent au fil des appels à `recycler`).
- **P4** — pistes legacy ouvertes au reboot, non re-cadrées, vide de
  sous-pistes par ce générateur.
- **P5** — manuscrit, feuille blanche, bloqué par P1 puis par la porte 1
  que la clôture rouvre (`SKILL.md`, étape 4).

Ce fichier n'est **pas** fusionné avec un `pistes.md` existant par le
script : `--pistes-ecrire CHEMIN` écrase le contenu du chemin donné. Sur un
`hard` réel, c'est `cmd_hard` qui gère le déplacement du `pistes.md` legacy
vers l'archive puis l'écriture du nouveau squelette à la racine — jamais une
fusion des deux.

## Remontée vers `/etat update`

Le skill `etat` porte la règle : si `affirmations.md` existe à la racine
d'un projet, rien ne doit apparaître en §2 de `etat_des_decouvertes.md` qui
n'y soit marqué `[prouvée]`. Concrètement, après `affirmation A3 --statut
prouvée --preuve … --apply`, l'étape suivante — humaine, pas automatisée par
`reboot.py` — est d'ouvrir `/etat update` et d'ajouter en §2 une ligne du
type `- <énoncé>. destination : A. prouvé le <date>, env vX,
<store>@<version> (A3)`, en reprenant l'identifiant `A3` comme trace vers la
ligne du tableau. Une affirmation réfutée suit le même geste vers §3.
`reboot.py` ne fait jamais cette écriture à la place de l'assistant.

## La porte : rédaction bloquée tant qu'un P1 n'est pas tranché

`cycle_status.py::lire_affirmations` (module `cycle-projet`, lu directement
depuis le fichier plutôt que via un import de `reboot.py`, pour éviter une
boucle d'imports puisque `reboot.py` importe déjà `cycle_status`) calcule
`redaction_bloquee` : vrai dès qu'au moins une ligne `P1` du tableau porte
encore `non testée` ou `en test` dans sa cellule statut. C'est une condition
**nécessaire** de la porte 1 du cycle de vie, pas sa levée : un manuscrit bâti
sur un acquis hérité mais jamais re-prouvé est exactement ce que le dispositif
de reboot existe pour empêcher. Un projet sans `affirmations.md` à la racine
n'est pas concerné par ce contrôle — son absence renvoie simplement
`{"present": False}`, jamais un blocage.

Attention au cas qui passe entre les mailles : après `clore --apply`,
`affirmations.md` quitte la racine pour l'archive, donc ce contrôle se tait
alors que la porte 1 vient d'être **rouverte** (étape 4 du `SKILL.md`). Jusqu'à
ce que `cycle_status.py` lise les deux lignes de trace du bloc `## Reboot`
(piste AO2 du projet `environnement`), c'est `/cycle-projet gate` qui les
vérifie à la lecture.

## Ce qui relève du jugement de l'assistant, jamais du script

`reboot.py` et `affirmations.py` dérivent, annotent et comptent ; ils ne
jugent jamais du fond. Restent entièrement à la charge de l'assistant qui
conduit le reboot :

- **relire chaque ligne dérivée** avant de la considérer comme une base de
  travail fiable — le nettoyage de `nettoyer_enonce` est mécanique
  (troncature à 220 caractères, retrait de la mention de destination) et
  peut couper un énoncé à un endroit qui en change le sens ;
- **trancher un doublon annoté par le Jaccard** : fusionner mentalement
  deux lignes, en garder une seule comme référence de tranchage, ou décider
  qu'elles portent en réalité deux nuances distinctes — le script ne
  propose que le rapprochement, jamais la décision ;
- **décider qu'un énoncé est réellement `[prouvée]`** dans l'environnement et
  les données courants : relancer l'analyse, comparer au chiffre legacy,
  documenter la preuve dans la colonne `preuve` avant de passer le statut —
  `--statut prouvée` accepte la transition sans aucune vérification de
  fond, la commande fait confiance à qui l'invoque ;
- **relire réellement le cahier legacy** quand l'état source est un squelette :
  `--migrate` (AB8a) repère les puces, il ne les lit ni ne les juge — décider
  qu'un candidat brut « candidat brut --migrate » est une affirmation valide,
  le reformuler proprement, ou l'écarter reste un jugement entier de
  l'assistant, jamais du script ;
- **vérifier un voisin annoté par `--carrefour-match`** avant de s'y fier : la
  note « voisin carrefour : … » dit qu'un projet vivant a un énoncé qui
  ressemble, jamais qu'il a prouvé la même chose dans le même contexte — lire
  sa propre affirmation avant de considérer la sienne comme déjà établie ;
- **clore chaque sous-piste `P1.k`** et invoquer `impact_done.py` à la main,
  la commande `affirmation <id>` ne le fait jamais elle-même.
