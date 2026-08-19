#!/usr/bin/env python3
"""Схема пайки: радар LD2410C на екранованій витій парі Cat6 — фізичний вигляд.

Питання Івана 18.08.2026: «намалюй красивіше, щоб було видно, куди який дріт і кого
з ким зʼєднати, і з якого боку земля». Тому це не абстрактні лінії, а вигляд «як у
руках»: ліворуч клеми в коробці, праворуч плата радара з гребінкою і її підписами,
між ними кабель із чотирма реально перекрученими парами, фольгою і дренажною жилою.

Правило пари: КОЛІР — сигнал, БІЛА зі смужкою того ж кольору — його земля. Кожен
сигнал іде скручений зі своїм зворотним провідником, а не з чужим сигналом.

Екран — з ОДНОГО боку, з боку коробки. Корпус у нас пластиковий (DEC-085), металевого
«корпусу» нема взагалі, тому дренажна жила йде на землю схеми. З двох боків садити не
можна: вийде земляна петля і та сама наводка, від якої ми тікаємо.

Числа не з голови:
  · 23 AWG ≈ 0.067 Ом/м; траса 1 м → 0.067 Ом туди, 0.017 Ом назад (4 землі паралельно);
  · LD2410C бере ~80 мА → просадка 7 мВ;
  · ємність Cat6 ≈ 52 пФ/м → фронт одиниці нс проти 3.9 мкс бітового часу на 256000 бод,
    тобто на 1 м швидкість міняти не треба (DEC-156).

  radar_cable_wiring.py            зібрати SVG
  radar_cable_wiring.py --demo     самоперевірка без запису
"""
import argparse
import math
import sys
from pathlib import Path

OUT = Path(__file__).with_suffix(".svg")

AWG23_OHM_M = 0.067
RUN_M = 1.0
I_RADAR_A = 0.08
CAT6_PF_M = 52.0
BAUD = 256000

INK, INK2, SURFACE, GRID = "#0b0b0b", "#52514e", "#fcfcfb", "#e8e7e3"
WARN, SHIELD = "#c2410c", "#8a8a85"
BOARD, BOARD_EDGE = "#eef3f8", "#c2d2e2"

# (колір, назва пари, сигнал, клема в коробці, підпис на платі радара)
LINES = [
    ("#2a78d6", "синя",        "+5 В",       "понижайка 12→5 В, вихід +5 В", "5V"),
    ("#eb6834", "помаранчева", "TX радара",  "ESP32 · GPIO16, підпис RX2",   "TX"),
    ("#1baf7a", "зелена",      "RX радара",  "ESP32 · GPIO17, підпис TX2",   "RX"),
    ("#8b5a2b", "коричнева",   "OUT",        "ESP32 · GPIO27, підпис D27",   "OUT"),
]

X_L, X_R = 372, 946          # де кабель починається і закінчується
Y0, STEP = 214, 118


def drop_v() -> float:
    """Просадка: один провідник туди, чотири землі паралельно назад."""
    return I_RADAR_A * (AWG23_OHM_M * RUN_M + AWG23_OHM_M * RUN_M / 4)


def edge_ns() -> float:
    """Фронт від ємності лінії при вихідному опорі 50 Ом, у наносекундах."""
    return 50 * CAT6_PF_M * RUN_M * 1e-12 * 1e9


def bit_us() -> float:
    return 1e6 / BAUD


def twist(y: float, phase: float) -> str:
    """Одна жила перекрученої пари — синусоїда від X_L до X_R."""
    pts = []
    x = X_L
    while x <= X_R:
        pts.append(f"{x:.0f},{y + 9 * math.sin((x - X_L) / 17.0 + phase):.1f}")
        x += 5
    return "M" + " L".join(pts)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build() -> str:
    W, H = 1400, 900
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'width="{W}" height="{H}">',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>',
         '<style>text{font-family:-apple-system,Segoe UI,Roboto,sans-serif}'
         '.h{font-size:24px;font-weight:700}.s{font-size:14px}.t{font-size:14px}'
         '.p{font-size:15px;font-weight:700}.m{font-size:12px;fill:#52514e}'
         '.k{font-size:13px;font-weight:700}</style>']
    a = p.append

    a(f'<text class="h" x="30" y="44" fill="{INK}">Радар LD2410C — що з чим зʼєднати</text>')
    a(f'<text class="s" x="30" y="72" fill="{INK2}">Екранована вита пара Cat6, '
      f'{RUN_M:.0f} м. Правило пари: КОЛІР — сигнал, БІЛА зі смужкою того ж кольору — '
      f'земля саме цього сигналу.</text>')
    a(f'<text class="s" x="30" y="94" fill="{INK2}">Кожен сигнал скручений зі своєю '
      f'землею, а не з чужим сигналом — тільки так вита пара працює.</text>')

    box_h = STEP * 4 + 18
    # ── коробка ліворуч ────────────────────────────────────────────────
    a(f'<rect x="30" y="130" width="342" height="{box_h}" rx="12" '
      f'fill="{BOARD}" stroke="{BOARD_EDGE}" stroke-width="2"/>')
    a(f'<text class="p" x="50" y="162" fill="{INK}">Коробка в подіумі</text>')
    a(f'<text class="m" x="50" y="182">ESP32 + ЦАП + понижайка · корпус ПЛАСТИКОВИЙ</text>')

    # ── плата радара праворуч ──────────────────────────────────────────
    a(f'<rect x="946" y="130" width="300" height="{box_h}" rx="12" '
      f'fill="{BOARD}" stroke="{BOARD_EDGE}" stroke-width="2"/>')
    a(f'<text class="p" x="1010" y="162" fill="{INK}">Плата LD2410C</text>')
    a(f'<text class="m" x="1010" y="182">підписи читати З ПЛАТИ,</text>')
    a(f'<text class="m" x="1010" y="198">кольори хвоста не стандарт</text>')

    for i, (col, colname, sig, left, pinname) in enumerate(LINES):
        y = Y0 + i * STEP

        # земля пари: біла жила зі смужкою кольору
        a(f'<path d="{twist(y+30, math.pi)}" fill="none" stroke="#ffffff" stroke-width="7"/>')
        a(f'<path d="{twist(y+30, math.pi)}" fill="none" stroke="{col}" '
          f'stroke-width="7" stroke-dasharray="5 13"/>')
        # сигнал: суцільний колір
        a(f'<path d="{twist(y, 0)}" fill="none" stroke="{col}" stroke-width="7"/>')

        # клеми в коробці
        a(f'<circle cx="360" cy="{y}" r="7" fill="{col}" stroke="#fff" stroke-width="2"/>')
        a(f'<circle cx="360" cy="{y+30}" r="7" fill="#9ca3af" stroke="#fff" stroke-width="2"/>')
        a(f'<text class="t" x="344" y="{y+5}" fill="{INK}" text-anchor="end">{esc(left)}</text>')
        a(f'<text class="m" x="344" y="{y+34}" text-anchor="end">GND (спільна шина)</text>')

        # гребінка на платі радара
        a(f'<rect x="952" y="{y-11}" width="26" height="22" rx="3" fill="#111"/>')
        a(f'<rect x="952" y="{y+19}" width="26" height="22" rx="3" fill="#111"/>')
        a(f'<text class="k" x="990" y="{y+5}" fill="{INK}">{esc(pinname)}</text>')
        a(f'<text class="m" x="990" y="{y+34}">GND</text>')
        a(f'<text class="t" x="{(X_L+X_R)//2}" y="{y-26}" fill="{INK}" '
          f'text-anchor="middle">{esc(colname)} — {esc(sig)}</text>')

    # ── екран і дренажна жила ──────────────────────────────────────────
    ys = 130 + box_h + 46
    a(f'<path d="{twist(ys, 0.6)}" fill="none" stroke="{SHIELD}" stroke-width="6" '
      f'stroke-dasharray="2 5"/>')
    a(f'<line x1="360" y1="{ys}" x2="{X_L}" y2="{ys}" stroke="{SHIELD}" stroke-width="6"/>')
    a(f'<circle cx="360" cy="{ys}" r="7" fill="{SHIELD}" stroke="#fff" stroke-width="2"/>')
    a(f'<text class="t" x="344" y="{ys+5}" fill="{WARN}" text-anchor="end" '
      f'font-weight="700">екран — СЮДИ, на GND</text>')
    a(f'<text class="t" x="{(X_L+X_R)//2}" y="{ys-24}" fill="{INK2}" text-anchor="middle">'
      f'фольга + дренажна жила</text>')
    # обрив з боку радара
    a(f'<line x1="{X_R-26}" y1="{ys-16}" x2="{X_R+4}" y2="{ys+16}" '
      f'stroke="{WARN}" stroke-width="5"/>')
    a(f'<line x1="{X_R-26}" y1="{ys+16}" x2="{X_R+4}" y2="{ys-16}" '
      f'stroke="{WARN}" stroke-width="5"/>')
    a(f'<text class="t" x="{X_R+20}" y="{ys+1}" fill="{WARN}" font-weight="700">'
      f'тут НЕ паяти</text>')
    a(f'<text class="m" x="{X_R+20}" y="{ys+20}">відкусити + термоусадка</text>')

    # ── нотатки ────────────────────────────────────────────────────────
    yn = 130 + box_h + 118
    a(f'<line x1="30" y1="{yn-28}" x2="{W-30}" y2="{yn-28}" stroke="{GRID}" stroke-width="2"/>')
    bold = ' font-weight="700"'
    notes = [
        (WARN, bold, "Земля екрана — тільки з боку коробки. З двох кінців НЕ можна."),
        (INK2, "", "Корпус у нас пластиковий, металевого корпусу нема — дренажна жила "
                   "йде на спільну землю схеми в коробці."),
        (INK2, "", "Земля з двох кінців дає петлю, і екран починає ловити наводку "
                   "замість того, щоб її знімати."),
        (WARN, bold, "TX радара → RX плати, RX радара → TX плати. Навхрест, не однойменно."),
        (INK2, "", f"Усі чотири білі жили зводяться в одну землю на обох кінцях. "
                   f"Просадка на {RUN_M:.0f} м при {I_RADAR_A*1000:.0f} мА — "
                   f"{drop_v()*1000:.0f} мВ."),
        (INK2, "", f"Швидкість {BAUD} бод лишаємо: фронт від ємності {edge_ns():.1f} нс "
                   f"проти {bit_us():.1f} мкс бітового часу."),
    ]
    for i, (colr, weight, txt) in enumerate(notes):
        a(f'<text class="s" x="30" y="{yn + i*26}" fill="{colr}"{weight}>{esc(txt)}</text>')
    a('</svg>')
    return "\n".join(p)


def demo() -> int:
    s = build()
    assert s.startswith("<svg") and s.rstrip().endswith("</svg>")
    assert len(LINES) == 4, "чотири пари Cat6 — чотири сигнали"
    assert {l[2] for l in LINES} == {"+5 В", "TX радара", "RX радара", "OUT"}
    assert 0.002 < drop_v() < 0.05, drop_v()
    assert edge_ns() < bit_us() * 100, "фронт мусить бути на порядки менший за біт"
    for _, name, _, _, pin in LINES:
        assert name in s and f'>{pin}<' in s, name
    assert "навхрест" in s.lower(), "перехрещення TX/RX має бути на схемі"
    assert "тільки з боку коробки" in s, "правило екрана має бути на схемі"
    assert "тут НЕ паяти" in s, "обрив екрана з боку радара має бути показаний"
    assert s.count("<path") >= len(LINES) * 3, "кожна пара — дві жили, плюс екран"
    print(f"demo ok — 4 пари, просадка {drop_v()*1000:.0f} мВ, "
          f"фронт {edge_ns():.1f} нс проти {bit_us():.1f} мкс, {len(s)} байт")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--demo", action="store_true")
    if ap.parse_args().demo:
        sys.exit(demo())
    OUT.write_text(build())
    print(f"{OUT} — {RUN_M:.0f} м, просадка {drop_v()*1000:.0f} мВ")
