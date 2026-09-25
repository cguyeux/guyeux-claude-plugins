---
name: suite
description: Consigne la piste suivante à traiter (avec son étiquette [Modèle:effort]) juste avant un /clear délibéré, et fait réapparaître ce rappel automatiquement juste après le /clear, sans ressaisie. Use on `/suite`, or "note la piste suivante avant de clear", "prépare le clear", "rappelle-moi où reprendre après le clear".
---

# suite — rappel de piste après vidage de contexte

`/clear` est une commande CLI interceptée en amont du modèle : aucune commande
personnalisée ni aucun hook ne peut la déclencher elle-même (vérifié auprès de
`claude-code-guide` le 2026-09-16). `/suite` ne remplace donc pas `/clear` —
elle le **prépare** : elle écrit la piste ouverte la plus prioritaire du
projet courant (état, étiquette `[Modèle:effort]` déjà posée par
`/routage étiqueter`, titre), puis invite à taper `/clear` soi-même. Le hook
`SessionStart` (matcher `"clear"`) relit cette suggestion et la réaffiche
automatiquement dans le contexte de la nouvelle session, une seule fois.

## Exécution

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/suite/suite.py [argument]
```

`argument` est optionnel (correctif S7, 2026-09-22) :
- absent → comportement automatique inchangé (ci-dessous) ;
- un identifiant de piste existant du projet courant (`/suite P2.6`) → sa
  ligne d'index dans `pistes.md`/`pistes/<racine>.md` en fournit directement
  titre et étiquette, sans passer par le choix automatique ;
- tout autre texte (ne ressemblant pas à un identifiant, ou identifiant
  introuvable dans le projet) → repris tel quel comme amorce libre — utile
  pour porter un diagnostic ou une contrainte déjà rédigés au moment du
  `/clear`, sans attendre qu'ils soient recopiés dans `pistes.md`.

Sans argument, le script :
1. remonte depuis le répertoire courant jusqu'au premier `cahier_de_labo.md`
   (même convention que tous les autres skills à cahier) ;
2. si `pistes.md` existe, choisit la piste ouverte prioritaire — une `en
   cours` avant une `à faire`, dans l'ordre du fichier — via
   `carrefour.py::parse_pistes_tree` (pas `status.py`, qui ne reconnaît pas
   les identifiants hors rail à lettre seule comme `N6`/`S2` ; voir
   l'en-tête de `suite.py` pour le détail de ce choix) ; les fichiers de
   détail `pistes/<racine>.md` lus sont ceux dont la racine est détectée par
   `status.detecter_prefixes()` (correctif S8, 2026-09-22 : l'ancien glob
   figé `P*.md` rendait invisibles tous les projets à racines hors `P`, dont
   celui-ci) ;
3. écrit la suggestion dans `~/.claude/state/suite/<hash(root)>.md` ;
4. affiche la même suggestion à l'écran et invite à taper `/clear`.

Sans piste ouverte, ou hors d'un projet à cahier, le script le dit et
n'écrit rien (pas de suggestion périmée qui traînerait pour un `/clear`
sans rapport).

## Limite connue

Le choix de la piste « prioritaire » (sans argument) est mécanique (une
piste en cours avant une à faire, ordre du fichier) — il ne consulte pas
l'utilisateur et ne sait pas préférer une piste bloquante à une piste
secondaire. Donner explicitement l'identifiant voulu en argument (ci-dessus)
contourne cette limite sans avoir à réordonner ou clore une piste
indésirable.

## Écosystème

- Étiquettes `[Modèle:effort]` posées par le skill `/routage` — `/suite` ne
  recalcule jamais cette logique, il la lit.
- État affiché par `~/.claude/hooks/session_context.sh`, bloc `[SUITE — ...]`,
  seulement quand `source == "clear"`.
- Piste S de `environnement/pistes.md` porte la conception complète et les
  deux défauts d'outillage trouvés en la testant (voir cahier de labo du
  projet `environnement`, entrée du 2026-09-16).
