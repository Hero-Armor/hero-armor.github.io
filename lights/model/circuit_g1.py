#!/usr/bin/env python3
"""
Гр.1 — прожектори заливки: електрична схема кільця.

Що показує: шлях від щита до восьми прожекторів на стійках. Реле групи,
ШІМ-диммер, замкнуте кільце по периметру октагона і відвід на кожну стійку.

Числа — з моделі (lights_node_model.cable_tree / fuses / peak_watts) і з
lights/data/params.json. Жодної цифри руками.

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
SPOT = next(f for f in P["fixtures"] if f["id"] == "spot")
GROUPS = P["groups"]
TREE = {r["id"]: r for r in lnm.cable_tree()}
FUSE = {f["id"]: f["rating"] for f in lnm.fuses()}
PEAK = lnm.peak_watts()

BR = TREE["br_g1"]          # щит → коробка диммера
RING = TREE["ring_g1"]      # диммер → кільце
DROP = TREE["drop_spot"]    # відвід на прожектор

N = SPOT["qty"]
W_UNIT = SPOT["w_unit"]


def build():
    s = sk.Sheet(
        1280, 700,
        "Гр.1 · прожектори заливки — кільце по периметру подіуму",
        f'{N} × {W_UNIT:g} Вт · {PEAK["g1"]:.0f} Вт на групу · запобіжник '
        f'{FUSE["g1"]:g} А · яскравість крутиться ШІМ-диммером',
        "Кільце замкнуте: найдальша стійка живиться з двох боків, тому крайні "
        "прожектори не тьмяніші за ближні.")

    panel = s.block(40, 170, 180, 120, "Щит подіуму",
                    f'запобіжник Гр.1 · {FUSE["g1"]:g} А\nреле 12 В / 30 А\n'
                    f'гасить групу цілком',
                    color=sk.G1, bg=sk.PANEL_BG)
    p_out = panel.port("g1", "r", 0.5)

    dim = s.block(360, 170, 200, 120, "ШІМ-диммер",
                  "SUPERNIGHT 12-24 В · 30 А\nгвинтові клеми IN / OUT\nу гермокоробці IP65",
                  color=sk.G1)
    d_in = dim.port("in", "l", 0.5, "IN")
    d_out = dim.port("out", "r", 0.5, "OUT")

    ring_x0, ring_x1, ring_y = 700, 1240, 230
    ring = s.block(ring_x0, ring_y - 24, ring_x1 - ring_x0, 48,
                   f'Кільце по периметру · {RING["length_m"]:.0f} м · {RING["cable"]}',
                   color=sk.G1, bg="#fff")
    r_in = ring.port("in", "l", 0.5)

    s.wire(p_out, d_in, sk.G1, 2.4,
           label=f'{BR["cable"]} · {BR["length_m"]:.0f} м')
    s.wire(d_out, r_in, sk.G1, 2.4,
           label=f'AWG{RING["awg"]} · {RING["amps"]:.1f} А · −{RING["drop_pct"]:.1f}%')

    # вісім стійок висять на кільці власними відводами
    posts, step = [], (ring_x1 - ring_x0 - 70) / (N - 1)
    for i in range(N):
        px = ring_x0 + 35 + step * i
        post = s.block(px - 28, 400, 56, 76, f'#{i+1}',
                       f'MR16\n{W_UNIT:g} Вт', color=sk.INK)
        posts.append(post)
        s.wire(ring.port(f"tap{i}", "b", (px - ring_x0) / (ring_x1 - ring_x0)),
               post.port("v", "t", 0.5), sk.G1, 1.6)

    # замикання кільця: назад у ту саму точку вводу, але з іншого кінця
    tail = s.block(ring_x1 - 150, 560, 150, 58, "Кінець кільця",
                   "змикається з вводом", color=sk.G1, bg=sk.PANEL_BG, dash="5,4")
    s.wire(posts[-1].port("loop", "b", 0.5), tail.port("in", "t", 0.5), sk.G1, 1.6, dash="6,4")
    s.wire(tail.port("back", "l", 0.5), dim.port("loop", "b", 0.7), sk.G1, 1.6, dash="6,4")

    s.text(40, 340, "Диммер керує ШІМ-імпульсами,", 10, sk.TXT2)
    s.text(40, 358, "а не заниженням напруги —", 10, sk.TXT2)
    s.text(40, 376, "лампа бачить повні 12 В і не", 10, sk.TXT2)
    s.text(40, 394, "жовтіє на малій яскравості.", 10, sk.TXT2)

    s.text(40, 440, f'Відвід на кожну стійку:', 10, sk.INK, weight="bold")
    s.text(40, 458, f'{DROP["cable"]}, {DROP["length_m"]:.1f} м —', 10, sk.TXT2)
    s.text(40, 476, "штатний хвіст світильника", 10, sk.TXT2)
    s.text(40, 494, "плюс подовження.", 10, sk.TXT2)

    s.text(40, 540, "Перегорів один прожектор —", 10, sk.TXT2)
    s.text(40, 558, "решта світять: кільце не", 10, sk.TXT2)
    s.text(40, 576, "рветься, кожен висить на", 10, sk.TXT2)
    s.text(40, 594, "власному відводі.", 10, sk.TXT2)

    est = " (прикидка)" if RING.get("estimate") else ""
    s.footnote(f'Просадка до найдальшої стійки −{RING["drop_pct"]:.1f}% при межі '
               f'{P["wiring"]["drop_crit_pct"]:.0f}% · струм групи {RING["amps"]:.1f} А '
               f'при межі диммера 30 А.')
    s.footnote(f'Довжина кільця {RING["length_m"]:.0f} м{est} — периметр октагона з '
               f'креслення; відвід {DROP["length_m"]:.1f} м на стійку.')
    s.footnote("Прицілювання ~16° угору на фігуру, розкрив 60°, 4000 K — "
               "тепліше світло робило синю броню сірою.")
    return s


if __name__ == "__main__":
    build().write(HERE / "circuit_g1.svg")
