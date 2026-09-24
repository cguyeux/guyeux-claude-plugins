---
name: jgi-imgvr
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST, peer-reviewed comparative
  genomics) for programmatic access to the JGI Genome Portal / IMG-VR (viral
  and metagenomic sequence database, Integrated Microbial Genomes, DOE Joint
  Genome Institute): bulk download of an export by API, streaming BLAST or
  single-record extraction of the internal multi-hundred-gigabyte .fna.gz
  without ever materialising it decompressed on disk, and the IMG/VR
  "Viral/Spacer BLAST" web form driven by token (currently broken server-side,
  documented below). Use when: BLASTing a query set (spacers, candidate
  protospacers, any short sequence) against IMG/VR's viral/metagenomic
  content, retrieving one specific record from a JGI bulk export by header
  substring, or downloading a JGI Data Portal file programmatically without a
  browser session.
argument-hint: "download|scan|extract|blast <args>"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# JGI Data Portal / IMG-VR, accès programmatique

## Ce que c'est

Client Python sans dépendance lourde (`requests` seul, plus `blastn`/`makeblastdb` du BLAST+
système pour `scan`) vers deux services du DOE Joint Genome Institute : le **JGI Genome Portal**
(export en masse, authentification par jeton de session) et **IMG/VR**
(`img.jgi.doe.gov/cgi-bin/vr/`, base de séquences virales et métagénomiques, formulaire web
« Viral/Spacer BLAST »). Écrit et durci dans `archeo_crispr` (test protospacer CRISPR de
*M. canettii*, A1.5), promu skill partagé le 2026-09-22 après un second projet effectivement
réutilisateur (`SpacerEgalVirus`, cf. PROVENANCE.md).

| | |
|---|---|
| Script | `scripts/jgi_imgvr_access.py` (stdlib + `requests`) |
| Auth par défaut | Bearer token, `~/.jgi_session_token` (menu avatar JGI -> « Copy My Session Token ») |
| Auth de repli (non encapsulée) | cookie Keycloak `kc_session=<JWT>`, bouton « Command line download » du panier — cf. § Authentification |
| Origine | `mtbc/en_cours/archeo_crispr`, A1.5.e/f/g (2026-08-11/12) |
| BLAST+ requis pour `scan` | `makeblastdb`, `blastn` dans le PATH |

## Obtenir un jeton

1. Se connecter au portail (`genome.jgi.doe.gov` ou `img.jgi.doe.gov`) via **Sign in with ORCID**
   (le JGI a basculé son login vers ORCID + 2FA obligatoire le 2026-07-27 ; l'ancien flux
   « créer un compte JGI puis lier l'ORCID » n'est plus la voie la plus courte).
2. Menu avatar -> « Copy My Session Token ».
3. Coller dans `~/.jgi_session_token` (mode `600`, un jeton par ligne, `Bearer ` optionnel en
   préfixe).

Le jeton expire (durée non documentée par JGI, observée valide au moins un mois dans ce projet) ;
un HTTP 401 sur `download`/`scan`/`extract`/`blast` (soumission, pas récupération) signale un
renouvellement nécessaire.

## Interroger

```bash
JGI=~/docs/environnement/plugins/bacteria/skills/jgi-imgvr/scripts/jgi_imgvr_access.py

# Télécharger un export JGI Data Portal (panier constitué sur le site, file_id/top_hit lus
# dans l'URL ou le payload de la requête POST observée dans les devtools du navigateur)
$JGI download --source Custom_MPI-IMG_VR --file-id <id> --top-hit <id> \
    --out data/imgvr/export.zip

# BLAST par lots contre le dump nucléotidique complet, streaming, jamais matérialisé entier
$JGI scan --zip data/imgvr/export.zip --query variables.fa --control controle.fa \
    --batch-gb 8 --out résultats/protospacer_imgvr.json

# Une seule séquence, par sous-chaîne de son en-tête FASTA (beaucoup plus rapide que scan
# pour une cible déjà identifiée)
$JGI extract --zip data/imgvr/export.zip --id-substring 2565956756_000002 \
    --out résultats/candidat.fasta

# Formulaire web « Viral/Spacer BLAST » — CASSÉ CÔTÉ SERVEUR, voir garde-fou ci-dessous
$JGI blast --fasta requêtes.fasta --use-db nucleotide_db --evalue 1e-0 \
    --out résultats/protospacer_online.json
```

`scan` et `extract` opèrent sur un export **déjà téléchargé** (`download` d'abord, ou obtenu par
un autre canal, cf. § Authentification) : ni l'un ni l'autre ne matérialise le `.fna.gz` interne
décompressé sur disque (streaming ligne par ligne, garde-fous RAM et disque intégrés — voir le
docstring du module pour le détail des deux incidents qui les ont fait naître, OOM-kill silencieux
et timeout `blastn` non attrapé).

## Garde-fou majeur : `blast` est cassé côté serveur IMG/VR (persistant, pas transitoire)

**Ne pas router une piste dépendante sur `blast` sans un test de fumée récent qui le confirme
réparé.** La récupération des résultats du formulaire web échoue systématiquement avec
`Software error: 'null' expected, at character offset 0 (before "no2 - /webfs/message...") at
.../WorkspaceBlast.pm line 454`, y compris via le lien de repli « View raw Blast data file » de
la page d'erreur elle-même. La **soumission** est acceptée sans erreur (jeton valide, job mis en
file et exécuté) : seule la **récupération** échoue, côté serveur, pas côté client — ce n'est ni
un problème d'authentification ni un problème de requête.

Détecté le 2026-08-12 (`archeo_crispr`, A1.5.g/A1.5.l), reproduit à l'identique le 2026-09-01
(`SpacerEgalVirus`, sur un lot de 10 spacers quelconques ET sur les 5 hits SpacePHARER les mieux
caractérisés — donc pas un problème de contenu de requête), **reconfirmé le 2026-09-22** (smoke
test d'une ligne, même trace exacte, même numéro de ligne Perl). Trois mesures sur six semaines,
même signature : traiter comme une panne serveur durable, pas ponctuelle. `scan`/`extract`
donnent accès aux mêmes données nucléotidiques par un chemin différent (dump complet plutôt que
formulaire) et ne sont pas affectés.

Si une piste a besoin de `blast` spécifiquement (jeu court, < 10 000 caractères, pas de dump
disponible) : relancer le smoke test ci-dessous avant d'investir dessus, et signaler au webmaster
IMG/VR si toujours cassé (adresse obscurcie dans la page d'erreur elle-même, cf. code source).

```bash
printf '>smoke\nACGTGACCTGATCGATCGTAGCTAGCTAGCATCGATCGA\n' > /tmp/smoke.fa
$JGI blast --fasta /tmp/smoke.fa --timeout-s 45 --poll-interval 5
# Soumission + job "terminé" attendus ; RuntimeError "Software error" = toujours cassé.
```

## Garde-fous transversaux (RAM, disque)

Machine PARTAGÉE : `scan`/`extract` lisent `MemAvailable` (`/proc/meminfo`, jamais `MemFree` ni
le swap libre) avant d'indexer un lot BLAST et s'arrêtent proprement en dessous de `--min-ram-gb`
plutôt que de risquer un OOM-kill silencieux (SIGKILL, aucune trace exploitable — cf. l'incident
qui a fait naître ce garde-fou, docstring du module). Le disque est vérifié avant CHAQUE lot et
PENDANT l'écriture (pas seulement avant/après), seuil `--min-free-gb` (défaut 2x `--batch-gb`).
Ne jamais estimer un ratio de décompression par `gzip -l` seul au-delà de quelques Gio : mesurer
sur un échantillon réel avant d'engager un `scan`/`download` de plusieurs dizaines de Gio.

## Authentification, deux mécanismes non interchangeables

Le Bearer token (`~/.jgi_session_token`) couvre `download`/`scan`/`extract`/`blast` dans ce
script. Un second mécanisme, distinct, a été découvert le 2026-09-03 sur un usage tiers
(`SpacerEgalVirus`, téléchargement de `IMGVR_all_Host_information-high_confidence.tsv` via le
bouton « Command line download » du panier du NOUVEAU JGI Data Portal, qui échoue en HTTP 401 avec
le Bearer classique alors que celui-ci reste valide pour `download`/`scan`/`blast`) : cookie de
session Keycloak (`kc_session=<JWT>`), obtenu depuis ce même bouton, testé HTTP 200 fichier intact.
**Non encapsulé dans ce script** — à ajouter comme repli `--auth cookie` si le Bearer venait à se
périmer, ou si un usage futur en a besoin. N'importe quel dataset du JGI Data Portal expose le
même bouton, pas seulement IMG/VR : généralisable au-delà de ce skill.

## Recyclabilité

En-tête normalisée du module (`Objet / Entrées / Sorties / Réutilisable / Projet / Date`,
convention `python-patterns-donnees-scientifiques-manuscrit.md` du 2026-08-26) : lire seulement
ces ~15 premières lignes avant de juger si une nouvelle piste doit réutiliser ce script plutôt que
d'en réécrire un.

## Voisinage

`crisprcasdb` (base CRISPR-Cas locale, même plugin) pour la comparaison catalogue plutôt que
recherche brute de protospacer ; `crisprbuilder` (même plugin) pour la détection CRISPR de novo
sur reads/assemblages, en amont des séquences qu'on soumet ensuite ici. Ce skill répond à une
question qu'aucun des deux ne couvre : la présence d'une séquence donnée dans le contenu viral et
métagénomique IMG/VR, hors de tout catalogue CRISPR.
