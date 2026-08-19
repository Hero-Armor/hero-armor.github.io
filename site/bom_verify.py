#!/usr/bin/env python3
"""Чи справді лінк веде на той товар, який записаний у закупівлі.

Правило Івана 01.08.2026: у кожної позиції — посилання на КОНКРЕТНУ сторінку
товара і фото. Лінк, набраний «по памʼяті», гірший за порожню клітинку: він
виглядає перевіреним. Тому перед публікацією ганяємо цей скрипт — він відкриває
сторінку через свій Firecrawl і дивиться, чи вона взагалі існує і чи згадує
потрібний ASIN.

Запуск:  python3 site/bom_verify.py [--only "підрядок"]
Вихід:   рядок на позицію + підсумок; код 1, якщо є мертві лінки.
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOM_FILE = ROOT / "data" / "bom.json"
FIRECRAWL = "http://localhost:3002/v1/scrape"


PROXY_FILE = Path("/root/.secrets/us_proxy")
MOBILE_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
             "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")


def fetch_amazon(asin):
    """Amazon через Firecrawl віддає капчу — і перевірка мовчки бракує живі лінки.

    17.08.2026: `bom_verify` показав 84 «підозрілих» позиції, хоча ті самі ASIN
    відкривались вручну з кодом 200. Причина — не лістинги, а сам скрипт: Firecrawl
    з німецького сервера отримував сторінку-капчу з заголовком «Amazon.com», у якій
    ASIN, звісно, нема. Сліпа перевірка гірша за відсутню, бо виглядає як робота.
    Тому для Amazon ідемо мобільною сторінкою крізь американський проксі — той самий
    шлях, яким ми і так тягнемо ціни.
    """
    if not PROXY_FILE.exists():
        return "__ERR__нема /root/.secrets/us_proxy"
    px = PROXY_FILE.read_text().strip()
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": px, "https": px}))
    req = urllib.request.Request(f"https://www.amazon.com/gp/aw/d/{asin}",
                                 headers={"User-Agent": MOBILE_UA,
                                          "Accept-Language": "en-US,en;q=0.9"})
    try:
        with op.open(req, timeout=90) as r:
            return r.read().decode("utf-8", "ignore")
    except Exception as e:
        return f"__ERR__{e}"


def fetch(url, asin=None):
    if asin and "amazon." in url:
        return fetch_amazon(asin)
    body = json.dumps({"url": url, "formats": ["rawHtml"]}).encode()
    req = urllib.request.Request(FIRECRAWL, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.loads(r.read().decode("utf-8", "ignore"))
        return ((d.get("data") or {}).get("rawHtml") or "")
    except Exception as e:
        return f"__ERR__{e}"


def title_of(html):
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    return re.sub(r"\s+", " ", m.group(1)).strip()[:90] if m else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()

    bad, ok_n = [], 0
    for b in json.loads(BOM_FILE.read_text()):
        url = b.get("url")
        if not url or (a.only and a.only.lower() not in b["item"].lower()):
            continue
        asin = (re.search(r"/dp/([A-Z0-9]{10})", url) or [None, None])[1]
        html = fetch(url, asin)
        if html.startswith("__ERR__"):
            print(f"  ✗ {b['item'][:44]} — сторінка не відкрилась ({html[7:60]})")
            bad.append(b["item"])
            continue
        if asin and asin not in html:
            print(f"  ✗ {b['item'][:44]} — на сторінці нема ASIN {asin}: {title_of(html)}")
            bad.append(b["item"])
            continue
        ok_n += 1
        print(f"  ✓ {b['item'][:44]} — {title_of(html) or 'сторінка жива'}")

    total = len(bad) + ok_n
    print(f"\nпідсумок: перевірено {total}, підозрілих {len(bad)}")

    # ⚠ Граблі 17.08.2026: перевірка показала 84 «мертвих» лінки на живих лістингах —
    # насправді Amazon віддавав нашому серверу капчу. Масовий однаковий вердикт — це
    # привід підозрювати ІНСТРУМЕНТ, а не дані. Тому мовчазний «все погано» заборонено.
    if total >= 10 and len(bad) / total > 0.6:
        print(f"\n⚠⚠ СТОП: підозрілих {len(bad)} з {total} — це схоже на поломку самої "
              f"перевірки (капча, проксі, мережа), а не на мертві лінки.")
        print("   Перевір ОДИН лінк руками, перш ніж вірити цьому списку.")
        sys.exit(2)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
