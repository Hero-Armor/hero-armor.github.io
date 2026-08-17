#!/usr/bin/env python3
"""Ящик під станцію і генератор — план згори і розріз.

Постановка Івана 16.08.2026: один ящик, у ньому станція і генератор, між ними
перегородка, бо генератор гріє. Ця схема показує не «як гарно скласти дві коробки»,
а три речі, на яких така конструкція зазвичай і горить:

  · куди йде повітря — генератор охолоджується примусово і глухий ящик його вбʼє;
  · куди йде вихлоп — крізь гільзу назовні, а не «десь у щілину»;
  · що саме розділяє відсіки — мінеральна вата з фольгою, а не піна.

Числа заліза з офіційних сторінок EcoFlow (enclosure/data/genbox.json).
Габарит самого ящика — прикидка під ескіз, і на схемі це підписано.

  python3 enclosure/model/genbox_plan.py  →  genbox_plan.svg
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = json.loads((HERE.parent / "data/genbox.json").read_text(encoding="utf-8"))

GEN = D["units"]["generator"]["size_mm"]
STA = D["units"]["station"]["size_mm"]
INNER = D["size_estimate"]["inner_mm"]

S = 0.42                      # пікселів на мм
INK, DIM, GREY = "#1b1b1b", "#555", "#a0a0a0"
RED, BLUE, GREEN, ORANGE = "#d81f1f", "#1f4fd8", "#0b8a3e", "#c2660a"


def px(v):
    return v * S


def t(x, y, s, size=11, fill=INK, anchor="start", weight="400"):
    s = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial,Helvetica,sans-serif" '
            f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


def box(x, y, w, h, label="", sub="", fill="#f4f6fb", stroke=GREY, lw=1.4):
    o = [f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" '
         f'stroke="{stroke}" stroke-width="{lw}"/>']
    if label:
        o.append(t(x + w / 2, y + h / 2 - (4 if sub else -4), label, 11.5, INK, "middle", "600"))
    if sub:
        o.append(t(x + w / 2, y + h / 2 + 12, sub, 10, DIM, "middle"))
    return "\n".join(o)


def dim_h(x1, x2, y, label, color=RED):
    return (f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" stroke="{color}" '
            f'stroke-width="1.3" marker-start="url(#a)" marker-end="url(#a)"/>\n'
            + t((x1 + x2) / 2, y - 6, label, 10.5, color, "middle", "700"))


def arrow(x1, y1, x2, y2, color, w=2.4):
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" '
            f'stroke-width="{w}" marker-end="url(#f{color[1:]})"/>')


def build() -> str:
    W, H = 1240, 900
    o = [t(40, 34, "Ящик під станцію і генератор — план і розріз", 19, INK, "start", "700"),
         t(40, 56, "Габарити заліза — з офіційних сторінок EcoFlow. Габарит самого ящика — "
                   "прикидка під ескіз, уточнюється після підтвердження моделі генератора.", 11, DIM),
         t(40, 74, "Головне на схемі не розміри, а три речі: рух повітря, вихід вихлопу і з чого "
                   "зроблена перегородка.", 11, DIM)]

    # ── ПЛАН ЗГОРИ ───────────────────────────────────────────────────────
    ox, oy = 60, 130
    bw, bh = px(INNER[0]), px(INNER[1])
    o.append(t(ox, oy - 14, "ПЛАН ЗГОРИ", 13, INK, "start", "700"))
    o.append(box(ox - 8, oy - 8, bw + 16, bh + 16, "", "", "#ffffff", INK, 2))
    o.append(t(ox + bw + 22, oy + 12, "фанера 12-15 мм", 10, DIM))

    # станція ліворуч
    sw, sh = px(STA[0]), px(STA[1])
    o.append(box(ox + px(30), oy + (bh - sh) / 2, sw, sh, "станція",
                 f'{STA[0]}×{STA[1]} мм · 33.7 кг', "#eef3ff", "#9db4e8"))
    # перегородка
    px0 = ox + px(30) + sw + px(20)
    o.append(box(px0, oy, px(90), bh, "", "", "#fff6e8", ORANGE, 1.8))
    o.append(t(px0 + px(45), oy + bh + 16, "перегородка", 10.5, ORANGE, "middle", "700"))
    o.append(t(px0 + px(45), oy + bh + 30, "вата 50 мм + фольга", 10, ORANGE, "middle"))
    # генератор
    gw, gh = px(GEN[0]), px(GEN[1])
    gx = px0 + px(90) + px(20)
    o.append(box(gx, oy + (bh - gh) / 2, gw, gh, "генератор",
                 f'{GEN[0]}×{GEN[1]} мм · 38 кг', "#fdeeee", "#e0a0a0"))

    # вихлоп
    o.append(arrow(gx + gw, oy + bh / 2, gx + gw + px(150), oy + bh / 2, RED))
    o.append(t(gx + gw + px(20), oy + bh / 2 - 10, "вихлоп назовні", 10.5, RED, "start", "700"))
    o.append(t(gx + gw + px(20), oy + bh / 2 + 14, "гофра в металевій гільзі", 10, DIM))

    # повітря
    o.append(arrow(ox - px(60), oy + bh - px(40), ox + px(20), oy + bh - px(40), BLUE))
    o.append(t(ox - px(60), oy + bh - px(52), "повітря входить", 10.5, BLUE, "start", "700"))
    o.append(dim_h(ox - 8, ox + bw + 8, oy + bh + 56, f'≈{INNER[0]} мм — прикидка'))

    # ── РОЗРІЗ ───────────────────────────────────────────────────────────
    oy2 = oy + bh + 130
    bh2 = px(INNER[2])
    o.append(t(ox, oy2 - 14, "РОЗРІЗ", 13, INK, "start", "700"))
    o.append(box(ox - 8, oy2 - 8, bw + 16, bh2 + 16, "", "", "#ffffff", INK, 2))
    o.append(box(ox + px(30), oy2 + bh2 - px(395), sw, px(395), "станція", "395 мм заввишки",
                 "#eef3ff", "#9db4e8"))
    o.append(box(px0, oy2, px(90), bh2, "", "", "#fff6e8", ORANGE, 1.8))
    o.append(box(gx, oy2 + bh2 - px(529), gw, px(529), "генератор", "529 мм заввишки",
                 "#fdeeee", "#e0a0a0"))
    # потоки
    o.append(arrow(ox + px(10), oy2 + bh2 - px(30), ox + px(10), oy2 + px(40), BLUE, 3))
    o.append(t(ox + px(16), oy2 + px(30), "холодне знизу", 10.5, BLUE, "start", "700"))
    o.append(arrow(gx + gw / 2, oy2 + px(60), gx + gw / 2, oy2 - px(30), GREEN, 3))
    o.append(t(gx + gw / 2 + 8, oy2 - px(20), "гаряче вгору + вентилятор", 10.5, GREEN, "start", "700"))
    o.append(t(ox, oy2 + bh2 + 34, "вхід унизу з боку станції · вихід угорі з боку генератора — "
                                   "проти конвекції не працюємо", 10.5, DIM))
    o.append(dim_h(ox - 8, ox + bw + 8, oy2 + bh2 + 62, f'висота ≈{INNER[2]} мм'))

    # ── ПРАВИЛА ──────────────────────────────────────────────────────────
    rx = ox + bw + 90
    o.append(t(rx, oy - 14, "ЧОГО НЕ МОЖНА", 13, RED, "start", "700"))
    rules = [("Глухий ящик", "Генератор засмоктує повітря і викидає гаряче. Без наскрізного "
                             "продуву це піч: паспортна стеля 40 °C, на плайї в тіні і так під 40."),
             ("Піна", "Ні поліуретан, ні пінополістирол. Плавляться і горять біля вихлопу. "
                      "Тільки мінеральна вата — вона негорюча."),
             ("МДФ", "Набирає вологу від першої роси і розбухає, важчий за фанеру. "
                     "Береза 12-15 мм робить те саме легше і надійніше."),
             ("Вихлоп у щілину", "Тільки труба назовні і датчик чадного газу — в ящику і в житлі."),
             ("Паливо в ящику", "Балон і каністра живуть окремо, з піддоном під розлив.")]
    for i, (h1, body) in enumerate(rules):
        y = oy + 14 + i * 74
        o.append(t(rx, y, "· " + h1, 11.5, RED, "start", "700"))
        words, line, lines = body.split(), "", []
        for w in words:
            if len(line) + len(w) > 44:
                lines.append(line); line = w
            else:
                line = (line + " " + w).strip()
        lines.append(line)
        for j, ln in enumerate(lines[:4]):
            o.append(t(rx + 10, y + 16 + j * 14, ln, 10.3, DIM))

    o.append(t(rx, oy2 - 14, "СТЕЛЯ ПО ТЕПЛУ", 13, INK, "start", "700"))
    for i, ln in enumerate(["генератор працює до 40 °C навколо",
                            "станція заряджається до 45 °C",
                            "найкраще станції — 20-30 °C",
                            "тобто ящик мусить бути ХОЛОДНІШИЙ за вулицю,",
                            "а не теплішим — звідси вентилятор, а не щілини"]):
        o.append(t(rx, oy2 + 12 + i * 18, ln, 10.8, INK if i < 3 else GREEN))

    mk = lambda c: (f'<marker id="f{c[1:]}" markerWidth="10" markerHeight="10" refX="6" refY="5" '
                    f'orient="auto"><path d="M1,1 L9,5 L1,9 z" fill="{c}"/></marker>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
            f'<defs><marker id="a" markerWidth="9" markerHeight="9" refX="4.5" refY="4.5" orient="auto">'
            f'<path d="M1,1 L8,4.5 L1,8" fill="none" stroke="{RED}" stroke-width="1.2"/></marker>'
            f'{mk(RED)}{mk(BLUE)}{mk(GREEN)}</defs>\n'
            f'<rect width="{W}" height="{H}" fill="#ffffff"/>\n' + "\n".join(o) + "\n</svg>\n")


def demo() -> int:
    s = build()
    assert "<svg" in s and s.count("<text") > 30
    assert "мінеральна вата" in s or "вата" in s
    # габарит ящика мусить бути більшим за суму заліза
    assert INNER[0] > GEN[0] + STA[0], "ящик вужчий за те, що в нього кладемо"
    assert INNER[2] > GEN[2], "ящик нижчий за генератор"
    print("demo ok — схема будується, габарит більший за вміст")
    return 0


if __name__ == "__main__":
    import sys
    if "--demo" in sys.argv:
        sys.exit(demo())
    out = HERE / "genbox_plan.svg"
    out.write_text(build(), encoding="utf-8")
    print(f"готово: {out}")
