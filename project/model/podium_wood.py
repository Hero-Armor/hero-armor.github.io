#!/usr/bin/env python3
"""Вартість дерева подіуму: розкрій каркаса на 8-футові дошки + листи настилу.

Тільки дерево — без металу, шурупів, клею і фарби (див. _scope у даних).
Числа на сторінці podium_lab.html рахує ЛИШЕ ця модель.

    python3 podium_wood.py          зведення в консоль + самоперевірка
"""
import json
from pathlib import Path

P = json.loads((Path(__file__).resolve().parents[1] / "data" / "podium_wood.json").read_text())


def cut_plan(stock):
    """Розкладка деталей одного перерізу по дошках (first-fit decreasing).

    ponytail: жадібний FFD, а не точний пакувальник — для 12–32 деталей
    він або оптимальний, або на дошку гірший; перевірка — lower_bound().
    """
    cuts = sorted((pc["len_mm"] for pc in P["pieces"] if pc["stock"] == stock
                   for _ in range(pc["per_quarter"] * P["quarters"])), reverse=True)
    boards = []  # [[довжини деталей], ...]
    for c in cuts:
        for b in boards:
            if sum(b) + P["kerf_mm"] * len(b) + c <= P["board_mm"]:
                b.append(c)
                break
        else:
            boards.append([c])
    return boards


def lower_bound(stock):
    total = sum(pc["len_mm"] * pc["per_quarter"] * P["quarters"]
                for pc in P["pieces"] if pc["stock"] == stock)
    return -(-total // P["board_mm"])


def totals(deck_key=None):
    deck_key = deck_key or P["deck"]["default"]
    rows = []
    for key, s in P["stock"].items():
        n = len(cut_plan(key))
        rows.append(dict(s, key=key, qty=n, sum=round(n * s["price"], 2)))
    d = P["deck"]["options"][deck_key]
    rows.append(dict(d, key="deck", qty=P["deck"]["sheets"],
                     sum=round(P["deck"]["sheets"] * d["price"], 2)))
    net = round(sum(r["sum"] for r in rows), 2)
    tax = round(net * P["tax_pct"] / 100, 2)
    return {"rows": rows, "net": net, "tax": tax, "total": round(net + tax, 2)}


if __name__ == "__main__":
    for k in P["stock"]:
        plan = cut_plan(k)
        assert all(sum(b) + P["kerf_mm"] * (len(b) - 1) <= P["board_mm"] for b in plan)
        assert len(plan) <= lower_bound(k) + 1, f"{k}: розкрій гірший за межу"
        print(k, len(plan), "дошок (мін.", lower_bound(k), ")", plan)
    for dk in P["deck"]["options"]:
        t = totals(dk)
        assert abs(t["total"] - t["net"] * (1 + P["tax_pct"] / 100)) < 0.02
        print(dk, f'${t["net"]} + податок ${t["tax"]} = ${t["total"]}')
