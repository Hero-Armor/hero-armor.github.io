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
* теги всередині шматка ховаються за мітки <x1/>, тож посилання й <b> лишаються
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
import time
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

MAX_SEGMENT = 900        # довші шматки ріжемо по <br> і реченнях
SKIP_SUBTREE = ("metadata", "defs")   # службові нутрощі SVG від matplotlib

TOKEN = re.compile(
    r"(?P<comment><!--.*?-->)"
    r"|(?P<script><script\b[^>]*>.*?</script>)"
    r"|(?P<style><style\b[^>]*>.*?</style>)"
    r"|(?P<tag><[^>]+>)"
    r"|(?P<text>[^<]+)", re.S | re.I)

TAG_NAME = re.compile(r"</?\s*([a-zA-Z][\w:-]*)")
# мітка тега: схожа на розмітку, тому модель її не переписує.
# Пробував ⟦n⟧ — на довгих абзацах модель губила дужку («⟧5⟧») і шматок
# доводилось лишати неперекладеним.
PH = "<x%d/>"
PH_FIND = re.compile(r"<x\d+/>")
PH_LOOSE = re.compile(r"<\s*/?\s*x\s*(\d+)\s*/?\s*>")


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
        i = int(re.search(r"\d+", m.group(0)).group(0))
        return tags[i] if i < len(tags) else ""
    return PH_FIND.sub(sub, text)


def _tidy(en):
    """Підрівняти мітки, якщо модель загубила дужку чи слеш."""
    return PH_LOOSE.sub(lambda m: PH % int(m.group(1)), en)


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
            if name in BLOCK:
                for fr in stack:             # «листком» не є жоден предок
                    fr[2] = True
            stack.append([name, m.end(), False])
            continue
        if not closing:                      # <br/>, <img …>
            if name in BLOCK:
                for fr in stack:
                    fr[2] = True
            continue

        # закриття: розкручуємо стек до свого імені (розмітка буває неохайна)
        while stack:
            open_name, inner_start, has_block = stack.pop()
            if open_name != name:
                continue
            if open_name in BLOCK and not has_block:
                inner = html[inner_start:m.start()]
                if CYR.search(inner):
                    for a, b in _chunks(html, inner_start, m.start()):
                        piece = html[a:b]
                        if not CYR.search(piece):
                            continue
                        src, tags = _protect(piece)
                        if src.strip():
                            spans.append({"start": a, "end": b,
                                          "src": src, "tags": tags})
                    covered.append((inner_start, m.start()))
            break

    spans.extend(_loose_text_spans(html, covered))
    spans.extend(_attr_spans(html))
    skip = _skip_ranges(html)
    spans = [s for s in spans
             if not any(a <= s["start"] and s["end"] <= b for a, b in skip)]
    spans.sort(key=lambda s: s["start"])
    return spans


def _skip_ranges(html):
    """Службові нутрощі SVG (RDF-метадані matplotlib) перекладати нема чого."""
    out = []
    for tag in SKIP_SUBTREE:
        for m in re.finditer(rf"<{tag}\b.*?</{tag}>", html, re.S | re.I):
            out.append((m.start(), m.end()))
    return out


def _chunks(html, start, end):
    """Розрізати задовгий шматок на шматки, які модель дійсно дотягує.

    Довгі абзаци (пам'ятка по стрічці — півтори тисячі символів і три десятки
    тегів) модель обривала на середині й губила мітки. Ріжемо по <br> і по
    кінцях речень, кожен шматок лишається цілою думкою.
    """
    if end - start <= MAX_SEGMENT:
        return [(start, end)]
    cuts = [start]
    for m in re.finditer(r"<br\s*/?>|(?<=[.;:!?])\s+(?=[^<])", html[start:end]):
        cuts.append(start + m.end())
    cuts.append(end)
    out, a = [], start
    for c in cuts[1:]:
        if c - a >= MAX_SEGMENT // 2:
            out.append((a, c))
            a = c
    if a < end:
        if out and end - a < 40:
            out[-1] = (out[-1][0], end)
        else:
            out.append((a, end))
    return out


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
- Preserve EVERY placeholder <x0/> <x1/> … byte for byte, same count, each \
exactly once, in the position that keeps the sentence natural. They stand for \
HTML tags — never renumber, merge, drop or reformat them.
- Do not translate proper names of people, brands, or file names.
- Some segments are labels on wiring diagrams or table headers: keep them as \
short as the original, abbreviate the way an electrician would.
- Never output Ukrainian or Russian text.

Return STRICT JSON: {"t": ["…", "…"]} — one string per input segment, same \
order, same count. No commentary."""


def _api(messages, tries=3):
    """Виклик моделі з повторами: мережа інколи відвалюється на довгій пачці."""
    body = json.dumps({"model": MODEL, "temperature": 0,
                       "response_format": {"type": "json_object"},
                       "messages": messages}).encode()
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(
                API_URL, data=body,
                headers={"Authorization": f"Bearer {KEY_FILE.read_text().strip()}",
                         "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                raw = json.loads(r.read())["choices"][0]["message"]["content"]
            return json.loads(raw)
        except Exception as e:               # мережа, таймаут, кривий JSON
            last = e
            time.sleep(3 * (attempt + 1))
    raise last


def _glossary_block(glossary):
    if not glossary:
        return ""
    lines = "\n".join(f"- {k} → {v}" for k, v in glossary.items())
    return f"\nGlossary — use these renderings consistently:\n{lines}\n"


def translate(missing, glossary, tm, verbose=True):
    """Перекласти нові рядки пачками, складаючи їх у памʼять по ходу.

    Памʼять пишеться після кожної пачки: якщо мережа впаде на середині,
    наступний запуск доплатить лише за залишок.
    """
    batch, size = [], 0
    batches = []
    for s in missing:
        if batch and (len(batch) >= 20 or size + len(s) > 3500):
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
            got = _api(msgs).get("t") or []
        except Exception as e:
            print(f"  пачка {i}: збій API ({e}) — пробую поштучно")
            got = []
        if len(got) != len(b):
            got = _one_by_one(b, glossary)
        for src, en in zip(b, got):
            en = _tidy(en or "")
            if en and _placeholders_ok(src, en):
                tm[src] = en
                continue
            fixed = _tidy((_one_by_one([src], glossary) or [""])[0] or "")
            if fixed and _placeholders_ok(src, fixed):
                tm[src] = fixed
            else:
                print(f"  ⚠ не переклалось (лишаю як є): {src[:70]}")
        save_tm(tm)
        if verbose:
            print(f"  пачка {i}/{len(batches)}: {len(b)} шматків")
    return tm


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


HEAD_MARK = re.compile(r'^<!doctype html><html lang="\w+">.*?\n', re.S | re.I)
SWITCH_MARK = re.compile(r' · <a class="lang-sw"[^>]*>[^<]*</a>')


def strip_injected(html):
    """Прибрати шапку й перемикач, дописані минулою збіркою.

    Без цього друга збірка перекладала б власний перемикач і клеїла другу
    шапку — сторінка з кожним разом обростала б сміттям.
    """
    html = HEAD_MARK.sub("", html)
    return SWITCH_MARK.sub("", html)


def head_block(lang, name):
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
        html = strip_injected(p.read_text())
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
        translate(missing, glossary, tm, verbose)

    EN.mkdir(parents=True, exist_ok=True)
    for name, (html, sp) in plans.items():
        en_html = to_en_paths(render(html, sp, tm))
        (EN / name).write_text(with_switch(en_html, "en", name))
        (DOCS / name).write_text(with_switch(html, "uk", name))
        left = len(CYR.findall(_visible_only((EN / name).read_text())))
        print(f"  en/{name:22} лишилось українських літер: {left}")
    print(f"готово: {len(plans)} сторінок у docs/en/")


def _visible_only(html):
    """Те, що бачить читач: без машинних даних і без наших коментарів у коді."""
    html = re.sub(r"<script[^>]*application/ld\+json.*?</script>", "", html,
                  flags=re.S | re.I)
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    html = SWITCH_MARK.sub("", html)      # «Українською» на кнопці — це навмисне
    return re.sub(r"//[^\n]*", "", html)


def check():
    bad = 0
    for p in sorted(EN.glob("*.html")):
        txt = _visible_only(p.read_text())
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
