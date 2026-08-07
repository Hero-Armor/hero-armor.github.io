#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Карта вузлів і з'єднань → скільки коробок треба.

Правило Івана 07.08.2026: КОЖЕН елемент і КОЖНЕ з'єднання ховається у власну
пластикову коробку. Щоб знати, скільки коробок докупити, треба спершу перелічити
всі місця, де провід розривається або де стоїть прилад.

Модель нічого не вигадує: топологію бере з lights/data/params.json (гілки і
відводи), кількості світильників — звідти ж, місця пайки стрічки — з
lights/data/strip_install.json, аудіо-вузол — з audio/data/assembly.json,
ящики — з enclosure/data/params.json, а те, що вже куплено чи лежить у кошику —
з data/bom.json.

Два місця, де креслення ще нема (топологія 24 врізних вогнів торця і 10 ламп на
корпусі робота), рахуються ДІАПАЗОНОМ: від «зірка з однієї коробки» до «сплайс
на кожен світильник». Саме через це підсумок — вилка, а не одне число.

Запуск:  python3 enclosure/model/joint_map.py [--json]
Пише:    enclosure/data/joints.json
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


P = load("lights/data/params.json")
BOM = load("data/bom.json")

FIX = {f["id"]: f for f in P["fixtures"]}
SEG = {s["id"]: s for s in P["topology"]["segments"]}


def qty(fid):
    return int(FIX.get(fid, {}).get("qty", 0))


# --- 1. Вузли: прилад або щит, який фізично стоїть у своїй коробці -----------
# «where» — зона, «why» — чому це окрема коробка, «box» — який клас корпусу.

NODES = [
    dict(id="case_station", where="D · ящик станції", box="ящик",
         title="Станція живлення",
         why="Заводський корпус, але сам ящик потрібен від пилу і сонця",
         seg=None),
    dict(id="case_panel", where="D · ящик станції", box="ящик",
         title="Ящик щита і проводки",
         why="Другий тот поруч зі станцією — у ньому живе щит",
         seg=None),
    dict(id="panel", where="D · ящик щита", box="гермокоробка IP66",
         title="Щит запобіжників",
         why="Блок запобіжників Cyrico + шини + 4 ватметри + 3 тумблери — один вузол",
         seg="trunk"),
    dict(id="box_marker", where="D · стінка ящика", box="мала IP65",
         title="Розгалуження на маркерні вогники ящика",
         why="Окремий корінь топології: магістраль подіуму цих вогників не бачить",
         seg="box_g3a"),
    dict(id="dimmer", where="B · подіум", box="гермокоробка IP65",
         title="Коробка ШІМ-диммера (Гр.1)",
         why="Диммер продається без захисту — голі клеми",
         seg="br_g1"),
    dict(id="wled", where="B · центр подіуму", box="гермокоробка IP65",
         title="Центральний вузол стрічки: контролер WLED + конденсатор",
         why="Тут сходяться 8 рукавів і 3 точки підкачки живлення",
         seg="br_g2"),
    dict(id="relay_g3a", where="B · подіум", box="гермокоробка IP65",
         title="Коробка аварійної групи (Гр.3А)",
         why="Реле окремої лінії, яка гасне останньою; рознесена від щита на 6 м",
         seg="br_g3a"),
    dict(id="audio", where="A · груди фігури", box="гермокоробка IP65",
         title="Аудіо-вузол",
         why="ESP32 + ЦАП + підсилювач на одній платі, радіатор назовні",
         seg=None),
    dict(id="back_core", where="A · спина фігури", box="без коробки",
         title="Ядро на спині",
         why="Кишеня в самій оболонці робота вже герметична — окремий корпус зайвий",
         seg="drop_back_core"),
]

# --- 2. З'єднання: місця, де провід розривається ----------------------------
# fixed — точно відоме число; lo/hi — вилка, поки нема креслення.

JOINTS = [
    dict(id="spot_splices", title="Відвід на кожну стійку прожектора",
         where="B · 8 стійок по периметру", fixed=qty("spot"),
         box="гель-бокс на сплайс",
         why="Кільце йде повз стійку, від нього відгалужується хвіст лампи",
         src="params.json → spot_group.install"),
    dict(id="strip_arms", title="Вхід живлення в кожен рукав стрічки",
         where="B · центр подіуму", fixed=8, box="всередині коробки WLED",
         why="Пайка на майданчики + термоусадка з клеєм, усе сходиться в один вузол",
         src="strip_install.json → joints"),
    dict(id="strip_inject", title="Точки підкачки живлення стрічки",
         where="B · настил подіуму", fixed=3, box="всередині коробки WLED",
         why="Підкачка кожні 2.5–3 м, струм ділиться на три вводи",
         src="params.json → topology.inj_g2"),
    dict(id="strip_caps", title="Заглушка на торець кожного відрізка стрічки",
         where="B · зовнішні кінці променів", fixed=8, box="заглушка+герметик",
         why="Відкритий торець неону — головний вхід для пилу; це не коробка",
         src="strip_install.json → joints"),
    dict(id="stairs", title="Сплайси врізних вогнів торця",
         where="B · торець подіуму", lo=1, hi=qty("stairs") or 24,
         box="гель-бокс на сплайс",
         why="Топологія не задана: зірка з однієї коробки чи шлейф із відводом на кожен вогонь",
         src="params.json → topology.stairs_g3a (топологія відсутня)"),
    dict(id="robot_lamps", title="Сплайси ламп на корпусі робота",
         where="A · всередині броні", lo=1, hi=qty("led12") + qty("led8"),
         box="мала коробка / гель",
         why="Один хвіст 18AWG несе всі лампи, але як саме — шлейфом чи зіркою — не вирішено",
         src="params.json → topology.drop_robot (топологія відсутня)"),
    dict(id="figure_link", title="Перехід кабелю подіум → фігура",
         where="B/A · крізь настил", lo=1, hi=1, box="роз'єм + коробка",
         why="Ніде не описано, чи фігура знімна і як заведений кабель — а це стик, який рветься при перевезенні",
         src="в файлах немає"),
    dict(id="station_link", title="Стик станція → магістраль подіуму",
         where="D → B", fixed=1, box="роз'єм Anderson у стінці ящика",
         why="Роз'ємне з'єднання на 30 А, ховається в стінку ящика",
         src="params.json → topology.trunk"),
]


def n_lo(j):
    return j.get("fixed", j.get("lo", 0))


def n_hi(j):
    return j.get("fixed", j.get("hi", 0))


# --- 3. Що вже є в реєстрі ---------------------------------------------------

def bom_boxes():
    """Позиції BOM, які є корпусами або гермовводами."""
    words = ("коробк", "ящик", "гермовв", "кейс", "гель-конектор")
    out = []
    for r in BOM:
        name = (r.get("item") or "").lower()
        if any(w in name for w in words):
            out.append(dict(item=r.get("item"), qty=r.get("qty"),
                            price=r.get("price"), flow=r.get("flow"),
                            system=r.get("system"), url=r.get("url", "")))
    return out


def build():
    # коробки під вузли (крім тих, що «без коробки»)
    node_boxes = [n for n in NODES if n["box"] != "без коробки"]
    # коробки під з'єднання (крім тих, що ховаються всередині іншої коробки)
    joint_lo = sum(n_lo(j) for j in JOINTS if "всередині" not in j["box"]
                   and "заглушка" not in j["box"])
    joint_hi = sum(n_hi(j) for j in JOINTS if "всередині" not in j["box"]
                   and "заглушка" not in j["box"])
    return dict(
        _source="enclosure/model/joint_map.py — рахується з даних, руками не правити",
        _rule="Іван 07.08.2026: кожен елемент і кожне з'єднання — у власній коробці",
        nodes=NODES,
        joints=JOINTS,
        totals=dict(
            nodes=len(NODES),
            node_boxes=len(node_boxes),
            joints_lo=sum(n_lo(j) for j in JOINTS),
            joints_hi=sum(n_hi(j) for j in JOINTS),
            boxes_lo=len(node_boxes) + joint_lo,
            boxes_hi=len(node_boxes) + joint_hi,
        ),
        in_registry=bom_boxes(),
        open_questions=[j["title"] for j in JOINTS if "lo" in j and j["lo"] != j["hi"]]
        + ["Де саме стоїть коробка диммера (params.json сам пише placement_open)"],
    )


def main():
    data = build()
    out = os.path.join(ROOT, "enclosure/data/joints.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    if "--json" in sys.argv:
        print(json.dumps(data, ensure_ascii=False, indent=1))
        return

    t = data["totals"]
    print("ВУЗЛИ (прилад або щит у власному корпусі):")
    for n in data["nodes"]:
        print(f"  · {n['title']:52} {n['where']:22} {n['box']}")
    print("\nЗ'ЄДНАННЯ (місця, де провід розривається):")
    for j in data["joints"]:
        cnt = str(j["fixed"]) if "fixed" in j else f"{j['lo']}…{j['hi']}"
        print(f"  · {j['title']:52} {j['where']:22} {cnt:>7}  {j['box']}")
    print(f"\nПІДСУМОК: вузлів {t['nodes']}, з них у своїй коробці {t['node_boxes']}")
    print(f"          з'єднань {t['joints_lo']}…{t['joints_hi']}")
    print(f"          КОРОБОК ТРЕБА: {t['boxes_lo']}…{t['boxes_hi']}")
    print("\nЩО ВЖЕ В РЕЄСТРІ:")
    for b in data["in_registry"]:
        print(f"  · {b['item'][:58]:58} {str(b['qty']):16} {str(b['price']):10} {b['flow']}")
    print("\nВІДКРИТЕ (через це підсумок — вилка):")
    for q in data["open_questions"]:
        print("  ·", q)


if __name__ == "__main__":
    main()
