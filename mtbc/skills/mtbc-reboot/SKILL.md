---
name: mtbc-reboot
description: >-
  [DEPRECIE -> /reboot] Aucun declencheur : ne jamais l'invoquer directement.
  Academic research toolkit, conduite de projet : ce skill a ete remplace le
  2026-09-22 par le skill utilisateur `/reboot`, generique et scripte. Ne rien
  lancer ici ; toute reprise de projet passe par `/reboot diagnostic`. Conserve
  uniquement comme pierre tombale pour les registres qui le citent encore.
argument-hint: "(deprecie — utiliser /reboot)"
allowed-tools: Read
user-invocable: false
---

# /mtbc-reboot -- DEPRECIE, remplace par `/reboot`

Ce skill est deprecie depuis 2026-09-22 (piste AB, `~/docs/environnement`). Il
est remplace par le skill utilisateur `/reboot` (`~/.claude/skills/reboot/`),
generique a tout projet de recherche du depot, scripte (`reboot.py`, dry-run
par defaut) plutot que porte par de la prose, et compatible avec le modele a
cinq artefacts (etat, pistes, verdict de diffusion, plan narratif) que ce
skill ignorait.

Les projets qui portent encore un vestige d'un reboot conduit par ce skill
(`reboot_state.md`, `reanalysis_registry.md`, `archives/<date>_reboot/`) se
lisent sans le relancer : `python3 ~/.claude/skills/reboot/reboot.py status
--legacy` affiche ces fichiers en lecture seule. Pour engager un reboot
aujourd'hui sur n'importe quel projet, y compris un projet MTBC : `/reboot
diagnostic`.

Le contenu integral de ce skill (889 lignes, quatre phases archive / survey /
plan-claim / article) reste dans l'historique git du depot `plugins/` et est
resume, avec les raisons precises de son remplacement, dans
`~/.claude/skills/reboot/references/legacy_mtbc_reboot.md`.
