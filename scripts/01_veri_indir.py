"""
01 - Veri indirme: ham veriyi data/raw/ klasörüne indirir. Ham veri bir kez
indirilir, sonra dokunulmaz (sonraki adımlar yalnızca okur).

1. Football-Data.co.uk: Premier Lig maç sonuçları ve korner sayıları
   2009-10 ... 2025-26  ->  data/raw/football_data/E0_0910.csv ...
   Önemli sütunlar: HomeTeam, AwayTeam, HC (ev sahibi korner), AC (deplasman korner)

2. Understat: şut verisi (xG ve "situation" etiketi; kornerden gelen şutlar = FromCorner)
   2014-15 ... 2025-26 (Understat 2014-15'ten başlıyor)
   - Sezon fikstürü ->  data/raw/understat/league_EPL_2014.json ...
   - Maç başına şutlar -> data/raw/understat/matches/<maç_id>.json.gz (sıkıştırılmış)

Script yarıda kesilirse yeniden çalıştırmak yeterli: inmiş dosyaları atlar.

Çalıştırma:  python scripts/01_veri_indir.py
"""

import gzip
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from takimlar import sezon_listesi

KOK = Path(__file__).resolve().parents[1]
FD_HAM = KOK / "data" / "raw" / "football_data"
US_HAM = KOK / "data" / "raw" / "understat"

# Understat verisini sayfanın kendi kullandığı JSON uçlarından alıyoruz
US_BASLIK = {"X-Requested-With": "XMLHttpRequest",
             "User-Agent": "saha-korner-analizi arastirma (github.com/osmangazi7hub/saha-korner-analizi)"}
BEKLEME = 0.4  # sunucuyu yormamak için istekler arası saniye (her iş parçacığında)
PARALEL = 4    # aynı anda en fazla 4 istek (nazik bir sınır)

# Her iş parçacığı kendi oturumunu tekrar kullanır (bağlantı her seferinde
# yeniden kurulmaz, bu da indirmeyi çok hızlandırır)
_yerel = threading.local()


def oturum():
    if not hasattr(_yerel, "s"):
        _yerel.s = requests.Session()
    return _yerel.s


def getir(url, basliklar=None):
    """Ağ hatalarında artan beklemeyle (2, 4, 8, 16 sn) en fazla 4 kez dener."""
    for deneme in range(4):
        try:
            r = oturum().get(url, headers=basliklar, timeout=60)
            r.raise_for_status()
            return r
        except requests.RequestException as hata:
            print(f"  hata ({deneme + 1}/4): {hata}")
            time.sleep(2 ** (deneme + 1))
    raise RuntimeError(f"İndirilemedi: {url}")


def football_data_indir():
    print("Football-Data indiriliyor...")
    FD_HAM.mkdir(parents=True, exist_ok=True)
    for sezon, kod in sezon_listesi(2009, 2025):
        hedef = FD_HAM / f"E0_{kod}.csv"
        if not hedef.exists():
            hedef.write_bytes(getir(f"https://www.football-data.co.uk/mmz4281/{kod}/E0.csv").content)
        print(f"  {sezon}: {hedef.name}")


def mac_indir(mac_id):
    """Tek maçın şut verisini indirip sıkıştırılmış olarak kaydeder."""
    hedef = US_HAM / "matches" / f"{mac_id}.json.gz"
    veri = getir(f"https://understat.com/getMatchData/{mac_id}", US_BASLIK).content
    json.loads(veri)  # bozuk yanıtı kaydetmemek için kontrol
    hedef.write_bytes(gzip.compress(veri))
    time.sleep(BEKLEME)


def understat_indir():
    print("Understat indiriliyor...")
    (US_HAM / "matches").mkdir(parents=True, exist_ok=True)
    toplam_yeni = 0
    for yil in range(2014, 2026):  # Understat sezonu başlangıç yılıyla adlandırır (2014 = 2014-15)
        lig_dosya = US_HAM / f"league_EPL_{yil}.json"
        if not lig_dosya.exists():
            lig_dosya.write_text(getir(f"https://understat.com/getLeagueData/EPL/{yil}", US_BASLIK).text,
                                 encoding="utf-8")
            time.sleep(BEKLEME)
        maclar = [m for m in json.loads(lig_dosya.read_text(encoding="utf-8"))["dates"] if m["isResult"]]

        eksik = [m["id"] for m in maclar if not (US_HAM / "matches" / f"{m['id']}.json.gz").exists()]
        with ThreadPoolExecutor(PARALEL) as havuz:
            list(havuz.map(mac_indir, eksik))
        yeni = len(eksik)
        toplam_yeni += yeni
        print(f"  {yil}-{str(yil + 1)[2:]}: {len(maclar)} oynanmış maç ({yeni} yeni indirildi)")
    print(f"Toplam yeni maç dosyası: {toplam_yeni}")


if __name__ == "__main__":
    football_data_indir()
    understat_indir()
