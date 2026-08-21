---
name: biotools
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST) for querying the ELIXIR
  bio.tools registry (~30 000 catalogued bioinformatics tools) and, crucially,
  diffing the result against the skills and knowledge base we already have, so a
  sweep returns what is genuinely new rather than what we already use. Use when:
  asking whether a published tool exists for a task before writing one, looking
  for independent implementations to cross-check a home-made method, doing a
  periodic watch on tooling for MTBC, mycobacteria, Yersinia or any bacterium, or
  checking whether a tool named in a manuscript is registered and still alive.
argument-hint: "--preset mtbc|mycobacteries|yersinia|mobilome | --termes \"terme1,terme2\""
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebFetch
---

# bio.tools : chercher un outil publié avant d'en écrire un

## Ce que ce skill apporte vraiment

Interroger bio.tools est trivial (`https://bio.tools/api/tool/?q=<terme>&format=json`, sans
authentification). Le travail utile est ailleurs : **une requête rend surtout ce qu'on connaît déjà,
noyé dans du hors-sujet**. Le script fait donc trois choses.

```bash
S=${CLAUDE_PLUGIN_ROOT}/skills/biotools/scripts/biotools_scan.py
python3 $S --preset mtbc --out rapport.md
python3 $S --preset yersinia --details        # + signaux de qualité des fiches
python3 $S --termes "spoligotyping,MIRU-VNTR"
```

1. Il **balaie plusieurs termes** en une passe : le registre n'a pas de notion de « domaine MTBC ».
2. Il **diffe contre le texte intégral de nos 255 SKILL.md et de la base de connaissances** : un outil
   déjà mentionné chez nous n'est pas une découverte. C'est le cœur du dispositif ; sans lui, un
   balayage de 169 outils est illisible.
3. Il **trie sur les champs de qualité de la fiche** (`--details`) : `homepage_status` signale un site
   mort, `maturity` et `publication` disent si l'outil est citable.

Mesure du premier balayage (2026-08-17, 16 termes) : **169 outils distincts, 27 déjà chez nous,
50 inconnus trouvés par un terme ciblant nos organismes**. Le triage de ces 50 est dans
`references/candidats_2026-08-17.md`.

## Paramètres d'API vérifiés

| paramètre | effet | vérifié |
|---|---|---|
| `q=` | recherche libre dans tout le texte de la fiche | oui |
| `name=` | nom exact | oui |
| `topic=` | terme EDAM (`"Microbial ecology"` → 599) | oui |
| `topicID=` | identifiant EDAM (`"topic_3301"` → 309) | oui |
| `operation=` | opération EDAM (`"Genotyping"` → 1762) | oui |
| `/api/tool/<biotoolsID>/` | fiche complète | oui |

Champs utiles de la fiche complète : `homepage_status`, `maturity`, `validated`, `confidence_flag`,
`license`, `publication` (DOI, PMID, PMCID, titre), `download`, `documentation`, `function.operation`
(EDAM), `topic`, `lastUpdate`.

## Trois pièges du registre, constatés

> [!WARNING]
> **`q=` cherche dans tout le texte, donc les termes polysémiques mentent.** « lineage barcode »
> remonte BARtab, CellDestiny et TedSim, qui font du **code-barres cellulaire** en transcriptomique et
> n'ont rien à voir avec un barcode de lignée bactérienne. Lire les descriptions, jamais les comptes.
>
> **Le domaine médical écrase la génomique** sur « tuberculosis » : radiologie et dépistage
> (DecXpert, Qure.ai, ScreenTB, mtTB, COTS, ATBdiscrimination) occupent une bonne part des résultats.
> Ce n'est pas du bruit d'indexation, ce sont de vrais outils, simplement hors de notre objet.
>
> **`page=N` échoue sur certaines requêtes** (réponse `{"detail": ...}`). Suivre le champ `next` de la
> réponse, qui est la pagination fiable. Et préférer plusieurs termes étroits à un terme vague, un
> `count` élevé ne garantissant pas que tout soit rendu.

## Ce que le registre ne dit pas

Une fiche bio.tools atteste une **déclaration**, pas un état de marche. Avant de recommander un outil
trouvé ici : vérifier que le dépôt vit (dernier commit), que la publication existe vraiment
(`lit-review`, ou le DOI du champ `publication`), et que l'outil s'installe. Un `homepage_status`
non nul est un signal, son absence n'est pas une garantie.

Utile aussi dans l'autre sens : **nos propres outils y sont indexés** (MTBC Gene Atlas,
CRISPRbuilder-TB, SpolLineages), donc le registre sert à vérifier comment ils sont décrits et si leur
fiche est à jour.

## Quand l'utiliser

- **Avant d'écrire un script non trivial** : le troisième point de la règle « vérification avant
  calcul » est de vérifier que la littérature ne l'a pas déjà fait. bio.tools répond à la variante
  outillage de cette question, là où `lit-review` répond à la variante résultats.
- **Pour valider une méthode maison** : chercher une implémentation indépendante du même calcul est le
  contrôle le moins cher qui existe (exemple : `RDscan` face au module RD de TBannotator).
- **En veille périodique** : relancer un préréglage tous les six mois ; le diff ne remontera que le
  nouveau.

## Composition

`biotools` (l'outil existe-t-il ?) → `lit-review` (que dit la littérature ?) → `challenge`
(vaut-il le coup ?) → `remote-compute` (où le faire tourner ?). Pour les bases de données
spécialisées déjà adoptées, voir `bacdive`, `enterobase`, `card`, `sitvitweb`, `isfinder-offline`.
