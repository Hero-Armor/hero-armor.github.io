#!/usr/bin/env python3
"""
Що навішано на самій фігурі вартового — вигляд спереду і ззаду в одному масштабі.

Питання, на яке відповідає ця схема, звучить у проєкті постійно: «а що взагалі
стоїть на роботі?» Словами це розсипано по трьох різних місцях бази — лампи в
списку світильників, динамік і радар у вимогах аудіо, ядро в своїй окремій
папці, — і зібрати з цього картинку в голові неможливо. Тут усе разом на двох
силуетах:

  · вісім ламп Ø12 мм — верх шолома, скроні, плечі, груди, коліно, стопа;
  · дві лампи Ø8 мм на передпліччях (у базі про них сказано тільки «strip-line»,
    тому місце наше і показане пунктиром);
  · динамік у грудях мембраною ВНИЗ, з грилем і протипиловою тканиною —
    стрілка вниз на схемі означає саме це, а не напрям звуку;
  · діелектричне вікно 60×60 мм під радар: крізь метал LD2410C не бачить, тому
    на цьому квадраті не має бути ні металу, ні металізованого фарбування;
  · три смуги світловідбивної стрічки з креслення — №3 і №4 білі, №5 жовта;
  · ядро на спині Ø180 мм — воно тільки для масштабу, своя схема в lights/.

Головна чесність схеми в двох місцях. Перше: в базі стоїть 8 ламп Ø12 мм, а
описаних місць девʼять — цю розбіжність схема виводить числом у підвал, а не
домальовує зайву точку і не ховає її. Друге: на фасадах архітектора позначки
продубльовані і спереду, і ззаду, тому точної адресації кожної лампи в
першоджерелах нема; усе, чого нема в кресленні, йде пунктиром.

Звідки числа. Кількості, ватти і назви світильників — lights/data/params.json
(fixtures led12, led8, back_core). Радар і його струм — audio/data/params.json.
Пропорції силуета, висота фігури і діаметри лінз — lights/data/back_core.json
(figure, shell), звідти ж їх бере схема спини, тому обидві малюють ОДНОГО
робота. Координати кожної точки на корпусі і назви місць — свої,
armor/data/fixtures_map.json. Тільки stdlib.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DATA = HERE.parent / "data"

M = json.loads((DATA / "fixtures_map.json").read_text())
LP = json.loads((ROOT / "lights" / "data" / "params.json").read_text())
BC = json.loads((ROOT / "lights" / "data" / "back_core.json").read_text())
AP = json.loads((ROOT / "audio" / "data" / "params.json").read_text())

if "figure" not in BC or "lamp_d_mm" not in BC.get("figure", {}):
    raise SystemExit("lights/data/back_core.json → figure зник: пропорції фігури "
                     "і діаметри лінз живуть тільки там, дублювати їх сюди не можна")

FIG = BC["figure"]                 # пропорції силуета — частки висоти фігури
SHELL = BC["shell"]
WIN = BC["window"]
MOD = next(m for m in BC["modules"] if m["key"] == BC["chosen"]["module"])
LAMP_D = FIG["lamp_d_mm"]          # Ø лінзи по типу лампи
FIG_H_M = SHELL["figure_h_m"]      # висота фігури над настилом

FX = {f["id"]: f for f in LP["fixtures"]}
SENSOR = AP["sensor"]
RADAR = M["radar_window"]
SPK = M["speaker"]

# --- полотно: чисто малювальні константи, фізики в них нема -----------------
W, H = 960, 800
GROUND_Y = 630                     # настил подіуму під ногами
FIG_PX = 470                       # висота фігури на схемі
PPM = FIG_PX / FIG_H_M             # пікселів на метр — єдиний масштаб схеми
CX = {"front": 250, "rear": 660}
DECK_HALF, DECK_EDGE = 140, 6
LINE_H = 15                        # крок рядків усередині одного підпису
LAMP_R = 4.2                       # позначка лампи — збільшена, див. підвал
CAP_Y = 148                        # підпис виду над фігурою
SCALE_STEPS = 4                    # масштабна лінійка = чверть висоти фігури
SCALE_Y = GROUND_Y + 30
FOOT_Y = 682                       # перший рядок легенди і підвалу
FOOT_STEP = 18
NOTE_X = 470                       # підвал праворуч від легенди
LAB_BOTTOM = 620                   # нижче підпис не опускається — там настил

INK, TXT2, HAIR = "#24231d", "#6b675c", "#c9c6ba"
ACC, SIG, GOOD, WARN = "#b35b1e", "#3d6f96", "#3d7a4f", "#b07c14"
BODY, PLATE, WHITE = "#efeee7", "#e8e4d6", "#ffffff"
TAPE_FILL = {"біла": WHITE, "жовта": "#f2e9d2"}
TAPE_LINE = {"біла": INK, "жовта": WARN}
GHOST = "4 6"                      # єдиний пунктир на схемі: місце припущене


def fy(yf):
    """Частка висоти фігури від настилу → піксель по вертикалі."""
    return GROUND_Y - yf * FIG_PX


def fx(view, xf):
    """Частка висоти фігури вбік від осі → піксель по горизонталі."""
    return CX[view] + xf * FIG_PX


def mm(v):
    """Міліметри на фігурі → пікселі схеми, у тому ж масштабі."""
    return v / 1000 * PPM


def plural(n, forms):
    """Українське закінчення до числа: (одна, дві, пʼять).

    Кількості на схемі беруться з бази і колись зміняться; без цього при
    правці qty на сторінці зʼявилось би «2 ламп» або «241 діодів»."""
    one, few, many = forms
    if n % 100 in (11, 12, 13, 14):
        return many
    if n % 10 == 1:
        return one
    if n % 10 in (2, 3, 4):
        return few
    return many


LAMP_W = ("лампа", "лампи", "ламп")
DIODE_W = ("діод", "діоди", "діодів")


# ------------------------------------------------------- силует по пропорціях
def _seg(pts, yf):
    """Півширина на висоті yf по ламаній (yf, півширина), зверху вниз."""
    if yf >= pts[0][0]:
        return pts[0][1]
    for (y1, w1), (y2, w2) in zip(pts, pts[1:]):
        if y2 <= yf <= y1:
            return w1 + (w2 - w1) * (y1 - yf) / (y1 - y2)
    return pts[-1][1]


def torso_half(yf):
    return _seg([(FIG["shoulder_y"], FIG["shoulder_w"]), (FIG["back_y"], FIG["back_w"]),
                 (FIG["waist_y"], FIG["waist_w"]), (FIG["hip_y"], FIG["hip_w"])], yf)


def arm_half(yf):
    return _seg([(FIG["shoulder_y"], FIG["arm_w"]), (FIG["wrist_y"], FIG["wrist_w"])], yf)


def leg_half(yf):
    return _seg([(FIG["hip_y"], FIG["thigh_w"]), (FIG["knee_y"], FIG["knee_w"]),
                 (FIG["ankle_y"], FIG["ankle_w"])], yf)


def leg_cx(side):
    return side * (FIG["hip_w"] + FIG["leg_gap"]) / 2


def _torso():
    f = FIG
    return [(-f["shoulder_w"], f["shoulder_y"]), (f["shoulder_w"], f["shoulder_y"]),
            (f["back_w"], f["back_y"]), (f["waist_w"], f["waist_y"]),
            (f["hip_w"], f["hip_y"]), (-f["hip_w"], f["hip_y"]),
            (-f["waist_w"], f["waist_y"]), (-f["back_w"], f["back_y"])]


def _leg(side):
    cx = leg_cx(side)
    return [(cx - FIG["thigh_w"], FIG["hip_y"]), (cx + FIG["thigh_w"], FIG["hip_y"]),
            (cx + FIG["knee_w"], FIG["knee_y"]), (cx + FIG["ankle_w"], FIG["ankle_y"]),
            (cx - FIG["ankle_w"], FIG["ankle_y"]), (cx - FIG["knee_w"], FIG["knee_y"])]


def _foot(side):
    cx = leg_cx(side)
    return [(cx - FIG["foot_w"], FIG["ankle_y"]), (cx + FIG["foot_w"], FIG["ankle_y"]),
            (cx + FIG["foot_w"], 0), (cx - FIG["foot_w"], 0)]


def _arm(side):
    x = side * FIG["arm_x"]
    return [(x - FIG["arm_w"], FIG["shoulder_y"]), (x + FIG["arm_w"], FIG["shoulder_y"]),
            (x + FIG["wrist_w"], FIG["wrist_y"]), (x - FIG["wrist_w"], FIG["wrist_y"])]


# ------------------------------------------------------------------ розрахунок
def lamp_audit():
    """Скільки ламп у базі і скільки місць для них описано.

    Опис у params.json («Голова 4, плечі 2, груди, коліно, стопа») дає девʼять
    точок при qty 8. Схему цікавить не «як замазати», а чи видно розбіжність."""
    out = []
    for key in LAMP_D:
        spots = sum(len(s["x"]) for s in M["lamps"] if s["fixture"] == key)
        out.append(dict(key=key, name=FX[key]["name"], qty=FX[key]["qty"],
                        d_mm=LAMP_D[key], w_unit=FX[key]["w_unit"], spots=spots,
                        gap=spots - FX[key]["qty"]))
    return out


def lamp_watts():
    """Скільки бере все точкове світло корпусу — без ядра, воно рахується окремо."""
    return sum(FX[a["key"]]["qty"] * FX[a["key"]]["w_unit"] for a in lamp_audit())


def true_lamp_px():
    """Якою була б лампа Ø12 мм у масштабі схеми — обґрунтування збільшених позначок."""
    return mm(LAMP_D["led12"])


def tape_bands(view):
    """Смуги стрічки на цьому виді: (запис, сторона, x0, x1, y0, y1) у частках."""
    out = []
    for t in M["tape"]:
        if view not in t["views"]:
            continue
        for side in (-1, 1):
            # Ширину смуги беремо по ВУЖЧОМУ краю: і рука, і нога донизу
            # звужуються, і якщо взяти середину, низ смуги вилізе за силует.
            if t["part"] == "arm":
                c, half = side * FIG["arm_x"], arm_half
            elif t["part"] == "leg":
                c, half = leg_cx(side), leg_half
            else:
                if side < 0:
                    continue
                c, half = 0.0, torso_half
            hw = min(half(t["y0"]), half(t["y1"]))
            out.append((t, side, c - hw, c + hw, t["y0"], t["y1"]))
    return out


# ------------------------------------------------------------------- підписи
def stack(items, ymin, ymax, gap=13):
    """Розсунути підписи по вертикалі, щоб вони не налазили один на одного.

    Кожен підпис хоче стати навпроти свого елемента; коли елементи стоять
    щільно (груди, радар і динамік — усе на 30 пікселях торса), підписи
    роз'їжджаються, а виноски лишаються похилими."""
    items = sorted(items, key=lambda it: it["y"])
    hs = [(len(it["lines"]) - 1) * LINE_H for it in items]
    ys = [it["y"] for it in items]
    cur = ymin
    for i in range(len(items)):
        ys[i] = max(ys[i], cur)
        cur = ys[i] + hs[i] + gap
    cur = ymax
    for i in range(len(items) - 1, -1, -1):
        ys[i] = min(ys[i], cur - hs[i])
        cur = ys[i] - gap
    if ys and ys[0] < ymin - 0.5:
        raise SystemExit("підписів більше, ніж влазить у колонку — треба ширше полотно")
    return list(zip(items, ys))


def _text(x, y, s, fill=TXT2, size=11, anchor="start", weight=None):
    w = f' font-weight="{weight}"' if weight else ""
    return (f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" font-size="{size}" '
            f'fill="{fill}"{w}>{s}</text>')


def _column(items, x, anchor, ymin, ymax):
    """Колонка підписів з виносками-волосінями до самих елементів."""
    o = []
    for it, y in stack(items, ymin, ymax):
        ex, ey = it["at"]
        if anchor == "end":
            knee_x, near_x = x + 30, x + 12
        else:
            knee_x, near_x = x - 30, x - 12
        o.append(f'<polyline points="{ex:.1f},{ey:.1f} {knee_x},{ey:.1f} '
                 f'{near_x},{y - 4:.0f}" fill="none" stroke="{HAIR}" stroke-width="0.9"/>')
        for i, (s, fill, size) in enumerate(it["lines"]):
            o.append(_text(x, y + i * LINE_H, s, fill, size, anchor,
                           "600" if i == 0 else None))
    return o


# ------------------------------------------------------------------ креслення
def _poly(view, pts, fill=BODY, stroke=INK, sw=1.6):
    d = " ".join(f"{fx(view, a):.1f},{fy(b):.1f}" for a, b in pts)
    return (f'<polygon points="{d}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw}" stroke-linejoin="round"/>')


def silhouette(view):
    """Силует: торс, ноги, стопи, шия, шолом, руки. Спереду — ще щиток."""
    o = [_poly(view, _torso())]
    for s in (-1, 1):
        o.append(_poly(view, _leg(s)))
        o.append(_poly(view, _foot(s)))
    o.append(f'<rect x="{fx(view, -FIG["neck_w"]):.1f}" y="{fy(1 - FIG["head_h"]):.1f}" '
             f'width="{2 * FIG["neck_w"] * FIG_PX:.1f}" '
             f'height="{(1 - FIG["head_h"] - FIG["shoulder_y"]) * FIG_PX:.1f}" '
             f'fill="{BODY}" stroke="{INK}" stroke-width="1.6"/>')
    o.append(f'<rect x="{fx(view, -FIG["head_w"]):.1f}" y="{fy(1.0):.1f}" '
             f'width="{2 * FIG["head_w"] * FIG_PX:.1f}" '
             f'height="{FIG["head_h"] * FIG_PX:.1f}" '
             f'rx="{FIG["head_w"] * FIG_PX * 0.5:.1f}" '
             f'fill="{BODY}" stroke="{INK}" stroke-width="1.6"/>')
    if view == "front":
        v = M["visor"]
        o.append(f'<rect x="{fx(view, -v["x"]):.1f}" y="{fy(v["y1"]):.1f}" '
                 f'width="{2 * v["x"] * FIG_PX:.1f}" '
                 f'height="{(v["y1"] - v["y0"]) * FIG_PX:.1f}" rx="3" '
                 f'fill="{PLATE}" stroke="{INK}" stroke-width="1.2"/>')
    for s in (-1, 1):
        o.append(_poly(view, _arm(s)))
    return o


def deck(view):
    """Настил подіуму під ногами — орієнтир, а не тема схеми."""
    x0, x1 = CX[view] - DECK_HALF, CX[view] + DECK_HALF
    return [f'<rect x="{x0}" y="{GROUND_Y}" width="{2 * DECK_HALF}" '
            f'height="{DECK_EDGE}" fill="{PLATE}" stroke="{HAIR}" stroke-width="1.5"/>',
            f'<line x1="{x0}" y1="{GROUND_Y}" x2="{x1}" y2="{GROUND_Y}" '
            f'stroke="{INK}" stroke-width="1.5"/>']


def tape(view):
    o = []
    for t, _side, x0, x1, y0, y1 in tape_bands(view):
        o.append(f'<rect x="{fx(view, x0):.1f}" y="{fy(y1):.1f}" '
                 f'width="{(x1 - x0) * FIG_PX:.1f}" height="{(y1 - y0) * FIG_PX:.1f}" '
                 f'fill="{TAPE_FILL[t["color"]]}" stroke="{TAPE_LINE[t["color"]]}" '
                 f'stroke-width="1.5" stroke-dasharray="{GHOST}"/>')
    return o


def lamps(view):
    o = []
    for s in M["lamps"]:
        if s["view"] != view:
            continue
        for xf in s["x"]:
            x, y = fx(view, xf), fy(s["y"])
            # Сама лампа малюється однаково завжди — пунктиром позначаємо не її,
            # а НЕВІДОМЕ МІСЦЕ: окремим кільцем навколо. Якщо пунктиром робити
            # сам контур Ø8 мм, з нього лишається три штрихи і виходить не
            # «місце під питанням», а брудна крапка.
            if s.get("assumed"):
                o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{LAMP_R + 3.4}" '
                         f'fill="none" stroke="{TXT2}" stroke-width="1" '
                         f'stroke-dasharray="2 2"/>')
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{LAMP_R}" fill="{WHITE}" '
                     f'stroke="{ACC}" stroke-width="1.8"/>')
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.3" fill="{ACC}"/>')
    return o


def radar(view):
    if RADAR["view"] != view:
        return []
    s = mm(RADAR["size_mm"])
    x, y = fx(view, RADAR["x"]), fy(RADAR["y"])
    return [f'<rect x="{x - s / 2:.1f}" y="{y - s / 2:.1f}" width="{s:.1f}" '
            f'height="{s:.1f}" fill="{WHITE}" stroke="{SIG}" stroke-width="1.8" '
            f'stroke-dasharray="{GHOST}"/>',
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.2" fill="{SIG}"/>']


def speaker(view):
    if SPK["view"] != view:
        return []
    r = mm(SPK["d_mm"]) / 2
    x, y = fx(view, SPK["x"]), fy(SPK["y"])
    o = [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{WHITE}" '
         f'stroke="{GOOD}" stroke-width="1.8"/>']
    for k in (0.72, 0.46, 0.2):
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * k:.1f}" fill="none" '
                 f'stroke="{GOOD}" stroke-width="0.9"/>')
    o.append(f'<line x1="{x:.1f}" y1="{y + r + 3:.1f}" x2="{x:.1f}" '
             f'y2="{y + r + 20:.1f}" stroke="{GOOD}" stroke-width="1.8" '
             f'marker-end="url(#rf-down)"/>')
    return o


def core(view):
    """Ядро на спині — тільки для масштабу, деталі в lights/model/back_core_place.py."""
    if M["back_core_view"] != view:
        return []
    r = mm(WIN["size_mm"]) / 2
    x, y = fx(view, 0), fy(FIG["core_y"])
    o = [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#f6f2e9" '
         f'stroke="{ACC}" stroke-width="1.8"/>']
    for i in range(1, 4):
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * i / 4:.1f}" fill="none" '
                 f'stroke="{ACC}" stroke-width="0.9"/>')
    return o


def front_labels():
    """Підписи фігури спереду.

    Усі лампи виведені ЛІВОРУЧ, а вузли грудей і стрічка — ПРАВОРУЧ. Так
    зроблено не для краси: виноска чіпляється за той бік елемента, у який вона
    йде, і тоді жодна не тягнеться через увесь торс навскіс."""
    left, mid = [], []
    for s in M["lamps"]:
        if s["view"] != "front":
            continue
        d = LAMP_D[s["fixture"]]
        left.append(dict(y=fy(s["y"]),
                         at=(fx("front", min(s["x"])) - LAMP_R, fy(s["y"])), lines=[
            (s["place"], INK, 12),
            (f'{len(s["x"])} × Ø{d} мм', TXT2, 11)]))

    half = mm(RADAR["size_mm"]) / 2
    mid.append(dict(y=fy(RADAR["y"]),
                    at=(fx("front", RADAR["x"]) + half, fy(RADAR["y"]) - half), lines=[
        ("вікно радара", INK, 12),
        (f'{RADAR["size_mm"]} × {RADAR["size_mm"]} мм', SIG, 11),
        ("діелектрик, без металу", TXT2, 11)]))

    r = mm(SPK["d_mm"]) / 2
    mid.append(dict(y=fy(SPK["y"]),
                    at=(fx("front", SPK["x"]) + r * 0.71, fy(SPK["y"]) - r * 0.71), lines=[
        ("динамік", INK, 12),
        (f'Ø{SPK["d_mm"]} мм, мембраною вниз', GOOD, 11),
        ("гриль і тканина від пилу", TXT2, 11)]))

    shin = next(t for t in M["tape"] if t["part"] == "leg")
    ym = (shin["y0"] + shin["y1"]) / 2
    mid.append(dict(y=fy(ym), at=(fx("front", leg_cx(1) + leg_half(ym)), fy(ym)), lines=[
        (f'стрічка №{shin["spec"]}, {shin["color"]}', INK, 12),
        (shin["place"], TXT2, 11)]))

    return _column(left, 150, "end", 172, LAB_BOTTOM) + \
        _column(mid, 362, "start", 172, LAB_BOTTOM)


def rear_labels():
    """Підписи фігури ззаду: ядро і дві смуги стрічки, які видно саме звідси."""
    items = []
    r = mm(WIN["size_mm"]) / 2
    y = fy(FIG["core_y"])
    items.append(dict(y=y, at=(fx("rear", 0) + r * 0.71, y - r * 0.71), lines=[
        ("ядро на спині", INK, 12),
        (f'Ø{WIN["size_mm"]:g} мм, {MOD["diodes"]} '
         f'{plural(MOD["diodes"], DIODE_W)}', ACC, 11)]))
    for t in M["tape"]:
        if t["part"] != "arm":
            continue
        ym = (t["y0"] + t["y1"]) / 2
        items.append(dict(y=fy(ym),
                          at=(fx("rear", FIG["arm_x"] + arm_half(ym)), fy(ym)), lines=[
            (f'стрічка №{t["spec"]}, {t["color"]}', INK, 12),
            (t["place"], TXT2, 11)]))
    return _column(items, 776, "start", 172, LAB_BOTTOM)


def scale_bar():
    """Масштабна лінійка між фігурами — щоб розмір читався без арифметики."""
    step_m = FIG_H_M / SCALE_STEPS
    ln = step_m * PPM
    x0 = (CX["front"] + CX["rear"]) / 2 - ln / 2
    return [f'<line x1="{x0:.1f}" y1="{SCALE_Y}" x2="{x0 + ln:.1f}" y2="{SCALE_Y}" '
            f'stroke="{SIG}" stroke-width="1.8" marker-start="url(#rf-dim)" '
            f'marker-end="url(#rf-dim)"/>',
            _text(x0 + ln / 2, SCALE_Y - 7, f'{step_m:g} м', SIG, 11, "middle")]


def legend():
    """Легенда: мініатюра самого елемента плюс рядок словами."""
    o, y = [], FOOT_Y
    o.append(f'<circle cx="34" cy="{y - 4}" r="{LAMP_R}" fill="{WHITE}" stroke="{ACC}" '
             f'stroke-width="1.8"/>')
    o.append(_text(52, y, "активне світло: лампи на корпусі і ядро на спині"))
    y += FOOT_STEP
    o.append(f'<rect x="28" y="{y - 10}" width="12" height="12" fill="{WHITE}" '
             f'stroke="{SIG}" stroke-width="1.8" stroke-dasharray="{GHOST}"/>')
    o.append(_text(52, y, "вікно радара — тільки діелектрик, крізь метал не бачить"))
    y += FOOT_STEP
    o.append(f'<circle cx="34" cy="{y - 4}" r="6" fill="{WHITE}" stroke="{GOOD}" '
             f'stroke-width="1.8"/>')
    o.append(f'<circle cx="34" cy="{y - 4}" r="2.8" fill="none" stroke="{GOOD}" '
             f'stroke-width="0.9"/>')
    o.append(_text(52, y, "динамік мембраною вниз, гриль і протипилова тканина"))
    y += FOOT_STEP
    o.append(f'<rect x="26" y="{y - 9}" width="16" height="10" fill="{WHITE}" '
             f'stroke="{INK}" stroke-width="1.5"/>')
    o.append(f'<rect x="26" y="{y + 9}" width="16" height="10" '
             f'fill="{TAPE_FILL["жовта"]}" stroke="{WARN}" stroke-width="1.5"/>')
    o.append(_text(52, y, "світловідбивна стрічка: №3 і №4 білі,"))
    y += FOOT_STEP
    o.append(_text(52, y, "№5 жовта — ріжеться по формі місця"))
    y += FOOT_STEP
    o.append(_text(52, y, "№ — номер позиції у специфікації конструктора", TXT2, 11))
    y += FOOT_STEP
    o.append(f'<line x1="26" y1="{y - 4}" x2="42" y2="{y - 4}" stroke="{TXT2}" '
             f'stroke-width="1.8" stroke-dasharray="{GHOST}"/>')
    o.append(_text(52, y, "пунктир — місце припущене, у кресленні його нема"))
    return o


def notes():
    """Підвал праворуч: що саме в цій схемі недосказане і чому."""
    out = []
    for a in lamp_audit():
        if a["gap"]:
            out.append(f'у базі {a["qty"]} {plural(a["qty"], LAMP_W)} Ø{a["d_mm"]} мм, '
                       f'а місць в описі {a["spots"]} — розбіжність показуємо')
    out += [
        'лампи стоять у передній стінці оболонки — ззаду їх не видно',
        f'позначка лампи збільшена: у масштабі схеми Ø{LAMP_D["led12"]} мм — '
        f'це {true_lamp_px():.1f} точки',
        'місця стрічки і вікна радара умовні — у кресленні їх нема',
        'ядро на спині — своя схема і свої числа, тут воно для масштабу',
    ]
    o, y = [], FOOT_Y
    for s in out:
        o.append(_text(NOTE_X, y, s))
        y += FOOT_STEP
    return o


def svg():
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" '
         f'font-family="ui-monospace,Menlo,monospace">',
         '<defs>'
         '<marker id="rf-down" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
         f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" '
         f'fill="{GOOD}"/></marker>'
         '<marker id="rf-dim" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
         f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" '
         f'fill="{SIG}"/></marker>'
         '</defs>']

    a12, a8 = lamp_audit()
    # «по стільки-то ват» пишемо тільки якщо обидва типи справді однакові:
    # варто комусь у базі розвести їх по потужності — рядок почав би брехати.
    same_w = f' по {a12["w_unit"]:g} Вт' if a12["w_unit"] == a8["w_unit"] else ""
    o.append(_text(W / 2, 24, "Що змонтовано на самій фігурі вартового", INK, 14, "middle"))
    o.append(_text(W / 2, 42,
                   f'{a12["qty"]} {plural(a12["qty"], LAMP_W)} Ø{a12["d_mm"]} мм і '
                   f'{a8["qty"]} {plural(a8["qty"], LAMP_W)} Ø{a8["d_mm"]} мм{same_w} · '
                   f'динамік · вікно радара · ядро на спині', TXT2, 11, "middle"))
    o.append(_text(W / 2, 60,
                   f'фігура {FIG_H_M:.1f} м над настилом · обидва види в одному '
                   f'масштабі · разом точкове світло корпусу {lamp_watts():.1f} Вт',
                   TXT2, 11, "middle"))

    for v in M["views"]:
        view = v["key"]
        o.append(_text(CX[view], CAP_Y, v["label"], INK, 12, "middle", "600"))
        o += deck(view)
        o += silhouette(view)
        o += tape(view)
        o += lamps(view)
        o += radar(view)
        o += speaker(view)
        o += core(view)

    o.append(_text(CX["front"], GROUND_Y + 26, "настил подіуму", TXT2, 11, "middle"))
    o += scale_bar()
    o += front_labels()
    o += rear_labels()
    o += legend()
    o += notes()
    o.append("</svg>")
    return "\n".join(o)


def main():
    for a in lamp_audit():
        gap = "" if not a["gap"] else f'  ⚠ місць в описі {a["spots"]}, різниця {a["gap"]:+d}'
        print(f'{a["name"]}: {a["qty"]} шт × {a["w_unit"]} Вт, Ø{a["d_mm"]} мм{gap}')
    print(f'точкове світло корпусу разом {lamp_watts():.1f} Вт '
          f'(ядро на спині рахується окремо)')
    print(f'динамік Ø{SPK["d_mm"]} мм мембраною вниз · вікно радара '
          f'{RADAR["size_mm"]}×{RADAR["size_mm"]} мм під {SENSOR["type"]}, '
          f'зона {SENSOR["range_m"]:g} м')
    print(f'ядро на спині Ø{WIN["size_mm"]:g} мм, {MOD["diodes"]} '
          f'{plural(MOD["diodes"], DIODE_W)} — найбільша річ на корпусі')
    for t in M["tape"]:
        print(f'  стрічка №{t["spec"]} {t["color"]}: {t["place"]} '
              f'({"місце умовне" if t.get("assumed") else "з креслення"})')
    print(f'фігура {FIG_H_M:.1f} м · масштаб {PPM:.0f} px/м · лампа Ø{LAMP_D["led12"]} мм '
          f'у ньому — {true_lamp_px():.1f} px, тому позначки збільшені')
    (HERE / "robot_fixtures.svg").write_text(svg())
    print("креслення: robot_fixtures.svg")


if __name__ == "__main__":
    main()
