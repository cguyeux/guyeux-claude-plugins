# Taxonomie des claims scientifiques

Guide de classification et de verification des affirmations dans un article
scientifique, avec exemples du domaine TB/bioinfo.

## Niveaux de priorite

### P1 -- Structurant

**Critere** : le claim fonde l'argumentation principale de l'article.
Si ce claim est faux, la these centrale de l'article s'effondre.

**Ou les trouver** : Abstract, Results (resultats principaux), Conclusion

**Exemples TB/bioinfo** :
- "Notre analyse phylogenomique revele que la lignee L4.10 est associee a
  un taux de MDR significativement plus eleve que les autres sous-lignees L4"
- "Les souches du cluster X partagent une distance SNP mediane de 5,
  compatible avec une transmission recente"
- "La mutation rpoB S450L confere un haut niveau de resistance a la rifampicine
  dans 98% des cas"
- "Le modele de machine learning atteint une AUC de 0.94 pour la prediction
  de resistance a l'INH"

**Strategie de verification** :
- Reproduire le calcul si possible (requete TBannotator, re-execution du script)
- Verifier les chiffres cles dans les sources primaires
- Croiser avec la litterature recente

---

### P2 -- Support

**Critere** : le claim renforce l'argument principal sans le porter seul.
Si faux, l'article est affaibli mais pas invalide.

**Ou les trouver** : Results (resultats secondaires), Discussion (comparaisons)

**Exemples TB/bioinfo** :
- "La sous-lignee L4.1.2 represente 23% des souches de notre echantillon"
- "Le temps de calcul moyen de notre pipeline est de 4h par genome"
- "La concordance entre notre methode et le test phenotypique est de 87%"
- "Les souches isolees en France montrent une diversite genetique plus faible
  que celles d'Afrique de l'Ouest"

**Strategie de verification** :
- Requete BDD pour les statistiques descriptives
- Verification croisee avec d'autres etudes si disponible
- Moindre urgence que P1 mais a ne pas ignorer

---

### P3 -- Contexte

**Critere** : le claim decrit l'etat de l'art ou le contexte general.
Si faux, c'est genant pour la credibilite mais ne change pas les resultats.

**Ou les trouver** : Introduction, debut de Discussion

**Exemples TB/bioinfo** :
- "La tuberculose est la premiere cause de mortalite par un agent infectieux unique"
- "Le WGS est devenu le standard pour le typage des souches MTBC"
- "Environ 10 millions de nouveaux cas de TB sont diagnostiques chaque annee"
- "La lignee L2 (Beijing) est predominante en Asie de l'Est"

**Strategie de verification** :
- WebSearch vers les rapports officiels (WHO, ECDC)
- Verification rapide, pas besoin de reproduire un calcul
- Attention aux chiffres desormais obsoletes (rapports anciens)

---

### P4 -- Annexe

**Critere** : claim peripherique, detail d'illustration ou precision
methodologique mineure. Si faux, c'est une erreur mais sans consequence
sur les conclusions.

**Ou les trouver** : Methods (details techniques), Supplementary, captions

**Exemples TB/bioinfo** :
- "Les sequences ont ete deposees sous l'accession PRJNA123456"
- "Le seuil de qualite de mapping etait fixe a Q30"
- "RAxML a ete execute avec 1000 bootstraps"
- "L'echantillon comprenait 342 genomes"

**Strategie de verification** :
- Verification ponctuelle (le depot existe-t-il ? le chiffre N est-il coherent ?)
- Faible priorite, verifier en dernier

---

## Types de claims et strategies de verification

### Resultat bioinformatique

**Exemples** : distances SNP, topologie d'arbre, clusters de transmission,
taux de resistance par lignee

**Outils** :
- TBannotator MCP : `tool_query_postgres` pour interroger la BDD directement
- Scripts existants dans le repertoire du projet
- Recalcul a partir des donnees brutes si accessibles

**Niveau de preuve requis** : le resultat du recalcul correspond (tolerance
selon le contexte : exact pour un comptage, +-5% pour un pourcentage)

---

### Donnee epidemiologique

**Exemples** : incidence, prevalence, mortalite, repartition geographique

**Outils** :
- WebSearch : WHO Global TB Report (annuel), ECDC surveillance atlas
- WebFetch : pages specifiques des rapports
- TBannotator si les donnees epidemio sont dans la BDD

**Niveau de preuve requis** : le chiffre est coherent avec la source officielle
la plus recente. Tolerer un ecart de 1-2 ans si la source citee est plus
ancienne que le rapport le plus recent.

---

### Affirmation gene/mutation

**Exemples** : association mutation-resistance, frequence d'une mutation,
fonction d'un gene

**Outils** :
- TBannotator : requete sur les mutations et leur association avec la resistance
- WebSearch : WHO catalogue of mutations, CRyPTIC consortium, litterature
- NCBI Gene, UniProt pour les fonctions de genes

**Niveau de preuve requis** : l'association ou la fonction est documentee
dans au moins une source primaire fiable

---

### Claim methodologique

**Exemples** : performance comparee, superiorite d'une methode, gold standard

**Outils** :
- WebSearch + WebFetch : lire le papier original cite
- Verifier que la comparaison est equitable et que les chiffres correspondent

**Niveau de preuve requis** : le papier cite supporte bien l'affirmation.
Attention aux exagerations ("X is the best" vs "X performed well in our test")

---

### Claim de litterature

**Exemples** : "il a ete montre que...", "selon [ref]...", "X et al. ont demontre..."

**Outils** :
- WebSearch du papier cite
- WebFetch de l'abstract ou de la page du papier
- Comparaison entre l'affirmation et le contenu reel du papier

**Niveau de preuve requis** : le papier traite bien du sujet et supporte
l'affirmation. Tolerance moderee (la formulation peut differer).
Tolerance nulle pour les attributions directes ("X a propose Y").

---

### Donnee chiffree

**Exemples** : "42% des souches...", "n=342", "p<0.001", "IC95% [0.87-0.96]"

**Outils** :
- TBannotator si les donnees sont dans la BDD
- Verification dans la source citee
- Recalcul si les donnees brutes sont accessibles

**Niveau de preuve requis** : exact pour les comptages et les p-values.
Tolerance +-2% pour les pourcentages derives de grands echantillons.

---

## Signaux d'alerte

Indicateurs qu'un claim merite une attention particuliere :

- **Chiffre trop rond** : "exactement 50%" → probablement arrondi ou invente
- **Claim sans reference** dans l'introduction : chaque fait devrait etre source
- **Superlatif** : "le premier", "le seul", "le plus grand" → souvent exagere
- **Incoherence interne** : un chiffre dans les Results differe de celui dans
  la Discussion ou l'Abstract
- **Chiffre obsolete** : statistiques WHO de > 3 ans dans un article soumis en 2026
- **Claim copie d'un autre article** : formulation identique a une source →
  verifier que le claim original etait correct
