# Provenance et portabilite

- Origine : inventaire operationnel local du groupe Guyeux, releve et teste le 17 aout 2026, revu et
  complete le 4 septembre 2026 a partir de la documentation officielle du mesocentre de calcul de
  Franche-Comte (`https://mesoservices.univ-fcomte.fr`, alias `mesodoc.univ-fcomte.fr`, et le wiki
  historique `mesowiki.univ-fcomte.fr` qui documente l'autre cluster, Lumiere/SGE), chaque valeur
  etant recoupee par une sonde directe des machines.
- Contenu redistribue : procedures SSH/Slurm, sonde en lecture et modeles de soumission ; aucun
  logiciel tiers ni jeu de donnees n'est embarque. Les chiffres de tarification et les adresses de
  contact proviennent des pages publiques du mesocentre.
- Dependances privees : les alias `mp`, `mh`, `ml`, `ms` et le rebond `bilbo` doivent etre
  declares dans la configuration SSH de l'utilisateur. Le VPN n'est PLUS une action humaine sur le
  poste de l'auteur (regle sudo NOPASSWD, cf. `scripts/vpn_ensure.sh`) ; ailleurs, le script se
  rabat proprement sur une demande a l'utilisateur.
- Fraicheur : capacites, quotas, QOS et modules sont des observations datees. La sonde doit preceder
  toute decision de placement. La documentation officielle elle-meme contient des valeurs perimees
  (RAM et walltime des noeuds GPU notamment) : en cas de divergence, `sinfo` et `scontrol` font foi.

## Garde-fou

Le skill ne contient ni mot de passe, ni cle SSH, ni jeton. Les secrets et la configuration VPN
restent hors depot. Une machine injoignable n'est pas une preuve d'absence de donnees.
