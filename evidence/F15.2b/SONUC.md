# F15.2b kanıt — ExitPanel/TwoLegPanel i18n (15.4 görsel kabul)

## Referans
`docs/ARASTIRMA_FAZ15_GORSEL_DUZELTME.md` §3 terminoloji sözlüğü (Faz 12.5'in
atladığı iki ekran; `grep t\(" → 0` idi).

## Yeni ekran
`evidence/F15.2b/exit-tr.png` (Açık Pozisyon/Aktivasyon Fiyatı/İz Sürme Oranı %),
`exit-en.png` (aynı ekran EN: Open Position Size/Activation Price/Trailing
Rate %), `twoleg-tr.png` (Hedge Bacağı/Hedge Yönü/Dolum Durumu).

## Dürüst fark notu
Her iki panel de TR+EN'e geçti (47 yeni `strings.xml` anahtarı, sıfır ham
metin — eyebrow kısaltmaları hariç). Kontroller hâlâ düz input; segment/
toggle dönüşümü 15.3–15.3c'nin işi. "Session kimliği/Fill kimliği" TR metni
sözlükte karşılığı olmadığı için aynen korundu, yalnız EN eklendi.

## Tasarım gerekçesi (Yönerge m.4)
Sözlük dışı yeniden adlandırma yapılmadı (churn'u önlemek için); tablo
değişikliği isteyen 8 terim (Açık Pozisyon, Aktivasyon Fiyatı, İz Sürme
Oranı %, Hedge Bacağı A/B, Hedge Yönü, Dolum Durumu, Kurtarma Gerekli,
Zaman Aşımı) birebir uygulandı.

## Doğrulama
- checker 1414/1414 PASS (1 skip), tsc temiz, vitest 193/193 (4 yeni).
- EN testleri `I18nProvider` + localStorage ile gerçek çeviriyi kanıtlar.
