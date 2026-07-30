#!/usr/bin/env python3
"""Ящик для станції: чи влізе і чи не звариться.

Навіщо окрема модель. Станції EcoFlow/Bluetti за паспортом працюють до +45°C,
а на плайї повітря вдень саме 40-45°C. Глухо закритий ящик перетворюється на
печку: станція ріже потужність або йде в захист саме тоді, коли має заряджатись.
Але й відкритий ящик не годиться — лужний пил (pH 9-10) осідає на платах.

Тому ящик рахуємо як два незалежні питання:
  1. ГЕОМЕТРІЯ — чи влазить станція з зазорами на продув і на кабелі;
  2. ТЕПЛО — який потік повітря треба, щоб всередині було не гарячіше за межу.

Модель на стандартній бібліотеці — CI збирає сайт без залежностей.
"""

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
P = json.loads((DATA / "params.json").read_text())

AIR = P["air"]


# ---------------------------------------------------------------- геометрія
def fits(station, case, clearance_mm=None):
    """Чи влізе станція в ящик, з зазором на продув.

    Зазор потрібен не «щоб не тиснуло», а щоб повітря мало куди йти: якщо
    станція лежить впритул до стінок, вентилятор ганяє повітря по колу біля
    себе, а решта ящика лишається гарячою.
    """
    c = P["fit"]["clearance_mm"] if clearance_mm is None else clearance_mm
    sd = sorted(station["dims_mm"], reverse=True)
    cd = sorted(case["inner_mm"], reverse=True)
    need = [d + 2 * c for d in sd]
    ok = all(n <= have for n, have in zip(need, cd))
    slack = [round(have - n) for n, have in zip(need, cd)]
    return dict(fits=ok, need_mm=[round(n) for n in need], case_mm=cd,
                slack_mm=slack, tight=ok and min(slack) < c)


# ---------------------------------------------------------------- тепло
def heat_w(charge_w=None, load_w=None):
    """Скільки тепла станція віддає в ящик.

    Джерела: втрати на зарядці (сонце → батарея), втрати на віддачі в
    навантаження і власний холостий хід. Беремо ККД із параметрів — точні
    цифри виробники не публікують, тому це інженерна оцінка, а не паспорт.
    """
    ch = P["thermal"]["charge_w"] if charge_w is None else charge_w
    ld = P["thermal"]["load_w"] if load_w is None else load_w
    e_ch, e_dis = P["thermal"]["eff_charge"], P["thermal"]["eff_discharge"]
    return (ch * (1 - e_ch) + ld * (1 - e_dis) + P["thermal"]["standby_w"])


def airflow_cfm(heat, dt_c=None):
    """Потрібний потік повітря, щоб перегрів не перевищив dt_c.

    Фізика: потік = тепло / (щільність × теплоємність × перегрів).
    Формула у звичних одиницях: CFM ≈ 3.16 × Вт / ΔT(°F). Переводимо з °C.
    """
    dt = P["thermal"]["max_rise_c"] if dt_c is None else dt_c
    dt_f = dt * 9 / 5
    return 3.16 * heat / dt_f if dt_f else float("inf")


def fan_verdict(cfm_needed, fan):
    """Чи витягне вентилятор — з поправкою на фільтр.

    Пиловий фільтр і сітка ріжуть реальний потік: паспортні CFM міряють на
    вільному вході. Беремо консервативну поправку з параметрів.
    """
    real = fan["cfm"] * AIR["filter_derate"]
    return dict(name=fan["name"], cfm_spec=fan["cfm"], cfm_real=round(real, 1),
                enough=real >= cfm_needed,
                margin=round(real - cfm_needed, 1))


def inlet_area_cm2(cfm):
    """Площа вхідного отвору під заданий потік.

    Якщо вхід замалий, вентилятор працює «на розрідження»: шумить, а повітря
    майже не рухається. Швидкість беремо помірну — на швидкому потоці фільтр
    забивається пилом швидше.
    """
    m3h = cfm * 1.699
    v = AIR["inlet_speed_ms"]
    return round(m3h / 3600 / v * 10000, 1)


def headroom(ambient_c=None):
    """Скільки перегріву ми взагалі можемо собі дозволити при даній спеці.

    Це і є справжня постановка задачі. Не «який потік дасть 8°C перегріву», а
    навпаки: межа станції +45°C, зовні вже 42°C — значить на перегрів лишається
    3°C, і саме під них треба рахувати потік. Якщо зовні спекотніше за межу,
    жоден вентилятор не допоможе: він не може зробити холодніше за вулицю.
    """
    amb = P["ambient"]["playa_shade_c"] if ambient_c is None else ambient_c
    limit = P["ambient"]["station_limit_c"]
    margin = P["ambient"].get("safety_c", 2)
    allowed = limit - margin - amb
    return dict(ambient_c=amb, limit_c=limit, safety_c=margin,
                allowed_rise_c=round(allowed, 1),
                possible=allowed > 0)


def need_cfm(ambient_c=None, heat=None):
    """Потрібний потік саме під цю спеку (а не під абстрактні 8°C)."""
    hr = headroom(ambient_c)
    h = heat_w() if heat is None else heat
    if not hr["possible"]:
        return dict(**hr, heat_w=round(h, 1), cfm=None,
                    verdict="вентиляція не врятує — потрібна тінь або охолодження")
    cfm = airflow_cfm(h, hr["allowed_rise_c"])
    fans = [fan_verdict(cfm, f) for f in P["fans"]]
    workable = [f for f in fans if f["enough"]]
    return dict(**hr, heat_w=round(h, 1), cfm=round(cfm, 1),
                inlet_cm2=inlet_area_cm2(cfm),
                fans=fans,
                cheapest=workable[0]["name"] if workable else None,
                verdict=("вистачить " + workable[0]["name"]) if workable
                        else "жоден вентилятор із списку не витягне")


def run_case(station, case):
    g = fits(station, case)
    h = heat_w()
    cfm = airflow_cfm(h)
    fans = [fan_verdict(cfm, f) for f in P["fans"]]
    return dict(station=station["name"], case=case["name"], geom=g,
                heat_w=round(h, 1), cfm_needed=round(cfm, 1),
                inlet_cm2=inlet_area_cm2(cfm), fans=fans,
                price_usd=case.get("price_usd"))


def main():
    h = heat_w()
    cfm = airflow_cfm(h)
    print(f"Тепло в ящику: {h:.1f} Вт "
          f"(зарядка {P['thermal']['charge_w']} Вт + віддача "
          f"{P['thermal']['load_w']} Вт + холостий хід)")
    print(f"Потрібний потік: {cfm:.1f} CFM при перегріві не більше "
          f"{P['thermal']['max_rise_c']}°C")
    print(f"Вхідний отвір: від {inlet_area_cm2(cfm):.0f} см²\n")

    for f in (fan_verdict(cfm, x) for x in P["fans"]):
        mark = "ok " if f["enough"] else "МАЛО"
        print(f"  {mark} {f['name']:34} {f['cfm_spec']:>5} CFM паспорт → "
              f"{f['cfm_real']:>5} з фільтром")

    print("Скільки потоку треба насправді — залежно від спеки зовні:")
    for amb in (35, 38, P["ambient"]["playa_shade_c"], 45, P["ambient"]["playa_sun_c"]):
        r = need_cfm(amb)
        if r["cfm"] is None:
            print(f"  зовні {amb}°C: на перегрів лишається "
                  f"{r['allowed_rise_c']}°C -> {r['verdict']}")
        else:
            print(f"  зовні {amb}°C: дозволений перегрів {r['allowed_rise_c']}°C -> "
                  f"треба {r['cfm']:.0f} CFM, отвір {r['inlet_cm2']:.0f} см² -> {r['verdict']}")
    print()

    print(f"\n{'Станція':26} {'Ящик':30} {'влазить':>9} {'запас':>16}")
    print("-" * 86)
    for st in P["stations"]:
        for cs in P["cases"]:
            r = run_case(st, cs)
            g = r["geom"]
            verdict = ("впритул" if g["tight"] else "так") if g["fits"] else "ні"
            print(f"  {st['name']:24} {cs['name']:30} {verdict:>9} "
                  f"{str(g['slack_mm']):>16}")


if __name__ == "__main__":
    main()
