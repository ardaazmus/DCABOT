# F15.3c kanıt — Hedge Bot kart tasarımı (15.4 görsel kabul)

## Referans
Referans yok (DCABOT-native). `docs/wireframes/15_3c_hedge_bot.svg`
(kaba ölçü taslağı; piksel/renk kopyalanmadı).

## Yeni ekran
`evidence/F15.3c/hedge-cards.png` (gerçek uçlar: session f15shot3c,
A FULL 0.5 + B PARTIAL 0.3 → PARTIAL_HEDGE, 2 dolum).

## Dürüst fark notu
Durum şeridi (durum+session+dolum) + bağımsız formlu iki kart +
S/R "Kapalı" rozeti tamam. Ham state etiketi korunur (ONE_LEG_FILLED
gibi; çeviri değil, backend etiketi). Event time tek paylaşılan
alanda kalır (kart başına saat yok, saatten tahmin yok).

## Tasarım gerekçesi (Yönerge m.4)
SVG tek form + tablo öngörüyordu; bacak bağımsızlığı için karta
gömülü ayrı form + SegmentedControl (Yön/Durum) seçildi. Bacak
durumu FULL→AÇIK/PARTIAL→KISMİ/NONE→KAPALI rozetlenir; miktar
backend exact metnidir. S/R rozeti kapalıdır çünkü projeksiyonda
seviye verisi yoktur (uydurulmadı).
