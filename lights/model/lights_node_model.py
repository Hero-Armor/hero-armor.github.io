#!/usr/bin/env python3
"""
Hero Armor lights node — how much the light actually eats. 12V bus.

  g1  прожектори заливки (MR16 через ШІМ-диммер, voltage-following)
  g2  декоративне: лампи робота + адресна «біжуча вода» + контролер WLED
  g3a аварійна лінія: габаритні вогні + сходи — не регулюється, горить рівно

This node is a pure CONSUMER: it knows nothing about batteries, panels or
autonomy. Generation and storage live in the power node (solar/), which imports
demand() from here. Keeping the split means changing the EcoFlow model never
touches the light calculation, and vice versa.

All constants live in lights/data/params.json; night scenarios in cases.json.
Stdlib only — CI builds the site without deps.
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



def min_awg(run, g_watts):
    """Thinnest stocked gauge that keeps this run under the critical drop."""
    i = sum(g_watts[k] for k in run["groups"]) / BUS_V
    limit = WIRE["drop_crit_pct"] / 100 * BUS_V
    ok = [int(a) for a, ohm in sorted(WIRE["awg_ohm_per_m"].items(), key=lambda x: -int(x[0]))
          if i * 2 * run["length_m"] * ohm <= limit]
    return max(ok) if ok else None


def run_case(c):
    g = group_watts(c)
    runs = wiring_losses(g)
    load_w = sum(g.values())
    loss_w = sum(r["loss_w"] for r in runs)
    draw_w = load_w + loss_w

    _, lm_ratio = spot_ratios(c["v_spot"])
    spot = next(f for f in P["fixtures"] if f["id"] == "spot")
    lumens = spot["qty"] * spot["lumens"] * lm_ratio
    lux = lumens * PHOTO["utilization"] / PHOTO["figure_area_m2"]

    return dict(
        case=c["name"], key=c["key"], hours=c["hours"],
        g1=g["g1"], g2=g["g2"], g3a=g["g3a"],
        load_w=load_w, loss_w=loss_w, draw_w=draw_w,
        wh_night=draw_w * c["hours"],
        amps=draw_w / BUS_V, lumens=lumens, lux=lux,
        lux_margin=lux - PHOTO["target_lux"],
        worst_drop_pct=max(r["drop_pct"] for r in runs),
        runs=runs)


def composite_night():
    """Weighted playa night from cases.json. Returns (Wh/night, results by key)."""
    results = {r["key"]: r for r in (run_case(c) for c in CASES_DOC["cases"])}
    wh = sum(results[k]["draw_w"] * h for k, h in CASES_DOC["composite_night"].items())
    return wh, results


def group_energy():
    """Wh per composite night split by power group + copper losses."""
    _, results = composite_night()
    acc = {"g1": 0.0, "g2": 0.0, "g3a": 0.0, "loss": 0.0}
    for k, h in CASES_DOC["composite_night"].items():
        r = results[k]
        for grp in ("g1", "g2", "g3a"):
            acc[grp] += r[grp] * h
        acc["loss"] += r["loss_w"] * h
    return acc


def demand():
    """Public contract for the power node: what the light asks of the station."""
    wh, results = composite_night()
    return dict(node="lights", wh_per_day=wh,
                hours=sum(CASES_DOC["composite_night"].values()),
                peak_w=sum(peak_watts().values()),
                max_draw_w=max(r["draw_w"] for r in results.values()),
                by_group=group_energy())


def main():
    hdr = (f"{'Case':28} {'Гр.1':>6} {'Гр.2':>6} {'Гр.3А':>6} {'Разом':>7} "
           f"{'Wh/ніч':>7} {'lux':>6} {'просадка':>9}")
    print(hdr)
    print("-" * len(hdr))
    for c in CASES_DOC["cases"]:
        r = run_case(c)
        flag = " !!" if r["worst_drop_pct"] > WIRE["drop_crit_pct"] else ""
        print(f"{r['case']:28} {r['g1']:5.1f}W {r['g2']:5.1f}W {r['g3a']:5.1f}W "
              f"{r['draw_w']:6.1f}W {r['wh_night']:7.0f} {r['lux']:6.0f} "
              f"{r['worst_drop_pct']:8.2f}%{flag}")

    pk = peak_watts()
    ref = P["spec_reference"]
    print(f"\nПік за паспортом: Гр.1 {pk['g1']:.0f}W · Гр.2 {pk['g2']:.0f}W · "
          f"Гр.3А {pk['g3a']:.0f}W · разом {sum(pk.values()):.0f}W")
    print(f"  (розрахунок архітектора: {ref['architect_groups_w']} → "
          f"{ref['architect_peak_w']}W / {ref['architect_night_wh']} Wh)")

    d = demand()
    print(f"\nКомпозитна ніч {d['hours']:.1f} год -> {d['wh_per_day']:.0f} Wh/добу "
          f"(пік споживання {d['max_draw_w']:.0f} W)")
    for k, label in (("g2", "декор (стрічка+робот)"), ("g3a", "аварійна (габарити+сходи)"),
                     ("g1", "прожектори"), ("loss", "втрати в міді")):
        v = d["by_group"][k]
        print(f"  {label:28} {v:5.0f} Wh  {100*v/d['wh_per_day']:4.1f}%")

    print(f"\nПросадка на шині {BUS_V:.0f} В (усе на повну, межа {WIRE['drop_crit_pct']:.0f}%):")
    for r in wiring_losses(pk):
        need = min_awg(next(x for x in WIRE["runs"] if x["id"] == r["id"]), pk)
        verdict = "ok" if r["drop_pct"] <= WIRE["drop_crit_pct"] else f"ТРЕБА AWG {need}"
        print(f"  {r['label']:32} AWG{r['awg']:<3} {r['length_m']:5.1f}m "
              f"{r['amps']:5.1f}A  −{r['v_drop']:.2f}V ({r['drop_pct']:5.2f}%)  {verdict}")


if __name__ == "__main__":
    main()
