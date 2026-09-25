#!/usr/bin/env python3
"""
Objet : feu de forfait — rythme de consommation des fenêtres Claude (5 h, 7 j) rapporté à
        l'avancement dans la fenêtre, rendu en gradient continu du vert au rouge et en facteur
        de marge (×1,4 : on peut accélérer de 40 % ; ×0,8 : il faut ralentir de 20 %).
Entrées : pourcentage consommé (`used_percentage`) et instant de réinitialisation (`resets_at`,
        epoch secondes) de chaque fenêtre, tels que la statusline les reçoit et les journalise
        dans ~/.agents/coord/quota/quota.jsonl (`five_hour`/`five_reset`, `seven_day`/`seven_reset`).
Sorties : dict par fenêtre (avancement, projection, facteur, rgb, ansi, mot) ; feu global = la
        fenêtre la plus contraignante ; `conseil()` rend la phrase de conduite lue par l'assistant.
Réutilisable : oui — importé par ~/.claude/statusline-command.sh, par le hook SessionStart
        (~/.claude/hooks/session_context.sh, bloc [SOBRIÉTÉ]) et par `routage.py etat` ; CLI
        `python3 feu.py` affiche le feu du dernier échantillon.
Projet : skill /routage (${CLAUDE_PLUGIN_ROOT}/skills/routage), demande CG 2026-09-13.
Date : 2026-09-13.

Modèle. Une fenêtre couvre [resets_at - durée, resets_at]. Avancement a = 1 - (resets_at - now)/durée
(fraction de fenêtre déjà écoulée, sur l'horloge murale — sert de proxy au rythme PASSÉ, inchangé).
Rythme passé = used / max(a, 0,10) (plancher 10 % pour ne pas juger sur les premières minutes :
prudent en début de fenêtre, jamais laxiste). Projection p = used + rythme_passé × (temps_effectif
restant / durée) : ce qu'on aura consommé en fin de fenêtre si le rythme PASSÉ se maintient
seulement pendant le temps où il reste RÉELLEMENT possible de coder (demande CG 2026-09-14) — pas
sur l'horloge murale brute. Le temps effectif retire du restant brut les visios prévues (cache
peuplé à part, feu.py ne fait jamais d'appel réseau) et les heures après CUTOFF_HEURE (19 h, CG ne
vibe-code quasiment jamais après) : sans visio ni soirée dans la fenêtre, temps_effectif = restant
brut et p retombe exactement sur l'ancienne formule used/a (généralisation, pas rupture). Cette
projection est celle du COMPTE courant (`projection_compte`) ; la projection qui pilote tout le
reste la divise par COMPTES_MAX (CG a deux comptes Max aux fenêtres indépendantes, cf. la note
sur la constante) : la fenêtre 7 j n'a donc à couvrir que 3,5 jours de travail sur un compte
donné, la 5 h que 2 h 30. Facteur
f = 100 / p : multiplicateur de rythme admissible avant de cogner la limite. Le feu global prend la
fenêtre de plus petit f. Couleur : interpolation linéaire entre points de contrôle (p = 0 vert → 50
vert-jaune → 80 jaune → 100 orange → 130 rouge), donc un gradient continu, pas trois paliers. Les
seuils de CONDUITE, eux, sont discrets parce qu'une règle l'est, et gradués selon ce que coûte
l'escalade (un cran d'effort ≈ +30 à +50 % de requêtes, Sonnet → Opus ≈ ×2,5 par requête) : f ≥ 2 →
vert franc, escalade de MODÈLE et sessions supplémentaires possibles ; 1,25 ≤ f < 2 → vert, un cran
d'EFFORT sur les tâches à intérêt ; 1,0 ≤ f < 1,25 → orange, au rythme ; f < 1,0 → rouge, freiner.
"""
import json
import os
import sys
import time
from pathlib import Path

DUREES = {"five_hour": 5 * 3600, "seven_day": 7 * 86400}
NOMS = {"five_hour": "5 h", "seven_day": "7 j"}
PLANCHER_AVANCEMENT = 0.10

# ---------------------------------------------------------------------------
# NOMBRE DE COMPTES MAX — le seul paramètre à changer si CG revient à un compte
# unique (mettre 1, rien d'autre à toucher : couleurs, mots, seuils de conduite et
# recommandations de pistes en découlent tous).
#
# CG a DEUX comptes Max (déclaré 2026-09-14, confirmé et mis en application
# 2026-09-22). Chaque compte porte ses PROPRES fenêtres 5 h et 7 j, indépendantes,
# et `rate_limits` ne dit jamais rien que du compte de la session courante. La
# capacité réellement disponible est donc COMPTES_MAX fois celle qu'une session
# voit, et l'horizon à tenir sur un compte donné n'est pas la fenêtre entière mais
# sa fraction : 3,5 jours pour la fenêtre 7 j, 2 h 30 pour la fenêtre 5 h, à deux
# comptes. Sans ce facteur, le feu réclamait de ralentir à mi-capacité — un feu qui
# crie au rouge quand il reste la moitié du réservoir cesse d'être lu, et fait
# différer du travail qui pouvait être fait.
#
# HYPOTHÈSE, à connaître pour lire le feu : la charge se répartit à peu près
# également entre les comptes. Si CG épuise un compte PUIS bascule sur l'autre,
# le facteur reste juste sur la capacité totale mais le compte courant, lui,
# touchera bien sa limite avant la fin de sa fenêtre : c'est ce que dit le champ
# `projection_compte` et le rappel de bascule ajouté à `conseil()`. La conduite à
# tenir alors n'est pas de ralentir, c'est de changer de compte.
COMPTES_MAX = int(os.environ.get("CLAUDE_COMPTES_MAX") or 2)
POINTS = [(0, (40, 200, 60)), (50, (150, 210, 40)), (80, (235, 200, 0)),
          (100, (240, 120, 0)), (130, (230, 30, 30))]
QLOG = Path.home() / ".agents/coord/quota/quota.jsonl"

# Temps effectif restant : deux motifs de retrait du restant brut.
# Heure locale au-delà de laquelle vous ne codez quasiment jamais le soir (exemple : CG,
# 19 h) ; 24 désactive ce retrait pour qui travaille sans coupure horaire régulière (0
# exclurait au contraire la journée entière, cf. `_hors_horaires` : ne pas l'utiliser).
CUTOFF_HEURE = int(os.environ.get("CLAUDE_CUTOFF_HEURE") or 19)
CACHE_VISIOS = Path.home() / ".agents/coord/quota/agenda_visios.json"
VISIOS_PERIME_S = 6 * 3600  # cache de visios ignoré au-delà de cette fraîcheur (dégradation
                            # silencieuse vers l'ancien comportement, jamais de plantage)


def rgb(projection):
    """Couleur (r, g, b) du gradient pour une projection en pourcent."""
    p = max(POINTS[0][0], min(POINTS[-1][0], float(projection)))
    for (p0, c0), (p1, c1) in zip(POINTS, POINTS[1:]):
        if p <= p1:
            t = 0.0 if p1 == p0 else (p - p0) / (p1 - p0)
            return tuple(int(round(a + (b - a) * t)) for a, b in zip(c0, c1))
    return POINTS[-1][1]


def ansi(projection):
    r, g, b = rgb(projection)
    return f"\033[38;2;{r};{g};{b}m"


def mot(projection):
    p = float(projection)
    if p < 50:
        return "vert franc"
    if p < 80:
        return "vert"
    if p < 100:
        return "orange"
    if p < 130:
        return "rouge"
    return "rouge vif"


def _fusionner(intervalles):
    """Fusionne une liste de (début, fin) qui peuvent se chevaucher, en intervalles disjoints
    triés. Les intervalles vides ou inversés sont ignorés."""
    ivs = sorted((s, e) for s, e in intervalles if e > s)
    out = []
    for s, e in ivs:
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def _hors_horaires(debut, fin, cutoff_heure=CUTOFF_HEURE):
    """Intervalles [cutoff_heure, minuit) de chaque jour calendaire (heure locale) chevauchant
    [debut, fin). Ne modélise qu'une borne du soir (demande CG 2026-09-14 : pas d'affirmation sur
    une heure de reprise le matin, faute d'avoir été formulée)."""
    if fin <= debut:
        return []
    out = []
    t = time.localtime(debut)
    jour = time.mktime((t.tm_year, t.tm_mon, t.tm_mday, 0, 0, 0, 0, 0, -1))
    while jour < fin:
        soir = jour + cutoff_heure * 3600
        minuit_suivant = jour + 86400
        s, e = max(soir, debut), min(minuit_suivant, fin)
        if e > s:
            out.append((s, e))
        jour = minuit_suivant
    return out


def _visios(debut, fin, cache_path=CACHE_VISIOS, now=None):
    """Intervalles de visios prévues chevauchant [debut, fin), depuis un cache peuplé à part
    (feu.py est appelé à chaque rendu de statusline : aucun appel réseau ici). Cache absent,
    illisible ou plus vieux que VISIOS_PERIME_S : dégradation silencieuse vers []."""
    now = time.time() if now is None else now
    try:
        d = json.loads(cache_path.read_text(encoding="utf-8"))
        if now - float(d.get("updated_at", 0)) > VISIOS_PERIME_S:
            return []
        out = []
        for iv in d.get("intervals", []):
            s, e = max(float(iv["start"]), debut), min(float(iv["end"]), fin)
            if e > s:
                out.append((s, e))
        return out
    except Exception:
        return []


def temps_effectif_restant(now, fin, cache_path=CACHE_VISIOS):
    """Secondes réellement disponibles pour coder entre `now` et `fin` : le brut moins l'union
    des visios prévues et des heures après CUTOFF_HEURE (demande CG 2026-09-14)."""
    if fin <= now:
        return 0.0
    brut = fin - now
    indispo = _fusionner(_hors_horaires(now, fin) + _visios(now, fin, cache_path, now))
    couvert = sum(e - s for s, e in indispo)
    return max(0.0, brut - couvert)


def feu(used, resets_at, cle, now=None, cache_path=CACHE_VISIOS, comptes=None):
    """Feu d'une fenêtre, ou None si l'une des deux grandeurs manque.

    `projection_compte` est la projection sur le SEUL compte de la session (ce que
    `rate_limits` mesure) ; `projection` la rapporte à la capacité réelle des
    `comptes` comptes Max, et c'est elle qui pilote couleur, mot et facteur — donc
    la statusline, le rappel [SOBRIÉTÉ] et `routage.py etat` sans qu'ils changent."""
    if not isinstance(used, (int, float)) or not isinstance(resets_at, (int, float)):
        return None
    now = time.time() if now is None else now
    n = max(1, int(COMPTES_MAX if comptes is None else comptes))
    duree = DUREES[cle]
    restant = max(0.0, resets_at - now)
    a = min(1.0, max(0.0, 1.0 - restant / duree))
    restant_eff = temps_effectif_restant(now, resets_at, cache_path)
    rythme = float(used) / max(a, PLANCHER_AVANCEMENT)
    p_compte = float(used) + rythme * (restant_eff / duree)
    p = p_compte / n
    f = (100.0 / p) if p > 0 else float("inf")
    return {"cle": cle, "nom": NOMS[cle], "used": float(used), "restant_s": restant,
            "restant_eff_s": restant_eff, "avancement": a, "projection": p,
            "projection_compte": p_compte, "comptes": n, "facteur": f,
            "horizon_s": duree / n,
            "rgb": rgb(p), "ansi": ansi(p), "mot": mot(p)}


def feux(ech, now=None):
    """Feux des deux fenêtres depuis un échantillon quota.jsonl (ou le JSON de la statusline
    déjà aplati en five_hour/five_reset/seven_day/seven_reset)."""
    out = {}
    for cle, k_used, k_reset in (("five_hour", "five_hour", "five_reset"),
                                 ("seven_day", "seven_day", "seven_reset")):
        f = feu(ech.get(k_used), ech.get(k_reset), cle, now)
        if f:
            out[cle] = f
    return out


def global_(fx):
    """La fenêtre la plus contraignante (plus petit facteur), ou None."""
    return min(fx.values(), key=lambda f: f["facteur"]) if fx else None


def duree_lisible(s):
    s = int(max(0, s))
    j, h, m = s // 86400, (s % 86400) // 3600, (s % 3600) // 60
    if j:
        return f"{j} j {h:02d} h"
    if h:
        return f"{h} h {m:02d}"
    return f"{m} min"


def bascule(fx):
    """Rappel de bascule de compte : '' à un seul compte, ou tant qu'aucune fenêtre ne
    projette l'épuisement du compte COURANT. À plusieurs comptes, un compte qui cogne sa
    limite n'appelle pas à ralentir (la capacité globale reste là) mais à changer de
    compte — conduite que le seul feu global, calculé sur la capacité totale, ne dit pas."""
    epuisees = [f for f in fx.values() if f.get("comptes", 1) > 1
                and f.get("projection_compte", 0) >= 100]
    if not epuisees:
        return ""
    pire = min(epuisees, key=lambda f: f["facteur"])
    return (f"BASCULE DE COMPTE : sur ce compte, la fenêtre {pire['nom']} projette "
            f"{pire['projection_compte']:.0f} % et sera épuisée avant sa réinitialisation "
            f"(dans {duree_lisible(pire['restant_s'])}). La capacité globale des "
            f"{pire['comptes']} comptes n'est pas en cause : passer sur l'autre compte, "
            "pas ralentir.")


def conseil(fx):
    """Phrase de conduite pour l'assistant, déduite du feu global. '' si aucun feu."""
    g = global_(fx)
    if not g:
        return ""
    f = g["facteur"]
    fac = "∞" if f == float("inf") else f"×{f:.2f}"
    n = g.get("comptes", 1)
    borne = f"bornée par la fenêtre {g['nom']}"
    if n > 1:
        borne += f" ({duree_lisible(g['horizon_s'])} d'horizon par compte, {n} comptes)"
    b = bascule(fx)
    suffixe = ("  " + b) if b else ""
    if f >= 2.0:
        return (f"FEU VERT FRANC (marge de rythme {fac}, {borne}) : d'autres sessions peuvent "
                "tourner et, au tour 1, la colonne Escalade de la grille devient le défaut dès que la "
                "tâche peut gagner en profondeur (E/F/G, C ambigu, résultat à creuser), modèle "
                "compris (Sonnet → Opus) : c'est le moment de creuser." + suffixe)
    if f >= 1.25:
        return (f"FEU VERT (marge {fac}, {borne}) : au tour 1, proposer un cran d'EFFORT au-dessus de "
                "l'étiquette quand la tâche a un intérêt à creuser ; pas de changement de modèle "
                "systématique (×2,5 par requête), une session de plus au plus." + suffixe)
    if f >= 1.0:
        return (f"FEU ORANGE (marge {fac}, {borne}) : au rythme ; étiquette telle quelle, pas de "
                "session lourde en plus, pas d'escalade sans intérêt démontré." + suffixe)
    return (f"FEU ROUGE (fenêtre {g['nom']} : ralentir de {100 - 100 * f:.0f} %, réinit. dans "
            f"{duree_lisible(g['restant_s'])}) : Sonnet et sous-agents, aucune nouvelle session, "
            "différer ce qui peut attendre la réinitialisation." + suffixe)


def dernier_echantillon(session_id=None):
    try:
        lignes = QLOG.read_text(encoding="utf-8", errors="replace").splitlines()[-3000:]
    except Exception:
        return None
    for l in reversed(lignes):
        try:
            r = json.loads(l)
        except Exception:
            continue
        if r.get("seven_day") is None and r.get("five_hour") is None:
            continue
        if session_id and r.get("session_id") != session_id:
            continue
        return r
    return None


def _epoch_local(s):
    """Parse une chaîne ISO locale ('2026-09-14T15:00') en epoch secondes. Accepte aussi un
    horodatage déjà tz-aware (auquel cas la conversion ne passe pas par l'heure locale)."""
    from datetime import datetime
    dt = datetime.fromisoformat(s)
    return dt.timestamp() if dt.tzinfo is not None else time.mktime(dt.timetuple())


def _charger_visios(path=CACHE_VISIOS):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"updated_at": 0, "intervals": []}


def _sauver_visios(d, path=CACHE_VISIOS):
    d["updated_at"] = time.time()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def _cli_visio(argv):
    """Sous-commandes de gestion manuelle du cache de visios (demande CG 2026-09-14) :
    `feu.py visio ajouter <début ISO> <fin ISO> [titre]`, `feu.py visio liste`,
    `feu.py visio purger` (retire les entrées déjà terminées). Cache lu par `feu()` à chaque
    rendu de statusline ; feu.py lui-même ne fait jamais d'appel réseau ni de requête calendrier —
    ce cache doit être peuplé depuis une session qui a accès au calendrier (query_email_and_calendar
    côté Superhuman), manuellement pour l'instant."""
    action = argv[0] if argv else "liste"
    d = _charger_visios()
    if action == "ajouter":
        if len(argv) < 3:
            print("usage : feu.py visio ajouter <début ISO> <fin ISO> [titre]"); sys.exit(1)
        s, e = _epoch_local(argv[1]), _epoch_local(argv[2])
        titre = argv[3] if len(argv) > 3 else ""
        d.setdefault("intervals", []).append({"start": s, "end": e, "titre": titre})
        _sauver_visios(d)
        print(f"ajouté : {argv[1]} → {argv[2]}" + (f" ({titre})" if titre else ""))
    elif action == "purger":
        now = time.time()
        avant = len(d.get("intervals", []))
        d["intervals"] = [iv for iv in d.get("intervals", []) if float(iv["end"]) > now]
        _sauver_visios(d)
        print(f"purgé : {avant - len(d['intervals'])} entrée(s) passée(s) retirée(s), "
              f"{len(d['intervals'])} restante(s).")
    elif action == "liste":
        ivs = d.get("intervals", [])
        if not ivs:
            print("aucune visio dans le cache."); return
        for iv in sorted(ivs, key=lambda x: x["start"]):
            s = time.strftime("%Y-%m-%d %H:%M", time.localtime(iv["start"]))
            e = time.strftime("%H:%M", time.localtime(iv["end"]))
            print(f"  {s} → {e}" + (f"  {iv.get('titre')}" if iv.get("titre") else ""))
    else:
        print(f"sous-commande inconnue : {action} (ajouter | liste | purger)"); sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "visio":
        _cli_visio(sys.argv[2:])
        sys.exit(0)
    ech = dernier_echantillon(sys.argv[1] if len(sys.argv) > 1 else None)
    if not ech:
        print("aucun échantillon de quota (quota.jsonl vide ou sans fenêtres).")
        sys.exit(0)
    fx = feux(ech)
    age = (time.time() - ech["ts"]) / 60
    print(f"échantillon d'il y a {age:.0f} min (session {str(ech.get('session_id'))[:8]})")
    for f in fx.values():
        print(f"  {f['ansi']}{f['nom']} : {f['used']:.0f} % consommé à {100 * f['avancement']:.0f} % de la "
              f"fenêtre → projection {f['projection']:.0f} % ({f['mot']}), marge ×{f['facteur']:.2f}, "
              f"restant brut {duree_lisible(f['restant_s'])}, effectif {duree_lisible(f['restant_eff_s'])}"
              f"\033[0m")
    print("  " + conseil(fx))
