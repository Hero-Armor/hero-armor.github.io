#!/usr/bin/env python3
"""Креслення ящика станції: розріз із потоком повітря + два графіки.

Генерує поруч із собою:
  schematic.svg/.png — розріз ящика: станція, зазори, дві ступені фільтра,
                       вентилятор на нагнітання, гермовводи, тінь.
  thermal.svg/.png   — скільки потоку треба залежно від температури надворі.
  cooler.svg/.png    — гіпотеза теплової маси: температура води по годинах.

Жодної цифри руками: усе береться з enclosure/data/params.json і моделі.
"""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import enclosure_model as enc  # noqa: E402

P = json.loads((HERE.parent / "data" / "params.json").read_text())
INK, INK2, LINE = "#24231d", "#6b675c", "#d8d5c9"
ACCENT, SIGNAL, GOOD, CRIT = "#b35b1e", "#3d6f96", "#3d7a4f", "#b23a2e"
plt.rcParams.update({"font.size": 9, "font.family": "DejaVu Sans",
                     "text.color": INK, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2})


def save(fig, name):
    for ext in ("svg", "png"):
        fig.savefig(HERE / f"{name}.{ext}", bbox_inches="tight",
                    transparent=(ext == "svg"), dpi=140)
    plt.close(fig)


# ------------------------------------------------------------------ розріз
def draw_section():
    cl = P["fit"]["clearance_mm"]
    amb = P["ambient"]
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_xlim(0, 100); ax.set_ylim(0, 52); ax.axis("off")

    # тінь над ящиком — вона важить більше за вентилятор
    ax.add_patch(Rectangle((6, 45), 76, 2.4, fc="#c9c5b6", ec="none"))
    ax.text(44, 48.4, f'ТІНЬ  ·  без неї ящик бачить {amb["playa_sun_c"]} °C замість '
            f'{amb["playa_shade_c"]}', ha="center", color=INK2, fontsize=9)

    # ящик
    ax.add_patch(Rectangle((14, 8), 62, 32, fc="none", ec=INK, lw=2.2))
    # станція всередині з зазором
    ax.add_patch(Rectangle((26, 13), 38, 22, fc="#efeee7", ec=INK, lw=1.6))
    ax.text(45, 25.5, "СТАНЦІЯ", ha="center", va="center", fontsize=11,
            color=INK, fontweight="bold")
    ax.text(45, 21.5, "вентилятори станції — на бокових\nгранях, їх не перекривати",
            ha="center", va="center", fontsize=7.5, color=INK2)

    # зазор
    for x0, x1, y in ((14, 26, 36.6), (64, 76, 36.6)):
        ax.annotate("", xy=(x0, y), xytext=(x1, y),
                    arrowprops=dict(arrowstyle="<->", color=SIGNAL, lw=1.1))
    ax.text(20, 37.8, f"{cl} мм", ha="center", fontsize=8, color=SIGNAL)
    ax.text(70, 37.8, f"{cl} мм", ha="center", fontsize=8, color=SIGNAL)
    ax.text(45, 9.6, "зазор не «щоб не тиснуло», а щоб повітрю було куди йти",
            ha="center", fontsize=7.5, color=SIGNAL)

    # вхід: дві ступені + вентилятор на нагнітання
    ax.add_patch(Rectangle((1.5, 20), 4.5, 12, fc="#e8e4d6", ec=INK, lw=1.3))
    ax.text(3.75, 33.6, "поролон", ha="center", fontsize=7.5, color=INK2)
    ax.text(3.75, 26, "1", ha="center", va="center", fontsize=13,
            color=ACCENT, fontweight="bold")
    ax.add_patch(Rectangle((7, 20), 4.5, 12, fc="#dfe7ee", ec=INK, lw=1.3))
    ax.text(9.25, 35.4, "MERV 13", ha="center", fontsize=7.5, color=INK2)
    ax.plot([9.25, 9.25], [32.2, 34.9], color=LINE, lw=.8)
    ax.text(9.25, 26, "2", ha="center", va="center", fontsize=13,
            color=SIGNAL, fontweight="bold")
    ax.add_patch(FancyArrowPatch((11.8, 26), (18.5, 26), color=GOOD,
                                 arrowstyle="-|>", mutation_scale=17, lw=2.2))
    ax.text(14.4, 15.5, "ДМЕМО\nВСЕРЕДИНУ", ha="center", fontsize=7.5,
            color=GOOD, fontweight="bold")

    # надлишковий тиск + витік назовні
    lo, hi = P["pressure"]["target_pa"]
    ax.text(45, 42, f"надлишковий тиск {lo}–{hi} Па", ha="center",
            fontsize=9, color=GOOD, fontweight="bold")
    for x, y in ((21, 39.4), (69, 39.4), (76.6, 16)):
        ax.add_patch(FancyArrowPatch((x, y), (x + 3.2, y + 1.6), color=GOOD,
                                     arrowstyle="-|>", mutation_scale=10, lw=1.2))
    ax.text(88, 41.6, "витік іде НАЗОВНІ —\nпил не заходить\nпроти градієнта",
            ha="center", fontsize=7.5, color=GOOD)

    # пасивний випуск
    ax.add_patch(Rectangle((76, 21), 2.2, 8, fc="#efeee7", ec=INK, lw=1.2))
    ax.text(83.5, 25, "жалюзі\nна випуск", ha="center", va="center",
            fontsize=7.5, color=INK2)

    # гермовводи знизу
    for x in (34, 44, 54):
        ax.add_patch(Rectangle((x, 6.4), 3.2, 1.8, fc="#efeee7", ec=INK, lw=1.1))
    ax.annotate("гермовводи: кабель 12 В і сонце.\n"
                "під кришкою не виводити — фільтрація втратить сенс",
                xy=(44, 6.3), xytext=(44, 0.6), ha="center", fontsize=7.5, color=INK2,
                arrowprops=dict(arrowstyle="-", color=LINE, lw=.8))

    # підставка
    ax.add_patch(Rectangle((14, 4.2), 62, 1.4, fc="#c9c5b6", ec="none"))
    ax.text(89, 4.6, "підставка —\nземля плайї пече", ha="center",
            fontsize=7.5, color=INK2)

    ax.text(0, 50.4, "Ящик станції — розріз", fontsize=13, fontweight="bold", color=INK)
    save(fig, "schematic")


# ------------------------------------------------------------------ тепло
def draw_thermal():
    amb = P["ambient"]
    heat = enc.heat_w()
    temps = list(range(30, int(amb["playa_sun_c"]) + 1))
    cfm, blocked = [], []
    for t in temps:
        r = enc.need_cfm(t)
        cfm.append(r["cfm"] if r["cfm"] else float("nan"))
        if r["cfm"] is None:
            blocked.append(t)

    fig, ax = plt.subplots(figsize=(8.6, 3.9))
    ax.plot(temps, cfm, color=ACCENT, lw=2.4, zorder=3)
    if blocked:
        ax.axvspan(min(blocked) - .5, max(temps) + .5, color="#f3ded9", zorder=0)
        ax.text((min(blocked) + max(temps)) / 2, ax.get_ylim()[1] * .55,
                "вентилятор\nне рятує:\nповітря вже\nгарячіше за межу",
                ha="center", color=CRIT, fontsize=8.5, fontweight="bold")
    ax.axvline(amb["playa_shade_c"], color=SIGNAL, ls="--", lw=1.2)
    ax.text(amb["playa_shade_c"] - .3, ax.get_ylim()[1] * .9, "у тіні на плайї",
            ha="right", color=SIGNAL, fontsize=8.5)
    ax.axvline(amb["playa_sun_c"], color=CRIT, ls="--", lw=1.2)
    ax.text(amb["playa_sun_c"] - .3, ax.get_ylim()[1] * .9, "на сонці",
            ha="right", color=CRIT, fontsize=8.5)
    for f in P["fans"]:
        ax.axhline(f["cfm"] * P["air"]["filter_derate"], color=LINE, lw=1)
        ax.text(temps[0] + .2, f["cfm"] * P["air"]["filter_derate"] + 1.5,
                f'{f["name"]} — {f["cfm"] * P["air"]["filter_derate"]:.0f} CFM з фільтром',
                fontsize=7, color=INK2)
    ax.set_xlabel("температура повітря надворі, °C")
    ax.set_ylabel("потрібний потік, CFM")
    ax.set_title(f'Скільки продуву треба: {heat:.0f} Вт тепла, межа станції '
                 f'{amb["station_limit_c"]} °C', fontsize=11, color=INK, loc="left")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(LINE); ax.spines["left"].set_color(LINE)
    ax.grid(axis="y", color=LINE, lw=.6, alpha=.6)
    save(fig, "thermal")


# ------------------------------------------------------------------ кулер
def draw_cooler():
    heat = enc.heat_w()
    amb_day = P["ambient"]["playa_shade_c"]
    limit = P["ambient"]["station_limit_c"]
    L, W, H = 0.60, 0.40, 0.45
    area = 2 * (L * W + L * H + W * H)
    u = 1 / (1 / (0.033 / 0.030) + 1 / 10 + 1 / 8)   # кулер 30 мм + плівки
    c_w, t0, hours = 4186.0, 14.0, 10

    fig, ax = plt.subplots(figsize=(8.6, 3.9))
    for mass, col in ((10, "#c9c5b6"), (20, SIGNAL), (30, ACCENT), (40, GOOD)):
        t, xs, ys = t0, [], []
        for step in range(hours * 60):
            xs.append(step / 60); ys.append(t)
            t += (heat + u * area * (amb_day - t)) * 60 / (mass * c_w)
        ax.plot(xs, ys, color=col, lw=2.2, label=f"{mass} кг води")
    ax.axhline(35, color=CRIT, ls="--", lw=1.2)
    ax.text(.1, 35.8, "поріг 35 °C — далі станція близько до межі",
            color=CRIT, fontsize=8.5)
    ax.axhline(limit, color=CRIT, lw=1.4)
    ax.text(.1, limit + .8, f"паспортна межа {limit} °C", color=CRIT,
            fontsize=8.5, fontweight="bold")
    ax.set_xlabel("годин світлового дня")
    ax.set_ylabel("температура води (≈ станції), °C")
    ax.set_title("Гіпотеза кулера: вода за ніч остигає до 14 °C і тримає день",
                 fontsize=11, color=INK, loc="left")
    ax.legend(frameon=False, fontsize=8.5, loc="lower right")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(LINE); ax.spines["left"].set_color(LINE)
    ax.grid(axis="y", color=LINE, lw=.6, alpha=.6)
    save(fig, "cooler")


if __name__ == "__main__":
    draw_section(); draw_thermal(); draw_cooler()
    print("enclosure: schematic / thermal / cooler — svg+png")
