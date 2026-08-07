#!/usr/bin/env python3
"""
Гр.3А — аварійна лінія: електрична схема.

Що показує: щит подіуму (запобіжник + реле групи) → коробка аварійної лінії →
кабель у каналі настилу → вісім граней октагона по три врізних вогні на грань,
усі паралельно на одному кабелі. Окремо, власним коротким хвостом біля ящика
станції — два маркерні вогники ящика: магістраль подіуму їх не бачить.

Числа — з lights_node_model.cable_tree / fuses / peak_watts, з
lights/data/params.json (fixtures, wiring) і з lights/data/podium_plan.json
(геометрія октагона: скільки граней і по скільки вогнів на грань). Жодної
цифри руками.

Малюється конструктором schema_kit: дріт зʼєднує два порти, verify не дає
лишити обірваний кінець чи перетин без містка.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lights_node_model as lnm            # noqa: E402
import schema_kit as sk                    # noqa: E402

P = json.loads((HERE.parent / "data" / "params.json").read_text())
PODIUM = json.loads((HERE.parent / "data" / "podium_plan.json").read_text())
VIS = json.loads((HERE.parent / "data" / "visibility.json").read_text())

STAIRS = next(f for f in P["fixtures"] if f["id"] == "stairs")
BOXFX = next(f for f in P["fixtures"] if f["id"] == "box_marker")
PANEL_METERS = next(f for f in P["fixtures"] if f["id"] == "panel_meters")
G3A = P["groups"]["g3a"]
BUS_V = P["bus_v"]

TREE = {r["id"]: r for r in lnm.cable_tree()}
FUSE = {f["id"]: f["rating"] for f in lnm.fuses()}
PEAK = lnm.peak_watts()

BR = TREE["br_g3a"]              # щит → коробка аварійної
STAIRS_SEG = TREE["stairs_g3a"]  # коробка → врізні вогні торця
BOX_SEG = TREE["box_g3a"]        # щит ящика → маркерні вогники ящика

N = STAIRS["qty"]
W_UNIT = STAIRS["w_unit"]
SIDES = PODIUM["octagon"]["sides"]
assert N % SIDES == 0, "кількість вогнів торця не ділиться порівну на грані октагона"
PER_FACE = N // SIDES

NQ = BOXFX["qty"]
NW = BOXFX["w_unit"]

STAIRS_PEAK = N * W_UNIT
BOX_PEAK = NQ * NW
PM_PEAK = PANEL_METERS["qty"] * PANEL_METERS["w_unit"]

EDGE = json.loads((HERE.parent / "data" / "edge_light.json").read_text())
CONFLICT = EDGE["conflict"]


def build():
    s = sk.Sheet(
        1280, 900,
        "Гр.3А · аварійна лінія — врізні вогні торця + маркер ящика",
        f'{N} × {W_UNIT:g} Вт по торцю (по {PER_FACE} на грань) + {NQ} × {NW:g} Вт '
        f'на ящику · пік групи {PEAK["g3a"]:.1f} Вт · запобіжник {FUSE["g3a"]:g} А · '
        f'не регулюється диммером',
        G3A["note"])

    # ── щит подіуму ────────────────────────────────────────────────────
    # усі три порти на одній висоті (y=230) — дріт іде прямою, без зламу,
    # тому підпис над ним ніколи не потрапляє на сусідній блок (див. circuit_g1).
    panel = s.block(40, 170, 200, 120, "Щит подіуму",
                     f'запобіжник Гр.3А · {FUSE["g3a"]:g} А\nреле {BUS_V:.0f} В / 30 А\n'
                     f'аварійна — своя, окремий канал',
                     color=sk.WARN, bg=sk.PANEL_BG)
    p_out = panel.port("g3a", "r", 0.5)

    box = s.block(380, 170, 200, 120, "Коробка аварійної лінії",
                   "гермокоробка IP65\nрозподіл на торець подіуму",
                   color=sk.WARN)
    b_in = box.port("in", "l", 0.5)
    b_out = box.port("out", "r", 0.5)

    bus_x0, bus_x1, bus_y = 720, 1220, 230
    bus = s.block(bus_x0, bus_y - 24, bus_x1 - bus_x0, 48,
                   f'Кабель у каналі настилу · {STAIRS_SEG["length_m"]:.0f} м · {STAIRS_SEG["cable"]}',
                   color=sk.WARN, bg="#fff")
    bus_in = bus.port("in", "l", 0.5)

    s.wire(p_out, b_in, sk.WARN, 2.4, label=f'{BR["cable"]} · {BR["length_m"]:.1f} м')
    s.wire(b_out, bus_in, sk.WARN, 2.4,
           label=f'AWG{STAIRS_SEG["awg"]} · {STAIRS_SEG["amps"]:.2f} А · '
                 f'−{STAIRS_SEG["drop_pct"]:.1f}%')

    s.text(bus_x0, 300, f'{N} врізних вогнів торця діляться порівну на {SIDES} '
                          f'граней октагона — по {PER_FACE} на грань,', 10, sk.TXT2)
    s.text(bus_x0, 318, "усі грані сидять паралельно на одному кабелі (не ланцюжком).",
           10, sk.TXT2)

    # ── вісім граней октагона, по PER_FACE вогнів на кожній ─────────────
    faces, step = [], (bus_x1 - bus_x0 - 70) / (SIDES - 1)
    for i in range(SIDES):
        fx = bus_x0 + 35 + step * i
        face = s.block(fx - 30, 380, 60, 80, f'Грань {i+1}',
                        f'{PER_FACE} × {W_UNIT:g} Вт\n{PER_FACE * W_UNIT:.1f} Вт',
                        color=sk.WARN)
        faces.append(face)
        s.wire(bus.port(f"face{i}", "b", (fx - bus_x0) / (bus_x1 - bus_x0)),
               face.port("v", "t", 0.5), sk.WARN, 1.6)

    # ── маркерні вогники ящика: свій короткий хвіст, окремо від подіуму ──
    s.text(760, 505, "Ящик станції — окреме живлення, не через щит подіуму:", 10,
           sk.INK, weight="bold")

    # обидва маркери на одній висоті з портом щита (y=575) — прямі дроти,
    # без зламу, підпис лягає рівно в проміжку між блоками.
    boxpanel = s.block(760, 520, 200, 110, "Щит ящика станції",
                        f'{BOX_SEG["cable"]}\n{BOX_SEG["length_m"]:.1f} м — свій хвіст,\n'
                        f'магістраль подіуму це не бачить',
                        color=sk.G2, bg=sk.PANEL_BG)
    out1 = boxpanel.port("out1", "r", 0.5)
    out2 = boxpanel.port("out2", "r", 0.72)

    m1 = s.block(1100, 535, 90, 80, "Маркер #1", f'{NW:g} Вт', color=sk.G2)
    m2 = s.block(1100, 645, 90, 80, "Маркер #2", f'{NW:g} Вт', color=sk.G2)

    s.wire(out1, m1.port("in", "l", 0.5), sk.G2, 1.8,
           label=f'AWG{BOX_SEG["awg"]} · {BOX_SEG["amps"]:.2f} А')
    s.wire(out2, m2.port("in", "l", 0.5), sk.G2, 1.8)

    s.text(760, 665, "Два вогники на протилежні боки ящика — з одного боку", 10, sk.TXT2)
    s.text(760, 683, "він інакше лишається темним у пилу.", 10, sk.TXT2)

    # ── пояснення текстом (ліва колонка) ────────────────────────────────
    s.text(40, 340, "Чому ця лінія окрема:", 10, sk.INK, weight="bold")
    s.text(40, 358, f'коли станція сідає, Гр.2 {P["groups"]["g2"]["note"]},', 10, sk.TXT2)
    s.text(40, 376, f'Гр.1 {P["groups"]["g1"]["note"]},', 10, sk.TXT2)
    s.text(40, 394, f'а Гр.3А {G3A["note"]}.', 10, sk.TXT2)

    s.text(40, 460, "Не регулюється диммером:", 10, sk.INK, weight="bold")
    s.text(40, 478, f'{STAIRS["name"].lower()} і {BOXFX["name"].lower()}', 10, sk.TXT2)
    s.text(40, 496, "мають dimming=none — або горять на повну,", 10, sk.TXT2)
    s.text(40, 514, "або вимкнені цілком, проміжного стану нема.", 10, sk.TXT2)

    s.text(40, 570, "Пасивний шар (страховка, не заміна):", 10, sk.INK, weight="bold")
    s.text(40, 588, "катафоти і мікропризматична стрічка по торцю", 10, sk.TXT2)
    s.text(40, 606, "повертають чужу фару навіть при повному", 10, sk.TXT2)
    s.text(40, 624, "знеструмленні — але без чужого світла на них", 10, sk.TXT2)
    s.text(40, 642, "не видно нічого, вони не замінюють цю лінію.", 10, sk.TXT2)

    est = " (прикидка)" if STAIRS_SEG.get("estimate") else ""
    verdict = "у нормі" if STAIRS_SEG["ok"] else "ПОНАД бюджет"
    s.footnote(f'Просадка від коробки −{STAIRS_SEG["drop_pct"]:.1f}%, накопичено від станції до '
               f'найдальшого вогню торця −{STAIRS_SEG["cum_pct"]:.1f}% при бюджеті лінії '
               f'{STAIRS_SEG["budget_pct"]:.0f}% ({verdict}) · струм лінії {STAIRS_SEG["amps"]:.2f} А '
               f'при запобіжнику Гр.3А {FUSE["g3a"]:g} А.')
    s.footnote(f'Довжина {STAIRS_SEG["length_m"]:.0f} м{est} від коробки до торця, {BR["length_m"]:.1f} м '
               f'від щита до коробки{" (прикидка)" if BR.get("estimate") else ""} — обидві не з креслення, '
               f'міряти по факту складання.')
    s.footnote(f'Запобіжник Гр.3А рахований на всю групу (тут на схемі — {STAIRS_PEAK:.1f} Вт торця + '
               f'{BOX_PEAK:.1f} Вт ящика; ще {PM_PEAK:.1f} Вт бере пост контролю в щиті, він на цій схемі не показаний).')
    s.footnote(f'Хвіст ящика: −{BOX_SEG["cum_pct"]:.2f}% просадки, {BOX_SEG["amps"]:.2f} А — окрема ділянка, '
               f'у ланцюг подіуму не додається.')
    s.footnote(f'Відкрите: {CONFLICT["text"]} Узгодження з {CONFLICT["owner"]} — {CONFLICT["status"]}.')
    s.footnote(VIS["warning"])
    return s


if __name__ == "__main__":
    build().write(HERE / "circuit_g3a.svg")
