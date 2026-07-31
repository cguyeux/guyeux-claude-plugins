---
name: fetch-tbannotator
description: "Fetch report.json and generate spdi.txt for MTBC strains from the TBannotator server. Use when populating BDD directories with missing genomic data for strains already in the TBannotator database."
argument-hint: <lineage_dir> [strain1 strain2 ...] | <lineage_dir> --all-empty | <prefix> --all-missing (recursive across a clade tree)
user-invocable: true
disable-model-invocation: false
allowed-tools: Bash, Read, Write, Glob, Grep, mcp__tbannotator__tool_query_postgres
---

# Fetch TBannotator Reports

Retrieve `report.json` and generate `spdi.txt` for MTBC strains from the TBannotator pipeline.

> [!NOTE]
> **Timeouts adaptatifs selon la source (sinon faux echecs sur gros telechargements).**
> ERR (ENA, souvent > 900 Mo) = **3 h** ; FASTQ deja locaux = 1 h ; mapping seul = 30 min.
> Pour les paired-end ENA, utiliser **`prefetch` + `fasterq-dump --split-3`** (jamais
> `fastq-dump` seul, qui peut tronquer ou ne pas separer les paires).

## Arguments

- `$0`: Lineage directory path (relative to BDD/, e.g. `Pinipedii`, `L6.1.1`, or absolute path) : OR a clade PREFIX (e.g. `Bovis`) when combined with `--all-missing`.
- `$1...`: Either specific strain accessions (SRR/ERR/DRR), or `--all-empty` to auto-detect empty directories in ONE lineage dir, or `--all-missing` to scan a whole clade tree recursively (see below).

> **Two distinct "missing" cases.** `--all-empty` targets subdirs missing `spdi.txt` (never populated). But a
> subdir can have `spdi.txt` (valid placement) yet lack `report.json` (annotation gap). `--all-missing` catches
> BOTH, recursively across all sub-clades under a prefix, the right mode when an audit reports strains scattered
> across many clades (don't invoke the per-lineage mode N times).

## Access routes : primary vs fallback

TBannotator data lives in **two equivalent locations**. Always try the primary (SSH) route first; fall back to HTTP only if SSH is unavailable.

### Primary: SSH/scp on `mp` (canonical pipeline)

The TBannotator Snakemake pipeline by Gaëtan Senelle (`gsenelle`) runs on **`mp`** (SSH alias for `mesoprivate1.univ-fcomte.fr`, defined in `~/.ssh/config`, reached via ProxyCommand bilbo). All annotated strains live as filesystem directories at:

```
mp:/data/current/run/results/<SRA>/
    report.json
    snps.vcf
    (other intermediate files)
```

As of 2026-05, this filesystem contains **~136 000 annotated MTBC strains**. The HTTP server below exposes the same data but is hosted on a personal Freebox and may go down : SSH is the canonical route.

Existence check:
```bash
ssh mp 'test -e /data/current/run/results/<SRA>/report.json && echo OK || echo MISS'
```

Fetch (per strain):
```bash
mkdir -p "$target/NC_000962.3"
scp "mp:/data/current/run/results/<SRA>/{report.json,snps.vcf}" "$target/NC_000962.3/"
```

Bulk existence probe (45 strains in one round-trip):
```bash
RUNS="SRR123 ERR456 ..."
ssh mp "cd /data/current/run/results && for s in $RUNS; do
    [ -f \$s/report.json ] && echo \"FOUND \$s\" || echo \"MISS \$s\"
done"
```

### Recursive mode `--all-missing` (strains scattered across a clade tree)

When an audit reports strains missing `report.json` spread across many sub-clades (e.g. 57 across ~10 `Bovis.*`
dirs), scan the whole tree once instead of invoking the per-lineage mode N times. Recipe (one disk scan + one bulk
SSH probe + per-FOUND scp): collect every `<BDD>/<prefix>*/<SRA>/NC_000962.3/` that has `spdi.txt` but no
`report.json`, probe `mp` for all of them in a single round-trip, `scp` the FOUND, list the MISS. A ready-made,
read-only implementation of exactly this lives at `mtbc/Bovis_emergence/analyses/fetch_missing_reports.py`
(`--dry-run`/`--prefix`, idempotent), reuse or adapt it rather than hand-looping.

> **Rolling-window caveat (verified 2026-06-30).** The ~136k figure is a SNAPSHOT: `mp:/data/current/run/results`
> is a rolling window, so a strain annotated in the past can have its `report.json` PURGED from the server. Such a
> strain probes `MISS` even though it has a valid local `spdi.txt`. It then needs a **full re-annotation**
> (ingestion → download + map + annotate), NOT a fetch. Real case: of 57 missing-`report.json` Bovis strains, only
> 6 were still on the server; 51 (mostly ERR/ENA) were purged → re-ingestion required, not scp. Always report the
> MISS split (purged-needs-reingest vs never-ingested) rather than assuming a fetch will recover them.

### Fallback: HTTP server (TBannotator v2 MCP)

- report.json: `https://tblearn.tbannotator.ideev.universite-paris-saclay.fr/mcp/download/report/{strain}`
- spdi.txt: extracted from the downloaded report.json (snp[].spdi field)

When the HTTP server returns 503 or times out, switch to SSH mp.

### When a strain is in neither location

The strain has **never been ingested**. To ingest, append the SRA to `/data/current/run/config/samples.tsv` on mp and (re)launch the pipeline.

**Append with dedup (preserves in-flight candidates, restores header)**:
```bash
scp ./new_sras.txt mp:~/new_sras.txt   # one accession per line, no header
ssh mp '
  cp /data/current/run/config/samples.tsv /data/current/run/config/samples.tsv.bak_$(date +%Y%m%d)
  (echo accession; grep -v "^accession$" /data/current/run/config/samples.tsv; cat ~/new_sras.txt) \
    | awk "NR==1 || (!seen[\$0]++ && \$0!=\"accession\")" \
    > /tmp/merged.tsv
  mv /tmp/merged.tsv /data/current/run/config/samples.tsv
  wc -l /data/current/run/config/samples.tsv
'
```

Launch (only if `script.sh` is not already running, check `ps aux | grep snakemake` first):
```bash
ssh mp 'cd /data/current/run && nohup ./script.sh > /tmp/snakemake_$(date +%Y%m%d).log 2>&1 & disown'
```

**Do not** use `~/integrate_new_sras.py` on mp for an append workflow, that helper opens `samples.tsv` in mode `'w'` and would wipe existing in-flight candidates. Manual append is safer.

## Directory structure expected (local)

```
BDD/{lineage}/{strain}/NC_000962.3/
    report.json    <- downloaded
    spdi.txt       <- generated from report.json
```

## Steps to follow

1. **Resolve the BDD path**: if `$0` doesn't start with `/`, prepend the TBannotator BDD root (find it by looking for a `BDD/` directory in the current project tree, typically `../../BDD/` from articles/ or the repo root's `BDD/`).

2. **Identify target strains**:
   - If `--all-empty` is passed: scan the lineage directory for subdirectories missing `NC_000962.3/spdi.txt`
   - Otherwise: use the strain accessions provided as arguments

3. **Probe availability** (bulk SSH single round-trip preferred over per-strain HTTP):
   ```bash
   ssh mp "cd /data/current/run/results && for s in $STRAINS; do
       [ -f \$s/report.json ] && echo \"FOUND \$s\" || echo \"MISS \$s\"
   done"
   ```

4. **For each FOUND strain**:
   - `scp` `report.json` and `snps.vcf` into `BDD/{lineage}/{strain}/NC_000962.3/`
   - Generate `spdi.txt` from `report.json`:
     ```python
     import json
     data = json.load(open(report_path))
     spdis = [snp['spdi'] for snp in data.get('snp', []) if snp.get('spdi')]
     open(spdi_path, 'w').write('\n'.join(spdis))
     ```

5. **For each MISS strain**:
   - If only a few: try the HTTP fallback before declaring absence.
   - If many: prepare a `new_sras.txt` and follow the ingestion procedure above.

6. **Verify** by listing each strain with report status and SPDI count. Compare counts against the per-lineage median (typical MTBC range: ~1200–2400 SPDI on H37Rv). Counts <500 signal a mapping failure, flag for `strain-qc`.

### Validation
After completion, optionally verify a sample strain against the DB:
```sql
SELECT COUNT(*) FROM tb_report_strain_spdi ss
JOIN tb_report_strain s ON s.strain_id = ss.strain_id
WHERE s.strain_name = '{strain}'
```
Compare with the line count of the generated spdi.txt.

## Example usage

```
/fetch-tbannotator Pinipedii --all-empty
/fetch-tbannotator L6.1.1 ERR1023220 ERR1023225
/fetch-tbannotator /home/user/project/BDD/Dassie --all-empty
```
