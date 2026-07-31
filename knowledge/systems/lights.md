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

* [Адресну стрічку рахуємо по біжучому фронту, не по повній лінії](/decisions/adresnu-strichku-rakhuiemo-po-bizhuchomu-frontu-ne-po-povnii.md)
* [Прожектори — MR16 без стабілізатора (voltage-following)](/decisions/prozhektory-mr16-bez-stabilizatora-voltage-following.md)
* [Адресна стрічка вдень вимкнена](/decisions/adresna-strichka-vden-vymknena.md)
* [«Біжуча вода» — біла, зовнішній контур прибрано](/decisions/bizhucha-voda-bila-zovnishnii-kontur-prybrano.md)
* [Анімація замість заливки — стрічка світить не вся одразу](/decisions/animatsiia-zamist-zalyvky-strichka-svityt-ne-vsia-odrazu.md)
* [Сходи подіуму — наша лінія чи автономні сонячні](/decisions/skhody-podiumu-nasha-liniia-chy-avtonomni-soniachni.md)
* [Колір габаритних вогнів — жовтий чи червоний](/decisions/kolir-habarytnykh-vohniv-zhovtyi-chy-chervonyi.md)
* [Стрічка обрана — WS2811 (мій розбір WS2815 перекрито)](/decisions/strichka-obrana-ws2811-mii-rozbir-ws2815-perekryto.md)
* [Стрічку ріжемо і міняємо модулями, а не латаємо на плайї](/decisions/strichku-rizhemo-i-miniaiemo-moduliamy-a-ne-lataiemo-na-plai.md)
* [Фотореле прибрано — автовмикання по темряві скасовано](/decisions/fotorele-prybrano-avtovmykannia-po-temriavi-skasovano.md)
* [Три групи — три реле, аварійна на своєму каналі](/decisions/try-hrupy-try-rele-avariina-na-svoiemu-kanali.md)
* [Просадку рахуємо деревом, а не по лініях](/decisions/prosadku-rakhuiemo-derevom-a-ne-po-liniiakh.md)
* [Стрічку обмежуємо по струму в прошивці](/decisions/strichku-obmezhuiemo-po-strumu-v-proshyvtsi.md)
* [Номінали запобіжників — з моделі, а не навмання](/decisions/nominaly-zapobizhnykiv-z-modeli-a-ne-navmannia.md)
* [Наявного кабелю вистачає — AWG 6 не купуємо](/decisions/naiavnoho-kabeliu-vystachaie-awg-6-ne-kupuiemo.md)
* [Довжини кабелів — прикидки, не з креслень](/decisions/dovzhyny-kabeliv-prykydky-ne-z-kreslen.md)
* [Реальний замір удвічі менший за модель — звірити стрічку](/decisions/realnyi-zamir-udvichi-menshyi-za-model-zviryty-strichku.md)
* [Коло, а не восьмикутник — фінально](/decisions/kolo-a-ne-vosmykutnyk-finalno.md)
* [Стрічка мусить тримати +60°C — попередні відхилені](/decisions/strichka-musyt-trymaty-60-c-poperedni-vidkhyleni.md)
* [Просадка вздовж самої стрічки — перевірити на довжині гілки](/decisions/prosadka-vzdovzh-samoi-strichky-pereviryty-na-dovzhyni-hilky.md)
* [Як герметизувати різи стрічки: нейтральний силікон, не оцтовий і не термоклей](/decisions/iak-hermetyzuvaty-rizy-strichky-neitralnyi-sylikon-ne-otstov.md)
* [Чим вмикати прожектори і аварійну без фотореле](/decisions/chym-vmykaty-prozhektory-i-avariinu-bez-fotorele.md)
* [Звук і світло — два окремі кабелі від станції](/decisions/zvuk-i-svitlo-dva-okremi-kabeli-vid-stantsii.md)

# Задачі

* [Звести бюджет світла: заявлені ~170–220 Вт LED проти панелі 100 Вт — перерахувати (сайт сам радить зменшити стрічки)](/tasks/zvesty-biudzhet-svitla-zaiavleni-170-220-vt-led-proty-paneli.md) — готово
* [Обрати і замовити неон WS2811 під 12 В](/tasks/obraty-i-zamovyty-neon-ws2811-pid-12-v.md) — готово
* [Стенд ламп прожектора: три лампи на заниженні напруги](/tasks/stend-lamp-prozhektora-try-lampy-na-zanyzhenni-napruhy.md) — в роботі
* [Вирішити: 12 В MR16 на шині 24 В через ШІМ чи step-down](/tasks/vyrishyty-12-v-mr16-na-shyni-24-v-cherez-shim-chy-step-down.md) — готово
* [Уточнити в архітектора: сходи ×24 в нашу лінію чи автономні сонячні](/tasks/utochnyty-v-arkhitektora-skhody-24-v-nashu-liniiu-chy-avtono.md) — чекаємо
* [Звірити статуси закупівлі світла з інвойсом](/tasks/zviryty-statusy-zakupivli-svitla-z-invoisom.md) — чекаємо
* [Докупити товщий кабель: AWG 6 магістраль, AWG 8 декор](/tasks/dokupyty-tovshchyi-kabel-awg-6-mahistral-awg-8-dekor.md) — готово
* [Заміряти реальні довжини траси після складання подіуму](/tasks/zamiriaty-realni-dovzhyny-trasy-pislia-skladannia-podiumu.md) — чекаємо
* [Запитати конструктора про зовнішній периметр подіуму](/tasks/zapytaty-konstruktora-pro-zovnishnii-perymetr-podiumu.md) — чекаємо
* [Marcel: заміряти трубу кріплення прожектора (діаметр, різьба)](/tasks/marcel-zamiriaty-trubu-kriplennia-prozhektora-diametr-rizba.md) — чекаємо
* [Відповісти Володимиру по просадці 12В — тест уже зроблено](/tasks/vidpovisty-volodymyru-po-prosadtsi-12v-test-uzhe-zrobleno.md) — чекаємо
* [Зміряти ватметром реальне споживання LED-стрічки (Вт/м)](/tasks/zmiriaty-vatmetrom-realne-spozhyvannia-led-strichky-vt-m.md) — в роботі
* [Дозамовити стрічку: 2 рулони по 5 м (треба 9.77 м, є 5 м)](/tasks/dozamovyty-strichku-2-rulony-po-5-m-treba-9-77-m-ie-5-m.md) — готово
* [Перевірити, на яку адресу йде стрічка (LA чи SF)](/tasks/pereviryty-na-iaku-adresu-ide-strichka-la-chy-sf.md) — до роботи
* [Написати Володимиру: коло лишається + цифри просадки](/tasks/napysaty-volodymyru-kolo-lyshaietsia-tsyfry-prosadky.md) — готово
* [Заміряти переріз стрічки, коли прийде (під заглушки)](/tasks/zamiriaty-pereriz-strichky-koly-pryide-pid-zahlushky.md) — до роботи
* [Обрати, чим вмикати прожектори і аварійну без фотореле](/tasks/obraty-chym-vmykaty-prozhektory-i-avariinu-bez-fotorele.md) — чекаємо
* [Замовити кошик дрібниці по світлу (заглушки + термоусадка) ≈ $84](/tasks/zamovyty-koshyk-dribnytsi-po-svitlu-zahlushky-termousadka-84.md) — до роботи

# Закупівля

* [Gardencoin прожектор + MR16 4000K](/bom/gardencoin-prozhektor-mr16-4000k.md) — $43/уп, купити
* [Gebildet LED 12 мм, металеві](/bom/gebildet-led-12-mm-metalevi.md) — —, купити
* [Gebildet LED 8 мм, металеві](/bom/gebildet-led-8-mm-metalevi.md) — —, купити
* [Nilight габаритні вогні 3 Вт](/bom/nilight-habarytni-vohni-3-vt.md) — $18.50, купити
* [Landscapestation лампи сходів 1 Вт](/bom/landscapestation-lampy-skhodiv-1-vt.md) — $100/уп, купити
* [Неон WS2811 12 В силіконовий — дозамовити 2 рулони по 5 м](/bom/neon-ws2811-12-v-sylikonovyi-dozamovyty-2-rulony-po-5-m.md) — $47, купити
* [GLEDOPTO ESP32 WLED, IP65](/bom/gledopto-esp32-wled-ip65.md) — $23, купити
* [SUPERNIGHT ШІМ-диммер 12-24 В 30 А](/bom/supernight-shim-dymmer-12-24-v-30-a.md) — $12, купити
* [Щит-бокс із тримачами запобіжників](/bom/shchyt-boks-iz-trymachamy-zapobizhnykiv.md) — —, купити
* [Запобіжники ATO/ATC, набір](/bom/zapobizhnyky-ato-atc-nabir.md) — —, купити
* [Реле на групи 12 В, 30 А](/bom/rele-na-hrupy-12-v-30-a.md) — —, купити
* [Гермокоробка IP66 для щита і реле](/bom/hermokorobka-ip66-dlia-shchyta-i-rele.md) — —, купити
* [Гермокоробки IP65 під диммер і WLED](/bom/hermokorobky-ip65-pid-dymmer-i-wled.md) — —, купити
* [Гермороз'єми IP68 (швидкознімні)](/bom/hermoroziemy-ip68-shvydkoznimni.md) — —, купити
* [Гель-конектори / вологозахищені клеми](/bom/hel-konektory-volohozakhyshcheni-klemy.md) — —, купити
* [Гофра/кабель-канал для відводів](/bom/hofra-kabel-kanal-dlia-vidvodiv.md) — —, купити
* [Кабель: Станція (30 А вихід) → щит запобіжників](/bom/kabel-stantsiia-30-a-vykhid-shchyt-zapobizhnykiv.md) — —, купити
* [Кабель: Щит → коробка диммера (Гр.1)](/bom/kabel-shchyt-korobka-dymmera-hr-1.md) — —, купити
* [Кабель: Диммер → кільце прожекторів](/bom/kabel-dymmer-kiltse-prozhektoriv.md) — —, купити
* [Кабель: Відвід на прожектор (найдальший)](/bom/kabel-vidvid-na-prozhektor-naidalshyi.md) — —, купити
* [Кабель: Щит → коробка WLED (Гр.2)](/bom/kabel-shchyt-korobka-wled-hr-2.md) — —, купити
* [Кабель: WLED → точки живлення стрічки](/bom/kabel-wled-tochky-zhyvlennia-strichky.md) — —, купити
* [Кабель: Коробка → лампи робота](/bom/kabel-korobka-lampy-robota.md) — —, купити
* [Кабель: Щит → коробка аварійної (Гр.3А)](/bom/kabel-shchyt-korobka-avariinoi-hr-3a.md) — —, купити
* [Кабель: Коробка → габарити по кутах](/bom/kabel-korobka-habaryty-po-kutakh.md) — —, купити
* [Кабель: Коробка → лампи сходів](/bom/kabel-korobka-lampy-skhodiv.md) — —, купити
* [Алюмінієвий U-профіль для LED у настил подіуму](/bom/aliuminiievyi-u-profil-dlia-led-u-nastyl-podiumu.md) — ~$30, купити
* [ASI 388 Electronic Grade Silicone, тюбик 2.8 oz](/bom/asi-388-electronic-grade-silicone-tiubyk-2-8-oz.md) — $10, купити
* [Заглушки неон 6×12 мм — набір (глухі + з отвором)](/bom/zahlushky-neon-6-12-mm-nabir-hlukhi-z-otvorom.md) — $13.59, купити
* [Заглушки неон 6×12 мм — альтернатива iNextStation](/bom/zahlushky-neon-6-12-mm-alternatyva-inextstation.md) — $11.99, купити
* [Заглушки неон 8×16 мм — набір 60 шт](/bom/zahlushky-neon-8-16-mm-nabir-60-sht.md) — $11.99, купити
* [Заглушки неон 10 мм (SMD5050) — набір 200 шт](/bom/zahlushky-neon-10-mm-smd5050-nabir-200-sht.md) — $11.99, купити
* [Заглушки 12 мм з герметиком — набір 50 шт](/bom/zahlushky-12-mm-z-hermetykom-nabir-50-sht.md) — $13.99, купити
* [Термоусадка з клеєм 3:1, набір 350 шт](/bom/termousadka-z-kleiem-3-1-nabir-350-sht.md) — $6, купити
* [Термоусадка з клеєм 3:1, набір 350 шт](/bom/termousadka-z-kleiem-3-1-nabir-350-sht.md) — $6, купити
