# Provenance

- Source externe consultee : NCBI E-utilities, bases `sra` et `bioproject`.
- Code importe : aucun client tiers ; `scripts/scout_bioprojects.py` est un script local stdlib, derive des motifs utilises dans `global_supplementary/bioproject_geo/sweep_bioprojects.py`.
- Donnees produites : listes de BioProjects et accessions candidates, a recouper avec TBannotator avant toute ingestion.

Garde-fou : un pays ou un mot-cle de resistance extrait d'un titre BioProject est un signal documentaire grossier. Il ne doit pas devenir une affirmation biologique sans verification post-ingestion.
