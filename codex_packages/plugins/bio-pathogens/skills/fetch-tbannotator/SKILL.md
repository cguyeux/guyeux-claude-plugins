---

name: fetch-tbannotator
description: "\"Academic research tooling for peer-reviewed MTBC phylogenomics (Guyeux group, FEMTO-ST): fetch report.json and generate spdi.txt for published research isolates from the TBannotator server, and queue new SRA accessions for annotation with `sra_to_add.py` (pre-flight against ENA + the pipeline queue, then a safe append to samples.tsv on mp). Use when populating BDD directories with missing genomic data, or when asked to add / ingest / queue SRA runs into the TBannotator pipeline.\""
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

TBannotator data lives in two locations that are **NOT always in sync**. Try the primary (SSH) route first; fall back to HTTP if SSH is unavailable — and **fall back the other way too**.

> [!WARNING]
> **The two sources DESYNCHRONISE, in both directions (verified 2026-07-31).** `mp:/data/current/run/results/` is a
> rolling window; the HTTP server exposes the annotated database. Real case: 67 strains of one BioProject were served
> fine over HTTP while **none of them had a `report.json` on `mp`**. So `MISS` on `mp` does **not** mean "absent from
> TBannotator", and an HTTP 404 does not mean `mp` lacks it. **Probe BOTH before concluding a strain must be
> re-ingested** — re-ingestion is expensive and usually unnecessary.

### Primary: SSH/scp on `mp` (canonical pipeline)

> [!IMPORTANT]
> **`mp` n'est joignable que VPN monté : `sudo vpn up`.** Le symptôme d'un VPN tombé est
> `Connection timed out during banner exchange`, qui ressemble à une panne serveur et n'en est pas une
> (l'« outage transitoire » noté ici le 2026-07-31 était selon toute vraisemblance cela). Vérifier le VPN
> **avant** de basculer sur la route HTTP, et ne jamais conclure d'un échec SSH qu'une souche est absente
> de TBannotator. La commande est à lancer par l'utilisateur (`! sudo vpn up`), elle demande un mot de passe.

The TBannotator Snakemake pipeline by Gaëtan Senelle (`gsenelle`) runs on **`mp`** (SSH alias for `mesoprivate1.univ-fcomte.fr`, defined in `~/.ssh/config`, reached via ProxyCommand bilbo). All annotated strains live as filesystem directories at:

```
mp:/data/current/run/results/<SRA>/
    report.json
    snps.vcf
    (other intermediate files)
```

As of 2026-05, this filesystem contains **~136 000 annotated MTBC strains**. The HTTP server below exposes the same data but is hosted on a personal Freebox and may go down : SSH is the canonical route.

Existence check — **always include a POSITIVE CONTROL**:
```bash
# <SRA> = the strain in question ; <KNOWN> = a strain you KNOW is available (e.g. one you just fetched)
ssh mp 'cd /data/current/run/results && for s in <SRA> <KNOWN>; do
    [ -f $s/report.json ] && echo "FOUND $s" || echo "MISS  $s"
done'
```
If the **known** strain also comes back `MISS`, the probe is measuring nothing: stop and diagnose the route instead
of concluding the strain is absent. This single control is what separates "this strain needs re-ingestion" from
"this filesystem no longer holds any of them".

> [!IMPORTANT]
> **Test the FILE, never the directory.** `results/<SRA>/` can exist while holding no `report.json` at all. Seen on
> 69 directories containing only `genes.bed`, `is.bed`, `rd.bed` and `logs/prefetch.log` from a **failed run**
> (prefetch died fetching the reference: *"path not found while creating directory"*). A `[ -d <SRA> ]` test then
> says "present" and `[ -f <SRA>/report.json ]` says "absent" for the very same strain. To tell apart *never
> ingested* / *failed run* / *purged from the rolling window*, read `logs/prefetch.log` and the directory's date
> (`stat -c %y`). Note that a failed prefetch is **not** discriminating on its own: strains that failed identically
> in that run were later annotated by another one.

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

When the HTTP server returns 503 or times out, switch to SSH mp. **And symmetrically**: when `mp` is unreachable
(seen 2026-07-31: `Connection timed out during banner exchange`), fall back to HTTP — that outage proved transient,
so **re-test before declaring a route dead**. HTTP is also the route that actually held the data in that case:
29 genomes were retrieved over HTTP while `mp` had none of them.

A clean **404** here means the strain is in neither the annotated database nor reachable that way — that is the
signal for re-ingestion, unlike a 503/timeout which is an outage.

### When a strain is in neither location

The strain has **never been ingested**. To ingest, append the SRA to `/data/current/run/config/samples.tsv` on mp and (re)launch the pipeline.

#### Route outillée : `sra_to_add.py` (à préférer)

```bash
S=scripts/sra_to_add.py

python3 $S --check ERR1023220 SRR1234567          # pré-vol seul, aucune écriture
python3 $S --check --file candidates.tsv          # accepte un TSV (1er champ reconnu)
python3 $S --queue --file new_sras.txt            # empile dans la file LOCALE
python3 $S --list                                 # état de la file locale
python3 $S --push                                 # dry-run vers mp
python3 $S --push --apply                         # écrit réellement samples.tsv
```

Le **pré-vol** classe chaque accession en `A_AJOUTER` / `DEJA_EN_FILE` / `DEJA_ANNOTE` / `DOUTEUSE` /
`INVALIDE`, en croisant trois sources : format de l'accession, métadonnées ENA (existence réelle,
organisme déclaré, taille à télécharger, plateforme), et état distant (`samples.tsv` + `results/`, avec
repli HTTP). Il évite les trois dépenses inutiles : ingérer une accession qui n'existe pas, ré-ingérer
une souche déjà annotée, et lancer des jours de calcul sur un run hors Mycobacterium.

> [!NOTE]
> L'organisme ENA est **déclaratif** : un run MTBC peut être déposé sous « Mycobacterium sp. » et
> l'inverse existe. Le script lève un drapeau, il ne rejette pas. Une accession `Escherichia coli`
> reste ingérable si tu sais pourquoi.

La **file locale** (`sra_to_add.txt`, écrit à la racine du projet, celle qui porte `cahier_de_labo.md`)
existe pour une raison précise : `mp` n'est joignable que VPN monté, et une session sans VPN ne doit pas
perdre le travail de qualification. `--push` sans VPN sort en code 2 **sans toucher à la file**, il suffit
de relancer plus tard. `--push --apply` vide la file seulement après avoir vérifié le nombre de lignes du
fichier transféré.

L'écriture distante ne perd rien : sauvegarde datée `samples.tsv.bak_<horodatage>`, toutes les lignes
existantes conservées dans leur ordre (les candidats en vol des autres campagnes), dédoublonnage sur le
premier champ, en-tête `accession` restauré, `mv` atomique après contrôle du décompte.

Codes de sortie : `0` rien à signaler, `1` au moins une accession refusée ou douteuse, `2` `mp`
injoignable (VPN) ou contrôle de décompte échoué.

#### Route manuelle (repli si le script est indisponible)

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

> [!CAUTION]
> **Appending and launching are TWO decisions, not one — dissociate them.** `sra_to_add.py` n'a
> volontairement **aucun** mode de lancement : il imprime la commande et le contrôle de processus, la
> décision reste humaine. The append above is cheap and reversible
> (dated backup + dedup). **Launching is not**: `samples.tsv` routinely holds hundreds of accessions belonging to
> OTHER work (seen 2026-07-31: 299 `CUS*` candidates unrelated to the project at hand), and the run embarks all of
> them on a shared server. Weigh it against the actual gain — adding 2 strains out of 69, changing no conclusion,
> does not justify an unsolicited compute run. **Ask the user before launching**; appending alone is usually enough,
> since the strains will be annotated on the next run they start themselves.
>
> **Counting processes is unreliable**: `ps aux | grep -c "[s]nakemake"` returned `2` with no pipeline running,
> because the enclosing `bash -c`/ssh command line CONTAINS the string. The `[s]` trick stops grep matching itself,
> not its wrapper. Tell-tale sign: the count rises exactly when you run the check. Use
> `ps -eo user,pid,lstart,cmd | grep "[s]nakemake"` and **read the lines** instead of trusting the count.

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

## Codex workflow guardrail

This packaged copy imports a Claude-origin project workflow into Codex. Before writing project registers, moving BDD files, changing Atlas content, appending remote queues, archiving a project, or launching remote compute, require an explicit user request in the current turn. Use recoverable operations only, keep project provenance boundaries, and follow the global rule that files are moved to the trash rather than permanently deleted.

## Codex MCP note

MCP tool names in `allowed-tools` are prerequisites. Verify them with `codex mcp list` before relying on live queries.
