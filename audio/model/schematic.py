#!/usr/bin/env python3
"""
Hero Armor audio node — wiring schematic (module-to-module, pin-to-pin).
Generates schematic.svg + schematic.png next to this file.

  12V (EcoFlow DC port) --fuse--> TPA3116D2 MONO amp + buck 12->5V
  5V  --> ESP32 VIN, PCM5102A VIN, LD2410C VCC;  3V3 (from ESP32 LDO) --> SD, XSMT
  ESP32: I2S -> PCM5102A -> L analog -> mono amp -> 1x MA-3013 speaker
         (second speaker of the pair = ready spare)
         SPI -> microSD;  GPIO27/UART2 <-> LD2410C
  LDR divider (3V3 - LDR - GPIO34 - 10k - GND): auto day/night volume profile
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

    # ---------------- ESP32 ----------------
    esp = ic(
        left=[("GND", "", "GND"), ("VIN", "", "VIN"),
              ("GPIO5", "CS", "CS"), ("GPIO18", "SCK", "SCK"),
              ("GPIO23", "MOSI", "MOSI"), ("GPIO19", "MISO", "MISO")],
        right=[("GPIO26", "BCK", "BCK"), ("GPIO25", "LRCK", "LRCK"),
               ("GPIO22", "DIN", "DIN")],
        bottom=[("27", "", "ROUT"), ("16", "", "RX2"), ("17", "", "TX2")],
        w=3.6, edgepad=0.8)
    d += esp.right().anchor("center").at((0, 0)).label(
        "ESP32 WROOM-32 DevKit", "top", fontsize=10)

    d += elm.Vdd().at(esp.VIN).left().label("5V", fontsize=9)
    d += elm.Ground().at(esp.GND).left()

    # ---------------- microSD (left, SPI) ----------------
    sd = ic(
        right=[("CS", "", "CS"), ("SCK", "", "SCK"),
               ("MOSI", "", "MOSI"), ("MISO", "", "MISO")],
        left=[("GND", "", "GND"), ("VCC", "", "VCC")],
        w=2.6)
    d += sd.right().anchor("CS").at((-7.5, esp.absanchors["CS"][1])).label(
        "microSD SPI\nSanDisk 32GB, MP3", "top", fontsize=10)
    d += elm.Vdd().at(sd.VCC).left().label("5V", fontsize=9)  # HiLetgo-type module: LDO + level shifter onboard
    d += elm.Ground().at(sd.GND).left()
    for p in ("CS", "SCK", "MOSI", "MISO"):
        d += elm.Line().at(sd.absanchors[p]).to(esp.absanchors[p])

    # ---------------- PCM5102A DAC (right, I2S) ----------------
    dac = ic(
        left=[("BCK", "", "BCK"), ("LCK", "", "LCK"), ("DIN", "", "DIN"),
              ("SCK", "", "PSCK"), ("FMT", "", "FMT"), ("XSMT", "", "XSMT"),
              ("VIN", "", "VIN"), ("GND", "", "GND")],
        right=[("AGND", "", "AGND"), ("L", "", "L")],
        w=2.8)
    d += dac.right().anchor("BCK").at((7.0, esp.absanchors["BCK"][1])).label(
        "PCM5102A (GY-PCM5102)", "top", fontsize=10)
    d += elm.Line().at(esp.BCK).to(dac.BCK)
    d += elm.Line().at(esp.LRCK).to(dac.LCK)
    d += elm.Line().at(esp.DIN).to(dac.DIN)
    # config: SCK->GND (internal PLL), FMT->GND (I2S), XSMT->3V3 (unmute)
    d += elm.Ground().at(dac.PSCK).left()
    d += elm.Ground().at(dac.FMT).left()
    d += elm.Vdd().at(dac.XSMT).left().label("3V3", fontsize=9)
    d += elm.Vdd().at(dac.VIN).left().label("5V", fontsize=9)
    d += elm.Ground().at(dac.GND).left()

    # ---------------- LD2410C radar (below ESP32) ----------------
    radar = ic(
        top=[("OUT", "", "OUT"), ("TX", "", "TX"), ("RX", "", "RX")],
        left=[("GND", "", "GND"), ("VCC", "", "VCC")],
        w=3.4, pinspacing=1.1, edgepad=0.9)
    d += radar.right().anchor("OUT").at(
        (esp.absanchors["ROUT"][0], esp.absanchors["ROUT"][1] - 2.2)).label(
        "LD2410C mmWave 24GHz", "bottom", fontsize=10)
    d += elm.Wire("|-").at(esp.ROUT).to(radar.OUT)
    d += elm.Wire("|-").at(esp.RX2).to(radar.TX)
    d += elm.Wire("|-").at(esp.TX2).to(radar.RX)
    d += elm.Vdd().at(radar.VCC).left().label("5V", fontsize=9)
    d += elm.Ground().at(radar.GND).left()

    # ---------------- TPA3116D2 mono amp, single MA-3013 ----------------
    amp = ic(
        left=[("INM", "IN-", "INM"), ("INP", "IN+", "INP"), ("VCC", "", "VCC")],
        right=[("GND", "", "PGND"), ("OUTM", "OUT-", "OUTM"), ("OUTP", "OUT+", "OUTP")],
        w=3.2)
    d += amp.right().anchor("INM").at((13.5, dac.absanchors["AGND"][1])).label(
        "TPA3116D2 Mono — радіатор назовні!", "top", fontsize=10)
    d += elm.Line().at(dac.AGND).to(amp.INM)
    d += elm.Line().at(dac.L).to(amp.INP).label("екранований кабель", "top", fontsize=8)
    d += elm.Vdd().at(amp.VCC).left().label("12V", fontsize=9)
    d += elm.Ground().at(amp.PGND).right()

    # one speaker; second MA-3013 of the pair is kept as a ready spare
    spk = elm.Speaker().right().at(
        (19.0, amp.absanchors["OUTP"][1])).anchor("in1")
    d += spk
    d += elm.Line().at(amp.OUTP).to(spk.in1)
    d += elm.Wire("-|").at(amp.OUTM).to(spk.in2)
    d += elm.Label().at((19.9, amp.absanchors["OUTP"][1] - 1.6)).label(
        "MA-3013 4Ω, мембрана вниз\n(другий з пари — запас)", fontsize=8)

    # ---------------- power section (bottom left) ----------------
    y0 = -8.5
    batt = elm.BatteryCell().at((-12.0, y0)).up().label(
        "EcoFlow 12.6V\nприкурювач → XT60", fontsize=9)
    d += batt
    fuse = elm.Fuse().right().at(batt.end).label("3A", fontsize=9)
    d += fuse
    node12 = fuse.end
    d += elm.Dot().at(node12)
    d += elm.Line().right().at(node12).length(1.0)
    d += elm.Vdd().label("12V", fontsize=9)
    cap = elm.Capacitor(polar=True).at(node12).down().length(1.5).label(
        "1000µF\nбіля ампа", fontsize=8, loc="bottom")
    d += cap
    d += elm.Ground().at(cap.end)
    d += elm.Ground().at(batt.start)

    buck = ic(
        left=[("GND", "", "GNDI"), ("+12V", "", "VIN12")],
        right=[("GND", "", "GNDO"), ("+5V", "", "V5")],
        w=3.0)
    d += buck.right().anchor("VIN12").at((-7.5, y0 + 0.5)).label(
        "Buck 12→5V ≥1.5A\nMP1584 + LC фільтр", "top", fontsize=10)
    d += elm.Wire("-|").at(node12).to(buck.VIN12)
    d += elm.Ground().at(buck.GNDI).left()
    d += elm.Line().right().at(buck.V5).length(1.0)
    d += elm.Vdd().label("5V", fontsize=9)
    d += elm.Ground().at(buck.GNDO).right()

    # ---------------- LDR: auto day/night sensing on GPIO34 ----------------
    d += elm.Label().at((4.4, y0 + 4.9)).label("Авто день/ніч", fontsize=9)
    d += elm.Vdd().at((4.2, y0 + 3.6)).label("3V3", fontsize=9)
    ldr = elm.Photoresistor().at((4.2, y0 + 3.6)).down().length(1.4).label("LDR", fontsize=8)
    d += ldr
    d += elm.Dot().at(ldr.end)
    d += elm.Line().at(ldr.end).right().length(0.8).label("→ GPIO34 (ADC)", "right", fontsize=8)
    r10 = elm.Resistor().at(ldr.end).down().length(1.4).label("10k", fontsize=8)
    d += r10
    d += elm.Ground().at(r10.end)

    d += elm.Label().at((6.0, y0 - 0.5)).label(
        "Земля: зіркою в одній точці біля АКБ.\n"
        "3V3 — з стабілізатора плати ESP32 (пін 3V3).\n"
        "AGND ЦАП → амп окремим проводом (не через силову землю).\n"
        "LD2410C — за вікном у броні БЕЗ металу (ABS/акрил/склотканина).", fontsize=8)

d.save(OUT + ".png", dpi=220)
print("wrote schematic.svg + schematic.png")
