# F15.6 kanıt — Bot başlatma koşulu akışı (15.4 görsel kabul)

## Referans
`docs/referans_ekranlar/01_3commas_dca_bot.png` (start condition
bölümü) + `04_3commas_signal_bot.webp` (3 adım + Max Capital).

## Yeni ekran
`evidence/F15.6/start-indicator.png` (segment + SMA/EMA + periyot
2/3 + koşul + GERÇEK kesişim listesi: Bar 3/4/6/7/12/17/18/23,
yüklenen bardan `/api/signals/indicators/cross` ile).
`evidence/F15.6/start-webhook.png` (webhook URL görünümü).

## Dürüst fark notu
3Commas sırası tamam: segment → koşullu form → önizle. Ancak:
(1) RSI YOK — backend'de RSI yok (13.5 DEFERRED ürün kararı),
SMA/EMA gerçektir (EMA-cross backend'e eklendi: `kind`); (2) Timeframe
YOK — çoklu-TF besleme yok, önizleme yüklenen datasette çalışır;
(3) Max Capital SignalPanel'de doğrulanan+yankılanan yerel lansman
parametresidir (bind sözleşmesinde tavan yok, icra motor işidir);
(4) otomatik ad deterministiktir (`{tip}-bot-N`, saat yok).

## Tasarım gerekçesi (Yönerge m.4)
Seçici yalnız backend'in doğrulayabildiği seçenekleri sunar (sahte
RSI/timeframe kontrolü konmadı). Önizleme 1000 barla sınırlıdır
(endpoint sınırı) ve dilimlenirse not düşer.
