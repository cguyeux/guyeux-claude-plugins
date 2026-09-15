# Provenance

- Source scientifique : RDscan, Bespiatykh et al., mSphere 2021, doi `10.1128/mSphere.00535-21`.
- Depot amont RDscan : `https://github.com/dbespiatykh/RDscan`, commit lu localement dans le skill comme `f7e2d91`, licence MIT indiquee dans le skill.
- Code importe : `scripts/crosscheck_rdscan.py` est un comparateur local des sorties TBannotator et RDscan ; aucun code RDscan n'est embarque.

Garde-fou : RDscan est un recoupement independant, pas un remplacement automatique des appels TBannotator. Les desaccords doivent etre documentes souche par souche.
