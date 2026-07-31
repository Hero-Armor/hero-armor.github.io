# Hero Armor — правила для Claude Code

Burning Man 2026: меморіальна інсталяція памʼяті Захара Захарова (hero-armor.com); вартовий промовляє його голосом. Саб-проєкти: **audio** (готовий дизайн),
**solar** = ЖИВЛЕННЯ (одна станція EcoFlow на все + самозбірний масив, станція змінна),
**lights** (шина 12В, три групи), **armor**, **project** (спільне).

## Правило Івана 31.07.2026 — розмова не є місцем зберігання

Усе, що вирішили або заміряли в діалозі, лягає в базу і на сайт У ТОМУ Ж ХОДІ:
цифра → у профільний `*/data/*.json`, рішення → `data/decisions.json`,
наступний крок → `data/tasks.json`, куплене → `bom.json` + `orders.json`,
подія → `data/project.json → log`. Далі `build.py` → `guard.py` →
`i18n.py --offline` → пуш і перевірка, що сторінка жива. Якщо число живе тільки
у відповіді в чаті — крок не закінчений. Деталі — скіл `hero-armor-process`, розділ 0.

## Джерело правди — файлова база `data/`

- `audio/data/params.json` — константи аудіо · `audio/data/cases.json` — кейси плайї
- `lights/data/params.json` — константи світла · `lights/data/cases.json` — сценарії ночі
- `solar/data/params.json` — станції і масив · `solar/data/cases.json` — сценарії генерації
- `data/systems.json` — реєстр систем (картки на індексі)
- `bom.json` — закупівля · `decisions.json` — рішення · `tasks.json` — задачі
- `orders.json` — замовлення · `addresses.json` — логістика LA→SF
- Кожен запис має `system`: `audio | solar | lights | armor | project`

**Перед публікацією:** `python3 site/guard.py` — ловить секрети, витік приватного
в публічне, правку build-продуктів руками і записи без системи.
**Місток «зібране → data»:** `/root/tools/hero_armor_promote.py scan|list|accept` —
знаходить у чатах схоже на рішення і кладе В ЧЕРГУ на підтвердження; авто нічого
не публікується.

**НІКОЛИ не редагуй HTML дашборда руками.** Правиш `data/*.json` →
`cd site && python3 build.py` → перепублікувати артефакти (ті самі URL).
Числа на сторінках рахують тільки моделі (`audio_node_model.py`, `lights_node_model.py`,
`power_node_model.py`) — руками в HTML жодної цифри. Споживачі (audio, lights) НЕ знають
про джерело живлення; `power_node_model` сам імпортує з них споживання. Не дублюй
автономність і сонце на сторінках споживачів — це система «Живлення».

**Дашборд двомовний.** Українська — джерело, англійська збирається поверх неї:
`python3 site/i18n.py` після `build.py`. Переклад лягає в памʼять
`site/i18n/tm.json` (її ТРЕБА комітити), терміни — у `site/i18n/glossary.json`,
правити переклад руками треба саме там, а не в HTML. На GitHub англійська
збирається з памʼяті (`--offline`), тож після правок текстів прожени переклад
локально і закоміть `tm.json` — інакше нові абзаци лишаться українськими.
Перевірка: `python3 site/i18n_test.py` (з `--browser` — ще й у справжньому
браузері). Підписи на схемах перекладаються самі, бо `svg.fonttype = "none"`
у генераторах лишає їх текстом — не повертай криві.

**`knowledge/` — OKF-бандл (Open Knowledge Format v0.2, Google Cloud spec):**
markdown-концепти з YAML frontmatter, генеруються тим самим `build.py` з
`data/*.json`. НІКОЛИ не правити руками — це build-продукт, комітиться в репо
для агентів/людей. Журнал проєкту — `data/project.json → log`; робочі
процеси — `data/playbooks.json` → `knowledge/playbooks/`.

## Системи: як ведемо

Реєстр — `data/systems.json` (key, label, emoji, status, summary, page,
links, figures). Статуси: `concept → in-design → design-ready → build`.

- **Сторінка системи** (`solar.html`, `lights.html`, `armor.html`)
  генерується автоматично з `system.tmpl.html`: рішення/задачі/BOM/замовлення
  з відповідним `system`-тегом підтягуються самі. Додати систему =
  картка в реєстрі, сторінка зʼявиться після build.
- **Інженерія починається** → створюємо `<key>/data/params.json` (+`cases.json`)
  і `<key>/model/*.py`; числа на сторінках рахує ТІЛЬКИ модель (приклад: audio;
  наступний кандидат — модель бюджету світла).
- **Власний дашборд** (як `audio.html` + `lab.html`) — коли generic-сторінки
  мало: свій шаблон `site/templates/<key>.tmpl.html` + секція в `build.py`,
  інтерактив окремою сторінкою, артефакт-дзеркало на claude.ai (той самий
  file path → той самий URL), лінк у `links` картки і navbar index.
- Повний плейбук: `knowledge/playbooks/` (генерується з `data/playbooks.json`).

## Приватність

**Принцип (Іван, 28.07.2026): приватне = ВСЯ робота, публічне = ТІЛЬКИ вирішене.**
Обговорення, чернетки, невирішене, сирий збір із чатів, голоси, переписка, адреси,
трек-номери — у приватне (репо `Hero-Armor/private` + `data/private/`). У публічний
репо (hero-armor.github.io) йде тільки вже ПРИЙНЯТЕ рішення: оформив у `data/*.json` →
build → сайт. Сумнів «публікувати чи ні» → у приватне.

`data/private/` — gitignored: реальні адреси і трек-номери. НІКОЛИ не комітити,
не вставляти в публічні файли, артефакти чи commit messages. Публічні файли
посилаються на адреси тільки ключами (`la`/`sf`).

## Покупки

Агенти ГОТУЮТЬ замовлення (лінки, кошики, ціни, BOM-статуси) — **купує тільки людина**.
Після покупки: запис в `orders.json` (`ORD-NNN`, дата, `deliver_to` за правилом ship-to
з `addresses.json`), статус BOM → `have`, rebuild.

## Опубліковані сторінки (артефакти)

- Головна (дашборд): https://claude.ai/code/artifact/b5f9223c-1934-413a-9557-be9204d2572b
- Задачі (kanban): https://claude.ai/code/artifact/8bd7dba2-027a-472a-9bb3-3d7a495a9ec1
- Лабораторія: https://claude.ai/code/artifact/822f630a-a99b-4f3b-98cf-bef6e216dced
- Операції: https://claude.ai/code/artifact/5ca1ebd7-1356-4457-8362-812703167859

## Спеціалізовані агенти (.claude/agents/)

- `logistics` — задачі/замовлення/доставки, ops-сторінка
- `procurement` — BOM, ціни, підготовка кошиків (без покупок)

Схеми правляться в `audio/`, `lights/`, `solar/` → `model/schematic.py` (schemdraw),
сигнальний тракт — `audio/model/signal_chain.py`. Публічний сайт проєкту hero-armor.com — ОКРЕМИЙ хостинг, не чіпати; хаб — hero-armor.github.io.
