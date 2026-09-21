# Faz 12 kanıt — SONUC.md (UI terminoloji + i18n, 2026-09-21)

## 12.1 grafik altyapısı
`chart-data` sözleşmesine `base_volume` eklendi (exact passthrough).
CandleChart (mum+hacim+marker+canlı çizgi, BigInt ölçek) + LiveTickStrip
(paper baskıları). 11/11 vitest; backend 1 yeni test.

## 12.5 i18n + terminoloji
Tek `strings.xml` (51 anahtar) + `?raw`/DOMParser `t()` + TR/EN düğmesi
(localStorage). Nav + bot stüdyosu (Baz Emir/Güvenlik Emri/Fiyat Sapması)
+ sihirbaz adımları taşındı. 10/10 vitest.

## 12.2 birleşik Bot Oluştur
Kimlik+Parite → Giriş → Çıkış → Bütçe → Önizleme+Backtest; giriş/çıkış
istemci taslağı (localStorage), kayıt yükü değişmedi. Gelişmiş Araçlar
2 kapalı grup. 6/6 + 1/1 vitest.

## 12.3 Grid Bot gerçek akışı
Küme B bağlandı (salt okunur projeksiyon): placement/position/margin/
lifecycle/policy/variants endpoint'leri + brüt aralık % (exact bayraklı).
Hedge/Sonsuz kapıda kapalı + gerekçeli. 15 backend + 8 vitest.

## 12.4 sinyal botu görünümü
3 adım (Ayarlar→Alertler→Başlat) Faz 13 webhook'larına bağlı; manuel akış
kapalı detaya taşındı (etiketler aynı). Status/list endpoint'leri. 5+4 test.

## 12.6 temizlik
bootstrap/domain.math/persistence.store ERİŞİLİYOR (üretim+tools import)
→ silinmedi, karar notu yazıldı. "Kilitli canlı kapı" test-only netleşti.

- Tam checker 1414/1414 PASS (F12 payı +21); tsc temiz; vitest 171/171.
- `python tools/phase_gate.py F12` → GATE PASS.
