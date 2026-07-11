---
name: read-scientific-pdf
description: >-
  Extraction rapide du texte d'un PDF scientifique (articles, theses,
  rapports) via pdftotext, markitdown ou pdfminer, puis relecture du
  fichier texte intermediaire avec Read. Pipeline plus efficace que la
  lecture multimodale native pour les documents longs (>10 pages), les
  PDFs a colonnes multiples, les tableaux complexes, et la lecture en
  lot pour revues de litterature.

  Use when: PDF scientifique long AVEC couche texte, article avec
  colonnes ou tableaux complexes, lecture sequentielle d'un corpus pour
  une revue, ou lorsque la lecture native d'un PDF retourne un resultat
  partiel ou inattendu.

  Sur un PDF SCANNE sans couche texte (archives numerisees, manuscrits,
  vieux tirages), pdftotext/markitdown/pdfminer renvoient du VIDE en
  SILENCE : le skill applique alors un garde-fou et bascule sur `Read`
  multimodal, ou sur Mistral OCR 4 (`mistral-ocr-latest`, utilitaire
  `mistral_ocr.py` livre avec le skill) quand il faut une couche texte
  greppable, un traitement en lot, ou dechiffrer une ecriture difficile
  (cursive ancienne, manuscrit). L'OCR est ensuite CORRIGE par le modele
  lui-meme (`--audit`) : triage par score de confiance, puis controle
  semantique sur la logique du texte, puis arbitrage multimodal des seuls
  passages douteux — sans jamais normaliser la langue du scripteur.
argument-hint: "<chemin_pdf> [--mode text|markdown|pages|ocr] [--pages N-M] [--audit]"
allowed-tools: Bash, Read
user-invocable: true
---

# read-scientific-pdf

## Quand utiliser ce skill

**Cas typiques** :
- PDF >10 pages a lire en entier ou par sections
- Article scientifique avec colonnes multiples ou tableaux complexes
- Lecture en lot pour une revue de litterature (`lit-review`,
  `claim-check`, `bib-check`)
- Lecture native d'un PDF qui echoue ou produit un resultat partiel

**Ne pas utiliser si** :
- **Le PDF est un scan sans couche texte** (archives numerisees,
  manuscrits, vieux tirages) : toute la chaine d'extraction renvoie du
  vide en silence. Utiliser `Read` multimodal avec `pages`. Voir
  « Garde-fou couche texte », a executer avant toute extraction.
- Le PDF est court et generique (CV, contrat, slides) : `Read` natif
  fonctionne plus directement
- L'utilisateur veut explicitement voir les figures ou images : `Read`
  natif est necessaire pour le rendu multimodal

## Pourquoi extraire le texte separement

Extraire le texte via `pdftotext` ou `markitdown` puis le relire avec
`Read` presente plusieurs avantages techniques :

- **Vitesse** : l'extraction est locale, instantanee, et le fichier
  texte resultant est plus leger que le PDF original
- **Fiabilite sur documents longs** : la lecture par chunks de pages est
  triviale (`-f N -l M`), idem pour la pagination
- **Tableaux** : `markitdown` convertit en Markdown structure, plus
  lisible que le rendu image natif
- **Reutilisation** : le fichier extrait peut etre conserve dans
  `litterature_review/extracted_pdfs/` pour eviter de retraiter le
  meme PDF dans une session ulterieure

## Comportement par defaut

### 1. Choix du mode d'extraction

| Mode | Outil | Usage |
|------|-------|-------|
| `text` (defaut) | `pdftotext -layout` | Texte brut, conserve mise en page |
| `markdown` | `uvx markitdown` | Tables converties, structure preservee |
| `pages` | `pdftotext` page par page | PDFs longs, lecture incrementale |
| `ocr` | `mistral_ocr.py` (Mistral OCR 4) | **Scans SANS couche texte** : manuscrits, archives, lots |
| `ocr --audit` | idem + confiance par mot | OCR **corrige par le LLM** : triage → sémantique → arbitrage multimodal |

### 2. Sequence

0. **GARDE-FOU OBLIGATOIRE : verifier qu'il existe une couche texte.**
   A faire AVANT de choisir un mode. Voir la section « Garde-fou couche
   texte » ci-dessous. Si le PDF est un scan, ce skill NE S'APPLIQUE PAS :
   sortir immediatement et basculer sur `Read` multimodal.
1. **Verifier que le PDF existe** : `ls -la <chemin_pdf>`
2. **Recuperer metadata** : `pdfinfo <chemin_pdf>` (titre, auteur, nb pages)
3. **Extraire** selon le mode :
   - `text` : `pdftotext -layout <chemin> /tmp/<basename>.txt`
   - `markdown` : `uvx markitdown <chemin> > /tmp/<basename>.md`
   - `pages N-M` : `pdftotext -layout -f N -l M <chemin> /tmp/<basename>_p<N>-<M>.txt`
4. **Lire le fichier** extrait avec `Read`
5. **Synthese** : presenter le contenu pertinent a l'utilisateur

### 3. Fallbacks

Si `pdftotext` produit du texte illisible (ordre des colonnes casse,
caracteres absents) :
- Reessayer avec `pdftotext -raw` (ordre de lecture brut)
- Fallback a `uvx markitdown` (meilleure detection de structure)
- Ultime fallback : `uvx --from pdfminer.six pdf2txt.py <chemin>`

## Garde-fou couche texte (etape 0, obligatoire)

**Le mode d'echec le plus couteux de ce skill : sur un PDF scanne, toute la
chaine (`pdftotext`, `markitdown`, `pdfminer`) renvoie du VIDE en silence,
sans erreur.** L'instance conclut alors a tort que le document est illisible
ou corrompu, alors qu'il est parfaitement lisible en multimodal.

Verifier systematiquement AVANT d'extraire, en caracteres par page :

```bash
p=$(pdfinfo "$f" | awk '/^Pages/{print $2}'); c=$(pdftotext "$f" - 2>/dev/null | tr -d '[:space:]' | wc -c); echo "$c caracteres / $p pages = $((c / (p>0?p:1))) car./page"
```

Seuil : **moins de ~50 caracteres non blancs par page => PDF scanne, aucune
couche texte.** Raisonner par page et non en valeur absolue : un scan d'une
seule page produit 0 caractere, ce qu'un seuil global type « <100 caracteres
pour >5 pages » ne detecte pas.

### Ce qu'il NE faut PAS faire

- **`markitdown` ne fait PAS d'OCR sur les PDF.** Verifie : il renvoie 0
  caractere sur un scan. Ne pas y recourir en esperant un OCR implicite.
- Ne pas enchainer `-raw`, puis `markitdown`, puis `pdfminer` : les trois
  s'appuient sur la meme couche texte absente et renverront tous du vide.

### Ce qu'il faut faire

1. **Voie normale : `Read` multimodal avec le parametre `pages`** (20 pages
   max par appel). C'est la bonne reponse dans l'immense majorite des cas :
   aucun pretraitement, et le modele lit le scan directement, y compris de
   l'ecriture manuscrite. Annoncer a l'utilisateur que le PDF est un scan et
   qu'on bascule en lecture multimodale.
2. **Mistral OCR 4, pour les cas recalcitrants et le traitement en lot.**
   C'est le bon outil des qu'il faut une COUCHE TEXTE reelle (grep,
   indexation, corpus de centaines de pages) ou quand la lecture multimodale
   peine. Voir la section dediee ci-dessous.
3. **`tesseract` en depannage hors ligne** (pas de reseau, pas de cle) :
   ```bash
   pdftoppm -r 300 -png "$f" /tmp/pg && for i in /tmp/pg-*.png; do tesseract "$i" "${i%.png}" -l fra 2>/dev/null; done && cat /tmp/pg-*.txt > /tmp/ocr.txt
   ```
   (`ocrmypdf` serait plus direct mais n'est pas installe.) Tres mediocre sur
   manuscrit : n'y recourir que faute de mieux.

## Mistral OCR 4 (documents recalcitrants, manuscrits, lots)

Modele `mistral-ocr-latest`. Cle deja presente dans `~/.bashrc`
(`$MISTRAL_API_KEY`). Un utilitaire autonome est livre avec ce skill, en
stdlib pure (pas de SDK `mistralai` a installer) :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/read-scientific-pdf/mistral_ocr.py <fichier.pdf>            # -> markdown sur stdout
python3 .../mistral_ocr.py dossier.pdf -o /tmp/dossier.md --pages 1-10                          # plage de pages
python3 .../mistral_ocr.py 'corpus/*.pdf' --batch -o /tmp/ocr_out/                              # Batch API, 50% moins cher
```

**Quand y aller plutot qu'en multimodal** :
- il faut une couche texte **greppable** (indexer, chercher un motif dans tout
  un corpus, construire un TSV) ;
- le volume depasse ce qu'on veut lire page a page (au-dela de ~50 pages,
  passer en `--batch`) ;
- l'ecriture est difficile et la lecture multimodale hesite.

**Performance reelle constatee** (archives de naturalisation, 2026-07) :
- Manuscrit de 1999 : restitution quasi parfaite, **y compris le francais
  fautif du redacteur**, ce qui compte quand la langue du demandeur est
  elle-meme l'objet d'etude.
- **Cursive de chancellerie de 1790 : dechiffree**, supplique restituee en
  entier. C'est la ou `tesseract` s'effondre.

**Piege de fiabilite, a ne jamais oublier** : l'OCR produit des erreurs
**semantiquement plausibles**, pas du charabia. Sur le manuscrit de 1999, il a
lu « il y a de **genre** » la ou le document dit « il y a de **guerre** ». Un
mot faux mais bien forme ne se detecte par aucun controle automatique, et peut
polluer une analyse en aval (ici, « genre » est justement un axe du corpus : un
`grep` naif y aurait cree un faux positif). **Ne jamais citer un passage
verbatim sur la seule foi de l'OCR** : le verifier a l'oeil avec `Read`
multimodal sur la page concernee. L'OCR sert a INDEXER et a ORIENTER ; la
lecture multimodale sert a CITER.

Tarif (juillet 2026) : 4 $ / 1000 pages en synchrone, 2 $ / 1000 pages en
`--batch`. Un corpus de 1700 pages coute donc de l'ordre de 3 a 7 $ : le cout
n'est pas un obstacle, la fiabilite si.

## Corriger l'OCR par le LLM : triage, raisonnement, arbitrage

L'OCR seul n'est pas fiable, la lecture multimodale seule ne passe pas a
l'echelle. **La bonne architecture les compose** : l'OCR degrossit, le
raisonnement du modele localise le doute, la multimodalite tranche. Trois
signaux, dont deux seulement sont des SIGNAUX et un seul est un JUGE.

### Etape 1 — Triage statistique (`--audit`)

Mistral OCR renvoie une confiance par mot. `mistral_ocr.py <pdf> --audit`
marque les mots douteux `⟦mot|0.20⟧` et liste les pages a arbitrer :

```bash
python3 .../mistral_ocr.py archive.pdf --audit
```

Seuils empiriques (archives manuscrites) : **< 0.50 = suspicion FORTE**,
**0.50-0.80 = suspicion faible**, > 0.80 = fiable. Sur un manuscrit reel, cela
concentre l'attention sur ~3 % du texte (suspicion forte) au lieu de tout
relire.

### Etape 2 — Controle semantique (raisonnement sur la logique du texte)

Lire la transcription **sans l'image** et reperer ce qui ne tient pas : mot
incoherent avec le contexte, rupture de sens, terme hors du champ lexical du
document, date ou nom impossible, formule administrative deformee. Un mot faux
est souvent bien forme mais **contextuellement absurde** : « mon pays il y a de
*genre* », dans une lettre ou il est ensuite question de fuir la campagne et
l'« Armee Rouge », ne peut pas etre autre chose que « guerre ».

Ce signal est INDEPENDANT du precedent, ce qui fait sa valeur : quand la
confiance basse et l'incoherence semantique designent le meme mot, l'erreur est
quasi certaine. Exploiter aussi les **verites terrain externes** : un inventaire,
des metadonnees, une fiche d'etat civil donnent gratuitement le nom, l'annee, la
nationalite du sujet — si l'OCR les contredit, c'est l'OCR qui a tort.

### Etape 3 — Arbitrage multimodal (le seul juge)

`Read` avec `pages` sur **les seules pages signalees**. C'est la seule instance
qui voit l'encre, donc la seule qui tranche. Ni la confiance ni le raisonnement
ne decident : ils designent ou regarder.

### LE PIEGE A NE JAMAIS FRANCHIR : ne pas normaliser la langue du scripteur

**Un mot peu sur peut etre une erreur de l'OCR, ou une faute de l'AUTEUR
fidelement transcrite. Les deux sont indiscernables par le score.** Cas mesure
sur un manuscrit de 1999 :

| mot OCR | confiance | verdict apres arbitrage |
|---|---|---|
| `genre` | 0.20 | **erreur d'OCR** — l'encre dit « guerre ». A corriger. |
| `socher` | 0.18 | **fidele** — le demandeur a bien ecrit ce mot informe. A PRESERVER. |
| `monger` | 0.78 | **fidele** — le demandeur ecrit « monger » pour « manger ». A PRESERVER. |

Deux mots de confiance jumelle (0.18 et 0.20) appellent des verdicts opposes.
Le score hierarchise le soupcon ; il est **aveugle a la nature du defaut**.

**Corollaire sur les documents anciens : l'ORTHOGRAPHE D'EPOQUE fait chuter la
confiance et sera « corrigee » a tort.** Sur une supplique de 1790, l'audit
signale `enfans` (0.75) et `impatiant` (0.80) : ce ne sont pas des erreurs, c'est
la graphie correcte du XVIIIe siecle. Les normaliser en « enfants » et
« impatient » detruirait la valeur diplomatique de la transcription. Meme
consigne : la graphie ancienne se preserve et se signale, elle ne se corrige pas.

### DANGER : le signal semantique est le plus TRAITRE des trois

Contre-intuitif, et verifie sur pieces. Le controle semantique **corrige vers la
forme historiquement juste**, et c'est precisement ce qui le rend dangereux : il
est confiant, erudit, et il efface l'erreur de l'auteur.

Cas mesure. Lettre d'un refugie armenien (1940), OCR : « j'ai toujours travaille
sous le couvert d'un passeport **Hansen** » (confiance 0.55, suspicion seulement
*faible*). Le raisonnement semantique est ecrasant : il ne peut s'agir que du
**passeport Nansen**, le titre de voyage delivre aux apatrides — tout historien
« corrigerait ». Mais l'encre porte, selon toute apparence, un H. Deux lectures
restent ouvertes : confusion N/H de l'OCR en cursive, **ou faute du requerant
lui-meme, ecrivant de travers le nom du document qui definit son apatridie**.
Cette seconde hypothese est une donnee de premier ordre — et la « correction »
semantique l'aurait detruite sans laisser de trace.

Regle : **quand le signal semantique et l'arbitrage multimodal ne concordent pas,
c'est l'encre qui gagne ; et quand l'encre est ambigue, on marque `[?]`, on ne
tranche pas.** Ne jamais laisser l'erudition reecrire la source. Le score de
confiance, lui, est seulement bruyant (il signale `Aux Armees` a 0.27 alors que
la lecture est juste) : il fait perdre du temps, il ne fait pas perdre la donnee.

Le reflexe naturel d'un LLM est de reecrire en francais correct. Sur un corpus
ou la langue du redacteur est elle-meme l'objet d'etude (demandes de
naturalisation, lettres de migrants, ecrits populaires, copies d'eleves), cette
normalisation **detruit la donnee**. Regle : on corrige ce que la MACHINE a mal
lu, jamais ce que l'AUTEUR a mal ecrit. En cas de doute, conserver la graphie et
la signaler, plutot que de lisser.

## Formulaires a deux colonnes : `pair_form.py`

Sur un formulaire administratif (questions imprimees a gauche, reponses manuscrites
a droite), **l'OCR decolonne** : toutes les questions en un bloc, toutes les
reponses en un autre, **sans appariement**, et avec un decalage **non constant**
(une question sans reponse ne produit aucune ligne). **Aucun ancrage textuel ne
rattrape cela** — ce n'est pas un probleme de segmentation mais d'ALIGNEMENT.

**La solution est GEOMETRIQUE** : `include_blocks=True` renvoie les boites
englobantes, et la reponse est tracee **a la meme hauteur** que sa question. On
apparie par recouvrement vertical.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/read-scientific-pdf/pair_form.py dossier.pdf --pages 9
python3 .../pair_form.py dossier.pdf --pages 6-10 --json
```

Deux pieges, tous deux constates : les questions se terminent par des **points de
conduite** (« Quelle est leur residence ? . . . ») — un `endswith("?")` naif les
rejette et casse tout ; et **ne pas se fier a `x`** pour separer les colonnes,
selon le scan elles peuvent se retrouver du meme cote.

### Sortie recommandee

Une transcription diplomatique (graphie d'origine preservee), avec les
corrections d'OCR appliquees et tracees, et les incertitudes restantes marquees
`[?]`. Ne jamais livrer une transcription « propre » qui masque ce qui a ete
devine.

## Usage avec arguments

### Sans argument (mode interactif)
```
/read-scientific-pdf
```
Lister les PDFs du repertoire courant et demander lequel lire.

### Avec chemin
```
/read-scientific-pdf docs/Holdaway_2016.pdf
```
Mode `text` par defaut, lecture complete.

### Avec mode explicite
```
/read-scientific-pdf article.pdf --mode markdown
/read-scientific-pdf these.pdf --mode pages --pages 12-25
/read-scientific-pdf archive_scannee.pdf --mode ocr        # scan/manuscrit -> Mistral OCR 4
```

## Exemple d'execution complete

Utilisateur : `/read-scientific-pdf docs/ARCHEO_Holdaway_2016.pdf`

```bash
# 1. Verification
ls -la docs/ARCHEO_Holdaway_2016.pdf
# -rw-rw-r-- 1 user user 1006846 Apr 26 09:17 ...

# 2. Metadata
pdfinfo docs/ARCHEO_Holdaway_2016.pdf | grep -E "Title|Author|Pages"
# Title: The Fayum revisited...
# Pages: 8

# 3. Extraction texte
pdftotext -layout docs/ARCHEO_Holdaway_2016.pdf /tmp/holdaway_2016.txt
wc -l /tmp/holdaway_2016.txt
# 542 /tmp/holdaway_2016.txt

# 4. Lecture
Read(/tmp/holdaway_2016.txt)

# 5. Synthese a l'utilisateur
```

## Cas particuliers

### PDF avec colonnes
`pdftotext -layout` preserve les colonnes mais melange parfois l'ordre de
lecture. Si le texte semble incoherent :
```bash
pdftotext -raw <chemin> -    # ordre de lecture continu
```

### PDF avec equations
Les equations LaTeX sont generalement perdues par pdftotext. Pour articles
mathematiques, utiliser `markitdown` (preserve mieux) ou conseiller a
l'utilisateur de regarder les pages specifiques avec un viewer.

### Tableaux complexes
`pdftotext` produit des tableaux mal alignes. Utiliser `markitdown` qui
convertit en Markdown table avec separateurs `|`.

### PDFs proteges/cryptes
```bash
pdftotext -upw "<password>" <chemin>
# ou si pas de password
qpdf --decrypt <input> <output_decrypted>
```

### PDFs >50 Mo
Decouper en chunks de pages :
```bash
for i in 1 11 21 31; do
  end=$((i+9))
  pdftotext -layout -f $i -l $end <chemin> /tmp/chunk_${i}.txt
done
```

## Persistance dans litterature_review/

Si le projet possede `litterature_review/`, sauvegarder l'extraction
au lieu de `/tmp/` :
```bash
mkdir -p litterature_review/extracted_pdfs
pdftotext -layout docs/<pdf> litterature_review/extracted_pdfs/<basename>.txt
```

Cela evite de retraiter le meme PDF a chaque session.

## Integration avec autres skills

- **`lit-review`** : pour chaque PDF candidat, utiliser ce skill au lieu de
  Read direct sur les documents longs ou denses.
- **`bib-check`** : meme principe lors de la verification des references
  citees a partir des PDFs source.
- **`claim-check`** : pour verifier une affirmation contre une source PDF
  longue.
- **`fetch-tbannotator`** / `pubmed-database` : telecharger puis extraire
  via ce skill.
