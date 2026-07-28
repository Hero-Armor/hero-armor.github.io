#!/usr/bin/env python3
"""
Hero Armor — project-level site builder.

  data/*.json (shared) + <component>/data + <component>/model  ->  docs/ site

Pages: index (project overview: hero image, components, shared BOM, team),
audio (decisions + schematic), lab (interactive simulator), ops (tasks/orders),
plus knowledge.jsonld (schema.org JSON-LD graph of everything).

Adding a component: rows in shared data with its `component` tag + a card in
data/components.json; its own data/ + model/ folder when engineering starts.

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
AUDIO = ROOT / "audio"
sys.path.insert(0, str(AUDIO / "model"))
import audio_node_model as m  # noqa: E402  (reads audio/data/*)

BOM = json.loads((DATA / "bom.json").read_text())
DECISIONS = json.loads((DATA / "decisions.json").read_text())
TASKS = json.loads((DATA / "tasks.json").read_text())
ORDERS = json.loads((DATA / "orders.json").read_text())
ADDR = json.loads((DATA / "addresses.json").read_text())
COMPONENTS_REG = json.loads((DATA / "components.json").read_text())
PROJ = json.loads((DATA / "project.json").read_text())
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

COMPONENTS = ["project", "audio", "solar", "lights", "armor"]
COMP_LABEL = {"project": "Проєкт", "audio": "Аудіо", "solar": "Сонце/живлення",
              "lights": "Світло", "armor": "Броня"}
COMP_STATUS_LABEL = {"design-ready": "дизайн готовий", "in-design": "проєктується",
                     "build": "збірка", "concept": "концепт"}
TASK_STATUS = {"doing": "в роботі", "waiting": "чекаємо", "todo": "до роботи", "done": "готово"}
ORDER_STATUS = {"ordered": "замовлено", "shipped": "їде", "delivered": "доставлено",
                "received": "отримано"}
PILL = {"have": ("have", "у списку"), "add": ("add", "додати"), "tbd": ("tbd", "обрати")}
PILL_OVERRIDES = {"EcoFlow (12V DC-порт)": "є", "Poly-Planar MA-3013, пара": "замовлено",
                  "Herdio HMS60 3\", пара": "замовлено"}
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


def bom_rows_html():
    rows = []
    for b in BOM:
        cls, label = PILL[b["status"]]
        label = PILL_OVERRIDES.get(b["item"], label)
        item = esc(b["item"])
        if b.get("url"):
            item = f'<a href="{b["url"]}">{item}</a>'
        rows.append(
            f'      <tr data-status="{b["status"]}"><td>{item}</td>'
            f'<td><span class="chip {b["component"]}">{b["component"]}</span></td>'
            f'<td class="num">{b["qty"]}</td>'
            f'<td class="num">{b["price"]}</td><td><span class="pill {cls}">{label}</span></td>'
            f'<td>{esc(b["note"])}</td></tr>')
    return "\n".join(rows)


def build_knowledge():
    """Everything in data/ as a schema.org JSON-LD @graph. Public by design:
    city-level addresses only, never tracking numbers."""
    reg = {c["key"]: c for c in COMPONENTS_REG}
    graph = [{
        "@id": "#project", "@type": "Project", "name": "Hero Armor",
        "description": "Memorial art installation for Burning Man 2026 honoring "
                       "Ukrainian defenders, in memory of Zakhar Zakharov — a "
                       "guardian figure that speaks with his voice when someone "
                       "approaches (LD2410C radar → ESP32 → PCM5102A → TPA3116D2).",
        "url": "https://hero-armor.com/",
        "sameAs": [SITE_URL, "https://github.com/Hero-Armor/hero-armor.github.io"],
        "image": "https://hero-armor.com/images/hero-render.jpg",
        "hasPart": [{"@id": f"#sub-{c}"} for c in COMPONENTS if c != "project"],
    }, {
        "@id": "#event", "@type": "Event", "name": PROJ["event"]["name"],
        "startDate": PROJ["event"]["gate_open"], "endDate": PROJ["event"]["end"],
        "location": {"@type": "Place", "name": PROJ["event"]["location"]},
        "workFeatured": {"@id": "#project"},
    }]
    for c in COMPONENTS:
        if c == "project":
            continue
        node = {"@id": f"#sub-{c}", "@type": "Project",
                "name": f"Hero Armor — {COMP_LABEL[c]}",
                "parentOrganization": {"@id": "#project"}}
        if c in reg:
            node["description"] = reg[c]["summary"]
            node["additionalProperty"] = [{"@type": "PropertyValue",
                                           "name": "status", "value": reg[c]["status"]}]
        graph.append(node)

    def comp_ref(c):
        return {"@id": "#project" if c == "project" else f"#sub-{c}"}

    bom_ids = {}
    for b in BOM:
        bid = f"#bom-{slug(b['item'])}"
        bom_ids[b["item"]] = bid
        node = {"@id": bid, "@type": "Product", "name": b["item"],
                "description": b["note"], "isRelatedTo": comp_ref(b["component"]),
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
                "addressLocality": ADDR["locations"][o["deliver_to"]]["label"]}},
            "description": o.get("note", "")})

    for t in TASKS:
        graph.append({
            "@id": f"#task-{slug(t['task'])}", "@type": "Action",
            "name": t["task"], "description": t.get("note", ""),
            "actionStatus": f"https://schema.org/{ACTION_STATUS_LD[t['status']]}",
            "object": comp_ref(t["component"])})

    for d in DECISIONS:
        graph.append({
            "@id": f"#decision-{slug(d['title'])}", "@type": "CreativeWork",
            "genre": "engineering-decision", "name": d["title"],
            "text": re.sub(r"<[^>]+>", "", d["why"]), "about": comp_ref(d["component"])})

    for fname, desc in [("data/project.json", "Project metadata and event dates"),
                        ("data/components.json", "Component registry with status"),
                        ("data/bom.json", "Bill of materials with sourcing status"),
                        ("data/decisions.json", "Engineering decision log"),
                        ("data/tasks.json", "Task board by sub-project"),
                        ("data/orders.json", "Purchase orders and delivery status"),
                        ("audio/data/params.json", "Audio node model constants"),
                        ("audio/data/cases.json", "Playa scenarios for the audio model")]:
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

    comp_slug = {c["key"]: c["key"] for c in COMPONENTS_REG}
    comp_link = {k: f"/components/{k}.md" for k in comp_slug}
    comp_link["project"] = "/project.md"

    def clink(k):
        label = COMP_LABEL.get(k, k)
        return f"[{label}]({comp_link.get(k, '/project.md')})"

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
        (okf / path).write_text("\n".join(parts).rstrip() + "\n")

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

* [Компоненти](/components/index.md) — аудіо, сонце/живлення, світло, броня
* [Рішення](/decisions/index.md) — інженерний лог рішень з «чому»
* [Задачі](/tasks/index.md) — дошка по компонентах
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

    # ---- components ----
    comp_items = []
    for c in COMPONENTS_REG:
        k = c["key"]
        c_dec = [d for d in DECISIONS if d["component"] == k]
        c_tasks = [t for t in TASKS if t["component"] == k]
        c_bom = [b for b in BOM if b["component"] == k]
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
        write(f"components/{k}.md", {
            "type": "Component", "title": c["label"], "description": c["summary"][:160],
            "resource": SITE_URL + c["page"], "tags": [k],
            "component_status": c["status"], "generated": gen,
        }, "\n".join(body))
        comp_items.append(f"[{c['label']}]({k}.md) - {COMP_STATUS_LABEL[c['status']]}")
    index_md("components/index.md", "Компоненти", [("Компоненти", comp_items)])

    # ---- decisions (human-confirmed => verified: human) ----
    dec_items = []
    for d in DECISIONS:
        s = uslug(d["title"])
        write(f"decisions/{s}.md", {
            "type": "Engineering Decision", "title": d["title"],
            "description": re.split(r"(?<=[.!?])\s+", md_text(d["why"]))[0][:200],
            "tags": [d["component"]], "generated": gen,
            "verified": {"by": "human:gumanist", "at": "2026-07-27T00:00:00Z"},
        }, f"Компонент: {clink(d['component'])}\n\n# Чому\n\n{md_text(d['why'])}")
        dec_items.append(f"[{d['title']}]({s}.md)")
    index_md("decisions/index.md", "Інженерні рішення", [("Рішення", dec_items)])

    # ---- tasks ----
    t_items = []
    for t in TASKS:
        s = uslug(t["task"])
        note = t.get("note", "")
        write(f"tasks/{s}.md", {
            "type": "Task", "title": t["task"], "description": note[:160] or None,
            "tags": [t["component"]], "task_status": t["status"], "generated": gen,
        }, f"Статус: **{TASK_STATUS[t['status']]}** · компонент: {clink(t['component'])}"
           + (f"\n\n{note}" if note else ""))
        t_items.append(f"[{t['task']}]({s}.md) - {TASK_STATUS[t['status']]}")
    index_md("tasks/index.md", "Задачі", [("Задачі", t_items)])

    # ---- BOM parts ----
    b_items = []
    for b in BOM:
        s = uslug(b["item"])
        write(f"bom/{s}.md", {
            "type": "Part", "title": b["item"], "description": b["note"][:160],
            "resource": b.get("url"), "tags": [b["component"]],
            "quantity": b["qty"], "price": b["price"],
            "procurement_status": b["status"], "generated": gen,
        }, f"{b['note']}\n\nКомпонент: {clink(b['component'])} · статус: "
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
            "tags": [o["component"]], "order_status": o["status"],
            "order_date": o["date"],
            "deliver_to": ADDR["locations"][o["deliver_to"]]["label"],
            "generated": gen,
        }, f"Статус: **{ORDER_STATUS[o['status']]}** · замовлено {o['date']} · "
           f"доставка: {ADDR['locations'][o['deliver_to']]['label']}\n\n# Позиції\n\n{items_md}"
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

Компонент: [Аудіо](/components/audio.md).

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
            f"[Компоненти](components/index.md) - {len(COMPONENTS_REG)} підсистеми",
            f"[Рішення](decisions/index.md) - {len(DECISIONS)} інженерних рішень з «чому»",
            f"[Задачі](tasks/index.md) - {len(TASKS)} задач, відкрито {open_n}",
            f"[Закупівля](bom/index.md) - {len(BOM)} позицій, докупити {tobuy_n}",
            f"[Замовлення](orders/index.md) - {len(ORDERS)}",
            "[Модель](model/index.md) - розраховані цифри аудіо-вузла",
            "[Обчислення](computations/index.md) - санкціоновані розрахунки"]),
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
    days_lo, days_hi = min(auto["days"].values()), max(auto["days"].values())
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
        tile("Автономність (EcoFlow)", f"{days_lo:.1f}–{days_hi:.1f}", "діб",
             f"{' → '.join(auto['days'])}; стендбай станції ~{P['power_source']['standby_w']} Вт"),
        tile("Сонце в нуль", f"~{auto['solar_w']:.0f}", "Вт",
             f"разом зі стендбаєм EcoFlow (вузол сам — ~{wh_node/(P['solar']['sun_hours']*P['solar']['system_eff']):.0f} Вт)"),
        tile("Tj ампа, найгірший кейс", f"{tj_worst:.0f}", "°C",
             f"межа {P['thermal']['tj_max']:.0f}°C; радіатор {P['thermal']['heatsink_rth']}°C/W назовні", "good"),
        tile("Гучність @3 м", f"{day['spl_peak']:.0f}", "dB пік",
             f"{esc(spk['name'])} {cfg}: ~{day['spl_avg']:.0f} dB сер.; "
             f"{day['margin_avg']:+.0f} дБ вдень, {night['margin_avg']:+.0f} на гучній вечірці"),
        tile("Детекція", f"{sn['range_m']:.1f}", "м", "стабільно вдень/вночі/в бурю", "good"),
    ]
    audio = audio.replace("{{TILES_HTML}}", "\n".join(audio_tiles))

    decs = "\n".join(
        f'    <div class="decision">\n      <h3>{esc(d["title"])}</h3>\n'
        f'      <p><span class="why">чому</span> · {d["why"]}</p>\n    </div>'
        for d in DECISIONS if d["component"] == "audio")
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
        dest = ADDR["locations"][o["deliver_to"]]["label"]
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


    # ================= generic component pages (solar/lights/armor) =================
    comp_pages = {}
    for reg in COMPONENTS_REG:
        k = reg["key"]
        if k == "audio":
            continue
        page = tmpl("component.tmpl.html")
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

        c_decs = [d for d in DECISIONS if d["component"] == k]
        if c_decs:
            d_html = "\n".join(
                f'  <div class="decision">\n    <h3>{esc(d["title"])}</h3>\n'
                f'    <p><span class="why">чому</span> · {d["why"]}</p>\n  </div>'
                for d in c_decs)
            sections.append(f'  <h2>Рішення</h2>\n{d_html}')

        c_tasks = [t for t in TASKS if t["component"] == k]
        if c_tasks:
            t_rows = "\n".join(
                f'      <tr><td><span class="pill {t["status"]}">{TASK_STATUS[t["status"]]}</span></td>'
                f'<td>{esc(t["task"])}</td><td>{esc(t.get("note", ""))}</td></tr>'
                for t in sorted(c_tasks, key=lambda x: {"doing":0,"waiting":1,"todo":2,"done":3}.get(x["status"], 9)))
            sections.append('  <h2>Задачі</h2>\n  <div class="tbl-wrap">\n  <table>\n'
                            '    <thead><tr><th>Статус</th><th>Задача</th><th>Нотатка</th></tr></thead>\n'
                            f'    <tbody>\n{t_rows}\n    </tbody>\n  </table>\n  </div>')

        c_bom = [b for b in BOM if b["component"] == k]
        if c_bom:
            b_rows = []
            for b in c_bom:
                cls, label = PILL[b["status"]]
                label = PILL_OVERRIDES.get(b["item"], label)
                item = f'<a href="{b["url"]}">{esc(b["item"])}</a>' if b.get("url") else esc(b["item"])
                b_rows.append(f'      <tr><td>{item}</td><td class="num">{b["qty"]}</td>'
                              f'<td class="num">{b["price"]}</td>'
                              f'<td><span class="pill {b["status"]}">{label}</span></td>'
                              f'<td>{esc(b["note"])}</td></tr>')
            sections.append('  <h2>Закупівля</h2>\n  <div class="tbl-wrap">\n  <table>\n'
                            '    <thead><tr><th>Позиція</th><th>К-сть</th><th>~Ціна</th><th>Статус</th><th>Нотатка</th></tr></thead>\n'
                            f'    <tbody>\n{chr(10).join(b_rows)}\n    </tbody>\n  </table>\n  </div>')

        c_orders = [o for o in ORDERS if o["component"] == k]
        if c_orders:
            o_rows = "\n".join(
                f'      <tr><td class="num">{o["id"]}</td><td class="num">{o["date"]}</td>'
                f'<td>{esc("; ".join(o["items"]))}</td>'
                f'<td><span class="pill {o["status"]}">{ORDER_STATUS[o["status"]]}</span></td>'
                f'<td>{esc(ADDR["locations"][o["deliver_to"]]["label"])}</td></tr>'
                for o in c_orders)
            sections.append('  <h2>Замовлення</h2>\n  <div class="tbl-wrap">\n  <table>\n'
                            '    <thead><tr><th>ID</th><th>Дата</th><th>Що</th><th>Статус</th><th>Куди</th></tr></thead>\n'
                            f'    <tbody>\n{o_rows}\n    </tbody>\n  </table>\n  </div>')

        if not sections:
            sections.append('  <div class="empty">Тут поки порожньо. Додай задачі/BOM/рішення з тегом '
                            f'<span style="font-family:var(--mono)">component: "{k}"</span> у data/ — '
                            'і вони зʼявляться тут автоматично.</div>')

        page = page.replace("{{SECTIONS}}", "\n\n".join(sections))
        page = page.replace("{{GEN_DATE}}", today.isoformat())
        comp_pages[reg["page"]] = page

    # ================= tasks page (kanban board) =================
    tasks_page = tmpl("tasks.tmpl.html")
    kan_status = [("doing", "в роботі"), ("waiting", "чекаємо"),
                  ("todo", "до роботи"), ("done", "готово")]
    comp_order = {c: i for i, c in enumerate(COMPONENTS)}
    cols = []
    for st, st_label in kan_status:
        cards_k = []
        for t in sorted((t for t in TASKS if t["status"] == st),
                        key=lambda x: comp_order.get(x["component"], 9)):
            note = f'<p class="kn">{esc(t["note"])}</p>' if t.get("note") else ""
            done_cls = " done-card" if st == "done" else ""
            cards_k.append(
                f'      <div class="kcard{done_cls}" data-comp="{t["component"]}">\n'
                f'        <p class="kt">{esc(t["task"])}</p>\n{("        " + note + chr(10)) if note else ""}'
                f'        <span class="chip {t["component"]}">{COMP_LABEL[t["component"]].lower()}</span>\n'
                f'      </div>')
        body = "\n".join(cards_k) if cards_k else '      <p class="kempty">порожньо</p>'
        cols.append(
            f'    <div class="kcol" data-status="{st}">\n'
            f'      <h3>{st_label} <span class="count">{len(cards_k)}</span></h3>\n'
            f'{body}\n    </div>')
    tasks_page = tasks_page.replace("{{KANBAN_COLUMNS}}", "\n".join(cols))

    chips = [f'      <button class="fchip active" data-f="all">всі · {len(TASKS)}</button>']
    for k in COMPONENTS:
        n = sum(1 for t in TASKS if t["component"] == k)
        if n:
            chips.append(f'      <button class="fchip" data-f="{k}">'
                         f'{COMP_LABEL[k].lower()} · {n}</button>')
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

    comp_hue = {"audio": "var(--comp-audio)", "solar": "var(--comp-solar)",
                "lights": "var(--comp-lights)", "armor": "var(--comp-armor)",
                "project": "var(--comp-project)"}
    cards = []
    for c in COMPONENTS_REG:
        k = c["key"]
        c_tasks = [t for t in TASKS if t["component"] == k]
        c_done = sum(1 for t in c_tasks if t["status"] == "done")
        c_bom = [b for b in BOM if b["component"] == k]
        c_have = sum(1 for b in c_bom if b["status"] == "have")
        tot = len(c_tasks) + len(c_bom)
        pct = round(100 * (c_done + c_have) / tot) if tot else 0
        links = []
        for label, href in c.get("links", []):
            art = {"lab.html": ART_LAB, "ops.html": ART_OPS}.get(href, SITE_URL + href)
            links.append(f'<a href="{art}">{esc(label.split(" (")[0].lower())}</a>')
        meta = []
        if c_tasks:
            meta.append(f"задач: {len(c_tasks) - c_done}")
        if c_bom:
            meta.append(f"купити: {len(c_bom) - c_have}")
        cards.append(
            f'    <div class="card" id="card-{k}" style="--cc:{comp_hue[k]}">\n'
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
    for k in COMPONENTS:
        n = sum(1 for t in TASKS if t["component"] == k and t["status"] != "done")
        if n:
            summary.append(f'        <span class="chip {k}">{COMP_LABEL[k].lower()} · {n}</span>')
    index = index.replace("{{TASK_SUMMARY}}", "\n".join(summary))

    # BOM + budget
    total_b = budget_have + budget_tobuy
    seg_have = round(100 * budget_have / total_b) if total_b else 0
    index = index.replace("{{BUDGET_SEGMENTS}}",
        f'<i class="seg-have" style="--w:{seg_have}%"></i>'
        f'<i class="seg-add" style="--w:{100 - seg_have}%"></i>')
    index = index.replace("{{BUDGET_HAVE}}", f"{budget_have:.0f}")
    index = index.replace("{{BUDGET_TOBUY}}", f"{budget_tobuy:.0f}")
    n_add = sum(1 for b in BOM if b["status"] != "have")
    index = index.replace("{{BOM_FILTER_CHIPS}}", "\n".join([
        f'      <button class="fchip active" data-f="all">всі · {len(BOM)}</button>',
        f'      <button class="fchip" data-f="add">купити · {n_add}</button>',
        f'      <button class="fchip" data-f="have">є · {have_n}</button>']))
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
            f'<td>{esc(ADDR["locations"][o["deliver_to"]]["label"])}</td></tr>')
    if not orows_i:
        orows_i.append('      <tr><td colspan="7">Поки нічого не замовлено.</td></tr>')
    index = index.replace("{{ORDER_ROWS}}", "\n".join(orows_i))
    index = index.replace("{{GEN_DATE}}", today.isoformat())

    # knowledge graph embedded in index
    kg = build_knowledge()
    kg_json = json.dumps(kg, ensure_ascii=False, indent=1).replace("</", "<\\/")
    index += f'\n<script type="application/ld+json">\n{kg_json}\n</script>\n'

    OUT.mkdir(exist_ok=True)
    pages = {"index.html": index, "audio.html": audio, "lab.html": lab, "ops.html": ops,
             "tasks.html": tasks_page, **comp_pages}
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
             (SITE_URL + "lights.html", "lights.html"), (SITE_URL + "armor.html", "armor.html"),
             ('href="' + SITE_URL + '"', 'href="index.html"')]
    for name in ("index.html", "audio.html", "lab.html", "ops.html", "tasks.html",
                 "solar.html", "lights.html", "armor.html"):
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
