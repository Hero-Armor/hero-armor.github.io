#!/usr/bin/env python3
"""
Hero Armor — стенд ламп прожектора: чи економить лампа від заниження напруги.

Іван занижає напругу на групі прожекторів, щоб зняти ватти з батареї. Спрацює це
чи ні — залежить від того, що стоїть усередині лампи. Дослід міряє одне й те саме
у трьох ламп (струм і люкси на кількох напругах) і зводить кожну до двох чисел:

  n_power  показник степеня в P ~ (V/Vnom)^n — як круто падає споживання
  n_lux    те саме для яскравості

Вигода від заниження = наскільки n_power більший за n_lux: ватти мають падати
швидше за світло. Якщо n_power ~ 0 — усередині стабілізатор струму, метод Івана
на цій лампі не працює, скільки не крути.

Числа-переможця вручну переносимо в lights/data/params.json → voltage_following
(power_exponent, v_min), і вся модель світла починає рахувати по факту, не по
прикидці. Порожня база вимірювань — нормальний стан: сторінка тоді показує
протокол і чекає замірів. Тільки stdlib.
"""

import json
from math import log
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
B = json.loads((DATA / "lamp_bench.json").read_text())

CRIT = B["criteria"]
V_NOM = 12.0


def lamps():
    return B["lamps"]


def lamp(lamp_id):
    return next(l for l in B["lamps"] if l["id"] == lamp_id)


def points(lamp_id):
    """Заміри однієї лампи, від високої напруги до низької."""
    rows = [m for m in B["measurements"] if m["lamp"] == lamp_id]
    return sorted(rows, key=lambda m: -m["v"])


def _slope(pairs):
    """Нахил ln(y) по ln(x) методом найменших квадратів — той самий показник n.

    Логарифмуємо, бо степенева залежність у логарифмах стає прямою: замість
    підбирати n перебором, беремо нахил прямої. Точки з нулем (лампа згасла)
    у розрахунок не йдуть — нуль у логарифм не влазить і це вже інший режим."""
    pts = [(log(x), log(y)) for x, y in pairs if x > 0 and y > 0]
    if len(pts) < 2:
        return None
    mx = sum(p[0] for p in pts) / len(pts)
    my = sum(p[1] for p in pts) / len(pts)
    den = sum((p[0] - mx) ** 2 for p in pts)
    if den == 0:
        return None
    return sum((p[0] - mx) * (p[1] - my) for p in pts) / den


def fit(lamp_id):
    """Два показники степеня лампи + напруга, на якій вона реально гасне."""
    rows = points(lamp_id)
    lit = [m for m in rows if m.get("a", 0) > 0]
    dark = [m for m in rows if m.get("a", 0) <= 0 or m.get("lux", 0) <= 0]
    return {
        "n_power": _slope([(m["v"], m["v"] * m["a"]) for m in lit]),
        "n_lux": _slope([(m["v"], m.get("lux", 0)) for m in lit]),
        "v_off": max((m["v"] for m in dark), default=None),
        "n_points": len(lit),
    }


def verdict(n_power):
    """Словами: чи працює на цій лампі метод «занизив напругу — зекономив»."""
    if n_power is None:
        return "чекає заміру", "wait"
    if n_power >= CRIT["exp_vf"]:
        return "слідує за напругою — економить", "good"
    if n_power <= CRIT["exp_cc"]:
        return "тримає потужність — заниження не дає економії", "crit"
    return "економить частково", "warn"


def curve(lamp_id):
    """Заміри, переведені в те, що нас цікавить: ватти групи і що з яскравістю.

    Усе рахується у відсотках від робочої точки 12 В цієї ж лампи — тоді лампи
    різної потужності порівнюються між собою чесно."""
    rows = points(lamp_id)
    if not rows:
        return []
    base = min(rows, key=lambda m: abs(m["v"] - V_NOM))
    w0 = base["v"] * base["a"] or 1.0
    lux0 = base.get("lux") or 0
    out = []
    for m in rows:
        w = m["v"] * m["a"]
        lux = m.get("lux", 0)
        w_pct = 100 * w / w0
        lux_pct = 100 * lux / lux0 if lux0 else None
        group_w = w * CRIT["spot_qty"]
        out.append({
            "v": m["v"], "a": m["a"], "w": w, "lux": lux,
            "w_pct": w_pct, "lux_pct": lux_pct,
            # Скільки відсотків ватт віддає лампа за кожен відсоток втраченого
            # світла. Більше за 1 — вигідний обмін, менше — гасимо задарма.
            "trade": ((100 - w_pct) / (100 - lux_pct)
                      if lux_pct is not None and lux_pct < 99.5 else None),
            "group_w": group_w,
            "night_wh": group_w * CRIT["night_h"],
            "fits_dc": group_w <= CRIT["dc_port_w"],
            "fits_target": group_w <= CRIT["target_group_w"],
            "note": m.get("note", ""),
        })
    return out


def working_point(lamp_id):
    """Найнижча напруга, на якій група ще влазить у ціль по ваттах і світить."""
    rows = [r for r in curve(lamp_id) if r["lux"] > 0 and r["fits_target"]]
    return min(rows, key=lambda r: r["v"]) if rows else None


def ranking():
    """Лампи в порядку придатності: спершу ті, що реально економлять."""
    out = []
    for l in lamps():
        f = fit(l["id"])
        v_text, v_cls = verdict(f["n_power"])
        wp = working_point(l["id"])
        out.append({**l, **f, "verdict": v_text, "cls": v_cls, "working": wp})
    order = {"good": 0, "warn": 1, "wait": 2, "crit": 3}
    return sorted(out, key=lambda r: (order[r["cls"]], -(r["n_power"] or 0)))


def dimmer_runs():
    """Що показав блок живлення на крайніх положеннях ШІМ-диммера.

    Це окрема історія від заниження напруги: диммер не садить вольти, він рубає
    живлення імпульсами. Тому тут не показник степеня, а простий діапазон —
    скільки лампа бере на повній і скільки на мінімумі крутилки. Для батареї
    важливий саме нижній край: у ньому ми доживаємо ніч, якщо сонця не було."""
    a_rating, derate = CRIT["dimmer_a"], CRIT["dimmer_derate"]
    safe = a_rating * derate
    flick = {f["lamp"]: f for f in B["flicker"]}
    out = []
    for r in B["dimmer_runs"]:
        l = lamp(r["lamp"])
        f = flick.get(r["lamp"], {})
        grp = r["a_full"] * CRIT["spot_qty"]
        out.append({
            "id": r["lamp"], "name": l["name"], "role": l["role"],
            "a_full": r["a_full"], "a_min": r["a_min"],
            "w_full": r["v"] * r["a_full"], "w_min": r["v"] * r["a_min"],
            "range_x": r["a_full"] / r["a_min"] if r["a_min"] else None,
            "group_a": grp, "group_w": r["v"] * grp,
            "group_a_min": r["a_min"] * CRIT["spot_qty"],
            "night_wh": r["v"] * grp * CRIT["night_h"],
            "dimmer_ok": grp <= safe,
            "dimmer_load_pct": 100 * grp / a_rating,
            "headroom_pct": 100 * (1 - grp / safe),
            "fits_dc": r["v"] * grp <= CRIT["dc_port_w"],
            "flicker": f.get("verdict", "не перевіряли"),
            "flicker_note": f.get("note", ""),
            "note": r.get("note", ""),
        })
    return sorted(out, key=lambda r: r["a_full"])


def worst_a_full():
    """Найпрожерливіша з заміряних ламп — по ній рахуємо кабель і диммер."""
    runs = B["dimmer_runs"]
    return max((r["a_full"] for r in runs), default=None)


def status():
    """Скільки замірів уже є — сторінка з цього вирішує, що показувати."""
    done = {l["id"]: len(points(l["id"])) for l in lamps()}
    return {
        "measurements": len(B["measurements"]),
        "by_lamp": done,
        "expected": len(lamps()) * len(B["points_v"]),
        "flicker": len(B["flicker"]),
        "pending": [l["name"] for l in lamps() if not done[l["id"]]],
    }


def main():
    st = status()
    print("ШІМ-диммер, крайні положення:")
    for r in dimmer_runs():
        print(f'  {r["name"]:38} {r["a_full"]:.2f}→{r["a_min"]:.2f} A '
              f'(×{r["range_x"]:.0f}) · група {r["group_a"]:.2f} A '
              f'{r["group_w"]:.0f} Вт · запас у диммері {r["headroom_pct"]:.0f}%'
              f'{"" if r["dimmer_ok"] else "  ⚠ НЕ ПРОХОДИТЬ"}')
    print(f'заміри напруги: {st["measurements"]} з {st["expected"]}')
    for r in ranking():
        n = f'{r["n_power"]:.2f}' if r["n_power"] is not None else "—"
        print(f'  {r["name"]:38} n={n:>5}  {r["verdict"]}')
        for row in curve(r["id"]):
            print(f'      {row["v"]:>5.1f} В  {row["w"]:5.2f} Вт  '
                  f'{row["lux"]:>6.0f} лк  група {row["group_w"]:5.1f} Вт')


if __name__ == "__main__":
    main()
