#!/usr/bin/env python3
"""
Живлення ядра на спині: від дванадцятивольтової шини подіуму до плати з діодами.

Ланцюг короткий, але в ньому два місця, де числа перестають бути очевидними,
і саме заради них ця схема:

  1. КРАН. На суцільному білому плата взяла б у рази більше, ніж їй колись
     дадуть узяти. Такого кадру не буде ніколи: стелю ставить не залізо, а
     ліміт струму в прошивці WLED — контролер сам притишує картинку, щойно
     вона намагається взяти більше дозволеного. Тому в бюджет ночі йде не
     паспорт плати, а виставлене нами число ампер. Без крана ядро одне
     перевищило б груповий запобіжник.
  2. ПОНИЖУВАЧ. Модуль живиться нижчою напругою, ніж шина, і частина ват
     осідає теплом усередині броні, а не світлом на спині. Її видно окремим
     числом, щоб було зрозуміло, чому понижувач треба ставити в продув.

Схема навмисно НЕ принципова: прямокутники і стрілки, а не умовні позначення.
Її читають Іван і Марсель, тому на кожній ділянці підписано рівно три речі —
напруга, струм і ватти, — а не позиційні позначення елементів.

Кожна трійка перемножується сама в собі, бо струм береться там, де він тече:
на шині — від напруги шини, на вході понижувача — від тієї напруги, що
лишилась після кабелю (понижувач бере ПОТУЖНІСТЬ, тому при просадці струм у
нього трохи більший), за понижувачем — від напруги модуля.

Окремо тонкою лінією показана лінія даних. Вона тут не для краси: у GLEDOPTO
рівневий зсув і резистор уже всередині, тому між контролером і платою нема
жодної деталі, яку треба паяти, — три дроти і все.

Числа: lights/data/back_core.json через back_core.py (ватти, струми, ліміт),
гілка і кабель — lights/data/params.json → topology через lights_node_model.py.
Просадка на кабелі рахується по тій самій таблиці опору, що й уся кабельна
лабораторія, але з ПОВНИМ струмом ділянки: контролер фізично висить на тому
самому кабелі, а в дереві сегментів він стоїть окремою позицією без власного
кабелю. Через це сторінка кабелів дає на цьому ж відводі трохи меншу просадку —
обидва числа стоять на схемі поруч, щоб розбіжність не довелося шукати.
Те саме пояснення лежить у базі: back_core.json → wiring._drop_note.
Тільки stdlib: CI збирає сайт без залежностей.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import back_core as bc          # noqa: E402  модель ядра
import lights_node_model as lm  # noqa: E402  контекст гілки і запобіжників

P = bc.P                        # lights/data/params.json
BUS_V = bc.BUS_V

MOD = bc.module()
CTRL = bc.controller()
BUCK = bc.D["buck"]
WIR = bc.D["wiring"]            # довжина лінії даних, рішення по запобіжнику
LIMIT_A = bc.D["chosen"]["current_limit_a"]
NIGHT_H = bc.D["chosen"]["night_h"]

# --------------------------------------------------------------- числа ланцюга
B = bc.draw_from_bus()          # ватти й ампери з шини, з понижувачем і контролером
TREE = {r["id"]: r for r in lm.cable_tree()}
BR = TREE[WIR["branch"]]        # гілка Гр.2 — вона ж годує подіумну стрічку
SEG = next(s for s in P["topology"]["segments"] if s["id"] == WIR["segment"])
ROW = TREE[SEG["id"]]           # той самий відвід очима кабельної лабораторії
FUSE = next(f for f in lm.fuses() if f["id"] == "g2")

A_CORE = B["peak_a"]            # скільки ядро бере з шини (пік = робота: ріже кран)
W_CORE = B["peak_w"]

# Кабель у костюм несе і понижувач, і контролер, тому просадку рахуємо з повного
# струму ділянки, а не з рядка дерева (там на сегменті підписаний лише модуль).
R_SEG = 2 * SEG["length_m"] * P["wiring"]["awg_ohm_per_m"][str(SEG["awg"])]
V_DROP = A_CORE * R_SEG
W_COPPER = A_CORE ** 2 * R_SEG
V_AT_BUCK = BR["v_at_end"] - V_DROP
V_CUM = BUS_V - V_AT_BUCK               # разом від станції: магістраль + гілка + відвід
PCT_CUM = 100 * V_CUM / BUS_V
BUDGET_PCT = P["wiring"]["drop_budget"]["relaxed_pct"]

W_BUCK_IN = W_CORE - B["ctrl_w"]
# Струм на вході понижувача рахуємо від НАПРУГИ В ЦІЙ ТОЧЦІ, а не від номіналу
# шини: понижувач — споживач потужності, тому просіла напруга означає трохи
# більший струм. Інакше підписана поруч трійка «напруга · струм · ватти» не
# перемножувалась би сама в собі: напруга стояла б після просадки, а струм —
# від номіналу шини.
A_BUCK_IN = W_BUCK_IN / V_AT_BUCK
W_MOD = min(B["full_w"], B["cap_w"])     # стеля, яку тримає кран
A_MOD = W_MOD / MOD["v"]
W_HEAT = W_BUCK_IN - W_MOD               # ККД понижувача — у тепло

# Скільки б це коштувало шині БЕЗ крана — цифра для порівняння, не для бюджету.
W_BUS_OPEN = B["full_w"] / B["buck_eff"] + B["ctrl_w"]
A_BUS_OPEN = W_BUS_OPEN / BUS_V

FUSE_NEED_A = A_CORE * P["fusing"]["derate"]
FUSE_OWN_A = next(a for a in P["fusing"]["standard_a"] if a >= FUSE_NEED_A)

# --------------------------------------------------------------------- палітра
BG, PANEL = "#0b0e14", "#0f141d"
INK, DIM, LINE = "#eaf1ff", "#8e97a6", "#26436e"
GLOW, ACC = "#5b9bff", "#e08b3e"

W, H = 900, 740
BX, BW = 60, 380                 # колонка блоків
BH, GAP = 62, 48                 # висота блока і проміжок під стрілку
Y0 = 78
CX = BX + BW / 2
PX, PW = 480, 380                # права колонка

# Ідентифікатори всередині <defs> префіксуємо: сторінка лабораторії інлайнить
# усі схеми ядра в ОДИН документ, а url(#id) резолвиться в перший збіг по всьому
# DOM — без префікса сусідня схема забрала б собі наші наконечники стрілок.
M_PW, M_DT = "wir_pw", "wir_dt"


GRP = P["groups"]["g2"]["label"].split(" · ")[0]   # «Гр.2» без розшифровки


def _a(v):
    """Ампери без зайвої точності: 14.5, але 0.78 — щоб не губити десяті там,
    де вони і є весь сенс."""
    return f"{v:.1f}" if v >= 10 else f"{v:.2f}".rstrip("0").rstrip(".")


def _diodes(n):
    """«241 діод», але «24 діоди» і «60 діодів».

    Модуль у базі змінний (chosen.module — є варіанти на 24, 60, 64, 256 діодів),
    тому закінчення рахуємо з самого числа, а не вписуємо словом: інакше зміна
    модуля тихо зробить на схемі граматичну помилку."""
    t1, t2 = n % 10, n % 100
    if t1 == 1 and t2 != 11:
        word = "діод"
    elif t1 in (2, 3, 4) and t2 not in (12, 13, 14):
        word = "діоди"
    else:
        word = "діодів"
    return f"{n} {word}"


def _y(i):
    return Y0 + i * (BH + GAP)


def _t(x, y, s, size=10, fill=INK, anchor="start"):
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" fill="{fill}"'
            f'{"" if anchor == "start" else f" text-anchor={chr(34)}{anchor}{chr(34)}"}'
            f'>{s}</text>')


def _box(i, title, sub, accent=False):
    """Блок ланцюга: назва зверху, під нею — що з нею відбувається по числах."""
    y = _y(i)
    stroke = ACC if accent else LINE
    o = [f'<rect x="{BX}" y="{y}" width="{BW}" height="{BH}" rx="8" fill="{PANEL}" '
         f'stroke="{stroke}" stroke-width="1.4"/>',
         _t(BX + 16, y + 23, title, 12, INK)]
    for k, s in enumerate(sub):
        o.append(_t(BX + 16, y + 40 + k * 13, s, 9, DIM))
    return o


def _arrow(i, lines, x=None, color=GLOW, width=2.4, marker=M_PW,
           label_x=None, anchor="start", dash=None):
    """Стрілка в проміжку під блоком i, з підписом «напруга · струм · ватти»."""
    x = CX if x is None else x
    y1, y2 = _y(i) + BH + 4, _y(i + 1) - 4
    d = f' stroke-dasharray="{dash}"' if dash else ""
    o = [f'<line x1="{x:.0f}" y1="{y1:.0f}" x2="{x:.0f}" y2="{y2:.0f}" '
         f'stroke="{color}" stroke-width="{width}"{d} marker-end="url(#{marker})"/>']
    lx = (x + 14) if label_x is None else label_x
    for k, s in enumerate(lines):
        o.append(_t(lx, y1 + 14 + k * 13, s, 9, color if k == 0 else DIM, anchor))
    return o


def _bar(x, y, w_val, w_max, width, color):
    """Смужка порівняння: скільки взяв би модуль без крана і скільки бере з ним."""
    return (f'<rect x="{x:.0f}" y="{y:.0f}" width="{max(2, width * w_val / w_max):.0f}" '
            f'height="11" rx="3" fill="{color}"/>')


def svg():
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'font-family="ui-monospace,Menlo,monospace">',
         '<defs>'
         f'<marker id="{M_PW}" markerUnits="userSpaceOnUse" markerWidth="10" '
         f'markerHeight="10" refX="7" refY="3.5" orient="auto">'
         f'<path d="M0,0 L7,3.5 L0,7 z" fill="{GLOW}"/></marker>'
         f'<marker id="{M_DT}" markerUnits="userSpaceOnUse" markerWidth="10" '
         f'markerHeight="10" refX="7" refY="3.5" orient="auto">'
         f'<path d="M0,0 L7,3.5 L0,7 z" fill="{DIM}"/></marker>'
         '</defs>',
         f'<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>',
         _t(BX, 34, f'Живлення ядра на спині: шина {BUS_V:.0f} В → '
                    f'{_diodes(MOD["diodes"])} {MOD["chip"]}', 13, INK),
         _t(BX, 52, 'на кожній ділянці — напруга, струм і ватти в тій самій точці '
                    'ланцюга', 10, DIM)]

    # ------------------------------------------------------------- ланцюг живлення
    o += _box(0, f'Шина {BUS_V:.0f} В · щит подіуму', [
        f'гілка {GRP} ({BR["id"]}) · AWG {BR["awg"]} · {BR["length_m"]:.1f} м · '
        f'{BR["load_w"]:.1f} Вт',
        'та сама гілка годує подіумну стрічку'])
    o += _arrow(0, [f'{BUS_V:.0f} В · {_a(BR["amps"])} А · {BR["load_w"]:.1f} Вт',
                    'уся гілка через запобіжник'])

    o += _box(1, f'Запобіжник {GRP} · {FUSE["rating"]:g} А', [
        f'{_a(FUSE["amps"])} А × запас {P["fusing"]["derate"]:g} → '
        f'{FUSE["rating"]:g} А зі стандартного ряду',
        f'свого ядро не має: йому треба {FUSE_NEED_A:.1f} А, а ряд починається з '
        f'{P["fusing"]["standard_a"][0]:g} А'])
    o += _arrow(1, [f'{BUS_V:.0f} В · {_a(A_CORE)} А · {W_CORE:.1f} Вт',
                    'стільки ядро бере з шини'])

    o += _box(2, f'Кабель у костюм · {SEG["awg"]} AWG · {SEG["length_m"]:.1f} м', [
        f'{SEG["id"]} · −{V_DROP:.2f} В у міді, {W_COPPER:.2f} Вт на нагрів',
        f'на кінці {V_AT_BUCK:.1f} В · просадка від повних {_a(A_CORE)} А — '
        f'контролер тут же'])
    # Другий рядок підпису тримаємо коротким навмисно: правіше PX починається
    # панель висновків, і довгий текст просто заїде під неї.
    o += _arrow(2, [f'{V_AT_BUCK:.1f} В · {_a(A_BUCK_IN)} А · {W_BUCK_IN:.1f} Вт',
                    'на вході понижувача, вже після просадки'])

    o += _box(3, f'Понижувач {BUS_V:.0f}→{MOD["v"]:.0f} В · ККД {BUCK["efficiency"]}', [
        f'{BUCK["model"]} · {W_HEAT:.2f} Вт іде в тепло',
        f'{B["ctrl_w"]:.1f} Вт контролера модель лічить прямо на шині'])
    o += _arrow(3, [f'{MOD["v"]:.0f} В · {_a(A_MOD)} А · {W_MOD:.1f} Вт',
                    'стеля, яку тримає кран'])

    o += _box(4, f'Контролер {CTRL["name"].split(",")[0]}', [
        f'вхід {CTRL["v_in"]} В · живлення йде крізь нього на модуль',
        f'ТУТ КРАН: ліміт струму {LIMIT_A} А в прошивці'], accent=True)
    # живлення і дані йдуть поруч: товста лінія і тонка пунктирна
    o += _arrow(4, [f'{MOD["v"]:.0f} В · {_a(A_MOD)} А'],
                x=BX + 140, label_x=BX + 128, anchor="end")
    o += _arrow(4, ['DATA ' + f'{MOD["v"]:.0f} В · ~{WIR["data_line_mm"]:.0f} мм',
                    'рівневий зсув усередині'],
                x=BX + 250, label_x=BX + 262, color=DIM, width=1.2,
                marker=M_DT, dash="5 4")

    o += _box(5, f'Модуль {_diodes(MOD["diodes"])} {MOD["chip"]} · Ø{MOD["size_mm"]} мм', [
        f'{MOD["rings"]} вкладених кілець · робоча картинка {W_MOD:.1f} Вт',
        f'суцільний білий узяв би {B["full_w"]:.1f} Вт ({_a(B["full_a_module"])} А) — '
        f'кран не пускає'])

    # ------------------------------------------------------------------ кран
    o.append(f'<rect x="{PX}" y="{Y0}" width="{PW}" height="222" rx="8" '
             f'fill="{PANEL}" stroke="{LINE}" stroke-width="1.4"/>')
    o.append(_t(PX + 16, Y0 + 24, f'Кран: ліміт {LIMIT_A} А в прошивці WLED', 12, ACC))
    bw_max = max(W_BUS_OPEN, B["full_w"])
    bar_w = PW - 32
    rows = [('модуль, суцільний білий', B["full_w"], B["full_a_module"], MOD["v"], ACC),
            ('модуль під краном', W_MOD, A_MOD, MOD["v"], GLOW),
            ('з шини без крана', W_BUS_OPEN, A_BUS_OPEN, BUS_V, ACC),
            ('з шини під краном', W_CORE, A_CORE, BUS_V, GLOW)]
    for k, (name, w_val, a_val, v_val, col) in enumerate(rows):
        ry = Y0 + 46 + k * 34
        o.append(_t(PX + 16, ry, name, 9, DIM))
        o.append(_t(PX + PW - 16, ry, f'{w_val:.1f} Вт · {_a(a_val)} А на {v_val:.0f} В',
                    9, INK, "end"))
        o.append(_bar(PX + 16, ry + 6, w_val, bw_max, bar_w, col))
    o.append(_t(PX + 16, Y0 + 196,
                f'без крана ядро одне взяло б {_a(A_BUS_OPEN)} А — більше', 9, INK))
    o.append(_t(PX + 16, Y0 + 209,
                f'за груповий запобіжник {FUSE["rating"]:g} А на всю {GRP}', 9, INK))

    # --------------------------------------------------------------- висновки
    ny = Y0 + 242
    o.append(f'<rect x="{PX}" y="{ny}" width="{PW}" height="{_y(5) + BH - ny:.0f}" '
             f'rx="8" fill="{PANEL}" stroke="{LINE}" stroke-width="1.4"/>')
    o.append(_t(PX + 16, ny + 24, 'Що з цього випливає', 12, INK))
    notes = [
        (f'Три дроти від контролера до плати: +{MOD["v"]:.0f} В, GND і DATA.',
         'Рівневий зсув і резистор — усередині GLEDOPTO, паяти нічого.'),
        (f'Кабель у броні {SEG["awg"]} AWG × {SEG["length_m"]:.0f} м зʼїдає '
         f'{V_DROP:.2f} В — на понижувач',
         f'приходить {V_AT_BUCK:.1f} В, і це для нього ще з запасом.'),
        (f'Сторінка кабелів дає тут {ROW["v_drop"]:.2f} В ({ROW["cum_pct"]:.1f}%): '
         f'у дереві на сегменті',
         f'висить лише модуль, а контролер — окремою позицією без кабелю.'),
        (f'Понижувач гріється на {W_HEAT:.2f} Вт — це ті '
         f'{100 * (1 - BUCK["efficiency"]):.0f}%, що не дійшли',
         'до плати. Ставити в продув, а не в глухий кут корпусу.'),
        (f'Свого запобіжника ядро не має: розрахунково {FUSE_NEED_A:.1f} А, а ряд',
         f'починається з {FUSE_OWN_A:g} А — це вже груповий Гр.2.'),
        (f'За ніч {NIGHT_H:.0f} год ядро бере {B["wh_night"]:.0f} Вт·год з шини —',
         'стільки тримає кран, а не стільки може плата.'),
        (f'У гілці {GRP} ядро — {100 * W_CORE / BR["load_w"]:.0f}% ват: воно і стрічка '
         f'сидять на',
         'одному кабелі AWG ' + f'{BR["awg"]}, і запобіжник у них спільний.'),
        (f'Від станції до понижувача просідає {V_CUM:.2f} В ({PCT_CUM:.1f}%)',
         f'при межі {BUDGET_PCT:.0f}% для неадресних ділянок — з запасом.'),
        ('Вдень адресне світло вимкнене: усередині броні на сонці',
         'ще гарячіше, ніж на подіумі.'),
    ]
    for k, (l1, l2) in enumerate(notes):
        y = ny + 48 + k * 36
        o.append(_t(PX + 16, y, '· ' + l1, 9, DIM))
        o.append(_t(PX + 24, y + 13, l2, 9, DIM))

    o.append(_t(BX, H - 22,
                'числа: lights/data/back_core.json через back_core.py · гілка, кабель '
                'і запобіжник — lights/data/params.json', 9, DIM))
    o.append("</svg>")
    return "\n".join(o)


def main():
    print(f'гілка {BR["id"]}: AWG {BR["awg"]} · {BR["length_m"]:.1f} м · '
          f'{BR["load_w"]:.1f} Вт / {BR["amps"]:.2f} А · запобіжник {FUSE["rating"]:g} А')
    print(f'ядро з шини: {W_CORE:.1f} Вт / {A_CORE:.2f} А '
          f'(за ніч {B["wh_night"]:.0f} Вт·год)')
    print(f'кабель {SEG["awg"]} AWG × {SEG["length_m"]:.1f} м: −{V_DROP:.2f} В '
          f'({W_COPPER:.2f} Вт у міді) → {V_AT_BUCK:.2f} В на понижувачі')
    print(f'понижувач {BUS_V:.0f}→{MOD["v"]:.0f} В: {W_BUCK_IN:.1f} Вт всередину, '
          f'{W_MOD:.1f} Вт на модуль, {W_HEAT:.2f} Вт у тепло')
    print(f'кран {LIMIT_A} А: модуль {W_MOD:.1f} Вт замість {B["full_w"]:.1f} Вт · '
          f'з шини {W_CORE:.1f} Вт замість {W_BUS_OPEN:.1f} Вт '
          f'({_a(A_BUS_OPEN)} А проти запобіжника {FUSE["rating"]:g} А)')
    print(f'у дереві кабелів той самий відвід: −{ROW["v_drop"]:.2f} В '
          f'({ROW["cum_pct"]:.1f}% від станції) — там на сегменті лише модуль, '
          f'контролер окремою позицією')
    (HERE / "back_core_wiring.svg").write_text(svg())
    print("схема: back_core_wiring.svg")


if __name__ == "__main__":
    main()
