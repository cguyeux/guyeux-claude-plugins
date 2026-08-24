# Affichage console : formats detailles -- version integrale

Reference de `mtbc-bilan` : texte integral des sections 9.5 et Epilogue.

### 9.5 Affichage console

Apres ecriture, afficher en console un **resume** : identite projet,
verdict argumente, etat consolide des connaissances en 3-5 phrases,
top 3 intentions memorisees non honorees ("A faire maintenant"), top 3
pistes prospectives avec justification.

**Fin du resume console : bilan obligatoire des trois fichiers
livres** sous forme d'un mini-tableau qui confirme leur generation :

```
Fichiers generes :
  Markdown  : <projet>/bilans/YYYY-MM-DD_bilan.md       (<taille>)
  PDF       : <projet>/bilans/YYYY-MM-DD_bilan.pdf      (<taille>)
  Beamer    : <projet>/bilans/YYYY-MM-DD_bilan_slides.pdf (<taille>)
```

Si l'un des trois fichiers manque (compilation echouee, par exemple),
la ligne correspondante affiche `[ECHEC]` suivi de la commande exacte
permettant a l'utilisateur de relancer la compilation. **Ne jamais
omettre une ligne** : si le PDF n'a pas pu etre genere, c'est une
information critique a faire remonter, pas un detail a passer sous
silence.

Voir section "Epilogue" pour le format detaille du resume scientifique.


---

## Epilogue -- Resume console

Apres ecriture du bilan, afficher un resume **consolide et oriente
action** (pas un tableau de metriques, pas un narratif iteratif) :

```
=== Bilan : <nom projet> ===

Bilan produit :
  Markdown : <chemin>                  (<taille>)   [OK]
  PDF      : <chemin>                  (<taille>)   [OK | ECHEC]
  Slides   : <chemin .pdf>             (<taille>)   [OK | ECHEC]

(Les trois fichiers sont OBLIGATOIRES. En cas d'ECHEC, afficher la
commande de relancement manuel immediatement sous la ligne.)

Etat consolide des connaissances (3-5 phrases) :
<Resumer ce que le projet SAIT aujourd'hui, par theme principal. Pas
"on a fait X puis Y" -- plutot "le projet a etabli que [fait
consolide], que [fait consolide], et a documente [mecanisme]." Donner
l'image stabilisee du savoir, pas le cheminement.>

Faits volatils ou fragiles a surveiller :
  - <fait> [volatile|fragile] -- <amplitude ou hypothese critique> ;
    consolidation : <piste si elle existe, sinon "pas de voie evidente">
  - <fait> [...] -- <...>
<Lister explicitement les 2-5 faits non-`etabli` les plus importants
du projet, surtout ceux qui apparaitront dans le manuscrit ou seraient
cites a une reunion. Si tous les faits centraux sont `etabli`, le dire :
"Aucun fait central marque volatile ou fragile.">

Verdict : <CLORE | A POURSUIVRE> (X/7 criteres, dont critere 7
"consolidation" bloquant)
<2 phrases justifiant le verdict.>

A faire maintenant (intentions memorisees non honorees) :
  1. <intention> (cahier YYYY-MM-DD) -- <ce qui manque pour l'executer>
  2. <intention> (cahier YYYY-MM-DD) -- <ce qui manque>
  3. <intention> (cahier YYYY-MM-DD) -- <ce qui manque>
<Si la liste est vide, le dire explicitement.>

Pistes prospectives (nouvelles directions deduites) :
  1. <titre> (score X.X) -- <justification en une phrase> → `/<skill>`
  2. <titre> (score X.X) -- <justification> → `/<skill>`
  3. <titre> (score X.X) -- <justification> → `/<skill>`

Connexion litterature : <1-2 phrases sur les lacunes exploitables
ou les resultats qui contredisent/confirment la litterature>
```

Si mode `--full` :

```
Bilan global produit : <chemin absolu>
  Projets scannes : N
  Prets a clore  : M
  Dormants       : P
  Top priorites cross-projets : <3 lignes>
```

Suggestions de prochaines etapes (si pertinentes) :
- `/cahier-de-labo update` si le bilan a revele une production de
  connaissance nouvelle.
- `/<skill prioritaire>` pour la premiere piste haute priorite.
- `/mtbc-bilan --full` si un seul projet vient d'etre traite, pour
  remettre en perspective.
