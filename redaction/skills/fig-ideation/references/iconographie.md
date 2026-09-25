# Iconographie libre — donner un corps aux schémas sans quitter LaTeX

Une figure conceptuelle faite uniquement de boîtes et de flèches reste abstraite. Un
schéma de saut d'hôte où l'on voit un humain, un bovin, un caprin et un phoque se lit
instantanément. Cette page dit où trouver ces éléments **légalement**, comment les faire
entrer dans une figure TikZ **sans Inkscape**, et quel piège de licence peut coûter une
soumission.

Outillé par `scripts/sci_icons.py`.

## Les deux sources retenues, et pourquoi celles-là

### PhyloPic — silhouettes d'organismes, résolues par taxid NCBI

Environ 10 000 silhouettes de tout le vivant, sous CC0, CC BY ou CC BY-SA. La propriété
décisive : **la résolution se fait par identifiant taxonomique NCBI**, pas par mot-clé.

```
python3 scripts/sci_icons.py taxon 9913 --out cattle --tint "#D55E00"
```

L'icône est donc indexée sur la même clé que la biologie du projet. Aucune ambiguïté de
nommage, aucune recherche textuelle à valider à la main.

Taxids utiles pour le MTBC : **9606** humain, **9913** bovin, **9925** caprin,
**9709** phocides, **1773** *M. tuberculosis*, **1765** *M. bovis*, **9615** chien,
**9796** cheval, **9838** camélidés.

Détail d'API à connaître : `/resolve/ncbi.nlm.nih.gov/taxid/<id>` répond **307** pour
injecter le numéro de build courant. Un client qui ne suit pas la redirection reçoit un
corps vide, sans erreur. Le style visuel (silhouette pleine, monochrome) est exactement
celui d'une figure scientifique, contrairement aux illustrations détaillées.

### Bioicons — icônes de biologie et de chimie

Environ 2 800 icônes SVG sous CC0, CC BY, MIT ou BSD, réparties en catégories dont
`Microbiology` (154), `Genetics`, `Genomics`, `Nucleic_acids`, `Cell_types`,
`Lab_apparatus`, `Viruses`, `Animals`.

```
python3 scripts/sci_icons.py search "bacteri" --category Microbiology
python3 scripts/sci_icons.py icon Bacillus_subtilis --out bacillus --tint "#0072B2"
```

Piège de chemin : l'index `icons.json` donne nom, catégorie, auteur et licence, mais le
fichier vit à `licence/Catégorie/Auteur/Nom.svg`. **L'auteur fait partie du chemin** ;
construire l'URL sans lui rend un 404 de 14 octets que `rsvg-convert` signale comme une
erreur de parsing XML, ce qui égare le diagnostic.

Bioicons ne couvre pas les mammifères hôtes (sa catégorie `Animals` vise les organismes
modèles). Pour un bovin, un caprin ou un phoque, c'est PhyloPic.

### BioRender — bibliothèque et brouillon assisté par prompt (MCP officiel, réévalué 2026-09-25)

Vérifié le 2026-09-25 depuis Claude Code (`/mcp`, authentification `biorender` réussie) : un
MCP **officiel** existe désormais (`mcp__biorender__*`), ce qui invalide en partie le verdict
« écarté » qui suivait ce paragraphe jusqu'ici — écrit avant que ce MCP existe, il ne vaut plus
tel quel. Deux outils, deux usages distincts.

**`search-biorender`** — recherche à la fois les fichiers propres/partagés de CG dans son
compte BioRender et la bibliothèque publique de gabarits, en une requête. Utile en deux temps :
(1) avant toute composition, vérifier qu'une figure équivalente n'existe pas déjà sur le
compte — même logique que le mode `triage` de ce skill, mais côté BioRender plutôt que côté
disque local ; (2) trouver un gabarit de départ (`templateId`) à passer en `canvasContext` de
`custom-figure-create-session`.

**`custom-figure-create-session`** — génère un brouillon de figure depuis un prompt texte, avec
un contexte optionnel (image, gabarit BioRender, figure existante). Asynchrone :
`custom-figure-get-preview-job` pour suivre l'état, puis `custom-figure-get-session` pour
récupérer l'aperçu — cet appel **finalise lui-même la génération** (l'appel à
`custom-figure-confirm-preview` est déprécié et inutile). La réponse porte une URL d'éditeur
BioRender : c'est CG, pas l'agent, qui l'ouvre pour composer, ajuster le texte et exporter la
version finale.

**Ce que cet outil apporte que Bioicons n'apporte pas.** Bioicons couvre des icônes plates,
isolées, par catégorie (`Microbiology`, `Cell_types`...). BioRender couvre des **scènes
composées** — cellule en coupe, voie de signalisation, cycle infectieux, interaction
hôte-pathogène — avec un vocabulaire iconographique bien plus riche que ce que Bioicons ou une
composition TikZ manuelle permettent d'assembler en un temps raisonnable. C'est précisément la
lacune que la famille **M** (mécanisme) du bestiaire rencontre le plus souvent sur un mécanisme
biologique réellement complexe, au-delà de ce qu'une frise de boîtes/flèches TikZ porte.

**Ce que cet outil n'apporte PAS, et qui borne son usage dans ce skill.**

1. **Aucun export scriptable.** Contrairement à `tikz_build.py`, rien dans ce MCP ne produit un
   PDF vectoriel ou un PNG haute résolution récupérable par l'agent : la finition et l'export
   restent un geste humain dans l'éditeur BioRender. Ce n'est donc **pas** un pipeline
   reproductible comme TikZ — à ne jamais présenter comme tel dans `fig_plan.md`.
2. **Droits de republication non vérifiés depuis l'agent.** Aucun outil de ce MCP ne renseigne
   le palier d'abonnement de CG ni les droits associés. La pratique documentée de BioRender
   (usage gratuit limité à un usage personnel, republication en article scientifique
   conditionnée à un abonnement payant, attribution « Created with BioRender.com » presque
   toujours requise en légende quel que soit le palier) reste la référence par défaut :
   **vérifier le palier d'abonnement de CG et la mention d'attribution avant toute figure
   destinée à un manuscrit soumis**, exactement comme le garde-fou de licence de
   PhyloPic/Bioicons ci-dessus.
3. **Usage réservé à l'esquisse assistée, pas au livrable.** `custom-figure-create-session` se
   positionne comme Mermaid/Graphviz dans la procédure du skill (étape 6, esquisse jetable) :
   utile pour trancher rapidement une composition biologique riche, jamais comme substitut à
   TikZ pour un schéma qui se réduit à des boîtes, des flèches ou une frise — ceux-là restent
   moins chers et plus contrôlables en TikZ.

Tant que ces trois réserves ne sont pas levées, une figure BioRender reste au statut
`esquissée` dans `fig_plan.md`, jamais `produite` : ce dernier état suppose que CG a confirmé
le palier de licence et fini l'export lui-même.

### Ce qui a été écarté, et pourquoi

**SMART / Servier Medical Art** (3 000 illustrations médicales, CC BY) est riche mais
orienté anatomie et clinique humaine, avec un style illustratif chargé qui convient au
poster et à la slide plus qu'à une figure de revue. À considérer pour un support de
communication, pas pour un manuscrit.

## La chaîne de conversion, sans Inkscape

Inkscape n'est pas installé et n'est pas nécessaire. `rsvg-convert` (paquet
`librsvg2-bin`, présent) produit du **PDF vectoriel** directement :

```
rsvg-convert -f pdf -h 300 -o icone.pdf icone.svg
```

Contrôle à faire une fois : si le PDF produit contient un objet `/Image`, c'est un bitmap
encapsulé et non du vectoriel. `sci_icons.py` le signale automatiquement.

### Le piège de la teinte

**Une silhouette porte sa propre couleur de remplissage** (`fill="#000000"`). Envelopper
l'inclusion d'un `\textcolor` n'a donc **aucun effet** :

```latex
\textcolor{orange}{\includegraphics[height=1cm]{cattle.pdf}}   % rend NOIR
```

La teinte se fait sur le SVG, avant conversion — c'est ce que fait `--tint` :

```
sed -E 's/fill="(?!none)[^"]*"/fill="#D55E00"/g' in.svg > out.svg
```

Symptôme reconnaissable : l'icône sort noire alors que le code dit le contraire. Ce n'est
pas un problème LaTeX, c'est que la couleur n'a pas été posée à la source.

## Le garde-fou qui compte : le share-alike

Sur les quatre hôtes du MTBC, **deux silhouettes PhyloPic sont en CC BY-SA 3.0**
(bovin et phocides, au moment de l'écriture). Le share-alike impose de rediffuser l'œuvre
dérivée sous la même licence : il **contamine la figure, donc potentiellement l'article**,
et plusieurs éditeurs qui exigent une cession exclusive le refusent.

```
python3 scripts/sci_icons.py taxon 9606 9913 9925 9709 --libre
```

`--libre` ne se contente pas d'écarter : il **cherche dans le même clade une silhouette
non share-alike** et le dit. L'image « primaire » d'un nœud PhyloPic est souvent en
CC BY-SA alors que le clade en porte d'autres en CC0 — écarter sans chercher priverait
d'une icône qui existe. Sur les quatre hôtes du MTBC, les deux images primaires en CC BY-SA
ont été remplacées automatiquement par une CC BY 4.0 et une CC0 du même clade. Sans
`--libre`, la licence de chaque icône est affichée et les SA sont marquées.

Dans tous les cas le script écrit `ATTRIBUTION_icons.tex`, prêt à reporter dans la légende
ou les remerciements. Ce fichier est **fusionné, jamais écrasé** : le flux naturel étant un
appel par icône, un fichier écrasé après huit appels serait incomplet **en ayant l'air
complet**, ce qui est exactement le défaut qu'il existe pour empêcher. **Une icône sans sa ligne d'attribution n'est pas utilisable** : une
figure d'article engage l'auteur sur les droits de tout ce qu'elle contient, y compris ce
qu'un agent y a déposé.

Trois questions à trancher avant d'inclure une icône, dans cet ordre : la licence
autorise-t-elle la republication commerciale (une revue en est une) ? impose-t-elle un
share-alike ? l'attribution est-elle écrite quelque part dans le manuscrit ?

## Quand une icône dessert la figure

Une icône n'est pas gratuite en charge cognitive. Trois cas où il faut s'en passer.

- **L'icône décorative.** Une éprouvette à côté du mot « expérience » n'ajoute rien.
  Même critère que pour une figure entière : si elle ne porte aucune information, elle
  se coupe.
- **L'icône trop détaillée.** Une illustration anatomique dans un schéma par ailleurs
  fait de traits crée une rupture de registre visible. Préférer les silhouettes pleines,
  qui se lisent à petite taille et survivent au noir et blanc.
- **L'icône qui affirme plus que les données.** Poser un bovin au bout d'une branche
  affirme que l'écotype est bovin. Si l'assignation d'hôte est inférée, la légende doit
  le dire, exactement comme pour une flèche de mécanisme.

## Patron de référence

`assets/patrons/saut_hote.tex` (archétype M4) monte la chaîne complète : quatre
silhouettes résolues par taxid, converties en PDF vectoriel, placées en regard des
feuilles d'une phylogénie schématique, avec les événements de changement d'hôte marqués
**sur les branches** et un encart qui distingue les deux événements inférés d'un flux
continu. Il porte aussi l'avertissement de licence dans sa propre légende.
