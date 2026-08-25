#!/usr/bin/env python3
"""Розкрій ОДНОГО листа алюмінію: одна секція підлоги + максимум торцевих смуг.

Іван 25.08.2026: «зроби розкрій — один цей трикутник, і все інше на торці, і так,
щоб максимум влізло. Дай візуалізацію».

⚠ ПЕРША ВЕРСІЯ БУЛА НЕПРАВИЛЬНА, і Іван це побачив одразу: я намалював секцію
приблизною фігурою «з голови», хоча справжній контур лежав картинкою в його
переписці з Лізою. Тепер вершини взяті з того аркуша (06.13 рев.3.2) і збігаються
з підписаними на ньому розмірами: ліва сторона 853, низ 259+107+853, два зрізи по
281, права сторона 898.

ЩО ВИЯВИЛОСЬ ВАЖЛИВЕ, коли контур став справжнім: за кресленням на одному листі
лежать ДВІ секції, а не одна — вони вкладені «валетом», і між ними йде один різ.
Саме тому в комплекті пʼять листів на вісім секцій, а не вісім.

Тому цей розкрій — не той, що в кресленні. Це варіант Івана: одна секція, а вся
решта листа йде на торцеві смуги.

    alu_nesting.py            намалювати
    alu_nesting.py --selftest перевірити геометрію і вкладання
"""
import sys
from pathlib import Path

SHEET = 1219          # 48″
STRIP_W = 160         # висота торцевої смуги, замір Лізи 24.08
MM = 25.4
OUT = Path(__file__).resolve().parents[2] / "site" / "assets"

# Контур ОДНІЄЇ секції — нижня з двох на аркуші 06.13, посунута в кут листа.
# Вершини аркуша: A(0,0) F(866,359) E(1219,1219) D(366,1219) C(259,962) B(0,853).
# Беремо верхню секцію A-F-C-B: у неї пряма ліва сторона 853 і пряма верхня межа,
# тому вона лягає в кут листа без втрат.
SEG = [(0, 0), (866, 359), (259, 962), (0, 853)]


def inside(poly, x, y) -> bool:
    """Точка в багатокутнику — променевий тест."""
    n, r = len(poly), False
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            r = not r
    return r


def free(poly, x, y, w, h, step=20) -> bool:
    """Прямокутник цілком поза секцією і в межах листа.

    Перевіряємо сіткою по контуру і всередині: секція опукла з одного боку, тому
    достатньо густої сітки. Крок 20 мм — дрібніше не має сенсу, різ і так ширший."""
    if x < 0 or y < 0 or x + w > SHEET or y + h > SHEET:
        return False
    ys = list(range(int(y), int(y + h) + 1, step)) + [int(y + h)]
    xs = list(range(int(x), int(x + w) + 1, step)) + [int(x + w)]
    return not any(inside(poly, px, py) for py in ys for px in xs)


def pack(strip_len: int, step: int = 20) -> list:
    """Жадібно кладемо смуги: спершу вертикально справа, потім горизонтально знизу."""
    placed = []

    def clash(x, y, w, h):
        return any(not (x + w <= px or px + pw <= x or y + h <= py or py + ph <= y)
                   for px, py, pw, ph in placed)

    for w, h in ((STRIP_W, strip_len), (strip_len, STRIP_W)):
        y = 0
        while y + h <= SHEET:
            x = 0
            while x + w <= SHEET:
                if free(SEG, x, y, w, h, step) and not clash(x, y, w, h):
                    placed.append((x, y, w, h))
                    x += w
                else:
                    x += step
            y += step
    return placed


def svg(strip_len: int, placed: list) -> str:
    s, pad = 0.44, 95
    W = int(SHEET * s) + pad * 2
    H = int(SHEET * s) + pad * 2 + 74
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family="DejaVu Sans, Arial">',
         f'<rect width="{W}" height="{H}" fill="white"/>',
         f'<g transform="translate({pad},{pad}) scale({s})">',
         f'<rect x="0" y="0" width="{SHEET}" height="{SHEET}" fill="#fbfbfb" '
         f'stroke="#333" stroke-width="4"/>']
    pts = " ".join(f"{x},{y}" for x, y in SEG)
    o.append(f'<polygon points="{pts}" fill="#cfe3f7" stroke="#1560a8" stroke-width="7"/>')
    o.append('<text x="300" y="430" font-size="42" fill="#1560a8">СЕКЦІЯ</text>')
    o.append('<text x="300" y="480" font-size="27" fill="#5a86ad">за аркушем 06.13</text>')
    # підписи сторін секції — ті самі числа, що на кресленні
    o.append('<text x="-52" y="430" font-size="30" transform="rotate(-90,-52,430)">853</text>')
    o.append('<text x="430" y="150" font-size="30" fill="#1560a8">898</text>')
    o.append('<text x="470" y="700" font-size="30" fill="#1560a8">281</text>')
    for x, y, w, h in placed:
        o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#d8f0d8" '
                 f'stroke="#2e7d32" stroke-width="5"/>')
        cx, cy = x + w / 2, y + h / 2
        rot = f' transform="rotate(-90,{cx},{cy})"' if h > w else ""
        o.append(f'<text x="{cx}" y="{cy+10}" font-size="28" fill="#2e7d32" '
                 f'text-anchor="middle"{rot}>{STRIP_W}×{strip_len}</text>')
    o.append(f'<text x="{SHEET/2}" y="-30" font-size="34" text-anchor="middle">1219 мм (48″)</text>')
    o.append(f'<text x="-30" y="{SHEET/2}" font-size="34" text-anchor="middle" '
             f'transform="rotate(-90,-30,{SHEET/2})">1219 мм (48″)</text>')
    o.append('</g>')
    o.append(f'<text x="{W/2}" y="{H-36}" font-size="18" text-anchor="middle" font-weight="bold">'
             f'Розкрій листа 48×48″ · 1 секція + торці по {strip_len} мм</text>')
    o.append(f'<text x="{W/2}" y="{H-14}" font-size="15" text-anchor="middle" fill="#555">'
             f'виходить {len(placed)} торцевих смуг {STRIP_W}×{strip_len} мм</text>')
    o.append('</svg>')
    return "\n".join(o)


def selftest() -> int:
    """Контур мусить сходитись із числами, підписаними на аркуші."""
    d = lambda a, b: round(((a[0]-b[0])**2 + (a[1]-b[1])**2) ** 0.5)
    A, F, C, B = SEG
    assert d(B, A) == 853, f"ліва сторона {d(B,A)}, а на кресленні 853"
    assert abs(d(A, F) - 933) < 40, d(A, F)
    assert abs(d(C, B) - 281) < 15, f"зріз {d(C,B)}, а на кресленні 281"
    assert inside(SEG, 200, 200) and not inside(SEG, 1100, 200), "тест точки збився"
    assert not inside(SEG, 1100, 1100)
    for L in (853, 900):
        p = pack(L)
        assert p, f"жодної смуги при довжині {L}"
        for x, y, w, h in p:
            assert free(SEG, x, y, w, h), "смуга налізла на секцію"
    print("selftest ok — контур збігається з кресленням, смуги секцію не перетинають")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    OUT.mkdir(parents=True, exist_ok=True)
    for L in (853, 900):
        p = pack(L)
        (OUT / f"alu_nesting_{L}.svg").write_text(svg(L, p))
        print(f"торець {L} мм → {len(p)} смуг з листа")
    return 0


if __name__ == "__main__":
    sys.exit(main())
