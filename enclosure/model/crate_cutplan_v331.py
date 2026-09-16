#!/usr/bin/env python3
"""ПОВНИЙ перелік усіх брусків каркаса — щоб пройтись по купі й позначити, чого нема.

Іван 28.08.2026: «нарисуй рез… всіх палок, і я перевірю що є а чого ні».

Тому це не план різу однієї дошки, а ЗВІРЯЛЬНИЙ ЛИСТ: усі 28 шматків каркаса в одному
місці, відсортовані за довжиною — бо звіряти купу зручно рулеткою від найдовшого, а не
за номерами з креслення.

Звідки що:
  · No.1-No.8  — перший розкрій, аркуш 06.24 рев. 3.3 (Володимир, 24.08). Мали бути
    нарізані ще в Сан-Франциско;
  · №9, №10, №11 — креслення 06.26 рев. 3.3.1 (27.08), розміщення ДВОХ панелей;
  · укосини    — повідомлення 28.08 07:02, «враховуючи можливий сильний вітер».

Друга частина картинки — звідки різати нові дев'ять: сім виходять з обрізків першого
розкрою, і лише два №9 потребують нової дошки. Саме тому купувати треба одну, а не три.

    crate_cutplan_v331.py            намалювати
    crate_cutplan_v331.py --selftest перевірити, що розкрій і перелік сходяться
"""
import sys
from fractions import Fraction
from pathlib import Path

KERF = 3
BOARD = 2438
OUT = Path("/root/hero-armor/private/quotes")

# (мітка, довжина, шт, переріз, різ, призначення, партія)
PIECES = [
    ("No.1",  2240, 2, "2x4", "straight", "нижні базові балки",              "перший розкрій"),
    ("No.5",  1750, 2, "2x3", "angle30",  "похилі балки під панель",         "перший розкрій"),
    ("No.8",  1354, 2, "2x3", "straight", "балка під ящик станції",          "перший розкрій"),
    ("No.3",  1200, 2, "2x3", "straight", "рейки кріплення панелей",         "перший розкрій"),
    ("№11",   1142, 1, "2x3", "straight", "перемичка зверху (38+1066+38)",   "НОВЕ 3.3.1"),
    ("No.6",  1100, 1, "2x3", "angle",    "задній розкіс",                   "перший розкрій"),
    ("No.4",  1066, 2, "2x3", "straight", "нижні поперечини під ящик",       "перший розкрій"),
    ("No.6",   990, 2, "2x3", "straight", "верхня рейка і поперечини",       "перший розкрій"),
    ("No.7",   960, 2, "2x3", "angle",    "передні розкоси",                 "перший розкрій"),
    ("No.2",   844, 2, "2x4", "straight", "вертикальні стійки",              "перший розкрій"),
    ("No.8",   713, 2, "2x3", "angle37",  "діагоналі, V з базою 1134",       "перший розкрій"),
    ("№9",     700, 2, "2x3", "straight", "подовження під ДРУГУ панель",     "НОВЕ 3.3.1"),
    ("укосина", 500, 2, "2x3", "angle",   "підкіс проти вітру, з обох боків", "НОВЕ 28.08"),
    ("№10",    200, 4, "2x3", "straight", "проставки під кутики кріплення",  "НОВЕ 3.3.1"),
]

# звідки різати НОВІ дев'ять: (джерело, повна довжина, [(мітка, довжина, різ)])
CUT = [
    ("обрізок", 1335, [("№11", 1142, "straight")]),
    ("НОВА дошка 8 ft", BOARD, [("№9", 700, "straight"), ("№9", 700, "straight")]),
    ("обрізок", 685, [("укосина", 500, "angle")]),
    ("обрізок", 685, [("укосина", 500, "angle")]),
    ("обрізок", 512, [("№10", 200, "straight"), ("№10", 200, "straight")]),
    ("обрізок", 452, [("№10", 200, "straight"), ("№10", 200, "straight")]),
]
COL = {"straight": "#2e7d32", "angle": "#e65100", "angle30": "#e65100", "angle37": "#e65100"}
CUTNAME = {"straight": "рівно 90°", "angle": "під кут, за місцем",
           "angle30": "верх під 30°", "angle37": "обидва кінці 37°"}


def inch(mm: int) -> str:
    i = mm / 25.4
    w = int(i)
    f = Fraction(round((i - w) * 16), 16)
    if f == 1:
        w, f = w + 1, Fraction(0)
    return f'{w}"' + (f" {f.numerator}/{f.denominator}" if f else "")


def svg() -> str:
    # SC підібраний так, щоб найдовший брусок (2240 мм) лишався в межах смуги 325 px —
    # інакше колонка з довжиною налазить на смугу, а на коротких деталях підпис налазить
    # на саму смугу (спіймано очима на першій версії: «укосина» поверх «500 мм»).
    LEFT, SC, ROW, BARH = 92, 0.145, 40, 24
    W, TOP = 1180, 118
    H = TOP + ROW * len(PIECES) + 130 + 52 + 66 * len(CUT) + 70
    y = TOP
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family="DejaVu Sans, Arial">',
         f'<rect width="{W}" height="{H}" fill="white"/>',
         '<text x="30" y="42" font-size="27" font-weight="bold">'
         'УСІ БРУСКИ КАРКАСА — звіряльний лист</text>',
         '<text x="30" y="68" font-size="14" fill="#555">'
         'Відсортовано за довжиною: іди по купі з рулеткою від найдовшого. '
         'Зелене — рівно 90°, помаранчеве — під кут.</text>',
         '<text x="30" y="90" font-size="14" fill="#b00" font-weight="bold">'
         'Червоним — те, що додалось після оновлення каркаса (креслення 3.3.1 і укосини).</text>',
         f'<text x="30" y="{y-6}" font-size="13" font-weight="bold" fill="#666">✓</text>'
         f'<text x="{LEFT}" y="{y-6}" font-size="13" font-weight="bold" fill="#666">деталь</text>'
         f'<text x="{LEFT+340}" y="{y-6}" font-size="13" font-weight="bold" fill="#666">довжина</text>'
         f'<text x="{LEFT+470}" y="{y-6}" font-size="13" font-weight="bold" fill="#666">шт</text>'
         f'<text x="{LEFT+512}" y="{y-6}" font-size="13" font-weight="bold" fill="#666">переріз</text>'
         f'<text x="{LEFT+580}" y="{y-6}" font-size="13" font-weight="bold" fill="#666">різ</text>'
         f'<text x="{LEFT+720}" y="{y-6}" font-size="13" font-weight="bold" fill="#666">куди</text>']
    total = 0
    for tag, L, q, sec, how, what, batch in PIECES:
        new = batch != "перший розкрій"
        col = COL[how]
        total += q
        for i in range(q):                       # окремий квадратик на КОЖЕН шматок
            o.append(f'<rect x="{24+i*16}" y="{y+2}" width="13" height="13" '
                     f'fill="white" stroke="#888" stroke-width="1.4"/>')
        if new:                                  # нові — світлою смугою на весь рядок
            o.append(f'<rect x="24" y="{y-4}" width="{W-48}" height="{BARH+8}" '
                     f'fill="#b00" fill-opacity="0.05"/>')
        o.append(f'<rect x="{LEFT}" y="{y}" width="{L*SC:.0f}" height="{BARH}" '
                 f'fill="{col}" fill-opacity="0.15" stroke="{col}" stroke-width="2"/>')
        o.append(f'<text x="{LEFT+6}" y="{y+17}" font-size="13" font-weight="bold" '
                 f'fill="{"#b00" if new else "#111"}">{tag}</text>')
        # довжина стоїть у СВОЇЙ колонці, а не всередині смуги — коротка деталь інакше
        # не вміщає підпис і текст лягає один на одного
        o.append(f'<text x="{LEFT+340}" y="{y+17}" font-size="12" fill="#111">'
                 f'{L} мм · {inch(L)}</text>')
        o.append(f'<text x="{LEFT+470}" y="{y+17}" font-size="13" font-weight="bold">×{q}</text>')
        o.append(f'<text x="{LEFT+512}" y="{y+17}" font-size="12" fill="#555">{sec}"</text>')
        o.append(f'<text x="{LEFT+580}" y="{y+17}" font-size="12" fill="{col}">{CUTNAME[how]}</text>')
        o.append(f'<text x="{LEFT+720}" y="{y+17}" font-size="12" fill="#333">{what}</text>')
        y += ROW
    n24 = sum(p[2] for p in PIECES if p[3] == "2x4")
    o.append(f'<text x="30" y="{y+24}" font-size="16" font-weight="bold">'
             f'РАЗОМ {total} шматків: {n24} з бруса 2×4" і {total-n24} з 2×3". '
             f'Нових після оновлення — 9.</text>')

    # ---- друга частина: звідки різати нові
    y += 62
    o.append(f'<text x="30" y="{y}" font-size="21" font-weight="bold">'
             f'ЗВІДКИ РІЗАТИ ДЕВ\'ЯТЬ НОВИХ</text>')
    o.append(f'<text x="30" y="{y+24}" font-size="14" fill="#b00" font-weight="bold">'
             f'Сім виходять з обрізків. Купити треба ОДНУ дошку 2×3" × 8 ft — на два №9.</text>')
    # Чесна примітка: довжини обрізків ПОРАХОВАНІ з першого розкрою, а не заміряні.
    # Аркуш іде і конструктору теж, тому він мусить бачити, що це розрахунок.
    o.append(f'<text x="30" y="{y+44}" font-size="12.5" fill="#666">'
             f'Довжини обрізків пораховані з розкрою аркуша 06.24 (кожна дошка 2438 мм, '
             f'пропил 3 мм), по факту не заміряні — перевірити рулеткою перед різом.</text>')
    y += 70
    SC2, BARH2, ROW2, L2 = 0.30, 40, 66, 200
    for src, full, cuts in CUT:
        new = src.startswith("НОВА")
        o.append(f'<text x="30" y="{y+19}" font-size="14" font-weight="bold" '
                 f'fill="{"#b00" if new else "#333"}">{src}</text>')
        o.append(f'<text x="30" y="{y+36}" font-size="12" fill="#777">{full} мм</text>')
        o.append(f'<rect x="{L2}" y="{y}" width="{full*SC2:.0f}" height="{BARH2}" '
                 f'fill="{"#fff3f0" if new else "#f3ede2"}" '
                 f'stroke="{"#b00" if new else "#9c8f7a"}" stroke-width="2"/>')
        x, used = L2, 0
        for part, L, how in cuts:
            col = COL[how]
            w = L * SC2
            o.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{BARH2}" '
                     f'fill="{col}" fill-opacity="0.16" stroke="{col}" stroke-width="3"/>')
            o.append(f'<text x="{x+w/2:.0f}" y="{y+17}" font-size="14" fill="{col}" '
                     f'text-anchor="middle" font-weight="bold">{part}</text>')
            o.append(f'<text x="{x+w/2:.0f}" y="{y+34}" font-size="12" fill="#111" '
                     f'text-anchor="middle">{L} мм</text>')
            used += L + KERF
            x += w
            o.append(f'<line x1="{x:.1f}" y1="{y-8}" x2="{x:.1f}" y2="{y+BARH2+8}" '
                     f'stroke="#c00" stroke-width="2" stroke-dasharray="5,4"/>')
        o.append(f'<text x="{L2+full*SC2+12:.0f}" y="{y+25}" font-size="12" fill="#777">'
                 f'лишиться {full-used+KERF} мм</text>')
        y += ROW2
    o.append(f'<text x="30" y="{y+18}" font-size="14" font-weight="bold" fill="#b00">'
             f'Порядок: №11 з довгого обрізка → №9 з нової дошки → укосини останніми, за місцем.</text>')
    o.append(f'<text x="30" y="{y+40}" font-size="13">'
             f'Підписуй кожен шматок одразу після різу.</text>')
    o.append('</svg>')
    return "\n".join(o)


def selftest() -> int:
    for src, full, cuts in CUT:
        need = sum(L for _, L, _ in cuts) + KERF * len(cuts)
        assert need <= full, f"{src} {full}: треба {need} мм"
    new_needed = {}
    for tag, L, q, _s, _h, _w, batch in PIECES:
        if batch != "перший розкрій":
            new_needed[(tag, L)] = new_needed.get((tag, L), 0) + q
    made = {}
    for _s, _f, cuts in CUT:
        for p, L, _h in cuts:
            made[(p, L)] = made.get((p, L), 0) + 1
    assert new_needed == made, f"перелік і розкрій розходяться: {new_needed} vs {made}"
    boards = [p for p in CUT if p[0].startswith("НОВА")]
    assert len(boards) == 1, "нова дошка мусить бути рівно одна"
    assert all(c[0] == "№9" for c in boards[0][2]), "з нової дошки ріжуться тільки №9"
    assert sum(q for *_, q, _s, _h, _w, _b in
               [(0, 0, p[2], p[3], p[4], p[5], p[6]) for p in PIECES]) == 28
    assert inch(1142) == '44" 15/16' and inch(2240) == '88" 3/16'
    print(f"selftest ok — 28 шматків у переліку, дев'ять нових сходяться з розкроєм")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / "crate_cutplan_v331.svg"
    f.write_text(svg())
    print("зроблено:", f)
