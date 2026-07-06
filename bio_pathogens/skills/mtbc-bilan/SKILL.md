---
name: mtbc-bilan
description: >-
  Bilan complet et honnete d'un projet MTBC : etat actuel consolide des
  connaissances acquises, et plan d'action pour la suite. Le bilan ne
  raconte PAS le cheminement iteratif -- il consolide ce qui est
  actuellement su, comment cela a ete etabli, et ce qui reste a faire
  d'apres ce qui a deja ete memorise dans le cahier. En cas de
  conflit entre une ancienne et une nouvelle entree du cahier, on garde
  la derniere version consolidee. Pour la phase litterature, interroger
  en priorite tbmonitor-papers (corpus PubMed TB pre-indexe ~190k papiers,
  sub-seconde) avant les sources externes. Mode --full pour un bilan
  comparatif de tous les projets MTBC.

  Use when: faire le point sur un projet, decider quoi faire ensuite,
  preparer une reunion, arbitrer entre plusieurs projets, evaluer si un
  projet est pret a etre clos, repartir d'une etude apres une pause.
argument-hint: "[chemin-projet | --full]"
allowed-tools: Bash, Read, Write, Grep, Glob
user-invocable: true
---

# /mtbc-bilan -- Etat actuel des connaissances et plan d'action

Parcourt un projet MTBC (ou l'ensemble du dossier `mtbc/`) pour produire un
bilan scientifique **consolide, pedagogue, et tourne vers l'action**. Le
skill lit la memoire projet (CLAUDE.md, cahier_de_labo.md, article,
litterature, analyses, BDD), **agrege l'ensemble des connaissances
actuellement acquises** (en consolidant les entrees successives, en gardant
la derniere version d'un fait en cas de conflit), explique comment chaque
connaissance a ete etablie, et liste ce qui reste a faire d'apres les
intentions memorisees dans le cahier. Si l'etude est arrivee a son terme,
le skill le dit franchement sans proposer d'analyses gadget.

**Principe cardinal : l'etat consolide prime sur le narratif.** Le bilan
n'est pas un journal des sessions ; c'est l'image stabilisee de ce qui est
su au moment ou il est ecrit. Un bref apercu chronologique reste autorise,
mais resume.

**Corollaire d'honnetete** : si moins de trois pistes a haute priorite
emergent du parcours, la sortie doit etre courte et assumee -- jamais de
remplissage artificiel.

> [!IMPORTANT]
> **Taxonomie VIVANTE -- recompter les effectifs a chaque bilan.** `bdd/actuelle/` se
> deplace en continu (souches reclassees, sous-lignees creees ou scindees entre deux
> sessions, parfois par une session concurrente). Ne JAMAIS reutiliser les comptages ni
> les noms de sous-lignees d'un bilan ancien ou d'un manuscrit : RECOMPTER au moment du
> bilan via `bdd/actuelle/` + `global_supplementary/barcoding_v2/barcode_complete.tsv`.
> Cas vecu : `L4.1_proto` (18 souches en avril 2026) videe puis scindee en `L4.1_proto1`
> (49) + `L4.1_proto2` (24) au 10 juin 2026 -- un chiffre recopie aurait ete faux.

## Ton et style (principes-cles)

Le bilan n'est **pas un inventaire comptable**, ni un journal de bord ; c'est
un **etat consolide des connaissances** du projet, accompagne d'un plan
d'action, qui aide le chercheur a prendre du recul et a savoir quoi faire
ensuite.

### Ce que le bilan doit etre

- **Narratif et continu** : le bilan se lit comme un texte scientifique
  reflechi, **en prose continue**, pas comme une fiche technique ni un
  rapport d'inventaire. Chaque section centrale (etat des connaissances,
  decouvertes majeures, paysage de la litterature) est composee de
  **paragraphes argumentes** qui s'enchainent : le lecteur doit pouvoir
  parcourir 3-5 paragraphes pour saisir un theme entier sans rencontrer
  de liste a puces, de tableau, ni de bloc structure "Fait / Methode /
  Consolidation". Les chiffres, methodes, et niveaux de consolidation
  s'integrent **dans la phrase** ("Le sous-clade proto-L4.2, identifie
  sur 412 souches reparties dans 23 pays via `phase3_subclade_marker.py`,
  est aujourd'hui consolide comme `etabli` apres deux reproductions
  independantes a un mois d'intervalle"). Les listes a puces sont
  reservees aux annexes (inventaire de scripts, faits a faire,
  references), pas au coeur du recit.
- **Consolide, pas chronologique** : la colonne vertebrale est *ce qui est
  su aujourd'hui*, organise par theme. Le cheminement iteratif n'apparait
  que dans une section "Apercu chronologique" courte (4-8 phrases).
  Quand deux entrees du cahier disent des choses differentes du meme fait,
  on garde la **derniere version**, eventuellement en notant en une phrase
  l'evolution si elle est instructive.
- **Pedagogue** : expliquer *pourquoi* un resultat est marquant, pas juste
  *qu'il* existe. "La decouverte de 57 marqueurs inverses dans L4.9 est
  remarquable car elle remet en question le postulat d'irreversibilite des
  SNP chez MTBC, un principe fondateur du barcode de Coll et al. (2014)."
- **Argumente, pas affirme** : chaque resultat est presente avec son
  contexte (ce que la litterature disait avant), sa portee (ce qu'il
  change dans la connaissance du domaine), et ses limites (consolidation
  partielle, hypotheses non testees). Une affirmation seche ("Le MRCA est
  de 1240 CE.") n'a pas sa place ; sa formulation narrative est
  obligatoire ("La datation moleculaire LSD2 place le MRCA de proto-L4.2
  vers 1240 CE, ce qui le situe **avant** les premiers contacts coloniaux
  europeens-americains -- un resultat contre-intuitif pour une sous-lignee
  initialement decrite en Europe occidentale. La valeur reste neanmoins
  `volatile` : BEAST tip-dating donne 1110 CE, et la datation par
  calibration fossile remonte a 1340 CE. Le pattern qualitatif est stable,
  mais le chiffre exact necessite une horloge moleculaire relaxee pour
  etre cite sans reserve.").
- **Trace de la maniere d'acquerir** : pour chaque connaissance consolidee,
  rappeler en une phrase comment elle a ete etablie (script, methode,
  donnees, reference). Une connaissance sans methode d'acquisition est une
  affirmation suspecte.
- **Ancre dans la litterature** : chaque decouverte majeure est mise en
  perspective avec ce que la litterature dit (ou ne dit pas) sur le sujet.
  Citer les references de `litterature_review/references.bib` quand elles
  existent, mentionner les lacunes quand rien n'a ete publie.
- **Interpretatif** : ne pas juste rapporter les faits mais les interpreter.
  Que signifie biologiquement tel resultat ? Quel mecanisme pourrait
  l'expliquer ? Quelles hypotheses soutient-il ou refute-t-il ?
- **Tourne vers l'action** : une section "A faire maintenant" recense
  explicitement les choses memorisees dans le cahier qui n'ont pas ete
  faites (analyses planifiees, verifications evoquees, hypotheses non
  testees, donnees mentionnees mais non integrees...). C'est la **valeur
  pratique** du bilan : ne pas laisser de fil pendant inapercu.
- **Autonome (standalone, sans heritage)** : chaque bilan est un
  document **complet en soi**. Il **n'evoque jamais** un bilan
  precedent et ne presuppose **jamais** qu'un lecteur ait deja vu une
  version anterieure. Un lecteur decouvrant le projet pour la
  premiere fois doit pouvoir tout comprendre. **Aucune des formules
  suivantes n'est admissible** : "comme dans le bilan precedent",
  "le bilan v2 reste valable", "depuis la derniere session de
  bilan", "rien de neuf cote X", "voir bilan du JJ/MM pour les
  details", "delta par rapport a v3", "synthese des changements".
  Si une connaissance reste vraie, on la **reformule entierement** ;
  on ne renvoie pas a sa version anterieure. Le bilan n'est pas un
  changelog, c'est un **etat des lieux exhaustif a date**.
- **Exhaustif sur le fond** : ne rien laisser de cote. Lire TOUT le cahier,
  TOUTE la litterature disponible, TOUS les resultats. Un bilan superficiel
  qui survole est inutile.
- **Pedagogiquement adapte au lecteur** : le destinataire principal est
  Christophe Guyeux, formation math pures + info de base. Tout concept de
  biologie evolutive, genetique des populations, ethno-linguistique,
  epidemiologie ou statistique inferentielle doit etre explique via des
  **encadres pedagogiques** (`notion`, `methode`, `originalite`,
  `remarquable`) inseres au fil du texte. Voir Phase 4.6 et 9.1bis. Avoir
  la main lourde sur les explications -- mieux vaut un encadre superflu
  qu'une notion laissee dans l'ombre.
- **Visuel** : un bilan dense en texte fatigue. Utiliser **cartes,
  schemas, chronologies, diagrammes** au fil du document chaque fois que
  cela aide la comprehension. Reutiliser le materiel de l'article
  (`article/figures/`) **et generer du materiel de novo** (TikZ, pgfplots)
  quand aucune figure existante ne couvre un point pedagogique. Voir
  Phase 9.1ter. Les bilans riches comportent typiquement 4 a 10 figures
  ou schemas, dont 2-4 generes specifiquement pour le bilan.

### Ce que le bilan ne doit PAS etre

- Une liste de bullet points avec des comptages ("12 figures, 8 scripts")
- Un tableau sans explication
- Une enumeration seche de pistes sans justification scientifique
- **Un journal narratif des sessions** ("le 12 mars on a lance X, puis le
  15 mars on a vu que Y, alors le 18 on a essaye Z"). Le cheminement
  iteratif ne doit apparaitre que dans la section "Apercu chronologique",
  resume en quelques phrases.
- Un resume telegraphique du cahier
- Un document ou chaque section tient en 3 lignes
- **Un document sans section "A faire maintenant"** : si le projet n'est
  pas encore boucle, le bilan doit explicitement dire ce qui reste a
  faire d'apres ce qui est inscrit dans le cahier.
- **Une mise a jour incrementale d'un bilan precedent**. Si un bilan
  anterieur existe dans `<projet>/bilans/`, il n'est ni lu, ni cite,
  ni "complete". Le nouveau bilan est ecrit de A a Z comme s'il
  s'agissait du premier, en consolidant l'integralite du cahier de
  labo et de la litterature. Les bilans anteriors sont des **archives
  datees**, conserves cote a cote mais sans hierarchie de version
  active : chacun reflete l'etat des connaissances a sa date
  d'ecriture, et le plus recent ne suppose pas la lecture des autres.

## Prealable -- Consultation memoire

**Avant toute action** :

1. Consulter le skill `mtbc-lineages` pour la golden law sur les lignees
   MTBC (hierarchie Guyeux, biais de reference H37Rv). Degrader gracieusement
   si ce skill est indisponible -- le bilan reste possible, seule la
   validation golden law est affaiblie.

   > **Source de verite -- LISTE et EFFECTIFS des lignees** (cf.
   > `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`) : pour la
   > liste des lignees existantes et le nombre de souches par lignee, la
   > reference autoritative est **`bdd/actuelle/`** (les repertoires de
   > souches font foi), avec **`barcoding_v2/barcode_complete.tsv`** comme
   > registre derive. Ne PAS lire la "golden law" `lignees.py` comme source
   > des effectifs : elle peut etre desynchronisee de la taxonomie vivante
   > (snapshot en retard sur les cycles de subdivision recents). De meme,
   > `snp_barcoding.csv` (v1 obsolete) et `strain_lineages.csv` (perime)
   > ne sont jamais des references taxonomiques.
   >
   > **Source de verite (cf. `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`)** : dans TBannotator, `system='Senelle'` EST le systeme maison (= moi/Guyeux), mais c'est un **snapshot** susceptible d'etre en retard sur la taxonomie vivante. Pour tout clade recent du cycle multi-signal (L1.\*, Bovis1.\*, BCG.\*, L6 profond), recouper le label avec `bdd/actuelle/` + `barcoding_v2/barcode_complete.tsv`. Ne jamais lire `snp_barcoding.csv` (v1 obsolete) ni `strain_lineages.csv` (perime) comme reference taxonomique.

2. Si une `~/.claude/knowledge/tuberculosis.md` existe, la consulter pour
   les apprentissages transverses.
3. Lire `codes/mtbc/CLAUDE.md` pour les conventions globales du depot.

## Declenchement

```
/mtbc-bilan                    # Bilan du projet dans le repertoire courant
/mtbc-bilan L4.9               # Bilan d'un projet specifique (nom ou chemin)
/mtbc-bilan /abs/path/to/L5    # Bilan via chemin absolu
/mtbc-bilan --full             # Bilan comparatif de TOUS les projets mtbc/
```

- **Sans argument** : cible le repertoire courant (`pwd`).
- **Argument positionnel** : nom de projet relatif a `codes/mtbc/` ou chemin
  absolu vers le repertoire projet.
- **`--full`** : scan exhaustif, bilan comparatif multi-projets.

**Livrables systematiques** : chaque invocation produit **trois fichiers**
dans `<projet>/bilans/`, tous obligatoires :

- `YYYY-MM-DD_bilan.md` (source Markdown editable)
- `YYYY-MM-DD_bilan.pdf` (rendu PDF compile, **toujours genere**)
- `YYYY-MM-DD_bilan_slides.pdf` (presentation Beamer)

Le mode `--full` produit le Markdown + PDF (pas de slides en mode full).
Le PDF est genere automatiquement dans la meme passe que le Markdown ;
livrer le `.md` sans le `.pdf` correspondant est consideré comme une
livraison incomplete (voir Phase 9.2).

**Mode standalone (defaut et unique)** : chaque bilan est un document
**complet et autonome**. Si des bilans plus anciens existent deja dans
`<projet>/bilans/`, ils sont **ignores** lors de la generation : pas
de lecture, pas de citation, pas de "delta", pas de "depuis le bilan
v2". Le nouveau bilan est ecrit a partir de zero en consolidant le
cahier de labo et la litterature, comme si c'etait le premier bilan
du projet. Les anciens fichiers sont conserves cote a cote en tant
qu'archives datees (pas ecrases : suffixe `_v2`, `_v3`... en cas de
collision de date), mais ne participent jamais a la redaction. Voir
Phase 1 pour le detail des sources autorisees / interdites.

Profondeur : **lecture seule + inspection legere**. Aucun calcul lourd, aucun
appel a TBannotator, aucun lancement d'analyse. Le skill **suggere**, il
**n'execute pas**.

**Non destructif** : la seule ecriture autorisee est la creation des fichiers
bilan (et du repertoire `bilans/` si absent).

---

## Phase 0 -- Resolution et sanity-check

1. Resoudre le chemin cible :
   - Si `--full` → `MTBC_ROOT=/home/christophe/docs/codes/mtbc`
     et passer au mode full (section dediee plus bas).
   - Sinon si argument fourni :
     - Si chemin absolu → utiliser tel quel.
     - Si nom relatif → prefixer par `$MTBC_ROOT/`.
   - Sinon → utiliser `pwd`.
2. Normaliser via `realpath` pour eviter les ambiguites ulterieures.
3. Verifier que le repertoire existe. Si non : abandon propre avec message.
4. Sanity-check "est-ce un projet MTBC ?" :
   - Compter les presences parmi : `CLAUDE.md`, `cahier_de_labo.md`,
     `JOURNAL.md`, `analyses/`, `article/`.
   - Si moins de 2 : afficher "Ce repertoire ne ressemble pas a un projet
     MTBC. Trouve : <liste>. Abandon." et terminer.

---

## Phase 1 -- Lecture du cahier et consolidation des connaissances

L'objectif de cette phase n'est pas de reconstituer l'histoire iterative
du projet, mais de **consolider l'etat actuel des connaissances**. La
lecture se fait **en partant des entrees les plus recentes** et en
remontant le temps, en accumulant les faits etablis et en gardant la
derniere version consolidee en cas de conflit.

**Sources autorisees pour cette phase** :

- `<projet>/CLAUDE.md` (lecture integrale).
- `<projet>/cahier_de_labo.md` (ou `JOURNAL.md`) lu **en entier**,
  dans l'ordre inverse.
- `<projet>/article/` : manuscrit en cours, `claim_check.md`,
  `review/INDEX.md`, `litterature_review/`.
- `<projet>/analyses/`, `<projet>/resultats/`, `<projet>/data/` :
  inspection legere pour l'inventaire (Phase 2).
- `~/.claude/knowledge/tuberculosis.md`, skills `mtbc-lineages`,
  `mtbc-deepen`.

**Source explicitement INTERDITE** : tout fichier dans
`<projet>/bilans/` (qu'il s'agisse de `.md`, `.pdf`, ou `.tex`).
Les bilans precedents ne sont **ni lus, ni resumes, ni cites**. La
seule operation autorisee sur ce repertoire est `ls` pour detecter
une collision de nom de fichier le jour meme (afin d'appliquer le
suffixe `_v2`, `_v3`...). Cette interdiction garantit que chaque
nouveau bilan est un **document standalone**, ecrit a partir du
cahier de labo et de la litterature, sans reprendre ni amender un
texte anterieur.

**Pourquoi cette regle** : un bilan qui s'appuie sur le precedent
derive vers un mode "delta" ("rien de neuf cote phylogeographie",
"voir v2 pour la datation"), qui suppose la lecture de l'archive
anterieure et perd progressivement son autonomie. L'utilisateur, qui
ouvre le bilan le plus recent pour avoir l'etat du projet, doit y
trouver l'**etat consolide complet**, pas un changelog. La memoire
factuelle reside dans le cahier de labo ; le bilan en est une
relecture argumentee a date.

1. `Read <projet>/CLAUDE.md` (integralement) :
   - Extraire le titre du projet, la lignee, les conventions locales.
   - Comprendre la question scientifique fondatrice du projet.

2. Localiser le journal :
   - Prioritairement `cahier_de_labo.md`.
   - Fallback `JOURNAL.md` (anciens projets comme `methodology/`).
   - Si les deux existent : lire les deux et signaler l'incoherence.

3. **Lire le cahier INTEGRALEMENT, mais dans l'ordre inverse** -- c'est
   la phase la plus importante. Commencer par la derniere entree, puis
   remonter entree par entree jusqu'a la premiere. Si > 5000 lignes, lire
   par chunks de 2000 en partant de la fin, **jamais tronquer
   silencieusement**. Ne pas se contenter de grep les headers.

   **Pourquoi a rebours** : ce qui est ecrit le plus recemment reflete
   l'etat actuel du savoir et des outils du projet. En remontant, on
   ajoute des elements anterieurs uniquement quand ils n'ont pas ete
   recouverts ou contredits par une entree posterieure.

4. **Consolidation au fil de la lecture** : maintenir mentalement (ou
   dans un brouillon) deux structures :

   **A. Carte des connaissances actuelles** -- thematique (lignee/clade,
   marqueurs, datation, phylogeographie, resistance, methodologie...). Pour
   chaque fait consolide, noter :
   - **Le fait** lui-meme (formulation actuelle, post-consolidation)
   - **Comment il a ete etabli** (script `phase4_xxx.py`, methode
     RAxML-NG GTR+G, base de donnees de N souches, reference Coll 2014...)
   - **Le niveau de consolidation** (voir taxonomie Phase 1bis) :
     `etabli`, `convergent`, `unique`, `volatile`, `fragile`,
     `hypothetique`, `speculatif`.
   - **Pour les faits non `etabli`** : amplitude de variation observee
     ou source de fragilite (en chiffres ou en mots si pas chiffrable),
     et une **piste de consolidation** quand elle existe (ou explicitement
     "pas de voie de consolidation evidente avec les donnees actuelles").
   - **Eventuellement** : la mention "version revisee, anterieurement
     [ancien chiffre/affirmation]" si l'evolution est instructive
     (changement de methode, donnee corrigee, biais decouvert).

   **B. Liste des intentions non honorees** -- toute mention dans le
   cahier d'une chose a faire, a verifier, a explorer, qui n'apparait
   ulterieurement nulle part dans une entree plus recente comme realisee.
   Sources typiques :
   - `### Pistes futures` (sections explicites)
   - "il faudrait", "a verifier", "TODO", "on devrait", "prochaine etape"
   - Hypothese formulee mais non testee dans les entrees ulterieures
   - Donnee mentionnee mais non integree (souche, BDD, fichier externe)
   - Reference suggeree comme a lire mais non incorporee a la
     litterature_review

   **Regle de consolidation en cas de conflit** : si l'entree du
   2026-04-15 dit "57 SNP retro-mutes detectes" et celle du 2026-04-22
   dit "apres correction d'alignement, 38 SNP retro-mutes confirmes",
   on garde **38**, eventuellement avec une note pedagogique sur la
   correction. Ne JAMAIS garder les deux chiffres comme si c'etait deux
   resultats independants.

5. Pendant la consolidation, aussi noter :

   a. **Les mecanismes biologiques actuellement invoques** : quels
      genes, quels pathways, quelles hypotheses evolutives sont
      mentionnes dans les entrees recentes ? Alimentera la mise en
      perspective avec la litterature.

   b. **Les echecs instructifs** confirmes (pas remplaces par un succes
      ulterieur) : `Grep ^#### Negatifs` mais aussi lire les sections
      ou quelque chose n'a pas marche. Si une entree ulterieure decrit
      la solution, l'echec est devenu un pas-de-cote dans le narratif
      court ; sinon, il reste comme une limite ou une piste.

   c. **Les indices de statut** :
      `Grep -i "submitted\|accepted\|published\|en preparation\|bouclee"`
      (recents en priorite).

   d. **Le squelette du narratif chronologique court** : 4-8 jalons
      dates qui ressortent en remontant le cahier. Ne PAS reconstruire
      tous les pas du projet ; ne retenir que les tournants reels
      (premier resultat marquant, reorientation, decouverte majeure,
      soumission...).

**Important : separation stricte bookkeeping vs redaction.** La
structure "fait + methode + niveau de consolidation + amplitude /
fragilite + piste" est un format de **bookkeeping interne** utilise
pendant la lecture du cahier en Phase 1. Elle **ne doit jamais
apparaitre telle quelle** dans le bilan final (sous forme de blocs
quote "**Fait :** ... **Methode :** ..." ou de fiches structurees).
Au moment de la redaction (Phase 9.1), chaque element bookkeepe est
**re-rendu en prose** dans des paragraphes argumentes, ou ces memes
informations (chiffres, methode, niveau de consolidation, amplitude)
s'integrent naturellement dans les phrases. Voir les exemples
narratifs de la section "Etat actuel des connaissances acquises" et
"Decouvertes majeures et leur signification" pour le rendu attendu.

---

## Phase 1bis -- Taxonomie du niveau de consolidation

Chaque fait consolide en Phase 1 recoit l'un des **sept niveaux**
suivants. Le choix du niveau est explicite, jamais sous-entendu, et
apparait textuellement dans le bilan (section "Etat actuel des
connaissances" et section "Decouvertes majeures").

### Les sept niveaux

| Niveau | Definition | Indication typique |
|--------|------------|---------------------|
| `etabli` | Reproduit par >=2 methodes ou >=2 executions independantes ; claim-check OK ; robuste aux variations raisonnables de parametres | Vert |
| `convergent` | Plusieurs methodes/analyses concordent, mais non encore formellement reproduit (meme jeu de donnees, methodes proches) | Vert clair |
| `unique` | Une seule analyse/methode ; valeur precise mais sensibilite non testee | Jaune |
| `volatile` | La valeur exacte change significativement avec la methode, le parametre, ou la sous-selection de donnees ; le pattern qualitatif peut rester | Orange |
| `fragile` | Depend d'une hypothese forte (horloge moleculaire stricte, biais H37Rv, modele d'evolution) qui pourrait etre violee | Orange |
| `hypothetique` | Hypothese de travail formulee a partir des resultats du projet, pas encore testee | Rouge clair |
| `speculatif` | Suggere par la litterature, par analogie, ou par intuition ; aucun test sur les donnees du projet | Rouge |

**Regles d'attribution** :

1. Un fait n'est `etabli` que si on peut citer **deux** sources de
   validation (par exemple : RAxML-NG + IQ-TREE concordent, OU resultat
   reproduit a un mois d'intervalle apres ajout de souches, OU verifie
   par claim-check).
2. Un fait est `volatile` des qu'une variation de methode (BEAST vs
   LSD2, modele GTR vs GTR+G+I, sous-echantillonnage) change le
   resultat de plus de 15-20 % en relatif, ou de plus que l'IC95
   nominal.
3. Un fait est `fragile` s'il repose sur une hypothese identifiable et
   testable mais non testee : ex. "MRCA = 1240 CE en supposant horloge
   stricte" -> fragile si la relaxation de l'horloge n'a pas ete
   essayee.
4. La distinction `volatile` / `fragile` :
   - **volatile** = "le chiffre bouge quand on change la methode"
     (instabilite empirique observee)
   - **fragile** = "le chiffre repose sur une hypothese non verifiee
     qui, si fausse, le casserait" (instabilite logique potentielle)
   Un meme fait peut etre les deux ; dans ce cas, prendre le niveau le
   plus pessimiste (`fragile`).
5. `hypothetique` vs `speculatif` :
   - **hypothetique** = formule a partir des donnees du projet,
     testable a l'avenir (ex. "la retro-mutation pourrait s'expliquer
     par selection convergente sur katG").
   - **speculatif** = vient de l'exterieur, pas de donnee projet pour
     le supporter ou le refuter directement (ex. "l'apparition de
     proto-L4.2 pourrait coincider avec les famines du XIVe siecle").

### Marquage explicite des faits volatils / fragiles

Tout fait `volatile` ou `fragile` doit imperativement preciser :

1. **L'amplitude de variation observee** (volatile) ou **l'hypothese
   qui pourrait casser** (fragile). En chiffres si possible :
   - "MRCA = 1240 CE [LSD2 sur arbre RAxML] ; 1080-1410 CE selon la
     methode (BEAST tip-dating : 1110 CE ; BEAST node-dating : 1340 CE ;
     LSD2 : 1240 CE)."
   - "Estimation fragile : suppose une horloge moleculaire stricte
     ; la relaxation par BEAST n'a pas ete testee, elle pourrait
     elargir l'IC de ~200 ans."
2. **Une piste de consolidation** quand elle existe :
   - "Pour consolider : lancer BEAST avec horloge relaxee et
     calibration par dates de prelevement (`/molecular-clock`)."
   - "Pour consolider : repliquer avec sous-echantillonnage 80%
     (jackknife) pour estimer la stabilite empirique."
   - Si aucune piste evidente : "Pas de voie de consolidation
     immediate avec les donnees actuelles ; la stabilite ne pourra
     etre evaluee qu'avec un corpus elargi."
3. La piste de consolidation est **automatiquement ajoutee** soit a
   "A faire maintenant" (si elle a deja ete evoquee dans le cahier),
   soit a "Pistes d'approfondissement" (si c'est une piste deduite).
   Le lien est explicite : "Cf. section 'A faire maintenant', item
   `<titre>`."

### Encadre `fragilite` (nouveau type)

Pour les faits centraux du projet qui sont `volatile` ou `fragile`,
inserer un encadre dedie dans le bilan PDF, sur le modele de
`notion`/`methode`/`originalite`/`remarquable`. Ce nouvel encadre,
**`fragilite`**, attire l'attention sur :

- Pourquoi le resultat est instable / fragile
- L'amplitude exacte de la variation
- Les hypotheses sous-jacentes
- Les voies de consolidation

Voir section 9.1bis pour la syntaxe LaTeX exacte (a ajouter au template
`bilan.latex` lors de la prochaine evolution du template ; en attendant,
utiliser un environnement `tcolorbox` rouge/orange ad hoc, ou recycler
`remarquable` avec un titre commencant par "Fragilite :").

### Heuristiques de detection automatique

Pendant la lecture du cahier (Phase 1), reperer les signaux suivants
qui orientent vers `volatile`/`fragile`/`hypothetique` :

- Mots-cles : "depend de", "selon la methode", "varie entre", "sous
  hypothese de", "il faudrait verifier", "preliminaire", "indicatif",
  "ordre de grandeur", "robuste a confirmer", "a tester", "non encore
  reproduit".
- Plusieurs valeurs differentes pour le meme fait au fil des entrees
  (ex. dates de MRCA qui evoluent) -> `volatile` par defaut, meme si
  la derniere valeur est rapportee comme "consolidee".
- Resultat issu d'un seul script sans re-execution -> jamais `etabli`,
  au mieux `unique`.
- Hypothese biologique mentionnee dans la section "Hypotheses" ou
  "Interpretation" mais sans test associe -> `hypothetique`.

---

## Phase 2 -- Inventaire des donnees et scripts

1. `Glob <projet>/analyses/phase*_*.py` :
   - Compter par phase (phase1, phase2, ...).
   - Detecter les gaps (phase 3 sans phase 4 → trou suspect).
   - Lister en une ligne chaque script (nom + eventuellement premiere
     docstring).
2. `Glob <projet>/resultats/**/*.pdf`, `.png`, `.svg`, `.csv`, `.tsv` :
   - Compter figures/tables.
   - Lister les fichiers cles (csv de matrices, tables supplementaires).
3. `Glob <projet>/data/*.{csv,tsv,fasta,nwk,txt}` :
   - Lister les donnees brutes presentes.
4. BDD centrale :
   - Determiner le nom de lignee (depuis nom de repertoire ou CLAUDE.md).
   - Verifier `<projet>/../../bdd/actuelle/<lignee>/` (depuis le projet).
   - Si present : compter les sous-repertoires (= souches) via
     `ls | wc -l`, lister quelques noms.
   - Si absent : mentionner comme anomalie, ne pas bloquer.

---

## Phase 3 -- Etat du manuscrit

Si `<projet>/article/` existe :

1. `Read <projet>/article/main.tex` limit 300, puis
   `Grep ^\\section{` sur le fichier entier → structure des sections
   redigees.
2. Si `<projet>/article/claim_check.md` present : le lire et extraire
   `total claims`, `verifies`, `infirmes`, `a verifier`.
3. Si `<projet>/article/review/INDEX.md` present : le lire et extraire
   le nombre de reviews recues et leur statut (en cours / traitee /
   soumise).
4. `Glob <projet>/article/figures/*` → compter les figures integrees.
5. Chercher un indice de statut : fichier `submitted.md`, mention
   "submitted"/"accepted" dans un commit recent ou dans le cahier.

Si `article/` absent : section "Manuscrit" = "Non initialise".

---

## Phase 4 -- Exploitation approfondie de la litterature

La litterature n'est pas une annexe du bilan — c'est le **cadre
interpretatif** qui donne du sens aux decouvertes du projet. Cette phase
doit produire une comprehension fine de ce que la communaute sait (et ne
sait pas) sur le sujet, pour pouvoir ensuite situer les resultats du
projet dans ce paysage.

**Cette phase alimente deux sections du bilan** :
- La section "Etat des connaissances avant ce projet" (background)
- La section "Paysage de la litterature" (mise en perspective des
  resultats du projet)

### 4.1 Inventaire des sources disponibles

1. `Glob <projet>/litterature_review/*.md` → fiches thematiques presentes.
2. `Read <projet>/litterature_review/index.md` → sujets explores, derniere
   MAJ, directions futures suggerees.
3. Compter les references :
   `Grep -c ^@ <projet>/litterature_review/references.bib`
4. Si `article/references.bib` ou `article/*.bib` existe aussi : le lire,
   car il contient souvent des refs supplementaires citees dans le manuscrit
   mais pas dans la litterature_review.

### 4.2 Lecture des syntheses thematiques

**Pour chaque fiche thematique** dans `litterature_review/` :

1. `Read` la fiche integralement (pas juste les lacunes).
2. Extraire :
   - La synthese narrative (section `## Synthese`)
   - Les articles cles et leur contribution
   - Les lacunes identifiees
   - Les directions suggerees non explorees
3. **Construire un mapping decouvertes ↔ litterature** : pour chaque
   decouverte majeure du projet (Phase 1), identifier :
   - Quels articles de la litterature_review confirment, contredisent,
     ou sont coherents avec ce resultat ?
   - Est-ce que cette decouverte comble une lacune identifiee ?
   - Est-ce que cette decouverte est completement nouvelle (rien dans
     la litterature ne la mentionne ou l'anticipe) ?

### 4.3 Mise en perspective des decouvertes

C'est le coeur de cette phase. Pour chaque decouverte majeure du projet :

1. **Situer dans la litterature** : cette observation a-t-elle ete faite
   ailleurs ? Sur d'autres lignees ? Avec d'autres methodes ? Si oui,
   les resultats convergent-ils ?

2. **Evaluer l'originalite** : est-ce une confirmation de resultats
   connus, une extension a une nouvelle lignee, ou une observation
   genuinement nouvelle ?

3. **Identifier les mecanismes** : la litterature propose-t-elle des
   mecanismes biologiques qui expliqueraient cette observation ? Si oui,
   lesquels ? Si non, c'est une lacune a mentionner.

4. **Detecter les contradictions** : cette decouverte contredit-elle des
   resultats publies ? Si oui, c'est potentiellement l'element le plus
   interessant du bilan.

### 4.4 Identification des angles morts

Comparer ce que la litterature couvre avec ce que le projet a explore :

1. Y a-t-il des sujets bien couverts dans la litterature mais que le
   projet n'a pas abordes ? (opportunites manquees)
2. Y a-t-il des resultats du projet qui ne correspondent a aucune fiche
   thematique ? (lacune dans la lit-review, pas dans le projet)
3. Les lacunes identifiees dans les fiches : lesquelles le projet
   pourrait-il combler avec ses donnees actuelles ?

### 4.5 Si litterature_review/ n'existe pas

Ne pas se contenter de noter "pas de litterature". A la place :

1. Lire les references du manuscrit (`article/*.bib`) si elles existent.
2. Identifier les articles les plus cites dans le cahier de labo.
3. Mentionner cette absence comme une **lacune majeure** du projet et
   la proposer comme piste haute priorite (`/lit-review <sujet> --wide`).

### 4.6 Identification des notions a expliciter pedagogiquement

Le bilan est destine en premier lieu a **Christophe Guyeux**, dont la
formation est mathematiques pures + informatique de base. Tout ce qui
releve de la biologie evolutive, de la genetique des populations, de
l'ethno-linguistique, de l'epidemiologie des maladies infectieuses, ou
des statistiques inferentielles avancees est **a priori opaque** pour ce
profil et doit etre explicite.

**Principe directeur** : mieux vaut un encadre superflu qu'une notion
laissee dans l'ombre. Avoir la main lourde sur les explications --
l'objectif est qu'a la lecture du bilan, le specialiste de math
pures puisse expliquer a un collegue ce que sont les Bantu, ce qu'est
un test de Mantel partiel, et pourquoi c'est utilise ici.

**Avant de commencer la redaction (Phase 9)**, dresser une liste des
notions presentes dans le projet qui meritent un encadre pedagogique.
Categories typiques a passer en revue :

#### A. Anthropologie, ethno-linguistique, geographie historique
Concepts a expliciter quand ils apparaissent dans le projet (frequents
sur les lignees L5, L6, L9, L10 et tout projet a dimension
phylogeographique africaine, asiatique ou amerindienne) :
- Familles linguistiques (Bantu, Kwa, Niger-Congo, Afro-asiatiques,
  Nilo-sahariennes, Khoisan, Austronesien, Sino-tibetain...)
- Migrations historiques (expansion bantoue, peuplement du Sahel,
  routes de la soie, traites negrieres et leurs consequences
  demographiques)
- Groupes ethniques cles cites dans l'article (Yoruba, Akan, Mossi,
  Zoulou, Massai, Hutu/Tutsi, Pygmees, San, Ewondo...)
- Ecotypes et co-evolution hote-pathogene (notion d'animal-adapted
  vs human-adapted MTBC, ecotypes M. bovis / M. caprae / M. mungi /
  M. orygis...)
- Geographie sanitaire et historique coloniale (anciennes colonies,
  decoupages administratifs hérites qui structurent encore les bases
  de donnees)

Pour chacun de ces concepts presents dans le projet, expliquer dans un
encadre **Notion** :
1. De quoi il s'agit (en 2-4 phrases)
2. Pourquoi c'est pertinent pour le projet (genetique des populations
   humaines coevoluant avec MTBC, pression demographique, brassage)
3. Quels groupes/regions sont concernes
4. Une reference de vulgarisation ou un article de reference si
   disponible

#### B. Biologie et genetique des populations
Concepts qui semblent triviaux a un biologiste mais ne le sont pas
pour un mathematicien :
- Goulot d'etranglement, effet fondateur, derive genetique
- Isolat, deme, structure de population (Fst, Wright)
- Coalescent, ancestral state reconstruction
- Selection (positive, purifiante, balancee, frequence-dependante)
- Equilibre de Hardy-Weinberg, deviation et ses causes
- Recombinaison vs mutation, mutation rate, taux de substitution
- Marqueurs neutres vs sous selection
- Linkage disequilibrium, hitchhiking
- Notion d'haplotype, haplogroupe
- Notions d'epidemiologie : R0, transmission cluster, source case,
  super-spreader, latence, reactivation
- Specificites MTBC : clonalite (pas de recombinaison horizontale
  significative), absence de plasmide majeur, lent taux de mutation

#### C. Phylogenetique et evolution moleculaire
Methodes phylogenetiques avancees a expliciter :
- Maximum de vraisemblance (ML) vs maximum de parcimonie vs
  inference bayesienne
- Modeles de substitution (JC69, HKY, GTR, GTR+G+I, partitionnement)
- Bootstrap et support : que mesure-t-il vraiment ?
- Datation moleculaire : horloge stricte vs relachee, calibration
  par fossiles ou par dates de prelevement (tip-dating)
- Notion d'outgroup et de polarisation
- Ancestral state reconstruction (parsimony, ML, stochastic mapping)
- Coalescent et skyline plots (BEAST, LSD2)
- Tree skewness, balance index, branche longue
- Notions de monophylie, paraphylie, polyphylie
- Specificites SNP-based phylogeny chez MTBC (faible diversite,
  ascertainment bias, biais de reference H37Rv)

#### D. Statistiques inferentielles utilisees en biologie
A expliciter systematiquement -- ces tests ne font partie d'aucun
cursus standard de math pures ou d'informatique :
- Test de Mantel (simple), test de Mantel partiel : qu'est-ce que
  ca compare, quelle est la statistique, pourquoi des permutations,
  quand est-ce justifie ?
- Tests non-parametriques (Wilcoxon, Mann-Whitney, Kruskal-Wallis) :
  quand les preferer aux tests parametriques
- Correction multiple (Bonferroni, FDR de Benjamini-Hochberg) :
  pourquoi corriger, qu'est-ce que controle chaque methode
- Tests d'enrichissement (hypergeometrique, GO enrichment, gene
  set enrichment analysis)
- Tests de neutralite (Tajima's D, Fu-Li, McDonald-Kreitman, dN/dS)
- ABC (Approximate Bayesian Computation), MCMC dans le contexte
  phylogenetique
- Bootstrap parametrique vs non-parametrique
- p-values, intervalles de confiance, taille d'effet : la difference
- Tests de robustesse, analyses de sensibilite

#### E. Outils et formats specifiques au domaine
Les acronymes et formats qui sont du folklore pour un bioinformaticien
mais opaques sinon :
- VCF, BAM, FASTA, FASTQ, GFF3, GenBank
- SPDI, HGVS pour la nomenclature des variants
- Spoligotyping, MIRU-VNTR, RFLP
- WGS, WES, ddRADseq, amplicon sequencing
- BWA, GATK, samtools, bcftools, snippy, BLAST
- RAxML, IQ-TREE, BEAST, MrBayes, PhyML
- Outils MTBC-specifiques (TBProfiler, MTBseq, Mykrobe, TBannotator)

#### F. Concepts MTBC et tuberculose
Memes les chercheurs MTBC repertorient ces notions, donc a fortiori
un mathematicien :
- Definition des lignees (L1-L10) et leur biogeographie
- Animal-adapted vs human-adapted ecotypes
- Notion de "modern" vs "ancient" lineages (L2/L4 vs L5/L6/L7)
- Pathogenie : granulome, latence, reactivation, miliaire
- Resistance : MDR, XDR, pre-XDR, definition OMS, mecanismes
  (katG, rpoB, embB, gyrA, pncA)
- Outils diagnostiques : GeneXpert, LJ, MGIT, BACTEC
- Notion de "transmission cluster" en epidemiologie moleculaire

**Rendu** : pour chaque concept retenu, prevoir un encadre dans la
section appropriee du bilan (typiquement la premiere occurrence dans
"Etat des connaissances avant ce projet", "Etat actuel des
connaissances acquises", ou "Decouvertes majeures").
La syntaxe d'insertion est detaillee en Phase 9.

**Cible quantitative** : un bilan typique contient **10 a 25 encadres
pedagogiques** repartis sur l'ensemble du document, dont typiquement :
- 5 a 12 encadres `notion` (concepts de domaine)
- 3 a 6 encadres `methode` (techniques non triviales)
- 1 a 5 encadres `originalite` (un par decouverte majeure)
- 3 a 6 encadres `remarquable` (resultats frappants en soi)
- 1 a 5 encadres `fragilite` (un par fait central marque `volatile`
  ou `fragile` en Phase 1bis ; **obligatoire** pour les datations,
  estimations de taille de population, et tout chiffre dont la valeur
  exacte depend de la methode)

Un bilan court avec 2-3 encadres seulement signifie generalement que la
phase 4.6 a ete bacleee. Un bilan avec > 35 encadres peut au contraire
devenir lourd a lire et signifie qu'il faudrait fusionner certains
concepts ou eliminer les encadres `remarquable` qui ne sont pas
genuinement saisissants.

---

## Phase 5 -- Statut des intentions memorisees + nouvelles pistes

Cette phase produit deux listes distinctes, qui alimentent deux sections
differentes du bilan :

### 5.A Intentions memorisees non honorees ("A faire maintenant")

Repartir de la **liste B** construite en Phase 1 (intentions non
honorees). Pour chaque entree :

1. Verifier une derniere fois qu'aucune entree posterieure ne la decrit
   comme realisee (recherche par mots-cles dans les entrees plus
   recentes que celle d'origine).
2. Classer le statut :
   - `a_faire` -- planifie dans le cahier, jamais traite par la suite.
   - `partiellement_fait` -- amorce mais inacheve d'apres les entrees
     posterieures.
   - `close` -- finalement traite dans une entree ulterieure (sortir de
     la liste).
   - `obsolete` -- mention explicite d'abandon, ou intention rendue
     caduque par un resultat ulterieur.
3. Pour les `a_faire` et `partiellement_fait`, noter :
   - **L'entree d'origine** (date) et la formulation exacte si courte.
   - **Pourquoi c'etait prevu** (motivation memorisee dans le cahier).
   - **Ce qui manque concretement** pour l'executer (donnee, outil,
     decision, temps).

Ces elements alimentent la section "A faire maintenant" du bilan, qui
est **factuelle** et tracee : chaque item renvoie a une entree precise
du cahier.

### 5.B Deduplication globale et nouvelles pistes

1. Partir des bullets de la liste A.5.A `a_faire` + `partiellement_fait`,
   AINSI QUE des pistes ouvertes anciennes (sections "Pistes futures"
   d'entrees plus anciennes non encore traitees).
2. Deduplication par similarite semantique (regroupement manuel des
   formulations proches).
3. Ajouter en plus les pistes **deduites par le skill** des inventaires
   (Phases 2-4) et de la litterature : ce sont des nouvelles directions
   qui ne sont pas dans le cahier, mais qui emergent de l'analyse.
4. Marquer chaque piste comme :
   - `memorisee` -- vient du cahier (toujours tracee a une date).
   - `deduite_inventaire` -- emerge de l'analyse des scripts/resultats.
   - `deduite_litterature` -- emerge d'une lacune dans
     `litterature_review/`.
5. Toutes les pistes (memorisees non honorees + deduites) passent en
   Phase 7 pour hierarchisation, mais elles alimentent **deux sections
   distinctes** du bilan : "A faire maintenant" pour les memorisees,
   "Pistes d'approfondissement" pour les deduites.

---

## Phase 6 -- Convergences inter-projets (leger en mode normal)

Le but n'est pas d'ouvrir chaque projet voisin, juste de reperer des
convergences evidentes :

1. `ls /home/christophe/docs/codes/mtbc/` -- lister les
   repertoires freres.
2. Pour chaque voisin pertinent (meme famille de lignee, ou projet
   transversal connu) : `Read CLAUDE.md` limit 20 → titre + objectif.
3. Identifier :
   - Lignees apparentees (ex : travail sur L4.9 et L4.14 → methodologie
     commune possible).
   - Projets transversaux qui couvriraient deja la question (ex :
     `animal_vs_human/` couvre deja la convergence ESX).
   - Donnees partagees possibles (BDD commune, outgroup commun).

En mode `--full`, cette phase devient centrale et detaillee.

---

## Phase 7 -- Hierarchisation argumentee par impact

Pour chaque piste `open` collectee en Phase 5, plus toute nouvelle piste
deduite des inventaires des Phases 2-4 et de la mise en perspective
litteraire (Phase 4) :

### 7.1 Construction de l'argumentaire scientifique

**Avant de scorer**, construire pour chaque piste un argumentaire de 4-8
phrases qui repond a ces questions :
- Quelle question scientifique cette piste adresse-t-elle ?
- Pourquoi est-ce interessant dans le contexte de CE projet ?
- Que dit la litterature sur ce sujet ? Y a-t-il une lacune a combler ?
- Quelle methode utiliser et quel resultat peut-on raisonnablement
  attendre ?
- Qu'est-ce que ca changerait pour les conclusions du projet ?

Cet argumentaire sera repris tel quel dans la section "Pistes
d'approfondissement" du bilan.
Les pistes dont on ne peut pas construire un argumentaire convaincant
sont probablement basses priorite.

### 7.2 Scoring

1. Scorer chaque piste sur trois dimensions (0 a 3) :
   - **Valeur scientifique** : impact attendu sur les conclusions, la
     publication, ou la connaissance de fond.
   - **Faisabilite** : donnees disponibles, outils existants, complexite
     technique.
   - **Cout** : temps et ressources calcul. Un cout eleve **divise** le
     score.
2. Score final = `valeur * faisabilite / cout`. Arrondi au dixieme.
3. Classement : **haute** (score >= 2), **moyenne** (1-2), **basse** (< 1).

### 7.3 Association aux skills

Pour chaque piste, associer explicitement un ou plusieurs skills
existants du plugin `bio/` :
- Phylogenie / datation : `/raxml`, `/iqtree-lsd2`, `/molecular-clock`,
  `/bayesian-skyline`, `/pastml`
- Structure de population : `/clade-finder`, `/tsne-hdbscan`,
  `/phylo-history`, `/snp-distance`
- Annotation / evolution : `/spdi-annotation`, `/convergent-evolution`,
  `/coevolution`, `/mk-ascertainment`, `/pangenome-enrichment`
- Epidemiologie / phenotype : `/lineage-comparison`,
  `/resistance-profiler`, `/phylogeography`
- BDD / queries : `/tb-cli`, `/tbannotator-mcp`, `/fetch-tbannotator`
- Manuscrit / litterature : `/lit-review`, `/claim-check`,
  `/manuscript-review`, `/reviewer-response`, `/bib-check`

Si aucun skill existant ne convient pour une piste haute priorite :
suggerer explicitement la creation d'un nouveau skill.

**Regle d'honnetete** : ne PAS gonfler la liste. Si moins de 3 pistes
haute priorite emergent honnetement, assumer une sortie courte.

---

## Phase 8 -- Verdict

Appliquer les sept criteres de cloture. Au moins **5/7** pour verdict
"bouclee", **et le critere 7 doit etre satisfait** (un projet ne peut
pas etre boucle si ses faits centraux sont volatils ou fragiles non
documentes) :

1. **Article** : soumis/accepte/publie (indice cahier) **OU**
   `claim_check.md` avec 0 infirme ET 100 % verifies.
2. **Pistes** : toutes les pistes cumulees sont `close` ou `abandonnee`
   (aucune `open`).
3. **Reviews** : toutes les reviews de `review/INDEX.md` sont traitees
   (ou aucune review attendue).
4. **Litterature** : lacunes toutes couvertes **OU** pas de nouvelle
   direction depuis > 60 jours.
5. **Analyses** : aucune phase inachevee, pas de script en erreur, pas
   de resultats partiels.
6. **Activite** : derniere entree cahier > 90 jours ET conclut
   positivement (pas de "bloque", pas de "a reprendre").
7. **Consolidation** (**critere bloquant**) : aucun fait central n'est
   marque `volatile`, `fragile`, ou `hypothetique` sans documentation
   explicite des hypotheses et de l'amplitude de variation dans le
   manuscrit. Tous les chiffres cites dans le manuscrit sont `etabli`
   ou `convergent`, ou bien la fragilite est explicitement discutee
   dans la section "Limitations" de l'article.

**Si verdict bouclee** : le declarer en tete du bilan. Ne PAS proposer
d'analyses -- se contenter d'une breve section "Pour archivage" listant
les livrables finaux.

**Sinon (verdict "a poursuivre")** : lister explicitement quels criteres
manquent, puis presenter les pistes hierarchisees. Si seul le critere 7
manque, le bilan le signale au sommet : **"Projet quasi-boucle, mais les
faits suivants restent fragiles -- consolidation requise avant cloture
serieuse."**

---

## Phase 9 -- Redaction et persistance (Markdown + PDF + Beamer)

Le bilan est produit en **trois formats**, **tous obligatoires** :

1. **Markdown** (`YYYY-MM-DD_bilan.md`) -- source unique, editable,
   versionnable.
2. **PDF** (`YYYY-MM-DD_bilan.pdf`) -- rendu de lecture, compile via
   pandoc + xelatex avec le template `bilan.latex`. **Toujours genere
   dans la meme passe que le Markdown.**
3. **Beamer** (`YYYY-MM-DD_bilan_slides.pdf` + `.tex`) -- support de
   reunion / seminaire, compile via xelatex avec le template
   `bilan_slides.tex`.

**Regle de completude** : un bilan n'est pas considere comme livre tant
que les trois fichiers ne sont pas presents dans `<projet>/bilans/`. En
particulier, **produire le Markdown sans generer le PDF est une livraison
incomplete** : le PDF est la forme exploitable du bilan (mise en page,
encadres pedagogiques colores, figures inserees correctement, table des
matieres) et c'est generalement ce que l'utilisateur ouvre en premier.
Si la compilation pandoc/xelatex echoue, ne pas abandonner silencieusement :
signaler l'erreur, conserver le Markdown, et indiquer dans l'epilogue
console la commande exacte permettant de relancer manuellement la
compilation apres correction.

L'epilogue console (Phase 9.5) doit lister explicitement les trois
chemins generes, avec la taille de chaque fichier.

### 9.1 Ecriture du Markdown

1. Creer `<projet>/bilans/` si absent (mkdir -p).
2. Nom du fichier : `YYYY-MM-DD_bilan.md` (date du jour).
3. Si un fichier du meme jour existe deja : suffixer `_v2`, `_v3`...
4. **YAML frontmatter obligatoire** en tete du fichier Markdown. Ce
   frontmatter alimente la page de titre du PDF :

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

5. Ecrire le bilan en suivant le template ci-dessous (section "Template
   du bilan produit"). L'ordre canonique des sections est :
   Identite, Verdict synthetique, Etat des connaissances avant ce projet,
   **Etat actuel des connaissances acquises** (section centrale),
   **Apercu chronologique** (court), Decouvertes majeures et leur
   signification, Donnees et analyses : etat des lieux, Etat du
   manuscrit, Paysage de la litterature, **A faire maintenant**
   (intentions memorisees non honorees), Pistes d'approfondissement
   (nouvelles directions), Convergences inter-projets, Limites et
   biais, Anomalies detectees, Plan d'action pour la prochaine session.
6. **Les sections du bilan utilisent `##` (h2) comme niveau principal**,
   `###` (h3) pour les sous-sections. Ne PAS utiliser `#` (h1) dans le
   corps — le h1 est reserve au titre genere par le frontmatter.

7. **Relecture avant ecriture** : le bilan est-il narratif et
   pedagogue ? Chaque section contient-elle au moins un paragraphe de
   prose ? Les decouvertes sont-elles reliees a la litterature ? Si le
   bilan ressemble a une liste d'items, le reecrire.

8. **Check d'autonomie (standalone)** : avant de fermer le fichier,
   grep le document pour les expressions interdites :

   ```bash
   grep -niE 'bilan (precedent|anterieur|v[0-9])|comme deja|comme indique|comme vu|depuis (le|la) derniere?|delta par rapport|changelog|version (precedente|anterieure)|voir bilan|cf\.\s*bilan|rien de neuf' bilans/YYYY-MM-DD_bilan.md
   ```

   Si le grep retourne quoi que ce soit : **reecrire les passages
   incrimines en prose autonome**. Aucun renvoi a une version
   anterieure du bilan ne doit subsister. Une connaissance qui
   apparaissait deja dans un bilan precedent est reformulee
   integralement, sans cette mention.

9. **Inserer les encadres pedagogiques** identifies en Phase 4.6
   (voir section 9.1bis ci-dessous).

### 9.1bis Insertion des encadres pedagogiques

Le template PDF (`templates/bilan.latex`) definit trois environnements
`tcolorbox` dedies, et le template Beamer (`templates/bilan_slides.tex`)
definit trois commandes equivalentes. Ces encadres permettent
d'expliquer, sans rompre la narration, les notions opaques pour un
lecteur de formation math pure / info de base.

#### Cinq types d'encadres

| Type | Usage | Couleur |
|------|-------|---------|
| `notion` | Concept de domaine (ethno-linguistique, biologie, geographie, MTBC...) | Bleu |
| `methode` | Technique statistique, algorithmique, ou methodologique (test de Mantel, ABC, datation moleculaire...) | Vert |
| `originalite` | En quoi un resultat est nouveau / original / novateur **par rapport a la litterature existante** | Violet |
| `remarquable` | Pourquoi un resultat est frappant / impressionnant / non trivial **dans l'absolu**, en quoi un non-specialiste devrait y preter attention | Ambre |
| `fragilite` | Pourquoi un fait `volatile` ou `fragile` (Phase 1bis) ne peut pas etre cite tel quel : amplitude de variation, hypotheses critiques, voies de consolidation. **Obligatoire** pour tout fait central non-`etabli`. | Rouge / orange |

**Distinction `originalite` vs `remarquable`** : ce sont deux dimensions
distinctes, qui peuvent coexister sur un meme resultat.
- `originalite` repond a : *qu'apporte ce resultat que la litterature ne
  contient pas deja ?* C'est une comparaison externe, ancree dans
  references publiees.
- `remarquable` repond a : *pourquoi ce chiffre, ce pattern, cette
  observation est frappant en soi, qu'est-ce qui devrait surprendre ou
  interpeller un lecteur non specialiste ?* C'est une mise en relief
  pedagogique de l'amplitude, de la precision, de la rarete, ou des
  consequences du resultat.

Exemples illustrant la difference :
- *"57 SNP retro-mutes detectes dans L4.9"* → un encadre `remarquable`
  explique pourquoi 57 est un grand nombre (les SNP MTBC sont reputes
  irreversibles a l'echelle d'une lignee, on s'attend a 0-2 retro-mutations
  par hasard sur ce volume de donnees ; 57 est 30 fois plus eleve que la
  borne attendue) ; et un encadre `originalite` explique que la
  reversibilite n'avait jamais ete quantifiee a cette echelle dans la
  litterature MTBC.
- *"Datation MRCA de proto-L4.2 a 1240 CE [IC95 : 980-1430]"* →
  `remarquable` peut souligner la precision de l'intervalle et le fait
  que cela situe l'emergence avant les premiers contacts coloniaux,
  contrairement a l'intuition ; `originalite` peut souligner que c'est la
  premiere datation publiee de cette sous-lignee.

Un resultat peut etre `remarquable` sans etre tres `original` (confirmation
d'un pattern attendu, mais avec une amplitude saisissante) et inversement
(premiere mesure publiee, mais sans surprise particuliere). Quand le
resultat est a la fois remarquable ET original, mettre **les deux
encadres** -- ils ne se substituent pas l'un a l'autre.

#### Syntaxe Markdown (rendu PDF)

Inserer les encadres via des **blocs raw LaTeX** pandoc. La syntaxe
` ```{=latex} ` indique a pandoc de passer le contenu tel quel au moteur
LaTeX (sans tenter de l'interpreter comme du Markdown).

````markdown
```{=latex}
\begin{notion}[Bantu et Kwa : familles linguistiques d'Afrique de l'Ouest]
Les langues bantoues (Niger-Congo, branche bantoue) sont parlees par
environ 350 millions de personnes en Afrique sub-saharienne, depuis le
Cameroun jusqu'a l'Afrique du Sud. Les langues kwa (Niger-Congo, branche
kwa) sont parlees plus au nord, principalement en Cote d'Ivoire, au Ghana,
au Togo et au Benin (Akan, Ewe, Yoruba...).

L'expansion bantoue (debutee il y a ~3000-5000 ans depuis la frontiere
Cameroun-Nigeria) est l'un des evenements demographiques majeurs de
l'histoire humaine recente : elle a remodele en profondeur la structure
genetique des populations subsahariennes. Les groupes humains coevoluant
avec les ecotypes MTBC L5 et L6 (West-African 1 et 2) sont
majoritairement de langue kwa et bantoue, ce qui rend la correlation
genetique humaine / lignee MTBC particulierement informative dans cette
region. La distinction Bantu/Kwa structure ainsi les analyses
phylogeographiques de L5/L6 a un niveau plus fin que la simple
geographie.

\textit{Reference de vulgarisation : Pakendorf et al., 2011, Trends in
Genetics ; Patin et al., 2017, Science.}
\end{notion}
```
````

Autre exemple, encadre methode :

````markdown
```{=latex}
\begin{methode}[Test de Mantel partiel]
Le test de Mantel (Mantel, 1967) compare deux matrices de distances
calculees sur les memes objets : par exemple, une matrice de distances
genetiques entre souches MTBC, et une matrice de distances geographiques
entre les lieux de prelevement. Il calcule la correlation entre les
elements correspondants des deux matrices, et evalue sa significativite
par permutations (typiquement 9999) -- les permutations etant necessaires
parce que les elements d'une matrice de distances ne sont pas
independants.

Le \textit{Mantel partiel} (Smouse et al., 1986) etend cela en
controlant pour une troisieme matrice. Question typique : la correlation
genetique-langue persiste-t-elle apres avoir controle pour la geographie ?
Si oui, c'est un argument pour une coevolution culture-pathogene
au-dela de la simple proximite spatiale.

\textbf{Limites} : le test de Mantel est puissant pour detecter des
patterns globaux mais peu sensible aux structures locales. Il a aussi
une puissance statistique reduite par rapport aux methodes plus modernes
(MMRR, dbRDA), et ses p-values peuvent etre instables sur petits
echantillons. Quand un effet est detecte par Mantel partiel, il est
generalement reel ; quand il ne l'est pas, ca ne prouve rien.
\end{methode}
```
````

Autre exemple, encadre remarquable :

````markdown
```{=latex}
\begin{remarquable}[57 SNP retro-mutes dans L4.9 : un signal 30 fois au-dessus du bruit]
Pour comprendre pourquoi ce chiffre est frappant : un SNP est une
mutation ponctuelle (un nucleotide change) qui, une fois fixee dans une
lignee, est consideree comme \textit{irreversible} a l'echelle de
quelques milliers d'annees -- c'est le postulat fondateur sur lequel
repose toute la phylogenie SNP de MTBC. Sur un corpus de 1200 souches
L4.9, en supposant un taux d'erreur de sequencage de l'ordre de
$10^{-6}$ par base et le postulat d'irreversibilite, on s'attend a
detecter \textbf{0 a 2 reversions par hasard}.

Or, ce projet en detecte \textbf{57}, soit un ordre de grandeur
au-dessus de toute attente. Ce n'est pas un effet marginal : c'est un
signal massif qui exige une explication biologique. Les hypotheses en
lice (selection convergente sur certains genes, hot-spots mutationnels,
biais d'alignement contre H37Rv) ont chacune des consequences
differentes pour l'usage du barcode SNP en epidemiologie moleculaire.

Concretement, si une fraction non negligeable des SNP utilises pour
typer les souches MTBC dans les hopitaux peut retromuter, alors
certaines souches classees comme appartenant a une lignee donnee
pourraient en realite avoir reverti depuis une autre. Les consequences
diagnostiques sont potentiellement importantes -- d'ou l'interet d'aller
au bout de cette analyse.
\end{remarquable}
```
````

Autre exemple, encadre originalite :

````markdown
```{=latex}
\begin{originalite}[Premiere caracterisation phylogeographique de proto-L4.2 a l'echelle mondiale]
Les sous-lignees L4.2 avaient ete decrites par Coll et al. (2014) sur
la base de 6 souches d'Europe occidentale. Aucune etude posterieure
n'avait elargi l'echantillonnage : la lignee restait definie par 91 SNP
sur un corpus de reference qui ne capturait pas sa diversite reelle.

Ce projet apporte la premiere caracterisation a l'echelle mondiale de
proto-L4.2, sur un corpus de 412 souches reparties sur 23 pays. Il
montre que (i) la lignee a une diversite phylogeographique bien plus
riche que ce qu'indiquait l'echantillonnage initial, (ii) 28 marqueurs
SNP supplementaires sont exclusifs a proto-L4.2 et permettent un
diagnostic moleculaire plus robuste, (iii) la distribution geographique
suggere une origine est-mediterraneenne et non ouest-europeenne comme
suppose initialement.

C'est typiquement le genre de resultat qui ne pouvait pas emerger sans
acces a une base de donnees genomique mondiale -- d'ou l'apport
specifique de ce projet, qui s'appuie sur l'agregation TBannotator.
\end{originalite}
```
````

Autre exemple, encadre fragilite (a inserer apres chaque fait central
classe `volatile` ou `fragile` en Phase 1bis) :

````markdown
```{=latex}
\begin{fragilite}[Datation du MRCA proto-L4.2 : un chiffre qui ne tient pas]
La valeur centrale de 1240 CE retenue dans le bilan provient de LSD2
sur un arbre RAxML-NG (GTR+G, calibration par dates de prelevement). Or
trois methodes alternatives appliquees aux memes donnees donnent des
valeurs sensiblement differentes :

\begin{itemize}
\item BEAST tip-dating, horloge stricte : 1110 CE [IC95 980-1240]
\item BEAST node-dating, calibration fossile : 1340 CE [IC95 1230-1450]
\item LSD2 (la valeur retenue) : 1240 CE
\end{itemize}

L'amplitude inter-methodes est de \textbf{260 ans}, soit beaucoup plus
que les IC95 individuels. Le \textit{pattern qualitatif} -- emergence
anterieure aux contacts coloniaux -- est stable, mais le chiffre exact
ne peut pas etre cite tel quel dans un manuscrit sans precaution.

\textbf{Hypotheses critiques} : (i) horloge moleculaire stricte
(LSD2 et BEAST tip-dating l'imposent), (ii) absence de structure de
population sous-jacente non modelisee, (iii) representativite de
l'echantillonnage temporel.

\textbf{Voies de consolidation} :
(1) BEAST avec horloge relaxee + calibration combinee
(\texttt{/molecular-clock}) ;
(2) tip-dating sur sous-echantillonnages stratifies (jackknife) pour
borner la sensibilite empirique ;
(3) comparaison croisee avec proto-L4.2 d'autres etudes si elles
existent (\texttt{/lit-review datation L4}).
\textit{Cf. section "A faire maintenant", item "Datation BEAST horloge relaxee".}
\end{fragilite}
```
````

**Note sur le template LaTeX** : tant que `templates/bilan.latex` ne
definit pas formellement l'environnement `fragilite`, recycler
provisoirement un environnement existant (par exemple `remarquable` avec
un titre commencant par "Fragilite :") ou definir un `tcolorbox` ad hoc
en preambule. La couleur cible est rouge-orange (`!RedOrange` ou
`colback=red!5!white,colframe=red!75!black`). L'ajout formel de
`\newtcolorbox{fragilite}` est une evolution future du template.

Syntaxe Beamer equivalente (a ajouter au template `bilan_slides.tex`) :

```latex
\fragilite{MRCA proto-L4.2 : volatile}{Valeur centrale 1240 CE (LSD2),
  mais 1110-1340 CE selon la methode. Pattern qualitatif stable
  (pre-colonial), chiffre exact non citable. A consolider par BEAST
  horloge relaxee.}
```

#### Regles d'insertion

1. **Au fil du texte, pas en annexe** : un encadre est insere a la
   premiere occurrence du concept dans le bilan, jamais regroupe en
   "glossaire" en fin de document. L'idee est qu'au moment ou le lecteur
   rencontre un terme inconnu, l'explication est a portee de regard.

2. **Une seule fois par concept** : ne pas redefinir Mantel partiel
   trois fois. La premiere occurrence dans le bilan recoit l'encadre.

3. **Heavy explanations** : 4-12 phrases par encadre est la cible
   normale. Mieux vaut un encadre dense et complet qu'un encadre
   superficiel qui n'apporte rien. Inclure systematiquement :
   - **Quoi** : definition simple mais precise
   - **Pourquoi c'est utilise ici** : lien explicite avec le projet
   - **Limites / nuances** : ce qu'il faut savoir pour ne pas
     surinterpreter
   - **Reference** : article ou ouvrage de vulgarisation

4. **Simple sans etre simpliste** : ne pas dire "Mantel mesure une
   correlation" et s'arreter la. Mais ne pas non plus rentrer dans la
   theorie complete des U-statistiques. Donner l'intuition + un niveau
   de detail suffisant pour que le lecteur puisse en parler.

5. **Encadres `originalite` : un par decouverte majeure** au minimum.
   Dans la section "Decouvertes majeures et leur signification", chaque
   sous-section doit avoir son encadre `originalite` qui dit en quoi
   ce resultat est nouveau / non trivial / important par rapport a
   l'existant. C'est ce que le specialiste considere evident et que
   le profil math/info ne peut pas evaluer seul.

5bis. **Encadres `remarquable` : pour chaque resultat frappant en soi**.
   Independamment de la litterature, certains resultats meritent qu'on
   explique pourquoi ils impressionnent : amplitude inattendue, precision
   exceptionnelle, rarete d'un phenomene, contre-intuition par rapport au
   sens commun, consequences pratiques importantes. L'encadre
   `remarquable` rend ces dimensions visibles a un lecteur non
   specialiste, qui ne peut pas evaluer seul si "57 retro-mutations" ou
   "datation a 1240 CE" est banal ou extraordinaire.

   Tous les resultats du projet n'ont pas vocation a etre `remarquable` :
   reserver cet encadre aux resultats genuinement saisissants. **Cible :
   3 a 6 encadres `remarquable` par bilan**, pas un par decouverte. Si
   tout est remarquable, rien ne l'est.

   Un meme resultat peut recevoir a la fois `originalite` et
   `remarquable` quand les deux dimensions s'appliquent (cf. distinction
   plus haut). Structure type d'un encadre `remarquable` :
   (i) rappel de ce a quoi on s'attend (ordre de grandeur, intuition,
   borne theorique) ;
   (ii) ce qui est observe ;
   (iii) le ratio ou le contraste qui rend la chose frappante ;
   (iv) la consequence pratique ou conceptuelle.

6. **Encadres `methode` : un par technique non triviale**. Pour chaque
   methode statistique ou phylogenetique mentionnee dans le bilan
   (Mantel, ABC, BEAST, dN/dS, IQ-TREE+LSD2, PastML...), un encadre
   `methode` la premiere fois qu'elle apparait.

7. **Encadres `notion` : couvrir A-F de la Phase 4.6**. Passer en revue
   les six categories et inserer un encadre pour chaque concept present
   dans le projet et non maitrise par un profil math/info pure.

#### Syntaxe pour les slides Beamer

Dans le fichier `bilan_slides.tex`, utiliser les commandes definies
dans le template :

```latex
\notion{Bantu et Kwa}{Familles linguistiques d'Afrique de l'Ouest.
  Les langues bantoues s'etendent du Cameroun a l'Afrique du Sud
  (~350 M locuteurs). L'expansion bantoue (-3000 ans) a remodele
  la genetique humaine subsaharienne et structure la coevolution
  avec MTBC L5/L6.}

\methode{Test de Mantel partiel}{Compare deux matrices de distances
  en controlant pour une troisieme. Permutations pour la
  significativite. Utile pour tester correlation genetique-langue
  apres controle de la geographie.}

\nouveau{Premiere caracterisation mondiale de proto-L4.2}{Coll 2014
  decrivait la lignee sur 6 souches europeennes. Ce projet l'etend
  a 412 souches sur 23 pays, decouvre 28 SNP marqueurs
  supplementaires, et reoriente l'origine geographique suppose.}
```

**Regle slides** : sur les slides, les encadres sont plus courts (3-5
lignes max). Privilegier 1-2 encadres par slide pertinent, jamais plus.
Les explications detaillees vont dans le PDF, pas dans les slides.

### 9.1ter Cartes, schemas et figures

Un bilan n'est pas un texte plat. Les visuels (cartes, schemas
mecanistiques, chronologies, arbres simplifies, diagrammes conceptuels)
ameliorent significativement la comprehension d'un lecteur de formation
math/info, qui ne dispose pas des images mentales que le specialiste
forme spontanement.

**Principe** : ne pas hesiter a piocher dans le materiel de l'article ET
a generer des visuels de novo specifiquement pour le bilan. Les figures
de l'article sont concues pour un public expert ; le bilan a besoin en
plus de figures pedagogiques (cartes situant la lignee, schemas du
mecanisme biologique invoque, chronologies replacant l'etude dans
l'histoire de la litterature...).

**Cible quantitative** : 4 a 10 visuels par bilan, dont au minimum
**2 generes specifiquement** pour le bilan (au-dela de la simple
reutilisation de l'article). Si le projet a une dimension geographique
(distribution mondiale, regionale, ou GPS), **au moins une carte
produite via `geo-map`** est obligatoire -- une carte schematique TikZ
ne remplace pas une vraie carte cartographique pour discuter
distribution de lignee, foyer ancestral, ou flux phylogeographiques.

#### A. Reutilisation des figures de l'article

Les templates definissent un `\graphicspath` qui inclut
`../article/figures/`, `../resultats/`, et `./figures/` (relatif au
fichier `.md` du bilan). On peut donc inclure directement par le nom de
fichier (sans le chemin) :

````markdown
```{=latex}
\begin{figure}[H]
  \centering
  \includegraphics[width=0.85\textwidth]{phylogeo_L4_2.pdf}
  \caption{Distribution geographique de proto-L4.2 (412 souches,
    23 pays). Les couleurs codent les sous-clades identifies par
    \textit{clade-finder}. Reproduit de l'article (figure 2).}
  \label{fig:bilan-phylogeo}
\end{figure}
```
````

Selectionner pour le bilan :
- 1-2 figures cles de l'article qui resument visuellement les
  decouvertes principales
- Les figures qui appellent une explication pedagogique (souvent celles
  qu'un reviewer demanderait de simplifier)

Ne pas reproduire mecaniquement TOUTES les figures de l'article -- le
bilan est une selection commentee, pas un duplicata.

#### B. Generation de novo : carte de situation

Quand le projet implique une dimension geographique (lignees regionales,
ecotypes, distribution de souches), une carte aide enormement. **Le
mode par defaut est l'appel au skill `geo-map`** : il produit des
cartes Natural Earth en projection cartographique correcte (Robinson,
Albers, Lambert selon la region), avec ocean, lacs, frontieres, barre
d'echelle, et palette MTBC standardisee. La carte schematique TikZ ne
sert qu'en cas de fallback (pas de donnees geocodees disponibles, ou
besoin tres simplifie).

**Appel canonique a `geo-map` depuis le bilan** :

1. Extraire les donnees du cahier ou des BDD en CSV minimal :
   `country,n` ou `country,lineage,n` ou `lat,lon,lineage`.
2. Lancer `geo-map` en mode approprie, sortie en PDF vectoriel place
   dans `<projet>/bilans/figures/` (creer le dossier si absent) :

   ```bash
   # Cas typique : distribution mondiale d'une lignee
   python3 ~/.../bio/skills/geo-map/scripts/geo_map.py \
     bilans/data/proto-L4.2-countries.csv \
     -t choropleth -v n --log-scale \
     --region world --preset generic \
     --insets auto --smart-labels fast \
     --title "Distribution mondiale de proto-L4.2 (412 souches, 23 pays)" \
     -o bilans/figures/fig-distrib-mondiale.pdf

   # Cas regional avec relief : L5 en Afrique
   python3 ~/.../bio/skills/geo-map/scripts/geo_map.py \
     bilans/data/L5-africa.csv -t choropleth -v n \
     --region africa --hillshade --show-tropics \
     --title "L5 en Afrique sub-saharienne" \
     -o bilans/figures/fig-L5-afrique.pdf

   # Sites d'echantillonnage GPS par sous-lignee
   python3 ~/.../bio/skills/geo-map/scripts/geo_map.py \
     bilans/data/samples-gps.csv -t points \
     --lat-col lat --lon-col lon -g sublineage \
     --region southeast_asia --show-cities --min-pop 2000000 \
     --title "Sites d'echantillonnage L1 -- Asie du Sud-Est" \
     -o bilans/figures/fig-samples-l1.pdf
   ```

3. Inclure le PDF generemnt dans le bilan via `\includegraphics`,
   avec une caption argumentee (3-5 lignes) qui explique ce que le
   lecteur doit y voir et pourquoi.

**Cas ou `geo-map` est l'appel correct** :

- Distribution d'une lignee par pays (choropleth).
- Composition en sous-lignees par pays (pie chart map).
- Sites d'echantillonnage GPS individuels (points).
- Flux phylogeographiques entre regions (arcs, ex : reconstruction
  BEAST 2 discrete trait).
- Comparaison entre lignees / periodes (multi-panel facet).
- Composition complexe (choropleth + points + arcs en `layered`).

**Fallback TikZ schematique** : reserve aux cas ou aucune donnee
geocodee n'existe (ex : carte purement illustrative d'un texte ancien)
ou ou un effet stylistique simplifie est volontairement recherche.
Quand on l'utilise, le mentionner explicitement dans la caption
("Carte schematique, non a l'echelle.").

**Exemple TikZ de fallback** (Afrique avec bulles) :

````markdown
```{=latex}
\begin{figure}[H]
\centering
\begin{tikzpicture}[scale=0.9]
  % Contour simplifie de l'Afrique (polygone schematique)
  \draw[fill=lightgray!40, draw=darkgray, thick]
    (0,0) -- (2,0.3) -- (3.5,0) -- (4,1.5) -- (4.5,3) --
    (4,4.5) -- (3,5.5) -- (1.5,5.8) -- (0,5) --
    (-0.5,3.5) -- (-0.5,1.5) -- cycle;
  % Repere lat/lon approximatif
  \node[font=\tiny, midgray] at (3.5,4.8) {N};
  \node[font=\tiny, midgray] at (-0.3,0.3) {S};
  % Pays cles (positions schematiques)
  \node[font=\scriptsize, darkgray] at (1.0,4.5) {Senegal};
  \node[font=\scriptsize, darkgray] at (1.7,3.8) {Mali};
  \node[font=\scriptsize, darkgray] at (2.4,3.5) {Burkina};
  \node[font=\scriptsize, darkgray] at (3.0,3.2) {Nigeria};
  \node[font=\scriptsize, darkgray] at (3.5,2.0) {RDC};
  \node[font=\scriptsize, darkgray] at (3.0,0.5) {Afrique du Sud};
  % Bulles : taille proportionnelle au nombre de souches
  \fill[notioncolor, opacity=0.55] (1.2,4.4) circle (8pt);
  \fill[notioncolor, opacity=0.55] (1.8,3.7) circle (12pt);
  \fill[notioncolor, opacity=0.55] (2.5,3.5) circle (6pt);
  \fill[notioncolor, opacity=0.55] (3.1,3.1) circle (15pt);
  % Legende
  \node[font=\footnotesize, anchor=north west]
    at (5.5,5) {\textbf{N souches L5}};
  \fill[notioncolor, opacity=0.55] (5.7,4.2) circle (4pt);
  \node[font=\scriptsize, anchor=west] at (6,4.2) {< 10};
  \fill[notioncolor, opacity=0.55] (5.7,3.6) circle (8pt);
  \node[font=\scriptsize, anchor=west] at (6,3.6) {10--50};
  \fill[notioncolor, opacity=0.55] (5.7,3.0) circle (12pt);
  \node[font=\scriptsize, anchor=west] at (6,3.0) {50--150};
\end{tikzpicture}
\caption{Distribution schematique des souches L5 dans le corpus.
  Les bulles sont proportionnelles au nombre de souches par pays.
  Carte simplifiee, non a l'echelle.}
\label{fig:bilan-carte-l5}
\end{figure}
```
````

**Carte plus precise** : si le projet a un fichier shapefile ou des
coordonnees lat/lon, prefer un `pgfplots` avec `axis equal` et un
nuage de points sur fond uni, ou inclure directement une figure
generee par python (`cartopy`, `geopandas`) si elle est dans
`resultats/` ou `article/figures/`.

**Quand generer une carte de novo** : a chaque fois que la dimension
geographique est evoquee dans le bilan ET qu'aucune carte similaire
n'existe deja dans `article/figures/`. Une simple carte avec 5-10
labels de pays et des bulles aide enormement le lecteur a se reperer.

#### C. Generation de novo : schema de mecanisme biologique

Quand un mecanisme est invoque (selection convergente, retro-mutation,
goulot demographique, transmission inter-hote), un schema TikZ
synthetique vaut mieux qu'un long paragraphe.

````markdown
```{=latex}
\begin{figure}[H]
\centering
\begin{tikzpicture}[
  node distance=1.2cm,
  state/.style={circle, draw=darkgray, fill=lightgray!40,
                minimum size=8mm, font=\small},
  arr/.style={-{Stealth[length=4pt]}, thick}
]
  \node[state] (anc) {A};
  \node[state, right=of anc, fill=notioncolor!20] (mut) {C};
  \node[state, right=of mut, fill=remarquablecolor!30] (rev) {A};
  \draw[arr] (anc) -- node[above, font=\scriptsize]{mutation} (mut);
  \draw[arr, dashed, remarquablecolor] (mut) -- node[above, font=\scriptsize]
    {\textbf{retro-mutation}} (rev);
  \node[font=\scriptsize, midgray, below=4mm of anc]
    {ancetre commun};
  \node[font=\scriptsize, midgray, below=4mm of mut]
    {fixation chez L4.9};
  \node[font=\scriptsize, midgray, below=4mm of rev]
    {retour a l'etat ancestral};
\end{tikzpicture}
\caption{Schema d'une retro-mutation : un SNP fixe (A$\to$C) revient a
  l'etat ancestral (C$\to$A) dans un sous-clade ulterieur. Ce phenomene
  est suppose extremement rare en MTBC du fait de la clonalite et du
  faible taux de mutation.}
\label{fig:bilan-retromutation}
\end{figure}
```
````

#### D. Generation de novo : chronologie / timeline

Pour replacer l'etude dans son contexte historique (decouvertes
successives sur la lignee, evenements demographiques, jalons
methodologiques) :

````markdown
```{=latex}
\begin{figure}[H]
\centering
\begin{tikzpicture}[
  evt/.style={font=\scriptsize, anchor=south, align=center},
  ref/.style={font=\tiny, anchor=north, midgray}
]
  % Axe temps
  \draw[->, thick, accent] (0,0) -- (12,0)
    node[right, font=\small] {temps};
  % Graduations
  \foreach \x/\y in {1/2014, 3/2017, 5/2020, 7/2022, 9/2024, 11/2026} {
    \draw (\x,0.1) -- (\x,-0.1) node[ref]{\y};
  }
  % Evenements (au-dessus)
  \node[evt] at (1,0.2) {Coll \textit{et al.}\\barcode L4};
  \node[evt] at (3,0.2) {Stucki\\dual epidemic};
  \node[evt] at (5,0.2) {Napier\\refinement};
  \node[evt] at (7,0.2) {Freschi\\global tree};
  \node[evt, accent] at (9.5,0.2) {\textbf{Ce projet}\\proto-L4.2 mondiale};
  % Repere visuel sur le projet courant
  \fill[accent] (9.5,0) circle (3pt);
\end{tikzpicture}
\caption{Chronologie des travaux majeurs sur la lignee L4 et
  positionnement de ce projet dans la litterature.}
\label{fig:bilan-chronologie}
\end{figure}
```
````

#### E. Generation de novo : arbre simplifie

Pour illustrer la position d'une lignee dans l'arbre MTBC, ou la
structure interne d'un sous-clade, un arbre TikZ simplifie est plus
lisible qu'un arbre Newick brut.

Utiliser le style `child` natif de TikZ ou la bibliotheque `forest`
si elle est chargee.

````markdown
```{=latex}
\begin{figure}[H]
\centering
\begin{tikzpicture}[
  level distance=12mm,
  level 1/.style={sibling distance=22mm},
  level 2/.style={sibling distance=10mm},
  every node/.style={font=\scriptsize, draw=darkgray,
                     rounded corners=2pt, inner sep=2pt}
]
\node {MTBC}
  child {node {L1-L4 (modern)}
    child {node[fill=accent!15]{\textbf{L4}}}
    child {node {L2}}
    child {node {L1}}
  }
  child {node[fill=notioncolor!15]{\textbf{L5-L6} (West-African)}}
  child {node {L7-L10}}
  child {node {animal-adapted\\(\textit{M. bovis}, \textit{M. caprae}...)}};
\end{tikzpicture}
\caption{Position de la lignee etudiee dans l'arbre MTBC simplifie.
  Adapte de Brites \& Gagneux (2017).}
\label{fig:bilan-arbre-mtbc}
\end{figure}
```
````

#### F. Choix entre reutilisation et generation

| Cas | Action |
|-----|--------|
| L'article a deja une figure qui couvre le point | **Reutiliser** via `\includegraphics` |
| L'article a une figure complexe que le lecteur math/info pourrait mal interpreter | Reutiliser **+ ajouter un schema simplifie** generemnt de novo a cote |
| Le point est purement pedagogique (mecanisme, contexte historique, position dans l'arbre MTBC) | **Generer de novo** en TikZ |
| Carte de situation geographique (pays / regions / GPS / flux) | **Appeler `geo-map`** (skill, sortie PDF vectoriel) -- voir B |
| Visualisation chiffree generique (scatter, histo, barplot) | **Appeler `seaborn`** (skill) si pas dans `resultats/`, sinon reutiliser |
| Visualisation composite ou non standard (heatmap multi-panel, violin par lignee, courbe ROC...) | **Appeler `create-viz`** (skill, sortie PDF) |
| Arbre phylogenetique simplifie illustratif | TikZ natif (voir E) ou skill `iqtree-lsd2`/`itol` si donnees disponibles |
| Pipeline du projet | Section dediee Phase 9 (deja prevue : TikZ generemnt) |

**Regle generale** : ne jamais reinventer en TikZ schematique ce qu'un
skill d'illustration produit en qualite publication. Les skills
disponibles (canonical dans `bio/skills/`) :

| Skill | Usage typique dans un bilan |
|-------|----------------------------|
| `geo-map` | Toutes les cartes (choropleth, points GPS, arcs, layered, multi-panel) |
| `seaborn` | Distributions, scatter, regplot, barplot, boxplot |
| `create-viz` | Heatmaps, dashboards composites, visualisations sur mesure |
| `itol` | Arbres phylogenetiques annotes |
| `iqtree-lsd2` | Arbres dates (chronogrammes) |

Le bilan **enchaine prose + figures** : a chaque fois qu'un paragraphe
mentionne une donnee qui se visualise mieux qu'elle ne se decrit
(distribution geographique, structure d'arbre, gradient temporel,
distribution numerique), inserer la figure correspondante juste apres
le paragraphe, avec une caption argumentee.

#### G. Regles de qualite

1. **Toute figure a une caption explicative**, pas juste un titre. La
   caption explique ce que le lecteur doit voir et pourquoi c'est
   pertinent (3-5 lignes, pas une simple etiquette).
2. **Toute figure est referencee dans le texte** (`Cf.~\cref{fig:...}`),
   sinon elle ne sert a rien et peut etre supprimee.
3. **Couleurs coherentes** : reutiliser les couleurs definies dans le
   template (`accent`, `notioncolor`, `methodecolor`, `originalitecolor`,
   `remarquablecolor`, `verdictgreen`, `verdictorange`). Ne pas
   introduire de nouvelles couleurs.
4. **Cartes de novo** : preciser explicitement dans la caption que la
   carte est schematique (non a l'echelle), pour eviter toute
   surinterpretation.
5. **Eviter les fichiers raster** sauf si vraiment necessaire (PNG/JPG
   uniquement pour des cartes ou des figures de l'article qui n'existent
   qu'en raster). Privilegier PDF, SVG, et generation TikZ native.
6. **Pas de figures decoratives** : si une figure ne porte pas
   d'information specifique, la supprimer. Le bilan est dense, pas
   illustre.

### 9.2 Generation du PDF (obligatoire dans la meme passe)

**Le PDF n'est pas optionnel** : il est produit systematiquement
immediatement apres le Markdown, dans la meme execution du skill.
Un bilan livre sans PDF compile est une livraison incomplete et doit
etre completee avant de rendre la main a l'utilisateur.

```bash
TEMPLATE=~/Documents/docs/codes/claude_plugins/bio/skills/mtbc-bilan/templates/bilan.latex

pandoc "<projet>/bilans/YYYY-MM-DD_bilan.md" \
  -o "<projet>/bilans/YYYY-MM-DD_bilan.pdf" \
  --template="$TEMPLATE" \
  --pdf-engine=xelatex \
  --shift-heading-level-by=-1 \
  --variable=colorlinks:true
```

- `--shift-heading-level-by=-1` : les `##` du Markdown deviennent des
  `\section{}` dans le PDF (numerotation 1, 2, 3... et non 0.1, 0.2...).
- Le template produit : page de titre coloree, table des matieres,
  en-tetes projet/date, encadre bleu pour le verdict, typographie
  professionnelle.
- **En cas d'echec de compilation** : ne pas perdre le Markdown
  (deja ecrit, on le conserve), mais traiter la situation comme un
  echec partiel a remonter explicitement. La marche a suivre :
  1. Capturer le message d'erreur pandoc / xelatex.
  2. Tenter une correction automatique des causes les plus
     frequentes (caracteres unicode non supportes par la police,
     `\` ou `$` mal echappes, chemin de figure introuvable).
  3. Si la correction est triviale (echappement, encodage), relancer
     immediatement la compilation.
  4. Si l'echec persiste : afficher dans l'epilogue console
     l'erreur exacte et la **commande pandoc complete** permettant a
     l'utilisateur de relancer manuellement apres correction. Ne
     **jamais** declarer le bilan livre quand le PDF manque -- le
     rendu attendu est `MD + PDF + Beamer`, pas `MD seul`.

### 9.3 Pour le mode `--full`

La meme procedure s'applique au bilan global :
- Markdown dans `mtbc/bilans_globaux/YYYY-MM-DD_bilan_global.md`
- PDF dans `mtbc/bilans_globaux/YYYY-MM-DD_bilan_global.pdf`
- Frontmatter adapte :

  ```yaml
  ---
  title: "Bilan global MTBC"
  subtitle: "État de tous les projets au YYYY-MM-DD"
  project: "MTBC (tous projets)"
  date: "YYYY-MM-DD"
  verdict: "<N projets actifs, M prêts à clore>"
  ---
  ```

### 9.4 Generation de la presentation Beamer

Apres le PDF du bilan, generer automatiquement une presentation Beamer
qui synthetise le projet en slides. Cette presentation n'est **pas une
version comprimee du bilan** — c'est une visite guidee de l'etat actuel
des connaissances du projet, structuree en 4 actes (contexte, donnees
et methode, resultats, synthese), avec une logique de presentation
claire (pas un journal chronologique des sessions).

#### 9.4.1 Ecriture du fichier LaTeX

Ecrire `<projet>/bilans/YYYY-MM-DD_bilan_slides.tex` (pas un Markdown
converti — un fichier Beamer LaTeX natif). Le template Metropolis est
dans `bio/skills/mtbc-bilan/templates/bilan_slides.tex` et fournit le
preambule, le theme, et les commandes MTBC (\mtb, \spdi, \lignee, \kb).

**Structure obligatoire des slides** (adapter au contenu reel du bilan) :

```latex
% ── ACTE 1 : CONTEXTE (3-4 slides) ──────────────────────────────
\section{Contexte et objectifs}

% Slide 1 : Pourquoi ce projet ?
\begin{frame}{[Titre : la question scientifique]}
  % La question fondatrice du projet, pas le nom de la lignee.
  % Ex: "Existe-t-il des sous-lignees non-decrites au sein de L4 ?"
  % Pas : "Projet L4.2_proto"
  %
  % Utiliser 3-4 bullets ou un schema TikZ simple.
  % Terminer par un keybox avec la question precise.
  \kb{Question : [question scientifique en une phrase]}
\end{frame}

% Slide 2 : Etat des connaissances
\begin{frame}{Ce que l'on savait avant}
  % Extraire de la section "Etat des connaissances avant ce projet"
  % du bilan. 4-5 points cles, chacun avec la reference (Coll 2014,
  % Napier 2020...). Pas de prose — bullets concis.
\end{frame}

% Slide 3 : Lacunes
\begin{frame}{Ce qui manquait}
  % Extraire de "Lacunes et questions ouvertes" du bilan.
  % 2-3 lacunes cles, formulees comme des questions.
  % Terminer par un keybox : "Ce projet vise a combler [lacune X]"
\end{frame}

% ── ACTE 2 : DONNEES ET METHODE (2-3 slides) ────────────────────
\section{Donn\'ees et m\'ethode}

% Slide 4 : Les donnees
\begin{frame}{Donn\'ees}
  % Nombre de souches, source (TBannotator, SRA), lignee(s),
  % distribution geographique si pertinente.
  % Utiliser un tableau compact ou un columns text+carte.
  % Toujours citer la taille de l'echantillon.
\end{frame}

% Slide 5 : Pipeline
\begin{frame}{Pipeline d'analyse}
  % Schema TikZ du pipeline (reprendre le diagramme du bilan si
  % present, ou en creer un simplifie).
  % Chaque etape = une boite avec outil + statut.
  % Max 6 etapes sur un slide.
\end{frame}

% ── ACTE 3 : RESULTATS (4-8 slides) ─────────────────────────────
\section{R\'esultats}

% Pour chaque decouverte majeure du bilan (section "Decouvertes
% majeures et leur signification"), creer 1 slide :
%
% - Titre = enonce de la decouverte (pas "Resultat 1")
% - Figure si disponible (columns figure+interpretation)
% - 2-3 bullets d'interpretation
% - Keybox avec le take-away
%
% Selectionner les 4-8 resultats les plus marquants.
% Ordre : logique narrative, pas chronologique.

% Slide type resultat avec figure :
%\begin{frame}{[Titre : enonce de la decouverte]}
%\begin{columns}[T,onlytextwidth]
%\begin{column}{0.55\textwidth}
%  \centering
%  \includegraphics[width=\linewidth,height=0.70\textheight,
%    keepaspectratio]{../article/figures/xxx.pdf}
%\end{column}
%\begin{column}{0.42\textwidth}
%  \begin{itemize}\setlength\itemsep{3pt}
%    \item Observation cle
%    \item Interpretation biologique
%    \item Mise en perspective
%  \end{itemize}
%  \kb{Take-home : [message en une phrase]}
%\end{column}
%\end{columns}
%\end{frame}

% Slide type resultat sans figure :
%\begin{frame}{[Titre : enonce de la decouverte]}
%  \begin{itemize}\setlength\itemsep{5pt}
%    \item ...
%  \end{itemize}
%  \kb{[message]}
%\end{frame}

% ── ACTE 4 : SYNTHESE ET PERSPECTIVES (3-4 slides) ──────────────
\section{Synth\`ese et perspectives}

% Slide synthese (LE slide le plus important)
\begin{frame}{Synth\`ese}
  % NE PAS repeter tous les resultats.
  % Presenter l'image integree : qu'est-ce que l'ensemble des
  % resultats nous dit sur la question fondatrice ?
  % Utiliser un schema TikZ, un diagramme, ou 3-4 bullets
  % synthetiques avec keybox finale.
  \kb{Message principal : [la reponse a la question fondatrice]}
\end{frame}

% Slide limites (bref, honnete)
\begin{frame}{Limites}
  % 3-4 bullets : biais echantillonnage, reference H37Rv,
  % couverture geographique... Pas d'auto-flagellation, juste
  % de la transparence.
\end{frame}

% Slide fragilite (obligatoire si des faits centraux sont volatile/fragile)
\begin{frame}{Faits a consolider}
  % Lister les 2-4 faits centraux marques `volatile`/`fragile` en
  % Phase 1bis, avec amplitude / hypothese critique en une ligne
  % et la piste de consolidation en une ligne.
  % Utiliser un encadre \fragilite{} sur le fait le plus important.
  % Si aucun fait fragile : supprimer ce slide.
\end{frame}

% Slide a faire maintenant
\begin{frame}{\`A faire maintenant}
  % Extraire les 3-5 intentions memorisees non honorees les plus
  % importantes (section "A faire maintenant" du bilan).
  % Chaque item = 1 bullet : intention + trace cahier (date) + ce qui
  % manque pour l'executer.
  % Si la liste est vide : le dire et le souligner comme un signe de
  % maturite du projet.
\end{frame}

% Slide perspectives
\begin{frame}{Perspectives}
  % Extraire les 3-5 pistes haute/moyenne priorite (NOUVELLES
  % directions, distinctes des intentions memorisees du slide
  % precedent).
  % Chaque piste = 1 bullet avec justification courte.
  % Si verdict "bouclee" : dire que le projet est termine et
  % mentionner les retombees attendues.
\end{frame}
```

**Regles de redaction des slides** :

1. **Narratif** : chaque slide doit avancer l'histoire. Si un slide
   n'avance pas la narration, le supprimer.
2. **Un message par slide** : si deux idees, deux slides.
3. **Figures d'abord** : si une figure existe dans `article/figures/`
   pour illustrer un resultat, l'utiliser. Le `\graphicspath` du
   template inclut deja `../article/figures/`, `../resultats/` et
   `./figures/`, donc indiquer juste le nom du fichier suffit. Generer
   aussi du materiel de novo (cartes schematiques, schemas mecanistiques,
   chronologies, arbres simplifies) quand aucune figure existante ne
   couvre le point pedagogique. Voir Phase 9.1ter pour les patterns TikZ
   types.
4. **Titres specifiques** : "28 marqueurs SNP exclusifs au proto-L4.2",
   pas "Resultats phylogenetiques".
5. **Max 6 bullets par slide**, max 10 mots par bullet.
6. **Keybox sur chaque slide de resultat** : le take-away en une phrase.
7. **Total** : 12-20 slides de contenu (hors titre et merci). Adapter
   a la richesse du projet — un projet avec 2 resultats = 12 slides,
   un projet riche = 20 slides.
8. **Pipeline en TikZ** : reprendre le diagramme du bilan s'il existe,
   sinon en creer un simplifie (max 6 etapes).
9. **References** : utiliser `\footnote{\tiny Coll et al., 2014}` pour
   les references cles, pas de bibliographie formelle.
10. **Encadres pedagogiques sur les slides** : utiliser les commandes
    `\notion{titre}{contenu}`, `\methode{titre}{contenu}`,
    `\nouveau{titre}{contenu}`, `\remarquable{titre}{contenu}` et
    `\fragilite{titre}{contenu}` (a ajouter au template, couleur
    rouge/orange). Sur les slides, les encadres sont courts (3-5 lignes
    max) -- les explications detaillees vont dans le PDF. Inserer un
    `\nouveau` sur le slide synthese pour resumer en une phrase ce qui
    est nouveau dans ce projet vs la litterature, un `\remarquable` sur
    le slide d'un resultat marquant pour expliciter son amplitude / sa
    precision / son caractere frappant, et un **`\fragilite` sur le
    slide "Faits a consolider"** (et eventuellement sur le slide d'un
    resultat dont la valeur exacte est volatile et qu'on veut quand
    meme presenter).

#### 9.4.2 Compilation

```bash
cd "<projet>/bilans/"
pdflatex -interaction=nonstopmode YYYY-MM-DD_bilan_slides.tex
pdflatex -interaction=nonstopmode YYYY-MM-DD_bilan_slides.tex
```

- Deux passes pour la table des matieres et la numerotation.
- Si la compilation echoue (package manquant, figure introuvable) :
  signaler l'erreur a l'utilisateur, ne pas bloquer le bilan.
  Produire le .tex quand meme.
- Verifier : `grep -c "^!" YYYY-MM-DD_bilan_slides.log` doit etre 0.

#### 9.4.3 Pour le mode `--full`

Pas de slides en mode `--full` — la presentation Beamer n'a de sens
que pour un projet individuel. En mode `--full`, ne generer que le
Markdown + PDF du bilan global.

### 9.5 Affichage console

Apres ecriture, afficher en console un **resume** : identite projet,
verdict argumente, etat consolide des connaissances en 3-5 phrases,
top 3 intentions memorisees non honorees ("A faire maintenant"), top 3
pistes prospectives avec justification.

**Fin du resume console : bilan obligatoire des trois fichiers
livres** sous forme d'un mini-tableau qui confirme leur generation :

```
Fichiers generes :
  Markdown  : <projet>/bilans/YYYY-MM-DD_bilan.md       (<taille>)
  PDF       : <projet>/bilans/YYYY-MM-DD_bilan.pdf      (<taille>)
  Beamer    : <projet>/bilans/YYYY-MM-DD_bilan_slides.pdf (<taille>)
```

Si l'un des trois fichiers manque (compilation echouee, par exemple),
la ligne correspondante affiche `[ECHEC]` suivi de la commande exacte
permettant a l'utilisateur de relancer la compilation. **Ne jamais
omettre une ligne** : si le PDF n'a pas pu etre genere, c'est une
information critique a faire remonter, pas un detail a passer sous
silence.

Voir section "Epilogue" pour le format detaille du resume scientifique.

---

## Template du bilan produit

```markdown
# Bilan projet -- <nom> -- YYYY-MM-DD

## Identite
- **Projet** : <titre depuis CLAUDE.md>
- **Responsable** : Christophe Guyeux (FEMTO-ST)
- **Lignee MTBC** : <...>
- **Cree le** : <date premiere entree cahier>
- **Derniere activite** : <date derniere entree, + delta jours>
- **Chemin** : <absolu>
- **Format cahier** : cahier_de_labo.md | JOURNAL.md | les deux (anomalie)

## Verdict synthetique
> **<bouclee | a poursuivre | actions prioritaires>**
> Criteres de cloture : X/7 (dont critere 7 "consolidation" bloquant ;
> detail en section "Limites et biais").
>
> <Paragraphe de 3-5 phrases justifiant le verdict. Pas un simple
> label mais une appreciation argumentee : pourquoi ce projet est/n'est
> pas termine, quels sont les enjeux restants, quel est le rapport
> effort/gain pour continuer.>

## Etat des connaissances avant ce projet

<Cette section pose le decor scientifique : qu'est-ce que la communaute
savait (et ne savait pas) sur le sujet AVANT que ce projet ne demarre ?
C'est le "Related Work" / "Background" du bilan — sans lui, le lecteur
ne peut pas apprecier la valeur des decouvertes du projet.>

<C'est aussi la section qui contient le plus d'encadres `notion` :
chaque concept de domaine apparaissant pour la premiere fois (lignee,
ecotype, groupe ethnique, methode de typage, etc.) declenche un
encadre. Voir Phase 4.6 et 9.1bis pour la syntaxe.>

<Rediger 3-8 paragraphes de prose continue, structures par sous-themes,
qui couvrent :>

### Ce que la litterature etablissait

<Synthese des connaissances pre-existantes sur la lignee, la methode,
ou le phenomene etudie. Pour chaque fait majeur, citer la reference
(auteur, annee) et expliquer brievement la contribution.>

<Exemples de questions a couvrir selon le type de projet :>
- **Projet sur une lignee** (L4.9, La4, L4.14...) : quand et par qui
  la lignee a-t-elle ete decrite ? Quelle etait sa definition initiale ?
  Combien de souches avaient ete etudiees ? Quelle distribution
  geographique etait connue ? Quels marqueurs definissaient la lignee ?
  Quelles hypotheses existaient sur son evolution ?
- **Projet methodologique** : quelle etait la methode standard avant
  ce projet ? Quelles limites avaient ete identifiees ? Qui avait
  propose des ameliorations ?
- **Projet transversal** (resistance, coevolution...) : quel etait
  l'etat du consensus ? Quelles controverses existaient ?

<Ne pas se contenter de lister les articles — raconter l'histoire de
la connaissance sur ce sujet, en montrant comment les idees se sont
construites les unes sur les autres.>

### Lacunes et questions ouvertes

<Quelles questions restaient sans reponse ? Quelles lacunes avaient
ete identifiees explicitement dans la litterature (ou implicitement
par l'absence de travaux) ? C'est ici que le projet trouve sa
justification scientifique.>

<Exemples : "Aucune etude n'avait analyse la distribution geographique
de L4.9 a l'echelle mondiale — les travaux de Coll et al. (2014) et
Napier et al. (2020) la mentionnent comme sous-lignee de L4 sans la
caracteriser davantage." Ou : "La question de la reversibilite des SNP
chez MTBC avait ete soulevee par [ref] mais jamais quantifiee
systematiquement.">

### References fondatrices

<Tableau des 5-15 articles les plus importants pour comprendre le
contexte du projet. Ce ne sont PAS tous les articles de la
litterature_review — ce sont les references incontournables que
quelqu'un devrait lire pour comprendre d'ou part ce projet.>

| Reference | Annee | Contribution cle pour ce projet |
|-----------|-------|-------------------------------|
| Coll et al. | 2014 | Barcode SNP definissant les lignees MTBC |
| ... | ... | ... |

### Sources pour cette section

Pour construire cette section, le skill doit :

1. **Lire `litterature_review/`** integralement (s'il existe) :
   syntheses, articles cles, lacunes identifiees.
2. **Lire les references de l'article** (`article/*.bib`) pour les
   refs deja citees dans le manuscrit.
3. **Lire le cahier** : les sections "Litterature" et "Connaissances
   acquises" mentionnent souvent des faits de la litterature.
4. **Consulter `~/.claude/knowledge/tuberculosis.md`** pour le
   contexte general MTBC.
5. Si les sources locales sont insuffisantes : le signaler comme
   lacune ("cette section meriterait un `/lit-review --wide` pour
   etre completee").

**Ne JAMAIS inventer de references.** Si une affirmation n'est pas
sourcee par une reference trouvee dans les fichiers du projet ou dans
la base de connaissances, ne pas la faire ou la marquer explicitement
comme "[ref a trouver]".

---

## Etat actuel des connaissances acquises

<C'est la section centrale du bilan. Elle presente, **organisee par
theme** (et non par ordre chronologique de decouverte), l'ensemble des
connaissances actuellement consolidees sur le projet, dans la version
post-consolidation issue de la Phase 1. C'est la **carte stabilisee** de
ce qui est su aujourd'hui.>

<Pour chaque grand theme (typiquement 4-8 selon le projet : structure
phylogenetique, marqueurs definissant la lignee, datation, distribution
geographique, mecanismes evolutifs, resistance, methodologie...), ecrire
une sous-section qui consolide TOUT ce que le projet a etabli sur ce
theme. Une connaissance qui a evolue n'apparait que dans sa version
actuelle ; mentionner l'evolution en une phrase seulement si elle est
instructive (ex : "Apres correction d'un biais d'alignement contre
H37Rv, 38 SNP retro-mutes sont confirmes -- la valeur initiale de 57
incluait des artefacts.").>

<Chaque connaissance acquise est presentee **en prose**, dans une phrase
ou un paragraphe court qui integre simultanement :>

- **L'enonce** : le fait lui-meme, formule de maniere precise et
  autonome (chiffre, identifiant de marqueur, gene, date, region...).
- **La maniere dont il a ete etabli** : la donnee source (nombre de
  souches, BDD), la methode (script, outil, algorithme, modele),
  eventuellement la reference de validation. Ces informations
  s'inserent **dans la phrase** ("identifie sur 412 souches via
  `phase3_subclade_marker.py`"), pas en bloc separe.
- **Le niveau de consolidation** parmi les sept de la Phase 1bis,
  enonce **textuellement dans la phrase** : "aujourd'hui `etabli`",
  "actuellement `volatile`", etc.
- **Pour tout fait non `etabli`** : enchainer dans le paragraphe avec
  l'amplitude de variation observee, ou l'hypothese qui pourrait
  casser, et la piste de consolidation. Pas de format "Fait /
  Volatilite / Consolidation" en sous-blocs : tout cela se dit en
  prose, dans le fil d'un paragraphe argumente.

**Interdiction absolue** dans cette section : les blocs structures
type "> **Fait :** ... > **Methode :** ... > **Consolidation :** ...".
Ce format etait utilise en interne en Phase 1 pour bookkeeper la
consolidation ; il **ne doit jamais apparaitre dans le bilan ecrit**.
Une connaissance se raconte ; elle ne se ficheote pas.

<Voici comment les memes connaissances doivent etre redigees en prose.>

**Exemple narratif -- fait bien consolide** :

> Le sous-clade proto-L4.2, identifie sur 412 souches reparties dans
> 23 pays via `phase3_subclade_marker.py` (BDD `bdd/actuelle/L4/`,
> TBannotator v3.6, critere d'exclusivite >= 95 %), repose sur 28
> marqueurs SNP exclusifs. Le resultat est aujourd'hui `etabli` :
> deux reproductions independantes a un mois d'intervalle, apres
> ajout de souches au corpus, ont restitue exactement les memes
> 28 marqueurs, et le claim-check confirme leur tracabilite jusqu'a
> la BDD source.

**Exemple narratif -- fait volatile** :

> La datation du MRCA de proto-L4.2 reste le point le plus instable
> de l'etude. La methode LSD2 (sur arbre RAxML-NG GTR+G, 1000
> bootstraps, calibration par dates de prelevement) place le MRCA
> aux alentours de 1240 CE, ce qui le situe avant les premiers
> contacts coloniaux europeens-americains : un resultat
> contre-intuitif pour une sous-lignee initialement decrite en
> Europe occidentale. Mais la valeur est `volatile` : BEAST en
> tip-dating donne 1110 CE [IC95 980-1240], et BEAST en node-dating
> avec calibration fossile remonte a 1340 CE [IC95 1230-1450].
> Soit une amplitude inter-methode de 330 ans pour la valeur centrale,
> bien superieure aux intervalles internes a chaque methode. Le
> pattern qualitatif (anteriorite aux contacts coloniaux) est
> robuste, mais le chiffre exact ne peut pas etre cite sans reserve.
> Deux pistes de consolidation existent : refaire BEAST avec une
> horloge relaxee et une calibration combinee (`/molecular-clock`),
> et lancer un tip-dating sur sous-echantillonnage stratifie pour
> evaluer la stabilite empirique (Cf. section "A faire maintenant").

**Exemple narratif -- fait fragile** :

> Le signal d'expansion demographique de L5 au XVIIIe siecle, obtenu
> par skyline BEAST (modele coalescent constant-then-growth,
> calibration par tip-dates), est qualifie de `fragile` parce qu'il
> repose sur trois hypotheses fortes : horloge moleculaire stricte,
> absence de structure de population non modelisee, echantillonnage
> representatif. Or aucune de ces hypotheses n'a ete testee sur les
> sous-populations connues de L5, et la violation de la deuxieme
> peut a elle seule generer un signal d'expansion fictif. Le
> resultat reste cite avec precaution ; sa consolidation passe par
> un refit avec multi-tree skyline et un sous-echantillonnage
> equilibre par region.

**Exemple narratif -- fait hypothetique** :

> L'hypothese actuelle pour expliquer les retro-mutations de L4.9
> est une selection convergente agissant specifiquement sur katG et
> inhA, deux genes cibles d'antibiotiques antituberculeux. Cette
> piste decoule de l'interpretation des resultats de
> `phase5_retromutation.py`, qui montrent une concentration des
> retro-mutations dans ces deux genes, mais elle n'a fait l'objet
> d'aucun test formel : ni dN/dS, ni McDonald-Kreitman. Le statut
> reste donc `hypothetique`, et une alternative reste plausible --
> des hot-spots mutationnels intrinseques aux regions concernees,
> independants de toute pression selective. Trancher entre les deux
> demande un appel au skill `/mk-ascertainment` sur katG et inhA,
> ou une comparaison avec les SNP non retro-mutes des memes genes.

### Themes (a adapter au projet)

#### Structure phylogenetique et clades
<Consolidation des connaissances sur l'arbre, les sous-clades, leur
support, leurs definitions.>

#### Marqueurs et signatures genetiques
<Consolidation des SNP, indels, signatures specifiques etablies par
le projet.>

#### Datation et evolution temporelle
<Si applicable : MRCA, age des clades, signaux de demographie.>

#### Distribution geographique et hote
<Si applicable : phylogeographie, associations ethniques, ecotypes.>

#### Mecanismes biologiques invoques
<Consolidation des hypotheses biologiques en cours : selection,
goulot, retro-mutation, hot-spots mutationnels... avec le statut de
chacune (test fait, en cours, hypothese non testee).>

#### Methodologie etablie par le projet
<Si le projet a developpe un workflow ou un outil reutilisable :
le decrire ici comme une connaissance methodologique acquise.>

<Inserer ici les encadres `notion`, `methode`, `originalite`,
`remarquable`, et `fragilite` selon les regles de la Phase 4.6,
9.1bis, et 1bis. L'etat actuel des connaissances est l'endroit le
plus dense en encadres pedagogiques. **Tout fait central marque
`volatile` ou `fragile` recoit obligatoirement un encadre
`fragilite`** qui explicite l'amplitude / l'hypothese critique et
renvoie a la piste de consolidation.>

## Apercu chronologique

<Section **courte** (4-8 phrases, pas plus) qui resume comment l'etat
de connaissance s'est construit, en ne retenant que les tournants
significatifs. NE PAS rentrer dans le detail des sessions ni de chaque
iteration ; donner les jalons : phase de demarrage, premier resultat
marquant, reorientation eventuelle, decouverte majeure, etat actuel.>

<Exemple de ton :>

> Le projet a demarre en septembre 2025 par un controle qualite des
> donnees TBannotator pour L4 (412 souches retenues). En decembre, la
> phase de typage a fait emerger un sous-clade non decrit dans la
> litterature, ce qui a reoriente l'etude vers la caracterisation de
> proto-L4.2. La datation moleculaire (mars 2026) a place le MRCA au
> XIIIe siecle, et la phylogeographie associee a fait l'objet d'un
> manuscrit soumis en avril 2026. L'etude est aujourd'hui en revision.

<Si une evolution d'une connaissance merite d'etre soulignee (ex :
correction d'un biais qui a divise par deux un effet), le mentionner
en une phrase. Tout le reste de la chronologie detaillee reste dans
le cahier de labo, pas dans le bilan.>

## Decouvertes majeures et leur signification

<Cette section met en relief, parmi l'etat actuel des connaissances
(section "Etat actuel des connaissances acquises"), les decouvertes les
plus significatives. C'est un **zoom commente** sur les 8-10 faits qui
font la valeur scientifique du projet, presentes dans leur **version
consolidee** (post-Phase 1).>

Pour chaque decouverte marquante (pas plus de 8-10, selectionner les
plus significatives si le projet est riche) :

### 4.N. <Titre descriptif de la decouverte>

<**Texte uniquement en prose**, pas de bloc "Etabli par / Niveau de
consolidation / Date" en en-tete. Le titre h3 suffit. Les informations
factuelles (methode d'etablissement, niveau de consolidation, date)
sont integrees dans les phrases qui suivent.>

<Rediger un **paragraphe argumentatif de 6 a 12 phrases** (et non
3-6 lignes en liste a puces) qui raconte la decouverte dans sa version
consolidee. Le paragraphe doit naturellement contenir, dans l'ordre
narratif qui convient le mieux :>

- le fait brut consolide, avec les chiffres exacts (sans les recopier en
  bullet : les inserer dans la phrase) ;
- la maniere dont il a ete etabli (donnees, script, outil) -- en une
  proposition incise, pas en ligne separee ;
- le **niveau de consolidation** enonce textuellement ("aujourd'hui
  `etabli`", "actuellement `volatile`", etc.) et, pour les faits non
  `etabli`, l'amplitude de variation ou l'hypothese critique tissee
  dans le paragraphe ;
- le mecanisme biologique sous-jacent (connu ou hypothetique) ;
- le lien argumente avec la litterature : ce que tel auteur (Coll,
  Stucki, Napier, Freschi...) disait jusqu'ici, et ce que ce projet
  confirme, contredit, etend ou nuance. Les citations sont integrees
  dans le texte, pas listees ;
- la **portee scientifique** : qu'est-ce que ce resultat change dans
  l'image globale de MTBC, du clade, ou de la methode ? Quelle est
  l'implication pour la suite du projet ou pour le terrain ?

<Si la valeur consolidee differe d'une valeur anterieure et que
l'evolution est instructive, une phrase de note dans le paragraphe
("Initialement estime a X, corrige a Y apres [methode/correction].").
Ne PAS detailler chaque iteration.>

<**Exemple de paragraphe attendu** (a transposer au contexte) :>

> La caracterisation phylogeographique mondiale de proto-L4.2 constitue
> le resultat le plus structurant de l'etude. A partir d'un corpus de
> 412 souches reparties dans 23 pays, extrait de TBannotator v3.6 puis
> filtre par `phase3_subclade_marker.py` (criteres d'exclusivite >= 95 %),
> 28 marqueurs SNP nouveaux et distincts de ceux de Coll *et al.* (2014)
> ont ete identifies, definissant la sous-lignee a une resolution
> jusque-la inedite. Le resultat est aujourd'hui `etabli` : deux
> reproductions independantes a un mois d'intervalle ont restitue le
> meme jeu de marqueurs, et le claim-check confirme la tracabilite
> jusqu'a la BDD source. La distribution geographique observee inverse
> le recit standard : alors que la lignee L4.2 avait ete decrite en
> Europe occidentale par Coll *et al.* sur six souches, la
> caracterisation mondiale fait apparaitre un noyau de diversite
> est-mediterraneen et levantin, suggerant que l'echantillonnage
> europeen initial capturait seulement la frange terminale de
> l'expansion. Cette geographie remaniee est compatible avec une
> emergence avant les contacts coloniaux, hypothese renforcee par la
> datation moleculaire (cf. section suivante), mais elle reste fragile
> sur la position exacte du foyer ancestral : les 23 pays
> d'echantillonnage ne couvrent pas l'Asie centrale, qui pourrait
> heberger les branches profondes manquantes. Pour la suite du projet,
> cela ouvre deux pistes precises : un appel a TBannotator restreint au
> Caucase et a l'Asie centrale, et une reconstruction d'etats ancestraux
> sur l'arbre phylogeographique enrichi.

<**Encadre `originalite` obligatoire** apres ce paragraphe : expliquer
en quoi ce resultat est nouveau / non trivial / important par rapport a
l'existant. Ce qu'un specialiste considere evident et qu'un profil
math/info pure ne peut pas evaluer seul. Voir Phase 9.1bis.>

<**Encadre `remarquable` si la decouverte est saisissante en soi** :
amplitude inattendue, precision exceptionnelle, contre-intuition,
consequence pratique majeure. Distinct de `originalite` (qui se compare
a la litterature) -- ici on rend pedagogique l'idee que "ce chiffre /
ce pattern devrait surprendre". Voir Phase 9.1bis pour la distinction
detaillee. Pas systematique : reserver aux resultats genuinement
frappants (3-6 par bilan max).>

<**Encadre `methode` si pertinent** : si la decouverte repose sur une
technique non triviale (Mantel partiel, ABC, dN/dS, ancestral state
reconstruction...), inserer un encadre `methode` la premiere fois que
la technique apparait dans le bilan.>

<Si le resultat est negatif (hypothese refutee, methode qui echoue),
expliquer en quoi cet echec est informatif et ce qu'il enseigne.>

## Donnees et analyses : etat des lieux

<Paragraphe introductif decrivant la masse de donnees accumulee et les
grandes etapes analytiques. Pas une liste seche — un survol qui donne
au lecteur une idee de l'ampleur du travail realise.>

<Exemple de ton : "Le projet repose sur un corpus de N souches
rassemblees dans la BDD centrale, dont les genomes ont ete annotes par
TBannotator v3.6. L'analyse s'est deployee en K phases, depuis le
controle qualite initial des variants jusqu'a la reconstruction
phylogenetique par maximum de vraisemblance. Les artefacts principaux
comprennent [arbre ML de N feuilles, matrice de distances SNP, K
figures de phylogeographie].">

### Vue schematique du pipeline

**IMPORTANT : le diagramme de pipeline est genere en TikZ**, insere
dans le Markdown via un bloc raw LaTeX. Ne JAMAIS tenter de dessiner
un pipeline en texte/ASCII/Unicode — c'est illisible en PDF.

Generer un bloc ```` ```{=latex} ```` contenant un `\begin{tikzpicture}`
qui represente le pipeline sous forme de boites reliees par des fleches.

**Modele de reference** (adapter au projet reel — phases, outils,
statuts) :

````markdown
```{=latex}
\begin{center}
\begin{tikzpicture}[
  phase/.style={
    rectangle, rounded corners=3pt, draw=accent, fill=accent!8,
    minimum width=13cm, minimum height=1.1cm, align=left,
    font=\small, text=darkgray, inner sep=8pt
  },
  arrow/.style={-{Stealth[length=5pt]}, thick, accent},
  done/.style={font=\small\bfseries, verdictgreen},
  partial/.style={font=\small\bfseries, verdictorange},
  node distance=0.5cm
]
\node[phase] (p1) {\textbf{Phase 1 — Contrôle qualité}\\
  bcftools, TBannotator v3.6 \hfill \textcolor{verdictgreen}{\textbf{OK}}\\
  \textit{→ N souches retenues sur M candidates, K variants filtrés}};

\node[phase, below=of p1] (p2) {\textbf{Phase 2 — Arbre ML}\\
  RAxML-NG (GTR+G, 1000 bootstraps) \hfill \textcolor{verdictgreen}{\textbf{OK}}\\
  \textit{→ Arbre de N feuilles, support moyen X\%}};

\node[phase, below=of p2] (p3) {\textbf{Phase 3 — Phylogéographie}\\
  geo\_map.py, choropleth \hfill \textcolor{verdictgreen}{\textbf{OK}}\\
  \textit{→ K figures, distribution dans P pays}};

\node[phase, below=of p3] (p4) {\textbf{Phase 4 — Datation moléculaire}\\
  IQ-TREE + LSD2 \hfill \textcolor{verdictorange}{\textbf{À faire}}\\
  \textit{→ Prérequis : fichier de dates des souches}};

\draw[arrow] (p1) -- (p2);
\draw[arrow] (p2) -- (p3);
\draw[arrow] (p3) -- (p4);
\end{tikzpicture}
\end{center}
```
````

**Regles pour le diagramme** :

1. **Une boite par phase reelle du projet** (pas de phases inventees).
   Lire les scripts `analyses/phase*_*.py` pour identifier les phases.
2. **Chaque boite contient** : titre de la phase, outil(s) utilise(s),
   statut (OK en vert, Partiel en orange, A faire en orange), et une
   ligne italique resumant le resultat concret.
3. **Fleches** entre les phases dans l'ordre sequentiel. Si deux phases
   sont independantes, les placer cote a cote (utiliser `right=of` au
   lieu de `below=of`).
4. **Largeur fixe** (`minimum width=13cm`) pour que toutes les boites
   soient alignees. Ajuster si le texte deborde.
5. **Couleurs** : utiliser les couleurs definies dans le template
   (`accent`, `verdictgreen`, `verdictorange`, `darkgray`). Ne pas
   definir de nouvelles couleurs.
6. **Ne pas surcharger** : max 8 phases. Si le projet en a plus,
   regrouper les phases proches.

### Donnees cles

| Ressource | Detail | Localisation |
|-----------|--------|-------------|
| BDD | N souches | `../../bdd/actuelle/<lignee>/` |
| Arbre ML | N feuilles, bootstrap X | `resultats/xxx.nwk` |
| ... | ... | ... |

## Etat du manuscrit

<Paragraphe decrivant l'avancement du manuscrit. Pas une liste de
sections — une evaluation qualitative : le manuscrit est-il coherent
avec les decouvertes ? Les resultats les plus importants y figurent-ils ?
La narration est-elle convaincante ?>

- **Structure** : <sections redigees, sections manquantes>
- **Verification factuelle** : <claims verifies/infirmes/a verifier>
- **Reviews** : <statut, points saillants des reviews recues>
- **Figures** : <adequation avec les resultats>
- **Statut** : en preparation | soumis | en revision | accepte | publie

<Si des claims ont ete infirmes par le claim-check, expliquer lesquels
et ce que ca implique pour le manuscrit.>

## Paysage de la litterature

<C'est la section ou la Phase 4 se materialise. Ecrire un ou plusieurs
paragraphes qui situent le projet dans le paysage de la recherche
publiee. Ce n'est PAS un inventaire de references — c'est une mise en
contexte qui aide a comprendre l'importance (ou non) du projet.>

<Questions auxquelles cette section doit repondre :>
- Que sait la communaute sur ce sujet ? Quels sont les travaux fondateurs ?
- En quoi ce projet apporte quelque chose de nouveau par rapport a l'existant ?
- Y a-t-il des resultats du projet qui contredisent la litterature ?
  (Si oui, c'est potentiellement le point le plus fort du bilan.)
- Quelles lacunes de la litterature ce projet pourrait-il combler ?
- Y a-t-il des travaux recents qui changent la donne ?

<Citer les references specifiques, pas juste "la litterature montre que".>

### Lacunes exploitables

<Pour chaque lacune identifiee dans la litterature ET adressable avec
les donnees du projet, expliquer en 2-3 phrases pourquoi c'est une
opportunite et comment le projet pourrait la combler.>

## A faire maintenant

<Cette section est **factuelle et tracee** : elle liste les choses
memorisees dans le cahier de labo qui n'ont pas ete faites. C'est la
valeur pratique du bilan -- ne laisser aucun fil pendant inapercu.>

<Paragraphe introductif : combien d'intentions non honorees ont ete
extraites, sur quelle periode du cahier elles s'etendent, et quelle est
la part de `a_faire` vs `partiellement_fait` (issue de la Phase 5.A).>

<Pour chaque intention non honoree, un bloc structure :>

### <Titre court de l'intention>

**Statut** : `a_faire` | `partiellement_fait`
**Origine** : entree du cahier du `YYYY-MM-DD`
**Citation** (si formulation marquante) : *"<copier la phrase exacte
du cahier>"*

<Paragraphe de 2-5 phrases qui explique :>
- **Ce qui etait prevu** (formulation precise du cahier).
- **Pourquoi ca avait ete prevu** (motivation memorisee : verifier une
  hypothese, repondre a un reviewer, completer une analyse, integrer
  une donnee externe...).
- **Ce qui manque concretement** pour l'executer (donnee, decision,
  temps, outil, prerequis methodologique).
- **Si partiel** : ou ca s'est arrete et quel etait le dernier etat.

**Commande suggeree** (si applicable) : `/<skill> <args>`
**Estimation effort** : faible | moyen | important

<Repeter pour chaque intention. Si plus de 10 intentions emergent,
regrouper celles qui sont semantiquement proches (ex : "Verifications
factuelles sur le manuscrit" qui regroupe 4 items).>

<Si la liste est vide -- toutes les intentions memorisees ont ete
realisees -- le dire explicitement et le considerer comme un critere
favorable pour le verdict "bouclee".>

## Pistes d'approfondissement

<Cette section est **prospective** : elle propose des nouvelles
directions qui ne sont pas dans le cahier, deduites de l'analyse
(inventaire des donnees, lacunes de la litterature, convergences
inter-projets). A distinguer nettement de "A faire maintenant" qui
trace les intentions deja memorisees.>

<Paragraphe introductif : combien de pistes emergent, d'ou elles
viennent (litterature, inventaire, convergence), et quelle est
la logique globale.>

### 8.N. <Titre de la piste>

**Priorite** : haute | moyenne | basse
**Score** : X.X (valeur Y/3, faisabilite Z/3, cout W/3)
**Origine** : <cahier YYYY-MM-DD | lacune litteraire | angle mort
methodologique | convergence inter-projets>

<Paragraphe de 4-8 phrases qui argumente scientifiquement pourquoi
cette piste vaut la peine. Inclure :>
- **La question** : que cherche-t-on a savoir ?
- **Le raisonnement** : pourquoi est-ce que cette question est
  interessante dans le contexte de ce projet ET de la litterature ?
  Quels articles suggerent que c'est un sujet porteur ? Quelle lacune
  ca comblerait ?
- **La methode** : comment proceder concretement ? Quel skill utiliser,
  avec quels parametres, sur quelles donnees ?
- **Le resultat attendu** : qu'est-ce qu'on espere trouver, et qu'est-ce
  que ca changerait pour les conclusions du projet ?
- **Les risques** : qu'est-ce qui pourrait ne pas marcher, et pourquoi
  ca vaut quand meme le coup ?

**Commande suggeree** : `/<skill> <args>`
**Prerequis** : <ce qu'il faut avant de lancer>

<Repeter pour chaque piste. Les pistes basses priorite peuvent etre
plus courtes (2-3 phrases) mais doivent quand meme etre argumentees,
pas juste listees.>

### Skills suggeres (si pertinent)

<Si une piste haute priorite ne peut etre couverte par aucun skill
existant, proposer la creation d'un nouveau skill avec nom, description,
et justification.>

## Convergences inter-projets

<Paragraphe (pas une liste) decrivant les projets MTBC voisins qui
partagent des questions, des donnees, ou des methodes avec ce projet.
Expliquer concretement ce que la mutualisation apporterait.>

## Limites et biais

<Paragraphe discutant honnetement les limites du projet. Pour chaque
limite, expliquer son impact sur les conclusions et si elle est
remediable ou inherente.>

<Points a toujours evaluer :>
- Biais de reference H37Rv (golden law MTBC)
- Taille et representativite de l'echantillon
- Couverture geographique et temporelle
- Biais d'echantillonnage (quelles souches sont disponibles et pourquoi)
- Limites des outils utilises

### Inventaire des faits fragiles ou volatils

<Cette sous-section recapitule explicitement les faits du projet dont
le niveau de consolidation (Phase 1bis) n'est pas `etabli` ni
`convergent`. Pour chacun :>

| Fait | Niveau | Amplitude / hypothese critique | Piste de consolidation |
|------|--------|-------------------------------|------------------------|
| <fait> | volatile | 1080-1410 CE (260 ans inter-methodes) | BEAST horloge relaxee (`/molecular-clock`) |
| <fait> | fragile | suppose horloge stricte, non teste | jackknife + multi-tree skyline |
| <fait> | hypothetique | mecanisme non teste | `/mk-ascertainment` sur katG/inhA |

<Le critere 7 de cloture (Phase 8) renvoie a ce tableau : tant qu'il
contient un fait central, le projet n'est pas boucle.>

## Anomalies detectees

<Vide ou paragraphe (pas une liste seche) : double format cahier, BDD
absente, phase sans script, claim non verifie depuis X jours, etc.
Pour chaque anomalie, suggerer une action corrective.>

## Plan d'action pour la prochaine session

<Pas une simple liste de commandes -- un paragraphe qui sequentialise
les actions en expliquant la logique, en **piochant en priorite dans
"A faire maintenant"** (intentions deja memorisees, donc d'effort faible
ou prevu) avant de proposer des elements de "Pistes d'approfondissement"
(nouvelles directions). La logique typique : "Commencer par finaliser
[intention non honoree X] car [raison], ce qui debloque ensuite la
piste prospective [Y]." Puis les commandes concretes :>

1. `/<skill> <args>` -- <justification, source : A faire / Piste>
2. `/<skill> <args>` -- <justification, source : A faire / Piste>
3. `/<skill> <args>` -- <justification, source : A faire / Piste>
```

---

## Mode `--full` -- Bilan comparatif de tous les projets

1. `ls /home/christophe/docs/codes/mtbc/` -- lister les
   repertoires.
2. Filtrer :
   - **Inclure** : repertoires contenant `CLAUDE.md` ET (`article/` OU
     `analyses/` OU `cahier_de_labo.md` OU `JOURNAL.md`).
   - **Exclure explicitement** : `bdd/`, `investigate_phylo/`,
     `global_supplementary/`, `bilans_globaux/`, `.git/`, fichiers
     isoles (`init_project.py`, `*.png`, etc.).
3. Pour chaque projet retenu, executer une **version allegee** des
   Phases 1 a 5 :
   - Cahier : compter entrees, derniere date, pistes ouvertes (liste).
   - Manuscrit : presence + pourcentage de claims verifies si
     `claim_check.md` existe.
   - Verdict mini : appliquer les 7 criteres de cloture (dont le 7e,
     "consolidation", bloquant).
4. Agregation :

```markdown
# Bilan global MTBC -- YYYY-MM-DD

## Tableau comparatif
| Projet | Lignee | Derniere activite | Entrees cahier | Article | Claims OK | Pistes ouvertes | Verdict |
|--------|--------|-------------------|----------------|---------|-----------|-----------------|---------|
| L4.9 | L4.9 | 2026-04-07 (-2j) | 6 | en prep | n/a | 5 | poursuivre |
| L4.15 | L4.15 | 2026-04-06 (-3j) | 1 | soumis | 12/12 | 0 | **bouclee** |
| ... | ... | ... | ... | ... | ... | ... | ... |

## Priorites cross-projets
<Pistes apparaissant dans plusieurs projets -- ex : datation moleculaire
manquante dans L4.9, L4.14, L5 → lancer une campagne groupee.>

## Convergences possibles
<Projets qui pourraient partager donnees, outgroup, methodologie, ou
fusionner leur analyse.>

## Projets prets a clore
<Liste des projets passant le verdict "bouclee". Action suggeree :
archivage, soumission finale, passage a un nouveau projet.>

## Projets dormants (> 180 jours sans activite ET non boucles)
<Liste avec date de derniere activite. Signalement : risque de perte
de contexte, reouvrir ou clore explicitement.>

## Top 10 des pistes haute priorite (tous projets confondus)
1. **<projet>** -- <piste> (score X.X)
2. **<projet>** -- <piste> (score X.X)
...
```

5. Ecrire dans
   `/home/christophe/docs/codes/mtbc/bilans_globaux/YYYY-MM-DD_bilan_global.md`
   (creer le repertoire si absent, suffixer `_v2` si collision).

---

## Points de vigilance

1. **Fallback format** : `cahier_de_labo.md` ou `JOURNAL.md`. Si les
   deux existent, lire les deux et le signaler dans "anomalies".
2. **Chemins** : normaliser via `realpath` en Phase 0 pour eviter les
   erreurs de persistance en cas d'invocation depuis un autre cwd.
3. **Cahier volumineux** : chunks de 2000 lignes si > 5000, jamais
   tronquer.
4. **BDD absente ou deplacee** : mentionner comme anomalie, ne pas
   bloquer.
5. **Biais reference H37Rv** : rappel automatique dans la section
   "Limites connues" si des analyses SNP sont presentes (golden law
   MTBC).
6. **Collision de fichier** : suffixer `_v2`, `_v3`, jamais ecraser.
7. **`--full` faux positifs** : filtrer strictement (`bdd/`,
   `investigate_phylo/`, etc.).
8. **`mtbc-lineages` absent** : degrader gracieusement, ne pas echouer.
9. **Honnetete** : < 3 pistes haute priorite → sortie courte assumee,
   surtout pas de remplissage. Mais "court" ne veut pas dire "sec" :
   meme un bilan qui conclut "rien a faire" doit etre narratif et
   pedagogue dans sa justification.
10. **Non destructif** : la seule ecriture autorisee est le fichier
    bilan et le repertoire `bilans/`.
11. **Pistes "deduites"** : distinguer clairement les pistes venant du
    cahier (citer la date) de celles deduites de l'inventaire (marquer
    "deduite de l'inventaire").
12. **Projets imbriques** : verifier a la volee la localisation des
    projets animaux (racine vs sous-repertoire), ne rien supposer.

---

## Epilogue -- Resume console

Apres ecriture du bilan, afficher un resume **consolide et oriente
action** (pas un tableau de metriques, pas un narratif iteratif) :

```
=== Bilan : <nom projet> ===

Bilan produit :
  Markdown : <chemin>                  (<taille>)   [OK]
  PDF      : <chemin>                  (<taille>)   [OK | ECHEC]
  Slides   : <chemin .pdf>             (<taille>)   [OK | ECHEC]

(Les trois fichiers sont OBLIGATOIRES. En cas d'ECHEC, afficher la
commande de relancement manuel immediatement sous la ligne.)

Etat consolide des connaissances (3-5 phrases) :
<Resumer ce que le projet SAIT aujourd'hui, par theme principal. Pas
"on a fait X puis Y" -- plutot "le projet a etabli que [fait
consolide], que [fait consolide], et a documente [mecanisme]." Donner
l'image stabilisee du savoir, pas le cheminement.>

Faits volatils ou fragiles a surveiller :
  - <fait> [volatile|fragile] -- <amplitude ou hypothese critique> ;
    consolidation : <piste si elle existe, sinon "pas de voie evidente">
  - <fait> [...] -- <...>
<Lister explicitement les 2-5 faits non-`etabli` les plus importants
du projet, surtout ceux qui apparaitront dans le manuscrit ou seraient
cites a une reunion. Si tous les faits centraux sont `etabli`, le dire :
"Aucun fait central marque volatile ou fragile.">

Verdict : <CLORE | A POURSUIVRE> (X/7 criteres, dont critere 7
"consolidation" bloquant)
<2 phrases justifiant le verdict.>

A faire maintenant (intentions memorisees non honorees) :
  1. <intention> (cahier YYYY-MM-DD) -- <ce qui manque pour l'executer>
  2. <intention> (cahier YYYY-MM-DD) -- <ce qui manque>
  3. <intention> (cahier YYYY-MM-DD) -- <ce qui manque>
<Si la liste est vide, le dire explicitement.>

Pistes prospectives (nouvelles directions deduites) :
  1. <titre> (score X.X) -- <justification en une phrase> → `/<skill>`
  2. <titre> (score X.X) -- <justification> → `/<skill>`
  3. <titre> (score X.X) -- <justification> → `/<skill>`

Connexion litterature : <1-2 phrases sur les lacunes exploitables
ou les resultats qui contredisent/confirment la litterature>
```

Si mode `--full` :

```
Bilan global produit : <chemin absolu>
  Projets scannes : N
  Prets a clore  : M
  Dormants       : P
  Top priorites cross-projets : <3 lignes>
```

Suggestions de prochaines etapes (si pertinentes) :
- `/cahier-de-labo update` si le bilan a revele une production de
  connaissance nouvelle.
- `/<skill prioritaire>` pour la premiere piste haute priorite.
- `/mtbc-bilan --full` si un seul projet vient d'etre traite, pour
  remettre en perspective.
