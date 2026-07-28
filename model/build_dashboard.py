#!/usr/bin/env python3
"""
Build the Hero Armor dashboard pages from data/*.json + model outputs.

  data/params.json, cases.json, bom.json, decisions.json  ->  dashboard/main.html + dashboard/lab.html

Everything numeric on the pages is computed by audio_node_model; BOM and the
decision log are rendered from their JSON files. Edit data, run this, republish.

Usage:  python3 build_dashboard.py [--copy-to DIR] [--docs]
        --copy-to DIR   also copy outputs to DIR (e.g. the artifact publish dir)
        --docs          also write docs/ for GitHub Pages: relative links between
                        pages, private data (tracking/addresses) HARD-excluded
"""

import argparse
import base64
import json
import re
import sys
from pathlib import Path

import audio_node_model as m

ROOT = Path(__file__).resolve().parent.parent
DATA, MODEL, OUT = ROOT / "data", ROOT / "model", ROOT / "dashboard"

BOM = json.loads((DATA / "bom.json").read_text())
DECISIONS = json.loads((DATA / "decisions.json").read_text())
TASKS = json.loads((DATA / "tasks.json").read_text())
ORDERS = json.loads((DATA / "orders.json").read_text())
ADDR = json.loads((DATA / "addresses.json").read_text())
PRIVATE_FILE = DATA / "private" / "private.json"
PRIVATE = json.loads(PRIVATE_FILE.read_text()) if PRIVATE_FILE.exists() else {}
if __import__("os").environ.get("CI"):
    PRIVATE = {}  # CI/Pages builds must never see tracking numbers or addresses

ART_MAIN = "https://claude.ai/code/artifact/b5f9223c-1934-413a-9557-be9204d2572b"
ART_LAB = "https://claude.ai/code/artifact/822f630a-a99b-4f3b-98cf-bef6e216dced"
ART_OPS = "https://claude.ai/code/artifact/5ca1ebd7-1356-4457-8362-812703167859"
P = m.P

COMPONENTS = ["project", "audio", "solar", "lights", "armor"]
COMP_LABEL = {"project": "Проєкт", "audio": "Аудіо", "solar": "Сонце/живлення",
              "lights": "Світло", "armor": "Броня"}
TASK_STATUS = {"doing": "в роботі", "waiting": "чекаємо", "todo": "до роботи", "done": "готово"}
ORDER_STATUS = {"ordered": "замовлено", "shipped": "їде", "delivered": "доставлено",
                "received": "отримано"}

PILL = {"have": ("have", "у списку"), "add": ("add", "додати"), "tbd": ("tbd", "обрати")}
PILL_OVERRIDES = {"EcoFlow (12V DC-порт)": "є", "Poly-Planar MA-3013, пара": "замовлено",
                  "Herdio HMS60 3\", пара": "замовлено"}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build():
    wh_node, results = m.composite_day()
    auto = m.autonomy(wh_node)
    day, night = results["day"], results["night"]
    tj_worst = max(r["t_j_worst"] for r in results.values())
    i_comp = wh_node / m.V / 24
    days_lo, days_hi = min(auto["days"].values()), max(auto["days"].values())
    spk = m.SPK

    # ---------- lab ----------
    lab = (MODEL / "templates" / "lab.tmpl.html").read_text()
    png_b64 = base64.b64encode((MODEL / "signal_chain.png").read_bytes()).decode()
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

    th, sn, c33 = P["thermal"], P["sensor"], P["currents_33v"]
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

    cfg = "моно" if P["speaker"]["config"] == "mono" else "стерео ×2"
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

    # ---------- main ----------
    main = (MODEL / "templates" / "main.tmpl.html").read_text()
    svg = (MODEL / "schematic.svg").read_text()
    svg = re.sub(r"<\?xml[^>]*\?>\s*|<!DOCTYPE[^>]*>\s*", "", svg)
    main = main.replace("{{SCHEMATIC_SVG}}", svg)

    def tile(k, v, u, note, cls=""):
        return (f'    <div class="tile {cls}"><div class="k">{k}</div>'
                f'<div class="v">{v}<span class="u"> {u}</span></div>'
                f'<div class="note">{note}</div></div>')

    tiles = [
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
    main = main.replace("{{TILES_HTML}}", "\n".join(tiles))

    decs = "\n".join(
        f'    <div class="decision">\n      <h3>{esc(d["title"])}</h3>\n'
        f'      <p><span class="why">чому</span> · {d["why"]}</p>\n    </div>'
        for d in DECISIONS)
    main = main.replace("{{DECISIONS_HTML}}", decs)

    bom_rows = []
    for b in BOM:
        cls, label = PILL[b["status"]]
        label = PILL_OVERRIDES.get(b["item"], label)
        item = esc(b["item"])
        if b.get("url"):
            item = f'<a href="{b["url"]}">{item}</a>'
        bom_rows.append(
            f'      <tr><td>{item}</td><td class="num">{b["qty"]}</td>'
            f'<td class="num">{b["price"]}</td><td><span class="pill {cls}">{label}</span></td>'
            f'<td>{esc(b["note"])}</td></tr>')
    main = main.replace("{{BOM_ROWS}}", "\n".join(bom_rows))

    # ---------- ops (tasks + orders + ship-to) ----------
    from datetime import date
    today = date.today()
    ops = (MODEL / "templates" / "ops.tmpl.html").read_text()

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

    OUT.mkdir(exist_ok=True)
    (OUT / "lab.html").write_text(lab)
    (OUT / "main.html").write_text(main)
    (OUT / "ops.html").write_text(ops)
    leftovers = re.findall(r"\{\{[A-Z_]+\}\}", lab + main + ops)
    if leftovers:
        sys.exit(f"unreplaced tokens: {leftovers}")
    print(f"built dashboard/: main ({len(main)//1024} KB), lab ({len(lab)//1024} KB), "
          f"ops ({len(ops)//1024} KB)")
    return OUT


def build_docs(out):
    """GitHub Pages output: relative links, private data excluded by CI guard."""
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    swaps = [(ART_MAIN, "index.html"), (ART_LAB, "lab.html"), (ART_OPS, "ops.html")]
    for src, dst in [("main.html", "index.html"), ("lab.html", "lab.html"),
                     ("ops.html", "ops.html")]:
        html = (out / src).read_text()
        for url, rel in swaps:
            html = html.replace(url, rel)
        (docs / dst).write_text(html)
    print(f"wrote docs/ (index, lab, ops) — Pages-ready")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--copy-to", help="also copy outputs into this directory (artifact publish paths)")
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
        shutil.copy(out / "main.html", dst / "hero-armor-audio-sim.html")
        shutil.copy(out / "lab.html", dst / "hero-armor-lab.html")
        shutil.copy(out / "ops.html", dst / "hero-armor-ops.html")
        print(f"copied to {dst}")
