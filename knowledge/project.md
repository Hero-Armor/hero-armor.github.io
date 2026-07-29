---
type: "Project"
title: "Hero Armor"
description: "Меморіальна інсталяція для Burning Man 2026 памʼяті Захара Захарова — воїн-захисник, що промовляє його голосом."
resource: "https://hero-armor.com/"
tags: ["project"]
generated: { by: "process:site-build" }
---

Меморіальна інсталяція памʼяті Захара Захарова — 3D-художника, який загинув,
захищаючи Україну (2022). Історія — на [hero-armor.com](https://hero-armor.com/)
(меморіальний сайт, окремий хостинг). Вартовий промовляє голосом Захара
(ElevenLabs-клон), коли людина підходить на 2.5–3 м.

# Складові

* [Системи](/systems/index.md) — аудіо, сонце/живлення, світло, броня
* [Рішення](/decisions/index.md) — інженерний лог рішень з «чому»
* [Задачі](/tasks/index.md) — дошка по системих
* [Закупівля](/bom/index.md) — BOM з лінками й статусами
* [Замовлення](/orders/index.md) — що їде і куди
* [Модель](/model/index.md) — розраховані цифри аудіо-вузла
* [Подія](/event.md) — Burning Man 2026

# Джерела правди

Бандл генерується з файлової бази `data/*.json` командою
`cd site && python3 build.py` — правити треба JSON, не ці файли.
Інженерний хаб: [hero-armor.github.io](https://hero-armor.github.io/) · [репозиторій](https://github.com/Hero-Armor/hero-armor.github.io).
