---
type: "Task"
title: "Вписати розділ Travel & Fuel у вкладку «Hero Armor — Purchase Audit» таблиці Марселя"
description: "ГОТОВО ДО ЗАПИСУ (13.08): структуру звірено з живою таблицею через доступ Івана. У вкладці «Hero Armor — Purchase Audit» розділи йдуть Lighting(9-23) → Cable(24"
tags: ["project"]
task_status: "todo"
generated: { by: "process:site-build" }
---

Статус: **до роботи** · система: [Проєкт](/project.md)

ГОТОВО ДО ЗАПИСУ (13.08): структуру звірено з живою таблицею через доступ Івана. У вкладці «Hero Armor — Purchase Audit» розділи йдуть Lighting(9-23) → Cable(24-26) → Audio(27-39) → Power(40-45) → Assembly & Consumables(46-54) → TOTAL KEPT(56). Travel & Fuel стає між рядком 54 і TOTAL KEPT: заголовок, три рядки (Shell 106.97 / One9 65.35 / Arco 155.30, Paid by Ivan, дата 09.08), підсумок 327.62. TOTAL KEPT стає 1242.03 замість 914.41. ⚠ Записати точково можна ТІЛЬКИ з ключем Івана (Sheets API): наш rclone ходить під спільним клієнтом rclone, де Sheets API вимкнений і ми його не ввімкнемо. Права доступу вже є — Марсель дав Івану редактора 13.08.
