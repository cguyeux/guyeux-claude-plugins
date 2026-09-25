---
name: challenge
description: Adversarial check on a proposal before launching work OR on a result already obtained, applied alike to the user's ideas and the assistant's own. Use on `/challenge <proposition>`, or "challenge cette idée", "prends du recul", "joue l'avocat du diable", "est-ce que ça vaut le coup", "vérifie avant de te lancer", before any non-trivial analysis or computation — and, mode RÉSULTAT, on "ce résultat est surprenant", "ça contredit ce qu'on pensait", "vérifie avant que j'y croie", before writing a counter-intuitive or literature/KB-contradicting finding into `etat_des_decouvertes.md`, before closing a piste on a surprising positive result, or before a manuscript section built on such a result.
argument-hint: "<proposition à challenger, ou 'résultat <description>' pour le mode post-hoc>"
---

# challenge — Crible adversarial avant de se lancer, et avant d'y croire

Ce skill opérationnalise la prise de recul, à deux moments distincts. **Mode
PRÉ-VOL** (par défaut) : avant de coder ou de lancer un calcul non trivial, on
passe la proposition au crible pour éviter trois échecs récurrents :
redécouvrir du connu, se jeter dans un calcul mal cadré, et oublier ce qui a
déjà été tenté. **Mode RÉSULTAT** (§ dédiée plus bas) : sur un résultat DÉJÀ
obtenu et surprenant, avant de le consolider comme acquis. Les deux modes
s'appliquent symétriquement aux idées de l'utilisateur et à celles de
l'assistant — la symétrie est volontaire, et plus encore en mode RÉSULTAT, où
l'enthousiasme pour une découverte inattendue est précisément ce qui empêche de
la challenger spontanément.

L'argument est la **proposition à challenger** (mode pré-vol) ou le **résultat
à contre-expertiser** (mode résultat, préfixer `résultat` ou laisser le contexte
trancher — un résultat déjà obtenu et surprenant déclenche le mode résultat même
sans préfixe explicite). Si aucun argument n'est fourni, challenger la dernière
action ou le dernier résultat substantiel de la conversation.

Déclencheurs pré-vol : `/challenge <proposition>`, « challenge cette idée », « prends du
recul », « joue l'avocat du diable », « est-ce que ça vaut le coup », « vérifie
avant de te lancer », et plus généralement tout moment précédant l'engagement
dans une analyse ou un calcul non trivial.

Déclencheurs résultat : un résultat contre-intuitif, une émergence multiple
indépendante, une corrélation spectaculaire, une nouveauté taxonomique ou
mécanistique, tout énoncé qui contredit la KB, la littérature ou l'attente de
départ, avant de l'écrire dans `etat_des_decouvertes.md` comme prouvé, avant de
clore une piste dessus (`/pistes done`), ou avant qu'il n'entre dans un
manuscrit. Aussi sur demande explicite : « challenge ce résultat », « est-ce que
j'y crois vraiment », « prends du recul sur cette découverte ».

## Localiser le contexte

Remonter jusqu'à la racine projet (premier répertoire avec `cahier_de_labo.md`).
Lire, pour ancrer les contrôles : `etat_des_decouvertes.md` (objectifs +
prouvé/infirmé), `pistes.md` (ce qui est déjà fait/en cours/abandonné), et
l'index de `litterature_review/`. Hors projet, faire les contrôles 4-6 seulement.

## Les six contrôles

1. **Déjà fait ?** — Chercher dans `cahier_de_labo.md` et `pistes.md` une
   entrée/piste équivalente (`[réalisé]`, `[en cours]`, ou `[abandonné]` avec
   raison). Si oui : le signaler et s'arrêter là (ne pas refaire).
2. **Déjà publié ?** — Confronter à `litterature_review/`. Si le sujet n'a pas
   été couvert, recommander `/lit-review <sujet>` (et, si votre domaine dispose
   d'un outil de veille documentaire dédié, le lancer aussi) AVANT tout calcul.
   C'est le garde-fou anti-redécouverte.
   Si ce qui « a déjà été publié » vient trancher la proposition, peser son
   poids avec le contrôle dédié plus bas (« Peser l'autorité d'une source »)
   avant de l'accepter comme verdict.
3. **Aligné aux objectifs ?** — Confronter à `etat_des_decouvertes.md §1`. Si la
   proposition n'avance aucun objectif courant, le dire franchement (dérive
   hors-sujet) et demander si un objectif doit être révisé.
4. **Contre-argument le plus fort** — Formuler explicitement la meilleure
   objection à la proposition (rôle d'avocat du diable, y compris contre une
   demande de l'utilisateur). Quelle hypothèse cachée pourrait la faire échouer ?
5. **Quel modèle nul / contrôle la falsifierait ?** — Exiger la formulation d'un
   test qui pourrait tuer l'hypothèse (contrôle négatif, modèle nul, calibration
   de puissance). Une proposition qu'aucun résultat ne pourrait infirmer n'est
   pas prête.
5bis. **CALCUL DE PUISSANCE, avant tout, dès que la proposition promet de MESURER.**
   Ne pas se contenter de citer la puissance comme un principe : la **calculer**, avec
   l'effectif réel du sous-groupe sur lequel la mesure portera, pas l'effectif total du
   corpus. Trois questions : sur combien d'unités la quantité visée s'estime-t-elle
   réellement ? quel intervalle de confiance cela donne-t-il ? cet intervalle
   permet-il de trancher la question posée ? Si non, la proposition est morte, quelle
   que soit sa pertinence.
   *(Vécu 2026-08-17 : projet d'audit de performance d'un diagnostic sur 696 souches
   d'un groupe rare. Effectif réel utile = les seules souches RÉSISTANTES, soit ~40 au
   taux observé en cohorte, d'où un IC95 de ± 11 points sur la sensibilité, et ± 17
   points à taux plus bas. Sur un autre médicament : 6 souches, IC95 [54-100 %], zéro
   information. La proposition avait été formulée, journalisée et présentée avant que
   ce calcul de trois lignes ne soit fait.)*
   Signal d'alarme : un dénominateur impressionnant (« 129 000 génomes », « 52 000
   souches ») cité pour justifier une mesure qui, elle, se joue sur un sous-groupe de
   quelques dizaines d'unités. **Toujours descendre au dénominateur EFFECTIF.**
6. **Gain attendu vs coût** — Estimer le bénéfice scientifique (qu'apprend-on si
   ça marche ? si ça échoue ?) et le coût (temps de calcul, données à récupérer,
   complexité). Le jeu en vaut-il la chandelle ?

## Peser l'autorité d'une source, quand deux claims s'opposent

Se déclenche chaque fois qu'un claim de la littérature sert d'arbitre — pour tuer
une proposition (contrôle 2 ci-dessus), pour nommer un canonique (test A
ci-dessous), ou pour fournir la contre-explication d'un résultat surprenant
(contrôle 2 du mode RÉSULTAT plus bas) — et plus encore quand DEUX claims se
contredisent et qu'un seul doit guider la décision.

Trois axes à évaluer :

1. **L'auteur.** Spécialiste reconnu du domaine PRÉCIS (pas d'un domaine
   voisin), visible dans la communauté : H-index dans le domaine, comité
   éditorial, conférences invitées. Réutiliser le skill `profil-chercheur` pour
   ce lookup plutôt que le refaire à la main.
2. **La revue.** Spécialiste vs généraliste, indexée (Web of Science/Scopus),
   facteur d'impact ou SJR — un IF brut est un indicateur GROSSIER et
   manipulable (revue prédatrice, auto-citation) : préférer un rang de
   catégorie (percentile) quand disponible, et croiser avec une liste de
   revues prédatrices si le nom n'est pas familier.
3. **Le claim lui-même.** Nombre de citations DE CET ARTICLE précis (pas
   seulement de la revue), et fraîcheur — mais la fraîcheur seule ne dit rien :
   un claim ancien jamais recontesté peut signifier « personne n'a vérifié »,
   pas « c'est solide ».

**Règle de pondération.** La barre pour CONTREDIRE un claim porté par un
spécialiste reconnu, dans une revue de référence du domaine, largement cité et
récent, doit être haute : une preuve spécifique (donnée, échec de
reproduction, erratum ou rétractation documenté), pas une impression. À
l'inverse, un claim porté par des non-spécialistes, dans une revue non
spécialiste ou à faible facteur d'impact, peu cité, mérite d'être marqué
« à consolider » avant d'être bâti dessus ou cité comme acquis — pas rejeté
d'office, mais pas traité à égalité sans corroboration.

**Garde-fou épistémique, à ne jamais perdre de vue.** L'autorité est un signal
de TRIAGE de l'effort de vérification, jamais un arbitre de vérité — sinon
c'est un sophisme d'autorité. Un claim minoritaire, porté par des
non-spécialistes, PEUT être juste contre un grand nom ; ce contrôle dit
combien de vérification il faut avant de le construire dessus, pas s'il faut
le rejeter. Rappel vécu : une classification interne « maison » a parfois plus
de valeur sur un cas précis que le système de référence externe qu'elle
contredit — l'autorité externe n'efface pas une expertise interne mieux
informée.

**Verdict de ce contrôle**, à joindre au verdict global : **Autorité forte**
(barre haute pour contredire ce claim), **Autorité faible / à consolider**
(corroboration requise avant usage), ou **Autorité non évaluable** (source
anonyme, prépublication non révisée, littérature grise — traiter comme non
consolidé par défaut).

## Mode ANTÉRIORITÉ (quand la proposition repose sur des PIÈCES / des CAS)

Déclencher ce mode dès que la proposition s'appuie sur des **documents, des cas, des
observations frappantes** (archives, dossiers cliniques, génomes remarquables, logs).
Les six contrôles ci-dessus ne suffisent PAS : trois thèses ont été tuées ici en une
heure, après des jours d'enthousiasme (cf. [[refuter-sa-propre-piste]]).

### Qui exécute le crible : décider AVANT de déléguer

Le mandat de réfutation ci-dessous vaut quel que soit l'exécutant. Ce qui se décide
d'abord, c'est **qui** le porte. Règle, dans cet ordre :

1. **Boucle principale par défaut, dès que les sources sont LOCALES et RAPIDES.**
   Corpus SQL indexé (`tbmonitor`, ~330 k résumés TB, sub-seconde), plein texte
   Europe PMC (`europepmc_fulltext.py search`), fichiers du projet, PDF sur disque :
   le coût fixe d'un sous-agent (démarrage, exploration de ses propres outils,
   rédaction d'un rapport) dépasse alors le coût de la requête. Quelques requêtes
   suffisent et elles rendent, elles.
2. **Déléguer un agent par thèse UNIQUEMENT si la recherche est LARGE et
   EXPLORATOIRE** : plusieurs angles hétérogènes, sources dispersées, on ne sait pas
   encore ce qu'on cherche. C'est le seul cas où le fan-out paie.
3. **Si l'on délègue, prévoir le repli DÈS le lancement.** Un agent adversarial qui ne
   rend rien est le mode d'échec NOMINAL de ce dispositif, pas un incident : mesuré
   trois fois (2026-07-30 projet Rv2438A, rien en 14 min ; 2026-08-03 dossier ANRS,
   mort sur erreur d'API ; 2026-08-17 dossier ANRS, trois agents sur trois rendus
   inactifs sans rapport, y compris après relance ciblée). Discipline : une seule
   relance, puis refaire le contrôle soi-même, puis `TaskStop`. **Ne JAMAIS conclure en
   supposant ce que l'agent aurait trouvé**, et ne jamais attendre indéfiniment quand
   un chemin direct existe.

Budgéter en appels de recherche et non en agents : chaque agent essaime lui-même 3 à 6
sous-agents sur le même compteur `WebSearch` partagé (5 agents ≈ 25 chercheurs réels,
200 appels consommés en 15 min le 2026-07-29). Détail dans
[[lit-review-fanout-verification]] §7 et §8.

### Le mandat de réfutation (quel que soit l'exécutant)

> « Ton travail n'est PAS d'évaluer cette thèse, c'est de la **RÉFUTER**. Cherche
> activement à démontrer qu'elle est déjà publiée, banale ou fausse. Si tu ne
> parviens pas à la tuer, dis-le — mais ne la sauve pas par politesse. »

Un agent à qui l'on demande d'« évaluer » **valide** ; un agent à qui l'on demande de
**réfuter** réfute. La différence est mesurée, elle est énorme. Quand le crible est fait
en boucle principale, se l'appliquer explicitement à soi-même : chercher ce qui tue sa
propre proposition, pas ce qui la conforte.

Le prompt de l'agent DOIT contenir ces tests, dans cet ordre (A-D toujours ; E dès que la
proposition corrige/audite/re-score une ressource publiée) :

- **A. ANTÉRIORITÉ.** Nommer les 4-5 canoniques du domaine et **lire leurs pièces**, pas
  leurs résumés. Chercher explicitement **le livre dont le titre porte le sujet**. Peser
  chaque canonique avec « Peser l'autorité d'une source » ci-dessus : un canonique mineur,
  isolé, ne pèse pas comme les 4-5 références qui font consensus dans le domaine.
  *(Vécu : un livre de 1999 traitait exactement notre fonds, avec deux chapitres sur
  notre objet. Nous ne l'avions pas ouvert.)*

  **Obligatoire : passer par le PLEIN TEXTE, jamais par les seuls résumés.** Une méthode,
  un jeu de données, un contrôle statistique vivent dans les Méthodes, presque jamais dans
  l'abstract — donc une antériorité méthodologique est structurellement invisible à une
  recherche par résumé. Outil : `europepmc_fulltext.py search "<requête>"`, qui affiche
  l'écart résumé / plein texte.
  *(Vécu 2026-08-17, dossier ANRS : sur les requêtes du crible, le plein texte rendait 52
  à 70 fois plus d'articles que les résumés seuls, et c'est par là que sont sortis les
  trois travaux qui ont tué la proposition — une évaluation de performance déjà stratifiée
  par lignée, un catalogue déjà re-gradué par régression multivariée sur 52 000 isolats, et
  la reconstruction automatisée du catalogue par le consortium qui l'a bâti. Une recherche
  par résumé n'en voyait aucun des trois.)*

  **Et nommer les DÉTENTEURS de la donnée, pas seulement les publications.** Quand la
  proposition consiste à corriger ou enrichir une ressource, demander qui détient le
  matériau brut : si ce sont les auteurs de la ressource ou un consortium, ils ont plus de
  données, plus de compute et un chantier déjà ouvert. Une proposition qui les affronte sur
  LEUR terrain perd, même si elle est juste. Chercher plutôt ce que personne ne peut faire
  à leur place.

- **B. TEST DE LA MOYENNE.** *Mon cas est-il l'exemplaire MÉDIAN d'une série déjà
  quantifiée ?* **Chercher les travaux QUANTITATIFS avant les interprétatifs.**
  *(Vécu : notre cas vedette était taxé 1 200 livres ; la moyenne publiée de la série
  est 1 190. Nous avions trouvé la moyenne arithmétique et l'appelions une découverte.)*
  Corollaire : si tous mes cas sont dans la **queue de la distribution**, je n'ai pas un
  échantillon, j'ai **les monstres d'un corpus choisi pour être frappant**.

- **C. TEST DE LA SOURCE.** *Est-ce un ÉNONCÉ (loi, décision, mesure) ou un PLAIDOYER
  (supplique, requête, mémoire, communiqué) ?* Une pièce de partie est un **acte de
  persuasion, pas un constat** — et sa prémisse peut être **fausse**. Chercher la
  **DÉCISION**, pas seulement la demande.
  *(Vécu : nous citions comme « énoncé du droit du sol » une phrase d'avocat dont la
  prémisse — « la loi ne parle point des enfants » — était factuellement fausse.)*

- **D. TEST DE LA CLAUSE DE STYLE.** *La formule qui me frappe est-elle une formule
  ORDINAIRE du genre documentaire ?* Vérifier dans les manuels de diplomatique, de
  chancellerie, de rédaction du domaine.
  *(Vécu : « par grâce et sans tirer à conséquence », notre pièce à conviction, est la
  clause de style de TOUT acte gracieux royal. Elle prouvait le contraire de ce que nous
  y lisions.)*

- **E. TEST DU RÉSIDU** *(dès que la proposition CORRIGE, AUDITE, RE-SCORE ou FILTRE une
  ressource publiée)*. Un enrichissement brut contre le fond ne prouve rien : la source
  publie presque toujours déjà des colonnes de qualité, des flags, des avertissements.
  Trois questions, dans cet ordre :
  1. **Quel est le résidu APRÈS application des filtres que la source publie déjà ?** Pas
     l'enrichissement, le résidu : compter les entités que mon critère écarte et que le flag
     officiel n'écartait pas.
  2. **De quoi ce résidu est-il composé ?** Décomposer par classe d'entités. Une classe
     structurelle du jeu de données (objets trop courts, trop petits, trop rares pour être
     mesurables) explique souvent tout le signal — et son plafond est technique, donc non
     corrigible, et déjà signalé par une autre colonne.
  3. **Les auteurs énoncent-ils déjà la limite ?** Lire les Methods / STAR Methods, pas
     l'abstract. Et chercher si les MÊMES auteurs ont publié depuis un raffinement : un
     problème qu'on croit ignoré est souvent leur chantier en cours.

  *(Vécu 2026-08-03 : enrichissement réel, monotone, spectaculaire — guides CRISPRi faibles
  ×3,77 dans le top 50 d'un classement de vulnérabilité contre le fond génomique. Décomposé :
  19 des 23 gènes concernés étaient DÉJÀ marqués `certain=False` par les auteurs, et 17 sur 23
  étaient des ARNt, trop courts pour héberger assez de sites PAM. Résidu net : 3 gènes sur
  4052, tous abondamment échantillonnés. Le ×3,77 était exact et sans valeur. En prime les
  auteurs traitaient déjà la question dans un article de 2024, et un consortium avait publié
  la ressource intégrée quatre mois plus tôt.)*

  Signal d'alarme gratuit : **un enrichissement dont on n'a pas regardé QUI le compose.** Si
  l'on sait dire « ×3,77 » mais pas « et ce sont surtout des X déjà flaggés », le test
  n'a pas été fait.

**Piège transversal à vérifier systématiquement — L'INVERSION :**
> *Si ma thèse était vraie, cette pièce existerait-elle seulement ?*

Souvent le document prouve **l'inverse** de ce qu'on y lit. *(Vécu : que le fisc taxe en
1701 un homme né en France en 1664 ne prouve pas que le droit du sol existait — cela
prouve qu'il **ne protégeait de rien**.)*

## Mode RÉSULTAT (sur un résultat DÉJÀ obtenu, avant de le consolider)

Déclencher ce mode dès qu'un résultat obtenu est **surprenant, contre-intuitif,
ou contredit la KB, la littérature ou l'attente de départ** — pas seulement
avant de lancer un calcul, mais après l'avoir obtenu, avant qu'il ne devienne
un acquis écrit (`etat_des_decouvertes.md`, clôture de piste, section de
manuscrit). Les six contrôles pré-vol répondent à « faut-il lancer ? » ; ceux-ci
répondent à une question différente, « dois-je croire ce que j'ai obtenu ? »,
et l'a priori change de signe : un résultat surprenant part avec une
présomption d'échec, pas de succès.

Incident fondateur (anonymisé) : deux manuscrits d'un même groupe soutenaient,
après des semaines d'itérations et plusieurs relectures internes, l'émergence
indépendante répétée d'un variant candidat dans une dizaine de lignées
distinctes d'un pathogène clonal — un résultat spectaculaire, cité comme
argument de sélection positive. Une personne qui relisait a demandé la table
brute souche par souche (lignée, couverture, lectures au codon). Une phrase a
suffi : « la table indique des souches qui portent l'allèle alternatif, alors
qu'on cherche l'allèle dérivé, et l'alternatif est ancestral — qqch
m'échappe ? ». Le pipeline confondait absence d'appel de variant (lue comme
allèle de référence) et allèle réellement porté (ancestral) : les souches
« sans variant » ne portaient en réalité aucune lecture de l'allèle de
référence, seulement des lectures de l'allèle ancestral alternatif. Aucune des
itérations précédentes n'avait rouvert une seule lecture brute ; le résultat
agrégé se répétait d'un texte à l'autre sans jamais redescendre à l'unité.
Détail complet et mécanisme technique : dans une base de connaissances
méthodologique inter-projets, si vous en tenez une.

### Les six contrôles

1. **Prior inversé, explicite.** Écrire la phrase « ce résultat a probablement
   une explication banale » avant de chercher laquelle. Le réflexe à
   remplacer n'est pas "quel calcul supplémentaire le renforcerait" mais "quel
   calcul le tuerait".
2. **Contre-explication nommée.** Formuler l'hypothèse alternative précise —
   artefact technique, convention de mapping, biais de référence, homoplasie,
   effet de lot, erreur de polarité, **métadonnée déclarée erronée (date, pays,
   hôte, lignée/espèce)** — qui produirait EXACTEMENT ce signal sans que
   l'hypothèse centrale soit vraie. Un résultat qu'aucune contre-explication
   plausible ne peut menacer n'a simplement pas encore été cherché sérieusement.
   Quand la contre-explication s'appuie sur un claim de la littérature, peser son
   autorité (section dédiée plus haut) avant de la retenir ou de l'écarter.
   *(Vécu : une souche de collection repiquée en série déclarait sa date
   d'isolement original, pas celle du génome séquencé — son retrait a changé
   le SIGNE d'un estimateur de taux agrégé. Un blocage sur un nœud, un taux ou
   une date doit d'abord faire soupçonner sa métadonnée déclarée avant d'y
   lire un signal biologique.)*
3. **Redescendre à l'unité brute, pas à l'agrégat.** Prendre 3 à 5 des cas
   individuels les plus emblématiques du résultat et rouvrir la donnée SOURCE
   (lecture, pileup, ligne brute, pièce), jamais le chiffre déjà calculé. C'est
   ce contrôle précis, et lui seul, qui a cassé l'incident fondateur ci-dessus :
   la table agrégée disait « émergences indépendantes », les lectures brutes de
   ces mêmes souches disaient l'inverse.
4. **La prémisse plutôt que la conclusion.** Nommer l'hypothèse implicite et
   non testée sur laquelle tout le raisonnement s'appuie (une correspondance
   colonne/allèle, un « absence de X vaut Y », un sens de polarité). C'est
   presque toujours là que ça casse, jamais dans le calcul qui suit — recalculer
   plus soigneusement une prémisse fausse ne la rend pas vraie.
5. **Le regard du spécialiste, avant qu'il ne le porte.** Si un collègue qui
   connaît le domaine sur le bout des doigts voyait CE tableau précis en une
   minute, quelle serait sa première question ? Se la poser explicitement avant
   l'envoi ou l'écriture, pas après coup.
6. **Convergence suspecte.** Si un second projet ou texte s'appuie sur le même
   résultat pour se conforter mutuellement, vérifier qu'ils ne partagent pas la
   même erreur en amont avant de compter deux confirmations indépendantes —
   c'est exactement ce qui s'est produit entre les deux manuscrits de l'incident
   fondateur ci-dessus, chacun citant l'autre en soutien du même artefact.

### Verdict de ce mode

- **Consolidé** — la contre-explication la plus forte a été cherchée et n'a
  pas tenu ; le résultat peut être écrit comme acquis.
- **Fragile** — un point précis reste à vérifier avant d'écrire quoi que ce
  soit (le nommer) ; ne pas consolider tant qu'il n'est pas tranché.
- **Réfuté** — la contre-explication tient ; corriger l'énoncé et consigner la
  leçon dans la KB (`refuter-sa-propre-piste.md` ou la fiche du domaine), pas
  seulement corriger le chiffre.

Le coût de ce mode est de l'ordre de quelques minutes à une requête ; le coût
d'un résultat faux non challengé, une fois qu'un manuscrit est construit
dessus, se compte en jours voire en semaines de réécriture — et, au-delà du
temps, en crédibilité auprès des relecteurs qui l'auraient vu en un coup d'œil.

## Verdict (obligatoire, à l'écran)

Conclure par un verdict tranché parmi :
- **Lancer** — la proposition est neuve, cadrée, falsifiable, alignée, rentable.
- **Lancer après lit-review** — d'abord vérifier la littérature (contrôle 2).
- **Reformuler** — l'idée tient mais le cadrage (null, contrôle, périmètre) doit
  être revu ; proposer la reformulation.
- **Abandonner** — déjà fait, déjà publié, hors-sujet, ou coût > gain ; proposer
  `/pistes drop Px "<raison>"` pour en garder la trace.

## Esprit

Bref et incisif, pas un rapport. Trois à six lignes de verdict argumenté
suffisent. Le skill est aussi suggéré automatiquement par le hook `PreToolUse`
au moment d'écrire un script dans `analyses/` ; il reste invocable à la main par
l'utilisateur sur ses propres idées.
