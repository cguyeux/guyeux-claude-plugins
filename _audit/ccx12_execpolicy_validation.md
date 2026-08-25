# Validation CCX-12, permissions Claude et execpolicy Codex

Date : 2026-08-25

## Référence fonctionnelle

La documentation officielle Codex décrit les fichiers `rules/*.rules`, les
décisions `allow`, `prompt` et `forbidden`, la priorité de la décision la plus
restrictive, les tests intégrés `match` et `not_match`, ainsi que le traitement
spécial des wrappers shell. Source :
<https://learn.chatgpt.com/docs/agent-configuration/rules>.

## Inventaire constaté

- Claude : 97 autorisations, dont 89 Bash, 7 destructives et 74 commandes
  exactes ou historiques ;
- Codex avant migration : 447 `prefix_rule`, toutes en `allow` ;
- règles Codex avec chemin temporaire : 143 ;
- wrappers shell exacts : 177 ;
- références à `~/.claude/knowledge` : 89 ;
- règles historiques sans justification, `match` ou `not_match` : 447.

Le rapport agrégé et la fréquence observée sur sept jours sont conservés dans
`_audit/execpolicy_report.json` et `_audit/execpolicy_report.md`. Les sessions
ne sont jamais recopiées : seuls les noms d'exécutables et leurs comptes sont
persistés.

## Politique retenue

`codex_rules/default.rules` contient 15 règles :

- 4 `forbidden` pour les suppressions permanentes, `git clean`, le reset dur et
  les push forcés usuels ;
- 10 `prompt` pour les mutations distantes, l'élévation de privilèges, le
  réseau, les wrappers shell, les services, l'infrastructure et les interfaces
  graphiques ;
- 1 `allow`, limité à `gio trash`.

Chaque règle porte une justification et des exemples positifs et négatifs. Les
commandes ordinaires restent dans le sandbox et n'ont donc pas besoin d'une
autorisation globale. Les anciennes permissions Claude ne sont pas additionnées
aux règles Codex.

## Installation et réversibilité

`~/.codex/rules/default.rules` est un lien vers la politique Git. Le fichier de
447 règles a été déplacé vers
`~/.agents/migration/backups/execpolicy/20260825T160113.299219Z/default.rules`.
Aucun fichier n'a été supprimé.

## Tests

`codex execpolicy check` confirme :

- `rm -rf ...` : `forbidden` ;
- `git push --force ...` : `forbidden` ;
- `git push ...` : `prompt` ;
- `ssh ...` : `prompt` ;
- `gio trash ...` : `allow` ;
- wrapper simple ou opaque contenant une suppression : jamais `allow`.

Le hook `no_rm_guard` reste nécessaire comme seconde barrière pour un script
opaque, car une règle de préfixe ne peut pas interpréter toutes les expansions,
substitutions et structures de contrôle du shell.

La projection Git propre exécute 100 tests avec succès. Le harnais franchit
également les audits de skills, hooks, profil et politique active. Il s'arrête
ensuite sur les deux rapports KB déjà modifiés par une autre session, laissés
hors de ce lot.

La documentation officielle précise qu'une nouvelle session est nécessaire
pour charger les règles modifiées. `codex execpolicy check` teste toutefois le
fichier actif directement et permet de valider la politique avant redémarrage.
