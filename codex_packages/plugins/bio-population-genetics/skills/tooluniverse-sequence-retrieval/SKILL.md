---

name: tooluniverse-sequence-retrieval
description: Retrieves biological sequences (DNA, RNA, protein) from NCBI and ENA with gene disambiguation, accession type handling, and comprehensive sequence profiles. Creates detailed reports with sequence metadata, cross-database references, and download options. Use when users need nucleotide sequences, protein sequences, genome data, or mention GenBank, RefSeq, EMBL accessions.
---

# Biological Sequence Retrieval

Retrieve DNA, RNA, and protein sequences with proper disambiguation and cross-database handling.

**IMPORTANT**: Always use English terms in tool calls. Only try original-language terms as fallback. Respond in the user's language.

**LOOK UP DON'T GUESS**: Never assume accession numbers or sequence versions. Always retrieve and verify from NCBI or ENA.

## Domain Reasoning

Sequence quality hierarchy: RefSeq (NM_/NP_ = curated) > RefSeq predicted (XM_/XP_) > GenBank (submitted). Prefer the MANE Select transcript for human canonical isoforms. Check version numbers -- annotations improve across versions.

## Workflow

```
Phase 0: Clarify (if needed) → Phase 1: Disambiguate Gene/Organism → Phase 2: Search & Retrieve → Phase 3: Report
```

---

## Phase 0: Clarification (When Needed)

Ask ONLY if: gene exists in multiple organisms, sequence type unclear, or strain matters.
Skip for: specific accessions, clear organism+gene combos, complete genome requests with organism.

---

## Phase 1: Gene/Organism Disambiguation

### Accession Type Decision Tree

| Prefix | Type | Use With |
|--------|------|----------|
| NC_/NM_/NR_/NP_/XM_ | RefSeq | NCBI only |
| U*/M*/K*/X*/CP*/NZ_ | GenBank | NCBI or ENA |
| EMBL format | EMBL | ENA preferred |

**CRITICAL**: Never try ENA tools with RefSeq accessions -- they return 404.

### Identity Checklist
- Organism confirmed (scientific name)
- Gene symbol/name identified
- Sequence type determined (genomic/mRNA/protein)
- Accession prefix identified for tool selection

---

## Phase 2: Data Retrieval (Internal)

Retrieve silently. Do NOT narrate the search process.

### Obtaining `tu`

Every snippet below assumes a live ToolUniverse instance named `tu`. It does not
exist by default; create it once per session:

```bash
pip install tooluniverse
```

```python
from tooluniverse import ToolUniverse

tu = ToolUniverse()
tu.load_tools()                 # populates tu.tools; required before any call

# Confirm the NCBI/ENA tools are actually present in this install
print([n for n in tu.list_built_in_tools() if "NCBI" in n or "ena" in n.lower()])
```

If `tooluniverse` is not installed, or the NCBI tools are missing from the build,
do not fake the calls: fall back to the NCBI E-utilities over plain HTTP, which
need no package and are the substrate ToolUniverse wraps anyway.

```bash
# search
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=nuccore&term=katG[Gene]+AND+Mycobacterium+tuberculosis[Organism]&retmode=json"
# fetch FASTA by accession
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=NC_000962.3&rettype=fasta&retmode=text"
# ENA, non-RefSeq accessions only
curl -s "https://www.ebi.ac.uk/ena/browser/api/fasta/AL123456.3"
```

Set `NCBI_API_KEY` and pass it as `&api_key=$NCBI_API_KEY` to raise the E-utilities
rate limit from 3 to 10 requests per second.

### Tool calls

```python
# Search NCBI Nucleotide
result = tu.tools.NCBI_search_nucleotide(
    operation="search", organism=organism, gene=gene,
    strain=strain, keywords=keywords, seq_type=seq_type, limit=10
)

# Get accessions from UIDs
accessions = tu.tools.NCBI_fetch_accessions(operation="fetch_accession", uids=result["data"]["uids"])

# Retrieve sequence (FASTA or GenBank format)
sequence = tu.tools.NCBI_get_sequence(operation="fetch_sequence", accession=accession, format="fasta")

# ENA alternative (non-RefSeq accessions only)
entry = tu.tools.ena_get_entry(accession=accession)
fasta = tu.tools.ena_get_sequence_fasta(accession=accession)
```

### Fallback Chains

| Primary | Fallback | Notes |
|---------|----------|-------|
| NCBI_get_sequence | ENA (if GenBank format) | NCBI unavailable |
| ENA_get_entry | NCBI_get_sequence | ENA doesn't have RefSeq |
| NCBI_search_nucleotide | Try broader keywords | No results |

---

## Phase 3: Report Sequence Profile

Present as a **Sequence Profile Report**. Hide search process. Include:

1. **Search Summary**: query, database, result count
2. **Primary Sequence**: accession, type (RefSeq/GenBank), organism, strain, length, molecule, topology, curation level
3. **Sequence Preview**: first lines of FASTA (truncated)
4. **Annotations Summary**: CDS/tRNA/rRNA/regulatory feature counts (from GenBank format)
5. **Alternative Sequences**: ranked by relevance and curation, with ENA compatibility
6. **Cross-Database References**: RefSeq, GenBank, ENA/EMBL, BioProject, BioSample
7. **Download Options**: FASTA (for BLAST/alignment), GenBank (for annotation)

### Curation Level Tiers

| Tier | Prefix | Description |
|------|--------|-------------|
| RefSeq Reference (best) | NC_, NM_, NP_ | NCBI-curated, gold standard |
| RefSeq Predicted | XM_, XP_, XR_ | Computationally predicted |
| GenBank Validated | Various | Submitted, some curation |
| GenBank Direct | Various | Direct submission |
| Third Party | TPA_ | Third-party annotation |

---

## Reasoning Framework

**Sequence quality**: Prefer RefSeq over GenBank. Check version numbers. Sequences with "PREDICTED" in definition are not experimentally validated.

**Accession guidance**: RefSeq = NCBI-only. GenBank = mirrored in ENA/EMBL. Default to RefSeq mRNA (NM_) for human/model organisms; most complete genome assembly for microbial queries.

### Microbial and MTBC retrieval

The defaults above (NM_/NP_, MANE Select) are human-centric and do not apply to
bacteria: prokaryotic genes have no introns, no alternative transcripts and
therefore no MANE concept. For a bacterial gene, retrieve the genome and the CDS
feature, not a transcript.

| Target | Accession | Note |
|---|---|---|
| H37Rv reference genome | `NC_000962.3` (RefSeq) | GenBank equivalent `AL123456.3`; same sequence, different annotation lineage |
| M. bovis AF2122/97 | `NC_002945.4` | |
| A single gene, e.g. katG | `Rv1908c` locus tag | Resolve through the genome record's CDS features, or through UniProt; there is no per-gene RefSeq accession |
| Protein product | `NP_216424.1` (katG) | RefSeq protein accessions do exist for bacteria |

```python
# Whole genome, FASTA
seq = tu.tools.NCBI_get_sequence(operation="fetch_sequence",
                                 accession="NC_000962.3", format="fasta")

# Annotated genome (GenBank) to walk CDS features and pull one locus tag
gb = tu.tools.NCBI_get_sequence(operation="fetch_sequence",
                                accession="NC_000962.3", format="gb")
```

A full H37Rv GenBank record is around 4.4 Mb of sequence plus roughly 4000
features, so parse it with `biopython` (`SeqIO.parse(..., "genbank")`) rather than
reading it into the conversation. For a gene's function, `mtbc-gene` answers
offline-first and is the faster path; use this skill when the raw sequence itself
is what is needed, for instance to feed an alignment or a BLAST.

Strain matters for MTBC: an accession retrieved for "Mycobacterium tuberculosis"
without a strain qualifier may be any of thousands of deposited genomes. Always
confirm the strain in the record before using coordinates from it, because
positions are only comparable against H37Rv.

**Cross-database reconciliation**: Same sequence may have different accessions (e.g., GenBank U00096 = RefSeq NC_000913 for E. coli K-12). Always report both when available. Discrepancies between GenBank/RefSeq typically indicate RefSeq curation corrected submission errors.

### Synthesis Questions
1. What is the highest-quality accession available?
2. Are there alternative accessions in other databases?
3. What is the annotation completeness?
4. Is the sequence from the expected organism/strain?
5. What download format suits the user's downstream analysis?

---

## Error Handling

| Error | Response |
|-------|----------|
| "No search criteria provided" | Add organism, gene, or keywords |
| "ENA 404 error" | Likely RefSeq -- use NCBI only |
| "No results found" | Broaden search, check spelling, try synonyms |
| "Sequence too large" | Note size, provide download link instead |

---

## Tool Reference

**NCBI Tools**: `NCBI_search_nucleotide` (search), `NCBI_fetch_accessions` (UID→accession), `NCBI_get_sequence` (retrieve)
**ENA Tools (GenBank/EMBL only)**: `ena_get_entry` (metadata), `ena_get_sequence_fasta` (FASTA), `ena_get_entry_summary` (summary)

---

## Search Parameters Reference

**NCBI_search_nucleotide**: `operation`="search", `organism` (scientific name), `gene` (symbol), `strain`, `keywords`, `seq_type` (complete_genome/mrna/refseq), `limit`

**NCBI_get_sequence**: `operation`="fetch_sequence", `accession`, `format` (fasta/genbank)
