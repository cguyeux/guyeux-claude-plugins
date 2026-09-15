# bio_redac — coquille de compatibilité (P5.2, 2026-09-15)

Ce répertoire n'est plus un plugin Claude Code (pas de `.claude-plugin/plugin.json`, absent de `marketplace.json`, invisible à `claude plugin list`). Il ne contient que des liens symboliques vers les skills désormais réels ailleurs (17 plugins de la refonte P5), pour que les scripts externes qui référencent encore le chemin `bio_redac/skills/<nom>` en dur continuent de fonctionner.

102 fichiers de code sous `~/docs/codes` et `~/docs/projects` référençaient ces chemins au 2026-09-15 (recensement `grep`). Migrer ces références vers leur nouvel emplacement (table `audit/2026-09-15/table_affectation.tsv`, colonne `cible_fine`) avant le retrait de cette coquille, prévu à P7.3 comme les autres liens de compatibilité de ce projet.
