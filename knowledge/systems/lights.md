---
type: "Component"
title: "Світло"
description: "Шина 12 В, три групи: прожектори заливки, декор («біжуча вода» + лампи робота) і аварійна лінія, яка тримається найдовше. Композитна ніч 715 Wh — дві третини з'"
resource: "https://hero-armor.github.io/lights.html"
tags: ["lights"]
system_status: "in-design"
generated: { by: "process:site-build" }
---

Шина 12 В, три групи: прожектори заливки, декор («біжуча вода» + лампи робота) і аварійна лінія, яка тримається найдовше. Композитна ніч 715 Wh — дві третини з'їдають декор і аварійка, не прожектори. Наявного кабелю вистачає на все: магістраль 7.6 м на Ancor 8/2 просідає 2%, найгірша ділянка — кільце прожекторів 12 м на 12/2, 3.5%. Докуповувати товщий AWG 6 не треба (закрито 29.07).

# Рішення

* [Пост контролю в щиті: видно вольти і ватти по кожній лінії, і є чим вимкнути](/decisions/post-kontroliu-v-shchyti-vydno-volty-i-vatty-po-kozhnii-lini.md)
* [Контрольні точки на кінцях ліній — щоб бачити просадку, а не рахувати її](/decisions/kontrolni-tochky-na-kintsiakh-linii-shchob-bachyty-prosadku-.md)
* [Металева рама і труби подіуму — заземлити на мінус системи](/decisions/metaleva-rama-i-truby-podiumu-zazemlyty-na-minus-systemy.md)
* [Буфер-конденсатор на вхід адресної стрічки — від пускового струму](/decisions/bufer-kondensator-na-vkhid-adresnoi-strichky-vid-puskovoho-s.md)
* [Геометрія зірки підтверджена кресленням Rev 2.1: коло R 346 мм (2.17 м), рукав 1.22 м](/decisions/heometriia-zirky-pidtverdzhena-kreslenniam-rev-2-1-kolo-r-34.md)
* [Запасний варіант Володимира — світло без стрічки і без нижніх вогнів](/decisions/zapasnyi-variant-volodymyra-svitlo-bez-strichky-i-bez-nyzhni.md)
* [На спині робота зʼявляється світне ядро — окремий модуль зі своїм контролером](/decisions/na-spyni-robota-ziavliaietsia-svitne-iadro-okremyi-modul-zi-.md)
* [Нижнє світло по торцю подіуму лишається — сонячні садові скасовані](/decisions/nyzhnie-svitlo-po-tortsiu-podiumu-lyshaietsia-soniachni-sado.md)
* [Габаритні вогні на стійках прожекторів — скасовано](/decisions/habarytni-vohni-na-stiikakh-prozhektoriv-skasovano.md)
* [Окремі сторінки-калькулятори по типах світла](/decisions/okremi-storinky-kalkuliatory-po-typakh-svitla.md)
* [Стрічка — це вісім рукавів, а не промені плюс окреме коло](/decisions/strichka-tse-visim-rukaviv-a-ne-promeni-plius-okreme-kolo.md)
* [Регулюємо прожектори ШІМ-диммером, а не заниженням напруги](/decisions/rehuliuiemo-prozhektory-shim-dymmerom-a-ne-zanyzhenniam-napr.md)
* [Переріз неону — 8 × 16 мм, заглушки беремо під цей розмір](/decisions/pereriz-neonu-8-16-mm-zahlushky-beremo-pid-tsei-rozmir.md)
* [Суцільна заливка стрічки заборонена; робочий режим — «Комета»](/decisions/sutsilna-zalyvka-strichky-zaboronena-robochyi-rezhym-kometa.md)
* [Прожектори зʼєднуємо по краю подіуму, а не через коробку в центрі](/decisions/prozhektory-ziednuiemo-po-kraiu-podiumu-a-ne-cherez-korobku-.md)
* [Лампа прожекторів — Luxrite MR16 4000K, вибір закрито](/decisions/lampa-prozhektoriv-luxrite-mr16-4000k-vybir-zakryto.md)
* [Адресну стрічку рахуємо по біжучому фронту, не по повній лінії](/decisions/adresnu-strichku-rakhuiemo-po-bizhuchomu-frontu-ne-po-povnii.md)
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
* [Обидва кабелі лишаються — ні 8/2, ні 12/2 не повертаємо [ЧАСТКОВО СКАСОВАНО 05.08]](/decisions/obydva-kabeli-lyshaiutsia-ni-8-2-ni-12-2-ne-povertaiemo-chas.md)
* [Корпусів прожекторів лишаємо рівно 12 — надлишок повернути](/decisions/korpusiv-prozhektoriv-lyshaiemo-rivno-12-nadlyshok-povernuty.md)
* [Лампи на корпусі робота — паралельно від клемного вузла, не шлейфом](/decisions/lampy-na-korpusi-robota-paralelno-vid-klemnoho-vuzla-ne-shle.md)
* [Стрічка подіуму: усі вісім рукавів зводяться в центр, живлення одним кабелем](/decisions/strichka-podiumu-usi-visim-rukaviv-zvodiatsia-v-tsentr-zhyvl.md)
* [Кабель 12/2 перезамовляємо: у реєстрі стояв круглий Ancor за $208 замість плоского за $103](/decisions/kabel-12-2-perezamovliaiemo-u-reiestri-stoiav-kruhlyi-ancor-.md)
* [Магістраль станція → щит лишилась без кабелю: обидві бухти 8/2 у поверненні](/decisions/mahistral-stantsiia-shchyt-lyshylas-bez-kabeliu-obydvi-bukht.md)
* [Обрана стрічка не гнеться на коло: мінімальний радіус 80 мм](/decisions/obrana-strichka-ne-hnetsia-na-kolo-minimalnyi-radius-80-mm.md)
* [Діоди на корпусі робота — 3-вольтові: резистор на кожен, підключення паралельно](/decisions/diody-na-korpusi-robota-3-voltovi-rezystor-na-kozhen-pidkliu.md)
* [Кабель до подіуму НЕ закопуємо — ведемо поверхнею в гофрі й позначаємо](/decisions/kabel-do-podiumu-ne-zakopuiemo-vedemo-poverkhneiu-v-hofri-i-.md)

# Задачі

* [Перевірити ватметри на малому струмі до виїзду](/tasks/pereviryty-vatmetry-na-malomu-strumi-do-vyizdu.md) — чекаємо
* [Вивести контрольні точки на кінцях трьох ліній під щуп](/tasks/vyvesty-kontrolni-tochky-na-kintsiakh-trokh-linii-pid-shchup.md) — чекаємо
* [Зібрати пост контролю в щиті: три ватметри груп, ватметр вводу, три тумблери](/tasks/zibraty-post-kontroliu-v-shchyti-try-vatmetry-hrup-vatmetr-v.md) — до роботи
* [Відповісти Володимиру пакетом: помітність, отвір під вогник, труба прожектора, канал під стрічку](/tasks/vidpovisty-volodymyru-paketom-pomitnist-otvir-pid-vohnyk-tru.md) — до роботи
* [Замовити врізні вогні в торець подіуму — 24 шт класу 0.6 Вт](/tasks/zamovyty-vrizni-vohni-v-torets-podiumu-24-sht-klasu-0-6-vt.md) — до роботи
* [Звірити з Володимиром посадковий отвір під обраний врізний вогник](/tasks/zviryty-z-volodymyrom-posadkovyi-otvir-pid-obranyi-vriznyi-v.md) — чекаємо
* [Заміряти ватметром реальне споживання врізного вогника](/tasks/zamiriaty-vatmetrom-realne-spozhyvannia-vriznoho-vohnyka.md) — чекаємо
* [Перевірити диммери SUPERNIGHT після приїзду: мерехтіння і нагрів](/tasks/pereviryty-dymmery-supernight-pislia-pryizdu-merekhtinnia-i-.md) — чекаємо
* [Замовити ШІМ-диммери SUPERNIGHT 30 А — набір 2 шт](/tasks/zamovyty-shim-dymmery-supernight-30-a-nabir-2-sht.md) — готово
* [Замовити Luxrite MR16 4000K — 10 шт у прожектори](/tasks/zamovyty-luxrite-mr16-4000k-10-sht-u-prozhektory.md) — до роботи
* [Звести бюджет світла: заявлені ~170–220 Вт LED проти панелі 100 Вт — перерахувати (сайт сам радить зменшити стрічки)](/tasks/zvesty-biudzhet-svitla-zaiavleni-170-220-vt-led-proty-paneli.md) — готово
* [Обрати і замовити неон WS2811 під 12 В](/tasks/obraty-i-zamovyty-neon-ws2811-pid-12-v.md) — готово
* [Стенд ламп прожектора: три лампи на заниженні напруги](/tasks/stend-lamp-prozhektora-try-lampy-na-zanyzhenni-napruhy.md) — готово
* [Вирішити: 12 В MR16 на шині 24 В через ШІМ чи step-down](/tasks/vyrishyty-12-v-mr16-na-shyni-24-v-cherez-shim-chy-step-down.md) — готово
* [Вирішити: врізні вогні торця в нашу лінію чи автономні сонячні](/tasks/vyrishyty-vrizni-vohni-tortsia-v-nashu-liniiu-chy-avtonomni-.md) — готово
* [Звірити статуси закупівлі світла з інвойсом](/tasks/zviryty-statusy-zakupivli-svitla-z-invoisom.md) — чекаємо
* [Докупити товщий кабель: AWG 6 магістраль, AWG 8 декор](/tasks/dokupyty-tovshchyi-kabel-awg-6-mahistral-awg-8-dekor.md) — готово
* [Заміряти реальні довжини траси після складання подіуму](/tasks/zamiriaty-realni-dovzhyny-trasy-pislia-skladannia-podiumu.md) — чекаємо
* [Запитати конструктора про зовнішній периметр подіуму](/tasks/zapytaty-konstruktora-pro-zovnishnii-perymetr-podiumu.md) — чекаємо
* [Marcel: заміряти трубу кріплення прожектора (діаметр, різьба)](/tasks/marcel-zamiriaty-trubu-kriplennia-prozhektora-diametr-rizba.md) — чекаємо
* [Відповісти Володимиру по просадці 12В — тест уже зроблено](/tasks/vidpovisty-volodymyru-po-prosadtsi-12v-test-uzhe-zrobleno.md) — чекаємо
* [Зміряти ватметром реальне споживання LED-стрічки (Вт/м)](/tasks/zmiriaty-vatmetrom-realne-spozhyvannia-led-strichky-vt-m.md) — готово
* [Дозамовити стрічку: 2 рулони по 5 м (треба 9.77 м, є 5 м)](/tasks/dozamovyty-strichku-2-rulony-po-5-m-treba-9-77-m-ie-5-m.md) — готово
* [Перевірити, на яку адресу йде стрічка (LA чи SF)](/tasks/pereviryty-na-iaku-adresu-ide-strichka-la-chy-sf.md) — до роботи
* [Написати Володимиру: коло лишається + цифри просадки](/tasks/napysaty-volodymyru-kolo-lyshaietsia-tsyfry-prosadky.md) — готово
* [Заміряти переріз стрічки, коли прийде (під заглушки)](/tasks/zamiriaty-pereriz-strichky-koly-pryide-pid-zahlushky.md) — готово
* [Обрати, чим вмикати прожектори і аварійну без фотореле](/tasks/obraty-chym-vmykaty-prozhektory-i-avariinu-bez-fotorele.md) — чекаємо
* [Замовити кошик дрібниці по світлу (заглушки + термоусадка) ≈ $84](/tasks/zamovyty-koshyk-dribnytsi-po-svitlu-zahlushky-termousadka-84.md) — до роботи
* [Виставити обмежувач струму в контролері стрічки (щоб суцільний білий не поклав 12 В-вихід)](/tasks/vystavyty-obmezhuvach-strumu-v-kontroleri-strichky-shchob-su.md) — до роботи
* [Реле на живлення стрічки — рвати на день](/tasks/rele-na-zhyvlennia-strichky-rvaty-na-den.md) — до роботи
* [Замовити ядро на спині: кільця 241 діод + контролер GLEDOPTO + понижувач 12→5 В](/tasks/zamovyty-iadro-na-spyni-kiltsia-241-diod-kontroler-gledopto-.md) — до роботи
* [Заміряти ватметром реальну частку світла ядра в переливі](/tasks/zamiriaty-vatmetrom-realnu-chastku-svitla-iadra-v-perelyvi.md) — чекаємо
* [Відновити посилання на неон WS2811 — старий лістинг Amazon знято](/tasks/vidnovyty-posylannia-na-neon-ws2811-staryi-listynh-amazon-zn.md) — до роботи
* [Заземлити металеву раму подіуму на мінус шини](/tasks/zazemlyty-metalevu-ramu-podiumu-na-minus-shyny.md) — чекаємо
* [Зняти справжні довжини кабельних трас із креслення (зараз прикидка)](/tasks/zniaty-spravzhni-dovzhyny-kabelnykh-tras-iz-kreslennia-zaraz.md) — до роботи
* [Дозамовити упаковку ламп 12 мм на адресу Марселя — не вистачає 5 шт](/tasks/dozamovyty-upakovku-lamp-12-mm-na-adresu-marselia-ne-vystach.md) — в роботі
* [Обрати кабель магістралі станція → щит під Anderson 30 А](/tasks/obraty-kabel-mahistrali-stantsiia-shchyt-pid-anderson-30-a.md) — до роботи
* [Звірити руками, скільки рулонів неону фізично лежить у Марселя](/tasks/zviryty-rukamy-skilky-ruloniv-neonu-fizychno-lezhyt-u-marsel.md) — до роботи
* [Обрати кабель на гілку Гр.2 замість поверненої бухти](/tasks/obraty-kabel-na-hilku-hr-2-zamist-povernenoi-bukhty.md) — до роботи
* [Задати топологію 24 врізних вогнів торця (зірка / шлейф / по гранях)](/tasks/zadaty-topolohiiu-24-vriznykh-vohniv-tortsia-zirka-shleif-po.md) — до роботи
* [Задати розводку 10 ламп на корпусі робота (шлейф чи зірка всередині броні)](/tasks/zadaty-rozvodku-10-lamp-na-korpusi-robota-shleif-chy-zirka-v.md) — до роботи
* [Описати перехід кабелю подіум → фігура (роз'єм чи глухий ввід)](/tasks/opysaty-perekhid-kabeliu-podium-fihura-roziem-chy-hlukhyi-vv.md) — до роботи
* [Перед оплатою кошика виставити кількість 1 на бухту 12/2 і 1 на лот 16/2](/tasks/pered-oplatoiu-koshyka-vystavyty-kilkist-1-na-bukhtu-12-2-i-.md) — до роботи
* [14/2 можна прибрати із закупівлі — лінія підживлення стрічки тягне 0.38 А](/tasks/14-2-mozhna-prybraty-iz-zakupivli-liniia-pidzhyvlennia-stric.md) — до роботи

# Закупівля

* [Gardencoin прожектор (корпус)](/bom/gardencoin-prozhektor-korpus.md) — $43/уп, купити
* [Luxrite MR16 4000K — лампа прожекторів](/bom/luxrite-mr16-4000k-lampa-prozhektoriv.md) — $96.34 за 12-пак, купити
* [Gebildet LED 12 мм, металеві](/bom/gebildet-led-12-mm-metalevi.md) — $10.99 за 5 шт (фактично DMWD), купити
* [Gebildet LED 8 мм, металеві](/bom/gebildet-led-8-mm-metalevi.md) — $8.99 за 5 шт (фактично DMWD), купити
* [Врізні вогні в торець подіуму, 0.6 Вт](/bom/vrizni-vohni-v-torets-podiumu-0-6-vt.md) — $55.99, купити
* [Неон WS2811 12 В силіконовий — дозамовити 2 рулони по 5 м](/bom/neon-ws2811-12-v-sylikonovyi-dozamovyty-2-rulony-po-5-m.md) — $27.99/рулон 16.4 ft — три рулони, $93 разом, купити
* [GLEDOPTO ESP32 WLED, IP65](/bom/gledopto-esp32-wled-ip65.md) — $23, купити
* [SUPERNIGHT ШІМ-диммер 12-24 В 30 А](/bom/supernight-shim-dymmer-12-24-v-30-a.md) — $13.99 за 2 шт, купити
* [Щит-бокс із тримачами запобіжників — Cyrico 12 Circuits](/bom/shchyt-boks-iz-trymachamy-zapobizhnykiv-cyrico-12-circuits.md) — $15.99, купити
* [Запобіжники ATO/ATC, набір](/bom/zapobizhnyky-ato-atc-nabir.md) — $9.99, купити
* [Реле на групи 12 В, 30 А](/bom/rele-na-hrupy-12-v-30-a.md) — $12.15, купити
* [Гермокоробка IP66 для щита і реле](/bom/hermokorobka-ip66-dlia-shchyta-i-rele.md) — $49.59, купити
* [Гермокоробки IP65 під диммер, WLED і аварійну Гр.3А](/bom/hermokorobky-ip65-pid-dymmer-wled-i-avariinu-hr-3a.md) — $8.99, купити
* [Гермороз'єми IP68 (швидкознімні)](/bom/hermoroziemy-ip68-shvydkoznimni.md) — $14.95, купити
* [Гель-конектори / вологозахищені клеми](/bom/hel-konektory-volohozakhyshcheni-klemy.md) — $9.99, купити
* [Гофра/кабель-канал для відводів](/bom/hofra-kabel-kanal-dlia-vidvodiv.md) — $30.99, купити
* [Кабель: Щит → коробка диммера (Гр.1)](/bom/kabel-shchyt-korobka-dymmera-hr-1.md) — $79.77, купити
* [Кабель: Диммер → кільце прожекторів](/bom/kabel-dymmer-kiltse-prozhektoriv.md) — $79.77, купити
* [Кабель: Відвід на прожектор (найдальший)](/bom/kabel-vidvid-na-prozhektor-naidalshyi.md) — $71.12, купити
* [Кабель: WLED → точки живлення стрічки](/bom/kabel-wled-tochky-zhyvlennia-strichky.md) — $33.99, купити
* [Кабель: Коробка → лампи робота](/bom/kabel-korobka-lampy-robota.md) — $11.26, купити
* [Кабель: Щит → коробка аварійної (Гр.3А)](/bom/kabel-shchyt-korobka-avariinoi-hr-3a.md) — $79.77, купити
* [Кабель: Коробка → врізні вогні торця](/bom/kabel-korobka-vrizni-vohni-tortsia.md) — $71.12, купити
* [Алюмінієвий U-профіль для LED у настил подіуму](/bom/aliuminiievyi-u-profil-dlia-led-u-nastyl-podiumu.md) — $29.39, купити
* [ASI 388 Electronic Grade Silicone, тюбик 2.8 oz](/bom/asi-388-electronic-grade-silicone-tiubyk-2-8-oz.md) — $10, купити
* [Заглушки неон 8×16 З ОТВОРОМ під дріт — набір 60 шт](/bom/zahlushky-neon-8-16-z-otvorom-pid-drit-nabir-60-sht.md) — $11.99, купити
* [Заглушки неон 8×16 ГЛУХІ (без отвору) — набір 60 шт](/bom/zahlushky-neon-8-16-hlukhi-bez-otvoru-nabir-60-sht.md) — $11.99, купити
* [Кліпси кріплення неону 8×16 з саморізами, 20 шт](/bom/klipsy-kriplennia-neonu-8-16-z-samorizamy-20-sht.md) — $13.19, купити
* [Дріт 3-жильний 22AWG, 20 м — перемички між рукавами](/bom/drit-3-zhylnyi-22awg-20-m-peremychky-mizh-rukavamy.md) — $12.58, купити
* [Термоусадка з клеєм 3:1, набір 350 шт](/bom/termousadka-z-kleiem-3-1-nabir-350-sht.md) — $6, купити
* [Таймер-реле 12 В — чим рвати живлення стрічки на день](/bom/taimer-rele-12-v-chym-rvaty-zhyvlennia-strichky-na-den.md) — $13.49, купити
* [Підсилювач сигналу SP901E (WS2811/WS2812)](/bom/pidsyliuvach-syhnalu-sp901e-ws2811-ws2812.md) — $19.99, купити
* [Набір кілець WS2812B 241 діод — ядро на спині](/bom/nabir-kilets-ws2812b-241-diod-iadro-na-spyni.md) — $25.99, купити
* [GLEDOPTO ESP32 Mini WLED 5-24 В — контролер ядра](/bom/gledopto-esp32-mini-wled-5-24-v-kontroler-iadra.md) — $19.07, купити
* [Понижувач 12 В → 5 В, 10 А (2 шт) — під ядро на спині](/bom/ponyzhuvach-12-v-5-v-10-a-2-sht-pid-iadro-na-spyni.md) — $14.99, купити
* [Ватметр Гр.1+Гр.2+Гр.3А — DROK DC 4.5–100 В / 0–50 А, LED-дисплей з шунтом](/bom/vatmetr-hr-1-hr-2-hr-3a-drok-dc-4-5-100-v-0-50-a-led-dysplei.md) — $15.49, купити
* [Ватметр ВВОДУ — CGELE DC 0–200 В / 0–100 А, LCD 9 параметрів з шунтом](/bom/vatmetr-vvodu-cgele-dc-0-200-v-0-100-a-lcd-9-parametriv-z-sh.md) — $18.59, купити
* [Тумблери підсвічені — DaierTek 12 В 20 А IP65, 5-pack](/bom/tumblery-pidsvicheni-daiertek-12-v-20-a-ip65-5-pack.md) — $8.99, купити
* [Кліщі DC/AC — allsun Hall Effect 400 А, True RMS, авторанг](/bom/klishchi-dc-ac-allsun-hall-effect-400-a-true-rms-avtoranh.md) — $33.99, купити
* [DMWD 12мм LED — дозамовити 1 упаковку](/bom/dmwd-12mm-led-dozamovyty-1-upakovku.md) — $10.99, купити
* [Шини розподільчі 150 А — Avelis, 2 шт в наборі](/bom/shyny-rozpodilchi-150-a-avelis-2-sht-v-nabori.md) — $11.99 за набір, купити
* [Гофра 3/4" на магістраль (розрізний лум)](/bom/hofra-3-4-na-mahistral-rozriznyi-lum.md) — $~13, купити
