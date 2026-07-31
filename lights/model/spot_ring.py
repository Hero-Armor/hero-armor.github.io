#!/usr/bin/env python3
"""
Як звʼязати між собою 8 прожекторів заливки — і що це дає по просадці.

Питання просте на вигляд: вісім однакових ламп по колу, один диммер. Але від
того, ЯК підвести живлення, залежить, чи світять вони однаково. Живлення з
одного кінця шлейфом означає, що перший відрізок несе струм усіх восьми, а
останній — одного; уся ця різниця осідає в міді, і дальня лампа тьмяніша за
ближню. Тому рахуємо три схеми на однакових даних:

  chain   шлейф в один бік        — найпростіше, найгірша рівність
  split   годуємо в обидва боки   — той самий кабель, просадка вчетверо менша
  star    променем до кожної      — найрівніше і найдорожче по міді

Струм лампи — заміряний (lights/data/params.json → spot_group.measured), не
паспортний. Просадка рахується туди-назад по тій самій таблиці опору, що і в
кабельній лабораторії. Малює план кільця в spot_ring.svg. Тільки stdlib.
"""

import json
import sys
from math import cos, pi, sin
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lamp_bench as lb

DATA = Path(__file__).resolve().parent.parent / "data"
P = json.loads((DATA / "params.json").read_text())

SG = P["spot_group"]
RING = SG["ring"]
DIM = SG["dimmer"]
OHM = P["wiring"]["awg_ohm_per_m"]
V = P["bus_v"]

QTY = SG["qty"]
# Кабель і диммер рахуємо по НАЙПРОЖЕРЛИВІШІЙ із заміряних ламп: лампу ще не
# обрали, а перекладати проводку після вибору ніхто не буде.
A_LAMP = lb.worst_a_full() or SG["measured"]["a_full"]
# Хорда між сусідніми стійками на колі: саме її треба пройти кабелем,
# бо канал іде по периметру настилу, а не через центр.
SEG_M = 2 * RING["r_post_m"] * sin(pi / QTY)


def group_a(n=QTY):
    return round(n * A_LAMP, 3)


def _drop(segments, awg):
    """Падіння напруги в кінці ланцюга: сума струм × опір по кожній ділянці.

    Опір беремо туди-назад — струм іде плюсом і повертається мінусом, мідь
    гріється на обох."""
    r = OHM[str(awg)]
    return sum(2 * r * length * amps for length, amps in segments)


def scheme(kind):
    """Просадка до найдальшої лампи для однієї схеми підключення."""
    ring_awg, drop_awg = RING["ring_awg"], RING["drop_awg"]
    tail = [(RING["drop_m"], A_LAMP)]  # власний хвіст світильника — завжди один
    if kind == "chain":
        # шлейф в один бік: ділянка k несе всі лампи, що лишились попереду
        segs = [(SEG_M, A_LAMP * (QTY - k)) for k in range(QTY - 1)]
        label = "Шлейф в один бік"
        why = ("Найкоротший кабель і один ввід у кільце. Перший відрізок несе "
               "струм усіх восьми ламп, тому дальня лампа помітно тьмяніша.")
    elif kind == "split":
        # годуємо кільце з середини в обидва боки: у кожній гілці по половині
        half = QTY // 2
        segs = [(SEG_M, A_LAMP * (half - k)) for k in range(half)]
        label = "Годуємо в обидва боки"
        why = ("Той самий кабель і той самий ввід, просто від щита йдемо вліво "
               "і вправо по чотири лампи. Струм у гілці вдвічі менший, а він у "
               "просадку входить лінійно — тому виграш більший за вдвічі.")
    elif kind == "star":
        # коробка в центрі подіуму, від неї своя пара до кожної стійки —
        # довжина променя однакова для всіх, тому й просадка однакова
        label = "Промінь до кожної з центру"
        why = ("Коробка в центрі подіуму, від неї своя пара до кожної стійки. "
               "Просадка найменша і в усіх однакова, але головне не це: у полі "
               "нема жодного проміжного зʼєднання — усі вісім сходяться в одній "
               "коробці. Ціна — вдвічі більше міді й вісім пар у коробці.")
        far = [(RING["r_post_m"], A_LAMP)]
        v = _drop(far + tail, drop_awg)
        return {"kind": kind, "label": label, "why": why,
                "cable_m": QTY * RING["r_post_m"],
                "joints": 0, "worst_v": v, "worst_pct": 100 * v / V}
    else:
        raise ValueError(kind)
    v = _drop(segs, ring_awg) + _drop(tail, drop_awg)
    # шлейф проходить кільце один раз, дві гілки — по половині кожна, але
    # від щита до точки входу теж треба дійти, тому виходить повне коло
    cable = SEG_M * (QTY - 1) if kind == "chain" else SEG_M * QTY
    # Проміжні зʼєднання — це те, що доводиться робити в пилу на плайї
    # і що потім відмовляє першим. У шлейфі відвід на кожній стійці.
    return {"kind": kind, "label": label, "why": why, "cable_m": cable,
            "joints": QTY - 1 if kind == "chain" else QTY,
            "worst_v": v, "worst_pct": 100 * v / V}


def schemes():
    return [scheme(k) for k in ("chain", "split", "star")]


def dimmer():
    """Чи проходить група в диммер — з паспортним запасом, не впритул."""
    a = group_a()
    safe = DIM["a_rating"] * DIM["derate"]
    # нижній край беремо в тієї ж лампи, по якій рахували верхній
    run = max(lb.dimmer_runs(), key=lambda r: r["a_full"], default=None)
    a_min = run["a_min"] if run else SG["measured"]["a_dim_min"]
    return {
        "load_a": a,
        "rating_a": DIM["a_rating"],
        "safe_a": safe,
        "headroom_pct": 100 * (1 - a / safe),
        "ok": a <= safe,
        "lamp": run["name"] if run else SG["measured"]["lamp"],
        "min_a": a_min * QTY,
        "range_x": A_LAMP / a_min,
    }


def fuse():
    """Номінал запобіжника групи: робочий струм × запас, вгору по ряду."""
    need = group_a() * SG["fuse_derate"]
    return next(a for a in P["fusing"]["standard_a"] if a >= need)


def watts():
    return {"full": round(V * group_a(), 1),
            "dim_min": round(V * dimmer()["min_a"], 1)}


# ------------------------------------------------------------------- креслення
def svg():
    """План подіуму: вісім стійок, коробка в центрі, промінь до кожної.

    Малюємо рекомендовану схему — щоб з картинки було видно головне: усі вісім
    пар сходяться в ОДНІЙ коробці, а по колу не йде жодного зʼєднання."""
    W, H, CX, CY = 620, 420, 300, 215
    R = 130
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'font-family="ui-monospace,Menlo,monospace">']
    ink, line, acc, sig = "#24231d", "#c9c6ba", "#b35b1e", "#3d6f96"

    o.append(f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="none" stroke="{line}" '
             f'stroke-width="1.5" stroke-dasharray="5 4"/>')
    o.append(f'<circle cx="{CX}" cy="{CY}" r="34" fill="none" stroke="{line}"/>')
    o.append(f'<text x="{CX}" y="{CY+4}" text-anchor="middle" font-size="10" '
             f'fill="#6b675c">подіум</text>')

    # стійки: нумеруємо від щита проти і за годинниковою — по чотири в гілці
    pts = []
    for k in range(QTY):
        ang = -pi / 2 + 2 * pi * k / QTY
        pts.append((CX + R * cos(ang), CY + R * sin(ang)))

    box = (CX, CY)
    for x, y in pts:
        o.append(f'<line x1="{CX}" y1="{CY}" x2="{x:.1f}" y2="{y:.1f}" '
                 f'stroke="{acc}" stroke-width="2"/>')

    for k, (x, y) in enumerate(pts):
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="#fff" stroke="{ink}" '
                 f'stroke-width="1.6"/>')
        lx, ly = CX + (R + 26) * cos(-pi / 2 + 2 * pi * k / QTY), \
                 CY + (R + 26) * sin(-pi / 2 + 2 * pi * k / QTY)
        o.append(f'<text x="{lx:.1f}" y="{ly+4:.1f}" text-anchor="middle" font-size="10" '
                 f'fill="{ink}">{A_LAMP:.2f}A</text>')

    bx, by = box
    o.append(f'<rect x="{bx-52:.0f}" y="{by-19:.0f}" width="104" height="38" rx="4" '
             f'fill="#fff" stroke="{ink}" stroke-width="1.8"/>')
    o.append(f'<text x="{bx:.0f}" y="{by-4:.0f}" text-anchor="middle" font-size="11" '
             f'fill="{ink}">коробка</text>')
    o.append(f'<text x="{bx:.0f}" y="{by+11:.0f}" text-anchor="middle" font-size="9" '
             f'fill="#6b675c">8 пар + {fuse():.0f}A</text>')

    o.append(f'<line x1="{bx-52:.0f}" y1="{by:.0f}" x2="26" y2="{by:.0f}" '
             f'stroke="{sig}" stroke-width="2.5"/>')
    o.append(f'<text x="26" y="{by-10:.0f}" font-size="10" fill="{sig}">'
             f'магістраль AWG {RING["trunk_awg"]} · ШІМ-диммер</text>')
    o.append(f'<text x="26" y="{by+20:.0f}" font-size="10" fill="#6b675c">'
             f'{group_a():.2f} A на повній</text>')

    st = scheme("star")
    o.append(f'<text x="{CX}" y="26" text-anchor="middle" font-size="12" fill="{ink}">'
             f'Прожектори: своя пара до кожної стійки з однієї коробки</text>')
    o.append(f'<text x="{CX}" y="44" text-anchor="middle" font-size="10" fill="#6b675c">'
             f'промінь {RING["r_post_m"]:.2f} м · кабель AWG {RING["drop_awg"]} · '
             f'просадка {st["worst_pct"]:.1f}% і однакова в усіх · зʼєднань у полі нема</text>')
    o.append("</svg>")
    return "\n".join(o)


def main():
    d = dimmer()
    print(f'група {group_a()} A ({watts()["full"]} Вт), на мінімумі '
          f'{d["min_a"]:.2f} A ({watts()["dim_min"]} Вт), діапазон ×{d["range_x"]:.0f}')
    print(f'диммер {d["rating_a"]:.0f} A, робоча стеля {d["safe_a"]:.1f} A — '
          f'{"проходимо" if d["ok"] else "НЕ проходимо"}, запас {d["headroom_pct"]:.0f}%')
    print(f'запобіжник групи {fuse():.0f} A · відрізок кільця {SEG_M:.2f} м')
    for s in schemes():
        print(f'  {s["label"]:24} просадка {s["worst_v"]:.3f} В '
              f'({s["worst_pct"]:.2f}%) · міді {s["cable_m"]:.1f} м')
    (Path(__file__).resolve().parent / "spot_ring.svg").write_text(svg())
    print("креслення: spot_ring.svg")


if __name__ == "__main__":
    main()
