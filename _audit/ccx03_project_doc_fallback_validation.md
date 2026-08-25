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

Le scan récursif du 2026-08-25 compte :

- 264 fichiers `CLAUDE.md` ;
- 248 sans `AGENTS.md` dans le même répertoire ;
- 16 accompagnés d'un `AGENTS.md` ;
- 3 fichiers `CLAUDE.md` au-dessus de 32 KiB ;
- 1 seul fichier au-dessus de 32 KiB sans `AGENTS.md` local.

Les trois fichiers volumineux mesurent 227598, 73136 et 36239 octets. Les deux
premiers possédaient déjà un `AGENTS.md`. Le troisième, seul cas exposé à la
troncature silencieuse, appartient à un projet-outil actif.

## Traitement du fichier exposé à la troncature

Un `AGENTS.md` court a été créé à la racine du projet-outil concerné. Il porte
uniquement les règles opérationnelles et les pointeurs vers sa documentation
longue et ses registres. L'ajout est tracé dans son cahier append-only à
l'entrée du 2026-08-25 13:25 ; aucun résultat ni registre scientifique n'a été
modifié.

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

La configuration persistante, la précédence, la découverte imbriquée et le seul
cas Claude-only dépassant 32 KiB sont traités. CCX-03 reste ouverte pour classer
les 248 projets sans `AGENTS.md` selon leur activité et migrer progressivement
les seuls projets actifs, conformément au critère de clôture.
