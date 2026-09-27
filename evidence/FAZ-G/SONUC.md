# BÜYÜK FAZ G kanıt — DCA-spec parametre genişletmesi I (4/4 dilim kapalı)

## Kapsam (FAZ16 harita §8.6)
- G.1 (Claude + muse teyit/UI): `Config.margin_mode`
  ISOLATED/CROSS (zorunlu, varsayımsız) + binding-hash
  immutability + preflight read-confirm + sembol-registry +
  -4046..-4051 haritası + Cross'ta D.1/F.2 admisyonu.
  UI: sihirbaz alanı + 8.1 Cross uyarısı.
- G.2 (Claude + muse teyit/UI): rol-bazlı 4 order type
  (LIMIT varsayılan) + max_adverse_slippage_bps fail-closed +
  MARK-only referans + realized_slippage çıktı-only. UI:
  sihirbaz 4 rol + slippage (binding bilinçli kapalı).
- G.3 (Claude + muse teyit/UI): `max_active_safety_orders`
  (None=safety_count) + eşzamanlı-SO kapısı (apply+decision)
  + creation-bazlı index. UI: binding + sihirbaz alanı.
- G.4 (Claude + muse teyit, motor-only): Kleene AST
  (All/Any_/Not/CrossUp/CrossDown) + MACD/StochRSI
  sabit-nokta + Bollinger exact/float sınırı + registry.
  UI builder yok (brief'e uygun).

## Doğrulama (muse, 2026-09-23)
- Dilim testleri: G.1 32, G.2 18, G.3 19+3, G.4 53.
- `uv run --frozen python tools/run_checks.py` → **1806/1806
  PASS** (skip=1).
- `npx tsc -b` temiz; `npx vitest run` → **335/335** (G UI:
  4+4+3); `npm run build` temiz (dist üretildi).
- M/F/B (muse, kod-okumalı): Kleene tabloları ✓, cross
  None→UNKNOWN ✓, fixed-point birikimsiz ✓, Bollinger
  exact/float ayrımı ✓, allowlist +1 ✓, should_act
  bağlı değil ✓, native indikatörler dokunulmadı ✓,
  G.1/G.2/G.3 motor kuralları kayıtla birebir ✓.
- Float sızıntı (muse, grep): yeni köprü-dönüşümleri
  dışında `application/`'da float/sqrt yok; G rotası yok
  (97 route, yalnız eski futures/margin).
- Gözlem: :8000 boş (kullanıcı sunucusu yok); dist :8902'de
  200 + G dizgileri pakette; canlı Kleene/MACD/import
  smok'u geçti; başlatılan iş bırakılmadı.

## Bilinçli kapsam-dışı (gelecek iş)
- Fiziksel Order 3'lü tip-ayrımı (davranışsız refactor).
- `Condition` yaprağına runtime TriState doğrulaması
  (bloke-değil gözlem: sıfır çağıran, kod-tabanı normuyla
  tutarlı; istenirse mikro-dilim).
- Canlı fapi pre-flight (futures credential açık soru).
- G.4 UI builder (ayrı ürün kararı).

## Kapanış
- **BÜYÜK FAZ G kapısı koşuldu; Arda onayı bekleniyor.**
