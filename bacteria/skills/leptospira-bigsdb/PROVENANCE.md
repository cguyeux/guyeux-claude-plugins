# Provenance

- Source scientifique : Jolley KA, Bray JE, Maiden MCJ. *Open-access bacterial population
  genomics: BIGSdb software, the PubMLST.org website and their applications.* Wellcome Open
  Research 2018, 3:124. DOI: 10.12688/wellcomeopenres.14826.1
- Service source : BIGSdb Pasteur, Institut Pasteur (Unité Biologie des Spirochètes,
  Mathieu Picardeau), bases `pubmlst_leptospira_isolates` et `pubmlst_leptospira_seqdef`.
  `https://bigsdb.pasteur.fr/api`.
- Code dans ce plugin : `scripts/bigsdb_leptospira.py` est un client REST original (module
  `requests`), sans données embarquées.
- Contact pour un compte (lève le plafond 2024-12-31) : Alexandre Giraud-Gatineau, Institut
  Pasteur — origine de ce skill (mail du 2026-09-18).

## Mesures du 2026-09-22 (API interrogée en direct, cf. `~/.agents/knowledge/leptospira.md` pour
le détail scientifique — ne pas dupliquer ici)

- 1558 isolats, 1557 génomes assemblés téléchargeables.
- Répartition par clade : P1 1312, S1 146, P2 71, S2 9, Unknown 7.
- Complétude (valeurs informatives, hors `Unknown`/`unknown`/`Not examined`/`not examined`/
  `Unknow` et champs absents) : `country` 98,5 %, `clade` 98,7 %, `host` 91,0 %,
  `sample_type` 69,6 %, `serogroup` 58,7 %, `serovar` 34,5 %.
- `GET /db/{base}/isolates?<champ>=<valeur>` ignore silencieusement un filtre inconnu et
  renvoie toute la base (piège actif, vérifié) ; seul `POST /isolates/search` filtre
  réellement.
- Filtrage : égalité stricte, insensible à la casse, pas de correspondance par sous-chaîne.

## Garde-fous du script

- `--filter` obligatoire pour `genomes`, sauf `--all-isolates` explicite.
- `--limit` par défaut 50 sur `genomes` (`--limit 0` pour lever le plafond).
- Toute requête réseau relaie l'avertissement serveur sur le plafond 2024-12-31 (piège b).
- `genomes` lève une erreur (au lieu d'écrire un répertoire vide) si aucun isolat du lot filtré
  ne porte de génome assemblé.

## Test de non-régression effectué à l'écriture (2026-09-22)

`stats`, `breakdown` (6 champs, complétude reproduisant les valeurs ci-dessus à 0,1 point
près), `search --filter clade=S2` (9/9 isolats), `genomes --filter clade=S2` (9/9 génomes
téléchargés, nombre de contigs de chaque FASTA reconcilié avec `sequence_bin.contig_count`
déclaré par la base — 0 écart), `search`/`genomes` sur filtre inconnu (lève) et sur filtre
valide légitimement vide `clade=P3` (`search` : 0 ligne annoncée, `genomes` : lève).
