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
> réécrire chaque YAML avec `msa: <chemin local>` avant `sbatch`. **(2026-09-07, change le
> dimensionnement des campagnes Boltz)** le job array ne se heurte plus forcément à
> `QOSMaxGRESPerUser` : la QOS `3gpu` est désormais attachée au compte `cguyeux`, et
> `#SBATCH --qos=3gpu` avec `--array=1-N%3` fait tourner **trois prédictions de front** au lieu
> d'une (vérifié le 2026-09-08 : trois jobs `RUNNING` simultanés). Sans cette ligne `--qos`, rien
> ne change, la QOS par défaut restant `normal` : les tâches au-delà de la première restent
> `PENDING` et s'enchaînent seules, ce qui n'est pas une erreur de soumission mais un oubli de
> trois mots. Une campagne de 196 jobs passe ainsi d'environ trois semaines à une bonne semaine.
> Détail des plafonds et de la restitution des QOS prêtées : skill `remote-compute`.
>
> **(2026-09-04) Deux vérifications sur `mh`, toutes deux faites en direct.** (1) Le driver NVIDIA
> est passé en **550** (`550.163.01`) et le mésocentre prévient qu'un environnement conda antérieur
> peut cesser d'utiliser le GPU **sans lever d'erreur**, le code retombant en CPU où Boltz est
> ~700× plus lent. **L'environnement `/Work/Users/<user>/envs/boltz` n'est PAS touché** : testé, il
> rend `2.5.1+cu121 / CUDA 12.1 / True`. Garder malgré tout une **assertion** en tête de job,
> `python3 -c "import torch; assert torch.cuda.is_available()"`, plutôt qu'un simple affichage : la
> panne est silencieuse et le prochain changement de driver ne préviendra pas.
> (2) **Cet environnement tourne tel quel sur une L40**, vérifié sur `node4-28`. Mais la partition
> `gpu_l40` est **PRIVÉE, financée par un tiers** (Kamel Mazouzi, 2026-09-04) : elle est visible
> dans `sinfo` et presque toujours `idle` quand `gpu` sature, ce qui la rend très tentante, mais
> **ne pas s'y router de sa propre initiative**. Une demande d'autorisation est en cours ; d'ici là
> rester sur `gpu` et ses A100. Voir `remote-compute`.
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

**Incident (8), 2026-08-30/31 (`mtbc/Rv1125`, P1.5.c, 3 jobs CPU locaux 16 coeurs, protéines
~390-430 tokens, gabarit du 2026-08-30 déjà à jour des correctifs (5)-(7)) : le filet de sécurité
`STALL_TIMEOUT=10800` (3h) s'est révélé lui-même trop court, signature identique à (6)/(7).** Les
3 jobs (`positive_control_abwsd1`, `test_rv1125_wt`, `mutant_rv1125_h138a`) ont chacun été tués et
relancés 1 à 2 fois (6 redémarrages cumulés dans `boltz.log`, aucun `SIGTERM` jamais consigné),
chaque tentative repartant de zéro sans jamais dépasser `Predicting DataLoader 0: 0%` avant d'être
retuée à l'échéance des 3h — soit environ 17h de calcul CPU perdues en boucle sans qu'aucun des 3
jobs n'aboutisse. Vérifié à la main (`ps -o pid,etime,pcpu`, delta CPU-temps) sur la tentative en
cours au moment du diagnostic : 227 % CPU, 1h48 de temps CPU cumulé, aucun signe d'OOM (`dmesg`
vide), aucun `SIGTERM` logué — signature (6)/(7) sans ambiguïté, pas un vrai blocage. Neutralisé en
tuant uniquement le wrapper `run.sh` (`kill -TERM` sur son PID, PAS sur le PID `boltz predict`,
devenu orphelin sain) pour laisser la tentative en cours terminer sans nouvelle relance forcée.
**Leçon distincte des incidents (6)/(7) : un seuil fixe, même déjà relevé deux fois sur retour
d'incident réel (1800s puis 10800s), reste une estimation bornée par les jobs déjà observés, pas
une garantie pour un job de taille jamais mesurée — remonter encore le chiffre à la prochaine
récidive serait deviner une troisième fois.** Le signal fiable documenté depuis (6) (delta de temps
CPU cumulé entre deux `ps` espacés, déjà utilisé ici en diagnostic manuel) n'est PAS encore intégré
dans la boucle `run_job` elle-même, qui ne regarde toujours que la taille du fichier `boltz.log` ;
tant que ce n'est pas fait, `STALL_TIMEOUT` restera un pari sur la taille des protéines à venir.
**Correctif proposé, non appliqué à ce gabarit (décision humaine requise avant intégration dans un
skill partagé par plusieurs projets)** : remplacer le critère « `boltz.log` immobile depuis
`STALL_TIMEOUT` » par une vérification de l'activité CPU réelle du PID (`/proc/$bpid/stat` ou deux
`ps -o times` espacés) — ne déclencher le `SIGKILL` que si le process est à la fois immobile en log
ET n'accumule plus de temps CPU sur une fenêtre courte (quelques minutes), ce qui distinguerait un
vrai blocage d'une étape `Predicting` longue quelle que soit sa durée, sans borne arbitraire à
deviner. Tant que ce correctif n'est pas écrit et testé, tout projet lançant des jobs CPU sur des
protéines de taille comparable ou supérieure à Rv1125 doit s'attendre à devoir neutraliser le
wrapper à la main (`kill -TERM` sur son PID, jamais sur le PID `boltz predict`) plutôt que de
compter sur `STALL_TIMEOUT` pour ne jamais se déclencher à tort.

**Incident (9), 2026-08-31 (`mtbc/Rv2566`, P8.2, 1 job CPU local, fragment tronqué 533 tokens,
gabarit déjà à jour des correctifs (5)-(8)) : récidive à l'identique de (8), même seuil
`STALL_TIMEOUT=10800` déjà signalé trop court pour cette classe de taille.** Tentative 1 tuée à
15:01+3h00 (`boltz.log` immobile depuis 10800s, aucun `SIGTERM` logué), remise en file
automatiquement, tentative 2 relancée à 18:09:42. Vérifiée saine en cours de tentative 2
(`ps -o etime,pcpu,time` à deux instants espacés de 20s : TIME cumulé 00:57:51 -> 00:58:11, soit
20s de CPU consommées pour 20s d'horloge, ~92 % CPU constant, 0 `SIGTERM` logué) — signature (6)/(7)/
(8) sans ambiguïté, pas un vrai blocage, à ~1h30 d'un 2e `SIGKILL` prématuré identique si rien
n'est fait. Neutralisé de la même façon que (8) : `kill -TERM` sur le seul PID du wrapper
(`bash ./run.sh`, retrouvé par filiation `ps -eo pid,ppid,cmd` -- PAS le `bash -c` parent qui a
lancé `nohup`, qui reste vivant sans rapport avec la boucle de surveillance), PID `boltz predict`
laissé orphelin sain (reparenté à PID 1, calcul non interrompu). **Quatrième récidive documentée du
même seuil fixe en deux semaines (8/17, 8/19-20, 8/30-31, 8/31) sur quatre projets différents** :
le correctif proposé en (8) (activité CPU réelle du PID plutôt qu'immobilité du seul `boltz.log`)
n'est toujours pas intégré au gabarit partagé -- chaque nouveau projet lançant un job CPU de taille
comparable ou supérieure à ~400 tokens doit s'attendre à devoir répéter ce diagnostic manuel.

**Correctif intégré, 2026-09-01 (`mtbc/Rv1125`, P1.5.c-ter) : `get_cpu_ticks()` (lecture de
`/proc/$pid/stat`, champs utime+stime) et `CPU_STALL_CONFIRM` remplacent le critère d'immobilité du
seul `boltz.log` comme signal de blocage réel — un job n'est déclaré bloqué (hors SIGTERM) que s'il
est immobile en log ET n'accumule plus de temps CPU depuis `CPU_STALL_CONFIRM` (300 s). `STALL_TIMEOUT`
redevient un pur filet de secours, utilisé seulement si `/proc` est illisible (repli explicite,
`cpu_check_ok=0`). Testé avant intégration sur un cas synthétique (script `test_cpu_watchdog.sh`,
non conservé dans le dépôt car ponctuel) : un process en boucle CPU pure sans sortie log (simule une
étape `Predicting` longue et silencieuse mais réelle) survit indéfiniment au correctif, un process
endormi (`sleep`, ~0 % CPU, simule un vrai blocage) est tué dès la première fenêtre de confirmation
écoulée — les deux scénarios qui avaient respectivement produit un faux positif (8)/(9) et un vrai
blocage (5) sont donc discriminés correctement. **Non encore rééprouvé sur un job Boltz réel
multi-heures** (le test synthétique valide la logique du watchdog, pas le comportement de Boltz
lui-même sous ce nouveau critère) : à surveiller sur le premier lot qui rencontre une étape
`Predicting` effectivement longue, et à documenter ici (succès ou nouvel échec) plutôt que supposé
acquis. Détail et smoke-test : cahier de labo `mtbc/Rv1125`, 2026-09-01.

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
STALL_TIMEOUT=10800   # 3h -- FILET DE SECOURS UNIQUEMENT, utilise seulement si /proc est illisible
                      # (cf. correctif incident (8)/(9) ci-dessous, get_cpu_ticks). Dans le cas
                      # normal (Linux, /proc disponible), le critere reel de blocage n'est plus ce
                      # seuil mais CPU_STALL_CONFIRM.
SIGTERM_GRACE=300     # 5 min -- des qu'un SIGTERM est vu dans boltz.log, l'immobilite qui suit est
                      # un signal FORT et specifique du mode d'echec de l'incident (5) : ne pas
                      # attendre le filet de 3h dans ce cas, la conclusion est deja acquise.
# CORRECTIF INCIDENT (8)/(9), 2026-09-01 (mtbc/Rv1125, P1.5.c-ter) : le seuil fixe STALL_TIMEOUT,
# meme relevé deux fois sur incident reel (1800s puis 10800s), a quand meme tue a tort 4 jobs
# SAINS sur 4 projets differents (Rv0810c, Rv2516c/Rv3909, Rv1125, Rv2566) simplement parce
# qu'une etape "Predicting" CPU peut rester silencieuse en log plus longtemps que N'IMPORTE
# QUEL seuil arbitraire choisi a l'avance -- ce n'est pas une question de mieux calibrer le
# chiffre, c'est le CRITERE lui-meme (immobilite du LOG) qui est le mauvais proxy. Remplace par
# le signal propose dans le recit de l'incident (8) : l'activite CPU REELLE du PID, lue dans
# /proc/$pid/stat (champs utime+stime, cf. man 5 proc). Un job ne peut etre declare bloque que
# s'il est A LA FOIS immobile en log ET n'accumule plus de temps CPU sur une fenetre courte --
# une etape silencieuse mais qui calcule reste protegee indefiniment, sans plus jamais deviner
# une duree a l'avance.
CPU_STALL_CONFIRM=300 # 5 min -- fenetre de confirmation CROISEE (log ET cpu flats tous les deux
                      # depuis au moins ce delai) avant SIGKILL, EN L'ABSENCE de tout SIGTERM
                      # logue. Remplace STALL_TIMEOUT comme critere reel quand /proc est lisible ;
                      # peut rester court (la garantie de securite vient de la conjonction des deux
                      # signaux, pas de la duree du seuil) -- teste sur un cas synthetique (busy-loop
                      # CPU jamais tue vs process endormi tue en ~1 fenetre) avant integration ici,
                      # cf. cahier de labo mtbc/Rv1125 2026-09-01. Pas encore reeprouve sur un job
                      # Boltz reel multi-heures (cf. note de prudence en fin de section) : a
                      # surveiller sur le premier lot qui rencontre une etape "Predicting" longue.

# Lit utime+stime (temps CPU cumule, en ticks d'horloge) d'un PID depuis /proc. Retourne une
# chaine vide (et code 1) si /proc est illisible (conteneur restreint, PID deja mort, plateforme
# non-Linux) -- l'appelant doit alors se replier sur STALL_TIMEOUT seul, jamais planter dessus.
# Le nom de commande (comm) est entre parentheses et peut lui-meme contenir des parentheses ou
# des espaces (man 5 proc) : on coupe sur la DERNIERE occurrence de ") " pour retomber sur les
# champs numeriques a coup sur, jamais sur un split naif par espace depuis le debut de la ligne.
get_cpu_ticks() {
  local pid="$1" stat after utime stime
  stat=$(cat "/proc/$pid/stat" 2>/dev/null) || return 1
  after="${stat##*) }"
  set -- $after
  utime="${12:-}"; stime="${13:-}"
  [ -z "$utime" ] && return 1
  [ -z "$stime" ] && return 1
  echo $((utime + stime))
}

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
  # MAIS l'immobilite seule de boltz.log n'est PAS une preuve de blocage (incident (6), meme jour ;
  # confirme a plus grande echelle par (8)/(9)) : une etape "Predicting" sur un DataLoader a un
  # seul item peut legitimement ne rien ecrire pendant tres longtemps tout en calculant. Le signal
  # de blocage retenu depuis (8)/(9) est double : soit un SIGTERM logue par PyTorch Lightning
  # (incident (5), toujours suivi d'une vraie mort), soit l'absence conjointe de toute ecriture
  # log ET de toute progression CPU sur la fenetre CPU_STALL_CONFIRM (get_cpu_ticks ci-dessus).
  "$B" predict "$y.yaml" --out_dir "out_$y" --accelerator cpu --devices 1 \
      --output_format mmcif --diffusion_samples 1 --num_workers 0 --use_msa_server \
      >> boltz.log 2>&1 &
  local bpid=$! last_size=-1 last_change sigterm_seen=0
  local last_cpu_ticks=-1 last_cpu_change cpu_check_ok=1
  last_change=$(date +%s)
  last_cpu_change=$last_change
  while kill -0 "$bpid" 2>/dev/null; do
    sleep 30
    local cur_size now sigterm_count cur_cpu_ticks
    cur_size=$(stat -c%s boltz.log 2>/dev/null || echo -1)
    now=$(date +%s)
    if [ "$cur_size" != "$last_size" ]; then
      last_size=$cur_size
      last_change=$now
    fi
    if cur_cpu_ticks=$(get_cpu_ticks "$bpid"); then
      cpu_check_ok=1
      if [ "$cur_cpu_ticks" != "$last_cpu_ticks" ]; then
        last_cpu_ticks=$cur_cpu_ticks
        last_cpu_change=$now
      fi
    else
      # /proc illisible : on ne sait plus juger l'activite CPU -- repli explicite sur
      # STALL_TIMEOUT seul (comportement pre-(8), jamais pire que l'ancien gabarit).
      cpu_check_ok=0
    fi
    sigterm_count=$(grep -c "Received SIGTERM" boltz.log 2>/dev/null)
    sigterm_count=${sigterm_count:-0}
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
    elif [ "$sigterm_seen" -eq 0 ] && [ "$cpu_check_ok" -eq 1 ] \
         && [ $((now - last_change)) -ge "$CPU_STALL_CONFIRM" ] \
         && [ $((now - last_cpu_change)) -ge "$CPU_STALL_CONFIRM" ]; then
      echo "  $y BLOQUE : boltz.log ET temps CPU cumule tous deux immobiles depuis ${CPU_STALL_CONFIRM}s (incident (8)/(9)), process $bpid toujours vivant -> SIGKILL" | tee -a "$STATUS"
      kill -KILL "$bpid" 2>/dev/null
      wait "$bpid" 2>/dev/null
      echo "  $y ECHEC (stall confirme log+cpu)" | tee -a "$STATUS"
      return 1
    elif [ "$sigterm_seen" -eq 0 ] && [ "$cpu_check_ok" -eq 0 ] \
         && [ $((now - last_change)) -ge "$STALL_TIMEOUT" ]; then
      echo "  $y BLOQUE : boltz.log immobile depuis ${STALL_TIMEOUT}s SANS SIGTERM logue, /proc illisible donc repli filet de securite pur, process $bpid toujours vivant -> SIGKILL" | tee -a "$STATUS"
      kill -KILL "$bpid" 2>/dev/null
      wait "$bpid" 2>/dev/null
      echo "  $y ECHEC (stall, repli sans lecture CPU)" | tee -a "$STATUS"
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
    # CORRECTIF 2026-09-13 (mtbc/Rv2628, P3.3) : le chemin verifie etait "out_$y/confidence_...",
    # qui ne pointe JAMAIS vers rien -- boltz ecrit sous out_$y/boltz_results_$y/predictions/$y/.
    # Ce bug faisait declarer ECHEC un job qui avait REELLEMENT reussi (confidence_score present sur
    # disque), avec deux consequences vecues : (a) en single-job, le runner rapporte "ECHEC (sortie
    # absente)" alors que le calcul a produit un resultat exploitable ; (b) dans CETTE boucle multi-
    # job, un job reussi ne serait jamais reconnu "deja fait", serait remis en file indefiniment et
    # fini par etre declare ABANDONNE apres MAX_JOB_RETRIES malgre un succes reel. Non re-eprouve sur
    # une campagne multi-job reelle depuis le correctif (seul le cas single-job, mtbc/Rv2628, l'a
    # revele) : a confirmer sur le premier lot qui l'exerce.
    if [ -s "out_$y/boltz_results_$y/predictions/$y/confidence_${y}_model_0.json" ] 2>/dev/null; then
      continue   # deja fait (reprise apres interruption ou cycle precedent)
    fi
    if check_resources "$tokens"; then
      run_job "$y"
      if [ -s "out_$y/boltz_results_$y/predictions/$y/confidence_${y}_model_0.json" ] 2>/dev/null; then
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

**Lecture normalisée d'un lot Boltz : `scripts/boltz_readout.py <dirs...>`** (2026-09-03).
Là où le parseur bi-schéma ci-dessus rend les scores, celui-ci rend en plus, et
systématiquement, les quatre mesures que le garde-fou nº0 exige et qu'un coup d'œil
au JSON de confiance ne donne pas : profondeur du MSA **apparié** par paire (comptée
correctement, voir l'encadré du garde-fou nº0), dispersion des scores entre
échantillons de diffusion, ptm **propre** et PAE **intra**-chaîne de chaque
partenaire, et position du meilleur contact inter-chaînes. Il lève tout seul deux
alertes bloquantes sur stderr : profondeurs appariées dans un rapport supérieur à 3,
et moins de trois échantillons de diffusion. Il accepte la disposition locale comme
celle des jobs Slurm (`out_<job>/boltz_results_<job>/…`), n'a besoin que de numpy, et
sort en TSV ou en Markdown (`--markdown`). Non-régression vérifiée sur les six
prédictions de `mtbc/Rv0007` P3.1 : valeurs identiques au tableau publié.

## Garde-fous d'interprétation (ne pas les sauter)

0. **CLASSER DEUX PARTENAIRES EXIGE D'APPARIER LEURS MSA APPARIÉS.** C'est le
   confondant le plus coûteux du skill, découvert le 2026-09-02 sur `mtbc/Rv0007`
   après qu'un manuscrit entier eut été rédigé sur le classement obtenu. Le
   `pair.a3m` porte l'information inter-chaînes ; sa profondeur varie
   d'un ordre de grandeur d'un partenaire à l'autre pour la MÊME protéine requête,
   et **le partenaire dont le MSA apparié est le plus PAUVRE peut obtenir le meilleur
   score d'interface**. Mesuré : CofA-FL × PonA1-TM, **714 lignes
   appariées** ; CofA-FL × PonA2-TM, **12 lignes appariées** ; facteur **59,5**, et
   c'est PonA2, avec douze lignes appariées en tout, qui « gagne ».

   > **Deux resserrements de formulation (2026-09-03, après contrôle bibliographique).**
   > (a) Ne pas écrire « privé de contrainte de coévolution » : Luo et al., bioRxiv
   > 2026, 10.64898/2026.04.14.718427, montrent par appariement MÉLANGÉ que les gains
   > de l'appariement viennent de la PROFONDEUR brute et non des contraintes
   > d'appariement. Ce que compte `pair.a3m` est de la profondeur.
   > (b) Ne pas affirmer le SENS de l'effet : au niveau population, Burke et al.,
   > *Nat Struct Mol Biol* 2023, 10.1038/s41594-022-00910-8, observent l'inverse,
   > « the pDockQ values tend to increase with less disorder and more sequences in the
   > alignments ». Le point robuste et suffisant est que **la profondeur appariée est
   > une covariable non contrôlée du score, à mesurer et à déclarer avant tout
   > classement** — au même titre que la taille (Todor 2026) et le désordre (Dunbrack
   > 2025). Un cas isolé où le plus pauvre gagne ne devient un effet qu'après avoir
   > écarté la taille ET la variabilité de graine, et à n ≥ 5.
   **Avant de conclure qu'un partenaire l'emporte, mesurer la profondeur appariée
   de chaque paire et la déclarer.** Si les profondeurs diffèrent d'un facteur
   supérieur à ~3, le classement n'est pas interprétable tel quel :
   sous-échantillonner le MSA le plus profond à la profondeur du plus pauvre et
   rejouer.

   > **Comment la mesurer, car `grep -c '^>'` donne un faux compte** (corrigé le
   > 2026-09-03 ; la première rédaction de ce garde-fou annonçait 1 429 contre 52,
   > facteur 27, deux chiffres faux et un rapport deux fois trop petit). `pair.a3m`
   > n'est pas un FASTA ordinaire : il concatène **un bloc par chaîne, séparés par
   > un octet NUL**, si bien que le total des en-têtes mélange les deux chaînes et
   > leurs deux requêtes ; et cet octet NUL fait basculer `grep` en mode binaire, où
   > son comptage diffère encore (1 430 en binaire, 1 429 avec `-a`, pour 1 430
   > en-têtes réels). La profondeur **appariée** d'une paire vaut `en-têtes du bloc
   > − 1`, identique pour les deux blocs par construction de l'appariement, et c'est
   > elle seule qui mesure l'information inter-chaînes disponible pour l'interface.
   > `scripts/boltz_readout.py` la calcule et lève l'alerte automatiquement ; ne pas
   > recompter à la main.

   Trois corollaires du même cas, tous vérifiés sur les fichiers bruts :
   - **le PAE inter-chaînes MINIMUM est une statistique d'extrême** (une cellule
     parmi 12 000 à 29 000) : à `--diffusion_samples 1`, il est sans variance et ne
     départage rien. Publier le PAE **moyen** à côté ; dans ce cas, PonA2 à 23,48
     contre témoin négatif à 24,20 sur une échelle saturant vers 30, soit
     indiscernables, alors que le minimum semblait trancher ;
   - **un partenaire que le modèle ne replie pas avec confiance ne peut pas être
     déclaré « mauvais interacteur »** : vérifier le ptm PROPRE et le PAE
     INTRA-chaîne du partenaire avant tout (ici PonA1-TM à ptm 0,671 / PAE 12,26
     contre PonA2-TM à 0,840 / 6,68 — le « pire que le bruit » était l'artefact) ;
   - **vérifier où tombe l'interface prédite** : si les meilleurs contacts tombent
     dans les mêmes hélices TM pour le vrai candidat ET pour le témoin négatif,
     l'interface n'a aucune spécificité, quel que soit le score.
   Enfin, **ne jamais écarter le bras d'un plan factoriel qui contredit** en gardant
   celui qui confirme, au même n = 1 : sur Rv0007 le classement s'inversait entre
   construction pleine longueur et tronquée, et seule la construction favorable a
   été retenue comme « méthodologiquement valide ».

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

   > **RÉGIME OÙ LE CONTRÔLE POSITIF ÉCHOUE POUR DE BON : les paires
   > hélice transmembranaire × petite protéine membranaire** (mesuré le 2026-09-03,
   > `mtbc/Rv0007` P5.2 — premier étalonnage de CE dépôt sur vérité expérimentale
   > externe ; la littérature publiée, elle, connaît déjà le constat général, voir la
   > note bibliographique en fin d'encadré). Cinq paires CofA × aPBP-TM tirées de Sher et al. 2020
   > (*eLife*, essai POLAR), dans DEUX organismes, dont deux paires **démontrées
   > interagissantes** et trois **démontrées non interagissantes**, à
   > `--diffusion_samples 5` : **ipTM de 0,801 à 0,815 pour les cinq**, PAE
   > inter-chaînes minimum de 2,0 à 2,7 Å pour les cinq. Zéro pouvoir discriminant,
   > avec une puissance suffisante (écart minimal détectable 0,112 en ipTM, contre
   > 0,155 pour l'effet qu'on cherchait à confirmer). Trois conséquences pratiques :
   > - **l'échec ne se voit pas au score, qui reste haut.** Un non-partenaire
   >   démontré obtient ici l'apparence d'une interface confiante. Ne jamais lire
   >   « ipTM 0,8 sur une paire TM-TM » comme une interaction ;
   > - **la dispersion écrase l'effet cherché** : sur un bras positif, le PAE min
   >   couvre 0,53 à 7,41 Å sur cinq tirages du même échantillon, un intervalle plus
   >   large que l'écart de 4,67 Å qu'un criblage à n = 1 avait tenu pour décisif ;
   > - **le MSA de ces paires est vide des DEUX façons** (0 ligne appariée pour les
   >   cinq, et surtout 1 à 12 séquences AU TOTAL côté partenaire). Le
   >   garde-fou nº0 et celui-ci se répondent — à profondeur inégale le classement
   >   suit la profondeur, à profondeur nulle il n'y a plus de classement du tout.
   >
   > **CORRECTION DU 2026-09-03 (soir), IMPORTANTE, issue d'une passe adversariale
   > indépendante puis vérifiée directement.** La première rédaction de cet encadré
   > expliquait le MSA vide par la longueur du fragment (« MMseqs2 n'apparie presque
   > rien sur des fragments de 40 à 50 résidus ») : **c'est faux**, et l'erreur avait
   > été propagée jusqu'à la base de connaissances. Mesure qui la réfute : les 20
   > décoys du garde-fou nº2 bis sont des fenêtres de **41 aa** et leurs MSA comptent
   > de **62 à 7168 séquences** (médiane ~640). Ce n'est donc pas la longueur qui vide
   > le MSA, c'est **l'ORGANISME** : les fenêtres du témoin venaient de
   > *Corynebacterium glutamicum* et *C. jeikeium*, très peu représentés dans les
   > bases, contre *M. tuberculosis* pour les décoys.
   >
   > **Les deux facteurs ont ensuite été DÉCROISÉS par mesure directe** (le même jour,
   > après objection d'une instance indépendante : tant qu'on compare 41 aa à 44 aa, les
   > deux explications restent confondues). Plan factoriel, MSA seuls, ~1 min de serveur
   > MMseqs2, aucune prédiction structurale — `mtbc/Rv0007/analyses/phase14_p5_2bis_
   > organisme_vs_longueur.py` :
   >
   > | | 41 aa | 44 aa |
   > |---|---|---|
   > | *M. tuberculosis* | **47, 315, 4159** | — |
   > | *C. glutamicum* | **3** | 6 |
   > | *C. jeikeium* | **2** | 2 |
   >
   > À longueur strictement égale, l'écart entre organismes va d'un facteur 15 à un
   > facteur 1400 ; tronquer la MÊME fenêtre du MÊME organisme de 44 à 41 aa ne change
   > pratiquement rien. **Le facteur est l'organisme, pas la longueur du fragment.** Le
   > fait sous-jacent est publié (Bryant, Pozzati & Elofsson, *Nat Commun* 2022,
   > 10.1038/s41467-022-28865-w : l'exactitude suit l'information évolutive disponible,
   > y compris entre organismes d'un même règne) ; ce qui ne l'est pas, c'est la règle de
   > sélection qui en découle. **Règle à appliquer : un témoin positif emprunté à un
   > organisme moins séquencé que celui de l'étude n'étalonne pas l'étude.** Vérifier la
   > profondeur de MSA du témoin AVANT de le calculer, pas après. **Conséquence sur la portée de ce
   > garde-fou, à ne pas escamoter** : ce témoin établit que le score ne discrimine pas
   > quand le partenaire n'a pratiquement pas d'homologues, ce qui est un régime réel
   > mais étroit ; il **n'étalonne pas** un criblage dont les partenaires ont des MSA
   > profonds (326 à 1983 séquences dans le cas Rv0007). Avant d'invoquer ce garde-fou
   > contre un criblage, **mesurer la profondeur TOTALE du MSA de chaque partenaire, pas
   > seulement la profondeur appariée** — les deux se comportent différemment, et c'est
   > la profondeur brute qui porte l'essentiel de l'information selon Luo et al. 2026.
   >
   > Ce n'est PAS un verdict général sur Boltz : le même écosystème a produit des
   > négatifs propres et des contrastes massifs sur des paires solubles ou
   > ligand-dépendantes (`Rv1025`, `Rv2516c` ci-dessus). Le constat est spécifique
   > au régime TM-TM dont le partenaire n'a quasiment pas d'homologues (MSA total de
   > l'ordre de la dizaine de séquences, appariement nul), cf. la correction ci-dessus.
   > **Dans ce régime, un criblage de partenaires
   > par co-repliement ne produit pas de résultat exploitable, et il faut le dire
   > avant de lancer le calcul plutôt qu'après l'avoir écrit dans un manuscrit.**
   >
   > **Ancrage bibliographique (vérifié le 2026-09-03, DOI résolus contre CrossRef et
   > citations relues sur le texte).** Le constat général est publié et il faut le
   > citer plutôt que le redécouvrir : **Smorodina et al., bioRxiv 2026,
   > 10.64898/2026.03.02.709004** ont mesuré exactement cela sur 106 complexes
   > nanocorps-antigène expérimentaux contre 11 342 appariements mélangés, avec
   > AlphaFold3, **Boltz-2** et Chai-1 — « internal confidence metrics (ipTM)
   > frequently failed to discriminate correct from incorrect pairings », et
   > « increased sampling improved structural refinement but not pairing
   > discrimination ». En criblage d'interactome : Schmid & Walter, *Mol Cell* 2025,
   > 10.1016/j.molcel.2025.01.034 ; Lambourne et al., *Nat Commun* 2026,
   > 10.1038/s41467-026-70942-x. Deux covariables publiées faussent en outre toute
   > comparaison d'ipTM entre paires : la **taille** (Todor et al., *Mol Syst Biol*
   > 2026, 10.1038/s44320-026-00189-7 : ipTM des paires non interagissantes
   > proportionnel à la racine de la taille sommée) et le **désordre** (Dunbrack,
   > bioRxiv 2025, 10.1101/2025.02.10.637595, ipSAE). Todor chiffre aussi la
   > variabilité de graine : sur 314 paires repliées deux fois, 16,6 % diffèrent de
   > plus de 0,1 en ipTM et 2,5 % de plus de 0,4 — **ce seul chiffre condamne toute
   > lecture à n = 1**. Enfin, ne pas parler de « contrainte de coévolution » à propos
   > de la profondeur appariée : Luo et al., bioRxiv 2026,
   > 10.64898/2026.04.14.718427, montrent par appariement mélangé que les gains
   > viennent de la profondeur brute, pas des contraintes d'appariement.
2. **Le discriminant net est le PAE inter-chaînes minimum**, pas l'ipTM absolu —
   **mais seulement à n ≥ 5 et publié avec sa dispersion.** Amendement du
   2026-09-03 : le minimum est une statistique d'extrême sur une cellule parmi des
   milliers, et à `--diffusion_samples 1` il n'a pas de variance, donc il ne
   départage rien (garde-fou nº0). Mesuré sur un même échantillon : 0,53 à 7,41 Å
   selon le tirage. Rapporter systématiquement min ET moyen, chacun avec son
   écart-type sur les échantillons.

   > **CE QUE COÛTE EXACTEMENT UN CRIBLAGE À n = 1, MESURÉ** (2026-09-03, `mtbc/Rv0007`
   > P5.3 : les six paires d'un criblage publié rejouées à 3 graines × 5 échantillons,
   > **MSA figé**, soit 15 modèles par paire ; 39 jobs A100, ~2 min chacun).
   > - **L'ordre lu à n = 1 ressortait dans 54 à 66 % des tirages seulement** (bootstrap
   >   20 000 tirages d'un modèle par paire), sur la construction où il s'est finalement
   >   avéré juste — et dans 20 à 29 % sur l'autre construction, où il était faux. Un
   >   criblage à un échantillon ne vaut donc guère mieux qu'un tirage à pile ou face
   >   entre trois partenaires, y compris quand sa conclusion se trouve bonne.
   > - **Deux lectures secondaires du criblage étaient de purs artefacts d'échantillon
   >   unique** : un candidat déclaré « pire que le témoin négatif » (ipTM publié 0,163,
   >   jamais retrouvé en 15 tirages, étendue 0,185-0,647) devient indiscernable du
   >   témoin ; et un « contrôle négatif interne en échec » (le témoin battait les deux
   >   candidats) cesse d'échouer à n = 15. **Un contrôle négatif qui gagne à n = 1 n'est
   >   pas un résultat, c'est un tirage.**
   > - **La variance vient de l'échantillonnage, pas de la graine** : σ intra-graine
   >   0,048-0,142 en ipTM, σ inter-graine 0,019-0,081 à MSA figé. Conséquence
   >   opérationnelle directe : **`--diffusion_samples 5` fait le travail, multiplier les
   >   `--seed` est du gaspillage.**
   > - **Boltz-2 est parfaitement déterministe à graine fixée, MSA compris.** Deux jobs
   >   d'un même lot se sont trouvés porter la même séquence de partenaire (deux paralogues
   >   à fenêtre TM identique) : MSA générés séparément par le serveur, sorties identiques
   >   au millième (0,325 d'ipTM, 13,73 Å, 277 lignes appariées de part et d'autre). Le
   >   bruit de bout en bout du pipeline est nul ; toute la dispersion observée est celle
   >   de la diffusion. Utile à savoir avant de soupçonner l'infrastructure.

2 bis. **CALIBRER CONTRE UNE DISTRIBUTION NULLE DE PARTENAIRES TIRÉS AU HASARD, pas
   contre un unique témoin négatif choisi.** Un témoin négatif isolé donne un point,
   pas une échelle : il peut être atypiquement sévère ou atypiquement complaisant, et
   rien dans le criblage ne le dit. **Recette, ~20 jobs, générique** (2026-09-03,
   `mtbc/Rv0007` P5.3, volet B ; script de conception
   `mtbc/Rv0007/analyses/phase10_p5_3_variance_et_nulle.py`) : tirer au hasard une
   vingtaine de partenaires du même protéome, du **même régime biophysique** que les
   candidats (ici : protéines monotopiques prédites par DeepTMHMM, fenêtre de la même
   longueur exacte que les candidats, centrée sur l'hélice TM), **excluant mécaniquement
   par mots-clés du produit tout ce qui touche à la fonction étudiée** — un décoy doit
   être invraisemblable, pas seulement non testé (sur ce cas, un premier tirage avait
   retenu un domaine DivIVA, un Lcp et un domaine FHA, tous trois liés à la paroi :
   filtre resserré avant calcul). Chaîne requête identique et longueur de partenaire
   constante : **le biais de taille (Todor 2026) est alors neutralisé par construction**,
   pas seulement écarté par un argument.
   Ce que la distribution nulle a donné sur ce cas : ipTM médian **0,596**, étendue
   **0,325-0,741** ; PAE minimum médian **6,63 Å**, étendue 4,11-13,73. Le « gagnant » du
   criblage (0,681 / 4,64 Å) tombait au **85e-90e centile — deux décoys faisaient mieux**,
   une PPE et une autre PPE. Autrement dit un score qui semblait net, et qui battait
   significativement le témoin choisi, **était atteignable par une protéine PPE, une Mce
   ou une sous-unité d'ATP synthase prise au hasard**. Le témoin négatif d'origine, lui,
   se situait au 35e centile : représentatif, mais rien ne permettait de le savoir avant.
   **Bénéfice secondaire gratuit** : ces ~20 paires à taille constante donnent aussi la
   régression profondeur appariée → score que le garde-fou nº0 réclame, sur 20 points au
   lieu de 3 (ici ρ = −0,314, p = 0,18 : le signe de l'effet soupçonné, mais pas la
   significativité — ce qui a suffi à rétrograder l'explication mécanistique candidate).

2 ter. **TESTER LA SENSIBILITÉ D'UN CLASSEMENT À LA PROFONDEUR APPARIÉE, en 7 jobs.**
   Une corrélation entre profondeur et score ne se lit pas, elle se manipule. Dans les
   MSA au format Boltz (`key,sequence` : clé `0` = requête, clés `1..N` = lignes appariées
   entre chaînes, `-1` = non appariée), **basculer les clés excédentaires vers `-1`**
   appauvrit l'appariement **en laissant la profondeur TOTALE intacte** — les séquences
   restent et informent le repliement de chaque chaîne, seule l'information inter-chaînes
   part. Supprimer les lignes changerait deux variables à la fois, la profondeur brute
   agissant déjà sur le score (Burke 2023, Luo 2026). Prendre trois tirages indépendants
   des lignes conservées : quelles lignes on garde n'est pas neutre. Script réutilisable :
   `mtbc/Rv0007/analyses/phase12_p5_1_sousechantillonnage.py`.
   Résultat obtenu sur le cas Rv0007 (2026-09-03, P5.1), qui donne l'ordre de grandeur à
   attendre : appauvrir une paire de 714 à 12 lignes fait **monter** son ipTM de 0,406 à
   0,516 (+0,111, t = +2,14, les trois tirages concordants, dose-réponse cohérente à
   100 lignes) — mais **ne comble que 40 % de l'écart** avec la paire naturellement pauvre
   du même criblage, et **le témoin de la même campagne réagit en sens inverse**
   (0,520 → 0,461). **À retenir tel quel : la profondeur appariée est une covariable
   causale du score, d'effet modeste et de signe dépendant de la paire — à mesurer et à
   déclarer, jamais à invoquer comme le mécanisme qui fabriquerait un classement, et jamais
   sous la forme « le partenaire au MSA le plus pauvre gagne ».**

   > **CETTE MANIPULATION EST PUBLIÉE, NE PAS LA REDÉCOUVRIR** (contrôle de nouveauté du
   > 2026-09-03, DOI résolu, citation vérifiée sur le texte). Li, Mu & Yan, bioRxiv 2026,
   > 10.64898/2026.04.03.716280, la nomment **Block MSA** : « all non-query sequences were
   > gap-padded to eliminate inter-chain pairing » — les séquences restent, seul
   > l'appariement disparaît, exactement la bascule de clés décrite ci-dessus. Et leur
   > résultat, à retenir avant de lancer quoi que ce soit : « Predictions from Block MSAs
   > and native AFM MSAs are **nearly indistinguishable (|Δ| ≤ 0.2)**, indicating that
   > explicit sequence pairing contributes little to predictive accuracy. » L'effet mesuré
   > sur Rv0007 (+0,08 à +0,11 d'ipTM) tombe dans cette marge d'indiscernabilité.
   > **Conséquence pratique : faire ce test pour vérifier la robustesse d'un classement
   > donné reste utile ; en attendre un effet publiable ne l'est pas.** Le voisin à citer
   > est Luo et al., bioRxiv 2026, 10.64898/2026.04.14.718427 (appariement mélangé, qui
   > détruit la correspondance en conservant la profondeur).
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

   > **UN ÉCART DE pLDDT ENTRE DEUX PRÉDICTEURS N'EST PAS UN EFFET BIOLOGIQUE tant que
   > l'offset des deux outils n'a pas été mesuré SUR LA MÊME CONSTRUCTION** (mesuré le
   > 2026-09-05, `mtbc/Rv2566` P8.2 ; c'est le pendant monomère du garde-fou nº0, qui ne
   > couvrait que les interfaces). Question posée : un fragment tronqué par frameshift
   > (533 aa sur 1140) garde-t-il un module catalytique replié une fois privé de son
   > échafaudage C-terminal ? Boltz-2 sur le fragment rendait **83,56** de pLDDT moyen sur
   > le module, contre **93,10** pour les mêmes résidus du modèle AlphaFold pleine longueur
   > — soit −9,54, qu'il aurait été naturel de lire comme une déstabilisation par
   > troncature. **La totalité de ces 9,54 points était l'offset entre les deux outils** :
   > le module SAUVAGE (les 252 mêmes résidus, sans aucune troncature) replié par Boltz-2
   > rend **83,50**. Écart réel imputable à la troncature : **0,06 point.**
   >
   > Trois conséquences pratiques, toutes transposables :
   > - **Chercher le contrôle sur le disque AVANT de lancer un job.** Ici les 30 modèles
   >   d'étalonnage (6 constructions × 5 échantillons) existaient déjà, produits des semaines
   >   plus tôt par une AUTRE piste du même projet pour une AUTRE question. Coût du contrôle
   >   décisif : zéro cycle de calcul. Le réflexe « il me faut un contrôle donc je lance un
   >   job » a failli faire dépenser une nuit de CPU pour une réponse déjà disponible.
   > - **Construire d'emblée les lectures qui n'ont pas besoin de l'offset**, plutôt que de
   >   s'en remettre à la comparaison directe : (a) un contraste INTERNE au seul modèle (ici
   >   module catalytique 83,56 contre moignon du domaine amputé 72,79, p = 3,2e-27) ne fait
   >   intervenir aucune calibration ; (b) une DIFFÉRENCE DES DIFFÉRENCES entre deux régions
   >   annule tout décalage uniforme d'outil ; (c) un **RMSD Cα après superposition de
   >   Kabsch** ne dépend d'aucune échelle de confiance et s'est révélé le résultat porteur
   >   (module tronqué à 1,52 Å du modèle pleine longueur, contre 19,19 Å pour le moignon).
   > - **Un RMSD non plus n'a pas d'échelle tant qu'on ne l'a pas étalonné.** Les mêmes 30
   >   modèles ont montré que Boltz-2 s'écarte du modèle AlphaFold de 1,14 à 6,62 Å sur ce
   >   module SAUVAGE (moyenne 2,98 Å) : les 1,52 Å du fragment tronqué ne sont donc pas
   >   seulement « bons », ils sont dans le tiers le plus favorable de ce que l'outil produit
   >   quand rien n'est tronqué. Sans cet étalonnage, 1,52 Å restait un chiffre nu.
   >
   > **Bénéfice secondaire, gratuit** : un lot déjà calculé à `--diffusion_samples 5` fournit
   > aussi la dispersion qu'un job à n = 1 ne peut pas donner (ici σ INTRA-construction 0,30
   > à 1,08 point de pLDDT, toute la dispersion inter-modèles venant du CONTEXTE et non du
   > tirage) — de quoi répondre au garde-fou nº2 sans rejouer le job.
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
