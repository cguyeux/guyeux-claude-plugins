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
  des soumissions (qui, où, quand, statut) et en tirer les enseignements des
  rejets. Utiliser quand l'utilisateur veut « soumettre un article », « choisir
  une revue », « où soumettre ce papier », « préparer la soumission », « déposer
  le préprint », « où en sont mes soumissions », « le journal a répondu », « on
  m'a rejeté, où resoumettre », ou tape /soumission.
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
| `scripts/preflight.py` | le manuscrit est-il en état d'être soumis aujourd'hui |
| `scripts/journals.py` | base de revues : filtrer, apparier, tenir à jour |
| `scripts/submissions.py` | registre central des soumissions et règle de variation |
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
| « soumets-le » | soumettre | phases 0 à 5 |
| « où en sont mes soumissions ? » | suivre | phase 6 |
| « ils ont répondu / rejeté » | apprendre | phase 7 |
| « déposer le préprint » seul | dépôts | phase 4 |

---

## Phase 0 : mémoire, avant toute chose

1. Lire la mémoire du projet : `cahier_de_labo.md` (au moins les trois dernières
   entrées), `etat_des_decouvertes.md`, `pistes.md`, puis `AGENTS.md` ou, à défaut,
   `CLAUDE.md`.
2. Lire l'état des soumissions : `submissions.py list` puis `submissions.py stale`.
   Ce que le registre dit prime sur le souvenir de la conversation.
3. Lire les enseignements accumulés : `~/.agents/knowledge/journals/rejections.md`
   et `portal_lessons.md`. Ne pas refaire une erreur qui y est écrite.

Rappel qui a déjà coûté deux sessions : **le statut éditorial d'un manuscrit ne se
lit pas dans le dépôt local.** Seuls le système de gestion de la revue et les mails
font foi. Un `article/` figé ne prouve pas une soumission.

## Phase 1 : pré-vol

```bash
python3 scripts/preflight.py <projet> [--journal CLE] [--target-words N] [--abstract-max N]
```

Rend un verdict par point de contrôle. Les points bloquants sont des conditions
posées par l'auteur, pas des préférences :

- **`main_fr.tex` existe et n'est pas en retard sur l'anglais.** Le contrôle compare
  le nombre de sections et la longueur relative : une refonte du gabarit anglais qui
  n'a pas été répercutée en français est détectée ici, et nulle part ailleurs.
- le manuscrit compile et `main.pdf` est postérieur à `main.tex` ;
- la déclaration d'assistance IA est présente ;
- les figures référencées existent.

Ne pas passer outre un point bloquant. Le corriger, ou le faire corriger, avant la
phase 2.

Si le pipeline qualité n'a pas tourné sur cette version, l'enchaîner maintenant
plutôt qu'après un desk-reject : `/claim-check`, `/bib-check`, `/fig-check`,
`/supp-check`, `/deai-latex`, `/manuscript-review`.

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

## Phase 6 : suivre

```bash
python3 scripts/submissions.py list --open
python3 scripts/submissions.py stale --days 60
```

Pour chaque soumission signalée, vérifier l'état **dans le système de gestion**
(portail, ou mails du système dans Gmail), jamais dans le dépôt local, puis
`submissions.py set <id> status=under-review`.

Un silence de plus de trois mois sans changement d'état justifie de relancer
l'éditeur. Proposer le texte de relance ; l'envoi reste un acte de l'auteur.

## Phase 7 : apprendre d'une décision

```bash
python3 scripts/submissions.py reject <id> --kind reject-desk \
  --lesson "ce que cette décision apprend pour la prochaine fois" \
  --next-target "<cle_revue>"
```

La commande met le registre à jour, place la revue en cooldown d'un an et écrit
l'enseignement dans `rejections.md`. N'écrire une leçon que si elle est réutilisable :
un rejet qui n'apprend rien reste dans le registre et s'arrête là.

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
