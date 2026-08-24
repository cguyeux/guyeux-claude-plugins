# Audit des paquets workflow Codex

Ce fichier est genere par `_audit/tools/materialize_codex_workflow_packages.py`.
Il couvre les workflows projet importes avec garde-fou explicite de mutation.

| skill | paquet | fichiers copies | fichiers exclus | racines exclues |
|---|---|---:|---:|---|
| atlas-add-lineage | bio-pathogens | 1 | 0 | none |
| bdd-bridge | bio-pathogens | 4 | 0 | none |
| denovo-content-qc | bio-pathogens | 4 | 1 | __pycache__ |
| fetch-tbannotator | bio-pathogens | 3 | 1 | __pycache__ |
| mtbc-bilan | bio-pathogens | 17 | 0 | none |
| mtbc-reboot | bio-pathogens | 1 | 0 | none |
| pectinated-subclade-mining | bio-pathogens | 2 | 0 | none |
| strain-qc | bio-pathogens | 1 | 0 | none |
| fig-ideation | bio-redac | 15 | 0 | none |
| documentation | ops | 1 | 0 | none |
