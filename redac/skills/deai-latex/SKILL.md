---
name: deai-latex
description: >-
  Applique les regles de style scientifique a un article LaTeX : supprime le gras abusif,
  convertit les listes a puces en prose, fusionne les micro-sections, verifie les acronymes
  (definis une seule fois), met les noms d'especes en italique, elimine les cliches
  redactionnels et ameliore la coherence des temps verbaux. A utiliser quand l'utilisateur
  demande de nettoyer les marqueurs de texte genere par IA, de retirer les tirets cadratin,
  de depuceliser un texte trop liste, d'harmoniser le style d'un manuscrit, ou avant une
  soumission.
argument-hint: "<chemin vers main.tex>"
---

# /deai-latex -- Mise en conformite stylistique d'un article scientifique

Applique les regles classiques de style des revues scientifiques a un article
LaTeX. Agit uniquement sur la **forme** (mise en page, conventions typographiques,
fluidite), jamais sur le fond. Utile apres une phase de redaction intensive
ou des allers-retours de coautorat, ou des ecarts stylistiques se sont accumules.



## Prealable -- Consultation memoire projet

**Avant toute action**, verifier si le projet possede :
1. Un `JOURNAL.md` dans le repertoire du projet → le lire pour connaitre l'historique
2. Un `CLAUDE.md` local → le lire pour les instructions specifiques
3. Un `claim_check.md`, `review/INDEX.md`, ou `response.md` → connaitre l'etat courant

Afficher un bref resume de l'etat connu du projet avant de commencer :

```
Etat projet : [titre article]
  Journal     : [derniere entree ou "absent"]
  Claim-check : [N claims, M infirmes ou "jamais execute"]
  Reviews     : [N reviews, M en cours ou "aucune"]
  Derniere action : [date et description]
```

## Declenchement

```
/deai-latex path/to/main.tex
```

Si aucun argument, chercher `main.tex` dans le repertoire courant.

---

## Phase 0 -- Lecture integrale

1. Localiser le `.tex` principal (argument `$ARGUMENTS` ou `main.tex`)
2. Lire le fichier en entier. Resoudre les `\input{}` et `\include{}`
3. Prendre des notes mentales sur la structure globale : nombre de sections,
   sous-sections, listes, occurrences de `\textbf`, etc.
4. Identifier la langue de l'article (francais ou anglais) pour adapter les corrections

---

## Phase 1 -- Diagnostic

Avant de modifier quoi que ce soit, produire un diagnostic quantitatif.

**Deux des mesures ne se font PAS a la main** (elles ont chacune un piege qui rend
un chiffre faux mais credible, cf. R13.1 et R12) : la longueur de l'abstract et la
detection de cuisine locale. Les obtenir via le script du skill :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/deai-latex/scripts/latex_metrics.py main.tex --pdf main.pdf
```

Il rend la longueur de l'abstract (comptee sur le texte REELLEMENT rendu) avec sa
plage de conformite, et les occurrences de cuisine locale visibles dans le PDF.
Passer `--pdf` suppose le manuscrit compile ; sans PDF, le scan R12 est saute et il
faut le signaler comme non fait (ne PAS le remplacer par un grep sur le source :
voir R12, "Test final").

```
Diagnostic deai-latex :
  Langue           : [francais/anglais]
  Abstract         : N mots (cible 150-300), [violations detectees ou OK]
  Sections         : X (dont Y sous-sections < 5 lignes)
  \textbf dans le corps : N occurrences
  Environnements itemize : N
  Environnements enumerate : N
  Acronymes trouves : N (dont M non definis, P definis plusieurs fois)
  Noms d'especes non italiques : N
  Cliches rédactionnels detectes : N (details en Phase 2)
```

Ne pas commencer les corrections avant que le diagnostic soit affiche.

---

## Phase 2 -- Corrections (appliquer dans cet ordre)

### R1. Suppression du gras abusif

**Regle** : dans le corps de l'article (hors titres, captions, labels de
`description`), `\textbf{}` n'a quasiment jamais sa place. Un article
scientifique utilise `\emph{}` pour insister, pas le gras.

**Actions** :
- Supprimer `\textbf{...}` → garder le texte nu (sans mise en forme)
- Si le gras sert a introduire un terme defini pour la premiere fois :
  remplacer par `\emph{...}`
- Conserver le gras uniquement dans :
  - Les titres de sections/sous-sections
  - Les labels `\item[...]` dans `description`
  - Les captions de figures/tables (si utilise comme label)
  - Les en-tetes de tableaux
- **Ne jamais ajouter** de `\textbf` dans le corps du texte

**GARDE-FOU POST-RETRAIT -- la majuscule perdue** *(ajoute le 2026-07-31, defaut vecu)*.
Retirer une balise qui ENVELOPPE LE DEBUT D'UNE PHRASE laisse la minuscule de
l'interieur de l'accolade : `\textbf{The test is only...}` devient `the test is
only...`. Le LaTeX compile, le PDF s'affiche, et **rien ne signale l'erreur** ; elle
survit jusqu'a la relecture suivante, voire jusqu'a la soumission. Le meme piege vaut
pour `\emph{}`, `\textit{}` et pour toute conversion de balise en debut de phrase.

**Controle systematique a passer APRES tout retrait ou conversion de balise** :

```bash
# phrases commencant par une minuscule, hors abreviations
python3 - <<'EOS'
import re
src=open("main.tex").read()
body=src[src.index("\\section{Introduction}"):src.index("\\bibliographystyle")]
flat=re.sub(r"\s+"," ",body)
for m in re.finditer(r"\.\s+([a-z][a-z]{2,})", flat):
    pre=flat[:m.start()+1]
    if re.search(r"(e\.g|i\.e|cf|vs|et al|Fig|Tab|approx|no)\.$", pre): continue
    print("->", flat[max(0,m.start()-70):m.start()+45])
EOS
```

**Calibrage mesure** (manuscrit reel, 12 pages) : 7 detections, dont **1 vrai defaut**
et 6 faux positifs, TOUS sur des noms d'especes abreges (`\textit{M. decipiens}`, le
point de `M.` etant pris pour une fin de phrase). Inspecter les 7, ne corriger que le
vrai : le taux de faux positifs est eleve mais le controle reste rentable, car le vrai
defaut est invisible autrement.

**Corollaire d'ordonnancement du pipeline qualite** : ce defaut est introduit par le
nettoyage et n'est visible qu'a la relecture. `/manuscript-review` doit donc passer
APRES `/deai-latex`, jamais l'inverse.

### R2. Conversion des listes a puces en prose

**Regle** : un article scientifique est ecrit en prose. Les `itemize` et
`enumerate` sont rares et reserves a des cas precis (protocole experimental
etape par etape, liste de criteres formels).

**Actions** :
- **Si itemize contient 2-3 items courts** : reformuler en une phrase de prose.
  Exemple :
  ```latex
  % AVANT
  The main advantages are:
  \begin{itemize}
    \item High sensitivity
    \item Low cost
    \item Rapid turnaround time
  \end{itemize}

  % APRES
  The main advantages are high sensitivity, low cost, and rapid turnaround time.
  ```

- **Si itemize contient des items avec \textbf{Label:}** : convertir en
  environnement `description` ou en prose selon le contexte

- **Si itemize contient des items longs (> 1 phrase)** : convertir en
  paragraphes separes, ou en sous-sections si le contenu est assez riche

- **Conserver itemize uniquement si** :
  - C'est un protocole ou une procedure etape par etape (prefer `enumerate`)
  - C'est une liste formelle de criteres, d'hypotheses, ou d'objectifs numerotes
  - C'est une liste de symboles/notations

- **Ratio cible** : maximum 1-2 listes par section de l'article.
  Au-dela de 3 listes par section, le texte gagne presque toujours a etre
  reformule en prose continue

### R3. Fusion des micro-sections

**Regle** : une sous-section de 2-5 lignes est rarement justifiee dans un
article. Un texte scientifique progresse par paragraphes denses, pas par
micro-sections.

**Actions** :
- **Si une sous-section fait < 5 lignes** :
  1. Option 1 : fusionner avec la sous-section precedente ou suivante si le
     theme est proche
  2. Option 2 : developper le contenu (ajouter des details, des exemples,
     des references) pour atteindre au moins 8-10 lignes
  3. Option 3 : supprimer la sous-section et integrer le contenu comme
     paragraphe dans la section parente
- **Ne pas creer de sous-sections juste pour "organiser"** : dans un article
  scientifique, la hierarchie est section > sous-section > paragraphe.
  Les sous-sous-sections (`\subsubsection`) sont rares
- **Titres de sections** : eviter les titres trop generiques ou pompeux
  ("Comprehensive Analysis", "In-Depth Investigation"). Prefer des titres
  factuels ("Resistance mutations in katG", "Phylogenetic analysis")

### R4. Acronymes et abreviations

**Regle** : chaque acronyme est defini exactement une fois, a sa premiere
occurrence dans le texte (pas dans l'abstract si l'abstract est autonome).
L'abstract peut utiliser l'acronyme sans le definir si c'est standard dans
le domaine (DNA, RNA, PCR, HIV...).

**Actions** :
1. Lister tous les acronymes utilises dans l'article
2. Pour chaque acronyme, trouver la premiere occurrence :
   - Si non defini : ajouter la definition.
     Format anglais : `MTBC (\textit{Mycobacterium tuberculosis} complex)`
     ou `whole-genome sequencing (WGS)`
   - Si defini plusieurs fois : garder uniquement la premiere definition,
     remplacer les autres par l'acronyme seul
   - Si defini dans l'abstract ET dans le corps : garder les deux
     (l'abstract est un document autonome), sauf si la revue cible
     interdit la redefinition
3. Verifier la coherence : une fois defini, l'acronyme est utilise partout
   (pas de retour a la forme longue)
4. Les acronymes universels du domaine (DNA, RNA, PCR, SNP, WGS, NGS, HIV,
   TB, MDR, XDR, WHO, CDC...) n'ont pas besoin de definition dans un article
   specialise. Adapter au public cible

### R5. Noms scientifiques d'especes

**Regle** : les noms latins d'especes et de genres sont toujours en italique.
La premiere occurrence donne le nom complet, les suivantes utilisent
l'abreviation du genre.

**Actions** :
- Mettre en italique avec `\textit{}` ou `\emph{}` :
  - Noms de genre : *Mycobacterium*, *Escherichia*, *Staphylococcus*...
  - Noms d'espece : *M. tuberculosis*, *E. coli*, *S. aureus*...
  - Noms de sous-espece/lignee : *M. tuberculosis* var. *bovis*
- Premiere occurrence : nom complet (`\textit{Mycobacterium tuberculosis}`)
- Occurrences suivantes : genre abrege (`\textit{M. tuberculosis}`)
- **Ne pas mettre en italique** :
  - Les noms de famille/ordre/classe (Mycobacteriaceae, Actinobacteria)
  - Les noms vernaculaires (tuberculosis bacillus)
  - Les noms de complexes quand utilises comme nom commun (MTBC, sans italique)
  - "spp." et "sp." (le genre reste en italique : `\textit{Mycobacterium} spp.`)

### R6. Cliches rédactionnels

**Regle** : certains mots et tournures sont sur-utilises dans la redaction
scientifique contemporaine et alourdissent le texte. Les identifier et les
reformuler ameliore nettement la lisibilite.

**Mots et expressions a traquer** (anglais) :
- "Furthermore", "Moreover", "Additionally" → varier : "Also", "In addition",
  ou restructurer la phrase pour ne pas avoir besoin de connecteur
- "It is worth noting that", "It should be noted that",
  "Notably", "Importantly" → supprimer, aller droit au fait
- "crucial", "pivotal", "paramount", "instrumental" → "important", "key",
  ou supprimer si le contexte suffit
- "comprehensive", "in-depth", "thorough" → supprimer sauf si strictement justifie
- "aims to", "seeks to" au debut de chaque section → varier
- "plays a crucial/key/pivotal role" → reformuler
- "landscape" (au sens figure), "realm", "paradigm shift" → supprimer
- "delve into", "shed light on", "pave the way" → "examine", "clarify", "enable"
- "leverage" → "use"
- "robust" (sauf contexte statistique precis) → "reliable", "effective"
- "In this study, we..." repete a chaque section → varier les ouvertures
- "a wide range of", "a plethora of" → "many", "various", "several"

**Mots et expressions a traquer** (francais) :
- "Il convient de noter que", "Il est important de souligner" → supprimer
- "De maniere significative" → "nettement", "sensiblement"
- "Dans le cadre de cette etude" repete → varier
- "De plus", "En outre", "Par ailleurs" en cascade → restructurer
- "joue un role crucial/cle/determinant" → reformuler
- "offre une perspective unique" → supprimer ou preciser
- "permet de mettre en lumiere" → "montre", "revele"
- "exhaustif/exhaustive" → souvent exagere, supprimer ou remplacer

**Action** : ne pas faire un remplacement mecanique. Relire la phrase et
la reformuler naturellement. Parfois la meilleure correction est de fusionner
deux phrases ou de supprimer un paragraphe entier qui ne dit rien.

### R7. Structure des paragraphes

**Regle** : un paragraphe scientifique fait typiquement 5-12 lignes.
Il ne commence pas systematiquement par une phrase-sujet suivie de
trois arguments puis d'une conclusion.

**Actions** :
- **Paragraphes d'une seule phrase** : fusionner avec le paragraphe
  precedent ou suivant
- **Paragraphes identiquement structures** (tous commencent par
  "Regarding X, ...", ou tous suivent le pattern claim-evidence-conclusion) :
  varier les structures
- **Paragraphes > 20 lignes** : envisager de scinder si deux idees
  distinctes sont presentes

### R8. Tirets cadratins et ponctuation

**Regle** : les em-dashes (---) sont rares dans l'ecriture scientifique
anglophone et leur usage doit rester exceptionnel.

**Actions** :
- Remplacer `---` par des parentheses, des virgules, ou deux phrases separees
- En francais : les tirets cadratins sont plus courants mais ne doivent
  pas etre abuses. Limiter a 1-2 par page maximum
- Verifier l'absence d'emojis (les supprimer si presents)

### R9. References croisees et flottants

**Regle** : chaque figure et table est referencee dans le texte.
Les references utilisent `\cref{}` (package cleveref).

**Actions** :
- Verifier que chaque `\begin{figure}` et `\begin{table}` est reference
  par au moins un `\cref{fig:...}` ou `\cref{tab:...}` dans le texte
- Remplacer les references manuelles ("Figure 1", "Table 2") par `\cref{}`
- Verifier que les captions sont informatives :
  - Mauvais : "Results of the analysis"
  - Bon : "Distribution of SNP distances among L4 lineage strains (n=342)"

### R10. Coherence des temps verbaux

**Regle** : dans un article scientifique :
- **Methodes** : passe simple (anglais) ou passe compose (francais)
  → "Sequences were aligned using..." / "Les sequences ont ete alignees avec..."
- **Resultats** : passe simple → "Analysis revealed..."
- **Discussion** : present pour les faits etablis, passe pour les resultats
  → "Drug resistance is a growing concern... Our analysis showed..."
- **Introduction** : present pour le contexte general

**Actions** :
- Verifier la coherence intra-section
- Signaler les melanges de temps (present + passe dans la meme phrase
  pour des faits du meme type)

### R11. Verifications supplementaires

- **Nombres** : les nombres < 10 s'ecrivent en toutes lettres dans le texte
  courant (sauf mesures : "5 mL"). Utiliser `\num{}` (siunitx) pour les
  grands nombres
- **Unites** : toujours avec `\si{}` ou `\SI{}` du package siunitx :
  `\SI{42}{\percent}`, `\SI{3.5}{\kilo\base\pair}`
- **Guillemets** : utiliser `\enquote{}` (csquotes), jamais de guillemets manuels
- **Tirets dans les mots composes** : coherence (drug-resistant partout,
  pas drug resistant puis drug-resistant)
- **Espaces insecables** : avant les references (`see~\cref{fig:x}`),
  entre un nombre et son unite si pas siunitx

### R12. Retrait des references internes / cuisine locale

Un manuscrit scientifique public ne doit jamais exposer la plomberie
interne de l'equipe : scripts maison non publies, repertoires de
projet, noms de fichiers, API internes, classifications privees.
Tout cela se comporte mal a la lecture (un reviewer demande ou sont
publies ces outils, comment les versionner, etc.) et affaiblit la
credibilite du manuscrit.

**A supprimer systematiquement** :

| Categorie | Exemple a detecter | Reformulation |
|-----------|-------------------|---------------|
| Scripts maison | `lignees.py`, `rangement.pkl`, `phase*.py` | Omettre, ou citer le schema publie |
| Classifications privees | `"moi"` (Guyeux), `in-house continuously-maintained classification` | "published schemes" + citations `\citep{coll, stucki, napier, freschi, ...}` |
| Repertoires projet | `animal_vs_human/`, `bdd/actuelle/`, `investigate_phylo/` | "a curated list", "local catalogue", "the reference annotation (GenBank, GFF3)" |
| Skills/commandes | `/spdi-annotation`, `/mtbc-lineages`, `/cahier-de-labo` | Omettre et decrire la methode directement |
| Noms de fichiers internes | `convergence_inter_species.tsv`, `known_coverage.ESP{1..43}` | "a curated list of N genes", "per-spacer read coverage" |
| Endpoints d'API internes | `validationFormulaire AJAX endpoint`, noms de tables SQL | Omettre, decrire en prose ("queried against SITVIT2") |
| URLs de dev | `tbannotator.univ-fcomte.fr`, `freeboxos.fr`, `82.64...nip.io` | En footnote, URL publique definitive |

**Detection automatique** : rechercher **dans tout le manuscrit, captions
de tableaux et figures incluses** (les chemins internes s'incrustent souvent
dans les captions de Supplementary Tables/Figures, qui echappent a une
relecture lineaire). Motifs a traquer :

```
\\(texttt|textit|verb|path)\{[^}]*[a-z_/][a-z_/0-9.-]*\\}    # commandes/chemins
\\(texttt|textit|verb)\{[^}]*\\.(json|csv|tsv|pkl|h5|nwk|html?|yaml?|py|sh|fa|fasta|md|log|sql|txt)\\}  # extensions de fichiers
\\_vs\\_|_py\\b                                                # suffixes de noms de scripts
AJAX|endpoint|API|POST request                                 # details d'implementation
in-house|home-made|our own                                     # auto-references opaques
fallback to (the )?local|repli sur (le fichier|la table)       # formules indicatrices
companion (figure|file) `[a-z_/.-]+`                           # references a fichier compagnon nomme
\\(analyse|analysis|step|task|todo)\\s*[A-Z][0-9]+\\)?         # taxonomie privee d'analyses (A3, S2, T7...)
\\texttt\{/[a-z-]+\\}                                         # skills (commencent par /)
\\texttt\{[a-z]+/[a-z_/]+\\}                                  # chemins de repertoires
```

**Important** : ne pas se limiter a `\texttt{}`. Les chemins internes apparaissent
aussi en `\textit{}` (italique nominal), `\verb{}` (texte verbatim), et meme en
texte simple sans enveloppe. Toujours scanner sur l'extension du fichier.

**Apprentissage 2026-05-03** : l'extension `.json` n'etait pas dans la liste
initiale, et un `\textit{report.json}` est passe inapercu pendant une passe
complete (ainsi que plusieurs `\texttt{supplementary\_materials/...}` dans
des captions de tableaux). La detection doit couvrir TOUTES les extensions
de fichiers locaux (json, csv, h5, pkl, nwk, html, yaml...) et TOUTES les
enveloppes LaTeX (`\texttt`, `\textit`, `\verb`).

**Exemples concrets avant / apres** (pipeline MTBC) :

| Avant (cuisine locale) | Apres (publie + neutre) |
|---|---|
| *"18 taxonomy systems declared in the live lignees.py registry of the MTBC project, comprising published schemes (Coll, Stucki, ...) plus our in-house moi classification"* | *"17 published MTBC taxonomy schemes available at the time of this work: Coll~\citep{coll2014robust}, Stucki~\citep{stucki2016mycobacterium}, Napier~\citep{napier2020robust}, Freschi~\citep{freschi2021population}, Coscolla, Shitikov, ..."* |
| *"reconstructed from TBannotator's known\_coverage.ESP\{1..43\} fields"* | *"reconstructed in silico from per-spacer read coverage"* |
| *"queried against SITVIT2 via the validationFormulaire AJAX endpoint"* | *"queried against SITVIT2"* |
| *"annotated using the GFF3 and GenBank files distributed with the investigate\_phylo resources"* | *"annotated against the H37Rv reference (NC\_000962.3, GenBank and GFF3)"* |
| *"following the formal rule documented in /spdi-annotation"* | (Omettre ; la regle elle-meme reste decrite en prose.) |
| *"the convergence\_inter\_species.tsv table of 1 986 genes convergently mutated"* | *"a curated list of 1 986 genes convergently mutated"* |
| *"SPDI profiles retrieved from the animal\_vs\_human/ project"* | *"SPDI profiles of the four animal ecotypes, with amino-acid changes annotated against H37Rv"* |
| *"we retain locally in our lignees.py catalogue"* | *"one of the canonical markers published with the scheme"* |
| URL `tbannotator.univ-fcomte.fr` dans le texte | URL reelle en footnote : `\\footnote\{\\url\{https://...\}\}` |
| *"with fallback to the local \\textit\{report.json\} file when NCBI returned no metadata"* | Suppression complete (le fallback local est une cuisine d'implementation, pas une methode publique) |
| *"recorded in the canonical barcoding table \\texttt\{global\\_supplementary/snp\\_barcoding.csv\}"* | *"recorded in the canonical SNP-barcoding table accompanying [Guyeux 2026]"* |
| *"Full table provided as \\texttt\{supplementary\\_materials/table\\_S1\\_sensitivity.csv\}"* (caption) | *"Full table provided as Supplementary Table~S1"* (le journal renomme les fichiers a la publication) |
| *"the interactive PastML tree as \\texttt\{pastml\\_host\\_acr\\_compressed.html\}"* | *"the interactive PastML tree as a Supplementary HTML file"* |
| *"are flagged for verification (analysis A3)"* | *"are analysed in detail in \\cref\{sec:results-cases\}"* (taxonomie privee de tasks/A1, A2... a remplacer par \\cref vers la section du manuscrit) |

**Regle de conservation** : tout ce qui est **une methode reproductible
par un tiers** doit rester (description en prose des etapes, formats
standards type GFF3/GenBank/VCF/FASTA, outils publies avec citation).
Tout ce qui est **un artefact du workflow local** doit disparaitre
(noms de repertoires, de fichiers, de scripts, d'API internes).

**Apres R12**, relire la section Methods en se demandant : "un
chercheur independant, sans acces a mes repertoires, peut-il
reproduire cette analyse en lisant uniquement le manuscrit et en
consultant les references bibliographiques ?" Si la reponse est
non parce qu'une information essentielle vient de mes scripts, il
faut soit publier le script (Zenodo + citation), soit decrire
l'algorithme en prose.

**Test final post-R12** : compiler le manuscrit en PDF, puis

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/deai-latex/scripts/latex_metrics.py main.tex --pdf main.pdf
```

Le script fait le grep sur le **PDF rendu** (seul test qui fasse foi) avec des motifs
calibres pour ne PAS sur-detecter : une regex naive « un slash quelque part » ramasse
`GAS6/AXL`, `epithelial/mesenchymal`, `E/M`, `0.5/0.5`, `miR-205/ZEB1` et les DOI que
`pdftotext` coupe en fin de ligne. **Un test qui hurle a tort est un test qu'on apprend
a ignorer : il est pire qu'absent.** Le script exige donc un indice fort de chemin
(segment snake_case suivi d'un slash, extension de fichier locale, chemin multi-segments,
chemin systeme) et filtre URL/DOI sur leur voisinage. Calibrage verifie : 0 faux positif
sur un manuscrit propre, detection de `experiments/met_rtk_split/` sur le meme manuscrit
avant nettoyage.

Variante manuelle (si le script est indisponible) : `pdftotext main.pdf - | grep -E ...`
avec une liste de chemins/repertoires/fichiers locaux connus (extraite via
`grep -roE "[a-z_/-]+/[a-z_/-]+" $PROJECT/`). **Aucune occurrence visible
dans le PDF rendu** = R12 acceptable. Cette verification au niveau du PDF
attrape ce que la regex au niveau LaTeX aurait pu manquer (ex. cuisine locale
incrustee dans des captions de Supplementary Tables que le scan source ne
matche pas si l'enveloppe LaTeX n'est pas dans la liste).

Distinction critique source vs rendu : `\includegraphics{supplementary_materials/fig_SX.pdf}`
**reste dans le source LaTeX** (directive de compilation) mais n'apparait pas
dans le PDF rendu : a conserver. Tout `\texttt{supplementary_materials/...}`
**apparait dans le PDF rendu** : a abstraire.

### R13. Verification de l'abstract

**Regle** : l'abstract est un texte autonome, dense, qui presente le contexte,
l'objectif, l'approche en une phrase, les resultats principaux et la conclusion.
Il obeit a des canons stricts dans la litterature scientifique. Une attention
particuliere doit lui etre portee car c'est la partie la plus lue du manuscrit
et la premiere filtree par les editeurs et les bases de donnees.

**Localisation** :
1. Reperer le bloc abstract : `\begin{abstract}...\end{abstract}`,
   `\abstract{...}`, ou commande equivalente selon la classe (`elsarticle`,
   `IEEEtran`, `acmart`, etc.)
2. Si l'article a une version traduite (resume + abstract en francais et anglais),
   appliquer R13 a chacune

**R13.1 -- Longueur**

**Ne pas compter a la main, ni improviser une regex.** Utiliser :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/deai-latex/scripts/latex_metrics.py main.tex
```

Piege documente (vecu le 2026-07-11, un abstract declare conforme a tort). La
consigne intuitive « ignorer les commandes LaTeX » se traduit naivement par une
regex qui supprime la commande **avec son argument**. Or `\emph{X}`, `\textit{X}`,
`\node{X}`, `\ce{X}` **rendent** leur argument : le supprimer **sous-estime** la
longueur. Le reflexe de controle (compter sur le PDF via `pdftotext`) **sur-estime**
des que le manuscrit charge `lineno`, car les numeros de ligne deviennent des mots.
Resultat observe sur un meme abstract : **315 mots** (sous-estime), **354** (sur-estime),
**324** en verite. Deux mesures fausses en sens opposes, la bonne valeur entre les
deux, et aucun moyen de s'en apercevoir sans un troisieme compteur. D'ou le script,
qui garde l'argument des commandes de mise en forme, supprime les commandes
structurelles avec leur argument, et compte une formule inline comme partie du mot
qu'elle touche (`$\Delta$Np63$\alpha$` rend « DNp63a », UN mot, pas trois).

Plages de conformite (le script les rend directement) :

| Plage | Statut | Action |
|-------|--------|--------|
| < 100 mots | trop court | signaler : abstract probablement insuffisant, manque le contexte ou la conclusion |
| 100-150 mots | court | tolerable pour certains journaux (PNAS, Nature Brief Communications) ; verifier la cible |
| 150-250 mots | **plage standard** | OK pour la majorite des revues |
| 250-300 mots | acceptable | verifier la limite du journal cible |
| 300-350 mots | long | signaler ; beaucoup de revues coupent a 300 |
| > 350 mots | trop long | a raccourcir imperativement (sera tronque par l'editeur) |

Si le journal cible est connu (extrait de `\documentclass`, du fichier `.cls`,
ou d'une mention dans le manuscrit), donner la limite specifique :
- *Nature*, *Science* : 150-200 mots
- *PLOS ONE*, *Scientific Reports* : 250-300 mots
- *Bioinformatics* : 150-200 mots
- *Genome Research*, *Nucleic Acids Research* : 200-250 mots
- *eLife* : 150 mots (impact statement separe)

**R13.2 -- Structure interdite**

Un abstract est en **prose continue**. Les elements suivants sont interdits
sauf si le journal cible impose explicitement un structured abstract
(BMC, JAMA, certains journaux medicaux) :

- `\section`, `\subsection`, `\paragraph` a l'interieur de l'abstract
- Sous-titres en gras du type `\textbf{Background:}`, `\textbf{Methods:}`,
  `\textbf{Results:}`, `\textbf{Conclusion:}`
- Listes `itemize` ou `enumerate`
- Sauts de ligne forces (`\\`) qui simulent une structure

**Action** : si un structured abstract est detecte sans indication explicite
qu'il est requis, le convertir en prose continue. Demander a l'utilisateur
en cas de doute sur le journal cible.

**R13.3 -- Contenu interdit : Material and Methods detailles**

L'abstract ne contient **pas** de description detaillee de protocoles
experimentaux. Une phrase synthetique sur l'approche suffit.

| Mauvais (trop detaille) | Bon (synthetique) |
|---|---|
| "DNA was extracted using the Qiagen DNeasy Blood & Tissue Kit, libraries were prepared with Illumina TruSeq Nano DNA, sequenced on a NovaSeq 6000, reads were trimmed with Trimmomatic v0.39 and aligned with BWA-MEM v0.7.17 against H37Rv (NC_000962.3)..." | "We sequenced 342 MTBC isolates by Illumina short-read sequencing and aligned reads against the H37Rv reference." |
| "P-values were computed using a two-sided Wilcoxon rank-sum test with Bonferroni correction implemented in scipy.stats..." | "Statistical comparisons used non-parametric tests with multiple-testing correction." |

**Patterns a detecter** :
- Noms de kits commerciaux (Qiagen, Illumina TruSeq, NEBNext, ...)
- Versions logicielles (`v0.7.17`, `version 2.4`, ...)
- Numeros d'accession techniques (sauf reference d'organisme principal)
- Parametres numeriques de pipeline (`--min-coverage 30`, `q-value < 0.05`...)
- Listes de logiciels (`BWA, GATK, samtools, bcftools, ...`)

**R13.4 -- Contenu interdit : references et renvois**

L'abstract est **autonome** : il ne renvoie pas au reste du manuscrit ni
a la litterature externe.

- **Citations interdites** : `\cite`, `\citep`, `\citet`, `\citeauthor`,
  `\citeyear`, `\bibcite`, ainsi que toute reference textuelle du type
  "(Smith et al., 2020)" ou "[1]"
  (rare exception : certains journaux autorisent une citation unique
  pour un dataset ou un travail anterieur fondateur)
- **Renvois internes interdits** : `\ref`, `\cref`, `\Cref`, `\autoref`,
  `\eqref`, `\pageref`, ainsi que les renvois textuels "Figure 1",
  "Table 2", "see Section 3", "as discussed below", "(see Methods)"

**R13.5 -- Equations et flottants**

- Pas d'equations en display mode (`\begin{equation}`, `\[...\]`, `$$...$$`)
- Une expression mathematique inline simple est tolerable si necessaire
- Aucun `\begin{figure}`, `\begin{table}`, `\includegraphics` dans l'abstract

**R13.6 -- Acronymes dans l'abstract**

L'abstract est un document autonome. Les acronymes y sont definis
independamment du corps du manuscrit :

- Acronymes universels du domaine cible : utilisables sans definition
  (DNA, RNA, PCR, SNP, WGS, NGS, HIV, TB, MDR, XDR, WHO, CDC...)
- Acronymes specifiques : definir a la premiere occurrence dans l'abstract
  s'ils sont utilises au moins deux fois
- Acronymes utilises une seule fois : prefer la forme longue, supprimer l'acronyme

**R13.7 -- Style et meta-references**

A traquer et reformuler :
- "In this paper/study/work, we..." repete (acceptable une fois en ouverture,
  pas plus) → varier les formulations
- "This paper presents...", "The present study aims to..." → tournures lourdes,
  prefer une formulation directe ("We show that...", "We characterize...")
- "Our results show that our approach is better than other approaches" →
  trop vague, etre precis sur le gain

**R13.8 -- Conclusion**

Un abstract se termine par **une seule phrase** de conclusion / implication.
Pas de section "Discussion" : la nuance et les limites vont dans le corps
du manuscrit.

**Actions globales R13** :
1. Extraire le contenu textuel de l'abstract et compter les mots
2. Lancer les detections automatiques :
   ```
   grep -E '\\(cite|citep|citet|citeauthor|ref|cref|Cref|autoref|eqref)'
   grep -E '\\(section|subsection|paragraph)\{'
   grep -E '\\textbf\{(Background|Methods?|Results?|Conclusions?|Objectives?|Aims?)'
   grep -E '\\begin\{(itemize|enumerate|equation|align|figure|table)\}'
   ```
3. Pour chaque violation, proposer une reformulation
4. Afficher un compte-rendu specifique :
   ```
   Abstract :
     Longueur     : N mots (cible: 150-250)
     Citations    : 0 (OK) / N detectees (a supprimer)
     Renvois      : 0 (OK) / N detectees (a supprimer)
     Structure    : prose continue (OK) / structured abstract detecte
     Methods      : synthetique (OK) / details de pipeline detectes
     Acronymes    : N definis, M non definis (verifier si universels)
   ```

---

## Phase 3 -- Application des corrections

1. **Traiter l'abstract en premier** : appliquer R13 (longueur, structure, contenu
   interdit, citations, renvois, methods detailles, acronymes, meta-references).
   L'abstract est un cas special qui justifie un passage dedie.
2. Appliquer ensuite les corrections **section par section**, en commencant par
   l'introduction
3. Pour chaque section (hors abstract) :
   - Appliquer R1 a R12
   - Relire la section corrigee pour verifier la fluidite
   - Ne pas denaturer le propos : la forme change, pas le fond
4. Afficher un resume apres chaque section corrigee :
   ```
   Abstract corrige :
     - 287 mots → 234 mots (cible 150-250 atteinte)
     - 2 citations supprimees
     - 1 \cref retire
     - structured abstract converti en prose
     - 3 details de pipeline retires
   ```
   ```
   Section "Methods" corrigee :
     - 4 \textbf supprimes
     - 2 itemize convertis en prose
     - 1 micro-section fusionnee
     - 3 acronymes corriges
     - 2 noms d'especes mis en italique
   ```

---

## Phase 4 -- Rapport final

```markdown
# Rapport deai-latex

**Article :** [titre]
**Date :** YYYY-MM-DD

## Corrections appliquees

| Regle | Avant | Apres |
|-------|-------|-------|
| R1. Gras abusif | N occurrences | M restantes (justifiees) |
| R2. Listes → prose | N itemize | M restants |
| R3. Micro-sections | N fusionnees | — |
| R4. Acronymes | N corriges | tous definis 1x |
| R5. Noms d'especes | N mis en italique | — |
| R6. Cliches | N reformules | — |
| R7. Paragraphes | N restructures | — |
| R8. Em-dashes | N remplaces | — |
| R9. References | N corrigees | — |
| R10. Temps verbaux | N ajustes | — |
| R11. Divers | N corrections | — |
| R12. Cuisine locale | N references retirees (scripts, repertoires, API internes, classifications privees) | — |
| R13. Abstract | N mots → M mots (cible 150-250), K violations corrigees (citations, renvois, structure, methods detailles) | — |

## Points d'attention restants

[Signaler ce qui n'a pas pu etre corrige automatiquement :
 sections trop courtes a developper, paragraphes a reecrire en profondeur, etc.]
```

---

## Consignes

### Ce que le skill DOIT faire
- Lire TOUT le manuscrit avant de commencer les corrections
- Etre systematique : appliquer chaque regle a chaque section
- Preserver le sens : ne modifier que la forme
- Montrer les corrections au fur et a mesure (pas de modifications silencieuses)
- Reformuler intelligemment, pas mecaniquement (pas de simple find-replace)

### Ce que le skill NE DOIT PAS faire
- Changer le contenu scientifique
- Ajouter des references ou des resultats
- Supprimer des informations factuelles
- Reecrire des phrases correctes juste pour "faire different"
- Appliquer les regles aveuglément : une liste peut etre justifiee,
  un \textbf peut etre voulu, un "Furthermore" peut etre le bon mot


---

## Epilogue -- Resume et suggestion de suite

A la **fin de chaque invocation** (apres le rapport, le registre, ou la derniere
action du skill), ajouter systematiquement un bloc de cloture pour l'humain.

### Resume de session

Rappeler en 3-5 lignes :
- Ce qui vient d'etre fait dans cette invocation
- L'etat actuel du manuscrit (claims verifies, review en cours, references OK...)
- Les fichiers produits ou modifies

### Suggestion de prochaine etape

Evaluer l'etat global du manuscrit et proposer **la ou les commandes prioritaires**
parmi le pipeline de qualite :

| Commande | Quand la suggerer |
|----------|-------------------|
| `/claim-check` | Claims non verifies, article modifie depuis dernier run, ou jamais execute |
| `/bib-check` | References non verifiees, nouvelles refs ajoutees, ou jamais execute |
| `/deai-latex` | Article jamais passe au peigne stylistique, ou modifie substantiellement depuis |
| `/manuscript-review` | Article pret pour une evaluation globale, ou modifications majeures appliquees |
| `/lit-review [sujet]` | Un sujet necessite un approfondissement bibliographique |
| `/reviewer-response` | Une review existe non encore traitee, ou traitement en cours |
| `/reviewer-response next` | Remarques en attente dans la review active |

**Format de la suggestion** :

```
━━━━ Prochaine etape suggeree ━━━━

Le manuscrit a ete modifie par cette session. Je recommande :

  1. /claim-check --force    ← re-verifier les claims apres les modifications
  2. /bib-check              ← verifier les nouvelles references ajoutees

(ou /reviewer-response next s'il reste des remarques en attente)
```

Si a ton sens le travail est **termine** (toutes les reviews traitees, claims
verifies, bib OK, texte nettoye), le dire clairement :

```
━━━━ Etat du manuscrit ━━━━

Le manuscrit semble pret pour soumission/resoumission :
  ✅ Claims verifies (claim_check.md : 0 infirme)
  ✅ References verifiees (34/34, 0 suspecte)
  ✅ Review traitee (14/14 remarques resolues)
  ✅ Style normalise (deai-latex applique)

Aucune action supplementaire identifiee.
```
