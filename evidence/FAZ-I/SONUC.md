# BÜYÜK FAZ I kanıt — Profit Currency + Max Active Deals (2/2 dilim kapalı)

## Kapsam (FAZ16 harita §8.6 + RG-12)
- I.1 (Claude + muse teyit/UI): `Config.profit_asset`
  (null|base|quote, üçüncü coin yok) + maliyet-geri-kazanım
  satışı (qty_step'e YUKARI) + `WITHDRAW_PROFIT` (tek-sefer,
  tam-kalan) + STOP etkilenmez + ladder+base ret. UI:
  sihirbaz kâr-birimi + §8.1 Base uyarısı + tek-seferlik
  onay + base+ladder ret aynası.
- I.2 (Claude + muse teyit/UI): `active_deals_registry.py`
  (Config/engine'e dokunmaz) — hesap/bot/parite 3 sınır,
  aşımda REDDET (kuyruk yok), atomik kayıt. UI: sihirbaz
  3 limit alanı (orkestrasyon bağlantısı ayrı iş notuyla).

## Doğrulama (muse, 2026-09-23)
- Dilim testleri: I.1 14, I.2 10, I UI 5.
- `uv run --frozen python tools/run_checks.py` → **1889/1889
  PASS** (skip=1).
- `npx tsc -b` temiz; `npx vitest run` → **347/347**;
  `npm run build` temiz (dist üretildi).
- M/F/B (muse, kod-okumalı): round-up yönü ✓, WITHDRAW
  kapıları (base+final+boş+tam-kalan) ✓, finalize koşulu
  (EXIT+base+tam-dolum) ✓, STOP tam-satış ✓, ladder+base
  ret ✓, registry atomik kayıt + tip-doğrulama ✓,
  Config/engine'de active_deals yok ✓, üçüncü-coin ret
  gerekçesi ✓, 2021-22 riski retained+UI-uyarısı ✓.
- Float sızıntı (muse, grep): registry'de sayı-dışı yok;
  engine'de float yok; allowlist değişmedi (5 köprü);
  I rotası yok (97 route).
- Gözlem: :8000 boş; dist :8903'te 200 + I dizgileri;
  canlı profit-parse + registry open/close smok'u geçti;
  başlatılan iş bırakılmadı.

## Bilinçli kapsam-dışı (gelecek iş)
- Dinamik quote_asset (canlı venue metadata, ayrı dilim).
- Reinvest/registry orkestrasyon kablolaması (ayrı iş).
- Gözlem (bloke-değil): retained base quote-equity
  dışında (dönüşümsüzlük ilkesi, muhafazakâr yön);
  registry close-kimlik-uyuşmazlığı hayaletleri limiti
  sıkılaştırır (muhafazakâr yön).

## Kapanış
- **BÜYÜK FAZ I kapısı koşuldu; Claude bağımsız
  doğrulama/onayı bekleniyor.**
