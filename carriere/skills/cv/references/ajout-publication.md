# Ajouter une publication au CV

De l'annonce d'acceptation au ticket Publiweb clos. La partie mécanique est
scriptée ; la partie enquête ne l'est pas et c'est elle qui prend le temps.

## 0. Quelle famille ?

Le CV a deux familles de publications, qui s'ajoutent de façons sans rapport.

**Famille 1, générée.** Articles de revue `[J]` et communications avec actes
`[C]`. Source de vérité : `references/journals.bib` (`@article`) et
`references/conferences.bib` (`@inproceedings`). Rendu produit par `all.py`.
C'est l'objet de ce document.

**Famille 2, écrite à la main.** Workshops `[W]`, talks et communications sans
actes `[T]`, monographies `[M]`, chapitres `[CH]`, brevets `[P]`, logiciels `[S]`.
Source de vérité : directement `cvDoc/publications.tex`. Aucun `.bib`, aucun
`all.py`. Voir `sections-manuelles.md`.

Décision : un article de revue ou un proceedings à comité de lecture → famille 1.
Un poster, un abstract de workshop, une conférence invitée → famille 2. Un poster
publié dans des actes est un cas limite : il va en famille 1 avec
`poster = {True}`.

## 1. Enquête : rassembler les métadonnées

Dans cet ordre, en s'arrêtant dès que le compte y est.

### Les mails

Souvent la seule source au moment de l'acceptation, avant toute mise en ligne.
Chercher, via le MCP Superhuman :

- l'accusé de l'éditeur : sujet contenant `accept`, `decision`, le nom de la
  revue, ou le numéro de manuscrit. Il donne le titre définitif, la revue, la date
  d'acceptation, parfois le DOI réservé ;
- le fil avec les co-auteurs, pour la liste d'auteurs **finale** et son ordre :
  c'est ce qui bouge le plus jusqu'au dernier moment ;
- pour une conférence : la notification d'acceptation donne l'acronyme, les dates
  et le lieu ; le taux d'acceptation, quand il y figure, se met dans `note`.

Ne pas se fier au sujet du mail pour le titre : il est souvent tronqué ou
approximatif. Prendre le titre du corps du message ou du manuscrit.

### Crossref

Dès qu'un DOI existe, c'est la source la plus fiable et la plus rapide :

```
python3 cv_add.py --doi 10.3390/ai6100253
```

Remplit titre, auteurs (format `Nom, Prénom`), revue ou actes, volume, numéro,
pagination, mois, éditeur, résumé (le balisage JATS est retiré) et mots-clés
quand ils y sont. Sans DOI, `--title "Titre exact"` tente une recherche et rend
les candidats à départager.

Crossref ne connaît ni l'acronyme d'une conférence, ni sa ville, ni son rang
CORE : ces champs restent à remplir ailleurs.

### Le dépôt du manuscrit

`~/docs/publis/<titre>/`, parfois avec un sous-dossier `article/`, ou
`~/docs/codes/<projet>/article/`. Y prendre le titre exact, la liste d'auteurs,
le résumé et les mots-clés quand l'article n'est pas encore chez Crossref.
`find_manuscript.py "titre"` retrouve le dossier.

### Le site de la conférence

Acronyme officiel avec l'année (`DATA 2026`), intitulé complet, ville, pays,
jours exacts, éditeur des actes, URL — qui va dans `web`. Le rang CORE se
vérifie sur le portail CORE et se met dans `rank`.

## 2. Ce qui manque se demande

Toute information encore absente après ces quatre sources se demande à
l'utilisateur, **en une seule fois, groupée**. `cv_add.py` liste en fin de
rapport les champs vides indispensables au canevas Publiweb.

Ne jamais deviner : un acronyme, un rang CORE ou une pagination inventés
survivent des années dans le CV et ressortent dans chaque dossier.

## 3. Écrire l'entrée

```
# aperçu, rien n'est écrit
python3 cv_add.py --doi 10.xxxx/yyyy

# métadonnées rassemblées à la main, par exemple depuis un mail
python3 cv_add.py --json /tmp/papier.json --kind inproceedings

# compléter, corriger, puis écrire
python3 cv_add.py --doi 10.xxxx/yyyy --set "rank=CORE B" \
                  --set "acronym=DATA 2026" --write
```

Format du JSON : les noms de champs du dépôt, plus une clé `authors` acceptant
une liste de `"Nom, Prénom"`.

```json
{
  "kind": "inproceedings",
  "title": "…",
  "authors": ["Paudyal, Bibek", "Guyeux, Christophe"],
  "booktitle": "15th International Conference on …",
  "acronym": "DATA 2026",
  "city": "Porto", "country": "Portugal",
  "month": "July", "day": "12-14", "year": "2026",
  "abstract": "…", "keywords": "…", "doi": "", "web": "https://…"
}
```

Ce que le script garantit : clé conforme (initiales des noms + année sur deux
chiffres + `:ij` ou `:ip`, suffixe numérique en cas de collision), refus des
doublons de DOI et de titre, ordre des champs du `modele`, échappement LaTeX de
`& % # _`, `publiweb = {False}`.

Ce qu'il refuse : écrire quand un auteur manque à `affiliations.txt`. Les ajouter
d'abord, dans la même commande :

```
--add-affiliations "Nakache, Lise=Femto-ST Institute, UMR 6174 CNRS, Université Marie et Louis Pasteur|France"
```

L'insertion respecte le tri alphabétique du fichier. Attention à la forme exacte
du nom : la comparaison est verbatim, `Blanc, V\'{e}ronique` et `Blanc, Véronique`
sont deux personnes différentes pour `all.py`.

## 4. Régénérer et vérifier

```
./cv_build.sh
```

Contrôle d'intégrité, `all.py`, deux passes de `pdflatex`, lecture du log, puis
le canevas Publiweb des publications encore à déclarer. Vérifier que la nouvelle
entrée apparaît bien dans le PDF, au bon endroit chronologique.

## 5. Le ticket Publiweb

Le canevas imprimé par `all.py` **est** le corps du ticket. Le coller tel quel
après « Bonjour, / Voici : », sans le reconstruire.

Le ticket se dépose avec le skill **`femto-tickets`**, entité Publiweb. Catégorie
ACL pour un article de revue à comité de lecture, ACTI pour une conférence
internationale avec actes, ACTN pour une conférence nationale. Titre du ticket :
`Nouvelle entrée : <titre exact>`. Un ticket par publication.

### Les deux PDF

Publiweb attend deux fichiers distincts :

1. le **PDF auteur** : le manuscrit accepté compilé maison, auteurs visibles,
   sans la mise en page de l'éditeur. C'est lui qui sera déposé sur HAL et rendu
   accessible depuis les sites FEMTO-ST ;
2. le **PDF éditeur** : l'article tel que publié. Archivé, non diffusé, même en
   open access.

Une version anonymisée pour évaluation en double aveugle n'est **ni l'un ni
l'autre** : elle ne va pas sur HAL.

```
python3 find_manuscript.py "Titre de l'article"
```

Liste les PDF candidats par date, avec le dépôt git d'origine, et signale ceux
dont le nom trahit une version éditeur ou anonymisée. Contrôler la date : un
`main.pdf` antérieur à la dernière révision n'est pas la version acceptée, il faut
recompiler le dépôt. Si rien ne sort, le manuscrit est resté sur Overleaf (skill
`overleaf-bridge`) ou en pièce jointe d'un mail.

L'upload de fichier n'est pas automatisable : préparer le formulaire, puis
demander à l'utilisateur de sélectionner lui-même les fichiers, en les lui
nommant précisément.

## 6. Refermer la boucle, et la rattraper

| État | `publiweb` |
|---|---|
| à déclarer | `{False}` — fait sortir le canevas |
| ticket soumis, en attente | `{En cours}` |
| publication effectivement ingérée | `{True}` |

La dernière bascule s'oublie, toujours, parce que rien ne la déclenche : la
référence d'archivage arrive des semaines plus tard, dans un ticket qu'on ne
rouvre pas. Résultat mesuré en septembre 2026 : 130 entrées bloquées à
`{En cours}`, dont 111 en réalité archivées depuis longtemps.

Le champ est donc **déclaratif et non fiable**. La preuve d'ingestion est
externe : la page personnelle publique, où une publication n'apparaît que
lorsque l'équipe Publiweb l'a définitivement traitée.

    https://www.femto-st.fr/fr/personnel-femto/cguyeux

Accessible sans VPN. Chaque publication y figure dans un `<li class="<type>
y-<année>">` avec son BibTeX complet et un lien
`publiweb.femto-st.fr/tntnet/entries/<id>`.

```
python3 cv_publiweb_sync.py                    # rapport
python3 cv_publiweb_sync.py --apply            # bascule en {True} ce qui y figure
python3 cv_publiweb_sync.py --cache /tmp/p.html  # hors ligne
```

Cinq listes en sortie :

1. **à basculer** : sur la page, pas encore `{True}` dans le `.bib` ;
2. **sans trace** : `{En cours}` mais absentes de la page. Une publication de
   l'année en cours peut simplement être en traitement ; au-delà, la déclaration
   n'a pas abouti. `--stale-to-false` les repasse en `{False}` pour que leur
   canevas ressorte, à ne lancer qu'après examen ;
3. **en attente** : `{False}` et absentes de la page, état cohérent ;
4. **sur la page, absentes des `.bib`** : soit une publication déclarée à
   FEMTO-ST qui manque au CV, soit une entrée de famille 2 (workshop, ouvrage,
   logiciel), qui n'a rien à faire dans les `.bib` ;
5. **titres divergents** : même travail des deux côtés sous deux titres
   différents. Cause habituelle, un titre changé en révision et jamais reporté au
   CV. À corriger à la main après vérification : un fort recouvrement de
   vocabulaire ne prouve rien entre deux articles voisins du même groupe.

**Ne jamais conclure d'un `{False}` ou d'un `{En cours}` qu'une publication n'est
pas déclarée.** Passer ce script avant d'ouvrir un ticket, sous peine d'en créer
un pour une publication déjà archivée.

## 7. Le cycle réel a cinq états, pas trois

Reconstitué en septembre 2026 par dépouillement des fils GLPI. Le champ
`publiweb` n'en connaît que trois ; les deux états intermédiaires ne vivent que
dans les mails, et c'est là que les publications se perdent.

| # | État | Trace |
|---|---|---|
| 1 | ticket déposé | mail `[Publiweb #NNNNN] | DISC ] Nouveau ticket …` |
| 2 | **archivé** | mail `Nouveau suivi` : Karine DIEZ donne la référence `ACTI-2026-000xx` et dit ce qui manque |
| 3 | **affichage demandé** | transfert du mail de suivi à `pierre-alain.masson@femto-st.fr` |
| 4 | affiché | Pierre-Alain répond qu'il a coché l'affichage ; la publication paraît sur la page personnelle |
| 5 | ticket clos | automatique, une quinzaine de jours après l'étape 2 sans remarque |

**Le piège est entre 2 et 3.** Karine écrit « la demande d'affichage Web peut
être faite », puis ferme le ticket au bout de quinze jours, remarque ou pas. Si
le transfert à Pierre-Alain n'a pas eu lieu, la publication reste archivée,
invisible, et son ticket est clos : plus aucun signal nulle part. **Un ticket
clos ne vaut pas publication en ligne.** Cinq publications étaient dans cet état
en septembre 2026, dont trois archivées depuis juillet.

Le délai de prise en charge par le service est de un à deux mois : un ticket
déposé début juin a été traité le 21 juillet. Ne pas s'inquiéter avant.

### Le registre de suivi

`~/docs/cv/publiweb_suivi.json` porte ces états intermédiaires, un objet par
ticket : numéro, référence d'archivage, clé BibTeX, date, statut, ce qui reste en
attente, et `affichage_demande`. Il se remplit à la lecture des mails GLPI
(chercher `noreply-tickets@femto-st.fr`, ou le mot `Publiweb` dans le corps) et
se croise automatiquement avec la page personnelle :

```
python3 cv_publiweb_sync.py            # la rubrique 6 liste les archivées non affichées
```

### Demander l'affichage

Pierre-Alain Masson coche l'affichage web. Il traite plusieurs publications d'un
coup, donc **grouper la demande** plutôt que de transférer un mail par
publication : c'est le geste qui fait gagner le plus de temps sur toute la
chaîne. Le registre relu, un seul mail listant les références `ACTI-…` suffit.
Registre de langue : tutoiement, mails très courts des deux côtés.

Une fois sa réponse reçue, mettre `affichage_demande: true` dans le registre,
puis relancer `cv_publiweb_sync.py --apply` quelques jours plus tard : les
publications seront apparues sur la page et basculeront en `{True}`.

### Ce que le service attend du PDF auteur

Signalé par Karine DIEZ sur le ticket ICDAR 2026 : « le fichier auteur ne
comporte pas les noms des auteurs, cela risque de poser problème lors du dépôt
sur HAL ». Un PDF anonymisé pour l'évaluation en double aveugle **n'est pas** un
PDF auteur. Vérifier que les auteurs sont visibles avant de joindre le fichier.

## Pièges avérés

- **`all.py` s'arrête net** (`exit()`) au premier auteur absent
  d'`affiliations.txt`, après avoir déjà écrit une partie des `.tex`. Toujours
  passer `cv_check.py` avant, ou laisser `cv_build.sh` le faire.
- **Le test `"En cours"`** portait sur toute l'entrée et non sur le champ
  `publiweb` : une entrée avec `dixCitations = {En cours}` était exclue du canevas.
  Corrigé le 2026-09-06 ; si le canevas reste vide alors qu'une entrée est à
  `{False}`, c'est le premier endroit à regarder. Le cas trouvé était en réalité
  déjà déclaré : un canevas qui ressort n'est pas la preuve qu'il faut ouvrir un
  ticket, seule la page personnelle tranche.
- **Accolade parasite** `}{URL},` en début de ligne : elle ferme l'entrée trop
  tôt et rend tous les champs suivants invisibles. Trois cas trouvés et réparés
  en 2026-09 ; `cv_check.py` détecte le motif.
- **Version conférence puis version revue** du même travail : deux entrées
  légitimes, avec le même titre voire le même DOI. `cv_check.py` les signale comme
  doublons potentiels, ne pas les supprimer sans vérifier.
- **Les `.tex` de `references/` sont générés.** Une correction faite là est
  perdue au prochain `all.py` : corriger le `.bib`.
