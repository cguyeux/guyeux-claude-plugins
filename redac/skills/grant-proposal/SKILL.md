---
name: grant-proposal
description: >
  Aide à la rédaction de demandes de financement de recherche adaptées aux
  formats français et européens : ANR (AAPG, LabCom, PRCI), Horizon Europe,
  Interreg, PHC (Hubert Curien), ARS, AMI, Région, UMLP/Sunergia. Ce skill
  connaît la structure exacte de chaque appel, les contraintes de formatage,
  et s'appuie sur les propositions précédentes de l'utilisateur comme modèles.
  Utiliser quand l'utilisateur rédige un projet de recherche, une demande de
  financement, un pré-projet, répond à un appel à projets, ou a besoin de
  reformuler/améliorer une section de proposition existante. Trigger phrases :
  "rédiger un projet ANR", "préparer une soumission Horizon", "écrire le
  pré-projet Interreg", "section impact pour le PHC", "budget du projet",
  "work packages", "appel à projets", "grant proposal", "write a proposal".
---

# Grant Proposal Writing Skill

Rédaction de propositions de recherche adaptées aux formats de financement français et européens. S'appuie sur les propositions précédentes dans `~/Documents/docs/projects/` comme modèles de référence.

## Interaction avec les autres skills

- **`/cv`** : extraire les données CV (encadrements, financements, h-index) à injecter dans la proposition
- **`/researcher`** : trouver le contenu thématique (publications, abstracts, réunions, notes) pour nourrir les sections scientifiques
- Ce skill gère la **structure, le format et la rédaction** de la proposition elle-même

## Étape 1 — Identifier le type de financement

Demander à l'utilisateur le type d'appel, puis appliquer le format correspondant :

| Financement | Format | Modèle existant |
|---|---|---|
| **ANR AAPG** | LaTeX, 20 pages max | `projects/ANR/AAPG2026/` |
| **ANR LabCom** | DOCX/XLSX | `projects/ANR/LabCom-ARS/` |
| **Horizon Europe** | LaTeX | `projects/Horizon/` |
| **Interreg France-Suisse** | DOCX/LaTeX (fiche pré-projet) | `projects/Interreg/2026/` |
| **PHC Maghreb/Toubkal** | Markdown → soumission en ligne | `projects/PHC/Maghreb 2026/` |
| **ARS** | Markdown + XLSX budget | `projects/ARS/projet_actuel_finance/` |
| **AMI** | Markdown (formulaire court) | `projects/AMI/Smart MI 2026/` |
| **Région BFC** | XLSX budget + MD résumé | `projects/Région/Urgences-BFC/` |
| **UMLP Sunergia** | LaTeX | `projects/UMLP/Sunergia_2026/` |

## Étape 2 — Appliquer la structure spécifique

### ANR AAPG (Appel à Projets Générique)

**Contraintes** : 20 pages max (personnel, Gantt, budget, biblio inclus). Calibri 11 / Carlito, interligne simple, marges 2 cm. Couleur titres : bleu ANR (RGB 68, 114, 148).

**Sections obligatoires** (numérotation romaine) :

I. **Qualité et ambition scientifique**
   - a. Objectifs et hypothèses de recherche
   - b. Positionnement par rapport à l'état de l'art
   - c. Méthodologie et gestion des risques
   - d. Positionnement par rapport aux enjeux de l'axe scientifique

II. **Organisation et réalisation du projet**
   - a. Partenariat (consortium, complémentarité)
   - b. Moyens mis en œuvre et demandés (par partenaire : personnel, équipement, fonctionnement)

III. **Impact et retombées du projet**

**Éléments obligatoires** :
- Tableau du personnel (partenaire, nom, statut, rôle, personne-mois)
- Diagramme de Gantt coloré avec jalons
- Tableau budgétaire avec justification scientifique par partenaire
- Bibliographie (hors limite de pages)

**Référence** : lire `projects/ANR/AAPG2026/` pour le template LaTeX et les exemples.

### Horizon Europe

**Structure** : Work Packages (WP1 = Coordination, WP2..N = R&D, dernier WP = Dissemination).

**Sections clés** :
- Vision & positionnement scientifique
- Alignement priorités européennes (ProtectEU, AI Act, etc.)
- Consortium (par pays, expertise complémentaire)
- Roadmap avec livrables et jalons
- Indicateurs d'impact (RCOI codes)

**Référence** : lire `projects/Horizon/main.tex` et `projects/Horizon/notes_horizon_europe.md`.

### Interreg France-Suisse VI-A

**Format** : Fiche pré-projet puis proposition complète.

**Sections fiche pré-projet** :
1. Partenariat (français + suisse, SIRET/TVA, contacts)
2. Présentation du projet (acronyme, priorité, objectif spécifique, résumé 10 lignes)
3. Descriptif détaillé (objectifs, plan de travail)
4. Work Packages (WP1 = Coordination, WP2..N = R&D, dernier = Dissemination)
5. Indicateurs Interreg (RCO 007, 014, 084, 087)

**Référence** : lire `projects/Interreg/2026/`.

### PHC (Programme Hubert Curien)

**Sections obligatoires** (numérotation 3 à 5, les sections 1-2 sont administratives) :

3. **Contexte et Historique** : objectifs, état de l'art, projets en cours, coopération existante, complémentarité des équipes, productions significatives
4. **Description** : description du projet, méthodologie, programme de travail et calendrier, moyens, infrastructures, rôle des jeunes chercheurs, questions de genre
5. **Perspectives** : résultats attendus, perspectives européennes/internationales, perspectives industrielles

**Spécificités** : co-tutelle de thèse obligatoire, mobilité (30% Sud-Sud min, 20% Nord-Sud min), budget orienté mobilité.

**Référence** : lire `projects/PHC/Maghreb 2026/`.

### ARS (Agence Régionale de Santé)

**Format léger** : projet + budget XLSX. Pas de template imposé.
- Description du projet et objectifs
- Équipe et répartition des rôles
- Budget par nature (RH ~80%, équipement, fonctionnement, missions)
- Calendrier pluriannuel

**Référence** : lire `projects/ARS/projet_actuel_finance/`.

### AMI (Appel à Manifestation d'Intérêt)

**Format court** (formulaire) :
1. Description en 5 lignes
2. Objectif principal (choix dans liste)
3. Technologie utilisée
4. État d'avancement (POC / Prototype / Prototype avancé / Marché)
5. Transformation opérationnelle
6. Indicateurs projetés (KPI)
7. Adaptabilité à d'autres contextes
8. Description du besoin + phases d'expérimentation (Phase 1/2/3 + livrables)
9. Durée estimée du POC
10. Coût prévisionnel (ventilé : Dev, Infra, Intégration, Tests, Doc)
11. Pré-requis techniques
12. 2 cas d'usage / références
13. Contacts et partenariats

**Référence** : lire `projects/AMI/Smart MI 2026/`.

### Région BFC

**Budget-first** : XLSX avec ventilation par nature (RH, Stage, EQT, ADE, FI, Missions, PE), pluriannuel, co-financement (Région + ANR + autres).

**Référence** : lire `projects/Région/Urgences-BFC/`.

### UMLP Sunergia

**Candidature réseau** (11 mois, budget coordination ~3k€) :
1. Participants (porteur + partenaires, tableau)
2. Présentation (titre, réseau, thématiques, dates, description synthétique)
3. Budget (missions uniquement)
4. Justification scientifique (objectifs, résultats attendus, dissémination)

**Référence** : lire `projects/UMLP/Sunergia_2026/`.

## Étape 3 — Rédiger section par section

### Processus pour chaque section

1. **Lire le modèle existant** correspondant dans `~/Documents/docs/projects/` pour s'imprégner du style et du niveau de détail attendu
2. **Extraire le contenu thématique** via le skill `/researcher` (publications avec abstracts, notes, CR de réunions récents sur le sujet)
3. **Extraire les données CV** via le skill `/cv` si la section le requiert (encadrements, financements passés, metrics)
4. **Rédiger** en respectant le format, les limites de pages, et le style académique français ou anglais selon le document
5. **Vérifier** la cohérence avec les autres sections déjà rédigées

### Conseils de rédaction par section type

**État de l'art / Positionnement** :
- Citer les publications de l'utilisateur (grep .bib pour les abstracts pertinents)
- Positionner par rapport à la littérature internationale
- Identifier clairement le verrou scientifique ("gap")

**Méthodologie** :
- Structurer en tâches ou WP selon le format
- Inclure gestion des risques (risque → mitigation → plan B)
- Être réaliste sur le calendrier

**Impact** :
- Distinguer impact scientifique (publications, outils) et sociétal (déploiement, partenaires)
- Utiliser les déploiements existants comme preuves (PredictOps SDIS, TBannotator, etc.)

**Budget** :
- Ventiler par partenaire ET par nature de dépense
- Justifier scientifiquement chaque poste (pas juste "1 ingénieur" mais "1 ingénieur pour développer le pipeline X")
- Vérifier la cohérence personne-mois / budget

## Étape 4 — Vérification finale

Checklist avant soumission :

- [ ] Toutes les sections obligatoires sont présentes
- [ ] Limite de pages respectée (ANR : 20 pages, etc.)
- [ ] Tableau du personnel complet (noms, rôles, personne-mois)
- [ ] Budget cohérent avec le plan de travail
- [ ] Gantt/calendrier cohérent avec les WP/tâches
- [ ] Bibliographie à jour (vérifier DOI)
- [ ] Formatage conforme (police, marges, couleurs)
- [ ] Langue cohérente (pas de mélange FR/EN involontaire)
- [ ] Acronyme du projet défini et utilisé partout
- [ ] CV du coordinateur prêt (2 pages, format requis)

## Notes importantes

- **Ne jamais inventer** de données, chiffres, ou citations. Toujours lire les sources.
- **Langue** : ANR et PHC en français ; Horizon et certains Interreg en anglais ; adapter selon l'appel.
- Les propositions dans `~/Documents/docs/projects/` sont des **modèles de référence**, pas des textes à copier. S'en inspirer pour le style et le niveau de détail.
- Pour les budgets complexes, proposer un tableau structuré et demander à l'utilisateur de valider les montants.
