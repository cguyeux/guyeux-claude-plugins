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

# /zenodo-deposit : Dépôt Zenodo réutilisable (DOI citable)

Résout définitivement la corvée « recréer un token à chaque article » : le token
Zenodo est **réutilisable à vie** ; ce skill le stocke une fois et le réutilise.

Script : `scripts/zenodo_deposit.py` (urllib, zéro dépendance).

## Préalable : mémoire projet

Lire `cahier_de_labo.md` / `JOURNAL.md` / `CLAUDE.md` du projet, et
`review/INDEX.md` / `response.md` si présents, pour connaître l'état (souvent le
DOI est une remarque de review du type R01 « released sans DOI »).

## Phase 0 : Token (une seule fois, jamais ré-créé)

1. Tester si un token est déjà configuré :
   ```bash
   python3 scripts/zenodo_deposit.py status 0 2>&1 | head -3   # imprime le message token si absent
   ```
   (ou vérifier `~/.config/zenodo/token`).
2. **S'il manque** : guider l'utilisateur (voir `references/TOKEN_SETUP.md`), créer
   un Personal Access Token sur zenodo.org (scopes `deposit:write` + `deposit:actions`),
   puis l'enregistrer une fois :
   ```bash
   printf '%s' 'COLLER_LE_TOKEN' | python3 scripts/zenodo_deposit.py set-token
   ```
   Insister : **c'est à faire une seule fois**, le token est ensuite réutilisé pour
   tous les dépôts futurs. Ne jamais committer le token ; ne jamais l'afficher.
3. **Répétition à blanc** possible sur le bac à sable (`--sandbox`, token sandbox
   séparé créé sur sandbox.zenodo.org) avant le vrai dépôt.

## Phase 1 : Quoi déposer

Identifier l'artefact à déposer (demander si ambigu) : typiquement le **harnais
d'évaluation** / le **code de reproduction** / les **supplementary materials**.
C'est un répertoire (ex. `paper/eval/`, `supplementary_materials/`) que le script
archive automatiquement (`--src DIR`, exclut `__pycache__`/`.pyc`/`.git`), ou une
archive `.zip` déjà prête (`--zip FILE`). Vérifier que l'archive est
**autosuffisante pour reproduire les chiffres du manuscrit** (scripts + données +
README), pas seulement le PDF.

## Phase 2 : Métadonnées

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

## Phase 3 : Dépôt (brouillon + DOI réservé, SANS publier)

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

**Vérification d'intégrité automatique (depuis 2026-07-30).** Après l'upload, le script
compare la **taille** et le **checksum MD5** renvoyés par Zenodo au fichier local ; un
upload tronqué ou corrompu (ex. timeout partiel) fait ÉCHOUER l'opération au lieu de
passer pour un succès. `status <id>` affiche aussi `filesize` + `checksum` par fichier,
pour auditer l'intégrité même a posteriori. Ne jamais se fier au seul « HTTP 200 » : la
taille/somme distante fait foi. Pour un `update` (ré-upload), garder le MÊME nom de dossier
source, sinon l'ancien zip subsiste (le PUT bucket ne remplace que le fichier de même nom).

### Phase 3bis : Déposer une NOUVELLE VERSION d'un record déjà publié (v2, v3...)

`update` ne marche QUE sur un brouillon non publié. Pour une v2 d'un record **publié** (Zenodo
interdit de modifier un record publié ; il faut une version liée sous le même DOI concept) :
```bash
python3 scripts/zenodo_deposit.py new-version <record_id_publié> \
  --zip supplementary_v2.zip --metadata zenodo/metadata.json --patch-tex paper/main.tex
```
Le script fait `POST actions/newversion`, retire les fichiers hérités de la version précédente
(garder avec `--keep-files`), upload la nouvelle archive (avec la même vérif d'intégrité), écrit
les métadonnées et réserve le **DOI de version**. Il s'arrête au brouillon ; la publication reste
`publish <draft_id>`. Note : le `conceptdoi` (visible via `status`) pointe toujours vers la
dernière version, au camera-ready, citer le DOI concept plutôt qu'un DOI de version figé.

> **Sandbox Claude Code : `urllib` est souvent bloqué** (le script est en urllib → échec au 1er
> appel HTTP). Le réseau passe par `curl` direct en Bash. Si le script ne joint pas Zenodo,
> soit lancer la commande depuis le shell de l'utilisateur (réseau réel), soit répliquer le flux
> en curl (`Authorization: Bearer $(cat ~/.config/zenodo/token)`, token jamais affiché). Détail
> du flux curl new-version en KB `~/.claude/knowledge/python-patterns.md`.

## Phase 4 : Publication (IRRÉVERSIBLE, confirmation explicite)

**Ne jamais publier sans le feu vert explicite de l'auteur.** Un enregistrement
Zenodo publié ne peut pas être supprimé (seulement versionné). Le DOI réservé est
déjà citable et s'active à la publication, pratique standard : réserver à la
soumission, publier au camera-ready.

Quand l'auteur confirme, après vérification du brouillon sur le portail :
```bash
python3 scripts/zenodo_deposit.py publish <id>
```

### Checklist AVANT publication (l'ordre compte, tout devient définitif après)

1. **Resynchroniser les métadonnées EN LIGNE, pas seulement le `metadata.json` local.**
   Un titre d'article change souvent entre le dépôt du brouillon et la publication.
   Le brouillon garde l'ancien, et le `metadata.json` corrigé sur disque **ne remonte
   pas tout seul**. Faire un `PUT /api/deposit/depositions/<id>` d'abord. Vécu
   (dark_enzymes 2026-07-31) : brouillon déposé sous l'ancien titre, corrigé en local
   six semaines plus tôt, jamais propagé — le DOI aurait porté l'ancien titre pour
   toujours. Penser aussi à la **description**, qui cite souvent le titre en toutes
   lettres : un `replace` sur le seul champ `title` laisse la description périmée.

2. **Vérifier le CONTENU DISTANT, pas une note de session antérieure.** Le fichier
   local a pu être nettoyé après téléversement, et une note « intégrité vérifiée »
   datant d'une autre séance n'est pas une vérification. Retélécharger depuis Zenodo
   (`files[i].links.download` + `?access_token=`) et contrôler ce qui compte : MD5,
   taille décompressée, **décompte des entrées attendues**, présence nominative des
   éléments que le manuscrit cite. Vécu : bundle de 43 Mo retéléchargé, MD5 conforme,
   3942 fichiers dont exactement 3906 fiches attendues et les 6 cibles nommées
   présentes. C'est cette vérification-là qui autorise un geste irréversible.

3. **Déclarer les liens entre dépôts** via `related_identifiers` (`isDerivedFrom`,
   `isSupplementTo`, `references`) quand plusieurs records se citent l'un l'autre.
   Gratuit avant publication, laborieux après.

### Choisir le DOI À CITER : concept ou version, décidé PAR RESSOURCE

Zenodo donne deux DOI : le **concept** (résout toujours vers la dernière version) et
la **version** (fige un état). Le réflexe « toujours le concept » ou « toujours la
version » est faux : la règle dépend de ce que la phrase du manuscrit promet au
lecteur.

| Ce que le texte dit de la ressource | DOI à citer |
|---|---|
| « continuellement mise à jour », « ressource vivante », atlas, base | **concept** |
| étaye des tables, figures, modèles **nommés** dans le texte | **version** |
| provenance / contexte général | concept |
| « les scripts qui produisent les chiffres rapportés ici » | version |

Test décisif : *le lecteur qui suit ce lien doit-il trouver exactement ce que
l'article décrit, ou l'état courant ?* Vécu (dark_enzymes) : le même manuscrit cite
le **concept** pour l'atlas compagnon (décrit comme continuellement mis à jour) et la
**version** pour son paquet supplémentaire (qui porte les Tables S4/S5 et les modèles
que le texte nomme). Les deux choix sont corrects, dans le même article.

> **★ Ne JAMAIS citer une URL de service quand un identifiant pérenne existe.**
> Une URL de fonction serverless autogénérée (`*.functions.fnc.*.scw.cloud`, Cloud Run,
> Lambda…), et même un domaine custom pointant dessus, n'a pas la stabilité d'une
> citation. Vécu : l'URL de l'atlas compagnon citée en Méthodes comme provenance des
> six cibles est **morte** entre la rédaction et la soumission ; une review l'avait
> signalée comme « mineure : stabiliser l'URL » et le point était resté ouvert. La
> panne a forcé une correction qui était la bonne **indépendamment de la panne**.
> Corollaire de diagnostic : un **TCP qui se connecte puis une poignée TLS qui meurt
> sans réponse** n'est ni un scale-to-zero (qui donnerait un délai puis une réponse)
> ni un container supprimé (qui donnerait un 404 depuis l'edge) — c'est un front cassé
> derrière un load-balancer encore en écoute. Tester **hors bac à sable** avant de
> conclure, et avec des témoins (un site connu doit répondre 200 depuis le même point).

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

## Épilogue : Résumé et suite

Clore par : ce qui a été déposé, le DOI réservé, l'état (brouillon non publié /
publié), et le rappel que la publication est une action auteur. Suggérer la suite du
pipeline qualité (`/claim-check`, `/bib-check`, `/manuscript-review`,
`/reviewer-response next`) selon l'état du manuscrit.
