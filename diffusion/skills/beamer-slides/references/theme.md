# Le thème `guyeux`

```latex
\documentclass[aspectratio=169,11pt]{beamer}
\usetheme[academique]{guyeux}     % ou [affirmee]
```

Base metropolis, police Fira Sans. Compile en `pdflatex`, `xelatex` et
`lualatex`. Fira est native de metropolis, présente dans TeX Live et sur
Overleaf : **aucune installation n'est requise et le deck reste portable**.

Copier `assets/beamerthemeguyeux.sty` dans le répertoire de la présentation.
Le répertoire doit être autonome : c'est ce qui permet de le déposer sur
Overleaf ou de l'envoyer à un co-auteur sans rien d'autre.

## Les deux intensités

**`academique`** — séminaire, conférence, cours. Fond clair, titre à l'encre
souligné d'un filet d'accent court, un seul accent de couleur, beaucoup de
blanc. C'est le registre par défaut.

**`affirmee`** — audition, keynote, soutenance, grand public. Même grille, même
palette, même police, mais le titre de slide s'assoit sur un aplat profond et la
page de titre est pleine couleur. L'identité reste reconnaissable, l'énergie
monte.

Les deux ne diffèrent que par la couleur et le rythme, jamais par la grille :
un exposé reste identifiable comme venant du même auteur.

## La palette

Consolidée depuis les decks existants du parc, donc déjà reconnaissable.

| Nom | Valeur | Emploi |
|---|---|---|
| `gxencre` | `1B1F23` | tout le texte |
| `gxprofond` | `1F4E3D` | structure, aplats, titres en intensité affirmée |
| `gxaccent` | `C0563B` | l'accent unique : filet, barre de progression, emphase |
| `gxsauge` | `7FA37F` | second accent, comparaisons |
| `gxacier` | `2E5E8C` | troisième accent, encadrés de notion |
| `gxsable` | `E7E8D1` | fond d'encadré |
| `gxcreme` | `FAF8F0` | texte sur aplat |
| `gxardoise` | `6B7079` | texte secondaire, clés de lecture, pieds de page |

Un accent, pas trois : `gxaccent` porte l'emphase, les deux autres ne servent
qu'à distinguer des séries ou des types d'encadré.

## Les macros

| Macro | Rôle |
|---|---|
| `\begin{sliderupture}[couleur]` | slide de rupture pleine couleur |
| `\bigchiffre[couleur]{chiffre}{phrase}` | grand chiffre centré verticalement |
| `\slidefigure[part]{fichier}{clé}` | figure dominante, hauteur calculée |
| `\slidefiguretexte[part]{fichier}{texte}` | figure et commentaire côte à côte |
| `\slidecompare{titre G}{contenu G}{titre D}{contenu D}` | comparaison appariée |
| `\cle{...}` | clé de lecture sous une figure |
| `\kb[couleur]{...}` | take-away |
| `\notion{titre}{texte}` | encadré de notion |
| `\methode{titre}{texte}` | encadré de méthode |
| `\nouveau{titre}{texte}` | ce qui est neuf par rapport à la littérature |
| `\remarquable{titre}{texte}` | amplitude ou précision frappante |
| `\fragilite{titre}{texte}` | fait à consolider |
| `\src{...}` | source d'une figure, en petit et en gris |

## Deux pièges déjà payés

**`\textheight` n'est pas la hauteur disponible dans le corps d'une frame.**
Beamer y compte aussi le titre de slide, sa barre de progression et le pied de
page, qui consomment environ un quart. Le thème expose `\gx@corps`, réglé à
0,70 `\textheight` en intensité académique et 0,76 en affirmée, mesuré au rendu.
Toute macro qui calcule une hauteur doit partir de `\gx@corps`, jamais de
`\textheight` : c'est l'erreur qui a produit 51 pt de débordement silencieux au
premier essai.

**`\lecture` est déjà pris par Beamer** (mode conférence). D'où `\cle`.

## Inter, si on y tient

`inter.sty` est dans TeX Live, en OTF et en Type1, donc utilisable même en
`pdflatex`. Son fichier de style charge l'encodage grec : il faut
`texlive-langgreek`, sans quoi la compilation échoue sur `lgrenc.def` introuvable.
Le gain visuel sur Fira est mince et le coût de portabilité réel. À proposer, pas
à imposer.

## Vérifier le thème

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/beamer-slides/scripts/deck_render.py assets/demo_theme.tex
python3 ${CLAUDE_PLUGIN_ROOT}/skills/beamer-slides/scripts/slide_audit.py assets/demo_theme.tex
```

La démo exerce tous les types dans les deux intensités. Elle doit compiler avec
zéro `Overfull` : si elle en produit, c'est le thème qui est cassé, pas le deck.
