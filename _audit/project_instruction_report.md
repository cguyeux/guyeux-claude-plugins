# Couverture des instructions projet Claude vers Codex

Rapport deterministe de CCX-03. Les signaux d'activite servent au triage
et ne ferment ni n'archivent automatiquement aucun projet.

## Resume

- Racine auditee : `/home/christophe/docs/codes`
- Budget par fichier : 32768 octets
- `CLAUDE.md` bruts decouverts : 300
- Instructions de projets retenues : 259
- Copies internes ou dependances exclues : 41
- Avec `AGENTS.md` local : 18
- Avec `AGENTS.override.md` local : 6
- Fallback seul : 241
- `CLAUDE.md` au-dessus du budget : 4
- Fallback seul au-dessus du budget : 0
- Chaines d'instructions au-dessus du budget : 0

## Classes de triage

| Classe | Nombre | Portee |
|---|---:|---|
| `agents-local` | 18 | Couche Codex locale presente |
| `instruction-chain-over-budget` | 0 | Remediation prioritaire |
| `fallback-active-signal` | 87 | Travail ouvert explicitement signale |
| `fallback-archive-signal` | 23 | Chemin d'archive, a confirmer |
| `fallback-review-required` | 131 | Activite indeterminee, decision humaine |

## Inventaire complet

| Projet | CLAUDE | Chaine | AGENTS | Registres | Signaux ouverts | Dernier document | Classe |
|---|---:|---:|:---:|---|---|---|---|
| `.` | 14600 | 14600 | non | pistes.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `admin/gis` | 8229 | 8229 | non | cahier_de_labo.md, pistes.md | pistes.md | 2026-09-15 | `fallback-active-signal` |
| `admin/labcom` | 1388 | 1388 | non | - | - | 2026-09-13 | `fallback-review-required` |
| `archives/mic_watcher` | 1683 | 1683 | non | - | - | 2026-09-13 | `fallback-archive-signal` |
| `archives/old/Michaël` | 9161 | 9161 | non | - | - | 2026-07-29 | `fallback-archive-signal` |
| `autre/pomologie` | 16156 | 16156 | non | - | - | 2026-04-05 | `fallback-review-required` |
| `bio/bi-clustering` | 12616 | 12616 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `bio/deciphering-tuberculosis-with-ai` | 2119 | 2119 | non | - | - | 2026-09-13 | `fallback-review-required` |
| `bio/isfinder_ng` | 7395 | 7395 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-09 | `fallback-active-signal` |
| `bio/mabossDemo` | 12366 | 5830 | oui | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-07-21 | `agents-local` |
| `cours/chatkit` | 1987 | 1987 | non | cahier_de_labo.md | - | 2026-09-15 | `fallback-review-required` |
| `droit-shs/cours_camille` | 5266 | 5266 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `droit-shs/decheance-le-pen` | 5106 | 5106 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `droit-shs/lepoutre` | 22808 | 9899 | oui | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-16 | `agents-local` |
| `droit-shs/lineaire_a` | 240113 | 1569 | oui | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-14 | `agents-local` |
| `droit-shs/mnhn-musee-homme-ia-multimodale` | 1624 | 2840 | oui | cahier_de_labo.md, pistes.md, JOURNAL.md | - | 2026-09-13 | `agents-local` |
| `droit-shs/oxyrhynque-papyrologie-ia` | 1687 | 1009 | oui | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-15 | `agents-local` |
| `droit-shs/rohonczi` | 23167 | 1043 | oui | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-15 | `agents-local` |
| `droit-shs/voynich` | 7795 | 1497 | oui | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-15 | `agents-local` |
| `ia/langchain` | 3120 | 3120 | non | cahier_de_labo.md | - | 2026-05-10 | `fallback-review-required` |
| `ia/sad` | 1461 | 1461 | non | - | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/Borstel` | 11109 | 11109 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Bovis_emergence` | 21665 | 21665 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-15 | `fallback-active-signal` |
| `mtbc/Bovis_full` | 21565 | 21565 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-16 | `fallback-active-signal` |
| `mtbc/Bovis_full/sandbox_p53_af1/investigate_phylo` | 4393 | 4393 | non | cahier_de_labo.md | - | 2026-08-10 | `fallback-review-required` |
| `mtbc/Bovis_full/sandbox_p53_af1/lineage_navigator` | 94171 | 1924 | oui | cahier_de_labo.md, pistes.md | pistes.md | 2026-09-15 | `agents-local` |
| `mtbc/Bovis_proto` | 4416 | 4416 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Bovis_slaughter_bottleneck` | 8485 | 8485 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc` | 9639 | 9639 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-15 | `fallback-active-signal` |
| `mtbc/Canettii` | 2287 | 2287 | non | cahier_de_labo.md | - | 2026-08-10 | `fallback-review-required` |
| `mtbc/Cap-Vert` | 8557 | 8557 | non | cahier_de_labo.md | - | 2026-04-28 | `fallback-review-required` |
| `mtbc/Caprae` | 5133 | 5133 | non | cahier_de_labo.md, pistes.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Kazakhstan` | 3292 | 3292 | non | cahier_de_labo.md | - | 2026-06-04 | `fallback-review-required` |
| `mtbc/L1-Brazil_Mozambique-triangular_slave_trade` | 4179 | 4179 | non | cahier_de_labo.md | - | 2026-07-22 | `fallback-review-required` |
| `mtbc/L1-phylogenie` | 3807 | 3807 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/L1-radiations-eclair` | 3871 | 3871 | non | cahier_de_labo.md, JOURNAL.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/L1-voie_maritime_ocean_indien` | 4366 | 4366 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/L10` | 2852 | 2852 | non | cahier_de_labo.md | - | 2026-08-10 | `fallback-review-required` |
| `mtbc/L1_manila_galleon` | 1365 | 1365 | non | cahier_de_labo.md | - | 2026-06-04 | `fallback-review-required` |
| `mtbc/L2.2_cand_beijing` | 3198 | 3198 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/L2_cand_korea` | 2638 | 2638 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/L3` | 4487 | 4487 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/L3_cand_intl` | 2598 | 2598 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/L3_cand_tanzania` | 3047 | 3047 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/L4-Madagascar_Brazil-reciprocal_slave_trade` | 4099 | 4099 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/L4-orbis-empire_romain` | 8090 | 8090 | non | cahier_de_labo.md | - | 2026-05-17 | `fallback-review-required` |
| `mtbc/L4.10` | 12928 | 12928 | non | cahier_de_labo.md | - | 2026-05-30 | `fallback-review-required` |
| `mtbc/L4.11` | 5261 | 5261 | non | cahier_de_labo.md | - | 2026-08-31 | `fallback-review-required` |
| `mtbc/L4.12` | 2542 | 2542 | non | cahier_de_labo.md | - | 2026-06-06 | `fallback-review-required` |
| `mtbc/L4.13` | 6875 | 6875 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/L4.14` | 4383 | 4383 | non | cahier_de_labo.md | - | 2026-05-15 | `fallback-review-required` |
| `mtbc/L4.15` | 2672 | 2672 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/L4.17` | 9111 | 9111 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/L4.2_proto` | 6444 | 6444 | non | cahier_de_labo.md | - | 2026-09-07 | `fallback-review-required` |
| `mtbc/L4.3_phylogenie` | 4135 | 4135 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/L4.6.2_Cameroun` | 16483 | 16483 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/L4.8` | 6843 | 6843 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/L4.9` | 4309 | 4309 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/L46-LAM10Cam-trans_atlantic` | 6053 | 6053 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/L4_cand_clade6` | 3782 | 3782 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/L4_cand_near_L4.5` | 2936 | 2936 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/L4_cand_paireB` | 3383 | 3383 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/L4_imbriquees` | 4842 | 4842 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/L5` | 2203 | 2203 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/L5L6-codivergence_ethnies_ouest_afrique` | 11948 | 11948 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-10 | `fallback-active-signal` |
| `mtbc/L5L6-codivergence_ethnies_ouest_afrique/archives/2026-07-07_siblings/multipathogen_control_maf_bovis_ulcerans` | 8155 | 8155 | non | cahier_de_labo.md | - | 2026-05-15 | `fallback-archive-signal` |
| `mtbc/L5L6-codivergence_ethnies_ouest_afrique/archives/2026-07-07_siblings/precolonial_states_molecular_archaeology` | 9741 | 9741 | non | cahier_de_labo.md | - | 2026-05-15 | `fallback-archive-signal` |
| `mtbc/L5L6-codivergence_ethnies_ouest_afrique/archives/2026-07-07_siblings/subnational_resolution_maf_codivergence` | 10500 | 10500 | non | cahier_de_labo.md | - | 2026-05-16 | `fallback-archive-signal` |
| `mtbc/L5L6-codivergence_ethnies_ouest_afrique/archives/2026-07-07_siblings/ultrafine_ethnolinguistic_sublineage_codivergence` | 8849 | 8849 | non | cahier_de_labo.md | - | 2026-05-16 | `fallback-archive-signal` |
| `mtbc/L5L6-dating_polity_dynamics` | 6817 | 6817 | non | cahier_de_labo.md | - | 2026-08-31 | `fallback-review-required` |
| `mtbc/L7L9-codivergence_ethnies_afrique_est` | 15937 | 15937 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/L8` | 11526 | 11526 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/L9` | 2853 | 2853 | non | cahier_de_labo.md, pistes.md | pistes.md | 2026-08-10 | `fallback-active-signal` |
| `mtbc/LChimpanze` | 1091 | 1091 | non | cahier_de_labo.md | - | 2026-08-31 | `fallback-review-required` |
| `mtbc/LDassie` | 2228 | 2228 | non | cahier_de_labo.md | - | 2026-08-10 | `fallback-review-required` |
| `mtbc/LMungi` | 2393 | 2393 | non | cahier_de_labo.md | - | 2026-08-10 | `fallback-review-required` |
| `mtbc/LSuricattae` | 2181 | 2181 | non | cahier_de_labo.md | - | 2026-08-10 | `fallback-review-required` |
| `mtbc/La4` | 3597 | 3597 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/La4-phylogenie` | 6458 | 6458 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Liban` | 6036 | 6036 | non | cahier_de_labo.md | - | 2026-09-06 | `fallback-review-required` |
| `mtbc/Lignées` | 1875 | 1875 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `mtbc/MKC_sp_identification` | 1645 | 1645 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/MTBC-constrained-node-dating` | 5329 | 5329 | non | cahier_de_labo.md, JOURNAL.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/MTBC-roman-expansion-skyline` | 11127 | 11127 | non | cahier_de_labo.md | - | 2026-06-26 | `fallback-review-required` |
| `mtbc/MTBC_enteric_relics` | 7583 | 7583 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Maf_establishment_barrier` | 3749 | 3749 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/NTM_unidentified` | 9476 | 9476 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-08 | `fallback-active-signal` |
| `mtbc/Oman` | 5217 | 5217 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Resistance_antibio` | 21588 | 21588 | non | cahier_de_labo.md | - | 2026-09-08 | `fallback-review-required` |
| `mtbc/Rv0057` | 1539 | 1539 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv0236A` | 1584 | 1584 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv0549c` | 4099 | 4099 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv0877` | 1592 | 1592 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv0979c` | 1542 | 1542 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv1557` | 3557 | 3557 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv1825` | 4433 | 4433 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-15 | `fallback-active-signal` |
| `mtbc/Rv1831` | 1539 | 1539 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv2516c` | 7777 | 7777 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-08 | `fallback-active-signal` |
| `mtbc/Rv2520c` | 3284 | 3284 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv2541` | 1539 | 1539 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv2548A` | 1589 | 1589 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv2566` | 5749 | 5749 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv2569c` | 6452 | 6452 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-15 | `fallback-active-signal` |
| `mtbc/Rv2660c` | 1585 | 1585 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv2698` | 1547 | 1547 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv2699c` | 1577 | 1577 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv2892c` | 5281 | 5281 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-15 | `fallback-active-signal` |
| `mtbc/Rv2901c` | 1566 | 1566 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv3165c` | 1596 | 1596 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv3190c` | 1576 | 1576 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv3258c` | 1550 | 1550 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv3355c` | 1551 | 1551 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv3566A` | 1528 | 1528 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv3604c` | 1550 | 1550 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv3656c` | 1596 | 1596 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/Rv3896c-Rv3898c` | 18258 | 18258 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-15 | `fallback-active-signal` |
| `mtbc/Rv3909` | 4137 | 4137 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/SpacerEgalVirus` | 3391 | 3391 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-16 | `fallback-active-signal` |
| `mtbc/TYK2-MTBC-coevolution` | 8910 | 8910 | non | cahier_de_labo.md, pistes.md | pistes.md | 2026-09-15 | `fallback-active-signal` |
| `mtbc/a_ranger_phylo` | 1392 | 1392 | non | cahier_de_labo.md, etat_des_decouvertes.md, JOURNAL.md | - | 2026-09-14 | `fallback-review-required` |
| `mtbc/abandonne/clustering_sola` | 9841 | 9841 | non | cahier_de_labo.md, pistes.md | pistes.md | 2026-08-17 | `fallback-archive-signal` |
| `mtbc/ancient_pathogens_tracer_ranking` | 4260 | 4260 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/animal_vs_human` | 4227 | 4227 | non | cahier_de_labo.md | - | 2026-09-09 | `fallback-review-required` |
| `mtbc/annotation_mtbc` | 9327 | 9327 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-16 | `fallback-active-signal` |
| `mtbc/archeo_crispr` | 3720 | 3720 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-05 | `fallback-active-signal` |
| `mtbc/atlas_mtbc` | 11307 | 11307 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-07-30 | `fallback-active-signal` |
| `mtbc/bdd` | 13169 | 13169 | non | - | - | 2026-09-07 | `fallback-review-required` |
| `mtbc/canettii_mtbc_emergence` | 6784 | 6784 | non | cahier_de_labo.md, JOURNAL.md | - | 2026-06-26 | `fallback-review-required` |
| `mtbc/citation_gap_mtbc` | 1581 | 1581 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-15 | `fallback-active-signal` |
| `mtbc/coclustering_lineages` | 1512 | 1512 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/complex_datation` | 15344 | 15344 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/consensus_coverage_bias` | 5499 | 5499 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/conserved_orphan_modules` | 5274 | 5274 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-14 | `fallback-active-signal` |
| `mtbc/crispr_extinction_is6110` | 7587 | 7587 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/crisprcasdb_local` | 1776 | 1776 | non | cahier_de_labo.md, etat_des_decouvertes.md | - | 2026-09-14 | `fallback-review-required` |
| `mtbc/dassie_suricattae` | 13964 | 13964 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/data-quality` | 3580 | 3580 | non | cahier_de_labo.md, pistes.md | pistes.md | 2026-09-07 | `fallback-active-signal` |
| `mtbc/duf501_eukaryotic` | 2787 | 2787 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/fini/Rv0810c` | 8082 | 8082 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-15 | `fallback-archive-signal` |
| `mtbc/fini/Rv1025` | 3648 | 3648 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-archive-signal` |
| `mtbc/fini/Rv1125` | 9186 | 9186 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-archive-signal` |
| `mtbc/fini/Rv2438A` | 6978 | 1880 | oui | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-16 | `agents-local` |
| `mtbc/fini/Rv3222c` | 21870 | 21870 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-09 | `fallback-archive-signal` |
| `mtbc/fini/bpal_resistance_emergence` | 4661 | 4661 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-13 | `fallback-archive-signal` |
| `mtbc/fini/dark_enzymes` | 11393 | 11393 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-09 | `fallback-archive-signal` |
| `mtbc/gene_decay_census` | 7309 | 7309 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/global_supplementary` | 4004 | 4004 | non | cahier_de_labo.md, etat_des_decouvertes.md | - | 2026-09-14 | `fallback-review-required` |
| `mtbc/h37Rv` | 2705 | 2705 | non | cahier_de_labo.md, etat_des_decouvertes.md | - | 2026-09-14 | `fallback-review-required` |
| `mtbc/holdout_benchmark` | 5250 | 5250 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/investigate_phylo` | 4393 | 4393 | non | cahier_de_labo.md | - | 2026-08-10 | `fallback-review-required` |
| `mtbc/lineage_markers_who_catalogue` | 3835 | 3835 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/lineage_navigator` | 94171 | 1924 | oui | cahier_de_labo.md, pistes.md | pistes.md | 2026-09-15 | `agents-local` |
| `mtbc/lineage_subdivision_methods` | 1616 | 1616 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/methodology` | 2177 | 2177 | non | cahier_de_labo.md, JOURNAL.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/mixed_clade_synapomorphies` | 4339 | 4339 | non | cahier_de_labo.md, JOURNAL.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/mixed_infections_multimarker` | 5047 | 5047 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/mleprae_atlas` | 3159 | 3159 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/molecular_clock` | 4474 | 4474 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/mtbc0_reconstruction` | 3124 | 3124 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/nucs_deletion_mutators` | 4943 | 4943 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/orygis-phylogenie` | 9504 | 9504 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/orygis-phylogenie/archive/orygis_zoonotic` | 6155 | 6155 | non | cahier_de_labo.md | - | 2026-06-06 | `fallback-archive-signal` |
| `mtbc/outils` | 1487 | 1487 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `mtbc/ponA_microsatellite` | 7478 | 7478 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/projets_abandonnes/A la recherche de nouvelles lignees` | 10649 | 10649 | non | cahier_de_labo.md | - | 2026-06-09 | `fallback-archive-signal` |
| `mtbc/projets_abandonnes/Bovis_RDs` | 6924 | 6924 | non | cahier_de_labo.md | - | 2026-06-12 | `fallback-archive-signal` |
| `mtbc/projets_abandonnes/Mycobacterium_divergent_cluster3` | 4791 | 4791 | non | cahier_de_labo.md, JOURNAL.md | - | 2026-09-13 | `fallback-archive-signal` |
| `mtbc/projets_abandonnes/Mycobacterium_sp_novel` | 7676 | 7676 | non | cahier_de_labo.md, JOURNAL.md | - | 2026-09-13 | `fallback-archive-signal` |
| `mtbc/projets_abandonnes/Still unknown gene function` | 12798 | 12798 | non | cahier_de_labo.md | - | 2026-06-13 | `fallback-archive-signal` |
| `mtbc/projets_abandonnes/TA_persistence` | 3221 | 3221 | non | cahier_de_labo.md, JOURNAL.md | - | 2026-09-13 | `fallback-archive-signal` |
| `mtbc/projets_abandonnes/TA_repertoire` | 4766 | 4766 | non | cahier_de_labo.md, JOURNAL.md | - | 2026-06-09 | `fallback-archive-signal` |
| `mtbc/projets_abandonnes/diversifying_antigens` | 7964 | 7964 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-archive-signal` |
| `mtbc/projets_abandonnes/musee_de_lhomme` | 1911 | 1911 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-08-12 | `fallback-archive-signal` |
| `mtbc/projets_clos_non_soumis/GC_par_lignee` | 3382 | 3382 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/projets_clos_non_soumis/Rv0007` | 2777 | 2777 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/projets_clos_non_soumis/Rv0537c` | 5592 | 5592 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-16 | `fallback-active-signal` |
| `mtbc/projets_clos_non_soumis/Rv2628` | 1588 | 1588 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-15 | `fallback-active-signal` |
| `mtbc/rehumanisation_L6L9L10` | 9767 | 9767 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-15 | `fallback-active-signal` |
| `mtbc/snp_barcoding` | 1090 | 1090 | non | cahier_de_labo.md | - | 2026-05-15 | `fallback-review-required` |
| `mtbc/spoligo_clock` | 5780 | 5780 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/structural_variation_is_rd` | 2901 | 2901 | non | cahier_de_labo.md | - | 2026-09-13 | `fallback-review-required` |
| `mtbc/tbannotator_local` | 1744 | 1744 | non | cahier_de_labo.md, etat_des_decouvertes.md | - | 2026-09-14 | `fallback-review-required` |
| `mtbc/tissue_tropism_mtbc` | 9922 | 9922 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/variant_nucs` | 6009 | 6009 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/yersinia_atlas` | 4507 | 4507 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `mtbc/yersinia_pestis_grands_lacs` | 7438 | 7438 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-08-17 | `fallback-active-signal` |
| `mtbc/yersiniomics` | 4695 | 4695 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-13 | `fallback-active-signal` |
| `outillage/claude-code` | 1691 | 1691 | non | cahier_de_labo.md | - | 2026-05-12 | `fallback-review-required` |
| `outillage/micwatch` | 2630 | 2630 | non | - | - | 2026-09-13 | `fallback-review-required` |
| `outillage/veille_llm` | 9697 | 31783 | oui | cahier_de_labo.md | - | 2026-08-09 | `agents-local` |
| `pompiers/airgos` | 16192 | 16192 | non | cahier_de_labo.md | - | 2026-09-14 | `fallback-review-required` |
| `pompiers/airgos/dashboard` | 11 | 16519 | oui | - | - | 2026-06-08 | `agents-local` |
| `pompiers/ars` | 16379 | 993 | oui | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-15 | `agents-local` |
| `pompiers/doctrinops` | 3234 | 927 | oui | cahier_de_labo.md | - | 2026-09-09 | `agents-local` |
| `pompiers/hydroreel` | 1464 | 1464 | non | - | - | 2026-09-13 | `fallback-review-required` |
| `pompiers/iappels` | 11242 | 11242 | non | cahier_de_labo.md | - | 2026-09-04 | `fallback-review-required` |
| `pompiers/iappels/adversarial-conversational-emergency-ai` | 2969 | 14211 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `pompiers/iappels/asr-benchmark-uncertainty-emergency` | 2956 | 14198 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `pompiers/iappels/automation-bias-hitl-ux-triage` | 2963 | 14205 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `pompiers/iappels/conformal-uncertainty-critical-nlp` | 2962 | 14204 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `pompiers/iappels/data-barriers-perspectives-emergency` | 2971 | 14213 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `pompiers/iappels/docs/articles/two-way-pipeline` | 12033 | 23275 | non | JOURNAL.md | - | 2026-08-11 | `fallback-review-required` |
| `pompiers/iappels/genai-use-cases-emergency` | 2953 | 14195 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `pompiers/iappels/legal-aiact-compliance-emergency` | 2999 | 14241 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `pompiers/iappels/linguistic-acoustic-specificities` | 2975 | 14217 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `pompiers/iappels/multilingual-mt-codeswitching-emergency` | 2953 | 14195 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `pompiers/iappels/open-emergency-corpora-deidentification` | 2988 | 14230 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `pompiers/iappels/prosody-affect-stress-triage` | 2960 | 14202 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `pompiers/iappels/resilience-graceful-degradation` | 2967 | 14209 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `pompiers/iappels/robust-asr-degraded-conditions` | 2939 | 14181 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `pompiers/iappels/safety-driven-mlops-emergency` | 2954 | 14196 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `pompiers/iappels/sfep-false-green-evaluation` | 2969 | 14211 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `pompiers/iappels/sociolinguistic-bias-equity-asr` | 2931 | 14173 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `pompiers/iappels/survey-genai-emergency-calls` | 2946 | 14188 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `pompiers/optimops` | 73136 | 2704 | oui | cahier_de_labo.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-15 | `agents-local` |
| `pompiers/pompiers_croyances` | 14702 | 14702 | non | cahier_de_labo.md | - | 2026-06-16 | `fallback-review-required` |
| `pompiers/predictops` | 5101 | 1044 | oui | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-09-15 | `agents-local` |
| `pompiers/predictops-mcp/.worktrees/master-release/example_prompts` | 10524 | 20804 | non | - | - | 2026-08-07 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/master-release/external_mcps/static_plotting_mcp` | 947 | 11227 | non | - | - | 2026-08-07 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/master-release/mymcps` | 10410 | 20690 | non | - | - | 2026-08-07 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p1-16-atmo-dedup/example_prompts` | 10524 | 19293 | non | - | - | 2026-08-14 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p1-16-atmo-dedup/external_mcps/static_plotting_mcp` | 947 | 9716 | non | - | - | 2026-08-14 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p1-16-atmo-dedup/mymcps` | 10410 | 19179 | non | - | - | 2026-08-14 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p25-register/example_prompts` | 10524 | 10524 | non | - | - | 2026-08-06 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p25-register/external_mcps/static_plotting_mcp` | 947 | 947 | non | - | - | 2026-08-06 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p25-register/mymcps` | 10410 | 10410 | non | - | - | 2026-08-06 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p4-3-caddy-loopback/example_prompts` | 10524 | 15996 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p4-3-caddy-loopback/external_mcps/static_plotting_mcp` | 947 | 6419 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p4-3-caddy-loopback/mymcps` | 10410 | 15882 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-12-pluies-intenses/example_prompts` | 10524 | 13219 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-12-pluies-intenses/external_mcps/static_plotting_mcp` | 947 | 3642 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-12-pluies-intenses/mymcps` | 10410 | 13105 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-13-fiabilite-predictops/example_prompts` | 10524 | 14636 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-13-fiabilite-predictops/external_mcps/static_plotting_mcp` | 947 | 5059 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-13-fiabilite-predictops/mymcps` | 10410 | 14522 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-14-observations-meteofrance/example_prompts` | 10524 | 14778 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-14-observations-meteofrance/external_mcps/static_plotting_mcp` | 947 | 5201 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-14-observations-meteofrance/mymcps` | 10410 | 14664 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-15-sante-meteo/example_prompts` | 10524 | 15525 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-15-sante-meteo/external_mcps/static_plotting_mcp` | 947 | 5948 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-15-sante-meteo/mymcps` | 10410 | 15411 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-16-prise-garde/example_prompts` | 10524 | 16649 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-16-prise-garde/external_mcps/static_plotting_mcp` | 947 | 7072 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-16-prise-garde/mymcps` | 10410 | 16535 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-17-calls-quality-audit/example_prompts` | 10524 | 17410 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-17-calls-quality-audit/external_mcps/static_plotting_mcp` | 947 | 7833 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-17-calls-quality-audit/mymcps` | 10410 | 17296 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-18-supervision/example_prompts` | 10524 | 17410 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-18-supervision/external_mcps/static_plotting_mcp` | 947 | 7833 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-18-supervision/mymcps` | 10410 | 17296 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-19-legifrance-doctrine/example_prompts` | 10524 | 18260 | non | - | - | 2026-08-13 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-19-legifrance-doctrine/external_mcps/static_plotting_mcp` | 947 | 8683 | non | - | - | 2026-08-13 | `fallback-review-required` |
| `pompiers/predictops-mcp/.worktrees/p8-19-legifrance-doctrine/mymcps` | 10410 | 18146 | non | - | - | 2026-08-13 | `fallback-review-required` |
| `pompiers/predictops-mcp` | 20860 | 10280 | oui | cahier_de_labo.md, pistes.md, JOURNAL.md | pistes.md | 2026-09-15 | `agents-local` |
| `pompiers/predictops-mcp/example_prompts` | 10524 | 20804 | non | - | - | 2026-06-16 | `fallback-review-required` |
| `pompiers/predictops-mcp/external_mcps/static_plotting_mcp` | 947 | 11227 | non | - | - | 2026-06-16 | `fallback-review-required` |
| `pompiers/predictops-mcp/mymcps` | 10410 | 20690 | non | - | - | 2026-06-16 | `fallback-review-required` |
| `pompiers/predictops-monitor` | 1632 | 1632 | non | - | - | 2026-09-13 | `fallback-review-required` |
| `pompiers/regulation-grounded-completeness-agent` | 18949 | 1629 | oui | - | - | 2026-09-04 | `agents-local` |

## Exclusions de perimetre

Les chemins sous `.claude`, `.codex`, `.agents`, environnements Python,
`node_modules` et caches Python sont comptes dans le total brut mais ne
sont jamais traites comme des projets. La liste exacte et la raison de
chaque exclusion sont conservees dans le rapport JSON.

## Regle de decision

Un signal ouvert provient uniquement d'une case Markdown non cochee ou
d'un statut explicite dans `pistes.md` ou `TASKS.md`. Une date recente,
la presence d'un depot Git ou un nom de domaine ne suffisent jamais a
declarer un projet actif. Les lignes `fallback-review-required` exigent
donc un arbitrage humain ou une preuve dans le registre du projet.
