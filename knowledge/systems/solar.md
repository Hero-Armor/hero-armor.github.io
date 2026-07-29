---
type: "Component"
title: "Живлення"
description: "Одна станція EcoFlow годує і світло, і звук: разом 1516 Wh на добу. Панелі збираємо самі — у нуль виходить ~418 Вт, беремо 600 Вт із запасом. Станція змінна: сі"
resource: "https://hero-armor.github.io/solar.html"
tags: ["solar"]
system_status: "in-design"
generated: { by: "process:site-build" }
---

Одна станція EcoFlow годує і світло, і звук: разом 1516 Wh на добу. Панелі збираємо самі — у нуль виходить ~418 Вт, беремо 600 Вт із запасом. Станція змінна: сіла — на базу під розетку, на її місце заряджена. Без панелей тримає лише добу.

# Рішення

* [Живлення — окремий компонент, одна станція на все](/decisions/zhyvlennia-okremyi-komponent-odna-stantsiia-na-vse.md)
* [Станція змінна за задумом, а не в аварії](/decisions/stantsiia-zminna-za-zadumom-a-ne-v-avarii.md)
* [Панелі — несуча частина, а не страховка](/decisions/paneli-nesucha-chastyna-a-ne-strakhovka.md)
* [Стелю масиву задає не бюджет, а вхід станції](/decisions/steliu-masyvu-zadaie-ne-biudzhet-a-vkhid-stantsii.md)
* [Скільки станцій купуємо](/decisions/skilky-stantsii-kupuiemo.md)
* [Паспортні числа станцій треба звірити](/decisions/pasportni-chysla-stantsii-treba-zviryty.md)
* [Станція і масив не фіксуються заздалегідь](/decisions/stantsiia-i-masyv-ne-fiksuiutsia-zazdalehid.md)

# Задачі

* [Тест EcoFlow: «DC always on» під навантаженням 1.6 Вт на всю ніч](/tasks/test-ecoflow-dc-always-on-pid-navantazhenniam-1-6-vt-na-vsiu.md) — до роботи
* [Вирішити скільки станцій EcoFlow і яку модель](/tasks/vyrishyty-skilky-stantsii-ecoflow-i-iaku-model.md) — до роботи
* [Звірити паспорт станції: ліміт сонячного входу](/tasks/zviryty-pasport-stantsii-limit-soniachnoho-vkhodu.md) — до роботи
* [Спроєктувати раму сонячного масиву під вітер плайї](/tasks/sproiektuvaty-ramu-soniachnoho-masyvu-pid-viter-plaii.md) — до роботи

# Закупівля

* [EcoFlow (12V DC-порт)](/bom/ecoflow-12v-dc-port.md) — —, є
* [Сонячні панелі для масиву (потужність не обрана)](/bom/soniachni-paneli-dlia-masyvu-potuzhnist-ne-obrana.md) — $149, купити
* [Станції EcoFlow ×2 (модель не обрана)](/bom/stantsii-ecoflow-2-model-ne-obrana.md) — $1099/шт, купити
* [Рама під сонячний масив](/bom/rama-pid-soniachnyi-masyv.md) — —, купити
* [Кабель MC4 + роз'єми для масиву](/bom/kabel-mc4-roziemy-dlia-masyvu.md) — —, купити
