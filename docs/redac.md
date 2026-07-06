# Plugin `redac`

> Un plugin pour la rédaction d'articles et de projets

## Rôle dans un projet M. tuberculosis

Rédaction et contrôle qualité du manuscrit M. tuberculosis : mise en forme LaTeX, vérification des affirmations et des références, nettoyage stylistique, réponse aux relecteurs, dépôt Zenodo et pont Overleaf.

Skills propres (canoniques) : **29** ; skills partagés utilisés (symlinks) : **6**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [beamer-slides](#beamer-slides) ; [bib-check](#bib-check) ; [biblatex](#biblatex) ; [claim-check](#claim-check) ; [cv](#cv) ; [deai-latex](#deai-latex) ; [docs-latex](#docs-latex) ; [fig-check](#fig-check) ; [grant-proposal](#grant-proposal) ; [humanizer](#humanizer) ; [latex-build](#latex-build) ; [latex-document](#latex-document) ; [latex-formatting](#latex-formatting) ; [latex-paper-en](#latex-paper-en) ; [latex-posters](#latex-posters) ; [latex-tables](#latex-tables) ; [latex-writing](#latex-writing) ; [lit-review](#lit-review) ; [manuscript-review](#manuscript-review) ; [overleaf-bridge](#overleaf-bridge) ; [pdf-to-latex](#pdf-to-latex) ; [plotly](#plotly) ; [reviewer-response](#reviewer-response) ; [slide-design](#slide-design) ; [slide-polish](#slide-polish) ; [supp-check](#supp-check) ; [synthesize-research](#synthesize-research) ; [theme-factory](#theme-factory) ; [zenodo-deposit](#zenodo-deposit)

### beamer-slides

Génère des slides de présentation Beamer/LaTeX professionnelles à partir d'un travail de recherche. Analyse main.tex, les données et les figures pour bâtir une présentation scientifique autonome, guidée par la narration et pédagogique.

Compétences : produire une présentation scientifique à partir d'un manuscrit et de ses figures ; préparer un exposé de séminaire ou de soutenance

### bib-check

Vérification exhaustive des références BibTeX d'un article LaTeX. Vérifie l'existence réelle de chaque référence en ligne, la cohérence des métadonnées (auteurs, titre, année, journal), la pertinence des citations dans leur contexte, et détecte les doublons sémantiques. Outil anti-hallucinations. Pour les références TB/MTBC, tbmonitor-papers valide en SQL sub-seconde l'existence d'une référence contre le corpus PubMed TB pré-indexé avant de recourir à WebFetch/OpenAlex/CrossRef.

Compétences : vérifier la bibliographie d'un manuscrit avant soumission ; détecter des références hallucinées ou des doublons ; confirmer les métadonnées d'un DOI

### biblatex

Paquets LaTeX biblatex/biber pour la gestion moderne de bibliographie.

Compétences : aider à citer des références ; gérer des fichiers .bib ; choisir un style de citation ; dépanner la compilation de bibliographie

### claim-check

Extraction et vérification systématique des affirmations scientifiques d'un article. Classe les affirmations par priorité (structurantes puis annexes), les vérifie via bioinfo, base de données ou littérature. Pour la vérification littérature TB/MTBC, interroger d'abord tbmonitor (corpus PubMed TB pré-indexé, SQL sub-seconde) avant WebSearch/WebFetch. Maintient un registre claim_check.md avec dates de vérification, et ne revérifie que les affirmations non vérifiées ou anciennes.

Compétences : vérifier factuellement un manuscrit avant soumission ; établir ce qui est prouvé, à vérifier ou incertain ; tracer les vérifications dans le temps

### cv

Extrait les informations pertinentes du CV LaTeX de Christophe Guyeux pour appuyer la rédaction de projets, de demandes de financement (ANR, ERC, Horizon, LabCom), de candidatures, de lettres de recommandation, de résumés de recherche, ou de tout document exigeant une présentation de soi exacte.

Compétences : rédiger un projet, un dossier de candidature, une lettre de motivation, un résumé de recherche, une liste de publications, un dossier d'encadrement ou d'historique de financement ; citer des éléments précis du CV (publications, financements, indicateurs d'impact, co-auteurs), même sans dire explicitement « CV 

### deai-latex

Applique les règles de style scientifique à un article LaTeX : supprime le gras abusif, convertit les listes à puces en prose, fusionne les micro-sections, vérifie les acronymes (définis une seule fois), met les noms d'espèces en italique, élimine les clichés rédactionnels et améliore la cohérence des temps verbaux. Produit un manuscrit conforme aux conventions des revues.

Compétences : nettoyer les marqueurs de texte généré par IA dans un manuscrit ; harmoniser le style avant soumission

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

Skill LaTeX universel : créer, compiler et convertir tout document en PDF professionnel avec aperçus PNG. Gère CV, rapports, lettres, factures, articles académiques, thèses, présentations Beamer, posters, examens, livres, aide-mémoires, formulaires PDF remplissables, fusion de courrier depuis CSV/JSON, diff de versions (latexdiff), graphiques (pgfplots + matplotlib), tableaux (booktabs), images (TikZ), diagrammes Mermaid, bibliographie (BibTeX/biblatex), multilingue/CJK (XeLaTeX auto), algorithmes, conversion Pandoc (Markdown/DOCX/HTML ↔ LaTeX) et conversion PDF-vers-LaTeX de documents manuscrits ou imprimés. Compilation pdflatex/xelatex/lualatex avec détection auto et filtrage de logs.

Compétences : créer un CV ou une lettre ; écrire ou compiler un document LaTeX ; produire un PDF avec tableaux/graphiques/images ; faire un rapport, une facture, une présentation, une thèse, un poster, un examen, un livre ; convertir entre formats de documents ; convertir ou OCR un PDF en LaTeX ; déboguer une compilation LaTeX

### latex-formatting

Gère la mise en forme, les gabarits et le style LaTeX des articles académiques : gabarits de conférences (ICML, ICLR, NeurIPS, AAAI, ACL), correction de problèmes de mise en forme, gestion des paquets, conformité aux exigences des lieux de publication.

Compétences : mettre en place un gabarit d'article ; corriger une mise en forme LaTeX ; préparer une soumission

### latex-paper-en

Assistant LaTeX pour articles académiques en anglais sur des projets .tex existants (IEEE, ACM, Springer, NeurIPS, ICML).

Compétences : compiler, linter, auditer ou améliorer un article LaTeX anglais ; corriger la bibliographie, la grammaire, la logique ; polir l'expression, traduire, optimiser le titre, vérifier figures et pseudocode ;  relis mon article », « corrige mon LaTeX », « prépare la soumission 

### latex-posters

Crée des posters de recherche professionnels en LaTeX avec beamerposter, tikzposter ou baposter. Gère mise en page, palettes, formats multi-colonnes, intégration de figures et bonnes pratiques propres aux posters.

Compétences : produire un poster scientifique pour une conférence ; concevoir une communication visuelle académique

### latex-tables

Tableaux LaTeX avec le paquet tabularray.

Compétences : tableau LaTeX, tabularray, colonnes à largeur fixe, alignement de tableau

### latex-writing

Guide la rédaction de documents LaTeX selon les bonnes pratiques et un balisage sémantique correct. Veille au bon usage des environnements sémantiques (description vs itemize), de csquotes (\enquote{} plutôt que ``...'') et de cleveref (\cref{} plutôt que \S\ref{}).

Compétences : écrire ou éditer des fichiers .tex ou .nw ; l'utilisateur mentionne LaTeX, BibTeX ou la mise en forme ; relire la qualité d'un code LaTeX

### lit-review

Revue de littérature scientifique systématique et incrémentale. Recherche, lit, synthétise et stocke dans litterature_review/. À chaque relance, approfondit de nouvelles directions ou enrichit les sujets existants. Maintient un BibTeX cumulatif. Pour les sujets TB/MTBC, préfère tbmonitor-papers (corpus PubMed TB pré-indexé, réponses sub-seconde) avant l'API PubMed live. Le mode --wide active le backward chaining sur les références et la recherche pré-nomenclature.

Compétences : construire une revue de littérature sur un sujet ; approfondir une revue existante ; préparer un état de l'art pour un article ou une demande de financement ; repérer des lacunes ; découvrir des travaux précurseurs antérieurs à la terminologie actuelle

### manuscript-review

Relecture par les pairs d'un manuscrit scientifique comme pour une revue à fort impact. Lit l'article complet (LaTeX ou texte), évalue structure, méthodologie, statistiques, terminologie, figures, références, et produit une revue structurée en français avec recommandations classées par sévérité. Pour les manuscrits TB/MTBC, valide l'état de l'art et la complétude des citations contre tbmonitor-papers.

Compétences : relire un manuscrit avant soumission ou resoumission ; obtenir une critique structurée par sévérité ; détecter une publication récente majeure oubliée par les auteurs

### overleaf-bridge

Synchronise un dépôt local article/ avec un projet Overleaf via l'intégration Git officielle d'Overleaf (git-bridge, git.overleaf.com). Dépose un nouveau manuscrit, récupère les dernières éditions des co-auteurs, montre le diff et collecte les commentaires laissés par les co-auteurs dans le .tex. Git standard sur le remote officiel, sans serveur MCP, sans API non officielle, sans scraping.

Compétences : déposer un manuscrit sur Overleaf ; récupérer les éditions des co-auteurs ; voir le diff ; collecter et traiter les commentaires laissés dans le .tex

### pdf-to-latex

Reconstruit un code source LaTeX compilable à partir d'un document PDF. Analyse structure, mise en page, polices, tableaux, équations et figures pour produire un .tex visuellement fidèle. Utilise markitdown pour l'extraction du texte, puis reconstruit classe de document, paquets, géométrie et contenu.

Compétences : rétro-ingénierie d'un PDF vers LaTeX ; reproduire un gabarit d'article ; éditer un article sans les fichiers source ; reconstruire des documents institutionnels

### plotly

Bibliothèque de tracé interactif de haut niveau pour Python. Idéale pour les visualisations web, les tracés 3D et les tableaux de bord interactifs complexes. Bâtie sur plotly.js, elle permet de zoomer, déplacer et survoler les points de données dans le navigateur. Sert aux graphiques interactifs, applications web, notebooks Jupyter, cartes géographiques, animations, séries temporelles et tableaux de bord Dash.

Compétences : produire des graphiques interactifs (survol, zoom) ; visualiser en 3D ; construire un tableau de bord web ; intégrer une figure dans un notebook Jupyter

### reviewer-response

Réponse systématique point par point à une relecture de manuscrit. Décompose les commentaires du relecteur en tâches individuelles, évalue chacune de façon critique (accord/désaccord), planifie et exécute des analyses (bioinfo, littérature, statistiques) dans experiments/, améliore le manuscrit et produit une lettre de réponse horodatée dans review/. Quand un relecteur demande des citations TB/MTBC, utiliser d'abord tbmonitor-papers.

Compétences : répondre à une relecture point par point ; démarrer avec /reviewer-response review/fichier.md, avancer avec next, vérifier avec status, ou sauter à une remarque précise (R05)

### slide-design

Transforme une brève description de ce qu'on veut dire en une à quelques slides de qualité éditoriale. Impose un système de design (palette, typographie, grille), raisonne sur la narration, propose plusieurs options structurelles avec références éditoriales explicites (NYT Graphics, Bloomberg, Pudding, Tufte, Nature Methods), exige au moins une option à forte signature visuelle (schéma TikZ, big number, image plein cadre, sparkline), délègue les cartes à geo-map et les graphiques à create-viz/seaborn, et compile un aperçu qu'elle relit visuellement avant livraison.

Compétences : l'utilisateur tape /slide-design ; demande « fais-moi une slide / deux slides » pour une idée ;  il me faut une slide qui dit ;  « conçois une slide sur X », « comment je présenterais X en une slide  ; convertir une idée verbale en slide soignée plutôt que générer une présentation entière

### slide-polish

Amélioration ciblée d'une slide Beamer existante, sur le fond et sur la forme, avec une étape obligatoire de reconstruction de la thèse pleine du projet pour éviter la moyennisation par polissage (rendre une slide moyenne plus joliment moyenne en sacrifiant spécificité, nuance et voix). Compile et relit visuellement les PNG, choisit une modalité (TikZ, Mermaid, frise, big number, carte), applique un deai-latex étendu, et score chaque version avec veto anti-moyennisation.

Compétences : améliorer une slide précise d'un fichier .tex (titre, identifiant ou numéro) ; enrichir vers la singularité plutôt qu'alléger vers la généralité ; passer une boucle propreté visuelle (débordements, collisions, veuves, footer)

### supp-check

Vérification d'alignement entre un manuscrit principal et ses supplementary materials. Itère sur chaque table/figure/fichier supplémentaire, comprend son rôle, parcourt le cahier_de_labo.md pour reconstruire sa genèse et ce qui s'est passé depuis, puis détecte les divergences avec le main.tex et avec la vérité la plus récente. Les dernières entrées du cahier font autorité : si un supplément est obsolète, le skill propose de le retravailler, de réécrire le main, de lancer une expérience d'arbitrage ou de remettre l'ensemble en question.

Compétences : préparer une soumission ou resoumission ; après toute modification de la BDD ou des scripts ; après correction d'un bug influençant les chiffres ; après mise à jour d'une méthode ou d'un outil ; avant envoi de révisions à un relecteur

### synthesize-research

Synthétise de la recherche utilisateur (entretiens, sondages, retours) en insights structurés.

Compétences : un tas de notes d'entretiens, réponses de sondage ou tickets de support à comprendre ; extraire des thèmes et classer les résultats par fréquence et impact ; transformer des retours bruts en recommandations de feuille de route

### theme-factory

Boîte à outils pour appliquer un thème à des artefacts (slides, docs, reportings, pages web HTML). Propose 10 thèmes pré-réglés (couleurs/polices) applicables à un artefact existant, ou génère un nouveau thème à la volée.

Compétences : styliser un artefact existant avec un thème cohérent ; générer une palette et une typographie sur mesure

### zenodo-deposit

Dépôt automatique d'un artefact de recherche (code, données, harnais d'évaluation, supplementary materials) sur Zenodo, pour obtenir un DOI citable à insérer dans un manuscrit. Le token Zenodo est configuré une seule fois puis réutilisé pour tous les articles. Crée un brouillon, téléverse l'archive, écrit les métadonnées (titre, auteurs, ORCID, licence extraits du .tex), réserve le DOI et peut remplacer le placeholder dans le main.tex. La publication (irréversible) reste une étape explicite confirmée par l'auteur.

Compétences :  déposer sur Zenodo  ;  obtenir un DOI  ;  publier le harnais / les supplementary  ;  activer le DOI Zenodo de l'article  ; ou taper /zenodo-deposit

## Skills partagés (via symlink)

Documentés sur la page de leur plugin d'origine.

| Skill | Origine |
|-------|---------|
| [create-viz](ops.md#create-viz) | `ops` |
| [geo-map](bio_population_genetics.md#geo-map) | `bio_population_genetics` |
| [matplotlib](ia.md#matplotlib) | `ia` |
| [matplotlib-pro](ia.md#matplotlib-pro) | `ia` |
| [read-scientific-pdf](bio_population_genetics.md#read-scientific-pdf) | `bio_population_genetics` |
| [seaborn](bio_population_genetics.md#seaborn) | `bio_population_genetics` |

