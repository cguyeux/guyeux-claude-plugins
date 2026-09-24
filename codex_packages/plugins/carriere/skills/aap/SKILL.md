---

name: aap
description: >
  Gère tout le cycle d'un appel à projets (ANR, ANRS MIE, ERC, Horizon Europe, IUF,
  Interreg, PHC, AUF, ARS, Région, Smart MI, OPCO, EDIH), de la veille à la
  décision du financeur : repérer les appels ouverts, instruire un appel et
  rendre un verdict go/no-go avant toute rédaction, amorcer un dossier
  pré-rempli (SIRET, RNSR, signataires, coûts), relire un brouillon contre la
  grille de critères, et enregistrer la décision du financeur pour en tirer
  l'enseignement réutilisable. Tient le registre CENTRAL des candidatures, seul
  endroit où se voient la limite d'implication de l'ANR, les clauses de
  non-cumul et les mandats interdisant un dépôt.

  Utiliser quand l'utilisateur reçoit ou mentionne un appel à projets, demande
  s'il faut candidater, cherche un financement, prépare ou dépose un dossier,
  veut savoir où en sont ses candidatures, ou reçoit une réponse du financeur.
  Trigger : « appel à projets », « faut-il candidater », « monter un dossier
  ANR », « on a été refusé », « on est lauréat ».
---

# Appels à projets — instruire, décider, déposer, capitaliser

Ce skill est au financement ce que `/soumission` est aux articles. Il ne rédige pas les
sections : cela reste le travail de `/grant-proposal`, qu'il appelle une fois la décision
de déposer prise. Il porte ce qui l'entoure et qui se perdait jusqu'ici : quel appel
existe, faut-il y aller, qui a le droit de porter, quelles informations le formulaire va
redemander pour la douzième fois, et ce que la décision du financeur apprend.

## Les données

Tout vit dans `~/.agents/knowledge/funding/`, central et jamais par dossier.

| Fichier | Contenu |
|---|---|
| `calls.tsv` | un dispositif par ligne, dont `who_can_apply` et `blockers` |
| `calls/<key>.md` | fiche détaillée quand le règlement a été lu |
| `applications.tsv` | registre central des candidatures, tous financeurs confondus |
| `admin_profile.json` | les informations administratives récurrentes |
| `rejections.md` | ce qu'une décision, ou un verrou découvert trop tard, apprend |
| `SCHEMA.md` | schéma des deux TSV et règle anti-hallucination |

```bash
SK=~/docs/environnement/plugins/carriere/skills/aap/scripts
python3 $SK/veille.py search --terms "..." --status open           # sujet + échéance
python3 $SK/veille.py due --days 60                                 # clôtures proches, tous portails ouverts
python3 $SK/calls.py list --instructed          # dispositifs réellement instruits
python3 $SK/calls.py show anrs-mie-generique    # fiche complète, blockers en évidence
python3 $SK/calls.py due --days 120             # clôtures qui approchent
python3 $SK/calls.py stale --days 365           # fiches à revérifier avant usage
python3 $SK/applications.py open                # candidatures actives, et ce qui dort
python3 $SK/applications.py eligibility anr-aapg --year 2027
python3 $SK/admin_profile.py get siret          # valeur prête à coller
python3 $SK/admin_profile.py missing            # ce qui reste à obtenir, et où
```

## Geste 0 — repérer un appel

Avant même qu'un mail de financeur n'arrive : `veille.py search` interroge un portail
agrégateur (`appelsprojetsrecherche.fr` pour l'instant, voir `references/sources.md`
pour le contrat et pour ajouter une autre source) et affiche, par résultat, le sujet
et la date limite — jamais plus, ce n'est pas une instruction.

```bash
python3 $SK/veille.py search --terms "sécurité civile" --status open,upcoming
python3 $SK/veille.py due --days 90 --terms "intelligence artificielle"
```

Un résultat qui mérite d'aller plus loin passe au geste 1, avec l'URL trouvée ici
comme point de départ pour lire le règlement complet — la veille ne dit jamais si un
appel est pertinent ou éligible, elle dit seulement qu'il existe et jusqu'à quand.
Un `status=upcoming` n'a le plus souvent aucune date publiée (pré-annonce) : c'est
normal, pas un défaut d'extraction.

## Geste 1 — un appel arrive

Déclenché par la veille du geste 0, un mail du financeur, un relais du directeur
d'unité, ou un lien.

1. Lire le règlement en entier. Pas le flyer, le règlement. Les verrous d'éligibilité
   n'apparaissent jamais dans le résumé.
2. `calls.py show <key>` si le dispositif est connu, `calls.py add` sinon, puis remplir
   `who_can_apply` et `blockers` **avant tout le reste** : ce sont les deux colonnes qui
   tuent un dossier quand on les lit trop tard.
3. `applications.py eligibility <call> --year <n>` : le registre confronte les blockers du
   règlement à ce qui est déjà engagé cette année.
4. Rendre le verdict go/no-go selon `references/go_no_go.md`. Un verdict, argumenté, jamais
   un menu laissé à l'auteur. L'enregistrer avec `applications.py add` puis `set`.

Ne jamais écrire une ligne du dossier avant d'avoir franchi cette porte.

## Geste 2 — amorcer le dossier

1. Créer le dossier sous `~/docs/projects/<financeur>/<appel>/`, comme les dossiers
   existants, avec un `AGENTS.md` or `AGENTS.md or CLAUDE.md fallback` fallback qui porte le cadrage de l'appel et un `JOURNAL.md`
   horodaté. Un dossier de candidature n'est pas un projet de recherche : les cinq
   artefacts de `/init-project` ne s'y appliquent pas, sauf s'il produit de la science, et
   dans ce cas le résultat se rapatrie tout de suite dans le projet scientifique concerné
   plutôt que d'attendre le sort de la candidature.
2. Pré-remplir les champs administratifs avec `admin_profile.py show`. Ce qui vaut
   `unknown` se va chercher, il ne s'invente pas.
3. Passer la main à `/grant-proposal` pour la structure et la rédaction section par
   section, à `/cv` pour les données de carrière, à `/researcher` pour la matière
   scientifique, à `/profil-chercheur` pour instruire un partenaire pressenti.

## Geste 3 — relire avant dépôt

Suivre `references/review_grid.md` : notation critère par critère selon le règlement,
contrôle de matérialité, conformité formelle, simulation des objections. Le rapport daté
va dans `review/` à la racine du dossier.

Passer aussi `/claim-check` et `/bib-check` si le dossier avance des chiffres et des
références, et `/deai-latex` sur toute source LaTeX.

## Geste 4 — la décision tombe

`applications.py decide <key> accepte|refuse|abandonne --amount <montant>`, puis écrire
dans `rejections.md` le **verbatim** des motifs, pas leur paraphrase adoucie. Un motif non
écrit le jour même ne sera jamais retrouvé, et le même reproche reviendra chez le financeur
suivant. Une acceptation s'y consigne aussi : elle dit sur quel argument le dossier a porté.

## Trois règles qui font la valeur de ces fichiers

**Un `unknown` n'est pas une donnée, c'est une vérification à faire.** Aucune date, aucun
plafond, aucun SIRET ne s'écrit de mémoire. `source` dit d'où vient la valeur, `verified_on`
dit quand. Une fiche de plus d'un an se revérifie avant de servir à décider d'un dépôt : les
dates glissent d'un millésime à l'autre, et c'est exactement le champ qu'on croit connaître.

**Le registre est central, jamais par dossier.** La limite d'implication de l'ANR se calcule
sur l'ensemble de l'année, un mandat de présidence de comité ferme un millésime entier, et
une clause de non-cumul se lit contre les autres candidatures en cours. Aucune de ces trois
contraintes n'est visible depuis un dossier isolé.

**L'éligibilité se lit avant l'opportunité.** Un dossier inéligible ne se rattrape par
aucune qualité de rédaction, et il ne rapporte même pas un retour d'instruction utile.

## Interaction avec les autres skills

`/grant-proposal` rédige les sections une fois la décision prise. `/cv` fournit les données
de carrière et les publications significatives. `/researcher` et `/lit-review` fournissent
la matière scientifique. `/profil-chercheur` instruit un partenaire. `/soumission` est le
pendant de ce skill pour les articles, et partage sa logique de registre central.

## Codex workflow guardrail

This packaged copy imports a Claude-origin project workflow into Codex. Before writing project registers, moving BDD files, changing Atlas content, appending remote queues, archiving a project, or launching remote compute, require an explicit user request in the current turn. Use recoverable operations only, keep project provenance boundaries, and follow the global rule that files are moved to the trash rather than permanently deleted.
