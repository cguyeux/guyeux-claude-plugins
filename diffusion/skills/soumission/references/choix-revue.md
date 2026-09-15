# Choisir la revue, et présenter le choix à l'auteur

La décision appartient à l'auteur. Le travail de l'assistant est de réduire cette
décision à une minute de lecture, en ayant fait toutes les vérifications en amont.

## Les cinq critères

### 1. Le format cadre, ou s'adapte à moindre effort

Comparer la longueur réelle du manuscrit, mesurée par section
(`preflight.py` la sort), à la limite de la revue. Trois cas seulement :

- **il tient** : rien à faire ;
- **il s'adapte** : le dépassement se résorbe en basculant vers les supplementary
  du matériel de moindre impact, sans toucher à l'argument. Un dépassement de moins
  d'un tiers est généralement de ce type ;
- **il ne rentre pas** : le manuscrit devrait perdre du fond. Écarter la revue,
  ou en faire une version courte assumée si le message le supporte.

Attention aux limites qui ne portent pas sur le corps : nombre de figures, nombre
de références, longueur du résumé. Un résumé de 251 mots pour une limite de 250 se
fait refuser au collage dans le formulaire, ce qui se découvre au pire moment.

### 2. Le scope cadre, vérifié sur les articles et non sur la page

La page « aims and scope » est un document de communication. Ce qui prédit un
desk-reject, c'est ce que la revue a réellement publié récemment.

**Test des trois articles.** Avant de proposer une revue, trouver dans ses douze
derniers mois au moins trois articles comparables au manuscrit : même nature de
travail, même type de preuve, même échelle. Si on n'en trouve aucun, la revue est
écartée quelle que soit la séduction de son scope affiché. Si on en trouve un ou
deux, la revue passe en second choix et la lettre d'accompagnement doit
explicitement faire le pont.

Ce test est le seul garde-fou qui aurait évité trois desk-rejects consécutifs en
août 2026 : trois manuscrits purement in silico envoyés à des revues dont le scope
réel demande de la biologie expérimentale, avec des lettres de rejet toutes
motivées par l'inadéquation éditoriale et non par la science.

**Comment chercher, car la méthode naïve donne le résultat inverse du vrai.**
Interroger une base par le nom de la méthode (« in silico », « computational »,
« docking ») ramène surtout les articles **mixtes**, ceux qui revendiquent la
méthode dans leur résumé parce qu'elle y est un argument à côté de la paillasse.
Les articles purement computationnels, eux, portent dans leur titre et leur résumé
l'objet biologique et non la méthode : ils échappent à cette requête. Une revue peut
donc paraître exiger de l'expérimental alors qu'elle publie régulièrement du pur
calcul. Vécu le 2026-08-25 sur Current Microbiology, écartée à tort sur une requête
par méthode, puis retenue après récolte du corpus complet.

La méthode qui tient : récolter le corpus des douze derniers mois de la revue,
puis lire les résumés pour trancher un par un s'il y a eu de la paillasse. Europe PMC
s'y prête mieux qu'une requête PubMed, parce qu'il rend les résumés en masse.

**Et lire les clauses d'exclusion, pas seulement le scope.** C'est là que se trouve
l'information décisive, et elle est souvent absente du résumé de scope. Trois
exemples relevés le même jour : Microbial Pathogenesis, « experimental validation is
a mandatory requirement for all submissions » ; Molecular Biology Reports, « the
journal does not publish purely bioinformatic / in silico papers » ; Journal of
Structural Biology, « purely computational approaches on drug binding and drug
development are outside the scope ». Aucune de ces phrases n'apparaît dans un scope
résumé, et chacune suffit à condamner une soumission.

Le cas le plus instructif est celui d'une revue dont le scope thématique paraît
idéal. Tuberculosis (Elsevier) est la revue TB par excellence, et elle exclut
séparément, par trois clauses distinctes, la réanalyse de données publiées sans
implication expérimentale des auteurs, la découverte de médicament in silico sans
travail expérimental, et la méta-analyse fondée sur des bases publiques. Zéro article
comparable sur 81 en douze mois. Un fit thématique parfait peut recouvrir une
exclusion méthodologique totale.

Corollaire pour les dossiers computationnels : une revue qui écrit « basic
experimental research » dans son scope rejettera un dossier sans paillasse, même
excellent. Chercher les revues qui publient de la génomique comparative, de la
bioinformatique ou de l'analyse de données comme contribution première.

### 3. Les niveaux s'alignent

Une revue trop facile gâche un bon travail ; une revue trop exigeante expose un
travail honnête à un refus de principe. Estimer le niveau du manuscrit avec la même
franchise qu'on estimerait celui d'un autre :

| Niveau | Ce qui le caractérise |
|---|---|
| `top` | déplace une question ouverte du domaine, ou ouvre un jeu de données ou une méthode que d'autres adopteront |
| `high` | résultat nouveau porté par plusieurs lignes de preuve indépendantes, généralisable au-delà du cas étudié |
| `solid` | résultat nouveau et bien établi, dont la portée reste le cas étudié ; un négatif rigoureux et complet entre ici |
| `modest` | caractérisation descriptive, extension incrémentale, réplication soignée |
| `low-barrier` | note, ressource, jeu de données, court rapport |

Deux questions qui recalibrent vite. Quelle est la phrase que ce papier ajoute à
la littérature, et cette phrase intéresse-t-elle quelqu'un qui ne travaille pas sur
cet objet précis ? Et : combien de lignes de preuve indépendantes soutiennent la
conclusion principale, une seule ou plusieurs ?

Viser la revue dont le `tier` égale celui du manuscrit, ou un cran au-dessus quand
le dossier est complet et le délai de décision court. Deux crans d'écart, dans un
sens ou dans l'autre, sont une erreur de calibrage.

### 4. Le coût est nul, sauf décision contraire de l'auteur

L'auteur publie sans budget de frais de publication. Filtrer sur `--free` par
défaut. Distinguer trois choses que les éditeurs entretiennent floues :

- **une voie gratuite existe** : titre hybride publié en voie abonnement, titre
  purement sur abonnement, ou vrai diamond. C'est ce que mesure `free_route`.
- **les frais annexes** : page charges, frais de figure couleur, frais de matériel
  supplémentaire, frais de soumission. Un titre « sans APC » peut en avoir. C'est
  ce que mesure `hidden_fees`, et c'est là que se cachent les mauvaises surprises.
- **la gratuité conditionnelle**, qui est le piège le plus coûteux des trois. Une
  revue peut être gratuite pour quelqu'un d'autre : Open Research Europe et Wellcome
  Open Research sont réservées aux bénéficiaires d'un financement Horizon ou Wellcome ;
  les titres Microbiology Society (Access Microbiology, Microbial Genomics, Microbiology,
  IJSEM) dépendent d'un accord Publish and Read de l'établissement ; Subscribe to Open
  chez ASM dépend d'une cible atteinte chaque année, page charges en sus. Ces trois cas
  se **vérifient pour cet auteur précis**, ils ne se supposent pas.

  Conséquence sur la base : une gratuité conditionnelle s'écrit `free_route=no` tant
  que la condition n'est pas établie. La mettre en note ne suffit pas, puisque c'est la
  colonne que lisent les filtres. Trois revues inéligibles sont remontées en tête d'un
  classement le 2026-08-25 faute de cette discipline, et `journals.py lint` signale
  désormais les fiches marquées gratuites dont les notes évoquent une condition.

Ne jamais sélectionner une option Open Access payante, ni accepter un transfert
vers un titre à frais, sans décision explicite de l'auteur pour ce manuscrit précis.

### 5. La variation est respectée

Trois manuscrits du même auteur arrivant en même temps chez le même éditeur, et a
fortiori dans la même revue, tombent souvent sur le même éditeur associé. L'effet
est réel et défavorable, indépendamment de la qualité de chaque dossier.

`submissions.py variety <cle>` rend le verdict :

- **REFUS** : plus d'un manuscrit déjà en évaluation dans cette revue, ou rejet de
  cette revue depuis moins de douze mois ;
- **ALERTE** : un manuscrit déjà en évaluation ici, ou deux et plus chez cet
  éditeur ;
- **OK** : rien à signaler.

Un REFUS n'interdit rien mécaniquement. Il oblige à dire à l'auteur pourquoi on
passerait outre, ce qui suffit presque toujours à faire préférer une autre cible.

## Le format de la proposition

Trois à quatre revues. Jamais une seule, qui ne laisse pas décider. Jamais une
liste de dix, qui reporte le travail sur l'auteur. Pour chacune, dans cet ordre :

1. **le nom et l'éditeur**, et la voie retenue (abonnement, diamond) ;
2. **pour** : ce qui plaide en sa faveur, en une ou deux phrases concrètes, dont
   le résultat du test des trois articles ;
3. **contre** : le vrai risque, nommé. S'il n'y en a pas, c'est qu'il n'a pas été
   cherché ;
4. **format** : ce qu'il faudrait changer au manuscrit, chiffré (« corps à
   ramener de 5 300 à 4 500 mots, deux tableaux vers les supplementary ») ;
5. **délai de première décision**, avec sa source, ou l'aveu qu'il est inconnu ;
6. **chances estimées**, avec ce qui fonde l'estimation.

Puis une recommandation assumée, en une phrase, et la décision passée à l'auteur
par une question explicite à l'utilisateur.

## Estimer les chances honnêtement

Un pourcentage inventé ne vaut rien. Une estimation se construit sur quatre
observables, dont trois sont vérifiables :

- **le test des trois articles** : trois articles comparables trouvés, ou moins.
  C'est le meilleur prédicteur du desk-reject, qui est le mode d'échec dominant ;
- **l'écart de niveau** entre le manuscrit et la revue, tel que défini plus haut ;
- **le taux d'acceptation** quand la revue le publie, et le fait qu'elle le publie
  ou non est déjà une information ;
- **l'historique** : ce que `rejections.md` dit d'une revue ou d'un éditeur qui a
  déjà répondu à un dossier de même nature.

Formuler en trois classes plutôt qu'en pourcentage : « bonnes » quand le fit est
démontré par des articles récents et que les niveaux s'alignent ; « moyennes »
quand le fit demande un pont argumentatif dans la lettre d'accompagnement ;
« faibles mais le dossier vaut la tentative » quand la revue est un cran au-dessus
et que le délai de décision est court, ce qui rend l'échec peu coûteux.

Ce dernier point est décisif et souvent oublié : le coût d'une tentative n'est pas
le rejet, c'est le **temps** perdu. Une revue qui desk-reject en cinq jours autorise
une tentative ambitieuse. Une revue qui met huit mois à dire non ne l'autorise pas,
même à chances égales. À fit égal, préférer toujours le délai le plus court, et
écarter d'emblée les revues sans métrique de délai publiée quand une alternative
la publie.

### Le piège du délai de première décision

Un chiffre bas est le plus trompeur de toute la base, parce qu'il se lit
spontanément à l'envers.

Les éditeurs publient plusieurs métriques sous des noms voisins. « Submission to
first decision » compte le délai jusqu'à **n'importe quelle** décision, desk-reject
inclus, et Nature Portfolio comme Wiley le définissent explicitement ainsi. Une revue
qui affiche deux jours n'est donc pas une revue qui relit vite : c'est une revue qui
refuse vite, et souvent. Elsevier lève l'ambiguïté en affichant les deux, et l'écart
est parlant : le même titre annonce trois jours pour la première décision et
trente-cinq jours pour la décision après relecture.

Ce qui intéresse un auteur, c'est la seconde. C'est pourquoi la base préfixe ses
valeurs par leur sémantique (`editorial`, `review`, `acceptance`) et pourquoi
`journals.py match` n'accorde de bonus qu'aux métriques `review`.

Un tri éditorial très rapide n'est pas pour autant une mauvaise nouvelle : il rend
l'échec peu coûteux, donc autorise une tentative un cran au-dessus. Mais il oblige à
faire le test des trois articles avec d'autant plus de sérieux, puisque c'est
précisément là que la revue tranchera.

Protocole complet d'établissement d'un délai, source par source, dans
`~/.agents/knowledge/journals/preprints_et_delais.md`, partie 2.

## Ne jamais perdre de matériel

Reformater vers une revue plus courte ne veut pas dire supprimer du travail. Le
matériel qui sort du corps va dans les supplementary, dans le dépôt de code, ou
dans le second papier, et l'état des découvertes garde trace de sa destination.
Un résultat qui disparaît d'un manuscrit sans être reversé quelque part est un
résultat perdu.
