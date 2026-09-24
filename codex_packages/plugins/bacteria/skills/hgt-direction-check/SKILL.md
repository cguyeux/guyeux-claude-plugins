---

name: hgt-direction-check
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST), peer-reviewed comparative
  genomics: decide the DIRECTION of a horizontal transfer before it becomes a
  claim, and kill the commonest way of getting it backwards. A high sequence
  identity between a bacterial gene and a viral (or plasmid, or any other donor
  candidate) gene says NOTHING about who captured whom: it measures a position
  inside the structure of the gene family. The test that does settle direction
  is topological, and it comes with its own null. (1) NESTING: build the family
  tree from a reference panel of CELLULAR homologues plus the sequences carried
  by the candidate donor, and ask whether each donor-borne sequence sits INSIDE
  the cellular diversity (capture cell - donor) or BASAL to it (the family
  would then originate in the donor). (2) HOST CONCORDANCE: nesting alone is
  not enough — each donor-borne sequence must land next to the homologues of
  its OWN host taxon, which is what separates a real capture from an arbitrary
  placement, and what turns one case into a repeated, independent result.
  (3) LONG-BRANCH CONTROL: the host clade must still exist in a tree inferred
  independently WITHOUT the donor sequences, otherwise the nesting was
  manufactured by the analysis. Also carries the correlation pre-test that
  disqualifies an identity-based argument in seconds, before any tree is built.

  Use when: a manuscript is about to say "this bacterial gene derives from a
  phage" (or from a plasmid, or an integron) on the strength of a BLAST
  identity; an insertion sequence, transposase or any mobile-element gene is
  found in a viral genome; a reviewer asks which way a transfer went; a
  striking identity to a viral gene needs to be checked against the plain
  alternative that it is simply the family's internal structure; or a negative
  result (no transfer detectable) must be made publishable rather than silent.
---

# hgt-direction-check — quel sens a pris le transfert, et la preuve qui le dit

## Pourquoi ce skill existe

Un manuscrit de ce dépôt a été **classé sans diffusion** parce que sa thèse centrale lisait
un transfert horizontal à l'envers. Il défendait une proximité inattendue entre deux séquences
d'insertion du MTBC (IS1081, IS1553) et le gène 30 du corynébactériophage Poushou, et en
faisait « a family-specific signature of the MTBC ». Le panel de famille IS256 contenait
pourtant deux éléments non-MTBC dont l'identité à ce même gène phagique dépassait celle
d'IS1553 de 23 à 27 points, et ils étaient absents du texte comme des figures.

Deux mesures ont suffi à retourner la lecture, et la seconde a demandé un arbre :

- **la corrélation** entre identité à la cible virale et identité au meilleur homologue
  CELLULAIRE de la même famille vaut rho = 0,913 (p = 1,0e-94, n = 240). « Être proche du
  gène phagique » n'est donc pas une propriété phagique, c'est une position dans la structure
  de la famille ;
- **la topologie** place les cinq séquences portées par des phages À L'INTÉRIEUR de la
  diversité cellulaire, 5 sur 5, chacune auprès des IS du phylum de son propre hôte, avec des
  clades d'accueil qui survivent au retrait des séquences phagiques. Le sens est
  **cellule vers phage**, établi trois fois indépendamment sur trois phylums d'hôtes.

La corrélation seule ne tranchait pas : elle disqualifiait l'argument d'identité sans dire qui
avait capturé qui. C'est le couple des deux qui conclut, et c'est ce couple que ce skill
outille.

## La règle, en une phrase

**Une identité de séquence ne porte aucune information de sens de transfert.** Avant d'écrire
qu'un gène bactérien dérive d'un phage, d'un plasmide ou de quoi que ce soit d'autre, mesurer
la corrélation qui disqualifie l'argument, puis, si l'affaire mérite d'être poursuivie,
produire l'arbre et son contrôle.

## Étape 0 — le pré-test qui coûte deux minutes

```bash
python3 scripts/identity_correlation.py --panel <famille.faa> --cible <gene_donneur.faa> \
    --reference <homologue_cellulaire.faa>
```

Pour chaque membre du panel, l'identité à la cible supposée donneuse et l'identité à un
homologue cellulaire de référence, puis leur corrélation de Spearman.

**Lecture.** Un rho élevé signifie que l'identité à la cible est prédite par la seule position
dans la famille : **l'argument d'identité est mort**, et il faut soit l'abandonner, soit passer
à la topologie. Un rho faible ne prouve rien de positif, il rend seulement la suite
intéressante.

**Le chiffre dépend de la définition de l'identité, et l'écart est mesuré.** Deux dénominateurs
circulent, et `--identity` les expose tous les deux. Sur le panel IS256 du cas fondateur
(n = 238) : **rho = 0,911 avec `full`** (dénominateur = longueur totale de l'alignement, gaps
compris — la définition des scripts d'origine, donc celle qui reproduit le 0,913 consigné au
registre à 0,002 près, l'écart résiduel venant de deux séquences exclues par le filtre de
longueur) et **rho = 0,715 avec `aligned`** (colonnes appariées seulement, la définition usuelle
de BLAST). La conclusion qualitative est la même dans les deux cas, mais `full` est le défaut
pour qu'un lecteur qui relit P68 retrouve son chiffre plutôt qu'un autre.

Garde-fou de cette étape : choisir l'homologue cellulaire de référence AVANT de voir le
résultat, et le choisir pour une raison indépendante (le plus proche par identité, ou le
prototype nommé de la famille), jamais parce qu'il donne le rho voulu.

## Étape 1 — construire le panel

```bash
python3 scripts/build_panel.py --family-faa <references_cellulaires.faa> \
    --hits <hits.tsv> --genomes <fasta_donneurs.fasta> --out <dossier>
```

Trois exigences, dont deux ont chacune failli fausser le résultat sur le cas fondateur :

1. **Le panel cellulaire doit être exhaustif pour la famille**, pas un trio choisi. Sur le cas
   fondateur, passer d'une seule référence (IS285) aux 241 références IS256 d'ISfinder a suffi
   à faire apparaître les deux éléments qui retournaient la lecture.
2. **Plusieurs taxons d'hôtes chez les donneurs, si la nature le permet.** C'est ce qui
   transforme un cas unique en résultat répété : sur le cas fondateur, quatre corynéphages
   d'actinobactéries (protéine strictement identique entre eux, donc une seule entrée après
   déduplication) mais aussi deux *Paenibacillus* phages et un *Staphylococcus* phage, soit
   des Firmicutes à 33-36 % d'identité. Trois phylums, trois tests indépendants.
3. **Dédupliquer par SÉQUENCE, pas par nom.** Quatre génomes distincts portant la même
   protéine ne sont pas quatre observations.

## Étape 2 — les deux arbres, jamais un seul

```bash
# sur mp ou mh, cf. le skill remote-compute
mafft --localpair --maxiterate 1000 --thread 16 panel.faa > panel.aln
iqtree2 -s panel.aln -m MFP -B 1000 -alrt 1000 -T 16 -pre panel
# et le contrôle, inféré INDÉPENDAMMENT sur le seul panel cellulaire
mafft --localpair --maxiterate 1000 --thread 16 panel_sans_donneurs.faa > panel_sans.aln
iqtree2 -s panel_sans.aln -m MFP -B 1000 -alrt 1000 -T 16 -pre panel_sans
```

Le second arbre n'est pas un luxe : c'est le modèle nul du premier. Sans lui, un nichage peut
être une fabrication de l'attraction des longues branches, ce que le `CLAUDE.md` de `mtbc/`
impose de contrôler (règle 2 de la validation taxonomique, née d'une fausse espèce nouvelle
qui avait survécu à 27 pages de manuscrit).

**Ne jamais élaguer le premier arbre pour fabriquer le second.** L'élagage rend les mêmes
partitions, donc un contrôle trivialement satisfait qui ne contrôle rien. Mesuré : sur le cas
fondateur, l'arbre élagué donnait 5/5 avant tout calcul indépendant, et l'arbre réellement
inféré a donné 5/5 aussi — mais il pouvait donner autre chose, et c'est tout l'intérêt.

## Étape 3 — lire les arbres

```bash
python3 scripts/read_direction.py --tree panel.treefile --tree-control panel_sans.treefile \
    --hosts hosts.tsv --origins <famille.csv> --out verdict.txt
```

Trois mesures, et aucune ne conclut seule.

- **Nichage.** Pour chaque feuille donneuse, le plus petit ancêtre contenant au moins une
  référence cellulaire. Un clade d'accueil de 1 % de l'arbre signe un nichage profond ; une
  séquence basale n'a de cellulaires qu'à un ancêtre très haut.
- **Concordance d'hôte.** Le clade d'accueil doit porter des homologues du taxon de l'hôte du
  donneur. Un nichage sans concordance ne vaut pas démonstration.
- **Contrôle LBA.** L'ensemble des feuilles cellulaires du clade d'accueil doit être un clade
  de l'arbre de contrôle, à une feuille près (tolérance déclarée d'avance, jamais ajustée
  après coup).

Si le contrôle manque (calcul en cours, machine injoignable), le script rend le nichage et les
supports en marquant le contrôle « NON MESURÉ » **et ne prononce aucun verdict**. Une première
version affichait « OUI » par ligne dans ce cas : c'était le faux positif exact que tout le
dispositif existe pour empêcher.

## Pièges d'outillage, tous payés sur le cas fondateur

- **Biopython ne parse pas le support composite d'IQ-TREE.** Un treefile produit avec `-B` et
  `-alrt` écrit `SH-aLRT/UFBoot` (par exemple `94.4/100`) ; `Bio.Phylo` rend alors
  `confidence = None`, donc un nœud à UFBoot 100 se lit comme un nœud SANS support.
  `read_direction.py` lit le Newick deux fois, une fois avec chaque moitié du champ.
- **Le rattachement des taxons à leur phylum doit être instruit, pas devine.** Oublier
  *Pelotomaculum*, *Desulfotomaculum*, *Veillonella* et *Caldicellulosiruptor*, tous des
  Bacillota, transformait une concordance en discordance. Les taxons non rattachés sont
  comptés à part, jamais versés dans « autre », qui se lirait comme une discordance établie.
- **Un clade d'accueil à UNE seule référence cellulaire n'est pas testable par partition** :
  une feuille isolée n'est jamais une partition interne, et le contrôle rendrait NON par
  construction. Remonter au premier ancêtre portant au moins deux cellulaires.
- **Ne jamais repérer un champ ou une séquence par son CONTENU** quand un identifiant existe.
  Corollaire général appris ailleurs le même jour, mais qui vaut ici pour les en-têtes FASTA.
- **Une base BLAST construite sans `-parse_seqids`** répond « DB contains no accession info »
  à tout `blastdbcmd -entry`, quelle que soit la forme de l'identifiant. Extraire depuis les
  FASTA sources.

## Ce que le skill ne fait pas

Il ne date pas le transfert, ne dit pas combien de fois il a eu lieu au-delà du nombre de
nichages indépendants observés, et ne remplace pas une recherche d'antériorité : le sens d'un
transfert peut être déjà publié pour la famille étudiée, et le vérifier coûte quelques
requêtes avant d'engager deux arbres. Sur le cas fondateur, aucune antériorité n'a été trouvée
pour la famille IS256 chez les corynéphages, ce qui laissait le créneau ouvert — mais ce
négatif vaut ce que vaut une recherche web, et il est consigné comme tel.

## Cas fondateur et traçabilité

`mtbc/pistes.md` P68 (sérendipité issue de `SpacerEgalVirus`), sous-pistes P68.1 (littérature),
P68.2 (la phylogénie, close le 2026-09-12) et P68.3 (décision). Scripts d'origine :
`SpacerEgalVirus/analyses/phase58_p14_1_ismlu3_isbli2.py` (la corrélation),
`phase61_p68_2_phylogenie_is256.py` (le panel) et `phase61b_p68_2_lecture_arbre.py` (la
lecture). Le manuscrit qui portait la lecture inverse a été classé sans diffusion le
2026-09-08, et ce classement se trouve confirmé a posteriori par la topologie.
