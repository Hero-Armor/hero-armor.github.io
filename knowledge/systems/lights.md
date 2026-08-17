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
* [Нижнє світло по торцю подіуму лишається — сонячні садові скасовані](/decisions/nyzhnie-svitlo-po-tortsiu-podiumu-lyshaietsia-soniachni-sado.md)
* [Габаритні вогні на стійках прожекторів — скасовано](/decisions/habarytni-vohni-na-stiikakh-prozhektoriv-skasovano.md)
* [Окремі сторінки-калькулятори по типах світла](/decisions/okremi-storinky-kalkuliatory-po-typakh-svitla.md)
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
* [Звук і світло — два окремі кабелі від станції](/decisions/zvuk-i-svitlo-dva-okremi-kabeli-vid-stantsii.md)
* [Корпусів прожекторів лишаємо рівно 12 — надлишок повернути](/decisions/korpusiv-prozhektoriv-lyshaiemo-rivno-12-nadlyshok-povernuty.md)
* [Лампи на корпусі робота — паралельно від клемного вузла, не шлейфом](/decisions/lampy-na-korpusi-robota-paralelno-vid-klemnoho-vuzla-ne-shle.md)
* [Стрічка подіуму: усі вісім рукавів зводяться в центр, живлення одним кабелем](/decisions/strichka-podiumu-usi-visim-rukaviv-zvodiatsia-v-tsentr-zhyvl.md)
* [Кабель 12/2 перезамовляємо: у реєстрі стояв круглий Ancor за $208 замість плоского за $103](/decisions/kabel-12-2-perezamovliaiemo-u-reiestri-stoiav-kruhlyi-ancor-.md)
* [Магістраль станція → щит лишилась без кабелю: обидві бухти 8/2 у поверненні](/decisions/mahistral-stantsiia-shchyt-lyshylas-bez-kabeliu-obydvi-bukht.md)
* [Обрана стрічка не гнеться на коло: мінімальний радіус 80 мм](/decisions/obrana-strichka-ne-hnetsia-na-kolo-minimalnyi-radius-80-mm.md)
* [Індикаторні лампи корпусу — 12-вольтові з резистором усередині, живлення тільки паралельне](/decisions/indykatorni-lampy-korpusu-12-voltovi-z-rezystorom-useredyni-.md)
* [Кабель до подіуму НЕ закопуємо — ведемо поверхнею в гофрі й позначаємо](/decisions/kabel-do-podiumu-ne-zakopuiemo-vedemo-poverkhneiu-v-hofri-i-.md)
* [Джгут із фігури вниз — три кабелі, три розʼєми, отвір не менший за 25 мм](/decisions/dzhhut-iz-fihury-vnyz-try-kabeli-try-roziemy-otvir-ne-menshy.md)
* [Чим вмикати світло без людини — тижневий таймер з годинником, фотореле як додаток](/decisions/chym-vmykaty-svitlo-bez-liudyny-tyzhnevyi-taimer-z-hodynnyko.md)
* [Врізні вогні торця ставимо В ПЛАСТИКОВОМУ КОЖУСІ, отвір 3/4″](/decisions/vrizni-vohni-tortsia-stavymo-v-plastykovomu-kozhusi-otvir-3-.md)
* [Світло на спині — звичайна лампа MR16 12 В за надрукованою панеллю, без адресних кілець](/decisions/svitlo-na-spyni-zvychaina-lampa-mr16-12-v-za-nadrukovanoiu-p.md)
* [Коронки по алюмінію — тільки біметал M42 фірмових ліній, дешевий набір не беремо](/decisions/koronky-po-aliuminiiu-tilky-bimetal-m42-firmovykh-linii-desh.md)

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
* [Задати розводку 10 ламп на корпусі робота (шлейф чи зірка всередині броні)](/tasks/zadaty-rozvodku-10-lamp-na-korpusi-robota-shleif-chy-zirka-v.md) — готово
* [Описати перехід кабелю подіум → фігура (роз'єм чи глухий ввід)](/tasks/opysaty-perekhid-kabeliu-podium-fihura-roziem-chy-hlukhyi-vv.md) — готово
* [Перед оплатою кошика виставити кількість 1 на бухту 12/2 і 1 на лот 16/2](/tasks/pered-oplatoiu-koshyka-vystavyty-kilkist-1-na-bukhtu-12-2-i-.md) — до роботи
* [14/2 можна прибрати із закупівлі — лінія підживлення стрічки тягне 0.38 А](/tasks/14-2-mozhna-prybraty-iz-zakupivli-liniia-pidzhyvlennia-stric.md) — до роботи
* [Врізні вогні торця: отвір за кресленням 04.8 — 22 мм в алюмінієвій накладці (R11) і 50 мм у дереві за нею (R25). Наш Sunmerit просить 22.6 мм — на 0.4 мм більше. Вирішити: свердлимо 23 мм ступінчастим свердлом чи просимо Володимира поправити креслення](/tasks/vrizni-vohni-tortsia-otvir-za-kreslenniam-04-8-22-mm-v-alium.md) — в роботі
* [Аварійні габаритні вогні на стійки прожекторів (поз. N7 креслення 04.6): 8 шт, IP67, 3 Вт, бурштин/червоний, 10-30 В — у Володимира в специфікації є, у нашій закупівлі їх немає взагалі](/tasks/avariini-habarytni-vohni-na-stiiky-prozhektoriv-poz-n7-kresl.md) — до роботи
* [Свіжі креслення освітлення Володимира (липень 2026, рев. 3.1) всі на 24 В, а ми перейшли на шину 12 В (DEC-120, 08.08 — новіше). Звірити з ним, щоб він переклав специфікацію на 12 В або підтвердив, що це не критично](/tasks/svizhi-kreslennia-osvitlennia-volodymyra-lypen-2026-rev-3-1-.md) — до роботи
* [Світло в торець подіуму: Іван чекає відповідь по лазерній різці отворів. Якщо великі круглі отвори зробити не вийде — беремо накладні (ALFU бурштин $2/шт або Dream Lighting теплий білий $4.5/шт)](/tasks/svitlo-v-torets-podiumu-ivan-chekaie-vidpovid-po-lazernii-ri.md) — чекаємо
* [Ідентифікувати лампи MR16, що приїхали 10.08 (замовлення поза нашою базою). Якщо на коробці не Luxrite — перевибір: стенд 31.07 показав, що саме Luxrite не мерехтить на мінімумі під ШІМ-диммером, на інший бренд цей результат не переноситься, треба перетестувати перед монтажем](/tasks/identyfikuvaty-lampy-mr16-shcho-pryikhaly-10-08-zamovlennia-.md) — до роботи
* [Оформити повернення димера SUPERNIGHT/Lelukee B095M4JS31 на Amazon (замовлення 113-4638535-6465017 від 31.07, $15.49, набір з 2 шт) — забирає половину потужності](/tasks/oformyty-povernennia-dymera-supernight-lelukee-b095m4js31-na.md) — до роботи
* [Димер: рішення за Іваном. Найдешевше і без ризику — лишити перший Greenclick (він працює бездоганно) і прибрати його єдиний недолік: тонкі дроти обжати в наконечники і завести в клемну колодку за $5 у тій самій герметичній коробці. Якщо хочеться новий блок з рідними клемами — 12Vmonster B076MVT1CR, 30 А, метал, сертифікація ETL/cULus, ~$16, скарг на нагрів у відгуках нема](/tasks/dymer-rishennia-za-ivanom-naideshevshe-i-bez-ryzyku-lyshyty-.md) — чекаємо
* [⚠ Не купувати пробійник Greenlee 7/8", поки не зафіксований світильник: пробійник дає рівно 22.2 мм і розширити пробитий отвір неможливо, а наш Sunmerit просить 22.6. Ступінчасте свердло дає будь-який діаметр — поки світильник не обраний остаточно, беремо його](/tasks/ne-kupuvaty-probiinyk-greenlee-7-8-poky-ne-zafiksovanyi-svit.md) — до роботи
* [Скасувати на Amazon повернення двох прожекторів Gardencoin — лишаємо всі 10 (рішення Івана 13.08)](/tasks/skasuvaty-na-amazon-povernennia-dvokh-prozhektoriv-gardencoi.md) — до роботи
* [Вирішити, де ставити розʼєми фігура↔подіум: під настилом чи вище. Від цього довжина хвостів і місце отвору](/tasks/vyrishyty-de-stavyty-roziemy-fihura-podium-pid-nastylom-chy-.md) — чекаємо
* [Просвердлити отвір Ø25 мм під джгут фігури (пропускає кабельну половину LP-12 по одній)](/tasks/prosverdlyty-otvir-25-mm-pid-dzhhut-fihury-propuskaie-kabeln.md) — до роботи
* [Замовити розʼєм CNLINKO M12 4 контакти на живлення світла фігури ($10.13)](/tasks/zamovyty-roziem-cnlinko-m12-4-kontakty-na-zhyvlennia-svitla-.md) — до роботи
* [Замовити таймери на Amazon: 2× Heschen CN101A 12 В ($8.57) + 1× MISOL 25 А ($19.49), разом $36.63; фотореле ($11.93 eBay) — за бажанням](/tasks/zamovyty-taimery-na-amazon-2-heschen-cn101a-12-v-8-57-1-miso.md) — до роботи
* [Свердлити торець у зборі: спершу прикрутити алюмінієву накладку до дерева, потім проходити коронкою наскрізь — отвори будуть співвісні](/tasks/sverdlyty-torets-u-zbori-spershu-prykrutyty-aliuminiievu-nak.md) — до роботи
* [Іван дасть фінальне рішення по електриці фігури — звірити, що ще скасовується після переходу спини на лампу MR16](/tasks/ivan-dast-finalne-rishennia-po-elektrytsi-fihury-zviryty-shc.md) — чекаємо
* [Лампи Diodesy, замовлення 114-0792999-4940230 ($92.32): або відправити повернення до 06.09, або переоформити скаргу A-to-z до 14.09](/tasks/lampy-diodesy-zamovlennia-114-0792999-4940230-92-32-abo-vidp.md) — до роботи
* [Заміри є: корпус світильника 17.6 мм, конус 18.8 мм — 3/4″ підходить обом](/tasks/zamiry-ie-korpus-svitylnyka-17-6-mm-konus-18-8-mm-3-4-pidkho.md) — готово

# Закупівля

* [Gardencoin прожектор (корпус)](/bom/gardencoin-prozhektor-korpus.md) — $43/уп, купити
* [Luxrite MR16 4000K — лампа прожекторів](/bom/luxrite-mr16-4000k-lampa-prozhektoriv.md) — $96.34 за 12-пак, купити
* [Gebildet LED 12 мм, металеві](/bom/gebildet-led-12-mm-metalevi.md) — $10.99 за 5 шт (фактично DMWD), купити
* [Gebildet LED 8 мм, металеві](/bom/gebildet-led-8-mm-metalevi.md) — $8.99 за 5 шт (фактично DMWD), купити
* [Врізні вогні в торець подіуму, 0.6 Вт, IP68](/bom/vrizni-vohni-v-torets-podiumu-0-6-vt-ip68.md) — $37.99, купити
* [Неон WS2811 12 В силіконовий — дозамовити 2 рулони по 5 м](/bom/neon-ws2811-12-v-sylikonovyi-dozamovyty-2-rulony-po-5-m.md) — $27.99/рулон 16.4 ft — три рулони, $93 разом, купити
* [GLEDOPTO ESP32 WLED, IP65](/bom/gledopto-esp32-wled-ip65.md) — $23, купити
* [SUPERNIGHT ШІМ-диммер 12-24 В 30 А](/bom/supernight-shim-dymmer-12-24-v-30-a.md) — $13.99 за 2 шт, купити
* [Щит-бокс із тримачами запобіжників — Cyrico 12 Circuits](/bom/shchyt-boks-iz-trymachamy-zapobizhnykiv-cyrico-12-circuits.md) — $15.99, купити
* [Запобіжники ATO/ATC, набір](/bom/zapobizhnyky-ato-atc-nabir.md) — $9.99, купити
* [Реле на групи 12 В, 30 А](/bom/rele-na-hrupy-12-v-30-a.md) — $12.15, купити
* [Гермокоробка IP66 для щита і реле](/bom/hermokorobka-ip66-dlia-shchyta-i-rele.md) — $53.98, купити
* [Гермокоробки IP65 під диммер, WLED і аварійну Гр.3А](/bom/hermokorobky-ip65-pid-dymmer-wled-i-avariinu-hr-3a.md) — $8.99, купити
* [Гермороз'єми IP68 (швидкознімні)](/bom/hermoroziemy-ip68-shvydkoznimni.md) — $14.95, купити
* [Гель-конектори / вологозахищені клеми](/bom/hel-konektory-volohozakhyshcheni-klemy.md) — $9.99, купити
* [Гофра/кабель-канал для відводів](/bom/hofra-kabel-kanal-dlia-vidvodiv.md) — $30.99, купити
* [Кабель: Щит → коробка диммера (Гр.1)](/bom/kabel-shchyt-korobka-dymmera-hr-1.md) — $102.77, купити
* [Кабель: Диммер → кільце прожекторів](/bom/kabel-dymmer-kiltse-prozhektoriv.md) — $102.77, купити
* [Кабель: Відвід на прожектор (найдальший)](/bom/kabel-vidvid-na-prozhektor-naidalshyi.md) — $42.99, купити
* [Кабель: WLED → точки живлення стрічки](/bom/kabel-wled-tochky-zhyvlennia-strichky.md) — $33.99, купити
* [Кабель: Коробка → лампи робота](/bom/kabel-korobka-lampy-robota.md) — $11.26, купити
* [Кабель: Щит → коробка аварійної (Гр.3А)](/bom/kabel-shchyt-korobka-avariinoi-hr-3a.md) — $102.77, купити
* [Кабель: Коробка → врізні вогні торця](/bom/kabel-korobka-vrizni-vohni-tortsia.md) — $42.99, купити
* [Алюмінієвий U-профіль для LED у настил подіуму](/bom/aliuminiievyi-u-profil-dlia-led-u-nastyl-podiumu.md) — $37.99, купити
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
* [Кондуит liquid-tight 3/4" на магістраль (суцільний, не розрізний)](/bom/konduyt-liquid-tight-3-4-na-mahistral-sutsilnyi-ne-rozriznyi.md) — $28.99, купити
* [Свердло Форстнера 1" (25.4 мм) по дереву](/bom/sverdlo-forstnera-1-25-4-mm-po-derevu.md) — $~15, купити
* [Ступінчасте свердло 6-35 мм (дерево + алюміній)](/bom/stupinchaste-sverdlo-6-35-mm-derevo-aliuminii.md) — $~20, купити
* [Аварійний габаритний вогонь на стійку прожектора (поз. N7 креслення)](/bom/avariinyi-habarytnyi-vohon-na-stiiku-prozhektora-poz-n7-kres.md) — —, купити
* [Накладні вогні в торець подіуму — Dream Lighting, теплий білий (альтернатива врізним)](/bom/nakladni-vohni-v-torets-podiumu-dream-lighting-teplyi-bilyi-.md) — $~108, купити
* [Бокові маркери ALFU, накладні, 10 шт (варіант замість врізних)](/bom/bokovi-markery-alfu-nakladni-10-sht-variant-zamist-vriznykh.md) — $60 ($2/шт), купити
* [Rock light GZ5CG, чорний накладний, 2 шт у наборі](/bom/rock-light-gz5cg-chornyi-nakladnyi-2-sht-u-nabori.md) — $90 ($7.5/шт), купити
* [Sunlite MR16 6W 12V 4000K CRI90 (арт. 81120) — лампи прожекторів, друга партія](/bom/sunlite-mr16-6w-12v-4000k-cri90-art-81120-lampy-prozhektoriv.md) — —, купити
* [Кільцеві пили біметал 7/8" і 15/16" на спільний арбор (24 отвори під врізні вогні)](/bom/kiltsevi-pyly-bimetal-7-8-i-15-16-na-spilnyi-arbor-24-otvory.md) — $15-25, купити
* [Вирубний пробійник Klein 53819, 7/8" (заміна відсутньому Greenlee)](/bom/vyrubnyi-probiinyk-klein-53819-7-8-zamina-vidsutnomu-greenle.md) — $28.49, купити
* [Резистори 1/2 Вт, набір 25 номіналів — струмообмеження світлодіодів на корпусі](/bom/rezystory-1-2-vt-nabir-25-nominaliv-strumoobmezhennia-svitlo.md) — $12.12, купити
* [Розʼєм CNLINKO M12 4 контакти IP67 — живлення світла фігури](/bom/roziem-cnlinko-m12-4-kontakty-ip67-zhyvlennia-svitla-fihury.md) — $11.69, купити
* [Тижневий таймер DC 12 В з годинником і LCD (CN101), 16 А — вмикання світла за розкладом](/bom/tyzhnevyi-taimer-dc-12-v-z-hodynnykom-i-lcd-cn101-16-a-vmyka.md) — $11.89, купити
* [Фотореле DC 12-48 В, dusk-to-dawn - вмикання по темряві](/bom/fotorele-dc-12-48-v-dusk-to-dawn-vmykannia-po-temriavi.md) — $11.93, купити
* [Тижневий таймер DC 12 В Heschen CN101A, 16 А — вмикання світла за розкладом](/bom/tyzhnevyi-taimer-dc-12-v-heschen-cn101a-16-a-vmykannia-svitl.md) — $9.89 за шт ($19.78 за дві), купити
* [Таймер DC 12 В MISOL 25 А з LCD — потужний, як страховка](/bom/taimer-dc-12-v-misol-25-a-z-lcd-potuzhnyi-iak-strakhovka.md) — $22.49, є
* [Коронка Bosch HBT075 3/4″ біметал M42 — отвори під врізні вогні](/bom/koronka-bosch-hbt075-3-4-bimetal-m42-otvory-pid-vrizni-vohni.md) — $6.49 за шт ($12.98 за дві), купити
* [Ступеневе свердло 1/4″–3/4″ (Neiko 10184A) — точний діаметр по алюмінію](/bom/stupeneve-sverdlo-1-4-3-4-neiko-10184a-tochnyi-diametr-po-al.md) — $9.19, купити
* [Мастило для різання металу (cutting fluid) — обовʼязкове для алюмінію](/bom/mastylo-dlia-rizannia-metalu-cutting-fluid-oboviazkove-dlia-.md) — ~$10, купити
* [Набір біметалевих коронок M42, 3/4″–2″ — під світильники, розʼєми і кабельні проходи](/bom/nabir-bimetalevykh-koronok-m42-3-4-2-pid-svitylnyky-roziemy-.md) — $24-38 залежно від набору, купити
* [Стійки під плати самоклейні, нейлон — 100 шт (не свердлити коробку)](/bom/stiiky-pid-platy-samokleini-neilon-100-sht-ne-sverdlyty-koro.md) — $9.99, купити
* [Латунні стійки M3 з гвинтами і гайками, 320 шт — коли є монтажна панель](/bom/latunni-stiiky-m3-z-hvyntamy-i-haikamy-320-sht-koly-ie-monta.md) — $14.98, купити
* [Врізні вогні торця подіуму — 16 шт LED IP68 у захисному кожусі, 12 В 0.6 Вт](/bom/vrizni-vohni-tortsia-podiumu-16-sht-led-ip68-u-zakhysnomu-ko.md) — $52.49 за набір, купити
* [Коронка LENOX Speed Slot 3/4″ біметал з тримачем — запасна до Bosch](/bom/koronka-lenox-speed-slot-3-4-bimetal-z-trymachem-zapasna-do-.md) — $13.35, купити
* [Коронка VIKITON 3/4″ з тримачем — друга запасна](/bom/koronka-vikiton-3-4-z-trymachem-druha-zapasna.md) — $9.61, купити
* [Набір коронок KATA 18 предметів, 3/4″–2½″ — з розмірами 1″, 1⅛″ і 1¼″ під конус світильника](/bom/nabir-koronok-kata-18-predmetiv-3-4-2-z-rozmiramy-1-1-i-1-pi.md) — $35.99, купити
* [Коронка LENOX 1″ з тримачем (1772481) — отвір під джгут із фігури](/bom/koronka-lenox-1-z-trymachem-1772481-otvir-pid-dzhhut-iz-fihu.md) — $9.86, купити
* [Коронка 1″ VIKITON з тримачем — дешева заміна LENOX](/bom/koronka-1-vikiton-z-trymachem-desheva-zamina-lenox.md) — $8.79, купити
* [Коронка LENOX 1⅛″ з тримачем (1772483) — із запасом під гермоввід](/bom/koronka-lenox-1-z-trymachem-1772483-iz-zapasom-pid-hermovvid.md) — $14.79, купити
* [Коронка Bosch HBT100 1″ біметал M42 — робоча, під отвір джгута](/bom/koronka-bosch-hbt100-1-bimetal-m42-robocha-pid-otvir-dzhhuta.md) — $7.49, купити
* [Набір Milwaukee Hole Dozer 13 предметів (49-22-4025) — якщо потрібен саме набір](/bom/nabir-milwaukee-hole-dozer-13-predmetiv-49-22-4025-iakshcho-.md) — $89.00, купити
* [Мастило для різання алюмінію — Tap Magic Aluminum, 16 oz з носиком](/bom/mastylo-dlia-rizannia-aliuminiiu-tap-magic-aluminum-16-oz-z-.md) — $14.78, купити
* [Восковий олівець для різання — Champion BruteLube, 2 oz](/bom/voskovyi-olivets-dlia-rizannia-champion-brutelube-2-oz.md) — $11.56, купити
* [Набір коронок Bosch HSBIM9, 9 предметів — 6 коронок + ДВІ оправки + кейс](/bom/nabir-koronok-bosch-hsbim9-9-predmetiv-6-koronok-dvi-opravky.md) — $37.49, купити
