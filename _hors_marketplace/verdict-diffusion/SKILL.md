---
name: verdict-diffusion
description: Les deux portes de décision du cycle, qui demandent si un travail MÉRITE d'être écrit puis diffusé. Porte 1bis (`amont`, AVANT toute rédaction) — faut-il rédiger, recadrer, élargir la question, ou classer un sujet creux ou déjà publié ? Porte 3bis (défaut, manuscrit stabilisé) — soumettre, préprint seul, ne pas diffuser, ou rouvrir ? Rend UN verdict argumenté, jamais un menu. Use on `/verdict-diffusion`, `/verdict-diffusion amont`, `/verdict-diffusion read`, or "est-ce que ça vaut la peine d'écrire cet article", "faut-il se lancer dans la rédaction", "le sujet est-il assez solide", "est-ce que ça mérite d'être soumis", "est-ce publiable", "faut-il soumettre ou juste un préprint", "ce travail vaut-il un article", "on soumet ou pas".
argument-hint: "[amont | read] [chemin-projet]"
---

# verdict-diffusion — Ce travail mérite-t-il d'être écrit, puis publié, et où

Le pipeline qualité mesure si le manuscrit est **bien fait**. Aucun de ses skills ne
demande si le **résultat** mérite d'exister comme publication. C'est deux questions
différentes, et la seconde n'a jamais eu de porte.

La preuve qu'elle en avait besoin est dans le dépôt : le projet
`Mycobacterium_sp_novel` a produit 27 pages, trois relectures internes, un
`claim-check` et un `bib-check` verts — et sa découverte centrale était un double
artefact. Tous les contrôles de fabrication étaient au vert pendant que la science
était fausse. Un manuscrit bien fait autour d'un résultat sans valeur franchit la
porte 3 sans effort.

> [!IMPORTANT]
> **Ce skill rend UN verdict, pas trois options.** L'auteur arbitre l'action — c'est
> son travail et sa signature. Mais il arbitre à partir d'un jugement tranché et
> argumenté, jamais d'un menu qui lui rend la décision intacte. Un « à toi de voir »
> est un refus de faire le travail.

## Place dans le cycle

Ce skill porte **deux** portes, la même question posée à deux moments où elle ne
coûte pas le même prix.

- **Porte 1bis** (`/verdict-diffusion amont`), entre la porte 1 et la phase 2 :
  **faut-il écrire ?** Section « Mode `amont` » en fin de fichier — s'y reporter
  directement, le reste de ce document décrit la porte aval.
- **Porte 3bis** (mode par défaut, décrit ci-dessous), entre la porte 3 et la
  phase 4 : **faut-il diffuser, et où ?**

La 3bis n'est pas une sixième phase : une phase est un corps de travail de
plusieurs semaines, ceci est une décision d'une heure. Mais c'est une vraie porte,
avec une propriété que seule la 1bis partage : **elle peut renvoyer le projet en
arrière**, en phase 1.

**Pourquoi deux portes et non une.** La 3bis, seule, rattrape les erreurs après
qu'elles ont coûté un manuscrit — c'est exactement ce qui est arrivé à
`mtbc/projets_clos_non_soumis/Rv0007`, arrêté sur une thèse déjà publiée par sa
propre source primaire, après 643 lignes rédigées et trois relectures. La 1bis
pose la même question quand elle ne coûte encore rien. Leur exigence diffère en
conséquence : la 1bis est **clémente** (dans le doute, on rédige), la 3bis est
**stricte** (dans le doute, on ne diffuse pas). Cette asymétrie est délibérée.

Sans elle, la phase 4 tranchait le mode de diffusion comme une **préférence de
l'auteur** (temporisation, priorité, choix personnel). C'est légitime et ça le
reste, mais ça ne répond pas à la question scientifique : ce résultat vaut-il un
comité de lecture ? La porte 3bis produit la réponse scientifique ; le mode (a),
(b), (c) ou (d) de la phase 4 reste l'arbitrage de l'auteur, désormais informé.

## Les quatre verdicts

| Verdict | Sens | Suite |
|---|---|---|
| **SOUMETTRE** | le résultat est neuf, sa preuve tient la charge qu'il lui fait porter, et un débouché réel existe | phase 4 mode (a) |
| **DIFFUSER-SANS-COMITE** | le travail vaut d'être public et daté, mais sa preuve ne tiendra pas devant un relecteur, ou sa taille n'est pas celle d'un article | phase 4 mode (b) ou (c) |
| **NE-PAS-DIFFUSER** | réplication de l'existant, ou résultat central expliqué par un artefact irréparable | phase 4 mode (d), puis phase 5 — le savoir part à la KB et aux registres, pas à la poubelle |
| **ROUVRIR** | la question posée n'est pas décidable en l'état, mais une analyse accessible la décide, ou une question plus large la remplace avantageusement | **retour phase 1**, pistes ouvertes, verdict rejoué ensuite |

**DIFFUSER-SANS-COMITE n'est pas un lot de consolation.** Un préprint est public et
engage le nom de l'auteur autant qu'un article. Ce verdict dit : ce résultat mérite
d'être daté et lisible, mais le soumettre serait acheter un billet de loterie avec
le temps de trois relecteurs. Il ne sert jamais à éviter de prononcer
NE-PAS-DIFFUSER.

## Conflit d'intérêt, et comment on le neutralise

**L'instance qui a rédigé le manuscrit est structurellement le plus mauvais juge de
ce manuscrit** : elle a écrit la lettre d'accompagnement qui plaide pour lui, elle a
formulé les acquis dans l'état, et elle porte le coût déjà engagé. Deux mesures ne
lui appartiennent donc pas et se délèguent à une instance **sans accès au contexte
de rédaction** (`Agent`, jamais `fork`) :

1. **La passe adversariale** — mandat explicite de construire le dossier le plus
   solide CONTRE la soumission, en lisant `résultats/` et pas seulement le `.tex`.
2. **Le contrôle de nouveauté** — refait EN DIRECT, jamais lu dans le §5 de
   `etat_des_decouvertes.md`, qui a été écrit par la même main que le manuscrit.
   `tbmonitor-papers` d'abord pour TB/MTBC, puis Europe PMC en **plein texte** (un
   gène cité dans le corps d'un article n'apparaît presque jamais dans son résumé —
   voir le skill `literature-access`), puis les préprints récents.

Le reste du travail — lecture des registres, application du barème, rédaction du
verdict — se fait ici.

## Les cinq axes

Chaque axe porte sa question, sa **mesure** et son **falsificateur**. Un axe non
mesuré est un axe non rempli : il ne se comble pas à l'estime.

**N — Nouveauté.** Existe-t-il au moins une affirmation qui ne soit pas déjà dans la
littérature ? *Mesure* : contrôle de nouveauté en direct, affirmation par
affirmation. *Falsificateur* : un article publié qui énonce déjà l'affirmation.
Contredire une affirmation publiée compte comme neuf ; la re-dériver ne compte pas.

**P — Charge de preuve.** La preuve réelle de l'affirmation qui porte le titre est-elle
de la force que ses mots lui prêtent ? *Mesure* : niveau de preuve (expérience
directe / jeux de données indépendants / tirage in silico unique / silence de base de
données) confronté au verbe employé, plus l'explication **méthodologique** la plus
probable du signal et le témoin qui la discrimine. *Falsificateur* : un contrôle
jamais fait qui aurait produit le même signal.

**D — Décidabilité et coût de la décision.** Le manuscrit tranche-t-il la question
qu'il pose ? Sinon, la preuve manquante est-elle hors de portée (paillasse : c'est
une limite déclarée, elle ne bloque pas) ou **accessible en quelques jours in
silico** ? *Falsificateur* : une analyse faisable qui ferait passer l'affirmation de
« convergente » à « tranchée ». **C'est l'axe le plus décisif du barème** : si le
relecteur va demander une analyse que nous pouvons faire nous-mêmes, la faire vaut
mieux que soumettre.

**U — Unité de contribution.** Y a-t-il un article, ou une note, une entrée d'atlas,
un supplementary d'un autre papier ? *Mesure* : nombre d'affirmations neuves
indépendantes qui survivent à N, et le message tient-il en une phrase falsifiable
(exigence déjà posée en phase 2). *Falsificateur* : tout le contenu tient comme
section d'un manuscrit existant — c'est alors un TRANSFÉRER de `/recadrage`, pas une
soumission.

**E — Débouché réel.** Une revue accepte-t-elle ce **genre** de travail dans sa
pratique effective ? *Mesure* : `computational_only` de `journals.tsv`, et le compte
d'articles comparables réellement publiés sur douze mois — jamais la page « aims and
scope ». *Falsificateur* : zéro comparable en douze mois dans le niveau visé.

## La règle de décision, dans cet ordre

1. **N = 0** → **NE-PAS-DIFFUSER**, *sauf* si les données DÉJÀ PRODUITES portent une
   question neuve, auquel cas **ROUVRIR**. Réplication : le savoir va à la KB et à
   l'atlas, le manuscrit est archivé. **Toujours poser la question de l'exception
   avant de conclure** : un manuscrit dont la thèse est morte a très souvent produit,
   en chemin, une mesure que personne n'a faite — un contrôle qui échoue, une
   asymétrie de méthode, un artefact reproductible. Archiver le projet sans l'avoir
   cherchée jette la seule chose qui restait. Cette exception a été ajoutée le
   2026-09-02, à la première application sérieuse de ce barème : la règle telle
   qu'écrite aurait classé un projet dont la thèse était bien morte, alors que ses
   propres fichiers de sortie contenaient un résultat méthodologique vérifié et
   généralisable à tout le dépôt.
2. **Signal central expliqué par un artefact** → **ROUVRIR** si le témoin manquant
   est faisable, **NE-PAS-DIFFUSER** si l'artefact est fatal et irréparable.
3. **Une analyse in silico accessible trancherait la question** → **ROUVRIR**. C'est
   la garde contre le défaut que le cycle nomme lui-même : s'arrêter trop tôt.
4. **U insuffisant** (une note, pas un article) **ou E nul** (aucun débouché réel
   pour ce genre) → **DIFFUSER-SANS-COMITE**.
5. **Sinon** → **SOUMETTRE**, conditionné à la reformulation si P a trouvé un écart
   entre la force des mots et celle de la preuve. Cette reformulation est une action
   **bloquante**, pas une suggestion.

Le verdict porte sur le manuscrit **tel qu'il est**, jamais tel qu'il pourrait être.

## Niveau de contribution (obligatoire quand le verdict est SOUMETTRE)

SOUMETTRE dit que l'article PEUT être envoyé ; il ne dit rien de ce qu'il vaut une fois
là-bas. Sans un second jugement, chaque SOUMETTRE se lit comme le même « +1 » générique,
alors qu'une correction d'un biais de pipeline déjà documenté ailleurs et un renversement
d'une conclusion citée du sous-champ n'appellent ni le même choix de cible, ni la même
attente côté auteur. Ce niveau n'est jamais une politesse ni une sanction : c'est une
lecture calibrée, aussi exigeante à la hausse qu'à la baisse.

**Échelle fixe, jamais un chiffre ou un adjectif libre.** Chaque niveau exige sa preuve
mesurée, pas une impression — même logique anti-inflation que le barème MIU du skill
`pistes` (une I≥2 exige une clause qui dit ce que ça change).

| Niveau | Critère mesuré | Test de calibration |
|---|---|---|
| **RUPTURE** | remet en cause une conclusion PUBLIÉE et citée du domaine, ou tranche une question que personne n'avait posée sous cette forme | un lecteur qui connaît l'article contredit peut-il encore le citer sans réserve après celui-ci ? |
| **AVANCÉE** | établit un fait nouveau qui change la pratique ou l'interprétation d'un sous-champ actif, avec une preuve qui tient sans réserve majeure | un spécialiste du sous-champ changerait-il un choix méthodologique ou une lecture après avoir lu l'article ? |
| **SOLIDE** | contribution correcte et bien menée, qui ferme une question ouverte ou réplique/étend un résultat avec une preuve propre, mais de portée locale | la conclusion aurait-elle surpris quelqu'un qui suit déjà ce sous-champ de près, ou seulement confirmé ce qu'il pressentait ? |
| **MINEUR (weak accept)** | résultat vrai et correctement établi, mais de portée étroite : réplication avec une nuance, correction technique sans généralisation démontrée, extension incrémentale | le résultat tiendrait-il en une note, un paragraphe ou un supplementary d'un autre article plutôt qu'en article séparé ? |

**Déduction à partir des cinq axes déjà mesurés, jamais d'une impression séparée** :
- N élevé (contredit une affirmation publiée, pas seulement une absence de littérature) **et**
  P fort (preuve directe, réplication indépendante, pas seulement convergente) → candidat
  RUPTURE ou AVANCÉE selon la portée du champ concerné (tout le domaine, ou un sous-champ).
- N réel mais P partiel (preuve convergente ou indirecte, limite reconnue et non résolue) →
  SOLIDE.
- N faible (étend sans contredire, contexte déjà largement anticipé) ou U fragile (proche
  du seuil qui aurait donné DIFFUSER-SANS-COMITE) → MINEUR.

**Le paragraphe de justification, dans le registre, doit nommer explicitement les trois
mêmes choses à chaque fois** : (a) ce que la littérature tenait pour établi sur ce point
précis avant cet article ; (b) ce que l'article change concrètement à cette croyance ou
cette pratique, avec le fait précis qui porte le changement ; (c) la limite qui empêche
de monter d'un cran, énoncée sans détour. Un paragraphe qui ne fait que (a)+(b) sans (c)
n'est pas calibré, il est complaisant.

**Erreur à éviter, dans les deux sens.** Ne pas gonfler le niveau pour flatter le travail
engagé (le biais des coûts irrécupérables, déjà nommé plus bas, s'applique identiquement
ici) — mais ne pas sous-noter par excès de prudence non plus : un résultat qui renverse
effectivement une lecture publiée EST une rupture, le dire à mi-voix ne le rend pas plus
rigoureux, et prive l'auteur de l'information dont il a besoin pour choisir sa cible et
son ton de lettre d'accompagnement.

## Ce que chaque verdict déclenche

- **SOUMETTRE** : phase 4 mode (a), `/soumission` prend la suite. `preflight.py`
  vérifie mécaniquement que ce verdict existe et est favorable avant tout dépôt, ET que le
  registre porte une clé `niveau` non vide (voir section dédiée ci-dessus) — un SOUMETTRE
  sans niveau est un verdict incomplet. Le niveau informe directement le choix de cible dans
  `/soumission` : une RUPTURE/AVANCÉE vise le haut de la liste des revues motivées, un MINEUR
  vise une cible à options gratuites et un délai de décision rapide plutôt qu'un pari long sur
  un titre prestigieux.
- **DIFFUSER-SANS-COMITE** : phase 4 mode (b) ou (c). Le préprint se dépose avec ses
  limites énoncées dans le texte, pas masquées.
- **NE-PAS-DIFFUSER** : phase 4 mode (d), puis phase 5, archivage dans
  `projets_clos_non_soumis/`. **Obligatoire avant l'archivage** : passe `/recadrage`
  complète, pour que les acquis partent en destination C1/C2/E et que la KB reçoive
  ce qui est transférable. Un projet non diffusé n'est pas un projet perdu ; un
  projet non diffusé ET non rangé, si.
- **ROUVRIR** : les pistes correspondantes s'ouvrent dans `pistes.md` (état
  `[à faire]`, `origine : verdict-diffusion <date>`), et **rien n'est supprimé** —
  le manuscrit, les figures et les registres restent, ils resserviront. Le verdict
  se rejoue quand les pistes ouvertes sont closes.

  **La phase déclarée redescend à 1 POUR LES QUESTIONS ROUVERTES, pas pour le projet
  entier.** Écrire le périmètre dans l'en-tête de `etat_des_decouvertes.md`, par
  exemple `**Phase :** 1/5 pour P5 (questions rouvertes), manuscrit gelé à la porte
  3bis`. Un ROUVRIR ne dit presque jamais que la revue de littérature et tout le
  programme d'analyse sont à refaire : il dit qu'UNE question précise, nommée, doit
  être instruite avec la discipline de la phase 1 (challenge, littérature, modèle
  nul) avant que le manuscrit puisse repartir. Déclarer le projet entier en phase 1
  pour une analyse manquante d'une journée est faux, décourageant, et fait perdre la
  trace de tout ce qui était acquis.

## Le registre `verdict_diffusion.md`

À la racine du projet, à côté de `claim_check.md` et `fig_check.md`. **Verdicts
empilés du plus récent au plus ancien** : c'est le premier bloc que lisent les
outils, et les verdicts passés ne se suppriment jamais (un ROUVRIR suivi six mois
plus tard d'un SOUMETTRE est précisément ce qu'on veut pouvoir relire).

En-tête normalisé, machine-lisible, quatre clés exactement dans cet ordre — cinq quand le
verdict est `SOUMETTRE`, la cinquième (`niveau`) n'existant que dans ce cas :

```markdown
## Verdict du 2026-09-02

verdict : SOUMETTRE
niveau : SOLIDE
rendu le : 2026-09-02
manuscrit : article/main.tex
renversé par : <le fait précis, vérifiable, qui changerait ce verdict>
```

`verdict` prend exactement une des quatre valeurs : `SOUMETTRE`,
`DIFFUSER-SANS-COMITE`, `NE-PAS-DIFFUSER`, `ROUVRIR`. `niveau`, présent seulement sur
`SOUMETTRE`, prend exactement une des quatre valeurs de l'échelle ci-dessus (`RUPTURE`,
`AVANCÉE`, `SOLIDE`, `MINEUR`) — jamais un chiffre, jamais absent sur un SOUMETTRE. Puis le
corps : les cinq axes avec leur mesure et leur source, la sortie de la passe adversariale et
du contrôle de nouveauté (résumées, avec ce qu'elles ont trouvé et non seulement leur
conclusion), la règle qui a tranché, le paragraphe de justification du niveau si SOUMETTRE
(les trois éléments (a)/(b)/(c) de la section dédiée), et les actions bloquantes s'il y en a.

**Péremption.** Un verdict vieux de plus de trois mois, ou rendu avant un résultat
nouveau, ne vaut plus : le rejouer. `preflight.py` signale un `main.tex` modifié
après la date du verdict.

## Modes

- **`/verdict-diffusion`** (défaut) — rendre le verdict : lancer les deux instances
  indépendantes, mesurer les cinq axes, appliquer la règle, écrire le registre — en ajoutant,
  si le verdict est SOUMETTRE, le niveau de contribution et son paragraphe de justification
  (a)/(b)/(c) — puis énoncer le verdict, le niveau s'il y a lieu, et sa justification à
  l'écran.
- **`/verdict-diffusion read`** — lire le verdict courant, sa date, sa péremption.
- **`/verdict-diffusion amont`** — la **porte 1bis**, avant d'écrire la moindre
  ligne. Section dédiée ci-dessous.

## Mode `amont` — la porte 1bis, avant toute rédaction

**Quand** : porte 1 franchie (plus rien à analyser), avant d'entrer en phase 2.
**Question** : ce qu'on a appris mérite-t-il d'être rédigé ?

**Pourquoi ce mode existe** (arbitrage CG du 2026-09-04). Tout ce skill est arrivé
trop tard une fois de trop : `mtbc/projets_clos_non_soumis/Rv0007` a franchi la
porte 1, écrit 643 lignes de manuscrit, passé cinq skills de pipeline qualité et
trois relectures — puis la porte 3bis a établi que sa thèse était **déjà publiée
par l'article qu'il citait en première ligne**, qui l'énonçait dans son résumé, sa
Discussion et ses légendes de figure. Le contrôle qui l'aurait sauvé était une
lecture plein texte de sa source primaire, faisable avant le premier paragraphe.
**Une porte qui ne juge le fond qu'après la rédaction fait payer la rédaction.**

### Les quatre verdicts amont

| Verdict | Sens | Suite |
|---|---|---|
| **RÉDIGER** | le message tient, sa preuve est à sa hauteur, il a un débouché | phase 2, et le geste suivant est **`/narratif`**, jamais le squelette |
| **RECADRER** | il y a de la matière, mais pas celle qu'on croyait porter | `/recadrage`, nouveau §1, puis re-verdict |
| **ÉLARGIR** | la question est trop étroite pour un article ; une question qui l'englobe en ferait un | **retour phase 1** sur la question élargie |
| **CLASSER** | déjà publié, ou creux : rien qui vaille d'être rédigé | phase 5 directement |

### La règle du doute, asymétrique et non négociable

> [!IMPORTANT]
> **Dans le doute, RÉDIGER.** Cette porte est délibérément **plus clémente que la
> 3bis**, pour une raison de coût asymétrique : un manuscrit rédigé puis arrêté à
> la 3bis coûte des jetons, un projet sain tué à la 1bis coûte le projet.
> **CLASSER ne se prononce que sur une preuve POSITIVE** — une source qui énonce
> déjà l'affirmation, ou l'absence mesurée de tout énoncé à défendre. Jamais sur
> une impression de faiblesse, jamais sur « ça ne m'a pas l'air très fort ». Un
> doute sur l'intérêt d'un résultat n'est pas un doute sur son existence, et
> l'histoire de la discipline est pleine de résultats jugés ternes par leur auteur.

### Les cinq axes, mesurés sur l'ÉTAT et non sur un manuscrit

Il n'y a encore rien d'écrit : la matière est `etat_des_decouvertes.md` §2, et
**l'affirmation qui portera le titre, formulée à l'avance en une phrase
falsifiable**. Sans cette phrase, la porte n'a rien à juger et le premier travail
est de l'écrire.

- **N — nouveauté. Axe cardinal, et le SEUL dont l'échec suffit à prononcer
  CLASSER.** Délégué à une instance sans accès au projet, comme en 3bis. Une
  exigence propre à ce mode : **lire le PLEIN TEXTE des deux ou trois sources
  primaires** que le futur article contredit ou prolonge, résumés insuffisants.
  C'est très exactement là que Rv0007 s'est perdu — la source disait dans sa
  Discussion le contraire de ce que le projet lui prêtait, et personne n'avait
  ouvert le texte intégral avant d'écrire.
- **P — charge de preuve** : le niveau de preuve disponible soutient-il le VERBE
  du message envisagé ? Corriger « nous montrons que » en « nos données sont
  compatibles avec » coûte ici une ligne, après rédaction une réécriture.
- **D — décidabilité. C'est l'axe au meilleur rendement de toute la porte.** Une
  analyse accessible ferait-elle passer le message de « convergent » à
  « tranché » ? Si oui, **la faire maintenant**, avant d'écrire : le manuscrit
  sera écrit une fois, autour du résultat fort, au lieu d'être écrit autour du
  faible puis rustiné.
- **U — unité** : un article, une note, ou une section d'un manuscrit existant ?
  Répondre « une note » ne ferme rien, cela fixe le format visé — et évite
  d'écrire vingt pages pour un objet qui en vaut trois.
- **E — débouché** : ce genre se publie-t-il réellement quelque part ? Mesuré sur
  la pratique effective d'une revue, jamais sur sa page « aims and scope ».

### Registre

Même fichier `verdict_diffusion.md`, même en-tête machine-lisible, la clé
`verdict` prenant une des quatre valeurs amont. Ajouter `porte : 1bis` pour que
les deux familles de verdicts ne se confondent pas à la relecture :

```markdown
## Verdict amont du 2026-09-04

verdict : RÉDIGER
porte : 1bis
rendu le : 2026-09-04
message visé : <l'affirmation qui portera le titre, en une phrase falsifiable>
renversé par : <le fait précis qui changerait ce verdict>
```

### Ce que ce mode ne fait pas

Il ne juge pas la qualité d'un texte (il n'y en a pas), ne remplace pas
`/recadrage` (qui range les acquis, quand celui-ci décide s'il faut écrire), et
**ne rejoue pas la porte 1** : si des pistes sont encore ouvertes, ce n'est pas
ce mode qu'il faut, c'est du travail d'analyse.

## Erreurs à éviter

- **Le coût déjà engagé n'entre dans aucun axe.** « On a déjà écrit quinze pages »
  n'est pas un argument, c'est la définition du biais des coûts irrécupérables.
- **Ne pas confondre porte 3 et porte 3bis.** Bien fait n'est pas digne d'être fait.
- **Ne pas juger le manuscrit sur ses propres affirmations** : lire `résultats/`, les
  sorties réelles, les chiffres. Un manuscrit décrit toujours sa preuve sous son
  meilleur jour.
- **Ne pas se servir du préprint comme d'une poubelle** pour éviter de prononcer
  NE-PAS-DIFFUSER.
- **Ne pas rendre le verdict sans la passe adversariale indépendante** quand c'est la
  même session qui a rédigé.
- **Ne pas être négatif par principe.** Une porte qui ne laisse jamais rien passer
  est aussi cassée qu'une porte qui laisse tout passer. SOUMETTRE est la bonne
  réponse quand le travail est bon, et il faut savoir la donner nettement.
- **Ne jamais rendre SOUMETTRE sans niveau, et ne jamais calibrer ce niveau à l'estime.**
  Un SOUMETTRE nu ne dit pas si l'auteur tient une rupture ou un weak accept — les deux
  cas existent réellement et n'appellent ni la même cible de revue ni le même ton de lettre
  d'accompagnement. Le niveau se déduit des axes déjà mesurés (N, P surtout), jamais d'une
  impression tenue à part ; ni complaisant envers le travail engagé, ni prudent par réflexe.

## Frontière avec les skills voisins

`/manuscript-review` juge le **texte** et le rend meilleur ; `/claim-check` vérifie
que chaque affirmation **correspond à sa source** ; `/challenge` filtre une
proposition **avant** qu'on y travaille ; `/recadrage` demande si chaque acquis est
**au bon endroit** ; `/cadrage-editorial` demande, une fois la revue choisie, si la
**vitrine** dit à cette revue ce qu'elle publie. `verdict-diffusion` est le seul à
demander si le résultat mérite d'exister comme publication, et le seul dont la réponse
peut être **non**.

Le partage avec `/cadrage-editorial` est net et vaut d'être rappelé, parce que les deux
skills peuvent renvoyer un projet en arrière. Cette porte-ci juge le **résultat**, sans
connaître la revue, et son verdict porte un niveau de contribution. Celle-là juge
l'**adéquation de la présentation à une cible nommée**, en aval, et ne peut jamais
relever le niveau : un `niveau : MINEUR` interdit un titre de rupture, quelle que soit
l'envie de maximiser les chances. Quand le cadrage conclut qu'aucune vitrine honnête
n'existe pour ce niveau de revue, il rend `ROUVRIR` et la question remonte ici.
