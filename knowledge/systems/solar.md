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
* [12-вольтовий вихід EcoFlow тримає лише 126 Вт — це вузьке місце](/decisions/12-voltovyi-vykhid-ecoflow-trymaie-lyshe-126-vt-tse-vuzke-mi.md)
* [Станції гріються: межа +45°C, а на плайї 40-45°C](/decisions/stantsii-hriiutsia-mezha-45-c-a-na-plaii-40-45-c.md)
* [Нічне мале навантаження станцію не присипляє](/decisions/nichne-male-navantazhennia-stantsiiu-ne-prysypliaie.md)
* [Якщо 126 Вт не вистачить — чотири станції з 30 А по 12 В](/decisions/iakshcho-126-vt-ne-vystachyt-chotyry-stantsii-z-30-a-po-12-v.md)
* [Перехідник від порту зовнішньої батареї — уточнено (див. нижче)](/decisions/perekhidnyk-vid-portu-zovnishnoi-batarei-utochneno-dyv-nyzhc.md)
* [Запасний шлях: розетка 220 В + блок живлення 12 В коштує ~20% ємності](/decisions/zapasnyi-shliakh-rozetka-220-v-blok-zhyvlennia-12-v-koshtuie.md)
* [Anker F2000 має TT-30R — але це 120 В змінного, не наші 12 В](/decisions/anker-f2000-maie-tt-30r-ale-tse-120-v-zminnoho-ne-nashi-12-v.md)
* [Перехідники на сторонні АКБ існують — але вони 48-вольтові](/decisions/perekhidnyky-na-storonni-akb-isnuiut-ale-vony-48-voltovi.md)
* [Найпростіший шлях: окремий АКБ 12 В живить світло, станція його заряджає](/decisions/naiprostishyi-shliakh-okremyi-akb-12-v-zhyvyt-svitlo-stantsi.md)
* [Понизити порт розширення 48→12 В — підтверджено, EcoFlow сам так робить](/decisions/ponyzyty-port-rozshyrennia-48-12-v-pidtverdzheno-ecoflow-sam.md)
* [Bluetti має ШТАТНИЙ 12 В / 30 А — нічого не паяти](/decisions/bluetti-maie-shtatnyi-12-v-30-a-nichoho-ne-paiaty.md)
* [AC200P на Marketplace за $700 — найдешевший робочий шлях](/decisions/ac200p-na-marketplace-za-700-naideshevshyi-robochyi-shliakh.md)

# Задачі

* [Тест EcoFlow: «DC always on» під навантаженням 1.6 Вт на всю ніч](/tasks/test-ecoflow-dc-always-on-pid-navantazhenniam-1-6-vt-na-vsiu.md) — чекаємо
* [Вирішити скільки станцій і яку модель](/tasks/vyrishyty-skilky-stantsii-i-iaku-model.md) — чекаємо
* [Звірити паспорт станції: ліміт сонячного входу](/tasks/zviryty-pasport-stantsii-limit-soniachnoho-vkhodu.md) — готово
* [Спроєктувати раму сонячного масиву під вітер плайї](/tasks/sproiektuvaty-ramu-soniachnoho-masyvu-pid-viter-plaii.md) — чекаємо
* [Знайти шлях на 20-30 А по 12 В (станція або перехідник)](/tasks/znaity-shliakh-na-20-30-a-po-12-v-stantsiia-abo-perekhidnyk.md) — в роботі
* [Перевірити за $1, чи віддає порт розширення струм (резистор 1 кОм + мультиметр)](/tasks/pereviryty-za-1-chy-viddaie-port-rozshyrennia-strum-rezystor.md) — до роботи
* [Подивитись Bluetti AC200P на Marketplace ($700-800, самовивіз)](/tasks/podyvytys-bluetti-ac200p-na-marketplace-700-800-samovyviz.md) — до роботи

# Закупівля

* [Сонячні панелі для масиву (потужність не обрана)](/bom/soniachni-paneli-dlia-masyvu-potuzhnist-ne-obrana.md) — $149, купити
* [Станції EcoFlow ×2 (модель не обрана)](/bom/stantsii-ecoflow-2-model-ne-obrana.md) — $1099/шт, купити
* [Рама під сонячний масив](/bom/rama-pid-soniachnyi-masyv.md) — —, купити
* [Кабель MC4 + роз'єми для масиву](/bom/kabel-mc4-roziemy-dlia-masyvu.md) — $34.00, купити
* [LiFePO4 12 В 100 Ah (буфер під світло)](/bom/lifepo4-12-v-100-ah-bufer-pid-svitlo.md) — ~$250, купити
* [Зарядник 14.6 В 20-30 А з Anderson](/bom/zariadnyk-14-6-v-20-30-a-z-anderson.md) — ~$60, купити
* [Victron Orion-Tr 48/12-30A (360 Вт), ізольований](/bom/victron-orion-tr-48-12-30a-360-vt-izolovanyi.md) — $201, купити
* [Victron Orion-Tr 48/12-20A (240 Вт), ізольований](/bom/victron-orion-tr-48-12-20a-240-vt-izolovanyi.md) — $114, купити
* [BLUETTI RV Cable 12V/30A (авіа→XT60→Anderson)](/bom/bluetti-rv-cable-12v-30a-avia-xt60-anderson.md) — ~$45, купити
* [Кабель XT150 для порту розширення (готовий)](/bom/kabel-xt150-dlia-portu-rozshyrennia-hotovyi.md) — ~$25, купити
