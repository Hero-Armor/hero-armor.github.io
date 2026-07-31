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

ARM = next(f for f in P["fixtures"] if f["id"] == "water_arms")
ADDR = P["addressable"]

N = ARM["qty"]
RAY_M = ARM["ray_m"]                  # промінь: край подіуму → центр
TURN_M = ARM["turn_m"]                # заворот: 1/8 кола до основи наступного
ARM_M = ARM["length_m"]               # рукав цілком, одна суцільна стрічка
RING_M = ARM["ring_m"]                # коло = сума восьми заворотів
PIX_M = ARM["pixel_m"]                # піксель WS2811 = 3 діоди
R_RING_M = RING_M / (2 * pi)
TOTAL_M = N * ARM_M
DUTY = ADDR["duty_animation"]
PER_ARM = int(round(ARM_M / PIX_M))   # скільки пікселів у рукаві
CYCLE_S = 3.2                         # один прохід фронту по рукаву


def pixels():
    """Координати кожного пікселя вздовж рукава, від зовнішнього кінця до кінця
    заворота — у метрах відносно центру подіуму.

    Спершу пікселі йдуть по прямій до центру, а після променя лягають на дугу:
    та сама послідовність, у якій по них побіжить сигнал."""
    out = []
    for k in range(N):
        a0 = -pi / 2 + 2 * pi * k / N
        arm = []
        for i in range(PER_ARM):
            d = (i + 0.5) * PIX_M                 # відстань від зовнішнього кінця
            if d <= RAY_M:
                r, ang = R_RING_M + (RAY_M - d), a0
            else:
                r, ang = R_RING_M, a0 + (d - RAY_M) / R_RING_M
            arm.append((r * cos(ang), r * sin(ang)))
        out.append(arm)
    return out


def svg():
    """Схема в тому вигляді, як Іван її затвердив ще в червні (podium_anim.mp4):
    нічний фон, окремі пікселі, комета з хвостом, потік від краю до центру і
    далі в заворот. Тут вона жива і рахується з тих самих даних, що й числа."""
    W = H = 560
    CX = CY = 280
    scale = 205 / (R_RING_M + RAY_M)
    r_out_px = (R_RING_M + RAY_M) * scale
    bg, dim, core, glow_c = "#0b0e14", "#26436e", "#eaf1ff", "#5b9bff"
    txt, txt2 = "#dfe4ec", "#8e97a6"
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'font-family="ui-monospace,Menlo,monospace">',
         f'<defs><filter id="ng" x="-70%" y="-70%" width="240%" height="240%">'
         f'<feGaussianBlur stdDeviation="4.5"/></filter></defs>',
         f'<rect width="{W}" height="{H}" rx="8" fill="{bg}"/>']

    # настил подіуму — орієнтир, не траса
    o.append(f'<circle cx="{CX}" cy="{CY}" r="{r_out_px+16:.0f}" fill="none" '
             f'stroke="#1c222c" stroke-dasharray="4 6"/>')

    # Хвіст комети = та сама частка рукава, якою модель рахує споживання: що
    # видно на схемі, те й стоїть у ваттах.
    tail_px = max(1, round(DUTY * PER_ARM))
    # Хвіст не має «загортатись» на початок рукава: поки фронт іде по променю,
    # у заворотi не повинно світитись нічого (Іван, 31.07). Тому цикл ділимо на
    # дві частини — прохід голови від краю до кінця завороту і час, за який
    # хвіст доганяє і гасне. Без цього останні пікселі догоряли б уже тоді, коли
    # на промені стартував наступний фронт.
    fade = tail_px / PER_ARM
    travel_s = CYCLE_S / (1 + fade)
    fade_key = (fade * travel_s) / CYCLE_S
    arms = pixels()
    # Усі вісім рукавів у фазі: піксель з тим самим номером спалахує одночасно
    # в кожному рукаві. Зсув по часу лише вздовж рукава — через begin.
    for arm in arms:
        for i, (mx, my) in enumerate(arm):
            x, y = CX + mx * scale, CY + my * scale
            # Піксель спалахує, коли до нього доходить голова, і гасне за час
            # хвоста. Негативний begin означає, що анімація вже триває з моменту
            # завантаження — так усі вісім рукавів ідуть у фазі.
            peak_s = travel_s * i / PER_ARM
            anim = (f'<animate attributeName="opacity" values="1;0.12;0.12" '
                    f'keyTimes="0;{fade_key:.3f};1" dur="{CYCLE_S}s" '
                    f'repeatCount="indefinite" begin="{peak_s - CYCLE_S:.3f}s"/>')
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.1" fill="{dim}"/>')
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="{glow_c}" '
                     f'filter="url(#ng)" opacity="0.12">{anim}</circle>')
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="{core}" '
                     f'opacity="0.12">{anim}</circle>')

    # вхід живлення і місце різу — зовнішній кінець кожного рукава
    for arm in arms:
        mx, my = arm[0]
        x, y = CX + mx * scale, CY + my * scale
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="none" '
                 f'stroke="#e08b3e" stroke-width="1.6"/>')

    o.append(f'<text x="{CX}" y="26" text-anchor="middle" font-size="13" fill="{txt}">'
             f'{N} рукавів по {ARM_M:.2f} м: промінь {RAY_M:.2f} + заворот {TURN_M:.2f}</text>')
    o.append(f'<text x="{CX}" y="43" text-anchor="middle" font-size="10" fill="{txt2}">'
             f'окремого кільця нема: коло {RING_M:.2f} м складають вісім заворотів</text>')
    o.append(f'<text x="{CX}" y="58" text-anchor="middle" font-size="10" fill="{txt2}">'
             f'{PER_ARM} пікселів на рукав ({PIX_M*1000:.0f} мм = 3 діоди) · '
             f'разом {TOTAL_M:.2f} м</text>')
    o.append(f'<circle cx="34" cy="{H-38}" r="6" fill="none" stroke="#e08b3e" stroke-width="1.6"/>')
    o.append(f'<text x="48" y="{H-34}" font-size="10" fill="{txt2}">'
             f'вхід живлення і місце різу</text>')
    o.append(f'<text x="34" y="{H-16}" font-size="10" fill="{txt2}">'
             f'хвіст комети = {DUTY*100:.0f}% рукава — з цієї ж частки рахуються ватти</text>')
    o.append("</svg>")
    return "\n".join(o)


def blocked():
    """Що саме стоїть через незроблений замір — щоб це було видно й тут, і на
    сторінці, а не тільки в голові."""
    mt = I["measure_task"]
    return None if mt["status"] == "закрито" else f'{mt["title"]}: {mt["unblocks"]}'


def main():
    print(f'{N} рукавів × {ARM_M} м (промінь {RAY_M} + заворот {TURN_M}) = {TOTAL_M:.2f} м')
    print(f'коло {RING_M} м = {N} × {TURN_M} м заворотів · радіус {R_RING_M*1000:.0f} мм '
          f'· фронт {DUTY*100:.0f}%')
    for j in I["joints"]:
        print(f'  {j["where"]:32} {j["what"]}  [{j["status"]}]')
    if blocked():
        print(f'  ЧЕКАЄ: {blocked()}')
    (Path(__file__).resolve().parent / "strip_layout.svg").write_text(svg())
    print("креслення: strip_layout.svg")


if __name__ == "__main__":
    main()
