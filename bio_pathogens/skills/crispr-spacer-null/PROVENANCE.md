# Provenance

- Origine locale : harnais generalise depuis le dossier de recherche `SpacerEgalVirus`.
- Base methodologique : permutations d'Altschul-Erickson generalisees, diagnostic BEST, controles genomiques GC-apparies, BLASTN observe versus nul, et k-mers partiels.
- Code importe : `scripts/crispr_spacer_null.py` est une extraction locale originale du harnais de recherche, sans dependance externe embarquee.

Garde-fou : un alignement court CRISPR/protospacer ne se lit jamais seul. Rapporter le modele nul, le ratio observe/nul, le p empirique et la degenerescence du nul si `k >= 3`.
