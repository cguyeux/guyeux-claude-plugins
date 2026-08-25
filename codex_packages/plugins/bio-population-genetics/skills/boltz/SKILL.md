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

> [!TIP]
> **Il existe désormais un vrai GPU accessible.** Le cluster `mh` (mesohelios) offre des
> **A100-PCIE-40GB** (3 par nœud, partition `gpu`, jusqu'à 12 jours) et des nœuds à 1 To de RAM,
> avec les modules `deep/pytorch-gpu/2.0.1`. Pour un complexe qui sature la mémoire en local, ou
> pour un lot de prédictions, passer par le skill **`remote-compute`** plutôt que d'étirer
> l'inférence CPU locale : la formule d'empreinte ci-dessous (≈ C + a·N²) reste la bonne façon de
> dimensionner le `--mem` du job `sbatch`. Prérequis : VPN monté. Ce skill reste la référence pour
> l'exécution locale, qui garde son intérêt (aucune file d'attente, aucun transfert).
>
> **Premier déploiement réussi sur `mh`, 2026-08-18 (`annotation_mtbc`, P16.2a-sexies-bis.5) — deux
> pièges GPU-spécifiques, absents en CPU local :**
> 1. **`/Home` (NFS) est en lecture seule sur les NŒUDS DE CALCUL**, alors qu'il est en
>    lecture-écriture sur la frontale où on télécharge/vérifie les poids. `boltz` extrait le CCD et
>    télécharge les poids d'affinité AU RUNTIME dans le cache : sans redirection, le job échoue en
>    quelques secondes (`OSError: Read-only file system`). Toujours passer `--cache
>    /Work/Users/<user>/boltz_cache` (ou `$BOLTZ_CACHE`), jamais le défaut `~/.boltz`. Détail :
>    `~/.Codex/knowledge/remote-compute.md`, entrée du 2026-08-18.
> 2. **Le noyau CUDA fusionné (`triangular_mult`) requiert `cuequivariance_torch`**, absent d'une
>    installation `pip install boltz` standard : `ModuleNotFoundError: No module named
>    'cuequivariance_torch'`, qui ne se déclenche QUE sur GPU (le chemin CPU ne passe pas par ce
>    noyau, d'où son absence du reste de ce skill). Contournement immédiat : `--no_kernels` (léger
>    coût de vitesse, résultat numérique inchangé). Non testé : installer `cuequivariance-torch`
>    pour retrouver l'accélération — à faire si `--no_kernels` s'avère trop lent sur un lot.
>
> Recette d'installation validée sur `mh` (`/Work/Users/<user>/envs/boltz`, Python 3.11 via
> micromamba) : `uv`/`pip install --index-url https://download.pytorch.org/whl/cu121 torch` (driver
> mesuré : CUDA 12.4, cu121 compatible), puis `pip install boltz` — mêmes versions épinglées que la
> recette CPU (`numpy` 1.26.4, `scipy` 1.13.1, `numba` 0.61.0), aucun conflit observé.
>
> **Deuxième déploiement confirmé, 2026-08-18 (`Rv3909`, P4.1/P4.3) : l'environnement
> `/Work/Users/<user>/envs/boltz` est réutilisable TEL QUEL par un autre projet**, aucune
> réinstallation nécessaire (comme `/data/cguyeux` sur `mp`, cf. `remote-compute.md`) — sonder
> `/Work/Users/<user>/envs/` avant de réinstaller. Ce même run a aussi validé un pattern à
> réutiliser : **générer les MSA sur la FRONTALE plutôt que `--use_msa_server` dans le job GPU**
> (l'égress réseau des nœuds de calcul n'est pas garanti, contrairement à `/Home` en lecture seule
> qui lui est documenté) — appeler `boltz.data.msa.mmseqs2.run_mmseqs2` (cf. plus bas, 1-10 s par
> séquence) sur la frontale pour chaque séquence distincte des YAML du lot, sauver en `.a3m`, et
> réécrire chaque YAML avec `msa: <chemin local>` avant `sbatch`. Le job array Slurm se heurte à
> `QOSMaxGRESPerUser` (1 GPU concurrent par utilisateur sur `gpu`) : les tâches au-delà de la
> première restent `PENDING` et s'enchaînent seules, ce n'est pas une erreur de soumission.
>
> **Trou de couverture corrigé dans le gabarit ci-dessous (2026-08-18, `Rv3909`) : le retry ne
> couvrait que les échecs de PRÉ-VOL** (mémoire, exclusivité), pas un job qui démarre puis échoue en
> cours de calcul (`SIGTERM`/crash) — il sortait silencieusement de la boucle sans être retenté.
> `MAX_JOB_RETRIES` (compteur par job, distinct de `MAX_CYCLES`) ajouté à la boucle principale :
> tout job dont le fichier de confiance n'existe pas après `run_job` est remis en file jusqu'à
> épuisement de son budget. Sur GPU `mh` (isolation Slurm par nœud) ce mode d'échec est moins
> probable qu'en local partagé, mais le correctif est générique et vaut pour les deux.

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

**Récupérer UN MSA profond seul, sans structure, en quelques secondes.** Besoin fréquent
au-delà de Boltz lui-même : conservation par résidu, clustering de site fonctionnel de-novo
(`annotation_mtbc` P17.2), toute analyse évolutive qui a besoin d'un alignement profond mais
pas d'une prédiction de structure. Le paquet `boltz` embarque directement la fonction qui fait
l'appel réseau ColabFold, réutilisable SANS lancer de prédiction (donc sans le coût CPU de la
diffusion, qui domine tout le reste) :
```python
from boltz.data.msa.mmseqs2 import run_mmseqs2
a3m = run_mmseqs2(sequence, prefix="mon_prefixe", use_env=True, use_pairing=False)[0]
```
Mesuré (2026-08-05, protéines 100-160 aa) : **1-10 secondes**, 700 à 4800 séquences alignées
selon la protéine — un ordre de grandeur ou deux moins profond qu'un run AF3 dédié (Rv1025 :
8700 séq, mais soumission manuelle au serveur AF3, non automatisable), largement suffisant pour
identifier des positions quasi invariantes (identité >=90%). `a3m` est le contenu a3m complet
(texte, pas un fichier) : à parser comme un `.a3m` classique (minuscules = insertions à retirer
pour obtenir l'alignement aux colonnes de la query). Élimine le besoin d'une soumission AF3
manuelle par gène pour tout usage qui ne nécessite QUE l'alignement, pas la structure.

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

> [!WARNING]
> **Un `ipTM` obtenu avec `--diffusion_samples 1` N'EST PAS INTERPRÉTABLE seul, même comparé à un
> témoin négatif du même lot** (vécu 2026-08-18, `Rv3909` P4.3). Un premier tirage a montré un
> écart apparent net entre un domaine testé (ipTM=0,594) et un témoin négatif (0,345) — lecture
> naturelle : signal spécifique. Un second run à `--diffusion_samples 5` sur les mêmes deux
> constructs a montré que la variance INTRA-construct (écart-type ≈0,18-0,21 sur 5 poses,
> étendue jusqu'à 0,20-0,74) est du même ordre que l'écart observé sur une seule pose — le témoin
> négatif atteignait 0,676 sur sa meilleure pose, au-dessus de la MOYENNE du construct testé. Le
> signal apparent était du bruit d'échantillonnage. **Avant de rapporter un ipTM isolé comme
> signal (positif ou négatif), soit être GPU (coût marginal, ~1 min/job sur A100) et lancer
> systématiquement `--diffusion_samples 5` sur le lot complet (cible + témoin) et comparer les
> distributions, pas les points uniques, soit annoncer explicitement le résultat comme
> préliminaire et non vérifié.**

**RÈGLE FERME, SANS EXCEPTION (arbitrage Christophe Guyeux, 2026-08-13) : un seul
`boltz predict` actif à la fois sur la machine, tous projets MTBC confondus.**
Deux jobs Boltz concurrents (~9 Gio chacun) ont fait planter Firefox/Chrome par
saturation mémoire — cette machine n'a **aucune swap active** (vérifier avec
`free -h` / `swapon --show` avant de supposer le contraire ; la zram a disparu en
cours de journée le 2026-08-13 sans explication trouvée), donc rien n'amortit un
dépassement. **Ne JAMAIS retirer la garde d'exclusivité** (`pgrep -f "${B}
predict"` dans `check_resources()` ci-dessous) pour débloquer un job qui attend
trop longtemps derrière un voisin — c'est exactement l'erreur commise le
2026-08-11 (`mtbc/Rv3909`, gabarit v3/v4) : la garde avait été retirée parce
qu'elle bloquait un lot de 4 jobs pendant des heures contre un unique voisin
persistant, ce qui a directement permis l'incident du 2026-08-13. **Attendre est
acceptable ; faire planter le poste de travail de l'utilisateur ne l'est pas.**
Si un job doit vraiment être priorisé devant un voisin qui tourne déjà, la
décision revient à l'utilisateur (tuer le voisin en connaissance de cause), pas
au script. Budget de cycles à augmenter (`MAX_CYCLES`) plutôt que la garde à
retirer si l'attente dépasse la fenêtre par défaut (12h30).

**Le runner généré doit être auto-défensif, pas seulement lancé en tâche de fond.**
Quatre incidents vécus (`mtbc/Rv2516c`, `mtbc/Rv3909`) montrent que « lancer en fond »
ne suffit pas :
(1) 2026-08-01, le venv Boltz avait disparu entre deux séances et **3 des 4 jobs d'un run
à 4 contrôles ont échoué en silence**, laissant un seul ipTM en apparence excellent
(0,890) sans aucun de ses contrôles — un résultat sans ses contrôles ressemble exactement
à un résultat ; (2) 2026-08-01, un runner relancé via `bash run.sh &` (attaché au shell
interactif de l'agent) est mort avec la fermeture de ce shell **4 minutes** après son
lancement, sans message d'erreur, en laissant des fichiers intermédiaires (MSA
téléchargé, structures pré-traitées) qui donnaient l'illusion d'un calcul en cours ;
(3) 2026-08-04 **et** 2026-08-05, le **même job** (P4.1/J2, contrôle positif toxine-
antitoxine) a été tué en silence PAR L'OS (signature : mort en plein milieu de l'étape
« Predicting », juste après une génération de MSA réussie, aucune trace d'erreur Python)
**deux fois de suite**, à chaque fois pendant qu'un ou plusieurs AUTRES processus
`boltz predict` d'un projet différent tournaient en parallèle sur la même machine
partagée, avec un swap déjà rempli à plus de 90 %. `free -h` seul, regardé une fois
avant de lancer, ne suffit pas : la contention peut apparaître APRÈS coup, pendant
qu'un runner à plusieurs jobs boucle, exactement ce qui a tué J2 alors que J1 (lancé
juste avant, sur la même machine) a fini par réussir des heures plus tard ;
(4) 2026-08-13 (`mtbc/Rv3909`, P4.3), un runner lancé via le mécanisme de tâche de fond
**suivi par l'agent** (`run_in_background: true`, celui qui rapporte un ID de tâche et
notifie à la fin) s'est arrêté (`status: killed`) après ~1h10, **alors qu'aucun
`boltz predict` n'avait encore démarré** : le script était inactif en `sleep 300`, en
boucle sur des échecs de pré-vol mémoire, donc ni OOM ni contention Boltz ne peuvent
l'expliquer. Un runner strictement identique relancé via `nohup ./run.sh >> log 2>&1
< /dev/null & disown` (appel Bash ordinaire, PAS `run_in_background: true`) a survécu
au-delà d'1h sans problème et a fini par lancer un vrai calcul. **Ceci contredit
directement** une règle plus ancienne et plus fortement établie (`~/.Codex/knowledge/bash-patterns.md`, incident du 2026-08-04, `mtbc/Rv3222c`) selon laquelle `nohup … &
disown` ne survivrait JAMAIS au retour de l'appel Bash et `run_in_background: true`
serait la SEULE voie fiable — l'inverse de ce qui vient d'être observé. Un troisième
facteur, non isolé, pourrait réconcilier les deux : l'incident de 2026-08-04 backgroundait
`boltz predict` avec un `&` INTERNE au script (job bash distinct, mort en `STOPPED`/
SIGTSTP) alors que le gabarit de ce skill appelle `boltz predict` de façon SYNCHRONE
(`run_job` bloque). **Statut non résolu** — cf. l'entrée `bash-patterns.md` du
2026-08-13 pour le détail complet. Ne traiter NI `run_in_background: true` NI
`nohup … & disown` comme une garantie de survie multi-heures : quel que soit le
mécanisme choisi, revenir vérifier avec `ps -p <pid> -o pid,etime,stat` (pas seulement
l'ID de tâche ou le PID affiché au lancement), et considérer un relancement avec
l'AUTRE mécanisme si l'un des deux se révèle mort sans raison Boltz identifiable.
Le gabarit de runner ci-dessous ferme les trois trous historiquement identifiés (venv
disparu, attachement au shell, contention/mémoire réévaluée à chaque job) : il refuse
de démarrer si le binaire est absent, il survit à la fermeture du shell qui l'a lancé
(`trap '' HUP`), l'ABSENCE de sa ligne finale dans le fichier de statut est elle-même
le diagnostic plutôt qu'un silence ambigu à interpréter à la main des heures plus tard,
et il **revérifie la disponibilité mémoire ET l'absence d'un autre `boltz predict`
concurrent avant CHAQUE job de la boucle**, pas seulement une fois au démarrage du
script. Le quatrième trou (incident (4)) N'EST PAS fermé par ce gabarit : aucun
mécanisme de lancement connu n'est encore prouvé fiable sur plusieurs heures dans cet
environnement (voir consigne de lancement ci-dessous).

(5) 2026-08-12 → 2026-08-17 (`mtbc/Rv0810c`, P6.1), un job lancé via `nohup ./run.sh
>> log 2>&1 < /dev/null & disown` a reçu **deux** `[rank: 0] Received SIGTERM: 15`
(loggés par PyTorch Lightning) quelques secondes après être entré dans l'étape
`Predicting`, puis n'a **plus jamais progressé ni terminé** : `ps` le montrait toujours
`R` (running), accumulant du temps CPU (~5j17h de temps CPU cumulé sur 39 threads pour
4,5 jours d'horloge murale), `boltz.log` figé au même octet pendant tout ce temps,
aucun fichier écrit dans `out_*/predictions/`. **Mode d'échec distinct des incidents
(1)-(4)** : ceux-ci sont des morts propres (process disparu, code retour non nul,
détectable par `kill -0` ou par l'absence du process) ; celui-ci est un **process
vivant qui a cessé de calculer** — indétectable par une garde qui ne vérifie que
l'existence du PID. Un `kill -TERM` de contrôle envoyé manuellement sur le PID bloqué
n'a eu strictement aucun effet (le gestionnaire de signal de PyTorch Lightning
consigne le SIGTERM mais ne fait apparemment pas céder la passe avant du modèle qui
tourne dans du code C/Fortran hors GIL) ; seul un `kill -KILL` a permis de le libérer.
Relancé ensuite via `run_in_background: true`, le même job a lui aussi reçu 3
`Received SIGTERM: 15` supplémentaires en moins d'une minute (donc l'origine du signal
n'est PAS spécifique à `nohup … & disown`, contrairement à l'hypothèse initiale) —
cohérent avec le caractère « non résolu » de l'incident (4) plutôt qu'un facteur isolé.
**Correctif appliqué à ce gabarit (partiel, ferme la CONSÉQUENCE, pas la CAUSE)** : le
`run_job` ci-dessous ne bloque plus indéfiniment sur le process Boltz — il le
background lui-même et surveille la taille de `boltz.log` ; l'absence de croissance
pendant `STALL_TIMEOUT` (défaut 30 min) déclenche un `SIGKILL` et fait échouer le job
proprement (repris au cycle suivant), au lieu de laisser un process zombie consommer du
CPU en silence pendant des jours. Ceci ne résout PAS la cause des `SIGTERM` reçus (encore
inconnue au 2026-08-17) : voir `~/.Codex/knowledge/bash-patterns.md` pour le suivi.

**Incident (6), 2026-08-17, quelques heures après (5) (`mtbc/Rv0810c`, P6.1, job déporté sur
`mp`)** : le watchdog de l'incident (5), jamais encore éprouvé en conditions réelles, a failli
tuer un job **parfaitement sain**. À 29 min 41 s d'immobilité de `boltz.log` — à 19 s du seuil
`STALL_TIMEOUT=1800` d'alors — le process affichait 2777 % CPU et +3202 s de temps CPU cumulé en
seulement 100 s d'horloge réelle (mesuré par delta entre deux `ps` espacés, la seule méthode fiable
en présence d'une horloge distante suspecte) : un calcul manifestement actif. `grep -c "Received
SIGTERM" boltz.log` valait 0 sur tout le fichier, contrairement à l'incident (5) où le signal était
systématiquement consigné avant l'arrêt de progression. **Cause du silence identifiée** : l'étape
`Predicting DataLoader 0` porte sur un DataLoader à **un seul item** (l'unique batch couvrant tous
les échantillons de diffusion demandés) ; `tqdm` n'écrit une ligne qu'au changement de la valeur du
compteur, donc rien entre `0/1` et `1/1` — un silence de plusieurs dizaines de minutes, voire
plusieurs heures sur CPU pour une protéine de quelques centaines de tokens, y est attendu par
construction et ne signale rien d'anormal. Le watchdog de l'incident (5) confondait ainsi deux
signatures distinctes sous un seul critère (immobilité du log) : un **process vivant qui a cessé de
calculer** (incident (5), toujours précédé d'un `SIGTERM` consigné) et un **process vivant qui
calcule une étape non instrumentée** (incident (6), jamais précédé d'un `SIGTERM`). Neutralisé
manuellement in extremis (`kill -TERM` sur le seul wrapper de surveillance, PID distinct du process
`boltz predict` laissé intact) faute de mieux le temps de corriger ce gabarit.

**Correctif appliqué (révision du gabarit ci-dessous, 2026-08-17)** : `run_job` distingue désormais
les deux signatures au lieu d'un seuil unique. Un `SIGTERM` consigné dans `boltz.log` est un signal
**fort et spécifique** du mode d'échec de l'incident (5) : une fois vu, une immobilité de seulement
`SIGTERM_GRACE` (5 min) déclenche le `SIGKILL` — plus rapide qu'avant (30 min). En l'ABSENCE de tout
`SIGTERM` logué, l'immobilité seule n'est plus une preuve de blocage (incident (6)) : le seuil
`STALL_TIMEOUT` sert alors de simple filet de sécurité, porté à 3h (10800 s), largement au-dessus de
toute étape `Predicting` CPU non instrumentée observée à ce jour. Ce filet reste un seuil fixe faute
de modèle de durée attendue par nombre de tokens / `diffusion_samples` — à resserrer seulement si
calibré sur des mesures réelles, jamais en devinant.

**Incident (7), 2026-08-19/20 (`mtbc/Rv1025`, P4.3/P8.1.a.4) : les deux bugs déjà corrigés ci-dessus
(incidents 5-6 et le trou de couverture du retry, 2026-08-17/18) ont RÉCIDIVÉ à l'identique**, non
parce que le diagnostic était faux mais parce que le runner généré pour ce projet (`run_all.sh`,
2026-08-19) utilisait un gabarit `STALL_TIMEOUT=1800` sans distinction SIGTERM/immobilité pure, ET
sans `MAX_JOB_RETRIES` — une copie ANTÉRIEURE aux deux correctifs, alors que ceux-ci existaient déjà
dans ce skill depuis 1 à 2 jours au moment de la génération. Conséquence mesurée : sur un panel de 7
jobs, le runner d'origine a tué 5 jobs SAINS (immobilité seule, aucun `SIGTERM` logué — signature
identique à l'incident (6) ; `rv1025_ftsZ_Rv2150c` tournait encore à 148 % CPU après 42 min quand il
a été tué pour une autre raison, mémoire locale, avant même le SIGKILL du watchdog) et n'a fait
passer que 2/7 jobs. Un correctif ad hoc (`MAX_ATTEMPTS=2` sans distinction SIGTERM, `STALL_TIMEOUT`
inchangé à 1800s) a d'abord été écrit sur place avant de relire ce skill — il a fallu une SECONDE
itération, avec un seuil remonté à 4h, pour que les 5 jobs restants passent enfin (confirmés sains :
tous couraient encore entre 15 et 53 min sans aucun `SIGTERM` logué). **Leçon distincte des
correctifs eux-mêmes : un gabarit corrigé dans ce skill ne corrige RIEN pour un projet dont le
runner a déjà été généré avant le correctif — il n'y a pas de mécanisme de propagation automatique.**
Avant de lancer une nouvelle campagne multi-jobs sur un projet existant, RELIRE ce skill et
RÉGÉNÉRER le runner depuis le gabarit ci-dessous plutôt que de réutiliser/adapter une copie locale
qui peut dater d'avant un correctif — un `diff` rapide entre le gabarit ici et le `run_*.sh` du
projet est le réflexe bon marché qui aurait évité les deux tiers de cet incident.

```bash
#!/usr/bin/env bash
set -u
trap '' HUP              # survit a la fermeture du shell qui l'a lance (SIGHUP ignore)
cd "$(dirname "$0")"
B=$HOME/venvs/boltz/bin/boltz
STATUS=boltz_status.log

if [ ! -x "$B" ]; then   # echouer BRUYAMMENT plutot que job par job
  echo "ERREUR : binaire Boltz introuvable ou non executable : $B" | tee -a "$STATUS" >&2
  echo "  Le venv a-t-il disparu ? Voir ce skill, section Installation." >&2
  exit 1
fi

# Pre-vol ressources, reevalue avant CHAQUE job (pas seulement au demarrage du script) :
# un autre boltz predict deja actif ou une memoire insuffisante sont la cause CONFIRMEE
# d'echecs silencieux vecus deux fois sur le meme job (mtbc/Rv2516c, P4.1/J2, 2026-08-04 et
# 2026-08-05). Echec du pre-vol = job SAUTE, pas lance dans l'espoir que ca passe.
#
# REVISION 2026-08-09, deux corrections apres usage reel. NE PAS revenir en arriere :
#
# (1) LE CRITERE "SWAP LIBRE" EST RETIRE. Il produisait un faux positif PERMANENT sur une
#     machine a zram (swap = RAM compressee) et gros tmpfs : /proc/swaps y affiche le swap
#     plein a 100 % en continu alors que zramctl montre quelques centaines de Mio reellement
#     stockes. Resultat vecu : le pre-vol refusait 100 % des jobs, y compris ceux qui
#     tenaient largement en memoire, et le refus etait indiscernable d'une vraie contention.
#     Un garde-fou dont le critere est un PROXY sature pour une raison sans rapport bloque
#     tout. Se fier a la colonne `available` de free, qui est correcte.
#
# (2) LE SEUIL ABSOLU EST REMPLACE PAR UN MODELE CONSCIENT DE LA TAILLE DU JOB. Un seuil fixe
#     (4000 Mio) ne peut pas expliquer pourquoi, dans un meme lot, c'est toujours le plus gros
#     job qui meurt. La memoire de Boltz suit ~ C + a*N^2 (N = tokens, proteine + acides
#     nucleiques, TOUTES chaines confondues), le terme constant venant des poids du modele.
#     Calibrer C et a sur DEUX mesures de VOTRE machine (mesurer en PSS, pas en RSS, qui
#     double-compte les pages partagees entre le parent et ses workers) :
#        for p in $(pgrep -f "boltz predict"); do
#          awk '/^Pss:/{s+=$2} END{printf "%d MB\n", s/1024}' /proc/$p/smaps_rollup; done
#     Valeurs de depart mesurees sur la machine FEMTO (62 Gio, CPU) : C=5367, a=0.02639
#     (164 tokens -> 5,3 Go ; 350 -> 8,6 Go ; 568 -> 13,9 Go). Marge x1,2 : le modele estime
#     deja un pic. Details et chaine causale complete : ~/.Codex/knowledge/bioinformatics.md
#     et linux-desktop.md.
#
# Definir TOKENS par job avant l'appel (somme des longueurs de toutes les chaines du YAML).
MEM_C=5367       # Mio, terme constant (poids du modele) -- recalibrer par machine
MEM_A=0.02639    # Mio par token^2                       -- recalibrer par machine

check_resources() {  # usage : check_resources <nb_tokens_du_job>
  local tokens="$1" other avail_mib need_mib
  # NB : matcher "boltz predict" nu peut s'AUTO-DETECTER si la chaine figure dans la ligne de
  # commande du shell appelant (vecu : refus fantome). Ancrer sur le binaire reel -- MAIS PAS
  # en debut de ligne (`^`) : boltz est un entry-point Python, le process reel s'execute comme
  # ".../python .../boltz predict ...", l'interpreteur precede toujours le chemin de boltz dans
  # argv. Un ancrage "^${B} predict" ne matche donc JAMAIS AUCUN job Boltz, le sien compris --
  # bug vecu le 2026-08-11 (mtbc/Rv0810c, P6.1) : deux jobs Boltz ont tourne simultanement sur
  # la meme machine malgre ce garde-fou cense l'empecher, silencieusement, jusqu'a inspection
  # de `ps aux`. Garder le chemin complet (specifique, evite le faux positif sur la commande du
  # shell appelant) mais SANS `^`.
  other=$(pgrep -f "${B} predict" 2>/dev/null || true)
  if [ -n "$other" ]; then
    echo "  PRE-VOL ECHEC : un autre processus Boltz tourne deja (PID $other)." >&2
    return 1
  fi
  avail_mib=$(free -m | awk '/^Mem:/{print $7}')
  need_mib=$(awk -v n="$tokens" -v c="$MEM_C" -v a="$MEM_A" 'BEGIN{printf "%d", c + a*n*n}')
  if [ "${avail_mib:-0}" -lt $((need_mib * 6 / 5)) ]; then
    echo "  PRE-VOL ECHEC : RAM disponible ${avail_mib:-?} Mio < 1,2x besoin estime ${need_mib} Mio" >&2
    echo "    ($tokens tokens). Si /tmp est un tmpfs, il immobilise de la RAM : df -h /tmp" >&2
    return 1
  fi
  echo "  pre-vol OK : ${avail_mib} Mio dispo, besoin estime ${need_mib} Mio ($tokens tokens)"
  return 0
}

# REVISION 2026-08-11 (mtbc/Rv3909, P4.1/P4.3) : boucle de CYCLES, pas un passage unique par job.
# Un premier passage "check une fois, SAUTE definitivement si echec" (version anterieure de ce
# gabarit) a laisse tourner un lot de 4 jobs pendant 2h40 sans qu'AUCUN ne soit tente : les 32
# controles (deja avec une sous-boucle de retry par job, 8 essais x 5 min) ont tous echoue sur le
# MEME motif -- un unique job Boltz voisin, actif en continu sur toute la fenetre (diffusion_samples
# eleve, donc long), bloquait le garde-fou anti-contention. Le defaut n'etait pas la memoire (elle
# etait devenue largement suffisante en cours de fenetre) mais la structure : chaque job epuisait
# son propre budget de retry contre une condition bloquante PARTAGEE avant de ceder la place au
# suivant, et un job une fois SAUTE n'etait plus jamais retente meme si les conditions changeaient
# ensuite. Correctif : une boucle EXTERIEURE de cycles qui, a chaque reveil, retente TOUS les jobs
# pas encore faits dans l'ordre, enchaine autant de jobs que la voie le permet (chaque appel etant
# bloquant, le suivant est revérifié avec des conditions a jour, pas perimees), et REPREND sur
# interruption (saute un job dont la sortie existe deja). Budget total large (defaut : 150 cycles x
# 5 min = 12h30) car la duree de la condition bloquante -- un job voisin -- n'est pas sous controle
# de ce script.
MAX_CYCLES=150
CYCLE_SLEEP=300   # 5 min
# Deux seuils distincts depuis l'incident (6), 2026-08-17 -- un seuil UNIQUE fondu sur la seule
# immobilite du log a failli tuer un job sain (voir le recit ci-dessus) :
STALL_TIMEOUT=10800   # 3h -- filet de securite pur, EN L'ABSENCE de tout SIGTERM logue. Une etape
                      # "Predicting" CPU sur un DataLoader a un seul item peut rester silencieuse
                      # tres longtemps sans que ce soit un blocage (incident (6)). A resserrer
                      # seulement si calibre sur une mesure reelle de duree attendue.
SIGTERM_GRACE=300     # 5 min -- des qu'un SIGTERM est vu dans boltz.log, l'immobilite qui suit est
                      # un signal FORT et specifique du mode d'echec de l'incident (5) : ne pas
                      # attendre le filet de 3h dans ce cas, la conclusion est deja acquise.

run_job() {
  local y="$1"
  echo "=== $y $(date +%H:%M:%S) ===" | tee -a "$STATUS"
  # --num_workers 0 : sur CPU avec un seul echantillon de diffusion, les workers de chargement
  # n'apportent RIEN (le goulot est le passage avant du modele, il y a un seul exemple a lire)
  # et coutent tres cher. Mesure PSS du 2026-08-09 : sur un job a 164 tokens, le principal pese
  # 4495 Mio et les DEUX workers 3868 Mio de plus, soit 46 % du total gaspilles. Ne pas remonter
  # cette valeur sans avoir mesure un benefice reel.
  #
  # Backgrounde et surveille lui-meme le process (incident (5), 2026-08-17, mtbc/Rv0810c/P6.1) :
  # un job Boltz peut recevoir un SIGTERM externe (origine encore inconnue), le consigner via le
  # handler PyTorch Lightning, et rester "R" (running) sans plus jamais progresser ni se terminer
  # -- un SIGTERM manuel de controle sur ce meme PID s'est revele sans effet, seul un SIGKILL l'a
  # libere. Un `run_job` purement synchrone (ancienne version) ne peut PAS detecter cet etat : le
  # process reste vivant, `&&`/`||` n'evalue rien tant qu'il n'a pas quitte de lui-meme -- vecu :
  # 4,5 jours de CPU consomme pour zero progres, decouvert seulement par inspection manuelle.
  #
  # MAIS l'immobilite seule de boltz.log n'est PAS une preuve de blocage (incident (6), meme jour) :
  # une etape "Predicting" sur un DataLoader a un seul item peut legitimement ne rien ecrire pendant
  # tres longtemps. Le signal fiable est la PRESENCE d'un SIGTERM logue par PyTorch Lightning, qui a
  # systematiquement precede le vrai blocage (5) et n'est jamais apparu dans le faux positif (6).
  "$B" predict "$y.yaml" --out_dir "out_$y" --accelerator cpu --devices 1 \
      --output_format mmcif --diffusion_samples 1 --num_workers 0 --use_msa_server \
      >> boltz.log 2>&1 &
  local bpid=$! last_size=-1 last_change sigterm_seen=0
  last_change=$(date +%s)
  while kill -0 "$bpid" 2>/dev/null; do
    sleep 30
    local cur_size now sigterm_count
    cur_size=$(stat -c%s boltz.log 2>/dev/null || echo -1)
    now=$(date +%s)
    if [ "$cur_size" != "$last_size" ]; then
      last_size=$cur_size
      last_change=$now
    fi
    sigterm_count=$(grep -c "Received SIGTERM" boltz.log 2>/dev/null || echo 0)
    if [ "$sigterm_count" -gt 0 ] && [ "$sigterm_seen" -eq 0 ]; then
      sigterm_seen=1
      echo "  $y SIGTERM detecte dans boltz.log -- surveillance resserree a ${SIGTERM_GRACE}s (incident (5))" | tee -a "$STATUS"
    fi
    if [ "$sigterm_seen" -eq 1 ] && [ $((now - last_change)) -ge "$SIGTERM_GRACE" ]; then
      echo "  $y BLOQUE : SIGTERM logue puis boltz.log immobile ${SIGTERM_GRACE}s, process $bpid toujours vivant -> SIGKILL" | tee -a "$STATUS"
      kill -KILL "$bpid" 2>/dev/null
      wait "$bpid" 2>/dev/null
      echo "  $y ECHEC (stall apres SIGTERM)" | tee -a "$STATUS"
      return 1
    elif [ "$sigterm_seen" -eq 0 ] && [ $((now - last_change)) -ge "$STALL_TIMEOUT" ]; then
      echo "  $y BLOQUE : boltz.log immobile depuis ${STALL_TIMEOUT}s SANS SIGTERM logue (filet de securite), process $bpid toujours vivant -> SIGKILL" | tee -a "$STATUS"
      kill -KILL "$bpid" 2>/dev/null
      wait "$bpid" 2>/dev/null
      echo "  $y ECHEC (stall)" | tee -a "$STATUS"
      return 1
    fi
  done
  wait "$bpid" && echo "  $y OK" | tee -a "$STATUS" || echo "  $y ECHEC" | tee -a "$STATUS"
}

# Un job = "<nom>:<nb_tokens>". Le nombre de tokens est la SOMME des longueurs de toutes les
# chaines du YAML (proteines + brins d'ADN/ARN), y compris les copies d'un homodimere.
jobs="job1:164 job2:350 job3:568"
remaining="$jobs"
MAX_JOB_RETRIES=3   # tentatives APRES un demarrage reussi (echec en cours de calcul : SIGTERM,
                    # crash, stall) -- distinct de MAX_CYCLES qui ne couvre que les echecs de PRE-VOL
                    # (memoire, exclusivite). Trou de couverture vecu le 2026-08-13 puis a nouveau
                    # le 2026-08-18 (Rv3909, P4.3) : un job qui demarre puis echoue sortait
                    # silencieusement de la boucle sans jamais etre retente.
declare -A attempts
for cycle in $(seq 1 $MAX_CYCLES); do
  [ -z "$remaining" ] && break
  next_remaining=""
  for spec in $remaining; do
    y="${spec%%:*}"; tokens="${spec##*:}"
    if [ -s "out_$y/confidence_${y}_model_0.json" ] 2>/dev/null; then
      continue   # deja fait (reprise apres interruption ou cycle precedent)
    fi
    if check_resources "$tokens"; then
      run_job "$y"
      if [ -s "out_$y/confidence_${y}_model_0.json" ] 2>/dev/null; then
        continue   # succes reel (verifie sur disque, pas sur le code de sortie du sous-shell)
      fi
      attempts[$y]=$(( ${attempts[$y]:-0} + 1 ))
      if [ "${attempts[$y]}" -lt "$MAX_JOB_RETRIES" ]; then
        echo "  $y : echec EN COURS DE CALCUL (tentative ${attempts[$y]}/$MAX_JOB_RETRIES), remis en file" | tee -a "$STATUS"
        next_remaining="$next_remaining $spec"
      else
        echo "  $y : ABANDONNE apres $MAX_JOB_RETRIES echecs en cours de calcul" | tee -a "$STATUS"
      fi
    else
      next_remaining="$next_remaining $spec"
    fi
  done
  remaining="$next_remaining"
  if [ -n "$remaining" ]; then
    echo "  cycle $cycle/$MAX_CYCLES : $(echo $remaining | wc -w) job(s) restant(s), attente ${CYCLE_SLEEP}s ($(date +%H:%M:%S))" | tee -a "$STATUS"
    sleep "$CYCLE_SLEEP"
  fi
done
if [ -n "$remaining" ]; then
  echo "  TIMEOUT : $(echo $remaining | wc -w) job(s) jamais lances apres $MAX_CYCLES cycles : $remaining" | tee -a "$STATUS"
fi
echo "=== TERMINE $(date +%H:%M:%S) ===" | tee -a "$STATUS"
```

**Le choix entre `nohup ./run.sh >> log 2>&1 < /dev/null & disown` et
`run_in_background: true` (paramètre natif du Bash tool) n'est PAS tranché** — les deux
mécanismes ont chacun été observés tuant un runner sans raison Boltz identifiable dans
des incidents différents (`bash-patterns.md`, 2026-08-04 pour `nohup`/`disown` ;
incident (4) ci-dessus, 2026-08-13, pour `run_in_background: true`). Commencer par
`run_in_background: true` (recommandation historique la plus ancienne, notification
automatique à la fin) ; si le statut de tâche rapporte une mort (`killed`/`stopped`)
sans corrélat Boltz (pas de `SIGTERM` dans `boltz.log`, pas de contention/mémoire
identifiable), relancer via `nohup ... & disown` explicite plutôt que de réessayer le
même mécanisme à l'identique. Le `trap '' HUP` du gabarit reste une deuxième ligne de
défense (utile en cas de fermeture du shell), pas une garantie de survie à elle seule,
quel que soit le mécanisme de lancement choisi. Avant de conclure qu'un run est
« toujours en cours », vérifier `ps -p <pid> -o pid,etime,stat` et le contenu du fichier
de statut — jamais la seule présence de fichiers intermédiaires dans le répertoire de
sortie, ni la seule confiance dans l'ID de tâche retourné par l'agent ou le PID affiché
par `nohup`. Un job qui reste dans la liste "restant(s)" cycle après cycle signifie que
le pré-vol a refusé de le lancer à chaque tentative : ce n'est ni un succès ni un échec
de calcul, c'est une protection qui a fonctionné. Un `TIMEOUT` en fin de fichier de
statut signale que la condition bloquante (mémoire ou contention) a duré plus longtemps
que `MAX_CYCLES x CYCLE_SLEEP` — augmenter ce budget plutôt que de relancer le script à
l'identique, qui repartirait du même point grâce à la reprise sur sortie existante mais
perdrait le temps déjà écoulé.

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
   membranaires, MSA apparié peu profond). **Le « même contexte » inclut le
   COFACTEUR requis, pas seulement les bonnes chaînes protéiques** : un
   régulateur connu pour dimériser sur son ADN (structure de référence = un
   co-cristal protéine-ADN) peut donner un signal apo faible ou nul si sa
   dimérisation est en réalité INDUITE ou stabilisée par la liaison à l'ADN
   (`mtbc/Rv2516c`, 2026-08-03 : BldC seul en homodimère apo, ipTM 0,564,
   PAE 4,48 Å, 16 contacts d'interface ; le MÊME BldC avec son duplex d'ADN
   opérateur, ipTM 0,827, PAE 0,64 Å, 113 contacts — écart massif sur la même
   protéine, même pipeline, seule la présence de l'ADN change). Un positif
   apparemment raté par le contrôle positif peut donc signaler un choix de
   CONTEXTE MOLÉCULAIRE incomplet pour ce contrôle, pas une défaillance du
   pipeline — vérifier la littérature sur le mode d'oligomérisation exact
   (constitutif vs induit par le ligand/l'ADN) avant de blâmer l'outil.
2. **Le discriminant net est le PAE inter-chaînes minimum**, pas l'ipTM absolu.
3. **Reproductibilité entre modèles** : un ipTM qui s'effondre d'un modèle à
   l'autre = non-convergence = négatif.
4. **Contrôles de spécificité / modèle nul** : co-plier aussi 2-3 partenaires ou
   ligands NON attendus. C'est le **contraste** qui informe, jamais la valeur
   absolue. Un négatif propre est un résultat citable. **Sur un test d'auto-
   association (homodimère apo) de petites protéines (~100-200 résidus) en CPU
   à un seul échantillon de diffusion**, ce contrôle de spécificité est
   INDISPENSABLE et pas suffisant en soi : un domaine sans aucune fonction ni
   propension connue peut obtenir un score PLUS élevé que le test lui-même
   (`mtbc/Rv2516c`, même date : un domaine ferredoxin-like sans fonction de
   liaison à l'ADN connue obtient ipTM 0,873, PAE 0,64 Å, 55 contacts — mieux
   que le test ET que le contrôle positif). Dans ce régime, Boltz semble
   replier volontiers n'importe quel domaine globulaire compact en un
   homodimère symétrique plausible et confiant, indépendamment d'une réelle
   propension biologique — un biais générique d'empilement, pas un signal.
   Un score de test « décent » n'est donc interprétable QUE s'il dépasse
   nettement ce contrôle, jamais en valeur absolue même modérée.
   **Deuxième cas confirmant, sens INVERSE** (`mtbc/Rv0810c`, 2026-08-10/11, P3.4) : hypothèse
   d'homo-oligomère tête-bêche sur une protéine de 60 aa à architecture BIPARTITE non compacte
   (module ordonné 1-33 + queue acide étendue, rayon de giration 22,8 Å) contre un contrôle de
   spécificité RpmG2 (50S ribosomal L33, 55 aa, ne s'auto-associe pas biologiquement hors du
   ribosome). Résultat, 5 échantillons de diffusion chacun : test ipTM 0,091-0,138 / PAE
   inter-chaînes 15,9-17,0 Å (aucune interface confiante, les 5 modèles) ; contrôle ipTM
   0,385-0,714 / PAE 3,4-8,8 Å (interface confiante) — **cette fois le contrôle NON pertinent
   bat largement le test réel**, sens opposé au cas Rv2516c où le contrôle avait battu à la
   fois le test ET le positif. Les deux cas ensemble montrent que le biais générique
   d'empilement de Boltz sur les petits domaines COMPACTS n'opère pas uniformément : une
   protéine non compacte (IDR étendue) peut au contraire échouer à produire QUOI QUE CE SOIT
   de confiant, y compris l'artefact lui-même. Conséquence méthodologique : ne jamais lire un
   score bas comme un négatif interprétable sans le contrôle — il peut aussi bien signifier
   « pas d'interaction » que « architecture incompatible avec l'empilement par défaut du
   modèle », et seul le contraste avec un contrôle de MÊME régime (petite protéine, CPU, même
   nombre d'échantillons) permet de trancher entre les deux.
5. **Ions** : un modèle place volontiers un métal sur tout amas Cys/His/Glu
   plausible. Une prédiction holo ne prouve pas l'occupation physiologique →
   croiser avec la conservation et un contrôle négatif (mutant du site).
6. **Étiqueter la méthode** dans toute sortie destinée à un manuscrit, et ne
   jamais comparer un chiffre Boltz à un chiffre AF3 sans le dire.
7. **Le biais d'empilement générique (point 4) s'étend aux complexes PROTÉINE-ADN, pas
   seulement à l'auto-association apo** — et un triangle de contrôles à quatre branches,
   même complet, peut ne PAS suffire à le détecter s'il n'inclut pas le positif RÉEL.
   `mtbc/Rv2516c`, P4.3bis-e, 2026-08-11 : quatre jobs sur le même pipeline (CPU, un seul
   échantillon de diffusion, protéine-protéine-ADN ~100-200 résidus + duplex de 22 pb) —
   E1 test (unité wHTH candidate ×2 + ADN hétérologue, l'opérateur de BldC) ipTM 0,930 ;
   E2 négatif de SÉQUENCE (même système, ADN brouillé par permutation préservant les
   dinucléotides) ipTM 0,928, PAE inter-chaînes MEILLEUR que E1 (0,46 vs 0,48 Å) ; E3
   négatif de DOMAINE (domaine sans fonction ADN connue ×2 + le même ADN) ipTM 0,854 ; E4
   **positif RÉEL** (BldC ×2 + son propre opérateur, reconstitution directe d'un co-cristal
   résolu, 6AMA) ipTM 0,905, **PAE inter-chaînes LE PIRE des quatre** (0,65 Å) malgré le
   plus grand nombre de contacts d'interface (212). Le complexe cognat, structurellement
   validé, score MOINS BIEN sur ipTM/pTM que le test hétérologue ET que le négatif de
   séquence, et pire que tous sur le PAE. **Verdict : sur cette classe de systèmes, ipTM/
   pTM/PAE ne discriminent PAS un complexe protéine-ADN cognat d'un test hétérologue ou
   d'un contrôle de séquence brouillée — un ipTM élevé sur un complexe wHTH-ADN n'est PAS
   interprétable comme preuve de reconnaissance de séquence, quel que soit le nombre de
   contrôles apparentés (même domaine, même ADN) s'ils ne comprennent pas un positif RÉEL
   au même format moléculaire.** Le seul indicateur qui ordonne les quatre jobs de façon
   biologiquement sensée est le compte BRUT de contacts d'interface (positif > test ≈
   négatif de séquence > négatif de domaine), mais l'écart entre le test et son négatif de
   séquence y reste trop ténu (6 contacts sur ~200) pour servir seul de test de spécificité.
   **Conséquence pratique : pour une question de spécificité de SÉQUENCE spécifiquement,
   ne pas utiliser Boltz/AF du tout dans ce régime** — passer par une méthode NON
   générative et structurellement insensible à ce biais (complémentarité électrostatique
   calibrée APBS/PDB2PQR, consensus dérivé de contacts base-résidu lus directement sur des
   structures homologues résolues). Boltz/AF reste informatif pour la géométrie de contact
   protéine-ADN générale (point 1) et pour des questions d'auto-association ou
   d'appariement de chaînes, pas pour trancher si UNE séquence précise est reconnue.

## Voir aussi

- `active-site-check` (résidus catalytiques M-CSA), `esm-atlas-cli` (structures et
  scores de séquence), `raxml` / `iqtree-lsd2` (phylogénie).
- Exemple travaillé : `mtbc/Rv1025/analyses/phase21_boltz_homodimer.py` (génère les
  YAML + le runner, réutilise le MSA AF3) et `phase20_homodimer_parse.py` (lecture
  de la coordination inter-chaînes, applicable tel quel aux sorties Boltz).

## Codex knowledge path note

This packaged copy resolves personal knowledge-base references under `~/.Codex/knowledge/`. CCX-04 still tracks the broader Claude/Codex knowledge-base reconciliation, so verify that the referenced note exists before relying on it.
