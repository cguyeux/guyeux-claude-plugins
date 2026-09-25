---
name: routage
description: Choisit le modèle Claude et le niveau d'effort d'une tâche ou d'une piste, à qualité strictement égale et pour la moindre consommation du forfait (limites 5 h / 7 j), puis mesure ce que la tâche a réellement coûté et affine la grille. Étiquette les pistes ouvertes d'un projet en `[Modèle:effort]`, rend la recette de lancement (`/clear`, modèle, effort), mesure la consommation d'une session ou d'un mois de sessions depuis les transcripts, compare prévu et observé, calibre les poids, et tient à jour le roster des modèles quand Anthropic en publie un nouveau. Déclencheurs — « quel modèle pour cette tâche », « quel effort », « est-ce que Sonnet suffit », « ça va coûter combien », « combien j'ai consommé », « où en est mon forfait », « pourquoi ma semaine part si vite », « étiqueter les pistes », « il y a un nouveau modèle Claude », `/routage`.
argument-hint: "[etat|estimer \"<tâche>\"|etiqueter <projet>|mesurer|calibrer|maj]"
---

# Routage modèle / effort et sobriété du forfait

La connaissance vit dans **`~/.agents/knowledge/model-routing.md`** (grille, roster, poids,
journal). Ce skill est la procédure ; le script est
`${CLAUDE_PLUGIN_ROOT}/skills/routage/scripts/routage.py` (stdlib seule, aucun appel LLM, aucun token).

**Le principe, qui prime sur tout le reste : la moindre configuration qui donne EXACTEMENT
la qualité qu'aurait donnée un modèle plus fort.** Jamais une qualité dégradée pour
économiser. En cas d'hésitation entre deux configurations, prendre la plus forte : une
tâche ratée coûte la tentative, la reprise, et un aller-retour avec l'utilisateur, donc
plus cher que la tâche faite correctement du premier coup.

## Ce qui consomme, en une ligne

`coût ≈ requêtes × contexte × poids lecture-cache`. Chaque appel d'outil est une requête
qui renvoie tout le contexte. Ce qui compte n'est donc pas le contexte moyen mais l'INTÉGRALE
des tokens lus : tout ajout est relu par toutes les requêtes suivantes. Mesuré le 2026-09-13
sur 23 000 requêtes Opus (§1ter de la fiche) : préfixe du tour 1 **28 %** (dont le listing des
skills 43 %), résultats d'outils 25 %, **entrées d'outils 22 %** (les heredocs Bash font 85 % des
caractères d'entrée), réflexion **11 %** — et la réflexion n'est PAS retirée du contexte. Donc
36 % de ce qui est relu est ce que l'assistant a lui-même écrit : la sortie n'est marginale qu'à
la génération. Leviers, dans l'ordre du gain mesuré : couper la session (`/clear` à 250 k, −38 %),
alléger le préfixe (désactiver les plugins de skills inutiles au projet, −20 % du préfixe), ne pas
retaper un script pour le corriger, sous-agents pour les grosses sorties, puis le choix du modèle.

## Modes

- `scripts/feu.py [session_id]` — feu de forfait seul : consommé rapporté à l'avancement de chaque
  fenêtre, projection de fin de fenêtre, gradient vert → rouge, facteur de marge et conseil de
  conduite (partagé avec la statusline et le rappel `[SOBRIÉTÉ]`).
  **PLUSIEURS COMPTES MAX (exemple), donc horizon divisé d'autant.** Si vous alternez
  entre plusieurs comptes Max aux fenêtres indépendantes (exemple vécu : deux comptes),
  `rate_limits` ne voit que celui de la session en cours. `feu.py::COMPTES_MAX` (variable
  d'environnement `CLAUDE_COMPTES_MAX`, défaut 2) divise la projection par ce nombre : avec
  deux comptes, la fenêtre 7 j doit couvrir **3,5 jours** de travail sur un compte donné, la
  5 h en couvrir **2 h 30**, et couleurs, facteur de marge, conduite d'escalade et
  recommandations de pistes s'entendent tous sur cet horizon. Ne jamais refaire la division
  à la main par-dessus : elle est déjà faite. Compte unique = `CLAUDE_COMPTES_MAX=1`. Quand
  `projection_compte ≥ 100`, le conseil ajoute « BASCULE DE COMPTE » : ce compte-ci sera
  épuisé, la conduite est de changer de compte, pas de ralentir. `CUTOFF_HEURE` (variable
  `CLAUDE_CUTOFF_HEURE`, défaut 19 h) retire de même les heures du soir où vous ne codez
  généralement pas ; mettre 24 pour désactiver ce retrait. Détail et mesures, si vous tenez
  une base de connaissances méthodologique : à documenter au même endroit.
- `routage.py etat [--projet <chemin>]` — modèle et effort de la session, feu de forfait, quotas 5 h / 7 j du
  dernier échantillon, rappel de la grille, alerte si le modèle est inconnu du roster, et
  comparaison avec les étiquettes des pistes `en cours` du projet. À lancer quand on ne sait
  pas où on en est.
- `routage.py estimer "<libellé de tâche>" [--projet P --verifiable|--non-verifiable]` —
  archétype, étiquette, bande de coût, recette de lancement. C'est ce mode qui répond à
  « quel modèle pour ça ».
- `routage.py etiqueter <projet> [--apply]` — écrit `<projet>/pistes_etiquettes_proposees.md`
  pour les feuilles ouvertes non étiquetées. **Relire et corriger le fichier**, puis `--apply`
  (il applique ce fichier, ligne à ligne, avec sauvegarde `.bak_etiquettes_*`). Jamais
  d'étiquetage en masse sans cette relecture : la grille se trompe sur les libellés elliptiques.
- `routage.py mesurer [--session ID] [--jours N]` — consommation réelle de la session
  (tokens par type et par modèle, sous-agents compris, part des lectures de cache).
  `routage.py mesurer --retro --jours 30` — classement des sessions les plus coûteuses du mois.
- `scripts/contexte.py prefixe|integrale|clear [--jours N] [--famille opus|…]` — d'où vient le
  contexte relu et ce que coûterait de le couper. `prefixe` décompose le tour 1 (listing des skills
  par plugin, CLAUDE.md, harnais) ; `integrale` donne la part de chaque origine dans les tokens lus,
  par outil, et la place des heredocs Bash ; `clear` rejoue les sessions en coupant au-delà d'un
  seuil et chiffre l'économie. À lancer quand on se demande POURQUOI la semaine part vite, avant de
  toucher au routage : le contexte pèse trois fois le choix de modèle.
  `contexte.py alleger <répertoires…> [--plugins bio|redac|<plugin@marketplace>] [--apply]
  [--retablir]` pose le `.claude/settings.local.json` qui retire du listing les plugins de skills
  inutiles à ce projet (dry-run par défaut, fusion sans écrasement, sauvegarde). À faire à
  l'ouverture d'un projet qui ne relève pas d'un domaine outillé, ou quand un plugin devient inutile
  (`redac` après la clôture d'un manuscrit). Le réglage n'est pas hérité par les sous-répertoires.
- `routage.py audit [--session ID] [--piste Px] [--json]` — compare, pour les tâches déjà
  fermées par `tache done` sur la session, la bande PRÉVUE (`cout_prevu`) à la bande RÉELLEMENT
  OBSERVÉE, et ne signale QUE les dépassements (S→M, M→L…). Silencieux et sans coût si tout
  s'est déroulé dans la bande annoncée. C'est le geste qui bouclait la demande de CG du
  2026-09-13 : « audit systématique quand la consommation dépasse l'attendu, avec diagnostic et
  correctifs d'environnement » — sans ajouter de mesure à chaque tour de chaque session, en
  s'appuyant sur ce que `tache start/done` enregistre déjà.
- `routage.py journal "<passe>" "<constat>" "<effet>"` — ajoute une ligne au tableau §7 de
  `model-routing.md` (mêmes colonnes que le journal de calibration existant). À utiliser après un
  audit qui a révélé une cause précise, même si le correctif d'environnement n'est pas encore
  appliqué : le prochain audit doit voir que ce cas a déjà été vu, pour ne pas re-diagnostiquer
  indéfiniment le même défaut.
- `routage.py tache start|done --piste Px …` — appelé par `/pistes start` et `/pistes done` ;
  enregistre la prédiction puis l'observation dans `~/.agents/coord/quota/taches.jsonl`.
- `routage.py calibrer [--jours 7] [--apply]` — ajuste les poids par famille de modèle
  (régression du Δ 7 j sur les tokens réels) et sort les statistiques par étiquette. Sans
  `--apply`, rien n'est écrit.
- `routage.py maj [--apply]` — veille : récupère la doc Anthropic en Markdown, diffe le roster
  (nouveau modèle, prix, effort par défaut, contexte), signale les clés périmées de
  `settings.json`. **Un nouveau modèle apparu impose de relire la grille §2 et de qualifier sa
  facturation** (forfait ou crédits d'usage) : le script ne le devine pas.

## Quand l'invoquer

1. **Avant de proposer un enchaînement** : la rubrique « Enchaînement proposé » doit porter
   la ligne de lancement (`/clear`, modèle, effort) et la bande de coût. `estimer` la donne.
2. **À l'ouverture d'une piste** (`/pistes start`) : comparer l'étiquette au modèle courant.
   Si elles diffèrent et que le contexte est encore court, `/clear` puis bascule ; si le
   contexte est déjà lourd, continuer ici et le noter — une bascule à chaud relit tout le
   contexte sans cache.
3. **À la fermeture d'une piste** : `tache done --qualite OK|reprise|echec`, et reporter la
   ligne de consommation dans le bilan de séance.
4. **Quand le forfait file plus vite que prévu** : `mesurer --retro --jours 7`, puis regarder
   la part des lectures de cache et les sessions en tête de classement. Vérifier d'abord que
   le feu n'est pas simplement en train d'annoncer la fin du compte COURANT (deux comptes,
   horizon 3,5 j) : dans ce cas la réponse est la bascule de compte, pas la sobriété.
5. **Quand un modèle inconnu apparaît** (`etat` le signale, le hook SessionStart aussi) :
   `maj --apply`, puis relire la grille.
6. **Quand une phase d'une piste se clôt sans que la piste soit close** : une étiquette décrit
   le travail qui RESTE, pas celui qui a justifié l'ouverture. Si le reste demande une autre
   configuration (méthode tranchée et code livré, il ne reste qu'une lecture de résultat), on
   RÉVISE l'étiquette dans le registre au même moment, avec une ligne qui dit pourquoi. La
   ligne `Lancement :` du bilan reprend ensuite exactement cette étiquette : elle ne s'en
   écarte jamais d'elle-même. Cas fondateur du 2026-09-24 (environnement, AG3) : « Pistes
   ouvertes » listait AG3 `[Opus:high]` et le Lancement proposait `Sonnet:medium` pour la même
   piste ; l'utilisateur a cru à deux pistes mélangées. Contrôle exécutoire :
   `${CLAUDE_PLUGIN_ROOT}/skills/pistes/lancement_check.py`, appelé par le hook Stop
   `pistes_audit_stop.sh` dans tout projet doté de `pistes.md`.

## Pièges vérifiés

- `/model <alias>` et `/effort <niveau>` tapés directement, ou validés par Entrée, écrivent le
  défaut des sessions futures dans `settings.json` ; seule la touche `s` limite le choix à la
  session. **Depuis le 2026-09-13 la touche n'a plus d'importance** : `env.ANTHROPIC_MODEL` prime
  sur la clé `model` (ordre documenté et vérifié), et le hook `defaults_guard.sh`
  (UserPromptSubmit + PostModelSwitch) ramène `settings.json` à `~/.claude/defaults_reference.json`,
  qui est la seule source de vérité des défauts (`Sonnet:high` partout). Changer un défaut global =
  demande explicite de CG, exécutée en éditant ce fichier. Aucun hook ne peut fixer le modèle d'une
  session (`PreModelSwitch` ne sait que bloquer) : le routage reste un geste humain.
- Une bascule de modèle ou d'effort en cours de session relit tout le contexte **sans cache**
  (exception : l'effort sur Fable 5.1). Au tour 1 le contexte ne fait que ~65 k (mesuré) : la
  bascule y coûte 0,4 $-éq vers Opus et se fait directement, sans `/clear` ; en session chargée
  (300 k, ~2 $-éq), `/clear` d'abord avec l'amorce de la piste.
- Un sous-agent ne partage pas le cache du parent et paie son propre préfixe : il est rentable
  quand il évite au parent d'avaler une grosse sortie d'outil, pas pour une question courte.
- Ne jamais mettre `model:` dans le frontmatter d'un skill : ce tour devient une bascule.
- Un rapport de sous-agent ne prouve pas qu'il a écrit : vérifier le fichier attendu. Et un hook
  `SubagentStop` qui renvoie `additionalContext` fait repartir le sous-agent pour un tour et
  écrase son rapport (mesuré le 2026-09-13, corrigé dans `coord_subagent_check.sh`).
- Les poids valent les prix de liste tant que `calibrer` n'a pas tourné : ce sont des
  ordres de grandeur relatifs, pas une facture.
