# Hero Armor — аудіо-вузол (Burning Man)

Робот говорить голосом Захара: LD2410C радар → ESP32 → PCM5102A → TPA3116D2 Mono → MA-3013.

## Файлова база даних → дашборд

Всі дані проєкту живуть у `data/` — правиш JSON, перезбираєш, публікуєш:

| Файл | Що в ньому |
|---|---|
| `data/params.json` | всі константи: електрика, тепло, динаміки, EcoFlow, гучність |
| `data/cases.json` | кейси плайї (джерело для моделі, пресетів лаби і таблиці) |
| `data/bom.json` | BOM зі статусами (`have`/`add`/`tbd`) |
| `data/decisions.json` | журнал рішень (заголовок + «чому») |

## Збірка

```bash
cd model
python3 audio_node_model.py     # консольна таблиця кейсів (перевірка)
python3 schematic.py            # схема → schematic.svg/png
python3 signal_chain.py         # сигнальний тракт → signal_chain.png
python3 build_dashboard.py      # → dashboard/main.html + dashboard/lab.html
```

`build_dashboard.py` бере числа ТІЛЬКИ з моделі (яка читає `data/`), BOM і рішення — з JSON.
Жодних чисел руками в HTML. `--copy-to DIR` — скопіювати у теку публікації артефактів.

## Команда: доступ і приватні дані

Дві репи, доступ = права на GitHub:

- **Публічна** (ця, з Pages): код, моделі, `data/` без адрес — бачать усі.
- **Приватна** `hero-armor/private`: `private.json` з адресами і трек-номерами.

Онбординг тіммейта:

```bash
git clone https://github.com/hero-armor/hero-armor.github.io
cd hero-armor.github.io
git clone https://github.com/hero-armor/private data/private   # якщо є доступ
```

`data/private/` — у .gitignore публічної репи; build підхоплює `private.json`
автоматично (локально видно все). Сайт на Pages збирає CI (`.github/workflows/pages.yml`),
який приватну репу НЕ чекаутить + build обнуляє приватні дані при `CI=1` —
подвійний захист від публікації адрес. Клонував — отримав і агентів:
`CLAUDE.md`, `.claude/agents/`, `.claude/skills/` їдуть з репою.

## Опубліковані сторінки

- Головна (підсумок + рішення + схема + BOM): https://claude.ai/code/artifact/b5f9223c-1934-413a-9557-be9204d2572b
- Лабораторія (симулятор + гучність + сигнальний тракт): https://claude.ai/code/artifact/822f630a-a99b-4f3b-98cf-bef6e216dced

Оновлення артефактів — через Claude Code: перезібрати й перепублікувати ті самі URL.

## Типові правки

- Купили/обрали компонент → `data/bom.json` (status: `have`) → rebuild.
- Нове рішення → `data/decisions.json` → rebuild.
- Виміряли реальний струм/чутливість → `data/params.json` → rebuild (усі числа перерахуються).
- Обрали модель EcoFlow → `power_source.default_wh` + можна лишити тільки її в `models`.
- Переграли моно→стерео → `speaker.config: "stereo"` (+ поправити схему в `model/schematic.py`).
