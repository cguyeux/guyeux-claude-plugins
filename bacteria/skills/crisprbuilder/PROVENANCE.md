# Provenance

- Origine scientifique : CRISPRbuilder-TB, Guyeux 2021, PLOS Computational Biology, depot `https://github.com/cguyeux/CRISPRbuilder-TB`.
- Code dans ce plugin : `scripts/crisprbuilder2.py` est une evolution locale originale qui retire la dependance au catalogue fixe de motifs MTBC et ajoute la detection de novo.
- Donnee embarquee : `data/dr_genres_ev4.tsv`, catalogue local derive de CRISPRCasdb evidence 4, utilise comme garde-fou de QC par genre.
- Source de la donnee : copie locale CRISPRCasdb arretee au 6 avril 2022, reconstruisible via le skill `crisprcasdb`.

Politique de droits : la table `dr_genres_ev4.tsv` est un artefact local de recherche destine a l'usage interne du plugin. Avant redistribution publique, verifier les conditions applicables au dump CRISPRCasdb source.

Garde-fou : un `status: no_dr_found` sur assemblage ne prouve pas l'absence de CRISPR. Les reads restent la voie fiable quand le locus repetitif a pu etre efface par l'assembleur.
