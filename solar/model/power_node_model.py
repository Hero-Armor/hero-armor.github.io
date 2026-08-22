#!/usr/bin/env python3
"""
Hero Armor power node — EcoFlow station + self-built solar array.

One station feeds BOTH consumers (light and sound). This node owns everything
about generation and storage; the consumer nodes own only their own draw and
export demand() / composite_day(). Swap the EcoFlow model here and no light
calculation changes.

The station is treated as swappable by design: if the panels die or the station
drains, it gets pulled and a charged one takes its place while the first goes
back to base for an AC top-up. So the questions this node answers are:

  1. does the array cover a day, with what margin
  2. how long does a full station last with no sun at all (= swap deadline)
  3. how long does the pulled station need on the wall before it can go back

Stdlib only — CI builds the site without deps.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = Path(__file__).resolve().parent.parent / "data"
sys.path.insert(0, str(ROOT / "lights" / "model"))
sys.path.insert(0, str(ROOT / "audio" / "model"))
import lights_node_model as lights  # noqa: E402
import audio_node_model as audio  # noqa: E402

P = json.loads((DATA / "params.json").read_text())
CASES_DOC = json.loads((DATA / "cases.json").read_text())

PLAYA = P["playa"]
ST = P["station"]
STATIONS = P["stations"]


def station(name=None):
    name = name or P["station_chosen"]
    return name, STATIONS[name]


def panel_yield_wh(panel_w, sun_factor=1.0):
    """Wh a self-built array actually delivers into the station on the playa."""
    return (panel_w * PLAYA["sun_hours"] * PLAYA["dust_derate"]
            * PLAYA["heat_derate"] * PLAYA["cable_derate"] * sun_factor)


def accepted_panel_w(panel_w, st):
    """Anything above the station's solar input ceiling is simply not taken."""
    return min(panel_w, st["solar_in_w"])


def demand(light_case=None):
    """What the consumers ask of the station, per day.

    light_case picks one lights scenario for the whole night; None uses the
    weighted composite night. Audio is a flat 24h load either way.
    """
    audio_wh, _ = audio.composite_day()
    if light_case:
        _, res = lights.composite_night()
        r = res[light_case]
        lights_wh = r["draw_w"] * r["hours"]
    else:
        lights_wh = lights.demand()["wh_per_day"]
    standby_wh = ST["standby_w"] * 24
    return dict(lights=lights_wh, audio=audio_wh, standby=standby_wh,
                total=lights_wh + audio_wh + standby_wh)


def run_case(c, panel_w=None, station_name=None):
    name, st = station(station_name)
    panel_w = P["panel"]["chosen_w"] if panel_w is None else panel_w

    d = demand(c.get("light_case"))
    used_w = accepted_panel_w(panel_w, st)
    gen = panel_yield_wh(used_w, c["sun_factor"])

    usable = st["wh"] * ST["usable_frac"]
    reserve = usable * ST["reserve_frac"]
    workable = usable - reserve

    net = gen - d["total"]
    # days a full station survives once generation no longer covers the draw
    days_to_swap = workable / -net if net < 0 else float("inf")

    return dict(
        case=c["name"], key=c["key"], station=name,
        panel_w=panel_w, panel_used_w=used_w, panel_wasted_w=panel_w - used_w,
        gen_wh=gen, demand_wh=d["total"], demand=d,
        balance_wh=net, usable_wh=usable, reserve_wh=reserve, workable_wh=workable,
        days_to_swap=days_to_swap,
        recharge_h=usable / min(st["ac_in_w"], P["base"]["ac_charge_w"]))


def dc12_headroom(station_name=None, peak_w=None):
    """Чи влізає піковий струм світла у 12-вольтовий вихід станції.

    Відкрилось при звірці мануалів 29.07: у ВСІХ моделей EcoFlow 12 В обмежені
    126 Вт / 10 А (гніздо прикурювача ділить ліміт із двома DC5521 по 38 Вт).
    Ємність станції на це не впливає. Виняток — Delta Pro: порт Anderson
    12.6 В 30 А = 378 Вт. Тому вибір станції тепер залежить не лише від Wh,
    а й від того, чи пролізе пік по 12 В.
    """
    name, st = station(station_name)
    limit = max(st.get("dc12_total_w", 126), st.get("anderson_w", 0))
    if peak_w is None:
        import lights_node_model as _lm
        _, res = _lm.composite_night()
        peak_w = max(r["draw_w"] for r in res.values())
    return dict(station=name, peak_w=peak_w, limit_w=limit,
                port="Anderson" if st.get("anderson_w") else "12V DC (прикурювач)",
                fits=peak_w <= limit, headroom_w=limit - peak_w,
                peak_a=peak_w / 12.0, limit_a=limit / 12.6)


def break_even_panel_w(light_case=None):
    """Array size that exactly covers a day — before the station's input ceiling."""
    d = demand(light_case)
    per_w = panel_yield_wh(1.0)
    return d["total"] / per_w


def station_options(panel_w=None):
    """Every station against the composite day: does it hold, for how long."""
    panel_w = P["panel"]["chosen_w"] if panel_w is None else panel_w
    d = demand()
    out = []
    for name, st in STATIONS.items():
        used = accepted_panel_w(panel_w, st)
        gen = panel_yield_wh(used)
        usable = st["wh"] * ST["usable_frac"]
        workable = usable * (1 - ST["reserve_frac"])
        net = gen - d["total"]
        out.append(dict(
            name=name, wh=st["wh"], solar_in_w=st["solar_in_w"],
            panel_used_w=used, gen_wh=gen, balance_wh=net,
            nights_no_sun=workable / d["total"],
            days_to_swap=workable / -net if net < 0 else float("inf"),
            recharge_h=usable / min(st["ac_in_w"], P["base"]["ac_charge_w"])))
    return out



def generator():
    """Генератор як джерело: скільки бензину і як часто заливати.

    Питання Івана 22.08.2026: «як часто заливати, враховуючи наше маленьке
    споживання» і «чи зекономить вихід 12 В».

    Головна пастка тут не в арифметиці, а в режимі. Генератор жере паливо за
    ОБЕРТИ, а не за віддані вати. Якщо тримати його ввімкненим цілу добу заради
    наших ~34 Вт середніх, платимо за холостий хід — це в рази дорожче, ніж
    зарядити станцію ривком і заглушити.
    """
    G = P["generator"]
    d = demand()
    gal_per_h_at_25 = G["tank_gal"] / G["runtime_h_25pct_gas"]

    # Режим А — генератор годує інсталяцію напряму, цілу добу.
    lo, hi = G["idle_gal_per_h_est"]
    mid = gal_per_h_at_25 * G["idle_ratio_of_25pct"]
    direct = {"gal_day": (lo * 24, hi * 24), "gal_h_mid": mid,
              "hours_per_tank": (G["tank_gal"] / hi, G["tank_gal"] / lo),
              "hours_per_tank_mid": G["tank_gal"] / mid,
              "refuels_day": (lo * 24 / G["tank_gal"], hi * 24 / G["tank_gal"])}

    # Режим Б — генератор ривком заряджає станцію, станція годує інсталяцію.
    into_battery = d["total"] / G["charge_eff"]
    hours = into_battery / G["charge_w"]
    # Паливо рахуємо через ЕНЕРГІЮ, а не через години: за годину на 1100 Вт мотор
    # віддає більше, ніж за годину на 800 Вт, тому множити години на витрату для
    # 25% навантаження — це занижувати. Перший варіант так і зробив і дав 10 діб
    # на бак замість 7.3, розійшовшись із енергетичним рахунком на тій же сторінці.
    gal_per_wh = G["tank_gal"] / (G["runtime_h_25pct_gas"] * G["load_at_25pct_w"])
    gal_day = into_battery * gal_per_wh
    burst = {"hours": hours, "gal_day": gal_day,
             "days_per_tank": G["tank_gal"] / gal_day}

    # Пропан тим самим режимом: рахуємо енергію, яку віддає один балон 20 фунтів.
    lpg_wh_per_tank = G["runtime_h_25pct_lpg20lb"] * G["load_at_25pct_w"]
    gas_wh_per_tank = G["runtime_h_25pct_gas"] * G["load_at_25pct_w"]
    fuels = {"пропан 20 фунтів": lpg_wh_per_tank / into_battery,
             f"бензин {G['tank_gal']} гал": gas_wh_per_tank / into_battery}
    return dict(gal_per_h_at_25=gal_per_h_at_25, direct=direct, burst=burst,
                fuels=fuels, into_battery=into_battery)


def _selfcheck():
    """Одна перевірка, що ловить головне: ривковий режим мусить бути в рази
    економнішим за цілодобовий, інакше в моделі помилка знаку або одиниць."""
    g = generator()
    assert g["burst"]["gal_day"] * 5 < g["direct"]["gal_day"][0], \
        "ривковий режим має бути щонайменше вп'ятеро економнішим"
    assert 5 < g["burst"]["days_per_tank"] < 30, "діб на бак вийшло неправдоподібно"
    # Центр діапазону холостого ходу мусить лежати ВСЕРЕДИНІ самого діапазону,
    # інакше коефіцієнт і межі розʼїхались при черговій правці даних.
    _lo, _hi = P["generator"]["idle_gal_per_h_est"]
    assert _lo <= g["direct"]["gal_h_mid"] <= _hi, "центр холостого ходу випав з діапазону"
    # Два способи порахувати «скільки діб дає бак» мусять збігатись: через паливо
    # за добу і через енергію на бак. Розбіжність = помилка в обліку годин.
    assert abs(g["burst"]["days_per_tank"] - g["fuels"]["бензин 1.48 гал"]) < 0.1, \
        "рахунок по паливу і по енергії розійшлись"
    assert P["generator"]["has_12v_power_socket"] is False
    return True


def main():
    d = demand()
    name, st = station()
    print(f"Споживачі за добу: світло {d['lights']:.0f} + звук {d['audio']:.0f} "
          f"+ холостий хід станції {d['standby']:.0f} = {d['total']:.0f} Wh")
    print(f"Панель {P['panel']['chosen_w']} Вт -> у станцію заходить "
          f"{accepted_panel_w(P['panel']['chosen_w'], st)} Вт "
          f"(ліміт входу {name}: {st['solar_in_w']} Вт)")
    print(f"Панель в нуль: ~{break_even_panel_w():.0f} Вт\n")

    hdr = f"{'Сценарій':30} {'сонце':>6} {'дає':>7} {'жере':>7} {'баланс':>8} {'до підміни':>12}"
    print(hdr)
    print("-" * len(hdr))
    for c in CASES_DOC["cases"]:
        r = run_case(c)
        swap = "—" if r["days_to_swap"] == float("inf") else f"{r['days_to_swap']:.1f} діб"
        print(f"{r['case']:30} {c['sun_factor']*100:5.0f}% {r['gen_wh']:6.0f} "
              f"{r['demand_wh']:6.0f} {r['balance_wh']:+7.0f} {swap:>12}")

    print(f"\nСтанції під панель {P['panel']['chosen_w']} Вт "
          f"(композитна доба {d['total']:.0f} Wh):")
    for s in station_options():
        swap = "тримає" if s["days_to_swap"] == float("inf") else f"{s['days_to_swap']:.1f} діб"
        cap = "" if s["panel_used_w"] >= P["panel"]["chosen_w"] else \
              f"  [бере лише {s['panel_used_w']:.0f} Вт з панелі]"
        print(f"  {s['name']:14} {s['wh']:5} Wh  баланс {s['balance_wh']:+6.0f} Wh  "
              f"без сонця {s['nights_no_sun']:4.1f} діб  підміна {swap:>10}  "
              f"зарядка {s['recharge_h']:4.1f} год{cap}")

    G, g = P["generator"], generator()
    print(f"\n=== ГЕНЕРАТОР: {G['model']} ===")
    print(f"Бак {G['tank_gal']} гал · на 25% навантаження (800 Вт) {G['runtime_h_25pct_gas']} год "
          f"-> {g['gal_per_h_at_25']:.3f} гал/год")
    lo, hi = g["direct"]["gal_day"]
    rlo, rhi = g["direct"]["refuels_day"]
    hlo, hhi = g["direct"]["hours_per_tank"]
    print(f"А. Годує інсталяцію ЦІЛОДОБОВО: {lo:.1f}-{hi:.1f} гал/добу, "
          f"тобто заливати {rlo:.1f}-{rhi:.1f} разів на день  [холостий хід — ОЦІНКА за аналогом]")
    print(f"   На ОДНОМУ баку на холостому ходу: {hhi:.0f}-{hlo:.0f} год "
          f"(центр {g['direct']['hours_per_tank_mid']:.0f} год) при {g['direct']['gal_h_mid']:.3f} гал/год")
    b = g["burst"]
    print(f"Б. Ривком заряджає станцію:     {b['gal_day']:.2f} гал/добу "
          f"({b['hours']*60:.0f} хв роботи), одного бака вистачає на {b['days_per_tank']:.1f} діб")
    for fuel, days in g["fuels"].items():
        print(f"   один {fuel:18} = {days:.0f} діб інсталяції")
    print(f"12 В: {G['dc_output']} — {G['_dc_note'][:60]}...")
    assert _selfcheck()


if __name__ == "__main__":
    main()
