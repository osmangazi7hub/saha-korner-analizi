"""
04 - Analiz: saha genişliği kornerden gol ve xG üretimini etkiliyor mu?

Dönem: 2014-15 -> 2025-26 (Understat xG verisi bu yıldan başlıyor).
Saha ölçüsü bilinmeyen maçlar dışarıda bırakılır.

Tablo 1 - Genişliğe göre korner verimi (tüm takımlar birlikte)
  Her genişlik değeri için: korner sayısı, kornerden gol, 100 kornerde gol,
  korner başına xG, korner başına şut.

Tablo 2 - Takım bazında (deplasman maçları)
  Her takımın deplasmanda dar sahalarda (< 68 m) ve 68 m sahalarda korner verimi.
  Sadece deplasman: takımın kendi sahası hep aynı olduğu için karşılaştırma
  deplasmandaki farklı sahalar üzerinden yapılır.

Çıktılar:
  outputs/tablo1_genislige_gore.csv
  outputs/tablo2_takim_bazinda.csv

Çalıştırma:  python scripts/04_analiz.py
"""

from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parents[1]
CIKTI = KOK / "outputs"


def verim(df):
    """Bir grup satırdan korner verimi özetini hesaplar."""
    korner = df["corners"].sum()
    return pd.Series({
        "mac": df["match_key"].nunique(),
        "korner": int(korner),
        "kornerden_gol": int(df["corner_goals"].sum()),
        "100_kornerde_gol": 100 * df["corner_goals"].sum() / korner,
        "korner_basina_xg": df["corner_xg"].sum() / korner,
        "korner_basina_sut": df["corner_shots"].sum() / korner,
    })


def main():
    CIKTI.mkdir(exist_ok=True)
    t = pd.read_csv(KOK / "data" / "processed" / "takim_mac.csv")
    t = t[t["us_match_id"].notna() & (t["pitch_status"] == "resmi")]

    # --- Tablo 1: genişliğe göre ---
    t1 = t.groupby("width_m").apply(verim, include_groups=False)
    t1["stadyumlar"] = t.groupby("width_m")["stadium"].unique().apply(lambda s: ", ".join(sorted(s)))
    t1.to_csv(CIKTI / "tablo1_genislige_gore.csv")
    pd.set_option("display.width", 200, "display.max_colwidth", 60)
    print("TABLO 1 - Genişliğe göre korner verimi (2014-15 -> 2025-26)")
    print(t1.round(3).to_string())

    # --- Tablo 2: takım bazında, deplasman ---
    d = t[t["is_home"] == 0].copy()
    d["saha"] = d["width_m"].apply(lambda w: "dar (<68 m)" if w < 68 else "68 m")
    t2 = d.groupby(["team", "saha"]).apply(verim, include_groups=False).reset_index()
    t2.to_csv(CIKTI / "tablo2_takim_bazinda.csv", index=False)
    print("\nTABLO 2 - Takım bazında, deplasman (örnek: Arsenal)")
    print(t2[t2["team"] == "Arsenal"].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
