#!/usr/bin/env python3
"""
Пасивна помітність: чому мікропризма повертає промінь у фару, а фарба — ні.

Схема відповідає на питання, яке виникає щоразу, коли мова заходить про
катафоти: «навіщо нам активне світло, якщо можна обклеїти все відбивачкою?»

Дві частини, і разом вони і є відповідь.

Верхня — фізика. Три однакові шматки поверхні, на кожен під одним і тим самим
кутом падає промінь фари, і видно, куди він дівається далі. Дзеркало відкидає
його вбік — повз того, хто світив. Біла фарба розкидає навсібіч, і назад
вертається дрібка. Мікропризма — це насправді пари дзеркал під прямим кутом:
промінь відбивається двічі й виходить точно назустріч тому, звідки прийшов.
Хід променя в призмі не намальований «на око», а порахований: відрізки
трасуються по зубцях, кожен раз відбиваючись від грані, і те, що на виході
промінь антипаралельний вхідному, — результат розрахунку, а не домовленості.

Нижня — та сама фізика в поле. Вигляд згори: подіум зі стрічкою по торцю і
катафотами на кутах, ящик станції поруч, велосипедист і арт-кар, що
під'їжджають уночі. Під ними лінійка дальності: з якої відстані що читається.
Лінійка логарифмічна (рівні кроки — це множення), бо інакше найближча і
найдальша позначки не влізли б в один рядок. На ній стоїть межа, яку задає
правило Burning Man.

Головне, заради чого схема і малювалась, написано внизу: катафот працює тільки
поки на нього хтось світить. Велосипедист без фари не побачить нічого — тому
пасивний шар не заміняє активного світла, а страхує його.

Жодного числа в цьому файлі нема: дальності, клас плівки, правило Burning Man і
розкладка катафотів — з lights/data/visibility.json, кількість активних вогнів і
відстань до ящика — з lights/data/params.json. У коді лише координати полотна.
Тільки stdlib: CI збирає сайт без залежностей.
"""

import json
import math
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
V = json.loads((DATA / "visibility.json").read_text())
P = json.loads((DATA / "params.json").read_text())

RULE = V["rule"]
SURF = {s["key"]: s for s in V["surfaces"]}
RANGES = V["ranges"]
PASSIVE = V["passive"]
SCENE = V["scene"]

# Активне світло — не дублюємо, беремо з тієї ж бази, звідки його рахує модель.
FIX = {f["id"]: f for f in P["fixtures"]}
STAIRS_N = FIX["stairs"]["qty"]
MARKER_N = FIX["box_marker"]["qty"]
TRUNK_M = next(s for s in P["topology"]["segments"] if s["id"] == "trunk")["length_m"]

# ------------------------------------------------------------------- палітра
INK, DIM, THIN = "#24231d", "#6b675c", "#d8d5c9"
ACC, SIG, GOOD = "#b35b1e", "#3d6f96", "#3d7a4f"
WARN, CRIT = "#b07c14", "#b23a2e"
PAPER, GLASS, GREY = "#efeee7", "#dfe7ee", "#c9c6ba"
WASH = "#f2e9d2"          # бліда підкладка під конус фари

W, H = 960, 718
MARG = 30

# ------------------------------------------------- частина 1: три поверхні
PAN_W, PAN_GAP = 280, 30
SRC = (96, 100)          # фара, у координатах панелі
HIT = (150, 200)         # куди промінь приходить на поверхню
TOP_Y, BOT_Y = 200, 218  # тіло матеріалу
TOOTH_X0, TOOTH_X1 = 34, 250   # зубчаста спинка призми
TOOTH_H = 27                   # глибина зубця = півперіод: грані рівно під 45°
# 250-34 = 216 = 8x27: парне число кроків, тому пилка починається і кінчається
# вершиною, і скраю не лишається горизонтальної полички замість грані
NAME_Y, NOTE_Y = 262, 280

DX, DY = HIT[0] - SRC[0], HIT[1] - SRC[1]
DLEN = math.hypot(DX, DY)
DIR = (DX / DLEN, DY / DLEN)


def _teeth():
    """Зубці на спинці призми: пилка з граней рівно під 45° одна до одної."""
    pts, x, y = [], TOOTH_X1, BOT_Y
    while x > TOOTH_X0 + 1e-9:
        pts.append((x, y))
        x -= TOOTH_H
        y = BOT_Y + TOOTH_H if y == BOT_Y else BOT_Y
    pts.append((TOOTH_X0, BOT_Y))
    return pts


TEETH = _teeth()
SEGS = list(zip(TEETH, TEETH[1:]))


def _hit(pos, d):
    """Найближча грань попереду по променю: точка і нормаль до неї."""
    best = None
    for (x1, y1), (x2, y2) in SEGS:
        ex, ey = x2 - x1, y2 - y1
        den = d[0] * ey - d[1] * ex
        if abs(den) < 1e-9:
            continue
        rx, ry = x1 - pos[0], y1 - pos[1]
        t = (rx * ey - ry * ex) / den
        s = (rx * d[1] - ry * d[0]) / den
        if t > 1e-6 and -1e-9 <= s <= 1 + 1e-9 and (best is None or t < best[0]):
            n = (ey, -ex)
            ln = math.hypot(*n)
            n = (n[0] / ln, n[1] / ln)
            if n[0] * d[0] + n[1] * d[1] > 0:      # нормаль назустріч променю
                n = (-n[0], -n[1])
            best = (t, (pos[0] + t * d[0], pos[1] + t * d[1]), n)
    return best


def prism_path():
    """Хід променя в призмі: вхід, два відбиття, вихід.

    Тут і видно, чому кутовий відбивач працює: після ДВОХ відбиттів від
    граней під прямим кутом напрямок стає рівно протилежним вхідному —
    промінь іде назад тією ж дорогою, якою прийшов."""
    pos, d = HIT, DIR
    pts = [pos]
    for _ in range(2):
        h = _hit(pos, d)
        if h is None:
            break
        _, pos, n = h
        dn = d[0] * n[0] + d[1] * n[1]
        d = (d[0] - 2 * dn * n[0], d[1] - 2 * dn * n[1])
        pts.append(pos)
    t = (TOP_Y - pos[1]) / d[1]                    # вихід крізь лицьову грань
    out = (pos[0] + t * d[0], TOP_Y)
    pts.append(out)
    return pts, d


# ------------------------------------------------- частина 2: сцена і лінійка
XA, XB = 150.0, 920.0                  # ліва і права межі лінійки дальності
D_MIN, D_MAX = SCENE["axis_min_m"], SCENE["axis_max_m"]
KLOG = (XB - XA) / (math.log10(D_MAX) - math.log10(D_MIN))

POD = (82.0, 380.0)
POD_R = 26.0
BOX = (150.0, 380.0)
Y_CAR, Y_BIKE = 340.0, 382.0
BAR_Y = [468.0, 494.0, 520.0, 546.0]
AXIS_Y = 568.0
TICKS_M = SCENE["axis_ticks_m"]


def x_of(m):
    return XA + KLOG * (math.log10(m) - math.log10(D_MIN))


def wrap(s, n):
    """Розбити довгий текст на рядки по n знаків — кожен рядок окремим <text>,
    бо перенесення всередині одного текстового вузла SVG не вміє."""
    out, cur = [], ""
    for word in s.split():
        if cur and len(cur) + 1 + len(word) > n:
            out.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    return out + ([cur] if cur else [])


def t(x, y, s, size=11, fill=DIM, anchor="start", weight=None):
    """Підпис окремим <text>: англійська версія сайту перекладає саме текстові
    вузли, тому нічого не можна віддавати кривими чи картинкою."""
    w = f' font-weight="{weight}"' if weight else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}"'
            f' text-anchor="{anchor}"{w}>{s}</text>')


def line(x1, y1, x2, y2, stroke, width=1.5, dash=None, marker=None, op=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    mk = f' marker-end="url(#{marker})"' if marker else ""
    o = f' opacity="{op}"' if op else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{width}"{d}{mk}{o}/>')


def cone(apex, x_to, half_deg, y_to=None):
    """Конус фари згори: клин від фари в бік обʼєкта."""
    ax, ay = apex
    ty = ay if y_to is None else y_to
    ln = math.hypot(x_to - ax, ty - ay)
    a = math.atan2(ty - ay, x_to - ax)
    h = math.radians(half_deg)
    p1 = (ax + ln * math.cos(a - h), ay + ln * math.sin(a - h))
    p2 = (ax + ln * math.cos(a + h), ay + ln * math.sin(a + h))
    # Заливка — готова бліда підкладка з палітри, а не warn із прозорістю:
    # прозорість деякі рендерери просто ігнорують, і тоді конус стає глухою
    # плямою поверх усього.
    return (f'<path d="M {ax:.1f} {ay:.1f} L {p1[0]:.1f} {p1[1]:.1f} '
            f'L {p2[0]:.1f} {p2[1]:.1f} Z" fill="{WASH}" stroke="{WARN}" '
            f'stroke-width="1.5"/>')


def octagon(cx, cy, r):
    pts = []
    for k in range(8):
        a = -math.pi / 2 + math.pi / 4 * k
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def headlight(x0, o):
    """Фара — джерело променя. Стоїть однаково в усіх трьох панелях, щоб
    різницю давала рівно поверхня, а не картинка."""
    sx, sy = x0 + SRC[0], SRC[1]
    o.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="7" fill="#fff" '
             f'stroke="{INK}" stroke-width="1.6"/>')
    for k in (-26, 0, 26):
        a = math.radians(64 + k)
        o.append(line(sx + 9 * math.cos(a), sy + 9 * math.sin(a),
                      sx + 16 * math.cos(a), sy + 16 * math.sin(a), WARN, 1.5))
    # підпис ліворуч від кружка, а не над ним: над ним іде заголовок частини
    o.append(t(sx - 13, sy + 4, "фара", 11, DIM, "end"))


def slab(x0, o, fill):
    o.append(f'<rect x="{x0+TOOTH_X0:.1f}" y="{TOP_Y}" '
             f'width="{TOOTH_X1-TOOTH_X0}" height="{BOT_Y-TOP_Y}" '
             f'fill="{fill}" stroke="{INK}" stroke-width="1.6"/>')


def panel_mirror(x0, o):
    slab(x0, o, GLASS)
    o.append(line(x0 + TOOTH_X0, TOP_Y, x0 + TOOTH_X1, TOP_Y, SIG, 2.5))
    o.append(line(x0 + SRC[0], SRC[1] + 7, x0 + HIT[0], HIT[1], WARN, 2.5))
    ln = 118
    o.append(line(x0 + HIT[0], HIT[1], x0 + HIT[0] + ln * DIR[0],
                  HIT[1] - ln * DIR[1], DIM, 2.0, marker="nv-arr-dim"))
    o.append(t(x0 + HIT[0] + 62, HIT[1] - 74, "повз фару", 11, DIM))


def panel_paint(x0, o):
    slab(x0, o, "#ffffff")
    # шорсткість поверхні — дрібна пилка по лицю: саме через неї промінь
    # і розсипається, замість того щоб іти в один бік
    rough = " ".join(
        f'{x0+x},{TOP_Y - (3 if (x // 6) % 2 else 0)}'
        for x in range(TOOTH_X0, TOOTH_X1 + 1, 6))
    o.append(f'<polyline points="{rough}" fill="none" stroke="{INK}" '
             f'stroke-width="1.5"/>')
    o.append(line(x0 + SRC[0], SRC[1] + 7, x0 + HIT[0], HIT[1], WARN, 2.5))
    for deg in (195, 215, 270, 295, 320, 345):
        a = math.radians(deg)
        o.append(line(x0 + HIT[0], HIT[1], x0 + HIT[0] + 62 * math.cos(a),
                      HIT[1] + 62 * math.sin(a), GREY, 1.5))
    # промінь, що вернувся у фару, малюємо не поверх вхідного, а поруч із ним:
    # фізично він іде тією ж дорогою, і якщо покласти лінії одна на одну,
    # виходить, ніби фарба працює як призма
    ox, oy = -DIR[1] * 7, DIR[0] * 7
    o.append(line(x0 + HIT[0] + ox, HIT[1] + oy,
                  x0 + HIT[0] + ox - 62 * DIR[0], HIT[1] + oy - 62 * DIR[1],
                  ACC, 2.0, marker="nv-arr-acc"))
    o.append(t(x0 + HIT[0] - 52, HIT[1] - 62, "дрібка", 11, ACC, "end"))


def panel_prism(x0, o):
    pts, _ = prism_path()
    body = ([(x0 + TOOTH_X0, TOP_Y), (x0 + TOOTH_X1, TOP_Y)]
            + [(x0 + x, y) for x, y in TEETH])
    o.append('<path d="M ' + " L ".join(f'{x:.1f} {y:.1f}' for x, y in body)
             + f' Z" fill="{PAPER}" stroke="{INK}" stroke-width="1.6"/>')
    o.append(line(x0 + SRC[0], SRC[1] + 7, x0 + HIT[0], HIT[1], WARN, 2.5))
    o.append(line(x0 + pts[0][0], pts[0][1], x0 + pts[1][0], pts[1][1], WARN, 2.2))
    for a, b in zip(pts[1:], pts[2:]):
        o.append(line(x0 + a[0], a[1], x0 + b[0], b[1], ACC, 2.2))
    out = pts[-1]
    o.append(line(x0 + out[0], out[1], x0 + out[0] - 106 * DIR[0],
                  out[1] - 106 * DIR[1], ACC, 2.5, marker="nv-arr-acc"))
    o.append(t(x0 + out[0] - 56, out[1] - 78, "назад у фару", 11, ACC, "end"))


def part_surfaces(o):
    o.append(t(MARG, 88, "1 · Що поверхня робить з променем фари", 12, INK))
    draw = {"mirror": panel_mirror, "paint": panel_paint, "prism": panel_prism}
    notes = {
        "mirror": ["Кут падіння = куту відбиття: промінь іде",
                   "далі, повз того, хто світив."],
        "paint": ["Розкидає світло навсібіч. Назад іде",
                  "дрібка — тому біле не видно здалеку."],
        "prism": ["Два дзеркала під прямим кутом: промінь",
                  "вертається точно у фару, а не вбік."],
    }
    for i, key in enumerate(("mirror", "paint", "prism")):
        x0 = MARG + i * (PAN_W + PAN_GAP)
        headlight(x0, o)
        draw[key](x0, o)
        s = SURF[key]
        o.append(t(x0 + PAN_W / 2, NAME_Y, s["name"], 12,
                   INK if s["back"] else DIM, "middle",
                   "600" if s["back"] else None))
        for j, ln in enumerate(notes[key]):
            o.append(t(x0, NOTE_Y + j * 14, ln, 11, DIM))


def scene(o):
    """Вигляд згори: обʼєкт, ті, хто до нього під'їжджає, і промені їхніх фар."""
    o.append(cone((686, Y_BIKE), 118, 3.4))
    o.append(cone((860, Y_CAR), 640, 5.0))

    # подіум: стрічка по торцю — це сам восьмикутник, катафоти — на його кутах
    pts = octagon(*POD, POD_R)
    o.append('<polygon points="'
             + " ".join(f'{x:.1f},{y:.1f}' for x, y in pts)
             + f'" fill="#fff" stroke="{ACC}" stroke-width="2.5"/>')
    for x, y in pts:
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="{ACC}"/>')
    o.append(f'<circle cx="{POD[0]:.1f}" cy="{POD[1]:.1f}" r="5" fill="{INK}"/>')

    # ящик станції: та сама стрічка по боках і катафоти на чотирьох кутах
    bx, by = BOX
    o.append(f'<rect x="{bx-13:.1f}" y="{by-9:.1f}" width="26" height="18" '
             f'fill="#fff" stroke="{INK}" stroke-width="1.6"/>')
    o.append(line(bx - 13, by - 9, bx + 13, by - 9, ACC, 2.5))
    o.append(line(bx - 13, by + 9, bx + 13, by + 9, ACC, 2.5))
    for sx in (-13, 13):
        for sy in (-9, 9):
            o.append(f'<circle cx="{bx+sx:.1f}" cy="{by+sy:.1f}" r="2.6" '
                     f'fill="{ACC}"/>')
    o.append(line(POD[0] + POD_R, by, bx - 13, by, GREY, 1.5))

    # велосипедист згори: колеса лінією, сам їздець кружком
    o.append(line(686, Y_BIKE, 710, Y_BIKE, INK, 1.8))
    for wx in (686, 710):
        o.append(line(wx, Y_BIKE - 5, wx, Y_BIKE + 5, INK, 1.8))
    o.append(f'<circle cx="698" cy="{Y_BIKE:.1f}" r="5" fill="#fff" '
             f'stroke="{INK}" stroke-width="1.6"/>')
    # арт-кар згори
    o.append(f'<rect x="862" y="{Y_CAR-8:.1f}" width="34" height="16" rx="3" '
             f'fill="#fff" stroke="{INK}" stroke-width="1.8"/>')

    # промінь туди і назад — та сама пара, що на верхній частині схеми
    o.append(line(682, 372, 122, 372, WARN, 2.0, marker="nv-arr-warn"))
    o.append(t(430, 366, "світло фари", 11, WARN))
    o.append(line(122, 392, 682, 392, ACC, 2.5, marker="nv-arr-acc"))
    o.append(t(430, 406, "повернулось назад у фару", 11, ACC))
    o.append(line(640, Y_CAR, 118, 360, WARN, 2.0, "5 4", "nv-arr-warn"))

    o.append(t(POD[0], 424, "подіум", 11, INK, "middle"))
    o.append(t(BOX[0] + 5, 424, f'ящик · {TRUNK_M:g} м', 11, DIM, "middle"))
    o.append(t(698, 420, f'велосипедист · {SCENE["cyclist_m"]:g} м', 11, INK,
               "middle"))
    o.append(t(879, 366, f'арт-кар · {SCENE["artcar_m"]:g} м', 11, INK, "middle"))


def bars(o):
    """Лінійка дальності: з якої відстані що читається."""
    x_rule = x_of(RULE["distance_m"])
    o.append(line(x_rule, 458, x_rule, AXIS_Y + 12, SIG, 1.8))
    o.append(t(x_rule, 452,
               f'{RULE["distance_m"]:g} м — правило Burning Man', 11, SIG,
               "middle"))

    for y, r in zip(BAR_Y, RANGES):
        x1, x2 = x_of(r["from_m"]), x_of(r["to_m"])
        taken = r.get("taken", True)
        fill, ink = (ACC, ACC) if taken else (GREY, DIM)
        o.append(f'<rect x="{x1:.1f}" y="{y-9:.1f}" width="{x2-x1:.1f}" '
                 f'height="11" rx="2" fill="{fill}" '
                 f'stroke="{ink}" stroke-width="1.5"/>')
        num = f'{r["from_m"]:g}–{r["to_m"]:g} м'
        if not taken:
            num += " · не беремо"
        mid = min(max((x1 + x2) / 2, MARG + len(num) * 3.3), W - MARG - len(num) * 3.3)
        o.append(t(mid, y - 14, num, 11, SIG, "middle"))
        # підпис лягає праворуч від смуги, а якщо там уже нема місця до краю
        # полотна — ліворуч від неї: інакше він або обріжеться, або наїде на
        # лінію правила Burning Man
        name = r["label"]
        if x2 + 8 + len(name) * 6.6 <= W - MARG:
            o.append(t(x2 + 8, y, name, 11, INK if taken else DIM))
        else:
            o.append(t(x1 - 8, y, name, 11, INK if taken else DIM, "end"))

    o.append(line(XA, AXIS_Y, XB, AXIS_Y, INK, 1.5))
    for m in [D_MIN] + TICKS_M:
        x = x_of(m)
        o.append(line(x, AXIS_Y, x, AXIS_Y + 6, INK, 1.5))
        o.append(t(x, AXIS_Y + 18, f'{m:g}', 11, DIM, "middle"))
    o.append(t(MARG, 604,
               "лінійка дальності: рівні кроки — це множення, інакше "
               f'{RULE["distance_m"]:g} м і {SCENE["artcar_m"]:g} м не влізли б '
               "в один рядок", 11, DIM))
    o.append(t(MARG, 620,
               "мікропризма повертає вдесятеро більше світла за стрічку на "
               "скляній крихті, і луговий пил з неї протирається — з крихти вже ні",
               11, DIM))


def legend(o):
    """Три колонки по два рядки. Мініатюра кожного пункту — той самий елемент
    тим самим кольором і тією ж товщиною, що на схемі."""
    y1, y2 = 645, 667
    c1, c2, c3 = MARG, 350, 660

    o.append(line(c1, y1 - 4, c1 + 24, y1 - 4, WARN, 2.0))
    o.append(t(c1 + 32, y1, "промінь фари, що йде на обʼєкт", 11, DIM))
    o.append(line(c1, y2 - 4, c1 + 24, y2 - 4, ACC, 2.5))
    o.append(t(c1 + 32, y2, "світло, повернуте назад у фару", 11, DIM))

    o.append(f'<circle cx="{c2+12}" cy="{y1-4}" r="3.2" fill="{ACC}"/>')
    o.append(t(c2 + 32, y1,
               f'катафот {PASSIVE["reflector_size_in"][0]:g}×'
               f'{PASSIVE["reflector_size_in"][1]:g}": '
               f'{PASSIVE["reflectors_podium"]} + '
               f'{PASSIVE["reflectors_box"]} на ящик', 11, DIM))
    o.append(line(c2, y2 - 4, c2 + 24, y2 - 4, ACC, 2.5))
    o.append(t(c2 + 32, y2,
               f'стрічка DOT-C2, смуга 50 мм ({PASSIVE["tape_width_in"]:g}"), по торцю',
               11, DIM))

    o.append(line(c3 + 12, y1 - 12, c3 + 12, y1 + 2, SIG, 1.8))
    o.append(t(c3 + 32, y1,
               f'правило Burning Man: {RULE["distance_m"]:g} м', 11, DIM))
    o.append(line(c3, y2 - 4, c3 + 24, y2 - 4, WARN, 2.0, "5 4"))
    o.append(t(c3 + 32, y2, "пунктир — промінь фари скорочено", 11, DIM))


def svg():
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'width="100%" font-family="ui-monospace,Menlo,monospace">',
         "<defs>"]
    # Під кожен колір свій маркер: заливка вістря не успадковується від
    # stroke лінії. Id з префіксом файлу — на сторінку інлайняться кілька схем.
    for name, color in (("nv-arr-warn", WARN), ("nv-arr-acc", ACC),
                        ("nv-arr-dim", DIM)):
        o.append(f'<marker id="{name}" viewBox="0 0 10 10" refX="9" refY="5" '
                 f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                 f'<path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker>')
    o.append("</defs>")

    o.append(t(W / 2, 24,
               "Пасивна помітність: чому призма повертає промінь, а фарба — ні",
               14, INK, "middle"))
    o.append(t(W / 2, 42,
               f'Правило Burning Man: обʼєкт має бути видно за '
               f'{RULE["distance_ft"]:g} футів ≈ {RULE["distance_m"]:g} м. Це '
               f'виконує активне світло — {STAIRS_N} врізних вогні торця і '
               f'{MARKER_N} маркери ящика.', 11, DIM, "middle"))
    o.append(t(W / 2, 58,
               "Катафоти і стрічка самі не світять: вони повертають чужу фару, "
               "тому активне світло не заміняють.", 11, DIM, "middle"))

    part_surfaces(o)
    o.append(t(MARG, 314, "2 · З якої відстані що видно вночі", 12, INK))
    scene(o)
    bars(o)
    legend(o)
    for i, ln in enumerate(wrap(V["warning"], 136)):
        o.append(t(MARG, 690 + i * 16, ln, 11, CRIT))
    o.append("</svg>")
    return "\n".join(o)


def main():
    pts, d = prism_path()
    back = -(d[0] * DIR[0] + d[1] * DIR[1])
    print(f'правило BM: {RULE["seconds"]:g} с × {RULE["vehicle_mph"]:g} миль/год '
          f'= {RULE["distance_ft"]:g} футів ≈ {RULE["distance_m"]:g} м')
    print(f'активне світло: {STAIRS_N} врізних вогні торця + {MARKER_N} маркери '
          f'ящика (ящик за {TRUNK_M:g} м)')
    print(f'призма: {len(pts)-2} відбиття, вихід антипаралельний входу на '
          f'{back*100:.1f}% (1.0 = точно назад)')
    for r in RANGES:
        mark = "беремо " if r.get("taken", True) else "не беремо"
        print(f'  {mark} {r["name"]:22} від {r["lamp"]:9} '
              f'{r["from_m"]:>3g}–{r["to_m"]:>3g} м')
    print(f'пасив: {PASSIVE["reflectors_podium"]} катафотів на кути подіуму + '
          f'{PASSIVE["reflectors_box"]} на ящик, стрічка '
          f'{PASSIVE["tape_width_in"]:g}" {PASSIVE["tape_where"]}')
    (Path(__file__).resolve().parent / "night_visibility.svg").write_text(svg())
    print("креслення: night_visibility.svg")


if __name__ == "__main__":
    main()
