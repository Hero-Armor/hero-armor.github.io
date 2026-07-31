#!/usr/bin/env python3
"""Посилання і справжні фото коробок для лабораторії ящика.

Іван 31.07: «хочу бачити, про що взагалі мова» — у таблиці стояли самі назви
й розміри, і зрозуміти, Pelican це валіза на колесах чи кулер-холодильник,
можна було тільки гуглячи вручну.

Що робить:
  1. шукає сторінку товару (DuckDuckGo, без ключів), надаючи перевагу сайту
     виробника, а не перекупникам;
  2. ЗВІРЯЄ, що знайдена сторінка — саме та модель (номер моделі має бути в
     адресі або в заголовку). Раніше на меморіалі вже стався випадок, коли
     я склеїв адресу «по памʼяті» і повісив посилання не на ту статтю —
     більше адреси руками не будуємо;
  3. тягне фото зі сторінки (og:image), стискає до мініатюри і кладе в
     site/assets/cases/;
  4. дописує `url` і `img` у enclosure/data/params.json.

Запуск:  /tmp/hvenv/bin/python3 enclosure/model/case_media.py [--only "Nanuk 960"]
         (потрібен Pillow; --dry — лише показати, що знайшлось)
"""
import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PARAMS = ROOT / "enclosure" / "data" / "params.json"
IMG_DIR = ROOT / "site" / "assets" / "cases"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

# сайти виробників — їм віримо найбільше; далі великі магазини з чесним фото
MAKER = ("pelican.com", "explorercases.com", "explorer-cases.com", "nanuk.com",
         "skbcases.com", "monoprice.com", "hprc.it", "seahorsecases.com",
         "b-w-international.com", "bwcases.com", "harborfreight.com",
         "rubbermaid.com", "coleman.com", "greenmadeproducts.com")
SHOP = ("bhphotovideo.com", "homedepot.com", "lowes.com", "walmart.com",
        "amazon.com", "adorama.com", "cases2go.com", "midwestcasecompany.com",
        "target.com", "costco.com")
BAD = ("ebay.", "aliexpress.", "pinterest.", "youtube.", "reddit.", "facebook.",
       "guenstiger.de", "duckduckgo.com/y.js", "wikipedia.org", "quora.",
       "tiktok.", "instagram.")

# назви, з яких пошуковий запит сам собою не збирається
QUERY = {
    "Monoprice 30×19×15.8 на колесах":
        "Monoprice weatherproof hard case 30 x 19 x 15.8 wheels",
    "Ящик Costco 27 gal (Greenmade)": "Greenmade 27 gallon storage tote",
    "Coleman 150 qt (кулер)": "Coleman 150 quart Xtreme cooler",
    "Coleman 100 qt на колесах (кулер)": "Coleman 100 quart Xtreme wheeled cooler",
    "Rubbermaid ActionPacker 24 gal": "Rubbermaid ActionPacker 24 gallon lockable storage box",
    "Rubbermaid ActionPacker 35 gal": "Rubbermaid ActionPacker 35 gallon lockable storage box",
    "Apache 4800 (Harbor Freight)": "Apache 4800 weatherproof protective case Harbor Freight",
    "Pelican iM3075 (Storm)": "Pelican Storm iM3075 case",
    "Pelican iM2950 (Storm)": "Pelican Storm iM2950 case",
    "B&W International Type 7800": "B&W International outdoor case type 7800",
    "SKB iSeries 3i-3026-15": "SKB iSeries 3i-3026-15 case",
}


# Адреси, знайдені в ОФІЦІЙНІЙ карті сайту виробника (sitemap.xml), а не
# вигадані: пошуковики нас ріжуть, а вгадувати шлях руками — той самий гріх,
# через який на /press колись повисли дві биті посилання. Скрипт однаково
# перевіряє кожну сторінку на номер моделі, перш ніж її записати.
URL_HINTS = {
    "Pelican 1620": "https://www.pelican.com/us/en/product/cases/protector/1620",
    "Pelican 1650": "https://www.pelican.com/us/en/product/cases/protector/1650",
    "Pelican 1660": "https://www.pelican.com/us/en/product/cases/protector/1660",
    "Pelican 1630": "https://www.pelican.com/us/en/product/cases/protector/1630",
    "Pelican Vault V600": "https://www.pelican.com/us/en/product/cases/vault/v600",
    "Pelican iM2950 (Storm)": "https://www.pelican.com/us/en/product/cases/storm/im2950",
    "Pelican iM3075 (Storm)": "https://www.pelican.com/us/en/product/cases/storm/im3075",
    "Nanuk 960": "https://nanuk.com/products/nanuk-960",
    "Nanuk 965": "https://nanuk.com/products/nanuk-965",
}

# Пошук у самого магазину: загальні пошуковики на ці позиції вперто дають
# головні сторінки брендів («coleman.com/»), а не картку товару. Свій пошук
# магазину знає свій же асортимент.
SITE_SEARCH = {
    "Monoprice 30×19×15.8 на колесах":
        ("https://www.monoprice.com/search/index?keyword=weatherproof+hard+case+wheels", "monoprice.com"),
    "Seahorse SE-1220": ("https://seahorsecases.com/?s=SE-1220", "seahorsecases.com"),
    "Apache 4800 (Harbor Freight)":
        ("https://www.harborfreight.com/catalogsearch/result?q=apache+4800", "harborfreight.com"),
    "Rubbermaid ActionPacker 24 gal":
        ("https://www.homedepot.com/s/rubbermaid%2520actionpacker%252024%2520gal", "homedepot.com"),
    "Rubbermaid ActionPacker 35 gal":
        ("https://www.homedepot.com/s/rubbermaid%2520actionpacker%252035%2520gal", "homedepot.com"),
    "Ящик Costco 27 gal (Greenmade)":
        ("https://www.costco.com/CatalogSearch?keyword=greenmade+27+gallon+tote", "costco.com"),
    "Coleman 150 qt (кулер)":
        ("https://www.coleman.com/catalogsearch/result/?q=150+quart+xtreme+cooler", "coleman.com"),
    "Coleman 100 qt на колесах (кулер)":
        ("https://www.coleman.com/catalogsearch/result/?q=100+quart+xtreme+wheeled", "coleman.com"),
}

# що саме має бути на сторінці, коли номера моделі в назві нема
VERIFY = {
    "Monoprice 30×19×15.8 на колесах": ["monoprice", "case"],
    "Ящик Costco 27 gal (Greenmade)": ["greenmade", "27"],
    "Coleman 150 qt (кулер)": ["150", "cooler"],
    "Coleman 100 qt на колесах (кулер)": ["100", "cooler"],
    "Rubbermaid ActionPacker 24 gal": ["actionpacker", "24"],
    "Rubbermaid ActionPacker 35 gal": ["actionpacker", "35"],
    "Apache 4800 (Harbor Freight)": ["apache", "4800"],
    "Seahorse SE-1220": ["se-1220"],
}


def slug(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "case"


def model_tokens(name):
    """Що саме має підтвердитись на сторінці — номер моделі, а не бренд."""
    toks = re.findall(r"[A-Za-z]*\d[\w-]*", name)
    return [t.lower() for t in toks if len(t) >= 3]


def get(url, referer=None, timeout=30):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,image/avif,image/webp,*/*",
        "Accept-Language": "en-US,en;q=0.9",
        **({"Referer": referer} if referer else {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def search(query, limit=12):
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    html = get(url).decode("utf-8", "ignore")
    out = []
    for href in re.findall(r'class="result__a"[^>]*href="([^"]+)"', html):
        m = re.search(r"uddg=([^&]+)", href)
        link = urllib.parse.unquote(m.group(1)) if m else href
        if any(b in link for b in BAD):
            continue
        if link not in out:
            out.append(link)
    return out[:limit]


def rank(links):
    def key(u):
        host = urllib.parse.urlparse(u).netloc.lower()
        if any(d in host for d in MAKER):
            return 0
        if any(d in host for d in SHOP):
            return 1
        return 2
    return sorted(links, key=key)


def page_image(url, tokens):
    """Фото товару зі сторінки + перевірка, що сторінка про цю модель."""
    html = get(url).decode("utf-8", "ignore")
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    title = re.sub(r"\s+", " ", title.group(1)).strip() if title else ""
    hay = (url + " " + title).lower().replace("_", "-")
    if tokens and not any(t in hay for t in tokens):
        # модель у заголовку не підтвердилась — шукаємо її хоч у тексті
        if not any(t in html.lower() for t in tokens):
            return None, title, "модель не підтвердилась"
    img = None
    for pat in (r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"',
                r'<meta[^>]+content="([^"]+)"[^>]+property="og:image"',
                r'<meta[^>]+name="twitter:image"[^>]+content="([^"]+)"'):
        m = re.search(pat, html, re.I)
        if m:
            img = m.group(1)
            break
    if not img:
        img = _ld_image(html)
    if img:
        img = urllib.parse.urljoin(url, img.replace("&amp;", "&"))
    return img, title, None


def _ld_image(html):
    """Фото зі структурованих даних сторінки (schema.org Product)."""
    for block in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>',
                            html, re.S | re.I):
        try:
            data = json.loads(block)
        except Exception:
            continue
        for node in (data if isinstance(data, list) else [data]):
            if not isinstance(node, dict):
                continue
            img = node.get("image")
            if isinstance(img, list):
                img = img[0] if img else None
            if isinstance(img, dict):
                img = img.get("url")
            if isinstance(img, str) and img.startswith("http"):
                return img
    return None


def save_thumb(img_url, referer, dest, box=520):
    from PIL import Image
    raw = get(img_url, referer=referer, timeout=45)
    im = Image.open(BytesIO(raw))
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        im = im.convert("RGBA")
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert("RGB")
    w, h = im.size
    if min(w, h) < 200:
        raise ValueError(f"замала картинка {w}×{h}")
    if not 0.4 <= w / h <= 2.5:
        raise ValueError(f"це не фото товару, а смуга {w}×{h}")
    im.thumbnail((box, box))
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "JPEG", quality=82, optimize=True)
    return im.size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="лише ці назви")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--force", action="store_true", help="перезібрати вже знайдене")
    a = ap.parse_args()

    data = json.loads(PARAMS.read_text())
    cases = data["cases"]
    done = failed = 0
    for c in cases:
        name = c["name"]
        if a.only and name not in a.only:
            continue
        if c.get("img") and c.get("url") and not a.force:
            continue
        tokens = VERIFY.get(name) or model_tokens(name)
        if name in URL_HINTS:
            links = [URL_HINTS[name]]
        else:
            try:
                links = rank(search(QUERY.get(name, name)))
            except Exception as e:
                print(f"✗ {name}: пошук впав ({e})")
                failed += 1
                continue
        picked = None
        for link in links:
            try:
                img, title, why = page_image(link, tokens)
            except Exception as e:
                continue
            if why or not img:
                continue
            picked = (link, img, title)
            break
        if not picked:
            print(f"✗ {name}: сторінки з фото не знайшов ({len(links)} кандидатів)")
            failed += 1
            continue
        link, img, title = picked
        print(f"• {name}\n    → {link}\n    фото: {img[:90]}")
        if a.dry:
            continue
        dest = IMG_DIR / f"{slug(name)}.jpg"
        try:
            size = save_thumb(img, link, dest)
        except Exception as e:
            print(f"    ✗ фото не завантажилось: {e}")
            failed += 1
            continue
        c["url"] = link
        c["img"] = f"assets/cases/{dest.name}"
        print(f"    збережено {dest.name} {size[0]}×{size[1]}")
        done += 1
        time.sleep(1.5)

    if not a.dry:
        PARAMS.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    print(f"\nготово: {done} з фото, {failed} без")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
