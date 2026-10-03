# Roots: website

Statische, drietalige site (nl / en / de) voor kwekerij Roots in IJsselmuiden.

- Teksten: `content.py` (alleen feiten van de familie)
- Opmaak en wortel-animatie: `static/css/site.css`, `static/js/roots.js`
- Uitvoer: `docs/` (wordt door GitHub Pages geserveerd)

## Bouwen

```bash
# GitHub Pages zonder eigen domein (https://aim-daniel.github.io/roots-kwekerij/), nog niet indexeren
python3 build.py

# Met eigen domein: zet de naam in docs/CNAME (bv. www.atroots.nl) en bouw gewoon opnieuw.
# build.py leest docs/CNAME en zet dan canonical, hreflang, sitemap en indexeren aan.
echo www.atroots.nl > docs/CNAME && python3 build.py
```

Pas docs/CNAME toevoegen als de DNS van het domein naar GitHub Pages wijst
(A-records 185.199.108.153 / .109.153 / .110.153 / .111.153, www als CNAME naar aim-daniel.github.io).

Daarna `docs/` committen en pushen naar `main`; GitHub Pages publiceert vanuit `main /docs`.
