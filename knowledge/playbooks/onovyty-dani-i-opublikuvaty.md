---
type: "Playbook"
title: "Оновити дані й опублікувати"
description: "Єдиний цикл публікації: правка data/*.json → build.py → push (CI) → перепублікація артефактів."
tags: ["project"]
generated: { by: "process:site-build" }
verified: { by: "human:gumanist", at: "2026-07-28T00:00:00Z" }
---

# Цикл

1. Правиш **тільки** `data/*.json` (або `<comp>/data/*.json`). HTML у `dashboard/` і markdown у `knowledge/` — build-продукти, руками не правляться.
2. `cd site && python3 build.py` — перебудує сторінки **і** OKF-бандл `knowledge/`.
3. `git commit && git push` — CI перевикладе hero-armor.github.io за ~хвилину (Pages збирає `--docs` без приватних даних).
4. Артефакти claude.ai — перепублікувати ті самі file paths (URL не змінюються): головна, задачі, лабораторія, операції.

# Без клона

Правка `data/*.json` прямо на GitHub (Edit → commit у `main`) — CI сам перебудує сайт і `knowledge/` не зачепить (він регенерується при наступному локальному build). Артефакти-дзеркала оновляться при наступній локальній публікації.

# Приватне

Адреси і трек-номери — тільки `data/private/private.json` (gitignored; окрема репа `Hero-Armor/private`). Ніколи в публічні файли, артефакти чи commit messages.
