---
name: recadrage
description: Triage de périmètre et re-cadrage d'un projet de recherche — chaque acquis reçoit une destination (article en cours / second papier / projet voisin qui posait déjà la question / registre parent / réponse à une question ouverte d'ailleurs / classé), le cadrage lui-même est remis en question, et la restructuration à deux projets (transférer, fusionner, redécouper, scinder) est proposée quand le projet déborde. Use on `/recadrage`, `/recadrage triage`, `/recadrage scinder`, or "faut-il repenser le projet", "est-ce que ça rentre encore dans l'article", "cette découverte est hors sujet", "on a trouvé autre chose", "scinder le projet", "ouvrir un nouveau projet", "sérendipité", "ne pas perdre cette découverte", "qui d'autre cherchait ça".
argument-hint: "[triage | complet | scinder] [chemin-projet]"
---

# recadrage — Trier ce qui est découvert, décider ce qui sera écrit

Un projet de recherche produit deux choses qu'on confond systématiquement : **ce
qui est découvert** et **ce qui sera rédigé**. Elles divergent avec le temps. Le
manuscrit se resserre autour d'une thèse ; le savoir, lui, continue de s'étendre
latéralement. Sans geste explicite, tout ce qui n'entre pas dans le manuscrit est
perdu — non par décision, mais par silence : ça reste dans le cahier, personne ne
le relit, le projet se clôt, la découverte meurt avec.

Ce skill est ce geste. Il ne cherche rien de neuf et ne recalcule rien : il prend
ce qui existe déjà et tranche **où ça va**, puis se demande si le contenant
lui-même tient encore.

> [!NOTE]
> **Frontière avec les skills voisins — quatre gestes distincts.**
> - `mtbc-bilan` **photographie** ce qui est su (lecture seule, rapport daté).
> - `mtbc-prospect` **imagine** des directions neuves et les inscrit dans `pistes.md`.
> - `/reboot` **repart d'un acquis re-prouvé** quand l'environnement ou les
>   données ont trop bougé depuis la dernière séance (il appelle `recadrage`
>   AVANT d'archiver quoi que ce soit : cf. son étape 2b).
> - `recadrage` (ce skill) **range** : il ne crée pas de matière, il l'affecte.
>   Sa question n'est pas « que pourrait-on faire ? » mais « ce qu'on a
>   découvert appartient-il encore à ce projet, et ce projet est-il encore le
>   bon contenant ? ».
>
> Enchaînement naturel : `bilan` (où en est-on) → `recadrage` (ce qui reste dans
> le cadre, ce qui en sort) → `prospect` (quelles directions neuves) → `reboot`
> seulement si le recadrage conclut que rien n'est récupérable.

## Les six destinations

Chaque acquis du projet — chaque énoncé de `etat_des_decouvertes.md` §2, et
chaque fait établi depuis — reçoit **exactement une** destination :

| Code | Destination | Où il vit désormais |
|---|---|---|
| **A** | Article en cours | `etat_des_decouvertes.md` §2, cité par le manuscrit |
| **B** | Second papier / supplementary du **même** projet | §2 + une piste de valorisation dans le `pistes.md` du projet |
| **C1** | **Essaimage vers un projet VIVANT** qui posait déjà la question | §9 + une sous-piste dans le `pistes.md` de ce projet-là |
| **C2** | **Essaimage vers le registre parent**, faute de destinataire | §9 + une piste `[SÉRENDIPITÉ ← <projet>]` dans le `pistes.md` du **parent**, portant la preuve de recherche |
| **D** | Classé sans suite | §9, **avec la raison écrite** |
| **E** | **Réponse** à une question ouverte d'un autre projet | §2 (il reste un acquis d'ici) + une sous-piste `[RÉPONSE EXTERNE ← <projet> <date>]` chez l'autre |

**Règle d'or : aucun acquis sans destination, et D exige une raison.** Un acquis
sans tag est un acquis qui sera perdu par défaut ; c'est exactement le mode
d'échec que ce skill existe pour empêcher. `recadrage_signals.py` compte les
acquis non tagués et déclenche sur ce seul motif.

**D n'est pas la poubelle du doute.** Dans le doute entre C et D, c'est C : une
ligne de trop dans le registre parent coûte une ligne ; une découverte perdue
coûte la découverte. D est réservé à ce qui est *établi comme sans portée* :
artefact technique compris, négatif sans valeur informative, redite d'un acquis
déjà tagué.

**C et E ne s'excluent pas, et leur différence est de sens, pas de contenu.** En
C, le fait SORT du projet parce qu'il n'y a pas sa place. En E, le fait RESTE ici
— il peut très bien être A par ailleurs — et une copie de son énoncé part
répondre à quelqu'un qui cherchait. Un même acquis peut donc être A et E : il
porte l'article, et il ferme une question ouverte ailleurs.

### Chercher le destinataire avant d'écrire (arbitrage CG du 2026-08-26)

Le dispositif a longtemps versé toute découverte hors périmètre au registre du
dépôt sans jamais demander si un projet vivant posait déjà la question. Trois
gestes, tranchés par CG, corrigent cela.

**1. C1 avant C2, avec preuve de recherche.** Avant d'écrire quoi que ce soit au
registre parent, chercher un destinataire :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pistes/carrefour.py match "<le fait, en une phrase>"
```

Si un projet vivant porte une question que ce fait fait avancer, c'est **C1** :
la sous-piste s'écrit chez lui. Sinon, et seulement sinon, c'est **C2**, et la
sortie du match est recopiée dans la piste de sérendipité comme **preuve que la
recherche a eu lieu** (bloc `destinataire cherché :` du gabarit de Phase 3bis).
Sans cette trace, on ne saura jamais, en relisant, si le registre a reçu ce fait
par défaut ou après examen — et c'est précisément ce défaut-là qui a motivé le
geste.

**2. E, la réponse, en écriture directe.** Un fait établi ici qui fait avancer une
piste ouverte d'un autre projet s'écrit **chez l'autre**, en sous-piste :

```markdown
  - P<n>.<k> [RÉPONSE EXTERNE ← <projet source> <date>] <l'énoncé factuel, avec son
    chiffre et son dénominateur> [à faire]
    ce que ça change ici : <en une phrase — pourquoi le propriétaire de la piste
    doit agir différemment maintenant>
    source : <projet>/cahier_de_labo.md <date> · <script ou figure traçable>
```

Deux règles, non négociables, qui font tenir le geste :

- **Écrire seulement si le fait est ACTIONNABLE pour lui** — il change ce que le
  propriétaire de la piste ferait ensuite. Jamais « pour information ». Écrire
  chez un voisin lui coûte du travail de lecture ; un registre qui reçoit des
  notes non actionnables devient une boîte de réception, et cesse d'être lu.
- **Ne jamais fermer soi-même la piste d'autrui.** On apporte une réponse, on ne
  décide pas à sa place qu'elle suffit. La sous-piste s'écrit `[à faire]`, jamais
  `[réalisé]`, et l'état de la piste parente n'est pas touché.

L'alternative écartée (notification passive, où le propriétaire découvrirait la
réponse tout seul au prochain `/pistes read`) déplace la charge sur celui qui
ignore justement qu'une réponse existe.

**3. Un match n'est pas une décision.** Le script rend des candidats classés par
recouvrement lexical, jamais un verdict. Ouvrir le `pistes/Px.md` du candidat
avant d'écrire chez lui : un score dit que deux textes partagent du vocabulaire,
pas qu'ils posent la même question. Et un recouvrement élevé ne prouve rien — le
plus haut score mesuré du dépôt `mtbc/` appartient à un doublon parfaitement sain
et assumé, dont la division du travail est écrite noir sur blanc.

## Localiser le projet et son registre parent

**Projet** : remonter depuis le répertoire courant, 6 niveaux max ; premier
répertoire portant `cahier_de_labo.md`. **Ancêtres stricts uniquement** — jamais
un répertoire frère (faux positif historique du hook `Stop`). Si rien : « Aucun
projet structuré trouvé. » et s'arrêter.

**Registre parent** = le **premier `pistes.md` ancestral qui existe vraiment**, en
remontant depuis le projet — pas mécaniquement `<parent>/pistes.md`. Un projet
déplacé dans un répertoire d'archivage (`clos_soumis/`, `clos_abandonne/`) aurait
sinon pour registre celui du cimetière, que personne ne relit : exactement
l'inverse du but. Pour `mtbc/clos_soumis/dark_enzymes`, le registre est donc
`mtbc/pistes.md`, pas `mtbc/clos_soumis/pistes.md`. `recadrage_signals.py` applique déjà
cette remontée et affiche le chemin retenu. Si aucun registre n'existe dans toute
la chaîne, créer celui du parent direct avec l'en-tête `/pistes` standard avant
d'y écrire — ne jamais essaimer dans le vide.

**Cas particulier : un projet clos ou archivé.** C'est là que l'essaimage est le
plus urgent, pas le moins : le projet ne produira plus rien, donc tout ce qui
n'en sort pas maintenant y reste définitivement. Une passe de recadrage sur un
projet de `clos_soumis/` est légitime et n'a pas à le rouvrir : elle écrit dans le
registre vivant, et n'ajoute au projet clos que sa §9 et ses destinations.

**Registre d'index du dépôt, s'il existe.** Si un `INDEX.md` vit au même niveau
que le registre parent retenu ci-dessus (ex. `mtbc/INDEX.md` à côté de
`mtbc/pistes.md`), c'est un annuaire à plat de tous les projets du dépôt
(identifiant, résumé en une ou deux phrases, maturité, dernière modification).
Un recadrage y rend presque toujours une ligne périmée : verdict POURSUIVRE /
RECADRER / SCINDER qui change la maturité affichée, scission qui crée une
nouvelle ligne à ajouter, ou déplacement vers `clos_soumis/`/`clos_abandonne/` qui
change le statut. Ne pas l'éditer automatiquement — ce n'est pas un artefact du
projet, il appartient au dépôt entier et une réécriture mécanique risquerait de
désynchroniser sa colonne « estimation automatique » de la méthode qui l'a
produite. **Soulever la question en Phase 6** (bilan narratif) : signaler que la
ligne du projet dans `INDEX.md` peut être obsolète après ce recadrage, et
proposer sa mise à jour plutôt que la faire silencieusement.

## Mode `triage` (léger, par défaut en fin de session)

Une passe de quelques secondes, sans relecture du projet entier. Ne regarde que
**ce que la session courante a produit**.

1. Énumérer les faits établis pendant la session (y compris ceux nés d'une
   discussion, d'une sortie de script ou d'une lecture — pas seulement du code).
2. Pour chacun : destination A, B, C, D — et, en plus, se demander si c'est aussi
   un **E** (répond-il à la question ouverte d'un autre projet ?).
3. N'agir que sur les **C**, les **B** et les **E** : les A sont déjà chez eux.
   - **C** → `carrefour.py match` d'abord. Destinataire vivant trouvé → **C1**,
     sous-piste chez lui. Aucun → **C2**, piste de sérendipité au registre parent
     avec la sortie du match en preuve de recherche (format en Phase 3bis).
   - **B** → sous-piste de valorisation dans le `pistes.md` du projet.
   - **E** → sous-piste `[RÉPONSE EXTERNE ← <projet> <date>]` chez l'autre, si et
     seulement si le fait lui est actionnable.
4. Afficher les lignes écrites, en nommant chaque projet voisin chez qui on a
   écrit. Si tout est A, le dire en une phrase et s'arrêter.

Le mode triage est le seul point du dispositif qui tourne à chaque session : un
`match` y coûte deux dixièmes de seconde et une vingtaine de lignes, ce qui est
le prix à payer pour que la recherche de destinataire soit un réflexe et non une
cérémonie annuelle.

C'est le mode que déclenchent le hook `Stop` et `/pistes read`. Il ne réécrit
jamais `etat_des_decouvertes.md` (c'est le rôle de `/etat update`).

## Mode complet (défaut de `/recadrage` sans argument)

### Phase 0 — Signaux

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/recadrage/recadrage_signals.py [projet]
```

Rend les métriques de déclenchement et les signaux de scission. **Le script ne
tranche rien** : il fournit la matière factuelle, le verdict est rendu ici.
Afficher son résumé avant d'aller plus loin.

### Phase 1 — Lecture

`CLAUDE.md` (question fondatrice), `etat_des_decouvertes.md` intégralement,
`pistes.md` du projet, les entrées de cahier postérieures au dernier recadrage,
et **le manuscrit** (`article/main.tex`) — au moins son abstract, ses titres de
section et ses légendes de figures. Le manuscrit est la définition opérationnelle
du périmètre : ce qui n'y a pas de place n'est pas A, quel que soit son intérêt.

### Phase 2 — Affectation des destinations

Parcourir **tous** les acquis de §2, un par un, sans en sauter. Pour chacun :

- Le manuscrit le mentionne-t-il, ou aurait-il une place naturelle dans une de
  ses sections ? → **A**.
- Est-il solide et intéressant, mais ferait-il dérailler l'argument du manuscrit
  si on l'y ajoutait ? → **B** (le critère n'est pas la qualité, c'est la
  cohérence narrative).
- Concerne-t-il un autre objet que celui du projet (autre gène, autre lignée,
  autre méthode, autre organisme, autre discipline) ? → **C**, puis
  `carrefour.py match` tranche entre **C1** (un projet vivant le cherchait) et
  **C2** (personne, il va au registre parent avec la preuve de recherche).
- Est-il établi comme sans portée ? → **D** + raison.

Puis, **une seconde passe sur les acquis déjà tagués**, celle qu'on oublie : un
acquis A ou B peut en plus être **E**. La question n'est pas « où va-t-il ? »
mais « qui d'autre l'attendait ? ». Un `match --types question,incertain,angle-mort`
sur les acquis les plus solides du projet suffit ; ne pas le faire sur les 40
acquis d'un état mûr, seulement sur ceux qui énoncent un fait général.

Écrire la destination dans la ligne de l'acquis, au format `destination : X`
(voir le squelette de `/etat`), et `destination : A + E → <projet>` quand les
deux s'appliquent — `recadrage_signals.py` ne comptera alors que la destination
principale (ici A), ce qui est voulu : un E secondaire ne change ni le décompte
des acquis non tagués ni la part hors article, puisque l'acquis reste ici. L'affectation est **révisable** : un B peut devenir A si le
cadrage change en Phase 3.

### Phase 3 — La question de recadrage

C'est le cœur du skill, et la question qu'aucun autre n'ose poser :

> **L'état actuel du savoir justifie-t-il encore le cadrage annoncé en §1 ?**

Quatre symptômes de cadrage périmé, à vérifier explicitement, chacun avec sa
réponse :

1. **L'objectif principal a été atteint, ou tranché par la négative, et le projet
   continue par inertie.** → le nouvel objectif est ce qui occupe réellement les
   sessions récentes : le nommer.
2. **Le résultat le plus solide du projet n'est pas celui que le titre annonce.**
   Symptôme mesurable : l'acquis de plus forte solidité en §2 n'est pas celui que
   l'abstract met en avant. → recadrer le manuscrit autour de ce qui est
   réellement établi, pas de ce qu'on espérait établir.
3. **La part d'acquis hors article dépasse le seuil** (signal du script). → soit
   le périmètre est trop étroit (élargir), soit le projet a essaimé (scinder).
4. **Une hypothèse fondatrice est passée en §3 (réfutée) sans que §1 bouge.** →
   §1 ment ; le réécrire.

Verdict de phase : **POURSUIVRE** (le cadrage tient) ou **RECADRER** (proposer le
nouveau §1 et le nouveau titre de travail, à confirmer par l'auteur). Un
recadrage rejette mécaniquement des acquis de A vers B ou C : les réaffecter dans
la même passe, jamais « plus tard ».

**Cinquième verdict : ABANDONNÉ**, pour un projet arrêté avant publication. C'est
le cas où la passe rapporte le plus, et le seul où **ne rien faire perd tout** :
un projet clos par soumission finira par valoriser ses acquis, un projet
abandonné ne valorisera rien par définition.

Trois adaptations, parce que la procédure standard ne s'applique pas :

1. **Il n'y a en général ni `etat_des_decouvertes.md` ni `pistes.md`** (ils sont
   arrivés après ces projets). La matière est dans le `cahier_de_labo.md` et
   surtout dans l'`ARCHIVE_NOTE.md` / la note de clôture, qui condense
   déjà le travail : **la lire en premier, c'est presque toujours suffisant**.
   Ne PAS reconstruire un état des découvertes pour un projet mort : c'est cher
   et ça n'aura aucun lecteur.
2. **Le critère de tri change.** « Le manuscrit le porte-t-il ? » n'a pas de sens
   sans manuscrit. La question devient : **ce fait dépend-il de la raison de
   l'abandon ?**
   - **OUI** → `D`, avec la raison nommée (« repose sur l'identification erronée
     de la souche »). Il meurt avec l'erreur, et c'est justifié.
   - **NON** → il survit intact. `C` s'il a une suite possible, sinon au moins
     une trace dans le registre pour que personne ne le refasse.
3. **Chercher les faits LATÉRAUX en priorité.** Un projet réfuté produit
   presque toujours des mesures vraies sur autre chose que ce qu'il testait, et
   ce sont elles qui survivent le mieux — précisément parce que personne ne les
   regardait. Un négatif propre (« l'hypothèse H est fausse, voici le contrôle
   qui la tue ») est lui aussi un fait indépendant, souvent publiable, et au
   minimum une économie : sans trace au registre, il sera refait.

Ne pas rouvrir le projet : écrire dans le **registre vivant** (jamais dans celui
du répertoire d'archivage) et ajouter une ligne à l'`ARCHIVE_NOTE.md` disant ce
qui a été essaimé et où.

**Quatrième verdict : CLOS.** Sur un projet soumis ou archivé, le cadrage n'est
plus révisable — un manuscrit parti ne se recadre pas. Ne pas simuler un verdict
POURSUIVRE qui n'a pas de sens : rendre **CLOS**, et la passe garde alors ses
deux autres utilités, qui sont même plus urgentes qu'ailleurs :
- **l'essaimage**, parce que le projet ne produira plus rien : ce qui n'en sort
  pas maintenant y reste définitivement ;
- **la préparation de la révision** : tout acquis tagué A mais absent du texte, ou
  réduit à une clause alors qu'il répond à une faiblesse concédée, devient du
  matériel de rebuttal identifié à l'avance plutôt que retrouvé dans l'urgence
  quand les rapports arrivent.
Ne pas rouvrir le projet pour autant : on n'y écrit que sa §9, ses destinations
et sa note MIU.

### Phase 3bis — Fait nouveau ⇒ projet potentiel

Pour chaque acquis **C2** — donc après que le `match` a confirmé qu'aucun projet
vivant ne posait la question —, se demander s'il ouvre non pas une piste mais un
**projet**. (Un acquis **C1** n'a pas à passer par là : il rejoint une question
déjà posée ailleurs, et c'est le propriétaire de cette question qui jugera si
elle mérite un projet.) Signes : il concerne un objet qui mériterait sa propre question de
recherche ; il est généralisable au-delà du cas observé ; sa vérification
demanderait un jeu de données que le projet courant n'a pas.

Dans ce cas, la piste écrite dans le registre parent porte **obligatoirement**
ses sous-pistes d'amorçage — c'est ce qui distingue une piste d'un vœu :

```markdown
## P<n>. [SÉRENDIPITÉ ← <projet>] <fait observé, avec son chiffre> [à faire]
  origine : /recadrage <projet> <date>    maj : <date>
  Fait : <énoncé factuel + dénominateur + preuve traçable (script, figure, chiffre)>
  Pourquoi hors périmètre : <en une phrase — pourquoi ça ne rentre pas dans l'article courant>
  destinataire cherché : `/pistes match` le <date> — <les 3 meilleurs candidats avec
    leur score et pourquoi aucun ne convient, ou « aucun rapprochement »>
  Projet potentiel : <la question de recherche qu'il ouvrirait, si elle tient>
  - P<n>.1 AMORCE littérature : est-ce déjà publié ? (`/lit-review`, `tbmonitor-papers`,
    `literature-access` pour le plein texte) [à faire]
    critère d'arrêt : si publié à l'identique → basculer la piste en [abandonné] avec la réf
  - P<n>.2 AMORCE in silico minimale : <le test le moins cher qui distingue le signal
    du bruit — pas l'analyse complète, le test à une heure> [à faire]
    modèle nul : <ce à quoi on compare pour que le résultat veuille dire quelque chose>
  - P<n>.3 DÉCISION go/no-go : ouvrir un projet via `/init-project <nom>` si
    <critère chiffré explicite>, sinon clore [à faire]
```

Sans P<n>.1 et P<n>.2, ne pas écrire la piste : une sérendipité sans test
d'amorçage est une note d'intention, et le registre parent se remplirait de
bonnes intentions jusqu'à devenir illisible — donc jusqu'à ne plus être lu.

La ligne `destinataire cherché :` est du même ordre : sans elle, une piste du
registre ne dit pas si elle y est parce que personne ne la voulait ou parce que
personne n'a demandé. Écrire « aucun rapprochement » est une information ; ne
rien écrire n'en est pas une.

### Phase 3ter — Restructuration du registre (fusion / redécoupage)

Un fait nouveau ne fait pas qu'ajouter une ligne : il peut révéler que **des lignes
existantes étaient mal découpées**. Ce passage est obligatoire avant d'écrire toute
nouvelle piste, dans le registre parent comme dans celui du projet. Sans lui, un
registre se dégrade toujours de la même façon : des jumelles qui s'ignorent d'un
côté, des fourre-tout illisibles de l'autre.

**FUSION — rassembler ce qui pose la même question.**

Déclencheur : la piste à écrire porte sur le **même objet** qu'une piste existante
(même lignée, même gène, même locus, même organisme), ou l'une est un **test** de
l'autre, ou les deux dépendent du **même jeu de données décisif**.

Exemple canonique. Une piste « émergence de L1 » existe. On observe que des
spoligotypes L1 sans perte d'espaceurs subsistent en Éthiopie. Ce n'est pas une
piste jumelle : un spoligotype non délété est un **caractère ancestral**, donc une
observation qui documente directement l'émergence de L1. Les deux doivent vivre
sous une seule entrée. Séparées, elles produisent au mieux deux articles qui se
citent mal, au pire un article écrit en oubliant l'autre moitié de son propre
argument.

Ce qui NE fusionne PAS : deux pistes qui ne partagent qu'une **méthode** (« toutes
deux passent par Foldseek »), qu'un outil, ou qu'un répertoire. La méthode n'est
pas l'objet ; fusionner par méthode fabrique précisément les fourre-tout que le
redécoupage ci-dessous doit ensuite défaire.

Procédure, non destructive comme toujours :
- Piste nouvelle + piste existante → écrire la nouvelle **comme sous-piste** de
  l'existante, jamais comme piste sœur.
- Deux pistes **préexistantes** → désigner la porteuse (la plus générale, ou celle
  qui porte déjà les données), y ajouter les sous-pistes de l'autre, puis marquer
  l'absorbée `[abandonné] — raison : fusionnée dans Py (<date>)` si son contenu a
  réellement migré, ou lui ajouter une simple ligne « rattachée à Py (fusion
  <date>) » si elle garde une vie propre. Jamais de suppression, jamais de
  réécriture du texte d'origine.

**REDÉCOUPAGE — séparer ce qui pose deux questions.**

Déclencheurs, du plus fiable au moins fiable :
1. **Le titre a besoin d'un « et » (ou d'une virgule énumérative) pour être vrai.**
   C'est le meilleur indicateur, et le moins coûteux à vérifier.
2. Deux groupes de sous-pistes **sans dépendance mutuelle** : aucune d'un groupe
   n'est prérequis d'une du second.
3. ≥ 8 sous-pistes directes, ou une profondeur au-delà de trois niveaux.
4. Les sous-pistes ne partagent plus ni jeu de données ni méthode.

Procédure : créer la ou les pistes nouvelles, y **recopier** les sous-pistes
concernées **en conservant leur `origine:` d'origine** (c'est elle qui garde la
mémoire de d'où venait l'idée, et la perdre est la seule perte irréversible d'un
redécoupage), puis marquer dans la piste d'origine « sous-pistes X, Y migrées vers
Pz (redécoupage <date>) ». Ne pas supprimer les lignes migrées.

**PROMOTION — quand une piste cesse d'être une piste.**

Une piste de sérendipité qui, après fusion, rassemble **≥ 3 sous-pistes amorcées**
et dispose d'un **jeu de données propre** n'est plus une piste : c'est un projet.
C'est le geste symétrique de la Phase 4 — on **scinde** un projet devenu trop
gros, on **promeut** une piste devenue trop grosse. Même procédure
(`/init-project`, pointeurs réciproques, migration non destructive), et le même
seuil de prudence : promouvoir trop tôt fabrique un projet vide avec cinq
artefacts à maintenir.

### Phase 3quater — Notation MIU (maturité, importance, urgence)

Un registre qui grossit devient une liste sans relief : tout y a l'air également
à faire. La notation MIU sert à répondre à deux questions distinctes — « que
faire maintenant ? » et « qu'est-ce qui est le plus prometteur ? » — que la
lecture d'un arbre de pistes ne permet pas de trancher.

Format, sur la ligne `origine:`/`maj:` d'une piste majeure :

```
  origine : …    maj : 2026-08-12    MIU : M2 I3 U1
  I: change une conclusion du manuscrit en cours ; U: dépend de la soumission de <projet>
```

Et pour un projet entier, dans l'en-tête de `etat_des_decouvertes.md` :
`**MIU projet :** M3 I2 U1`.

| | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| **M**aturité | idée nue | amorce faite (littérature ou test minimal) | résultat obtenu, non consolidé | résultat consolidé, prêt à rédiger |
| **I**mportance | anecdotique | utile localement (confort, outillage) | change une conclusion du projet | publiable en soi, ou change la direction |
| **U**rgence | aucune contrainte | échéance lointaine ou donnée périssable | bloque une autre piste ou un manuscrit | échéance ferme et **datée** |

**Deux garde-fous, parce qu'une échelle non contrainte dérive toujours vers le
haut.** M et U sont des faits vérifiables (y a-t-il un résultat ? y a-t-il une
dépendance ou une date ?) ; **I est le seul jugement**, donc le seul à protéger :

- **I ≥ 2 exige une clause `I:` qui dit ce que ça change.** Sans elle, plafonner
  à 1. « C'est important » n'est pas une justification, « ça change la conclusion
  de la section 3.4 » en est une.
- **U = 3 exige une date.** Sans date, plafonner à 1. Une urgence sans échéance
  est une préférence.

`recadrage_signals.py --priorites` signale les notes en défaut sur ces deux
règles ; ne pas les laisser passer, c'est ce qui garde l'échelle discriminante.

**Lecture — deux classements disjoints, jamais un score unique.**

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/recadrage/recadrage_signals.py [projet] --priorites
python3 ${CLAUDE_PLUGIN_ROOT}/skills/recadrage/recadrage_signals.py --portfolio   # tous les projets
```

- **ACTION** : trié par urgence, puis par I+M. C'est le principe « finir ce qui
  est presque fini » : à importance égale, une piste mûre coûte moins cher à
  conclure qu'une piste nue, et laisser les chantiers mûrs ouverts est ce qui
  fait grossir un registre sans que rien n'en sorte.
- **PROMESSE** : importance ≥ 2 **et** maturité ≤ 1. Volontairement **disjoint**
  du classement d'action, parce qu'un pari n'a par construction jamais l'air
  prioritaire face à un chantier ouvert. Les fusionner en un score unique, c'est
  garantir qu'aucun pari ne sera jamais lancé.

Le `--portfolio` répond à une question que le MIU par piste ne peut pas trancher :
**lequel des projets finir en premier**. Une piste M3 I3 dans un projet mort ne
vaut pas une piste M2 I2 dans un projet à deux semaines de la soumission.

Noter en priorité les pistes **ouvertes** ; ne pas noter rétroactivement les
pistes closes, c'est du travail sans lecteur.

### Phase 4 — Test de scission

Cinq critères. Le script en mesure trois ; les deux derniers relèvent du jugement
et doivent être tranchés explicitement, pas éludés :

1. Part d'acquis hors article ≥ 40 % *(mesuré)*.
2. Manuscrit ≥ 9 sections, ou ≥ 8 figures, ou ≥ 1400 lignes *(mesuré)*.
3. ≥ 12 pistes majeures ouvertes *(mesuré)*.
4. **≥ 2 questions de recherche indépendantes** en §1, dont aucune n'est
   prérequis de l'autre *(jugement)*.
5. **Deux publics ou deux journaux cibles distincts** *(jugement)*.

**3 critères sur 5 → proposer SCINDER.** En dessous, ne pas le proposer : scinder
trop tôt fabrique deux projets faibles au lieu d'un solide, et double le coût de
maintenance des artefacts.

Procédure de scission — **non destructive, aucune suppression nulle part** :

1. `python3 ${CLAUDE_PLUGIN_ROOT}/skills/init-project/init_project.py <nouveau> --at <parent> --domain mtbc`
2. Dans le `CLAUDE.md` du nouveau projet : « Issu de la scission de `<parent>`
   le `<date>` — raison : … ». Dans celui du parent : le pointeur réciproque.
   Les deux pointeurs, toujours : un lien à sens unique se perd.
3. Les acquis migrent par **copie** dans le §2 du nouveau projet. Dans le parent,
   ils restent en §9 avec la mention « essaimé vers `<nouveau>` ».
4. Les pistes migrent : dans le parent, la piste passe `[abandonné] — raison :
   migrée vers <nouveau>` (jamais supprimée, conformément à `/pistes`) ; dans le
   nouveau projet elles sont recréées, renumérotées P1…Pn, en gardant leur
   `origine:` d'origine.
5. Une entrée au cahier des **deux** projets, le même jour, se citant mutuellement.
6. Les données restent où elles sont ; le nouveau projet y accède par chemin
   relatif. Ne jamais dupliquer un jeu de données pour une scission.

### Phase 4bis — Verdicts à DEUX projets

> [!IMPORTANT]
> **Ne pas confondre avec la Phase 3ter.** FUSIONNER et REDÉCOUPER y désignent
> des gestes sur des **pistes à l'intérieur d'un registre** ; ici ils désignent
> des gestes sur des **projets entiers**, avec leurs cinq artefacts, leurs
> données et leurs manuscrits. Même mot, deux ordres de grandeur de coût. En cas
> de doute sur le niveau visé, c'est celui de 3ter : réorganiser des pistes est
> presque toujours suffisant, et toujours moins cher.

La Phase 4 ne connaît qu'un geste, SCINDER, et il ne concerne qu'un projet qui
déborde. Or la pathologie inverse existe autant : deux projets qui se marchent
dessus, ou dont le découpage ne suit pas la ligne de leurs questions. Trois
verdicts la traitent, du moins coûteux au plus coûteux. **Aucun ne s'exécute
d'office** : ils se proposent, et l'auteur tranche.

La matière factuelle vient de :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pistes/carrefour.py overlap
```

qui rend les paires de projets dont l'objet se recouvre, avec les tokens
partagés. **Lecture obligatoire de cette sortie : un score élevé ne prouve
rien.** Le plus haut recouvrement mesuré du dépôt `mtbc/` (0,41) appartient à
une paire parfaitement saine, dont la division du travail est explicitement
écrite. Le score mesure la proximité d'objet, jamais la pathologie ; il ne se lit
qu'en le croisant avec une question qu'aucun script ne répond : **cette division
du travail est-elle écrite quelque part ?** Si oui, il n'y a rien à faire, quel
que soit le score.

**`overlap` seul SOUS-COMPTE, et un triage à N projets nommés doit s'en méfier**
(constaté 2026-09-01, triage croisé Bovis à 4 projets sur `mtbc/`) : le mode
global `overlap` n'a rendu qu'UNE paire pertinente sur QUATRE trouvées par la
suite, les trois autres n'émergeant qu'en interrogeant `match` avec le TEXTE DE
L'OBJECTIF (§1 de chaque `etat_des_decouvertes.md`) de chaque projet candidat,
pas avec son nom. `overlap` classe par score global sur tout le dépôt et
tronque ; deux projets peuvent se recouvrir fortement sur leur objet sans
apparaître dans les toutes premières lignes. Quand la demande porte
explicitement sur un ensemble de projets nommés (pas une veille générale), ne
pas se contenter d'`overlap` : lancer aussi un `match "<objectif de chaque
projet>"` un par un et lire les résultats croisant les AUTRES projets du même
ensemble, avant de conclure à l'absence de recouvrement.

**TRANSFÉRER — un acquis ou une piste change de projet.** Le geste le moins
coûteux, réversible, et celui à préférer par défaut : il couvre le cas fréquent
où seule une partie de X appartient en réalité à Y. Déclencheur : un acquis (ou
un petit groupe de pistes) de X apparie systématiquement les questions de Y, et
personne dans X ne l'exploite. Procédure : c'est exactement un **C1**, à l'échelle
d'un bloc plutôt que d'un fait isolé. L'acquis passe en §9 de X avec la mention
« transféré vers Y le `<date>` », il est **recopié** en §2 de Y, et les pistes
concernées sont recréées chez Y en gardant leur `origine:` d'origine. Rien n'est
supprimé nulle part, des deux côtés.

**FUSIONNER — deux projets n'en font qu'un.** Le plus coûteux et le plus rare.
Critère décisif, unique, et volontairement difficile à satisfaire : **on ne peut
pas écrire l'abstract de l'un sans citer le résultat principal de l'autre.** Tant
qu'on le peut, ce sont deux projets voisins, et voisiner n'est pas une maladie.
Garde-fou dur : **jamais entre deux projets déjà en phase 3** (itération draft) —
fusionner deux manuscrits en cours de rédaction détruit deux argumentaires pour
en fabriquer un troisième que personne n'a conçu ; à ce stade, la bonne réponse
est TRANSFÉRER, ou deux articles qui se citent. Procédure : désigner le projet
porteur (celui dont la question est la plus générale, ou qui porte les données),
migrer par copie comme en Phase 4, laisser l'absorbé en place avec un
`ARCHIVE_NOTE.md` de cause `scindé` pointant vers le porteur, et des pointeurs
réciproques dans les deux `CLAUDE.md`.

**REDÉCOUPER — deux projets, mais pas selon la même ligne.** Le cas le plus
intéressant et le plus délicat. Signature mesurable : **chacun des deux porte des
acquis qui apparient mieux les questions de l'AUTRE que les siennes propres** —
c'est-à-dire que la frontière actuelle passe au mauvais endroit. `overlap` la
suggère, mais seul un `match` des acquis de X contre les questions de Y, et
réciproquement, la démontre. Procédure : c'est un double TRANSFÉRER, symétrique,
et il doit être proposé comme tel, acquis par acquis nommés, jamais exécuté
d'office. Un redécoupage silencieux est la seule opération de ce skill dont un
auteur pourrait ne pas retrouver la trace en relisant ses registres.

Verdict de phase, à rendre explicitement même quand il est négatif : **RIEN À
FAIRE** (le recouvrement est déclaré et sain), TRANSFÉRER, FUSIONNER ou
REDÉCOUPER, chacun avec la paire de projets nommée et le critère qui le motive.

### Phase 5 — Écriture

Dans cet ordre, et rien d'autre :

1. `etat_des_decouvertes.md` : destinations en §2, §9 « Hors périmètre », et la
   ligne d'en-tête `**Dernier recadrage :** <date> (<verdict>)`. Si la §9 ou la
   ligne manquent, les créer — c'est le squelette de `/etat` étendu.
   Si le recadrage a changé §1, passer par `/etat update` (réécriture intégrale)
   plutôt que d'éditer §1 à la main.

   **Écrire les destinations par script, mais ligne à ligne, jamais par `split`.**
   Sur un état mûr (40+ acquis multi-lignes), l'édition manuelle n'est pas tenable
   et un script est justifié. Deux pièges vécus le 2026-08-12 sur Rv2516c :
   - Un `re.split(r'\n(?=- )')` met dans le bloc d'un acquis **tout** ce qui le
     suit jusqu'au suivant, y compris la ligne vide et le sous-titre `###`. La
     destination atterrit alors *après* le sous-titre de la section suivante.
     Parcourir les lignes et insérer après la **dernière ligne non vide** du bloc,
     en s'arrêtant sur `- ` en colonne 0, `###` ou `##`.
   - Un `'\n'.join(blocs)` avec `rstrip` mange les lignes vides de séparation.
   **Vérifier par `diff` en ne filtrant QUE les lignes ajoutées** (`grep -v
   '^  destination : '`), jamais en ignorant les lignes vides : c'est précisément
   la mise en forme qu'un tel script dégrade, et un diff qui ignore le blanc ne
   la voit pas.
2. `pistes.md` du projet : sous-pistes de valorisation (B), en **mutation locale**.
3. `pistes.md` (ou `pistes/Px.md`) des projets VOISINS : les **C1** et les **E**.
   C'est le seul point du dispositif où l'on écrit chez quelqu'un d'autre, donc
   le seul qui demande des précautions particulières :
   - ouvrir le `pistes/Px.md` de la piste visée avant d'écrire, pour vérifier que
     la question est bien celle que le `match` a fait croire ;
   - écrire une **sous-piste**, jamais une piste majeure, et toujours `[à faire]` ;
   - ne toucher à aucun état existant, et surtout pas à celui de la piste
     parente : elle appartient à son propriétaire ;
   - si le projet visé est migré en architecture index + détail, n'éditer que son
     `pistes/Px.md` (l'index ne référence que les pistes majeures, il n'a rien à
     apprendre d'une sous-piste ajoutée).
4. `pistes.md` du parent : pistes de sérendipité (**C2** seulement), en mutation
   locale, avec la ligne `destinataire cherché :`, sans jamais toucher aux pistes
   existantes.
5. `cahier_de_labo.md` : une entrée via `/cahier-de-labo update`, qui dit le
   verdict et ce qui a bougé de destination. **Quand un C1 ou un E a été écrit
   chez un voisin, ajouter aussi une entrée au cahier de CE projet-là**, le même
   jour, les deux se citant — même règle que pour une scission. Sans cela, le
   propriétaire de la piste voit un jour apparaître une sous-piste dont il ignore
   l'origine.

### Phase 6 — Bilan narratif (obligatoire)

À l'écran, en prose, jamais un tableau sec. Doit contenir : le verdict
(POURSUIVRE / RECADRER / SCINDER) et ce qui le motive ; le verdict de Phase 4bis
s'il y a lieu (RIEN À FAIRE / TRANSFÉRER / FUSIONNER / REDÉCOUPER, avec la paire
nommée) ; combien d'acquis dans chaque destination, avec le dénominateur ;
**chaque acquis passé de A à B ou C, nommé un par un** (c'est ce que
l'utilisateur risque le plus de découvrir trop tard) ; **chaque écriture faite
chez un projet voisin (C1, E), avec le projet et la piste visés, nommés** — on
vient d'ajouter du travail au registre de quelqu'un d'autre, cela ne se découvre
pas par hasard ; les pistes de sérendipité écrites, avec leur test d'amorçage et
ce que le `match` avait rendu ; la prochaine action concrète. L'utilisateur ne doit jamais avoir à ouvrir un fichier
pour savoir ce qui vient d'être décidé. **Si un `INDEX.md` existe au niveau du
registre parent** (cf. « Registre d'index du dépôt » ci-dessus), terminer par une
question explicite sur sa mise à jour (résumé, maturité, date) plutôt que de
l'ignorer ou de l'éditer sans le dire.

## Cadence et points d'appel

Le mode complet ne doit pas tourner à chaque session — un rituel expédié ne
recadre rien. Les seuils du script (30 jours, ou 15 entrées de cahier, ou un
acquis non tagué) définissent quand il est dû.

| Point d'appel | Mode | Déclenchement |
|---|---|---|
| Hook `SessionStart` | — | affiche « recadrage dû » (script `--quiet`), n'exécute rien |
| Hook `Stop` | `triage` | si un fait hors périmètre a émergé sans être aiguillé |
| `/pistes match "<fait>"` | — | recherche de destinataire seule, sans passer par le skill : le geste de C1/E à la demande |
| `/pistes read` | invitation | propose `/recadrage` si dû ; n'enchaîne jamais sans accord |
| `mtbc-prospect` (Phase 9) | `triage` | les candidates hors projet vont au registre parent, pas dans le projet |
| `manuscript-review` (épilogue) | complet | la review révèle le décalage manuscrit ↔ savoir |
| `mtbc-bilan --deepen` (verdict) | complet | ajoute SCINDER / ESSAIMER à CLORE / APPROFONDIR / PIVOTER |
| `/init-project` | — | vérifie que le registre parent existe |

## Erreurs à éviter

- **Ne jamais supprimer un acquis** parce qu'il sort du périmètre : il change de
  destination, il ne disparaît pas. Le §9 et le registre parent existent pour ça.
- **Ne pas écrire une piste de sérendipité sans ses tests d'amorçage** (P.1, P.2)
  ni son critère de décision (P.3).
- **Ne pas verser au registre parent sans avoir cherché un destinataire** : C2
  n'est légitime qu'après un `match` sans réponse, et la sortie du match est la
  preuve que la recherche a eu lieu. C'était le défaut central du dispositif
  jusqu'au 2026-08-26.
- **Ne pas écrire chez un voisin un fait qui ne lui est pas ACTIONNABLE.** Le
  risque introduit par l'outillage du carrefour n'est pas de manquer un
  rapprochement, c'est d'en fabriquer trop et de transformer les registres en
  boîtes de réception. « Pour information » n'est jamais une raison suffisante.
- **Ne jamais fermer la piste d'un autre projet**, ni changer son état, même
  quand on croit y avoir répondu : la sous-piste `[RÉPONSE EXTERNE ← …]` s'écrit
  `[à faire]`, et c'est son propriétaire qui juge si la réponse suffit.
- **Ne pas confondre un score de recouvrement avec un diagnostic** : le plus haut
  score du dépôt appartient à un doublon sain et déclaré. Croiser toujours avec
  « cette division du travail est-elle écrite quelque part ? ».
- **Ne pas exécuter REDÉCOUPER d'office** : c'est la seule opération de ce skill
  dont un auteur pourrait ne pas retrouver la trace en relisant ses registres.
- **Ne pas recadrer sur un seul résultat récent** : un cadrage se juge sur l'état
  consolidé, pas sur la dernière session. Le biais de récence est le principal
  risque de ce skill.
- **Ne pas scinder sous 3 critères sur 5.**
- **Ne pas confondre « intéressant » et « dans l'article »** : c'est la confusion
  que le skill existe pour lever. Un acquis peut être excellent et destination C.
- **Ne pas réécrire `pistes.md` en bloc** (mutation locale, cf. `/pistes`), ni
  changer l'état d'une piste existante du registre parent.
- **Ne pas laisser un acquis sans destination** en se disant qu'on tranchera plus
  tard : « plus tard » est le mécanisme exact de la perte.
- **Ne jamais utiliser `rm`** : `gio trash`.
