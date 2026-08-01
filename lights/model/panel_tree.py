#!/usr/bin/env python3
"""
Щит подіуму і дерево кабелів.

Схема ліво-право: станція EcoFlow → магістраль → щит із запобіжниками → три
групові гілки. На кожному відрізку підписано AWG, довжину, струм і просадку
у відсотках. Де estimate:true — підпис «(прикидка)», бо числа ще не з
креслення. Відрізки із просадкою вище норми (drop_warn_pct) підсвічені
помаранчевим, вище критичної (drop_crit_pct) — червоним.

Числа з моделі: lights_node_model.cable_tree() і fuses(). Нових числових
констант не додаємо.  Тільки stdlib; SVG пишеться текстом.
"""

import json
import sys
from pathlib import Path

# щоб можна було запускати звідусіль
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lights_node_model as lnm  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
P = json.loads((DATA / "params.json").read_text())
META = json.loads((DATA / "panel_tree.json").read_text())

TREE = lnm.cable_tree()
SEG = {r["id"]: r for r in TREE}
FUSE_LIST = lnm.fuses()
FUSE = {f["id"]: f["rating"] for f in FUSE_LIST}
FUSE_A = {f["id"]: f["amps"] for f in FUSE_LIST}
WIRE = P["wiring"]
GROUPS = P["groups"]
WARN_PCT = WIRE["drop_warn_pct"]
CRIT_PCT = WIRE["drop_crit_pct"]
BUS_V = P["bus_v"]

# ── Палітра (з podium_plan.py) ────────────────────────────────────────────────
INK   = "#24231d"
TXT2  = "#6b675c"
THIN  = "#d8d5c9"
GHOST = "#c9c6ba"
ACC   = "#b35b1e"   # магістраль / силова траса
G1    = "#b07c14"   # прожектори
G2    = "#3d6f96"   # декор
G3    = "#3d7a4f"   # аварійна
WARN  = "#c47a1a"   # просадка: попередження
CRIT  = "#b02020"   # просадка: критична
OK    = "#3d7a4f"   # просадка: норма
BGBOX = "#f7f5f0"   # фон прямокутників вузлів

# ── Полотно ───────────────────────────────────────────────────────────────────
W, H = 1000, 680

# Горизонтальні X-позиції колонок
X_STATION = 60      # ліво: станція
X_TRUNK   = 200     # щит
X_PANEL   = 380     # щит-блок (ширина 90)
X_BR      = 560     # виходи груп (після щита)
X_LOAD    = 810     # навантаження (кінцеві вузли)

PANEL_W, PANEL_H = 90, 170
PANEL_X = 370
PANEL_Y = 250

# Y центри трьох груп
Y_G1  = 160
Y_G2  = 340
Y_G3  = 530

# Станція
STAT_X, STAT_Y = 36, 300
STAT_W, STAT_H = 90, 100

GRP_COLOR = {"g1": G1, "g2": G2, "g3a": G3}


# ── Утиліти ───────────────────────────────────────────────────────────────────

def _drop_color(pct, cum_pct=None):
    """Колір лінії залежно від просадки."""
    p = cum_pct if cum_pct is not None else pct
    if p > CRIT_PCT:
        return CRIT
    if p > WARN_PCT:
        return WARN
    return INK


def _t(x, y, s, size=11, fill=TXT2, anchor="start", weight=None):
    w = f' font-weight="{weight}"' if weight else ""
    return (f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" '
            f'font-size="{size}" fill="{fill}"{w}>{s}</text>')


def _rect(x, y, w, h, fill=BGBOX, stroke=INK, sw=1.5, rx=4):
    return (f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" '
            f'rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')


def _line(x1, y1, x2, y2, color=INK, sw=2.0, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
            f'stroke="{color}" stroke-width="{sw}"{d}/>')


def _polyline(pts, color=INK, sw=2.0):
    s = " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
    return f'<polyline points="{s}" fill="none" stroke="{color}" stroke-width="{sw}"/>'


def _fuse_sym(x, y, color=INK, size=16, sw=1.5):
    """Символ запобіжника: прямокутник з рискою всередині."""
    hw, hh = size // 2, size // 4
    return [
        f'<rect x="{x - hw:.0f}" y="{y - hh:.0f}" width="{size:.0f}" height="{size // 2:.0f}" '
        f'fill="white" stroke="{color}" stroke-width="{sw}" rx="2"/>',
        f'<line x1="{x - hw:.0f}" y1="{y:.0f}" x2="{x + hw:.0f}" y2="{y:.0f}" '
        f'stroke="{color}" stroke-width="{sw}"/>',
    ]


def _relay_sym(x, y, color=INK, size=14, sw=1.5):
    """Символ реле: кружок з горизонтальною рискою."""
    r = size // 2
    return [
        f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="white" '
        f'stroke="{color}" stroke-width="{sw}"/>',
        f'<line x1="{x - r + 3:.0f}" y1="{y - 3:.0f}" x2="{x + r - 3:.0f}" y2="{y + 3:.0f}" '
        f'stroke="{color}" stroke-width="{sw}"/>',
    ]


def _dimmer_sym(x, y, color=G1, size=14, sw=1.5):
    """Символ диммера: змінний резистор-трикутник."""
    return [
        f'<rect x="{x - size // 2:.0f}" y="{y - size // 4:.0f}" '
        f'width="{size:.0f}" height="{size // 2:.0f}" fill="white" '
        f'stroke="{color}" stroke-width="{sw}" rx="2"/>',
        f'<line x1="{x - size // 2 + 3:.0f}" y1="{y:.0f}" x2="{x + size // 2 - 3:.0f}" y2="{y:.0f}" '
        f'stroke="{color}" stroke-width="{sw}"/>',
        # стрілка діагональ
        f'<line x1="{x - 4:.0f}" y1="{y + 6:.0f}" x2="{x + 4:.0f}" y2="{y - 6:.0f}" '
        f'stroke="{color}" stroke-width="1.2"/>',
    ]


def _seg_label(seg, side="top"):
    """Рядок AWG · довжина · струм · просадка (власна / накопичена)."""
    est = " (прикидка)" if seg["estimate"] else ""
    own = f'{seg["drop_pct"]:.1f}%'
    cum = f'{seg["cum_pct"]:.1f}%'
    return (f'AWG{seg["awg"]} · {seg["length_m"]:g} м · {seg["amps"]:.2f} А'
            f' · −{own} (Σ{cum}){est}')


def _seg_label_short(seg):
    """Коротший підпис для вертикальних гілок."""
    est = "~" if seg["estimate"] else ""
    return (f'{est}AWG{seg["awg"]} {seg["length_m"]:g}м {seg["amps"]:.2f}А −{seg["drop_pct"]:.1f}%')


# ── Генерація SVG ─────────────────────────────────────────────────────────────

def svg():
    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {W} {H}" width="100%" '
        f'font-family="ui-monospace,Menlo,monospace">',
    ]

    # ── Фон ───────────────────────────────────────────────────────────────────
    o.append(f'<rect width="{W}" height="{H}" fill="#fafaf8"/>')

    # ── Заголовок ─────────────────────────────────────────────────────────────
    o.append(_t(W / 2, 28, "Щит подіуму і дерево кабелів · Hero Armor 2026",
                14, INK, "middle", weight="600"))
    peak = sum(lnm.peak_watts().values())
    o.append(_t(W / 2, 46,
                f'12 В шина · пік {peak:.0f} Вт · головний запобіжник {FUSE["main"]:g} А · '
                f'усі довжини — прикидки (★)',
                11, TXT2, "middle"))

    # ── Станція EcoFlow ───────────────────────────────────────────────────────
    sx, sy = STAT_X, STAT_Y - STAT_H // 2
    o.append(_rect(sx, sy, STAT_W, STAT_H, fill="#efeee7", stroke=INK, sw=2.0))
    o.append(_t(sx + STAT_W / 2, sy + 18, "Станція", 11, INK, "middle", weight="600"))
    o.append(_t(sx + STAT_W / 2, sy + 33, "EcoFlow", 11, INK, "middle"))
    o.append(_t(sx + STAT_W / 2, sy + 52, f'{BUS_V:.0f} В вихід', 10, TXT2, "middle"))
    o.append(_t(sx + STAT_W / 2, sy + 67, f'{FUSE["main"]:g} А макс', 10, TXT2, "middle"))
    o.append(_t(sx + STAT_W / 2, sy + 83, META["station"]["note"], 10, GHOST, "middle"))

    # ── Магістраль trunk ──────────────────────────────────────────────────────
    trunk = SEG["trunk"]
    y_trunk = STAT_Y
    x_from = STAT_X + STAT_W
    x_to = PANEL_X
    trunk_color = _drop_color(trunk["drop_pct"], trunk["cum_pct"])
    # лінія магістралі
    o.append(_line(x_from, y_trunk, x_to, y_trunk, color=ACC, sw=3.5))
    # запобіжник головний — на середині магістралі
    fuse_x = (x_from + x_to) // 2
    o.extend(_fuse_sym(fuse_x, y_trunk, color=ACC, size=18))
    o.append(_t(fuse_x, y_trunk - 22,
                f'Головний {FUSE["main"]:g} А ({FUSE_A["main"]:.1f} А робочий)',
                10, ACC, "middle"))
    # підпис кабелю магістралі
    lbl = _seg_label_short(trunk)
    c = _drop_color(trunk["drop_pct"], trunk["cum_pct"])
    o.append(_t(fuse_x, y_trunk + 18, lbl, 10, c, "middle"))

    # ── Щит ───────────────────────────────────────────────────────────────────
    o.append(_rect(PANEL_X, PANEL_Y, PANEL_W, PANEL_H, fill=BGBOX, stroke=INK, sw=2.0))
    o.append(_t(PANEL_X + PANEL_W / 2, PANEL_Y + 14, "Щит", 11, INK, "middle", weight="600"))
    o.append(_t(PANEL_X + PANEL_W / 2, PANEL_Y + 28, "подіуму", 11, INK, "middle", weight="600"))

    # три групових запобіжники всередині щита, вертикально розміщені
    fuse_y_positions = {
        "g1": PANEL_Y + 60,
        "g2": PANEL_Y + 100,
        "g3a": PANEL_Y + 140,
    }
    for gid, gy in fuse_y_positions.items():
        fc = GRP_COLOR[gid]
        o.extend(_fuse_sym(PANEL_X + PANEL_W // 2, gy, color=fc, size=14))
        o.append(_t(PANEL_X + PANEL_W // 2, gy - 12,
                    f'{FUSE[gid]:g} А', 9, fc, "middle"))

    # ── Гілки трьох груп ─────────────────────────────────────────────────────
    group_data = [
        # (id, Y-центр, сегменти гілки в порядку від щита до навантаження)
        ("g1",  Y_G1,  ["br_g1", "ring_g1", "drop_spot"]),
        ("g2",  Y_G2,  ["br_g2", "inj_g2", "drop_robot", "drop_back_core"]),
        ("g3a", Y_G3,  ["br_g3a", "stairs_g3a"]),
    ]

    for gid, gy, seg_ids in group_data:
        gc = GRP_COLOR[gid]
        glabel = GROUPS[gid]["label"]

        # Точка виходу зі щита
        panel_exit_x = PANEL_X + PANEL_W
        panel_exit_y = fuse_y_positions[gid]

        # горизонтальна лінія зі щита до Y-рівня групи
        x_bend = panel_exit_x + 30
        o.append(_polyline(
            [(panel_exit_x, panel_exit_y), (x_bend, panel_exit_y),
             (x_bend, gy)],
            color=gc, sw=2.0))

        # ── Реле групи ────────────────────────────────────────────────────────
        relay_x = x_bend + 30
        o.append(_line(x_bend, gy, relay_x, gy, color=gc, sw=2.0))
        o.extend(_relay_sym(relay_x, gy, color=gc))
        o.append(_t(relay_x, gy - 16, "реле", 9, gc, "middle"))

        # ── Диммер / контролер для Гр.1 і Гр.2 ─────────────────────────────
        x_after_relay = relay_x + 12
        x_dim = x_after_relay + 30
        if gid == "g1":
            o.append(_line(x_after_relay, gy, x_dim, gy, color=gc, sw=2.0))
            o.extend(_dimmer_sym(x_dim, gy, color=gc))
            o.append(_t(x_dim, gy - 16, "ШІМ-диммер 30 А", 9, gc, "middle"))
            x_group_start = x_dim + 12
        elif gid == "g2":
            # контролер WLED
            cwx, cww, cwh = x_after_relay + 10, 58, 26
            cwy = gy - cwh // 2
            o.append(_line(x_after_relay, gy, cwx, gy, color=gc, sw=2.0))
            o.append(_rect(cwx, cwy, cww, cwh, fill="#e8f0f8", stroke=gc, sw=1.5))
            o.append(_t(cwx + cww / 2, gy - 4, "WLED", 9, gc, "middle", weight="600"))
            o.append(_t(cwx + cww / 2, gy + 10, "контролер", 9, gc, "middle"))
            x_group_start = cwx + cww
        else:
            x_group_start = x_after_relay

        # ── Відрізки гілки (від x_group_start горизонтально) ────────────────
        x_cur = x_group_start

        # зберігаємо де і які підгілки є
        branch_lines = []  # (seg, x1, x2, y, sub_ids)

        # Для Гр.2 є три кінцеві: inj_g2 (стрічка), drop_robot, drop_back_core
        # Для Гр.1: ring_g1 → drop_spot (один)
        # Для Гр.3А: stairs_g3a (один)

        if gid == "g1":
            # br_g1 → ring_g1 → drop_spot
            br_seg = SEG["br_g1"]
            ring_seg = SEG["ring_g1"]
            drop_seg = SEG["drop_spot"]

            # від щита до диммера вже намальовано, тепер від диммера далі
            x1 = x_group_start
            x2 = X_BR + 20
            o.append(_line(x1, gy, x2, gy, color=gc, sw=2.5))

            # підписи br_g1 зверху
            mid_x = (x1 + x2) / 2
            lbl_br = _seg_label_short(br_seg)
            ccolor = _drop_color(br_seg["drop_pct"], br_seg["cum_pct"])
            o.append(_t(mid_x, gy - 10, lbl_br, 9, ccolor, "middle"))

            # ring_g1 — кільце прожекторів (показуємо горизонтально далі)
            x3 = X_BR + 80
            o.append(_line(x2, gy, x3, gy, color=gc, sw=2.5))
            lbl_ring = _seg_label_short(ring_seg)
            ccolor2 = _drop_color(ring_seg["drop_pct"], ring_seg["cum_pct"])
            o.append(_t((x2 + x3) / 2, gy - 10, lbl_ring, 9, ccolor2, "middle"))

            # drop_spot — вниз до прожектора
            x_drop = x3
            y_load = gy + 55
            o.append(_line(x_drop, gy, x_drop, y_load, color=gc, sw=1.8))
            # прямокутник прожектора
            lw, lh = 100, 28
            o.append(_rect(x_drop - lw // 2, y_load, lw, lh,
                           fill="#fff8ea", stroke=gc, sw=1.5))
            o.append(_t(x_drop, y_load + 12, "8× прожектор MR16", 9, gc, "middle"))
            o.append(_t(x_drop, y_load + 24, f'5 Вт кожен · Гр.1', 9, TXT2, "middle"))
            # підпис drop
            lbl_drop = _seg_label_short(drop_seg)
            ccolor3 = _drop_color(drop_seg["drop_pct"], drop_seg["cum_pct"])
            o.append(_t(x_drop + 6, gy + 22, lbl_drop, 9, ccolor3, "start"))

            # позначка групи
            o.append(_t(x1 + 2, gy - 38, glabel, 10, gc, "start", weight="600"))

        elif gid == "g2":
            # br_g2 → [inj_g2 (стрічка), drop_robot, drop_back_core]
            br_seg = SEG["br_g2"]
            inj_seg = SEG["inj_g2"]
            rob_seg = SEG["drop_robot"]
            back_seg = SEG["drop_back_core"]

            # горизонтальна лінія br_g2
            x1 = x_group_start
            x_node = X_BR + 30
            o.append(_line(x1, gy, x_node, gy, color=gc, sw=2.5))
            lbl_br = _seg_label_short(br_seg)
            ccolor_br = _drop_color(br_seg["drop_pct"], br_seg["cum_pct"])
            o.append(_t((x1 + x_node) / 2, gy - 10, lbl_br, 9, ccolor_br, "middle"))

            # точка розгалуження — вертикальна шина
            y_top = gy - 80
            y_bot = gy + 80
            o.append(_line(x_node, y_top, x_node, y_bot, color=gc, sw=1.5, dash="4 3"))

            # inj_g2: стрічка (вгору)
            y_strip = gy - 80
            x_strip_end = X_LOAD
            o.append(_line(x_node, y_strip, x_strip_end, y_strip, color=gc, sw=2.0))
            o.append(_t((x_node + x_strip_end) / 2, y_strip - 10,
                        _seg_label_short(inj_seg), 9,
                        _drop_color(inj_seg["drop_pct"], inj_seg["cum_pct"]), "middle"))
            lw, lh = 120, 32
            o.append(_rect(x_strip_end - lw // 2, y_strip - lh - 5, lw, lh,
                           fill="#e8f0f8", stroke=gc, sw=1.5))
            o.append(_t(x_strip_end, y_strip - lh + 5, "8× рукав стрічки", 9, gc, "middle"))
            o.append(_t(x_strip_end, y_strip - 10, "«Біжуча вода» WS2811", 9, TXT2, "middle"))

            # drop_robot: лампи робота (середина)
            y_rob = gy
            x_rob_end = X_LOAD
            o.append(_line(x_node, y_rob, x_rob_end, y_rob, color=gc, sw=2.0))
            o.append(_t((x_node + x_rob_end) / 2, y_rob - 10,
                        _seg_label_short(rob_seg), 9,
                        _drop_color(rob_seg["drop_pct"], rob_seg["cum_pct"]), "middle"))
            lw2, lh2 = 120, 32
            o.append(_rect(x_rob_end - lw2 // 2, y_rob - lh2 // 2, lw2, lh2,
                           fill="#e8f0f8", stroke=gc, sw=1.5))
            o.append(_t(x_rob_end, y_rob - 4, "Лампи робота + WLED", 9, gc, "middle"))
            o.append(_t(x_rob_end, y_rob + 11, f'10× 0.4 Вт + контролер 4 Вт', 9, TXT2, "middle"))

            # drop_back_core: ядро на спині (вниз)
            y_back = gy + 80
            x_back_end = X_LOAD
            o.append(_line(x_node, y_back, x_back_end, y_back, color=gc, sw=2.0))
            o.append(_t((x_node + x_back_end) / 2, y_back - 10,
                        _seg_label_short(back_seg), 9,
                        _drop_color(back_seg["drop_pct"], back_seg["cum_pct"]), "middle"))
            lw3, lh3 = 120, 32
            o.append(_rect(x_back_end - lw3 // 2, y_back - lh3 // 2, lw3, lh3,
                           fill="#e8f0f8", stroke=gc, sw=1.5))
            o.append(_t(x_back_end, y_back - 4, "Ядро на спині (спина)", 9, gc, "middle"))
            o.append(_t(x_back_end, y_back + 11, "WS2812B 241 діод · 8.3 Вт пік", 9, TXT2, "middle"))

            # позначка групи
            o.append(_t(x1 + 2, gy - 108, glabel, 10, gc, "start", weight="600"))

        elif gid == "g3a":
            # br_g3a → stairs_g3a
            # та ще box_g3a — окремий від магістралі подіуму (parent=null)
            br_seg = SEG["br_g3a"]
            st_seg = SEG["stairs_g3a"]
            box_seg = SEG["box_g3a"]

            x1 = x_group_start
            x_node = X_BR + 30
            o.append(_line(x1, gy, x_node, gy, color=gc, sw=2.5))
            ccolor_br = _drop_color(br_seg["drop_pct"], br_seg["cum_pct"])
            o.append(_t((x1 + x_node) / 2, gy - 10,
                        _seg_label_short(br_seg), 9, ccolor_br, "middle"))

            # stairs_g3a → врізні вогні
            x_st_end = X_LOAD
            o.append(_line(x_node, gy, x_st_end, gy, color=gc, sw=2.0))
            ccolor_st = _drop_color(st_seg["drop_pct"], st_seg["cum_pct"])
            o.append(_t((x_node + x_st_end) / 2, gy - 10,
                        _seg_label_short(st_seg), 9, ccolor_st, "middle"))
            lw, lh = 130, 36
            o.append(_rect(x_st_end - lw // 2, gy - lh // 2, lw, lh,
                           fill="#e8f5ec", stroke=gc, sw=1.5))
            o.append(_t(x_st_end, gy - 6, "24× врізні вогні торця", 9, gc, "middle"))
            o.append(_t(x_st_end, gy + 10, "0.6 Вт · IP67 · по колу подіуму", 9, TXT2, "middle"))

            # box_g3a — маркерні вогники ящика: ідуть від самої станції
            # показуємо окремою пунктирною лінією від станції донизу
            by = gy + 55
            box_from_x = STAT_X + STAT_W
            box_from_y = STAT_Y + 40
            o.append(_polyline(
                [(box_from_x, box_from_y), (box_from_x + 20, box_from_y),
                 (box_from_x + 20, by), (X_LOAD, by)],
                color=gc, sw=1.5))
            # підпис
            o.append(_t((box_from_x + 20 + X_LOAD) / 2, by - 10,
                        f'~AWG{box_seg["awg"]} {box_seg["length_m"]:g}м '
                        f'{box_seg["amps"]:.2f}А −{box_seg["drop_pct"]:.1f}% (★)',
                        9, gc, "middle"))
            lw2, lh2 = 130, 36
            o.append(_rect(X_LOAD - lw2 // 2, by - lh2 // 2, lw2, lh2,
                           fill="#e8f5ec", stroke=gc, sw=1.5))
            o.append(_t(X_LOAD, by - 6, "2× маркерний вогник", 9, gc, "middle"))
            o.append(_t(X_LOAD, by + 10, "ящика станції · 0.24 Вт · в стінці", 9, TXT2, "middle"))
            # позначка пунктиру
            o.append(_t(box_from_x + 24, box_from_y + 8, "окремо від щита", 8, GHOST, "start"))

            # позначка групи
            o.append(_t(x1 + 2, gy - 30, glabel, 10, gc, "start", weight="600"))

    # ── Легенда ───────────────────────────────────────────────────────────────
    LEG_X = 36
    LEG_Y = H - 118
    LEG_STEP = 20

    o.append(_t(LEG_X, LEG_Y - 14, "Легенда:", 11, INK, "start", weight="600"))

    # колірна шкала просадки
    for lbl, color in [
        (f'просадка у нормі (≤ {WARN_PCT:.0f}%)', INK),
        (f'попередження ({WARN_PCT:.0f}–{CRIT_PCT:.0f}%)', WARN),
        (f'критична (> {CRIT_PCT:.0f}%) — підсвічено', CRIT),
    ]:
        o.append(_line(LEG_X, LEG_Y + 4, LEG_X + 24, LEG_Y + 4, color=color, sw=3.0))
        o.append(_t(LEG_X + 30, LEG_Y + 8, lbl, 10, TXT2))
        LEG_Y += LEG_STEP

    # символи
    o.extend(_fuse_sym(LEG_X + 12, LEG_Y + 6, color=INK, size=14))
    o.append(_t(LEG_X + 30, LEG_Y + 10, "запобіжник (номінал вказано поруч)", 10, TXT2))
    LEG_Y += LEG_STEP

    o.extend(_relay_sym(LEG_X + 12, LEG_Y + 6, color=INK, size=12))
    o.append(_t(LEG_X + 30, LEG_Y + 10, "реле групи", 10, TXT2))
    LEG_Y += LEG_STEP

    # AWG пояснення
    o.append(_t(LEG_X, LEG_Y + 10,
                "★ = довжина прикидкова (estimate: true), не з креслення конструктора",
                10, WARN))
    LEG_Y += LEG_STEP
    o.append(_t(LEG_X, LEG_Y + 10,
                "підпис сегмента: AWG · довжина м · струм А · −просадка% (Σнакопичена%)",
                10, TXT2))

    # ── Колонки з запобіжниками (числова таблиця) ───────────────────────────
    tbl_x = 540
    tbl_y = H - 118
    o.append(_t(tbl_x, tbl_y - 14, "Запобіжники:", 11, INK, "start", weight="600"))
    headers = [("Лінія", 0), ("Роб.А", 130), ("Ном.А", 190)]
    for hdr, dx in headers:
        o.append(_t(tbl_x + dx, tbl_y, hdr, 10, INK, "start", weight="600"))
    for i, f in enumerate(FUSE_LIST):
        ry = tbl_y + 16 + i * 17
        o.append(_t(tbl_x, ry, f['label'], 9, TXT2))
        o.append(_t(tbl_x + 130, ry, f'{f["amps"]:.2f}', 9, TXT2))
        o.append(_t(tbl_x + 190, ry, f'{f["rating"]:g}', 9, INK, weight="600"))

    # ── Підвал ────────────────────────────────────────────────────────────────
    o.append(_t(W / 2, H - 8,
                "Числа з lights_node_model.cable_tree() — не вигадані. "
                "Довжини — прикидки до замірів на місці збірки.",
                9, GHOST, "middle"))

    o.append("</svg>")
    return "\n".join(o)


def main():
    out = Path(__file__).resolve().parent / "panel_tree.svg"
    out.write_text(svg())
    print(f"panel_tree.svg ({out.stat().st_size} байт)")

    # Верифікація через xml.etree
    import xml.etree.ElementTree as ET
    tree = ET.parse(out)
    root = tree.getroot()
    ns = "http://www.w3.org/2000/svg"
    texts = root.findall(f".//{{{ns}}}text")
    rects = root.findall(f".//{{{ns}}}rect")
    lines = root.findall(f".//{{{ns}}}line") + root.findall(f".//{{{ns}}}polyline")
    print(f"  <text>: {len(texts)}  <rect>: {len(rects)}  <line>/<polyline>: {len(lines)}")

    # Перевіряємо що всі текстові координати в межах viewBox
    vw, vh = 1000, 680
    bad = []
    for el in root.iter():
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        if tag in ("text", "rect", "circle", "line"):
            for attr in ("x", "y", "x1", "y1", "x2", "y2", "cx", "cy"):
                val = el.get(attr)
                if val is not None:
                    v = float(val)
                    if attr in ("x", "x1", "x2", "cx") and not (-20 <= v <= vw + 20):
                        bad.append(f"{tag} {attr}={v:.0f}")
                    if attr in ("y", "y1", "y2", "cy") and not (-20 <= v <= vh + 20):
                        bad.append(f"{tag} {attr}={v:.0f}")
    if bad:
        print(f"  ПОЗА viewBox ({len(bad)} елементів):")
        for b in bad[:10]:
            print(f"    {b}")
    else:
        print("  усі координати в межах viewBox ✓")


if __name__ == "__main__":
    main()
