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
AUDIO, LIGHTS = ROOT / "audio", ROOT / "lights"
sys.path.insert(0, str(AUDIO / "model"))
sys.path.insert(0, str(LIGHTS / "model"))
import audio_node_model as m  # noqa: E402  (reads audio/data/*)
import lights_node_model as lm  # noqa: E402  (reads lights/data/*)

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
LIGHTS_LAB_URL = SITE_URL + "lights_lab.html"

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
                        ("audio/data/cases.json", "Playa scenarios for the audio model"),
                        ("lights/data/params.json", "Lights node model constants: fixtures, "
                                                    "power groups, wiring, battery and solar"),
                        ("lights/data/cases.json", "Playa night scenarios for the lights model")]:
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

    # ================= lights page + lights lab =================
    LP = lm.P
    wh_light, l_res = lm.composite_night()
    l_bal = lm.energy_balance(wh_light)
    l_peak = lm.peak_watts()
    peak_runs = lm.wiring_losses(l_peak)
    l_burn, l_norm, l_eco = l_res["burn"], l_res["normal"], l_res["eco"]
    worst_drop = max(r["drop_pct"] for r in peak_runs)
    ref = LP["spec_reference"]
    photo, sol_l, batt_l = LP["photometry"], LP["solar"], LP["battery"]
    night_h = sum(lm.CASES_DOC["composite_night"].values())

    lights = tmpl("lights.tmpl.html")
    lsvg = (LIGHTS / "model" / "schematic.svg").read_text()
    lsvg = re.sub(r"<\?xml[^>]*\?>\s*|<!DOCTYPE[^>]*>\s*", "", lsvg)
    lights = lights.replace("{{SCHEMATIC_SVG}}", lsvg)

    l_nights = l_bal["nights"]
    lights_tiles = [
        tile("Спожито за ніч", f"{wh_light:.0f}", "Wh",
             f"композитна ніч {night_h:.1f} год: пік, штатно, економ", "good"),
        tile("Добовий баланс", f"{l_bal['balance_wh']:+.0f}", "Wh",
             f"панель {sol_l['panel_w']} Вт дає {l_bal['gen_wh']:.0f} Wh з деративами пилу і жари",
             "good" if l_bal["balance_wh"] >= 0 else "crit"),
        tile("Автономність", f"{min(l_nights.values()):.1f}–{max(l_nights.values()):.1f}", "ночей",
             f"{' → '.join(l_nights)} без сонця взагалі; робоча {batt_l['ah']} Аг"),
        tile("Панель в нуль", f"~{l_bal['solar_need_w']:.0f}", "Вт",
             f"попередні {sol_l['legacy_panel_w']} Вт з сайту дали б {l_bal['legacy_gen_wh'] - wh_light:+.0f} Wh щодоби"),
        tile("Пік системи", f"{sum(l_peak.values()):.0f}", "Вт",
             f"Гр.1 {l_peak['g1']:.0f} · Гр.2 {l_peak['g2']:.0f} · Гр.3А {l_peak['g3a']:.0f}; "
             f"у архітектора {ref['architect_peak_w']} Вт (з аудіоплеєром)"),
        tile("Освітленість фігури", f"{l_burn['lux']:.0f}", "лк",
             f"ціль {photo['target_lux']} лк; у штатному режимі {l_norm['lux']:.0f}, "
             f"в економі {l_eco['lux']:.0f}", "good"),
        tile("Просадка в лініях", f"{worst_drop:.1f}", "%",
             f"межа {LP['wiring']['drop_warn_pct']:.0f}%; тримається завдяки шині 24 В", "good"),
    ]
    lights = lights.replace("{{TILES_HTML}}", "\n".join(lights_tiles))

    l_decs = [d for d in DECISIONS if d["component"] == "lights"]
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
        if f.get("addressable"):
            qty = f'{f["qty"]}× {f["length_m"]} м'
        else:
            qty = str(f["qty"])
        f_rows.append(
            f'      <tr><td class="num">{f["spec"]}</td><td>{esc(f["name"])}</td>'
            f'<td>{esc(f["zone"])}</td><td class="num">{qty}</td>'
            f'<td class="num">{lm.fixture_peak(f):.1f} Вт</td>'
            f'<td><span class="grp {f["group"]}">{esc(grp_label[f["group"]].split(" · ")[0])}</span></td>'
            f'<td>{esc(f.get("model", "—"))}</td></tr>')
    lights = lights.replace("{{FIXTURES_ROWS}}", "\n".join(f_rows))
    lights = lights.replace("{{FIXTURES_CAPTION}}",
        f'Паспортний пік — усе світить на повну, анімація не врахована: '
        f'{sum(l_peak.values()):.0f} Вт проти {ref["architect_peak_w"]} Вт у розрахунку архітектора '
        f'(різниця — аудіоплеєр, який у нас живиться окремо від EcoFlow, і сходи 1 Вт замість 0.48 Вт '
        f'у кресленні). У реальних режимах система бере {l_eco["draw_w"]:.0f}–{l_burn["draw_w"]:.0f} Вт: '
        f'прожектори підсаджені по напрузі, а «біжуча вода» світить біжучим фронтом, '
        f'а не всією довжиною одразу.')

    w_rows = "\n".join(
        f'      <tr><td>{esc(r["label"])}</td><td class="num">AWG {r["awg"]}</td>'
        f'<td class="num">{r["length_m"]:.1f} м</td><td class="num">{r["amps"]:.1f} A</td>'
        f'<td class="num">−{r["v_drop"]:.2f} В ({r["drop_pct"]:.2f}%)</td>'
        f'<td class="num">{r["loss_w"]:.1f} Вт</td></tr>' for r in peak_runs)
    lights = lights.replace("{{WIRING_ROWS}}", w_rows)
    lights = lights.replace("{{WIRING_CAPTION}}",
        f'Опір рахується туди-назад (2 × довжина). Найгірша лінія — {worst_drop:.2f}% при межі '
        f'{LP["wiring"]["drop_warn_pct"]:.0f}%, у міді гріється {sum(r["loss_w"] for r in peak_runs):.1f} Вт. '
        f'{esc(LP["wiring"]["note"])}')

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
        f'TARGET_LUX={photo["target_lux"]};\n'
        f'  const SUNH={sol_l["sun_hours"]}, MPPT={sol_l["mppt_eff"]}, '
        f'DUST={sol_l["dust_derate"]}, HEAT={sol_l["heat_derate"]};\n'
        f'  const BATT_V={batt_l["v_nom"]}, DOD={batt_l["dod"]};')
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
             sun=round(c["sun_factor"] * 100), panel=sol_l["panel_w"], ah=batt_l["ah"],
             emerg=1 if c["dim_g3a"] > 0 else 0)
        for c in lm.CASES_DOC["cases"] if c.get("dashboard")], ensure_ascii=False))
    llab = llab.replace("{{CASE_TABLE_TITLE}}",
        f'Кейси ночі (модель: шина {LP["bus_v"]:.0f} В, панель {sol_l["panel_w"]} Вт, '
        f'АКБ {batt_l["ah"]} Аг, анімація {LP["addressable"]["duty_animation"]*100:.0f}%)')

    l_rows = []
    for c in lm.CASES_DOC["cases"]:
        if not c.get("dashboard"):
            continue
        r = l_res[c["key"]]
        bal = r["balance_wh"]
        bal_s = (f'<td class="num"{" style=\"color:var(--crit)\"" if bal < 0 else ""}>'
                 f'{"+" if bal >= 0 else "−"}{abs(bal):.0f} Wh</td>')
        l_rows.append(
            f'      <tr><td>{esc(r["case"])}</td>'
            f'<td class="num">{r["g1"]:.0f} Вт</td><td class="num">{r["g2"]:.0f} Вт</td>'
            f'<td class="num">{r["g3a"]:.0f} Вт</td><td class="num">{r["draw_w"]:.0f} Вт</td>'
            f'<td class="num">{r["wh_night"]:.0f}</td><td class="num">{r["lux"]:.0f} лк</td>'
            f'<td class="num">{r["gen_wh"]:.0f} Wh</td>{bal_s}</tr>')
    l_rows.append(
        f'      <tr><td><b>Композитна ніч</b></td><td class="num">—</td><td class="num">—</td>'
        f'<td class="num">—</td><td class="num">~{wh_light/night_h:.0f} Вт</td>'
        f'<td class="num"><b>{wh_light:.0f}</b></td><td class="num">—</td>'
        f'<td class="num">{l_bal["gen_wh"]:.0f} Wh</td>'
        f'<td class="num">{l_bal["balance_wh"]:+.0f} Wh</td></tr>')
    llab = llab.replace("{{CASE_ROWS}}", "\n".join(l_rows))
    llab = llab.replace("{{LAB_CAPTION}}",
        f'Композитна ніч ({night_h:.1f} год) — {wh_light:.0f} Wh. Панель {sol_l["panel_w"]} Вт з '
        f'деративами (MPPT {sol_l["mppt_eff"]}, пил {sol_l["dust_derate"]}, жара {sol_l["heat_derate"]}) '
        f'дає {l_bal["gen_wh"]:.0f} Wh за добу — баланс {l_bal["balance_wh"]:+.0f} Wh. '
        f'АКБ {batt_l["ah"]} Аг при DoD {batt_l["dod"]*100:.0f}% тримає '
        f'{l_bal["usable_wh"]/wh_light:.1f} ночі повністю без сонця. '
        f'Найвужче місце — пилова буря: сонце падає до {[c["sun_factor"] for c in lm.CASES_DOC["cases"] if c["key"]=="storm"][0]*100:.0f}%, '
        f'і навіть з вимкненим декором доба йде в мінус '
        f'{l_res["storm"]["balance_wh"]:.0f} Wh. Дві такі доби поспіль — і треба гасити все, крім аварійної лінії.')

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
        if k in ("audio", "lights"):
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
            art = {"lab.html": ART_LAB, "ops.html": ART_OPS,
                   "lights_lab.html": LIGHTS_LAB_URL}.get(href, SITE_URL + href)
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
             "tasks.html": tasks_page, "lights.html": lights,
             "lights_lab.html": llab, **comp_pages}
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
             (ART_TASKS, "tasks.html"),
             (SITE_URL + "audio.html", "audio.html"), (SITE_URL + "tasks.html", "tasks.html"),
             (SITE_URL + "solar.html", "solar.html"),
             (LIGHTS_LAB_URL, "lights_lab.html"),
             (SITE_URL + "lights.html", "lights.html"), (SITE_URL + "armor.html", "armor.html"),
             ('href="' + SITE_URL + '"', 'href="index.html"')]
    for name in ("index.html", "audio.html", "lab.html", "ops.html", "tasks.html",
                 "solar.html", "lights.html", "lights_lab.html", "armor.html"):
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
