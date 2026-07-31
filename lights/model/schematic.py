#!/usr/bin/env python3
"""
Hero Armor lights node — wiring schematic, 12V bus.
Generates schematic.svg + schematic.png next to this file.

Starts at the station's 12V output — everything upstream (panels, EcoFlow,
swap logic) belongs to the power node and lives in solar/model/schematic.py.

  12V from station --> щит подіуму --> Гр.1 ШІМ-диммер -> 8x MR16
                                   --> Гр.2 WLED -> WS2811 неон; лампи робота
                                   --> Гр.3А габаритні вогні + сходи (аварійна)
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lights_node_model as lm

import matplotlib
# підписи лишаються ТЕКСТОМ, а не кривими: інакше англійська
# версія дашборда не може їх перекласти
matplotlib.rcParams["svg.fonttype"] = "none"

import schemdraw
import schemdraw.elements as elm

FUSES = {f["id"]: f for f in lm.fuses()}
PEAK = lm.peak_watts()

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

    # ---------------- 12V in from the station ----------------
    d += elm.Vdd().at((0, 0)).label("12V зі станції EcoFlow", fontsize=10)
    d += elm.Line().down().at((0, 0)).length(1.2)
    fuse = elm.Fuse().right().length(2.2).label(f"{FUSES['main']['rating']}A", fontsize=9)
    d += fuse
    bus = fuse.end
    d += elm.Dot().at(bus)
    d += elm.Label().at((1.0, -2.6)).label(
        "магістраль AWG 8 (наявна)\nтільки світло — звук іде своїм кабелем", fontsize=8)

    panel_box = ic(left=[("IN", "", "IN")],
                   right=[("G3A", "Гр.3А", "G3A"), ("G2", "Гр.2", "G2"), ("G1", "Гр.1", "G1")],
                   w=3.6, pinspacing=2.2, edgepad=1.0)
    d += panel_box.right().anchor("IN").at((5.5, 0)).label(
        "Щит подіуму\n4 запобіжники + 3 групові реле", "top", fontsize=10)
    d += elm.Line().at(bus).to(panel_box.IN)

    # ---------------- Гр.1 spots ----------------
    dim = ic(left=[("IN", "", "IN")], right=[("OUT", "", "OUT")], w=3.2, edgepad=0.6)
    d += dim.right().anchor("IN").at((12.0, 2.2)).label(
        "ШІМ-диммер\nSUPERNIGHT 30A", "top", fontsize=9)
    d += elm.Wire("-|").at(panel_box.G1).to(dim.IN)
    d += elm.Lamp().right().at((19.0, 2.2)).label(
        "8× MR16 5W · 4000K · 60°\nрегулюються напругою", "top", fontsize=8)
    d += elm.Line().at(dim.OUT).to((19.0, 2.2))
    d += elm.Label().at((10.2, 3.0)).label(f"Гр.1 · {PEAK['g1']:.0f} Вт · запобіжник {FUSES['g1']['rating']}A",
                    fontsize=10, color="#b35b1e")

    # ---------------- Гр.2 decor ----------------
    wled = ic(left=[("VIN", "12V", "VIN")], right=[("DATA", "DATA", "DATA")],
              w=3.2, edgepad=0.6)
    d += wled.right().anchor("VIN").at((12.0, -1.4)).label(
        "ESP32 WLED\nIP65 · WiFi", "top", fontsize=9)
    d += elm.Wire("-|").at(panel_box.G2).to(wled.VIN)

    strip = ic(left=[("DIN", "", "DIN")], w=3.6, edgepad=0.7)
    d += strip.right().anchor("DIN").at((19.0, -1.4)).label(
        "WS2811 12V неон\nкільце 2.17м + 8× 0.95м", "top", fontsize=9)
    d += elm.Line().at(wled.DATA).to(strip.DIN)
    d += elm.Label().at((14.8, -3.8)).label(
        "лінія декору AWG 8 → інжекція AWG 14", fontsize=8)
    d += elm.Label().at((21.5, -3.2)).label(
        "power injection кожні 2.5–3 м\nвдень ВИМКНЕНО (перегрів чипів)", fontsize=8)

    d += elm.Lamp().right().at((12.5, -5.0)).label(
        "8× 12мм + 2× 8мм — лампи робота", "bottom", fontsize=8)
    d += elm.Wire("-|").at(panel_box.G2).to((12.5, -5.0))
    d += elm.Label().at((10.2, -0.6)).label(f"Гр.2 · {PEAK['g2']:.0f} Вт · запобіжник {FUSES['g2']['rating']}A",
                    fontsize=10, color="#b35b1e")

    # ---------------- Гр.3А emergency ----------------
    d += elm.Label().at((10.2, -6.6)).label(
        f"Гр.3А · {PEAK['g3a']:.0f} Вт · запобіжник {FUSES['g3a']['rating']}A\n"
        "аварійна, не регулюється", fontsize=10, color="#3d7a4f")
    d += elm.Lamp().right().at((12.5, -8.0)).label(
        "8× габаритні 3W\nNilight IP67", "bottom", fontsize=8)
    d += elm.Wire("-|").at(panel_box.G3A).to((12.5, -8.0))
    d += elm.Lamp().right().at((19.0, -8.0)).label(
        "24× сходи 1W\nврізні IP67", "bottom", fontsize=8)
    d += elm.Wire("-|").at(panel_box.G3A).to((19.0, -8.0))

    d += elm.Label().at((5.5, 4.6)).label(
        "На кожній групі своє реле 12В/30А (гасимо групи по черзі).\n"
        "Чим їх вмикати — ще не обрано: ручний вимикач у щиті або вихід WLED\n"
        "(фотореле з проєкту прибрано 29.07).", fontsize=8)
    d += elm.Label().at((8.0, -10.6)).label(
        "Три лінії окремі, щоб гасити їх по черзі: коли станція сідає, першими йдуть\n"
        "прожектори і декор, а габарити зі сходами тримаються найдовше — щоб у темряві\n"
        "ніхто не наштовхнувся на подіум. Аварійна лінія за ніч з'їдає стільки ж, як декор.\n"
        "Земля — зіркою в одній точці біля щита. Все обладнання в тінь, зазор від землі 5+ см.",
        fontsize=8)

d.save(OUT + ".png", dpi=200)
print("wrote schematic.svg + schematic.png")
