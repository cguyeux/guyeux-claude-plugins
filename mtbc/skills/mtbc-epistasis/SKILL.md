---
name: mtbc-epistasis
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST), peer-reviewed MTBC
  phylogenomics: detecte l'evolution COMPENSATOIRE et l'epistasie de resistance
  dans le MTBC, en POLARISANT le signal par lignee pour ecarter l'homoplasie.
  Teste si une mutation de resistance couteuse (rpoB/RRDR) co-occurre avec une
  mutation compensatoire candidate (rpoC, rpoA ; ahpC pour katG) plus que le
  hasard, non globalement (confondu avec les marqueurs de lignee) mais entre
  isolats resistants/non-resistants de la MEME lignee, agrege par
  Mantel-Haenszel.

  Use when: clones resistants deja compenses/transmissibles ? tester
  "resistance transmise clonalement" ; distinguer compensation vraie et
  marqueur de sous-lignee. Portee : developpe sur le MTBC, applicable a toute
  bacterie clonale (Yersinia, Leptospira...) — lignee + Mantel-Haenszel =
  methode generique, rpoB/rpoC/katG-ahpC = PARAMETRES. Hors MTBC : fournir
  paires de genes et base de souches (--bdd/--manifest).
argument-hint: "[--bdd DIR | --manifest TSV] [--lineage-major] [--out FICHIER]"
allowed-tools: Bash, Read, Write, Grep, Glob
user-invocable: true
---

# /mtbc-epistasis -- Compensation et epistasie de la resistance, polarisees par lignee

Une mutation de resistance a un **cout de fitness** (ex. rpoB-S450L ralentit la
transcription). Ce cout est souvent **compense** par une seconde mutation (rpoC,
rpoA) qui restaure la fitness sans perdre la resistance. Un clone resistant
**compense** est fit, donc transmissible ; un clone non compense l'est moins.
Savoir si les isolats resistants d'une cohorte sont compenses repond directement
a "quels clones R vont se propager".

**Le piege que ce skill est fait pour eviter.** Compter naivement la co-occurrence
"mutation R + mutation candidate" a travers tous les genomes **confond la
compensation avec la structure de population** : une mutation candidate peut
n'etre qu'un **marqueur fixe d'une sous-lignee**, present chez tous ses membres,
resistants ou non. La co-occurrence brute est alors un artefact d'homoplasie, pas
une compensation. C'est exactement l'erreur demontee dans le projet Oman (P10.7 :
une "resistance candidate locale" n'etait que le fond L1 du panel).

**La parade : polarisation intra-lignee.** On ne compare jamais globalement. Dans
**chaque lignee**, on teste si la mutation candidate est enrichie chez les
**resistants** par rapport aux **non-resistants** de cette meme lignee (table
2x2), puis on **agrege par Mantel-Haenszel** (odds ratio ajuste sur la lignee,
test de Cochran-Mantel-Haenszel). Une vraie compensatoire est enrichie chez les R
intra-lignee (OR_MH > 1, p significatif). Un simple marqueur de lignee donne un
stratum non informatif (present partout dans la lignee) ou OR_MH ~ 1 : il ne
produit PAS de faux signal.

## Prealable

1. Lire `~/.claude/knowledge/tuberculosis.md` (biais de reference H37Rv, piege
   homoplasie, conventions SPDI).
2. Consulter `mtbc-lineages` pour la hierarchie et l'etiquetage des lignees si un
   doute subsiste sur les labels ; degrader gracieusement s'il est indisponible.
3. Verifier que les `report.json` cibles existent (couche TBannotator v2). Structure
   exploitee : `d["snp"][i]["spdi"]` (= `NC_000962.3:<pos0>:<ref>:<alt>`, 0-based ;
   position 1-based = pos0+1) et la liste imbriquee `d["snp"][i]["annotations"][j]`
   avec `gene_name`, `gene_locus_tag` (prefixe `gene-`), `annotation` (effets),
   `impact`, `protein_position`, `hgvs_p`. Le parser matche par `gene_name` d'abord.

## Ce que fait le script

`scripts/epistasis.py` (Python >= 3.10, scipy pour la loi du chi2 ; Mantel-Haenszel
code a la main, aucune dependance a statsmodels) :

1. **Charge** les souches et leur lignee, soit depuis une arborescence
   `bdd/actuelle` (`--bdd DIR` ou chaque `DIR/<lignee>/<SRA>/NC_000962.3/report.json`
   donne la lignee par le nom du repertoire), soit depuis un `--manifest TSV`
   (colonnes `strain <tab> lineage <tab> report_path`).
2. **Classe** chaque souche :
   - **Statut R** (proxy robuste, catalogue-independant) : porte-t-elle une
     mutation non-synonyme dans la region a cout de fitness connu ? rpoB RRDR
     (codons 426-452) pour RIF ; katG 315 pour INH. (Choix delibere : ce sont les
     mutations dont le cout de fitness et la compensation sont documentes.)
   - **Statut compensatoire** : porte-t-elle une mutation non-synonyme dans le
     gene candidat (rpoC = Rv0668, rpoA = Rv3457c) ? Pour ahpC (Rv2428), inclut
     aussi les variants de **promoteur** (upstream), car c'est la leur signature.
3. **Construit** pour chaque paire (R-gene -> compensatoire) une table 2x2 par
   lignee, calcule l'OR par stratum, l'**OR de Mantel-Haenszel** et le **p de
   Cochran-Mantel-Haenszel** (correction de continuite). Un stratum sans R, sans
   non-R, ou ou la candidate est fixee (present partout) est **non informatif** et
   exclu -- c'est la garde anti-homoplasie.
4. **Ecrit** un TSV (2x2 par lignee) et un resume console avec un **verdict** par
   paire.

### Paires livrees par defaut

| Resistance (cout) | Compensatoire candidate | Evidence litterature |
|-------------------|-------------------------|----------------------|
| rpoB RRDR (RIF)   | rpoC (Rv0668)           | forte -- Comas 2012 Nat Genet, de Vos 2013 AAC, Song 2014 |
| rpoB RRDR (RIF)   | rpoA (Rv3457c)          | forte -- Comas 2012 |
| katG S315 (INH)   | ahpC (Rv2428, +promoteur) | faible -- **co-marqueur**, pas compensation de fitness prouvee (Sherman 1996) |

Les coordonnees H37Rv et les paires sont en tete du script, **modifiables** pour
ajouter une paire (ex. gyrA -> gene candidat) ou corriger une borne.

## Usage

```bash
SK=${CLAUDE_PLUGIN_ROOT}/skills/mtbc-epistasis/scripts/epistasis.py

# Sur une arborescence bdd/actuelle (lignee = repertoire parent)
python3 $SK --bdd ../../bdd/actuelle --lineage-major --out epistasis_result.tsv

# Sur un sous-ensemble via manifeste (strain<tab>lineage<tab>report_path)
python3 $SK --manifest strains.tsv --out epistasis_result.tsv
```

- `--lineage-major` regroupe les sous-lignees par lignee majeure (`L1.2.3 -> L1`) :
  utile quand les effectifs par sous-lignee sont faibles ; sans l'option, la
  stratification est plus fine (plus conservatrice, plus exigeante en N).
- `--min-per-stratum N` (defaut 4) : effectif R minimal pour qu'une lignee compte.
- `--describe` : **lecture PAR ISOLAT resistant**, avec le fond de sous-lignee
  soustrait. Sort, pour chaque isolat R, ses mutations candidates `comp_total` et
  surtout `comp_specific` (celles qui lui sont PROPRES, absentes de tous les
  non-R de sa sous-lignee), plus un verdict et un caveat automatique quand les
  temoins sont trop peu nombreux. Ecrit `<out>_describe.tsv`.

> [!WARNING]
> **Utiliser `--describe` des qu'on veut dire « CET isolat est compense ».** Ne
> jamais lire les mutations d'un isolat a la main pour l'affirmer : une mutation
> candidate presente aussi chez les non-resistants de la meme sous-lignee est un
> **marqueur de clade**, pas une compensation. Cas vecu (2026-07-31, projet Oman) :
> rpoC Ala172Val et Pro601Leu, portees par 37/37 genomes L1 resistants comme
> sensibles, ont ete prises pour des compensations dans une lecture descriptive
> hors outil ; le faux positif s'est propage dans quatre documents avant
> correction. Le test agrege (Mantel-Haenszel) evitait deja ce piege, mais **un
> garde-fou ne protege que ce qui passe PAR l'outil** : d'ou ce mode. Apres
> soustraction du fond, le resultat correct etait 1 cas sur 2 (le MDR portait
> rpoC Arg480His propre ; le mono-resistant n'avait rien).

## Lecture du verdict

- **COMPENSATION soutenue (intra-lignee)** : OR_MH > 1,5 et p_CMH < 0,05 sur des
  strata informatifs -> la compensation resiste au controle de la structure de
  population. C'est le seul verdict qui autorise a parler de compensation.
- **confondu / pas de signal net** : OR_MH ~ 1 -> la co-occurrence brute etait
  vraisemblablement un marqueur de lignee ; ne PAS conclure a la compensation.
- **tendance, non significative** / **N insuffisant** : signal possible mais
  sous-puissant -> refaire sur une cohorte plus large (typiquement les 407 SQU
  plutot que les 66 publics).

**Regle d'or** : le verdict porte sur l'ASSOCIATION intra-lignee, pas sur la
causalite ni l'ordre temporel. Pour etablir que la compensatoire est apparue
APRES la resistance (vraie compensation, non simple co-heritage), l'etape suivante
est phylogenetique (reconstruction d'etats ancestraux : la R doit preceder la
compensatoire sur l'arbre) -> `ancestral-reconstruction` / `pastml`. Ce skill est
le crible statistique rapide qui dit s'il vaut la peine d'y aller.

## Limites et pieges

- **Proxy de resistance** : le statut R est defini par la region (RRDR, katG 315),
  pas par un phenotype ni le catalogue OMS complet. Pour un profil R exact, croiser
  avec `resistance-catalogue` / `resistance-profiler`. Le proxy est volontairement
  restreint aux mutations a compensation documentee.
- **Petits N** : la stratification par lignee coute de la puissance. Sur < ~200
  genomes ou peu de R, attendre des verdicts "N insuffisant" ; c'est honnete, pas
  un echec.
- **Compensation vs co-marqueur** : ahpC est fourni mais signale comme
  co-marqueur ; ne pas le presenter comme une compensation de fitness prouvee.
- **Biais de reference H37Rv** : la detection SPDI passe par TBannotator (mapping
  sur H37Rv) ; pour les lignees eloignees de L4, garder ce biais en tete (golden
  law MTBC).

## Integration avec l'ecosysteme

- **`resistance-catalogue` / `resistance-profiler`** : pour un statut R fonde sur
  le catalogue OMS plutot que le proxy RRDR/315.
- **`ancestral-reconstruction` / `pastml`** : etape de confirmation
  phylogenetique (ordre R -> compensatoire sur l'arbre).
- **`thd` / `bayesian-skyline`** : une fois la compensation etablie, tester si les
  clones compenses ont un succes epidemique superieur (lien fitness -> transmission).
- **`convergent-evolution`** : complementaire (convergence INTER-lignees d'un
  gene) ; ce skill teste au contraire l'association INTRA-lignee resistance x
  compensatoire.
- **`/cahier-de-labo`**, **`/pistes`**, **`/claim-check`** : tracer le resultat,
  faire avancer la piste (Oman P12.1), verifier tout claim de compensation.

## Sortie attendue

A la fin, afficher : le nombre de souches et de lignees chargees, le tableau
resume (paire, drug, lignees informatives, n_R, OR_MH, p_CMH, verdict), le chemin
du TSV detaille, et la prochaine etape suggeree (elargir la cohorte, ou passer a
la confirmation phylogenetique si un verdict "COMPENSATION soutenue" ressort).
