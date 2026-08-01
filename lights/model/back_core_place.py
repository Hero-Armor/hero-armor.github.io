#!/usr/bin/env python3
"""
Де ядро сидить на фігурі — вигляд робота ЗЗАДУ, у масштабі.

Числа про ядро вже пораховані (back_core.py), але з них не видно головного:
чи не завелике коло Ø180 на спині і чи не загубиться воно на двометровій
фігурі. Це питання не рахується — його видно тільки очима, тому тут фігура
і коло на ній намальовані в ОДНОМУ масштабі, поруч із лінійкою в метрах.

Три речі, заради яких малюнок узагалі існує:

  1. розмір. Ядро Ø180 мм на фігурі 2 м — це приблизно як голова робота
     завширшки. Дрібні лампи корпусу (Ø12 і Ø8 мм) стоять поруч крапками:
     видно, що ядро більше за них у пʼятнадцять разів у поперечнику;
  2. висота. Центр кола — на рівні лопаток, нижче плечей і вище талії;
     скільки це в метрах від настилу, показує лінійка збоку;
  3. ребра. Панель спини Марсель друкує сендвічем з ребрами через 15-20 см.
     Ядру потрібне рівне місце під усю посадку (вікно + поле). Сітка ребер
     намальована з двома кроками одразу: зліва 15 см, справа 20 см — і обидві
     стоять у НАЙКРАЩІЙ для ядра фазі, тобто зсунуті так, щоб ядро опинилось
     точно посередині між двома ребрами. Де ребра насправді, ми не знаємо
     (задньої проєкції на кресленні Rev 2.1 нема), і саме тому малювати
     випадкову фазу не можна: з неї нічого не випливає. А з найкращої —
     випливає все: при 15 см ребро лізе під коло навіть у ній, при 20 см ядро
     проходить, але рівно посередині і з запасом 4 мм на всю посадку. Тому
     помаранчеве ребро на схемі читається однозначно: «не рятує жоден зсув».
     Це і є питання до Марселя.

Кільця модуля намальовані за правилом бази (rings_radius_rule через
back_core.rings()), а не рівним кроком: проміжки між ними НЕрівні — 5.7 мм у
центрі і 17.2 мм між двома зовнішніми. Це не дрібниця, а знахідка, яку база
велить показувати (uniformity.radial_note): саме по краю плати світло може
вийти менш рівним. Рівний крок її замальовував би.

Силует умовний: пропорції людини в броні, а не креслення панелей — справжніх
розмірів спини в нас поки нема. Усі частки лежать у lights/data/back_core.json
→ figure, звідти ж діаметри і висота фігури; подіум рахується з геометрії
стрічки в lights/data/params.json. Тільки stdlib.
"""

import json
import sys
from math import cos, pi, sin
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import back_core as bc  # noqa: E402  (посадка — похідна, її рахує модель)

DATA = Path(__file__).resolve().parent.parent / "data"
D = json.loads((DATA / "back_core.json").read_text())
P = json.loads((DATA / "params.json").read_text())

SHELL = D["shell"]
FIG = D["figure"]
WIN = D["window"]
DIF = D["diffuser"]
MOD = next(m for m in D["modules"] if m["key"] == D["chosen"]["module"])
ARM = next(f for f in P["fixtures"] if f["id"] == "water_arms")

FIG_H_M = SHELL["figure_h_m"]            # висота фігури
WIN_M = WIN["size_mm"] / 1000            # світне коло
FOOT_MM = bc.footprint_mm()              # посадка = вікно + поле з двох боків
SEAT_M = FOOT_MM / 1000                  # та сама посадка в метрах
CORE_M = FIG_H_M * FIG["core_y"]         # висота центра ядра над настилом
RIBS_CM = SHELL["ribs_cm"]

# Радіус настилу. Зовнішній периметр октагона на кресленні не заданий (див.
# params.json → topology._lengths_source), тому беремо єдине, що звідти є:
# промінь стрічки від краю до центру плюс радіус центрального кола.
DECK_R_M = ARM["ray_m"] + ARM["ring_m"] / (2 * pi)

# --- полотно: чисто малювальні константи, фізики в них нема ---------------
W, H = 830, 700
CX, GROUND_Y = 285, 490      # вісь фігури і настил під ногами
FIG_PX = 410                 # висота фігури на схемі
PPM = FIG_PX / FIG_H_M       # пікселів на метр — єдиний масштаб схеми
DECK_SQUASH = 0.30           # настил у слабкій перспективі
DECK_EDGE = 10               # видима товщина настилу (умовна)
RULER_X = 130
LAB_X = 470

BG, BODY, LINE = "#0b0e14", "#121826", "#26436e"
CORE_C, GLOW, ACC = "#eaf1ff", "#5b9bff", "#e08b3e"
TXT, TXT2 = "#eaf1ff", "#8e97a6"


def m2px(m):
    return m * PPM


def fx(xf):
    """Частка висоти фігури вбік від осі → піксель по горизонталі."""
    return CX + xf * FIG_PX


def fy(yf):
    """Частка висоти фігури від настилу → піксель по вертикалі."""
    return GROUND_Y - yf * FIG_PX


# ------------------------------------------------------------------ розрахунок
def torso_half(yf):
    """Півширина торса на заданій висоті — щоб ребра не вилазили за силует."""
    pts = [(FIG["shoulder_y"], FIG["shoulder_w"]), (FIG["back_y"], FIG["back_w"]),
           (FIG["waist_y"], FIG["waist_w"]), (FIG["hip_y"], FIG["hip_w"])]
    if yf >= pts[0][0]:
        return pts[0][1]
    for (y1, w1), (y2, w2) in zip(pts, pts[1:]):
        if y2 <= yf <= y1:
            k = (y1 - yf) / (y1 - y2)
            return w1 + (w2 - w1) * k
    return pts[-1][1]


def ribs(pitch_cm):
    """Висоти ребер (у частках) для сітки з таким кроком — у найкращій для ядра фазі.

    Звідки сітка починається, ми не знаємо: задньої проєкції на кресленні
    Rev 2.1 нема. Раніше ми прив'язувались до лінії плечей — і це виявилось
    гірше за випадковість: при кроці 20 см ребро сідало рівно в центр ядра, і
    малюнок кричав «не влазить» там, де підпис поруч чесно рахував запас у
    4 мм. Половина схеми спростовувала другу половину.

    Тому фазу тепер не вгадуємо, а вибираємо найвигіднішу: сітка зсунута так,
    щоб ядро стало точно посередині між двома ребрами. Тоді малюнок не
    обіцяє удачі і не лякає без причини — він показує МЕЖУ. Помаранчеве ребро
    в такій фазі означає рівно те саме, що рахує rib_clash(): не рятує жоден
    зсув. Ребра тягнемо в межах панелі спини — від плечей до стегон."""
    step = (pitch_cm / 100) / FIG_H_M
    out, y = [], FIG["core_y"] + step / 2
    while y + step <= FIG["shoulder_y"]:
        y += step
    while y > FIG["shoulder_y"]:      # крок більший за саму спину — не лізем вище плечей
        y -= step
    while y >= FIG["hip_y"]:
        out.append(y)
        y -= step
    return out


def under_core(yf):
    """Чи проходить ребро на цій висоті під посадкою ядра."""
    return abs(yf - FIG["core_y"]) * FIG_H_M < SEAT_M / 2


def rib_clash():
    """Чи неминуче ребро під посадкою ядра — по кожному кроку сітки.

    Просвіт між сусідніми ребрами дорівнює кроку. Якщо крок менший за
    посадку (вікно плюс поле, back_core.footprint_mm()), ребро потрапляє під
    деталь при будь-якому зсуві сітки — вибирати нема з чого. Якщо більший,
    ядро пролазить, але тільки якщо стане рівно між ребрами, і запас на це
    видно числом.

    hits рахуються по тій самій ribs(), що й малюється, тобто в найкращій
    фазі. Тому порожній hits читається не як «пронесло», а як «пролізе саме в
    цій фазі і ні в якій іншій» — і це той самий висновок, що й free_mm."""
    out = []
    for cm in RIBS_CM:
        free_mm = cm * 10 - FOOT_MM
        out.append(dict(pitch_cm=cm, free_mm=free_mm, inevitable=free_mm <= 0,
                        hits=[y for y in ribs(cm) if under_core(y)]))
    return out


def core_label_y(size=10):
    """Висота рядка «центр ядра» — у просвіті між ребрами, а не «на око вище виноски».

    Ставити підпис на фіксовані кілька пікселів над виносною лінією не можна:
    сітка ребер рахується з даних і рухається разом з ними. У першій версії
    схеми ребро під ядром — єдиний сигнальний елемент усього малюнка — лягло
    рівно на слова «центр ядра»: підпис жував ребро, ребро перекреслювало
    підпис. Тому просвіт не вгадуємо, а рахуємо: беремо сусідні ребра лівої
    сітки (у текстову смугу лізе тільки вона — текст іде від лінійки до осі) і
    ставимо рядок посередині просвіту, з того боку виноски, де просвіт більший."""
    ccy = fy(FIG["core_y"])
    ys = [fy(y) for y in ribs(RIBS_CM[0])]
    top = max([y for y in ys if y < ccy], default=ccy - 4 * size)
    bot = min([y for y in ys if y > ccy], default=ccy + 4 * size)
    band = (top, ccy) if ccy - top >= bot - ccy else (ccy, bot)
    # baseline нижче за оптичний центр рядка: над ним 0.7 висоти шрифта, під
    # ним тільки виносні елементи.
    return sum(band) / 2 + size * 0.25


def size_ratio(key="led12"):
    """У скільки разів ядро більше за звичайну лампу корпусу."""
    d = FIG["lamp_d_mm"][key]
    k = WIN["size_mm"] / d
    return dict(key=key, d_mm=d, times=k, area_times=k * k)


def lamp_audit():
    """Скільки ламп у базі і скільки місць для них описано.

    Опис місць у params.json (led12: «Голова 4, плечі 2, груди, коліно,
    стопа») дає девʼять точок при qty 8. Схема має показувати цю розбіжність,
    а не тихо домальовувати стільки, скільки треба."""
    out = []
    for key in FIG["lamp_d_mm"]:
        f = next(x for x in P["fixtures"] if x["id"] == key)
        drawn = sum(len(s["x"]) for s in FIG["lamp_spots"] if s["fixture"] == key)
        out.append(dict(key=key, name=f["name"], qty=f["qty"], spots=drawn,
                        gap=drawn - f["qty"]))
    return out


# ------------------------------------------------------------------- креслення
def _poly(pts, fill=BODY, stroke=LINE, sw=1.4):
    d = " ".join(f"{fx(a):.1f},{fy(b):.1f}" for a, b in pts)
    return (f'<polygon points="{d}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw}" stroke-linejoin="round"/>')


def _leg(side):
    cx = side * (FIG["hip_w"] + FIG["leg_gap"]) / 2
    return [(cx - FIG["thigh_w"], FIG["hip_y"]), (cx + FIG["thigh_w"], FIG["hip_y"]),
            (cx + FIG["knee_w"], FIG["knee_y"]), (cx + FIG["ankle_w"], FIG["ankle_y"]),
            (cx - FIG["ankle_w"], FIG["ankle_y"]), (cx - FIG["knee_w"], FIG["knee_y"])]


def _foot(side):
    cx = side * (FIG["hip_w"] + FIG["leg_gap"]) / 2
    return [(cx - FIG["foot_w"], FIG["ankle_y"]), (cx + FIG["foot_w"], FIG["ankle_y"]),
            (cx + FIG["foot_w"], 0), (cx - FIG["foot_w"], 0)]


def _arm(side):
    x = side * FIG["arm_x"]
    return [(x - FIG["arm_w"], FIG["shoulder_y"]), (x + FIG["arm_w"], FIG["shoulder_y"]),
            (x + FIG["wrist_w"], FIG["wrist_y"]), (x - FIG["wrist_w"], FIG["wrist_y"])]


def _torso():
    f = FIG
    return [(-f["shoulder_w"], f["shoulder_y"]), (f["shoulder_w"], f["shoulder_y"]),
            (f["back_w"], f["back_y"]), (f["waist_w"], f["waist_y"]),
            (f["hip_w"], f["hip_y"]), (-f["hip_w"], f["hip_y"]),
            (-f["waist_w"], f["waist_y"]), (-f["back_w"], f["back_y"])]


def _text(x, y, s, fill=TXT2, size=10, anchor="start"):
    return (f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" '
            f'font-size="{size}" fill="{fill}">{s}</text>')


def _block(x, y, lines, step=15):
    """Стовпчик підписів: (текст, колір, розмір)."""
    out = []
    for i, (s, fill, size) in enumerate(lines):
        out.append(_text(x, y + i * step, s, fill, size))
    return out


def svg():
    """Вигляд ззаду: настил, фігура, ядро, ребра, лінійка і підписи.

    Порядок шарів має сенс: ребра лягають на торс ПІСЛЯ силуета, але ДО рук —
    руки висять збоку і мали б їх перекривати, як у житті. Ядро малюється
    поверх усього, бо воно і є тема схеми."""
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'font-family="ui-monospace,Menlo,monospace">',
         '<defs>'
         '<filter id="cglow" x="-120%" y="-120%" width="340%" height="340%">'
         '<feGaussianBlur stdDeviation="7"/></filter>'
         '<filter id="sglow" x="-300%" y="-300%" width="700%" height="700%">'
         '<feGaussianBlur stdDeviation="2"/></filter>'
         '</defs>',
         f'<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>']

    # --- подіум-октагон у слабкій перспективі
    r = m2px(DECK_R_M)
    top = [(CX + r * cos(pi / 8 + k * pi / 4),
            GROUND_Y + r * DECK_SQUASH * sin(pi / 8 + k * pi / 4)) for k in range(8)]
    side = " ".join(f"{x:.1f},{y + DECK_EDGE:.1f}" for x, y in top)
    face = " ".join(f"{x:.1f},{y:.1f}" for x, y in top)
    o.append(f'<polygon points="{side}" fill="#0a0f18" stroke="#1c2836"/>')
    o.append(f'<polygon points="{face}" fill="#0e131d" stroke="{LINE}"/>')

    # --- силует: торс, ноги, стопи, шия, шолом
    o.append(_poly(_torso()))
    for s in (-1, 1):
        o.append(_poly(_leg(s)))
        o.append(_poly(_foot(s)))
    o.append(f'<rect x="{fx(-FIG["neck_w"]):.1f}" y="{fy(1 - FIG["head_h"]):.1f}" '
             f'width="{2 * FIG["neck_w"] * FIG_PX:.1f}" '
             f'height="{(1 - FIG["head_h"] - FIG["shoulder_y"]) * FIG_PX:.1f}" '
             f'fill="{BODY}" stroke="{LINE}" stroke-width="1.4"/>')
    o.append(f'<rect x="{fx(-FIG["head_w"]):.1f}" y="{fy(1.0):.1f}" '
             f'width="{2 * FIG["head_w"] * FIG_PX:.1f}" '
             f'height="{FIG["head_h"] * FIG_PX:.1f}" '
             f'rx="{FIG["head_w"] * FIG_PX * 0.5:.1f}" '
             f'fill="{BODY}" stroke="{LINE}" stroke-width="1.4"/>')

    # --- ребра: зліва сітка з дрібним кроком, справа з великим. Так обидва
    # варіанти видно на одній фігурі, і не треба малювати дві схеми.
    for cl, sgn in zip(rib_clash(), (-1, 1)):
        dash = "6 5" if sgn < 0 else "2 6"
        for y in ribs(cl["pitch_cm"]):
            hit = under_core(y)
            o.append(f'<line x1="{fx(0):.1f}" y1="{fy(y):.1f}" '
                     f'x2="{fx(sgn * torso_half(y)):.1f}" y2="{fy(y):.1f}" '
                     f'stroke="{ACC if hit else LINE}" '
                     f'stroke-width="{1.8 if hit else 1.2}" '
                     f'stroke-dasharray="{dash}" opacity="{1 if hit else 0.6}"/>')
        o.append(_text(fx(sgn * (FIG["shoulder_w"] + 0.012)),
                       fy(FIG["shoulder_y"]) - 8,
                       f'ребра {cl["pitch_cm"]} см', TXT2, 9,
                       "end" if sgn < 0 else "start"))
    for s in (-1, 1):
        o.append(_poly(_arm(s)))

    # --- ядро: посадка, світне коло, девʼять вкладених кілець модуля
    ccx, ccy = fx(0), fy(FIG["core_y"])
    o.append(f'<circle cx="{ccx:.1f}" cy="{ccy:.1f}" r="{m2px(SEAT_M / 2):.1f}" '
             f'fill="none" stroke="{TXT2}" stroke-width="1" stroke-dasharray="3 4" '
             f'opacity="0.7"/>')
    o.append(f'<circle cx="{ccx:.1f}" cy="{ccy:.1f}" r="{m2px(WIN_M / 2) + 3:.1f}" '
             f'fill="{GLOW}" filter="url(#cglow)" opacity="0.35">'
             f'<animate attributeName="opacity" values="0.28;0.6;0.28" dur="3.6s" '
             f'repeatCount="indefinite"/></circle>')
    o.append(f'<circle cx="{ccx:.1f}" cy="{ccy:.1f}" r="{m2px(WIN_M / 2):.1f}" '
             f'fill="#16294a" stroke="{GLOW}" stroke-width="1.5"/>')
    # Радіуси кілець — за правилом бази (back_core.rings(), rings_radius_rule),
    # а не рівним кроком. Різниця не косметична: проміжки між кільцями нерівні,
    # 5.7 мм у центрі проти 17.2 мм між двома зовнішніми, і саме ця нерівність —
    # причина, чому по краю плати світло може вийти менш рівним
    # (uniformity.radial_note). Рівний крок цю знахідку замальовував би, та ще й
    # розходився б із сусідньою схемою back_core_face.py, яка рахує за правилом.
    for i, ring in enumerate(bc.rings(MOD)):
        rr = m2px(ring["r_mm"] / 1000)
        if ring["n"] == 1:
            # Перший елемент розкладки — один центральний діод, а не кільце:
            # у нього радіус нуль, тому він і намальований крапкою.
            o.append(f'<circle cx="{ccx:.1f}" cy="{ccy:.1f}" r="1.6" fill="{CORE_C}"/>')
            continue
        o.append(f'<circle cx="{ccx:.1f}" cy="{ccy:.1f}" r="{rr:.1f}" fill="none" '
                 f'stroke="{GLOW}" stroke-width="0.7" '
                 f'opacity="{0.55 - 0.03 * i:.2f}"/>')

    # --- лампи корпусу: ті самі, що вже стоять у params.json, у тому ж масштабі.
    # Лампи з іншого боку фігури (hidden) не малюємо взагалі: це вигляд ЗЗАДУ,
    # і показувати крізь корпус те, чого звідси не видно, — брехня. Про них
    # сказано в підвалі словами. Пунктиром ідуть тільки припущені місця.
    for spot in FIG["lamp_spots"]:
        if spot.get("hidden"):
            continue
        rr = FIG["lamp_d_mm"][spot["fixture"]] / 2 / 1000 * PPM
        for xf in spot["x"]:
            x, y = fx(xf), fy(spot["y"])
            if spot.get("assumed"):
                o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rr + 1.6:.1f}" '
                         f'fill="none" stroke="{TXT2}" stroke-width="0.8" '
                         f'stroke-dasharray="1.5 1.5"/>')
            else:
                o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rr + 2.4:.1f}" '
                         f'fill="{GLOW}" filter="url(#sglow)" opacity="0.5"/>')
                o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rr:.1f}" '
                         f'fill="{CORE_C}"/>')

    # --- лінійка: крок у чверть фігури і окремо підписаний відрізок унизу
    step_m = FIG_H_M / 4
    o.append(f'<line x1="{RULER_X}" y1="{GROUND_Y}" x2="{RULER_X}" '
             f'y2="{fy(1.0):.1f}" stroke="{LINE}" stroke-width="1.2"/>')
    n = int(round(FIG_H_M / step_m))
    for i in range(n + 1):
        mm, y = i * step_m, GROUND_Y - m2px(i * step_m)
        o.append(f'<line x1="{RULER_X - 5}" y1="{y:.1f}" x2="{RULER_X + 5}" '
                 f'y2="{y:.1f}" stroke="{LINE}" stroke-width="1.2"/>')
        o.append(_text(RULER_X - 10, y + 3.5, f"{mm:.1f} м", TXT2, 9, "end"))
    o.append(f'<line x1="{RULER_X}" y1="{GROUND_Y}" x2="{RULER_X}" '
             f'y2="{GROUND_Y - m2px(step_m):.1f}" stroke="{TXT}" stroke-width="2.6"/>')
    o.append(_text(RULER_X + 9, GROUND_Y - m2px(step_m) / 2 + 3.5,
                   f"{step_m:.1f} м", TXT, 10))

    # --- висота центра ядра: винос від лінійки просто до кола. Свідомо НЕ
    # помаранчевий: цим кольором на схемі говорить тільки збіг із ребром.
    o.append(f'<line x1="{RULER_X}" y1="{ccy:.1f}" x2="{ccx:.1f}" y2="{ccy:.1f}" '
             f'stroke="{TXT2}" stroke-width="1" stroke-dasharray="4 4" opacity="0.7"/>')
    lab = 10
    o.append(_text(RULER_X + 8, core_label_y(lab),
                   f"{CORE_M:.2f} м — центр ядра", TXT, lab))

    # --- підписи праворуч: ядро. Винос іде НЕ по центру кола, а навскіс угору —
    # так текстовий блок стає НАД ядром і не наїжджає на сітку ребер, а сама
    # виноска не дублює горизонталь, яка вже йде від лінійки до центру.
    rs = m2px(SEAT_M / 2)
    k1x, k1y = ccx + rs * 0.71, ccy - rs * 0.71
    o.append(f'<polyline points="{k1x:.1f},{k1y:.1f} {k1x + 16:.1f},{k1y - 16:.1f} '
             f'{LAB_X - 8},{k1y - 16:.1f}" fill="none" stroke="{LINE}" stroke-width="1"/>')
    o.extend(_block(LAB_X, ccy - 40, [
        (f'ядро Ø{WIN["size_mm"]:.0f} мм на рівні лопаток', TXT, 12),
        (f'модуль {bc.diodes_label(MOD["diodes"])} Ø{MOD["size_mm"]} мм, '
         f'{bc.rings_label(MOD["rings"])}', TXT2, 10),
        (f'вікно {DIF["thickness_mm"]} мм, плата на {DIF["gap_mm"]} мм углиб', TXT2, 10),
        (f'рівного місця під посадку — Ø{FOOT_MM:g} мм '
         f'(вікно + поле {WIN["bezel_mm"]} мм)', TXT2, 10),
    ]))

    # --- підписи праворуч: ребра, з готовим висновком
    # Блок про ребра відводимо на один великий крок сітки нижче ядра: так
    # виноска йде в порожнину між ребрами, а не по самому ребру.
    ry = fy(FIG["core_y"] - (RIBS_CM[1] / 100) / FIG_H_M)
    o.append(f'<line x1="{fx(torso_half(FIG["waist_y"])) + 4:.1f}" y1="{ry:.1f}" '
             f'x2="{LAB_X - 8}" y2="{ry:.1f}" stroke="{LINE}" stroke-width="1"/>')
    rib_lines = [(f'ребра панелі, крок {RIBS_CM[0]}-{RIBS_CM[1]} см', TXT, 12),
                 (f'зліва сітка {RIBS_CM[0]} см, справа {RIBS_CM[1]} см', TXT2, 10)]
    for cl in rib_clash():
        if cl["inevitable"]:
            rib_lines.append((f'{cl["pitch_cm"]} см — посадка не влазить у просвіт '
                              f'({cl["free_mm"]:.0f} мм):', ACC, 10))
            rib_lines.append(('ребро під ядром при будь-якому зсуві сітки', ACC, 10))
        else:
            rib_lines.append((f'{cl["pitch_cm"]} см — вільних {cl["free_mm"]:.0f} мм: '
                              f'пролізе тільки якщо', TXT2, 10))
            rib_lines.append(('коло стане рівно між двома ребрами', TXT2, 10))
    rib_lines.append(('де саме ребра на спині — питання до Марселя', ACC, 10))
    rib_lines.append(('фаза сітки невідома: задньої проєкції на Rev 2.1', TXT2, 10))
    rib_lines.append(('нема. Тому обидві сітки намальовані в найкращій', TXT2, 10))
    rib_lines.append(('для ядра фазі — рівно між ребрами; помаранчеве', TXT2, 10))
    rib_lines.append(('ребро тоді значить: не рятує і найвдаліший зсув', ACC, 10))
    o.extend(_block(LAB_X, ry + 6, rib_lines))

    # --- шапка і підвал
    o.append(_text(W / 2, 26,
                   f'Вигляд ззаду: ядро Ø{WIN["size_mm"]:.0f} мм на фігурі '
                   f'{FIG_H_M:.1f} м', TXT, 13, "middle"))
    sr = size_ratio()
    o.append(_text(W / 2, 44,
                   f'центр на {CORE_M:.2f} м від настилу · крапки — лампи корпусу '
                   f'Ø{sr["d_mm"]} і Ø{FIG["lamp_d_mm"]["led8"]} мм у тому ж масштабі',
                   TXT2, 10, "middle"))

    foot = [f'ядро ширше за лампу Ø{sr["d_mm"]} мм у {sr["times"]:.0f} разів у '
            f'поперечнику і в {sr["area_times"]:.0f} разів за площею',
            'силует умовний — пропорції людини в броні, а не креслення панелей спини',
            f'подіум-октагон Ø{2 * DECK_R_M:.2f} м — прикидка: промінь стрічки плюс '
            f'радіус центрального кола, зовнішній периметр у кресленні не заданий']
    for s in FIG["lamp_spots"]:
        if s.get("hidden"):
            foot.append(f'лампа на місці «{s["place"]}» у цей вигляд не потрапляє — '
                        f'вона з іншого боку фігури; у базі вона є')
        elif s.get("assumed"):
            foot.append(f'пунктирні крапки — {len(s["x"])} лампи '
                        f'Ø{FIG["lamp_d_mm"][s["fixture"]]} мм: база каже скільки їх, '
                        f'але не каже де')
    for g in [a for a in lamp_audit() if a["gap"]]:
        foot.append(f'у базі {g["qty"]} ламп Ø{FIG["lamp_d_mm"][g["key"]]} мм, а місць '
                    f'в описі {g["spots"]} — розбіжність показуємо, а не ховаємо')
    for i, s in enumerate(foot):
        o.append(_text(24, H - 96 + i * 17, s, TXT2, 10))

    o.append("</svg>")
    return "\n".join(o)


def main():
    print(f'фігура {FIG_H_M:.2f} м · ядро Ø{WIN["size_mm"]:.0f} мм на висоті '
          f'{CORE_M:.2f} м (лопатки, {FIG["core_y"]:.2f} висоти)')
    sr = size_ratio()
    print(f'проти лампи Ø{sr["d_mm"]} мм: ×{sr["times"]:.0f} у поперечнику, '
          f'×{sr["area_times"]:.0f} за площею · посадка Ø{FOOT_MM:g} мм')
    rs = bc.rings(MOD)
    print(f'модуль {bc.diodes_label(MOD["diodes"])}: {bc.rings_label(len(rs))} '
          f'за правилом бази, радіуси {rs[1]["r_mm"]:.1f}…{rs[-1]["r_mm"]:.1f} мм '
          f'(проміжки нерівні, не рівний крок)')
    for cl in rib_clash():
        state = "ребро під ядром неминуче" if cl["inevitable"] else \
                f'вільних {cl["free_mm"]:.0f} мм, тільки точно між ребрами'
        print(f'  ребра через {cl["pitch_cm"]} см (сітка в найкращій фазі): {state}')
    for a in lamp_audit():
        note = "" if not a["gap"] else f'  ⚠ розбіжність {a["gap"]:+d}'
        print(f'  {a["name"]}: у базі {a["qty"]}, місць описано {a["spots"]}{note}')
    print(f'подіум Ø{2 * DECK_R_M:.2f} м (прикидка, зовнішній периметр не заданий)')
    (Path(__file__).resolve().parent / "back_core_place.svg").write_text(svg())
    print("креслення: back_core_place.svg")


if __name__ == "__main__":
    main()
