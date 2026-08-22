# Provenance et portabilite

- Origine : inventaire operationnel local du groupe Guyeux, releve et teste le 17 aout 2026.
- Contenu redistribue : procedures SSH/Slurm, sonde en lecture et modeles de soumission ; aucun logiciel tiers ni jeu de donnees n'est embarque.
- Dependances privees : les alias `mp`, `mh` et le rebond `bilbo` doivent etre declares dans la configuration SSH de l'utilisateur ; le VPN reste une action humaine.
- Fraicheur : capacites, quotas et modules sont des observations datees. La sonde doit preceder toute decision de placement.

## Garde-fou

Le skill ne contient ni mot de passe, ni cle SSH, ni jeton. Les secrets et la configuration VPN restent hors depot. Une machine injoignable n'est pas une preuve d'absence de donnees.
