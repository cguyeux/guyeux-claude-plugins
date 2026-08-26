# Validation CCX-13 : import sélectif des mémoires Claude

Date : 2026-08-26.

## Périmètre observé

- Source : `~/.claude/projects/*/memory/`.
- 124 fichiers Markdown, 362 100 octets, répartis entre 15 clés projet.
- Trois `.consolidate-lock` exclus comme verrous techniques.
- Les 2,9 Go de sessions, caches et états sous `~/.claude/projects/` n'ont pas été copiés.
- Aucun chat récent n'a été importé.

Le décompte corrige la formulation historique « 123 fichiers, environ 353 Ko » :
les trois entrées brutes supplémentaires du premier instantané étaient des
verrous techniques. Une nouvelle mémoire Claude a été créée pendant la
validation ; le manifeste final l'inclut, sans figer dans l'outil un cardinal
qui rendrait l'audit périodique incapable d'accepter un ajout légitime.

## Crible adversarial

Verdict : reformuler l'import massif en import classifié. Le contre-argument le
plus fort est qu'un même répertoire Claude mélange préférences durables, état
projet périssable, références, informations personnelles et index. Le contrôle
falsifiant est un import témoin dont le `cwd`, les hashes, la sensibilité et
l'idempotence doivent tous être prouvés. Un seul échec ferme le lot concerné.

Le gain d'un import brut est inférieur à son coût : il dupliquerait la KB et
pourrait faire prévaloir un ancien état sur le cahier ou
`etat_des_decouvertes.md`. La source est donc classée avant toute écriture.

## Taxonomie complète

| Type source | Fichiers | Destination de principe |
|---|---:|---|
| feedback | 49 | KB technique partagée |
| project | 39 | registres courants du projet, après revérification |
| reference | 17 | KB technique partagée |
| index | 15 | routage d'extension, sans duplication du détail |
| user | 4 | instructions globales ou KB privée après déduplication |

Le routage effectif produit 62 candidats KB, 35 candidats registres projet, 12
index d'extension et 15 fichiers isolés pour revue privée. Treize fichiers
contiennent un localisateur d'infrastructure. Aucun motif de secret exploitable
n'a été trouvé dans les 124 sources. Deux index contiennent un lien Markdown
local cassé. Les rapports ne conservent jamais les valeurs à l'origine d'un
indicateur sensible.

La dimension de fraîcheur est indépendante du type : 64 fichiers sont des
candidats durables, 45 états projet ou références d'infrastructure sont marqués
`potentially-stale-verify-live`, et 15 sont de simples index. Aucun instantané
daté n'est donc promu sans comparaison au registre ou à l'état réel.

## Interface Codex vérifiée

CLI locale : `codex-cli 0.149.1`.

- `memories` est activé dans le profil local.
- `external_agent_memory_import` est une fonction en développement, désactivée
  par défaut, activée seulement sur la commande d'import.
- `external_migration` est retiré de la CLI et reste une dette CCX-14 dans le
  fichier de configuration.
- Le protocole app-server expose `externalAgentConfig/detect` et
  `externalAgentConfig/import`. La sélection mémoire porte sur des clés projet,
  jamais sur le répertoire `projects/` complet.

La documentation officielle décrit le stockage sous `~/.codex/memories/`, la
génération différée, le contrôle par chat et la nécessité de revoir les fichiers
avant partage. Elle présente encore la fonction mémoire comme expérimentale,
alors que la CLI locale classe le cœur `memories` comme stable. La CLI installée
fait foi pour l'exécution et cet écart documentaire est conservé comme réserve.

## Témoin officiel et contrôle négatif

Contrôle négatif Voynich : deux tentatives, dont une avec un `cwd` explicite
dans l'item de migration, ont toutes deux échoué avec
`selected memory project has no reliable cwd`. Aucun fichier Voynich n'a été
importé et le garde-fou n'a pas été contourné.

Témoin PredictOps : la clé
`-home-christophe-docs-codes-predictops`, proposée par le détecteur officiel, a
été importée avec succès. Résultat :

- `scope.json` contient `/home/christophe/docs/codes/predictops` ;
- trois fichiers Markdown source et cible ont des SHA-256 identiques ;
- seul `extensions/external_agent_import` diffère de la sauvegarde préalable ;
- le second passage ne repropose plus la clé ;
- le wrapper reconnaît l'import intègre comme déjà à jour et ne crée aucun
  doublon ni nouvelle sauvegarde.

Sauvegarde préalable :
`~/.agents/migration/backups/memory/20260826T053639.614776547Z/memories`.

## Frontière durable

- Mémoire native Codex : contexte local produit ou importé avec provenance et
  scope, non autoritatif.
- KB `~/.agents/knowledge/` : apprentissages techniques inter-projets.
- Registres projet : vérité scientifique courante, historique et pistes.
- Source Claude non importée : matériau de migration accessible par le rapport,
  jamais une instruction active.

Le pointeur autorisé
`~/.codex/memories/extensions/ad_hoc/notes/20260826T054806Z-claude-memory-routing.md`
rend le manifeste complet découvrable sans recopier les 120 autres fichiers.

## Artefacts et contrôles

- `_audit/tools/audit_claude_memories.py` : inventaire et classification.
- `_audit/tools/import_claude_memories.py` : détection, sauvegarde, import et
  vérification officiels, dry-run par défaut.
- `_audit/claude_memory_report.json` : manifeste fichier par fichier sans valeur
  sensible.
- `_audit/claude_memory_report.md` : synthèse exploitable.
- `_audit/tests/test_claude_memories.py` : sensibilité, liens, sélection, scope,
  hashes et idempotence.

Contrôles ciblés : six tests passent. `audit_claude_memories.py --check` et
`import_claude_memories.py --check` passent sur le profil réel.

La suite transversale a exécuté 105 tests : 103 passent et deux contrôles
d'inventaire échouent parce que le skill concurrent non indexé
`redac/skills/soumission/` porte le registre global de 189 à 190 entrées. Le
harnais Git-index s'arrête de même sur les rapports d'instructions projet
devenus obsolètes à la suite de changements hors CCX-13. Ces dérives ne sont ni
créées ni corrigées par ce lot et leurs fichiers restent hors de son index.
