---
name: read-scientific-pdf
description: >-
  Extraction rapide du texte d'un PDF scientifique (articles, theses,
  rapports) via pdftotext, markitdown ou pdfminer, puis relecture du
  fichier texte intermediaire avec Read. Pipeline plus efficace que la
  lecture multimodale native pour les documents longs (>10 pages), les
  PDFs a colonnes multiples, les tableaux complexes, et la lecture en
  lot pour revues de litterature.

  Use when: PDF scientifique long, article avec colonnes ou tableaux
  complexes, lecture sequentielle d'un corpus pour une revue, PDF
  scanne necessitant OCR, ou lorsque la lecture native d'un PDF
  retourne un resultat partiel ou inattendu.
argument-hint: "<chemin_pdf> [--mode text|markdown|pages] [--pages N-M]"
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
- PDF scanne necessitant OCR
- Lecture native d'un PDF qui echoue ou produit un resultat partiel

**Ne pas utiliser si** :
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

### 2. Sequence

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

Si le PDF est scanne (pas de couche texte) :
- Detecter via `pdftotext` produisant <100 caracteres pour >5 pages
- Utiliser `uvx markitdown` qui fait OCR via tesseract si dispo
- Sinon avertir l'utilisateur que le PDF necessite OCR manuel

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
