#!/usr/bin/env python3
"""
Hero Armor power node — schematic of the station + self-built array.
Generates schematic.svg + schematic.png next to this file.

  Самозбірний масив панелей --MC4--> сонячний вхід EcoFlow
  EcoFlow 12V DC out --> щит світла (три групи)
                     --> аудіо-вузол
  Станція змінна: сіла -> на базу під розетку, на її місце заряджена.
"""

import matplotlib
# підписи на схемі мають лишатись ТЕКСТОМ, а не кривими: інакше
# англійська версія дашборда не може їх перекласти
matplotlib.rcParams["svg.fonttype"] = "none"

import schemdraw
import schemdraw.elements as elm

schemdraw.config(fontsize=9, lw=1.4)
OUT = str(__import__("pathlib").Path(__file__).resolve().parent / "schematic")


def ic(left=(), right=(), w=3.2, pinspacing=0.6, edgepad=0.5):
    pins = []
    for side, plist in (("left", left), ("right", right)):
        for pname, pinlabel, anchor in plist:
            pins.append(elm.IcPin(name=pname, pin=pinlabel, side=side,
                                  anchorname=anchor or pname))
    return elm.Ic(pins=pins, w=w, pinspacing=pinspacing, edgepadH=edgepad, leadlen=0.5)


with schemdraw.Drawing(file=OUT + ".svg", show=False) as d:

    # ---------------- self-built array ----------------
    arr = ic(right=[("−", "", "NEG"), ("+", "", "POS")], w=3.4, edgepad=0.9)
    d += arr.right().anchor("POS").at((0, 0)).label(
        "Масив панелей (збираємо самі)\n600 Вт · рама під нахил\n"
        "мити скло щодня — пил ріже вихід", "top", fontsize=10)

    # ---------------- EcoFlow station ----------------
    eco = ic(left=[("SOLAR", "сонце", "SOL"), ("AC", "розетка", "AC")],
             right=[("DC1", "12V", "DC1"), ("DC2", "12V", "DC2")],
             w=4.2, pinspacing=1.4, edgepad=1.0)
    d += eco.right().anchor("SOL").at((7.0, 0)).label(
        "EcoFlow Delta 2 Max\n2048 Wh · вхід сонця до 1000 Вт", "top", fontsize=10)
    d += elm.Line().at(arr.POS).to(eco.SOL).label("MC4", "top", fontsize=8)
    d += elm.Line().at(arr.NEG).to((eco.absanchors["SOL"][0] - 0.5,
                                    arr.absanchors["NEG"][1]))

    d += elm.Line().left().at(eco.AC).length(1.6)
    d += elm.Dot(open=True).label("на базі — у розетку", "left", fontsize=8)

    # ---------------- consumers ----------------
    lights_box = ic(left=[("IN", "", "IN")], w=4.0, edgepad=0.9)
    d += lights_box.right().anchor("IN").at((15.5, 1.4)).label(
        "СВІТЛО · щит подіуму\nГр.1 прожектори · Гр.2 декор\nГр.3А аварійна",
        "top", fontsize=10)
    d += elm.Wire("-|").at(eco.DC2).to(lights_box.IN).label("1416 Wh/добу", "top", fontsize=8)

    audio_box = ic(left=[("IN", "", "IN")], w=4.0, edgepad=0.9)
    d += audio_box.right().anchor("IN").at((15.5, -2.6)).label(
        "ЗВУК · вартовий\nрадар → ESP32 → підсилювач", "top", fontsize=10)
    d += elm.Wire("-|").at(eco.DC1).to(audio_box.IN).label("39 Wh/добу", "top", fontsize=8)

    # ---------------- swap loop ----------------
    d += elm.Label().at((7.5, -5.2)).label(
        "ПІДМІНА СТАНЦІЇ\nПанелі стали або станція сіла — знімаємо, ставимо заряджену,\n"
        "цю везем на базу під розетку. Повна зарядка ~1.5 год.\n"
        "Тому потрібні ДВІ станції, а не одна.", fontsize=9, color="#b35b1e")

    d += elm.Label().at((7.5, -8.0)).label(
        "Без панелей станція тримає рівно добу — масив не «на всяк випадок», а несуча частина.\n"
        "Запилене скло на 40% ріже вихід сильніше, ніж здається: підміна вже через ~5 діб.\n"
        "Станцію і панелі — в тінь і від землі; пил плайї лужний, роз'єми чистити стисненим повітрям.",
        fontsize=8)

d.save(OUT + ".png", dpi=200)
print("wrote schematic.svg + schematic.png")
