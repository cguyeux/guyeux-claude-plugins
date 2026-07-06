---
name: zenodo-deposit
description: >-
  Dépôt automatique d'un artefact de recherche (code, données, harnais
  d'évaluation, supplementary materials) sur Zenodo, pour obtenir un DOI citable
  à insérer dans un manuscrit. Le token Zenodo est configuré UNE SEULE FOIS puis
  réutilisé pour tous les articles (stocké dans ~/.config/zenodo/, jamais
  recréé). Crée un brouillon, téléverse l'archive, écrit les métadonnées (titre,
  auteurs, ORCID, licence extraits du .tex), RÉSERVE le DOI, et peut remplacer le
  placeholder DOI dans le main.tex. La publication (irréversible) reste une étape
  explicite, confirmée par l'auteur. Utiliser quand l'utilisateur veut « déposer
  sur Zenodo », « obtenir un DOI », « publier le harnais / les supplementary »,
  « activer le DOI Zenodo de l'article », ou tape /zenodo-deposit.
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
---

# /zenodo-deposit — Dépôt Zenodo réutilisable (DOI citable)

Résout définitivement la corvée « recréer un token à chaque article » : le token
Zenodo est **réutilisable à vie** ; ce skill le stocke une fois et le réutilise.

Script : `scripts/zenodo_deposit.py` (urllib, zéro dépendance).

## Préalable — mémoire projet

Lire `cahier_de_labo.md` / `JOURNAL.md` / `CLAUDE.md` du projet, et
`review/INDEX.md` / `response.md` si présents, pour connaître l'état (souvent le
DOI est une remarque de review du type R01 « released sans DOI »).

## Phase 0 — Token (une seule fois, jamais ré-créé)

1. Tester si un token est déjà configuré :
   ```bash
   python3 scripts/zenodo_deposit.py status 0 2>&1 | head -3   # imprime le message token si absent
   ```
   (ou vérifier `~/.config/zenodo/token`).
2. **S'il manque** : guider l'utilisateur (voir `references/TOKEN_SETUP.md`) — créer
   un Personal Access Token sur zenodo.org (scopes `deposit:write` + `deposit:actions`),
   puis l'enregistrer une fois :
   ```bash
   printf '%s' 'COLLER_LE_TOKEN' | python3 scripts/zenodo_deposit.py set-token
   ```
   Insister : **c'est à faire une seule fois**, le token est ensuite réutilisé pour
   tous les dépôts futurs. Ne jamais committer le token ; ne jamais l'afficher.
3. **Répétition à blanc** possible sur le bac à sable (`--sandbox`, token sandbox
   séparé créé sur sandbox.zenodo.org) avant le vrai dépôt.

## Phase 1 — Quoi déposer

Identifier l'artefact à déposer (demander si ambigu) : typiquement le **harnais
d'évaluation** / le **code de reproduction** / les **supplementary materials**.
C'est un répertoire (ex. `paper/eval/`, `supplementary_materials/`) que le script
archive automatiquement (`--src DIR`, exclut `__pycache__`/`.pyc`/`.git`), ou une
archive `.zip` déjà prête (`--zip FILE`). Vérifier que l'archive est
**autosuffisante pour reproduire les chiffres du manuscrit** (scripts + données +
README), pas seulement le PDF.

## Phase 2 — Métadonnées

Construire les métadonnées Zenodo à partir du `.tex` :
- **title** : reformuler le `\title{}` (ou « <Système> reproducibility bundle / evaluation
  harness for: <titre de l'article> »).
- **creators** : extraire `\author{}` + l'affiliation (`\institute{}`) + l'ORCID
  (`\orcidID{}`). Format script : `--creator "Nom, Prénom|Affiliation|0000-...."`.
- **description** : 4-8 lignes décrivant le contenu et comment reproduire (lister les
  scripts et les jeux de données).
- **license** : `mit` pour du code, `cc-by-4.0` pour des données mixtes (défaut).
- **upload_type** : `software` (harnais/code) ou `dataset`.
- **keywords** : repris des `\keywords{}`.

Écrire un `metadata.json` (format Zenodo, cf. l'exemple ci-dessous) dans le dossier
du projet (ex. `paper/zenodo/metadata.json`), OU passer les champs en flags. Préférer
le `metadata.json` versionné (traçable, réutilisable pour une v2).

## Phase 3 — Dépôt (brouillon + DOI réservé, SANS publier)

```bash
python3 scripts/zenodo_deposit.py create \
  --src paper/eval \
  --metadata paper/zenodo/metadata.json \
  --patch-tex paper/main.tex
```
Le script : crée le brouillon, upload, écrit les métadonnées, **réserve le DOI**, et
si `--patch-tex` est fourni remplace le placeholder `[Zenodo DOI to be inserted]` par
`\url{https://doi.org/<doi>}`. Recompiler ensuite le manuscrit et vérifier que le DOI
apparaît bien (le DOI vit dans le PDF rendu).

## Phase 4 — Publication (IRRÉVERSIBLE — confirmation explicite)

**Ne jamais publier sans le feu vert explicite de l'auteur.** Un enregistrement
Zenodo publié ne peut pas être supprimé (seulement versionné). Le DOI réservé est
déjà citable et s'active à la publication — pratique standard : réserver à la
soumission, publier au camera-ready.

Quand l'auteur confirme, après vérification du brouillon sur le portail :
```bash
python3 scripts/zenodo_deposit.py publish <id>
```

## Exemple de metadata.json

```json
{
  "metadata": {
    "upload_type": "software",
    "title": "<Système> evaluation harness for: <titre de l'article>",
    "creators": [
      {"name": "Nom, Prénom", "affiliation": "...", "orcid": "0000-0000-0000-0000"}
    ],
    "description": "Harness reproducing every number reported in ... Contents: ...",
    "keywords": ["...", "..."],
    "access_right": "open",
    "license": "mit",
    "language": "eng"
  }
}
```

## Consignes

- **Token : une fois pour toutes.** Ne jamais demander de recréer un token si
  `~/.config/zenodo/token` existe déjà ; ne jamais le committer ni l'afficher.
- **Jamais de publication automatique** : `create` s'arrête au brouillon ; `publish`
  exige une confirmation explicite.
- **Ne pas inventer de DOI** : tant que le dépôt n'est pas créé, garder le placeholder.
- Versionner `metadata.json` et le script de dépôt dans le repo de l'article ;
  **gitignorer l'archive .zip** (régénérable depuis la source).

## Épilogue — Résumé et suite

Clore par : ce qui a été déposé, le DOI réservé, l'état (brouillon non publié /
publié), et le rappel que la publication est une action auteur. Suggérer la suite du
pipeline qualité (`/claim-check`, `/bib-check`, `/manuscript-review`,
`/reviewer-response next`) selon l'état du manuscrit.
