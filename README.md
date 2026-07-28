# Hero Armor — інженерний хаб (Burning Man 2026)

Меморіальна інсталяція памʼяті Захара Захарова — https://hero-armor.com/
Аудіо-вузол: вартовий промовляє голосом Захара. LD2410C радар → ESP32 → PCM5102A → TPA3116D2 Mono → MA-3013.
Світловий вузол: шина 12В, три групи (прожектори / декор / аварійна) — 1416 Wh за ніч.
Живлення: одна станція EcoFlow на весь проєкт + самозбірний сонячний масив; станція змінна.

## Файлова база даних → дашборд

Всі дані проєкту живуть у `data/` — правиш JSON, перезбираєш, публікуєш:

| Файл | Що в ньому |
|---|---|
| `audio/data/params.json` | константи аудіо: електрика, тепло, динаміки, EcoFlow, гучність |
| `audio/data/cases.json` | кейси плайї для аудіо (модель, пресети лаби, таблиця) |
| `lights/data/params.json` | константи світла: світильники, групи живлення, кабелі, АКБ, сонце |
| `lights/data/cases.json` | сценарії ночі (пік / штатно / економ / буря / аварія) |
| `solar/data/params.json` | константи живлення: станції EcoFlow, масив, поправки плайї |
| `solar/data/cases.json` | сценарії генерації і підміни станції |
| `data/bom.json` | BOM зі статусами (`have`/`add`/`tbd`) |
| `data/decisions.json` | журнал рішень (заголовок + «чому»; `open: true` — відкрите питання) |

## Структура

Публічний сайт проєкту: https://hero-armor.com/ (окремий хостинг).
Інженерний хаб (цей репозиторій): https://hero-armor.github.io/

```
data/        спільна база: components, bom, tasks, orders, decisions, addresses
audio/       модель + схема + params/cases аудіо-вузла
lights/      модель + схема + params/cases світлового вузла (чистий споживач)
solar/       живлення: станція + масив; модель тягне споживання з lights і audio
armor/       так само, коли зʼявиться контент
site/        збірник сайту + шаблони; site/assets/hero.png — арт (codex)
docs/        генерований сайт (gitignored; збирає CI)
```

## Збірка

```bash
cd audio/model  && python3 audio_node_model.py    # консольна таблиця кейсів аудіо
cd lights/model && python3 lights_node_model.py   # споживання по групах + просадка в кабелях
cd solar/model  && python3 power_node_model.py    # генерація, запас ходу, момент підміни
cd audio/model  && python3 schematic.py           # схема → schematic.svg/png
cd lights/model && python3 schematic.py           # те саме для світла (треба schemdraw)
cd solar/model  && python3 schematic.py           # схема живлення
cd site && python3 build.py --docs                # → dashboard/ + docs/
```

Моделі — на стандартній бібліотеці (CI збирає сайт без залежностей). `schemdraw` потрібен
тільки щоб перегенерувати схеми; самі `.svg`/`.png` лежать у репо.

`site/build.py` бере числа ТІЛЬКИ з моделей, решту — з `data/*.json`. Вузли розділені за
принципом «споживачі не знають про джерело»: `lights` і `audio` рахують лише власне
споживання, а `solar` імпортує його з них і рахує генерацію, запас і підміну станції.
Тому цифри не можуть розійтися: змінив режим світла — баланс живлення переїхав сам.
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
