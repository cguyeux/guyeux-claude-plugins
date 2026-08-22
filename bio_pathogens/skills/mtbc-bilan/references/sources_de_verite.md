# Sources de verite taxonomiques -- texte integral

Reference de `mtbc-bilan` : bloc integral du prealable "Consultation memoire".
Le SKILL.md en porte une version condensee ; on lit ici la formulation
complete, avec le detail de ce qui fait autorite et de ce qui ne le fait pas.

## Prealable -- Consultation memoire

**Avant toute action** :

1. Consulter le skill `mtbc-lineages` pour la golden law sur les lignees
   MTBC (hierarchie Guyeux, biais de reference H37Rv). Degrader gracieusement
   si ce skill est indisponible -- le bilan reste possible, seule la
   validation golden law est affaiblie.

   > **Source de verite -- LISTE et EFFECTIFS des lignees** (cf.
   > `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`) : pour la
   > liste des lignees existantes et le nombre de souches par lignee, la
   > reference autoritative est **`bdd/actuelle/`** (les repertoires de
   > souches font foi), avec **`barcoding_v2/barcode_complete.tsv`** comme
   > registre derive. Ne PAS lire la "golden law" `lignees.py` comme source
   > des effectifs : elle peut etre desynchronisee de la taxonomie vivante
   > (snapshot en retard sur les cycles de subdivision recents). De meme,
   > `snp_barcoding.csv` (v1 obsolete) et `strain_lineages.csv` (perime)
   > ne sont jamais des references taxonomiques.
   >
   > **Source de verite (cf. `global_supplementary/barcoding_v2/SOURCES_OF_TRUTH.md`)** : dans TBannotator, `system='Senelle'` EST le systeme maison (= moi/Guyeux), mais c'est un **snapshot** susceptible d'etre en retard sur la taxonomie vivante. Pour tout clade recent du cycle multi-signal (L1.\*, Bovis1.\*, BCG.\*, L6 profond), recouper le label avec `bdd/actuelle/` + `barcoding_v2/barcode_complete.tsv`. Ne jamais lire `snp_barcoding.csv` (v1 obsolete) ni `strain_lineages.csv` (perime) comme reference taxonomique.

2. Si une `~/.claude/knowledge/tuberculosis.md` existe, la consulter pour
   les apprentissages transverses.
3. Lire `codes/mtbc/CLAUDE.md` pour les conventions globales du depot (le
   descriptif du depot : inventaire des repertoires, structure standard d'un
   projet, `bdd/`, skills, est dans `codes/mtbc/README.md` depuis le 2026-08-09).

