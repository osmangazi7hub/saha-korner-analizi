"""
Takım adları ve stadyum bilgileri (tüm script'lerin ortak kullandığı sözlükler).

- FD_RESMI: Football-Data.co.uk'deki kısa adı -> Premier League el kitabındaki resmi ad
- WEB_IPUCU: El kitabında kulüp sayfasındaki web adresinde geçen parça (çapraz kontrol için)
- STADYUM: Kulübün hangi sezonlarda hangi stadyumda oynadığı
  (saha ÖLÇÜSÜ burada yok; ölçüler yalnızca el kitabından gelir)
"""

# Football-Data adı -> el kitabındaki resmi kulüp adı
FD_RESMI = {
    "Arsenal": "Arsenal",
    "Aston Villa": "Aston Villa",
    "Birmingham": "Birmingham City",
    "Blackburn": "Blackburn Rovers",
    "Blackpool": "Blackpool",
    "Bolton": "Bolton Wanderers",
    "Bournemouth": "AFC Bournemouth",
    "Brentford": "Brentford",
    "Brighton": "Brighton & Hove Albion",
    "Burnley": "Burnley",
    "Cardiff": "Cardiff City",
    "Chelsea": "Chelsea",
    "Crystal Palace": "Crystal Palace",
    "Everton": "Everton",
    "Fulham": "Fulham",
    "Huddersfield": "Huddersfield Town",
    "Hull": "Hull City",
    "Ipswich": "Ipswich Town",
    "Leeds": "Leeds United",
    "Leicester": "Leicester City",
    "Liverpool": "Liverpool",
    "Luton": "Luton Town",
    "Man City": "Manchester City",
    "Man United": "Manchester United",
    "Middlesbrough": "Middlesbrough",
    "Newcastle": "Newcastle United",
    "Norwich": "Norwich City",
    "Nott'm Forest": "Nottingham Forest",
    "Portsmouth": "Portsmouth",
    "QPR": "Queens Park Rangers",
    "Reading": "Reading",
    "Sheffield United": "Sheffield United",
    "Southampton": "Southampton",
    "Stoke": "Stoke City",
    "Sunderland": "Sunderland",
    "Swansea": "Swansea City",
    "Tottenham": "Tottenham Hotspur",
    "Watford": "Watford",
    "West Brom": "West Bromwich Albion",
    "West Ham": "West Ham United",
    "Wigan": "Wigan Athletic",
    "Wolves": "Wolverhampton Wanderers",
}

# El kitabındaki web adresinde aranacak parça (düzenli ifade)
WEB_IPUCU = {
    "AFC Bournemouth": "afcb",
    "Arsenal": "arsenal",
    "Aston Villa": "avfc",
    "Birmingham City": "bcfc|birmingham",
    "Blackburn Rovers": "rovers|blackburn",
    "Blackpool": "blackpool",
    "Bolton Wanderers": "bwfc|bolton",
    "Brentford": "brentford",
    "Brighton & Hove Albion": "brighton",
    "Burnley": "burnley",
    "Cardiff City": "cardiff",
    "Chelsea": "chelsea",
    "Crystal Palace": "cpfc",
    "Everton": "everton",
    "Fulham": "fulham",
    "Huddersfield Town": "htafc",
    "Hull City": "hull",
    "Ipswich Town": "itfc",
    "Leeds United": "leeds",
    "Leicester City": "lcfc",
    "Liverpool": "liverpool",
    "Luton Town": "luton",
    "Manchester City": "mancity|mcfc",
    "Manchester United": "manutd",
    "Middlesbrough": "mfc",
    "Newcastle United": "nufc|newcastle",
    "Norwich City": "canaries|norwich",
    "Nottingham Forest": "nottingham",
    "Portsmouth": "portsmouth|pompey",
    "Queens Park Rangers": "qpr",
    "Reading": "reading",
    "Sheffield United": "sufc",
    "Southampton": "saints|southampton",
    "Stoke City": "stoke",
    "Sunderland": "safc",
    "Swansea City": "swansea",
    "Tottenham Hotspur": "tottenham",
    "Watford": "watford",
    "West Bromwich Albion": "wba",
    "West Ham United": "whufc",
    "Wigan Athletic": "wigan|latics",
    "Wolverhampton Wanderers": "wolves",
}

# Stadyum adı. Değer ya düz metin (her sezon aynı) ya da
# [(ilk_sezon, son_sezon, stadyum), ...] listesi (taşınan kulüpler).
# Sezonlar "2009-10" biçiminde; karşılaştırma metin olarak yapılır.
STADYUM = {
    "AFC Bournemouth": "Vitality Stadium (Dean Court)",
    "Arsenal": "Emirates Stadium",
    "Aston Villa": "Villa Park",
    "Birmingham City": "St Andrew's",
    "Blackburn Rovers": "Ewood Park",
    "Blackpool": "Bloomfield Road",
    "Bolton Wanderers": "Bolton Stadium (Reebok)",
    "Brentford": "Brentford Community Stadium",
    "Brighton & Hove Albion": "Falmer Stadium (Amex)",
    "Burnley": "Turf Moor",
    "Cardiff City": "Cardiff City Stadium",
    "Chelsea": "Stamford Bridge",
    "Crystal Palace": "Selhurst Park",
    "Everton": [("2009-10", "2024-25", "Goodison Park"),
                ("2025-26", "2025-26", "Hill Dickinson Stadium")],
    "Fulham": "Craven Cottage",
    "Huddersfield Town": "Kirklees Stadium (John Smith's)",
    "Hull City": "Hull City Stadium (KCOM/MKM)",
    "Ipswich Town": "Portman Road",
    "Leeds United": "Elland Road",
    "Leicester City": "King Power Stadium",
    "Liverpool": "Anfield",
    "Luton Town": "Kenilworth Road",
    "Manchester City": "Etihad Stadium",
    "Manchester United": "Old Trafford",
    "Middlesbrough": "Riverside Stadium",
    "Newcastle United": "St James' Park",
    "Norwich City": "Carrow Road",
    "Nottingham Forest": "City Ground",
    "Portsmouth": "Fratton Park",
    "Queens Park Rangers": "Loftus Road",
    "Reading": "Madejski Stadium",
    "Sheffield United": "Bramall Lane",
    "Southampton": "St Mary's Stadium",
    "Stoke City": "Stoke Stadium (Britannia/bet365)",
    "Sunderland": "Stadium of Light",
    "Swansea City": "Liberty Stadium",
    "Tottenham Hotspur": [("2009-10", "2016-17", "White Hart Lane"),
                          ("2017-18", "2017-18", "Wembley Stadium"),
                          ("2018-19", "2018-19", "Wembley Stadium -> Tottenham Hotspur Stadium (3 Nisan 2019)"),
                          ("2019-20", "2025-26", "Tottenham Hotspur Stadium")],
    "Watford": "Vicarage Road",
    "West Bromwich Albion": "The Hawthorns",
    "West Ham United": [("2009-10", "2015-16", "Boleyn Ground (Upton Park)"),
                        ("2016-17", "2025-26", "London Stadium")],
    "Wigan Athletic": "DW Stadium",
    "Wolverhampton Wanderers": "Molineux",
}

# Stadyum değişikliği / dikkat gerektiren sezonlar için not
STADYUM_NOTU = {
    ("West Ham United", "2016-17"): "Stadyum değişti: Boleyn Ground -> London Stadium",
    ("Tottenham Hotspur", "2017-18"): "Geçici stadyum: Wembley (White Hart Lane yıkıldı)",
    ("Tottenham Hotspur", "2018-19"): "Sezon içi taşınma: 3 Nisan 2019'a kadar Wembley, sonra yeni stadyum; el kitabında tek ölçü var",
    ("Tottenham Hotspur", "2019-20"): "Yeni stadyumun ilk tam sezonu",
    ("Everton", "2025-26"): "Stadyum değişti: Goodison Park -> Hill Dickinson Stadium",
}


def stadyum_bul(kulup, sezon):
    """Kulübün o sezondaki stadyum adını döndürür."""
    deger = STADYUM[kulup]
    if isinstance(deger, str):
        return deger
    for ilk, son, ad in deger:
        if ilk <= sezon <= son:
            return ad
    raise ValueError(f"Stadyum bulunamadı: {kulup} {sezon}")


def sezon_listesi(ilk=2009, son=2025):
    """[('2009-10', '0910'), ...] biçiminde sezon adları ve Football-Data kodları."""
    return [(f"{y}-{str(y + 1)[2:]}", f"{str(y)[2:]}{str(y + 1)[2:]}") for y in range(ilk, son + 1)]
