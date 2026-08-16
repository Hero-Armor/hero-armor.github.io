#!/usr/bin/env python3
"""Що і де міряти на готовій фігурі — схема для рулетки.

Навіщо. 15.08.2026 зʼясувалось, що весь транспорт стоїть на одному невідомому числі.
За кресленням «METAL FRAME» Rev 3.1 каркас на рівні кистей має 47.7″, вантажний отвір
Pacifica — 49″. Різниця 1.3″, і вона цілком у товщині надрукованої обшивки, якої на
кресленні нема. Тому міряти треба ГОТОВУ фігуру, а не каркас.

Схема малює два види з винесеними розмірами і підписами «звідки й куди тягнути стрічку».
Числа з креслення стоять поруч сірим — щоб одразу було видно, збігається чи ні.

Підписи виводяться текстом (не криві), щоб їх підхопив шар перекладу хаба.

  python3 project/model/measure_guide.py  →  measure_guide.svg
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Числа з креслення (аркуш 6, Front/Right Elevation) — очікуване, для звірки
DWG = {"hands": 47.7, "tube": 60.2, "depth": 8.6, "height": 79.0,
       "legs": 31.5, "base": 27.2, "shoulders": 21.26}
OPENING = 49.0          # вантажний отвір Pacifica зі схеми В. Кормільця

S = 5.6                 # пікселів на дюйм
INK, DIM, GREY = "#1b1b1b", "#555", "#9a9a9a"
RED, BLUE, GREEN = "#d81f1f", "#1f4fd8", "#0b8a3e"


def px(v):
    return v * S


def t(x, y, s, size=12, fill=INK, anchor="start", weight="400"):
    s = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial,Helvetica,sans-serif" '
            f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


def dim_h(x1, x2, y, label, sub="", color=RED):
    o = [f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" stroke="{color}" '
         f'stroke-width="1.6" marker-start="url(#a)" marker-end="url(#a)"/>']
    for x in (x1, x2):
        o.append(f'<line x1="{x:.1f}" y1="{y-7:.1f}" x2="{x:.1f}" y2="{y+7:.1f}" '
                 f'stroke="{color}" stroke-width="1.2"/>')
    o.append(t((x1 + x2) / 2, y - 8, label, 13, color, "middle", "700"))
    if sub:
        o.append(t((x1 + x2) / 2, y + 18, sub, 11, GREY, "middle"))
    return "\n".join(o)


def dim_v(x, y1, y2, label, sub="", color=RED):
    o = [f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" stroke="{color}" '
         f'stroke-width="1.6" marker-start="url(#a)" marker-end="url(#a)"/>']
    for y in (y1, y2):
        o.append(f'<line x1="{x-7:.1f}" y1="{y:.1f}" x2="{x+7:.1f}" y2="{y:.1f}" '
                 f'stroke="{color}" stroke-width="1.2"/>')
    o.append(t(x + 9, (y1 + y2) / 2, label, 13, color, "start", "700"))
    if sub:
        o.append(t(x + 9, (y1 + y2) / 2 + 15, sub, 11, GREY))
    return "\n".join(o)


def figure_front(ox, oy):
    """Спрощений силует спереду: голова, тулуб, руки вниз-назовні, ноги, база."""
    cx = ox + px(DWG["hands"]) / 2
    o = []
    top = oy
    head_r = px(4.5)
    o.append(f'<circle cx="{cx:.1f}" cy="{top+head_r:.1f}" r="{head_r:.1f}" '
             f'fill="none" stroke="{BLUE}" stroke-width="2"/>')
    sh_y = top + head_r * 2 + px(2)
    sh_w = px(DWG["shoulders"])
    hip_y = sh_y + px(26)
    o.append(f'<path d="M{cx-sh_w/2:.1f} {sh_y:.1f} L{cx+sh_w/2:.1f} {sh_y:.1f} '
             f'L{cx+sh_w/2*0.8:.1f} {hip_y:.1f} L{cx-sh_w/2*0.8:.1f} {hip_y:.1f} Z" '
             f'fill="none" stroke="{BLUE}" stroke-width="2"/>')
    # руки вниз і назовні, кисті — найширше місце фігури
    hand_y = sh_y + px(30)
    for sgn in (-1, 1):
        hx = cx + sgn * px(DWG["hands"]) / 2
        o.append(f'<path d="M{cx+sgn*sh_w/2:.1f} {sh_y+px(1):.1f} L{hx:.1f} {hand_y:.1f}" '
                 f'stroke="{BLUE}" stroke-width="6" fill="none" stroke-linecap="round"/>')
        o.append(f'<circle cx="{hx:.1f}" cy="{hand_y:.1f}" r="{px(1.6):.1f}" fill="{BLUE}"/>')
    # поперечна труба в плечах — виступає за кисті
    ty = sh_y + px(1)
    o.append(f'<rect x="{cx-px(DWG["tube"])/2:.1f}" y="{ty-px(1.1):.1f}" '
             f'width="{px(DWG["tube"]):.1f}" height="{px(2.2):.1f}" '
             f'fill="none" stroke="{GREEN}" stroke-width="2"/>')
    o.append(t(cx - px(DWG["tube"]) / 2 - 6, ty + 4, "труба", 11, GREEN, "end"))
    # ноги і база
    foot_y = top + px(DWG["height"])
    for sgn in (-1, 1):
        lx = cx + sgn * px(DWG["legs"]) / 2 * 0.55
        o.append(f'<line x1="{cx+sgn*sh_w/2*0.5:.1f}" y1="{hip_y:.1f}" x2="{lx:.1f}" y2="{foot_y:.1f}" '
                 f'stroke="{BLUE}" stroke-width="7" stroke-linecap="round"/>')
    o.append(f'<rect x="{cx-px(DWG["base"])/2:.1f}" y="{foot_y:.1f}" width="{px(DWG["base"]):.1f}" '
             f'height="{px(1.6):.1f}" fill="{BLUE}" fill-opacity="0.25" stroke="{BLUE}" stroke-width="1.6"/>')
    return "\n".join(o), cx, top, sh_y, hand_y, foot_y


def figure_side(ox, oy):
    """Вид збоку: глибина — друге невідоме після ширини."""
    o = []
    top = oy
    d = px(DWG["depth"] + 4)          # каркас 8.6″ + обшивка спереду і ззаду
    head_r = px(4.5)
    cx = ox + d / 2
    o.append(f'<circle cx="{cx:.1f}" cy="{top+head_r:.1f}" r="{head_r:.1f}" '
             f'fill="none" stroke="{BLUE}" stroke-width="2"/>')
    sh_y = top + head_r * 2 + px(2)
    hip_y = sh_y + px(26)
    foot_y = top + px(DWG["height"])
    o.append(f'<path d="M{ox:.1f} {sh_y:.1f} L{ox+d:.1f} {sh_y:.1f} L{ox+d*0.85:.1f} {hip_y:.1f} '
             f'L{ox+d*0.15:.1f} {hip_y:.1f} Z" fill="none" stroke="{BLUE}" stroke-width="2"/>')
    # ядро на спині — саме воно може виявитись найглибшою точкою
    o.append(f'<rect x="{ox+d:.1f}" y="{sh_y+px(4):.1f}" width="{px(4):.1f}" height="{px(9):.1f}" '
             f'fill="{GREEN}" fill-opacity="0.18" stroke="{GREEN}" stroke-width="1.6"/>')
    o.append(t(ox + d + px(5), sh_y + px(9), "ядро на спині", 11, GREEN))
    o.append(f'<line x1="{cx:.1f}" y1="{hip_y:.1f}" x2="{cx:.1f}" y2="{foot_y:.1f}" '
             f'stroke="{BLUE}" stroke-width="7" stroke-linecap="round"/>')
    o.append(f'<rect x="{ox:.1f}" y="{foot_y:.1f}" width="{d:.1f}" height="{px(1.6):.1f}" '
             f'fill="{BLUE}" fill-opacity="0.25" stroke="{BLUE}" stroke-width="1.6"/>')
    return "\n".join(o), ox, d, top, sh_y, foot_y


def build() -> str:
    W, H = 1180, 1010
    o = [t(40, 38, "Що міряти на ГОТОВІЙ фігурі", 20, INK, "start", "700"),
         t(40, 60, "Рулетку тягнути по зібраній фігурі з обшивкою, а не по каркасу. "
                   "Сірим — що дає креслення; якщо збіглось, добре.", 12, DIM)]

    front, cx, top, sh_y, hand_y, foot_y = figure_front(150, 200)
    o.append(front)

    # M1 — головний розмір
    o.append(dim_h(cx - px(DWG["hands"]) / 2, cx + px(DWG["hands"]) / 2, hand_y + px(6),
                   "M1 · від кисті до кисті — головне число",
                   f'креслення {DWG["hands"]}″'))
    # M2 — труба
    o.append(dim_h(cx - px(DWG["tube"]) / 2, cx + px(DWG["tube"]) / 2, top - 34,
                   "M2 · труба в плечах, повна довжина", f'креслення {DWG["tube"]}″', GREEN))
    # M4 — висота
    o.append(dim_v(cx + px(DWG["tube"]) / 2 + 46, top, foot_y, "M4 · висота",
                   f'креслення {DWG["height"]}″'))
    # M5 — база, M6 — ноги
    o.append(dim_h(cx - px(DWG["legs"]) / 2 * 0.55 - px(2), cx + px(DWG["legs"]) / 2 * 0.55 + px(2),
                   foot_y - px(6), "M6 · розмах стоп", f'креслення {DWG["legs"]}″', GREEN))
    o.append(dim_h(cx - px(DWG["base"]) / 2, cx + px(DWG["base"]) / 2, foot_y + px(9),
                   "M5 · діаметр бази", f'креслення {DWG["base"]}″'))

    # межа мінівена
    xl, xr = cx - px(OPENING) / 2, cx + px(OPENING) / 2
    for x in (xl, xr):
        o.append(f'<line x1="{x:.1f}" y1="{top-58:.1f}" x2="{x:.1f}" y2="{foot_y+px(12):.1f}" '
                 f'stroke="{RED}" stroke-width="1.4" stroke-dasharray="8 5"/>')
    o.append(t(cx, top - 66, f'вантажний отвір мінівена {OPENING:.0f}″ — фігура має пройти між цими лініями',
               12, RED, "middle", "700"))

    side, sx, sd, stop, ssh, sfoot = figure_side(880, 200)
    o.append(side)
    o.append(t(880, 182, "вид збоку", 13, DIM, "start", "700"))
    o.append(dim_h(sx, sx + sd + px(4), ssh + px(22),
                   "M3 · глибина", f'каркас {DWG["depth"]}″ + обшивка'))

    y0 = foot_y + px(26)
    o.append(t(40, y0, "Як міряти", 15, INK, "start", "700"))
    rows = [
        ("M1", "від кисті до кисті", "Найширше місце фігури. Стрічку натягнути по прямій між "
                                     "крайніми точками кистей, не по дузі рук."),
        ("M2", "труба в плечах", "Повна довжина, від торця до торця. Заодно — на скільки вона "
                                 "виступає за кисті: це те, що можна відрізати."),
        ("M3", "глибина", "У найтовщому місці, від грудей до найдальшої точки ЗЗАДУ. "
                          "Ядро на спині рахується — воно й може бути тією точкою."),
        ("M4", "висота", "Від низу бази до маківки, фігура стоїть."),
        ("M5", "діаметр бази", "Диск під ногами, по крайніх точках."),
        ("M6", "розмах ніг унизу", "По зовнішніх краях стоп."),
    ]
    for i, (k, name, how) in enumerate(rows):
        y = y0 + 22 + i * 19
        o.append(t(40, y, k, 12, RED, "start", "700"))
        o.append(t(72, y, name, 12, INK, "start", "600"))
        o.append(t(230, y, how, 11.5, DIM))

    o.append(t(40, y0 + 22 + len(rows) * 19 + 18,
               "Головне: якщо M1 з обшивкою вийде більше 49″ — мінівен відпадає і веземо причепом. "
               "Менше — заходить, але без ящика, у ковдрах.", 12, INK, "start", "600"))

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
            f'<defs><marker id="a" markerWidth="9" markerHeight="9" refX="4.5" refY="4.5" orient="auto">'
            f'<path d="M1,1 L8,4.5 L1,8" fill="none" stroke="{RED}" stroke-width="1.2"/></marker></defs>\n'
            f'<rect width="{W}" height="{H}" fill="#ffffff"/>\n' + "\n".join(o) + "\n</svg>\n")


if __name__ == "__main__":
    out = HERE / "measure_guide.svg"
    out.write_text(build(), encoding="utf-8")
    print(f"готово: {out}")
