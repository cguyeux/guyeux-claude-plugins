# Plugin `litterature`

> Academic literature-mining toolkit: full-text and supplementary-table recall, open-access resolution, systematic review synthesis, biomedical entity annotation. Guyeux group (FEMTO-ST), peer-reviewed research, transverse to all domains.

Skills propres (canoniques) : **9** ; skills partagés utilisés (symlinks) : **0**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [bioc-pmc](#bioc-pmc) ; [europe-pmc](#europe-pmc) ; [lit-review](#lit-review) ; [literature-access](#literature-access) ; [openalex](#openalex) ; [pubmed-database](#pubmed-database) ; [pubtator](#pubtator) ; [supp-tables](#supp-tables) ; [synthesize-research](#synthesize-research)

### bioc-pmc

BioC-PMC, le sous-ensemble Open Access et manuscrits d'auteur de PubMed Central au format BioC (NCBI/NLM) : environ 3 millions d'articles biomedicaux en texte integral avec sections structurees (titre, resume, corps, figures, tableaux) en XML ou JSON, optimise pour les pipelines de TAL. Pour les flux TB limites aux resumes, preferer tbmonitor-papers (environ 190 000 resumes TB preindexes, SQL en moins d'une seconde) ; BioC-PMC est le bon outil des que le corps du texte, les figures ou les tableaux sont necessaires.

Compétences : construire un corpus plein texte pour le text mining MTBC ou M ; bovis ; recuperer des sections structurees pour de la reconnaissance d'entites nommees ou de l'extraction de relations ; telecharger en masse des articles PMC OA en format lisible par machine ; alimenter PubTator ou un modele de NER

### europe-pmc

Interroge Europe PMC (EMBL-EBI), le depot europeen de litterature biomedicale couvrant les resumes PubMed, le texte integral PMC, les preprints de plus de 32 serveurs (bioRxiv, medRxiv, Research Square), livres, brevets, recommandations et financements. Fournit une API REST pour la recherche, la recuperation du texte integral et des annotations de text mining precalculees (genes, maladies, molecules, organismes, termes GO, numeros d'acces). Pour la litterature TB limitee a PubMed sans preprints, tbmonitor-papers est plus rapide.

Compétences : chercher de la litterature biomedicale y compris des preprints ; recuperer le texte integral d'un article en acces ouvert ; recuperer des annotations en JSON ou XML ; relier des publications a des numeros d'acces de donnees (ENA, UniProt, ChEMBL, PDB) ; decouvrir des articles lies via le graphe de citations

### lit-review

Revue de littérature scientifique systématique et incrémentale. Recherche, lit, synthétise et stocke dans litterature_review/. À chaque relance, approfondit de nouvelles directions ou enrichit les sujets existants. Maintient un BibTeX cumulatif. Pour les sujets TB/MTBC, préfère tbmonitor-papers (corpus PubMed TB pré-indexé, réponses sub-seconde) avant l'API PubMed live. Le mode --wide active le backward chaining sur les références et la recherche pré-nomenclature.

Compétences : construire une revue de littérature sur un sujet ; approfondir une revue existante ; préparer un état de l'art pour un article ou une demande de financement ; repérer des lacunes ; découvrir des travaux précurseurs antérieurs à la terminologie actuelle

### literature-access

Maximise l'accès LÉGAL au plein texte scientifique en cascade, pour combler le trou entre « résumé » (tbmonitor, abstracts) et « article payant ». Deux moteurs : recall par le CORPS du texte (trouver les articles dont le corps mentionne un gène / locus tag / méthode, pas seulement le résumé, via europepmc_fulltext.py search) et résolution d'accès (donné un DOI, rendre la meilleure voie légale : Europe PMC OA lisible ici, Unpaywall green/gold OA, OpenAlex, Semantic Scholar, puis hand-off vers TDM institutionnel / bibliothèque sous licence / contact auteur). Ne contourne AUCUN paywall

Compétences : un gène ressort « sans littérature » alors qu'il est cité dans des articles OA ; vérifier qu'un terme est réellement absent de la littérature ; obtenir le plein texte d'un DOI pour claim-check/bib-check/lit-review ; construire une revue à haut rappel

### openalex

Interroge OpenAlex, le graphe de connaissances savant entièrement ouvert (307 M travaux, 118 M auteurs, 124k institutions, 65k concepts) publié par OurResearch comme successeur de Microsoft Academic Graph. API REST gratuite, métadonnées CC0 et dumps en masse. Substrat bibliométrique de référence pour les revues de littérature, l'analyse de réseaux de co-auteurs et la découverte par concept, complémentaire de PubMed/Europe PMC et de Google Scholar.

Compétences : construire une revue de littérature depuis une requête thématique ; cartographier les réseaux de co-signature autour d'une lignée MTBC ou d'un article ; lister les publications d'un labo ou chercheur ; résoudre des identifiants d'institution ; calculer des métriques de citation sans accès Web of Science ; enrichir une bibliographie de tags de concepts

### pubmed-database

Accès direct à l'API REST de PubMed : requêtes booléennes/MeSH avancées, API E-utilities, traitement par lots, gestion des citations. Pour les workflows Python, préférer biopython (Bio.Entrez). Pour la littérature TB/MTBC spécifiquement, préférer tbmonitor-papers (SQL sub-seconde sur un corpus pré-indexé de ~190k articles PubMed TB avec MeSH/mots-clés/auteurs en JSON).

Compétences : sujets non-TB ; travail HTTP/REST direct ; implémentations d'API personnalisées

### pubtator

Interroge PubTator 3.0 / PubTator Central (NCBI BioNLP), service de référence d'annotations d'entités biomédicales pré-calculées sur les résumés PubMed et le texte intégral PMC. Utilise un NER de pointe (AIONER) pour étiqueter six types d'entités : gènes/protéines, maladies, chimie, espèces, variants génétiques et lignées cellulaires, avec extraction de relations en v3. Évite d'entraîner son propre NER biomédical.

Compétences : pré-annoter des résumés ou textes intégraux MTBC avec des entités standardisées ; extraire des mentions de gènes/variants/médicaments d'un article TB ; construire un graphe d'associations gène-maladie depuis la littérature ; accélérer un pipeline de fouille de texte ; Pour des corpus TB seuls, bâtir la liste d'abstracts avec tbmonitor-papers avant de passer les PMID à PubTator

### supp-tables

Cherche un gène, un locus tag, une accession ou tout motif dans les TABLES SUPPLÉMENTAIRES d'articles scientifiques, .xlsx, .csv, .docx qu'aucun moteur plein texte n'indexe. Comble le troisième angle mort du rappel bibliographique, après l'écart résumé/plein texte et le gène rebaptisé : un gène peut être ABSENT du corps de tous les articles pertinents et PRÉSENT dans les tables de plusieurs d'entre eux. Récupère par Europe PMC, avec repli obligatoire par le préprint bioRxiv si l'article n'est pas en accès ouvert, et rend chaque occurrence avec ses EN-TÊTES de colonnes. Porte son propre garde-fou : `rank` situe une valeur trouvée dans la distribution de sa propre table, parce qu'une ligne trouvée n'est pas un résultat

Compétences : un gène ressort « sans littérature » alors que des jeux protéomiques, des cribles CRISPRi, des tables d'essentialité ou des sorties de GWAS le contiennent ; vérifier qu'un terme est réellement absent ; instruire un gène dark ; préparer un claim-check sur une donnée publiée

### synthesize-research

Synthetise un ensemble de materiaux qualitatifs en constats structures et hierarchises par force de preuve : analyse thematique, cartographie par affinites, triangulation entre sources, et integration du qualitatif avec le quantitatif. Distingue explicitement deux registres, scientifique et produit, qui partagent les methodes mais pas les livrables. N'est ni la verification des affirmations d'un manuscrit (claim-check) ni une recherche bibliographique ciblee (lit-review), qui partent de la question et non du corpus.

Compétences : de nombreuses sources separees portent sur une meme question et il faut en degager les themes : articles lus pour une revue, notes d'entretiens d'experts ou de parties prenantes, reponses libres de questionnaire, commentaires de relecteurs sur plusieurs tours, retours de terrain
