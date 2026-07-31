---
name: boltz
description: >
  Academic research toolkit (Guyeux group, FEMTO-ST), peer-reviewed structural
  bioinformatics : prédit EN LOCAL des complexes biomoléculaires (multimères,
  ions métalliques, ligands) avec Boltz-2, sans compte ni GPU (inférence CPU),
  là où AlphaFold Server n'est pas automatisable. Fournit la recette
  d'installation validée, l'écriture des entrées YAML, la réutilisation d'un MSA
  déjà produit, la lecture correcte des sorties (schéma Boltz ≠ schéma AF3) et
  les garde-fous d'interprétation. Utiliser quand : tester une interaction ou une
  homo-oligomérisation, savoir si un site métal est complété en trans, cribler un
  ligand/substrat candidat, ou refaire une prédiction de complexe sans solliciter
  l'utilisateur.
---

# boltz : prédiction locale de complexes (multimères, ions, ligands)

## Quand l'utiliser, et quand NE PAS

**Utiliser** pour tout **criblage** ou test d'hypothèse structurale en autonomie :
interaction binaire, homo-oligomérisation, complétion d'un site métal en trans,
ligand/substrat candidat, panel de partenaires.

**Ne PAS utiliser comme méthode de référence d'un manuscrit** si le projet a déjà
des prédictions AlphaFold3 : mélanger les deux produit une **comparaison
inter-modèles**. Discipline retenue dans l'écosystème : **Boltz = criblage,
AF3 Server = référence publiable**, et tout résultat Boltz rapporté est étiqueté
comme tel. (Boltz-2 est publié et citable ; l'assumer comme méthode principale est
un choix légitime, mais alors il faut homogénéiser tout le manuscrit.)

## Pourquoi ce skill existe

AlphaFold Server **n'est pas automatisable**, pour trois raisons cumulées :
(a) aucune API publique ; (b) SPA impilotable par l'extension navigateur (blocage
`document_idle`, cf. KB `claude-in-chrome-automation.md`) ; (c) **login Google +
acceptation de CGU**, actions que l'assistant ne doit pas faire à la place de
l'utilisateur. (c) est rédhibitoire : même (a) et (b) résolus, la voie reste
fermée. Boltz-2 lève le blocage pour tout ce qui relève du criblage.

## Coût disque réel : VÉRIFIER AVANT (~7-8 Go, pas 2)

| Élément | Taille |
|---|---|
| venv (torch CPU + deps) | ~1,5 Go |
| `~/.boltz/mols.tar` (CCD) | 1,86 Go |
| `~/.boltz/mols/` (extrait) | ~1,2 Go |
| `~/.boltz/boltz2_conf.ckpt` | 2,29 Go |
| **total** | **~7-8 Go** |

`df -h` **avant** de commencer. (Estimation initiale de ~2 Go : fausse, corrigée après
mesure.)

## Installation (recette validée, sans root)

Les dépendances de boltz sont épinglées (`numpy<2.0`, `scipy==1.13.1`,
`numba==0.61.0`) : **aucun wheel pour Python 3.14**. Provisionner un 3.11 avec `uv`.

```bash
uv python install 3.11
uv venv --python 3.11 ~/venvs/boltz
uv pip install --python ~/venvs/boltz/bin/python --index-url https://download.pytorch.org/whl/cpu torch
uv pip install --python ~/venvs/boltz/bin/python boltz
```

**PIÈGE CRITIQUE 1 (pip)** : installer torch **d'abord**, depuis l'index CPU
**exclusif**. Sinon pip tire ~3 Go de paquets `nvidia-*` inutiles sur une machine
sans GPU CUDA utilisable. Avec l'index CPU : venv ≈ 1,5 Go.

**PIÈGE CRITIQUE 2 (téléchargements) : PRÉ-TÉLÉCHARGER LES GROS FICHIERS EN `curl`.**
Vécu 2026-07-31 : laissé à lui-même, Boltz télécharge ses données depuis Python et
**cela cale en cours de route dans un sandbox**, connexion HTTPS ESTABLISHED, 0 % CPU,
aucune progression pendant 20 min, puis `tarfile.ReadError: unexpected end of data` au
run suivant parce que le `.tar` est **tronqué silencieusement** (1,22 Go reçus sur
1,86 Go). Le même `curl` passe à ~33 Mo/s. Donc, AVANT le premier `boltz predict` :

```bash
mkdir -p ~/.boltz && cd ~/.boltz
B=https://huggingface.co/boltz-community/boltz-2/resolve/main
for f in mols.tar boltz2_conf.ckpt; do
  curl -L --retry 3 -o "$f.part" "$B/$f"
  exp=$(curl -sIL "$B/$f" | awk 'tolower($1)=="content-length:"{print $2}' | tail -1 | tr -d '\r')
  got=$(stat -c %s "$f.part")
  [ "$got" = "$exp" ] && mv "$f.part" "$f" && echo "$f OK ($got)" || echo "$f INCOMPLET $got/$exp — NE PAS renommer"
done
```

**Toujours comparer la taille reçue à `content-length`** : un fichier tronqué ne
provoque aucune erreur au téléchargement, seulement un plantage obscur des heures plus
tard. (`model-gateway.boltz.bio/<f>` redirige en 307 vers ces mêmes URL HuggingFace.)

## Écrire l'entrée (YAML)

```yaml
version: 1
sequences:
  - protein:
      id: [A, B]              # deux chaînes identiques = homodimère
      sequence: VVTRQ...      # séquence complète
      msa: /chemin/vers.a3m   # voir ci-dessous
  - ligand:
      id: C
      ccd: FE                 # ion/ligand par code CCD (FE, ZN, MN, ATP...)
  - ligand:
      id: D
      smiles: "CC(=O)O"       # ou par SMILES pour une molécule quelconque
```

**MSA, préférer la réutilisation à l'appel externe.** Si le projet a déjà fait
tourner AlphaFold3, le MSA est sur disque :
`fold_<job>/msas/<job>_unpaired_msa_chains_a.a3m`. Le pointer dans `msa:` a deux
avantages : **aucun appel réseau**, et **même entrée évolutive qu'AF3**, donc une
comparaison plus juste. Vérifier que la première séquence du `.a3m` est bien la
requête attendue. À défaut, `--use_msa_server` interroge le serveur MMseqs2 de
ColabFold (service externe public, sans compte : la séquence y est envoyée, à
n'utiliser que pour des séquences déjà publiques).

## Lancer

```bash
~/venvs/boltz/bin/boltz predict entree.yaml \
    --out_dir <dir> --accelerator cpu --devices 1 \
    --output_format mmcif --diffusion_samples 1 --num_workers 4
```

**Coût réel** : sur CPU (16 cœurs), un dimère de ~310 résidus prend **plusieurs
heures**. Toujours lancer en tâche de fond avec un log, jamais en avant-plan.
`--diffusion_samples` augmente le nombre de poses (et le temps) ; garder 1 pour un
criblage, augmenter seulement si la question porte sur la variabilité des poses.

## Lire les sorties : ATTENTION, le schéma diffère d'AlphaFold3

Boltz écrit, par modèle classé :

| Fichier | Contenu |
|---|---|
| `<id>_model_<rank>.cif` | structure (mmCIF) |
| `confidence_<id>_model_<rank>.json` | `confidence_score`, `ptm`, `iptm`, `complex_plddt`, `chains_ptm`, `pair_chains_iptm`, `protein_iptm`, `ligand_iptm` |
| `pae_<id>_model_<rank>.npz` | matrice PAE brute (numpy) |

Conséquences pratiques, **vérifiées** :
- un parseur qui lit la **géométrie dans le mmCIF** (coordination d'un ion, contacts
  d'interface, pLDDT en B-factor) fonctionne **sans modification** sur du Boltz ;
- un parseur écrit pour AF3 qui lit `*summary_confidences*.json` et la clé
  **`chain_pair_pae_min` ne fonctionne PAS** : cette clé n'existe pas chez Boltz.
  L'ipTM est disponible (`iptm`, `pair_chains_iptm`), mais le **PAE minimum
  inter-chaînes doit être recalculé** depuis le `.npz` (charger la matrice, la
  découper selon l'affectation des chaînes lue dans le mmCIF, prendre le minimum
  hors-diagonale).

**Parseur bi-schéma prêt à l'emploi** :
`mtbc/Rv1025/analyses/phase3_afmultimer_parse.py <dir>` détecte automatiquement le
format par dossier de job (`*summary_confidences*.json` → AF3 ;
`confidence_*.json` → Boltz), recalcule le PAE inter-chaînes depuis le `.npz` pour
Boltz, et ajoute une colonne `source` au TSV pour que les deux ne soient jamais
confondus. Tokenisation utilisée pour découper la matrice PAE : **1 token par résidu
polymère, 1 token par atome de ligand** ; si la somme ne correspond pas à la dimension
de la matrice, il renvoie `NA (tokens N != PAE M)` **plutôt qu'un chiffre faux**.
Non-régression vérifiée : les jobs AF3 redonnent exactement les valeurs publiées.

## Garde-fous d'interprétation (ne pas les sauter)

1. **Contrôle positif du MÊME système**, obligatoire : une paire connue pour
   interagir dans le même contexte calibre le plafond. Un seuil générique
   « ipTM ≥ 0,6 » rejette à tort de vraies interfaces (petites protéines
   membranaires, MSA apparié peu profond).
2. **Le discriminant net est le PAE inter-chaînes minimum**, pas l'ipTM absolu.
3. **Reproductibilité entre modèles** : un ipTM qui s'effondre d'un modèle à
   l'autre = non-convergence = négatif.
4. **Contrôles de spécificité / modèle nul** : co-plier aussi 2-3 partenaires ou
   ligands NON attendus. C'est le **contraste** qui informe, jamais la valeur
   absolue. Un négatif propre est un résultat citable.
5. **Ions** : un modèle place volontiers un métal sur tout amas Cys/His/Glu
   plausible. Une prédiction holo ne prouve pas l'occupation physiologique →
   croiser avec la conservation et un contrôle négatif (mutant du site).
6. **Étiqueter la méthode** dans toute sortie destinée à un manuscrit, et ne
   jamais comparer un chiffre Boltz à un chiffre AF3 sans le dire.

## Voir aussi

- `active-site-check` (résidus catalytiques M-CSA), `esm-atlas-cli` (structures et
  scores de séquence), `raxml` / `iqtree-lsd2` (phylogénie).
- Exemple travaillé : `mtbc/Rv1025/analyses/phase21_boltz_homodimer.py` (génère les
  YAML + le runner, réutilise le MSA AF3) et `phase20_homodimer_parse.py` (lecture
  de la coordination inter-chaînes, applicable tel quel aux sorties Boltz).
