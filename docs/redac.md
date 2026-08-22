# Plugin `redac`

> Un plugin pour la rédaction d'articles et de projets

## Rôle dans un projet M. tuberculosis

Rédaction et contrôle qualité du manuscrit M. tuberculosis : mise en forme LaTeX, vérification des affirmations et des références, nettoyage stylistique, réponse aux relecteurs, dépôt Zenodo et pont Overleaf.

Skills propres (canoniques) : **29** ; skills partagés utilisés (symlinks) : **4**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [beamer-slides](#beamer-slides) ; [bib-check](#bib-check) ; [biblatex](#biblatex) ; [claim-check](#claim-check) ; [cv](#cv) ; [deai-latex](#deai-latex) ; [docs-latex](#docs-latex) ; [fig-check](#fig-check) ; [grant-proposal](#grant-proposal) ; [humanizer](#humanizer) ; [latex-build](#latex-build) ; [latex-document](#latex-document) ; [latex-formatting](#latex-formatting) ; [latex-paper-en](#latex-paper-en) ; [latex-posters](#latex-posters) ; [latex-tables](#latex-tables) ; [latex-writing](#latex-writing) ; [lit-review](#lit-review) ; [literature-access](#literature-access) ; [manuscript-review](#manuscript-review) ; [overleaf-bridge](#overleaf-bridge) ; [pdf-to-latex](#pdf-to-latex) ; [reviewer-response](#reviewer-response) ; [slide-design](#slide-design) ; [slide-polish](#slide-polish) ; [supp-check](#supp-check) ; [synthesize-research](#synthesize-research) ; [theme-factory](#theme-factory) ; [zenodo-deposit](#zenodo-deposit)

### beamer-slides

Genere une presentation scientifique Beamer complete a partir de la matiere de recherche existante : lit main.tex, les donnees et les figures, puis construit un deck autonome, narratif et pedagogique. Pour une ou deux slides a partir d'une idee, utiliser slide-design ; pour retravailler une slide existante, slide-polish.

Compétences : l'utilisateur demande un expose, une presentation de seminaire ou de conference, un deck de soutenance, ou des slides couvrant tout un article ou tout un projet

### bib-check

Verification exhaustive des references BibTeX d'un article LaTeX. Verifie l'existence reelle de chaque reference en ligne (tbmonitor-papers pour la TB et le MTBC, puis CrossRef, WebFetch, WebSearch), la coherence des metadonnees (auteurs, titre, annee, journal), la pertinence des citations dans leur contexte, et detecte les doublons semantiques. Outil anti-hallucinations : marque chaque reference verifiee.

Compétences : verifier la bibliographie ; controler que les references existent vraiment ; detecter des references inventees ou des doublons ; avant une soumission

### biblatex

Paquets LaTeX biblatex/biber pour la gestion moderne de bibliographie.

Compétences : aider à citer des références ; gérer des fichiers .bib ; choisir un style de citation ; dépanner la compilation de bibliographie

### claim-check

Extraction et verification systematique des affirmations scientifiques d'un article LaTeX. Classe les affirmations par priorite (structurantes vers annexes), audite la coherence numerique interne, verifie via bioinformatique, base de donnees ou litterature (tbmonitor prioritaire pour la TB et le MTBC, sinon WebSearch et WebFetch). Maintient un registre claim_check.md date et ne reverifie que les affirmations non verifiees ou perimees.

Compétences : verifier les affirmations d'un manuscrit ; controler que les chiffres du texte correspondent aux donnees ; recroiser un resultat avec la litterature ; avant une soumission

### cv

Extrait les informations pertinentes du CV LaTeX de Christophe Guyeux pour appuyer la rédaction de projets, de demandes de financement (ANR, ERC, Horizon, LabCom), de candidatures, de lettres de recommandation, de résumés de recherche, ou de tout document exigeant une présentation de soi exacte.

Compétences : rédiger un projet, un dossier de candidature, une lettre de motivation, un résumé de recherche, une liste de publications, un dossier d'encadrement ou d'historique de financement ; citer des éléments précis du CV (publications, financements, indicateurs d'impact, co-auteurs), même sans dire explicitement « CV 

### deai-latex

Applique les regles de style scientifique a un article LaTeX : supprime le gras abusif, convertit les listes a puces en prose, fusionne les micro-sections, verifie les acronymes (definis une seule fois), met les noms d'especes en italique, elimine les cliches redactionnels et ameliore la coherence des temps verbaux.

Compétences : nettoyer les marqueurs de texte genere par IA ; retirer les tirets cadratin ; degonfler un texte trop liste ; harmoniser le style d'un manuscrit ; avant une soumission

### docs-latex

Convertit des documents Markdown en LaTeX professionnel avec visualisations TikZ, puis compile en PDF.

Compétences : produire un PDF de qualité présentation à partir d'un Markdown ; générer un rapport professionnel avec diagrammes ; convertir de la documentation en format prêt à imprimer

### fig-check

Vérification visuelle systématique des figures d'un article scientifique via les capacités multimodales. Pour chaque \includegraphics : lit l'image, évalue lisibilité, résolution, chevauchements, taille des textes, clarté des flèches, cohérence de palette, correspondance figure/légende. Maintient un registre fig_check.md et propose (applique en mode --fix) des corrections par régénération du script source quand il est détectable.

Compétences : préparer une soumission ou resoumission ; après modification de figures ; vérifier avant impression d'un poster ; déboguer une figure illisible dans le PDF final

### grant-proposal

Aide à la rédaction de demandes de financement adaptées aux formats français et européens : ANR (AAPG, LabCom, PRCI), Horizon Europe, Interreg, PHC (Hubert Curien), ARS, AMI, Région, UMLP/Sunergia. Connaît la structure exacte de chaque appel, les contraintes de formatage, et s'appuie sur les propositions antérieures de l'utilisateur comme modèles.

Compétences : rédiger un projet de recherche, une demande de financement, un pré-projet ; répondre à un appel à projets ; reformuler ou améliorer une section (impact, work packages, budget) d'une proposition existante

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

### latex-posters

Cree des posters de recherche en LaTeX avec beamerposter, tikzposter ou baposter : mise en page et grilles de colonnes, palettes, integration des figures, et regles propres au poster sur la taille de police, la distance de lecture et la hierarchie visuelle. Pour des slides utiliser beamer-slides, pour les figures elles-memes sci-figure.

Compétences : l'utilisateur demande un poster de conference ; mentionne un format A0 ou A1, beamerposter, tikzposter ou baposter ; veut transformer un article en poster

### latex-tables

Tableaux LaTeX avec le paquet tabularray.

Compétences : tableau LaTeX, tabularray, colonnes à largeur fixe, alignement de tableau

### latex-writing

Guide la rédaction de documents LaTeX selon les bonnes pratiques et un balisage sémantique correct. Veille au bon usage des environnements sémantiques (description vs itemize), de csquotes (\enquote{} plutôt que ``...'') et de cleveref (\cref{} plutôt que \S\ref{}).

Compétences : écrire ou éditer des fichiers .tex ou .nw ; l'utilisateur mentionne LaTeX, BibTeX ou la mise en forme ; relire la qualité d'un code LaTeX

### lit-review

Revue de littérature scientifique systématique et incrémentale. Recherche, lit, synthétise et stocke dans litterature_review/. À chaque relance, approfondit de nouvelles directions ou enrichit les sujets existants. Maintient un BibTeX cumulatif. Pour les sujets TB/MTBC, préfère tbmonitor-papers (corpus PubMed TB pré-indexé, réponses sub-seconde) avant l'API PubMed live. Le mode --wide active le backward chaining sur les références et la recherche pré-nomenclature.

Compétences : construire une revue de littérature sur un sujet ; approfondir une revue existante ; préparer un état de l'art pour un article ou une demande de financement ; repérer des lacunes ; découvrir des travaux précurseurs antérieurs à la terminologie actuelle

### literature-access

Maximise l'accès LÉGAL au plein texte scientifique en cascade, pour combler le trou entre « résumé » (tbmonitor, abstracts) et « article payant ». Deux moteurs : recall par le CORPS du texte (trouver les articles dont le corps mentionne un gène / locus tag / méthode, pas seulement le résumé, via europepmc_fulltext.py search) et résolution d'accès (donné un DOI, rendre la meilleure voie légale : Europe PMC OA lisible ici, Unpaywall green/gold OA, OpenAlex, Semantic Scholar, puis hand-off vers TDM institutionnel / bibliothèque sous licence / contact auteur). Ne contourne AUCUN paywall

Compétences : un gène ressort « sans littérature » alors qu'il est cité dans des articles OA ; vérifier qu'un terme est réellement absent de la littérature ; obtenir le plein texte d'un DOI pour claim-check/bib-check/lit-review ; construire une revue à haut rappel

### manuscript-review

Revue par les pairs d'un manuscrit scientifique comme pour une revue a fort facteur d'impact. Lit l'article complet (LaTeX ou texte), evalue structure, methodologie, statistiques, terminologie, figures et references, et produit une revue structuree en francais avec des recommandations classees par severite. Pour les manuscrits TB et MTBC, valide l'etat de l'art et la completude des citations contre tbmonitor-papers (environ 190 000 resumes TB de PubMed).

Compétences : obtenir une lecture critique d'un manuscrit ; savoir ce qu'un relecteur objecterait ; faire relire un article avant soumission ; demander un second avis sur un brouillon

### overleaf-bridge

Synchronise un depot local article/ avec un projet Overleaf via l'integration Git officielle d'Overleaf (git-bridge, git.overleaf.com). Git standard sur le depot officiel : pas de serveur MCP, pas d'API non officielle, pas de scraping.

Compétences : pousser un manuscrit vers Overleaf ; recuperer les modifications des co-auteurs dans le depot local ; voir ce qui a change depuis la derniere synchronisation ; resoudre une divergence entre les deux ; collecter les commentaires laisses par les co-auteurs dans le .tex

### pdf-to-latex

Reconstruit un code source LaTeX compilable à partir d'un document PDF. Analyse structure, mise en page, polices, tableaux, équations et figures pour produire un .tex visuellement fidèle. Utilise markitdown pour l'extraction du texte, puis reconstruit classe de document, paquets, géométrie et contenu.

Compétences : rétro-ingénierie d'un PDF vers LaTeX ; reproduire un gabarit d'article ; éditer un article sans les fichiers source ; reconstruire des documents institutionnels

### reviewer-response

Reponse point par point systematique a une revue de manuscrit. Decoupe les commentaires des relecteurs en taches individuelles, evalue chacune de facon critique (accord ou desaccord), planifie et execute les analyses (bioinformatique, litterature, statistiques) dans experiments/, ameliore le manuscrit et produit une lettre de reponse datee dans review/. S'invoque avec review/fichier.md pour demarrer, next pour avancer, status pour l'avancement, R05 pour sauter a une remarque.

Compétences : des rapports de relecture sont arrives et il faut y repondre ; traiter une revision ; rediger une lettre de reponse

### slide-design

Transforme une courte description de ce que l'on veut dire en une a quelques slides de qualite editoriale. Impose un systeme graphique (palette, typographie, grille), raisonne sur la narration, propose plusieurs options structurelles avec des references editoriales explicites (NYT Graphics, Bloomberg, Pudding, Tufte, Nature Methods), exige au moins une option a signature visuelle forte, prefere schemas, frises et diagrammes au texte brut, reutilise les figures trouvees dans le projet, delegue les cartes a geo-map et les graphiques a sci-figure, s'aligne sur le style du deck hote, et compile systematiquement un apercu qu'il critique avant livraison.

Compétences : taper /slide-design ; demander une ou deux slides sur une idee ; dire j'ai besoin d'une slide qui dit ; ou fais-moi 2 slides sur Y ; transformer une idee verbale en matiere de slide plutot que generer une presentation entiere

### slide-polish

Amelioration ciblee d'une slide Beamer existante, sur le fond et sur la forme, avec une etape obligatoire de brassage large : relire la matiere du projet (cahier de labo, manuscrit, JOURNAL, claim-check) pour reconstruire la these pleine et eviter la moyennisation par polissage, ce defaut classique qui rend une slide moyenne plus belle en sacrifiant specificite, nuance et voix. Compile et lit visuellement les PNG, choisit une modalite (TikZ, Mermaid, frise, big number, carte via geo-map), applique deai-latex etendu, score chaque version sur 16 points avec veto anti-moyennisation, itere tant que le score progresse, puis enchaine une boucle de proprete visuelle sur crops haute resolution et un test final de voix scientifique.

Compétences : taper /slide-polish ; demander d'ameliorer, de retravailler ou de rendre meilleure une slide precise existante, plutot que d'en creer une nouvelle ou de generer un deck entier

### supp-check

Vérification d'alignement entre un manuscrit principal et ses supplementary materials. Itère sur chaque table/figure/fichier supplémentaire, comprend son rôle, parcourt le cahier_de_labo.md pour reconstruire sa genèse et ce qui s'est passé depuis, puis détecte les divergences avec le main.tex et avec la vérité la plus récente. Les dernières entrées du cahier font autorité : si un supplément est obsolète, le skill propose de le retravailler, de réécrire le main, de lancer une expérience d'arbitrage ou de remettre l'ensemble en question.

Compétences : préparer une soumission ou resoumission ; après toute modification de la BDD ou des scripts ; après correction d'un bug influençant les chiffres ; après mise à jour d'une méthode ou d'un outil ; avant envoi de révisions à un relecteur

### synthesize-research

Synthetise un ensemble de materiaux qualitatifs en constats structures et hierarchises par force de preuve : analyse thematique, cartographie par affinites, triangulation entre sources, et integration du qualitatif avec le quantitatif. Distingue explicitement deux registres, scientifique et produit, qui partagent les methodes mais pas les livrables. N'est ni la verification des affirmations d'un manuscrit (claim-check) ni une recherche bibliographique ciblee (lit-review), qui partent de la question et non du corpus.

Compétences : de nombreuses sources separees portent sur une meme question et il faut en degager les themes : articles lus pour une revue, notes d'entretiens d'experts ou de parties prenantes, reponses libres de questionnaire, commentaires de relecteurs sur plusieurs tours, retours de terrain

### theme-factory

Applique un theme visuel coherent (couleurs, typographie, espacement) a un artefact : slides, documents, rapports, pages HTML. Dix themes preetablis sont disponibles et un nouveau theme peut etre genere a la volee. Pour le travail de slide scientifique utiliser slide-design, et pour les gabarits de figures de revue sci-figure.

Compétences : restyler ou harmoniser un artefact existant ; obtenir une autre apparence pour un deck ou une page ; demander une palette et un appariement de polices sur mesure

### zenodo-deposit

Dépôt automatique d'un artefact de recherche (code, données, harnais d'évaluation, supplementary materials) sur Zenodo, pour obtenir un DOI citable à insérer dans un manuscrit. Le token Zenodo est configuré une seule fois puis réutilisé pour tous les articles. Crée un brouillon, téléverse l'archive, écrit les métadonnées (titre, auteurs, ORCID, licence extraits du .tex), réserve le DOI et peut remplacer le placeholder dans le main.tex. La publication (irréversible) reste une étape explicite confirmée par l'auteur.

Compétences :  déposer sur Zenodo  ;  obtenir un DOI  ;  publier le harnais / les supplementary  ;  activer le DOI Zenodo de l'article  ; ou taper /zenodo-deposit

## Skills partagés (via symlink)

Documentés sur la page de leur plugin d'origine.

| Skill | Origine |
|-------|---------|
| [create-viz](bio_population_genetics.md#create-viz) | `bio_population_genetics` |
| [geo-map](bio_population_genetics.md#geo-map) | `bio_population_genetics` |
| [read-scientific-pdf](bio_population_genetics.md#read-scientific-pdf) | `bio_population_genetics` |
| [sci-figure](bio_population_genetics.md#sci-figure) | `bio_population_genetics` |
