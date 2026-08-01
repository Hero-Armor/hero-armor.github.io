#!/usr/bin/env python3
"""Справжні фото товарів у закупівлі — «щоб було видно, про що мова».

Прохання Івана 31.07/01.08: у таблиці закупівлі стояли самі назви, і зрозуміти,
що таке «Катафоти 2×3\" DOT-SAE» чи «Врізні вогні в торець подіуму», можна було
тільки відкривши лінк. Тепер біля кожної позиції з посиланням на Amazon стоїть
мініатюра справжнього товару.

Як це працює:
  1. беремо позиції `data/bom.json`, у яких `url` виду amazon.com/dp/<ASIN>;
  2. тягнемо сторінку товару через СВІЙ Firecrawl (localhost:3002) — Amazon
     віддає капчу звичайному urllib, а через нього приходить справжня сторінка
     і не витрачається квота платних товарних API;
  3. ЗВІРЯЄМО, що сторінка справді про цей ASIN (він має бути в тілі сторінки),
     і лише тоді беремо фото — адреси і картинки «по памʼяті» в цьому проєкті
     не склеюються, на цьому вже обпікались;
  4. стискаємо до мініатюри 400 px і кладемо в `site/assets/bom/<ASIN>.jpg`;
  5. дописуємо `img` у відповідну позицію `data/bom.json`.

Резерв, якщо Firecrawl мовчить: товарний рушій `/root/tools/product-research`
(він повертає поле image) — але тільки коли ASIN у знайденому лінку збігається.

Запуск:   python3 site/bom_media.py [--only "катафот"] [--limit N] [--dry] [--force]
Потрібен Pillow (локально; CI фото не тягне — вони комітяться разом з bom.json).
"""

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOM_FILE = ROOT / "data" / "bom.json"
IMG_DIR = ROOT / "site" / "assets" / "bom"
FIRECRAWL = "http://localhost:3002/v1/scrape"
RESEARCH = "/root/tools/product-research/research.py"
THUMB_PX = 400
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def asin_of(url):
    m = re.search(r"/dp/([A-Z0-9]{10})", url or "")
    return m.group(1) if m else None


def scrape(asin):
    """Сторінка товару через свій Firecrawl. Повертає html або None."""
    body = json.dumps({"url": f"https://www.amazon.com/dp/{asin}",
                       "formats": ["rawHtml"]}).encode()
    req = urllib.request.Request(FIRECRAWL, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.loads(r.read().decode("utf-8", "ignore"))
        return (d.get("data") or {}).get("rawHtml")
    except Exception as e:
        print(f"    firecrawl: {e}")
        return None


def image_from_html(html, asin):
    """Найбільше фото товару зі сторінки — і тільки якщо сторінка про наш ASIN."""
    if not html or asin not in html:
        return None
    pats = [
        r'"hiRes":"(https://m\.media-amazon\.com/images/[^"]+)"',
        r'"large":"(https://m\.media-amazon\.com/images/[^"]+)"',
        r'data-old-hires="(https://m\.media-amazon\.com/images/[^"]+)"',
        r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"',
        r'id="landingImage"[^>]*src="(https://m\.media-amazon\.com/images/[^"]+)"',
        r'data-a-dynamic-image="\{&quot;(https://m\.media-amazon\.com/images/[^&]+)&quot;',
        r'"mainUrl":"(https://m\.media-amazon\.com/images/[^"]+)"',
        r'(https://m\.media-amazon\.com/images/I/[A-Za-z0-9%+._-]+\._AC_[A-Za-z0-9_]*\.jpg)',
    ]
    for p in pats:
        m = re.search(p, html)
        if m:
            return m.group(1).replace("\\/", "/")
    return None


def image_from_engine(asin, title):
    """Резерв: товарний рушій. Беремо фото лише з лінка з тим самим ASIN."""
    try:
        out = subprocess.run(
            [sys.executable, RESEARCH, "--mode", "shop", "--limit", "8",
             "--json", asin],
            capture_output=True, text=True, timeout=240).stdout
        data = json.loads(out[out.index("{"):])
        shop = data.get("shop")
        if not isinstance(shop, list):   # останній рубіж рушія — просто текст
            return None
        for it in shop:
            if not isinstance(it, dict):
                continue
            if asin_of(it.get("url", "")) == asin and it.get("image"):
                return it["image"]
    except Exception as e:
        print(f"    рушій: {e}")
    return None


def save_thumb(url, dest):
    from PIL import Image
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    raw = urllib.request.urlopen(req, timeout=60).read()
    im = Image.open(BytesIO(raw))
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    im.thumbnail((THUMB_PX, THUMB_PX), Image.LANCZOS)
    bg = Image.new("RGB", im.size, "white")
    bg.paste(im)
    dest.parent.mkdir(parents=True, exist_ok=True)
    bg.save(dest, "JPEG", quality=82, optimize=True)
    return dest.stat().st_size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="підрядок назви позиції")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--force", action="store_true", help="перетягнути навіть якщо фото вже є")
    a = ap.parse_args()

    bom = json.loads(BOM_FILE.read_text())
    todo = []
    for b in bom:
        asin = asin_of(b.get("url", ""))
        if not asin:
            continue
        if a.only and a.only.lower() not in b["item"].lower():
            continue
        have = b.get("img") and (ROOT / "site" / b["img"]).exists()
        if have and not a.force:
            continue
        todo.append((b, asin))
    if a.limit:
        todo = todo[:a.limit]

    print(f"позицій до роботи: {len(todo)}")
    got = 0
    for b, asin in todo:
        print(f"  · {b['item'][:60]} [{asin}]")
        if a.dry:
            continue
        # Amazon час від часу віддає капчу — пробуємо тричі, потім рушій
        src = None
        for attempt in range(3):
            src = image_from_html(scrape(asin), asin)
            if src:
                break
            time.sleep(2.0 * (attempt + 1))
        src = src or image_from_engine(asin, b["item"])
        if not src:
            print("    фото не знайшлось — лишаю без картинки")
            continue
        try:
            size = save_thumb(src, IMG_DIR / f"{asin}.jpg")
        except Exception as e:
            print(f"    завантаження: {e}")
            continue
        # перечитуємо файл перед записом: у репо буває паралельна сесія
        cur = json.loads(BOM_FILE.read_text())
        for x in cur:
            if x.get("url") == b.get("url") and x["item"] == b["item"]:
                x["img"] = f"assets/bom/{asin}.jpg"
        BOM_FILE.write_text(json.dumps(cur, ensure_ascii=False, indent=1) + "\n")
        got += 1
        print(f"    ok — {size // 1024} КБ")
        time.sleep(1.0)

    print(f"готово: фото у {got} позицій")


if __name__ == "__main__":
    main()
