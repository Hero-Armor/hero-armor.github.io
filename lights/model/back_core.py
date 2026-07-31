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
    Матриця: крок — це сторона, поділена на проміжки між рядами.
    Набір вкладених кілець рахувати так не можна (241 діод сидить на девʼяти
    колах, а не на одному) — у нього крок стоїть у базі числом."""
    if m.get("pitch_mm"):
        return m["pitch_mm"]
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


def watts(m=None, duty=None, brightness=1.0, limit_a=None):
    """Споживання модуля: стеля на суцільному білому і робоча картинка.

    Адресні модулі рахуються не «скільки в паспорті», а скільки з них у цю мить
    світиться: перелив запалює частину діодів і не на повну — так само, як комета
    на подіумній стрічці бере 3.6% від суцільної заливки.

    Ліміт струму в прошивці ріже і те, і те: WLED сам притишує картинку, щойно
    вона намагається взяти більше дозволеного. Тому стеля модуля — це не паспорт
    плати, а виставлене нами число ампер."""
    m = m or module()
    duty = D["chosen"]["duty_animation"] if duty is None else duty
    limit_a = D["chosen"]["current_limit_a"] if limit_a is None else limit_a
    cap = limit_a * m["v"] if limit_a else float("inf")
    full = m["diodes"] * m["w_diode"]
    work = min(full * duty * brightness, cap)
    return dict(full_w=full, work_w=work, duty=duty,
                cap_w=cap, capped=full * duty * brightness > cap,
                full_a_module=full / m["v"], work_a_module=work / m["v"])


def draw_from_bus(m=None, duty=None, brightness=1.0, limit_a=None, ctrl=None):
    """Скільки це коштує 12-вольтовій шині — з урахуванням понижувача і контролера.

    Модуль на 5 В живиться через понижувач, і той бере своє: на 12 В струм
    менший, ніж на 5 В, але ватти додаються, а не зникають."""
    m = m or module()
    c = ctrl or controller()
    w = watts(m, duty, brightness, limit_a)
    buck = D["buck"]["efficiency"] if m["v"] != BUS_V else 1.0
    peak_w = min(w["full_w"], w["cap_w"])
    bus_peak = peak_w / buck + c["w_idle"]
    bus_work = w["work_w"] / buck + c["w_idle"]
    return dict(w, needs_buck=m["v"] != BUS_V, buck_eff=buck,
                ctrl_w=c["w_idle"],
                peak_w=bus_peak, work_w=bus_work,
                peak_a=bus_peak / BUS_V, work_a=bus_work / BUS_V,
                wh_night=bus_work * D["chosen"]["night_h"])


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
    print(f'суцільний білий {b["full_w"]:.1f} Вт (ліміт прошивки ріже до {b["cap_w"]:.1f}), '
          f'перелив {b["work_w"]:.1f} Вт ({b["work_a"]:.2f} A з шини), '
          f'за ніч {b["wh_night"]:.0f} Wh')
    print(f'вікно: {s["window"]["shape"]} {s["window"]["size_mm"]} мм, '
          f'{s["thickness_mm"]} мм товщиною')
