---
name: deai-latex
description: >-
  Applique les regles de style scientifique a un article LaTeX : supprime le gras abusif,
  convertit les listes a puces en prose, fusionne les micro-sections, verifie les acronymes
  (definis une seule fois), met les noms d'especes en italique, elimine les cliches
  redactionnels et ameliore la coherence des temps verbaux. Fait aussi l'ECONOMIE DU TEXTE :
  coupe le narratif des essais infructueux qui n'apprennent rien, elimine les redites entre
  sections, mesure la longueur face a la limite de la revue cible et bascule le materiel de
  moindre impact vers les supplementary materials. Detecte aussi les jetons \texttt{} longs
  et non coupables (checkpoints, chemins, accessions a underscores) qui debordent
  silencieusement la marge sans le signaler dans le log de compilation. A utiliser quand
  l'utilisateur demande de nettoyer les marqueurs de texte genere par IA, de retirer les
  tirets cadratin, de depuceliser un texte trop liste, de raccourcir un manuscrit trop long,
  de supprimer les repetitions, d'alleger le recit des pistes qui n'ont mene nulle part,
  d'harmoniser le style d'un manuscrit, de corriger un identifiant ou un nom de fichier qui
  deborde de la marge, ou avant une soumission.
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
detection de cuisine locale. Le script du skill les rend, **et couvre aussi R1,
R2, R8 et R9 en un seul passage** (ajoute le 2026-08-01 : ces quatre comptages
etaient auparavant improvises au grep a chaque invocation) :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/deai-latex/scripts/latex_metrics.py main.tex --pdf main.pdf
```

Il rend la longueur de l'abstract (comptee sur le texte REELLEMENT rendu) avec sa
plage de conformite, le nombre de `\textbf` dans le corps (R1), d'environnements
`itemize`/`enumerate` (R2), les paragraphes trop longs (R7, voir ci-dessous), de
tirets cadratins (R8), les labels jamais reference (R9, orphelins de
`\ref`/`\cref`/`\Cref`/`\autoref`/`\eqref`), et les occurrences de cuisine locale
visibles dans le PDF (R12). Ce sont des SIGNAUX a examiner avec le contexte sous
les yeux, pas des verdicts automatiques : un `\textbf` en legende, en en-tete de
tableau ou en label de `description` reste legitime (voir R1 ci-dessous), et un
paragraphe FLAG peut etre une description de protocole ou une table transposee
en prose qui a legitimement besoin de place ; le script ne fait que remonter le
compte pour eviter de le re-derive a la main (R7) ou a l'oeil (R1/R2/R8/R9) a
chaque manuscrit. Passer `--pdf` suppose le manuscrit compile ; sans PDF, seul
le scan R12 est saute et il faut le signaler comme non fait (ne PAS le remplacer
par un grep sur le source : voir R12, "Test final").
R3 a R6, R10, R11 et R13.2-R13.8 restent une lecture attentive, pas un script :
ce sont des jugements de style/coherence, pas des comptages structurels surs.

**Economie du texte (R14, R15, R16)** -- trois mesures qui exigent de comparer des
passages DISTANTS, chacun correct isolement, ce qu'une relecture lineaire ne fait
jamais. Second script, meme repertoire :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/deai-latex/scripts/content_economy.py main.tex
python3 ${CLAUDE_PLUGIN_ROOT}/skills/deai-latex/scripts/content_economy.py main.tex --limit 6500
```

Il resout les `\input`/`\include`, rend la longueur DECOMPOSEE (texte seul / resume
inclus / legendes incluses -- une limite de revue porte sur l'un de ces perimetres
et presque jamais sur le meme), la masse par section, les n-grammes partages entre
sections (redite quasi verbatim), la carte des jetons numeriques presents dans
plusieurs sections du corps (un chiffre redonne trois fois = raisonnement refait au
lieu d'etre synthetise), les passages a marqueur d'essai infructueux, et
l'inventaire du supplementaire existant. `--limit` prend la limite de la revue cible
**apres l'avoir lue dans le guide auteurs**, jamais de memoire.

Comme pour R1/R2/R8/R9, ce sont des SIGNAUX : un chiffre partage entre trois
sections peut etre la longueur de la proteine (legitime), un marqueur de negatif
peut annoncer un resultat publiable. Le script remonte les passages, le tri se fait
avec le contexte sous les yeux.

```
Diagnostic deai-latex :
  Langue           : [francais/anglais]
  Abstract         : N mots (cible 150-300), [violations detectees ou OK]
  Sections         : X (dont Y sous-sections < 5 lignes)
  \textbf dans le corps : N occurrences
  Environnements itemize : N
  Environnements enumerate : N
  Paragraphes trop longs (R7) : N (mise en page : deux/une colonne, seuils WARN/FLAG)
  Acronymes trouves : N (dont M non definis, P definis plusieurs fois)
  Noms d'especes non italiques : N
  Cliches rédactionnels detectes : N (details en Phase 2)
  Longueur totale     : N mots texte seul / M resume inclus  [vs limite revue : ...]
  Masse par section   : Results N (X %), Discussion M, Methods P
  Redites             : N n-grammes partages, M chiffres dans >= 3 sections
  Narratif d'echec    : N passages a trier (informatif vs impasse de chantier)
  Supplementaire      : N fichiers, M renvois depuis le corps
  Jetons non coupables (R17) : N (dont M FLAG >= 20 car.) -- a verifier apres compilation
  Debordement de marge (R18) : N mot(s) > 2pt -- mesure sur le PDF rendu, chaque langue
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

**Ne pas juger la longueur sur les lignes du SOURCE .tex, ni a l'oeil** *(piege
vecu, Rv3222c 2026-08-12, defaut vecu)*. Le retour a la ligne dans le fichier
`.tex` est arbitraire (~100 caracteres, choix de l'editeur) et n'a **aucun**
rapport fiable avec l'occupation reelle dans un PDF a deux colonnes : un
paragraphe de 759 mots, largement sous la vigilance d'un seuil pense en
"lignes source", s'est etale sur **PRESQUE DEUX COLONNES PLEINES** d'un article
en relisant le PDF compile -- c'est exactement le meme piege que R13.1 (compter
a la main un abstract donne un chiffre faux mais credible). Utiliser :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/deai-latex/scripts/latex_metrics.py main.tex
```

Le script (i) detecte la mise en page (deux colonnes : option `twocolumn`,
elsarticle `3p`/`5p`, ou classe a deux colonnes par defaut comme IEEEtran,
acmart, revtex4 ; une colonne : option `1p`/`onecolumn`, ou classe a une
colonne par defaut comme `article`/`report`/`book`/elsarticle sans option/
KOMA-Script/amsart, sauf `\twocolumn` explicite dans le document ; seulement
si la classe est reellement inconnue, hypothese prudente deux colonnes --
correctif du 2026-08-26, avant quoi `article` sans option tombait a tort dans
ce dernier cas, cf. faux WARN vecu sur Rv0810c le 2026-08-17), (ii) compte les
mots RENDUS de chaque paragraphe de prose
(memes regles de rendu que R13.1 : `\emph`/`\textit`/... gardent leur
contenu, `\cite`/`\label`/... sont retires, une formule `$...$` compte pour un
mot), en excluant les blocs qui contiennent un flottant, une liste, un titre de
section ou un `\begin{...}` (pas des paragraphes de texte courant). Seuils,
calibres sur l'incident ci-dessus (un decoupage en 5 paragraphes de 140 a 215
mots donnait, sur ce meme document en deux colonnes, des paragraphes de 1/3 a
1/2 colonne chacun, visuellement normaux) :

| Mise en page | WARN (a surveiller) | FLAG (a scinder) |
|---|---|---|
| Deux colonnes (`3p`/`5p`/`twocolumn`/IEEEtran) | >= 300 mots | >= 450 mots |
| Une colonne (`1p`/`onecolumn`/classe generique) | >= 500 mots | >= 750 mots |

**Actions** :
- **Paragraphes d'une seule phrase** : fusionner avec le paragraphe
  precedent ou suivant
- **Paragraphes identiquement structures** (tous commencent par
  "Regarding X, ...", ou tous suivent le pattern claim-evidence-conclusion) :
  varier les structures
- **Paragraphe FLAG ou WARN par le script** : chercher une frontiere de sens
  DEJA marquee dans le texte lui-meme avant d'en inventer une -- un paragraphe
  qui accumule plusieurs preuves independantes le dit souvent explicitement
  ("A second, paired control...", "A third, orthogonal control...",
  "What the data reveal instead is...") ; scinder a ces frontieres est un
  simple ajout de ligne vide, **jamais une reecriture** (ne pas reformuler
  les phrases adjacentes pour "lisser" la coupe, cf. R14/R15/R16 : la forme
  change, pas le fond). Si aucune frontiere naturelle n'existe et que le
  paragraphe traite reellement une seule idee indivisible, un FLAG isole peut
  rester (signal a relire, pas un verdict automatique) -- mais le cas est rare
  au-dela de 450 mots.
- Un paragraphe FLAG sur une section a forte densite tabulaire (description
  organisme-par-organisme, protocole etape par etape) est un candidat naturel
  a la bascule en supplementaire (R16), pas seulement a la scission.

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

### R17. Jetons longs non coupables (identifiants, checkpoints, chemins, accessions)

**Regle** : tout `\texttt{}` (ou `\verb`) portant un identifiant technique --
checkpoint de modele, chemin de fichier, accession, hash -- doit rester **coupable**
en fin de ligne justifiee. Un `\_` (underscore echappe) est une **macro**, jamais un
caractere ordinaire : il n'offre par construction **aucun** point de rupture a TeX,
contrairement a un tiret litteral (`-`) ou une espace, que TeX sait rompre meme en
police `\texttt`. Un identifiant long compose uniquement de lettres/chiffres/`\_`
est donc un bloc **entierement insecable**, qui deborde silencieusement la marge
des qu'il tombe pres de la fin d'une ligne -- sans qu'il faille attendre une
soumission ou une relecture pour le decouvrir.

**Incident fondateur (Rv1557, 2026-08-29)** : `\texttt{esm1v\_t33\_650M\_UR90S\_1}`
(22 caracteres, aucun tiret) a fait deborder la marge droite de pres de 2cm dans le
PDF compile. **Piege decouvert a cette occasion, imperatif a retenir** : le log
`pdflatex` n'est **pas fiable** pour cette classe de defaut -- sur les DEUX
versions linguistiques du meme manuscrit, portant le meme `\texttt{}` au meme
endroit structurel, la version anglaise a emis un `Overfull \hbox`, la version
**francaise n'a rien signale du tout**, alors que le meme debordement visuel de
~59pt y etait bel et bien present (confirme par mesure de pixels sur le PDF
rendu). **Ne jamais conclure "aucun Overfull dans le log = aucun debordement"**
pour ce type de contenu : c'est precisement l'inverse de ce qu'un log propre
donne a croire.

**Detection** : `latex_metrics.py` (Phase 1) scanne desormais le SOURCE --
avant toute compilation, donc independamment du piege de log ci-dessus -- pour
tout `\texttt{}`/`\verb` sans tiret ni espace, a partir de 15 caracteres (`WARN`,
signal a verifier visuellement une fois compile) et 20 caracteres (`FLAG`, palier
de l'incident reel). Un `WARN` court (ex. une sequence ADN de 15 pb citee entre
`\texttt{}`) n'est pas forcement fautif -- verifier avec le contexte, comme pour
R1/R2/R8/R9 -- mais tout `FLAG` doit etre corrige.

**Actions** :
- Remplacer `\texttt{esm1v\_t33\_650M\_UR90S\_1}` par `\path{esm1v_t33_650M_UR90S_1}`
  (package `url`, deja charge via `hyperref` -- underscores **litteraux**, pas
  echappes, `\path` lit son argument en mode verbatim). `\path` casse
  automatiquement aux underscores, points et slashes quand la ligne l'exige, et
  rend dans la meme police que `\texttt` (`\ttfamily`) : aucun changement visuel
  quand la coupure n'est pas necessaire.
- **Dans un `\caption{}`, un titre de section, une note de bas de page ou tout
  autre argument mobile** : `\protect\path{...}`, sinon erreur fatale a la
  compilation (`\Url Error -> \url used in a moving argument`) -- vecu sur
  `figures/icons/ATTRIBUTION\_icons.tex` dans une legende de figure, corrige de
  la meme session.
- **Ne jamais utiliser `\seqsplit{}` seul sur un contenu portant des `\_`
  echappes** : `\seqsplit` scanne caractere par caractere et ne sait pas
  interpreter une macro comme `\_` -- `\texttt{\seqsplit{esm1v\_t33\_650M\_UR90S\_1}}`
  produit `! Undefined control sequence.` a la compilation (essaye et ecarte sur
  cet incident). `\seqsplit` reste utile pour un jeton SANS caractere special
  LaTeX (un hash hexadecimal, un DOI deja compose de chiffres/lettres/points) --
  jamais pour un identifiant a underscores.
- **Test final, imperatif au vu du piege de log ci-dessus** : recompiler et
  **rendre visuellement la page concernee** (`pdftoppm -r 200`, `Read` sur le
  PNG, ou a defaut comparer la longueur de la ligne `pdftotext -layout` porteuse
  du jeton a celle des lignes voisines) plutot que de se fier a l'absence
  d'`Overfull \hbox` dans le log -- et refaire ce test sur **chaque version
  linguistique** du manuscrit, jamais une seule : le meme defaut peut se
  manifester dans le log de l'une et rester totalement silencieux dans l'autre.

### R18. Debordement de marge sur le PDF rendu (tableaux, titres, contenu large)

**Regle** : tout mot dont la boite deborde la marge de droite du texte, quelle
qu'en soit la cause (tableau a trop de colonnes, titre de section trop long,
URL longue), doit etre corrige -- **y compris un debordement deja present dans
une passe precedente**. Un `Overfull \hbox` connu depuis plusieurs sessions
n'est pas moins reel qu'un nouveau : ce que change une session qui le revoit
n'est pas sa realite mais seulement l'attention qu'on lui porte.

**Incident fondateur (Rv0007, 2026-09-01)** : un `tabular{lccccc}` a six
colonnes debordait la marge droite de ~37pt (~1,3cm) sur son en-tete "Complex
pLDDT" -- signale par un `Overfull \hbox (43.15652pt too wide)` present dans le
log **depuis la toute premiere compilation de la session**, mais ecarte a
chaque relecture comme "avertissement pre-existant, deja vu, sans regression" --
sans jamais etre revisualise. C'est l'utilisateur, pas l'outillage, qui a
repere le debordement a l'oeil dans le PDF final. Reprise systematique au
moyen d'une mesure de bounding-box (`pdftotext -bbox-layout`) plutot que d'une
relecture visuelle seule (qui avait deja echoue une fois sur ce meme
manuscrit) : deux autres debordements reels sont apparus, plus discrets --
un titre de sous-section trop long (`peptidoglycan-synthase`, 51pt) et deux
paragraphes de Methods/Data availability portant un `\texttt{}`/`\url{}` en
fin de ligne (3,5 a 8,8pt), aucun des trois signale au meme endroit dans les
deux versions linguistiques (meme piege que R17).

**Detection** : `latex_metrics.py --pdf <compile>.pdf` (Phase 1) lit la marge
de droite dans le preambule (`\usepackage[margin=...]{geometry}` ou
`right=...`) puis mesure, via `pdftotext -bbox-layout` sur le PDF **rendu**,
la position de chaque mot de chaque page. Seuil de negligeabilite : 2pt (sous
ce seuil, invisible a l'impression -- calibre sur un 0,97pt de legende du meme
manuscrit, laisse tel quel a bon droit). R18 se desactive proprement (et le
signale) si la marge n'est pas reconnaissable dans le preambule plutot que de
deviner une valeur.

**Actions, du cas le plus frequent au plus rare** :
- **Tableau trop large** : `\small` (ou `\footnotesize`) juste avant
  `\begin{tabular}` (`\begin{table}` scope la commande : pas de `\normalsize`
  a remettre apres `\end{table}`), et/ou raccourcir un en-tete de colonne deja
  redondant avec la legende ("Complex pLDDT" -> "pLDDT" quand la legende dit
  deja "predicted lDDT of the complex (pLDDT)"). `\small` seul ne suffit pas
  toujours : mesurer a nouveau plutot que de supposer la correction acquise.
- **Titre de section trop long** : `\\` manuel dans l'argument de
  `\section{}`/`\subsection{}`, place a la meilleure coupure syntaxique
  (apres un adjectif compose, jamais au milieu d'un groupe nominal).
- **Paragraphe de prose legerement overfull sans jeton isole responsable**
  (justification tendue par l'accumulation de mots, pas par un seul token
  insecable -- distinct de R17) : envelopper le seul paragraphe concerne dans
  `\begin{sloppypar}...\end{sloppypar}` plutot que de reformuler le contenu
  scientifique -- convertit l'Overfull en un Underfull (espacement legerement
  plus lache, jamais un debordement visible), sans toucher au texte.
- **Jeton `\texttt{}` isole responsable** (ex. `rest.uniprot.org`, sous le
  seuil FLAG de R17 mais reellement debordant en pratique) : meme correction
  que R17, `\path{}`.
- **Test final, imperatif** : recompiler puis relancer `latex_metrics.py
  --pdf` sur **chaque version linguistique separement** -- "aucun
  debordement > 2pt" doit apparaitre pour les deux, jamais suppose de l'une a
  l'autre.

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
| Auto-reference narrative au labo/projet comme sujet | *"the group's own earlier work"*, *"across the group's MTBC projects"*, *"the project's null-model infrastructure"*, *"the rest of the project"*, *"our team's pipeline"* | Reformuler sans sujet grammatical "le groupe"/"le projet" : soit citer le travail anterieur publie (`\citep{...}`), soit decrire la methode en prose sans meta-reference organisationnelle |
| Note de suivi interne laissee dans le texte (TODO destine a une session future) | *"this should be repeated ... before formal submission, not treated as a substitute for it"*, *"a verifier au prochain passage"*, *"reste a faire avant soumission"* | Ce n'est jamais un defaut de forme a reformuler : c'est la preuve que l'action n'a pas ete faite. Executer l'action (ou la retirer si elle ne s'applique plus), PUIS retirer la phrase -- ne jamais neutraliser seulement la phrase |

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

**Apprentissage 2026-08-26 (SpacerEgalVirus)** : la regex ci-dessus ne detecte
QUE la cuisine locale a signature de chemin/fichier. Deux formes distinctes de
"raconter sa vie" lui echappent totalement, car ce sont des phrases de prose
sans aucun slash ni extension -- elles ont survecu telles quelles a un
`/manuscript-review` ET a un `/deai-latex` complets : (1) l'**auto-reference
narrative**, ou "le groupe" ou "le projet" devient le sujet grammatical d'une
phrase du corps (*"correcting an assumption occasionally repeated in the
group's own earlier work"*) -- un lecteur externe n'a aucun interet a savoir
qu'une hypothese anterieure DU LABO etait fausse, seul l'etat de connaissance
actuel compte ; (2) la **note de suivi interne**, phrase imperative ou au futur
qui s'adresse a une session de travail future et non au lecteur (*"this should
be repeated through [la base interne] before formal submission, not treated as
a substitute for it"*, trouvee dans une section Limitations censee etre
soumise en l'etat). Une note de ce type prouve a elle seule que la porte 3 du
cycle de vie (`/cycle-projet`, point fixe de redaction) n'est PAS franchie,
quel que soit l'etat des registres claim-check/bib-check/fig-check : elle est
donc a chercher explicitement, a l'oeil, dans la Discussion et les Limitations,
sans attendre qu'un script la trouve. Recherche manuelle minimale avant de
declarer R12 acquis :
```
grep -inE "\b(the (group|project|team|lab(oratory)?)('s)?|our (group|project|team|lab))\b.{0,60}(work|infrastructure|pipeline|projects?|classification)" main.tex
grep -inE "(should be (repeated|redone|revisited)|reste (a|à) (faire|verifier|verifier)|a (verifier|refaire) au prochain|before (formal )?submission,? not)" main.tex
```

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

## Phase 2bis -- Economie du texte (R14 a R16)

Les trois regles qui suivent ne portent ni sur la typographie ni sur le style de
phrase : elles portent sur **ce qui a le droit d'occuper de la place**. Elles
s'appliquent dans l'ordre R14 -> R15 -> R16, parce que chacune reduit la matiere
sur laquelle travaille la suivante.

**Quand les passer.** Si une contrainte de longueur existe (limite de la revue
cible, ou manuscrit visiblement long), les passer **AVANT** R1-R13 : polir la
typographie d'un paragraphe qu'on va supprimer est du travail perdu. Sinon, les
passer apres, en fin de session.

### R14. Le narratif des essais infructueux

**Regle.** Un article rapporte un **etat de connaissance**, pas la **chronologie du
chantier**. Le cahier de laboratoire garde l'histoire des tentatives : c'est sa
fonction, et c'est la seule trace dont le projet a besoin. Un echec n'entre dans le
manuscrit que s'il **apprend quelque chose a un lecteur qui n'a jamais su qu'on
avait essaye**.

**Test a appliquer passage par passage (test du lecteur ignorant)** : un lecteur qui
ignore totalement cette tentative tire-t-il une conclusion differente, ou refait-il
la meme erreur ? Si non aux deux, le passage sort.

**Les quatre cas ou un negatif MERITE sa place** :

1. **Il refute ou borne un claim que le lecteur porterait sinon** : affirmation
   publiee, attente standard du domaine, cadrage initial du projet s'il a circule.
   (Ex. la vulnerabilite CRISPRi de Rv3222c : le retrait est un resultat, parce que
   le chiffre est dans une base que d'autres liront.)
2. **Il sert de controle** : modele nul, controle positif, controle negatif. Sans
   lui le positif voisin n'est pas credible. Il n'est alors pas un echec, c'est la
   moitie de la mesure.
3. **Il borne l'espace de recherche** : « cherche dans A, B et C au seuil S, rien
   trouve » est un resultat d'exhaustivite, qui contraint l'interpretation.
4. **C'est un piege methodologique qu'un tiers reproduirait a ses frais.** Il va
   alors en Methodes ou en note supplementaire, en **une phrase impersonnelle**
   (« la mesure sur assemblage complet fabrique un faux signal de proximite »), pas
   en recit.

**Ce qui n'a aucune place, quelle que soit la reussite finale** :

- la chronologie des tentatives (« nous avons d'abord essaye X, puis bascule sur Y ») ;
- un outil ecarte sans que la raison n'apprenne rien au lecteur ;
- les **peripeties d'acces a une ressource** : telechargement bloque, page editeur
  en 403, route de repli, quota d'API, fichier recupere a la main. Le lecteur veut
  la **provenance** de la donnee, pas l'itineraire pour y arriver ;
- un negatif sur une hypothese que personne n'avait (refuter ce que nul n'a suppose
  n'informe pas) ;
- un negatif deja implique par un autre negatif rapporte : n'en garder que le plus
  informatif ;
- la mention d'un calcul lance puis juge non concluant, quand rien n'en depend.

**Reecriture** :

| Avant (recit) | Apres (etat de connaissance) |
|---|---|
| « We first attempted a BLAST search, which returned no usable homolog, and therefore turned to profile-based methods. » | « No homolog is detectable by profile-based methods (HHpred, top hit E = 1300). » |
| « The Europe PMC supplementary route and the PMC HTML page were both blocked, so the table was obtained directly from the publisher. » | « Data from the supplementary tables of [ref]. » |
| « Our first co-folding run used the wrong stoichiometry and was discarded. » | (supprimer) |
| « Docking was attempted but the pocket predictions were unstable, so this line was abandoned. » | (supprimer, ou -> note supplementaire si le lecteur risque de refaire l'essai) |

**Regle de puissance, non negociable pour tout negatif conserve.** Un negatif sans
sa **puissance de detection** n'est pas interpretable et se retourne contre l'auteur
en review : dire ce qui a ete cherche, **avec quoi**, **a quel seuil**, **dans quelle
version de quelle base**. C'est ce qui transforme une absence en resultat. Un
negatif qu'on ne sait pas doter de sa puissance est un negatif a supprimer, pas a
nuancer.

**Ce qu'il ne faut PAS faire** : supprimer un negatif informatif pour faire propre.
Un resultat negatif citable est un actif du manuscrit (et la discipline en manque) ;
c'est le **recit** des impasses qui est du remplissage, pas le negatif lui-meme.

### R15. Redites

**Regle.** Une information est enoncee **une fois** a sa place, et **rappelee** au
plus une fois ailleurs, sous forme de conclusion et non de demonstration. Le lecteur
qui lit trois fois le meme chiffre ne le retient pas mieux : il en deduit que
l'article n'est pas tenu.

**Trois formes de redite, de la plus facile a la plus dangereuse** :

1. **Quasi verbatim** : la Discussion recopie les phrases des Resultats. Detectee
   par les n-grammes partages du script. Symptome type de l'edition par accretion.
2. **Numerique** : le meme chiffre reapparait dans trois sections, avec son
   raisonnement refait a chaque fois. Detectee par la carte des jetons numeriques.
3. **Thetique** : la meme these est affirmee en Introduction, en Resultats, en
   Discussion et en Conclusion, chaque fois avec d'autres mots. **Aucun script ne la
   voit** : elle se lit en mettant cote a cote les sections de synthese.

**Repetitions LEGITIMES, a ne pas toucher** : l'abstract redit (il est autonome) ;
la Conclusion redit en une phrase ; un chiffre rappele **une** fois en Discussion
pour ouvrir une interpretation. La frontiere est simple : **les Resultats etablissent,
la Discussion interprete.** Un paragraphe de Discussion qu'on peut supprimer sans
perdre une interpretation etait un doublon.

**Reecriture** : remplacer la redite par une conclusion et un renvoi.

> « Rv3222c's essentiality is supported by four independent lines: seven TA sites all
> uniquely mappable, six genomes across five lineages, an empirical anti-polarity
> control, and p ~ 1e-7 under H0 » (Discussion, chiffres redonnes en entier)
>
> devient
>
> « Essentiality is robust to the mappability and polarity objections (\cref{sec:essentiality}). »

**Gain mesure** sur un manuscrit reel (dark_enzymes, FEMS) : **~630 mots** sur ce
seul levier, sans perdre un chiffre ni une citation.

**Controle de coherence a passer dans la foulee** (defaut jumeau de la redite,
introduit par les memes ajouts successifs) : relire abstract, Discussion et
Conclusion **contre** le corps. Traquer les compteurs figes (« trois elements »,
« deux raisons ») qu'un ajout au corps a rendus faux, les resultats ajoutes que
la Discussion ne reprend nulle part, et le diff conceptuel Introduction <-> Conclusion
(si l'intro dit « ce n'est pas X mais Y » et que la conclusion s'ouvre sur X, c'est
casse). Deux minutes, et c'est le defaut le plus grave que ce skill puisse attraper.

### R16. Longueur totale, limite de la revue, et bascule en supplementaire

**Regle.** La longueur n'est pas une question cosmetique : **elle decide de la liste
des revues auxquelles l'article peut etre soumis**. Un manuscrit qui grossit sans
surveillance se ferme des cibles, et l'auteur ne s'en apercoit qu'au moment de
choisir, quand tout est ecrit.

> [!IMPORTANT]
> **Mais la revue n'arbitre ni l'article, ni le message, ni la longueur** (regle CG
> 2026-09-09). On mesure la longueur pour SAVOIR quelles cibles restent ouvertes,
> jamais pour amputer une demonstration qui a besoin de sa place. Si aucune revue
> n'admet la taille que la demonstration exige, **le preprint (bioRxiv, HAL) est une
> reponse legitime**, et l'amputation n'en est pas une. Un beau travail bien ecrit et
> depose vaut mieux qu'une compromission editoriale payee en qualite scientifique.

**Contrepartie amont.** Cette regle est curative : elle coupe des mots deja ecrits.
Sa jumelle preventive est le skill **`/narratif`**, en phase 2, qui decide AVANT
redaction du temps et du lieu de chaque fait. Un manuscrit passe par `/narratif` puis
ecrit le long de son squelette arrive ici avec peu a couper — et ce qui reste a couper
est signale par son propre plan, pas devine.

**Mesure**. Le perimetre sur lequel une revue exprime sa limite varie (texte seul ;
resume inclus ; legendes et references exclues presque toujours). Le script rend les
trois. **Verifier la limite et son perimetre dans le guide auteurs de la revue
(WebFetch), ne jamais les supposer.**

**Ordre des leviers -- il n'est pas interchangeable** (verifie sur dark_enzymes,
7779 -> 6500 mots) :

0. **Mesurer la derive contre le plan narratif, s'il existe.** Une section sans ligne
   `% narratif:` est une section que personne n'a decidee : c'est la premiere a
   examiner, et souvent la seule a supprimer entierement.

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/narratif/scripts/plan_vs_manuscrit.py [projet]
   ```

   Le script rend aussi les sections tres au-dela de leur taille visee et les items
   classes SUPPLEMENTAIRE que le corps developpe malgre tout. **Signal, jamais
   verdict** : une derive peut etre legitime, la redaction decouvre des choses. Elle
   se corrige alors AU PLAN, datee et motivee, jamais en silence.
1. **Epuiser les redites (R15) d'abord.** Rendement le plus eleve, perte nulle.
2. **Migrer, jamais reecrire, vers le supplementaire.** Le materiel supplementaire
   ne compte pas dans la limite de mots de la plupart des revues (le **verifier** :
   FEMS l'ecrit explicitement, d'autres non).
3. **Polir phrase par phrase en dernier.** Rendement marginal faible ; ne s'applique
   proprement qu'a la prose connective qui reste une fois les deux leviers
   structurels epuises. Le faire en premier revient a sacrifier du contenu qui
   n'avait pas besoin de l'etre.

**Ce qui migre** (materiel de moindre impact, forte valeur de reproductibilite) :
protocoles de controle detailles, tableaux organisme-par-organisme ou
souche-par-souche, balayages de parametres, geometries completes, versions et
parametres d'outils, negatifs secondaires conserves au titre de R14, methodes
etendues, jeux de donnees derives.

**Ce qui ne migre JAMAIS** : le chiffre qui soutient une conclusion enoncee dans le
corps, et la conclusion elle-meme. **Le corps reste autonome pour ses conclusions ;
le supplementaire n'ajoute que la reproductibilite.** Garder « p = 0,36 » dans le
texte, migrer le detail organisme-par-organisme qui y mene.

**Comment migrer** :
- **verbatim** : la migration est un copier-coller, pas une paraphrase (une valeur
  reecrite en chemin est une valeur qui derive) ;
- **pointeur bidirectionnel** : le corps dit ou regarder (« full geometry in
  Supplementary Note S6 »), le supplementaire dit a quoi il repond ;
- **numerotation** : `Supplementary Table S1`, `Supplementary Note S1`... chaque
  item supplementaire est **cite au moins une fois** dans le corps (meme exigence
  qu'en R9 pour les flottants) ;
- **captions** : un item supplementaire porte une legende autonome, il sera lu hors
  du corps ;
- ne pas laisser de chemin local dans les renvois (`\texttt{supplementary_materials/
  table_S1.csv}` -> « Supplementary Table S1 ») : la revue renomme les fichiers a la
  publication, et c'est une violation de R12.

**Signaux structurels de sous-utilisation du supplementaire**, a signaler meme sans
contrainte de longueur :
- Resultats > ~50 % du corps ;
- une sous-section de plus de ~800 mots faite de procedure pure ;
- **zero fichier supplementaire** pour un manuscrit de plus de ~8000 mots : c'est
  presque toujours que du materiel de reproductibilite est reste dans le corps ;
- des flottants dans le corps qui ne sont jamais commentes au-dela de leur legende.

**Si le manuscrit est bilingue** : la coupe ne vaut que pour la langue soumise ; la
version parallele est mise en miroir **contenu par contenu** (memes migrations,
memes pointeurs vers les memes notes supplementaires), **sans viser le meme compte
de mots**. Verification de parite : comparer les jetons numeriques entre les deux
versions, pas leur longueur.

---

## Phase 3 -- Application des corrections

0. **Passe d'economie du texte (R14 -> R15 -> R16), en PREMIER des qu'une contrainte
   de longueur existe** ou que le diagnostic signale une masse anormale (Resultats
   > 50 %, zero supplementaire au-dela de 8000 mots, redites nombreuses). Elle
   travaille sur des blocs entiers : la passer apres le polish typographique revient
   a polir du texte destine a partir. Sans contrainte de longueur, la reporter en
   fin de session.
   - Soumettre les coupes de R14 et les migrations de R16 **avant** de les
     appliquer : supprimer un negatif informatif ou migrer une conclusion sont des
     erreurs couteuses, et le tri demande le jugement de l'auteur.
1. **Traiter l'abstract** : appliquer R13 (longueur, structure, contenu
   interdit, citations, renvois, methods detailles, acronymes, meta-references).
   L'abstract est un cas special qui justifie un passage dedie. Si la passe 0 a
   coupe ou migre du contenu, verifier que l'abstract ne resume plus un corps qui
   n'existe plus.
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
| R7. Paragraphes | N FLAG + M WARN detectes (script) | K scindes aux frontieres de sens, P laisses (justifies) |
| R8. Em-dashes | N remplaces | — |
| R9. References | N corrigees | — |
| R10. Temps verbaux | N ajustes | — |
| R11. Divers | N corrections | — |
| R12. Cuisine locale | N references retirees (scripts, repertoires, API internes, classifications privees) | — |
| R13. Abstract | N mots → M mots (cible 150-250), K violations corrigees (citations, renvois, structure, methods detailles) | — |
| R14. Narratif d'echec | N passages examines | M coupes, P conserves comme negatifs informatifs (avec leur puissance de detection) |
| R15. Redites | N n-grammes partages, M chiffres multi-sections | K passages remplaces par conclusion + renvoi, −W mots |
| R16. Longueur | N mots (texte seul) | M mots — limite revue L : conforme / depassement de D |
| R16b. Supplementaire | N items avant | M items apres (S1…S{M}), −W mots migres verbatim |
| R17. Jetons non coupables | N WARN + M FLAG (script) | K corriges (`\path{}`), P laisses (WARN benins, verifies) |
| R18. Debordement de marge | N mot(s) > 2pt (script, PDF rendu, chaque langue) | K corriges (`\small`/`\\`/`sloppypar`/`\path{}`), 0 restant |

## Economie du texte -- detail

**Negatifs conserves** (et pourquoi) :
- [passage] — refute [claim publie] / controle de [resultat] / borne l'espace de recherche
  → puissance declaree : [outil, seuil, base, version]

**Negatifs supprimes** : [liste courte, une ligne chacun]

**Migre vers le supplementaire** : [S1 : quoi, depuis quelle section, combien de mots]
Verification : chaque conclusion du corps reste soutenue par un chiffre du corps ;
chaque item S est cite au moins une fois.

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
- **Supprimer un resultat negatif informatif** sous pretexte de R14 : ce qui se
  coupe est le RECIT des impasses, pas le negatif qui borne une conclusion, refute
  un claim publie ou sert de controle
- **Migrer une conclusion, ou le chiffre qui la soutient, vers le supplementaire**
  (R16) : le corps doit rester autonome pour ce qu'il affirme
- **Reecrire une valeur en la migrant** : une migration est un copier-coller verbatim
- Couper phrase par phrase avant d'avoir epuise les redites (R15) et les migrations
  (R16) : c'est l'ordre qui sacrifie du contenu pour rien


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
