#!/usr/bin/env python3
"""
Розводка ламп на корпусі робота: паралельно від клемного вузла, не шлейфом.

Навіщо ця схема
─────────────────
На кресленні конструктора провід до ламп намальований однією зеленою ниткою,
яка обходить фігуру знизу вгору. Читається як послідовне зʼєднання — і саме так
її прочитав Марсель 07.08.2026: «In this schematics the wire looks like being run
in series. If so, we need to run it in parallel». Зелена лінія на кресленні — це
ТРАСА кабелю (де він фізично лежить у решітці корпусу), а не електрична схема.
Ця схема показує електрику: магістральна пара заходить у корпус, сідає на клемний
вузол, і кожна лампа висить на вузлі своєю парою — паралельно.

Що показує
────────────
  Коробка Гр.2 (WLED)
    → магістраль 18/2 AWG усередину костюма  (awg / довжина / струм / просадка — з моделі)
      → клемний вузол Wago 221 у гелевому боксі: шина «+12 В» і шина «−»
        → своя пара до кожної лампи: шолом ×4, плечі ×2, груди, коліно, стопа (Ø12 мм)
        → передпліччя ×2 (Ø8 мм)

Звідки числа
──────────────
  · lights/data/params.json      — bus_v, fixtures (кількість і Вт на лампу), install-правило Wago
  · lights/data/back_core.json   — figure.lamp_spots (де саме сидять лампи на фігурі)
  · lights_node_model.cable_tree — відрізок drop_robot (AWG, довжина, струм, просадка)
Жодної захардкодженої цифри тут нема.

Тільки stdlib — CI будує сайт без pip-пакетів.
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lights_node_model as lnm  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
P = json.loads((DATA / "params.json").read_text())
BC = json.loads((DATA / "back_core.json").read_text())

BUS_V = P["bus_v"]
FIX = {f["id"]: f for f in P["fixtures"]}
LED12 = FIX["led12"]
LED8 = FIX["led8"]
SPOTS = BC["figure"]["lamp_spots"]
LAMP_D = BC["figure"]["lamp_d_mm"]

TREE = {r["id"]: r for r in lnm.cable_tree()}
DROP = TREE["drop_robot"]          # Коробка → лампи робота
FUSE = {f["id"]: f["rating"] for f in lnm.fuses()}

# правило зʼєднань — з бази, не з голови
WAGO = next((i for i in P["spots"]["install"] if "Wago" in i["rule"]), None) \
    if isinstance(P.get("spots"), dict) and P["spots"].get("install") else None
if WAGO is None:
    for blk in P.values():
        if isinstance(blk, dict) and isinstance(blk.get("install"), list):
            WAGO = next((i for i in blk["install"] if "Wago" in i.get("rule", "")), None)
            if WAGO:
                break

# ── палітра (спільна з panel_tree.py / podium_plan.py) ──────────────────────
INK = "#24231d"
TXT2 = "#6b675c"
THIN = "#d8d5c9"
GHOST = "#c9c6ba"
ACC = "#b35b1e"          # плюсова пара
NEG = "#4a4a44"          # мінусова пара
G2 = "#3d6f96"           # група декору
G3 = "#3d7a4f"           # ок / добре
PASSIVE = "#b23a2e"      # так НЕ робимо
BOX_BG = "#f5f4ef"
PANEL_BG = "#efeee7"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"

W, H = 1180, 1060

# геометрія: верхня половина — сама розводка, нижня — дві врізки і підвал
BOX_X, BOX_Y = 40, 150           # коробка Гр.2
BOX_W, BOX_H = 170, 92
HUB_X = 330                      # клемний вузол
HUB_Y = 130
HUB_W, HUB_H = 220, 160
PLUS_Y = HUB_Y + 66              # рівень шини «+»
MINUS_Y = HUB_Y + 122            # рівень шини «−»
LAMP_X = 760                     # колонка ламп
LAMP_W = 380
ROW_TOP = 348
ROW_STEP = 60


def _t(x, y, text, size=11, fill=TXT2, anchor="start", weight=None, italic=False):
    extra = ""
    if weight:
        extra += f' font-weight="{weight}"'
    if italic:
        extra += ' font-style="italic"'
    return (f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" '
            f'font-size="{size}" fill="{fill}"{extra}>{text}</text>')


def _rect(x, y, w, h, fill=BOX_BG, stroke=INK, rx=3, sw=1.5, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" '
            f'rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')


def _line(x1, y1, x2, y2, stroke=ACC, sw=2.0, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}/>')


def _path(pts, stroke=ACC, sw=2.0, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    body = " ".join(f"{'M' if i == 0 else 'L'}{x:.0f},{y:.0f}"
                    for i, (x, y) in enumerate(pts))
    return f'<path d="{body}" fill="none" stroke="{stroke}" stroke-width="{sw}"{d}/>'


def _dot(x, y, r=4, fill=ACC):
    return f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{fill}"/>'


def lamp_rows():
    """Рядки схеми: по одному на місце встановлення, з кількістю ламп."""
    rows = []
    for sp in SPOTS:
        fx = FIX[sp["fixture"]]
        n = len(sp["x"])
        rows.append({
            "place": sp["place"],
            "fixture": sp["fixture"],
            "n": n,
            "d_mm": LAMP_D[sp["fixture"]],
            "w_unit": fx["w_unit"],
            "hidden": bool(sp.get("hidden")),
            "assumed": bool(sp.get("assumed")),
        })
    return rows


def svg():
    rows = lamp_rows()
    n_total = sum(r["n"] for r in rows)
    declared = LED12["qty"] + LED8["qty"]
    w_total = sum(r["n"] * r["w_unit"] for r in rows)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'width="100%" font-family="{FONT}">']

    # ── шапка ───────────────────────────────────────────────────────────
    o.append(_t(W // 2, 30, "Лампи на корпусі робота — кожна своєю парою від клемного вузла",
                15, INK, "middle", weight="bold"))
    o.append(_t(W // 2, 52,
                f'шина {BUS_V:.0f} В · група Гр.2 (декор) · {LED12["qty"]}× Ø{LAMP_D["led12"]} мм '
                f'+ {LED8["qty"]}× Ø{LAMP_D["led8"]} мм · {LED12["w_unit"]} Вт на лампу · '
                f'разом {w_total:.1f} Вт',
                11, TXT2, "middle"))
    o.append(_t(W // 2, 72,
                "Паралельно: згасла одна лампа — решта світять. Послідовно (ланцюжком) ми не робимо.",
                11, G3, "middle", weight="bold"))

    # ── коробка Гр.2 ────────────────────────────────────────────────────
    o.append(_rect(BOX_X, BOX_Y, BOX_W, BOX_H, fill=PANEL_BG, stroke=G2, sw=1.8, rx=5))
    o.append(_t(BOX_X + BOX_W // 2, BOX_Y + 26, "Коробка Гр.2", 12, INK, "middle", weight="bold"))
    o.append(_t(BOX_X + BOX_W // 2, BOX_Y + 44, "контролер WLED", 10, TXT2, "middle"))
    o.append(_t(BOX_X + BOX_W // 2, BOX_Y + 60, f'запобіжник {FUSE["g2"]:g} А', 10, G2, "middle"))
    o.append(_t(BOX_X + BOX_W // 2, BOX_Y + 76, "у гермокоробці IP65", 9, TXT2, "middle"))

    # ── магістраль у корпус: пара розходиться на дві шини ───────────────
    y_mid = BOX_Y + BOX_H // 2
    o.append(_path([(BOX_X + BOX_W, y_mid - 7), (HUB_X - 45, y_mid - 7),
                    (HUB_X - 45, PLUS_Y), (HUB_X + 16, PLUS_Y)], ACC, 2.6))
    o.append(_path([(BOX_X + BOX_W, y_mid + 7), (HUB_X - 28, y_mid + 7),
                    (HUB_X - 28, MINUS_Y), (HUB_X + 16, MINUS_Y)], NEG, 2.6))
    est = " ~" if DROP.get("estimate") else ""
    cy = BOX_Y + BOX_H + 44
    o.append(_t(BOX_X, cy, "Магістральна пара в корпус", 11, INK, "start", weight="bold"))
    o.append(_t(BOX_X, cy + 18, f'{DROP["cable"]}', 10, TXT2, "start"))
    o.append(_t(BOX_X, cy + 34, f'AWG{DROP["awg"]} · {DROP["length_m"]:.1f} м{est} · '
                                f'{DROP["amps"]:.2f} А · просадка −{DROP["drop_pct"]:.1f}%',
                10, TXT2, "start"))
    o.append(_t(BOX_X, cy + 52, "іде всередині решітки корпусу, не по поверхні",
                10, TXT2, "start"))

    # ── клемний вузол ───────────────────────────────────────────────────
    o.append(_rect(HUB_X, HUB_Y, HUB_W, HUB_H, fill=BOX_BG, stroke=INK, sw=1.8, rx=5))
    o.append(_t(HUB_X + HUB_W // 2, HUB_Y + 24, "Клемний вузол", 12, INK, "middle", weight="bold"))
    o.append(_t(HUB_X + HUB_W // 2, HUB_Y + 40, "Wago 221 у гелевому боксі", 9, TXT2, "middle"))

    # шини + і −
    for y, lbl, col in ((PLUS_Y, f'+{BUS_V:.0f} В', ACC), (MINUS_Y, "−  (спільний)", NEG)):
        o.append(_rect(HUB_X + 16, y - 11, HUB_W - 32, 22, fill="#fff", stroke=col, sw=1.6, rx=3))
        o.append(_t(HUB_X + HUB_W // 2, y + 4, lbl, 10, col, "middle", weight="bold"))

    o.append(_t(HUB_X + HUB_W // 2, HUB_Y + HUB_H + 18,
                "усередині фігури, у грудях", 9, TXT2, "middle"))

    # ── вертикальні стояки від шин до рівня ламп ────────────────────────
    riser_p = HUB_X + HUB_W + 40
    riser_n = HUB_X + HUB_W + 66
    bottom = ROW_TOP + (len(rows) - 1) * ROW_STEP
    o.append(_path([(HUB_X + HUB_W, PLUS_Y), (riser_p, PLUS_Y), (riser_p, bottom)], ACC, 2.6))
    o.append(_path([(HUB_X + HUB_W, MINUS_Y), (riser_n, MINUS_Y), (riser_n, bottom)], NEG, 2.6))

    # ── ряди ламп ───────────────────────────────────────────────────────
    for i, r in enumerate(rows):
        y = ROW_TOP + i * ROW_STEP
        dash = "5,4" if (r["hidden"] or r["assumed"]) else ""
        o.append(_dot(riser_p, y, 4, ACC))
        o.append(_dot(riser_n, y + 14, 4, NEG))
        o.append(_line(riser_p, y, LAMP_X, y, ACC, 1.8, dash))
        o.append(_line(riser_n, y + 14, LAMP_X, y + 14, NEG, 1.8, dash))
        # сама лампа
        o.append(_rect(LAMP_X, y - 12, LAMP_W, 40, fill=BOX_BG, stroke=INK, sw=1.4, rx=4,
                       dash=dash))
        cap = f'{r["place"]} · {r["n"]}× Ø{r["d_mm"]} мм'
        o.append(_t(LAMP_X + 14, y + 4, cap, 11, INK, "start", weight="bold"))
        sub = f'{r["n"] * r["w_unit"]:.1f} Вт'
        if r["hidden"]:
            sub += " · з іншого боку фігури"
        if r["assumed"]:
            sub += " · місце ще уточнюємо"
        o.append(_t(LAMP_X + 14, y + 20, sub, 9, TXT2, "start"))

    # підпис колонки
    o.append(_t(LAMP_X, ROW_TOP - 40, "Кожна лампа — своя пара до шин", 11, INK,
                "start", weight="bold"))
    o.append(_t(LAMP_X, ROW_TOP - 24,
                "перегоріла лампа рве тільки свою пару, шина живе", 9, TXT2, "start"))

    # ── врізка: послідовно vs паралельно ────────────────────────────────
    box_top = max(bottom + 70, 700)
    ix, iy, iw, ih = 40, box_top, 545, 210
    o.append(_rect(ix, iy, iw, ih, fill="#fff", stroke=THIN, sw=1.2, rx=6))
    o.append(_t(ix + 18, iy + 26, "Чому не послідовно", 12, INK, "start", weight="bold"))

    o.append(_t(ix + 18, iy + 50, "Послідовно (ланцюжком):", 11, PASSIVE, "start", weight="bold"))
    o.append(_t(ix + 18, iy + 68,
                "струм тече крізь кожну лампу по черзі. Обрив у будь-якій —", 10, TXT2, "start"))
    o.append(_t(ix + 18, iy + 84,
                "і гасне вся лінія. Так ми не робимо.", 10, TXT2, "start"))

    o.append(_t(ix + 18, iy + 110, "Паралельно (наш варіант):", 11, G3, "start", weight="bold"))
    o.append(_t(ix + 18, iy + 128,
                f'на кожній лампі повні {BUS_V:.0f} В — усі сидять на тих самих двох шинах.',
                10, TXT2, "start"))
    o.append(_t(ix + 18, iy + 144, "Згасла одна — решта не помічають.", 10, TXT2, "start"))

    o.append(_t(ix + 18, iy + 170, "Що таки може погасити все:", 11, INK, "start", weight="bold"))
    o.append(_t(ix + 18, iy + 188,
                "обрив магістральної пари до вузла або запобіжник групи.", 10, TXT2, "start"))

    # ── врізка: зʼєднання ───────────────────────────────────────────────
    jx, jy, jw, jh = 615, box_top, 525, 210
    o.append(_rect(jx, jy, jw, jh, fill=PANEL_BG, stroke=THIN, sw=1.2, rx=6))
    o.append(_t(jx + 18, jy + 26, "Чим саме зʼєднуємо", 12, INK, "start", weight="bold"))
    rule = (WAGO or {}).get("rule", "Wago 221 у гелевому боксі")
    o.append(_t(jx + 18, jy + 50, "Важільні клеми Wago 221 у гелевому боксі,", 10, TXT2, "start"))
    o.append(_t(jx + 18, jy + 66, "або гелеві ковпачки на кінцях.", 10, TXT2, "start"))
    o.append(_t(jx + 18, jy + 92,
                "Важіль відкривається без інструмента — лампу знімають", 10, TXT2, "start"))
    o.append(_t(jx + 18, jy + 108,
                "і повертають прямо на плайї. Гель тримає пил 1–10 мкм", 10, TXT2, "start"))
    o.append(_t(jx + 18, jy + 124,
                "і нічний конденсат. Скрутка й ізолента — ні.", 10, TXT2, "start"))
    o.append(_t(jx + 18, jy + 150,
                "Магістраль іде всередині решітки корпусу, не по поверхні.",
                10, TXT2, "start"))
    o.append(_t(jx + 18, jy + 176,
                "Скільки клем: стільки пар, скільки ламп на вузлі.", 10, TXT2, "start"))

    # ── підвал ──────────────────────────────────────────────────────────
    foot_y = box_top + ih + 46
    o.append(_line(40, foot_y - 18, W - 40, foot_y - 18, THIN, 1.0))
    o.append(_t(40, foot_y,
                f'Місць на схемі {n_total}, у специфікації {declared} ламп — '
                f'розбіжність усередині бази, показуємо як є, а не ховаємо.',
                10, TXT2, "start"))
    o.append(_t(40, foot_y + 18,
                "Пунктиром — те, що ще не підтверджене: лампа на грудях видна лише спереду, "
                "місце двох Ø8 мм уточнюємо з конструктором.", 10, TXT2, "start"))
    o.append(_t(40, foot_y + 36,
                f'Довжина магістралі {DROP["length_m"]:.1f} м — прикидка, з креслення не знята. '
                f'Стрічка подіуму живиться так само паралельно, але має свої точки живлення '
                f'(power injection) — окрема схема.',
                10, TXT2, "start"))

    o.append("</svg>")
    return "\n".join(o)


def verify_svg(text):
    """SVG парситься, має ненульовий viewBox і всі місця ламп підписані."""
    root = ET.fromstring(text)
    vb = root.get("viewBox", "")
    if not vb:
        raise ValueError("SVG не має viewBox")
    parts = vb.split()
    if float(parts[2]) <= 0 or float(parts[3]) <= 0:
        raise ValueError(f"viewBox має нульовий розмір: {vb}")

    texts = " ".join(el.text or "" for el in
                     root.iter("{http://www.w3.org/2000/svg}text"))
    for r in lamp_rows():
        if r["place"] not in texts:
            raise ValueError(f"на схемі нема місця «{r['place']}»")
    for must in ("Паралельно", "Wago"):
        if must not in texts:
            raise ValueError(f"на схемі нема ключового підпису «{must}»")
    return True


def main():
    content = svg()
    verify_svg(content)
    out = Path(__file__).resolve().parent / "body_wiring.svg"
    out.write_text(content, encoding="utf-8")
    print(f"SVG записано: {out}  ({len(content.encode('utf-8')) / 1024:.1f} KB)")

    rows = lamp_rows()
    print(f"\nМагістраль у корпус: AWG{DROP['awg']} {DROP['length_m']} м "
          f"{DROP['amps']:.2f} А −{DROP['drop_pct']:.1f}%")
    for r in rows:
        print(f"  {r['place']:<14} {r['n']}× Ø{r['d_mm']} мм  {r['n'] * r['w_unit']:.1f} Вт")
    print(f"  разом місць: {sum(r['n'] for r in rows)} "
          f"(у специфікації {LED12['qty'] + LED8['qty']})")


if __name__ == "__main__":
    main()
