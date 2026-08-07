#!/usr/bin/env python3
"""
Окрема сторінка-калькулятор під кожен тип світла: покрутити руками.

У світловій лабораторії все зведено докупи — зручно бачити систему, незручно
гратись з однією гілкою. Тут навпаки: одна сторінка = один тип світильника, і
на ній можна крутити скільки штук, яка яскравість, який кабель і як він
прокладений, а числа рахуються одразу.

Фізика для всіх типів однакова, різняться тільки вхідні:

    струм гілки = штук × струм одиниці × частка яскравості
    просадка    = 2 × опір_метра × K(схема, штук) × довжина_відрізка × струм_одиниці

Коефіцієнт K — це вся різниця між схемами прокладки. Він рахується двічі:
тут по відрізках (чесно, по кожній ділянці) і в браузері закритою формулою.
Обидва мають збігатись — інакше сторінка показувала б не те, що модель, і
розбіжність спливла б уже на плайї. Перевірка стоїть у _assert_k().

Дані типів — lights/data/circuits.json; струми ламп прожектора беруться з
заміряних (lamp_bench), Вт/м стрічки — зі стенда стрічки (strip_bench).
Тільки stdlib.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lamp_bench as lb

DATA = Path(__file__).resolve().parent.parent / "data"
P = json.loads((DATA / "params.json").read_text())
C = json.loads((DATA / "circuits.json").read_text())

OHM = P["wiring"]["awg_ohm_per_m"]
V = P["bus_v"]


# ------------------------------------------------------- коефіцієнти схем
def k_segments(topology, n):
    """K по відрізках: сума струмів (у одиницях однієї лампи) по ділянках,
    які лежать на шляху до найдальшого світильника."""
    if topology == "chain":
        return sum(n - k for k in range(n - 1))
    if topology == "split":
        half = n // 2
        return sum(half - k for k in range(half))
    if topology == "loop":
        half = n // 2
        return sum(half - k - 0.5 for k in range(half))
    if topology == "star":
        return 1.0
    raise ValueError(topology)


def k_closed(topology, n):
    """Та сама величина закритою формулою — саме її рахує сторінка в браузері."""
    half = n // 2
    return {
        "chain": n * (n + 1) / 2 - 1,
        "split": half * (half + 1) / 2,
        "loop": half * half / 2,
        "star": 1.0,
    }[topology]


def k2_segments(topology, n):
    """Те саме для ВТРАТ: у мідь іде квадрат струму, тому ділянки складаються
    квадратами, і схема прокладки міняє не лише рівність, а й самі втрати."""
    if topology == "chain":
        return sum((n - k) ** 2 for k in range(n - 1))
    if topology == "split":
        half = n // 2
        return 2 * sum((half - k) ** 2 for k in range(half))
    if topology == "loop":
        half = n // 2
        return 2 * sum((half - k - 0.5) ** 2 for k in range(half))
    if topology == "star":
        return float(n)
    raise ValueError(topology)


def k2_closed(topology, n):
    """Закрита форма — саме її рахує сторінка."""
    h = n // 2
    sq = lambda m: m * (m + 1) * (2 * m + 1) / 6
    return {
        "chain": sq(n) - 1,
        "split": 2 * sq(h),
        "loop": 2 * (sq(h) - h * (h + 1) / 2 + 0.25 * h),
        "star": float(n),
    }[topology]


def _assert_k():
    for topo in ("chain", "split", "loop", "star"):
        for n in range(1, 33):
            for f_seg, f_cls, what in ((k_segments, k_closed, "K"),
                                       (k2_segments, k2_closed, "K²")):
                a, b = f_seg(topo, n), f_cls(topo, n)
                assert abs(a - b) < 1e-9, f"{what} розійшовся: {topo} n={n}: {a} != {b}"


_assert_k()


# ------------------------------------------------------------- складання
def _load(ld):
    """Одна позиція на сторінці: скільки бере одна штука (чи метр)."""
    out = dict(ld)
    if ld.get("from") == "lamp_bench":
        run = next(r for r in lb.dimmer_runs() if r["id"] == ld["lamp"])
        out["name"] = run["name"]
        out["a_full"] = run["a_full"]
        out["a_min"] = run["a_min"]
        out["source"] = f'заміряно на стенді {run["date"] if "date" in run else ""}'.strip()
    elif ld.get("from") == "strip_bench":
        try:
            import strip_bench as sb
            kind, wpm = sb.source()
            out["a_full"] = round(wpm / V, 4)
            out["source"] = f"стенд стрічки: {kind}"
        except Exception:
            out["a_full"] = round(ld["w_fallback"] / V, 4)
            out["source"] = "паспортні Вт/м — стенд ще не дав числа"
        out["a_min"] = 0.0
    else:
        out["a_full"] = round(ld["w_unit"] / V, 4)
        out["a_min"] = 0.0
        out["source"] = ld.get("source", "паспорт")
    return out


def circuits():
    """Готові конфіги сторінок — по одному на тип світла."""
    out = []
    for c in C["circuits"]:
        cfg = {k: v for k, v in c.items() if k != "loads"}
        cfg["loads"] = [_load(ld) for ld in c["loads"]]
        cfg["gauges"] = C["gauges"]
        cfg["ohm"] = {str(g): OHM[str(g)] for g in C["gauges"]}
        cfg["v"] = V
        cfg["limits"] = {**C["limits"], **c.get("limits", {})}
        # порядок беремо з самої цепі, а не з загального списку: перша в списку —
        # та, яку ми справді робимо, вона ж стоїть за замовчуванням на сторінці
        _tmap = {t["key"]: t for t in C["topologies"]}
        cfg["topologies"] = [_tmap[k] for k in c["topologies"] if k in _tmap]
        out.append(cfg)
    return out


def main():
    for c in circuits():
        print(f'{c["key"]:10} {c["title"]}')
        for ld in c["loads"]:
            print(f'    {ld["name"]:34} {ld["a_full"]:.3f} A/{c["unit"]} · {ld["source"]}')
        for t in c["topologies"]:
            n = c["loads"][0]["n_default"]
            print(f'      {t["key"]:6} K={k_closed(t["key"], n):6.1f} при {n} шт')


if __name__ == "__main__":
    main()
