# F15.3 kanıt — tek-amaç Bot Oluştur ekranı (15.4 görsel kabul)

## Referans
`docs/wireframes/15_3_bot_olustur.svg` (ölçü taslağı %35/%65),
`01_3commas_dca_bot.png` (Create DCA Bot yapısı), `05_bitsgap_dca_strategies.webp`
(boş filo + Start new bot).

## Yeni ekran
`evidence/F15.3/create-dca.png` (tip seçici + form %35 + grafik %65),
`create-grid.png`, `create-futures.png`, `create-signal.png` (4 tip),
`create-footer.png` (veri aralığı + Çalışmaya hazır + Geriye Dönük Test),
`fleet-empty.png` (sekmeler + tip çipleri + boş-durum + CTA),
`stack-open-button.png` (+ Yeni Bot).

## Dürüst fark notu
Tek-amaç görünüm, tip seçici, pair satırları, hazır-ayar içe aktarma, filo
sekmeleri/filtre/boş-durum ve alt bar tamam. Ancak: (1) Futures DCA henüz
Grid ile aynı formu gösterir (15.3b'de Pionex yerleşimi); (2) sihirbaz hâlâ
5 adımlı — referanslardaki tek-ekran form değil; (3) "30g" süre seçici YOK:
DCABOT backtest'i tüm dataset'i koşar, sahte pencere konmadı — yerine gerçek
veri-aralığı rozeti var; (4) görünüm kapanınca girilenler silinir (taslak
yalnız kayıtta yazılır); (5) Geçmiş sekmesi satır uydurmaz, Olaylar'a yönlendirir.

## Tasarım gerekçesi (Yönerge m.4)
SVG'deki 30g+takvim DCABOT'ta veri-aralığı rozeti oldu (gerekçe yukarıda m.3).
Formlar kopyalanmadı: mevcut 3 panel tip'lere bağlandı. Tip bilgisi sunucu
sözleşmesinde yok — istemci taslağından okunur, tipsiz bot "—" görünür ve
yalnız Tümü'nde listelenir. Yerli `color-scheme` eklendi (select/range
koyu-temada beyaz kalıyordu). Segment hover özgüllük hatası yakalanıp düzeltildi.

## Doğrulama
- checker 1414/1414 PASS (1 skip), tsc temiz, vitest 203/203 (10 yeni).
- Not: powershell ile repo dosyası yazımı bir test dosyasını bozdu; git'ten
  geri yüklenip temiz araçlarla yeniden uygulandı, kayıp yok.
