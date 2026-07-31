#!/usr/bin/env python3
"""
Hero Armor — стенд LED-стрічки: скільки вона бере насправді.

Уся модель світла досі рахує стрічку по паспортних 15 Вт/м. Непрямий замір
Івана 22.07 (вісім прожекторів плюс п'ять метрів стрічки разом = 55 Вт) натякає,
що реально вона бере разів у п'ять менше. На 9.77 м проєкту це різниця між
147 Вт і 29 Вт — тобто між «12-вольтовий вихід станції не тягне» і «тягне
з великим запасом». Тому це гейт: поки числа нема, вибір станції стоїть.

Стенд міряє п'ять режимів ватметром і зводить їх до двох чисел:

  w_per_m   ватти на метр на білому 100% — стеля, від неї кабель і запобіжники
  duty      яка частка цієї стелі лишається в робочій анімації «біжуча вода»

Плюс окремо холостий хід контролера: у WS28xx чіп їсть постійно, навіть коли
діод темний, і на 9.77 м це вже входить у нічний бюджет.

Числа з прогону вручну переносимо в lights/data/params.json → fixtures
(w_per_m) і addressable (duty_animation, duty_peak), і вся модель починає
рахувати по факту. Порожня база — нормальний стан: сторінка тоді показує
протокол і чекає замірів. Тільки stdlib.
"""

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
B = json.loads((DATA / "strip_bench.json").read_text())

CRIT = B["criteria"]
V_NOM = 12.0
TOTAL_M = CRIT["ring_m"] + CRIT["rays_m"]


def modes():
    return B["modes"]


def measured():
    """Заміри за id режиму — рівно ті, що вже зроблені."""
    return {m["mode"]: m for m in B["measurements"]}


def _w(row):
    """Ватти запису: беремо як є, або рахуємо з В×А, якщо записані струм і напруга."""
    if row is None:
        return None
    if row.get("w") is not None:
        return row["w"]
    if row.get("a") is not None:
        return row.get("v", V_NOM) * row["a"]
    return None


def status():
    """Скільки режимів пройдено з п'яти — і чи є вже головне число."""
    got = measured()
    return {
        "measurements": len(got),
        "expected": len(B["modes"]),
        "branch": len(B["branch_results"]),
        "branch_expected": len(B["branch"]["checks"]),
        "has_w_per_m": w_per_m() is not None,
    }


def idle_w():
    """Холостий хід контролера — віднімається з решти режимів, щоб лишилась стрічка."""
    return _w(measured().get("idle")) or 0.0


def w_per_m():
    """Ватти на метр стрічки на білому 100%, без контролера.

    Спершу пробуємо режим «один метр окремо» — це найчесніше число. Якщо його
    ще нема, ділимо всю стрічку на її довжину. Обидва рази віднімаємо холостий
    хід: він не залежить від довжини і на метрі спотворив би результат."""
    got = measured()
    one = got.get("one_meter")
    if one is not None and _w(one) is not None:
        return max(_w(one) - idle_w(), 0) / (one.get("length_m") or 1.0)
    full = got.get("white100")
    if full is not None and _w(full) is not None and full.get("length_m"):
        return max(_w(full) - idle_w(), 0) / full["length_m"]
    return None


def duty():
    """Частка стелі, яку реально їсть анімація.

    Два джерела, і ватметр тут НЕ головне. Пряме ділення (анімація / білий)
    беремо, якщо обидва режими зняті приладом. Але на анімації струм падає до
    сотих ампера, де ватметр Івана вже не читає — саме на цьому ми один раз
    обпеклись. Тому за замовчуванням береться частка з профілю контролера:
    вона знята як частка засвічених пікселів, а не як струм, і тому не залежить
    ні від приладу, ні від ока."""
    got = measured()
    a, f = _w(got.get("animation")), _w(got.get("white100"))
    if a is not None and f is not None:
        base = f - idle_w()
        if base > 0:
            return (a - idle_w()) / base
    p = duty_from_profile(187)
    return p["avg"] if p else None


def indirect_w_per_m():
    """Прикидка 22.07 через різницю: усе разом мінус пораховані прожектори.

    Це не замір стрічки, а віднімання, і саме тому потрібен прямий прогін.
    Але порядок величини вона задає — і він у п'ять разів нижчий за паспорт."""
    i = B["indirect"]
    spots_w = i["spots_qty"] * i["spot_a"] * V_NOM
    return max(i["total_w"] - spots_w, 0) / i["strip_m"]


def source():
    """Звідки взяті Вт/м, які показує сторінка: замір, прикидка чи паспорт."""
    if w_per_m() is not None:
        return "measured", w_per_m()
    return "indirect", indirect_w_per_m()


def project(wpm=None, d=None):
    """Що ці Вт/м означають для всієї зірки: пік, анімація, ватт-години за ніч."""
    wpm = wpm if wpm is not None else source()[1]
    d = d if d is not None else (duty() if duty() is not None else CRIT["duty_model"])
    peak = wpm * TOTAL_M + idle_w()
    anim = wpm * TOTAL_M * d + idle_w()
    return {
        "w_per_m": wpm,
        "duty": d,
        "total_m": TOTAL_M,
        "peak_w": peak,
        "peak_a": peak / V_NOM,
        "anim_w": anim,
        "anim_a": anim / V_NOM,
        "night_wh": anim * CRIT["night_h"],
        "fits_dc": peak <= CRIT["dc_port_w"],
        "dc_load_pct": 100 * peak / CRIT["dc_port_w"],
    }


def scenarios():
    """Три версії однієї зірки: за паспортом, за прикидкою і за заміром.

    Показуємо їх поруч, бо весь сенс досліду — у розмаху між ними. Поки замір
    не зроблено, третій рядок порожній і це видно чесно, а не ховається."""
    out = [
        {"id": "model", "label": "Паспортні 15 Вт/м (як рахує модель зараз)",
         "kind": "wait", **project(CRIT["w_per_m_model"], CRIT["duty_model"])},
        {"id": "indirect", "label": f'Прикидка з заміру {B["indirect"]["date"]} (різниця)',
         "kind": "warn", **project(indirect_w_per_m(), CRIT["duty_model"])},
    ]
    if w_per_m() is not None:
        out.append({"id": "measured", "label": "Прямий замір на стенді",
                    "kind": "good", **project()})
    return out


def spots_w():
    """Скільки з 12-вольтового виходу вже зайняли прожектори — решта лишається стрічці."""
    from lamp_bench import dimmer_runs, decision
    d = decision()
    if not d:
        return None
    return next(r["group_w"] for r in dimmer_runs() if r["id"] == d["chosen"])


def headroom():
    """Скільки ват лишається стрічці після прожекторів — і чи влазить вона."""
    sw = spots_w()
    if sw is None:
        return None
    left = CRIT["dc_port_w"] - sw
    p = project()
    return {
        "spots_w": sw,
        "left_w": left,
        "strip_w": p["peak_w"],
        "fits": p["peak_w"] <= left,
        "used_pct": 100 * p["peak_w"] / left if left > 0 else None,
    }


def verdict():
    """Словами: що дослід уже сказав і чого ще чекає."""
    st = status()
    h = headroom()
    if not st["has_w_per_m"]:
        return ("чекає прогону",
                f'Прямих замірів нема — на сторінці стоїть прикидка через різницю '
                f'({indirect_w_per_m():.1f} Вт/м). Гейт для вибору станції не знятий.',
                "wait")
    # Два різні питання, які легко злити в одне і збрехати собі. Суцільна
    # заливка на всю зірку НЕ влазить — і не влізе, скільки не рахуй. Але ми її
    # і не вмикаємо: у роботі йде анімація, а вона на порядок легша. Тому вирок
    # виносимо по РОБОЧОМУ режиму, а заливку називаємо забороненою межею.
    p = project()
    over = [e for e in effect_ranking() if h and e["peak_w"] > h["left_w"]]
    bad = ", ".join(e["name"] for e in over)
    if not h:
        return ("влазить", f'{p["w_per_m"]:.1f} Вт/м заміряно.', "good")
    if p["anim_w"] > h["left_w"]:
        return ("не влазить",
                f'Навіть робоча анімація бере {p["anim_w"]:.0f} Вт, а після '
                f'прожекторів лишається {h["left_w"]:.0f} Вт.', "crit")
    return (f'робочий режим влазить, заливка — ні',
            f'{p["w_per_m"]:.1f} Вт/м заміряно. Робоча анімація бере '
            f'{p["anim_w"]:.1f} Вт (пік {p["w_per_m"]*TOTAL_M*duty_from_profile(187)["peak"]:.0f} Вт) '
            f'і {p["night_wh"]:.0f} Вт·год за ніч — це вільно влазить у '
            f'{h["left_w"]:.0f} Вт, що лишились після прожекторів. А от суцільний білий '
            f'на всю зірку — {p["peak_w"]:.0f} Вт, вдвічі більше за дозволене, тому такий '
            f'кадр не можна давати НІКОЛИ: ні як ефект, ні випадково при вмиканні. '
            + (f'З наших десяти режимів за межу виходить {bad} — на повній яскравості '
               f'його брати не можна.' if over else 'Решта режимів проходять.'), "warn")


def effect_ranking():
    """Ефекти від найощадливішого до найненажерливішого, з перерахунком у ватти.

    Профіль знятий з самого контролера і дає ЧАСТКУ: скільки пікселів світиться
    в еквіваленті повного білого. Множимо її на ватти суцільного білого — і
    кожен режим одразу видно в тих одиницях, у яких рахується ніч. Поки Вт/м
    беруться з прикидки, ватти тут теж прикидка; заміряємо — цифри стануть
    твердими самі, формула не змінюється."""
    prof = B.get("effect_profile")
    if not prof:
        return []
    full_w = source()[1] * TOTAL_M
    out = []
    for e in prof["effects"]:
        out.append({**e,
                    "avg_w": full_w * e["avg_pct"] / 100,
                    "peak_w": full_w * e["peak_pct"] / 100,
                    "night_wh": full_w * e["avg_pct"] / 100 * CRIT["night_h"]})
    return sorted(out, key=lambda e: e["avg_pct"])


def duty_from_profile(fx=187):
    """Частка світіння робочого ефекту — те, що в моделі поки стоїть як 0.45."""
    prof = B.get("effect_profile")
    if not prof:
        return None
    e = next((x for x in prof["effects"] if x["fx"] == fx), None)
    return {"avg": e["avg_pct"] / 100, "peak": e["peak_pct"] / 100,
            "name": e["name"]} if e else None


def voltage_points():
    """Сітка напруг прогону з перерахунком у просадку — у тих самих відсотках,
    якими оперує модель кабелю. Так видно не «9.5 вольта», а «21% просадки»:
    саме це число потім або дозволяє тонший дріт, або вимагає товщий."""
    vr = B.get("voltage_run")
    if not vr:
        return []
    done = {m["v"]: m for m in vr["measurements"]}
    out = []
    for v in vr["points_v"]:
        m = done.get(v, {})
        out.append({"v": v, "drop_pct": 100 * (1 - v / V_NOM),
                    "within_limit": (1 - v / V_NOM) <= vr["cable_limit_now"],
                    "a": m.get("a"), "color": m.get("color"),
                    "glitches": m.get("glitches")})
    return out


def voltage_verdict():
    """Де стрічка ще біла, а де вже ні — і що це означає для перерізу кабелю."""
    vr = B.get("voltage_run")
    if not vr or not vr["measurements"]:
        return ("чекає прогону",
                f'Межа просадки для адресної стрічки в моделі кабелю зараз '
                f'{vr["cable_limit_now"]*100:.0f}% — узята з практики, не з нашої '
                f'стрічки. Прогін замінить її на власну.', "wait")
    ok = [m for m in vr["measurements"] if m.get("color") in ("біле", "трохи тепліше")]
    if not ok:
        return ("біле не тримається", "Уже на першій точці колір поїхав.", "crit")
    v_min = min(m["v"] for m in ok)
    drop = 100 * (1 - v_min / V_NOM)
    cls = "good" if drop >= vr["cable_limit_now"] * 100 else "crit"
    return (f'біле тримається до {v_min:g} В',
            f'Це {drop:.0f}% просадки. Модель кабелю дозволяє '
            f'{vr["cable_limit_now"]*100:.0f}% — '
            + ("запас є, переріз можна не роздувати." if cls == "good" else
               "тобто чинна межа ЗАМАЛА, переріз треба піднімати."), cls)


def branch_checks():
    """Чотири перевірки гілки 1.20 м з результатами, якщо вони вже є."""
    done = {r["check"]: r for r in B["branch_results"]}
    return [{**c, "result": done.get(c["id"], {}).get("result"),
             "note": done.get(c["id"], {}).get("note", "")}
            for c in B["branch"]["checks"]]


def main():
    st = status()
    kind, wpm = source()
    print(f'режимів знято: {st["measurements"]} з {st["expected"]} · '
          f'гілка: {st["branch"]} з {st["branch_expected"]}')
    print(f'Вт/м: {wpm:.2f} ({"замір" if kind == "measured" else "прикидка через різницю"})')
    for s in scenarios():
        print(f'  {s["label"]:52} пік {s["peak_w"]:6.1f} Вт · '
              f'анімація {s["anim_w"]:6.1f} Вт · ніч {s["night_wh"]:7.0f} Wh · '
              f'{"влазить" if s["fits_dc"] else "НЕ ВЛАЗИТЬ у 126 Вт"}')
    h = headroom()
    if h:
        print(f'прожектори {h["spots_w"]:.0f} Вт → стрічці лишається {h["left_w"]:.0f} Вт, '
              f'бере {h["strip_w"]:.0f} Вт')
    v = verdict()
    print(f'вирок: {v[0]} — {v[1]}')


if __name__ == "__main__":
    main()
