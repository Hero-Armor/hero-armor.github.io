#!/root/venv/playwright/bin/python3
"""Те саме, що case_media.py, але через хмарний браузер.

Половина магазинів (Seahorse, Coleman, Home Depot, Costco, Harbor Freight) і
самі пошуковики ріжуть наш серверний IP: 403 або «unusual traffic». Тому
другий захід іде через Browserless із резидентною американською адресою —
той самий шлях, яким пробивали блокування українських медіа для /press.

  /root/venv/playwright/bin/python3 enclosure/model/case_media_browser.py
        [--only "Nanuk 960" ...] [--dry]

Фото качаємо ТІЄЮ Ж сесією браузера: посилання на CDN підписані й сторонньому
завантажувачу віддають 403.
"""
import argparse
import json
import re
import sys
import unicodedata
from io import BytesIO
from pathlib import Path

sys.path.insert(0, "/root/tools")
import cloud_browser                                   # noqa: E402
from PIL import Image                                  # noqa: E402
from playwright.sync_api import sync_playwright        # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
PARAMS = ROOT / "enclosure" / "data" / "params.json"
IMG_DIR = ROOT / "site" / "assets" / "cases"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from case_media import (BAD, MAKER, SHOP, QUERY, VERIFY, URL_HINTS,  # noqa: E402
                        SITE_SEARCH, model_tokens, slug)


def rank(links):
    def key(u):
        host = u.split("/")[2].lower() if "://" in u else u
        if any(d in host for d in MAKER):
            return 0
        if any(d in host for d in SHOP):
            return 1
        return 2
    return sorted(links, key=key)


def search(page, query):
    """Пошук через Bing у справжньому браузері.

    DuckDuckGo і Google з хмарного браузера віддають порожню видачу (SPA не
    домальовується / капча), Bing віддає нормально. Посилання в Bing —
    редиректи виду bing.com/ck/a, тому домен беремо з підпису під заголовком
    і за ним сортуємо, а справжню адресу дізнаємось уже після переходу.
    """
    page.goto("https://www.bing.com/search?q=" + query.replace(" ", "+"),
              wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_selector("li.b_algo h2 a", timeout=20000)
    except Exception:
        return []
    items = page.eval_on_selector_all("li.b_algo", """els => els.map(el => {
        const a = el.querySelector('h2 a');
        const cite = el.querySelector('cite');
        return a ? {href: a.href,
                    host: (cite ? cite.textContent : '').split(/[\s\u203a\/]/)[0].toLowerCase()}
                 : null;
    }).filter(Boolean)""")
    items = [i for i in items if not any(b in i["host"] for b in BAD)]

    def key(i):
        if any(d in i["host"] for d in MAKER):
            return 0
        if any(d in i["host"] for d in SHOP):
            return 1
        return 2
    return [i["href"] for i in sorted(items, key=key)]


ALLOWED = MAKER + SHOP


def site_search(page, url, host):
    """Пошук усередині магазину: беремо посилання на товар з його ж домену."""
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)
    links = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
    out = []
    for l in links:
        if host not in l or l in out:
            continue
        if any(x in l.lower() for x in ("/search", "?keyword", "/cart", "/login",
                                        "/account", "javascript:", "#")):
            continue
        if re.search(r"/(p|product|products|item|shop)/|\.p\?|\.html$", l, re.I):
            out.append(l)
    return out[:8]


def product_image(page, url, tokens):
    """Перейти, переконатись що це та модель, і взяти фото товару.

    Адресу беремо ПІСЛЯ переходу (`page.url`): у видачі Bing посилання —
    його власний редиректор, і саме він осів би в базі замість сторінки
    товару.
    """
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(1800)
    real = page.url
    host = real.split("/")[2].lower() if "://" in real else ""
    if not any(d in host for d in ALLOWED):
        return None, real, f"чужий сайт ({host})"
    title = (page.title() or "").strip()
    hay = (real + " " + title).lower().replace("_", "-")
    if tokens:
        body = (page.content() or "").lower()
        for t in tokens:
            if t not in hay and t not in body:
                return None, real, f"на сторінці нема «{t}»"
    img = page.evaluate("""() => {
        const meta = document.querySelector('meta[property="og:image"], meta[name="twitter:image"]');
        if (meta && meta.content) return meta.content;
        let best = null, area = 0;
        for (const im of document.images) {
            const a = im.naturalWidth * im.naturalHeight;
            if (a > area && im.naturalWidth >= 300) { area = a; best = im.currentSrc || im.src; }
        }
        return best;
    }""")
    return img, real, None


def save(ctx, img_url, referer, dest, box=520):
    resp = ctx.request.get(img_url, headers={"Referer": referer})
    if not resp.ok:
        raise ValueError(f"CDN віддав {resp.status}")
    im = Image.open(BytesIO(resp.body()))
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
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    data = json.loads(PARAMS.read_text())
    todo = [c for c in data["cases"]
            if (not c.get("img") or not c.get("url"))
            and (not a.only or c["name"] in a.only)]
    if not todo:
        print("нема чого добирати")
        return 0
    print(f"через хмарний браузер: {len(todo)} позицій")

    done = failed = 0
    with sync_playwright() as pw:
        for c in todo:
            # окрема сесія на кожну позицію: спільна вмирала на третій-четвертій
            # («Target page, context or browser has been closed»)
            try:
                br = pw.chromium.connect_over_cdp(cloud_browser.build_ws_url(gov=False),
                                                  timeout=120000)
            except Exception as e:
                print(f"✗ браузер не піднявся: {str(e)[:70]}")
                failed += 1
                continue
            ctx = br.contexts[0] if br.contexts else br.new_context()
            page = ctx.new_page()
            name = c["name"]
            tokens = VERIFY.get(name) or model_tokens(name)
            try:
                if name in URL_HINTS:
                    links = [URL_HINTS[name]]
                elif name in SITE_SEARCH:
                    links = site_search(page, *SITE_SEARCH[name])
                    if not links:
                        links = search(page, QUERY.get(name, name))
                else:
                    links = search(page, QUERY.get(name, name))
            except Exception as e:
                print(f"✗ {name}: пошук впав ({str(e)[:60]})")
                failed += 1
                br.close()
                continue
            picked = None
            for link in links[:6]:
                try:
                    img, real, why = product_image(page, link, tokens)
                except Exception:
                    continue
                if why or not img:
                    continue
                picked = (real, img)
                break
            if not picked:
                print(f"✗ {name}: не знайшов сторінки з фото ({len(links)} кандидатів)")
                failed += 1
                br.close()
                continue
            link, img = picked
            print(f"• {name}\n    → {link}")
            if a.dry:
                continue
            dest = IMG_DIR / f"{slug(name)}.jpg"
            try:
                size = save(ctx, img, link, dest)
            except Exception as e:
                print(f"    ✗ фото: {str(e)[:70]}")
                failed += 1
                br.close()
                continue
            c["url"], c["img"] = link, f"assets/cases/{dest.name}"
            print(f"    збережено {dest.name} {size[0]}×{size[1]}")
            done += 1
            br.close()

    if not a.dry:
        PARAMS.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    print(f"\nготово: {done} з фото, {failed} без")
    return 0


if __name__ == "__main__":
    sys.exit(main())
