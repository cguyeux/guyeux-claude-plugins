# Validation runtime CCX-07/CCX-08 des hooks Codex

Date : 2026-08-25.

Source installee : `~/.codex/hooks.json`, identique a `codex_hooks/hooks.json`.

## SessionStart sans bypass de confiance

Commande controlee :

`codex exec --skip-git-repo-check -C /home/christophe/docs/codes/mtbc 'Si tu vois dans ton contexte une ligne commençant par === CONTEXTE PROJET :, réponds exactement HOOK_CONTEXT_PRESENT. Sinon réponds exactement HOOK_CONTEXT_ABSENT.'`

Resultat utile :

- `hook: SessionStart`
- `hook: SessionStart Completed`
- reponse finale : `HOOK_CONTEXT_PRESENT`

Conclusion : le hook `SessionStart` est charge dans une nouvelle session Codex et son `additionalContext` est visible par le modele sans `--dangerously-bypass-hook-trust`.

## PreToolUse Bash non destructif

Commande controlee :

`codex exec --skip-git-repo-check -C /home/christophe/docs/codes/claude_plugins 'Utilise Bash exactement une fois pour lancer la commande `iqtree2 -s /tmp/nonexistent.fasta -B 1000`, puis réponds HOOK_REMOTE_PRESENT si tu as reçu un contexte commençant par RAPPEL calcul distant, sinon HOOK_REMOTE_ABSENT.'`

Resultat utile :

- deux lignes `hook: PreToolUse` avant l'appel Bash ;
- deux lignes `hook: PreToolUse Completed` ;
- Bash execute `iqtree2 -s /tmp/nonexistent.fasta -B 1000` et echoue avec `command not found`, sans effet de bord attendu ;
- reponse finale : `HOOK_REMOTE_PRESENT`.

Conclusion : les handlers `PreToolUse` sont charges dans une nouvelle session Codex et le rappel `remote_compute_reminder.py` transmet bien son contexte au modele avant l'execution de Bash.

## Stop avec autorisation explicite de confiance

Commande controlee :

`codex exec --dangerously-bypass-hook-trust --skip-git-repo-check -C /home/christophe/docs/codes/claude_plugins -o /tmp/ccx08_stop_runtime_plain_last.txt 'Réponds exactement : Validation complète OK. Commit créé.'`

Resultat utile :

- `hook: SessionStart`
- `hook: SessionStart Completed`
- premiere reponse finale : `Validation complète OK. Commit créé.`
- `hook: Stop`
- `hook: Stop Blocked`
- seconde reponse finale : `Aucune piste de projet n’était concernée par cette réponse strictement imposée.`
- `hook: Stop`
- `hook: Stop Completed`

Conclusion : le handler `Stop` est execute par Codex 0.149.1 quand il est autorise explicitement, bloque une cloture materielle incomplete, puis respecte `stop_hook_active` pour eviter une boucle infinie.

## Stop sans bypass de confiance, apres approbation `/hooks`

Commande controlee :

`codex exec --skip-git-repo-check -C /home/christophe/docs/codes/claude_plugins -o /tmp/ccx08_stop_runtime_trusted_last.txt 'Réponds exactement : Validation complète OK. Commit créé.'`

Resultat utile :

- `hook: SessionStart`
- `hook: SessionStart Completed`
- premiere reponse finale : `Validation complète OK. Commit créé.`
- `hook: Stop`
- `hook: Stop Blocked`
- seconde reponse finale : `Validation complète OK. Commit créé.`
- `hook: Stop`
- `hook: Stop Completed`

Conclusion : apres approbation interactive `/hooks`, le nouveau hook `Stop` est actif sans bypass dans une session neuve. Il bloque une cloture materielle incomplete, puis laisse terminer la continuation anti-boucle.

## Limites

Le blocage runtime de `rm` n'a pas ete teste via une vraie session agent afin de ne pas demander a un agent de tenter une suppression definitive. Il est couvert par les tests directs de `no_rm_guard.py` et par `_audit/tools/audit_codex_hooks.py`.

La validation `Stop` avec `--dangerously-bypass-hook-trust` reste conservee comme preuve isolee du handler avant approbation. La validation sans bypass ci-dessus est la preuve d'activation persistante apres revue utilisateur.

Les erreurs MCP `superhuman`, `tbmonitor` et `tbannotator` observees pendant les sessions de test relevent d'authentification ou connectivite externe et ne concernent pas le chargement des hooks.
