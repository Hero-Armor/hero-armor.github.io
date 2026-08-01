#!/usr/bin/env python3
"""
Ящик станції вночі: чим його видно і як сидить маркерний вогник у стінці.

Ящик стоїть окремо, за 7.6 м від подіуму, і в темряві його не видно взагалі —
це рівно те, об що спотикаються. Тому помітність робиться двома шарами, і на
схемі вони показані разом.

Пасивний шар працює навіть коли живлення нема взагалі: світлоповертальна
стрічка DOT-C2 смугою по периметру боків і чотири призматичні катафоти на кути.
Вони нічого не споживають, але світять тільки у відповідь на чужу фару — тобто
активне світло не заміняють, і правила Burning Man вимагають саме активне.

Активний шар — два маленькі вогники в протилежних стінках, що світять назовні.
З одного вогника ящик з іншого боку лишається темним, тому їх два. Вони в
аварійній групі: гаснуть останніми.

Схема має три частини. Вигляд збоку показує, чому ящик стоїть на підставці під
навісом: у тіні він бачить 42°C замість 55°C, а межа станції — 45°C, тобто
запасу майже нема. Вигляд згори показує розмітку по периметру і куди дивляться
обидва вогники. Окремий розріз показує посадку вогника в стінку: гвинтова
ніжка, гайка з прокладкою зсередини, силікон зовні по стику — бо інакше отвір
Ø12 мм стає найкоротшою дорогою для лугового пилу всередину, до самої станції.

Звідки числа:
  lights/data/params.json      — вогник (кількість, ватти, напруга, група),
                                 відстань до подіуму, калібр хвоста 18 AWG
  enclosure/data/params.json   — температури плайї, межа станції, зазор навколо
                                 станції, розмір пилу, надлишковий тиск, гермоввід
  solar/data/params.json       — яку станцію возимо (її габарит малюється всередині)
  enclosure/data/box_marking.json — тільки те, чого нема в базі: умовний габарит
                                 ящика, розміри катафота і стрічки, посадкові
                                 розміри вогника, правило 150 футів

Тільки stdlib. У коді нижче з чисел є лише координати полотна.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
HERE = Path(__file__).resolve().parent
E = json.loads((ROOT / "enclosure" / "data" / "params.json").read_text())
B = json.loads((ROOT / "enclosure" / "data" / "box_marking.json").read_text())
L = json.loads((ROOT / "lights" / "data" / "params.json").read_text())
S = json.loads((ROOT / "solar" / "data" / "params.json").read_text())

MARK = next(f for f in L["fixtures"] if f["id"] == "box_marker")
TRUNK = next(s for s in L["topology"]["segments"] if s["id"] == "trunk")
TAIL = next(s for s in L["topology"]["segments"] if s["id"] == "box_g3a")
STATION = next(s for s in E["stations"] if s["name"].endswith(S["station_chosen"]))
AMB = E["ambient"]
DUST = E["filtration"]["dust_um"]
PA = E["pressure"]["target_pa"]
GLAND = E["cable_entry"]["items"][0]["name"].split(" IP")[0]

BOX, REFL, TAPE, MK, VIS = B["box"], B["reflector"], B["tape"], B["marker"], B["visibility"]

# ---- палітра сайту (ті самі змінні, що в :root шаблонів)
INK, DIM2, HAIR, LINE = "#24231d", "#6b675c", "#d8d5c9", "#c9c6ba"
ACC, SIG, WARN, MASS = "#b35b1e", "#3d6f96", "#b07c14", "#c9c5b6"
FILL, GHOST_F, GASKET = "#efeee7", "#f6f2e9", "#dfe7ee"

# ---- полотно (єдині числа, які тут задані руками)
W, H = 960, 670
PX = 0.30                      # пікселів на міліметр в обох видах


def mm(v):
    return v * PX


def t(x, y, s, size=11, fill=DIM2, anchor="start", weight=None):
    w = f' font-weight="{weight}"' if weight else ""
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return (f'<text x="{x:.0f}" y="{y:.0f}"{a} font-size="{size}" '
            f'fill="{fill}"{w}>{s}</text>')


def leader(x1, y1, x2, y2):
    return (f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
            f'stroke="{HAIR}" stroke-width="0.8"/>')


def box(x, y, w, h, fill="#ffffff", stroke=INK, sw=1.6, extra=""):
    return (f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{extra}/>')


def beam(x, y, dx, half):
    """Конус світла маркерного вогника: куди він реально світить."""
    return (f'<polygon points="{x:.0f},{y:.0f} {x+dx:.0f},{y-half:.0f} '
            f'{x+dx:.0f},{y+half:.0f}" fill="{WARN}" opacity="0.18"/>')


def side_view(o):
    """Вигляд збоку: навіс, підставка, стрічка, катафоти, вогники, ввід кабелю."""
    o.append(t(48, 86, "Вигляд збоку", 12, INK, weight="600"))

    bw, bh = mm(BOX["l_mm"]), mm(BOX["h_mm"])
    x0, gy = 120, 330
    y1 = gy - mm(B["stand_mm"])
    y0 = y1 - bh
    x1 = x0 + bw

    # сонце і навіс: тінь важить більше за будь-який продув
    for sx in (160, 200, 240):
        o.append(f'<line x1="{sx}" y1="92" x2="{sx}" y2="110" stroke="{WARN}" '
                 f'stroke-width="1.5" marker-end="url(#bxm-sun)"/>')
    o.append(t(110, 100, "сонце", 11, WARN))
    o.append(f'<line x1="100" y1="120" x2="350" y2="120" stroke="{DIM2}" stroke-width="2"/>')
    o.append(f'<line x1="100" y1="120" x2="100" y2="130" stroke="{DIM2}" stroke-width="2"/>')
    o.append(f'<line x1="350" y1="120" x2="350" y2="130" stroke="{DIM2}" stroke-width="2"/>')
    o.append(t(356, 124, "навіс — тінь"))
    o.append(t(356, 140, f'{AMB["playa_shade_c"]}°C у тіні'))
    o.append(t(356, 156, f'{AMB["playa_sun_c"]}°C на сонці'))

    # земля і підставка над нею
    o.append(f'<line x1="44" y1="{gy}" x2="500" y2="{gy}" stroke="{MASS}" stroke-width="1.8"/>')
    for sx in (x0 + 20, x1 - 50):
        o.append(box(sx, y1, 30, gy - y1, MASS, MASS, 1.5))
    o.append(t(176, 322, "підставка"))
    o.append(t(350, 348, "розпечена земля"))

    # сам ящик і станція всередині (привид-орієнтир)
    o.append(box(x0, y0, bw, bh, FILL))
    sw_, sh_ = mm(STATION["dims_mm"][0]), mm(STATION["dims_mm"][2])
    sx0 = x0 + (bw - sw_) / 2
    sy1 = y1 - mm(E["fit"]["clearance_mm"])
    o.append(box(sx0, sy1 - sh_, sw_, sh_, "none", LINE, 1.5,
                 ' stroke-dasharray="4 6"'))
    o.append(t(x0 + bw / 2, 240, "станція", 11, DIM2, "middle"))

    # катафоти на видимих кутах
    rw, rh = mm(REFL["w_mm"]), mm(REFL["h_mm"])
    for rx in (x0, x1 - rw):
        o.append(box(rx, y0 + 16, rw, rh, GHOST_F, INK, 1.5))
    o.append(leader(x1, 180, 352, 172))
    o.append(t(356, 176, "катафот"))

    # світлоповертальна стрічка: тут вона в масштабі, тому й розмір підписаний
    tw = mm(TAPE["width_mm"])
    ty = y0 + bh * 0.76
    o.append(box(x0, ty, bw, tw, "#ffffff", INK, 1.5))
    o.append(f'<line x1="104" y1="{ty:.0f}" x2="104" y2="{ty+tw:.0f}" stroke="{SIG}" '
             f'stroke-width="1.5" marker-start="url(#bxm-sig)" marker-end="url(#bxm-sig)"/>')
    o.append(t(56, ty + tw - 3, f'{TAPE["width_mm"]:.0f} мм', 11, SIG))

    # два вогники в протилежних стінках і куди вони світять
    my = y0 + bh * 0.49
    o.append(beam(x0, my, -64, 20))
    o.append(beam(x1, my, 74, 22))
    for mx in (x0, x1):
        o.append(f'<circle cx="{mx:.0f}" cy="{my:.0f}" r="5" fill="{WARN}" '
                 f'stroke="{INK}" stroke-width="1.5"/>')
    o.append(t(410, my - 11, "маркерний", 11, INK))
    o.append(t(410, my + 5, f'вогник {MK["hole_mm"]:.0f} мм', 11, INK))

    # ввід кабелю: гермоввід у стінці, далі під землю в рукаві
    cy = y1 - 9
    o.append(box(x0 - 5, cy - 5, 10, 10, "#ffffff", INK, 1.5))
    o.append(leader(x0 - 5, cy + 6, 174, 303))
    o.append(t(176, 306, "гермоввід"))
    o.append(f'<polyline points="{x0-5:.0f},{cy:.0f} 92,{cy:.0f} 92,{gy}" '
             f'fill="none" stroke="{SIG}" stroke-width="2.5"/>')
    o.append(f'<polyline points="92,{gy} 92,342 50,342" fill="none" stroke="{SIG}" '
             f'stroke-width="2.5" stroke-dasharray="5 4" marker-end="url(#bxm-sig)"/>')
    o.append(t(48, 360, "кабель у рукаві під землею", 11, SIG))
    o.append(t(44, 378, "габарит ящика умовний — кейс ще не обраний"))


def top_view(o):
    """Вигляд згори: стрічка по периметру, катафоти на кутах, два конуси світла."""
    o.append(t(552, 86, "Вигляд згори", 12, INK, weight="600"))
    o.append(t(552, 104, "стрічка по периметру, катафоти на кутах"))

    bw, bd = mm(BOX["l_mm"]), mm(BOX["w_mm"])
    x0, y0 = 600, 165
    x1, y1 = x0 + bw, y0 + bd

    # смуга стрічки показана кільцем навколо контуру — у плані вона на ребрі
    o.append(box(x0 - 7, y0 - 7, bw + 14, bd + 14, FILL, LINE, 1.5))
    o.append(box(x0, y0, bw, bd, "#ffffff", INK, 1.8))

    # катафоти на чотирьох кутах
    rs = mm(REFL["h_mm"]) * 0.55
    for cx, cy in ((x0, y0), (x1 - rs, y0), (x0, y1 - rs), (x1 - rs, y1 - rs)):
        o.append(box(cx, cy, rs, rs, GHOST_F, INK, 1.5))
    o.append(t(x0 + bw / 2, y0 + bd / 2 + 4, "ящик станції", 12, INK, "middle"))

    # вогники в протилежних стінках: один світить угору по плану, другий униз
    up_x, dn_x = x1 - 40, x0 + 50
    o.append(f'<polygon points="{up_x},{y0} {up_x-34},{y0-45} {up_x+34},{y0-45}" '
             f'fill="{WARN}" opacity="0.18"/>')
    o.append(f'<polygon points="{dn_x},{y1} {dn_x-34},{y1+45} {dn_x+34},{y1+45}" '
             f'fill="{WARN}" opacity="0.18"/>')
    for mx, my in ((up_x, y0), (dn_x, y1)):
        o.append(f'<circle cx="{mx:.0f}" cy="{my:.0f}" r="5" fill="{WARN}" '
                 f'stroke="{INK}" stroke-width="1.5"/>')
    o.append(t(556, 140, "вогник світить назовні"))
    o.append(t(700, y1 + 29, f'{MARK["w_unit"]} Вт кожен'))
    o.append(t(552, y1 + 57, "два вогники — на протилежні стінки"))

    # ввід кабелю і напрямок на подіум
    cy = y1 - 30
    o.append(box(x1 - 4, cy - 6, 8, 12, "#ffffff", INK, 1.5))
    o.append(f'<line x1="{x1+4}" y1="{cy}" x2="892" y2="{cy}" stroke="{SIG}" '
             f'stroke-width="2.5" stroke-dasharray="5 4" marker-end="url(#bxm-sig)"/>')
    o.append(t(820, cy - 12, f'до подіуму {TRUNK["length_m"]} м', 11, SIG))


def detail(o):
    """Розріз: як вогник сидить у стінці — і чому саме так."""
    o.append(t(48, 418, "Розріз: як вогник сидить у стінці", 12, INK, weight="600"))

    wx0, wx1 = 300, 320
    hy0, hy1 = 486, 506          # отвір Ø12 мм у стінці
    o.append(box(wx0, 440, wx1 - wx0, hy0 - 440, FILL))
    o.append(box(wx0, hy1, wx1 - wx0, 568 - hy1, FILL))

    # промінь назовні
    o.append(f'<polygon points="276,496 212,472 212,520" fill="{WARN}" opacity="0.18"/>')
    o.append(t(108, 496, "світить назовні"))

    # голова вогника зовні
    o.append(box(276, 485, 24, 22, GHOST_F))
    o.append(f'<circle cx="288" cy="496" r="7" fill="{WARN}" opacity="0.5"/>')

    # силікон по стику зовні — акцентом, це головне на розрізі
    o.append(f'<polygon points="300,485 300,477 291,485" fill="{ACC}"/>')
    o.append(f'<polygon points="300,507 300,515 291,507" fill="{ACC}"/>')
    o.append(leader(258, 461, 297, 481))
    o.append(t(108, 458, "силікон зовні по стику", 11, ACC))

    # гвинтова ніжка з різьбою, прокладка і гайка зсередини
    o.append(box(300, 489, 56, 14, FILL, INK, 1.5))
    for tx in range(305, 357, 7):
        o.append(f'<line x1="{tx}" y1="489" x2="{tx}" y2="503" stroke="{INK}" '
                 f'stroke-width="1.5"/>')
    o.append(box(320, 484, 9, 24, GASKET, SIG, 1.5))
    o.append(box(331, 481, 16, 30))

    o.append(leader(370, 451, 312, 485))
    o.append(t(372, 448, f'отвір Ø{MK["hole_mm"]:.0f} мм у стінці'))
    o.append(leader(370, 469, 339, 480))
    o.append(t(372, 466, "гайка з прокладкою зсередини"))
    o.append(leader(374, 525, 354, 506))
    o.append(t(372, 528, "гвинтова ніжка з різьбою"))
    o.append(leader(192, 537, 298, 545))
    o.append(t(108, 540, "стінка ящика"))

    # хвіст на щит ящика — вогники живляться на місці, не з подіуму
    for wy in (493, 499):
        o.append(f'<line x1="356" y1="{wy}" x2="432" y2="{wy}" stroke="{INK}" '
                 f'stroke-width="1.5"/>')
    o.append(t(440, 487, f'{TAIL["awg"]} AWG до щита ящика'))

    o.append(t(600, 440, "Чому саме так", 12, INK, weight="600"))
    for i, s in enumerate((
            f'отвір Ø{MK["hole_mm"]:.0f} мм — найтонше місце ящика',
            "гайка з прокладкою зсередини притискає корпус,",
            "силікон зовні закриває стик по колу",
            f'без цього отвір стає входом для пилу {DUST[0]}-{DUST[1]} мкм,',
            "а він провідний і сідає просто на станцію",
            f'надлишковий тиск усередині {PA[0]}-{PA[1]} Па працює',
            "тільки поки корпус щільний")):
        o.append(t(600, 464 + i * 18, s))


def legend(o):
    """Легенда: мініатюра самого елемента плюс підпис — і розшифровка пунктирів."""
    y1, y2, y3 = 598, 620, 642
    o.append(f'<circle cx="52" cy="{y1-4}" r="5" fill="{WARN}" stroke="{INK}" '
             f'stroke-width="1.5"/>')
    o.append(t(64, y1, f'маркерний вогник {MK["hole_mm"]:.0f} мм · {MARK["w_unit"]} Вт · '
                       f'{MARK["qty"]} шт, аварійна група'))
    o.append(box(46, y2 - 12, 12, 16, GHOST_F, INK, 1.5))
    o.append(t(64, y2, f'катафот {REFL["w_mm"]:.0f}×{REFL["h_mm"]:.0f} мм · '
                       f'{REFL["qty_box"]} кути ящика'))
    o.append(box(44, y3 - 10, 16, 10, "#ffffff", INK, 1.5))
    o.append(t(64, y3, f'стрічка {TAPE["grade"]}, смуга {TAPE["width_mm"]:.0f} мм по периметру'))

    o.append(f'<line x1="500" y1="{y1-4}" x2="512" y2="{y1-4}" stroke="{SIG}" '
             f'stroke-width="2.5" stroke-dasharray="5 4"/>')
    o.append(t(518, y1, f'пунктир синій — кабель під землею, до подіуму '
                        f'{TRUNK["length_m"]} м'))
    o.append(f'<line x1="500" y1="{y2-4}" x2="512" y2="{y2-4}" stroke="{LINE}" '
             f'stroke-width="1.5" stroke-dasharray="4 6"/>')
    o.append(t(518, y2, "пунктир сірий — станція всередині ящика, орієнтир"))
    o.append(t(500, y3, "катафоти не заміняють активне світло — воно обовʼязкове"))


def svg():
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'width="100%" font-family="ui-monospace,Menlo,monospace">',
         f'<defs>'
         f'<marker id="bxm-sig" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
         f'markerHeight="7" orient="auto-start-reverse">'
         f'<path d="M0,0 L10,5 L0,10 z" fill="{SIG}"/></marker>'
         f'<marker id="bxm-sun" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
         f'markerHeight="7" orient="auto-start-reverse">'
         f'<path d="M0,0 L10,5 L0,10 z" fill="{WARN}"/></marker>'
         f'</defs>']
    o.append(t(W / 2, 24, "Ящик станції вночі: чим його видно і як сидить вогник",
               14, INK, "middle"))
    o.append(t(W / 2, 42, f'{MARK["qty"]} маркерні вогники по {MARK["w_unit"]} Вт · '
                          f'{REFL["qty_box"]} катафоти на кути · стрічка {TAPE["grade"]} '
                          f'по периметру', 11, DIM2, "middle"))
    o.append(t(W / 2, 58, f'ящик за {TRUNK["length_m"]} м від подіуму · правило Burning Man: '
                          f'обʼєкт має читатись за {VIS["m"]} м', 11, DIM2, "middle"))
    side_view(o)
    top_view(o)
    detail(o)
    legend(o)
    o.append("</svg>")
    return "\n".join(o)


def load_w():
    """Скільки бере пасивно-активна розмітка ящика — щоб число було видно і тут."""
    w = MARK["qty"] * MARK["w_unit"]
    return {"w": round(w, 2), "a": round(w / L["bus_v"], 3)}


def main():
    p = load_w()
    print(f'ящик {BOX["l_mm"]}×{BOX["w_mm"]}×{BOX["h_mm"]} мм (умовний) на підставці '
          f'{B["stand_mm"]} мм, за {TRUNK["length_m"]} м від подіуму')
    print(f'активно: {MARK["qty"]} × {MARK["w_unit"]} Вт = {p["w"]} Вт '
          f'({p["a"]} A на {L["bus_v"]:g} В), група {L["groups"][MARK["group"]]["label"]}')
    print(f'пасивно: {REFL["qty_box"]} катафоти {REFL["w_mm"]:.0f}×{REFL["h_mm"]:.0f} мм + '
          f'стрічка {TAPE["grade"]} {TAPE["width_mm"]:.0f} мм × {TAPE["length_m"]} м — '
          f'нуль ват, працюють при повному знеструмленні')
    print(f'посадка: отвір Ø{MK["hole_mm"]:.0f} мм, різьба Ø{MK["thread_mm"]:.0f} мм, '
          f'{MK["seal"]}')
    print(f'ввід кабелю: {GLAND}; хвіст живлення {TAIL["awg"]} AWG {TAIL["length_m"]} м')
    print(f'тепло: {AMB["playa_shade_c"]}°C у тіні проти {AMB["playa_sun_c"]}°C на сонці '
          f'при межі станції {AMB["station_limit_c"]}°C — звідси навіс і підставка')
    print(f'видимість за правилом: {VIS["ft"]} футів ≈ {VIS["m"]} м')
    (HERE / "box_marking.svg").write_text(svg())
    print("креслення: box_marking.svg")


if __name__ == "__main__":
    main()
