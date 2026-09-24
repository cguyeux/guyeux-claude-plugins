# Panels versionnés

Chaque fichier `<genre>_<description>.tsv` de ce répertoire est un panel
figé, réutilisable sans reconstruction par tout projet du dépôt qui étudie
ce genre. Format et colonnes obligatoires : voir `../SKILL.md` § Format du
panel. Un panel se construit à partir d'une revue de littérature tracée
(`/lit-review`), jamais improvisé.

## `leptospira_p1_p2_s1_s2.tsv`

Clades de pathogénicité P1 (pathogènes, haute virulence) / P2
(intermédiaires) / S1 / S2 (saprophytes), établi depuis Vincent et al.
2019 (PLoS Neglected Tropical Diseases, DOI 10.1371/journal.pntd.0007270,
pas BMC Genomics — corrigé le 2026-09-18) et trois articles de description
d'espèces post-2019 (Korba 2021, Fernandes 2022, Hamond 2025), consolidés
par la Table 1 d'une revue de synthèse janvier 2026 (Current Microbiology,
DOI 10.1007/s00284-026-04722-7). Détail de la revue :
`mtbc/litterature_review/leptospira_phylogenomique.md`.

**66 espèces sur 74 décrites** ont au moins une accession directement
exploitable (79 lignes : plusieurs espèces portent 2 candidats non
départagés faute d'accès au plein texte qui nomme la souche type). Test de
bout en bout du script sur `borgpetersenii` (GCA_000013945.1, groupe P1) :
téléchargement + `skani` + verdict, OK.

**8 espèces manquantes, à compléter avant de considérer le panel
définitif** — le rapport de revue ne donnait qu'une notation par plage
(« N candidats, RQFA–RQFC00000000 ») pour ces espèces, sans accession
individualisée à recopier fidèlement ; les données existent (tableau
supplémentaire S1 de Vincent et al. 2019, 124 génomes, parsé par l'agent
de revue mais conservé dans son scratchpad de session, pas versé au
dépôt) :

| Espèce | Groupe | Manque |
|---|---|---|
| gomenensis | P1 | accessions individuelles (4 candidats rapportés en plage) |
| yasudae (= dzianensis) | P1 | accessions individuelles (6 candidats rapportés en plage) |
| selangorensis | P2 | accessions individuelles (3 candidats, dont un nom de souche sans accession) |
| bouyouniensis | S1 | 2 des 3 accessions rapportées en forme abrégée non confirmée |
| bourretii | S1 | accessions individuelles (4 candidats rapportés en plage) |
| congkakensis | S1 | accessions individuelles (3 candidats rapportés en plage) |
| kanakyensis | S1 | accessions individuelles (3 candidats rapportés en plage) |
| levettii | S1 | aucune accession rapportée (espèce la plus échantillonnée, 12 candidats) |

**Ambiguïtés à trancher avant publication** (dans le TSV, colonne `note`) :
huit paires d'espèces portent 2 candidats génomiques sans que la souche
portant le statut nomenclatural type (marque T) soit identifiable depuis
le plein texte accessible — relire la description originale de chacune au
moment de figer le panel pour un usage publié, ou garder les deux lignes
(inoffensif pour le classement : `skani` retient de toute façon le
meilleur hit). Cinq espèces (`ainazelensis`, `ainlahdjerensis`,
`chreensis`, `abararensis` — Korba 2021 — et `sanjuanensis` — Fernandes
2022) reposent sur une source non-OA lue seulement via la Table 1 de la
revue 2026 (source secondaire) : à confirmer par `/literature-access`
avant tout usage publié.

**Aucun outil de classement publié équivalent** (constat de la revue) :
BIGSdb-Pasteur Leptospira fait de l'identification d'espèce par cgMLST
mais ne rend pas le clade P1/P2/S1/S2 ; Abdullah et al. 2025 refait une
classification indépendante par AAI mais ne publie ni code ni pipeline et
retombe sur une résolution plus grossière (S1+S2 fusionnés). Ce panel est
donc le seul artefact réutilisable identifié pour cette question.
