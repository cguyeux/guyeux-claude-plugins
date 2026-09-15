# Services du mésocentre au-delà du `sbatch`

Relevé documentaire (`mesoservices.univ-fcomte.fr` et `mesowiki.univ-fcomte.fr`) croisé avec une
sonde du 2026-09-04. Ces services sont réels et ouverts, mais aucun n'est utilisé aujourd'hui : ce
fichier existe pour qu'on cesse de résoudre en local des problèmes qui ont déjà une réponse ici.

## Base de données hébergée — `mesodb.univ-fcomte.fr`

Machine dédiée à l'hébergement de bases, physiquement dans le cluster, reliée au calcul en
Infiniband et joignable depuis tout le réseau universitaire.

| | |
|---|---|
| Matériel | Xeon E5-2630 v2, 12 cœurs, **128 Go de RAM**, **500 Go SSD** + 5 To de disque |
| Moteurs | **PostgreSQL 17.5**, **PostGIS 3.5**, MariaDB 11.6.2 |
| Administration | pgAdmin4 `https://mesodb.univ-fcomte.fr/postgresql/`, phpMyAdmin `/mariadb/` |
| Accès | **sur demande** à `meso-admins@univ-fcomte.fr`, création d'identifiants |

Le port 5432 répond depuis `mh` (vérifié le 2026-09-04). Intérêt concret : toute base de travail
qu'on interroge aujourd'hui en SQLite local ou en PostgreSQL sur un poste unique (annotations de
génomes, corpus bibliographique, catalogues de variants, index de projet) peut y vivre avec 128 Go
de RAM, un SSD, une sauvegarde d'établissement et un accès depuis les nœuds de calcul comme depuis
le bureau. PostGIS ouvre en prime les requêtes spatiales sur les métadonnées géographiques.

## JupyterHub — `https://mesohelios1.univ-fcomte.fr`

Identifiants du mésocentre. Au démarrage on choisit un profil :

- `Local` : tourne sur la frontale, **sans GPU**, réservé aux tests ;
- profils Slurm : **1 GPU, 72 ou 128 Go de mémoire, 4 heures**.

Réservé aux sessions courtes ; un calcul long reste un `sbatch`. Arrêter le serveur explicitement
par `Control Panel` → `Stop My Server`, se déconnecter ne suffit pas et laisse le job Slurm vivant.

Pour utiliser un environnement conda existant comme noyau :

```bash
conda install -c conda-forge ipykernel
python -m ipykernel install --user --name monenv --display-name "Mon env (Python)"
# noyau R : conda install -c conda-forge r-irkernel puis
# R -e "IRkernel::installspec(name='r_env', displayname='r_env (R)')"
```

Variante sans JupyterHub, depuis un job interactif : lancer
`jupyter-notebook --no-browser --ip=0.0.0.0` sur le nœud, puis depuis la frontale
`ssh -g -N -L 9999:localhost:8888 <login>@node4-21`, et ouvrir
`http://mesohelios1.univ-fcomte.fr:9999` avec le jeton affiché.

## Visualisation 3D accélérée — partition `visu`

Trois NVIDIA A40, 64 cœurs, 252 Go, VirtualGL, trois sessions simultanées maximum, 4 heures par
défaut. Il faut **TurboVNC** sur le poste local.

```bash
# sur la frontale, depuis $WORK
svgl                 # ou /Softs/helios/visu/svgl en SSH non interactif
svgl -t 6:00:00      # plus de temps
svgl --mem=96G       # plus de mémoire (maximum 192 Go)
export VNC_OPTIONS="-geometry 1680x1050"   # résolution, avant svgl
```

`svgl` affiche l'adresse VNC de la session (`mesohelios1.univ-fcomte.fr:1`), qui **change à chaque
fois**. Les programmes OpenGL se lancent préfixés par `vglrun`. Fermer le client VNC laisse la
session vivante et permet d'y revenir ; se déconnecter de XFCE tue le job. Première utilisation :
initialiser l'environnement XFCE une fois via X2Go, sinon `svgl` échoue.

## L'autre cluster, Lumière, n'est pas mort : c'est une seconde machine en service

Contrairement à ce que suggère l'âge de sa documentation, Lumière tourne. Relevé sur le Ganglia
public du mésocentre (`https://mesoportail.univ-fcomte.fr/ganglia-cluster/?c=lumiere`, sans
authentification) le **2026-09-04 à 15h43** : **1162 cœurs, 68 hôtes actifs, 0 hors service**,
charge moyenne 27 %, et les nœuds sont individuellement quasi inactifs.

| ressource | ce qu'elle offre |
|---|---|
| **`mesoshared.univ-fcomte.fr`** | **96 cœurs, 256 Go**, machine SMP partagée **sans ordonnanceur ni file**, 408 jours d'uptime |
| file `volta.q` | 2 nœuds, **8 GPU** dont 4× **V100-SXM2 32 Go** sur `node3-70`, limite 8 jours |
| file `bigmem.q` | 96 Go, séquentiel et OpenMP |
| `mesologin1` / `mesologin2` | frontales SGE (`qsub`, `qstat`, `qdel`), CentOS 6 |
| `mesowin1.univ-fcomte.fr` | **Windows Server 2012 R2**, 32 cœurs, 128 Go, Quadro K5200, 8 To sur `G:`, accès RDP sur ticket |

Intérêt concret : une V100 de 32 Go immédiatement libre vaut mieux qu'une A100 dans une file, et
`mesoshared` offre 96 cœurs et 256 Go sans attendre, là où `smp` sur Helios plafonne à 32 cœurs et
96 Go par nœud. Cet intérêt a **baissé pour le GPU** depuis l'attachement de la QOS `3gpu` le
2026-09-07, qui permet trois A100 de front sur Helios : Lumière reste surtout utile pour le
CPU sans file (`mesoshared`) et comme repli quand la partition `gpu` d'Helios est en `drain`.

> [!NOTE]
> **Accès obtenu le 2026-09-04**, après un détour instructif. Les alias `ml` (mesologin1) et `ms`
> (mesoshared) sont configurés et fonctionnent par le rebond `bilbo`. Trois conditions étaient
> nécessaires : les algorithmes hérités (`HostkeyAlgorithms +ssh-rsa`,
> `PubkeyAcceptedAlgorithms +ssh-rsa`), la clé **RSA** et non ED25519 (OpenSSH 5.3 côté serveur),
> et surtout le dépôt de la clé dans le **bon** répertoire personnel, voir le piège ci-dessous.

> [!CAUTION]
> **Deux répertoires personnels, et `ssh-copy-id` écrit dans le mauvais.** `getent passwd` donne
> `/Home/Users/<login>` comme répertoire de connexion, mais le profil réexporte `HOME` vers
> `/Work/Users/<login>` dès qu'un shell démarre. Toute commande distante écrit donc dans l'espace de
> travail, alors que `sshd` lit `authorized_keys` **avant** tout shell, dans le répertoire de
> `/etc/passwd`. Un `ssh-copy-id` conclut par `Number of key(s) added: 1` et la connexion reste
> refusée, avec le message d'une clé absente. Correctif appliqué : recopier la clé dans
> `/Home/Users/<login>/.ssh/authorized_keys` en 600, le répertoire `.ssh` en 700.

> [!CAUTION]
> **`/Work/Users/<login>` n'est PAS le même espace sur Lumière et sur Helios.** Ce sont deux
> systèmes BeeGFS distincts au chemin identique : 233 To (116 utilisés) côté Lumière, 193 To
> (47 utilisés) côté Helios, et des contenus qui n'ont rien à voir. Un script qui écrit dans
> `/Work/Users/cguyeux` n'écrit pas au même endroit selon la machine, sans aucun avertissement.

État relevé le 2026-09-04, une fois connecté :

| | |
|---|---|
| `mesologin1` | CentOS 6.10, noyau 2.6.32, 12 cœurs Xeon X5650, 62 Go. Frontale seulement. |
| `mesoshared` | **96 cœurs, 251 Go dont 239 libres**, charge 0.11, 408 jours d'uptime. Réellement disponible. |
| files SGE actives | `all.q` (896 slots, 347 libres), `parallel.q` (1040, 272 libres), **`volta.q` (28 slots, 28 libres)**, `3dvisu.q`, `interactive.q` |
| files hors service | `bigmem.q`, `tesla.q`, `xphi.q`, `magma.q`, `logincentos79` : tous leurs slots en état `cdsuE` |
| modules bio | `bwa`, `bcftools`, `bamtools`, `htslib`, `emboss`, `cdhit`, `exabayes`, `mira`, `igv`, `mcl`, `dwgsim` |

> [!TIP]
> **`free -g` n'a pas le même format sur CentOS 6.** Il n'y a pas de colonne `available` : la
> septième colonne est `cached`. Une sonde écrite pour Rocky 8 y lit donc 1 Go de mémoire
> disponible sur une machine qui en a 239 de libres, et conclut à tort à la saturation. Lire la
> colonne `free`, ou `free -h` en entier.

Attention en revanche à ne rien transposer de sa documentation vers Helios : toute la syntaxe SGE
(`qsub`, `#$ -pe openmp N`, `$NSLOTS`, `$SGE_TASK_ID`, `-l h_vmem`, files `all.q`, `parallel.q`,
`tesla.q`) et les versions logicielles du wiki, qui accusent une décennie de retard, n'y ont aucun
équivalent. `mesologin1` est resté en CentOS 6, ce qui explique la plupart des contournements
alambiqués qu'on lit dans ce wiki (conda sous Singularity, Python plafonné à 3.7).

## Centres nationaux, quand Helios ne suffit plus

Accès GENCI (Jean Zay à l'IDRIS, Adastra au CINES, TGCC) par une demande DARI sur `edari.fr`.
**Deux campagnes par an** : de septembre à décembre pour une attribution au 1er janvier, de mai à
juin pour le 1er juillet. À viser pour un besoin GPU qui dépasse durablement ce qu'Helios peut
donner, c'est-à-dire aujourd'hui trois A100 de 40 Go en parallèle (QOS `3gpu`, prêtée depuis le
2026-09-07) sur un cluster que ses administrateurs décrivent eux-mêmes comme « très limité en
ressources ». Un entraînement qui demande de la VRAM agrégée avec une interconnexion rapide, ou
plusieurs semaines de GPU continues, relève du DARI et non d'une nouvelle demande de QOS.

## Coût, et ce qu'un projet peut financer

Le mésocentre applique un « ticket modérateur » par laboratoire :

| heures CPU par an | montant |
|---|---|
| **moins de 100 000** | **gratuit** |
| moins de 500 000 | 3 000 € |
| moins de 1 000 000 | 6 000 € |
| plus de 1 000 000 | 9 000 € |

Repère : 100 000 heures CPU, c'est douze cœurs occupés en continu pendant un an. Facturation à
l'heure hors forfait : 6 centimes en interne (UFC, UTBM, ENSMM), 10 centimes à l'extérieur.

Pour un dossier de financement, la règle qui compte : **un projet ANR ne retient que les coûts
marginaux, donc ne peut PAS payer des heures de calcul facturées en interne — il doit financer des
machines**, hébergées au mésocentre sur devis de celui-ci. Un projet européen ou région, à
l'inverse, peut financer indifféremment des machines ou des heures. Tout investissement en machines
se déduit du ticket modérateur, sur plusieurs années si besoin.

## Contacts et vie du service

L'équipe et la gouvernance, utiles parce que la voie du ticket n'est pas la seule : **Kamel Mazouzi**
est le responsable technique (bureau 155B), **Robin Tissot** ingénieur d'études (bureau 153B),
**Fabien Picaud** responsable scientifique. Un **comité scientifique** composé de représentants des
utilisateurs, dont **Raphaël Couturier** pour FEMTO-ST, reçoit conseils, propositions et arbitrages
de ressources. C'est la voie institutionnelle pour demander un logiciel, une file dédiée ou un
arbitrage, distincte du ticket technique. Un accès pédagogique existe aussi, à demander une semaine
avant une séance : compte partagé et file réservée avec passage direct, ce qui évite qu'un TP à
trente étudiants sur GPU ne se heurte à la file générale.

- Tickets techniques, canal officiel : `svpmeso@univ-fcomte.fr` (un sujet par problème, avec login,
  message d'erreur, chemin du script et identifiant du job). **En pratique cette boîte ne nous a
  jamais servi qu'à recevoir des notifications automatiques d'expiration de compte** ; les demandes
  de ressources qui ont abouti sont passées par le mail direct à Kamel Mazouzi avec
  `meso-admins@univ-fcomte.fr` en copie.
- Équipe : `meso-admins@univ-fcomte.fr`. Téléphone 03.81.66.63.11 ou 03.81.66.20.12.
- **Liste `meso-utilisateurs@univ-fcomte.fr`** : c'est là et nulle part ailleurs que sont annoncées
  les maintenances. Un cluster injoignable un mardi matin est probablement une maintenance annoncée
  sur cette liste, pas une panne.
- **VPN** : la connexion se fait avec l'identifiant **ENT**, pas l'identifiant mésocentre, et le nom
  d'utilisateur doit être suffixé par `@ufc` (par exemple `guyeux@ufc`). Documentation officielle sur
  `vpn.univ-fcomte.fr`.
- **Supports de formation** en français, téléchargeables sans authentification depuis
  `mesowiki.univ-fcomte.fr/dokuwiki/lib/exe/fetch.php?media=<nom>` : `openmp.pdf`, `MPI-1.pdf`,
  `intro_parallel.pdf`, `optimisation.pdf`, `PrallelMPI_Application.pdf`. Matière de cours HPC
  réutilisable en master.
- Publications : le mésocentre demande à être cité, « Computations have been performed on the
  supercomputer facilities of the Mésocentre de calcul de Franche-Comté ». À placer dans les
  remerciements de tout article dont un calcul est passé par `mh`.
