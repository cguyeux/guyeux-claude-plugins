---

name: fig-ideation
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST), peer-reviewed MTBC phylogenomics :
  moteur d'ideation de FIGURES pour un manuscrit. Ne dessine pas ce qu'on lui demande,
  cherche la figure qui MANQUE. Part de l'etat des decouvertes et du manuscrit, detecte
  mecaniquement les figures pendantes, orphelines, muettes et le deficit de registre
  conceptuel, balaie un bestiaire de 25 archetypes (frise a double registre, tanglegram
  hote-pathogene, avant/apres de topologie, flux CONSORT genomique, schema de mecanisme,
  anatomie de locus), auto-challenge chaque candidate (charge de preuve, modele nul, gain
  contre cout), prototype en esquisse jetable puis livre en TikZ vectoriel, et tient le
  registre fig_plan.md. A utiliser a l'entree en phase 2 quand on ecrit le squelette d'un
  article, apres un manuscript-review pour repondre a une objection par un schema, quand un
  article parait austere, quand un mecanisme est decrit en prose sans dessin, ou pour savoir
  quelles figures deja produites dorment sur le disque.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebSearch, WebFetch
---

# fig-ideation — chercher la figure qui manque

> **Règle d'or.** Une figure ne se dessine pas pour illustrer ce que le texte dit. Elle se
> dessine parce que le texte, seul, ne sait pas le porter. Tout le reste est décoration,
> et la décoration se coupe.

Ce skill est le pendant amont de `/fig-check`. `fig-check` part du `main.tex` et vérifie les
figures **présentes** : il ne peut donc, par construction, jamais signaler une figure
**absente**. `manuscript-review` ne le fait pas davantage (sa dimension D8 ne pose que cinq
questions sur les figures existantes). Personne, dans toute la chaîne, ne dit « il manque ici
une figure qui montrerait X ». C'est le trou que ce skill remplit.

## Le diagnostic qui justifie ce skill

Mesuré sur le dépôt `mtbc/` en août 2026, sur 105 manuscrits actifs et un échantillon de
113 figures tirées de 17 manuscrits rédigés :

| Constat | Chiffre |
|---|---|
| Figures qui sont un graphique statistique tiré d'un tableau | **50,4 %** |
| Figures conceptuelles (schéma + pipeline + frise) | **15,9 %** |
| Manuscrits de l'échantillon avec plus d'une figure conceptuelle | **1 sur 17** |
| Manuscrits rédigés (plus de 800 mots) sans aucune figure | **9**, dont un de 6 887 mots déjà soumis |
| Scripts important matplotlib | 354, pour **0** feuille de style partagée |
| Appels `dpi=` respectant la règle des 600 DPI du `AGENTS.md` or `AGENTS.md or CLAUDE.md fallback` fallback | **moins d'un tiers** |

Cas emblématiques, tous vérifiables : `animal_vs_human` porte 21 figures dont 17 arbres,
**aucune carte et aucune frise**, sur un sujet de saut d'hôte animal vers humain.
`SpacerEgalVirus` compte 5 075 mots, zéro figure, et une sous-section intitulée
« An evolutionary sketch » qui décrit en prose un scénario évolutif complet.
`data-quality` décrit quatre portes de contrôle qualité successives et laisse trois lignes
de commentaire LaTeX en guise de cahier des charges de la figure jamais faite.

**Et le défaut symétrique, que personne ne regarde non plus :** `L4.16` a cinq fichiers de
figures sur le disque et zéro dans son manuscrit ; `MTBC-roman-expansion-skyline` a produit
39 images pour un `main.tex` de 182 mots ; `animal_vs_human` a 85 images orphelines et trois
figures incluses que le corps du texte ne cite jamais. Le travail visuel existe souvent
déjà : il n'a simplement jamais rejoint l'article.

## Ce que ce skill ne fait pas

Il **ne produit aucune figure de données**. Il oriente et il spécifie, puis il délègue.

| Besoin | Délégation | Point d'entrée |
|---|---|---|
| Graphique de données aux normes d'une revue | `sci-figure` | `scripts/figstyle.py`, presets Nature/Science/PLOS/Cell |
| Carte | `geo-map` | `-t choropleth\|bubble\|pie\|points\|arcs\|layered` |
| Arbre phylogénétique annoté | `itol` | `scripts/itol_pipeline.py pipeline` |
| Schéma conceptuel vectoriel | patrons de `references/patrons_tikz.md` | TikZ standalone compilé ici |
| Relecture visuelle de la figure produite | `fig-check` | `/fig-check main.tex --force` |
| Slide à partir d'une figure | `slide-design`, `slide-polish` | registres visuels partagés |

**Interdit absolu :** ne jamais réinventer en TikZ ce qu'un skill produit en qualité
publication. Un arbre se fait avec `itol` ou `ete3`, une carte avec `geo-map`, une
distribution avec `sci-figure`. TikZ sert au **conceptuel** : ce qu'aucune donnée ne trace
toute seule.

### Donner un corps aux schémas : iconographie libre

Un schéma fait uniquement de boîtes reste abstrait. Deux sources libres, vectorielles et
citables, outillées par `scripts/sci_icons.py` :

```
python3 scripts/sci_icons.py taxon 9606 9913 9925 9709 --libre
python3 scripts/sci_icons.py search bacteri --category Microbiology
```

**PhyloPic** résout une silhouette d'organisme par **taxid NCBI** — l'icône est donc indexée
sur la même clé que la biologie du projet (9606 humain, 9913 bovin, 9925 caprin, 9709
phocides). **Bioicons** donne 2 800 icônes de biologie et chimie par nom et catégorie. La
conversion se fait en PDF vectoriel par `rsvg-convert`, sans Inkscape.

**Le garde-fou décisif est la licence.** Deux des quatre silhouettes d'hôtes du MTBC sont en
CC BY-SA : un share-alike **contamine la figure, donc l'article**, et plusieurs éditeurs le
refusent. Le script affiche toujours la licence, `--libre` écarte les SA en le disant, et il
écrit `ATTRIBUTION_icons.tex`. **Une icône sans sa ligne d'attribution n'est pas utilisable.**
Détail complet et pièges dans `references/iconographie.md` ; chaîne montée de bout en bout
dans le patron `saut_hote.tex`.

### Outils écartés, et pourquoi (revue faite, pas supposée)

La question « pourquoi pas Inkscape ou draw.io » mérite une réponse tracée, parce que les deux
existent bel et bien côté agent.

| Outil | Existe-t-il ? | Verdict |
|---|---|---|
| **draw.io** | oui, MCP **officiel** (jgraph) plus trois implémentations tierces | **utile en amont seulement.** Son atout réel est le va-et-vient avec l'humain : le `.drawio` est éditable par l'agent *et* à la souris, ce que TikZ n'offre pas. Mais sa typographie ne s'aligne pas sur le manuscrit et son esthétique lit « diagramme d'architecture logicielle ». À proposer comme esquisse quand l'auteur veut participer à l'arbitrage, jamais comme livrable de manuscrit. |
| **Inkscape** | oui, plusieurs MCP communautaires, aucun d'auteur établi | **non requis.** `rsvg-convert` couvre SVG vers PDF et PNG, `pdftocairo` couvre PDF vers SVG. Restent hors de portée la vectorisation de texte en chemins et les filtres SVG complexes : si l'un devient nécessaire, installer le **binaire**, pas un MCP. |
| Skills publics de schémas scientifiques | oui (`sciagent-skills@scientific-schematics`, `@nejm-figure-guide`) | **à lire, pas à installer** : moins de 100 installations, auteur non établi. Leur découpage en cinq familles de schémas recoupe le bestiaire sans rien y ajouter. |
| MCP dédié aux figures | aucun qui apporte davantage | rien à ajouter. |

**Principe général :** un MCP se justifie quand il donne accès à un état distant qu'aucune
commande locale ne rend. Pour dessiner, la commande locale existe déjà et elle est
scriptable, donc reproductible — ce qu'un serveur ne garantit pas.

**Ne pas créer une sixième palette.** Le dépôt en compte déjà cinq divergentes
(`MTBC_PALETTE` et `MTBC_PALETTE_CB` dans `geo-map/scripts/geo_map.py`,
`PALETTE_CATEGORICAL` dans `sci-figure/scripts/figstyle.py`, celle de `slide-design`, celle
d'`itol`). Pour un article MTBC, la référence est `MTBC_PALETTE_CB` ; pour un schéma
conceptuel sans lignées, l'Okabe-Ito réduit des patrons TikZ. Rien d'autre.

## Quand ce skill se déclenche

Trois points d'entrée dans le cycle de `/cycle-projet`, et un quatrième hors cycle.

1. **Phase 2, écriture du squelette — le moment nominal.** Le cycle impose déjà, avant toute
   rédaction, un squelette listant « sections, figures, tables, et pour chacune ce qu'elle
   démontre ». Ce skill *est* l'outil de cette étape : il transforme les acquis de
   `etat_des_decouvertes.md` en plan de figures, chacune portant sa charge de preuve.
   Le faire ici coûte une heure ; le faire en phase 3 coûte une réécriture.
2. **Phase 3, après `/manuscript-review`.** Mode `review` : chaque objection est examinée
   sous l'angle « une figure serait-elle la meilleure réponse ? ». Voir la section dédiée.
3. **Phase 3, quand un tour de `/fig-check` revient propre.** Une figure propre n'est pas une
   figure suffisante. Un `fig_check.md` sans défaut est le bon moment pour demander ce qui
   manque encore.
4. **Hors cycle : quand l'auteur trouve son article austère.** C'est un symptôme fiable, et
   la cause est presque toujours la même : le registre conceptuel est vide.

## Modes

| Invocation | Ce qu'elle fait |
|---|---|
| `/fig-ideation` | Mode plan. Idéation complète depuis l'état et le manuscrit, écrit `fig_plan.md`. |
| `/fig-ideation audit` | Diagnostic seul, sans idéation : pendantes, orphelines, muettes, registre, production. |
| `/fig-ideation review` | Part des objections de `review/` et cherche lesquelles se répondent par une figure. |
| `/fig-ideation build F3` | Passe d'une fiche du plan à un prototype compilé et inspecté. |
| `/fig-ideation <concept>` | Ciblé : « un schéma du mécanisme de délétion médiée par IS6110 ». |

`--force` réexamine les figures déjà décidées dans le registre au lieu de les considérer
comme acquises.

---

## Procédure du mode plan

### Étape 0 — Lire la mémoire du projet, avant tout

Comme tout skill de la chaîne. Dans cet ordre : `etat_des_decouvertes.md` (l'intrant
principal, et le seul en phase 2), le squelette et le message de l'article s'ils existent,
les trois dernières entrées de `cahier_de_labo.md`, `pistes.md`, puis les registres
`fig_check.md`, `claim_check.md`, `review/INDEX.md` s'ils existent. Si `fig_plan.md` existe
déjà, ne rejouer que ce qui n'y est pas décidé, sauf `--force`.

Un registre absent vaut preuve que le contrôle n'a pas eu lieu : ne jamais supposer qu'une
idéation antérieure a eu lieu parce que les figures « ont l'air bien ».

### Étape 1 — Diagnostic mécanique

```
python3 scripts/fig_gap_scan.py <main.tex> --json /tmp/figgap.json
```

Le script rend six mesures qu'aucune lecture linéaire ne donne : figures **pendantes**
(un `\ref{fig:x}` sans figure), **orphelines** (une image produite jamais incluse),
**muettes** (une figure incluse jamais citée), le **registre visuel** comparé au corpus,
les **sections longues sans appel de figure** classées par densité de marqueurs, et un audit
de **production** (dpi, formats, palettes, feuille de style).

Le point clé : chaque famille de marqueurs pointe vers un archétype. Une section dense en
marqueurs de mécanisme appelle un M1, une section dense en dates appelle un T1, une section
dense en filtres et seuils appelle un P1. Un titre de section qui annonce déjà un dessin
(« sketch », « overview », « architecture ») est le signal le plus sûr du corpus.

**Ce que le script rend est une liste de candidats à inspecter, jamais un verdict.** Il
produit des faux positifs et il en produira toujours : lire les sections signalées avant de
conclure. Sur `Rv2438A`, il désigne à juste titre la section de l'architecture du locus ; il
désigne aussi « Relation to previous work », qui n'appelle rien.

### Étape 2 — Extraire les charges de preuve

Reprendre chaque acquis de la section 2 de `etat_des_decouvertes.md` (ou chaque claim
structurant de `claim_check.md`) et écrire, pour chacun, **la phrase falsifiable qu'il
affirme**. Puis marquer comment cette phrase est portée aujourd'hui : par une figure, par une
table, ou par la seule prose.

**Un acquis structurant porté par la seule prose est une figure candidate.** C'est la
règle la plus productive de tout le skill, et elle est mécanique.

### Étape 3 — Balayer les sept registres, systématiquement

Ne pas se contenter des candidates que l'étape 2 a rendues : elles reproduisent le biais du
manuscrit. Parcourir le bestiaire (`references/bestiaire.md`, 25 archétypes en 7 familles) et
poser pour **chaque famille** la question : *quelle serait la version de cet article ?*

| Famille | La question à se poser |
|---|---|
| **M** mécanisme | Quel processus l'article explique-t-il, dont l'observation n'est que la trace ? |
| **T** temps | Quelles dates l'article avance-t-il, et contre quelle chronologie externe ? |
| **G** géographie | Quelle affirmation de l'article dépend d'un lieu ? |
| **P** procédure | Comment passe-t-on des données publiques au jeu analysé ? |
| **C** contribution | Que croyait-on avant, et qu'est-ce qui change ? |
| **D** données structurées | Quelle matrice, quel appariement, quelle correspondance ? |
| **S** structure | Quel locus, quelle protéine, quelle architecture ? |

Le balayage est obligatoire même quand il ne rend rien : c'est lui qui a montré que
`animal_vs_human` n'a ni carte ni frise sur un sujet de saut d'hôte.

### Étape 4 — Le test du lecteur pressé

Lire **uniquement** les figures et leurs légendes, dans l'ordre, en ignorant le corps du
texte. Écrire ce qu'on comprend. Comparer au message de l'article.

**Là où la compréhension casse, il manque une figure**, et son emplacement est celui de la
rupture. Ce test est le plus fiable des quatre parce qu'il reproduit exactement le
comportement d'un relecteur et d'un lecteur réels.

Variante en phase 2, quand aucune figure n'existe encore : lire le squelette et les charges
de preuve de l'étape 2 dans l'ordre, et repérer où le raisonnement demande une image.

### Étape 5 — Auto-challenge de chaque candidate

Aucune candidate ne survit sans passer les quatre questions, dans cet ordre. Elles sont la
transposition aux figures de la discipline de `/challenge`.

1. **Charge de preuve.** Quelle phrase falsifiable cette figure démontre-t-elle ? Si elle ne
   tient pas en une phrase, la figure porte deux figures, ou n'en porte aucune.
2. **Contre-argument le plus fort.** Un tableau ferait-il mieux ? Si la figure ne fait que
   ranger des nombres qu'on voudra lire un par un, c'est une table. Si le lecteur doit
   comparer des formes, des ordres ou des voisinages, c'est une figure.
3. **Modèle nul.** À quoi ressemblerait cette figure si l'effet n'existait pas ? Une figure
   dont la version « sans effet » est indiscernable de la version publiée ne démontre rien.
   Une frise sans intervalle de crédibilité, un tanglegram sans test de congruence, une carte
   sans dénominateur en sont les trois cas les plus fréquents.
4. **Gain contre coût.** Qu'apporte-t-elle qu'aucune autre figure du plan n'apporte déjà ?
   Combien coûte-t-elle, sachant qu'un TikZ conceptuel demande deux à quatre tours de
   compilation et d'inspection ?

Deux vérifications de robustesse s'ajoutent avant de retenir une candidate : la figure
survit-elle **en noir et blanc** (donc l'information ne passe pas par la seule teinte), et
survit-elle à **86 mm de large** (la colonne simple de la plupart des revues) ?

Journaliser les candidates **rejetées** avec leur raison, dans le registre. Une candidate
tuée proprement ne revient pas à chaque passage.

### Étape 6 — Esquisser avant de s'engager

Une figure conceptuelle se tranche sur une esquisse jetable, pas sur une discussion.

**Esquisse (minutes, jetable).** Mermaid pour un flux, un arbre de décision, une séquence ;
Graphviz `dot` quand il n'y a pas de réseau, il est installé localement. L'esquisse sert à
**arbitrer entre deux structures**, jamais à être livrée.

**Livrable (heures, versionné).** TikZ standalone compilé en PDF vectoriel, dans
`article/figures/<nom>.tex`. Motifs : la police suit celle du manuscrit, le vectoriel passe
toutes les limites de revue, le code se relit et se corrige, et la figure se régénère.
Le dépôt n'a **aucun** outil de dessin vectoriel installé (ni Inkscape, ni draw.io) : TikZ
n'est pas une préférence, c'est la seule voie éditable disponible.

Anti-patron mesuré dans le dépôt : 25 scripts détournent matplotlib en outil de dessin
(`FancyBboxPatch` plus `FancyArrowPatch`) pour produire des schémas. Cela fonctionne mais ne
se maintient pas, et le savoir-faire n'a jamais été réutilisé au-delà des quatre projets qui
l'ont écrit.

**La boucle de production, qui n'est pas négociable :**

```
compiler -> rastériser -> REGARDER -> corriger -> recompiler -> REGARDER ENCORE
```

```
python3 scripts/tikz_build.py article/figures/fig1.tex --dpi 220 --crops
```

Le script compile en `-halt-on-error`, rastérise, et découpe les zones denses. Une correction
de figure n'est **acquise qu'après ré-inspection** : chaque déplacement d'élément libère une
zone et en occupe une autre. Deux tours sont la norme, pas l'exception. Les patrons livrés
avec ce skill ont tous demandé au moins une correction après la première lecture visuelle.

### Étape 7 — Inscrire

Écrire `fig_plan.md` à la racine du projet (format dans `references/registre.md`), une fiche
par figure retenue et une ligne par candidate rejetée. Puis sérialiser dans `pistes.md` :
une sous-piste par figure à produire, rattachée à la piste majeure de l'article.

Enfin, ajouter une entrée au cahier via `/cahier-de-labo update`, y compris si aucune figure
n'a encore été produite : une idéation est une production de connaissance.

---

## Mode `review` — répondre à une objection par une figure

Une part importante des objections de relecture ne demande pas une analyse de plus, mais une
**figure de plus**. Le relecteur ne dit presque jamais « faites une figure » : il dit qu'il
ne comprend pas, qu'il n'est pas convaincu, ou que la méthode n'est pas reproductible.

Lire `review/*.md` et `review/INDEX.md`, puis classer chaque remarque avec cette table.

| Formulation du relecteur | Archétype de réponse |
|---|---|
| « la méthode est difficile à suivre », « je n'ai pas pu reproduire » | **P1** flux CONSORT génomique |
| « combien de génomes exactement, et lesquels ont été écartés ? » | **P1**, avec les exclusions chiffrées et motivées |
| « en quoi cela diffère de [travail antérieur] ? » | **C1** avant/après |
| « la nouveauté n'est pas claire » | **C1**, ou **C2** figure-thèse |
| « le mécanisme proposé n'est pas étayé » | **M1**, avec l'encart de ce que la donnée ne tranche pas |
| « la datation n'est pas convaincante » | **T1** avec HPD tracés, **T2** calibration |
| « quel est le lien avec l'histoire humaine ? » | **T1** à double registre |
| « la co-divergence pourrait être un artefact géographique » | **D3** tanglegram avec test et Mantel partiel |
| « les résultats ne sont pas généralisables » | **G1** carte des origines, avec dénominateurs |
| « pourquoi ces seuils ? » | **P2** arbre de décision avec les valeurs aux arêtes |
| « la figure X est illisible » | ce n'est pas ce skill : c'est `/fig-check --fix` |

Attention au piège central de ce mode : **une figure n'est une réponse que si l'objection
porte sur la lisibilité de l'argument, pas sur sa validité.** Un relecteur qui doute d'un
résultat veut une analyse, pas un dessin. Dessiner un argument faux le rend seulement plus
visible. Quand le doute est de fond, la piste ouverte est une piste d'analyse, avec la
discipline de phase 1, et la figure vient après.

Le résultat de ce mode s'écrit dans `fig_plan.md` **et** se rattache à la remarque dans
`review/INDEX.md`, pour que `/reviewer-response` sache que la réponse existe.

---

## Modes d'échec connus

- **La figure décorative.** Elle est belle, elle est citée, elle ne démontre rien.
  Détection : impossible d'écrire sa charge de preuve en une phrase falsifiable. Remède :
  couper, ou fusionner avec la figure voisine qui, elle, démontre quelque chose.
- **La figure qui redit la table.** Un barplot de sept valeurs qu'on veut lire au chiffre
  près. Remède : la table, et la place rendue sert une figure conceptuelle.
- **Le schéma qui affirme plus que les données.** Une flèche entre deux boîtes est une
  affirmation causale. Un connecteur de frise entre un événement humain et un événement
  pathogène affirme une co-occurrence. Remède : ne tracer que ce qui est testé quelque part
  dans l'article, et tracer les intervalles.
- **L'échelle non linéaire silencieuse.** Une frise qui comprime le passé profond sans marque
  de rupture visible est une faute de lecture, pas une commodité.
- **Le top-N silencieux.** Un `[:8]` dans le script de tracé fait disparaître des catégories
  que le texte nomme explicitement. Vérifier tout slicing dans le script source.
- **La correction non ré-inspectée.** Le mode d'échec le plus fréquent du polissage : une
  légende déplacée pour libérer des barres vient masquer un label ailleurs.
- **La sixième palette.** Résister à l'envie d'un jeu de couleurs propre au projet.
- **L'idéation sans registre.** Une idéation dont il ne reste pas de `fig_plan.md` sera
  refaite intégralement au passage suivant, avec d'autres conclusions.

## Références

- `references/bestiaire.md` — les 25 archétypes en 7 familles : ce que chacun démontre, quand
  il s'impose, sa déclinaison MTBC, son outil, son piège propre.
- `references/patrons_tikz.md` — cinq patrons TikZ compilés et inspectés (frise à double
  registre, flux CONSORT, mécanisme IS, avant/après de topologie, tanglegram), plus les
  pièges de compilation vécus.
- `references/iconographie.md` — PhyloPic et Bioicons, résolution par taxid NCBI, chaîne
  SVG vers PDF vectoriel sans Inkscape, piège de la teinte, et le garde-fou de licence
  share-alike qui peut coûter une soumission.
- `references/registre.md` — format de `fig_plan.md`, et la fiche de spécification d'une
  figure.
- Hors de ce skill : `~/.claude/knowledge/tikz-beamer-patterns.md` (antipatterns TikZ
  structurels, pièges `\def` et macros à chiffres), `~/.claude/knowledge/figures-publication-inspection.md`
  (défauts matplotlib récurrents, méthode de recadrage), et
  `bio_pathogens/skills/mtbc-bilan/references/figures_et_visuels.md` (table de routage
  figure vers skill, règles de qualité).

## Codex workflow guardrail

This packaged copy imports a Claude-origin project workflow into Codex. Before writing project registers, moving BDD files, changing Atlas content, appending remote queues, archiving a project, or launching remote compute, require an explicit user request in the current turn. Use recoverable operations only, keep project provenance boundaries, and follow the global rule that files are moved to the trash rather than permanently deleted.

## Codex MCP note

MCP tool names in `allowed-tools` are prerequisites. Verify them with `codex mcp list` before relying on live queries.
