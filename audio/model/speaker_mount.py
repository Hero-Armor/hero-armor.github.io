#!/usr/bin/env python3
"""
Hero Armor — креслення посадкового місця динаміка в броні.

Навіщо: у розділі «Креслення» на сторінці звуку креслення НЕ БУЛО (замість
нього лежало фото коробок — Іван знайшов 02.08). Посадкове місце — єдине,
що фізично звʼязує аудіо-вузол із бронею, і саме його треба дати
конструктору й тому, хто друкує решітку.

Тільки stdlib: SVG пишеться текстом, щоб підписи лишались текстом і
перекладались в англійську версію дашборда (правило репо).

Розміри — з audio/data/params.json (обраний динамік) і audio/data/mount.json.
Жодної цифри руками в цьому файлі: усе з json.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
OUT = HERE / "speaker_mount.svg"

m = json.loads((DATA / "mount.json").read_text())
S = m["scale_px_per_mm"]
front, cut = m["front"], m["section"]


def px(mm):
    return mm * S


def text(x, y, s, size=11, anchor="middle", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="Helvetica, Arial" '
            f'font-size="{size}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


def line(x1, y1, x2, y2, w=1.4, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#000" stroke-width="{w}"{d}/>')


def circle(cx, cy, r, w=1.4, dash=None, fill="none"):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" '
            f'stroke="#000" stroke-width="{w}"{d}/>')


def rect(x, y, w, h, sw=1.4, fill="none", dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'fill="{fill}" stroke="#000" stroke-width="{sw}"{d}/>')


def dim_h(x1, x2, y, label):
    """Розмірна лінія по горизонталі зі стрілками-засічками."""
    out = [line(x1, y, x2, y, 1.0)]
    for x in (x1, x2):
        out.append(line(x, y - 5, x, y + 5, 1.0))
    out.append(text((x1 + x2) / 2, y - 7, label, 11))
    return out


def dim_v(x, y1, y2, label):
    out = [line(x, y1, x, y2, 1.0)]
    for y in (y1, y2):
        out.append(line(x - 5, y, x + 5, y, 1.0))
    out.append(text(x + 6, (y1 + y2) / 2 + 4, label, 11, anchor="start"))
    return out


W, H = m["canvas"]
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
       f'viewBox="0 0 {W} {H}">', f'<rect width="{W}" height="{H}" fill="#fff"/>']

# ─────────────────────────── вид спереду ───────────────────────────
cx, cy = m["front_center"]
svg.append(text(cx, 30, m["title_front"], 14, weight="bold"))

svg.append(circle(cx, cy, px(front["flange_d"] / 2)))                    # фланець
svg.append(circle(cx, cy, px(front["cut_d"] / 2), dash="7,5"))           # виріз у броні
svg.append(circle(cx, cy, px(front["cone_d"] / 2), w=1.0))               # мембрана
for i, ang in enumerate(front["screws_deg"]):
    import math
    a = math.radians(ang)
    sx = cx + px(front["screw_circle_d"] / 2) * math.cos(a)
    sy = cy + px(front["screw_circle_d"] / 2) * math.sin(a)
    svg.append(circle(sx, sy, px(front["screw_d"] / 2), w=1.2))

svg += dim_h(cx - px(front["cut_d"] / 2), cx + px(front["cut_d"] / 2),
             cy + px(front["flange_d"] / 2) + 34, front["cut_label"])
svg += dim_h(cx - px(front["flange_d"] / 2), cx + px(front["flange_d"] / 2),
             cy + px(front["flange_d"] / 2) + 66, front["flange_label"])
svg.append(text(cx, cy + px(front["flange_d"] / 2) + 96, front["note"], 11))

# ─────────────────────────── розріз ───────────────────────────
sx0, sy0 = m["section_origin"]
svg.append(text(sx0 + 150, 30, m["title_section"], 14, weight="bold"))

skin_t = px(cut["skin_mm"])
svg.append(rect(sx0, sy0, skin_t, px(cut["skin_h_mm"]), fill="#e8e8e8"))   # обшивка броні
svg.append(text(sx0 + skin_t / 2, sy0 - 10, cut["skin_label"], 11))

# отвір в обшивці — розрив у прямокутнику показуємо світлим блоком
hole_h = px(cut["cut_d"])
hole_y = sy0 + (px(cut["skin_h_mm"]) - hole_h) / 2
svg.append(rect(sx0 - 1, hole_y, skin_t + 2, hole_h, sw=0, fill="#fff"))
svg.append(line(sx0, hole_y, sx0 + skin_t, hole_y, 1.4))
svg.append(line(sx0, hole_y + hole_h, sx0 + skin_t, hole_y + hole_h, 1.4))

# корпус динаміка — за обшивкою
bx = sx0 + skin_t
svg.append(rect(bx, hole_y, px(cut["depth_mm"]), hole_h))
svg.append(text(bx + px(cut["depth_mm"]) / 2, hole_y + hole_h / 2 + 4, cut["body_label"], 11))
# фланець притискає обшивку зовні
svg.append(rect(sx0 - px(cut["flange_t_mm"]), hole_y - px(cut["flange_lip_mm"]),
                px(cut["flange_t_mm"]), hole_h + 2 * px(cut["flange_lip_mm"]), fill="#d0d0d0"))
svg.append(text(sx0 - px(cut["flange_t_mm"]) - 8, hole_y - px(cut["flange_lip_mm"]) - 8,
                cut["flange_label"], 11, anchor="end"))

svg += dim_h(bx, bx + px(cut["depth_mm"]), hole_y - 26, cut["depth_label"])
svg += dim_v(bx + px(cut["depth_mm"]) + 30, hole_y, hole_y + hole_h, cut["cut_label"])
# примітки — суцільним блоком по центру листа, щоб не лізли на розмірні лінії
note_y = m["notes_y"]
for i, key in enumerate(("note1", "note2", "note3")):
    svg.append(text(W / 2, note_y + i * 21, cut[key], 11))

svg.append(text(W / 2, H - 16, m["footer"], 11))
svg.append("</svg>")

OUT.write_text("\n".join(svg))
print(f"wrote {OUT.name}")
