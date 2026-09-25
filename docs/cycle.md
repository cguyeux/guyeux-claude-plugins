# Plugin `cycle`

> Research-project lifecycle toolkit: five-phase cycle with closure gates, decision gates on whether findings are worth writing up and disseminating, research-leads registry, lab notebook, consolidated state of knowledge, pre-flight and post-result adversarial checks, reframing and scope triage, model/effort routing under usage quotas, dataset versioning and drift detection, project scaffolding. Domain-agnostic: usable for phylogenomics, other sciences, or any long-running research project. Guyeux group (FEMTO-ST), academic research workflow.

Skills propres (canoniques) : **13** ; skills partagés utilisés (symlinks) : **0**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [bdd](#bdd) ; [cahier-de-labo](#cahier-de-labo) ; [challenge](#challenge) ; [cycle-projet](#cycle-projet) ; [etat](#etat) ; [init-project](#init-project) ; [narratif](#narratif) ; [pistes](#pistes) ; [reboot](#reboot) ; [recadrage](#recadrage) ; [routage](#routage) ; [suite](#suite) ; [verdict-diffusion](#verdict-diffusion)

### bdd

Versionnage et journalisation de bases de donnees internes declarees dans un registre `bdd/registre.json` (par exemple un corpus principal, un corpus de barcodes, un atlas de genes/lignees, un second genre ou domaine suivi separement...). Sous-commandes `init/stamp/check/bump/log/diff/miroir/abonnes` via `bdd.py` ; bibliotheque d'ecriture `bdd_journal.py` pour les scripts qui modifient un store ; registre d'abonnes pour verifier a la demande que les projets consommateurs d'un store n'ont pas derive. Declencheurs, "quelle version de la base actuelle", "cite la source de ces donnees", "cette base a-t-elle derive", "journalise ce script d'ecriture", "qui consomme cette base, a-t-il derive", "bdd init/stamp/check/bump/abonnes", `/bdd`.

### cahier-de-labo

Read or append timestamped entries to a research project's lab notebook (`cahier_de_labo.md`). Use on `/cahier-de-labo`, `/cahier-de-labo update`, `/cahier-de-labo read`, or "ajouter une entrée au cahier", "mettre à jour le cahier de labo", "consulter le cahier", "what's in the lab notebook". Found by walking up from the current directory.

### challenge

Adversarial check on a proposal before launching work OR on a result already obtained, applied alike to the user's ideas and the assistant's own. Use on `/challenge <proposition>`, or "challenge cette idée", "prends du recul", "joue l'avocat du diable", "est-ce que ça vaut le coup", "vérifie avant de te lancer", before any non-trivial analysis or computation, and, mode RÉSULTAT, on "ce résultat est surprenant", "ça contredit ce qu'on pensait", "vérifie avant que j'y croie", before writing a counter-intuitive or literature/KB-contradicting finding into `etat_des_decouvertes.md`, before closing a piste on a surprising positive result, or before a manuscript section built on such a result.

### cycle-projet

Cycle de vie canonique d'un projet de recherche, de l'analyse primaire à l'archivage, cinq phases strictement ordonnées, chacune fermée par une PORTE (point fixe) qu'il faut prouver avant de passer à la suivante, dont deux portes de DÉCISION qui demandent si le travail mérite d'être écrit (1bis) puis diffusé (3bis). Use on `/cycle-projet`, `/cycle-projet gate`, `/cycle-projet next`, or "où en est ce projet", "est-ce qu'on peut commencer à rédiger", "le projet est-il fini", "quelle est la prochaine phase", "peut-on soumettre", "peut-on archiver le projet", "phase d'analyse terminée ?".

### etat

Read or rewrite a project's consolidated state of knowledge (`etat_des_decouvertes.md`), proven, refuted, uncertain, position vs literature. Use on `/etat`, `/etat read`, `/etat update`, or "faire le point", "où on en est", "réécrire l'état des découvertes", "consolider ce qu'on sait", "state of knowledge". Project root = first parent with `cahier_de_labo.md`.

### init-project

Scaffold a new academic research project, short CLAUDE.md (context, structure, pointers ; rules inherited from codes/CLAUDE.md), the five memory artefacts, standard dirs, and `article/` as its own Git repo on the article voie. Flags `--voie article|réponse|réoutillage|coordination`, `--famille`. Use on `/init-project <name>`, "initialise un projet", "scaffolde un projet", "create a new research project".

### narratif

Conception de l'article entre le message et le squelette. Ordonne l'acquis en vue de la démonstration, fixe la chaîne d'arguments et ses points de bascule, puis décide du temps et du lieu de chaque fait, développé dans le corps, porté par une figure, réduit à une phrase avec renvoi, versé au supplémentaire, ou reconnu comme sérendipité. Émet ensuite le squelette LaTeX depuis le plan, chaque section portant son allocation. Use on `/narratif`, `/narratif read`, `/narratif tri`, `/narratif drift`, `/narratif reprise`, or « comment structurer cet article », « quel est le fil de la démonstration », « dans quel ordre sortir les arguments », « qu'est-ce qui va en supplementary », « l'article est trop verbeux », « on perd le lecteur », « par quoi commencer », avant d'écrire le squelette d'un manuscrit.

### pistes

Research-leads tree (`pistes.md`) of a project, directions and sub-leads with states à faire / en cours / réalisé / abandonné. Read or mutate via `/pistes`, `/pistes add "…"`, `/pistes start P1.2`, `/pistes done P1.2`, `/pistes drop P3 "raison"`, or "ajouter une piste", "quelles pistes restent", "cocher cette piste", "abandonner cette piste". Project root = first parent with `cahier_de_labo.md`.

### reboot

Reprise d'un projet de recherche interrompu, quand l'environnement (cycle, cinq artefacts, skills, hooks, données) a changé depuis la dernière séance et qu'on ne sait plus ce qui, dans l'acquis du projet, tient encore. Rend un verdict mesuré HARD / SOFT / AUCUN, puis conduit soit une simple migration d'environnement, soit une refondation complète où tout l'acquis legacy transite par `affirmations.md` et n'est réinscrit à l'état qu'une fois re-prouvé

Compétences :  « je reprends ce projet », « ça date de plusieurs mois », « où en étais-je », « est-ce que ces chiffres tiennent encore », « le projet est périmé », « il faut repartir de zéro », « l'environnement a changé depuis », « diagnostic de reprise », un bandeau SQUELETTE NON RENSEIGNÉ, un état dont les données citées ont dérivé, `/reboot`

### recadrage

Triage de périmètre et re-cadrage d'un projet de recherche, chaque acquis reçoit une destination (article en cours / second papier / projet voisin qui posait déjà la question / registre parent / réponse à une question ouverte d'ailleurs / classé), le cadrage lui-même est remis en question, et la restructuration à deux projets (transférer, fusionner, redécouper, scinder) est proposée quand le projet déborde. Use on `/recadrage`, `/recadrage triage`, `/recadrage scinder`, or "faut-il repenser le projet", "est-ce que ça rentre encore dans l'article", "cette découverte est hors sujet", "on a trouvé autre chose", "scinder le projet", "ouvrir un nouveau projet", "sérendipité", "ne pas perdre cette découverte", "qui d'autre cherchait ça".

### routage

Choisit le modèle Claude et le niveau d'effort d'une tâche ou d'une piste, à qualité strictement égale et pour la moindre consommation du forfait (limites 5 h / 7 j), puis mesure ce que la tâche a réellement coûté et affine la grille. Étiquette les pistes ouvertes d'un projet en `[Modèle:effort]`, rend la recette de lancement (`/clear`, modèle, effort), mesure la consommation d'une session ou d'un mois de sessions depuis les transcripts, compare prévu et observé, calibre les poids, et tient à jour le roster des modèles quand Anthropic en publie un nouveau

Compétences :  « quel modèle pour cette tâche », « quel effort », « est-ce que Sonnet suffit », « ça va coûter combien », « combien j'ai consommé », « où en est mon forfait », « pourquoi ma semaine part si vite », « étiqueter les pistes », « il y a un nouveau modèle Claude », `/routage`

### suite

Consigne la piste suivante à traiter (avec son étiquette [Modèle:effort]) juste avant un /clear délibéré, et fait réapparaître ce rappel automatiquement juste après le /clear, sans ressaisie. Use on `/suite`, or "note la piste suivante avant de clear", "prépare le clear", "rappelle-moi où reprendre après le clear".

### verdict-diffusion

Les deux portes de décision du cycle, qui demandent si un travail MÉRITE d'être écrit puis diffusé. Porte 1bis (`amont`, AVANT toute rédaction), faut-il rédiger, recadrer, élargir la question, ou classer un sujet creux ou déjà publié ? Porte 3bis (défaut, manuscrit stabilisé), soumettre, préprint seul, ne pas diffuser, ou rouvrir ? Rend UN verdict argumenté, jamais un menu. Use on `/verdict-diffusion`, `/verdict-diffusion amont`, `/verdict-diffusion read`, or "est-ce que ça vaut la peine d'écrire cet article", "faut-il se lancer dans la rédaction", "le sujet est-il assez solide", "est-ce que ça mérite d'être soumis", "est-ce publiable", "faut-il soumettre ou juste un préprint", "ce travail vaut-il un article", "on soumet ou pas".
