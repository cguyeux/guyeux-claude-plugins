# Simulation de rejet éditorial — protocole

Le test central du skill. Il vaut par son indépendance : une instance qui connaît les
résultats du manuscrit lit le résumé mieux qu'un éditeur ne le lira jamais, et ne peut
donc pas voir le malentendu qu'on cherche.

## Ce que l'instance reçoit, et rien d'autre

Un éditeur en chef décide sur trois minutes de lecture. Le matériel transmis reproduit
exactement ce qu'il a sous les yeux :

1. le titre candidat ;
2. le résumé candidat, tel quel, sans le corps ;
3. les mots-clés ;
4. la lettre d'accompagnement, si elle existe déjà ;
5. les clauses d'exclusion de la revue, **relevées mot pour mot** du guide aux auteurs et de
   la page de scope, jamais résumées ;
6. le type d'article visé et sa limite de longueur ;
7. trois titres et résumés publiés par la revue dans les douze derniers mois, tirés du cache
   `corpus_fit.py` et choisis pour être les plus proches du manuscrit.

Ce qui n'est **jamais** transmis : le corps du manuscrit, les figures, les résultats, le
verdict de diffusion, le nom de l'auteur, l'historique du projet, l'avis de la session qui a
rédigé. Chacune de ces pièces rend l'éditeur simulé plus indulgent, ce qui est exactement
l'inverse du but.

## Consigne à donner

> Tu es l'éditeur en chef de <revue>. Voici les clauses de périmètre de ta revue, trois
> articles que tu as publiés cette année, et un manuscrit qu'on vient de te soumettre, dont
> tu ne lis que le titre, le résumé, les mots-clés et la lettre d'accompagnement.
>
> Décide : envoi en relecture, ou desk-reject. Réponds dans ce format exact :
>
> DÉCISION : RELECTURE | DESK-REJECT
> MOTIF : une phrase
> PHRASE EN CAUSE : la citation exacte du titre ou du résumé qui déclenche la décision, ou
>   « aucune » si la décision est positive
> CLAUSE HEURTÉE : la clause de périmètre concernée, citée, ou « aucune »
> CE QUE JE CROIS QUE CE PAPIER FAIT : deux phrases, dans tes mots
> CE QUE JE NE COMPRENDS PAS : ce qui reste flou après ces trois minutes
>
> N'invente rien sur le contenu du manuscrit : si une information te manque pour décider,
> c'est en soi un constat, écris-le. Ne cherche pas à être charitable.

## Lire le retour

Le champ le plus instructif n'est pas la décision : c'est **CE QUE JE CROIS QUE CE PAPIER
FAIT**. L'écart entre cette reformulation et ce que le manuscrit fait réellement est la
mesure directe du malentendu, et il est fréquent qu'il apparaisse alors même que la décision
est positive. Un éditeur qui envoie en relecture un papier qu'il a compris de travers le fait
tomber sur les mauvais relecteurs, ce qui coûte plus cher qu'un desk-reject rapide.

**CE QUE JE NE COMPRENDS PAS** pointe en général la phrase du résumé qui promet un objet sans
dire à quelle échelle ni sur quelles données. C'est le premier endroit à retoucher.

**Règle de lecture de ce champ, et elle est décisive.** Une incompréhension portant sur une
information que le manuscrit contient est un défaut de VITRINE, et vaut retouche due. Seule
une incompréhension portant sur une information réellement absente du manuscrit interroge le
fond, et relève alors de `/manuscript-review` ou de la porte 3bis, pas de cette passe.

Le premier rodage (2026-09-09) a produit les quatre incompréhensions d'un coup, toutes du
premier type : jeu de données de remplacement jamais dimensionné alors que tout l'argument
repose sur sa supériorité, effectif du clade incriminé non donné, article réexaminé non nommé,
et apport positif non énoncé au-delà de la réfutation. Aucune n'exigeait de toucher aux
Résultats ; toutes se réparaient dans le résumé.

L'instance sollicitée a formulé elle-même la limite structurelle du test : voyant la seule
vitrine, elle ne peut pas distinguer un manuscrit mince d'un manuscrit dense mal résumé. C'est
exact, et ce n'est pas un défaut à corriger : l'éditeur réel est dans la même position, et
c'est précisément ce que la passe cherche à mesurer. La règle de lecture ci-dessus est ce qui
transforme cette limite en information exploitable.

Une réponse évasive (« cela pourrait convenir », « selon les priorités éditoriales ») n'est pas
un retour : redemander une décision binaire. Si la deuxième tentative reste évasive, c'est en
soi un signal que le dossier ne se laisse pas trancher en trois minutes, donc un défaut de
cadrage à part entière.

## Quand simuler deux fois

- La décision revient positive alors que le temps 1 a mesuré des écarts francs : l'instance a
  probablement comblé les trous avec ce qu'elle savait du domaine.
- Après retouche : la simulation se rejoue sur la vitrine retouchée, et c'est ce second tour
  sans changement qui autorise le verdict ALIGNE.
- Quand deux titres candidats sont en balance : les faire juger séparément, jamais côte à côte,
  une comparaison transformant la question en préférence esthétique.

## Ce que la simulation ne prouve pas

Elle ne prouve pas qu'un manuscrit sera accepté, ni même qu'il passera le vrai desk. Elle
prouve seulement qu'un lecteur sans contexte, muni des clauses de la revue, comprend de quoi
il s'agit et ne trouve pas de motif de renvoi immédiat. C'est peu, et c'est exactement ce qui
manquait au dispositif.
