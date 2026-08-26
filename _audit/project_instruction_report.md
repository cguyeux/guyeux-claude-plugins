# Couverture des instructions projet Claude vers Codex

Rapport deterministe de CCX-03. Les signaux d'activite servent au triage
et ne ferment ni n'archivent automatiquement aucun projet.

## Resume

- Racine auditee : `/home/christophe/docs/codes`
- Budget par fichier : 32768 octets
- `CLAUDE.md` bruts decouverts : 266
- Instructions de projets retenues : 233
- Copies internes ou dependances exclues : 33
- Avec `AGENTS.md` local : 18
- Avec `AGENTS.override.md` local : 6
- Fallback seul : 215
- `CLAUDE.md` au-dessus du budget : 3
- Fallback seul au-dessus du budget : 0
- Chaines d'instructions au-dessus du budget : 0

## Classes de triage

| Classe | Nombre | Portee |
|---|---:|---|
| `agents-local` | 18 | Couche Codex locale presente |
| `instruction-chain-over-budget` | 0 | Remediation prioritaire |
| `fallback-active-signal` | 65 | Travail ouvert explicitement signale |
| `fallback-archive-signal` | 19 | Chemin d'archive, a confirmer |
| `fallback-review-required` | 131 | Activite indeterminee, decision humaine |

## Inventaire complet

| Projet | CLAUDE | Chaine | AGENTS | Registres | Signaux ouverts | Dernier document | Classe |
|---|---:|---:|:---:|---|---|---|---|
| `airgos` | 16192 | 16192 | non | cahier_de_labo.md | - | 2026-08-21 | `fallback-review-required` |
| `airgos/dashboard` | 11 | 16519 | oui | - | - | 2026-06-08 | `agents-local` |
| `ars` | 16379 | 993 | oui | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-25 | `agents-local` |
| `bi-clustering` | 12616 | 12616 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `claude-code` | 1691 | 1691 | non | cahier_de_labo.md | - | 2026-05-12 | `fallback-review-required` |
| `claude_plugins` | 19871 | 19871 | non | - | - | 2026-08-22 | `fallback-review-required` |
| `claude_plugins/_audit/fixtures/parity/project with spaces` | 316 | 20184 | oui | - | - | 2026-08-26 | `agents-local` |
| `decheance-le-pen` | 6330 | 6330 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-08 | `fallback-active-signal` |
| `doctrinops` | 3234 | 927 | oui | cahier_de_labo.md | - | 2026-07-01 | `agents-local` |
| `gis` | 5202 | 5202 | non | cahier_de_labo.md, pistes.md | pistes.md | 2026-08-26 | `fallback-active-signal` |
| `iappels` | 11242 | 11242 | non | cahier_de_labo.md | - | 2026-08-16 | `fallback-review-required` |
| `iappels/adversarial-conversational-emergency-ai` | 2969 | 14211 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `iappels/asr-benchmark-uncertainty-emergency` | 2956 | 14198 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `iappels/automation-bias-hitl-ux-triage` | 2963 | 14205 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `iappels/conformal-uncertainty-critical-nlp` | 2962 | 14204 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `iappels/data-barriers-perspectives-emergency` | 2971 | 14213 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `iappels/docs/articles/two-way-pipeline` | 12033 | 23275 | non | JOURNAL.md | - | 2026-08-11 | `fallback-review-required` |
| `iappels/genai-use-cases-emergency` | 2953 | 14195 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `iappels/legal-aiact-compliance-emergency` | 2999 | 14241 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `iappels/linguistic-acoustic-specificities` | 2975 | 14217 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `iappels/multilingual-mt-codeswitching-emergency` | 2953 | 14195 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `iappels/open-emergency-corpora-deidentification` | 2988 | 14230 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `iappels/prosody-affect-stress-triage` | 2960 | 14202 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `iappels/regulation-grounded-completeness-agent` | 10163 | 12791 | oui | - | - | 2026-08-16 | `agents-local` |
| `iappels/resilience-graceful-degradation` | 2967 | 14209 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `iappels/robust-asr-degraded-conditions` | 2939 | 14181 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `iappels/safety-driven-mlops-emergency` | 2954 | 14196 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `iappels/sfep-false-green-evaluation` | 2969 | 14211 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `iappels/sociolinguistic-bias-equity-asr` | 2931 | 14173 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `iappels/survey-genai-emergency-calls` | 2946 | 14188 | non | - | - | 2026-04-30 | `fallback-review-required` |
| `isfinder_ng` | 7395 | 7395 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-09 | `fallback-active-signal` |
| `langchain` | 3120 | 3120 | non | cahier_de_labo.md | - | 2026-05-10 | `fallback-review-required` |
| `lepoutre` | 21707 | 9899 | oui | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-08-23 | `agents-local` |
| `lineaire_a` | 230827 | 1070 | oui | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-26 | `agents-local` |
| `mabossDemo` | 12366 | 5830 | oui | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-07-21 | `agents-local` |
| `mnhn-musee-homme-ia-multimodale` | 2848 | 2840 | oui | cahier_de_labo.md, pistes.md, JOURNAL.md | - | 2026-08-08 | `agents-local` |
| `mtbc/Borstel` | 11260 | 11260 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-07-07 | `fallback-active-signal` |
| `mtbc/Bovis_emergence` | 20241 | 20241 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-08-25 | `fallback-active-signal` |
| `mtbc/Bovis_full` | 12653 | 12653 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-17 | `fallback-active-signal` |
| `mtbc/Bovis_proto` | 5940 | 5940 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-07 | `fallback-active-signal` |
| `mtbc` | 8479 | 8479 | non | cahier_de_labo.md, pistes.md | pistes.md | 2026-08-25 | `fallback-active-signal` |
| `mtbc/Canettii` | 2287 | 2287 | non | cahier_de_labo.md | - | 2026-08-10 | `fallback-review-required` |
| `mtbc/Cap-Vert` | 8557 | 8557 | non | cahier_de_labo.md | - | 2026-04-28 | `fallback-review-required` |
| `mtbc/Caprae` | 5600 | 5600 | non | cahier_de_labo.md, pistes.md | pistes.md | 2026-07-02 | `fallback-active-signal` |
| `mtbc/Kazakhstan` | 3292 | 3292 | non | cahier_de_labo.md | - | 2026-06-04 | `fallback-review-required` |
| `mtbc/L1-Brazil_Mozambique-triangular_slave_trade` | 4179 | 4179 | non | cahier_de_labo.md | - | 2026-07-22 | `fallback-review-required` |
| `mtbc/L1-phylogenie` | 4542 | 4542 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-07-01 | `fallback-active-signal` |
| `mtbc/L1-radiations-eclair` | 5395 | 5395 | non | cahier_de_labo.md, JOURNAL.md | - | 2026-06-04 | `fallback-review-required` |
| `mtbc/L1-voie_maritime_ocean_indien` | 4833 | 4833 | non | cahier_de_labo.md | - | 2026-06-09 | `fallback-review-required` |
| `mtbc/L10` | 2852 | 2852 | non | cahier_de_labo.md | - | 2026-08-10 | `fallback-review-required` |
| `mtbc/L1_manila_galleon` | 1365 | 1365 | non | cahier_de_labo.md | - | 2026-06-04 | `fallback-review-required` |
| `mtbc/L2.2_cand_beijing` | 3665 | 3665 | non | cahier_de_labo.md | - | 2026-06-09 | `fallback-review-required` |
| `mtbc/L2_cand_korea` | 3105 | 3105 | non | cahier_de_labo.md | - | 2026-06-09 | `fallback-review-required` |
| `mtbc/L3` | 4954 | 4954 | non | cahier_de_labo.md | - | 2026-04-28 | `fallback-review-required` |
| `mtbc/L3_cand_intl` | 3065 | 3065 | non | cahier_de_labo.md | - | 2026-08-12 | `fallback-review-required` |
| `mtbc/L3_cand_tanzania` | 3514 | 3514 | non | cahier_de_labo.md | - | 2026-08-12 | `fallback-review-required` |
| `mtbc/L4-Madagascar_Brazil-reciprocal_slave_trade` | 6274 | 6274 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-12 | `fallback-active-signal` |
| `mtbc/L4-orbis-empire_romain` | 8090 | 8090 | non | cahier_de_labo.md | - | 2026-05-17 | `fallback-review-required` |
| `mtbc/L4.10` | 12928 | 12928 | non | cahier_de_labo.md | - | 2026-05-30 | `fallback-review-required` |
| `mtbc/L4.11` | 5261 | 5261 | non | cahier_de_labo.md | - | 2026-05-15 | `fallback-review-required` |
| `mtbc/L4.12` | 2542 | 2542 | non | cahier_de_labo.md | - | 2026-06-06 | `fallback-review-required` |
| `mtbc/L4.13` | 6828 | 6828 | non | cahier_de_labo.md | - | 2026-06-03 | `fallback-review-required` |
| `mtbc/L4.14` | 4383 | 4383 | non | cahier_de_labo.md | - | 2026-05-15 | `fallback-review-required` |
| `mtbc/L4.15` | 2619 | 2619 | non | cahier_de_labo.md | - | 2026-07-05 | `fallback-review-required` |
| `mtbc/L4.17` | 9580 | 9580 | non | cahier_de_labo.md | - | 2026-04-28 | `fallback-review-required` |
| `mtbc/L4.2_proto` | 6444 | 6444 | non | cahier_de_labo.md | - | 2026-06-10 | `fallback-review-required` |
| `mtbc/L4.3_phylogenie` | 4602 | 4602 | non | cahier_de_labo.md | - | 2026-06-08 | `fallback-review-required` |
| `mtbc/L4.6.2_Cameroun` | 16436 | 16436 | non | cahier_de_labo.md | - | 2026-05-16 | `fallback-review-required` |
| `mtbc/L4.8` | 7310 | 7310 | non | cahier_de_labo.md | - | 2026-05-18 | `fallback-review-required` |
| `mtbc/L4.9` | 4256 | 4256 | non | cahier_de_labo.md | - | 2026-04-28 | `fallback-review-required` |
| `mtbc/L46-LAM10Cam-trans_atlantic` | 6520 | 6520 | non | cahier_de_labo.md | - | 2026-05-15 | `fallback-review-required` |
| `mtbc/L4_cand_clade6` | 4249 | 4249 | non | cahier_de_labo.md | - | 2026-06-09 | `fallback-review-required` |
| `mtbc/L4_cand_near_L4.5` | 3403 | 3403 | non | cahier_de_labo.md | - | 2026-06-09 | `fallback-review-required` |
| `mtbc/L4_cand_paireB` | 3588 | 3588 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-07-07 | `fallback-active-signal` |
| `mtbc/L4_imbriquees` | 5309 | 5309 | non | cahier_de_labo.md | - | 2026-04-28 | `fallback-review-required` |
| `mtbc/L5` | 2670 | 2670 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-08-19 | `fallback-active-signal` |
| `mtbc/L5L6-codivergence_ethnies_ouest_afrique` | 11298 | 11298 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-07-22 | `fallback-active-signal` |
| `mtbc/L5L6-codivergence_ethnies_ouest_afrique/archives/2026-07-07_siblings/multipathogen_control_maf_bovis_ulcerans` | 8155 | 8155 | non | cahier_de_labo.md | - | 2026-05-15 | `fallback-archive-signal` |
| `mtbc/L5L6-codivergence_ethnies_ouest_afrique/archives/2026-07-07_siblings/precolonial_states_molecular_archaeology` | 9741 | 9741 | non | cahier_de_labo.md | - | 2026-05-15 | `fallback-archive-signal` |
| `mtbc/L5L6-codivergence_ethnies_ouest_afrique/archives/2026-07-07_siblings/subnational_resolution_maf_codivergence` | 10500 | 10500 | non | cahier_de_labo.md | - | 2026-05-16 | `fallback-archive-signal` |
| `mtbc/L5L6-codivergence_ethnies_ouest_afrique/archives/2026-07-07_siblings/ultrafine_ethnolinguistic_sublineage_codivergence` | 8849 | 8849 | non | cahier_de_labo.md | - | 2026-05-16 | `fallback-archive-signal` |
| `mtbc/L5L6-dating_polity_dynamics` | 6817 | 6817 | non | cahier_de_labo.md | - | 2026-05-15 | `fallback-review-required` |
| `mtbc/L7L9-codivergence_ethnies_afrique_est` | 15890 | 15890 | non | cahier_de_labo.md | - | 2026-06-04 | `fallback-review-required` |
| `mtbc/L8` | 11526 | 11526 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-08-17 | `fallback-active-signal` |
| `mtbc/L9` | 2853 | 2853 | non | cahier_de_labo.md, pistes.md | pistes.md | 2026-08-10 | `fallback-active-signal` |
| `mtbc/LChimpanze` | 1091 | 1091 | non | cahier_de_labo.md | - | 2026-04-28 | `fallback-review-required` |
| `mtbc/LDassie` | 2228 | 2228 | non | cahier_de_labo.md | - | 2026-08-10 | `fallback-review-required` |
| `mtbc/LMungi` | 2393 | 2393 | non | cahier_de_labo.md | - | 2026-08-10 | `fallback-review-required` |
| `mtbc/LSuricattae` | 2181 | 2181 | non | cahier_de_labo.md | - | 2026-08-10 | `fallback-review-required` |
| `mtbc/La4` | 4332 | 4332 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-07-01 | `fallback-active-signal` |
| `mtbc/La4-phylogenie` | 8300 | 8300 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-17 | `fallback-active-signal` |
| `mtbc/Liban` | 6036 | 6036 | non | cahier_de_labo.md | - | 2026-06-09 | `fallback-review-required` |
| `mtbc/Lignées` | 1875 | 1875 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `mtbc/MKC_sp_identification` | 3820 | 3820 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-18 | `fallback-active-signal` |
| `mtbc/MTBC-constrained-node-dating` | 5353 | 5353 | non | cahier_de_labo.md, JOURNAL.md | - | 2026-06-08 | `fallback-review-required` |
| `mtbc/MTBC-roman-expansion-skyline` | 11127 | 11127 | non | cahier_de_labo.md | - | 2026-06-26 | `fallback-review-required` |
| `mtbc/NTM_unidentified` | 8957 | 8957 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-08-26 | `fallback-active-signal` |
| `mtbc/Oman` | 5438 | 5438 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-08-25 | `fallback-active-signal` |
| `mtbc/Resistance_antibio` | 21588 | 21588 | non | cahier_de_labo.md | - | 2026-06-16 | `fallback-review-required` |
| `mtbc/Rv0007` | 4952 | 4952 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-11 | `fallback-active-signal` |
| `mtbc/Rv0057` | 3714 | 3714 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-31 | `fallback-active-signal` |
| `mtbc/Rv0236A` | 3759 | 3759 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-31 | `fallback-active-signal` |
| `mtbc/Rv0877` | 3767 | 3767 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-31 | `fallback-active-signal` |
| `mtbc/Rv0979c` | 3717 | 3717 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-31 | `fallback-active-signal` |
| `mtbc/Rv1025` | 5432 | 5432 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-25 | `fallback-active-signal` |
| `mtbc/Rv1831` | 3714 | 3714 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-25 | `fallback-active-signal` |
| `mtbc/Rv2516c` | 7777 | 7777 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-17 | `fallback-active-signal` |
| `mtbc/Rv2520c` | 4778 | 4778 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-25 | `fallback-active-signal` |
| `mtbc/Rv2541` | 3714 | 3714 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-31 | `fallback-active-signal` |
| `mtbc/Rv2548A` | 3764 | 3764 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-31 | `fallback-active-signal` |
| `mtbc/Rv2628` | 3763 | 3763 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-31 | `fallback-active-signal` |
| `mtbc/Rv2660c` | 3760 | 3760 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-31 | `fallback-active-signal` |
| `mtbc/Rv2698` | 3722 | 3722 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-31 | `fallback-active-signal` |
| `mtbc/Rv2699c` | 3752 | 3752 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-12 | `fallback-active-signal` |
| `mtbc/Rv2901c` | 3741 | 3741 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-31 | `fallback-active-signal` |
| `mtbc/Rv3165c` | 3771 | 3771 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-31 | `fallback-active-signal` |
| `mtbc/Rv3190c` | 3751 | 3751 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-31 | `fallback-active-signal` |
| `mtbc/Rv3258c` | 3725 | 3725 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-31 | `fallback-active-signal` |
| `mtbc/Rv3355c` | 3726 | 3726 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-31 | `fallback-active-signal` |
| `mtbc/Rv3566A` | 3703 | 3703 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-31 | `fallback-active-signal` |
| `mtbc/Rv3604c` | 3725 | 3725 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-31 | `fallback-active-signal` |
| `mtbc/Rv3656c` | 3771 | 3771 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-31 | `fallback-active-signal` |
| `mtbc/Rv3909` | 6312 | 6312 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-18 | `fallback-active-signal` |
| `mtbc/SpacerEgalVirus` | 3391 | 3391 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-08-26 | `fallback-active-signal` |
| `mtbc/TYK2-MTBC-coevolution` | 8910 | 8910 | non | cahier_de_labo.md | - | 2026-05-17 | `fallback-review-required` |
| `mtbc/a_ranger_phylo` | 2916 | 2916 | non | cahier_de_labo.md, JOURNAL.md | - | 2026-06-04 | `fallback-review-required` |
| `mtbc/abandonne/clustering_sola` | 9841 | 9841 | non | cahier_de_labo.md, pistes.md | pistes.md | 2026-08-17 | `fallback-archive-signal` |
| `mtbc/ancient_pathogens_tracer_ranking` | 6435 | 6435 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-12 | `fallback-active-signal` |
| `mtbc/animal_vs_human` | 4227 | 4227 | non | cahier_de_labo.md | - | 2026-08-25 | `fallback-review-required` |
| `mtbc/annotation_mtbc` | 7282 | 7282 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-08-26 | `fallback-active-signal` |
| `mtbc/archeo_crispr` | 3720 | 3720 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-08-20 | `fallback-active-signal` |
| `mtbc/atlas_mtbc` | 11307 | 11307 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-07-30 | `fallback-active-signal` |
| `mtbc/bdd` | 3939 | 3939 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `mtbc/canettii_mtbc_emergence` | 6784 | 6784 | non | cahier_de_labo.md, JOURNAL.md | - | 2026-06-26 | `fallback-review-required` |
| `mtbc/coclustering_lineages` | 3687 | 3687 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-12 | `fallback-active-signal` |
| `mtbc/complex_datation` | 15297 | 15297 | non | cahier_de_labo.md | - | 2026-05-15 | `fallback-review-required` |
| `mtbc/conserved_orphan_modules` | 5274 | 5274 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-07-07 | `fallback-active-signal` |
| `mtbc/crisprcasdb_local` | 1776 | 1776 | non | cahier_de_labo.md | - | 2026-08-03 | `fallback-review-required` |
| `mtbc/dassie_suricattae` | 14431 | 14431 | non | cahier_de_labo.md | - | 2026-04-28 | `fallback-review-required` |
| `mtbc/data-quality` | 3580 | 3580 | non | cahier_de_labo.md | - | 2026-08-10 | `fallback-review-required` |
| `mtbc/fini/Rv0810c` | 10257 | 10257 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-25 | `fallback-archive-signal` |
| `mtbc/fini/Rv2438A` | 9153 | 1880 | oui | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-12 | `agents-local` |
| `mtbc/fini/Rv3222c` | 21870 | 21870 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-25 | `fallback-archive-signal` |
| `mtbc/fini/bpal_resistance_emergence` | 5128 | 5128 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-08-25 | `fallback-archive-signal` |
| `mtbc/fini/dark_enzymes` | 11393 | 11393 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-12 | `fallback-archive-signal` |
| `mtbc/gene_decay_census` | 7309 | 7309 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-07-07 | `fallback-active-signal` |
| `mtbc/global_supplementary` | 4004 | 4004 | non | cahier_de_labo.md | - | 2026-08-10 | `fallback-review-required` |
| `mtbc/h37Rv` | 3172 | 3172 | non | cahier_de_labo.md | - | 2026-04-28 | `fallback-review-required` |
| `mtbc/holdout_benchmark` | 7425 | 7425 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-01 | `fallback-active-signal` |
| `mtbc/investigate_phylo` | 4393 | 4393 | non | cahier_de_labo.md | - | 2026-08-10 | `fallback-review-required` |
| `mtbc/lineage_markers_who_catalogue` | 4302 | 4302 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-08-18 | `fallback-active-signal` |
| `mtbc/lineage_navigator` | 52652 | 1924 | oui | cahier_de_labo.md, pistes.md | pistes.md | 2026-08-26 | `agents-local` |
| `mtbc/methodology` | 2124 | 2124 | non | cahier_de_labo.md, JOURNAL.md | - | 2026-05-15 | `fallback-review-required` |
| `mtbc/mixed_clade_synapomorphies` | 5863 | 5863 | non | cahier_de_labo.md, JOURNAL.md | - | 2026-05-24 | `fallback-review-required` |
| `mtbc/mixed_infections_multimarker` | 5514 | 5514 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-08-20 | `fallback-active-signal` |
| `mtbc/mleprae_atlas` | 5001 | 5001 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-12 | `fallback-active-signal` |
| `mtbc/molecular_clock` | 4941 | 4941 | non | cahier_de_labo.md | - | 2026-05-17 | `fallback-review-required` |
| `mtbc/mtbc0_reconstruction` | 6487 | 6487 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-20 | `fallback-active-signal` |
| `mtbc/orygis-phylogenie` | 11679 | 11679 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-07 | `fallback-active-signal` |
| `mtbc/orygis-phylogenie/archive/orygis_zoonotic` | 6155 | 6155 | non | cahier_de_labo.md | - | 2026-06-06 | `fallback-archive-signal` |
| `mtbc/outils` | 1487 | 1487 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `mtbc/ponA_microsatellite` | 9002 | 9002 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-07-30 | `fallback-active-signal` |
| `mtbc/projets_abandonnes/A la recherche de nouvelles lignees` | 10649 | 10649 | non | cahier_de_labo.md | - | 2026-06-09 | `fallback-archive-signal` |
| `mtbc/projets_abandonnes/Bovis_RDs` | 6924 | 6924 | non | cahier_de_labo.md | - | 2026-06-12 | `fallback-archive-signal` |
| `mtbc/projets_abandonnes/Mycobacterium_divergent_cluster3` | 6315 | 6315 | non | cahier_de_labo.md, JOURNAL.md | - | 2026-05-29 | `fallback-archive-signal` |
| `mtbc/projets_abandonnes/Mycobacterium_sp_novel` | 8326 | 8326 | non | cahier_de_labo.md, JOURNAL.md | - | 2026-05-31 | `fallback-archive-signal` |
| `mtbc/projets_abandonnes/Still unknown gene function` | 12798 | 12798 | non | cahier_de_labo.md | - | 2026-06-13 | `fallback-archive-signal` |
| `mtbc/projets_abandonnes/TA_persistence` | 4745 | 4745 | non | cahier_de_labo.md, JOURNAL.md | - | 2026-06-09 | `fallback-archive-signal` |
| `mtbc/projets_abandonnes/TA_repertoire` | 4766 | 4766 | non | cahier_de_labo.md, JOURNAL.md | - | 2026-06-09 | `fallback-archive-signal` |
| `mtbc/projets_abandonnes/diversifying_antigens` | 7964 | 7964 | non | cahier_de_labo.md | - | 2026-06-12 | `fallback-archive-signal` |
| `mtbc/projets_abandonnes/musee_de_lhomme` | 1911 | 1911 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-08-12 | `fallback-archive-signal` |
| `mtbc/rehumanisation_L6L9L10` | 9767 | 9767 | non | cahier_de_labo.md | - | 2026-06-06 | `fallback-review-required` |
| `mtbc/snp_barcoding` | 1090 | 1090 | non | cahier_de_labo.md | - | 2026-05-15 | `fallback-review-required` |
| `mtbc/spoligo_clock` | 6247 | 6247 | non | cahier_de_labo.md | - | 2026-06-10 | `fallback-review-required` |
| `mtbc/structural_variation_is_rd` | 3368 | 3368 | non | cahier_de_labo.md | - | 2026-06-14 | `fallback-review-required` |
| `mtbc/tbannotator_local` | 1744 | 1744 | non | cahier_de_labo.md | - | 2026-07-31 | `fallback-review-required` |
| `mtbc/tissue_tropism_mtbc` | 11714 | 11714 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-17 | `fallback-active-signal` |
| `mtbc/variant_nucs` | 8591 | 8591 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-26 | `fallback-active-signal` |
| `mtbc/yersinia_atlas` | 6349 | 6349 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-12 | `fallback-active-signal` |
| `mtbc/yersinia_pestis_grands_lacs` | 7438 | 7438 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-08-17 | `fallback-active-signal` |
| `mtbc/yersiniomics` | 6537 | 6537 | non | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-12 | `fallback-active-signal` |
| `old/Michaël` | 9161 | 9161 | non | - | - | 2026-07-29 | `fallback-review-required` |
| `optimops` | 73136 | 2704 | oui | cahier_de_labo.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-24 | `agents-local` |
| `oxyrhynque-papyrologie-ia` | 2911 | 1009 | oui | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-26 | `agents-local` |
| `pomologie` | 16156 | 16156 | non | - | - | 2026-04-05 | `fallback-review-required` |
| `pompiers_croyances` | 14702 | 14702 | non | cahier_de_labo.md | - | 2026-06-16 | `fallback-review-required` |
| `predictops` | 5101 | 1044 | oui | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md | pistes.md | 2026-08-26 | `agents-local` |
| `predictops-mcp/.worktrees/master-release/example_prompts` | 10524 | 20804 | non | - | - | 2026-08-07 | `fallback-review-required` |
| `predictops-mcp/.worktrees/master-release/external_mcps/static_plotting_mcp` | 947 | 11227 | non | - | - | 2026-08-07 | `fallback-review-required` |
| `predictops-mcp/.worktrees/master-release/mymcps` | 10410 | 20690 | non | - | - | 2026-08-07 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p1-16-atmo-dedup/example_prompts` | 10524 | 19293 | non | - | - | 2026-08-14 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p1-16-atmo-dedup/external_mcps/static_plotting_mcp` | 947 | 9716 | non | - | - | 2026-08-14 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p1-16-atmo-dedup/mymcps` | 10410 | 19179 | non | - | - | 2026-08-14 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p25-register/example_prompts` | 10524 | 10524 | non | - | - | 2026-08-06 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p25-register/external_mcps/static_plotting_mcp` | 947 | 947 | non | - | - | 2026-08-06 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p25-register/mymcps` | 10410 | 10410 | non | - | - | 2026-08-06 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p4-3-caddy-loopback/example_prompts` | 10524 | 15996 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p4-3-caddy-loopback/external_mcps/static_plotting_mcp` | 947 | 6419 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p4-3-caddy-loopback/mymcps` | 10410 | 15882 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-12-pluies-intenses/example_prompts` | 10524 | 13219 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-12-pluies-intenses/external_mcps/static_plotting_mcp` | 947 | 3642 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-12-pluies-intenses/mymcps` | 10410 | 13105 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-13-fiabilite-predictops/example_prompts` | 10524 | 14636 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-13-fiabilite-predictops/external_mcps/static_plotting_mcp` | 947 | 5059 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-13-fiabilite-predictops/mymcps` | 10410 | 14522 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-14-observations-meteofrance/example_prompts` | 10524 | 14778 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-14-observations-meteofrance/external_mcps/static_plotting_mcp` | 947 | 5201 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-14-observations-meteofrance/mymcps` | 10410 | 14664 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-15-sante-meteo/example_prompts` | 10524 | 15525 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-15-sante-meteo/external_mcps/static_plotting_mcp` | 947 | 5948 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-15-sante-meteo/mymcps` | 10410 | 15411 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-16-prise-garde/example_prompts` | 10524 | 16649 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-16-prise-garde/external_mcps/static_plotting_mcp` | 947 | 7072 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-16-prise-garde/mymcps` | 10410 | 16535 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-17-calls-quality-audit/example_prompts` | 10524 | 17410 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-17-calls-quality-audit/external_mcps/static_plotting_mcp` | 947 | 7833 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-17-calls-quality-audit/mymcps` | 10410 | 17296 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-18-supervision/example_prompts` | 10524 | 17410 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-18-supervision/external_mcps/static_plotting_mcp` | 947 | 7833 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-18-supervision/mymcps` | 10410 | 17296 | non | - | - | 2026-08-10 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-19-legifrance-doctrine/example_prompts` | 10524 | 18260 | non | - | - | 2026-08-13 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-19-legifrance-doctrine/external_mcps/static_plotting_mcp` | 947 | 8683 | non | - | - | 2026-08-13 | `fallback-review-required` |
| `predictops-mcp/.worktrees/p8-19-legifrance-doctrine/mymcps` | 10410 | 18146 | non | - | - | 2026-08-13 | `fallback-review-required` |
| `predictops-mcp` | 19678 | 10280 | oui | cahier_de_labo.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-16 | `agents-local` |
| `predictops-mcp/example_prompts` | 10524 | 20804 | non | - | - | 2026-06-16 | `fallback-review-required` |
| `predictops-mcp/external_mcps/static_plotting_mcp` | 947 | 11227 | non | - | - | 2026-06-16 | `fallback-review-required` |
| `predictops-mcp/mymcps` | 10410 | 20690 | non | - | - | 2026-06-16 | `fallback-review-required` |
| `predictops-mcp-merge/example_prompts` | 10524 | 10524 | non | - | - | 2026-06-17 | `fallback-review-required` |
| `predictops-mcp-merge/external_mcps/static_plotting_mcp` | 947 | 947 | non | - | - | 2026-06-17 | `fallback-review-required` |
| `predictops-mcp-merge/mymcps` | 10410 | 10410 | non | - | - | 2026-06-17 | `fallback-review-required` |
| `rohonczi` | 23850 | 1043 | oui | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | - | 2026-08-26 | `agents-local` |
| `veille_llm` | 9697 | 31783 | oui | cahier_de_labo.md | - | 2026-08-09 | `agents-local` |
| `voynich` | 7951 | 1100 | oui | cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md | pistes.md | 2026-08-26 | `agents-local` |

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
