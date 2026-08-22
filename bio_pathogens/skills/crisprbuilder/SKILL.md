---
name: crisprbuilder
description: >
  Academic research toolkit (Guyeux group, FEMTO-ST), peer-reviewed comparative genomics:
  extrait un locus CRISPR (DR consensus, arrays, spacers) d'un genome, d'un assemblage ou
  de reads, SANS catalogue de motifs prealable, par decouverte de novo du direct repeat.
  Successeur outille de CRISPRbuilder-TB (Guyeux 2021), dont il leve le verrou : celui-ci
  ne reconnait que les 221 motifs du MTBC et ne trouve donc RIEN chez une souche a DR
  different, comme les M. canettii a systeme de type I-G, I-E ou I-C. Use when: extraire les
  spacers d'une souche, comparer des repertoires d'espaceurs entre lignees ou especes,
  spoligotypage in-silico, verifier si un locus a survecu a l'assemblage, ou identifier un
  systeme CRISPR inconnu chez une bacterie hors MTBC.
---

# crisprbuilder — extraction d'un locus CRISPR sans catalogue

> [!TIP]
> **Trois outils publiés à connaître pour le spoligotypage in silico.** **SpoTyping** (lectures
> courtes) est la référence usuelle ; **Galru** (`github.com/quadram-institute-bioscience/galru`,
> GPL-3.0) fait du spoligotypage rapide depuis des **lectures longues non corrigées**, angle que ce
> skill ne couvre pas ; **TGS-TB** (`gph.niid.go.jp/tgs-tb/`, `10.1371/journal.pone.0142951`) combine
> spoligotypage, phylogénie et détection d'IS dans une interface web ; **lorikeet** (AbeelLab) fait de
> l'empreinte génétique. Notre `SpolLineages` reste l'outil de prédiction de familles, et il est
> indexé dans bio.tools. Pour comparer une reconstruction locale à ces sorties, exiger le même jeu de
> spacers de référence des deux côtés, sinon le désaccord ne mesure que la convention.


## Ce que c'est, et pourquoi il existe

`scripts/crisprbuilder2.py` extrait un locus CRISPR complet (DR consensus, arrays,
spacers dans l'ordre) depuis un genome, un assemblage ou des reads. Il ne depend
d'**aucun catalogue de motifs** : le DR est soit fourni, soit **decouvert de novo**.

Il prolonge **CRISPRbuilder-TB** (Guyeux 2021, *PLOS Comput Biol* 17(3):e1008500,
`github.com/cguyeux/CRISPRbuilder-TB`), dont il reprend l'idee juste — reconstruire le
locus depuis les READS, jamais depuis l'assemblage — en levant sa limite structurelle :
l'original blaste un fichier de **221 motifs connus du MTBC**
(`data/fastas/crispr_patterns.fasta`) et ne peut donc rien trouver la ou le DR differe.
Or *M. canettii* porte au moins **quatre systemes distincts** (III-A avec le DR du MTBC,
I-G, I-E, I-C) dont les DR n'ont aucun rapport entre eux.

## Utilisation

```bash
CB=~/docs/codes/claude_plugins/bio_pathogens/skills/crisprbuilder/scripts/crisprbuilder2.py

python3 $CB detect  --genome g.fasta                      # quel(s) DR dans ce genome ?
python3 $CB extract --genome g.fasta --json out.json      # DR de novo + arrays + spacers
python3 $CB extract --genome g.fasta --dr GTCGTCAGACC...  # DR connu (plus rapide, plus sur)
python3 $CB extract --reads r.fastq.gz --json out.json    # depuis des lectures locales
python3 $CB extract --reads https://.../ERRxxx.fastq.gz --limit 1500000   # EN FLUX, rien sur disque
python3 $CB extract --genome g.fasta --fasta spacers.fa   # ecrit les spacers du plus grand array
python3 $CB batch   --glob '.../*/assembly/contigs.fasta' --json all.json
python3 $CB qc      --genome g.fasta --attendu Mycobacterium --taille-attendue 4400000
```

`--reads` accepte une **URL** : les lectures sont alors streamees et analysees a la volee, sans
jamais etre ecrites. Sur un lot de 150 runs cela evite ~39 Go de fichiers temporaires — et
`--limit` fait qu'on ne telecharge meme pas le fichier entier.

Sortie JSON : `dr`, `dr_conservation`, `n_arrays`, `n_spacers_total`, et pour chaque array
`sequence / strand / start / end / span / n_dr / n_spacers / spacers[]`. Chaque candidat de
`dr_candidates` porte en plus `spacer_diversity` (proche de 1 pour un vrai array, proche de
0 pour une repetition en tandem) et `validation_score`.

Compter **~75 s et ~250 Mo par genome bacterien** en detection aveugle ; fournir `--dr`
evite entierement la phase de decouverte et rend l'extraction quasi instantanee. C'est la
bonne option des qu'on traite un lot de souches du meme clade.

## Comment la decouverte de novo fonctionne

Un DR CRISPR est un k-mer qui (1) revient souvent et surtout (2) revient **a intervalles
reguliers**, l'intervalle valant DR + spacer, soit 55 a 130 nt. **C'est la seconde condition
qui fait tout le travail** : elle distingue un DR d'un simple repete genomique, et c'est
elle qui evite les faux positifs sur les familles repetees en tandem (PE-PGRS, MIRU), ou
les ecarts sont bien plus courts et irreguliers.

La periodicite ne suffit pourtant pas : une repetition en tandem la satisfait aussi bien,
et mieux (ses ecarts sont parfaitement constants la ou un array CRISPR varie de quelques
nucleotides, ses spacers etant de longueurs inegales). Les candidats sont donc **reclasses
par validation** : on extrait reellement l'array de chacun et on le note sur trois termes,

    nombre de spacers  x  conservation du DR (au carre)  x  diversite des spacers

la conservation entrant au carre parce que l'ecart utile se joue dans les dix derniers
points (CRISPRCasdb : 93,1 % en moyenne a l'evidence 4, 41,6 % a l'evidence 2), et la
diversite parce que c'est le seul terme qui separe vraiment un CRISPR d'un VNTR.

Le comptage de k-mers passe par un **filtre de comptage a memoire bornee** : les k-mers de
21 nt vus plusieurs fois dans un genome bacterien sont rares, il est donc inutile de payer
le stockage des millions de k-mers uniques. Une premiere passe marque les seaux vus au
moins deux fois, une seconde ne releve les positions que de ceux-la. Aucun faux negatif
possible, et le resultat ne depend pas de la graine de hachage puisque la seconde passe
recompte exactement.

## Validation, contre CRISPRCasdb comme verite independante

Banc reproductible : `scripts/valider.py --data <repertoire des fasta>`. Il rejoue les
six genomes ci-dessous en detection totalement aveugle et compare le DR rendu au consensus
evidence 4 de CRISPRCasdb, dans les deux sens de lecture.

| genome | systeme | avant (2026-08-03) | apres (2026-08-10) |
|---|---|---|---|
| H37Rv NC_000962.3 | III-A | exact, 37 spacers | **exact**, 37 spacers, 99,8 % |
| *M. canettii* CIPT 140010059 | III-A | exact | **exact**, 29 spacers, 100 % |
| CIPT 140070005 | I-E | exact (brin -) | **exact**, 105 spacers, 100 % |
| CIPT 140070010 | I-C / I-G | exact, les deux systemes | **exact**, 53 spacers |
| CIPT 140070008 | I-G | **faux** (un VNTR l'emportait) | **exact**, 36 nt |
| CIPT 140070017 | I-G | quasi-exact (1 mismatch) | **quasi-exact** (1 mismatch) |

**6 cas sur 6**, contre 5 sur 6 auparavant, en **468 s au lieu de 745** et avec **248 Mo
de memoire residente au lieu de 1,25 Go**. Les orientations inverses sont normales : les DR
sont rendus dans le sens du brin ou ils ont ete vus, comparer toujours les deux sens.

Le « quasi-exact » de CIPT 140070017 n'est pas un echec de l'outil : le DR rendu differe
d'un seul nucleotide du consensus de reference, lequel a ete calcule sur une AUTRE souche
(CIPT 140070008) ; la conservation de 99,8 % mesuree sur les copies de 140070017 dit que
c'est bien sa base a elle.

### Ce que le petit array cassait, et comment il a ete repare

Le seul echec du banc, CIPT 140070008 (10 copies du DR), avait quatre causes distinctes
qui se masquaient l'une l'autre. Elles sont documentees ici parce que les trois premieres
se rencontreront ailleurs :

1. **Le seuil de conservation etait fixe (80 %) alors qu'il doit dependre de l'effectif.**
   Avec 10 copies dans un genome a 65 % de GC, une colonne de spacer atteint 8/10 par
   hasard trois fois sur mille : l'extension mordait sur le spacer et rendait 41 nt. Le
   critere est desormais binomial, lu contre la composition du genome — 9/10 exiges a dix
   occurrences, 26/30 a trente.
2. **La deduplication se faisait APRES extension, sur un quota de 15 DR distincts.** Le
   vrai DR arrivait au rang 80 des 649 k-mers periodiques, avec un score a peine inferieur
   aux premiers : il n'etait jamais teste. La deduplication porte maintenant sur le LOCUS
   (les occurrences tombent-elles aux memes endroits ?) et precede l'extension.
3. **Rien ne distinguait un CRISPR d'une REPETITION EN TANDEM.** Un VNTR de 11 copies d'un
   motif de 23 nt, a 69 nt d'ecart onze fois de suite, battait le vrai locus sur tous les
   criteres : meme periodicite, meme conservation (100 %). Ce qui les separe est ce qu'il
   y a ENTRE les copies — le champ `spacer_diversity` mesure l'identite moyenne entre
   spacers (Jaccard sur les 8-mers). Un VNTR tombe a 0,1, un array CRISPR reste au-dessus
   de 0,95. Un simple test d'unicite ne suffisait pas : le VNTR rend 7 spacers « distincts »
   sur 10, qui sont des variantes a un nucleotide.
4. **La regle de parcimonie sur la longueur, devenue nuisible.** Elle compensait la
   sur-extension ; celle-ci corrigee, elle ne faisait plus que preferer les graines de
   21 nt aux vrais DR de 36 nt. Retiree.

Le filtre de basse complexite, qui n'etait applique qu'aux lectures, l'est aussi aux
genomes : les repetitions GC des familles PE-PGRS passaient autrement en tete.

### ⚠ La detection de novo depuis des LECTURES etait cassee, en silence

Mesure le 2026-08-10 sur des lectures simulees depuis le locus de H37Rv, a couverture 50x :

| longueur des lectures | ancien consensus | nouveau |
|---|---|---|
| 75 nt | `GTCGGCTCGGGGGGGGTGGGG` — **pas meme un morceau du DR** | DR exact, 36 nt |
| 100 nt | 21 nt, graine non etendue | DR exact, 36 nt |
| 150 nt | 21 nt, graine non etendue | DR exact, 36 nt |

Cause : les contextes d'occurrence etaient decoupes sans remplissage, si bien qu'une
occurrence situee a moins de 50 nt du bord decalait toutes ses colonnes. Sur un chromosome
complet cela ne concerne qu'une poignee de positions ; sur des lectures courtes, c'est
presque toutes. Le symptome visible etait ailleurs : ~14 % des DR « detectes » sur un lot
de 151 souches etaient des adaptateurs une fois etendus, ce que l'outil rattrapait par un
re-filtrage apres extension. Ce rattrapage reste en place, mais il n'a plus grand-chose a
rattraper.

**Consequence pratique** : un `--dr` connu n'etait pas affecte (il court-circuite
l'extension). Tout resultat de novo SUR LECTURES anterieur au 2026-08-10 est a rejouer.

## Detecter une contamination (`qc`)

Un locus CRISPR est un marqueur taxonomique a haute resolution et quasi gratuit : le DR est
propre a un clade. Un DR d'un autre genre que l'attendu trahit un melange qu'un mapping
contre la reference de l'espece attendue ne verra **jamais**, puisque les lectures du
contaminant ne mappent pas et disparaissent en silence.

```bash
python3 $CB qc --genome contigs.fasta --attendu Mycobacterium --taille-attendue 4400000
```

Le controle croise deux signaux independants : le genre porteur du DR, lu dans
`data/dr_genres_ev4.tsv` (7 115 DR consensus d'evidence 4 de CRISPRCasdb, avec les genres
qui les portent), et le rapport entre la taille de l'assemblage et celle attendue. Verdict
`OK` / `SUSPECT` / `INDETERMINE`.

Valide sur un temoin negatif et un temoin positif :

| genome | verdict | detail |
|---|---|---|
| H37Rv | **OK** | DR -> *Mycobacterium* (exact, 981 loci), taille 1,0x |
| ERR266123, etiquete *M. canettii* | **SUSPECT** | DR dominant -> *Pseudomonas* (58 loci), deux autres DR *Pseudomonas*, taille **2,45x** |

ERR266123 est le cas fondateur : etiquete *M. canettii*, il porte le DR du systeme I-F de
*Pseudomonas aeruginosa*. Le catalogue se reconstruit avec le skill `crisprcasdb` si la
version figee ne suffit pas (elle s'arrete au 6 avril 2022, comme CRISPRCasdb).

## Garde-fous

**1. Un assemblage EFFACE souvent le locus, silencieusement — mais ne pas confondre avec
un DR different.** Mesure sur 21 assemblages SPAdes de *M. canettii* en cherchant le seul
DR du MTBC : 17 sans aucune copie. **Refait en detection de novo, le compte tombe a 5** :
douze de ces genomes portaient simplement un AUTRE systeme CRISPR. Pour ces cinq-la
l'effacement par l'assembleur reste l'explication — l'assembleur ne resout pas une region
de ~30 repetitions quasi identiques et l'ecarte, sans que rien dans les contigs le signale.
Un `status: "no_dr_found"` sur un assemblage ne veut donc **pas** dire « pas de CRISPR » :
passer aux reads. Et un « pas de DR connu » ne veut pas dire « pas de DR » : c'est le
garde-fou 4, et il a ete enfreint le jour meme ou il a ete ecrit.

**2. `dr_conservation` est le juge de paix.** Un vrai CRISPR est >= 90 % ; en dessous de
~70 % ce ne sont pas des repetitions. C'est ce chiffre qui a permis d'etablir que les
« archeo-CRISPR » de H37Rv (18-28 %) sont des artefacts de detection sur PE-PGRS. Voir le
skill `crisprcasdb`, garde-fou 1.

**3. Comparer un repertoire de spacers exige les DEUX sens.** Les spacers sont rendus dans
le sens du brin ou l'array a ete lu, qui n'est pas celui de la nomenclature publiee.

**4. Ne pas confondre « pas de DR du MTBC » et « pas de CRISPR ».** C'est precisement
l'erreur que cet outil corrige : chercher uniquement le DR du MTBC chez un *M. canettii*
de type I rend un faux negatif.

## Voisinage

`crisprcasdb` pour la verite de reference (CRISPRCasFinder sur 36 605 genomes, champ
`drconservation`) ; `spoligo_clock` (projet) pour l'usage du spoligotype comme horloge ;
`sitvitweb` et `mbovis` pour les spoligotypes de reference ; `SpacerEgalVirus` (projet)
pour l'origine des espaceurs.

**Source alternative, catalogue-based (pas de novo) : `crispr_report.json` du pipeline
TBannotator** (`mp:/data/current/run/scripts/crispr_report.py`, lu en source le 2026-08-17).
Reconstruction par mapping sur spacers/DR connus (noms `ESP*`/`DR*`) + comblement des trous
depuis `contigs.fasta` (uniquement pour les souches ASSEMBLEES, absent en mapping-only — meme
piege que `vntr_report.json`, voir `miru-vntr`). **Piege d'orientation silencieux** : quand les
brins mappes des elements CRISPR sont majoritairement mais pas unanimement inverses
(`count != reverse_count` ET `count != 0`), le script se contente d'un `print("WARNING: Mismatch
direction")` dans le log et NE CORRIGE RIEN — aucun flag d'ambiguite n'atterrit dans le JSON
final, un cas melange rend donc une sortie normale en apparence. Avant de faire confiance a
l'orientation d'un `crispr_report.json`, grep le `results/<SRA>/logs/crispr_report.log`
correspondant pour ce message plutot que de supposer l'orientation correcte par defaut.

## Dependances

Python >= 3.9, aucune bibliotheque externe (stdlib seule). `blastn` n'est pas requis.
