# Phase 4 — Finalisation et diffusion (détail opératoire)

À lire à l'entrée en phase 4, une fois la porte 3 franchie (le manuscrit anglais
ne bouge plus sous le pipeline qualité).

---

## 0. Trancher le mode de diffusion — avant toute proposition de cible

Un manuscrit stabilisé (porte 3 franchie) n'implique pas une soumission à comité de
lecture. Demander explicitement à l'auteur, sans présumer, lequel des quatre modes
s'applique à **ce** projet et à **cette** itération :

| Mode | Description | Gestes de la section 5 | Cible/style/déclaration IA |
|---|---|---|---|
| **(a)** | Soumission à une revue ou conférence à comité de lecture | préprint + code | requis (sections 2 à 6 en entier) |
| **(b)** | Préprint seulement, pas de soumission à comité pour l'instant | préprint (code en option) | non requis |
| **(c)** | Code et données seulement | code | non requis |
| **(d)** | Aucun dépôt externe pour l'instant | aucun | non requis |

**Raisons légitimes de choisir (b), (c) ou (d)** : temporisation délibérée, absence
d'envie de gérer un cycle de révision pour l'instant, priorité donnée à d'autres
projets, ou toute autre raison propre à l'auteur — aucune de ces raisons n'a besoin
d'être justifiée davantage qu'un simple choix exprimé.

**Ce choix n'est pas irréversible.** Un projet clôturé sur (b), (c) ou (d) est
archivé dans `clos/` (Phase 5) plutôt que `clos_soumis/`, et peut en
repartir vers le déroulé (a) le jour où l'auteur le souhaite : rien n'est à refaire,
le manuscrit et son code sont intacts, seul le geste de dépôt manquant s'ajoute.

Pour les modes (b), (c) et (d), la version française (section 1) reste produite :
elle sert la relecture personnelle et la réutilisation de l'auteur (séminaire,
dossier, HDR), indépendamment de toute soumission.

---

## 1. Version française traduite à la lettre

Produire `article/main_fr.tex` : **traduction fidèle, pas adaptation**. Même
structure, mêmes sections, mêmes figures, mêmes chiffres, mêmes références. Ce
n'est pas une version grand public ni un résumé étendu : c'est le même article en
français, pour que l'auteur puisse le relire dans sa langue et le réutiliser
(séminaire, dossier, rapport d'activité, HDR).

Compiler et vérifier que le PDF français sort proprement (césures, guillemets
français via `csquotes`, espaces insécables avant `: ; ! ?`).

---

## 2. Choisir la cible — et ne jamais perdre de matériel

*(Mode (a) uniquement — sauter à la section 5 pour les modes (b), (c), (d).)*

Deux familles à proposer **ensemble**, jamais l'une seule :

**Conférences sélectives** — visibilité rapide, mais deux contraintes à poser
AVANT de proposer : la présentation en direct est en général obligatoire pour
l'entrée aux actes, et le budget congrès doit être acquis. Un papier accepté mais
non présenté n'entre pas dans les actes et reste libre de toute double soumission
(cf. `~/.claude/knowledge/scientific-journals.md`, qui documente ce cas vécu).

**Revues** — avec **systématiquement des options gratuites** dans la proposition :

- **Diamond OA** (gratuit auteur et lecteur, aucun APC) : la cible prioritaire dès
  que le scope correspond.
- **Accords transformatifs Couperin** : vérifier la couverture avant de présumer un
  APC. L'accord couvre l'APC pour l'auteur corresponding affilié à un établissement
  abonné, ce qui est le cas de l'UMLP chez les grands éditeurs.
- **Voie verte** : à défaut, une revue hybride sans APC avec dépôt du postprint en
  archive ouverte (HAL) reste une option gratuite.

La cartographie détaillée (diamond OA, Elsevier, Springer-Nature, couverture
Couperin, pièges éditoriaux vécus) vit dans
**`~/.claude/knowledge/scientific-journals.md`** — la lire et l'**enrichir** après
chaque soumission, plutôt que de re-dériver le paysage à chaque projet. Elle est
orientée épidémiologie computationnelle et IA santé ; pour un manuscrit de
phylogénomique ou de génomique comparative bactérienne, s'appuyer aussi sur les
cibles déjà éprouvées par vos propres projets clos, si vous en tenez un registre.

### La règle qui gouverne toutes les propositions

Chaque cible proposée est **soit compatible avec la taille de l'article** (limite
de mots, de figures, de références), **soit accompagnée d'une proposition de
refactoring** qui redistribue le matériel de sorte qu'**aucun travail ne soit
perdu**.

Exemple de refactoring légitime : passer de deux à trois articles, le premier vers
une revue à format court à fort ticket d'entrée, le second vers une revue de
domaine à format long, le troisième vers une revue méthodologique. Chaque morceau a
sa cible.

Ce qui n'est **jamais** acceptable : proposer une revue à 4 000 mots pour un
manuscrit de 9 000 sans dire ce que deviennent les 5 000 mots retirés. Une coupe
sèche n'est pas une réponse ; la seule réponse valable est une destination (autre
article, supplementary materials, ou `/recadrage` en sérendipité).

Vérifier la taille réelle avant de proposer : `/deai-latex` et
`/manuscript-review` mesurent la longueur face à la limite de la revue cible et
identifient le matériel basculable en supplementary.

---

## 2bis. Cadrer la vitrine sur la cible retenue — avant tout reformatage

*(Mode (a) uniquement.)*

La cible arrêtée, le geste suivant n'est pas le gabarit LaTeX : c'est `/cadrage-editorial
<cle>`. Cette passe relit le titre, le résumé, les mots-clés, la clôture d'introduction, la
première phrase de discussion, la conclusion et la lettre d'accompagnement contre ce que
cette revue publie réellement, mesuré sur son corpus des douze derniers mois, et fait
simuler le desk-reject par une instance indépendante qui ne voit que ce que l'éditeur lit.

Ce que la section 2 fait, c'est écarter les cibles impossibles. Ce que celle-ci fait, c'est
éviter qu'un travail adéquat soit renvoyé sur un malentendu de formulation. Le périmètre est
strictement borné à la vitrine : Résultats, Méthodes, figures et ordre de la démonstration
ne sont pas touchés, ce dernier appartenant à `plan_narratif.md` et au skill `narratif`.

Le verdict, daté dans `cadrage_editorial.md`, est l'un de quatre : `ALIGNE` (passer à la
section 3), `RETOUCHER` (appliquer, revérifier, empiler un `ALIGNE`), `CHANGER-DE-CIBLE`
(retour section 2 : l'écart ne se comble pas sans mentir) ou `ROUVRIR` (retour porte 3bis :
aucune vitrine honnête n'existe pour ce niveau de revue). `preflight.py` bloque la
soumission tant qu'aucune entrée `ALIGNE` ne couvre la clé de revue visée.

---

## 3. Adapter le style à la cible

*(Mode (a) uniquement.)*

Une fois la cible retenue : classe LaTeX de l'éditeur, style bibliographique,
conventions de sections, limite de mots du résumé, format des figures. Skills :
`latex-paper-en` (audit et conformité), `latex-formatting` (gabarits éditeurs),
`/deai-latex` (style scientifique, économie du texte), `/fig-check` (figures aux
normes après changement de gabarit — un changement de classe change les largeurs).

---

## 4. Mener la soumission, en sollicitant l'auteur le moins possible

*(Mode (a) uniquement.)*

**Principe** : l'assistant fait la plus grande part possible via l'automatisation
du navigateur (`claude-in-chrome`), en s'appuyant sur les ressources déjà
disponibles :

- **`/cv`** — nom canonique, affiliation exacte, ORCID, historique de publications,
  financements ; tout ce que les formulaires éditeurs réclament.
- **Mails** (MCP `superhuman`) — retrouver les identifiants de compte éditeur
  existants, récupérer les accusés de réception, suivre le statut. Rappel de la KB
  `scientific-journals.md` : **le statut éditorial d'un manuscrit ne se lit pas dans
  son dépôt**, seuls les mails du système de gestion et le programme officiel font
  foi.
- **Web** — scope exact de la revue, instructions aux auteurs, limites en vigueur.

**Ce que l'assistant prépare et remplit seul** : création ou réutilisation du
compte, métadonnées (titre, résumé, mots-clés, catégories), téléversement des
fichiers, lettre d'accompagnement (cover letter) rédigée depuis le message de
l'article, suggestions de relecteurs, déclarations standard (conflits d'intérêts,
contributions, disponibilité des données).

**Ce qui remonte à l'auteur, et rien d'autre** : le clic final de soumission quand
l'éditeur exige une action authentifiée de l'auteur lui-même, les déclarations
légales engageant sa responsabilité, tout paiement, et une connexion interactive
qu'il faut faire soi-même (proposer alors la forme `! <commande>` ou la saisie
manuelle dans le navigateur).

**Pièges d'automatisation connus** (cf. `~/.claude/knowledge/claude-in-chrome-automation.md`) :
boutons radio stylés non cochés par clic-coordonnées, portails derrière Cloudflare
(OpenReview notamment — ne **jamais** créer un second profil, réinitialiser le mot
de passe sur l'adresse institutionnelle rattachée). Après deux ou trois échecs sur
la même action, s'arrêter et demander plutôt que de boucler.

---

## 5. Dépôts libres

*(Selon le mode retenu en section 0 : préprint pour (a) et (b), code pour (a) et
(c), aucun des deux pour (d).)*

**Préprint** — déposer sur le serveur correspondant au domaine : **bioRxiv**
(biologie, génomique, phylogénomique), **medRxiv** (si le contenu touche à la santé
humaine ou au clinique), **arXiv** (si la contribution est méthodologique ou
computationnelle). Le dépôt est gratuit et rend l'article citable immédiatement.
Vérifier la politique de préprint de la revue cible avant dépôt (la quasi-totalité
des revues visées l'acceptent, mais quelques-unes contraignent la licence).

**Code et données** — pousser le dépôt compagnon sur
**`<votre-compte>/<votre-depot>`** (GitHub, public). Y déposer les
scripts d'analyse, les données dérivées et de quoi reproduire les figures. Pour un
DOI citable sur cet artefact, `/zenodo-deposit` crée le dépôt, réserve le DOI et
peut remplacer le placeholder dans le `main.tex` (la publication du dépôt, qui est
irréversible, reste une étape explicitement confirmée par l'auteur).

Ne pas confondre avec le dépôt Overleaf du manuscrit (`article/`, souvent privé et
nommé `article-<projet>`), qui sert la collaboration sur le texte.

⚠ **Piège vécu : pousser le PDF AVANT que la finalisation soit complète le rend
silencieusement périmé.** Le PDF `manuscripts/<projet>-characterisation.pdf`
avait été poussé à l'étape « préparer la soumission », un jour avant que la version
réellement déposée ne reçoive ses derniers ajustements imposés par le portail (ici : section
`Importance` ASM + `\journal{...}`, P7.21). Le dépôt public a affiché pendant 6 jours une
version de 21 pages différente des 22 pages réellement soumises, sans que rien ne le signale
(le README continuait d'afficher « Draft, pending peer review », jamais recalé sur
« Submitted »). Ne pousser le PDF (et mettre à jour son statut en « Submitted to \<revue\>,
pending peer review ») **qu'après** la confirmation effective du dépôt (porte 4, accusé de
réception), jamais à l'étape de préparation — et vérifier `pdfinfo`/`pdftotext` du fichier
poussé contre `article/main.pdf` local avant de considérer ce point clos.

⚠ **Piège apparenté (BPaL/BPaLM et dark_enzymes, `annotation_mtbc`, 2026-08-26) : un manuscrit
TRANSVERSAL qui caractérise plusieurs gènes sans qu'aucun n'ait de projet `mtbc/<Rv>/` dédié peut
soumettre sans que ses conclusions n'atteignent jamais les fiches atlas des gènes concernés** —
rien ne relie automatiquement un manuscrit thématique aux fiches qu'il caractérise (contrairement à
un projet-gène dédié, synchronisé par `gene_project_sync.py`). Avant de considérer la porte 4
franchie pour ce type de manuscrit, lancer, depuis `annotation_mtbc/` :

```
python3 analyses/manuscript_gene_sync.py <projet>
```

et rédiger à la main (jamais automatiquement, cf. docstring du script) une `curation_note` calibrée
pour chaque fiche signalée dont le gène est un vrai sujet de caractérisation — pas pour un simple
gène de fond/marqueur cité en passant.

---

## 6. Déclaration d'assistance IA — obligatoire pour le mode (a)

*(Mode (a) uniquement. Pour (b)/(c)/(d), la déclaration s'ajoute seulement au
moment où le projet, éventuellement plus tard, bascule effectivement vers une
soumission à comité de lecture.)*

Tout manuscrit **soumis** dans cet environnement porte, avant la bibliographie, une
section de déclaration. Texte canonique, éprouvé sur des manuscrits précédents :

```latex
\section*{Declaration of generative AI and AI-assisted technologies in the writing process}

During the preparation of this work, the author used Claude Code (Anthropic), an AI-agent software
environment powered by the Claude Sonnet 5 model, for in silico data retrieval, statistical analysis,
literature verification and drafting assistance, as described in the Materials and Methods. After using
this tool, the author reviewed, independently verified against primary sources, and edited the content
as necessary, and takes full responsibility for the content of this publication.
```

Adapter le nom du modèle effectivement employé. Quand la revue impose son propre
gabarit de déclaration, le sien prime : reprendre sa formulation en gardant les
trois éléments de fond (outil nommé, usage décrit, responsabilité pleine de
l'auteur).

**Et son pendant dans les Méthodes**, qui décrit l'usage réel plutôt que de le
déclarer en bloc — c'est lui qui rend la déclaration crédible en review :

```latex
The bioinformatic analyses, database queries and literature cross-referencing underlying this study were
carried out within an AI-augmented bioinformatics working environment, Claude Code (Anthropic), operating
the Claude Sonnet 5 language model as an interactive analysis agent under continuous human direction.
Every script, statistical test and numerical claim produced within this environment was independently
traced back to its underlying raw data, primary publication or database record before being reported
here, following the verification discipline described throughout this section; the corresponding author
designed the study, specified and reviewed every analysis, and takes full responsibility for the accuracy
of its content.
```

---

## Porte 4 — ce qu'il faut pouvoir montrer

**Mode (a)** :

- manuscrit **soumis** (accusé de réception dans les mails, pas une supposition) ;
- **préprint en ligne** avec son DOI ou son identifiant de serveur ;
- **code déposé** sur `deciphering-tuberculosis-with-ai`, avec le PDF **identique** à la
  version réellement soumise (`pdfinfo`/`pdftotext` recoupés contre `article/main.pdf` local,
  pas seulement « un PDF existe ») et le statut du tableau `README.md` recalé sur « Submitted » ;
- pour un manuscrit **transversal** (plusieurs gènes cités, aucun projet `mtbc/<Rv>/` dédié) :
  `python3 analyses/manuscript_gene_sync.py <projet>` lancé depuis `annotation_mtbc/` et ses
  fiches signalées traitées (cf. piège BPaL/BPaLM et dark_enzymes, section 5) ;
- **déclaration d'assistance IA** présente dans la version soumise ;
- version **française** compilée et archivée dans `article/`.

**Mode (b)** : préprint en ligne avec son identifiant de serveur (code déposé en
plus si l'auteur le souhaite) ; version française compilée et archivée.

**Mode (c)** : code et données déposés sur `deciphering-tuberculosis-with-ai` ;
version française compilée et archivée.

**Mode (d)** : rien à déposer ; version française compilée et archivée ; le choix
du mode (d) lui-même est tracé dans le cahier de labo et dans `pistes.md` ou
l'en-tête de `etat_des_decouvertes.md`, pour qu'une relecture future du projet
comprenne immédiatement pourquoi aucun dépôt n'a eu lieu sans avoir à demander à
l'auteur.
