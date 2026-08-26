#!/usr/bin/env python3
"""План різу бруса для каркаса перевезення — картинка, з якою можна стояти біля пили.

Іван 25.08.2026: «намалюй план різу — як мені різати, де під яким кутом, яку палку
і на якій довжині».

Джерело чисел — аркуш 06.24 ревізії 3.3 (V3-3, Володимир, 24.08.2026), той самий,
що лежить на його Драйві. Кути — з аркуша 06.23 тієї ж ревізії.

Кожен брус намальований смугою в масштабі. Видно, де ставити олівець, скільки
лишається обрізка і які кінці ріжуться під кутом, а які рівно. Довжини підписані
в міліметрах І в дюймах — Іван будує в дюймах, а думає в метрах.

    crate_cutplan.py            намалювати
    crate_cutplan.py --selftest перевірити, що розкрій влазить у бруси
"""
import sys
from fractions import Fraction
from pathlib import Path

BOARD = 2438            # 8 футів
KERF = 3                # ширина пропилу, мм
OUT = Path("/root/hero-armor/private/quotes")

# (мітка бруса, переріз, [(деталь, довжина, як різати), ...])
PLAN = [
    ("A", "2x4", [("No.1", 2240, "straight")]),
    ("B", "2x4", [("No.1", 2240, "straight")]),
    ("C", "2x4", [("No.2", 844, "straight"), ("No.2", 844, "straight")]),
    ("1", "2x3", [("No.3", 1200, "straight"), ("No.3", 1200, "straight")]),
    ("2", "2x3", [("No.4", 1066, "straight"), ("No.4", 1066, "straight")]),
    ("3", "2x3", [("No.5", 1750, "angle30")]),
    ("4", "2x3", [("No.5", 1750, "angle30")]),
    ("5", "2x3", [("No.6", 1100, "angle")]),
    ("6", "2x3", [("No.6", 990, "straight"), ("No.6", 990, "straight")]),
    ("7", "2x3", [("No.7", 960, "angle"), ("No.7", 960, "angle")]),
    ("8", "2x3", [("No.8", 1354, "straight"), ("No.8", 713, "angle37")]),
    ("9", "2x3", [("No.8", 1354, "straight"), ("No.8", 713, "angle37")]),
]
HOW = {
    "straight": ("straight 90°", "#2e7d32"),
    "angle":    ("ANGLE — fit on site", "#e65100"),
    "angle30":  ("top end at 30°", "#e65100"),
    "angle37":  ("both ends at 37°", "#e65100"),
}


def inch(mm: int) -> str:
    i = mm / 25.4
    w = int(i)
    f = Fraction(round((i - w) * 16), 16)
    if f == 1:
        w, f = w + 1, Fraction(0)
    return f'{w}"' + (f" {f.numerator}/{f.denominator}" if f else "")


def svg() -> str:
    LEFT, TOP, ROW, BARH = 150, 96, 74, 40
    SC = 0.52                      # мм креслення -> пікселі
    W = int(LEFT + BOARD * SC + 300)
    H = TOP + ROW * len(PLAN) + 130
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family="DejaVu Sans, Arial">',
         f'<rect width="{W}" height="{H}" fill="white"/>',
         f'<text x="{LEFT}" y="40" font-size="26" font-weight="bold">'
         f'CUT PLAN — transport crate · sheet 06.24 rev 3.3</text>',
         f'<text x="{LEFT}" y="66" font-size="15" fill="#555">'
         f'Every board is 8 ft = 2438 mm = 96". Kerf {KERF} mm allowed per cut. '
         f'Green = straight 90°, orange = angled, cut long and fit on site.</text>']
    y = TOP
    for tag, sec, cuts in PLAN:
        o.append(f'<text x="20" y="{y+26}" font-size="17" font-weight="bold">'
                 f'{sec} · board {tag}</text>')
        o.append(f'<rect x="{LEFT}" y="{y}" width="{BOARD*SC:.0f}" height="{BARH}" '
                 f'fill="#f3ede2" stroke="#9c8f7a" stroke-width="2"/>')
        x = LEFT
        used = 0
        for part, L, how in cuts:
            label, col = HOW[how]
            w = L * SC
            o.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{BARH}" '
                     f'fill="{col}" fill-opacity="0.16" stroke="{col}" stroke-width="3"/>')
            o.append(f'<text x="{x+w/2:.0f}" y="{y+17}" font-size="15" fill="{col}" '
                     f'text-anchor="middle" font-weight="bold">{part}</text>')
            o.append(f'<text x="{x+w/2:.0f}" y="{y+34}" font-size="13" fill="#111" '
                     f'text-anchor="middle">{L} mm · {inch(L)}</text>')
            used += L + KERF
            x += w
            # мітка різу
            o.append(f'<line x1="{x:.1f}" y1="{y-8}" x2="{x:.1f}" y2="{y+BARH+8}" '
                     f'stroke="#c00" stroke-width="2" stroke-dasharray="5,4"/>')
        rest = BOARD - used + KERF
        o.append(f'<text x="{LEFT+BOARD*SC+12:.0f}" y="{y+18}" font-size="13" fill="#777">'
                 f'offcut {max(rest,0)} mm</text>')
        o.append(f'<text x="{LEFT+BOARD*SC+12:.0f}" y="{y+34}" font-size="12" fill="{HOW[cuts[0][2]][1]}">'
                 f'{HOW[cuts[0][2]][0]}</text>')
        y += ROW
    o.append(f'<text x="{LEFT}" y="{y+34}" font-size="15" font-weight="bold">ANGLES</text>')
    for i, t in enumerate([
        "30° — solar panel tilt: the TOP end of the two No.5 beams",
        "10.68° — vertical post lean (see side view on sheet 06.23)",
        "37° — the two No.8 diagonals; they meet in a V with a 1134 mm base",
        "No.6-1100 and No.7 — angle is NOT printed on the drawing: cut long, fit on site",
    ]):
        o.append(f'<text x="{LEFT}" y="{y+56+i*20}" font-size="14">· {t}</text>')
    o.append(f'<text x="{LEFT}" y="{y+150}" font-size="14" font-weight="bold">'
             f'Mark every piece with its number No.1 … No.8 before you cut the next one.</text>')
    o.append('</svg>')
    return "\n".join(o)


def selftest() -> int:
    """Головне — щоб розкрій фізично влазив у восьмифутовий брус."""
    n24 = sum(1 for _, s, _ in PLAN if s == "2x4")
    n23 = sum(1 for _, s, _ in PLAN if s == "2x3")
    assert n24 == 3 and n23 == 9, f"брусів {n24}/{n23}, а має бути 3 і 9"
    for tag, sec, cuts in PLAN:
        need = sum(L for _, L, _ in cuts) + KERF * len(cuts)
        assert need <= BOARD, f"брус {tag}: треба {need} мм, а є {BOARD}"
    parts = {}
    for _, _, cuts in PLAN:
        for p, L, _h in cuts:
            parts.setdefault((p, L), 0)
            parts[(p, L)] += 1
    assert parts[("No.1", 2240)] == 2 and parts[("No.2", 844)] == 2
    assert parts[("No.5", 1750)] == 2 and parts[("No.8", 713)] == 2
    assert inch(2240) == '88" 3/16', inch(2240)
    print(f"selftest ok — 3 бруси 2x4 і 9 брусів 2x3, увесь розкрій влазить")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / "crate_cutplan_EN.svg"
    f.write_text(svg())
    print("зроблено:", f)
