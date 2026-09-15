#!/usr/bin/env python3
"""
beast2_binary.py — Génère un XML BEAST2 CORRECT pour un alignement SNP binaire MTBC.

Problème récurrent diagnostiqué sur molecular_clock/data/beast2_run.xml :
    un alignement présence/absence {A,T} tourné sous modèle NUCLÉOTIDIQUE HKY.
    -> HKY attend 4 bases ; sur 2 lettres kappa s'effondre (~1e-13) et clockRate
       ne converge jamais (ESS ~6). Le modèle de substitution est le coupable.

Correctif : dataType="binary" + modèle binaire réversible à 2 états (GTR-2-state),
horloge stricte estimée, coalescent constant. Dates de prélèvement (tip dating)
conservées telles quelles. Option --ascertainment pour corriger le biais SNP
(l'alignement ne contient que des sites variables).

Usage :
    beast2_binary.py --in orig.xml --out corrige.xml [--chain 20000000] [--ascertainment]
    beast2_binary.py --phylip aln.phy --dates dates.tsv --out corrige.xml
"""
import re, os, argparse

def read_seqs_from_xml(path):
    xml = open(path).read()
    seqs = re.findall(r'<sequence taxon="([^"]+)"[^>]*>\s*([ACGTNacgtn?\-01]+)', xml)
    # dates depuis le trait
    m = re.search(r"traitname='date-forward'[^>]*value='([^']+)'", xml) or \
        re.search(r'traitname="date-forward"[^>]*value="([^"]+)"', xml)
    dates = {}
    if m:
        for tok in m.group(1).split(','):
            k, v = tok.split('=')
            dates[k.strip()] = float(v)
    return seqs, dates

def read_phylip(path):
    lines = [l.rstrip('\n') for l in open(path) if l.strip()]
    n, L = map(int, lines[0].split())
    seqs = []
    for ln in lines[1:1+n]:
        parts = ln.split()
        seqs.append((parts[0], parts[-1]))
    return seqs

def to_binary(seq):
    """A/0 -> 0 ; T/1 -> 1 ; garde 0/1 ; N/-/? -> ?"""
    out = []
    for c in seq:
        if c in 'A0': out.append('0')
        elif c in 'T1': out.append('1')
        else: out.append('?')
    return ''.join(out)

# Patron calqué sur les exemples LIVRÉS et VALIDÉS de BEAST 2.7
# (examples/testTipDates.xml + testHKY.xml). Le namespace en tête est COMPLET :
# un namespace incomplet fait échouer la résolution des specs courts avec le
# message trompeur "Could not find class ... BEASTInterface as service".
# Seule différence avec le patron nucléotidique : modèle binaire 2-états au lieu de HKY.
XML_TMPL = """<?xml version="1.0" encoding="UTF-8"?>
<beast version='2.0'
       namespace='beast.base.math:beast.base.evolution.alignment:beast.pkgmgmt:beast.base.core:beast.base.inference:beast.base.inference.distribution:beast.base.evolution.tree.coalescent:beast.base.inference.util:beast.base.evolution.operator:beast.base.inference.operator:beast.base.evolution.sitemodel:beast.base.evolution.substitutionmodel:beast.base.evolution.likelihood'>

<!-- {ntax} taxa, {nsite} sites binaires (présence/absence SNP) -->
<data id="alignment" dataType="binary">
{seqs}
</data>
{asc_block}
<!-- Modèle binaire 2-états (au lieu de HKY nucléotidique) -->
<input spec='GeneralSubstitutionModel' id='binaryModel'>
    <parameter name='rates' id='rates' value='1.0 1.0' dimension='2' estimate='true' lower='0.0'/>
    <frequencies id='freqs' spec='Frequencies'>
        <data idref='{aln_ref}'/>
    </frequencies>
</input>

<input spec='SiteModel' id="siteModel">
    <input name='substModel' idref='binaryModel'/>
</input>

<tree spec='beast.base.evolution.tree.ClusterTree' id='tree' clusterType='upgma'>
    <trait spec='beast.base.evolution.tree.TraitSet' traitname='date-forward' units='year' value='{dates}'>
        <taxa spec='TaxonSet' alignment='@alignment'/>
    </trait>
    <input name='taxa' idref='alignment'/>
</tree>

<distribution id="posterior" spec="CompoundDistribution">
    <distribution id="prior" spec="CompoundDistribution">
        <distribution id="coalescent" spec="Coalescent">
            <populationModel id="ConstantPopulation" spec="ConstantPopulation">
                <parameter id="popSize" name="popSize" value="100.0" estimate="true"/>
            </populationModel>
            <treeIntervals id="TreeIntervals" spec="beast.base.evolution.tree.TreeIntervals" tree="@tree"/>
        </distribution>
        <distribution id="popPrior" spec="distribution.Prior" x="@popSize">
            <distr id="OneOnPop" offset="0.0" spec="distribution.OneOnX"/>
        </distribution>
        <distribution id="clock.prior" spec="distribution.Prior" x="@clockRate">
            <distr id="clockLogNormal" spec="distribution.LogNormalDistributionModel" M="{clock_M}" S="{clock_S}"/>
        </distribution>
    </distribution>
    <distribution id="likelihood" spec="CompoundDistribution">
        <distribution spec='TreeLikelihood' id="treeLikelihood">
            <input name='data' idref="{aln_ref}"/>
            <input name='tree' idref="tree"/>
            <input name='siteModel' idref="siteModel"/>
            <branchRateModel id="StrictClockModel" spec="beast.base.evolution.branchratemodel.StrictClockModel">
                <parameter dimension="1" estimate="true" id="clockRate" name="clock.rate" value="{clock_init}" lower="0.0"/>
            </branchRateModel>
        </distribution>
    </distribution>
</distribution>

<run spec="MCMC" id="mcmc" chainLength="{chain}">
    <state>
        <input name='stateNode' idref="rates"/>
        <input name='stateNode' idref="clockRate"/>
        <input name='stateNode' idref="popSize"/>
        <input name='stateNode' idref="tree"/>
    </state>

    <distribution idref="posterior"/>

    <operator id='ratesScaler' spec='ScaleOperator' scaleFactor="0.5" weight="1" parameter="@rates"/>
    <operator id='clockRateScaler' spec='ScaleOperator' scaleFactor="0.5" weight="3" parameter="@clockRate"/>
    <operator id='popSizeScaler' spec='ScaleOperator' scaleFactor="0.5" weight="3" parameter="@popSize"/>
    <operator id='treeScaler' spec='ScaleOperator' scaleFactor="0.5" weight="3" tree='@tree'/>
    <operator spec='beast.base.evolution.operator.Uniform' weight="30" tree='@tree'/>
    <operator spec='SubtreeSlide' weight="15" gaussian="true" size="1.0" tree='@tree'/>
    <operator id='narrow' spec='Exchange' isNarrow='true' weight="15" tree='@tree'/>
    <operator id='wide' spec='Exchange' isNarrow='false' weight="3" tree='@tree'/>
    <operator spec='WilsonBalding' weight="3" tree='@tree'/>

    <logger logEvery="{logevery}" fileName="{prefix}.log">
        <log idref="posterior"/>
        <log idref="likelihood"/>
        <log idref="prior"/>
        <log idref='clockRate'/>
        <log idref='popSize'/>
        <log spec='beast.base.evolution.tree.TreeHeightLogger' tree='@tree'/>
    </logger>
    <logger logEvery="{logevery}" fileName="{prefix}.trees">
        <log idref="tree"/>
    </logger>
    <logger logEvery="{logevery}">
        <log idref="posterior"/>
        <log idref='clockRate'/>
        <log spec='beast.base.evolution.tree.TreeHeightLogger' tree='@tree'/>
    </logger>
</run>
</beast>
"""

def build(seqs, dates, chain, prefix, ascertainment, logevery, genome_len=None,
          clock_prior=1e-7, clock_prior_sd=1.25):
    import math
    seq_xml = "\n".join(
        f'<sequence taxon="{t}" value="{to_binary(s)}"/>' for t, s in seqs)
    date_str = ",".join(f"{t}={dates[t]}" for t, _ in seqs if t in dates)
    nsite = len(seqs[0][1]) if seqs else 0

    # Prior LogNormal sur clockRate : M = log(médiane), S = écart-type en
    # espace log. Le défaut historique S=2.0 est TROP large (IC95% couvre
    # ~3 ordres de grandeur) et laisse la chaîne errer jusqu'à 1e-9. Un prior
    # informatif centré sur la littérature MTBC (~1e-7) avec S~1.25 (IC95%
    # ~[9e-9, 1.2e-6]) ancre le paramètre que les données seules ne
    # contraignent pas — c'est le levier de convergence identifié par la
    # comparaison brut/propre (le nettoyage seul ne suffit pas).
    clock_M = round(math.log(clock_prior), 4)
    clock_S = clock_prior_sd
    clock_init = clock_prior

    # Correction d'ascertainment : réintègre les sites CONSTANTS exclus de
    # l'alignement SNP-only, via FilteredAlignment + constantSiteWeights.
    # Sans elle, les longueurs de branches (et donc le taux d'horloge) sont
    # gonflées. Pour données binaires : poids = "n0 n1" = nombre de sites
    # invariants à l'état 0 (allèle de référence) et à l'état 1.
    # Approximation standard MTBC : quasi tous les sites constants sont à
    # l'état 0 (référence), donc n1 = 0.
    if ascertainment:
        if genome_len is None:
            raise SystemExit("--ascertainment exige --genome-len (taille du "
                             "génome appelable, ex. 4411532 pour H37Rv)")
        n_const0 = genome_len - nsite
        if n_const0 < 0:
            raise SystemExit(f"--genome-len ({genome_len}) < nombre de SNP "
                             f"({nsite}) : incohérent")
        asc_block = (
            "\n<!-- Correction d'ascertainment : {c} sites constants (état 0) "
            "réintégrés -->\n"
            "<data id='alignmentFiltered' spec='FilteredAlignment' "
            "filter='-' data='@alignment' constantSiteWeights='{c} 0'/>\n"
        ).format(c=n_const0)
        aln_ref = "alignmentFiltered"
    else:
        asc_block = ""
        aln_ref = "alignment"

    return XML_TMPL.format(
        ntax=len(seqs), nsite=nsite,
        seqs=seq_xml, dates=date_str, chain=chain, prefix=prefix,
        logevery=logevery, asc_block=asc_block, aln_ref=aln_ref,
        clock_M=clock_M, clock_S=clock_S, clock_init=clock_init)

def main():
    ap = argparse.ArgumentParser(description="Génère un XML BEAST2 binaire correct (MTBC SNP)")
    ap.add_argument("--in", dest="inp", help="XML BEAST2 existant (récupère seqs+dates)")
    ap.add_argument("--phylip", help="alignement PHYLIP binaire (alt. à --in)")
    ap.add_argument("--dates", help="TSV taxon<TAB>date (requis avec --phylip)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--chain", type=int, default=20_000_000)
    ap.add_argument("--logevery", type=int, default=5000)
    ap.add_argument("--prefix", default=None)
    ap.add_argument("--ascertainment", action="store_true",
                    help="correction du biais d'ascertainment SNP (réintègre les sites constants)")
    ap.add_argument("--genome-len", type=int, default=None,
                    help="taille du génome appelable pour --ascertainment (ex. 4411532 = H37Rv NC_000962.3)")
    ap.add_argument("--clock-prior", type=float, default=1e-7, dest="clock_prior",
                    help="médiane du prior LogNormal sur clockRate (défaut 1e-7 = littérature MTBC)")
    ap.add_argument("--clock-prior-sd", type=float, default=1.25, dest="clock_prior_sd",
                    help="écart-type en log du prior clockRate (défaut 1.25 ; historique 2.0 = trop large)")
    args = ap.parse_args()

    if args.inp:
        seqs, dates = read_seqs_from_xml(args.inp)
    else:
        seqs = read_phylip(args.phylip)
        dates = {}
        if args.dates:
            for ln in open(args.dates):
                if ln.strip():
                    k, v = ln.split()[:2]; dates[k] = float(v)
    prefix = args.prefix or os.path.splitext(os.path.basename(args.out))[0]
    xml = build(seqs, dates, args.chain, prefix, args.ascertainment, args.logevery,
                genome_len=args.genome_len, clock_prior=args.clock_prior,
                clock_prior_sd=args.clock_prior_sd)
    open(args.out, "w").write(xml)
    print(f"OK: {args.out}  ({len(seqs)} taxa, {len(seqs[0][1])} sites, chain={args.chain})")
    missing = [t for t, _ in seqs if t not in dates]
    if missing:
        print(f"  ⚠ {len(missing)} taxa sans date: {missing[:5]}")

if __name__ == "__main__":
    main()
