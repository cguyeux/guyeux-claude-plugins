---
name: cycle-projet
description: Cycle de vie canonique d'un projet de recherche, de l'analyse primaire à l'archivage — cinq phases strictement ordonnées, chacune fermée par une PORTE (point fixe) qu'il faut prouver avant de passer à la suivante, dont deux portes de DÉCISION qui demandent si le travail mérite d'être écrit (1bis) puis diffusé (3bis). Use on `/cycle-projet`, `/cycle-projet gate`, `/cycle-projet next`, or "où en est ce projet", "est-ce qu'on peut commencer à rédiger", "le projet est-il fini", "quelle est la prochaine phase", "peut-on soumettre", "peut-on archiver le projet", "phase d'analyse terminée ?".
argument-hint: "[status | gate | next] [chemin-projet]"
---

# cycle-projet — Les cinq phases, et les portes entre elles

Un projet de recherche échoue rarement sur un calcul faux. Il échoue parce qu'on
**rédige trop tôt** (la thèse se fige autour d'un état partiel, et tout ce qui
sera découvert ensuite devient une rustine), parce qu'on **s'arrête trop tôt**
(un article part alors qu'une piste triviale l'aurait renforcé), ou parce qu'on
**clôt sans ranger** (la moitié du savoir produit meurt avec le répertoire).

Ce skill est le rail. Il ne fait le travail d'aucun autre skill : il dit **où en
est le projet**, **ce qu'il reste à prouver pour changer de phase**, et **quel
skill fait le travail** de la phase courante.

> [!IMPORTANT]
> **Les phases sont strictement ordonnées et chacune se ferme par une PORTE.**
> Une porte n'est pas une impression, c'est un **point fixe démontré** : un tour
> complet de la boucle de la phase qui ne produit **rien de nouveau**. Tant que la
> porte n'est pas franchie, on ne passe pas à la phase suivante — et quand un
> résultat de phase 3 rouvre une question d'analyse, on **redescend** en phase 1
> pour cette question précise, discipline comprise (challenge, littérature,
> modèle nul), puis on remonte.
>
> **Interdire de sauter une phase n'a jamais voulu dire interdire d'en redescendre
> une.** DEUX portes peuvent renvoyer en arrière (la 1bis par ÉLARGIR, la 3bis par ROUVRIR).
> La porte 3bis (verdict de diffusion) peut renvoyer tout le projet en phase 1
> si la mesure le commande : c'est un résultat du rail, pas une entorse.

> [!IMPORTANT]
> **Le rail n'est pas l'objectif. La recherche l'est, et elle se fait en phase 1.**
> Arbitrage CG du 2026-09-09, à lire AVANT la vue d'ensemble, parce qu'il gouverne
> la façon de lire tout ce qui suit. L'article et la diffusion sont un débouché
> possible, jamais le but ; le but est de bien faire le travail de recherche,
> c'est-à-dire prendre le temps de creuser, fouiller, imaginer et consolider.
> **La phase 1 est le nœud central de la contribution et la valeur ajoutée du
> dispositif**, pas un péage à franchir au plus vite.
>
> Conséquences opératoires, qui vont à rebours des réflexes usuels :
>
> - **Avancer d'une phase n'est pas un progrès en soi.** Un projet qui reste en
>   phase 1 pendant des mois parce qu'il y a encore à instruire est un projet SAIN.
>   Ne jamais présenter le franchissement d'une porte comme l'objectif d'une
>   séance, ni un projet en phase 1 comme « en retard » : la porte 1 mesure
>   l'épuisement du sujet, elle ne récompense pas la vitesse.
> - **Ne jamais proposer la valorisation comme suite par défaut.** Tant qu'une
>   direction instruisible existe, la suite est cette direction, et la mentionner
>   avant est une pression vers la sortie qui coûte au fond. `/soumission`,
>   `/verdict-diffusion` et le pipeline manuscrit ne se proposent qu'une fois la
>   porte réellement atteinte, ou sur demande explicite de l'auteur.
> - **La symétrique est vraie, et elle est le seul garde-fou :** faire du SUR
>   PLACE n'est pas de la recherche non plus. Quand le sujet est épuisé, il l'est,
>   et il devient alors légitime de passer à l'étape suivante, qui est de se
>   demander si ce qui a été fait mérite d'être communiqué (porte 1bis). Le
>   critère qui sépare les deux est celui de la porte, mesuré par les deux tours à
>   vide, jamais une impression de lassitude ni une échéance.
> - **Ce qui est mal fait doit être refait, même si cela fait « reculer ».** Une
>   question rouverte, une mesure reprise, un outil reforgé au milieu d'une phase
>   sont du travail de recherche, pas du retard.

## AVANT tout : ce rail ne vaut que pour la voie ARTICLE

> [!IMPORTANT]
> **Un projet n'a pas forcément vocation à finir en article, et le présumer est
> une erreur de cadrage.** Arbitrage CG du 2026-09-11. Trois débouchés sont
> également légitimes, et les cinq phases ci-dessous ne décrivent QUE le premier.
>
> | Voie | Origine typique | Livrable | Le projet est fini quand |
> |---|---|---|---|
> | **(a) Article** | une question scientifique | manuscrit | la porte 5 est franchie |
> | **(b) Réponse** | la demande d'un collègue | un mail argumenté et ses notes | la réponse est partie |
> | **(c) Réoutillage** | une question technique | skill créé ou corrigé, fiche KB, ticket chez qui détient le code | l'outil est reforgé |
>
> **Un projet peut emprunter deux de ces voies, ou les trois, et basculer de
> l'une à l'autre.** Une question technique posée par un collègue devient un
> article le jour où la mesure faite pour lui répondre se révèle neuve et
> généralisable ; un article avorté laisse souvent derrière lui un outil et une
> réponse qui valaient le détour. Rien n'est figé.
>
> **La voie se DÉCLARE au lieu de se supposer.** Elle s'inscrit dans l'en-tête de
> `etat_des_decouvertes.md` à côté de la phase, se révise quand elle change, et
> le changement se trace dans le cahier avec son motif.
>
> **Conséquences opératoires, dans les deux sens.** Sur les voies (b) et (c), les
> cinq phases, les sept portes et le pipeline qualité manuscrit ne s'appliquent
> PAS : réclamer un `plan_narratif.md` à un projet qui répond à un mail est un
> contresens, et mesurer sa « phase observée » ne veut rien dire. Inversement, ce
> qui est appris sur ces voies se consigne avec la même rigueur — cahier, pistes,
> base de connaissances inter-projets — puisque c'est exactement ce qui permettra
> la bascule vers (a) si elle vient. **Un projet qui se termine sans article n'est
> pas un projet qui a échoué.**

## Où la phase est inscrite

Dans l'en-tête de `etat_des_decouvertes.md`, sur sa propre ligne, **avec la voie
déclarée** :

```
**Itération :** 8    **Voie :** article    **Phase :** 3/5 — itération draft    **Réécrit le :** 2026-08-17
```

Sur les voies (b) et (c), la phase n'a pas de sens et cède la place à un état
libre mais explicite :

```
**Voie :** réoutillage (+ réponse)    **État :** ticket déposé chez l'amont, en attente    **Réécrit le :** 2026-09-11
```

Le hook `SessionStart` l'affiche à chaque ouverture de session. C'est la seule
copie : ne pas la dupliquer dans `CLAUDE.md` ni dans `pistes.md`.

## Profil de plugins, réécrit à chaque porte

Les plugins d'un projet ne sont pas les dix-sept du marketplace : son profil est
`socle + blocs de sa famille + blocs de sa phase`, écrit dans son
`.claude/settings.json`. Quand une porte est franchie et que la phase change, le
profil est réécrit dans la foulée :

```bash
python3 ~/docs/environnement/outils/profil_plugins.py --apply <projet> --write
```

puis **dire à CG de redémarrer la session** : une session déjà ouverte ne verra pas
la bascule, et `/reload-plugins` ne la rattrape pas. `cycle_status.py` affiche de
lui-même `Plugins : profil À RÉÉCRIRE` quand le settings a pris du retard sur la
phase. Table des profils : `~/docs/environnement/profils/profils.json`. Détail
opératoire, pièges du runtime et justification (ce n'est PAS une économie de
budget) : **`references/plugins.md`**.

## Vue d'ensemble

| Phase | Nom | Boucle interne | Porte de sortie (point fixe) |
|---|---|---|---|
| **1** | Analyse primaire | pistes ouvertes ↔ `/mtbc-prospect` ↔ `/lit-review` | plus aucune direction instruisible |
| **1bis** | *Verdict de sujet* (décision, pas une phase) | nouveauté ↔ charge de preuve ↔ décidabilité ↔ débouché | un verdict amont daté — RÉDIGER, RECADRER, ÉLARGIR ou CLASSER |
| **2** | Valorisation et squelette | état → stratégie → message → **narratif** → squelette | chaque article a message + plan narratif + squelette + sa piste |
| **3** | Itération draft | rédaction ↔ analyse ↔ pipeline qualité | un tour complet du pipeline ne rend rien |
| **3bis** | *Verdict de diffusion* (décision, pas une phase) | nouveauté ↔ charge de preuve ↔ décidabilité ↔ débouché | un verdict tranché, daté, argumenté — ou retour en phase 1 |
| **4** | Finalisation et diffusion | mode de diffusion → cible → style → soumission/dépôts | selon le mode choisi (détail ci-dessous) |
| **5** | Clôture | sérendipité → KB → archivage | plus rien à perdre, projet dans `clos_soumis/` ou `clos/` |

---

## Phase 1 — Analyse primaire (bioinfo et littérature)

**Entrée** : `/init-project` passé.

**Le premier geste est une revue de littérature approfondie, avant tout calcul.**
`/lit-review` (et, si votre domaine dispose d'un outil de veille documentaire
dédié, le lancer aussi ; `literature-access` pour le plein texte). Ce n'est pas
une formalité d'ouverture : réplication n'est pas découverte, et un calcul
lancé avant la revue est un calcul qu'on refera. Le hook `PreToolUse` le
rappelle à l'écriture d'un script dans `analyses/`.

**Puis la boucle, jusqu'à épuisement**, en alternant les trois registres :

1. **Résoudre les pistes techniques ouvertes** de `pistes.md`, une par une, chacune
   passée au crible `/challenge` avant lancement (contre-argument le plus fort,
   modèle nul falsifiant, gain attendu contre coût).
2. **Rouvrir l'idéation** avec un skill d'idéation de domaine si vous en avez un
   (exemple : `/mtbc-prospect`, un skill du plugin `mtbc`, absent de ce plugin
   générique) quand la liste des pistes se vide : axes latéraux, skills non
   mobilisés comme lentilles, relecture rétrospective du cahier. Les candidates
   hors périmètre partent au registre parent, pas dans le projet.
3. **Réapprofondir la littérature** (`/lit-review --wide`) : ce que le projet a
   appris change les mots-clés qu'il faut chercher. Une revue faite au jour 1 est
   périmée au jour 30.

**`etat_des_decouvertes.md` est LA VÉRITÉ, et il est toujours à jour.** Au même
niveau d'exigence et dans les mêmes sections : ce qui vient de la **littérature**
(dûment cité, référence vérifiable) et ce qui vient de l'**in silico** (script,
chiffre, dénominateur, modèle nul). Un fait de littérature sans citation n'est pas
un acquis ; un chiffre sans son dénominateur non plus. Réécriture via `/etat update`
à chaque fin d'itération.

### Porte 1 — le point fixe d'analyse

Trois conditions, **toutes** requises, et la troisième est la seule qui coûte :

- aucune piste technique de `pistes.md` n'est `[à faire]` ou `[en cours]` ;
- un tour complet d'idéation (votre skill de domaine, s'il en existe un) ne produit
  **aucune direction nouvelle instruisible** (les candidates rendues sont soit déjà
  faites, soit hors de portée in silico, soit hors périmètre donc essaimées) ;
- une `/lit-review` fraîche n'ouvre **aucun angle neuf**.

**Exiger deux tours à vide consécutifs**, pas un. Un seul tour sec est fréquent et
trompeur ; c'est le second qui atteste le point fixe. Ce qui reste hors de portée
in silico (protéomique dédiée, expérience humide) **ne bloque pas** la porte : il
est documenté comme tel en §7 de l'état et devient une limite déclarée du futur
article, pas une piste ouverte.

> **« Tour à vide » se juge à l'ESPRIT, pas à la LETTRE.** Le critère qui compte est **« aucune direction
> nouvelle ET ACTIONNABLE ne survit au challenge »**, pas « zéro référence
> touchée » ni « zéro candidate ne serait-ce que générée ». Une `/lit-review` qui
> trouve une référence puis la tue immédiatement sur une preuve interne à la
> source elle-même (l'article dit lui-même que le mécanisme espéré est absent, le
> substrat inconnu, l'organisme différent...) **compte comme un tour à vide** :
> c'est le challenge qui a fonctionné comme prévu, pas une lacune de recherche.
> Exiger la lettre stricte — littéralement aucun item, même tué proprement, sur
> deux passages consécutifs — ouvre une **régression sans fin** : sur un sujet
> déjà balayé à fond, toute recherche assez large finit presque toujours par
> effleurer un item tangentiel, qui sera à son tour correctement écarté, ce qui
> réclame un tour de plus, puis un autre. Ce n'est alors plus la porte qui teste
> quelque chose, c'est la définition de « vide » qui devient impossible à
> satisfaire. Cas vécu : sur un projet réel, 2 tours d'idéation strictement vides
> plus 3 tours `/lit-review` (dont un ayant trouvé puis tué une référence sur la
> propre conclusion de son article) ont été traités comme convergence
> suffisante plutôt que de chasser un 4e ou 5e tour parfaitement vierge.
> **Documenter explicitement ce jugement** (dans `etat_des_decouvertes.md`
> et le cahier) comme une décision assumée, jamais un glissement silencieux — il
> reste contestable par l'auteur, qui peut toujours redemander un tour
> supplémentaire s'il juge la convergence insuffisante.

> **Projet sorti d'un reboot HARD : la clôture rouvre la porte 1.** Quand le
> `CLAUDE.md` porte un bloc `## Reboot` « Clos
> le … », la porte 1 est **ouverte**, même si elle avait été franchie avant le
> reboot et même si P1, P3 et P4 sont soldés. Un reboot hard peut infirmer ce que
> le manuscrit affirmait et faire émerger de l'inédit, après le seul recadrage que
> prévoit `reboot` (sur les artefacts legacy, avant archivage). Deux conditions
> s'ajoutent alors aux trois ci-dessus, datées **postérieurement à la clôture** :
> un `/recadrage` sur l'état post-reboot (réfutées, acquis nouveaux) et une
> `/lit-review` ciblée sur le cadrage qui en sort, toujours faite, qu'il y ait eu
> RECADRER ou non. Elles valent premier tour, pas point fixe : les pistes qu'elles
> ouvrent se traitent en phase 1. Tout verdict 1bis ou 3bis antérieur à la
> clôture est périmé, et le manuscrit ne se dégèle qu'après une 1bis re-rendue.
> Preuve lue par `gate` : les deux lignes de trace du bloc `## Reboot`, passées
> de « à faire » à « fait le AAAA-MM-JJ » avec l'entrée de cahier correspondante,
> à une date au moins égale à celle de la clôture. Doctrine complète : `/reboot`,
> étape 4.

> **Anti-pattern le plus coûteux du cycle** : commencer à rédiger parce que
> l'analyse « tourne en rond ». Tourner en rond n'est pas le point fixe, c'est le
> symptôme qu'il faut relancer l'idéation ou rouvrir la littérature. Rédiger à ce
> moment fige la thèse sur un état partiel.

---

## Porte 1bis — Le verdict de sujet, AVANT d'écrire

**Entrée** : porte 1 franchie. **Skill : `/verdict-diffusion amont`.**

La porte 1 démontre qu'il n'y a plus rien à analyser. Elle ne dit rien de la
question qu'aucune autre porte ne pose à ce moment-là : **ce qu'on a appris
mérite-t-il d'être rédigé ?** Sans elle, la seule instance qui juge le fond est
la porte 3bis, et elle arrive après le manuscrit.

**La preuve qu'il fallait aussi une porte AMONT est dans le dépôt** (cas vécu). Un
projet a franchi la porte 1, écrit plusieurs centaines de lignes de manuscrit,
passé cinq skills de pipeline qualité et trois relectures — puis la porte 3bis a
établi que sa thèse était **déjà publiée par l'article qu'il citait en première
ligne**, dans son résumé, sa Discussion et ses légendes de figure. Le contrôle
qui l'aurait sauvé (une lecture plein texte de sa source primaire) coûtait une
heure et pouvait être fait avant le premier paragraphe. Tout ce qui a été écrit
entre les deux portes est perdu, et c'est du temps de calcul et d'écriture
qu'aucune porte aval ne rembourse.

### Les quatre verdicts amont

| Verdict | Sens | Suite |
|---|---|---|
| **RÉDIGER** | le message tient, sa preuve est à sa hauteur, il a un débouché | phase 2 |
| **RECADRER** | il y a de la matière, mais pas celle qu'on croyait porter | `/recadrage`, nouveau §1, puis re-verdict |
| **ÉLARGIR** | la question est trop étroite pour un article ; une question qui l'englobe en ferait un | **retour phase 1** sur la question élargie |
| **CLASSER** | déjà publié, ou creux : rien qui vaille d'être rédigé | phase 5 directement, sans passer par la rédaction |

### La règle du doute, et elle est asymétrique

> [!IMPORTANT]
> **Dans le doute, RÉDIGER** (règle posée par CG le 2026-09-04). Cette porte est
> volontairement **plus clémente que la 3bis**, et pour une raison de coût : un
> manuscrit rédigé puis arrêté à la 3bis coûte des jetons ; un projet sain tué à
> la 1bis coûte le projet. **L'asymétrie est donc voulue et ne doit pas être
> corrigée** : CLASSER ne se prononce que sur une preuve positive de redondance ou
> de vacuité, jamais sur une impression de faiblesse. Un doute sur l'intérêt d'un
> résultat n'est pas un doute sur son existence.

### Les cinq axes, mesurés sur l'ÉTAT, pas sur un manuscrit

Mêmes axes qu'à la 3bis (`/verdict-diffusion`), appliqués à `etat_des_decouvertes.md`
§2 puisqu'il n'y a encore rien d'écrit. Un seul est bloquant.

- **N — nouveauté. C'est l'axe cardinal de cette porte, et le seul dont l'échec
  suffit à prononcer CLASSER.** Le contrôle se délègue à une instance sans accès
  au projet, et porte sur **l'affirmation qui portera le titre**, formulée à
  l'avance. **Lire le PLEIN TEXTE des deux ou trois sources primaires** que le
  futur article contredit ou prolonge, jamais leurs seuls résumés : c'est
  exactement là que le cas vécu ci-dessus s'est perdu, sa source disant dans sa
  Discussion le contraire de ce qu'il lui prêtait.
- **P — charge de preuve** : le niveau de preuve disponible soutient-il le verbe
  du message envisagé ? Un « nous montrons que » adossé à un tirage in silico
  unique se corrige ici, gratuitement, alors qu'il coûtera une réécriture après
  rédaction.
- **D — décidabilité** : une analyse accessible ferait-elle passer le message de
  « convergent » à « tranché » ? Si oui, **la faire avant d'écrire**, pas après.
  C'est le meilleur rendement de toute la porte.
- **U — unité** : y a-t-il un article, ou une note, ou une section d'un autre
  manuscrit ? Répondre « une note » ne ferme rien, cela change le format visé.
- **E — débouché** : ce genre se publie-t-il quelque part ? Mesuré sur la
  pratique effective, jamais sur une page « aims and scope ».

### Porte 1bis

Un verdict amont daté dans `verdict_diffusion.md` (même registre, même en-tête
machine-lisible, la clé `verdict` prenant alors une des quatre valeurs amont), et
le contrôle de nouveauté effectivement délégué et rendu. **Un projet qui entre en
phase 2 sans ce verdict n'a pas franchi la porte**, même si son état est riche.

---

## Phase 2 — Stratégie de valorisation et squelette

**Entrée** : porte 1 franchie.

**L'unique intrant est `etat_des_decouvertes.md`**, pas le cahier. Le cahier est
l'historique ; l'état est le savoir consolidé, et c'est de lui que part la
rédaction.

1. **Proposer une ou plusieurs stratégies de valorisation.** Combien d'articles,
   portant quel message, pour quel public. Le critère est la **communication
   optimale**, pas le maximum de papiers : deux articles qui se citent mal valent
   moins qu'un article dense. Présenter les options à l'auteur avec leur
   contrepartie, et recommander.
2. **Tout ce qu'aucun article ne porte passe par `/recadrage`** : destination B
   (second papier du même projet), C (essaimage au registre parent, avec les trois
   sous-pistes d'amorçage obligatoires), D (classé, raison écrite). **Aucun acquis
   sans destination** — c'est ici que se joue la non-perte, pas à la clôture.
3. **Sérialiser dans `pistes.md`** : typiquement **une piste majeure par article**,
   ses sous-pistes étant les unités de rédaction. C'est ce qui rend la phase 3
   pilotable et reprenable après une pause.
4. **Pour chaque article, dans cet ordre et jamais l'inverse :**
   - **le MESSAGE** — une seule phrase, ce que le lecteur doit retenir, falsifiable.
     Si elle ne tient pas en une phrase, l'article porte deux articles.
   - **le NARRATIF** — **`/narratif`**, et c'est l'étape que l'on saute sans s'en
     apercevoir. Le message dit ce qu'il faut faire admettre ; le squelette dit où
     les sections tombent. Entre les deux, personne ne demandait **comment exploiter
     l'acquis pour délivrer le message** : quelle chaîne d'arguments le lecteur doit
     accepter, où sont les points de bascule, dans quel ordre les sortir, et surtout
     **le temps et le lieu de chaque fait** — développé dans le corps, porté par une
     figure, réduit à une phrase avec renvoi, versé au supplémentaire, ou reconnu
     comme sérendipité et rendu à `/recadrage`. Sans cette étape, l'article hérite
     par gravité de l'ordre du chantier et se remplit de ce qui a coûté du temps :
     c'est le défaut mesuré sur le parc (`animal_vs_human`, 13 558 mots, 22 figures,
     zéro fichier supplémentaire, Résultats découpés nœud par nœud). Registre :
     `plan_narratif.md`, d'où le squelette est **émis** avec son allocation par
     section. Le faire ici coûte une heure ; ne pas le faire coûte le lecteur.
   - **le SQUELETTE** — sections, figures, tables, et pour chacune **ce qu'elle
     démontre**. Une figure qui n'a pas de charge de preuve est une figure à couper.
     C'est ici, et pas plus tard, que se fait **`/fig-ideation`** : il part des points
     de bascule du plan narratif, qui sont les emplacements où une figure est due, et il
     cherche celles qui **manquent** — ce qu'aucun `/fig-check` ultérieur ne saura faire,
     puisqu'il part du `.tex` et ne voit donc que les figures présentes. Le faire ici coûte
     une heure ; le faire en phase 3 coûte une réécriture. Registre : `fig_plan.md`.
   - **puis seulement** les sous-pistes de rédaction.

Écrire avant d'avoir le message, c'est découvrir sa thèse en la rédigeant, donc
réécrire trois fois.

### Porte 2

Chaque article planifié a **son message écrit**, **son plan narratif écrit**, **son
squelette écrit**, et **sa piste dans `pistes.md`** ; **chaque acquis de §2 de l'état
porte une `destination :`** ; et **chaque acquis destiné à cet article porte un rang**
au plan narratif — PORTEUR, BASCULE, MENTION, SUPPLÉMENTAIRE ou SÉRENDIPITÉ.

Contrôle mécanique de la dernière condition, qui rend aussi les bascules sans figure
et les dépendances inversées entre maillons :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/narratif/scripts/plan_status.py [projet]
```

**Un squelette dont une section ne renvoie à aucun maillon ni à aucune bascule n'a pas
franchi la porte** : c'est une section que personne n'a décidée, et c'est par elle que
la verbosité entre.

---

## Phase 3 — Itération draft (analyse ↔ rédaction)

**Entrée** : porte 2 franchie. Le draft se rédige le long du squelette.

Une fois l'état de draft atteint, **boucler le pipeline qualité jusqu'au point
fixe** : `/claim-check`, `/bib-check`, `/fig-check`, `/supp-check`, `/deai-latex`,
`/manuscript-review`, puis `/fig-ideation review`. Chacun maintient son registre daté
(`claim_check.md`, `fig_check.md`, `fig_plan.md`, `review/INDEX.md`, marques `verified`
du `.bib`) — ce sont ces registres qui prouvent la porte, pas l'impression d'avoir fini.

`/fig-ideation review` ferme le tour parce qu'une part des objections de relecture ne
demande pas une analyse de plus mais une **figure** de plus : « la méthode est difficile à
suivre » appelle un diagramme de flux, « en quoi cela diffère du travail antérieur » appelle
un avant/après. Attention au piège : une figure ne répond qu'aux objections portant sur la
**lisibilité** de l'argument. Un relecteur qui doute d'un résultat veut une analyse, et
dessiner un argument faux le rend seulement plus visible.

**Cette phase alterne obligatoirement rédaction et ANALYSE.** C'est ce qui la
distingue d'un polissage : un claim qui ne se vérifie pas, une objection de
`manuscript-review`, un contrôle manquant, une référence qui dit autre chose que ce
qu'on lui fait dire — chacun **ouvre une piste d'analyse**, qui s'instruit avec la
discipline de la phase 1 (`/challenge`, littérature d'abord, modèle nul), puis se
réintègre au texte. Un tour de pipeline qui n'aurait produit que des corrections de
style est suspect : c'est en général qu'on n'a pas cherché.

Toute connaissance produite ici remonte au cahier **et** à l'état : l'état ne cesse
pas d'être la vérité parce que la rédaction a commencé.

### Porte 3 — le point fixe de rédaction

Un **tour complet** du pipeline ne produit aucune action nouvelle :
`claim-check` sans claim non vérifié ni périmé, `bib-check` sans référence non
vérifiée ni doublon, `fig-check` propre, `supp-check` aligné, `deai-latex` sans
narratif de chantier ni cuisine locale restants (R12/R14, voir plus bas),
`manuscript-review` ne soulevant rien au-dessus du cosmétique.

**Exiger deux tours à vide consécutifs, pas un** — même discipline qu'à la porte 1,
et pour la même raison : un premier tour propre est fréquent et trompeur, la
correction d'une objection de `manuscript-review` en rouvre souvent une autre
qu'un seul passage n'aurait pas vue. Ne JAMAIS déclarer la porte franchie sur un
unique passage du pipeline, aussi complet soit-il en apparence.

**Même lecture esprit-plutôt-que-lettre qu'à la porte 1** (cf. l'encadré dédié
ci-dessus) : un tour qui soulève une remarque strictement cosmétique et la corrige
sur-le-champ (typo, référence de figure, formulation) reste un tour à vide au sens
qui compte — aucune ACTION DE FOND nouvelle. Ce qui casse la série, c'est une
objection qui rouvre une analyse, une figure ou une clause substantielle, pas la
simple présence d'une modification sur le fichier. Ne pas chasser un tour
parfaitement immaculé au prix d'une régression sans fin sur un manuscrit déjà mûr.

**Un manuscrit encombré de sa propre histoire n'a pas franchi la porte**, même si
`claim-check`/`bib-check`/`fig-check` sont tous verts : un passage qui subsiste
dans le corps ou les Limitations — chronologie du chantier, mention du « projet »
ou du « groupe » comme sujet grammatical, note destinée à un futur passage
(« à refaire avant soumission », « reste à vérifier ») — est un signal que la
porte n'est pas franchie, quel que soit l'état des registres numériques. C'est le
travail de `/deai-latex` (règles R12 et R14) de le détecter ; s'il ne l'a pas
détecté, ce n'est pas la preuve qu'il n'y en a pas, c'est une raison de relire à
l'œil avant de conclure au point fixe.

**Chaque manuscrit du projet franchit sa PROPRE porte 3**, séparément. Un projet à
deux articles (`article/` et `article2/`) n'est pas en phase 3 clos parce que l'un
des deux l'est : le second garde son propre `claim_check.md`, son propre
`review/INDEX.md`, son propre passage `/deai-latex`, jusqu'à son propre point
fixe. `cycle_status.py` rend désormais la phase observée du projet comme le
minimum des phases de chacun de ses manuscrits, précisément pour empêcher qu'un
second manuscrit moins avancé se cache derrière l'avancement du premier.

---

## Porte 3bis — Le verdict de diffusion

**Entrée** : porte 3 franchie. **Skill : `/verdict-diffusion`.**

Tout ce qui précède mesure si le manuscrit est **bien fait**. Rien ne demande si le
**résultat** mérite d'exister comme publication. Ce sont deux questions distinctes, et
la preuve qu'il fallait une porte pour la seconde est dans le dépôt : un projet a
produit 27 pages, trois relectures internes, un `claim-check` et un `bib-check`
verts autour d'une découverte centrale qui était un double artefact. **Tous les
contrôles de fabrication étaient au vert pendant que la science était fausse.**

Quatre verdicts possibles, un seul rendu, argumenté :

- **SOUMETTRE** — résultat neuf, preuve à la hauteur de ce qu'on lui fait porter,
  débouché réel → phase 4 mode (a) ;
- **DIFFUSER-SANS-COMITE** — le travail vaut d'être public et daté, mais sa preuve ne
  tiendra pas devant un relecteur, ou sa taille n'est pas celle d'un article → phase 4
  mode (b) ou (c) ;
- **NE-PAS-DIFFUSER** — réplication de l'existant, ou résultat central expliqué par un
  artefact irréparable → phase 4 mode (d) puis phase 5, **après** passe `/recadrage`
  pour que le savoir parte aux registres et à la KB ;
- **ROUVRIR** — la question n'est pas décidable en l'état mais une analyse accessible
  la trancherait, ou une question plus large la remplace avantageusement → **retour en
  phase 1**.

**C'est la seule porte du cycle qui peut renvoyer le projet en arrière**, et c'est
délibéré : le rail interdit de sauter une phase, il n'a jamais interdit d'en
redescendre une quand la mesure le commande. Le retour est non destructif — manuscrit,
figures et registres restent en place, et les pistes correspondantes s'ouvrent avec
`origine : verdict-diffusion <date>`. La phase déclarée redescend à 1 **pour les
questions rouvertes seulement**, ce qui s'écrit tel quel dans l'en-tête de
`etat_des_decouvertes.md` (`1/5 pour P5, manuscrit gelé à la porte 3bis`) : un ROUVRIR
dit qu'une question nommée doit être instruite avec la discipline de la phase 1, pas
que tout le programme d'analyse est à refaire.

**L'axe qui tranche le plus souvent** est celui-ci : si la première demande d'un
relecteur est une analyse que nous pouvons faire nous-mêmes en quelques jours in
silico, la faire vaut mieux que soumettre — c'est ROUVRIR, pas SOUMETTRE. À l'inverse,
une preuve hors de portée (paillasse) ne bloque rien : elle devient une limite
déclarée.

**Garde-fou de conflit d'intérêt** : l'instance qui a rédigé le manuscrit est le plus
mauvais juge de ce manuscrit. La passe adversariale et le contrôle de nouveauté se
délèguent à une instance indépendante, sans le contexte de rédaction, et la nouveauté
se remesure **en direct** plutôt que de se relire dans le §5 de l'état, écrit par la
même main. Détail du barème, du registre `verdict_diffusion.md` et de son en-tête
machine-lisible : skill **`/verdict-diffusion`**.

**Application mécanique** : `preflight.py` du skill `/soumission` refuse tout dépôt
sans verdict favorable au mode visé. La porte n'est pas seulement écrite, elle est
appliquée par l'outil qui mène à la soumission.

### Porte 3bis

`verdict_diffusion.md` existe à la racine, porte un verdict daté parmi les quatre,
les cinq axes y sont mesurés (et non estimés), et la passe indépendante y figure.
Un verdict de plus de trois mois, ou antérieur à un résultat nouveau, est périmé.

---

## Phase 4 — Finalisation et diffusion

**Entrée** : porte 3bis franchie, verdict favorable, version définitive en anglais.

**Le mode de diffusion est contraint par le verdict de la porte 3bis, puis arbitré par
l'auteur.** Le verdict dit ce que la science autorise ; l'auteur reste libre du geste,
y compris de temporiser pour des raisons de priorité ou de choix personnel — mais un
mode qui **contredit** le verdict (soumettre à un comité malgré un
DIFFUSER-SANS-COMITE, par exemple) est une décision assumée par l'auteur, à tracer
comme telle dans le cahier, jamais un glissement silencieux. Quatre modes, mutuellement
exclusifs pour l'itération courante :

- **(a) soumission à une revue ou conférence à comité de lecture** — le déroulé
  complet ci-dessous s'applique, rien n'est sauté ;
- **(b) dépôt en préprint seulement** (bioRxiv/medRxiv/arXiv), sans soumission à
  comité pour l'instant ;
- **(c) dépôt du code et des données seulement**, sur
  `<votre-compte>/<votre-depot>`, sans préprint ni soumission ;
- **(d) aucun dépôt externe pour l'instant** — le manuscrit reste figé sur disque,
  archivé tel quel.

**Ce choix n'est jamais définitif.** Un projet réglé sur (b), (c) ou (d) peut
reprendre le déroulé (a) plus tard si l'auteur change d'avis — voir Phase 5,
répertoire `clos/` : rien n'est perdu ni à refaire, seul le
geste de dépôt change.

Le détail opératoire complet (critères de choix de revue, options gratuites,
refactoring quand la taille ne passe pas, automatisation de la soumission,
préprints, dépôt GitHub, et le **paragraphe de déclaration d'assistance IA
obligatoire pour le mode (a)** avec son texte canonique) est dans
**`references/soumission.md`** — le lire à l'entrée en phase 4, quel que soit le
mode retenu.

Pour le mode **(a)**, dans l'ordre :

1. **Version française traduite à la lettre** (`main_fr.tex`) : fidèle, pas adaptée.
2. **Propositions de cibles** : conférences et revues sélectives, **avec
   systématiquement des options gratuites** pour les revues. Chaque proposition est
   soit **compatible avec la taille** de l'article (limites de mots et de figures),
   soit accompagnée d'une **proposition de refactoring** (par exemple passer de deux
   à trois articles, chacun vers une cible différente) **de sorte qu'aucun travail
   ne soit perdu**. Ne jamais proposer une cible qui impose de couper sans dire où
   va le matériel coupé.
3. **Adaptation du style** à la cible retenue (classe LaTeX, limite de mots,
   conventions de sections).
4. **Soumission menée par l'assistant**, au maximum, via le navigateur, en
   s'appuyant sur le CV (`/cv`), les mails et le web. **Solliciter l'auteur le moins
   possible** : ne remonter que les actes irréductibles (clic final si l'éditeur
   exige une action authentifiée de l'auteur, déclarations légales, paiement).
5. **Préprint libre** : bioRxiv / medRxiv / arXiv selon le domaine.
6. **Dépôt du code** sur `<votre-compte>/<votre-depot>`.
7. **Paragraphe de déclaration d'assistance IA** présent dans le manuscrit.

Pour les modes **(b)**, **(c)** et **(d)**, la version française reste requise (elle
sert la relecture et la réutilisation de l'auteur, indépendamment de toute
soumission) ; seuls les gestes correspondant au mode choisi s'appliquent parmi 5 et
6 — aucune cible, aucun style d'éditeur, aucune déclaration d'assistance IA à
produire tant qu'aucune soumission n'a lieu.

### Porte 4

Selon le mode retenu :

- **(a)** manuscrit soumis, préprint en ligne, code déposé, déclaration
  d'assistance IA présente dans la version soumise ;
- **(b)** préprint en ligne (code déposé en plus si l'auteur le souhaite) ;
- **(c)** code et données déposés sur `deciphering-tuberculosis-with-ai` ;
- **(d)** rien à déposer — la porte est franchie par le choix lui-même,
  explicitement tracé dans le cahier de labo et dans `pistes.md` ou l'en-tête de
  `etat_des_decouvertes.md`.

Dans tous les cas : version française compilée et archivée dans `article/`.

---

## Phase 5 — Clôture et archivage

**Entrée** : porte 4 franchie.

1. **Passe de sérendipité finale — `/recadrage` complet.** La question exacte :
   **toute connaissance produite par ce projet et non publiée est-elle sauvée ?**
   Ce qui n'entre dans aucun article doit porter une destination, les **C** partant
   au `pistes.md` du répertoire **parent** avec leurs sous-pistes d'amorçage. C'est
   la dernière occasion : après le déplacement, plus personne ne relit ce projet.
2. **`/reflect`** : cristalliser les apprentissages techniques du projet dans
   `~/.claude/knowledge/` (API comprises, pièges résolus, protocoles réutilisables),
   avec la ligne d'index dans `KNOWLEDGE.md`. Vérifier avant d'écrire qu'un fichier
   ne couvre pas déjà le point.
3. **Archiver** : la destination dépend du mode de diffusion tranché en Phase 4.
   Un projet relève d'un et un seul des **cinq statuts** gravés le 2026-09-16
   (`mtbc/CLAUDE.md`, `codes/CLAUDE.md`), qui sont son emplacement sur le disque :
   `en_cours/` tant qu'il vit, puis l'un des **quatre répertoires de clôture**, à ne
   jamais confondre :

   - **mode (a)** (soumis à comité) → `clos_soumis/` sous `mtbc/`, avec sa ligne au
     `clos_soumis/README.md` : date de clôture, revue et statut, résumé en un paragraphe,
     connaissances back-propagées s'il y en a ;
   - **modes (b), (c) ou (d)** (pas de soumission à comité pour l'instant) →
     `clos/` sous `mtbc/`, avec sa ligne au
     `clos/README.md` : date de clôture, mode de diffusion
     retenu et ce qui a effectivement été déposé (préprint seul / code seul /
     rien), résumé en un paragraphe, connaissances back-propagées s'il y en a. Ce
     répertoire n'est **ni** `clos_soumis/` (aucune soumission à comité n'a eu lieu) **ni**
     `clos_abandonne/` (le projet n'a pas été arrêté en cours de route : le
     savoir est complet, la clôture est un choix délibéré, pas un abandon) — un
     projet qui y vit peut repartir vers une soumission à comité plus tard sans
     reprendre aucun travail, seul le geste de dépôt Phase 4 change alors ;
   - **`clos_abandonne/`** reste réservé aux projets arrêtés **avant** d'avoir
     atteint la porte 3 (draft stable) ou la porte 5, faute de résultat exploitable
     — un cas distinct des trois précédents, où le projet n'a jamais atteint son
     point final ;
   - **`clos_accepte/`** n'est pas une destination de clôture mais la suite de
     `clos_soumis/` : le projet y passe le jour de la notification d'acceptation,
     avec sa ligne au `clos_accepte/README.md` (revue, date, DOI de l'article et du
     dépôt de données, dettes restantes : camera-ready, publication du dépôt Zenodo
     réservé, mise à jour du préprint). Un projet ne va jamais directement de la
     Phase 5 à `clos_accepte/`, il y monte depuis `clos_soumis/`.

   Déplacement par `outils/deplacer_projet.py` (sous `~/docs/environnement/`), qui
   emporte la mémoire native Claude, les transcripts et les entrées de configuration,
   indexés par le chemin absolu — un `mv` nu les laisse derrière. Jamais `rm`, et
   `gio trash` pour toute suppression.

### Porte 5

Le projet n'est plus dans la liste des projets actifs, sa ligne est au registre
de clôture qui correspond à son mode de diffusion (`clos_soumis/`, `clos/` ou
`clos_abandonne/`), la KB est à jour, et le registre de sérendipité du
parent porte ce qui a survécu au projet.

---

## Modes d'invocation

- **`/cycle-projet`** ou **`status`** (défaut) — situer le projet : lancer
  `cycle_status.py`, afficher la phase déclarée, les mesures, et signaler tout
  désaccord entre la phase déclarée et ce que les artefacts montrent.
- **`/cycle-projet gate`** — instruire la porte de la phase courante : énoncer ses
  conditions une par une, dire pour chacune si elle est remplie **et sur quelle
  preuve**, puis rendre FRANCHIE / NON FRANCHIE. Ne jamais rendre FRANCHIE sur une
  impression : une condition non mesurable est une condition non remplie. Quand la
  phase courante est 3 et que son point fixe est atteint, `gate` ne conclut pas à
  l'entrée en phase 4 : il renvoie à **`/verdict-diffusion`**, qui est la porte
  suivante et dont la réponse peut être un retour en phase 1. Sur un projet dont
  le reboot HARD est clos, `gate` instruit la porte 1 quelle que soit la phase
  déclarée, et la rend NON FRANCHIE tant que les deux traces post-clôture
  (recadrage, revue ciblée) ne sont pas « fait le » à une date au moins égale à
  la clôture (encadré de la Porte 1).
- **`/cycle-projet next`** — la prochaine action concrète dans la phase courante,
  une seule, avec le skill qui la porte. **Sur un projet en phase 1 dont la porte 1
  est franchie, cette action est `/verdict-diffusion amont` et rien d'autre** : la
  1bis est la seule chose qui sépare une analyse close d'une rédaction lancée, et
  c'est le moment où elle ne coûte encore rien. **Sur un projet dont le reboot
  HARD vient d'être clos, cette action est `/recadrage` sur l'état post-reboot**,
  puis `/lit-review` ciblée ; jamais le dégel du manuscrit.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/cycle-projet/cycle_status.py [projet]
```

Le script **ne tranche rien** : il fournit les mesures (revue de littérature
présente, pistes ouvertes, acquis sans destination, taille du manuscrit, registres
qualité et leur fraîcheur, version française, préprint, phase déclarée). Le verdict
est rendu ici, à la lecture.

## Erreurs à éviter

- **Ne pas sauter une phase.** Rédiger avant la porte 1, soumettre avant la porte 3,
  archiver avant la porte 5 : ce sont les trois façons connues de perdre du travail.
- **Ne pas lire la clôture d'un reboot HARD comme une porte 1 franchie.** Elle la
  rouvre : recadrage post-clôture, revue ciblée, porte 1 re-prouvée, puis 1bis,
  avant tout dégel du manuscrit (encadré de la Porte 1, `/reboot` étape 4).
- **Ne pas confondre « tourner en rond » et « point fixe ».** Le point fixe se
  démontre par deux tours à vide, pas par la lassitude.
- **Ne pas confondre « tour à vide » (lettre) et « aucune direction actionnable »
  (esprit).** Un item trouvé puis tué proprement par le challenge lui-même compte
  comme un tour à vide ; exiger zéro item touché, même correctement écarté, ouvre
  une régression sans fin sur tout sujet déjà bien balayé. Voir l'encadré dédié en
  Porte 1.
- **Ne pas passer du message au squelette sans le narratif.** C'est la façon la plus
  fréquente de produire un article exact et illisible : l'ordre du chantier tient lieu
  de plan, et tout ce qui a coûté du temps réclame sa place.
- **Ne pas confondre porte 3 et porte 3bis.** La première prouve que le manuscrit est
  bien fait, la seconde que le résultat méritait d'être écrit. Un pipeline qualité
  entièrement vert ne dit rien de la valeur de ce qui a été démontré.
- **Ne jamais faire entrer le coût déjà engagé dans un verdict.** « On a déjà écrit
  quinze pages » est la définition du biais des coûts irrécupérables, pas un argument
  de publiabilité.
- **Ne pas laisser l'état prendre du retard** dès que la rédaction commence :
  l'état reste la vérité pendant toute la phase 3.
- **Ne pas proposer une cible qui force à couper** sans dire où va le matériel coupé
  (un refactoring en plusieurs articles est une réponse, une coupe sèche n'en est
  pas une).
- **Ne pas archiver sans la passe de sérendipité** : après le déplacement, le
  `pistes.md` du projet ne sera plus jamais relu.
- **Ne jamais `rm`** : `gio trash`.

## Frontière avec les skills voisins

`mtbc-bilan` **photographie** l'état ; `/recadrage` **range** les acquis par
destination ; `mtbc-prospect` **imagine** des directions ; `/reboot` **repart d'un
acquis re-prouvé** quand le projet a été rattrapé par le temps ; `/verdict-diffusion`
**juge** si le résultat mérite d'être publié et par
quelle voie ; `/narratif` **ordonne** l'acquis en démonstration et donne à chaque fait
son lieu. `cycle-projet` **séquence** : il est le seul à dire *dans quel ordre* et
*à quelle condition on avance*. Il appelle les autres, il ne les remplace pas.
