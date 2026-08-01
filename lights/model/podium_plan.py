#!/usr/bin/env python3
"""
Головний план проєкту: подіум згори — що де фізично стоїть.

Уся інженерія по світлу досі жила в таблицях і в схемах «що з чим зʼєднано»,
а на питання «як воно виглядає зверху» відповіді не було ніде. Ця схема і є
відповідь: один малюнок, на якому одночасно видно всі чотири шари.

  · вісім стійок з прожекторами заливки стоять у КУТАХ октагона, і кожна
    цілиться променем усередину, на фігуру; конус показує розкрив;
  · вісім рукавів адресної стрічки лежать у швах настилу — промінь від
    центрального кола до кута плюс заворот по колу;
  · двадцять чотири врізні вогні сидять у ТОРЦІ подіуму, по три на кожну
    грань. Це аварійна лінія: вона гасне останньою, бо саме вона тримає
    подіум видимим;
  · пасивний шар світла не потребує взагалі — катафоти на восьми кутах і
    світлоповертальна стрічка по торцю повертають фару того, хто їде,
    навіть коли живлення нема.

Праворуч — те, що поза подіумом: щит із запобіжниками на краю, силова траса
до ящика станції і сам ящик зі своїми двома маркерними вогниками і
катафотами на кутах. Траса намальована з розривом: 7.6 метрів у масштабі
подіуму просто не влазять у полотно, тому подвійна риска на ній означає
«тут вирізано, довжина підписана числом».

Звідки числа. Кількості, ватти, групи, розкрив променя, довжина магістралі і
геометрія стрічки — з lights/data/params.json; запобіжники рахує
lights_node_model.py; габарит станції — з enclosure/data/params.json і
solar/data/params.json. Розміри самого подіуму (радіус октагона, висота
торця, стійка, катафоти, фігура, прикидка ящика) — з lights/data/podium_plan.json,
куди вони знесені з конструкторського комплекту Rev 3.1. У цьому файлі з
чисел лише координати полотна.

Що рахується, а не задається: грань октагона і його периметр, крок врізних
вогнів по грані, промінь стрічки (радіус октагона мінус радіус центрального
кола), скільки вогнів на грань і скільки катафотів. Тому схема не може
розійтися з базою — вона з неї виводиться. Тільки stdlib.
"""

import json
import sys
from math import cos, hypot, pi, radians, sin, tan
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lights_node_model as lnm  # noqa: E402  (запобіжники рахує модель)

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(__file__).resolve().parent.parent / "data"
P = json.loads((DATA / "params.json").read_text())
D = json.loads((DATA / "podium_plan.json").read_text())
ENC = json.loads((ROOT / "enclosure" / "data" / "params.json").read_text())
SOL = json.loads((ROOT / "solar" / "data" / "params.json").read_text())


def fixture(fid):
    return next(f for f in P["fixtures"] if f["id"] == fid)


SPOT = fixture("spot")
STAIRS = fixture("stairs")
MARKER = fixture("box_marker")
ARM = fixture("water_arms")
GROUPS = P["groups"]
TRUNK = next(r for r in P["wiring"]["runs"] if r["id"] == "trunk")
FUSE = {f["id"]: f["rating"] for f in lnm.fuses()}
PEAK = lnm.peak_watts()

OCT = D["octagon"]
POST = D["post"]
PASS = D["passive"]
FIG = D["figure"]
BOX = D["box"]

# ------------------------------------------------------------------ геометрія
N = OCT["sides"]
R_MM = OCT["circumradius_mm"]            # центр → вершина
ACROSS_MM = 2 * R_MM                     # через вершини
FACE_MM = 2 * R_MM * sin(pi / N)         # довжина однієї грані
PERIM_MM = N * FACE_MM                   # периметр торця
RING_R_MM = ARM["ring_m"] * 1000 / (2 * pi)   # центральне коло настилу
RAY_MM = R_MM - RING_R_MM                # промінь стрічки: коло → вершина
TURN_MM = ARM["ring_m"] * 1000 / N       # заворот = 1/8 кола
PER_FACE = STAIRS["qty"] // N            # скільки врізних вогнів на грань
STEP_MM = FACE_MM / (PER_FACE + 1)       # крок між ними по грані
STATION = next(s for s in ENC["stations"] if SOL["station_chosen"] in s["name"])

# ------------------------------------------------------- полотно (тільки px)
W, H = 960, 668
CX, CY = 270, 300                        # центр подіуму на полотні
R_PX = 165                               # радіус октагона на полотні
S = R_PX / R_MM                          # єдиний масштаб схеми, px на мм
TAPE_PX = R_PX + 9                       # світлоповертальна стрічка по торцю
REFL_PX = R_PX + 20                      # катафоти на кутах
CABLE_Y = 314                            # вісь силової траси
PANEL = (470, 296, 78, 36)               # щит: x, y, ширина, висота
BOX_X, BOX_W = 680, BOX["plan_mm"][0] * S
BOX_H = BOX["plan_mm"][1] * S
BREAK_X = 612                            # де траса розірвана
LAB_X = 452                              # ліва межа блоку підписів праворуч
NOTE_X = 632                             # блок підписів під ящиком
LEG_Y, LEG_STEP = 514, 22                # легенда
COL2 = 520

INK, TXT2 = "#24231d", "#6b675c"
THIN, GHOST = "#d8d5c9", "#c9c6ba"
ACC, SIG = "#b35b1e", "#3d6f96"          # силова траса · розміри
G1, G2, G3 = "#b07c14", "#3d6f96", "#3d7a4f"   # прожектори · декор · аварійна
PASSIVE = "#b23a2e"                      # катафоти і стрічка


def px(x_mm, y_mm):
    """Модельні міліметри (центр подіуму 0,0, вісь Y вгору) → піксель."""
    return CX + x_mm * S, CY - y_mm * S


def ang(k):
    """Кут вершини k: перша дивиться на глядача, далі за годинниковою."""
    return radians(90 - 360 * k / N)


def vertex(k, r_mm=None):
    r = R_MM if r_mm is None else r_mm
    a = ang(k)
    return px(r * cos(a), r * sin(a))


def poly(r_px):
    """Октагон заданого радіуса, у пікселях."""
    return [(CX + r_px * cos(ang(k)), CY - r_px * sin(ang(k))) for k in range(N)]


def edge_lights():
    """Точки врізних вогнів: по три на грань, у чвертях її довжини."""
    out = []
    for k in range(N):
        x1, y1 = vertex(k)
        x2, y2 = vertex((k + 1) % N)
        for i in range(1, PER_FACE + 1):
            t = i / (PER_FACE + 1)
            out.append((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t))
    return out


def _pts(seq):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in seq)


def _t(x, y, s, size=11, fill=TXT2, anchor="start", weight=None):
    w = f' font-weight="{weight}"' if weight else ""
    return (f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" '
            f'font-size="{size}" fill="{fill}"{w}>{s}</text>')


def _block(x, y, lines, step=17):
    return [_t(x, y + i * step, s, size, fill) for i, (s, fill, size) in enumerate(lines)]


# ------------------------------------------------------------------- креслення
def svg():
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'width="100%" font-family="ui-monospace,Menlo,monospace">',
         '<defs>'
         '<marker id="pod-dim" viewBox="0 0 10 10" refX="9" refY="5" '
         'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
         f'<path d="M0,0 L10,5 L0,10 z" fill="{SIG}"/></marker>'
         '<marker id="pod-beam" viewBox="0 0 10 10" refX="9" refY="5" '
         'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
         f'<path d="M0,0 L10,5 L0,10 z" fill="{G1}"/></marker>'
         '</defs>']

    # --- шапка
    o.append(_t(W / 2, 24, "План подіуму згори: що де стоїть", 14, INK, "middle"))
    o.append(_t(W / 2, 42,
                f'октагон {ACROSS_MM:.0f} мм через вершини, {N} кутів · стійки з '
                f'прожекторами в кутах · ящик станції за {TRUNK["length_m"]:g} м',
                11, TXT2, "middle"))
    o.append(_t(W / 2, 58,
                f'грань {FACE_MM:.0f} мм · по {PER_FACE} врізні вогні на грань через '
                f'{STEP_MM:.0f} мм · коло стрічки R {RING_R_MM:.0f} мм · '
                f'торець {OCT["edge_height_mm"]} мм заввишки',
                11, TXT2, "middle"))

    # --- розмір через вершини: виносні лінії від лівої і правої вершини вгору
    lx, rx = CX - R_PX, CX + R_PX
    for x in (lx, rx):
        o.append(f'<line x1="{x}" y1="{CY - 6}" x2="{x}" y2="92" stroke="{THIN}" '
                 f'stroke-width="0.8"/>')
    o.append(f'<line x1="{lx}" y1="96" x2="{rx}" y2="96" stroke="{SIG}" '
             f'stroke-width="1.5" marker-start="url(#pod-dim)" '
             f'marker-end="url(#pod-dim)"/>')
    o.append(_t(CX, 88, f'{ACROSS_MM:.0f} мм через вершини · R {R_MM:.0f} мм',
                11, SIG, "middle"))

    # --- пасивний шар: стрічка по торцю (штрих = червоно-біла) і катафоти
    o.append(f'<polygon points="{_pts(poly(TAPE_PX))}" fill="none" '
             f'stroke="{PASSIVE}" stroke-width="2.2" stroke-dasharray="7 5"/>')
    for k in range(N):
        x, y = vertex(k, R_MM * REFL_PX / R_PX)
        o.append(f'<rect x="{x - 4:.1f}" y="{y - 4:.1f}" width="8" height="8" '
                 f'fill="{PASSIVE}"/>')

    # --- сам октагон: контур настилу і торця
    o.append(f'<polygon points="{_pts(poly(R_PX))}" fill="#ffffff" stroke="{INK}" '
             f'stroke-width="1.8"/>')

    # --- габарит фігури: привид-орієнтир, до нього ціляться всі прожектори
    ghost_r = FIG["arm_span_mm"] / 2 * S
    o.append(f'<circle cx="{CX}" cy="{CY}" r="{ghost_r:.1f}" fill="none" '
             f'stroke="{GHOST}" stroke-width="1.5" stroke-dasharray="4 6"/>')

    # --- промені прожекторів: конус розкриву від стійки всередину, до фігури
    half = radians(SPOT["beam_deg"] / 2)
    for k in range(N):
        pxp, pyp = vertex(k)
        ux, uy = CX - pxp, CY - pyp
        n = hypot(ux, uy)
        ux, uy = ux / n, uy / n
        length = n - ghost_r
        fx_, fy_ = pxp + ux * length, pyp + uy * length
        hw = length * tan(half)
        c1 = (fx_ - uy * hw, fy_ + ux * hw)
        c2 = (fx_ + uy * hw, fy_ - ux * hw)
        o.append(f'<polygon points="{_pts([(pxp, pyp), c1, c2])}" fill="{G1}" '
                 f'opacity="0.09"/>')
        o.append(f'<line x1="{pxp + ux * 9:.1f}" y1="{pyp + uy * 9:.1f}" '
                 f'x2="{fx_:.1f}" y2="{fy_:.1f}" stroke="{G1}" stroke-width="1.5" '
                 f'marker-end="url(#pod-beam)"/>')

    # --- стрічка: вісім рукавів у швах настилу, промінь плюс заворот по колу
    rr = RING_R_MM * S
    for k in range(N):
        x1, y1 = vertex(k)
        x2, y2 = vertex(k, RING_R_MM)
        a2 = ang(k + 1)
        x3, y3 = px(RING_R_MM * cos(a2), RING_R_MM * sin(a2))
        o.append(f'<path d="M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f} '
                 f'A{rr:.1f},{rr:.1f} 0 0 1 {x3:.1f},{y3:.1f}" fill="none" '
                 f'stroke="{G2}" stroke-width="2.2"/>')

    # --- фігура в центрі: дві опорні труби ніг і підпис
    for side in (-1, 1):
        x, y = px(side * FIG["leg_gap_mm"] / 2, 0)
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" '
                 f'r="{max(2.4, FIG["leg_tube_mm"] / 2 * S):.1f}" fill="{INK}"/>')
    o.append(_t(CX, CY + 18, "фігура", 11, INK, "middle"))

    # --- врізні вогні торця: по три на грань
    for x, y in edge_lights():
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="{G3}"/>')

    # --- стійки з прожекторами у кутах
    for k in range(N):
        x, y = vertex(k)
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6.5" fill="#ffffff" '
                 f'stroke="{INK}" stroke-width="1.6"/>')
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{G1}"/>')

    # --- виноска на стійку і блок про прожектори
    vx, vy = vertex(1)
    o.append(f'<polyline points="{vx:.1f},{vy - 6.5:.1f} {vx:.1f},150 {LAB_X - 6},150" '
             f'fill="none" stroke="{THIN}" stroke-width="0.8"/>')
    o.extend(_block(LAB_X, 162, [
        ("Прожектор заливки на стійці", INK, 12),
        (f'{SPOT["qty"]} стійок у кутах октагона, труба {POST["tube_mm"]} мм, '
         f'висота {POST["height_mm"]} мм', TXT2, 11),
        (f'розкрив {SPOT["beam_deg"]}°, приціл угору {POST["aim_up_deg"]}° на фігуру',
         TXT2, 11),
        (f'{SPOT["w_unit"]:g} Вт × {SPOT["qty"]} = {PEAK["g1"]:.0f} Вт, '
         f'запобіжник {FUSE["g1"]:g} А', TXT2, 11),
    ]))

    # --- силова траса: вихід із подіуму, щит, розрив, ящик
    ex, ey = CX + R_PX - 6, CABLE_Y
    px_, py_, pw, ph = PANEL
    o.append(f'<line x1="{ex:.1f}" y1="{ey}" x2="{px_}" y2="{ey}" stroke="{ACC}" '
             f'stroke-width="2.5"/>')
    o.append(f'<line x1="{px_ + pw}" y1="{ey}" x2="{BOX_X}" y2="{ey}" stroke="{ACC}" '
             f'stroke-width="2.5"/>')
    for x in (BREAK_X - 8, BREAK_X):
        o.append(f'<line x1="{x - 4}" y1="{ey + 8}" x2="{x + 4}" y2="{ey - 8}" '
                 f'stroke="{ACC}" stroke-width="1.5"/>')
    o.append(_t(BREAK_X + 4, ey - 14, f'{TRUNK["length_m"]:g} м', 11, SIG, "middle"))
    o.append(_t(BREAK_X + 4, ey + 20, "кабель у рукаві", 11, TXT2, "middle"))

    # --- щит подіуму: головний запобіжник і три групові
    o.append(f'<rect x="{px_}" y="{py_}" width="{pw}" height="{ph}" rx="3" '
             f'fill="#ffffff" stroke="{INK}" stroke-width="1.8"/>')
    o.append(_t(px_, py_ - 8, "щит подіуму", 11, INK))
    for i, c in enumerate((ACC, G1, G2, G3)):
        o.append(f'<rect x="{px_ + 9 + i * 16}" y="{py_ + 10}" width="9" height="16" '
                 f'rx="2" fill="{c}"/>')
    o.extend(_block(px_, py_ + ph + 16, [
        (f'головний {FUSE["main"]:g} А', TXT2, 11),
        (f'три групи по {FUSE["g1"]:g} А', TXT2, 11),
    ]))

    # --- ящик станції: стрічка по боках, катафоти на кути, два маркерні вогники
    bx, by = BOX_X, CABLE_Y - BOX_H / 2
    o.append(f'<rect x="{bx - 4:.1f}" y="{by - 4:.1f}" width="{BOX_W + 8:.1f}" '
             f'height="{BOX_H + 8:.1f}" fill="none" stroke="{PASSIVE}" '
             f'stroke-width="2.2" stroke-dasharray="7 5"/>')
    o.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{BOX_W:.1f}" '
             f'height="{BOX_H:.1f}" rx="3" fill="#ffffff" stroke="{INK}" '
             f'stroke-width="1.8"/>')
    for cx_ in (bx, bx + BOX_W):
        for cy_ in (by, by + BOX_H):
            o.append(f'<rect x="{cx_ - 4:.1f}" y="{cy_ - 4:.1f}" width="8" height="8" '
                     f'fill="{PASSIVE}"/>')
    sw, sh = STATION["dims_mm"][0] * S, STATION["dims_mm"][1] * S
    o.append(f'<rect x="{bx + (BOX_W - sw) / 2:.1f}" y="{by + (BOX_H - sh) / 2:.1f}" '
             f'width="{sw:.1f}" height="{sh:.1f}" fill="#efeee7" stroke="{GHOST}" '
             f'stroke-width="1.5"/>')
    o.append(_t(bx + BOX_W / 2, CABLE_Y + 4, "станція", 11, TXT2, "middle"))
    for sgn in (-1, 1):
        mx, my = bx + BOX_W / 2, CABLE_Y + sgn * BOX_H / 2
        o.append(f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="3.4" fill="{G3}"/>')
        o.append(f'<line x1="{mx:.1f}" y1="{my + sgn * 6:.1f}" x2="{mx:.1f}" '
                 f'y2="{my + sgn * 13:.1f}" stroke="{G3}" stroke-width="1.5"/>')
    o.append(_t(bx + BOX_W / 2, by - 22, "ящик станції", 12, INK, "middle"))
    o.extend(_block(NOTE_X, by + BOX_H + 32, [
        (f'габарит ≈{BOX["plan_mm"][0] / 1000:g} × {BOX["plan_mm"][1] / 1000:g} м — '
         f'розмір ще не обраний', TXT2, 11),
        (f'станція {STATION["dims_mm"][0]:.0f} × {STATION["dims_mm"][1]:.0f} мм у плані',
         TXT2, 11),
        (f'{MARKER["qty"]} маркерні вогники по {MARKER["w_unit"]} Вт у стінках',
         TXT2, 11),
        (f'катафоти на {4} кути, стрічка по боках', TXT2, 11),
    ]))

    # --- легенда: ліва колонка
    y = LEG_Y
    o.append(f'<circle cx="34" cy="{y - 4}" r="6.5" fill="#ffffff" stroke="{INK}" '
             f'stroke-width="1.6"/>')
    o.append(f'<circle cx="34" cy="{y - 4}" r="3" fill="{G1}"/>')
    o.append(_t(52, y, f'{GROUPS["g1"]["label"]}: {SPOT["qty"]} шт у кутах, '
                       f'конус — напрямок на фігуру'))
    y += LEG_STEP
    o.append(f'<line x1="26" y1="{y - 4}" x2="44" y2="{y - 4}" stroke="{G2}" '
             f'stroke-width="2.2"/>')
    o.append(_t(52, y, f'{GROUPS["g2"]["label"]}: {ARM["qty"]} рукавів стрічки '
                       f'у швах настилу'))
    y += LEG_STEP
    o.append(f'<circle cx="34" cy="{y - 4}" r="3.4" fill="{G3}"/>')
    o.append(_t(52, y, f'{GROUPS["g3a"]["label"]}: {STAIRS["qty"]} врізні вогні '
                       f'в торець + {MARKER["qty"]} маркери ящика'))
    y += LEG_STEP
    o.append(f'<line x1="26" y1="{y - 4}" x2="44" y2="{y - 4}" stroke="{ACC}" '
             f'stroke-width="2.5"/>')
    o.append(_t(52, y, f'силова траса {P["bus_v"]:g} В і щит із запобіжниками'))

    # --- легенда: права колонка
    y = LEG_Y
    o.append(f'<rect x="{COL2 - 4}" y="{y - 8}" width="8" height="8" fill="{PASSIVE}"/>')
    o.append(_t(COL2 + 18, y, f'катафоти {PASS["reflector_mm"][0]}×'
                              f'{PASS["reflector_mm"][1]} мм — {N} кутів подіуму, '
                              f'4 кути ящика'))
    y += LEG_STEP
    o.append(f'<line x1="{COL2 - 8}" y1="{y - 4}" x2="{COL2 + 10}" y2="{y - 4}" '
             f'stroke="{PASSIVE}" stroke-width="2.2" stroke-dasharray="7 5"/>')
    o.append(_t(COL2 + 18, y, f'світлоповертальна стрічка {PASS["tape_width_mm"]} мм '
                              f'по торцю і по боках ящика'))
    y += LEG_STEP
    o.append(f'<line x1="{COL2 - 8}" y1="{y - 4}" x2="{COL2 + 10}" y2="{y - 4}" '
             f'stroke="{GHOST}" stroke-width="1.5" stroke-dasharray="4 6"/>')
    o.append(_t(COL2 + 18, y, f'штрихове коло — габарит фігури по розмаху рук '
                              f'{FIG["arm_span_mm"] / 1000:g} м'))
    y += LEG_STEP
    for x in (COL2 - 8, COL2):
        o.append(f'<line x1="{x - 4}" y1="{y}" x2="{x + 4}" y2="{y - 10}" '
                 f'stroke="{ACC}" stroke-width="1.5"/>')
    o.append(_t(COL2 + 18, y, f'подвійна риска — розрив траси: {TRUNK["length_m"]:g} м '
                              f'у масштабі не влазять'))

    # --- підвал: те, чого в плані згори видно не може бути
    o.extend(_block(24, LEG_Y + 4 * LEG_STEP + 22, [
        (f'торець подіуму {OCT["edge_height_mm"]} мм заввишки: у плані врізні вогні '
         f'видно як точки по грані, вісь кожного на '
         f'{D["edge_light"]["axis_below_deck_mm"]} мм нижче настилу', TXT2, 11),
        (f'розміри подіуму — з конструкторського комплекту, редакція 3.1 '
         f'(2.44 м (вісім футів) через вершини); ящик і його точне місце ще не обрані',
         TXT2, 11),
    ]))

    o.append("</svg>")
    return "\n".join(o)


def main():
    print(f'октагон: {N} кутів, {ACROSS_MM:.0f} мм через вершини (R {R_MM:.0f}), '
          f'грань {FACE_MM:.0f} мм, периметр {PERIM_MM / 1000:.2f} м, '
          f'торець {OCT["edge_height_mm"]} мм')
    print(f'стійки: {SPOT["qty"]} у вершинах, труба {POST["tube_mm"]} мм × '
          f'{POST["height_mm"]} мм, розкрив {SPOT["beam_deg"]}°, '
          f'приціл {POST["aim_up_deg"]}°')
    print(f'стрічка: коло R {RING_R_MM:.0f} мм, промінь {RAY_MM:.0f} мм, '
          f'заворот {TURN_MM:.0f} мм, {ARM["qty"]} рукавів')
    print(f'врізні вогні: {STAIRS["qty"]} = {N} × {PER_FACE} на грань, крок '
          f'{STEP_MM:.0f} мм, вісь {D["edge_light"]["axis_below_deck_mm"]} мм '
          f'нижче настилу')
    print(f'пасивне: {N} катафотів на кути подіуму + 4 на ящик, стрічка '
          f'{PASS["tape_width_mm"]} мм на {PERIM_MM / 1000:.2f} м периметра')
    print(f'траса {TRUNK["length_m"]:g} м до ящика ≈{BOX["plan_mm"][0] / 1000:g}×'
          f'{BOX["plan_mm"][1] / 1000:g} м (розмір не обраний), станція '
          f'{STATION["name"]}')
    print(f'щит: головний {FUSE["main"]:g} А · Гр.1 {FUSE["g1"]:g} А · '
          f'Гр.2 {FUSE["g2"]:g} А · Гр.3А {FUSE["g3a"]:g} А')
    for c in D["_conflicts"]:
        print(f'  ⚠ {c}')
    (Path(__file__).resolve().parent / "podium_plan.svg").write_text(svg())
    print("креслення: podium_plan.svg")


if __name__ == "__main__":
    main()
