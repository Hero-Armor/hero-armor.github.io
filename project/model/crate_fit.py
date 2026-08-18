#!/usr/bin/env python3
"""Ящик з фігурою — влізе в пікап, чи потрібен причіп.

Постановка Івана 17.08.2026: фігура готова 26.08 і одразу лягає в транспортний
ящик за розмірами Володимира. Причіп-дім Богдана відпав («не піде»), але Богдан
дає СВІЙ ПІКАП, щоб зʼїздити за фігурою в Сан-Франциско або Ріно. Повернення після
бурну теж у Ріно, а не в SF.

Тому питання змінилось: не «в який фургон орендувати», а «чи влазить ящик у кузов
пікапа, і якщо ні — який причіп треба». Ця схема рахує саме це.

Головне, що тут рахується, а не малюється: розмір ЯЩИКА виводиться з фігури плюс
поролон плюс фанера, і всі кузови міряються проти нього. Зміниться заміряна глибина
фігури — переміряються всі варіанти.

  python3 project/model/crate_fit.py  →  crate_fit.svg
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRD = json.loads((HERE.parent / "data/transport.json").read_text(encoding="utf-8"))

FIG_L = 79.0           # зріст фігури, дюйми
FIG_W = 47.7           # розмах рук — з креслення Володимира
FIG_D = 13.0           # глибина з обшивкою — підтверджена Володимиром 16.08
TUBE = 60.2            # труба в плечах; вона ЗНІМНА/ріжеться, тому окремим варіантом
FOAM = 2.0             # поролон з кожного боку
PLY = 0.75             # фанера стінки

# Кузови. У пікапа ДВІ ширини, і плутати їх не можна: між колісними арками ~50″,
# а поверх арок ~64″. Ящик, ширший за 50″, не «не влазить» — він лягає ЗВЕРХУ на
# арки, і тоді потрібні бруски-підкладки, щоб він не спирався на пластик.
# (name, довжина, між арками, поверх арок, висота борта, примітка)
BEDS = [
    ("Пікап, короткий кузов 5.5 фута", 66.0, 50.0, 64.0, 21.0, "між арками 50″, поверх 64″"),
    ("Пікап, стандарт 6.5 фута", 78.0, 50.0, 64.0, 21.0, "між арками 50″, поверх 64″"),
    ("Пікап, довгий кузов 8 футів", 96.0, 50.0, 64.0, 21.0, "між арками 50″, поверх 64″"),
    # Конкретна машина, яку Іван знайшов на Turo 17.08: Nissan Frontier 2022 Crew Cab.
    # Числа заводські: підлога 59.5″, між арками 44.5″, найширше 61.4″, глибина 19.4″.
    ("Nissan Frontier 2022 Crew Cab (Turo, Hayward)", 59.5, 44.5, 61.4, 19.4,
     "коротка платформа 5 футів — у Crew Cab вона завжди коротка"),
    ("Причіп 5×8 (U-Haul)", 96.0, 60.0, 60.0, 999.0, "борти 12″, відкритий"),
    ("Причіп 6×12", 144.0, 72.0, 72.0, 999.0, "з запасом на подіум"),
]
TAILGATE = 20.0        # відкинутий задній борт додає довжини

S = 3.0
INK, DIM, GREY = "#1b1b1b", "#555", "#a0a0a0"
RED, BLUE, GREEN, ORANGE = "#d81f1f", "#1f4fd8", "#0b8a3e", "#c2660a"


def crate(with_tube: bool):
    """Габарит ящика зовні: фігура + поролон з двох боків + дві стінки фанери."""
    w = (TUBE if with_tube else FIG_W)
    add = 2 * FOAM + 2 * PLY
    return round(FIG_L + add, 1), round(w + add, 1), round(FIG_D + add, 1)


def fits(bed, box, tailgate=False):
    """Влазить = довжина і ширина ПОВЕРХ арок. Висота борта не обмежує: ящик
    товщиною 19″ стирчить над бортом на кілька дюймів, це нормально і кріпиться."""
    L, w_top = bed[1], bed[3]
    if tailgate:
        L += TAILGATE
    return box[0] <= L and box[1] <= w_top


def on_arches(bed, box) -> bool:
    """Ящик ширший за просвіт між арками — лягає зверху на них."""
    return box[1] > bed[2]


def px(v):
    return v * S


def t(x, y, s, size=11, fill=INK, anchor="start", weight="400"):
    s = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial,Helvetica,sans-serif" '
            f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


def rect(x, y, w, h, fill="#f4f6fb", stroke=GREY, lw=1.3, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{lw}"{d}/>')


def build() -> str:
    box_no = crate(False)
    box_yes = crate(True)
    W, H = 1460, 980
    o = [t(40, 34, "Ящик з фігурою: пікап Богдана чи причіп", 19, INK, "start", "700"),
         t(40, 56, "Причіп-дім відпав — Богдан дає свій пікап. Питання тепер одне: чи влазить ящик "
                   "у кузов. Усі кузови міряються проти РОЗРАХОВАНОГО ящика, а не навпаки.", 11, DIM),
         t(40, 74, f"Ящик = фігура {FIG_L:.0f}×{FIG_W:.1f}×{FIG_D:.0f}″ + поролон {FOAM:.0f}″ з кожного "
                   f"боку + фанера {PLY} ″ стінки.", 11, DIM)]

    # ── два варіанти ящика ────────────────────────────────────────────────
    y = 110
    o.append(t(40, y, "ДВА ВАРІАНТИ ЯЩИКА", 13, INK, "start", "700"))
    for i, (label, b, note) in enumerate([
            ("Труба в плечах ЗНЯТА або вкорочена", box_no,
             "везеться окремо вздовж ящика — вона просто труба"),
            ("Труба лишається в плечах", box_yes,
             f"ширина зростає на {box_yes[1] - box_no[1]:.0f}″ і вбиває половину варіантів")]):
        yy = y + 24 + i * 46
        o.append(t(56, yy, f"· {label}", 11.5, INK, "start", "600"))
        o.append(t(56, yy + 16, f"{b[0]:.1f}″ × {b[1]:.1f}″ × {b[2]:.1f}″   ({b[0] / 12:.1f} × "
                                f"{b[1] / 12:.1f} × {b[2] / 12:.1f} фута) — {note}", 11, DIM))

    # ── таблиця кузовів ───────────────────────────────────────────────────
    y = 230
    o.append(t(40, y, "ЩО КУДИ ВЛАЗИТЬ", 13, INK, "start", "700"))
    hdr = ["кузов", "довжина", "між/поверх арок", "борт", "ящик без труби", "ящик із трубою"]
    xs = [40, 300, 395, 520, 600, 800]
    for x, hh in zip(xs, hdr):
        o.append(t(x, y + 22, hh, 10.5, DIM, "start", "700"))
    for i, bed in enumerate(BEDS):
        yy = y + 44 + i * 26
        o.append(t(xs[0], yy, bed[0], 11))
        o.append(t(xs[1], yy, f'{bed[1]:.0f}″', 11, DIM))
        o.append(t(xs[2], yy, f'{bed[2]:.0f}/{bed[3]:.0f}″', 11, DIM))
        o.append(t(xs[3], yy, "—" if bed[4] > 900 else f'{bed[4]:.0f}″', 11, DIM))
        for j, box in enumerate((box_no, box_yes)):
            ok = fits(bed, box)
            ok_tg = fits(bed, box, tailgate=True)
            if ok:
                txt, col = "так", GREEN
            elif ok_tg:
                txt, col = "тільки з відкинутим бортом", ORANGE
            else:
                short = []
                if box[0] > bed[1] + TAILGATE:
                    short.append(f"довжина +{box[0] - bed[1]:.0f}″")
                if box[1] > bed[3]:
                    short.append(f"ширина +{box[1] - bed[3]:.0f}″")
                txt, col = "ні — " + ", ".join(short), RED
            o.append(t(xs[4 + j], yy, txt, 10.5, col, "start", "600"))

    # ── малюнок: ящик у кузові 6.5 фута ──────────────────────────────────
    oy = 420
    o.append(t(40, oy, "ЯК ЦЕ ВИГЛЯДАЄ: стандартний кузов 6.5 фута, вид згори", 13, INK, "start", "700"))
    bx, by = 60, oy + 24
    bedL, bedW = 78.0, 60.0
    o.append(rect(bx, by, px(bedL), px(bedW), "#ffffff", INK, 2))
    o.append(t(bx + px(bedL) / 2, by - 6, f'платформа {bedL:.0f}″', 10, DIM, "middle"))
    # арки
    o.append(rect(bx + px(20), by, px(28), px(5), "#eceff4", GREY, 1))
    o.append(rect(bx + px(20), by + px(bedW - 5), px(28), px(5), "#eceff4", GREY, 1))
    o.append(t(bx + px(34), by + px(2.5) + 4, "арка", 8.5, GREY, "middle"))
    # відкинутий борт
    o.append(rect(bx + px(bedL), by, px(TAILGATE), px(bedW), "#f7f2ea", ORANGE, 1.4, "6 4"))
    o.append(t(bx + px(bedL) + px(TAILGATE / 2), by + px(bedW) / 2 + 4, "борт", 9.5, ORANGE, "middle"))
    # ящик
    o.append(rect(bx + 2, by + (px(bedW) - px(box_no[1])) / 2, px(box_no[0]), px(box_no[1]),
                  "#ffe9c9", ORANGE, 1.8))
    o.append(t(bx + px(box_no[0]) / 2, by + px(bedW) / 2 + 4,
               f'ЯЩИК {box_no[0]:.0f}″ × {box_no[1]:.0f}″', 11, ORANGE, "middle", "700"))
    o.append(t(bx, by + px(bedW) + 22,
               f'Ящик довший за платформу на {box_no[0] - bedL:.0f}″ — їде з відкинутим бортом, '
               f'спертий на нього. Це законно, але кінець треба позначити червоним прапорцем.',
               11, DIM))
    o.append(t(bx, by + px(bedW) + 40,
               f'Ширина {box_no[1]:.0f}″ більша за відстань між арками (50″) — ящик лягає ЗВЕРХУ на арки, '
               f'а не між ними. Значить, потрібні бруски-підкладки, щоб він не спирався на пластик арки.',
               11, DIM))

    # ── висновки ─────────────────────────────────────────────────────────
    y2 = 760
    o.append(t(40, y2, "ЩО З ЦЬОГО ВИПЛИВАЄ", 13, INK, "start", "700"))
    lines = [
        (f"Труба в плечах вирішує все. Без неї ящик {box_no[1]:.0f}″ завширшки і влазить у будь-який "
         f"пікап; з нею {box_yes[1]:.0f}″ — ширше за причіп 5×8.", ORANGE),
        ("У пікапі Богдана ящик поїде з ВІДКИНУТИМ бортом у будь-якому разі, крім довгого кузова "
         "8 футів. Це нормально для 300 миль по трасі, але вантаж треба стягнути так, щоб він не "
         "рухався взагалі: ящик спирається на борт, а не тримається ним.", INK),
        ("Причіп 5×8 бере ящик цілком і всередину, без звисання — але тільки якщо труба знята.", GREEN),
        ("Подіум у пікап РАЗОМ із ящиком не влізе. Або два рейси, або причіп 6×12 на все одразу.", RED),
        ("Повернення тепер у Ріно, а не в SF — це міняє і пробіг, і те, куди Богдан жене машину назад. "
         "Порахувати треба обидва плеча, не тільки дорогу туди.", INK),
    ]
    for i, (ln, c) in enumerate(lines):
        o.append(t(40, y2 + 24 + i * 20, "· " + ln, 11, c, "start", "600" if c != INK else "400"))

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
            f'<rect width="{W}" height="{H}" fill="#ffffff"/>\n' + "\n".join(o) + "\n</svg>\n")


def demo() -> int:
    a, b = crate(False), crate(True)
    assert a[0] == 84.5 and abs(a[1] - 53.2) < 0.05, a
    assert b[1] > a[1], "з трубою ящик мусить бути ширшим"
    assert not fits(BEDS[0], a), "у короткий кузов 5.5 фута ящик не має влазити без борта"
    assert fits(BEDS[2], a), "у довгий кузов 8 футів ящик мусить влазити"
    assert fits(BEDS[1], a, tailgate=True), "у 6.5 фута з відкинутим бортом — мусить"
    assert not fits(BEDS[3], b), "з трубою ящик ширший за причіп 5×8"
    assert on_arches(BEDS[1], a), "53″ ящик мусить лягати ЗВЕРХУ на арки"
    s = build()
    assert s.startswith("<svg") and s.count("<text") > 30
    print(f"demo ok — ящик без труби {a}, з трубою {b}")
    return 0


if __name__ == "__main__":
    import sys
    if "--demo" in sys.argv:
        sys.exit(demo())
    out = HERE / "crate_fit.svg"
    out.write_text(build(), encoding="utf-8")
    print(f"готово: {out}")
