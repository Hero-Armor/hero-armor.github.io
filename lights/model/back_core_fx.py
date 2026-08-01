#!/usr/bin/env python3
"""Анімовані превʼю режимів ядра — фрагмент сторінки, а не картинка.

Про режими можна написати «пульс від центру» і «дихання», але словами не видно
різниці, а вона тут головна: від того, яка частка з 241 діода горить у середньому,
залежать ватти. Тому кожен режим показуємо живим — маленьке коло, у якому реально
крутиться той самий ефект, і поруч його частка світіння.

Чому canvas, а не CSS-анімація, як у подіумної стрічки: там превʼю — смужка, і
градієнт, що їде вбік, справді схожий на стрічку. Тут же плата — девʼять вкладених
кілець з різною кількістю діодів, і весь сенс картинки в тому, що зовнішнє кільце
вшестеро «дорожче» за внутрішнє. Намалювати це градієнтом не вийде, тому кожен
діод малюється окремою крапкою на своєму місці: радіус кільця виводиться з
кількості діодів у ньому (r = n × крок / 2π — правило записане в базі).

Числа в таблиці не вписані руками: частки світіння лежать у back_core.json
(effects), ватти рахує back_core.watts() — і разом з ними те, що ліміт струму в
прошивці ріже всі шість режимів до однієї цифри. Це і є висновок сторінки.

Пише site/templates/_back_core_fx.html — самодостатній фрагмент (свій <style> з
префіксом fx-, розмітка, свій <script>). Тільки stdlib.
"""

import json
import math
import re
from pathlib import Path

import back_core as bc

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "site" / "templates" / "_back_core_fx.html"

FX = bc.D["effects"]
MOD = bc.module()
WIN = bc.WIN

# Напис на кнопці живе в одному місці, бо його друкують двоє: розмітка (перший
# стан) і скрипт (після кліку). Розведеш — перекладач отримає два різні рядки і
# англійська кнопка почне міняти формулювання від натискання до натискання.
BTN_STOP = "зупинити перелив"
BTN_START = "запустити перелив"


def rows():
    """Режим за режимом: частка світіння → ватти без ліміту → ватти по факту.

    Ватти без ліміту рахуються двічі — на середній частці і на піковій. Пікові
    (peak_raw_w) стоять у таблиці поруч із середніми не для краси: у «пульсі» і
    в «промені по колу» середні ватти майже однакові, а піки вже помітно різні —
    і саме пік показує, наскільки далеко режим ліз би за стелю, якби її не було.

    Ліміт струму рахує не ця функція, а модель: watts() сама притискає картинку
    до стелі прошивки, рівно як це робить WLED на живому контролері."""
    full = MOD["diodes"] * MOD["w_diode"]
    out = []
    for e in FX["list"]:
        share = e["avg_pct"] / 100.0
        w = bc.watts(MOD, duty=share)
        out.append(dict(e, share=share, raw_w=full * share,
                        act_w=w["work_w"], capped=w["capped"],
                        peak_raw_w=full * e["peak_pct"] / 100.0))
    return out


def facts():
    """Числа, якими підписана таблиця — усі з моделі, жодного набраного руками.

    Одне число тут округлюється не «як гарніше», а ВГОРУ: need_a — це той ліміт
    струму, з якого режими нарешті починають різнитись ваттами. На сьогоднішній
    базі найощадніший просить 1.735 А; надрукуєш «1.7 А» — і читач виведе з
    підпису, що вже на 1.71 А різниця буде, а її там ще нема. Тому в текст іде
    need_a_up — округлення до сотих у БІЛЬШИЙ бік: підпис мусить лишатись
    правдивим саме на межі, а не поруч із нею."""
    w = bc.watts(MOD, duty=1.0)
    bus = bc.draw_from_bus(MOD, duty=1.0)
    rs = rows()
    lightest = min(rs, key=lambda r: r["raw_w"])
    need_a = lightest["raw_w"] / MOD["v"]
    return dict(
        diodes=MOD["diodes"], rings=len(MOD["rings_layout"]),
        pitch_mm=bc.pitch_mm(MOD), size_mm=MOD["size_mm"], v=MOD["v"],
        full_w=w["full_w"], cap_w=w["cap_w"],
        limit_a=bc.D["chosen"]["current_limit_a"],
        bus_w=bus["work_w"], wh=bus["wh_night"], night_h=bc.D["chosen"]["night_h"],
        threshold_pct=100.0 * w["cap_w"] / w["full_w"],
        need_a=need_a, need_a_up=math.ceil(need_a * 100.0) / 100.0,
        lightest=lightest["name"], lightest_peak_w=lightest["peak_raw_w"],
        core_duty_pct=100.0 * bc.D["chosen"]["duty_animation"],
    )


def geo():
    """Розкладка діодів для скрипта: самі кільця, крок і радіус модуля.

    Далі координати рахує вже браузер тим самим правилом, що й креслення —
    щоб превʼю і схема не розʼїхались, якщо колись зміниться модуль."""
    return dict(rings=MOD["rings_layout"], pitch_mm=bc.pitch_mm(MOD),
                r_mm=MOD["size_mm"] / 2.0, win_mm=WIN["size_mm"])


def js_modes():
    return [dict(key=e["key"], preview=e["preview"], period=e["period_s"],
                 palette=e["palette"]) for e in FX["list"]]


STYLE = """<style>
  /* Превʼю режимів ядра. Усе під префіксом fx- і всередині .fx-core-block,
     щоб не зачепити превʼю подіумної стрічки (.fx-track) на сусідній сторінці. */
  .fx-core-block { margin-top: .4rem; }
  .fx-core-sub { color: var(--ink-2); max-width: 66ch; margin: 0 0 .9rem; }
  .fx-core-bar { display: flex; align-items: center; gap: .6rem; margin: 0 0 .7rem;
                 flex-wrap: wrap; }
  .fx-core-btn {
    font-family: var(--mono, ui-monospace, Menlo, monospace); font-size: .74rem;
    padding: .35rem .7rem; background: var(--panel); color: var(--ink);
    border: 1px solid var(--line); border-radius: 4px; cursor: pointer;
    /* Кнопка стоїть у гнучкому рядку поруч із довгою підказкою — без цих двох
       рядків підказка стискає її, і напис «зупинити перелив» ламається навпіл
       на будь-якій ширині. Англійський («stop the shimmer») ще довший, тож
       кнопка не має ні тиснутись, ні переноситись усередині. */
    white-space: nowrap; flex: 0 0 auto;
  }
  .fx-core-btn:hover { border-color: var(--accent); }
  .fx-core-hint { font-size: .74rem; color: var(--ink-2); flex: 1 1 18rem; min-width: 0; }
  .fx-core-wrap { overflow-x: auto; background: var(--panel);
                  border: 1px solid var(--line); border-radius: 6px; }
  .fx-core-tbl { border-collapse: collapse; width: 100%; font-size: .84rem; }
  .fx-core-tbl th, .fx-core-tbl td {
    text-align: left; padding: .5rem .7rem; border-bottom: 1px solid var(--line);
    white-space: nowrap; }
  .fx-core-tbl th { font-family: var(--mono, ui-monospace, Menlo, monospace);
    font-size: .68rem; letter-spacing: .1em; text-transform: uppercase; color: var(--ink-2); }
  .fx-core-tbl tr:last-child td { border-bottom: 0; }
  .fx-core-tbl td.fx-core-num { font-family: var(--mono, ui-monospace, Menlo, monospace);
    font-variant-numeric: tabular-nums; }
  .fx-core-nm { font-weight: 650; }
  .fx-core-wled { font-family: var(--mono, ui-monospace, Menlo, monospace);
    font-size: .74em; color: var(--ink-2); margin-left: .4rem; }
  .fx-core-desc { display: block; font-size: .8em; color: var(--ink-2);
    white-space: normal; max-width: 34ch; }
  /* Колодязь вікна завжди темний — це ж непрозорий бік панелі, крізь який
     світять діоди; у світлій темі він теж має читатись як «вимкнене скло». */
  .fx-core-eye {
    display: block; width: 76px; height: 76px; border-radius: 50%;
    background: radial-gradient(circle at 50% 45%, #171a20, #0c0e12 70%);
    box-shadow: inset 0 1px 3px rgba(0,0,0,.7), 0 0 0 1px var(--line);
  }
  .fx-core-eye canvas { display: block; width: 100%; height: 100%; border-radius: 50%; }
  .fx-core-cap { font-size: .8rem; color: var(--ink-2); margin-top: .6rem; max-width: 82ch; }
  .fx-core-cut { color: var(--warn); }
  .fx-core-pick td { background: var(--good-bg); }
  .fx-core-pick td:first-child { box-shadow: inset 3px 0 0 var(--good); }
  /* Підпис під підсвіченим рядком. Квадратик повторює саму підсвітку (фон +
     смужка зліва) — щоб було видно, що абзац пояснює саме зелений рядок, а не
     висить сам по собі. Звʼязок кольором, а не словами «рядок вище». */
  .fx-core-picknote { display: flex; gap: .5rem; align-items: baseline; }
  .fx-core-swatch { flex: 0 0 auto; width: .72rem; height: .72rem; border-radius: 2px;
    background: var(--good-bg); box-shadow: inset 3px 0 0 var(--good), 0 0 0 1px var(--line); }
  @media (max-width: 600px) {
    .fx-core-eye { width: 58px; height: 58px; }
  }
</style>"""


SCRIPT = """<script>
(function () {
  "use strict";
  // Розкладка модуля і параметри режимів приїхали з lights/data/back_core.json —
  // тут вони тільки малюються.
  var GEO = %GEO%;
  var FX = %FX%;

  var block = document.querySelector(".fx-core-block");
  if (!block) return;
  var TWO = Math.PI * 2;
  var WHITE = [255, 255, 255];

  // Координати кожного діода. Радіус кільця виводиться з кількості діодів у ньому
  // (r = n * крок / 2pi): саме тому зовнішнє кільце на 60 діодів і дає Ø172 мм.
  var DOTS = (function () {
    var out = [], k, i, n, r, a;
    for (k = 0; k < GEO.rings.length; k++) {
      n = GEO.rings[k];
      r = n === 1 ? 0 : n * GEO.pitch_mm / TWO;
      for (i = 0; i < n; i++) {
        a = TWO * i / n + k * 0.21;
        out.push({ x: r * Math.cos(a), y: r * Math.sin(a),
                   rn: r / GEO.r_mm, ang: (a % TWO + TWO) % TWO,
                   ring: k, seed: (k * 7919 + i * 104729) % 1000 / 1000 });
      }
    }
    return out;
  })();

  // Кольори беремо зі змінних сторінки, щоб превʼю жило і в темній, і в світлій темі.
  var PAL = {};
  function readPalette() {
    var probe = document.createElement("span");
    probe.style.cssText = "position:absolute;visibility:hidden";
    block.appendChild(probe);
    ["signal", "accent", "ink-2"].forEach(function (name) {
      probe.style.color = "var(--" + name + ")";
      var m = /(\\d+)[^\\d]+(\\d+)[^\\d]+(\\d+)/.exec(getComputedStyle(probe).color);
      PAL[name] = m ? [+m[1], +m[2], +m[3]] : [200, 210, 230];
    });
    block.removeChild(probe);
    SPRITES = {};
  }

  function mix(a, b, k) {
    k = k < 0 ? 0 : k > 1 ? 1 : k;
    return [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];
  }
  function hue2rgb(h) {                       // h у долях кола
    // Обгортаємо через floor, а не через %: у JS -0.2 % 1 = -0.2, і відʼємний
    // відтінок ліз би за межі таблиці кольорів. Ловилось живцем у браузері.
    h = h - Math.floor(h);
    var i = Math.floor(h * 6) % 6, f = h * 6 - Math.floor(h * 6);
    var q = 1 - f, t = f;
    var c = [[1, t, 0], [q, 1, 0], [0, 1, t], [0, q, 1], [t, 0, 1], [1, 0, q]][i] || [1, 1, 1];
    return [60 + c[0] * 195, 60 + c[1] * 195, 60 + c[2] * 195];
  }

  // Крапка малюється готовим спрайтом-плямою: інакше 241 градієнт на кадр
  // на шести превʼю кладе слабкий телефон. Колір округлюємо, щоб спрайтів
  // було десятки, а не тисячі.
  var SPRITES = {};
  function sprite(c) {
    var r = Math.round(c[0] / 24) * 24, g = Math.round(c[1] / 24) * 24, b = Math.round(c[2] / 24) * 24;
    var key = r + "_" + g + "_" + b;
    if (SPRITES[key]) return SPRITES[key];
    var s = 32, cv = document.createElement("canvas");
    cv.width = cv.height = s;
    var ctx = cv.getContext("2d");
    var col = r + "," + g + "," + b;
    var grd = ctx.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
    grd.addColorStop(0, "rgba(" + col + ",1)");
    grd.addColorStop(0.2, "rgba(" + col + ",0.8)");
    grd.addColorStop(0.45, "rgba(" + col + ",0.25)");
    grd.addColorStop(1, "rgba(" + col + ",0)");
    ctx.fillStyle = grd;
    ctx.fillRect(0, 0, s, s);
    SPRITES[key] = cv;
    return cv;
  }

  // Яскравість окремого діода в конкретну мить. Це і є весь режим.
  var BRIGHT = {
    // Фронт іде з ядра на обід і зривається з краю; ядро тліє завжди.
    pulse: function (d, t, T) {
      var p = (t % T) / T, front = -0.15 + p * 1.35;
      var w = Math.exp(-Math.pow((d.rn - front) / 0.2, 2));
      return Math.min(1, w + 0.28 * Math.exp(-Math.pow(d.rn / 0.2, 2)));
    },
    // Не гасне жоден діод — гойдається сама яскравість.
    breathe: function (d, t, T) {
      return 0.08 + 0.92 * (0.5 - 0.5 * Math.cos(TWO * t / T));
    },
    // Сектор їде по колу, за ним тягнеться хвіст.
    sweep: function (d, t, T) {
      if (d.rn < 0.05) return 0.55;
      var beam = TWO * (t % T) / T;
      var back = (beam - d.ang + TWO) % TWO;
      var near = Math.min(back, TWO - back);
      return Math.min(1, 0.9 * Math.exp(-Math.pow(near / 0.28, 2)) + 0.55 * Math.exp(-back / 0.8));
    },
    // Кожен діод мерехтить сам по собі; ядро гарячіше за обід.
    fire: function (d, t, T) {
      var ph = d.seed * TWO, w = TWO / T;
      var n = 0.5 + 0.5 * Math.sin(t * w * 2.3 + ph);
      var m = 0.5 + 0.5 * Math.sin(t * w * 0.9 + ph * 2.7);
      return Math.max(0.05, (0.25 + 0.75 * n * m) * (1 - 0.3 * d.rn));
    },
    // Повна заливка, різниця тільки в кольорі кілець.
    rainbow: function () { return 0.95; },
    // Без анімації: горить усе і рівно.
    solid: function () { return 0.92; }
  };

  // Колір діода при цій яскравості. Яку палітру бере режим — сказано в базі
  // (effects[].palette), тут тільки правило: до чисто білого доходить лише те,
  // що світить на повну, решта лишається кольоровою.
  var COLOR = {
    signal: function (d, b) { return mix(PAL.signal, WHITE, Math.pow(b, 2.3)); },
    accent: function (d, b) { return mix(PAL.accent, WHITE, Math.pow(b, 2.4)); },
    rainbow: function (d, b, t, T) {
      return hue2rgb(((d.ring / GEO.rings.length) + t / T) % 1);
    },
    white: function () { return mix(PAL.signal, WHITE, 0.7); }
  };

  function setup(cv) {
    var box = cv.parentNode.getBoundingClientRect();
    var css = Math.max(40, Math.round(box.width));
    var dpr = Math.min(2, window.devicePixelRatio || 1);
    cv.width = cv.height = Math.round(css * dpr);
    cv._ctx = cv.getContext("2d");
    cv._css = css;
    cv._dpr = dpr;
    // Вікно ширше за плату — тому дрібка порожнього поля по колу лишається темною.
    cv._scale = (css / 2 - 2) / (GEO.win_mm / 2);
    cv._spr = Math.max(5, GEO.pitch_mm * cv._scale * 2.6);
  }

  function draw(cv, t) {
    var ctx = cv._ctx, c = cv._css / 2, s = cv._scale, sp = cv._spr;
    var mode = cv._mode, br = BRIGHT[mode.preview], cl = COLOR[mode.palette], T = mode.period;
    ctx.setTransform(cv._dpr, 0, 0, cv._dpr, 0, 0);
    ctx.clearRect(0, 0, cv._css, cv._css);

    // Спершу незапалені діоди — щоб було видно, що це плата з кілець, а не пляма.
    ctx.fillStyle = "rgba(" + PAL["ink-2"].join(",") + ",0.22)";
    var i, d, x, y;
    for (i = 0; i < DOTS.length; i++) {
      d = DOTS[i];
      ctx.beginPath();
      ctx.arc(c + d.x * s, c + d.y * s, Math.max(0.4, sp * 0.11), 0, TWO);
      ctx.fill();
    }

    ctx.globalCompositeOperation = "lighter";
    for (i = 0; i < DOTS.length; i++) {
      d = DOTS[i];
      var b = br(d, t, T);
      if (b <= 0.03) continue;
      ctx.globalAlpha = b > 1 ? 1 : b;
      x = c + d.x * s - sp / 2;
      y = c + d.y * s - sp / 2;
      ctx.drawImage(sprite(cl(d, b, t, T)), x, y, sp, sp);
    }
    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = "source-over";
  }

  var canvases = [].slice.call(block.querySelectorAll("canvas[data-fx]"));
  canvases.forEach(function (cv) {
    cv._mode = FX.filter(function (m) { return m.key === cv.getAttribute("data-fx"); })[0];
  });
  readPalette();
  canvases.forEach(setup);

  // Малюємо тільки те, що зараз на екрані, і не частіше ~30 кадрів на секунду:
  // шість кіл по 241 крапці не мають гріти телефон у кишені.
  var visible = canvases.slice();
  if (window.IntersectionObserver) {
    visible = [];
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var at = visible.indexOf(en.target);
        if (en.isIntersecting && at < 0) visible.push(en.target);
        if (!en.isIntersecting && at >= 0) visible.splice(at, 1);
      });
    }, { rootMargin: "120px" });
    canvases.forEach(function (cv) { io.observe(cv); });
  }

  var still = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var running = !still, t0 = performance.now(), last = -999, raf = 0;

  function tick(now) {
    if (now - last >= 32) {
      last = now;
      // Мітка часу від браузера буває трохи РАНІШЕ за нашу стартову (кадр міг
      // початись до того, як ми його замовили) — звідси відʼємний час і
      // покорчена перша картинка. Тому не пускаємо час нижче нуля.
      var t = Math.max(0, (now - t0) / 1000);
      for (var i = 0; i < visible.length; i++) draw(visible[i], t);
    }
    raf = requestAnimationFrame(tick);
  }
  // Перемалювати ВСІ превʼю одразу — і ті, що зараз поза екраном. Треба після
  // зміни розміру (полотно від зміни ширини стає чистим) і на паузі: інакше
  // кружечок лишається порожньою чорною дірою, поки не потрапить у поле зору.
  function paintAll() {
    var t = running ? Math.max(0, (performance.now() - t0) / 1000) : 0;
    canvases.forEach(function (cv) { draw(cv, running ? t : cv._mode.period * 0.62); });
  }

  var btn = document.getElementById("fx-core-toggle");
  function label() { btn.textContent = running ? %BTN_STOP% : %BTN_START%; }
  if (btn) {
    label();
    btn.addEventListener("click", function () {
      running = !running;
      label();
      if (running) { t0 = performance.now(); raf = requestAnimationFrame(tick); }
      else { cancelAnimationFrame(raf); raf = 0; paintAll(); }
    });
  }

  if (running) raf = requestAnimationFrame(tick);
  else paintAll();

  // Тема могла перемкнутись — перечитуємо кольори і перемальовуємо застиглий кадр.
  var repaint = function () { readPalette(); paintAll(); };
  if (window.matchMedia) {
    var mq = window.matchMedia("(prefers-color-scheme: dark)");
    (mq.addEventListener ? mq.addEventListener.bind(mq, "change") : mq.addListener.bind(mq))(repaint);
  }
  if (window.MutationObserver) {
    new MutationObserver(repaint).observe(document.documentElement,
      { attributes: true, attributeFilter: ["data-theme", "class"] });
  }

  var rt = 0;
  window.addEventListener("resize", function () {
    clearTimeout(rt);
    rt = setTimeout(function () { canvases.forEach(setup); paintAll(); }, 180);
  });
})();
</script>"""


# Та сама регулярка, якою site/i18n.py вибирає з <script> рядки на переклад.
# Копія тут навмисна: чужий файл ми не імпортуємо, але мусимо бачити скрипт
# його очима.
JS_LITERAL = re.compile(r"""(['"`])((?:\\.|(?!\1)[^\\])*)\1""")
CYR = re.compile("[Ѐ-ӿ]")


def script():
    """Скрипт фрагмента — і перевірка, що перекладач бачить у ньому тільки текст.

    Перекладач шукає в тілі скрипта рядкові літерали регуляркою і не знає, що
    таке коментар. Тому один ПРЯМИЙ апостроф у слові «відʼємний» усередині
    коментаря відкриває для нього літерал, який закривається наступним таким же
    апострофом через півскрипта, — і в памʼять перекладу їде блоб на 6 тисяч
    символів із живим кодом усередині. Англійська сторінка після цього
    лишається без превʼю. Ловилось саме так, тому перевірка тут, а не в голові:
    у скрипті мусять знаходитись рівно два українські рядки — обидва стани
    кнопки, і нічого більше."""
    js = (SCRIPT.replace("%GEO%", json.dumps(geo(), ensure_ascii=False))
                .replace("%FX%", json.dumps(js_modes(), ensure_ascii=False))
                .replace("%BTN_STOP%", json.dumps(BTN_STOP, ensure_ascii=False))
                .replace("%BTN_START%", json.dumps(BTN_START, ensure_ascii=False)))
    body = js[js.index(">") + 1:js.rindex("</script")]
    found = [m.group(2) for m in JS_LITERAL.finditer(body) if CYR.search(m.group(2))]
    if found != [BTN_STOP, BTN_START]:
        raise SystemExit(
            "back_core_fx: перекладач бачить у скрипті не ті рядки — "
            f"{[s[:40] for s in found]}. Найімовірніше, у коментар заліз прямий "
            "апостроф (') замість ʼ і склеїв половину коду в один «рядок».")
    return js


def html():
    f = facts()
    rs = rows()
    pick = FX.get("pick")

    body = []
    for r in rs:
        cls = ' class="fx-core-pick"' if r["key"] == pick else ""
        act = (f'<span class="fx-core-cut">{r["act_w"]:.1f}</span>' if r["capped"]
               else f'{r["act_w"]:.1f}')
        body.append(
            f'      <tr{cls}>\n'
            f'        <td><span class="fx-core-nm">{r["name"]}</span>'
            f'<span class="fx-core-wled">{r["wled_hint"]}</span>'
            f'<span class="fx-core-desc">{r["desc"]}</span></td>\n'
            f'        <td><span class="fx-core-eye">'
            f'<canvas data-fx="{r["key"]}" role="img" '
            f'aria-label="Превʼю режиму «{r["name"]}»: {r["desc"]}"></canvas>'
            f'</span></td>\n'
            f'        <td class="fx-core-num">{r["avg_pct"]}%</td>\n'
            f'        <td class="fx-core-num">{r["peak_pct"]}%</td>\n'
            f'        <td class="fx-core-num">{r["raw_w"]:.1f} / '
            f'{r["peak_raw_w"]:.1f} Вт</td>\n'
            f'        <td class="fx-core-num">{act} Вт</td>\n'
            f'      </tr>')

    cap = (
        f'Частка світіння — це скільки діодів у середньому горить і на скільки, у '
        f'перерахунку на суцільний білий (усього їх на платі {f["diodes"]}); '
        f'від неї й ватти: частка × '
        f'{f["full_w"]:.1f} Вт. Але ліміт струму в прошивці ({f["limit_a"]} А × {f["v"]:.0f} В '
        f'= {f["cap_w"]:.1f} Вт) ріже все, що вище {f["threshold_pct"]:.1f}%, — а під цією '
        f'межею не лишається жоден із шести. Тому по факту всі режими беруть однаково: '
        f'{f["cap_w"]:.1f} Вт з модуля, {f["bus_w"]:.1f} Вт із шини і {f["wh"]:.0f} Wh за '
        f'{f["night_h"]:.0f} годин ночі. Вибір режиму — це вибір картинки, а не споживання; '
        f'щоб різниця в ваттах узагалі зʼявилась, ліміт довелося б підняти щонайменше до '
        f'{f["need_a_up"]:.2f} А — стільки просить у середньому найощадніший '
        f'«{f["lightest"].lower()}», а на піку він і поготів тягне {f["lightest_peak_w"]:.1f} Вт. '
        f'У базі ядра на перелив закладено {f["core_duty_pct"]:.0f}% — але й ця частка '
        f'впирається в ту саму стелю, тому в нічному балансі світла ядро стоїть тими самими '
        f'{f["bus_w"]:.1f} Вт, хоч який режим ми зрештою виберемо.')

    # Чому підсвічено зелений рядок — має бути написано, а не матись на увазі.
    # Пояснення лежить у базі (effects._pick_note) поруч із самим вибором
    # (effects.pick), тож текст і підсвітка не можуть розʼїхатись.
    note = FX.get("_pick_note")
    pick_note = (f'  <p class="fx-core-cap fx-core-picknote">'
                 f'<span class="fx-core-swatch" aria-hidden="true"></span>'
                 f'{note}</p>') if note else None

    return "\n".join(p for p in [
        "<!-- Анімовані превʼю режимів ядра на спині.",
        "     Згенеровано lights/model/back_core_fx.py з lights/data/back_core.json —",
        "     руками не правити: числа і сама розкладка діодів приїжджають з бази.",
        "     Фрагмент самодостатній: свої стилі (префікс fx-core-), своя розмітка,",
        "     свій скрипт. Кольори тягне зі змінних сторінки, тож лягає і в темну тему. -->",
        STYLE,
        "",
        '<div class="fx-core-block">',
        f'  <p class="fx-core-sub">{FX["_note"]} '
        f'У превʼю крутиться той самий ефект на справжній розкладці модуля: '
        f'вкладених кілець — {f["rings"]}, діодів — {f["diodes"]}, '
        f'крок {f["pitch_mm"]:.1f} мм. Кожен кружечок тут окремий діод, '
        f'а не мальована пляма.</p>',
        '  <div class="fx-core-bar">',
        f'    <button type="button" id="fx-core-toggle" class="fx-core-btn">{BTN_STOP}</button>',
        f'    <span class="fx-core-hint">{FX["ledmap_note"]}</span>',
        '  </div>',
        '  <div class="fx-core-wrap">',
        '  <table class="fx-core-tbl">',
        '    <thead><tr><th>Режим</th><th>Превʼю</th><th>Світиться, середнє</th>'
        '<th>Світиться, пік</th><th>Без ліміту, сер. / пік</th><th>По факту</th></tr></thead>',
        '    <tbody>',
        "\n".join(body),
        '    </tbody>',
        '  </table>',
        '  </div>',
        pick_note,
        f'  <p class="fx-core-cap">{cap}</p>',
        f'  <p class="fx-core-cap">{FX["_measured_note"]} {FX["how_estimated"]}</p>',
        '</div>',
        "",
        script(),
        "",
    ] if p is not None)


def main():
    f = facts()
    print(f'{len(FX["list"])} режимів · діодів {f["diodes"]} на {f["rings"]} кільцях '
          f'· крок {f["pitch_mm"]:.1f} мм')
    for r in rows():
        mark = "ріже ліміт" if r["capped"] else "влазить у ліміт"
        print(f'  {r["name"]:22} {r["avg_pct"]:3}% сер. / {r["peak_pct"]:3}% пік  '
              f'{r["raw_w"]:5.1f} / {r["peak_raw_w"]:5.1f} Вт без ліміту → '
              f'{r["act_w"]:4.1f} Вт  ({mark})')
    print(f'стеля прошивки {f["cap_w"]:.1f} Вт = {f["threshold_pct"]:.1f}% модуля; '
          f'з шини {f["bus_w"]:.1f} Вт, за ніч {f["wh"]:.0f} Wh')
    print(f'режими розійшлись би у ваттах з ліміту {f["need_a_up"]:.2f} А '
          f'(найощадніший просить {f["need_a"]:.3f} А); '
          f'у базі ядра на перелив закладено {f["core_duty_pct"]:.0f}%')
    OUT.write_text(html())
    print(f"фрагмент: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
