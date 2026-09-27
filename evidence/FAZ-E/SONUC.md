# BÜYÜK FAZ E kanıt — Lab altyapısı + Whale Wall Detection Faz-0

## Kapsam (FAZ16 harita §8.6, 3/3 dilim kapalı)
- E.1 (muse): `application/lab_rate_budget.py` — paylaşılan tavanlı
  kayan-60sn bütçe + venue-gözlem tabanı + `usage_1m`. 9 test.
- E.2 (muse): Lab nav bloğu (ana nav'dan ayrı, amber) + `LabPanel`
  iskeleti (§8.1 uyarısı + tek-seferlik onay). 4 test. Kapıda metin
  dürüstlüğü düzeltmesi ("motor hazır, gösterim ayrı dilimde").
- E.3 (Claude + muse teyit): spot `@depth` okuyucu (REST snapshot +
  WS, keyless) + düzeltilmiş U/u sync makinesi (spot'ta `pu` YOK —
  resmi dokümana karşı doğrulandı) + exact Fraction z² MAD tespiti
  + kalıcılık/trade-çapraz-doğrulama (yalnız-CONFIRMED) + E.1
  bütçe bağlama. Faz-0: tüketici/emir/UI yok. 46 test.

## Doğrulama (2026-09-22)
- `uv run --frozen python tools/run_checks.py` → **1639/1639 PASS**
  (skip=1; E.1 +9, E.3 +46).
- `npx tsc -b` temiz; `npx vitest run` → **324/324**; build temiz.
- CANLI KANIT (E kapısı): gerçek venue'den 3 public snapshot
  (`/tmp/e_gate_probe.py`, commitlenmedi) — venue header'ları
  5/10/15, bütçe takibi birebir aynı, tavan 600 aşılmadı.
- Gözlem notu: tur başında canlı :8000 yanıt vermez oldu (süreçler
  yok; muse durdurmadı — kullanıcı/Claude tarafı).

## Bilinçli kapsam-dışı (gelecek iş)
- Whale canlı gösterim UI bağlama (ayrı dilim).
- SO/TP kaydırma incelik katmanı (sonraki faz).
- Lab tavanı kalibrasyonu (geçici 600).

## Kapanış
- **BÜYÜK FAZ E Arda onayıyla KAPANDI (2026-09-22, ek not yok).**
