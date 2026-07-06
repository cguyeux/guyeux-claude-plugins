---
name: beamer-slides
description: Generate professional Beamer/LaTeX presentation slides from research work. Analyzes main.tex, data, and figures to build a self-contained, narrative-driven, pedagogical scientific presentation.
user_invocable: true
invocation: /slides
---

# Beamer Slides Generator

Generate professional LaTeX/Beamer presentation slides from research work. The skill analyzes the project context (article, data, figures), identifies key findings, builds a narrative arc, and produces a self-contained, scientifically rigorous yet pedagogical presentation.

## When to Use

- The user asks to create slides, a presentation, or a talk from their research
- The user asks to update existing slides after article modifications
- The user wants a conference talk, lab meeting presentation, or thesis defense slides
- The user says `/slides`

## Philosophy

A good scientific presentation is **not a compressed paper**. It is a guided tour through your scientific reasoning. The audience should:
1. Understand the problem before seeing any data
2. Follow the logic of each result as it builds on the previous one
3. Leave with 3-5 key takeaways they can explain to someone else

**Every slide must earn its place.** If a slide doesn't advance the narrative or provide essential context, cut it.

## Process

### Phase 1: Understand the Research

Before writing a single slide, thoroughly analyze the project:

1. **Read the article** (`main.tex` or equivalent):
   - Abstract: extract the 3-5 core claims
   - Introduction: identify the gap/question
   - Methods: note anything the audience needs to understand results
   - Results: rank by importance and narrative weight
   - Discussion: extract the interpretive insights (not data repetition)
   - Conclusion: identify the take-home messages

2. **Inventory available figures** (`figures/` directory):
   - Which figures are publication-quality and self-explanatory?
   - Which need simplification for a talk?
   - Are there figures not in the article that could help (pipeline diagrams, etc.)?

3. **Identify the audience level**:
   - Ask the user if not obvious: conference (specialists), lab meeting (mixed), thesis defense (committee), general seminar (broad)
   - Default: conference talk for specialists with clear context for non-experts

4. **Determine duration**:
   - Ask if not specified. Default: 20 minutes (~18-22 content slides + title + thanks)
   - Rule of thumb: 1-1.5 minutes per content slide

### Phase 2: Build the Narrative Arc

Structure the presentation as a **story**, not a table of contents:

```
ACT 1: SETUP (3-4 slides)
  - Why should the audience care? (the problem)
  - What was missing? (the gap)
  - What did you do? (1-slide overview, not detailed methods)

ACT 2: THE JOURNEY (10-14 slides)
  - Present results in logical order (not necessarily paper order)
  - Each slide = one idea, one figure, one take-away
  - Build complexity progressively
  - Include "bridge slides" between sections (1-sentence transition)

ACT 3: RESOLUTION (3-4 slides)
  - Synthesis: what does it all mean together?
  - Limitations (brief, honest)
  - Perspectives (concrete next steps)
  - Final take-home message
```

**Key narrative principles:**
- **Start with the question, not the methods.** Nobody cares about your pipeline until they understand why it matters.
- **One message per slide.** If you need two ideas, make two slides.
- **Show data, then interpret.** Let the figure speak first, then add your conclusion.
- **Every dataset must be introduced.** Never show data without explaining what it is, where it comes from, how many samples, and what the axes mean.
- **Transitions matter.** End each section with a bridge sentence to the next.
- **The synthesis slide is the most important slide.** Spend time making it excellent.

### Phase 3: Write the Slides

#### Beamer Template

Use the Metropolis theme by default (clean, modern, professional). Adapt if the user has a preferred theme.

```latex
\documentclass[10pt, aspectratio=169]{beamer}

\usetheme[progressbar=frametitle, block=fill,
          sectionpage=progressbar, numbering=fraction]{metropolis}

\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[french]{babel}    % or [english]{babel}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{amsmath}
\usepackage{xcolor}
\usepackage{tcolorbox}
\usepackage{tikz}
\usetikzlibrary{arrows.meta, positioning}
\usepackage{fontawesome5}

% Compact spacing
\setlength{\parskip}{2pt}
\setbeamersize{text margin left=6mm, text margin right=6mm}
\setbeamerfont{itemize/enumerate body}{size=\small}
\setbeamerfont{itemize/enumerate subbody}{size=\footnotesize}
```

#### Slide Design Rules

**Text:**
- Maximum 6 bullet points per slide (fewer is better)
- Maximum 8-10 words per bullet
- No full sentences in bullets — use keywords and fragments
- Body text: `\small` or `\footnotesize` to fit more if needed
- **Never** put a wall of text on a slide

**Figures:**
- One figure per slide (two max if direct comparison)
- Figures should occupy 50-70% of the slide area
- Always caption or annotate: what are the axes? what are the colors?
- Use `\includegraphics[width=\linewidth,height=0.70\textheight,keepaspectratio]`

**Layout:**
- Use `\begin{columns}[T,onlytextwidth]` for figure+text side-by-side
- Typical split: 55% figure, 42% text (or 48/49)
- Use TikZ for simple diagrams, flowcharts, and schemas
- Use `tcolorbox` (keybox) for highlighted take-away messages

**Colors:**
- Define a consistent palette (5-6 colors) matching the topic
- Use `\alert{}` for emphasis (red by default)
- Use colored keyboxes for key messages
- Keep backgrounds clean (white or very light)

**Keybox pattern** (for take-away messages):
```latex
\newcommand{\kb}[2][maincolor]{%
  \begin{tcolorbox}[colback=#1!8,colframe=#1,arc=3pt,
    boxrule=0.8pt,top=2pt,bottom=2pt,left=5pt,right=5pt]
  \footnotesize #2
  \end{tcolorbox}}
```

#### Slide Types

**Title slide:**
```latex
\begin{frame}[plain]\titlepage\end{frame}
```

**Outline slide** (optional, for talks > 15 min):
```latex
\begin{frame}{Plan}
\tableofcontents[hideallsubsections]
\end{frame}
```

**Content slide with figure:**
```latex
\begin{frame}{Clear, Specific Title (Not Generic)}
\begin{columns}[T,onlytextwidth]
\begin{column}{0.55\textwidth}
  \centering
  \includegraphics[width=\linewidth,height=0.70\textheight,
    keepaspectratio]{figures/my_figure.png}
\end{column}
\begin{column}{0.42\textwidth}
  \begin{itemize}\setlength\itemsep{3pt}
    \item Key observation 1
    \item Key observation 2
    \item Interpretation
  \end{itemize}
  \vspace{3pt}
  \kb{Take-home message for this slide}
\end{column}
\end{columns}
\end{frame}
```

**Data introduction slide** (MANDATORY before showing results):
```latex
\begin{frame}{What we analyzed}
\begin{columns}[T,onlytextwidth]
\begin{column}{0.48\textwidth}
  % Table or diagram of dataset composition
\end{column}
\begin{column}{0.48\textwidth}
  % Pipeline overview or method summary
\end{column}
\end{columns}
\end{frame}
```

**Synthesis slide** (the most important slide):
```latex
\begin{frame}{Synthesis / Key Messages}
% Use TikZ, numbered list, or visual summary
% NOT a repetition of all results
% Instead: the integrated story, the big picture
\end{frame}
```

**Closing slide:**
```latex
\begin{frame}[standout]
  \centering
  {\large\bfseries Thank you / Merci}\\[10pt]
  \normalsize
  \textbf{Code:} \texttt{github.com/...}\\[4pt]
  \textbf{Data:} \texttt{...}\\[4pt]
  \textbf{Contact:} \texttt{email@...}
\end{frame}
```

### Phase 4: Self-Containment Checklist

Before finalizing, verify the presentation is self-contained:

- [ ] **Datasets explained**: sample sizes, species/groups, source database, how collected
- [ ] **Methods explained**: at minimum a 1-slide overview; audience must understand what "core genome" / "enrichment" / your key method means
- [ ] **Jargon defined**: any domain-specific term used more than twice must be explained on first use
- [ ] **Figures annotated**: all axes labeled, colors explained, sample sizes noted
- [ ] **Statistical tests explained**: what test, what p-value means in context, not just "p < 0.001"
- [ ] **Limitations acknowledged**: at least one slide or section on caveats
- [ ] **Narrative coherent**: someone who missed the first 2 slides can still follow from slide 3 onward
- [ ] **Synthesis slide works standalone**: if someone only sees this one slide, they get the main message

### Phase 5: Compilation and Verification

```bash
cd <article_directory>
pdflatex -interaction=nonstopmode slides.tex
pdflatex -interaction=nonstopmode slides.tex   # second pass for refs
grep -c "^!" slides.log                        # must be 0
grep -c "LaTeX Warning.*undefined" slides.log  # must be 0
```

Check:
- All figures render (no missing file errors)
- No overfull frames (text spilling off slides)
- Slide count matches expected duration
- Section progress bar works

## Updating Existing Slides

When updating slides after article modifications:

1. **Read the article diff** (or understand what changed from context)
2. **Identify which slides are affected** — don't blindly regenerate everything
3. **Update affected slides only**, preserving the existing style and structure
4. **Check narrative coherence** — a change in one slide may require transition updates
5. **Recompile and verify**

Common update scenarios:
- **Title changed** → update title slide + any self-references
- **Key number changed** → search all slides for that number
- **New caveat added** → add to relevant slide + limitations
- **Section restructured** → may need to reorder slides
- **New result added** → insert slide in narrative-appropriate position

## Language

- Match the article language by default
- For French presentations: use `[french]{babel}`, French punctuation rules (espace avant : ; ? !)
- For English presentations: use `[english]{babel}`
- Technical terms stay in their original language regardless

## Common Mistakes to Avoid

1. **The "paper dump"**: copying paragraphs from the article onto slides. Never.
2. **The methods maze**: spending 5 slides on methods before showing any result.
3. **The naked figure**: showing a complex figure without explaining what we're looking at.
4. **The missing context**: jumping to results without explaining the dataset.
5. **The anticlimax**: putting the most important result in the middle, not building to it.
6. **The wall of numbers**: showing tables with 20+ numbers. Simplify to key comparisons.
7. **The orphan slide**: a slide with no connection to what came before or after.
8. **The generic title**: "Results (1)", "Methods". Use specific, informative titles.
9. **The absent synthesis**: ending with "perspectives" instead of a clear take-home message.
10. **The overcrowded slide**: if you need to use `[shrink]`, the slide has too much content.

## Appendix Slides

For anticipated questions, add appendix slides after `\appendix`:
- Detailed methods
- Supplementary figures
- Statistical details
- Comparison tables

These don't count toward the main presentation time but show preparedness.

## Output

The skill produces a single `slides.tex` file in the article directory (or the current working directory), compilable with `pdflatex`. The file should:
- Be well-commented with section separators
- Use consistent formatting throughout
- Include a `\graphicspath` pointing to the figures directory
- Compile cleanly in two passes with zero errors
