---
name: order-placed
description: Зафіксувати покупку — користувач щось замовив (каже "замовив X", "купили Y"). Додає запис в orders.json, оновлює BOM і задачі, перезбирає дашборд.
---

Користувач щойно щось замовив. Зроби облік:

1. Розпитай тільки те, чого нема в повідомленні: що саме (звір з `data/bom.json`),
   дата (за замовчуванням — сьогодні), продавець (за замовчуванням Amazon), лінк.
2. `data/orders.json`: новий запис `ORD-NNN` (наступний вільний номер), items —
   назви рядків BOM, `status: "ordered"`, `component` від items.
3. `deliver_to`: якщо `addresses.move_date` задана і сьогодні + typical_delivery_days
   + move_buffer_days ≥ move_date → `"sf"`, інакше `addresses.current`. Якщо
   move_date = null — попередь, що порадник не працює, і спитай куди слали.
4. Відповідні рядки `data/bom.json` → `status: "have"`.
5. Якщо є трек-номер — запиши в `data/private/private.json` (`tracking.ORD-NNN`),
   НЕ в публічні файли.
6. Додай запис у `data/project.json → log` ({date, kind: "Creation", text: "Замовлено …"}).
7. `cd site && python3 build.py` — перебудує сторінки і OKF-бандл `knowledge/`;
   перепублікувати артефакти «Головна» і «Операції» (ті самі file paths → ті самі URL).
8. Підсумуй: номер замовлення, куди їде, що розблокується після доставки.
