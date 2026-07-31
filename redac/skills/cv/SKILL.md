---
name: cv
description: >
  Extracts relevant information from Christophe Guyeux's LaTeX CV to support writing
  project proposals, grant applications (ANR, ERC, Horizon, LabCom), job applications,
  recommendation letters, research summaries, or any document requiring accurate
  self-presentation. Use this skill whenever the user is drafting a project proposal,
  candidature dossier, cover letter, research summary, list of publications, supervision
  record, funding history, or needs to cite specific CV elements (publications, funding,
  impact metrics, co-authors). Trigger even when the user doesn't say "CV" explicitly,
  if they're writing something professional about their research, teaching, or supervision,
  this skill provides the sourced material they need.
---

# CV Extraction Skill

You have access to Christophe Guyeux's complete LaTeX CV, located in `~/docs/cv/`.

Check the path exists before reading (`ls ~/docs/cv/cvDoc/`). If it does not, ask
the user where the CV lives rather than answering from memory: every figure in this
skill (h-index, funding amounts, thesis dates) must come from the source files.

## Your job

When the user is drafting a document (project proposal, application, letter, bio, etc.), read the relevant CV files and extract **exactly what they need**, **sourced to the specific file and section**. Do not summarize from memory, always read the actual files.

## CV structure

**Root**: `~/docs/cv/`
- `cv.tex`, main content entry point (shows overall structure)
- `affiliations.txt`, all co-authors: `Lastname, Firstname $ Institution $ Country`
- `references/conferences.bib`, full BibTeX for conference papers (340 KB)
- `references/journals.bib`, full BibTeX for journal papers (273 KB)
- `references/abstracts_found.json`, `references/abstracts_missing.json`, abstract
  retrieval status per entry; useful to know which papers have no abstract on file
- Variant CVs at the root (`erc.tex`, `iuf.tex`, `deleg.tex`, `avancement.tex`,
  `chrysalide.tex`) assemble the same `cvDoc/` blocks for a specific dossier. When
  the user is preparing one of these exact dossiers, read the variant first: it
  already encodes which sections that funder or committee expects.

**Modular content in `cvDoc/`**, read only what the context requires:

| File | Content |
|------|---------|
| `debut.tex` | Identity: name, position, affiliation (Femto-ST / UFC) |
| `researchArea.tex` | Research domains: AI/ML, bioinformatics, TB genomics, civil security |
| `researchPublicationsSummary.tex` | Key metrics: h-index 35, i10-index 121, ~250 publications |
| `research5pub.tex` | 5 representative publications with journal names and years |
| `journals.tex` | Recent journal articles (reverse chronological, with DOIs) |
| `journalsOld.tex` | Older journal articles (archive) |
| `conferences.tex` | Recent conference papers |
| `conferencesOld.tex` | Older conference papers |
| `submitted.tex` | Papers currently under review |
| `researchFundings.tex` | Grants and contracts (ANR Labcom SADIAND 360 k€, Interreg RESponSE 550 k€, etc.) |
| `researchImpact.tex` | Scientific and societal impact (200k TB genomes, SDIS deployments) |
| `researchAwards.tex` | Distinctions: PEDR, RIPEC, computing hour grants |
| `researchOrganizationEditor.tex` | Conference organisation, editorial and PC roles |
| `researchInternationalMobility.tex` | International visits (Lebanon, Italy, Sweden) |
| `researchComm.tex` | Science communication, media, outreach |
| `supervisionPhD.tex` | PhD supervision (ongoing and completed) |
| `evaluationPhD.tex` | PhD juries, ANR expert, journal reviewing |
| `teachingDetails.tex` | Teaching activities by institution and year |
| `teachingAcademic.tex` | Administrative and academic responsibilities |
| `expertise.tex` | Expert evaluation roles |
| `deeps.tex` | Detailed entry for the DEEPS project (earthquake prediction) |
| `researchSupervision.tex` | Supervision and evaluation section wrapper |
| `research.tex`, `teaching.tex`, `publications.tex` | Section wrappers that `\input` the blocks above; read them to see the canonical ordering |
| `journals2pages.tex`, `publications2pages.tex`, `teachingAccShort.tex` | Condensed variants for page-limited dossiers |
| `titre.tex` | Title block (formatting only, no content) |

Blocks are wrapped in `\begin{francais}...\end{francais}` and
`\begin{anglais}...\end{anglais}`. Read both and pick the one matching the target
document's language rather than translating the wrong one.

## Step-by-step process

### 1. Identify the document type and what it needs

Map the request to the files below. Use your judgement for combinations.

| Document type | Primary files to read |
|---------------|-----------------------|
| ANR / LabCom proposal | `researchFundings`, `researchImpact`, `researchArea`, `supervisionPhD`, `researchPublicationsSummary` |
| ERC proposal | `researchArea`, `research5pub`, `researchPublicationsSummary`, `researchInternationalMobility`, `researchFundings` |
| Horizon / Interreg | `researchFundings`, `researchImpact`, `researchArea`, `researchOrganizationEditor` |
| Candidature poste / promotion | `debut`, `researchArea`, `researchPublicationsSummary`, `researchAwards`, `supervisionPhD`, `teachingDetails`, `teachingAcademic` |
| Lettre de recommandation | `debut`, `researchArea`, `supervisionPhD`, `researchImpact` |
| Résumé de recherche / bio | `debut`, `researchArea`, `researchPublicationsSummary`, `research5pub`, `researchImpact` |
| Liste de publications | `journals`, `journalsOld`, `conferences`, `conferencesOld` |
| Encadrements | `supervisionPhD`, `evaluationPhD` |
| Financement | `researchFundings`, `researchAwards` |
| Affiliations co-auteurs | `affiliations.txt` |

### 2. Read the files

Use the Read tool on each relevant file. For the BibTeX databases (`references/*.bib`), use Grep with specific author names, keywords, or years rather than loading the full file, they are very large.

### 3. Extract and present

Present extracted information:
- **Structured** by section (publications, funding, supervision, etc.)
- **Properly referenced**: include the actual bibliographic or administrative reference, not the internal .tex file name. The goal is that the user can paste the result directly into their document:
  - For a **publication**: authors, title, journal/conference, volume, pages, year, DOI
  - For a **funding project**: full project name, funding agency, grant reference or number if available, amount, dates, your role
  - For a **supervised thesis**: student name, thesis title, institution, year defended or expected, your role (director / co-director)
  - For a **co-author affiliation**: exact name and institution as it appears in affiliations.txt
- **Ready to use**: paste-ready text or structured lists, not a meta-commentary about the CV

If the user needs specific BibTeX entries, grep `references/conferences.bib` or `references/journals.bib` by title keywords or year.

If the user needs co-author affiliations, grep `affiliations.txt` by last name.

### 4. Language

Match the language of the target document:
- French document → extract and present in French
- English document → translate or present in English as needed
- When the LaTeX source has bilingual blocks (`\begin{francais}...\end{francais}`), read both and pick the right one

## What good output looks like

When the user says *"I'm writing an ANR AAPG proposal, give me the funding section"*, you should:
1. Read `researchFundings.tex` and `researchAwards.tex`
2. Return the actual content with proper references: project name, grant agency, reference number if available, amount, dates, your role, ready to paste
3. Offer to also extract supervision or impact data if relevant

When the user says *"Who are my co-authors at University of Monastir?"*, you should:
1. Grep `affiliations.txt` for "Monastir"
2. Return the matching lines formatted cleanly

## Important notes

- **Never invent or approximate** publication counts, h-index, funding amounts, or dates, read the source.
- The CV files use LaTeX macros. Strip formatting commands (`\textbf{}`, `\href{}{}`, `\emph{}`, etc.) when presenting content, show the plain text content.
- For supervision, distinguish clearly between completed PhDs, ongoing theses, and co-supervisions vs. primary supervision.
- `journals.tex` and `conferences.tex` use `etaremune` (reverse-numbered list), the most recent entries appear first.
