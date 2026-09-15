---
name: pdf-to-latex
description: >-
  Reconstruct compilable LaTeX source code from a PDF document. Analyzes
  structure, layout, fonts, tables, equations, and figures to produce a
  visually faithful .tex file. Uses markitdown for text extraction then
  rebuilds document class, packages, geometry, and content.

  Use when: reverse-engineering a PDF to LaTeX, reproducing a paper template,
  editing an article without source files, or reconstructing institutional documents.
disable-model-invocation: true
allowed-tools: [Bash(uvx markitdown*), Bash(pdflatex*), Bash(pdffonts*), Bash(pdfimages*), Bash(pdfinfo*)]
---

# PDF to LaTeX Reverse Engineering

Reconstruct LaTeX source code from a PDF document by analyzing its structure, layout, fonts, and content. The goal is to produce a compilable `.tex` file that generates a visually faithful reproduction of the original PDF.

## Process

### Step 1: Extract content from the PDF

Use the `read-scientific-pdf` skill first to get a text extraction (it handles scanned PDFs via OCR):

```bash
uvx --with 'markitdown[pdf]' markitdown input.pdf -o input_raw.md
```

Then open the original PDF to visually analyze elements markitdown can't capture:

- Page layout (margins, columns, header/footer)
- Font families and sizes
- Tables, figures, equations
- Colors, boxes, decorative elements
- Page numbering style
- Section hierarchy

### Step 2: Identify the document class and packages

Analyze the PDF to determine:

| Visual Clue | Likely LaTeX Setup |
|---|---|
| Two-column academic paper | `\documentclass[twocolumn]{article}` or `IEEEtran`, `revtex` |
| Book with chapters | `\documentclass{book}` or `memoir` |
| Slides/presentation | `\documentclass{beamer}` |
| Letter format | `\documentclass{letter}` |
| French document | Add `\usepackage[french]{babel}` |
| ANR/institutional template | Check for custom class, often provided as `.cls` file |
| Wide margins | `\usepackage[margin=2.5cm]{geometry}` |
| Narrow margins | `\usepackage[margin=1cm]{geometry}` |

Common package detection:

| Feature in PDF | Package |
|---|---|
| Colored text or boxes | `xcolor`, `tcolorbox` |
| Fancy headers/footers | `fancyhdr` |
| Hyperlinks (colored or boxed refs) | `hyperref` |
| Code listings | `listings` or `minted` |
| Complex tables | `booktabs`, `tabularx`, `longtable` |
| Mathematical equations | `amsmath`, `amssymb`, `mathtools` |
| Subfigures | `subcaption` or `subfig` |
| Bibliography | `biblatex` or `natbib` |
| Algorithms | `algorithm2e` or `algorithmicx` |
| SI units | `siunitx` |
| Chemical formulas | `mhchem` |
| Tikz diagrams | `tikz`, `pgfplots` |

### Step 3: Detect fonts

| Visual Appearance | Likely Font Setup |
|---|---|
| Computer Modern (default LaTeX) | No font package needed |
| Times-like serif | `\usepackage{mathptmx}` or `\usepackage{newtxtext,newtxmath}` |
| Palatino-like | `\usepackage{mathpazo}` or `\usepackage{newpxtext,newpxmath}` |
| Helvetica/Arial-like sans | `\usepackage{helvet}` |
| Modern sans-serif | Consider `fontspec` with XeLaTeX/LuaLaTeX |
| Monospace code font | `\usepackage{inconsolata}` or `\usepackage{FiraMono}` |

### Step 4: Reconstruct page geometry

Measure approximate margins and layout from the PDF:

```latex
\usepackage[
  a4paper,          % or letterpaper
  top=2.5cm,
  bottom=2.5cm,
  left=2.5cm,
  right=2.5cm,
  headheight=14pt
]{geometry}
```

For multi-column layouts:

```latex
\usepackage{multicol}
\begin{multicols}{2}
...
\end{multicols}
```

### Step 5: Reconstruct headers and footers

```latex
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{Left header text}
\fancyhead[R]{Right header text}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}
```

### Step 6: Reconstruct content

Work through the document page by page:

**Section hierarchy:**

```latex
\section{...}      % Large bold, numbered
\subsection{...}   % Medium bold, numbered
\subsubsection{...}
\paragraph{...}    % Inline bold heading
```

**Lists:** Identify bullet style (`\textbullet`, `--`, numbered) and nesting.

**Tables:** Reconstruct using `booktabs` for clean horizontal rules:

```latex
\begin{table}[htbp]
\centering
\caption{...}
\begin{tabular}{lcc}
\toprule
Header 1 & Header 2 & Header 3 \\
\midrule
Data & Data & Data \\
\bottomrule
\end{tabular}
\end{table}
```

**Figures:** Use placeholder with approximate dimensions:

```latex
\begin{figure}[htbp]
\centering
% \includegraphics[width=0.8\textwidth]{figure_name.pdf}
\rule{0.8\textwidth}{5cm}  % Placeholder
\caption{Caption text from PDF}
\label{fig:label}
\end{figure}
```

**Equations:** Reconstruct mathematical content:

```latex
\begin{equation}
  f(x) = \sum_{i=1}^{n} \alpha_i \cdot x_i + \beta
  \label{eq:example}
\end{equation}
```

**Colored boxes / callouts:**

```latex
\usepackage{tcolorbox}
\begin{tcolorbox}[colback=blue!5, colframe=blue!50, title=Note]
Content of the box
\end{tcolorbox}
```

**Footnotes:** Look for superscript numbers and corresponding text at page bottom.

### Step 7: Handle special elements

**Bibliography:**

```latex
% If references are visible, reconstruct as:
\usepackage[backend=biber, style=numeric]{biblatex}
\addbibresource{references.bib}
% ... at end:
\printbibliography
```

Create a `references.bib` file with entries extracted from the reference list.

**Cross-references:** Identify patterns like "see Section 3" or "Figure 2" and add `\ref{}` / `\autoref{}`.

**Table of contents:** If present, add `\tableofcontents` and verify section numbering matches.

### Step 8: Compile and iterate

```bash
# Compile with pdflatex (or xelatex/lualatex if using fontspec)
pdflatex -interaction=nonstopmode output.tex
biber output  # if using biblatex
pdflatex -interaction=nonstopmode output.tex
pdflatex -interaction=nonstopmode output.tex
```

Compare output PDF with original visually. Iterate on:

- Spacing and margins
- Font sizes
- Table column widths
- Float placement
- Page breaks

## Output structure

Produce these files:

```
output/
├── main.tex          # Main LaTeX source
├── references.bib    # Bibliography (if applicable)
├── figures/          # Extracted or placeholder figures
└── README.md         # Notes on reconstruction choices
```

## Known limitations

- **Images**: Cannot extract embedded images as vector graphics. Use placeholders or extract raster images with `pdfimages`.
- **Custom fonts**: If the PDF uses proprietary fonts, substitute with closest open alternatives.
- **Complex layouts**: Multi-column with spanning elements may require manual adjustment.
- **Mathematical OCR**: Complex equations need careful manual verification.
- **Exact spacing**: Micro-typography (kerning, tracking) won't match exactly.

## Tips

- Run `pdffonts input.pdf` (from poppler-utils) to identify fonts used
- Run `pdfimages -list input.pdf` to inventory embedded images
- Use `pdfinfo input.pdf` for metadata (page size, creator application)
- If the PDF was created by Word, the layout may not map cleanly to LaTeX idioms, focus on semantic reconstruction rather than pixel-perfect replication
- If an institutional template exists (e.g., ANR, IEEE, Springer), find and use it rather than reconstructing from scratch
