# Rapport CCX-15 de parité Claude/Codex

Ce rapport compare des invariants observables. Il ne conserve aucun transcript ni valeur secrète.

- Scénarios : 18
- Réussis : 16
- Partiels : 2
- Bloqués : 0
- Échecs : 0
- Non exécutés : 0
- Matrice complète : oui

| scénario | famille | Claude | Codex | verdict | propriétaire |
|---|---|---|---|---|---|
| instructions-globales | instructions | pass | pass | pass | CCX-15 |
| doctrine-globale-session-neuve | instructions | pass | pass | pass | CCX-02/15 |
| projet-racine-espace | instructions | pass | pass | pass | CCX-15 |
| projet-sous-repertoire | instructions | pass | pass | pass | CCX-15 |
| chaine-instructions-volumineuse | instructions | pass | pass | pass | CCX-03 |
| projet-sans-registre | project-memory | pass | pass | pass | CCX-15 |
| kb-partagee | knowledge | pass | pass | pass | CCX-04 |
| memoire-native-separee | memory | pass | pass | pass | CCX-13 |
| skills-canoniques | skills | pass | pass | pass | CCX-11 |
| skill-challenge-declenche | skills | pass | pass | pass | CCX-05/15 |
| skill-desactive-absent | skills | pass | pass | pass | CCX-15 |
| plugins-personnels | plugins | pass | pass | pass | CCX-10 |
| hooks-demarrage-arret | hooks | partial | pass | partial | CCX-07/08 |
| suppression-bloquee | hooks | pass | pass | pass | CCX-07 |
| permissions-minimales | rules | pass | pass | pass | CCX-12 |
| mcp-configures | mcp | partial | pass | partial | CCX-14 |
| interface-native | interface | pass | pass | pass | CCX-14 |
| secrets-non-importes | negative | pass | pass | pass | CCX-01/15 |

## Écarts et limites

- `hooks-demarrage-arret` / claude : partial - le mode --print n'émet pas d'événement Stop exploitable (propriétaire : Claude-CLI).
- `mcp-configures` / claude : partial - connecteur personnel claude.ai (Booking.com), sans équivalent Codex requis (propriétaire : external-services).
- `mcp-configures` / codex : pass - Superhuman en connecteur distant (URL, sans OAuth local) des deux côtés ; URL tbannotator intentionnellement distincte (propriétaire : CCX-14).
