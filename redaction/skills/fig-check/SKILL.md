---
name: fig-check
description: >-
  Verification visuelle systematique des figures d'un article scientifique via
  les capacites multimodales. Pour chaque \includegraphics : lisibilite,
  resolution, chevauchements, taille des textes, fleches, palette,
  correspondance figure/legende. Registre fig_check.md ; corrections
  appliquees avec --fix.

  Use when: soumission ou resoumission, figures modifiees, poster, figure
  illisible en PDF final.
argument-hint: "<main.tex> [--force] [--stale-days 90] [--fix]"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# /fig-check -- Verification visuelle des figures d'un article

Parcourt un manuscrit LaTeX, extrait toutes les figures (via
`\includegraphics{}`), localise chaque fichier, **le lit visuellement**
avec les capacites multimodales, et evalue une batterie de criteres de
qualite editoriale et scientifique. Maintient un registre persistant
`fig_check.md` avec statut par figure, dans l'esprit de `/claim-check`
et `/bib-check`.

---

## Prealable -- Consultation memoire projet

**Avant toute action**, verifier si le projet possede :
1. Un `CLAUDE.md` local → instructions specifiques (conventions figures,
   palette de couleurs, standards de publication)
2. Un `cahier_de_labo.md` ou `JOURNAL.md` → historique recent des
   figures regenerees
3. Un `fig_check.md` existant → registre a reprendre

Afficher un bref etat initial :

```
Etat projet : [titre article]
Registre fig-check : [N figures, M OK, P problematiques ou "jamais execute"]
Derniere verification : [date ou "jamais"]
```

---

## Declenchement

```
/fig-check path/to/main.tex
/fig-check path/to/main.tex --force
/fig-check path/to/main.tex --stale-days 180
/fig-check path/to/main.tex --fix
```

- Sans argument : chercher `main.tex` dans le repertoire courant
- `--force` : re-verifier toutes les figures, meme celles validees recemment
- `--stale-days N` (defaut 90) : re-verifier celles verifiees il y a plus
  de N jours
- `--fix` : tenter d'appliquer automatiquement les corrections quand un
  script source regenerable est identifie. Sans cette option, le skill
  se contente de proposer les corrections.

---

## Phase 0 -- Chargement du registre

1. Localiser le `.tex` principal (argument ou `main.tex`).
2. Resoudre les `\input{}` / `\include{}` pour obtenir le texte complet.
3. Chercher `fig_check.md` dans le meme repertoire.
4. Si present : parser le tableau des figures et leur statut/date.
5. Sinon : noter qu'il sera cree en Phase 6.

---

## Phase 1 -- Extraction des figures

Parcourir le manuscrit et extraire **toutes** les figures :

1. `Grep -n '\\includegraphics' main.tex` (et fichiers inclus).
2. Pour chaque occurrence, extraire :
   - **Chemin** du fichier (`{figures/fig2_ml_tree.pdf}`)
   - **Options** `[width=..., height=..., angle=..., ...]`
   - **Environnement englobant** : `figure`, `figure*`, `subfigure`,
     `wrapfigure`, `minipage`
   - **Caption** associee : `\caption{...}` du meme environnement
   - **Label** : `\label{fig:xxx}`
   - **Referencement** dans le texte : `Grep '\\ref{fig:xxx}'`, en excluant
     l'occurrence dans la propre caption/legende de la figure → liste des
     endroits ou la figure est citee depuis la prose (Results, Discussion,
     etc.). Une liste vide est une trouvaille a part entiere, traitee en
     Phase 5 (regle imperative ci-dessous) : une figure incluse mais jamais
     appelee depuis le texte n'a pas sa place dans l'article.
   - **Numero d'apparition** dans l'ordre du PDF (ordre sequentiel dans
     le source .tex)
3. Separer les figures principales des figures de supplementary (detecter
   si un fichier `supplementary_materials/` ou `supp*.tex` est inclus).
4. Deduplication : si deux `\includegraphics` pointent vers le meme
   fichier, compter comme une seule figure, mais noter les deux
   emplacements.

---

## Phase 2 -- Localisation et sanity check technique

Pour chaque figure extraite :

1. **Resolution du chemin** : essayer dans l'ordre
   `<dir>/<path>`, `<dir>/figures/<basename>`, `<dir>/<basename>`.
   Tester les extensions `.pdf`, `.png`, `.jpg`, `.svg` si l'extension
   est absente du code LaTeX.
2. **Existe-t-il ?** Sinon : statut `MISSING`, passer a la suivante.
3. **Taille sur disque** : `ls -l`. Signaler si < 20 Ko (trop petit,
   probablement degrade) ou > 20 Mo (trop lourd, risque de compilation).
4. **Format** : noter PDF / PNG / JPG / SVG. Pour un article publication,
   preferer PDF (vectoriel) ou PNG >= 600 DPI.
5. **Si PDF** : tenter `pdfinfo <fichier>` pour obtenir dimensions en
   points, nombre de pages. Si le binaire n'est pas disponible, utiliser
   la taille par defaut de Read.
6. **Si PNG/JPG** : tenter `identify <fichier>` (ImageMagick) ou `file`
   pour les dimensions en pixels et le DPI. Signaler si < 300 DPI pour
   publication ou si la densite n'est pas identifiable.
7. **Script source detectable ?** : chercher dans le projet un script
   Python ou un Makefile qui produit ce fichier.
   - `Grep -rn "<basename>" analyses/ reproducibility/ scripts/ résultats/scripts/`
   - Chercher un `savefig('...fig2_ml_tree.pdf'...)` ou un output
     Makefile.
   - Si trouve : noter le chemin du script dans le registre (utile en
     mode `--fix`).
8. **Risque de debordement vertical (portrait + `width=\textwidth`)** :
   a partir des dimensions `pdfinfo`/`identify` deja obtenues, calculer le
   ratio hauteur/largeur du fichier. Si ce ratio depasse 1 (image plus
   haute que large -- typiquement un flowchart ou un arbre vertical) **et**
   que le code LaTeX force `width=\textwidth` (ou `width=\linewidth`) sans
   borne de hauteur (`height=`, `keepaspectratio` avec un plafond) : signaler
   un **risque** explicite avant meme la Phase 4, avec l'estimation
   `hauteur_rendue = \textwidth_manuscrit * ratio` (recuperer `\textwidth`
   reel via le petit document de sondage de la Phase 4 ci-dessous, ou a
   defaut estimer ~455pt pour un A4/margin=2.5cm en 11pt). Une image dont la
   hauteur rendue depasse a elle seule ~85% de `\textheight` ne laisse
   quasiment plus de place a la legende : c'est le motif exact qui a fait
   disparaitre la fin de la legende de la Figure 1 de `Rv1557` (flowchart
   CONSORT portrait a `width=\textwidth`, legende de 200 mots) sans qu'aucun
   `Overfull \vbox` ne soit emis dans le log -- LaTeX absorbe silencieusement
   le debordement en bas de page plutot que d'avertir. Ce risque **rend la
   Phase 4 obligatoire** pour cette figure (voir plus bas), meme en l'absence
   de tout autre signal.

### 2bis -- Rendu des formats que `Read` ne sait pas ouvrir

`Read` n'affiche que les formats matriciels. Un SVG ou un EPS reste donc
`UNREVIEWABLE` alors que c'est precisement le format d'export d'iTOL, de
ggtree et de la plupart des cartes : dans un groupe de phylo, laisser ces
figures non inspectees revient a ne pas inspecter les figures principales.
**Avant de classer une figure `UNREVIEWABLE`, la convertir en PNG.**

Convertir vers un fichier temporaire (`/tmp/figcheck_<basename>.png`), ne
jamais ecraser l'original. Essayer les outils dans cet ordre, prendre le
premier disponible :

```bash
# SVG -> PNG (echelle 2 pour que le texte reste lisible a l'inspection)
rsvg-convert -z 2 -o /tmp/figcheck_fig3.png figures/fig3.svg
python3 -c "import cairosvg; cairosvg.svg2png(url='figures/fig3.svg', write_to='/tmp/figcheck_fig3.png', scale=2)"
inkscape figures/fig3.svg --export-type=png --export-dpi=200 --export-filename=/tmp/figcheck_fig3.png

# EPS / PS -> PNG
pdftocairo -png -r 200 -singlefile figures/fig3.eps /tmp/figcheck_fig3
gs -dNOPAUSE -dBATCH -sDEVICE=png16m -r200 -sOutputFile=/tmp/figcheck_fig3.png figures/fig3.eps
convert -density 200 figures/fig3.eps /tmp/figcheck_fig3.png   # ImageMagick

# PDF multipage ou figure PDF que Read rend mal
pdftocairo -png -r 200 -singlefile figures/fig3.pdf /tmp/figcheck_fig3
```

Puis lire le PNG obtenu et poursuivre la Phase 3 normalement, en notant
dans le registre que l'inspection s'est faite sur un rendu converti (la
conversion peut substituer une police manquante, ce qui est une issue en
soi : si le rendu montre une police de remplacement evidente, c'est un
WARN critere H, pas un artefact a ignorer).

`UNREVIEWABLE` ne subsiste que si **aucun** convertisseur n'est installe.
Dans ce cas, noter explicitement lequel manque et la commande
d'installation (`apt install librsvg2-bin poppler-utils`), pour que le
prochain passage puisse inspecter la figure.

---

## Phase 3 -- Inspection visuelle multimodale

**Coeur du skill.** Pour chaque figure localisee, utiliser `Read` sur le
fichier image (PDF, PNG, JPG, l'outil supporte nativement ces formats).

Pour un PDF multi-pages, lire toutes les pages pertinentes (generalement
une seule par figure). Pour des figures tres lourdes, demander
explicitement `pages: "1"` si necessaire.

Une fois l'image affichee dans le contexte multimodal, evaluer
systematiquement les criteres suivants et attribuer a chaque figure un
**statut global** et une **liste d'issues**.

### Grille de criteres (chaque critere : OK | WARN | FAIL | NA)

**A. Lisibilite du texte**
- Taille des labels d'axes, ticks, legendes est-elle suffisante pour etre
  lue sans zoom excessif ? (proportionnee a la taille finale dans le PDF)
- Les polices sont-elles coherentes (pas de mix random de serif/sans-serif)
- Les textes rotatifs (90 deg sur axe Y) sont-ils lisibles

**B. Chevauchements et collisions**
- Les legendes empietent-elles sur les donnees (courbes, points, barres)
- Les labels de points se superposent-ils mutuellement (nuage de points,
  arbres phylogenetiques avec tip labels)
- Les titres d'axes debordent-ils
- Les annotations (fleches, texte libre, `\put`) collisionnent-elles avec
  d'autres elements
- Une barre de couleur (colorbar) masque-t-elle une portion des donnees

**C. Taille et proportions**
- Aspect ratio coherent avec le contenu (arbre phylo vertical, carte
  horizontale...)
- Figure ni trop etiree ni trop ecrasee
- `[width=...]` LaTeX coherent avec les dimensions reelles (une figure
  declaree `width=\textwidth` avec un contenu minuscule en pleine page
  = signal d'alerte)
- Marges blanches excessives autour du contenu (suggere un recadrage)

**D. Fleches et annotations suivables**
- Chaque fleche a une origine et une cible claires
- Les fleches ne se croisent pas inutilement
- La legende explique chaque fleche ou chaque type
- Les annotations textuelles ont un ancrage visible (leader line ou
  proximite non ambigue)

**E. Palette et couleurs**
- Palette coherente entre figures du meme article
- Palette accessible aux daltoniens si possible (eviter pure red vs green)
- Contraste suffisant entre elements
- Pas de jaune clair sur fond blanc (invisible)
- Pas de >8 categories avec des couleurs similaires indistinguables

**F. Correspondance et autosuffisance de la legende**
- Chaque element mentionne dans la caption est-il reellement visible
  (panneaux A/B/C cites et presents, couleurs citees et appliquees,
  gene/souche cite et etiquete) ?
- La caption ne decrit-elle pas un contenu obsolete (figure regeneree
  mais caption pas mise a jour) ?
- Les unites et echelles citees en caption correspondent-elles a ce qui
  est affiche ?
- **Autosuffisance (regle imperative, non negociable)** : la legende
  doit se comprendre **sans lire le corps du texte**. Un lecteur qui
  feuillette directement les figures doit pouvoir l'interpreter seul.
  Concretement, verifier que la caption definit ou rend inutile la
  consultation du texte principal pour : chaque abreviation/acronyme
  utilise dans les elements de la figure (axes, legende interne,
  annotations de panneaux) et non deja standard du domaine ; chaque
  panneau (A/B/C...) ; chaque couleur, symbole ou style de trait utilise
  pour coder une categorie ; l'effectif (N) et le test statistique
  quand un seuil de significativite ou une barre d'erreur est affiche ;
  l'unite de chaque axe ou echelle. Une caption qui renvoie implicitement
  a « voir Methodes » ou « voir section X » pour comprendre ce qui est
  affiche est une issue F-FAIL, pas un simple style a ameliorer.

**F2. Rendu integral dans le PDF compile (critere mecanique, Phase 4)**
- La legende complete (jusqu'a son dernier mot) apparait-elle **sur la
  meme page** que sa figure dans le PDF final -- verifie par comparaison
  automatique texte-source vs `pdftotext`, jamais par la seule lecture
  visuelle (voir Phase 4.2, methode et justification) ?
- Absence de FAIL ici est une condition **necessaire** au statut `OK` de
  la figure, independamment de tous les autres criteres : une figure dont
  le rendu isole est irreprochable mais dont la legende compilee est
  tronquee n'est pas publiable en l'etat.
- Ne s'applique -- et ne peut s'appliquer -- que si un `main.pdf` compile
  et a jour existe (sinon `NA`, jamais `OK` par defaut : voir Phase 4).

**G. Elements scientifiques specifiques (MTBC)**
- Sur un arbre phylogenetique : presence d'une echelle (substitutions
  par site), presence d'un outgroup clair, support de branches (bootstrap)
  lisibles
- Sur une carte geographique : echelle, legende des pays/regions, source
  des donnees
- Sur une heatmap : colorbar avec unites, labels lignes/colonnes visibles
- Sur un reseau / pangenome : legende des noeuds et aretes
- Sur un spoligotype : orientation (spacers de gauche a droite usuelle)

**H. Qualite technique editoriale**
- Rasterisation d'elements qui devraient etre vectoriels (texte pixelise
  dans un PDF)
- Compression artefacts (JPG pour un graphe scientifique = mauvaise idee)
- Bords coupes ou cadre incomplet
- Fond transparent vs fond blanc (attention aux fonds sombres accidentels)

### Attribution du statut global

| Statut | Definition |
|--------|------------|
| `OK` | Aucune issue FAIL, au plus 1-2 WARN mineurs |
| `MINOR` | Plusieurs WARN, rien de bloquant |
| `MAJOR` | Au moins 1 FAIL, figure publiable mais doit etre corrigee |
| `BLOCKING` | Figure illisible, decor manquant, ou fondamentalement erronee |
| `MISSING` | Fichier introuvable |
| `UNREVIEWABLE` | Aucun convertisseur disponible pour rendre le format en PNG (voir Phase 2bis) -- noter l'outil manquant. Ce statut ne doit **pas** etre attribue a un SVG ou un EPS tant que la conversion n'a pas ete tentee. |

### Ce qu'il faut documenter pour chaque issue

Par issue : critere (A-H, ou F2), severite (WARN/FAIL), description concrete
("la legende en haut a droite chevauche la branche L4.9.1"), et action
suggeree ("deplacer la legende hors du panneau principal",
"augmenter `fontsize` de 8 a 11 dans le script source").

### Regles imperatives

- **Ne pas halluciner** : ne decrire que ce qui est reellement visible
  dans l'image. Si un doute subsiste, statut WARN avec mention "a
  confirmer visuellement".
- **Comparer a la caption** : relire la caption a cote de l'image. Un
  ecart caption/image est une issue critere F.
- **Comparer entre figures** : apres avoir inspecte toutes les figures,
  evaluer la coherence inter-figures (palette, police, style).
- **Trois regles absolues, valables pour tout article verifie par ce
  skill, sans exception** :
  1. **Chaque legende doit se suffire a elle-meme** (critere F). Une
     figure comprehensible seulement en repartant lire le texte principal
     est une figure a corriger, meme si le rendu visuel est par ailleurs
     irreprochable.
  2. **Chaque figure incluse dans le manuscrit doit etre appelee au
     moins une fois par un `\ref{}` depuis la prose du corps du texte**
     (hors caption). Une figure presente dans le PDF mais jamais citee
     dans le recit (Results/Discussion) est une issue bloquante : soit
     l'appel manque et doit etre ajoute au bon endroit du texte, soit la
     figure est superflue et doit etre retiree ou deplacee en
     supplementary. Voir Phase 5 pour la detection systematique.
  3. **Chaque legende doit se rendre integralement, sur une seule page,
     dans le PDF compile** (critere F2, Phase 4). Une inspection qui se
     limite au fichier de figure isole ne peut pas voir ce defaut -- la
     legende n'existe que dans le `.tex` -- d'ou le caractere obligatoire
     de la Phase 4 des qu'un PDF compile est disponible, verifiee
     mecaniquement (texte source vs `pdftotext`) et non par la seule
     relecture visuelle, precisement parce qu'une legende tronquee en fin
     de phrase se confond a l'oeil avec une legende simplement courte.

---

## Phase 4 -- Inspection du rendu dans le PDF final (OBLIGATOIRE des qu'un PDF existe)

**Cette phase n'est plus optionnelle.** Un defaut ne vivant que dans la mise
en page du manuscrit compile -- jamais dans le fichier de figure isole --
est invisible a la Phase 3, quelle que soit la rigueur de l'inspection
visuelle : la legende n'existe nulle part dans le fichier `.pdf` de la
figure elle-meme, seulement dans le `.tex` du manuscrit. Verifie sur
`Rv1557` (2026-08-28) : la legende de la Figure 1 (flowchart CONSORT
portrait a `width=\textwidth`, ~200 mots de legende) etait tronquee --
sa derniere phrase disparaissait silencieusement sous le bas de la page,
sans le moindre `Overfull \vbox` dans le log -- et ce defaut a **survecu a
six tours de `/manuscript-review`** avant d'etre repere a l'oeil par
l'auteur. Toute figure signalee a risque en Phase 2 point 8 (portrait +
`width=\textwidth` sans plafond de hauteur), et plus generalement **toute
figure du manuscrit des que `main.pdf`/`main_fr.pdf` existe et est plus
recent que le `.tex`**, doit passer cette phase avant de recevoir un statut
`OK`.

### 4.1 -- Localisation de la page

Pour chaque figure, determiner la page qui la porte dans le PDF compile :

```bash
python3 -c "
import subprocess
out = subprocess.run(['pdftotext','-layout','article/main.pdf','-'],
                      capture_output=True, text=True).stdout
pages = out.split('\x0c')
for i, p in enumerate(pages, start=1):
    if 'fig:consort-flow'[4:] in p:  # remplacer par un fragment distinctif de la legende
        print(i)
"
```

En pratique, chercher un fragment distinctif du **debut** de la legende
(les premiers mots suffisent, ils ne sont jamais tronques) plutot que le
`\label{}`, qui n'apparait pas dans le texte rendu.

### 4.2 -- Verification mecanique de non-troncature (le coeur du controle)

Ne pas se fier a une lecture visuelle seule pour detecter une troncature :
une legende coupee en fin de phrase ressemble, a l'oeil, a une legende
simplement courte -- c'est precisement pourquoi ce defaut a survecu a six
reviews. La detection fiable est **mecanique**, en comparant le texte
source de la legende au texte reellement rendu sur sa page :

```bash
python3 - <<'EOF'
import subprocess, re

TEX = "article/main.tex"          # ou main_fr.tex
PDF = "article/main.pdf"          # ou main_fr.pdf

def normalize(s):
    # commandes LaTeX simples (\textit{...}, \citet{...}, ~, \, ...), accolades,
    # espaces multiples/retours a la ligne du source, et guillemets typographiques
    # que babel/le moteur substitue a la compilation (' source -> ' rendu) : sans
    # ce dernier point, une legende contenant une apostrophe est un faux positif
    # systematique (verifie sur Rv1557 -- 2 des 6 legendes du manuscrit).
    # Meme piege pour les commandes LaTeX qui RENDENT UN CARACTERE au lieu de
    # disparaitre : \S -> §, \P -> ¶, \pounds -> £, \dag -> †, \ddag -> ‡,
    # \copyright -> ©, \textdegree -> °, \% -> %, \& -> &, \# -> #, \_ -> _.
    # Cote source la regex les efface, cote PDF le caractere est bien la, et une
    # legende qui finit par « (\S3.1) » remonte alors comme TRONQUEE alors qu'elle
    # est intacte (verifie sur Rv1125, 2026-09-06 : 1 des 4 legendes, faux positif).
    # On les efface donc AUSSI cote PDF, en normalisant les deux textes pareil.
    # PIEGE DISTINCT (verifie sur Bovis_full, 2026-09-08) : \_, \%, \&, \# sont des
    # commandes LaTeX d'UN SEUL caractere non-alphabetique -- la regex ci-dessous ne
    # matche que \\[a-zA-Z]+, donc un chemin de fichier dans \texttt{...figure\_x.tsv}
    # laisse un '\' residuel cote source, absent cote PDF ('figure_x.tsv' rendu sans
    # backslash), et la legende remonte a tort comme TRONQUEE. On les convertit donc
    # d'abord en leur caractere nu, AVANT la regex generale des commandes lettrees.
    s = re.sub(r'\\([_%&#])', r'\1', s)
    s = re.sub(r'\\[a-zA-Z]+\{?', ' ', s)
    s = s.replace('{', '').replace('}', '')
    s = s.replace('~', ' ').replace('\\', ' ')
    s = s.replace('\u2019', "'").replace('\u2018', "'")
    for ch in '§¶£†‡©°':
        s = s.replace(ch, ' ')
    return re.sub(r'\s+', ' ', s).strip()

src = open(TEX, encoding="utf-8").read()
out = subprocess.run(['pdftotext', '-layout', PDF, '-'],
                      capture_output=True, text=True).stdout
pages = [normalize(p) for p in out.split('\x0c')]

for m in re.finditer(r'\\caption\{', src):
    # extraction naive par comptage d'accolades -- suffisant ici, pas de
    # \caption[...] court ni d'accolades non echappees dans le texte
    depth, i = 1, m.end()
    while depth and i < len(src):
        if src[i] == '{': depth += 1
        elif src[i] == '}': depth -= 1
        i += 1
    caption = src[m.end():i-1]
    tail = normalize(caption)[-50:]
    found_on = [pi+1 for pi, p in enumerate(pages) if tail in p]
    status = "OK" if found_on else "TRONQUEE -- fin de legende absente de tout le PDF"
    print(f"{status:45s} pages={found_on} | fin attendue : ...{tail[-40:]!r}")
EOF
```

Recette validee empiriquement sur `Rv1557` (`main.tex`/`main_fr.tex`, 6 figures
chacun) : 0 faux positif ni faux negatif apres normalisation, y compris sur les
deux legendes qui contenaient une apostrophe (piege le plus frequent, cf.
commentaire dans `normalize`) et sur celle qui s'etale sur plusieurs lignes de
source separees par de vrais retours a la ligne (`\n`, sinon jamais retrouve
dans le texte reflow du PDF).

Interpreter le resultat :
- **`found_on` vide** : la fin de la legende n'apparait sur AUCUNE page --
  c'est exactement le defaut de `Rv1557` (absorbee silencieusement sous le
  bas de page). Statut `FAIL`, critere **F2** (nouveau, voir grille), quel
  que soit par ailleurs le rendu visuel de la figure.
- **`found_on` non vide mais different de la page attendue** (celle du
  debut de legende, Phase 4.1) : la legende s'est coupee entre deux pages
  au milieu d'une phrase -- rare, mais tout aussi genant. Statut `FAIL`
  critere F2.
- **`found_on` egal a la page attendue** : rendu complet, poursuivre en
  4.3.

### 4.3 -- Verification visuelle complementaire

Une fois la non-troncature confirmee mecaniquement, `Read main.pdf pages
"X"` pour la page identifiee et verifier :
- La figure est-elle reellement visible sur la page ?
- Sa taille dans la page est-elle coherente avec son contenu ?
  (eviter une figure 2cm avec 50 branches illisibles)
- Reste-t-il une marge blanche raisonnable sous la legende (une figure qui
  remplit exactement la page au pixel pres, sans aucune marge, est un
  signal WARN meme si le controle 4.2 passe -- c'est `F2` a la limite de
  se reproduire au moindre ajout de texte)
- La figure est-elle pres du texte qui la reference (pas 5 pages plus
  loin) ?

### 4.4 -- Correction quand F2 echoue

**Gating `--fix`, comme pour toute autre correction de ce skill** : sans
`--fix`, se limiter a proposer la modification precise (option
`\includegraphics` cible, ou phrase de la legende a raccourcir avec le
`\ref{}` de remplacement) sans toucher au `.tex`. Avec `--fix`, appliquer
directement -- c'est l'exception etroite documentee dans « Ce que le skill
NE DOIT PAS faire » : seules les options `\includegraphics` et la longueur
de la legende (jamais son contenu factuel) peuvent etre editees.

Deux leviers, a combiner plutot qu'a choisir arbitrairement :
1. **Plafonner la hauteur de l'image** plutot que forcer `width=\textwidth`
   aveuglement : `\includegraphics[height=0.55\textheight,keepaspectratio]{...}`
   (ajuster la fraction pour laisser ~250-350pt a la legende selon sa
   longueur -- estimer avec la Phase 4.2 apres coup, iterer si necessaire).
   Le fichier de figure lui-meme n'est jamais modifie (regle absolue du
   skill), seule l'option `\includegraphics` du `.tex` change.
2. **Raccourcir la legende** quand son contenu duplique deja une section de
   Methods citee ailleurs (`Fig.~\ref{...}` depuis le texte) : renvoyer au
   `\S` correspondant plutot que de repeter le detail methodologique en
   entier dans la legende. Ne jamais retirer une information qui n'existe
   **que** dans la legende (violerait le critere F d'autosuffisance).
3. Recompiler (`make` / `make both`), puis **relancer integralement la
   Phase 4.2** sur la figure corrigee -- ne jamais se contenter d'une
   relecture visuelle apres correction, c'est exactement le pas qui avait
   ete saute jusqu'ici.

---

## Phase 5 -- Correlation inter-figures

Une fois toutes les figures inspectees :

1. **Palette** : lister les couleurs dominantes par figure, signaler les
   incoherences (ex : fig2 utilise rouge pour L4.9, fig5 utilise bleu).
2. **Police** : meme famille de police dans toutes les figures ?
3. **Numerotation des panneaux** : convention coherente ? (A/B/C vs
   a/b/c vs (a)/(b)/(c))
4. **Styles d'arbre** : meme mode de rendu (rectangulaire vs radial vs
   circulaire) ou choix justifie pour chacun ?
5. **Figures orphelines** : un fichier dans `article/figures/` non
   reference dans le `.tex` → signaler (menage a faire).
6. **Refs cassees** : un `\ref{fig:xxx}` sans `\label{fig:xxx}`
   correspondant → signaler.
7. **Figures jamais citees (regle imperative, symetrique du point 6)** :
   pour chaque figure avec un `\label{fig:xxx}`, verifier qu'au moins un
   `\ref{fig:xxx}` existe **dans le corps du texte** (Introduction,
   Results, Discussion...), en excluant l'occurrence dans sa propre
   caption. Une figure sans aucun appel depuis la prose est une issue
   bloquante, listee explicitement dans le rapport (Phase 6) meme si
   toutes ses autres criteres visuels sont OK : le statut global de
   cette figure ne peut pas etre `OK` tant qu'elle n'est pas citee.

---

## Phase 6 -- Rapport et mise a jour du registre

### 1. Ecrire `fig_check.md`

```markdown
# Registre de verification des figures

**Article :** [titre extrait du \title{}]
**Derniere verification :** YYYY-MM-DD
**Figures totales :** N (principales : X, supplementary : Y)

## Figures

| # | Label | Fichier | Format | Taille | Statut | Verifie le | Issues | Script source |
|---|-------|---------|--------|--------|--------|------------|--------|---------------|
| 1 | fig:context | figures/fig1_context.pdf | PDF vect. | 180 Ko | OK | 2026-04-09 | — | analyses/phase3_context.py |
| 2 | fig:ml_tree | figures/fig2_ml_tree.pdf | PDF vect. | 2.1 Mo | MAJOR | 2026-04-09 | B-FAIL, A-WARN | analyses/phase4_tree.py |
| 3 | fig:heatmap | figures/fig3_heatmap.pdf | PDF vect. | 780 Ko | MINOR | 2026-04-09 | E-WARN | résultats/scripts/heatmap.py |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |

## Details des issues

### Figure 2 — fig:ml_tree (MAJOR)
- **B-FAIL** : La legende des lignees (coin sup. droit) chevauche les
  branches terminales du clade F. Action : deplacer la legende hors du
  panneau principal, ou la rendre semi-transparente.
- **A-WARN** : Tip labels des 68 souches en police 6pt, difficilement
  lisibles a la taille de publication. Action : passer a 8pt minimum,
  ou grouper les labels par clade.

### Figure 3 — fig:heatmap (MINOR)
- **E-WARN** : Palette `viridis` utilisee pour une echelle bipolaire ;
  preferer `RdBu_r` ou `coolwarm` pour valeurs centrees sur 0.

...
```

**Regles d'ecriture** :
- Figures ordonnees par numero d'apparition dans l'article.
- Une ligne par figure dans le tableau.
- Une section "Details des issues" sous le tableau pour chaque figure
  non-OK.
- Les figures BLOCKING sont signalees en tete de document avec ⚠.
- En mode `--force`, toutes les dates sont mises a jour.

### 2. Afficher le rapport resume a l'ecran

```
━━━━ Rapport fig-check ━━━━

Article : [titre]
Date    : YYYY-MM-DD
Mode    : [normal / force / stale-days=N / fix]

Resume
  Figures totales     : N
  OK                  : X
  MINOR               : Y
  MAJOR               : Z
  BLOCKING            : W  ⚠
  MISSING             : M
  UNREVIEWABLE        : U

Issues inter-figures
  Palette incoherente : oui/non (detail)
  Figures orphelines  : K (liste)
  Refs cassees        : L (liste)
  Figures jamais citees dans le texte : M (liste)  ⚠ bloquant
  Legendes non autosuffisantes        : N (liste)  ⚠ bloquant
  Legendes tronquees a la compilation : P (liste)  ⚠ bloquant (critere F2)

Figures a corriger en priorite
  1. Figure 2 (fig:ml_tree) — MAJOR
     Issues : B-FAIL (legende chevauche), A-WARN (tip labels trop petits)
     Script source : analyses/phase4_tree.py
  2. Figure 5 (fig:map) — MAJOR
     ...
```

---

## Phase 7 -- Corrections (sugges­tion ou application)

### Sans `--fix` (defaut)

Pour chaque figure non-OK, proposer une correction concrete :

- Si un script source est detecte : citer le chemin et donner
  precisement la modification a apporter (nom de la variable, fonction
  matplotlib a ajuster, parametre a changer).
- Si pas de script source : proposer une action alternative (regenerer
  manuellement, contacter l'auteur de la figure, remplacer).

### Avec `--fix`

Pour chaque figure avec un script source identifie et une correction
applicable automatiquement :

1. **Lire le script source** (`Read`).
2. **Identifier la ligne a modifier** (fontsize, loc de la legende,
   palette, etc.).
3. **Appliquer la modification** via `Edit`.
4. **Relancer le script** via `Bash` depuis le repertoire approprie.
5. **Re-inspecter la figure regeneree** (retour Phase 3 limite a cette
   figure).
6. **Mettre a jour le registre** avec le nouveau statut.

**Regles imperatives en mode `--fix`** :
- Ne JAMAIS modifier le manuscrit `.tex` lui-meme (seulement les scripts
  sources de figures).
- Ne JAMAIS modifier un fichier de figure binaire (PDF/PNG) directement.
- Si plusieurs figures sont regenerees par le meme script, le lancer une
  seule fois.
- En cas d'echec de regeneration : laisser la figure originale, statut
  inchange, et signaler l'echec dans le rapport.
- Si aucun script source n'est detecte pour une figure a probleme : ne
  rien toucher, se contenter de la suggestion.
- Apres toute regeneration, signaler a l'utilisateur qu'une recompilation
  du manuscrit (`make` dans `article/`) est necessaire pour visualiser
  le resultat dans le PDF.

---

## Consignes generales

### Ce que le skill DOIT faire
- Lire visuellement CHAQUE figure via les capacites multimodales
- Appliquer la grille de criteres A-H systematiquement
- Comparer chaque figure a sa caption LaTeX
- **Verifier que chaque legende est autosuffisante** (comprehensible
  sans lire le texte principal, critere F, regle imperative)
- **Verifier mecaniquement, des qu'un PDF compile existe, que chaque
  legende se rend integralement sur sa page** (critere F2, Phase 4,
  obligatoire -- jamais seulement par lecture visuelle)
- **Verifier que chaque figure legendee est appelee par au moins un
  `\ref{}` depuis la prose du corps du texte** (regle imperative,
  Phase 5 point 7), pas seulement l'inverse (refs cassees)
- Maintenir `fig_check.md` a jour, tri par numero d'apparition
- Reperer les figures orphelines et les refs cassees
- Proposer des corrections concretes et actionnables (pas de "ameliorer
  la lisibilite" generique)
- En mode `--fix`, ne toucher que les scripts sources, jamais les
  fichiers binaires ni le manuscrit

### Ce que le skill NE DOIT PAS faire
- Decrire ce qu'il n'a pas reellement vu dans l'image
- Statuer `OK` sans inspection visuelle
- Statuer `OK` sur le critere F2 sans avoir fait tourner la verification
  mecanique de la Phase 4.2 (une lecture visuelle seule ne suffit jamais
  pour ce critere precis)
- Modifier le `.tex` du manuscrit (seul `/manuscript-review` et
  `/deai-latex` peuvent le faire) -- **exception unique et etroite** :
  en mode `--fix`, pour corriger un `FAIL` critere F2 (Phase 4.4), le
  skill peut ajuster les options `\includegraphics` (`width=`/`height=`/
  `keepaspectratio`) d'une figure et raccourcir une legende qui duplique
  du texte deja present ailleurs (avec renvoi `\ref{}` vers cette
  section). Meme dans ce cas : ne jamais alterer un chiffre, un resultat
  ou une affirmation scientifique de la legende -- ce type de correction
  reste du ressort de `/manuscript-review` ou `/claim-check`.
- Modifier une image binaire directement (ni `Edit` ni overwrite)
- Re-verifier une figure recemment validee (sauf `--force` ou
  `--stale-days`)
- Ignorer les figures supplementary (elles sont aussi dans le scope)
- Inventer un script source s'il n'a pas ete trouve

### Integration avec l'ecosysteme

- Complementaire a `/claim-check` (qui verifie les affirmations
  textuelles) et `/bib-check` (qui verifie les references).
- A lancer apres toute regeneration massive de figures, ou avant
  soumission.
- A re-lancer en mode `--force` apres chaque modification substantielle
  de figures.
- Le `fig_check.md` est consomme par `/manuscript-review` pour son
  inventaire qualite global.

---

## Epilogue -- Resume et suggestion de suite

### Resume de session

Afficher en 4-6 lignes :
- Nombre de figures inspectees cette session
- Statut global : toutes OK / N problematiques / K a re-generer
- Actions appliquees en mode `--fix` (scripts modifies, figures
  regenerees)
- Fichiers produits ou modifies (`fig_check.md`, scripts, eventuellement
  figures regenerees)

### Suggestion de prochaine etape

```
━━━━ Prochaine etape suggeree ━━━━

<N> figures necessitent une correction. Je recommande :

  1. /fig-check --fix            ← tenter la regeneration automatique
     (si scripts sources detectes et non encore appliques)
  2. make -C article/            ← recompiler pour verifier le rendu
     final dans le PDF
  3. /fig-check --force          ← re-verifier apres recompilation
```

Si toutes les figures sont OK :

```
━━━━ Etat des figures ━━━━

Toutes les figures sont OK (N inspectees, 0 issue bloquante) :
  ✅ Lisibilite
  ✅ Pas de chevauchements
  ✅ Palette coherente inter-figures
  ✅ Captions correspondent au contenu
  ✅ Aucune figure orpheline ni ref cassee
  ✅ Aucune legende tronquee a la compilation (verifie mecaniquement, Phase 4.2)

Aucune action requise sur les figures.
```
