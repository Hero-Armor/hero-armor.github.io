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


def fetch(url):
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

    bad = []
    for b in json.loads(BOM_FILE.read_text()):
        url = b.get("url")
        if not url or (a.only and a.only.lower() not in b["item"].lower()):
            continue
        asin = (re.search(r"/dp/([A-Z0-9]{10})", url) or [None, None])[1]
        html = fetch(url)
        if html.startswith("__ERR__"):
            print(f"  ✗ {b['item'][:44]} — сторінка не відкрилась ({html[7:60]})")
            bad.append(b["item"])
            continue
        if asin and asin not in html:
            print(f"  ✗ {b['item'][:44]} — на сторінці нема ASIN {asin}: {title_of(html)}")
            bad.append(b["item"])
            continue
        print(f"  ✓ {b['item'][:44]} — {title_of(html) or 'сторінка жива'}")

    print(f"\nпідсумок: перевірено лінків, підозрілих {len(bad)}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
