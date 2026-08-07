#!/usr/bin/env python3
"""
Hero Armor audio node — схема ЖИВЛЕННЯ (не сигнальний тракт, той у signal_chain.svg).

Показує шлях енергії: станція EcoFlow (авто-вихід 12 В) → ВЛАСНИЙ кабель повз
щит світла і групові реле → запобіжник → клемник-зірка → розгалуження на
підсилювач TPA3116D2 (+ буферний конденсатор впритул до VCC) і на понижувач
12→5 В, який годує ESP32, ЦАП PCM5102A і радар LD2410C.

Числа — з audio/data/params.json (ліміт порту станції, кабель, ККД, струми
3.3 В/5 В рейок, заміряний холостий хід) і audio/data/assembly.json (номінал
запобіжника, ємність буферного конденсатора — витягуються з текстових полів
монтажного плану, бо саме там вони й зафіксовані). Розрахунки піку/спокою —
через audio_node_model, той самий рушій, що рахує таблицю CLI і дашборд.

Малюється конструктором schema_kit (lights/model) — дріт з'єднує два порти,
verify не дає лишити обрив чи перетин без містка.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "lights" / "model"))
import audio_node_model as anm         # noqa: E402
import schema_kit as sk                # noqa: E402

ASM = json.loads((HERE.parent / "data" / "assembly.json").read_text())
P = anm.P
V = anm.V

# ---------------------------------------------------------------- дані входу
FEED = P["power_source"]["feed"]
LIMIT_W, LIMIT_A = FEED["limit_w"], FEED["limit_a"]
CABLE_AWG, CABLE_M = FEED["awg"], FEED["cable_m"]
ALWAYS_ON, OWN_CABLE = FEED["always_on"], FEED["own_cable"]

# запобіжник — номінал зафіксований текстом у монтажному плані (assembly.json),
# витягуємо регуляркою, а не переписуємо цифру руками. Він стоїть ДВІЧІ поспіль
# з тим самим номіналом: у штекері прикурювача і ще раз у гермовводі коробки.
_fuse_plug = next(c for c in ASM["connectors"] if "Станція" in c["iface"])
_fuse_box = next(c for c in ASM["connectors"] if "Вхід у коробку" in c["iface"])
FUSE_A = float(re.search(r"(\d+(?:\.\d+)?)\s*А", _fuse_box["conn"]).group(1))
FUSE_A_PLUG = float(re.search(r"(\d+(?:\.\d+)?)\s*А", _fuse_plug["conn"]).group(1))

_modules = {m["key"]: m for m in ASM["panel"]["modules"]}
CAP_LABEL = _modules["cap"]["label"]
CAP_NOTE = _modules["cap"]["note"]
BUCK_LABEL = _modules["buck"]["label"]
BUCK_NOTE = _modules["buck"]["note"]
AMP_LABEL = _modules["amp"]["label"]
AMP_NOTE = _modules["amp"]["note"]

# ---------------------------------------------------------------- розрахунки
C33 = P["currents_33v"]
SENSOR_W = P["sensor"]["a_5v"] * 5.0
ESP32_IDLE_W = C33["esp32_idle"] * 3.3
ESP32_PLAY_W = (C33["esp32_play"] + C33["sd_read"]) * 3.3
DAC_W = C33["dac"] * 3.3

AMP_IDLE_W = P["amp_idle_a"] * V


def _buck_in_w(playing):
    """Вхідна (12 В) потужність гілки buck — з урахуванням ККД понижувача."""
    a33 = (C33["esp32_play"] + C33["dac"] + C33["sd_read"]) if playing \
        else (C33["esp32_idle"] + C33["dac"])
    out_w = a33 * 3.3 + P["sensor"]["a_5v"] * 5.0
    return out_w / P["buck_eff"]


BUCK_IDLE_W = _buck_in_w(False)
BUCK_PLAY_W = _buck_in_w(True)

wh_day, _results = anm.composite_day()
NIGHT_KEYS = ("night", "quiet")          # 12 год композитної доби — нічна частка
NIGHT_H = sum(anm.CASES_DOC["composite_day_hours"][k] for k in NIGHT_KEYS)
wh_night = sum(_results[k]["i_avg"] * V * anm.CASES_DOC["composite_day_hours"][k]
               for k in NIGHT_KEYS)

_peak_case = max(_results.values(), key=lambda r: r["p_peak"])
AMP_PEAK_W = _peak_case["p_peak"] / P["amp_eff"] + AMP_IDLE_W

MEAS = P["measured"]
MODEL_IDLE_W = AMP_IDLE_W + BUCK_IDLE_W
NODE_PEAK_W = AMP_PEAK_W + BUCK_PLAY_W


def build():
    s = sk.Sheet(
        1400, 980,
        "Живлення аудіо-вузла — від станції до кожного споживача",
        f'вхід {LIMIT_W:g} Вт / {LIMIT_A:g} А (авто-порт EcoFlow) · '
        f'запобіжник {FUSE_A:g} А · вузол ~{NODE_PEAK_W:.0f} Вт на піку, '
        f'~{MODEL_IDLE_W:.1f} Вт у спокої (розрахунок моделі)',
        "Свій кабель повз щит світла і групові реле — звук працює цілодобово "
        "і не гасне разом зі світлом.")

    # ---- станція ----------------------------------------------------------
    station = s.block(40, 250, 190, 120, "Станція EcoFlow",
                       f'авто-вихід 12 В (прикурювач)\nліміт {LIMIT_W:g} Вт / '
                       f'{LIMIT_A:g} А\nзапас {LIMIT_W / NODE_PEAK_W:.0f}× '
                       f'до піку вузла', color=sk.G2, bg=sk.PANEL_BG)
    st_out = station.port("out", "r", 0.5)

    # ---- запобіжник (вхід у коробку) --------------------------------------
    fuse = s.block(430, 250, 150, 120, "Запобіжник",
                    f'{FUSE_A:g} А, у гермовводі,\nвпритул до клемника\n'
                    f'(ще {FUSE_A_PLUG:g} А — у штекері\nприкурювача, до кабелю)',
                    color=sk.WARN)
    f_in = fuse.port("in", "l", 0.5)
    f_out = fuse.port("out", "r", 0.5)

    s.wire(st_out, f_in, sk.G2, 2.4,
           label=f'{"ВЛАСНИЙ" if OWN_CABLE else "спільний"} кабель '
                 f'AWG{CABLE_AWG} · ~{CABLE_M:g} м')
    cable_note = "повз щит світла і групові реле" + \
        (" — цілодобово, без реле" if ALWAYS_ON else "")
    s.text(260, 230, cable_note, 9, sk.G3, "start")

    # ---- клемник K1 (точка зірки) -----------------------------------------
    k1 = s.block(680, 250, 160, 120, "Клемник K1",
                 "точка зірки: сюди\nсходяться всі землі",
                 color=sk.INK, bg=sk.PANEL_BG)
    k1_in = k1.port("in", "l", 0.5)
    k1_cap = k1.port("to_cap", "r", 0.25)
    k1_buck = k1.port("to_buck", "r", 0.75)
    s.wire(f_out, k1_in, sk.WARN, 2.4)

    # ---- гілка підсилювача: K1 -> конденсатор -> TPA3116D2 -----------------
    cap = s.block(960, 90, 150, 100, "Буферний конд.",
                  f'{CAP_LABEL}\n{CAP_NOTE}', color=sk.G1)
    cap_in = cap.port("in", "l", 0.5)
    cap_out = cap.port("out", "r", 0.5)
    s.wire(k1_cap, cap_in, sk.G1, 2.2)

    amp = s.block(1200, 90, 170, 150, f'Підсилювач {AMP_LABEL.split()[0]}',
                  f'спокій ~{AMP_IDLE_W:.2f} Вт\nпік ~{AMP_PEAK_W:.0f} Вт '
                  f'(модель,\n«{_peak_case["case"]}»)\nрадіатор — назовні коробки',
                  color=sk.G1)
    amp_in = amp.port("in", "l", 0.5)
    s.wire(cap_out, amp_in, sk.G1, 2.2)

    # ---- гілка живлення 5 В: K1 -> buck -> шина -> ESP32 / ЦАП / радар ------
    buck = s.block(960, 470, 170, 130, "Понижувач 12→5 В",
                   f'{BUCK_NOTE.split()[0]} · {BUCK_LABEL}\nвхід: спокій '
                   f'~{BUCK_IDLE_W:.2f} Вт · відтв. ~{BUCK_PLAY_W:.2f} Вт',
                   color=sk.G3)
    buck_in = buck.port("in", "l", 0.5)
    s.wire(k1_buck, buck_in, sk.G3, 2.2)

    esp32 = s.block(1200, 420, 170, 90, "ESP32 + microSD",
                    f'спокій ~{ESP32_IDLE_W:.2f} Вт\nвідтв. ~{ESP32_PLAY_W:.2f} Вт',
                    color=sk.G3)
    dac = s.block(1200, 540, 170, 90, "ЦАП PCM5102A",
                  f'~{DAC_W:.2f} Вт\nпостійно', color=sk.G3)
    radar = s.block(1200, 660, 170, 90, "Радар LD2410C",
                    f'~{SENSOR_W:.2f} Вт\nпостійно (завжди слухає)',
                    color=sk.G3)

    # вертикальна шина 5 В: тап на висоті КОЖНОГО споживача — дріт іде рівно
    # по горизонталі, без спільної проміжної лінії (звідти й були перетини)
    bus_y0, bus_y1 = esp32.y, radar.y + radar.h
    bus = s.block(1160, bus_y0, 18, bus_y1 - bus_y0, "", color=sk.G3, bg="#fff")
    bus_in = bus.port("in", "l", 0.5)
    s.wire(buck.port("out", "r", 0.5), bus_in, sk.G3, 2.2)
    s.text(bus.x - 6, bus.y - 10, "шина 5 В", 9, sk.TXT2, "start")

    for i, dev in enumerate((esp32, dac, radar)):
        cy = dev.y + dev.h / 2
        frac = (cy - bus.y) / bus.h
        s.wire(bus.port(f"tap{i}", "r", frac), dev.port("in", "l", 0.5), sk.G3, 1.8)

    # ---- пояснення зліва (як у circuit_g1) ---------------------------------
    s.text(40, 420, "Чому окремий кабель, а не щит світла:", 10, sk.INK, weight="bold")
    s.text(40, 438, "світло гасять реле й таймер станції —", 10, sk.TXT2)
    s.text(40, 456, "робот не має мовчати, коли гасне світло.", 10, sk.TXT2)
    s.text(40, 474, "Тому звук іде своїм проводом просто з", 10, sk.TXT2)
    s.text(40, 492, "авто-виходу станції, повз щит і реле.", 10, sk.TXT2)

    s.text(40, 550, "Радіатор ампа — крізь стінку назовні:", 10, sk.INK, weight="bold")
    s.text(40, 568, "у закритій коробці на сонці кристал іде", 10, sk.TXT2)
    s.text(40, 586, "за 150°C і замовкає в захисті. Радіатор", 10, sk.TXT2)
    s.text(40, 604, "50×50 мм через термопрокладку тримає", 10, sk.TXT2)
    s.text(40, 622, "його близько до 84°C навіть на плайї.", 10, sk.TXT2)

    s.text(40, 680, "Скільки їсть вузол (з моделі):", 10, sk.INK, weight="bold")
    s.text(40, 698, f'за ніч (~{NIGHT_H:g} год composite) — ~{wh_night:.1f} Вт·год', 10, sk.TXT2)
    s.text(40, 716, f'за добу (24 год composite) — ~{wh_day:.1f} Вт·год', 10, sk.TXT2)
    s.text(40, 734, f'холостий хід ЗАМІРЯНО {MEAS["node_w"]:g} Вт ({MEAS["date"]},', 10, sk.TXT2)
    s.text(40, 752, "живий вузол у коробці) — не з паспорта", 10, sk.TXT2)
    s.text(40, 770, f'модель дає ~{MODEL_IDLE_W:.2f} Вт спокою (близько,', 10, sk.TXT2)
    s.text(40, 788, "різниця — втрати, яких нема в розрахунку).", 10, sk.TXT2)

    # довжина кабелю в даних позначена як прикидка (FEED["note"]), не звірена по місцю
    est = " (прикидка)" if "прикидка" in FEED.get("note", "") else ""
    s.footnote(f'Ліміт авто-порту станції {LIMIT_W:g} Вт / {LIMIT_A:g} А — вузол '
               f'на піку бере ~{NODE_PEAK_W:.0f} Вт, запас у {LIMIT_W / NODE_PEAK_W:.0f}× '
               f'з гаком. Запобіжник стоїть двічі поспіль тим самим номіналом '
               f'{FUSE_A:g} А: у штекері прикурювача і ще раз у гермовводі коробки.')
    s.footnote(f'Кабель AWG{CABLE_AWG}, ~{CABLE_M:g} м{est} — власний, окремий від щита '
               f'світла; довжину міряти по місцю (рішення Івана 29.07).')
    s.footnote(f'Заміряний холостий хід {MEAS["node_w"]:g} Вт ({MEAS["date"]}) — '
               f'{MEAS["how"]}.')
    s.footnote(f'Підсилювач у монтажі {AMP_NOTE}.')
    s.footnote("Сигнальний тракт (ЦАП→підсилювач→динамік) — окрема схема "
               "audio/model/schematic.svg, тут лише живлення.")
    return s


if __name__ == "__main__":
    build().write(HERE / "power_chain.svg")
