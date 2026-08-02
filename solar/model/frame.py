#!/usr/bin/env python3
"""
Жива модель деревʼяного каркаса під сонячний масив.

Читає solar/data/frame.json (тип матеріалу, кут, деталі, анкери, такелаж)
та solar/data/params.json (потужність масиву, фактична конфігурація панелей).

Що рахується:
  · геометрія рами під фактичний масив (geometry)
  · розкрій дощок жадібним алгоритмом (cut_plan)
  · вітрове навантаження і сила на анкер (wind_load)

Функції geometry(), cut_plan(), wind_load() імпортуються сторінками хабу.
"""

import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

# ── шляхи ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
DATA = Path(__file__).resolve().parent.parent / "data"

FRAME = json.loads((DATA / "frame.json").read_text())
PARAMS = json.loads((DATA / "params.json").read_text())

# ── опорна панель (з frame.json) ─────────────────────────────────────────────
REF = FRAME["reference_panel"]        # 500 Вт, 1956 × 1134 × 30 мм

# ── матеріал ─────────────────────────────────────────────────────────────────
MAT = FRAME["material"]
BOARD_LEN = MAT["board_len_mm"]       # 2438 мм (8 ft)
THICK_MM   = MAT["actual_mm"][0]      # 38 мм (товщина 2×4)
WIDTH_MM   = MAT["actual_mm"][1]      # 89 мм

# ── кут ──────────────────────────────────────────────────────────────────────
TILT_DEG  = FRAME["tilt"]["deg"]      # 20°
TILT_RAD  = math.radians(TILT_DEG)

# ── просвіт під ящики ────────────────────────────────────────────────────────
FRONT_POST_MM = FRAME["clearance"]["front_post_mm"]  # 500 мм


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ГЕОМЕТРІЯ
# ═══════════════════════════════════════════════════════════════════════════════
def _panel_dims():
    """
    Визначає довжину і ширину однієї панелі.

    Якщо в params.json є поле panel.len_mm / panel.width_mm — беремо їх.
    Якщо ні — беремо розміри з reference_panel у frame.json і позначаємо
    це як прикидку (estimated=True).
    """
    p = PARAMS.get("panel", {})
    if "len_mm" in p and "width_mm" in p:
        return p["len_mm"], p["width_mm"], False
    # Прикидка: одна панель з reference_panel
    return REF["len_mm"], REF["width_mm"], True


def geometry():
    """
    Повертає словник з усіма розмірами рами:
      panel_len_mm, panel_width_mm — розмір однієї панелі
      n_panels               — кількість панелей (1 якщо прикидка)
      tilt_deg               — кут нахилу
      rise_mm                — підйом задньої сторони
      ground_proj_mm         — проекція рами на землю (горизонталь)
      rail_len_mm            — похила під панель = довжина панелі
      frame_width_mm         — загальна ширина рами
      post_front_mm          — передня стійка
      post_rear_mm           — задня стійка
      base_long_mm           — поздовжня база
      base_cross_mm          — поперечина бази
      top_cross_mm           — верхня поперечина
      brace_mm               — укосина (фіксована 620 мм)
      estimated              — True якщо розмір панелі взятий з reference_panel
      panel_w_watt           — потужність масиву (з params або reference)
    """
    panel_len, panel_width, estimated = _panel_dims()

    # Потужність
    panel_w = PARAMS.get("panel", {}).get("chosen_w", REF["w_watt"])

    rise_mm       = panel_len * math.sin(TILT_RAD)
    ground_proj   = panel_len * math.cos(TILT_RAD)

    post_front    = FRONT_POST_MM
    post_rear     = post_front + rise_mm

    # ширина рами = ширина панелі (панель лягає між рейками)
    frame_width   = panel_width

    # база і верхні поперечини — між поздовжніми (2×THICK відраховується
    # тому що поздовжні на ребро, поперечини між ними)
    base_cross    = frame_width - 2 * THICK_MM
    top_cross     = base_cross   # та сама формула

    return {
        "panel_len_mm":    panel_len,
        "panel_width_mm":  panel_width,
        "panel_w_watt":    panel_w,
        "tilt_deg":        TILT_DEG,
        "rise_mm":         rise_mm,
        "ground_proj_mm":  ground_proj,
        "rail_len_mm":     panel_len,
        "frame_width_mm":  frame_width,
        "post_front_mm":   post_front,
        "post_rear_mm":    post_rear,
        "base_long_mm":    ground_proj,
        "base_cross_mm":   base_cross,
        "top_cross_mm":    top_cross,
        "brace_mm":        620.0,          # фіксовано у frame.json, різати по місцю
        "estimated":       estimated,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. РОЗКРІЙ
# ═══════════════════════════════════════════════════════════════════════════════
def cut_plan():
    """
    Жадібний алгоритм укладання деталей у дошки 2438 мм.

    Повертає список дощок: [{board: N, pieces: [...], leftover_mm: X}, ...]
    і загальну кількість дощок.
    """
    g = geometry()

    # Кількість і довжини деталей з parts_pattern + реальних розмірів
    parts_pattern = FRAME["parts_pattern"]
    part_map = {
        "base_long":    (g["base_long_mm"],  2),
        "base_cross":   (g["base_cross_mm"], 2),
        "post_front":   (g["post_front_mm"], 2),
        "post_rear":    (g["post_rear_mm"],  2),
        "rail":         (g["rail_len_mm"],   2),
        "top_cross":    (g["top_cross_mm"],  2),
        "brace":        (g["brace_mm"],      4),
    }

    # Складаємо повний список деталей (розгорнутий)
    all_pieces = []
    for p in parts_pattern:
        pid = p["id"]
        if pid not in part_map:
            continue
        length, qty = part_map[pid]
        for i in range(qty):
            all_pieces.append({"id": pid, "name": p["name"], "len_mm": length})

    # Сортуємо за спаданням довжини (жадібний алгоритм дає кращий результат)
    all_pieces.sort(key=lambda x: -x["len_mm"])

    boards = []   # [{board: N, pieces: [...], leftover_mm: X}]

    for piece in all_pieces:
        placed = False
        for board in boards:
            if board["leftover_mm"] >= piece["len_mm"]:
                board["pieces"].append(piece)
                board["leftover_mm"] -= piece["len_mm"]
                placed = True
                break
        if not placed:
            boards.append({
                "board": len(boards) + 1,
                "pieces": [piece],
                "leftover_mm": BOARD_LEN - piece["len_mm"],
            })

    return {
        "boards": boards,
        "n_boards": len(boards),
        "board_len_mm": BOARD_LEN,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 3. ВІТРОВЕ НАВАНТАЖЕННЯ
# ═══════════════════════════════════════════════════════════════════════════════
def wind_load():
    """
    Орієнтовне вітрове навантаження на раму.

    Методика:
      1. Швидкісний натиск: q = 0.613 × v² Па  (при v у м/с)
         Коефіцієнт 0.613 = ρ_повітря/2 = 1.225/2
         Джерело: ASCE 7 / EN 1991-1-4, стандартна атмосфера на рівні моря.

      2. Коефіцієнт форми (Cd) для нахиленої плоскої пластини:
         ≈ 1.3 при куті ≤ 25°. Це консервативне наближення для
         прямокутної панелі на невисокому каркасі.
         Джерело: ASCE 7-22 Рисунок 29.4-1 (монтований на землі масив).

      3. Рівномірний розподіл сили на 4 анкерних точки.

    Поле _wind у frame.json зберігає коефіцієнти для прозорості.
    """
    wind_cfg = FRAME.get("_wind", {})

    # Швидкість вітру: з _wind або 70 mph
    v_mph = wind_cfg.get("design_wind_mph", 70.0)
    v_ms  = v_mph * 0.44704                  # mph → м/с

    # Коефіцієнт форми (Cd для нахиленої плити ≤ 25°)
    cd = wind_cfg.get("cd_panel", 1.3)

    # Кількість анкерів
    n_anchors = wind_cfg.get("n_anchors", 4)

    # Площа панелі
    g = geometry()
    area_m2 = (g["panel_len_mm"] / 1000) * (g["panel_width_mm"] / 1000)

    # Швидкісний натиск
    q_pa = 0.613 * v_ms ** 2

    # Сила (Н)
    force_n = q_pa * area_m2 * cd

    # Сила на один анкер
    per_anchor_n  = force_n / n_anchors
    per_anchor_kg = per_anchor_n / 9.81   # для розуміння: кг-сила

    return {
        "v_mph":           v_mph,
        "v_ms":            v_ms,
        "q_pa":            q_pa,
        "cd":              cd,
        "area_m2":         area_m2,
        "force_n":         force_n,
        "force_kg":        force_n / 9.81,
        "n_anchors":       n_anchors,
        "per_anchor_n":    per_anchor_n,
        "per_anchor_kg":   per_anchor_kg,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 4. SVG
# ═══════════════════════════════════════════════════════════════════════════════
# Палітра у стилі podium_plan.py
INK   = "#24231d"
TXT2  = "#6b675c"
THIN  = "#d8d5c9"
GHOST = "#c9c6ba"
ACC   = "#b35b1e"   # силова / розмірні лінії
SIG   = "#3d6f96"   # розміри
G2    = "#3d6f96"   # дошки розкрою (той самий що SIG — синій)
G3    = "#3d7a4f"   # залишки (зелений)
WARN  = "#b07c14"   # попередження


def _t(x, y, s, size=11, fill=TXT2, anchor="start", weight=None):
    w = f' font-weight="{weight}"' if weight else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
            f'font-size="{size}" fill="{fill}"{w}>{s}</text>')


def _dim_line(x1, y1, x2, y2, label, offset=12, horiz=True):
    """Розмірна лінія зі стрілками і підписом."""
    lines = []
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    lines.append(
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{SIG}" stroke-width="1.2" '
        f'marker-start="url(#fr-dim)" marker-end="url(#fr-dim)"/>'
    )
    if horiz:
        lines.append(_t(mid_x, mid_y - 4, label, 10, SIG, "middle"))
    else:
        lines.append(_t(mid_x + offset, mid_y, label, 10, SIG, "start"))
    return lines


def _svg_side_view(g, w, cx, top_y):
    """
    Вигляд рами збоку з розмірними лініями.

    Координати:
      Передня стійка — зліва, задня — справа.
      Підлога = top_y + panel_h (нижня лінія).
      Вся секція висотою panel_h.
    """
    lines = []

    scale = w / (g["ground_proj_mm"] * 1.35)  # пікс/мм
    panel_h = 260.0  # висота секції в пікселях

    # Опорні точки (зліва = передня сторона, знизу = підлога)
    floor_y = top_y + panel_h
    left_x  = cx - (g["ground_proj_mm"] * scale) / 2
    right_x = left_x + g["ground_proj_mm"] * scale

    post_f_h = g["post_front_mm"] * scale
    post_r_h = g["post_rear_mm"]  * scale

    front_top_y = floor_y - post_f_h
    rear_top_y  = floor_y - post_r_h

    # Панель (від front_top до rear_top)
    rail_len_px = g["rail_len_mm"] * scale

    # --- підлога
    lines.append(
        f'<line x1="{left_x - 15:.1f}" y1="{floor_y:.1f}" '
        f'x2="{right_x + 15:.1f}" y2="{floor_y:.1f}" '
        f'stroke="{THIN}" stroke-width="1.5" stroke-dasharray="6 4"/>'
    )

    # --- передня стійка
    lines.append(
        f'<rect x="{left_x:.1f}" y="{front_top_y:.1f}" '
        f'width="{THICK_MM * scale:.1f}" height="{post_f_h:.1f}" '
        f'fill="#f5f4ef" stroke="{INK}" stroke-width="1.5"/>'
    )
    # --- задня стійка
    lines.append(
        f'<rect x="{right_x - THICK_MM * scale:.1f}" y="{rear_top_y:.1f}" '
        f'width="{THICK_MM * scale:.1f}" height="{post_r_h:.1f}" '
        f'fill="#f5f4ef" stroke="{INK}" stroke-width="1.5"/>'
    )

    # --- похила (панельна рейка)
    rail_color = ACC
    lines.append(
        f'<line x1="{left_x + THICK_MM * scale / 2:.1f}" y1="{front_top_y:.1f}" '
        f'x2="{right_x - THICK_MM * scale / 2:.1f}" y2="{rear_top_y:.1f}" '
        f'stroke="{rail_color}" stroke-width="3.5"/>'
    )
    # Заповнення «панелі» — напівпрозорий прямокутник паралельно похилій
    sx = left_x + THICK_MM * scale / 2
    sy = front_top_y
    ex = right_x - THICK_MM * scale / 2
    ey = rear_top_y
    dx = ex - sx
    dy = ey - sy
    length = math.hypot(dx, dy)
    nx, ny = -dy / length * 8, dx / length * 8  # нормаль 8 пікселів
    pts = (
        f"{sx:.1f},{sy:.1f} {ex:.1f},{ey:.1f} "
        f"{ex + nx:.1f},{ey + ny:.1f} {sx + nx:.1f},{sy + ny:.1f}"
    )
    lines.append(
        f'<polygon points="{pts}" fill="#d4e8f8" opacity="0.6" stroke="none"/>'
    )

    # --- база
    lines.append(
        f'<rect x="{left_x:.1f}" y="{floor_y:.1f}" '
        f'width="{right_x - left_x:.1f}" height="{THICK_MM * scale * 1.2:.1f}" '
        f'fill="#f5f4ef" stroke="{INK}" stroke-width="1.5"/>'
    )

    # --- кут нахилу (дуга + підпис)
    r_arc = 32
    ang_end_x = left_x + THICK_MM * scale / 2 + r_arc * math.cos(TILT_RAD)
    ang_end_y = front_top_y - r_arc * math.sin(TILT_RAD)
    lines.append(
        f'<path d="M {left_x + THICK_MM * scale / 2 + r_arc:.1f},{front_top_y:.1f} '
        f'A {r_arc},{r_arc} 0 0 1 {ang_end_x:.1f},{ang_end_y:.1f}" '
        f'fill="none" stroke="{WARN}" stroke-width="1.2"/>'
    )
    lines.append(_t(
        left_x + THICK_MM * scale / 2 + r_arc + 4,
        front_top_y - 6,
        f"{g['tilt_deg']}°",
        11, WARN
    ))

    # --- розмірна лінія: проекція на землю
    dim_y = floor_y + THICK_MM * scale * 1.2 + 22
    lines.extend(_dim_line(
        left_x, dim_y, right_x, dim_y,
        f"проекція {g['ground_proj_mm']:.0f} мм", horiz=True
    ))

    # --- розмірна лінія: підйом
    rise_px = (g["rise_mm"]) * scale
    dim_rx = right_x + 34
    lines.extend(_dim_line(
        dim_rx, rear_top_y, dim_rx, front_top_y,
        f"підйом\n{g['rise_mm']:.0f} мм", offset=14, horiz=False
    ))
    # Горизонтальний поводок до задньої стійки
    lines.append(
        f'<line x1="{right_x:.1f}" y1="{rear_top_y:.1f}" '
        f'x2="{dim_rx:.1f}" y2="{rear_top_y:.1f}" '
        f'stroke="{THIN}" stroke-width="0.8"/>'
    )
    lines.append(
        f'<line x1="{right_x:.1f}" y1="{front_top_y:.1f}" '
        f'x2="{dim_rx:.1f}" y2="{front_top_y:.1f}" '
        f'stroke="{THIN}" stroke-width="0.8"/>'
    )

    # --- розмірна лінія: передня стійка
    dim_lx = left_x - 28
    lines.extend(_dim_line(
        dim_lx, front_top_y, dim_lx, floor_y,
        f"перед {g['post_front_mm']:.0f} мм", offset=-70, horiz=False
    ))
    lines.append(
        f'<line x1="{left_x:.1f}" y1="{front_top_y:.1f}" '
        f'x2="{dim_lx:.1f}" y2="{front_top_y:.1f}" '
        f'stroke="{THIN}" stroke-width="0.8"/>'
    )
    lines.append(
        f'<line x1="{left_x:.1f}" y1="{floor_y:.1f}" '
        f'x2="{dim_lx:.1f}" y2="{floor_y:.1f}" '
        f'stroke="{THIN}" stroke-width="0.8"/>'
    )

    # --- підписи стійок
    lines.append(_t(
        left_x + THICK_MM * scale / 2, front_top_y - 6,
        "↓ пд", 9, TXT2, "middle"
    ))
    lines.append(_t(
        right_x - THICK_MM * scale / 2, rear_top_y - 6,
        "↓ пн", 9, TXT2, "middle"
    ))

    # --- підпис рейки (похилої)
    mid_rx = (sx + ex) / 2 + nx / 2
    mid_ry = (sy + ey) / 2 + ny / 2
    lines.append(_t(
        mid_rx, mid_ry - 6,
        f"рейка {g['rail_len_mm']:.0f} мм", 9, ACC, "middle"
    ))

    # --- підпис "Вигляд збоку"
    lines.append(_t(cx, top_y - 10, "Вигляд збоку", 13, INK, "middle", "bold"))

    # --- підпис "підлога"
    lines.append(_t(right_x + 16, floor_y + 4, "підлога", 9, TXT2))

    return lines


def _svg_cut_plan(cp, g, cx, top_y, section_w):
    """Схема розкрою дощок."""
    lines = []
    lines.append(_t(cx, top_y - 10, "Розкрій: дошки 8 ft (2438 мм)", 13, INK, "middle", "bold"))

    boards = cp["boards"]
    board_px = section_w * 0.82
    scale = board_px / cp["board_len_mm"]
    row_h = 28
    gap   = 10

    # кольори деталей (по типу id)
    color_map = {
        "base_long":  "#b35b1e",
        "base_cross": "#8b4513",
        "post_front": "#3d6f96",
        "post_rear":  "#2d5477",
        "rail":       "#3d7a4f",
        "top_cross":  "#5b8a6f",
        "brace":      "#b07c14",
    }

    lx0 = cx - board_px / 2
    y   = top_y + 6

    for b in boards:
        by = y
        # сама дошка (рамка)
        lines.append(
            f'<rect x="{lx0:.1f}" y="{by:.1f}" '
            f'width="{board_px:.1f}" height="{row_h:.1f}" '
            f'fill="#f9f8f5" stroke="{INK}" stroke-width="1.2" rx="2"/>'
        )
        # деталі
        offset_px = 0.0
        for piece in b["pieces"]:
            pw = piece["len_mm"] * scale
            color = color_map.get(piece["id"], INK)
            lines.append(
                f'<rect x="{lx0 + offset_px:.1f}" y="{by:.1f}" '
                f'width="{pw:.1f}" height="{row_h:.1f}" '
                f'fill="{color}" opacity="0.75" stroke="none" rx="2"/>'
            )
            # підпис деталі (якщо влазить)
            short_name = piece["name"].split()[0]
            if pw > 30:
                lines.append(_t(
                    lx0 + offset_px + pw / 2,
                    by + row_h / 2 + 4,
                    short_name, 8, "#ffffff", "middle"
                ))
            offset_px += pw

        # залишок
        left_px = b["leftover_mm"] * scale
        if left_px > 2:
            lines.append(
                f'<rect x="{lx0 + offset_px:.1f}" y="{by:.1f}" '
                f'width="{left_px:.1f}" height="{row_h:.1f}" '
                f'fill="{G3}" opacity="0.3" stroke="{G3}" '
                f'stroke-width="0.8" rx="2"/>'
            )
            lines.append(_t(
                lx0 + offset_px + left_px / 2,
                by + row_h / 2 + 4,
                f"~{b['leftover_mm']:.0f}", 8, G3, "middle"
            ))

        # номер дошки
        lines.append(_t(
            lx0 - 4, by + row_h / 2 + 4,
            f"#{b['board']}", 9, TXT2, "end"
        ))
        y += row_h + gap

    # підсумок
    y += 4
    lines.append(_t(
        cx, y,
        f"Всього дощок: {cp['n_boards']}  (8 ft / 2438 мм кожна)",
        11, INK, "middle"
    ))

    return lines, y


def _svg_wind_block(wl, x, y, block_w):
    """Блок вітрового навантаження."""
    lines = []
    bw, bh = block_w, 100
    # рамка
    lines.append(
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
        f'rx="4" fill="#fdf9f2" stroke="{WARN}" stroke-width="1.2"/>'
    )
    lines.append(_t(x + bw / 2, y + 16, "Вітрове навантаження (70 mph)", 11, WARN, "middle", "bold"))
    step = 17
    data = [
        f"Швидкість: {wl['v_mph']:.0f} mph = {wl['v_ms']:.1f} м/с",
        f"Тиск q = 0.613·v² = {wl['q_pa']:.0f} Па",
        f"Площа панелі: {wl['area_m2']:.3f} м², Cd={wl['cd']}",
        f"Сила на раму: {wl['force_n']:.0f} Н = {wl['force_kg']:.1f} кгс",
        f"На 1 анкер ({wl['n_anchors']} точки): {wl['per_anchor_n']:.0f} Н"
        f" ≈ {wl['per_anchor_kg']:.1f} кгс",
    ]
    for i, row in enumerate(data):
        lines.append(_t(x + 10, y + 32 + i * step, row, 10, TXT2))
    return lines


def generate_svg():
    """Генерує повний SVG і повертає рядком."""
    g  = geometry()
    cp = cut_plan()
    wl = wind_load()

    W, H = 960, 820
    # Секції
    side_top   = 72
    side_h     = 300
    cut_top    = side_top + side_h + 40
    wind_top   = cut_top + cp["n_boards"] * 38 + 60
    wind_block_w = 400

    o = []
    o.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {W} {H}" width="100%" '
        f'font-family="ui-monospace,Menlo,monospace">'
    )
    # defs
    o.append(
        '<defs>'
        f'<marker id="fr-dim" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{SIG}"/></marker>'
        '</defs>'
    )

    # ── шапка ────────────────────────────────────────────────────────────────
    est_note = " (прикидка — reference_panel)" if g["estimated"] else ""
    o.append(_t(
        W / 2, 22,
        f"Каркас під сонячний масив — Hero Armor BM 2026",
        14, INK, "middle", "bold"
    ))
    o.append(_t(
        W / 2, 40,
        f"2×4 Douglas Fir · нахил {g['tilt_deg']}° · панель "
        f"{g['panel_len_mm']:.0f}×{g['panel_width_mm']:.0f} мм "
        f"{g['panel_w_watt']} Вт{est_note}",
        11, TXT2, "middle"
    ))

    # розподільча лінія
    o.append(
        f'<line x1="24" y1="52" x2="{W - 24}" y2="52" '
        f'stroke="{THIN}" stroke-width="1"/>'
    )

    # ── вигляд збоку ─────────────────────────────────────────────────────────
    side_lines = _svg_side_view(g, W * 0.55, W / 2, side_top + 16)
    o.extend(side_lines)

    # ── розкрій ──────────────────────────────────────────────────────────────
    cut_lines, cut_bottom_y = _svg_cut_plan(cp, g, W / 2, cut_top + 16, W * 0.72)
    o.extend(cut_lines)

    # підпис "залишки"
    o.append(_t(W / 2, cut_bottom_y + 14,
                "Залишки (зелені) ~480 мм: підкладки під базу на нерівній плайї",
                10, G3, "middle"))

    # ── вітрове навантаження ─────────────────────────────────────────────────
    actual_wind_top = cut_bottom_y + 32
    wind_lines = _svg_wind_block(
        wl,
        x=(W - wind_block_w) / 2,
        y=actual_wind_top,
        block_w=wind_block_w,
    )
    o.extend(wind_lines)

    # ── легенда ──────────────────────────────────────────────────────────────
    leg_y = actual_wind_top + 115
    leg_x = 24
    o.append(_t(leg_x, leg_y, "Легенда розкрою:", 10, INK, "start", "bold"))
    legend_items = [
        ("base_long",  "База поздовжня"),
        ("base_cross", "База поперечина"),
        ("post_front", "Стійка передня"),
        ("post_rear",  "Стійка задня"),
        ("rail",       "Похила (рейка)"),
        ("top_cross",  "Верхня поперечина"),
        ("brace",      "Укосина"),
    ]
    color_map_leg = {
        "base_long":  "#b35b1e",
        "base_cross": "#8b4513",
        "post_front": "#3d6f96",
        "post_rear":  "#2d5477",
        "rail":       "#3d7a4f",
        "top_cross":  "#5b8a6f",
        "brace":      "#b07c14",
    }
    row = 0
    for pid, name in legend_items:
        col = row % 4
        r   = row // 4
        lx  = leg_x + col * 220
        ly  = leg_y + 16 + r * 20
        c   = color_map_leg[pid]
        o.append(
            f'<rect x="{lx}" y="{ly - 10}" width="16" height="12" '
            f'fill="{c}" opacity="0.75" rx="2"/>'
        )
        o.append(_t(lx + 20, ly, name, 10, TXT2))
        row += 1

    # залишок
    lx = leg_x + (row % 4) * 220
    ly = leg_y + 16 + (row // 4) * 20
    o.append(
        f'<rect x="{lx}" y="{ly - 10}" width="16" height="12" '
        f'fill="{G3}" opacity="0.3" stroke="{G3}" stroke-width="0.8" rx="2"/>'
    )
    o.append(_t(lx + 20, ly, "залишок", 10, G3))

    # ── підвал ───────────────────────────────────────────────────────────────
    foot_y = leg_y + 40
    o.append(
        f'<line x1="24" y1="{foot_y}" x2="{W - 24}" y2="{foot_y}" '
        f'stroke="{THIN}" stroke-width="1"/>'
    )
    o.append(_t(
        W / 2, foot_y + 14,
        "Такелаж: трос 1/8\" ПВХ · рим-болти 1/4\"×3\" у верх стійок · "
        f"анкери lag screw 3/8\"×10\" під кутом 45° — {wl['n_anchors']} основних",
        10, TXT2, "middle"
    ))

    final_h = foot_y + 30
    # Перезапишемо viewBox з правильною висотою
    o[0] = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {W} {final_h}" width="100%" '
        f'font-family="ui-monospace,Menlo,monospace">'
    )

    o.append("</svg>")
    return "\n".join(o), W, final_h


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ПЕРЕВІРКА SVG (перетини підписів)
# ═══════════════════════════════════════════════════════════════════════════════
def _check_svg_labels(svg_text, W, H):
    """
    Перевіряє, що всі підписи в межах viewBox.
    Повертає (ok: bool, errors: list[str]).
    """
    root = ET.fromstring(svg_text)
    ns = ""
    texts = root.iter(f"{ns}text") if ns else root.iter("text")

    errors = []
    labels = []

    for t in root.iter("{http://www.w3.org/2000/svg}text"):
        pass  # з namespace
    # Спробуємо без namespace (svg може бути без)
    all_texts = list(root.iter("text"))
    if not all_texts:
        # Спроба з namespace
        all_texts = list(root.iter("{http://www.w3.org/2000/svg}text"))

    for t in all_texts:
        x = float(t.get("x", 0))
        y = float(t.get("y", 0))
        fs = float(t.get("font-size", 11))
        text = (t.text or "")
        # Приблизна ширина: кількість символів × 0.55 × font-size
        est_w = len(text) * 0.55 * fs
        anchor = t.get("text-anchor", "start")

        if anchor == "middle":
            x_min, x_max = x - est_w / 2, x + est_w / 2
        elif anchor == "end":
            x_min, x_max = x - est_w, x
        else:
            x_min, x_max = x, x + est_w

        y_min, y_max = y - fs, y

        if x_min < 0 or x_max > W or y_max > H + 10:
            errors.append(
                f"Підпис «{text[:30]}» може вийти за viewBox: "
                f"x=[{x_min:.0f}..{x_max:.0f}] y=[{y_min:.0f}..{y_max:.0f}] "
                f"(viewBox 0..{W} × 0..{H})"
            )

        labels.append((x, y, text[:40]))

    return len(errors) == 0, errors, len(all_texts)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    g  = geometry()
    cp = cut_plan()
    wl = wind_load()

    est = " (ПРИКИДКА: розмір взятий з reference_panel)" if g["estimated"] else ""
    print("=" * 62)
    print("ГЕОМЕТРІЯ РАМИ")
    print("=" * 62)
    print(f"Панель:           {g['panel_len_mm']:.0f} × {g['panel_width_mm']:.0f} мм, "
          f"{g['panel_w_watt']} Вт{est}")
    print(f"Кут нахилу:       {g['tilt_deg']}°")
    print(f"Підйом (задня):   {g['rise_mm']:.1f} мм")
    print(f"Проекція (земля): {g['ground_proj_mm']:.1f} мм")
    print(f"Ширина рами:      {g['frame_width_mm']:.0f} мм")
    print(f"Передня стійка:   {g['post_front_mm']:.0f} мм")
    print(f"Задня стійка:     {g['post_rear_mm']:.1f} мм")
    print(f"База поздовжня:   {g['base_long_mm']:.1f} мм × 2")
    print(f"База поперечина:  {g['base_cross_mm']:.1f} мм × 2")
    print(f"Рейка (похила):   {g['rail_len_mm']:.0f} мм × 2")
    print(f"Верхня поперечина:{g['top_cross_mm']:.1f} мм × 2")
    print(f"Укосина:          {g['brace_mm']:.0f} мм × 4 (різати по місцю)")

    print()
    print("=" * 62)
    print("РОЗКРІЙ")
    print("=" * 62)
    print(f"Дошка 2×4 Douglas Fir: {cp['board_len_mm']} мм (8 ft)")
    for b in cp["boards"]:
        pieces_str = ", ".join(
            f"{p['name']} {p['len_mm']:.0f}мм"
            for p in b["pieces"]
        )
        print(f"  #{b['board']}: {pieces_str}  |  залишок {b['leftover_mm']:.0f} мм")
    print(f"РАЗОМ: {cp['n_boards']} дощок")

    print()
    print("=" * 62)
    print("ВІТРОВЕ НАВАНТАЖЕННЯ")
    print("=" * 62)
    print(f"Розрахункова швидкість: {wl['v_mph']:.0f} mph = {wl['v_ms']:.1f} м/с")
    print(f"Швидкісний натиск q:    {wl['q_pa']:.1f} Па")
    print(f"Площа панелі:           {wl['area_m2']:.3f} м²")
    print(f"Cd (нахилена плита):    {wl['cd']}")
    print(f"Сила на раму:           {wl['force_n']:.0f} Н = {wl['force_kg']:.1f} кгс")
    print(f"На 1 анкер (з {wl['n_anchors']}):      {wl['per_anchor_n']:.0f} Н ≈ "
          f"{wl['per_anchor_kg']:.1f} кгс — ось навіщо такелаж")

    print()
    print("=" * 62)
    print("SVG")
    print("=" * 62)
    svg_text, W, H = generate_svg()
    out_path = Path(__file__).resolve().parent / "frame.svg"
    out_path.write_text(svg_text)
    print(f"Записано: {out_path}")
    print(f"Розмір полотна: {W} × {H:.0f} px (viewBox)")

    # Перевірка
    ok, errs, n_labels = _check_svg_labels(svg_text, W, H)
    print(f"Підписів: {n_labels}")
    if ok:
        print("Перевірка viewBox: всі підписи в межах ✓")
    else:
        print("⚠ Підписи поза viewBox:")
        for e in errs:
            print(f"  {e}")


if __name__ == "__main__":
    main()
