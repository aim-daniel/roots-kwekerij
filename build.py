#!/usr/bin/env python3
"""Bouwt de Roots-site in docs/ (statisch, klaar voor GitHub Pages of elke webhost).

Gebruik:
    python3 build.py                                          # GitHub Pages (aim-daniel.github.io/roots-kwekerij/): noindex
    ROOTS_SITE_URL=https://www.voorbeeld.nl python3 build.py  # live: canonical, hreflang, sitemap, indexeerbaar

Teksten staan in content.py, opmaak in static/css/site.css, de wortel in static/js/roots.js.
"""
import hashlib
import html
import json
import os
import re
import shutil

from PIL import Image, ImageDraw, ImageFilter

from content import COMPANY, IDS, LANG_NAMES, LANGS, OG_LOCALE, T

ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(ROOT, "static")
OUT = os.path.join(ROOT, "docs")
SITE_URL = os.environ.get("ROOTS_SITE_URL", "").rstrip("/")
INDEXABLE = bool(SITE_URL) and os.environ.get("ROOTS_NOINDEX") != "1"
# map waarin de site op de server staat (GitHub Pages zonder eigen domein: /roots-kwekerij/)
_bp = os.environ.get("ROOTS_BASE_PATH", "/" if SITE_URL else "/roots-kwekerij/").strip("/")
BASE_PATH = "/" + _bp + "/" if _bp else "/"
PAGES = ["home", "sempervivum", "perovskia", "hibiscus"]
YEAR = "2026"

e = html.escape


def nb(text):
    """Escape + de laatste twee woorden aan elkaar (vaste spatie): geen los woord op een eigen regel,
    ook in Safari 16.3 waar text-wrap:balance niet werkt."""
    i = text.rfind(" ")
    if i > 0:
        text = text[:i] + "\u00a0" + text[i + 1:]
    return e(text)


# ---------------------------------------------------------------- paden
def path(lang, page):
    """Pad vanaf de root, bv. '' / 'sempervivum/' / 'en/' / 'de/hibiscus/'."""
    pre = "" if lang == "nl" else lang + "/"
    return pre + ("" if page == "home" else page + "/")


def up(lang, page):
    """Relatief voorvoegsel van deze pagina naar de root."""
    return "../" * path(lang, page).count("/")


def link(lang, page, to_lang, to_page, anchor=""):
    target = path(to_lang, to_page)
    href = up(lang, page) + target
    if not href:
        href = "./"
    return href + (("#" + anchor) if anchor else "")


def absolute(p):
    return SITE_URL + "/" + p


# ---------------------------------------------------------------- beelden
IMG_SIZES = {}
NO_WEBP = set()  # beelden waarvan de webp niet kleiner is: alleen jpg


def prepare_images():
    src = os.path.join(STATIC, "img")
    dst = os.path.join(OUT, "img")
    os.makedirs(dst, exist_ok=True)
    for f in sorted(os.listdir(src)):
        if not f.lower().endswith(".jpg"):
            continue
        name = f[:-4]
        im = Image.open(os.path.join(src, f)).convert("RGB")
        IMG_SIZES[name] = im.size
        shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
        im.save(os.path.join(dst, name + ".webp"), "WEBP", quality=78, method=6)
        if os.path.getsize(os.path.join(dst, name + ".webp")) >= os.path.getsize(os.path.join(dst, f)):
            os.remove(os.path.join(dst, name + ".webp"))
            NO_WEBP.add(name)
        if im.size[0] > 560:
            h = round(im.size[1] * 560 / im.size[0])
            small = im.resize((560, h), Image.LANCZOS)
            small.save(os.path.join(dst, name + "-560.jpg"), quality=78, optimize=True, progressive=True)
            small.save(os.path.join(dst, name + "-560.webp"), "WEBP", quality=76, method=6)


def pic(b, name, alt, sizes, lazy=True):
    w, h = IMG_SIZES[name]
    big = w > 560
    webp = f'{b}img/{name}-560.webp 560w, {b}img/{name}.webp {w}w' if big else f'{b}img/{name}.webp {w}w'
    jpg = f'{b}img/{name}-560.jpg 560w, {b}img/{name}.jpg {w}w' if big else f'{b}img/{name}.jpg {w}w'
    load = ' loading="lazy" decoding="async"' if lazy else ""
    if name in NO_WEBP:
        return f'<img src="{b}img/{name}.jpg" srcset="{jpg}" sizes="{sizes}" alt="{e(alt)}" width="{w}" height="{h}"{load}>'
    return (f'<picture><source type="image/webp" srcset="{webp}" sizes="{sizes}">'
            f'<img src="{b}img/{name}.jpg" srcset="{jpg}" sizes="{sizes}" alt="{e(alt)}" width="{w}" height="{h}"{load}></picture>')


def make_icons_and_og():
    """Favicon (svg + png) en deelafbeelding, alleen gegenereerd uit eigen materiaal."""
    # icoontjes uit de rozet van het logo (static/src/rozet.png)
    ros = Image.open(os.path.join(STATIC, "src", "rozet.png")).convert("RGBA")
    for size, name in ((32, "favicon-32.png"), (192, "icon-192.png")):
        ros.resize((size, size), Image.LANCZOS).save(os.path.join(OUT, name), optimize=True)
    touch = Image.new("RGBA", (180, 180), (242, 236, 223, 255))
    r = ros.resize((140, 140), Image.LANCZOS)
    touch.paste(r, (20, 20), r)
    touch.convert("RGB").save(os.path.join(OUT, "apple-touch-icon.png"), optimize=True)

    # deelafbeelding 1200x630: eigen kasfoto (rood-gele Sempervivum boven een volle kas)
    src = os.path.join(ROOT, "bron", "kas-rozet-hand.jpg")
    if os.path.exists(src):
        im = Image.open(src).convert("RGB")
        W, H = im.size
        ch = round(W * 630 / 1200)
        y0 = max(0, min(H - ch, 980 - ch // 2))
        og = im.crop((0, y0, W, y0 + ch)).resize((1200, 630), Image.LANCZOS)
        og.save(os.path.join(STATIC, "og", "og.jpg"), quality=82, optimize=True, progressive=True)
    # bron/ staat niet in git: dan de eerder gemaakte versie gebruiken
    shutil.copy2(os.path.join(STATIC, "og", "og.jpg"), os.path.join(OUT, "img", "og.jpg"))


# ---------------------------------------------------------------- vaste stukjes
ICONS = {
    "stek": '<path d="M12 21v-7"/><path d="M12 14c-4.5 0-7-2.8-7-7.5 4.6 0 7 2.6 7 7.5z"/><path d="M12 12c0-4.3 2.2-7 6.5-7 0 4.2-2.3 7-6.5 7z"/><path d="M8.5 21h7"/>',
    "wortel": '<path d="M3 9.5h18"/><path d="M12 3.5v6"/><path d="M12 9.5c0 4-2.5 5.5-3.5 10"/><path d="M12 9.5c0 3.5 3 4.5 4 9"/><path d="M10.6 14.5c-1.8.2-3.4 1-4.6 2.6"/><path d="M14.2 13.6c1.6.1 2.9.9 3.8 2.2"/>',
    "pot": '<path d="M4 11h16"/><path d="M5.5 11l1.6 9h9.8l1.6-9"/><path d="M12 11c0-3 1.2-5.2 4.5-6.5"/><path d="M12 11c0-2.4-1.3-4.3-4.5-5.2"/>',
    "kas": '<path d="M3 20V10l4.5-5 4.5 5 4.5-5 4.5 5v10z"/><path d="M12 10v10"/><path d="M3 14.5h18"/>',
    "tray": '<rect x="3" y="12" width="18" height="7" rx="1.2"/><path d="M8 12v7M16 12v7"/><path d="M5.5 12c0-2 1-3.4 2.5-3.4S10.5 10 10.5 12"/><path d="M13.5 12c0-2 1-3.4 2.5-3.4s2.5 1.4 2.5 3.4"/>',
    "klok": '<circle cx="12" cy="12" r="8.5"/><path d="M12 12l4.2-2.8"/><path d="M12 4.6v1.6M19.4 12h-1.6M12 19.4v-1.6M4.6 12h1.6"/><circle cx="12" cy="12" r=".9" fill="currentColor"/>',
    "truck": '<path d="M2.5 6.5h11v10h-11z"/><path d="M13.5 9.5h4l3 3.4v3.6h-7"/><circle cx="6.5" cy="17.6" r="1.7"/><circle cx="17" cy="17.6" r="1.7"/>',
    "tel": '<path d="M5 4h3.5l1.8 4.6-2.3 1.4a11 11 0 005 5l1.4-2.3L19 14.5V18a2 2 0 01-2 2A15 15 0 013 6a2 2 0 012-2z"/>',
    "pen": '<path d="M4 20l1-4.2L16.2 4.6a2 2 0 012.8 0l.4.4a2 2 0 010 2.8L8.2 19z"/><path d="M14.5 6.3l3.2 3.2"/>',
}


def ico(name, sw="1.6"):
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{sw}" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


SOIL = ('<svg class="soil-edge" viewBox="0 -10 2400 74" preserveAspectRatio="xMidYMax slice"><path d="M0 64 L0 34 Q27 15 53 35 Q73 5 93 33 '
        'Q113 5 133 31 Q162 17 192 32 Q221 -3 251 32 Q275 2 299 37 Q333 8 366 37 Q385 -4 405 33 Q427 16 448 33 Q488 14 528 34 Q564 9 599 34 '
        'Q619 17 638 32 Q675 7 711 33 Q745 7 779 33 Q818 0 858 32 Q891 5 925 36 Q962 11 1000 37 Q1021 8 1042 36 Q1065 6 1087 31 Q1123 -2 1159 34 '
        'Q1200 10 1242 35 Q1276 3 1310 34 Q1351 -6 1391 34 Q1427 17 1463 35 Q1499 -8 1534 36 Q1560 9 1586 35 Q1604 7 1623 32 Q1644 17 1665 36 '
        'Q1687 12 1708 33 Q1750 17 1791 34 Q1824 -5 1857 36 Q1898 11 1940 33 Q1967 -5 1995 37 Q2017 14 2039 32 Q2063 6 2088 35 Q2113 19 2138 34 '
        'Q2166 4 2194 37 Q2230 5 2267 35 Q2303 17 2340 36 Q2379 -4 2418 36 L2400 64Z"/></svg>')

GROUND = f'<div class="ground" aria-hidden="true"><svg class="plant" id="plant" viewBox="-160 -84 320 94"></svg>{SOIL}</div>'

ARROW_L = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>'
ARROW_R = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg>'


# ---------------------------------------------------------------- head / header / footer
def asset_version():
    h = hashlib.sha1()
    for p in ("css/site.css", "js/roots.js"):
        h.update(open(os.path.join(STATIC, p), "rb").read())
    return h.hexdigest()[:8]


VER = None


def org_ld():
    org = {
        "@type": "Organization",
        "name": COMPANY["name"],
        "legalName": COMPANY["legal_name"],
        "email": COMPANY["email"],
        "telephone": COMPANY["phone_e164"],
        "foundingDate": COMPANY["founded"],
        "address": {"@type": "PostalAddress", "streetAddress": COMPANY["street"], "postalCode": COMPANY["postcode"],
                    "addressLocality": COMPANY["city"], "addressCountry": COMPANY["country"]},
        "identifier": {"@type": "PropertyValue", "propertyID": "KvK", "value": COMPANY["kvk"]},
        "knowsAbout": ["Sempervivum", "Perovskia", "Hibiscus"],
        "sameAs": [COMPANY["plantipp"]],
    }
    if SITE_URL:
        org["@id"] = SITE_URL + "/#org"
        org["url"] = SITE_URL + "/"
        org["logo"] = SITE_URL + "/icon-192.png"
    return org


def head(lang, page, title, desc, graph):
    t = T[lang]
    b = up(lang, page)
    out = [f'<!doctype html>\n<html lang="{lang}">\n<head>',
           '<meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">',
           f'<title>{e(title)}</title>',
           f'<meta name="description" content="{e(desc)}">']
    if not INDEXABLE:
        out.append('<meta name="robots" content="noindex">')
    if SITE_URL:
        out.append(f'<link rel="canonical" href="{absolute(path(lang, page))}">')
        for l in LANGS:
            out.append(f'<link rel="alternate" hreflang="{l}" href="{absolute(path(l, page))}">')
        out.append(f'<link rel="alternate" hreflang="x-default" href="{absolute(path("en", page))}">')
    out += ['<meta name="theme-color" content="#F2ECDF">',
            f'<link rel="icon" href="{b}favicon-32.png" sizes="32x32" type="image/png">',
            f'<link rel="icon" href="{b}icon-192.png" sizes="192x192" type="image/png">',
            f'<link rel="apple-touch-icon" href="{b}apple-touch-icon.png">',
            f'<link rel="preload" href="{b}fonts/hanken-grotesk-latin.woff2" as="font" type="font/woff2" crossorigin>',
            f'<link rel="stylesheet" href="{b}css/site.css?v={VER}">',
            '<meta property="og:type" content="website">',
            '<meta property="og:site_name" content="Roots">',
            f'<meta property="og:title" content="{e(title)}">',
            f'<meta property="og:description" content="{e(desc)}">',
            f'<meta property="og:locale" content="{OG_LOCALE[lang]}">']
    for l in LANGS:
        if l != lang:
            out.append(f'<meta property="og:locale:alternate" content="{OG_LOCALE[l]}">')
    og_img = (SITE_URL + "/img/og.jpg") if SITE_URL else (b + "img/og.jpg")
    if SITE_URL:
        out.append(f'<meta property="og:url" content="{absolute(path(lang, page))}">')
    out += [f'<meta property="og:image" content="{og_img}">',
            '<meta property="og:image:width" content="1200">',
            '<meta property="og:image:height" content="630">',
            '<meta name="twitter:card" content="summary_large_image">',
            '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False) + '</script>',
            '</head>']
    return "\n".join(out)


def logo_img(b, name, alt):
    return (f'<picture><source type="image/webp" srcset="{b}logo/{name}.webp">'
            f'<img class="logo" src="{b}logo/{name}.png" alt="{e(alt)}" width="117" height="24"></picture>')


def logo_imgs(b):
    # donker logo op de lichte kop, licht logo zodra de kop donker wordt (onder de grond)
    return (f'<span class="logo-d">{logo_img(b, "logo", "")}</span>'
            f'<span class="logo-l">{logo_img(b, "logo-licht", "")}</span>')


def header(lang, page):
    t = T[lang]
    ids = IDS[lang]
    home = lambda a: (("#" + a) if page == "home" else link(lang, page, lang, "home", a))
    nav = "".join(f'<a href="{home(ids[k])}">{e(t["nav"][k])}</a>' for k in ("process", "plants", "about", "buy"))
    langs = "".join(
        f'<a href="{link(lang, page, l, page)}" hreflang="{l}" lang="{l}" title="{LANG_NAMES[l]}"'
        + (' aria-current="page"' if l == lang else "") + f'>{l.upper()}</a>' for l in LANGS)
    contact = "#" + ids["contact"]
    brand_href = "#start" if page == "home" else link(lang, page, lang, "home")
    return f'''<a class="skip" href="#main">{e(t["skip"])}</a>
<header class="top scrolled" id="top">
  <div class="wrap top-in">
    <a class="brand" href="{brand_href}" aria-label="{e(t["brand_label"])}">{logo_imgs(up(lang, page))}</a>
    <nav class="nav" aria-label="{e(t["menu_label"])}">{nav}</nav>
    <div class="top-end">
      <nav class="langs" aria-label="{e(t["lang_label"])}">{langs}</nav>
      <a class="btn" href="{contact}">{e(t["contact_btn"])}</a>
    </div>
  </div>
</header>'''


def footer(lang, page):
    t = T[lang]
    c = COMPANY
    country = (", " + t["country"]) if t["country"] else ""
    plants = " · ".join(f'<a href="{link(lang, page, lang, p)}">{e(T[lang]["pages"][p]["h1"])}</a>' for p in PAGES[1:])
    return f'''<footer class="foot">
  <div class="wrap">
    <span class="brand">{logo_img(up(lang, page), "logo-licht", "@Roots")}</span>
    <ul>
      <li>{plants}</li>
      <li>{e(c["street"])}, {e(c["postcode"])} {e(c["city"])}{e(country)}</li>
      <li>{e(t["kvk"].format(kvk=c["kvk"]))}</li>
      <li>© {YEAR} Roots</li>
    </ul>
  </div>
</footer>
<script src="{up(lang, page)}js/roots.js?v={VER}" defer></script>
</body>
</html>
'''


def contact_section(lang):
    t = T[lang]
    c = COMPANY
    phone_label = c["phone_nl"] if lang == "nl" else c["phone_intl"]
    country = ("<br>" + e(t["country"])) if t["country"] else ""
    return f'''    <section class="contact sec" id="{IDS[lang]["contact"]}" aria-labelledby="h-contact">
      <div class="wrap">
        <h2 id="h-contact">{nb(t["contact_h2"])}</h2>
        <p class="lede">{nb(t["contact_lede"])}</p>
        <div class="hero-cta">
          <a class="btn btn-light" href="tel:{c["phone_e164"]}">{e(t["call"].format(phone=phone_label))}</a>
          <a class="btn btn-ghost" href="mailto:{c["email"]}">{e(t["mail"])}</a>
        </div>
        <dl class="nap">
          <div><dt>{e(t["nap_phone"])}</dt><dd>{e(phone_label)}</dd></div>
          <div><dt>{e(t["nap_mail"])}</dt><dd>{e(c["email"])}</dd></div>
          <div><dt>{e(t["nap_address"])}</dt><dd>{e(c["street"])}<br>{e(c["postcode"])} {e(c["city"])}{country}</dd></div>
        </dl>
      </div>
    </section>'''


def case(b, key, s, href=None, sizes="(max-width:640px) 84vw, (max-width:900px) 50vw, 380px", anchor_id=None):
    season = " season" if key in ("perovskia", "hibiscus") else ""
    img = pic(b, IMG[key], s["alt"], sizes)
    inner = f'{img}<figcaption><span class="tag{season}">{e(s["tag"])}</span><h3 id="t-{key}">{nb(s["name"])}</h3><p>{e(s["text"])}</p></figcaption>'
    idattr = f' id="{anchor_id}"' if anchor_id else ""
    if href:
        return f'<a class="case" href="{href}" aria-labelledby="t-{key}"{idattr}><figure style="margin:0;height:100%">{inner}</figure></a>'
    return f'<figure class="case"{idattr}>{inner}</figure>'


IMG = {"chick-charms": "chick-charms", "giants": "giants", "colorockz": "colorockz", "perovskia": "perovskia", "hibiscus": "hibiscus"}
CARD_TARGET = {"chick-charms": ("sempervivum", "chick-charms"), "giants": ("sempervivum", "giants"),
               "colorockz": ("sempervivum", "colorockz"), "perovskia": ("perovskia", ""), "hibiscus": ("hibiscus", "")}
STEP_ICONS = ["stek", "wortel", "pot", "kas", "tray", "klok", "truck"]
STEP_PHOTOS = [None, "stap-wortelen", "stap-oppotten", "stap-groeien", "stap-kar", "stap-verkoopklaar", "stap-onderweg"]
STEP_SIDES = ["l", "r", "l", "r", "l", "r", "l"]


# ---------------------------------------------------------------- homepage
def home(lang):
    t = T[lang]
    ids = IDS[lang]
    b = up(lang, "home")
    ticker_items = "".join(f"<li>{x}</li>" for x in ["Sempervivum", "Chick Charms®", "Colorockz®", "Giants", "Perovskia", "Hibiscus" if lang != "de" else "Hibiskus"])

    def step(i):
        s = t["steps"][i]
        chips = ('<span class="chips">' + "".join(f"<span>{e(c)}</span>" for c in s["chips"]) + "</span>") if s["chips"] else ""
        # een stap zonder (aangeleverde) foto toont alleen de zin
        photo = (f'<figure class="st-photo">{pic(b, STEP_PHOTOS[i], s["alt"], "260px")}</figure>') if STEP_PHOTOS[i] in IMG_SIZES else ""
        return f'''            <li class="step {STEP_SIDES[i]}">
              <details class="st">
                <summary><span class="st-main"><span class="ico">{ico(STEP_ICONS[i])}</span><span class="st-body"><h3>{nb(s["title"])}</h3>{chips}</span><i class="plus" aria-hidden="true"></i></span></summary>
                <div class="st-more"><p>{e(s["text"])}</p>{photo}</div>
              </details>
            </li>'''

    steps_in = "\n".join(step(i) for i in range(4))
    steps_out = "\n".join(step(i) for i in range(4, 7))
    cards = "\n          ".join(
        case(b, k, t["series"][k], href=link(lang, "home", lang, CARD_TARGET[k][0], CARD_TARGET[k][1]))
        for k in ["chick-charms", "giants", "colorockz", "perovskia", "hibiscus"])
    people = "".join(f'<div class="person"><h3>{e(p["name"])}</h3><p class="role">{e(p["role"])}</p><p>{e(p["text"])}</p></div>' for p in t["people"])
    buy_icons = ["klok", "tel", "pen"]
    buy = "\n".join(f'''        <div class="buy-card">
          <div class="ico">{ico(buy_icons[i])}</div>
          <h3>{nb(c["title"])}</h3>
          <p>{nb(c["text"])}</p>
        </div>''' for i, c in enumerate(t["buy_cards"]))
    d = t["dest"]
    faq = "\n".join(f'          <details><summary>{e(q)}<i aria-hidden="true"></i></summary><p>{e(a)}</p></details>' for q, a in t["faq"])

    graph = [org_ld(),
             {"@type": "WebSite", "name": "Roots", "inLanguage": lang, **({"url": absolute(path(lang, "home")), "publisher": {"@id": SITE_URL + "/#org"}} if SITE_URL else {})},
             {"@type": "FAQPage", "inLanguage": lang, "mainEntity": [
                 {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in t["faq"]]}]

    body = f'''<body>
{header(lang, "home")}

<main id="main">
  <section class="hero" id="start" aria-labelledby="h1">
    <div class="wrap">
      <p class="badge"><i></i>{e(t["badge"])}</p>
      <h1 id="h1">{nb(t["h1"])}</h1>
      <p class="lede">{nb(t["lede"])}</p>
      <div class="hero-cta">
        <a class="btn btn-dark" href="#{ids["plants"]}">{e(t["cta_plants"])} <span class="arr" aria-hidden="true">→</span></a>
        <a class="btn btn-line" href="#{ids["buy"]}">{e(t["cta_buy"])}</a>
      </div>
    </div>
    <div class="ticker" tabindex="0" role="group" aria-label="{e(t["ticker_label"] + ": " + t["ticker_pause"])}">
      <p class="ticker-label">{e(t["ticker_label"])}</p>
      <div class="track">
        <ul>{ticker_items}</ul>
        <ul aria-hidden="true">{ticker_items}</ul>
      </div>
    </div>
    {GROUND}
  </section>

  <div class="under" id="under">
    <svg class="rootsvg" id="rootsvg" aria-hidden="true"></svg>

    <section class="proc" id="{ids["process"]}" aria-labelledby="h-proc">
      <div class="wrap">
        <div class="sec-title">
          <h2 id="h-proc">{nb(t["proc_h2"])}</h2>
          <span class="scribble">{e(t["proc_scribble"])}</span>
          <p>{e(t["proc_intro"])}</p>
        </div>
        <div id="steps">
          <div class="group"><span>{e(t["group_in"])}</span></div>
          <ol class="steps">
{steps_in}
          </ol>
          <div class="group group-uit"><span>{e(t["group_out"])}</span></div>
          <ol class="steps uit" start="5">
{steps_out}
          </ol>
        </div>
      </div>
    </section>

    <section class="plants sec" id="{ids["plants"]}" aria-labelledby="h-plants">
      <div class="wrap sec-title">
        <h2 id="h-plants">{nb(t["plants_h2"])}</h2>
        <span class="scribble">{e(t["plants_scribble"])}</span>
        <p>{nb(t["plants_intro"])}</p>
      </div>
      <div class="carousel">
        <button class="car-btn prev" type="button" id="prev" aria-label="{e(t["prev"])}">{ARROW_L}</button>
        <div class="cases" id="cases" tabindex="0" role="region" aria-label="{e(t["cards_label"])}">
          {cards}
        </div>
        <button class="car-btn next" type="button" id="next" aria-label="{e(t["next"])}">{ARROW_R}</button>
      </div>
      <p class="credit">{e(t["credit"])}</p>
    </section>

    <section class="about sec" id="{ids["about"]}" aria-labelledby="h-about">
      <div class="wrap about-grid">
        <figure class="about-photo">{pic(b, "stefan-christol-rond", t["about_alt"], "(max-width:760px) 160px, 250px")}</figure>
        <div class="about-txt">
          <h2 id="h-about">{nb(t["about_h2"])}</h2>
          <span class="scribble">{e(t["about_scribble"])}</span>
          <p>{nb(t["about_p"])}</p>
          <details class="more">
            <summary>{e(t["about_more"])}<i class="plus" aria-hidden="true"></i></summary>
            <p>{e(t["about_story"])}</p>
            <div class="people">{people}</div>
            <p class="small">{e(t["about_small"])}</p>
          </details>
        </div>
      </div>
    </section>

    <section class="buy sec" id="{ids["buy"]}" aria-labelledby="h-buy">
      <div class="wrap sec-title">
        <h2 id="h-buy">{nb(t["buy_h2"])}</h2>
        <span class="scribble">{e(t["buy_scribble"])}</span>
      </div>
      <div class="wrap buy-grid">
{buy}
      </div>
      <div class="wrap dest">
        <p class="mono">{e(t["dest_label"])}</p>
        <ul class="compass">
          <li class="place n"><b>{e(d["n"][0])}</b><span>{e(d["n"][1])}</span></li>
          <li class="place w"><b>{e(d["w"][0])}</b><span>{e(d["w"][1])}</span></li>
          <li class="hub" aria-hidden="true"><i>{ico("stek", "1.8")}</i><small>IJsselmuiden</small></li>
          <li class="place e"><b>{e(d["e"][0])}</b><span>{e(d["e"][1])}</span></li>
          <li class="place s"><b>{e(d["s"][0])}</b><span>{e(d["s"][1])}</span></li>
        </ul>
      </div>
    </section>

    <section class="faq-sec sec" id="{ids["faq"]}" aria-labelledby="h-faq">
      <div class="wrap sec-title">
        <h2 id="h-faq">{nb(t["faq_h2"])}</h2>
      </div>
      <div class="wrap">
        <div class="faq">
{faq}
        </div>
      </div>
    </section>

{contact_section(lang)}
  </div>
</main>

'''
    return head(lang, "home", t["home_title"], t["home_desc"], graph) + "\n" + body + footer(lang, "home")


# ---------------------------------------------------------------- plantpagina's
def plant_page(lang, key):
    t = T[lang]
    p = t["pages"][key]
    b = up(lang, key)
    ids = IDS[lang]
    facts = "".join(f"<li>{e(f)}</li>" for f in p["facts"])
    phone_label = COMPANY["phone_nl"] if lang == "nl" else COMPANY["phone_intl"]

    if key == "sempervivum":
        cards = "\n          ".join(case(b, k, t["series"][k], anchor_id=k, sizes="(max-width:600px) 92vw, (max-width:900px) 46vw, 380px")
                                    for k in ["chick-charms", "giants", "colorockz"])
        gallery_imgs = ["stap-groeien", "stap-oppotten", "stap-verkoopklaar", "stap-kar"]
        gallery = "".join(f"<figure>{pic(b, n, p['gallery_alts'][i], '(max-width:900px) 46vw, 270px')}</figure>" for i, n in enumerate(gallery_imgs))
        sections = f'''    <section class="sec first" aria-labelledby="h-series">
      <div class="wrap sec-title">
        <h2 id="h-series">{nb(p["series_h2"])}</h2>
        <span class="scribble">{e(p["series_scribble"])}</span>
      </div>
      <div class="wrap cards">
          {cards}
      </div>
      <p class="credit">{e(t["credit"])}</p>
    </section>

    <section class="sec" aria-labelledby="h-gallery">
      <div class="wrap sec-title">
        <h2 id="h-gallery">{nb(t["gallery_h2"])}</h2>
        <span class="scribble">{e(t["gallery_scribble"])}</span>
      </div>
      <div class="wrap gallery">{gallery}</div>
    </section>'''
    else:
        s = t["series"][key]
        if key == "perovskia":
            own = (f'<figure class="case">{pic(b, "stefan-christol-rond", p["alts"][1], "(max-width:600px) 92vw, 400px")}'
                   f'<figcaption><span class="tag">Roots</span><h3>Stefan &amp; Christel</h3></figcaption></figure>')
            cards = case(b, key, s, sizes="(max-width:600px) 92vw, 400px") + "\n          " + own
            klass = "cards two"
        else:
            cards = case(b, key, s, sizes="(max-width:600px) 92vw, 460px")
            klass = "cards one"
        sections = f'''    <section class="sec first" aria-labelledby="h-photos">
      <div class="wrap sec-title">
        <h2 id="h-photos">{nb(p["photos_h2"])}</h2>
        <span class="scribble">{e(p["photos_scribble"])}</span>
      </div>
      <div class="wrap {klass}">
          {cards}
      </div>
      <p class="credit">{e(t["credit"])}</p>
      <p class="center"><a class="back" href="{link(lang, key, lang, "home", ids["plants"])}">{e(t["back_home"])}</a></p>
    </section>'''

    crumbs = {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": t["crumb_home"], **({"item": absolute(path(lang, "home"))} if SITE_URL else {})},
        {"@type": "ListItem", "position": 2, "name": p["h1"], **({"item": absolute(path(lang, key))} if SITE_URL else {})}]}
    graph = [org_ld(), crumbs]

    body = f'''<body>
{header(lang, key)}

<main id="main">
  <section class="hero page-hero" id="start" aria-labelledby="h1">
    <div class="wrap">
      <p class="badge"><i></i>{e(p["badge"])}</p>
      <h1 id="h1">{nb(p["h1"])}</h1>
      <p class="lede">{nb(p["lede"])}</p>
      <ul class="facts">{facts}</ul>
      <div class="hero-cta">
        <a class="btn btn-dark" href="{link(lang, key, lang, "home", ids["buy"])}">{e(t["page_cta_buy"])} <span class="arr" aria-hidden="true">→</span></a>
        <a class="btn btn-line" href="tel:{COMPANY["phone_e164"]}">{e(t["call"].format(phone=phone_label))}</a>
      </div>
    </div>
    {GROUND}
  </section>

  <div class="under" id="under">
    <svg class="rootsvg" id="rootsvg" aria-hidden="true"></svg>

{sections}

{contact_section(lang)}
  </div>
</main>

'''
    return head(lang, key, p["title"], p["desc"], graph) + "\n" + body + footer(lang, key)


# ---------------------------------------------------------------- 404, robots, sitemap
def not_found():
    t = T["nl"]
    en = T["en"]
    de = T["de"]
    graph = [org_ld()]
    h = head("nl", "home", t["nf_title"], t["nf_p"], graph).replace('<meta name="robots" content="noindex">', "")
    h = re.sub(r'<link rel="(?:canonical|alternate)"[^>]*>\n|<meta property="og:url"[^>]*>\n', "", h)
    # 404 wordt op elke diepte geserveerd: <base> laat de relatieve paden vanaf de site-map werken
    h = h.replace("<head>", f'<head>\n<base href="{BASE_PATH}">\n<meta name="robots" content="noindex">')
    return h + f'''
<body>
<main id="main">
  <section class="hero" aria-labelledby="h1" style="min-height:100vh;padding-bottom:80px">
    <div class="wrap">
      <p class="badge"><i></i>404</p>
      <h1 id="h1">{nb(t["nf_h1"])}</h1>
      <p class="lede">{e(t["nf_p"])}</p>
      <p class="lede" lang="en" style="margin-top:12px">{e(en["nf_h1"])} {e(en["nf_p"])}</p>
      <p class="lede" lang="de" style="margin-top:12px">{e(de["nf_h1"])} {e(de["nf_p"])}</p>
      <div class="hero-cta"><a class="btn btn-dark" href="./">{e(t["nf_btn"])}</a><a class="btn btn-line" href="en/" lang="en">{e(en["nf_btn"])}</a><a class="btn btn-line" href="de/" lang="de">{e(de["nf_btn"])}</a></div>
    </div>
  </section>
</main>
</body>
</html>
'''


def robots():
    lines = ["User-agent: *", "Allow: /"]
    if SITE_URL:
        lines.append(f"Sitemap: {SITE_URL}/sitemap.xml")
    return "\n".join(lines) + "\n"


def sitemap():
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for page in PAGES:
        for lang in LANGS:
            out.append("  <url>")
            out.append(f"    <loc>{absolute(path(lang, page))}</loc>")
            for l in LANGS:
                out.append(f'    <xhtml:link rel="alternate" hreflang="{l}" href="{absolute(path(l, page))}"/>')
            out.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{absolute(path("en", page))}"/>')
            out.append("  </url>")
    out.append("</urlset>")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- bouwen
def write(rel_path, text):
    full = os.path.join(OUT, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    global VER
    VER = asset_version()
    if os.path.isdir(OUT):
        keep = {"CNAME"}
        for f in os.listdir(OUT):
            if f in keep:
                continue
            p = os.path.join(OUT, f)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(OUT, exist_ok=True)
    for d in ("css", "js", "fonts", "logo"):
        shutil.copytree(os.path.join(STATIC, d), os.path.join(OUT, d), dirs_exist_ok=True)
    prepare_images()
    make_icons_and_og()
    for lang in LANGS:
        write(path(lang, "home") + "index.html", home(lang))
        for key in PAGES[1:]:
            write(path(lang, key) + "index.html", plant_page(lang, key))
    write("404.html", not_found())
    write("robots.txt", robots())
    if SITE_URL:
        write("sitemap.xml", sitemap())
    write(".nojekyll", "")
    n = sum(len(fs) for _, _, fs in os.walk(OUT))
    print(f"docs/ gebouwd: {n} bestanden, site-url: {SITE_URL or '(nog geen domein: noindex, relatieve links)'}")


if __name__ == "__main__":
    main()
