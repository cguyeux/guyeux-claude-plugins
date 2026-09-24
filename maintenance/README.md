# Maintenance durable de l'environnement Claude et Codex

Ce répertoire clôt CCX-16. Il permet de reconstruire les surfaces non
sensibles depuis le dépôt et un snapshot local contrôlé, sans utiliser les
caches Claude ou Codex.

## Frontière de reconstruction

Le dépôt contient les plugins, hooks Codex, règles, registres, tests et scripts
de synchronisation. Le snapshot automatique conserve les instructions communes,
les hooks Claude et `TASKS.md`. Il scanne aussi séparément chaque entrée de la
KB et chaque skill personnel, puis sauvegarde uniquement les sous-arbres propres.

Les entrées KB ou skills bloquées, les mémoires natives, les profils bruts, les
historiques et les authentifications ne sont jamais copiés par cet outil. Les
sous-arbres bloqués doivent être restaurés depuis la sauvegarde privée de la
machine après revue. Les authentifications Claude, Codex et MCP doivent être
rétablies par connexion ou variables d'environnement.

## Snapshot récupérable

Prévisualisation :

```text
python3 _audit/tools/maintain_environment.py snapshot
```

Création sous `~/.agents/migration/backups/ccx16/` :

```text
python3 _audit/tools/maintain_environment.py snapshot --apply
```

Chaque élément est scanné avant copie. Le manifeste du snapshot contient des
empreintes et des tailles, jamais le contenu des fichiers. Une source requise
bloquée par le scanner fait échouer l'opération en mode fermé.

## Reconstruction depuis une machine vierge

1. Installer Python, Git, `gio`, Claude Code et Codex CLI.
2. Cloner ce dépôt sous `~/docs/environnement/plugins` à une révision vérifiée.
3. Copier le snapshot CCX-16 sur la machine et restaurer les sources privées
   validées par le dispositif privé habituel.
4. Prévisualiser la reconstruction.
5. Appliquer les fichiers dérivés et reconstruire les plugins Codex depuis le
   marketplace du dépôt.
6. Réauthentifier Claude, Codex et les MCP, puis relancer l'audit.

Commandes :

```text
python3 _audit/tools/maintain_environment.py reconstruct --snapshot CHEMIN_DU_SNAPSHOT
python3 _audit/tools/maintain_environment.py reconstruct --snapshot CHEMIN_DU_SNAPSHOT --apply --install-codex-plugins
python3 _audit/tools/maintain_environment.py audit
```

La reconstruction régénère les instructions, les vues de KB, les hooks, la
politique d'exécution, les 53 liens directs et les dix plugins Codex. Elle ne
réactive jamais `mbovis` ou `triangulate-route`.

Pour Claude, reconstruire le marketplace et les trois plugins personnels
actifs avec les commandes suivantes :

```text
claude plugin marketplace add ~/docs/environnement/plugins
claude plugin install bio_bacteria@guyeux-claude-plugins -s user -y
claude plugin install bio_pathogens@guyeux-claude-plugins -s user -y
claude plugin install redac@guyeux-claude-plugins -s user -y
```

Pyright et les autres plugins tiers restent des dépendances externes à
réinstaller depuis leur source officielle.

## Rollback

Avant chaque remplacement, la cible existante est déplacée sous
`~/.agents/migration/rollbacks/reconstruct-<horodatage>/`. Aucun fichier n'est
supprimé définitivement. Pour restaurer un snapshot sans reconstruire les
surfaces dérivées :

```text
python3 _audit/tools/maintain_environment.py restore CHEMIN_DU_SNAPSHOT
python3 _audit/tools/maintain_environment.py restore CHEMIN_DU_SNAPSHOT --apply
```

Après inspection, déplacer manuellement les fichiers souhaités du répertoire
de rollback vers leur cible. Si une cible doit être écartée, utiliser
`gio trash CHEMIN`.

## Audit périodique

L'audit est strictement en lecture seule. Il vérifie la synchronisation des
instructions, les vues de KB, les hooks approuvés, la politique d'exécution,
les liens morts, les skills désactivés, les plugins, les noms MCP et les
registres générés. Il ne sérialise aucune valeur de configuration.

Les unités systemd utilisateur sont dans `maintenance/systemd/`. Après copie
vers `~/.config/systemd/user/`, activer le timer avec :

```text
systemctl --user daemon-reload
systemctl --user enable --now codex-migration-audit.timer
systemctl --user list-timers codex-migration-audit.timer
```

Sur une machine sans bus systemd utilisateur accessible, conserver les unités
installées et effectuer l'activation à la prochaine session utilisateur.

## Cycle d'évolution

Modifier la source canonique, lancer les générateurs, exécuter les tests,
scanner l'index Git, committer, synchroniser les profils, ouvrir une nouvelle
session et valider les invariants. Ne jamais corriger directement un cache ou
un fichier dérivé sans reporter la modification vers sa source.
