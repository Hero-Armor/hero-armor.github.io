#!/usr/bin/env python3
"""Англійська версія дашборда Hero Armor.

Дашборд пишеться українською: тексти живуть у `data/*.json`, у шаблонах і в
самому `build.py`. Перекладати джерела означало б вести дві копії правди і
щоразу забувати одну з них. Тому переклад — окремий шар ПІСЛЯ збірки:

    python3 site/build.py     # docs/*.html   (українською, як і було)
    python3 site/i18n.py      # docs/en/*.html (англійською) + перемикач мови

Як це працює
------------
* сторінка ріжеться на смислові шматки (абзац, комірка таблиці, підпис на
  схемі), а не на окремі слова — інакше переклад виходить рваним;
* теги всередині шматка ховаються за мітки ⟦1⟧, тож посилання й <b> лишаються
  на своїх місцях і модель їх не псує;
* усе перекладене складається в памʼять `site/i18n/tm.json`. Наступна збірка
  платить лише за нові рядки, а виправлення руками в памʼяті переживають
  перезбірку — це і є місце, де людина правит переклад;
* терміни (просадка, щит, біжуча вода) тримає `site/i18n/glossary.json`, щоб
  на всіх сторінках вони звучали однаково.

Схеми перекладаються самі: `build.py` вставляє їх у сторінку як SVG-текст, а
не картинкою, тож підписи на кресленнях — такі самі шматки тексту.

Команди:
    python3 site/i18n.py                # зібрати всю англійську версію
    python3 site/i18n.py --only lights_lab.html   # одну сторінку (пілот)
    python3 site/i18n.py --dry          # скільки нового треба перекласти
    python3 site/i18n.py --check        # чи не лишилось українського в /en
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
EN = DOCS / "en"
I18N = ROOT / "site" / "i18n"
TM_FILE = I18N / "tm.json"
GLOSSARY_FILE = I18N / "glossary.json"

KEY_FILE = Path("/root/.secrets/openai_api_key")
API_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o"

CYR = re.compile(r"[А-Яа-яЇїІіЄєҐґ]")

# теги без закриття (у т.ч. SVG-фігури) — стек їх не чекає
VOID = {"br", "img", "input", "hr", "meta", "link", "source", "area", "base",
        "col", "embed", "param", "track", "wbr", "path", "circle", "rect",
        "line", "polyline", "polygon", "use", "stop", "ellipse", "image"}

# смислові шматки: беремо ті, що не містять інших таких самих усередині
BLOCK = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "td", "th", "caption",
         "label", "button", "option", "figcaption", "summary", "dt", "dd",
         "div", "blockquote", "legend", "title", "text", "tspan", "desc"}

ATTRS = ("alt", "title", "placeholder", "aria-label")

TOKEN = re.compile(
    r"(?P<comment><!--.*?-->)"
    r"|(?P<script><script\b[^>]*>.*?</script>)"
    r"|(?P<style><style\b[^>]*>.*?</style>)"
    r"|(?P<tag><[^>]+>)"
    r"|(?P<text>[^<]+)", re.S | re.I)

TAG_NAME = re.compile(r"</?\s*([a-zA-Z][\w:-]*)")
PH = "⟦%d⟧"
PH_FIND = re.compile(r"⟦\d+⟧")


# --- памʼять перекладу -----------------------------------------------------

def load_tm():
    if TM_FILE.exists():
        return json.loads(TM_FILE.read_text())
    return {}


def save_tm(tm):
    I18N.mkdir(parents=True, exist_ok=True)
    TM_FILE.write_text(json.dumps(tm, ensure_ascii=False, indent=1,
                                  sort_keys=True) + "\n")


def load_glossary():
    if GLOSSARY_FILE.exists():
        return json.loads(GLOSSARY_FILE.read_text())
    return {}


# --- розбір сторінки на шматки --------------------------------------------

def _protect(inner):
    """Сховати теги за мітки ⟦n⟧: модель бачить чистий текст."""
    tags = []

    def sub(m):
        tags.append(m.group(0))
        return PH % (len(tags) - 1)

    return re.sub(r"<[^>]+>", sub, inner), tags


def _restore(text, tags):
    def sub(m):
        i = int(m.group(0)[1:-1])
        return tags[i] if i < len(tags) else ""
    return PH_FIND.sub(sub, text)


def plan(html):
    """Список ділянок сторінки, які треба перекласти.

    Кожна — {start, end, src, tags}: `src` іде в модель, `tags` повертають
    посилання й розмітку на місце.
    """
    spans = []
    covered = []          # (start, end) вже взятих смислових шматків
    stack = []            # [tagname, inner_start, has_block_child]

    for m in TOKEN.finditer(html):
        kind = m.lastgroup
        if kind in ("comment", "style"):
            continue
        if kind == "script":
            spans.extend(_script_spans(html, m.start(), m.group(0)))
            continue
        if kind == "text":
            continue
        tag = m.group(0)
        name_m = TAG_NAME.match(tag)
        if not name_m:
            continue
        name = name_m.group(1).lower()
        closing = tag.startswith("</")
        selfclose = tag.rstrip().endswith("/>") or name in VOID

        if not closing and not selfclose:
            if name in BLOCK and stack:
                stack[-1][2] = True
            stack.append([name, m.end(), False])
            continue
        if not closing:                      # <br/>, <img …>
            if name in BLOCK and stack:
                stack[-1][2] = True
            continue

        # закриття: розкручуємо стек до свого імені (розмітка буває неохайна)
        while stack:
            open_name, inner_start, has_block = stack.pop()
            if open_name != name:
                continue
            if open_name in BLOCK and not has_block:
                inner = html[inner_start:m.start()]
                if CYR.search(inner):
                    src, tags = _protect(inner)
                    if src.strip():
                        spans.append({"start": inner_start, "end": m.start(),
                                      "src": src, "tags": tags})
                        covered.append((inner_start, m.start()))
            break

    spans.extend(_loose_text_spans(html, covered))
    spans.extend(_attr_spans(html))
    spans.sort(key=lambda s: s["start"])
    return spans


def _loose_text_spans(html, covered):
    """Текст, що не потрапив у жоден смисловий шматок (буває в контейнерах)."""
    covered.sort()
    out = []
    for m in TOKEN.finditer(html):
        if m.lastgroup != "text":
            continue
        if not CYR.search(m.group(0)):
            continue
        s, e = m.start(), m.end()
        if any(cs <= s and e <= ce for cs, ce in covered):
            continue
        text = m.group(0)
        lead = len(text) - len(text.lstrip())
        trail = len(text) - len(text.rstrip())
        out.append({"start": s + lead, "end": e - trail,
                    "src": text.strip(), "tags": []})
    return out


def _attr_spans(html):
    out = []
    for m in TOKEN.finditer(html):
        if m.lastgroup != "tag":
            continue
        tag = m.group(0)
        for a in ATTRS:
            for am in re.finditer(rf'\b{a}="([^"]*)"', tag):
                if CYR.search(am.group(1)):
                    out.append({"start": m.start() + am.start(1),
                                "end": m.start() + am.end(1),
                                "src": am.group(1), "tags": []})
    return out


def _script_spans(html, offset, block):
    """Рядки-літерали з українським текстом усередині скриптів сторінки."""
    if re.match(r"<script[^>]*application/ld\+json", block, re.I):
        return []          # машинні дані для агентів, не екран
    out = []
    body_m = re.match(r"<script\b[^>]*>", block, re.I)
    body_start = body_m.end()
    body = block[body_start:block.rfind("</script")]
    for m in re.finditer(r"(['\"`])((?:\\.|(?!\1)[^\\])*)\1", body):
        if CYR.search(m.group(2)):
            out.append({"start": offset + body_start + m.start(2),
                        "end": offset + body_start + m.end(2),
                        "src": m.group(2), "tags": []})
    return out


def render(html, spans, tm):
    """Скласти сторінку назад з перекладеними ділянками."""
    out = html
    for sp in sorted(spans, key=lambda s: s["start"], reverse=True):
        en = tm.get(sp["src"])
        if not en:
            continue
        out = out[:sp["start"]] + _restore(en, sp["tags"]) + out[sp["end"]:]
    return out


# --- переклад --------------------------------------------------------------

SYSTEM = """You translate the internal engineering dashboard of "Hero Armor" \
from Ukrainian into English.

Hero Armor is a memorial art installation for Burning Man 2026 honouring a \
fallen Ukrainian defender, Zakhar Zakharov. The dashboard covers 12V wiring, \
LED lighting, addressable strip, solar/power stations, audio, enclosure, \
purchasing and logistics. Readers are the project's engineers and producers.

Rules:
- Keep the register: terse, factual engineering notes. Do not embellish, do \
not add or drop information, do not explain.
- Preserve EXACTLY: numbers, units, part numbers, model names, currency, \
percentages, URLs, HTML entities (&nbsp; &mdash; …), emoji, punctuation marks \
like · ← →.
- Preserve EVERY placeholder ⟦0⟧ ⟦1⟧ … exactly as written, same count, in the \
position that keeps the sentence natural. They stand for HTML tags.
- Do not translate proper names of people, brands, or file names.
- Some segments are labels on wiring diagrams or table headers: keep them as \
short as the original, abbreviate the way an electrician would.
- Never output Ukrainian or Russian text.

Return STRICT JSON: {"t": ["…", "…"]} — one string per input segment, same \
order, same count. No commentary."""


def _api(messages):
    body = json.dumps({"model": MODEL, "temperature": 0,
                       "response_format": {"type": "json_object"},
                       "messages": messages}).encode()
    req = urllib.request.Request(
        API_URL, data=body,
        headers={"Authorization": f"Bearer {KEY_FILE.read_text().strip()}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(json.loads(r.read())["choices"][0]["message"]["content"])


def _glossary_block(glossary):
    if not glossary:
        return ""
    lines = "\n".join(f"- {k} → {v}" for k, v in glossary.items())
    return f"\nGlossary — use these renderings consistently:\n{lines}\n"


def translate(missing, glossary, verbose=True):
    """Перекласти нові рядки пачками; повертає {укр: англ}."""
    done = {}
    batch, size = [], 0
    batches = []
    for s in missing:
        if batch and (len(batch) >= 30 or size + len(s) > 5000):
            batches.append(batch)
            batch, size = [], 0
        batch.append(s)
        size += len(s)
    if batch:
        batches.append(batch)

    for i, b in enumerate(batches, 1):
        payload = json.dumps({"segments": b}, ensure_ascii=False)
        msgs = [{"role": "system", "content": SYSTEM + _glossary_block(glossary)},
                {"role": "user", "content": payload}]
        try:
            res = _api(msgs)
            got = res.get("t") or []
        except (urllib.error.URLError, ValueError, KeyError) as e:
            print(f"  пачка {i}: збій API ({e}) — пробую поштучно")
            got = []
        if len(got) != len(b):
            got = _one_by_one(b, glossary)
        for src, en in zip(b, got):
            if en and _placeholders_ok(src, en):
                done[src] = en
            else:
                fixed = _one_by_one([src], glossary)
                if fixed and fixed[0] and _placeholders_ok(src, fixed[0]):
                    done[src] = fixed[0]
                else:
                    print(f"  ⚠ не переклалось (лишаю як є): {src[:70]}")
        if verbose:
            print(f"  пачка {i}/{len(batches)}: {len(b)} шматків")
    return done


def _one_by_one(items, glossary):
    out = []
    for s in items:
        try:
            res = _api([{"role": "system",
                         "content": SYSTEM + _glossary_block(glossary)},
                        {"role": "user",
                         "content": json.dumps({"segments": [s]},
                                               ensure_ascii=False)}])
            t = (res.get("t") or [""])[0]
        except Exception:
            t = ""
        out.append(t)
    return out


def _placeholders_ok(src, en):
    return sorted(PH_FIND.findall(src)) == sorted(PH_FIND.findall(en))


# --- складання сторінок ----------------------------------------------------

SWITCH_UK = ' · <a class="lang-sw" href="en/{name}" hreflang="en">English</a>'
SWITCH_EN = ' · <a class="lang-sw" href="../{name}" hreflang="uk">Українською</a>'
EYEBROW = re.compile(r'(<p class="eyebrow"[^>]*>)(.*?)(</p>)', re.S)


def head_block(lang, name):
    alt_uk = name if lang == "en" else f"../{name}" if False else name
    if lang == "en":
        uk_href, en_href = f"../{name}", name
    else:
        uk_href, en_href = name, f"en/{name}"
    return (f'<!doctype html><html lang="{lang}">'
            f'<meta charset="utf-8">'
            f'<link rel="alternate" hreflang="uk" href="{uk_href}">'
            f'<link rel="alternate" hreflang="en" href="{en_href}">\n')


def with_switch(html, lang, name):
    """Перемикач мови — у рядок-хлібні крихти вгорі сторінки."""
    link = (SWITCH_EN if lang == "en" else SWITCH_UK).format(name=name)
    if EYEBROW.search(html):
        html = EYEBROW.sub(lambda m: m.group(1) + m.group(2) + link + m.group(3),
                           html, count=1)
    else:
        html = html.replace("</h1>", "</h1>" + f'<p class="eyebrow">{link[3:]}</p>',
                            1)
    return head_block(lang, name) + html


def to_en_paths(html):
    """У /en/ спільні файли лежать на рівень вище."""
    html = re.sub(r'(src|href)="(assets/|knowledge/)', r'\1="../\2', html)
    return html.replace("url(assets/", "url(../assets/")


def build(only=None, dry=False, verbose=True):
    tm = load_tm()
    glossary = load_glossary()
    pages = sorted(p for p in DOCS.glob("*.html"))
    if only:
        pages = [p for p in pages if p.name in only]
        if not pages:
            sys.exit(f"нема таких сторінок у docs/: {only}")

    plans, missing = {}, []
    for p in pages:
        html = p.read_text()
        sp = plan(html)
        plans[p.name] = (html, sp)
        for s in sp:
            if s["src"] not in tm and s["src"] not in missing:
                missing.append(s["src"])

    words = sum(len(s.split()) for s in missing)
    print(f"сторінок: {len(pages)} · нових шматків: {len(missing)} (~{words} слів)")
    if dry:
        for s in missing[:20]:
            print("   ", s[:100])
        return
    if missing:
        tm.update(translate(missing, glossary, verbose))
        save_tm(tm)

    EN.mkdir(parents=True, exist_ok=True)
    for name, (html, sp) in plans.items():
        en_html = to_en_paths(render(html, sp, tm))
        (EN / name).write_text(with_switch(en_html, "en", name))
        (DOCS / name).write_text(with_switch(html, "uk", name))
        left = len(CYR.findall(re.sub(r"<script[^>]*application/ld\+json.*?</script>",
                                      "", (EN / name).read_text(), flags=re.S | re.I)))
        print(f"  en/{name:22} лишилось українських літер: {left}")
    print(f"готово: {len(plans)} сторінок у docs/en/")


def check():
    bad = 0
    for p in sorted(EN.glob("*.html")):
        txt = re.sub(r"<script[^>]*application/ld\+json.*?</script>", "",
                     p.read_text(), flags=re.S | re.I)
        hits = CYR.findall(txt)
        if hits:
            bad += 1
            frag = re.findall(r"[^\s<>]*[А-Яа-яЇїІіЄєҐґ][^\s<>]*", txt)[:6]
            print(f"{p.name}: {len(hits)} літер, напр. {frag}")
    print("чисто" if not bad else f"сторінок з українським текстом: {bad}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="перекласти лише ці сторінки")
    ap.add_argument("--dry", action="store_true", help="лише порахувати нове")
    ap.add_argument("--check", action="store_true", help="перевірити /en")
    a = ap.parse_args()
    if a.check:
        check()
    else:
        build(only=a.only, dry=a.dry)
