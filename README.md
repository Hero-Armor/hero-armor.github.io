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

## Структура

Публічний сайт проєкту: https://hero-armor.com/ (окремий хостинг).
Інженерний хаб (цей репозиторій): https://hero-armor.github.io/

```
data/        спільна база: components, bom, tasks, orders, decisions, addresses
audio/       модель + схема + params/cases аудіо-вузла
solar/ lights/ armor/   так само, коли зʼявиться контент
site/        збірник сайту + шаблони; site/assets/hero.png — арт (codex)
docs/        генерований сайт (gitignored; збирає CI)
```

## Збірка

```bash
cd audio/model && python3 audio_node_model.py   # консольна таблиця кейсів
cd audio/model && python3 schematic.py          # схема → schematic.svg/png
cd site && python3 build.py --docs              # → dashboard/ + docs/
```

`site/build.py` бере числа ТІЛЬКИ з моделі (яка читає `audio/data/`), решту — з `data/*.json`.
Жодних чисел руками в HTML. Новий компонент: рядки з `component`-тегом у спільних даних
+ картка в `data/components.json`; своя тека — коли почнеться інженерія.

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
