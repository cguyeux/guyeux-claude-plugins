# Validation CCX-03 du fallback `CLAUDE.md` pour Codex

Date : 2026-08-25

## Configuration persistante

Le profil utilisateur Codex contient désormais, au niveau racine de
`~/.codex/config.toml` :

```toml
project_doc_fallback_filenames = ["CLAUDE.md"]
```

Cette option conserve `AGENTS.md` comme nom principal et ne consulte
`CLAUDE.md` qu'en repli lorsqu'aucun `AGENTS.md` n'est applicable.

## Preuves runtime

Les témoins temporaires ont été exécutés sans surcharge `-c`, après écriture de
la configuration persistante.

| Scénario | Commande résumée | Résultat |
|---|---|---|
| Projet racine avec seulement `CLAUDE.md` | `codex exec --skip-git-repo-check -C /tmp/ccx03_only_claude ...` | `CLAUDE_FALLBACK_LOADED` |
| Sous-répertoire imbriqué du même projet | `codex exec --skip-git-repo-check -C /tmp/ccx03_only_claude/sub/a ...` | `CLAUDE_FALLBACK_LOADED` |
| Projet avec `AGENTS.md` et `CLAUDE.md` contradictoires | `codex exec --skip-git-repo-check -C /tmp/ccx03_precedence/sub/a ...` | `AGENTS_WINS` |

Les mêmes trois scénarios avaient d'abord été vérifiés avec la surcharge
explicite `-c 'project_doc_fallback_filenames=["CLAUDE.md"]'`. Les répertoires
témoins ont ensuite été déplacés vers un volume compatible et mis à la
corbeille avec `gio trash`.

## Inventaire sous `~/docs/codes`

Le premier scan brut compte 264 fichiers `CLAUDE.md`. L'audit versionné
`_audit/tools/audit_project_instructions.py` affine ce total :

- 231 répertoires projet retenus ;
- 33 copies internes ou dépendances exclues, notamment `.claude/worktrees`,
  environnements Python et `node_modules` ;
- 17 projets avec `AGENTS.md` local ;
- 214 projets couverts directement par le fallback `CLAUDE.md` ;
- 64 fallbacks avec travail ouvert explicitement signalé ;
- 19 fallbacks placés sous un chemin d'archive ou d'abandon ;
- 131 fallbacks dont l'activité reste indéterminée, mais dont les instructions
  sont néanmoins accessibles ;
- 0 fallback individuel et 0 chaîne effective d'instructions au-dessus du
  budget de 32 KiB après remédiation.

Le JSON conserve les 231 lignes de projet, les 33 exclusions et leurs raisons.
Le Markdown fournit le triage complet. Aucun signal n'est promu en verdict
d'activité automatique.

## Traitement du fichier exposé à la troncature

Un `AGENTS.md` court a été créé à la racine du projet-outil concerné. Il porte
uniquement les règles opérationnelles et les pointeurs vers sa documentation
longue et ses registres. L'ajout est tracé dans son cahier append-only à
l'entrée du 2026-08-25 13:25 ; aucun résultat ni registre scientifique n'a été
modifié.

L'audit de chaîne a ensuite montré que six projets possédaient un `AGENTS.md`
local lui-même supérieur au budget. Un `AGENTS.override.md` de 993 à 1100
octets a été ajouté à chacun. Les longs `AGENTS.md` et `CLAUDE.md` restent
intacts et consultables par sections ciblées. Chaque ajout est tracé dans le
cahier append-only du projet.

La CLI locale expose la précédence `AGENTS.override.md`, `AGENTS.md`, puis
fallbacks configurés. Une sonde neutre depuis un sous-répertoire a répondu
`AGENTS_OVERRIDE_LOADED`. Une sonde réelle sur un projet documentaire a répondu
`OVERRIDE_COURT_ACTIF`.

## Limite de la validation

Une tentative de contrôle détaillé depuis un sous-répertoire du projet réel a
été rejetée par la revue automatique avant exécution à cause de la
classification du chemin. Ce contrôle n'a pas été contourné. La preuve runtime
repose donc sur les projets témoins neutres, tandis que le risque de troncature
du projet réel est réduit matériellement par la présence de son `AGENTS.md`
court.

Les erreurs MCP apparues pendant certaines sessions témoins concernaient des
serveurs externes non authentifiés ou injoignables et ne modifient pas les
résultats de découverte des instructions projet.

## Statut CCX-03

CCX-03 est close. La configuration persistante couvre les 214 projets encore
Claude-only sans recopier leurs instructions. Les 17 projets dotés d'un
`AGENTS.md` sont prioritaires, dont six utilisent un override court pour éviter
la troncature. Les sondes valident fallback, découverte imbriquée, précédence et
override ; l'audit complet ne trouve plus aucune chaîne au-dessus du budget.
