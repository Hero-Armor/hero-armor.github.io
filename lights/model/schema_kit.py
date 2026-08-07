#!/usr/bin/env python3
"""
Конструктор електричних схем: блоки, порти, ортогональні дроти — і перевірка.

Навіщо він є
──────────────
Перші схеми малювались schemdraw-ом, і на них дроти обривались у повітря:
лінія від щита йшла вправо і просто закінчувалась, лампа висіла ні на чому,
підпис «12V» лежав поверх проводу. Іван спіймав це на аудіо (02.08) і повторно
на світлі (07.08): «щоб не було проводів як було зі звуком».

Тому тут дріт не можна намалювати «кудись». Дріт зʼєднує ДВА ПОРТИ двох блоків,
маршрут будується ортогонально, а `Sheet.verify()` перед записом файлу
перевіряє чотири речі:

  1. кожен сегмент строго горизонтальний або вертикальний;
  2. обидва кінці дроту лежать рівно на портах (нема обривів у повітря);
  3. до кожного оголошеного порту реально приходить дріт (нема «мертвих» пінів);
  4. дроти різних ланцюгів не перетинаються — а якщо перетин неминучий,
     він має бути оголошений явно як місток (`hop`), інакше verify падає.

Плюс перевірка, що підписи не лізуть на блоки: текст, який накрив чужий
прямокутник, читається як частина того блоку — саме так на старій схемі
«12V» опинилось посеред проводу.

Числа сюди не зашиваються: генератори схем беруть їх з lights_node_model
і з data/*.json, а kit лише малює.

Тільки stdlib.
"""

import xml.etree.ElementTree as ET

FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"

# спільна палітра всіх схем проєкту (podium_plan.py / panel_tree.py)
INK = "#24231d"
TXT2 = "#6b675c"
THIN = "#d8d5c9"
POS = "#b35b1e"          # плюсова лінія
NEG = "#4a4a44"          # мінусова лінія
DATA = "#3d6f96"         # лінія даних
G1 = "#b07c14"
G2 = "#3d6f96"
G3 = "#3d7a4f"
WARN = "#b23a2e"
BOX_BG = "#f5f4ef"
PANEL_BG = "#efeee7"

EPS = 0.6                # допуск співпадіння координат, px


class Port:
    __slots__ = ("x", "y", "side", "name", "block")

    def __init__(self, x, y, side, name, block):
        self.x, self.y, self.side, self.name, self.block = x, y, side, name, block

    def __repr__(self):
        return f"<{self.block.label}:{self.name} @{self.x:.0f},{self.y:.0f}>"


class Block:
    def __init__(self, sheet, x, y, w, h, label, sub=None, color=INK, bg=BOX_BG,
                 dash="", note=None):
        self.sheet, self.x, self.y, self.w, self.h = sheet, x, y, w, h
        self.label, self.sub, self.color, self.bg, self.dash = label, sub, color, bg, dash
        self.note = note
        self.ports = {}

    # ── порти ───────────────────────────────────────────────────────────
    def port(self, name, side, frac=0.5, label=None):
        """Порт на грані блоку. frac — частка вздовж грані (0..1)."""
        if side == "l":
            x, y = self.x, self.y + self.h * frac
        elif side == "r":
            x, y = self.x + self.w, self.y + self.h * frac
        elif side == "t":
            x, y = self.x + self.w * frac, self.y
        else:
            x, y = self.x + self.w * frac, self.y + self.h
        p = Port(x, y, side, name, self)
        self.ports[name] = p
        if label:
            self.sheet._port_labels.append((p, label))
        return p

    def center(self):
        return self.x + self.w / 2, self.y + self.h / 2


class Wire:
    def __init__(self, a, b, color, width, dash, label, hops):
        self.a, self.b, self.color, self.width = a, b, color, width
        self.dash, self.label, self.hops = dash, label, hops
        self.segments = []


class Sheet:
    def __init__(self, w, h, title, subtitle=None, lede=None):
        self.w, self.h = w, h
        self.title, self.subtitle, self.lede = title, subtitle, lede
        self.blocks, self.wires, self.texts = [], [], []
        self.foot = []
        self._port_labels = []
        self._free_marks = []

    # ── елементи ────────────────────────────────────────────────────────
    def block(self, x, y, w, h, label, sub=None, color=INK, bg=BOX_BG, dash="",
              note=None):
        b = Block(self, x, y, w, h, label, sub, color, bg, dash, note)
        self.blocks.append(b)
        return b

    def text(self, x, y, s, size=10, fill=TXT2, anchor="start", weight=None):
        self.texts.append((x, y, s, size, fill, anchor, weight))

    def footnote(self, s):
        self.foot.append(s)

    def mark(self, x, y, r=4, color=POS):
        self._free_marks.append((x, y, r, color))

    def wire(self, a, b, color=POS, width=2.0, dash="", label=None, hops=()):
        """Дріт від порту `a` до порту `b`. Маршрут ортогональний.

        `hops` — координати X або Y, де цей дріт свідомо перестрибує чужий:
        малюється дужка, і verify такий перетин пропускає.
        """
        wr = Wire(a, b, color, width, dash, label, tuple(hops))
        wr.segments = self._route(a, b)
        self.wires.append(wr)
        if label:
            # підпис дроту йде в загальний список текстів — тоді verify ловить,
            # якщо він ліг поверх блоку (стара граблина: «12V» посеред проводу)
            horiz = [g for g in wr.segments if abs(g[1] - g[3]) < EPS]
            g = max(horiz, key=lambda q: abs(q[2] - q[0])) if horiz else wr.segments[0]
            self.text((g[0] + g[2]) / 2, min(g[1], g[3]) - 10, label, 9, TXT2, "middle")
            wr.label = None
        return wr

    # ── маршрутизація ───────────────────────────────────────────────────
    @staticmethod
    def _pts_to_segs(pts):
        return [(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
                for i in range(len(pts) - 1)
                if not (abs(pts[i][0] - pts[i + 1][0]) < EPS
                        and abs(pts[i][1] - pts[i + 1][1]) < EPS)]

    def _route(self, a, b):
        """Г- або Z-подібний шлях, що виходить із порту «назовні» його грані."""
        out = {"l": (-1, 0), "r": (1, 0), "t": (0, -1), "b": (0, 1)}
        stub = 18
        ax, ay = a.x + out[a.side][0] * stub, a.y + out[a.side][1] * stub
        bx, by = b.x + out[b.side][0] * stub, b.y + out[b.side][1] * stub
        pts = [(a.x, a.y), (ax, ay)]
        if abs(ay - by) < EPS or abs(ax - bx) < EPS:
            pts += [(bx, by)]
        elif a.side in ("l", "r"):
            mid = (ax + bx) / 2 if b.side in ("l", "r") else bx
            pts += [(mid, ay), (mid, by)] if b.side in ("l", "r") else [(bx, ay)]
        else:
            mid = (ay + by) / 2 if b.side in ("t", "b") else by
            pts += [(ax, mid), (bx, mid)] if b.side in ("t", "b") else [(ax, by)]
        pts += [(bx, by), (b.x, b.y)]
        # прибрати дублікати підряд
        clean = [pts[0]]
        for p in pts[1:]:
            if abs(p[0] - clean[-1][0]) > EPS or abs(p[1] - clean[-1][1]) > EPS:
                clean.append(p)
        return self._pts_to_segs(clean)

    # ── перевірка ───────────────────────────────────────────────────────
    @staticmethod
    def _seg_cross(s1, s2):
        """Точка перетину горизонтального і вертикального сегментів або None."""
        def horiz(s):
            return abs(s[1] - s[3]) < EPS

        if horiz(s1) == horiz(s2):
            return None
        h, v = (s1, s2) if horiz(s1) else (s2, s1)
        x1, x2 = sorted((h[0], h[2]))
        y1, y2 = sorted((v[1], v[3]))
        if x1 - EPS <= v[0] <= x2 + EPS and y1 - EPS <= h[1] <= y2 + EPS:
            # дотик кінцями (спільний вузол) перетином не рахуємо
            ends = ((h[0], h[1]), (h[2], h[3]), (v[0], v[1]), (v[2], v[3]))
            pt = (v[0], h[1])
            if any(abs(e[0] - pt[0]) < EPS and abs(e[1] - pt[1]) < EPS for e in ends):
                return None
            return pt
        return None

    def verify(self):
        errs = []

        # 1. ортогональність
        for w in self.wires:
            for s in w.segments:
                if abs(s[0] - s[2]) > EPS and abs(s[1] - s[3]) > EPS:
                    errs.append(f"дріт {w.a}→{w.b}: сегмент не ортогональний {s}")

        # 2. кінці дротів сидять на портах
        for w in self.wires:
            if not w.segments:
                errs.append(f"дріт {w.a}→{w.b}: порожній маршрут")
                continue
            first, last = w.segments[0], w.segments[-1]
            if abs(first[0] - w.a.x) > EPS or abs(first[1] - w.a.y) > EPS:
                errs.append(f"дріт {w.a}→{w.b}: початок не на порту")
            if abs(last[2] - w.b.x) > EPS or abs(last[3] - w.b.y) > EPS:
                errs.append(f"дріт {w.a}→{w.b}: кінець висить у повітрі")

        # 3. кожен оголошений порт зайнятий
        used = set()
        for w in self.wires:
            used.add(id(w.a))
            used.add(id(w.b))
        for b in self.blocks:
            for name, p in b.ports.items():
                if id(p) not in used:
                    errs.append(f"порт {b.label}:{name} нікуди не підключений")

        # 4. перетини дротів
        for i, w1 in enumerate(self.wires):
            for w2 in self.wires[i + 1:]:
                for s1 in w1.segments:
                    for s2 in w2.segments:
                        pt = self._seg_cross(s1, s2)
                        if pt is None:
                            continue
                        declared = any(abs(hx - pt[0]) < 4 for hx in w1.hops) or \
                            any(abs(hx - pt[0]) < 4 for hx in w2.hops)
                        if not declared:
                            errs.append(
                                f"перетин дротів без містка у ({pt[0]:.0f},{pt[1]:.0f}): "
                                f"{w1.a.block.label}→{w1.b.block.label} × "
                                f"{w2.a.block.label}→{w2.b.block.label}")

        # 5. підписи не лізуть на чужі блоки
        for (x, y, s, size, fill, anchor, weight) in self.texts:
            wpx = len(s) * size * 0.52
            x0 = x - wpx / 2 if anchor == "middle" else (x - wpx if anchor == "end" else x)
            for b in self.blocks:
                if (x0 + wpx > b.x + 2 and x0 < b.x + b.w - 2
                        and y > b.y + 2 and y - size < b.y + b.h - 2):
                    errs.append(f"підпис «{s[:28]}» лежить поверх блоку «{b.label}»")
                    break
        return errs

    # ── рендер ──────────────────────────────────────────────────────────
    def _t(self, x, y, s, size=10, fill=TXT2, anchor="start", weight=None):
        extra = f' font-weight="{weight}"' if weight else ""
        s = (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        return (f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" '
                f'font-size="{size}" fill="{fill}"{extra}>{s}</text>')

    def svg(self):
        o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
             f'width="100%" font-family="{FONT}">']
        o.append(self._t(self.w // 2, 30, self.title, 15, INK, "middle", "bold"))
        if self.subtitle:
            o.append(self._t(self.w // 2, 52, self.subtitle, 11, TXT2, "middle"))
        if self.lede:
            o.append(self._t(self.w // 2, 72, self.lede, 11, G3, "middle", "bold"))

        # дроти — під блоками, щоб входи ховались за рамкою
        for w in self.wires:
            d = f' stroke-dasharray="{w.dash}"' if w.dash else ""
            for (x1, y1, x2, y2) in w.segments:
                o.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
                         f'stroke="{w.color}" stroke-width="{w.width}"{d}/>')
            for hx in w.hops:
                for (x1, y1, x2, y2) in w.segments:
                    if abs(y1 - y2) < EPS and min(x1, x2) < hx < max(x1, x2):
                        o.append(f'<path d="M{hx-6:.0f},{y1:.0f} q6,-9 12,0" fill="none" '
                                 f'stroke="{w.color}" stroke-width="{w.width}"/>')
            if w.label:
                mx = (w.segments[0][0] + w.segments[-1][2]) / 2
                my = min(s[1] for s in w.segments) - 8
                o.append(self._t(mx, my, w.label, 9, TXT2, "middle"))

        for b in self.blocks:
            d = f' stroke-dasharray="{b.dash}"' if b.dash else ""
            o.append(f'<rect x="{b.x:.0f}" y="{b.y:.0f}" width="{b.w:.0f}" '
                     f'height="{b.h:.0f}" rx="5" fill="{b.bg}" stroke="{b.color}" '
                     f'stroke-width="1.8"{d}/>')
            cx = b.x + b.w / 2
            ty = b.y + 22 if b.sub else b.y + b.h / 2 + 4
            o.append(self._t(cx, ty, b.label, 11, b.color, "middle", "bold"))
            if b.sub:
                for i, line in enumerate(b.sub.split("\n")):
                    o.append(self._t(cx, ty + 16 + i * 14, line, 9, TXT2, "middle"))

        for p, lab in self._port_labels:
            dx = {"l": -8, "r": 8, "t": 0, "b": 0}[p.side]
            dy = {"l": 3, "r": 3, "t": -6, "b": 12}[p.side]
            anc = {"l": "end", "r": "start", "t": "middle", "b": "middle"}[p.side]
            o.append(self._t(p.x + dx, p.y + dy, lab, 9, TXT2, anc))

        for (x, y, r, c) in self._free_marks:
            o.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{c}"/>')

        for (x, y, s, size, fill, anchor, weight) in self.texts:
            o.append(self._t(x, y, s, size, fill, anchor, weight))

        if self.foot:
            fy = self.h - 18 - 16 * (len(self.foot) - 1)
            o.append(f'<line x1="40" y1="{fy-22:.0f}" x2="{self.w-40}" y2="{fy-22:.0f}" '
                     f'stroke="{THIN}" stroke-width="1"/>')
            for i, line in enumerate(self.foot):
                o.append(self._t(40, fy + i * 16, line, 10, TXT2))

        o.append("</svg>")
        return "\n".join(o)

    def write(self, path, quiet=False):
        errs = self.verify()
        if errs:
            raise SystemExit("СХЕМА НЕ ПРОЙШЛА ПЕРЕВІРКУ:\n  · " + "\n  · ".join(errs))
        text = self.svg()
        ET.fromstring(text)                       # синтаксис SVG
        path.write_text(text, encoding="utf-8")
        if not quiet:
            print(f"SVG записано: {path} ({len(text.encode('utf-8'))/1024:.1f} KB) · "
                  f"блоків {len(self.blocks)} · дротів {len(self.wires)} · перевірка пройшла")
        return text
