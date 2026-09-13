# La porte go/no-go

Un dossier ANR coûte plusieurs semaines. Un PHC en coûte une. Le pipeline de rédaction
prouve qu'un dossier est bien fait ; il ne dit jamais s'il fallait l'écrire. Cette porte
répond à la seule question qui précède : monte-t-on ce dossier, et sous quelle forme ?

Elle rend un verdict, jamais un menu. Quatre verdicts possibles.

**DÉPOSER.** On monte le dossier tel quel.

**RECADRER.** La matière existe mais le projet proposé n'est pas celui qui gagne. On monte
un dossier, sur une autre question ou un autre périmètre, explicité avant de commencer.

**REPORTER.** Le dossier est bon mais le millésime est mauvais : verrou d'éligibilité,
plafond d'implication déjà atteint, partenaire non consolidé, résultat préliminaire qui
arrive après la clôture. On vise le millésime suivant et on note pourquoi.

**RENONCER.** On ne dépose pas. Le savoir accumulé pendant l'instruction ne se perd pas
pour autant : il part aux registres du projet scientifique concerné, comme l'a fait la
candidature ANRS dont le criblage a été rapatrié dans `mtbc/lineage_markers_who_catalogue/`
avant même la décision.

## Les cinq axes, mesurés et non estimés

**1. Éligibilité, avant tout le reste.** Qui a le droit de porter ? Le registre répond par
`applications.py eligibility <call> --year <n>`, qui confronte les blockers du règlement
aux candidatures déjà enregistrées. Cet axe est éliminatoire : un dossier inéligible ne se
rattrape par aucune qualité. Trois cas vécus le prouvent, consignés dans `rejections.md` :
le laboratoire qui ne peut pas porter un Smart MI, la limite d'implication de l'ANR qui se
calcule sur l'année entière, la présidence de comité qui ferme un millésime.

**2. Adéquation au périmètre réel de l'appel, pas à son titre.** Le titre d'un appel est
large, ses priorités sont étroites. Lire la liste des priorités et dire laquelle porte le
projet, en une phrase. Si la réponse est « aucune, mais c'est éligible quand même », c'est
un fait à assumer, pas à masquer : à l'ANRS, le hors-priorité reste recevable mais n'est
qu'encouragé, ce qui n'est pas la même chose.

**3. Ce qui existe déjà, contre ce qui reste à faire.** Le levier le plus fort d'un dossier
n'est pas le plan de travail, c'est le « on ne part pas de zéro ». Recenser les
démonstrateurs, jeux de données, déploiements et publications mobilisables. Un dossier qui
n'a rien à montrer en amont demande à être financé sur une promesse, et se juge comme tel.

**4. Le consortium, et son état réel.** Les partenaires sont-ils engagés, ou seulement
pressentis ? Une lettre de soutien non demandée à J-15 est un risque, pas un détail. Les
dossiers du répertoire portent tous cette trace : partenaire libanais non identifié,
lettres d'engagement à demander, porteur officiel à confirmer.

**5. Le coût du dossier contre l'espérance de gain.** Nombre de jours de rédaction, pièces
à collecter, signatures à obtenir, face au montant et au taux de sélection. Sur un
dispositif à 3 000 euros, une trame courte suffit et l'argument porte sur la trajectoire
ouverte, pas sur le travail financé. Sur un AAPG, l'investissement ne se justifie que si
les quatre premiers axes sont solides.

## Deux règles

**Le coût déjà engagé n'entre dans aucun axe.** Trois jours passés à lire un règlement ne
sont pas une raison de déposer.

**Dans le doute, déposer.** L'asymétrie est voulue et vaut pour les dispositifs légers : un
dossier déposé et refusé coûte des jours et rapporte un retour d'instruction réutilisable ;
un dossier sain non déposé coûte le financement, et on ne le saura jamais. Elle ne vaut pas
contre l'axe 1 : un dossier inéligible ne rapporte pas même un retour.

## Trace

Le verdict s'écrit dans `applications.tsv` via `applications.py add` puis `set`, avec sa
date et son motif dans `notes`. Un go/no-go non tracé se rejoue à l'identique l'année
suivante.
