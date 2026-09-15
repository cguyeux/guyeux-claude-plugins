# Plugin `structure`

> Academic research toolkit for structural bioinformatics: protein structure prediction and complex modelling (Boltz, ESM Atlas), pocket detection, active-site validation, small-molecule handling. Guyeux group (FEMTO-ST), peer-reviewed research.

Skills propres (canoniques) : **6** ; skills partagés utilisés (symlinks) : **0**.

[Retour à l'index de la documentation](README.md)

## Skills propres

Sommaire : [active-site-check](#active-site-check) ; [boltz](#boltz) ; [esm-atlas-cli](#esm-atlas-cli) ; [foldseek](#foldseek) ; [pocket-detection](#pocket-detection) ; [rdkit](#rdkit)

### active-site-check

Boîte à outils de recherche académique (groupe Guyeux, FEMTO-ST). Valide une requalification d'enzyme « même repli → enzyme active » en vérifiant que les résidus catalytiques de l'enzyme M-CSA (Mechanism and Catalytic Site Atlas, EBI) appariée par Foldseek sont bien alignés et conservés dans la protéine requête. C'est la brique de rigueur qui manque à un transfert de fonction purement structural : un repli partagé n'implique pas un site actif fonctionnel.

Compétences : un gène « hypothetical »/dark du MTBC a un hit Foldseek vers une enzyme connue et il faut trancher « enzyme active vs simple homologie de repli » avant d'écrire une fonction ; annoter un protéome bactérien par structure en graduant la confiance des requalifications enzymatiques ; répondre à un relecteur demandant des preuves de site actif

### boltz

Boite a outils de recherche academique (groupe Guyeux, FEMTO-ST), bio-informatique structurale evaluee par les pairs : predit EN LOCAL des complexes biomoleculaires (multimeres, ions metalliques, ligands) avec Boltz-2, sans compte ni GPU (inference sur processeur), la ou AlphaFold Server n'est pas automatisable. Fournit la recette d'installation validee, l'ecriture des entrees YAML, la reutilisation d'un MSA deja produit, la lecture correcte des sorties (le schema Boltz differe du schema AF3) et les garde-fous d'interpretation.

Compétences : tester une interaction ou une homo-oligomerisation ; savoir si un site metallique est complete en trans ; cribler un ligand ou un substrat candidat ; refaire une prediction de complexe sans solliciter l'utilisateur

### esm-atlas-cli

Boîte à outils académique (groupe Guyeux, FEMTO-ST) pour l'évolution des protéines : client Python résilient de l'API Protein Atlas (EvolutionaryScale × BioHub), qui expose les features d'autoencodeur parcimonieux (SAE) d'ESMC et les structures ESMFold2 sur 6,8 milliards de protéines. Recherche par hash de contenu, par similarité de séquence, interprétation des features SAE, métadonnées de cluster et récupération de structures 3D, avec cache disque et repli gracieux quand l'API alpha est dégradée.

Compétences : traduire une séquence protéique en résumé de fonction biologique ; récupérer une structure prédite ; trouver des homologues dans l'espace ESM ; comparer deux séquences (sauvage vs variant) par différence de features SAE

### foldseek

Academic research toolkit for peer-reviewed structural bioinformatics in the Guyeux group (FEMTO-ST). This skill should be used when the user asks to search a protein structure with Foldseek, compare AlphaFold or ESMFold models against PDB, AlphaFold DB or CATH, investigate a structurally conserved dark gene, interpret Foldseek E-values and TM-scores, or cluster predicted protein structures without overclaiming molecular function.

### pocket-detection

Academic research toolkit (Guyeux group, FEMTO-ST) : détection de poches de liaison sur un modèle structural (P2Rank, fpocket, PocketMiner/AE-PocketMiner), installation locale validée (workarounds GCC 14+/16 et GPU→CPU inclus), et surtout le garde-fou qui prime sur les trois outils : aucun score de poche ne se lit en valeur absolue sans calibration par témoins positif ET négatif appariés à la population étudiée (taille, membranaire ou non, prédit ou expérimental)

Compétences : chercher un site de liaison candidat sur un gène dark bien replié, juger la druggabilité d'une cible, ou évaluer si l'absence de poche est un résultat négatif informatif ou un angle mort du détecteur (protéines courtes, membranaires)

### rdkit

Boîte à outils open source de chémoinformatique et de machine learning pour la découverte de médicaments, la manipulation moléculaire et le calcul de propriétés chimiques. RDKit gère les SMILES, les empreintes moléculaires, la recherche de sous-structures, la génération de conformères 3D, la modélisation de pharmacophores et le QSAR.

Compétences : travailler avec des structures chimiques ; propriétés drug-like, similarité moléculaire, criblage virtuel ou workflows de chimie computationnelle
