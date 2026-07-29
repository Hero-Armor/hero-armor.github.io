---
type: "Component"
title: "Світло"
description: "Шина 12 В, три групи: прожектори заливки, декор («біжуча вода» + лампи робота) і аварійна лінія, яка тримається найдовше. Композитна ніч 1416 Wh — дві третини з"
resource: "https://hero-armor.github.io/lights.html"
tags: ["lights"]
system_status: "in-design"
generated: { by: "process:site-build" }
---

Шина 12 В, три групи: прожектори заливки, декор («біжуча вода» + лампи робота) і аварійна лінія, яка тримається найдовше. Композитна ніч 1416 Wh — дві третини з'їдають декор і аварійка, не прожектори. Модель показала, що наявний кабель на 12 В не тягне: магістралі треба AWG 6, лінії декору — AWG 8.

# Рішення

* [Прожектори — MR16 без стабілізатора (voltage-following)](/decisions/prozhektory-mr16-bez-stabilizatora-voltage-following.md)
* [Адресна стрічка вдень вимкнена](/decisions/adresna-strichka-vden-vymknena.md)
* [«Біжуча вода» — біла, зовнішній контур прибрано](/decisions/bizhucha-voda-bila-zovnishnii-kontur-prybrano.md)
* [Панель 500 Вт замість попередніх 100 Вт](/decisions/panel-500-vt-zamist-poperednikh-100-vt.md)
* [Анімація замість заливки — стрічка світить не вся одразу](/decisions/animatsiia-zamist-zalyvky-strichka-svityt-ne-vsia-odrazu.md)
* [Сходи подіуму — наша лінія чи автономні сонячні](/decisions/skhody-podiumu-nasha-liniia-chy-avtonomni-soniachni.md)
* [Колір габаритних вогнів — жовтий чи червоний](/decisions/kolir-habarytnykh-vohniv-zhovtyi-chy-chervonyi.md)
* [Неон WS2811 ще не замовлено](/decisions/neon-ws2811-shche-ne-zamovleno.md)
* [Світло вмикає фотореле, а не таймер](/decisions/svitlo-vmykaie-fotorele-a-ne-taimer.md)
* [Три групи — три реле, аварійна на своєму каналі](/decisions/try-hrupy-try-rele-avariina-na-svoiemu-kanali.md)
* [Просадку рахуємо деревом, а не по лініях](/decisions/prosadku-rakhuiemo-derevom-a-ne-po-liniiakh.md)
* [Стрічку обмежуємо по струму в прошивці](/decisions/strichku-obmezhuiemo-po-strumu-v-proshyvtsi.md)
* [Номінали запобіжників — з моделі, а не навмання](/decisions/nominaly-zapobizhnykiv-z-modeli-a-ne-navmannia.md)
* [Кабель, куплений під 24 В, треба доповнити під 12 В](/decisions/kabel-kuplenyi-pid-24-v-treba-dopovnyty-pid-12-v.md)
* [Довжини кабелів — прикидки, не з креслень](/decisions/dovzhyny-kabeliv-prykydky-ne-z-kreslen.md)
* [Реальний замір удвічі менший за модель — звірити стрічку](/decisions/realnyi-zamir-udvichi-menshyi-za-model-zviryty-strichku.md)

# Задачі

* [Звести бюджет світла: заявлені ~170–220 Вт LED проти панелі 100 Вт — перерахувати (сайт сам радить зменшити стрічки)](/tasks/zvesty-biudzhet-svitla-zaiavleni-170-220-vt-led-proty-paneli.md) — готово
* [Обрати і замовити неон WS2811 під 12 В](/tasks/obraty-i-zamovyty-neon-ws2811-pid-12-v.md) — до роботи
* [Перевірити ватметром voltage-following на Gardencoin](/tasks/pereviryty-vatmetrom-voltage-following-na-gardencoin.md) — до роботи
* [Вирішити: 12 В MR16 на шині 24 В через ШІМ чи step-down](/tasks/vyrishyty-12-v-mr16-na-shyni-24-v-cherez-shim-chy-step-down.md) — готово
* [Уточнити в архітектора: сходи ×24 в нашу лінію чи автономні сонячні](/tasks/utochnyty-v-arkhitektora-skhody-24-v-nashu-liniiu-chy-avtono.md) — чекаємо
* [Звірити статуси закупівлі світла з інвойсом](/tasks/zviryty-statusy-zakupivli-svitla-z-invoisom.md) — до роботи
* [Докупити товщий кабель: AWG 6 магістраль, AWG 8 декор](/tasks/dokupyty-tovshchyi-kabel-awg-6-mahistral-awg-8-dekor.md) — до роботи
* [Заміряти реальні довжини траси після складання подіуму](/tasks/zamiriaty-realni-dovzhyny-trasy-pislia-skladannia-podiumu.md) — чекаємо
* [Запитати конструктора про зовнішній периметр подіуму](/tasks/zapytaty-konstruktora-pro-zovnishnii-perymetr-podiumu.md) — до роботи

# Закупівля

* [Gardencoin прожектор + MR16 4000K](/bom/gardencoin-prozhektor-mr16-4000k.md) — $43/уп, є
* [Gebildet LED 12 мм, металеві](/bom/gebildet-led-12-mm-metalevi.md) — —, є
* [Gebildet LED 8 мм, металеві](/bom/gebildet-led-8-mm-metalevi.md) — —, є
* [Nilight габаритні вогні 3 Вт](/bom/nilight-habarytni-vohni-3-vt.md) — $18.50, є
* [Landscapestation лампи сходів 1 Вт](/bom/landscapestation-lampy-skhodiv-1-vt.md) — $100/уп, є
* [Неон WS2811/WS2815 12 В силіконовий, 10 м](/bom/neon-ws2811-ws2815-12-v-sylikonovyi-10-m.md) — $47, купити
* [GLEDOPTO ESP32 WLED, IP65](/bom/gledopto-esp32-wled-ip65.md) — $23, є
* [SUPERNIGHT ШІМ-диммер 12-24 В 30 А](/bom/supernight-shim-dymmer-12-24-v-30-a.md) — $12, є
* [Щит-бокс із тримачами запобіжників](/bom/shchyt-boks-iz-trymachamy-zapobizhnykiv.md) — —, купити
* [Запобіжники ATO/ATC, набір](/bom/zapobizhnyky-ato-atc-nabir.md) — —, купити
* [Фотореле (сутінкове) 12 В](/bom/fotorele-sutinkove-12-v.md) — —, купити
* [Реле на групи 12 В, 30 А](/bom/rele-na-hrupy-12-v-30-a.md) — —, купити
* [Гермокоробка IP66 для щита і реле](/bom/hermokorobka-ip66-dlia-shchyta-i-rele.md) — —, купити
* [Гермокоробки IP65 під диммер і WLED](/bom/hermokorobky-ip65-pid-dymmer-i-wled.md) — —, купити
* [Гермороз'єми IP68 (швидкознімні)](/bom/hermoroziemy-ip68-shvydkoznimni.md) — —, купити
* [Гель-конектори / вологозахищені клеми](/bom/hel-konektory-volohozakhyshcheni-klemy.md) — —, купити
* [Гофра/кабель-канал для відводів](/bom/hofra-kabel-kanal-dlia-vidvodiv.md) — —, купити
* [Кабель: Станція → щит запобіжників](/bom/kabel-stantsiia-shchyt-zapobizhnykiv.md) — —, купити
* [Кабель: Щит → коробка диммера (Гр.1)](/bom/kabel-shchyt-korobka-dymmera-hr-1.md) — —, купити
* [Кабель: Диммер → кільце прожекторів](/bom/kabel-dymmer-kiltse-prozhektoriv.md) — —, купити
* [Кабель: Відвід на прожектор (найдальший)](/bom/kabel-vidvid-na-prozhektor-naidalshyi.md) — —, купити
* [Кабель: Щит → коробка WLED (Гр.2)](/bom/kabel-shchyt-korobka-wled-hr-2.md) — —, купити
* [Кабель: WLED → точки живлення стрічки](/bom/kabel-wled-tochky-zhyvlennia-strichky.md) — —, купити
* [Кабель: Коробка → лампи робота](/bom/kabel-korobka-lampy-robota.md) — —, купити
* [Кабель: Щит → коробка аварійної (Гр.3А)](/bom/kabel-shchyt-korobka-avariinoi-hr-3a.md) — —, купити
* [Кабель: Коробка → габарити по кутах](/bom/kabel-korobka-habaryty-po-kutakh.md) — —, купити
* [Кабель: Коробка → лампи сходів](/bom/kabel-korobka-lampy-skhodiv.md) — —, купити
* [Блок запобіжників Blue Sea 5026 (12 кіл)](/bom/blok-zapobizhnykiv-blue-sea-5026-12-kil.md) — ~$40, купити
* [Алюмінієвий U-профіль для LED у настил подіуму](/bom/aliuminiievyi-u-profil-dlia-led-u-nastyl-podiumu.md) — ~$30, купити
