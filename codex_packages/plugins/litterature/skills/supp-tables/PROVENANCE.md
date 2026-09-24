# Provenance — supp-tables

Créé le 2026-09-08 depuis le projet `mtbc/Rv2520c`, piste P11.1.

**Origine.** La sous-piste P9.3 de ce projet cherchait une preuve empirique d'orientation
membranaire dans la protéomique publiée. Les quatre jeux de données qui portaient la réponse ont
tous été trouvés dans des tables supplémentaires, aucun par recherche plein texte : la chaîne
« Rv2520c » n'apparaît dans le corps d'aucun des articles de Lepe 2025, Jaisinghani 2024 et
Sanyal 2026. Le code de fouille écrit pour l'occasion
(`experiments/2026-09-07_p9_3_proteomique_surface/grep_supp.py`) a servi quatre fois en deux jours,
sur deux pistes distinctes (P9.3 et P10), ce qui a motivé sa promotion en skill plutôt que sa
réécriture au coup suivant.

**Ce qui a été ajouté au passage du script jetable au skill.**
- Résolution DOI / PMID / PMCID par Europe PMC, sans jamais deviner un PMCID.
- Repli préprint par appariement des listes d'auteurs, la recherche par titre échouant dès que le
  titre change entre préprint et version publiée (constaté sur Jaisinghani 2024).
- Reprise sur HTTP 429 de bioRxiv.
- Vérification de la taille des fichiers obtenus (piège du disque plein, mesuré le 2026-09-07).
- La sous-commande `rank`, qui n'existait pas dans le script jetable et qui porte le garde-fou
  central : situer une valeur dans la distribution de sa propre table.

**Connaissances associées.** `~/.agents/knowledge/topology-orientation-calibration.md`, sections du
2026-09-07 sur l'angle mort des tables supplémentaires et sur les recettes réseau.
