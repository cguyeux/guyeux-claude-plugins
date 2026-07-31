# Ton et style du bilan -- version integrale

Reference de `mtbc-bilan`. Le SKILL.md ne garde que le resume ; le detail
complet des criteres redactionnels est ici. A lire avant la Phase 9
(redaction) quand le bilan doit etre ecrit avec soin.

## Ton et style (principes-cles)

Le bilan n'est **pas un inventaire comptable**, ni un journal de bord ; c'est
un **etat consolide des connaissances** du projet, accompagne d'un plan
d'action, qui aide le chercheur a prendre du recul et a savoir quoi faire
ensuite.

### Ce que le bilan doit etre

- **Narratif et continu** : le bilan se lit comme un texte scientifique
  reflechi, **en prose continue**, pas comme une fiche technique ni un
  rapport d'inventaire. Chaque section centrale (etat des connaissances,
  decouvertes majeures, paysage de la litterature) est composee de
  **paragraphes argumentes** qui s'enchainent : le lecteur doit pouvoir
  parcourir 3-5 paragraphes pour saisir un theme entier sans rencontrer
  de liste a puces, de tableau, ni de bloc structure "Fait / Methode /
  Consolidation". Les chiffres, methodes, et niveaux de consolidation
  s'integrent **dans la phrase** ("Le sous-clade proto-L4.2, identifie
  sur 412 souches reparties dans 23 pays via `phase3_subclade_marker.py`,
  est aujourd'hui consolide comme `etabli` apres deux reproductions
  independantes a un mois d'intervalle"). Les listes a puces sont
  reservees aux annexes (inventaire de scripts, faits a faire,
  references), pas au coeur du recit.
- **Consolide, pas chronologique** : la colonne vertebrale est *ce qui est
  su aujourd'hui*, organise par theme. Le cheminement iteratif n'apparait
  que dans une section "Apercu chronologique" courte (4-8 phrases).
  Quand deux entrees du cahier disent des choses differentes du meme fait,
  on garde la **derniere version**, eventuellement en notant en une phrase
  l'evolution si elle est instructive.
- **Pedagogue** : expliquer *pourquoi* un resultat est marquant, pas juste
  *qu'il* existe. "La decouverte de 57 marqueurs inverses dans L4.9 est
  remarquable car elle remet en question le postulat d'irreversibilite des
  SNP chez MTBC, un principe fondateur du barcode de Coll et al. (2014)."
- **Argumente, pas affirme** : chaque resultat est presente avec son
  contexte (ce que la litterature disait avant), sa portee (ce qu'il
  change dans la connaissance du domaine), et ses limites (consolidation
  partielle, hypotheses non testees). Une affirmation seche ("Le MRCA est
  de 1240 CE.") n'a pas sa place ; sa formulation narrative est
  obligatoire ("La datation moleculaire LSD2 place le MRCA de proto-L4.2
  vers 1240 CE, ce qui le situe **avant** les premiers contacts coloniaux
  europeens-americains -- un resultat contre-intuitif pour une sous-lignee
  initialement decrite en Europe occidentale. La valeur reste neanmoins
  `volatile` : BEAST tip-dating donne 1110 CE, et la datation par
  calibration fossile remonte a 1340 CE. Le pattern qualitatif est stable,
  mais le chiffre exact necessite une horloge moleculaire relaxee pour
  etre cite sans reserve.").
- **Trace de la maniere d'acquerir** : pour chaque connaissance consolidee,
  rappeler en une phrase comment elle a ete etablie (script, methode,
  donnees, reference). Une connaissance sans methode d'acquisition est une
  affirmation suspecte.
- **Ancre dans la litterature** : chaque decouverte majeure est mise en
  perspective avec ce que la litterature dit (ou ne dit pas) sur le sujet.
  Citer les references de `litterature_review/references.bib` quand elles
  existent, mentionner les lacunes quand rien n'a ete publie.
- **Interpretatif** : ne pas juste rapporter les faits mais les interpreter.
  Que signifie biologiquement tel resultat ? Quel mecanisme pourrait
  l'expliquer ? Quelles hypotheses soutient-il ou refute-t-il ?
- **Tourne vers l'action** : une section "A faire maintenant" recense
  explicitement les choses memorisees dans le cahier qui n'ont pas ete
  faites (analyses planifiees, verifications evoquees, hypotheses non
  testees, donnees mentionnees mais non integrees...). C'est la **valeur
  pratique** du bilan : ne pas laisser de fil pendant inapercu.
- **Autonome (standalone, sans heritage)** : chaque bilan est un
  document **complet en soi**. Il **n'evoque jamais** un bilan
  precedent et ne presuppose **jamais** qu'un lecteur ait deja vu une
  version anterieure. Un lecteur decouvrant le projet pour la
  premiere fois doit pouvoir tout comprendre. **Aucune des formules
  suivantes n'est admissible** : "comme dans le bilan precedent",
  "le bilan v2 reste valable", "depuis la derniere session de
  bilan", "rien de neuf cote X", "voir bilan du JJ/MM pour les
  details", "delta par rapport a v3", "synthese des changements".
  Si une connaissance reste vraie, on la **reformule entierement** ;
  on ne renvoie pas a sa version anterieure. Le bilan n'est pas un
  changelog, c'est un **etat des lieux exhaustif a date**.
- **Exhaustif sur le fond** : ne rien laisser de cote. Lire TOUT le cahier,
  TOUTE la litterature disponible, TOUS les resultats. Un bilan superficiel
  qui survole est inutile.
- **Pedagogiquement adapte au lecteur** : le destinataire principal est
  Christophe Guyeux, formation math pures + info de base. Tout concept de
  biologie evolutive, genetique des populations, ethno-linguistique,
  epidemiologie ou statistique inferentielle doit etre explique via des
  **encadres pedagogiques** (`notion`, `methode`, `originalite`,
  `remarquable`) inseres au fil du texte. Voir Phase 4.6 et 9.1bis. Avoir
  la main lourde sur les explications -- mieux vaut un encadre superflu
  qu'une notion laissee dans l'ombre.
- **Visuel** : un bilan dense en texte fatigue. Utiliser **cartes,
  schemas, chronologies, diagrammes** au fil du document chaque fois que
  cela aide la comprehension. Reutiliser le materiel de l'article
  (`article/figures/`) **et generer du materiel de novo** (TikZ, pgfplots)
  quand aucune figure existante ne couvre un point pedagogique. Voir
  Phase 9.1ter. Les bilans riches comportent typiquement 4 a 10 figures
  ou schemas, dont 2-4 generes specifiquement pour le bilan.

### Ce que le bilan ne doit PAS etre

- Une liste de bullet points avec des comptages ("12 figures, 8 scripts")
- Un tableau sans explication
- Une enumeration seche de pistes sans justification scientifique
- **Un journal narratif des sessions** ("le 12 mars on a lance X, puis le
  15 mars on a vu que Y, alors le 18 on a essaye Z"). Le cheminement
  iteratif ne doit apparaitre que dans la section "Apercu chronologique",
  resume en quelques phrases.
- Un resume telegraphique du cahier
- Un document ou chaque section tient en 3 lignes
- **Un document sans section "A faire maintenant"** : si le projet n'est
  pas encore boucle, le bilan doit explicitement dire ce qui reste a
  faire d'apres ce qui est inscrit dans le cahier.
- **Une mise a jour incrementale d'un bilan precedent**. Si un bilan
  anterieur existe dans `<projet>/bilans/`, il n'est ni lu, ni cite,
  ni "complete". Le nouveau bilan est ecrit de A a Z comme s'il
  s'agissait du premier, en consolidant l'integralite du cahier de
  labo et de la litterature. Les bilans anteriors sont des **archives
  datees**, conserves cote a cote mais sans hierarchie de version
  active : chacun reflete l'etat des connaissances a sa date
  d'ecriture, et le plus recent ne suppose pas la lecture des autres.

