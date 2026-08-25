# Validation CCX-11, ferme de skills commune

Date : 2026-08-25

## Résultat

`_audit/tools/skills_farm.py` fournit désormais une interface commune aux
surfaces Claude et Codex. La source de vérité est `canon_skills.json` et
`~/.claude/scripts/skills_farm.py` est un adaptateur vers cet outil versionné.
L'ancien script a été conservé sous
`~/.agents/migration/backups/20260825T_ccx11/skills_farm.py`.

L'audit unique contrôle 189 skills canoniques, 53 exports directs Codex, 136
skills empaquetés, 10 plugins personnels installés, les deux fermes personnelles
de 46 skills, les fermes projet Claude, les liens morts, les collisions de nom,
les cibles non canoniques et le poids des métadonnées. Il encode explicitement
la différence de découverte : masquage possible par un farm projet sous Claude,
ferme personnelle, exports et plugins sous Codex sans supposer de farm projet.

Le farm racine `~/docs/.claude/skills` a reçu les deux liens canoniques manquants,
`fig-ideation` et `literature-access`. Un second dry-run annonce zéro action.
Les deux fermes mixtes encore partielles sont signalées sans mutation : le farm
de candidature conserve sa sélection locale et `mabossDemo` conserve son skill
local `deploy` tant qu'une sélection explicite n'est pas demandée.

## Garde-fous validés

- `audit` est en lecture seule ;
- `sync` reste un dry-run sans `--apply` ;
- aucune primitive de suppression permanente n'est présente ;
- un chemin existant, y compris un lien divergent, n'est jamais remplacé ;
- une synchronisation demande une ferme cible et une sélection de skills ;
- un lot sur une ferme mixte est refusé sans `--allow-mixed` ;
- cinq tests dédiés couvrent dérive, lien mort, dry-run, ferme mixte, refus de
  remplacement et création exclusive de liens symboliques ;
- le harnais global exécute aussi l'audit unifié.

## Commandes de référence

```text
python3 _audit/tools/skills_farm.py audit --profile-root ~/.codex
python3 _audit/tools/skills_farm.py sync --farm ~/docs/.claude/skills --plugin redac --all-missing --dry-run
python3 _audit/tools/check_all.py --source git-index --profile-root ~/.codex
```
