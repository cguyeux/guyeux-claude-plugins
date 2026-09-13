# Carte de `~/docs/cv/`

Lire ce fichier avant de fouiller : les 39 pages du CV sortent d'une trentaine de
blocs modulaires, et ouvrir le mauvais fait perdre plus de temps que de le
chercher ici.

## Chaîne de production

```
references/journals.bib      ─┐
references/conferences.bib   ─┤ all.py ─> references/journals.tex
affiliations.txt             ─┘          references/conferences.tex
                                         journals.txt, conferences.txt (canevas)
                                         journals.png, conferences.png (histogrammes)

main.tex  ─ préambule + \input{cv} ─> cv.tex ─> cvDoc/*.tex + references/*.tex
          └─ pdflatex ×2 ─> main.pdf
```

`main.tex` sélectionne la variante active par une seule ligne `\input{…}` non
commentée en bas de fichier ; toutes les autres sont commentées. Ne pas la
modifier pour compiler une variante : `cv_variant.py build` s'en charge sans y
toucher.

## Racine

| Fichier | Rôle |
|---|---|
| `main.tex` | préambule complet (KOMA-script, polices TeX Gyre, palette, macros) et sélection de la variante |
| `cv.tex` | le CV par défaut : titre, début, enseignement, recherche, publications |
| `all.py` | générateur BibTeX → LaTeX, et producteur du canevas Publiweb |
| `update_scholar.py` | métriques Google Scholar → `researchPublicationsSummary.tex` |
| `affiliations.txt` | `Nom, Prénom $ Institution $ Pays`, un auteur par ligne, trié |
| `Makefile` | `make cv`, `make scholar`, `make full` (voir la réserve sur `scholar` dans le SKILL) |
| `AGENTS.md` | workflow d'ajout côté Codex, cohérent avec ce skill |
| `iuf.tex`, `deleg.tex`, `erc.tex`, `anr-h14.tex`, `avancement.tex`, `chrysalide.tex`, `pedr.tex` | variantes existantes |
| `archives/` | scripts de correction ponctuels déjà joués, et sauvegardes |

## `cvDoc/` — les blocs de contenu

| Fichier | Contenu | Volume |
|---|---|---|
| `titre.tex` | bloc de titre, mise en forme seule | minuscule |
| `debut.tex` | identité, poste, affiliation, contacts | court |
| `research.tex` | enveloppe : enchaîne les blocs recherche ci-dessous | — |
| `researchArea.tex` | domaines : IA/apprentissage, bio-informatique, génomique TB, sécurité civile | moyen |
| `researchPublicationsSummary.tex` | **généré** : h-index, i10, citations, nombre de publications, date de mesure | court |
| `research5pub.tex` | 5 publications représentatives — générique, daté 2021-2023, non branché | court |
| `researchImpact.tex` | impact scientifique et sociétal | moyen |
| `researchComm.tex` | vulgarisation, médias, presse | **~3 pages** |
| `researchFundings.tex` | projets et contrats, macro `\ContractEntry` | **long** |
| `deeps.tex` | projet DEEPS, inclus par `researchFundings` | court |
| `researchSupervision.tex` | enveloppe encadrement et évaluation | — |
| `supervisionPhD.tex` | thèses encadrées, macro `\ThesisYear` | **long** |
| `evaluationPhD.tex` | jurys, expertises ANR, relectures | moyen |
| `researchOrganizationEditor.tex` | organisation de conférences, comités, activité éditoriale | moyen |
| `researchAwards.tex` | PEDR, RIPEC, dotations d'heures de calcul | court |
| `researchInternationalMobility.tex` | séjours à l'étranger | court |
| `expertise.tex` | missions d'expertise | court |
| `teaching.tex` | enveloppe enseignement | — |
| `teachingDetails.tex` | enseignements par établissement et année | long |
| `teachingAcademic.tex` | responsabilités administratives et pédagogiques | moyen |
| `teachingAccShort.tex` | version condensée de l'enseignement | court |
| `publications.tex` | enveloppe des publications : liens profils, sections M/CH/S/P/W/O/T en dur, puis import des `[J]` et `[C]` générés | long |
| `journals.tex`, `conferences.tex`, `journalsOld.tex`, `conferencesOld.tex` | archives de rendu, antérieures à la génération actuelle |
| `journals2pages.tex`, `publications2pages.tex` | variantes condensées pour dossier à pages limitées |
| `submitted.tex` | articles en cours d'évaluation |

Les blocs marqués **long** ou **~3 pages** sont les premiers à retirer d'une
variante courte.

## `references/`

| Fichier | Rôle |
|---|---|
| `journals.bib` | 129 `@article` + l'entrée `modele` |
| `conferences.bib` | 156 `@inproceedings` + `modele` |
| `journals.tex`, `conferences.tex` | **générés par `all.py`**, ne jamais éditer à la main |
| `abstracts_found.json`, `abstracts_missing.json` | état de récupération des résumés, dit quelles entrées n'en ont pas |

L'entrée `modele` en tête de chaque `.bib` est la liste de référence des champs :
la copier pour une nouvelle entrée plutôt que d'en inventer la structure.

## Champs BibTeX propres au dépôt

Au-delà des champs standards, `all.py` consomme :

`category` (ACL, ACTI, ACTN…), `rank` (facteur d'impact ou rang CORE, rendu entre
parenthèses après la revue), `note` (mention libre, ex. `Best Paper Award` pour un
article de revue), `publiweb` (`True`, `False`, `En cours`), `web` (site de la
revue ou de l'événement), `arxiv`, `hal`, `dixCitations`, `researchgate`,
`order = {alphabetic}` (auteurs par ordre alphabétique, marqué d'un astérisque),
et pour les conférences `acronym`, `booktitle`, `city`, `country`, `day`,
`selection` (`Full`, `Abstract`, `Extended abstract`), `best`, `poster`,
`presented`, `proc`, `editor`.

Distinction à ne pas confondre : un **best paper de revue** se signale par `note`,
un **best paper de conférence** par `best = {True}`.
