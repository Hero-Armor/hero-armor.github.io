#!/usr/bin/env python3
"""Як фігура лежить у машині — схема завантаження.

Питання просте і дороге: у що вона взагалі влазить. Іван 14.08.2026 задав габарит
перевезення 4×4×8 футів (48×48×96 дюймів) — це не сама фігура, а коробка, яку вона
займає РАЗОМ із рамою, на якій лежить.

Як їде (зі слів Івана, 14.08):
  · фігура лежить ЛИЦЕМ ВНИЗ — так найкраще захищені лице, груди й ядро на спині
    дивиться вгору, тобто нічим не притиснуте;
  · у плечі вставляється поперечна ТРУБА;
  · від труби вперед, під 90°, стирчить каркас — він тримає фігуру від перекочування
    і не дає лягти обличчям на підлогу;
  · від тієї ж труби вниз ідуть ДВІ РЕЙКИ до металевого багатокутника основи;
  · з боків лишається запас — фігура вужча за 48 дюймів.

Схема малює три види в одному масштабі: збоку (як лежить), зверху (як стоїть у
кузові) і з торця (чому не перекочується). Поруч — три машини в тому ж масштабі,
щоб було видно, що влазить, а що ні.

Числа беруться з бази, а не з голови:
  · габарит перевезення — transport.json (слова Івана);
  · зріст фігури і подіум — lights/data/back_core.json і креслення Rev 2.1;
  · салони машин — transport.json (звірено по специфікаціях 14.08).

  python3 project/model/transport_load.py   →  transport_load.svg
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DATA = json.loads((ROOT / "project/data/transport.json").read_text(encoding="utf-8"))

BOX = DATA["box_in"]            # {"l":96,"w":48,"h":48}
VANS = DATA["vans"]
FIG = DATA["figure"]

SCALE = 5.4                     # пікселів на дюйм
PAD = 40
INK = "#e8edf7"
DIM = "#7f8aa3"
ACC = "#4da3ff"
WARN = "#ffb648"
BG = "#0e1420"


def px(inch):
    return inch * SCALE


def txt(x, y, s, size=12, fill=INK, anchor="start", weight="400"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="Inter,system-ui,sans-serif" '
            f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


def dim_line(x1, y1, x2, y2, label):
    """Розмірна лінія зі стрілками і підписом посередині."""
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    out = [f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
           f'stroke="{DIM}" stroke-width="1" marker-start="url(#a)" marker-end="url(#a)"/>']
    dy = -6 if abs(y1 - y2) < 1 else 4
    out.append(txt(mx, my + dy, label, 11, DIM, "middle"))
    return "\n".join(out)


def side_view(ox, oy):
    """Вигляд збоку: фігура лицем вниз, труба в плечах, каркас під 90° вперед, дві рейки вниз."""
    L, H = px(BOX["l"]), px(BOX["h"])
    o = [f'<rect x="{ox}" y="{oy}" width="{L:.1f}" height="{H:.1f}" fill="none" '
         f'stroke="{DIM}" stroke-width="1" stroke-dasharray="6 4"/>',
         txt(ox, oy - 14, "Збоку — як лежить у кузові", 13, INK, "start", "600")]

    floor = oy + H
    o.append(f'<line x1="{ox}" y1="{floor:.1f}" x2="{ox+L:.1f}" y2="{floor:.1f}" stroke="{DIM}" stroke-width="2"/>')

    # тіло: голова ліворуч, ноги праворуч; лежить на висоті рами
    lift = px(10)
    yb = floor - lift
    x0 = ox + px(5)
    body = px(FIG["height_in"])
    o.append(f'<path d="M{x0:.1f} {yb:.1f} q {px(5):.1f} {-px(8):.1f} {px(11):.1f} 0 '
             f'l {px(9):.1f} 0 q {px(7):.1f} {-px(4):.1f} {px(15):.1f} 0 '
             f'l {body-px(48):.1f} 0 q {px(7):.1f} {px(1):.1f} {px(13):.1f} {px(2):.1f} '
             f'l 0 {px(8):.1f} l {-body+px(5):.1f} 0 z" '
             f'fill="#1b2740" stroke="{ACC}" stroke-width="1.6"/>')
    o.append(txt(x0 + px(2), yb - px(11), "фігура лежить ЛИЦЕМ ВНИЗ", 11, ACC))

    # труба в плечах — у профіль це кружок
    xs = x0 + px(24)
    ys = yb - px(2)
    o.append(f'<circle cx="{xs:.1f}" cy="{ys:.1f}" r="5.5" fill="{WARN}"/>')
    o.append(txt(xs + 10, ys - px(4), "труба в плечах", 11, WARN))

    # каркас під 90° ВПЕРЕД від плечей: у положенні «лицем вниз» це вниз, до підлоги.
    # він і не дає фігурі лягти обличчям і тримає її від перекочування.
    o.append(f'<line x1="{xs:.1f}" y1="{ys:.1f}" x2="{xs:.1f}" y2="{floor:.1f}" '
             f'stroke="{WARN}" stroke-width="3.2"/>')
    o.append(f'<path d="M{xs+4:.1f} {floor-16:.1f} l 12 0 l 0 12" fill="none" stroke="{WARN}" stroke-width="1"/>')
    o.append(txt(xs - 8, floor + 14, "каркас під 90° вперед", 11, WARN, "middle"))

    # дві рейки від тієї ж труби вниз до металевого багатокутника
    for dx in (px(8), px(18)):
        o.append(f'<line x1="{xs:.1f}" y1="{ys:.1f}" x2="{xs+dx:.1f}" y2="{floor-px(4):.1f}" '
                 f'stroke="{WARN}" stroke-width="2.2" stroke-dasharray="7 3"/>')
    o.append(txt(xs + px(21), ys + px(4), "дві рейки вниз", 11, WARN))

    # металевий багатокутник основи
    o.append(f'<rect x="{xs-px(2):.1f}" y="{floor-px(4):.1f}" width="{px(26):.1f}" height="{px(4):.1f}" '
             f'fill="#243350" stroke="{WARN}" stroke-width="1.4"/>')
    o.append(txt(xs + px(28), floor - px(1.2), "металевий багатокутник основи", 11, DIM))

    o.append(dim_line(ox, floor + 44, ox + L, floor + 44, f'{BOX["l"]}" ({BOX["l"]//12} фути)'))
    o.append(dim_line(ox - 24, oy, ox - 24, floor, f'{BOX["h"]}"'))
    return "\n".join(o), L, H


def top_view(ox, oy):
    """Вигляд зверху: скільки лишається з боків."""
    L, W = px(BOX["l"]), px(BOX["w"])
    o = [f'<rect x="{ox}" y="{oy}" width="{L:.1f}" height="{W:.1f}" fill="none" '
         f'stroke="{DIM}" stroke-width="1" stroke-dasharray="6 4"/>',
         txt(ox, oy - 12, "Зверху — запас з боків", 13, INK, "start", "600")]
    fw = px(FIG["shoulders_in"])
    y = oy + (W - fw) / 2
    o.append(f'<rect x="{ox+px(4):.1f}" y="{y:.1f}" width="{px(FIG["height_in"]):.1f}" height="{fw:.1f}" '
             f'rx="{px(5):.1f}" fill="#1b2740" stroke="{ACC}" stroke-width="1.6"/>')
    o.append(txt(ox + px(10), y + fw / 2 + 4, f'фігура: плечі {FIG["shoulders_in"]}"', 11, ACC))
    gap = (BOX["w"] - FIG["shoulders_in"]) / 2
    o.append(dim_line(ox + px(6), oy, ox + px(6), y, f'{gap:.0f}"'))
    o.append(dim_line(ox + px(6), y + fw, ox + px(6), oy + W, f'{gap:.0f}"'))
    o.append(dim_line(ox, oy + W + 26, ox + L, oy + W + 26, f'{BOX["w"]}" завширшки'))
    return "\n".join(o), L, W


def vans_block(ox, oy, width):
    """Машини в тому ж масштабі: що влазить, а що ні."""
    o = [txt(ox, oy - 12, "Що влазить — вантажний обʼєм у тому ж масштабі", 13, INK, "start", "600")]
    y = oy
    for v in VANS:
        fits = v["len_in"] >= BOX["l"] and v["w_in"] >= BOX["w"] and v["h_in"] >= BOX["h"]
        col = "#59d98e" if fits else "#ff6b6b"
        w = px(min(v["len_in"], 126))
        h = 26
        o.append(f'<rect x="{ox}" y="{y}" width="{w:.1f}" height="{h}" rx="4" '
                 f'fill="none" stroke="{col}" stroke-width="1.6"/>')
        # наш ящик поверх — видно, чи вилазить
        o.append(f'<rect x="{ox}" y="{y+5}" width="{px(BOX["l"]):.1f}" height="{h-10}" '
                 f'fill="{ACC}" fill-opacity="0.18" stroke="{ACC}" stroke-width="1" stroke-dasharray="4 3"/>')
        o.append(txt(ox + w + 12, y + 17,
                     f'{v["name"]} — {v["len_in"]}" × {v["w_in"]}" × {v["h_in"]}"'
                     f'{"" if fits else "  ✗ " + v.get("why", "")}', 12, col))
        y += h + 12
    o.append(txt(ox, y + 6, f'синім пунктиром — наш габарит {BOX["l"]}×{BOX["w"]}×{BOX["h"]}"', 11, DIM))
    return "\n".join(o), y + 18 - oy


def build() -> str:
    w = int(px(BOX["l"]) + PAD * 2 + 430)
    parts = []
    y = PAD + 24
    s, _, hs = side_view(PAD + 30, y)
    parts.append(s)
    y += hs + 92
    t, _, ht = top_view(PAD + 30, y)
    parts.append(t)
    y += ht + 78
    v, hv = vans_block(PAD + 30, y, w)
    parts.append(v)
    y += hv + 30
    parts.append(txt(PAD, y, DATA["note"], 11, DIM))
    h = int(y + 30)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
            f'<defs><marker id="a" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">'
            f'<path d="M1,1 L7,4 L1,7" fill="none" stroke="{DIM}" stroke-width="1"/></marker></defs>\n'
            f'<rect width="{w}" height="{h}" fill="{BG}"/>\n' + "\n".join(parts) + "\n</svg>\n")


if __name__ == "__main__":
    out = HERE / "transport_load.svg"
    out.write_text(build(), encoding="utf-8")
    print(f"готово: {out}")
