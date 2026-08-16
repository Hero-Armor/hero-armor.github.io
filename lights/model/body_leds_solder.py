#!/usr/bin/env python3
"""Світлодіоди на корпусі фігури — що з чим паяти знизу.

Навіщо. 16.08.2026 Іван: корпус уже закритий, дроти від світлодіодів виведені ВНИЗ,
паяти доведеться там же, наосліп для самих світлодіодів. Тому схема має відповідати
на три питання і не більше: скільки гілок, який резистор у кожній і де плюс.

Головне правило, яке легко порушити: у кожного світлодіода СВІЙ резистор. Вішати
два світлодіоди паралельно на один резистор не можна — розкид прямої напруги
призводить до того, що один забирає струм на себе, світить яскравіше і швидше
вигорає.

Про колір і напругу. Пряма напруга світлодіода задається шириною забороненої зони
кристала, а вона ж задає колір: жовті й червоні роблять на AlGaInP і вони мають
близько 2.0-2.2 В, сині, зелені й білі — на InGaN, близько 3 В (білий це синій
кристал плюс люмінофор). Це не марка і не виробник, це фізика кристала.

АЛЕ на шині 12 В ця різниця майже нічого не міняє: резистор бачить 9.9 В проти 9.0 В,
тобто струм відрізняється на 9%. Тому колір тут не критичний, і 1 кОм безпечний в
обидва боки: жовтий дасть 9.9 мА, білий 9.0 мА. Знати Vf точно важливо на живленні
3-5 В, а не на дванадцяти. У таблиці нижче обидва випадки — але вибирати між ними
не обовʼязково.

  python3 lights/model/body_leds_solder.py  →  body_leds_solder.svg
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent

BUS_V = 12.0
GROUPS = [("шолом", 4, "над очима, справа і зліва"),
          ("пояс", 2, "два по боках")]
VF = {"жовтий": 2.1, "білий або синій": 3.0}
CURRENTS = [0.010, 0.015, 0.020]

W, H = 1240, 1010
INK, DIM, GREY = "#1b1b1b", "#555", "#9a9a9a"
RED, BLACK, GREEN, ORANGE = "#d81f1f", "#1b1b1b", "#0b8a3e", "#c2660a"


def t(x, y, s, size=12, fill=INK, anchor="start", weight="400"):
    s = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial,Helvetica,sans-serif" '
            f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


def resistor(x, y, w=46, h=16):
    """Прямокутник резистора з виводами."""
    return (f'<rect x="{x:.1f}" y="{y-h/2:.1f}" width="{w}" height="{h}" fill="#fff" '
            f'stroke="{INK}" stroke-width="1.6"/>')


def led(x, y, r=11, color=ORANGE):
    """Світлодіод: трикутник із рискою і стрілками."""
    return (f'<path d="M{x-r:.1f} {y-r:.1f} L{x-r:.1f} {y+r:.1f} L{x+r*0.7:.1f} {y:.1f} Z" '
            f'fill="{color}" fill-opacity="0.25" stroke="{INK}" stroke-width="1.6"/>'
            f'<line x1="{x+r*0.7:.1f}" y1="{y-r:.1f}" x2="{x+r*0.7:.1f}" y2="{y+r:.1f}" '
            f'stroke="{INK}" stroke-width="2"/>'
            f'<path d="M{x+2:.1f} {y-r-4:.1f} l7,-7 M{x+9:.1f} {y-r-6:.1f} l3,-1 -1,3" '
            f'stroke="{INK}" stroke-width="1.2" fill="none"/>')


def calc_rows():
    """Таблиця номіналів: (колір, струм, опір, найближчий стандартний, розсіювання)."""
    STD = [330, 390, 470, 510, 560, 620, 680, 750, 820, 910, 1000, 1200]
    out = []
    for name, vf in VF.items():
        for i in CURRENTS:
            r = (BUS_V - vf) / i
            std = min(STD, key=lambda s: abs(s - r))
            p = i * i * std
            out.append((name, i, r, std, p))
    return out


def build() -> str:
    o = [t(40, 36, "Світлодіоди на корпусі — що з чим паяти знизу", 19, INK, "start", "700"),
         t(40, 58, "Корпус закритий, дроти виведені вниз. Кожна гілка однакова: "
                   "плюс шини → резистор → світлодіод → мінус шини.", 12, DIM),
         t(40, 76, "У КОЖНОГО світлодіода свій резистор. Два світлодіоди на один резистор "
                   "паралельно вішати не можна.", 12, RED, "start", "600"),
         t(40, 96, "1 кОм безпечний і для жовтого, і для білого: на 12 В різниця в струмі всього 9% "
                   "(9.9 проти 9.0 мА). Колір тут не критичний.", 12, GREEN, "start", "600")]

    # ── шини ─────────────────────────────────────────────────────────────
    x0, x1 = 120, 620
    y_plus, y_minus = 170, 490
    o.append(f'<line x1="{x0}" y1="{y_plus}" x2="{x1}" y2="{y_plus}" stroke="{RED}" stroke-width="3.5"/>')
    o.append(f'<line x1="{x0}" y1="{y_minus}" x2="{x1}" y2="{y_minus}" stroke="{BLACK}" stroke-width="3.5"/>')
    o.append(t(x0 - 10, y_plus + 4, "+12 В", 13, RED, "end", "700"))
    o.append(t(x0 - 10, y_minus + 4, "мінус", 13, BLACK, "end", "700"))
    o.append(t(x0 - 10, y_plus - 16, "від щита, група Гр.2", 10.5, DIM, "end"))

    # ── гілки ────────────────────────────────────────────────────────────
    total = sum(n for _, n, _ in GROUPS)
    step = (x1 - x0 - 80) / max(1, total - 1)
    x = x0 + 40
    idx = 0
    for gname, n, where in GROUPS:
        gx0 = x
        for k in range(n):
            o.append(f'<line x1="{x:.1f}" y1="{y_plus}" x2="{x:.1f}" y2="{y_plus+60}" '
                     f'stroke="{RED}" stroke-width="2"/>')
            o.append(f'<g transform="rotate(90 {x:.1f} {y_plus+90:.1f})">' +
                     resistor(x - 23, y_plus + 90) + '</g>')
            o.append(f'<line x1="{x:.1f}" y1="{y_plus+113}" x2="{x:.1f}" y2="{y_plus+150}" '
                     f'stroke="{RED}" stroke-width="2"/>')
            o.append(f'<g transform="rotate(90 {x:.1f} {y_plus+168:.1f})">' + led(x, y_plus + 168) + '</g>')
            o.append(f'<line x1="{x:.1f}" y1="{y_plus+186}" x2="{x:.1f}" y2="{y_minus}" '
                     f'stroke="{BLACK}" stroke-width="2"/>')
            o.append(t(x + 16, y_plus + 92, "R", 11.5, INK, "start", "700"))
            o.append(t(x + 16, y_plus + 172, "LED", 10.5, DIM))
            x += step
            idx += 1
        gxe = x - step
        o.append(f'<line x1="{gx0-16:.1f}" y1="{y_minus+30}" x2="{gxe+16:.1f}" y2="{y_minus+30}" '
                 f'stroke="{GREEN}" stroke-width="1.4"/>')
        o.append(t((gx0 + gxe) / 2, y_minus + 48, f'{gname} — {n} шт', 12, GREEN, "middle", "700"))
        o.append(t((gx0 + gxe) / 2, y_minus + 64, where, 10.5, GREY, "middle"))
        x += step * 0.5

    o.append(t(x1 + 46, y_plus + 92, "свій на кожен", 10.5, DIM))
    o.append(t(x1 + 46, y_plus + 172, "довга ніжка = плюс", 10.5, DIM))

    # ── таблиця номіналів ────────────────────────────────────────────────
    ty = y_minus + 110
    o.append(t(40, ty, "Який резистор ставити", 15, INK, "start", "700"))
    o.append(t(40, ty + 20, "Порахунок від шини 12 В. Беремо 1/2 Вт, а не 1/4: запас на спеку +40 °C.",
               11.5, DIM))
    hdr = ["колір світлодіода", "струм", "розрахунок", "СТАВИМО", "гріється"]
    cols = [40, 230, 320, 430, 560]
    for c, hh in zip(cols, hdr):
        o.append(t(c, ty + 46, hh, 11, GREY, "start", "700"))
    for i, (name, cur, r, std, p) in enumerate(calc_rows()):
        y = ty + 68 + i * 19
        best = abs(cur - 0.010) < 1e-9
        col = GREEN if best else INK
        o.append(t(cols[0], y, name, 11, col, "start", "600" if best else "400"))
        o.append(t(cols[1], y, f'{cur*1000:.0f} мА', 11, col))
        o.append(t(cols[2], y, f'{r:.0f} Ом', 11, GREY))
        o.append(t(cols[3], y, f'{std} Ом', 11.5, col, "start", "700"))
        o.append(t(cols[4], y, f'{p*1000:.0f} мВт', 11, GREY))
    o.append(t(cols[0], ty + 68 + len(calc_rows()) * 19 + 16,
               "Зеленим — рекомендація: 10 мА. На 12 В колір впливає на струм лише на 9%, "
               "тому 1 кОм можна ставити не розбираючись.", 11.5, GREEN))

    # ── бічна колонка порад ──────────────────────────────────────────────
    sx = 760
    o.append(t(sx, ty, "Перед паянням", 15, INK, "start", "700"))
    tips = [
        ("Який у вас світлодіод", "Жовтий — 2.1 В, білий і синій — 3 В. Якщо не знаєте: "
                                  "мультиметр у режимі перевірки діода покаже пряму напругу."),
        ("Де плюс", "Довга ніжка — плюс. Якщо ніжки вже обрізані: у мультиметрі режим діода, "
                    "світлодіод блимне, коли червоний щуп на плюсі."),
        ("Резистор — у плюсовий провід", "Електрично байдуже, але так плюс скрізь через резистор, "
                                         "і випадкове коротке на корпус не спалить світлодіод."),
        ("Кожен резистор — у термоусадку", "Голий вивід у закритому корпусі знизу — це замикання, "
                                           "яке ви побачите вже на плайї."),
        ("Не паяйте все в один вузол", "Клемник або WAGO знизу: один світлодіод відмовив — "
                                       "міняється окремо, без розпаювання всієї групи."),
        ("Свій запобіжник", "Уся група бере копійки: 6 × 10 мА = 60 мА, менше вата. "
                            "Запобіжник 1 А на групу — цього досить."),
    ]
    for i, (h1, body) in enumerate(tips):
        y = ty + 28 + i * 62
        o.append(t(sx, y, "· " + h1, 11.5, INK, "start", "700"))
        words, line, lines = body.split(), "", []
        for w in words:
            if len(line) + len(w) > 52:
                lines.append(line); line = w
            else:
                line = (line + " " + w).strip()
        lines.append(line)
        for j, ln in enumerate(lines[:3]):
            o.append(t(sx + 10, y + 16 + j * 14, ln, 10.5, DIM))

    o.append(t(40, H - 34, "Варіант, якщо резисторів шкода: два світлодіоди ПОСЛІДОВНО на пару "
                           "(пояс окремо, шолом окремо) — тоді 750 Ом на 10 мА, удвічі менше "
                           "резисторів і тепла.", 11, ORANGE))

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
            f'<rect width="{W}" height="{H}" fill="#ffffff"/>\n' + "\n".join(o) + "\n</svg>\n")


def demo() -> int:
    rows = calc_rows()
    y10 = [r for r in rows if r[0] == "жовтий" and abs(r[1] - 0.010) < 1e-9][0]
    assert y10[3] == 1000, y10          # (12−2.1)/0.01 = 990 → 1 кОм
    w20 = [r for r in rows if r[0].startswith("білий") and abs(r[1] - 0.020) < 1e-9][0]
    assert w20[3] == 470, w20           # (12−3)/0.02 = 450 → 470 Ом
    assert all(r[4] < 0.5 for r in rows), "усе має влазити в резистор 1/2 Вт"
    assert "<svg" in build() and "750 Ом" in build()
    print("demo ok — номінали рахуються, усе в межах 1/2 Вт")
    return 0


if __name__ == "__main__":
    import sys
    if "--demo" in sys.argv:
        sys.exit(demo())
    out = HERE / "body_leds_solder.svg"
    out.write_text(build(), encoding="utf-8")
    print(f"готово: {out}")
