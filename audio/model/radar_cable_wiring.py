#!/usr/bin/env python3
"""Схема пайки: радар LD2410C на екранованій витій парі Cat6.

Питання Івана 18.08.2026: «яка жила куди паяється». Правило пари просте і його
видно на схемі: КОЛІР — сигнал, БІЛА жила ЗІ СМУЖКОЮ ТОГО Ж КОЛЬОРУ — його земля.
Так кожен сигнал іде скручений зі своїм зворотним провідником, а не з чужим —
саме це й робить виту пару витою парою.

Числа не з голови:
  · 23 AWG ≈ 0.067 Ом/м; траса 3 м → 0.20 Ом туди, 0.05 Ом назад (4 землі паралельно);
  · LD2410C бере ~80 мА → просадка 0.02 В. Живлення можна вести однією жилою.

  radar_cable_wiring.py            зібрати SVG
  radar_cable_wiring.py --demo     самоперевірка без запису
"""
import argparse
import sys
from pathlib import Path

OUT = Path(__file__).with_suffix(".svg")

AWG23_OHM_M = 0.067
RUN_M = 3.0
I_RADAR_A = 0.08

INK, INK2, SURFACE, GRID = "#0b0b0b", "#52514e", "#fcfcfb", "#e8e7e3"
WARN = "#c2410c"

# (колір жили, підпис кольору, сигнал, куди на боці коробки, куди на боці радара)
LINES = [
    ("#2a78d6", "синя",       "+5 В",        "buck 12→5 В, вихід +5 В", "VCC"),
    ("#eb6834", "помаранчева", "TX радара",  "ESP32 GPIO16 (RX2)",      "TX"),
    ("#1baf7a", "зелена",      "RX радара",  "ESP32 GPIO17 (TX2)",      "RX"),
    ("#8b5a2b", "коричнева",   "OUT",        "ESP32 GPIO27 (D27)",      "OUT"),
]


def drop_v() -> float:
    """Просадка на трасі: один провідник туди, чотири землі паралельно назад."""
    return I_RADAR_A * (AWG23_OHM_M * RUN_M + AWG23_OHM_M * RUN_M / 4)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build() -> str:
    W, H = 1180, 720
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>',
         '<style>text{font-family:-apple-system,Segoe UI,Roboto,sans-serif}'
         '.h{font-size:21px;font-weight:700}.s{font-size:13px}.t{font-size:14px}'
         '.m{font-size:12px;fill:#52514e}</style>']
    a = p.append
    a(f'<text class="h" x="28" y="40" fill="{INK}">Радар LD2410C на витій парі Cat6 — '
      f'що куди паяти</text>')
    a(f'<text class="s" x="28" y="64" fill="{INK2}">Правило одне: КОЛІР — сигнал, '
      f'БІЛА зі смужкою того ж кольору — його земля. Кожен сигнал скручений зі своєю '
      f'землею, а не з чужим сигналом.</text>')

    # рамки боків
    a(f'<rect x="28" y="92" width="270" height="430" rx="10" fill="none" '
      f'stroke="{GRID}" stroke-width="2"/>')
    a(f'<text class="t" x="44" y="118" fill="{INK}" font-weight="700">Коробка в подіумі</text>')
    a(f'<text class="m" x="44" y="138">ESP32 + ЦАП + понижайка</text>')
    a(f'<rect x="882" y="92" width="270" height="430" rx="10" fill="none" '
      f'stroke="{GRID}" stroke-width="2"/>')
    a(f'<text class="t" x="898" y="118" fill="{INK}" font-weight="700">Радар у фігурі</text>')
    a(f'<text class="m" x="898" y="138">підписи читати з плати, не з кольору дроту</text>')

    y0 = 176
    for i, (col, colname, sig, left, right) in enumerate(LINES):
        y = y0 + i * 88
        a(f'<line x1="298" y1="{y}" x2="882" y2="{y}" stroke="{col}" stroke-width="5"/>')
        a(f'<line x1="298" y1="{y+22}" x2="882" y2="{y+22}" stroke="{col}" '
          f'stroke-width="5" stroke-dasharray="9 7"/>')
        a(f'<text class="t" x="590" y="{y-8}" fill="{INK}" text-anchor="middle">'
          f'{esc(colname)} — {esc(sig)}</text>')
        a(f'<text class="m" x="590" y="{y+40}" text-anchor="middle">'
          f'біла зі смужкою ({esc(colname)}) — земля цієї пари</text>')
        a(f'<text class="t" x="286" y="{y+5}" fill="{INK}" text-anchor="end">{esc(left)}</text>')
        a(f'<text class="t" x="894" y="{y+5}" fill="{INK}">{esc(right)}</text>')
        a(f'<text class="m" x="286" y="{y+27}" text-anchor="end">GND</text>')
        a(f'<text class="m" x="894" y="{y+27}">GND</text>')

    yw = 566
    a(f'<text class="t" x="28" y="{yw}" fill="{WARN}" font-weight="700">'
      f'Екран — тільки з боку коробки</text>')
    a(f'<text class="s" x="28" y="{yw+22}" fill="{INK2}">'
      f'Дренажну жилу і фольгу паяємо на землю в коробці. З боку радара екран '
      f'відкусити і закрити термоусадкою: земля з двох кінців дає петлю.</text>')
    a(f'<text class="s" x="28" y="{yw+48}" fill="{WARN}" font-weight="700">'
      f'TX радара йде на RX плати, RX радара — на TX плати. Навхрест, не однойменно.</text>')
    a(f'<text class="s" x="28" y="{yw+72}" fill="{INK2}">'
      f'Усі чотири білі жили зводяться разом в одну землю на обох кінцях. '
      f'Просадка на {RUN_M:.0f} м при {I_RADAR_A*1000:.0f} мА — '
      f'{drop_v()*1000:.0f} мВ, живлення однієї жили вистачає з запасом.</text>')
    a('</svg>')
    return "\n".join(p)


def demo() -> int:
    s = build()
    assert s.startswith("<svg") and s.rstrip().endswith("</svg>")
    assert len(LINES) == 4, "чотири пари Cat6 — чотири сигнали"
    sigs = {l[2] for l in LINES}
    assert sigs == {"+5 В", "TX радара", "RX радара", "OUT"}, sigs
    assert 0.01 < drop_v() < 0.05, drop_v()      # десятки мВ, не вольти
    for _, name, _, _, _ in LINES:
        assert name in s, name
    assert "навхрест" in s.lower(), "попередження про перехрещення TX/RX обовʼязкове"
    assert "з боку коробки" in s, "правило екрана обовʼязкове"
    print(f"demo ok — 4 пари, просадка {drop_v()*1000:.0f} мВ, {len(s)} байт SVG")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--demo", action="store_true")
    if ap.parse_args().demo:
        sys.exit(demo())
    OUT.write_text(build())
    print(f"{OUT} — просадка {drop_v()*1000:.0f} мВ на {RUN_M:.0f} м")
