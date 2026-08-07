#!/usr/bin/env python3
"""
Гр.2 — «біжуча вода»: електрична схема адресної стрічки на подіумі.

Що показує: шлях від щита до восьми рукавів зірки. Коробка WLED (гермокоробка
IP65) стоїть посередником: контролер, конденсатор-буфер на живленні і буфер
сигналу на лінії DATA — усі три потрібні саме тому, що лінія до стрічки довга
(рішення Івана 02.08, data/decisions.json). Далі один магістральний кабель
заходить під настил ДО ЦЕНТРУ подіуму (рішення Івана, підтверджене 07.08.2026:
усі вісім рукавів зводяться в одну точку, а не живляться з восьми зовнішніх
кінців) і там паралельно розходиться на вісім рукавів.

Числа — з lights_node_model (cable_tree/fuses) і lights/data/params.json +
lights/data/strip_install.json. Жодної цифри руками.

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
INSTALL = json.loads((HERE.parent / "data" / "strip_install.json").read_text())

WA = next(f for f in P["fixtures"] if f["id"] == "water_arms")
WLED = next(f for f in P["fixtures"] if f["id"] == "wled")
ADDR = P["addressable"]
AINS = P["addressable_install"]
GROUPS = P["groups"]
BUDGET = P["wiring"]["drop_budget"]

TREE = {r["id"]: r for r in lnm.cable_tree()}
FUSE = {f["id"]: f["rating"] for f in lnm.fuses()}

BR = TREE["br_g2"]           # щит → коробка WLED
INJ = TREE["inj_g2"]         # WLED → точки живлення стрічки

N = WA["qty"]
ARM_LEN = WA["length_m"]                       # промінь + заворот, одна ланка
ARM_FULL_W = ARM_LEN * WA["w_per_m"]           # нейплейт рукава на суцільному білому
ARM_PEAK_W = ARM_FULL_W * ADDR["duty_peak"]    # реальний миттєвий пік біжучого фронту

FEED = INSTALL["feed_point"]
INJ_JOINT = next(j for j in INSTALL["joints"] if "інжек" in j["where"].lower())


def build():
    s = sk.Sheet(
        1280, 860,
        "Гр.2 · «біжуча вода» — адресна стрічка подіуму",
        f'{N} × {ARM_LEN:.2f} м · {ARM_FULL_W:.1f} Вт нейплейт на рукав · '
        f'запобіжник Гр.2 {FUSE["g2"]:g} А · робочий пік стрічки '
        f'{ARM_PEAK_W * N:.1f} Вт при {ADDR["duty_peak"] * 100:.0f}% біжучого фронту',
        "Ввід живлення й даних — у центрі подіуму, не з восьми зовнішніх кінців: "
        "менше міді, і траса не лежить по краю, де на неї наступають.")

    # ── щит ────────────────────────────────────────────────────────────
    panel = s.block(40, 150, 180, 150, "Щит подіуму",
                    f'запобіжник Гр.2 · {FUSE["g2"]:g} А\nреле 12 В / 30 А\n'
                    f'гасить групу цілком',
                    color=sk.G2, bg=sk.PANEL_BG)
    p_out = panel.port("g2", "r", 0.5)

    # ── коробка WLED: контролер + конденсатор + буфер сигналу ───────────
    wled_model, wled_in = WLED["model"].split(", ", 1)
    wled = s.block(360, 150, 260, 150, "Коробка WLED · гермокоробка IP65",
                   f'{wled_model}\n{wled_in}\n'
                   f'конденсатор {AINS["input_cap_uf"]}+ мкФ / {AINS["input_cap_v"]}В+\n'
                   f'буфер {AINS["data_buffer_chip"]} на лінії DATA',
                   color=sk.G2)
    w_in = wled.port("in", "l", 0.5)
    w_out = wled.port("out", "r", 0.5)

    # ── центральний вузол під настилом ───────────────────────────────────
    hub_x0, hub_x1, hub_y = 700, 1240, 225
    hub = s.block(hub_x0, hub_y - 24, hub_x1 - hub_x0, 48,
                  "Центральний вузол під настилом · шина +12В / шина − / лінія DATA",
                  color=sk.G2, bg="#fff")
    h_in = hub.port("in", "l", 0.5)

    s.wire(p_out, w_in, sk.G2, 2.4,
           label=f'{BR["cable"]} · {BR["length_m"]:.0f} м')
    s.wire(w_out, h_in, sk.G2, 2.4,
           label=f'{INJ["cable"]} · {INJ["length_m"]:.0f} м')

    # ── вісім рукавів, кожен своєю парою від вузла ──────────────────────
    step = (hub_x1 - hub_x0 - 70) / (N - 1)
    for i in range(N):
        px = hub_x0 + 35 + step * i
        arm = s.block(px - 27, 400, 54, 80, f'#{i + 1}',
                      f'{ARM_LEN:.2f} м\n{ARM_FULL_W:.1f} Вт',
                      color=sk.INK)
        s.wire(hub.port(f"tap{i}", "b", (px - hub_x0) / (hub_x1 - hub_x0)),
               arm.port("v", "t", 0.5), sk.G2, 1.6)

    # ── пояснювальні тексти ──────────────────────────────────────────────
    s.text(40, 340, "Кабель WLED→стрічка довгий —", 10, sk.TXT2)
    s.text(40, 358, "тому конденсатор на вході і", 10, sk.TXT2)
    s.text(40, 376, "буфер на DATA не розкіш, а те,", 10, sk.TXT2)
    s.text(40, 394, "без чого контролер скидається.", 10, sk.TXT2)

    s.text(40, 440, "Ввід у центрі, не з восьми", 10, sk.INK, weight="bold")
    s.text(40, 458, "зовнішніх кінців: менше міді,", 10, sk.TXT2)
    s.text(40, 476, "траса не йде по краю подіуму,", 10, sk.TXT2)
    s.text(40, 494, "де на неї наступають.", 10, sk.TXT2)

    s.text(40, 540, "Рукави підключені паралельно,", 10, sk.TXT2)
    s.text(40, 558, "не ланцюжком: згас один —", 10, sk.TXT2)
    s.text(40, 576, "решта світять як і раніше.", 10, sk.TXT2)

    s.text(40, 610, "Напрямок хвилі задає реверс", 10, sk.TXT2)
    s.text(40, 628, "сегмента у прошивці WLED, а не", 10, sk.TXT2)
    s.text(40, 646, "те, з якого кінця прийшов дріт.", 10, sk.TXT2)

    if ADDR.get("day_lockout"):
        s.text(40, 680, "Вдень стрічка вимкнена —", 10, sk.WARN)
        s.text(40, 698, "чипи перегріваються на сонці.", 10, sk.WARN)

    # ── підвал: цифри без вигадки ────────────────────────────────────────
    strict = INJ["id"] in BUDGET["strict_ids"]
    budget_pct = BUDGET["strict_pct"] if strict else BUDGET["relaxed_pct"]
    s.footnote(f'Просадка WLED→вузол −{INJ["drop_pct"]:.2f}% (сукупно від щита '
               f'−{INJ["cum_pct"]:.2f}%) при межі {budget_pct:.0f}% для адресної '
               f'лінії · струм {INJ["amps"]:.2f} А.')
    s.footnote(f'Точки підживлення (power injection) на самому рукаві: '
               f'{INJ_JOINT["what"]} — {INJ_JOINT["status"]}.')
    s.footnote(f'{AINS["data_note"]}')
    s.footnote(f'{FEED["direction_note"]}')
    s.footnote(f'Вт на рукаві — нейплейт суцільного білого (ніколи не буває); '
               f'реальний робочий пік {ARM_PEAK_W:.2f} Вт на рукав при '
               f'{ADDR["duty_peak"] * 100:.0f}% біжучого фронту.')

    return s


if __name__ == "__main__":
    build().write(HERE / "circuit_g2_strip.svg")
