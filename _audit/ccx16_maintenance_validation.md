# Validation CCX-16 : reconstruction et maintenance durable

Date : 2026-08-26

## Verdict

CCX-16 est terminé pour les surfaces reconstructibles sans secret. Le dépôt
porte désormais un manifeste machine-readable, un outil de snapshot,
reconstruction, restauration et audit, une procédure complète, des tests et un
timer hebdomadaire actif.

La frontière est explicite : aucun profil brut, identifiant, historique, cache
ou mémoire native n'est copié. Les entrées KB et skills sont scannées
individuellement. Les sous-arbres propres sont sauvegardés ; ceux que le scanner
bloque restent du ressort du dispositif privé de la machine.

## Snapshot réel

Le snapshot valide est installé sous :

`~/.agents/migration/backups/ccx16/20260826T074302.276003Z/`

- mode du répertoire : `700` ;
- mode du manifeste : `600` ;
- taille : 16 Mio ;
- éléments inventoriés : 171 ;
- éléments sauvegardés : 157 ;
- éléments bloqués et non copiés : 14 ;
- Graphify : sauvegardé ;
- classes exclues : credentials, profils bruts, historiques, caches et
  mémoires natives.

Le premier bundle produit pendant le développement a révélé une empreinte de
fichier dépendante du nom du payload. Il a été déplacé sans suppression sous
`backups/ccx16/superseded/20260826T073717.523853Z-invalid-digest-v1/`. Le format
valide porte désormais `digest_version: 2` et a été retesté de bout en bout.

## Reconstruction vierge

Un profil neuf sans cache a été reconstruit depuis le snapshot valide et le
marketplace versionné. Résultats observés :

| surface | résultat |
|---|---:|
| instructions Claude et Codex | conformes à la source commune |
| vues KB | deux liens canoniques |
| hooks Codex | source approuvée |
| politique d'exécution | lien vers la source versionnée |
| skills personnels Agents restaurés | 43 |
| entrées KB restaurées | 72 |
| skills Codex directs | 53 |
| skills Codex empaquetés | 136 |
| plugins Codex activés | 10 |
| Graphify | présent |
| skills désactivés visibles | 0 |
| liens morts | 0 |

Le profil temporaire a ensuite été placé à la corbeille.

L'audit du profil vierge passe 13 contrôles sur 15. Les deux refus sont voulus :

1. aucun MCP n'est fabriqué sans réauthentification ni restauration des
   variables secrètes ;
2. le registre canonique détecte le skill non suivi `soumission` présent dans le
   worktree réel, hors lot CCX-16.

Sur le profil personnel courant, 14 contrôles sur 15 passent. Le seul écart est
le même registre canonique rendu obsolète par ce travail non suivi. Les MCP,
plugins, hooks, instructions, règles, vues KB et fermes installés sont conformes.

## Contrôles adversariaux

- le mode par défaut de `snapshot`, `restore` et `reconstruct` est un dry-run ;
- une cible divergente est déplacée dans un rollback horodaté avant
  remplacement ;
- le test conserve puis relit un ancien `hooks.json` dans le rollback ;
- un hook non approuvé est détecté ;
- un lien mort est détecté ;
- `mbovis` artificiellement réintroduit est détecté ;
- aucune primitive de suppression permanente n'existe dans l'outil ;
- le manifeste refuse tout chevauchement entre snapshot et exclusions ;
- les rapports ne sérialisent aucune valeur secrète.

## Audit périodique

Les unités `codex-migration-audit.service` et `.timer` sont installées sous
`~/.config/systemd/user/`. Le timer est `enabled` et `active`. Sa première
exécution est planifiée le 31 août 2026. Il lance uniquement la commande
`maintain_environment.py audit` en lecture seule.

## Artefacts versionnés

- `maintenance/environment_manifest.json` ;
- `maintenance/README.md` ;
- `maintenance/systemd/codex-migration-audit.service` ;
- `maintenance/systemd/codex-migration-audit.timer` ;
- `_audit/tools/maintain_environment.py` ;
- `_audit/tests/test_maintenance.py` ;
- intégration dans `_audit/tools/check_all.py`.

## Commandes de contrôle

```text
python3 _audit/tools/maintain_environment.py validate
python3 _audit/tools/maintain_environment.py snapshot
python3 _audit/tools/maintain_environment.py reconstruct --snapshot CHEMIN
python3 _audit/tools/maintain_environment.py audit
python3 -m unittest _audit.tests.test_maintenance _audit.tests.test_check_all
```

La projection exacte de l'index passe les 120 tests du dépôt. Le harnais global
valide les registres de skills, matrices, documentation et audit canonique, puis
s'arrête sur les rapports d'instructions projet devenus obsolètes à cause de
changements externes au lot. Ils ne sont pas écrasés par CCX-16.

Le scanner `publish` appliqué aux dix fichiers CCX-16 rend zéro signalement. Le
scan global de l'index retrouve quatorze candidats historiques déjà présents
dans iTOL, IMDb, CRISPRCasdb et un ancien test ; aucun n'est introduit par ce
lot.
