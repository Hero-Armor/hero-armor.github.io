#!/usr/bin/env python3
"""Вартість дерева подіуму: розкрій каркаса на дошки + листи настилу.

Тільки дерево — без металу, шурупів, клею і фарби (див. _scope у даних).
Три набори: звичайне дерево з фанерою (як зроблено), з OSB (як на кресленні)
і водостійкий — усе просочене. Числа на podium_lab.html рахує ЛИШЕ ця модель.

    python3 podium_wood.py          зведення в консоль + самоперевірка
"""
import json
from pathlib import Path

P = json.loads((Path(__file__).resolve().parents[1] / "data" / "podium_wood.json").read_text())


def variants():
    """ключ → (підпис, бруси і дошки, лист настилу)."""
    out = {k: (o["label"], P["stock"], o) for k, o in P["deck"]["options"].items()}
    w = P["waterproof"]
    out["waterproof"] = (w["label"], w["stock"], w["deck"])
    return out


def cut_plan(stock, board_mm):
    """Розкладка деталей одного перерізу по дошках (first-fit decreasing).

    ponytail: жадібний FFD, а не точний пакувальник — для 12–32 деталей
    він або оптимальний, або на дошку гірший; перевірка — lower_bound().
    """
    cuts = sorted((pc["len_mm"] for pc in P["pieces"] if pc["stock"] == stock
                   for _ in range(pc["per_quarter"] * P["quarters"])), reverse=True)
    boards = []  # [[довжини деталей], ...]
    for c in cuts:
        for b in boards:
            if sum(b) + P["kerf_mm"] * len(b) + c <= board_mm:
                b.append(c)
                break
        else:
            boards.append([c])
    return boards


def lower_bound(stock, board_mm):
    total = sum(pc["len_mm"] * pc["per_quarter"] * P["quarters"]
                for pc in P["pieces"] if pc["stock"] == stock)
    return -(-total // board_mm)


def totals(key=None):
    _, stock, deck = variants()[key or P["deck"]["default"]]
    rows, cuts = [], []
    for k, s in stock.items():
        plan = cut_plan(k, s["board_mm"])
        rows.append(dict(s, key=k, qty=len(plan), sum=round(len(plan) * s["price"], 2)))
        cuts += [{"name": f"{k} № {i}", "parts": b,
                  "left": s["board_mm"] - sum(b) - P["kerf_mm"] * (len(b) - 1)}
                 for i, b in enumerate(plan, 1)]
    rows.append(dict(deck, key="deck", qty=P["deck"]["sheets"],
                     sum=round(P["deck"]["sheets"] * deck["price"], 2)))
    net = round(sum(r["sum"] for r in rows), 2)
    tax = round(net * P["tax_pct"] / 100, 2)
    return {"rows": rows, "cuts": cuts, "net": net, "tax": tax, "total": round(net + tax, 2)}


if __name__ == "__main__":
    for key, (label, stock, _) in variants().items():
        t = totals(key)
        for k, s in stock.items():
            plan = cut_plan(k, s["board_mm"])
            assert max(pc["len_mm"] for pc in P["pieces"] if pc["stock"] == k) <= s["board_mm"]
            assert all(sum(b) + P["kerf_mm"] * (len(b) - 1) <= s["board_mm"] for b in plan)
            print(f"  {k}: {len(plan)} дошок по {s['board_mm']} мм (мін. {lower_bound(k, s['board_mm'])})")
        assert abs(t["total"] - t["net"] * (1 + P["tax_pct"] / 100)) < 0.02
        print(f"{label}: ${t['net']} + податок ${t['tax']} = ${t['total']}")
