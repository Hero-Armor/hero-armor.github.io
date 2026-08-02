#!/usr/bin/env python3
"""
Hero Armor audio node — wiring schematic (module-to-module, pin-to-pin).
Generates schematic.svg + schematic.png next to this file.

  12V (auto/cigarette port of the station, OWN cable) --fuse--> TPA3116D2 MONO amp + buck 12->5V
  5V  --> ESP32 VIN, PCM5102A VIN, LD2410C VCC, microSD;  3V3 (from ESP32 LDO) --> XSMT
  ESP32: I2S -> PCM5102A -> L analog -> mono amp -> 1x MA-3013 speaker
         (second speaker of the pair = ready spare)
         SPI -> microSD;  D27/UART2 (RX2,TX2) <-> LD2410C
"""

import matplotlib
# підписи на схемі мають лишатись ТЕКСТОМ, а не кривими: інакше
# англійська версія дашборда не може їх перекласти
matplotlib.rcParams["svg.fonttype"] = "none"

import schemdraw
import schemdraw.elements as elm

schemdraw.config(fontsize=9, lw=1.4)

PIN_SP = 0.6
OUT = str(__import__("pathlib").Path(__file__).resolve().parent / "schematic")


def ic(left=(), right=(), top=(), bottom=(), w=3.2, pinspacing=PIN_SP, edgepad=0.45,
       side_spacing=None, size=None):
    """Sides listed bottom-up (left/right) or in listed order (top/bottom)."""
    pins = []
    for side, plist in (("left", left), ("right", right), ("top", top), ("bottom", bottom)):
        for spec in plist:
            # (ім'я, номер ніжки, якір) або з п'ятим значенням — позиція вздовж
            # сторони 0..1, коли підписи довгі і злипаються (низ ESP32)
            pname, pinlabel, anchor = spec[0], spec[1], spec[2]
            pos = spec[3] if len(spec) > 3 else None
            kw = {"pos": pos} if pos is not None else {}
            pins.append(elm.IcPin(name=pname, pin=pinlabel, side=side,
                                  anchorname=anchor or pname, **kw))
    kw = {"size": size} if size else {}
    e = elm.Ic(pins=pins, w=w, pinspacing=pinspacing, edgepadH=edgepad, leadlen=0.5, **kw)
    for side, sp in (side_spacing or {}).items():
        # свій крок для однієї сторони: коли підписи довгі, вони злипаються
        e.side(side, spacing=sp, pad=0.9, leadlen=0.5)
    return e



def power_in(d, elem, vcc_anchor, gnd_anchor, label, lead=0.7):
    """Живлення і земля модуля — рознесені, а не двома значками впритул.

    Коли elm.Vdd() і elm.Ground() стоять на сусідніх пінах, вони зливаються
    в одну картинку і читаються як деталь між VCC і GND (Іван 02.08: «діод?»).
    Тому земля йде вбік і ВНИЗ, живлення — вбік і вгору.
    """
    v = elm.Line().at(elem.absanchors[vcc_anchor]).left().length(lead)
    d += v
    d += elm.Vdd().at(v.end).label(label, fontsize=9)
    g = elm.Line().at(elem.absanchors[gnd_anchor]).left().length(lead)
    d += g
    d += elm.Line().at(g.end).down().length(0.9)
    d += elm.Ground()


with schemdraw.Drawing(file=OUT + ".svg", show=False) as d:

    # ---------------- ESP32 ----------------
    esp = ic(
        # Підписи — ЯК НА ПЛАТІ (шовкографія DevKit V1), а не номери GPIO:
        # їх шукає людина з паяльником. Де ім'я не збігається з номером —
        # номер у дужках (Іван, 02.08.2026).
        left=[("GND", "", "GND"), ("VIN", "", "VIN"),
              ("D5", "CS", "CS"), ("D18", "SCK", "SCK"),
              ("D23", "MOSI", "MOSI"), ("D19", "MISO", "MISO")],
        right=[("D26", "BCK", "BCK"), ("D25", "LRCK", "LRCK"),
               ("D22", "DIN", "DIN")],
        bottom=[("D27", "", "ROUT"), ("RX2 (16)", "", "RX2"), ("TX2 (17)", "", "TX2")],
        w=3.6, edgepad=0.8, side_spacing={"B": 2.2})
    d += esp.right().anchor("center").at((0, 0)).label(
        "ESP32 WROOM-32 DevKit V1 — підписи як на платі", "top", fontsize=10)
    # USB-C плати навмисно НЕ є частиною бойової схеми: у роботі він не
    # підключений, живлення йде на VIN. Але без цього підпису людина з
    # паяльником питає «а чому роз'єму нема на схемі» (Іван, 02.08).
    d += elm.Label().at((esp.absanchors["center"][0], esp.absanchors["center"][1] + 4.3)).label(
        "USB-C збоку плати — тільки прошивка і консоль.\n"
        "У роботі не підключений: живлення приходить на VIN.\n"
        "Одночасно USB і VIN не тримати — щось одне.", fontsize=8)

    power_in(d, esp, "VIN", "GND", "5 В")

    # ---------------- microSD (left, SPI) ----------------
    sd = ic(
        right=[("CS", "", "CS"), ("SCK", "", "SCK"),
               ("MOSI", "", "MOSI"), ("MISO", "", "MISO")],
        left=[("GND", "", "GND"), ("VCC", "", "VCC")],
        w=2.6)
    d += sd.right().anchor("CS").at((-7.5, esp.absanchors["CS"][1])).label(
        "microSD SPI\nSanDisk 32GB, MP3", "top", fontsize=10)
    power_in(d, sd, "VCC", "GND", "5 В")  # на модулі свій LDO і рівні
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
    power_in(d, dac, "VIN", "GND", "5 В")

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
    # 5 В і земля розводяться в РІЗНІ боки: коли значок живлення і значок землі
    # стоять поруч, вони читаються як деталь між VCC і GND (Іван, 02.08 — «діод?»)
    rv = elm.Line().at(radar.VCC).left().length(0.7)
    d += rv
    d += elm.Vdd().at(rv.end).label("5 В", fontsize=9)
    rg = elm.Line().at(radar.GND).left().length(0.7)
    d += rg
    d += elm.Line().at(rg.end).down().length(1.0)
    d += elm.Ground()

    # ---------------- TPA3116D2 mono amp, single MA-3013 ----------------
    # Підписи — як на клемниках плати HiLetgo: «IN + −», «VCC + −», «+ OUT −»,
    # плюс підстроєчник «VOL». Ніяких INP/INM, яких на платі нема.
    amp = ic(
        left=[("IN −", "", "INM"), ("IN +", "", "INP"), ("VCC +", "", "VCC")],
        right=[("VCC −", "", "PGND"), ("OUT −", "", "OUTM"), ("OUT +", "", "OUTP")],
        w=3.2, size=(4.4, 2.6))
    d += amp.right().anchor("INM").at((13.5, dac.absanchors["AGND"][1])).label(
        "TPA3116D2 Mono (підписи як на платі)\nрадіатор назовні · VOL = стеля гучності", "top", fontsize=10)
    # Дві сигнальні лінії з ЦАПа — це ОДИН екранований кабель ~30 см:
    # центральна жила несе звук, обплетення-екран є зворотним проводом.
    # Підписи ставимо ПІД лініями, щоб вони не читались як частина живлення.
    d += elm.Line().at(dac.AGND).to(amp.INM).label(
        "екран кабелю", "bottom", fontsize=8, ofst=0.12)
    d += elm.Line().at(dac.L).to(amp.INP).label(
        "жила кабелю — звук", "bottom", fontsize=8, ofst=0.12)
    d += elm.Vdd().at(amp.VCC).left().label("12 В — свій провід", fontsize=8)
    d += elm.Label().at(((dac.absanchors["L"][0] + amp.absanchors["INP"][0]) / 2 + 1.0,
                         dac.absanchors["AGND"][1] - 0.95)).label(
        "обидві лінії — це ОДИН екранований кабель ~30 см (відрізок аукс-шнура)",
        fontsize=8)
    # земля мінуса живлення веде праворуч і ВНИЗ — щоб не лізти на підпис динаміка
    gline = elm.Line().at(amp.PGND).right().length(0.8)
    d += gline
    d += elm.Line().at(gline.end).down().length(1.1)
    d += elm.Ground()

    # one speaker; second MA-3013 of the pair is kept as a ready spare
    spk = elm.Speaker().right().at(
        (19.0, amp.absanchors["OUTP"][1])).anchor("in1")
    d += spk
    d += elm.Line().at(amp.OUTP).to(spk.in1)
    d += elm.Wire("-|").at(amp.OUTM).to(spk.in2)
    d += elm.Label().at((21.6, amp.absanchors["OUTP"][1] - 1.2)).label(
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
    # вихід 5 В ведемо ВНИЗ і вже там ставимо значок шини: праворуч упритул
    # стоїть радар, і два значки зливались в один незрозумілий елемент
    # без значка живлення: поруч радар і земля, три символи зливались.
    # Просто підписана лінія — куди йде вихід понижайки.
    d += elm.Line().right().at(buck.V5).length(1.3).label(
        "→ шина 5 В", "bottom", fontsize=9)
    d += elm.Ground().at(buck.GNDO).right()

    d += elm.Label().at((6.0, y0 - 0.5)).label(
        "Земля: зіркою в одній точці біля АКБ.\n"
        "3V3 — з стабілізатора плати ESP32 (пін 3V3).\n"
        "AGND ЦАП → амп окремим проводом (не через силову землю).\n"
        "LD2410C — за вікном у броні БЕЗ металу (ABS/акрил/склотканина).", fontsize=8)

d.save(OUT + ".png", dpi=220)
print("wrote schematic.svg + schematic.png")
