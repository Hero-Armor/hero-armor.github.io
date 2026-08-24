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
| Автономність | River 2 Pro ≈ 7.0 діб · Delta 2 ≈ 9.3 діб · Delta 2 Max ≈ 18.5 діб · Delta Pro ≈ 32.6 діб · Delta 3 Max Plus ≈ 18.5 діб · Growatt INFINITY 2000 PRO ≈ 18.5 діб · FOSSiBOT F2400 ≈ 18.5 діб · Pecron E1500LFP ≈ 13.9 діб · Bluetti AC200MAX ≈ 18.5 діб · Delta 3 Ultra Plus ≈ 27.8 діб · Bluetti AC200P ≈ 18.1 діб |
| Сонце «в нуль» | ~28 Вт |
| Tj ампа, найгірший кейс | 81 °C (межа 150) |
| Гучність @3 м, день | 86 dB пік / ~74 dB сер. (+9 дБ до шуму) |
| Гучність @3 м, гучна ніч | запас -1 дБ |

Система: [Аудіо](/systems/audio.md).

[^params]: audio/data/params.json — константи моделі
[^cases]: audio/data/cases.json — кейси плайї
