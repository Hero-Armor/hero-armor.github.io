#!/usr/bin/env python3
"""
Hero Armor audio node — signal-chain model.
Generates signal_chain.png with three panels:

  A. Gain staging: output power vs DAC digital level for TPA3116 gain settings,
     clipping onset at the 12V rail.
  B. Frequency response of each analog stage and the total chain,
     against the speech intelligibility band.
  C. Time domain: speech-shaped signal clean vs clipped at the rail.

Chain: PCM5102A (2.1 Vrms FS) -> input RC HPF -> TPA3116D2 (BTL, 12V) ->
       LC output filter (33uH + 0.68uF) -> 4 ohm driver in sealed chest box.
"""

import numpy as np
import matplotlib
matplotlib.rcParams["svg.fonttype"] = "none"
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---- electrical constants (з audio/data/params.json — руками не вписуємо) ----
import json as _json, pathlib as _pl
_P = _json.loads((_pl.Path(__file__).resolve().parents[1] / "data" / "params.json").read_text())
VCC = _P["rail_v"]
R_LOAD = _P["speaker"]["candidates"][_P["speaker"]["chosen"]]["ohms"]
V_CLIP_RMS = VCC / np.sqrt(2)        # BTL max sine ~8.49 Vrms -> 18 W
P_CLIP = V_CLIP_RMS**2 / R_LOAD
DAC_FS_VRMS = _P["dac_fs_vrms"]        # PCM5102A full scale
GAINS_DB = _P["gain_options"]          # TPA3116 gain select
SPEECH_CREST_DB = _P["crest_db"]       # typical speech crest factor

# ---- palette (dataviz reference, light mode) ----
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e8e7e3"
S1, S2, S3, S4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "text.color": INK, "axes.edgecolor": INK2,
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "font.size": 9, "axes.titlesize": 10.5, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False,
    "grid.color": GRID, "grid.linewidth": 0.8,
})

fig, (axA, axB, axC) = plt.subplots(1, 3, figsize=(15, 4.6))
fig.subplots_adjust(left=0.05, right=0.985, top=0.82, bottom=0.14, wspace=0.28)

# =============== A. gain staging ===============
dbfs = np.linspace(-30, 0, 400)
colors = [S1, S2, S3, S4]
clip_onsets = []
for g_db, c in zip(GAINS_DB, colors):
    g = 10 ** (g_db / 20)
    v = DAC_FS_VRMS * 10 ** (dbfs / 20) * g
    p = np.minimum(v, V_CLIP_RMS) ** 2 / R_LOAD
    axA.plot(dbfs, p, color=c, lw=2, label=f"gain {g_db} dB")
    onset = 20 * np.log10(V_CLIP_RMS / (DAC_FS_VRMS * g))
    clip_onsets.append(onset)
    axA.plot(onset, P_CLIP, "o", color=c, ms=5, zorder=5)

axA.axhline(P_CLIP, color=INK2, lw=1, ls=(0, (4, 3)))
axA.text(-0.5, P_CLIP + 0.6, f"кліпінг: {P_CLIP:.0f} Вт @ 12V/4Ω",
         fontsize=8, color=INK2, ha="right")
axA.set_title("A · Gain staging: де починається кліпінг")
axA.set_xlabel("Цифровий рівень DAC, dBFS")
axA.set_ylabel("Вихідна потужність, Вт")
axA.set_ylim(0, 22)
axA.grid(True, axis="y")
axA.legend(frameon=False, fontsize=8, loc="upper left")

# =============== B. frequency response ===============
f = np.logspace(np.log10(20), np.log10(40000), 600)
w = 2j * np.pi * f

def hp1(fc):                       # 1st-order high-pass (input RC)
    return (w / (2 * np.pi * fc)) / (1 + w / (2 * np.pi * fc))

def hp2(fc, q):                    # 2nd-order HP (sealed box)
    s = w / (2 * np.pi * fc)
    return s**2 / (s**2 + s / q + 1)

def lp2(fc, q):                    # 2nd-order LP (LC output filter)
    s = w / (2 * np.pi * fc)
    return 1 / (s**2 + s / q + 1)

# LC filter: 33uH + 0.68uF into 4 ohm
f_lc = 1 / (2 * np.pi * np.sqrt(33e-6 * 0.68e-6))
q_lc = R_LOAD * np.sqrt(0.68e-6 / 33e-6)
h_rc = hp1(160)                    # 100nF into 10k input
h_box = hp2(140, 0.9)              # 4" driver in sealed chest volume
h_lc = lp2(f_lc, q_lc)
h_tot = h_rc * h_box * h_lc

axB.axvspan(300, 3400, color=S3, alpha=0.10, lw=0)
axB.text(1000, 3.0, "мовний діапазон\n300–3400 Гц", ha="center",
         fontsize=8, color=INK2)
axB.semilogx(f, 20*np.log10(abs(h_rc)), color=S4, lw=1.6, label="RC HPF 160 Гц")
axB.semilogx(f, 20*np.log10(abs(h_box)), color=S2, lw=1.6, label="бокс у грудях (HP 140 Гц)")
axB.semilogx(f, 20*np.log10(abs(h_lc)), color=S3, lw=1.6, label=f"LC фільтр ампа ({f_lc/1000:.0f} кГц)")
axB.semilogx(f, 20*np.log10(abs(h_tot)), color=S1, lw=2.4, label="разом")
axB.set_title("B · АЧХ тракту: голос проходить без втрат")
axB.set_xlabel("Частота, Гц")
axB.set_ylabel("Підсилення, дБ")
axB.set_ylim(-30, 6)
axB.grid(True, which="both", alpha=0.6)
axB.legend(frameon=True, facecolor=SURFACE, edgecolor=GRID,
           fontsize=8, loc="lower right")

# =============== C. speech clipping, time domain ===============
rng = np.random.default_rng(7)
fs = 16000
n = int(0.35 * fs)
white = rng.standard_normal(n * 2)
spec = np.fft.rfft(white)
freqs = np.fft.rfftfreq(len(white), 1 / fs)
shape = np.where(freqs > 0, 1 / np.maximum(freqs, 120) ** 0.5, 0)   # ~speech tilt
shape *= abs(hp1(150).real[0] * 0 + 1)                              # keep simple
band = (freqs > 100) & (freqs < 4000)
spec = spec * shape * band
speech = np.fft.irfft(spec)[:n]
syll = 0.5 * (1 + np.sin(2 * np.pi * 4 * np.arange(n) / fs - 1.2))  # 4 Hz syllables
speech = speech * syll
speech /= np.sqrt(np.mean(speech**2))                               # rms = 1

t = np.arange(n) / fs * 1000
v_peak_clip = VCC                                                   # BTL peak swing
for avg_w, c, lab in [(14, S2, "перекручено (сер. 14 Вт)"),
                      (4, S1, "нормальна гучність (сер. 4 Вт)")]:
    v = speech * np.sqrt(avg_w * R_LOAD)
    vc = np.clip(v, -v_peak_clip, v_peak_clip)
    clipped_pct = 100 * np.mean(np.abs(v) > v_peak_clip)
    axC.plot(t, vc, color=c, lw=0.9,
             label=f"{lab} — кліп {clipped_pct:.1f}% семплів")

axC.axhline(v_peak_clip, color=INK2, lw=1, ls=(0, (4, 3)))
axC.axhline(-v_peak_clip, color=INK2, lw=1, ls=(0, (4, 3)))
axC.text(2, v_peak_clip + 0.7, "межа 12V рейки", fontsize=8, color=INK2)
axC.set_title("C · Мова у часі: запас по кресту 12 дБ")
axC.set_xlabel("Час, мс")
axC.set_ylabel("Напруга на динаміку, В")
axC.set_ylim(-16, 16)
axC.grid(True, axis="y")
axC.legend(frameon=True, facecolor=SURFACE, edgecolor=GRID,
           fontsize=8, loc="lower center")

fig.suptitle("Hero Armor · сигнальний тракт: DAC 2.1 Vrms → TPA3116D2 @12V → 4Ω",
             fontsize=12, fontweight="bold", x=0.05, ha="left")

out = str(__import__("pathlib").Path(__file__).resolve().parent / "signal_chain.png")
fig.savefig(out, dpi=170)
print("wrote", out)

# ---- console summary ----
print(f"\nClip power: {P_CLIP:.1f} W sine @ {VCC:.0f}V/4ohm (BTL)")
for g_db, onset in zip(GAINS_DB, clip_onsets):
    print(f"  gain {g_db} dB: DAC clips above {onset:6.1f} dBFS")
avg_at_clip = P_CLIP / 10 ** (SPEECH_CREST_DB / 10)
print(f"Speech at clip-limited peaks (crest {SPEECH_CREST_DB:.0f} dB): "
      f"average electrical power ≈ {avg_at_clip:.1f} W")
print(f"LC filter corner: {f_lc/1000:.1f} kHz, Q={q_lc:.2f} (flat in audio band)")
