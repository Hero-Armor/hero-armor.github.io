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
COMP_STATUS_LABEL = {"design-ready": "дизайн готовий", "in-design": "проєктується",
                     "build": "збірка", "concept": "концепт"}
TASK_STATUS = {"doing": "в роботі", "waiting": "чекаємо", "todo": "до роботи", "done": "готово"}
ORDER_STATUS = {"ordered": "замовлено", "shipped": "їде", "delivered": "доставлено",
                "received": "отримано"}
PILL = {"have": ("have", "у списку"), "add": ("add", "додати"), "tbd": ("tbd", "обрати")}
# Ланцюг статусів Івана: замовити -> їде -> приїхало. Виводиться з даних
# (bom.status + активні замовлення), руками ніде не дублюється.
FLOW = {"to_order": ("add", "замовити"), "ordered": ("tbd", "їде"),
        "arrived": ("have", "приїхало")}
FLOW_LABEL = {"to_order": "Замовити", "ordered": "Їде", "arrived": "Приїхало"}
ORDER_STATUS_LD = {"ordered": "OrderProcessing", "shipped": "OrderInTransit",
                   "delivered": "OrderDelivered", "received": "OrderDelivered"}
ACTION_STATUS_LD = {"todo": "PotentialActionStatus", "doing": "ActiveActionStatus",
                    "waiting": "PotentialActionStatus", "done": "CompletedActionStatus"}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")[:60]


def tmpl(name):
    return (SITE / "templates" / name).read_text()


def usd(price_str):
    """First $-amount in a BOM price string ('$17/3шт' -> 17.0), 0 if none."""
    mm = re.search(r"\$(\d+(?:\.\d+)?)", price_str or "")
    return float(mm.group(1)) if mm else 0.0


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


def dest_label(o):
    """Куди їде замовлення. Адреса може бути ще не з'ясована (щойно замовили і
    не подивились у підтвердженні) — тоді кажемо про це прямо, а не падаємо."""
    return ADDR["locations"].get(o.get("deliver_to"), {}).get("label", "адресу уточнити")


def bom_rows_html():
    rows = []
    for b in BOM:
        cls, label = FLOW.get(b.get("flow"), PILL[b["status"]])
        item = esc(b["item"])
        if b.get("url"):
            item = f'<a href="{b["url"]}">{item}</a>'
        rows.append(
            f'      <tr data-status="{b.get("flow", b["status"])}"><td>{item}</td>'
            f'<td><span class="chip {b["system"]}">{b["system"]}</span></td>'
            f'<td class="num">{b["qty"]}</td>'
            f'<td class="num">{b["price"]}</td><td><span class="pill {cls}">{label}</span></td>'
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
                    {"@type": "PropertyValue", "name": "procurement-status", "value": b["status"]},
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
            body += [f"* [{t['task']}](/tasks/{uslug(t['task'])}.md) — {TASK_STATUS[t['status']]}"
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
        }, f"Статус: **{TASK_STATUS[t['status']]}** · система: {clink(t['system'])}"
           + (f"\n\n{note}" if note else ""))
        t_items.append(f"[{t['task']}]({s}.md) - {TASK_STATUS[t['status']]}")
    index_md("tasks/index.md", "Задачі", [("Задачі", t_items)])

    # ---- BOM parts ----
    b_items = []
    for b in BOM:
        s = uslug(b["item"])
        write(f"bom/{s}.md", {
            "type": "Part", "title": b["item"], "description": b["note"][:160],
            "resource": b.get("url"), "tags": [b["system"]],
            "quantity": b["qty"], "price": b["price"],
            "procurement_status": b["status"], "generated": gen,
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
        log_lines += [f"* **{e['kind']}**: {e['text']}" for e in log_by_date[d_key]]
        log_lines.append("")
    (okf / "log.md").write_text("\n".join(log_lines).rstrip() + "\n")

    open_n = sum(1 for t in TASKS if t["status"] != "done")
    tobuy_n = sum(1 for b in BOM if b["status"] != "have")
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
    audio = audio.replace("{{FIGURES}}", figures_html("audio"))
    audio = audio.replace("{{TILES_HTML}}", "\n".join(audio_tiles))

    decs = "\n".join(
        f'    <div class="decision">\n      <h3>{esc(d["title"])}</h3>\n'
        f'      <p><span class="why">чому</span> · {d["why"]}</p>\n    </div>'
        for d in DECISIONS if d["system"] == "audio")
    audio = audio.replace("{{DECISIONS_HTML}}", decs)

    # ================= lab page =================
    lab = tmpl("lab.tmpl.html")
    png_b64 = base64.b64encode((AUDIO / "model" / "signal_chain.png").read_bytes()).decode()
    lab = lab.replace("{{SIGNAL_PNG}}", "data:image/png;base64," + png_b64)

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
    lsvg = (LIGHTS / "model" / "schematic.svg").read_text()
    lsvg = re.sub(r"<\?xml[^>]*\?>\s*|<!DOCTYPE[^>]*>\s*", "", lsvg)
    lights = lights.replace("{{SCHEMATIC_SVG}}", lsvg)

    lights_tiles = [
        tile("Спожито за ніч", f"{wh_light:.0f}", "Wh",
             f"композитна ніч {night_h:.1f} год: пік, штатно, економ", "good"),
        tile("Найбільший їдок", f"{by_grp['g2']:.0f}", "Wh",
             f"декор — {100*by_grp['g2']/wh_light:.0f}% ночі; аварійна {by_grp['g3a']:.0f}, "
             f"прожектори лише {by_grp['g1']:.0f}"),
        tile("Аварійна лінія", f"{l_res['emergency']['g3a']:.0f}", "Вт",
             f"не регулюється зовсім — {by_grp['g3a']:.0f} Wh за ніч, "
             f"з них половина це 24 лампи сходів"),
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
    lights = lights.replace("{{FIGURES}}", figures_html("lights"))
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
        qty = f'{f["qty"]}× {f["length_m"]} м' if f.get("addressable") else str(f["qty"])
        f_rows.append(
            f'      <tr><td class="num">{f["spec"]}</td><td>{esc(f["name"])}</td>'
            f'<td>{esc(f["zone"])}</td><td class="num">{qty}</td>'
            f'<td class="num">{lm.fixture_peak(f):.1f} Вт</td>'
            f'<td><span class="grp {f["group"]}">{esc(grp_label[f["group"]].split(" · ")[0])}</span></td>'
            f'<td>{esc(f.get("model", "—"))}</td></tr>')
    lights = lights.replace("{{FIXTURES_ROWS}}", "\n".join(f_rows))
    lights = lights.replace("{{FIXTURES_CAPTION}}",
        f'Паспортний пік — усе на повну, анімація не врахована: {sum(l_peak.values()):.0f} Вт '
        f'проти {ref["architect_peak_w"]} Вт у розрахунку архітектора (у його Гр.2 сидів ще аудіоплеєр, '
        f'а сходи в кресленні були 0.48 Вт замість наших 1 Вт). У реальних режимах система бере '
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
        | {k: f[k] for k in ("w_unit", "length_m", "w_per_m", "addressable") if k in f}
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
        + (f'На піку вилітає лише {len(bad_pk)} ділянка — лінія стрічки. Але «пік» тут означає '
           f'усю стрічку білим на повну довжину, чого в анімації «біжуча вода» не буває: '
           f'простіше поставити ліміт струму в WLED, ніж тягнути мідь під режим, який не увімкнеться.'
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
                 and any(w in b["item"] for w in ("Щит", "Запобіжники", "Фотореле", "Реле",
                                                  "Гермокоробка", "Гермокоробки", "Гермороз",
                                                  "Гель-конектори", "Гофра"))]
    k_rows = "\n".join(
        f'      <tr><td>{esc(b["item"])}</td><td class="num">{esc(b["qty"])}</td>'
        f'<td><span class="pill {b["status"]}">{PILL[b["status"]][1]}</span></td>'
        f'<td>{esc(b["note"])}</td></tr>' for b in kit_items)
    cables = cables.replace("{{KIT_ROWS}}", k_rows)
    cables = cables.replace("{{KIT_CAPTION}}",
        "Кабель на кожну ділянку дерева заведено в закупівлю окремими рядками — шукай їх у "
        "загальному списку на головній за префіксом «Кабель:». Головне правило по коробках: "
        "вентиляція важливіша за герметичність. Глухо закритий бокс на сонці плайї перегріється "
        "швидше, ніж у нього набʼється пил.")

    cab_decs = [d for d in DECISIONS if d["system"] == "lights"]
    cables = cables.replace("{{DECISIONS_HTML}}", "\n".join(
        f'    <div class="decision">\n      <h3>{esc(d["title"])}</h3>\n'
        f'      <p><span class="why">чому</span> · {d["why"]}</p>\n    </div>'
        for d in cab_decs if not d.get("open")))
    cables = cables.replace("{{FLAGS_HTML}}", "\n".join(
        f'  <div class="flag">\n    <h3>{esc(d["title"])}</h3>\n'
        f'    <p><span class="why">відкрите</span> · {d["why"]}</p>\n  </div>'
        for d in cab_decs if d.get("open")))

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
    solar_page = solar_page.replace("{{FIGURES}}", figures_html("solar"))
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
    pk = max(r["draw_w"] for r in l_res_for_lab.values()) + p_demand["audio"]
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

        sections = []
        figs = reg.get("figures", [])
        if figs:
            f_html = "\n".join(
                f'    <div class="fig"><img src="{src_}" alt="{esc(cap)}" loading="lazy"><p>{esc(cap)}</p></div>'
                for src_, cap in figs)
            sections.append(f'  <h2>Креслення</h2>\n  <div class="figs">\n{f_html}\n  </div>')

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
                f'      <tr><td><span class="pill {t["status"]}">{TASK_STATUS[t["status"]]}</span></td>'
                f'<td>{esc(t["task"])}</td><td>{esc(t.get("note", ""))}</td></tr>'
                for t in sorted(c_tasks, key=lambda x: {"doing":0,"waiting":1,"todo":2,"done":3}.get(x["status"], 9)))
            sections.append('  <h2>Задачі</h2>\n  <div class="tbl-wrap">\n  <table>\n'
                            '    <thead><tr><th>Статус</th><th>Задача</th><th>Нотатка</th></tr></thead>\n'
                            f'    <tbody>\n{t_rows}\n    </tbody>\n  </table>\n  </div>')

        c_bom = [b for b in BOM if b["system"] == k]
        if c_bom:
            b_rows = []
            for b in c_bom:
                cls, label = FLOW.get(b.get("flow"), PILL[b["status"]])
                item = f'<a href="{b["url"]}">{esc(b["item"])}</a>' if b.get("url") else esc(b["item"])
                b_rows.append(f'      <tr><td>{item}</td><td class="num">{b["qty"]}</td>'
                              f'<td class="num">{b["price"]}</td>'
                              f'<td><span class="pill {cls}">{label}</span></td>'
                              f'<td>{esc(b["note"])}</td></tr>')
            sections.append('  <h2>Закупівля</h2>\n  <div class="tbl-wrap">\n  <table>\n'
                            '    <thead><tr><th>Позиція</th><th>К-сть</th><th>~Ціна</th><th>Статус</th><th>Нотатка</th></tr></thead>\n'
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
    have_n = sum(1 for b in BOM if b["status"] == "have")
    budget_have = sum(usd(b["price"]) for b in BOM if b["status"] == "have")
    budget_tobuy = sum(usd(b["price"]) for b in BOM if b["status"] != "have")
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
             "кошик лінками в BOM нижче"),
    ]))

    sys_hue = {"audio": "var(--comp-audio)", "solar": "var(--comp-solar)",
                "lights": "var(--comp-lights)", "armor": "var(--comp-armor)",
                "project": "var(--comp-project)"}
    cards = []
    for c in SYSTEMS_REG:
        k = c["key"]
        c_tasks = [t for t in TASKS if t["system"] == k]
        c_done = sum(1 for t in c_tasks if t["status"] == "done")
        c_bom = [b for b in BOM if b["system"] == k]
        c_have = sum(1 for b in c_bom if b["status"] == "have")
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
            f'    <div class="card" id="card-{k}" style="--cc:{sys_hue[k]}">\n'
            f'      <div class="row"><h3><a href="{SITE_URL}{c["page"]}">{c["emoji"]} {esc(c["label"])}</a></h3>'
            f'<span class="pill {c["status"]}">{COMP_STATUS_LABEL[c["status"]]}</span></div>\n'
            f'      <p>{esc(c["summary"])}</p>\n'
            f'      <div class="bar"><i style="--w:{pct}%"></i></div>\n'
            f'      <div class="row"><span class="links"><a href="{SITE_URL}{c["page"]}">сторінка</a>'
            f'{"".join(" · " + s for s in links)}</span>'
            f'<span class="meta">{pct}% · {" · ".join(meta) or "—"}</span></div>\n'
            f'    </div>')
    index = index.replace("{{COMPONENT_CARDS}}", "\n".join(cards))

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
    n_flow = {k: sum(1 for b in BOM if b.get("flow") == k)
              for k in ("to_order", "ordered", "arrived")}
    chips_bom = [f'      <button class="fchip active" data-f="all">всі · {len(BOM)}</button>']
    for k in ("to_order", "ordered", "arrived"):
        if n_flow[k]:
            chips_bom.append(f'      <button class="fchip" data-f="{k}">'
                             f'{FLOW_LABEL[k]} · {n_flow[k]}</button>')
    index = index.replace("{{BOM_FILTER_CHIPS}}", "\n".join(chips_bom))
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

    cases = ENC["cases"]
    elab = elab.replace("{{CASE_HEADS}}", "".join(
        f'<th>{esc(c["name"])}<br><span style="font-weight:400;text-transform:none">'
        f'${c["price_usd"]} · {esc(c["seal"])}</span></th>' for c in cases))
    fit_rows = []
    for st in ENC["stations"]:
        cells = []
        for c in cases:
            g = enc.fits(st, c)
            if not g["fits"]:
                cells.append('<td><span class="pill add">ні</span></td>')
            elif g["tight"]:
                cells.append('<td><span class="pill tbd">впритул</span></td>')
            else:
                cells.append(f'<td><span class="pill have">так</span>'
                             f'<br><span style="font-size:.7rem;color:var(--ink-2)">'
                             f'запас {min(g["slack_mm"])} мм</span></td>')
        d = "×".join(str(x) for x in st["dims_mm"])
        fit_rows.append(f'      <tr><td><b>{esc(st["name"])}</b></td>'
                        f'<td class="num">{d}</td><td class="num">{st["kg"]} кг</td>'
                        + "".join(cells) + '</tr>')
    elab = elab.replace("{{ENC_FIT}}", "\n".join(fit_rows))
    elab = elab.replace("{{FIT_CAPTION}}", esc(ENC["_verify"]))

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

    pages = {"index.html": index, "audio.html": audio, "lab.html": lab, "ops.html": ops,
             "tasks.html": tasks_page, "lights.html": lights,
             "lights_lab.html": llab, "cables.html": cables,
             "solar.html": solar_page,
             "solar_lab.html": slab, "cables_lab.html": clab,
             "enclosure_lab.html": elab, **sys_pages}
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
    swaps = [(ART_MAIN, "index.html"), (ART_LAB, "lab.html"), (ART_OPS, "ops.html"),
             (ART_TASKS, "tasks.html"),
             (SITE_URL + "audio.html", "audio.html"), (SITE_URL + "tasks.html", "tasks.html"),
             (SITE_URL + "solar.html", "solar.html"),
             (LIGHTS_LAB_URL, "lights_lab.html"),
             (SITE_URL + "cables.html", "cables.html"),
             (SOLAR_LAB_URL, "solar_lab.html"),
             (CABLES_LAB_URL, "cables_lab.html"),
             (ENCLOSURE_LAB_URL, "enclosure_lab.html"),
             (SITE_URL + "audio.html", "audio.html"),
             (SITE_URL + "lights.html", "lights.html"), (SITE_URL + "armor.html", "armor.html"),
             ('href="' + SITE_URL + '"', 'href="index.html"')]
    for name in ("index.html", "audio.html", "lab.html", "ops.html", "tasks.html",
                 "solar.html", "solar_lab.html", "enclosure_lab.html",
                 "lights.html", "lights_lab.html", "cables.html", "cables_lab.html",
                 "armor.html"):
        html = (out / name).read_text()
        for url, rel in swaps:
            html = html.replace(url, rel)
        (docs / name).write_text(html)
    (docs / "assets").mkdir(exist_ok=True)
    for a in (SITE / "assets").glob("*.jpg"):
        (docs / "assets" / a.name).write_bytes(a.read_bytes())
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
