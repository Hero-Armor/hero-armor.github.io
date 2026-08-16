#!/usr/bin/env python3
"""Причіп Богдана згори — розміри поверх заводського плану.

Причіп упізнано з фото в чаті «Rv 2026» (20.07.2026): Keystone Passport SL 268BH.
Сам заводський план лежить поруч картинкою (`site/assets/rv_268bh_floorplan.jpg`) —
цей файл малює НЕ його заміну, а розмірну схему в тій самій орієнтації: ніс і зчіп
праворуч, обидві двері внизу, як на заводському кресленні. Так дві картинки читаються
як одна пара і не суперечать одна одній.

Планування (з заводського плану, звірено зі словами Івана 16.08):
  спереду праворуч — спальня, ліжко queen 60×80″;
  заходиш у ГОЛОВНІ двері: праворуч від тебе спальня, ліворуч кухонний острівець
  із телевізором, далі холодильник і шафа-комора;
  зверху в слайд-ауті — U-подібний дінет і диван;
  ззаду ліворуч — двоярусні ліжка 51×74″, санвузол і душ;
  ДРУГІ двері — задні, ведуть просто в зону ліжок.

Що позначено розмірами: усе, що знайшлось у заводських даних, плюс окремо жовтим —
те, чого в жодних відкритих даних нема і що треба зняти рулеткою в Богдана.

  python3 project/model/rv_plan.py  →  rv_plan.svg
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent

EXT_L, EXT_W = 367.0, 96.0        # 30 ft 7 in × 8 ft — заводські дані
WALL = 3.0
INT_W = EXT_W - 2 * WALL
DOOR_MAIN = (26.0, 74.0)          # keystonerv.com, Passport SL
QUEEN = (60.0, 80.0)              # підписано на заводському плані
BUNK = (51.0, 74.0)               # підписано на заводському плані
FIG = (79.0, 47.7, 13.0)   # глибина підтверджена Володимиром 16.08
TUBE = 60.2

S = 2.6
INK, DIM, GREY = "#1b1b1b", "#555", "#a0a0a0"
RED, BLUE, GREEN, ORANGE = "#d81f1f", "#1f4fd8", "#0b8a3e", "#c2660a"


def px(v):
    return v * S


def t(x, y, s, size=11, fill=INK, anchor="start", weight="400"):
    s = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial,Helvetica,sans-serif" '
            f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


def box(x, y, w, h, label="", fill="#f2f2f2", stroke=GREY, sub=""):
    o = [f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" '
         f'stroke="{stroke}" stroke-width="1.2"/>']
    if label:
        o.append(t(x + w / 2, y + h / 2 + (0 if not sub else -4), label, 10, DIM, "middle"))
    if sub:
        o.append(t(x + w / 2, y + h / 2 + 12, sub, 9.5, GREY, "middle"))
    return "\n".join(o)


def dim_h(x1, x2, y, label, color=RED, below=False):
    return (f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" stroke="{color}" '
            f'stroke-width="1.4" marker-start="url(#a{color[1:]})" marker-end="url(#a{color[1:]})"/>\n'
            + t((x1 + x2) / 2, y + (14 if below else -6), label, 10.5, color, "middle", "700"))


def dim_v(x, y1, y2, label, color=RED):
    return (f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" stroke="{color}" '
            f'stroke-width="1.4" marker-start="url(#a{color[1:]})" marker-end="url(#a{color[1:]})"/>\n'
            + t(x + 7, (y1 + y2) / 2 + 4, label, 10.5, color, "start", "700"))


def build() -> str:
    W, H = 1240, 1060
    ox, oy = 70, 210
    R = ox + px(EXT_L)                      # правий край = НІС причепа
    o = [t(40, 34, "Причіп Богдана — розміри поверх заводського плану", 19, INK, "start", "700"),
         t(40, 56, "Keystone Passport SL 268BH. Орієнтація та сама, що на заводському кресленні вище: "
                   "ніс і зчіп ПРАВОРУЧ, обидві двері знизу.", 11, DIM),
         t(40, 74, "Червоним — розміри із заводських даних. Жовтим — те, чого у відкритих даних нема "
                   "і що треба зняти рулеткою в Богдана.", 11, DIM)]

    o.append(f'<rect x="{ox:.1f}" y="{oy:.1f}" width="{px(EXT_L):.1f}" height="{px(EXT_W):.1f}" '
             f'rx="{px(8):.1f}" fill="#ffffff" stroke="{INK}" stroke-width="2"/>')
    iy = oy + px(WALL)
    # зчіп праворуч
    o.append(f'<path d="M{R:.1f} {oy+px(EXT_W)/2-px(4):.1f} L{R+px(26):.1f} {oy+px(EXT_W)/2:.1f} '
             f'L{R:.1f} {oy+px(EXT_W)/2+px(4):.1f} Z" fill="none" stroke="{INK}" stroke-width="1.6"/>')
    o.append(t(R + px(4), oy - px(6), "зчіп, ніс →", 10, DIM))

    def fromright(inches):
        return R - px(inches)

    # ── СПАЛЬНЯ спереду (праворуч) ───────────────────────────────────────
    bed_w = px(84)
    o.append(box(fromright(84), iy, bed_w, px(INT_W), "спальня: ліжко queen",
                 "#eef3ff", "#9db4e8", f'{QUEEN[0]:.0f}″ × {QUEEN[1]:.0f}″'))
    # ── ГОЛОВНІ ДВЕРІ і те, що обабіч ────────────────────────────────────
    dm_x = fromright(112)                       # двері одразу за спальнею
    o.append(box(fromright(150), iy, px(38), px(30), "острівець, ТБ", "#f2f7f0", "#a9c6a1"))
    o.append(box(fromright(196), iy, px(46), px(30), "холодильник, НВЧ",
                 "#f2f7f0", "#a9c6a1"))
    o.append(box(fromright(238), iy, px(42), px(30), "шафа-комора", "#f7f2ea", "#cbbba2"))
    # слайд-аут згори
    o.append(f'<rect x="{fromright(240):.1f}" y="{oy-px(30):.1f}" width="{px(130):.1f}" '
             f'height="{px(30)+2:.1f}" fill="#f6f6ff" stroke="{BLUE}" stroke-width="1.4" '
             f'stroke-dasharray="6 4"/>')
    o.append(t(fromright(175), oy - px(15) + 4, "слайд-аут: U-дінет і диван", 10, BLUE, "middle"))
    # ── ЗАДНЯ ЧАСТИНА ────────────────────────────────────────────────────
    o.append(box(ox + px(3), iy, px(46), px(44), "душ і санвузол", "#f7f2ea", "#cbbba2"))
    o.append(box(ox + px(3), iy + px(44), px(78), px(INT_W - 44), "двоярусні ліжка",
                 "#fff4ee", "#e0b49a", f'{BUNK[0]:.0f}″ × {BUNK[1]:.0f}″'))
    o.append(box(ox + px(49), iy, px(74), px(44), "зовнішня кухня (ззовні)", "#fafafa", "#dcdcdc"))
    # прохід
    aisle_x1, aisle_x2 = fromright(240), fromright(112) + px(DOOR_MAIN[0])
    o.append(f'<rect x="{aisle_x1:.1f}" y="{iy+px(30):.1f}" width="{aisle_x2-aisle_x1:.1f}" '
             f'height="{px(INT_W-30):.1f}" fill="{GREEN}" fill-opacity="0.09" stroke="{GREEN}" '
             f'stroke-width="1" stroke-dasharray="5 4"/>')
    o.append(t((aisle_x1 + aisle_x2) / 2, iy + px(30) + px(INT_W - 30) / 2 + 4,
               "прохід — заміряти", 10, GREEN, "middle", "700"))

    # ── ДВЕРІ ────────────────────────────────────────────────────────────
    door_y = oy + px(EXT_W) - 2
    o.append(f'<rect x="{dm_x:.1f}" y="{door_y-3:.1f}" width="{px(DOOR_MAIN[0]):.1f}" height="6" '
             f'fill="{RED}"/>')
    o.append(t(dm_x + px(13), door_y + 24, "ГОЛОВНІ двері", 11, RED, "middle", "700"))
    o.append(t(dm_x + px(13), door_y + 38, f'{DOOR_MAIN[0]:.0f}″ × {DOOR_MAIN[1]:.0f}″', 10.5, RED, "middle"))
    o.append(t(dm_x + px(13), door_y + 52, "праворуч спальня, ліворуч острівець", 9.5, DIM, "middle"))
    dr_x = ox + px(96)
    o.append(f'<rect x="{dr_x:.1f}" y="{door_y-3:.1f}" width="{px(26):.1f}" height="6" fill="{ORANGE}"/>')
    o.append(t(dr_x + px(13), door_y + 24, "ЗАДНІ двері — у ліжка", 11, ORANGE, "middle", "700"))
    o.append(t(dr_x + px(13), door_y + 38, "розмір заміряти", 10.5, ORANGE, "middle"))

    # шляхи занесення
    o.append(f'<path d="M{dr_x+px(13):.1f} {door_y+px(14):.1f} L{dr_x+px(13):.1f} {iy+px(60):.1f}" '
             f'stroke="{ORANGE}" stroke-width="2.4" fill="none" stroke-dasharray="9 5"/>')
    o.append(f'<path d="M{dm_x+px(13):.1f} {door_y+px(14):.1f} L{dm_x+px(13):.1f} '
             f'{iy+px(INT_W)-px(6):.1f} L{aisle_x1+px(10):.1f} {iy+px(INT_W)-px(6):.1f}" '
             f'stroke="{RED}" stroke-width="2" fill="none" stroke-dasharray="9 5"/>')

    # ── РОЗМІРИ ──────────────────────────────────────────────────────────
    o.append(dim_h(ox, R, oy - px(38), '30 ft 7 in = 367″ — повна довжина'))
    o.append(dim_v(R + px(40), oy, oy + px(EXT_W), '8 ft = 96″'))
    o.append(dim_h(fromright(84), R, oy + px(EXT_W) + px(26), '84″ — спальня', RED, below=True))
    o.append(dim_h(ox, ox + px(96), oy - px(14), '≈96″ — задня зона з ліжками', ORANGE))

    # ── ФІГУРА І ПЕРЕРІЗ ─────────────────────────────────────────────────
    fy = oy + px(EXT_W) + 150
    o.append(t(40, fy - 26, "Фігура в тому ж масштабі і що саме бачать двері", 14, INK, "start", "700"))
    o.append(f'<rect x="{70:.1f}" y="{fy:.1f}" width="{px(FIG[0]):.1f}" height="{px(FIG[1]):.1f}" '
             f'fill="{BLUE}" fill-opacity="0.12" stroke="{BLUE}" stroke-width="1.6"/>')
    o.append(t(70 + px(FIG[0]) / 2, fy + px(FIG[1]) / 2 + 4,
               f'фігура згори: {FIG[0]:.0f}″ × {FIG[1]:.1f}″', 11, BLUE, "middle", "600"))
    o.append(dim_h(70, 70 + px(FIG[0]), fy + px(FIG[1]) + 22, f'{FIG[0]:.0f}″', BLUE, below=True))

    cx = 70 + px(FIG[0]) + 110
    o.append(t(cx, fy - 8, "переріз у дверях, якщо нести НА БОЦІ:", 11, INK, "start", "700"))
    dw, dh = px(DOOR_MAIN[0]), px(DOOR_MAIN[1])
    o.append(f'<rect x="{cx:.1f}" y="{fy+6:.1f}" width="{dw:.1f}" height="{dh:.1f}" '
             f'fill="none" stroke="{RED}" stroke-width="2"/>')
    o.append(t(cx + dw / 2, fy + dh + 20, "двері 26 × 74″", 10, RED, "middle"))
    o.append(f'<rect x="{cx + (dw-px(FIG[2]))/2:.1f}" y="{fy+6+(dh-px(TUBE))/2:.1f}" '
             f'width="{px(FIG[2]):.1f}" height="{px(TUBE):.1f}" fill="{GREEN}" fill-opacity="0.3" '
             f'stroke="{GREEN}" stroke-width="1.6"/>')
    for i, line in enumerate([
            f'глибина {FIG[2]:.0f}″ проти 26″ — запас {26-FIG[2]:.0f}″',
            f'труба в плечах {TUBE:.1f}″ проти 74″ — запас {74-TUBE:.1f}″',
            f'без труби {FIG[1]:.1f}″ — запас {74-FIG[1]:.1f}″']):
        o.append(t(cx + dw + 16, fy + 24 + i * 20, line, 11, GREEN))
    o.append(t(cx + dw + 16, fy + 100, "Вузьке місце — не двері.", 11, INK, "start", "700"))
    o.append(t(cx + dw + 16, fy + 120, "Задні двері ведуть просто до ліжок — повз кухню нести не треба.",
               11, ORANGE))
    # ── КУДИ КЛАСТИ: поверхні проти довжини фігури ───────────────────────
    sx, sy = cx + dw + 16, fy + 138
    o.append(t(sx, sy, "КУДИ КЛАСТИ — довжина поверхні проти 79″ фігури:", 11, INK, "start", "700"))
    surf = [("ліжко queen 60 × 80″", 80.0, True, "влазить, але веде вузький прохід і ТБ посередині"),
            ("двоярусні ліжка 51 × 74″", 74.0, True, "коротше на 5″ — звисатиме"),
            ("розкладений диван", None, False, "у відкритих даних нема, типово 68-72″ — заміряти"),
            ("дінет, розкладений у ліжко", None, False, "у відкритих даних нема, типово 68-74″ — заміряти")]
    for i, (name, ln, known, note) in enumerate(surf):
        y = sy + 20 + i * 19
        col = GREEN if (known and ln and ln >= 79) else (RED if known else ORANGE)
        mark = "+" if (known and ln and ln >= 79) else ("−" if known else "?")
        o.append(t(sx, y, f'{mark} {name}', 10.5, col, "start", "600"))
        o.append(t(sx + 190, y, note, 10, DIM))
    o.append(t(sx, sy + 20 + len(surf) * 19 + 14,
               "Але внутрішня ширина причепа ≈ 90″ — фігура вільно лягає ПОПЕРЕК,", 11, INK, "start", "700"))
    o.append(t(sx, sy + 20 + len(surf) * 19 + 32,
               "від дивана до протилежної стінки. Тоді довжина поверхні взагалі не важлива.", 11, INK))
    o.append(t(sx, sy + 20 + len(surf) * 19 + 58, "ЩО ЗАМІРЯТИ В БОГДАНА:", 11, ORANGE, "start", "700"))
    for i, line in enumerate(["розмір ЗАДНІХ дверей", "ширину внутрішніх дверей у спальню",
                              "довжину розкладеного дивана і дінета",
                              "висоту порога над землею", "ширину проходу в найвужчому місці"]):
        o.append(t(sx, sy + 20 + len(surf) * 19 + 78 + i * 18, "· " + line, 10.5, DIM))

    mk = lambda c: (f'<marker id="a{c[1:]}" markerWidth="10" markerHeight="10" refX="5" refY="5" '
                    f'orient="auto"><path d="M1,1 L9,5 L1,9" fill="none" stroke="{c}" '
                    f'stroke-width="1.4"/></marker>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
            f'<defs>{mk(RED)}{mk(ORANGE)}{mk(BLUE)}{mk(GREEN)}</defs>\n'
            f'<rect width="{W}" height="{H}" fill="#ffffff"/>\n' + "\n".join(o) + "\n</svg>\n")


if __name__ == "__main__":
    out = HERE / "rv_plan.svg"
    out.write_text(build(), encoding="utf-8")
    print(f"готово: {out}")
