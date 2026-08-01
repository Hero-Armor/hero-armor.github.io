#!/usr/bin/env python3
"""
Розріз ядра збоку: чому плата стоїть на 12 мм углиб, а не впритул до вікна.

Питання виникає в кожного, хто бачить вузол уперше: якщо плата світить, то чим
ближче вона до вікна, тим яскравіше — навіщо ховати її вглиб і робити корпус
товщим? Відповідь не в яскравості, а в тому, ЩО саме видно зовні. Діоди сидять
з кроком 9 мм, кожен світить своїм конусом, і поки конуси сусідів не встигли
перекритись, на вікні лишаються окремі крапки. Зазор — це і є та відстань, на
якій крапки встигають злитись.

Тому картинка складена з двох однакових розрізів у ОДНОМУ масштабі:

  ліворуч  «як треба»                — зазор 12 мм з бази;
  праворуч «якщо притиснути впритул» — зазор 3.5 мм (плата просто на бобишках).

Усе інше в них однакове, тож різницю дає рівно одне число. Зверху над кожним
розрізом — порахована яскравість уздовж вікна: у робочому варіанті це рівна
лінія, у поганому — хвиля з провалами між діодами.

Як рахується яскравість. Кожен діод світить за законом Ламберта: E ~ cos^m(кут)
поділити на відстань², де показник m виводиться з паспортного кута світіння
WS2812B (120° → m = 1). Складаємо внески ряду діодів уздовж радіуса плати і
дивимось на площину ВНУТРІШНЬОЇ поверхні вікна — тобто на картинку ДО того, як
її підмиє саме біле ASA. Розсіювання в пластику навмисно не враховане: справжня
нерівність буде трохи менша за пораховану, і запас іде в наш бік.

Друге, що видно на розрізі і чого не видно в тексті: вікно — не накладка на
готовий корпус. Це ділянка тієї самої панелі броні, у якій сендвіч 5 мм
(1.2 + порожнина 2.6 + 1.2) переходить в одну суцільну стінку 1.6 мм.

ЩО САМЕ В МАСШТАБІ. Один масштаб S px/мм по обох осях тримають усі тіла:
панель, порожнина сендвіча, стінка вікна, зазор, плата (pcb_mm) і корпус діода
(diode_mm × diode_h_mm). Не в масштабі рівно дві речі, і обидві не є розміром:
розмиті ореоли над діодами (це «горить», а не габарит) і крапка на висоті
сходження конусів. Виносні розміри показують саме те, що підписано: полиця
«поле» починається на краю світного кола, риска «зазор» — на ЗАДНІЙ поверхні
вікна, а не на зовнішній поверхні броні (інакше в неї потрапляє ще й товщина
вікна, і в поганій половині розмір роздувається на 46%).

Оптика рахується від площини плати, хоч корпус діода тепер намальований своїми
1.6 мм. Це свідомо: правило рівності в базі (uniformity) і back_core.uniformity()
міряють зазор саме від плати, і схема не має права рахувати інакше за модель,
на яку сама ж посилається. Різниця в 1.6 мм задокументована в базі
(modules.ring241._diode_h_note) — 1.33 кроку від плати проти 1.16 від світної
поверхні, обидва вище comfort_ratio.

Межі графіка яскравості теж не вибрані на око, а зняті з самих кривих
(band_limits): доти нижня межа стояла вище справжнього мінімуму поганої
половини, десяток точок лягав плоскою поличкою на підлогу графіка, і провал
читався як «яскравість стала», а не «пішла вниз». Довгі підписи розбиті на
рядки заздалегідь (_wrap) із запасом на англійський переклад — сторінка
двомовна, і рядок, який в українській ледь влазить, в англійській вилазить
за рамку.

Усі розміри — lights/data/back_core.json через модель back_core.py, вердикт про
рівність дає back_core.uniformity(). Тільки stdlib: CI збирає сайт без залежностей.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import back_core as bc

MOD = bc.module()
SHELL = bc.D["shell"]

PITCH = bc.pitch_mm(MOD)                      # крок між діодами, мм
GAP = bc.DIF["gap_mm"]                        # робочий зазор плата → вікно
GAP_BAD = bc.DIF["gap_bad_mm"]                # поганий варіант: плата впритул
THICK = bc.DIF["thickness_mm"]                # товщина вікна, одна стінка
SANDWICH = SHELL["sandwich_mm"]               # панель броні цілком
SKIN = SHELL["skin_mm"]                       # одна оболонка сендвіча
CORE = SHELL["core_mm"]                       # порожнина між оболонками
BEZEL = bc.WIN["bezel_mm"]                    # поле, яким вікно лягає на корпус
WIN_MM = bc.WIN["size_mm"]                    # світне коло
BOARD_MM = MOD["size_mm"]                     # плата
PCB_MM = MOD["pcb_mm"]                        # товщина плати, FR4
DIODE_MM = MOD["diode_mm"]                    # корпус діода, 5050 — сторона
DIODE_H_MM = MOD["diode_h_mm"]                # корпус діода — висота над платою
RIM_MM = (WIN_MM - BOARD_MM) / 2              # обід: від краю вікна до краю плати

BEAM = bc.UNI["beam_deg"]                     # паспортний кут світіння діода
HALF = math.radians(BEAM / 2)
# Показник Ламберта з кута світіння: у кутi beam/2 яскравість падає вдвічі.
M_EXP = math.log(0.5) / math.log(math.cos(HALF))
# На якій висоті над платою конуси сусідніх діодів уперше перекриваються.
CROSS_MM = PITCH / (2 * math.tan(HALF))

# Ряд діодів уздовж радіуса плати: від краю до центру з тим самим кроком. Плата
# насправді складена з вкладених кілець, але правило рівності бере рівно один
# крок, тому в розрізі ряд — чесне спрощення.
D0_MM = RIM_MM + DIODE_MM / 2                 # перший діод від краю вікна
N_ROW = int((BOARD_MM / 2 - DIODE_MM) // PITCH) + 1
DIODES_MM = [D0_MM + i * PITCH for i in range(N_ROW)]
SHOWN = 5                                     # скільки діодів влазить у фрагмент


def profile(gap_mm, x_mm):
    """Яскравість на внутрішній поверхні вікна в точці x (сума по всіх діодах).

    Один діод дає E ~ cos^m(кут) / відстань². Це та сама формула, з якої
    виводиться правило «зазор ≥ крок»: збільшуючи зазор, ми не гасимо світло, а
    розмазуємо внесок кожного діода на ширшу пляму, і плями перекриваються."""
    p = (M_EXP + 2) / 2
    return sum(gap_mm ** M_EXP / ((x_mm - d) ** 2 + gap_mm ** 2) ** p
               for d in DIODES_MM)


def ripple(gap_mm, span=201):
    """Наскільки нерівне світло в СЕРЕДИНІ вікна, у частках від середньої.

    Беремо один крок між двома діодами подалі від краю (край темніший сам по
    собі, і це інша історія) і дивимось розмах: (макс−мін)/(макс+мін). Нуль —
    рівне поле, десятки відсотків — око бачить окремі плями."""
    a, b = DIODES_MM[2], DIODES_MM[3]
    vals = [profile(gap_mm, a + (b - a) * k / (span - 1)) for k in range(span)]
    mx, mn = max(vals), min(vals)
    mean = sum(vals) / len(vals)
    return dict(max=mx, min=mn, mean=mean, pct=100 * (mx - mn) / (mx + mn))


def case(gap_mm):
    """Один із двох розрізів одним обʼєктом: зазор, вердикт, нерівність."""
    u = bc.uniformity(MOD, gap_mm=gap_mm)
    r = ripple(gap_mm)
    return dict(u, ripple_pct=r["pct"], mean=r["mean"],
                left_mm=gap_mm - CROSS_MM)


# --------------------------------------------------------------------- полотно
S = 7.2                                   # px на мм, однаковий по обох осях
X0_MM = -(BEZEL + 6)                      # ліворуч від краю вікна — суцільна панель
X1_MM = D0_MM + (SHOWN - 1) * PITCH + DIODE_MM / 2 + 2   # праворуч — розрив
PANEL_W = (X1_MM - X0_MM) * S
MARGIN, MIDGAP = 22.0, 36.0
W = 2 * PANEL_W + 2 * MARGIN + MIDGAP
CURVE_N = 160                             # точок на криву яскравості

BG, INK, DIM = "#0b0e14", "#eaf1ff", "#8e97a6"
GLOW, ACC, LINE = "#5b9bff", "#e08b3e", "#26436e"
MAT, WALL = "#1b2230", "#b9c9e0"

# Ширина одного знака в частках від кегля. Не на око: заміряно в браузері по
# самому ж кресленню (getComputedTextLength на всіх <text> дає 0.6011…0.6021
# em) — ui-monospace, Menlo і підмінний DejaVu Sans Mono усі дають однакову
# ширину і для кирилиці, і для «→», «≥», «Ø».
CHAR_W = 0.602
# Запас на англійський переклад. Теж не на око: 974 пари з памʼяті перекладу
# проєкту (site/i18n/tm.json, рядки від 40 знаків) дали медіану 1.02, 95-й
# процентиль 1.21, найдовший випадок 1.54. Беремо 1.25 — покриває 96% рядків,
# а решта це заголовки, які й так із запасом.
EXPAND = 1.25
FOOT_SIZE, FOOT_LEAD = 9, 12.0
NOTE_SIZE, NOTE_LEAD = 8, 11.0


def _wrap(text, width_px, size):
    """Розбити абзац на рядки, які не вилізуть за відведену ширину.

    Рахуємо в знаках, бо шрифт моноширинний: бюджет = ширина / (кегль × CHAR_W)
    і ще поділити на запас під переклад. Переносити треба тут, у генераторі, а
    не сподіватись на рендерер: <text> у SVG не переноситься сам ніколи, а
    англійська версія сторінки збирається з тих самих вузлів і довшає."""
    budget = max(8, int(width_px / (size * CHAR_W * EXPAND)))
    lines, cur = [], ""
    for word in text.split():
        probe = f"{cur} {word}".strip()
        if cur and len(probe) > budget:
            lines.append(cur)
            cur = word
        else:
            cur = probe
    if cur:
        lines.append(cur)
    return lines


# ---- довгі підписи ріжемо на рядки ДО того, як розкладати поверхи по висоті:
# від кількості рядків залежить, де стоїть смуга свічення і яка висота полотна.
NOTE_W = X1_MM * S - 6                    # від краю вікна до розриву, мінус відступ
RIM_NOTE = _wrap(f'обід темніший: за краєм плати діодів нема — на це і '
                 f'закладені {RIM_MM:g} мм обода', NOTE_W, NOTE_SIZE)
FOOT_TEXT = [
    f'панель броні — сендвіч {SANDWICH:g} мм ({SKIN} + порожнина {CORE} + '
    f'{SKIN}); на колі вікна лишається одна стінка {THICK} мм білого ASA: '
    f'вікно не накладка, а ділянка тієї самої панелі',
    f'правило рівності: зазор ≥ {bc.UNI["comfort_ratio"]:g} кроку — рівне '
    f'світло, ≥ {bc.UNI["min_ratio"]:g} кроку — крапки ще вгадуються; конус '
    f'{BEAM:g}° — паспортний кут діода {MOD["chip"]}, корпус {DIODE_MM:g} мм '
    f'при висоті {DIODE_H_MM:g} мм, плата {PCB_MM:g} мм',
    'яскравість рахована за законом Ламберта на внутрішній поверхні вікна; '
    'розсіювання в самому ASA не враховане — воно ще підмиє картинку, тобто '
    'запас іде в наш бік',
]
FOOT_PARA_GAP = 5.0


def _foot_layout():
    """Рядки виноски з готовим зсувом по вертикалі: [(dy, рядок), …].

    Між абзацами проміжок більший, ніж усередині абзацу: шість однаково
    розставлених рядків читаються суцільною плитою, і стає не видно, де
    закінчилась одна думка і почалась інша."""
    out, dy = [], 0.0
    for para in FOOT_TEXT:
        for line in _wrap(para, W - 2 * MARGIN, FOOT_SIZE):
            out.append((dy, line))
            dy += FOOT_LEAD
        dy += FOOT_PARA_GAP
    return out


FOOT_LINES = _foot_layout()

# ---- поверхи по висоті. Усе, що нижче графіка, стоїть одне на одному, тому
# рахується від попереднього, а не вписується числом: додався рядок у виносці —
# смуга і розріз самі поїхали вниз, нічого не наклалось.
Y_TITLE, Y_HALF, Y_SUB = 26.0, 44.0, 62.0
BAND_TOP, BAND_BOT = 84.0, 150.0          # смуга з графіком яскравості
NOTE_TOP = BAND_BOT + 12                  # пояснення провалу на обіді
WASH_TOP = NOTE_TOP + (len(RIM_NOTE) - 1) * NOTE_LEAD + 8
WASH_BOT = WASH_TOP + 22                  # як це виглядає з боку глядача
# Між смугою свічення і бронею лишаємо просвіт на цілу полицю: під зовнішньою
# поверхнею панелі стоїть виносний розмір «поле», і йому треба своє місце,
# інакше підпис читається як частина смуги.
Y_OUT = WASH_BOT + 16                     # зовнішня поверхня броні
Y_TEXT = Y_OUT + 154                      # вердикт під розрізом — на одному рівні
FOOT_TOP = Y_TEXT + 54
H = FOOT_TOP + FOOT_LINES[-1][0] + 13

# Ореол над діодом — не розмір, а «горить»: розмита пляма розміром із чіп.
# Привʼязана до корпусу, щоб не жити окремим числом, якщо модуль поміняється.
GLOW_R = DIODE_MM * S / 6


def _x(x0, x_mm):
    return x0 + x_mm * S


def _y(d_mm):
    """Глибина всередину корпусу від зовнішньої поверхні броні."""
    return Y_OUT + d_mm * S


def band_limits(margin=0.06, step=0.05):
    """Межі графіка яскравості — зняті з самих кривих, а не вибрані на око.

    Обидві половини мусять лежати в одній шкалі (у цьому вся картинка), тож
    беремо мінімум і максимум по ОБОХ і додаємо трохи полів. Чому не рівні
    числа «від 0.45»: у поганої половини справжній мінімум 0.16 — на обіді,
    де діодів за краєм плати вже нема. Обрізана шкала перетворювала цей провал
    на пласку поличку вздовж підлоги графіка, і найстрашніше місце картинки
    читалось як «тут яскравість стала». Тепер не обрізає нічого."""
    vals = []
    for gap in (GAP, GAP_BAD):
        mean = ripple(gap)["mean"]
        vals += [profile(gap, X1_MM * k / CURVE_N) / mean
                 for k in range(CURVE_N + 1)]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * margin
    return (math.floor((lo - pad) / step) * step,
            math.ceil((hi + pad) / step) * step)


V_LO, V_HI = band_limits()                # межі графіка, у частках від середньої


def _txt(x, y, s, size=10, fill=DIM, anchor="start"):
    """Підпис. Тільки <text>: сторінка перекладається англійською автоматично,
    і переклад бере саме текстові вузли — криві або растр він не зачепить.

    Підкладок і обведень під текстом навмисно нема: підписи розставлені так,
    щоб не лізти на графіку. Обведення (paint-order) різні рендерери малюють
    по-різному і місцями просто затирають ним літери."""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}"'
            f' text-anchor="{anchor}">{s}</text>')


def _ticks_v(x, ys):
    """Вертикальна виносна риска з поличками на кожній межі шару."""
    o = [f'<line x1="{x:.1f}" y1="{ys[0]:.1f}" x2="{x:.1f}" y2="{ys[-1]:.1f}" '
         f'stroke="{LINE}" stroke-width="1"/>']
    for y in ys:
        o.append(f'<line x1="{x-3:.1f}" y1="{y:.1f}" x2="{x+3:.1f}" y2="{y:.1f}" '
                 f'stroke="{LINE}" stroke-width="1"/>')
    return o


def _dim_v(x, y1, y2, label, label_y=None, size=9):
    """Виносний розмір по вертикалі; підпис — ліворуч від риски.

    y1 і y2 — це рівно ті дві поверхні, між якими стоїть підписане число.
    Правило звучить банально, але саме на ньому схема вже брехала: риска
    «зазор» починалась із зовнішньої поверхні броні і забирала в себе ще й
    товщину вікна."""
    o = _ticks_v(x, [y1, y2])
    o.append(_txt(x - 6, (y1 + y2) / 2 + 3 if label_y is None else label_y,
                  label, size, anchor="end"))
    return o


def _dim_h(y, x1, x2, label, size=9):
    """Виносний розмір по горизонталі. Те саме правило, що і в _dim_v: полиця
    йде рівно від межі до межі, а не «десь звідти»."""
    o = [f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" '
         f'stroke="{LINE}" stroke-width="1"/>']
    for x in (x1, x2):
        o.append(f'<line x1="{x:.1f}" y1="{y-3:.1f}" x2="{x:.1f}" y2="{y+3:.1f}" '
                 f'stroke="{LINE}" stroke-width="1"/>')
    o.append(_txt((x1 + x2) / 2, y - 5, label, size, anchor="middle"))
    return o


def panel(x0, c, idx, full):
    """Один розріз: панель броні, вікно, зазор, плата з діодами і конусами.

    x0 — де в полотні стоїть край світного кола (нуль по міліметрах).
    full=True малює всі підписи (лівий розріз), False — тільки те, що змінилось."""
    gap = c["gap_mm"]
    o = []
    xl, xr = _x(x0, X0_MM), _x(x0, X1_MM)     # ліва межа фрагмента і розрив
    xa = _x(x0, 0.0)                          # край світного кола
    y_win = _y(THICK)                         # внутрішня поверхня вікна
    y_in = _y(SANDWICH)                       # внутрішня поверхня сендвіча
    y_brd = _y(THICK + gap)                   # верх плати
    y_pcb = y_brd + PCB_MM * S                # спід плати
    y_face = y_brd - DIODE_H_MM * S           # світна поверхня діода
    dio = [_x(x0, D0_MM + i * PITCH) for i in range(SHOWN)]

    # ---- панель броні одним контуром: сендвіч ліворуч, одна стінка у вікні
    o.append(f'<path d="M {xl:.1f} {Y_OUT:.1f} L {xr:.1f} {Y_OUT:.1f} '
             f'L {xr:.1f} {y_win:.1f} L {xa:.1f} {y_win:.1f} '
             f'L {xa:.1f} {y_in:.1f} L {xl:.1f} {y_in:.1f} Z" '
             f'fill="{MAT}" stroke="{LINE}" stroke-width="1.2"/>')
    # порожнина сендвіча — те, чого в панелі нема
    o.append(f'<rect x="{xl:.1f}" y="{_y(SKIN):.1f}" width="{xa-xl:.1f}" '
             f'height="{CORE*S:.1f}" fill="{BG}" stroke="{LINE}" '
             f'stroke-width="0.8" stroke-dasharray="3 3"/>')
    # ділянка вікна — та сама панель, тільки тонка і біла
    o.append(f'<rect x="{xa:.1f}" y="{Y_OUT:.1f}" width="{xr-xa:.1f}" '
             f'height="{THICK*S:.1f}" fill="{WALL}" opacity="0.9"/>')

    # ---- світлові конуси: видно, де вони перетинаються
    o.append(f'<g clip-path="url(#clip{idx})">')
    half = gap * math.tan(HALF) * S
    for i in (1, 2, 3):
        x = dio[i]
        o.append(f'<path d="M {x:.1f} {y_brd:.1f} L {x-half:.1f} {y_win:.1f} '
                 f'L {x+half:.1f} {y_win:.1f} Z" fill="url(#cone{idx})"/>')
    o.append('</g>')
    # висота, на якій конуси сусідів уперше зійшлись
    y_cross = y_brd - CROSS_MM * S
    o.append(f'<line x1="{dio[1]:.1f}" y1="{y_cross:.1f}" x2="{dio[3]:.1f}" '
             f'y2="{y_cross:.1f}" stroke="{ACC}" stroke-width="0.9" '
             f'stroke-dasharray="4 4" opacity="0.8"/>')
    o.append(f'<circle cx="{(dio[1]+dio[2])/2:.1f}" cy="{y_cross:.1f}" r="2.6" '
             f'fill="{ACC}"/>')

    # ---- плата з діодами: і сама плата, і корпуси — у тому самому масштабі,
    # що і зазор. Інакше на око здається, що місця під діодом більше, ніж є.
    o.append(f'<rect x="{_x(x0, RIM_MM):.1f}" y="{y_brd:.1f}" '
             f'width="{xr-_x(x0, RIM_MM):.1f}" height="{PCB_MM*S:.1f}" '
             f'fill="{MAT}" stroke="{LINE}" stroke-width="1.2"/>')
    for x in dio:
        o.append(f'<rect x="{x-DIODE_MM*S/2:.1f}" y="{y_face:.1f}" '
                 f'width="{DIODE_MM*S:.1f}" height="{DIODE_H_MM*S:.1f}" '
                 f'fill="{WALL}" opacity="0.75"/>')
        o.append(f'<circle cx="{x:.1f}" cy="{y_face:.1f}" r="{GLOW_R:.1f}" '
                 f'fill="{GLOW}" filter="url(#soft)"/>')

    # ---- розриви: фрагмент, далі все те саме до центру вікна
    for y1, y2 in ((Y_OUT, y_win), (y_brd, y_pcb)):
        o.append(f'<path d="M {xr:.1f} {y1:.1f} L {xr-5:.1f} {(y1+y2)/2:.1f} '
                 f'L {xr:.1f} {y2:.1f}" fill="none" stroke="{BG}" stroke-width="2"/>')

    # ---- розміри. Підпис зазору стоїть під самою рискою, а не посередині:
    # у правій половині зазор такий малий, що посередині туди нічого не влазить.
    # Сама риска йде від ЗАДНЬОЇ поверхні вікна (y_win) до верху плати — це і є
    # те повітря, про яке говорить diffuser._gap_note.
    o += _dim_v(xa - 22, y_win, y_brd, f'зазор {gap:g} мм',
                label_y=max(y_brd + 4, y_in + 16), size=10)
    o += _dim_h(y_brd + 26, dio[1], dio[2], f'крок {PITCH:.1f} мм')
    if full:
        # товщина вікна — підписом одразу під стінкою, всередині світного кола
        o += _ticks_v(xa + 9, [Y_OUT, y_win])
        o.append(_txt(xa + 16, y_win + 12, f'вікно {THICK} мм — одна стінка', 9))
        # сендвіч: риска з поличками на межах шарів, підпис у вільному полі зверху
        o += _ticks_v(xl + 8, [Y_OUT, _y(SKIN), _y(SKIN + CORE), y_in])
        o.append(_txt(xl, 106, 'панель броні', 9))
        o.append(_txt(xl, 120, f'сендвіч {SANDWICH:g} мм', 9))
        o.append(_txt(xl, 134, f'{SKIN} + {CORE} + {SKIN}', 9))
        # поле вікна — рівно 8 мм від краю світного кола назовні, не від лівої
        # межі фрагмента: фрагмент захоплює ще шматок панелі за полем.
        o += _dim_h(Y_OUT - 6, _x(x0, -BEZEL), xa, f'поле {BEZEL:g} мм')
        o.append(_txt(_x(x0, RIM_MM), y_pcb + 20, f'плата Ø{BOARD_MM:g} мм', 9))
        # плата тонка, і в масштабі це видно — тому її товщину теж підписуємо
        # тією самою колонкою розмірів, що і зазор.
        o += _dim_v(xa - 22, y_brd, y_pcb, f'плата {PCB_MM:g} мм',
                    label_y=y_pcb + 14)
    else:
        o.append(_txt(dio[2], y_pcb + 44, 'плата сидить просто на бобишках',
                      9, ACC, anchor="middle"))

    # ---- що з цього виходить: смуга свічення і графік яскравості
    o += wash(x0, idx, c, full)
    o += curve(x0, c, full)
    if full:
        o += rim_note(x0)

    # ---- заголовок половини і вердикт
    ok = c["level"] == "good"
    o.append(_txt((xl + xr) / 2, Y_HALF,
                  'як треба' if ok else 'якщо притиснути впритул',
                  13, INK if ok else ACC, anchor="middle"))
    o.append(_txt((xl + xr) / 2, Y_SUB,
                  f'зазор {c["gap_mm"]:g} мм = {c["ratio"]:.2f} кроку → {c["verdict"]}',
                  10, DIM, anchor="middle"))
    o.append(_txt(xl, Y_TEXT, f'нерівність світла на вікні ±{c["ripple_pct"]:.1f}%',
                  11, GLOW if ok else ACC))
    if ok:
        o.append(_txt(xl, Y_TEXT + 16,
                      f'конуси сусідів зійшлись за {CROSS_MM:.1f} мм — і до вікна '
                      f'лишається ще {c["left_mm"]:.1f} мм,', 9))
        o.append(_txt(xl, Y_TEXT + 30,
                      'щоб їхні краї встигли розмитись і накластись один на одний', 9))
    else:
        o.append(_txt(xl, Y_TEXT + 16,
                      f'конуси зійшлись так само за {CROSS_MM:.1f} мм, але вікно вже '
                      f'за {c["left_mm"]:.1f} мм:', 9))
        o.append(_txt(xl, Y_TEXT + 30,
                      'перекриття вузьке, і між діодами лишається темна смуга', 9))
    return o


def rim_note(x0):
    """Чому крива провалюється на самому краю вікна.

    Стоїть між графіком і смугою свічення, а не в полі графіка, з двох причин.
    Перша: пояснює одразу обидва зображення — і провал на кривій, і темніший
    край смуги під нею. Друга: у полі графіка цей підпис чіплявся за саму
    криву, щойно шкалу опустили до справжнього мінімуму (band_limits), а
    рядок, розбитий на два, ще й вилазив за лінію розриву половини."""
    xa = _x(x0, 0.0)
    return [_txt(xa + 6, NOTE_TOP + i * NOTE_LEAD, s, NOTE_SIZE)
            for i, s in enumerate(RIM_NOTE)]


def wash(x0, idx, c, full):
    """Смуга свічення на самому вікні — те, що бачить глядач ззаду робота.

    Це та сама порахована яскравість, що й на графіку, тільки показана не
    лінією, а світлом: рівна смуга проти окремих плям."""
    xa, xr = _x(x0, 0.0), _x(x0, X1_MM)
    o = [f'<rect x="{xa:.1f}" y="{WASH_TOP:.1f}" width="{xr-xa:.1f}" '
         f'height="{WASH_BOT-WASH_TOP:.1f}" fill="url(#wash{idx})" rx="3"/>']
    if full:
        # підпис стоїть ЛІВОРУЧ від смуги, у полі над панеллю броні: рівно там
        # вільно і від пояснення обода згори, і від полиці «поле» знизу.
        o.append(_txt(xa - 8, WASH_TOP - 4, 'видно зовні:', 9, anchor="end"))
    return o


def curve(x0, c, full):
    """Графік яскравості вздовж вікна, у частках від середньої по центру."""
    xa, xr = _x(x0, 0.0), _x(x0, X1_MM)
    y1 = BAND_BOT - (1.0 - V_LO) / (V_HI - V_LO) * (BAND_BOT - BAND_TOP)
    o = [f'<line x1="{xa:.1f}" y1="{y1:.1f}" x2="{xr:.1f}" y2="{y1:.1f}" '
         f'stroke="{LINE}" stroke-width="1" stroke-dasharray="3 4"/>']
    pts = []
    for k in range(CURVE_N + 1):
        x_mm = X1_MM * k / CURVE_N
        v = profile(c["gap_mm"], x_mm) / c["mean"]
        # обмежувач лишений як страховка на випадок інших чисел у базі; при
        # межах із band_limits він не спрацьовує жодного разу, тобто крива
        # ніде не лягає на рамку графіка і провал видно до самого дна.
        v = min(max(v, V_LO), V_HI)
        y = BAND_BOT - (v - V_LO) / (V_HI - V_LO) * (BAND_BOT - BAND_TOP)
        pts.append(f'{_x(x0, x_mm):.1f},{y:.1f}')
    o.append(f'<polyline points="{" ".join(pts)}" fill="none" '
             f'stroke="{GLOW if c["level"] == "good" else ACC}" stroke-width="2"/>')
    if full:
        o.append(_txt(xa, BAND_TOP - 8, 'яскравість уздовж вікна', 9))
        o.append(_txt(xr, y1 - 5, 'середня', 8, LINE, anchor="end"))
    return o


def svg():
    """Дві половини в одному масштабі — різниця рівно в одному числі."""
    good, bad = case(GAP), case(GAP_BAD)
    x_left = MARGIN - X0_MM * S               # де стоїть край вікна лівої половини
    x_right = x_left + PANEL_W + MIDGAP
    # Роздільник — точно посередині проміжку МІЖ половинами. x_left/x_right —
    # це нулі міліметрової сітки (край світного кола), а не ліві межі панелей,
    # і саме через цю підміну пунктир раніше стояв усередині правої половини,
    # рівно під першою літерою її підзаголовка.
    x_mid = (_x(x_left, X1_MM) + _x(x_right, X0_MM)) / 2
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
         f'font-family="ui-monospace,Menlo,monospace">']

    d = ['<defs>',
         '<filter id="soft" x="-200%" y="-200%" width="500%" height="500%">'
         '<feGaussianBlur stdDeviation="2.4"/></filter>']
    for idx, (x0, c) in enumerate(((x_left, good), (x_right, bad))):
        gap = c["gap_mm"]
        y_brd, y_win = _y(THICK + gap), _y(THICK)
        d.append(f'<linearGradient id="cone{idx}" gradientUnits="userSpaceOnUse" '
                 f'x1="0" y1="{y_brd:.1f}" x2="0" y2="{y_win:.1f}">'
                 f'<stop offset="0" stop-color="{GLOW}" stop-opacity="0.30"/>'
                 f'<stop offset="1" stop-color="{GLOW}" stop-opacity="0.05"/>'
                 f'</linearGradient>')
        d.append(f'<clipPath id="clip{idx}"><rect x="{_x(x0, 0.0):.1f}" '
                 f'y="{y_win:.1f}" width="{_x(x0, X1_MM)-_x(x0, 0.0):.1f}" '
                 f'height="{y_brd-y_win:.1f}"/></clipPath>')
        # смуга свічення: колір один, міняється тільки прозорість — рівно за
        # порахованою яскравістю, нормованою на максимум у цьому ж вікні
        vals = [profile(gap, X1_MM * k / 60) for k in range(61)]
        top = max(vals)
        stops = "".join(
            f'<stop offset="{k/60:.3f}" stop-color="{GLOW}" '
            f'stop-opacity="{0.80*v/top:.3f}"/>' for k, v in enumerate(vals))
        d.append(f'<linearGradient id="wash{idx}" gradientUnits="userSpaceOnUse" '
                 f'x1="{_x(x0, 0.0):.1f}" y1="0" x2="{_x(x0, X1_MM):.1f}" y2="0">'
                 f'{stops}</linearGradient>')
    d.append('</defs>')
    o += d

    o.append(f'<rect width="{W:.0f}" height="{H:.0f}" rx="8" fill="{BG}"/>')
    o.append(_txt(x_mid, Y_TITLE, f'Розріз ядра: чому плата стоїть на {GAP:g} мм '
                                  f'углиб, а не впритул до вікна',
                  13, INK, anchor="middle"))
    o.append(f'<line x1="{x_mid:.1f}" y1="34" x2="{x_mid:.1f}" '
             f'y2="{Y_TEXT+34:.0f}" stroke="{LINE}" stroke-width="1" '
             f'stroke-dasharray="2 6"/>')

    o += panel(x_left, good, 0, True)
    o += panel(x_right, bad, 1, False)

    for dy, line in FOOT_LINES:
        o.append(_txt(MARGIN, FOOT_TOP + dy, line, FOOT_SIZE))
    o.append('</svg>')
    return "\n".join(o)


def main():
    good, bad = case(GAP), case(GAP_BAD)
    print(f'крок {PITCH:.1f} мм · конус {BEAM:g}° (m={M_EXP:.2f}) · конуси сусідів '
          f'сходяться за {CROSS_MM:.1f} мм над платою')
    for name, c in (("як треба", good), ("впритул", bad)):
        print(f'  {name:9} зазор {c["gap_mm"]:>4g} мм = {c["ratio"]:.2f} кроку · '
              f'нерівність ±{c["ripple_pct"]:.1f}% · {c["verdict"]}')
    print(f'ряд діодів у розрахунку: {N_ROW} шт від краю плати до центру, '
          f'показано {SHOWN}')
    print(f'у масштабі {S:g} px/мм по обох осях: плата {PCB_MM:g} мм, корпус '
          f'діода {DIODE_MM:g}×{DIODE_H_MM:g} мм, вікно {THICK:g} мм, '
          f'поле {BEZEL:g} мм')
    print(f'шкала графіка знята з кривих: {V_LO:.2f}…{V_HI:.2f} від середньої '
          f'(мінімум у поганій половині {min(profile(GAP_BAD, X1_MM*k/CURVE_N) for k in range(CURVE_N+1))/bad["mean"]:.2f})')
    longest = max(len(ln) for _, ln in FOOT_LINES)
    print(f'виноски розбито на {len(FOOT_LINES)} рядків, найдовший {longest} '
          f'знаків ({longest*FOOT_SIZE*CHAR_W:.0f} px, з запасом на переклад '
          f'{longest*FOOT_SIZE*CHAR_W*EXPAND:.0f} px при {W-2*MARGIN:.0f} '
          f'px доступних)')
    (Path(__file__).resolve().parent / "back_core_section.svg").write_text(svg())
    print("креслення: back_core_section.svg")


if __name__ == "__main__":
    main()
