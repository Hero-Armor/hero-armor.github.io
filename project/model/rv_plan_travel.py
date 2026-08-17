#!/usr/bin/env python3
"""Причіп у ПОХІДНОМУ положенні — слайд зсунутий, і що з цього лишається всередині.

Питання Івана 17.08: «а є такий самий план, де кімнати не розсунуті?». Відповідь:
у заводських даних такого плану НЕМА — перевірено, Keystone публікує тільки план із
висунутим слайдом і кількість слайдів, а глибину висування не публікує ніде. Тому цю
схему малюємо самі, і вона свідомо ПАРАМЕТРИЧНА: слайд може ходити на 24, 30 або 36
дюймів, і всі три випадки показані поруч.

Чому це взагалі важливо: везти фігуру всередині причепа можна тільки в похідному
положенні, а саме в ньому дінет і диван заїжджають усередину і з'їдають прохід.
План із висунутим слайдом на це питання не відповідає взагалі.

Головний висновок рахується, а не малюється: фігура кладеться НА БІК, тобто їй
потрібна смуга 13″ завширшки, а не 47.7″. Тому вона проходить у всіх трьох випадках.

  python3 project/model/rv_plan_travel.py  →  rv_plan_travel.svg
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent

EXT_L, EXT_W = 367.0, 96.0        # заводські дані
WALL = 3.0
INT_W = EXT_W - 2 * WALL          # 90″ між стінами
GALLEY = 30.0                     # глибина ряду «острівець — холодильник — комора»
SLIDES = (24.0, 30.0, 36.0)       # глибина слайда: невідома, три правдоподібні
FIG = (79.0, 47.7, 13.0)          # фігура: довжина, ширина, товщина
BUNK = (51.0, 74.0)
WALK = 12.0                       # скільки лишити людині, щоб пройти повз фігуру

S = 2.35
INK, DIM, GREY = "#1b1b1b", "#555", "#a0a0a0"
RED, BLUE, GREEN, ORANGE = "#d81f1f", "#1f4fd8", "#0b8a3e", "#c2660a"


def px(v):
    return v * S


def aisle_for(slide_in: float) -> float:
    """Скільки лишається між рядом кухні і зсунутим усередину слайдом."""
    return INT_W - GALLEY - slide_in


def verdict(slide_in: float) -> tuple[bool, str]:
    a = aisle_for(slide_in)
    if a >= FIG[2] + WALK:
        return True, f"лишається {a:.0f}″ — фігура на боці ({FIG[2]:.0f}″) і ще {a - FIG[2]:.0f}″ на прохід"
    if a >= FIG[2]:
        return True, f"лишається {a:.0f}″ — фігура влізе, але повз неї вже не пройти"
    return False, f"лишається {a:.0f}″ — фігура на боці не проходить"


def t(x, y, s, size=11, fill=INK, anchor="start", weight="400"):
    s = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial,Helvetica,sans-serif" '
            f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


def box(x, y, w, h, label="", fill="#f2f2f2", stroke=GREY, sub="", dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    o = [f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" '
         f'stroke="{stroke}" stroke-width="1.2"{d}/>']
    if label:
        o.append(t(x + w / 2, y + h / 2 + (0 if not sub else -4), label, 10, DIM, "middle"))
    if sub:
        o.append(t(x + w / 2, y + h / 2 + 12, sub, 9.5, GREY, "middle"))
    return "\n".join(o)


def dim_v(x, y1, y2, label, color=RED):
    return (f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" stroke="{color}" '
            f'stroke-width="1.4" marker-start="url(#a)" marker-end="url(#a)"/>\n'
            + t(x + 7, (y1 + y2) / 2 + 4, label, 10, color, "start", "700"))


def strip(oy: float, slide_in: float, ox: float = 70) -> str:
    """Один причіп у похідному положенні для заданої глибини слайда."""
    ok, txt = verdict(slide_in)
    o = [t(ox, oy - 12, f"слайд заходить на {slide_in:.0f}″", 12.5, INK, "start", "700")]
    o.append(f'<rect x="{ox:.1f}" y="{oy:.1f}" width="{px(EXT_L):.1f}" height="{px(EXT_W):.1f}" '
             f'rx="{px(8):.1f}" fill="#ffffff" stroke="{INK}" stroke-width="2"/>')
    iy = oy + px(WALL)
    R = ox + px(EXT_L)

    def fr(inches):
        return R - px(inches)

    # спальня і ряд кухні — вони не рухаються
    o.append(box(fr(84), iy, px(84), px(INT_W), "спальня", "#eef3ff", "#9db4e8"))
    gy = iy + px(INT_W - GALLEY)          # ряд кухні йде вздовж НИЖНЬОЇ стіни
    o.append(box(fr(150), gy, px(38), px(GALLEY), "острівець, ТБ", "#f2f7f0", "#a9c6a1"))
    o.append(box(fr(196), gy, px(46), px(GALLEY), "холодильник", "#f2f7f0", "#a9c6a1"))
    o.append(box(fr(238), gy, px(42), px(GALLEY), "комора", "#f7f2ea", "#cbbba2"))
    o.append(box(ox + px(3), iy, px(46), px(44), "санвузол", "#f7f2ea", "#cbbba2"))
    o.append(box(ox + px(3), iy + px(44), px(78), px(INT_W - 44), "ліжка",
                 "#fff4ee", "#e0b49a", f'{BUNK[0]:.0f}×{BUNK[1]:.0f}″'))

    # слайд — ЗАЇХАВ усередину, тому він тепер у салоні, а не за габаритом
    o.append(box(fr(240), iy, px(130), px(slide_in), "U-дінет і диван — заїхали всередину",
                 "#e8eaff", BLUE, "", "6 4"))

    # прохід, що лишився
    a = aisle_for(slide_in)
    ay = iy + px(slide_in)
    o.append(f'<rect x="{fr(240):.1f}" y="{ay:.1f}" width="{px(130):.1f}" height="{px(a):.1f}" '
             f'fill="{GREEN if ok else RED}" fill-opacity="0.10" stroke="{GREEN if ok else RED}" '
             f'stroke-width="1" stroke-dasharray="5 4"/>')
    # фігура на боці
    o.append(box(fr(230), ay + 2, px(FIG[0]), px(FIG[2]), "", "#ffe9c9", ORANGE))
    o.append(t(fr(230) + px(FIG[0]) / 2, ay + px(FIG[2]) / 2 + 5,
               f'фігура НА БОЦІ {FIG[0]:.0f}″ × {FIG[2]:.0f}″', 9.5, ORANGE, "middle", "700"))
    o.append(dim_v(fr(246), ay, ay + px(a), f'{a:.0f}″', GREEN if ok else RED))
    tight = aisle_for(slide_in) < FIG[2] + WALK
    col = RED if not ok else (ORANGE if tight else GREEN)
    o.append(t(ox + px(EXT_L) + 14, oy + px(EXT_W) / 2, ("ТАК — " if ok else "НІ — ") + txt,
               11, col, "start", "700"))
    return "\n".join(o)


def build() -> str:
    W = 1500
    rows = len(SLIDES)
    H = 150 + rows * (px(EXT_W) + 70) + 150
    o = [t(40, 34, "Причіп у похідному положенні — слайд зсунутий", 19, INK, "start", "700"),
         t(40, 56, "Заводського плану зі зсунутим слайдом НЕ ІСНУЄ: Keystone публікує тільки "
                   "розсунутий і кількість слайдів, а глибину висування не дає ніде. Тому три "
                   "варіанти поруч — 24, 30 і 36 дюймів.", 11, DIM),
         t(40, 74, "Орієнтація та сама, що на заводському кресленні: ніс праворуч. Синім — дінет "
                   "і диван, які в похідному положенні заїжджають усередину і забирають прохід.",
           11, DIM)]
    for i, s in enumerate(SLIDES):
        o.append(strip(150 + i * (px(EXT_W) + 70), s))

    y = 150 + rows * (px(EXT_W) + 70) + 20
    o.append(t(40, y, "ЩО З ЦЬОГО ВИПЛИВАЄ", 13, INK, "start", "700"))
    lines = [
        (f"Фігуру везуть НА БОЦІ. Тоді їй треба смуга {FIG[2]:.0f}″ завширшки, а не {FIG[1]:.1f}″ — "
         f"і вона проходить у всіх трьох випадках.", GREEN),
        (f"Місця по довжині вистачає з запасом: вільна зона між спальнею і ліжками близько 154″ "
         f"проти {FIG[0]:.0f}″ фігури.", INK),
        (f"На нижнє ліжко фігура НЕ ляже: полиця {BUNK[1]:.0f}″, фігура {FIG[0]:.0f}″ — не вистачає "
         f"пʼяти дюймів. Тільки підлога.", RED),
        ("Слайд не можна везти висунутим — ні на трасі, ні на плайї. Тому всі розрахунки "
         "перевезення робимо тільки по цій схемі, а не по заводській.", INK),
        ("ОДИН ЗАМІР ЗАКРИВАЄ ПИТАННЯ: ширина проходу між кухонним рядом і зсунутим дінетом. "
         "Рулетка в Богдана, тридцять секунд — і три варіанти стають одним.", ORANGE),
    ]
    for i, (ln, c) in enumerate(lines):
        o.append(t(40, y + 24 + i * 20, "· " + ln, 11, c, "start", "600" if c != INK else "400"))

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H:.0f}" '
            f'viewBox="0 0 {W} {H:.0f}">\n'
            f'<defs><marker id="a" markerWidth="9" markerHeight="9" refX="4.5" refY="4.5" '
            f'orient="auto"><path d="M1,1 L8,4.5 L1,8" fill="none" stroke="currentColor" '
            f'stroke-width="1.2"/></marker></defs>\n'
            f'<rect width="{W}" height="{H:.0f}" fill="#ffffff"/>\n' + "\n".join(o) + "\n</svg>\n")


def demo() -> int:
    assert aisle_for(24) == 36 and aisle_for(36) == 24, aisle_for(24)
    ok24, _ = verdict(24)
    ok36, _ = verdict(36)
    assert ok24 and ok36, "фігура на боці мусить проходити в усіх трьох варіантах"
    assert not verdict(60)[0], "при абсурдній глибині слайда вердикт мусить стати негативним"
    assert FIG[0] > BUNK[1], "перевірка: фігура довша за нижнє ліжко"
    s = build()
    assert s.startswith("<svg") and s.count("<text") > 40
    print(f"demo ok — прохід {aisle_for(24):.0f}/{aisle_for(30):.0f}/{aisle_for(36):.0f}″, "
          f"фігура на боці {FIG[2]:.0f}″ проходить скрізь")
    return 0


if __name__ == "__main__":
    import sys
    if "--demo" in sys.argv:
        sys.exit(demo())
    out = HERE / "rv_plan_travel.svg"
    out.write_text(build(), encoding="utf-8")
    print(f"готово: {out}")
