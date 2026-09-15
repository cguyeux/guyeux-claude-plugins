# Versions courtes et ciblées du CV

Le CV complet fait 39 pages. Presque aucun destinataire n'en veut autant : une
demande ANR veut deux pages, un organisateur de colloque veut dix lignes, un
partenaire de consortium veut une page en anglais. Ce document dit comment les
produire sans abîmer le CV par défaut.

## Le principe

Une variante est un fichier `.tex` à la racine de `~/docs/cv/` qui **réassemble
les mêmes blocs `cvDoc/`** dans un autre ordre, avec un sous-ensemble choisi.
C'est déjà le montage d'`iuf.tex`, `deleg.tex`, `erc.tex`, `anr-h14.tex`.

Deux interdits, qui ont chacun coûté une reprise :

1. **Ne jamais éditer un bloc `cvDoc/` pour un besoin propre à un dossier.**
   `research.tex` est partagé par `cv.tex`, `deleg.tex` et `iuf.tex` : en retirer
   une sous-section pour une candidature les casse toutes. Si une seule
   sous-section est de trop, reproduire le squelette (`\NewPart`, `\NewSubPart`,
   `\sectiongap`) dans le fichier variante et `\input` individuellement les blocs
   voulus.
2. **Ne jamais modifier `main.tex` pour compiler.** L'ancien montage demandait de
   commenter `\input{cv}`, compiler, copier le PDF, restaurer, recompiler : une
   interruption au milieu laissait `main.pdf` qui n'était plus le CV par défaut.
   `cv_variant.py build` dérive un fichier maître jetable et jette ses
   auxiliaires à la corbeille.

## Commandes

```
python3 cv_variant.py list

python3 cv_variant.py new --name anr-sadiand --preset 2pages --lang fr \
                          --focus "tubercul|genom" --top 6 --for "ANR AAPG 2027"

python3 cv_variant.py build --name anr-sadiand --lang fr --preset-pages 2 \
                            --out ~/Bureau/CV_Guyeux_ANR.pdf
```

`list` donne aussi la variante active dans `main.tex`, et les blocs que chacune
importe.

### Presets de `new`

| Preset | Blocs |
|---|---|
| `1page` | titre, identité, domaines de recherche, métriques |
| `2pages` | idem + financements, encadrements, distinctions |
| `complet` | la structure de `cv.tex`, à élaguer |

Ce sont des points de départ, pas des garanties : `2pages` produit six pages tel
quel, parce que `researchFundings.tex` et `supervisionPhD.tex` sont longs.
`build --preset-pages N` mesure et avertit.

### Tenir la limite de pages

Dans l'ordre, ce qui se retire en premier :

1. `researchComm.tex` — vulgarisation et médias, environ trois pages, hors sujet
   dans presque tout dossier scientifique ;
2. la liste exhaustive de publications — la remplacer par une sélection
   thématique (`--focus`) suivie d'un lien vers Google Scholar et dblp ; le bloc
   de liens tout fait est en tête de `cvDoc/publications.tex` ;
3. `teachingDetails.tex` — sauf candidature à un poste d'enseignant-chercheur ;
4. `evaluationPhD.tex`, `researchOrganizationEditor.tex` — sauf dossier de
   promotion ou de rayonnement.

Réduire la police ou les marges est le mauvais réflexe : un CV de deux pages en
8 pt se lit comme un aveu, et le préambule est partagé avec le CV complet.

### Sélection thématique des publications

`--focus` appelle `cv_select.py`. La sélection produite est un **point de départ à
relire** : le filtre lexical ne connaît pas l'importance relative des travaux, et
attrape des faux amis. Vérifier d'abord ce que chaque motif ramène :

```
python3 cv_select.py --focus "wildfire|forest fire|firemen|fire brigade" --format count
```

Un motif à zéro est mal orthographié ou inutile. Un thème s'écrit rarement d'une
seule façon : chercher `firefight` rate les entrées qui n'écrivent que `firemen`.

Ne pas réutiliser `cvDoc/research5pub.tex` pour un dossier thématique : il est
générique, daté 2021-2023, uniquement chaos et cryptanalyse, et son import est
commenté dans `research.tex`.

## Langue

Les blocs sont bilingues. `build --lang fr|en` règle `\includeversion` et
`\excludeversion` dans le fichier maître jetable, sans toucher `main.tex`.

Vérifier que les blocs choisis ont bien les deux versions : certains n'ont que le
français, et le PDF anglais sortirait avec un trou. Contrôle rapide :

```
grep -c "begin{anglais}\|begin{francais}" cvDoc/<bloc>.tex
```

## Le cas du paragraphe

Pour une bio d'invité, une notice de partenaire, une présentation de dix lignes :
pas de LaTeX, pas de variante. Rassembler les faits sourcés, puis rédiger.

| Fait | Où |
|---|---|
| h-index, i10, citations, nombre de publications, date | `cvDoc/researchPublicationsSummary.tex` (regénéré par `cv_metrics.sh`) |
| poste, affiliation | `cvDoc/debut.tex` |
| domaines | `cvDoc/researchArea.tex` |
| projets phares et montants | `cvDoc/researchFundings.tex` |
| encadrements | `cvDoc/supervisionPhD.tex` |
| publications du thème | `cv_select.py --focus …` |

Le texte partant à un tiers, appliquer les règles de rédaction de l'utilisateur :
pas de tiret cadratin ni de double tiret, pas d'emoji, pas de gras ni de Markdown
ornemental, prose continue plutôt que listes, titres de niveau 2 seulement si la
longueur le justifie. Livrer en un seul paragraphe sans retour à la ligne
interne, et dire explicitement qu'il est prêt à copier-coller.

Adapter au destinataire : un comité ANR veut le rôle dans les projets et les
montants, un organisateur de colloque veut le domaine et deux résultats
marquants, une fiche partenaire veut l'équipe et les moyens.
