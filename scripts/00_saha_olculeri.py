"""
00 - Saha ölçüleri: Premier League Handbook'tan (resmi el kitabı) sezon bazında
uzunluk ve genişlik çıkarır ve data/stadiums.csv dosyasını yazar.

Neden el kitabı?
  Premier League kuralı K.20 gereği her kulüp, sezon başlamadan önce sahasının
  ölçülerini lige "Form 8" ile kaydettirir. Lig bu değerleri her sezonun el
  kitabındaki kulüp sayfasında "Pitch Dimensions" satırında yayımlar.
  Kural K.22: sezon içinde ölçü ancak ligin yazılı izniyle değişebilir.

Nasıl çalışır?
  1. Her sezonun el kitabını indirir (data/raw/handbooks/, git'e girmez, büyük dosyalar).
  2. PDF'i metne çevirir (pdftotext, poppler-utils paketi gerekir).
  3. Her "Pitch Dimensions" bloğundaki değeri okur.
  4. Kulüp sayfaları el kitabında alfabetik sıradadır. O sezonun 20 kulübünü
     Football-Data'dan alıp alfabetik sıraya dizer ve blokları sırayla eşler.
  5. Çapraz kontrol: bloğun hemen önünde/arkasındaki kulüp web adresi,
     eşlenen kulübe ait mi? (ör. www.liverpoolfc.com -> Liverpool)
  6. Değer yoksa (boş, "TBC", "To be advised") ölçü BOŞ bırakılır ve işaretlenir.
     Hiçbir değer tahminle doldurulmaz.

Çalıştırma:  python scripts/00_saha_olculeri.py
"""

import csv
import io
import html
import re
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).parent))
from takimlar import FD_RESMI, WEB_IPUCU, STADYUM_NOTU, stadyum_bul, sezon_listesi

KOK = Path(__file__).resolve().parents[1]
HAM = KOK / "data" / "raw" / "handbooks"
FD_HAM = KOK / "data" / "raw" / "football_data"
CIKTI = KOK / "data" / "stadiums.csv"

ARSIV = "https://archive.org/download/2019-20-premier-league-handbooks/{} Premier League Handbook.pdf"

# Sezon -> el kitabı adresi. 2009-10 ... 2023-24: Internet Archive koleksiyonu.
KAYNAK = {sezon: ARSIV.format(sezon).replace(" ", "%20") for sezon, _ in sezon_listesi(2009, 2023)}
# 2024-25 ve 2025-26: Premier League'in kendi sitesi
KAYNAK["2024-25"] = ("https://resources.premierleague.pulselive.com/premierleague/document/2024/12/11/"
                     "e9aa1b9e-a7d5-4788-8afe-6e07b8a5f5fc/TM1603-PL_Handbook-and-Collateral-2024-25_11.12_DIGITAL.pdf")
KAYNAK["2025-26"] = ("https://resources.premierleague.pulselive.com/premierleague/document/2025/07/28/"
                     "379e2f04-d81f-4768-ab68-e45de43b9d4d/PL_Handbook_25-26_Digital_28.07.pdf")

BASLIK = {"User-Agent": "saha-korner-analizi arastirma (github.com/osmangazi7hub/saha-korner-analizi)"}
YARD = 0.9144  # 1 yard = 0.9144 metre


def indir(url, hedef):
    """Dosya yoksa indirir (ham veri bir kez indirilir, sonra dokunulmaz)."""
    if hedef.exists() and hedef.stat().st_size > 0:
        return
    hedef.parent.mkdir(parents=True, exist_ok=True)
    for deneme in range(4):
        try:
            r = requests.get(url, headers=BASLIK, timeout=600)
            r.raise_for_status()
            hedef.write_bytes(r.content)
            return
        except requests.RequestException as hata:
            print(f"  indirme hatası ({deneme + 1}/4): {hata}")
            time.sleep(2 ** (deneme + 1))
    raise RuntimeError(f"İndirilemedi: {url}")


def metne_cevir(dosya):
    """PDF ya da HTML el kitabını düz metne çevirir. Sayfalar '\\f' ile ayrılır."""
    txt = dosya.with_suffix(".txt")
    if not txt.exists():
        if dosya.suffix == ".pdf":
            subprocess.run(["pdftotext", "-raw", str(dosya), str(txt)], check=True)
        else:  # SEC HTML eki: etiketleri satır sonuna çevir
            t = dosya.read_text(encoding="utf-8", errors="ignore")
            t = html.unescape(re.sub(r"<[^>]+>", "\n", t))
            txt.write_text(re.sub(r"\n\s*\n+", "\n", t), encoding="utf-8")
    return txt.read_text(encoding="utf-8", errors="ignore")


def sezon_kulupleri(sezon, fd_kod):
    """O sezon ligde oynayan 20 kulübün resmi adları (Football-Data maç listesinden)."""
    dosya = FD_HAM / f"E0_{fd_kod}.csv"
    indir(f"https://www.football-data.co.uk/mmz4281/{fd_kod}/E0.csv", dosya)
    df = pd.read_csv(dosya, encoding="latin-1", usecols=["HomeTeam"]).dropna()
    return sorted({FD_RESMI[t] for t in df["HomeTeam"]})


def olcu_oku(metin):
    """Blok metninden (uzunluk, genişlik) metre olarak okur; yoksa (None, None)."""
    m = re.search(r"Length:?\s*([\d.]+)\s*(metres?|meters?|m\b|yards?|yds)?.*?"
                  r"Width:?\s*([\d.]+)\s*(metres?|meters?|m\b|yards?|yds)?", metin, re.I | re.S)
    if not m:
        return None, None, ""
    uzunluk, genislik = float(m.group(1)), float(m.group(3))
    birim = (m.group(2) or m.group(4) or "metres").lower()
    if birim.startswith(("yard", "yd")):
        return round(uzunluk * YARD, 2), round(genislik * YARD, 2), "yarddan çevrildi"
    return uzunluk, genislik, ""


def bloklari_bul(metin):
    """
    'Pitch Dimensions' başlıklı kulüp bloklarını bulur.
    Gerçek kulüp bloğu: başlıktan sonra en fazla 4 satır içinde 'Directors' gelir
    (kural metnindeki ya da içindekiler sayfasındaki geçişleri eler).
    """
    satirlar = metin.split("\n")
    # Her satırın sayfa numarası ('\f' sayfa ayırıcıdır)
    sayfa, sayfalar = 1, []
    for s in satirlar:
        sayfalar.append(sayfa)
        sayfa += s.count("\f")
    webler = [(i, s.lower()) for i, s in enumerate(satirlar)
              if re.search(r"www\.[a-z0-9.-]+\.(com|co\.uk|net|org|tv)", s, re.I)
              and "premierleague" not in s.lower()]

    bloklar = []
    for i, s in enumerate(satirlar):
        if not re.match(r"\s*\f?\s*Pitch Dimensions", s, re.I):
            continue
        govde = [re.sub(r"(?i).*Pitch Dimensions:?", "", s)]
        for j in range(i + 1, min(i + 6, len(satirlar))):
            if re.match(r"\s*\f?\s*Directors", satirlar[j]):
                ham = " ".join(x.strip() for x in govde if x.strip())
                once = [w for k, w in webler if k < i][-1:]
                sonra = [w for k, w in webler if k > i][:1]
                bloklar.append({"ham": ham, "sayfa": sayfalar[i], "web": " ".join(once + sonra)})
                break
            govde.append(satirlar[j])
    return bloklar


def main():
    satirlar = []
    for sezon, fd_kod in sezon_listesi(2009, 2025):
        url = KAYNAK[sezon]
        uzanti = ".htm" if url.endswith(".htm") else ".pdf"
        dosya = HAM / f"handbook_{sezon}{uzanti}"
        print(f"{sezon}: el kitabı hazırlanıyor...")
        indir(url, dosya)
        bloklar = bloklari_bul(metne_cevir(dosya))
        kulupler = sezon_kulupleri(sezon, fd_kod)
        if len(bloklar) != 20 or len(kulupler) != 20:
            raise RuntimeError(f"{sezon}: {len(bloklar)} blok, {len(kulupler)} kulüp; eşleme yapılamaz")

        for kulup, b in zip(kulupler, bloklar):
            uzunluk, genislik, cevrim = olcu_oku(b["ham"])
            web_uyumlu = bool(re.search(WEB_IPUCU[kulup], b["web"]))
            notlar = [n for n in (cevrim, STADYUM_NOTU.get((kulup, sezon), "")) if n]
            if uzunluk is None:
                notlar.append("El kitabında değer yok: '" + (b["ham"] or "boş") + "'")
            satirlar.append({
                "season": sezon,
                "club": kulup,
                "stadium": stadyum_bul(kulup, sezon),
                "length_m": uzunluk,
                "width_m": genislik,
                "status": "resmi" if uzunluk is not None else "eksik",
                "source": f"Premier League Handbook {sezon}",
                "source_url": url,
                "source_page": b["sayfa"] if uzanti == ".pdf" else "",
                "check": "sira+web_adresi" if web_uyumlu else "sadece_sira",
                "raw_text": b["ham"],
                "note": "; ".join(notlar),
            })

    df = pd.DataFrame(satirlar)
    df.to_csv(CIKTI, index=False, quoting=csv.QUOTE_MINIMAL)

    # --- Kısa özet ---
    print(f"\n{CIKTI.relative_to(KOK)} yazıldı: {len(df)} kulüp-sezon")
    print("Durum:", df["status"].value_counts().to_dict())
    print("Çapraz kontrol:", df["check"].value_counts().to_dict())
    print("\nGenişlik dağılımı (m):")
    print(df["width_m"].value_counts(dropna=False).sort_index().to_string())


if __name__ == "__main__":
    main()
