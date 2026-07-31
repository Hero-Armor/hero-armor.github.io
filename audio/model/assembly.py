#!/usr/bin/env python3
"""
Hero Armor audio node — монтажний план панелі-основи (перфоборд 150×90).

Малює у масштабі: де стоїть кожен модуль, чим тримається, куди виходить
радіатор ампа, де входять гермовводи. Дані — audio/data/assembly.json
(єдине джерело; тут ніяких габаритів руками).

  python3 audio/model/assembly.py   →  assembly.png + assembly.svg
"""
import json
from pathlib import Path

import matplotlib
matplotlib.rcParams["svg.fonttype"] = "none"
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle

HERE = Path(__file__).resolve().parent
A = json.loads((HERE.parent / "data" / "assembly.json").read_text())
P = A["panel"]
W, H = P["w_mm"], P["h_mm"]

FILL = {
    "esp32": "#cfe3f7", "sd": "#d7f0d5", "dac": "#d7f0d5",
    "amp": "#f7d9c4", "buck": "#f2e3b3", "cap": "#f2e3b3",
    "k1": "#e3e3e3", "k2": "#e3e3e3", "radar": "#e7d4f2",
}
SHORT = {
    "хедери-мама 2.54 (знімний)": "хедери",
    "нейлонові стійки M3 + гвинти": "стійки M3",
    "нейлонові стійки M2.5": "стійки M2.5",
    "впаяний, ніжки короткі": "впаяний",
    "впаяний 5.08 мм": "впаяний",
    "хедер-мама 4 пін": "хедер 4",
}


def draw():
    fig, ax = plt.subplots(figsize=(11.2, 7.0), dpi=150)
    ax.set_xlim(-30, W + 34)
    ax.set_ylim(-22, H + 30)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.add_patch(FancyBboxPatch((0, 0), W, H, boxstyle="round,pad=0,rounding_size=4",
                                ec="#333", fc="#f6f2e9", lw=2, zorder=1))
    # сітка перфоборда 2.54 — поверх підкладки, щоб було видно реальні дірки
    step = 2.54
    x = step
    while x < W:
        ax.plot([x, x], [1.5, H - 1.5], lw=.25, color="#cec5b2", zorder=1.5)
        x += step
    y = step
    while y < H:
        ax.plot([1.5, W - 1.5], [y, y], lw=.25, color="#cec5b2", zorder=1.5)
        y += step
    for hx, hy in [(5, 5), (W - 5, 5), (5, H - 5), (W - 5, H - 5)]:
        ax.add_patch(Circle((hx, hy), 1.9, ec="#333", fc="white", lw=1.2, zorder=3))

    for mod in P["modules"]:
        mx, my, mw, mh = mod["x"], mod["y"], mod["w"], mod["h"]
        ax.add_patch(FancyBboxPatch((mx, my), mw, mh,
                                    boxstyle="round,pad=0,rounding_size=1.2",
                                    ec="#222", fc=FILL.get(mod["key"], "#eee"),
                                    lw=1.3, zorder=2))
        label = {"k1": "12 В\nвхід", "k2": "динамік",
                 "radar": "радар\n4 пін"}.get(mod["key"], mod["label"])
        big = mw * mh > 900
        ax.text(mx + mw / 2, my + mh / 2 + (2.2 if big else 0), label,
                ha="center", va="center", fontsize=7.4 if big else 6.2,
                weight="bold", color="#111", zorder=4)
        if big:
            ax.text(mx + mw / 2, my + mh / 2 - 3.4,
                    SHORT.get(mod["mount"], mod["mount"]), ha="center", va="center",
                    fontsize=5.8, color="#555", zorder=4)

    # радіатор ампа — крізь праву стінку коробки
    hs = P["heatsink"]
    amp = next(m for m in P["modules"] if m["key"] == "amp")
    hy = amp["y"] + amp["h"] / 2 - hs["h"] / 2
    ax.add_patch(Rectangle((W + 6, hy), 11, hs["h"], ec="#222", fc="#c4c4c4",
                           hatch="////", lw=1.2, zorder=2))
    ax.text(W + 11.5, hy + hs["h"] + 4,
            f"радіатор {hs['w']}×{hs['h']} — НАЗОВНІ,\n{hs['wall']}",
            ha="center", va="bottom", fontsize=5.8, color="#111", zorder=4)
    ax.annotate("", xy=(W + 5, amp["y"] + amp["h"] / 2), xytext=(W - 3, amp["y"] + amp["h"] / 2),
                arrowprops=dict(arrowstyle="->", color="#b03030", lw=1.3))

    # вводи в коробку
    def gland(gx, gy, text):
        ax.add_patch(Circle((gx, gy), 3.0, ec="#222", fc="#cfcfcf", lw=1.2, zorder=3))
        ax.text(gx, gy + 5.5, text, ha="center", va="bottom",
                fontsize=5.8, color="#111", zorder=4)

    k1 = next(m for m in P["modules"] if m["key"] == "k1")
    k2 = next(m for m in P["modules"] if m["key"] == "k2")
    rad = next(m for m in P["modules"] if m["key"] == "radar")
    gland(-17, k1["y"] + k1["h"] / 2, "гермоввід PG7\n12 В + запобіжник 3 А")
    ax.annotate("", xy=(k1["x"] - 1, k1["y"] + k1["h"] / 2), xytext=(-14, k1["y"] + k1["h"] / 2),
                arrowprops=dict(arrowstyle="->", color="#b03030", lw=1.3))
    gland(W + 17, k2["y"] + k2["h"] / 2, "гермоввід PG7\nна динамік")
    ax.annotate("", xy=(W + 13, k2["y"] + k2["h"] / 2), xytext=(k2["x"] + k2["w"] + 1, k2["y"] + k2["h"] / 2),
                arrowprops=dict(arrowstyle="->", color="#b03030", lw=1.3))
    ax.annotate("кабель 20 см до LD2410C\n(за вікном броні без металу)",
                xy=(rad["x"] + rad["w"] / 2, rad["y"] + rad["h"]),
                xytext=(rad["x"] + rad["w"] / 2, H + 13), ha="center",
                fontsize=5.8, color="#5a2d82",
                arrowprops=dict(arrowstyle="->", color="#5a2d82", lw=1))

    esp = next(m for m in P["modules"] if m["key"] == "esp32")
    ax.annotate("USB — до знімної кришки",
                xy=(esp["x"] + 3, esp["y"] + esp["h"] / 2),
                xytext=(-29, esp["y"] - 14), ha="left",
                fontsize=5.8, color="#1a5c7a",
                arrowprops=dict(arrowstyle="->", color="#1a5c7a", lw=1))

    # габарити
    ax.annotate("", xy=(0, -8), xytext=(W, -8),
                arrowprops=dict(arrowstyle="<->", color="#666", lw=1))
    ax.text(W / 2, -12, f"{W} мм", ha="center", fontsize=7, color="#444")
    ax.annotate("", xy=(-6, 0), xytext=(-6, H),
                arrowprops=dict(arrowstyle="<->", color="#666", lw=1))
    ax.text(-9, H / 2, f"{H} мм", ha="center", va="center", rotation=90,
            fontsize=7, color="#444")

    ax.text(W / 2, H + 21,
            f"ПАНЕЛЬ-ОСНОВА аудіо-вузла · перфоборд {W}×{H} мм, крок 2.54 · "
            f"плата на 4 стійках {P['standoff_mm']} мм — вузол виймається цілим",
            ha="center", fontsize=8.2, weight="bold", color="#222")
    ax.text(W / 2, -17,
            "Хедери паяти З ВСТАВЛЕНИМ модулем як шаблоном (рознесення рядів ESP32 буває 0.9″ і 1.0″). "
            "Динамік — окремо, у вирізі грудей, мембраною вниз.",
            ha="center", fontsize=6.4, color="#555")

    out = HERE / "assembly"
    fig.savefig(str(out) + ".png", bbox_inches="tight", facecolor="white")
    fig.savefig(str(out) + ".svg", bbox_inches="tight", facecolor="white")
    print("wrote assembly.png + assembly.svg")


if __name__ == "__main__":
    draw()
