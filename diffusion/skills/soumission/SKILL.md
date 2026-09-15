---
name: soumission
description: >-
  Gère tout le cycle de soumission d'un article scientifique, de la préparation
  au suivi, avec exécution externe seulement sur demande explicite : choisir la revue cible (base de
  revues avec scope, contraintes de longueur, frais réels, facteur d'impact et
  délai de première décision), contrôler que le manuscrit est prêt (dont la
  version française main_fr.tex), se connecter aux portails éditeurs par ORCID,
  déposer le préprint sur bioRxiv/medRxiv/arXiv et le code sur le GitHub
  centralisateur, remplir le formulaire de soumission, tenir le registre central
  des soumissions (qui, où, quand, statut), faire après chaque soumission le point
  d'état de tous les manuscrits (déposé, rejeté, en révision, préparé mais jamais
  soumis) et reprendre ce qui cloche, et en tirer les enseignements des rejets. Utiliser quand l'utilisateur veut « soumettre un article », « choisir
  une revue », « où soumettre ce papier », « préparer la soumission », « déposer
  le préprint », « où en sont mes soumissions », « le journal a répondu », « on
  m'a rejeté, où resoumettre », « fais le point sur mes soumissions », ou tape
  /soumission.
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Glob
  - Grep
  - WebSearch
  - WebFetch
  - AskUserQuestion
---

# /soumission : choisir une revue, soumettre, suivre, apprendre

Un article soumis coûte deux choses à l'auteur : le choix de la cible, qui demande
son jugement, et le travail de secrétariat, qui ne le demande pas. Ce skill prend
tout le second et prépare le premier.

Scripts (Python stdlib, zéro dépendance) :

| Script | Rôle |
|---|---|
| `scripts/preflight.py` | le manuscrit est-il en état d'être soumis aujourd'hui (recompile les deux versions) |
| `scripts/journals.py` | base de revues : filtrer, apparier, tenir à jour |
| `scripts/submissions.py` | registre central des soumissions, point d'état (`review`) et règle de variation |
| `scripts/author_profile.py` | dossier auteur réutilisable et mémoire des portails |

Données persistantes, hors du skill, dans `~/.agents/knowledge/journals/` :
`journals.tsv`, `submissions.tsv`, `author_profile.json`, `portals.tsv`,
`rejections.md`, `portal_lessons.md`.

## Périmètre d'autorisation

Une demande explicite dans le tour courant est nécessaire avant toute interaction
avec un portail éditeur, un serveur de préprint, un dépôt de code ou une boîte mail.
Quand cette demande existe, elle reste strictement bornée à l'acte nommé : soumettre
un article, mettre à jour une soumission ou vérifier son état. Toute autre action sur
un compte, une revue ou une boîte mail sort du périmètre, même si elle paraît utile
en chemin. La préparation locale, le pré-vol et la proposition de revues ne valent
jamais autorisation d'agir à l'extérieur.

Ce que ce skill ne fait jamais, quelle que soit l'insistance :

- saisir un mot de passe, un identifiant bancaire ou un token dans un champ, y
  compris un mot de passe que l'auteur vient de dicter (voir `references/acces.md`
  pour ce qui remplace la saisie, et qui marche mieux) ;
- choisir une option Open Access payante, accepter un transfert vers un titre à
  APC, engager une dépense ;
- cliquer le bouton final quand le portail affiche une déclaration légale que
  l'auteur seul peut engager ;
- publier un dépôt Zenodo, un préprint ou un dépôt GitHub sans confirmation
  explicite pour ce geste précis.

## Avant la première soumission d'une nouvelle session de travail

Vérifier en une commande que le dispositif est en état :

```bash
python3 scripts/author_profile.py portals
python3 scripts/journals.py lint
```

`portals` dit quelle voie d'accès a marché la dernière fois sur chaque portail, et
signale les domaines refusés par l'extension Chrome, qui sont le vrai verrou et non
les mots de passe. `lint` signale les fiches périmées et les clés de revue que le
registre cite sans que la base les connaisse.

Si plusieurs portails sont en `inconnu`, la configuration initiale n'a pas été faite :
suivre `references/setup-initial.md`, vingt minutes une fois pour toutes.

## Une seule fenêtre de navigateur, ouverte une fois, fermée à la fin

Toute la soumission tient dans UNE fenêtre : `tabs_context_mcp{createIfEmpty:true}` au
début, puis un `tabId` explicite passé à chaque `navigate` pour enchaîner les pages
dans le même onglet, puis `tabs_close_mcp` avant de rendre la main, y compris quand le
dépôt reste en attente d'un geste de l'auteur.

La raison est qu'un agent ne peut fermer que les onglets de SON groupe : ce qu'une
session n'a pas fermé avant de finir n'est plus fermable par personne. Une journée de
soumissions a ainsi laissé 47 onglets ouverts le 2026-08-25. Détail et exceptions dans
`references/portails.md`.

## Modes

L'intention de l'utilisateur détermine le point d'entrée. En cas d'ambiguïté,
partir de l'état réel : `submissions.py list --open` dit ce qui est en cours.

| Intention | Mode | Aller à |
|---|---|---|
| « où soumettre ce papier ? » | choisir | phases 0, 1, 2 |
| « le titre et le résumé cadrent-ils avec cette revue ? » | cadrer | phase 2bis |
| « soumets-le » | soumettre | phases 0 à 5, puis 6 obligatoirement |
| « où en sont mes soumissions ? », « fais le point » | suivre | phase 6 |
| « ils ont répondu / rejeté » | apprendre | phase 7 |
| « déposer le préprint » seul | dépôts | phase 4 |

---

## Phase 0 : mémoire, avant toute chose

1. Lire la mémoire du projet : `cahier_de_labo.md` (au moins les trois dernières
   entrées), `etat_des_decouvertes.md`, `pistes.md`, puis `AGENTS.md` ou, à défaut,
   `CLAUDE.md`.
2. Lire l'état des soumissions : `submissions.py review`, qui rend d'un coup le
   portefeuille et ses anomalies. Ce que le registre dit prime sur le souvenir de la
   conversation ; ce qu'il signale comme douteux se vérifie avant d'être cru.
3. Lire les enseignements accumulés : `~/.agents/knowledge/journals/rejections.md`
   et `portal_lessons.md`. Ne pas refaire une erreur qui y est écrite.

Rappel qui a déjà coûté deux sessions : **le statut éditorial d'un manuscrit ne se
lit pas dans le dépôt local.** Seuls le système de gestion de la revue et les mails
font foi. Un `article/` figé ne prouve pas une soumission.

## Phase 1 : pré-vol

```bash
python3 scripts/preflight.py <projet> [--journal CLE] [--target-words N] [--abstract-max N] [--no-compile]
```

Rend un verdict par point de contrôle. Les points bloquants sont des conditions
posées par l'auteur, pas des préférences :

- **la porte 3bis est franchie** : `verdict_diffusion.md` porte un verdict daté et
  favorable au mode visé (skill `/verdict-diffusion`). Ce skill-ci sait choisir une
  revue et remplir un portail ; il ne sait pas dire si le travail méritait d'être
  soumis, et le pipeline qualité ne le dit pas non plus — il prouve seulement que le
  manuscrit est bien fait. Un verdict `NE-PAS-DIFFUSER` ou `ROUVRIR` bloque le
  pré-vol ; un `DIFFUSER-SANS-COMITE` le bloque dès qu'une revue est visée avec
  `--journal`, et laisse passer la voie préprint.
- **la vitrine est cadrée pour LA revue visée** : `cadrage_editorial.md` porte un verdict
  `ALIGNE` daté pour cette clé de revue (skill `/cadrage-editorial`, phase 2bis). Le
  contrôle ne s'applique qu'avec `--journal`, puisqu'un cadrage n'existe que relativement
  à une cible ; un verdict rendu pour une autre revue, un `RETOUCHER` non intégré, un
  `CHANGER-DE-CIBLE` ou un `ROUVRIR` bloquent le pré-vol, et une vitrine modifiée depuis
  le cadrage (empreinte du titre et du résumé) le met en réserve.
- **`main_fr.tex` existe et n'est pas en retard sur l'anglais.** Le contrôle compare
  le nombre de sections et la longueur relative : une refonte du gabarit anglais qui
  n'a pas été répercutée en français est détectée ici, et nulle part ailleurs.
- **les deux versions COMPILENT réellement, et sans un seul renvoi non résolu.** Le
  pré-vol ne se contente plus de vérifier qu'un `main.pdf` existe et qu'il est
  postérieur à `main.tex` : il recompile `main.tex` et `main_fr.tex` dans une copie
  temporaire et bloque sur toute erreur LaTeX, toute citation et tout renvoi non
  résolus. Le critère est bien « des `??` dans le PDF que verrait le relecteur », pas
  « un `\ref` sans `\label` ». Cas vécu qui a motivé le contrôle : `animal_vs_human`
  avait un PDF à jour, mais 32 entrées de son `.bib` sans virgule avant le champ
  `verified` faisaient refuser la base ENTIÈRE par bibtex, et le PDF portait 79
  citations et 68 renvois non résolus sur une trentaine de pages.
  Le protocole est celui, éprouvé sur les 187 manuscrits du dépôt `mtbc`, de la piste
  P41.14.2 : compilation **dans une copie**, `article/` et son voisin
  `litterature_review/` recopiés, fichiers dérivés purgés, compilation **en place**.
  Compiler avec `-outdir` paraîtrait plus propre mais casse les
  `\bibliography{../litterature_review/references}` et produit des échecs fantômes
  quand un `.bbl` pré-construit est plus riche que le `.bib` ; et les renvois se
  comptent sur le `.log` de la **dernière passe**, jamais sur la sortie cumulée de
  latexmk, dont la première passe précède la construction du `.bbl`. Sans ces trois
  précautions, le contrôle crie au loup quatre fois sur cinq.
  `--no-compile` saute cette étape pour une itération rapide, au prix d'une réserve
  explicite : le pré-vol perd alors sa garantie principale.
- la déclaration d'assistance IA est présente ;
- les deux formules imposées de l'extérieur sont justes : le mésocentre est remercié
  si et seulement si un calcul est passé par lui, et la signature scientifique est
  celle qu'impose l'université (voir ci-dessous) ;
- les figures référencées existent.

Ces deux dernières ne relèvent pas du fond, et c'est pour cela qu'aucune relecture
scientifique ne les rattrape. Le mésocentre de calcul de Franche-Comté demande à être
cité par tout article dont un calcul est passé chez lui, dans les termes qu'il fixe :
« Computations have been performed on the supercomputer facilities of the Mésocentre de
calcul de Franche-Comté. » Le pré-vol cherche la trace d'un calcul distant dans le
cahier de laboratoire du projet et compare avec les remerciements du manuscrit, dans
les deux sens : un calcul non remercié est bloquant, un remerciement recopié d'un
article précédent sans calcul correspondant est une affirmation fausse comme une autre.

La signature scientifique, elle, est imposée depuis janvier 2025 et a été rappelée cinq
fois par la direction de l'institut, statistiques de non-conformité à l'appui :

> Université Marie et Louis Pasteur, (établissements-composantes employeurs ou
> hébergeurs des auteurs, dans leur ordre d'apparition), CNRS, institut FEMTO-ST,
> F-code postal Ville, France

en anglais `CNRS, FEMTO-ST institute` à la place des deux derniers segments. Le sigle
« UMLP » y est proscrit, le nom se donne en toutes lettres ; « Université de
Franche-Comté » et « Bourgogne-Franche-Comté » sont des noms d'avant 2025 qui font
perdre la publication dans les bases bibliométriques. Le générateur officiel tranche
les cas à plusieurs établissements-composantes :
`https://scienceouverte.umlp.fr/accueil/publications/signature-scientifique/`.
Détail et historique dans `~/.agents/knowledge/signature-et-remerciements.md`.

Ne pas passer outre un point bloquant. Le corriger, ou le faire corriger, avant la
phase 2.

Si le pipeline qualité n'a pas tourné sur cette version, l'enchaîner maintenant
plutôt qu'après un desk-reject : `/claim-check`, `/bib-check`, `/fig-check`,
`/supp-check`, `/deai-latex`, `/manuscript-review`. Ce pipeline prouve que le manuscrit
est bien fait ; il ne dit rien de son cadrage sur la cible, dont s'occupe la phase 2bis
une fois la revue arrêtée.

## Phase 2 : choisir la revue, et la faire choisir

Le choix appartient à l'auteur. Le travail de l'assistant est de lui présenter un
dossier sur lequel décider en une minute.

```bash
python3 scripts/journals.py match --domain micro-tb --words 5300 --tier solid --free
python3 scripts/submissions.py variety <cle_revue>
```

Détail des cinq critères, du calibrage de niveau et du format exact de la
proposition : lire `references/choix-revue.md`. En résumé :

1. **le format cadre** ou s'adapte à moindre effort (bascule vers les supplementary) ;
2. **le scope cadre**, vérifié sur des articles récents et pas seulement sur la
   page « aims and scope » ;
3. **les niveaux s'alignent** : ne pas gâcher un travail excellent dans une revue
   facile, ne pas exposer un travail honnête à un refus de principe ;
4. **le coût est nul** sauf décision contraire explicite de l'auteur ;
5. **la variation est respectée** : pas trois manuscrits chez le même éditeur au
   même moment, et pas de retour dans les douze mois vers une revue qui a rejeté.

Présenter **trois à quatre revues**, jamais une seule et jamais une liste. Pour
chacune : ce qui plaide pour, ce qui plaide contre, le délai de première décision
avec sa source, et une estimation honnête des chances. Terminer par une
recommandation assumée. Demander explicitement la décision à l'utilisateur.

Une valeur `unknown` dans la base n'est pas une donnée : c'est une vérification à
faire avant de proposer la revue. La vérifier sur le site de l'éditeur, puis
l'écrire avec `journals.py set`, pour ne plus jamais la rechercher.

**Lire une clause d'exclusion ne suffit pas : il faut trancher le champ.** Cas vécu
(desk-reject de Computers in Biology and Medicine, 2026-08-30) : la clause
d'exclusion du travail « in silico élémentaire » avait déjà été lue et recopiée dans
`notes` lors d'une session antérieure, mais `computational_only` était resté
`unknown` — le champ que `match --computational` lit réellement pour pénaliser une
revue. La revue a donc remonté dans le classement comme si la clause n'existait pas.
`journals.py lint` détecte maintenant cet écart (notes porteuses d'un signal
d'exclusion, champ resté `unknown`) ; **lancer `lint` et le laisser propre avant de
présenter les trois à quatre revues à l'auteur**, pas seulement avant de committer.

## Phase 2bis : cadrer la vitrine sur la revue retenue

Une fois la cible arrêtée par l'auteur, et **avant** tout reformatage, lancer
`/cadrage-editorial <cle>`. Cette passe relit le titre, le résumé, les mots-clés, la
clôture d'introduction, la première phrase de discussion, la conclusion et la lettre
d'accompagnement contre ce que la revue publie réellement, et rend un verdict daté
dans `cadrage_editorial.md`.

Ce que la phase 2 a fait, c'est écarter les cibles impossibles. Ce que cette passe fait,
c'est éviter qu'un travail adéquat soit renvoyé par un éditeur qui, en trois minutes de
lecture de la vitrine, ne voit pas ce que ce papier fait chez lui. Les deux gestes sont
distincts et aucun ne remplace l'autre : le corpus des douze derniers mois récolté au
critère 2 sert ici une seconde fois, à calibrer la forme au lieu de trancher l'admission.

Deux conséquences opérationnelles :

- **Le verdict peut renvoyer en phase 2** (`CHANGER-DE-CIBLE`) quand l'écart ne se comble
  pas sans mentir. Ce n'est pas un échec de la passe, c'est sa raison d'être : reformuler
  pour masquer une inadéquation de fond se paie au premier relecteur.
- **`preflight.py` bloque** dès que `--journal` est passé et qu'aucune entrée `ALIGNE` ne
  couvre cette clé de revue, ou que le cadrage a été rendu pour une autre revue. Un
  cadrage ne se transpose pas d'une cible à l'autre.

## Phase 3 : adapter le manuscrit à la cible retenue

Reformater vers le gabarit de la revue, ajuster la longueur, écrire la lettre
d'accompagnement depuis le message de l'article, préparer les suggestions de
relecteurs (`author_profile.py reviewers --n 5`), relire les déclarations exigées.

Relancer `preflight.py <projet> --journal <cle>` : passer la clé suffit, les limites
de corps et de résumé sont lues dans la base et deviennent les seuils du contrôle.
Les surcharger avec `--target-words` et `--abstract-max` seulement quand la revue
impose une limite propre au type d'article visé que la fiche ne porte pas.

Puis figer : commit dans `article/`, pour que la version déposée soit retrouvable.

## Phase 4 : les deux dépôts parallèles, obligatoires

Toute soumission à une revue s'accompagne de deux dépôts. Procédures, choix du
serveur, licences et pièges : `references/depots-paralleles.md`.

1. **Préprint** sur bioRxiv (biologie, génomique), medRxiv (santé humaine,
   clinique) ou arXiv (méthodologie, calcul, IA). Vérifier d'abord que la revue
   cible accepte le préprint (champ `preprint_policy`).
2. **Code et données** sur le dépôt GitHub centralisateur correspondant au
   domaine : `cguyeux/deciphering-tuberculosis-with-ai` pour la tuberculose,
   `cguyeux/ia-securite-civile` pour les travaux sécurité civile et IA.

Ordre impératif, appris à ses dépens : **pousser le PDF seulement après la
confirmation de dépôt effective**, jamais à l'étape de préparation. Un PDF poussé
en avance devient silencieusement périmé dès le premier ajustement imposé par le
portail.

Deux corollaires, appris du refus Rv1125 (2026-09-04) :

- **Un dépôt de préprint n'est pas acquis.** bioRxiv refuse au criblage une partie
  des manuscrits entièrement in silico sur données publiques, avec une clause de
  périmètre absente de sa FAQ (trois refus sur cinq dépôts du même profil, mais deux
  acceptations : le criblage n'est pas déterministe). Ne jamais présenter la mise en
  ligne comme acquise, annoncer le serveur de repli dès le plan de diffusion, et
  rappeler que la lettre de refus dit explicitement ne porter aucun jugement sur le
  fond. Détail et citation exacte : `references/depots-paralleles.md`.
- **Si le préprint est refusé, le dépôt de code se dégage du chaînage** et redevient
  un geste autonome à proposer à l'auteur. L'ordre ci-dessus interdit de pousser
  trop tôt, il n'autorise pas à laisser un dépôt en suspens derrière un événement
  qui n'aura pas lieu.

## Phase 5 : la soumission elle-même

0. **Si un brouillon existe déjà sur le portail, lire ce qu'il contient avant d'y
   toucher.** Ni son URL ni le nom de la revue ne disent quel manuscrit il porte ;
   seul le nom du fichier déjà téléversé le dit. Plusieurs sessions peuvent préparer
   des dossiers en parallèle sur le même compte éditeur, et un téléversement de plus
   sur le mauvais brouillon mélange deux articles dans une même soumission.
   Confronter au registre : un brouillon inconnu de `submissions.py list` est un
   brouillon dont on ne sait rien.
1. **Se connecter.** Ordre de préférence strict, détaillé dans `references/acces.md` :
   session vivante, puis « Sign in with ORCID », puis autofill de Chrome, puis, en
   dernier recours et sur autorisation, la réinitialisation par mail dont
   l'assistant fait tout sauf la saisie finale.
2. **Remplir.** Le dossier auteur évite de tout retaper :
   `author_profile.py show` sort affiliation, ORCID, déclarations et mots-clés
   prêts à coller. Pièges par portail : `references/portails.md`.
3. **Rendre la main** pour le clic final quand le portail engage l'auteur, et pour
   toute case qui atteste d'une lecture ou accepte des conditions. Les déclarations
   factuelles, en revanche, se remplissent : elles ne font que recopier ce que le
   manuscrit affirme déjà, et il faut alors les reprendre mot pour mot depuis lui,
   car beaucoup de portails annoncent que leur version remplace celle du texte.
4. **Enregistrer immédiatement**, avec l'identifiant rendu par le portail :

```bash
python3 scripts/submissions.py add --project Rv1025 --title "..." \
  --journal-key archives-of-microbiology --manuscript-id "..." \
  --preprint-server biorxiv --preprint-id "BIORXIV/2026/746906" \
  --github-repo cguyeux/deciphering-tuberculosis-with-ai --fr-version article/main_fr.tex
```

5. **Consigner ce qui a coincé.** Tout champ qui a résisté, tout bouton qui n'a pas
   répondu, toute exigence non documentée devient une ligne dans
   `portal_lessons.md` et un `author_profile.py portal-set <portail> quirks="..."`.
   C'est ce qui rend la soumission suivante plus rapide que celle-ci.
6. **Enchaîner sur le point d'état de la phase 6, sans attendre qu'on le demande.**
   Une soumission n'est pas finie quand le portail affiche son numéro, mais quand le
   portefeuille entier est à jour.

## Phase 6 : le point d'état, obligatoire après chaque soumission

Une soumission qui vient d'aboutir est le seul moment où l'on a le portefeuille sous
les yeux. C'est donc là qu'il faut le regarder en entier, et pas seulement la ligne
qu'on vient d'écrire. L'écart le plus coûteux n'est pas un rejet, qui se voit : c'est
un manuscrit que l'auteur croit soumis et qui dort en `preparing` parce qu'une session
précédente a préparé le paquet sans jamais cliquer, ou une décision arrivée par mail
que personne n'a reportée. Le registre ne ment pas, mais il ne sait que ce qu'on lui
a dit, et il vieillit tout seul.

```bash
python3 scripts/submissions.py review
```

La commande sort trois choses : l'état de chaque manuscrit groupé par statut, la liste
des anomalies déductibles du seul registre, et celles qui exigent d'aller voir dehors.
Elle détecte le paquet préparé jamais déposé, le statut hors vocabulaire qui fait
échapper une ligne aux compteurs, la soumission active sans identifiant de manuscrit,
la révision dont l'horloge tourne depuis plus d'un mois, l'accepté jamais passé à
`published`, le statut figé au-delà du seuil, le projet dont la dernière ligne est un
rejet sans cible suivante, et la concentration chez une même revue ou un même éditeur.

**Le point d'état ne se contente pas de lister.** Chaque anomalie appelle un geste, et
c'est là que se fait le travail :

- **préparé jamais déposé** : reprendre le dépôt à la phase 5 s'il est encore
  pertinent, sinon acter l'abandon de la cible (`set <id> status=abandoned`) pour que
  la ligne cesse de bloquer l'éditeur au titre de la règle de variation ;
- **rejeté sans suite** : c'est une phase 2 à rouvrir, pas une ligne à ranger.
  `variety <cle>` avant de proposer la revue suivante, en tenant compte du cooldown ;
- **révision qui traîne** : retrouver la date limite de renvoi, puis ouvrir le travail
  de révision ou demander un délai, ce dernier point revenant à l'auteur ;
- **statut figé, actif sans identifiant** : ce sont des questions auxquelles le registre
  ne peut pas répondre. Elles se vérifient dans le système de gestion ou dans les mails
  de l'éditeur, jamais dans le dépôt local ;
- **accepté** : voir ci-dessous, c'est la seule fenêtre où certaines choses se corrigent
  encore.

**Ce qu'une acceptation déclenche.** Une signature scientifique corrigée dans le dépôt
local ne change rien à ce que l'éditeur détient : la fiche auteur de son portail, elle,
commande l'indexation, et la direction de l'institut demande explicitement de la mettre à
jour, pas seulement de corriger le manuscrit suivant. Le bon moment n'est pas la
soumission, où toucher aux bases auteurs d'un manuscrit en cours d'évaluation n'apporte
rien (arbitrage de l'auteur, 2026-09-09), mais l'acceptation : les épreuves passent sous
ses yeux et le dossier se solde. Trois gestes, dans cet ordre. Sur les **épreuves**,
vérifier la signature scientifique et les remerciements, mésocentre et financeurs
compris : c'est la dernière fenêtre où ils se corrigent. Dans la **base auteurs du
portail**, mettre l'affiliation à jour. À la **parution**, passer le statut à `published`
et déclarer la publication (ticket Publiweb). Le point d'état sort ce rappel dès qu'une
ligne entre en `accepted`, sans attendre un délai.

Ces vérifications externes sont bornées par le périmètre d'autorisation : sans demande
explicite dans le tour courant, elles se **proposent** et ne s'exécutent pas. La liste
« vérification externe due » est faite pour être présentée telle quelle à l'auteur, qui
autorise ou non le contrôle en une phrase.

Le registre corrigé, mettre à jour ce qui a bougé :

```bash
python3 scripts/submissions.py set <id> status=under-review
python3 scripts/submissions.py stale --days 60
python3 scripts/submissions.py audit
```

`audit` confronte le registre aux cahiers de laboratoire des projets et rattrape ce qui
a été raconté quelque part sans jamais être enregistré ici.

Un silence de plus de trois mois sans changement d'état justifie de relancer l'éditeur.
Proposer le texte de relance ; l'envoi reste un acte de l'auteur.

**Restituer en prose, pas en tableau.** L'auteur veut savoir ce qui a changé et ce qui
cloche, manuscrit par manuscrit, en quelques lignes : ce qui est parti aujourd'hui, ce
qui attend une décision et depuis combien de temps, ce qui est bloqué et par quoi, ce
qu'il doit décider lui-même. Le tableau complet reste dans le registre pour qui veut
l'ouvrir.

## Phase 7 : apprendre d'une décision

```bash
python3 scripts/submissions.py reject <id> --kind reject-desk \
  --lesson "ce que cette décision apprend pour la prochaine fois" \
  --next-target "<cle_revue>"
```

La commande met le registre à jour, place la revue en cooldown d'un an et écrit
l'enseignement dans `rejections.md`. N'écrire une leçon que si elle est réutilisable :
un rejet qui n'apprend rien reste dans le registre et s'arrête là.

Sur un desk-reject, distinguer deux motifs qui n'appellent pas la même correction. Un
rejet **de fond** (la revue n'admet pas ce type de travail) est une erreur de choix de
cible, à corriger dans `references/choix-revue.md` et dans la fiche de la revue. Un rejet
**de cadrage** (l'éditeur n'a pas vu ce que le papier faisait chez lui) est une erreur de
vitrine : relire l'entrée correspondante de `cadrage_editorial.md`, comparer ce que la
simulation avait prédit à ce que l'éditeur a écrit, et verser l'écart dans le registre
avant de recadrer pour la cible suivante. Une simulation qui avait laissé passer ce que le
vrai desk a refusé est l'enseignement le plus utile qu'un rejet puisse donner.

Trois desk-rejects en une semaine chez le même éditeur ne sont pas trois accidents,
c'est un signal sur le calibrage. Quand le motif se répète, ce n'est pas la revue
suivante qu'il faut chercher, c'est le critère de choix qu'il faut corriger, et la
correction s'écrit dans `references/choix-revue.md`.

Puis mettre à jour la fiche de la revue si la décision a révélé un fait durable
(scope réel plus étroit que la page l'annonce, politique de transfert payant,
délai réel très différent de l'affiché).

---

## Consignes

- **Un `unknown` n'est jamais une donnée.** Ni un facteur d'impact, ni un APC, ni un
  délai ne se citent de mémoire. Vérifier sur le site de l'éditeur, écrire dans la
  base, dater.
- **Ce que le portail impose et ce que le guide aux auteurs impose sont deux jeux de
  contraintes distincts**, pas redondants. Lire les deux.
- **Mesurer la longueur par section**, jamais le document entier : les limites d'une
  revue portent sur le résumé, sur le corps, parfois sur le nombre de figures.
- **Après deux ou trois échecs sur la même action de navigateur**, s'arrêter et
  demander, plutôt que de boucler.
- **Bilan narratif obligatoire** en fin de session : ce qui a été fait, où en est la
  soumission, ce qui reste, la prochaine étape. L'auteur ne doit pas avoir à ouvrir
  le registre pour savoir ce qui vient de se passer.
- Terminer par la liste des pistes ouvertes du projet et une rubrique
  `## Enchaînement proposé`.

## Épilogue

Après une session significative, `/cahier-de-labo update` dans le projet concerné,
et `/reflect` si un portail a livré une leçon qui vaut au-delà de cet article.
