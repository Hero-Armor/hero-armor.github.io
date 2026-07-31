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


def addr_full(f):
    """Watts of an addressable fixture lit solid white — the ceiling it never reaches.

    Стрічка рахується метрами, а модуль (кільце/матриця на спині робота) несе
    власну паспортну цифру: у нього нема довжини, є плата з відомою кількістю діодів."""
    if "w_full" in f:
        return f["qty"] * f["w_full"]
    return f["qty"] * f["length_m"] * f["w_per_m"]


def addr_duty(f, key):
    """Share of the module actually lit at a given moment.

    Подіумна стрічка йде одним контролером і однією анімацією — її частки лежать
    у params["addressable"]. У лампи на спині свій контролер і своя картинка, тому
    вона несе власні частки поруч із собою і не залежить від режиму стрічки."""
    return f.get(key, ADDR[key])


def fixture_power(f, case):
    """Watts drawn by one fixture line under a case's dimming settings."""
    grp = f["group"]
    if grp == "g1":
        p_ratio, _ = spot_ratios(case["v_spot"])
        return f["qty"] * f["w_unit"] * p_ratio

    dim = case["dim_g3a"] if grp == "g3a" else case["dim_g2"]
    if f.get("addressable"):
        return addr_full(f) * addr_duty(f, "duty_animation") * dim
    if f["dimming"] == "none":
        # not dimmable: it is either on or off
        return f["qty"] * f["w_unit"] * (1.0 if dim > 0 else 0.0)
    return f["qty"] * f["w_unit"] * dim


def fixture_peak(f):
    """Worst-case instantaneous watts at full brightness (no dimming).

    Для адресної стрічки «біжуча вода» пік — це НЕ вся лінія на 100% (так світло не
    працює: одночасно горить лише біжучий фронт), а максимальна миттєва частка стрічки
    × повна потужність. Архітектор колись сайзив по повній лінії — прибрано (Іван 29.07).
    Звичайні (не адресні) світильники можуть горіти повністю, тому в них пік = вся потужність.
    """
    if f.get("addressable"):
        return addr_full(f) * addr_duty(f, "duty_peak")
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


# ---------------------------------------------------------------- cable tree
TOPO = P["topology"]["segments"]
FUSE = P["fusing"]
SEG = {x["id"]: x for x in TOPO}


def _seg_load_w(seg, g_watts):
    """Watts flowing through one segment: a group branch carries whole groups,
    a device drop carries its own fixtures (optionally a share of them)."""
    if seg.get("feeds"):
        return sum(g_watts[k] for k in seg["feeds"])
    f = next(x for x in P["fixtures"] if x["id"] == seg["device"])
    return fixture_peak(f) * seg.get("share", 1)


def _chain(seg_id):
    """Segment ids from the station down to this one, inclusive."""
    out, cur = [], SEG[seg_id]
    while cur:
        out.append(cur["id"])
        cur = SEG[cur["parent"]] if cur.get("parent") else None
    return list(reversed(out))


def cable_tree(g_watts=None):
    """Every segment with its own drop AND the drop accumulated from the station.

    The accumulated figure is the one that matters: a lamp at the end of three
    hops sees the sum, not just its own tail."""
    g_watts = peak_watts() if g_watts is None else g_watts
    own = {}
    for seg in TOPO:
        w = _seg_load_w(seg, g_watts)
        i = w / BUS_V
        res = 2 * seg["length_m"] * WIRE["awg_ohm_per_m"][str(seg["awg"])]
        own[seg["id"]] = dict(seg=seg, load_w=w, amps=i, ohm=res,
                              v_drop=i * res, loss_w=i * i * res)

    rows = []
    for seg in TOPO:
        chain = _chain(seg["id"])
        cum_v = sum(own[s]["v_drop"] for s in chain)
        o = own[seg["id"]]
        rows.append(dict(
            id=seg["id"], label=seg["label"], cable=seg.get("cable", ""),
            note=seg.get("note", ""), estimate=seg.get("estimate", False),
            awg=seg["awg"], length_m=seg["length_m"], depth=len(chain) - 1,
            load_w=o["load_w"], amps=o["amps"], loss_w=o["loss_w"],
            v_drop=o["v_drop"], drop_pct=100 * o["v_drop"] / BUS_V,
            cum_v=cum_v, cum_pct=100 * cum_v / BUS_V,
            v_at_end=BUS_V - cum_v,
            need_awg=_need_awg(seg, o["amps"], chain, own),
            budget_pct=_budget(seg["id"]),
            ok=100 * cum_v / BUS_V <= _budget(seg["id"]),
            is_leaf=bool(seg.get("device"))))
    return rows


def _budget(seg_id):
    """Addressable strip needs a tight budget; plain lamps tolerate more."""
    b = WIRE["drop_budget"]
    return b["strict_pct"] if seg_id in b["strict_ids"] else b["relaxed_pct"]


def cable_tree_operating():
    """Same tree at the normal working point, not the nameplate peak.

    Sizing and fusing use the peak; what the eye actually sees is this."""
    _, res = composite_night()
    r = res["normal"]
    return cable_tree({"g1": r["g1"], "g2": r["g2"], "g3a": r["g3a"]})


def _need_awg(seg, amps, chain, own):
    """Thinnest gauge for THIS segment that keeps the whole chain under the limit."""
    upstream = sum(own[s]["v_drop"] for s in chain[:-1])
    budget = _budget(seg["id"]) / 100 * BUS_V - upstream
    if budget <= 0:
        return None
    ok = [int(a) for a, ohm in WIRE["awg_ohm_per_m"].items()
          if amps * 2 * seg["length_m"] * ohm <= budget]
    return max(ok) if ok else None


def fuses(g_watts=None):
    """Fuse rating per group + main, from real current with a safety factor."""
    g_watts = peak_watts() if g_watts is None else g_watts
    ladder = FUSE["standard_a"]

    def pick(a):
        need = a * FUSE["derate"]
        return next((x for x in ladder if x >= need), ladder[-1])

    out = [dict(id="main", label="Головний, на магістралі",
                amps=sum(g_watts.values()) / BUS_V,
                rating=pick(sum(g_watts.values()) / BUS_V))]
    for k, g in GROUPS.items():
        a = g_watts[k] / BUS_V
        out.append(dict(id=k, label=g["label"], amps=a, rating=pick(a)))
    return out


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
