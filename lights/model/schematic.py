#!/usr/bin/env python3
"""
Hero Armor lights node — wiring schematic (module-to-module).
Generates schematic.svg + schematic.png next to this file.

  SunGoldPower 500W --> Victron MPPT 100/20 --> LiFePO4 24V 200Ah (ANL 100A)
  24V bus --LVD1 23.6V--> Гр.1 (ШІМ-диммер -> 8x MR16 spot)
                      --> Гр.2 (WLED ESP32 -> WS2811 neon; лампи робота)
          --LVD2 22.2V--> Гр.3А (габаритні вогні + сходи) — аварійна лінія

Two LVD thresholds are the whole point: main light dies first, the emergency
line keeps the podium visible so nobody walks into it in the dark.
"""

import schemdraw
import schemdraw.elements as elm

schemdraw.config(fontsize=9, lw=1.4)

PIN_SP = 0.6
OUT = str(__import__("pathlib").Path(__file__).resolve().parent / "schematic")


def ic(left=(), right=(), top=(), bottom=(), w=3.2, pinspacing=PIN_SP, edgepad=0.45):
    """Sides listed bottom-up (left/right) or in listed order (top/bottom)."""
    pins = []
    for side, plist in (("left", left), ("right", right), ("top", top), ("bottom", bottom)):
        for pname, pinlabel, anchor in plist:
            pins.append(elm.IcPin(name=pname, pin=pinlabel, side=side,
                                  anchorname=anchor or pname))
    return elm.Ic(pins=pins, w=w, pinspacing=pinspacing, edgepadH=edgepad, leadlen=0.5)


with schemdraw.Drawing(file=OUT + ".svg", show=False) as d:

    # ---------------- solar panel -> MPPT ----------------
    panel = ic(right=[("−", "", "NEG"), ("+", "", "POS")], w=3.0, edgepad=0.7)
    d += panel.right().anchor("POS").at((0, 0)).label(
        "Сонячна панель\nSunGoldPower 500W\nVoc 44.4V · Vmp 37.6V", "top", fontsize=10)

    mppt = ic(left=[("PV−", "", "PVN"), ("PV+", "", "PVP")],
              right=[("BAT−", "", "BATN"), ("BAT+", "", "BATP")],
              w=3.4, edgepad=0.7)
    d += mppt.right().anchor("PVP").at((5.5, 0)).label(
        "Victron SmartSolar\nMPPT 100/20", "top", fontsize=10)
    d += elm.Line().at(panel.POS).to(mppt.PVP)
    d += elm.Line().at(panel.NEG).to(mppt.PVN)

    # ---------------- battery + main fuse ----------------
    fuse = elm.Fuse().right().at(mppt.BATP).length(2.0).label("ANL 100A", fontsize=9)
    d += fuse
    busbar = fuse.end
    d += elm.Dot().at(busbar)

    batt = elm.BatteryCell().at((13.0, -3.2)).up().label(
        "LiFePO4 24V 200Ah\n4800 Wh · DoD 80%", fontsize=9, loc="bottom")
    d += batt
    d += elm.Wire("|-").at(batt.end).to(busbar)
    d += elm.Ground().at(batt.start)
    d += elm.Line().at(mppt.BATN).to((mppt.absanchors["BATN"][0] + 1.0, mppt.absanchors["BATN"][1]))
    d += elm.Ground()

    d += elm.Line().up().at(busbar).length(0.9)
    d += elm.Vdd().label("шина 24V", fontsize=9)

    # ---------------- LVD split: main vs emergency ----------------
    lvd1 = ic(left=[("IN", "", "IN")], right=[("OUT", "", "OUT")], w=3.4, edgepad=0.6)
    d += lvd1.right().anchor("IN").at((16.5, 2.4)).label(
        "LVD #1 — поріг 23.6V\nICSTATION 20A", "top", fontsize=9)
    d += elm.Wire("-|").at(busbar).to(lvd1.IN)

    lvd2 = ic(left=[("IN", "", "IN")], right=[("OUT", "", "OUT")], w=3.4, edgepad=0.6)
    d += lvd2.right().anchor("IN").at((16.5, -5.0)).label(
        "LVD #2 — поріг 22.2V\nаварійна лінія", "bottom", fontsize=9)
    d += elm.Wire("-|").at(busbar).to(lvd2.IN)

    # ---------------- Гр.1 — прожектори через ШІМ-диммер ----------------
    d += elm.Label().at((20.6, 4.6)).label("Гр.1 · 40W пік", fontsize=10, color="#b35b1e")
    dim = ic(left=[("IN", "", "IN")], right=[("OUT", "", "OUT")], w=3.2, edgepad=0.6)
    d += dim.right().anchor("IN").at((22.5, 5.8)).label(
        "ШІМ-диммер\nSUPERNIGHT 12-24V 30A", "top", fontsize=9)
    d += elm.Wire("-|").at(lvd1.OUT).to(dim.IN)

    d += elm.Lamp().right().at((30.0, 5.8)).label("8× MR16 5W · 4000K · 60°", "top", fontsize=8)
    d += elm.Line().at(dim.OUT).to((30.0, 5.8))

    # ---------------- Гр.2 — WLED -> адресний неон + лампи робота ----------------
    d += elm.Label().at((20.6, 0.2)).label("Гр.2 · 155W пік", fontsize=10, color="#b35b1e")
    wled = ic(left=[("5-24V", "", "VIN")], right=[("DATA", "", "DATA"), ("V+", "", "VOUT")],
              w=3.2, edgepad=0.6)
    d += wled.right().anchor("VIN").at((22.5, 1.4)).label(
        "GLEDOPTO ESP32 WLED\nIP65 · WiFi", "top", fontsize=9)
    d += elm.Wire("-|").at(lvd1.OUT).to(wled.VIN)

    strip = ic(left=[("DIN", "", "DIN"), ("+24V", "", "VP")], w=3.6, edgepad=0.6)
    d += strip.right().anchor("DIN").at((30.0, 1.4)).label(
        "WS2811 24V неон\nкільце 2.17м + 8×0.95м", "top", fontsize=9)
    d += elm.Line().at(wled.DATA).to(strip.DIN)
    d += elm.Line().at(wled.VOUT).to(strip.VP)
    d += elm.Label().at((32.2, -0.4)).label(
        "power injection кожні 2.5–3 м\nвдень ВИМКНЕНО (перегрів чипів)", fontsize=8)

    d += elm.Lamp().right().at((23.5, -2.4)).label(
        "8× 12мм + 2× 8мм — лампи робота 0.4W", "bottom", fontsize=8)
    d += elm.Wire("-|").at(lvd1.OUT).to((23.5, -2.4))

    # ---------------- Гр.3А — аварійна лінія ----------------
    d += elm.Label().at((26.5, -4.4)).label("Гр.3А · 48W — аварійна", fontsize=10, color="#3d7a4f")
    d += elm.Lamp().right().at((23.5, -6.4)).label(
        "8× габаритні 3W\nNilight IP67", "bottom", fontsize=8)
    d += elm.Wire("-|").at(lvd2.OUT).to((23.5, -6.4))

    d += elm.Lamp().right().at((30.0, -6.4)).label(
        "24× сходи 1W\nврізні IP67", "bottom", fontsize=8)
    d += elm.Wire("-|").at(lvd2.OUT).to((30.0, -6.4))

    # ---------------- notes ----------------
    d += elm.Label().at((8.0, -9.0)).label(
        "Шина 24V, не 12V: удвічі менший струм — удвічі менша просадка в довгих лініях.\n"
        "Кабель: магістраль Ancor 8/2 AWG, відгалуження 12/2 AWG (просадка < 3% у всіх режимах).\n"
        "Два пороги LVD — головне рішення: на 23.6V гасне основне світло, на 22.2V — аварійне,\n"
        "щоб подіум лишався видимим до останнього. Земля — зіркою в одній точці біля АКБ.\n"
        "Все обладнання в тінь, зазор від землі 5+ см, плати вкриті лаком MG 422B (пил pH 9-10).",
        fontsize=8)

d.save(OUT + ".png", dpi=200)
print("wrote schematic.svg + schematic.png")
