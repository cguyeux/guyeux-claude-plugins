---
name: cv
description: >
  Le CV LaTeX de Christophe Guyeux (~/docs/cv/) : le lire pour rédiger, et le tenir à jour.
  Utiliser quand il faut extraire de la matière sourcée pour une demande de financement
  (ANR, ERC, Horizon, LabCom), une candidature, une lettre, une bio, une liste de
  publications ou un dossier d'encadrement ; ajouter un article de revue ou une
  communication qui vient d'être accepté, avec son ticket Publiweb et son PDF auteur ;
  rafraîchir h-index, i10-index, citations, nombre de publications et date du CV depuis
  Google Scholar ; ajouter un projet financé, un encadrement, une communication ; produire
  une version d'une page, de deux pages ou d'un paragraphe, en français ou en anglais, pour
  un destinataire précis ; recompiler et vérifier. Utiliser aussi sans le mot « CV » :
  « j'ai eu l'acceptation de cet article », « ajoute ce papier », « mets à jour mon
  h-index », « un CV court pour l'ANR », « une bio de dix lignes ».
---

# CV de C. Guyeux — lecture et mise à jour

Le CV vit dans `~/docs/cv/` : 39 pages, ~290 références, sources LaTeX modulaires.
Deux usages, qui n'ouvrent pas les mêmes fichiers.

| Ce que demande l'utilisateur | Aller à |
|---|---|
| Rédiger un dossier, une bio, une lettre, une liste de publications | § A, Lecture |
| « J'ai eu l'acceptation de… », ajouter un papier, déclarer sur Publiweb | § B, Ajouter une publication |
| h-index, i10, citations, nombre de publications, date du CV | § C, Chiffres |
| CV court, 1 page, 2 pages, paragraphe, version anglaise, dossier ciblé | § D, Variantes |
| Projet financé, thèse encadrée, jury, workshop, talk invité | § E, Sections manuelles |
| « Où en sont mes déclarations Publiweb », remettre le champ d'équerre | § B, étape 6 |
| Recompiler, « est-ce que ça compile encore » | § F, Compilation |

Scripts : `${CLAUDE_PLUGIN_ROOT}/skills/cv/scripts/`. Ils lisent et écrivent
`~/docs/cv/` directement ; les lancer depuis leur propre répertoire (ils
importent `bibtools.py`).

Règle qui vaut pour tout ce document : **ne jamais inventer un chiffre, une date,
un montant ou une référence.** Tout sort des fichiers sources ou d'une source
externe citée. Un champ introuvable reste vide et se demande à l'utilisateur.

---

## A. Lecture — extraire de la matière pour un document

Carte complète des fichiers, avec qui contient quoi :
`references/structure.md`. À lire avant de fouiller au hasard.

Marche à suivre : identifier le type de document, lire les blocs `cvDoc/`
correspondants, restituer le contenu **avec sa référence utilisable** (une
publication avec ses auteurs, revue, volume, année, DOI ; un projet avec son
programme, montant, dates et rôle ; une thèse avec le nom, le titre, l'année et
le rôle exact), en texte prêt à coller et non en commentaire sur le CV.

Pour une liste de publications sur un thème, ne pas parcourir les `.bib` à la
main :

```
python3 cv_select.py --focus "tubercul|mycobact|genom" --top 8
python3 cv_select.py --focus "wildfire|forest fire|firemen" --format count
```

`--format count` dit ce que chaque motif a ramené : un motif à zéro est mal
orthographié ou inutile, et un thème s'écrit rarement d'une seule façon dans
290 titres (chercher `firefight` rate les entrées qui n'écrivent que `firemen`).
Relire la sortie : le filtre attrape des faux amis (« emergence » évolutive pour
« emergency », « high-risk clone » bactérien pour « risk »).

Langue : les blocs sont bilingues, `\begin{francais}…\end{francais}` et
`\begin{anglais}…\end{anglais}`. Lire celui de la langue du document cible
plutôt que de traduire l'autre.

---

## B. Ajouter une publication acceptée

C'est le mode le plus long, parce que l'essentiel du travail est une enquête que
personne ne peut automatiser. Procédure complète et pièges :
`references/ajout-publication.md`. En résumé :

**1. Établir de quoi il s'agit.** Revue ou conférence ? Le CV les sépare
strictement : `~/docs/cv/references/journals.bib` (`@article`) et
`~/docs/cv/references/conferences.bib` (`@inproceedings`). Un poster, un talk invité, un
abstract de workshop ne passe par aucun des deux, mais par § E.

**2. Rassembler les métadonnées.** Dans cet ordre, en s'arrêtant dès que c'est
complet :

- le **mail d'acceptation** (Superhuman MCP) : titre, revue ou conférence, dates,
  parfois le DOI et le numéro de manuscrit. Chercher l'accusé de l'éditeur, puis
  le fil avec les co-auteurs ;
- **Crossref**, dès qu'un DOI existe : `python3 cv_add.py --doi 10.xxxx/yyyy`
  remplit titre, auteurs, revue, volume, pages, mois, éditeur et résumé ;
- le **dépôt du manuscrit** (`~/docs/publis/<titre>/`, `~/docs/codes/<projet>/article/`)
  pour le titre exact, la liste d'auteurs finale et le résumé, quand l'article
  n'est pas encore chez Crossref ;
- le **site de la conférence** pour l'acronyme, les dates, la ville, le pays, le
  rang CORE.

Ce qui reste introuvable se **demande à l'utilisateur**, groupé en une seule
question, jamais deviné. Un acronyme de conférence inventé se retrouve dans le
CV pendant des années.

**3. Écrire l'entrée.**

```
python3 cv_add.py --doi 10.3390/ai6100253                       # aperçu
python3 cv_add.py --json /tmp/papier.json --kind inproceedings  # depuis le mail
python3 cv_add.py --doi … --set "rank=CORE B" --write           # écriture
```

Le script forge la clé maison (initiales des auteurs + année sur deux chiffres +
`:ij` ou `:ip`), refuse un doublon de DOI ou de titre, échappe le LaTeX, et
**refuse d'écrire tant qu'un auteur manque à `affiliations.txt`** — c'est la
panne n° 1 : `all.py` s'arrête brutalement dessus. Les ajouter d'un coup :
`--add-affiliations "Nom, Prénom=Institution complète|Pays"`.

Laisser `publiweb = {False}` : c'est ce qui fait sortir le canevas du ticket.

**4. Régénérer, compiler, vérifier** : `./cv_build.sh` (§ F). La sortie se
termine par le canevas Publiweb de la publication.

**5. Déclarer sur Publiweb.** Le canevas imprimé par `all.py` **est** le corps du
ticket, à coller tel quel après « Bonjour, / Voici : ». Le ticket lui-même se
fait avec le skill **`femto-tickets`** (entité Publiweb, catégorie ACL pour une
revue, ACTI pour une conférence internationale).

Deux fichiers à joindre : le **PDF auteur** (manuscrit accepté compilé maison,
auteurs visibles, sans la mise en page de l'éditeur — c'est lui qui part sur
HAL) et le PDF éditeur quand il existe. Localiser le premier :

```
python3 find_manuscript.py "Titre de l'article"
```

Il balaie `~/docs/publis/` et `~/docs/codes/*/article/`, liste les PDF par date
avec le dépôt git d'origine, et signale ceux qui ressemblent à une version
éditeur ou anonymisée. Vérifier la date : un `main.pdf` antérieur à la dernière
révision n'est pas la version acceptée, il faut recompiler le dépôt. Si rien ne
sort, le manuscrit est peut-être resté sur Overleaf (skill `overleaf-bridge`) ou
en pièce jointe d'un mail.

**6. Refermer la boucle.** Ticket soumis → `publiweb = {En cours}` ; publication
effectivement ingérée → `publiweb = {True}`.

La bascule finale s'oublie systématiquement, et c'est sans gravité : elle se
rattrape en une commande, parce qu'une source externe fait foi. Une publication
n'apparaît sur la **page personnelle publique** que lorsque l'équipe Publiweb l'a
définitivement traitée :

```
python3 cv_publiweb_sync.py            # rapport
python3 cv_publiweb_sync.py --apply    # bascule en {True} ce qui y figure
```

`https://www.femto-st.fr/fr/personnel-femto/cguyeux`, accessible sans VPN. Le
script apparie par DOI puis par titre en tenant compte du type, et rend six
listes : à basculer, marquées `{En cours}` mais sans trace sur la page, en attente
de déclaration, présentes sur la page et absentes du CV, titres divergents entre
les deux, et **archivées mais jamais affichées**. `--apply` ne réécrit que le
champ `publiweb`.

Cette dernière rubrique est l'angle mort du dispositif. Le cycle réel a cinq
états, pas trois : ticket déposé, archivé par Karine DIEZ sous une référence
`ACTI-2026-000xx`, affichage demandé à Pierre-Alain Masson, affiché, ticket clos.
Le ticket se ferme tout seul quinze jours après l'archivage, que l'affichage ait
été demandé ou non : **un ticket clos ne vaut pas publication en ligne.** Ces
états intermédiaires ne vivent que dans les mails GLPI et se consignent dans
`~/docs/cv/publiweb_suivi.json`, que le script croise avec la page. Détail de la
procédure et du mail groupé à envoyer : `references/ajout-publication.md`.

**Ne jamais conclure d'un `publiweb = {False}` ou `{En cours}` qu'une publication
n'a pas été déclarée** : le champ est déclaratif et dérive. Seule la page
tranche. Passer `cv_publiweb_sync.py` avant d'ouvrir un ticket, sous peine d'en
créer un pour une publication déjà archivée.

---

## C. Chiffres : h-index, i10-index, citations, date

```
./cv_metrics.sh              # récupère, vérifie, recompile
./cv_metrics.sh --dry-run    # montre le diff sans recompiler
```

Le wrapper appelle `~/docs/cv/update_scholar.py` (profil Scholar `ebdFNfYAAAAJ`),
qui réécrit `cvDoc/researchPublicationsSummary.tex` : h-index, i10-index et
citations globales et sur cinq ans, nombre de publications recompté dans les deux
`.bib` et arrondi à la dizaine inférieure, et la date de mesure en français et en
anglais.

Deux dates cohabitent, ne pas les confondre : celle de l'en-tête du CV vient de
`\today` dans `cvDoc/titre.tex` et se met donc à jour **à chaque compilation**,
même sans nouvelle mesure ; celle des métriques est la date de l'interrogation de
Scholar. Un CV recompilé aujourd'hui affiche donc la date du jour en couverture
avec des chiffres pouvant dater de plusieurs mois. Lancer `cv_metrics.sh` avant
d'envoyer un CV à un comité, pour que les deux coïncident.

Trois choses que le wrapper ajoute et qu'il ne faut pas contourner : `uv run
--with scholarly` (le paquet n'est pas installé et `make scholar` échoue sinon en
`ModuleNotFoundError`) ; le refus d'un h-index nul ou en baisse, qui signale un
scraping bloqué par Scholar et non un résultat, avec restauration du fichier ; et
la recompilation, sans laquelle le PDF garde les anciens chiffres.

---

## D. Variantes : une page, deux pages, un paragraphe, une langue

Une variante est un `.tex` à la racine de `~/docs/cv/` qui réassemble les mêmes
blocs `cvDoc/` — c'est déjà le montage de `iuf.tex`, `deleg.tex`, `anr-h14.tex`.
Recettes détaillées et arbitrages : `references/variantes.md`.

```
python3 cv_variant.py list
python3 cv_variant.py new --name anr-sadiand --preset 2pages --lang fr \
                          --focus "tubercul|genom" --for "ANR AAPG 2027"
python3 cv_variant.py build --name anr-sadiand --lang fr --preset-pages 2
```

`build` **ne touche jamais `main.tex`** : il en dérive un fichier maître jetable,
compile, récupère le PDF, puis jette les auxiliaires à la corbeille. L'ancien
montage — commenter la ligne `\input{cv}`, compiler, restaurer — laissait le
dépôt dans un état faux à la moindre interruption.

Deux règles de fond :

- **ne jamais éditer un bloc `cvDoc/` pour un besoin propre à un dossier.** Ils
  sont partagés par `cv.tex`, `deleg.tex`, `iuf.tex` : le texte spécifique s'écrit
  dans le fichier variante ;
- **tenir la limite de pages en retirant des blocs, pas en réduisant la police.**
  `build --preset-pages N` avertit quand le compte est dépassé. `researchComm.tex`
  pèse trois pages à lui seul et est hors sujet dans la plupart des dossiers.

Pour un **paragraphe** (bio d'invité, présentation de partenaire, notice), pas de
LaTeX : rassembler les faits sourcés — métriques dans
`researchPublicationsSummary.tex`, domaines dans `researchArea.tex`, projets dans
`researchFundings.tex`, encadrements dans `supervisionPhD.tex`, publications via
`cv_select.py` — puis rédiger. Le texte partant à un tiers, appliquer les règles
de rédaction de l'utilisateur : pas de tiret cadratin, pas d'emoji, pas de gras
ni de Markdown ornemental, prose continue plutôt que listes, et signaler qu'il
est prêt à copier-coller (un seul paragraphe sans retour à la ligne interne).

---

## E. Sections écrites à la main

Publications de revue et de conférence mises à part, tout le reste du CV est du
LaTeX écrit directement : projets financés (`researchFundings.tex`), thèses
encadrées (`supervisionPhD.tex`), jurys et expertises (`evaluationPhD.tex`),
workshops, talks invités, posters, ouvrages, brevets, logiciels
(`publications.tex`). **Aucun passage par les `.bib`, ni `affiliations.txt`, ni
`all.py`** : seulement `pdflatex` deux fois.

Macros, emplacement exact et gabarits bilingues :
`references/sections-manuelles.md`.

---

## F. Compilation et vérification

```
./cv_build.sh              # contrôle, all.py, pdflatex ×2, lecture du log
./cv_build.sh --no-check   # sans le contrôle d'intégrité
python3 cv_check.py        # contrôle seul
```

`cv_build.sh` enchaîne le contrôle d'intégrité, la régénération des `.tex` depuis
les `.bib` (`MPLBACKEND=Agg python3 all.py`), deux passes de `pdflatex` (la
seconde résout les compteurs de publications), puis **lit le log** : séquences de
contrôle indéfinies, références non résolues, débordements de marge de plus de
20 pt, nombre de pages. Un `pdflatex` qui rend un code 0 ne prouve rien, le CV
compile même amputé d'une section.

`cv_check.py` est le garde-fou qui manquait à `all.py`, lequel meurt d'un `exit()`
au premier auteur inconnu après avoir déjà écrit des `.tex` à moitié. Il rend
d'un coup : auteurs absents d'`affiliations.txt` (en distinguant ceux qui
bloquent de ceux qui sont sans effet), accolades parasites qui coupent une entrée
en deux, clés dupliquées, DOI et titres en double, valeurs de `publiweb`
invalides, champs manquants pour le canevas Publiweb.

**Après toute modification du CV, recompiler et vérifier.** Un `.bib` corrigé
sans `all.py` ne change rien au PDF, et un `.tex` régénéré sans `pdflatex` non
plus.

---

## Ce qui a déjà mordu

- `all.py` testait la chaîne `"En cours"` **n'importe où dans l'entrée** au lieu
  du champ `publiweb`. Une entrée portant `dixCitations = {En cours}` passait pour
  déclarée et son canevas ne sortait jamais. Corrigé le 2026-09-06 (sauvegarde de
  l'ancienne version dans `~/docs/cv/archives/`). À noter : le seul cas concret
  trouvé (IMPROVE 2024) **était bel et bien déclaré** — vérification faite sur la
  page personnelle. Le bug faussait le signal, il n'avait pas fait perdre de
  déclaration. C'est la leçon générale : le champ `publiweb` ne prouve rien, la
  page personnelle si.
- Le champ `publiweb` avait dérivé : 130 entrées à `{En cours}`, dont 111
  effectivement archivées, faute de bascule finale. Réconcilié le 2026-09-06 avec
  `cv_publiweb_sync.py`. Relancer ce script périodiquement plutôt que d'espérer
  tenir le champ à jour à la main.
- Deux titres du CV étaient faux et l'ont montré à cette occasion :
  `gcbd19:ij` annonçait « **un**foldable self-avoiding walks » là où l'article
  publié dit « foldable » (sens inversé, vérifié chez Crossref sur son propre
  DOI), et `udgns23:ij` portait « MoS 2 » avec un espace parasite. Corrigés.
- Trois entrées de `~/docs/cv/references/conferences.bib` portaient une accolade parasite `}{URL},`
  qui les coupait en deux. `all.py` y survivait par accident, tout parseur correct
  non. Réparées le 2026-09-06 ; `cv_check.py` détecte le motif.
- `affiliations.txt` est consulté **verbatim** : un auteur écrit
  `Blanc, V\'{e}ronique` dans le `.bib` n'y sera jamais trouvé s'il y figure en
  `Blanc, Véronique`. Vérifier la forme exacte des deux côtés.
- Le CV n'est **pas** sous git. Aucune modification n'est annulable par `git
  checkout` : sauvegarder avant de toucher à un script, et ne jamais supprimer
  avec `rm` (utiliser `gio trash`).
