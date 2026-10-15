"""
02 - Temizleme: ham veriyi okur, takım adlarını tek bir standarda (el kitabındaki
resmi ad) çevirir, iki kaynaktaki maçları eşleştirir ve data/processed/ altına yazar.

Çıktılar:
  data/processed/maclar.csv  Football-Data maçları (17 sezon): tarih, takımlar,
                             skor, şut, korner + (2014-15'ten itibaren) Understat maç kimliği
  data/processed/sutlar.csv  Understat şutları (12 sezon): maç, takım, durum (situation), xG, sonuç

Kontroller (ekrana yazılır):
  - Her sezonda 380 maç var mı?
  - Understat maçlarının hepsi Football-Data'da bulunuyor mu? (sezon + ev + deplasman ile)
  - Eşleşen maçlarda tarih ve skor tutuyor mu?

Çalıştırma:  python scripts/02_temizle.py
"""

import glob
import gzip
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from takimlar import FD_RESMI, US_RESMI, sezon_listesi

KOK = Path(__file__).resolve().parents[1]
HAM = KOK / "data" / "raw"
ISLENMIS = KOK / "data" / "processed"


def football_data_oku():
    """17 sezonun maç dosyalarını tek tabloda toplar, gerekli sütunları seçer."""
    parcalar = []
    for sezon, kod in sezon_listesi(2009, 2025):
        d = pd.read_csv(HAM / "football_data" / f"E0_{kod}.csv", encoding="latin-1")
        d = d.dropna(subset=["HomeTeam"]).copy()
        d["season"] = sezon
        parcalar.append(d)
    d = pd.concat(parcalar, ignore_index=True)
    d = d.rename(columns={"Date": "date", "HomeTeam": "home", "AwayTeam": "away",
                          "FTHG": "home_goals", "FTAG": "away_goals",
                          "HS": "home_shots", "AS": "away_shots",
                          "HC": "home_corners", "AC": "away_corners"})
    d["date"] = pd.to_datetime(d["date"], dayfirst=True, format="mixed")  # tarih biçimi gün/ay/yıl
    d["home"] = d["home"].map(FD_RESMI)
    d["away"] = d["away"].map(FD_RESMI)
    sutunlar = ["season", "date", "home", "away", "home_goals", "away_goals",
                "home_shots", "away_shots", "home_corners", "away_corners"]
    return d[sutunlar]


def understat_oku():
    """Understat maç listesi ve tüm şutlar."""
    maclar, sutlar = [], []
    for f in sorted(glob.glob(str(HAM / "understat" / "league_EPL_*.json"))):
        for m in json.load(open(f, encoding="utf-8"))["dates"]:
            if not m["isResult"]:
                continue
            maclar.append({"us_match_id": int(m["id"]),
                           "us_date": pd.to_datetime(m["datetime"]).normalize(),
                           "home": US_RESMI.get(m["h"]["title"], m["h"]["title"]),
                           "away": US_RESMI.get(m["a"]["title"], m["a"]["title"]),
                           "us_home_goals": int(m["goals"]["h"]),
                           "us_away_goals": int(m["goals"]["a"])})
            veri = json.loads(gzip.decompress((HAM / "understat" / "matches" / f"{m['id']}.json.gz").read_bytes()))
            for taraf in ("h", "a"):
                for s in veri["shots"][taraf]:
                    sutlar.append({"us_match_id": int(m["id"]),
                                   "side": "home" if taraf == "h" else "away",
                                   "minute": int(s["minute"]),
                                   "situation": s["situation"],   # OpenPlay, FromCorner, SetPiece, DirectFreekick, Penalty
                                   "shot_type": s["shotType"],
                                   "result": s["result"],         # Goal, SavedShot, MissedShots, BlockedShot, ShotOnPost, OwnGoal
                                   "xg": float(s["xG"]),
                                   "x": float(s["X"]), "y": float(s["Y"])})
    return pd.DataFrame(maclar), pd.DataFrame(sutlar)


def main():
    ISLENMIS.mkdir(parents=True, exist_ok=True)
    fd = football_data_oku()
    assert fd["home"].notna().all() and fd["away"].notna().all(), "Eşlenmeyen takım adı var"
    print("Sezon başına maç sayısı:", fd.groupby("season").size().unique().tolist())

    us_mac, sut = understat_oku()
    # Sezon bilgisi: Football-Data'daki aynı ev-deplasman çifti ve yakın tarih ile
    fd["season_start"] = fd["season"].str[:4].astype(int)
    us_mac["season_start"] = us_mac["us_date"].apply(lambda t: t.year if t.month >= 7 else t.year - 1)
    # 2019-20 (COVID) sezonu Ağustos 2020'ye kadar sürdü; Temmuz-Ağustos 2020 maçlarını düzelt
    covid = (us_mac["us_date"] >= "2020-06-01") & (us_mac["us_date"] <= "2020-08-31")
    us_mac.loc[covid, "season_start"] = 2019

    birlesik = fd.merge(us_mac, on=["season_start", "home", "away"], how="left", validate="one_to_one")
    eslesen = birlesik["us_match_id"].notna()
    print(f"Understat maçı: {len(us_mac)}, Football-Data ile eşleşen: {eslesen.sum()}")

    e = birlesik[eslesen]
    tarih_farki = (e["date"] - e["us_date"]).dt.days.abs()
    skor_farki = (e["home_goals"] != e["us_home_goals"]) | (e["away_goals"] != e["us_away_goals"])
    print(f"Tarihi 1 günden fazla farklı maç: {(tarih_farki > 1).sum()}")
    print(f"Skoru farklı maç: {skor_farki.sum()}")
    if skor_farki.any():
        print(e.loc[skor_farki, ["season", "date", "home", "away", "home_goals", "away_goals",
                                 "us_home_goals", "us_away_goals"]].to_string())

    birlesik["us_match_id"] = birlesik["us_match_id"].astype("Int64")
    birlesik.drop(columns=["season_start", "us_date", "us_home_goals", "us_away_goals"]) \
        .to_csv(ISLENMIS / "maclar.csv", index=False)
    sut.to_csv(ISLENMIS / "sutlar.csv", index=False)
    print(f"\nYazıldı: maclar.csv ({len(birlesik)} maç), sutlar.csv ({len(sut)} şut)")
    print("Şut durumları:", sut["situation"].value_counts().to_dict())


if __name__ == "__main__":
    main()
