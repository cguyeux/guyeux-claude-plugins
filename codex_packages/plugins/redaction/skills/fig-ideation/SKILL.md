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

Cas emblématiques, tous vérifiables : `animal_vs_human` porte 21 figures et **aucune ne
nomme un hôte**, sur un article dont le titre porte sur l'adaptation d'hôte ; il n'a non
plus aucune figure de flux de données. Sa part conceptuelle est pourtant de 24 %, au-dessus
du corpus — **le déficit n'est donc pas une question de quantité mais de registres
entièrement absents**, ce qu'une moyenne ne montre jamais.
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

**Piège connu — export PDF/SVG direct d'`ete3`.** Vérifié 2026-09-01 (`nucs_deletion_mutators`,
arbre annoté à 42 feuilles, sans clé API iTOL configurée) : `Tree.render('*.pdf', ...)` **segfault
systématiquement** (PyQt5/QPrinter), reproductible sur un arbre minimal à 2 feuilles ; l'export
SVG fonctionne mais rend des `TextFace`/légendes à une taille démesurée par rapport aux branches
(moteur `QSvgGenerator` non calibré comme le moteur raster). **Seul l'export PNG direct est
fiable** (`t.render('*.png', tree_style=ts, w=..., units="mm", dpi=600)`) ; pour obtenir malgré
tout un PDF, encapsuler ce PNG via Pillow (`Image.save(path, "PDF", resolution=600.0)`) plutôt que
de chercher à réparer le rendu PDF/SVG natif d'ete3. Détail complet et code :
`~/.agents/knowledge/python-patterns.md`, entrée « [2026-09-01] ete3 : l'export PDF/SVG direct
segfault ou déforme les polices ». Si un PDF réellement vectoriel est requis, préférer `itol`
(nécessite une clé API) plutôt que de dépendre du rendu PDF/SVG natif d'ete3.

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
refusent. Le script affiche toujours la licence et écrit `ATTRIBUTION_icons.tex` (fusionné,
jamais écrasé) ; `--libre` ne se contente pas d'écarter, il **cherche dans le même clade une
silhouette libre** et le dit — sur les quatre hôtes du MTBC, les deux images primaires en
CC BY-SA ont été remplacées automatiquement par une CC BY 4.0 et une CC0. **Une icône sans sa ligne d'attribution n'est pas utilisable.**
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

1. **Phase 2, écriture du squelette — le moment nominal, et il vient APRÈS `/narratif`.**
   Le cycle impose déjà, avant toute rédaction, un squelette listant « sections, figures,
   tables, et pour chacune ce qu'elle démontre ». Ce skill *est* l'outil de cette étape :
   il transforme les acquis de `etat_des_decouvertes.md` en plan de figures, chacune
   portant sa charge de preuve. Le faire ici coûte une heure ; le faire en phase 3 coûte
   une réécriture.

   **Les emplacements où une figure est due sont déjà décidés.** `plan_narratif.md`
   (skill `/narratif`) porte les **points de bascule** de l'article, c'est-à-dire les
   deux à quatre endroits où une explication alternative meurt et où la croyance du
   lecteur change. Le nombre de figures du corps égale le nombre de bascules ; ce skill
   dit **quelle** figure remplit chaque emplacement, il ne décide pas combien il en faut.
   Une candidate qui ne sert aucune bascule se justifie en une ligne au registre — les
   cas légitimes sont l'orientation sans laquelle la suite est illisible, le schéma de
   mécanisme, le flux de sélection des données — ou elle part au supplémentaire.
   **Le nombre de figures ne se dérive JAMAIS d'un format de revue** : la revue n'arbitre
   ni l'article, ni le message, ni sa longueur (règle CG 2026-09-09), et se choisit après.
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
| `/fig-ideation triage` | Trie les orphelines de TOUT le dépôt par récupérabilité (`fig_triage.py`). |

`--force` réexamine les figures déjà décidées dans le registre au lieu de les considérer
comme acquises.

---

## Procédure du mode plan

### Étape 0 — Lire la mémoire du projet, avant tout

Comme tout skill de la chaîne. Dans cet ordre : `plan_narratif.md` s'il existe — c'est de
lui que viennent le **message**, recopié tel quel et jamais reformulé, et les **bascules**
qui fixent les emplacements de figures ; `etat_des_decouvertes.md` (l'intrant principal des
figures elles-mêmes, et le seul en phase 2 si aucun plan narratif n'existe encore, auquel
cas signaler que `/narratif` aurait dû précéder) ; le squelette de l'article s'il existe,
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

**Regarder les figures existantes, pas seulement leurs légendes.** Le script classe par
mots-clés de légende ; il ne voit pas ce que la figure porte réellement. Lire chaque image
avec `Read` avant de passer à l'étape 2 : c'est ce qui distingue « il manque une figure qui
montrerait X » de « la figure qui montre X existe mais est illisible », deux diagnostics qui
appellent des actions opposées.

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

**Le balayage est obligatoire même quand il ne rend rien, et un vide est un résultat.**
Sur `animal_vs_human`, la famille T n'a rien rendu — non par oubli, mais parce que le
manuscrit **n'avance aucune date** (aucune occurrence de « years ago », « kya », ni d'âge
de MRCA). Ce vide a servi deux fois : il a écarté une frise candidate, et il a surtout
justifié d'**abandonner** une frise déjà produite qui dormait sur le disque. Un balayage
qui ne rend rien vous dit ce qu'il ne faut pas produire, et parfois ce qu'il faut jeter.

Le même balayage a montré que, sur un article dont le titre porte sur l'adaptation d'hôte,
**aucune des 21 figures ne nommait un hôte**.

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

**`--embed-width-pt` est OBLIGATOIRE dès qu'une figure sera insérée avec `width=\textwidth`
(ou toute fraction) dans un manuscrit plus étroit que sa taille native.** Bug constaté
(`variant_nucs`, fig1_mechanism_verdict, 2026-09-03) : un panneau A + panneau B côte à côte
produit une figure native large (764pt), du texte en `\tiny`/`\scriptsize` (5-7pt source) y
est parfaitement net à 220 DPI — le DPI ne fixe que la résolution des pixels, jamais la
taille angulaire finale. Une fois insérée à `width=\textwidth` dans un article a4 marges
2.5cm (`\textwidth` ≈ 455pt), la figure est réduite d'un facteur ≈0.6 et ce même texte tombe
à 3-4pt effectifs, illisible — défaut resté invisible à plusieurs tours de la boucle native.
Obtenir la largeur cible en pt pour le documentclass/geometry du manuscrit visé :

```
python3 -c "
import subprocess
tex = r'''\documentclass[11pt,a4paper]{article}
\usepackage[margin=2.5cm]{geometry}
\begin{document}\typeout{TEXTWIDTH=\the\textwidth}\end{document}'''
open('/tmp/tw.tex','w').write(tex)
out = subprocess.run(['pdflatex','-interaction=nonstopmode','/tmp/tw.tex'],
                      capture_output=True, text=True, cwd='/tmp').stdout
print([l for l in out.splitlines() if 'TEXTWIDTH' in l][0])
"
```

puis :

```
python3 scripts/tikz_build.py article/figures/fig1.tex --embed-width-pt 455.24 --crops
```

Le script calcule le facteur d'échelle réel, imprime la taille effective (en pt) de chaque
style de police utilisé, échoue (code retour 1) si l'une tombe sous 6pt effectifs (`--min-
effective-pt` pour ajuster), et produit un PNG `*_embedpreview*` qui simule fidèlement le
rendu inséré — c'est **ce PNG-là**, pas le natif, qu'il faut relire avant de conclure qu'une
figure large-format est lisible.

**Piège distinct, constaté immédiatement après le premier correctif (`variant_nucs`,
2026-09-03) : `tikz_build.py` compile TOUJOURS dans `--outdir` (par défaut
`<figure>/_build/`), jamais dans le fichier que le manuscrit inclut réellement
(`article/figures/<nom>.pdf`).** Corriger le `.tex`, relire le PNG `_build/` et lancer `make`
ne suffit PAS : `make` recompile le manuscrit avec l'ANCIEN PDF resté dans `figures/`, et rien
dans la chaîne (ni `make`, ni `pdflatex`) ne signale ce décalage puisque les deux fichiers
existent. Après toute correction validée par la boucle `compiler -> regarder`, copier
explicitement le PDF du dossier de build vers l'emplacement inclus par `\includegraphics`
AVANT de recompiler le manuscrit :

```
cp article/figures/_build/fig1.pdf article/figures/fig1.pdf
```

puis seulement alors relancer `make` et rouvrir la page concernée du `main.pdf` (pas seulement
le PNG isolé) pour confirmer que le changement y apparaît bel et bien.

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

---

## Mode `triage` — que faire des orphelines, projet par projet

`fig_gap_scan.py` rend des FICHIERS jamais inclus. `fig_triage.py` en fait des
FIGURES, puis les trie :

```bash
python3 scripts/fig_triage.py <racine> \
        --gap /tmp/gap_all.json --json /tmp/triage.json
```

**Le compte en fichiers sur-évalue d'environ 40 %.** Un même graphique existe en
`.png`, `.pdf` et `.svg`, parfois dans deux répertoires, et pèse alors cinq
orphelines. Mesuré sur `mtbc/` le 2026-08-31 : **585 fichiers orphelins pour 351
figures distinctes**. Le regroupement par stem est donc la première opération, pas
un raffinement.

Six classes, dans l'ordre où les regarder :

- **CANDIDAT** (164) — un script du projet la produit, ses entrées existent, et
  aucun registre ne l'a déjà tranchée. C'est le gisement, sous réserve de lire le
  registre du projet avant d'agir (voir ci-dessous).
- **INDÉTERMINÉ** (141) — aucun script ne la nomme. Ni régénérable ni datable
  autrement que par son `mtime` ; contient aussi les faux positifs du scan
  (assets de template, logos d'éditeur).
- **REBUT** (11) — un membre de la même famille de noms est plus RÉCENT sur le
  disque, ou une version est déjà incluse dans le manuscrit.
- **OUTILLAGE** (11) — nom de contrôle interne (checklist, validation, guide de
  style) : jamais destinée à un manuscrit.
- **DONNÉE MORTE** (5) — un script la produit, mais son arbre ou son fichier
  d'entrée a disparu.
- **ARBITRÉE** (19) — un registre du projet (`fig_plan.md`, `fig_check.md`,
  `claim_check.md`, `supp_check.md`) a DÉJÀ décidé de son sort. Cette classe
  passe avant toutes les autres : reproposer ce qu'un humain a tranché est
  précisément le travers que ce skill combat.

**Le tri mécanique doit lire les registres, sinon il rouvre des décisions
prises.** Ajouté après l'avoir payé : `SpacerEgalVirus` ressortait avec dix
figures candidates et un manuscrit sans aucune figure, cas d'école du
raccordement facile. Son `fig_check.md`, écrit le 2026-08-12, disait déjà que
ces figures « proviennent de l'ancien cadre 2019-2022 et prédatent le cadre
statistique actuel », donc qu'aucune n'est réutilisable sans régénération. Et le
`fig_plan.md` d'`animal_vs_human` ouvre sa section par la même phrase : « le
premier réflexe, le travail visuel est déjà fait, il suffit de le raccorder, est
faux ici ».

Une décision peut aussi porter sur un LOT sans nommer une seule figure (« les
sept fichiers de `résultats/` prédatent le cadre »). Le mode affiche donc en tête
la liste des projets dont un registre statue en bloc, avant tout classement :
sur `mtbc/`, sept projets sont dans ce cas, dont les deux plus chargés en
orphelines.

**Trois pièges de classement, chacun payé par un faux résultat.** La récence se
lit sur le `mtime`, jamais sur la longueur du nom : `fig2_geographic_enhanced`
était classé périmé au profit de `fig2_geographic_distribution` alors que
« enhanced » était la version suivante. Un `.tex` ne compte comme producteur que
s'il est `standalone` ou `tikz` : un manuscrit qui nomme un stem ne le produit
pas, et le compter donnait « SCITEPRESS ← main.tex », un logo d'éditeur pris pour
une figure régénérable. Enfin une entrée n'est morte que si elle est absente de la
forêt ET du disque, sans quoi une phrase de documentation entre guillemets et un
`partition.nex` d'IQ-TREE passent pour des arbres perdus.

**« DONNÉE MORTE » ne veut pas dire perte.** Vérifié sur les trois figures de
`MTBC-roman-expansion-skyline` qui dépendent d'un `lsd_run1.timetree` absent : le
cahier du projet montre que ce premier run a été remplacé par `iqtree_validated`.
Ces figures appartiennent à une génération de données abandonnée. Lire le cahier
avant d'alerter, toujours.

**Ce que le tri change pour un manuscrit sans figure.** Trois des six manuscrits
rédigés sans aucune figure ont en réalité des figures déjà produites et jamais
raccordées — `SpacerEgalVirus` en a dix, toutes avec un script vivant. Les trois
autres n'ont rien du tout et relèvent bien du mode plan. C'est le même symptôme
pour deux causes opposées, et seul le tri les sépare.

## Modes d'échec connus

- **La figure décorative.** Elle est belle, elle est citée, elle ne démontre rien.
  Détection : impossible d'écrire sa charge de preuve en une phrase falsifiable. Remède :
  couper, ou fusionner avec la figure voisine qui, elle, démontre quelque chose.
- **La figure qui redit la table.** Un barplot de sept valeurs qu'on veut lire au chiffre
  près. Remède : la table, et la place rendue sert une figure conceptuelle.
- **L'idéation qui lit les légendes sans REGARDER les figures.** Une légende dit ce que la
  figure est, rarement tout ce qu'elle porte. Cas vécu sur `animal_vs_human` : une candidate
  « annoter le cladogramme avec les gènes lipidiques par nœud » a été retenue à l'étape 5,
  puis classée sans objet le jour même — la figure les portait déjà, losanges compris, ce
  que sa légende (« schematic cladogram showing the five annotated internal nodes ») ne
  laissait pas deviner. **Regarder chaque figure existante avant l'étape 3**, avec `Read` sur
  le fichier image : c'est le même geste que `/fig-check`, pour un coût de quelques minutes,
  et il évite de proposer ce qui existe. Corollaire : ce qui manquait à cette figure n'était
  pas l'annotation mais la **lisibilité**, un diagnostic qu'aucune lecture de légende ne rend.
- **L'orpheline réintégrée sans enquête.** Le réflexe « le travail visuel est déjà fait,
  il suffit de le raccorder » est faux dans une part des cas : **une figure orpheline est
  orpheline pour une raison, et la raison est parfois qu'elle est fausse.** Cas vécu sur
  `animal_vs_human` : une frise chronologique dormait sur le disque, l'article n'ayant
  aucune figure temporelle ; elle portait un jalon nommé d'après un résultat que le
  `AGENTS.md` or `AGENTS.md or CLAUDE.md fallback` fallback du projet déclare **invalidé**, et une chronologie que le manuscrit n'assume
  nulle part. L'intégrer aurait réintroduit un résultat réfuté dans un manuscrit qui s'en
  était débarrassé. **La première question sur une orpheline n'est jamais « peut-on
  l'intégrer ? » mais « pourquoi ne l'a-t-on pas intégrée ? »** — chercher la réponse dans
  le cahier, le `AGENTS.md` or `AGENTS.md or CLAUDE.md fallback` fallback du projet et le registre des claims avant de décider.
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
- `references/patrons_tikz.md` — six patrons TikZ compilés et inspectés (frise à double
  registre, flux CONSORT, mécanisme IS, avant/après de topologie, tanglegram, saut d'hôte),
  plus les pièges de compilation vécus, dont la liste de contrôle du préambule minimal.
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
