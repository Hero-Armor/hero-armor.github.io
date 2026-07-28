---
type: "Model Snapshot"
title: "Аудіо-вузол — розраховані цифри"
description: "Ключові числа з моделі: споживання, автономність, температура, гучність."
tags: ["audio"]
generated: { by: "process:site-build" }
sources:
  - { id: "params", resource: "https://github.com/Hero-Armor/hero-armor.github.io/blob/main/audio/data/params.json", title: "audio/data/params.json — константи моделі" }
  - { id: "cases", resource: "https://github.com/Hero-Armor/hero-armor.github.io/blob/main/audio/data/cases.json", title: "audio/data/cases.json — кейси плайї" }
---

Числа нижче рахує тільки [санкціонована модель](/computations/audio-node-model.md);
руками їх ніхто не пише.[^params]

# Цифри

| Метрика | Значення |
|---------|----------|
| Споживання вузла | 39 Wh/добу (композитна доба)[^cases] |
| Разом з EcoFlow standby | 99 Wh/добу |
| Автономність | River 2 ≈ 2.3 діб · River 2 Max ≈ 4.6 діб · Delta 2 ≈ 9.3 діб |
| Сонце «в нуль» | ~28 Вт |
| Tj ампа, найгірший кейс | 81 °C (межа 150) |
| Гучність @3 м, день | 86 dB пік / ~74 dB сер. (+9 дБ до шуму) |
| Гучність @3 м, гучна ніч | запас -1 дБ |

Компонент: [Аудіо](/components/audio.md).

[^params]: audio/data/params.json — константи моделі
[^cases]: audio/data/cases.json — кейси плайї
