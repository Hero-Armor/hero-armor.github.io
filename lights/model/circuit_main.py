#!/usr/bin/env python3
"""
Загальна схема електрики світла: від станції до трьох груп.

Замінює стару схему на schemdraw, де дроти обривались у повітря, а підпис
«12V» лежав поверх лінії (Іван, 07.08.2026). Тут кожен дріт зʼєднує два порти,
і `schema_kit.verify()` не дасть записати файл, якщо щось висить.

Це верхній рівень: станція → головний запобіжник → щит → три групи. Що
всередині кожної групи — на окремих схемах (circuit_g1 / circuit_g2_strip /
circuit_g3a), сюди вони не лізуть, щоб аркуш лишався читабельним.

Числа — з lights_node_model (cable_tree, fuses, peak_watts) і params.json.
Тільки stdlib.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lights_node_model as lnm            # noqa: E402
import schema_kit as sk                    # noqa: E402

P = json.loads((HERE.parent / "data" / "params.json").read_text())
GROUPS = P["groups"]
TREE = {r["id"]: r for r in lnm.cable_tree()}
FUSE = {f["id"]: f["rating"] for f in lnm.fuses()}
PEAK = lnm.peak_watts()
BUS_V = P["bus_v"]

TRUNK = TREE["trunk"]


def build():
    total = sum(PEAK.values())
    s = sk.Sheet(
        1240, 780,
        "Світло цілком — від станції до трьох груп",
        f'шина {BUS_V:.0f} В · пік {total:.0f} Вт · головний запобіжник '
        f'{FUSE["main"]:g} А · магістраль {TRUNK["cable"]}, {TRUNK["length_m"]:.1f} м',
        "Три групи окремі, кожна зі своїм запобіжником і своїм реле — щоб гасити "
        "їх по черзі, коли станція сідає.")

    st = s.block(40, 190, 190, 130, "Станція EcoFlow",
                 f'вихід {BUS_V:.0f} В\nсиловий розʼєм 30 А\n(не прикурювач)',
                 color=sk.INK, bg=sk.PANEL_BG)
    st_out = st.port("dc", "r", 0.5)

    fuse = s.block(350, 215, 130, 80, f'{FUSE["main"]:g} А',
                   "головний\nзапобіжник", color=sk.WARN)
    f_in = fuse.port("in", "l", 0.5)
    f_out = fuse.port("out", "r", 0.5)

    panel = s.block(600, 150, 210, 210, "Щит подіуму",
                    "4 запобіжники\n3 групові реле 12 В / 30 А\nпост контролю: "
                    "ватметри\nі тумблери\nу гермокоробці IP66",
                    color=sk.INK, bg=sk.PANEL_BG)
    p_in = panel.port("in", "l", 0.5)

    s.wire(st_out, f_in, sk.POS, 2.6, label="магістраль світла")
    s.wire(f_out, p_in, sk.POS, 2.6,
           label=f'{TRUNK["length_m"]:.1f} м · {TRUNK["amps"]:.1f} А · '
                 f'−{TRUNK["drop_pct"]:.1f}%')

    rows = [
        ("g1", sk.G1, "Гр.1 · прожектори заливки",
         "8 × MR16 через ШІМ-диммер", "circuit_g1"),
        ("g2", sk.G2, "Гр.2 · декор",
         "стрічка подіуму, лампи робота,\nядро на спині — через WLED", "circuit_g2_strip"),
        ("g3a", sk.G3, "Гр.3А · аварійна лінія",
         "24 врізні вогні торця\n+ 2 маркери ящика", "circuit_g3a"),
    ]
    ys = [140, 320, 500]
    for (gid, color, title, sub, sheet_name), gy in zip(rows, ys):
        blk = s.block(880, gy, 320, 120, title,
                      f'{sub}\n{PEAK[gid]:.0f} Вт · запобіжник {FUSE[gid]:g} А',
                      color=color)
        frac = min(max((gy + 60 - 150) / 210, 0.12), 0.88)
        s.wire(panel.port(gid, "r", frac), blk.port("in", "l", 0.5), color, 2.2)

    s.text(40, 400, "Що НЕ на цій схемі", 12, sk.INK, weight="bold")
    for i, line in enumerate([
            "Звук живиться окремим кабелем прямо",
            "з авто-виходу станції — повз цей щит",
            "і повз групові реле, щоб не гаснути",
            "разом зі світлом.",
            "",
            "Що всередині кожної групи — на своїх",
            "схемах: кільце прожекторів, стрічка",
            "подіуму, аварійна лінія, лампи по тілу",
            "робота і ядро на спині.",
    ]):
        s.text(40, 424 + i * 17, line, 10, sk.TXT2)

    s.text(40, 610, "Чому три групи, а не одна", 12, sk.INK, weight="bold")
    for i, line in enumerate([
            "Коли станція сідає, гасимо по черзі:",
            "першим декор (найдорожчий по ватах),",
            "другою заливку фігури, а аварійну",
            "тримаємо найдовше — щоб уночі ніхто",
            "не наштовхнувся на подіум.",
    ]):
        s.text(40, 634 + i * 17, line, 10, sk.TXT2)

    s.footnote(f'Земля — зіркою в одній точці біля щита. Все обладнання в тінь, '
               f'зазор від землі 5+ см.')
    s.footnote(f'Фотореле з проєкту прибрано 29.07 — чим вмикати Гр.1 і Гр.3А по темряві, '
               f'ще не обрано: ручний тумблер у щиті або вихід WLED.')
    s.footnote(f'Довжина магістралі {TRUNK["length_m"]:.1f} м — прикидка, з креслення не '
               f'знята; просадка на ній −{TRUNK["drop_pct"]:.1f}% при межі '
               f'{P["wiring"]["drop_crit_pct"]:.0f}%.')
    return s


if __name__ == "__main__":
    build().write(HERE / "circuit_main.svg")
