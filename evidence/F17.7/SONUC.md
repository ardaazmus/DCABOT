# F17.7 kanıt — Short/Bidirectional matematik çekirdeği (Faz 1: refactor)

## Kaynak
3 bağımsız yapay-zeka ajanından anonim araştırma raporu (2026-09-21):
`dca_short_bidirectional_research_report.md`, `python_dca_bot_rehberi.md`,
`anonim_arastirma_raporu_01_short_bidirectional_yon_destegi.md`. Üçü de
bağımsız olarak aynı işaretli-yön (`dir=+1/-1`) modeline, aynı kümülatif
sapma formülüne (`D_k = d1*(s^k-1)/(s-1)`) ve aynı TP/SL/SO ters-çevirme
kurallarına ulaştı — mutabakat güçlü bir doğrulama sinyalidir.

## M/F/B doğrulama (docs/ARASTIRMA_FAZ16_QWEN_VIZYON_HARITASI.md §6.C kriterleri)
- **(M) Matematik:** Tüm formüller (`dir*qty*(exit-entry)`, `avg*(1±dir*rate)`,
  `anchor*(1-dir*D_k)`) çarpım/toplama/çıkarma — `Fraction` ile exact,
  yuvarlama yok. PASS.
- **(F) Finansal doğruluk:** Üç rapor da PnL/TP/SL/SO işaret tablosunda
  birebir örtüşüyor; sayısal örnekler (SO merdiveni, PnL simetrisi) elle
  doğrulandı. PASS.
- **(B) Borsa kuralı:** WebSearch ile bağımsız çapraz kontrol yapıldı —
  Binance Hedge Mode'da `reduceOnly` + `positionSide` birlikte gönderimi
  gerçekten `-1106`/`-2022` ile reddediliyor (NautilusTrader #4231, CCXT
  #18233/#8801 — raporların 3'ü de aynı olayı bağımsız kaynak gösteriyor).
  **Küçük düzeltme:** raporlardan biri "TP/SL kapatmada reduceOnly opsiyonel"
  diyor; bağımsız arama sonucu daha kesin: **Hedge Mode'da reduceOnly hiç
  gönderilmemeli** (yalnız One-Way modda anlamlı) — bu, adapter tasarımına
  not düşüldü, henüz adapter kodu yazılmadı (kapsam dışı, bkz. altta).
  Binance Hedge-Mode maintenance-margin toplamının iki bacağın toplamı
  olduğu iddiası (S16) bağımsız aramada tam metinle doğrulanamadı (orta
  güven — resmi sayfa formülü tam alıntılamadı), 3 raporun da aynı S16
  kaynağını göstermesiyle kabul edildi, ileride canlı entegrasyonda tekrar
  doğrulanacak.

## Yapılan (Faz 1 — matematik refactor, additive/geriye-uyumlu)
- `src/dcabot/domain/math.py`: `Direction` (LONG=+1/SHORT=-1) enum +
  `signed_pnl`, `directional_take_profit`, `directional_stop_loss`,
  `directional_safety_price`, `is_safety_triggered` — saf, yön-simetrik,
  float'suz fonksiyonlar. Mevcut `Position`/`build_plan`/long-only motor
  **hiç değiştirilmedi** — bu fonksiyonlar şimdilik hiçbir çağıran koddan
  kullanılmıyor (Config/engine.py entegrasyonu henüz yapılmadı, kasıtlı).
- `tests/test_directional_math.py`: 14 test — PnL işareti+simetrisi, TP/SL
  sıralaması (long: SL<E<TP, short: TP<E<SL), SO merdiveni ayna-simetrisi,
  "inverted comparator" sektör hatasının regresyon testi (short ladder
  anchor fiyatında anında tetiklenmiyor), geçersiz girdi reddi.

## Doğrulama
- `PYTHONPATH=src uv run python -m unittest tests.test_directional_math
  tests.test_math_core` → 21/21 PASS (mevcut long-only testler değişmedi).
- `uv run python tools/run_checks.py` → **1446/1446 PASS** (1432'den +14,
  yalnız yeni testler; hiçbir mevcut test bozulmadı).

## Açık kalan (17.7'nin devamı, henüz yapılmadı — ayrı onay/dilim)
- Config'e `direction` alanı eklenmesi (LONG varsayılan, geriye uyumlu).
- `Position`/`build_plan`'ın SHORT/average-up davranışını destekleyecek
  şekilde genişletilmesi (şu an yalnız long-only invariant'ları var).
- `engine.py`'nin deal döngüsüne yön-farkında SO/TP/SL çağrılarının
  bağlanması.
- Borsa adapter katmanında `positionSide`/`reduceOnly`/hedge-mode capability
  matrisi (raporların Bölüm 4/9/21'i) — yalnız gerçek/testnet hesap
  bağlandığında anlamlı, bugün kapsam dışı.
- Bidirectional concurrency (aynı sembolde bağımsız long+short state
  machine) — raporların Bölüm 7/11/12'si, ayrı ürün kararı gerektirir.
