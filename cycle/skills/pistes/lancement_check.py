#!/usr/bin/env python3
"""
Objet: vérifier que le bilan de fin de tour ne contredit pas le registre de pistes sur le
    routage modèle/effort. Deux contrôles, déterministes :
    (1) la ligne « Lancement : » de « Enchaînement proposé » reprend EXACTEMENT l'étiquette
        [Modèle:effort] de la piste visée ;
    (2) chaque entrée « **ID** [Modèle:effort] » de « Pistes ouvertes » porte l'étiquette que
        le registre donne à cet identifiant.
Entrées: racine du projet ; --transcript (JSONL de la session : dernier message de
    l'assistant) ; --since (fichier dont le mtime marque le début de la session : la note
    DERNIERE_SESSION.md n'est contrôlée que si elle a été écrite depuis).
Sorties: rien et code 0 si tout concorde ; sinon un message par écart sur stdout, code 1.
Réutilisable: oui, appelé par ~/.claude/hooks/pistes_audit_stop.sh dans tout projet à
    `pistes.md`.
Date: 2026-09-24 (environnement, après une étiquette [Opus:high] listée pour AG3 alors que la
    ligne Lancement proposait Sonnet:medium pour la même piste).

Règle que ce contrôle rend exécutoire : une étiquette décrit le travail qui RESTE sur la
piste. Quand une phase se clôt et que le reste demande moins (ou plus), on révise l'étiquette
dans le registre au même moment ; la ligne Lancement ne s'en écarte jamais d'elle-même.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

MODELES = r"(Opus|Sonnet|Haiku|Fable)"
EFFORTS = r"(low|medium|high|xhigh|max)"
RE_ME = re.compile(MODELES + r"\s*:\s*" + EFFORTS, re.I)
RE_ETIQ = re.compile(r"\[\s*" + MODELES + r"\s*:\s*" + EFFORTS + r"\s*\]", re.I)
RE_ID = r"[A-Z]{1,3}\d+(?:\.\d+)*(?:bis|ter)?[a-z]?"
RE_ENTREE = re.compile(r"\*\*(" + RE_ID + r")\*\*\s*\[\s*" + MODELES + r"\s*:\s*" + EFFORTS
                       + r"\s*\]", re.I)
STATUS = Path(__file__).resolve().parent / "status.py"


def norme(modele, effort):
    return f"{modele.capitalize()}:{effort.lower()}"


def etiquettes_registre(racine):
    """{identifiant: 'Modèle:effort'} pour les pistes ouvertes étiquetées, via status.py."""
    try:
        r = subprocess.run([sys.executable, str(STATUS), "--open"], cwd=racine,
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    reg = {}
    for ligne in r.stdout.splitlines():
        champs = ligne.split("\t")
        if not champs or not champs[0].strip():
            continue
        m = RE_ETIQ.search(champs[-1]) if len(champs) > 1 else None
        if m:
            reg[champs[0].strip()] = norme(m.group(1), m.group(2))
    return reg


def section(texte, titre):
    """Corps de la section dont le titre contient `titre`, jusqu'au titre suivant."""
    lignes, dedans, corps = texte.splitlines(), False, []
    for l in lignes:
        if re.match(r"\s*#{1,6}\s", l):
            if dedans:
                break
            dedans = titre.lower() in l.lower()
            continue
        if dedans:
            corps.append(l)
    return "\n".join(corps) if dedans or corps else ""


def piste_visee(corps, reg):
    m = re.search(r"[Pp]iste vis[ée]e\s*:?\s*\**\s*(" + RE_ID + r")", corps)
    if m:
        return m.group(1)
    for ident in re.findall(r"\b(" + RE_ID + r")\b", corps):
        if ident in reg:
            return ident
    return None


def controle(texte, reg, source):
    ecarts = []
    ench = section(texte, "Enchaînement proposé") or section(texte, "Enchainement propose")
    if ench:
        # Le paragraphe « Lancement » est souvent enveloppé manuellement sur plusieurs
        # lignes physiques (prose à ~80-90 caractères) : ne retenir que la première ligne
        # physique raterait un Modèle:effort placé après le retour à la ligne. On rejoint
        # donc les lignes du paragraphe (jusqu'à la première ligne vide) avant de chercher.
        lignes_ench = ench.splitlines()
        idx = next((i for i, l in enumerate(lignes_ench) if re.match(r"\W*Lancement", l)), None)
        ligne = None
        if idx is not None:
            paragraphe = [lignes_ench[idx]]
            for suite in lignes_ench[idx + 1:]:
                if not suite.strip():
                    break
                paragraphe.append(suite)
            ligne = " ".join(paragraphe)
        visee = piste_visee(ench, reg)
        if ligne and visee and visee in reg:
            m = RE_ME.search(ligne)
            if m is None:
                ecarts.append(f"[{source}] la ligne « Lancement » ne donne pas de Modèle:effort, "
                              f"alors que la piste visée {visee} est étiquetée [{reg[visee]}].")
            elif norme(m.group(1), m.group(2)) != reg[visee]:
                ecarts.append(
                    f"[{source}] « Lancement » propose {norme(m.group(1), m.group(2))} pour la "
                    f"piste {visee}, que le registre étiquette [{reg[visee]}].")
    ouvertes = section(texte, "Pistes ouvertes")
    for ident, mod, eff in RE_ENTREE.findall(ouvertes):
        if ident in reg and norme(mod, eff) != reg[ident]:
            ecarts.append(f"[{source}] « Pistes ouvertes » donne [{norme(mod, eff)}] à {ident}, "
                          f"que le registre étiquette [{reg[ident]}].")
    return ecarts


def dernier_message(transcript):
    """Texte du dernier tour de l'assistant (blocs texte depuis le dernier message humain)."""
    try:
        lignes = Path(transcript).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    textes = []
    for brut in lignes:
        try:
            e = json.loads(brut)
        except ValueError:
            continue
        msg = e.get("message") or {}
        contenu = msg.get("content")
        if e.get("type") == "user":
            humain = isinstance(contenu, str) or (
                isinstance(contenu, list)
                and any(isinstance(b, dict) and b.get("type") == "text" for b in contenu))
            if humain:
                textes = []
        elif e.get("type") == "assistant" and isinstance(contenu, list):
            textes += [b.get("text", "") for b in contenu
                       if isinstance(b, dict) and b.get("type") == "text"]
    return "\n".join(textes)


def main():
    p = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[1])
    p.add_argument("racine")
    p.add_argument("--transcript")
    p.add_argument("--since", help="fichier dont le mtime marque le début de la session")
    a = p.parse_args()

    racine = Path(a.racine)
    reg = etiquettes_registre(racine)
    if not reg:
        return 0
    ecarts = []
    if a.transcript:
        texte = dernier_message(a.transcript)
        if texte:
            ecarts += controle(texte, reg, "bilan affiché")
    note = racine / "DERNIERE_SESSION.md"
    debut = Path(a.since).stat().st_mtime if a.since and Path(a.since).exists() else None
    if note.exists() and (debut is None or note.stat().st_mtime > debut):
        ecarts += controle(note.read_text(encoding="utf-8", errors="replace"), reg,
                           "DERNIERE_SESSION.md")
    if not ecarts:
        return 0
    print("Routage incohérent entre le bilan et le registre de pistes :")
    for e in ecarts:
        print("  - " + e)
    print("Une étiquette décrit le travail qui RESTE. Si le reste de la piste demande une autre "
          "configuration, réviser d'abord l'étiquette dans le registre (pistes.md ou pistes/<X>.md, "
          "en notant pourquoi) ; sinon, aligner le bilan sur l'étiquette. Jamais les deux "
          "versions à la fois.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
