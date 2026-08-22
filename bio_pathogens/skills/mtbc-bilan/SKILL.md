---
name: mtbc-bilan
description: >-
  Bilan consolidé d'un projet MTBC : ce qui est su, comment ça a été établi,
  ce qui reste à faire (Markdown, PDF, slides). `--deepen` ajoute revue de
  littérature élargie, inventaire des méthodes non mobilisées, verdict
  CLORE / APPROFONDIR / PIVOTER. `--full` : comparatif de tous les projets.

  Use when: faire le point, préparer une réunion, décider la suite, juger si un
  projet peut être clos, relancer un projet qui stagne, repartir après une pause.
argument-hint: "[chemin-projet] [--deepen] [--full]"
allowed-tools: Bash, Read, Write, Grep, Glob, WebSearch, WebFetch
user-invocable: true
---

# /mtbc-bilan -- Etat actuel des connaissances et plan d'action

Parcourt un projet MTBC (ou tout le dossier `mtbc/`) pour produire un bilan
**consolide, pedagogue et tourne vers l'action** : lit la memoire projet
(CLAUDE.md, cahier de labo, article, litterature, analyses, BDD), agrege les
connaissances acquises en consolidant les entrees successives, explique
comment chacune a ete etablie, liste ce qui reste a faire d'apres les
intentions memorisees dans le cahier. Le mode `--deepen` prolonge par une
exploration : litterature elargie, methodes non mobilisees, verdict
CLORE / APPROFONDIR / PIVOTER.

**Principe cardinal : l'etat consolide prime sur le narratif** -- pas un
journal des sessions, l'image stabilisee de ce qui est su au moment ou le
bilan est ecrit. **Honnetete** : moins de trois pistes haute priorite →
sortie courte et assumee, jamais de remplissage ; si l'etude est arrivee a
son terme, le dire franchement sans proposer d'analyses gadget. **"Rien de
plus a faire" est un resultat valide et souhaitable.**

> [!IMPORTANT]
> **Taxonomie VIVANTE -- recompter les effectifs a chaque bilan.**
> `bdd/actuelle/` se deplace en continu (souches reclassees, sous-lignees creees
> ou scindees entre deux sessions, parfois par une session concurrente). Ne
> JAMAIS reutiliser les comptages ni les noms de sous-lignees d'un bilan ancien
> ou d'un manuscrit : RECOMPTER via `bdd/actuelle/` +
> `global_supplementary/barcoding_v2/barcode_complete.tsv`. Cas vecu :
> `L4.1_proto` (18 souches en avril 2026) videe puis scindee en `L4.1_proto1`
> (49) + `L4.1_proto2` (24) au 10 juin 2026 -- un chiffre recopie aurait ete faux.

> [!NOTE]
> **Frontiere bilan / reboot.** `mtbc-bilan` PHOTOGRAPHIE l'etat su (lecture
> seule) et, sous `--deepen`, EXPLORE de nouvelles pistes quand un projet stagne.
> `mtbc-reboot` REPART a zero quand la derive est trop forte : archive taggee
> VERIFIE / A VERIFIER / REFUTE + re-analyse claim par claim, **operation
> destructrice**. Ne pas rebooter ce qu'un `--deepen` suffirait a traiter.

## Fichiers de reference (a lire a la demande)

Ce SKILL.md porte le deroule operationnel ; catalogues, gabarits et syntaxes
verbeuses sont dans `references/`, a lire **au moment ou on en a besoin**
(chemins relatifs a ce repertoire de skill).

| Besoin | Fichier |
|--------|---------|
| Style : criteres complets, formules interdites | `references/ton_et_style.md` |
| Phases 1 / 1bis integrales, sept niveaux, heuristiques | `references/consolidation.md` |
| Sources de verite taxonomiques | `references/sources_de_verite.md` |
| Notions a expliciter, categories A-F (4.6) | `references/notions_pedagogiques.md` |
| Skills par domaine (7.3 et D2) | `references/skills_par_domaine.md` |
| Gabarit integral du bilan a ecrire (9.1) | `references/template_bilan.md` |
| Encadres : syntaxe LaTeX, exemples (9.1bis) | `references/encadres_latex.md` |
| Figures : `geo-map`, patterns TikZ (9.1ter) | `references/figures_et_visuels.md` |
| Squelette des slides Beamer (9.4) | `references/beamer_slides.md` |
| Affichage console, formats detailles (9.5) | `references/epilogue_console.md` |
| Mode `--full` : procedure, template global | `references/mode_full.md` |
| Mode `--deepen` : rubrique, gabarit du rapport | `references/deepen.md` |
| Douze points de vigilance, texte complet | `references/points_de_vigilance.md` |

Templates de compilation, a ne pas modifier : `templates/bilan.latex` (PDF
pandoc), `templates/bilan_slides.tex` (Beamer Metropolis).

## Ton et style (resume)

Le bilan est un **etat consolide des connaissances**, pas un inventaire
comptable ni un journal de bord : **narratif, en prose continue** (chiffres,
methodes et niveaux de consolidation integres dans la phrase, listes a puces
reservees aux annexes) ; **organise par theme** ; **pedagogue et argumente** ;
**trace** (une connaissance sans methode d'acquisition est suspecte) ;
**ancre dans la litterature** ; **tourne vers l'action** ; **autonome**
(jamais de renvoi a un bilan precedent, jamais un changelog) ; **adapte au
lecteur** (Christophe Guyeux, math pures + info : tout concept de biologie,
genetique des populations, ethno-linguistique, epidemiologie ou statistiques
passe par un encadre) ; **visuel** (4-10 figures). **Avant de rediger, lire
`references/ton_et_style.md`.**

## Prealable

1. Consulter `mtbc-lineages` pour la golden law (hierarchie Guyeux, biais de
   reference H37Rv) ; s'il est indisponible, degrader gracieusement.

   > **Sources de verite -- liste et effectifs des lignees** (cf.
   > `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`) : l'autorite est
   > **`bdd/actuelle/`** (les repertoires de souches font foi), avec
   > **`barcoding_v2/barcode_complete.tsv`** comme registre derive. La "golden
   > law" `lignees.py` et, dans TBannotator, `system_name='guyeux' (ex-'Senelle')` (bien le systeme
   > maison) sont des **snapshots** possiblement en retard sur la taxonomie
   > vivante : ne pas les lire comme source des effectifs, et recouper tout clade
   > recent du cycle multi-signal (L1.\*, Bovis1.\*, BCG.\*, L6 profond) avec
   > `bdd/actuelle/` + `barcode_complete.tsv`. `snp_barcoding.csv` (v1 obsolete)
   > et `strain_lineages.csv` (perime) ne sont **jamais** des references
   > taxonomiques. Integral : `references/sources_de_verite.md`.

2. Consulter `~/.claude/knowledge/tuberculosis.md` s'il existe.
3. Lire `codes/mtbc/CLAUDE.md` (conventions globales du depot ; l'inventaire des
   repertoires, la structure standard d'un projet et la description de `bdd/`
   sont dans `codes/mtbc/README.md` depuis le 2026-08-09).

## Declenchement

```
/mtbc-bilan                    # Projet du repertoire courant
/mtbc-bilan L4.9               # Projet specifique (nom relatif a codes/mtbc/, ou chemin)
/mtbc-bilan L4.9 --deepen      # Bilan + exploration + verdict CLORE/APPROFONDIR/PIVOTER
/mtbc-bilan --full             # Comparatif de TOUS les projets mtbc/
```

`--deepen` ajoute les phases D1 a D5 entre la Phase 7 et la Phase 8 et
produit `bilans/YYYY-MM-DD_deepen.md` ; `--full` fait un scan multi-projets.
**Les deux sont incompatibles** : le deepen est par projet.

**Livrables obligatoires** dans `<projet>/bilans/` : `YYYY-MM-DD_bilan.md`,
`YYYY-MM-DD_bilan.pdf` (**toujours genere, meme passe**),
`YYYY-MM-DD_bilan_slides.pdf`, plus `YYYY-MM-DD_deepen.md` si `--deepen`. Le
mode `--full` produit Markdown + PDF seulement. Livrer le `.md` sans son
`.pdf` est une livraison incomplete.

**Mode standalone (defaut et unique)** : les bilans anterieurs de
`<projet>/bilans/` sont **ignores** (pas de lecture, pas de citation, pas de
"delta", pas de "depuis le bilan v2") ; le nouveau est ecrit de zero en
consolidant cahier et litterature, comme si c'etait le premier. Les anciens
sont conserves comme archives datees, jamais ecrases (suffixe `_v2`, `_v3`
si collision de date). **Exception `--deepen`** : un rapport de moins de
7 jours peut etre relu pour eviter de refaire l'inventaire des methodes,
sans dispenser de reecrire le bilan.

Profondeur : **lecture seule + inspection legere**, aucun calcul lourd,
aucun appel a TBannotator, aucune analyse lancee -- le skill **suggere**, il
**n'execute pas**. **Non destructif** : seules ecritures autorisees, les
fichiers bilan et le repertoire `bilans/`.

---

## Phase 0 -- Resolution et sanity-check

1. Resoudre le chemin : `--full` → `MTBC_ROOT=/home/christophe/docs/codes/mtbc`
   et passer au mode full ; sinon argument absolu tel quel, ou nom relatif
   prefixe par `$MTBC_ROOT/` ; sinon `pwd`. Normaliser via `realpath`.
2. Verifier l'existence du repertoire ; sinon, abandon propre avec message.
3. Sanity-check : compter les presences parmi `CLAUDE.md`,
   `cahier_de_labo.md`, `JOURNAL.md`, `analyses/`, `article/`. Moins de 2 →
   "Ce repertoire ne ressemble pas a un projet MTBC. Trouve : <liste>.
   Abandon." et terminer.
4. Afficher le contexte : projet, lignee, chemin, entrees du cahier et date
   de la derniere, statut de l'article.

## Phase 1 -- Lecture du cahier et consolidation

Consolider **l'etat actuel des connaissances**, pas reconstituer l'histoire
iterative. Lire **en partant des entrees les plus recentes** et en
remontant : on n'ajoute un element anterieur que s'il n'a pas ete recouvert
ou contredit ensuite.

**Sources autorisees** : `CLAUDE.md` (integral) ; le cahier
(`cahier_de_labo.md`, fallback `JOURNAL.md`) lu **en entier** en ordre
inverse ; `article/` (manuscrit, `claim_check.md`, `review/INDEX.md`,
`litterature_review/`) ; `analyses/`, `resultats/`, `data/` (inspection
legere) ; `~/.claude/knowledge/tuberculosis.md` ; skill `mtbc-lineages`.
**Source INTERDITE** : tout fichier de `<projet>/bilans/`, ni lu ni resume
ni cite ; seul `ls` est autorise, pour detecter une collision de nom.

1. `Read CLAUDE.md` integralement : titre, lignee, conventions, question
   scientifique fondatrice.
2. Localiser le journal ; si `cahier_de_labo.md` et `JOURNAL.md` coexistent,
   lire les deux et signaler l'incoherence en anomalie.
3. **Lire le cahier INTEGRALEMENT, en ordre inverse.** Au-dela de 5000
   lignes, chunks de 2000 en partant de la fin, **jamais tronquer
   silencieusement** ; ne pas se contenter de greper les headers.
4. **Consolider au fil de la lecture**, deux structures :
   - **A. Carte des connaissances**, thematique : le fait ; comment il a ete
     etabli (script, methode, donnees, reference) ; son niveau de
     consolidation (Phase 1bis) ; pour tout fait non `etabli`, l'amplitude
     de variation ou la source de fragilite et une piste de consolidation.
   - **B. Intentions non honorees** : toute chose a faire, verifier ou
     explorer qui n'apparait nulle part ensuite comme realisee (`### Pistes
     futures`, "il faudrait", "a verifier", "TODO", hypothese non testee,
     donnee mentionnee non integree, reference suggeree non incorporee).
   - **Conflit** : si le 15/04 dit "57 SNP retro-mutes" et le 22/04 "apres
     correction, 38 confirmes", garder **38** ; jamais les deux comme deux
     resultats independants.
5. Noter aussi : mecanismes biologiques invoques recemment ; echecs
   instructifs non resolus ensuite ; indices de statut
   (`Grep -i "submitted\|accepted\|published\|en preparation\|bouclee"`) ;
   4-8 jalons dates pour le narratif court (tournants reels seulement).

**Separation bookkeeping / redaction** : "fait + methode + niveau +
amplitude + piste" est un format **interne**, qui **ne doit jamais
apparaitre tel quel** dans le bilan ; tout est **re-rendu en prose** a la
redaction. **Texte integral : `references/consolidation.md`.**

## Phase 1bis -- Niveau de consolidation

Chaque fait recoit l'un des **sept niveaux**, enonce textuellement dans le
bilan : `etabli` (reproduit par >= 2 methodes ou >= 2 executions
independantes), `convergent` (analyses concordantes sans reproduction
formelle), `unique` (une seule analyse, sensibilite non testee), `volatile`
(la valeur exacte change avec la methode ou les donnees, le pattern
qualitatif pouvant rester), `fragile` (depend d'une hypothese forte non
testee), `hypothetique` (hypothese issue des resultats du projet, pas encore
testee), `speculatif` (venu de la litterature ou d'une analogie, aucun test
sur les donnees du projet).

`etabli` exige **deux** sources de validation ; `volatile` des qu'un
changement de methode deplace le resultat de plus de 15-20 % en relatif ou
de plus que l'IC95 nominal ; entre `volatile` et `fragile`, prendre le plus
pessimiste. Tout fait `volatile` ou `fragile` precise imperativement
**l'amplitude de variation observee** (ou l'hypothese qui pourrait casser)
**et une piste de consolidation**, ajoutee a "A faire maintenant" si elle
etait deja evoquee dans le cahier, sinon a "Pistes d'approfondissement",
avec renvoi explicite ; les faits centraux non `etabli` recoivent en plus un
encadre `fragilite`. **Regles d'attribution, exemples chiffres et
heuristiques de detection : `references/consolidation.md`.**

## Phase 2 -- Inventaire des donnees et scripts

1. `Glob analyses/phase*_*.py` : compter par phase, detecter les gaps (phase
   3 sans phase 4 → trou suspect), lister chaque script en une ligne.
2. `Glob resultats/**/*.pdf`, `.png`, `.svg`, `.csv`, `.tsv` : compter
   figures et tables, lister les fichiers cles.
3. `Glob data/*.{csv,tsv,fasta,nwk,txt}` : donnees brutes presentes.
4. BDD centrale : determiner la lignee, verifier
   `<projet>/../../bdd/actuelle/<lignee>/`, compter les sous-repertoires
   (= souches) via `ls | wc -l`. Absente → anomalie, ne pas bloquer.

## Phase 3 -- Etat du manuscrit

Si `article/` existe : `Read article/main.tex` limit 300 puis
`Grep ^\\section{` sur le fichier entier (sections redigees) ;
`article/claim_check.md` (claims totaux, verifies, infirmes, a verifier) ;
`article/review/INDEX.md` (reviews et statut) ; `Glob article/figures/*` ;
indice de statut (`submitted.md`, mention "submitted"/"accepted" dans un
commit recent ou le cahier). Sinon : "Manuscrit = non initialise".

## Phase 4 -- Exploitation approfondie de la litterature

Cadre interpretatif des decouvertes ; alimente "Etat des connaissances avant
ce projet" et "Paysage de la litterature".

**4.1 Inventaire.** `Glob litterature_review/*.md` ;
`Read litterature_review/index.md` ;
`Grep -c ^@ litterature_review/references.bib` ; lire aussi `article/*.bib`,
qui contient souvent des refs citees dans le manuscrit mais absentes de la
lit-review. Toute recherche bibliographique interroge **en priorite
`tbmonitor-papers`** (corpus PubMed TB pre-indexe, ~190k papiers, reponse
sub-seconde) avant les sources externes.

**4.2 Syntheses.** Lire **chaque** fiche integralement (pas juste les
lacunes) et construire un **mapping decouvertes ↔ litterature** : quels
articles confirment, contredisent ou sont coherents avec chaque decouverte ;
comble-t-elle une lacune identifiee ; est-elle completement nouvelle ?

**4.3 Mise en perspective** (coeur de la phase) : **situer** chaque
decouverte (deja observee ailleurs, sur d'autres lignees, avec d'autres
methodes ?), **evaluer son originalite**, **identifier les mecanismes**
proposes par la litterature (ou noter la lacune), **detecter les
contradictions** avec des resultats publies -- potentiellement l'element le
plus interessant du bilan.

**4.4 Angles morts.** Sujets bien couverts que le projet n'a pas abordes ;
resultats sans fiche correspondante (lacune de la lit-review) ; lacunes que
le projet pourrait combler avec ses donnees.

**4.5 Pas de `litterature_review/`.** Lire `article/*.bib`, reperer les
articles les plus cites dans le cahier, signaler l'absence comme **lacune
majeure** et la proposer en piste haute priorite.

**4.6 Notions a expliciter.** Le lecteur principal, de formation
mathematiques pures + informatique de base, trouve **a priori opaques** la
biologie evolutive, la genetique des populations, l'ethno-linguistique,
l'epidemiologie et les statistiques inferentielles. **Mieux vaut un encadre
superflu qu'une notion laissee dans l'ombre.** Avant la redaction, lister
les notions du projet meritant un encadre en parcourant les six categories
du catalogue (anthropologie et ethno-linguistique ; biologie et genetique
des populations ; phylogenetique et evolution moleculaire ; statistiques
inferentielles ; outils et formats du domaine ; concepts MTBC et
tuberculose). **Catalogue detaille :
`references/notions_pedagogiques.md` -- le parcourir a ce moment precis.**
**Cible : 10 a 25 encadres** (5-12 `notion`, 3-6 `methode`, 1-5
`originalite`, 3-6 `remarquable`, 1-5 `fragilite`) ; 2-3 encadres signalent
une phase 4.6 baclee, au-dela de 35 il faut fusionner ou elaguer.

## Phase 5 -- Intentions memorisees + nouvelles pistes

**5.A "A faire maintenant".** Repartir de la **liste B** de la Phase 1 :
verifier qu'aucune entree posterieure ne decrit l'intention comme realisee,
puis classer en `a_faire`, `partiellement_fait`, `close` (sortir de la
liste) ou `obsolete`. Pour les deux premiers, noter **l'entree d'origine**
(date, formulation exacte si courte), **pourquoi c'etait prevu** et **ce qui
manque concretement** pour l'executer. Section **factuelle et tracee** :
chaque item renvoie a une entree precise du cahier.

**5.B Deduplication et nouvelles pistes.** Reunir les `a_faire` +
`partiellement_fait` et les pistes ouvertes anciennes non traitees ;
dedupliquer par similarite semantique ; ajouter les pistes **deduites** des
inventaires (Phases 2-4) et de la litterature. Marquer chaque piste
`memorisee` (cahier, tracee a une date), `deduite_inventaire` ou
`deduite_litterature`. Toutes passent en Phase 7 mais alimentent **deux
sections distinctes** du bilan : "A faire maintenant" pour les memorisees,
"Pistes d'approfondissement" pour les deduites.

## Phase 6 -- Convergences inter-projets (leger en mode normal)

`ls /home/christophe/docs/codes/mtbc/`, puis pour chaque voisin pertinent
`Read CLAUDE.md` limit 20 → titre + objectif. Identifier lignees
apparentees (methodologie commune), projets transversaux couvrant deja la
question, donnees partageables (BDD commune, outgroup commun). Centrale en
mode `--full`.

## Phase 7 -- Hierarchisation argumentee par impact

**7.1 Argumentaire.** **Avant de scorer**, ecrire 4-8 phrases par piste :
quelle question scientifique elle adresse ; pourquoi c'est interessant dans
CE projet ; ce que dit la litterature et s'il y a une lacune a combler ;
quelle methode et quel resultat attendre ; ce que ca changerait pour les
conclusions. Repris tel quel dans "Pistes d'approfondissement" ; une piste
sans argumentaire convaincant est probablement basse priorite.

**7.2 Scoring (mode normal, trois dimensions).** Scorer 0 a 3 sur **valeur
scientifique**, **faisabilite** (donnees, outils, complexite) et **cout**
(temps et calcul ; un cout eleve **divise** le score) :
`score = valeur * faisabilite / cout`, arrondi au dixieme. **Haute** >= 2,
**moyenne** 1-2, **basse** < 1.

> En mode `--deepen`, cette grille est **remplacee** par celle a cinq
> dimensions de la phase D3, qui ajoute soutien litteraire, originalite et
> synergie -- dimensions que seules les phases D1 et D2 permettent de
> renseigner honnetement. Hors `--deepen`, la grille a trois dimensions
> reste la bonne.

**7.3 Association aux skills.** Associer a chaque piste un ou plusieurs
skills de `bio_pathogens` / `bio_population_genetics` (`/raxml`,
`/iqtree-lsd2`, `/molecular-clock`, `/bayesian-skyline`, `/pastml`,
`/lineage-subdivision`, `/convergent-evolution`, `/coevolution`,
`/mk-ascertainment`, `/lineage-comparison`, `/resistance-profiler`,
`/phylogeography`, `/tb-cli`, `/lit-review`, `/claim-check`,
`/manuscript-review`...). **Catalogue complet par domaine :
`references/skills_par_domaine.md`.** Si aucun skill ne convient pour une
piste haute priorite, suggerer la creation d'un nouveau skill. **Ne PAS
gonfler la liste.**

---

## Mode `--deepen` -- exploration avant verdict

**N'executer que si `--deepen` est passe en argument** ; s'intercale entre
la Phase 7 et la Phase 8. Ne jamais inventer de pistes pour justifier la
poursuite d'un projet epuise.

**D1 -- Litterature elargie.** Executer l'equivalent de
`/lit-review <sujet> --wide`, en s'appuyant en priorite sur
`tbmonitor-papers`. Le **sujet** se derive du titre du projet, de la lignee
et des termes recurrents du cahier, formule comme une **requete de
recherche** et non comme un titre de projet ("L4.9" → "Mycobacterium
tuberculosis lineage 4.9 phylogeography evolution"). On cherche les
**articles recents** depuis la derniere lit-review, les **travaux
precurseurs** via la recherche pre-nomenclature de `--wide` (ceux qui
decrivaient le phenomene avant qu'il soit nomme), le **backward chaining**
sur les references des articles fondateurs, et les **convergences** avec
d'autres lignees ou approches. `litterature_review/` presente → mode
approfondissement (enrichir, pas repartir de zero) ; absente → mode
creation ; `--wide` force dans les deux cas. **Budget : une seule session**,
sinon proposer l'approfondissement comme piste. Afficher : sujet, mode,
nouvelles refs, precurseurs, backward scan, lacunes.

**D2 -- Methodes non mobilisees.** Confronter les capacites analytiques
disponibles a ce qui a ete fait, pour identifier les **angles morts
methodologiques**.

```bash
ls "${CLAUDE_PLUGIN_ROOT}/../bio_pathogens/skills/" "${CLAUDE_PLUGIN_ROOT}/../bio_population_genetics/skills/"
```

Classifier chaque skill par domaine **d'apres sa description, pas son nom**
(neuf domaines dans `references/skills_par_domaine.md`). Pour chaque skill
**d'analyse** (exclure manuscrit et BDD, qui sont des outils et non des
methodes) : lire le frontmatter, chercher des traces d'usage dans le cahier,
les scripts et les resultats, puis classer en **utilise**, **pertinent non
utilise** (applicable aux donnees du projet mais jamais lance) ou **non
pertinent** (ex : `bovine-genomics` pour un projet L4 humain). Pour chaque
"pertinent non utilise" : **ce qu'il apporterait**, **ce qu'il faudrait**
(donnees, prerequis), **l'effort** (rapide < 1 h, modere 1-4 h, lourd
> 4 h). Afficher le decompte des trois categories, puis les methodes non
exploitees avec leurs prerequis.

**D3 -- Croisement et scoring a cinq dimensions.** Croiser pistes du bilan
(Phases 5 et 7), lacunes de la litterature (D1) et methodes non exploitees
(D2) : une piste qui correspond a une lacune ET peut etre adressee par un
skill disponible est **forte** ; une piste isolee (ni support litteraire, ni
methode) est **faible**. Rescorer **toutes** les pistes de 0 a 3 sur cinq
dimensions -- **valeur scientifique** (0 anecdotique → 3 potentiellement
majeur), **soutien litteraire** (0 aucun precedent → 3 lacune identifiee
dans la litterature), **faisabilite technique** (0 donnees absentes → 3 pret
a lancer), **originalite** (0 deja fait ailleurs → 3 premiere etude a le
faire), **synergie** (0 isole → 3 transforme les conclusions) :

`score = (valeur×3 + soutien×2 + faisabilite×2 + originalite×2 + synergie×1) / 10`

**Haute** >= 2.0 ; **moyenne** 1.0-2.0 ; **basse** < 1.0. Chaque piste garde
la trace de sa **source** (bilan, litterature, inventaire, convergence).
**Rubrique detaillee : `references/deepen.md`.**

**D4 -- Verdict.** **CLORE** si au moins 3 conditions sont vraies : verdict
bouclee au bilan (>= 4/7 criteres) ; aucune lacune litteraire exploitable
avec les donnees existantes ; aucune piste au-dessus de 1.5 ; article soumis
/ accepte / publie ; toutes les methodes pertinentes deja explorees.
**PIVOTER** si le projet est a un stade precoce (< 3 phases d'analyse), OU
si la litterature revele que la question initiale est mal posee ou deja
resolue, OU si une piste completement differente emerge avec un score tres
superieur. **APPROFONDIR** sinon, en precisant les pistes haute priorite par
score et, pour chacune, la commande exacte, les prerequis et le resultat
attendu. Ce verdict **prime** sur le verdict binaire de la Phase 8, qu'il
englobe (CLORE = "bouclee" ; APPROFONDIR et PIVOTER = "a poursuivre") ;
appliquer quand meme les sept criteres pour produire le compte X/7.

**D5 -- Rapport.** Ecrire `<projet>/bilans/YYYY-MM-DD_deepen.md` en plus des
trois livrables : verdict justifie en 2-3 phrases ; bilan resume (10 lignes
max) ; litterature (tableau des articles nouveaux, precurseurs retrouves
avec l'explication de leur invisibilite par recherche standard, lacunes) ;
tableau des methodes non exploitees (skill, apport, prerequis, effort) ;
pistes par priorite avec le detail des cinq scores ; plan d'action sequence ;
convergences inter-projets. **Gabarit complet : `references/deepen.md`.**

**Vigilance propre au mode** : ne pas inventer de pistes ; tracer chaque
piste a sa source ; suggerer sans executer ; scorer honnetement (faisabilite
3 implique donnees presentes et script existant ou trivial) ; signaler quand
un article a ete retrouve grace au mode wide et pourquoi il etait invisible
par mots-cles ; pas de `--full` en mode deepen.

---

## Phase 8 -- Verdict

Sept criteres de cloture ; au moins **5/7** pour "bouclee", **et le critere
7 doit etre satisfait**.

1. **Article** soumis/accepte/publie **OU** `claim_check.md` a 0 infirme et
   100 % verifies.
2. **Pistes** toutes `close` ou `abandonnee` (aucune `open`).
3. **Reviews** de `review/INDEX.md` toutes traitees (ou aucune attendue).
4. **Litterature** : lacunes couvertes **OU** pas de nouvelle direction
   depuis > 60 jours.
5. **Analyses** : aucune phase inachevee, aucun script en erreur, aucun
   resultat partiel.
6. **Activite** : derniere entree cahier > 90 jours ET conclusion positive
   (pas de "bloque", pas de "a reprendre").
7. **Consolidation** (**bloquant**) : aucun fait central `volatile`,
   `fragile` ou `hypothetique` sans documentation explicite des hypotheses
   et de l'amplitude dans le manuscrit ; tous les chiffres cites sont
   `etabli` ou `convergent`, ou bien la fragilite est discutee en
   "Limitations".

**Si bouclee** : le declarer en tete du bilan, ne PAS proposer d'analyses,
se contenter d'une breve section "Pour archivage". **Sinon** : lister les
criteres manquants puis les pistes hierarchisees. Si seul le critere 7
manque : **"Projet quasi-boucle, mais les faits suivants restent fragiles --
consolidation requise avant cloture serieuse."**

### Phase 8bis -- Verdict de PERIMETRE (en plus du verdict de cloture)

Les sept criteres ci-dessus disent si le projet est FINI. Ils ne disent pas s'il
est encore le BON CONTENANT. Deux projets sur lesquels ce skill a ete lance
peuvent etre "non boucles" pour des raisons opposees : il reste du travail dans
le cadre, ou le cadre lui-meme a cesse de correspondre a ce qui est su.

Lancer :

```bash
python3 ~/.claude/skills/recadrage/recadrage_signals.py <projet>
```

et reporter dans le bilan, en une sous-section courte :

- **acquis hors article** : combien d'acquis de `etat_des_decouvertes.md` §2
  portent une destination B (second papier) ou C (essaimage), et combien n'ont
  AUCUNE destination -- un acquis non tague est un acquis qui se perdra a la
  cloture ;
- **signaux de scission** atteints (sur les 5 criteres de `/recadrage` Phase 4) ;
- **anciennete du dernier recadrage**.

Puis ajouter au verdict, a cote de CLORE / APPROFONDIR / PIVOTER, deux issues
que la grille de cloture ne sait pas produire :

- **ESSAIMER** : le projet est sain et son article tient, mais il porte des
  acquis qui n'y entreront jamais. Ils doivent partir vers le `pistes.md` du
  repertoire parent avant la cloture, sans quoi ils meurent avec le projet.
- **SCINDER** : >= 3 criteres sur 5 atteints. Le projet contient deux articles
  qui s'empechent mutuellement.

Dans les deux cas, ne pas executer le geste ici (ce skill est en lecture seule) :
le nommer, le chiffrer, et renvoyer vers `/recadrage`.

---

## Phase 9 -- Redaction et persistance

Trois formats **tous obligatoires** : Markdown (source editable), PDF
(pandoc + xelatex, `templates/bilan.latex`), Beamer (`.tex` + `.pdf`,
`templates/bilan_slides.tex`). **Un bilan n'est pas livre tant que les trois
fichiers ne sont pas presents.** En cas d'echec de compilation : signaler
l'erreur, conserver le Markdown, donner la commande exacte de relance.

### 9.1 Ecriture du Markdown

1. `mkdir -p <projet>/bilans/`, fichier `YYYY-MM-DD_bilan.md` (suffixe
   `_v2`, `_v3` si collision de date).
2. **YAML frontmatter obligatoire**, qui alimente la page de titre du PDF :

   ```yaml
   ---
   title: "Bilan projet — <nom>"
   subtitle: "<sous-titre descriptif : theme principal du projet>"
   project: "<nom court>"
   lineage: "<lignee MTBC>"
   date: "YYYY-MM-DD"
   verdict: "<Bouclée | À poursuivre | À pivoter>"
   ---
   ```

3. **Ecrire les quinze sections dans l'ordre canonique, de "Identite" a
   "Plan d'action pour la prochaine session", avec pour colonne vertebrale
   "Etat actuel des connaissances acquises" et, en valeur pratique, "A faire
   maintenant". Le gabarit integral -- ordre exact, consignes de redaction,
   tableaux attendus, diagramme TikZ du pipeline, exemples narratifs par
   niveau de consolidation -- est dans `references/template_bilan.md` : le
   lire avant d'ecrire.**
4. Titres : `##` pour les sections, `###` pour les sous-sections ; pas de
   `#` dans le corps (reserve au titre genere par le frontmatter).
5. **Relecture** : narratif et pedagogue ? au moins un paragraphe de prose
   par section ? decouvertes reliees a la litterature ? Si le bilan
   ressemble a une liste d'items, le reecrire.
6. **Check d'autonomie** ; tout resultat impose de reecrire le passage en
   prose autonome :

   ```bash
   grep -niE 'bilan (precedent|anterieur|v[0-9])|comme deja|comme indique|comme vu|depuis (le|la) derniere?|delta par rapport|changelog|version (precedente|anterieure)|voir bilan|cf\.\s*bilan|rien de neuf' bilans/YYYY-MM-DD_bilan.md
   ```

7. **Inserer les encadres pedagogiques** identifies en Phase 4.6.

### 9.1bis Encadres pedagogiques

Cinq types : **`notion`** (concept de domaine), **`methode`** (technique
statistique ou algorithmique), **`originalite`** (ce que le resultat apporte
**par rapport a la litterature**), **`remarquable`** (pourquoi il est
frappant **dans l'absolu**), **`fragilite`** (pourquoi un fait
`volatile`/`fragile` n'est pas citable tel quel ; **obligatoire** pour tout
fait central non `etabli`). `originalite` et `remarquable` sont distincts :
quand les deux s'appliquent, mettre **les deux encadres**. Insertion **au
fil du texte** a la premiere occurrence du concept, **une seule fois par
concept**, 4-12 phrases (3-5 lignes sur les slides). **Syntaxe LaTeX,
exemples longs et regles d'insertion : `references/encadres_latex.md`.**

### 9.1ter Cartes, schemas et figures

Piocher dans `article/figures/` (accessible par simple nom de fichier grace
au `\graphicspath` du template) **et** generer des visuels de novo.
**Cible : 4 a 10 visuels, dont au moins 2 generes specifiquement** ; si le
projet a une dimension geographique, **au moins une carte via `geo-map`**
est obligatoire. TikZ pour les points purement pedagogiques (mecanisme,
chronologie, position dans l'arbre MTBC) ; `geo-map` pour les cartes,
`seaborn` pour les distributions, `create-viz` pour les visualisations
composites, `itol` / `iqtree-lsd2` pour les arbres. **Ne jamais reinventer
en TikZ ce qu'un skill d'illustration produit en qualite publication.**
Caption explicative de 3-5 lignes, figure referencee dans le texte.
**Patterns TikZ et regles de qualite : `references/figures_et_visuels.md`.**

### 9.2 Generation du PDF (obligatoire dans la meme passe)

```bash
TEMPLATE=${CLAUDE_PLUGIN_ROOT}/skills/mtbc-bilan/templates/bilan.latex

pandoc "<projet>/bilans/YYYY-MM-DD_bilan.md" -o "<projet>/bilans/YYYY-MM-DD_bilan.pdf" --template="$TEMPLATE" --pdf-engine=xelatex --shift-heading-level-by=-1 --variable=colorlinks:true
```

`--shift-heading-level-by=-1` fait des `##` des `\section{}`. **En cas
d'echec** : conserver le Markdown, capturer l'erreur, corriger les causes
frequentes (unicode non supporte par la police, `\` ou `$` mal echappes,
chemin de figure introuvable), relancer si la correction est triviale ;
sinon afficher l'erreur exacte et la commande pandoc complete. Ne **jamais**
declarer le bilan livre quand le PDF manque.

### 9.3 Mode `--full`

Meme procedure pour le bilan global, frontmatter adapte, sortie dans
`mtbc/bilans_globaux/`. **Detail : `references/mode_full.md`.**

### 9.4 Presentation Beamer

Ecrire `<projet>/bilans/YYYY-MM-DD_bilan_slides.tex` (Beamer natif, pas un
Markdown converti) ; le template Metropolis fournit preambule, theme et
commandes MTBC (`\mtb`, `\spdi`, `\lignee`, `\kb`). Ce n'est **pas une
version comprimee du bilan** mais une visite guidee en **quatre actes** :
contexte (3-4 slides), donnees et methode (2-3), resultats (4-8, un par
decouverte majeure), synthese et perspectives (3-4). **Total 12-20 slides**,
un message par slide, titres specifiques ("28 marqueurs SNP exclusifs au
proto-L4.2", pas "Resultats phylogenetiques"), max 6 bullets de 10 mots,
keybox de take-away sur chaque slide de resultat. **Squelette complet et dix
regles de redaction : `references/beamer_slides.md`.**

```bash
cd "<projet>/bilans/" && pdflatex -interaction=nonstopmode YYYY-MM-DD_bilan_slides.tex && pdflatex -interaction=nonstopmode YYYY-MM-DD_bilan_slides.tex
```

Deux passes pour la table des matieres ; verifier que
`grep -c "^!" YYYY-MM-DD_bilan_slides.log` vaut 0. Si la compilation echoue,
signaler l'erreur et produire le `.tex` quand meme, sans bloquer le bilan.
Pas de slides en `--full`.

### 9.5 Affichage console

Resume oriente action : identite du projet, verdict argumente, etat
consolide des connaissances en 3-5 phrases, faits volatils ou fragiles a
surveiller, top 3 des intentions memorisees non honorees, top 3 des pistes
prospectives justifiees, connexion litterature. **Terminer par le bilan des
fichiers livres, avec leur taille** :

```
Fichiers generes :
  Markdown  : <projet>/bilans/YYYY-MM-DD_bilan.md         (<taille>)  [OK]
  PDF       : <projet>/bilans/YYYY-MM-DD_bilan.pdf        (<taille>)  [OK | ECHEC]
  Beamer    : <projet>/bilans/YYYY-MM-DD_bilan_slides.pdf (<taille>)  [OK | ECHEC]
  Deepen    : <projet>/bilans/YYYY-MM-DD_deepen.md        (<taille>)  [si --deepen]
```

Une ligne `[ECHEC]` est suivie de la commande exacte de relance ; **ne
jamais omettre une ligne**. **Format detaille :
`references/epilogue_console.md`.**

---

## Mode `--full` -- Bilan comparatif de tous les projets

1. `ls /home/christophe/docs/codes/mtbc/`, puis filtrer : **inclure** les
   repertoires contenant `CLAUDE.md` ET (`article/` OU `analyses/` OU
   `cahier_de_labo.md` OU `JOURNAL.md`) ; **exclure** `bdd/`,
   `investigate_phylo/`, `global_supplementary/`, `bilans_globaux/`,
   `.git/` et les fichiers isoles.
2. Pour chaque projet retenu, version **allegee** des Phases 1 a 5 : cahier
   (entrees, derniere date, pistes ouvertes), manuscrit (presence, part de
   claims verifies), verdict mini sur les 7 criteres.
3. Agreger : tableau comparatif, priorites cross-projets, convergences
   possibles, projets prets a clore, projets dormants (> 180 jours sans
   activite et non boucles), top 10 des pistes haute priorite.
4. Ecrire dans
   `/home/christophe/docs/codes/mtbc/bilans_globaux/YYYY-MM-DD_bilan_global.md`
   (creer le repertoire si absent, suffixer `_v2` si collision) et compiler
   le PDF. **Template complet : `references/mode_full.md`.**

## Points de vigilance

1. **Cahier volumineux** : chunks de 2000 lignes si > 5000, **jamais
   tronquer**.
2. **Collision de fichier** : suffixer `_v2`, `_v3`, **jamais ecraser**.
   Seules ecritures autorisees : les fichiers bilan et `bilans/`.
3. **Honnetete** : moins de 3 pistes haute priorite → sortie courte assumee.
   Mais "court" ne veut pas dire "sec" : meme un bilan qui conclut "rien a
   faire" doit etre narratif et pedagogue dans sa justification.
4. **Degradation gracieuse** : `mtbc-lineages` absent, BDD absente ou
   deplacee, double format de cahier → anomalie signalee, jamais d'echec.
5. **Biais de reference H37Rv** : rappel automatique dans "Limites" si des
   analyses SNP sont presentes (golden law MTBC).
6. **Pistes deduites** : distinguer celles qui viennent du cahier (citer la
   date) de celles deduites de l'inventaire.

**Douze points en formulation complete (normalisation par `realpath`, faux
positifs du `--full`, projets imbriques) :
`references/points_de_vigilance.md`.**

## Epilogue

Afficher le resume de la section 9.5, puis suggerer les suites :
`/cahier-de-labo update` si le bilan a revele une production de connaissance
nouvelle ; le skill de la premiere piste haute priorite ;
`/mtbc-bilan <projet> --deepen` si le bilan seul ne tranche pas ou si le
projet stagne ; `/mtbc-bilan --full` pour remettre en perspective globale.
Apres un verdict `--deepen` CLORE : `/claim-check`, `/bib-check`,
`/deai-latex`, `/manuscript-review`, puis archivage. Apres un PIVOTER :
documenter l'abandon de la direction initiale, reformuler la question, puis
`/lit-review "<nouveau sujet>" --wide`.
