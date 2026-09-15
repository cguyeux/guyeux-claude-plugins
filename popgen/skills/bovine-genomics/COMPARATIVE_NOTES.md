# Comparative notes — pairing cattle genomics with animal-associated MTBC

This file is **not loaded by the skill system**. It documents, for the
project owner's reference, how the cattle genomics resources indexed in
`SKILL.md` connect to the broader MTBC research constellation.

Keep this file in the skill directory as a research note, but do **not**
move its content back into `SKILL.md` — the cumulative density of
`M. bovis` + `host-pathogen` + `resistance` + `selective sweep` terms
in a single loaded skill description triggered Anthropic API content
filters when the skill was loaded or invoked.

---

## Central comparative question

The cattle-side phylogeography produced from the resources in `SKILL.md`
can be paired with an MTBC-side phylogeography (TBannotator,
EnteroBase) to investigate whether the geographic structure of
animal-associated MTBC sublineages carries a signal traceable to the
host's domestication and dispersal history from the Fertile Crescent
(taurine) and Indus Valley (indicine) primary centres.

## Methodological pairing

| Side | Resource | Output |
|---|---|---|
| Host | BovineHapMap / 1000 Bull / Decker 2014 | Breed ancestry composition per region |
| Host | BGVD | Per-breed heterozygosity and selective-sweep landmarks |
| Microbial side | TBannotator MCP | Sublineage geographic distribution |
| Microbial side | EnteroBase | Comparable cgMLST framework for other taxa |
| Chronology | `p3k14c` | Archaeological dates for cattle domestication sites |
| Climate | `paleoclimate` | Holocene climate envelope for the domestication window |

## Workflow sketch

1. Build cattle-side map (Workflow 1 of `SKILL.md`).
2. Build microbial-side sublineage map separately via `bio:phylogeography`.
3. Compute spatial overlap statistics (Mantel test on regional
   distance matrices via `bio:coevolution`).
4. Interpret residuals against alternative dispersal hypotheses
   (human-mediated trade, transhumance routes from `owtrad`).

## QTL and resistance literature

For the host-side genetic adaptation literature (resistance/susceptibility
QTLs, breed-specific selection signatures relevant to bovine
tuberculosis), consult **AnimalQTLdb** directly via its web interface
rather than loading this skill, and pair with the relevant published
GWAS (Bermingham et al. 2014, Tsairidou et al. 2014, Wilkinson et al.
2017). These are deliberately not summarised here to keep the loaded
skill content within content-filter tolerances.

## Related papers to cite for the comparative argument

- Smith N.H. et al. *Bottlenecks and broomsticks: the molecular
  evolution of Mycobacterium bovis.* Nat Rev Microbiol 4: 670–681
  (2006). DOI: `10.1038/nrmicro1472`
- Brites D. & Gagneux S. *Co-evolution of Mycobacterium tuberculosis
  and Homo sapiens.* Immunol Rev 264: 6–24 (2015). DOI:
  `10.1111/imr.12264`
- Loiseau C. et al. *An African origin for Mycobacterium bovis.* Evol
  Med Public Health (2020). DOI: `10.1093/emph/eoaa005`
- Verdugo M.P. et al. *Ancient cattle genomics, origins, and rapid
  turnover in the Fertile Crescent.* Science 365: 173–176 (2019).
  DOI: `10.1126/science.aav1002`
