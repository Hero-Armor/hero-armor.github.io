# Hero Armor — інженерний хаб (Burning Man 2026)

Меморіальна інсталяція памʼяті Захара Захарова — https://hero-armor.com/
Аудіо-вузол: вартовий промовляє голосом Захара. LD2410C радар → ESP32 → PCM5102A → TPA3116D2 Mono → MA-3013.

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
data/        спільна база: components, bom, tasks, orders, decisions, addresses, project
audio/       модель + схема + params/cases аудіо-вузла
solar/ lights/ armor/   так само, коли зʼявиться контент
site/        збірник сайту + шаблони; site/assets/hero.png — арт (codex)
knowledge/   OKF-бандл (Open Knowledge Format v0.2) — ГЕНЕРУЄТЬСЯ з data/, не правити
docs/        генерований сайт (gitignored; збирає CI)
```

## База знань — Open Knowledge Format

`knowledge/` — [OKF v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf)
бандл: один markdown-концепт на файл (компонент, рішення, задача, позиція BOM,
замовлення), YAML frontmatter, крос-лінки = граф. Його генерує `build.py` з
`data/*.json` — читати можна будь-чим (GitHub, Obsidian, будь-який агент),
правити треба JSON. Рішення несуть `verified: human:…`, розраховані цифри
посилаються на санкціоновану модель (`type: Attested Computation`).

## Збірка

```bash
cd audio/model && python3 audio_node_model.py   # консольна таблиця кейсів
cd audio/model && python3 schematic.py          # схема → schematic.svg/png
cd site && python3 build.py --docs              # → dashboard/ + docs/
```

`site/build.py` бере числа ТІЛЬКИ з моделі (яка читає `audio/data/`), решту — з `data/*.json`.
Жодних чисел руками в HTML.

## Компоненти: життєвий цикл

Реєстр — `data/components.json`; статуси `concept → in-design → design-ready → build`.

1. **Реєстрація**: картка в `components.json` (`key`, `label`, `emoji`, `status`,
   `summary`, `page: "<key>.html"`) → сторінка компонента генерується автоматично
   (`component.tmpl.html`), зʼявляється в навігації і на дашборді.
2. **Дані**: будь-який запис у спільних `data/*.json` з `"component": "<key>"`
   сам потрапляє на сторінку компонента, дашборд і в `knowledge/`.
   Креслення — `site/assets/*.jpg` + `figures` у картці.
3. **Інженерія** (як audio): `<key>/data/params.json` (+`cases.json`) +
   `<key>/model/*.py` — числа рахує тільки модель.
4. **Власний дашборд** (як `audio.html` + `lab.html`): свій шаблон
   `site/templates/<key>.tmpl.html` + секція в `build.py`; симулятор — окремою
   сторінкою; артефакт-дзеркало на claude.ai; лінк у `links` картки.

Повний плейбук — [knowledge/playbooks/](knowledge/playbooks/index.md).

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
