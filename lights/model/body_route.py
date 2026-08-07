#!/usr/bin/env python3
"""
План розводки ламп по тілу робота: де яка лампа і як до неї приходить дріт.

Навіщо
────────
Іван, 07.08.2026: «схем і планів підключення різних лампочок по тілу робота
зовсім нема — ні на старих схемах Володимира, ні на твоїх нових малюнках».
І це правда: креслення конструктора показує ТОЧКИ ламп на фігурі, а schema_kit-
схема `body_wiring.svg` — електрику (шини, паралельне підключення), але жодна
не каже, ЯКИМ ШЛЯХОМ дріт іде всередині костюма і скільки його треба.

Ця схема саме про це: силует фігури, точки ламп на своїх місцях і траса
магістралі — від настилу подіуму крізь ногу в корпус, до клемного вузла в
грудях, і далі гілками в шолом, плечі, передпліччя, коліно і стопу.

Звідки числа
──────────────
  · lights/data/back_core.json → figure: пропорції силуета і lamp_spots
    (де саме сидить кожна лампа — частки висоти фігури);
  · lights/data/params.json → fixtures led12 / led8: кількість і Вт;
  · lights_node_model.cable_tree → drop_robot: калібр і струм магістралі.

Довжини гілок ТУТ РАХУЮТЬСЯ ГЕОМЕТРИЧНО з пропорцій фігури (висота фігури над
настилом — з тієї ж бази), а не беруться з креслення. Це чесна прикидка, щоб
знати, скільки дроту купувати; на схемі це прямо підписано.

Малюється силует тими самими примітивами, що й `armor/model/robot_fixtures.py`
— щоб фігура на обох схемах була однією і тією ж, а не двома різними.

Тільки stdlib.
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "armor" / "model"))

import lights_node_model as lnm            # noqa: E402
import robot_fixtures as rf                # noqa: E402

P = json.loads((HERE.parent / "data" / "params.json").read_text())
BC = json.loads((HERE.parent / "data" / "back_core.json").read_text())
FIG = BC["figure"]
SPOTS = FIG["lamp_spots"]
LAMP_D = FIG["lamp_d_mm"]
FIX = {f["id"]: f for f in P["fixtures"]}
DROP = {r["id"]: r for r in lnm.cable_tree()}["drop_robot"]
FIG_H_M = rf.FIG_H_M                        # висота фігури над настилом, м

INK, TXT2, THIN = "#24231d", "#6b675c", "#d8d5c9"
POS, NEG, HUB = "#b35b1e", "#4a4a44", "#b35b1e"
GOOD = "#3d7a4f"
BODY, PLATE = "#efeee7", "#e8e4d6"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"

W, H = 1240, 1010
CX = 500                                    # вісь фігури на цьому аркуші
GROUND_Y = 850
FIG_PX = 640                                # висота фігури в пікселях

HUB_YF = 0.735                              # вузол — у грудях, на рівні лампи грудей
ENTRY_XF = 0.062                            # нога, крізь яку заходить кабель (як стопа)


def fy(yf):
    return GROUND_Y - yf * FIG_PX


def fx(xf):
    return CX + xf * FIG_PX


def m_per_px():
    return FIG_H_M / FIG_PX


def lamps():
    """Плаский список ламп: місце, тип, координати в частках."""
    out = []
    for sp in SPOTS:
        for x in sp["x"]:
            out.append({"place": sp["place"], "fixture": sp["fixture"],
                        "xf": x, "yf": sp["y"],
                        "d": LAMP_D[sp["fixture"]],
                        "w": FIX[sp["fixture"]]["w_unit"],
                        "soft": bool(sp.get("hidden") or sp.get("assumed"))})
    return out


def route_to(lamp, hub):
    """Траса від вузла до лампи так, як дріт реально піде всередині костюма.

    Не по діагоналі крізь порожнечу і не між ногами: спершу вздовж корпусу,
    далі вбік у ту кінцівку, де сидить лампа, і вже нею — до самої лампи.
    """
    hx, hy = hub
    xf, yf = lamp["xf"], lamp["yf"]
    hip, sh = FIG["hip_y"], FIG["shoulder_y"]
    leg_cx = (FIG["hip_w"] + FIG["leg_gap"]) / 2
    arm_cx = FIG["arm_x"]

    if yf < hip:                                   # нога: коліно, стопа
        side = 1 if xf >= 0 else -1
        return [(hx, hy), (hx, hip), (side * leg_cx, hip),
                (side * leg_cx, yf), (xf, yf)]
    if abs(xf) >= arm_cx - 0.02 and yf < sh:       # рука: передпліччя
        side = 1 if xf >= 0 else -1
        return [(hx, hy), (hx, sh), (side * arm_cx, sh), (side * arm_cx, yf), (xf, yf)]
    return [(hx, hy), (hx, yf), (xf, yf)]          # тулуб, плечі, шолом


def branch_len_m(pts):
    """Довжина ламаної в метрах — за пропорціями фігури."""
    total = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        total += (abs(x1 - x2) + abs(y1 - y2)) * FIG_H_M
    return total


def _t(x, y, s, size=10, fill=TXT2, anchor="start", weight=None):
    extra = f' font-weight="{weight}"' if weight else ""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" font-size="{size}" '
            f'fill="{fill}"{extra}>{s}</text>')


def _poly(pts, fill=BODY, stroke=INK, sw=1.4):
    d = " ".join(f'{"M" if i == 0 else "L"}{x:.1f},{y:.1f}' for i, (x, y) in enumerate(pts))
    return f'<path d="{d} Z" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def silhouette():
    """Силует фігури по тих самих пропорціях, що й схема броні: голова, тулуб,
    руки, ноги, стопи. Ключі — ті, що реально є в back_core.json → figure."""
    o = []
    sh, wa, hip = FIG["shoulder_y"], FIG["waist_y"], FIG["hip_y"]
    shw, ww, hpw = FIG["shoulder_w"], FIG["waist_w"], FIG["hip_w"]
    head_top = sh + FIG["head_h"]

    # голова
    o.append(f'<rect x="{fx(-FIG["head_w"]):.0f}" y="{fy(head_top):.0f}" '
             f'width="{2*FIG["head_w"]*FIG_PX:.0f}" '
             f'height="{(FIG["head_h"]-0.02)*FIG_PX:.0f}" rx="12" fill="{BODY}" '
             f'stroke="{INK}" stroke-width="1.4"/>')
    # шия
    o.append(f'<rect x="{fx(-FIG["neck_w"]):.0f}" y="{fy(sh+0.03):.0f}" '
             f'width="{2*FIG["neck_w"]*FIG_PX:.0f}" height="{0.03*FIG_PX:.0f}" '
             f'fill="{BODY}" stroke="{INK}" stroke-width="1.2"/>')
    # тулуб
    o.append(_poly([(fx(-shw), fy(sh)), (fx(shw), fy(sh)), (fx(ww), fy(wa)),
                    (fx(hpw), fy(hip)), (fx(-hpw), fy(hip)), (fx(-ww), fy(wa))]))
    # руки: вертикальні кінцівки від плеча до зап'ястя — саме на них сидять
    # лампи передпліч, тому руку треба малювати, а не позначати лінією
    for side in (-1, 1):
        ax = side * FIG["arm_x"]
        o.append(_poly([(fx(ax - FIG["arm_w"] / 2), fy(sh)),
                        (fx(ax + FIG["arm_w"] / 2), fy(sh)),
                        (fx(ax + FIG["wrist_w"] / 2), fy(FIG["wrist_y"])),
                        (fx(ax - FIG["wrist_w"] / 2), fy(FIG["wrist_y"]))]))
    # ноги і стопи
    for side in (-1, 1):
        cxf = side * (FIG["hip_w"] + FIG["leg_gap"]) / 2
        o.append(_poly([(fx(cxf - FIG["thigh_w"]), fy(hip)),
                        (fx(cxf + FIG["thigh_w"]), fy(hip)),
                        (fx(cxf + FIG["ankle_w"]), fy(FIG["ankle_y"])),
                        (fx(cxf - FIG["ankle_w"]), fy(FIG["ankle_y"]))]))
        o.append(f'<rect x="{fx(cxf - FIG["foot_w"]):.0f}" y="{fy(FIG["ankle_y"]):.0f}" '
                 f'width="{2*FIG["foot_w"]*FIG_PX:.0f}" height="{0.045*FIG_PX:.0f}" '
                 f'rx="3" fill="{PLATE}" stroke="{INK}" stroke-width="1.2"/>')
    # настил
    o.append(f'<rect x="{fx(-0.34):.0f}" y="{GROUND_Y:.0f}" width="{0.68*FIG_PX:.0f}" '
             f'height="12" fill="{PLATE}" stroke="{INK}" stroke-width="1.2"/>')
    return o


def svg():
    L = lamps()
    hub = (0.0, HUB_YF)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'width="100%" font-family="{FONT}">']
    o.append(_t(W // 2, 30, "Розводка ламп по тілу робота — куди йде кожен дріт",
                15, INK, "middle", "bold"))
    n12 = FIX["led12"]["qty"]
    n8 = FIX["led8"]["qty"]
    o.append(_t(W // 2, 52,
                f'{n12} ламп Ø{LAMP_D["led12"]} мм + {n8} лампи Ø{LAMP_D["led8"]} мм · '
                f'{FIX["led12"]["w_unit"]} Вт кожна · магістраль {DROP["cable"]}, '
                f'{DROP["amps"]:.2f} А', 11, TXT2, "middle"))
    o.append(_t(W // 2, 72,
                "Один кабель заходить крізь ногу, далі клемний вузол у грудях — "
                "і від нього своя пара до кожної лампи.", 11, GOOD, "middle", "bold"))

    o += silhouette()

    # ── магістраль: настил → стопа → нога → вузол ───────────────────────
    ex = ENTRY_XF
    trunk = [(ex, 0.0), (ex, HUB_YF), (0.0, HUB_YF)]
    d = " ".join(f'{"M" if i == 0 else "L"}{fx(x):.0f},{fy(y):.0f}'
                 for i, (x, y) in enumerate(trunk))
    o.append(f'<path d="{d}" fill="none" stroke="{POS}" stroke-width="3.4"/>')
    o.append(f'<circle cx="{fx(ex):.0f}" cy="{fy(0.0):.0f}" r="6" fill="{POS}"/>')
    o.append(_t(fx(ex) + 22, fy(0.0) + 34, "вхід кабелю з настилу подіуму", 10, INK))
    o.append(_t(fx(ex) + 22, fy(0.0) + 50,
                f'{DROP["cable"]}, {DROP["length_m"]:.1f} м від коробки Гр.2', 9, TXT2))

    # ── гілки до кожної лампи ───────────────────────────────────────────
    total_branch = 0.0
    for lamp in L:
        pts = route_to(lamp, hub)
        total_branch += branch_len_m(pts)
        dd = " ".join(f'{"M" if i == 0 else "L"}{fx(x):.0f},{fy(y):.0f}'
                      for i, (x, y) in enumerate(pts))
        dash = ' stroke-dasharray="5,4"' if lamp["soft"] else ""
        o.append(f'<path d="{dd}" fill="none" stroke="{POS}" stroke-width="1.5" '
                 f'opacity="0.85"{dash}/>')
        r = 5 if lamp["fixture"] == "led12" else 4
        o.append(f'<circle cx="{fx(lamp["xf"]):.0f}" cy="{fy(lamp["yf"]):.0f}" r="{r}" '
                 f'fill="#fff" stroke="{POS}" stroke-width="2"/>')

    # ── вузол ───────────────────────────────────────────────────────────
    hx, hy = fx(hub[0]), fy(hub[1])
    o.append(f'<rect x="{hx-52:.0f}" y="{hy-20:.0f}" width="104" height="40" rx="6" '
             f'fill="#fff" stroke="{HUB}" stroke-width="2"/>')
    o.append(_t(hx, hy - 4, "клемний вузол", 10, INK, "middle", "bold"))
    o.append(_t(hx, hy + 11, "Wago 221 у гелі", 9, TXT2, "middle"))

    # ── таблиця гілок збоку ─────────────────────────────────────────────
    tx, ty = 800, 150
    o.append(_t(tx, ty, "Гілки від вузла", 12, INK, "start", "bold"))
    o.append(_t(tx, ty + 18, "довжина — геометрична прикидка з пропорцій фігури", 9, TXT2))
    rows = {}
    for lamp in L:
        key = (lamp["place"], lamp["fixture"])
        rows.setdefault(key, {"n": 0, "len": 0.0, "w": 0.0, "soft": lamp["soft"]})
        rows[key]["n"] += 1
        rows[key]["len"] += branch_len_m(route_to(lamp, hub))
        rows[key]["w"] += lamp["w"]
    y = ty + 46
    for (place, fixture), r in rows.items():
        mark = " (місце уточнюємо)" if r["soft"] else ""
        o.append(_t(tx, y, f'{place} · {r["n"]}× Ø{LAMP_D[fixture]} мм{mark}',
                    10, INK, "start", "bold"))
        length = ("сидить на самому вузлі" if r["len"] < 0.05
                  else f'{r["len"]:.2f} м дроту')
        o.append(_t(tx, y + 15, f'{length} · {r["w"]:.1f} Вт', 10, TXT2))
        y += 38

    trunk_m = branch_len_m(trunk)
    o.append(f'<line x1="{tx}" y1="{y-6}" x2="{W-40}" y2="{y-6}" stroke="{THIN}"/>')
    o.append(_t(tx, y + 14, f'Магістраль у тілі: {trunk_m:.2f} м', 10, INK, "start", "bold"))
    o.append(_t(tx, y + 32, f'Усі гілки разом: {total_branch:.2f} м', 10, INK, "start", "bold"))
    o.append(_t(tx, y + 50, f'Разом дроту в костюмі ≈ {trunk_m + total_branch:.1f} м',
                10, GOOD, "start", "bold"))
    o.append(_t(tx, y + 68, "плюс запас на вигини і зачистку", 9, TXT2))

    # ── пояснення ───────────────────────────────────────────────────────
    ex_x, ex_y = 60, 150
    o.append(_t(ex_x, ex_y, "Як це читати", 12, INK, "start", "bold"))
    for i, line in enumerate([
            "Товста лінія — магістральна пара: заходить",
            "з настилу крізь ногу і піднімається до грудей.",
            "",
            "Тонкі лінії — гілки до окремих ламп. Кожна",
            "лампа має СВОЮ пару від вузла, тому",
            "перегоріла лампа не гасить сусідніх.",
            "",
            "Дріт іде всередині решітки корпусу —",
            "по прямій крізь порожнечу він не піде,",
            "тому траси намальовані ламаними.",
            "",
            "Пунктир — те, що ще не підтверджене",
            "конструктором (лампа грудей видна лише",
            "спереду, місце двох Ø8 мм уточнюємо).",
    ]):
        o.append(_t(ex_x, ex_y + 24 + i * 16, line, 10, TXT2))

    # ── підвал ──────────────────────────────────────────────────────────
    fy0 = H - 76
    o.append(f'<line x1="40" y1="{fy0-20}" x2="{W-40}" y2="{fy0-20}" stroke="{THIN}"/>')
    o.append(_t(40, fy0,
                f'Довжини рахуються з пропорцій фігури (висота {FIG_H_M:.1f} м над настилом) '
                f'манхеттенською трасою — це прикидка на закупівлю дроту, а не розмір з креслення.',
                10, TXT2))
    o.append(_t(40, fy0 + 18,
                f'Місць на схемі {len(L)}, у специфікації {n12 + n8} ламп — '
                f'розбіжність усередині бази показуємо, а не ховаємо.', 10, TXT2))
    o.append(_t(40, fy0 + 36,
                "Електрика цього ж вузла (шини, запобіжник, паралельне підключення) — "
                "на схемі «Лампи на корпусі робота».", 10, TXT2))
    o.append("</svg>")
    return "\n".join(o)


def verify(text):
    root = ET.fromstring(text)
    labels = " ".join(el.text or "" for el in
                      root.iter("{http://www.w3.org/2000/svg}text"))
    for sp in SPOTS:
        if sp["place"] not in labels:
            raise SystemExit(f"на плані нема місця «{sp['place']}»")
    # кожна лампа має свою гілку: шляхів має бути не менше, ніж ламп
    paths = list(root.iter("{http://www.w3.org/2000/svg}path"))
    if len(paths) < len(lamps()):
        raise SystemExit("гілок менше, ніж ламп — хтось лишився без дроту")
    return True


def main():
    text = svg()
    verify(text)
    out = HERE / "body_route.svg"
    out.write_text(text, encoding="utf-8")
    L = lamps()
    hub = (0.0, HUB_YF)
    total = sum(branch_len_m(route_to(x, hub)) for x in L)
    print(f"SVG записано: {out} ({len(text.encode('utf-8'))/1024:.1f} KB) · "
          f"ламп {len(L)} · гілок стільки ж · перевірка пройшла")
    print(f"дроту в костюмі ≈ {total + branch_len_m([(ENTRY_XF,0.0),(ENTRY_XF,HUB_YF),(0.0,HUB_YF)]):.1f} м")


if __name__ == "__main__":
    main()
