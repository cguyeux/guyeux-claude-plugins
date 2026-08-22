#!/usr/bin/env python3
"""Etat instantane des deux machines de calcul distantes (mp, mh) et recommandation.

POURQUOI SONDER AVANT DE DECIDER
--------------------------------
L'inventaire statique (nombre de coeurs, RAM totale) ne suffit pas a choisir ou
lancer un calcul. Ce qui decide, c'est l'etat du moment :

  * sur `mp`, il n'y a AUCUN ordonnanceur. Deux calculs lances en meme temps se
    battent pour les 64 threads, et le pipeline TBannotator (Snakemake) peut
    tourner sans crier gare. Sonder = verifier qu'on ne va pas ecraser un run.
  * sur `mh`, tout passe par Slurm. Un nombre de coeurs "disponibles" ne veut
    rien dire si la partition est pleine ou si les noeuds sont en `drain`. Au
    sondage du 2026-08-17, 3 des 5 noeuds GPU etaient drain/inval.
  * les deux ont un disque presque plein a un endroit precis : `/` sur `mp`
    (97 %), `$HOME` sur `mh` (quota NFS 20 Go). Ecrire au mauvais endroit fait
    echouer le job en plein calcul.

PREREQUIS : VPN monte (`sudo vpn up`). Sans lui, les deux machines sont
injoignables et le symptome ressemble a une panne serveur (`banner exchange`).

USAGE
  python3 remote_probe.py                       # etat des deux machines
  python3 remote_probe.py --need gpu            # + recommandation ciblee
  python3 remote_probe.py --need ram=400        # 400 Go de RAM
  python3 remote_probe.py --need disk=5000      # 5 To d'espace de travail
  python3 remote_probe.py --need cpus=48,hours=72
  python3 remote_probe.py --json

CODES DE SORTIE
  0 = au moins une machine joignable ; 2 = aucune (VPN ?).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

SSH_OPTS = ["-o", "ConnectTimeout=20", "-o", "BatchMode=yes"]

# --- mp : machine autonome, sans ordonnanceur -------------------------------- #
MP_CMD = r"""
echo "@load"; cat /proc/loadavg | cut -d' ' -f1-3
echo "@ram"; free -g | awk '/^Mem:/{print $2" "$7}'
echo "@data"; df -BG --output=size,avail /data 2>/dev/null | tail -1
echo "@root"; df -BG --output=size,avail,pcent / | tail -1
echo "@busy"; ps -eo pcpu,rss,etime,cmd --sort=-pcpu | awk 'NR>1 && $1>20' | head -5
# Detection du pipeline : le motif doit etre ecrit de facon a ne PAS apparaitre
# tel quel dans la ligne de commande qui le cherche, sinon la sonde se compte
# elle-meme (piege verifie le 2026-08-17 : faux "pipeline EN COURS"). On exclut
# aussi les wrappers `bash -c` d'une session ssh.
echo "@pipeline"; ps -eo cmd | grep "snakemak[e]" | grep -v "bash -c" | grep -cv "^grep" || true
echo "@users"; who | wc -l
"""

# --- mh : frontale Slurm ----------------------------------------------------- #
# `bash -lc` est OBLIGATOIRE des qu'on veut `module` : en ssh non interactif la
# fonction shell de Lmod n'est pas definie et `module load` echoue en silence.
MH_CMD = r"""
echo "@load"; cat /proc/loadavg | cut -d' ' -f1-3
echo "@idle"; sinfo -h -o "%P|%n|%c|%m|%G|%t" | grep -E "idle|mix"
echo "@pending"; squeue -h -t PD | wc -l
echo "@mine"; squeue -h -u $USER -o "%.10i %.9P %.2t %.10M %R" | head -10
echo "@work"; beegfs-ctl --getquota --uid $USER --mount=/Work 2>/dev/null | tail -1
echo "@home"; du -s --block-size=1G $HOME 2>/dev/null | cut -f1
echo "@scratch"; df -BG --output=size,avail /Scratch 2>/dev/null | tail -1
"""


def ssh(host: str, cmd: str, timeout: int = 90) -> str | None:
    try:
        res = subprocess.run(["ssh", *SSH_OPTS, host, cmd],
                             capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None
    return res.stdout if res.returncode == 0 else (res.stdout or None)


def sections(out: str) -> dict[str, list[str]]:
    cur, d = None, {}
    for line in out.splitlines():
        if line.startswith("@"):
            cur = line[1:].strip()
            d[cur] = []
        elif cur:
            d[cur].append(line.rstrip())
    return d


def probe_mp() -> dict:
    out = ssh("mp", MP_CMD)
    if out is None:
        return {"host": "mp", "reachable": False}
    s = sections(out)
    ram = (s.get("ram") or ["0 0"])[0].split()
    data = (s.get("data") or ["0G 0G"])[0].split()
    root = (s.get("root") or ["0G 0G 0%"])[0].split()
    return {
        "host": "mp", "reachable": True,
        "load": " ".join(s.get("load", ["?"])[0].split()),
        "ram_total_gb": int(ram[0]) if ram and ram[0].isdigit() else None,
        "ram_free_gb": int(ram[1]) if len(ram) > 1 and ram[1].isdigit() else None,
        "data_avail_gb": int(data[1].rstrip("G")) if len(data) > 1 else None,
        "root_pct": root[2] if len(root) > 2 else "?",
        "busy": [l for l in s.get("busy", []) if l.strip()],
        "pipeline_running": (s.get("pipeline") or ["0"])[0].strip() not in ("0", ""),
        "users": (s.get("users") or ["?"])[0].strip(),
    }


def probe_mh() -> dict:
    out = ssh("mh", MH_CMD)
    if out is None:
        return {"host": "mh", "reachable": False}
    s = sections(out)
    nodes = []
    for line in s.get("idle", []):
        parts = line.split("|")
        if len(parts) == 6:
            nodes.append({"partition": parts[0].rstrip("*"), "node": parts[1],
                          "cpus": parts[2], "mem_mb": parts[3],
                          "gres": parts[4], "state": parts[5]})
    work = (s.get("work") or [""])[0]
    m = re.search(r"\|\s*([\d.]+)\s*(\w+)\|\s*([\d.]+)\s*(\w+)\|", work)
    return {
        "host": "mh", "reachable": True,
        "load": " ".join(s.get("load", ["?"])[0].split()),
        "nodes": nodes,
        "pending": (s.get("pending") or ["?"])[0].strip(),
        "my_jobs": [l for l in s.get("mine", []) if l.strip()],
        "work_used": f"{m.group(1)} {m.group(2)}" if m else "?",
        "work_quota": f"{m.group(3)} {m.group(4)}" if m else "?",
        "home_gb": (s.get("home") or ["?"])[0].strip(),
        "scratch_avail_gb": ((s.get("scratch") or ["? ?"])[0].split() + ["?"])[1],
    }


# --------------------------------------------------------------------------- #
# Recommandation
# --------------------------------------------------------------------------- #

def recommend(need: dict, mp: dict, mh: dict) -> list[str]:
    """Regles explicites, volontairement peu nombreuses. Elles encodent les
    contraintes STRUCTURELLES des deux machines, pas des preferences."""
    out: list[str] = []
    gpu = need.get("gpu")
    ram = need.get("ram")
    disk = need.get("disk")
    cpus = need.get("cpus")
    hours = need.get("hours")

    if gpu:
        free = [n for n in mh.get("nodes", []) if "gpu:" in n["gres"]]
        if not mh.get("reachable"):
            out.append("GPU demande mais mh injoignable : aucun GPU ailleurs, pas de repli.")
        elif free:
            out.append("mh, partition gpu (A100 40 Go) ou gpu_l40 (L40) : "
                       + ", ".join(f"{n['node']}({n['gres']},{n['state']})" for n in free))
        else:
            out.append("mh : aucun noeud GPU libre a l'instant, le job attendra en file. "
                       "Verifier `sinfo -p gpu` avant de promettre un delai.")
        out.append("mp n'a AUCUN GPU : ne jamais y router un calcul CUDA.")

    if ram:
        if ram > 500:
            out.append(f"{ram} Go : seuls mh `bigmem` (1 To) et `gpu_l40` (1 To) tiennent. "
                       "mp plafonne a 125 Go.")
        elif ram > 125:
            out.append(f"{ram} Go : depasse mp (125 Go). Aller sur mh, partition "
                       "`gpu`/`bigmem` (515 Go a 1 To) ; `smp` et `mpi` n'offrent que ~95 Go/noeud.")
        elif mp.get("reachable") and (mp.get("ram_free_gb") or 0) >= ram:
            out.append(f"{ram} Go : mp suffit ({mp['ram_free_gb']} Go libres) et evite la file d'attente.")

    if disk:
        if disk > 800:
            out.append(f"{disk} Go d'espace : mp `/data` uniquement "
                       f"({mp.get('data_avail_gb')} Go libres). Le quota BeeGFS de mh est de 1 Tio, "
                       "dont 221 Gio deja pris.")
        else:
            out.append(f"{disk} Go d'espace : mp `/data/cguyeux` ou mh `/Work/Users/cguyeux` "
                       "(verifier le quota ci-dessus). JAMAIS `$HOME` ni `/` sur mp.")

    if hours and hours > 192:
        out.append(f"{hours} h : depasse le MaxTime Slurm de 8 jours (12 j sur gpu). "
                   "Soit decouper en jobs avec reprise, soit lancer sur mp (pas de limite de temps).")

    if cpus:
        if cpus > 64:
            out.append(f"{cpus} coeurs : mp n'en a que 64 (32 physiques x2 HT). "
                       "Au-dela, mh multi-noeuds (`mpi`, 24 c/noeud) avec un code qui sait le faire.")
        elif mp.get("reachable") and not mp.get("pipeline_running"):
            out.append(f"{cpus} coeurs : mp est libre (load {mp.get('load')}), "
                       "disponible immediatement, sans file.")

    if mp.get("pipeline_running"):
        out.append("ATTENTION : un Snakemake tourne sur mp. Ne pas y lancer de calcul lourd "
                   "sans en parler, le pipeline TBannotator est prioritaire.")
    if not need:
        out.append("Aucun besoin precise (--need) : regle par defaut = beaucoup de disque ou "
                   "aucune attente -> mp ; GPU, tres grosse RAM ou multi-noeuds -> mh.")
    return out


def render(mp: dict, mh: dict, recos: list[str]) -> None:
    print("=" * 72)
    if not mp.get("reachable"):
        print("mp  INJOIGNABLE  (VPN tombe ? `sudo vpn up`)")
    else:
        print(f"mp  Xeon Gold 6226R, 64 threads, {mp['ram_total_gb']} Go RAM, pas de GPU, "
              f"pas d'ordonnanceur")
        print(f"    load {mp['load']} | RAM libre {mp['ram_free_gb']} Go | "
              f"/data libre {mp['data_avail_gb']} Go | / a {mp['root_pct']} | "
              f"{mp['users']} session(s)")
        print(f"    pipeline Snakemake : {'EN COURS' if mp['pipeline_running'] else 'arrete'}")
        for b in mp["busy"]:
            print(f"    occupe: {b[:100]}")

    print("-" * 72)
    if not mh.get("reachable"):
        print("mh  INJOIGNABLE  (VPN tombe ? `sudo vpn up`)")
    else:
        print(f"mh  frontale Slurm (mesohelios) | load {mh['load']} | "
              f"{mh['pending']} job(s) en attente sur le cluster")
        print(f"    /Work {mh['work_used']} / {mh['work_quota']} de quota | "
              f"$HOME {mh['home_gb']} Go (quota 20 Go) | /Scratch libre {mh['scratch_avail_gb']}")
        if mh["my_jobs"]:
            print("    mes jobs :")
            for j in mh["my_jobs"]:
                print(f"      {j}")
        else:
            print("    mes jobs : aucun")
        print("    noeuds disponibles (idle/mix) :")
        for n in mh["nodes"]:
            g = n["gres"] if n["gres"] not in ("(null)", "") else "-"
            print(f"      {n['partition']:9s} {n['node']:10s} {n['cpus']:>4s} c  "
                  f"{int(n['mem_mb'].rstrip('+')) // 1024:>5d} Go  {g:14s} {n['state']}")
    print("=" * 72)
    if recos:
        print("\nOU LANCER :")
        for r in recos:
            print(f"  - {r}")


def parse_need(spec: str | None) -> dict:
    need: dict = {}
    if not spec:
        return need
    for token in re.split(r"[,\s]+", spec):
        if not token:
            continue
        if token == "gpu":
            need["gpu"] = True
        elif "=" in token:
            k, v = token.split("=", 1)
            try:
                need[k] = float(v) if "." in v else int(v)
            except ValueError:
                need[k] = v
    return need


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--need", help="besoins : gpu, ram=<Go>, disk=<Go>, cpus=<n>, hours=<h>")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    mp, mh = probe_mp(), probe_mh()
    need = parse_need(args.need)
    recos = recommend(need, mp, mh)

    if args.json:
        print(json.dumps({"mp": mp, "mh": mh, "need": need, "recommendation": recos},
                         indent=2, ensure_ascii=False))
    else:
        render(mp, mh, recos)

    return 0 if (mp.get("reachable") or mh.get("reachable")) else 2


if __name__ == "__main__":
    sys.exit(main())
