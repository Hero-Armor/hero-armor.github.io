#!/usr/bin/env python3
"""
Hero Armor — project-level site builder.

  data/*.json (shared) + <system>/data + <system>/model  ->  docs/ site

Pages: index (project overview: hero image, systems, shared BOM, team),
audio (decisions + schematic), lab (interactive simulator), ops (tasks/orders),
plus knowledge.jsonld (schema.org JSON-LD graph of everything).

Adding a system: rows in shared data with its `system` tag + a card in
data/systems.json; its own data/ + model/ folder when engineering starts.

Usage:  python3 build.py [--copy-to DIR] [--docs]
        --copy-to DIR   copy artifact mirrors (Claude artifact publish paths)
        --docs          write docs/ for GitHub Pages (relative links; private
                        logistics data HARD-excluded)
"""

import argparse
import base64
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA, SITE, OUT = ROOT / "data", ROOT / "site", ROOT / "dashboard"
AUDIO, LIGHTS, SOLAR = ROOT / "audio", ROOT / "lights", ROOT / "solar"
sys.path.insert(0, str(AUDIO / "model"))
sys.path.insert(0, str(LIGHTS / "model"))
sys.path.insert(0, str(SOLAR / "model"))
import audio_node_model as m  # noqa: E402  (reads audio/data/*)
import lights_node_model as lm  # noqa: E402  (reads lights/data/*)
import lamp_bench as lb  # noqa: E402  (стенд ламп прожектора, lights/data/lamp_bench.json)
import spot_ring as sr  # noqa: E402  (звʼязка 8 прожекторів: схема, диммер, запобіжник)
import strip_bench as sb  # noqa: E402  (стенд LED-стрічки, lights/data/strip_bench.json)
import circuit_lab as cl  # noqa: E402  (окремі сторінки-калькулятори по типах світла)
import strip_layout as stl  # noqa: E402  (план стрічки в подіумі + монтаж і закупівля)
import back_core as bcore  # noqa: E402  (ядро на спині: модуль, вікно, ТЗ друкарю)
import power_node_model as pw
sys.path.insert(0, str(ROOT / "enclosure" / "model"))
import enclosure_model as enc  # noqa: E402  (pulls demand from lights + audio)

BOM = json.loads((DATA / "bom.json").read_text())
DECISIONS = json.loads((DATA / "decisions.json").read_text())
# Архівні рішення (закриті теми) не показуємо серед чинних — лише в історії,
# щоб база не суперечила сама собі й закрите питання не спливало як живе.
ARCHIVED = [d for d in DECISIONS if d.get("archived")]
DECISIONS = [d for d in DECISIONS if not d.get("archived")]
TASKS = json.loads((DATA / "tasks.json").read_text())
ORDERS = json.loads((DATA / "orders.json").read_text())
ADDR = json.loads((DATA / "addresses.json").read_text())
SYSTEMS_REG = json.loads((DATA / "systems.json").read_text())
LABS = json.loads((DATA / "labs.json").read_text())

# Хто вирішує. Єдиного «головного» немає: кожен головний у своїй зоні.
DECIDERS = {"ivan": "Іван", "liza": "Ліза", "volodymyr": "Володимир (конструктор)",
            "pavlo": "Павло", "team": "команда"}
PROJ = json.loads((DATA / "project.json").read_text())
PLAYBOOKS = json.loads((DATA / "playbooks.json").read_text())
PRIVATE_FILE = DATA / "private" / "private.json"
PRIVATE = json.loads(PRIVATE_FILE.read_text()) if PRIVATE_FILE.exists() else {}
if __import__("os").environ.get("CI"):
    PRIVATE = {}  # CI/Pages builds must never see tracking numbers or addresses
P = m.P

SITE_URL = "https://hero-armor.github.io/"
ART_MAIN = "https://claude.ai/code/artifact/b5f9223c-1934-413a-9557-be9204d2572b"
ART_LAB = "https://claude.ai/code/artifact/822f630a-a99b-4f3b-98cf-bef6e216dced"
ART_OPS = "https://claude.ai/code/artifact/5ca1ebd7-1356-4457-8362-812703167859"
ART_TASKS = "https://claude.ai/code/artifact/8bd7dba2-027a-472a-9bb3-3d7a495a9ec1"
LIGHTS_LAB_URL = SITE_URL + "lights_lab.html"
SOLAR_LAB_URL = SITE_URL + "solar_lab.html"
ENCLOSURE_LAB_URL = SITE_URL + "enclosure_lab.html"
CABLES_LAB_URL = SITE_URL + "cables_lab.html"

SYSTEMS = ["project", "audio", "solar", "lights", "armor"]
SYS_LABEL = {"project": "Проєкт", "audio": "Аудіо", "solar": "Живлення",
              "lights": "Світло", "armor": "Броня"}
# нові системи з реєстру підхоплюються самі — інакше запис із свіжим system
# роняє збірку по KeyError (спіймано 31.07 на «enclosure»)
SYS_LABEL.update({c["key"]: c["label"] for c in SYSTEMS_REG
                  if c["key"] not in SYS_LABEL})
COMP_STATUS_LABEL = {"design-ready": "дизайн готовий", "in-design": "проєктується",
                     "build": "збірка", "concept": "концепт"}
TASK_STATUS = {"doing": "в роботі", "waiting": "чекаємо", "todo": "до роботи", "done": "готово"}


def task_status(t):
    """Підпис статусу задачі, який НЕ валить складача через незнайоме слово.

    07.08.2026: у data/tasks.json приїхав статус «open», якого в словнику немає —
    `build.py --docs` упав з KeyError, а це рівно та команда, якою збирається сайт
    на GitHub. Один зайвий статус не має гасити весь портал: показуємо його як є
    і голосно попереджаємо в логу складача.
    """
    st = t.get("status", "")
    if st not in TASK_STATUS:
        print(f'warn: незнайомий статус задачі «{st}» — {t.get("task", "")[:60]}')
        return st
    return TASK_STATUS[st]
ORDER_STATUS = {"ordered": "замовлено", "shipped": "їде", "delivered": "доставлено",
                "received": "отримано", "returned": "повернуто"}
PILL = {"have": ("have", "у списку"), "add": ("add", "додати"), "tbd": ("tbd", "обрати")}


def pill_of(b):
    """Значок стану позиції закупівлі. Веде `flow`; `status` — спадщина.

    Тонкість, на якій збірка падала 08.08.2026: запис виду
    `FLOW.get(b.get("flow"), PILL[b["status"]])` обчислює запасний варіант ЗАВЖДИ,
    навіть коли `flow` є. Тому позиція з порожнім чи чужим `status` валила весь
    build з `KeyError: ''` — а таку позицію створював `hero_armor_promote.py accept`.
    Тут запасний варіант береться ліниво і ніколи не кидає.
    """
    f = FLOW.get(b.get("flow"))
    if f:
        return f
    return PILL.get(b.get("status"), ("tbd", "обрати"))
# Ланцюг статусів Івана: замовити -> їде -> приїхало. Виводиться з даних
# (bom.status + активні замовлення), руками ніде не дублюється.
FLOW = {"to_order": ("add", "замовити"), "in_cart": ("add", "у кошику"),
        "ordered": ("tbd", "їде"), "arrived": ("have", "приїхало"),
        "returned": ("tbd", "повернуто"), "dropped": ("tbd", "знято")}
FLOW_LABEL = {"to_order": "Замовити", "in_cart": "У кошику", "ordered": "Їде",
              "arrived": "Приїхало", "returned": "Повернуто", "dropped": "Знято"}
# Стани, за які ще треба заплатити. «Знято» і «повернуто» у бюджет не йдуть:
# перше — відхилений варіант, друге — гроші вже повернулись.
FLOW_TOBUY = ("to_order", "in_cart")
FLOW_HAVE = ("arrived", "ordered")
ORDER_STATUS_LD = {"ordered": "OrderProcessing", "shipped": "OrderInTransit",
                   "delivered": "OrderDelivered", "received": "OrderDelivered",
                   "returned": "OrderReturned"}
ACTION_STATUS_LD = {"todo": "PotentialActionStatus", "doing": "ActiveActionStatus",
                    "waiting": "PotentialActionStatus", "done": "CompletedActionStatus"}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")[:60]


def tmpl(name):
    return (SITE / "templates" / name).read_text()


def usd(price_str):
    """First $-amount in a BOM price string ('$17/3шт' -> 17.0), 0 if none.

    Кому-роздільник тисяч теж рахуємо: «$1,599.00» раніше давало 0 — станція
    за півтори тисячі мовчки випадала з бюджету (спіймано 07.08.2026).
    """
    mm = re.search(r"\$(\d[\d,]*(?:\.\d+)?)", price_str or "")
    return float(mm.group(1).replace(",", "")) if mm else 0.0


def figures_html(key):
    """Креслення з картки системи — одна домівка (site/assets) для всіх сторінок.

    Кастомні сторінки (звук/світло/живлення) раніше не показували `figures`
    взагалі: їх малює лише універсальний шаблон. Через це прийняті креслення
    лежали в assets, але на сторінку не потрапляли.
    """
    reg = next((c for c in SYSTEMS_REG if c["key"] == key), None)
    figs = (reg or {}).get("figures") or []
    if not figs:
        return ""
    cards = "\n".join(
        f'    <div class="fig"><img src="{f[0]}" alt="{esc(f[1])}" loading="lazy">'
        f'<p>{esc(f[1])}</p></div>' for f in figs)
    return f'  <h2>Креслення</h2>\n  <div class="figs">\n{cards}\n  </div>\n'


def photos_html(key):
    """Фото з місця — окремо від креслень.

    Іван 02.08 знайшов у «Кресленнях» фото коробок з динаміками: фотографія
    з чату — це не креслення, і в тому розділі вона бреше. Фото цінні (видно,
    що фактично лежить у людей на руках), тому не викидаємо, а виносимо сюди.
    """
    reg = next((c for c in SYSTEMS_REG if c["key"] == key), None)
    pics = (reg or {}).get("photos") or []
    if not pics:
        return ""
    cards = "\n".join(
        f'    <div class="fig"><img src="{p[0]}" alt="{esc(p[1])}" loading="lazy">'
        f'<p>{esc(p[1])}</p></div>' for p in pics)
    return f'  <h2>Фото з місця</h2>\n  <div class="figs">\n{cards}\n  </div>\n'


def diagrams_html(key, heading="Схеми", extra=None):
    """Схеми системи, вставлені ТЕКСТОМ SVG, а не картинкою.

    Так підписи на схемі лишаються справжнім текстом — англійська версія сайту
    їх перекладає, а пошук їх бачить. Реєструються в data/systems.json полем
    `diagrams`: [["lights/model/podium_plan.svg", "підпис"], ...].
    Файл, якого ще нема, просто пропускається з попередженням — щоб не валити
    збірку, поки схему домальовують.

    Тап по схемі відкриває її на весь екран з горизонтальною прокруткою — на
    телефоні дрібні підписи інакше не роздивишся, а Іван читає хаб з айфона.

    У темній темі схема лишається на світлій підкладці, як аркуш креслення:
    малюють їх тушшю по світлому, і на темному фоні темні підписи зникали
    (спіймано на сторінці броні 01.08). Пояснення тримаємо тут, а не коментарем
    у CSS: український коментар усередині <style> протікав в англійську версію.
    """
    if key == "index":
        dias = [["lights/model/podium_plan.svg",
                 "Подіум згори: вісім стійок із прожекторами, рукави стрічки, "
                 "24 врізних вогні по торцю, катафоти на кутах і кабель до ящика станції"],
                ["solar/model/site_plan.svg",
                 "Те саме на місці: подіум, ящик станції за 7.6 м, сонячний масив, "
                 "траса кабелю і бік, з якого вночі підʼїжджають"]]
    else:
        reg = next((c for c in SYSTEMS_REG if c["key"] == key), None)
        dias = list((reg or {}).get("diagrams") or [])
    if extra:
        dias = list(dias) + list(extra)
    cards = []
    for path_, cap in dias:
        f = ROOT / path_
        if not f.exists():
            print(f"warn: нема схеми {path_} — прожени її генератор")
            continue
        svg = f.read_text()
        svg = svg[svg.index("<svg"):]
        cards.append(f'    <figure class="dia">\n{svg}\n'
                     f'      <p class="zoomhint">торкнись схеми, щоб розгорнути на весь екран</p>\n'
                     f'      <figcaption>{esc(cap)}</figcaption>\n    </figure>')
    if not cards:
        return ""
    css = ("  <style>\n"
           "    .dias { display: grid; gap: 1.2rem; margin-bottom: 1.4rem; }\n"
           "    .dia { margin: 0; border: 1px solid var(--line); border-radius: 8px;\n"
           "           background: var(--panel); padding: 1rem 1rem .8rem; }\n"
           "    @media (prefers-color-scheme: dark) {\n"
           "      :root:not([data-theme=\'light\']) .dia,\n"
           "      :root:not([data-theme=\'light\']) .diazoom { background: #f4f1e6; }\n"
           "      :root:not([data-theme=\'light\']) .dia figcaption,\n"
           "      :root:not([data-theme=\'light\']) .dia .zoomhint { color: #6b675c; }\n"
           "    }\n"
           "    :root[data-theme=\'dark\'] .dia,\n"
           "    :root[data-theme=\'dark\'] .diazoom { background: #f4f1e6; }\n"
           "    :root[data-theme=\'dark\'] .dia figcaption,\n"
           "    :root[data-theme=\'dark\'] .dia .zoomhint { color: #6b675c; }\n"
           "    .dia svg { width: 100%; height: auto; display: block; cursor: zoom-in; }\n"
           "    .dia figcaption { font-size: .8rem; color: var(--ink-2); margin-top: .7rem;\n"
           "                      max-width: 70ch; }\n"
           "    .dia .zoomhint { display: none; font-size: .72rem; color: var(--ink-2);\n"
           "                     font-family: var(--mono); margin-top: .5rem; }\n"
           "    @media (max-width: 780px) { .dia .zoomhint { display: block; } }\n"
           "    .diazoom { position: fixed; inset: 0; z-index: 200; background: var(--bg);\n"
           "               overflow: auto; padding: 3rem .5rem 2rem; }\n"
           "    .diazoom svg { width: 260%; max-width: none; height: auto; }\n"
           "    @media (min-width: 781px) { .diazoom svg { width: 100%; } }\n"
           "    .diazoom .x { position: fixed; top: .6rem; right: .8rem; z-index: 201;\n"
           "                  border: 1px solid var(--line); background: var(--panel);\n"
           "                  color: var(--ink); border-radius: 999px; width: 2.2rem;\n"
           "                  height: 2.2rem; font-size: 1.1rem; cursor: pointer; }\n"
           "  </style>\n"
           "  <script>\n"
           "  document.addEventListener('click', function (e) {\n"
           "    const svg = e.target.closest('.dia svg');\n"
           "    if (!svg) return;\n"
           "    const box = document.createElement('div');\n"
           "    box.className = 'diazoom';\n"
           "    box.innerHTML = '<button class=\\'x\\' aria-label=\\'закрити\\'>&times;</button>';\n"
           "    box.appendChild(svg.cloneNode(true));\n"
           "    box.addEventListener('click', function (ev) {\n"
           "      if (ev.target.classList.contains('x') || ev.target === box) box.remove();\n"
           "    });\n"
           "    document.body.appendChild(box);\n"
           "  });\n"
           "  </script>\n")
    head = f'  <h2>{esc(heading)}</h2>\n' if heading else ""
    return (head + f'{css}  <div class="dias">\n'
            + "\n".join(cards) + "\n  </div>\n")


LAB_CSS = """<style>
  .labs-strip { display: flex; flex-wrap: wrap; align-items: center; gap: .4rem;
    margin: 0 0 1.4rem; padding: .5rem .7rem; border: 1px solid var(--line);
    border-radius: 8px; background: var(--panel); }
  .labs-strip .lead { font-family: var(--mono); font-size: .72rem;
    letter-spacing: .04em; text-transform: uppercase; color: var(--ink-2);
    margin-right: .2rem; }
  .labs-strip a { font-size: .84rem; text-decoration: none; color: var(--ink-2);
    padding: .2rem .55rem; border-radius: 6px; border: 1px solid transparent; }
  .labs-strip a:hover { color: var(--ink); background: var(--panel-2);
    border-color: var(--line); }
  .labs-strip a.here { color: var(--ink); background: var(--panel-2);
    border-color: color-mix(in srgb, var(--accent) 45%, var(--line));
    font-weight: 600; }
</style>"""


def labs_strip_html(active=None):
    """Смужка переходу між лабораторіями.

    Іван 31.07: «дуже тяжко знайти лабораторію, а лабораторія — найцікавіше».
    Раніше в лабораторію вів один лінк з картки системи, і з однієї
    лабораторії не було видно решти. Тепер вони знають одна про одну.
    """
    links = "".join(
        f'<a class="lab{" here" if l["page"] == active else ""}" '
        f'href="{SITE_URL}{l["page"]}">{l["emoji"]} {esc(l["short"])}</a>'
        for l in LABS)
    return (LAB_CSS + '\n  <nav class="labs-strip" aria-label="Лабораторії">'
            '<span class="lead">Лабораторії</span>' + links + '</nav>\n')


def _sys_label(key):
    """Назва системи для мітки: реєстр систем ширший за старий SYS_LABEL."""
    reg = next((c for c in SYSTEMS_REG if c["key"] == key), None)
    return ((reg or {}).get("label") or SYS_LABEL.get(key, key)).lower()


def labs_cards_html():
    """Блок лабораторій на головній — з поясненням, що там можна покрутити."""
    out = []
    for l in LABS:
        subs = "".join(
            f'<a href="{SITE_URL}{href}">{esc(label)}</a>'
            + (" · " if i < len(l["sub"]) - 1 else "")
            for i, (label, href) in enumerate(l["sub"]))
        sub_row = f'      <div class="row"><span class="links">{subs}</span></div>\n' if subs else ""
        out.append(
            f'    <div class="card lab-card">\n'
            f'      <div class="row"><h3><a href="{SITE_URL}{l["page"]}">'
            f'{l["emoji"]} {esc(l["title"])}</a></h3>'
            f'<span class="pill">{esc(_sys_label(l["system"]))}</span></div>\n'
            f'      <p>{esc(l["knob"])}</p>\n{sub_row}'
            f'    </div>')
    return "\n".join(out)


def assembly_html():
    """Монтаж вузла: план панелі, вимоги до коробки, конектори, всі з'єднання.

    Дані — audio/data/assembly.json (габарити і дроти), малюнок —
    audio/model/assembly.py. Тут тільки розкладка по HTML, жодної цифри руками.
    """
    a = json.loads((AUDIO / "data" / "assembly.json").read_text())
    svg = (AUDIO / "model" / "assembly.svg").read_text()
    svg = re.sub(r"<\?xml[^>]*\?>\s*|<!DOCTYPE[^>]*>\s*|<!--.*?-->\s*", "", svg, flags=re.S)

    enc, mi = a["enclosure"], a["enclosure"]["min_inner_mm"]
    reqs = "\n".join(f"      <li>{esc(r['text'])}</li>" for r in enc["requirements"])
    conns = "\n".join(
        f'      <tr><td>{esc(c["iface"])}</td><td>{esc(c["conn"])}</td>'
        f'<td>{esc(c.get("note", ""))}</td></tr>' for c in a["connectors"])
    wires = "\n".join(
        f'      <tr><td class="num">{w["n"]}</td><td>{esc(w["from"])}</td><td>{esc(w["to"])}</td>'
        f'<td class="num">{esc(str(w["awg"]))}</td><td class="num">{esc(w["len"])}</td>'
        f'<td>{esc(w["color"])}</td><td>{esc(w.get("note", ""))}</td></tr>'
        for w in a["wires"])
    steps = "\n".join(f"      <li>{esc(s)}</li>" for s in a["steps"])
    tests = "\n".join(f"      <li>{esc(t)}</li>" for t in a["tests"])

    # Плата підписує піни іменами, а не номерами GPIO — без цієї таблиці людина
    # з паяльником шукає на шовкографії «16» і не знаходить (Іван, 02.08.2026).
    board_html = ""
    brd = a.get("board")
    if brd:
        silk_rows = "\n".join(
            f'      <tr><td>{esc(g)}</td><td><b>{esc(mark)}</b></td></tr>'
            for g, mark in brd["silk"].items())
        rows_html = "\n".join(
            f'      <li><b>{esc(name)}:</b> {esc(" · ".join(pins))}</li>'
            for name, pins in brd["rows"].items())
        board_html = (
            f'  <h3>Плата ESP32 — як підписані піни</h3>\n'
            f'  <p class="files"><a href="{brd["url"]}">{esc(brd["name"])}</a>. {esc(brd["why"])}</p>\n'
            f'  <ul class="files">\n{rows_html}\n  </ul>\n'
            f'  <div class="tbl-wrap"><table>\n'
            f'    <tr><th>У схемі</th><th>Шукати на платі</th></tr>\n{silk_rows}\n'
            f'  </table></div>\n'
            f'  <p class="files">{esc(brd["note"])}</p>\n')

        fp = brd.get("first_power")
        if fp:
            st = "\n".join(f'      <li>{esc(x)}</li>' for x in fp["steps"])
            board_html += (
                f'  <h3>{esc(fp["title"])}</h3>\n'
                f'  <ol class="files">\n{st}\n  </ol>\n'
                f'  <p class="files">{esc(fp["note"])}</p>\n')

        dac = brd.get("dac")
        if dac:
            board_html += (
                f'  <h3>ЦАП — що куди і як швидко перевірити</h3>\n'
                f'  <p class="files"><a href="{dac["url"]}">{esc(dac["name"])}</a>. {esc(dac["pins"])}</p>\n'
                f'  <p class="files">{esc(dac.get("what_is", ""))}</p>\n'
                f'  <p class="files"><b>Підключення:</b> {esc(dac["wire"])}</p>\n'
                f'  <p class="files"><b>💡 {esc(dac["trick"])}</b></p>\n')
            if dac.get("check"):
                items = "\n".join(f'      <li>{esc(x)}</li>' for x in dac["check"])
                board_html += f'  <ol class="files">\n{items}\n  </ol>\n'

        usb = brd.get("usb")
        if usb:
            board_html += (
                f'  <h3>{esc(usb["title"])}</h3>\n'
                f'  <p class="files">{esc(usb["text"])}</p>\n'
                f'  <p class="files"><b>⚠ {esc(usb["watch"])}</b></p>\n')

        bench = brd.get("bench")
        if bench:
            board_html += (
                f'  <h3>{esc(bench["title"])}</h3>\n'
                f'  <p class="files">{esc(bench["text"])}</p>\n'
                f'  <p class="files"><b>⚠ {esc(bench["watch"])}</b></p>\n')

        amp = brd.get("amp")
        if amp:
            t_rows = "\n".join(
                f'      <tr><td><b>{esc(t)}</b></td><td>{esc(txt)}</td></tr>'
                for t, txt in amp["terminals"])
            board_html += (
                f'  <h3>Підсилювач — що на які клеми</h3>\n'
                f'  <p class="files"><a href="{amp["url"]}">{esc(amp["name"])}</a>. {esc(amp["note"])}</p>\n'
                f'  <div class="tbl-wrap"><table>\n'
                f'    <tr><th>Клема</th><th>Що туди йде</th></tr>\n{t_rows}\n'
                f'  </table></div>\n'
                f'  <p class="files">{esc(amp.get("mono_note", ""))}</p>\n'
                f'  <p class="files"><b>⚠ {esc(amp["warning"])}</b></p>\n')

    pick, pick_html = enc.get("pick"), ""
    if pick:
        alt = pick.get("alt") or {}
        pick_html = (
            f'  <p class="files"><b>Якщо своя не підійде — беремо цю:</b> '
            f'<a href="{pick["url"]}">{esc(pick["item"])}</a>, {esc(pick["price"])}. '
            f'{esc(pick["why"])} Кріплення плати: {esc(pick["mounting"])}'
            + (f' Альтернатива — <a href="{alt["url"]}">{esc(alt["item"])}</a>, '
               f'{esc(alt["price"])}: {esc(alt["why"])}.' if alt else "") + "</p>\n")

    return f"""  <div class="fig">{svg}</div>
  <p class="fig-cap">План панелі-основи в масштабі. Джерело:
  <span style="font-family:var(--mono)">audio/data/assembly.json</span> →
  <span style="font-family:var(--mono)">audio/model/assembly.py</span>.</p>

  <h3>Коробка — сім вимог</h3>
  <p class="files">Мінімум усередині {mi['l']}×{mi['w']}×{mi['h']} мм,
  матеріал — {esc(enc['material'])}, захист {esc(enc['ip'])}. {esc(enc['note'])}</p>
  <ul class="files">
{reqs}
  </ul>
{pick_html}
  <h3>Конектори — де вузол розбирається</h3>
  <div class="tbl-wrap"><table>
    <tr><th>Місце</th><th>Конектор</th><th>Чому так</th></tr>
{conns}
  </table></div>

{board_html}
  <h3>Усі з'єднання</h3>
  <div class="tbl-wrap"><table>
    <tr><th>№</th><th>Звідки</th><th>Куди</th><th>AWG</th><th>Довжина</th><th>Колір</th><th>Примітка</th></tr>
{wires}
  </table></div>

  <h3>Порядок збірки</h3>
  <ol class="files">
{steps}
  </ol>

  <h3>Перевірка після збірки</h3>
  <ol class="files">
{tests}
  </ol>
"""


def dest_label(o):
    """Куди їде замовлення. Адреса може бути ще не з'ясована (щойно замовили і
    не подивились у підтвердженні) — тоді кажемо про це прямо, а не падаємо."""
    return ADDR["locations"].get(o.get("deliver_to"), {}).get("label", "адресу уточнити")


def photo_wall_html(rows, heading="Що це фізично"):
    """Смужка справжніх фото товарів — «щоб було видно, про що мова».

    Іван 01.08: «додай всюди більше картинок про що йде мова». На сторінках
    типів світла це відповідає на найпростіше питання: як воно виглядає в руках.
    Фото тягне site/bom_media.py, підпис — назва позиції з BOM.
    """
    cards = []
    for b in rows:
        if not b.get("img"):
            continue
        inner = (f'<img src="{b["img"]}" alt="{esc(b["item"])}" loading="lazy">'
                 f'<span>{esc(b["item"])}</span>')
        cards.append(f'      <a class="pw-item" href="{esc(b["url"])}">{inner}</a>'
                     if b.get("url") else f'      <div class="pw-item">{inner}</div>')
    if not cards:
        return ""
    css = ("  <style>\n"
           "    .pw { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));\n"
           "          gap: .8rem; margin: .2rem 0 1.4rem; }\n"
           "    .pw-item { display: block; text-decoration: none; color: inherit;\n"
           "               border: 1px solid var(--line); border-radius: 8px;\n"
           "               background: var(--panel); padding: .6rem; }\n"
           "    .pw-item img { width: 100%; aspect-ratio: 1/1; object-fit: contain;\n"
           "                   background: #fff; border-radius: 6px; display: block; }\n"
           "    .pw-item span { display: block; font-size: .74rem; color: var(--ink-2);\n"
           "                    margin-top: .45rem; line-height: 1.35; }\n"
           "  </style>\n")
    return f'  <h2>{esc(heading)}</h2>\n{css}  <div class="pw">\n' + "\n".join(cards) + "\n  </div>\n"


def buy_table_html(rows, note=""):
    """Таблиця «що з цього купити» — з мініатюрою товару в першій колонці."""
    if not rows:
        return ""
    body = "".join(
        f'<tr>{bom_thumb(b)}<td>'
        + (f'<a href="{esc(b["url"])}">{esc(b["item"])}</a>' if b.get("url") else esc(b["item"]))
        + f'</td><td>{esc(str(b.get("qty", "—")))}</td>'
          f'<td class="num">{esc(str(b.get("price", "—")))}</td>'
          f'<td><span class="pill {pill_of(b)[0]}">'
          f'{pill_of(b)[1]}</span></td>'
          f'<td>{esc(b.get("where", "—"))}</td>'
          f'<td style="white-space:normal;max-width:56ch">{esc(b.get("note", ""))}</td></tr>'
        for b in rows)
    tail = f'<p class="fig-cap">{esc(note)}</p>' if note else ""
    # стилі мініатюри тримаємо тут, а не в шаблоні: таблиця вставляється на
    # різні сторінки, і кожна має показати фото однаково маленьким
    css = ("<style>\n"
           "  td.pic { width: 62px; padding: .35rem .4rem .35rem .8rem; }\n"
           "  td.pic img { width: 54px; height: 54px; object-fit: contain; border-radius: 6px;\n"
           "               background: #fff; border: 1px solid var(--line); display: block; }\n"
           "  td.pic .nopic { width: 54px; height: 54px; border-radius: 6px;\n"
           "                  border: 1px dashed var(--line); display: block; }\n"
           "  td.pic .nopic-t { display: flex; align-items: center; justify-content: center;\n"
           "                    text-align: center; font-family: var(--mono); font-size: .58rem;\n"
           "                    line-height: 1.15; color: var(--ink-2); padding: .2rem; }\n"
           "</style>")
    return (css + '<h2>Що з цього треба купити</h2><div class="tbl-wrap"><table>'
            '<thead><tr><th></th><th>Позиція</th><th>Скільки</th><th>Ціна</th>'
            '<th>Стан</th><th>Де купуємо</th><th>Навіщо</th></tr></thead><tbody>' + body
            + '</tbody></table></div>' + tail)


def bom_thumb(b):
    """Мініатюра товару для таблиці закупівлі.

    Фото тягне site/bom_media.py зі сторінки товару (через свій Firecrawl) і
    кладе в site/assets/bom/. Сенс простий: у таблиці має бути видно, ПРО ЩО
    позиція, без відкривання лінка (прохання Івана). Нема фото — лишається
    пунктирна рамка, щоб рядки не стрибали.
    """
    img = b.get("img")
    if not img:
        # Порожня клітинка читається як «забув». Якщо товар свідомо ще не
        # обраний або робиться самотужки — так і пишемо словом (Іван 01.08).
        note = esc(b.get("img_note", ""))
        inner = (f'<span class="nopic nopic-t">{note}</span>' if note
                 else '<span class="nopic"></span>')
        return f'<td class="pic">{inner}</td>'
    tag = f'<img src="{img}" alt="{esc(b["item"])}" loading="lazy">'
    if b.get("url"):
        tag = f'<a href="{b["url"]}" title="{esc(b["item"])}">{tag}</a>'
    return f'<td class="pic">{tag}</td>'


def buy_block_html(systems, match=None, note="", heading="Що це фізично"):
    """Блок закупівлі для сторінки: смужка фото + таблиця «що з цього купити».

    Правило Івана 01.08 і повторно 02.08: сторінка, де згадана річ, яку можна
    купити, зобовʼязана показати, ЩО САМЕ купувати і по якому лінку — інакше
    вона не готова. Реєстр закупівлі один (data/bom.json), тут лише зріз:
    по системі, а за потреби ще й по словах `match` із даних підсистеми.
    Порожній зріз — це майже завжди помилка в match, тому кажемо про це вголос.
    """
    if isinstance(systems, str):
        systems = (systems,)
    rows = [b for b in BOM if b.get("system") in systems]
    if match:
        rows = [b for b in rows
                if any(m.lower() in (b["item"] + b.get("note", "")).lower() for m in match)]
    if not rows:
        print(f"warn: закупівля порожня для {systems} — перевір buy.match")
        return ""
    return photo_wall_html(rows, heading) + buy_table_html(rows, note)


def _cables_buy_block():
    """Зріз закупівлі під кабельну лабораторію.

    Тут, на відміну від сторінок систем, потрібен саме вузький зріз: сторінка
    про переріз і просадку, отже показуємо кабель, запобіжники, клеми і гофру,
    а не всю систему. Слова живуть у lights/data/params.json -> wiring.buy.
    """
    cfg = lm.P["wiring"].get("buy") or {}
    return buy_block_html(("lights", "solar"), cfg.get("match"), cfg.get("note", ""))


def bom_rows_html():
    rows = []
    for b in BOM:
        cls, label = pill_of(b)
        item = esc(b["item"])
        if b.get("url"):
            item = f'<a href="{b["url"]}">{item}</a>'
        rows.append(
            f'      <tr data-status="{b.get("flow") or b.get("status") or "tbd"}">{bom_thumb(b)}<td>{item}</td>'
            f'<td><span class="chip {b["system"]}">{b["system"]}</span></td>'
            f'<td class="num">{b["qty"]}</td>'
            f'<td class="num">{b["price"]}</td><td><span class="pill {cls}">{label}</span></td>'
            f'<td>{esc(b.get("where", "—"))}</td>'
            f'<td>{esc(b["note"])}</td></tr>')
    return "\n".join(rows)


def build_knowledge():
    """Everything in data/ as a schema.org JSON-LD @graph. Public by design:
    city-level addresses only, never tracking numbers."""
    reg = {c["key"]: c for c in SYSTEMS_REG}
    graph = [{
        "@id": "#project", "@type": "Project", "name": "Hero Armor",
        "description": "Memorial art installation for Burning Man 2026 honoring "
                       "Ukrainian defenders, in memory of Zakhar Zakharov — a "
                       "guardian figure that speaks with his voice when someone "
                       "approaches (LD2410C radar → ESP32 → PCM5102A → TPA3116D2).",
        "url": "https://hero-armor.com/",
        "sameAs": [SITE_URL, "https://github.com/Hero-Armor/hero-armor.github.io"],
        "image": "https://hero-armor.com/images/hero-render.jpg",
        "hasPart": [{"@id": f"#sub-{c}"} for c in SYSTEMS if c != "project"],
    }, {
        "@id": "#event", "@type": "Event", "name": PROJ["event"]["name"],
        "startDate": PROJ["event"]["gate_open"], "endDate": PROJ["event"]["end"],
        "location": {"@type": "Place", "name": PROJ["event"]["location"]},
        "workFeatured": {"@id": "#project"},
    }]
    for c in SYSTEMS:
        if c == "project":
            continue
        node = {"@id": f"#sub-{c}", "@type": "Project",
                "name": f"Hero Armor — {SYS_LABEL[c]}",
                "parentOrganization": {"@id": "#project"}}
        if c in reg:
            node["description"] = reg[c]["summary"]
            node["additionalProperty"] = [{"@type": "PropertyValue",
                                           "name": "status", "value": reg[c]["status"]}]
        graph.append(node)

    def sys_ref(c):
        return {"@id": "#project" if c == "project" else f"#sub-{c}"}

    bom_ids = {}
    for b in BOM:
        bid = f"#bom-{slug(b['item'])}"
        bom_ids[b["item"]] = bid
        node = {"@id": bid, "@type": "Product", "name": b["item"],
                "description": b["note"], "isRelatedTo": sys_ref(b["system"]),
                "additionalProperty": [
                    {"@type": "PropertyValue", "name": "procurement-status", "value": b.get("status") or b.get("flow") or ""},
                    {"@type": "PropertyValue", "name": "quantity", "value": b["qty"]}]}
        price = re.search(r"\$(\d+(?:\.\d+)?)", b["price"])
        if b.get("url"):
            node["offers"] = {"@type": "Offer", "url": b["url"],
                              **({"price": price.group(1), "priceCurrency": "USD"} if price else {})}
        graph.append(node)

    for o in ORDERS:
        graph.append({
            "@id": f"#{o['id'].lower()}", "@type": "Order",
            "orderNumber": o["id"], "orderDate": o["date"],
            "orderStatus": f"https://schema.org/{ORDER_STATUS_LD[o['status']]}",
            "seller": {"@type": "Organization", "name": o["vendor"]},
            "orderedItem": [{"@id": bom_ids[i]} for i in o["items"] if i in bom_ids],
            "orderDelivery": {"@type": "ParcelDelivery", "deliveryAddress": {
                "@type": "PostalAddress",
                "addressLocality": dest_label(o)}},
            "description": o.get("note", "")})

    for t in TASKS:
        graph.append({
            "@id": f"#task-{slug(t['task'])}", "@type": "Action",
            "name": t["task"], "description": t.get("note", ""),
            "actionStatus": f"https://schema.org/{ACTION_STATUS_LD[t['status']]}",
            "object": sys_ref(t["system"])})

    for d in DECISIONS:
        graph.append({
            "@id": f"#decision-{slug(d['title'])}", "@type": "CreativeWork",
            "genre": "engineering-decision", "name": d["title"],
            "text": re.sub(r"<[^>]+>", "", d["why"]), "about": sys_ref(d["system"])})

    for fname, desc in [("data/project.json", "Project metadata, event dates, change log"),
                        ("data/playbooks.json", "Working-process playbooks"),
                        ("data/systems.json", "Component registry with status"),
                        ("data/bom.json", "Bill of materials with sourcing status"),
                        ("data/decisions.json", "Engineering decision log"),
                        ("data/tasks.json", "Task board by sub-project"),
                        ("data/orders.json", "Purchase orders and delivery status"),
                        ("audio/data/params.json", "Audio node model constants"),
                        ("audio/data/cases.json", "Playa scenarios for the audio model"),
                        ("lights/data/params.json", "Lights node model constants: fixtures, "
                                                    "power groups, wiring, battery and solar"),
                        ("lights/data/cases.json", "Playa night scenarios for the lights model"),
                        ("solar/data/params.json", "Power node constants: EcoFlow stations, "
                                                   "self-built array, playa derates"),
                        ("solar/data/cases.json", "Generation scenarios and swap cases")]:
        graph.append({"@id": f"#data-{slug(fname)}", "@type": "Dataset",
                      "name": f"Hero Armor {fname}", "description": desc,
                      "isPartOf": {"@id": "#project"},
                      "encodingFormat": "application/json"})

    return {"@context": "https://schema.org", "@graph": graph}


GH = "https://github.com/Hero-Armor/hero-armor.github.io"
UK2LAT = {
    "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e", "є": "ie",
    "ж": "zh", "з": "z", "и": "y", "і": "i", "ї": "i", "й": "i", "к": "k", "л": "l",
    "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch", "ь": "",
    "ю": "iu", "я": "ia", "’": "", "ʼ": "", "'": "",
}


def uslug(s):
    """Transliterated slug for OKF file names (Ukrainian-safe)."""
    return slug("".join(UK2LAT.get(ch, ch) for ch in s.lower()))


def md_text(html):
    """decisions.why is light HTML -> markdown (links kept, tags stripped)."""
    txt = re.sub(r'<a href="([^"]+)">([^<]+)</a>', r"[\2](\1)", html)
    return re.sub(r"<[^>]+>", "", txt)


def fm(fields):
    """YAML frontmatter from an ordered dict of simple values."""
    lines = ["---"]
    for k, v in fields.items():
        if v is None:
            continue
        if isinstance(v, list) and v and isinstance(v[0], dict):
            lines.append(f"{k}:")
            for item in v:
                inner = ", ".join(f"{ik}: {json.dumps(iv, ensure_ascii=False)}"
                                  for ik, iv in item.items())
                lines.append(f"  - {{ {inner} }}")
        elif isinstance(v, list):
            lines.append(f"{k}: [{', '.join(json.dumps(x, ensure_ascii=False) for x in v)}]")
        elif isinstance(v, dict):
            inner = ", ".join(f"{ik}: {json.dumps(iv, ensure_ascii=False)}" for ik, iv in v.items())
            lines.append(f"{k}: {{ {inner} }}")
        else:
            lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def build_okf():
    """Compile data/ into an OKF v0.2 bundle (knowledge/): one markdown concept
    per file, YAML frontmatter, bundle-relative cross-links. data/*.json stays
    the editing format; this is generated — never hand-edit knowledge/."""
    import shutil
    okf = ROOT / "knowledge"
    if okf.exists():
        shutil.rmtree(okf)
    okf.mkdir()
    gen = {"by": "process:site-build"}
    ev = PROJ["event"]
    wh_node, results = m.composite_day()
    auto = m.autonomy(wh_node)
    day, night = results["day"], results["night"]
    tj_worst = max(r["t_j_worst"] for r in results.values())

    sys_slug = {c["key"]: c["key"] for c in SYSTEMS_REG}
    sys_link = {k: f"/systems/{k}.md" for k in sys_slug}
    sys_link["project"] = "/project.md"

    def clink(k):
        label = SYS_LABEL.get(k, k)
        return f"[{label}]({sys_link.get(k, '/project.md')})"

    def write(path, fields, body):
        p = okf / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(fm(fields) + body.rstrip() + "\n")

    def index_md(path, title, sections, root=False):
        head = f'---\nokf_version: "0.2"\n---\n\n' if root else ""
        parts = [head + f"# {title}\n"]
        for heading, items in sections:
            if not items:
                continue
            parts.append(f"\n# {heading}\n" if heading != title else "")
            parts.extend(f"* {it}" for it in items)
            parts.append("")
        p = okf / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(parts).rstrip() + "\n")

    # ---- project + event ----
    write("project.md", {
        "type": "Project", "title": "Hero Armor",
        "description": "Меморіальна інсталяція для Burning Man 2026 памʼяті Захара Захарова — "
                       "воїн-захисник, що промовляє його голосом.",
        "resource": "https://hero-armor.com/", "tags": ["project"], "generated": gen,
    }, f"""Меморіальна інсталяція памʼяті Захара Захарова — 3D-художника, який загинув,
захищаючи Україну (2022). Історія — на [hero-armor.com](https://hero-armor.com/)
(меморіальний сайт, окремий хостинг). Вартовий промовляє голосом Захара
(ElevenLabs-клон), коли людина підходить на 2.5–3 м.

# Складові

* [Системи](/systems/index.md) — аудіо, сонце/живлення, світло, броня
* [Рішення](/decisions/index.md) — інженерний лог рішень з «чому»
* [Задачі](/tasks/index.md) — дошка по системих
* [Закупівля](/bom/index.md) — BOM з лінками й статусами
* [Замовлення](/orders/index.md) — що їде і куди
* [Модель](/model/index.md) — розраховані цифри аудіо-вузла
* [Подія](/event.md) — {ev["name"]}

# Джерела правди

Бандл генерується з файлової бази `data/*.json` командою
`cd site && python3 build.py` — правити треба JSON, не ці файли.
Інженерний хаб: [hero-armor.github.io]({SITE_URL}) · [репозиторій]({GH}).""")

    write("event.md", {
        "type": "Event", "title": ev["name"],
        "description": f"Ворота {ev['gate_open']}, Man горить {ev['burn_night']}, фінал {ev['end']} — {ev['location']}.",
        "resource": "https://burningman.org/", "tags": ["project"], "generated": gen,
        "start_date": ev["gate_open"], "end_date": ev["end"],
    }, f"""# Дати

| Що | Коли |
|----|------|
| Ворота відчиняються | {ev["gate_open"]} |
| Man горить | {ev["burn_night"]} |
| Фінал | {ev["end"]} |

Місце: {ev["location"]}. Інсталяція: [Hero Armor](/project.md).""")

    # ---- systems ----
    sys_items = []
    for c in SYSTEMS_REG:
        k = c["key"]
        c_dec = [d for d in DECISIONS if d["system"] == k]
        c_tasks = [t for t in TASKS if t["system"] == k]
        c_bom = [b for b in BOM if b["system"] == k]
        body = [c["summary"], ""]
        if c_dec:
            body.append("# Рішення\n")
            body += [f"* [{d['title']}](/decisions/{uslug(d['title'])}.md)" for d in c_dec]
            body.append("")
        if c_tasks:
            body.append("# Задачі\n")
            body += [f"* [{t['task']}](/tasks/{uslug(t['task'])}.md) — {task_status(t)}"
                     for t in c_tasks]
            body.append("")
        if c_bom:
            body.append("# Закупівля\n")
            body += [f"* [{b['item']}](/bom/{uslug(b['item'])}.md) — {b['price']}, "
                     f"{'є' if b['status'] == 'have' else 'купити'}" for b in c_bom]
            body.append("")
        if k == "audio":
            body.append("# Розраховані цифри\n\nДив. [модель аудіо-вузла](/model/audio-node.md) — "
                        "числа рахує тільки [санкціонована модель](/computations/audio-node-model.md).\n")
        write(f"systems/{k}.md", {
            "type": "Component", "title": c["label"], "description": c["summary"][:160],
            "resource": SITE_URL + c["page"], "tags": [k],
            "system_status": c["status"], "generated": gen,
        }, "\n".join(body))
        sys_items.append(f"[{c['label']}]({k}.md) - {COMP_STATUS_LABEL[c['status']]}")
    index_md("systems/index.md", "Системи", [("Системи", sys_items)])

    # ---- decisions (human-confirmed => verified: human) ----
    dec_items = []
    for d in DECISIONS:
        s = uslug(d["title"])
        write(f"decisions/{s}.md", {
            "type": "Engineering Decision", "title": d["title"],
            "description": re.split(r"(?<=[.!?])\s+", md_text(d["why"]))[0][:200],
            "tags": [d["system"]], "generated": gen,
            "decided_by": d.get("decided_by", "team"),
            "decision_zone": d.get("decision_zone", ""),
            "verified": {"by": f"human:{d.get('decided_by', 'gumanist')}",
                         "at": "2026-07-27T00:00:00Z"},
        }, f"Система: {clink(d['system'])} · вирішив: **{DECIDERS.get(d.get('decided_by'), d.get('decided_by', '—'))}**"
           f"{' (' + d['decision_zone'] + ')' if d.get('decision_zone') else ''}"
           f"\n\n# Чому\n\n{md_text(d['why'])}")
        dec_items.append(f"[{d['title']}]({s}.md)")
    index_md("decisions/index.md", "Інженерні рішення", [("Рішення", dec_items)])

    # ---- tasks ----
    t_items = []
    for t in TASKS:
        s = uslug(t["task"])
        note = t.get("note", "")
        write(f"tasks/{s}.md", {
            "type": "Task", "title": t["task"], "description": note[:160] or None,
            "tags": [t["system"]], "task_status": t["status"], "generated": gen,
        }, f"Статус: **{task_status(t)}** · система: {clink(t['system'])}"
           + (f"\n\n{note}" if note else ""))
        t_items.append(f"[{t['task']}]({s}.md) - {task_status(t)}")
    index_md("tasks/index.md", "Задачі", [("Задачі", t_items)])

    # ---- BOM parts ----
    b_items = []
    for b in BOM:
        s = uslug(b["item"])
        write(f"bom/{s}.md", {
            "type": "Part", "title": b["item"], "description": b["note"][:160],
            "resource": b.get("url"), "tags": [b["system"]],
            "quantity": b["qty"], "price": b["price"],
            "procurement_status": b.get("status") or b.get("flow") or "", "generated": gen,
        }, f"{b['note']}\n\nСистема: {clink(b['system'])} · статус: "
           f"**{'є' if b['status'] == 'have' else 'купити'}** · ціна {b['price']} · к-сть {b['qty']}")
        b_items.append(f"[{b['item']}]({s}.md) - {b['price']}, "
                       f"{'є' if b['status'] == 'have' else 'купити'}")
    index_md("bom/index.md", "Закупівля (BOM)", [("Позиції", b_items)])

    # ---- orders ----
    o_items = []
    for o in ORDERS:
        s = o["id"].lower()
        items_md = "\n".join(f"* [{i}](/bom/{uslug(i)}.md)" for i in o["items"])
        write(f"orders/{s}.md", {
            "type": "Order", "title": f"{o['id']} — {o['vendor']}",
            "description": o.get("note", ""), "resource": o.get("url"),
            "tags": [o["system"]], "order_status": o["status"],
            "order_date": o["date"],
            "deliver_to": dest_label(o),
            "generated": gen,
        }, f"Статус: **{ORDER_STATUS[o['status']]}** · замовлено {o['date']} · "
           f"доставка: {dest_label(o)}\n\n# Позиції\n\n{items_md}"
           + (f"\n\n{o['note']}" if o.get("note") else ""))
        o_items.append(f"[{o['id']} — {o['vendor']}]({s}.md) - {ORDER_STATUS[o['status']]}")
    index_md("orders/index.md", "Замовлення", [("Замовлення", o_items)])

    # ---- model snapshot + attested computation ----
    days_txt = " · ".join(f"{n} ≈ {d:.1f} діб" for n, d in auto["days"].items())
    write("model/audio-node.md", {
        "type": "Model Snapshot", "title": "Аудіо-вузол — розраховані цифри",
        "description": "Ключові числа з моделі: споживання, автономність, температура, гучність.",
        "tags": ["audio"], "generated": gen,
        "sources": [
            {"id": "params", "resource": f"{GH}/blob/main/audio/data/params.json",
             "title": "audio/data/params.json — константи моделі"},
            {"id": "cases", "resource": f"{GH}/blob/main/audio/data/cases.json",
             "title": "audio/data/cases.json — кейси плайї"},
        ],
    }, f"""Числа нижче рахує тільки [санкціонована модель](/computations/audio-node-model.md);
руками їх ніхто не пише.[^params]

# Цифри

| Метрика | Значення |
|---------|----------|
| Споживання вузла | {wh_node:.0f} Wh/добу (композитна доба)[^cases] |
| Разом з EcoFlow standby | {auto["total_wh_day"]:.0f} Wh/добу |
| Автономність | {days_txt} |
| Сонце «в нуль» | ~{auto["solar_w"]:.0f} Вт |
| Tj ампа, найгірший кейс | {tj_worst:.0f} °C (межа {P["thermal"]["tj_max"]:.0f}) |
| Гучність @3 м, день | {day["spl_peak"]:.0f} dB пік / ~{day["spl_avg"]:.0f} dB сер. ({day["margin_avg"]:+.0f} дБ до шуму) |
| Гучність @3 м, гучна ніч | запас {night["margin_avg"]:+.0f} дБ |

Система: [Аудіо](/systems/audio.md).

[^params]: audio/data/params.json — константи моделі
[^cases]: audio/data/cases.json — кейси плайї""")
    index_md("model/index.md", "Модель", [("Модель", [
        "[Аудіо-вузол — розраховані цифри](audio-node.md) - Wh/добу, автономність, Tj, SPL"])])

    write("computations/audio-node-model.md", {
        "type": "Attested Computation", "title": "Модель аудіо-вузла",
        "description": "Санкціонований розрахунок усіх цифр аудіо-вузла з data/params.json + cases.json.",
        "runtime": "python",
        "computation": f"{GH}/blob/main/audio/model/audio_node_model.py",
        "tags": ["audio"], "generated": gen,
        "verified": {"by": "human:gumanist", "at": "2026-07-27T00:00:00Z"},
    }, """Єдине санкціоноване джерело чисел аудіо-вузла: power budget (крест-фактор
мови), теплова модель TPA3116, SPL, автономність від EcoFlow.

# Запуск

    cd site && python3 build.py        # перерахує все і перебудує сторінки
    python3 audio/model/audio_node_model.py   # тільки модель, друк у консоль

Вхід — [params.json](/model/audio-node.md) (константи) і кейси плайї; вихід —
числа на сторінках хабу та в [знімку моделі](/model/audio-node.md).
Правило проєкту: числа на сторінках рахує тільки ця модель.""")
    index_md("computations/index.md", "Обчислення", [("Обчислення", [
        "[Модель аудіо-вузла](audio-node-model.md) - санкціонований розрахунок цифр"])])

    # ---- playbooks ----
    pb_items = []
    for pb in PLAYBOOKS:
        s = uslug(pb["title"])
        write(f"playbooks/{s}.md", {
            "type": "Playbook", "title": pb["title"], "description": pb["description"],
            "tags": pb.get("tags", ["project"]), "generated": gen,
            "verified": {"by": "human:gumanist", "at": "2026-07-28T00:00:00Z"},
        }, pb["body"])
        pb_items.append(f"[{pb['title']}]({s}.md) - {pb['description']}")
    index_md("playbooks/index.md", "Плейбуки", [("Плейбуки", pb_items)])

    # ---- log + root index ----
    log_by_date = {}
    for entry in PROJ.get("log", []):
        log_by_date.setdefault(entry["date"], []).append(entry)
    log_lines = ["# Журнал проєкту", ""]
    for d_key in sorted(log_by_date, reverse=True):
        log_lines.append(f"## {d_key}")
        log_lines += [f"* **{e.get('kind', 'Event')}**: {e.get('text', '')}" for e in log_by_date[d_key]]
        log_lines.append("")
    (okf / "log.md").write_text("\n".join(log_lines).rstrip() + "\n")

    open_n = sum(1 for t in TASKS if t["status"] != "done")
    tobuy_n = sum(1 for b in BOM if b.get("status") != "have")
    index_md("index.md", "Hero Armor — база знань (OKF)", [
        ("Проєкт", [
            "[Hero Armor](project.md) - меморіальна інсталяція памʼяті Захара Захарова",
            f"[{ev['name']}](event.md) - ворота {ev['gate_open']}, Man горить {ev['burn_night']}",
            "[Журнал](log.md) - хронологія проєкту"]),
        ("Розділи", [
            f"[Системи](systems/index.md) - {len(SYSTEMS_REG)} підсистеми",
            f"[Рішення](decisions/index.md) - {len(DECISIONS)} інженерних рішень з «чому»",
            f"[Задачі](tasks/index.md) - {len(TASKS)} задач, відкрито {open_n}",
            f"[Закупівля](bom/index.md) - {len(BOM)} позицій, докупити {tobuy_n}",
            f"[Замовлення](orders/index.md) - {len(ORDERS)}",
            "[Модель](model/index.md) - розраховані цифри аудіо-вузла",
            "[Обчислення](computations/index.md) - санкціоновані розрахунки",
            f"[Плейбуки](playbooks/index.md) - {len(PLAYBOOKS)} робочих процеси"]),
    ], root=True)

    n_files = sum(1 for _ in okf.rglob("*.md"))
    print(f"built knowledge/ — OKF v0.2 bundle, {n_files} files")


def build():
    today = date.today()
    wh_node, results = m.composite_day()
    auto = m.autonomy(wh_node)
    day, night = results["day"], results["night"]
    tj_worst = max(r["t_j_worst"] for r in results.values())
    i_comp = wh_node / m.V / 24
    spk = m.SPK
    sn = P["sensor"]
    cfg = "моно" if P["speaker"]["config"] == "mono" else "стерео ×2"

    def tile(k, v, u, note, cls=""):
        return (f'    <div class="tile {cls}"><div class="k">{k}</div>'
                f'<div class="v">{v}<span class="u"> {u}</span></div>'
                f'<div class="note">{note}</div></div>')

    # ================= audio page =================
    audio = tmpl("audio.tmpl.html")
    svg = (AUDIO / "model" / "schematic.svg").read_text()
    svg = re.sub(r"<\?xml[^>]*\?>\s*|<!DOCTYPE[^>]*>\s*", "", svg)
    audio = audio.replace("{{SCHEMATIC_SVG}}", svg)

    audio_tiles = [
        tile("Споживання вузла", f"{wh_node:.0f}", "Wh/добу",
             f"мова (крест {P['crest_db']:.0f} дБ), композитна доба", "good"),
        tile("Частка в системі", f"{100*wh_node/pw.demand()['total']:.0f}", "%",
             "звук — найдешевший вузол; запас і підміна станції рахуються "
             "в системі «Живлення»"),
        tile("Tj ампа, найгірший кейс", f"{tj_worst:.0f}", "°C",
             f"межа {P['thermal']['tj_max']:.0f}°C; радіатор {P['thermal']['heatsink_rth']}°C/W назовні", "good"),
        tile("Гучність @3 м", f"{day['spl_peak']:.0f}", "dB пік",
             f"{esc(spk['name'])} {cfg}: ~{day['spl_avg']:.0f} dB сер.; "
             f"{day['margin_avg']:+.0f} дБ вдень, {night['margin_avg']:+.0f} на гучній вечірці"),
        tile("Детекція", f"{sn['range_m']:.1f}", "м", "стабільно вдень/вночі/в бурю", "good"),
    ]
    audio = audio.replace("{{ASSEMBLY_HTML}}", assembly_html())
    audio = audio.replace("{{DIAGRAMS}}", diagrams_html("audio", heading="Схеми і креслення"))
    audio = audio.replace("{{FIGURES}}", figures_html("audio"))
    audio = audio.replace("{{PHOTOS}}", photos_html("audio"))
    audio = audio.replace("{{TILES_HTML}}", "\n".join(audio_tiles))

    decs = "\n".join(
        f'    <div class="decision">\n      <h3>{esc(d["title"])}</h3>\n'
        f'      <p><span class="why">чому</span> · {d["why"]}</p>\n    </div>'
        for d in DECISIONS if d["system"] == "audio")
    audio = audio.replace("{{DECISIONS_HTML}}", decs)

    # Закупівля прямо на сторінці системи: Іван 02.08 шукав список саме тут,
    # а він жив тільки на головній — зі сторінки, де паяють, він не видно.
    a_bom = [b for b in BOM if b["system"] == "audio"]
    b_rows = []
    for b in a_bom:
        cls, label = pill_of(b)
        item = f'<a href="{b["url"]}">{esc(b["item"])}</a>' if b.get("url") else esc(b["item"])
        b_rows.append(f'      <tr>{bom_thumb(b)}<td>{item}</td><td class="num">{b["qty"]}</td>'
                      f'<td class="num">{b["price"]}</td>'
                      f'<td><span class="pill {cls}">{label}</span></td>'
                      f'<td>{esc(b["note"])}</td></tr>')
    audio = audio.replace("{{BOM_HTML}}",
                          '  <div class="tbl-wrap">\n  <table>\n'
                          '    <thead><tr><th></th><th>Позиція</th><th>К-сть</th><th>~Ціна</th>'
                          '<th>Статус</th><th>Нотатка</th></tr></thead>\n'
                          f'    <tbody>\n{chr(10).join(b_rows)}\n    </tbody>\n  </table>\n  </div>')

    # ================= lab page =================
    lab = tmpl("lab.tmpl.html")
    # схему вставляємо текстом svg, а не картинкою: інакше підписи
    # на ній не перекладаються в англійській версії
    ssvg = (AUDIO / "model" / "signal_chain.svg").read_text()
    ssvg = ssvg[ssvg.index("<svg"):]
    lab = lab.replace("{{SIGNAL_SVG}}", ssvg)

    presets = []
    for c in m.CASES_DOC["cases"]:
        if not c.get("dashboard"):
            continue
        presets.append(dict(name=c["name"], tamb=c["t_ambient"], solar=c["solar_load"],
                            noise=c["noise_db"], trig=c["triggers_per_hr"], clip=c["clip_s"],
                            cool=c["cooldown_s"], dist=c["listener_m"], vol=c["vol_dbfs"],
                            rth=P["thermal"]["heatsink_rth"], sens=spk["sens_db"],
                            bat=P["power_source"]["default_wh"], night=c["night_mode"],
                            gain=P["gain_db"]))
    lab = lab.replace("{{PRESETS_JSON}}", json.dumps(presets, ensure_ascii=False))

    th, c33 = P["thermal"], P["currents_33v"]
    lab = lab.replace("{{JS_CONST_1}}",
        f'const V={P["rail_v"]}, BUCK={P["buck_eff"]}, EFF={P["amp_eff"]}, '
        f'IDLE={P["amp_idle_a"]}, RJC={th["rth_jc"]}, RPAD={th["rth_pad"]}, SKIN={sn["skin_c"]};')
    lab = lab.replace("{{JS_CONST_2}}",
        f'const DACFS={P["dac_fs_vrms"]}, VCLIP=V/Math.sqrt(2), R={spk["ohms"]}, '
        f'CREST=Math.pow(10,{P["crest_db"]}/10);')
    lab = lab.replace("{{ECOFLOW_STANDBY}}", str(P["power_source"]["standby_w"]))
    lab = lab.replace("{{NIGHT_DELTA}}", str(P["volume"]["night_delta_db"]))
    lab = lab.replace("{{RADAR_RANGE}}", str(P["sensor"]["range_m"]))
    lab = lab.replace("{{USABLE_FRAC}}", str(P["power_source"]["usable_frac"]))
    lab = lab.replace("{{SUN_HOURS}}", str(P["solar"]["sun_hours"]))
    lab = lab.replace("{{SYS_EFF}}", str(P["solar"]["system_eff"]))
    lab = lab.replace("{{A33_PLAY}}", f'{c33["esp32_play"]}+{c33["dac"]}+{c33["sd_read"]}')
    lab = lab.replace("{{A33_IDLE}}", f'{c33["esp32_idle"]}+{c33["dac"]}')
    lab = lab.replace("{{RADAR_W}}", f'{sn["a_5v"]}*5.0')
    lab = lab.replace("{{PIR_W}}", f'{sn["pir_a_33v"]}*3.3')

    cands = P["speaker"]["candidates"]
    chosen = P["speaker"]["chosen"]
    btns = "".join(
        f'<button data-sens="{c["sens_db"]}"{" class=\"active\"" if key == chosen else ""}>'
        f'{esc(c["name"])} ({c["sens_db"]} дБ)</button>\n        '
        for key, c in cands.items())
    lab = lab.replace("{{SPK_BTNS}}", btns.rstrip())
    lab = lab.replace("{{CASE_TABLE_TITLE}}",
        f'Кейси (модель: мова, {sn["type"]}, gain {P["gain_db"]} дБ, {esc(spk["name"])} {cfg})')

    rows = []
    for c in m.CASES_DOC["cases"]:
        if not c.get("dashboard"):
            continue
        r = results[c["key"]]
        marg = r["margin_avg"]
        marg_s = (f'<td class="num"{" style=\"color:var(--crit)\"" if marg < 0 else ""}>'
                  f'{"+" if marg >= 0 else "−"}{abs(marg):.0f} dB</td>')
        rows.append(
            f'      <tr><td>{esc(c["name"])} ({c["t_ambient"]}°C)</td>'
            f'<td class="num">{r["duty"]*100:.1f}%</td>'
            f'<td class="num">{r["i_avg"]*1000:.0f} mA</td>'
            f'<td class="num">{r["wh_day"]:.0f}</td>'
            f'<td class="num">{r["t_j_worst"]:.0f}°C</td>'
            f'<td class="num">{r["spl_avg"]:.0f} dB</td>'
            f'{marg_s}<td class="num">{r["radar_range_m"]:.1f} м</td></tr>')
    rows.append(
        f'      <tr><td><b>Композитна доба Burn</b></td><td class="num">—</td>'
        f'<td class="num">~{i_comp*1000:.0f} mA</td><td class="num"><b>{wh_node:.0f}</b></td>'
        f'<td class="num">—</td><td class="num">—</td><td class="num">—</td><td class="num">—</td></tr>')
    lab = lab.replace("{{CASE_ROWS}}", "\n".join(rows))
    lab = lab.replace("{{BUY_BLOCK}}", buy_block_html(
        "audio",
        note="Уся закупівля по аудіо-вузлу: динаміки, підсилювач, джерело, комутація і кріплення. Зріз єдиного реєстру за системою."))

    days_txt = ", ".join(f"{n} ≈ {d:.1f}" for n, d in auto["days"].items())
    lab = lab.replace("{{LAB_CAPTION}}",
        f'Мовна модель (крест {P["crest_db"]:.0f} дБ): вузол ≈ {wh_node:.0f} Wh/добу. '
        f'Живлення — EcoFlow (12V DC): зі стендбаєм станції ~{P["power_source"]["standby_w"]} Вт '
        f'разом ≈ {auto["total_wh_day"]:.0f} Wh/добу → діб: {days_txt}; '
        f'сонце в нуль — ~{auto["solar_w"]:.0f} Вт. Рішення по звуку — {cfg} '
        f'({esc(spk["name"])}): вдень запас {day["margin_avg"]:+.0f} дБ, на гучній нічній '
        f'вечірці {night["margin_avg"]:+.0f} дБ — піки {night["spl_peak"]:.0f} дБ пробиваються, '
        f'середина на межі. Стерео-варіант (+3 дБ) можна увімкнути чекбоксом для порівняння.')

    # ================= lights page + lights lab =================
    LP = lm.P
    wh_light, l_res = lm.composite_night()
    l_demand = lm.demand()
    l_peak = lm.peak_watts()
    peak_runs = lm.wiring_losses(l_peak)
    l_burn, l_norm, l_eco = l_res["burn"], l_res["normal"], l_res["eco"]
    worst_drop = max(r["drop_pct"] for r in peak_runs)
    bad_runs = [r for r in peak_runs if r["drop_pct"] > LP["wiring"]["drop_crit_pct"]]
    ref = LP["spec_reference"]
    photo = LP["photometry"]
    night_h = l_demand["hours"]
    by_grp = l_demand["by_group"]
    GAUGES = sorted((int(a) for a in LP["wiring"]["awg_ohm_per_m"]), reverse=True)

    lights = tmpl("lights.tmpl.html")
    lsvg = (LIGHTS / "model" / "circuit_main.svg").read_text()
    lsvg = re.sub(r"<\?xml[^>]*\?>\s*|<!DOCTYPE[^>]*>\s*", "", lsvg)
    lights = lights.replace("{{SCHEMATIC_SVG}}", lsvg)

    lights_tiles = [
        tile("Спожито за ніч", f"{wh_light:.0f}", "Wh",
             f"композитна ніч {night_h:.1f} год: пік, штатно, економ", "good"),
        tile("Найбільший їдок", f"{by_grp['g2']:.0f}", "Wh",
             f"декор — {100*by_grp['g2']/wh_light:.0f}% ночі; аварійна {by_grp['g3a']:.0f}, "
             f"прожектори лише {by_grp['g1']:.0f}"),
        tile("Аварійна лінія", f"{l_res['emergency']['g3a']:.0f}", "Вт",
             f"не регулюється зовсім — {by_grp['g3a']:.0f} Wh за ніч; "
             f"це 24 врізні вогні торця плюс маркер ящика"),
        tile("Пік системи", f"{sum(l_peak.values()):.0f}", "Вт",
             f"Гр.1 {l_peak['g1']:.0f} · Гр.2 {l_peak['g2']:.0f} · Гр.3А {l_peak['g3a']:.0f}; "
             f"у архітектора {ref['architect_peak_w']} Вт"),
        tile("Освітленість фігури", f"{l_burn['lux']:.0f}", "лк",
             f"ціль {photo['target_lux']} лк; штатно {l_norm['lux']:.0f}, "
             f"економ {l_eco['lux']:.0f}", "good"),
        tile("Просадка в лініях", f"{worst_drop:.1f}", "%",
             f"межа {LP['wiring']['drop_crit_pct']:.0f}% — "
             + ("наявний кабель не тягне на 12 В" if bad_runs else "у нормі"),
             "crit" if bad_runs else "good"),
    ]
    lights = lights.replace("{{DIAGRAMS}}", diagrams_html("lights"))
    lights = lights.replace("{{FIGURES}}", figures_html("lights"))
    lights = lights.replace("{{PHOTOS}}", photos_html("lights"))
    lights = lights.replace("{{BUY_BLOCK}}", buy_block_html(
        "lights",
        note="Уся закупівля по світлу: прожектори, стрічка і неон, контролери, "
             "щит із запобіжниками, кабель і дрібні кріплення. Зріз єдиного реєстру "
             "за системою."))
    lights = lights.replace("{{TILES_HTML}}", "\n".join(lights_tiles))

    l_decs = [d for d in DECISIONS if d["system"] == "lights"]
    lights = lights.replace("{{DECISIONS_HTML}}", "\n".join(
        f'    <div class="decision">\n      <h3>{esc(d["title"])}</h3>\n'
        f'      <p><span class="why">чому</span> · {d["why"]}</p>\n    </div>'
        for d in l_decs if not d.get("open")))
    lights = lights.replace("{{FLAGS_HTML}}", "\n".join(
        f'  <div class="flag">\n    <h3>{esc(d["title"])}</h3>\n'
        f'    <p><span class="why">відкрите</span> · {d["why"]}</p>\n  </div>'
        for d in l_decs if d.get("open")))

    grp_label = {k: v["label"] for k, v in LP["groups"].items()}
    f_rows = []
    for f in LP["fixtures"]:
        qty = f'{f["qty"]}× {f["length_m"]} м' if f.get("length_m") else str(f["qty"])
        f_rows.append(
            f'      <tr><td class="num">{f["spec"]}</td><td>{esc(f["name"])}</td>'
            f'<td>{esc(f["zone"])}</td><td class="num">{qty}</td>'
            f'<td class="num">{lm.fixture_peak(f):.1f} Вт</td>'
            f'<td><span class="grp {f["group"]}">{esc(grp_label[f["group"]].split(" · ")[0])}</span></td>'
            f'<td>{esc(f.get("model", "—"))}</td></tr>')
    lights = lights.replace("{{FIXTURES_ROWS}}", "\n".join(f_rows))
    lights = lights.replace("{{FIXTURES_CAPTION}}",
        f'Паспортний пік — усе світло на повну, з урахуванням анімації (світиться біжучий фронт, не вся стрічка): {sum(l_peak.values()):.0f} Вт '
        f'проти {ref["architect_peak_w"]} Вт у розрахунку архітектора (у його Гр.2 сидів ще аудіоплеєр, '
        f'а габаритні вогні на стійках ми з неї прибрали). У реальних режимах система бере '
        f'{l_eco["draw_w"]:.0f}–{l_burn["draw_w"]:.0f} Вт.')

    w_rows = []
    for r in peak_runs:
        run = next(x for x in LP["wiring"]["runs"] if x["id"] == r["id"])
        need = lm.min_awg(run, l_peak)
        ok = r["drop_pct"] <= LP["wiring"]["drop_crit_pct"]
        verdict = ('<span class="pill have">ok</span>' if ok
                   else f'<span class="pill add">треба AWG {need}</span>')
        style = "" if ok else ' style="color:var(--crit)"'
        w_rows.append(
            f'      <tr><td>{esc(r["label"])}</td><td class="num">AWG {r["awg"]}</td>'
            f'<td class="num">{r["length_m"]:.1f} м</td><td class="num">{r["amps"]:.1f} A</td>'
            f'<td class="num"{style}>−{r["v_drop"]:.2f} В ({r["drop_pct"]:.2f}%)</td>'
            f'<td>{verdict}</td></tr>')
    lights = lights.replace("{{WIRING_ROWS}}", "\n".join(w_rows))
    lights = lights.replace("{{WIRING_CAPTION}}",
        f'Опір рахується туди-назад. {esc(LP["wiring"]["note"])} '
        + (f'Зараз не проходять {len(bad_runs)} лінії з {len(peak_runs)} — '
           f'найгірша {worst_drop:.2f}% при межі {LP["wiring"]["drop_crit_pct"]:.0f}%.'
           if bad_runs else "Усі лінії в межах норми."))

    # ---- lights lab ----
    llab = tmpl("lights_lab.tmpl.html")
    vf, wl = LP["voltage_following"], LP["wiring"]
    spot = next(f for f in LP["fixtures"] if f["id"] == "spot")
    llab = llab.replace("{{JS_CONST}}",
        f'const BUS={LP["bus_v"]}, VNOM={vf["v_nominal"]}, VMIN={vf["v_min"]}, '
        f'VMAX={vf["v_max"]}, PEXP={vf["power_exponent"]};\n'
        f'  const OHM={json.dumps(wl["awg_ohm_per_m"])}, '
        f'DROP_WARN={wl["drop_warn_pct"]}, DROP_CRIT={wl["drop_crit_pct"]};\n'
        f'  const SPOT_QTY={spot["qty"]}, SPOT_LM={spot["lumens"]}, '
        f'UTIL={photo["utilization"]}, AREA={photo["figure_area_m2"]}, '
        f'TARGET_LUX={photo["target_lux"]};')
    llab = llab.replace("{{GAUGES_JSON}}", json.dumps(GAUGES))
    llab = llab.replace("{{FIXTURES_JSON}}", json.dumps([
        {k: f[k] for k in ("group", "qty", "dimming") if k in f}
        | {k: f[k] for k in ("w_unit", "length_m", "w_per_m", "addressable",
                             "w_full", "duty_animation") if k in f}
        for f in LP["fixtures"]], ensure_ascii=False))
    llab = llab.replace("{{RUNS_JSON}}", json.dumps(
        [{"id": r["id"], "awg": str(r["awg"]), "length_m": r["length_m"], "groups": r["groups"]}
         for r in wl["runs"]], ensure_ascii=False))
    llab = llab.replace("{{PRESETS_JSON}}", json.dumps([
        dict(name=c["name"], vspot=c["v_spot"], dim2=round(c["dim_g2"] * 100),
             duty=round(LP["addressable"]["duty_animation"] * 100), hours=c["hours"],
             awgt=GAUGES.index(8), awgd=GAUGES.index(12),
             emerg=1 if c["dim_g3a"] > 0 else 0)
        for c in lm.CASES_DOC["cases"] if c.get("dashboard")], ensure_ascii=False))
    llab = llab.replace("{{CASE_TABLE_TITLE}}",
        f'Кейси ночі (шина {LP["bus_v"]:.0f} В, наявний кабель, анімація '
        f'{LP["addressable"]["duty_animation"]*100:.0f}%)')

    l_rows = []
    for c in lm.CASES_DOC["cases"]:
        if not c.get("dashboard"):
            continue
        r = l_res[c["key"]]
        d_style = ' style="color:var(--crit)"' if r["worst_drop_pct"] > wl["drop_crit_pct"] else ""
        l_rows.append(
            f'      <tr><td>{esc(r["case"])}</td>'
            f'<td class="num">{r["g1"]:.0f} Вт</td><td class="num">{r["g2"]:.0f} Вт</td>'
            f'<td class="num">{r["g3a"]:.0f} Вт</td><td class="num">{r["draw_w"]:.0f} Вт</td>'
            f'<td class="num">{r["wh_night"]:.0f}</td><td class="num">{r["lux"]:.0f} лк</td>'
            f'<td class="num"{d_style}>{r["worst_drop_pct"]:.2f}%</td></tr>')
    l_rows.append(
        f'      <tr><td><b>Композитна ніч</b></td><td class="num">—</td><td class="num">—</td>'
        f'<td class="num">—</td><td class="num">~{wh_light/night_h:.0f} Вт</td>'
        f'<td class="num"><b>{wh_light:.0f}</b></td><td class="num">—</td>'
        f'<td class="num">—</td></tr>')
    llab = llab.replace("{{CASE_ROWS}}", "\n".join(l_rows))
    llab = llab.replace("{{LAB_CAPTION}}",
        f'Композитна ніч ({night_h:.1f} год) — {wh_light:.0f} Wh. Розклад споживання: декор '
        f'{by_grp["g2"]:.0f} Wh ({100*by_grp["g2"]/wh_light:.0f}%), аварійна {by_grp["g3a"]:.0f} Wh '
        f'({100*by_grp["g3a"]/wh_light:.0f}%), прожектори {by_grp["g1"]:.0f} Wh '
        f'({100*by_grp["g1"]/wh_light:.0f}%), у міді згорає {by_grp["loss"]:.0f} Wh. '
        f'Просадка в таблиці порахована на наявному кабелі — посунь повзунки калібру, '
        f'щоб побачити, що дає товща мідь.')

    # ---- кільце прожекторів: чим зʼєднати і чи проходить диммер ----
    ring_d = sr.dimmer()
    ring_w = sr.watts()
    llab = llab.replace("{{RING_TILES}}", "\n".join([
        tile("Група на повній", f'{ring_d["load_a"]:.2f}', "A",
             f'{ring_w["full"]:.0f} Вт · рахунок по найпрожерливішій лампі'),
        tile("На мінімумі крутилки", f'{ring_w["dim_min"]:.1f}', "Вт",
             f'{ring_d["min_a"]:.2f} A на всі вісім — діапазон ×{ring_d["range_x"]:.0f}', "good"),
        tile("Запас у диммері", f'{ring_d["headroom_pct"]:.0f}', "%",
             f'{ring_d["load_a"]:.1f} A проти робочої стелі {ring_d["safe_a"]:.1f} A '
             f'(паспорт {ring_d["rating_a"]:.0f} A)',
             "good" if ring_d["headroom_pct"] >= 30 else "warn"),
        tile("Запобіжник групи", f"{sr.fuse():g}", "A",
             "робочий струм із запасом, вгору по стандартному ряду"),
    ]))
    llab = llab.replace("{{RING_SVG}}", re.sub(
        r"<\?xml[^>]*\?>\s*|<!DOCTYPE[^>]*>\s*", "",
        (LIGHTS / "model" / "spot_ring.svg").read_text()))
    llab = llab.replace("{{RING_CAPTION}}", esc(
        f'Радіус розстановки стійок {sr.RING["r_post_m"]:.2f} м — {sr.RING["length_source"]}. '
        f'Довжини уточнюємо після складання подіуму; на вибір схеми це не впливає, '
        f'бо різниця між схемами в рази, а не у відсотках.'))
    llab = llab.replace("{{RING_SCHEMES}}", "\n".join(
        f'      <tr><td>{esc(s["label"])}'
        + (' <span style="color:var(--good)">← беремо</span>'
           if s["kind"] == sr.SG["recommended"] else "")
        + f'</td><td class="num">{s["worst_v"]:.3f} В ({s["worst_pct"]:.2f}%)</td>'
        f'<td class="num">{s["cable_m"]:.1f} м</td>'
        f'<td class="num">{s["joints"]}</td>'
        f'<td style="white-space:normal;max-width:52ch">{esc(s["why"])}</td></tr>'
        for s in sr.schemes()))

    d_rows = []
    FLICK = {"рівно": "var(--good)", "мерехтить": "var(--crit)"}
    for r in lb.dimmer_runs():
        cls = "" if r["dimmer_ok"] else ' style="color:var(--crit)"'
        hcol = ("var(--good)" if r["headroom_pct"] >= 30 else
                "var(--warn)" if r["dimmer_ok"] else "var(--crit)")
        d_rows.append(
            f'      <tr><td>{esc(r["name"])}</td>'
            f'<td class="num">{r["a_full"]:.2f} A · {r["w_full"]:.1f} Вт</td>'
            f'<td class="num">{r["a_min"]:.2f} A · {r["w_min"]:.1f} Вт</td>'
            f'<td class="num">×{r["range_x"]:.0f}</td>'
            f'<td style="color:{FLICK.get(r["flicker"], "var(--ink-2)")}">'
            f'{esc(r["flicker"])}</td>'
            f'<td class="num"{cls}>{r["group_a"]:.2f} A · {r["group_w"]:.0f} Вт</td>'
            f'<td class="num" style="color:{hcol}">{r["headroom_pct"]:.0f}%</td></tr>')
    llab = llab.replace("{{DIMMER_ROWS}}", "\n".join(d_rows))
    llab = llab.replace("{{DIMMER_CAPTION}}", esc(
        f'{lb.B["lamps"][0]["note"].split(".")[0]}. Заміри Івана на блоці живлення 31.07 — '
        f'крайні положення крутилки ШІМ-диммера {sr.DIM["model"]}. Запас рахується не від '
        f'паспортних {sr.DIM["a_rating"]:.0f} A, а від робочої стелі '
        f'{sr.DIM["a_rating"]*sr.DIM["derate"]:.1f} A: тривале навантаження тримають до '
        f'{sr.DIM["derate"]*100:.0f}% номіналу. {sr.DIM["placement_open"]}'))
    # Живий підбір: скільки бере група на будь-якому положенні крутилки.
    # Числа — заміряні крайні точки обраної лампи, між ними пряма (середній
    # струм ШІМ іде за шириною імпульсу лінійно).
    sp_lamp = next(r for r in lb.dimmer_runs() if r["id"] == lb.decision()["chosen"]) \
        if lb.decision() else max(lb.dimmer_runs(), key=lambda r: r["a_full"])
    station = pw.P["stations"][pw.P["station_chosen"]]
    llab = llab.replace("{{SPOT_DIM_LAYER}}", "<p>" + esc(
        f'Диммер не садить вольти — він рубає живлення імпульсами, і середній струм іде за '
        f'шириною імпульсу. Заміряно на {sp_lamp["name"]}: {sp_lamp["a_full"]:.2f} A на повній '
        f'({sp_lamp["w_full"]:.1f} Вт з лампи) і {sp_lamp["a_min"]:.2f} A на мінімумі крутилки '
        f'({sp_lamp["w_min"]:.2f} Вт) — діапазон у {sp_lamp["range_x"]:.0f} разів. Уся вісімка '
        f'на мінімумі бере {8*sp_lamp["w_min"]:.1f} Вт: це той режим, у якому світло доживає '
        f'ніч, якщо вдень не було сонця.') + "</p>")
    llab = llab.replace("{{SPOTS_JSON}}", json.dumps({
        "v": 12.0, "qty": lb.CRIT["spot_qty"],
        "a_full": sp_lamp["a_full"], "a_min": sp_lamp["a_min"],
        "rating": lb.CRIT["dimmer_a"], "derate": lb.CRIT["dimmer_derate"],
        "dc_w": lb.CRIT["dc_port_w"], "station_wh": station["wh"],
        "lamp": sp_lamp["name"],
    }, ensure_ascii=False))
    llab = llab.replace("{{SPOTS_CAPTION}}", esc(
        f'Рахунок іде по {sp_lamp["name"]} — заміряні {sp_lamp["a_full"]:.2f} A на повній і '
        f'{sp_lamp["a_min"]:.2f} A на мінімумі при 12 В. Станція для відсотка — '
        f'{pw.P["station_chosen"]} ({station["wh"]} Wh); межа її 12 В-виходу '
        f'{lb.CRIT["dc_port_w"]} Вт. Втрати в міді сюди не входять — на цих струмах вони під 1% '
        f'(див. схему вище). Це модель, а не замір усіх восьми разом: коли лампи приїдуть, '
        f'вмикаємо всі вісім, міряємо і ставимо в базу реальне число.'))

    llab = llab.replace("{{INSTALL_RULES}}", "\n".join(
        f'    <div class="layer"><h3>{esc(r["rule"])}</h3>'
        f'<p>{esc(r["why"])} <a href="{esc(r["src"])}">джерело</a></p></div>'
        for r in sr.SG["install"]))

    # ---- стенд ламп прожектора (дослід усередині світлової лабораторії) ----
    bst = lb.status()
    b_rank = lb.ranking()
    b_lead = next((r for r in b_rank if r["cls"] == "good"), None)
    b_crit = lb.CRIT
    b_dec = lb.decision()
    lead_group_w = None
    if b_dec:
        chosen = next(r for r in lb.dimmer_runs() if r["id"] == b_dec["chosen"])
        lead_group_w = chosen["group_w"]
    elif b_lead:
        at12 = next((c for c in lb.curve(b_lead["id"]) if abs(c["v"] - 12) < 0.6), None)
        lead_group_w = at12["group_w"] if at12 else None

    llab = llab.replace("{{BENCH_INTRO}}",
        '<p class="sub">Стенд збирався під інше питання: чи падає споживання лампи, коли '
        'занизити напругу. Поки він збирався, Іван підключив лампи через ШІМ-диммер — а той '
        'не садить вольти, він рубає живлення імпульсами, і тоді ватти падають у будь-якої '
        'лампи, хоч що в неї за драйвер. Тому вирішило інше: <b>чи дружить лампа з диммером</b>. '
        'Цього нема в жодній специфікації — тільки живцем. Дві з трьох на мінімумі тремтять, '
        'одна світить рівно; вона й обрана.</p>'
        if b_dec else
        '<p class="sub">Уся економія прожекторів тримається на одному припущенні — що при '
        'заниженій напрузі лампа бере менше струму. Це правда не для кожної MR16: усередині '
        'може стояти стабілізатор, і тоді лампа тримає свої ватти до порога, а потім просто '
        'гасне. Тому три лампи міряються на стенді однаково — струм і яскравість на кількох '
        'напругах — і кожна зводиться до показника <b>n</b> у P&nbsp;~&nbsp;(V/12)<sup>n</sup>. '
        'Чим більший n, тим більше ватт віддає лампа за той самий втрачений відсоток світла.</p>')

    llab = llab.replace("{{BENCH_TILES}}", "\n".join([
        tile("Вибір лампи",
             "закрито" if b_dec else f'{bst["measurements"]}',
             "" if b_dec else f'з {bst["expected"]}',
             f'{b_dec["date"]}, вирішив {b_dec["by"]}' if b_dec else "три лампи × сім напруг",
             "good" if b_dec else "warn"),
        tile("У роботу йде",
             (b_dec["lamp"]["name"] if b_dec else
              (b_lead["name"] if b_lead else "—")).split()[0],
             f'{b_dec["lamp"]["cct"]}K' if b_dec else
             (f'n={b_lead["n_power"]:.2f}' if b_lead else ""),
             "єдина, що на мінімумі диммера не мерехтить" if b_dec
             else "визначиться після замірів", "good" if b_dec else ""),
        tile("Група 8 прожекторів на 12 В",
             f"{lead_group_w:.0f}" if lead_group_w else "—", "Вт",
             f'ціль — тримати групу під {b_crit["target_group_w"]} Вт',
             "good" if lead_group_w and lead_group_w <= b_crit["target_group_w"] else ""),
        tile("Межа 12 В-виходу станції", f'{b_crit["dc_port_w"]}', "Вт",
             "стеля EcoFlow — 10 А; світло сюди влазить із запасом", "warn"),
    ]))

    b_rows = []
    for r in b_rank:
        n_p = f'{r["n_power"]:.2f}' if r["n_power"] is not None else "—"
        n_l = f'{r["n_lux"]:.2f}' if r["n_lux"] is not None else "—"
        col = {"good": "var(--good)", "warn": "var(--warn)",
               "crit": "var(--crit)", "wait": "var(--ink-2)"}[r["cls"]]
        b_rows.append(
            f'      <tr><td>{esc(r["name"])}</td><td>{esc(r["role"])}</td>'
            f'<td class="num">{r["cct"]}K</td><td class="num">{n_p}</td>'
            f'<td class="num">{n_l}</td>'
            f'<td class="num">{f"{r["v_off"]:.1f} В" if r["v_off"] else "—"}</td>'
            f'<td style="color:{col}">{esc(r["verdict"])}</td></tr>')
    llab = llab.replace("{{BENCH_LAMPS}}", "\n".join(b_rows))
    llab = llab.replace("{{BENCH_CAPTION}}", esc(
        f'{b_dec["why"]} {b_dec["not_done"]}' if b_dec else
        f'Показник n рахується як нахил прямої в логарифмах — по всіх точках, де лампа ще '
        f'світила. Слідує за напругою — від {b_crit["exp_vf"]}; тримає потужність — до '
        f'{b_crit["exp_cc"]}. ' + (
            "Даних поки нема: лампи в Івана, стенд зібраний, чекаємо перший прогін."
            if not bst["measurements"] else
            f'Знято {bst["measurements"]} точок з {bst["expected"]}.')))

    # Криві двома панелями: ватти і яскравість, обидві у відсотках від 12 В —
    # так лампи різної потужності лягають в один масштаб. Поки замірів нема,
    # замість графіка показуємо сітку напруг, які треба пройти.
    if bst["measurements"]:
        COLS = ["var(--accent)", "var(--signal)", "var(--good)"]
        panels = []
        for key, title in (("w_pct", "Скільки бере, % від 12 В"),
                           ("lux_pct", "Скільки світить, % від 12 В")):
            vs = [p["v"] for r in b_rank for p in lb.curve(r["id"])]
            vmin, vmax = min(vs), max(vs)
            W, H, PAD = 430, 240, 34
            sx = lambda v: PAD + (v - vmin) / (vmax - vmin) * (W - 2 * PAD)
            sy = lambda p: H - PAD - min(p, 120) / 120 * (H - 2 * PAD)
            g = [f'<line x1="{PAD}" y1="{sy(y)}" x2="{W-PAD}" y2="{sy(y)}" '
                 f'stroke="var(--line)"/><text x="{PAD-6}" y="{sy(y)+4}" text-anchor="end" '
                 f'font-size="10" fill="var(--ink-2)">{y}%</text>' for y in (0, 50, 100)]
            for i, r in enumerate(b_rank):
                pts = [(sx(c["v"]), sy(c[key])) for c in lb.curve(r["id"])
                       if c.get(key) is not None]
                if not pts:
                    continue
                d = " ".join(f'{x:.1f},{y:.1f}' for x, y in pts)
                g.append(f'<polyline points="{d}" fill="none" stroke="{COLS[i % 3]}" '
                         f'stroke-width="2"/>')
                g += [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{COLS[i % 3]}"/>'
                      for x, y in pts]
            for v in sorted({round(p, 1) for p in vs}):
                g.append(f'<text x="{sx(v):.1f}" y="{H-PAD+16}" text-anchor="middle" '
                         f'font-size="10" fill="var(--ink-2)">{v:g}</text>')
            g.append(f'<text x="{PAD}" y="18" font-size="12" fill="var(--ink)">{esc(title)}</text>')
            g.append(f'<text x="{W-PAD}" y="{H-6}" text-anchor="end" font-size="10" '
                     f'fill="var(--ink-2)">напруга на лампі, В</text>')
            panels.append(f'<svg viewBox="0 0 {W} {H}" style="width:100%;max-width:{W}px">'
                          + "".join(g) + "</svg>")
        legend = " · ".join(
            f'<span style="color:{COLS[i % 3]}">■</span> {esc(r["name"])}'
            for i, r in enumerate(b_rank))
        llab = llab.replace("{{BENCH_CHART}}",
            '<div class="fig" style="display:flex;gap:1rem;flex-wrap:wrap;margin-top:1.2rem">'
            + "".join(panels) + f'</div><p class="fig-cap">{legend}</p>')
    elif b_dec:
        llab = llab.replace("{{BENCH_CHART}}",
            '<p class="fig-cap" style="margin-top:1rem">Кривих по напрузі нема і не буде — '
            'лампу обрано раніше, ніж знадобився цей прогін. Стенд і протокол лишаються '
            'описаними нижче: якщо колись доведеться економити заниженням напруги замість '
            'ШІМ, повертатись буде куди.</p>')
    else:
        grid = ", ".join(f"{v:g}" for v in lb.B["points_v"])
        llab = llab.replace("{{BENCH_CHART}}",
            f'<p class="fig-cap" style="margin-top:1rem">Графіки зʼявляться після першого '
            f'прогону. Сітка напруг: {grid} В — на кожній записуємо струм і люкси.</p>')

    llab = llab.replace("{{BENCH_RIG}}", "".join(
        f'<p style="margin:0 0 .3rem"><b>{esc(k)}:</b> {esc(str(v))}</p>'
        for k, v in (("Джерело", lb.B["rig"]["supply"]),
                     ("Корпус", lb.B["rig"]["fixture"]),
                     ("Яскравість", lb.B["rig"]["meter"]),
                     ("Геометрія", lb.B["rig"]["geometry"]))))
    llab = llab.replace("{{BENCH_PROTOCOL}}", "".join(
        f'<p style="margin:0 0 .3rem">{i}. {esc(s)}</p>'
        for i, s in enumerate(lb.B["protocol"], 1)))

    # ---- стенд LED-стрічки (другий дослід світлової лабораторії) ----
    # Гейт проєкту: поки Вт/м не заміряні, сторінка чесно показує прикидку
    # через різницю і не робить вигляд, що число відоме.
    s_st = sb.status()
    s_kind, s_wpm = sb.source()
    s_prj = sb.project()
    s_head = sb.headroom()
    s_v_title, s_v_text, s_v_cls = sb.verdict()
    s_done = sb.measured()

    llab = llab.replace("{{STRIP_INTRO}}",
        f'<p class="sub">Уся адресна стрічка зірки — коло подіуму плюс вісім променів, '
        f'{sb.TOTAL_M:.2f} м разом — досі порахована по паспортних '
        f'{sb.CRIT["w_per_m_model"]:.0f} Вт/м. Ватметр {sb.B["indirect"]["date"]} каже інше: '
        f'коли Іван міряв вісім прожекторів разом із п\'ятьма метрами стрічки, '
        f'усе вийшло {sb.B["indirect"]["total_w"]:.0f} Вт, і на стрічку з них лишається '
        f'близько {sb.indirect_w_per_m():.1f} Вт/м — у п\'ять разів менше паспорта. '
        f'Різниця не косметична: {sb.project(sb.CRIT["w_per_m_model"])["peak_w"]:.0f} Вт проти '
        f'{sb.project(sb.indirect_w_per_m())["peak_w"]:.0f} Вт на піку, тобто «12-вольтовий '
        f'вихід станції не тягне» проти «тягне з запасом». Тому дослід і став гейтом: від нього '
        f'висить вибір станції, замовлення решти закупівлі і питання порту на 30 А.</p>')

    llab = llab.replace("{{STRIP_TILES}}", "\n".join([
        tile("Вт на метр", f"{s_wpm:.1f}", "Вт/м",
             "прямий замір на стенді" if s_kind == "measured"
             else f'прикидка через різницю · замір ще не робили',
             "good" if s_kind == "measured" else "warn"),
        tile("Уся стрічка на піку", f'{s_prj["peak_w"]:.0f}', "Вт",
             f'{sb.TOTAL_M:.2f} м білим на повній · {s_prj["peak_a"]:.1f} A',
             "good" if s_prj["fits_dc"] else "crit"),
        tile("За ніч на анімації", f'{s_prj["night_wh"]:.0f}', "Wh",
             f'частка світіння {s_prj["duty"]*100:.0f}%'
             + ("" if sb.duty() is not None else " — поки прикидка"),
             "" if sb.duty() is None else "good"),
        tile("Лишається після прожекторів",
             f'{s_head["left_w"]:.0f}' if s_head else "—", "Вт",
             (f'з {sb.CRIT["dc_port_w"]} Вт виходу; прожектори взяли '
              f'{s_head["spots_w"]:.0f} Вт') if s_head else "прожектори ще не обрані",
             "good" if s_head and s_head["fits"] else "crit"),
    ]))

    s_rows = []
    for s in sb.scenarios():
        col = {"good": "var(--good)", "warn": "var(--warn)",
               "wait": "var(--ink-2)"}[s["kind"]]
        fit = ('<span style="color:var(--good)">влазить</span>' if s["fits_dc"]
               else '<span style="color:var(--crit)">не влазить</span>')
        s_rows.append(
            f'      <tr><td style="color:{col}">{esc(s["label"])}</td>'
            f'<td class="num">{s["w_per_m"]:.1f}</td>'
            f'<td class="num">{s["peak_w"]:.0f} Вт · {s["peak_a"]:.1f} A</td>'
            f'<td class="num">{s["anim_w"]:.0f} Вт</td>'
            f'<td class="num">{s["night_wh"]:.0f}</td>'
            f'<td class="num">{fit} ({s["dc_load_pct"]:.0f}%)</td></tr>')
    if sb.w_per_m() is None:
        s_rows.append(
            '      <tr><td colspan="6" style="color:var(--ink-2)">Третій рядок — прямий '
            'замір — зʼявиться після прогону. Поки його нема, модель світла свідомо '
            'рахує по верхньому рядку: краще перезакласти ватти, ніж недобрати станцію.</td></tr>')
    llab = llab.replace("{{STRIP_SCENARIOS}}", "\n".join(s_rows))
    llab = llab.replace("{{STRIP_CAPTION}}", esc(
        f'{s_v_title.capitalize()}. {s_v_text} '
        + (sb.B["indirect"]["note"] if s_kind == "indirect" else
           f'Виміряні {s_wpm:.1f} Вт/м уже стоять у моделі світла.')))

    m_rows = []
    for i, md in enumerate(sb.modes(), 1):
        got = s_done.get(md["id"])
        val = (f'<span style="color:var(--good)">{sb._w(got):.1f} Вт</span>' if got
               else '<span style="color:var(--ink-2)">чекає</span>')
        m_rows.append(
            f'      <tr><td class="num">{i}</td><td>{esc(md["label"])}</td>'
            f'<td>{esc(md["record"])}</td>'
            f'<td style="white-space:normal;max-width:46ch">{esc(md["why"])}</td>'
            f'<td class="num">{val}</td></tr>')
    llab = llab.replace("{{STRIP_MODES}}", "\n".join(m_rows))
    llab = llab.replace("{{STRIP_MODES_CAPTION}}", esc(
        f'Знято {s_st["measurements"]} режимів з {s_st["expected"]}. '
        + sb.B["rig"]["must_record"] + " " + sb.B["temperature"]["why"]))

    llab = llab.replace("{{STRIP_RIG}}", "".join(
        f'<p style="margin:0 0 .3rem"><b>{esc(k)}:</b> {esc(str(v))}</p>'
        for k, v in (("Джерело", sb.B["rig"]["supply"]),
                     ("Прилад", sb.B["rig"]["meter"]),
                     ("Контролер", sb.B["rig"]["controller"]),
                     ("Стрічка", sb.B["rig"]["strip"]),
                     ("Де ватметр", sb.B["rig"]["note"]))))
    llab = llab.replace("{{STRIP_PROTOCOL}}", "".join(
        f'<p style="margin:0 0 .3rem">{i}. {esc(s)}</p>'
        for i, s in enumerate(sb.B["protocol"], 1)))

    # Профіль режимів: контролер сам каже, яку частку стрічки палить кожен ефект.
    s_prof = sb.B.get("effect_profile", {})
    s_fx = sb.effect_ranking()
    s_work = sb.duty_from_profile(187)
    llab = llab.replace("{{STRIP_FX_WHY}}", esc(
        f'{s_prof.get("why", "")} {s_prof.get("how", "")}'))
    fx_rows = []
    for i, e in enumerate(s_fx):
        lead = ' style="color:var(--good)"' if i == 0 else (
            ' style="color:var(--crit)"' if i == len(s_fx) - 1 else "")
        # Назва режиму — у підписі показуємо Ukrainian name якщо є
        uk = e.get("uk_name", "")
        display_name = f'{esc(uk)} <span style="color:var(--ink-2);font-size:.78em">{esc(e["name"])}</span>' if uk else esc(e["name"])
        uk_desc = f'<br><span style="color:var(--ink-2);font-size:.8em">{esc(e.get("uk_desc", ""))}</span>' if e.get("uk_desc") else ""
        working_mark = ' <span style="color:var(--ink-2)">← робочий</span>' if e["fx"] == 187 else ""
        # Превʼю: один основний клас + опційні додаткові через preview_extra
        p_cls = e.get("preview_class", "")
        p_extra = e.get("preview_extra", "")
        extra_divs = "".join(f'<div class="{c}"></div>' for c in p_extra.split() if c)
        preview_td = (f'<td><div class="fx-track"><div class="{p_cls}"></div>{extra_divs}</div></td>'
                      if p_cls else "<td></td>")
        fx_rows.append(
            f'      <tr><td{lead}>{display_name}{uk_desc}{working_mark}'
            + f'</td>{preview_td}'
            + f'<td class="num">{e["avg_pct"]:.1f}%</td>'
            f'<td class="num">{e["peak_pct"]:.1f}%</td>'
            f'<td class="num">{e["avg_w"]:.1f} Вт</td>'
            f'<td class="num">{e["peak_w"]:.1f} Вт</td>'
            f'<td class="num">{e["night_wh"]:.0f}</td></tr>')
    llab = llab.replace("{{STRIP_FX_ROWS}}", "\n".join(fx_rows))
    llab = llab.replace("{{STRIP_FX_CAPTION}}", esc(
        f'Відсоток — це частка стрічки, що світиться в еквіваленті повного білого; '
        f'ватти — та сама частка, помножена на {sb.source()[1]:.1f} Вт/м × '
        f'{sb.TOTAL_M:.2f} м. Модель світла досі закладає '
        f'{sb.CRIT["duty_model"]*100:.0f}% на анімацію — робочий «{s_work["name"]}» '
        f'бере {s_work["avg"]*100:.1f}%, тобто у '
        f'{sb.CRIT["duty_model"]/s_work["avg"]:.0f} разів менше, і навіть найважчий '
        f'з десяти лишається під закладеним. Знято на гілці '
        f'{s_prof.get("branch_px")} пікселів; на іншій довжині частка трохи поїде — '
        f'біжучий фронт масштабується разом із сегментом. '
        f'{sb.B["controller"]["estimate_note"]}'))

    # Прогін по напрузі: у прожекторів заниження було способом економити,
    # у стрічки це аварія, яку приносить кабель. Тому й таблиця інша.
    s_vr = sb.B.get("voltage_run", {})
    s_vt, s_vtext, s_vcls = sb.voltage_verdict()
    llab = llab.replace("{{STRIP_V_WHY}}", esc(
        f'{s_vr.get("_goal", "")} {s_vr.get("_why_it_matters", "")}'))
    llab = llab.replace("{{STRIP_V_PHYS}}", esc(s_vr.get("physics", "")))
    v_rows = []
    for r in sb.voltage_points():
        lim = ('<span style="color:var(--good)">так</span>' if r["within_limit"]
               else '<span style="color:var(--ink-2)">ні</span>')
        a_txt = f'{r["a"]:.2f} A' if r["a"] else "—"
        v_rows.append(
            f'      <tr><td class="num">{r["v"]:g} В</td>'
            f'<td class="num">{r["drop_pct"]:.1f}%</td><td>{lim}</td>'
            f'<td class="num">{a_txt}</td>'
            f'<td>{esc(r["color"]) if r["color"] else "чекає"}</td>'
            f'<td>{esc(r["glitches"]) if r["glitches"] else "чекає"}</td></tr>')
    llab = llab.replace("{{STRIP_V_ROWS}}", "\n".join(v_rows))
    llab = llab.replace("{{STRIP_V_CAPTION}}", esc(
        f'{s_vt.capitalize()}. {s_vtext} Порядок замірів: '
        + " ".join(f'{i}) {s}' for i, s in enumerate(s_vr.get("protocol", []), 1))))

    llab = llab.replace("{{STRIP_BRANCH_WHY}}", esc(sb.B["branch"]["why"]))
    b_rows = []
    for i, c in enumerate(sb.branch_checks(), 1):
        res = (f'<span style="color:var(--good)">{esc(c["result"])}</span>'
               if c["result"] else '<span style="color:var(--ink-2)">чекає</span>')
        b_rows.append(
            f'      <tr><td class="num">{i}</td><td>{esc(c["label"])}</td>'
            f'<td style="white-space:normal;max-width:52ch">{esc(c["look_for"])}</td>'
            f'<td>{res}{" · " + esc(c["note"]) if c["note"] else ""}</td></tr>')
    llab = llab.replace("{{STRIP_BRANCH}}", "\n".join(b_rows))
    llab = llab.replace("{{BUY_BLOCK}}", buy_block_html(
        "lights",
        note="Те саме світло, але списком на закупівлю: усе, що симулятор вище ганяє по ватах, тут стоїть із фото, лінком і ціною."))

    # ================= cables / installation page =================
    tree_op = lm.cable_tree_operating()
    tree_pk = lm.cable_tree()
    fuse_rows_data = lm.fuses()
    auto = LP["automation"]
    fusing = LP["fusing"]
    bad_op = [r for r in tree_op if not r["ok"]]
    bad_pk = [r for r in tree_pk if not r["ok"]]
    worst_op = max(tree_op, key=lambda r: r["cum_pct"])
    total_cable_m = sum(x["length_m"] for x in LP["topology"]["segments"])

    cables = tmpl("cables.tmpl.html")
    # схема щита і груп — та сама, що на сторінці світла; сторінка кабелів була
    # без жодної картинки (Іван 01.08: «додай всюди більше картинок»)
    _csvg = (LIGHTS / "model" / "panel_tree.svg").read_text()
    _csvg = re.sub(r"<\?xml[^>]*\?>\s*|<!DOCTYPE[^>]*>\s*", "", _csvg)
    cables = cables.replace("{{SCHEMATIC_SVG}}", _csvg)
    cab_tiles = [
        tile("Ділянок у дереві", f"{len(tree_op)}", "",
             f"від станції до кожного пристрою · ~{total_cable_m:.0f} м кабелю разом"),
        tile("Найдовший ланцюг", f"{worst_op['cum_pct']:.1f}", "%",
             f"{esc(worst_op['label'])} — на кінці {worst_op['v_at_end']:.1f} В",
             "good" if worst_op["ok"] else "warn"),
        tile("Робочий режим", "усе ok" if not bad_op else f"{len(bad_op)} не проходить", "",
             "те, що реально буде вночі", "good" if not bad_op else "crit"),
        tile("Паспортний пік", "усе ok" if not bad_pk else f"{len(bad_pk)} не проходить", "",
             "режим, якого не буде, але кабель рахуємо під нього",
             "good" if not bad_pk else "warn"),
        tile("Головний запобіжник", f"{fuse_rows_data[0]['rating']}", "A",
             f"робочий струм {fuse_rows_data[0]['amps']:.1f} A із запасом ×{fusing['derate']}"),
        tile("Вмикання світла",
             "фотореле" if auto["trigger"] == "photocell" else "вручну", "",
             (f"поріг {auto['lux_on']} лк, гасне на {auto['lux_off']}, "
              f"затримка {auto['delay_s']} с") if auto["trigger"] == "photocell"
             else "фотореле прибрано — чим вмикати Гр.1 і Гр.3А, ще не обрано",
             "good" if auto["trigger"] == "photocell" else "warn"),
    ]
    cables = cables.replace("{{TILES_HTML}}", "\n".join(cab_tiles))

    def seg_name(r):
        est = ' <span class="est">оцінка</span>' if r["estimate"] else ""
        return f'<td class="seg-name seg-d{r["depth"]}">{esc(r["label"])}{est}</td>'

    def verdict(r):
        if r["ok"]:
            return '<span class="pill have">ok</span>'
        if r["need_awg"]:
            return f'<span class="pill add">треба AWG {r["need_awg"]}</span>'
        return '<span class="pill tbd">лікувати вище по ланцюгу</span>'

    op_rows = []
    for r in tree_op:
        style_c = "" if r["ok"] else ' style="color:var(--crit)"'
        op_rows.append(
            f'      <tr>{seg_name(r)}<td class="num">AWG {r["awg"]}</td>'
            f'<td class="num">{r["length_m"]:.1f} м</td><td class="num">{r["amps"]:.2f} A</td>'
            f'<td class="num">{r["drop_pct"]:.2f}%</td>'
            f'<td class="num"{style_c}>{r["cum_pct"]:.2f}%</td>'
            f'<td class="num">{r["v_at_end"]:.2f} В</td><td>{verdict(r)}</td></tr>')
    cables = cables.replace("{{TREE_OP_ROWS}}", "\n".join(op_rows))
    cables = cables.replace("{{TREE_OP_CAPTION}}",
        (f'У робочому режимі проходить усе: найгірше місце — {esc(worst_op["label"].lower())} '
         f'з накопиченими {worst_op["cum_pct"]:.2f}%, на кінці лишається {worst_op["v_at_end"]:.2f} В. '
         if not bad_op else
         f'Не проходять {len(bad_op)} ділянки навіть у робочому режимі — це вже треба лікувати. ')
        + 'Відступ у першій колонці показує глибину: кожен рівень додає свою просадку до всіх, '
          'хто нижче. Позначка «оцінка» — довжина ще не міряна по факту.')

    pk_rows = []
    for r in tree_pk:
        style_c = "" if r["ok"] else ' style="color:var(--crit)"'
        pk_rows.append(
            f'      <tr>{seg_name(r)}<td class="num">AWG {r["awg"]}</td>'
            f'<td class="num">{r["amps"]:.2f} A</td>'
            f'<td class="num">{r["drop_pct"]:.2f}%</td>'
            f'<td class="num"{style_c}>{r["cum_pct"]:.2f}%</td>'
            f'<td class="num">{r["budget_pct"]:.0f}%</td><td>{verdict(r)}</td></tr>')
    cables = cables.replace("{{TREE_PEAK_ROWS}}", "\n".join(pk_rows))
    budget = LP["wiring"]["drop_budget"]
    cables = cables.replace("{{TREE_PEAK_CAPTION}}",
        f'Межі різні навмисно: {budget["strict_pct"]:.0f}% для адресної стрічки і '
        f'{budget["relaxed_pct"]:.0f}% для звичайних ламп. {esc(budget["note"])} '
        + (f'На піку не проходить {len(bad_pk)} ділянка — лінія стрічки. Лікується лімітом струму '
           f'у WLED, а не товщою міддю.'
           if bad_pk else "На піку проходить усе."))

    f_rows = "\n".join(
        f'      <tr><td>{esc(f["label"])}</td><td class="num">{f["amps"]:.1f} A</td>'
        f'<td class="num">{f["amps"]*fusing["derate"]:.1f} A</td>'
        f'<td class="num"><b>{f["rating"]} A</b></td></tr>' for f in fuse_rows_data)
    cables = cables.replace("{{FUSE_ROWS}}", f_rows)
    cables = cables.replace("{{DERATE}}", str(fusing["derate"]))
    cables = cables.replace("{{FUSE_CAPTION}}", esc(fusing["note"]) +
        " Окремі запобіжники на групи потрібні саме для того, щоб коротке в одній гілці "
        "не гасило всю інсталяцію — вночі на плайї це різниця між «одна гілка не світить» "
        "і «фігура зникла».")

    grp_lbl = {k: v["label"] for k, v in LP["groups"].items()}
    auto_html = [
        f'    <div class="kit-item">\n      <h3>Чим вмикається</h3>\n'
        f'      <p>{esc(auto["note"])}</p>\n    </div>']
    for c in auto["controls"]:
        auto_html.append(
            f'    <div class="kit-item">\n      <h3>{esc(grp_lbl[c["group"]])}</h3>\n'
            f'      <p>{esc(c["via"])} — {esc(c["note"])}</p>\n    </div>')
    cables = cables.replace("{{AUTOMATION_HTML}}", "\n".join(auto_html))

    kit_items = [b for b in BOM if b["system"] == "lights"
                 and not b["item"].startswith("Кабель:")
                 and any(w in b["item"].lower() for w in ("щит", "запобіжник", "реле",
                                                          "гермокоробка", "гермокоробки", "гермороз",
                                                          "гель-конектори", "гофра", "вимикач"))]
    k_rows = "\n".join(
        f'      <tr><td>{esc(b["item"])}</td><td class="num">{esc(b["qty"])}</td>'
        f'<td><span class="pill {pill_of(b)[0]}">{pill_of(b)[1]}</span></td>'
        f'<td>{esc(b["note"])}</td></tr>' for b in kit_items)
    cables = cables.replace("{{KIT_ROWS}}", k_rows)
    cables = cables.replace("{{KIT_CAPTION}}",
        "Кабель на кожну ділянку дерева заведено в закупівлю окремими рядками — шукай їх у "
        "загальному списку на головній за префіксом «Кабель:». Головне правило по коробках: "
        "вентиляція важливіша за герметичність. Глухо закритий бокс на сонці плайї перегріється "
        "швидше, ніж у нього набʼється пил.")

    # Рішення і відкриті питання по світлу живуть ОДИН раз — на сторінці системи.
    # До 07.08 той самий список друкувався і тут повністю: обидва блоки фільтрували
    # DECISIONS однаково по system == "lights". Це і був найбільший дубль на сайті.
    cables = cables.replace("{{DECISIONS_HTML}}",
        f'    <p class="sub">Рішення і відкриті питання по світлу — одним списком на '
        f'сторінці <a href="{SITE_URL}lights.html">Світло</a>, щоб не розходились дві копії.</p>')
    cables = cables.replace("{{FLAGS_HTML}}", "")

    # ================= power node page + lab =================
    PP = pw.P
    p_demand = pw.demand()
    p_cases = {c["key"]: pw.run_case(c) for c in pw.CASES_DOC["cases"]}
    p_opts = pw.station_options()
    st_name, st_spec = pw.station()
    p_chosen = next(o for o in p_opts if o["name"] == st_name)
    p_sunny, p_dead = p_cases["sunny"], p_cases["dead"]
    breakeven = pw.break_even_panel_w()

    solar_page = tmpl("solar.tmpl.html")
    psvg = (SOLAR / "model" / "schematic.svg").read_text()
    psvg = re.sub(r"<\?xml[^>]*\?>\s*|<!DOCTYPE[^>]*>\s*", "", psvg)
    solar_page = solar_page.replace("{{SCHEMATIC_SVG}}", psvg)

    solar_tiles = [
        tile("Уся система жере", f"{p_demand['total']:.0f}", "Wh/добу",
             f"світло {p_demand['lights']:.0f} + звук {p_demand['audio']:.0f} "
             f"+ холостий хід станції {p_demand['standby']:.0f}", "good"),
        tile("Панель в нуль", f"~{breakeven:.0f}", "Вт",
             f"{PP['panel']['chosen_w']} Вт узято лише як точку відліку — не рішення"),
        tile("Ясна доба", f"{p_sunny['balance_wh']:+.0f}", "Wh",
             f"панель дає {p_sunny['gen_wh']:.0f}, система бере {p_sunny['demand_wh']:.0f}", "good"),
        tile("Без панелей", f"{p_dead['days_to_swap']:.1f}", "доби",
             "стільки тримає повна станція, якщо масив став — далі підміна", "crit"),
        tile("Запилені панелі", f"{p_cases['dusty']['days_to_swap']:.1f}", "діб",
             "при 60% сонця вже йдемо в мінус — мити скло щоранку", "warn"),
        tile("Зарядка на базі", f"{p_chosen['recharge_h']:.1f}", "год",
             f"{esc(st_name)} від розетки — обіг швидкий, але станцій треба дві"),
    ]
    solar_page = solar_page.replace("{{DIAGRAMS}}", diagrams_html("solar"))
    solar_page = solar_page.replace("{{FIGURES}}", figures_html("solar"))
    solar_page = solar_page.replace("{{PHOTOS}}", photos_html("solar"))
    # Сторінка системи показує ВЕСЬ свій зріз реєстру закупівлі, без слів-фільтрів:
    # тут людина читає про живлення цілком, отже й купувати має бачити цілком.
    solar_page = solar_page.replace("{{BUY_BLOCK}}", buy_block_html(
        "solar",
        note="Уся закупівля по живленню: станція, сонячний масив, рама під нього, "
             "кабелі, прилади контролю та інструмент. Зріз єдиного реєстру за "
             "системою — вужчі підбірки є в лабораторії живлення і на сторінці кабелю."))
    solar_page = solar_page.replace("{{TILES_HTML}}", "\n".join(solar_tiles))

    d_rows, d_labels = [], {"lights": "Світло", "audio": "Звук",
                            "standby": "Холостий хід станції"}
    d_notes = {c["node"]: c["note"] for c in PP["consumers"]}
    d_notes["standby"] = "станція витрачає на себе, навіть коли нічого не увімкнено"
    for k in ("lights", "audio", "standby"):
        v = p_demand[k]
        d_rows.append(
            f'      <tr><td>{d_labels[k]}</td><td class="num">{v:.0f}</td>'
            f'<td class="num">{100*v/p_demand["total"]:.0f}%</td>'
            f'<td>{esc(d_notes.get(k, ""))}</td></tr>')
    solar_page = solar_page.replace("{{DEMAND_ROWS}}", "\n".join(d_rows))
    solar_page = solar_page.replace("{{DEMAND_CAPTION}}",
        f'Ці числа не вписані руками — модель живлення тягне їх прямо з моделей світла і звуку. '
        f'Змінив режим світла — тут переїде саме. Світло з\'їдає '
        f'{100*p_demand["lights"]/p_demand["total"]:.0f}% усього, звук — менше трьох відсотків.')

    s_decs = [d for d in DECISIONS if d["system"] == "solar"]
    solar_page = solar_page.replace("{{DECISIONS_HTML}}", "\n".join(
        f'    <div class="decision">\n      <h3>{esc(d["title"])}</h3>\n'
        f'      <p><span class="why">чому</span> · {d["why"]}</p>\n    </div>'
        for d in s_decs if not d.get("open")))
    solar_page = solar_page.replace("{{FLAGS_HTML}}", "\n".join(
        f'  <div class="flag">\n    <h3>{esc(d["title"])}</h3>\n'
        f'    <p><span class="why">відкрите</span> · {d["why"]}</p>\n  </div>'
        for d in s_decs if d.get("open")))

    c_rows = []
    for c in pw.CASES_DOC["cases"]:
        r = p_cases[c["key"]]
        swap = "—" if r["days_to_swap"] == float("inf") else f'{r["days_to_swap"]:.1f} діб'
        bal = r["balance_wh"]
        b_style = ' style="color:var(--crit)"' if bal < 0 else ""
        c_rows.append(
            f'      <tr><td>{esc(r["case"])}</td><td class="num">{c["sun_factor"]*100:.0f}%</td>'
            f'<td class="num">{r["gen_wh"]:.0f} Wh</td>'
            f'<td class="num">{r["demand_wh"]:.0f} Wh</td>'
            f'<td class="num"{b_style}>{bal:+.0f} Wh</td>'
            f'<td class="num">{swap}</td></tr>')
    solar_page = solar_page.replace("{{CASE_ROWS}}", "\n".join(c_rows))
    solar_page = solar_page.replace("{{CASE_CAPTION}}",
        f'«До підміни» — скільки діб тримає повна станція {esc(st_name)}, поки не з\'їсть робочий '
        f'запас (ємність мінус {PP["station"]["reserve_frac"]*100:.0f}% недоторканого резерву). '
        f'Головне тут — рядок про непрацюючі панелі: доба. Тобто масив не страховка, а несуча '
        f'частина системи, і друга станція має бути зарядженою заздалегідь, а не «якось потім».')

    st_rows = []
    for o in p_opts:
        swap = "тримає" if o["days_to_swap"] == float("inf") else f'{o["days_to_swap"]:.1f} діб'
        cap = "" if o["panel_used_w"] >= PP["panel"]["chosen_w"] else \
              f' <span class="pill add">бере лише {o["panel_used_w"]:.0f} Вт</span>'
        mark = ""  # жодна станція ще не обрана — не позначаємо «вибрану»
        b_style = ' style="color:var(--crit)"' if o["balance_wh"] < 0 else ""
        st_rows.append(
            f'      <tr><td><b>{esc(o["name"])}</b>{mark}</td><td class="num">{o["wh"]} Wh</td>'
            f'<td class="num">{o["solar_in_w"]} Вт{cap}</td>'
            f'<td class="num"{b_style}>{o["balance_wh"]:+.0f} Wh</td>'
            f'<td class="num">{o["nights_no_sun"]:.1f} діб</td>'
            f'<td class="num">{o["recharge_h"]:.1f} год</td></tr>')
    # перевірка «чи пролізе пік по 12 В» — вузьке місце, знайдене 29.07
    for i, o in enumerate(p_opts):
        hr = pw.dc12_headroom(o["name"])
        badge = (f'<span class="pill have">{hr["limit_w"]:.0f} Вт через {hr["port"]}</span>'
                 if hr["fits"] else
                 f'<span class="pill add">лише {hr["limit_w"]:.0f} Вт по 12 В — пік не пролізе</span>')
        st_rows[i] = st_rows[i].replace("</tr>", f"<td>{badge}</td></tr>")
    solar_page = solar_page.replace(
        "<th>Зарядка на базі</th>", "<th>Зарядка на базі</th><th>12 В вихід</th>")
    solar_page = solar_page.replace("{{STATION_ROWS}}", "\n".join(st_rows))
    solar_page = solar_page.replace("{{STATION_CAPTION}}",
        f'Рахунок при орієнтовному масиві {PP["panel"]["chosen_w"]} Вт і композитній добі {p_demand["total"]:.0f} Wh. '
        f'Дві менші станції фізично не приймуть увесь масив — у них нижча стеля сонячного входу, '
        f'і зайві вати просто пропадуть. {esc(PP["_verify"])}')

    # ---- power lab ----
    slab = tmpl("solar_lab.tmpl.html")
    _spsvg = (SOLAR / "model" / "site_plan.svg").read_text()
    _spsvg = re.sub(r"<\?xml[^>]*\?>\s*|<!DOCTYPE[^>]*>\s*", "", _spsvg)
    slab = slab.replace("{{SITE_PLAN_SVG}}", _spsvg)
    pl, base = PP["playa"], PP["base"]
    _, l_res_for_lab = lm.composite_night()
    light_cases = {"composite": {"wh": wh_light, "label": "композитна ніч"}}
    for c in lm.CASES_DOC["cases"]:
        r = l_res_for_lab[c["key"]]
        light_cases[c["key"]] = {"wh": r["draw_w"] * r["hours"], "label": c["name"]}
    slab = slab.replace("{{JS_CONST}}",
        f'const AUDIO_WH={p_demand["audio"]:.1f}, STANDBY_W={PP["station"]["standby_w"]}, '
        f'USABLE={PP["station"]["usable_frac"]}, BASE_AC_W={base["ac_charge_w"]};\n'
        f'  const DUST={pl["dust_derate"]}, HEAT={pl["heat_derate"]}, CABLE={pl["cable_derate"]};')
    slab = slab.replace("{{STATIONS_JSON}}", json.dumps(PP["stations"], ensure_ascii=False))
    slab = slab.replace("{{LIGHT_CASES_JSON}}", json.dumps(light_cases, ensure_ascii=False))
    slab = slab.replace("{{STATION_DEFAULT}}", json.dumps(st_name, ensure_ascii=False))
    slab = slab.replace("{{LIGHT_DEFAULT}}", json.dumps("composite"))
    slab = slab.replace("{{STATION_BTNS}}", "\n        ".join(
        f'<button data-s="{esc(n)}"{" class=\'active\'" if n == st_name else ""}>'
        f'{esc(n)} · {v["wh"]} Wh</button>' for n, v in PP["stations"].items()))
    slab = slab.replace("{{LIGHT_BTNS}}", "\n        ".join(
        f'<button data-c="{esc(k)}"{" class=\'active\'" if k == "composite" else ""}>'
        f'{esc(v["label"])}</button>' for k, v in light_cases.items()))
    # гіпотези живлення: чи пролізе пік кожним шляхом (рахуємо, не вписуємо)
    # звук живиться окремим кабелем від авто-виходу (рішення Івана 29.07),
    # тому в ліміт силового шляху до світла він не входить
    pk = max(r["draw_w"] for r in l_res_for_lab.values())
    path_rows = []
    for pp in PP.get("power_paths", {}).get("paths", []):
        fits = pk <= pp["limit_w"]
        cls = "good" if fits else "crit"
        verdict = ("пролізає" if fits else "не пролізає")
        cost = "—" if not pp["cost_usd"] else f'${pp["cost_usd"]}'
        loss = "—" if not pp["losses_pct"] else f'{pp["losses_pct"]}%'
        path_rows.append(
            f'      <tr><td><b>{esc(pp["name"])}</b></td>'
            f'<td class="num">{pp["limit_w"]} Вт / {pp["limit_a"]} А</td>'
            f'<td class="num"><span class="pill {"have" if fits else "add"}">'
            f'{pk:.0f} Вт — {verdict}</span></td>'
            f'<td class="num">{cost}</td><td class="num">{loss}</td>'
            f'<td class="num">{"так" if pp["solder"] else "ні"}</td>'
            f'<td>{esc(pp["note"])}</td></tr>')
    # каталог станцій: вердикт рахуємо від нашого піку, ціни — з даних
    VERD = {"best": ("have", "найкраща"), "ok": ("have", "підходить"),
            "hack": ("tbd", "через хак"), "weak": ("add", "не тягне")}
    cat_rows = []
    for st in PP.get("station_catalog", {}).get("stations", []):
        vcls, vlab = VERD.get(st["verdict"], ("tbd", "?"))
        fits = pk <= st["dc12_w"]
        used = f'${st["used_usd"]}' if st.get("used_usd") else "—"
        cat_rows.append(
            f'      <tr><td><b>{esc(st["name"])}</b></td>'
            f'<td class="num">{st["wh"]} Wh</td>'
            f'<td>{esc(st["port"])}</td>'
            f'<td class="num"><span class="pill {"have" if fits else "add"}">'
            f'{st["dc12_w"]} Вт</span></td>'
            f'<td class="num">{st["solar_w"]} Вт</td>'
            f'<td class="num">${st["new_usd"]}</td>'
            f'<td class="num">{used}'
            + (f'<br><span style="font-size:.7rem;color:var(--ink-2);white-space:normal">'
               f'{esc(st["used_note"])}</span>'
               if st.get("used_usd") and st.get("used_note") else "") + '</td>'
            + f'<td><span class="pill {vcls}">{vlab}</span><br>'
            f'<span style="font-size:.74rem;color:var(--ink-2)">{esc(st["why"])}</span></td></tr>')
    slab = slab.replace("{{STATION_CATALOG}}", "\n".join(cat_rows))
    slab = slab.replace("{{POWER_PATHS}}", "\n".join(path_rows))
    slab = slab.replace("{{PRESETS_JSON}}", json.dumps([
        dict(name=c["name"], panel=PP["panel"]["chosen_w"],
             sun=round(c["sun_factor"] * 100), sunh=pl["sun_hours"],
             reserve=round(PP["station"]["reserve_frac"] * 100),
             light=c.get("light_case") or "composite")
        for c in pw.CASES_DOC["cases"] if c.get("dashboard")], ensure_ascii=False))

    # ================= cable-picker lab =================
    # Та сама фізика, що на cables.html, але інтерактивно: калібр рахує JS із
    # опорів/меж/наявності з lights params; готові силові шляхи — ті самі
    # path_rows, що і в лабораторії живлення (не дублюємо джерело).
    clab = tmpl("cables_lab.tmpl.html")
    W, FZ = lm.WIRE, lm.FUSE
    bud = W["drop_budget"]
    strict_ids = set(bud["strict_ids"])
    stock = W.get("stock_awg", [])
    clab = clab.replace("{{JS_CONST}}",
        f'const AWG_OHM={json.dumps(W["awg_ohm_per_m"])};\n'
        f'  const BUS_V={lm.BUS_V}, WARN={W["drop_warn_pct"]}, '
        f'STRICT_PCT={bud["strict_pct"]}, RELAXED_PCT={bud["relaxed_pct"]};\n'
        f'  const STOCK={json.dumps(stock)}, DERATE={FZ["derate"]}, '
        f'FUSE_SERIES={json.dumps(FZ["standard_a"])};')
    clab = clab.replace("{{PRESETS_JSON}}", json.dumps(
        [dict(label=r["label"], length_m=r["length_m"], amps=round(r["amps"], 1),
              strict=(r["id"] in strict_ids)) for r in lm.cable_tree()],
        ensure_ascii=False))
    clab = clab.replace("{{STRICT}}", f'{bud["strict_pct"]:g}')
    clab = clab.replace("{{RELAXED}}", f'{bud["relaxed_pct"]:g}')
    clab = clab.replace("{{DERATE}}", f'{FZ["derate"]:g}')
    clab = clab.replace("{{STOCK_LABEL}}", " і ".join(str(a) for a in stock) + " AWG")
    clab = clab.replace("{{POWER_PATHS}}", "\n".join(path_rows))
    clab = clab.replace("{{BUY_BLOCK}}", _cables_buy_block())

    # ================= схеми: зміст, а не друга копія =================
    # Було: сторінка вбудовувала кожну схему повністю ще раз — 560 КБ, з яких
    # 90% дублі того, що вже є на сторінках систем (Іван, 07.08: «дуже багато
    # дублікатів»). Стало: карта схем із підписами і лінком туди, де схема
    # живе разом зі своїми числами.
    SCHEME_MAP = [
        ("💡 Світло", [
            ("circuit_main.svg", "Світло цілком: станція → головний запобіжник → щит → три групи",
             "lights.html"),
            ("panel_tree.svg", "Щит і кабельне дерево: кожна ділянка з калібром, струмом і просадкою",
             "cables.html"),
            ("podium_plan.svg", "План подіуму згори: прожектори, рукави стрічки, врізні вогні, кабель до ящика",
             "lights.html"),
            ("spot_ring.svg", "Прожектори: як іде кабель по периметру від стійки до стійки",
             "spots.html"),
            ("circuit_g1.svg", "Прожектори, електрика: реле, ШІМ-диммер, замкнуте кільце, відвід на стійку",
             "spots.html"),
            ("strip_layout.svg", "Стрічка: вісім рукавів, ввід живлення у центрі, куди біжить хвиля",
             "strip.html"),
            ("circuit_g2_strip.svg", "Стрічка, електрика: WLED з конденсатором і буфером даних, центральний вузол",
             "strip.html"),
            ("body_route.svg", "Лампи робота: де яка сидить на фігурі і якою трасою до неї йде дріт",
             "body_lamps.html"),
            ("body_wiring.svg", "Лампи робота, електрика: клемний вузол Wago, кожна лампа своєю парою",
             "body_lamps.html"),
            ("edge_section.svg", "Аварійна лінія: розріз вузла врізного вогню в торці сходинки",
             "edge_lights.html"),
            ("circuit_g3a.svg", "Аварійна лінія, електрика: вісім граней по три вогні і хвіст на ящик",
             "edge_lights.html"),
            ("back_core_face.svg", "Ядро на спині в лоб: плата на 241 діод і те саме крізь біле вікно",
             "back_core_lab.html"),
            ("back_core_section.svg", "Ядро на спині в розрізі: чому плата стоїть углиб, а не впритул",
             "back_core_lab.html"),
            ("back_core_wiring.svg", "Ядро на спині: живлення від шини через понижувач до модуля",
             "back_core_lab.html"),
        ]),
        ("🔊 Звук", [
            ("schematic.svg", "Аудіо-вузол по пінах: радар → ESP32 → ЦАП → підсилювач → динамік",
             "audio.html"),
            ("signal_chain.svg", "Сигнальний тракт: що з чим говорить і в якому форматі", "audio.html"),
            ("power_chain.svg", "Живлення звуку: свій кабель від авто-виходу повз щит світла",
             "audio.html"),
            ("speaker_mount.svg", "Динамік у броні: отвір, фланець, глибина, мембрана вниз", "audio.html"),
        ]),
        ("🔋 Живлення", [
            ("site_plan.svg", "Розкладка на плайї: подіум, ящик станції, масив і траса кабелю", "solar.html"),
            ("frame.svg", "Рама під панелі: кути, розкрій дощок і вітрове навантаження", "solar.html"),
        ]),
        ("🛡️ Броня і ящик", [
            ("robot_fixtures.svg", "Що змонтовано на фігурі: лампи, динамік, вікно радара, ядро, стрічка",
             "armor.html"),
            ("night_visibility.svg", "Помітність уночі: чому мікропризма повертає промінь, а фарба ні",
             "armor.html"),
            ("box_marking.svg", "Ящик станції вночі: маркери, катафоти і стрічка по периметру",
             "enclosure.html"),
        ]),
    ]
    schemes = tmpl("schemes.tmpl.html")
    sch_toc, sch_blocks = [], []
    for group, rows in SCHEME_MAP:
        anchor = "sch-" + str(abs(hash(group)) % 9999)
        sch_toc.append(f'<a href="#{anchor}">{esc(group)}</a>')
        cards = []
        for fname, cap, page in rows:
            cards.append(
                f'<tr><td><a href="{SITE_URL}{page}">{esc(cap)}</a></td>'
                f'<td><a href="{SITE_URL}{page}">{esc(page[:-5])}</a></td></tr>')
        sch_blocks.append(
            f'  <h2 id="{anchor}">{esc(group)}</h2>\n'
            f'  <div class="tbl-wrap"><table><thead><tr><th>Схема</th>'
            f'<th>Де вона живе</th></tr></thead><tbody>\n'
            + "\n".join(cards) + '\n</tbody></table></div>')
    schemes = (schemes
               .replace("{{SCHEMES_TOC}}",
                        (LAB_CSS + '\n  <nav class="labs-strip" aria-label="Схеми">'
                         '<span class="lead">на сторінці</span> '
                         + " · ".join(sch_toc) + "</nav>"))
               .replace("{{SCHEMES_HTML}}", "\n".join(sch_blocks))
               .replace("{{GEN_DATE}}", today.isoformat()))


    # ================= paint page (розпис робота) =================
    # Окрема сторінка, а не блок на сторінці броні: там світло, лампи і катафоти,
    # і палітра в тому сусідстві губилась (зауваження Івана 12.08.2026).
    paint = tmpl("paint.tmpl.html")
    pal = json.loads((ROOT / "armor/data/palette.json").read_text())
    dia = ""
    svg_f = ROOT / "armor/model/palette.svg"
    if svg_f.exists():
        svg = svg_f.read_text()
        dia = ('  <figure class="dia">\n' + svg[svg.index("<svg"):] +
               '\n    <figcaption>Схема палітри: ліворуч оригінал Захара з виносками на зони, '
               'праворуч для кожної зони тінь, основний тон і світло з кодами.</figcaption>\n  </figure>')
    zone_cards = []
    for z in pal["zones"]:
        zone_cards.append(
            f'  <div class="zone">\n'
            f'    <div>\n      <div class="sw">'
            f'<div style="background:{z["shadow"]}"></div>'
            f'<div style="background:{z["hex"]}"></div>'
            f'<div style="background:{z["light"]}"></div></div>\n'
            f'      <div class="sw-cap">тінь {z["shadow"]} · <b>{z["hex"]}</b> · світло {z["light"]}</div>\n'
            f'    </div>\n'
            f'    <div>\n      <h3>{esc(z["label"])}</h3>\n'
            f'      <p class="code">{z["hex"]}<span class="meta">  ціль для фарби {z.get("target", z["hex"])}</span></p>\n'
            f'      <p>{esc(z["where"])}</p>\n'
            f'      <p class="meta">{esc(z["finish"])} · {esc(z["share"])}</p>\n'
            f'      <p>{esc(z.get("note", ""))}</p>\n    </div>\n  </div>')
    paint_rows = [b for b in BOM if b.get("tag") == "paint"]
    paint = (paint
             .replace("{{PALETTE_DIA}}", dia)
             .replace("{{ZONES_HTML}}", "\n".join(zone_cards))
             .replace("{{PAINT_BUY}}", photo_wall_html(paint_rows) + buy_table_html(paint_rows))
             .replace("{{GEN_DATE}}", today.isoformat()))

    # ================= transport page (як везмо фігуру) =================
    # Окрема сторінка, бо питання «у що вона влазить» вирішує вибір машини,
    # а це гроші і строки. Схема і числа — з project/data/transport.json.
    tr = tmpl("transport.tmpl.html")
    TRD = json.loads((ROOT / "project/data/transport.json").read_text())
    tsvg = ROOT / "project/model/transport_load.svg"
    tdia = ""
    if tsvg.exists():
        sv = tsvg.read_text()
        tdia = ('  <figure class="dia">\n' + sv[sv.index("<svg"):] +
                '\n    <figcaption>Як фігура лежить у кузові: лицем вниз, труба в плечах, '
                'каркас під 90° вперед і дві рейки вниз до металевого багатокутника основи. '
                'Нижче — вантажні обʼєми машин у тому ж масштабі.</figcaption>\n  </figure>')
    b = TRD["box_in"]
    how = (f'<ul>\n<li>Габарит перевезення: <b>{b["l"]}″ × {b["w"]}″ × {b["h"]}″</b> '
           f'({b["l"]//12}×{b["w"]//12}×{b["h"]//12} фути) — це фігура РАЗОМ із рамою.</li>\n'
           f'<li>Фігура лежить <b>лицем вниз</b>: так захищені лице і груди, а ядро на спині зверху.</li>\n'
           f'<li>У плечі — поперечна труба; від неї каркас під 90° вперед і дві рейки вниз '
           f'до металевого багатокутника основи.</li>\n'
           f'<li>З боків запас: у плечах {TRD["figure"]["shoulders_in"]}″ проти {b["w"]}″ кузова.</li>\n</ul>')
    rows = []
    for v in TRD["vans"]:
        fits = v["len_in"] >= b["l"] and v["w_in"] >= b["w"] and v["h_in"] >= b["h"]
        rows.append(f'<tr><td>{esc(v["name"])}</td><td>{v["len_in"]}″</td><td>{v["w_in"]}″</td>'
                    f'<td>{v["h_in"]}″</td><td>{"так" if fits else "ні — " + esc(v.get("why", ""))}</td></tr>')
    vans = ('<table class="tbl"><thead><tr><th>машина</th><th>довжина</th><th>ширина</th>'
            '<th>висота</th><th>влазить</th></tr></thead><tbody>' + "".join(rows) + '</tbody></table>')
    rent = TRD.get("rent_html", "")
    tdec = [d for d in DECISIONS if d.get("system") == "project" and "транспорт" in (d.get("title", "") + d.get("why", "")).lower()]
    ttask = [t for t in TASKS if t.get("system") == "project" and "транспорт" in t.get("task", "").lower()]
    tr = (tr.replace("{{LEAD}}", esc(TRD["note"]))
            .replace("{{DIAGRAM}}", tdia)
            .replace("{{HOW_HTML}}", how)
            .replace("{{MINIVAN}}", (lambda m: (
                f'<div class="card"><h3>Підходить рівно одна — {esc(m["only_one"])}</h3>'
                f'<p>{esc(m["why"])}</p>'
                f'<p><b>Ризик:</b> {esc(m["risk"])}</p>'
                f'<p><b>Що робити:</b> {esc(m["advice"])}</p>'
                f'<p class="meta">{esc(m["alternatives"])}</p></div>'))(TRD["minivan_verdict"]))
            .replace("{{VANS_HTML}}", vans)
            .replace("{{RENT_HTML}}", rent)
            .replace("{{DEC_HTML}}", "".join(
                f'<div class="card"><h3>{esc(d.get("title",""))}</h3><p>{d.get("why","")}</p></div>'
                for d in tdec) or '<p class="meta">поки нема</p>')
            .replace("{{TASK_HTML}}", "<ul>" + "".join(
                f'<li>{esc(t.get("task",""))} <span class="meta">— {esc(t.get("status",""))}</span></li>'
                for t in ttask) + "</ul>" if ttask else "")
            .replace("{{GEN_DATE}}", today.isoformat()))

    # ================= ops page =================
    ops = tmpl("ops.tmpl.html")
    if ADDR.get("move_date"):
        move = date.fromisoformat(ADDR["move_date"])
        cutoff = move.toordinal() - ADDR["typical_delivery_days"] - ADDR["move_buffer_days"]
        left = move.toordinal() - today.toordinal()
        if today.toordinal() >= cutoff:
            ship = (f'<div class="banner">📦 Переїзд LA→SF {ADDR["move_date"]} (за {left} дн.) — '
                    f'нові замовлення вже слати на <b>San Francisco</b>.</div>')
        else:
            ship = (f'<div class="banner ok">📦 Зараз шлемо в Los Angeles. Після '
                    f'{date.fromordinal(cutoff).isoformat()} — на San Francisco '
                    f'(переїзд {ADDR["move_date"]}, доставка ~{ADDR["typical_delivery_days"]} дн. '
                    f'+ буфер {ADDR["move_buffer_days"]}).</div>')
    else:
        ship = ('<div class="banner">⚠ Дата переїзду LA→SF не задана '
                '(<span style="font-family:var(--mono)">data/addresses.json → move_date</span>) — '
                'ship-to порадник не працює. Правило вручну: якщо доставка може приїхати після '
                'переїзду — слати одразу на SF.</div>')
    ops = ops.replace("{{SHIPTO_HTML}}", ship)

    tracking = PRIVATE.get("tracking", {})
    orows = []
    for o in ORDERS:
        days = today.toordinal() - date.fromisoformat(o["date"]).toordinal()
        vendor = f'<a href="{o["url"]}">{esc(o["vendor"])}</a>' if o.get("url") else esc(o["vendor"])
        trk = tracking.get(o["id"])
        trk_s = f'{esc(trk["carrier"])} {esc(trk["number"])}' if trk else '<span class="comp">private</span>'
        dest = dest_label(o)
        orows.append(
            f'      <tr><td class="num">{o["id"]}</td><td class="num">{o["date"]}</td>'
            f'<td class="num">{days}</td><td>{vendor}</td>'
            f'<td>{esc("; ".join(o["items"]))}</td>'
            f'<td><span class="pill {o["status"]}">{ORDER_STATUS[o["status"]]}</span></td>'
            f'<td>{esc(dest)}</td><td class="num">{trk_s}</td><td>{esc(o.get("note", ""))}</td></tr>')
    if not orows:
        orows.append('      <tr><td colspan="9">Поки нічого не замовлено.</td></tr>')
    ops = ops.replace("{{ORDERS_HTML}}", "\n".join(orows))
    ops = ops.replace("{{GEN_DATE}}", today.isoformat())


    # ================= generic system pages (solar/lights/armor) =================
    sys_pages = {}
    for reg in SYSTEMS_REG:
        k = reg["key"]
        if k in ("audio", "lights", "solar"):
            continue
        page = tmpl("system.tmpl.html")
        page = page.replace("{{PAGE_TITLE}}", f"Hero Armor — {reg['label']}")
        page = page.replace("{{KEY}}", k).replace("{{EMOJI}}", reg["emoji"])
        page = page.replace("{{LABEL}}", esc(reg["label"]))
        page = page.replace("{{STATUS}}", reg["status"])
        page = page.replace("{{STATUS_LABEL}}", COMP_STATUS_LABEL[reg["status"]])
        page = page.replace("{{SUMMARY}}", esc(reg["summary"]))
        # Лінки системи з реєстру. Generic-шаблон їх раніше не виводив узагалі —
        # тепер кожна нова система отримує їх без окремого шаблона.
        sl = "".join(
            f'<a href="{SITE_URL}{href}" style="margin-right:.9rem">{esc(label)}</a>'
            for label, href in reg.get("links", []))
        page = page.replace("{{LINKS}}", f'  <p class="sub" style="margin-top:-1rem">{sl}</p>'
                            if sl else "")

        sections = []
        dia = diagrams_html(k)
        if dia:
            sections.append(dia)
        figs = reg.get("figures", [])
        if figs:
            f_html = "\n".join(
                f'    <div class="fig"><img src="{src_}" alt="{esc(cap)}" loading="lazy"><p>{esc(cap)}</p></div>'
                for src_, cap in figs)
            sections.append(f'  <h2>Креслення</h2>\n  <div class="figs">\n{f_html}\n  </div>')

        pics_html = photos_html(k)
        if pics_html:
            sections.append(pics_html)

        c_decs = [d for d in DECISIONS if d["system"] == k]
        if c_decs:
            d_html = "\n".join(
                f'  <div class="decision">\n    <h3>{esc(d["title"])}</h3>\n'
                f'    <p><span class="why">чому</span> · {d["why"]}</p>\n  </div>'
                for d in c_decs)
            sections.append(f'  <h2>Рішення</h2>\n{d_html}')

        c_tasks = [t for t in TASKS if t["system"] == k]
        if c_tasks:
            t_rows = "\n".join(
                f'      <tr><td><span class="pill {t["status"]}">{task_status(t)}</span></td>'
                f'<td>{esc(t["task"])}</td><td>{esc(t.get("note", ""))}</td></tr>'
                for t in sorted(c_tasks, key=lambda x: {"doing":0,"waiting":1,"todo":2,"done":3}.get(x["status"], 9)))
            sections.append('  <h2>Задачі</h2>\n  <div class="tbl-wrap">\n  <table>\n'
                            '    <thead><tr><th>Статус</th><th>Задача</th><th>Нотатка</th></tr></thead>\n'
                            f'    <tbody>\n{t_rows}\n    </tbody>\n  </table>\n  </div>')

        c_bom = [b for b in BOM if b["system"] == k]
        if c_bom:
            b_rows = []
            for b in c_bom:
                cls, label = pill_of(b)
                item = f'<a href="{b["url"]}">{esc(b["item"])}</a>' if b.get("url") else esc(b["item"])
                b_rows.append(f'      <tr>{bom_thumb(b)}<td>{item}</td><td class="num">{b["qty"]}</td>'
                              f'<td class="num">{b["price"]}</td>'
                              f'<td><span class="pill {cls}">{label}</span></td>'
                              f'<td>{esc(b.get("where", "—"))}</td>'
                              f'<td>{esc(b["note"])}</td></tr>')
            sections.append('  <h2>Закупівля</h2>\n  <div class="tbl-wrap">\n  <table>\n'
                            '    <thead><tr><th></th><th>Позиція</th><th>К-сть</th><th>~Ціна</th><th>Статус</th>'
                            '<th>Де купуємо</th><th>Нотатка</th></tr></thead>\n'
                            f'    <tbody>\n{chr(10).join(b_rows)}\n    </tbody>\n  </table>\n  </div>')

        c_orders = [o for o in ORDERS if o["system"] == k]
        if c_orders:
            o_rows = "\n".join(
                f'      <tr><td class="num">{o["id"]}</td><td class="num">{o["date"]}</td>'
                f'<td>{esc("; ".join(o["items"]))}</td>'
                f'<td><span class="pill {o["status"]}">{ORDER_STATUS[o["status"]]}</span></td>'
                f'<td>{esc(dest_label(o))}</td></tr>'
                for o in c_orders)
            sections.append('  <h2>Замовлення</h2>\n  <div class="tbl-wrap">\n  <table>\n'
                            '    <thead><tr><th>ID</th><th>Дата</th><th>Що</th><th>Статус</th><th>Куди</th></tr></thead>\n'
                            f'    <tbody>\n{o_rows}\n    </tbody>\n  </table>\n  </div>')

        if not sections:
            sections.append('  <div class="empty">Тут поки порожньо. Додай задачі/BOM/рішення з тегом '
                            f'<span style="font-family:var(--mono)">system: "{k}"</span> у data/ — '
                            'і вони зʼявляться тут автоматично.</div>')

        page = page.replace("{{SECTIONS}}", "\n\n".join(sections))
        page = page.replace("{{GEN_DATE}}", today.isoformat())
        sys_pages[reg["page"]] = page

    # ================= tasks page (kanban board) =================
    tasks_page = tmpl("tasks.tmpl.html")
    # Дошка перебудована так, щоб відповідати на питання «що робити зараз» і
    # «хто кого тримає». Раніше 25 задач лежали купою в «чекаємо», і з неї не
    # було видно ні терміновості, ні того, від кого саме чекаємо.
    OWNER = {"ivan": "Іван", "marcel": "Marcel", "volodymyr": "Володимир",
             "liza": "Ліза", "team": "команда"}
    urgent = [t for t in TASKS if t.get("urgent") and t["status"] in ("todo", "doing")]
    mine = [t for t in TASKS if t["status"] in ("todo", "doing")
            and t.get("owner", "ivan") == "ivan" and not t.get("urgent")]
    by_people = {}
    for t in TASKS:
        if t["status"] == "waiting" and t.get("owner", "ivan") != "ivan":
            by_people.setdefault(t["owner"], []).append(t)

    def card(t):
        note = f'<p class="kn">{esc(t["note"])}</p>' if t.get("note") else ""
        return (f'      <div class="kcard" data-comp="{t["system"]}">\n'
                f'        <p class="kt">{esc(t["task"])}</p>\n{("        " + note + chr(10)) if note else ""}'
                f'        <span class="chip {t["system"]}">{SYS_LABEL[t["system"]].lower()}</span>\n'
                f'      </div>')

    focus = []
    if urgent:
        focus.append('    <div class="kcol" data-status="doing">\n'
                     f'      <h3>🔥 Зараз <span class="count">{len(urgent)}</span></h3>\n'
                     + "\n".join(card(t) for t in urgent) + '\n    </div>')
    for who, lst in sorted(by_people.items(), key=lambda x: -len(x[1])):
        focus.append('    <div class="kcol" data-status="waiting">\n'
                     f'      <h3>чекаємо: {OWNER.get(who, who)} '
                     f'<span class="count">{len(lst)}</span></h3>\n'
                     + "\n".join(card(t) for t in lst) + '\n    </div>')
    if mine:
        focus.append('    <div class="kcol" data-status="todo">\n'
                     f'      <h3>черга Івана <span class="count">{len(mine)}</span></h3>\n'
                     + "\n".join(card(t) for t in mine[:8]) + '\n    </div>')
    tasks_page = tasks_page.replace("{{FOCUS_COLUMNS}}", "\n".join(focus))

    kan_status = [("doing", "в роботі"), ("waiting", "чекаємо"),
                  ("todo", "до роботи"), ("done", "готово")]
    comp_order = {c: i for i, c in enumerate(SYSTEMS)}
    cols = []
    for st, st_label in kan_status:
        cards_k = []
        for t in sorted((t for t in TASKS if t["status"] == st),
                        key=lambda x: comp_order.get(x["system"], 9)):
            note = f'<p class="kn">{esc(t["note"])}</p>' if t.get("note") else ""
            done_cls = " done-card" if st == "done" else ""
            cards_k.append(
                f'      <div class="kcard{done_cls}" data-comp="{t["system"]}">\n'
                f'        <p class="kt">{esc(t["task"])}</p>\n{("        " + note + chr(10)) if note else ""}'
                f'        <span class="chip {t["system"]}">{SYS_LABEL[t["system"]].lower()}</span>\n'
                f'      </div>')
        body = "\n".join(cards_k) if cards_k else '      <p class="kempty">порожньо</p>'
        cols.append(
            f'    <div class="kcol" data-status="{st}">\n'
            f'      <h3>{st_label} <span class="count">{len(cards_k)}</span></h3>\n'
            f'{body}\n    </div>')
    tasks_page = tasks_page.replace("{{KANBAN_COLUMNS}}", "\n".join(cols))

    chips = [f'      <button class="fchip active" data-f="all">всі · {len(TASKS)}</button>']
    for k in SYSTEMS:
        n = sum(1 for t in TASKS if t["system"] == k)
        if n:
            chips.append(f'      <button class="fchip" data-f="{k}">'
                         f'{SYS_LABEL[k].lower()} · {n}</button>')
    tasks_page = tasks_page.replace("{{TASK_FILTER_CHIPS}}", "\n".join(chips))
    tasks_page = tasks_page.replace("{{GEN_DATE}}", today.isoformat())

    # ================= index (project dashboard) =================
    index = tmpl("index.tmpl.html")
    ev = PROJ["event"]
    gate = date.fromisoformat(ev["gate_open"])
    burn = date.fromisoformat(ev["burn_night"])
    days_to_gate = gate.toordinal() - today.toordinal()

    open_tasks = sum(1 for t in TASKS if t["status"] != "done")
    doing_n = sum(1 for t in TASKS if t["status"] == "doing")
    done_tasks = len(TASKS) - open_tasks
    in_transit = [o for o in ORDERS if o["status"] in ("ordered", "shipped")]
    # Стан позиції — це flow («приїхало / у кошику / замовити»), а не status:
    # status каже лише, чи позиція взагалі в списку. Рахуємо по flow, з фолбеком
    # на status для рядків, у яких flow ще не проставлений.
    def _st(b):
        f = b.get("flow")
        if f:
            return f
        return "arrived" if b.get("status") == "have" else "to_order"
    have_n = sum(1 for b in BOM if _st(b) in FLOW_HAVE)
    budget_have = sum(usd(b["price"]) for b in BOM if _st(b) in FLOW_HAVE)
    budget_tobuy = sum(usd(b["price"]) for b in BOM if _st(b) in FLOW_TOBUY)
    # де саме ці гроші треба витратити — розбивка по майданчиках
    by_where = {}
    for b in BOM:
        if _st(b) in FLOW_TOBUY:
            w = b.get("where", "—")
            by_where[w] = by_where.get(w, 0) + usd(b["price"])
    where_note = " · ".join(f"{w} ${v:.0f}" for w, v in
                            sorted(by_where.items(), key=lambda x: -x[1]) if v)
    ready_pct = round(100 * (done_tasks + have_n) / (len(TASKS) + len(BOM)))

    def stat(k, v, note, extra="", cls=""):
        return (f'    <div class="stat {cls}"><div class="k">{k}</div>'
                f'<div class="v">{v}</div><div class="note">{note}</div>{extra}</div>')

    index = index.replace("{{STAT_TILES}}", "\n".join([
        stat("до воріт Burning Man",
             f'<span id="countdown" data-gate="{ev["gate_open"]}">{days_to_gate}'
             '<span class="u"> дн</span></span>',
             f'ворота {gate.strftime("%d.%m")} · Man горить {burn.strftime("%d.%m")} · '
             f'{esc(ev["location"])}', cls="hero-stat"),
        stat("готовність", f'{ready_pct}<span class="u">%</span>',
             f'{done_tasks}/{len(TASKS)} задач · {have_n}/{len(BOM)} позицій BOM',
             f'<div class="bar"><i style="--w:{ready_pct}%"></i></div>'),
        stat("задачі", f'{open_tasks}<span class="u"> відкрито</span>',
             f'{doing_n} в роботі · дошка нижче'),
        stat("у дорозі", str(len(in_transit)),
             esc(in_transit[0]["note"]) if in_transit else "нічого не їде"),
        stat("докупити", f'~${budget_tobuy:.0f}',
             esc(where_note) or "кошик лінками в BOM нижче"),
    ]))

    sys_hue = {"audio": "var(--comp-audio)", "solar": "var(--comp-solar)",
                "lights": "var(--comp-lights)", "armor": "var(--comp-armor)",
                "project": "var(--comp-project)", "enclosure": "var(--comp-enclosure)"}
    cards = []
    for c in SYSTEMS_REG:
        k = c["key"]
        c_tasks = [t for t in TASKS if t["system"] == k]
        c_done = sum(1 for t in c_tasks if t["status"] == "done")
        c_bom = [b for b in BOM if b["system"] == k]
        c_have = sum(1 for b in c_bom if b.get("status") == "have")
        tot = len(c_tasks) + len(c_bom)
        pct = round(100 * (c_done + c_have) / tot) if tot else 0
        links = []
        for label, href in c.get("links", []):
            art = {"lab.html": ART_LAB, "ops.html": ART_OPS,
                   "lights_lab.html": LIGHTS_LAB_URL,
                   "solar_lab.html": SOLAR_LAB_URL}.get(href, SITE_URL + href)
            links.append(f'<a href="{art}">{esc(label.split(" (")[0].lower())}</a>')
        meta = []
        if c_tasks:
            meta.append(f"задач: {len(c_tasks) - c_done}")
        if c_bom:
            meta.append(f"купити: {len(c_bom) - c_have}")
        cards.append(
            f'    <div class="card" id="card-{k}" style="--cc:{sys_hue.get(k, 'var(--comp-project)')}">\n'
            f'      <div class="row"><h3><a href="{SITE_URL}{c["page"]}">{c["emoji"]} {esc(c["label"])}</a></h3>'
            f'<span class="pill {c["status"]}">{COMP_STATUS_LABEL[c["status"]]}</span></div>\n'
            f'      <p>{esc(c["summary"])}</p>\n'
            f'      <div class="bar"><i style="--w:{pct}%"></i></div>\n'
            f'      <div class="row"><span class="links"><a href="{SITE_URL}{c["page"]}">сторінка</a>'
            f'{"".join(" · " + s for s in links)}</span>'
            f'<span class="meta">{pct}% · {" · ".join(meta) or "—"}</span></div>\n'
            f'    </div>')
    index = index.replace("{{COMPONENT_CARDS}}", "\n".join(cards))
    # Дві головні схеми на першому екрані: «що де стоїть» і «як розкладено на місці».
    # Іван 01.08: «додай всюди більше картинок про що йде мова».
    index = index.replace("{{INDEX_DIAGRAMS}}", diagrams_html("index", heading="") or "")
    index = index.replace("{{LABS}}", labs_cards_html())

    # task summary strip (full board lives on tasks.html)
    summary = []
    for st, st_label in kan_status:
        n = sum(1 for t in TASKS if t["status"] == st)
        summary.append(f'        <span class="pill {st}">{st_label} · {n}</span>')
    for k in SYSTEMS:
        n = sum(1 for t in TASKS if t["system"] == k and t["status"] != "done")
        if n:
            summary.append(f'        <span class="chip {k}">{SYS_LABEL[k].lower()} · {n}</span>')
    index = index.replace("{{TASK_SUMMARY}}", "\n".join(summary))

    # BOM + budget
    total_b = budget_have + budget_tobuy
    seg_have = round(100 * budget_have / total_b) if total_b else 0
    index = index.replace("{{BUDGET_SEGMENTS}}",
        f'<i class="seg-have" style="--w:{seg_have}%"></i>'
        f'<i class="seg-add" style="--w:{100 - seg_have}%"></i>')
    index = index.replace("{{BUDGET_HAVE}}", f"{budget_have:.0f}")
    index = index.replace("{{BUDGET_TOBUY}}", f"{budget_tobuy:.0f}")
    # фільтри по ланцюгу «замовити → їде → приїхало»
    n_flow = {k: sum(1 for b in BOM if b.get("flow") == k) for k in FLOW_LABEL}
    chips_bom = [f'      <button class="fchip active" data-f="all">всі · {len(BOM)}</button>']
    for k in ("to_order", "in_cart", "ordered", "arrived", "returned", "dropped"):
        if n_flow[k]:
            chips_bom.append(f'      <button class="fchip" data-f="{k}">'
                             f'{FLOW_LABEL[k]} · {n_flow[k]}</button>')
    index = index.replace("{{BOM_FILTER_CHIPS}}", "\n".join(chips_bom))

    # Де що купуємо. Прохання Івана 07.08: одна закупівля живе на кількох
    # майданчиках (Amazon, eBay, Home Depot, Target, RSP Supply), і з таблиці
    # це не видно — потрібен зріз «куди йти і на скільки».
    src = {}
    for b in BOM:
        st = _st(b)
        w = b.get("where", "—")
        d = src.setdefault(w, {"tobuy_n": 0, "tobuy": 0.0, "have_n": 0})
        if st in FLOW_TOBUY:
            d["tobuy_n"] += 1
            d["tobuy"] += usd(b["price"])
        elif st in FLOW_HAVE:
            d["have_n"] += 1
    src_rows = "".join(
        f'<tr><td>{esc(w)}</td><td class="num">{d["tobuy_n"]}</td>'
        f'<td class="num">${d["tobuy"]:.0f}</td><td class="num">{d["have_n"]}</td></tr>'
        for w, d in sorted(src.items(), key=lambda x: (-x[1]["tobuy"], -x[1]["have_n"]))
        if d["tobuy_n"] or d["have_n"])
    index = index.replace("{{BOM_SOURCING}}",
                          '    <div class="tbl-wrap" style="margin:.6rem 0 1rem">\n'
                          '    <table><thead><tr><th>Де купуємо</th><th>Ще купити</th>'
                          '<th>Сума</th><th>Уже взяли</th></tr></thead><tbody>'
                          + src_rows + '</tbody></table></div>')
    index = index.replace("{{BOM_ROWS}}", bom_rows_html())

    # orders
    orows_i = []
    for o in ORDERS:
        days = today.toordinal() - date.fromisoformat(o["date"]).toordinal()
        vendor = f'<a href="{o["url"]}">{esc(o["vendor"])}</a>' if o.get("url") else esc(o["vendor"])
        orows_i.append(
            f'      <tr><td class="num">{o["id"]}</td><td class="num">{o["date"]}</td>'
            f'<td class="num">{days}</td><td>{vendor}</td>'
            f'<td>{esc("; ".join(o["items"]))}</td>'
            f'<td><span class="pill {o["status"]}">{ORDER_STATUS[o["status"]]}</span></td>'
            f'<td>{esc(dest_label(o))}</td></tr>')
    if not orows_i:
        orows_i.append('      <tr><td colspan="7">Поки нічого не замовлено.</td></tr>')
    index = index.replace("{{ORDER_ROWS}}", "\n".join(orows_i))
    index = index.replace("{{GEN_DATE}}", today.isoformat())

    # knowledge graph embedded in index
    kg = build_knowledge()
    kg_json = json.dumps(kg, ensure_ascii=False, indent=1).replace("</", "<\\/")
    index += f'\n<script type="application/ld+json">\n{kg_json}\n</script>\n'

    OUT.mkdir(exist_ok=True)
    # ================= лабораторія ящика =================
    ENC = enc.P
    elab = tmpl("enclosure_lab.tmpl.html")
    e_heat = enc.heat_w()
    e_shade = enc.need_cfm(ENC["ambient"]["playa_shade_c"])
    elab = elab.replace("{{CLEARANCE}}", str(ENC["fit"]["clearance_mm"]))
    elab = elab.replace("{{ENC_TILES}}", "\n".join([
        tile("Тепло в ящику", f"{e_heat:.0f}", "Вт",
             f'зарядка {ENC["thermal"]["charge_w"]} + віддача {ENC["thermal"]["load_w"]} + холостий хід'),
        tile("Межа станції", f'{ENC["ambient"]["station_limit_c"]}', "°C",
             "паспорт усіх станцій — і на розряд, і на заряд", "warn"),
        tile("У тіні на плайї", f'{ENC["ambient"]["playa_shade_c"]}', "°C",
             f'лишається {e_shade["allowed_rise_c"]}°C на перегрів', "crit"),
        tile("Треба потоку", f'{e_shade["cfm"]:.0f}' if e_shade["cfm"] else "—", "CFM",
             e_shade["verdict"], "good" if e_shade["cfm"] else "crit"),
    ]))

    th_rows = []
    for amb in (35, 38, ENC["ambient"]["playa_shade_c"], 45, ENC["ambient"]["playa_sun_c"]):
        r = enc.need_cfm(amb)
        if r["cfm"] is None:
            th_rows.append(
                f'      <tr><td class="num">{amb} °C</td>'
                f'<td class="num" style="color:var(--crit)">{r["allowed_rise_c"]} °C</td>'
                f'<td colspan="3"><span class="pill add">{esc(r["verdict"])}</span></td></tr>')
        else:
            th_rows.append(
                f'      <tr><td class="num">{amb} °C</td>'
                f'<td class="num">{r["allowed_rise_c"]} °C</td>'
                f'<td class="num">{r["cfm"]:.0f} CFM</td>'
                f'<td class="num">{r["inlet_cm2"]:.0f} см²</td>'
                f'<td><span class="pill have">{esc(r["cheapest"] or "—")}</span></td></tr>')
    elab = elab.replace("{{ENC_THERMAL}}", "\n".join(th_rows))

    # Підбір «станція → коробки» рахується в браузері тією самою геометрією,
    # що й enclosure_model.fits(): звіряємо тут на одній парі, щоб розбіжність
    # моделі й сторінки впала на build, а не тихо поїхала.
    _st0, _c0 = ENC["stations"][0], ENC["cases"][0]
    _need = sorted(d + 2 * ENC["fit"]["clearance_mm"] for d in _st0["dims_mm"])
    _have = sorted(_c0["inner_mm"])
    assert enc.fits(_st0, _c0)["fits"] == all(n <= h for n, h in zip(_need, _have)), \
        "геометрія в enclosure_lab розійшлась з enclosure_model.fits()"
    elab = elab.replace("{{ENC_STATIONS_JSON}}", json.dumps(
        [{"name": s["name"], "dims_mm": s["dims_mm"], "kg": s["kg"]}
         for s in ENC["stations"]], ensure_ascii=False))
    elab = elab.replace("{{ENC_CASES_JSON}}", json.dumps(
        [{"name": c["name"], "inner_mm": c["inner_mm"], "seal": c["seal"],
          "price_usd": c["price_usd"], "used": c.get("price_used_usd"),
          "kind": c.get("kind", "кейс"), "verify": bool(c.get("verify")),
          # фото і адреса товару: збирає enclosure/model/case_media.py
          "img": c.get("img", ""), "url": c.get("url", ""),
          # чому фото нема — щоб у таблиці не було німої порожньої клітинки
          "no_photo": c.get("no_photo", ""),
          "note": c.get("note", "")}
         for c in ENC["cases"]], ensure_ascii=False))
    elab = elab.replace("{{FIT_CAPTION}}", esc(ENC["_verify"]))

    for ph, fn in (("{{ENC_SVG_SECTION}}", "schematic"), ("{{ENC_SVG_THERMAL}}", "thermal"),
                   ("{{ENC_SVG_COOLER}}", "cooler")):
        fsvg = (ROOT / "enclosure" / "model" / f"{fn}.svg").read_text()
        fsvg = re.sub(r"<\?xml[^>]*\?>\s*|<!DOCTYPE[^>]*>\s*", "", fsvg)
        elab = elab.replace(ph, fsvg)

    KIND_COLOR = {"особистий досвід": "var(--good)", "офіційне джерело": "var(--signal)"}
    bl = []
    for key, b in ENC["burner_field"].items():
        if key.startswith("_"):
            continue
        col = KIND_COLOR.get(b.get("kind", ""), "var(--warn)")
        head = f'{esc(b["who"])} · <span style="color:{col}">{esc(b.get("kind",""))}</span>'
        body = f'<p>{esc(b["claim"])}</p>'
        if b.get("quote"):
            body += (f'<p style="margin-top:.4rem;font-style:italic;border-left:2px solid var(--line);'
                     f'padding-left:.7rem">«{esc(b["quote"])}»</p>')
        for extra in ("our_math", "caveat", "action", "also", "cost_usd"):
            if b.get(extra):
                lbl = {"our_math": "Наш рахунок", "caveat": "Застереження",
                       "action": "Що робимо", "also": "Там же", "cost_usd": "Ціна"}[extra]
                body += f'<p style="margin-top:.35rem"><b>{lbl}:</b> {esc(str(b[extra]))}</p>'
        if b.get("url"):
            body += f'<p style="margin-top:.35rem"><a href="{esc(b["url"])}">{esc(b["url"])}</a></p>'
        bl.append(f'    <div class="layer" style="border-left-color:{col}">'
                  f'<h3>{head}</h3>{body}</div>')
    elab = elab.replace("{{ENC_BURNERS}}", "\n".join(bl))
    elab = elab.replace("{{ENC_MYTHS}}", "\n".join(
        f'      <tr><td style="white-space:normal;max-width:26ch"><b>{esc(k)}</b></td>'
        f'<td style="white-space:normal;max-width:60ch">{esc(v)}</td></tr>'
        for k, v in ENC["burner_field"]["_myths"].items()))

    parts = []
    for grp in ("cable_entry", "filters"):
        for it in ENC[grp]["items"]:
            parts.append(f'      <tr><td>{esc(it["name"])}</td>'
                         f'<td class="num">{it["qty"]}</td>'
                         f'<td class="num">${it["price_usd"]}</td>'
                         f'<td style="white-space:normal">{esc(it.get("why", ""))}</td></tr>')
    for f in ENC["fans"]:
        parts.append(f'      <tr><td>Вентилятор {esc(f["name"])}</td>'
                     f'<td class="num">1</td><td class="num">${f["price_usd"]}</td>'
                     f'<td>{f["cfm"]} CFM паспорт → {f["cfm"]*ENC["air"]["filter_derate"]:.0f} з фільтром</td></tr>')
    elab = elab.replace("{{ENC_PARTS}}", "\n".join(parts))

    # Блок «що з цього треба купити» на лабораторіях живлення і ящика.
    # Джерело одне — реєстр закупівлі BOM; сторінка показує свій зріз за
    # словами з <підсистема>/data/params.json → buy.match. Правило Івана:
    # усе, що можна купити, стоїть із фото, посиланням на конкретний товар
    # і перевіреною наявністю (06.08.2026 — наявність стала третьою вимогою).
    def _buy_block(cfg, systems):
        if not cfg:
            return ""
        return buy_block_html(systems, cfg.get("match"), cfg.get("note", ""))

    elab = elab.replace("{{BUY_BLOCK}}", _buy_block(ENC.get("buy"), ("enclosure",)))
    slab = slab.replace("{{BUY_BLOCK}}", _buy_block(PP.get("buy"), ("solar",)))

    # ============ лабораторія ядра на спині ============
    # Велика світна лампа на спині робота: модуль адресних діодів усередині
    # корпусу, друковане біле вікно зовні. Сторінка відповідає на три питання —
    # який модуль, який зазор до вікна (щоб не було видно крапок) і що диктувати
    # друкарю. Числа рахує lights/model/back_core.py, руками тут нічого.
    bclab = tmpl("back_core_lab.tmpl.html")
    BC, bwin, bdif, bshell = bcore.D, bcore.WIN, bcore.DIF, bcore.D["shell"]
    bc_fix = next(f for f in LP["fixtures"] if f["id"] == "back_core")
    dc_port_w = cl.C["limits"]["dc_port_w"]
    # Скільки ват лишається ядру на 12-вольтовому виході станції, коли решта
    # світла вже на піку: саме цим числом і міряється «влазимо чи ні».
    bc_budget = dc_port_w - (sum(l_peak.values()) - lm.fixture_peak(bc_fix))
    bmat = {x["verdict"]: x for x in bdif["materials"]}
    bclab = (bclab
             .replace("{{MOD_BUTTONS}}", "".join(
                 f'<button data-key="{m_["key"]}"'
                 + (' class="active"' if m_["key"] == BC["chosen"]["module"] else "")
                 + f'>{esc(m_["name"].split(" (")[0])}</button>'
                 for m_ in bcore.MODS))
             .replace("{{MATERIALS_ROWS}}", "\n".join(
                 f'      <tr><td>{esc(x["name"])}</td>'
                 f'<td class="num">{(str(x["hdt_c"]) + " °C") if x.get("hdt_c") else "—"}</td>'
                 f'<td><span class="pill '
                 + ("have" if x["verdict"] in ("best", "ok") else "add")
                 + f'">{ {"best": "беремо", "ok": "запасний", "alt": "альтернатива", "no": "не можна"}[x["verdict"]] }</span></td>'
                 f'<td style="white-space:normal;max-width:60ch">{esc(x["why"])}</td></tr>'
                 for x in bcore.diffuser_pick()))
             .replace("{{SHELL_NOTE}}", esc(bshell["open"] + " " + bshell["precedent"]))
             .replace("{{FULL_W}}", f'{bcore.module()["diodes"] * bcore.module()["w_diode"]:.0f}')
             .replace("{{SANDWICH}}", f'{bshell["sandwich_mm"]:g}')
             .replace("{{SKIN}}", f'{bshell["skin_mm"]:g}')
             .replace("{{RIBS}}", "–".join(str(x) for x in bshell["ribs_cm"]))
             # Кожному модулю додаємо ГІРШИЙ крок: у набору вкладених кілець він не
             # уздовж кільця (9 мм), а між кільцями (17.2), і саме він вирішує, чи
             # рівний буде КРАЙ вікна. Рахує модель — сторінка не повторює формулу.
             .replace("{{MODS_JSON}}", json.dumps(
                 [dict(m_, pitch_worst_mm=round(bcore.uniformity(m_)["pitch_worst_mm"], 2),
                       ring_gap_mm=round(bcore.ring_gap_mm(m_), 2))
                  for m_ in bcore.MODS], ensure_ascii=False))
             .replace("{{CFG_JSON}}", json.dumps({
                 "chosen": BC["chosen"]["module"],
                 "bus_v": lm.BUS_V,
                 "buck_eff": BC["buck"]["efficiency"],
                 "ctrl_w": bcore.controller()["w_idle"],
                 "night_h": BC["chosen"]["night_h"],
                 "comfort_ratio": bcore.UNI["comfort_ratio"],
                 "min_ratio": bcore.UNI["min_ratio"],
                 "budget_w": round(bc_budget, 1),
                 "night_wh_lights": round(wh_light),
                 "line_mm": bdif["print_spec"]["line_mm"],
                 "layer_mm": bdif["print_spec"]["layer_mm"],
                 "infill_pct": bdif["print_spec"]["infill_pct"],
                 "finish": bdif["print_spec"]["top_bottom"],
                 "sandwich_mm": bshell["sandwich_mm"],
                 "material_best": bmat["best"]["name"],
                 "pla_hdt": bmat["no"]["hdt_c"],
             }, ensure_ascii=False)))

    # Схеми ядра. Кожну малює свій генератор у lights/model/back_core_*.py і кладе
    # .svg поруч; сюди вони приходять інлайном, щоб підписи всередині лишались
    # текстом — інакше їх не перекласти англійською.
    def bc_svg(name):
        f = LIGHTS / "model" / f"back_core_{name}.svg"
        if not f.exists():
            print(f"warn: нема {f.name} — прожени lights/model/back_core_{name}.py")
            return ""
        return re.sub(r"<\?xml[^>]*\?>\s*|<!DOCTYPE[^>]*>\s*", "", f.read_text())

    bc_u = bcore.uniformity()
    bc_mod = bcore.module()
    bc_draw = bcore.draw_from_bus()
    for name in ("face", "section", "wiring", "place", "drawing"):
        bclab = bclab.replace("{{SVG_" + name.upper() + "}}", bc_svg(name))
    # Креслення ще й окремим файлом поруч зі сторінкою: друкарю його показують
    # з телефона, і відкрити одну картинку зручніше, ніж гортати лабораторію.
    bc_dwg = LIGHTS / "model" / "back_core_drawing.svg"
    if bc_dwg.exists():
        (OUT / "back_core_drawing.svg").write_text(bc_dwg.read_text())
    bclab = (bclab
             .replace("{{FACE_CAP}}", esc(
                 f'Модуль {bc_mod["diodes"]} діодів Ø{bc_mod["size_mm"]} мм за вікном '
                 f'Ø{bwin["size_mm"]} мм. Зліва — що всередині, справа — що бачить глядач крізь '
                 f'{bdif["thickness_mm"]} мм білого пластику: крапки зникають, лишається рівне гало.'))
             .replace("{{SECTION_CAP}}", esc(
                 f'Крок між діодами {bc_u["pitch_mm"]:.1f} мм, зазор {bc_u["gap_mm"]:.0f} мм — '
                 f'{bc_u["ratio"]:.2f} кроку, тобто «{bc_u["verdict"]}». {bcore.UNI["why"]}'))
             .replace("{{WIRING_CAP}}", esc(
                 f'З 12 В шини ядро бере {bc_draw["work_w"]:.1f} Вт '
                 f'({bc_draw["work_a"]:.2f} A) і {bc_draw["wh_night"]:.0f} Wh за ніч. '
                 f'Суцільний білий на всі {bc_mod["diodes"]} діодів був би '
                 f'{bc_draw["full_w"]:.0f} Вт — до нього не доходить, бо ліміт '
                 f'{BC["chosen"]["current_limit_a"]} А в прошивці ріже раніше.'))
             .replace("{{PLACE_CAP}}", esc(
                 f'Фігура {bshell["figure_h_m"]:.0f} м заввишки, ядро Ø{bwin["size_mm"]} мм на '
                 f'рівні лопаток. {bshell["open"]}'))
             .replace("{{DRAWING_CAP}}",
                 f'Аркуш для Марселя: дві проєкції, розміри, посадка і примітки. '
                 f'Окремим файлом — <a href="{SITE_URL}back_core_drawing.svg">'
                 f'back_core_drawing.svg</a>, його зручно відкрити з телефона. '
                 + esc('Головне на аркуші не геометрія, а заборона PLA: усе інше '
                       'друкар зробить і так, а матеріал він обирає сам.')))

    # Анімовані превʼю режимів — окремий самодостатній фрагмент із власним CSS і JS.
    fx_file = SITE / "templates" / "_back_core_fx.html"
    bclab = bclab.replace("{{FX_BLOCK}}",
                          fx_file.read_text() if fx_file.exists() else "")

    # Закупівля ядра: фото товару + таблиця з лінками на картки. Позиції тягнемо
    # з BOM за словами back_core.json → buy.match, а не переписуємо руками —
    # реєстр закупівлі один, сторінка показує свій шматок. Правило Івана 01.08:
    # усе, що можна купити, стоїть із фото і посиланням на КОНКРЕТНИЙ товар.
    # Сторінка ядра була першою, де воно не виконувалось (Іван помітив 02.08).
    bc_buy = BC.get("buy", {})
    bc_rows = [b for b in BOM
               if any(mm in b["item"] + b.get("note", "") for mm in bc_buy.get("match", []))]
    if not bc_rows:
        print("warn: закупівля ядра порожня — перевір back_core.json → buy.match")
    bclab = bclab.replace("{{BUY_BLOCK}}",
                          photo_wall_html(bc_rows) + buy_table_html(bc_rows, bc_buy.get("note", "")))

    # План робіт по ядру — етапи і перевірки з lights/data/back_core_install.json.
    inst_file = LIGHTS / "data" / "back_core_install.json"
    INST = json.loads(inst_file.read_text()) if inst_file.exists() else {"stages": [], "checks": []}
    who_label = {"ivan": "Іван", "marcel": "Марсель", "team": "команда",
                 "volodymyr": "Володимир", "liza": "Ліза"}
    bclab = bclab.replace("{{INSTALL_STAGES}}", "\n".join(
        f'      <tr><td class="num">{s["n"]}</td><td>{esc(s["title"])}</td>'
        f'<td>{esc(who_label.get(s.get("who", ""), s.get("who", "—")))}</td>'
        f'<td style="white-space:normal;max-width:46ch">{esc(s["what"])}'
        + (f'<br><span style="color:var(--warn)">ризик: {esc(s["risk"])}</span>'
           if s.get("risk") else "")
        + f'</td><td style="white-space:normal;max-width:34ch">{esc(s["done_when"])}</td></tr>'
        for s in INST["stages"]))
    bclab = bclab.replace("{{INSTALL_CHECKS}}", "\n".join(
        f'    <div class="layer"><h3>{esc(c["title"])}</h3>'
        f'<p>{esc(c["how"])} <b>Навіщо:</b> {esc(c["why"])}</p></div>'
        for c in INST["checks"]))

    # ============ окремі сторінки-калькулятори по типах світла ============
    # Одна сторінка = один тип світильника: покрутити кількість, яскравість,
    # кабель і схему прокладки, не чіпаючи решту системи. Шаблон спільний,
    # різняться тільки дані з lights/data/circuits.json.
    circ_tmpl = tmpl("circuit.tmpl.html")
    all_circ = cl.circuits()
    circ_pages = {}
    for c in all_circ:
        page = circ_tmpl
        nav = "".join(
            f'<a href="{SITE_URL}{o["key"]}.html"'
            + (' class="on"' if o["key"] == c["key"] else "")
            + f'>{esc(o["title"])}</a>'
            for o in all_circ)
        src_rows = []
        for ld in c["loads"]:
            w = ld["a_full"] * c["v"]
            src_rows.append(
                f'      <tr><td>{esc(ld["name"])}</td>'
                f'<td class="num">{ld["a_full"]:.3f} A · {w:.2f} Вт на {esc(c["unit_one"])}</td>'
                f'<td>{esc(ld["source"])}</td>'
                f'<td style="white-space:normal">{esc(ld.get("note", ""))}</td></tr>')
        notes = [
            ("Як рахується просадка",
             "Кожна ділянка кабелю несе струм тих світильників, що живляться через неї, і на "
             "кожній осідає своя частка вольтів. Сторінка складає ці частки по шляху до "
             "найдальшого світильника і додає його власний хвіст. Опір береться туди-назад — "
             "струм іде плюсом і повертається мінусом."),
            ("Чому схема прокладки важливіша за калібр",
             "Між шлейфом в один бік і замкнутим кільцем різниця в рази, а між сусідніми "
             "калібрами — відсотки. Спершу вибирають схему, потім дотягують мідь."),
        ]
        if c["key"] == "spots":
            notes.append(("Рішення по прокладці",
                          sr.SG["_recommended_note"]))
        if c.get("topology_note"):
            notes.append(("Яка схема прокладки в нас насправді", c["topology_note"]))
        if c["key"] == "strip":
            notes.append(("Обережно з цими Вт/м", sb.status()["verdict"]
                          if isinstance(sb.status(), dict) and "verdict" in sb.status()
                          else "Число Вт/м поки не заміряне напряму — це прикидка."))
        # Креслення, місця зʼєднань і закупівля — там, де вони є. Прохання Івана
        # 31.07: на сторінці стрічки бракувало схеми і того, що з неї випливає
        # для закупівлі (заглушки не замовити, поки не заміряний переріз).
        fig, joints, buy = "", "", ""

        def _svg_block(entry, heading):
            """Секція зі схемою: «де стоїть» / «як зʼєднано» — зі своїм підписом."""
            if not entry:
                return ""
            path_, cap = entry
            f = ROOT / path_
            if not f.exists():
                print(f"warn: нема схеми {path_} для цепі {c['key']}")
                return ""
            svg_ = re.sub(r"<\?xml[^>]*\?>\s*|<!DOCTYPE[^>]*>\s*", "", f.read_text())
            return (f'<h2>{esc(heading)}</h2><div class="fig">{svg_}</div>'
                    f'<p class="fig-cap">{esc(cap)}</p>')

        # Кожна сторінка типу світла тепер має однаковий скелет: спершу де воно
        # стоїть, потім як зʼєднано, далі скільки їсть (калькулятор нижче в
        # шаблоні) і що купити. Прохання Івана 07.08: «щоб був порядок».
        fig = (_svg_block(c.get("plan_svg"), "Де воно стоїть")
               + _svg_block(c.get("scheme_svg"), "Як воно зʼєднано"))

        if c["key"] == "strip":
            fig += (f'<p class="fig-cap">{esc(stl.I["flow"])} '
                    f'{esc(stl.I["geometry_note"])} {esc(stl.I["cut_rule"])}</p>'
                    f'<div class="layer block"><h3>Живлення заходить у центрі: '
                    f'{esc(stl.I["feed_point"]["where"])}</h3>'
                    f'<p>{esc(stl.I["feed_point"]["what"])}. '
                    f'{esc(stl.I["feed_point"]["why"])} '
                    f'{esc(stl.I["feed_point"]["direction_note"])}</p></div>')
            joints = ('<h2>Місця зʼєднань</h2><div class="tbl-wrap"><table>'
                      '<thead><tr><th>Де</th><th>Чим</th><th>Стан</th>'
                      '<th>Чому саме так</th></tr></thead><tbody>'
                      + "".join(
                          f'<tr><td>{esc(j["where"])}</td><td>{esc(j["what"])}</td>'
                          f'<td><span class="pill">{esc(j["status"])}</span></td>'
                          f'<td style="white-space:normal;max-width:52ch">{esc(j["why"])}'
                          f'</td></tr>' for j in stl.I["joints"])
                      + '</tbody></table></div>')
            mt = stl.I["measure_task"]
            rows = [b for b in BOM
                    if b.get("system") == "lights"
                    and any(m in b["item"] + b.get("note", "") for m in stl.I["buy_match"])]
            buy = (photo_wall_html(rows)
                   + buy_table_html(rows, stl.I["buy_note"])
                   + f'<div class="layer block"><h3>Спершу замір: {esc(mt["title"])}</h3>'
                     f'<p>{esc(mt["why"])} {esc(mt["how"])} '
                     f'<b>Що це розблокує:</b> {esc(mt["unblocks"])}</p></div>')

        # Для решти цепей закупівля збирається з BOM за списком `buy_match`
        # у circuits.json — щоб на сторінці типу світла було видно і фото
        # товару, і що саме з нього треба купити (прохання Івана 01.08).
        if not buy and c.get("buy_match"):
            rows = [b for b in BOM
                    if b.get("system") in ("lights", "enclosure")
                    and b.get("flow") not in ("dropped", "returned")
                    and any(m in b["item"] + b.get("note", "") for m in c["buy_match"])]
            buy = photo_wall_html(rows) + buy_table_html(rows)

        page = (page
                .replace("{{C_FIGURE}}", fig)
                .replace("{{C_JOINTS}}", joints)
                .replace("{{C_BUY}}", buy)
                .replace("{{C_TITLE}}", esc(c["title"]))
                .replace("{{C_GROUP}}", esc(c["group"]))
                .replace("{{C_SUB}}", esc(c["sub"]))
                .replace("{{C_NAV}}", nav)
                .replace("{{C_DIM_LABEL}}", esc(c["dim_label"]))
                .replace("{{C_SEG_LABEL}}", esc(c["seg_label"]))
                .replace("{{C_SOURCES}}", "\n".join(src_rows))
                .replace("{{C_CAPTION}}", esc(
                    f'Струм одиниці × кількість × рівень яскравості дає струм гілки; далі '
                    f'просадка по обраній схемі. Межі: попередження від '
                    f'{c["limits"]["drop_warn_pct"]}%, критично від '
                    f'{c["limits"]["drop_crit_pct"]}%. Ніч і станція — для прикидки запасу, '
                    f'повний баланс живлення рахується у вузлі живлення.'))
                .replace("{{C_NOTES}}", "\n".join(
                    f'<div class="layer"><h3>{esc(t)}</h3><p>{esc(b)}</p></div>'
                    for t, b in notes))
                .replace("{{C_JSON}}", json.dumps(c, ensure_ascii=False)))
        circ_pages[f'{c["key"]}.html'] = page

    llab = llab.replace("{{CIRCUIT_NAV}}", " · ".join(
        f'<a href="{SITE_URL}{c["key"]}.html">{esc(c["title"])}</a>' for c in all_circ))

    pages = {**circ_pages,
             "index.html": index, "audio.html": audio, "lab.html": lab, "ops.html": ops,
             "tasks.html": tasks_page, "lights.html": lights,
             "schemes.html": schemes, "paint.html": paint, "transport.html": tr,
             "lights_lab.html": llab, "cables.html": cables,
             "solar.html": solar_page,
             "solar_lab.html": slab, "cables_lab.html": clab,
             "enclosure_lab.html": elab, "back_core_lab.html": bclab, **sys_pages}
    # Смужка «Лабораторії» на кожну лабораторну сторінку. Вставляємо тут, а не
    # в кожен шаблон окремо: інакше нова лабораторія знову виявиться загубленою.
    lab_pages = {l["page"]: l["page"] for l in LABS}
    lab_pages.update({c["key"] + ".html": "lights_lab.html" for c in all_circ})
    for name, active in lab_pages.items():
        if name not in pages or "labs-strip" in pages[name]:
            continue
        head, sep, tail = pages[name].partition("</h1>")
        if sep:
            pages[name] = head + sep + "\n" + labs_strip_html(active) + tail

    for name, html in pages.items():
        (OUT / name).write_text(html)
    (OUT / "knowledge.jsonld").write_text(json.dumps(kg, ensure_ascii=False, indent=1))
    leftovers = re.findall(r"\{\{[A-Z_0-9]+\}\}", "".join(pages.values()))
    if leftovers:
        sys.exit(f"unreplaced tokens: {leftovers}")
    print("built dashboard/: " + ", ".join(f"{n} ({len(h)//1024} KB)" for n, h in pages.items()))
    build_okf()
    return OUT


def build_docs(out):
    """GitHub Pages output: artifact/site URLs -> relative links."""
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    # Список сторінок беремо з того, що реально зібралось, а не руками: інакше
    # нова сторінка живе локально, лінк на неї стоїть — а на Pages 404
    # (саме так і сталося зі сторінками по типах світла 31.07).
    names = sorted(p.name for p in out.glob("*.html"))
    swaps = [(ART_MAIN, "index.html"), (ART_LAB, "lab.html"), (ART_OPS, "ops.html"),
             (ART_TASKS, "tasks.html"),
             (LIGHTS_LAB_URL, "lights_lab.html"),
             (SOLAR_LAB_URL, "solar_lab.html"),
             (CABLES_LAB_URL, "cables_lab.html"),
             (ENCLOSURE_LAB_URL, "enclosure_lab.html")]
    swaps += [(SITE_URL + n, n) for n in names]
    swaps += [('href="' + SITE_URL + '"', 'href="index.html"')]
    for name in names:
        html = (out / name).read_text()
        for url, rel in swaps:
            html = html.replace(url, rel)
        (docs / name).write_text(html)
    (docs / "assets").mkdir(exist_ok=True)
    # разом з підтеками: фото товарів лежать в assets/cases/ і без цього
    # рядка на Pages їх просто не було б (сторінка показувала б порожні рамки)
    for a in (SITE / "assets").rglob("*.jpg"):
        dst = docs / "assets" / a.relative_to(SITE / "assets")
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(a.read_bytes())
    # Окремі креслення, на які сторінки дають пряме посилання (їх відкривають з
    # телефона і показують фабрикатору) — без цього на Pages була б 404.
    for s in out.glob("*.svg"):
        (docs / s.name).write_text(s.read_text())
    (docs / "knowledge.jsonld").write_text((out / "knowledge.jsonld").read_text())
    print("wrote docs/ (index, audio, lab, ops, knowledge.jsonld) — Pages-ready")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--copy-to", help="copy artifact mirrors into this directory")
    ap.add_argument("--docs", action="store_true", help="also write docs/ for GitHub Pages")
    args = ap.parse_args()
    if args.docs and PRIVATE:
        sys.exit("refusing --docs with private data loaded: run in CI or move "
                 "data/private/private.json away (docs/ is published publicly)")
    out = build()
    if args.docs:
        build_docs(out)
    if args.copy_to:
        import shutil
        dst = Path(args.copy_to)
        idx = (out / "index.html").read_text()
        hero_b64 = base64.b64encode((SITE / "assets" / "hero.jpg").read_bytes()).decode()
        idx = idx.replace('src="assets/hero.jpg"', f'src="data:image/jpeg;base64,{hero_b64}"')
        (dst / "hero-armor-audio-sim.html").write_text(idx)
        shutil.copy(out / "lab.html", dst / "hero-armor-lab.html")
        shutil.copy(out / "ops.html", dst / "hero-armor-ops.html")
        shutil.copy(out / "tasks.html", dst / "hero-armor-tasks.html")
        print(f"copied artifact mirrors to {dst}")
