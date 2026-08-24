# Bestiaire des figures — 25 archétypes en 7 familles

Catalogue de référence du skill `fig-ideation`. Chaque entrée porte cinq champs :
**démontre** (la charge de preuve type), **s'impose quand**, **déclinaison MTBC**,
**outil**, **piège propre**.

Le balayage des sept familles est obligatoire à l'étape 3 du mode plan, y compris pour les
familles qui ne rendent rien : c'est l'absence de réponse qui est informative. Un article de
phylogéographie sans réponse à la famille G, ou un article de datation sans réponse à la
famille T, a un problème de figures avant d'avoir un problème de rédaction.

Rappel de routage : les familles D, G et une partie de T se produisent avec `sci-figure`,
`geo-map` et `itol`. Les familles M, P, C, S et la frise T1 se produisent en TikZ, parce
qu'aucune donnée ne les trace toute seule.

---

## Famille M — mécanisme : le processus dont l'observation n'est que la trace

C'est la famille la plus absente des manuscrits du dépôt, et la plus rentable. Un article de
génomique comparative observe des états ; le lecteur veut la cause. La distance entre
« il y a une délétion » et « voici comment une délétion apparaît » est exactement la distance
entre un rapport et un article.

### M1 — Schéma de mécanisme moléculaire, en états successifs
- **Démontre** : que l'observation est la conséquence prévisible d'un processus connu.
- **S'impose quand** : le texte contient « leads to », « results in », « gives rise to »,
  « scenario », « sketch », ou décrit une suite d'événements moléculaires en prose.
- **Déclinaison MTBC** : délétion médiée par recombinaison entre deux copies d'IS6110 en
  orientation directe (le patron livré) ; perte de spacers CRISPR par recombinaison entre
  répétitions directes ; pseudogénisation par décalage du cadre de lecture ; acquisition puis
  décroissance d'un bloc *cas*.
- **Outil** : TikZ, patron `mecanisme_is_deletion`.
- **Piège** : une flèche entre deux états est une affirmation causale. Ajouter systématiquement
  l'encart **« ce que la donnée seule ne tranche pas »** : c'est ce qui distingue un schéma
  scientifique d'une vignette de manuel.

### M2 — Schéma du biais méthodologique
- **Démontre** : qu'une limite reconnue de la méthode produit un artefact d'une direction
  et d'une amplitude prévisibles.
- **S'impose quand** : la section « limitations » décrit un biais en prose, ou quand un
  relecteur soupçonne un artefact.
- **Déclinaison MTBC** : le biais de référence H37Rv. Trois bandes de génome (L4, L2, une
  lignée animale) alignées sur la référence, avec les régions de couverture perdue et le
  compte de variants qui en résulte. Une figure qui explique pourquoi les lignées non-L4
  paraissent moins diverses.
- **Outil** : TikZ, ou `sci-figure` si la couverture réelle est tracée.
- **Piège** : montrer le biais sans le quantifier le transforme en excuse. Chiffrer la perte.

### M3 — Paysage d'aptitude et évolution compensatoire
- **Démontre** : qu'une mutation coûteuse est rattrapée par une seconde, et que le couple est
  plus apte que la première seule.
- **S'impose quand** : l'article parle de compensation, de coût de la résistance, ou de
  transmissibilité de clones résistants.
- **Déclinaison MTBC** : *rpoB* dans la RRDR puis *rpoC* ; *katG* S315T puis *ahpC*. Trois
  états sur un axe d'aptitude, avec les effectifs observés de chaque combinaison et le test
  de Mantel-Haenszel stratifié par lignée.
- **Outil** : TikZ pour le paysage, `sci-figure` pour les effectifs, en panneaux.
- **Piège** : l'axe d'aptitude est presque toujours qualitatif. Le dire dans la légende plutôt
  que de graduer un axe qu'on n'a pas mesuré.

### M4 — Écologie du saut d'hôte
- **Démontre** : la direction et la répétition des transferts entre hôtes.
- **S'impose quand** : l'article compare des écotypes, ou parle de zoonose et de
  ré-humanisation.
- **Déclinaison MTBC** : graphe dirigé humain, bovin, caprin, phoque, avec la phylogénie en
  fond et les flèches placées sur les branches où le changement d'hôte est inféré. La
  ré-humanisation secondaire de L6 et L9 se lit alors d'un coup.
- **Outil** : `itol` pour l'arbre, TikZ pour la surcouche des flèches, patron `saut_hote.tex`.
  Les silhouettes d'hôtes viennent de PhyloPic, résolues par taxid NCBI
  (`scripts/sci_icons.py taxon 9606 9913 9925 9709 --libre`) : voir
  `references/iconographie.md`, notamment le garde-fou de licence share-alike.
- **Piège** : une flèche par événement inféré, pas par paire d'hôtes. Sinon la figure suggère
  un flux continu là où il y a deux événements. Et une silhouette au bout d'une branche
  **affirme** l'écotype : si l'assignation d'hôte est inférée, la légende doit le dire.

---

## Famille T — temps : ce que les dates valent, et contre quoi elles se lisent

### T1 — Frise à double registre, hôte et pathogène
- **Démontre** : qu'un événement du pathogène coïncide, ou ne coïncide pas, avec un événement
  humain documenté indépendamment.
- **S'impose quand** : l'article avance une date et invoque un contexte historique. C'est
  l'archétype signature de l'éco-anthropologie hôte-pathogène, et il est presque absent du
  dépôt.
- **Déclinaison MTBC** : néolithique, âge du bronze, empire romain, contact colombien,
  révolution industrielle, ère antibiotique en registre haut ; MRCA du MTBC, radiation L2/L4,
  émergence du clade *M. bovis*, introduction de L4 en Amérique, allèles de résistance en
  registre bas.
- **Outil** : TikZ, patron `frise_double_registre`.
- **Piège** : deux pièges, tous deux fatals. Une date de datation moléculaire **sans son
  HPD** est une affirmation non falsifiable : l'intervalle se dessine, il ne se relègue pas
  en note. Et un connecteur entre les deux registres est une **hypothèse testée**, pas une
  décoration : ne relier que les paires dont le recouvrement est mesuré quelque part.

### T2 — Figure de calibration temporelle
- **Démontre** : que le signal temporel existe avant d'en tirer des dates.
- **S'impose quand** : l'article date quoi que ce soit. Un relecteur sérieux la demandera.
- **Déclinaison MTBC** : régression racine-vers-pointes avec son coefficient, plus le test de
  randomisation des dates montrant que le jeu réel sort de la distribution des jeux permutés.
  Le MTBC a un signal temporel notoirement faible : le montrer est un gage de sérieux, pas un
  aveu.
- **Outil** : `sci-figure`, deux panneaux.
- **Piège** : publier la régression sans la randomisation. C'est précisément ce que le
  relecteur vérifiera.

### T3 — Skyline démographique annotée
- **Démontre** : qu'une inflexion de la taille efficace coïncide avec un événement historique.
- **S'impose quand** : l'article porte une histoire d'expansion ou de contraction.
- **Déclinaison MTBC** : Ne(t) d'une lignée avec ses bandes de crédibilité, et les bandes
  verticales des événements candidats (transition néolithique, urbanisation, antibiotiques).
- **Outil** : `sci-figure` par-dessus la sortie BEAST.
- **Piège** : une skyline sans son intervalle de crédibilité invite à lire du bruit comme un
  événement. Et poser une bande d'événement sur une inflexion n'est pas un test.

### T4 — Frise d'historiographie
- **Démontre** : où se situe la contribution dans l'histoire du champ.
- **S'impose quand** : le sujet a une nomenclature qui a bougé, ou l'introduction énumère
  qui a décrit quoi.
- **Déclinaison MTBC** : la description successive des lignées L1 à L10, avec l'auteur, la
  méthode disponible à l'époque (spoligotypage, MIRU-VNTR, WGS) et le nombre de génomes
  alors disponibles. Une telle frise explique pourquoi une révision était possible aujourd'hui
  et ne l'était pas hier.
- **Outil** : TikZ, variante mono-registre de T1.
- **Piège** : elle vire vite à l'hommage. La garder au service d'un argument : ce qui a changé
  dans les moyens, pas la liste des mérites.

---

## Famille G — géographie

### G1 — Carte de distribution avec dénominateurs
- **Démontre** : qu'une lignée est concentrée quelque part.
- **S'impose quand** : l'article nomme des pays.
- **Déclinaison MTBC** : choroplèthe ou camemberts par pays de la fréquence d'une
  sous-lignée.
- **Outil** : `geo-map`.
- **Piège** : le dénominateur. Une carte de comptes bruts est une carte de l'effort de
  séquençage, pas une carte de la biologie. Toujours la fréquence, toujours l'effectif par
  pays, et un seuil d'effectif minimal affiché.

### G2 — Carte et arbre couplés
- **Démontre** : que la structure phylogénétique suit une structure géographique.
- **S'impose quand** : l'article infère des migrations.
- **Déclinaison MTBC** : arbre daté à gauche, carte à droite, arcs colorés par période, les
  états ancestraux venant de `pastml` ou d'une reconstruction DTA.
- **Outil** : `itol` plus `geo-map -t arcs`, composés en panneaux.
- **Piège** : un arc est une inférence, pas une observation. Sa couleur doit dire la période
  et son épaisseur le support, jamais l'inverse.

### G3 — Carte de l'échantillonnage contre carte du signal
- **Démontre** : que le motif géographique n'est pas le décalque de l'endroit où l'on a
  séquencé.
- **S'impose quand** : toujours, dès qu'un motif géographique porte un argument. C'est le
  contrôle que les relecteurs demandent et que presque personne ne fournit d'avance.
- **Déclinaison MTBC** : deux panneaux jumeaux, effort d'échantillonnage à gauche, fréquence
  de la lignée à droite, même projection et même échelle de teintes.
- **Outil** : `geo-map`, deux appels et un `--preset` commun.
- **Piège** : c'est une figure de supplementary dans neuf cas sur dix, et c'est très bien :
  elle désamorce l'objection sans encombrer le corps de l'article.

---

## Famille P — procédure : comment on est passé des données au résultat

### P1 — Flux CONSORT génomique
- **Démontre** : que le jeu analysé est traçable et reproductible.
- **S'impose quand** : toujours, dès qu'il y a un filtrage. C'est la figure la plus
  systématiquement absente des manuscrits du dépôt alors qu'elle est la plus demandée.
- **Déclinaison MTBC** : de 255 000 génomes TBannotator au jeu final, avec chaque exclusion
  chiffrée et motivée dans une boîte latérale (hors clade, échecs de `strain-qc` par critère,
  *M. kansasii* misclassifiés écartés par skani).
- **Outil** : TikZ, patron `flux_donnees`.
- **Piège** : les exclusions **sont** la moitié de l'information. Un flux qui n'affiche que
  les effectifs retenus est un organigramme, pas un CONSORT. Et chaque effectif doit être
  reproductible par un script déposé, sinon la figure promet plus que le dépôt ne tient.

### P2 — Arbre de décision ou logigramme de classification
- **Démontre** : que la règle appliquée est explicite, donc réfutable et rejouable.
- **S'impose quand** : l'article applique des seuils, ou le texte contient « gates »,
  « criteria », « cut-off », « triage ».
- **Déclinaison MTBC** : les portes de contrôle qualité d'une souche ; l'arbre de décision qui
  assigne une lignée à partir des marqueurs ; la cascade de résolution d'une origine
  géographique.
- **Outil** : esquisse Mermaid `flowchart TD` pour trancher la structure, puis TikZ pour le
  livrable.
- **Piège** : les valeurs de seuil vont **sur les arêtes**, pas dans la légende. Un logigramme
  sans ses valeurs est un organigramme.

### P3 — Architecture d'un outil ou d'une chaîne logicielle
- **Démontre** : ce que l'outil fait, ce qu'il consomme, ce qu'il rend.
- **S'impose quand** : l'article présente un outil, une base, une méthode outillée.
- **Déclinaison MTBC** : la chaîne TBannotator, de l'accession SRA au `report.json` puis au
  `spdi.txt` ; l'articulation entre base locale, index Elasticsearch et interface.
- **Outil** : TikZ, ou esquisse Mermaid `graph LR`.
- **Piège** : dessiner l'implémentation plutôt que le contrat. Le lecteur veut savoir ce qui
  entre et ce qui sort, pas le nom des modules.

### P4 — Chaîne de reproductibilité
- **Démontre** : que chaque figure et chaque chiffre a un script identifié.
- **S'impose quand** : le code est déposé, ou un relecteur doute de la reproductibilité.
- **Déclinaison MTBC** : accession, script d'analyse, fichier de résultats, figure du
  manuscrit, en quatre colonnes reliées.
- **Outil** : TikZ, ou une table quand les liens sont simples.
- **Piège** : si la chaîne se lit ligne par ligne sans croisement, c'est une **table**.
  Ne faire la figure que s'il y a des convergences ou des réutilisations à montrer.

---

## Famille C — contribution : ce qui change

### C1 — Avant et après
- **Démontre** : la contribution elle-même, d'un seul regard.
- **S'impose quand** : l'article révise quelque chose. Le texte contient « previously
  reported », « has been assumed », « in contrast », « we instead ». C'est **la figure la plus
  rentable d'un article austère**, parce qu'elle rend la contribution lisible avant que le
  lecteur ait lu une ligne de résultats.
- **Déclinaison MTBC** : panneau A, la topologie admise avec L6 et L9 dans le grand clade
  animal ; panneau B, la topologie soutenue, avec la branche déplacée mise en évidence et une
  flèche de repositionnement entre les deux.
- **Outil** : TikZ, patron `avant_apres_topologie`.
- **Piège** : deux opinions côte à côte ne sont pas une démonstration. Un encart **« ce qui
  tranche »** est obligatoire, portant le marqueur, l'effectif et le test qui départagent.

### C2 — Figure-thèse
- **Démontre** : le message de l'article, en une image.
- **S'impose quand** : le message tient en une phrase falsifiable mais demande trois pages à
  établir ; ou quand la revue accepte un résumé graphique.
- **Déclinaison MTBC** : la seule du dépôt est celle de `bpal_resistance_emergence`. Toutes
  les autres manquent.
- **Outil** : TikZ, souvent en composant des éléments d'autres figures.
- **Piège** : elle se dessine **après** que le message est écrit, jamais avant. Une figure-thèse
  dessinée trop tôt fige une thèse qui n'a pas encore été prouvée, et l'article se met à la
  servir.

### C3 — Position dans l'espace du champ
- **Démontre** : que le travail occupe une case vide, et laquelle.
- **S'impose quand** : la revue de littérature a identifié un manque qu'on peut situer sur
  deux axes.
- **Déclinaison MTBC** : résolution taxonomique contre couverture géographique ; nombre de
  génomes contre profondeur d'annotation ; les travaux publiés en points, le présent travail
  distingué.
- **Outil** : `sci-figure`, nuage annoté.
- **Piège** : c'est la figure la plus facilement complaisante du bestiaire. Les axes doivent
  être choisis avant de placer son propre point, et les travaux voisins nommés et cités.

---

## Famille D — données structurées : les motifs qu'un tableau ne montre pas

### D1 — Matrice de marqueurs triée par l'arbre
- **Démontre** : qu'un ensemble de marqueurs est bien exclusif d'un clade, et où se trouvent
  les exceptions.
- **S'impose quand** : l'article définit une sous-lignée par des synapomorphies.
- **Déclinaison MTBC** : souches en lignes, ordonnées par l'arbre placé en marge ; marqueurs
  SPDI en colonnes ; présence, absence et **non couvert** distingués par trois teintes.
- **Outil** : `sci-figure` pour la matrice, `itol` pour l'arbre latéral.
- **Piège** : le plus important du bestiaire. **Absent et non couvert ne sont pas la même
  chose.** Une matrice à deux états transforme un trou de couverture en absence de marqueur,
  et fabrique de l'homoplasie qui n'existe pas. Trois états, toujours.

### D2 — Alluvial des nomenclatures
- **Démontre** : la correspondance entre systèmes de nommage concurrents.
- **S'impose quand** : l'article emploie une nomenclature qui n'est pas celle du lecteur.
- **Déclinaison MTBC** : Coll, Napier, Freschi, Shitikov, guyeux, en colonnes reliées par des
  flux dont l'épaisseur est l'effectif. Les fusions et les scissions se voient immédiatement,
  ce qu'aucune table de correspondance ne montre.
- **Outil** : `sci-figure`.
- **Piège** : au-delà de trois systèmes la figure devient illisible. Choisir les trois qui
  comptent pour le lecteur visé et renvoyer le reste en supplementary.

### D3 — Tanglegram hôte et pathogène
- **Démontre** : la co-divergence, et surtout ses exceptions.
- **S'impose quand** : l'article compare une structure de populations humaines à une structure
  de lignées.
- **Déclinaison MTBC** : populations humaines à gauche, lignées MTBC à droite en miroir, les
  appariements congruents en trait plein et les croisements en pointillé.
- **Outil** : TikZ, patron `tanglegram`.
- **Piège** : **un tanglegram sans test est une illustration.** PACo ou Mantel partiel
  contrôlant la distance géographique, avec p et nombre de permutations, dans la légende ou
  dans un encart. Et les croisements ne se cachent pas : ce sont eux qui portent l'exception à
  expliquer.

### D4 — Graphe de conflit de marqueurs
- **Démontre** : qu'un jeu de marqueurs est compatible avec un arbre unique, ou qui casse quoi.
- **S'impose quand** : une charpente taxonomique est reconstruite, ou un clade paraît instable.
- **Déclinaison MTBC** : marqueurs en sommets, une arête par paire incompatible, la couleur
  disant le type de croisement et l'épaisseur la fragilité mesurée sur les souches témoins.
  Un graphe vide est un résultat publiable.
- **Outil** : `networkx` plus `sci-figure`, en appui du skill `marker-laminarity`.
- **Piège** : le codage à trois états, encore. Un croisement calculé en confondant absence et
  non-couverture est un faux conflit.

---

## Famille S — structure : locus et protéines

### S1 — Anatomie d'un locus
- **Démontre** : que l'organisation d'une région porte une conséquence fonctionnelle.
- **S'impose quand** : le texte donne des coordonnées, des brins, des chevauchements, un TSS.
  Le détecteur signale ces sections par la famille de marqueurs « structure ».
- **Déclinaison MTBC** : un cadre de lecture superposé à un gène essentiel sur le brin opposé,
  avec le chevauchement chiffré, la position du site d'initiation de la transcription, et la
  conséquence, par exemple qu'aucun ARN guide ne peut cibler l'un sans toucher l'autre.
- **Outil** : TikZ.
- **Piège** : l'échelle. Un chevauchement de 123 nucléotides dans un gène de 2 kb ne se voit
  pas à l'échelle linéaire. Un encart zoomé, avec sa marque de changement d'échelle, résout
  ce que le rétrécissement du gène long détruirait.

### S2 — Dossier structural d'un gène
- **Démontre** : qu'une protéine mal annotée a une fonction plausible, ou qu'une substitution
  est délétère.
- **S'impose quand** : l'article requalifie un gène « hypothetical », ou évalue un variant.
- **Déclinaison MTBC** : trois panneaux, conservation par position avec les résidus
  catalytiques marqués, structure prédite avec le site actif, et impact ESM-1v de la
  substitution rapporté à une distribution de fond.
- **Outil** : rendu structural externe, composition par `sci-figure`.
- **Piège** : un score de poche ou un score d'impact **ne se lit jamais en valeur absolue**
  sans témoins positif et négatif appariés. La figure doit porter les témoins, sinon elle
  affirme ce que le score ne dit pas.

### S3 — Carte du génome
- **Démontre** : que des éléments hétérogènes se distribuent de façon non aléatoire.
- **S'impose quand** : l'article parle de plusieurs classes d'éléments à la fois.
- **Déclinaison MTBC** : H37Rv en axe, avec les régions de différence, les sites d'insertion
  d'IS6110, le locus CRISPR et les gènes de résistance en pistes superposées.
- **Outil** : `sci-figure`, ou TikZ si peu d'éléments.
- **Piège** : une carte du génome sans **modèle nul de distribution** ne démontre pas
  l'agrégation qu'elle suggère à l'oeil. Soit tracer l'attendu, soit ne rien affirmer.

---

## Ce que le bestiaire ne couvre pas

Trois besoins fréquents qui ne sont **pas** des figures :

- **Ranger des nombres qu'on lira un par un.** C'est une table. Un barplot de sept valeurs
  qu'on veut au chiffre près coûte une figure et rend un service inférieur.
- **Lister ce qui a été fait.** C'est le cahier de laboratoire, ou la section méthodes.
- **Faire joli.** Il n'y a pas d'archétype pour cela, et c'est délibéré.
