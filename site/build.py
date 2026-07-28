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
PRIVATE_FILE = DATA / "private" / "private.json"
PRIVATE = json.loads(PRIVATE_FILE.read_text()) if PRIVATE_FILE.exists() else {}
if __import__("os").environ.get("CI"):
    PRIVATE = {}  # CI/Pages builds must never see tracking numbers or addresses
P = m.P

SITE_URL = "https://hero-armor.github.io/"
ART_MAIN = "https://claude.ai/code/artifact/b5f9223c-1934-413a-9557-be9204d2572b"
ART_LAB = "https://claude.ai/code/artifact/822f630a-a99b-4f3b-98cf-bef6e216dced"
ART_OPS = "https://claude.ai/code/artifact/5ca1ebd7-1356-4457-8362-812703167859"

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


def bom_rows_html():
    rows = []
    for b in BOM:
        cls, label = PILL[b["status"]]
        label = PILL_OVERRIDES.get(b["item"], label)
        item = esc(b["item"])
        if b.get("url"):
            item = f'<a href="{b["url"]}">{item}</a>'
        rows.append(
            f'      <tr><td>{item}</td><td><span class="comp">{b["component"]}</span></td>'
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

    for fname, desc in [("data/components.json", "Component registry with status"),
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

    status_order = {"doing": 0, "waiting": 1, "todo": 2, "done": 3}
    trows = []
    for comp in COMPONENTS:
        group = [t for t in TASKS if t["component"] == comp]
        if not group:
            continue
        open_n = sum(1 for t in group if t["status"] != "done")
        trows.append(f'      <tr><td colspan="4" style="background:var(--panel);'
                     f'font-family:var(--mono);font-size:.72rem;letter-spacing:.1em;'
                     f'text-transform:uppercase;color:var(--accent)">'
                     f'{COMP_LABEL[comp]} — відкрито {open_n}</td></tr>')
        for t in sorted(group, key=lambda x: status_order.get(x["status"], 9)):
            trows.append(
                f'      <tr><td><span class="pill {t["status"]}">{TASK_STATUS[t["status"]]}</span></td>'
                f'<td>{esc(t["task"])}</td><td><span class="comp">{t["component"]}</span></td>'
                f'<td>{esc(t.get("note", ""))}</td></tr>')
    ops = ops.replace("{{TASKS_HTML}}", "\n".join(trows))

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

    # ================= index (project overview) =================
    index = tmpl("index.tmpl.html")
    open_tasks = sum(1 for t in TASKS if t["status"] != "done")
    in_transit = sum(1 for o in ORDERS if o["status"] in ("ordered", "shipped"))
    have = sum(1 for b in BOM if b["status"] == "have")
    index = index.replace("{{PROJECT_TILES}}", "\n".join([
        tile("Компоненти", str(len(COMPONENTS_REG)), "",
             " · ".join(f"{c['emoji']} {COMP_STATUS_LABEL[c['status']]}" for c in COMPONENTS_REG)),
        tile("Задач відкрито", str(open_tasks), "",
             f"з {len(TASKS)}; дошка — в операціях"),
        tile("Замовлень у дорозі", str(in_transit), "",
             "динаміки на A/B тест" if in_transit else "—"),
        tile("Закупівля", f"{have}/{len(BOM)}", "позицій",
             "решта — лінками нижче, одним кошиком"),
    ]))

    cards = []
    for c in COMPONENTS_REG:
        open_n = sum(1 for t in TASKS if t["component"] == c["key"] and t["status"] != "done")
        links = []
        if c.get("page"):
            links.append(f'<a href="{SITE_URL}{c["page"]}">сторінка</a>')
        for label, href in c.get("links", []):
            art = {"lab.html": ART_LAB, "ops.html": ART_OPS}.get(href, SITE_URL + href)
            links.append(f'<a href="{art}">{esc(label.split(" (")[0].lower())}</a>')
        cards.append(
            f'    <div class="card" id="card-{c["key"]}">\n'
            f'      <div class="row"><h3>{c["emoji"]} {esc(c["label"])}</h3>'
            f'<span class="pill {c["status"]}">{COMP_STATUS_LABEL[c["status"]]}</span></div>\n'
            f'      <p>{esc(c["summary"])}</p>\n'
            f'      <div class="row"><span class="links">{" · ".join(links) or "&nbsp;"}</span>'
            f'<span class="open">задач: {open_n}</span></div>\n'
            f'    </div>')
    index = index.replace("{{COMPONENT_CARDS}}", "\n".join(cards))
    index = index.replace("{{BOM_ROWS}}", bom_rows_html())
    index = index.replace("{{GEN_DATE}}", today.isoformat())

    # knowledge graph embedded in index
    kg = build_knowledge()
    kg_json = json.dumps(kg, ensure_ascii=False, indent=1).replace("</", "<\\/")
    index += f'\n<script type="application/ld+json">\n{kg_json}\n</script>\n'

    OUT.mkdir(exist_ok=True)
    pages = {"index.html": index, "audio.html": audio, "lab.html": lab, "ops.html": ops, **comp_pages}
    for name, html in pages.items():
        (OUT / name).write_text(html)
    (OUT / "knowledge.jsonld").write_text(json.dumps(kg, ensure_ascii=False, indent=1))
    leftovers = re.findall(r"\{\{[A-Z_0-9]+\}\}", "".join(pages.values()))
    if leftovers:
        sys.exit(f"unreplaced tokens: {leftovers}")
    print("built dashboard/: " + ", ".join(f"{n} ({len(h)//1024} KB)" for n, h in pages.items()))
    return OUT


def build_docs(out):
    """GitHub Pages output: artifact/site URLs -> relative links."""
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    swaps = [(ART_MAIN, "index.html"), (ART_LAB, "lab.html"), (ART_OPS, "ops.html"),
             (SITE_URL + "audio.html", "audio.html"), (SITE_URL + "solar.html", "solar.html"),
             (SITE_URL + "lights.html", "lights.html"), (SITE_URL + "armor.html", "armor.html"),
             ('href="' + SITE_URL + '"', 'href="index.html"')]
    for name in ("index.html", "audio.html", "lab.html", "ops.html", "solar.html", "lights.html", "armor.html"):
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
        print(f"copied artifact mirrors to {dst}")
