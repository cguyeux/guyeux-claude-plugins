# Mode `--deepen` -- corps integral de l'ancien skill `mtbc-deepen`

Ce fichier conserve, sans coupe, le texte de l'ancien skill autonome
`mtbc-deepen`, fusionne dans `mtbc-bilan` le 2026-07-30 sous forme du mode
`--deepen`. Le SKILL.md porte le deroulé operationnel ; on lit ici le detail :
grille de scoring a cinq dimensions, gabarit du rapport d'approfondissement,
points de vigilance propres au mode, format du resume console.

Les references a `/mtbc-deepen` dans le texte ci-dessous se lisent desormais
`/mtbc-bilan --deepen`. La Phase 1 (bilan) y est decrite comme une etape
externe : dans le skill fusionne, elle correspond simplement aux Phases 0 a 7.

---

# /mtbc-deepen -- Approfondissement systematique d'une etude MTBC

Pour un projet MTBC donne, produit une analyse complete de son etat et
de son potentiel d'approfondissement. Le skill orchestre quatre phases
sequentielles, chacune alimentant la suivante, et aboutit a une
**decision argumentee** : poursuivre (avec des pistes concretes) ou
clore (avec une justification honnete).

**Principe cardinal : la conclusion "rien de plus a faire" est un
resultat valide et souhaitable.** Ne jamais inventer des pistes pour
justifier la poursuite d'un projet epuise. Un projet clos proprement
a plus de valeur qu'un projet maintenu artificiellement en vie.

**Contextes d'invocation typiques** : chercher de nouvelles directions pour
un projet qui stagne ; reprendre une etude apres une pause ; decider si un
projet merite encore du temps ; preparer la suite apres une phase d'analyse
terminee ; faire le point complet avant une reunion.

---

> [!NOTE]
> **Frontiere bilan / deepen / reboot (3 skills voisins, ne pas confondre).**
> `mtbc-bilan` PHOTOGRAPHIE l'etat su (lecture seule, consolidation, plan d'action) ;
> `mtbc-deepen` (ce skill) EXPLORE de nouvelles pistes quand un projet stagne (il
> commence par un bilan, puis lit-review elargie + inventaire des skills non mobilises) ;
> `mtbc-reboot` REPART a zero proprement quand la derive est trop forte (archive taggee
> VERIFIE / A VERIFIER / REFUTE + re-analyse claim par claim, operation destructrice).
> Regle : photographier -> explorer -> repartir.

## Prealable -- Resolution et chargement du contexte

1. **Resoudre le repertoire projet** :
   - Si argument fourni : chemin absolu ou nom relatif a
     `~/docs/codes/mtbc/`
   - Sinon : utiliser `pwd`
   - Normaliser via `realpath`
   - Verifier que le repertoire contient au moins 2 marqueurs de projet
     MTBC (`CLAUDE.md`, `cahier_de_labo.md`, `JOURNAL.md`, `article/`,
     `analyses/`). Sinon : abandon propre.

2. **Consultation memoire** (avant toute action) :
   - Lire `<projet>/CLAUDE.md` et `<projet>/cahier_de_labo.md` (ou
     `JOURNAL.md`)
   - Consulter `~/.claude/knowledge/tuberculosis.md` si present
   - Consulter le skill `mtbc-lineages` pour la golden law
   - Si un bilan recent existe dans `<projet>/bilans/` (< 7 jours) :
     le lire et le resumer au lieu de relancer un bilan complet

3. **Afficher le contexte** :

```
=== mtbc-deepen : [nom projet] ===
Lignee       : [...]
Chemin       : [...]
Cahier       : [N entrees, derniere le YYYY-MM-DD]
Dernier bilan: [YYYY-MM-DD ou "aucun"]
Article      : [statut]
```

---

## Phase 1 -- Bilan de l'etat du projet

Executer l'equivalent de `/mtbc-bilan` sur le projet. Si un bilan de
moins de 7 jours existe dans `<projet>/bilans/`, le relire et en
extraire les informations sans relancer l'analyse complete.

**Objectif** : obtenir une photographie factuelle de l'etat actuel.

### Ce qu'on extrait du bilan

- **Decouvertes cumulees** : liste datee depuis le cahier
- **Donnees produites** : souches en BDD, figures, scripts par phase
- **Etat du manuscrit** : sections, claims, reviews
- **Pistes ouvertes** : issues du cahier, avec leur score (valeur,
  faisabilite, cout)
- **Anomalies** : phases incompletes, donnees manquantes, cahier muet
- **Verdict bilan** : bouclee (X/6 criteres) ou a poursuivre

### Affichage intermediaire

```
Phase 1/4 : Bilan
  Verdict       : a poursuivre (4/6 criteres)
  Decouvertes   : 8 cumulees
  Pistes ouvertes: 5 (dont 2 haute priorite)
  Anomalies     : 1 (phase 3 sans script de datation)
```

Ne pas afficher le bilan complet ici -- il sera integre dans la
synthese finale.

---

## Phase 2 -- Revue de litterature elargie

Executer l'equivalent de `/lit-review <sujet> --wide` sur le sujet
principal du projet. Pour le sondage rapide du corpus, s'appuyer en
priorite sur `tbmonitor-papers` (corpus PubMed TB pre-indexe, ~190k
papiers, reponse sub-seconde) avant de basculer sur les recherches live.

### Determination du sujet

Le sujet de la lit-review est derive automatiquement :
1. Du titre du projet dans `CLAUDE.md`
2. De la lignee etudiee
3. Des mots-cles du cahier (extraire les termes recurrents)

Formuler le sujet comme une requete de recherche, pas comme un titre
de projet. Exemples :
- Projet "L4.9" → sujet : "Mycobacterium tuberculosis lineage 4.9
  phylogeography evolution"
- Projet "animal_vs_human" → sujet : "MTBC animal lineages human
  transmission cross-species"

### Ce qu'on cherche specifiquement

La lit-review en mode `--wide` cherche :
1. **Articles recents** (depuis la derniere lit-review, ou depuis
   la creation du projet si aucune n'a ete faite) sur le sujet
2. **Travaux precurseurs** : via la recherche pre-nomenclature de
   `--wide`, trouver les articles qui decrivaient le phenomene
   avant qu'il soit nomme
3. **Backward chaining** : scanner les references des articles
   fondateurs et des articles cles du projet
4. **Convergences** : articles qui connectent le sujet du projet
   a d'autres lignees ou d'autres approches methodologiques

### Interaction avec la litterature existante

- Si `litterature_review/` existe deja : mode approfondissement
  (enrichir, pas repartir de zero)
- Si absent : mode creation (nouvelle lit-review)
- Dans les deux cas, le mode `--wide` est force

### Affichage intermediaire

```
Phase 2/4 : Litterature (mode wide)
  Sujet         : "M. tuberculosis L4.9 phylogeography SNP markers"
  Mode          : approfondissement (derniere exploration : 2026-03-28)
  Nouvelles refs: 12 (dont 4 haute pertinence)
  Pre-nomenclature: 3 articles precurseurs retrouves
  Backward scan : 2 refs nouvelles depuis articles fondateurs
  Lacunes       : 2 identifiees
```

---

## Phase 3 -- Inventaire des skills et methodes non mobilises

C'est la phase la plus originale de ce skill. L'objectif est de
confronter les capacites analytiques disponibles (via les skills du
plugin bio/) avec ce qui a ete effectivement fait dans le projet,
pour identifier les **angles morts methodologiques**.

### Etapes

1. **Lister les skills des plugins bio** (scindes en deux depuis) :
   ```bash
   ls ~/docs/codes/claude_plugins/bio_pathogens/skills/ \
      ~/docs/codes/claude_plugins/bio_population_genetics/skills/
   ```

2. **Classifier chaque skill par domaine** (utiliser la description
   du skill, pas son nom) :
   - Phylogenie / datation
   - Structure de population / clustering
   - Annotation / evolution moleculaire
   - Epidemiologie / phenotype / resistance
   - Phylogeographie / cartes
   - Coevolution / contexte historique
   - Bases de donnees / queries
   - Litterature / manuscrit
   - Visualisation

3. **Pour chaque skill d'analyse** (exclure les skills de manuscrit
   et de BDD qui sont des outils, pas des methodes) :
   - Lire le frontmatter (description) du SKILL.md
   - Determiner si la methode correspondante a ete utilisee dans le
     projet : chercher des traces dans le cahier, les scripts, les
     resultats
   - Classer en :
     - **Utilise** : methode clairement appliquee (script, resultat,
       mention dans le cahier)
     - **Pertinent non utilise** : la methode serait applicable aux
       donnees du projet mais n'a jamais ete lancee
     - **Non pertinent** : la methode ne s'applique pas a ce projet
       (ex : bovine-genomics pour un projet L4 humain)

4. **Pour chaque skill "pertinent non utilise"**, evaluer :
   - **Ce qu'il apporterait** : quelle question scientifique il
     pourrait aider a resoudre
   - **Ce qu'il faudrait** : donnees necessaires (disponibles ou non),
     prerequis (arbre, matrice, etc.)
   - **Effort estime** : rapide (< 1h), modere (1-4h), lourd (> 4h)

### Affichage intermediaire

```
Phase 3/4 : Inventaire des methodes
  Skills analyses disponibles : 42
  Utilises dans ce projet     : 8
  Pertinents non utilises     : 6
  Non pertinents              : 28

  Methodes non exploitees :
    - /bayesian-skyline   : demographie Ne(t), arbre date requis
    - /convergent-evolution: mutations paralleles, matrice SPDI requise
    - /coevolution        : tests Mantel/PACo, donnees humaines requises
    - /thd                : succes epidemique, arbre date requis
    - /mk-ascertainment   : selection, SPDI par tier requis
    - /ancestral-reconstruction : etats ancestraux, arbre + metadata requis
```

---

## Phase 4 -- Synthese et decision

C'est la phase ou tout converge. Les trois phases precedentes
alimentent une reflexion structuree qui aboutit a une decision claire.

### 4.1 Croisement des sources

Construire un tableau croisant :
- Pistes du bilan (Phase 1)
- Lacunes de la litterature (Phase 2)
- Methodes non exploitees (Phase 3)

Chercher les **convergences** : une piste du bilan qui correspond a
une lacune de la litterature ET peut etre addressee par un skill
disponible = **piste forte**. Inversement, une piste isolee (pas de
support litteraire, pas de methode disponible) = **piste faible**.

### 4.2 Hierarchisation des pistes

Pour chaque piste (issue du bilan, de la litterature, ou de
l'inventaire des skills), scorer sur 5 dimensions :

| Dimension | 0 | 1 | 2 | 3 |
|-----------|---|---|---|---|
| **Valeur scientifique** | Anecdotique | Utile | Significatif | Potentiellement majeur |
| **Soutien litteraire** | Aucun precedent | Quelques refs tangentielles | Refs directes existent | Lacune identifiee dans la litt. |
| **Faisabilite technique** | Donnees absentes | Donnees partielles | Donnees presentes, effort modere | Pret a lancer |
| **Originalite** | Deja fait par d'autres | Approche classique | Angle peu explore | Premiere etude a le faire |
| **Synergie** | Isole | Lien avec 1 autre piste | Renforce le manuscrit | Transforme les conclusions |

**Score final** = moyenne ponderee :
`(valeur×3 + soutien×2 + faisabilite×2 + originalite×2 + synergie×1) / 10`

- **Haute priorite** : score >= 2.0
- **Moyenne** : 1.0 -- 2.0
- **Basse** : < 1.0

### 4.3 Decision

Appliquer la grille de decision suivante :

**Verdict "CLORE"** si au moins 3 de ces conditions sont vraies :
- Le bilan donne un verdict bouclee (>= 4/6 criteres de cloture)
- La litterature ne revele aucune lacune exploitable avec les donnees
  existantes
- Aucune piste ne depasse un score de 1.5
- L'article est soumis/accepte/publie
- Toutes les methodes pertinentes ont deja ete explorees

**Verdict "APPROFONDIR"** sinon, en precisant :
- Les pistes haute priorite classees par score
- Pour chaque piste : la commande skill exacte a lancer, les
  prerequis, et le resultat attendu

**Verdict "PIVOTER"** si :
- Le projet est a un stade precoce (< 3 phases d'analyse)
- La litterature revele que la question initiale est mal posee ou
  deja resolue
- Une piste completement differente emerge avec un score tres
  superieur aux pistes du projet actuel

### 4.4 Redaction du rapport

Ecrire le rapport dans `<projet>/bilans/YYYY-MM-DD_deepen.md` :

```markdown
# Approfondissement -- [nom projet] -- YYYY-MM-DD

## Verdict

> **[CLORE | APPROFONDIR | PIVOTER]**
> [Justification en 2-3 phrases]

## 1. Bilan resumé

[Resume des points cles du bilan -- 10 lignes max. Renvoyer au
fichier bilan complet si genere.]

- Decouvertes cumulees : N
- Pistes ouvertes (bilan) : M
- Etat manuscrit : [...]
- Criteres cloture : X/6

## 2. Litterature -- nouveautes et lacunes

### Articles nouveaux pertinents

| # | Ref | Annee | Pertinence | Apport |
|---|-----|-------|------------|--------|
| 1 | @auteur2026x | 2026 | Haute | [...] |

### Travaux precurseurs decouverts (mode wide)

[Articles retrouves via pre-nomenclature ou backward chaining,
avec explication de pourquoi ils etaient invisibles par
recherche standard]

### Lacunes identifiees

- [Lacune 1 : ce que la litterature ne couvre pas encore]
- [Lacune 2 : ...]

## 3. Methodes non exploitees

| Skill | Methode | Apport potentiel | Prerequis | Effort |
|-------|---------|------------------|-----------|--------|
| /bayesian-skyline | Demographie Ne(t) | Dynamique pop. | arbre date | modere |
| /convergent-evolution | Mutations paralleles | Selection | matrice SPDI | rapide |

## 4. Pistes d'approfondissement

### Haute priorite (score >= 2.0)

1. **[Titre piste]** -- score X.X
   - Source : [bilan | litterature | inventaire skills | convergence]
   - Valeur : X/3, Soutien litt. : X/3, Faisabilite : X/3,
     Originalite : X/3, Synergie : X/3
   - Commande : `/<skill> <args>`
   - Prerequis : [...]
   - Resultat attendu : [...]

### Moyenne priorite (1.0 -- 2.0)

[...]

### Basse priorite (< 1.0) -- mention uniquement

- [...]

## 5. Plan d'action suggere

[Si verdict APPROFONDIR : sequencer les pistes haute priorite
dans un ordre logique, en identifiant les dependances.]

1. D'abord : `/<skill1>` (prerequis pour les suivantes)
2. Ensuite : `/<skill2>` (exploite les resultats de 1)
3. En parallele : `/<skill3>` (independant)
4. Dernier : mettre a jour le manuscrit

[Si verdict CLORE :]

1. Verifier le manuscrit : `/claim-check`, `/bib-check`
2. Nettoyer : `/deai-latex`
3. Review finale : `/manuscript-review`
4. Archiver le projet

[Si verdict PIVOTER :]

1. Documenter pourquoi la direction initiale est abandonnee
2. Reformuler la question de recherche
3. Nouvelle lit-review sur le sujet reformule
4. Relancer les analyses dans la nouvelle direction

## 6. Convergences inter-projets

[Projets MTBC voisins qui partagent des donnees, des methodes,
ou des questions avec ce projet. Possibilites de mutualisation.]
```

---

## Points de vigilance

1. **Ne pas relancer un bilan si un recent existe** : lire le bilan
   de < 7 jours au lieu de refaire le travail.
2. **Ne pas inventer de pistes** : si rien ne justifie d'approfondir,
   le dire. Trois pistes mediocres valent moins qu'un verdict honnete
   de cloture.
3. **Distinguer les sources** : chaque piste doit etre tracee a sa
   source (bilan, litterature, inventaire skills, ou convergence).
4. **Ne pas executer les analyses** : le skill suggere, il n'execute
   pas. Les commandes sont des suggestions, pas des actions.
5. **Scorer honnetement** : un score de faisabilite 3 ("pret a lancer")
   implique que les donnees sont effectivement presentes et le script
   existe ou est trivial. Ne pas surestimer.
6. **Pre-nomenclature** : rappeler explicitement quand un article a
   ete retrouve grace au mode wide, et expliquer pourquoi il etait
   invisible par mots-cles.
7. **Budget lit-review** : en mode deepen, la lit-review est limitee
   a une session (pas de relances multiples). Si le sujet necessite
   un approfondissement massif, le suggerer comme piste plutot que
   de le faire en ligne.
8. **Cahier volumineux** : ne pas tronquer. Lire par chunks si > 5000
   lignes.
9. **Mode `--full` de mtbc-bilan** : ne PAS l'utiliser ici. Le deepen
   est par projet, pas global. Les convergences inter-projets sont
   gerees en Phase 4 de maniere legere.

---

## Epilogue -- Resume et prochaine etape

Afficher en console :

```
=== mtbc-deepen termine ===

Projet    : [nom]
Lignee    : [...]
Verdict   : [CLORE | APPROFONDIR | PIVOTER]

Bilan     : [X/6 criteres, N decouvertes, M pistes ouvertes]
Litterature: [N nouvelles refs, P precurseurs, L lacunes]
Methodes  : [N pertinentes non utilisees sur M disponibles]

[Si APPROFONDIR :]
Top 3 pistes :
  1. [titre] (score X.X) → /<skill>
  2. [titre] (score X.X) → /<skill>
  3. [titre] (score X.X) → /<skill>

Prochaine commande suggeree : /<skill> <args>

[Si CLORE :]
Prochaines commandes :
  1. /claim-check → verifier les claims
  2. /manuscript-review → review finale
  3. Archiver le projet

[Si PIVOTER :]
Direction suggeree : [...]
Prochaine commande : /lit-review "[nouveau sujet]" --wide

Rapport complet : <chemin>/bilans/YYYY-MM-DD_deepen.md
```

Suggestion de suite :
- `/cahier-de-labo update` si le deepen a produit des connaissances
- La commande suggeree pour la premiere piste haute priorite
- `/mtbc-bilan --full` pour remettre en perspective globale
