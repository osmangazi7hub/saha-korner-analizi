"""
03 - Birleştirme: analiz tablosunu kurar. Her satır "bir takımın bir maçtaki hücumu"
(her maç iki satır: ev sahibi hücumu ve deplasman hücumu).

Saha = ev sahibinin o sezonki stadyumu; ölçü data/stadiums.csv'den gelir.

Çıktı: data/processed/takim_mac.csv
  season, date, match_key, team, opponent, is_home
  venue_club, stadium, length_m, width_m, pitch_status
  corners            : takımın kullandığı korner sayısı (Football-Data)
  corners_against    : rakibin kullandığı korner sayısı
  goals, shots       : takımın golü ve şutu (Football-Data)
  -- 2014-15'ten itibaren (Understat) --
  corner_shots       : kornerden gelen şut sayısı
  corner_goals       : kornerden gelen gol sayısı (kendi kalesine goller hariç)
  corner_xg          : kornerden gelen şutların toplam xG'si
  openplay_xg        : oyun içi şutların toplam xG'si (takımın hücum gücü için kontrol)

Not: Understat'te "FromCorner" kornerden sonra gelen hücumdaki şutları kapsar
(ilk temas ve sonrasındaki kısa devam). Korner başına şut = corner_shots / corners.

Çalıştırma:  python scripts/03_birlestir.py
"""

import sys
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parents[1]
ISLENMIS = KOK / "data" / "processed"


def main():
    mac = pd.read_csv(ISLENMIS / "maclar.csv", parse_dates=["date"])
    sut = pd.read_csv(ISLENMIS / "sutlar.csv")
    saha = pd.read_csv(KOK / "data" / "stadiums.csv")
    mac["match_key"] = mac["season"] + "_" + mac["home"] + "_" + mac["away"]

    # --- Understat şutlarını maç + taraf düzeyinde topla ---
    sut = sut[sut["result"] != "OwnGoal"]  # kendi kalesine goller şut sayılmaz
    korner = sut[sut["situation"] == "FromCorner"]
    ozet = pd.concat([
        korner.groupby(["us_match_id", "side"]).size().rename("corner_shots"),
        korner[korner["result"] == "Goal"].groupby(["us_match_id", "side"]).size().rename("corner_goals"),
        korner.groupby(["us_match_id", "side"])["xg"].sum().rename("corner_xg"),
        sut[sut["situation"] == "OpenPlay"].groupby(["us_match_id", "side"])["xg"].sum().rename("openplay_xg"),
    ], axis=1).reset_index()

    # --- Her maçı iki satıra aç (ev sahibi hücumu + deplasman hücumu) ---
    satirlar = []
    for taraf, rakip in (("home", "away"), ("away", "home")):
        t = pd.DataFrame({
            "season": mac["season"], "date": mac["date"], "match_key": mac["match_key"],
            "us_match_id": mac["us_match_id"],
            "team": mac[taraf], "opponent": mac[rakip], "is_home": int(taraf == "home"),
            "venue_club": mac["home"],
            "corners": mac[f"{taraf}_corners"], "corners_against": mac[f"{rakip}_corners"],
            "goals": mac[f"{taraf}_goals"], "shots": mac[f"{taraf}_shots"],
            "side": taraf,
        })
        satirlar.append(t)
    tm = pd.concat(satirlar, ignore_index=True)

    # Understat değerlerini ekle; Understat'li maçta şut yoksa 0 (eksik değil)
    tm = tm.merge(ozet, on=["us_match_id", "side"], how="left")
    us_var = tm["us_match_id"].notna()
    for s in ["corner_shots", "corner_goals", "corner_xg", "openplay_xg"]:
        tm.loc[us_var, s] = tm.loc[us_var, s].fillna(0)

    # Saha ölçüsünü ekle (ev sahibinin o sezonki sahası)
    tm = tm.merge(saha[["season", "club", "stadium", "length_m", "width_m", "status"]]
                  .rename(columns={"club": "venue_club", "status": "pitch_status"}),
                  on=["season", "venue_club"], how="left", validate="many_to_one")
    assert tm["pitch_status"].notna().all(), "Saha bilgisi olmayan maç var"

    sutunlar = ["season", "date", "match_key", "us_match_id", "team", "opponent", "is_home",
                "venue_club", "stadium", "length_m", "width_m", "pitch_status",
                "corners", "corners_against", "goals", "shots",
                "corner_shots", "corner_goals", "corner_xg", "openplay_xg"]
    tm = tm[sutunlar].sort_values(["date", "match_key", "is_home"], ascending=[True, True, False])
    tm.to_csv(ISLENMIS / "takim_mac.csv", index=False)

    # --- Kısa özet ---
    print(f"takim_mac.csv: {len(tm)} satır ({len(tm) // 2} maç)")
    print(f"Saha ölçüsü olan: {(tm.pitch_status == 'resmi').sum()} satır, eksik: {(tm.pitch_status == 'eksik').sum()}")
    u = tm[tm["us_match_id"].notna()]
    print(f"Understat'li (2014-15+): {len(u)} satır")
    print(f"Korner başına şut: {u.corner_shots.sum() / u.corners.sum():.3f}, "
          f"gol: {u.corner_goals.sum() / u.corners.sum():.4f}, xG: {u.corner_xg.sum() / u.corners.sum():.4f}")


if __name__ == "__main__":
    main()
