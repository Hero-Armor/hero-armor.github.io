#!/usr/bin/env python3
"""Гардрейл перед публікацією: чи не порушено процес Hero Armor.

Принцип Івана: приватне = вся робота, публічне = тільки вирішене.
Цей скрипт ловить типові порушення ДО пушу в публічний репозиторій:

  1. секрети (токени, ключі) у застейджених файлах;
  2. приватні дані (адреси, трек-номери з data/private) у публічних файлах;
  3. build-продукти, правлені руками (dashboard/docs/knowledge замість data/);
  4. записи в data без системи (`system`) — осиротіють на сайті;
  5. картки систем, що посилаються на неіснуючі файли.

Запуск: python3 site/guard.py    (0 = чисто, 1 = є порушення)
Stdlib only — щоб CI і хуки працювали без залежностей.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
problems = []


def git(*args):
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args],
                              capture_output=True, text=True).stdout
    except Exception:
        return ""


# --- 1. секрети ------------------------------------------------------------
SECRET = re.compile(
    r"ghp_[A-Za-z0-9]{20,}|github_pat_|BEGIN [A-Z ]*PRIVATE KEY|"
    r"sk-ant-|AKIA[0-9A-Z]{16}|\d{8,10}:[\w-]{35}")
tracked = [l for l in git("ls-files").splitlines() if l]
SELF = "site/guard.py"  # у самому гардрейлі шаблони пошуку — це не секрети
for rel in tracked:
    if rel == SELF:
        continue
    f = ROOT / rel
    if not f.is_file() or f.stat().st_size > 2_000_000:
        continue
    try:
        txt = f.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    if SECRET.search(txt):
        problems.append(f"СЕКРЕТ у публічному файлі: {rel}")

# --- 2. приватні дані у публічному ----------------------------------------
priv_values = set()
for pf in (DATA / "private").glob("*.json"):
    if "example" in pf.name:
        continue
    try:
        def walk(x):
            if isinstance(x, dict):
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
            elif isinstance(x, str) and len(x) > 6:
                priv_values.add(x)
        walk(json.loads(pf.read_text()))
    except Exception:
        pass
if priv_values:
    for rel in tracked:
        if rel.startswith("data/private/"):
            continue
        f = ROOT / rel
        if not f.is_file():
            continue
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for v in priv_values:
            if v in txt:
                problems.append(f"ПРИВАТНЕ ({v[:18]}…) потрапило в {rel}")

# --- 3. build-продукти правлені руками ------------------------------------
staged = [l[3:] for l in git("status", "--porcelain").splitlines() if l]
hand = [p for p in staged
        if p.startswith(("dashboard/", "docs/", "knowledge/"))]
data_changed = any(p.startswith(("data/", "site/", "audio/", "lights/",
                                 "solar/", "armor/")) for p in staged)
if hand and not data_changed:
    problems.append(
        f"build-продукти змінені без правки джерела ({len(hand)} файлів) — "
        "правити треба data/*.json і перезбирати, не HTML/knowledge руками")

# --- 4. записи без системи -------------------------------------------------
try:
    keys = {c["key"] for c in json.loads((DATA / "systems.json").read_text())}
except Exception:
    keys = set()
# «project» — не система, а спільний тег для загальнопроєктних записів
keys |= {"project"}
for name in ("bom", "decisions", "tasks", "orders"):
    f = DATA / f"{name}.json"
    if not f.exists():
        continue
    try:
        items = json.loads(f.read_text())
    except Exception:
        problems.append(f"{name}.json — некоректний JSON")
        continue
    items = items if isinstance(items, list) else items.get(name, [])
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            continue
        s = it.get("system")
        if not s:
            problems.append(f"{name}.json[{i}] без системи — осиротіє на сайті")
        elif keys and s not in keys:
            problems.append(f"{name}.json[{i}] система «{s}» нема в systems.json")

# --- 5. картки систем із битими файлами ------------------------------------
try:
    for c in json.loads((DATA / "systems.json").read_text()):
        for fig in c.get("figures", []) or []:
            src = fig.get("src") if isinstance(fig, dict) else fig
            if src and not (ROOT / "site" / src.lstrip("/")).exists() \
                    and not (ROOT / src.lstrip("/")).exists():
                problems.append(f"система «{c['key']}»: нема файлу {src}")
except Exception:
    pass

# --- вердикт ---------------------------------------------------------------
if problems:
    print("ГАРДРЕЙЛ: знайдено порушення\n")
    for p in problems:
        print("  •", p)
    sys.exit(1)
print("гардрейл: чисто — секретів нема, приватне не тече, дані цілі")
