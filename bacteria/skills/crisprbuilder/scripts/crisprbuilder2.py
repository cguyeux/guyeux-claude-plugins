#!/usr/bin/env python3
"""crisprbuilder2 — extraction d'un locus CRISPR SANS catalogue de motifs.

Successeur outillé de CRISPRbuilder-TB (Guyeux 2021, PLOS Comput Biol
17(3):e1008500, https://github.com/cguyeux/CRISPRbuilder-TB).

POURQUOI CET OUTIL
------------------
CRISPRbuilder-TB reconstruit le locus DR depuis les reads — ce qui est la bonne
approche, car un assembleur EFFACE les régions faites de répétitions
(mesuré : 17 assemblages SPAdes de M. canettii sur 21 ne contiennent aucune
copie du DR, et l'échec est silencieux). Mais il part d'un catalogue de 221
motifs connus du MTBC (`crispr_patterns.fasta`), et ne peut donc rien trouver
là où le DR diffère. Or *M. canettii* porte au moins quatre systèmes distincts :
III-A (DR du MTBC), I-G, I-E et I-C, avec des DR sans aucun rapport entre eux.

Cet outil lève ce verrou : le DR est soit fourni, soit **découvert de novo**, et
l'extraction ne dépend d'aucun catalogue.

DEUX SOURCES, DEUX RÉGIMES
--------------------------
  genome   : séquence assemblée ou de référence. Rapide et exact, mais ne
             fonctionne que si le locus a survécu à l'assemblage (voir plus haut).
  reads    : FASTA/FASTQ de lectures. Robuste aux régions répétitives, seule
             voie fiable pour une souche sans génome complet.

MÉTHODE DE DÉCOUVERTE DE NOVO
-----------------------------
Un DR CRISPR est un k-mer qui (1) revient souvent et (2) revient à intervalles
RÉGULIERS, l'intervalle valant DR + spacer, soit typiquement 55 à 120 nt. La
seconde condition est ce qui distingue un DR d'un simple répète génomique, et
c'est elle qui évite les faux positifs sur les familles répétées en tandem
(PE-PGRS, MIRU) où les écarts sont bien plus courts et irréguliers.

Usage
-----
    crisprbuilder2.py detect  --genome g.fasta [--kmer 21]
    crisprbuilder2.py extract --genome g.fasta [--dr SEQ] [--json out.json]
    crisprbuilder2.py extract --reads r.fasta [--dr SEQ] [--json out.json]
    crisprbuilder2.py batch   --glob '.../*/assembly/contigs.fasta' --json out.json
"""

import argparse
import gzip
import json
import math
import signal
import socket
import statistics
import sys
from array import array
from collections import Counter, defaultdict
from pathlib import Path

# `urllib.request.urlopen` (mode `--reads` sur une URL http/https/ftp) n'a pas le repli rapide
# IPv4/IPv6 de `curl` : sur un hote a double pile dont la route IPv6 est instable ou tres lente
# (mesure : mp, 2026-09-22, extraction A5.1a phase 2), `socket.create_connection` attend le
# TIMEOUT ENTIER sur l'adresse IPv6 avant de retomber sur IPv4 -- facteur ~150-300x mesure sur un
# cas comparable (cf. python-patterns.md, entree du 2026-08-26). Force IPv4 pour tout le process,
# avant le premier appel reseau.
_getaddrinfo_v4 = socket.getaddrinfo


def _getaddrinfo_ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
    return _getaddrinfo_v4(host, port, socket.AF_INET, type, proto, flags)


socket.getaddrinfo = _getaddrinfo_ipv4_only

COMP = str.maketrans("ACGTNacgtn", "TGCANtgcan")

# Fenetre d'espacement DR->DR attendue pour un CRISPR (DR + spacer).
PERIOD_MIN, PERIOD_MAX = 55, 130
# Un spacer hors de ces bornes n'est pas retenu.
SPACER_MIN, SPACER_MAX = 20, 60


def rc(s):
    return s.translate(COMP)[::-1]


def read_fasta(path):
    """Rend {nom: sequence}. Accepte .gz, FASTA et FASTQ."""
    op = gzip.open if str(path).endswith(".gz") else open
    seqs, name, buf = {}, None, []
    with op(path, "rt") as f:
        first = f.readline()
        f.seek(0)
        if first.startswith("@"):                      # FASTQ
            for i, line in enumerate(f):
                if i % 4 == 0:
                    name = line[1:].split()[0]
                elif i % 4 == 1:
                    seqs[f"{name}_{i}"] = line.strip().upper()
            return seqs
        for line in f:                                  # FASTA
            line = line.rstrip()
            if line.startswith(">"):
                if name is not None:
                    seqs[name] = "".join(buf).upper()
                name, buf = line[1:].split()[0], []
            else:
                buf.append(line)
    if name is not None:
        seqs[name] = "".join(buf).upper()
    return seqs


def hamming_positions(hay, needle, max_mm):
    """Positions de `needle` dans `hay` avec au plus max_mm mismatches.

    Ancre sur une graine exacte pour rester rapide : une occurrence tolerant
    max_mm mismatches sur L nt contient forcement une graine exacte de
    L // (max_mm + 1) nt (principe des tiroirs).
    """
    L = len(needle)
    if L == 0 or len(hay) < L:
        return []
    seed_len = max(8, L // (max_mm + 1))
    seeds = [(i, needle[i:i + seed_len]) for i in range(0, L - seed_len + 1, seed_len)]
    cand = set()
    for off, seed in seeds:
        start = 0
        while True:
            j = hay.find(seed, start)
            if j < 0:
                break
            p = j - off
            if 0 <= p <= len(hay) - L:
                cand.add(p)
            start = j + 1
    out = []
    for p in sorted(cand):
        w = hay[p:p + L]
        if sum(1 for a, b in zip(w, needle) if a != b) <= max_mm:
            out.append(p)
    return out


def positions_kmers_repetes(seqs, names, kmer, min_occ):
    """Positions des k-mers vus au moins `min_occ` fois, canonises par brin.

    POURQUOI PAS UN SIMPLE DICTIONNAIRE. La version directe indexait les 4,4
    millions de k-mers d'un genome bacterien dans un `defaultdict(list)` et
    appelait `rc()` sur chacun : mesure sur un genome de M. canettii, 1,25 Go
    de memoire residente et environ une minute par genome — ce qui interdisait
    le passage a l'echelle (piste P10.3) et exposait a un kill memoire.

    Or les k-mers de 21 nt vus plusieurs fois dans un genome bacterien sont
    RARES (IS, operons rRNA, PE-PGRS, et le CRISPR cherche ici) : il est donc
    absurde de payer le stockage des millions de k-mers uniques. Deux passes :

      1. un filtre de comptage a memoire bornee (tableau de compteurs indexe
         par hachage, quelques dizaines de Mo) marque les seaux vus >= 2 fois ;
      2. seules les positions dont le seau est marque sont relues, canonisees
         et comptees EXACTEMENT.

    Le filtre ne peut pas produire de faux negatif — un k-mer reellement repete
    incremente forcement son seau au moins deux fois — donc le resultat final
    est identique a celui de la version directe, collisions comprises : elles
    n'ajoutent que du travail en passe 2, jamais une erreur. Le resultat ne
    depend pas non plus de la graine de hachage de Python, puisque la passe 2
    recompte exactement.
    """
    n_bases = sum(len(seqs[n]) for n in names)
    bits = min(27, max(20, n_bases.bit_length() + 3))
    masque = (1 << bits) - 1
    seaux = array("H", bytes(2 * (1 << bits)))

    for n in names:                                   # passe 1 : marquage
        s = seqs[n]
        for i in range(len(s) - kmer + 1):
            h = hash(s[i:i + kmer]) & masque
            if seaux[h] < 65535:
                seaux[h] += 1

    pos = defaultdict(list)                           # passe 2 : positions exactes
    for si, n in enumerate(names):
        s = seqs[n]
        for i in range(len(s) - kmer + 1):
            k = s[i:i + kmer]
            if seaux[hash(k) & masque] < 2 or "N" in k:
                continue
            pos[min(k, rc(k))].append((si, i))
    return {k: v for k, v in pos.items() if len(v) >= min_occ}


def frequences_bases(seqs):
    """Composition en bases du jeu, servant de reference au critere d'arret.

    Un genome a 65 % de GC rend une colonne dominee par un G bien moins
    surprenante qu'un genome equilibre : le seuil de conservation ne peut donc
    pas etre une constante, il doit se lire contre cette composition.
    """
    c = Counter()
    for s in seqs.values():
        c.update(s)
    n = sum(c[b] for b in "ACGT")
    return {b: (c[b] / n if n else 0.25) for b in "ACGT"}


def diversite_spacers(spacers, k=8, max_paires=2000):
    """1 - identite moyenne entre spacers, sur les k-mers partages (Jaccard).

    LE discriminant entre un CRISPR et une REPETITION EN TANDEM, et il manquait.
    Les deux produisent un motif court, tres conserve, revenant a intervalles
    reguliers : la periodicite ne les separe pas, la conservation du DR non plus
    (100 % dans les deux cas). Ce qui les separe est ce qu'il y a ENTRE les
    copies. Un array CRISPR intercale des spacers tous differents, captures
    independamment ; un VNTR repete une unite, donc ses « spacers » sont des
    copies les unes des autres.

    Cas qui a impose la mesure (CIPT 140070008) : un VNTR a 11 copies d'un
    motif de 23 nt, ecart de 69 nt ONZE FOIS DE SUITE, battait le vrai locus
    I-G (10 copies, ecarts 71/72/71/72/71/73) sur tous les criteres existants.
    Ses dix « spacers » sont pourtant des variantes a un nucleotide du meme
    GGTAATCGGACCGAT[AG]CCGCCCAGCGCGTTCAGGCTCAGCGGAAT. Un test d'unicite exacte
    ne l'aurait pas vu non plus — il rend 7 spacers « distincts » sur 10 — d'ou
    une mesure d'identite et non de duplication.

    Note : la regularite PARFAITE des ecarts est en soi un indice de tandem, un
    vrai array ayant des spacers de longueurs inegales. La diversite reste le
    critere plus sur, car un array a spacers de meme longueur existe.

    Renvoie 1,0 pour un array vide ou a un seul spacer (rien a contredire).
    """
    sp = [s for s in spacers if len(s) >= k]
    if len(sp) < 2:
        return 1.0
    ens = [{s[i:i + k] for i in range(len(s) - k + 1)} for s in sp]
    total = n = 0
    pas = max(1, (len(ens) * (len(ens) - 1) // 2) // max_paires)
    compteur = 0
    for a in range(len(ens)):
        for b in range(a + 1, len(ens)):
            compteur += 1
            if compteur % pas:
                continue
            union = ens[a] | ens[b]
            total += len(ens[a] & ens[b]) / len(union) if union else 0.0
            n += 1
    return round(1.0 - (total / n if n else 0.0), 3)


def _queue_binomiale(n_max, n, p):
    """P(X >= n_max) pour X ~ B(n, p), exactement."""
    if n_max <= 0:
        return 1.0
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i)
               for i in range(n_max, n + 1))


def detect_dr(seqs, kmer=21, min_occ=4, top=5, sample=None):
    """Decouvre le(s) DR candidat(s) de novo.

    Retourne une liste de dicts tries par score decroissant. Le score combine
    le nombre d'occurrences et la REGULARITE des ecarts, cette derniere etant
    le critere qui separe un vrai DR d'un simple repete.
    """
    names = list(seqs)
    if sample and len(names) > sample:
        step = max(1, len(names) // sample)
        names = names[::step][:sample]

    pos = positions_kmers_repetes(seqs, names, kmer, min_occ)
    fond = frequences_bases(seqs)

    cands = []
    for k, occ in pos.items():
        # FILTRE DE BASSE COMPLEXITE, ETENDU AU MODE GENOME (piste P10.1). Il
        # n'etait applique qu'aux lectures, ou il ecarte homopolymeres et
        # adaptateurs. Sur un genome de mycobacterie il est tout aussi
        # necessaire : les repetitions GC des familles PE-PGRS (motifs de type
        # CCGCCGGCGCCGCCGGCGCCG, Gly-Ala) sont nombreuses, quasi periodiques, et
        # dispersees sur des dizaines de genes — donc avec des intervalles tous
        # differents, ce que la mesure de diversite prend pour un bon array. Un
        # tel motif remportait le classement sur CIPT 140070008. Un vrai DR
        # CRISPR n'est jamais un microsatellite : le filtre est gratuit et sans
        # faux positif connu sur les DR de reference.
        if low_complexity(k):
            continue
        gaps = []
        by_seq = defaultdict(list)
        for si, i in occ:
            by_seq[si].append(i)
        for si, ii in by_seq.items():
            ii.sort()
            gaps += [b - a for a, b in zip(ii, ii[1:])]
        good = [g for g in gaps if PERIOD_MIN <= g <= PERIOD_MAX]
        if len(good) < 2:
            continue
        # regularite : ecart-type relatif faible = periode nette
        sd = statistics.pstdev(good) if len(good) > 1 else 0.0
        med = statistics.median(good)
        regularity = 1.0 / (1.0 + sd / med) if med else 0.0
        frac = len(good) / len(gaps) if gaps else 0.0
        score = len(good) * regularity * frac
        cands.append({"kmer": k, "occ": occ, "n_occ": len(occ),
                      "n_periodic": len(good), "median_gap": med,
                      "regularity": round(regularity, 3),
                      "frac_periodic": round(frac, 3), "score": round(score, 2)})
    cands.sort(key=lambda d: -d["score"])

    # DEDUPLICATION PAR LOCUS, ET AVANT L'EXTENSION (corrige, piste P10.1).
    # L'ancienne version dedupliquait sur le DR ETENDU, donc apres extension, et
    # s'arretait des que 15 DR distincts etaient retenus. Or les k-mers decales
    # d'un meme repete sont des dizaines : les quinze places etaient consommees
    # par une poignee de loci, et un DR classe au-dela n'etait jamais examine.
    # Mesure sur CIPT 140070008 : le vrai DR I-G arrive au rang 80 des 649
    # k-mers periodiques, avec un score de periodicite (8,91) a peine inferieur
    # a celui des premiers (10,00) — il etait donc ecarte sans avoir ete teste,
    # ce qui explique le seul echec du banc de validation.
    # Deux seeds sont maintenant tenus pour le meme repete si leurs occurrences
    # tombent aux memes endroits du genome, ce qui se lit sans rien calculer.
    kept, occupes = [], set()
    for c in cands:
        seaux = {(si, i // 32) for si, i in c["occ"]}
        voisins = {(si, b + d) for si, b in seaux for d in (-1, 0, 1)}
        if occupes and len(seaux & occupes) >= 0.6 * len(seaux):
            continue
        occupes |= voisins
        kept.append(c)
        if len(kept) >= max(40, top * 4):
            break
    for c in kept:
        c["dr"] = extend_consensus(seqs, c["kmer"], fond=fond)

    # RECLASSEMENT PAR VALIDATION. Le score de periodicite seul ne discrimine
    # plus quand l'array est petit : sur M. canettii CIPT 140070008, dont le
    # locus I-G ne compte que 10 DR, un simple repete genomique le depassait.
    # On tranche donc en extrayant reellement l'array de chaque candidat : un
    # vrai DR donne beaucoup de spacers ET une conservation elevee.
    for c in kept:
        arrays = extract_arrays(seqs, c["dr"], max_mm=3)
        c["n_spacers_found"] = sum(a["n_spacers"] for a in arrays)
        c["dr_conservation"] = dr_conservation(seqs, c["dr"], arrays)
        c["spacer_diversity"] = diversite_spacers(
            [sp for a in arrays for sp in a["spacers"]])
        # La conservation entre au CARRE, et non lineairement. Justification
        # chiffree, tiree de la calibration de CRISPRCasdb (143 878 loci) :
        # un locus evidence 4 est a 93,1 % de conservation en moyenne (mediane
        # 95,5), un locus evidence 2 — la classe des repetitions mal conservees
        # — a 41,6 %. L'ecart utile se joue donc dans les dix derniers points, et
        # un facteur lineaire ne le voit pas : sur CIPT 140070008, un repete
        # GC de 21 nt a 91,5 % arrivait a egalite avec le vrai DR I-G a 100 %.
        cons = c["dr_conservation"] / 100.0
        c["validation_score"] = round(
            c["n_spacers_found"] * cons * cons * c["spacer_diversity"], 2)
    # La regle de parcimonie « a validation egale, preferer le DR le plus court »
    # a ete RETIREE (piste P10.1). Elle compensait la sur-extension du consensus ;
    # celle-ci etant corrigee a la source, la regle ne faisait plus que privilegier
    # systematiquement les graines non etendues de 21 nt sur les vrais DR de 36 nt,
    # et c'est elle qui, une fois les autres correctifs poses, faisait encore
    # perdre le DR I-G de CIPT 140070008 (8,99 contre 8,87, ecarte pour 15 nt de
    # plus). Le classement se fait desormais sur la seule validation.
    kept.sort(key=lambda d: -d["validation_score"])
    return kept[:top]


def extend_consensus(seqs, seed, max_len=50, fond=None, plancher=0.85,
                     alpha=1e-3, max_ctx=400):
    """Etend une graine en DR complet par consensus des occurrences.

    max_len borne la longueur FINALE du DR. Sans cette borne, l'extension
    deborde sur les spacers voisins quand ceux-ci se ressemblent, et rend un
    pseudo-DR de plus de 100 nt qui est en fait un morceau d'array entier
    (constate sur M. canettii CIPT 140070008). Les DR CRISPR connus vont de 23
    a ~50 nt : au-dela, c'est une sur-extension.

    CRITERE D'ARRET (corrige, piste P10.1). L'ancienne version arretait
    l'extension a la premiere colonne dont la base dominante tombait sous 80 %,
    seuil FIXE quel que soit le nombre d'occurrences. Sur un petit array c'est
    trop permissif : avec 10 copies du DR et un genome a 65 % de GC, une colonne
    de spacer prise au hasard atteint 8/10 dans environ 3 tirages sur mille par
    colonne — assez pour que l'extension morde sur le spacer et rende 41 nt la
    ou le DR en fait 36 (CIPT 140070008, seul echec du banc de validation).

    Le seuil est donc rendu DEPENDANT DE L'EFFECTIF et de la composition : une
    colonne n'est retenue que si sa base dominante est plus frequente que ce
    qu'un tirage binomial sous la composition du genome produirait avec une
    probabilite `alpha`. Consequence chiffree : a 10 occurrences il faut 9/10,
    a 30 occurrences 26/30 suffisent. Un plancher absolu reste applique, sans
    quoi un tres grand nombre d'occurrences rendrait significative une colonne
    a 50 % de conservation, qui n'est pas une colonne de DR.

    ALIGNEMENT (corrige au passage). Les contextes etaient decoupes par
    `hay[max(0, j - pad) : ...]`, si bien qu'une occurrence situee a moins de
    `pad` nt du debut d'une sequence rendait un contexte plus court, dans lequel
    la graine ne commencait plus a l'indice `pad`. Toutes les colonnes de ce
    contexte etaient alors decalees et melangees aux autres. Invisible sur un
    chromosome complet, le defaut mord sur des contigs courts et sur des
    lectures — exactement les cas ou l'outil sert. Les contextes sont desormais
    completes par un caractere neutre, ignore au comptage.
    """
    fond = fond or frequences_bases(seqs)
    ctx = []
    pad = max_len
    for s in seqs.values():
        for hay in (s, rc(s)):
            start = 0
            while True:
                j = hay.find(seed, start)
                if j < 0:
                    break
                gauche = hay[max(0, j - pad):j].rjust(pad, ".")
                droite = hay[j + len(seed): j + len(seed) + pad].ljust(pad, ".")
                ctx.append(gauche + seed + droite)
                start = j + 1
        if len(ctx) >= max_ctx:
            break
    if not ctx:
        return seed
    ctx = ctx[:max_ctx]

    def colonne(d):
        """Bases observees a l'offset d par rapport au debut de la graine."""
        return [c[pad + d] for c in ctx if c[pad + d] != "."]

    def retenue(d):
        col = colonne(d)
        if len(col) < 4:
            return False
        b, n = Counter(col).most_common(1)[0]
        if b not in "ACGT" or n / len(col) < plancher:
            return False
        return _queue_binomiale(n, len(col), fond.get(b, 0.25)) <= alpha

    budget = max(0, max_len - len(seed))              # nt d'extension autorises
    left = right = 0
    for d in range(1, pad + 1):                       # extension a gauche
        if left + right >= budget or not retenue(-d):
            break
        left = d
    for d in range(0, pad):                           # extension a droite
        if left + right >= budget or not retenue(len(seed) + d):
            break
        right = d + 1

    out = []
    for d in range(-left, len(seed) + right):
        col = colonne(d)
        if not col:
            break
        out.append(Counter(col).most_common(1)[0][0])
    cons = "".join(out)
    return cons if len(cons) >= len(seed) else seed


def extract_arrays(seqs, dr, max_mm=3, min_spacers=2):
    """Extrait les arrays : positions du DR, puis intervalles = spacers."""
    arrays = []
    for name, s in seqs.items():
        for strand, hay in (("+", s), ("-", rc(s))):
            hits = hamming_positions(hay, dr, max_mm)
            if len(hits) < min_spacers + 1:
                continue
            # regroupe en arrays : DR consecutifs espaces de PERIOD_MIN..MAX
            block, blocks = [hits[0]], []
            for p in hits[1:]:
                if PERIOD_MIN <= p - block[-1] <= PERIOD_MAX:
                    block.append(p)
                else:
                    blocks.append(block)
                    block = [p]
            blocks.append(block)
            for b in blocks:
                if len(b) < min_spacers + 1:
                    continue
                spacers = []
                for a, c in zip(b, b[1:]):
                    sp = hay[a + len(dr): c]
                    if SPACER_MIN <= len(sp) <= SPACER_MAX:
                        spacers.append(sp)
                if len(spacers) < min_spacers:
                    continue
                arrays.append({
                    "sequence": name, "strand": strand,
                    "start": b[0], "end": b[-1] + len(dr),
                    "n_dr": len(b), "n_spacers": len(spacers),
                    "span": b[-1] + len(dr) - b[0], "spacers": spacers})
    arrays.sort(key=lambda a: -a["n_spacers"])
    return arrays


def dr_conservation(seqs, dr, arrays, max_mm=3):
    """% d'identite moyen des copies du DR au consensus.

    C'est LE discriminant entre un vrai CRISPR (>= 90 %) et un faux positif sur
    sequences repetees (18-30 %), cf. le champ drconservation de CRISPRCasdb.
    """
    ids = []
    for a in arrays:
        hay = seqs[a["sequence"]]
        if a["strand"] == "-":
            hay = rc(hay)
        for p in hamming_positions(hay[a["start"]:a["end"] + len(dr)], dr, max_mm):
            w = hay[a["start"] + p: a["start"] + p + len(dr)]
            if len(w) == len(dr):
                ids.append(100.0 * sum(1 for x, y in zip(w, dr) if x == y) / len(dr))
    return round(statistics.mean(ids), 1) if ids else 0.0


# Adaptateurs de sequencage les plus courants. Sur un run non trimme, ce sont
# EUX les k-mers les plus sur-representes, bien avant tout DR (constate sur
# ERR015598, run de 2010 : les 5 premiers candidats contenaient AGATCGGAAGAGC).
ADAPTERS = ("AGATCGGAAGAGCACACGTCTGAACTCCAGTCA",   # TruSeq, lecture 1 (extrait le 2026-08-04
                                                   # : "AGATCGGAAGAGC" seul (13 nt) laissait
                                                   # passer une continuation de l'adaptateur
                                                   # lue en decalage, ex. DR candidat
                                                   # `AAGAGCACACGTCTGAACTCC` sur SRR1173725,
                                                   # fragment EXACT de cette sequence complete)
            "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT",   # TruSeq, lecture 2
            "CTGTCTCTTATACACATCTCCGAGCCCACGAGAC",  # Nextera (etendue)
            "AATGATACGGCGACCACCGAGATCTACACTCTTTCCCTACACGACGCTCTTCCGATCT",  # P5 (etendue)
            "CAAGCAGAAGACGGCATACGAGATCGGTCTCGGCATTCCTGCTGAACCGCTCTTCCGATCT")  # P7 (etendue,
                                                   # remplace l'ancienne forme tronquee a 21 nt
                                                   # qui manquait le spacer `TCAAGCAGAAGACG
                                                   # GCATACG` trouve tel quel sur ERR181314)


def is_adapter(s, min_window=13):
    """Un candidat peut etre un FRAGMENT DECALE d'un adaptateur, pas l'adaptateur
    entier depuis sa position 0 : constate sur ERR551762, ou le DR candidat
    dominant etait `TCTCTTATACACATCTCCGAGCCCACGAG`, soit l'adaptateur Nextera
    `CTGTCTCTTATACACATCT` PRIVE de ses 3 premiers nt (lecture qui a demarre en
    plein milieu de l'adaptateur) puis etendu sur du bruit de sequencage. Le
    test `probe[:L] in s` d'origine ne comparait que le PREFIXE fixe de
    l'adaptateur et ratait donc tout decalage. On fait glisser une fenetre sur
    l'adaptateur entier et on teste chaque fenetre contre s."""
    for a in ADAPTERS:
        for probe in (a, rc(a)):
            for w in range(min_window, len(probe) + 1):
                for i in range(len(probe) - w + 1):
                    if probe[i:i + w] in s:
                        return True
    return False


def low_complexity(s, max_base_frac=0.55, min_distinct_3mers=0.45):
    """Ecarte homopolymeres et repetitions simples.

    Indispensable sur des lectures : les k-mers les plus frequents d'un jeu de
    reads sont des artefacts de sequencage (`AAAAA...`, adaptateurs), qui
    dominent tout critere de sur-representation. Constate sur ERR015598, dont le
    premier candidat brut etait un homopolymere poly-A.
    """
    if not s:
        return True
    if max(Counter(s).values()) / len(s) > max_base_frac:
        return True
    tri = {s[i:i + 3] for i in range(len(s) - 2)}
    return len(tri) / max(1, len(s) - 2) < min_distinct_3mers


def _context_scores(sub_seqs, candidats, kmer_len, frag_len=10):
    """Score de diversite de contexte pour CHAQUE candidat, en UNE SEULE passe
    sur le sous-echantillon (pas une recherche par candidat : cout independant
    du nombre de candidats).

    Substitut au critere de PERIODICITE (P10.1, mode genome), inapplicable ici
    (une lecture courte ne peut pas contenir deux DR, cf. docstring appelant).
    L'idee equivalente sur des lectures : un vrai DR CRISPR est suivi d'un
    contexte DIFFERENT a chaque occurrence (les spacers varient), alors qu'un
    motif generique tres copie (rRNA, IS6110, MIRU-VNTR) est suivi d'un
    contexte quasi IDENTIQUE partout (dominance ecrasante d'un seul groupe) —
    exactement le discriminant `spacer_diversity` de P10.1, transpose aux
    lectures via le `dominance` deja utilise dans `analyse()`.

    Chaque k-mer candidat n'est en general qu'un FRAGMENT decale du DR (36 nt
    pour III-A, k-mer de 21 nt) : si le decalage tombe pres du debut du DR, le
    "contexte suivant" contient encore du DR conserve et le score sous-estime
    la diversite reelle. Sans consequence en pratique : le comptage initial
    genere plusieurs decalages du meme DR sous-jacent (pas de 3 sur 36 nt), il
    suffit qu'UN SEUL tombe pres de la frontiere DR/spacer pour que ce DR
    remonte en tete du tri.
    """
    groups = defaultdict(lambda: defaultdict(int))
    for s in sub_seqs:
        for hay in (s, rc(s)):
            for i in range(0, len(hay) - kmer_len + 1):
                k = hay[i:i + kmer_len]
                kc = min(k, rc(k))
                if kc in candidats:
                    frag = hay[i + kmer_len: i + kmer_len + frag_len]
                    if len(frag) >= frag_len:
                        groups[kc][frag] += 1
    scores = {}
    for kc, frags in groups.items():
        counts = list(frags.values())
        total = sum(counts)
        if total < 4:                    # trop peu vu dans le sous-echantillon : pas fiable
            continue
        dominance = max(counts) / total
        scores[kc] = len(frags) * (1 - dominance)
    return scores


def detect_dr_reads(path, kmer=21, sample=400000, top=5, min_ratio=4.0,
                    max_ratio=120.0):
    """Decouvre le DR depuis des READS COURTS.

    Le critere de PERIODICITE utilise sur un genome ne s'applique pas ici : une
    lecture de ~75 nt ne peut pas contenir deux DR (36 + 37 + 36 = 109 nt), donc
    aucun ecart DR-DR n'est observable. Le critere qui marche sur des lectures
    est la SUR-REPRESENTATION : a couverture C, un k-mer en copie unique sort ~C
    fois, un DR present en n copies sort ~n x C fois. On cherche donc les k-mers
    dont la frequence depasse largement la mediane, puis on valide chaque
    candidat en tentant de reconstruire des spacers.

    SELECTION DES CANDIDATS A ETENDRE (corrige, piste P10.2). Trier `hot` par
    frequence brute et s'arreter aux `top` premiers ECHOUE sur un vrai run :
    mesure sur ERR5104570, le k-mer du DR III-A (21-27x la mediane) se classe
    au rang ~4340 sur 3,8 millions de k-mers, tres au-dela de tout quota
    praticable — plus de 3000 motifs (rRNA, IS6110, PE/PPE probables) sont a la
    fois dans la fourchette [min_ratio, max_ratio] ET plus frequents que lui.
    Le tri se fait donc desormais sur `_context_scores` (diversite du contexte
    aval, cf. ci-dessus), pas sur la frequence : la frequence ne sert plus qu'a
    fixer la fourchette [min_ratio, max_ratio] a examiner.
    """
    cnt = Counter()
    for s in iter_seqs(path, sample):
        for i in range(0, len(s) - kmer + 1, 3):        # pas de 3 : 3x plus rapide
            k = s[i:i + kmer]
            if "N" not in k:
                cnt[min(k, rc(k))] += 1
    if not cnt:
        return []
    freqs = [c for c in cnt.values() if c >= 3]
    if not freqs:
        return []
    med = statistics.median(freqs)
    # BORNE SUPERIEURE sur la sur-representation, aussi necessaire que la borne
    # inferieure. Un DR present en n copies dans un genome sort a environ n fois
    # la couverture mediane, et n vaut au plus ~70 chez le MTBC (record du locus
    # DR complet). Un k-mer a 180-230x la mediane n'est donc PAS un DR : c'est
    # du materiel non genomique. Constate sur ERR5104570, ou les 24 premiers
    # candidats etaient des k-mers de VECTEUR a 180-230x — on y reconnait
    # l'origine de replication de pUC/pBR322 (`GGATCTAGGTGAAGATCCTTTTTGATAATCT
    # CATG`) — qui saturaient entierement le classement par frequence et
    # repoussaient le vrai DR III-A hors du quota. `is_adapter` ne les voit pas :
    # il ne connait que les adaptateurs Illumina, pas les plasmides.
    hot = [(k, c) for k, c in cnt.items()
           if max(10, min_ratio * med) <= c <= max_ratio * med
           and not low_complexity(k) and not is_adapter(k)]
    # etend les meilleurs candidats en consensus, sur un sous-echantillon
    sub = {f"r{i}": s for i, s in enumerate(iter_seqs(path, 60000))}
    scores = _context_scores(sub.values(), {k for k, _ in hot}, kmer)
    hot.sort(key=lambda x: -scores.get(x[0], -1.0))      # diversite de contexte, pas frequence
    out, seen, n_graines = [], set(), 0
    for k, c in hot[:120]:
        dr = extend_consensus(sub, k)
        # RE-FILTRER apres extension, pas seulement sur le kmer de depart. Le
        # kmer initial peut etre propre (21 nt biologiques) alors que le
        # consensus etendu absorbe un adaptateur voisin dans le read : constate
        # sur un lot de 151 souches canettii, ou ~14 % des DR "detectes" en
        # etaient un une fois etendus (ex. graine propre -> DR final
        # `TTTTTTTTTTCAAGCAGAAGACGGCATACGAGAT...`, adaptateur P7 complet).
        if low_complexity(dr) or is_adapter(dr):
            continue
        key = min(dr, rc(dr))
        if key in seen or any(dr in s or s in dr or rc(dr) in s for s in seen):
            continue
        seen.add(key)
        out.append({"kmer": k, "count": c, "ratio_median": round(c / med, 1), "dr": dr})
        # EXTENSION AYANT ATTEINT LA BORNE : garder aussi la graine NUE.
        # Sur des lectures, les contextes d'une occurrence sont peu nombreux
        # (le sous-echantillon de 60 000 lectures ne porte le motif que quelques
        # fois) et peuvent tous provenir du MEME endroit du genome. Leurs flancs
        # sont alors identiques, l'extension ne rencontre aucune colonne
        # variable et court jusqu'a `max_len` — elle absorbe un spacer entier, et
        # le DR ainsi rallonge ne retrouve plus qu'une poignee de lectures.
        # Constate sur le temoin positif ERR5104570 : DR rendu de 50 nt, soit
        # exactement la borne, et 2 spacers au lieu de 30. Un vrai DR s'arrete de
        # lui-meme avant la borne ; l'atteindre est donc un signal, pas un
        # resultat. On laisse le score d'array arbitrer entre les deux formes
        # plutot que de trancher ici, ce qui ne coute qu'un candidat de plus et
        # seulement dans le cas suspect.
        n_graines += 1
        if len(dr) >= 50 and min(k, rc(k)) not in seen:
            seen.add(min(k, rc(k)))
            out.append({"kmer": k, "count": c, "ratio_median": round(c / med, 1),
                        "dr": k, "extension_bornee": True})
        # Le quota `top` compte les GRAINES examinees, pas les candidats emis :
        # une graine suspecte en produit deux, et sans cette distinction elle
        # consommerait deux places. Le vrai DR III-A sortant au rang 7 sur le
        # temoin positif, quelques graines suspectes suffiraient a le repousser
        # hors du quota — on recreerait le defaut que le passage de top=5 a
        # top=12 avait corrige le 2026-08-09.
        if n_graines >= top:
            break
    return out


def _open_text(path):
    """Ouvre un fichier local OU une URL http(s), gzip ou non, en flux texte.

    Le streaming HTTP evite d'ecrire les lectures sur disque : sur un lot de 150
    souches cela represente ~40 Go qu'il faudrait ensuite supprimer, et le
    repertoire temporaire peut etre un tmpfs (donc de la RAM) ou `gio trash` ne
    fonctionne meme pas. Avec `--limit`, on ne telecharge en outre que le debut
    du fichier.
    """
    p = str(path)
    if p.startswith(("http://", "https://", "ftp://")):
        import urllib.request
        r = urllib.request.urlopen(p, timeout=180)
        return gzip.open(r, "rt") if p.endswith(".gz") else r
    return (gzip.open if p.endswith(".gz") else open)(p, "rt")


def iter_seqs(path, limit=None):
    """Itere les sequences sans tout charger (indispensable sur des reads).

    Accepte aussi une LISTE de sequences deja en memoire, ce qui permet de
    mettre en cache le debut d'un flux HTTP et d'y faire plusieurs passes sans
    retelecharger.
    """
    if isinstance(path, list):
        for i, s in enumerate(path):
            if limit and i >= limit:
                return
            yield s
        return
    n = 0
    with _open_text(path) as f:
        # Detection du format SANS seek : un flux HTTP n'est pas rembobinable.
        # Un flux HTTP coupe en cours (connexion perdue avant --limit lectures : mesure sur
        # mp le 2026-09-22, route EBI a debit plafonne ~60 Ko/s et parfois interrompue avant
        # le marqueur de fin gzip) leve `EOFError`/`OSError` au milieu de la lecture -- traiter
        # comme une fin de flux (donnees partielles exploitables), jamais comme un crash : le
        # nombre de lectures deja obtenues reste un echantillon valide, juste plus petit que
        # prevu.
        try:
            first = f.readline()
        except (EOFError, OSError):
            return
        if not first:
            return
        if first.startswith("@"):                       # FASTQ
            i = 0                                       # la 1re ligne (header) est lue
            try:
                for line in f:
                    i += 1
                    # apres le header, les sequences sont aux lignes 1, 5, 9...
                    if i % 4 == 1:
                        yield line.strip().upper()
                        n += 1
                        if limit and n >= limit:
                            return
            except (EOFError, OSError):
                return
            return
        else:                                           # FASTA
            buf = []
            try:
                rest = [first] + list(f)
            except (EOFError, OSError):
                rest = [first]
            for line in rest:
                if line.startswith(">"):
                    if buf:
                        yield "".join(buf).upper()
                        n += 1
                        if limit and n >= limit:
                            return
                        buf = []
                else:
                    buf.append(line.rstrip())
            if buf:
                yield "".join(buf).upper()


def spacers_from_reads(path, dr, min_support=5, limit=None, max_mm=2):
    """Reconstruit les spacers depuis des reads COURTS.

    Pourquoi ce n'est pas `extract_arrays` : sur des lectures de ~75 nt, un
    spacer complet ne peut PAS tenir entre deux DR (36 + 37 + 36 = 109 nt).
    Chercher des DR consecutifs dans un read ne rend donc jamais rien, et c'est
    exactement pour cela que CRISPRbuilder-TB assemble avant d'annoter.

    Methode : on collecte les fragments qui SUIVENT un DR (au plus SPACER_MAX
    nt), on les regroupe par leur prefixe, puis on reconstruit chaque spacer par
    consensus colonne par colonne. Le spacer s'arrete des que le DR suivant
    commence. Le support (nombre de lectures) filtre le bruit de sequencage.
    """
    groups = defaultdict(list)
    seed = dr[:12]
    rseed = rc(dr)[:12]
    n_reads = n_hit = 0
    for s in iter_seqs(path, limit):
        n_reads += 1
        for hay in ((s,) if seed in s or rseed in s else ()):
            pass
        for hay in (s, rc(s)):
            if seed not in hay:
                continue
            for p in hamming_positions(hay, dr, max_mm):
                frag = hay[p + len(dr): p + len(dr) + SPACER_MAX + len(seed)]
                if len(frag) >= 16:
                    groups[frag[:10]].append(frag)
                    n_hit += 1
    spacers = []
    for frags in groups.values():
        if len(frags) < min_support:
            continue
        cons = []
        for i in range(max(len(f) for f in frags)):
            col = [f[i] for f in frags if len(f) > i]
            if len(col) < min_support:
                break
            b, c = Counter(col).most_common(1)[0]
            if c / len(col) < 0.7:
                break
            cons.append(b)
        sp = "".join(cons)
        cut = sp.find(dr[:10])                  # le DR suivant borne le spacer
        if cut > 0:
            sp = sp[:cut]
        if SPACER_MIN <= len(sp) <= SPACER_MAX:
            spacers.append({"spacer": sp, "support": len(frags)})
    # deduplique les spacers inclus les uns dans les autres
    spacers.sort(key=lambda d: -len(d["spacer"]))
    kept = []
    for s in spacers:
        if not any(s["spacer"] in k["spacer"] for k in kept):
            kept.append(s)
    return {"n_reads_scanned": n_reads, "n_dr_hits": n_hit,
            "n_spacers": len(kept),
            "spacers": sorted(kept, key=lambda d: -d["support"])}


def analyse(path, dr=None, source="genome", kmer=21, sample=None, max_mm=3,
            limit=None, min_support=5):
    if source == "reads":
        # Sur une URL, chaque passe relancerait un telechargement complet : on
        # met donc en cache en MEMOIRE le debut du flux (une seule fois), on y
        # fait toute la detection, et on ne relit le flux qu'une fois pour
        # l'extraction finale.
        if str(path).startswith(("http", "ftp")):
            buf = list(iter_seqs(path, sample or 400000))
            src_detect = buf
        else:
            src_detect = path
        cands = []
        if dr is None:
            # TOP ELARGI SUR READS (12 au lieu de 5, correctif 2026-08-09). Le classement
            # de detect_dr_reads se fait sur la FREQUENCE brute, et chez le MTBC les unites
            # MIRU-VNTR saturent les premieres places : ~12 sites disperses du genome, 2-3
            # unites en tandem par site, ce qui donne plus de lectures porteuses que le DR
            # CRISPR lui-meme (2196 contre 803 sur SRR28170812). Mesure sur cette souche :
            # le vrai DR III-A sort au RANG 7 - donc invisible avec top=5 - alors que son
            # score d'array (24,4) ecrase celui de tous les concurrents MIRU (4,0 au mieux).
            # La validation par array_score qui suit fait donc bien son travail : il
            # suffisait de lui donner le bon candidat a juger. Avec top=5, un M. canettii
            # porteur d'un III-A canonique a ete pris pour un "nouveau systeme CRISPR".
            cands = detect_dr_reads(src_detect, kmer=kmer, sample=sample or 400000, top=12)
            if not cands:
                return {"input": str(path), "source": "reads",
                        "status": "no_dr_found", "n_spacers": 0}
            # Valider chaque candidat en reconstruisant : le vrai DR en rend le
            # plus. Sur un sous-echantillon reduit : 5 candidats x 1,5 M lectures
            # feraient 7,5 M de lectures scannees pour un simple departage.
            for c in cands:
                t = spacers_from_reads(src_detect, c["dr"],
                                       min_support=max(2, min_support // 2),
                                       limit=300000)
                c["n_spacers_test"] = t["n_spacers"]
                c["hit_ratio"] = t["n_dr_hits"] / max(1, t["n_reads_scanned"])
                # DOMINANCE : un site genomique UNIQUE tres couvert (faux DR,
                # ex. duplication, element repete non-CRISPR) produit un seul
                # "spacer" au support ecrasant, car il n'a qu'un seul contexte
                # aval. Un vrai array CRISPR produit PLUSIEURS spacers a
                # supports comparables. Constate sur ERR5104570 : un motif
                # genomique concurrent (691 occurrences vs 74 pour le DR
                # III-A dans les k-mers germes) gagnait le classement par
                # frequence brute alors qu'il ne rendait qu'1 spacer a
                # dominance 100 % - le vrai DR III-A en rend 30, repartis.
                sup = [s["support"] for s in t["spacers"]]
                c["dominance"] = (max(sup) / sum(sup)) if sup else 1.0
                lens = [len(s["spacer"]) for s in t["spacers"]]
                c["len_std"] = statistics.pstdev(lens) if len(lens) >= 2 else 0.0
            # GARDE-FOU 1 : un vrai DR CRISPR occupe ~30 copies x 36 nt sur un
            # genome de 4,4 Mb, donc une fraction infime des lectures d'un run
            # WGS. Un candidat present dans plus de 1 % des lectures scannees
            # est un motif GENERIQUE (adaptateur non catalogue, index de
            # multiplexage). Constate sur le lot canettii (10/151 candidats
            # geants ecartes ainsi).
            cands = [c for c in cands if c["hit_ratio"] <= 0.01] or cands
            # GARDE-FOU 3 (piste P10.2, 2026-08-10) : un vrai array CRISPR
            # contraint fortement la longueur du spacer (mecanisme
            # d'acquisition) — 35-41 nt pour le III-A, ecart-type de
            # quelques nt tout au plus. Constate sur ERR5104570 apres le
            # premier correctif de la selection de graine (score de diversite
            # de contexte, ci-dessus) : celui-ci faisait remonter un motif
            # PE-PGRS (`CCGCCGGCGCCGCCGTTGCCG`, signature GC caracteristique,
            # cf. l'artefact deja documente en P6/P10.1) qui produit 74
            # "spacers" nombreux et divers en SEQUENCE (bon score de
            # diversite, bonne dominance) mais de longueur INCOHERENTE
            # (20 a 60 nt, ecart-type ~13 sur un echantillon des spacers a
            # plus fort support) — pas un array CRISPR, un gene repete a
            # motifs Gly-Ala-Pro degenere entre copies. Filtre DUR plutot
            # qu'une penalite continue : une penalite proportionnelle au
            # coefficient de variation ne suffisait pas a compenser le
            # nombre brut de spacers (74 contre ~30) dans le score.
            coherents = [c for c in cands if c["len_std"] <= 8.0]
            if coherents:
                cands = coherents
            # GARDE-FOU 2 : score de qualite d'array = nombre de spacers
            # PONDERE par la diversite (1 - dominance). Un candidat a 1 seul
            # spacer dominant a un score nul quel que soit son support brut.
            for c in cands:
                c["array_score"] = c["n_spacers_test"] * (1 - c["dominance"])
            cands.sort(key=lambda c: -c["array_score"])
            dr = cands[0]["dr"]
        res = spacers_from_reads(path, dr, min_support=min_support, limit=limit)
        if cands:
            res["dr_candidates"] = cands
        # .update(), pas |= (PEP 584, Python 3.9+ seulement) : mp tourne encore en 3.8.10,
        # mesure le 2026-09-22 -- deploiement A5.1a phase 2, TypeError a l'etape finale apres
        # une extraction reseau autrement reussie.
        res.update({"input": str(path), "source": "reads", "dr": dr,
                    "dr_length": len(dr),
                    "status": "ok" if res["n_spacers"] else "dr_found_but_no_spacer"})
        return res
    seqs = read_fasta(path)
    res = {"input": str(path), "source": source, "n_sequences": len(seqs),
           "total_bp": sum(len(s) for s in seqs.values())}
    if dr is None:
        cands = detect_dr(seqs, kmer=kmer, sample=sample)
        # **-unpacking, pas | (PEP 584, Python 3.9+ seulement) : compatible 3.8 (mp).
        res["dr_candidates"] = [{**{k: v for k, v in c.items() if k != "dr"}, "dr": c["dr"]}
                                for c in cands]
        if not cands:
            res["status"] = "no_dr_found"
            res["arrays"] = []
            return res
        dr = cands[0]["dr"]
    res["dr"] = dr
    res["dr_length"] = len(dr)
    arrays = extract_arrays(seqs, dr, max_mm=max_mm)
    res["arrays"] = arrays
    res["n_arrays"] = len(arrays)
    res["n_spacers_total"] = sum(a["n_spacers"] for a in arrays)
    res["dr_conservation"] = dr_conservation(seqs, dr, arrays, max_mm)
    res["status"] = "ok" if arrays else "dr_found_but_no_array"
    return res


CATALOGUE = Path(__file__).resolve().parent.parent / "data" / "dr_genres_ev4.tsv"


def charger_catalogue(chemin=None):
    """{DR: (n_loci, [genres])} depuis le catalogue tire de CRISPRCasdb."""
    chemin = Path(chemin or CATALOGUE)
    if not chemin.exists():
        return {}
    cat = {}
    with open(chemin) as f:
        next(f, None)
        for ligne in f:
            ch = ligne.rstrip("\n").split("\t")
            if len(ch) < 4:
                continue
            cat[ch[0].upper()] = (int(ch[1]), ch[3].split("|"))
    return cat


def genre_du_dr(dr, cat, max_mm=3):
    """Genres portant ce DR : exact d'abord, sinon le plus proche a max_mm pres.

    Les deux brins sont interroges : l'outil rend le DR dans le sens ou il l'a
    vu, qui n'est pas celui de la nomenclature de reference.
    """
    # Les DEUX orientations peuvent figurer au catalogue, avec des effectifs tres
    # inegaux (le DR du MTBC : 981 loci dans un sens, 29 dans l'autre, selon
    # l'orientation rendue par CRISPRCasFinder sur chaque genome). Retenir la
    # mieux documentee, sans quoi le compte de loci rapporte sous-estime la
    # certitude de l'attribution.
    exacts = [(cat[c][0], c) for c in (dr.upper(), rc(dr.upper())) if c in cat]
    if exacts:
        n, cand = max(exacts)
        return {"appariement": "exact", "dr_reference": cand,
                "n_loci": n, "genres": cat[cand][1], "mismatches": 0}
    meilleur = None
    for cand in (dr.upper(), rc(dr.upper())):
        for ref, (n, g) in cat.items():
            if len(ref) != len(cand):
                continue
            mm = sum(1 for a, b in zip(ref, cand) if a != b)
            if mm <= max_mm and (meilleur is None or mm < meilleur["mismatches"]):
                meilleur = {"appariement": "approche", "dr_reference": ref,
                            "n_loci": n, "genres": g, "mismatches": mm}
    return meilleur or {"appariement": "aucun", "dr_reference": None,
                        "n_loci": 0, "genres": [], "mismatches": None}


def qc_contamination(chemin, attendu, source="genome", taille_attendue=None,
                     catalogue=None, kmer=21, top=3):
    """Le CRISPR comme detecteur de contamination (piste P10.4).

    Un locus CRISPR est un marqueur taxonomique a haute resolution et quasi
    gratuit : son DR est propre a un clade. Un DR d'un AUTRE genre que celui
    attendu trahit un melange qu'un mapping contre la reference de l'espece
    attendue ne verra jamais, puisque les lectures du contaminant ne mappent pas
    et disparaissent en silence.

    Cas fondateur : ERR266123, etiquete *M. canettii*, rend un array de 40
    spacers sur le DR `GTTCACTGCCGTGTAGGCAGCTAAGAAA` — celui du systeme I-F de
    *Pseudomonas aeruginosa*, present dans 58 loci de CRISPRCasdb et chez ce
    seul genre. Confirmation independante : son assemblage faisait 10,8 Mb, soit
    2,45 fois un genome de mycobacterie. Les deux signaux sont donc rendus ici,
    car ils sont independants et se confortent.
    """
    cat = charger_catalogue(catalogue)
    res = analyse(chemin, source=source, kmer=kmer)
    alertes, verdict = [], "OK"

    if not cat:
        alertes.append("catalogue de DR absent : le controle taxonomique est desactive")
        verdict = "INDETERMINE"

    if source == "genome" and taille_attendue:
        taille = res.get("total_bp", 0)
        ratio = taille / taille_attendue if taille_attendue else 0
        res["taille_ratio"] = round(ratio, 2)
        if ratio > 1.5:
            alertes.append(f"assemblage {ratio:.2f}x la taille attendue "
                           f"({taille:,} nt) : melange probable")
            verdict = "SUSPECT"
        elif ratio < 0.7:
            alertes.append(f"assemblage {ratio:.2f}x la taille attendue : "
                           f"assemblage incomplet, prudence sur les absences")

    controles = []
    for c in (res.get("dr_candidates") or [])[:top]:
        info = genre_du_dr(c["dr"], cat) if cat else {}
        controles.append({"dr": c["dr"], "validation_score": c.get("validation_score"),
                          **info})
    if not controles and res.get("dr"):
        controles.append({"dr": res["dr"], **(genre_du_dr(res["dr"], cat) if cat else {})})
    res["controle_taxonomique"] = controles

    principal = controles[0] if controles else None
    if principal and principal.get("genres"):
        if attendu not in principal["genres"]:
            alertes.append(
                f"le DR dominant appartient a {', '.join(principal['genres'])} "
                f"et non a {attendu} (appariement {principal['appariement']}, "
                f"{principal['n_loci']} loci de reference)")
            verdict = "SUSPECT"
    elif principal and principal.get("appariement") == "aucun":
        alertes.append("le DR dominant n'est dans aucun genre de reference : "
                       "systeme inconnu, ou faux positif — a examiner, pas a conclure")
        if verdict == "OK":
            verdict = "INDETERMINE"

    # Un DR d'un AUTRE genre en second rang est le signal le plus specifique :
    # un melange laisse les deux loci visibles a la fois.
    etrangers = [c for c in controles[1:]
                 if c.get("genres") and attendu not in c["genres"]]
    if etrangers:
        alertes.append(
            "DR supplementaire(s) d'un autre genre, signature d'un melange : "
            + " ; ".join(f"{c['dr']} -> {', '.join(c['genres'])}" for c in etrangers))
        verdict = "SUSPECT"

    res["genre_attendu"] = attendu
    res["alertes"] = alertes
    res["verdict_qc"] = verdict
    return res


class _BatchTimeout(Exception):
    """Levee par `_raise_timeout` quand un element de `batch` depasse --timeout.

    SIGALRM (Unix uniquement) plutot qu'un sous-processus : `batch` appelle
    `analyse()` en mémoire, dans le même interpréteur, pour éviter le coût
    d'un `python3 crisprbuilder2.py extract ...` par élément (le lancement de
    l'interpréteur et le rechargement des modules dominent le temps d'exécution
    sur un petit génome). Un incident concret a motivé l'ajout : sur un lot de
    21 assemblages *M. canettii*, un appelant externe sans connaissance du
    budget interne de l'outil a du écrire un script de contournement (boucle
    shell, `timeout 300` par génome, exécution en arrière-plan) faute d'un
    garde-fou intégré à `batch` — exactement ce que ce paramètre évite.
    """


def _raise_timeout(signum, frame):
    raise _BatchTimeout()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("detect", "extract"):
        p = sub.add_parser(name)
        g = p.add_mutually_exclusive_group(required=True)
        g.add_argument("--genome")
        g.add_argument("--reads")
        p.add_argument("--dr", help="DR connu ; sinon decouverte de novo")
        p.add_argument("--kmer", type=int, default=21)
        p.add_argument("--max-mm", type=int, default=3)
        p.add_argument("--sample", type=int, default=200000,
                       help="nb de lectures echantillonnees pour la detection du DR")
        p.add_argument("--limit", type=int,
                       help="nb max de lectures scannees pour l'extraction")
        p.add_argument("--min-support", type=int, default=5,
                       help="nb minimal de lectures soutenant un spacer")
        p.add_argument("--json")
        p.add_argument("--fasta", help="ecrit les spacers du plus grand array")
    p = sub.add_parser("batch")
    p.add_argument("--glob", required=True)
    p.add_argument("--dr")
    p.add_argument("--kmer", type=int, default=21)
    p.add_argument("--max-mm", type=int, default=3)
    p.add_argument("--json", required=True)
    p.add_argument("--timeout", type=int, default=300,
                   help="secondes max par element avant de passer au suivant "
                        "(0 = pas de limite). La decouverte de novo en mode "
                        "genome peut prendre plusieurs minutes sur un genome "
                        "ou un k-mer concurrent est tres repete ; sans limite, "
                        "UN element lent bloque tout le lot indefiniment.")
    p = sub.add_parser("qc", help="le CRISPR comme detecteur de contamination")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--genome")
    g.add_argument("--reads")
    p.add_argument("--attendu", required=True,
                   help="genre attendu, ex. Mycobacterium")
    p.add_argument("--taille-attendue", type=int,
                   help="taille de genome attendue en nt, ex. 4400000")
    p.add_argument("--catalogue", help="TSV DR -> genres (defaut : data/dr_genres_ev4.tsv)")
    p.add_argument("--kmer", type=int, default=21)
    p.add_argument("--json")
    args = ap.parse_args()

    if args.cmd == "qc":
        res = qc_contamination(args.genome or args.reads, args.attendu,
                               source="genome" if args.genome else "reads",
                               taille_attendue=args.taille_attendue,
                               catalogue=args.catalogue, kmer=args.kmer)
        print(f"verdict : {res['verdict_qc']}   (genre attendu : {args.attendu})")
        if res.get("taille_ratio"):
            print(f"taille de l'assemblage : {res['taille_ratio']}x l'attendu")
        for c in res.get("controle_taxonomique", []):
            genres = ", ".join(c.get("genres") or []) or "inconnu"
            print(f"  DR {c['dr'][:44]:<44} -> {genres}"
                  f"  [{c.get('appariement')}, {c.get('n_loci', 0)} loci]")
        for a in res["alertes"]:
            print(f"  ! {a}")
        if not res["alertes"]:
            print("  aucun signal de contamination")
        if args.json:
            Path(args.json).write_text(json.dumps(res, indent=1))
        return

    if args.cmd == "batch":
        import glob as g
        paths = sorted(g.glob(args.glob))
        out = []
        for i, pth in enumerate(paths, 1):
            print(f"[{i}/{len(paths)}] {pth}", file=sys.stderr)
            if args.timeout:
                signal.signal(signal.SIGALRM, _raise_timeout)
                signal.alarm(args.timeout)
            try:
                r = analyse(pth, dr=args.dr, kmer=args.kmer, max_mm=args.max_mm)
            except _BatchTimeout:
                r = {"input": pth, "status": "error",
                     "error": f"timeout apres {args.timeout}s"}
                print(f"    -> timeout apres {args.timeout}s, element suivant",
                      file=sys.stderr)
            except Exception as e:                       # noqa: BLE001
                r = {"input": pth, "status": "error", "error": str(e)}
            finally:
                if args.timeout:
                    signal.alarm(0)
            r.pop("arrays", None) if r.get("status") == "error" else None
            out.append(r)
            Path(args.json).write_text(json.dumps(out, indent=1))   # ecrit au fil de l'eau
        ok = sum(1 for r in out if r.get("status") == "ok")
        print(f"\n{ok}/{len(out)} avec array ; ecrit dans {args.json}")
        return

    src = "genome" if args.genome else "reads"
    res = analyse(args.genome or args.reads, dr=args.dr, source=src,
                  kmer=args.kmer, sample=args.sample if src == "reads" else None,
                  max_mm=args.max_mm, limit=getattr(args, "limit", None),
                  min_support=getattr(args, "min_support", 5))
    if args.cmd == "detect":
        for c in res.get("dr_candidates", []):
            print(f"valid {c.get('validation_score', 0):>7}  spacers {c.get('n_spacers_found', 0):>4}"
                  f"  conserv {c.get('dr_conservation', 0):>6} %  gap {c['median_gap']:>5}"
                  f"  regul {c['regularity']}\n    {c['dr']}")
        if not res.get("dr_candidates"):
            print("aucun DR candidat")
    elif res.get("source") == "reads":
        print(f"DR ({res.get('dr_length')} nt) : {res.get('dr')}")
        print(f"lectures scannees : {res.get('n_reads_scanned', 0):,}"
              f" | portant le DR : {res.get('n_dr_hits', 0):,}")
        print(f"spacers reconstruits : {res.get('n_spacers', 0)}")
        for s in res.get("spacers", [])[:8]:
            print(f"  support {s['support']:>5}  {s['spacer']}")
        if args.fasta and res.get("spacers"):
            Path(args.fasta).write_text(
                "".join(f">{Path(res['input']).stem}_sp{i}_sup{s['support']}\n{s['spacer']}\n"
                        for i, s in enumerate(res["spacers"], 1)))
            print(f"  spacers ecrits dans {args.fasta}")
    else:
        print(f"DR ({res.get('dr_length')} nt) : {res.get('dr')}")
        print(f"conservation DR : {res.get('dr_conservation')} %")
        print(f"arrays : {res.get('n_arrays')} | spacers : {res.get('n_spacers_total')}")
        for a in res.get("arrays", [])[:5]:
            print(f"  {a['sequence']} brin {a['strand']} {a['start']}-{a['end']}"
                  f" ({a['span']} nt) : {a['n_dr']} DR, {a['n_spacers']} spacers")
        if args.fasta and res.get("arrays"):
            big = res["arrays"][0]
            Path(args.fasta).write_text(
                "".join(f">{Path(res['input']).stem}_sp{i}\n{s}\n"
                        for i, s in enumerate(big["spacers"], 1)))
            print(f"  spacers ecrits dans {args.fasta}")
    if args.json:
        Path(args.json).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
