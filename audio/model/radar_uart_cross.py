#!/usr/bin/env python3
"""Чому TX і RX ідуть навхрест — одна картинка замість абзацу.

Іван 18.08.2026: «не зрозумів нічого про підключення». Пояснення словами не зайшло,
тому те саме малюнком: TX — це рот, RX — це вухо. Рот одного йде у вухо іншого.
Рот у рот — обидва говорять, ніхто не чує.

Практичний наслідок, який і збиває з пантелику: та сама жила на двох кінцях сидить
на контактах із РІЗНИМИ підписами. Помаранчева — на «TX» біля радара і на «RX2» біля
плати. Це не помилка, це і є правильно.

  radar_uart_cross.py            зібрати SVG
  radar_uart_cross.py --demo     самоперевірка без запису
"""
import argparse
import sys
from pathlib import Path

OUT = Path(__file__).with_suffix(".svg")

INK, INK2, SURFACE = "#0b0b0b", "#52514e", "#fcfcfb"
WARN, OK = "#c2410c", "#1baf7a"
BOARD, BOARD_EDGE = "#eef3f8", "#c2d2e2"
ORANGE, GREEN = "#eb6834", "#1baf7a"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build() -> str:
    W, H = 1180, 560
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'width="{W}" height="{H}">',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>',
         '<style>text{font-family:-apple-system,Segoe UI,Roboto,sans-serif}'
         '.h{font-size:23px;font-weight:700}.s{font-size:14px}.t{font-size:15px}'
         '.p{font-size:16px;font-weight:700}.m{font-size:13px;fill:#52514e}'
         '.k{font-size:15px;font-weight:700}</style>']
    a = p.append

    a(f'<text class="h" x="30" y="44" fill="{INK}">Чому помаранчева і зелена йдуть '
      f'навхрест</text>')
    a(f'<text class="s" x="30" y="72" fill="{INK2}">TX — це рот, він говорить. '
      f'RX — це вухо, воно слухає. Рот одного йде у вухо іншого.</text>')

    # дві плати
    a(f'<rect x="30" y="104" width="330" height="232" rx="12" fill="{BOARD}" '
      f'stroke="{BOARD_EDGE}" stroke-width="2"/>')
    a(f'<text class="p" x="52" y="136" fill="{INK}">Радар LD2410C</text>')
    a(f'<rect x="820" y="104" width="330" height="232" rx="12" fill="{BOARD}" '
      f'stroke="{BOARD_EDGE}" stroke-width="2"/>')
    a(f'<text class="p" x="842" y="136" fill="{INK}">ESP32 у коробці</text>')

    y1, y2 = 200, 288
    # контакти радара
    for y, name, role in ((y1, "TX", "рот радара"), (y2, "RX", "вухо радара")):
        a(f'<rect x="300" y="{y-16}" width="30" height="30" rx="4" fill="#111"/>')
        a(f'<text class="k" x="286" y="{y+6}" fill="{INK}" text-anchor="end">{name}</text>')
        a(f'<text class="m" x="286" y="{y+26}" text-anchor="end">{role}</text>')
    # контакти плати
    for y, name, role in ((y1, "TX2 · GPIO17", "рот плати"), (y2, "RX2 · GPIO16", "вухо плати")):
        a(f'<rect x="850" y="{y-16}" width="30" height="30" rx="4" fill="#111"/>')
        a(f'<text class="k" x="894" y="{y+6}" fill="{INK}">{name}</text>')
        a(f'<text class="m" x="894" y="{y+26}">{role}</text>')

    # помаранчева: TX радара (y1) → RX2 плати (y2)
    a(f'<path d="M330,{y1} C520,{y1} 660,{y2} 850,{y2}" fill="none" '
      f'stroke="{ORANGE}" stroke-width="8"/>')
    # зелена: RX радара (y2) → TX2 плати (y1)
    a(f'<path d="M330,{y2} C520,{y2} 660,{y1} 850,{y1}" fill="none" '
      f'stroke="{GREEN}" stroke-width="8"/>')

    a(f'<text class="t" x="590" y="{y1-34}" fill="{ORANGE}" text-anchor="middle" '
      f'font-weight="700">помаранчева</text>')
    a(f'<text class="m" x="590" y="{y1-14}" text-anchor="middle">радар говорить — '
      f'плата слухає</text>')
    a(f'<text class="t" x="590" y="{y2+54}" fill="{GREEN}" text-anchor="middle" '
      f'font-weight="700">зелена</text>')
    a(f'<text class="m" x="590" y="{y2+74}" text-anchor="middle">плата говорить — '
      f'радар слухає</text>')

    yb = 396
    a(f'<text class="t" x="30" y="{yb}" fill="{WARN}" font-weight="700">'
      f'Та сама жила на двох кінцях сидить на контактах із РІЗНИМИ підписами — '
      f'і це правильно.</text>')
    a(f'<text class="s" x="30" y="{yb+28}" fill="{INK2}">'
      f'Помаранчева: біля радара на контакті «TX», у коробці на контакті «RX2».</text>')
    a(f'<text class="s" x="30" y="{yb+52}" fill="{INK2}">'
      f'Зелена: біля радара на контакті «RX», у коробці на контакті «TX2».</text>')
    a(f'<text class="s" x="30" y="{yb+84}" fill="{INK2}">'
      f'Якщо з’єднати однойменно (TX з TX) — нічого не згорить, але обидва говорять '
      f'і ніхто не слухає: по UART буде тиша.</text>')
    a(f'<text class="s" x="30" y="{yb+108}" fill="{OK}" font-weight="700">'
      f'Решта три жили — БЕЗ жодного перехрещення: синя VCC у +5 В, коричнева OUT у '
      f'GPIO27, усі білі в землю.</text>')
    a('</svg>')
    return "\n".join(p)


def demo() -> int:
    s = build()
    assert s.startswith("<svg") and s.rstrip().endswith("</svg>")
    for t in ("TX2 · GPIO17", "RX2 · GPIO16", "помаранчева", "зелена", "рот", "вухо"):
        assert t in s, t
    # помаранчева мусить іти згори вниз, зелена — знизу вгору
    assert "M330,200 C520,200 660,288 850,288" in s, "помаранчева: TX радара → RX2 плати"
    assert "M330,288 C520,288 660,200 850,200" in s, "зелена: RX радара → TX2 плати"
    assert "БЕЗ жодного перехрещення" in s, "решту жил не перехрещуємо — має бути сказано"
    print(f"demo ok — перехрещення намальоване в обидва боки, {len(s)} байт")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--demo", action="store_true")
    if ap.parse_args().demo:
        sys.exit(demo())
    OUT.write_text(build())
    print(OUT)
