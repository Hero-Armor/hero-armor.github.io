#!/usr/bin/env python3
"""Ядро на спині робота — модуль адресних світлодіодів за друкованим вікном.

Рахує три речі, які й вирішують, що замовляти і що друкувати:

  1. крок між діодами в обраному модулі і чи зіллються вони в рівне світло
     при заданому зазорі до вікна (правило зазор >= крок);
  2. скільки бере модуль — на суцільному білому (стеля, до якої не доходить)
     і в робочому переливі; звідси струм і чи треба понижувач з 12 В;
  3. яке вікно друкувати: матеріал, товщина, налаштування друку.

Дані — lights/data/back_core.json. Stdlib only: CI збирає сайт без залежностей.
"""

import json
import math
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
D = json.loads((DATA / "back_core.json").read_text())
P = json.loads((DATA / "params.json").read_text())

BUS_V = P["bus_v"]
WIN = D["window"]
DIF = D["diffuser"]
UNI = D["uniformity"]
MODS = D["modules"]
CTRL = D["controllers"]


def module(key=None):
    key = key or D["chosen"]["module"]
    return next(m for m in MODS if m["key"] == key)


def controller(key=None):
    key = key or D["chosen"]["controller"]
    return next(c for c in CTRL if c["key"] == key)


def pitch_mm(m, size_mm=None):
    """Distance between neighbouring diodes on the module, in mm.

    Кільце: діоди сидять по колу, тому крок — це довжина кола на кількість.
    Матриця: крок — це сторона, поділена на проміжки між рядами."""
    size = size_mm or m["size_mm"]
    if m["form"] == "ring":
        return math.pi * size / m["diodes"]
    side = int(round(math.sqrt(m["diodes"])))
    return size / (side - 1) if side > 1 else size


def uniformity(m=None, gap_mm=None, size_mm=None):
    """Чи зіллються крапки в рівне світло при цьому зазорі."""
    m = m or module()
    gap = DIF["gap_mm"] if gap_mm is None else gap_mm
    p = pitch_mm(m, size_mm)
    ratio = gap / p if p else 0
    if ratio >= UNI["comfort_ratio"]:
        verdict, level = "рівне світло", "good"
    elif ratio >= UNI["min_ratio"]:
        verdict, level = "крапки вгадуються — рятує товще вікно", "warn"
    else:
        verdict, level = "видно окремі діоди", "crit"
    return dict(pitch_mm=p, gap_mm=gap, ratio=ratio, verdict=verdict, level=level)


def watts(m=None, duty=None, brightness=1.0):
    """Споживання модуля: стеля на суцільному білому і робоча картинка.

    Адресні модулі рахуються не «скільки в паспорті», а скільки з них у цю мить
    світиться: перелив запалює частину діодів і не на повну — так само, як комета
    на подіумній стрічці бере 3.6% від суцільної заливки."""
    m = m or module()
    duty = D["chosen"]["duty_animation"] if duty is None else duty
    full = m["diodes"] * m["w_diode"]
    work = full * duty * brightness
    eff = CTRL["_buck_eff"] if isinstance(CTRL, dict) else None
    return dict(full_w=full, work_w=work, duty=duty,
                full_a_module=full / m["v"], work_a_module=work / m["v"])


def draw_from_bus(m=None, duty=None, brightness=1.0):
    """Скільки це коштує 12-вольтовій шині — з урахуванням понижувача і контролера.

    Модуль на 5 В живиться через понижувач, і той бере своє: на 12 В струм
    менший, ніж на 5 В, але ватти додаються, а не зникають."""
    m = m or module()
    c = controller()
    w = watts(m, duty, brightness)
    buck = D["buck"]["efficiency"] if m["v"] != BUS_V else 1.0
    bus_full = w["full_w"] / buck + c["w_idle"]
    bus_work = w["work_w"] / buck + c["w_idle"]
    return dict(needs_buck=m["v"] != BUS_V, buck_eff=buck,
                ctrl_w=c["w_idle"],
                full_w=bus_full, work_w=bus_work,
                full_a=bus_full / BUS_V, work_a=bus_work / BUS_V,
                wh_night=bus_work * D["chosen"]["night_h"], **w)


def night_wh(m=None, duty=None, brightness=1.0):
    return draw_from_bus(m, duty, brightness)["wh_night"]


def diffuser_pick():
    """Матеріали вікна, від «не можна» до «беремо»."""
    order = {"best": 0, "ok": 1, "alt": 2, "no": 3}
    return sorted(DIF["materials"], key=lambda x: order[x["verdict"]])


def print_brief(size_mm=None, shape=None):
    """ТЗ друкарю одним обʼєктом — рівно те, що треба продиктувати Марселю."""
    size = size_mm or WIN["size_mm"]
    shape = shape or WIN["shape"]
    sp = DIF["print_spec"]
    mat = next(x for x in DIF["materials"] if x["verdict"] == "best")
    alt = next(x for x in DIF["materials"] if x["verdict"] == "ok")
    ban = next(x for x in DIF["materials"] if x["verdict"] == "no")
    m = module()
    return dict(
        shape=shape, size_mm=size, bezel_mm=WIN["bezel_mm"],
        thickness_mm=DIF["thickness_mm"], gap_mm=DIF["gap_mm"],
        material=mat["name"], material_alt=alt["name"], material_ban=ban["name"],
        walls=sp["walls"], layer_mm=sp["layer_mm"], infill_pct=sp["infill_pct"],
        finish=sp["top_bottom"],
        seat_mm=m["size_mm"], seat_form=m["form"],
        uniformity=uniformity(m, size_mm=size))


def summary():
    m, c = module(), controller()
    b = draw_from_bus()
    u = uniformity(m)
    return dict(module=m, controller=c, bus=b, uniformity=u,
                window=WIN, thickness_mm=DIF["thickness_mm"])


if __name__ == "__main__":
    s = summary()
    m, b, u = s["module"], s["bus"], s["uniformity"]
    print(f'модуль: {m["name"]} — {m["diodes"]} діодів, {m["v"]:.0f} В, Ø{m["size_mm"]} мм')
    print(f'крок {u["pitch_mm"]:.1f} мм, зазор {u["gap_mm"]:.0f} мм → '
          f'{u["ratio"]:.2f} ({u["verdict"]})')
    print(f'суцільний білий {b["full_w"]:.1f} Вт, перелив {b["work_w"]:.1f} Вт '
          f'({b["work_a"]:.2f} A з шини), за ніч {b["wh_night"]:.0f} Wh')
    print(f'вікно: {s["window"]["shape"]} {s["window"]["size_mm"]} мм, '
          f'{s["thickness_mm"]} мм товщиною')
