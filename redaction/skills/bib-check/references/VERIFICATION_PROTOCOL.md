# Protocole de verification des references

Guide detaille pour la Phase 3 (verification en ligne) du skill bib-check.

## AVERTISSEMENT — le decoupage des entrees est le point de defaillance le plus dangereux

Les trois scripts partagent une regex `ENTRY` qui decoupe le `.bib` en entrees. **Quand elle rate
une entree, elle ne leve aucune erreur : elle rend simplement un compte plus faible et un verdict
rassurant.** C'est le pire mode de defaillance possible pour un outil anti-hallucination, et il
s'est produit deux fois, chaque correctif revelant le suivant.

1. **2026-08-12, `.bib` a une entree par ligne.** La regex exigeait `\n\}` en fin d'entree, ce qui
   suppose un fichier multi-lignes. Sur un fichier ou chaque entree tient sur une seule ligne et se
   termine par `}}`, les trois scripts rendaient **« 0 entree, 0 probleme »** au lieu d'echouer
   bruyamment. Corrige en `\}\s*(?=\n\s*@|\Z)`.
2. **2026-08-12, meme jour, revele par le correctif precedent : lignes de commentaire `%`.** Le
   lookahead `(?=\n\s*@)` exige qu'une entree soit suivie d'un `@`. Une ligne de commentaire `%`
   intercalee (sectionnement thematique, parfaitement legal, ignore par LaTeX) casse cette
   condition : la partie non gourmande `(.*?)` poursuit jusqu'a l'accolade fermante suivante et
   **absorbe la premiere entree de la section suivante**. Mesure sur un fichier de 164 entrees
   sectionne par un seul commentaire : le script en voyait 163, l'entree manquante etant la
   premiere d'apres le commentaire, tandis que le champ `author` extrait restait celui de l'entree
   precedente (la fonction `field` s'arretant a la premiere occurrence), donc **aucun symptome
   visible**. Un fichier decoupe en cinq sections perdrait cinq entrees en silence. Premiere version
   du correctif : `\}\s*(?=\n\s*(?:%[^\n]*\n\s*)*@|\Z)`.
3. **2026-08-12, meme jour, angle mort du correctif 2 : commentaire `%` APRES la derniere entree,
   avec ou sans retour a la ligne final.** Le correctif 2 exigeait `\n\s*(?:%[^\n]*\n\s*)*@|\Z` :
   si la derniere entree est suivie d'un commentaire puis de la fin de fichier, ni la branche `@`
   (aucune entree ne suit) ni la branche `\Z` (le commentaire s'interpose) ne peuvent etre
   atteintes, et la derniere entree du fichier est perdue en silence, exactement le meme mode de
   defaillance que le correctif 2 visait a eliminer entre deux entrees. Regex finale, qui rend le
   `\n` final de chaque ligne de commentaire optionnel (couvre aussi le cas ou le fichier ne se
   termine pas par un retour a la ligne) : `\}\s*(?=\s*(?:%[^\n]*(?:\n\s*)?)*(?:@|\Z))`.

**Reflexe a acquerir : toujours comparer le nombre d'entrees vu par le script au nombre reel**
(`grep -c '^@' fichier.bib`). Un ecart, meme de 1, est un defaut d'outil, jamais un detail. Ne
jamais conclure d'un rapport « 0 probleme » sans avoir verifie que le script a bien vu toutes les
entrees.

> **Etat au 2026-08-12 (apres-midi) — correctif final teste et valide.** Six controles executes
> (script `test_bibcheck_regex.py`, methode dans le cahier de labo de `yersinia_pestis_grands_lacs`) :
> (a) `.bib` a une entree par ligne AVEC une ligne `%` intercalee : 2/2 entrees vues (aucune perte) ;
> (b) non-regression sur le meme fichier sans la ligne de commentaire : 2/2 ;
> (c) non-regression sur un `.bib` classique multi-lignes, entree precedee d'un `%` : 2/2 ;
> (d) plusieurs lignes `%` consecutives : 2/2 ;
> (e) commentaire `%` APRES la derniere entree, fichier se terminant par un retour a la ligne :
> corrige, 2/2 (le correctif 2 seul rendait 1/2, la derniere entree perdue) ;
> (f) meme cas (e) mais SANS retour a la ligne final apres le commentaire : corrige, 2/2 (le
> correctif 2 rendait aussi 1/2 dans ce cas, non teste a l'epoque).
> Sur le fichier reel `yersinia_pestis_grands_lacs/litterature_review/references.bib` (166 entrees,
> un commentaire `%` intercale en son sein), le compte de la regex correspond exactement au compte
> reel (`grep -c '^@article'`), avant et apres le correctif final : aucune regression, correction
> confirmee sur un cas de production. Applique aux trois scripts (`crossref_verify.py`,
> `author_format.py`, `doi_coherence.py`).

## Strategie de recherche par type d'entree

### @article
1. Rechercher : `"titre exact" journal annee`
2. Source primaire : page DOI de l'editeur
3. Sources secondaires : PubMed, Semantic Scholar, Google Scholar
4. Verifier : auteurs, titre, journal, volume, pages, annee, DOI

### @inproceedings / @conference
1. Rechercher : `"titre exact" conference annee`
2. Source primaire : proceedings de la conference (IEEE, ACM, Springer)
3. Attention : le titre de la conference (`booktitle`) varie souvent entre
   forme longue et abregee — les deux sont acceptables
4. Verifier : auteurs, titre, booktitle, annee, pages

### @book
1. Rechercher : `"titre" auteur editeur`
2. Source primaire : catalogue editeur, WorldCat, Google Books
3. Verifier : auteurs/editeurs, titre, editeur, annee, edition, ISBN

### @phdthesis / @mastersthesis
1. Rechercher : `"titre" auteur universite`
2. Source primaire : depot institutionnel de l'universite (HAL, theses.fr, ProQuest)
3. Plus difficile a verifier — tolerer un niveau d'incertitude plus eleve

### @misc / @techreport / @online
1. Rechercher : titre + auteur/organisation
2. Verifier que l'URL (si presente) est encore accessible
3. Pour les preprints arXiv : verifier l'ID arXiv

## Regles de comparaison des metadonnees

### Auteurs
- **Formats acceptables** : "Nom, Prenom" ou "Prenom Nom" — ne pas signaler
  un changement de format comme une erreur
- **Initiales vs prenom complet** : tolerer (ex: "J. Smith" = "John Smith")
- **Erreur reelle** : nom different, auteur manquant dans la liste, ordre radicalement
  different (sauf si les conventions du domaine varient)
- **Accents** : tolerer les variantes (ex: "Muller" vs "Mueller" vs "Muller")

### Titre

**Le titre est le champ le plus souvent fabrique et le plus dangereux. Il se verifie
par un diff mot a mot contre la source faisant autorite (page editeur / DOI), pas par
une lecture approximative ni au snippet WebSearch.** Confirmer que le papier existe
(bons auteurs + annee + journal) NE valide PAS le titre.

- **Tolerable** (ne pas signaler) : differences de casse (BibTeX gere via accolades),
  diacritiques, et **troncature honnete** d'un sous-titre (le champ `title` est un
  vrai PREFIXE exact du titre reel, ex. titre principal sans `: sous-titre`).
- **ERREUR REELLE a corriger** : un mot different, un titre paraphrase/reformule, et
  surtout **un sous-titre DIFFERENT de celui de la source** (pas une troncature mais
  un autre libelle apres le deux-points). Ces cas sont des fabrications meme si tout
  le reste de l'entree (auteurs, annee, journal, volume, pages, DOI) est exact.
- **Reflexe** : ouvrir la page DOI/editeur (WebFetch), copier le titre exact, le
  comparer caractere par caractere. En cas de doute, ne pas poser `verified`.

> **Cas de reference (angle mort attrape par un humain, juin 2026).** Entree
> `meacock2017weekend` deja marquee `verified` : auteurs (Meacock, Anselmi, Kristensen,
> Doran, Sutton), journal (J. Health Serv. Res. Policy), annee (2017), volume/pages
> (22(1):12-19) et DOI tous EXACTS, mais titre FABRIQUE : « ...admitted *on weekends:
> the contribution of admission rates and severity* » au lieu du vrai « ...admitted
> *to hospital at weekends reflect a lower probability of admission* ». Le faux titre
> etait plausible (il decrivait le bon sujet), survivait au sens, et passait la Phase 4
> contextuelle. Seul un diff du titre a la source l'aurait attrape. Lecon : la marque
> `verified` ne protege pas d'un titre faux si la passe initiale n'a verifie que
> l'existence ; toujours diff le titre, et re-verifier sur signalement humain.

### Annee
- **Preprint vs publication** : un decalage de 1-2 ans entre la version preprint
  (arXiv) et la publication finale est frequent — signaler comme INFO, pas comme erreur
- **Erreur reelle** : decalage de 3+ ans, ou annee manifestement fausse

### Journal / Conference
- **Abreviations** : tolerer (ex: "J. Mol. Biol." = "Journal of Molecular Biology")
- **Erreur reelle** : journal/conference completement different
- **Quirk CrossRef confirme (2026-08-12, DOI prefixe `10.4269`, American Journal of
  Tropical Medicine and Hygiene / ASTMH)** : le champ `container-title` retourne par
  l'API CrossRef pour ces DOI n'est PAS le nom du journal mais celui de la SOCIETE
  editrice (« The American Society of Tropical Medicine and Hygiene »), verifie sur
  la reponse brute de l'API. `crossref_verify.py` le signalera donc en `DIFF` alors
  que le `.bib` (« The American Journal of Tropical Medicine and Hygiene ») est
  correct — ne pas corriger, l'erreur est cote CrossRef. Meme categorie de tolerance
  pour les variantes historiques de nom d'un meme journal (PNAS avec/sans suffixe
  "of the United States of America", "Microbiology" vs "Microbiology (Reading)",
  point vs deux-points dans un sous-titre de revue) : ce sont des formes
  d'enregistrement differentes du meme journal, pas des erreurs.

## Niveaux de confiance

| Niveau | Signification | Action |
|--------|---------------|--------|
| **CONFIRME** | Papier trouve, toutes metadonnees correctes | `verified = {YYYY-MM-DD}` |
| **CORRIGE** | Papier trouve, metadonnees ajustees | Corriger + `verified = {YYYY-MM-DD}` |
| **SUSPECT** | Papier introuvable apres recherche approfondie (post-2000) | `verified = {YYYY-MM-DD, status=suspect}` |
| **NON VERIFIABLE** | Papier ancien ou source rare, introuvable en ligne | `verified = {YYYY-MM-DD, status=unverifiable}` |
| **INCERTAIN** | Resultat ambigu, plusieurs papiers similaires | Signaler a l'utilisateur, ne pas marquer verified |

## Detection de doublons : criteres

Deux entrees sont considerees comme doublons si :
- Leurs titres ont une similarite > 90% (apres normalisation : lowercase, suppression
  ponctuation et accolades)
- OU meme DOI
- OU memes premiers auteurs + meme annee + meme journal

En cas de doublon :
1. Conserver l'entree la plus complete (plus de champs remplis)
2. Recommander de remplacer les `\cite{}` de l'entree supprimee
3. Ne pas supprimer automatiquement — laisser l'utilisateur decider

## Verification contextuelle : guide

### Claims typiques et comment les verifier

| Type de claim | Exemple | Verification |
|---------------|---------|--------------|
| Attribution de methode | "La methode X, proposee par [ref]" | Le papier propose-t-il bien cette methode ? |
| Resultat factuel | "Il a ete montre que X [ref]" | L'abstract/conclusion du papier mentionne-t-il X ? |
| Citation de fond | "X est un probleme important [ref1, ref2]" | Les refs traitent-elles du meme domaine ? (tolerance large) |
| Donnees chiffrees | "Le taux est de 42% [ref]" | Le chiffre 42% apparait-il dans le papier ? |

### Tolerance selon le type de citation

- **Citation de fond / contexte general** : tolerance large. Il suffit que la reference
  traite du meme domaine general
- **Attribution directe** : tolerance nulle. Si on dit "X a propose Y", X doit avoir
  propose Y dans ce papier precis
- **Chiffre precis** : tolerance nulle. Le chiffre doit etre verifiable dans la source
- **Affirmation scientifique** : tolerance moderee. Le papier doit supporter l'affirmation,
  meme si la formulation differe

### Signaux d'alerte

- Le papier cite traite d'un sujet completement different
- L'auteur cite un papier de 2020 pour une decouverte faite en 1990
  (la reference originale serait plus appropriee)
- Un papier de methodo est cite pour un resultat empirique (ou vice versa)
- Une affirmation forte ("X est prouve") citant un papier qui dit "X est suggere"
