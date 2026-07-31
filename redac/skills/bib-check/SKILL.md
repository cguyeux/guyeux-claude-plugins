---
name: bib-check
description: >-
  Verification exhaustive des references BibTeX d'un article LaTeX. Verifie l'existence
  reelle de chaque reference en ligne (tbmonitor-papers pour la TB / MTBC, puis CrossRef /
  WebFetch / WebSearch), la coherence des metadonnees (auteurs, titre, annee, journal), la
  pertinence des citations dans leur contexte, et detecte les doublons semantiques. Outil
  anti-hallucinations : marque chaque reference verifiee. A utiliser quand l'utilisateur
  demande de verifier la bibliographie, de controler que les references existent vraiment,
  de detecter des references inventees ou des doublons, ou avant une soumission.
argument-hint: "<chemin vers main.tex>"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, mcp__tbmonitor__execute_sql, mcp__tbmonitor__show_schema
---

# /bib-check -- Verification anti-hallucinations des references

Verifie que chaque reference BibTeX d'un article LaTeX est reelle, correcte,
et pertinente la ou elle est citee. Chaque reference verifiee est marquee dans
le `.bib` pour ne jamais etre re-verifiee.



## Prealable -- Consultation memoire projet

**Avant toute action**, verifier si le projet possede :
1. Un `JOURNAL.md` dans le repertoire du projet → le lire pour connaitre l'historique
2. Un `CLAUDE.md` local → le lire pour les instructions specifiques
3. Un `claim_check.md`, `review/INDEX.md`, ou `response.md` → connaitre l'etat courant

Afficher un bref resume de l'etat connu du projet avant de commencer :

```
Etat projet : [titre article]
  Journal     : [derniere entree ou "absent"]
  Claim-check : [N claims, M infirmes ou "jamais execute"]
  Reviews     : [N reviews, M en cours ou "aucune"]
  Derniere action : [date et description]
```

## Declenchement

```
/bib-check path/to/main.tex
```

Si aucun argument, chercher `main.tex` dans le repertoire courant.

---

## Phase 0 -- Decouverte des fichiers

1. Localiser le fichier `.tex` principal (argument `$ARGUMENTS` ou `main.tex`)
2. Le lire en entier. Resoudre les `\input{}` et `\include{}` pour obtenir
   le texte complet de l'article (lire chaque fichier inclus)
3. Localiser le fichier `.bib` via `\bibliography{...}` ou `\addbibresource{...}`
4. Lire le fichier `.bib` en entier
5. Compter les entrees et identifier celles qui ont deja un champ `verified`
6. Afficher :

```
Bib-check : [titre article]
Fichier .bib : [chemin]
Entrees totales : X
Deja verifiees : Y
A verifier : Z
```

### Cas degrade : PDF seul (aucun .tex/.bib disponible)

Frequent en review externe : on recoit un PDF (soumission, epreuve, article publie) sans les
sources LaTeX. Le skill reste utile en mode degrade -- ne PAS abandonner :

1. **Extraire la liste des references** du PDF (`pdftotext -layout article.pdf out.txt`, la
   bibliographie est en fin de fichier). Extraire aussi le corps pour la Phase 4 (contexte des
   citations), en numerotant les `[n]` / cles.
2. **Impossible** en mode degrade : `verify_bib.py` (Phase 1, pas de .bib), le champ `verified`
   (rien ou l'ecrire), la correction in-place. Le DIRE explicitement dans l'entete du rapport.
3. **Prioriser la verification en ligne** (Phase 3) au lieu de balayer les 60+ references une a
   une : d'abord (a) les references NOUVELLES ou recentes, (b) les auto-citations, (c) toute
   entree que la review a deja signalee douteuse, (d) les noms de modeles/outils recents
   (anti-hallucination : verifier qu'ils existent ET l'identifiant/version exact). Annoncer
   franchement que les references classiques restantes ne sont pas re-verifiees une a une, et
   qu'un bib-check exhaustif exige le .bib source.
4. **Consigner les erreurs dans un fichier externe durable** (le `.txt`/`.md` de travail de la
   review, ou `review/`), puisqu'on ne peut pas annoter le .bib. Horodater.
5. **Verifier sur le rendu, pas sur l'extraction** : une "faute" (espace autour de `=`, ligature,
   accent casse, cesure) peut etre un artefact `pdftotext`. Confirmer les coquilles douteuses en
   lisant la PAGE PDF (Read multimodal) avant de les affirmer.

Pieges de contenu (valent aussi en mode normal, mis en lumiere par le mode PDF-seul) :
- **Bon titre/DOI mais auteurs+pages faux = melange BibTeX** : diffuser TOUJOURS auteurs ET pages
  meme quand le titre matche (un 1er auteur correct ne valide pas les suivants).
- **L'erreur peut etre dans CrossRef lui-meme** (nom propre mal orthographie a la source) : ne pas
  conclure "verifie OK" sur la seule concordance .bib<->CrossRef quand un nom connu est visiblement
  faux ; corriger + recommander un erratum editeur.

---

## Phase 1 -- Verifications structurelles

Executer le script existant pour les verifications automatiques :

```bash
uv run python -B ${CLAUDE_PLUGIN_ROOT}/skills/latex-paper-en/scripts/verify_bib.py \
  [chemin .bib] --tex [chemin .tex] --json
```

Analyser le JSON retourne et rapporter immediatement :
- **Champs manquants** : entrees sans auteur, titre, annee, etc.
- **Cles dupliquees** : meme cle BibTeX utilisee deux fois
- **Entrees orphelines** : presentes dans le `.bib` mais jamais citees dans le `.tex`
- **Citations manquantes** : `\cite{key}` dans le `.tex` sans entree dans le `.bib`

Si le script n'est pas disponible, effectuer ces verifications manuellement en lisant
le `.bib` et le `.tex`.

---

## Phase 1bis -- Coherence INTERNE des entrees (hors ligne, avant toute requete reseau)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/bib-check/scripts/doi_coherence.py references.bib
```

Le prefixe d'un DOI encode l'EDITEUR (`10.1371` = PLOS, `10.1088` = IOP, `10.1126` = AAAS...).
Une entree qui annonce *Physical Biology* avec un DOI `10.1371/journal.pbio` est donc
**contradictoire avec elle-meme**, et c'est decidable SANS RESEAU. Ce cas apparait quand deux
articles sont fusionnes en une entree (moisson automatique, LLM, copier-coller).

**Pourquoi la Phase 3 ne suffit PAS a l'attraper.** Interroger PubMed AVEC le PMID de l'entree
rend le papier de ce PMID, qui existe, et la verification passe au vert. **Verifier qu'un
identifiant RESOUT ne prouve rien sur la COHERENCE de l'entree qui le porte.** Il faut confronter
les champs entre eux, pas seulement chaque champ au monde exterieur.

**Conception de l'outil, et le piege qu'il a fallu eviter.** La v1 faisait « prefixe -> editeur,
puis le journal est-il un journal de cet editeur ? » : INUTILISABLE, Elsevier publie des milliers
de titres, donc tout journal absent de la liste devenait un faux positif (15 alertes, 15 fausses).
La v2 part d'une **liste blanche de journaux a editeur certain** et n'alerte QUE sur ceux-la : un
journal inconnu n'est pas verifie, et c'est voulu, **mieux vaut ne rien dire que dire faux**.

## Phase 2 -- Detection de doublons semantiques

Comparer **toutes les paires d'entrees** pour detecter le meme article sous des cles
differentes. Criteres de doublon :

- Titres quasi-identiques (ignorer casse, ponctuation, accolades LaTeX)
- Memes premiers auteurs + meme annee
- Meme DOI

Pour chaque doublon detecte, signaler :
```
DOUBLON : @key1 et @key2 semblent etre le meme article
  Titre 1 : ...
  Titre 2 : ...
  Recommandation : conserver @key1, remplacer \cite{key2} par \cite{key1}
```

---

## Phase 3 -- Verification en ligne (coeur du skill)

**Consulter** `references/VERIFICATION_PROTOCOL.md` avant de commencer cette phase.

### Ordre de priorite des sources pour les references TB / MTBC

Pour toute reference relevant de la tuberculose ou du MTBC, interroger
d'ABORD le skill `tbmonitor-papers` : il valide en SQL sub-seconde l'existence
d'une reference (par DOI ou par titre) contre le corpus pre-indexe de
~190 000 papiers PubMed TB. N'en venir a WebFetch / OpenAlex / CrossRef que
si la reference n'y figure pas (sujet hors TB, rapport, these, papier tres
recent non encore ingere).

### Voie rapide et AUTORITAIRE pour les entrees a DOI : CrossRef

Pour toute entree portant un `doi`, la source primaire la plus fiable et la plus
rapide est l'API CrossRef (`https://api.crossref.org/works/<doi>`), qui rend les
metadonnees officielles de l'editeur (title exact, auteurs, annee print/online,
container-title, volume, pages). Preferer ce diff direct au diff sur des snippets
WebSearch (moins fiables). Recette :
1. Recuperer chaque DOI puis **diff au champ `.bib`** : title (tolerer casse,
   diacritiques ET balises HTML `<i>...</i>` que CrossRef inclut parfois dans le
   titre), annee (accepter print OU online), journal, volume, 1er auteur.
2. Un DOI qui **resout en HTTP 200** prouve l'existence ; un titre qui diffe (hors
   casse/HTML) = titre a corriger meme si auteurs/annee/journal collent.
3. **Piege d'environnement sandboxe** : `urllib`/`requests` en Python et un `curl`
   lance via `subprocess` peuvent etre **sans reseau** (reponse vide, champs `None`
   trompeurs, pas d'exception). Si un diff pur-Python rend tous les champs vides
   alors qu'un `curl` direct de test passe (HTTP 200), basculer sur la recette
   fiable : **boucle bash `curl` qui ecrit chaque reponse dans un fichier**
   (`curl -s -A 'bibcheck (mailto:...)' "$url" -o /tmp/xref/$key.json`), puis
   **parser les fichiers hors-ligne** en Python (aucun reseau requis).
Pour les entrees SANS DOI ou non couvertes par CrossRef (rapports, theses,
pre-2000), garder la voie WebSearch + WebFetch ci-dessous.

Pour chaque entree **sans champ `verified`**, proceder par lots de 10 :

### Pour chaque entree :

1. **Rechercher** le papier via WebSearch :
   - Requete : `"titre exact" premier_auteur annee`
   - Chercher dans des sources academiques (Google Scholar, Semantic Scholar, CrossRef, PubMed)

2. **Verifier l'existence** :
   - Le papier apparait-il dans au moins une source academique fiable ?
   - Si introuvable et publie apres 2000 : flag **POSSIBLEMENT FABRIQUE**
   - Si introuvable et publie avant 2000 : flag **non verifiable en ligne**
   - ⚠ **L'existence ne suffit PAS.** Confirmer qu'un papier des memes auteurs,
     meme annee, meme journal existe ne valide RIEN du champ `title`. L'erreur la
     plus dangereuse est un **titre plausible mais fabrique colle sur un vrai
     papier** : il survit au sens (il decrit le bon sujet) et passe meme la Phase 4
     contextuelle. Ne jamais s'arreter a « le papier existe » → toujours passer a
     l'etape 3 et comparer le titre a la source.

3. **Cross-checker les metadonnees** avec la source trouvee :
   - **Titre** : **rapatrier le titre EXACT depuis la page editeur/DOI** (WebFetch
     sur le DOI, pas seulement le snippet WebSearch) et le **diff au champ `title`
     mot a mot**. Tolerer uniquement casse et diacritiques (gere par BibTeX). Un
     mot different, un sous-titre different ou paraphrase, un deux-points suivi
     d'un autre libelle = **titre FABRIQUE a corriger**, meme si auteurs/annee/
     journal sont exacts (cf. cas Meacock dans VERIFICATION_PROTOCOL.md). En cas
     de doute sur le titre, ne PAS poser `verified` : signaler INCERTAIN.
   - **Auteurs** : noms corrects et complets ? Ordre correct ?
   - **Annee** : correcte ? (attention preprint vs publication finale)
   - **Journal/conference** : nom correct et complet ?
   - **Volume/pages/DOI** : si presents, sont-ils corrects ? Ajouter `doi=` lors
     d'une correction, pour ancrer la tracabilite de la verification.

4. **Lire l'abstract** via WebFetch si une page du papier est accessible.
   Garder l'abstract en memoire pour la Phase 4.

5. **Decision et action** :

   | Situation | Action |
   |-----------|--------|
   | Tout correct | Ajouter `verified = {YYYY-MM-DD}` dans le .bib |
   | Metadonnees incorrectes | Corriger via Edit + ajouter `verified = {YYYY-MM-DD}` |
   | Papier introuvable (post-2000) | Ajouter `verified = {YYYY-MM-DD, status=suspect}` + flag prioritaire |
   | Papier introuvable (pre-2000) | Ajouter `verified = {YYYY-MM-DD, status=unverifiable}` + flag info |

   Le champ `verified` est ajoute **apres la derniere ligne de champ** de l'entree,
   avant l'accolade fermante `}`. Format :
   ```bibtex
   @article{key,
     author = {...},
     title  = {...},
     ...
     verified = {2026-04-04},
   }
   ```

6. **Progression** : afficher l'avancement tous les 10 entrees :
   ```
   Progression : 20/45 entrees verifiees (3 corrections, 1 suspect)
   ```

### Regles imperatives

- **Ne JAMAIS verifier deux fois la meme entree** : si `verified` est present, passer.
  **EXCEPTION : un signalement humain credible PRIME sur un `verified` existant.**
  `verified = {D}` signifie « verifie a la date D par la methode de l'epoque » : une
  passe ancienne a pu valider l'existence sans diff du titre. Si quelqu'un dit « cette
  reference semble fausse / introuvable », re-verifier l'entree integralement (titre
  inclus) meme marquee `verified`, puis remettre `verified` a la date du jour.
- **Ne JAMAIS inventer de corrections** : si incertain, signaler plutot que corriger
- **Utiliser WebSearch pour CHAQUE entree** : ne pas se fier a sa memoire pour
  confirmer l'existence d'un papier
- **Privilegier les sources primaires** : DOI, page editeur, arXiv, PubMed
- **Une correction se propage a TOUTES les copies du `.bib`** (paquet co-auteurs,
  dossier Overleaf, repo public). Apres correction : `grep -rn "<fragment errone>"`
  sur tout le depot, corriger chaque copie, puis recompiler chaque PDF (le titre vit
  dans le `.bbl`, pas le `.tex`) et verifier le `.bbl` regenere.

---

## Phase 4 -- Verification contextuelle des citations

Pour chaque `\cite{key}` (ou `\citep`, `\citet`, `\parencite`, `\textcite`,
`\autocite`, `\fullcite`, `\citeauthor`, `\citeyear`) dans le `.tex` :

1. **Extraire le contexte** : la phrase complete contenant la citation,
   plus la phrase precedente si necessaire pour comprendre le claim

2. **Identifier le claim** : qu'est-ce que l'auteur affirme en citant cette reference ?
   Exemples de claims :
   - "X a ete demontre par [ref]"
   - "La methode Y, proposee dans [ref], ..."
   - "Plusieurs etudes ont montre Z [ref1, ref2]"

3. **Comparer avec l'abstract/contenu** du papier reference (lu en Phase 3) :
   - Le claim est-il coherent avec ce que le papier traite reellement ?
   - Le papier supporte-t-il l'affirmation faite ?

4. **Signaler les decalages** :
   ```
   CITATION DOUTEUSE (L.142) :
     Claim : "La resistance a l'isoniazide est principalement causee par des mutations dans katG"
     Reference : @smith2020 — "Machine learning for drug resistance prediction in M. tuberculosis"
     Probleme : Le papier traite de prediction ML, pas des mecanismes de resistance
     Suggestion : Chercher une reference sur les mecanismes moleculaires de resistance a l'INH
   ```

5. **Ne PAS signaler** les cas triviaux ou la correspondance est evidente
   (ex: citation d'un outil avec le bon nom)

---

## Phase 5 -- Rapport final

Generer un rapport structure en markdown :

```markdown
# Rapport de verification bibliographique

**Article :** [titre extrait du \title{} du .tex]
**Date :** YYYY-MM-DD
**Fichier .bib :** [chemin]
**Entrees totales :** X | **Verifiees cette session :** Y | **Deja verifiees :** Z

---

## Problemes critiques

- [FABRIQUE] @key — Papier introuvable dans aucune source academique
  - Titre : "..."
  - Cite a : L.XX ("claim fait")
  - Action requise : trouver la vraie reference ou supprimer

- [METADONNEES] @key — [description de l'erreur]
  - Avant : ...
  - Apres (corrige) : ...

## Doublons detectes

- @key1 et @key2 → meme article
  - Recommandation : [fusion proposee]

## Citations contextuellement douteuses

- L.XX : "claim" cite @key — mais @key traite de [sujet different]
  - Suggestion : [reference alternative si identifiee]

## Entrees orphelines

- @key — present dans .bib mais jamais cite

## Citations manquantes

- \cite{key} utilise dans le .tex mais absent du .bib

---

## Resume

| Categorie | Nombre |
|-----------|--------|
| Verifiees OK | N |
| Metadonnees corrigees | N |
| Possiblement fabriquees | N |
| Non verifiables (pre-2000) | N |
| Doublons | N |
| Citations douteuses | N |
| Orphelines | N |
```

Afficher le rapport a l'utilisateur. Si des problemes critiques existent,
les mettre en evidence en premier.

---

## Consignes generales

### Ce que le skill DOIT faire
- Verifier **chaque** entree individuellement via une recherche en ligne
- Etre **conservateur** : signaler plutot que corriger en cas de doute
- Marquer les entrees verifiees pour permettre la reprise incrementale
- Lire le texte complet de l'article pour comprendre le contexte des citations
- Privilegier la precision : un faux positif (faussement signale comme suspect)
  est moins grave qu'un faux negatif (hallucination non detectee)

### Ce que le skill NE DOIT PAS faire
- Se fier a sa memoire pour confirmer l'existence d'un papier
- Verifier une entree deja marquee `verified`
- Corriger silencieusement sans signaler dans le rapport
- Ignorer les entrees orphelines ou les doublons
- Bacle la Phase 4 (verification contextuelle) : c'est la valeur principale


---

## Epilogue -- Resume et suggestion de suite

A la **fin de chaque invocation** (apres le rapport, le registre, ou la derniere
action du skill), ajouter systematiquement un bloc de cloture pour l'humain.

### Resume de session

Rappeler en 3-5 lignes :
- Ce qui vient d'etre fait dans cette invocation
- L'etat actuel du manuscrit (claims verifies, review en cours, references OK...)
- Les fichiers produits ou modifies

### Suggestion de prochaine etape

Evaluer l'etat global du manuscrit et proposer **la ou les commandes prioritaires**
parmi le pipeline de qualite :

| Commande | Quand la suggerer |
|----------|-------------------|
| `/claim-check` | Claims non verifies, article modifie depuis dernier run, ou jamais execute |
| `/bib-check` | References non verifiees, nouvelles refs ajoutees, ou jamais execute |
| `/deai-latex` | Article jamais nettoye IA, ou modifie substantiellement depuis |
| `/manuscript-review` | Article pret pour une evaluation globale, ou modifications majeures appliquees |
| `/lit-review [sujet]` | Un sujet necessite un approfondissement bibliographique |
| `/reviewer-response` | Une review existe non encore traitee, ou traitement en cours |
| `/reviewer-response next` | Remarques en attente dans la review active |

**Format de la suggestion** :

```
━━━━ Prochaine etape suggeree ━━━━

Le manuscrit a ete modifie par cette session. Je recommande :

  1. /claim-check --force    ← re-verifier les claims apres les modifications
  2. /bib-check              ← verifier les nouvelles references ajoutees

(ou /reviewer-response next s'il reste des remarques en attente)
```

Si a ton sens le travail est **termine** (toutes les reviews traitees, claims
verifies, bib OK, texte nettoye), le dire clairement :

```
━━━━ Etat du manuscrit ━━━━

Le manuscrit semble pret pour soumission/resoumission :
  ✅ Claims verifies (claim_check.md : 0 infirme)
  ✅ References verifiees (34/34, 0 suspecte)
  ✅ Review traitee (14/14 remarques resolues)
  ✅ Texte nettoye (deai-latex applique)

Aucune action supplementaire identifiee.
```
