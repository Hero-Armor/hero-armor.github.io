---
type: "Engineering Decision"
title: "Нічне мале навантаження станцію не присипляє"
description: "Була підозра, що станція вимкне 12-вольтовий вихід уночі, коли навантаження мале."
tags: ["solar"]
generated: { by: "process:site-build" }
decided_by: "ivan"
decision_zone: "електрика"
verified: { by: "human:ivan", at: "2026-07-27T00:00:00Z" }
---

Система: [Живлення](/systems/solar.md) · вирішив: **Іван** (електрика)

# Чому

Була підозра, що станція вимкне 12-вольтовий вихід уночі, коли навантаження мале. Мануали Delta 2 / 2 Max / Pro кажуть прямо: «After the 12V DC output power button is turned on, the product will not shut off automatically». Автовимкнення через 2 години стосується лише випадку, коли ВСІ виходи вимкнені й навантаження нема. Тобто ризику нема — але кнопку DC треба тримати увімкненою, і це варто внести в чек-лист збірки.
