---
name: literature-access
description: >-
  Maximise l'accès LÉGAL au plein texte scientifique en cascade, pour combler le trou entre « résumé »
  (tbmonitor, abstracts) et « article payant ». Deux moteurs : recall par le CORPS du texte (trouver
  les articles dont le corps mentionne un gène / locus tag / méthode, pas seulement le résumé, via
  europepmc_fulltext.py search) et résolution d'accès (donné un DOI, rendre la meilleure voie légale :
  Europe PMC OA lisible ici, Unpaywall green/gold OA, OpenAlex, Semantic Scholar, puis hand-off vers
  TDM institutionnel / bibliothèque sous licence / contact auteur). Ne contourne AUCUN paywall.
  Use when: un gène ressort « sans littérature » alors qu'il est cité dans des articles OA ; vérifier
  qu'un terme est réellement absent de la littérature ; obtenir le plein texte d'un DOI pour
  claim-check/bib-check/lit-review ; construire une revue à haut rappel.
argument-hint: "search \"<terme>\" [--oa --grep <motif>] | access <DOI> | <DOI> (raccourci access)"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebFetch
---

# /literature-access — Accès légal maximal au plein texte

## Le problème, en deux moitiés qui n'ont pas la même solution

L'accès à la littérature n'est pas un problème unique. Il s'en cache deux, et les confondre fait
qu'on paie (ou qu'on contourne) pour un accès dont on n'avait pas besoin.

1. **Rappel** : « ce gène / cette méthode existe-t-il dans la littérature, et où ? » — souvent un
   faux problème de paywall. Le terme est dans le CORPS d'articles déjà **open access**, mais on l'a
   cherché dans les RÉSUMÉS. Mesuré le 2026-08-11 : `esxV` = 124 articles en plein texte contre 19
   en résumé (×6,5) ; `Rv1363c` = 8 contre **0**. Solution entièrement gratuite et légale : chercher
   dans le plein texte.
2. **Récupération** : « je veux LIRE cet article précis, derrière un paywall. » Vrai problème
   d'accès, résolu par une cascade de voies légales dont la plupart sont gratuites (une version OA
   déposée existe souvent), et dont la dernière, la vraie équivalente légale du contournement, est le
   **droit de fouille de texte (TDM) inclus dans l'abonnement de l'université**.

> [!IMPORTANT]
> Ce skill ne contourne AUCUN paywall et n'appelle jamais Sci-Hub ni équivalent. Il maximise
> l'accès *légal*. Le geste sous licence (récupérer un PDF via l'abonnement de la bibliothèque) reste
> HUMAIN par défaut ; le skill le prépare et lit ce que l'humain dépose. Une automatisation existe
> pour la session institutionnelle elle-même (§ hand-off, point 1bis) mais reste un outil PERSONNEL
> invoqué explicitement à la demande, jamais un geste que ce skill déclenche de lui-même.

## Moteur 1 — Rappel par le corps du texte (`search`)

Réutilise `europepmc_fulltext.py` (partagé avec `lit-review`/`claim-check`/`bib-check`, une seule
copie réelle). **Avant de conclure qu'une entité est absente de la littérature, lancer un `search`
plein texte.**

```bash
S=${CLAUDE_PLUGIN_ROOT}/skills/lit-review/scripts/europepmc_fulltext.py
python3 $S search "esxV" --oa --since 2020 --sort cited        # articles dont le CORPS mentionne esxV
python3 $S search "Rv1363c AND tuberculosis" --grep "Rv1363c"  # + phrases exactes de mention
```

`search` affiche l'écart résumé/plein texte (rend le manque visible), liste titre/année/DOI/PMCID +
drapeau OA, et `--grep` extrait du plein texte OA les phrases contenant le motif. Options :
`--oa` (ne garder que le plein texte récupérable), `--since/--until` (années), `--limit`,
`--sort {relevance,cited,date}`, `--grep-max`. Puis, sur un article ciblé, `resolve` / `sections` /
`fulltext --section --grep` (mêmes conventions que documenté dans `lit-review` §2.2b).

## Moteur 2 — Résolution d'accès légal (`access`)

Donné un DOI, rend une liste ORDONNÉE de voies légales, du plus direct (lisible ici) au substitut.

```bash
A=${CLAUDE_PLUGIN_ROOT}/skills/literature-access/scripts/access_cascade.py
python3 $A 10.1016/S0140-6736(15)00151-8     # un Lancet "payant" -> copie PMC OA légale
python3 $A 10.1038/s41467-024-45058-9 --json
```

Cascade (rang = priorité), stdlib seule, aucune clé, cache `~/.cache/litaccess/` :

| rang | source | ce qu'elle donne | lisible ici ? |
|---|---|---|---|
| 1 | `europepmc_oa` | plein texte JATS grep-able via `europepmc_fulltext.py` | **oui** |
| 2 | `hal` | dépôt HAL *green* OA (souvent le manuscrit auteur ; très fourni pour FEMTO-ST/uFC) + PDF | non, URL |
| 2 | `unpaywall` | meilleure localisation OA légale (manuscrit auteur *green*, ou *gold*) + URL PDF | non, URL |
| 3 | `openalex` | statut OA + `oa_url` (recoupe/complète Unpaywall) | non, URL |
| 4 | `semanticscholar` | `openAccessPdf` + **TLDR** (résumé généré = SUBSTITUT, pas une preuve) | non |
| 0 | (aucune) | émet le HAND-OFF hors-OA ci-dessous | — |

> [!NOTE]
> **HAL (`api.archives-ouvertes.fr`) est un levier institutionnel gratuit et légal**, souvent le
> manuscrit auteur lui-même. Particulièrement pertinent ici : les travaux FEMTO-ST / uFC y sont
> largement déposés (vérifié : la « M. africanum Lineage 10 » du groupe y est, PDF direct). API
> publique documentée, sans clé.

> [!NOTE]
> **Unpaywall est le plus gros levier gratuit.** Beaucoup d'articles « payants » chez l'éditeur ont
> un **manuscrit auteur** légalement déposé ailleurs (PMC author manuscript, dépôt institutionnel).
> Vérifié : le Lancet `10.1016/S0140-6736(15)00151-8` ressort avec sa copie PMC OA. Ne jamais
> conclure « payant, inaccessible » sans avoir passé `access`.
> E-mail de politesse (exigé par Unpaywall/OpenAlex) : `$UNPAYWALL_EMAIL`, défaut = adresse UMLP.

## Le hand-off hors-OA — la cascade légale, dans l'ordre

Quand `access` ne trouve aucune voie OA (rang 0), l'accès légal existe encore, par ordre de coût :

1. **Résolveur de la BU (Ariane / Primo VE)**, geste HUMAIN sous licence. La bibliothèque de
   l'Université Marie et Louis Pasteur tourne sur **Ex Libris Primo VE / Alma**, institution
   **`33UFC_INST`**, vue **`33UFC_INST:33UFC_testNDE`** (codes vérifiés le 2026-08-31 ; PAS
   `33UBFC_INST`/`...:openview`, qui n'existent plus et rendent respectivement un 404 direct et une
   attente infinie sur le spinner Primo). Lien OpenURL à ouvrir dans un navigateur AUTHENTIFIÉ (il
   pointe la copie sous licence de l'abonnement) :
   ```
   https://ariane.umlp.fr/discovery/openurl?institution=33UFC_INST&vid=33UFC_INST:33UFC_testNDE&rft.doi=<DOI>
   ```
   Le login empêche l'automatisation propre (l'API `pnxs` de Primo exige un jeton d'invité, semi-
   officiel et fragile — ne pas la scraper). C'est donc un geste humain : l'utilisateur suit le
   lien, récupère le PDF sous licence, et le dépose dans le dossier d'ingestion (ci-dessous).
   **Limite constatée** : un DOI seul peut ne pas suffire à Primo pour peupler un lien direct (notice
   pauvre, type générique, seule option « Contacter votre bibliothèque ») même sur un titre bien
   couvert par l'abonnement ; ajouter `rft.jtitle=`/`rft.issn=`/`rft.volume=`/`rft.spage=` améliore
   probablement la résolution, non vérifié à ce jour. Catalogue de découverte : `https://ariane.umlp.fr`.
   Archive ouverte institutionnelle : HAL-uFC (déjà couverte par la voie `hal` du moteur 2, automatisée).
1bis. **Session EZproxy/Shibboleth scriptée (outil personnel, dernier recours explicite)** —
   variante automatisée du point 1, construite et validée le 2026-08-26. La BU UMLP route l'accès
   distant via EZproxy (`scd1.univ-fcomte.fr`) adossé à une fédération Shibboleth
   (`idp1.univ-fcomte.fr`) et un portail LemonLDAP::NG (`auth.univ-fcomte.fr/cas`). Le script
   `~/.config/umlp-ent/ezproxy_fetch.py` (hors dépôt, personnel, jamais poussé sur un dépôt partagé)
   rejoue cette chaîne : `python3 ~/.config/umlp-ent/ezproxy_fetch.py "<url_ressource>"
   ~/.config/umlp-ent/user ~/.config/umlp-ent/password <fichier_sortie>`. Trois règles
   non négociables, actées avec l'utilisateur avant construction :
   - **un article à la fois, à la demande** — ne JAMAIS boucler ce script sur une liste de DOI/URL.
     Les CGU d'EZproxy et des éditeurs (Elsevier en tête) interdisent le téléchargement
     automatisé/systématique ; un usage en boucle expose la plage IP de TOUT l'établissement à un
     blocage éditeur, pas seulement le compte de l'auteur ;
   - **dernier recours**, seulement après échec de la cascade OA (moteur 2, points 3-4 ci-dessous
     compris) — ce n'est pas un raccourci pour éviter Unpaywall/Europe PMC ;
   - **ne jamais lire le fichier d'identifiants** (`~/.config/umlp-ent/{user,password}`, chmod 600,
     hors de tout dépôt git) avec `Read` ni l'un ni l'autre : seul le script les lit, via leur
     chemin, jamais leur valeur ne doit apparaître dans une commande, un log ou un registre.
2. **TDM institutionnel** — la vraie équivalente légale du contournement. Elsevier (`insttoken`),
   Springer Nature, Wiley exposent des API de *text and data mining* qui rendent le plein texte des
   articles couverts par l'abonnement, programmatiquement. Le droit TDM est généralement DÉJÀ inclus
   dans l'abonnement de l'université ; il manque une clé API, à demander au **pôle numérique du SCD
   (`pole-numerique-scd@univ-fcomte.fr`)** — ce n'est pas un MCP. **Si une clé est configurée**
   (variable d'env `ELSEVIER_INSTTOKEN` / `SPRINGER_API_KEY`), c'est la voie à privilégier pour un
   accès automatisable et large. Sans clé : ce niveau est documentaire, pas actionnable — le
   signaler, ne pas prétendre y accéder.
3. **Preprint** — bioRxiv / medRxiv / arXiv portent souvent une version identique sur le fond, en
   accès libre et légal. Chercher par titre ou par le DOI preprint (`10.1101/...`).
4. **Contact auteur** — l'auteur correspondant a le droit d'envoyer son propre article. Voie lente
   mais fiable entre chercheurs d'un même domaine.

## Le dernier kilomètre — dossier d'ingestion de PDF licenciés

Pour l'article qu'aucune couche automatisable ne rend, la division du travail propre est : **toi,
authentifié et sous licence, tu récupères le PDF ; le skill le lit et l'analyse.** Convention :
déposer les PDF dans `<projet>/litterature_review/pdf_licencies/` (ou un dossier nommé par
l'utilisateur). Les lire ensuite via `/read-scientific-pdf` (OCR Mistral inclus si scanné). Le fetch
licencié est TON geste ; l'analyse est celui du skill. Aucun PDF d'éditeur n'est téléchargé
automatiquement par ce skill.

## Ordre d'emploi recommandé

1. Question de rappel (« ce gène est-il documenté ? ») → `search` plein texte AVANT toute conclusion
   d'absence.
2. Article ciblé à lire → `access <DOI>` : si rang 1, lire par `europepmc_fulltext.py fulltext` ; si
   rang 2-3, suivre l'URL OA (WebFetch autorisé, ou humain) ; si rang 4 seul, le TLDR est un indice,
   pas une preuve ; si rang 0, appliquer le hand-off.
3. Journaliser la voie retenue (source + URL) là où la preuve est consignée
   (`claim_check.md` / registre `bib-check`), comme pour Europe PMC.

## Intégration avec l'écosystème

- **`lit-review` / `claim-check` / `bib-check`** : consommateurs directs. `search` sert leur rappel
  (ne plus déclarer « absent de la littérature » sur la foi des résumés) ; `access` leur donne le
  plein texte à citer. Le script `europepmc_fulltext.py` est partagé (une copie, deux symlinks).
- **`tbmonitor-papers`** : reste la porte d'entrée du RECENSEMENT (indexe aussi le non-OA en résumé,
  ~330 k abstracts) ; `literature-access` sert le RAPPEL par le corps et la RÉCUPÉRATION.
- **`sra-geolocate`** : partage l'usage d'Unpaywall (déjà câblé à son niveau 5 pour dater/localiser
  un SRA via son article) ; ici Unpaywall sert l'accès au plein texte, usage distinct.
- **`read-scientific-pdf`** : lit les PDF du dossier d'ingestion (dernier kilomètre) et les URL OA
  téléchargées.
- **`europe-pmc`** : frontière explicite (les deux partagent `europepmc_fulltext.py`). `europe-pmc`
  = les fonctions PROPRES de l'API Europe PMC (annotations text-mining, graphe de citations, liens
  d'accession ENA/UniProt/PDB, découverte de preprints sur 32+ serveurs). `literature-access` = la
  CASCADE d'accès légal multi-source (HAL/Unpaywall/OpenAlex/S2/TDM/BU) + le RAPPEL par le corps.
  Ne pas déclencher `literature-access` pour explorer les annotations d'un article : c'est
  `europe-pmc`. `pubmed-database` = API PubMed brute (E-utilities), pour le non-TB ou un niveau plus bas.
- **`bioc-pmc` / `pubtator`** : corpus plein texte en masse (format BioC) et annotations NER
  pré-calculées, pour du text-mining à grande échelle — hors périmètre de la récupération ciblée
  d'un article que fait `literature-access`.

## Limites, à garder honnêtes

- Couverture de `fulltext` (lecture) = open access seulement (35 264 articles TB en OA mesurés) ;
  `search` (recherche) indexe le corps plus largement mais un hit non-OA n'est pas lisible ici.
- Le TLDR de Semantic Scholar est un résumé GÉNÉRÉ : un indice de pertinence, jamais une source
  citable ni une preuve pour un claim.
- Ne jamais deviner un PMCID (l'API Europe PMC rend `200` avec un AUTRE article si le PMCID est
  faux) : partir du DOI, `europepmc_fulltext.py` recoupe déjà.
- Le TDM institutionnel est légal MAIS soumis aux CGU de l'éditeur (débit, usage non commercial) :
  respecter les quotas, ne pas re-diffuser les plein textes récupérés.
- La session EZproxy/Shibboleth scriptée (point 1bis) est un accès légitime (l'abonnement de
  l'utilisateur), mais un usage RÉPÉTÉ ou EN BOUCLE ressemble à un robot aux yeux de l'éditeur et
  risque un blocage IP côté établissement : rester strictement à l'article demandé, un par un.
