#!/usr/bin/env python3
"""
Hero Armor audio node — system-level model, driven by ../data/params.json + cases.json.

Chain: LD2410C radar -> ESP32 -> PCM5102A -> TPA3116D2 mono -> speaker (see params).
All constants live in data/params.json; playa scenarios in data/cases.json.
This module is the single computation source for the CLI table AND the dashboard
(model/build_dashboard.py imports it).
"""

import json
import math
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
P = json.loads((DATA / "params.json").read_text())
CASES_DOC = json.loads((DATA / "cases.json").read_text())

V = P["rail_v"]
V_CLIP_RMS = V / math.sqrt(2)          # BTL max sine at the rail
SPK = P["speaker"]["candidates"][P["speaker"]["chosen"]]
R_LOAD = SPK["ohms"]
SENS_EFF = SPK["sens_db"] + (3.0 if P["speaker"]["config"] == "stereo" else 0.0)
CREST = 10 ** (P["crest_db"] / 10)
TH = P["thermal"]


def volume_stage(vol_dbfs, night_mode=False, gain_db=None):
    """DAC level + amp gain -> peak (sine-equiv) power, speech avg, clip headroom."""
    gain_db = P["gain_db"] if gain_db is None else gain_db
    vol = vol_dbfs + (P["volume"]["night_delta_db"] if night_mode else 0)
    v_req = P["dac_fs_vrms"] * 10 ** (vol / 20) * 10 ** (gain_db / 20)
    v_rms = min(v_req, V_CLIP_RMS)
    p_peak = v_rms ** 2 / R_LOAD
    return dict(vol_eff=vol, p_peak=p_peak, p_avg=p_peak / CREST,
                headroom_db=20 * math.log10(V_CLIP_RMS / v_req))


def rail_33v_amps(playing):
    """3.3V + 5V (radar) loads reflected to the 12V rail."""
    c = P["currents_33v"]
    a33 = (c["esp32_play"] + c["dac"] + c["sd_read"]) if playing else (c["esp32_idle"] + c["dac"])
    return (a33 * 3.3 + P["sensor"]["a_5v"] * 5.0) / (V * P["buck_eff"])


def run_case(c):
    vs = volume_stage(c["vol_dbfs"], c["night_mode"])

    cycle = c["clip_s"] + c["cooldown_s"]
    trig = min(c["triggers_per_hr"], 3600 / cycle)
    duty = trig * c["clip_s"] / 3600

    i_play = vs["p_avg"] / (P["amp_eff"] * V) + P["amp_idle_a"] + rail_33v_amps(True)
    i_idle = P["amp_idle_a"] + rail_33v_amps(False)
    i_avg = duty * i_play + (1 - duty) * i_idle
    wh_day = i_avg * V * 24

    # thermal: conservative — continuous sine at the peak level
    p_dis = vs["p_peak"] * (1 / P["amp_eff"] - 1) + P["amp_idle_a"] * V * 0.5
    t_sink = c["t_ambient"] + c["solar_load"]
    rth_total = TH["rth_jc"] + TH["rth_pad"] + TH["heatsink_rth"]
    t_j_worst = t_sink + p_dis * rth_total
    p_dis_avg = duty * p_dis + (1 - duty) * P["amp_idle_a"] * V * 0.5
    t_j_avg = t_sink + p_dis_avg * rth_total

    dist = c["listener_m"]
    spl_peak = SENS_EFF + 10 * math.log10(max(vs["p_peak"], 1e-3)) - 20 * math.log10(dist)
    spl_avg = SENS_EFF + 10 * math.log10(max(vs["p_avg"], 1e-3)) - 20 * math.log10(dist)

    contrast = max(P["sensor"]["skin_c"] - c["t_ambient"], 0.0)
    pir_range_m = 3.0 * min(1.0, max(0.15, contrast / (P["sensor"]["skin_c"] - 20.0)))

    return dict(case=c["name"], key=c["key"], trig_eff=trig, duty=duty,
                i_avg=i_avg, wh_day=wh_day, p_dis=p_dis,
                t_j_worst=t_j_worst, t_j_avg=t_j_avg,
                spl_peak=spl_peak, spl_avg=spl_avg,
                margin_avg=spl_avg - c["noise_db"], noise_db=c["noise_db"],
                radar_range_m=P["sensor"]["range_m"], pir_range_m=pir_range_m, **vs)


def composite_day():
    """Weighted burn day from cases.json composite_day_hours. Returns (Wh/day node, results by key)."""
    results = {r["key"]: r for r in (run_case(c) for c in CASES_DOC["cases"])}
    wh = sum(results[k]["i_avg"] * V * h for k, h in CASES_DOC["composite_day_hours"].items())
    return wh, results


def _stations():
    """Станції беремо з системи «Живлення» — тут свого списку не тримаємо."""
    import json as _json, pathlib as _pl
    sp = _pl.Path(__file__).resolve().parents[2] / "solar" / "data" / "params.json"
    st = _json.loads(sp.read_text())["stations"]
    return {name: v["wh"] for name, v in st.items()}


def autonomy(wh_node_day):
    """Days per station incl. station standby; plus solar break-even W."""
    ps, sol = P["power_source"], P["solar"]
    total = wh_node_day + ps["standby_w"] * 24
    days = {name: wh * ps["usable_frac"] / total for name, wh in _stations().items()}
    return dict(total_wh_day=total, days=days,
                solar_w=total / (sol["sun_hours"] * sol["system_eff"]))


def main():
    hdr = (f"{'Case':20} {'trig/h':>6} {'duty':>6} {'Iavg':>7} {'Wh/d':>5} "
           f"{'Tj max':>7} {'SPLavg':>7} {'marg':>5} {'clip':>6}")
    print(hdr)
    print("-" * len(hdr))
    for c in CASES_DOC["cases"]:
        r = run_case(c)
        flag = " !!" if r["t_j_worst"] > TH["tj_derate"] else ""
        print(f"{r['case']:20} {r['trig_eff']:6.1f} {r['duty']*100:5.1f}% "
              f"{r['i_avg']*1000:5.0f}mA {r['wh_day']:5.1f} {r['t_j_worst']:6.1f}C "
              f"{r['spl_avg']:6.1f}dB {r['margin_avg']:+5.1f} {r['headroom_db']:+5.1f}dB{flag}")

    wh, _ = composite_day()
    a = autonomy(wh)
    print(f"\nComposite burn day: node {wh:.0f} Wh/day; "
          f"with {P['power_source']['type']} standby -> {a['total_wh_day']:.0f} Wh/day")
    for name, d in a["days"].items():
        print(f"  {name:14} -> {d:4.1f} days")
    print(f"  Solar break-even: ~{a['solar_w']:.0f} W")


if __name__ == "__main__":
    main()
