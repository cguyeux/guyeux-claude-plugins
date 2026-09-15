# Sources de la veille (`scripts/veille.py`)

La veille interroge des portails agrégateurs d'appels à projets pour répondre à une
question précise, avant même qu'un mail de financeur n'arrive : qu'est-ce qui est
ouvert ou à venir, avec quel sujet et quelle date limite ? Elle ne remplace jamais la
lecture du règlement (geste 1 du skill) : c'est un radar, pas une source de vérité.

## appelsprojetsrecherche.fr

Portail public agrégeant 128 organismes financeurs français (ANR, ADEME, ANRS MIE,
Inserm, INCa, fondations, régions, GIRCI...). Pas d'API publique documentée : le
site est une SPA Symfony qui interroge son propre backend en AJAX. Le contrat
ci-dessous a été retro-ingénié le 2026-09-14 en lisant le bundle JS
(`/build/app.*.js`) et le formulaire de recherche servi côté serveur ; il peut casser
si le site change de version. Si `veille.py search` échoue avec une erreur de forme
JSON, revenir ici avant de suspecter autre chose.

### Requête

```
POST https://www.appelsprojetsrecherche.fr/ajax/search-call-for-proposals?page=1&nbElementsPerPage=<N>
Content-Type: application/x-www-form-urlencoded
X-Requested-With: XMLHttpRequest
```

Corps (form-encodé, répétable pour les champs `[]`) :

| Champ | Valeurs | Rôle |
|---|---|---|
| `call_for_proposal_search[terms]` | texte libre | recherche plein texte, vide = tout |
| `call_for_proposal_search[sort]` | `publicationBeginDate-asc/desc`, `applyClosingDate-asc/desc`, `applyOpeningDate-asc/desc` | tri |
| `call_for_proposal_search[status][]` | `open`, `closed`, `upcoming` | répétable, défaut du site = tout |
| `call_for_proposal_search[partners][]` | nom exact de l'organisme (`ANR`, `ADEME`, ...) | répétable ; liste complète dans le HTML de `/` (dropdown "Partenaires") |
| `call_for_proposal_search[openToInternational]` | `1` | case à cocher |
| `call_for_proposal_search[openToCompanies]` | `1` | case à cocher |

Aucune authentification, aucun cookie requis : testé en `curl` nu. Le Cloudflare
Turnstile visible sur la page sert l'espace utilisateur connecté (dépôt de dossier),
pas la recherche publique.

### Réponse

JSON avec quatre clés utiles :

```json
{
  "call_for_proposals": "<fragment HTML des cartes résultats>",
  "pagination": {"page": 1, "nbElementsPerPage": 50, "nbPages": 1, "total": 28},
  "filters": "...", "actions": "...", "token": "..."
}
```

`call_for_proposals` n'est **pas du JSON structuré** : c'est le HTML que le site
injecte tel quel dans la page (comportement mesuré, pas une limite technique
contournable). `veille.py` découpe ce fragment sur le motif récurrent
`<div class="col px-0 px-md-4...">\n<div class="card-call-for-proposal` puis extrait
par carte :

| Champ | Motif HTML | Notes |
|---|---|---|
| titre | `<h3 class="card-title...">…</h3>` | |
| financeur | `<p class="text-primary...">…</p>` | un seul nom observé jusqu'ici, pas de liste multi-financeurs testée |
| sujet | `<div class="card-text fs-5">…<div class="card-footer` | texte intégral de la description, pas un résumé ; peut être long (plusieurs milliers de caractères) |
| lien détail | `href="/appel/..."` | relatif, à préfixer par `https://www.appelsprojetsrecherche.fr` |
| statut + échéance | `<span class="badge...">…</span>` dans le `card-footer` | voir ci-dessous |

**Le badge de clôture n'est fiable QUE pour `status=open`.** Dans ce cas il contient
une date complète (`16 nov. 2026, 13:00:00 UTC+1`), parsée par `_parse_french_date`.
Pour `upcoming`, le badge dit seulement « À venir » (aucune date, cohérent avec des
pré-annonces sans calendrier fixé). Pour `closed`, il dit « Appel clos » (aucune
date non plus dans la vue liste). Dans ces deux cas, la date exacte, si elle existe,
n'est disponible que sur la fiche détail (`/appel/<slug>`), non récupérée par la
veille pour rester légère — l'ouvrir au navigateur si l'échéance exacte d'un
« à venir » devient nécessaire.

### Limites connues

- Pas de pagination testée au-delà d'une seule requête à grand `nbElementsPerPage`
  (le total observé le 2026-09-14 était de 28 appels ouverts, largement sous
  `nbElementsPerPage=50` ; au-delà, `veille.py` ne boucle pas automatiquement sur
  les pages suivantes — augmenter `--limit` suffit tant que le total reste modeste).
- Le champ `terms` fait une recherche plein texte côté serveur dont l'algorithme
  n'est pas documenté (probablement un LIKE SQL ou un index full-text) : un mot-clé
  absent du résultat n'est pas une preuve d'absence du sujet dans le corpus, juste
  une absence de correspondance lexicale.
- `funder` peut être tronqué visuellement par le site (`text-truncate`) ; la valeur
  récupérée ici vient du HTML brut, pas du rendu, donc n'est pas coupée par CSS.

## Ajouter une autre source

`veille.py` expose un dictionnaire `SOURCES = {"cle": fonction}` où chaque fonction
a la signature `(terms, statuses, sort, partners, limit) -> list[CallHit]`. Ajouter un
portail = écrire une fonction de ce type, l'enregistrer dans `SOURCES`, et documenter
son contrat ici selon le même plan (requête, réponse, mapping de champs, limites).
Garder zéro dépendance externe (stdlib seule), comme le reste du skill.
