#!/usr/bin/env python3
"""
Робоче креслення вікна «ядра на спині» — аркуш під фабрикатора, а не інфографіка.

Вузол простий на словах і плутаний на пальцях: на спині робота світиться коло
Ø180, і це НЕ накладка на готовий корпус, а ділянка тієї самої панелі броні —
там, де решта панелі йде сендвічем 5 мм, на цьому колі лишається одна суцільна
стінка 1.6 мм білого ASA. Позаду неї, на 12 мм углиб, на полиці стоїть плата з
241 діодом. Пояснювати це в переписці — гарантовані перепитування, тому тут
аркуш: вид зовні, розріз А-А, розмірні лінії і блок приміток.

Дві речі, які на цьому аркуші головні:
  · PLA заборонено вголос — він пливе біля 52 °C, а темний корпус на плайському
    сонці набирає більше (температури беремо з бази ящика, не з памʼяті);
  · кишеню під плату після друку треба ЗАМІРЯТИ, а не вірити CAD.

Жодного розміру в коді нема: усе тягнеться з lights/data/back_core.json через
back_core.py (print_brief() — це вже готове ТЗ друкарю). Геометрія розрізу
виводиться з тих самих чисел: перехід сендвіча в стінку — фаска 45°, конус до
полиці — теж 45°, тобто друкується без підпор. Тільки stdlib.
"""

import sys
import textwrap
from math import cos, pi, sin
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import back_core as bc

# ───────────────────────── числа з бази ─────────────────────────

WIN, SH, DIF = bc.WIN, bc.D["shell"], bc.DIF
SPEC = DIF["print_spec"]
MOD = bc.module()
BRIEF = bc.print_brief()      # готове ТЗ друкарю — з нього і живе блок приміток
UNI = bc.uniformity()
AIR = bc.ambient()            # температури плайї лежать у базі ящика, не тут

D_WIN = WIN["size_mm"]
D_FOOT = BRIEF["footprint_mm"]   # похідне: вікно + поле з обох боків
D_BOARD = MOD["size_mm"]
CLR = WIN["fit_clearance_mm"]
D_BORE = round(D_BOARD + CLR, 2)
SHELF = WIN["shelf_mm"]
PW = WIN["pocket_wall_mm"]
HOLE = WIN["cable_hole_mm"]
BEZEL = WIN["bezel_mm"]
T_WALL = DIF["thickness_mm"]
GAP = DIF["gap_mm"]
PCB = MOD["pcb_mm"]
SAND, SKIN, CORE = SH["sandwich_mm"], SH["skin_mm"], SH["core_mm"]
RIB_MIN, RIB_MAX = (c * 10 for c in SH["ribs_cm"])
PITCH = bc.pitch_mm(MOD)

R_WIN, R_FOOT, R_BOARD = D_WIN / 2, D_FOOT / 2, D_BOARD / 2
R_BORE = D_BORE / 2
R_SHELF = R_BOARD - SHELF          # наскільки полиця заходить на плату
R_SKIRT = R_WIN + PW               # зовнішній бік стакана
R_SOLID = R_WIN + (SAND - T_WALL)  # де закінчується перехід під 45°
R_BREAK = R_FOOT + 10              # де обриваємо панель на розрізі

Z_WIN = T_WALL                     # внутрішній бік стінки вікна
Z_PANEL = SAND                     # внутрішній бік панелі
Z_BOARD = Z_WIN + GAP              # лице плати = полиця
Z_BACK = Z_BOARD + PCB             # тил плати
Z_HOLE = Z_BACK + PW + HOLE / 2    # вісь отвору живлення
Z_END = Z_HOLE + HOLE / 2 + PW     # дно стакана
Z_CONE = Z_BOARD - (R_WIN - R_SHELF)   # звідки конус 45° веде до полиці

RINGS = [0.0 if n == 1 else n * PITCH / (2 * pi) for n in MOD["rings_layout"]]
R_OUTER_LED = RINGS[-1]

# ───────────────────────── аркуш і палітра ─────────────────────────

W, H = 594.0, 420.0        # A2, одна одиниця viewBox = 1 мм
M = 12.0                   # поле
Y_HEAD, Y_MID = 46.0, 300.0
X_MID = 300.0

FX, FY = 155.0, 170.0      # центр виду зовні, масштаб 1:1
SX, SY = 297.0, 330.0      # початок розрізу, масштаб 2:1
S2 = 2.0

BG, FRAME = "#0b0e14", "#2b3648"
MAT, HATCH, EDGE = "#182234", "#3f5f96", "#7fa6e8"
DIMC, TXT, NOTE = "#5b9bff", "#eaf1ff", "#8e97a6"
ACC, PART = "#e08b3e", "#5fc9a0"
CENTER = "#3d5273"      # колір осьових

F_TITLE, F_VIEW, F_DIM, F_NOTE, F_TINY = 6.6, 4.2, 3.2, 3.3, 2.7
CW = 0.602                 # ширина моно-символа в частках кегля


def sx(r):
    return SX + r * S2


def sy(z):
    return SY + z * S2


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def n(v):
    """Число так, як його читають на кресленні: 12, а не 12.0."""
    return f"{v:g}"


def txt(x, y, s, size=F_DIM, fill=TXT, anchor="start", weight=None, opacity=None):
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    w = f' font-weight="{weight}"' if weight else ""
    op = f' opacity="{opacity}"' if opacity else ""
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" fill="{fill}"'
            f'{a}{w}{op}>{esc(s)}</text>')


def line(x1, y1, x2, y2, stroke=DIMC, w=0.16, dash=None, extra=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{stroke}" stroke-width="{w}"{d}{extra}/>')


def poly(pts, fill="none", stroke="none", w=0.45, rule=None, dash=None):
    d = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
    fr = f' fill-rule="{rule}"' if rule else ""
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<polygon points="{d}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{w}"{fr}{da}/>')


def rect(x, y, w_, h_, fill="none", stroke="none", sw=0.45, dash=None):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x:.2f}" y="{y:.2f}" width="{w_:.2f}" height="{h_:.2f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{da}/>')


def circ(cx, cy, r, fill="none", stroke="none", w=0.45, dash=None, opacity=None):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    op = f' opacity="{opacity}"' if opacity else ""
    return (f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{w}"{da}{op}/>')


ARROWS = ' marker-start="url(#a1)" marker-end="url(#a2)"'


def defs():
    """Стрілки, штрихування і світіння — усе, на що потім посилаємось."""
    return (
        '<defs>'
        f'<marker id="a1" markerWidth="2.8" markerHeight="1.9" refX="0" refY="0.95" '
        f'orient="auto" markerUnits="userSpaceOnUse">'
        f'<path d="M2.8,0 L0,0.95 L2.8,1.9 Z" fill="{DIMC}"/></marker>'
        f'<marker id="a2" markerWidth="2.8" markerHeight="1.9" refX="2.8" refY="0.95" '
        f'orient="auto" markerUnits="userSpaceOnUse">'
        f'<path d="M0,0 L2.8,0.95 L0,1.9 Z" fill="{DIMC}"/></marker>'
        f'<marker id="a3" markerWidth="2.6" markerHeight="1.8" refX="2.6" refY="0.9" '
        f'orient="auto" markerUnits="userSpaceOnUse">'
        f'<path d="M0,0 L2.6,0.9 L0,1.8 Z" fill="{NOTE}"/></marker>'
        # штрихування розрізу — як у кресленні, 45°, тонке
        f'<pattern id="cut" width="2.2" height="2.2" patternUnits="userSpaceOnUse" '
        f'patternTransform="rotate(45)">'
        f'<line x1="0" y1="0" x2="0" y2="2.2" stroke="{HATCH}" stroke-width="0.22"/>'
        f'</pattern>'
        # ділянка, де панель лишається сендвічем — рідше і тьмяніше
        f'<pattern id="sand" width="4" height="4" patternUnits="userSpaceOnUse" '
        f'patternTransform="rotate(45)">'
        f'<line x1="0" y1="0" x2="0" y2="4" stroke="#35557f" stroke-width="0.3"/>'
        f'</pattern>'
        f'<radialGradient id="lit"><stop offset="0" stop-color="{TXT}" stop-opacity="0.20"/>'
        f'<stop offset="0.72" stop-color="{TXT}" stop-opacity="0.10"/>'
        f'<stop offset="1" stop-color="{TXT}" stop-opacity="0.04"/></radialGradient>'
        '</defs>')


# ───────────────────────── розмірні лінії ─────────────────────────
#
# Правило те саме, що на паперових кресленнях: розмір стоїть на виносних
# лініях, стрілки впираються в межі, число — над лінією. Коли розмір
# дрібний і стрілки в нього не влазять, вони виносяться назовні, а число
# збоку. Нижче — рівно ці два випадки, більше нічого не треба.

TIGHT = 11.0        # менше цього між стрілками — виносимо їх назовні


def dim_h(x1, x2, y, label, y1=None, y2=None, sub=None, color=DIMC, size=F_DIM):
    """Горизонтальний розмір: виносні лінії від деталі вниз/вгору до лінії y."""
    o = []
    for x, yf in ((x1, y1), (x2, y2)):
        if yf is not None:
            step = 1.6 if yf < y else -1.6
            o.append(line(x, yf, x, y + step, color, 0.14))
    if abs(x2 - x1) >= TIGHT:
        o.append(line(x1, y, x2, y, color, 0.16, extra=ARROWS))
        o.append(txt((x1 + x2) / 2, y - 1.3, label, size, TXT, "middle"))
        if sub:
            o.append(txt((x1 + x2) / 2, y + 3.4, sub, F_TINY, NOTE, "middle"))
    else:
        o.append(line(x1 - 5, y, x2 + 5, y, color, 0.16))
        o.append(line(x1 - 4.6, y, x1, y, color, 0.16, extra=' marker-end="url(#a2)"'))
        o.append(line(x2 + 4.6, y, x2, y, color, 0.16, extra=' marker-end="url(#a2)"'))
        o.append(txt(x2 + 6.2, y - 1.3, label, size, TXT))
        if sub:
            o.append(txt(x2 + 6.2, y + 2.6, sub, F_TINY, NOTE))
    return o


def dim_v(y1, y2, x, label, x1=None, x2=None, side="left", sub=None, color=DIMC):
    """Вертикальний розмір: число збоку, бо повернуте боком читати незручно."""
    o = []
    for y, xf in ((y1, x1), (y2, x2)):
        if xf is not None:
            step = 1.6 if xf < x else -1.6
            o.append(line(xf, y, x + step, y, color, 0.14))
    ym = (y1 + y2) / 2
    tx = x - 1.8 if side == "left" else x + 1.8
    anchor = "end" if side == "left" else "start"
    if abs(y2 - y1) >= TIGHT:
        o.append(line(x, y1, x, y2, color, 0.16, extra=ARROWS))
    else:
        o.append(line(x, y1 - 5, x, y2 + 5, color, 0.16))
        o.append(line(x, y1 - 4.6, x, y1, color, 0.16, extra=' marker-end="url(#a2)"'))
        o.append(line(x, y2 + 4.6, x, y2, color, 0.16, extra=' marker-end="url(#a2)"'))
    o.append(txt(tx, ym + 1.1, label, F_DIM, TXT, anchor))
    if sub:
        o.append(txt(tx, ym + 5.2, sub, F_TINY, NOTE, anchor))
    return o


def leader(px, py, ex, ey, shelf_x, label, sub=None, anchor="end", color=NOTE):
    """Виносна полиця: стрілка в деталь, злам, поличка і підпис над нею."""
    o = [line(ex, ey, px, py, color, 0.16, extra=' marker-end="url(#a3)"'),
         line(shelf_x, ey, ex, ey, color, 0.16)]
    tx = shelf_x if anchor == "start" else ex
    o.append(txt(tx, ey - 1.4, label, F_DIM, TXT, anchor))
    if sub:
        o.append(txt(tx, ey + 3.2, sub, F_TINY, NOTE, anchor))
    return o


def dim_diam(cx, cy, r, ang, label, sub=None, color=DIMC, out=7.0):
    """Діаметр наскрізь через центр — стрілки в коло, число за колом."""
    a = ang * pi / 180.0
    dx, dy = cos(a), -sin(a)
    x1, y1 = cx + r * dx, cy + r * dy
    o = [line(cx - r * dx, cy - r * dy, x1, y1, color, 0.16, extra=ARROWS),
         line(x1, y1, cx + (r + out) * dx, cy + (r + out) * dy, color, 0.16)]
    tx, ty = cx + (r + out + 1.4) * dx, cy + (r + out + 1.4) * dy
    anchor = "start" if dx >= 0 else "end"
    o.append(txt(tx, ty + 1.0, label, F_DIM, TXT, anchor))
    if sub:
        o.append(txt(tx, ty + 4.9, sub, F_TINY, NOTE, anchor))
    return o


def polar(cx, cy, r, ang):
    """Точка на колі: кут звичний, за годинником вгору, а не як в SVG."""
    a = ang * pi / 180.0
    return cx + r * cos(a), cy - r * sin(a)


def dim_radial(cx, cy, r1, r2, ang, label, sub=None, color=DIMC):
    """Розмір уздовж радіуса — так міряють поле між двома колами.

    Стрілки завжди виносяться назовні: між колами тут одиниці міліметрів,
    усередину вони не влазять."""
    a = ang * pi / 180.0
    dx, dy = cos(a), -sin(a)
    p1 = (cx + r1 * dx, cy + r1 * dy)
    p2 = (cx + r2 * dx, cy + r2 * dy)
    q1 = (cx + (r1 - 5) * dx, cy + (r1 - 5) * dy)
    q2 = (cx + (r2 + 16) * dx, cy + (r2 + 16) * dy)
    o = [line(q1[0], q1[1], q2[0], q2[1], color, 0.16),
         line(q1[0], q1[1], p1[0], p1[1], color, 0.16,
              extra=' marker-end="url(#a2)"'),
         line(cx + (r2 + 5) * dx, cy + (r2 + 5) * dy, p2[0], p2[1], color, 0.16,
              extra=' marker-end="url(#a2)"')]
    tx, ty = cx + (r2 + 18) * dx, cy + (r2 + 18) * dy
    anchor = "start" if dx >= 0 else "end"
    o.append(txt(tx, ty, label, F_DIM, TXT, anchor))
    if sub:
        o.append(txt(tx, ty + 3.8, sub, F_TINY, NOTE, anchor))
    return o


def center_cross(cx, cy, r):
    """Осьові лінії — штрихпунктир, як і належить."""
    d = "6 1.4 1 1.4"
    return [line(cx - r, cy, cx + r, cy, CENTER, 0.16, dash=d),
            line(cx, cy - r, cx, cy + r, CENTER, 0.16, dash=d)]


# ───────────────────────── вид зовні ─────────────────────────


def diodes_front():
    """241 діод так, як вони насправді сидять: девʼять вкладених кілець.

    Малюємо їх не для краси — по них одразу видно те, через що на цьому
    аркуші окрема примітка: крайнє кільце стоїть майже на самому обрізі
    плати, тобто рівно там, куди заходить полиця."""
    o = []
    d = PITCH * 0.3 / 2           # діод показано кружком, це графіка, а не розмір
    for r, cnt in zip(RINGS, MOD["rings_layout"]):
        if cnt == 1:
            o.append(circ(FX, FY, d, PART, opacity=0.5))
            continue
        for i in range(cnt):
            a = 2 * pi * i / cnt - pi / 2
            o.append(circ(FX + r * cos(a), FY + r * sin(a), d, PART, opacity=0.5))
    return o


def view_front():
    o = ['<g id="front">']

    # 1. Зони панелі. Все, що далі R_SOLID, лишається сендвічем 5 мм;
    #    коло вікна — суцільна стінка 1.6 мм; між ними перехід під 45°.
    o.append(f'<path d="M {FX - R_BREAK:.2f},{FY:.2f} '
             f'a {R_BREAK:.2f},{R_BREAK:.2f} 0 1,0 {2*R_BREAK:.2f},0 '
             f'a {R_BREAK:.2f},{R_BREAK:.2f} 0 1,0 {-2*R_BREAK:.2f},0 '
             f'M {FX - R_SOLID:.2f},{FY:.2f} '
             f'a {R_SOLID:.2f},{R_SOLID:.2f} 0 1,0 {2*R_SOLID:.2f},0 '
             f'a {R_SOLID:.2f},{R_SOLID:.2f} 0 1,0 {-2*R_SOLID:.2f},0" '
             f'fill="url(#sand)" fill-rule="evenodd"/>')
    o.append(circ(FX, FY, R_SOLID, "#141c29"))          # перехід
    o.append(circ(FX, FY, R_WIN, "url(#lit)"))          # світна ділянка
    o.append(circ(FX, FY, R_WIN, "none", EDGE, 0.5))
    o.append(circ(FX, FY, R_SOLID, "none", "#44618f", 0.22, dash="3 2"))

    # 2. Плата під вікном — невидима, тому штрихова
    o.extend(diodes_front())
    o.append(circ(FX, FY, R_BOARD, "none", PART, 0.32, dash="3 1.6"))
    # полиця: кільце, яким деталь лягає на край плати
    o.append(circ(FX, FY, (R_BORE + R_SHELF) / 2, "none", ACC,
                  (R_BORE - R_SHELF), opacity=0.28))

    o.extend(leader(*polar(FX, FY, (R_BORE + R_SHELF) / 2, 246), 108.0, 262.0, 22.0,
                    f"полиця {n(SHELF)} мм", "заходить на край плати"))

    # 3. Рівне місце під увесь вузол
    o.append(circ(FX, FY, R_FOOT, "none", NOTE, 0.3, dash="5 2.5"))
    o.extend(center_cross(FX, FY, R_FOOT + 12))

    # 4. Ребра жорсткості: крок 150-200 мм, а рівного місця треба D_FOOT.
    #    Малюємо гіршу пару (крок 150) — видно, що коло на неї налазить.
    for s in (-1, 1):
        x = FX + s * RIB_MIN / 2
        o.append(line(x, FY - R_FOOT - 8, x, FY + R_FOOT + 8, ACC, 0.3, dash="4 3"))
    o.append(txt(FX + RIB_MIN / 2 + 3, FY - R_FOOT - 4, f"ребра, крок {n(RIB_MIN)}",
                 F_TINY, ACC))

    # 5. Розміри
    o.extend(dim_diam(FX, FY, R_WIN, 35, f"Ø{n(D_WIN)}", "світна ділянка, стінка 1.6"))
    o.extend(dim_diam(FX, FY, R_BOARD, 145, f"Ø{n(D_BOARD)}", "плата, 241 діод"))
    ybot = FY + R_FOOT + 12
    o.extend(dim_h(FX - R_FOOT, FX + R_FOOT, ybot, f"Ø{n(D_FOOT)}",
                   FY + R_FOOT, FY + R_FOOT, "рівного місця треба стільки"))
    # поле по краю: між світним колом і межею рівного місця
    o.extend(dim_radial(FX, FY, R_WIN, R_FOOT, -52, n(BEZEL), "поле по краю"))
    o.extend(leader(*polar(FX, FY, (R_WIN + R_SOLID) / 2, 128), 96.0, 74.0, 20.0,
                    "перехід 45°", "сендвіч сходить у стінку"))

    # 6. Слід розрізу А-А
    for s, lab in ((-1, "А"), (1, "А")):
        x = FX + s * (R_FOOT + 6)
        o.append(line(x - s * 7, FY, x, FY, TXT, 0.7))
        o.append(line(x, FY, x, FY + 6, TXT, 0.5, extra=' marker-end="url(#a2)"'))
        o.append(txt(x, FY - 2.4, lab, F_VIEW, TXT, "middle", "600"))

    o.append(txt(FX, Y_MID - 5, "ВИД ЗЗОВНІ · З БОКУ ГЛЯДАЧА · 1:1", F_VIEW, TXT, "middle"))
    o.append("</g>")
    return o


# ───────────────────────── розріз А-А ─────────────────────────


def solid_profile():
    """Контур матеріалу, права половина, у міліметрах (радіус, глибина).

    Читається згори за годинниковою: зовнішнє лице → обрив панелі →
    внутрішнє лице → фаска 45° переходу → стінка стакана назовні → дно →
    отвір під плату → полиця → конус 45° до вікна → стінка камери →
    внутрішній бік вікна назад до осі."""
    z_bevel = Z_WIN + (R_SKIRT - R_WIN)      # де фаска перетинає стакан
    return [(0, 0), (R_BREAK, 0), (R_BREAK, Z_PANEL), (R_SOLID, Z_PANEL),
            (R_SKIRT, z_bevel), (R_SKIRT, Z_END), (R_BORE, Z_END),
            (R_BORE, Z_BOARD), (R_SHELF, Z_BOARD), (R_WIN, Z_CONE),
            (R_WIN, Z_WIN), (0, Z_WIN)]


def view_section():
    o = ['<g id="section">']
    prof = solid_profile()
    full = [(sx(-r), sy(z)) for r, z in reversed(prof)] + [(sx(r), sy(z)) for r, z in prof]

    o.append(poly(full, MAT))
    o.append(poly(full, "url(#cut)", EDGE, 0.45))

    # порожнина сендвіча: там, де панель ще не стала суцільною
    for s in (-1, 1):
        x0, x1 = sorted((sx(s * R_SOLID), sx(s * R_BREAK)))
        o.append(rect(x0, sy(SKIN), x1 - x0, CORE * S2, BG, EDGE, 0.3))

    # обрив панелі — деталь триває далі
    for s in (-1, 1):
        x = sx(s * R_BREAK)
        zz = [(0, 0), (0.9, 1.2), (-0.9, 2.5), (0.9, 3.8), (0, 5.0)]
        pts = " ".join(f"{x + dx:.2f},{sy(z):.2f}" for dx, z in zz)
        o.append(f'<polyline points="{pts}" fill="none" stroke="{EDGE}" '
                 f'stroke-width="0.35"/>')

    # отвір під живлення і дані — наскрізь у стінці стакана, зліва
    hx0, hx1 = sx(-R_SKIRT), sx(-R_BORE)
    o.append(rect(hx0, sy(Z_HOLE - HOLE / 2), hx1 - hx0, HOLE * S2, BG))
    for z in (Z_HOLE - HOLE / 2, Z_HOLE + HOLE / 2):
        o.append(line(hx0, sy(z), hx1, sy(z), EDGE, 0.35))

    # плата з діодами: куплена річ, тому іншим кольором і без штрихування
    o.append(rect(sx(-R_BOARD), sy(Z_BOARD), D_BOARD * S2, PCB * S2, "#1b2c2a", PART, 0.35))
    # діоди стоять на лиці плати і дивляться у вікно; їх висота тут узята
    # рівною товщині плати — обидві 1.6, це графіка, а не окремий розмір
    dw = PITCH * 0.55
    for r in RINGS:
        for s in ((-1, 1) if r else (1,)):
            o.append(rect(sx(s * r) - dw * S2 / 2, sy(Z_BOARD - PCB),
                          dw * S2, PCB * S2, PART))
    o.append(line(SX, sy(-6), SX, sy(Z_END + 5), CENTER, 0.16, dash="6 1.4 1 1.4"))
    o.append("</g>")
    return o


def section_dims():
    """Розміри на розрізі. Дрібні товщини — виносними поличками, бо між
    стрілками там фізично нема місця; глибини — звичайними розмірними."""
    o = ['<g id="section-dims">']
    xl, xr = sx(-R_BREAK), sx(R_BREAK)

    # сендвіч цілком і три його шари
    o.extend(dim_v(sy(0), sy(Z_PANEL), xl - 7, n(SAND), xl, xl, "left", "сендвіч"))
    # точки беремо в різних місцях панелі, інакше три стрілки збігаються
    # в один пучок і незрозуміло, яка куди
    lay = ((SKIN / 2, f"оболонка {n(SKIN)}", 304.0, 7.0),
           (SKIN + CORE / 2, f"порожнина {n(CORE)}", 311.5, 16.0),
           (SKIN + CORE + SKIN / 2, f"оболонка {n(SKIN)}", 319.0, 25.0))
    for z, lab, ty, dx in lay:
        o.extend(leader(xl + dx, sy(z), 86.0, ty, 24.0, lab))

    # стінка вікна — головна товщина аркуша
    o.extend(leader(sx(-46), sy(T_WALL / 2), 205.0, 318.0, 132.0,
                    f"стінка вікна {n(T_WALL)}",
                    f"{SPEC['walls']} периметри по {n(SPEC['line_mm'])} — суцільна, без заповнення"))

    # повітря від вікна до плати — те, заради чого полиця стоїть саме тут
    xg = sx(16.5)
    o.extend(dim_v(sy(Z_WIN), sy(Z_BOARD), xg, n(GAP), None, None, "right",
                   "повітря до плати"))
    o.append(line(sx(-2), sy(Z_WIN), xg + 1.6, sy(Z_WIN), DIMC, 0.14))

    # уся кишеня і полиця
    o.extend(dim_v(sy(0), sy(Z_END), xr + 30, n(Z_END), xr, sx(R_SKIRT), "right",
                   "уся глибина від лиця"))
    o.extend(leader(sx(-85), sy(Z_BOARD), 96.0, 366.0, 30.0,
                    f"полиця, заходить на плату {n(SHELF)}",
                    "плата лягає на неї лицем"))
    o.extend(leader(sx(-R_SKIRT + PW / 2), sy(Z_HOLE), 74.0, 392.0, 26.0,
                    f"Ø{n(HOLE)} збоку", f"живлення {n(bc.BUS_V)} В і дані"))
    o.append(txt(sx(-30), sy(Z_END) - 4.5, f"плата Ø{n(D_BOARD)} · 241 діод · лицем до вікна",
                 F_DIM, TXT, "middle"))

    # діаметри знизу
    o.extend(dim_h(sx(-R_BORE), sx(R_BORE), 392.0, f"Ø{n(D_BORE)}",
                   sy(Z_END), sy(Z_END), f"кишеня = плата + {n(CLR)}"))
    o.extend(dim_h(sx(-R_WIN), sx(R_WIN), 403.0, f"Ø{n(D_WIN)}",
                   sy(Z_CONE), sy(Z_CONE), "світна ділянка"))

    o.append(txt(SX, 308.0, "РОЗРІЗ А-А · 2:1", F_VIEW, TXT, "middle"))
    o.append(txt(SX, 314.0, "зовнішній бік — угорі", F_TINY, NOTE, "middle"))
    o.append("</g>")
    return o


# ───────────────────────── примітки ─────────────────────────


def notes_text():
    """Те, без чого друк піде не так. Порядок — за ціною помилки."""
    rib_bad = D_FOOT > RIB_MIN
    return [
        ("МАТЕРІАЛ", TXT,
         f"{BRIEF['material']}, тільки білий — вікно і є розсіювач. Якщо ASA нема — "
         f"{BRIEF['material_alt']}: спеку тримає, але за пару тижнів на сонці трохи пожовкне."),
        ("PLA НЕ ДРУКУВАТИ", ACC,
         f"PLA пливе вже біля {n(BRIEF['material_ban_hdt_c'])} °C. На плайї в тіні "
         f"{n(AIR['shade_c'])} °C, а темний корпус на сонці набирає до {n(AIR['sun_c'])} °C — "
         f"це ВИЩЕ за межу, вікно просяде і потягне за собою всю панель. "
         f"ASA тримає {n(BRIEF['material_hdt_c'])} °C. Це найважливіший рядок аркуша."),
        ("ДРУК", TXT,
         f"{BRIEF['walls']} периметри · лінія {n(SPEC['line_mm'])} мм · шар "
         f"{n(BRIEF['layer_mm'])} мм · заповнення {n(BRIEF['infill_pct'])}% "
         f"({SPEC['infill_pattern']}) · {BRIEF['finish']}. Стінка вікна {n(T_WALL)} мм — це рівно "
         f"{BRIEF['walls']} лінії по {n(SPEC['line_mm'])}: суцільні периметри без заповнення, "
         f"інакше на просвіт підуть смуги."),
        ("ПОСАДКА ПЛАТИ", TXT,
         f"Кишеня Ø{n(D_BORE)} = плата Ø{n(D_BOARD)} плюс {n(CLR)} мм (по {n(CLR/2)} на бік). "
         f"Після друку кишеню ЗАМІРЯТИ штангелем і міряти саме деталь, а не вірити CAD: "
         f"друк дає усадку і «слонячу ногу» на перших шарах. Тісно — зняти ножем; "
         f"вільно — підкласти смужку скотчу."),
        ("ПОЛИЦЯ", TXT,
         f"Плату заводять ззаду, вона лягає лицем на полицю, тому полиця заходить на її "
         f"край на {n(SHELF)} мм. За правилом радіусів крайнє кільце діодів стоїть на "
         f"радіусі ≈{R_OUTER_LED:.0f} мм — це майже під полицею. На живому модулі перевірити: "
         f"якщо полиця сідає на діоди — зрізати її до трьох лапок."),
        ("ЗАЗОР", TXT,
         f"{n(GAP)} мм повітря від плати до вікна при кроці діодів {UNI['pitch_mm']:.1f} мм — це "
         f"{UNI['ratio']:.2f} кроку, {UNI['verdict']}. Менше не робити: полізуть крапки."),
        ("ОТВІР Ø8", TXT,
         f"Збоку в стінці кишені, за платою: крізь нього заходять живлення {n(bc.BUS_V)} В "
         f"і дані. "
         f"Заводити після того, як плата стала на полицю."),
        ("ЯКЩО ПАНЕЛЬ УЖЕ НАДРУКОВАНА ТОВСТОЮ", TXT,
         f"Запасний шлях: те саме коло Ø{n(D_WIN)} вибрати дремелем ЗСЕРЕДИНИ, лишивши "
         f"стінку {n(T_WALL)} мм. Товщину міряти по ходу — на просвіт добре видно, коли "
         f"лишається мало. Друкувати заново не обовʼязково."),
        ("ВІДКРИТЕ — ЗВІРИТИ З МАРСЕЛЕМ", ACC,
         f"{SH['open']} Рівного місця треба Ø{n(D_FOOT)}, а ребра йдуть через "
         f"{n(RIB_MIN)}-{n(RIB_MAX)} мм — "
         + ("між ребрами при кроці 150 мм коло НЕ ВЛАЗИТЬ, ребро доведеться обійти або "
            "перервати. " if rib_bad else "місце є не в кожному прольоті. ")
         + WIN["open_fix"]),
        ("ЧИСЛА", NOTE,
         "Усі розміри аркуша беруться з lights/data/back_core.json через back_core.py. "
         "Правити треба там: креслення перемальовується командою, руками в ньому нічого "
         "не виправляють."),
    ]


def notes_block(x0=306.0, y0=57.0, w=272.0):
    o = ['<g id="notes">', txt(x0, y0 - 5, "ПРИМІТКИ", F_VIEW, TXT)]
    o.append(line(x0, y0 - 2.6, x0 + w, y0 - 2.6, FRAME, 0.4))
    y = y0 + 4.5
    wrap_at = int((w - 6) / (F_NOTE * CW))
    for i, (head, color, body) in enumerate(notes_text(), 1):
        o.append(txt(x0 + 5, y, f"{i}. {head}", F_NOTE, color, weight="600"))
        if color is ACC:
            o.append(rect(x0, y - 3.4, 1.1, 4.6, ACC))
        y += 4.3
        for ln in textwrap.wrap(body, wrap_at):
            o.append(txt(x0 + 5, y, ln, F_NOTE, NOTE if color is not ACC else "#d8a978"))
            y += 4.0
        y += 2.4
    o.append("</g>")
    return o


# ───────────────────────── аркуш ─────────────────────────


def sheet():
    """Рамка, назва і кутовий штамп — щоб це читалось як креслення."""
    o = [f'<rect x="0" y="0" width="{n(W)}" height="{n(H)}" rx="8" fill="{BG}"/>',
         rect(M, M, W - 2 * M, H - 2 * M, "none", FRAME, 0.6),
         line(M, Y_HEAD, W - M, Y_HEAD, FRAME, 0.5),
         line(X_MID, Y_HEAD, X_MID, Y_MID, FRAME, 0.4),
         line(M, Y_MID, W - M, Y_MID, FRAME, 0.5),
         txt(19, 29, "ЯДРО НА СПИНІ — ВІКНО В ПАНЕЛІ БРОНІ", F_TITLE, TXT, weight="700"),
         txt(19, 39, "Hero Armor · Burning Man 2026 · система «світло» · вузол «ядро»",
             F_TINY, NOTE)]

    # штамп: те, що фабрикатор шукає очима першим
    x0, y0, wt, rows = 372.0, M, W - M - 372.0, [
        ("аркуш", "A2 594×420 мм, друкувати без масштабування"),
        ("масштаб", "вид зовні 1:1 · розріз А-А 2:1"),
        ("матеріал", f"{SH['material']}, білий · стінка вікна {n(T_WALL)} мм"),
        ("джерело чисел", "lights/data/back_core.json"),
    ]
    hrow = (Y_HEAD - M) / len(rows)
    o.append(rect(x0, y0, wt, Y_HEAD - M, "none", FRAME, 0.4))
    o.append(line(x0 + 40, y0, x0 + 40, Y_HEAD, FRAME, 0.3))
    for i, (k, v) in enumerate(rows):
        yy = y0 + hrow * (i + 1)
        if i:
            o.append(line(x0, y0 + hrow * i, x0 + wt, y0 + hrow * i, FRAME, 0.25))
        o.append(txt(x0 + 2.5, yy - 2.4, k, F_TINY, NOTE))
        o.append(txt(x0 + 43, yy - 2.4, v, F_TINY, TXT))
    return o


def legend():
    """Що означає тон і штриховка на виді — двома рядками, без таблиці."""
    o, x, y = [], 19.0, 55.0
    for fill, stroke, lab in (
            ("url(#sand)", "#44618f", f"панель лишається сендвічем {n(SAND)} мм"),
            ("url(#lit)", EDGE, f"тут стінка {n(T_WALL)} мм — світна ділянка")):
        o.append(rect(x, y - 3.6, 7, 4.6, fill, stroke, 0.3))
        o.append(txt(x + 10, y, lab, F_TINY, NOTE))
        y += 7.2
    return o


def svg():
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n(W)} {n(H)}" '
         f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
         defs()]
    o += sheet()
    o += legend()
    o += view_front()
    o += view_section()
    o += section_dims()
    o += notes_block()
    o.append("</svg>")
    return "\n".join(o)


def main():
    out = Path(__file__).resolve().parent / "back_core_drawing.svg"
    out.write_text(svg())
    print(f"вікно Ø{n(D_WIN)} у панелі {n(SAND)} мм → стінка {n(T_WALL)} мм; "
          f"плата Ø{n(D_BOARD)} на полиці {n(GAP)} мм углиб")
    print(f"кишеня Ø{n(D_BORE)} (плата + {n(CLR)}) · стакан углиб {n(Z_END)} мм · "
          f"отвір Ø{n(HOLE)} на {n(Z_HOLE)} мм від лиця")
    print(f"рівного місця треба Ø{n(D_FOOT)}, ребра через {n(RIB_MIN)}-{n(RIB_MAX)} мм — "
          + ("не влазить між ребрами, питати Марселя"
             if D_FOOT > RIB_MIN else "має влізти"))
    print(f"креслення: {out.name}")


if __name__ == "__main__":
    main()
