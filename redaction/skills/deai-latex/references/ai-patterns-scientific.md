# Patterns IA dans les articles scientifiques

Reference detaillee pour le skill deai-latex. Consulter ce fichier pour les
cas ambigus et les exemples avant/apres.

## Structures revelant une generation IA

### 1. Le "bullet-point paper"

Un article ou chaque section contient une ou plusieurs listes a puces.
Les humains ecrivent en prose ; les IA structurent en listes.

**Signal** : > 1 liste par page en moyenne, ou > 3 listes dans une section.

**Avant (IA)** :
```latex
The main contributions of this work are:
\begin{itemize}
  \item We propose a novel method for...
  \item We demonstrate that...
  \item We provide a comprehensive evaluation...
\end{itemize}
```

**Apres (humain)** :
```latex
This work proposes a method for X and demonstrates its effectiveness
on Y. The evaluation covers Z datasets across N experimental conditions.
```

Ou, si la liste est vraiment justifiee (ex: contributions en fin d'introduction),
utiliser `enumerate` et la garder concise.

### 2. Les micro-sections en cascade

L'IA cree une sous-section pour chaque concept, meme mineur.

**Signal** : 3+ sous-sections consecutives de < 5 lignes chacune.

**Avant (IA)** :
```latex
\subsection{Data Collection}
We collected 500 samples from three hospitals.

\subsection{Data Preprocessing}
Raw sequences were filtered using Trimmomatic v0.39.

\subsection{Quality Control}
FastQC was used to assess read quality.
```

**Apres (humain)** :
```latex
\subsection{Data collection and preprocessing}
We collected 500 samples from three hospitals. Raw sequences were filtered
using Trimmomatic v0.39 with default parameters, and read quality was
assessed using FastQC v0.11.9. Samples with fewer than 100,000 reads
after filtering were excluded (n=12).
```

### 3. Le paragraphe-formule

Chaque paragraphe suit exactement : phrase introductive → 3 arguments →
phrase conclusive. Cette structure identique repetee est un signal fort.

**Signal** : 3+ paragraphes consecutifs de meme structure.

**Avant (IA)** :
```latex
Drug resistance is a major public health concern. First, it increases
treatment duration. Second, it raises healthcare costs. Third, it
limits available therapeutic options. Therefore, understanding resistance
mechanisms is crucial.

Genomic approaches offer powerful tools for surveillance. First, WGS
provides comprehensive genetic information. Second, it enables rapid
genotyping. Third, it facilitates outbreak detection. Therefore, WGS
is increasingly adopted by public health laboratories.
```

**Apres (humain)** :
```latex
Drug resistance complicates treatment by extending its duration and
narrowing the range of effective antibiotics, with direct consequences
on healthcare costs and patient outcomes.

Whole-genome sequencing addresses several of these challenges at once:
a single assay provides genotyping, resistance prediction, and
transmission cluster identification. Public health laboratories in
over 30 countries now use WGS routinely for surveillance.
```

### 4. Le "furthermore cascade"

Enchainement de connecteurs logiques au debut de chaque phrase.

**Signal** : 3+ phrases consecutives commencant par un connecteur
(Moreover, Furthermore, Additionally, In addition, Notably).

**Correction** : supprimer le connecteur et restructurer. La logique doit
etre portee par le contenu, pas par les connecteurs.

## Gras : les cas limites

### Acceptable
```latex
\item[\textbf{Definition}]          % label de description
\textbf{Table 1.} Caption...        % si le style l'exige
\section{Results}                    % titres (gras automatique)
```

### Inacceptable
```latex
We found that \textbf{drug resistance} is increasing.
The \textbf{key finding} of this study is that...
\textbf{Importantly}, we observed that...
```

### Cas particulier : definition d'un terme
```latex
% Acceptable (premiere occurrence, definition)
We define \emph{core genome} as the set of genes present in all strains.

% Inacceptable (gras pour definir)
We define \textbf{core genome} as the set of genes present in all strains.
```

## Acronymes : decision tree

```
L'acronyme est-il universel dans le domaine ? (DNA, RNA, PCR, WHO...)
  → OUI : ne pas definir (sauf article grand public)
  → NON :
    Est-ce la premiere occurrence dans le corps du texte ?
      → OUI : definir → "whole-genome sequencing (WGS)"
      → NON :
        Est-ce dans l'abstract ?
          → OUI : definir separement (l'abstract est autonome)
          → NON : utiliser l'acronyme seul
    L'acronyme est-il utilise < 3 fois au total ?
      → OUI : ne pas creer d'acronyme, utiliser la forme longue partout
      → NON : definir et utiliser l'acronyme
```

## Noms d'especes : exemples courants

| Forme correcte | Formes incorrectes |
|----------------|-------------------|
| `\textit{Mycobacterium tuberculosis}` | Mycobacterium tuberculosis, *M. Tuberculosis* |
| `\textit{M. tuberculosis}` (apres 1ere occurrence) | M. tuberculosis (sans italique) |
| `\textit{Escherichia coli}` | E. Coli, *E. COLI* |
| `\textit{Staphylococcus aureus}` | S. Aureus |
| `\textit{Mycobacterium}` spp. | *Mycobacterium spp.* (spp. pas en italique) |
| `\textit{M. bovis}` BCG | *M. bovis BCG* (BCG pas en italique) |

**Attention** : le nom de l'espece ne prend jamais de majuscule
(*M. tuberculosis*, pas *M. Tuberculosis*).

## Temps verbaux : guide par section

| Section | Temps principal | Exemple |
|---------|----------------|---------|
| Introduction (contexte) | Present | "TB remains a leading cause of death" |
| Introduction (gap) | Present perfect | "Few studies have addressed..." |
| Introduction (objectifs) | Present/passe | "This study aims to..." ou "We analyzed..." |
| Methods | Passe | "Sequences were aligned using..." |
| Results | Passe | "Analysis revealed 42 SNPs..." |
| Discussion (resultats) | Passe | "Our analysis showed..." |
| Discussion (interpretation) | Present | "This suggests that resistance..." |
| Discussion (litterature) | Present | "Smith et al. report similar findings" |
| Conclusion | Present + futur | "WGS provides... Future work will..." |

## Checklist rapide

Avant de valider une section, verifier :

- [ ] Aucun `\textbf` dans le corps du texte (hors labels, titres, tableaux)
- [ ] Maximum 1-2 listes par section, et justifiees
- [ ] Toutes les sous-sections font > 5 lignes
- [ ] Pas de 3+ connecteurs consecutifs (Moreover/Furthermore/Additionally)
- [ ] Tous les acronymes definis exactement une fois
- [ ] Tous les noms d'especes en italique, genre abrege apres 1ere occurrence
- [ ] Pas de phrase orpheline (paragraphe d'une seule phrase)
- [ ] Figures et tables referencees par `\cref`
- [ ] Temps verbaux coherents dans la section
- [ ] Pas de guillemets manuels (utiliser `\enquote{}`)
