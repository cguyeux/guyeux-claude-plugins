---
name: mtbc-prospect
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST), peer-reviewed MTBC phylogenomics :
  moteur d'ideation divergente qui genere de nouvelles pistes de recherche pour un projet
  MTBC. Ce pilote Codex les presente en lecture seule tant que `pistes` n'est pas porte.
  Parcourt des axes lateraux interdisciplinaires
  (coevolution avec l'hote humain, histoire genetique humaine, routes commerciales, reseaux
  de genes et evolution compensatoire, conformation 3D des proteines, place du MTBC parmi
  les mycobacteries), audite chaque skill disponible comme lentille de decouverte, propose
  de nouveaux skills a forger, relit retrospectivement pistes.md et le cahier de labo, auto-
  challenge chaque idee (contre-argument le plus fort, modele nul falsifiant, gain vs cout)
  et inscrit les survivantes. A utiliser quand un projet a besoin de directions neuves, pour
  un brainstorming d'angles originaux, quand la gap-analysis de mtbc-bilan --deepen ne
  suffit pas, ou pour trancher s'il reste quelque chose a explorer.
allowed-tools: Bash, Read, Grep, Glob, WebSearch, WebFetch, mcp__tbmonitor__execute_sql, mcp__tbmonitor__show_schema, mcp__tbannotator__tool_query_postgres, mcp__tbannotator__tool_get_schema
---

# /mtbc-prospect -- Prospection de nouvelles pistes de recherche

Pour un projet MTBC donne, **imagine des directions neuves** qu'aucune session
n'a encore envisagees, de deux facons complementaires : (1) en pensant
**lateralement** -- l'hote humain et sa coevolution, l'histoire genetique et
geographique des populations, les routes commerciales et les empires, les reseaux
de genes et l'evolution compensatoire, la conformation 3D des proteines, la place
du MTBC dans les mycobacteries et ce que *M. canettii* et les ecotypes animaux
revelent par polarisation ; (2) en regardant **retrospectivement** le dossier lui-meme
-- relire `pistes.md` et le cahier de labo pour reperer ce qui a ete traite trop
vite, sous un seul angle, ou dont un resultat en a ouvert un autre reste non trace.
Chaque idee est passee au crible adversarial, et seules les survivantes sont
inscrites dans `pistes.md` -- soit comme pistes neuves, soit en **enrichissant ou en
splittant** une piste existante (ajout de sous-pistes, jamais de reecriture).

**Principe cardinal -- diverger PUIS selectionner.** La phase creative genere
large et sans autocensure (quantite d'abord) ; la phase adversariale tue sans
etat d'ame (qualite ensuite). Ne jamais melanger les deux : brider l'imagination
pendant la divergence tue les idees remarquables avant qu'elles existent ;
epargner une idee faible pendant le challenge pollue `pistes.md`.

**Honnetete -- "il n'y a plus rien a explorer" est un resultat valide et
souhaitable.** Si, apres divergence sur tous les axes et challenge, aucune piste
neuve ne survit au seuil, le dire franchement. Ne JAMAIS inventer des pistes
gadget pour justifier une sortie fournie. Un projet peut etre epuise ; c'est une
conclusion, pas un echec du skill.

> [!NOTE]
> **Frontiere avec `mtbc-bilan` et `mtbc-reboot` (trois skills voisins, ne pas
> confondre).**
> - `mtbc-bilan` PHOTOGRAPHIE l'etat su (lecture seule) et, sous `--deepen`, fait
>   une **gap-analysis systematique** (lit-review elargie + methodes non
>   mobilisees + scoring) qui produit un rapport date dans `bilans/`.
> - `mtbc-reboot` REPART a zero quand la derive est trop forte (operation
>   destructrice, re-analyse claim par claim).
> - `mtbc-prospect` (ce skill) fait de la **DIVERGENCE CREATIVE** : il ne
>   photographie pas et ne reboote pas, il **imagine lateralement** des angles
>   interdisciplinaires que la gap-analysis ne trouve pas (parce qu'ils ne
>   derivent pas d'une methode ou d'une lacune de la lit-review, mais d'une
>   analogie avec l'histoire humaine, la geographie, la structure 3D, l'outgroup),
>   puis les inscrit **directement dans `pistes.md`**.
>
> Regle : photographier (`bilan`) -> imaginer (`prospect`) -> repartir (`reboot`).
> Complementaires, pas concurrents. Si le besoin est "ou en est-on / que
> reste-t-il des intentions memorisees", c'est `bilan`, pas `prospect`.

## Prealable -- consultation memoire projet

**Avant toute action** :

1. Lire `CLAUDE.md` du projet (titre, lignee, question scientifique fondatrice).
2. Lire `etat_des_decouvertes.md` (prouve / infirme / incertain) s'il existe.
3. Lire `pistes.md` **integralement** -- c'est la liste de ce qui a deja ete
   envisage (a faire, en cours, realise, abandonne). **Toute piste generee qui
   duplique une entree existante -- meme close ou abandonnee -- est ecartee.**
   Une piste `[abandonne]` porte souvent sa raison : ne pas la re-proposer sans
   argument neuf levant cette raison.
4. Lire `cahier_de_labo.md` (au moins les 15-20 dernieres entrees ; si < 5000
   lignes, integralement) : decouvertes recentes, echecs instructifs, pistes
   evoquees non tracees.
5. Lire l'entree transverse de la base de connaissances tuberculosis lorsqu'elle
   est disponible (contexte MTBC, pieges documentes, biais connus).
6. Consulter `mtbc-lineages` pour la golden law (hierarchie Guyeux, biais de
   reference H37Rv) ; indisponible -> degrader gracieusement.

Afficher un bref resume avant de commencer :

```
Prospection : [projet] ([lignee])
  Question fondatrice : [...]
  Pistes existantes   : N (a faire X, en cours Y, realise Z, abandonne W)
  Derniere activite   : [date cahier]
  Axes retenus        : [tous | liste --axes]
```

## Declenchement

```
/mtbc-prospect                      # projet du repertoire courant
/mtbc-prospect L4.15                # projet nomme (relatif a codes/mtbc/, ou chemin absolu)
/mtbc-prospect --axes hote,geo,3d   # restreindre aux axes nommes (defaut : tous)
/mtbc-prospect --wild               # divergence maximale : idees haut-risque / haut-gain, analogies transverses
/mtbc-prospect --dry-run            # proposer et afficher SANS ecrire dans pistes.md
```

Identifiants d'axes pour `--axes` : `hote`, `histoire`, `geo`, `reseaux`, `3d`,
`mycobacteries`, `phylodyn`, `selection`. (Catalogue en Phase 2.)

Profondeur : lecture + inspection legere + recherche litterature ciblee. Le skill
**suggere, il n'execute pas** les analyses (aucun calcul lourd, aucun arbre
lance) ; il ecrit **uniquement** dans `pistes.md` (et, en `--dry-run`, nulle
part). Non destructif : jamais de `rm` (voir `gio trash`), jamais de reecriture
en bloc de `pistes.md` (mutation locale seulement, cf. `/pistes`).

---

## Phase 0 -- Resolution et sanity-check

1. Resoudre le chemin : argument absolu tel quel ; sinon nom relatif prefixe par
   `/home/christophe/docs/codes/mtbc/` ; sinon `pwd`. Normaliser (`realpath`).
2. Sanity-check : compter les presences parmi `CLAUDE.md`, `cahier_de_labo.md`,
   `pistes.md`, `analyses/`, `article/`. Moins de 2 -> "Ce repertoire ne ressemble
   pas a un projet MTBC. Abandon." et terminer.

   > **GARDE-FOU -- ne jamais prospecter la RACINE `mtbc/` par erreur** (defaut vecu le
   > 2026-07-31). `/home/christophe/docs/codes/mtbc/` possede LUI-MEME un `CLAUDE.md`,
   > un `cahier_de_labo.md` et un `pistes.md` : il **passe le sanity-check ci-dessus**
   > (3 presences sur 5). Un `cd ..` de trop, un `pwd` inattendu ou un argument vide
   > suffisent donc a prospecter l'arbre de pistes TRANSVERSE (toutes lignees, Yersinia,
   > L6...) en croyant lire celui d'un projet. Le symptome est un contenu **incoherent
   > avec le projet attendu** -- et il passe inapercu si l'on ne regarde que les
   > compteurs.
   >
   > Verifier explicitement, AVANT la Phase 1 :
   > ```bash
   > R=$(realpath "$TARGET"); [ "$R" = "$HOME/docs/codes/mtbc" ] && \
   >   { echo "REFUS : c'est la RACINE des projets MTBC, pas un projet. Preciser lequel."; exit 1; }
   > head -1 "$R/pistes.md"   # doit nommer le projet attendu
   > ```
   > Et **afficher le nom du projet lu** (premiere ligne de `pistes.md` / titre du
   > `CLAUDE.md`) dans le resume de la Phase 0 : c'est ce controle d'une ligne qui
   > rend l'erreur visible immediatement. Meme piege pour tout skill qui remonte
   > l'arborescence a la recherche d'un `cahier_de_labo.md`.
3. Si `pistes.md` est absent : le proposer via `/pistes` (amorcage depuis le
   cahier) avant de prospecter -- prospecter sans arbre de pistes revient a
   ecrire dans le vide.

## Phase 1 -- Cartographie de l'existant (frontiere du connu)

L'objectif est de tracer la **frontiere** entre ce qui est deja su/envisage et
l'inconnu, pour que la divergence vise l'inconnu et rien d'autre.

1. Depuis `etat_des_decouvertes.md` et le cahier : lister les faits **prouves**
   (une piste qui les redemontre est sans valeur), **infirmes** (ne pas
   ressusciter), **incertains/ouverts** (candidats a consolidation, pas a
   nouveaute).
2. Depuis `pistes.md` : construire l'ensemble **"deja envisage"** = toutes les
   pistes, quel que soit l'etat. Noter les `[abandonne]` avec leur raison.
3. Inventaire leger des donnees reellement disponibles (`data/`, souches en
   `bdd/actuelle/<lignee>/`, VCF/SPDI, metadonnees geo/date) : une piste dont les
   donnees n'existent pas et ne sont pas mobilisables est `hypothetique`, a
   flaguer comme telle, pas a presenter comme faisable.
4. Poser la **question fondatrice** en une phrase et les 2-3 sous-questions du
   projet. La divergence part de la, puis s'en eloigne deliberement.

## Phase 2 -- DIVERGENCE par axes lateraux (moteur creatif)

Le coeur du skill. **Parcourir chaque axe retenu, un par un**, et generer pour
chacun des pistes candidates **brutes** (3-8 par axe), sans filtrer encore. On
vise la quantite et l'originalite ; le tri viendra en Phase 6.

Pour chaque axe, se poser la **question generatrice** de l'axe appliquee aux
donnees et a la lignee de CE projet, et ecrire les idees qui en sortent. **Ne pas
survoler** : chaque axe merite un vrai temps de reflexion. Les banques de
questions detaillees et des exemples travailles sont dans
`references/axes_lateraux.md` -- **le lire au moment d'attaquer les axes**, il
demultiplie la generation.

### Catalogue des axes

**A. `hote` -- Coevolution avec l'hote humain.**
La lignee epouse-t-elle une structure de population humaine (modele sympatrique
Gagneux) ? Peut-on confronter la phylogeographie de la lignee a l'histoire
genetique des hotes (HLA, `SLC11A1`/NRAMP1, TLR, LTA4H) ? Existe-t-il des paires
hote-pathogene anciennes exploitables (aDNA) ? Skills : `host-pathogen-pair`,
`coevolution`, `modern-human-reference-panels`, `migration-data`.

**B. `histoire` -- Histoire genetique et evolutive humaine.**
Placer les TMRCA / dates d'introduction de la lignee sur la **frise des
evenements demographiques humains** (Neolithique, age du Bronze, expansions
commerciales, colonisation, migration de main-d'oeuvre contemporaine). Une
introduction datee coincide-t-elle avec un mouvement humain documente ? Skills :
`molecular-clock`, `iqtree-lsd2`, `bayesian-skyline`, `migration-data`.

**C. `geo` -- Histoire, geographie, routes.**
Quelles **routes commerciales, maritimes, caravanieres, de pelerinage** relient
la region du projet aux corridors genomiques observes ? Empires, ports, mousson,
climat comme priors d'hypotheses de flux. *Exemple (Oman) : l'enrichissement du
corridor Tanzanie s'explique-t-il par le commerce swahili de la mousson de
l'ocean Indien (Zanzibar, sultanat omanais), et le pelerinage / le Hajj module-t-il
les flux ?* Skills : `phylogeography`, `geo-map`, `sra-geolocate`,
`migration-data`, `ancestral-reconstruction`.

**D. `reseaux` -- Reseaux de genes, epistasie, evolution compensatoire.**
Les mutations definissant la lignee co-occurrent-elles (epistasie, operons,
regulons) ? Y a-t-il une signature d'**evolution compensatoire** (rpoB->rpoC,
katG->ahpC) ? Le reseau d'interaction (STRING) d'un gene mute est-il recable
specifiquement dans cette lignee ? Skills : `mtbc-gene-network`, `string-db`,
`convergent-evolution`, `spdi-annotation`.

**E. `3d` -- Evolution de la conformation 3D des proteines.**
Impact **structural** des mutations lignee-specifiques (destabilisation,
site actif, interface) via ESM / structures ? Convergence structurale (memes
consequences 3D par des voies differentes) ? Site catalytique conserve d'un gene
"hypothetique" requalifie ? Skills : `esm-atlas-cli`, `active-site-check`,
`mtbc-gene`, `spdi-annotation`.

**F. `mycobacteries` -- Place dans les mycobacteries, polarisation par Canettii
et animales.**
Que revele **l'outgroup** (*M. canettii*, ecotypes animaux, NTM proches) par
polarisation : quel etat d'un caractere est ancestral vs derive dans cette
lignee ? Un trait "specifique" l'est-il vraiment une fois compare a canettii /
bovis / caprae / orygis ? Transfert horizontal visible chez canettii et perdu
chez le MTBC ? Skills : `denovo-content-qc`, `species-id`, `pangenome-enrichment`,
`convergent-evolution`, projet voisin `Canettii/`.

**G. `phylodyn` -- Phylodynamique et ecologie evolutive.**
Trajectoire de la taille efficace Ne(t) vs evenements historiques ? Succes
epidemique gradue (THD) au-dela du binaire cluster/singleton ? Evolution
intra-hote, infections mixtes, topologie du reseau de transmission ? Skills :
`bayesian-skyline`, `thd`, `snp-distance`, `tsne-hdbscan`.

**H. `selection` -- Selection moleculaire et immuno-evasion.**
Signatures de selection (dN/dS, test MK avec correction d'ascertainment) ?
Convergence adaptative inter-lignees ? Paradoxe des epitopes T
hyperconserves (Comas 2010) applique a cette lignee ? PE/PPE, ESX, antigenes.
Skills : `mk-ascertainment`, `convergent-evolution`, `lineage-comparison`,
`spdi-annotation`.

### Meta-axe `--wild` (divergence maximale)

Si `--wild` : ajouter un tour d'**analogies transverses** -- importer un concept
d'un champ etranger (ecologie des metapopulations, epidemiologie des reseaux
sociaux, linguistique historique et arbres de langues, theorie des jeux
evolutionnaires, physique des transitions de phase) et se demander ce qu'il
donnerait applique a ce projet. Idees haut-risque assumees ; elles passeront le
challenge comme les autres.

## Phase 2bis -- Sources RETROSPECTIVES (introspection du dossier)

Les axes de la Phase 2 regardent **vers l'exterieur** (autres disciplines). Cette
phase regarde **vers l'interieur** : le meilleur gisement de pistes neuves est
souvent ce que le projet a DEJA produit et sous-exploite. Deux lentilles, a
parcourir aussi soigneusement que les axes, generant des candidates brutes (sans
filtrer -- le tri reste la Phase 6). Elles alimentent en priorite
l'**enrichissement / le split** de pistes existantes (Phase 8), pas seulement des
pistes neuves.

**R1 -- Relecture critique de `pistes.md`.** Reprendre **chaque** piste, quel que
soit son etat, et se poser :
- **[realise, mais...]** a-t-elle ete traitee **trop vite** ou par un raccourci
  methodologique (n faible, une seule methode, sensibilite non testee, prototype
  jamais passe a l'echelle) ? -> piste de **consolidation** ou de re-analyse plus
  robuste.
- **[realise, angle unique]** un **sous-angle** evident a-t-il ete laisse de cote
  (autre lignee, autre gene, autre metrique, direction inverse) ? -> **sous-piste
  complementaire** sous la piste existante.
- **[realise -> ouvre]** son resultat **ouvre-t-il logiquement** une question qui
  n'est nulle part tracee ? (ex. un corridor mis en evidence appelle sa datation ;
  une convergence appelle son test fonctionnel). -> nouvelle sous-piste.
- **[abandonne]** la **raison** de l'abandon **tient-elle encore** ? Un outil
  reforge, un nouvel arrivage de donnees, ou le resultat d'une autre piste
  peuvent l'avoir levee. -> proposer de **rouvrir** (jamais en changeant l'etat
  soi-meme : ajouter une sous-piste "reouverture envisagee car ..." et laisser
  `/pistes` trancher).
- **[en cours, bloque]** une piste stagnante appelle-t-elle un **contournement**
  (sous-ensemble faisable maintenant, methode alternative, prototype partiel) ?
- **[trop grosse]** une piste fourre-tout gagnerait-elle a etre **splittee** en
  sous-pistes distinctes, chacune testable et priorisable separement ?

**R2 -- Relecture critique du cahier de labo.** Lire le cahier (au moins les
entrees non deja couvertes par R1) en chassant ce qui a ete **dit puis oublie** :
- un **resultat sous-exploite** (un chiffre, une table, une figure produite pour
  autre chose mais qui porte un signal secondaire non suivi) ;
- une **observation "en passant"** (« on remarque que... », « curieusement... »)
  jamais reprise ensuite ;
- une **hypothese formulee et non testee**, ou testee partiellement ;
- un **echec instructif** dont la cause suggere une **autre approche** (pas juste
  "ca n'a pas marche" : "ca n'a pas marche PARCE QUE X, donc essayer Y") ;
- une **contradiction interne** entre deux entrees, jamais arbitree.

Chaque item de R1/R2 devient une candidate, **tracee a son origine** (piste Px, ou
date d'entree du cahier), et marquee comme cible d'**enrichissement/split** (Phase
8) ou de **piste neuve** selon le cas. Discipline inchangee : elles passent toutes
le challenge de la Phase 6 ; ne pas ressusciter une piste abandonnee sans que
l'argument neuf (outil, donnee, resultat) soit explicite et verifie.

## Phase 3 -- Audit des skills comme lentilles de decouverte

Passer en revue **les skills disponibles un par un** et, pour chacun, poser une
seule question : *applique aux donnees de CE projet, ce skill produirait-il une
decouverte complementaire que personne n'a encore lancee ?*

Inspecter les skills Codex installes et le catalogue canonique du projet ; ne pas
supposer une arborescence de plugins Claude voisine.

Pour chaque skill **d'analyse** (exclure les skills de redaction et de BDD, qui
sont des outils, pas des angles) : lire son frontmatter, chercher une trace
d'usage dans le cahier/scripts/resultats, puis classer :
- **utilise** -- deja mobilise, ignorer.
- **lentille candidate** -- applicable aux donnees du projet, jamais lance, et
  susceptible de reveler quelque chose de neuf. En faire une piste candidate
  (avec : ce qu'il apporterait, ce qu'il faudrait, l'effort estime).
- **non pertinent** -- hors sujet pour cette lignee/ce projet.

Ne PAS gonfler : un skill "lentille candidate" doit avoir un **resultat attendu
concret**, pas juste "on pourrait le lancer".

## Phase 4 -- Skills a forger (quand aucun outil n'existe)

Pour toute piste candidate a forte valeur qu'**aucun skill existant** ne couvre,
specifier un **nouveau skill a creer**, en une fiche courte :
- **nom** propose (convention `mtbc-<verbe>` ou domaine) ;
- **but** en une phrase ;
- **entrees / sorties** ;
- **pourquoi il debloquerait une decouverte** que les outils actuels ne
  permettent pas ;
- **effort de forge** estime (leger / modere / lourd).

Ces fiches ne creent rien : elles deviennent des pistes `[a faire]` de type
"outillage" dans `pistes.md`, a arbitrer par l'utilisateur. Rester sobre : une ou
deux propositions solides valent mieux que dix esquisses.

## Phase 5 -- Pollinisation inter-projets

`ls /home/christophe/docs/codes/mtbc/`, puis pour chaque voisin pertinent
`Read CLAUDE.md` limit 20 (titre + objectif). Chercher :
- une **methode** eprouvee ailleurs, transferable a ce projet ;
- des **donnees partageables** (BDD commune, outgroup commun, panel comparateur) ;
- une **decouverte** d'un voisin qui, transposee, ouvre une question ici ;
- une **contradiction** entre un voisin et ce projet (souvent la piste la plus
  interessante).

Chaque emprunt devient une piste candidate, tracee a sa source.

## Phase 6 -- AUTO-CHALLENGE adversarial (le crible)

**Passer CHAQUE piste candidate** (Phases 2, 2bis, 3, 4, 5) au crible de
`/challenge`. Pour chacune, ecrire :
1. **Le contre-argument le plus fort** : pourquoi cette piste pourrait ne rien
   donner, ou donner un artefact.
2. **Le modele nul falsifiant** : quel resultat neutre reproduirait le signal
   attendu sans l'hypothese (biais d'echantillonnage, densite, derive neutre,
   convergence/homoplasie, biais de reference H37Rv). Une piste qu'un modele nul
   trivial explique deja est **tuee**.
3. **Deja fait ?** : re-verifier contre `pistes.md`, le cahier, et la
   litterature (interroger **`tbmonitor-papers` en priorite** pour le MTBC, puis
   `lit-review`/WebSearch). Replication n'est pas decouverte : si la litterature
   l'a deja fait sur cette lignee, tuer ou reformuler en angle vraiment neuf.
4. **Gain attendu vs cout** : ce que ca changerait pour les conclusions, contre
   le temps/calcul/donnees requis.

Verdict par piste : **retenue** / **reformulee** (angle affine survivant au
challenge) / **tuee** (avec la raison). Ne garder que retenues + reformulees.

> Piege recurrent a appliquer systematiquement : **biais de reference H37Rv**
> (H37Rv = L4.9, toute analyse SNP le traitant comme neutre biaise pour L4.9) ;
> **convergence/homoplasie** (une mutation partagee par >= 2 lignees majeures
> n'est pas localisable) ; **densite d'echantillonnage** (un % de plus-proche-
> voisin brut est ininterpretable sans null de densite). Cf.
> la base de connaissances transverse tuberculosis, lorsqu'elle est disponible.

## Phase 7 -- Scoring et hierarchisation

Scorer les survivantes de 0 a 3 sur cinq dimensions :
- **valeur scientifique** (0 anecdotique -> 3 potentiellement structurant) ;
- **originalite** (0 deja fait ailleurs -> 3 premiere etude a le tenter) ;
- **faisabilite** (0 donnees absentes -> 3 pret a lancer avec les donnees en
  main) ;
- **soutien** (0 aucun precedent ni analogie -> 3 lacune claire dans la
  litterature, ou analogie historique/geographique forte) ;
- **serendipite/synergie** (0 isole -> 3 debloque plusieurs autres pistes ou
  relie deux axes).

`score = (valeur x3 + originalite x2 + faisabilite x2 + soutien x2 + serendipite x1) / 10`.
**Haute** >= 2,0 ; **moyenne** 1,0-2,0 ; **basse** < 1,0. Chaque piste garde la
trace de son **axe d'origine** et de sa **source** (divergence / lentille skill /
skill a forger / inter-projet / --wild).

## Phase 8 -- Ecriture dans pistes.md (mutation locale)

**Gate de portabilite Codex.** Tant que CCX-05 n'a pas porte le workflow personnel
`pistes`, ce paquet pilote est strictement en lecture seule : utiliser
`--dry-run`, presenter les candidates pour insertion humaine, et ne pas creer ou
modifier `pistes.md` automatiquement. Apres portage de ce workflow, inscrire les
pistes retenues en respectant sa convention append-only : ajouter des lignes,
sans reecrire un bloc, supprimer, ni changer l'etat ou le texte d'une piste
existante. Deux modes de sortie, selon l'origine de la piste :

**Mode A -- piste neuve** (candidate sans rattachement naturel a l'existant,
typiquement issue de la Phase 2 laterale, de la Phase 3/4/5).
- Nouveau(x) bloc(s) de piste majeure numerotes **dans la continuite** (P-suivant
  apres le dernier ` ## Pn`), a l'etat `[a faire]`, avec `origine : /mtbc-prospect`
  et `maj : <date du jour>`. Regrouper les pistes d'un meme axe sous un bloc, ou
  creer un bloc "Prospection <date>" -- au choix selon le volume, mais rester lisible.

**Mode B -- enrichissement / split d'une piste existante** (typiquement issu de la
Phase 2bis : une piste realisee trop vite, un sous-angle oublie, un resultat qui en
ouvre un autre, une piste fourre-tout a scinder).
- **Enrichir** : ajouter une **sous-piste** sous la piste concernee `Px`, numerotee
  dans sa continuite (`Px.y`, ou `Px.y.z`), a l'etat `[a faire]`, avec `origine :
  /mtbc-prospect (retrospection)`. Ne PAS modifier la piste parente ni ses autres
  sous-pistes.
- **Splitter** : ne jamais reecrire/supprimer la piste fourre-tout. A la place,
  ajouter sous elle les sous-pistes distinctes proposees, et une note indentee
  "split suggere : ... -- via /pistes" laissant `/pistes` acter la reorganisation.
- **Rouvrir un `[abandonne]`** : ne PAS rebasculer l'etat soi-meme ; ajouter une
  sous-piste "reouverture envisagee : <argument neuf verifie qui leve la raison
  d'abandon>" et laisser `/pistes start` trancher.

**Commun aux deux modes.**
- Pour chaque (sous-)piste : libelle concis + entre parentheses, en note indentee,
  la **source** (axe lateral, ou "retrospection Px", ou "cahier <date>"), le **gain
  attendu**, le **cout**, et le **contre-argument residuel** (ce que le challenge
  n'a pas totalement leve). La trace du challenge est ce qui distingue une piste
  prospectee d'une simple idee.
- **Ne jamais dupliquer** une piste deja presente (garde de la Phase 1).
- Les **skills a forger** (Phase 4) vont dans un bloc/sous-piste de type "outillage".

Recuperer la date du jour via `date +%F` (ne pas coder en dur).

Apres ecriture, afficher **la ou les branches touchees** (blocs neufs ET sous-pistes
ajoutees a des pistes existantes).

## Phase 9 -- Verdict et bilan narratif

Deux issues :

**(a) Des pistes ont survecu.** Presenter un **bilan narratif** a l'ecran (pas un
tableau sec), destine a l'utilisateur, qui :
- rappelle la question fondatrice et la frontiere du connu ;
- expose les pistes retenues par ordre de score, chacune avec son axe/source (y
  compris **retrospection** : "en relisant Px / le cahier du <date>, on voit
  que..."), l'idee, ce qu'elle changerait, et le contre-argument residuel ;
- distingue clairement les **pistes neuves** (mode A) des **enrichissements/splits
  de pistes existantes** (mode B) ;
- signale les skills a forger proposes ;
- termine par la **prochaine piste naturelle** (celle a lancer en premier) et la
  commande/skill exact pour l'attaquer.
Puis inviter a `/pistes read` pour voir l'arbre a jour, et `/cahier-de-labo update`
si la prospection a elle-meme produit une connaissance (une analogie eclairante,
un lien litterature).

**Triage de perimetre avant d'ecrire (obligatoire, cf. `/recadrage`).** Une
prospection laterale genere par construction des pistes qui debordent l'objet du
projet : c'est meme son interet. Avant l'ecriture de la Phase 8, trancher pour
chaque survivante ou elle appartient :
- **dans le projet** (elle sert la question fondatrice ou l'article en cours) ->
  `pistes.md` du projet, comme decrit en Phase 8 ;
- **hors du projet** (autre gene, autre lignee, autre organisme, autre
  discipline) -> `pistes.md` du repertoire **parent**, au format
  `[SERENDIPITE <- <projet>]` avec ses sous-pistes d'amorcage obligatoires
  (litterature, test in silico minimal, critere go/no-go). Voir `/recadrage`
  Phase 3bis pour le format exact.
Une piste hors perimetre inscrite dans le projet disparaitra avec lui : c'est le
mode de perte que `/recadrage` existe pour empecher, et la Phase 9 est le dernier
moment ou l'on peut encore l'eviter sans relire tout le dossier.

Enfin, si la prospection revele que la question fondatrice elle-meme ne colle
plus a ce qui est su (l'objectif principal est tranche, ou le resultat le plus
solide n'est pas celui qu'annonce le titre), ne pas le traiter comme une piste :
le signaler et proposer `/recadrage` complet. Prospect imagine des directions
neuves ; il n'a pas autorite pour redefinir le cadre.

**(b) Rien n'a survecu.** Le dire franchement, sans remplissage :

```
=== Prospection : [projet] ===
Axes parcourus : [liste]. Candidates generees : N. Survivantes : 0.

Verdict : rien de neuf a haute valeur ne subsiste apres challenge.
Raisons dominantes : [deja fait / deja en piste / tue par modele nul / donnees absentes].

Ce projet parait avoir explore l'essentiel de son espace de pistes accessible
avec les donnees actuelles. Rouvrir la prospection quand [nouvel arrivage de
donnees / nouvelle lignee voisine / nouveau skill] change la donne.
```

C'est une conclusion honnete et souhaitable : ne pas la maquiller.

---

## Consignes generales

### Le skill DOIT
- Separer strictement divergence (Phases 2 et 2bis, sans censure) et challenge
  (Phase 6, sans complaisance).
- Parcourir **chaque** axe lateral retenu (lire `references/axes_lateraux.md`) ET
  faire les deux relectures retrospectives R1 (pistes.md) et R2 (cahier).
- Tracer chaque piste a sa **source** (axe lateral / retrospection Px / cahier
  date / lentille skill / inter-projet).
- Passer chaque candidate par un **modele nul** avant de la retenir.
- Verifier la litterature (`tbmonitor-papers` d'abord) avant de qualifier une
  piste d'originale.
- Ecrire dans `pistes.md` en **mutation locale**, format `/pistes` : soit une piste
  neuve (mode A), soit une **sous-piste** ajoutee sous une piste existante (mode B,
  enrichissement/split), sans jamais dupliquer ni ecraser.
- Assumer un verdict "plus rien a explorer" quand c'est le cas.

### Le skill NE DOIT PAS
- Executer des analyses lourdes (il suggere, il n'execute pas).
- Reecrire `pistes.md` en bloc, supprimer une piste, ou **modifier l'etat ou le
  texte d'une piste existante** (l'enrichissement mode B n'AJOUTE que des
  sous-pistes/notes ; il ne touche jamais le parent).
- Rebasculer soi-meme l'etat d'une piste (y compris rouvrir un `[abandonne]`) :
  proposer via une sous-piste et laisser `/pistes` trancher.
- Gonfler la sortie avec des pistes gadget pour paraitre productif.
- Presenter comme faisable une piste dont les donnees n'existent pas (la flaguer
  `hypothetique`).
- Ressusciter une piste `[abandonne]` sans argument neuf verifie levant sa raison.
- Utiliser `rm` (toujours `gio trash`).

### Integration avec l'ecosysteme
- **`/pistes`** : autorite sur la mutation de `pistes.md`. Ce skill ecrit dans son
  format ; les transitions d'etat ulterieures (`start`/`done`/`drop`) passent par
  `/pistes`.
- **`/challenge`** : la Phase 6 en applique la logique a chaque candidate.
- **`mtbc-bilan --deepen`** : complementaire. Lancer `bilan` pour l'etat
  consolide et la gap-analysis systematique ; `prospect` pour la divergence
  creative. Les deux peuvent alimenter `pistes.md` ; eviter les doublons via la
  garde de la Phase 1.
- **`/lit-review` et `tbmonitor-papers`** : appui litterature du challenge.
- **`/etat`** : quand une piste prospectee, une fois realisee, produit un acquis,
  `/pistes done` propose de migrer vers `etat_des_decouvertes.md`.
- **`/recadrage`** : geste complementaire et symetrique. `prospect` CREE de la
  matiere (directions neuves) ; `recadrage` la RANGE (destination de chaque
  acquis, essaimage hors projet, scission). La Phase 9 de ce skill applique son
  triage a chaud sur les pistes generees ; le recadrage complet, lui, relit tout
  le dossier et peut redefinir la question fondatrice -- ce que prospect ne fait
  jamais.
- **`/cahier-de-labo`** : consigner la seance de prospection si elle a produit une
  connaissance (analogie, lien litterature, contradiction inter-projets).

## Epilogue

A la fin, produire systematiquement :
1. Le **bilan narratif** (Phase 9a) ou le **verdict d'epuisement** (Phase 9b).
2. L'**etat de `pistes.md`** : combien de pistes ajoutees, sous quel(s) bloc(s).
3. La **prochaine action** : la premiere piste a lancer + le skill exact, ou la
   condition de reouverture de la prospection.
