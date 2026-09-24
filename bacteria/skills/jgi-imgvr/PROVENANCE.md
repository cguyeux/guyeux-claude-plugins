# Provenance

- Service source : JGI Genome Portal (`genome.jgi.doe.gov`) et IMG/VR
  (`img.jgi.doe.gov/cgi-bin/vr/`), DOE Joint Genome Institute.
- Code dans ce plugin : `scripts/jgi_imgvr_access.py` est un client original écrit pour
  `archeo_crispr` (test protospacer CRISPR de *M. canettii*, piste A1.5, 2026-08-11/12), promu
  skill partagé le 2026-09-22.
- Réutilisation confirmée avant promotion : `SpacerEgalVirus` (`clos_soumis/`) a réutilisé le
  mécanisme `scan` (dump nucléotidique IMG/VR, sur `mp`, 2026-08-24/26,
  `analyses/phase24_imgvr_scan_depouillement.py`) et a découvert le 2026-09-03 un second
  mécanisme d'authentification (cookie Keycloak) pour un téléchargement que le Bearer token ne
  couvrait pas — documenté dans SKILL.md § Authentification, non encapsulé dans le script.
- Régression serveur connue sur la sous-commande `blast` (formulaire web « Viral/Spacer BLAST ») :
  détectée par `archeo_crispr` le 2026-08-12, reproduite par `SpacerEgalVirus` le 2026-09-01,
  reconfirmée par `archeo_crispr` le 2026-09-22 (même trace exacte à six semaines d'intervalle) —
  cf. SKILL.md pour le détail et le smoke test de reconfirmation.
- Données : aucune donnée IMG/VR n'est embarquée dans ce plugin ; le script suppose un jeton de
  session valide (`~/.jgi_session_token`) et, pour `scan`/`extract`, un export déjà téléchargé.
