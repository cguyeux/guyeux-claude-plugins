# Plugin `diffusion`

> Submission and dissemination of a finished manuscript: journal targeting, reviewer response, conference posters and talks, Zenodo deposit. Guyeux group (FEMTO-ST), phase 4 of the research cycle.

Skills propres (canoniques) : **9** ; skills partagés utilisés (symlinks) : **0**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [beamer-slides](#beamer-slides) ; [cadrage-editorial](#cadrage-editorial) ; [latex-posters](#latex-posters) ; [reviewer-response](#reviewer-response) ; [slide-design](#slide-design) ; [slide-polish](#slide-polish) ; [soumission](#soumission) ; [theme-factory](#theme-factory) ; [zenodo-deposit](#zenodo-deposit)

### beamer-slides

Genere une presentation scientifique Beamer complete a partir de la matiere de recherche existante : lit main.tex, les donnees et les figures, puis construit un deck autonome, narratif et pedagogique. Pour une ou deux slides a partir d'une idee, utiliser slide-design ; pour retravailler une slide existante, slide-polish.

Compétences : l'utilisateur demande un expose, une presentation de seminaire ou de conference, un deck de soutenance, ou des slides couvrant tout un article ou tout un projet

### cadrage-editorial

Dernière passe avant de déposer un manuscrit, une fois la revue choisie : relire la VITRINE (titre, résumé, mots-clés, clôture d'introduction, première phrase de discussion, conclusion, lettre d'accompagnement) contre ce que cette revue publie réellement, pour qu'un travail de qualité ne soit pas refusé sur un malentendu de formulation. Mesure la forme réelle du corpus de la revue, simule le rejet éditorial par une instance indépendante qui ne voit que ce que l'éditeur lit, propose des retouches justifiées par un fait éditorial vérifié, et rend UN verdict daté dans `cadrage_editorial.md` : ALIGNE, RETOUCHER, CHANGER-DE-CIBLE ou ROUVRIR. Ne touche jamais aux Résultats ni aux Méthodes, et ne sauve pas une revue mal choisie

Compétences : la revue est arrêtée et qu'il reste à vérifier que le cadrage colle, quand on craint un desk-reject de principe, quand on hésite sur le titre ou le résumé pour une cible donnée, quand on recadre après un rejet pour une nouvelle revue, ou taper /cadrage-editorial

### latex-posters

Cree des posters de recherche en LaTeX avec beamerposter, tikzposter ou baposter : mise en page et grilles de colonnes, palettes, integration des figures, et regles propres au poster sur la taille de police, la distance de lecture et la hierarchie visuelle. Pour des slides utiliser beamer-slides, pour les figures elles-memes sci-figure.

Compétences : l'utilisateur demande un poster de conference ; mentionne un format A0 ou A1, beamerposter, tikzposter ou baposter ; veut transformer un article en poster

### reviewer-response

Reponse point par point systematique a une revue de manuscrit. Decoupe les commentaires des relecteurs en taches individuelles, evalue chacune de facon critique (accord ou desaccord), planifie et execute les analyses (bioinformatique, litterature, statistiques) dans experiments/, ameliore le manuscrit et produit une lettre de reponse datee dans review/. S'invoque avec review/fichier.md pour demarrer, next pour avancer, status pour l'avancement, R05 pour sauter a une remarque.

Compétences : des rapports de relecture sont arrives et il faut y repondre ; traiter une revision ; rediger une lettre de reponse

### slide-design

Transforme une courte description de ce que l'on veut dire en une a quelques slides de qualite editoriale. Impose un systeme graphique (palette, typographie, grille), raisonne sur la narration, propose plusieurs options structurelles avec des references editoriales explicites (NYT Graphics, Bloomberg, Pudding, Tufte, Nature Methods), exige au moins une option a signature visuelle forte, prefere schemas, frises et diagrammes au texte brut, reutilise les figures trouvees dans le projet, delegue les cartes a geo-map et les graphiques a sci-figure, s'aligne sur le style du deck hote, et compile systematiquement un apercu qu'il critique avant livraison.

Compétences : taper /slide-design ; demander une ou deux slides sur une idee ; dire j'ai besoin d'une slide qui dit ; ou fais-moi 2 slides sur Y ; transformer une idee verbale en matiere de slide plutot que generer une presentation entiere

### slide-polish

Amelioration ciblee d'une slide Beamer existante, sur le fond et sur la forme, avec une etape obligatoire de brassage large : relire la matiere du projet (cahier de labo, manuscrit, JOURNAL, claim-check) pour reconstruire la these pleine et eviter la moyennisation par polissage, ce defaut classique qui rend une slide moyenne plus belle en sacrifiant specificite, nuance et voix. Compile et lit visuellement les PNG, choisit une modalite (TikZ, Mermaid, frise, big number, carte via geo-map), applique deai-latex etendu, score chaque version sur 16 points avec veto anti-moyennisation, itere tant que le score progresse, puis enchaine une boucle de proprete visuelle sur crops haute resolution et un test final de voix scientifique.

Compétences : taper /slide-polish ; demander d'ameliorer, de retravailler ou de rendre meilleure une slide precise existante, plutot que d'en creer une nouvelle ou de generer un deck entier

### soumission

Gère tout le cycle de soumission d'un article scientifique, de la préparation au suivi, avec exécution externe seulement sur demande explicite : choisir la revue cible (base de revues avec scope, contraintes de longueur, frais réels, facteur d'impact et délai de première décision), contrôler que le manuscrit est prêt (dont la version française main_fr.tex), se connecter aux portails éditeurs par ORCID, déposer le préprint sur bioRxiv/medRxiv/arXiv et le code sur le GitHub centralisateur, remplir le formulaire de soumission, tenir le registre central des soumissions (qui, où, quand, statut), faire après chaque soumission le point d'état de tous les manuscrits (déposé, rejeté, en révision, préparé mais jamais soumis) et reprendre ce qui cloche, et en tirer les enseignements des rejets

Compétences : l'utilisateur veut « soumettre un article », « choisir une revue », « où soumettre ce papier », « préparer la soumission », « déposer le préprint », « où en sont mes soumissions », « le journal a répondu », « on m'a rejeté, où resoumettre », « fais le point sur mes soumissions », ou tape /soumission

### theme-factory

Applique un theme visuel coherent (couleurs, typographie, espacement) a un artefact : slides, documents, rapports, pages HTML. Dix themes preetablis sont disponibles et un nouveau theme peut etre genere a la volee. Pour le travail de slide scientifique utiliser slide-design, et pour les gabarits de figures de revue sci-figure.

Compétences : restyler ou harmoniser un artefact existant ; obtenir une autre apparence pour un deck ou une page ; demander une palette et un appariement de polices sur mesure

### zenodo-deposit

Dépôt automatique d'un artefact de recherche (code, données, harnais d'évaluation, supplementary materials) sur Zenodo, pour obtenir un DOI citable à insérer dans un manuscrit. Le token Zenodo est configuré une seule fois puis réutilisé pour tous les articles. Crée un brouillon, téléverse l'archive, écrit les métadonnées (titre, auteurs, ORCID, licence extraits du .tex), réserve le DOI et peut remplacer le placeholder dans le main.tex. La publication (irréversible) reste une étape explicite confirmée par l'auteur.

Compétences :  déposer sur Zenodo  ;  obtenir un DOI  ;  publier le harnais / les supplementary  ;  activer le DOI Zenodo de l'article  ; ou taper /zenodo-deposit
