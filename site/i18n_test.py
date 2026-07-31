#!/usr/bin/env python3
"""Тести англійської версії дашборда.

Перевіряє не «схоже на переклад», а те, що ламається насправді: збита
розмітка після підстановки, загублені числа, мертві посилання, впалий
інтерактив. Запуск:

    python3 site/i18n_test.py                 # без браузера
    /root/venv/playwright/bin/python3 site/i18n_test.py --browser

Код виходу 1, якщо хоч один тест впав.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
EN = DOCS / "en"

CYR = re.compile(r"[А-Яа-яЇїІіЄєҐґ]")
TAGS = re.compile(r"<\s*(/?)\s*([a-zA-Z][\w:-]*)")
NUM = re.compile(r"\d+(?:[.,]\d+)?")
LD = re.compile(r"<script[^>]*application/ld\+json.*?</script>", re.S | re.I)
SCRIPT = re.compile(r"<script\b[^>]*>.*?</script>", re.S | re.I)
STYLE = re.compile(r"<style\b[^>]*>.*?</style>", re.S | re.I)

fails, checks = [], 0


def ok(name, cond, detail=""):
    global checks
    checks += 1
    if cond:
        print(f"  ✓ {name}")
    else:
        print(f"  ✗ {name} — {detail}")
        fails.append(f"{name}: {detail}")


def pages():
    return sorted(p.name for p in EN.glob("*.html"))


# --- 1. чи не лишилось українського --------------------------------------

def test_no_ukrainian():
    print("\n1. У англійській версії нема українського тексту")
    for name in pages():
        txt = _reader_text((EN / name).read_text())
        hits = [h for h in re.findall(r"[^\s<>\"]*[А-Яа-яЇїІіЄєҐґ][^\s<>\"]*", txt)
                if h.strip()]
        ok(name, not hits, f"{len(hits)} шматків, напр. {hits[:5]}")


def _reader_text(html):
    """Те, що бачить читач: без ld+json, без стилів, без коментарів у коді
    (коментарі — записки самим собі, їх не перекладаємо) і без кнопки мови."""
    html = LD.sub("", html)
    html = STYLE.sub("", html)
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    html = re.sub(r' · <a class="lang-sw"[^>]*>[^<]*</a>', "", html)
    return re.sub(r"//[^\n]*", "", html)


# --- 2. розмітка не поїхала ----------------------------------------------

def test_markup_identical():
    """Обидві мови зібрані з однієї сторінки, тож теги мають збігатись
    один в один: якщо мітка тега загубилась при перекладі — тут і вилізе."""
    print("\n2. Розмітка збігається з українською (теги не побиті)")
    for name in pages():
        uk = TAGS.findall((DOCS / name).read_text())
        en = TAGS.findall((EN / name).read_text())
        ok(name, uk == en,
           f"тегів uk={len(uk)} en={len(en)}; перша різниця — {_tag_diff(uk, en)}")


def _tag_diff(uk, en):
    for i, (a, b) in enumerate(zip(uk, en)):
        if a != b:
            return f"№{i}: {a} проти {b}"
    return "довжина"


# --- 3. числа на місці ----------------------------------------------------

def test_numbers_kept():
    print("\n3. Усі числа перенеслись (переклад не чіпав розрахунки)")
    for name in pages():
        uk = _visible(DOCS / name)
        en = _visible(EN / name)
        uk_n, en_n = sorted(NUM.findall(uk)), sorted(NUM.findall(en))
        lost = _missing(uk_n, en_n)
        ok(name, not lost, f"загублено {len(lost)}: {lost[:8]}")


def _visible(path):
    txt = LD.sub("", path.read_text())
    txt = STYLE.sub("", txt)
    return re.sub(r"<[^>]+>", " ", txt)


def _missing(a, b):
    from collections import Counter
    diff = Counter(a) - Counter(b)
    return sorted(diff.elements())


# --- 4. посилання і картинки живі ----------------------------------------

def test_links():
    print("\n4. Посилання й файли всередині англійської версії існують")
    for name in pages():
        html = (EN / name).read_text()
        bad = []
        for m in re.finditer(r'(?:href|src)="([^"#][^"]*)"', html):
            href = m.group(1)
            if href.startswith(("http", "data:", "mailto:", "#")):
                continue
            if "'+" in href or '"+' in href:
                continue          # склейка рядків у скрипті, а не адреса
            target = (EN / href).resolve()
            if not target.exists():
                bad.append(href)
        ok(name, not bad, f"нема файлів: {sorted(set(bad))[:5]}")


# --- 5. перемикач мови ----------------------------------------------------

def test_switch():
    print("\n5. Перемикач мови стоїть з обох боків і веде куди треба")
    for name in pages():
        en = (EN / name).read_text()
        uk = (DOCS / name).read_text()
        ok(f"en/{name} → ../{name}", f'href="../{name}"' in en, "нема лінка на українську")
        ok(f"{name} → en/{name}", f'href="en/{name}"' in uk, "нема лінка на англійську")
        ok(f"{name} lang", 'html lang="en"' in en and 'html lang="uk"' in uk,
           "нема позначки мови")


# --- 6. інтерактив рахує те саме ------------------------------------------

def test_browser():
    print("\n6. Сторінки відкриваються, скрипти рахують ті самі числа")
    from playwright.sync_api import sync_playwright
    shots = ROOT / "site" / "i18n" / "shots"
    shots.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for name in pages():
            errors = []
            page = br.new_page(viewport={"width": 1280, "height": 1000})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text)
                    if m.type == "error" else None)
            page.goto((EN / name).as_uri())
            page.wait_for_timeout(1200)
            en_nums = _dom_numbers(page)
            page.screenshot(path=str(shots / f"en-{name}.png"), full_page=True)
            page.close()

            page = br.new_page(viewport={"width": 1280, "height": 1000})
            page.goto((DOCS / name).as_uri())
            page.wait_for_timeout(1200)
            uk_nums = _dom_numbers(page)
            page.screenshot(path=str(shots / f"uk-{name}.png"), full_page=True)
            page.close()

            ok(f"{name}: без помилок у скриптах", not errors, str(errors[:2]))
            uk_d = {k: _digits(v) for k, v in uk_nums.items()}
            en_d = {k: _digits(v) for k, v in en_nums.items()}
            ok(f"{name}: інтерактив дає ті самі числа", uk_d == en_d,
               f"розбіжність у {_first_diff(uk_nums, en_nums)}")
        br.close()


def _dom_numbers(page):
    """Числа, які скрипт сам вписав у сторінку після завантаження."""
    return page.evaluate("""() => {
        const out = {};
        document.querySelectorAll('[id^="v-"], .num, .val, output, b[id]')
          .forEach(el => { const t = (el.textContent||'').trim();
                           if (/\\d/.test(t)) out[el.id || el.className] = t; });
        return out;
    }""")


def _digits(text):
    """Порівнюємо самі числа: одиниці ж і мають бути іншими (Вт → W)."""
    return re.findall(r"-?\d+(?:[.,]\d+)?", text or "")


def _first_diff(a, b):
    for k in sorted(set(a) | set(b)):
        if a.get(k) != b.get(k):
            return f"{k}: uk={a.get(k)!r} en={b.get(k)!r}"
    return ""


# --- 7. памʼять перекладу здорова ----------------------------------------

def test_tm():
    print("\n7. Памʼять перекладу без порожніх і без залишків української")
    tm = json.loads((ROOT / "site" / "i18n" / "tm.json").read_text())
    empty = [k for k, v in tm.items() if not (v or "").strip()]
    cyr = [k for k, v in tm.items() if CYR.search(v or "")]
    ph = [k for k, v in tm.items()
          if sorted(re.findall(r"<x\d+/>", k)) != sorted(re.findall(r"<x\d+/>", v or ""))]
    ok("нема порожніх перекладів", not empty, f"{len(empty)}")
    ok("нема українського в перекладі", not cyr, f"{len(cyr)}: {cyr[:3]}")
    ok("мітки тегів збігаються", not ph, f"{len(ph)}: {ph[:3]}")
    print(f"  (у памʼяті {len(tm)} рядків)")


def test_idempotent():
    """Друга збірка не має обростати другою шапкою і другим перемикачем."""
    print("\n8. Повторна збірка нічого не дублює")
    for name in pages():
        for path, tag in ((DOCS / name, "uk"), (EN / name, "en")):
            txt = path.read_text()
            heads = len(re.findall(r"<!doctype html>", txt, re.I))
            sw = len(re.findall(r'class="lang-sw"', txt))
            ok(f"{tag}/{name}", heads == 1 and sw == 1,
               f"шапок {heads}, перемикачів {sw}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--browser", action="store_true",
                    help="ще й прогнати сторінки у справжньому браузері")
    a = ap.parse_args()
    if not EN.exists():
        sys.exit("нема docs/en — спершу python3 site/i18n.py")
    test_no_ukrainian()
    test_markup_identical()
    test_numbers_kept()
    test_links()
    test_switch()
    test_tm()
    test_idempotent()
    if a.browser:
        test_browser()
    print(f"\nпройдено {checks - len(fails)}/{checks}")
    sys.exit(1 if fails else 0)
