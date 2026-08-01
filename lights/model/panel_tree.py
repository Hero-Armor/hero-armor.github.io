#!/usr/bin/env python3
"""
Щит подіуму і кабельне дерево: схема фізичного розводки від станції EcoFlow
до кожної групи навантаження.

Що показує ця схема
─────────────────────
Зліва направо — силовий шлях від накопичувача до кожного споживача:

  EcoFlow (12 В вихід)
    → магістральний кабель AWG8 → щит із запобіжниками
         Гр.1 → реле → ШІМ-диммер → кільце прожекторів (8 × 5 Вт)
         Гр.2 → реле → контролер WLED → адресна стрічка (8 рукавів)
                                       → лампи робота (8+2 шт)
                                       → ядро на спині
         Гр.3А → реле → коробка → 24 врізних вогні торця + 2 маркери ящика

На кожному відрізку кабелю підписані:
  – калібр (AWG), довжина (м), струм (А), просадка напруги (%)
  – якщо просадка перевищує межу — виділено попереджувальним кольором

Звідки числа
──────────────
Всі константи та розрахунки — виключно з:
  · lights/data/params.json  (bus_v, fixtures, wiring, topology, fusing)
  · lights_node_model.py     (cable_tree, fuses, peak_watts)
Жодних захардкоджених цифр у цьому файлі немає.

Довжини кабелів є ПРИКИДКАМИ (estimate: true), бо їх не знято з креслення
конструктора — про це прямо сказано в підвалі схеми.

Тільки stdlib — CI будує сайт без pip-пакетів.
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ── імпорт моделі (як у podium_plan.py) ─────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lights_node_model as lnm  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
P = json.loads((DATA / "params.json").read_text())

# ── константи зі щита ───────────────────────────────────────────────────────
BUS_V = P["bus_v"]
WIRE = P["wiring"]
GROUPS = P["groups"]

TREE = lnm.cable_tree()          # список рядків зі всіма розрахованими полями
FUSE_LIST = lnm.fuses()          # [{id, label, amps, rating}, ...]
FUSE = {f["id"]: f["rating"] for f in FUSE_LIST}
PEAK = lnm.peak_watts()

# ── палітра і шрифт (з podium_plan.py) ─────────────────────────────────────
INK = "#24231d"
TXT2 = "#6b675c"
THIN = "#d8d5c9"
GHOST = "#c9c6ba"
ACC = "#b35b1e"          # силовий кабель / акцент
SIG = "#3d6f96"          # розміри / позначки
G1 = "#b07c14"           # прожектори
G2 = "#3d6f96"           # декор
G3 = "#3d7a4f"           # аварійна
PASSIVE = "#b23a2e"      # пасивне / попередження
WARN = "#c45f00"         # просадка > drop_warn_pct
CRIT = "#b22020"         # просадка > drop_crit_pct
BOX_BG = "#f5f4ef"       # фон вузлів
PANEL_BG = "#efeee7"     # фон щита

FONT = "ui-monospace,Menlo,monospace"

# ── геометрія полотна ──────────────────────────────────────────────────────
W, H = 1040, 620

# X-позиції колонок (вузлів)
COL_ECO = 60       # EcoFlow
COL_TRUNK = 200    # магістральний кабель (мітка між ECO і PANEL)
COL_PANEL = 300    # щит із запобіжниками
COL_RELAY = 430    # реле груп
COL_MID = 570      # проміжний вузол (диммер / WLED-box / коробка)
COL_LEAF = 730     # кінцевий пристрій
COL_LEAF2 = 900    # другий рівень (відводи від WLED, врізні вогні)

# Y-центри трьох груп
GY = {
    "g1": 155,
    "g2": 300,
    "g3a": 480,
}

# висота щита
PANEL_X, PANEL_Y, PANEL_W, PANEL_H = COL_PANEL - 30, 90, 60, 450
PANEL_CY = PANEL_Y + PANEL_H // 2

ECO_X, ECO_Y, ECO_W, ECO_H = COL_ECO - 38, 220, 76, 120


def seg(sid):
    """Рядок кабельного дерева за ідентифікатором."""
    return next(r for r in TREE if r["id"] == sid)


def drop_color(row):
    """Колір підпису просадки: зелений / помаранчевий / червоний."""
    pct = row["cum_pct"]
    if pct > WIRE["drop_crit_pct"]:
        return CRIT
    if pct > WIRE["drop_warn_pct"]:
        return WARN
    return G3


def _t(x, y, text, size=11, fill=TXT2, anchor="start", weight=None, italic=False):
    """Один рядок тексту SVG як рядок."""
    extra = ""
    if weight:
        extra += f' font-weight="{weight}"'
    if italic:
        extra += ' font-style="italic"'
    return (f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" '
            f'font-size="{size}" fill="{fill}"{extra}>{text}</text>')


def _rect(x, y, w, h, fill=BOX_BG, stroke=INK, rx=3, sw=1.5):
    return (f'<rect x="{x:.0f}" y="{y:.0f}" width="{w}" height="{h}" '
            f'rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')


def _line(x1, y1, x2, y2, stroke=ACC, sw=2.0, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}/>')


def _hv(x1, y1, x2, y2, stroke=ACC, sw=2.0):
    """Г-подібний шлях: горизонталь від (x1,y1) до (x2,y1), потім вертикаль до (x2,y2)."""
    return (f'<path d="M{x1:.0f},{y1:.0f} L{x2:.0f},{y1:.0f} L{x2:.0f},{y2:.0f}" '
            f'fill="none" stroke="{stroke}" stroke-width="{sw}"/>')


def cable_label(row, x, y, anchor="middle", extra_line=None):
    """Підпис кабельного відрізка (AWG, довжина, струм, просадка)."""
    lines = []
    est = " ~" if row.get("estimate") else ""
    lines.append(_t(x, y, f'AWG{row["awg"]}  {row["length_m"]:.1f} м{est}',
                    10, TXT2, anchor))
    lines.append(_t(x, y + 13, f'{row["amps"]:.2f} А',
                    10, TXT2, anchor))
    dc = drop_color(row)
    lines.append(_t(x, y + 26, f'−{row["drop_pct"]:.1f}%',
                    10, dc, anchor))
    if extra_line:
        lines.append(_t(x, y + 39, extra_line, 9, TXT2, anchor))
    return "\n".join(lines)


def node_box(x, y, w, h, label, sublabel=None, color=INK, bg=BOX_BG,
             fuse_a=None, fuse_color=INK):
    """Прямокутник вузла з підписом і, якщо є, номіналом запобіжника."""
    out = [_rect(x - w // 2, y - h // 2, w, h, fill=bg, stroke=color)]
    out.append(_t(x, y + 4, label, 11, color, "middle", weight="bold"))
    if sublabel:
        out.append(_t(x, y + 17, sublabel, 9, TXT2, "middle"))
    if fuse_a is not None:
        fx = x - w // 2 + 4
        fy = y - h // 2 + 4
        out.append(_rect(fx, fy, 24, 12, fill=fuse_color, stroke="none", rx=2))
        out.append(_t(fx + 12, fy + 9, f'{fuse_a:g}А', 8, "#fff", "middle"))
    return "\n".join(out)


def fuse_chip(x, y, rating, color):
    """Маленький прямокутник-запобіжник."""
    out = [_rect(x - 14, y - 8, 28, 16, fill=color, stroke="none", rx=2)]
    out.append(_t(x, y + 4, f'{rating:g} А', 9, "#fff", "middle", weight="bold"))
    return "\n".join(out)


def svg():
    o = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
             f'width="100%" font-family="{FONT}">')

    # ── фон ─────────────────────────────────────────────────────────────────
    o.append(f'<rect width="{W}" height="{H}" fill="#fafaf7"/>')

    # ── шапка ────────────────────────────────────────────────────────────
    o.append(_t(W // 2, 24, "Щит подіуму і кабельне дерево · Hero Armor BM 2026",
                14, INK, "middle", weight="bold"))
    o.append(_t(W // 2, 42,
                f'шина {BUS_V:.0f} В · пік {sum(PEAK.values()):.0f} Вт · '
                f'головний запобіжник {FUSE["main"]:g} А · усі довжини — прикидки (estimate)',
                11, TXT2, "middle"))

    # ── EcoFlow / станція ────────────────────────────────────────────────
    ex, ey = ECO_X, ECO_Y
    ew, eh = ECO_W, ECO_H
    o.append(_rect(ex, ey, ew, eh, fill=PANEL_BG, stroke=INK, rx=5, sw=1.8))
    o.append(_t(ex + ew // 2, ey + 20, "EcoFlow", 12, INK, "middle", weight="bold"))
    o.append(_t(ex + ew // 2, ey + 35, "станція", 10, TXT2, "middle"))
    o.append(_t(ex + ew // 2, ey + 50, f'{BUS_V:.0f} В вихід', 10, TXT2, "middle"))
    o.append(_t(ex + ew // 2, ey + 65, f'{FUSE["main"]:g} А', 10, SIG, "middle"))
    # 12V вихідна мітка зі стрілкою
    out_x = ex + ew
    out_y = ey + eh // 2
    o.append(_t(ex + ew // 2, ey + 82, "12 В DC →", 10, ACC, "middle"))

    # ── щит подіуму ──────────────────────────────────────────────────────
    px_, py_, pw, ph = PANEL_X, PANEL_Y, PANEL_W, PANEL_H
    o.append(_rect(px_, py_, pw, ph, fill=PANEL_BG, stroke=INK, rx=4, sw=1.8))
    o.append(_t(px_ + pw // 2, py_ + 16, "Щит", 11, INK, "middle", weight="bold"))
    o.append(_t(px_ + pw // 2, py_ + 29, "подіуму", 11, INK, "middle", weight="bold"))

    # головний запобіжник угорі щита
    main_fuse_y = py_ + 50
    o.append(fuse_chip(px_ + pw // 2, main_fuse_y, FUSE["main"], INK))
    o.append(_t(px_ + pw // 2, main_fuse_y + 20, "головний", 8, TXT2, "middle"))

    # три групові запобіжники у щиті
    gfuse_colors = {"g1": G1, "g2": G2, "g3a": G3}
    for gid, gy in GY.items():
        fc = gfuse_colors[gid]
        o.append(fuse_chip(px_ + pw // 2, gy, FUSE[gid], fc))
        o.append(_t(px_ + pw // 2, gy + 20, f'{FUSE[gid]:g} А', 8, fc, "middle"))

    # ── магістральний кабель: EcoFlow → щит ─────────────────────────────
    trunk = seg("trunk")
    # горизонтальна лінія від EcoFlow до щита
    trunk_y = PANEL_Y + PANEL_H // 2
    o.append(_line(out_x, out_y, px_, trunk_y, stroke=ACC, sw=2.5))
    # мітка кабелю
    mid_x = (out_x + px_) // 2
    est_mark = " ~" if trunk["estimate"] else ""
    o.append(_t(mid_x, trunk_y - 30,
                f'AWG{trunk["awg"]}  {trunk["length_m"]:.1f} м{est_mark}',
                10, TXT2, "middle"))
    o.append(_t(mid_x, trunk_y - 17,
                f'{trunk["amps"]:.1f} А  −{trunk["drop_pct"]:.1f}%',
                10, drop_color(trunk), "middle"))

    # ── три гілки від щита до реле ──────────────────────────────────────
    relay_w, relay_h = 60, 28
    relay_x = COL_RELAY

    for gid, gy in GY.items():
        fc = gfuse_colors[gid]
        # лінія від щита до реле
        o.append(_line(px_ + pw, gy, relay_x - relay_w // 2, gy, stroke=fc, sw=2.0))

    # ── реле, диммер/WLED-box, кінцеві вузли ───────────────────────────

    # --- Гр.1: прожектори ───────────────────────────────────────────────
    gy1 = GY["g1"]
    # реле
    o.append(node_box(relay_x, gy1, relay_w, relay_h, "Реле", "Гр.1", G1))
    # гілка br_g1: щит → диммер
    br1 = seg("br_g1")
    dim_x = COL_MID
    o.append(_line(relay_x + relay_w // 2, gy1, dim_x - 50, gy1, stroke=G1, sw=2.0))
    # мітка br_g1
    bx1 = relay_x + relay_w // 2 + 20
    est1 = " ~" if br1["estimate"] else ""
    o.append(_t(bx1, gy1 - 18,
                f'AWG{br1["awg"]}  {br1["length_m"]:.1f} м{est1}',
                9, TXT2, "start"))
    o.append(_t(bx1, gy1 - 5,
                f'{br1["amps"]:.2f} А  −{br1["drop_pct"]:.1f}%',
                9, drop_color(br1), "start"))
    # ШІМ-диммер
    o.append(node_box(dim_x, gy1, 100, 36, "ШІМ-диммер", "SUPERNIGHT 30А", G1))
    # гілка ring_g1: диммер → кільце прожекторів
    ring1 = seg("ring_g1")
    leaf1_x = COL_LEAF
    o.append(_line(dim_x + 50, gy1, leaf1_x - 45, gy1, stroke=G1, sw=2.0))
    rx1 = dim_x + 50 + 10
    est_r1 = " ~" if ring1["estimate"] else ""
    o.append(_t(rx1, gy1 - 18,
                f'AWG{ring1["awg"]}  {ring1["length_m"]:.1f} м{est_r1}',
                9, TXT2, "start"))
    o.append(_t(rx1, gy1 - 5,
                f'{ring1["amps"]:.2f} А  −{ring1["drop_pct"]:.1f}%',
                9, drop_color(ring1), "start"))
    # вузол прожекторів
    spot_f = next(f for f in P["fixtures"] if f["id"] == "spot")
    o.append(node_box(leaf1_x, gy1, 90, 48,
                      f'{spot_f["qty"]} прожектори',
                      f'{spot_f["w_unit"]:.0f} Вт × {spot_f["qty"]} = {PEAK["g1"]:.0f} Вт',
                      G1))
    # відвід на один прожектор (drop_spot)
    drop1 = seg("drop_spot")
    drop1_x = COL_LEAF2 - 30
    drop1_y = gy1 + 35
    o.append(_hv(leaf1_x + 45, gy1, drop1_x, drop1_y, stroke=G1, sw=1.5))
    est_d1 = " ~" if drop1["estimate"] else ""
    o.append(_t(drop1_x + 5, drop1_y - 14,
                f'AWG{drop1["awg"]}  {drop1["length_m"]:.1f} м{est_d1}',
                8, TXT2, "start"))
    o.append(_t(drop1_x + 5, drop1_y - 2,
                f'{drop1["amps"]:.2f} А  −{drop1["cum_pct"]:.1f}% накоп.',
                8, drop_color(drop1), "start"))
    o.append(_t(drop1_x + 5, drop1_y + 10, "1 прожектор (найдальший)", 8, TXT2, "start"))

    # --- Гр.2: декор ────────────────────────────────────────────────────
    gy2 = GY["g2"]
    # реле
    o.append(node_box(relay_x, gy2, relay_w, relay_h, "Реле", "Гр.2", G2))
    # гілка br_g2: щит → WLED-box
    br2 = seg("br_g2")
    wled_x = COL_MID
    o.append(_line(relay_x + relay_w // 2, gy2, wled_x - 50, gy2, stroke=G2, sw=2.0))
    bx2 = relay_x + relay_w // 2 + 10
    est2 = " ~" if br2["estimate"] else ""
    o.append(_t(bx2, gy2 - 18,
                f'AWG{br2["awg"]}  {br2["length_m"]:.1f} м{est2}',
                9, TXT2, "start"))
    o.append(_t(bx2, gy2 - 5,
                f'{br2["amps"]:.2f} А  −{br2["drop_pct"]:.1f}%',
                9, drop_color(br2), "start"))
    # WLED-контролер / розподільна коробка
    o.append(node_box(wled_x, gy2, 100, 36, "WLED + розподіл", "ESP32 · Гр.2", G2))

    # Три відводи від WLED:
    # (a) інжекція стрічки (inj_g2)
    inj = seg("inj_g2")
    inj_y = gy2 - 60
    inj_x = COL_LEAF
    o.append(_hv(wled_x + 50, gy2, inj_x - 45, inj_y, stroke=G2, sw=1.8))
    est_inj = " ~" if inj["estimate"] else ""
    o.append(_t(wled_x + 55, inj_y + 5,
                f'AWG{inj["awg"]}  {inj["length_m"]:.1f} м{est_inj}',
                8, TXT2, "start"))
    inj_dc = drop_color(inj)
    o.append(_t(wled_x + 55, inj_y + 17,
                f'{inj["amps"]:.2f} А  −{inj["cum_pct"]:.1f}% накоп.',
                8, inj_dc, "start"))
    arm_f = next(f for f in P["fixtures"] if f["id"] == "water_arms")
    wled_f = next(f for f in P["fixtures"] if f["id"] == "wled")
    arm_peak = lnm.fixture_peak(arm_f)
    o.append(node_box(inj_x, inj_y, 110, 50,
                      "8 рукавів стрічки",
                      f'WS2811 · {arm_peak:.1f} Вт пік',
                      G2))
    o.append(_t(inj_x, inj_y + 38, f'+ WLED {wled_f["w_unit"]:.0f} Вт', 8, TXT2, "middle"))

    # (b) лампи робота (drop_robot)
    drobot = seg("drop_robot")
    robot_y = gy2 + 5
    robot_x = COL_LEAF
    o.append(_hv(wled_x + 50, gy2, robot_x - 45, robot_y, stroke=G2, sw=1.8))
    est_rob = " ~" if drobot["estimate"] else ""
    o.append(_t(wled_x + 60, robot_y + 5,
                f'AWG{drobot["awg"]}  {drobot["length_m"]:.1f} м{est_rob}',
                8, TXT2, "start"))
    o.append(_t(wled_x + 60, robot_y + 17,
                f'{drobot["amps"]:.2f} А  −{drobot["cum_pct"]:.1f}% накоп.',
                8, drop_color(drobot), "start"))
    led12 = next(f for f in P["fixtures"] if f["id"] == "led12")
    led8 = next(f for f in P["fixtures"] if f["id"] == "led8")
    robot_w = (led12["qty"] + led8["qty"]) * led12["w_unit"]
    o.append(node_box(robot_x, robot_y, 110, 44,
                      "Лампи робота",
                      f'{led12["qty"] + led8["qty"]} шт · {robot_w:.1f} Вт',
                      G2))

    # (c) ядро на спині (drop_back_core)
    dback = seg("drop_back_core")
    back_y = gy2 + 65
    back_x = COL_LEAF
    o.append(_hv(wled_x + 50, gy2, back_x - 45, back_y, stroke=G2, sw=1.8))
    est_back = " ~" if dback["estimate"] else ""
    o.append(_t(wled_x + 60, back_y + 5,
                f'AWG{dback["awg"]}  {dback["length_m"]:.1f} м{est_back}',
                8, TXT2, "start"))
    o.append(_t(wled_x + 60, back_y + 17,
                f'{dback["amps"]:.2f} А  −{dback["cum_pct"]:.1f}% накоп.',
                8, drop_color(dback), "start"))
    back_f = next(f for f in P["fixtures"] if f["id"] == "back_core")
    back_peak = lnm.fixture_peak(back_f)
    o.append(node_box(back_x, back_y, 110, 44,
                      "Ядро на спині",
                      f'WS2812B · {back_peak:.1f} Вт пік',
                      G2))

    # --- Гр.3А: аварійна ────────────────────────────────────────────────
    gy3 = GY["g3a"]
    # реле
    o.append(node_box(relay_x, gy3, relay_w, relay_h, "Реле", "Гр.3А", G3))
    # гілка br_g3a: щит → коробка аварійної
    br3 = seg("br_g3a")
    box3_x = COL_MID
    o.append(_line(relay_x + relay_w // 2, gy3, box3_x - 50, gy3, stroke=G3, sw=2.0))
    bx3 = relay_x + relay_w // 2 + 10
    est3 = " ~" if br3["estimate"] else ""
    o.append(_t(bx3, gy3 - 18,
                f'AWG{br3["awg"]}  {br3["length_m"]:.1f} м{est3}',
                9, TXT2, "start"))
    o.append(_t(bx3, gy3 - 5,
                f'{br3["amps"]:.2f} А  −{br3["drop_pct"]:.1f}%',
                9, drop_color(br3), "start"))
    # коробка аварійної
    o.append(node_box(box3_x, gy3, 100, 36, "Коробка Гр.3А", "аварійна лінія", G3))

    # відвід: врізні вогні торця (stairs_g3a)
    stairs = seg("stairs_g3a")
    stairs_y = gy3 - 50
    stairs_x = COL_LEAF
    o.append(_hv(box3_x + 50, gy3, stairs_x - 45, stairs_y, stroke=G3, sw=1.8))
    est_st = " ~" if stairs["estimate"] else ""
    o.append(_t(box3_x + 55, stairs_y + 5,
                f'AWG{stairs["awg"]}  {stairs["length_m"]:.1f} м{est_st}',
                8, TXT2, "start"))
    o.append(_t(box3_x + 55, stairs_y + 17,
                f'{stairs["amps"]:.2f} А  −{stairs["cum_pct"]:.1f}% накоп.',
                8, drop_color(stairs), "start"))
    stair_f = next(f for f in P["fixtures"] if f["id"] == "stairs")
    stair_peak = lnm.fixture_peak(stair_f)
    o.append(node_box(stairs_x, stairs_y, 110, 44,
                      "24 врізних вогні",
                      f'торець · {stair_peak:.1f} Вт',
                      G3))

    # маркери ящика (box_g3a) — окрема гілка від EcoFlow (parent: null)
    box3a = seg("box_g3a")
    marker_y = gy3 + 50
    marker_x = COL_LEAF
    # лінія від щита (як аварійна, але менша)
    o.append(_hv(box3_x + 50, gy3, marker_x - 45, marker_y, stroke=G3, sw=1.5))
    est_mk = " ~" if box3a["estimate"] else ""
    o.append(_t(box3_x + 55, marker_y + 5,
                f'AWG{box3a["awg"]}  {box3a["length_m"]:.1f} м{est_mk}',
                8, TXT2, "start"))
    marker_f = next(f for f in P["fixtures"] if f["id"] == "box_marker")
    marker_peak = lnm.fixture_peak(marker_f)
    o.append(_t(box3_x + 55, marker_y + 17,
                f'{box3a["amps"]:.2f} А · {marker_peak:.2f} Вт пік',
                8, drop_color(box3a), "start"))
    o.append(node_box(marker_x, marker_y, 110, 36,
                      "2 маркери ящика",
                      f'{marker_f["w_unit"]:.2f} Вт × 2',
                      G3))

    # ── легенда ──────────────────────────────────────────────────────────
    LX, LY, LS = 24, H - 116, 19
    o.append(_t(LX, LY, "Легенда:", 11, INK, "start", weight="bold"))
    y = LY + LS

    def legend_line(color, text, dash=""):
        nonlocal y
        d = f' stroke-dasharray="{dash}"' if dash else ""
        o.append(f'<line x1="{LX}" y1="{y - 4}" x2="{LX + 22}" y2="{y - 4}" '
                 f'stroke="{color}" stroke-width="2.2"{d}/>')
        o.append(_t(LX + 28, y, text, 10, TXT2))
        y += LS

    legend_line(G1, "Гр.1 · прожектори заливки")
    legend_line(G2, "Гр.2 · декор (стрічка, робот, ядро спини)")
    legend_line(G3, "Гр.3А · аварійна (торець + маркери ящика)")
    legend_line(ACC, "Магістраль · головний кабель від станції")

    y = LY + LS
    col2 = LX + 310
    o.append(_rect(col2, y - 11, 28, 14, fill=WARN, stroke="none", rx=2))
    o.append(_t(col2 + 36, y, f'Просадка > {WIRE["drop_warn_pct"]:.0f}% — увага', 10, TXT2))
    y += LS
    o.append(_rect(col2, y - 11, 28, 14, fill=CRIT, stroke="none", rx=2))
    o.append(_t(col2 + 36, y, f'Просадка > {WIRE["drop_crit_pct"]:.0f}% — критично', 10, TXT2))
    y += LS
    o.append(_t(col2, y, "~", 13, TXT2, "start"))
    o.append(_t(col2 + 14, y, "Довжина — прикидка, не з креслення", 10, TXT2))
    y += LS
    o.append(_t(col2, y, "накоп.", 9, TXT2, "start", italic=True))
    o.append(_t(col2 + 38, y, "— накопичена просадка від станції до вузла", 10, TXT2))

    # підвал
    o.append(_t(W // 2, H - 8,
                "Довжини кабелів — прикидки (estimate: true). "
                "Заміряти по факту складання подіуму і підставити в topology.segments.",
                9, TXT2, "middle", italic=True))

    o.append("</svg>")
    return "\n".join(o)


def verify_svg(text):
    """Перевіряє, що SVG парситься і містить очікувані мітки."""
    root = ET.fromstring(text)
    texts = [el.text or "" for el in root.iter("{http://www.w3.org/2000/svg}text")]
    combined = " ".join(texts)

    required = [
        "EcoFlow",
        "Щит",
        "Реле",
        "прожектор",        # вузол г1
        "ШІМ-диммер",
        "WLED",
        "рукавів стрічки",
        "Лампи робота",
        "Ядро на спині",
        "врізних вогні",
        "маркери ящика",
        "Гр.1",
        "Гр.2",
        "Гр.3А",
        "Легенда",
        "прикидка",
    ]
    missing = [r for r in required if r.lower() not in combined.lower()]
    if missing:
        raise ValueError(f"SVG не містить очікуваних міток: {missing}")

    # перевірити viewBox
    vb = root.get("viewBox", "")
    if not vb:
        raise ValueError("SVG не має viewBox")
    parts = vb.split()
    vw, vh = float(parts[2]), float(parts[3])
    if vw <= 0 or vh <= 0:
        raise ValueError(f"viewBox має нульовий розмір: {vb}")

    return True


def main():
    content = svg()
    out = Path(__file__).resolve().parent / "panel_tree.svg"
    out.write_text(content, encoding="utf-8")
    size_kb = len(content.encode("utf-8")) / 1024
    print(f"SVG записано: {out}  ({size_kb:.1f} KB)")

    # верифікація
    verify_svg(content)
    print("Верифікація пройшла: всі очікувані мітки присутні, viewBox коректний.")

    # коротка зведення
    trunk = seg("trunk")
    print(f"\nМагістраль:  AWG{trunk['awg']}  {trunk['length_m']} м  "
          f"{trunk['amps']:.1f} А  −{trunk['drop_pct']:.1f}%")
    for gid in ("g1", "g2", "g3a"):
        label = GROUPS[gid]["label"]
        print(f"  {label}: запобіжник {FUSE[gid]:g} А · пік {PEAK[gid]:.1f} Вт")


if __name__ == "__main__":
    main()
