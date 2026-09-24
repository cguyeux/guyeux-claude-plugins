# Provenance de `ntm-resources`

## Filiation locale

Le `SKILL.md` importé provenait du travail Claude Code du 17 août 2026. Avant durcissement, son
SHA-256 était `bd0dbcb56cbe3746c4fbad08867695a4492920e315a538e0b9533dbc4cfdc19b`. Le même contenu est
présent dans les objets Git `63e6c18be595037db4f86ce5027728d95a996edc` et
`2d6fe64edc5645a1c333ae90255d9026ba787b5a`.

Le lot CCX-09 du 21 août 2026 conserve ce canon, corrige ses affirmations temporelles, sépare les
droits des publications de ceux des bases et ajoute un registre structuré testable hors ligne. Le lien
`bio_redac/skills/ntm-resources` reste une projection relative vers ce canon. Aucun contenu, code,
modèle structural, profil de génotypage ou jeu de données provenant des trois services n'est embarqué.

## Sources primaires auditées le 2026-08-21

### NTM-DB

- Site officiel : <https://ngdc.cncb.ac.cn/ntmdb/>.
- Documentation : <https://ngdc.cncb.ac.cn/ntmdb/documentation>.
- Téléchargements : <https://ngdc.cncb.ac.cn/ntmdb/download>.
- Prépublication : <https://doi.org/10.1101/2025.07.22.666127>.
- Statut observé : le site, la documentation et les téléchargements répondaient en HTTPS. La page
  d'accueil date la mise en ligne de la version 1.0 au 1er juin 2023. La documentation indique que les
  données et résultats sont téléchargeables.
- Droits : le pied de page officiel affiche une licence Creative Commons Attribution 3.0 China
  Mainland. Cette mention n'efface pas les conditions et provenances des données amont, notamment
  GenBank, RefSeq, les publications et les soumissions tierces.

### Mabellini

- Site historique décrit par l'article : <https://www.mabellinidb.science/>.
- Article et description de l'API : <https://pmc.ncbi.nlm.nih.gov/articles/PMC6853642/> et
  <https://doi.org/10.1093/database/baz113>.
- Statut observé : les noms `mabellinidb.science` et `www.mabellinidb.science` ne se résolvaient pas
  depuis l'hôte d'audit. Cela constitue un échec de transport daté, pas une preuve d'arrêt définitif.
- Droits : l'article est disponible en libre accès, mais aucune licence propre au contenu de la base,
  à ses annotations ou à ses modèles n'a été établie pendant cet audit. La licence de l'article ne
  doit pas être transférée par inférence à ces objets.

### MAC-INMV-SSR

- Site historique : <http://mac-inmv.tours.inra.fr/>.
- Article officiel : <https://doi.org/10.1016/j.meegid.2019.104075>.
- Notice PubMed : <https://pubmed.ncbi.nlm.nih.gov/31634642/>.
- Statut observé : les contrôles HTTP et HTTPS n'étaient pas reproductibles, avec des échecs DNS
  répétés et un délai dépassé côté navigateur. Une réponse HTTP isolée n'a pas pu être reproduite.
- Droits : la page officielle de l'article Elsevier porte la mention `All rights reserved`. Aucune
  licence explicite de la base ou des profils soumis n'a été trouvée. L'accès web historique ne vaut
  donc pas autorisation de redistribution.

Le détail normalisé qui alimente les tests se trouve dans `references/resources.json`. Les statuts de
transport sont volontairement datés et doivent être réaudités avant une collecte automatisée.
