# Hero Armor — правила для Claude Code

Burning Man проєкт: робот, що говорить голосом Захара. Саб-проєкти: **audio** (готовий дизайн),
**solar** (живлення/EcoFlow), **lights**, **armor**, **project** (спільне).

## Джерело правди — файлова база `data/`

- `audio/data/params.json` — константи моделі · `audio/data/cases.json` — кейси плайї
- `data/components.json` — реєстр компонентів (картки на індексі)
- `bom.json` — закупівля · `decisions.json` — рішення · `tasks.json` — задачі
- `orders.json` — замовлення · `addresses.json` — логістика LA→SF
- Кожен запис має `component`: `audio | solar | lights | armor | project`

**НІКОЛИ не редагуй HTML дашборда руками.** Правиш `data/*.json` →
`cd site && python3 build.py` → перепублікувати артефакти (ті самі URL).
Числа на сторінках рахує тільки модель (`model/audio_node_model.py`).

## Приватність

`data/private/` — gitignored: реальні адреси і трек-номери. НІКОЛИ не комітити,
не вставляти в публічні файли, артефакти чи commit messages. Публічні файли
посилаються на адреси тільки ключами (`la`/`sf`).

## Покупки

Агенти ГОТУЮТЬ замовлення (лінки, кошики, ціни, BOM-статуси) — **купує тільки людина**.
Після покупки: запис в `orders.json` (`ORD-NNN`, дата, `deliver_to` за правилом ship-to
з `addresses.json`), статус BOM → `have`, rebuild.

## Опубліковані сторінки (артефакти)

- Головна: https://claude.ai/code/artifact/b5f9223c-1934-413a-9557-be9204d2572b
- Лабораторія: https://claude.ai/code/artifact/822f630a-a99b-4f3b-98cf-bef6e216dced
- Операції: https://claude.ai/code/artifact/5ca1ebd7-1356-4457-8362-812703167859

## Спеціалізовані агенти (.claude/agents/)

- `logistics` — задачі/замовлення/доставки, ops-сторінка
- `procurement` — BOM, ціни, підготовка кошиків (без покупок)

Схема правиться в `audio/model/schematic.py` (schemdraw), сигнальний тракт — `audio/model/signal_chain.py`. Публічний сайт проєкту hero-armor.com — ОКРЕМИЙ хостинг, не чіпати; хаб — hero-armor.github.io.
