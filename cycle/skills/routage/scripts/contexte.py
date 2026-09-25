#!/usr/bin/env python3
"""
Objet : dire d'où vient le contexte que chaque requête relit, et ce que coûterait de le couper.
        Trois mesures depuis les transcripts `~/.claude/projects/<slug>/<session>.jsonl` :
          prefixe   — décomposition du tour 1 (listing des skills, CLAUDE.md, mémoire, hooks,
                      constante harnais) en caractères, avec conversion en tokens calibrée ;
          integrale — part de l'INTÉGRALE des tokens lus (ce qui coûte) par origine : préfixe,
                      résultats d'outils, entrées d'outils (ce que l'assistant écrit), réflexion,
                      rappels/hooks, prompts, texte ; par outil ; entrées Bash en heredoc ;
          clear     — rejoue chaque session en coupant (/clear) au-delà d'un seuil de contexte,
                      aux frontières de tour humain seulement, et chiffre l'économie ;
          alleger   — pose (ou retire) dans un répertoire de projet le `.claude/settings.local.json`
                      qui désactive les plugins de skills inutiles ici, en fusionnant sans rien
                      écraser. Dry-run par défaut, `--apply` pour écrire.
Entrées : transcripts locaux ; options --jours N, --famille opus|sonnet|fable|haiku|toutes.
Sorties : texte sur stdout ; `--json` pour la sortie brute.
Réutilisable : oui, tout projet, aucun appel LLM (stdlib seule).
Projet : mtbc P73.4 (réduction du contexte moyen d'Opus).
Date : 2026-09-13.

Calibrations mesurées le 2026-09-13 (régressions intra-tour sur 4 sessions, Opus/Sonnet/Fable,
R2 0,90-0,99) : un résultat d'outil ou un rappel système pèse 0,45 token par caractère
(2,2 car/token) ; la sortie de l'assistant (texte, entrées d'outils) reste dans le contexte à
1,0 ; la RÉFLEXION reste aussi dans le contexte à 1,0-1,2 et n'est PAS retirée aux frontières de
tour humain (résidu ~+180 tokens, pente nulle sur Σréflexion). Le listing des skills vaut
0,40 token/car et les CLAUDE.md en français 0,51 token/car (régression sur 162 tours 1 ; la
constante 30 k tokens est le harnais : prompt système + définitions d'outils, absents du transcript).
"""
from __future__ import annotations
import argparse
import collections
import glob
import json
import os
import statistics as st
import sys
import time

TOK_PAR_CAR_RESULTAT = 0.45   # résultats d'outils, rappels, prompts (mesuré)
TOK_PAR_CAR_SKILLS = 0.40     # listing des skills (régression tours 1)
TOK_PAR_CAR_INSTR = 0.51      # CLAUDE.md et mémoire, français (régression tours 1)
HARNAIS_TOKENS = 30_000       # prompt système + définitions d'outils (constante de régression)
PRIX_LECTURE = {"opus": 0.5, "sonnet": 0.2, "fable": 0.25, "haiku": 0.1}  # $/Mtok lecture de cache


def famille(model: str) -> str:
    m = (model or "").lower()
    for f in ("opus", "sonnet", "fable", "haiku"):
        if f in m:
            return f
    return "?"


def texte(c) -> str:
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        out = []
        for b in c:
            if isinstance(b, dict):
                if isinstance(b.get("text"), str):
                    out.append(b["text"])
                elif "content" in b:
                    out.append(texte(b["content"]))
        return "".join(out)
    return ""


def rendu(rec) -> int:
    r = rec.get("rendered")
    n = 0
    if isinstance(r, list):
        for b in r:
            if isinstance(b, dict) and isinstance(b.get("content"), str):
                n += len(b["content"])
    return n


def transcripts(jours: float):
    t0 = time.time() - jours * 86400
    for path in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")):
        if os.path.getmtime(path) >= t0:
            yield path


def lire(path):
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return
    with fh:
        for ligne in fh:
            try:
                rec = json.loads(ligne)
            except Exception:
                continue
            if isinstance(rec, dict) and not rec.get("isSidechain"):
                yield rec


# ---------------------------------------------------------------- prefixe

def tour1(path):
    """Composants du dernier envoi avant le premier appel API (un prompt resoumis n'est pas doublé)."""
    envoi = None
    for rec in lire(path):
        t = rec.get("type")
        if t == "user":
            c = rec.get("message", {}).get("content")
            if isinstance(c, str) and "command-name" not in c and "local-command" not in c:
                envoi = collections.Counter(prompt=len(c))
        elif t == "attachment" and envoi is not None:
            a = rec.get("attachment", {})
            k = a.get("type")
            if k == "skill_listing":
                envoi["skill_listing"] = len(a.get("content") or "")
            elif k == "instructions":
                for f in a.get("files", []):
                    p = f.get("path", "")
                    kk = ("memoire" if "/memory/" in p else "claude_md_global" if p.endswith("/.claude/CLAUDE.md")
                          else "claude_md_projet")
                    envoi[kk] += len(f.get("content") or "")
            elif k == "prompt_snapshot":
                sp = a.get("systemPrompt")
                envoi["prompt_systeme"] = sum(len(x) for x in sp) if isinstance(sp, list) else 0
            elif k == "hook_additional_context":
                envoi["hooks"] += rendu(rec)
            else:
                envoi["divers"] += rendu(rec)
        elif t == "assistant":
            m = rec.get("message", {})
            u = m.get("usage") or {}
            tot = sum((u.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
            if tot and envoi is not None and m.get("model") != "<synthetic>":
                return tot, m.get("model"), envoi
    return None


def mode_prefixe(args):
    rows = []
    for path in transcripts(args.jours):
        r = tour1(path)
        if r:
            rows.append((os.path.basename(os.path.dirname(path)), os.path.basename(path)[:8], *r))
    if not rows:
        print("aucun tour 1 trouvé")
        return
    print(f"{len(rows)} tours 1 sur {args.jours:.0f} j ; tokens médians {st.median(r[2] for r in rows)/1000:.0f} k")
    print("\nDécomposition du préfixe (médianes, caractères → tokens estimés) :")
    comp = collections.defaultdict(list)
    for r in rows:
        for k, v in r[4].items():
            comp[k].append(v)
    conv = {"skill_listing": TOK_PAR_CAR_SKILLS, "claude_md_global": TOK_PAR_CAR_INSTR, "claude_md_projet": TOK_PAR_CAR_INSTR,
            "memoire": TOK_PAR_CAR_INSTR, "prompt_systeme": 0.0}
    total_tok = HARNAIS_TOKENS
    lignes = []
    for k, vs in comp.items():
        med = st.median(vs)
        tok = med * conv.get(k, TOK_PAR_CAR_RESULTAT)
        total_tok += tok
        lignes.append((tok, med, k))
    lignes.append((HARNAIS_TOKENS, 0, "harnais (prompt système + définitions d'outils, constante)"))
    for tok, med, k in sorted(lignes, reverse=True):
        print(f"  {tok/1000:6.1f} k tok {100*tok/total_tok:5.1f} %  {med/1000:6.1f} k car  {k}")
    print(f"  {'':>10s} total estimé {total_tok/1000:.0f} k (médiane mesurée {st.median(r[2] for r in rows)/1000:.0f} k)")
    # listing des skills par plugin, sur la session la plus récente qui l'a
    for path in sorted(transcripts(args.jours), key=os.path.getmtime, reverse=True):
        lst = None
        for rec in lire(path):
            if rec.get("type") == "attachment" and rec["attachment"].get("type") == "skill_listing":
                lst = rec["attachment"].get("content") or ""
                break
            if rec.get("type") == "assistant":
                break
        if lst:
            grp = collections.Counter()
            n = collections.Counter()
            for x in lst.split("\n"):
                if not x.startswith("- "):
                    continue
                nom = x[2:].split(":", 1)[0]
                plug = nom.split(":")[0] if ":" in x[2:].split(" ", 1)[0].rstrip(":") else "(personnel/builtin)"
                grp[plug] += len(x)
                n[plug] += 1
            print(f"\nListing des skills par plugin (session {os.path.basename(path)[:8]}, {len(lst)/1000:.0f} k car ≈ {len(lst)*TOK_PAR_CAR_SKILLS/1000:.0f} k tokens) :")
            for k, v in grp.most_common():
                print(f"  {v/1000:6.1f} k car ≈ {v*TOK_PAR_CAR_SKILLS/1000:5.1f} k tok  {n[k]:4d} skills  {k}")
            break
    if args.json:
        json.dump([{"slug": r[0], "sess": r[1], "tokens": r[2], "model": r[3], **r[4]} for r in rows], sys.stdout, ensure_ascii=False)


# ---------------------------------------------------------------- integrale

def session_events(path):
    """Événements ordonnés : ('REQ', ctx, out, think, model, mid) ; ('ASSIST', mid) une fois par
    message ; ('résultat:<outil>', chars) ; ('rappels/hooks', chars) ; ('prompt utilisateur', chars) ;
    ('HUMAN',). Les caractères écrits par l'assistant sont cumulés PAR MESSAGE dans `chars_par_msg`
    (un même message est journalisé sur plusieurs lignes, une par bloc de contenu)."""
    ev = []
    id2tool = {}
    seen = set()
    chars_par_msg = collections.defaultdict(collections.Counter)
    for rec in lire(path):
        t = rec.get("type")
        if t == "attachment":
            a = rec.get("attachment", {})
            if a.get("type") in ("skill_listing", "instructions", "prompt_snapshot"):
                continue
            n = rendu(rec)
            if n:
                ev.append(("rappels/hooks", n))
        elif t == "user":
            c = rec.get("message", {}).get("content")
            if isinstance(c, str):
                if "local-command" not in c:
                    ev.append(("HUMAN",))
                ev.append(("prompt utilisateur", len(c)))
            elif isinstance(c, list):
                for b in c:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "tool_result":
                        ev.append(("résultat d'outil:" + str(id2tool.get(b.get("tool_use_id"), "?")), len(texte(b.get("content")))))
                    elif b.get("type") == "text":
                        ev.append(("HUMAN",))
                        ev.append(("prompt utilisateur", len(b.get("text", ""))))
        elif t == "assistant":
            m = rec.get("message", {})
            mid = m.get("id") or rec.get("uuid")
            chars = chars_par_msg[mid]
            for b in m.get("content") or []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "tool_use":
                    id2tool[b.get("id")] = b.get("name")
                    chars["entrée d'outil:" + str(b.get("name"))] += len(json.dumps(b.get("input", {}), ensure_ascii=False))
                elif b.get("type") == "text":
                    chars["texte assistant"] += len(b.get("text", ""))
            u = m.get("usage")
            if not u or mid in seen or m.get("model") == "<synthetic>":
                continue
            tot = sum((u.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
            if not tot:
                continue
            seen.add(mid)
            ev.append(("REQ", tot, u.get("output_tokens") or 0, (u.get("output_tokens_details") or {}).get("thinking_tokens", 0), m.get("model"), mid))
    return ev, chars_par_msg


def integrale_session(ev, chars_par_msg):
    """Contribution de chaque origine à Σ contexte (chaque ajout relu par les requêtes suivantes)."""
    reqs = [e for e in ev if e[0] == "REQ"]
    N = len(reqs)
    if N == 0:
        return None
    contrib = collections.Counter()
    ajout = collections.Counter()
    contrib["préfixe (tour 1)"] = reqs[0][1] * N
    k = 0
    for e in ev:
        if e[0] == "REQ":
            k += 1
            out, think, mid = e[2], e[3], e[5]
            contrib["réflexion"] += think * (N - k)
            ajout["réflexion"] += think
            ch = chars_par_msg.get(mid) or {}
            tch = sum(ch.values()) or 1
            for typ, n in ch.items():
                tok = (out - think) * n / tch
                contrib[typ] += tok * (N - k)
                ajout[typ] += tok
            continue
        if e[0] == "HUMAN":
            continue
        typ, n = e
        tok = n * TOK_PAR_CAR_RESULTAT
        contrib[typ] += tok * (N - k)
        ajout[typ] += tok
    return {"N": N, "lus": sum(r[1] for r in reqs), "ctx_t1": reqs[0][1], "contrib": contrib, "ajout": ajout,
            "fam": famille(collections.Counter(r[4] for r in reqs).most_common(1)[0][0])}


def mode_integrale(args):
    sessions = []
    heredoc = [0, 0, 0, 0]  # appels, car, appels heredoc, car heredoc
    for path in transcripts(args.jours):
        ev, chars_par_msg = session_events(path)
        s = integrale_session(ev, chars_par_msg)
        if not s or (args.famille != "toutes" and s["fam"] != args.famille):
            continue
        s["slug"] = os.path.basename(os.path.dirname(path))
        s["sess"] = os.path.basename(path)[:8]
        s["n_clear"] = sum(1 for rec in lire(path) if rec.get("type") == "user" and isinstance(rec.get("message", {}).get("content"), str) and "<command-name>/clear" in rec["message"]["content"])
        sessions.append(s)
        for rec in lire(path):
            if rec.get("type") != "assistant":
                continue
            for b in rec.get("message", {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Bash":
                    cmd = (b.get("input") or {}).get("command") or ""
                    heredoc[0] += 1
                    heredoc[1] += len(cmd)
                    if "<<" in cmd:
                        heredoc[2] += 1
                        heredoc[3] += len(cmd)
    if not sessions:
        print("aucune session")
        return
    lus = sum(s["lus"] for s in sessions)
    N = sum(s["N"] for s in sessions)
    agg = collections.Counter()
    ajout = collections.Counter()
    for s in sessions:
        agg.update(s["contrib"])
        ajout.update(s["ajout"])
    recon = sum(agg.values())
    print(f"{len(sessions)} sessions {args.famille} sur {args.jours:.0f} j : {N} requêtes, {lus/1e6:.0f} M tokens lus (mesuré), "
          f"reconstitué {100*recon/lus:.0f} % ; contexte moyen pondéré {lus/N/1000:.0f} k ; préfixe médian {st.median(s['ctx_t1'] for s in sessions)/1000:.0f} k")
    grp = collections.Counter()
    for k, v in agg.items():
        grp[k.split(":")[0]] += v
    print("\nPart de l'intégrale des tokens lus (= du coût), par origine :")
    for k, v in grp.most_common():
        print(f"  {100*v/recon:5.1f} %  {k}")
    print("\nDétail par outil (part de l'intégrale) :")
    for k, v in agg.most_common(14):
        if ":" in k:
            print(f"  {100*v/recon:5.1f} %  {k}")
    TA = sum(ajout.values())
    print("\nTokens ajoutés au contexte (sans pondération) :")
    for k, v in ajout.most_common(8):
        print(f"  {100*v/TA:5.1f} %  {v/1e6:6.2f} M  {k}")
    if heredoc[0]:
        print(f"\nEntrées Bash : {heredoc[0]} appels, {heredoc[1]/1e6:.1f} M car ; heredocs (`<<`) : {heredoc[2]} appels "
              f"({100*heredoc[2]/heredoc[0]:.0f} %) portant {100*heredoc[3]/max(heredoc[1],1):.0f} % des caractères")
    longues = [s for s in sessions if s["N"] > 300]
    print(f"\nSessions > 300 requêtes : {len(longues)}/{len(sessions)}, {100*sum(s['lus'] for s in longues)/lus:.0f} % des tokens lus, "
          f"dont {sum(1 for s in longues if s['n_clear']==0)} sans aucun /clear")
    print("\nTop 10 sessions (M tokens lus, requêtes, contexte moyen, /clear) :")
    for s in sorted(sessions, key=lambda s: -s["lus"])[:10]:
        print(f"  {s['lus']/1e6:6.0f} M {s['N']:5d} req {s['lus']/s['N']/1000:5.0f} k  clear={s['n_clear']}  {s['slug'][-30:]}/{s['sess']}")
    if args.json:
        json.dump([{k: (dict(v) if isinstance(v, collections.Counter) else v) for k, v in s.items()} for s in sessions], sys.stdout, ensure_ascii=False)


# ---------------------------------------------------------------- clear

def mode_clear(args):
    sess = []
    for path in transcripts(args.jours):
        ctx, front, models = [], [], collections.Counter()
        human = False
        vus = set()
        for rec in lire(path):
            t = rec.get("type")
            if t == "user":
                c = rec.get("message", {}).get("content")
                if isinstance(c, str) and "local-command" not in c:
                    human = True
            elif t == "assistant":
                m = rec.get("message", {})
                u = m.get("usage") or {}
                if m.get("model") == "<synthetic>":
                    continue
                tot = sum((u.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
                if not tot or m.get("id") in vus:
                    continue
                vus.add(m.get("id"))
                ctx.append(tot)
                front.append(human)
                human = False
                models[famille(m.get("model"))] += 1
        if len(ctx) < 5:
            continue
        fam = models.most_common(1)[0][0]
        if args.famille != "toutes" and fam != args.famille:
            continue
        sess.append((ctx, front, fam))

    def rejoue(ctx, front, seuil):
        base = ctx[0]
        cur = base
        tot = 0
        coupes = 0
        for i, c in enumerate(ctx):
            if i > 0:
                aj = max(0, ctx[i] - ctx[i - 1])
                if front[i] and cur + aj > seuil and i < len(ctx) - 1:
                    cur = base + args.amorce
                    coupes += 1
                cur += aj
            tot += cur
        return tot, coupes

    reel = sum(sum(c) for c, _, _ in sess)
    reel_usd = sum(sum(c) * PRIX_LECTURE.get(f, 0.3) / 1e6 for c, _, f in sess)
    print(f"{len(sess)} sessions {args.famille} sur {args.jours:.0f} j ; amorce de reprise {args.amorce/1000:.0f} k tokens ; "
          f"réel {reel/1e6:.0f} M tokens lus ({reel_usd:.0f} $-éq de lecture de cache)")
    print(f"{'seuil':>7s} {'tokens lus':>11s} {'économie':>9s} {'coupes':>7s} {'$-éq/période':>13s}")
    for seuil in (150e3, 200e3, 250e3, 300e3, 400e3, 500e3):
        tot = usd = nc = 0
        for c, fr, f in sess:
            t_, k_ = rejoue(c, fr, seuil)
            tot += t_
            nc += k_
            usd += t_ * PRIX_LECTURE.get(f, 0.3) / 1e6
        print(f"{seuil/1000:6.0f}k {tot/1e6:10.0f}M {100*(1-tot/reel):8.0f}% {nc:7d} {reel_usd-usd:12.0f}")
    bandes = [(0, 150), (150, 250), (250, 400), (400, 600), (600, 1000)]
    cnt = collections.Counter()
    w = collections.Counter()
    for ctx_s, _, _ in sess:
        for x in ctx_s:
            for a, b in bandes:
                if a * 1000 <= x < b * 1000:
                    cnt[(a, b)] += 1
                    w[(a, b)] += x
    T, W = sum(cnt.values()), sum(w.values())
    print("\nOù se font les requêtes (bande de contexte) :")
    for a, b in bandes:
        print(f"  {a:4d}-{b:4d} k : {100*cnt[(a,b)]/T:5.1f} % des requêtes, {100*w[(a,b)]/W:5.1f} % des tokens lus")
    print("\nHypothèses : même travail après la coupe (mêmes ajouts), coupe seulement à une frontière de tour humain, "
          "reprise = préfixe + amorce. Estimation haute : une vraie coupe fait relire des fichiers.")


# ---------------------------------------------------------------- alleger

PLUGINS_CONNUS = {
    "bio": ["bio_pathogens@guyeux-claude-plugins", "bio_bacteria@guyeux-claude-plugins"],
    "redac": ["redac@guyeux-claude-plugins"],
}


def _listing_local() -> dict:
    """Taille du listing des skills par plugin, depuis le transcript le plus récent qui en porte un."""
    for path in sorted(glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")), key=os.path.getmtime, reverse=True):
        for rec in lire(path):
            if rec.get("type") == "attachment" and rec["attachment"].get("type") == "skill_listing":
                par = collections.Counter()
                for x in (rec["attachment"].get("content") or "").split("\n"):
                    if x.startswith("- "):
                        tete = x[2:].split(" ", 1)[0]
                        par[tete.split(":")[0] if ":" in tete.rstrip(":") else "(autres)"] += len(x)
                return par
            if rec.get("type") == "assistant":
                break
    return collections.Counter()


def mode_alleger(args):
    plugins = []
    for nom in args.plugins:
        plugins.extend(PLUGINS_CONNUS.get(nom, [nom]))
    par_plugin = _listing_local()
    gain_car = sum(par_plugin.get(p.split("@")[0], 0) for p in plugins)
    print(f"Plugins à désactiver : {', '.join(plugins)}")
    if gain_car:
        print(f"Gain estimé par session ouverte dans ces répertoires : {gain_car/1000:.0f} k caractères de listing "
              f"≈ {gain_car*TOK_PAR_CAR_SKILLS/1000:.0f} k tokens de préfixe, relus à chaque requête.")
    print(f"{'état':10s} {'fichier':60s} action")
    for rep in args.repertoires:
        rep = os.path.abspath(os.path.expanduser(rep))
        if not os.path.isdir(rep):
            print(f"{'ABSENT':10s} {rep[:60]:60s} ignoré")
            continue
        if os.path.realpath(rep) == os.path.realpath(os.path.expanduser("~")):
            print(f"{'REFUS':10s} {rep[:60]:60s} le home porte déjà les réglages GLOBAUX, ne pas y poser de réglage projet")
            continue
        f = os.path.join(rep, ".claude", "settings.local.json")
        data = {}
        if os.path.exists(f):
            try:
                data = json.load(open(f, encoding="utf-8"))
            except Exception:
                print(f"{'ILLISIBLE':10s} {f[:60]:60s} laissé tel quel")
                continue
        ep = dict(data.get("enabledPlugins") or {})
        cible = False if not args.retablir else True
        manquants = [p for p in plugins if ep.get(p) is not cible]
        if not manquants:
            print(f"{'DÉJÀ OK':10s} {f[:60]:60s} —")
            continue
        for p in manquants:
            ep[p] = cible
        data["enabledPlugins"] = ep
        if not args.apply:
            print(f"{'À FAIRE':10s} {f[:60]:60s} {'activer' if cible else 'désactiver'} {len(manquants)} plugin(s)")
            continue
        os.makedirs(os.path.dirname(f), exist_ok=True)
        if os.path.exists(f):
            sauv = f + ".bak_alleger_" + time.strftime("%Y%m%d_%H%M%S")
            with open(sauv, "w", encoding="utf-8") as fh:
                json.dump(json.load(open(f, encoding="utf-8")), fh, indent=2, ensure_ascii=False)
        with open(f, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print(f"{'ÉCRIT':10s} {f[:60]:60s} {'activé' if cible else 'désactivé'} : {', '.join(manquants)}")
    if not args.apply:
        print("\n(dry-run : rien n'a été écrit, relancer avec --apply)")
    print("Rappel : le réglage n'est PAS hérité par les sous-répertoires, et un skill retiré du listing "
          "reste invocable par son nom (`/nom`), il n'est plus que proposé spontanément.")


def main():
    ap = argparse.ArgumentParser(description="d'où vient le contexte relu à chaque requête, et ce que coûterait de le couper")
    sub = ap.add_subparsers(dest="mode", required=True)
    pa = sub.add_parser("alleger", help="poser le settings.local.json qui désactive des plugins de skills")
    pa.add_argument("repertoires", nargs="+", help="répertoires de projet à alléger")
    pa.add_argument("--plugins", nargs="+", default=["bio"], help="bio, redac, ou un identifiant complet plugin@marketplace")
    pa.add_argument("--apply", action="store_true", help="écrire (sans lui, dry-run)")
    pa.add_argument("--retablir", action="store_true", help="remettre les plugins à true au lieu de false")
    pa.set_defaults(fn=mode_alleger)
    for nom, fn in (("prefixe", mode_prefixe), ("integrale", mode_integrale), ("clear", mode_clear)):
        p = sub.add_parser(nom)
        p.add_argument("--jours", type=float, default=7)
        p.add_argument("--famille", default="opus" if nom != "prefixe" else "toutes", choices=["opus", "sonnet", "fable", "haiku", "toutes"])
        p.add_argument("--json", action="store_true")
        if nom == "clear":
            p.add_argument("--amorce", type=float, default=8000, help="tokens relus pour reprendre après une coupe")
        p.set_defaults(fn=fn)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
