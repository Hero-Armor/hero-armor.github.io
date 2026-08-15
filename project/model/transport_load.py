#!/usr/bin/env python3
"""Як фігура і подіум лежать у машині — схема завантаження в масштабі.

Питання, на які відповідає схема, коштують грошей і нервів на стоянці прокату:
  1. у що взагалі влазить фігура 96×48×48″;
  2. скільки лишається вільного місця поруч — біля стегон, уздовж ніг, зверху;
  3. чи їде разом із нею подіум і чи треба розбирати його на всі чотири частини.

Як їде (зі слів Івана, 14.08.2026):
  · фігура лежить ЛИЦЕМ ВНИЗ — лице і груди захищені, ядро на спині дивиться вгору;
  · у плечі вставлена поперечна труба;
  · від труби під 90° вперед (у цьому положенні — вниз, до підлоги) стирчить каркас:
    він тримає вагу і не дає лягти обличчям;
  · від тієї ж труби дві рейки йдуть униз до металевого багатокутника основи.

Що показує кожен вид:
  · ЗБОКУ — висота стосу: половина подіуму на підлозі, фігура на рамі над нею;
  · ЗВЕРХУ — план кузова: силует із головою, плечима, руками й ногами, і вільні
    кишені обабіч ніг із розмірами;
  · ПОДІУМ — половинами чи чвертями, як воно лягає;
  · МАШИНИ — вантажні обʼєми в тому ж масштабі: зелені влазять, червоні ні.

Числа — тільки з `project/data/transport.json`. Розмах рук і просвіт між ногами
прийшли туди з креслення Rev 3.1 через `lights/data/podium_plan.json`; що виміряно
на око — так і підписано в самому json.

  python3 project/model/transport_load.py   →  transport_load.svg
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DATA = json.loads((ROOT / "project/data/transport.json").read_text(encoding="utf-8"))

BOX, FIG, POD, VANS = DATA["box_in"], DATA["figure"], DATA["podium"], DATA["vans"]

S = 6.0                     # пікселів на дюйм
PAD = 46
INK, DIM, ACC = "#e8edf7", "#7f8aa3", "#4da3ff"
WARN, OK, BAD, FREE = "#ffb648", "#59d98e", "#ff6b6b", "#2ecc71"
BG, PANEL = "#0e1420", "#16203a"


def px(v):
    return v * S


def t(x, y, s, size=12, fill=INK, anchor="start", weight="400"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="Inter,system-ui,sans-serif" '
            f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


def dim(x1, y1, x2, y2, label):
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    vertical = abs(x1 - x2) < 1
    lab = t(mx + (10 if vertical else 0), my + (4 if vertical else -6), label, 11, DIM,
            "start" if vertical else "middle")
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{DIM}" '
            f'stroke-width="1" marker-start="url(#a)" marker-end="url(#a)"/>\n' + lab)


def figure_top(x, y, length_px):
    """Силует зверху: голова, плечі, руки вздовж тіла, таз, дві ноги."""
    sh, hip = px(FIG["shoulders_in"]), px(FIG["hips_in"])
    gap = px(FIG["leg_gap_in"])
    cy = y + sh / 2
    head_r = px(5.5)
    body_len = length_px * 0.46
    x0 = x + head_r * 1.6
    o = [f'<circle cx="{x+head_r:.1f}" cy="{cy:.1f}" r="{head_r:.1f}" fill="{PANEL}" '
         f'stroke="{ACC}" stroke-width="1.6"/>',
         f'<path d="M{x0:.1f} {cy-sh/2:.1f} L{x0+body_len:.1f} {cy-hip/2:.1f} '
         f'L{x0+body_len:.1f} {cy+hip/2:.1f} L{x0:.1f} {cy+sh/2:.1f} Z" '
         f'fill="{PANEL}" stroke="{ACC}" stroke-width="1.6"/>']
    arm_w = px(4.5)
    for sgn in (-1, 1):
        ay = cy + sgn * (sh / 2 - arm_w / 2)
        o.append(f'<rect x="{x0+px(2):.1f}" y="{ay-arm_w/2:.1f}" width="{body_len*0.9:.1f}" '
                 f'height="{arm_w:.1f}" rx="{arm_w/2:.1f}" fill="#1b2740" stroke="{ACC}" stroke-width="1.2"/>')
    leg_w = (hip - gap * 0.3) / 2
    legs_x = x0 + body_len
    for sgn in (-1, 1):
        ly = cy + sgn * (gap * 0.3 / 2 + leg_w / 2)
        o.append(f'<rect x="{legs_x:.1f}" y="{ly-leg_w/2:.1f}" '
                 f'width="{x+length_px-legs_x:.1f}" height="{leg_w:.1f}" rx="{px(2):.1f}" '
                 f'fill="{PANEL}" stroke="{ACC}" stroke-width="1.6"/>')
    return "\n".join(o), cy, sh, hip, legs_x


def top_view(ox, oy):
    L, W = px(BOX["l"]), px(BOX["w"])
    o = [t(ox, oy - 16, "Зверху — план кузова і що лишається вільним", 14, INK, "start", "600"),
         f'<rect x="{ox}" y="{oy}" width="{L:.1f}" height="{W:.1f}" rx="6" fill="none" '
         f'stroke="{DIM}" stroke-width="1.4" stroke-dasharray="7 5"/>']
    fig_len = px(FIG["height_in"])
    fy = oy + (W - px(FIG["shoulders_in"])) / 2
    fx = ox + px(4)
    body, cy, sh, hip, legs_x = figure_top(fx, fy, fig_len)

    pocket = (BOX["w"] - FIG["hips_in"]) / 2          # вільна смуга обабіч ніг
    for sgn in (-1, 1):
        top = cy + sgn * hip / 2 - (px(pocket) if sgn > 0 else 0)
        o.append(f'<rect x="{legs_x:.1f}" y="{top:.1f}" width="{ox+L-legs_x-px(2):.1f}" '
                 f'height="{px(pocket):.1f}" fill="{FREE}" fill-opacity="0.13" '
                 f'stroke="{FREE}" stroke-width="1" stroke-dasharray="5 4"/>')
    o.append(t(legs_x + px(5), cy - hip / 2 - px(pocket) / 2 + 4,
               f'вільна смуга {pocket:.0f}″ уздовж ніг — з обох боків', 11, FREE))
    o.append(body)
    o.append(t(fx + px(3), fy - 9, "фігура лицем вниз", 11, ACC))
    o.append(dim(ox, oy + W + 32, ox + L, oy + W + 32, f'{BOX["l"]}″ ({BOX["l"]//12} фути)'))
    o.append(dim(ox - 26, oy, ox - 26, oy + W, f'{BOX["w"]}″'))
    o.append(dim(fx + px(26), fy, fx + px(26), fy + sh, f'плечі {FIG["shoulders_in"]}″'))
    o.append(dim(legs_x + px(8), cy - hip / 2, legs_x + px(8), cy + hip / 2, f'стегна {FIG["hips_in"]}″'))
    return "\n".join(o), W


def side_view(ox, oy):
    L, H = px(BOX["l"]), px(BOX["h"])
    o = [t(ox, oy - 16, "Збоку — висота стосу: подіум знизу, фігура зверху", 14, INK, "start", "600"),
         f'<rect x="{ox}" y="{oy}" width="{L:.1f}" height="{H:.1f}" rx="6" fill="none" '
         f'stroke="{DIM}" stroke-width="1.4" stroke-dasharray="7 5"/>']
    floor = oy + H
    o.append(f'<line x1="{ox}" y1="{floor:.1f}" x2="{ox+L:.1f}" y2="{floor:.1f}" stroke="{DIM}" stroke-width="2.5"/>')

    deck = px(POD["deck_thick_in"])
    o.append(f'<rect x="{ox+2:.1f}" y="{floor-deck:.1f}" width="{L-4:.1f}" height="{deck:.1f}" '
             f'fill="#243350" stroke="{OK}" stroke-width="1.6"/>')
    o.append(t(ox + px(5), floor - deck / 2 + 4,
               f'половина подіуму {POD["half_in"][0]}×{POD["half_in"][1]}″ — точно по підлозі', 11, OK))

    lift = deck + px(6)
    yb = floor - lift
    x0 = ox + px(5)
    body = px(FIG["height_in"])
    thick = px(FIG["chest_thick_in"])
    o.append(f'<path d="M{x0:.1f} {yb:.1f} q {px(5):.1f} {-px(7):.1f} {px(11):.1f} 0 '
             f'l {px(8):.1f} 0 q {px(6):.1f} {-px(3.5):.1f} {px(14):.1f} 0 '
             f'l {body-px(46):.1f} 0 q {px(6):.1f} {px(1):.1f} {px(12):.1f} {px(2):.1f} '
             f'l 0 {thick*0.55:.1f} l {-body+px(4):.1f} 0 z" '
             f'fill="{PANEL}" stroke="{ACC}" stroke-width="1.8"/>')
    o.append(t(x0 + px(2), yb - px(9), "фігура лицем вниз", 11, ACC))

    xs, ys = x0 + px(23), yb - px(1.5)
    o.append(f'<circle cx="{xs:.1f}" cy="{ys:.1f}" r="6" fill="{WARN}"/>')
    o.append(t(xs + 11, ys - px(3.5), "труба в плечах", 11, WARN))
    o.append(f'<line x1="{xs:.1f}" y1="{ys:.1f}" x2="{xs:.1f}" y2="{floor-deck:.1f}" stroke="{WARN}" stroke-width="3.4"/>')
    o.append(f'<path d="M{xs+5:.1f} {floor-deck-15:.1f} l 11 0 l 0 11" fill="none" stroke="{WARN}" stroke-width="1"/>')
    o.append(t(xs - px(1), floor - deck + 17, "каркас під 90°", 11, WARN, "middle"))
    for dx in (px(9), px(19)):
        o.append(f'<line x1="{xs:.1f}" y1="{ys:.1f}" x2="{xs+dx:.1f}" y2="{floor-deck:.1f}" '
                 f'stroke="{WARN}" stroke-width="2.2" stroke-dasharray="7 3"/>')
    o.append(t(xs + px(21), ys + px(3), "дві рейки вниз", 11, WARN))

    top_free = BOX["h"] - POD["deck_thick_in"] - 6 - FIG["chest_thick_in"] * 0.55
    o.append(f'<rect x="{ox+2:.1f}" y="{oy+2:.1f}" width="{L-4:.1f}" height="{px(top_free):.1f}" '
             f'fill="{FREE}" fill-opacity="0.10" stroke="{FREE}" stroke-width="1" stroke-dasharray="5 4"/>')
    o.append(t(ox + px(5), oy + px(top_free) / 2 + 4,
               f'вільно зверху ≈{top_free:.0f}″ — ящики, кабелі, каркас', 11, FREE))
    o.append(dim(ox, floor + 46, ox + L, floor + 46, f'{BOX["l"]}″'))
    o.append(dim(ox - 26, oy, ox - 26, floor, f'{BOX["h"]}″'))
    return "\n".join(o), H


def podium_options(ox, oy):
    o = [t(ox, oy - 16, "Подіум: як розбирати", 14, INK, "start", "600")]
    y = oy
    hl, hw = POD["half_in"]
    o.append(f'<rect x="{ox}" y="{y}" width="{px(hl):.1f}" height="{px(hw)/2:.1f}" '
             f'fill="{OK}" fill-opacity="0.15" stroke="{OK}" stroke-width="1.6"/>')
    o.append(t(ox + px(3), y + px(hw) / 4 + 4,
               f'ДВІ половини {hl}×{hw}″ — лягають плазом, одна на одну', 12, OK))
    y += px(hw) / 2 + 18
    q = hw
    for i in range(POD["parts"]):
        qx = ox + i * (px(q) / 2 + 10)
        o.append(f'<rect x="{qx:.1f}" y="{y}" width="{px(q)/2:.1f}" height="{px(q)/2:.1f}" '
                 f'fill="{ACC}" fill-opacity="0.12" stroke="{ACC}" stroke-width="1.4"/>')
        o.append(t(qx + px(q) / 4, y + px(q) / 4 + 5, POD["part_labels"][i], 12, ACC, "middle"))
    o.append(t(ox + POD["parts"] * (px(q) / 2 + 10) + 10, y + px(q) / 4 + 5,
               f'або ЧОТИРИ чверті {q}×{q}″ — як у кресленні, на болтах M10', 12, ACC))
    y += px(q) / 2 + 16
    o.append(t(ox, y + 12, f'Настил {POD["deck_thick_in"]}″: дві половини одна на одній — '
                           f'{POD["deck_thick_in"]*2}″ висоти, і над ними ще лишається місце для фігури.', 11, DIM))
    return "\n".join(o), y + 26 - oy


def vans_block(ox, oy):
    o = [t(ox, oy - 16, "Машини в тому ж масштабі — що влазить", 14, INK, "start", "600")]
    y = oy
    for v in VANS:
        fits = v["len_in"] >= BOX["l"] and v["w_in"] >= BOX["w"] and v["h_in"] >= BOX["h"]
        col = OK if fits else BAD
        w, h = px(v["len_in"]), 24
        o.append(f'<rect x="{ox}" y="{y}" width="{w:.1f}" height="{h}" rx="4" fill="none" '
                 f'stroke="{col}" stroke-width="1.6"/>')
        o.append(f'<rect x="{ox}" y="{y+4}" width="{px(BOX["l"]):.1f}" height="{h-8}" '
                 f'fill="{ACC}" fill-opacity="0.16" stroke="{ACC}" stroke-width="1" stroke-dasharray="4 3"/>')
        label = (f'{v["name"]} · {v["len_in"]}×{v["w_in"]}×{v["h_in"]}″'
                 + ("" if fits else f'  ✗ {v.get("why", "")}'))
        o.append(t(ox + max(w, px(BOX["l"])) + 14, y + 16, label, 12, col))
        y += h + 10
    o.append(t(ox, y + 12, f'синім пунктиром — наш габарит {BOX["l"]}×{BOX["w"]}×{BOX["h"]}″', 11, DIM))
    return "\n".join(o), y + 26 - oy


def build() -> str:
    w = int(px(BOX["l"]) + PAD * 2 + 480)
    parts, y = [], PAD + 26
    for fn, gap in ((side_view, 104), (top_view, 104), (podium_options, 48), (vans_block, 26)):
        chunk, hh = fn(PAD + 34, y)
        parts.append(chunk)
        y += hh + gap
    parts.append(t(PAD, y, DATA["note"], 11, DIM))
    h = int(y + 34)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
            f'<defs><marker id="a" markerWidth="9" markerHeight="9" refX="4.5" refY="4.5" orient="auto">'
            f'<path d="M1,1 L8,4.5 L1,8" fill="none" stroke="{DIM}" stroke-width="1"/></marker></defs>\n'
            f'<rect width="{w}" height="{h}" fill="{BG}"/>\n' + "\n".join(parts) + "\n</svg>\n")


if __name__ == "__main__":
    out = HERE / "transport_load.svg"
    out.write_text(build(), encoding="utf-8")
    print(f"готово: {out}")
