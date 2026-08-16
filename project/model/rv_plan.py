#!/usr/bin/env python3
"""Причіп Богдана згори: планування, двоє дверей і куди заносити фігуру.

Причіп упізнано з фото в чаті «Rv 2026» (20.07.2026) — Keystone Passport SL. За
баками 43/30/30 гал, маркізою 16 ft і рядком Івана в таблиці кемпу («travel trailer
30 ft, 8 ft завширшки») це 268BH: 30 ft 7 in × 8 ft, планування «спальня спереду —
кухня і дінет посередині — двоярусні ліжка ззаду», ДВОЄ дверей.

Що на схемі:
  · контур причепа і слайд-аут у масштабі;
  · меблі за опублікованим планом 268BH — приблизно, для розуміння проходу;
  · ОБИДВІ двері з розмірами: головна 26×74″ і задня в зону ліжок;
  · фігура 79×48″ у масштабі поруч — щоб було видно співвідношення;
  · переріз, який фігура пропонує дверям, коли її несуть НА БОЦІ.

Чесно про джерела: розміри головних дверей — з офіційної сторінки Keystone. Ширина
ЗАДНІХ дверей у відкритих даних не публікується, тому вона на схемі позначена як
«заміряти» — саме її має сенс перевірити рулеткою в Богдана.

  python3 project/model/rv_plan.py  →  rv_plan.svg
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent

EXT_L, EXT_W = 367.0, 96.0        # 30 ft 7 in × 8 ft
WALL = 3.0                        # стінка з обшивкою
INT_L, INT_W = EXT_L - 2 * WALL, EXT_W - 2 * WALL
DOOR_MAIN = (26.0, 74.0)          # keystonerv.com, Passport SL
DOOR_REAR_W = 26.0                # не підтверджено — позначено на схемі
FIG = (79.0, 47.7, 12.0)          # довжина, розмах по кистях, глибина
TUBE = 60.2

S = 2.6                           # пікселів на дюйм
INK, DIM, GREY = "#1b1b1b", "#555", "#a0a0a0"
RED, BLUE, GREEN, ORANGE = "#d81f1f", "#1f4fd8", "#0b8a3e", "#c2660a"


def px(v):
    return v * S


def t(x, y, s, size=11, fill=INK, anchor="start", weight="400"):
    s = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial,Helvetica,sans-serif" '
            f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


def box(x, y, w, h, label="", fill="#f2f2f2", stroke=GREY, sub="", size=10):
    o = [f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" '
         f'stroke="{stroke}" stroke-width="1.2"/>']
    if label:
        o.append(t(x + w / 2, y + h / 2 + 3, label, size, DIM, "middle"))
    if sub:
        o.append(t(x + w / 2, y + h / 2 + 15, sub, 9, GREY, "middle"))
    return "\n".join(o)


def dim_h(x1, x2, y, label, color=RED):
    return (f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" stroke="{color}" '
            f'stroke-width="1.4" marker-start="url(#a)" marker-end="url(#a)"/>\n'
            + t((x1 + x2) / 2, y - 6, label, 11, color, "middle", "700"))


def build() -> str:
    W, H = 1180, 900
    ox, oy = 60, 200
    o = [t(40, 36, "Причіп Богдана згори — Keystone Passport SL 268BH", 19, INK, "start", "700"),
         t(40, 58, "30 ft 7 in × 8 ft. Планування з опублікованого плану 268BH; меблі показані "
                   "приблизно, щоб було видно прохід. Розміри головних дверей — з сайта Keystone.",
           11, DIM),
         t(40, 76, "Ніс причепа ліворуч, задок праворуч. Двері — на правому по ходу боці "
                   "(на схемі знизу).", 11, DIM)]

    # корпус
    o.append(f'<rect x="{ox:.1f}" y="{oy:.1f}" width="{px(EXT_L):.1f}" height="{px(EXT_W):.1f}" '
             f'rx="{px(8):.1f}" fill="#ffffff" stroke="{INK}" stroke-width="2"/>')
    ix, iy = ox + px(WALL), oy + px(WALL)
    # дишло
    o.append(f'<path d="M{ox:.1f} {oy+px(EXT_W)/2-px(4):.1f} L{ox-px(26):.1f} {oy+px(EXT_W)/2:.1f} '
             f'L{ox:.1f} {oy+px(EXT_W)/2+px(4):.1f} Z" fill="none" stroke="{INK}" stroke-width="1.6"/>')
    o.append(t(ox - px(26) - 6, oy + px(EXT_W) / 2 + 4, "зчіп", 10, DIM, "end"))

    # меблі: спереду спальня, посередині кухня і дінет, ззаду ліжка
    o.append(box(ix, iy, px(80), px(INT_W), "спальня: ліжко queen", "#eef3ff", "#9db4e8", "80″ уздовж"))
    o.append(box(ix + px(80), iy, px(34), px(38), "санвузол", "#f7f2ea", "#cbbba2"))
    o.append(box(ix + px(80), iy + px(38), px(34), px(INT_W - 38), "шафа", "#f7f2ea", "#cbbba2"))
    # кухня вздовж дальньої стінки
    o.append(box(ix + px(118), iy, px(120), px(26), "кухня", "#f2f7f0", "#a9c6a1"))
    # слайд-аут з дінетом
    o.append(f'<rect x="{ix+px(126):.1f}" y="{oy-px(28):.1f}" width="{px(110):.1f}" '
             f'height="{px(28)+2:.1f}" fill="#f6f6ff" stroke="{BLUE}" stroke-width="1.4" '
             f'stroke-dasharray="6 4"/>')
    o.append(t(ix + px(181), oy - px(14) + 4, "слайд-аут (дінет)", 10, BLUE, "middle"))
    # прохід
    aisle_y = iy + px(28)
    aisle_h = px(INT_W - 28)
    o.append(f'<rect x="{ix+px(118):.1f}" y="{aisle_y:.1f}" width="{px(120):.1f}" height="{aisle_h:.1f}" '
             f'fill="{GREEN}" fill-opacity="0.08" stroke="{GREEN}" stroke-width="1" stroke-dasharray="5 4"/>')
    o.append(t(ix + px(178), aisle_y + aisle_h / 2 + 4, "прохід ≈ 30-36″", 10, GREEN, "middle"))
    # двоярусні ліжка ззаду
    o.append(box(ix + px(238), iy, px(INT_L - 238), px(INT_W), "двоярусні ліжка", "#fff4ee", "#e0b49a",
                 "сюди веде задні двері"))

    # ДВЕРІ
    door_y = oy + px(EXT_W) - 2
    dm_x = ix + px(150)
    o.append(f'<rect x="{dm_x:.1f}" y="{door_y-3:.1f}" width="{px(DOOR_MAIN[0]):.1f}" height="6" '
             f'fill="{RED}"/>')
    o.append(t(dm_x + px(13), door_y + 26, "головні двері", 11, RED, "middle", "700"))
    o.append(t(dm_x + px(13), door_y + 40, "26″ × 74″ (Keystone)", 10, RED, "middle"))
    dr_x = ix + px(272)
    o.append(f'<rect x="{dr_x:.1f}" y="{door_y-3:.1f}" width="{px(DOOR_REAR_W):.1f}" height="6" '
             f'fill="{ORANGE}"/>')
    o.append(t(dr_x + px(13), door_y + 26, "задні двері в зону ліжок", 11, ORANGE, "middle", "700"))
    o.append(t(dr_x + px(13), door_y + 40, "ширина не опублікована — заміряти", 10, ORANGE, "middle"))

    # шлях занесення
    o.append(f'<path d="M{dr_x+px(13):.1f} {door_y+px(16):.1f} L{dr_x+px(13):.1f} {iy+px(40):.1f}" '
             f'stroke="{ORANGE}" stroke-width="2.4" fill="none" marker-end="url(#o)" '
             f'stroke-dasharray="9 5"/>')
    o.append(f'<path d="M{dm_x+px(13):.1f} {door_y+px(16):.1f} L{dm_x+px(13):.1f} {aisle_y+aisle_h/2:.1f}" '
             f'stroke="{RED}" stroke-width="2" fill="none" marker-end="url(#r)" stroke-dasharray="9 5"/>')

    o.append(dim_h(ox, ox + px(EXT_L), oy - px(34), f'{EXT_L/12:.1f} ft ({EXT_L:.0f}″) — довжина'))

    # ── ФІГУРА В МАСШТАБІ ────────────────────────────────────────────────
    fy = oy + px(EXT_W) + 150
    o.append(t(40, fy - 30, "Фігура в тому ж масштабі і що саме бачать двері", 14, INK, "start", "700"))
    fx = 60
    o.append(f'<rect x="{fx:.1f}" y="{fy:.1f}" width="{px(FIG[0]):.1f}" height="{px(FIG[1]):.1f}" '
             f'fill="{BLUE}" fill-opacity="0.12" stroke="{BLUE}" stroke-width="1.6"/>')
    o.append(t(fx + px(FIG[0]) / 2, fy + px(FIG[1]) / 2 + 4,
               f'фігура згори: {FIG[0]:.0f}″ × {FIG[1]:.0f}″', 11, BLUE, "middle", "600"))

    # переріз у дверях
    cx = fx + px(FIG[0]) + 90
    o.append(t(cx, fy - 8, "переріз у дверях, якщо нести НА БОЦІ:", 11, INK, "start", "700"))
    dw, dh = px(DOOR_MAIN[0]), px(DOOR_MAIN[1])
    o.append(f'<rect x="{cx:.1f}" y="{fy+6:.1f}" width="{dw:.1f}" height="{dh:.1f}" '
             f'fill="none" stroke="{RED}" stroke-width="2"/>')
    o.append(t(cx + dw / 2, fy + dh + 22, "двері 26 × 74″", 10, RED, "middle"))
    o.append(f'<rect x="{cx + (dw-px(FIG[2]))/2:.1f}" y="{fy+6+(dh-px(TUBE))/2:.1f}" '
             f'width="{px(FIG[2]):.1f}" height="{px(TUBE):.1f}" fill="{GREEN}" fill-opacity="0.3" '
             f'stroke="{GREEN}" stroke-width="1.6"/>')
    o.append(t(cx + dw + 14, fy + 30, f'глибина {FIG[2]:.0f}″ проти 26″ — запас {26-FIG[2]:.0f}″',
               11, GREEN))
    o.append(t(cx + dw + 14, fy + 50, f'труба в плечах {TUBE:.1f}″ проти 74″ — запас {74-TUBE:.1f}″',
               11, GREEN))
    o.append(t(cx + dw + 14, fy + 70, f'без труби {FIG[1]:.1f}″ — запас {74-FIG[1]:.1f}″', 11, GREEN))
    o.append(t(cx + dw + 14, fy + 96, "Тобто вузьке місце — не двері.", 11, INK, "start", "700"))
    o.append(t(cx + dw + 14, fy + 114, "Вузьке місце — поріг на 26-30″ над землею", 11, DIM))
    o.append(t(cx + dw + 14, fy + 130, "і прохід усередині.", 11, DIM))
    o.append(t(cx + dw + 14, fy + 152, "Задні двері ведуть одразу до ліжок —", 11, ORANGE))
    o.append(t(cx + dw + 14, fy + 168, "нести повз кухню не треба.", 11, ORANGE))

    mk = lambda i, c: (f'<marker id="{i}" markerWidth="10" markerHeight="10" refX="5" refY="5" '
                       f'orient="auto"><path d="M1,1 L9,5 L1,9" fill="none" stroke="{c}" '
                       f'stroke-width="1.4"/></marker>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
            f'<defs>{mk("a", RED)}{mk("r", RED)}{mk("o", ORANGE)}</defs>\n'
            f'<rect width="{W}" height="{H}" fill="#ffffff"/>\n' + "\n".join(o) + "\n</svg>\n")


if __name__ == "__main__":
    out = HERE / "rv_plan.svg"
    out.write_text(build(), encoding="utf-8")
    print(f"готово: {out}")
