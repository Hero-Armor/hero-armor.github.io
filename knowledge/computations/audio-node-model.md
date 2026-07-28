---
type: "Attested Computation"
title: "Модель аудіо-вузла"
description: "Санкціонований розрахунок усіх цифр аудіо-вузла з data/params.json + cases.json."
runtime: "python"
computation: "https://github.com/Hero-Armor/hero-armor.github.io/blob/main/audio/model/audio_node_model.py"
tags: ["audio"]
generated: { by: "process:site-build" }
verified: { by: "human:gumanist", at: "2026-07-27T00:00:00Z" }
---

Єдине санкціоноване джерело чисел аудіо-вузла: power budget (крест-фактор
мови), теплова модель TPA3116, SPL, автономність від EcoFlow.

# Запуск

    cd site && python3 build.py        # перерахує все і перебудує сторінки
    python3 audio/model/audio_node_model.py   # тільки модель, друк у консоль

Вхід — [params.json](/model/audio-node.md) (константи) і кейси плайї; вихід —
числа на сторінках хабу та в [знімку моделі](/model/audio-node.md).
Правило проєкту: числа на сторінках рахує тільки ця модель.
