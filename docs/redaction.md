# Plugin `redaction`

> Manuscript writing and quality control: LaTeX typesetting, reference and figure verification, stylistic cleanup, table design, Overleaf synchronisation. Guyeux group (FEMTO-ST), phases 2-3 of the research cycle.

Skills propres (canoniques) : **19** ; skills partagés utilisés (symlinks) : **0**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [bib-check](#bib-check) ; [biblatex](#biblatex) ; [claim-check](#claim-check) ; [deai-latex](#deai-latex) ; [docs-latex](#docs-latex) ; [fig-check](#fig-check) ; [fig-ideation](#fig-ideation) ; [humanizer](#humanizer) ; [latex-build](#latex-build) ; [latex-document](#latex-document) ; [latex-formatting](#latex-formatting) ; [latex-paper-en](#latex-paper-en) ; [latex-tables](#latex-tables) ; [latex-writing](#latex-writing) ; [manuscript-review](#manuscript-review) ; [overleaf-bridge](#overleaf-bridge) ; [pdf-to-latex](#pdf-to-latex) ; [sci-table](#sci-table) ; [supp-check](#supp-check)

### bib-check

Verification exhaustive des references BibTeX d'un article LaTeX. Verifie l'existence reelle de chaque reference en ligne (tbmonitor-papers pour la TB et le MTBC, puis CrossRef, WebFetch, WebSearch), la coherence des metadonnees (auteurs, titre, annee, journal), la pertinence des citations dans leur contexte, et detecte les doublons semantiques. Outil anti-hallucinations : marque chaque reference verifiee.

Compétences : verifier la bibliographie ; controler que les references existent vraiment ; detecter des references inventees ou des doublons ; avant une soumission

### biblatex

Paquets LaTeX biblatex/biber pour la gestion moderne de bibliographie.

Compétences : aider à citer des références ; gérer des fichiers .bib ; choisir un style de citation ; dépanner la compilation de bibliographie

### claim-check

Extraction et verification systematique des affirmations scientifiques d'un article LaTeX. Classe les affirmations par priorite (structurantes vers annexes), audite la coherence numerique interne, verifie via bioinformatique, base de donnees ou litterature (tbmonitor prioritaire pour la TB et le MTBC, sinon WebSearch et WebFetch). Maintient un registre claim_check.md date et ne reverifie que les affirmations non verifiees ou perimees.

Compétences : verifier les affirmations d'un manuscrit ; controler que les chiffres du texte correspondent aux donnees ; recroiser un resultat avec la litterature ; avant une soumission

### deai-latex

Applique les regles de style scientifique a un article LaTeX : supprime le gras abusif, convertit les listes a puces en prose, fusionne les micro-sections, verifie les acronymes (definis une seule fois), met les noms d'especes en italique, elimine les cliches redactionnels et ameliore la coherence des temps verbaux.

Compétences : nettoyer les marqueurs de texte genere par IA ; retirer les tirets cadratin ; degonfler un texte trop liste ; harmoniser le style d'un manuscrit ; avant une soumission

### docs-latex

Convertit des documents Markdown en LaTeX professionnel avec visualisations TikZ, puis compile en PDF.

Compétences : produire un PDF de qualité présentation à partir d'un Markdown ; générer un rapport professionnel avec diagrammes ; convertir de la documentation en format prêt à imprimer

### fig-check

Vérification visuelle systématique des figures d'un article scientifique via les capacités multimodales. Pour chaque \includegraphics : lit l'image, évalue lisibilité, résolution, chevauchements, taille des textes, clarté des flèches, cohérence de palette, correspondance figure/légende. Maintient un registre fig_check.md et propose (applique en mode --fix) des corrections par régénération du script source quand il est détectable.

Compétences : préparer une soumission ou resoumission ; après modification de figures ; vérifier avant impression d'un poster ; déboguer une figure illisible dans le PDF final

### fig-ideation

Idéation de figures pour un manuscrit : cherche la figure qui MANQUE, là où fig-check ne vérifie que celles qui existent. Détecte mécaniquement les figures pendantes, orphelines et muettes, mesure le déficit de registre conceptuel face au corpus, balaie un bestiaire de 25 archétypes (frise à double registre, tanglegram hôte-pathogène, avant/après de topologie, flux CONSORT génomique, schéma de mécanisme, anatomie de locus), auto-challenge chaque candidate (charge de preuve, modèle nul, gain contre coût), esquisse en jetable puis livre en TikZ vectoriel compilé et inspecté, et tient le registre fig_plan.md. Fournit aussi une couche d'iconographie libre (PhyloPic résolu par taxid NCBI, Bioicons), convertie en PDF vectoriel sans Inkscape, avec garde-fou de licence share-alike et génération automatique de l'attribution.

Compétences : écrire le squelette d'un article en phase 2 ; répondre à une objection de manuscript-review par un schéma ; un article paraît austère ou illisible ; un mécanisme est décrit en prose sans dessin ; savoir quelles figures déjà produites dorment sur le disque

### humanizer

Supprime les marqueurs d'écriture IA d'un texte pour le rendre naturel et humain. Élimine les tics : importance gonflée, abus de tirets cadratin, règle de trois, ton flagorneur, phrases de remplissage, gras abusif, attributions vagues. Ajoute de la voix, de la précision et du rythme.

Compétences : humaniser un texte généré par IA ; retirer les patterns de ChatGPT ; rendre une écriture moins robotique ; éditer un texte pour Wikipédia ou publication

### latex-build

Compilations LaTeX avec latexmk et prévisualisation en direct.

Compétences : latexmk, compilation LaTeX, prévisualisation en direct

### latex-document

Skill LaTeX universel : creer, compiler et convertir n'importe quel document en PDF professionnel avec apercus PNG. Couvre rapports, theses, livres, lettres, factures, CV academiques, examens, aide-memoires, formulaires PDF remplissables, contenu conditionnel, publipostage depuis CSV ou JSON, diffs de version latexdiff, graphiques pgfplots et matplotlib, tableaux booktabs, TikZ, diagrammes Mermaid, bibliographie, documents multilingues et CJK (XeLaTeX automatique), algorithmes, tcolorbox, siunitx, conversion Pandoc depuis et vers Markdown, DOCX et HTML, et conversion PDF vers LaTeX de documents imprimes ou manuscrits. Egalement des utilitaires PDF : fusion, decoupe, chiffrement, optimisation, filigrane, extraction de texte ou de tableaux, OCR, remplissage de formulaire. Pour les articles de revue preferer latex-paper-en, pour les slides beamer-slides, pour les posters latex-posters.

Compétences : ecrire, compiler, deboguer, convertir ou manipuler un document LaTeX ou un PDF

### latex-formatting

Gère la mise en forme, les gabarits et le style LaTeX des articles académiques : gabarits de conférences (ICML, ICLR, NeurIPS, AAAI, ACL), correction de problèmes de mise en forme, gestion des paquets, conformité aux exigences des lieux de publication.

Compétences : mettre en place un gabarit d'article ; corriger une mise en forme LaTeX ; préparer une soumission

### latex-paper-en

Assistant LaTeX pour articles académiques en anglais sur des projets .tex existants (IEEE, ACM, Springer, NeurIPS, ICML).

Compétences : compiler, linter, auditer ou améliorer un article LaTeX anglais ; corriger la bibliographie, la grammaire, la logique ; polir l'expression, traduire, optimiser le titre, vérifier figures et pseudocode ;  relis mon article », « corrige mon LaTeX », « prépare la soumission 

### latex-tables

Tableaux LaTeX avec le paquet tabularray.

Compétences : tableau LaTeX, tabularray, colonnes à largeur fixe, alignement de tableau

### latex-writing

Guide la rédaction de documents LaTeX selon les bonnes pratiques et un balisage sémantique correct. Veille au bon usage des environnements sémantiques (description vs itemize), de csquotes (\enquote{} plutôt que ``...'') et de cleveref (\cref{} plutôt que \S\ref{}).

Compétences : écrire ou éditer des fichiers .tex ou .nw ; l'utilisateur mentionne LaTeX, BibTeX ou la mise en forme ; relire la qualité d'un code LaTeX

### manuscript-review

Revue par les pairs d'un manuscrit scientifique comme pour une revue a fort facteur d'impact. Lit l'article complet (LaTeX ou texte), evalue structure, methodologie, statistiques, terminologie, figures et references, et produit une revue structuree en francais avec des recommandations classees par severite. Pour les manuscrits TB et MTBC, valide l'etat de l'art et la completude des citations contre tbmonitor-papers (environ 190 000 resumes TB de PubMed).

Compétences : obtenir une lecture critique d'un manuscrit ; savoir ce qu'un relecteur objecterait ; faire relire un article avant soumission ; demander un second avis sur un brouillon

### overleaf-bridge

Synchronise un depot local article/ avec un projet Overleaf via l'integration Git officielle d'Overleaf (git-bridge, git.overleaf.com). Git standard sur le depot officiel : pas de serveur MCP, pas d'API non officielle, pas de scraping.

Compétences : pousser un manuscrit vers Overleaf ; recuperer les modifications des co-auteurs dans le depot local ; voir ce qui a change depuis la derniere synchronisation ; resoudre une divergence entre les deux ; collecter les commentaires laisses par les co-auteurs dans le .tex

### pdf-to-latex

Reconstruit un code source LaTeX compilable à partir d'un document PDF. Analyse structure, mise en page, polices, tableaux, équations et figures pour produire un .tex visuellement fidèle. Utilise markitdown pour l'extraction du texte, puis reconstruit classe de document, paquets, géométrie et contenu.

Compétences : rétro-ingénierie d'un PDF vers LaTeX ; reproduire un gabarit d'article ; éditer un article sans les fichiers source ; reconstruire des documents institutionnels

### sci-table

Academic research toolkit (Guyeux group, FEMTO-ST), redaction d'articles evalues par les pairs : conception et mise en forme des TABLEAUX d'un manuscrit. Traite d'abord le FOND (ce tableau doit-il exister, ou est-ce une phrase, une figure, un supplementaire ; quelles lignes, quelles colonnes, quel ordre, quelle precision), puis la FORME (booktabs, alignement decimal siunitx, notes threeparttable, legende autonome, largeur reelle et ancrage colonne / pleine page / rotation / longtable). Audite mecaniquement les tableaux d'un .tex (20 regles : colonne constante, precision heterogene, largeur debordante, police reduite en rustine, tableau non cite, tableau relu dans le texte), construit un tableau depuis un CSV en explicitant ses decisions, et tient le registre tab_check.md. A

Compétences : on ecrit ou retravaille un tableau d'article, quand un tableau deborde de la marge, quand on hesite entre un tableau et une figure, ou avant une soumission ; Pour la seule syntaxe de tabularray, voir latex-tables

### supp-check

Vérification d'alignement entre un manuscrit principal et ses supplementary materials. Itère sur chaque table/figure/fichier supplémentaire, comprend son rôle, parcourt le cahier_de_labo.md pour reconstruire sa genèse et ce qui s'est passé depuis, puis détecte les divergences avec le main.tex et avec la vérité la plus récente. Les dernières entrées du cahier font autorité : si un supplément est obsolète, le skill propose de le retravailler, de réécrire le main, de lancer une expérience d'arbitrage ou de remettre l'ensemble en question.

Compétences : préparer une soumission ou resoumission ; après toute modification de la BDD ou des scripts ; après correction d'un bug influençant les chiffres ; après mise à jour d'une méthode ou d'un outil ; avant envoi de révisions à un relecteur
