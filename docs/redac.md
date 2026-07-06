# Plugin `redac`

> Un plugin pour la rédaction d'articles et de projets

## Rôle dans un projet M. tuberculosis

Rédaction et contrôle qualité du manuscrit M. tuberculosis : mise en forme LaTeX, vérification des affirmations et des références, nettoyage stylistique, réponse aux relecteurs, dépôt Zenodo et pont Overleaf.

Skills propres (canoniques) : **29** ; skills partagés utilisés (symlinks) : **6**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [beamer-slides](#beamer-slides) ; [bib-check](#bib-check) ; [biblatex](#biblatex) ; [claim-check](#claim-check) ; [cv](#cv) ; [deai-latex](#deai-latex) ; [docs-latex](#docs-latex) ; [fig-check](#fig-check) ; [grant-proposal](#grant-proposal) ; [humanizer](#humanizer) ; [latex-build](#latex-build) ; [latex-document](#latex-document) ; [latex-formatting](#latex-formatting) ; [latex-paper-en](#latex-paper-en) ; [latex-posters](#latex-posters) ; [latex-tables](#latex-tables) ; [latex-writing](#latex-writing) ; [lit-review](#lit-review) ; [manuscript-review](#manuscript-review) ; [overleaf-bridge](#overleaf-bridge) ; [pdf-to-latex](#pdf-to-latex) ; [plotly](#plotly) ; [reviewer-response](#reviewer-response) ; [slide-design](#slide-design) ; [slide-polish](#slide-polish) ; [supp-check](#supp-check) ; [synthesize-research](#synthesize-research) ; [theme-factory](#theme-factory) ; [zenodo-deposit](#zenodo-deposit)

### beamer-slides

Generate professional Beamer/LaTeX presentation slides from research work. Analyzes main.tex, data, and figures to build a self-contained, narrative-driven, pedagogical scientific presentation.

### bib-check

Verification exhaustive des references BibTeX d'un article LaTeX. Verifie l'existence reelle de chaque reference en ligne, la coherence des metadonnees (auteurs, titre, annee, journal), la pertinence des citations dans leur contexte, et detecte les doublons semantiques. Outil anti-hallucinations. Pour les references TB / MTBC, le skill `tbmonitor-papers` permet de valider en SQL sub-seconde l'existence d'une reference (DOI ou titre) contre le corpus pre-indexe de ~190 000 papiers PubMed TB, avant de tomber sur WebFetch / OpenAlex / CrossRef. Marque chaque reference verifiee pour ne pas la re-verifier.

### biblatex

LaTeX biblatex/biber packages for modern bibliography management

Compétences : helping users cite references, manage .bib files, choose citation styles, or troubleshoot bibliography compilation

### claim-check

Extraction et verification systematique des affirmations scientifiques d'un article. Classe les claims par priorite (structurants -> annexes), verifie via bioinfo, BDD, ou litterature. Pour la verification litterature TB / MTBC : interroger en priorite tbmonitor (corpus pre-indexe de ~190 000 papiers PubMed TB, requetable en SQL sub-seconde) avant de tomber sur WebSearch / WebFetch. Maintient un registre claim_check.md avec dates de verification. Re-verifie uniquement les claims non verifies ou anciens.

### cv

Extracts relevant information from Christophe Guyeux's LaTeX CV to support writing project proposals, grant applications (ANR, ERC, Horizon, LabCom), job applications, recommendation letters, research summaries, or any document requiring accurate self-presentation

Compétences : whenever the user is drafting a project proposal, candidature dossier, cover letter, research summary, list of publications, supervision record, funding history, or needs to cite specific CV elements (publications, funding, impact metrics, co-authors) ; Trigger even when the user doesn't say "CV" explicitly, if they're writing something professional about their research, teaching, or supervision, this skill provides the sourced material they need

### deai-latex

Applique les regles de style scientifique a un article LaTeX : supprime le gras abusif, convertit les listes a puces en prose, fusionne les micro-sections, verifie les acronymes (definis une seule fois), met les noms d'especes en italique, elimine les cliches rédactionnels et ameliore la coherence des temps verbaux. Produit un manuscrit conforme aux conventions des revues.

### docs-latex

Convert Markdown documents to professional LaTeX with TikZ visualizations and compile to PDF

Compétences : the user wants to create a presentation-quality PDF from a Markdown document, generate a professional report with diagrams, or convert documentation to print-ready format

### fig-check

Verification visuelle systematique des figures d'un article scientifique via les capacites multimodales. Pour chaque \includegraphics du manuscrit : lit l'image, evalue lisibilite, resolution, chevauchements, taille des textes, clarte des fleches, coherence de palette, correspondance figure/legende. Maintient un registre fig_check.md avec statut par figure. Propose (et applique en mode --fix) des corrections via regeneration du script source quand il est detectable

Compétences : preparation d'une soumission ou d'une resoumission, apres modification de figures, verification avant impression d'un poster, debogage d'une figure illisible en PDF final

### grant-proposal

Aide à la rédaction de demandes de financement de recherche adaptées aux formats français et européens : ANR (AAPG, LabCom, PRCI), Horizon Europe, Interreg, PHC (Hubert Curien), ARS, AMI, Région, UMLP/Sunergia. Ce skill connaît la structure exacte de chaque appel, les contraintes de formatage, et s'appuie sur les propositions précédentes de l'utilisateur comme modèles

Compétences : l'utilisateur rédige un projet de recherche, une demande de financement, un pré-projet, répond à un appel à projets, ou a besoin de reformuler/améliorer une section de proposition existante ; Trigger phrases : "rédiger un projet ANR", "préparer une soumission Horizon", "écrire le pré-projet Interreg", "section impact pour le PHC", "budget du projet", "work packages", "appel à projets", "grant proposal", "write a proposal

### humanizer

Remove AI writing patterns from text to make it sound natural and human. Eliminates AI-isms: inflated significance, em-dash overuse, rule-of-three, sycophantic tone, filler phrases, boldface abuse, vague attributions. Adds voice, specificity, and rhythm

Compétences : humanizing AI-generated text, removing ChatGPT patterns, making writing sound less robotic, or editing text for Wikipedia/publication

### latex-build

LaTeX builds with latexmk and live preview

Compétences : latexmk, LaTeX build, live preview, compilation

### latex-document

Universal LaTeX document skill: create, compile, and convert any document to professional PDF with PNG previews. Supports resumes, reports, cover letters, invoices, academic papers, theses/dissertations, academic CVs, presentations (Beamer), scientific posters, formal letters, exams/quizzes, books, cheat sheets, reference cards, exam formula sheets, fillable PDF forms (hyperref form fields), conditional content (etoolbox toggles), mail merge from CSV/JSON (Jinja2 templates), version diffing (latexdiff), charts (pgfplots + matplotlib), tables (booktabs + CSV import), images (TikZ), Mermaid diagrams, AI-generated images, watermarks, landscape pages, bibliography/citations (BibTeX/biblatex), multi-language/CJK (auto XeLaTeX), algorithms/pseudocode, colored boxes (tcolorbox), SI units (siunitx), Pandoc format conversion (Markdown/DOCX/HTML ↔ LaTeX), and PDF-to-LaTeX conversion of handwritten or printed documents (math, business, legal, general). Compile script supports pdflatex, xelatex, lualatex with auto-detection, latexmk backend, texfot log filtering, PDF/A output, and verbosity control (--verbose/--quiet). Empirically optimized scaling: single agent 1-10 pages, split 11-20, batch-7 pipeline 21+

Compétences : user asks to: (1) create a resume/CV/cover letter, (2) write a LaTeX document, (3) create PDF with tables/charts/images, (4) compile a .tex file, (5) make a report/invoice/presentation, (6) anything involving LaTeX or pdflatex, (7) convert/OCR a PDF to LaTeX, (8) convert handwritten notes, (9) create charts/graphs/diagrams, (10) create slides, (11) write a thesis or dissertation, (12) create an academic CV, (13) create a poster, (14) create an exam/quiz, (15) create a book, (16) convert between document formats (Markdown, DOCX, HTML to/from LaTeX), (17) generate Mermaid diagrams for LaTeX, (18) create a formal business letter, (19) create a cheat sheet or reference card, (20) create an exam formula sheet or crib sheet, (21) condense lecture notes/PDFs into a cheat sheet, (22) create a fillable PDF form with text fields/checkboxes/dropdowns, (23) create a document with conditional content/toggles (show/hide sections), (24) generate batch/mail-merge documents from CSV/JSON data, (25) create a version diff PDF (latexdiff) highlighting changes between documents, (26) create a homework or assignment submission with problems and solutions, (27) create a lab report with data tables, graphs, and error analysis, (28) encrypt or password-protect a PDF, (29) merge multiple PDFs into one, (30) optimize/compress a PDF for web or email, (31) lint or check a LaTeX document for common issues, (32) count words in a LaTeX document, (33) analyze document statistics (figures, tables, citations), (34) fetch BibTeX from a DOI, (35) convert a Graphviz .dot file to PDF/PNG, (36) convert a PlantUML .puml file to PDF/PNG, (37) create a one-pager/fact sheet/executive summary, (38) create a datasheet or product specification sheet, (39) extract pages from a PDF (page ranges, odd/even), (40) check LaTeX package availability before compiling, (41) analyze citations and cross-reference with .bib files, (42) debug LaTeX compilation errors, (43) make a document accessible (PDF/A, tagged PDF), (44) create lecture notes or course handouts, (45) fill an existing PDF form (fillable fields or non-fillable with annotations), (46) extract text or tables from a PDF (pdfplumber, pypdf), (47) OCR a scanned PDF to text (pytesseract), (48) create a PDF programmatically with reportlab (Canvas, Platypus), (49) rotate or crop PDF pages (pypdf), (50) add a watermark to an existing PDF, (51) extract metadata from a PDF (title, author, subject)

### latex-formatting

Handle LaTeX formatting, templates, and styling for academic papers. Set up conference templates (ICML, ICLR, NeurIPS, AAAI, ACL), fix formatting issues, manage packages, and ensure venue-specific compliance

Compétences : the user needs to set up a paper template, fix LaTeX formatting, or prepare for submission

### latex-paper-en

English LaTeX academic paper assistant for existing `.tex` projects

Compétences : whenever the user wants to compile, lint, audit, or improve an English LaTeX conference or journal paper such as IEEE, ACM, Springer, NeurIPS, or ICML submissions ; Trigger even when the user only mentions one paper issue, such as bibliography errors, grammar cleanup, sentence splitting, logic review, expression polishing, translation, title optimization, figure checks, pseudocode review, algorithm block cleanup, de-AI editing, or experiment-section review ; Also trigger for "proofread my paper", "fix my LaTeX", "prepare for submission", "check my manuscript", "improve my writing", `algorithm2e`, `algorithmicx`, `algpseudocodex`, `Require/Ensure`, or "Algorithm 1" when the user has a .tex file

### latex-posters

Create professional research posters in LaTeX using beamerposter, tikzposter, or baposter. Support for conference presentations, academic posters, and scientific communication. Includes layout design, color schemes, multi-column formats, figure integration, and poster-specific best practices for visual communication.

### latex-tables

LaTeX tables with tabularray package

Compétences : LaTeX table, tabularray, fixed-width columns, table alignment

### latex-writing

Guide LaTeX document authoring following best practices and proper semantic markup. Use proactively when: (1) writing or editing .tex files, (2) writing or editing .nw literate programming files, (3) literate-programming skill is active and working with .nw files, (4) user mentions LaTeX, BibTeX, or document formatting, (5) reviewing LaTeX code quality. Ensures proper use of semantic environments (description vs itemize), csquotes (\enquote{} not ``...''), and cleveref (\cref{} not \S\ref{}).

### lit-review

Revue de litterature scientifique systematique et incrementale. Recherche, lit, synthetise et stocke dans litterature_review/. A chaque relance, approfondit dans de nouvelles directions ou enrichit les sujets existants. Maintient un BibTeX cumulatif. Integre pubmed-database pour les recherches PubMed. Pour les sujets TB / MTBC, prefere le skill `tbmonitor-papers` (corpus PubMed TB pre-indexe : ~190 000 papiers avec MeSH/auteurs/keywords en JSON, reponses sub-seconde) avant de tomber sur l'API PubMed live. Le mode --wide active la recherche elargie : backward chaining systematique sur les refs de chaque article cle, recherche pre-nomenclature (concepts existant avant d'avoir ete nommes), et expansion des termes historiques

Compétences : building a literature review on a topic, deepening an existing review, preparing state-of-the-art for a paper or grant, finding gaps in the literature, discovering precursor work that predates current terminology

### manuscript-review

Peer review of a scientific manuscript as for a high-impact journal. Reads the full paper (LaTeX or text), evaluates structure, methodology, statistics, terminology, figures, references, and produces a structured review in French with severity-ranked recommendations. For TB / MTBC manuscripts, validates the state-of-the-art and citation completeness against `tbmonitor-papers` (~190k pre-indexed PubMed TB abstracts, sub-second SQL access), surfaces any major recent publication missed by the authors.

### overleaf-bridge

Synchronise a local article/ repository with an Overleaf project through Overleaf's official Git integration (git-bridge, git.overleaf.com). Deposit a new manuscript, pull the latest co-author edits, view the diff, and collect co-author comments left in the .tex for processing. Standard git on the official remote, no MCP server, no unofficial API, no scraping.

### pdf-to-latex

Reconstruct compilable LaTeX source code from a PDF document. Analyzes structure, layout, fonts, tables, equations, and figures to produce a visually faithful .tex file. Uses markitdown for text extraction then rebuilds document class, packages, geometry, and content

Compétences : reverse-engineering a PDF to LaTeX, reproducing a paper template, editing an article without source files, or reconstructing institutional documents

### plotly

A high-level interactive graphing library for Python. Ideal for web-based visualizations, 3D plots, and complex interactive dashboards. Built on plotly.js, it allows users to zoom, pan, and hover over data points in a browser-based environment. Use for interactive charts, web applications, Jupyter notebooks, 3D data visualization, geographic maps, financial charts, animations, time-series analysis, and building production-ready dashboards with Dash.

### reviewer-response

Systematic point-by-point response to a manuscript review. Parses reviewer comments into individual tasks, critically evaluates each (agree/disagree), plans and executes analyses (bioinfo, literature, statistics) in experiments/, improves the manuscript, and produces a timestamped rebuttal letter in review/. When a reviewer asks for additional citations on a TB / MTBC topic, use the `tbmonitor-papers` skill first (~190 000 PubMed TB papers, sub-second SQL access with MeSH / authors / keywords as JSON) before falling back to lit-review or WebSearch. Use /reviewer-response review/file.md to start, /reviewer-response next to advance, /reviewer-response status to check progress, /reviewer-response R05 to jump to a specific remark.

### slide-design

Transform a short description of what you want to say into 1 to a few editorial-grade slides. The skill enforces a design system (palette, typography, grid), reasons about the narrative, proposes several structural options with explicit editorial references (NYT Graphics, Bloomberg, Pudding, Tufte, Nature Methods...), requires at least one option with a strong visual signature (TikZ schema, big number, full-bleed image, sparkline), prefers schemas / timelines / diagrams / illustrations over plain text, looks for reusable figures in local project directories, evaluates whether web image search is relevant, delegates maps to `geo-map` and charts to `create-viz` / `seaborn`, matches the host presentation's style when slides are inserted into an existing deck, and **systematically compiles a preview, reads the PNG and critiques it visually before delivery**

Compétences : when the user types `/slide-design`, asks to "make a slide / two slides / a couple of slides" for an idea, says "I need a slide that says...", "design a slide on X", "comment je présenterais X en une slide", "fais-moi 2 slides sur Y", or otherwise needs to convert a verbal idea into polished slide material rather than generating an entire presentation

### slide-polish

_(pas de description)_

### supp-check

Verification d'alignement entre un manuscrit principal et ses supplementary materials. Itere sur chaque table/figure/fichier supplementaire, comprend son role, parcourt le cahier_de_labo.md pour reconstruire sa genese et ce qui s'est passe depuis, puis detecte les divergences avec le main.tex et avec la verite la plus recente. Les dernieres entrees du cahier font autorite : si un supplementary est devenu obsolete (souche ecartee, bioproject ajoute, bug corrige changeant les SPDI, nouvelle version TBannotator), le skill propose de retravailler le supplementary, de reecrire le main, de lancer une experience d'arbitrage, ou de remettre en question l'ensemble

Compétences : preparation d'une soumission ou resoumission, apres toute modification de la BDD ou des scripts d'analyse, apres correction d'un bug influencant les chiffres, apres mise a jour d'une methode ou d'un outil, avant envoi de revisions a un reviewer

### synthesize-research

Synthesize user research from interviews, surveys, and feedback into structured insights

Compétences : you have a pile of interview notes, survey responses, or support tickets to make sense of, need to extract themes and rank findings by frequency and impact, or want to turn raw feedback into roadmap recommendations

### theme-factory

Toolkit for styling artifacts with a theme. These artifacts can be slides, docs, reportings, HTML landing pages, etc. There are 10 pre-set themes with colors/fonts that you can apply to any artifact that has been creating, or can generate a new theme on-the-fly.

### zenodo-deposit

Dépôt automatique d'un artefact de recherche (code, données, harnais d'évaluation, supplementary materials) sur Zenodo, pour obtenir un DOI citable à insérer dans un manuscrit. Le token Zenodo est configuré UNE SEULE FOIS puis réutilisé pour tous les articles (stocké dans ~/.config/zenodo/, jamais recréé). Crée un brouillon, téléverse l'archive, écrit les métadonnées (titre, auteurs, ORCID, licence extraits du .tex), RÉSERVE le DOI, et peut remplacer le placeholder DOI dans le main.tex. La publication (irréversible) reste une étape explicite, confirmée par l'auteur

Compétences : l'utilisateur veut « déposer sur Zenodo », « obtenir un DOI », « publier le harnais / les supplementary », « activer le DOI Zenodo de l'article », ou tape /zenodo-deposit

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

