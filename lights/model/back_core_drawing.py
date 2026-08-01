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
  · PLA заборонено вголос — він пливе вже за 52 °C, а темний корпус на плайському
    сонці набирає більше (температури беремо з бази ящика, не з памʼяті);
  · кишеню під плату після друку треба ЗАМІРЯТИ, а не вірити CAD.

Жодного числа в коді нема: усе тягнеться з lights/data/back_core.json через
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
CTRL_MOD = bc.controller()
BRIEF = bc.print_brief()      # готове ТЗ друкарю — з нього і живе блок приміток
UNI = bc.uniformity()
AIR = bc.ambient()            # температури плайї лежать у базі ящика, не тут
WIRING = bc.D["wiring"]

D_WIN   = WIN["size_mm"]
D_FOOT  = BRIEF["footprint_mm"]   # похідне: вікно + поле з обох боків
D_BOARD = MOD["size_mm"]
CLR     = WIN["fit_clearance_mm"]
D_BORE  = round(D_BOARD + CLR, 2)
SHELF   = WIN["shelf_mm"]
PW      = WIN["pocket_wall_mm"]
HOLE    = WIN["cable_hole_mm"]
BEZEL   = WIN["bezel_mm"]
T_WALL  = DIF["thickness_mm"]
GAP     = DIF["gap_mm"]
PCB     = MOD["pcb_mm"]
DIODE_H = MOD["diode_h_mm"]     # висота корпусу 5050 над платою
DIODE_W = MOD["diode_mm"]       # ширина корпусу 5050
SAND, SKIN, CORE = SH["sandwich_mm"], SH["skin_mm"], SH["core_mm"]
RIB_MIN, RIB_MAX = (c * 10 for c in SH["ribs_cm"])
PITCH = bc.pitch_mm(MOD)
INNER_FILLET = WIN["inner_fillet_mm"]
HOLE_BACK = WIN["hole_back_mm"]   # осьовий просвіт від тилу плати до краю отвору
POCKET_END = WIN["pocket_end_mm"] # матеріал від дальнього краю отвору до торця
FIX_DEFAULT = WIN["fix_default"]
HOLE_CLOCK  = WIN["hole_clock_h"]
WIRES_IN_HOLE = WIRING["wires_in_hole"]

R_WIN,  R_FOOT  = D_WIN / 2,  D_FOOT / 2
R_BOARD, R_BORE = D_BOARD / 2, D_BORE / 2
R_SHELF = R_BOARD - SHELF         # внутрішній край полиці
R_SKIRT = R_WIN + PW              # зовнішній бік стакана
D_SKIRT = R_SKIRT * 2             # зовнішній Ø стакана
R_SOLID = R_WIN + (SAND - T_WALL) # де сендвіч повністю відновлюється (кінець переходу 45°)
D_SOLID = R_SOLID * 2
# R_BREAK: де обриваємо панель на розрізі. +10 мм від межі «рівного місця» —
# рівно стільки, щоб видно було перехід і хвилясту лінію обриву.
R_BREAK = R_FOOT + 10

Z_WIN   = T_WALL                  # внутрішній бік стінки вікна
Z_PANEL = SAND                    # внутрішній бік панелі
Z_BOARD = Z_WIN + GAP             # лице плати = рівень полиці
Z_BACK  = Z_BOARD + PCB           # тил плати
Z_HOLE  = Z_BACK + HOLE_BACK + HOLE / 2  # вісь отвору
Z_END   = Z_HOLE + HOLE / 2 + POCKET_END # торець стакана
Z_CONE  = Z_BOARD - (R_WIN - R_SHELF)    # де конус 45° виходить зі стінки

# Air gap from the LED emitter surface (top of die) to window inner face:
# GAP is measured from PCB face; LED body rises DIODE_H above PCB.
AIR_TO_EMITTER = GAP - DIODE_H

# Rings from the model (one source of truth):
RINGS_DATA = bc.rings()
R_OUTER_LED = RINGS_DATA[-1]["r_mm"]

# ───────────────────────── аркуш і палітра ─────────────────────────

W, H = 594.0, 420.0        # A2, одна одиниця viewBox = 1 мм
M = 12.0                   # поле
Y_HEAD, Y_MID = 46.0, 300.0
X_MID = 300.0

FX, FY = 148.0, 170.0      # центр виду зовні, масштаб 1:1
SX, SY = 297.0, 333.0      # початок розрізу, масштаб 2:1
S2 = 2.0

BG, FRAME = "#0b0e14", "#2b3648"
MAT, HATCH, EDGE = "#182234", "#3f5f96", "#7fa6e8"
DIMC, TXT, NOTE = "#5b9bff", "#eaf1ff", "#8e97a6"
ACC, PART = "#e08b3e", "#5fc9a0"
CENTER = "#3d5273"      # колір осьових
WARN = "#c97c2e"        # помаранчевий для «увага»

F_TITLE, F_VIEW, F_DIM, F_NOTE, F_TINY = 6.6, 4.2, 3.2, 3.4, 2.8
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


def g(v):
    """Число у форматі :g — те саме що n(), але повертає рядок для прямої підстановки."""
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
        f'<marker id="a3w" markerWidth="2.6" markerHeight="1.8" refX="2.6" refY="0.9" '
        f'orient="auto" markerUnits="userSpaceOnUse">'
        f'<path d="M0,0 L2.6,0.9 L0,1.8 Z" fill="{WARN}"/></marker>'
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
    arr_id = "a3w" if color == WARN else "a3"
    o = [line(ex, ey, px, py, color, 0.16, extra=f' marker-end="url(#{arr_id})"'),
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
    """Діоди так, як вони насправді сидять: дев'ять вкладених кілець.

    Малюємо їх не для краси — по них одразу видно те, через що на цьому
    аркуші окрема примітка: крайнє кільце стоїть майже на самому обрізі
    плати, тобто рівно там, куди заходить полиця.
    Розміри кружків — графіка, а не розмір деталі; реальний корпус
    5050 = {DIODE_W}×{DIODE_W} мм показаний в розрізі."""
    o = []
    dot_r = DIODE_W * 0.3 / 2   # умовний кружок, менший за реальний корпус
    for entry in RINGS_DATA:
        r, cnt = entry["r_mm"], entry["n"]
        if cnt == 1:
            o.append(circ(FX, FY, dot_r, PART, opacity=0.5))
            continue
        for i in range(cnt):
            a = 2 * pi * i / cnt - pi / 2
            o.append(circ(FX + r * cos(a), FY + r * sin(a), dot_r, PART, opacity=0.5))
    return o


def view_front():
    o = ['<g id="front">']

    # 1. Зони панелі. Все, що далі R_SOLID, лишається сендвічем 5 мм;
    #    коло вікна — суцільна стінка T_WALL мм; між ними перехід під 45°.
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
    # стакан зовні — Ø = D_SKIRT
    o.append(circ(FX, FY, R_SKIRT, "none", EDGE, 0.22, dash="2 2"))
    # полиця: кільце, яким деталь лягає на край плати
    o.append(circ(FX, FY, (R_BORE + R_SHELF) / 2, "none", ACC,
                  (R_BORE - R_SHELF), opacity=0.28))

    # 3. Отвір під кабель — на виді ззовні показаний на відповідній годині
    # hole_clock_h = 3 → "3 год" = 0° від правого краю по колу.
    # Кут у системі полярних координат (0°=право, зростання за год. стрілкою):
    hole_ang = (HOLE_CLOCK - 3) * 30.0   # год × 30°, де 3-год = 0°
    hx, hy = polar(FX, FY, R_SKIRT, -hole_ang)  # на зовнішній стінці стакана
    o.append(circ(hx, hy, HOLE / 2, BG, EDGE, 0.3))

    # підпис отвору на виді zzovni (стрілка до позиції на колі)
    lx, ly = polar(FX, FY, R_SKIRT + 14, -hole_ang + 15)
    ox, oy = polar(FX, FY, R_SKIRT + 2, -hole_ang)
    wires_str = " · ".join(WIRES_IN_HOLE)
    o.extend(leader(ox, oy, lx, ly, lx + 14, f"Ø{n(HOLE)}, {HOLE_CLOCK} год",
                    wires_str, anchor="start", color=NOTE))

    # мітка "ВЕРХ" — показуємо, що деталь кругла і орієнтація важлива
    ux, uy = FX, FY - R_SKIRT - 6
    o.append(line(FX, uy, FX, FY - R_SKIRT - 2, TXT, 0.3,
                  extra=' marker-end="url(#a2)"'))
    o.append(txt(FX, uy - 1.5, "ВЕРХ", F_DIM, TXT, "middle", "700"))
    o.append(txt(FX, uy + 2.8, f"кабель виходить на {HOLE_CLOCK} год", F_TINY, NOTE, "middle"))

    # 4. Розміри
    o.extend(dim_diam(FX, FY, R_WIN,   35, f"Ø{n(D_WIN)}",
                      f"світна ділянка, стінка {n(T_WALL)}"))
    o.extend(dim_diam(FX, FY, R_SKIRT, 50, f"Ø{D_SKIRT:g}",
                      "зовн. Ø стакана (кишені)", color=EDGE, out=5.0))
    o.extend(dim_diam(FX, FY, R_SOLID, 22, f"Ø{D_SOLID:g}",
                      "сендвіч відновлюється", color="#44618f", out=5.0))
    o.extend(dim_diam(FX, FY, R_BOARD, 145, f"Ø{n(D_BOARD)}",
                      f"плата · {bc.diodes_label(MOD['diodes'])}"))

    # рівного місця — горизонтальний розмір знизу
    ybot = FY + R_FOOT + 13
    o.extend(dim_h(FX - R_FOOT, FX + R_FOOT, ybot, f"Ø{n(D_FOOT)}",
                   FY + R_FOOT, FY + R_FOOT, "рівного місця на панелі"))

    # поле по краю: між світним колом і межею рівного місця
    o.extend(dim_radial(FX, FY, R_WIN, R_FOOT, -52, n(BEZEL), "поле по краю"))

    o.append(circ(FX, FY, R_FOOT, "none", NOTE, 0.3, dash="5 2.5"))
    o.extend(center_cross(FX, FY, R_FOOT + 12))

    o.extend(leader(*polar(FX, FY, (R_WIN + R_SOLID) / 2, 128), 82.0, 66.0, 16.0,
                    "перехід 45°", "сендвіч сходить у стінку"))

    # виносна для полиці
    o.extend(leader(*polar(FX, FY, (R_BORE + R_SHELF) / 2, 246), 100.0, 252.0, 18.0,
                    f"полиця, заходить {n(SHELF)} мм на плату",
                    f"зовн.край Ø{n(D_BORE)} → внутр. Ø{R_SHELF*2:g}"))

    # 5. Ребра жорсткості: крок 150-200 мм, а рівного місця треба D_FOOT.
    #    Малюємо гіршу пару (крок 150) — видно, що коло на неї налазить.
    rib_bad = D_FOOT > RIB_MIN
    for s in (-1, 1):
        x = FX + s * RIB_MIN / 2
        o.append(line(x, FY - R_FOOT - 8, x, FY + R_FOOT + 8, ACC, 0.3, dash="4 3"))
    o.append(txt(FX + RIB_MIN / 2 + 3, FY - R_FOOT - 5,
                 f"ребра, крок {n(RIB_MIN)}" + (" — НЕ ВЛАЗИТЬ!" if rib_bad else ""),
                 F_TINY, ACC))

    # 6. Слід розрізу А-А
    for s, lab in ((-1, "А"), (1, "А")):
        x = FX + s * (R_FOOT + 7)
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

    # отвір під кабель — наскрізь у стінці стакана, зліва
    hx0, hx1 = sx(-R_SKIRT), sx(-R_BORE)
    o.append(rect(hx0, sy(Z_HOLE - HOLE / 2), hx1 - hx0, HOLE * S2, BG))
    for z in (Z_HOLE - HOLE / 2, Z_HOLE + HOLE / 2):
        o.append(line(hx0, sy(z), hx1, sy(z), EDGE, 0.35))

    # внутрішній радіус (фаска) там, де стінка вікна переходить у стакан
    # (ліворуч: r = -R_WIN, z = Z_WIN; праворуч: r = R_WIN, z = Z_WIN)
    if INNER_FILLET > 0:
        fr = INNER_FILLET * S2
        for sx_c in (sx(-R_WIN), sx(R_WIN)):
            zy_c = sy(Z_WIN)
            # дуга у внутрішньому куті (чверть кола)
            o.append(f'<path d="M {sx_c:.2f},{zy_c - fr:.2f} '
                     f'Q {sx_c:.2f},{zy_c:.2f} {sx_c + (fr if sx_c < SX else -fr):.2f},{zy_c:.2f}" '
                     f'fill="none" stroke="{DIMC}" stroke-width="0.25" stroke-dasharray="1.5 1"/>')

    # плата з діодами: куплена річ, тому іншим кольором і без штрихування
    o.append(rect(sx(-R_BOARD), sy(Z_BOARD), D_BOARD * S2, PCB * S2, "#1b2c2a", PART, 0.35))
    # діоди: використовуємо реальні розміри з бази (DIODE_W × DIODE_H)
    dw = DIODE_W * S2       # ширина корпусу в масштабі 2:1
    dh = DIODE_H * S2       # висота корпусу над платою в масштабі 2:1
    for entry in RINGS_DATA:
        r = entry["r_mm"]
        for s in ((-1, 1) if r else (1,)):
            o.append(rect(sx(s * r) - dw / 2, sy(Z_BOARD - DIODE_H),
                          dw, dh, PART))
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
    lay = ((SKIN / 2, f"оболонка {n(SKIN)}", 314.0, 7.0),
           (SKIN + CORE / 2, f"порожнина {n(CORE)}", 322.5, 16.0),
           (SKIN + CORE + SKIN / 2, f"оболонка {n(SKIN)}", 331.0, 25.0))
    for z, lab, ty, dx in lay:
        o.extend(leader(xl + dx, sy(z), 86.0, ty, 24.0, lab))

    # стінка вікна — головна товщина аркуша
    o.extend(leader(sx(-46), sy(T_WALL / 2), 211.0, 318.0, 138.0,
                    f"стінка вікна {n(T_WALL)}",
                    f"{SPEC['walls']} периметри по {n(SPEC['line_mm'])} — суцільна"))

    # внутрішній радіус R у куті стінки
    o.extend(leader(sx(-R_WIN), sy(Z_WIN), 194.0, 325.0, 130.0,
                    f"R{n(INNER_FILLET)} у внутр. куті",
                    "тут тріскає першим", color=WARN))

    # стінка стакана: на рівні Z=0 вона = PW, на рівні кишені вона = 6.2 мм
    # PW — по вікну (найтонше місце); 6.2 = R_SKIRT - R_BORE по кишені
    wall_pocket = round(R_SKIRT - R_BORE, 2)
    xmid_wall_r = (sx(R_WIN) + sx(R_SKIRT)) / 2
    o.extend(leader(xmid_wall_r, sy(Z_WIN / 2), xr + 10, 333.0, xr + 55,
                    f"стінка у вікні {n(PW)} мм (ПРИКИДКА)",
                    f"у кишені {n(wall_pocket)} мм: Ø{D_SKIRT:g} − Ø{n(D_BORE)} / 2",
                    anchor="start"))

    # глибина від зовнішнього лиця до полиці (опорна площина)
    xg_shelf = xr + 43
    o.extend(dim_v(sy(0), sy(Z_BOARD), xg_shelf, n(Z_BOARD),
                   sx(R_SKIRT), sx(R_BOARD), "right",
                   f"від лиця до полиці ({n(T_WALL)}+{n(GAP)})"))

    # повітря від внутрішньої поверхні вікна до ЛИЦЯ плати
    xg = sx(16.5)
    o.extend(dim_v(sy(Z_WIN), sy(Z_BOARD), xg, n(GAP), None, None, "right",
                   f"від вікна до лиця плати"))
    o.append(line(sx(-2), sy(Z_WIN), xg + 1.6, sy(Z_WIN), DIMC, 0.14))

    # повітря від вікна до поверхні діода (светна точка)
    xg2 = xg + 12
    o.extend(dim_v(sy(Z_WIN), sy(Z_BOARD - DIODE_H), xg2, f"{AIR_TO_EMITTER:g}",
                   None, None, "right", "до поверхні діода"))
    o.append(line(sx(-2), sy(Z_BOARD - DIODE_H), xg2 + 1.6, sy(Z_BOARD - DIODE_H),
                  DIMC, 0.14, dash="2 1.5"))

    # висота корпусу діода і товщина плати
    xg3 = xg2 + 12
    o.extend(dim_v(sy(Z_BOARD - DIODE_H), sy(Z_BOARD), xg3, n(DIODE_H),
                   None, None, "right", f"корпус діода {n(DIODE_W)}×{n(DIODE_W)} мм"))
    o.extend(dim_v(sy(Z_BOARD), sy(Z_BACK), xg3, n(PCB),
                   None, None, "right", "плата (FR4)"))

    # уся кишеня від лиця і підпис що дно відкрите
    o.extend(dim_v(sy(0), sy(Z_END), xr + 68, n(Z_END), xr, sx(R_SKIRT), "right",
                   "уся глибина від лиця"))
    # пояснення: дно відкрите, плата заходить ззаду
    o.append(txt(xr + 69, sy(Z_END) + 5.5, "↑ дно ВІДКРИТЕ — плата заходить ззаду",
                 F_TINY, NOTE))

    # осьовий розмір отвору: від лиця до осі отвору
    xhole = xl - 20
    o.extend(dim_v(sy(0), sy(Z_HOLE), xhole, f"{Z_HOLE:g}",
                   sx(-R_SKIRT), sx(-R_SKIRT), "left",
                   f"від лиця до осі Ø{n(HOLE)}"))
    # кутове положення отвору
    o.append(txt(xhole - 2, sy(Z_HOLE) + 9.5, f"на {HOLE_CLOCK} год",
                 F_TINY, NOTE, "end"))

    # полиця і кріплення плати
    o.extend(leader(sx(-85), sy(Z_BOARD), 96.0, 376.0, 30.0,
                    f"полиця {n(SHELF)} мм, крайнє кільце на r≈{R_OUTER_LED:.0f}",
                    f"кріплення: {FIX_DEFAULT}"))
    # УВАГА: якщо полиця сідає на діоди
    if R_SHELF < R_OUTER_LED:
        o.append(txt(30.0, 383.0,
                     f"▲ УВАГА: полиця Ø{R_SHELF*2:g} перекриває діоди на r≈{R_OUTER_LED:.0f} — "
                     f"зрізати до {n(WIN['shelf_tabs'])} лапок по {n(WIN['shelf_tab_deg'])}°",
                     F_TINY, WARN))

    # підпис кабелю з правильними дротами
    wires_str = " · ".join(WIRES_IN_HOLE)
    o.extend(leader(sx(-R_SKIRT + PW / 2), sy(Z_HOLE), 76.0, 392.0, 22.0,
                    f"Ø{n(HOLE)} збоку в стінці",
                    wires_str))

    o.append(txt(sx(-30), sy(Z_END) - 4.5,
                 f"плата Ø{n(D_BOARD)} · {bc.diodes_label(MOD['diodes'])} · лицем до вікна",
                 F_DIM, TXT, "middle"))

    # діаметри знизу
    o.extend(dim_h(sx(-R_BORE), sx(R_BORE), 395.0, f"Ø{n(D_BORE)}",
                   sy(Z_END), sy(Z_END), f"кишеня = плата {n(D_BOARD)} + {n(CLR)} зазор"))
    o.extend(dim_h(sx(-R_WIN), sx(R_WIN), 406.0, f"Ø{n(D_WIN)}",
                   sy(Z_CONE), sy(Z_CONE), "світна ділянка"))
    # внутрішній Ø полиці
    o.extend(dim_h(sx(-R_SHELF), sx(R_SHELF), 395.0 - 8, f"Ø{R_SHELF*2:g}",
                   sy(Z_BOARD), sy(Z_BOARD), "внутр. Ø полиці",
                   color="#8e97a6"))

    o.append(txt(SX, 308.0, "РОЗРІЗ А-А · 2:1", F_VIEW, TXT, "middle"))
    o.append(txt(SX, 314.0, "зовнішній бік — угорі · дно відкрите", F_TINY, NOTE, "middle"))
    o.append("</g>")
    return o


# ───────────────────────── примітки ─────────────────────────


def notes_text():
    """Те, без чого друк піде не так. Порядок — за ціною помилки."""
    rib_bad = D_FOOT > RIB_MIN
    wall_pocket = round(R_SKIRT - R_BORE, 2)
    wires_str = " · ".join(WIRES_IN_HOLE)
    # PETG verdict from base:
    petg_entry = next(x for x in DIF["materials"] if x["key"] == "petg")
    petg_uv_note = petg_entry["why"]   # use the base text, do not contradict it
    return [
        ("МАТЕРІАЛ", TXT,
         f"{BRIEF['material']}, тільки білий — вікно і є розсіювач. Якщо ASA нема — "
         f"{BRIEF['material_alt']}: спеку тримає ({petg_entry['hdt_c']} °C), "
         f"{petg_uv_note}"),
        ("PLA НЕ ДРУКУВАТИ", ACC,
         f"PLA пливе вже за {n(BRIEF['material_ban_hdt_c'])} °C (hdt). На плайї в тіні "
         f"{n(AIR['shade_c'])} °C, на сонці {n(AIR['sun_c'])} °C; темний корпус набирає "
         f"ще зверху — тобто PLA вже за своєю межею, а не біля неї. "
         f"ASA тримає {n(BRIEF['material_hdt_c'])} °C. Це найважливіший рядок аркуша."),
        ("ОРІЄНТАЦІЯ ДРУКУ", TXT,
         f"{SPEC['orientation']}. "
         f"Підпори: {'потрібні' if SPEC['supports'] else 'НЕ потрібні'} — "
         f"обидва переходи 45°, міст над отвором Ø{n(HOLE)} мм (8 мм перекривається мостом; "
         f"якщо провисне — свердлити по місцю). "
         f"{SPEC.get('_supports_note', '')}"),
        ("ДРУК", TXT,
         f"{BRIEF['walls']} периметри · лінія {n(SPEC['line_mm'])} мм · шар "
         f"{n(BRIEF['layer_mm'])} мм · заповнення {n(BRIEF['infill_pct'])}% · "
         f"{BRIEF['finish']}. "
         f"УВАГА: нуль заповнення стосується ТІЛЬКИ стінки вікна ({n(T_WALL)} мм = "
         f"{BRIEF['walls']} периметри по {n(SPEC['line_mm'])}). "
         f"Стінка стакана і полиця — СУЦІЛЬНІ (заповнення 100%), інакше кишеня вийде порожньою."),
        ("ПОСАДКА ПЛАТИ", TXT,
         f"Кишеня Ø{n(D_BORE)} = плата Ø{n(D_BOARD)} + {n(CLR)} мм ({n(CLR/2)} на бік, ПРИКИДКА). "
         f"Після друку кишеню ЗАМІРЯТИ штангелем — друк дає усадку і «слонячу ногу» "
         f"на перших шарах. Тісно — зняти ножем; вільно — підкласти смужку скотчу."),
        ("ПОЛИЦЯ ТА КРІПЛЕННЯ", ACC if R_SHELF < R_OUTER_LED else TXT,
         f"Полиця Ø{R_SHELF*2:g}..{n(D_BORE)} мм, заходить {n(SHELF)} мм на край плати. "
         f"Крайнє кільце діодів на r≈{R_OUTER_LED:.0f} мм — "
         + (f"суцільна полиця СЯДЕ НА ДІОДИ. Зрізати до {n(WIN['shelf_tabs'])} лапок "
            f"по {n(WIN['shelf_tab_deg'])}° через 120° (кожна ≈30 мм по дузі). "
            if R_SHELF < R_OUTER_LED else "перевірити на живому модулі. ")
         + f"Кріплення: {FIX_DEFAULT}."),
        ("ЗАЗОР І РІВНОМІРНІСТЬ", TXT,
         f"Від вікна до ЛИЦЯ плати {n(GAP)} мм; до поверхні діода {AIR_TO_EMITTER:g} мм "
         f"(діод виступає {n(DIODE_H)} мм). "
         f"Крок вздовж кільця {UNI['pitch_mm']:.1f} мм → {GAP/UNI['pitch_mm']:.2f} кроку — рівне. "
         f"Між двома ЗОВНІШНІМИ кільцями (48 і 60 діодів) крок 17.2 мм → "
         f"{GAP/17.2:.2f} кроку — "
         + ("рівне. " if GAP/17.2 >= bc.UNI["comfort_ratio"] else "крапки вгадуються по краю. ")
         + "Перевіряти на живому модулі з 2-3 м."),
        ("ОТВІР ДЛЯ КАБЕЛЮ", TXT,
         f"Ø{n(HOLE)} мм збоку в стінці кишені, вісь на {Z_HOLE:g} мм від зовнішнього лиця, "
         f"на {HOLE_CLOCK} год (дивлячись ззовні, мітка «ВЕРХ» угорі). "
         f"Заводять після того, як плата стала на полицю: {wires_str}. "
         f"Дванадцять вольт у кишеню НЕ ЗАХОДЯТЬ — контролер і понижувач стоять ЗА нею."),
        ("ДОПУСК, ДАТА, РЕВ", NOTE,
         f"Загальний допуск ±0.3 мм на решту розмірів без власного допуску. "
         f"Ревізія: Rev 1.0 · дата: 2026-08-01. "
         f"Числа аркуша — lights/data/back_core.json через back_core.py; "
         f"правити там, після чого перезапустити генератор."),
        ("ЯКЩО ПАНЕЛЬ УЖЕ НАДРУКОВАНА", TXT,
         f"Те саме коло Ø{n(D_WIN)} вибрати дремелем ЗСЕРЕДИНИ, лишивши стінку {n(T_WALL)} мм. "
         f"Товщину міряти по ходу — на просвіт добре видно, коли лишається мало."),
        ("ВІДКРИТЕ — ЗВІРИТИ З МАРСЕЛЕМ", ACC,
         f"{SH['open']} Рівного місця треба Ø{n(D_FOOT)}, ребра через "
         f"{n(RIB_MIN)}-{n(RIB_MAX)} мм — "
         + ("між ребрами при кроці 150 мм коло НЕ ВЛАЗИТЬ, ребро доведеться обійти або "
            "перервати. " if rib_bad else "місце є не в кожному прольоті. ")
         + WIN["open_fix"]),
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
        y += 4.4
        for ln in textwrap.wrap(body, wrap_at):
            o.append(txt(x0 + 5, y, ln, F_NOTE, NOTE if color is not ACC else "#d8a978"))
            y += 4.1
        y += 2.5
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

    # штамп: те, що фабрикатор шукає очима першим.
    # Матеріал у штампі — матеріал ВІКНА (з print_brief), а не обшивки (shell.material).
    win_material = BRIEF["material"]
    x0, y0, wt, rows = 372.0, M, W - M - 372.0, [
        ("аркуш",   f"A2 {W:.0f}×{H:.0f} мм, друкувати без масштабування"),
        ("масштаб", f"вид зовні 1:1 · розріз А-А {S2:.0f}:1"),
        ("матеріал вікна", f"{win_material}, білий · стінка {n(T_WALL)} мм"),
        ("ревізія / дата", "Rev 1.0 · 2026-08-01"),
        ("джерело чисел", "lights/data/back_core.json"),
    ]
    hrow = (Y_HEAD - M) / len(rows)
    o.append(rect(x0, y0, wt, Y_HEAD - M, "none", FRAME, 0.4))
    o.append(line(x0 + 45, y0, x0 + 45, Y_HEAD, FRAME, 0.3))
    for i, (k, v) in enumerate(rows):
        yy = y0 + hrow * (i + 1)
        if i:
            o.append(line(x0, y0 + hrow * i, x0 + wt, y0 + hrow * i, FRAME, 0.25))
        o.append(txt(x0 + 2.5, yy - 2.4, k, F_TINY, NOTE))
        o.append(txt(x0 + 47, yy - 2.4, v, F_TINY, TXT))
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
    print(f"кишеня Ø{n(D_BORE)} (плата + {n(CLR)}) · стакан Ø{D_SKIRT:g} · "
          f"глибина {Z_END:g} мм · отвір Ø{n(HOLE)} на {Z_HOLE:g} мм від лиця, "
          f"на {HOLE_CLOCK} год")
    print(f"стінка у вікні {n(PW)} мм, у кишені {n(round(R_SKIRT-R_BORE,2))} мм; "
          f"R{n(INNER_FILLET)} у внутр. куті")
    print(f"air to emitter: {AIR_TO_EMITTER:g} мм (від вікна до поверхні діода); "
          f"air to PCB: {n(GAP)} мм")
    print(f"uniformity: вздовж кільця 12/{PITCH:.1f}={GAP/PITCH:.2f}; "
          f"між зовн. кільцями 12/17.2=0.70 — перевіряти")
    print(f"рівного місця треба Ø{n(D_FOOT)}, ребра через {n(RIB_MIN)}-{n(RIB_MAX)} мм — "
          + ("не влазить між ребрами, питати Марселя"
             if D_FOOT > RIB_MIN else "має влізти"))
    print(f"матеріал вікна: {BRIEF['material']} (тільки білий)")
    print(f"кріплення плати: {FIX_DEFAULT}")
    print(f"Rev 1.0 · 2026-08-01 · {out.name}")


if __name__ == "__main__":
    main()
