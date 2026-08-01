#!/usr/bin/env python3
"""
Врізний вогонь у торець подіуму: як вузол улаштований і чому його ще не замовили.

Ліва половина — розріз A-A по кресленню №8 архітектора. Знадвору (ліворуч) видно
тільки алюмінієву накладку торця з отвором; далі йде обшивна дошка з наскрізним
отвором під корпус, за нею — порожнина рами подіуму, куди виходить гайка і гофра
з кабелем. Розріз показує головне, чого не видно з переліку позицій: вогник
сідає не в дерево, а в тонку алюмінієву накладку, і саме її отвір задає, який
світильник узагалі можна купити.

Права половина — те, через що позиція стоїть у «чекаємо». Два силуети в ОДНОМУ
масштабі: отвори з креслення і посадка ходового набору з Amazon. Обидва кола
намальовані з тих самих даних, тому різниця видно одразу — червоне кільце між
ними і є те, що доведеться розсвердлити (або шукати інший світильник).

Звідки числа:
  lights/data/edge_light.json  — шари торця, отвори, кабель, розміри набору
                                 (заведений під цю схему, поле "_source" веде
                                 на аркуш №8 і на звірені 31.07 лістинги);
  lights/data/params.json      — скільки точок і скільки ватт на точку
                                 (fixtures → stairs), щоб не дублювати цифри.
У коді лишились тільки координати полотна. Тільки stdlib: CI збирає сайт без
залежностей.
"""

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
E = json.loads((DATA / "edge_light.json").read_text())
P = json.loads((DATA / "params.json").read_text())

SEC = E["section"]
HOLE = E["holes"]
CAB = E["cable"]
DRW = E["drawing"]
KIT = E["market_kit"]
CONF = E["conflict"]
STAIRS = next(f for f in P["fixtures"] if f["id"] == "stairs")

LAYERS = SEC["layers"]
T = {l["id"]: l["thick_mm"] for l in LAYERS}
LBL = {l["id"]: l["label"] for l in LAYERS}

# ---------------------------------------------------------------- палітра і кегль
INK, TXT2 = "#24231d", "#6b675c"
HAIR, THIN = "#d8d5c9", "#c9c6ba"
ACC, SIG = "#b35b1e", "#3d6f96"
GOOD, WARN, CRIT = "#3d7a4f", "#b07c14", "#b23a2e"
F_ALU, F_OSB, F_WOOD, F_PART, F_VOID = "#dfe7ee", "#e8e4d6", "#efeee7", "#f6f2e9", "#fcfcfb"
SAND = "#c9c5b6"

# ------------------------------------------------------------------- полотно
W, H = 960.0, 620.0
S = 1.7                       # px на мм у розрізі, однаковий по обох осях
Y_TOP = 132.0                 # верх настилу
X_FACE = 176.0                # зовнішня площина накладки торця
X_BREAK = 300.0               # де розріз обривається зиґзаґом
X_NOTE = 316.0                # колонка підписів праворуч від розрізу
X_DIV = 560.0                 # межа між половинами
X_B = 578.0                   # ліва межа правої половини
CX1, CX2 = 668.0, 848.0       # центри двох силуетів
CY_B = 200.0                  # спільна вісь силуетів
SB = 2.8                      # px на мм у силуетах


def _y(mm):
    """Глибина від верху настилу вниз, у пікселях полотна."""
    return Y_TOP + mm * S


def _x(mm):
    """Глибина всередину подіуму від зовнішньої площини накладки."""
    return X_FACE + mm * S


Y_ALU = _y(0.0)
Y_OSB = _y(T["alu_floor"])
Y_PINE = _y(T["alu_floor"] + T["osb"])
Y_PLANK = _y(T["alu_floor"] + T["osb"] + T["pine"])
Y_GND = _y(SEC["height_mm"])
Y_SAND = Y_GND - SEC["buried_mm"] * S
Y_AXIS = _y(SEC["axis_from_top_mm"])
X_BACK = _x(SEC["board_thick_mm"])          # тил обшивної дошки
X_PLATE = _x(SEC["plate_mm"])               # тил накладки


def _t(x, y, s, size=11, fill=TXT2, anchor="start", weight=None):
    """Підпис окремим <text> — інакше англійська версія сайту його не перекладе."""
    w = f' font-weight="{weight}"' if weight else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}"'
            f' text-anchor="{anchor}"{w}>{s}</text>')


def _box(x1, y1, x2, y2, fill, stroke=INK, sw=1.6):
    return (f'<rect x="{x1:.1f}" y="{y1:.1f}" width="{x2-x1:.1f}" '
            f'height="{y2-y1:.1f}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw}"/>')


def _lead(x1, y1, x2, y2):
    """Виноска-волосінь: тонка світла лінія без стрілки (стрілка означала б напрям)."""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{HAIR}" stroke-width="0.8"/>')


def _dim_v(x, y1, y2, ext_from=None):
    """Вертикальний розмір: двобічна стрілка + винесення від самої деталі."""
    o = [f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" '
         f'stroke="{SIG}" stroke-width="1.5" marker-start="url(#edge-arr)" '
         f'marker-end="url(#edge-arr)"/>']
    if ext_from is not None:
        for y in (y1, y2):
            o.append(f'<line x1="{x-4:.1f}" y1="{y:.1f}" x2="{ext_from:.1f}" '
                     f'y2="{y:.1f}" stroke="{HAIR}" stroke-width="0.8"/>')
    return o


def _conduit(pts):
    """Гофра з кабелем: лінія кольору траси плюс поперечні риски — щоб її не
    сплутали з виноскою."""
    d = " ".join(f'{x:.1f},{y:.1f}' for x, y in pts)
    o = [f'<polyline points="{d}" fill="none" stroke="{ACC}" stroke-width="2.5"/>']
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        n = max(2, int(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 // 13))
        ln = (((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5) or 1.0
        ux, uy = (x2 - x1) / ln, (y2 - y1) / ln
        for k in range(1, n):
            cx, cy = x1 + (x2 - x1) * k / n, y1 + (y2 - y1) * k / n
            o.append(f'<line x1="{cx-uy*3.2:.1f}" y1="{cy+ux*3.2:.1f}" '
                     f'x2="{cx+uy*3.2:.1f}" y2="{cy-ux*3.2:.1f}" '
                     f'stroke="{ACC}" stroke-width="1.5"/>')
    return o


def _zigzag(x, y1, y2, n=9, a=5.0):
    """Знак обірваного розрізу."""
    pts = []
    for k in range(n + 1):
        pts.append((x + (a if k % 2 else -a), y1 + (y2 - y1) * k / n))
    d = " ".join(f'{px:.1f},{py:.1f}' for px, py in pts)
    return [f'<polyline points="{d}" fill="none" stroke="{INK}" stroke-width="1.2"/>']


# --------------------------------------------------------------- ліва половина
def section():
    """Розріз A-A: шари торця, отвори, вогник, гайка і гофра."""
    o = []
    hw = HOLE["wood_mm"] * S / 2          # пів-отвору в сосні
    ha = HOLE["alu_mm"] * S / 2           # пів-отвору в накладці
    hp = HOLE["pocket_mm"] * S / 2        # пів-гнізда з тилу
    x_pocket = _x(SEC["board_thick_mm"] / 2)

    # ---- пісок: подіум на 38 мм заглиблений у плайю. Малюємо його тільки
    # знадвору — всередині рами піску нема, там порожнина над нижньою планкою.
    o.append(f'<rect x="46" y="{Y_SAND:.1f}" width="{X_FACE-46:.1f}" '
             f'height="78" fill="{SAND}" opacity="0.45"/>')
    o.append(f'<line x1="46" y1="{Y_SAND:.1f}" x2="{X_FACE:.1f}" y2="{Y_SAND:.1f}" '
             f'stroke="{SAND}" stroke-width="1.5"/>')

    # ---- настил і нижня планка
    o.append(_box(X_FACE, Y_ALU, X_BREAK, Y_OSB, F_ALU))
    o.append(_box(X_FACE, Y_OSB, X_BREAK, Y_PINE, F_OSB))
    o.append(_box(X_FACE, Y_PLANK, X_BREAK, Y_GND, F_OSB))

    # ---- обшивна дошка з отвором і гніздом з тилу
    o.append(_box(X_FACE, Y_PINE, X_BACK, Y_PLANK, F_WOOD))
    o.append(_box(X_FACE, Y_AXIS - hw, X_BACK, Y_AXIS + hw, F_VOID, THIN, 1.5))
    o.append(_box(x_pocket, Y_AXIS - hp, X_BACK, Y_AXIS + hp, F_VOID, THIN, 1.5))

    # ---- алюмінієва накладка торця: дві смуги, між ними отвір
    o.append(_box(X_FACE, Y_PINE, X_PLATE, Y_AXIS - ha, F_ALU, INK, 1.2))
    o.append(_box(X_FACE, Y_AXIS + ha, X_PLATE, Y_PLANK, F_ALU, INK, 1.2))

    # ---- кутик-носик по верхньому ребру
    c = SEC["corner_mm"] * S
    th = SEC["plate_mm"] * S
    o.append(f'<path d="M {X_FACE-th:.1f} {Y_PINE+c:.1f} L {X_FACE-th:.1f} '
             f'{Y_ALU-th:.1f} L {X_FACE+c:.1f} {Y_ALU-th:.1f} L {X_FACE+c:.1f} '
             f'{Y_ALU:.1f} L {X_FACE:.1f} {Y_ALU:.1f} L {X_FACE:.1f} '
             f'{Y_PINE+c:.1f} Z" fill="{F_ALU}" stroke="{INK}" stroke-width="1.2"/>')

    # ---- сам вогник: корпус проходить крізь дошку, гайка тягне його зсередини
    o.append(_box(X_FACE, Y_AXIS - ha, X_BACK, Y_AXIS + ha, F_PART))
    o.append(f'<rect x="{X_FACE-3:.1f}" y="{Y_AXIS-ha:.1f}" width="4.5" '
             f'height="{2*ha:.1f}" fill="{ACC}"/>')
    o.append(_box(X_BACK, Y_AXIS - ha - 5, X_BACK + 12, Y_AXIS + ha + 5, F_PART))
    o += _conduit([(X_BACK + 12, Y_AXIS), (X_BACK + 36, Y_AXIS),
                   (X_BREAK, Y_AXIS + 47)])
    o += _zigzag(X_BREAK, Y_ALU, Y_GND)

    # ---- розміри ліворуч: висота торця і обидва отвори
    o += _dim_v(64.0, Y_ALU, Y_GND)
    o.append(_t(64, Y_ALU - 6, f'{SEC["height_mm"]:g} мм', 11, SIG, "middle"))
    o += _dim_v(104.0, Y_AXIS - hw, Y_AXIS + hw, ext_from=X_PLATE)
    o.append(_t(110, Y_AXIS - hw - 4, f'Ø{HOLE["wood_mm"]:g}', 11, SIG))
    o += _dim_v(142.0, Y_AXIS - ha, Y_AXIS + ha, ext_from=X_FACE)
    o.append(_t(148, Y_AXIS + ha + 14, f'Ø{HOLE["alu_mm"]:g}', 11, SIG))
    o.append(_t(76, Y_SAND + 22, 'пісок плайї'))
    o.append(_t(76, Y_SAND + 38, f'у ґрунті {SEC["buried_mm"]:g} мм'))

    # ---- підписи праворуч, кожен зі своєю волосінню до деталі
    o.append(_t(X_FACE, 116, f'{SEC["corner_label"]}'))
    o.append(_lead(X_FACE + 44, 120, X_FACE + 30, Y_ALU - 4))

    rows = [
        (150, f'{LBL["alu_floor"]} {T["alu_floor"]:g} мм', (252, (Y_ALU + Y_OSB) / 2)),
        (172, f'{LBL["osb"]} {T["osb"]:g} мм', (252, (Y_OSB + Y_PINE) / 2)),
        (206, f'{LBL["pine"]} — {T["pine"]:g} мм', (215, Y_PINE + 40)),
        (222, 'обшивка торця', None),
        (250, f'{SEC["plate_label"]} {SEC["plate_mm"]:g} мм', (X_PLATE + 2, Y_AXIS - 40)),
        (280, f'вогник герметичний ({STAIRS["ip"]})', None),
        (296, 'затягується гайкою зсередини', (X_BACK + 13, Y_AXIS + 5)),
        (312, 'прокладка + силікон по колу', None),
        (336, f'{HOLE["pocket_label"]} Ø{HOLE["pocket_mm"]:g}', (x_pocket + 20, Y_AXIS + hp - 6)),
        (360, f'{CAB["label"]}: {CAB["gauge_awg"]} AWG, {CAB["area_mm2"]} мм²',
         (X_BREAK - 12, Y_AXIS + 39)),
        (392, f'{LBL["bottom"]} {T["bottom"]:g} мм', (255, (Y_PLANK + Y_GND) / 2)),
    ]
    for y, s, tgt in rows:
        o.append(_t(X_NOTE, y, s))
        if tgt:
            o.append(_lead(X_NOTE - 4, y - 4, tgt[0], tgt[1]))
    return o


# -------------------------------------------------------------- права половина
def silhouette(cx, title, circles, lines, lens=False):
    """Один силует: концентричні кола в масштабі SB і підписи під ними.

    Кола обох силуетів рахуються з тих самих даних і в тому самому масштабі —
    тільки тому їх і можна порівнювати оком."""
    o = [_t(cx, 136, title, 12, INK, "middle", 600)]
    for mm, stroke, sw, dash, fill in circles:
        d = f' stroke-dasharray="{dash}"' if dash else ""
        o.append(f'<circle cx="{cx:.1f}" cy="{CY_B:.1f}" r="{mm*SB/2:.1f}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')
    if lens:
        o.append(f'<circle cx="{cx:.1f}" cy="{CY_B:.1f}" r="11" fill="{ACC}"/>')
    for i, (s, fill, weight) in enumerate(lines):
        o.append(_t(cx, 282 + i * 18, s, 11, fill, "middle", weight))
    return o


def compare():
    """Креслення проти ходового набору: різницю дає рівно одне число."""
    gap = KIT["seat_mm"] - HOLE["alu_mm"]
    bezel = (KIT["flange_mm"] - KIT["seat_mm"]) / 2
    o = [_t(X_B, 92, 'Креслення проти ходового набору', 12, INK, weight=600)]

    o += silhouette(
        CX1, DRW["label"],
        [(HOLE["wood_mm"], THIN, 1.5, "5 4", "none"),
         (HOLE["alu_mm"], SIG, 1.8, "5 4", F_PART)],
        [(f'{HOLE["alu_label"]} Ø{HOLE["alu_mm"]:g}', TXT2, None),
         (f'{HOLE["wood_label"]} Ø{HOLE["wood_mm"]:g}', TXT2, None),
         ('вогник сідає в накладку', GOOD, 600)], lens=True)

    o += silhouette(
        CX2, KIT["label"],
        [(KIT["flange_mm"], CRIT, 1.5, None, "none"),
         (KIT["seat_mm"], CRIT, 2.0, None, CRIT),
         (HOLE["alu_mm"], SIG, 1.8, "5 4", F_VOID)],
        [(f'фланець Ø{KIT["flange_mm"]:g}', TXT2, None),
         (f'посадка Ø{KIT["seat_mm"]:g} — плюс {gap:g} мм', TXT2, None),
         ('у накладку не сідає', CRIT, 600)])
    # червоне кільце між отвором креслення і посадкою набору — це і є різниця
    o.append(_t(CX2 + 52, 164, f'+{gap:g} мм', 11, CRIT, "start", 600))
    o.append(_lead(CX2 + 50, 168, CX2 + 23, CY_B - 23))

    o.append(_t(X_B, 364, 'Відкрите питання', 12, WARN, weight=600))
    o.append(_t(X_B, 386, f'Розсвердлити накладку з Ø{HOLE["alu_mm"]:g} до '
                          f'Ø{KIT["seat_mm"]:g} —'))
    o.append(_t(X_B, 402, f'фланець Ø{KIT["flange_mm"]:g} накриє отвір з полем '
                          f'{bezel:g} мм.'))
    o.append(_t(X_B, 424, f'Або шукати вогник під Ø{HOLE["alu_mm"]:g}: вибір вужчий'))
    o.append(_t(X_B, 440, 'і дорожчий за штуку.'))
    o.append(_t(X_B, 462, f'{CONF["owner"]} — {CONF["status"]}', 11, WARN))
    return o


def legend():
    """Легенда: мініатюра самого елемента плюс що він означає."""
    o = [f'<line x1="30" y1="524" x2="52" y2="524" stroke="{SIG}" '
         f'stroke-width="1.5" marker-start="url(#edge-arr)" '
         f'marker-end="url(#edge-arr)"/>',
         _t(60, 528, 'розмір з креслення №8, Rev 2.1 (червень 2026)'),
         f'<circle cx="41" cy="546" r="7" fill="none" stroke="{SIG}" '
         f'stroke-width="1.8" stroke-dasharray="5 4"/>',
         _t(60, 550, f'пунктир — отвір за кресленням: Ø{HOLE["alu_mm"]:g} в '
                     f'накладці, Ø{HOLE["wood_mm"]:g} у сосні'),
         f'<circle cx="41" cy="568" r="7" fill="{CRIT}" stroke="{CRIT}" '
         f'stroke-width="1.5"/>',
         _t(60, 572, 'червоне — розмір ходового набору, який у цей отвір не сідає')]
    o += _zigzag(41, 586, 602, n=4, a=4.0)
    o.append(_t(60, 594, 'зиґзаґ — розріз обірвано, далі рама подіуму йде так само'))
    return o


def svg():
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
         f'width="100%" font-family="ui-monospace,Menlo,monospace">',
         f'<defs><marker id="edge-arr" viewBox="0 0 10 10" refX="9" refY="5" '
         f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
         f'<path d="M0,0 L10,5 L0,10 z" fill="{SIG}"/></marker></defs>']

    o.append(_t(W / 2, 24, 'Врізний вогонь у торець подіуму: розріз вузла і '
                           'відкрите питання', 14, INK, "middle"))
    o.append(_t(W / 2, 42, f'{STAIRS["qty"]} точок по колу торця, '
                           f'{STAIRS["w_unit"]:g} Вт кожна, аварійна група', 11,
               TXT2, "middle"))
    o.append(_t(W / 2, 58, f'розріз A-A: отвір Ø{HOLE["wood_mm"]:g} у сосні, '
                           f'Ø{HOLE["alu_mm"]:g} в алюмінієвій накладці торця',
               11, TXT2, "middle"))
    o.append(_t(46, 92, 'Розріз A-A — вузол у торці', 12, INK, weight=600))
    o.append(f'<line x1="{X_DIV}" y1="80" x2="{X_DIV}" y2="480" stroke="{HAIR}" '
             f'stroke-width="1.5"/>')

    o += section()
    o += compare()
    o.append(_t(46, 486, 'вогник затягується комплектною гайкою до алюмінієвої '
                         'накладки торця;'))
    o.append(_t(46, 502, 'прокладка під фланець і силікон зовні — щоб отвір не '
                         'став входом для пилу'))
    o += legend()
    o.append('</svg>')
    return "\n".join(o)


def main():
    stack = " + ".join(f'{l["label"]} {l["thick_mm"]:g}' for l in LAYERS)
    print(f'торець {SEC["height_mm"]:g} мм: {stack} (мм)')
    print(f'вісь вогника {SEC["axis_from_top_mm"]:g} мм від верху настилу · '
          f'у ґрунті {SEC["buried_mm"]:g} мм')
    print(f'отвори: Ø{HOLE["wood_mm"]:g} у сосні, Ø{HOLE["alu_mm"]:g} в накладці, '
          f'гніздо Ø{HOLE["pocket_mm"]:g} з тилу · кабель {CAB["gauge_awg"]} AWG '
          f'({CAB["area_mm2"]} мм²) у гофрі')
    print(f'{STAIRS["qty"]} точок × {STAIRS["w_unit"]:g} Вт = '
          f'{STAIRS["qty"]*STAIRS["w_unit"]:g} Вт на всю аварійну групу')
    print(f'ходовий набір: фланець Ø{KIT["flange_mm"]:g}, посадка '
          f'Ø{KIT["seat_mm"]:g} — на {KIT["seat_mm"]-HOLE["alu_mm"]:g} мм ширше '
          f'за отвір креслення')
    print(f'  {CONF["title"]} → {CONF["owner"]}, {CONF["status"]}')
    for opt in CONF["options"]:
        print(f'    · {opt}')
    (Path(__file__).resolve().parent / "edge_section.svg").write_text(svg())
    print("креслення: edge_section.svg")


if __name__ == "__main__":
    main()
