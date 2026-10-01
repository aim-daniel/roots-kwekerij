# Roots: website

Statische, drietalige site (nl / en / de) voor kwekerij Roots in IJsselmuiden.

- Teksten: `content.py` (alleen feiten van de familie)
- Opmaak en wortel-animatie: `static/css/site.css`, `static/js/roots.js`
- Uitvoer: `docs/` (wordt door GitHub Pages geserveerd)

## Bouwen

```bash
# GitHub Pages zonder eigen domein (https://aim-daniel.github.io/roots-kwekerij/), nog niet indexeren
python3 build.py

# Met eigen domein (zet ook docs/CNAME): canonical, hreflang, sitemap en indexeren aan
ROOTS_SITE_URL=https://www.voorbeeld.nl python3 build.py
```

Daarna `docs/` committen en pushen naar `main`; GitHub Pages publiceert vanuit `main /docs`.
