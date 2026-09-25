---
name: init-project
description: Scaffold a new academic research project — short CLAUDE.md (context, structure, pointers ; rules inherited from codes/CLAUDE.md), the five memory artefacts, standard dirs, and `article/` as its own Git repo on the article voie. Flags `--voie article|réponse|réoutillage|coordination`, `--famille`. Use on `/init-project <name>`, "initialise un projet", "scaffolde un projet", "create a new research project".
---

# init-project — Scaffold a research project

## When to use this skill

Trigger when the user asks to:
- "initialise un projet" / "init un projet" / "create a project"
- "scaffolde un projet" / "set up a research project"
- "create a new research project" / "set up a project for an article"
- "préparer un projet pour un article"
- types `/init-project <name>` or `/init-project <name> --title "..."`

Works in any directory (the tree is created in the current working directory by
default, or at the path given via `--at`).

## What this skill does

Calls `${CLAUDE_PLUGIN_ROOT}/skills/init-project/init_project.py` to create a standard research-project tree at the **current working directory** by default, or at a path the user specifies.

The standard tree is :

```
<name>/
├── CLAUDE.md                   # Contexte, structure, pointeurs — RIEN d'hérité (voir ci-dessous)
├── cahier_de_labo.md           # Lab notebook (append-only, timestamped)
├── etat_des_decouvertes.md     # En-tête : **Voie :** (+ **Phase :** sur article, "non applicable" sur coordination)
├── pistes.md                   # Un bloc P1 (P2, …) par voie déclarée
├── JOURNAL.md                  # Optional: high-level facts log
├── .gitignore                  # Excludes article/ from parent git (voie article)
├── article/                    # ── VOIE ARTICLE SEULEMENT : standalone Git repository ──
│   ├── .git/                   # Independent git, push to GitHub for Overleaf sync
│   ├── .gitignore              # LaTeX build artifacts
│   ├── main.tex
│   ├── references.bib
│   ├── Makefile
│   ├── figures/
│   ├── supplementary_materials/
│   └── review/
│       └── INDEX.md
├── reponse/                    # ── VOIE RÉPONSE SEULEMENT : brouillons du mail, notes ──
├── analyses/                   # Phased analysis scripts (phase1_*.py, phase2_*.py)
├── data/                       # Input data (documents reçus → /corpus-ingest)
├── corpus/                     # Derived by /corpus-ingest: INDEX.md, one folder per document
├── résultats/                  # Generated outputs
├── experiments/                # Ad-hoc experiments (YYYY-MM-DD_description/)
└── litterature_review/
    ├── index.md
    └── references.bib
```

Key choices:
- **Le `CLAUDE.md` de projet est court (≈ 35 lignes) et ne porte que le contexte, la structure
  et des pointeurs.** Depuis la refonte P2.3 (2026-09-13), il ne recopie plus les sections
  Cahier, État et pistes, Cycle de vie, Vérification avant calcul, Pipeline qualité ni Calcul
  distant : toutes vivent dans `~/docs/codes/CLAUDE.md`, chargé automatiquement par toute session
  ouverte sous `codes/` (les `CLAUDE.md` de tous les ancêtres du cwd sont chargés au lancement).
  Les recopier dans le projet ferait lire deux fois la même règle et figerait une version qui
  divergerait de la source. Ne pas les rajouter à la main après scaffold.
- **La VOIE se déclare** (`--voie`, défaut `article`) : `article`, `réponse` (le livrable est un
  mail argumenté et ses notes), `réoutillage` (un skill, une fiche KB, un ticket amont),
  `coordination` (l'entretien continu d'une structure ou d'un collectif : GIS, réseau,
  plateforme, comité — le livrable est l'ensemble vivant de ses artefacts de communication et de
  gouvernance, sans porte de clôture unique), cumulables par virgule. Elle est inscrite dans
  l'en-tête de `etat_des_decouvertes.md`, seule copie, et le hook `SessionStart` comme
  `/cycle-projet` la lisent : sans `article`, aucune phase n'est posée (« non applicable » sur
  la voie coordination), aucun `article/` n'est créé, et les pistes initiales sont celles du
  livrable réel. `--voie` s'applique aussi avec `--migrate` (§ ci-dessous) ; par défaut historique
  `--migrate` seul continue de supposer `article`, ce qui a posé une voie fausse sur un projet de
  coordination (`gis`, 2026-09-16) avant que cette option n'existe — toujours passer `--voie`
  explicitement sur `--migrate` quand le projet n'est pas un article.
- **La FAMILLE se déclare ou se devine** (`--famille`, une des dix familles de `codes/`) : devinée
  depuis le chemin `~/docs/codes/<famille>/…`, inscrite dans le `CLAUDE.md` ; `mtbc` implique
  `--domain mtbc`. Sans `--at`, `--famille X` crée le projet dans `~/docs/codes/X/` (le répertoire
  doit exister). Elle servira de repli au profil d'activation des plugins (refonte P5.5).
- **Convention des cinq emplacements, détectée et appliquée** (depuis le 2026-09-23) : si le
  répertoire parent visé contient un `en_cours/`, le projet y est créé au lieu de la racine de la
  famille, parce que le statut d'un projet EST son emplacement sur le disque (`codes/CLAUDE.md`).
  La convention se détecte par la présence du répertoire, elle n'est pas codée en dur sur une
  famille — seule `mtbc/` l'a adoptée à ce jour, une autre en bénéficiera sans retoucher le script.
  Un `--at` explicite reste souverain : le script avertit alors, mais ne redirige pas.
- **`article/` is its own git repo**, with an initial commit. The user can then `cd article && gh repo create` to publish it; once on GitHub it can be paired with Overleaf for collaborative editing with non-coders.
- **Parent `.gitignore`** automatically lists `article/` so the parent git (if any) does not track the article files. The article repo is the single source of truth for the manuscript.
- Templates are intentionally generic (no domain-specific bits). Use `--domain mtbc`, or its honest alias `--domain bacterio`, to get the bacterial-phylogenomics-flavoured `main.tex` (custom LaTeX commands); the conventions themselves (SPDI format, RAxML-NG) are inherited from `codes/mtbc/CLAUDE.md`, not recopied. The domain fits **any clonal bacterial pathogen** — MTBC, *Yersinia*, *Leptospira* — only the reference genome changes (H37Rv/`NC_000962.3`, CO92/`NC_003143`…), so do not read the internal name `mtbc` as a restriction to mycobacteria.

## How to invoke

Resolve the script path : `${CLAUDE_PLUGIN_ROOT}/skills/init-project/init_project.py`.
Run :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/init-project/init_project.py <name> [--title "..."] [--at <parent-dir>] [--famille <famille>] [--voie article|réponse|réoutillage|coordination[,…]] [--domain mtbc|droit|generic] [--no-classify] [--no-git] [--no-parent-gitignore]
```

**Flags** :
- `name` (required) : directory name to create.
- `--title "..."` : full project title (used in `CLAUDE.md` and `main.tex`). Defaults to a humanized form of `<name>`.
- `--at <dir>` : parent directory where `<name>/` is created. Defaults to `~/docs/codes/<famille>/` when `--famille` is given and the cwd is not already inside it, else the current working directory. When that default parent holds an `en_cours/`, the project goes there (five-emplacements convention) ; an explicit `--at` bypasses the redirection with a warning.
- `--famille pompiers|mtbc|bio|ia|shs|cours|admin|outillage|archives|autre` : famille de rangement de `codes/`. Guessed from the path when omitted ; written in `CLAUDE.md` ; `mtbc` implies `--domain mtbc`.
- `--voie article,réponse,réoutillage,coordination` (comma-separated, default `article`) : deliverable(s) of the project. Declared in the header of `etat_des_decouvertes.md`. Without `article` : no `article/`, no `**Phase :**` (coordination writes "non applicable" instead), and the initial `pistes.md` block matches the declared voie(s). `réponse` also creates `reponse/`. Also accepted alongside `--migrate` (defaults to `article` there for backward compatibility — pass it explicitly for a non-article project).
- `--domain mtbc` : applies the bacterial-phylogenomics-flavoured templates (extra LaTeX commands and naming conventions from the Guyeux research group's existing scaffold).
- `--domain droit` : legal-scholarship project. Writes the law conventions into `CLAUDE.md` (detailed references in footnotes, mandatory verification of case law against official sources) and enables the `droit` plugin **for that project only**, in `<project>/.claude/settings.json`.
- **Domain is GUESSED when `--domain` is omitted.** A classifier reads the name and title (and, with `--migrate`, the contents of the existing project) and prints its evidence: the strong legal terms found, the weak ones, and the biological terms that veto a law verdict. It never switches silently and it is deliberately conservative: it prefers missing a borderline project to capturing a biology one. `--no-classify` disarms it; an explicit `--domain` overrides it without discussion.
- `--no-git` : skip git initialisation in `article/` (still creates the directory).
- `--no-parent-gitignore` : skip writing/updating the parent `.gitignore`.
- `--from-piste Pxx --registry <pistes.md>` : this project originates from a piste already
  written elsewhere (typically a `[SÉRENDIPITÉ ← <projet>]` entry promoted by `/recadrage`).
  The piste's full text is recopied verbatim into the new project's `cahier_de_labo.md` (nothing
  is lost, nothing is synthesized), and the source piste is marked migrated **by local mutation**
  in `--registry` : its state tag flips to `[abandonné]` (never downgrading an existing
  `[réalisé]`) and a `MIGRÉ vers <name> (<date>)` line is inserted right after its `origine:`
  line. No other line of the registry is touched — this is the non-destructive migration
  discipline described in the `recadrage` skill's Phase 4 (scission).

## Discovery pass (always runs on project creation, and on `--migrate`)

Before finishing, the script does three crude, keyword-based scans and prints their results —
never silently. None is a semantic judgement (this script has no LLM in it), so a hit is a
signal to verify by hand, not proof of redundancy or relevance :

1. **Knowledge base** (`~/.claude/knowledge/KNOWLEDGE.md`) : keywords extracted from `name` and
   `--title` (>=4 chars, stopwords dropped) are matched against the index's one-line entries.
   Any hit is printed with the KB filename, so prior inter-project learnings aren't re-derived.
2. **Sibling projects** : every other directory directly under the target parent that has a
   `CLAUDE.md` is grepped for the same keywords. A hit suggests an existing project may already
   cover (part of) this ground — worth extending instead of duplicating.
3. **Sibling scripts** (`scan_sibling_scripts`) : every `.py` under a sibling's `analyses/` (plus
   its top level) is checked for reusable code, but **only its module-level docstring header is
   read** — never the body — against the same keywords. Convention detailed in
   `~/.agents/knowledge/python-patterns.md` (2026-08-26 entry) : a script meant to outlive one task
   should carry a labelled header (`Objet/Entrées/Sorties/Réutilisable/Projet/Date`) so this scan
   stays cheap even on a repo with hundreds of scripts. A hit is printed with the header itself, so
   no further `Read` is needed to judge relevance. Scripts that match by **filename only** (no
   header present) are listed separately for manual inspection — never auto-migrated in bulk; a
   missing header gets written the next time an agent reads that script in full for another reason.

This is why `/init-project` should always be invoked from (or with `--at` pointing at) the
directory where sibling research projects actually live — e.g. `mtbc/` for MTBC sub-projects —
not from an unrelated working directory, or the sibling scans find nothing to compare against.

## After running

Tell the user :
1. The project tree was created at `<absolute-path>/<name>/`, with its famille and voie(s).
2. On the `article` voie, `article/` is its own git repo with one initial commit.
3. Suggested next steps :
   - Edit `<name>/CLAUDE.md` to fill in the scientific context — **without** pasting back the
     cycle / cahier / pipeline rules, which are inherited from `~/docs/codes/CLAUDE.md`.
   - In `<name>/article/`, run `gh repo create <repo-name> --private --source=. --push` to publish the article repo, then connect it to Overleaf via *Menu → GitHub*.
   - Add the parent project to git (if not already) : `git add . && git commit` (the `article/` is excluded automatically by the new `.gitignore`).
   - Start the cahier de labo with `/cahier-de-labo update`.
   - Si le script signale `⚠ Registre parent absent`, créer `<parent>/pistes.md`
     avec l'en-tête `/pistes` standard : c'est le **registre de sérendipité** du
     répertoire, où atterrissent les découvertes faites dans un projet mais qui
     n'y ont pas leur place. Sans lui, elles se perdent à la clôture du projet
     (cf. skill `recadrage`).

## Important notes

- The script uses stdlib only (no external dependencies).
- The script never overwrites an existing directory — it errors out if `<name>/` already exists at the target.
- The `article/` git repo gets an initial commit signed by the local git config of the user; if `git config user.email` is unset, the commit will fail and the script will print a hint. We do **not** pass `--no-verify` or otherwise bypass git config rules.
- The legacy domain-specific init script (`~/docs/codes/mtbc/init_project.py`) is kept untouched; this generalized version supersedes it for new projects outside that directory.
