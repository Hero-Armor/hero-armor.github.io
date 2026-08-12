#!/usr/bin/env python3
"""Палітра розпису робота: витягти кольори з оригіналу Захара і намалювати схему.

Два режими:
  --measure   перерахувати кольори з `site/assets/palette/reference.jpg` і оновити
              hex/light/shadow у palette.json (щоб цифри не набивались руками)
  (без ключа) намалювати `armor/model/palette.svg` — референс із виносками на зони
              плюс плашки кольорів з кодами

SVG, а не PNG, бо підписи лишаються текстом і перекладаються в англійську версію
хаба (правило: `svg.fonttype = "none"`, див. hub/CLAUDE.md).
Тільки stdlib + PIL (PIL потрібен лише для --measure).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # .../hub
DATA = ROOT / "armor/data/palette.json"
REF = ROOT / "site/assets/palette/reference.jpg"
OUT = ROOT / "armor/model/palette.svg"

# куди дивиться виноска на референсі, у частках ширини/висоти картинки
ANCHORS = {
    "blue":   (0.50, 0.29),
    "amber":  (0.33, 0.38),
    "steel":  (0.32, 0.33),
    "carbon": (0.49, 0.50),
}


def measure():
    """Перерахувати кольори з рендера. Пікселі фігури розбираються за відтінком."""
    import colorsys
    from PIL import Image
    im = Image.open(REF).convert("RGB")
    w, h = im.size
    fig = im.crop((int(w * 0.18), int(h * 0.03), int(w * 0.82), int(h * 0.97)))
    buckets = {"blue": [], "amber": [], "steel": [], "carbon": []}
    for r, g, b in fig.getdata():
        hh, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        deg = hh * 360
        if v < 0.06:
            continue
        if 180 <= deg <= 250 and s > 0.20:
            buckets["blue"].append((r, g, b, v))
        elif 15 <= deg <= 55 and s > 0.28 and v > 0.30:
            buckets["amber"].append((r, g, b, v))
        elif s < 0.12 and v > 0.35:
            buckets["steel"].append((r, g, b, v))
        elif s < 0.18 and 0.10 < v <= 0.28:
            buckets["carbon"].append((r, g, b, v))

    def at(lst, pct):
        lst.sort(key=lambda t: t[3])
        r, g, b, _ = lst[min(int(len(lst) * pct), len(lst) - 1)]
        return "#%02X%02X%02X" % (r, g, b)

    doc = json.loads(DATA.read_text(encoding="utf-8"))
    for z in doc["zones"]:
        lst = buckets.get(z["id"]) or []
        if not lst:
            print(f"  {z['id']}: пікселів не знайшлось, лишаю як було")
            continue
        z["hex"] = at(lst, 0.70)
        z["light"] = at(lst, 0.92)
        z["shadow"] = at(lst, 0.25)
        print(f"  {z['id']:7} {z['hex']}  світло {z['light']}  тінь {z['shadow']}")
    DATA.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"оновлено {DATA.relative_to(ROOT)}")


def _ref_b64():
    """Референс усередину SVG рядком.

    Схема вставляється в сторінку ТЕКСТОМ (див. diagrams_html у site/build.py),
    тому відносний шлях до jpg рахувався б від сторінки, а сторінок дві —
    docs/armor.html і docs/en/armor.html. base64 працює в обох.
    """
    import base64
    return base64.b64encode(REF.read_bytes()).decode()


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def draw():
    doc = json.loads(DATA.read_text(encoding="utf-8"))
    zones = doc["zones"]
    IMG_W, IMG_H = 300, 489            # референс 800x1304 у масштабі
    PAD, ROW = 24, 108
    W = 980
    H = max(IMG_H + PAD * 2, PAD * 2 + 40 + ROW * len(zones))
    x0 = PAD + IMG_W + 46              # ліва межа колонки з плашками

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
         f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif">',
         f'<rect width="{W}" height="{H}" fill="#0f1115"/>',
         f'<image x="{PAD}" y="{PAD}" width="{IMG_W}" height="{IMG_H}" '
         f'xlink:href="data:image/jpeg;base64,{_ref_b64()}"/>']

    for i, z in enumerate(zones):
        y = PAD + 40 + i * ROW
        ax, ay = ANCHORS.get(z["id"], (0.5, 0.5))
        px, py = PAD + ax * IMG_W, PAD + ay * IMG_H
        # виноска від точки на роботі до плашки
        s.append(f'<line x1="{px:.0f}" y1="{py:.0f}" x2="{x0 - 12}" y2="{y + 26}" '
                 f'stroke="{z["hex"]}" stroke-width="1.5" opacity="0.75"/>')
        s.append(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="4" fill="none" '
                 f'stroke="{z["hex"]}" stroke-width="2"/>')
        # три плашки: тінь / основний / світло
        for j, key in enumerate(("shadow", "hex", "light")):
            s.append(f'<rect x="{x0 + j * 52}" y="{y}" width="50" height="50" rx="4" '
                     f'fill="{z[key]}" stroke="#2a2f3a"/>')
        s.append(f'<text x="{x0}" y="{y + 68}" fill="#8b93a7" font-size="10">'
                 f'тінь · основний · світло</text>')
        tx = x0 + 3 * 52 + 18
        s.append(f'<text x="{tx}" y="{y + 16}" fill="#e8ecf3" font-size="14" '
                 f'font-weight="bold">{esc(z["label"])}</text>')
        s.append(f'<text x="{tx}" y="{y + 34}" fill="{z["hex"]}" font-size="15" '
                 f'font-family="monospace">{z["hex"]}</text>')
        s.append(f'<text x="{tx + 86}" y="{y + 34}" fill="#8b93a7" font-size="11">'
                 f'ціль для фарби {z.get("target", z["hex"])}</text>')
        s.append(f'<text x="{tx}" y="{y + 52}" fill="#aab3c5" font-size="11">'
                 f'{esc(z["where"])}</text>')
        s.append(f'<text x="{tx}" y="{y + 68}" fill="#7d879b" font-size="11">'
                 f'{esc(z["finish"])} · {esc(z["share"])}</text>')

    s.append(f'<text x="{PAD}" y="{PAD + 24}" fill="#e8ecf3" font-size="15" '
             f'font-weight="bold">Палітра розпису — зміряна з оригіналу Захара</text>')
    s.append('</svg>')
    OUT.write_text("\n".join(s), encoding="utf-8")
    print(f"намальовано {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    if "--measure" in sys.argv:
        measure()
    draw()
