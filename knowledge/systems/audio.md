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

* [Захисний лак на всі плати — MG Chemicals 422B, два шари до виїзду](/decisions/zakhysnyi-lak-na-vsi-platy-mg-chemicals-422b-dva-shary-do-vy.md)
* [Кнопки взаємодії на прототипі голови — вирішити 1 чи 3 (Франк)](/decisions/knopky-vzaiemodii-na-prototypi-holovy-vyrishyty-1-chy-3-fran.md)
* [Датчик — LD2410C mmWave, не PIR](/decisions/datchyk-ld2410c-mmwave-ne-pir.md)
* [Радіатор TPA3116 — назовні герметичного боксу](/decisions/radiator-tpa3116-nazovni-hermetychnoho-boksu.md)
* [Без підвищувача до 16В — 12V вистачає](/decisions/bez-pidvyshchuvacha-do-16v-12v-vystachaie.md)
* [Гучність: gain 26 дБ + цифрове керування, три шари](/decisions/huchnist-gain-26-db-tsyfrove-keruvannia-try-shary.md)
* [Живлення звуку: свій кабель від авто-виходу 12 В, без реле](/decisions/zhyvlennia-zvuku-svii-kabel-vid-avto-vykhodu-12-v-bez-rele.md)
* [Звук — моно: один динамік, другий з пари — запас](/decisions/zvuk-mono-odyn-dynamik-druhyi-z-pary-zapas.md)
* [Запас плат ×2–3 — на плайї не паяємо](/decisions/zapas-plat-2-3-na-plaii-ne-paiaiemo.md)
* [Основа вузла — перфоборд 150×90, не 3D-друк і не «насипом у коробку»](/decisions/osnova-vuzla-perfobord-150-90-ne-3d-druk-i-ne-nasypom-u-koro.md)
* [Роз'ємні місця: XT60 на вході, клемники на платі, лопатки на динаміку](/decisions/roziemni-mistsia-xt60-na-vkhodi-klemnyky-na-plati-lopatky-na.md)
* [Коробка: пластик, з фільтрованою вентиляцією, радіатор ампа назовні](/decisions/korobka-plastyk-z-filtrovanoiu-ventyliatsiieiu-radiator-ampa.md)
* [Коробку аудіо не вентилюємо — рахунок каже, що нічого не гріється](/decisions/korobku-audio-ne-ventyliuiemo-rakhunok-kazhe-shcho-nichoho-n.md)
* [До динаміка паяємось, а не тиснемо «мами» на пелюстки](/decisions/do-dynamika-paiaiemos-a-ne-tysnemo-mamy-na-peliustky.md)
* [Читач радара — свій, не стороння бібліотека](/decisions/chytach-radara-svii-ne-storonnia-biblioteka.md)
* [Якщо радар замовк по UART — працюємо по піну OUT](/decisions/iakshcho-radar-zamovk-po-uart-pratsiuiemo-po-pinu-out.md)
* [Налаштування живуть у памʼяті ESP32, а не в прошивці](/decisions/nalashtuvannia-zhyvut-u-pamiati-esp32-a-ne-v-proshyvtsi.md)
* [Динамік ставимо ЗА бронею, отвору в ній не робимо](/decisions/dynamik-stavymo-za-broneiu-otvoru-v-nii-ne-robymo.md)
* [Робот рахує, скільки разів заговорив — журнал на картці](/decisions/robot-rakhuie-skilky-raziv-zahovoryv-zhurnal-na-karttsi.md)
* [Фраза лунає на ПОЯВУ людини, а не по таймеру](/decisions/fraza-lunaie-na-poiavu-liudyny-a-ne-po-taimeru.md)
* [Журнал пише і пропуски: коли радар бачив, а робот промовчав](/decisions/zhurnal-pyshe-i-propusky-koly-radar-bachyv-a-robot-promovcha.md)
* [XSMT на ЦАПі — обовʼязковий дріт на 3.3 В](/decisions/xsmt-na-tsapi-oboviazkovyi-drit-na-3-3-v.md)
* [Заміряно на живому вузлі: 1.5 Вт, працює від 10 В, радар бачить крізь пластик](/decisions/zamiriano-na-zhyvomu-vuzli-1-5-vt-pratsiuie-vid-10-v-radar-b.md)

# Задачі

* [A/B тест динаміків MA-3013 vs Herdio (на нічній гучності, 75 дБ фону)](/tasks/a-b-test-dynamikiv-ma-3013-vs-herdio-na-nichnii-huchnosti-75.md) — до роботи
* [Прошивка ESP32: MP3→I2S моно, 3 шари гучності, перемикання день/ніч по BLE, UART радара](/tasks/proshyvka-esp32-mp3-i2s-mono-3-shary-huchnosti-peremykannia-.md) — готово
* [Кліпи ElevenLabs: нормалізація піків −1 dBFS, HPF 120 Гц, 44.1k MP3 192k+](/tasks/klipy-elevenlabs-normalizatsiia-pikiv-1-dbfs-hpf-120-hts-44-.md) — чекаємо
* [Зібрати вузол на столі: повний ланцюг від EcoFlow, димова проба](/tasks/zibraty-vuzol-na-stoli-povnyi-lantsiuh-vid-ecoflow-dymova-pr.md) — готово
* [Пилозахист динаміка: гриль + тканина, мембрана вниз](/tasks/pylozakhyst-dynamika-hryl-tkanyna-membrana-vnyz.md) — готово
* [Звірити замовлену коробку по семи вимогах (пластик, 165×105×55, вводи, радіатор, вентиляція, доступ до USB)](/tasks/zviryty-zamovlenu-korobku-po-semy-vymohakh-plastyk-165-105-5.md) — готово
* [Зміряти лінійкою модулі й рознесення пінів ESP32, коли приїде посилка](/tasks/zmiriaty-liniikoiu-moduli-i-roznesennia-piniv-esp32-koly-pry.md) — чекаємо
* [Звірити тип клем динаміка MA-3013 (гвинт чи push-on) — від цього наконечники](/tasks/zviryty-typ-klem-dynamika-ma-3013-hvynt-chy-push-on-vid-tsoh.md) — готово
* [Докупити монтажну дрібницю: гермовводи, термоусадка, джампери, стяжки](/tasks/dokupyty-montazhnu-dribnytsiu-hermovvody-termousadka-dzhampe.md) — до роботи
* [Прошити ESP32 і пройти пʼять перевірок на столі (картка, звук, радар, BLE, потенціометр ампа)](/tasks/proshyty-esp32-i-proity-piat-perevirok-na-stoli-kartka-zvuk-.md) — готово
* [Звірити склад коробок: у листі Amazon 18 позицій, у нашому списку 19](/tasks/zviryty-sklad-korobok-u-lysti-amazon-18-pozytsii-u-nashomu-s.md) — до роботи
* [Нанести захисний лак MG Chemicals 422B на всі плати — до виїзду](/tasks/nanesty-zakhysnyi-lak-mg-chemicals-422b-na-vsi-platy-do-vyiz.md) — до роботи
* [Вирішити з Франком: 1 кнопка взаємодії чи 3 (так/ні/скасувати) на прототипі голови](/tasks/vyrishyty-z-frankom-1-knopka-vzaiemodii-chy-3-tak-ni-skasuva.md) — чекаємо
* [Дізнатись у конструктора остаточний Ø отвору і місце динаміка (груди Ø60 чи живіт)](/tasks/diznatys-u-konstruktora-ostatochnyi-otvoru-i-mistse-dynamika.md) — готово
* [Приміряти динамік до грудної панелі на місці і послухати, чи не глухо крізь броню](/tasks/prymiriaty-dynamik-do-hrudnoi-paneli-na-mistsi-i-poslukhaty-.md) — до роботи

# Закупівля

* [ESP32 WROOM-32 DevKit](/bom/esp32-wroom-32-devkit.md) — $16.59 за 3 плати, купити
* [PCM5102A (GY-PCM5102)](/bom/pcm5102a-gy-pcm5102.md) — $11.99 за набір 3 шт (взято 2 набори = 6 ЦАПів), купити
* [microSD SPI модуль](/bom/microsd-spi-modul.md) — $6.99 за 5 шт, купити
* [SanDisk 32GB Class 10](/bom/sandisk-32gb-class-10.md) — $23.95, купити
* [TPA3116D2 Mono (HiLetgo)](/bom/tpa3116d2-mono-hiletgo.md) — $13.99 за 2 плати, купити
* [Herdio 3" пара (куплено як Poly-Planar) — ПОВЕРНУТО](/bom/herdio-3-para-kupleno-iak-poly-planar-povernuto.md) — $69.99, купити
* [Herdio 3" пара (куплено як Poly-Planar) — ПОВЕРНУТО](/bom/herdio-3-para-kupleno-iak-poly-planar-povernuto.md) — $69.99, купити
* [LD2410C](/bom/ld2410c.md) — $20.48 за 3 шт, купити
* [Buck 12→5В ≥1.5А + LC](/bom/buck-12-5v-1-5a-lc.md) — $8.99 за 5 шт, купити
* [Радіатор 50×50 мм + термопрокладка](/bom/radiator-50-50-mm-termoprokladka.md) — ~$9/4шт, купити
* [Запобіжник 3А + тримач](/bom/zapobizhnyk-3a-trymach.md) — $8.99 за набір 6 шт, купити
* [Конденсатор 1000 µФ 25В low-ESR](/bom/kondensator-1000-f-25v-low-esr.md) — $4.99 за 10 шт, купити
* [Захист динаміка від пилу](/bom/zakhyst-dynamika-vid-pylu.md) — $10/2шт, купити
* [Штекер-прикурювач з клемами](/bom/shteker-prykuriuvach-z-klemamy.md) — $6/2шт, купити
* [XT60 пара + пігтейли](/bom/xt60-para-pihteily.md) — $6.99 за 2 пари, купити
* [Кабель 18AWG силікон, 2×2 м](/bom/kabel-18awg-sylikon-2-2-m.md) — $13/18м, купити
* [Макетна плата 9×15см двостороння](/bom/maketna-plata-9-15sm-dvostoronnia.md) — $13, купити
* [Набір нейлонових стійок M2.5/M3/M4](/bom/nabir-neilonovykh-stiiok-m2-5-m3-m4.md) — $17, купити
* [Клемники гвинтові 5.08мм 2-pin](/bom/klemnyky-hvyntovi-5-08mm-2-pin.md) — $9, купити
* [Гнізда-хедери 2.54мм (мама) кит](/bom/hnizda-khedery-2-54mm-mama-kyt.md) — $8, купити
* [Кабель: Станція (авто-вихід 12 В) → аудіо-вузол](/bom/kabel-stantsiia-avto-vykhid-12-v-audio-vuzol.md) — $71.12, купити
* [Екранований кабель ЦАП → амп (аукс-шнур, 30 см)](/bom/ekranovanyi-kabel-tsap-amp-auks-shnur-30-sm.md) — $4.19, купити
* [Гермовводи PG7–PG16, набір 25 шт](/bom/hermovvody-pg7-pg16-nabir-25-sht.md) — $7.99, купити
* [Джампери Dupont мама-мама 20 см](/bom/dzhampery-dupont-mama-mama-20-sm.md) — $4, купити
* [Стяжки нейлонові UV-стійкі, 400 шт](/bom/stiazhky-neilonovi-uv-stiiki-400-sht.md) — $7, купити
* [Коробка ABS IP65 200×120×75 (якщо своя не підійде)](/bom/korobka-abs-ip65-200-120-75-iakshcho-svoia-ne-pidiide.md) — $10, купити

# Розраховані цифри

Див. [модель аудіо-вузла](/model/audio-node.md) — числа рахує тільки [санкціонована модель](/computations/audio-node-model.md).
