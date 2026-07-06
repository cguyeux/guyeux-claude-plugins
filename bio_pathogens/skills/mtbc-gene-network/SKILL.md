---
name: mtbc-gene-network
description: >-
  Query the MTBC gene interaction network as a graph, LOCAL-FIRST from the group's own
  precomputed whole-proteome STRING network (annotation_mtbc/résultats/phase2h_string,
  ~4000 genes, ~38k medium-confidence edges, per-channel evidence). Loads it with
  networkx and exposes the graph operations the annotation pipeline does not: the
  interaction neighbours of a gene, the induced subnetwork of a gene set, the shortest
  path between two genes, the network hubs (degree / betweenness centrality), the
  functional modules (community detection), and guilt-by-association for a dark gene
  (infer its role from its high-confidence partners' functions, via mtbc-gene-function).
  The STRING API (`string-db` skill) is only the fallback for a gene absent locally.

  Use when: finding what a gene interacts with, building a PPI subnetwork for a pathway
  or a gene list, locating the hub/bottleneck genes of the interactome, detecting
  functional modules/operon-like clusters, hypothesising a function for an uncharacterised
  Rv locus from its neighbourhood, or producing network evidence for a manuscript figure.
argument-hint: "<command> [gene...] [--min-score N] [--top N]"
allowed-tools: Bash, Read, Write
user-invocable: true
---

# mtbc-gene-network — the MTBC interactome as a queryable graph (local-first)

## Overview

`annotation_mtbc` already computed the whole-proteome STRING network once
(`résultats/phase2h_string/string.json`: per gene, the partner list with combined score
and per-channel evidence). This skill loads that as a **networkx** graph and runs the
graph algorithms the annotation pipeline does not (it builds the network but never
analyses it as a graph). Answers come from your local interactome FIRST; the `string-db`
API is the fallback for a gene that is not in it.

## Requirements

networkx (present on the system Python; `pip install networkx` otherwise). The
`guilt` command additionally uses `mtbc-gene-function` (neighbour functions) and the API
fallback uses `string-db`, both lazily. The launcher wires all three:

```bash
cd <this skill> && ./run_network.sh neighbors katG --top 10
```

Set `MTBC_ANNOTATION_DIR` if `annotation_mtbc` is not at `~/docs/codes/mtbc/annotation_mtbc`.

## Commands

```bash
SRC=<this skill>/src ; export PYTHONPATH="$SRC"
python3 -m mtbc_gene_network info                                  # network size
python3 -m mtbc_gene_network neighbors katG --min-score 700 --top 10
python3 -m mtbc_gene_network path katG rpoB                        # shortest path (hops)
python3 -m mtbc_gene_network subnetwork katG,ahpC,furA,sodA        # induced subnetwork
python3 -m mtbc_gene_network hubs --top 20 [--metric betweenness]  # central genes
python3 -m mtbc_gene_network --min-score 700 communities --top 15  # functional modules
./run_network.sh guilt Rv2239c --min-score 700                     # dark-gene inference
python3 -m mtbc_gene_network.smoke_test                            # offline self-check
```

`--min-score` is the STRING combined-score threshold (400 medium, 700 high) and applies
to the whole graph; raise it for sparser, higher-confidence analyses (and faster
community detection). Genes are given by name (`katG`) or Rv locus tag (`Rv1908c`).

## What each command returns

- **neighbors** — partners sorted by confidence, with gene/product and score.
- **path** — the shortest chain of interactions between two genes (hops + weakest edge).
- **subnetwork** — the induced graph over a gene set (nodes, edges, edge scores): the
  PPI sub-graph of a pathway or a candidate operon.
- **hubs** — most connected genes (degree) or bottlenecks (sampled betweenness). On the
  MTBC interactome the degree hubs are the PKS/PDIM cluster (mas, pks2/5/12, ppsC).
- **communities** — functional modules by greedy modularity (gene sets).
- **guilt** — for a dark / hypothetical gene, its high-confidence partners with their
  curated functions (joined via `mtbc-gene-function`), i.e. a guilt-by-association
  functional hypothesis. Validated example: Rv2239c partners include `ahpE` (thiol
  peroxidase).

## Caveats

- **STRING confidence ≠ physical interaction.** STRING aggregates evidence channels
  (text-mining, co-expression, genomic context...). Filter by `--min-score` and inspect
  the channels for a claim; context-driven edges are flagged.
- **Community detection is heuristic.** Greedy modularity gives one partition; report it
  as modules, not ground-truth operons. Higher `--min-score` yields cleaner modules.
- **Betweenness is sampled** (`k` source nodes) for speed on ~4000 nodes; it is
  approximate. Degree is exact.

## Integration with other skills

| Tool | Role |
|---|---|
| `mtbc-gene-function` | curated function of a gene / of a neighbour (powers `guilt`) |
| `string-db` | STRING API fallback for a gene absent from the local interactome |
| `mtbc-pathway-explain` | narrate a module/subnetwork as a pathway |
| `networkx` | further custom graph analysis on the loaded graph |
| `itol` | render a tree; this skill renders the interaction graph side |
