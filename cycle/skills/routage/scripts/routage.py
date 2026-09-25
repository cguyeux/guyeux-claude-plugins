#!/usr/bin/env python3
"""
Objet        : routage modèle/effort par piste et mesure de la consommation du forfait Claude.
               Sous-commandes : etat, estimer, etiqueter, mesurer, tache (start|done), calibrer, maj.
Entrées      : fiche canonique ~/.agents/knowledge/model-routing.md (blocs ```json routage-roster / routage-poids),
               transcripts ~/.claude/projects/<slug>/<session>.jsonl (+ subagents/), échantillons statusline
               ~/.agents/coord/quota/quota.jsonl, journal des tâches ~/.agents/coord/quota/taches.jsonl,
               registres pistes.md / pistes/P*.md d'un projet, doc Anthropic en Markdown (maj).
Sorties      : texte pour l'agent (ou --json), propositions d'étiquettes <projet>/pistes_etiquettes_proposees.md,
               lignes ajoutées à taches.jsonl, blocs JSON de la fiche réécrits (calibrer --apply, maj --apply).
Réutilisable : oui, tout projet ; stdlib seule ; aucun appel LLM.
Projet       : ${CLAUDE_PLUGIN_ROOT}/skills/routage (skill personnel, inter-projets)
Date         : 2026-09-13
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOME = Path.home()
# `pistes` est un skill voisin du meme plugin ; chemin relatif d'abord (portable apres
# clonage/installation), repli sur le skill personnel pour qui n'a que celui-ci.
_PISTES_DIR = next(
    (c for c in (Path(__file__).resolve().parents[2] / "pistes",
                 HOME / ".claude" / "skills" / "pistes") if c.is_dir()),
    HOME / ".claude" / "skills" / "pistes",
)
FICHE = HOME / ".agents/knowledge/model-routing.md"
QUOTA_DIR = HOME / ".agents/coord/quota"
QUOTA_LOG = QUOTA_DIR / "quota.jsonl"
TACHES_LOG = QUOTA_DIR / "taches.jsonl"
PROJECTS = HOME / ".claude/projects"
SETTINGS = HOME / ".claude/settings.json"

TAG_RE = re.compile(r"\[(Haiku|Sonnet|Opus|Fable)(?::(low|medium|high|xhigh|max))?(?:\s*\+(Sonnet|Opus|Fable))?\]")
ETAT_RE = re.compile(r"\[([^\]]{0,24}?)(à faire|en cours|réalisé|abandonné)([^\]]*)\]")
ITEM_RE = re.compile(r"^(\s*)-\s+(P\d+(?:\.[0-9A-Za-z]+)+)\s+(.*)$")
HEAD_RE = re.compile(r"^##\s+(P\d+)\.\s+(.*)$")
FAMILLES = ("Fable", "Opus", "Sonnet", "Haiku")


# ---------------------------------------------------------------- fiche canonique
def _bloc(texte: str, nom: str):
    m = re.search(r"```json " + re.escape(nom) + r"\n(.*?)\n```", texte, re.S)
    if not m:
        raise SystemExit(f"bloc ```json {nom} introuvable dans {FICHE}")
    return m, json.loads(m.group(1))


def charger_fiche():
    texte = FICHE.read_text(encoding="utf-8")
    _, roster = _bloc(texte, "routage-roster")
    _, poids = _bloc(texte, "routage-poids")
    return texte, roster, poids


def sauver_bloc(nom: str, obj) -> None:
    texte = FICHE.read_text(encoding="utf-8")
    m, _ = _bloc(texte, nom)
    nouveau = json.dumps(obj, ensure_ascii=False, indent=2)
    FICHE.write_text(texte[: m.start(1)] + nouveau + texte[m.end(1):], encoding="utf-8")


def journal_fiche(passe: str, constat: str, effet: str = "—") -> None:
    texte = FICHE.read_text(encoding="utf-8")
    ligne = f"| {datetime.now():%Y-%m-%d} | {passe} | {constat} | {effet} |\n"
    if not texte.endswith("\n"):
        texte += "\n"
    FICHE.write_text(texte + ligne, encoding="utf-8")


def famille_de(model_id: str | None) -> str | None:
    if not model_id:
        return None
    low = model_id.lower()
    for fam in FAMILLES:
        if fam.lower() in low:
            return fam
    return None


def prix(roster, famille: str) -> dict:
    for m in roster["modeles"]:
        if m["famille"] == famille:
            return m["prix_usd_mtok"]
    return {"entree": 5.0, "lecture_cache": 0.5, "ecriture_cache_5m": 6.25, "ecriture_cache_1h": 10.0, "sortie": 25.0}


# ---------------------------------------------------------------- session et transcripts
def session_courante(explicit: str | None = None) -> str | None:
    return explicit or os.environ.get("CLAUDE_CODE_SESSION_ID")


def transcript_de(session_id: str) -> Path | None:
    hits = list(PROJECTS.glob(f"*/{session_id}.jsonl"))
    return hits[0] if hits else None


def _ts(rec) -> float | None:
    t = rec.get("timestamp")
    if not t:
        return None
    try:
        return datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def usage_transcript(path: Path, t0: float | None = None, t1: float | None = None) -> dict:
    """Agrège message.usage des messages assistant : par modèle, requêtes et tokens par type.
    Chaque enregistrement assistant porteur de usage = une requête API."""
    par_modele: dict[str, dict] = {}
    n_outils = 0
    n_blocages = 0
    premier = dernier = None
    # Un même message d'assistant est écrit sur PLUSIEURS lignes du transcript, une par bloc de
    # contenu (`apiBlockIndex`), et chacune répète le MÊME objet `usage`. Sans déduplication par
    # `message.id`, une session est surévaluée d'un facteur 1,5 à 2 (mesuré le 2026-09-13 : 202
    # enregistrements pour 113 réponses réelles, 56,6 $-éq calculés contre 34,1 rapportés par le
    # harnais). Le premier chiffrage du dispositif portait ce biais.
    vus: set = set()
    try:
        fh = path.open(encoding="utf-8", errors="replace")
    except OSError:
        return {"par_modele": par_modele, "n_outils": 0, "n_blocages": 0, "debut": None, "fin": None}
    with fh:
        for ligne in fh:
            try:
                rec = json.loads(ligne)
            except Exception:
                continue
            msg = rec.get("message") if isinstance(rec, dict) else None
            if not isinstance(msg, dict) or msg.get("role") != "assistant":
                continue
            ts = _ts(rec)
            if t0 is not None and ts is not None and ts < t0:
                continue
            if t1 is not None and ts is not None and ts > t1:
                continue
            contenu = msg.get("content")
            if isinstance(contenu, list):
                n_outils += sum(1 for b in contenu if isinstance(b, dict) and b.get("type") == "tool_use")
            u = msg.get("usage")
            if not isinstance(u, dict):
                continue
            cle = msg.get("id") or rec.get("requestId") or rec.get("uuid")
            if cle is not None:
                if cle in vus:
                    continue
                vus.add(cle)
            model = msg.get("model") or "?"
            # Enregistrement synthetique : message injecte par le harnais (erreur API, limite
            # atteinte), sans aucun token. Ce n'est pas une requete ; en revanche « hit your
            # limit » est l'evenement qui compte vraiment, on le denombre.
            if model == "<synthetic>" or not any(u.get(k) for k in
                    ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")):
                texte = ""
                if isinstance(contenu, list):
                    for b in contenu:
                        if isinstance(b, dict) and b.get("type") == "text":
                            texte = b.get("text", "")
                            break
                elif isinstance(contenu, str):
                    texte = contenu
                if "hit your" in texte and "limit" in texte:
                    n_blocages += 1
                continue
            d = par_modele.setdefault(model, {"requetes": 0, "entree": 0, "lecture_cache": 0, "ecriture_cache_5m": 0,
                                              "ecriture_cache_1h": 0, "sortie": 0, "reflexion": 0})
            d["requetes"] += 1
            d["entree"] += u.get("input_tokens", 0) or 0
            d["lecture_cache"] += u.get("cache_read_input_tokens", 0) or 0
            cc = u.get("cache_creation") or {}
            if isinstance(cc, dict) and (cc.get("ephemeral_1h_input_tokens") or cc.get("ephemeral_5m_input_tokens")):
                d["ecriture_cache_1h"] += cc.get("ephemeral_1h_input_tokens", 0) or 0
                d["ecriture_cache_5m"] += cc.get("ephemeral_5m_input_tokens", 0) or 0
            else:
                d["ecriture_cache_1h"] += u.get("cache_creation_input_tokens", 0) or 0
            d["sortie"] += u.get("output_tokens", 0) or 0
            det = u.get("output_tokens_details") or {}
            d["reflexion"] += det.get("thinking_tokens", 0) or 0 if isinstance(det, dict) else 0
            if ts is not None:
                premier = ts if premier is None else min(premier, ts)
                dernier = ts if dernier is None else max(dernier, ts)
    return {"par_modele": par_modele, "n_outils": n_outils, "n_blocages": n_blocages,
            "debut": premier, "fin": dernier}


def usage_session(session_id: str, t0=None, t1=None, avec_sous_agents=True) -> dict:
    tp = transcript_de(session_id)
    if not tp:
        return {"erreur": f"transcript introuvable pour {session_id}"}
    principal = usage_transcript(tp, t0, t1)
    sous = {}
    if avec_sous_agents:
        for sa in sorted((tp.parent / session_id / "subagents").glob("agent-*.jsonl")):
            u = usage_transcript(sa, t0, t1)
            if u["par_modele"]:
                sous[sa.stem] = u
    return {"transcript": str(tp), "principal": principal, "sous_agents": sous}


def cout(par_modele: dict, roster, poids) -> tuple[float, dict]:
    total, detail = 0.0, {}
    for model, d in par_modele.items():
        fam = famille_de(model) or "Opus"
        p = prix(roster, fam)
        f = poids["facteur_forfait"].get(fam, 1.0)
        c = (d["entree"] * p["entree"] + d["lecture_cache"] * p["lecture_cache"]
             + d["ecriture_cache_5m"] * p["ecriture_cache_5m"] + d["ecriture_cache_1h"] * p["ecriture_cache_1h"]
             + d["sortie"] * p["sortie"]) / 1e6 * f
        detail[model] = round(c, 3)
        total += c
    return round(total, 3), detail


def fusion(*usages: dict) -> dict:
    out: dict[str, dict] = {}
    for u in usages:
        for model, d in u.items():
            o = out.setdefault(model, {k: 0 for k in d})
            for k, v in d.items():
                o[k] = o.get(k, 0) + v
    return out


# ---------------------------------------------------------------- quota.jsonl
def lire_quota(depuis: float | None = None, jusqua: float | None = None, session: str | None = None) -> list[dict]:
    if not QUOTA_LOG.exists():
        return []
    out = []
    with QUOTA_LOG.open(encoding="utf-8", errors="replace") as fh:
        for ligne in fh:
            try:
                r = json.loads(ligne)
            except Exception:
                continue
            ts = r.get("ts")
            if depuis is not None and ts is not None and ts < depuis:
                continue
            if jusqua is not None and ts is not None and ts > jusqua:
                continue
            if session and r.get("session_id") != session:
                continue
            out.append(r)
    return out


def delta_pourcent(echantillons: list[dict], champ: str) -> float | None:
    """Somme des incréments positifs (une remise à zéro apparaît comme une chute, ignorée)."""
    vals = [(r["ts"], r[champ]) for r in echantillons if r.get(champ) is not None and r.get("ts") is not None]
    if len(vals) < 2:
        return None
    vals.sort()
    total, prev = 0.0, vals[0][1]
    for _, v in vals[1:]:
        if v >= prev:
            total += v - prev
        prev = v
    return round(total, 2)


def dernier_echantillon(session: str | None) -> dict | None:
    ech = lire_quota(session=session) if session else lire_quota()
    return ech[-1] if ech else None


# ---------------------------------------------------------------- estimation
ARCHETYPES = [
    ("A", ["relancer", "régénérer", "regénérer", "renommer", "déplacer", "extraire", "recompter", "reformater",
           "mettre à jour le registre", "mise à jour du registre", "convertir", "réindexer", "reindex", "cocher",
           "archiver", "copier", "lister"]),
    ("B", ["script", "parser", "parseur", "matrice", "tableau", "figure", "csv", "tsv", "statistique", "fisher",
           "comptage", "histogramme", "graphique", "bug", "correctif", "test", "cartographie", "carte",
           "synapomorphie", "marqueur", "alignement", "extraction", "annoter", "annotation",
           "in silico minimale", "in silico minimal", "échantillon", "vérifier sur", "recalculer",
           "recouper", "quantifier", "mesurer", "dénombrer"]),
    ("C", ["pipeline", "refactor", "déboguer", "debug", "cause inconnue", "multi-fichiers", "skill", "hook",
           "outillage", "implémenter", "intégrer", "automatiser", "portage", "migration", "orchestr",
           "reconstruire", "reconstruction", "charpente", "arbre", "phylogén", "raxml", "iqtree", "assembl",
           "subdiviser", "aplatissement", "laminar", "scaffold", "harnais"]),
    ("D", ["revue de littérature", "littérature", "lit-review", "bibliograph", "inventaire", "veille", "recenser",
           "pdf", "lecture", "collecte", "bioproject", "scanner", "explorer", "rechercher", "web"]),
    ("E", ["interpréter", "interprétation", "arbitrer", "hypothèse", "verdict", "état des découvertes", "recadrage",
           "porte 1bis", "porte 3bis", "décider", "trancher", "diagnostic", "expliquer", "mécanisme", "pourquoi",
           "signification", "biologique", "évolutif", "phylogéograph", "datation", "calibration",
           "décision", "go/no-go", "go-no-go", "faut-il", "vaut-il", "opportunité", "conclure", "juger"]),
    ("F", ["rédiger", "rédaction", "manuscrit", "article", "section", "discussion", "introduction", "abstract",
           "réponse aux relecteurs", "reviewer", "plan narratif", "narratif", "latex", "biblio", "figure d'article"]),
    ("H", ["attendre la réponse", "relancer", "mail", "courriel", "écrire à", "contacter", "ticket",
           "demander un", "demander une", "demander à", "invitation", "inscription", "compte", "accès",
           "qos", "quota", "convention", "réunion", "visio", "rendez-vous"]),
    ("G", ["méthode inédite", "nouvelle méthode", "architecture", "artefact", "frontière", "autonome",
           "de zéro", "from scratch", "preuve", "démonstration", "théorème", "modèle nul", "inférence bayésienne", "beast"]),
]
ETIQUETTES = {
    "A": ("[Sonnet:low]", "[Sonnet:medium]", "mécanique vérifiable localement"),
    "B": ("[Sonnet:high]", "[Sonnet:xhigh]", "script borné à résultat testable"),
    "C": ("[Sonnet:xhigh]", "[Opus:high]", "codage agentique, débogage, outillage"),
    "D": ("[Sonnet:high]", "[Opus:high]", "exploration et collecte à nombreux appels"),
    "E": ("[Opus:high]", "[Opus:xhigh]", "interprétation scientifique, arbitrage, verdict"),
    "F": ("[Opus:high]", "[Opus:xhigh]", "rédaction scientifique"),
    "G": ("[Opus:xhigh]", "[Fable:high]", "frontière"),
    "H": ("[Sonnet:high]", "[Opus:high]", "démarche externe, message, demande administrative"),
}
REQUETES_PAR_ARCHETYPE = {"A": "courte", "B": "moyenne", "C": "longue", "D": "longue", "E": "courte",
                          "F": "moyenne", "G": "autonome", "H": "courte"}
SORTIE_K_PAR_ARCHETYPE = {"A": 2, "B": 6, "C": 15, "D": 10, "E": 6, "F": 12, "G": 30, "H": 3}


def archetype(libelle: str) -> tuple[str, list[str]]:
    low = libelle.lower()
    scores: dict[str, list[str]] = {}
    for code, mots in ARCHETYPES:
        hits = [m for m in mots if m in low]
        if hits:
            scores[code] = hits
    if not scores:
        return "C", []  # doute → le plus fort des candidats raisonnables pour une tâche non typée
    # doute entre plusieurs archétypes : on prend le plus exigeant (ordre A<B<D<C<F<E<G)
    ordre = {"A": 0, "H": 1, "B": 2, "D": 3, "C": 4, "F": 5, "E": 6, "G": 7}
    best = max(scores, key=lambda c: (len(scores[c]) >= 2, ordre[c]))
    if len(scores) > 1:
        # règle du doute : si deux archétypes ont le même nombre d'indices, le plus fort gagne
        maxi = max(len(v) for v in scores.values())
        cands = [c for c, v in scores.items() if len(v) == maxi]
        best = max(cands, key=lambda c: ordre[c])
    return best, scores[best]


def bande(usd: float, poids) -> str:
    for nom, (lo, hi) in poids["bandes_usd_eq"].items():
        if usd >= lo and (hi is None or usd < hi):
            return nom
    return "XL"


def estimer(libelle: str, roster, poids, requetes: str | None = None, contexte: str | None = None,
            verifiable: bool | None = None, modele: str | None = None, effort: str | None = None) -> dict:
    code, indices = archetype(libelle)
    tag, escalade, nom = ETIQUETTES[code]
    if verifiable is True and code in ("B", "C"):
        tag = {"B": "[Sonnet:medium]", "C": "[Sonnet:high]"}[code]
    if verifiable is False and code in ("A", "B"):
        tag = escalade
    m = TAG_RE.match(tag)
    fam, eff = m.group(1), m.group(2)
    ecart = None
    if modele:
        # Le modèle RETENU (imposé par --modele, ou lu sur l'étiquette du registre via
        # --piste) prime sur celui déduit d'un mot-clé du libellé : sinon la bande
        # enregistrée par `tache start` est fausse d'un cran avant le premier geste, et
        # l'audit de sobriété signale ensuite un « dépassement » qui n'en est pas un
        # (AG2 le 2026-09-24, AG3 le 2026-09-25 — piste AP).
        fam_retenue = famille_de(modele)
        if not fam_retenue:
            raise SystemExit(f"--modele '{modele}' non reconnu (attendu : {', '.join(FAMILLES)})")
        eff_retenu = effort or eff
        if fam_retenue != fam or eff_retenu != eff:
            ecart = (f"archétype {code} ({nom}) suggère [{fam}" + (f":{eff}]" if eff else "]")
                     + f" ; retenu [{fam_retenue}" + (f":{eff_retenu}]" if eff_retenu else "]")
                     + " (--modele/--piste)")
        fam, eff = fam_retenue, eff_retenu
        tag = f"[{fam}" + (f":{eff}]" if eff else "]")
    req = requetes or REQUETES_PAR_ARCHETYPE[code]
    ctx = contexte or ("froid" if code in ("A", "E", "H") else "projet")
    n_req = poids["requetes_attendues"][req]
    ctx_k = poids["contexte_attendu_k"][ctx]
    p = prix(roster, fam)
    f = poids["facteur_forfait"].get(fam, 1.0)
    sortie_k = SORTIE_K_PAR_ARCHETYPE[code]
    usd = (n_req * ctx_k * 1e3 * p["lecture_cache"] + sortie_k * 1e3 * p["sortie"] + ctx_k * 1e3 * p["ecriture_cache_1h"]) / 1e6 * f
    alias = fam.lower()
    recette = (f"/model → {fam}" + (f" · /effort → {eff}" if eff else "")
               + " (au tour 1 directement ; /clear d'abord si la session est chargée ; Entrée ou s, les défauts sont protégés)"
               + " · puis « /pistes start <Px> »")
    return {"archetype": code, "archetype_nom": nom, "indices": indices, "etiquette": tag, "escalade": escalade,
            "requetes": req, "n_requetes": n_req, "contexte": ctx, "contexte_k": ctx_k, "sortie_k": sortie_k,
            "cout_usd_eq": round(usd, 2), "bande": bande(usd, poids), "lancement": recette, "alias": alias,
            "ecart_registre": ecart}


# ---------------------------------------------------------------- registre de pistes
def fichiers_pistes(projet: Path) -> list[Path]:
    out = []
    if (projet / "pistes.md").exists():
        out.append(projet / "pistes.md")
    out += sorted((projet / "pistes").glob("P*.md")) if (projet / "pistes").is_dir() else []
    return out


def feuilles_ouvertes(projet: Path) -> list[dict]:
    """Feuilles ouvertes d'un registre, avec leur étiquette éventuelle.

    Délègue à `status.py`, source de vérité du registre, plutôt que de re-parser :
    une seconde implémentation a divergé dès le premier essai (titres étalés sur cinq
    lignes physiques ignorés, pistes majeures sans sous-piste oubliées), et un
    étiquetage qui rate des pistes est pire qu'un étiquetage absent, puisqu'il fait
    croire le registre complet."""
    projet = Path(projet).resolve()
    sys.path.insert(0, str(_PISTES_DIR))
    import status as st
    st.ETIQUETTES.clear()
    states = st.lire_registre(str(projet), avec_audit=True)[0]
    ouvertes = {pid: v for pid, v in states.items()
                if v[0].endswith("à faire") or v[0].endswith("en cours")}
    res = []
    for pid, (etat, src, lib) in sorted(ouvertes.items(), key=lambda kv: st.sort_key(kv[0])):
        if any(autre.startswith(pid + ".") for autre in states):
            continue                                   # a des enfants : pas une feuille
        rel, _, num = src.rpartition(":")
        try:
            i = int(num) - 1
        except ValueError:
            continue
        fp = projet / rel
        try:
            ligne = fp.read_text(encoding="utf-8", errors="replace").splitlines()[i]
        except (OSError, IndexError):
            continue
        res.append({"fichier": str(fp), "ligne": i, "id": pid, "libelle": lib,
                    "etat": etat.split()[-1] if etat else "", "etiquette": st.ETIQUETTES.get(pid),
                    "texte": ligne})
    return res


def etiquette_de_piste(projet: Path, piste_id: str) -> str | None:
    """Étiquette [Modèle:effort] d'une piste par son identifiant, quel que soit son état.

    Contrairement à `feuilles_ouvertes` (limitée aux pistes à faire/en cours), `--piste` doit
    aussi retrouver une piste déjà close : c'est le cas d'AG3, fermée le jour même où l'audit
    de sobriété a signalé le dépassement qu'elle avait causé."""
    projet = Path(projet).resolve()
    sys.path.insert(0, str(_PISTES_DIR))
    import status as st
    st.ETIQUETTES.clear()
    states = st.lire_registre(str(projet), avec_audit=False)[0]
    if piste_id not in states:
        return None
    return st.ETIQUETTES.get(piste_id)


def inserer_etiquette(ligne: str, tag: str) -> str:
    """Insère ` [Tag]` juste avant le premier crochet d'état de la ligne ; à défaut avant `    maj :` ; sinon en fin."""
    e = ETAT_RE.search(ligne)
    if e:
        return ligne[: e.start()].rstrip() + f" {tag} " + ligne[e.start():]
    m = re.search(r"\s{2,}maj\s*:", ligne)
    if m:
        return ligne[: m.start()].rstrip() + f" {tag}" + ligne[m.start():]
    return ligne.rstrip() + f" {tag}"


def cmd_etiqueter(args, roster, poids):
    projet = Path(args.projet).resolve()
    feuilles = feuilles_ouvertes(projet)
    sans = [f for f in feuilles if not f["etiquette"]]
    print(f"{projet.name} : {len(feuilles)} feuille(s) ouverte(s), {len(sans)} sans étiquette.")
    if not sans:
        return
    props = []
    for f in sans:
        est = estimer(f["libelle"], roster, poids)
        props.append((f, est))
    sortie = projet / "pistes_etiquettes_proposees.md"
    # `--apply` applique le fichier TEL QU'IL EST sur disque, éventuellement corrigé à la main :
    # le régénérer d'abord effacerait silencieusement la relecture, qui est tout l'intérêt du
    # geste en deux temps (défaut constaté et corrigé le 2026-09-13).
    if args.apply and sortie.exists():
        print(f"application du fichier de propositions existant : {sortie}")
    else:
        with sortie.open("w", encoding="utf-8") as fh:
            fh.write(f"# Étiquettes proposées ({datetime.now():%Y-%m-%d}) — grille de "
                     f"~/.agents/knowledge/model-routing.md\n\n")
            fh.write("Relire, corriger la colonne étiquette si besoin, puis `routage.py etiqueter "
                     "<projet> --apply`, qui applique CE fichier ligne à ligne (sauvegarde .bak) sans "
                     "le régénérer. Règle du doute : le plus fort.\n\n")
            fh.write("| id | étiquette | archétype | indices | bande | libellé |\n|---|---|---|---|---|---|\n")
            for f, est in props:
                fh.write(f"| {f['id']} | {est['etiquette']} | {est['archetype']} | "
                         f"{', '.join(est['indices'][:3]) or '—'} | {est['bande']} | {f['libelle'][:90]} |\n")
    if not args.apply:
        print(f"propositions écrites : {sortie}")
        for f, est in props[:15]:
            print(f"  {f['id']:<10} {est['etiquette']:<16} {est['archetype']}  {f['libelle'][:70]}")
        if len(props) > 15:
            print(f"  … {len(props) - 15} autres dans le fichier")
        return
    # --apply : relire le fichier de propositions (éventuellement corrigé à la main) et muter ligne à ligne
    table = {}
    for l in sortie.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in l.strip().strip("|").split("|")]
        if len(cells) >= 2 and re.match(r"^P\d", cells[0]) and TAG_RE.fullmatch(cells[1] or ""):
            table[cells[0]] = cells[1]
    par_fichier: dict[str, list] = {}
    for f in sans:
        if f["id"] in table:
            par_fichier.setdefault(f["fichier"], []).append((f["ligne"], table[f["id"]]))
    n = 0
    for fp, edits in par_fichier.items():
        p = Path(fp)
        lignes = p.read_text(encoding="utf-8").splitlines(keepends=True)
        bak = p.with_suffix(p.suffix + f".bak_etiquettes_{datetime.now():%Y%m%d}")
        if not bak.exists():
            bak.write_text("".join(lignes), encoding="utf-8")
        for i, tag in edits:
            if TAG_RE.search(lignes[i]):
                continue
            fin = "\n" if lignes[i].endswith("\n") else ""
            lignes[i] = inserer_etiquette(lignes[i].rstrip("\n"), tag) + fin
            n += 1
        p.write_text("".join(lignes), encoding="utf-8")
    print(f"{n} étiquette(s) appliquée(s) dans {len(par_fichier)} fichier(s) (sauvegardes .bak_etiquettes_*).")


# ---------------------------------------------------------------- tâches (prédiction / observation)
def _append(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _lire_taches() -> list[dict]:
    if not TACHES_LOG.exists():
        return []
    out = []
    for l in TACHES_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            out.append(json.loads(l))
        except Exception:
            pass
    return out


def modele_session(session_id: str | None) -> str | None:
    if not session_id:
        return None
    ech = dernier_echantillon(session_id)
    if ech and ech.get("model"):
        return ech["model"]
    tp = transcript_de(session_id)
    if not tp:
        return None
    modele = None
    try:
        with tp.open(encoding="utf-8", errors="replace") as fh:
            for ligne in fh:
                if '"role":"assistant"' not in ligne and '"role": "assistant"' not in ligne:
                    continue
                try:
                    rec = json.loads(ligne)
                except Exception:
                    continue
                m = (rec.get("message") or {}).get("model")
                if m:
                    modele = m
    except OSError:
        pass
    return modele


def cmd_tache(args, roster, poids):
    sid = session_courante(args.session)
    if args.action == "start":
        rec = {"type": "start", "ts": time.time(), "date": datetime.now().isoformat(timespec="seconds"),
               "session_id": sid, "projet": str(Path(args.projet or os.getcwd()).resolve()), "piste": args.piste,
               "etiquette_prevue": args.etiquette, "cout_prevu": args.cout_prevu,
               "modele_reel": modele_session(sid), "effort_reel": os.environ.get("CLAUDE_EFFORT")}
        ech = dernier_echantillon(None)
        if ech:
            rec["seven_day_debut"] = ech.get("seven_day")
            rec["five_hour_debut"] = ech.get("five_hour")
        _append(TACHES_LOG, rec)
        avert = ""
        if args.etiquette and rec["modele_reel"]:
            m_tag = TAG_RE.match(args.etiquette)
            if not m_tag:
                avert = (f"  ⚠ --etiquette '{args.etiquette}' non reconnue (format attendu : "
                         f"'[Sonnet:xhigh]', crochets inclus) — avertissement de décalage modèle ignoré.")
            else:
                fam_prevue = m_tag.group(1)
                fam_reelle = famille_de(rec["modele_reel"])
                if fam_prevue != fam_reelle:
                    avert = (f"  ⚠ étiquette {args.etiquette} mais session sur {fam_reelle}:{rec['effort_reel']} — "
                             f"au tour 1 : /model → {fam_prevue} directement ; session chargée : /clear puis /model ; sinon continuer ici et le noter.")
        print(f"tâche ouverte : {args.piste} ({args.etiquette or 'sans étiquette'}, coût prévu {args.cout_prevu or '?'}) "
              f"session {sid} sur {rec['modele_reel']}:{rec['effort_reel']}{chr(10) + avert if avert else ''}")
        return
    # done
    taches = _lire_taches()
    ouverte = None
    for t in reversed(taches):
        if t.get("type") == "start" and t.get("piste") == args.piste and (not sid or t.get("session_id") == sid):
            ouverte = t
            break
    if not ouverte:
        for t in reversed(taches):
            if t.get("type") == "start" and t.get("piste") == args.piste:
                ouverte = t
                break
    t0 = ouverte["ts"] if ouverte else None
    sid_mesure = (ouverte or {}).get("session_id") or sid
    u = usage_session(sid_mesure, t0=t0) if sid_mesure else {"erreur": "session inconnue"}
    if "erreur" in u:
        print(u["erreur"])
        tokens, total, detail, n_req, n_sa = {}, 0.0, {}, 0, 0
    else:
        tokens = fusion(u["principal"]["par_modele"], *[s["par_modele"] for s in u["sous_agents"].values()])
        total, detail = cout(tokens, roster, poids)
        n_req = sum(d["requetes"] for d in tokens.values())
        n_sa = len(u["sous_agents"])
    ech_fin = dernier_echantillon(None)
    d7 = None
    if ouverte and ouverte.get("seven_day_debut") is not None and ech_fin and ech_fin.get("seven_day") is not None:
        d7 = delta_pourcent(lire_quota(depuis=t0), "seven_day")
    rec = {"type": "done", "ts": time.time(), "date": datetime.now().isoformat(timespec="seconds"), "session_id": sid_mesure,
           "piste": args.piste, "projet": (ouverte or {}).get("projet") or str(Path(os.getcwd()).resolve()),
           "etiquette_prevue": (ouverte or {}).get("etiquette_prevue") or args.etiquette,
           "cout_prevu": (ouverte or {}).get("cout_prevu") or args.cout_prevu,
           "modele_reel": (ouverte or {}).get("modele_reel") or modele_session(sid_mesure),
           "effort_reel": (ouverte or {}).get("effort_reel") or os.environ.get("CLAUDE_EFFORT"),
           "duree_min": round((time.time() - t0) / 60, 1) if t0 else None,
           "requetes": n_req, "sous_agents": n_sa, "tokens": tokens, "cout_usd_eq": total, "cout_detail": detail,
           "bande_observee": bande(total, poids), "delta_seven_day": d7,
           "qualite": args.qualite, "note": args.note}
    _append(TACHES_LOG, rec)
    prev = rec["cout_prevu"] or "?"
    print(f"Consommation {args.piste} : {n_req} requêtes ({n_sa} sous-agent(s)), {sum(d['lecture_cache'] for d in tokens.values())/1e6:.1f} M lus en cache, "
          f"{sum(d['sortie'] for d in tokens.values())/1e3:.1f} k de sortie → {total:.2f} $-éq (bande {rec['bande_observee']}, prévu {prev}) ; "
          f"Δ 7 j global {d7 if d7 is not None else 'n/d'} pt ; modèle {rec['modele_reel']}:{rec['effort_reel']} ; qualité {args.qualite}"
          + (f" ; {args.note}" if args.note else ""))


# ---------------------------------------------------------------- audit de sobriété
BANDES_ORDRE = ("XS", "S", "M", "L", "XL")


def cmd_audit(args, roster, poids):
    """Compare, pour les tâches `tache done` de la session, la bande prévue (cout_prevu)
    à la bande réellement observée. Ne signale QUE les dépassements (bande observée plus
    chère que prévu) : c'est le geste qui manquait pour boucler estimation → réalité →
    correctif, sans ajouter de coût quand tout s'est déroulé comme prévu."""
    sid = session_courante(args.session)
    taches = [t for t in _lire_taches() if t.get("type") == "done" and (not sid or t.get("session_id") == sid)]
    if args.piste:
        taches = [t for t in taches if t.get("piste") == args.piste]
    depassements = []
    for t in taches:
        prevu = (t.get("cout_prevu") or "").strip().upper()
        obs = t.get("bande_observee")
        if prevu not in BANDES_ORDRE or obs not in BANDES_ORDRE:
            continue
        ecart = BANDES_ORDRE.index(obs) - BANDES_ORDRE.index(prevu)
        if ecart > 0:
            depassements.append({
                "piste": t.get("piste"), "projet": t.get("projet"), "session_id": t.get("session_id"),
                "etiquette_prevue": t.get("etiquette_prevue"), "cout_prevu": prevu, "bande_observee": obs,
                "ecart_crans": ecart, "cout_usd_eq": t.get("cout_usd_eq"), "requetes": t.get("requetes"),
                "sous_agents": t.get("sous_agents"), "qualite": t.get("qualite"), "note": t.get("note"),
                "date": t.get("date"),
            })
    if args.json:
        print(json.dumps({"session": sid, "n_taches_fermees": len(taches), "depassements": depassements},
                          ensure_ascii=False, indent=1))
        return
    if not depassements:
        print(f"audit de sobriété : {len(taches)} tâche(s) fermée(s) sur cette session, aucun dépassement de bande.")
        return
    for d in depassements:
        print(f"⚠ {d['piste']} ({d['projet']}) : prévu {d['cout_prevu']}, observé {d['bande_observee']} "
              f"(+{d['ecart_crans']} cran(s)) — {d['cout_usd_eq']} $-éq, {d['requetes']} requêtes, "
              f"{d['sous_agents']} sous-agent(s), qualité {d['qualite']}" + (f", note : {d['note']}" if d["note"] else ""))


def cmd_journal(args, roster, poids):
    journal_fiche(args.passe, args.constat, args.effet or "—")
    print(f"journal_fiche : ligne ajoutée à {FICHE} §7 ({args.passe}).")


# ---------------------------------------------------------------- mesurer
def cmd_mesurer(args, roster, poids):
    if args.retro:
        depuis = time.time() - args.jours * 86400
        lignes = []
        for tp in PROJECTS.glob("*/*.jsonl"):
            try:
                if tp.stat().st_mtime < depuis:
                    continue
            except OSError:
                continue
            u = usage_transcript(tp, t0=depuis)
            if not u["par_modele"]:
                continue
            sous = [usage_transcript(sa, t0=depuis) for sa in (tp.parent / tp.stem / "subagents").glob("agent-*.jsonl")]
            tokens = fusion(u["par_modele"], *[s["par_modele"] for s in sous if s["par_modele"]])
            total, detail = cout(tokens, roster, poids)
            n_req = sum(d["requetes"] for d in tokens.values())
            lus = sum(d["lecture_cache"] for d in tokens.values())
            sortie = sum(d["sortie"] for d in tokens.values())
            blocages = u.get("n_blocages", 0) + sum(s.get("n_blocages", 0) for s in sous)
            par_fam_session: dict[str, float] = {}
            cout_cache = 0.0
            for model, d in tokens.items():
                fam = famille_de(model) or "?"
                par_fam_session[fam] = par_fam_session.get(fam, 0.0) + detail[model]
                cout_cache += d["lecture_cache"] * prix(roster, fam)["lecture_cache"] / 1e6
            fams = "+".join(sorted(par_fam_session, key=lambda f: -par_fam_session[f]))
            lignes.append((total, tp.parent.name, tp.stem[:8], n_req, lus, sortie, fams, len(sous),
                           par_fam_session, cout_cache, blocages))
        lignes.sort(reverse=True)
        tot = sum(l[0] for l in lignes)
        cache_tot = sum(l[9] for l in lignes)
        bloc_tot = sum(l[10] for l in lignes)
        print(f"Rétrospective {args.jours} j : {len(lignes)} session(s), {tot:.0f} $-éq au total "
              f"(poids = prix de liste × facteur_forfait ; c'est une mesure d'intensité, pas une facture).")
        par_fam: dict[str, float] = {}
        for l in lignes:
            for f, v in l[8].items():
                par_fam[f] = par_fam.get(f, 0.0) + v
        print("  par famille : " + ", ".join(f"{k} {v:.0f} ({100*v/max(tot,1e-9):.0f} %)"
                                             for k, v in sorted(par_fam.items(), key=lambda x: -x[1])))
        if lignes:
            print(f"  médiane par session {statistics.median([l[0] for l in lignes]):.2f} $-éq ; "
                  f"les lectures de cache font {100*cache_tot/max(tot,1e-9):.0f} % du coût "
                  f"(le levier est donc le nombre de requêtes × la taille du contexte)")
        if bloc_tot:
            print(f"  {bloc_tot} blocage(s) de limite rencontré(s) sur la fenêtre.")
        print("  top 12 :")
        for total, proj, sid, n_req, lus, sortie, fams, nsa, _pf, _cc, bl in lignes[:12]:
            print(f"   {total:7.2f} $-éq  {proj[:38]:<38} {sid}  {n_req:4d} req  {lus/1e6:6.1f} M lus  "
                  f"{sortie/1e3:6.1f} k out  {fams}  sa={nsa}" + (f"  BLOC×{bl}" if bl else ""))
        ech = lire_quota(depuis=depuis)
        d7 = delta_pourcent(ech, "seven_day")
        if d7 is not None:
            print(f"  Δ 7 j observé sur la fenêtre (statusline) : {d7} pt → {d7/max(tot,1e-9):.2f} pt par $-éq")
        return
    sid = session_courante(args.session)
    if not sid:
        raise SystemExit("session inconnue : --session ID ou CLAUDE_CODE_SESSION_ID")
    t0 = time.time() - args.jours * 86400 if args.jours else None
    u = usage_session(sid, t0=t0)
    if "erreur" in u:
        raise SystemExit(u["erreur"])
    tokens = fusion(u["principal"]["par_modele"], *[s["par_modele"] for s in u["sous_agents"].values()])
    total, detail = cout(tokens, roster, poids)
    if args.json:
        print(json.dumps({"session": sid, "tokens": tokens, "cout_usd_eq": total, "detail": detail,
                          "sous_agents": {k: v["par_modele"] for k, v in u["sous_agents"].items()}}, ensure_ascii=False, indent=1))
        return
    print(f"Session {sid} — {u['transcript']}")
    for model, d in sorted(tokens.items(), key=lambda x: -x[1]["requetes"]):
        print(f"  {model:<28} {d['requetes']:4d} req  entrée {d['entree']/1e3:7.1f} k  lu-cache {d['lecture_cache']/1e6:7.2f} M  "
              f"écrit-cache {(d['ecriture_cache_1h']+d['ecriture_cache_5m'])/1e3:7.1f} k  sortie {d['sortie']/1e3:6.1f} k "
              f"(dont réflexion {d['reflexion']/1e3:.1f} k)  → {detail[model]:.2f} $-éq")
    print(f"  total {total:.2f} $-éq ; {len(u['sous_agents'])} sous-agent(s) ; {u['principal']['n_outils']} appels d'outil dans le fil principal")
    lus = sum(d["lecture_cache"] for d in tokens.values())
    part = 0.0
    for model, d in tokens.items():
        part += d["lecture_cache"] * prix(roster, famille_de(model) or "Opus")["lecture_cache"] / 1e6
    if total:
        print(f"  part des lectures de cache dans le coût : {100*part/total:.0f} % ({lus/1e6:.1f} M tokens) — le levier est le nombre de requêtes × contexte")
    ech = lire_quota(session=sid)
    if ech:
        e = ech[-1]
        def pct(v):
            return f"{v:.0f} %" if isinstance(v, (int, float)) else "n/d"
        hr = e.get("hit_ratio")
        print(f"  statusline : 5 h {pct(e.get('five_hour'))} · 7 j {pct(e.get('seven_day'))} · "
              f"contexte {e.get('ctx')} · hit cache {f'{hr:.2f}' if isinstance(hr, (int, float)) else 'n/d'} "
              f"· Δ 7 j pendant la session (global) {delta_pourcent(lire_quota(depuis=ech[0]['ts']), 'seven_day')} pt")


# ---------------------------------------------------------------- etat
def cmd_etat(args, roster, poids):
    sid = session_courante(args.session)
    modele = modele_session(sid)
    fam = famille_de(modele)
    effort = os.environ.get("CLAUDE_EFFORT") or "?"
    ech = dernier_echantillon(sid) or dernier_echantillon(None)
    connus = {m["id"] for m in roster["modeles"]} | set(roster.get("legacy_reconnus", []))
    print(f"Session {sid or '?'} : modèle {modele or '?'} ({fam or '?'}), effort {effort}.")
    if modele and modele not in connus and not any(modele.startswith(c) for c in connus):
        print(f"  ⚠ modèle {modele} inconnu du roster (vérifié le {roster['derniere_verification']}) : lancer /routage maj")
    if ech:
        age = (time.time() - ech["ts"]) / 60
        def _p(v):
            return f"{v:.0f} %" if isinstance(v, (int, float)) else "n/d"
        hr = ech.get("hit_ratio")
        print(f"  forfait : 5 h {_p(ech.get('five_hour'))} · 7 j {_p(ech.get('seven_day'))} "
              f"(échantillon d'il y a {age:.0f} min) · contexte {ech.get('ctx')} · "
              f"hit cache {f'{hr:.2f}' if isinstance(hr, (int, float)) else 'n/d'}")
        try:
            import feu as _feu  # même répertoire ; gradient + facteur de marge + conseil
            fx = _feu.feux(ech)
            for f in fx.values():
                print(f"  feu {f['nom']} : {f['used']:.0f} % à {100 * f['avancement']:.0f} % de la fenêtre → "
                      f"projection {f['projection']:.0f} % ({f['mot']}), marge ×{f['facteur']:.2f}, "
                      f"réinit. dans {_feu.duree_lisible(f['restant_s'])}")
            if fx:
                print("  " + _feu.conseil(fx))
        except Exception:
            pass
    else:
        print("  forfait : aucun échantillon statusline encore (quota.jsonl vide).")
    for m in roster["modeles"]:
        if m["famille"] == "Fable" and m["facturation"] != "forfait":
            print(f"  Fable : facturation « {m['facturation']} » → hors grille tant que non établie (regarder la ligne Fable de /model).")
    if ech:
        for cle, seuil, nom in (("seven_day", 75, "7 j"), ("five_hour", 80, "5 h")):
            v = ech.get(cle)
            if isinstance(v, (int, float)) and v >= seuil:
                print(f"  ⚠ file {nom} à {v:.0f} % : passer les pistes non critiques en Sonnet, "
                      f"garder Opus pour les archétypes E, F et G.")
    print("  grille : A mécanique→[Sonnet:low]/[Haiku] · B script borné→[Sonnet:high] · C agentique→[Sonnet:xhigh]/[Opus:high] · "
          "D collecte→[Sonnet:high] en sous-agents · E interprétation→[Opus:high] · F rédaction→[Opus:high] · "
          "G frontière→[Fable:high] si session longue, sinon [Opus:xhigh] · H démarche externe→[Sonnet:high]")
    print("  règles : coût = requêtes × contexte ; vérifiable → un cran plus bas ; doute → le plus fort ; bascule seulement après /clear.")
    if args.projet:
        f = feuilles_ouvertes(Path(args.projet))
        en_cours = [x for x in f if x["etat"] == "en cours"]
        for x in en_cours[:8]:
            t = x["etiquette"] or "sans étiquette"
            note = ""
            if x["etiquette"] and fam and TAG_RE.match(x["etiquette"]).group(1) != fam:
                note = f"  ← session sur {fam}"
            print(f"  en cours : {x['id']} {t}{note}")


# ---------------------------------------------------------------- calibrer
def cmd_calibrer(args, roster, poids):
    depuis = time.time() - args.jours * 86400
    ech = lire_quota(depuis=depuis)
    if len(ech) < 10:
        print(f"{len(ech)} échantillon(s) statusline sur {args.jours} j : trop peu pour calibrer (il en faut des dizaines, "
              f"ils s'accumulent à chaque tour de chaque session). Réessayer plus tard.")
    else:
        # fenêtres horaires : Δ7j (incréments positifs) vs $-éq par famille calculés depuis les transcripts
        pas = 3600
        debut = min(e["ts"] for e in ech)
        n_fen = int((time.time() - debut) // pas) + 1
        usd_fen = [dict.fromkeys(FAMILLES, 0.0) for _ in range(n_fen)]
        for tp in PROJECTS.glob("*/*.jsonl"):
            try:
                if tp.stat().st_mtime < debut:
                    continue
            except OSError:
                continue
            fichiers = [tp] + list((tp.parent / tp.stem / "subagents").glob("agent-*.jsonl"))
            for f in fichiers:
                try:
                    fh = f.open(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                with fh:
                    for ligne in fh:
                        if '"usage"' not in ligne:
                            continue
                        try:
                            rec = json.loads(ligne)
                        except Exception:
                            continue
                        msg = rec.get("message") or {}
                        u = msg.get("usage")
                        ts = _ts(rec)
                        if not isinstance(u, dict) or ts is None or ts < debut:
                            continue
                        fam = famille_de(msg.get("model"))
                        if not fam:
                            continue
                        p = prix(roster, fam)
                        c = ((u.get("input_tokens", 0) or 0) * p["entree"] + (u.get("cache_read_input_tokens", 0) or 0) * p["lecture_cache"]
                             + (u.get("cache_creation_input_tokens", 0) or 0) * p["ecriture_cache_1h"] + (u.get("output_tokens", 0) or 0) * p["sortie"]) / 1e6
                        k = int((ts - debut) // pas)
                        if 0 <= k < n_fen:
                            usd_fen[k][fam] += c
        # Δ7j par fenêtre
        ech.sort(key=lambda e: e["ts"])
        d_fen = [0.0] * n_fen
        prev = None
        for e in ech:
            v = e.get("seven_day")
            if v is None:
                continue
            if prev is not None and v >= prev[1]:
                k = int((e["ts"] - debut) // pas)
                if 0 <= k < n_fen:
                    d_fen[k] += v - prev[1]
            prev = (e["ts"], v)
        # moindres carrés sans terme constant, un coefficient par famille présente ; contraintes ≥ 0 par clipping itératif
        fams = [f for f in FAMILLES if any(w[f] > 0 for w in usd_fen)]
        coef = {}
        if fams and sum(d_fen) > 0:
            actifs = list(fams)
            for _ in range(len(fams)):
                # résolution normale
                n = len(actifs)
                A = [[sum(usd_fen[k][a] * usd_fen[k][b] for k in range(n_fen)) for b in actifs] for a in actifs]
                y = [sum(usd_fen[k][a] * d_fen[k] for k in range(n_fen)) for a in actifs]
                try:
                    x = _resoudre(A, y)
                except Exception:
                    x = [0.0] * n
                neg = [a for a, v in zip(actifs, x) if v <= 0]
                coef = {a: max(0.0, v) for a, v in zip(actifs, x)}
                if not neg:
                    break
                actifs = [a for a in actifs if a not in neg]
                if not actifs:
                    break
        tot_usd = sum(sum(w.values()) for w in usd_fen)
        tot_d = sum(d_fen)
        print(f"Calibration sur {args.jours} j : {len(ech)} échantillons, {n_fen} fenêtres horaires, {tot_usd:.1f} $-éq, Δ 7 j cumulé {tot_d:.1f} pt "
              f"→ moyenne brute {tot_d/max(tot_usd,1e-9):.3f} pt par $-éq.")
        if coef:
            ref = coef.get("Sonnet") or coef.get("Opus") or max(coef.values())
            fac = {f: (round(coef[f] / ref, 2) if f in coef and ref else None) for f in FAMILLES}
            print("  pt/$-éq par famille : " + ", ".join(f"{f} {coef[f]:.3f}" for f in coef))
            print("  facteur_forfait relatif (Sonnet = 1) : " + ", ".join(f"{f} {v}" for f, v in fac.items() if v is not None))
            if args.apply:
                for f, v in fac.items():
                    if v is not None and v > 0:
                        poids["facteur_forfait"][f] = v
                poids["points_7j_par_usd_eq"] = round(ref, 4)
                poids["derniere_calibration"] = datetime.now().strftime("%Y-%m-%d")
                sauver_bloc("routage-poids", poids)
                journal_fiche("calibration", f"{args.jours} j, {len(ech)} éch., {tot_usd:.0f} $-éq, {tot_d:.0f} pt",
                              "facteur_forfait " + ", ".join(f"{f}={v}" for f, v in fac.items() if v is not None))
                print("  bloc routage-poids réécrit, journal §7 complété.")
    # stats par étiquette depuis taches.jsonl
    dones = [t for t in _lire_taches() if t.get("type") == "done"]
    if dones:
        par: dict[str, list] = {}
        for t in dones:
            par.setdefault(t.get("etiquette_prevue") or "sans", []).append(t)
        print("  observations par étiquette (taches.jsonl) :")
        for tag, lst in sorted(par.items()):
            couts = [t["cout_usd_eq"] for t in lst if t.get("cout_usd_eq") is not None]
            q = {k: sum(1 for t in lst if t.get("qualite") == k) for k in ("OK", "reprise", "echec")}
            print(f"   {tag:<18} n={len(lst)} médiane {statistics.median(couts) if couts else 0:.2f} $-éq  OK {q['OK']} / reprise {q['reprise']} / échec {q['echec']}")
    else:
        print("  aucune observation par étiquette encore (taches.jsonl vide) : elles viennent de /pistes start … done.")


def _resoudre(A, y):
    n = len(y)
    M = [row[:] + [y[i]] for i, row in enumerate(A)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c]))
        if abs(M[piv][c]) < 1e-12:
            raise ValueError("singulier")
        M[c], M[piv] = M[piv], M[c]
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                for k in range(c, n + 1):
                    M[r][k] -= f * M[c][k]
    return [M[i][n] / M[i][i] for i in range(n)]


# ---------------------------------------------------------------- maj (veille des modèles)
URL_OVERVIEW = "https://platform.claude.com/docs/en/models/overview.md"
URL_MODEL_CONFIG = "https://code.claude.com/docs/en/model-config.md"


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "routage.py (skill personnel Claude Code)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def _cellules(ligne: str) -> list[str]:
    return [c.strip() for c in ligne.strip().strip("|").split("|")]


def _label(c: str) -> str:
    m = re.match(r"\[([^\]]+)\]\(", c)
    return (m.group(1) if m else c).strip()


def parser_overview(md: str) -> dict:
    lignes = md.splitlines()
    i = next((k for k, l in enumerate(lignes) if l.startswith("| Feature")), None)
    if i is None:
        return {}
    colonnes = [_label(c) for c in _cellules(lignes[i])][1:]
    table = {}
    for l in lignes[i + 2:]:
        if not l.startswith("|"):
            break
        cells = _cellules(l)
        table[_label(cells[0])] = cells[1:]
    out = {}
    for j, nom in enumerate(colonnes):
        def cell(k):
            v = table.get(k, [])
            return v[j] if j < len(v) else ""
        mid = cell("Claude API ID").strip("`")
        pr = cell("Pricing")
        m = re.findall(r"\$([0-9.]+)", pr)
        ctx = cell("Context window")
        ctxn = 1_000_000 if ctx.upper().startswith("1M") else (200_000 if ctx.upper().startswith("200K") else None)
        out[mid] = {"nom": nom.replace("Claude ", ""), "entree": float(m[0]) if m else None, "sortie": float(m[1]) if len(m) > 1 else None,
                    "effort_defaut": (lambda v: None if (not v or "not supported" in v.lower()) else v)(cell("Default effort").strip("`")), "contexte": ctxn, "latence": cell("Comparative latency")}
    pc = re.search(r"cache reads cost (\d+)% of the base input price(?: \((\d+(?:\.\d+)?)% on ([^)]+)\))?", md)
    out["_cache"] = {"defaut_pct": float(pc.group(1)) if pc else 10.0,
                     "exceptions": {"pct": float(pc.group(2)), "modeles": pc.group(3)} if pc and pc.group(2) else None}
    return out


def parser_efforts(md: str) -> dict:
    out = {}
    for l in md.splitlines():
        if not (l.startswith("|") and "`low`" in l):
            continue
        cells = _cellules(l)
        if len(cells) == 2 and re.search(r"(Fable|Opus|Sonnet|Haiku)\s", cells[0] + " ") and "`" not in cells[0]:
            out[cells[0]] = re.findall(r"`(\w+)`", cells[1])
    return out


def cmd_maj(args, roster, poids):
    try:
        ov = parser_overview(_fetch(URL_OVERVIEW))
        ef = parser_efforts(_fetch(URL_MODEL_CONFIG))
    except Exception as e:
        raise SystemExit(f"récupération de la doc impossible ({e}) : faire la veille à la main (WebFetch) et corriger le bloc routage-roster.")
    cache = ov.pop("_cache", {"defaut_pct": 10.0, "exceptions": None})
    connus = {m["id"]: m for m in roster["modeles"]}
    diffs, nouveaux = [], []
    for mid, info in ov.items():
        if not mid:
            continue
        exc_pct = None
        if cache.get("exceptions") and info["nom"] and info["nom"].split()[0] in (cache["exceptions"]["modeles"] or ""):
            exc_pct = cache["exceptions"]["pct"]
        pct = exc_pct if exc_pct is not None else cache["defaut_pct"]
        attendu_cache = round((info["entree"] or 0) * pct / 100, 3)
        if mid in connus:
            m = connus[mid]
            p = m["prix_usd_mtok"]
            for cle, val in (("entree", info["entree"]), ("sortie", info["sortie"]), ("lecture_cache", attendu_cache)):
                if val is not None and abs(p.get(cle, -1) - val) > 1e-9:
                    diffs.append((mid, cle, p.get(cle), val))
            if info["effort_defaut"] and info["effort_defaut"] != m.get("effort_defaut"):
                diffs.append((mid, "effort_defaut", m.get("effort_defaut"), info["effort_defaut"]))
            if info["contexte"] and info["contexte"] != m.get("contexte"):
                diffs.append((mid, "contexte", m.get("contexte"), info["contexte"]))
        else:
            nouveaux.append((mid, info, attendu_cache))
    disparus = [mid for mid in connus if mid not in ov]
    print(f"Veille modèles ({datetime.now():%Y-%m-%d}) : {len(ov)} modèle(s) courants dans la doc, roster vérifié le {roster['derniere_verification']}.")
    for mid, info, ac in nouveaux:
        print(f"  NOUVEAU : {mid} ({info['nom']}) entrée {info['entree']} / sortie {info['sortie']} / lecture cache ≈ {ac} ; "
              f"effort défaut {info['effort_defaut']} ; contexte {info['contexte']} ; latence {info['latence']}")
    for mid, cle, av, ap in diffs:
        print(f"  CHANGÉ : {mid}.{cle} {av} → {ap}")
    for mid in disparus:
        print(f"  RETIRÉ de la table des modèles courants : {mid} (devient legacy)")
    if ef:
        print("  efforts par modèle (Claude Code) : " + " ; ".join(f"{k} = {','.join(v)}" for k, v in ef.items()))
    # réglages périmés
    try:
        st = json.loads(SETTINGS.read_text(encoding="utf-8"))
        for cle in (st.get("modelSettings") or {}):
            if cle not in connus and cle not in ov:
                print(f"  ⚠ settings.json modelSettings porte une clé hors roster et hors doc : {cle}")
    except Exception:
        pass
    if not (nouveaux or diffs or disparus):
        print("  aucun écart : roster à jour.")
    if args.apply and (nouveaux or diffs or disparus or args.forcer_date):
        for mid, cle, av, ap in diffs:
            m = connus[mid]
            if cle in ("entree", "sortie", "lecture_cache"):
                m["prix_usd_mtok"][cle] = ap
                if cle == "entree":
                    m["prix_usd_mtok"]["ecriture_cache_5m"] = round(ap * 1.25, 3)
                    m["prix_usd_mtok"]["ecriture_cache_1h"] = round(ap * 2.0, 3)
            else:
                m[cle] = ap
        for mid, info, ac in nouveaux:
            fam = famille_de(mid) or info["nom"].split()[0]
            roster["modeles"].insert(0, {
                "famille": fam, "id": mid, "alias_claude_code": fam.lower(), "nom": info["nom"],
                "prix_usd_mtok": {"entree": info["entree"], "lecture_cache": ac, "ecriture_cache_5m": round((info["entree"] or 0) * 1.25, 3),
                                  "ecriture_cache_1h": round((info["entree"] or 0) * 2.0, 3), "sortie": info["sortie"]},
                "contexte": info["contexte"], "efforts": ["low", "medium", "high", "xhigh", "max"] if info["effort_defaut"] else [],
                "effort_defaut": info["effort_defaut"], "changement_effort_garde_cache": None,
                "facturation": "inconnu", "note": f"ajouté par /routage maj le {datetime.now():%Y-%m-%d} ; à qualifier (facturation, cache, grille)"})
        for mid in disparus:
            roster["modeles"] = [m for m in roster["modeles"] if m["id"] != mid]
            roster.setdefault("legacy_reconnus", []).append(mid)
        roster["derniere_verification"] = datetime.now().strftime("%Y-%m-%d")
        sauver_bloc("routage-roster", roster)
        journal_fiche("veille modèles", f"{len(nouveaux)} nouveau(x), {len(diffs)} changement(s), {len(disparus)} retiré(s)",
                      "roster réécrit ; grille à relire si nouveau modèle")
        print("  roster réécrit et journal §7 complété. Si un modèle est NOUVEAU : relire la grille §2 et qualifier sa facturation.")
    elif args.apply:
        roster["derniere_verification"] = datetime.now().strftime("%Y-%m-%d")
        sauver_bloc("routage-roster", roster)
        print("  date de vérification mise à jour.")


# ---------------------------------------------------------------- estimer (CLI)
def cmd_estimer(args, roster, poids):
    libelle = args.libelle
    if re.fullmatch(r"P\d+(?:\.[0-9A-Za-z]+)*", libelle) and args.projet:
        for f in feuilles_ouvertes(Path(args.projet)):
            if f["id"] == libelle:
                libelle = f["libelle"]
                break
    modele, effort = None, None
    if args.piste:
        projet = Path(args.projet or os.getcwd())
        tag_piste = etiquette_de_piste(projet, args.piste)
        if not tag_piste:
            print(f"  ⚠ piste {args.piste} introuvable ou sans étiquette dans {projet} : --piste ignoré.")
        elif not TAG_RE.match(tag_piste):
            print(f"  ⚠ étiquette {tag_piste} de {args.piste} non reconnue : --piste ignoré.")
        else:
            m = TAG_RE.match(tag_piste)
            modele, effort = m.group(1), m.group(2)
    if args.modele:
        modele = args.modele
    if args.effort:
        effort = args.effort
    est = estimer(libelle, roster, poids, args.requetes, args.contexte,
                  True if args.verifiable else (False if args.non_verifiable else None),
                  modele=modele, effort=effort)
    if args.json:
        print(json.dumps(est, ensure_ascii=False, indent=1))
        return
    print(f"{est['etiquette']}  (archétype {est['archetype']} : {est['archetype_nom']}"
          + (f" ; indices : {', '.join(est['indices'][:4])}" if est["indices"] else " ; aucun indice lexical → doute → C") + ")")
    if est.get("ecart_registre"):
        print(f"  ⚠ écart archétype/registre : {est['ecart_registre']}")
    print(f"  coût prévu : bande {est['bande']} ≈ {est['cout_usd_eq']} $-éq ({est['n_requetes']} requêtes × {est['contexte_k']} k de contexte, "
          f"{est['sortie_k']} k de sortie) ; escalade : {est['escalade']}")
    print(f"  lancement : {est['lancement']}")


# ---------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description="routage modèle/effort et mesure du forfait")
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("etat"); s.add_argument("--session"); s.add_argument("--projet")
    s = sub.add_parser("estimer"); s.add_argument("libelle"); s.add_argument("--projet")
    s.add_argument("--requetes", choices=["courte", "moyenne", "longue", "autonome"]); s.add_argument("--contexte", choices=["froid", "projet", "charge"])
    s.add_argument("--verifiable", action="store_true"); s.add_argument("--non-verifiable", action="store_true"); s.add_argument("--json", action="store_true")
    s.add_argument("--modele", choices=list(FAMILLES), help="modèle RETENU, prime sur celui déduit de l'archétype")
    s.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"])
    s.add_argument("--piste", help="identifiant de piste : lit son étiquette [Modèle:effort] au registre du --projet (ou cwd)")
    s = sub.add_parser("etiqueter"); s.add_argument("projet"); s.add_argument("--apply", action="store_true")
    s = sub.add_parser("mesurer"); s.add_argument("--session"); s.add_argument("--jours", type=float, default=0); s.add_argument("--retro", action="store_true"); s.add_argument("--json", action="store_true")
    s = sub.add_parser("tache"); s.add_argument("action", choices=["start", "done"]); s.add_argument("--piste", required=True)
    s.add_argument("--projet"); s.add_argument("--etiquette"); s.add_argument("--cout-prevu", dest="cout_prevu"); s.add_argument("--session")
    s.add_argument("--qualite", choices=["OK", "reprise", "echec"]); s.add_argument("--note")
    s = sub.add_parser("calibrer"); s.add_argument("--jours", type=float, default=7); s.add_argument("--apply", action="store_true")
    s = sub.add_parser("maj"); s.add_argument("--apply", action="store_true"); s.add_argument("--dry-run", action="store_true"); s.add_argument("--forcer-date", action="store_true")
    s = sub.add_parser("audit"); s.add_argument("--session"); s.add_argument("--piste"); s.add_argument("--json", action="store_true")
    s = sub.add_parser("journal"); s.add_argument("passe"); s.add_argument("constat"); s.add_argument("effet", nargs="?")
    args = ap.parse_args(argv)
    if not args.cmd:
        args.cmd = "etat"; args.session = None; args.projet = None
    if args.cmd == "mesurer" and args.retro and not args.jours:
        args.jours = 30
    if args.cmd == "tache" and args.action == "done" and not args.qualite:
        ap.error("tache done exige --qualite OK|reprise|echec")
    if args.cmd == "etiqueter":
        # normaliser un chemin relatif
        args.projet = str(Path(args.projet))
    _, roster, poids = charger_fiche()
    {"etat": cmd_etat, "estimer": cmd_estimer, "etiqueter": cmd_etiqueter, "mesurer": cmd_mesurer,
     "tache": cmd_tache, "calibrer": cmd_calibrer, "maj": cmd_maj,
     "audit": cmd_audit, "journal": cmd_journal}[args.cmd](args, roster, poids)


if __name__ == "__main__":
    main()
