#!/usr/bin/env python3
"""
Ядро на спині в лоб: що всередині — і що з цього бачить глядач.

Головне питання по ядру словами не пояснити: всередині корпусу сидить плата з
двохсот сорока одної окремої крапки, а на спині робота має світитись рівне коло,
а не решето. Тому малюнок розрізаний навпіл по вертикалі:

  ліва половина  — сама плата зблизька: девʼять вкладених кілець, кожен діод
                   окремою крапкою, хвиля йде від центру назовні (так і світить
                   набір вкладених кілець — не по обіду, а від середини);
  права половина — те саме коло крізь біле вікно: та сама хвиля, але крапок уже
                   нема, лишається суцільне гало — скрізь, окрім крайньої смуги
                   між двома зовнішніми кільцями (чому саме там — нижче).

Це і є вся робота розсіювача, показана однією картинкою: геометрія однакова,
різниця тільки в тому, що між платою і оком стоїть 12 мм повітря і 1.6 мм
білого ASA.

Радіуси внутрішніх кілець продавець не публікує, тому вони не вписані руками, а
рахуються за правилом із бази (rings_radius_rule): діоди на всіх кільцях сидять
з тим самим кроком по дузі, отже r = n × крок / 2π. Для зовнішнього кільця це
сходиться з паспортними 172 мм, тож правило робоче й для решти.

Хвиля тут не абстрактна: це обраний режим ядра (effects.pick), і такт їй задає
period_s з тієї ж бази. Тому на сторінці ця картинка пульсує в один такт із
превʼю режимів поруч — інакше той самий «Пульс від центру» жив би на одній
сторінці з двома різними періодами.

І головне застереження. Правило «зазор проти кроку» діє у двох напрямках, а крок
у них різний. Уздовж кільця крок 9 мм, і 12 мм зазору дають рівне світло — права
половина справедливо намальована суцільним гало. Але проміжки МІЖ кільцями
нерівні, і між двома зовнішніми він удвічі більший; те саме правило бази дає там
уже «крапки вгадуються». Тому в цій крайній смузі гало не гладке: два останні
кільця проступають бусинами, смуга обведена і підписана числами. Малювати ідеал
там, де власні числа картинки його не обіцяють, — це обман глядача, а не стиль
(uniformity.radial_note у базі).

Усі розміри — lights/data/back_core.json через модель back_core.py. Тільки
stdlib: сайт збирається на CI без залежностей.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import back_core as bc

MOD = bc.module()
WIN_MM = bc.WIN["size_mm"]                    # вікно в панелі броні
BOARD_MM = MOD["size_mm"]                     # плата (зовнішнє кільце)
RIM_MM = (WIN_MM - BOARD_MM) / 2              # темний обід по колу
PITCH_MM = bc.pitch_mm(MOD)                   # крок між діодами по дузі
UNI = bc.uniformity(MOD)                      # чи зіллються крапки при зазорі
THICK_MM = bc.DIF["thickness_mm"]

# Полотно. viewBox без width/height — svg вставляється інлайном у сторінку і
# тягнеться по ширині колонки.
W, H = 720, 616
CX, CY = 360, 272
R_WIN = 190.0                                 # вікно на малюнку, px
SCALE = R_WIN / (WIN_MM / 2)                  # px на мм — один на всю картинку
R_BOARD = (BOARD_MM / 2) * SCALE

BG, LINE, DIM, GLOW = "#0b0e14", "#26436e", "#8e97a6", "#5b9bff"
INK, ACC, RIM = "#eaf1ff", "#e08b3e", "#1b2230"

# Хвиля на картинці — це обраний режим ядра, а не абстрактний перелив, тому
# і період їй задає база: та сама секунда, з якою пульсує превʼю режимів поруч
# на сторінці. TRAVEL і FADE аналога в базі не мають — це вже малярство.
FX = next(e for e in bc.D["effects"]["list"] if e["key"] == bc.D["effects"]["pick"])
CYCLE = FX["period_s"]   # повний такт ефекту: прохід від центру до обіду і пауза
TRAVEL = 0.72            # яку частку такту хвиля йде назовні
FADE = 0.30              # за яку частку такту крапка гасне після спалаху


def rings():
    """Кільця модуля: скільки діодів і на якому радіусі кожне.

    Центральний діод — це не кільце, у нього радіус нуль; решта рахується за
    правилом із бази. Заразом перевіряємо, що розкладка дає рівно стільки
    діодів, скільки стоїть у паспорті модуля."""
    layout = MOD["rings_layout"]
    if sum(layout) != MOD["diodes"]:
        raise ValueError(f'розкладка дає {sum(layout)}, '
                         f'а в паспорті модуля {diodes_label(MOD["diodes"])}')
    return [{"n": n, "r_mm": 0.0 if n == 1 else n * PITCH_MM / (2 * math.pi)}
            for n in layout]


def ring_steps_mm():
    """Відстані між сусідніми кільцями — від центру до зовнішнього."""
    r = [x["r_mm"] for x in rings()]
    return [b - a for a, b in zip(r, r[1:])]


def radial_uniformity():
    """Те саме правило «зазор проти кроку», але впоперек кілець, а не вздовж кільця.

    Крок у цих двох напрямках різний, тому й вердикт різний. Уздовж кільця
    діоди сидять через 9 мм, і 12 мм зазору дають рівне світло. А проміжки МІЖ
    кільцями нерівні, і найбільший з них — між двома зовнішніми: там того ж
    зазору вже не вистачає. Пороги не переписуємо, а віддаємо ту саму функцію
    моделі, підставивши їй більший крок, — щоб межа «рівно / вгадується»
    лишалась однією на весь проєкт (uniformity.comfort_ratio у базі)."""
    return bc.uniformity({**MOD, "pitch_mm": max(ring_steps_mm())})


def diodes_label(n):
    """«241 діод», але «60 діодів» — форма слова під число з бази.

    Раз число не вписане руками, то й закінчення вписувати руками не можна:
    поміняється chosen.module — і підпис поїде в неграматичність. Українське
    правило: одиниця в кінці (крім 11) тягне однину, 2-4 — «діоди», решта —
    «діодів»."""
    tail, hundred = n % 10, n % 100
    if tail == 1 and hundred != 11:
        word = "діод"
    elif 2 <= tail <= 4 and not 12 <= hundred <= 14:
        word = "діоди"
    else:
        word = "діодів"
    return f"{n} {word}"


def diodes():
    """Координати кожного діода в мм відносно центру плати.

    Кільця не зсунуті одне відносно одного: у наборів вкладених кілець діоди
    сходяться в промені, і саме так це виглядає на фото модуля."""
    out = []
    for k, ring in enumerate(rings()):
        n, r = ring["n"], ring["r_mm"]
        if n == 1:
            out.append((k, 0.0, 0.0))
            continue
        for i in range(n):
            a = -math.pi / 2 + 2 * math.pi * i / n
            out.append((k, r * math.cos(a), r * math.sin(a)))
    return out


def svg():
    """Дві половини одного кола: зліва плата, справа — вона ж крізь вікно."""
    rs = rings()
    steps = ring_steps_mm()
    rad = radial_uniformity()          # той самий зазор, але впоперек кілець
    r_out_px = rs[-1]["r_mm"] * SCALE
    travel_s = CYCLE * TRAVEL
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'font-family="ui-monospace,Menlo,monospace">']

    o.append(
        '<defs>'
        '<filter id="fd" x="-160%" y="-160%" width="420%" height="420%">'
        '<feGaussianBlur stdDeviation="3.4"/></filter>'
        '<filter id="fh" x="-40%" y="-40%" width="180%" height="180%">'
        '<feGaussianBlur stdDeviation="4"/></filter>'
        '<filter id="fw" x="-60%" y="-60%" width="220%" height="220%">'
        '<feGaussianBlur stdDeviation="9"/></filter>'
        '<radialGradient id="halo">'
        f'<stop offset="0" stop-color="{INK}" stop-opacity="0.95"/>'
        '<stop offset="0.32" stop-color="#a8c8ff" stop-opacity="0.78"/>'
        f'<stop offset="0.74" stop-color="{GLOW}" stop-opacity="0.5"/>'
        f'<stop offset="1" stop-color="{GLOW}" stop-opacity="0.2"/>'
        '</radialGradient>'
        f'<clipPath id="lf"><rect x="0" y="0" width="{CX}" height="{H}"/></clipPath>'
        f'<clipPath id="rt"><rect x="{CX}" y="0" width="{W - CX}" height="{H}"/></clipPath>'
        '</defs>')
    o.append(f'<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>')

    # Тіло вікна: темна шайба і по краю обід, під яким діодів уже нема.
    o.append(f'<circle cx="{CX}" cy="{CY}" r="{R_WIN:.1f}" fill="#0f141c"/>')
    o.append(f'<circle cx="{CX}" cy="{CY}" r="{(R_BOARD + R_WIN) / 2:.1f}" fill="none" '
             f'stroke="{RIM}" stroke-width="{R_WIN - R_BOARD:.1f}"/>')

    # ---- ліва половина: сама плата
    o.append('<g clip-path="url(#lf)">')
    for ring in rs[1:]:
        o.append(f'<circle cx="{CX}" cy="{CY}" r="{ring["r_mm"] * SCALE:.1f}" '
                 f'fill="none" stroke="#151d29"/>')
    for k, mx, my in diodes():
        if mx > 0.01:                      # права половина — не наша, там гало
            continue
        x, y = CX + mx * SCALE, CY + my * SCALE
        # Хвиля йде від центру назовні: кільце спалахує тим пізніше, чим воно
        # далі від середини, і гасне за той самий час, що й усі інші.
        peak_s = travel_s * rs[k]["r_mm"] / rs[-1]["r_mm"]
        anim = (f'<animate attributeName="opacity" values="1;0.16;0.16" '
                f'keyTimes="0;{FADE};1" dur="{CYCLE}s" repeatCount="indefinite" '
                f'begin="{peak_s - CYCLE:.3f}s"/>')
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.3" fill="{LINE}"/>')
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6.2" fill="{GLOW}" '
                 f'filter="url(#fd)" opacity="0.16">{anim}</circle>')
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="{INK}" '
                 f'opacity="0.16">{anim}</circle>')
    o.append('</g>')

    # ---- права половина: те саме крізь вікно
    o.append('<g clip-path="url(#rt)">')
    # Гало не доходить до краю плати рівно на розмиття: інакше воно вилізло б на
    # обід, а той під світло не працює — під ним діодів уже нема.
    o.append(f'<circle cx="{CX}" cy="{CY}" r="{R_BOARD - 7:.1f}" fill="url(#halo)" '
             f'filter="url(#fh)">'
             f'<animate attributeName="opacity" values="0.82;1;0.82" '
             f'keyTimes="0;{TRAVEL};1" dur="{CYCLE}s" repeatCount="indefinite" '
             f'begin="-{CYCLE}s"/></circle>')
    # Та сама хвиля, що зліва біжить по кільцях, тут іде суцільним фронтом:
    # у середині кола крок між кільцями крізь вікно вже не читається.
    o.append(f'<circle cx="{CX}" cy="{CY}" r="0" fill="none" stroke="{INK}" '
             f'stroke-width="16" filter="url(#fw)" opacity="0">'
             f'<animate attributeName="r" values="0;{r_out_px:.1f};{r_out_px:.1f}" '
             f'keyTimes="0;{TRAVEL};1" dur="{CYCLE}s" repeatCount="indefinite" '
             f'begin="-{CYCLE}s"/>'
             f'<animate attributeName="opacity" values="0.5;0.42;0;0" '
             f'keyTimes="0;{TRAVEL * 0.8:.2f};{TRAVEL};1" dur="{CYCLE}s" '
             f'repeatCount="indefinite" begin="-{CYCLE}s"/></circle>')
    # ...але не до самого краю. Між двома ЗОВНІШНІМИ кільцями проміжок найбільший,
    # і за тим самим правилом бази того ж зазору на нього вже не вистачає
    # (radial_uniformity() рахує це число). Тому в цій смузі гало не гладке:
    # два останні кільця ледь проступають бусинами.
    # Малювати тут ідеально рівне світло означало б сперечатися з власним числом
    # під картинкою (uniformity.radial_note).
    for k, mx, my in diodes():
        if mx < -0.01 or k < len(rs) - 2:
            continue
        x, y = CX + mx * SCALE, CY + my * SCALE
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6.0" fill="{INK}" '
                 f'filter="url(#fd)" opacity="0.2"/>')
    r_band = (rs[-2]["r_mm"] + rs[-1]["r_mm"]) / 2 * SCALE
    o.append(f'<path d="M {CX} {CY - r_band:.1f} A {r_band:.1f} {r_band:.1f} 0 0 1 '
             f'{CX} {CY + r_band:.1f}" fill="none" stroke="{ACC}" stroke-width="1.1" '
             f'stroke-dasharray="3 5" opacity="0.7"/>')
    o.append('</g>')

    # край плати і край вікна — поверх обох половин, щоб лінії лишились чіткі
    o.append(f'<circle cx="{CX}" cy="{CY}" r="{R_BOARD:.1f}" fill="none" '
             f'stroke="{LINE}" stroke-dasharray="3 4"/>')
    o.append(f'<circle cx="{CX}" cy="{CY}" r="{R_WIN:.1f}" fill="none" '
             f'stroke="{INK}" stroke-width="2"/>')
    o.append(f'<line x1="{CX}" y1="{CY - R_WIN - 8:.0f}" x2="{CX}" y2="{CY + R_WIN + 8:.0f}" '
             f'stroke="{DIM}" stroke-dasharray="2 5"/>')

    # ---- підписи
    o.append(f'<text x="{CX}" y="26" text-anchor="middle" font-size="13" fill="{INK}">'
             f'Ядро на спині в лоб: вікно Ø{WIN_MM:g} мм, за ним плата Ø{BOARD_MM:g} мм '
             f'на {diodes_label(MOD["diodes"])}</text>')
    o.append(f'<text x="{CX}" y="44" text-anchor="middle" font-size="10" fill="{DIM}">'
             f'одне й те саме коло: зліва — сама плата, справа — вона ж крізь '
             f'{THICK_MM} мм білого пластику</text>')
    o.append(f'<text x="{CX - 14}" y="70" text-anchor="end" font-size="10" fill="{GLOW}">'
             f'крапки на платі</text>')
    # Не просто «рівне гало»: рівне воно в середині, а на краю — з застереженням,
    # яке тут же поруч і намальоване. Обіцяти в підписі більше, ніж показує
    # малюнок, не можна.
    o.append(f'<text x="{CX + 14}" y="70" font-size="10" fill="{GLOW}">'
             f'гало у вікні — рівне, крім краю</text>')

    # виноска на обід
    px = CX + (R_BOARD + R_WIN) / 2 * math.cos(math.radians(-38))
    py = CY + (R_BOARD + R_WIN) / 2 * math.sin(math.radians(-38))
    o.append(f'<polyline points="{px:.1f},{py:.1f} 600,118 {W - 24},118" fill="none" '
             f'stroke="{ACC}" stroke-width="1.2"/>')
    o.append(f'<text x="{W - 24}" y="112" text-anchor="end" font-size="9.5" fill="{ACC}">'
             f'темний обід {RIM_MM:g} мм</text>')

    # виноска на зовнішнє кільце
    qx = CX + r_out_px * math.cos(math.radians(198))
    qy = CY + r_out_px * math.sin(math.radians(198))
    o.append(f'<polyline points="{qx:.1f},{qy:.1f} 150,196 24,196" fill="none" '
             f'stroke="{LINE}" stroke-width="1.2"/>')
    o.append(f'<text x="24" y="190" font-size="9.5" fill="{DIM}">'
             f'зовнішнє кільце — {diodes_label(rs[-1]["n"])}</text>')

    # виноска на крайню смугу: саме там гало намальоване з бусинами
    bx = CX + r_band * math.cos(math.radians(28))
    by = CY + r_band * math.sin(math.radians(28))
    o.append(f'<polyline points="{bx:.1f},{by:.1f} 560,400 {W - 24},400" fill="none" '
             f'stroke="{ACC}" stroke-width="1.2" stroke-dasharray="3 5"/>')
    o.append(f'<text x="{W - 24}" y="414" text-anchor="end" font-size="9.5" fill="{ACC}">'
             f'край: між кільцями {max(steps):.1f} мм</text>')
    o.append(f'<text x="{W - 24}" y="428" text-anchor="end" font-size="9.5" fill="{ACC}">'
             f'зазор {UNI["gap_mm"]:g} мм = {rad["ratio"]:.2f} кроку</text>')

    # розміри: плата ближче до фігури, вікно під нею
    for y, half, label, below in (
            (CY + R_WIN + 24, R_BOARD, f'Ø{BOARD_MM:g} мм — плата, '
                                       f'{diodes_label(MOD["diodes"])}', False),
            (CY + R_WIN + 48, R_WIN, f'Ø{WIN_MM:g} мм — вікно в панелі броні', True)):
        x1, x2 = CX - half, CX + half
        o.append(f'<line x1="{x1:.1f}" y1="{y:.0f}" x2="{x2:.1f}" y2="{y:.0f}" '
                 f'stroke="{LINE}"/>')
        for x in (x1, x2):
            o.append(f'<line x1="{x:.1f}" y1="{y - 5:.0f}" x2="{x:.1f}" y2="{y + 5:.0f}" '
                     f'stroke="{LINE}"/>')
        o.append(f'<text x="{CX}" y="{y + (15 if below else -8):.0f}" text-anchor="middle" '
                 f'font-size="10" fill="{DIM}">{label}</text>')

    o.append(f'<text x="24" y="{H - 70}" font-size="10" fill="{DIM}">'
             f'{MOD["rings"]} вкладених кілець '
             f'{"+".join(str(r["n"]) for r in rs)} = {diodes_label(MOD["diodes"])} · '
             f'крок по дузі {PITCH_MM:.1f} мм · між кільцями '
             f'{min(steps):.1f}…{max(steps):.1f} мм</text>')
    o.append(f'<text x="24" y="{H - 52}" font-size="10" fill="{DIM}">'
             f'обід {RIM_MM:g} мм по колу: вікно на {WIN_MM - BOARD_MM:g} мм ширше за плату, '
             f'щоб край світної частини не впирався в самі діоди</text>')
    # Два рядки, а не один: правило зазору дає різний вердикт уздовж кільця і
    # впоперек кілець, і другий вердикт гірший. Написати тільки перший означало б
    # обіцяти рівне світло там, де власні числа картинки його не обіцяють.
    o.append(f'<text x="24" y="{H - 34}" font-size="10" fill="{DIM}">'
             f'зазор до вікна {UNI["gap_mm"]:g} мм: уздовж кільця це '
             f'{UNI["ratio"]:.2f} кроку ({PITCH_MM:.1f} мм) → {UNI["verdict"]}, '
             f'справа крапок і не видно</text>')
    o.append(f'<text x="24" y="{H - 16}" font-size="10" fill="{ACC}">'
             f'а між двома зовнішніми кільцями {max(steps):.1f} мм → '
             f'{rad["ratio"]:.2f} → {rad["verdict"]}; заміряти, коли приїде</text>')
    o.append("</svg>")
    return "\n".join(o)


def main():
    rs, steps = rings(), ring_steps_mm()
    rad = radial_uniformity()
    print(f'вікно Ø{WIN_MM:g} мм · плата Ø{BOARD_MM:g} мм · обід {RIM_MM:g} мм по колу')
    print(f'{MOD["rings"]} кілець {"+".join(str(r["n"]) for r in rs)} = '
          f'{diodes_label(MOD["diodes"])} · крок по дузі {PITCH_MM:.1f} мм')
    for r in rs:
        print(f'  {diodes_label(r["n"]):>10}  r {r["r_mm"]:5.1f} мм  '
              f'Ø{r["r_mm"] * 2:5.1f} мм')
    print(f'між кільцями {min(steps):.1f}…{max(steps):.1f} мм '
          f'(в середньому {sum(steps) / len(steps):.1f})')
    print(f'зазор {UNI["gap_mm"]:g} мм уздовж кільця = {UNI["ratio"]:.2f} кроку '
          f'({PITCH_MM:.1f} мм) → {UNI["verdict"]}')
    print(f'той самий зазор упоперек кілець = {rad["ratio"]:.2f} кроку '
          f'({rad["pitch_mm"]:.1f} мм між двома зовнішніми) → {rad["verdict"]}')
    print(f'хвиля — режим «{FX["name"]}», такт {CYCLE:g} с (effects.pick з бази)')
    (Path(__file__).resolve().parent / "back_core_face.svg").write_text(svg())
    print("креслення: back_core_face.svg")


if __name__ == "__main__":
    main()
