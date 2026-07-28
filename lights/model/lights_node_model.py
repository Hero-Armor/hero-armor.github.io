#!/usr/bin/env python3
"""
Hero Armor lights node — system-level model, driven by ../data/params.json + cases.json.

Bus: LiFePO4 24V -> Victron MPPT + LVD -> three groups
  g1  прожектори заливки (MR16 12V через ШІМ-диммер, voltage-following)
  g2  декоративне: лампи робота + адресна «біжуча вода» + контролер WLED
  g3a аварійна лінія: габаритні вогні + сходи (окремий поріг LVD 22.2В)

All constants live in lights/data/params.json; playa scenarios in cases.json.
This module is the single computation source for the CLI table AND the dashboard
(site/build.py imports it). Stdlib only — CI builds the site without deps.
"""

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
P = json.loads((DATA / "params.json").read_text())
CASES_DOC = json.loads((DATA / "cases.json").read_text())

BUS_V = P["bus_v"]
VF = P["voltage_following"]
ADDR = P["addressable"]
WIRE = P["wiring"]
BATT = P["battery"]
SOL = P["solar"]
PHOTO = P["photometry"]
GROUPS = P["groups"]


def spot_ratios(v_spot):
    """MR16 without a regulator: I ~ V, so P ~ V², luminous flux ~ I ~ V.

    Below the LED forward-voltage floor the lamp simply goes dark."""
    if v_spot < VF["v_min"]:
        return 0.0, 0.0
    v = min(v_spot, VF["v_max"])
    ratio = v / VF["v_nominal"]
    return ratio ** VF["power_exponent"], ratio


def fixture_power(f, case):
    """Watts drawn by one fixture line under a case's dimming settings."""
    grp = f["group"]
    if grp == "g1":
        p_ratio, _ = spot_ratios(case["v_spot"])
        return f["qty"] * f["w_unit"] * p_ratio

    dim = case["dim_g3a"] if grp == "g3a" else case["dim_g2"]
    if f.get("addressable"):
        full = f["qty"] * f["length_m"] * f["w_per_m"]
        return full * ADDR["duty_animation"] * dim
    if f["dimming"] == "none":
        # not dimmable: it is either on or off
        return f["qty"] * f["w_unit"] * (1.0 if dim > 0 else 0.0)
    return f["qty"] * f["w_unit"] * dim


def fixture_peak(f):
    """Nameplate watts — everything on, animation ignored (architect's basis)."""
    if f.get("addressable"):
        return f["qty"] * f["length_m"] * f["w_per_m"]
    return f["qty"] * f["w_unit"]


def group_watts(case):
    g = {k: 0.0 for k in GROUPS}
    for f in P["fixtures"]:
        g[f["group"]] += fixture_power(f, case)
    return g


def peak_watts():
    g = {k: 0.0 for k in GROUPS}
    for f in P["fixtures"]:
        g[f["group"]] += fixture_peak(f)
    return g


def wiring_losses(g_watts):
    """Per-run current, round-trip resistance, voltage drop and copper loss."""
    runs = []
    for r in WIRE["runs"]:
        load_w = sum(g_watts[k] for k in r["groups"])
        i = load_w / BUS_V
        res = 2 * r["length_m"] * WIRE["awg_ohm_per_m"][str(r["awg"])]
        v_drop = i * res
        runs.append(dict(id=r["id"], label=r["label"], awg=r["awg"],
                         length_m=r["length_m"], load_w=load_w, amps=i,
                         ohm=res, v_drop=v_drop, drop_pct=100 * v_drop / BUS_V,
                         loss_w=i * i * res))
    return runs


def solar_yield(sun_factor=1.0, panel_w=None):
    panel_w = SOL["panel_w"] if panel_w is None else panel_w
    return (panel_w * SOL["sun_hours"] * SOL["mppt_eff"]
            * SOL["dust_derate"] * SOL["heat_derate"] * sun_factor)


def run_case(c):
    g = group_watts(c)
    runs = wiring_losses(g)
    load_w = sum(g.values())
    loss_w = sum(r["loss_w"] for r in runs)
    draw_w = load_w + loss_w
    wh_night = draw_w * c["hours"]

    _, lm_ratio = spot_ratios(c["v_spot"])
    spot = next(f for f in P["fixtures"] if f["id"] == "spot")
    lumens = spot["qty"] * spot["lumens"] * lm_ratio
    lux = lumens * PHOTO["utilization"] / PHOTO["figure_area_m2"]

    gen_wh = solar_yield(c["sun_factor"])
    usable_wh = BATT["ah"] * BATT["v_nom"] * BATT["dod"]

    return dict(
        case=c["name"], key=c["key"], hours=c["hours"],
        g1=g["g1"], g2=g["g2"], g3a=g["g3a"],
        load_w=load_w, loss_w=loss_w, draw_w=draw_w, wh_night=wh_night,
        amps=draw_w / BUS_V, lumens=lumens, lux=lux,
        lux_margin=lux - PHOTO["target_lux"],
        worst_drop_pct=max(r["drop_pct"] for r in runs),
        gen_wh=gen_wh, balance_wh=gen_wh - wh_night,
        nights=usable_wh / wh_night if wh_night else float("inf"),
        runs=runs)


def composite_night():
    """Weighted playa night from cases.json. Returns (Wh/night, results by key)."""
    results = {r["key"]: r for r in (run_case(c) for c in CASES_DOC["cases"])}
    wh = sum(results[k]["draw_w"] * h for k, h in CASES_DOC["composite_night"].items())
    return wh, results


def energy_balance(wh_night):
    """Autonomy per battery option + panel size needed to break even."""
    usable = {name: ah * BATT["v_nom"] * BATT["dod"] for name, ah in BATT["models_ah"].items()}
    nights = {name: wh / wh_night for name, wh in usable.items()}
    per_w = solar_yield(1.0, panel_w=1.0)
    return dict(
        wh_night=wh_night, nights=nights,
        usable_wh=BATT["ah"] * BATT["v_nom"] * BATT["dod"],
        solar_need_w=wh_night / per_w,
        gen_wh=solar_yield(), legacy_gen_wh=solar_yield(panel_w=SOL["legacy_panel_w"]),
        balance_wh=solar_yield() - wh_night)


def main():
    hdr = (f"{'Case':28} {'Гр.1':>6} {'Гр.2':>6} {'Гр.3А':>6} {'Разом':>7} "
           f"{'Wh/ніч':>7} {'lux':>6} {'просад':>7} {'баланс':>8}")
    print(hdr)
    print("-" * len(hdr))
    for c in CASES_DOC["cases"]:
        r = run_case(c)
        flag = " !!" if r["balance_wh"] < 0 else ""
        print(f"{r['case']:28} {r['g1']:5.1f}W {r['g2']:5.1f}W {r['g3a']:5.1f}W "
              f"{r['draw_w']:6.1f}W {r['wh_night']:7.0f} {r['lux']:6.0f} "
              f"{r['worst_drop_pct']:6.2f}% {r['balance_wh']:+7.0f}{flag}")

    pk = peak_watts()
    ref = P["spec_reference"]
    print(f"\nПік за паспортом: Гр.1 {pk['g1']:.0f}W · Гр.2 {pk['g2']:.0f}W · "
          f"Гр.3А {pk['g3a']:.0f}W · разом {sum(pk.values()):.0f}W")
    print(f"  (розрахунок архітектора: {ref['architect_groups_w']} → "
          f"{ref['architect_peak_w']}W / {ref['architect_night_wh']} Wh)")

    wh, _ = composite_night()
    b = energy_balance(wh)
    print(f"\nКомпозитна ніч: {wh:.0f} Wh")
    for name, n in b["nights"].items():
        print(f"  АКБ {name:8} -> {n:4.1f} ночей без сонця")
    print(f"  Панель {SOL['panel_w']}W дає {b['gen_wh']:.0f} Wh/добу -> баланс {b['balance_wh']:+.0f} Wh")
    print(f"  Попередня панель {SOL['legacy_panel_w']}W дала б {b['legacy_gen_wh']:.0f} Wh -> "
          f"{b['legacy_gen_wh'] - wh:+.0f} Wh")
    print(f"  Панель в нуль: ~{b['solar_need_w']:.0f} W")

    print("\nПросадка в лініях (worst case — усе на повну):")
    for r in wiring_losses(peak_watts()):
        print(f"  {r['label']:32} AWG{r['awg']:<3} {r['length_m']:5.1f}m "
              f"{r['amps']:5.1f}A  −{r['v_drop']:.2f}V ({r['drop_pct']:.2f}%)  "
              f"втрати {r['loss_w']:.1f}W")


if __name__ == "__main__":
    main()
