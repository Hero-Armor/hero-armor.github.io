#!/usr/bin/env python3
"""Ящик під станцію і генератор — З ЧОГО і В ЯКОМУ ПОРЯДКУ його будувати.

`genbox_plan.py` показує, ЩО ми будуємо (план, розріз, потоки повітря). Цей файл
відповідає на інші три питання, які виникають уже з ножівкою в руках:

  genbox_cut.svg      — деталі з розмірами і як вони лягають на аркуші фанери 4×8
  genbox_steps.svg    — порядок збірки: що за чим, щоб не довелось розбирати
  genbox_exhaust.svg  — два вузли, які вирішують усе: прохід вихлопу і вхід повітря

Розкрій рахується, а не малюється на око: наївна поличкова укладка (shelf packing)
кладе деталі на аркуш 1220×2440 і сама каже, скільки аркушів треба. Тому якщо
змінити габарит ящика в genbox.json, картинка перерахується, а не збреше.

  python3 enclosure/model/genbox_build.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = json.loads((HERE.parent / "data/genbox.json").read_text(encoding="utf-8"))

INNER = D["size_estimate"]["inner_mm"]          # 1400 × 520 × 620
T = 15                                          # товщина фанери, мм
SHEET = (1220, 2440)                            # аркуш 4×8 футів
PLY_KG_M2 = 9.5                                 # береза 15 мм
GEN = D["units"]["generator"]
STA = D["units"]["station"]

INK, DIM, GREY = "#1b1b1b", "#555", "#a0a0a0"
RED, BLUE, GREEN, ORANGE = "#d81f1f", "#1f4fd8", "#0b8a3e", "#c2660a"


def parts() -> list[tuple[str, int, int, int]]:
    """Назва, ширина, висота, кількість. Стик простий: торці між довгими стінками."""
    L, W, H = INNER[0] + 2 * T, INNER[1] + 2 * T, INNER[2]
    return [
        ("дно", L, W, 1),
        ("кришка", L, W, 1),
        ("стінка довга", L, H + T, 2),
        ("торець", INNER[1], H, 2),
        ("перегородка", INNER[1], H, 2),
    ]


def pack(items: list[tuple[str, int, int]]) -> list[list[dict]]:
    """Поличкова укладка з приміркою до ВСІХ уже відкритих аркушів.

    Деталь спершу кладемо довгим боком уздовж аркуша, далі шукаємо їй місце: спочатку
    в незакритій полиці, потім новою полицею, і тільки якщо не влізло в жоден аркуш —
    беремо наступний. Примірка до попередніх аркушів принципова: без неї дрібні деталі
    йдуть на новий лист, поки на першому лишається метр порожнечі, і розкрій бреше на
    цілий аркуш ($90 за березу).

    ponytail: guillotine-розкрій під ЧПУ не рахуємо — задача картинки сказати «трьох
    аркушів вистачить», а не видати керуючу програму.
    """
    sheets: list[dict] = []                      # {"parts": [...], "shelves": [{y,h,x}]}
    for name, w, h in sorted(items, key=lambda i: -max(i[1], i[2])):
        if w > h:                                # довгим боком уздовж аркуша
            w, h = h, w
        assert w <= SHEET[0] and h <= SHEET[1], f"деталь {name} більша за аркуш"
        for s in sheets + [None]:
            if s is None:                        # усі аркуші зайняті — беремо новий
                s = {"parts": [], "shelves": []}
                sheets.append(s)
            spot = None
            for sh in s["shelves"]:              # у відкриту полицю
                if sh["x"] + w <= SHEET[0] and h <= sh["h"]:
                    spot = (sh["x"], sh["y"], sh)
                    break
            if spot is None:                     # новою полицею
                top = sum(sh["h"] for sh in s["shelves"])
                if top + h <= SHEET[1]:
                    sh = {"y": top, "h": h, "x": 0}
                    s["shelves"].append(sh)
                    spot = (0, top, sh)
            if spot:
                x, y, sh = spot
                s["parts"].append({"name": name, "x": x, "y": y, "w": w, "h": h})
                sh["x"] = x + w
                break
    return [s["parts"] for s in sheets]


def t(x, y, s, size=11, fill=INK, anchor="start", weight="400", rot=None):
    s = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    r = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial,Helvetica,sans-serif" '
            f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}"{r}>{s}</text>')


def rect(x, y, w, h, fill="#f4f6fb", stroke=GREY, lw=1.3, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{lw}"{d}/>')


def wrap(s: str, n: int) -> list[str]:
    out, line = [], ""
    for w in s.split():
        if len(line) + len(w) > n:
            out.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    out.append(line)
    return out


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
            f'<defs><marker id="ar" markerWidth="10" markerHeight="10" refX="6" refY="5" orient="auto">'
            f'<path d="M1,1 L9,5 L1,9 z" fill="{RED}"/></marker>'
            f'<marker id="ab" markerWidth="10" markerHeight="10" refX="6" refY="5" orient="auto">'
            f'<path d="M1,1 L9,5 L1,9 z" fill="{BLUE}"/></marker></defs>\n'
            f'<rect width="{w}" height="{h}" fill="#ffffff"/>\n' + body + "\n</svg>\n")


# ─────────────────────────────────────────────────────────────── розкрій
def cut() -> str:
    flat = [(n, w, h) for n, w, h, q in parts() for _ in range(q)]
    sheets = pack(flat)
    area = sum(w * h for _, w, h in flat) / 1e6
    kg = area * PLY_KG_M2

    o = [t(40, 34, "Розкрій: із чого пиляємо ящик", 19, INK, "start", "700"),
         t(40, 56, f"Аркуш фанери 4×8 футів = {SHEET[0]}×{SHEET[1]} мм, товщина {T} мм. "
                   f"Деталей {len(flat)}, площа {area:.2f} м², аркушів треба {len(sheets)}.", 11, DIM)]

    # список деталей
    o.append(t(40, 92, "ДЕТАЛІ", 13, INK, "start", "700"))
    for i, (n, w, h, q) in enumerate(parts()):
        y = 114 + i * 22
        o.append(t(40, y, f"{q} × {n}", 11.5, INK, "start", "600"))
        o.append(t(200, y, f"{w} × {h} мм", 11.5, DIM))
    o.append(t(40, 114 + len(parts()) * 22 + 8,
               f"вага самої фанери ≈ {kg:.0f} кг", 11.5, RED, "start", "700"))

    # аркуші
    S = 0.135
    ox = 380
    for si, sh in enumerate(sheets):
        x0 = ox + si * (SHEET[0] * S + 60)
        o.append(t(x0, 92, f"АРКУШ {si + 1}", 13, INK, "start", "700"))
        o.append(rect(x0, 104, SHEET[0] * S, SHEET[1] * S, "#fcfcfc", INK, 1.8))
        for p in sh:
            px, py = x0 + p["x"] * S, 104 + p["y"] * S
            pw, ph = p["w"] * S, p["h"] * S
            o.append(rect(px, py, pw, ph, "#eef3ff", "#7f9ee0", 1.1))
            o.append(t(px + pw / 2, py + ph / 2 - 2, p["name"], 9.5, INK, "middle", "600"))
            o.append(t(px + pw / 2, py + ph / 2 + 11, f'{p["w"]}×{p["h"]}', 8.5, DIM, "middle"))
        o.append(t(x0, 104 + SHEET[1] * S + 18, "сірим — залишок, з нього ідуть косинці",
                   9.5, GREY))

    # попередження про вагу
    wx, wy = 40, 330
    o.append(t(wx, wy, "ВАГА — ГОЛОВНА ПАСТКА ЦІЄЇ КОНСТРУКЦІЇ", 13, RED, "start", "700"))
    total = kg + GEN["weight_kg"] + STA["weight_kg"]
    for i, ln in enumerate([
            f"фанера {kg:.0f} кг + генератор {GEN['weight_kg']} кг + станція {STA['weight_kg']} кг = "
            f"{total:.0f} кг",
            "стільки вдвох не піднімають і в кузов не подають. Три виходи:",
            "· колеса і ручка — ящик не носять, його котять;",
            "· кришка знімна, залізо виймається окремо — тоді носять 44 кг порожнього;",
            "· два ящики поруч, зчеплені болтами — кожен несуть окремо.",
            "12-мм фанера замість 15-мм знімає близько 9 кг і цього достатньо для стінок,",
            "але дно лишаємо 15 — на ньому стоїть уся вага."]):
        o.append(t(wx, wy + 22 + i * 19, ln, 11, INK if i < 2 else DIM))

    return svg(1240, 470 + 0, "\n".join(o))


# ─────────────────────────────────────────────────────────────── порядок
def steps() -> str:
    S = [("Дно і торці", "Спочатку рама: дно, два торці, кути на косинцях зсередини. "
                         "Поки нема довгих стінок — усе доступно з обох боків."),
         ("Перегородка", "Ставимо ДО довгих стінок: вата 50 мм між двома листами, "
                         "фольга на бік генератора, зазор 20 мм. Потім її туди не заведеш."),
         ("Прохід вихлопу", "Гільзу в торець ріжемо зараз, поки деталь лежить на столі. "
                            "Свердлити зібраний ящик — це стружка всередину і кривий отвір."),
         ("Вентиляція", "Станційний бік: отвір під фільтр і вентилятор на нагнітання. "
                        "Генераторний: великий вхід унизу і витяжка вгорі. Отвори теж по деталях."),
         ("Довгі стінки", "Закриваємо коробку. З цього моменту всередину лізе тільки рука."),
         ("Кришка на петлях", "Петлі, засувки, ручка. Кришка знімна або на петлях — "
                              "але залізо мусить виніматись без розбирання ящика."),
         ("Обшивка ватою", "Вата під перфорованим алюмінієм по стінках генераторного "
                           "відсіку. Волокно не має літати всередині."),
         ("Приміряти залізо", "Ставимо генератор і станцію ДО фарбування. Не влізло — "
                              "правити ще можна.")]
    o = [t(40, 34, "Порядок збірки — що за чим", 19, INK, "start", "700"),
         t(40, 56, "Порядок не косметичний: половину операцій фізично неможливо зробити після "
                   "того, як коробка закрита.", 11, DIM)]
    for i, (h1, body) in enumerate(S):
        col, row = i // 4, i % 4
        x, y = 40 + col * 600, 92 + row * 118
        o.append(rect(x, y, 560, 100, "#fbfcff", "#d5ddee", 1.2))
        o.append(f'<circle cx="{x + 28}" cy="{y + 32}" r="17" fill="{BLUE}"/>')
        o.append(t(x + 28, y + 37, str(i + 1), 16, "#fff", "middle", "700"))
        o.append(t(x + 58, y + 30, h1, 13, INK, "start", "700"))
        for j, ln in enumerate(wrap(body, 62)):
            o.append(t(x + 58, y + 52 + j * 16, ln, 10.8, DIM))
    o.append(t(40, 92 + 4 * 118 + 14, "Правило всієї збірки: кожен отвір і кожен виріз робиться "
                                      "по деталі, що лежить на столі. Все, що робиться в зібраному "
                                      "ящику, робиться погано.", 11.5, RED, "start", "600"))
    return svg(1240, 92 + 4 * 118 + 40, "\n".join(o))


# ─────────────────────────────────────────────── вузли: вихлоп і повітря
def nodes() -> str:
    o = [t(40, 34, "Два вузли, на яких усе тримається", 19, INK, "start", "700"),
         t(40, 56, "Решта ящика — це коробка. Ці два місця вирішують, буде він працювати чи "
                   "згорить.", 11, DIM)]

    # ── вихлоп ──────────────────────────────────────────────────────
    ox, oy = 60, 100
    o.append(t(ox, oy, "1 · ПРОХІД ВИХЛОПУ КРІЗЬ СТІНКУ", 13, RED, "start", "700"))
    wx, wy, wt, wh = ox + 190, oy + 40, 22, 250
    o.append(rect(wx, wy, wt, wh, "#e8dcc4", "#b09a70", 1.4))       # фанера в розрізі
    o.append(t(wx + 11, wy - 10, "фанера 15 мм", 10, DIM, "middle"))
    # гільза
    gy, gh = wy + 95, 60
    o.append(rect(wx - 6, gy, wt + 12, gh, "#dfe4ea", "#7a828c", 1.6))
    o.append(t(wx + 60, gy - 6, "металева гільза — ширша за трубу", 10.5, INK, "start", "600"))
    # труба
    py, ph = gy + 18, 24
    o.append(rect(wx - 120, py, 240, ph, "#c9ccd1", "#5c6169", 1.4))
    o.append(t(wx - 118, py + 16, "гофра нержавійка", 10, INK))
    # зазор
    o.append(f'<line x1="{wx + 26}" y1="{gy}" x2="{wx + 26}" y2="{py}" stroke="{RED}" stroke-width="1.4"/>')
    o.append(t(wx + 32, py - 4, "зазор ≥20 мм, не забивати ватою щільно", 10, RED, "start", "700"))
    # козирок і вихід донизу
    o.append(f'<path d="M{wx + 120},{py + ph} q30,10 30,50" fill="none" stroke="#5c6169" stroke-width="8"/>')
    o.append(t(wx + 156, py + 66, "вихід ДОНИЗУ", 10.5, INK, "start", "700"))
    o.append(t(wx + 156, py + 82, "пил і вода не залітають", 10, DIM))
    rules = ["фанера впритул до труби — це відкритий вогонь, тому гільза",
             "гільзу садити на термостійкий герметик, не на силікон",
             "з вулиці — сітка від іскри, з середини — нічого горючого в радіусі 100 мм",
             "датчик чадного газу: один у ящику, другий там, де спимо"]
    for i, ln in enumerate(rules):
        o.append(t(ox, oy + 320 + i * 18, "· " + ln, 10.8, INK if i < 2 else DIM))

    # ── вхід повітря ────────────────────────────────────────────────
    ax = 780
    o.append(t(ax, oy, "2 · ВХІД ПОВІТРЯ В СТАНЦІЙНИЙ ВІДСІК", 13, BLUE, "start", "700"))
    wt2, wy2, wh2 = 22, oy + 40, 250
    o.append(rect(ax, wy2, wt2, wh2, "#e8dcc4", "#b09a70", 1.4))
    o.append(t(ax + 11, wy2 - 10, "фанера", 10, DIM, "middle"))
    mid = wy2 + 130
    # потік: зовні → вентилятор → поролон → стінка → MERV → відсік
    o.append(f'<line x1="{ax - 230}" y1="{mid}" x2="{ax - 170}" y2="{mid}" '
             f'stroke="{BLUE}" stroke-width="3" marker-end="url(#ab)"/>')
    o.append(t(ax - 232, mid - 14, "з вулиці", 10.5, BLUE, "start", "700"))
    o.append(f'<circle cx="{ax - 140}" cy="{mid}" r="26" fill="#eef3ff" stroke="{BLUE}" stroke-width="1.6"/>')
    o.append(f'<path d="M{ax-158},{mid} q18,-16 18,0 q18,16 18,0" fill="none" stroke="{BLUE}" stroke-width="2.4"/>')
    o.append(f'<path d="M{ax-158},{mid+11} q18,-16 18,0 q18,16 18,0" fill="none" stroke="{BLUE}" stroke-width="2.4"/>')
    o.append(t(ax - 166, mid + 48, "вентилятор", 10.5, INK, "start", "600"))
    o.append(t(ax - 176, mid + 64, "дме ВСЕРЕДИНУ", 10, BLUE, "start", "700"))
    o.append(rect(ax - 92, mid - 45, 26, 90, "#eef3ff", "#7f9ee0", 1.4))
    o.append(t(ax - 79, mid - 56, "поролон", 10.5, INK, "middle", "600"))
    o.append(t(ax - 79, mid + 92, "пісок,", 10, DIM, "middle"))
    o.append(t(ax - 79, mid + 106, "миється", 10, DIM, "middle"))
    o.append(f'<line x1="{ax - 60}" y1="{mid}" x2="{ax - 4}" y2="{mid}" '
             f'stroke="{BLUE}" stroke-width="3" marker-end="url(#ab)"/>')
    o.append(rect(ax + 30, mid - 45, 26, 90, "#eef3ff", "#7f9ee0", 1.4))
    o.append(t(ax + 43, mid - 56, "MERV 13", 10.5, INK, "middle", "600"))
    o.append(t(ax + 68, mid + 62, "луговий пил pH 9-10 до плат не доходить", 10, DIM, "middle"))
    o.append(f'<line x1="{ax + 62}" y1="{mid}" x2="{ax + 130}" y2="{mid}" '
             f'stroke="{BLUE}" stroke-width="3" marker-end="url(#ab)"/>')
    o.append(t(ax + 136, mid - 6, "відсік станції", 10.5, INK, "start", "700"))
    o.append(t(ax + 136, mid + 10, "тиск на 20-50 Па вищий", 10.5, GREEN, "start", "700"))
    o.append(t(ax + 136, mid + 26, "за вулицю — витік іде", 10, DIM, "start"))
    o.append(t(ax + 136, mid + 40, "назовні, а не всередину", 10, DIM, "start"))
    keep = ["Це рішення DEC-087 і DEC-088, ухвалене ще під окремий ящик станції.",
            "Воно НЕ померло разом із гіпотезою кулера: пил на плайї нікуди не дівся,",
            "а генераторний відсік однаково продувається наскрізь.",
            "Різниця одна: фільтр тепер потрібен лише станційному боку, бо генератору",
            "фільтрувати повітря на горіння ми не будемо — у нього свій фільтр."]
    for i, ln in enumerate(keep):
        o.append(t(ax, oy + 320 + i * 18, ln, 10.8, INK if i < 3 else DIM))

    return svg(1420, 540, "\n".join(o))


def demo() -> int:
    flat = [(n, w, h) for n, w, h, q in parts() for _ in range(q)]
    sheets = pack(flat)
    placed = sum(len(s) for s in sheets)
    assert placed == len(flat), f"загубили деталі: {placed} з {len(flat)}"
    for sh in sheets:                       # нічого не вилазить за аркуш
        for p in sh:
            assert p["x"] + p["w"] <= SHEET[0] and p["y"] + p["h"] <= SHEET[1], p
    for sh in sheets:                       # і нічого не накладається
        for i, a in enumerate(sh):
            for b in sh[i + 1:]:
                over = (a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"]
                        and a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"])
                assert not over, (a, b)
    for fn in (cut, steps, nodes):
        s = fn()
        assert s.startswith("<svg") and s.count("<text") > 15, fn.__name__
    print(f"demo ok — {len(flat)} деталей на {len(sheets)} аркушах, три схеми будуються")
    return 0


if __name__ == "__main__":
    import sys
    if "--demo" in sys.argv:
        sys.exit(demo())
    for name, fn in (("genbox_cut", cut), ("genbox_steps", steps), ("genbox_exhaust", nodes)):
        (HERE / f"{name}.svg").write_text(fn(), encoding="utf-8")
        print(f"готово: {HERE / (name + '.svg')}")
