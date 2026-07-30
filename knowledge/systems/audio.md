---
type: "Component"
title: "Аудіо"
description: "Дизайн готовий: LD2410C радар → ESP32 → PCM5102A → TPA3116D2 Mono → MA-3013. 39 Wh/добу, радіатор назовні, 3 шари гучності. Чекаємо динаміки на A/B тест."
resource: "https://hero-armor.github.io/audio.html"
tags: ["audio"]
system_status: "design-ready"
generated: { by: "process:site-build" }
---

Дизайн готовий: LD2410C радар → ESP32 → PCM5102A → TPA3116D2 Mono → MA-3013. 39 Wh/добу, радіатор назовні, 3 шари гучності. Чекаємо динаміки на A/B тест.

# Рішення

* [Датчик — LD2410C mmWave, не PIR](/decisions/datchyk-ld2410c-mmwave-ne-pir.md)
* [Радіатор TPA3116 — назовні герметичного боксу](/decisions/radiator-tpa3116-nazovni-hermetychnoho-boksu.md)
* [Без підвищувача до 16В — 12V вистачає](/decisions/bez-pidvyshchuvacha-do-16v-12v-vystachaie.md)
* [Гучність: gain 26 дБ + цифрове керування, три шари](/decisions/huchnist-gain-26-db-tsyfrove-keruvannia-try-shary.md)
* [Живлення: EcoFlow 12V DC, buck ≥1.5A, захист](/decisions/zhyvlennia-ecoflow-12v-dc-buck-1-5a-zakhyst.md)
* [Звук — моно: один динамік, другий з пари — запас](/decisions/zvuk-mono-odyn-dynamik-druhyi-z-pary-zapas.md)
* [Запас плат ×2–3 — на плайї не паяємо](/decisions/zapas-plat-2-3-na-plaii-ne-paiaiemo.md)

# Задачі

* [A/B тест динаміків MA-3013 vs Herdio (на нічній гучності, 75 дБ фону)](/tasks/a-b-test-dynamikiv-ma-3013-vs-herdio-na-nichnii-huchnosti-75.md) — чекаємо
* [Прошивка ESP32: MP3→I2S моно, 3 шари гучності, перемикання день/ніч по BLE, UART радара](/tasks/proshyvka-esp32-mp3-i2s-mono-3-shary-huchnosti-peremykannia-.md) — чекаємо
* [Кліпи ElevenLabs: нормалізація піків −1 dBFS, HPF 120 Гц, 44.1k MP3 192k+](/tasks/klipy-elevenlabs-normalizatsiia-pikiv-1-dbfs-hpf-120-hts-44-.md) — чекаємо
* [Зібрати вузол на столі: повний ланцюг від EcoFlow, димова проба](/tasks/zibraty-vuzol-na-stoli-povnyi-lantsiuh-vid-ecoflow-dymova-pr.md) — чекаємо
* [Пилозахист динаміка: гриль + тканина, мембрана вниз](/tasks/pylozakhyst-dynamika-hryl-tkanyna-membrana-vnyz.md) — чекаємо

# Закупівля

* [ESP32 WROOM-32 DevKit](/bom/esp32-wroom-32-devkit.md) — $17/3шт, купити
* [PCM5102A (GY-PCM5102)](/bom/pcm5102a-gy-pcm5102.md) — $12/3шт, купити
* [microSD SPI модуль](/bom/microsd-spi-modul.md) — $7/5шт, купити
* [SanDisk 32GB Class 10](/bom/sandisk-32gb-class-10.md) — ~$10, купити
* [TPA3116D2 Mono (WINGONEER)](/bom/tpa3116d2-mono-wingoneer.md) — $14/2шт, купити
* [Poly-Planar MA-3013, пара](/bom/poly-planar-ma-3013-para.md) — $70, купити
* [Herdio HMS60 3", пара](/bom/herdio-hms60-3-para.md) — $32, купити
* [LD2410C](/bom/ld2410c.md) — $20/3шт, купити
* [Buck 12→5В ≥1.5А + LC](/bom/buck-12-5v-1-5a-lc.md) — $9/5шт, купити
* [Радіатор 50×50 мм + термопрокладка](/bom/radiator-50-50-mm-termoprokladka.md) — ~$9/4шт, купити
* [Запобіжник 3А + тримач, 1000 µФ 25В](/bom/zapobizhnyk-3a-trymach-1000-f-25v.md) — $9/6шт, купити
* [Конденсатор 1000 µФ 25В low-ESR](/bom/kondensator-1000-f-25v-low-esr.md) — $5/10шт, купити
* [Захист динаміка від пилу](/bom/zakhyst-dynamika-vid-pylu.md) — $10/2шт, купити
* [Штекер-прикурювач з клемами](/bom/shteker-prykuriuvach-z-klemamy.md) — $6/2шт, купити
* [XT60 пара + пігтейли](/bom/xt60-para-pihteily.md) — $7/2пари, купити
* [Кабель 18AWG силікон, 2×2 м](/bom/kabel-18awg-sylikon-2-2-m.md) — $13/18м, купити
* [Макетна плата 9×15см двостороння](/bom/maketna-plata-9-15sm-dvostoronnia.md) — $13, купити
* [Набір нейлонових стійок M2.5/M3/M4](/bom/nabir-neilonovykh-stiiok-m2-5-m3-m4.md) — $17, купити
* [Клемники гвинтові 5.08мм 2-pin](/bom/klemnyky-hvyntovi-5-08mm-2-pin.md) — $9, купити
* [Гнізда-хедери 2.54мм (мама) кит](/bom/hnizda-khedery-2-54mm-mama-kyt.md) — $8, купити

# Розраховані цифри

Див. [модель аудіо-вузла](/model/audio-node.md) — числа рахує тільки [санкціонована модель](/computations/audio-node-model.md).
