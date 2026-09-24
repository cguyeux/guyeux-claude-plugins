---
name: hgt-interdomain-check
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST), peer-reviewed comparative
  genomics: tests whether a gene bearing a "eukaryotic" domain in a bacterial
  published research genome really crossed the domains of life, or whether the
  signal is an artefact. Four gates, in order: ASSEMBLY CONTAMINATION first (a
  foreign contig produces exactly the signature one is about to publish),
  AMINO-ACID COMPOSITION and SATURATION between domains (which the long-branch
  control of a mobile-element analysis does not cover), an explicit TOPOLOGY
  TEST (AU) against the no-transfer hypothesis instead of merely reading a
  nesting, and TAXONOMIC concordance of the neighbourhood in place of host
  concordance, which is meaningless for a free-living eukaryotic donor.

  Use when: a bacterial protein carries a domain described as eukaryotic (SET,
  ankyrin, F-box, histone-modifying); a manuscript is about to claim an
  acquisition from a host or from an environmental eukaryote; a reviewer asks
  whether a bacteria-to-eukaryote transfer is established; or a spectacular
  cross-domain transfer needs to be ruled out before it is written up.
  For a cellular-family-versus-mobile-element case (phage, plasmid, integron),
  use the sibling skill hgt-direction-check instead.
---

# hgt-interdomain-check — un gène a-t-il vraiment traversé les domaines du vivant

## Pourquoi ce skill existe, et pourquoi il n'est pas une extension de son frère

`hgt-direction-check` tranche le SENS d'un transfert entre une famille cellulaire et un
élément mobile. Il a été écrit sur un cas où la lecture inverse avait produit un manuscrit
classé sans diffusion. Il est net, et il doit le rester.

Un cas inter-domaine n'est pas le même objet, mesuré le 2026-09-22 en lisant son corps :
son `read_direction.py` exige un `hosts.tsv` qui rattache chaque séquence donneuse au taxon de
SON HÔTE, notion vide de sens pour un donneur eucaryote libre vivant ; son unique contrôle
d'artefact est un arbre inféré sans les donneurs, qui ne teste ni la composition ni la
saturation ; et il ne contrôle pas du tout ce qui est le PREMIER suspect d'un « gène eucaryote
chez une bactérie », à savoir que le gène ne soit pas dans le génome mais dans l'assemblage.
Ce skill apporte les quatre choses qui manquent, et réutilise le reste : il IMPORTE le socle de
lecture d'arbre de son frère (`read_direction.py`) au lieu d'en recopier le parseur.

Précédent qui a décidé de la forme : `ani-panel-classify` a été écrit comme skill NEUF plutôt
qu'en extension de `species-id`, et ce choix a bien vieilli.

## La règle, en une phrase

**Un domaine protéique dit « eucaryote » chez une bactérie n'est pas une trace d'acquisition,
c'est une question.** Avant d'écrire qu'un gène vient d'un hôte ou d'un eucaryote de
l'environnement, prouver d'abord qu'il est dans le génome, puis que l'arbre qui le dit a le
droit d'être lu, puis que l'hypothèse contraire est rejetée par un test.

## Porte 0 — le gène est-il seulement dans le génome (bloquante)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/hgt-interdomain-check/scripts/assembly_contamination_check.py \
    --protein-accession <ACCESSION> --genbank <genome.gbff> --locus-tag <LOCUS> \
    --out contamination.txt
```

Le critère décisif n'est pas la phylogénie, c'est la **répétition indépendante** : la même
protéine portée à l'identique par des dizaines d'assemblages, produits par des laboratoires et
des années différents, n'est pas un artefact, il faudrait que la même contamination se soit
produite partout. Le script lit cette répétition en une requête dans la base *Identical Protein
Groups* du NCBI, et y ajoute quatre mesures de contexte : GC du gène contre la distribution des
CDS de longueur comparable (et non contre la moyenne de tous les CDS, qui fabrique une anomalie
pour tout gène court), position dans le réplicon et distance au bord du contig, voisinage
annoté, couverture du contig quand l'assembleur la donne.

Quatre issues, et une seule ouvre : `PASSE`, `SUSPECT`, `BLOQUE`, `NON_CONCLUANT`. Un rapport
qui déclare `PASSE` sur la seule répétition dit explicitement ce qu'il n'a PAS mesuré, pour
qu'un lecteur ne lise pas un contrôle de GC qui n'a pas eu lieu.

**Ce que coûte de sauter cette porte** : les transferts horizontaux massifs annoncés chez les
tardigrades en 2015 étaient de la contamination d'assemblage, et ils avaient franchi l'examen
par les pairs.

## Étape 1 — l'antériorité, puis le panel

L'antériorité d'abord, et elle n'est pas optionnelle : la question « ce domaine eucaryote chez
une bactérie est-il vertical ou horizontal ? » a souvent déjà été posée pour la famille, et y
répondre à nouveau sans le savoir est le meilleur moyen de se faire renvoyer un manuscrit.
Pour les domaines SET bactériens, c'est Alvarez-Venegas et al. 2007, *Mol. Biol. Evol.*
(PMID 17148507), vingt ans d'avance.

Le panel se construit ensuite par le domaine, et non par des hits BLAST contre des génomes
donneurs comme dans le skill frère, dont le `build_panel.py` ne convient donc pas ici :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/hgt-interdomain-check/scripts/panel_from_pfam.py \
    --pfam PF00856 --group BACTERIA:2 --group EUKARYOTA:2759:reviewed --group ARCHAEA:2157 \
    --query-faa requete.faa --query-label <REQUETE> --query-group <phylum> \
    --max-per-genus 2 --max-per-group 70 --out panel/
```

Il fait quatre choses qu'il ne faut pas faire à la main. **Il extrait le domaine à ses
coordonnées** : aligner un domaine de 143 aa contre des protéines eucaryotes de 1 200 aa est la
façon la plus sûre de fabriquer un artefact, et l'API InterPro donne les bornes. **Il
déduplique par séquence**, jamais par nom. **Il équilibre par genre** à graine fixe, parce
qu'un panel de trente souches du même genre n'est pas trente observations. Et **il rattache
chaque séquence à son phylum par la taxonomie NCBI**, en écrivant à part les séquences qu'elle
ne rattache pas, plutôt que de les verser dans un phylum qui se lirait comme une discordance.

L'exigence qui commande tout le reste, et qui est la leçon centrale de cette littérature :

> **Inclure les espèces LIBRES et environnementales du groupe.** Le paradigme d'un transfert
> hôte vers bactérie pour les domaines SET reposait sur leur présence chez les seules bactéries
> pathogènes et symbiotiques — c'est-à-dire sur le biais d'échantillonnage des génomes
> séquencés à l'époque. Élargir aux espèces libres a suffi à retourner la lecture. Pour
> *Leptospira*, cela veut dire les saprophytes (clade S, *L. biflexa*) et pas seulement
> *L. interrogans*.

`topology_test.py constraints` refuse d'ailleurs de tourner sur un panel de moins de deux
bactéries ou deux eucaryotes, en rappelant ce précédent.

## Étape 2 — l'arbre a-t-il le droit d'être lu

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/hgt-interdomain-check/scripts/composition_saturation.py \
    --alignment panel.aln --focus <REQUETE> --tree panel.treefile \
    --out-recoded panel_dayhoff6.aln --out composition.txt
```

Deux artefacts fabriquent un faux transfert inter-domaine, et le contrôle d'attraction des
longues branches du skill frère n'en couvre aucun :

- **l'hétérogénéité de composition** en acides aminés, qui regroupe les séquences par leur
  usage des résidus plutôt que par leur ascendance. Test du chi2 de chaque séquence contre la
  composition moyenne du jeu, comme IQ-TREE l'imprime ;
- **la saturation**, mesurée par la fraction de paires dont la p-distance dépasse 0,85 et, si un
  arbre est fourni, par la pente de la p-distance contre la distance patristique.

Le script écrit aussi l'alignement **recodé** (Dayhoff-6 par défaut, SR-4 pour les jeux les plus
saturés) : un transfert qui disparaît au recodage était une affaire de composition, pas
d'ascendance. Quatre verdicts : `HOMOGENE`, `HETEROGENE`, `SATURE`, `HETEROGENE_ET_SATURE`. Dès
que le verdict n'est pas `HOMOGENE`, l'étape 4 EXIGE l'arbre recodé et refuse de conclure sans.

## Étape 3 — les arbres, puis le test, jamais la seule lecture

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/hgt-interdomain-check/scripts/topology_test.py constraints \
    --alignment panel.aln --taxonomy taxonomy.tsv --query <REQUETE> \
    --model LG+C60+F+G --iqtree-bin iqtree --out au/
bash au/commandes.sh          # sur mp ou mh : cf. science-commun:remote-compute
python3 ${CLAUDE_PLUGIN_ROOT}/skills/hgt-interdomain-check/scripts/topology_test.py read \
    --iqtree au/au_test.iqtree --order au/trees_order.txt --out topologie.txt
```

Le nichage est une propriété de l'arbre retenu ; il ne dit rien de la marge. Le test AU demande
si l'arbre où **les bactéries restent monophylétiques, requête comprise** est rejeté par les
données. S'il ne l'est pas, le nichage observé est compatible avec l'absence de transfert, et
il n'y a pas de résultat. Trois verdicts : `TRANSFERT_SOUTENU`, `VERTICAL_SOUTENU`,
`INDECIDABLE` — et le troisième est fréquent sur un domaine court et ancien, ce n'est pas un
échec mais une réponse.

Le modèle par défaut est à profils hétérogènes (`LG+C60+F+G`) parce qu'un test AU sous modèle
homogène hérite de l'artefact qu'il est censé arbitrer. Prévoir aussi, dans le même run,
l'arbre **sans la requête** (contrôle) et l'arbre sur l'alignement **recodé**.

**Limite du test, mesurée sur PF00856 le 2026-09-24, à lire avant d'interpréter un double
rejet.** H1 et H2 ne diffèrent que par le placement de la requête, mais toutes deux imposent
une bipartition **globale** bactéries | eucaryotes. Dès que le domaine a une histoire réticulée,
cette bipartition est rejetée en soi et les deux arbres contraints sont pénalisés pour une
raison étrangère à la requête : les deux hypothèses tombent, et le verdict est `INDECIDABLE`
quel que soit le placement. Sur le panel SET de validation, le MRCA des 82 bactéries **est
l'arbre entier**, et ni les eucaryotes, ni les archées, ni même les Spirochaetota ne sont
monophylétiques. Le paradoxe est que l'exigence de panel large héritée d'Alvarez-Venegas
(inclure les espèces libres et environnementales) rend ce cas d'autant plus probable. Deux
conséquences pratiques : contrôler la monophylie de chaque domaine dans l'arbre libre avant de
lire le tableau AU, et, sur un double rejet, s'en remettre au placement dans l'arbre libre et à
son support — ce que fait `read_interdomain.py`, dont le verdict ne dépend pas de celui-ci.
`topology_test.py read` distingue désormais le double rejet de l'absence de rejet et reporte
l'écart de logL entre les deux, sans autoriser à retenir la moins rejetée.

### Mode local : tester le placement de la requête, pas la monophylie des domaines

Dès qu'un domaine n'est pas monophylétique dans l'arbre libre, préférer `--local`. Il exige
les deux arbres déjà prévus ci-dessus : l'arbre ML libre et l'arbre **sans la requête**.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/hgt-interdomain-check/scripts/topology_test.py constraints \
    --local --alignment panel.aln --taxonomy taxonomy.tsv --query <REQUETE> \
    --reference-tree sans_requete.treefile --ml-tree ML_libre.treefile \
    --model LG+C60+F+G --iqtree-bin iqtree --out au_local/
# une inférence contrainte par ligne de commandes.sh (indépendantes : un job chacune),
# puis le test AU sur les arbres distincts ; lecture comme en mode global :
python3 ${CLAUDE_PLUGIN_ROOT}/skills/hgt-interdomain-check/scripts/topology_test.py read \
    --iqtree au_local/au_local.iqtree --order au_local/trees_order.txt --out topologie.txt
```

La règle de choix des ensembles de référence est une décision de méthode, fixée ainsi :

- **Lue sur l'arbre SANS la requête**, jamais sur celui qui la contient : choisir les ensembles
  d'après le placement qu'on veut tester serait circulaire. Le script refuse un arbre de
  référence qui contient la requête.
- **Côté vertical** : chaque clade maximal pur du groupe fin de la requête (3e colonne de la
  taxonomie), d'au moins `--min-clade` séquences. **Côté transfert** : chaque clade maximal pur
  du domaine donneur. **Tous sont testés, aucun n'est élu** : sur PF00856, le clade eucaryote
  « le plus proche » de la requête est celui de 2 séquences en distance topologique et celui
  de 34 en distance patristique, et deux des quatre clades eucaryotes ne survivent pas à l'ajout
  de la requête. Un seul donneur choisi à la main aurait été arbitraire. `--donor-clade` reste
  possible pour une hypothèse pré-enregistrée, à condition d'être un clade réel de l'arbre de
  référence (sinon son rejet ne dirait rien de la requête, et le script refuse).
- **Contrainte partielle** : H_C impose le seul partage {requête} ∪ C | autres ensembles ; les
  séquences hors ensembles restent libres. C étant un côté d'arête de l'arbre de référence, ce
  partage y tient déjà sans la requête : seule la requête peut être pénalisée.
- **Alias** : une hypothèse que l'arbre ML satisfait déjà reprend CET arbre, sans inférence.
  Surtout pas de doublon dans le test AU : deux arbres identiques s'y partagent les victoires
  RELL et leurs p-AU deviennent fausses.
- **Arbre de départ compatible** pour chaque inférence (l'arbre de référence, la requête
  greffée sur la branche de C) : une recherche contrainte restée dans un optimum local
  sous-estime la vraisemblance de H_C et gonfle son rejet, c'est-à-dire fabrique un
  `VERTICAL_SOUTENU`.

Lecture : `VERTICAL_SOUTENU` si tous les clades donneurs sont rejetés et un clade de la lignée
ne l'est pas ; `TRANSFERT_SOUTENU` dans le cas symétrique ; `INDECIDABLE` si au moins un de
chaque famille survit (le signal de la requête manque, ce n'est plus un artefact). Si tout est
rejeté, le verdict reste `INDECIDABLE` mais la lecture change de sens par rapport au mode
global : ce n'est plus un artefact des contraintes, la requête se range ailleurs, et le
transfert depuis chacun des clades donneurs testés est bien rejeté. Limite : une séquence
isolée du domaine donneur (hors clade d'au moins `--min-clade`) n'est jamais proposée comme
sœur de la requête.

Coût mesuré sur le cas SET (159 séquences, `LG+C60+F+G`, 16 cœurs) : une inférence
contrainte partie d'un arbre quelconque a demandé 6 h 25 et ~101 h CPU en AG2 ; le mode local
en lance une par clade donneur (quatre ici), en parallèle.

Sur `mh`, l'environnement phylo est `/Work/Users/cguyeux/envs/phylo`, le binaire s'appelle
**`iqtree`** et non `iqtree2`, et `LD_LIBRARY_PATH=$P/lib` est exigé. `commandes.sh` lit `IQ` et
`ALN` dans l'environnement, donc rien à réécrire : `IQ=$P/bin/iqtree bash commandes.sh`.

## Étape 4 — la lecture, et le refus de conclure

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/hgt-interdomain-check/scripts/read_interdomain.py \
    --tree panel.treefile --tree-control panel_sans_requete.treefile \
    --tree-recoded panel_dayhoff6.treefile --taxonomy taxonomy.tsv --query <REQUETE> \
    --contamination-report contamination.txt --composition-report composition.txt \
    --topology-report topologie.txt --out verdict.txt
```

Quatre mesures, et aucune ne conclut seule :

- **enfouissement** : combien de feuilles de l'autre domaine surmontent la requête sans
  interruption. Sœur du groupe eucaryote n'est pas la même chose qu'enfouie sous douze
  eucaryotes successifs ;
- **cohérence taxonomique du voisinage**, qui remplace la concordance d'hôte : les plus proches
  voisins forment-ils un groupe cohérent (des plantes vertes, des champignons) ou un assortiment
  de lignées distantes, ce qui est la signature d'un artefact ;
- **survie au retrait de la requête** : le clade d'accueil existe-t-il sans elle, ou a-t-il été
  fabriqué par sa présence ;
- **stabilité au recodage** : le voisinage reste-t-il du même domaine sur l'arbre recodé.

Le script **relit les lignes machine-lisibles** laissées par les trois étapes amont et **ne
prononce aucun verdict** si l'une manque. Un rapport absent n'est pas un rapport favorable.
Cinq issues : `CONTAMINATION_PROBABLE`, `AUCUN_VERDICT`, `TRANSFERT_INTER_DOMAINE_SOUTENU`,
`ORIGINE_PROPRE_AU_DOMAINE`, `INDECIDABLE`.

## Pièges d'outillage, tous payés en écrivant ce skill

- **Le tableau « USER TREES » d'IQ-TREE sépare ses marqueurs `+`/`-` par une espace.** Un
  `split()` naïf donne des tokens `+` isolés qui décalent toutes les colonnes d'un cran, et on
  lit alors un `c-ELW` en croyant lire un `p-AU`, sans aucune erreur visible. Le parseur repère
  `p-AU` par son indice dans l'en-tête, filtre les marqueurs, et refuse la ligne si le compte ne
  tombe pas juste.
- **Un état d'acides aminés absent du jeu rendait `nan` la statistique de TOUTES les séquences.**
  L'effectif attendu nul faisait une division par zéro, et le test de composition ne détectait
  alors plus rien, en silence. Les états absents sont retirés et les degrés de liberté suivent.
- **`root_at_midpoint` de Biopython échoue sur `UnboundLocalError: tip1`** quand le Newick n'a
  pas de longueurs de branche (arbre de contrainte, topologie écrite à la main). Le socle
  détecte le cas et poursuit sans raciner : « basal » perd son sens, le nichage non.
- **Les parcours de clades de Biopython sont récursifs** et dépassent la limite par défaut sur
  un arbre de quelques centaines de feuilles un peu déséquilibré. Mesuré le 2026-09-22 en
  rejouant le cas fondateur sous Python 3.14 / Biopython 1.87, où il passait auparavant : la
  limite est relevée à la lecture de l'arbre.
- **Les distances patristiques coûtent cher** (30 000 appels pour 246 feuilles) : au-delà de
  `--max-pairs`, l'échantillon est tiré à graine fixe, donc reproductible.
- **Le rattachement taxonomique doit être INSTRUIT, jamais deviné.** Les feuilles sans domaine
  déclaré sont comptées à part et jamais versées dans un domaine, qui se lirait comme une
  discordance établie. Corollaire hérité du frère, vérifié à nouveau ici : une colonne
  d'origine mal indexée a fait rendre 0/5 concordances là où il y en a 5.

## Ce que le skill ne fait pas

Il ne date pas le transfert, ne compte pas ses occurrences, et ne nomme pas l'espèce donneuse :
un voisinage cohérent désigne un groupe taxonomique, jamais une espèce. Il ne dit rien de la
FONCTION du gène, qui est souvent la question la plus intéressante et la plus testable — pour
une nucléomoduline candidate, la question « modifie-t-elle la chromatine de l'hôte, comme RomA
chez *Legionella* ? » est plus neuve et plus décidable que « de quel eucaryote vient-elle ? ».
Et il ne remplace pas la recherche d'antériorité de l'étape 1.

## Cas de validation et traçabilité

- **Non-régression du socle partagé** : le cas fondateur IS256 du skill frère (P68.2,
  `mtbc/clos_soumis/SpacerEgalVirus`) rejoué le 2026-09-22 après modification de
  `read_direction.py` rend 5/5 nichages, 5 concordances, 5 contrôles, soit le verdict
  CELLULE → DONNEUR du 2026-09-12, inchangé.
- **Cas inter-domaine documenté** : les gènes bactériens à domaine SET, Alvarez-Venegas et al.
  2007. Leur dispositif est déjà celui d'ici en réduction (phylogénie, signes d'insertion dans
  la région chromosomique, GC du gène contre GC du chromosome), et leur conclusion est un
  verdict NÉGATIF : les gènes SET ont une histoire bactérienne propre, et le paradigme du
  transfert depuis l'hôte venait d'un échantillon biaisé. C'est le type de verdict que
  `ORIGINE_PROPRE_AU_DOMAINE` porte, et il est publiable.
- **Porte 0 exécutée sur un cas réel** : `LIMLP_01555` (`AKP24757.1`, SET domain-containing
  protein de *L. interrogans* Manilae, 143 aa), demandé par Alexandre Giraud-Gatineau le
  2026-09-18. La protéine identique est portée par **852 assemblages indépendants** de
  *Leptospira* : la contamination d'assemblage est écartée, et la question du sens reste
  entière. Mesure du 2026-09-22, à refaire si elle est citée dans un manuscrit.
- Tests : `_audit/tests/test_hgt_interdomain_check.py` (30 contrôles sur jeux fabriqués, dont
  10 pour le mode local : ensembles, contraintes partielles, arbres de départ, alias, verdicts).
- Pistes : `~/docs/environnement/pistes.md` AG2, AG3 ; contexte scientifique et antériorités :
  `~/.agents/knowledge/leptospira.md` ; volet scientifique : `mtbc/pistes.md` P78.5.
