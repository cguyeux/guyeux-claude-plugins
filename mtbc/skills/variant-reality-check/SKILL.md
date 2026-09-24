---
name: variant-reality-check
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST), peer-reviewed MTBC
  phylogenomics: decide whether a called variant is REAL and which allele is
  ANCESTRAL, before it becomes a claim. Two gestures: (1) sequence context of
  a called indel — placement ambiguity after normalisation (settles polymerase
  slippage, not homopolymer length), tandem repeats, local GC, k-mer
  uniqueness against cross-mapping, each with a null model from sampled
  positions measured the same way; (2) polarisation on CLOSED COMPLETE
  ASSEMBLIES instead of variant calls, locating the site by unique flanks and
  measuring the gap between them, answering coverage, mapping and calling
  artefacts at once. Also translates a CDS to the REAL stop, not the annotated
  boundary.

  Use when: an indel/frameshift is suspected a calling artefact, a variant is
  about to be called a synapomorphy, a `disrupt_frac` or snpEff HIGH label is
  about to be written as pseudogenisation, an outgroup appears to LACK a
  variant, or a reference annotation looks unrepresentative.

  Scope: developed on the MTBC, applies to any clonal bacterial pathogen
  (Yersinia, Leptospira...) — the reference genome is already an explicit
  argument (`--genome`), so only the closed assemblies of the genus are needed.
argument-hint: "--spdi <pos:ref:alt> --genome <ref.fasta> [--cds debut-fin:brin]"
user-invocable: true
disable-model-invocation: false
allowed-tools: Bash, Read, Write, Grep, Glob
---

# variant-reality-check

Un variant appelé n'est pas un fait. Ce skill porte les trois mesures qui
décident, dans l'ordre où elles coûtent le moins cher.

## 1. Polariser sur des génomes complets fermés (à faire EN PREMIER)

```bash
python3 scripts/polarize_on_assemblies.py \
  --spdi 4383143:C:CCGGGG \
  --genome .../NC_000962.3.fasta \
  --cache data/genomes_complets --out-tsv polarisation.tsv
```

Un assemblage circulaire clos n'a ni défaut de couverture, ni ambiguïté de
mapping, ni seuil d'appel. Il répond donc mieux qu'un pileup à la question que
le pileup posait, et en quelques minutes. Le script dérive automatiquement des
flancs **uniques** de part et d'autre du site, les cherche sur les deux brins
de chaque assemblage du panel, et rend **l'écart entre les deux flancs**.

Trois règles portées par le code, chacune apprise d'une erreur réelle.

- **Localiser par les flancs, jamais par les coordonnées.** Elles diffèrent d'un
  assemblage à l'autre, parfois de plusieurs kb.
- **Mesurer l'écart, jamais l'identité de ce qu'il y a entre les flancs.** Tester
  la présence de la chaîne `CGGGG` classait *M. canettii*, qui porte `CGGGA`,
  comme dépourvu des cinq bases, et inversait la polarité de tout un locus.
- **Ne jamais déduire une lignée du nom d'une souche.** KZN 1435 a été étiquetée
  L2 dans le panel parce qu'elle est XDR et sud-africaine ; elle est
  F15/LAM4/KZN, donc L4. L'erreur a fabriqué une fausse anomalie avant d'être
  repérée. Les étiquettes du panel par défaut sont indicatives.

Le panel par défaut couvre la référence, trois autres L4, L6, deux *M. bovis*
et *M. canettii*. Il **ne couvre pas** L1, L2, L3, L5, L7, L8, L9, L10 : il ne
permet donc pas d'écrire qu'un allèle est présent « dans toutes les lignées
humaines ». Le surcharger avec `--panel` (TSV accession/étiquette/groupe).

Un repli blastn se déclenche quand la divergence casse la correspondance exacte
des flancs. Il peut échouer sur un gène très divergent chez l'outgroup : c'est
un résultat honnête, pas un bug, et il appelle un alignement protéique.

## 2. Contexte séquence d'un indel

```bash
python3 scripts/sequence_context.py \
  --spdi 4383143:C:CCGGGG --cds 4383008-4383640:- \
  --genome .../NC_000962.3.fasta
```

Ce qu'il faut retenir avant de lire la sortie.

**La mesure qui tranche le slippage est l'ambiguïté de placement**, pas la
longueur de l'homopolymère : c'est le nombre de positions équivalentes auxquelles
l'indel peut être écrit sans changer la séquence produite. Trois à dix dans un
microsatellite ; **1 signifie qu'aucun glissement n'est possible** et que le
mécanisme est exclu, quelle que soit la composition locale.

**Le %GC se lit contre le fond du génome.** H37Rv est à 65,6 % : un contexte à
63 % est *sous* la médiane, au 35e centile. Le qualifier de « riche en G+C » est
une erreur de référentiel. De même, H37Rv n'a quasiment pas d'homopolymères
(médiane 1, p99 = 4), si bien qu'un C×3 y ressort au 96e centile sans être pour
autant un contexte propice.

**Le modèle nul mesure le même objet que le site** : des positions tirées au
hasard, auxquelles on applique la fonction du site. Comparer « le plus long
tandem au site » à « le plus long tandem dans une fenêtre de 100 pb » écrase le
signal.

**L'unicité des k-mers** écarte le second mécanisme d'artefact, le cross-mapping
depuis un paralogue, que le contexte répété ne couvre pas.

## 3. Traduire jusqu'au stop RÉEL

`sequence_context.py --cds` traduit au-delà de la borne annotée et prend pour
contrôle que l'allèle de référence, lui, retombe exactement sur le stop de
l'annotation.

**Ne jamais traduire une CDS jusqu'à sa borne et appeler le résultat « longueur
jusqu'au premier stop ».** Après un frameshift ou un stop_lost, le stop réel est
presque toujours hors de la CDS de référence, et Biopython n'émet qu'un warning
sur le codon partiel. Conséquence mesurée : un frameshift terminal que la couche
`conservation` de l'atlas compte comme lésion disruptive chez 97,7 % de 145 209
souches produit en réalité un ORF complet de 214 aa contre 210, avec 165 résidus
identiques en tête. **`disrupt_frac` hérite de l'étiquette HIGH mécanique de
snpEff, qui ne vérifie pas où le stop atterrit.** Avant d'écrire qu'un gène est
pseudogénisé, traduire jusqu'au stop réel.

## Convention de coordonnées

Les SPDI de TBannotator sont **0-based** (norme NCBI) ; les coordonnées de gènes
du GFF sont **1-based**. Les deux scripts vérifient la convention sur l'allèle de
référence et s'arrêtent si elle ne colle pas, plutôt que de la supposer.

## Provenance

Forgé dans `mtbc/Rv3896c-Rv3898c` (piste P2, 2026-09-10), où il a fermé trois
pistes d'un coup et retourné la polarité du variant fondateur du projet.
Généralise `homopolymer_context` de
`mtbc/clos_soumis/Rv0810c/analyses/phase6_p4_3_disruption.py`. Quatre projets du dépôt
(`gene_decay_census`, `lineage_navigator`, `Rv0810c`, `Rv2699c`) avaient eu
besoin de ces mesures sans les outiller.
