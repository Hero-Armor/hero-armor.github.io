#!/usr/bin/env python3
"""Вигляд зверху до схем Володимира — де саме лишається місце.

Володимир 15.08 порахував завантаження Pacifica у двох видах, збоку і з торця, і
зробив висновок: станція та її ящик навряд влізуть. Але обидва його види показують
ВИСОТУ, а вільне місце в цьому завантаженні лишається не по висоті, а з БОКІВ —
фігура вужча за подіум скрізь, крім плечей. Ця схема добудовує третій вид і міряє
ті кишені числами, щоб рішення «влізе / не влізе» спиралось на розмір, а не на око.

Що показано:
  · контур вантажного відсіку і подіум 96×48″ під ним;
  · силует фігури зверху в масштабі: голова, плечі, руки, таз, ноги;
  · чотири вільні кишені з розмірами — біля голови, обабіч ніг і за стопами;
  · станція EcoFlow (613×328 мм = 24.1×12.9″) укладена в ту кишеню, куди справді
    заходить, — щоб було видно, що зауваження Володимира знімається саме тут.

Стиль навмисно як у креслень Володимира: світлий фон, синій контур вантажу,
червоний — подіум. Так три види читаються як один комплект.

  python3 project/model/transport_top_view.py  →  transport_top_view.svg
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
D = json.loads((ROOT / "project/data/transport.json").read_text(encoding="utf-8"))

BOX, FIG = D["box_in"], D["figure"]
CABIN_W = 49.0          # ширина вантажного отвору Pacifica зі схеми Володимира
CABIN_L = 99.5          # довжина вантажного відсіку зі складеними сидіннями
STATION = (24.1, 12.9)  # EcoFlow DELTA 3 Ultra Plus, 613×328 мм

S = 9.0                 # пікселів на дюйм
PAD = 78
INK, DIM = "#1b1b1b", "#6b6b6b"
BLUE, RED, GREEN = "#1f4fd8", "#d81f1f", "#1f9d55"
BG = "#ffffff"


def px(v):
    return v * S


def t(x, y, s, size=12, fill=INK, anchor="start", weight="400"):
    # & у підписах ламає SVG як XML — екрануємо, інакше картинка не відкриється взагалі
    s = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial,Helvetica,sans-serif" '
            f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


def dim_h(x1, x2, y, label, color=DIM):
    return (f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" stroke="{color}" '
            f'stroke-width="1" marker-start="url(#ar)" marker-end="url(#ar)"/>\n'
            + t((x1 + x2) / 2, y - 5, label, 11, color, "middle"))


def dim_v(x, y1, y2, label, color=DIM):
    return (f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" stroke="{color}" '
            f'stroke-width="1" marker-start="url(#ar)" marker-end="url(#ar)"/>\n'
            + t(x + 6, (y1 + y2) / 2 + 4, label, 11, color))


def pocket(x, y, w, h, label, sub=""):
    """Вільна кишеня: зелена штриховка плюс розмір."""
    o = [f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{GREEN}" '
         f'fill-opacity="0.13" stroke="{GREEN}" stroke-width="1.2" stroke-dasharray="6 4"/>']
    if w > px(9) and h > px(5):
        o.append(t(x + w / 2, y + h / 2 + 4, label, 11, GREEN, "middle", "600"))
        if sub:
            o.append(t(x + w / 2, y + h / 2 + 18, sub, 10, GREEN, "middle"))
    return "\n".join(o)


def build() -> str:
    w = int(px(CABIN_L) + PAD * 2 + 250)
    h = int(px(CABIN_W) + PAD * 2 + 130)
    ox, oy = PAD + 40, PAD

    o = [t(ox, oy - 42, "TOP VIEW — вигляд зверху (доповнення до схем В. Кормільця)", 15, INK, "start", "700"),
         t(ox, oy - 24, "де саме лишається вільне місце над подіумом", 12, DIM)]

    # вантажний відсік
    o.append(f'<rect x="{ox:.1f}" y="{oy:.1f}" width="{px(CABIN_L):.1f}" height="{px(CABIN_W):.1f}" '
             f'fill="none" stroke="{INK}" stroke-width="1.6"/>')
    # подіум під усім вантажем
    py_ = oy + (px(CABIN_W) - px(BOX["w"])) / 2
    o.append(f'<rect x="{ox:.1f}" y="{py_:.1f}" width="{px(BOX["l"]):.1f}" height="{px(BOX["w"]):.1f}" '
             f'fill="none" stroke="{RED}" stroke-width="1.8"/>')
    o.append(t(ox + px(2), py_ + px(BOX["w"]) - 8, "Podium 1 + 2  ·  96″ × 48″", 12, RED))

    # силует фігури: голова ліворуч, ноги праворуч
    cy = oy + px(CABIN_W) / 2
    sh, hip = px(FIG["shoulders_in"]), px(FIG["hips_in"])
    head_r = px(5.0)
    fx = ox + px(3)
    body_len = px(FIG["height_in"]) * 0.44
    o.append(f'<circle cx="{fx+head_r:.1f}" cy="{cy:.1f}" r="{head_r:.1f}" fill="none" stroke="{BLUE}" stroke-width="1.6"/>')
    bx = fx + head_r * 1.7
    o.append(f'<path d="M{bx:.1f} {cy-sh/2:.1f} L{bx+body_len:.1f} {cy-hip/2:.1f} '
             f'L{bx+body_len:.1f} {cy+hip/2:.1f} L{bx:.1f} {cy+sh/2:.1f} Z" '
             f'fill="none" stroke="{BLUE}" stroke-width="1.8"/>')
    arm = px(3.4)
    for sgn in (-1, 1):
        ay = cy + sgn * (sh / 2 - arm * 0.8)
        o.append(f'<rect x="{bx+px(4):.1f}" y="{ay-arm/2:.1f}" width="{body_len*0.72:.1f}" height="{arm:.1f}" '
                 f'rx="{arm/2:.1f}" fill="none" stroke="{BLUE}" stroke-width="1.2"/>')
    legs_x = bx + body_len
    legs_end = fx + px(FIG["height_in"])
    leg_w = (hip - px(FIG["leg_gap_in"]) * 0.3) / 2
    for sgn in (-1, 1):
        ly = cy + sgn * (px(FIG["leg_gap_in"]) * 0.3 / 2 + leg_w / 2)
        o.append(f'<rect x="{legs_x:.1f}" y="{ly-leg_w/2:.1f}" width="{legs_end-legs_x:.1f}" '
                 f'height="{leg_w:.1f}" rx="{px(1.5):.1f}" fill="none" stroke="{BLUE}" stroke-width="1.6"/>')
    o.append(t(bx + px(4), cy + 4, "Robot & frame", 12, BLUE, "start", "600"))

    # вільні кишені
    side = (BOX["w"] - FIG["hips_in"]) / 2          # обабіч ніг
    top_p = py_
    bot_p = py_ + px(BOX["w"])
    o.append(pocket(legs_x, top_p, legs_end - legs_x, cy - hip / 2 - top_p, "", ""))
    o.append(pocket(legs_x, cy + hip / 2, legs_end - legs_x, bot_p - (cy + hip / 2),
                    f'вільно {side:.0f}″', "ящики, кабелі"))
    tail = BOX["l"] - FIG["height_in"]
    o.append(pocket(legs_end, top_p, px(tail), px(BOX["w"]), f'{tail:.0f}″ за стопами', "інструмент"))

    # станція в кишені
    st_w, st_h = px(STATION[0]), px(STATION[1])
    sx = legs_x + px(3)
    sy = top_p + (cy - hip / 2 - top_p - st_h) / 2
    o.append(f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{st_w:.1f}" height="{st_h:.1f}" '
             f'fill="{GREEN}" fill-opacity="0.25" stroke="{GREEN}" stroke-width="1.6"/>')
    o.append(t(sx + st_w / 2, sy + st_h / 2 + 4, f'EcoFlow {STATION[0]}″×{STATION[1]}″', 11, "#0b6b3a", "middle", "700"))
    o.append(t(sx + st_w + px(2), sy + st_h / 2 + 4, f'кишеня {side:.0f}″ — станція заходить', 10, GREEN))

    # розміри
    o.append(dim_h(ox, ox + px(CABIN_L), oy + px(CABIN_W) + 34, f'{CABIN_L}″ — довжина відсіку'))
    o.append(dim_h(ox, ox + px(BOX["l"]), oy + px(CABIN_W) + 58, f'{BOX["l"]}″ — подіум', RED))
    o.append(dim_v(ox + px(CABIN_L) + 16, oy, oy + px(CABIN_W), f'{CABIN_W:.0f}″'))
    o.append(dim_v(bx + px(20), cy - sh / 2, cy + sh / 2, f'плечі {FIG["shoulders_in"]}″', BLUE))
    o.append(dim_v(legs_x + px(26), cy - hip / 2, cy + hip / 2, f'стегна {FIG["hips_in"]}″', BLUE))
    o.append(dim_v(legs_x + px(12), top_p, cy - hip / 2, f'{side:.0f}″', GREEN))

    # висновок
    y0 = oy + px(CABIN_W) + 84
    o.append(t(ox, y0, "Що з цього видно:", 12, INK, "start", "700"))
    o.append(t(ox, y0 + 18, f'· у плечах фігура {FIG["shoulders_in"]}″ проти подіуму {BOX["w"]}″ — там вільно '
                            f'по {(BOX["w"]-FIG["shoulders_in"])/2:.0f}″ з боку, це найвужче місце;', 11, DIM))
    o.append(t(ox, y0 + 34, f'· уздовж ніг фігура {FIG["hips_in"]}″ — вільна смуга {side:.0f}″ з КОЖНОГО боку '
                            f'на всю довжину ніг;', 11, DIM))
    o.append(t(ox, y0 + 50, f'· за стопами лишається {tail:.0f}″ на всю ширину;', 11, DIM))
    o.append(t(ox, y0 + 66, f'· станція EcoFlow {STATION[0]}″×{STATION[1]}″ у бічну кишеню заходить — '
                            f'саме це знімає зауваження «станція не влізе».', 11, "#0b6b3a"))

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h+70}" viewBox="0 0 {w} {h+70}">\n'
            f'<defs><marker id="ar" markerWidth="9" markerHeight="9" refX="4.5" refY="4.5" orient="auto">'
            f'<path d="M1,1 L8,4.5 L1,8" fill="none" stroke="{DIM}" stroke-width="1"/></marker></defs>\n'
            f'<rect width="{w}" height="{h+70}" fill="{BG}"/>\n' + "\n".join(o) + "\n</svg>\n")


if __name__ == "__main__":
    out = HERE / "transport_top_view.svg"
    out.write_text(build(), encoding="utf-8")
    print(f"готово: {out}")
