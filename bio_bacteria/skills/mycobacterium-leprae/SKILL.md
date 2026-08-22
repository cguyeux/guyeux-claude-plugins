---
name: mycobacterium-leprae
description: >-
  Academic literature reference. Curated bibliography of peer-reviewed paleogenomic research
  on Mycobacterium leprae, the richest published ancient-DNA corpus for any Mycobacterium:
  49 ancient genomes across 13 countries spanning 2200 years, against 16 for ancient MTBC.
  Indexes the canonical papers (Schuenemann 2013 and 2018, Krause-Kyora 2018, Kerudin 2019,
  Fotakis 2020, Neukamm 2020, Pfrengle 2021, Bonczarowska 2022, Urban 2024), the documented
  non-human reservoirs (nine-banded armadillo, medieval English red squirrels), the European
  origin of New World samples, and the five canonical published lineages. Use when writing a
  comparative section on M. leprae versus M. tuberculosis paleogenomic trajectories,
  preparing seminar slides on ancient Mycobacterium genomics, contextualising zoonotic
  reservoirs in an article, or transposing published paleogenomic methodology to MTBC.
---

# *Mycobacterium leprae* : The Richest Ancient *Mycobacterium* Corpus

> [!TIP]
> **Leproma, la base génomique historique de l'espèce.** `genolist.pasteur.fr/Leproma` (Institut
> Pasteur, plateforme GenoList) donne l'annotation de référence de *M. leprae* TN, gène par gène, avec
> les pseudogènes explicitement marqués, ce qui est central chez une espèce dont le génome est en
> réduction massive. Base ancienne et figée : la croiser avec une annotation récente plutôt que s'y
> fier seule. À noter que la chaîne TBannotator a déjà tourné sur *M. leprae* : **710 souches** sous
> `mp:/data/current/run/references_results/NC_002677.1/`, profondeurs très hétérogènes (0,2× à 57×),
> à trier avant tout calcul (voir `panisa` et `remote-compute`).


## Overview

*Mycobacterium leprae* is the causative agent of leprosy (Hansen's
disease), an obligate intracellular pathogen with one of the most
reduced genomes in the genus *Mycobacterium* (~1,130 pseudogenes,
genome size ~3.3 Mb vs 4.4 Mb for *M. tuberculosis*). Paradoxically,
it has yielded the **largest and best-studied ancient-DNA corpus of
any *Mycobacterium***, thanks to characteristic skeletal lesions that
make archaeological case identification straightforward.

Within your constellation, *M. leprae* is the **closest comparative
anchor** to MTBC:

- **Same genus** → directly comparable methodologies and results
- **49 ancient genomes** published across **13 countries** spanning
  **100–2 200 BP** (verified from `spaam-ancient-metagenome-dir`),
  **3× the corpus of ancient MTBC** (16 genomes)
- **Distinct coevolution story** (different host range, different
  dispersal patterns) that highlights MTBC's specifics by contrast

## Key papers

| Paper | Finding |
|---|---|
| **Schuenemann V.J. et al. 2013 *Science*** 341(6142): 179–183. DOI: `10.1126/science.1238286`, *Genome-wide comparison of medieval and modern M. leprae* | First ancient *M. leprae* genomes from 5 medieval skeletons (UK, Sweden, Denmark). Remarkable conservation over 1000 years. Suggests European origin of New World leprosy |
| **Mendum T.A. et al. 2014 *BMC Genomics*** 15: 270. DOI: `10.1186/1471-2164-15-270`, *M. leprae genomes from a British medieval leprosy hospital: towards understanding an ancient epidemic* | Genomes from Winchester leprosarium (~1000 BP) |
| **Krause-Kyora B. et al. 2018 *Nature Communications*** 9: 1569. DOI: `10.1038/s41467-018-03857-x`, *Ancient DNA study reveals HLA susceptibility locus for leprosy in medieval Europeans* | **10 complete M. leprae genomes from a Danish medieval leprosarium**, the largest single-site corpus. Documents **HLA DRB1*15:01** as a susceptibility locus across both medieval and modern Europeans |
| **Schuenemann V.J. et al. 2018 *PLOS Pathogens*** 14(5): e1006997. DOI: `10.1371/journal.ppat.1006997`, *Ancient genomes reveal a high diversity of M. leprae in medieval Europe* | 10 new medieval genomes including early English medieval cases. 4 of 5 known *M. leprae* lineages already present in early medieval Europe |
| **Kerudin A. et al. 2019 *Journal of Archaeological Science***, *Ancient Mycobacterium leprae genomes from the mediaeval sites of Chichester and Raunds in England* | 3 medieval English genomes (2 × subtype 3I + 1 × subtype 3K). **Subtype 3K is rare in Britain but common in continental Europe**, interpretation: brought to Britain by Crusader-era travellers to the Holy Land |
| **Fotakis A.K. et al. 2020 *Phil. Trans. R. Soc. B*** 375(1812): 20190584. DOI: `10.1098/rstb.2019.0584`, *Multi-omic detection of M. leprae in archaeological human dental calculus* | **First ancient M. leprae genome from Norway** (SK92, 16th century Trondheim), 6.6× coverage, **recovered from dental calculus** (unusual substrate). Branch 3I. Combined proteomic + DNA detection |
| **Neukamm J. et al. 2020 *BMC Biology*** 18: 108. DOI: `10.1186/s12915-020-00839-8`, *2000-year-old pathogen genomes reconstructed from metagenomic analysis of Egyptian mummified individuals* | **The oldest M. leprae genome in the catalogue: ~2 200 BP from Abusir, Ptolemaic Egypt.** Doubles the temporal depth of the ancient *M. leprae* record and adds North Africa to the geographic range |
| **Pfrengle S. et al. 2021 *BMC Biology*** 19: 220. DOI: `10.1186/s12915-021-01120-2`, *M. leprae diversity and population dynamics in medieval Europe from novel ancient genomes* | **19 additional medieval European genomes** (the single largest project in the catalogue by count) from Belarus, Norway, Portugal, Russia, Spain, UK. Refines intra-continental population dynamics |
| **Bonczarowska J.H. et al. 2022 *Genome Biology*** 23: 250. DOI: `10.1186/s13059-022-02806-8`, *Pathogen genomics study of an early medieval community in Germany reveals extensive co-infections* | Merovingian community Lauchheim Mittelhofen (5th–8th c. CE) with **co-infections** (HBV + parvovirus B19 + variola + *M. leprae*). **Explicit link to the Late Antique Little Ice Age (LALIA)** as hypothesised stressor, direct cross-reference to the `paleoclimate` skill (Büntgen 2016) |
| **Urban C. et al. 2024 *Current Biology*** 34(10): 2221–2230. DOI: `10.1016/j.cub.2024.04.020`, *Ancient M. leprae genome reveals medieval English red squirrels as animal leprosy host* | **Medieval red squirrels carried M. leprae** strains phylogenetically nested within contemporary human strains, zoonotic reservoir in medieval Europe |
| **Truman R.W. et al. 2011 *NEJM*** 364: 1626–1633. DOI: `10.1056/NEJMoa1010536`, *Probable zoonotic leprosy in the southern United States* | **Nine-banded armadillos carry M. leprae** in the southern US, the modern zoonotic reservoir in the New World |
| **Avanzi C. et al. 2016 *Science*** 354(6313): 744–747. DOI: `10.1126/science.aah3783`, *Red squirrels in the British Isles are infected with leprosy bacilli* | Modern British red squirrels (*Sciurus vulgaris*) harbour both *M. leprae* and *M. lepromatosis* |

## The five canonical *M. leprae* lineages

Phylogenetic analysis has established **5 major lineages** named
numerically (Monot et al. 2005 *Science*, refined subsequently):

| Lineage | Modern distribution | Notes |
|---|---|---|
| **1** | Asia, Pacific | Early-branching |
| **2** | Central Asia, East Africa, Ethiopia | |
| **3** | Europe, North Africa, Middle East, Americas | **Dominant in medieval Europe**; ancestor of New World strains |
| **4** | West Africa, Brazil (colonial) | Brought to the Americas via trans-Atlantic slave trade |
| **5** | Asia | Minor modern branch |

Plus **M. lepromatosis**, a **distinct species** discovered in 2008
(Han et al. 2008) that also causes leprosy (diffuse lepromatous
leprosy); not yet documented in the archaeological record.

## Why it matters for your MTBC seminar

*M. leprae* gives you **three complementary narrative hooks**:

1. **Comparative richness of ancient corpora.** The ancient *M. leprae*
   record is **3× the size of ancient MTBC**, with 2 200 years of
   temporal depth (vs ~1 000 years for MTBC). This lets you say:
   *"The ancient DNA record for ***Mycobacterium*** as a whole is
   dominated by *M. leprae*; ancient MTBC is the frontier."*
2. **Documented zoonotic reservoirs, a complete story.** Leprosy
   has **two confirmed non-human reservoirs** (nine-banded
   armadillos in the Americas; European/British red squirrels in
   medieval and modern times), with **ancient DNA directly supporting
   the red squirrel story** (Urban 2024). This is the **exact kind of
   evidence you currently lack for *M. bovis* / *M. caprae***, a
   direct zoonotic reservoir story with ancient DNA. Citing the
   leprosy precedent is a way to frame the MTBC zoonotic hypothesis
   as testable rather than speculative.
3. **Colonial dispersal signature.** Lineage 4 in the Americas is the
   direct pathogen-side signature of the trans-Atlantic slave trade
   (chain with `slavevoyages`). Lineage 3 in the Americas reflects
   European colonial migration. These are **quantitative signatures
   of historical events**, exactly the kind of evidence Paul Verdu
   works with for human populations.

## Coverage in `spaam-ancient-metagenome-dir` (verified earlier)

From our session-verified snapshot:

- **49 individuals** across **10 projects**
- **13 countries**: Belarus, Czechia, Denmark, Egypt, Germany, Hungary,
  Italy, Norway, Portugal, Russia, Spain, Sweden, United Kingdom
- **Temporal span**: **100–2 200 BP**
- Verified project breakdown (from the session-fetched snapshot):
  `Pfrengle2021` (19, the largest), `KrauseKyora2018b` (10),
  `Schuenemann2013` (5), `Schuenemann2018` (4), `Urban2024` (4, incl.
  red squirrels), `Kerudin2019` (3), `Mendum2014` (1),
  `Fotakis2020` (1), `Neukamm2020` (1, Egypt Ptolemaic, **the
  earliest**, 2 200 BP), `Bonczarowska2022` (1, Germany Merovingian)

Compare with MTBC in the same catalogue:

| Metric | MTBC (tb + pinnipedii) | *M. leprae* |
|---|---|---|
| Individuals | 16 | **49** (3.1×) |
| Projects | 5 | 10 |
| Countries | 4 | **13** |
| Temporal span | 100–1 000 BP | **100–2 200 BP** (2.2×) |

## Host range : the narrow-host-range story

Unlike MTBC (which has a broad range of animal ecotypes), *M. leprae*
has **only three confirmed natural hosts**:

1. **Humans**, the canonical host for >3 000 years of recorded
   history
2. ***Dasypus novemcinctus***, the nine-banded armadillo in the
   southern United States and Central/South America (Truman 2011).
   Thought to have been infected by early European colonists; now a
   zoonotic source for modern US leprosy cases
3. ***Sciurus vulgaris***, the red squirrel, documented in modern
   British populations (Avanzi 2016) and in **medieval English
   specimens** (Urban 2024, ancient DNA)

Plus isolated reports of natural infection in chimpanzees in West
Africa (Hockings 2020 *Frontiers in Microbiol*).

This narrow host range stands in sharp contrast to MTBC's broad
host-jump record, and is a useful comparative point for discussing
host specificity and the evolutionary trade-offs between
transmissibility and reservoir breadth.

## Data resources

| Resource | Access | Content |
|---|---|---|
| **`spaam-ancient-metagenome-dir`** | This constellation | 49 ancient *M. leprae* genomes indexed, **start here** |
| **NCBI BioProject** | ENA / SRA | Raw reads per study (Schuenemann 2013: PRJEB12055; Schuenemann 2018: PRJEB21826; Krause-Kyora 2018: see NC `s41467-018-03857-x` supplementary; Pfrengle 2021: PRJEB43182; Neukamm 2020: see BMC Biology `s12915-020-00839-8`; Bonczarowska 2022: see *Genome Biology* `s13059-022-02806-8` supplementary; Urban 2024: check current accession) |
| **EnteroBase** | `enterobase.warwick.ac.uk` | *Helicobacter* is in EnteroBase but *Mycobacterium* is not; use TBannotator or TB-Profiler-style pipelines for *M. leprae* |
| **LepDB / LepMA** | Various | Classical MLST / VNTR databases for modern surveillance (check current status) |
| **WHO Global Leprosy Programme** | WHO | Modern epidemiological data |

## Workflows

### Workflow 1 : Build the comparative MTBC vs *M. leprae* ancient-DNA table

Goal: a single slide-ready table for the seminar showing the relative
state of ancient DNA for both pathogens.

```python
import pandas as pd
df = pd.read_csv("amdir_singlegenome_samples.tsv", sep="\t", low_memory=False)

def summarize(species_list):
    sub = df[df.singlegenome_species.isin(species_list)]
    return {
        "N individuals": len(sub),
        "N projects": sub.project_name.nunique(),
        "N countries": sub.geo_loc_name.nunique(),
        "Age range (BP)": f"{int(sub.sample_age.min())}–{int(sub.sample_age.max())}",
    }

print("MTBC sensu lato:", summarize([
    "Mycobacterium tuberculosis", "Mycobacterium pinnipedii"]))
print("M. leprae      :", summarize(["Mycobacterium leprae"]))
```

### Workflow 2 : European lineage dispersal narrative

Goal: trace the dispersal of lineage 3 from medieval Europe to the
Americas.

1. Extract European medieval *M. leprae* samples from
   `spaam-ancient-metagenome-dir`.
2. Assign lineages using published SNP markers (Monot 2005, Schuenemann 2018).
3. Cross-reference with the trans-Atlantic dispersal timeline from
   `slavevoyages`.
4. Narrate: *"Lineage 3 *M. leprae* reached the Americas with early
   colonists (~1500–1700), while lineage 4 arrived via the
   trans-Atlantic slave trade from West Africa."*

### Workflow 3 : Red squirrel zoonosis reconstruction

Goal: use Urban 2024 as a case study for zoonosis detection via ancient
DNA.

1. Download the Urban 2024 medieval red squirrel *M. leprae* genome
   from the corresponding ENA accession.
2. Reconstruct a tree with contemporary human *M. leprae* from the
   same region (Winchester, England; ~11th century).
3. The red squirrel strain should **nest within** the human strain
   diversity, supporting reverse zoonosis or shared environmental
   source.
4. Discussion: *"This is the template for testing hypothetical
   animal-host reservoirs of ancient MTBC, we just need the samples."*

### Workflow 4 : Compare ancient corpora visually with `iqtree-lsd2`

Goal: a dual-panel figure showing ancient MTBC tree vs ancient
*M. leprae* tree side-by-side.

1. Build two IQ-TREE phylogenies (`iqtree-lsd2` workflow), one for
   MTBC ancients + moderns, one for *M. leprae* ancients + moderns.
2. Use the same visual style (Auspice, FigTree, or baltic).
3. Layout side-by-side with matched time axes.
4. Annotate key nodes: Out of Africa (if detectable), medieval
   dispersal, colonial dispersal, modern global diversification.

## Caveats

- **Cultivation-independent pathogen.** *M. leprae* cannot be cultured
  on standard media. Research has historically used mouse footpad
  and armadillo passage. This affects how modern reference strains
  are maintained and genome-sequenced.
- **Extreme genome decay.** *M. leprae* has ~1 130 pseudogenes, more
  than half its coding potential is inactivated. Functional
  annotation is tricky; use the Cole et al. 2001 *Nature* reference
  genome TN as the baseline.
- **Slow molecular clock.** *M. leprae* evolves very slowly
  (~6e-10 subs/site/year, ~10× slower than MTBC), which makes
  tip-dating with 2 200-year-spanning ancient tips statistically
  robust, but also means short-term dispersal signals are weak.
- **Zoonotic reservoir evidence is still sparse.** Only two confirmed
  non-human natural reservoirs (armadillo, red squirrel). The
  medieval European red squirrel story (Urban 2024) is one data
  point; do not over-generalise.
- **M. lepromatosis is a distinct species.** Han et al. 2008
  described this separate leprosy agent, causing diffuse lepromatous
  leprosy. Not yet in the ancient DNA record. Do not conflate with
  *M. leprae*.
- **Skeletal diagnosis can be ambiguous.** Paleopathological
  identification of leprosy from bones requires specific lesion
  patterns; co-infection with syphilis or other diseases can
  confound. Always cross-reference with published skeletal reports.

## Integration with Other Skills

| Tool | Purpose |
|---|---|
| **`spaam-ancient-metagenome-dir`** | Primary ancient *M. leprae* catalogue (49 samples) |
| **`spaam-community`** | nf-core/eager / aMeta pipelines for processing |
| **`aadr`** | Ancient human hosts for the same skeletons |
| **`amtdb`** | Ancient human mtDNA for the same skeletons |
| **`slavevoyages`** | Trans-Atlantic dispersal of lineage 4 |
| **`pleiades`** / **`orbis`** | Historical place identifiers for medieval European sites |
| **`neolithic-14c`** / **`card`** / **`p3k14c`** | Chronological anchors |
| **`iqtree-lsd2`** / **`beast2-phylogeography`** | Tree building and dating |
| **`helicobacter-pylori-phylogeography`** | Another classical coevolution paradigm |
| **TBannotator MCP** | Comparative MTBC framework, the same methodology, applied to a different pathogen |
| **`ontologies`** | *M. leprae* = NCBITaxon:1769; *M. lepromatosis* = NCBITaxon:480418; leprosy = DOID:1024 |

## Citations

```bibtex
@article{schuenemann2013leprae,
  title   = {Genome-Wide Comparison of Medieval and Modern Mycobacterium leprae},
  author  = {Schuenemann, Verena J. and Singh, Pushpendra and Mendum, Thomas A.
             and Krause-Kyora, Ben and Jäger, Gunnar and Bos, Kirsten I.
             and Herbig, Alexander and Economou, Christos and Benjak, Andrej
             and Busso, Philippe and others},
  journal = {Science},
  volume  = {341},
  number  = {6142},
  pages   = {179--183},
  year    = {2013},
  doi     = {10.1126/science.1238286}
}

@article{schuenemann2018leprae,
  title   = {Ancient genomes reveal a high diversity of Mycobacterium
             leprae in medieval Europe},
  author  = {Schuenemann, Verena J. and Avanzi, Charlotte and Krause-Kyora,
             Ben and Seitz, Alexander and Herbig, Alexander and Inskip,
             Sarah A. and Bonazzi, Marion and Reiter, Ella and Urban,
             Christian and Pedersen, Dorthe Dangvard and others},
  journal = {PLOS Pathogens},
  volume  = {14},
  number  = {5},
  pages   = {e1006997},
  year    = {2018},
  doi     = {10.1371/journal.ppat.1006997}
}

@article{pfrengle2021leprae,
  title   = {Mycobacterium leprae diversity and population dynamics in
             medieval Europe from novel ancient genomes},
  author  = {Pfrengle, Saskia and Neukamm, Judith and Guellil, Meriam and
             Keller, Marcel and Molak, Martyna and Avanzi, Charlotte and
             Kushniarevich, Alena and Montes, N{\'u}ria and Neumann, Gunnar U.
             and Reiter, Ella and others},
  journal = {BMC Biology},
  volume  = {19},
  pages   = {220},
  year    = {2021},
  doi     = {10.1186/s12915-021-01120-2}
}

@article{urban2024squirrel,
  title   = {Ancient Mycobacterium leprae genome reveals medieval English
             red squirrels as animal leprosy host},
  author  = {Urban, Christian and Blom, Alette A. and Pfrengle, Saskia and
             Walker-Meikle, Kathleen and Stone, Anne C. and Inskip, Sarah A.
             and Schuenemann, Verena J.},
  journal = {Current Biology},
  volume  = {34},
  number  = {10},
  pages   = {2221--2230},
  year    = {2024},
  doi     = {10.1016/j.cub.2024.04.020}
}

@article{truman2011armadillo,
  title   = {Probable zoonotic leprosy in the southern United States},
  author  = {Truman, Richard W. and Singh, Pushpendra and Sharma, Rahul
             and Busso, Philippe and Rougemont, Jacques and Paniz-Mondolfi,
             Alberto and Kapopoulou, Adriana and Brisse, Sylvain and
             Scollard, David M. and Gillis, Thomas P. and Cole, Stewart T.},
  journal = {New England Journal of Medicine},
  volume  = {364},
  number  = {17},
  pages   = {1626--1633},
  year    = {2011},
  doi     = {10.1056/NEJMoa1010536}
}

@article{avanzi2016squirrelleprae,
  title   = {Red squirrels in the British Isles are infected with leprosy bacilli},
  author  = {Avanzi, Charlotte and del-Pozo, Jorge and Benjak, Andrej and
             Stevenson, Karen and Simpson, Victor R. and Busso, Philippe
             and McLuckie, Joyce and Loiseau, Camille and Lawton, Colin
             and Schoening, Janine and others},
  journal = {Science},
  volume  = {354},
  number  = {6313},
  pages   = {744--747},
  year    = {2016},
  doi     = {10.1126/science.aah3783}
}

@article{krausekyora2018leprae,
  title   = {Ancient DNA study reveals HLA susceptibility locus for
             leprosy in medieval Europeans},
  author  = {Krause-Kyora, Ben and Nutsua, Marcel and Boehme, Lisa and
             Pierini, Federica and Pedersen, Dorthe Dangvard and
             Kornell, Sabin-Christin and Drichel, Dmitriy and
             Bonazzi, Marion and Möbus, Lena and Tarp, Peter and others},
  journal = {Nature Communications},
  volume  = {9},
  pages   = {1569},
  year    = {2018},
  doi     = {10.1038/s41467-018-03857-x}
}

@article{mendum2014leprae,
  title   = {Mycobacterium leprae genomes from a British medieval
             leprosy hospital: towards understanding an ancient epidemic},
  author  = {Mendum, Thomas A. and Schuenemann, Verena J. and Roffey, Simon
             and Taylor, G. Michael and Wu, Huihai and Singh, Pushpendra
             and Tucker, Katie and Hinds, James and Cole, Stewart T. and
             Kierzek, Andrzej M. and Nieselt, Kay and Krause, Johannes and
             Stewart, Graham R.},
  journal = {BMC Genomics},
  volume  = {15},
  pages   = {270},
  year    = {2014},
  doi     = {10.1186/1471-2164-15-270}
}

@article{kerudin2019leprae,
  title   = {Ancient Mycobacterium leprae genomes from the mediaeval sites
             of Chichester and Raunds in England},
  author  = {Kerudin, Anisatu and Müller, Romy and Buckberry, Jo and
             Knüsel, Christopher J. and Brown, Terence A.},
  journal = {Journal of Archaeological Science},
  year    = {2019},
  doi     = {10.1016/j.jas.2019.04.008}
}

@article{fotakis2020leprae,
  title   = {Multi-omic detection of Mycobacterium leprae in
             archaeological human dental calculus},
  author  = {Fotakis, Anna K. and Denham, Sean D. and Mackie, Meaghan and
             Orbegozo, Maia Iturralde and Mylopotamitaki, Dimitra and
             Gopalakrishnan, Shyam and Sicheritz-Pontén, Thomas and
             Olsen, Jesper V. and Cappellini, Enrico and Zhang, Guojie and
             Christophersen, Axel and Gilbert, M. Thomas P. and Vågene, {\AA}shild J.},
  journal = {Philosophical Transactions of the Royal Society B},
  volume  = {375},
  number  = {1812},
  pages   = {20190584},
  year    = {2020},
  doi     = {10.1098/rstb.2019.0584}
}

@article{neukamm2020egypt,
  title   = {2000-year-old pathogen genomes reconstructed from
             metagenomic analysis of Egyptian mummified individuals},
  author  = {Neukamm, Judith and Pfrengle, Saskia and Molak, Martyna and
             Seitz, Alexander and Francken, Michael and Eppenberger, Patrick
             and Avanzi, Charlotte and Reiter, Ella and Urban, Christian and
             Welte, Ben and Stockhammer, Philipp W. and Teßmann, Barbara and
             Herbig, Alexander and Harvati, Katerina and Nieselt, Kay and
             Krause, Johannes and Schuenemann, Verena J.},
  journal = {BMC Biology},
  volume  = {18},
  pages   = {108},
  year    = {2020},
  doi     = {10.1186/s12915-020-00839-8}
}

@article{bonczarowska2022germany,
  title   = {Pathogen genomics study of an early medieval community in
             Germany reveals extensive co-infections},
  author  = {Bonczarowska, Joanna H. and Susat, Julian and Mühlemann, Barbara
             and Jasch-Boley, Ines and Brather, Sebastian and Höke, Benjamin
             and Brather-Walter, Susanne and Schoenenberg, Valerie and
             Scheschkewitz, Jonathan and Graenert, Gabriele and others},
  journal = {Genome Biology},
  volume  = {23},
  pages   = {250},
  year    = {2022},
  doi     = {10.1186/s13059-022-02806-8}
}
```
