# F15.1 kanıt — grafik hero eleman (15.4 görsel kabul)

## Referans
`docs/referans_ekranlar/03_3commas_grid_bot.webp` (Chart hero, sağ %65),
`01_3commas_dca_bot.png` (Chart sağ panel), `05_bitsgap_dca_strategies.webp`.

## Yeni ekran
`evidence/F15.1/hero-loaded-dark.png` (gerçek veri: 24 bar BTCUSDT 1h),
`hero-idle-dark.png` (boş durum + yükle düğmesi). Koyu tema.

## Dürüst fark notu
Grafik artık bot kurulumunun en üstünde ve simülasyon zincirini beklemiyor
(ön-uçuş yeterli — sunucu `chart-data`'nın simülasyonsuz çalıştığı curl ile
kanıtlı). Ancak referanslardaki form-sol/grafik-sağ %35/%65 yan-yana yerleşim
henüz yok — bu 15.3'ün işi; bu dilim bağımsız kapanabilir üst şeridi teslim eder.
Canlı baskı çizgisi paper-print yokluğunda görünmez (veri uydurulmadı).

## Tasarım gerekçesi (Yönerge m.4)
Wireframe (`15_3_bot_olustur.svg`) hero grafiği yan-yana düzende gösterir; bu
dilimde tam-genişlik üst şerit yorumlandı çünkü 15.3'ten bağımsız, test edilebilir
bir adım gerekliydi. Renk/tipografi mevcut tokenlardan alındı, yeni token yok.

## Doğrulama
- checker 1414/1414 PASS (1 skip), tsc temiz, vitest 177/177 (6 yeni).
- Not: :8000 worker F12.1-öncesi kodda kalmış (`base_volume` yok); ekran
  görüntüleri güncel kodu çalıştıran ayrı kilitli :8001 backendinden alındı,
  eski worker'a dokunulmadı.
