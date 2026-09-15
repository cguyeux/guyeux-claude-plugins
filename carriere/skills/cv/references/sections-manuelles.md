# Sections écrites à la main

Tout ce qui n'est ni un article de revue ni un proceedings à comité de lecture
s'écrit directement en LaTeX. **Aucun passage par les `.bib`, ni
`affiliations.txt`, ni `all.py`** : éditer le bloc, puis `pdflatex main.tex` deux
fois (ou `./cv_build.sh`, qui fait aussi le reste).

Chaque entrée s'écrit en deux blocs, `\begin{anglais}…\end{anglais}` et
`\begin{francais}…\end{francais}`. Une entrée qui n'existe que dans une langue
laisse un trou dans la version de l'autre langue.

---

## Projet financé, contrat — `cvDoc/researchFundings.tex`

Macro à quatre arguments :

```latex
\ContractEntry{intitulé du projet (montant)}{années}{programme}{rôle}
```

Gabarit complet :

```latex
\begin{anglais}
    \ContractEntry{Full project title in English (360 k\euro)}{2022 -- 2026}{ANR LabCom}{Leader}
\end{anglais}
\begin{francais}
    \ContractEntry{Intitulé complet en français (360 k\euro)}{2022 -- 2026}{ANR LabCom}{Porteur}
\end{francais}
```

Conventions relevées dans le fichier : montant entre parenthèses à la fin de
l'intitulé, en `k\euro` ; années séparées par ` -- ` ; le troisième argument
nomme le programme financeur (`ANR LabCom`, `PEPR PREZODE`, `Projet Chrysalide
UFC`, `AAP Recherche d'Excellence EIPHI-Région BFC (PIA3)`) et peut porter une
précision de classement ; le quatrième dit le rôle exact (`Leader`, `Porteur`,
`Leader du WP …`, `Co-contractant avec …`).

Placement : le fichier est découpé en sous-parties `\NewSubSubPart{1. Projets en
cours}`, puis les projets terminés. Ajouter un projet en cours **en tête** de sa
sous-partie. Un projet suffisamment gros peut avoir son propre fichier inclus,
comme `deeps.tex`.

---

## Thèse encadrée — `cvDoc/supervisionPhD.tex`

Le fichier est organisé par année de début, la plus récente en tête :

```latex
\ThesisYear{2025 -- \dots}
\begin{itemize}
	\item[-] Prénom Nom,
	      \begin{anglais}
		      \textit{Thesis title in English}. Cosupervision with Firstname Lastname, Institution, Country.
	      \end{anglais}
	      \begin{francais}
		      \textit{Titre de la thèse en français}. Codirection avec Prénom Nom, Institution, Pays.
	      \end{francais}
\end{itemize}
```

`\ThesisYear{2025 -- \dots}` pour une thèse en cours, `\ThesisYear{2021 -- 2024}`
pour une thèse soutenue. Si l'année existe déjà, ajouter un `\item[-]` dans son
`itemize` plutôt que de créer un second `\ThesisYear`.

Distinguer précisément, c'est ce qu'un comité regarde : direction seule,
codirection, cotutelle (préciser l'établissement partenaire et le pays),
co-encadrement. Les sections « thèses en cours » et « thèses soutenues » sont
séparées : une soutenance fait **déplacer** l'entrée, pas la dupliquer.

---

## Jury, expertise, relecture — `cvDoc/evaluationPhD.tex`

Jurys de thèse et d'HDR, expertises ANR et autres agences, activité de relecture.
Même structure bilingue. Pour un jury, mentionner le nom du doctorant,
l'établissement, la date et le rôle (rapporteur, examinateur, président).

---

## Workshop, poster, talk invité, communication sans actes

Dans `cvDoc/publications.tex`, section `[W]` (workshops internationaux et
nationaux à comité de lecture) ou `[T]`/`Other Publications`. Environnement
`etaremune` : la numérotation est **décroissante**, donc l'entrée la plus récente
se met **en tête** de la liste.

```latex
\item \label{nbWorkshops} \ConfDebut{Auteurs en clair}{Titre}{Acronyme}{Nom complet de l'événement}\ConfFin{Ville}{Pays}{Mois jour, année}{type de soumission}{note}{}{URL}{lien HAL ou PDF}{lien slides}
```

Les neuf arguments de `\ConfFin`, souvent vides : `{ville}{pays}{date}{type de
soumission, ex. (Extended abstract selection.)}{note, ex. Poster, Invited
speaker, pp. 90-95}{}{url}{hal ou pdf}{slides}`.

Auteurs écrits en clair, initiale du prénom et nom complet : « C. Lecarpentier,
G. Refrégier, C. Guyeux, and C. Sola ».

Exemples réels à recopier plutôt qu'à réinventer : les entrées ESM 2026, EENA
2025 et MedAccred V de `publications.tex`.

---

## Monographie, chapitre, logiciel, brevet

Toujours dans `cvDoc/publications.tex`, sections `\NewSubPart{Scientific
monographs}`, `Book Chapters`, `Software`, et la section brevets et dépôts APP.
Entrées libres, avec `\label{nbBooks}`, `\label{nbChapters}`, `\label{nbBrevets}`
selon la section : ces labels alimentent les compteurs affichés ailleurs dans le
CV, ne pas les omettre.

Format : auteurs, titre entre guillemets avec `\href` vers l'éditeur, collection,
année, ISBN pour un ouvrage ; référence APP complète pour un dépôt logiciel.

---

## Après toute édition

```
./cv_build.sh --no-check
```

Ces sections ne passent pas par les `.bib`, le contrôle d'intégrité n'a donc rien
à y voir, mais la compilation reste indispensable : vérifier que l'entrée apparaît
au bon endroit et que les compteurs n'ont pas bougé de travers.
