"""
05 - Grafikler: 04_analiz.py tablolarını görselleştirir.

  outputs/grafik1_genislige_gore.png  Genişliğe göre 100 kornerde gol ve korner başına xG
  outputs/grafik2_takim_bazinda.png   Takımların deplasmanda dar sahalarda ve 68 m
                                      sahalarda korner başına xG'si

Çalıştırma:  python scripts/05_grafik.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parents[1]
CIKTI = KOK / "outputs"

# Renkler (renk körlüğüne uygun mavi-turuncu çifti)
MAVI, TURUNCU = "#2a78d6", "#eb6834"
YAZI, YAZI2, IZGARA, ZEMIN = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
MIN_DAR_KORNER = 100  # grafik 2'de gösterilecek takımlar için en az dar-saha korner sayısı

plt.rcParams.update({
    "figure.facecolor": ZEMIN, "axes.facecolor": ZEMIN, "axes.edgecolor": IZGARA,
    "axes.labelcolor": YAZI2, "xtick.color": YAZI2, "ytick.color": YAZI2,
    "text.color": YAZI, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
})


def baslik(fig, ana, alt):
    """Başlık ve alt başlığı grafiğin en üstüne, üst üste binmeden yazar."""
    fig.text(0.01, 0.985, ana, fontsize=13, fontweight="bold", va="top")
    fig.text(0.01, 0.95, alt, fontsize=9, color=YAZI2, va="top")


def grafik1():
    t = pd.read_csv(CIKTI / "tablo1_genislige_gore.csv")
    t["stadyum_kisa"] = t["stadyumlar"].apply(
        lambda s: "33 stadyum" if s.count(",") > 3 else s.replace(" (Britannia/bet365)", "")
        .replace("Stoke Stadium", "Stoke").replace(" (John Smith's)", "").replace(", ", "\n"))
    x = np.arange(len(t))
    etiketler = [f"{w:g} m\n{s}\n{int(k)} korner" for w, s, k in zip(t["width_m"], t["stadyum_kisa"], t["korner"])]
    renk = [MAVI if w == 68 else TURUNCU for w in t["width_m"]]

    fig, eksenler = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    # Üst: 100 kornerde gol (+ %95 güven aralığı: gol sayısı Poisson varsayımıyla)
    ax = eksenler[0]
    ga = 100 * 1.96 * np.sqrt(t["kornerden_gol"]) / t["korner"]
    ax.errorbar(x, t["100_kornerde_gol"], yerr=ga, fmt="none", ecolor=YAZI2, elinewidth=1, capsize=3)
    ax.scatter(x, t["100_kornerde_gol"], s=70, c=renk, zorder=3, edgecolors=ZEMIN, linewidths=2)
    ax.axhline(t.loc[t["width_m"] == 68, "100_kornerde_gol"].iloc[0], color=MAVI, lw=1, ls="--", zorder=1)
    ax.set_ylabel("100 kornerde gol")
    baslik(fig, "Saha genişliğine göre korner verimi (Premier Lig, 2014-15 → 2025-26)",
           "Dikey çizgiler %95 güven aralığı. Kesikli çizgi: 68 m sahaların ortalaması.")
    # Alt: korner başına xG
    ax = eksenler[1]
    ax.scatter(x, t["korner_basina_xg"], s=70, c=renk, zorder=3, edgecolors=ZEMIN, linewidths=2)
    ax.axhline(t.loc[t["width_m"] == 68, "korner_basina_xg"].iloc[0], color=MAVI, lw=1, ls="--", zorder=1)
    ax.set_ylabel("Korner başına xG")
    ax.set_xticks(x, etiketler, fontsize=8)
    for a in eksenler:
        a.grid(axis="y", color=IZGARA, lw=0.8)
        a.set_axisbelow(True)
        a.set_ylim(bottom=0)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(CIKTI / "grafik1_genislige_gore.png", dpi=150)
    plt.close(fig)


def grafik2():
    t = pd.read_csv(CIKTI / "tablo2_takim_bazinda.csv")
    p = t.pivot(index="team", columns="saha", values=["korner_basina_xg", "korner"])
    p = p[p[("korner", "dar (<68 m)")] >= MIN_DAR_KORNER]
    p["fark"] = p[("korner_basina_xg", "dar (<68 m)")] - p[("korner_basina_xg", "68 m")]
    p = p.sort_values("fark")
    y = np.arange(len(p))

    fig, ax = plt.subplots(figsize=(9, 6.5))
    genis = p[("korner_basina_xg", "68 m")]
    dar = p[("korner_basina_xg", "dar (<68 m)")]
    ax.hlines(y, np.minimum(genis, dar), np.maximum(genis, dar), color=IZGARA, lw=2, zorder=1)
    ax.scatter(genis, y, s=70, c=MAVI, label="68 m sahalar", zorder=3, edgecolors=ZEMIN, linewidths=2)
    ax.scatter(dar, y, s=70, c=TURUNCU, label="Dar sahalar (< 68 m)", zorder=3, edgecolors=ZEMIN, linewidths=2)
    ax.set_yticks(y, [f"{takim}  ({int(n)} dar-saha kornesi)" for takim, n in
                      zip(p.index, p[("korner", "dar (<68 m)")])])
    ax.set_xlabel("Korner başına xG (deplasman maçları)")
    baslik(fig, "Takımların dar ve 68 m sahalarda korner başına xG'si",
           f"Deplasman maçları, 2014-15 → 2025-26. Dar sahalarda en az {MIN_DAR_KORNER} korner kullanan takımlar.")
    ax.grid(axis="x", color=IZGARA, lw=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(CIKTI / "grafik2_takim_bazinda.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    grafik1()
    grafik2()
    print("Yazıldı: outputs/grafik1_genislige_gore.png, outputs/grafik2_takim_bazinda.png")
