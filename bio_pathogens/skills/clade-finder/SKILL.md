---
name: clade-finder
description: >-
  Recherche de clades et sous-populations dans une lignee MTBC.
  Construit des vecteurs de features par SRA (pan-SPDI, positions IS,
  RD) a partir des fichiers report.json ou spdi.txt du repertoire
  bdd/actuelle/L<x>/. Applique t-SNE + HDBSCAN et produit un PNG
  haute resolution pour visualiser les sous-lignees potentielles.
  Une fois un cluster identifie, verifier dans `tbmonitor-papers`
  (~190k papiers PubMed TB pre-indexes) s'il a deja ete decrit dans
  la litterature avant de proposer une nouvelle sous-lignee.

  Use when: exploring sub-lineage structure within a lineage directory,
  looking for population clusters, checking if a lineage should be split.

  Pour la phase post-decouverte (extraction iterative pectinee des sous-clades
  apres avoir construit un arbre RAxML focalise et identifie visuellement les
  candidats), utiliser le skill complementaire `pectinated-subclade-mining`
  qui formalise le filtre PER-POOL strict de synapomorphismes SPDI.
argument-hint: "<chemin vers bdd/actuelle/L4.x/> [--min-cluster-size N] [--dpi 300]"
allowed-tools: Bash, Read, Write, Glob, Grep
---

# /clade-finder -- Recherche de sous-populations dans une lignee MTBC

A partir d'un repertoire de lignee dans `bdd/actuelle/`, construit un vecteur
de features par SRA (pan-SPDI + IS + RD), applique t-SNE + HDBSCAN, et produit
un PNG haute resolution pour voir a l'oeil nu si des sous-lignees existent.

## Declenchement

```
/clade-finder /path/to/bdd/actuelle/L4.9/
/clade-finder /path/to/bdd/actuelle/L4.9/ --min-cluster-size 10
/clade-finder /path/to/bdd/actuelle/L4.9/ --no-is --no-rd
```

## Phase 0 -- Scan du repertoire

1. Lister les sous-repertoires SRA dans le repertoire de lignee
2. Pour chaque SRA, verifier l'existence de `SRA/NC_000962.3/report.json`
   (source preferee) ou `SRA/NC_000962.3/spdi.txt` (fallback)
3. Ignorer les SRA sans aucune source de donnees
4. Afficher :
```
Clade-finder : L4.9
SRAs trouves   : 820
  avec report.json : 780
  avec spdi.txt seul : 35
  sans donnees (ignores) : 5
```

## Phase 1 -- Extraction des features

Executer le script (livre avec le skill) :
```bash
python3 "$CLAUDE_PLUGIN_ROOT/skills/clade-finder/scripts/clade_finder.py" \
  /path/to/bdd/actuelle/L4.9/ [options]
# ou, chemin absolu : ~/docs/codes/claude_plugins/bio_pathogens/skills/clade-finder/scripts/clade_finder.py
```

Le script lit chaque SRA et construit 3 sous-vecteurs :

### 1. Pan-SPDI (presence/absence)

- **Source** : `report.json` → `d['snp'][i]['spdi']`, ou fallback `spdi.txt`
- Union de tous les SPDIs de tous les SRAs = pan-SPDI
- Matrice binaire : 1 si le SRA a ce SPDI, 0 sinon
- **Filtrage** : exclure les SPDIs presents dans < 2 SRAs (singletons)
  et > 98% des SRAs (quasi-fixes, non informatifs)

### 2. Positions IS (presence/absence)

- **Source** : `report.json` → `d['insertion_sequences']`
- Chaque IS = paire (nom, position) → identifiant unique `IS6110_701383`
- Pan-IS = union de toutes les paires (nom, position)
- Matrice binaire par SRA
- Si `--no-is` : ignorer cette source

### 3. RD (presence/absence)

- **Source** : `report.json` → `d['large_rd']` + `d['missing_rd']`
- Pan-RD = union de tous les noms de RD
- Un RD est "present" si son `percent_missing` < 50%
  (dans `large_rd` avec couverture normale)
- Un RD est "absent" s'il est dans `missing_rd`
- Si `--no-rd` : ignorer cette source

### Concatenation

Matrice finale : n_SRA × (n_spdi + n_is + n_rd), toute binaire.

## Phase 2 -- t-SNE + HDBSCAN

- **Metrique** : Jaccard (adaptee aux donnees binaires)
- **Perplexite** : auto = max(5, (n-1)/3), ou valeur forcee
- **min_cluster_size** : auto = max(3, n/15), ou valeur forcee
- **seed** : 42 (reproductibilite)
- Le script calcule aussi le silhouette score

## Phase 3 -- PNG

Le script produit un PNG (defaut 300 DPI, 16×10 pouces) :
- **Panel gauche** : t-SNE colore par cluster HDBSCAN, bruit en gris
- **Panel droit** : meme t-SNE colore par densite ou avec labels SRA si < 150
- Titre : nom de la lignee + stats (n SRAs, n clusters, silhouette)
- Legende avec taille de chaque cluster
- Sauvegarde : `<lineage_dir>/clade_finder.png` (ou `--output`)

## Phase 4 -- Rapport

Le script affiche un JSON resume sur stdout :
```json
{
  "lineage": "L4.9",
  "n_samples": 815,
  "features": {"spdi": 4521, "is": 87, "rd": 42, "total": 4650},
  "tsne": {"perplexity": 30.0},
  "hdbscan": {
    "n_clusters": 5,
    "noise_count": 23,
    "silhouette_score": 0.67,
    "cluster_sizes": {"0": 312, "1": 198, "2": 145, "3": 98, "4": 39}
  },
  "output_png": "/path/to/L4.9/clade_finder.png"
}
```

Interpreter le resultat :
- **silhouette > 0.5** + **clusters bien separes** → sous-lignees probables
- **silhouette 0.25-0.5** → structure faible, a confirmer
- **silhouette < 0.25** ou **1 seul cluster** → lignee homogene, pas de split

## Options du script

| Option | Defaut | Description |
|--------|--------|-------------|
| `--min-cluster-size N` | auto | Taille minimale d'un cluster HDBSCAN |
| `--perplexity N` | auto | Perplexite t-SNE |
| `--dpi N` | 300 | Resolution du PNG |
| `--no-spdi` | off | Exclure les SPDIs des features |
| `--no-is` | off | Exclure les IS des features |
| `--no-rd` | off | Exclure les RD des features |
| `--output PATH` | `<dir>/clade_finder.png` | Chemin du PNG de sortie |
| `--ref REF` | `NC_000962.3` | ID de la reference genome |
| `--min-freq F` | 0.02 | Freq min d'un SPDI pour etre retenu (defaut 2%) |
| `--max-freq F` | 0.98 | Freq max d'un SPDI pour etre retenu (defaut 98%) |
