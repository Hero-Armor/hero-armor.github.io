#!/usr/bin/env python3
"""
План стрічки в подіумі: як іде лінія, куди біжить вода, де живлення і різи.

Словами це пояснювати довго, а на плані видно за секунду: вісім променів від
краю до центру, кожен заходить у коло заворотом вправо і встик упирається в
основу наступного — тому коло замкнуте без зазорів. Біжучий фронт іде від
зовнішнього кінця променя до центру; саме він і світиться, а не вся лінія —
через це стрічка бере набагато менше, ніж здається з довжини.

Малюнок анімований: біла ділянка бігає по рукаву, і її довжина — це та сама
частка, якою модель рахує споживання. Тобто на плані видно рівно те, що
стоїть у числах.

Геометрія береться з lights/data/params.json (довжини кола і променя),
підписи і монтаж — з lights/data/strip_install.json. Тільки stdlib.
"""

import json
from math import cos, pi, sin
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
P = json.loads((DATA / "params.json").read_text())
I = json.loads((DATA / "strip_install.json").read_text())

RAYS = next(f for f in P["fixtures"] if f["id"] == "water_rays")
RING = next(f for f in P["fixtures"] if f["id"] == "water_ring")
ADDR = P["addressable"]

N = RAYS["qty"]
RAY_M = RAYS["length_m"]
RING_M = RING["length_m"]
R_RING_M = RING_M / (2 * pi)          # радіус кола з його ж довжини
TOTAL_M = RING_M + N * RAY_M
DUTY = ADDR["duty_animation"]


def svg():
    W = H = 520
    CX = CY = 260
    # масштаб: від центру до зовнішнього кінця променя плюс поле під підписи
    scale = 190 / (R_RING_M + RAY_M)
    r_in = R_RING_M * scale
    r_out = (R_RING_M + RAY_M) * scale
    ink, line, acc, sig = "#24231d", "#c9c6ba", "#b35b1e", "#3d6f96"
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'font-family="ui-monospace,Menlo,monospace">']

    # настил подіуму — тільки орієнтир, не траса
    o.append(f'<circle cx="{CX}" cy="{CY}" r="{r_out+14:.0f}" fill="none" '
             f'stroke="{line}" stroke-dasharray="4 5"/>')


    # Рукав = промінь + його заворот по колу вправо, рівно до основи наступного
    # променя. Тому і малюємо його одним шляхом: фронт пробігає промінь до
    # центру і без розриву йде дугою — так само, як побіжить у залізі.
    ang = lambda k: -pi / 2 + 2 * pi * k / N
    arms = []
    for k in range(N):
        a, b = ang(k), ang(k + 1)
        x1, y1 = CX + r_out * cos(a), CY + r_out * sin(a)
        x2, y2 = CX + r_in * cos(a), CY + r_in * sin(a)
        x3, y3 = CX + r_in * cos(b), CY + r_in * sin(b)
        arms.append((f'M {x1:.1f} {y1:.1f} L {x2:.1f} {y2:.1f} '
                     f'A {r_in:.1f} {r_in:.1f} 0 0 1 {x3:.1f} {y3:.1f}', x1, y1))

    for d, _, _ in arms:
        o.append(f'<path d="{d}" fill="none" stroke="{acc}" stroke-width="6" '
                 f'stroke-linecap="round" opacity=".3"/>')
    # Усі вісім рукавів рухаються ОДНАКОВО: один і той самий момент старту і
    # однакова довжина шляху (pathLength=100 нормує промінь+дугу), тому фронти
    # ідуть паралельно, а не врозбій.
    for d, _, _ in arms:
        o.append(
            f'<path d="{d}" fill="none" stroke="#fff" stroke-width="6" '
            f'stroke-linecap="round" pathLength="100" '
            f'stroke-dasharray="{DUTY*100:.0f} {100-DUTY*100:.0f}">'
            f'<animate attributeName="stroke-dashoffset" values="100;0" '
            f'dur="2.6s" repeatCount="indefinite" begin="0s"/></path>')
    # точка входу живлення і різу — на зовнішньому кінці кожного рукава
    for _, x1, y1 in arms:
        o.append(f'<circle cx="{x1:.1f}" cy="{y1:.1f}" r="4.5" fill="#fff" '
                 f'stroke="{sig}" stroke-width="2"/>')

    # стрілка напрямку — на одному промені, щоб не рябіло
    a = ang(0)
    mx, my = CX + (r_in + r_out) / 2 * cos(a), CY + (r_in + r_out) / 2 * sin(a)
    o.append(f'<polygon points="{mx-5:.0f},{my-9:.0f} {mx+5:.0f},{my-9:.0f} {mx:.0f},{my+1:.0f}" '
             f'fill="{ink}"/>')
    o.append(f'<text x="{mx+10:.0f}" y="{my-2:.0f}" font-size="10" fill="{ink}">'
             f'до центру, далі заворотом</text>')

    o.append(f'<text x="{CX}" y="26" text-anchor="middle" font-size="13" fill="{ink}">'
             f'Зірка «біжучої води»: {N} променів по {RAY_M:.2f} м + коло {RING_M:.2f} м</text>')
    o.append(f'<text x="{CX}" y="44" text-anchor="middle" font-size="10" fill="#6b675c">'
             f'разом {TOTAL_M:.2f} м · світиться тільки фронт, {DUTY*100:.0f}% довжини</text>')
    o.append(f'<circle cx="40" cy="{H-30}" r="4.5" fill="#fff" stroke="{sig}" stroke-width="2"/>')
    o.append(f'<text x="52" y="{H-26}" font-size="10" fill="#6b675c">'
             f'вхід живлення і місце різу — на зовнішньому кінці рукава</text>')
    o.append("</svg>")
    return "\n".join(o)


def blocked():
    """Що саме стоїть через незроблений замір — щоб це було видно й тут, і на
    сторінці, а не тільки в голові."""
    mt = I["measure_task"]
    return None if mt["status"] == "закрито" else f'{mt["title"]}: {mt["unblocks"]}'


def main():
    print(f'{N} променів × {RAY_M} м + коло {RING_M} м = {TOTAL_M:.2f} м')
    print(f'радіус кола {R_RING_M*1000:.0f} мм · фронт {DUTY*100:.0f}%')
    for j in I["joints"]:
        print(f'  {j["where"]:32} {j["what"]}  [{j["status"]}]')
    if blocked():
        print(f'  ЧЕКАЄ: {blocked()}')
    (Path(__file__).resolve().parent / "strip_layout.svg").write_text(svg())
    print("креслення: strip_layout.svg")


if __name__ == "__main__":
    main()
