#!/usr/bin/env python3
"""
Розкладка на плайї: як подіум, ящик станції і сонячний масив стоять одне
відносно одного.

Це відповідь на питання, якого нема в жодній таблиці: «а як воно все стоїть на
місці?». Вигляд згори, північ угорі, полудневе сонце знизу. Видно чотири речі,
через які на плайї найчастіше і болить:

  · подіум із фігурою і стійками прожекторів у вершинах октагона;
  · ящик станції на іншому кінці силової траси — і тінь над ним, бо станція за
    паспортом працює лише до +45 °C, а повітря на плайї саме такої температури;
  · сонячний масив на південь від ящика, з нахилом і стрілкою «куди дивиться»;
  · саму трасу живлення і те, що з нею ще не вирішено.

Чого схема свідомо НЕ стверджує. Станція і масив на ній — це поточна точка
повзунка, а не вибір: `solar/data/params.json` тримає `station_fixed: false` і
`panel.fixed: false`, а `data/decisions.json` окремим рішенням забороняє
фіксувати їх заздалегідь. Так само не намальоване позначення траси: у
`data/tasks.json` це відкрита задача з трьома варіантами (стрічка вздовж траси,
килимок/лоток або підняти), тож схема лише називає питання невирішеним і
нагадує правило Burning Man — те, об що можна спіткнутись, треба СВІТИТИ, а
пасивне світло лише страхує. Розмір 7.6 м — теж не тверда відстань по землі, а
позначена прикидкою довжина КАБЕЛЮ від станції до щита.

Звідки числа. Геометрія подіуму, фігури і торця — lights/data/podium_plan.json;
кількості стійок, врізних вогнів і маркерів ящика — lights/data/params.json →
fixtures; довжина і калібр магістралі — там же, topology.segments[trunk];
станція, ємність, потужність масиву на повзунку і межа температури —
solar/data/params.json; габарит і вага станції — enclosure/data/params.json;
габарит ящика — enclosure/data/box_marking.json. Свої тут лише прикидки по
майданчику (навіс, модуль масиву з нахилом, сторони світу) —
solar/data/site_plan.json, там у кожного блока своє джерело і помітка estimate.

Тільки stdlib. Малює site_plan.svg поруч із собою.
"""

import json
from math import ceil, cos, pi, radians, sin
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
ROOT = HERE.parent.parent

SP = json.loads((DATA / "site_plan.json").read_text())
SOLAR = json.loads((DATA / "params.json").read_text())
LIGHTS = json.loads((ROOT / "lights" / "data" / "params.json").read_text())
PODIUM = json.loads((ROOT / "lights" / "data" / "podium_plan.json").read_text())
ENC = json.loads((ROOT / "enclosure" / "data" / "params.json").read_text())
BOXM = json.loads((ROOT / "enclosure" / "data" / "box_marking.json").read_text())


def fixture(fid):
    return next(f for f in LIGHTS["fixtures"] if f["id"] == fid)


# ---- числа з бази: світло --------------------------------------------------
SPOT = fixture("spot")                            # прожектори на стійках
STAIRS = fixture("stairs")                        # врізні вогні торця
MARKER = fixture("box_marker")                    # маркерні вогники ящика
TRUNK = next(s for s in LIGHTS["topology"]["segments"] if s["id"] == "trunk")
TRUNK_M = TRUNK["length_m"]                       # станція → щит подіуму
TRUNK_AWG = TRUNK["awg"]
TRUNK_EST = TRUNK.get("estimate", False)          # це прикидка, не з креслення

# ---- числа з бази: подіум і ящик -------------------------------------------
OCT = PODIUM["octagon"]
FIG = PODIUM["figure"]
N = OCT["sides"]
R_M = OCT["circumradius_mm"] / 1000               # центр → вершина
ACROSS_M = 2 * R_M                                # через вершини
EDGE_H_M = OCT["edge_height_mm"] / 1000           # висота торця
POSTS = SPOT["qty"]
BOX_MM = [BOXM["box"]["l_mm"], BOXM["box"]["w_mm"]]
BOX_CHOSEN = BOXM["box"].get("chosen", False)

# ---- числа з бази: живлення -------------------------------------------------
ST_NAME = SOLAR["station_chosen"]                 # яку станцію поки рахуємо
ST = SOLAR["stations"][ST_NAME]
ST_WH = ST["wh"]
ST_FIXED = SOLAR.get("station_fixed", False)
ARRAY_W = SOLAR["panel"]["chosen_w"]              # поточна точка повзунка
PANEL_FIXED = SOLAR["panel"].get("fixed", False)
T_MAX_C = SOLAR["temperature_limit"]["discharge_c"][1]
ST_BOX = next(s for s in ENC["stations"] if ST_NAME in s["name"])
ST_KG = ST_BOX["kg"]
ST_MM = ST_BOX["dims_mm"]                         # довжина × глибина × висота

# ---- прикидки майданчика (свій json) ---------------------------------------
CANOPY = SP["shade"]["canopy_mm"]
ARR = SP["array"]
PLAYA = SP["playa"]
MODULES = ceil(ARRAY_W / ARR["module_w"])         # скільки модулів у масиві
ARRAY_WIDE_M = MODULES * ARR["module_mm"][1] / 1000
# похилу панель згори видно коротшою — це і є її слід на землі
ARRAY_DEEP_M = ARR["module_mm"][0] / 1000 * cos(radians(ARR["tilt_deg"]))

# ---------------------------------------------------------------- полотно ----
W, H = 960, 716
OX, OY = 195, 300                                 # центр подіуму на полотні
S = 68                                            # пікселів на метр
LEG_Y, LEG_STEP, COL2 = 602, 22, 520              # легенда

INK, TXT2, THIN, HAIR = "#24231d", "#6b675c", "#c9c6ba", "#d8d5c9"
ACC, SIG, WARN, CRIT = "#b35b1e", "#3d6f96", "#b07c14", "#b23a2e"
GOOD, SHADE, FILL = "#3d7a4f", "#c9c5b6", "#efeee7"


def plural(n, one, few, many):
    """Форма числівника: 1 модуль, 3 модулі, 8 модулів."""
    n, n1, n2 = abs(n), abs(n) % 10, abs(n) % 100
    if 11 <= n2 <= 14:
        return many
    if n1 == 1:
        return one
    if 2 <= n1 <= 4:
        return few
    return many


def X(m):
    return OX + m * S


def Y(m):
    return OY - m * S


def txt(x, y, s, size=11, fill=TXT2, anchor=None, weight=None):
    a = f' text-anchor="{anchor}"' if anchor else ""
    w = f' font-weight="{weight}"' if weight else ""
    return f'<text x="{x:.0f}" y="{y:.0f}"{a} font-size="{size}" fill="{fill}"{w}>{s}</text>'


def marker(mid, color):
    return (f'<marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker>')


def octagon(cx, cy, r):
    """Вісім вершин октагона, перша дивиться вгору (на глядача)."""
    return [(cx + r * cos(pi / 2 + 2 * pi * k / N),
             cy - r * sin(pi / 2 + 2 * pi * k / N)) for k in range(N)]


def pts(seq):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in seq)


def svg():
    """План майданчика. Все, що має розмір, малюється в метрах через X()/Y();
    у пікселях задані тільки поля, заголовок, легенда і масштабна лінійка.

    Порядок шарів має значення: тіньовий навіс — це підкладка, тому він
    лягає ПЕРШИМ, а траса, ящик і кабель масиву йдуть уже поверх нього."""
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'width="100%" font-family="ui-monospace,Menlo,monospace">',
         '<defs>' + marker("site-dim", SIG) + marker("site-wind", WARN)
         + marker("site-go", GOOD) + marker("site-dir", INK) + '</defs>']

    unfixed = [] if PANEL_FIXED else ["масив"]
    if not ST_FIXED:
        unfixed.append("станція")

    # ---------------------------------------------------------- заголовок ----
    o.append(txt(W / 2, 24, "Розкладка на плайї: подіум, ящик станції і сонячний масив",
                 14, INK, "middle", "600"))
    head = (f"подіум {ACROSS_M:.2f} м через вершини · кабель до станції "
            f"{'≈' if TRUNK_EST else ''}{TRUNK_M:g} м")
    if unfixed:
        head += " · " + " і ".join(reversed(unfixed)) + " ще не обрані"
    o.append(txt(W / 2, 42, head, 11, TXT2, "middle"))
    o.append(txt(W / 2, 58,
                 "північ угорі, полудневе сонце знизу · вітер, сонце і бік під'їзду — "
                 "типові для плайї, точно розмічаємо на місці", 11, TXT2, "middle"))

    # ------------------------------------------------------------- компас ----
    o.append(f'<line x1="60" y1="200" x2="60" y2="160" stroke="{INK}" '
             f'stroke-width="1.8" marker-end="url(#site-dir)"/>')
    o.append(txt(60, 151, "північ", 11, INK, "middle"))

    # ------------------------------------------- звідки під'їжджають люди ----
    o.append(txt(330, 124, "звідси під'їжджають велосипеди й арт-кари", 11, GOOD))
    o.append(txt(330, 140, PLAYA["approach_from"], 11, TXT2))
    ax, ay = octagon(OX, OY, R_M * S)[7]           # вершина на північний схід
    o.append(f'<line x1="300" y1="180" x2="{ax + 6:.0f}" y2="{ay - 6:.0f}" '
             f'stroke="{GOOD}" stroke-width="3" marker-end="url(#site-go)"/>')

    # ---------------------------------------- підпис подіуму (над подіумом) --
    o.append(txt(OX, 172, f"подіум {ACROSS_M:.2f} м через вершини", 13, INK, "middle"))
    o.append(txt(OX, 188, f"торець {EDGE_H_M:.2f} м · {N} кутів · {POSTS} "
                          f"{plural(POSTS, 'стійка', 'стійки', 'стійок')} "
                          f"прожекторів у вершинах", 11, TXT2, "middle"))
    o.append(txt(OX, 204, "стійки показані умовно крупніше", 11, TXT2, "middle"))

    # ------------------------------------------------------ тінь (підкладка) -
    bx = R_M + TRUNK_M + BOX_MM[0] / 2000         # центр ящика, м від центру подіуму
    cw, ch = CANOPY[0] / 1000 * S, CANOPY[1] / 1000 * S
    o.append(f'<rect x="{X(bx) - cw / 2:.1f}" y="{Y(0) - ch / 2:.1f}" width="{cw:.1f}" '
             f'height="{ch:.1f}" rx="6" fill="{SHADE}" fill-opacity="0.3" '
             f'stroke="{TXT2}" stroke-width="1.6" stroke-dasharray="5 4"/>')
    o.append(txt(X(bx), 196, f"без тіні станція виходить за +{T_MAX_C:g} °C", 11, WARN, "middle"))
    o.append(txt(X(bx), 212, f'навіс {CANOPY[0] / 1000:.2f}×{CANOPY[1] / 1000:.2f} м — '
                             f'прикидка, місце ще не розмічене', 11, TXT2, "middle"))

    # -------------------------------------------------------------- подіум ---
    corners = octagon(OX, OY, R_M * S)
    o.append(f'<polygon points="{pts(corners)}" fill="#ffffff" stroke="{INK}" '
             f'stroke-width="1.8"/>')
    # габарит фігури по розмаху рук — привид-орієнтир, і дві опорні труби ніг
    o.append(f'<circle cx="{X(0):.0f}" cy="{Y(0):.0f}" '
             f'r="{FIG["arm_span_mm"] / 2000 * S:.1f}" fill="none" stroke="{THIN}" '
             f'stroke-width="1.5" stroke-dasharray="4 6"/>')
    for side in (-1, 1):
        o.append(f'<circle cx="{X(side * FIG["leg_gap_mm"] / 2000):.1f}" '
                 f'cy="{Y(0):.0f}" '
                 f'r="{max(2.4, FIG["leg_tube_mm"] / 2000 * S):.1f}" fill="{INK}"/>')
    o.append(txt(X(0), Y(0) + 26, "фігура", 11, INK, "middle"))
    for x, y in corners:                          # стійки прожекторів у вершинах
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#ffffff" '
                 f'stroke="{INK}" stroke-width="1.6"/>')

    # -------------------------------------------------- вітер і пил з ПЗ ----
    wx, wy = corners[3]                           # південно-західна вершина
    o.append(f'<line x1="{wx - 60:.0f}" y1="{wy + 95:.0f}" x2="{wx - 6:.0f}" '
             f'y2="{wy + 9:.0f}" stroke="{WARN}" stroke-width="3" '
             f'marker-end="url(#site-wind)"/>')
    o.append(txt(52, 486, "вітер і пил", 11, WARN))
    o.append(txt(52, 502, f'напрямок: {PLAYA["wind_from"]}', 11, WARN))

    # ------------------------------------------------------ траса живлення ---
    x_pod, x_box = X(R_M), X(bx) - BOX_MM[0] / 2000 * S
    tx = (x_pod + X(bx) - cw / 2) / 2             # центр блоку підписів траси
    o.append(f'<line x1="{x_pod:.0f}" y1="{Y(0):.0f}" x2="{x_box:.0f}" y2="{Y(0):.0f}" '
             f'stroke="{ACC}" stroke-width="2.5"/>')
    o.append(txt(tx, 276, f"магістраль світла AWG {TRUNK_AWG} · звук іде своїм кабелем",
                 11, ACC, "middle"))

    # розмір із виносними лініями: від вершини подіуму до стінки ящика
    y_dim, box_bot = 330, Y(0) + BOX_MM[1] / 2000 * S
    o.append(f'<line x1="{x_pod:.0f}" y1="{Y(0) + 6:.0f}" x2="{x_pod:.0f}" '
             f'y2="{y_dim + 6}" stroke="{HAIR}" stroke-width="0.8"/>')
    o.append(f'<line x1="{x_box:.0f}" y1="{box_bot + 4:.0f}" x2="{x_box:.0f}" '
             f'y2="{y_dim + 6}" stroke="{HAIR}" stroke-width="0.8"/>')
    o.append(f'<line x1="{x_pod:.0f}" y1="{y_dim}" x2="{x_box:.0f}" y2="{y_dim}" '
             f'stroke="{SIG}" stroke-width="1.5" marker-start="url(#site-dim)" '
             f'marker-end="url(#site-dim)"/>')
    o.append(txt(tx, y_dim - 8, f"{'≈' if TRUNK_EST else ''}{TRUNK_M:g} м", 11, SIG, "middle"))
    o.append(txt(tx, 352, "це довжина кабелю станція → щит, прикидка;", 11, TXT2, "middle"))
    o.append(txt(tx, 368, "по землі відстань менша — міряємо після складання",
                 11, TXT2, "middle"))
    o.append(txt(tx, 392, "об цю трасу спотикаються вночі: за правилом", 11, CRIT, "middle"))
    o.append(txt(tx, 408, "її треба світити, а не лише позначити", 11, CRIT, "middle"))
    o.append(txt(tx, 424, "чим саме — стрічкою, лотком чи підняти —", 11, TXT2, "middle"))
    o.append(txt(tx, 440, "ще не вирішено", 11, TXT2, "middle"))

    # ------------------------------------------------------- ящик і станція --
    bw, bh = BOX_MM[0] / 1000 * S, BOX_MM[1] / 1000 * S
    o.append(f'<rect x="{X(bx) - bw / 2:.1f}" y="{Y(0) - bh / 2:.1f}" width="{bw:.1f}" '
             f'height="{bh:.1f}" rx="3" fill="#ffffff" stroke="{INK}" stroke-width="1.8"/>')
    sw, sh = ST_MM[0] / 1000 * S, ST_MM[1] / 1000 * S
    o.append(f'<rect x="{X(bx) - sw / 2:.1f}" y="{Y(0) - sh / 2:.1f}" width="{sw:.1f}" '
             f'height="{sh:.1f}" rx="2" fill="#e8e4d6" stroke="{INK}" stroke-width="1.5"/>')
    o.append(txt(X(bx), 240, "ящик станції", 13, INK, "middle"))
    o.append(txt(X(bx), 256, f"поки рахуємо по {ST_NAME}: {ST_WH} Вт·год, {ST_KG:g} кг",
                 11, TXT2, "middle"))
    pend = [] if ST_FIXED else ["станція"]
    if not BOX_CHOSEN:
        pend.append("розмір ящика")
    if pend:
        o.append(txt(X(bx), 272, "ні " + ", ні ".join(pend) + " ще не обрані",
                     11, TXT2, "middle"))

    # -------------------------------------------------------------- масив ---
    ay_top = -(CANOPY[1] / 2000 + ARR["gap_to_shade_mm"] / 1000)
    aw, ah = ARRAY_WIDE_M * S, ARRAY_DEEP_M * S
    o.append(f'<line x1="{X(bx):.0f}" y1="{Y(0) + bh / 2:.0f}" x2="{X(bx):.0f}" '
             f'y2="{Y(ay_top):.0f}" stroke="{ACC}" stroke-width="2.5"/>')
    o.append(txt(X(bx) - bw / 2 - 8, Y(ay_top) - 10, "кабель масиву", 11, ACC, "end"))
    o.append(f'<rect x="{X(bx) - aw / 2:.1f}" y="{Y(ay_top):.1f}" width="{aw:.1f}" '
             f'height="{ah:.1f}" rx="3" fill="{FILL}" stroke="{INK}" stroke-width="1.8"/>')
    # стрілка «куди дивиться» — усередині рами, щоб підпис не ліз за рамку
    o.append(f'<line x1="{X(bx):.0f}" y1="{Y(ay_top) + 14:.0f}" x2="{X(bx):.0f}" '
             f'y2="{Y(ay_top) + ah - 12:.0f}" stroke="{INK}" stroke-width="1.8" '
             f'marker-end="url(#site-dir)"/>')
    ylab = Y(ay_top) + ah + 24
    o.append(txt(X(bx), ylab, "сонячний масив", 13, INK, "middle"))
    o.append(txt(X(bx), ylab + 16,
                 f'{ARRAY_W} Вт з повзунка ≈ {MODULES} '
                 f'{plural(MODULES, "модуль", "модулі", "модулів")} '
                 f'по {ARR["module_w"]} Вт', 11, TXT2, "middle"))
    o.append(txt(X(bx), ylab + 32,
                 f'нахил {ARR["tilt_deg"]:g}°, дивиться на {ARR["faces"]}',
                 11, TXT2, "middle"))
    if not PANEL_FIXED:
        o.append(txt(X(bx), ylab + 48, "потужність ще не обрана", 11, TXT2, "middle"))

    # ----------------------------------------------------- масштабна лінійка -
    x0, ybar, span = 340, 515, 3
    o.append(txt(x0, 505, "масштаб", 11, TXT2))
    o.append(f'<line x1="{x0}" y1="{ybar}" x2="{x0 + span * S}" y2="{ybar}" stroke="{INK}" '
             f'stroke-width="1.5"/>')
    for i in range(span + 1):
        o.append(f'<line x1="{x0 + i * S}" y1="{ybar - 5}" x2="{x0 + i * S}" '
                 f'y2="{ybar + 5}" stroke="{INK}" stroke-width="1.5"/>')
    o.append(txt(x0, ybar + 18, "0", 11, TXT2, "middle"))
    o.append(txt(x0 + span * S, ybar + 18, f"{span} м", 11, TXT2, "middle"))

    # -------------------------------------- що на цій схемі не показано вночі -
    o.append(txt(24, 540, f'вночі подіум тримає аварійна група: {STAIRS["qty"]} '
                          f'врізних вогнів у торці,', 11, TXT2))
    o.append(txt(24, 556, f'ящик має {MARKER["qty"]} маркерні '
                          f'{plural(MARKER["qty"], "вогник", "вогники", "вогників")} '
                          f'у стінках, катафоти й стрічку по боках —', 11, TXT2))
    o.append(txt(24, 572, "усе це на окремій схемі нічної помітності", 11, TXT2))

    # ------------------------------------------------------------- легенда ---
    y = LEG_Y
    o.append(f'<polygon points="{pts(octagon(40, y - 4, 7))}" fill="#ffffff" '
             f'stroke="{INK}" stroke-width="1.6"/>')
    o.append(txt(56, y, f'подіум: {N} кутів, {POSTS} '
                        f'{plural(POSTS, "стійка", "стійки", "стійок")} '
                        f'прожекторів у вершинах'))
    y += LEG_STEP
    o.append(f'<circle cx="40" cy="{y - 4}" r="7" fill="none" stroke="{THIN}" '
             f'stroke-width="1.5" stroke-dasharray="4 6"/>')
    o.append(f'<circle cx="40" cy="{y - 4}" r="2.4" fill="{INK}"/>')
    o.append(txt(56, y, f'штрихове коло — габарит фігури по розмаху рук '
                        f'{FIG["arm_span_mm"] / 1000:g} м, крапки — опорні труби ніг'))
    y += LEG_STEP
    o.append(f'<rect x="32" y="{y - 9}" width="16" height="11" fill="#ffffff" '
             f'stroke="{INK}" stroke-width="1.6"/>')
    o.append(f'<rect x="36" y="{y - 7}" width="8" height="7" fill="#e8e4d6" '
             f'stroke="{INK}" stroke-width="1.5"/>')
    o.append(txt(56, y, "ящик станції, всередині — сама станція"))
    y += LEG_STEP
    o.append(f'<rect x="32" y="{y - 9}" width="16" height="10" fill="{FILL}" '
             f'stroke="{INK}" stroke-width="1.8"/>')
    o.append(txt(56, y, "рама сонячного масиву"))
    y += LEG_STEP
    o.append(f'<rect x="32" y="{y - 9}" width="16" height="10" fill="{SHADE}" '
             f'fill-opacity="0.3" stroke="{TXT2}" stroke-width="1.6" '
             f'stroke-dasharray="5 4"/>')
    o.append(txt(56, y, "пунктир навколо ящика — межа тіньового навісу"))

    y = LEG_Y
    o.append(f'<line x1="{COL2 - 10}" y1="{y - 4}" x2="{COL2 + 10}" y2="{y - 4}" '
             f'stroke="{ACC}" stroke-width="2.5"/>')
    o.append(txt(COL2 + 18, y, "живлення: магістраль світла і кабель масиву"))
    y += LEG_STEP
    o.append(f'<line x1="{COL2 - 10}" y1="{y - 4}" x2="{COL2 + 10}" y2="{y - 4}" '
             f'stroke="{SIG}" stroke-width="1.5" marker-start="url(#site-dim)" '
             f'marker-end="url(#site-dim)"/>')
    o.append(txt(COL2 + 18, y, "синя лінія з двома стрілками — розмір"))
    y += LEG_STEP
    o.append(f'<line x1="{COL2 - 10}" y1="{y - 4}" x2="{COL2 + 10}" y2="{y - 4}" '
             f'stroke="{INK}" stroke-width="1.8" marker-end="url(#site-dir)"/>')
    o.append(txt(COL2 + 18, y, "чорна стрілка — напрямок: північ і куди дивиться масив"))
    y += LEG_STEP
    o.append(f'<line x1="{COL2 - 10}" y1="{y - 4}" x2="{COL2 + 10}" y2="{y - 4}" '
             f'stroke="{WARN}" stroke-width="2.5" marker-end="url(#site-wind)"/>')
    o.append(txt(COL2 + 18, y, "звідки дме вітер і йде пил"))
    y += LEG_STEP
    o.append(f'<line x1="{COL2 - 10}" y1="{y - 4}" x2="{COL2 + 10}" y2="{y - 4}" '
             f'stroke="{GOOD}" stroke-width="2.5" marker-end="url(#site-go)"/>')
    o.append(txt(COL2 + 18, y, "звідки під'їжджають люди"))

    o.append("</svg>")
    return "\n".join(o)


def main():
    print(f'подіум {ACROSS_M:.2f} м через вершини (R {R_M:.3f} м), торець '
          f'{EDGE_H_M * 1000:.0f} мм, {POSTS} стійок у вершинах')
    print(f'фігура: розмах рук {FIG["arm_span_mm"]} мм, опорні труби ніг через '
          f'{FIG["leg_gap_mm"]} мм — висота в плані згори не показана')
    print(f'траса: {TRUNK_M:g} м AWG {TRUNK_AWG} — {TRUNK.get("length_source", "—")}; '
          f'це довжина кабелю «{TRUNK["label"]}», а не відстань по землі')
    print(f'станція {ST_NAME}: {ST_WH} Вт·год, {ST_KG:g} кг, {ST_MM[0]}×{ST_MM[1]} мм '
          f'у плані, паспортна межа +{T_MAX_C:g} °C — '
          f'{"обрана" if ST_FIXED else "НЕ обрана, поточна точка повзунка"}')
    print(f'ящик у плані {BOX_MM[0]}×{BOX_MM[1]} мм '
          f'({"обраний" if BOX_CHOSEN else "прикидка, кейс не обраний"}), навіс '
          f'{CANOPY[0]}×{CANOPY[1]} мм (прикидка)')
    print(f'масив {ARRAY_W} Вт з повзунка ≈ {MODULES} × {ARR["module_w"]} Вт: '
          f'{ARRAY_WIDE_M:.2f} м завширшки, слід на землі {ARRAY_DEEP_M:.2f} м, '
          f'нахил {ARR["tilt_deg"]:g}° на {ARR["faces"]} — '
          f'{"обраний" if PANEL_FIXED else "НЕ обраний"}')
    print(f'нічна помітність (окрема схема): {STAIRS["qty"]} '
          f'{plural(STAIRS["qty"], "врізний вогонь", "врізні вогні", "врізних вогнів")} '
          f'у торці, {MARKER["qty"]} '
          f'{plural(MARKER["qty"], "маркер", "маркери", "маркерів")} ящика')
    for c in SP["_conflicts"]:
        print(f'  ⚠ {c}')
    (HERE / "site_plan.svg").write_text(svg())
    print("креслення: site_plan.svg")


if __name__ == "__main__":
    main()
