# Presentation Beamer du bilan -- version integrale

Reference de `mtbc-bilan` : texte integral de la section 9.4. Squelette complet
des slides en quatre actes, dix regles de redaction, compilation, cas du mode
`--full`.

### 9.4 Generation de la presentation Beamer

Apres le PDF du bilan, generer automatiquement une presentation Beamer
qui synthetise le projet en slides. Cette presentation n'est **pas une
version comprimee du bilan** — c'est une visite guidee de l'etat actuel
des connaissances du projet, structuree en 4 actes (contexte, donnees
et methode, resultats, synthese), avec une logique de presentation
claire (pas un journal chronologique des sessions).

#### 9.4.1 Ecriture du fichier LaTeX

Ecrire `<projet>/bilans/YYYY-MM-DD_bilan_slides.tex` (pas un Markdown
converti — un fichier Beamer LaTeX natif). Le template Metropolis est
dans ~/docs/codes/claude_plugins/bio_pathogens/skills/mtbc-bilan/templates/bilan_slides.tex et fournit le
preambule, le theme, et les commandes MTBC (\mtb, \spdi, \lignee, \kb).

**Structure obligatoire des slides** (adapter au contenu reel du bilan) :

```latex
% ── ACTE 1 : CONTEXTE (3-4 slides) ──────────────────────────────
\section{Contexte et objectifs}

% Slide 1 : Pourquoi ce projet ?
\begin{frame}{[Titre : la question scientifique]}
  % La question fondatrice du projet, pas le nom de la lignee.
  % Ex: "Existe-t-il des sous-lignees non-decrites au sein de L4 ?"
  % Pas : "Projet L4.2_proto"
  %
  % Utiliser 3-4 bullets ou un schema TikZ simple.
  % Terminer par un keybox avec la question precise.
  \kb{Question : [question scientifique en une phrase]}
\end{frame}

% Slide 2 : Etat des connaissances
\begin{frame}{Ce que l'on savait avant}
  % Extraire de la section "Etat des connaissances avant ce projet"
  % du bilan. 4-5 points cles, chacun avec la reference (Coll 2014,
  % Napier 2020...). Pas de prose — bullets concis.
\end{frame}

% Slide 3 : Lacunes
\begin{frame}{Ce qui manquait}
  % Extraire de "Lacunes et questions ouvertes" du bilan.
  % 2-3 lacunes cles, formulees comme des questions.
  % Terminer par un keybox : "Ce projet vise a combler [lacune X]"
\end{frame}

% ── ACTE 2 : DONNEES ET METHODE (2-3 slides) ────────────────────
\section{Donn\'ees et m\'ethode}

% Slide 4 : Les donnees
\begin{frame}{Donn\'ees}
  % Nombre de souches, source (TBannotator, SRA), lignee(s),
  % distribution geographique si pertinente.
  % Utiliser un tableau compact ou un columns text+carte.
  % Toujours citer la taille de l'echantillon.
\end{frame}

% Slide 5 : Pipeline
\begin{frame}{Pipeline d'analyse}
  % Schema TikZ du pipeline (reprendre le diagramme du bilan si
  % present, ou en creer un simplifie).
  % Chaque etape = une boite avec outil + statut.
  % Max 6 etapes sur un slide.
\end{frame}

% ── ACTE 3 : RESULTATS (4-8 slides) ─────────────────────────────
\section{R\'esultats}

% Pour chaque decouverte majeure du bilan (section "Decouvertes
% majeures et leur signification"), creer 1 slide :
%
% - Titre = enonce de la decouverte (pas "Resultat 1")
% - Figure si disponible (columns figure+interpretation)
% - 2-3 bullets d'interpretation
% - Keybox avec le take-away
%
% Selectionner les 4-8 resultats les plus marquants.
% Ordre : logique narrative, pas chronologique.

% Slide type resultat avec figure :
%\begin{frame}{[Titre : enonce de la decouverte]}
%\begin{columns}[T,onlytextwidth]
%\begin{column}{0.55\textwidth}
%  \centering
%  \includegraphics[width=\linewidth,height=0.70\textheight,
%    keepaspectratio]{../article/figures/xxx.pdf}
%\end{column}
%\begin{column}{0.42\textwidth}
%  \begin{itemize}\setlength\itemsep{3pt}
%    \item Observation cle
%    \item Interpretation biologique
%    \item Mise en perspective
%  \end{itemize}
%  \kb{Take-home : [message en une phrase]}
%\end{column}
%\end{columns}
%\end{frame}

% Slide type resultat sans figure :
%\begin{frame}{[Titre : enonce de la decouverte]}
%  \begin{itemize}\setlength\itemsep{5pt}
%    \item ...
%  \end{itemize}
%  \kb{[message]}
%\end{frame}

% ── ACTE 4 : SYNTHESE ET PERSPECTIVES (3-4 slides) ──────────────
\section{Synth\`ese et perspectives}

% Slide synthese (LE slide le plus important)
\begin{frame}{Synth\`ese}
  % NE PAS repeter tous les resultats.
  % Presenter l'image integree : qu'est-ce que l'ensemble des
  % resultats nous dit sur la question fondatrice ?
  % Utiliser un schema TikZ, un diagramme, ou 3-4 bullets
  % synthetiques avec keybox finale.
  \kb{Message principal : [la reponse a la question fondatrice]}
\end{frame}

% Slide limites (bref, honnete)
\begin{frame}{Limites}
  % 3-4 bullets : biais echantillonnage, reference H37Rv,
  % couverture geographique... Pas d'auto-flagellation, juste
  % de la transparence.
\end{frame}

% Slide fragilite (obligatoire si des faits centraux sont volatile/fragile)
\begin{frame}{Faits a consolider}
  % Lister les 2-4 faits centraux marques `volatile`/`fragile` en
  % Phase 1bis, avec amplitude / hypothese critique en une ligne
  % et la piste de consolidation en une ligne.
  % Utiliser un encadre \fragilite{} sur le fait le plus important.
  % Si aucun fait fragile : supprimer ce slide.
\end{frame}

% Slide a faire maintenant
\begin{frame}{\`A faire maintenant}
  % Extraire les 3-5 intentions memorisees non honorees les plus
  % importantes (section "A faire maintenant" du bilan).
  % Chaque item = 1 bullet : intention + trace cahier (date) + ce qui
  % manque pour l'executer.
  % Si la liste est vide : le dire et le souligner comme un signe de
  % maturite du projet.
\end{frame}

% Slide perspectives
\begin{frame}{Perspectives}
  % Extraire les 3-5 pistes haute/moyenne priorite (NOUVELLES
  % directions, distinctes des intentions memorisees du slide
  % precedent).
  % Chaque piste = 1 bullet avec justification courte.
  % Si verdict "bouclee" : dire que le projet est termine et
  % mentionner les retombees attendues.
\end{frame}
```

**Regles de redaction des slides** :

1. **Narratif** : chaque slide doit avancer l'histoire. Si un slide
   n'avance pas la narration, le supprimer.
2. **Un message par slide** : si deux idees, deux slides.
3. **Figures d'abord** : si une figure existe dans `article/figures/`
   pour illustrer un resultat, l'utiliser. Le `\graphicspath` du
   template inclut deja `../article/figures/`, `../resultats/` et
   `./figures/`, donc indiquer juste le nom du fichier suffit. Generer
   aussi du materiel de novo (cartes schematiques, schemas mecanistiques,
   chronologies, arbres simplifies) quand aucune figure existante ne
   couvre le point pedagogique. Voir Phase 9.1ter pour les patterns TikZ
   types.
4. **Titres specifiques** : "28 marqueurs SNP exclusifs au proto-L4.2",
   pas "Resultats phylogenetiques".
5. **Max 6 bullets par slide**, max 10 mots par bullet.
6. **Keybox sur chaque slide de resultat** : le take-away en une phrase.
7. **Total** : 12-20 slides de contenu (hors titre et merci). Adapter
   a la richesse du projet — un projet avec 2 resultats = 12 slides,
   un projet riche = 20 slides.
8. **Pipeline en TikZ** : reprendre le diagramme du bilan s'il existe,
   sinon en creer un simplifie (max 6 etapes).
9. **References** : utiliser `\footnote{\tiny Coll et al., 2014}` pour
   les references cles, pas de bibliographie formelle.
10. **Encadres pedagogiques sur les slides** : utiliser les commandes
    `\notion{titre}{contenu}`, `\methode{titre}{contenu}`,
    `\nouveau{titre}{contenu}`, `\remarquable{titre}{contenu}` et
    `\fragilite{titre}{contenu}` (a ajouter au template, couleur
    rouge/orange). Sur les slides, les encadres sont courts (3-5 lignes
    max) -- les explications detaillees vont dans le PDF. Inserer un
    `\nouveau` sur le slide synthese pour resumer en une phrase ce qui
    est nouveau dans ce projet vs la litterature, un `\remarquable` sur
    le slide d'un resultat marquant pour expliciter son amplitude / sa
    precision / son caractere frappant, et un **`\fragilite` sur le
    slide "Faits a consolider"** (et eventuellement sur le slide d'un
    resultat dont la valeur exacte est volatile et qu'on veut quand
    meme presenter).

#### 9.4.2 Compilation

```bash
cd "<projet>/bilans/"
pdflatex -interaction=nonstopmode YYYY-MM-DD_bilan_slides.tex
pdflatex -interaction=nonstopmode YYYY-MM-DD_bilan_slides.tex
```

- Deux passes pour la table des matieres et la numerotation.
- Si la compilation echoue (package manquant, figure introuvable) :
  signaler l'erreur a l'utilisateur, ne pas bloquer le bilan.
  Produire le .tex quand meme.
- Verifier : `grep -c "^!" YYYY-MM-DD_bilan_slides.log` doit etre 0.

#### 9.4.3 Pour le mode `--full`

Pas de slides en mode `--full` — la presentation Beamer n'a de sens
que pour un projet individuel. En mode `--full`, ne generer que le
Markdown + PDF du bilan global.
