# Points de vigilance -- texte integral

Reference de `mtbc-bilan` : les douze points de vigilance du skill, dans leur
formulation complete. Le SKILL.md n'en garde que les plus critiques. A parcourir
en fin de bilan, ou quand un cas limite se presente (cahier double, BDD absente,
collision de fichier, projet imbrique).

## Points de vigilance

1. **Fallback format** : `cahier_de_labo.md` ou `JOURNAL.md`. Si les
   deux existent, lire les deux et le signaler dans "anomalies".
2. **Chemins** : normaliser via `realpath` en Phase 0 pour eviter les
   erreurs de persistance en cas d'invocation depuis un autre cwd.
3. **Cahier volumineux** : chunks de 2000 lignes si > 5000, jamais
   tronquer.
4. **BDD absente ou deplacee** : mentionner comme anomalie, ne pas
   bloquer.
5. **Biais reference H37Rv** : rappel automatique dans la section
   "Limites connues" si des analyses SNP sont presentes (golden law
   MTBC).
6. **Collision de fichier** : suffixer `_v2`, `_v3`, jamais ecraser.
7. **`--full` faux positifs** : filtrer strictement (`bdd/`,
   `investigate_phylo/`, etc.).
8. **`mtbc-lineages` absent** : degrader gracieusement, ne pas echouer.
9. **Honnetete** : < 3 pistes haute priorite → sortie courte assumee,
   surtout pas de remplissage. Mais "court" ne veut pas dire "sec" :
   meme un bilan qui conclut "rien a faire" doit etre narratif et
   pedagogue dans sa justification.
10. **Non destructif** : la seule ecriture autorisee est le fichier
    bilan et le repertoire `bilans/`.
11. **Pistes "deduites"** : distinguer clairement les pistes venant du
    cahier (citer la date) de celles deduites de l'inventaire (marquer
    "deduite de l'inventaire").
12. **Projets imbriques** : verifier a la volee la localisation des
    projets animaux (racine vs sous-repertoire), ne rien supposer.
