# Provenance

- Amont : `https://github.com/steineggerlab/foldseek`.
- Commit amont verifie : `f53fe627dfb1d5a36c02319f96d78474951c658b`.
- Licence amont : GPL-3.0.
- Code importe dans ce skill : aucun code Foldseek n'est embarque ; le skill documente une installation et une pratique d'usage local.

Installation reproductible recommandee :

```bash
git clone https://github.com/steineggerlab/foldseek.git
git -C foldseek checkout f53fe627dfb1d5a36c02319f96d78474951c658b
```

Garde-fou : le web server Foldseek est un service vivant distinct du depot source. Son etat doit etre reverifie au moment de l'usage si la session depend du service en ligne.
