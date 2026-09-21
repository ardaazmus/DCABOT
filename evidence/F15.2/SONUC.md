# F15.2 kanıt — sektör-standardı form kontrolleri (15.4 görsel kabul)

## Referans
`01_3commas_dca_bot.png` (Direction segment, % çipleri), `03_3commas_grid_bot.webp`
(Grid type segment, Exit toggle listesi), `06_bitsgap_dca_averaging.webp`
(stepper/slider), `07_bitsgap_dca_tpsl.webp` (Regular/Trailing segment).

## Yeni ekran
`evidence/F15.2/wizard-entry.png` (stepper + 2 etiketli slider),
`wizard-exit.png` (TP çipleri + 2 toggle), `wizard-budget.png` (yatırım sliderı),
`futures-segment.png` (Grid Tipi/Boyutu segmentleri, Hedge/Sonsuz kapalı).

## Dürüst fark notu
Kontroller referans diline geçti (segment/çip/toggle/stepper/slider) ancak
sihirbaz hâlâ adımlı akışta — referanslardaki tek-ekran form 15.3'te geliyor.
Çip/slider eşlemesi exact metin tablosuyla yapılır, UI'da oran hesabı yok
(para kuralı korundu). Futures alt bölümlerindeki ham `<select>`ler 15.3b'ye kaldı.

## Tasarım gerekçesi (Yönerge m.4)
Wireframe renk/değer vermez; seçili segment = accent dolgu (Bitsgap ışık-tema
dili koyu temaya uyarlandı), 3Commas'ın içbükey koyu hapı değil — gerekçe:
DCABOT accent'i birincil eylem rengidir, tutarlılık korunur. Slider yerli
`accent-color` ile boyandı, özel thumb icat edilmedi (erişilebilirlik + az kod).
Bütçe sliderı % yerine doğrudan USDT tutarı yazar: DCABOT'ta bakiye kavramı
yok, % tabanı uydurulamaz.

## Doğrulama
- checker 1414/1414 PASS (1 skip), tsc temiz, vitest 189/189 (12 yeni).
- 6 yeni bileşen `forms.tsx` ailesinde; yeni paralel sistem yok.
